"""Symbolic law extraction for regime-specific temporal signals."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import numpy as np
import pandas as pd
from sklearn.linear_model import Lasso

from .operator_library import build_coupled_operator_matrices, build_operator_matrix
from .law_validator import (
    behavior_validation_score,
    coupled_field_validation_score,
    field_validation_score,
    r2_score,
    train_test_split,
)
from .regime_data_sampler import sample_regime_observations


@dataclass
class LawResult:
    regime: str
    field_name: str
    equation: str
    terms: List[str]
    coefficients: List[float]
    fit_score: float
    validation_score: float
    regime_match_score: float
    coupled_match_score: float = 0.0
    law_class: str | None = None
    law_signature: str | None = None


def _format_equation(coeffs: np.ndarray, names: List[str], field_name: str = "psi") -> str:
    terms = []
    for coeff, name in zip(coeffs, names):
        if abs(coeff) < 1e-6:
            continue
        terms.append(f"{coeff:+.3f} {name}")
    if not terms:
        return f"d{field_name}/dt = 0"
    return f"d{field_name}/dt = " + " ".join(terms)


def _law_signature(terms: List[str], coeffs: np.ndarray, threshold: float = 1e-4) -> str:
    active = [name for coeff, name in zip(coeffs, terms) if abs(coeff) >= threshold]
    if not active:
        return "null"
    return " + ".join(sorted(active))


def extract_symbolic_laws(
    df: pd.DataFrame,
    regime_column: str = "regime_signature",
    signal_column: str = "temporal_signal",
    field_column: str = "field",
    max_per_regime: int = 5,
    alpha: float = 0.01,
) -> List[LawResult]:
    has_multi = "temporal_signal_psi" in df.columns and "temporal_signal_phi" in df.columns
    if signal_column not in df.columns and not has_multi:
        return []
    sampled = sample_regime_observations(df, regime_column=regime_column, max_per_regime=max_per_regime)
    results: List[LawResult] = []
    for regime, group in sampled.groupby(regime_column):
        if has_multi:
            results.extend(
                _extract_coupled_regime_laws(
                    group,
                    regime=str(regime),
                    alpha=alpha,
                )
            )
        else:
            results.extend(
                _extract_single_regime_laws(
                    group,
                    regime=str(regime),
                    signal_column=signal_column,
                    field_column=field_column,
                    alpha=alpha,
                )
            )
    return results


def _extract_single_regime_laws(
    group: pd.DataFrame,
    regime: str,
    signal_column: str,
    field_column: str,
    alpha: float,
) -> List[LawResult]:
    matrices = []
    targets = []
    signals = []
    fields = []
    reference_metrics = []
    names: List[str] = []
    for _, row in group.iterrows():
        signal = row.get(signal_column)
        if signal is None:
            continue
        field = row.get(field_column) if field_column in row else None
        matrix, target, names = build_operator_matrix(signal, field=field)
        if matrix.size == 0:
            continue
        matrices.append(matrix)
        targets.append(target)
        signals.append(np.array(signal, dtype=float))
        if field is not None and isinstance(field, np.ndarray):
            fields.append(field)
            reference_metrics.append({key: row.get(key) for key in row.index})
    if not matrices:
        return []
    return [
        _fit_regime_law(
            regime=regime,
            field_name="psi",
            matrices=matrices,
            targets=targets,
            signals=signals,
            names=names,
            fields=fields,
            reference_metrics=reference_metrics,
            alpha=alpha,
        )
    ]


def _extract_coupled_regime_laws(
    group: pd.DataFrame,
    regime: str,
    alpha: float,
) -> List[LawResult]:
    matrices_psi = []
    targets_psi = []
    signals_psi = []
    matrices_phi = []
    targets_phi = []
    signals_phi = []
    names: List[str] = []
    fields_psi = []
    fields_phi = []
    reference_metrics_psi = []
    reference_metrics_phi = []
    reference_metrics_coupled = []
    for _, row in group.iterrows():
        psi_signal = row.get("temporal_signal_psi") or row.get("psi_temporal_signal")
        phi_signal = row.get("temporal_signal_phi") or row.get("phi_temporal_signal")
        if psi_signal is None or phi_signal is None:
            continue
        psi_field = row.get("field_psi")
        phi_field = row.get("field_phi")
        (
            matrix_psi,
            target_psi,
            names,
            matrix_phi,
            target_phi,
            _,
        ) = build_coupled_operator_matrices(
            psi_signal,
            phi_signal,
            psi_field=psi_field,
            phi_field=phi_field,
        )
        if matrix_psi.size == 0:
            continue
        matrices_psi.append(matrix_psi)
        targets_psi.append(target_psi)
        signals_psi.append(np.array(psi_signal, dtype=float))
        matrices_phi.append(matrix_phi)
        targets_phi.append(target_phi)
        signals_phi.append(np.array(phi_signal, dtype=float))
        if psi_field is not None and phi_field is not None:
            fields_psi.append(np.asarray(psi_field))
            fields_phi.append(np.asarray(phi_field))
            reference_metrics_psi.append(_extract_field_metrics(row, prefix="psi_"))
            reference_metrics_phi.append(_extract_field_metrics(row, prefix="phi_"))
            reference_metrics_coupled.append(_extract_coupled_metrics(row))
    if not matrices_psi or not matrices_phi:
        return []
    psi_result = _fit_regime_law(
        regime=regime,
        field_name="psi",
        matrices=matrices_psi,
        targets=targets_psi,
        signals=signals_psi,
        names=names,
        fields=fields_psi,
        reference_metrics=reference_metrics_psi,
        alpha=alpha,
        auxiliary_fields=fields_phi,
    )
    phi_result = _fit_regime_law(
        regime=regime,
        field_name="phi",
        matrices=matrices_phi,
        targets=targets_phi,
        signals=signals_phi,
        names=names,
        fields=fields_phi,
        reference_metrics=reference_metrics_phi,
        alpha=alpha,
        auxiliary_fields=fields_psi,
    )
    coupled_scores = []
    for psi_field, phi_field, metrics in zip(fields_psi, fields_phi, reference_metrics_coupled):
        match_score, _ = coupled_field_validation_score(
            psi_field,
            phi_field,
            np.array(psi_result.coefficients, dtype=float),
            np.array(phi_result.coefficients, dtype=float),
            names,
            metrics,
        )
        coupled_scores.append(match_score)
    coupled_match_score = float(np.mean(coupled_scores)) if coupled_scores else 0.0
    psi_result.coupled_match_score = coupled_match_score
    phi_result.coupled_match_score = coupled_match_score
    return [psi_result, phi_result]


def _extract_field_metrics(row: pd.Series, prefix: str) -> Dict[str, object]:
    keys = [
        "vortex_count",
        "coherence_length",
        "spectral_entropy",
        "defect_density",
        "particle_count",
        "energy_localization",
    ]
    metrics: Dict[str, object] = {}
    for key in keys:
        prefixed = f"{prefix}{key}"
        if prefixed in row.index:
            metrics[key] = row.get(prefixed)
    return metrics


def _extract_coupled_metrics(row: pd.Series) -> Dict[str, object]:
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
    metrics: Dict[str, object] = {}
    for key in keys:
        if key in row.index:
            metrics[key] = row.get(key)
    return metrics


def _fit_regime_law(
    regime: str,
    field_name: str,
    matrices: List[np.ndarray],
    targets: List[np.ndarray],
    signals: List[np.ndarray],
    names: List[str],
    fields: List[np.ndarray],
    reference_metrics: List[Dict[str, object]],
    alpha: float,
    auxiliary_fields: List[np.ndarray] | None = None,
) -> LawResult:
    X = np.vstack(matrices)
    y = np.concatenate(targets)
    X_train, X_test, y_train, y_test = train_test_split(X, y)
    model = Lasso(alpha=alpha, fit_intercept=False, max_iter=10000)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_train)
    fit_score = r2_score(y_train, y_pred)
    behavior_scores = [
        behavior_validation_score(model.coef_, matrix, signal)
        for matrix, signal in zip(matrices, signals)
    ]
    if behavior_scores:
        validation_score = float(np.mean(behavior_scores))
    else:
        val_pred = model.predict(X_test) if X_test.size else y_train
        validation_score = r2_score(y_test, val_pred) if X_test.size else fit_score
    regime_scores = []
    if auxiliary_fields is None:
        auxiliary_fields = [None] * len(fields)
    for field, metrics, aux in zip(fields, reference_metrics, auxiliary_fields):
        match_score, _ = field_validation_score(
            field,
            model.coef_,
            names,
            metrics,
            auxiliary_field=aux,
        )
        regime_scores.append(match_score)
    regime_match_score = float(np.mean(regime_scores)) if regime_scores else 0.0
    signature = _law_signature(names, model.coef_)
    equation = _format_equation(model.coef_, names, field_name=field_name)
    return LawResult(
        regime=regime,
        field_name=field_name,
        equation=equation,
        terms=names,
        coefficients=[float(v) for v in model.coef_],
        fit_score=float(fit_score),
        validation_score=float(validation_score),
        regime_match_score=regime_match_score,
        coupled_match_score=0.0,
        law_signature=signature,
    )


def laws_to_dataframe(laws: List[LawResult]) -> pd.DataFrame:
    if not laws:
        return pd.DataFrame()
    rows = [
        {
            "regime": law.regime,
            "law_field": law.field_name,
            "law_equation": law.equation,
            "law_terms": ", ".join(law.terms),
            "law_coefficients": ", ".join(f"{c:.3f}" for c in law.coefficients),
            "law_fit_score": law.fit_score,
            "law_validation_score": law.validation_score,
            "law_regime_match_score": law.regime_match_score,
            "law_coupled_match_score": law.coupled_match_score,
            "law_signature": law.law_signature,
        }
        for law in laws
    ]
    df = pd.DataFrame(rows)
    signatures = [sig for sig in df["law_signature"].unique() if sig]
    signatures_sorted = sorted(signatures)
    class_labels = {}
    for idx, sig in enumerate(signatures_sorted):
        label = f"Class {chr(65 + idx)}" if idx < 26 else f"Class {idx + 1}"
        class_labels[sig] = label
    df["law_class"] = df["law_signature"].map(class_labels)
    return df


def operator_importance_summary(laws: List[LawResult], threshold: float = 1e-4) -> pd.DataFrame:
    if not laws:
        return pd.DataFrame()
    counts: Dict[str, int] = {}
    for law in laws:
        for coeff, name in zip(law.coefficients, law.terms):
            if abs(coeff) >= threshold:
                counts[name] = counts.get(name, 0) + 1
    total = sum(counts.values())
    rows = [
        {"operator": name, "frequency": count, "share": count / total if total else 0.0}
        for name, count in sorted(counts.items(), key=lambda item: item[1], reverse=True)
    ]
    return pd.DataFrame(rows)