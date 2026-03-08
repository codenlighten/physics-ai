"""Infer conserved quantities from symmetry and temporal metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, List

import numpy as np
import sympy as sp


@dataclass
class NoetherResult:
    symmetry: str
    conserved_quantity: str
    drift_ratio: float
    conserved: bool
    evidence: str


def _rotation_symmetry(symmetry_group: str | None) -> bool:
    if not symmetry_group:
        return False
    return symmetry_group.startswith("SO") or symmetry_group.startswith("D") or symmetry_group.startswith("C")


def lagrangian_energy_drift(
    lagrangian: str,
    signal: List[float],
    dt: float = 1.0,
) -> float:
    if len(signal) < 4:
        return 1.0
    q, qd = sp.symbols("q qd")
    expr = sp.sympify(lagrangian)
    d_ldqd = sp.diff(expr, qd)
    energy_expr = qd * d_ldqd - expr
    f_energy = sp.lambdify((q, qd), energy_expr, "numpy")
    values = np.array(signal, dtype=float)
    vel = np.gradient(values, dt)
    energy_series = f_energy(values, vel)
    mean_energy = float(np.mean(energy_series)) if np.mean(energy_series) != 0 else 1.0
    return float(np.std(energy_series) / mean_energy)


def infer_noether(
    observation: Dict[str, Any],
    energy_threshold: float = 0.01,
    momentum_threshold: float = 0.05,
    translation_threshold: float = 0.85,
    scale_threshold: float = 0.8,
    phase_threshold: float = 0.8,
    lagrangian: str | None = None,
    dt: float = 1.0,
) -> List[NoetherResult]:
    results: List[NoetherResult] = []
    energy_drift = float(observation.get("temporal_energy_drift_ratio", 1.0))
    momentum_drift = float(observation.get("temporal_momentum_drift_ratio", 1.0))
    symmetry_group = observation.get("symmetry_group")
    temporal_signal = observation.get("temporal_signal", [])
    translation_score = float(observation.get("translation_invariance", 0.0))
    scale_score = float(observation.get("scale_invariance", 0.0))
    phase_score = float(observation.get("phase_invariance", 0.0))

    if energy_drift < energy_threshold:
        results.append(
            NoetherResult(
                symmetry="time_translation",
                conserved_quantity="energy",
                drift_ratio=energy_drift,
                conserved=True,
                evidence="temporal_energy_drift",
            )
        )

    if lagrangian and temporal_signal:
        lagrangian_drift = lagrangian_energy_drift(lagrangian, temporal_signal, dt=dt)
        if lagrangian_drift < energy_threshold:
            results.append(
                NoetherResult(
                    symmetry="time_translation",
                    conserved_quantity="energy",
                    drift_ratio=lagrangian_drift,
                    conserved=True,
                    evidence="lagrangian_energy",
                )
            )

    if _rotation_symmetry(symmetry_group) and momentum_drift < momentum_threshold:
        results.append(
            NoetherResult(
                symmetry="rotation",
                conserved_quantity="angular_momentum",
                drift_ratio=momentum_drift,
                conserved=True,
                evidence="temporal_momentum_drift",
            )
        )

    if translation_score >= translation_threshold and momentum_drift < momentum_threshold:
        results.append(
            NoetherResult(
                symmetry="space_translation",
                conserved_quantity="momentum",
                drift_ratio=1.0 - translation_score,
                conserved=True,
                evidence="translation_invariance",
            )
        )

    if scale_score >= scale_threshold:
        results.append(
            NoetherResult(
                symmetry="scale",
                conserved_quantity="dilation_charge",
                drift_ratio=1.0 - scale_score,
                conserved=True,
                evidence="scale_invariance",
            )
        )

    if phase_score >= phase_threshold:
        results.append(
            NoetherResult(
                symmetry="phase",
                conserved_quantity="charge",
                drift_ratio=1.0 - phase_score,
                conserved=True,
                evidence="phase_invariance",
            )
        )

    return results
