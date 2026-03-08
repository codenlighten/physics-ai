"""Resonance ratio analysis utilities for invariant discovery."""

from __future__ import annotations

from typing import Dict, Iterable, List, Tuple
import ast

import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN


KNOWN_CONSTANTS = {
    "phi": (1 + 5 ** 0.5) / 2,
    "inv_phi": 2 / (1 + 5 ** 0.5),
    "phi_sq": ((1 + 5 ** 0.5) / 2) ** 2,
    "sqrt2": 2 ** 0.5,
    "pi": np.pi,
    "e": np.e,
}


def _parse_list(value: object) -> List[float]:
    if value is None:
        return []
    if isinstance(value, list):
        return [float(v) for v in value if v is not None]
    if isinstance(value, str):
        try:
            parsed = ast.literal_eval(value)
            if isinstance(parsed, list):
                return [float(v) for v in parsed if v is not None]
        except (ValueError, SyntaxError):
            return []
    return []


def _peak_frequencies(values: List[float], top_n: int = 3) -> List[float]:
    clean = [v for v in values if v > 0]
    if not clean:
        return []
    idx = np.argsort(clean)[-top_n:]
    return [float(clean[i]) for i in idx][::-1]


def _pairwise_ratios(values: List[float]) -> List[float]:
    ratios: List[float] = []
    for i in range(len(values)):
        for j in range(i + 1, len(values)):
            if values[j] != 0:
                ratios.append(values[i] / values[j])
    return ratios


def extract_ratios(
    df: pd.DataFrame,
    fft_column: str = "temporal_fft",
    dominant_column: str = "dominant_frequency",
    max_peaks: int = 3,
) -> pd.DataFrame:
    """Extract ratio samples from per-universe frequency observables."""
    rows = []
    for idx, row in df.iterrows():
        spectrum = _parse_list(row.get(fft_column))
        peaks = _peak_frequencies(spectrum, top_n=max_peaks)
        if not peaks and dominant_column in df.columns:
            peaks = [float(row.get(dominant_column, 0.0))]
        ratios = _pairwise_ratios(peaks)
        for ratio in ratios:
            rows.append({
                "universe_id": row.get("universe_id", idx),
                "ratio": ratio,
                "source": "temporal_fft",
            })
    return pd.DataFrame(rows)


def cluster_ratios(
    ratios: Iterable[float],
    eps: float = 0.05,
    min_samples: int = 5,
) -> Tuple[pd.DataFrame, np.ndarray]:
    values = np.array([r for r in ratios if r > 0], dtype=float)
    if values.size == 0:
        return pd.DataFrame(), np.array([])
    labels = DBSCAN(eps=eps, min_samples=min_samples).fit_predict(values.reshape(-1, 1))
    summary_rows: List[Dict[str, float | int | str]] = []
    for label in sorted(set(labels)):
        cluster_values = values[labels == label]
        if cluster_values.size == 0:
            continue
        center = float(np.mean(cluster_values))
        match, confidence = match_constant(center)
        summary_rows.append({
            "ratio_cluster_id": int(label),
            "center": center,
            "count": int(cluster_values.size),
            "constant_match": match,
            "confidence": confidence,
        })
    return pd.DataFrame(summary_rows), labels


def match_constant(value: float) -> Tuple[str, float]:
    best_name = "unknown"
    best_score = 0.0
    for name, constant in KNOWN_CONSTANTS.items():
        if constant == 0:
            continue
        diff = abs(value - constant) / constant
        score = max(0.0, 1.0 - diff)
        if score > best_score:
            best_score = score
            best_name = name
    return best_name, float(best_score)


def annotate_ratios(
    df: pd.DataFrame,
    ratio_df: pd.DataFrame,
    clusters: pd.DataFrame,
) -> pd.DataFrame:
    if ratio_df.empty:
        annotated = df.copy()
        annotated["dominant_ratio"] = np.nan
        annotated["ratio_cluster_id"] = -1
        annotated["ratio_constant_match"] = "unknown"
        annotated["ratio_confidence"] = 0.0
        return annotated
    ratio_df = ratio_df.copy()
    if not clusters.empty:
        ratio_df = ratio_df.merge(clusters, on="ratio_cluster_id", how="left")
    grouped = ratio_df.sort_values("ratio", ascending=False).groupby("universe_id").first()
    annotated = df.copy()
    annotated = annotated.merge(
        grouped[["ratio", "ratio_cluster_id", "constant_match", "confidence"]],
        left_on="universe_id",
        right_index=True,
        how="left",
    )
    annotated = annotated.rename(
        columns={
            "ratio": "dominant_ratio",
            "constant_match": "ratio_constant_match",
            "confidence": "ratio_confidence",
        }
    )
    annotated["ratio_cluster_id"] = annotated["ratio_cluster_id"].fillna(-1).astype(int)
    annotated["ratio_constant_match"] = annotated["ratio_constant_match"].fillna("unknown")
    annotated["ratio_confidence"] = annotated["ratio_confidence"].fillna(0.0)
    return annotated


def analyze_ratios(
    df: pd.DataFrame,
    eps: float = 0.05,
    min_samples: int = 5,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    ratio_df = extract_ratios(df)
    if ratio_df.empty:
        return df.copy(), pd.DataFrame(), pd.DataFrame()
    clusters, labels = cluster_ratios(ratio_df["ratio"].to_numpy(), eps=eps, min_samples=min_samples)
    if not clusters.empty:
        ratio_df["ratio_cluster_id"] = labels
    annotated = annotate_ratios(df, ratio_df, clusters)
    return annotated, ratio_df, clusters
