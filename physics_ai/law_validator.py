"""Validation utilities for symbolic laws."""

from __future__ import annotations

from typing import Dict, Iterable, Tuple

import numpy as np

from .field_dynamics import laplacian
from .observer import observe, observe_multifield, observe_temporal, observe_temporal_multi


def train_test_split(matrix: np.ndarray, target: np.ndarray, split: float = 0.8) -> Tuple[np.ndarray, ...]:
    if matrix.shape[0] == 0:
        return matrix, matrix, target, target
    idx = int(matrix.shape[0] * split)
    return matrix[:idx], matrix[idx:], target[:idx], target[idx:]


def r2_score(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    if y_true.size == 0:
        return 0.0
    ss_res = float(np.sum((y_true - y_pred) ** 2))
    mean = float(np.mean(y_true))
    ss_tot = float(np.sum((y_true - mean) ** 2)) if y_true.size else 0.0
    if ss_tot == 0:
        return 0.0
    return float(1.0 - ss_res / ss_tot)


def simulate_ode(
    coeffs: np.ndarray,
    operator_matrix: np.ndarray,
    initial_value: float,
    dt: float = 1.0,
) -> np.ndarray:
    if operator_matrix.size == 0:
        return np.array([])
    values = [initial_value]
    for idx in range(1, operator_matrix.shape[0]):
        d_dt = float(np.dot(operator_matrix[idx - 1], coeffs))
        values.append(values[-1] + d_dt * dt)
    return np.array(values, dtype=float)


def behavior_validation_score(
    coeffs: np.ndarray,
    operator_matrix: np.ndarray,
    signal: np.ndarray,
    dt: float = 1.0,
) -> float:
    if signal.size == 0 or operator_matrix.size == 0:
        return 0.0
    pred = simulate_ode(coeffs, operator_matrix, float(signal[0]), dt=dt)
    if pred.size != signal.size:
        return 0.0
    return r2_score(signal, pred)


def simulate_field_law(
    initial_field: np.ndarray,
    coeffs: np.ndarray,
    names: Iterable[str],
    steps: int = 40,
    dt: float = 0.05,
    auxiliary_field: np.ndarray | None = None,
) -> np.ndarray:
    field = np.asarray(initial_field, dtype=float)
    aux = np.asarray(auxiliary_field, dtype=float) if auxiliary_field is not None else None
    frames = [field.copy()]
    name_list = list(names)
    for _ in range(max(1, steps)):
        d_dt = np.zeros_like(field)
        for coeff, name in zip(coeffs, name_list):
            if abs(coeff) < 1e-8:
                continue
            if name == "psi":
                d_dt += coeff * field
            elif name == "psi^3":
                d_dt += coeff * (field ** 3)
            elif name == "psi^5":
                d_dt += coeff * (field ** 5)
            elif name == "phi" and aux is not None:
                d_dt += coeff * aux
            elif name == "phi^3" and aux is not None:
                d_dt += coeff * (aux ** 3)
            elif name == "psi*phi" and aux is not None:
                d_dt += coeff * field * aux
            elif name == "psi^2*phi" and aux is not None:
                d_dt += coeff * (field ** 2) * aux
            elif name == "phi^2*psi" and aux is not None:
                d_dt += coeff * (aux ** 2) * field
            elif name == "laplacian":
                d_dt += coeff * laplacian(field)
            elif name == "laplacian_psi":
                d_dt += coeff * laplacian(field)
            elif name == "laplacian_phi" and aux is not None:
                d_dt += coeff * laplacian(aux)
            elif name == "biharmonic":
                d_dt += coeff * laplacian(laplacian(field))
            elif name == "abs(psi)^2 psi":
                d_dt += coeff * (np.abs(field) ** 2 * field)
        field = field + d_dt * dt
        frames.append(field.copy())
    return np.stack(frames)


def _evaluate_terms(
    field: np.ndarray,
    aux: np.ndarray | None,
    coeffs: np.ndarray,
    names: Iterable[str],
) -> np.ndarray:
    d_dt = np.zeros_like(field)
    for coeff, name in zip(coeffs, list(names)):
        if abs(coeff) < 1e-8:
            continue
        if name == "psi":
            d_dt += coeff * field
        elif name == "psi^3":
            d_dt += coeff * (field ** 3)
        elif name == "psi^5":
            d_dt += coeff * (field ** 5)
        elif name == "phi" and aux is not None:
            d_dt += coeff * aux
        elif name == "phi^3" and aux is not None:
            d_dt += coeff * (aux ** 3)
        elif name == "psi*phi" and aux is not None:
            d_dt += coeff * field * aux
        elif name == "psi^2*phi" and aux is not None:
            d_dt += coeff * (field ** 2) * aux
        elif name == "phi^2*psi" and aux is not None:
            d_dt += coeff * (aux ** 2) * field
        elif name in {"laplacian", "laplacian_psi"}:
            d_dt += coeff * laplacian(field)
        elif name == "laplacian_phi" and aux is not None:
            d_dt += coeff * laplacian(aux)
        elif name == "biharmonic":
            d_dt += coeff * laplacian(laplacian(field))
        elif name == "abs(psi)^2 psi":
            d_dt += coeff * (np.abs(field) ** 2 * field)
    return d_dt


def simulate_coupled_law(
    psi_field: np.ndarray,
    phi_field: np.ndarray,
    coeffs_psi: np.ndarray,
    coeffs_phi: np.ndarray,
    names: Iterable[str],
    steps: int = 40,
    dt: float = 0.05,
) -> np.ndarray:
    psi = np.asarray(psi_field, dtype=float)
    phi = np.asarray(phi_field, dtype=float)
    frames = [np.stack([psi.copy(), phi.copy()])]
    for _ in range(max(1, steps)):
        dpsi = _evaluate_terms(psi, phi, coeffs_psi, names)
        dphi = _evaluate_terms(phi, psi, coeffs_phi, names)
        psi = psi + dpsi * dt
        phi = phi + dphi * dt
        frames.append(np.stack([psi.copy(), phi.copy()]))
    return np.stack(frames)


def coupled_regime_match_score(
    reference_metrics: Dict[str, float],
    candidate_metrics: Dict[str, float],
) -> float:
    keys = [
        "psi_defect_density",
        "phi_defect_density",
        "psi_spectral_entropy",
        "phi_spectral_entropy",
        "psi_vortex_count",
        "phi_vortex_count",
        "cross_field_corr",
        "cross_field_temporal_corr",
    ]
    return regime_match_score(reference_metrics, candidate_metrics, keys=keys)


def coupled_field_validation_score(
    psi_field: np.ndarray,
    phi_field: np.ndarray,
    coeffs_psi: np.ndarray,
    coeffs_phi: np.ndarray,
    names: Iterable[str],
    reference_metrics: Dict[str, float],
    steps: int = 40,
    dt: float = 0.05,
) -> Tuple[float, Dict[str, float]]:
    frames = simulate_coupled_law(
        psi_field,
        phi_field,
        coeffs_psi,
        coeffs_phi,
        names,
        steps=steps,
        dt=dt,
    )
    final_metrics = observe_multifield({"psi": frames[-1, 0], "phi": frames[-1, 1]})
    temporal_metrics = observe_temporal_multi(frames, ["psi", "phi"])
    final_metrics.update(temporal_metrics)
    score = coupled_regime_match_score(reference_metrics, final_metrics)
    return score, final_metrics


def regime_match_score(
    reference: Dict[str, float],
    candidate: Dict[str, float],
    keys: Iterable[str] | None = None,
) -> float:
    metric_keys = list(
        keys
        if keys is not None
        else [
            "vortex_count",
            "coherence_length",
            "spectral_entropy",
            "defect_density",
            "particle_count",
            "energy_localization",
        ]
    )
    diffs = []
    for key in metric_keys:
        if key not in reference or key not in candidate:
            continue
        ref = float(reference.get(key, 0.0))
        cand = float(candidate.get(key, 0.0))
        denom = abs(ref) + abs(cand) + 1e-6
        diffs.append(abs(ref - cand) / denom)
    if not diffs:
        return 0.0
    score = 1.0 - float(np.mean(diffs))
    return float(np.clip(score, 0.0, 1.0))


def field_validation_score(
    initial_field: np.ndarray,
    coeffs: np.ndarray,
    names: Iterable[str],
    reference_metrics: Dict[str, float],
    steps: int = 40,
    dt: float = 0.05,
    auxiliary_field: np.ndarray | None = None,
) -> Tuple[float, Dict[str, float]]:
    frames = simulate_field_law(
        initial_field,
        coeffs,
        names,
        steps=steps,
        dt=dt,
        auxiliary_field=auxiliary_field,
    )
    final_metrics = observe(frames[-1])
    temporal_metrics = observe_temporal(frames)
    final_metrics.update(temporal_metrics)
    score = regime_match_score(reference_metrics, final_metrics)
    return score, final_metrics