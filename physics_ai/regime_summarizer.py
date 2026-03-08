"""Summarize behavioral regimes with human-readable descriptors."""

from __future__ import annotations

from typing import Dict, List

import numpy as np
import pandas as pd


METRIC_COLUMNS = [
    "defect_density",
    "vortex_count",
    "nodal_loop_count",
    "coherence_length",
    "spectral_entropy",
    "variance",
    "energy_localization",
    "particle_count",
    "resonance_strength",
    "curvature_strength",
]


def _metric_thresholds(df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
    thresholds: Dict[str, Dict[str, float]] = {}
    for col in METRIC_COLUMNS:
        if col in df.columns:
            series = df[col].fillna(0.0).to_numpy(dtype=float)
            thresholds[col] = {
                "p25": float(np.percentile(series, 25)),
                "p75": float(np.percentile(series, 75)),
            }
    return thresholds


def _describe_cluster(stats: Dict[str, float], thresholds: Dict[str, Dict[str, float]]) -> List[str]:
    descriptors: List[str] = []
    for key, label in [
        ("defect_density", "high defect density"),
        ("vortex_count", "high vortex count"),
        ("coherence_length", "long coherence length"),
        ("spectral_entropy", "high spectral entropy"),
        ("variance", "high variance"),
        ("energy_localization", "strong localization"),
        ("particle_count", "many particles"),
    ]:
        if key in stats and key in thresholds:
            if stats[key] >= thresholds[key]["p75"]:
                descriptors.append(label)
    if "spectral_entropy" in stats and "spectral_entropy" in thresholds:
        if stats["spectral_entropy"] <= thresholds["spectral_entropy"]["p25"]:
            descriptors.append("low spectral entropy")
    if not descriptors:
        descriptors.append("mixed dynamics")
    return descriptors


def _label_cluster(descriptors: List[str]) -> str:
    descriptor_set = set(descriptors)
    if "high vortex count" in descriptor_set and "long coherence length" in descriptor_set:
        return "vortex lattice"
    if "high defect density" in descriptor_set and "many particles" in descriptor_set:
        return "particle-rich regime"
    if "strong localization" in descriptor_set and "low spectral entropy" in descriptor_set:
        return "soliton-like regime"
    if "high spectral entropy" in descriptor_set and "high variance" in descriptor_set:
        return "turbulent regime"
    if "high defect density" in descriptor_set:
        return "defect-rich regime"
    return "mixed regime"


def _signature_from_descriptors(descriptors: List[str]) -> str:
    normalized = [
        desc.replace("high ", "high_")
        .replace("low ", "low_")
        .replace("strong ", "strong_")
        .replace("many ", "many_")
        .replace(" ", "_")
        for desc in descriptors
    ]
    return "_".join(normalized)


def summarize_behavior_clusters(
    df: pd.DataFrame,
    cluster_column: str = "behavior_cluster_id",
    probability_column: str = "behavior_cluster_probability",
) -> pd.DataFrame:
    """Summarize behavioral clusters with descriptors and labels."""
    if cluster_column not in df.columns:
        return pd.DataFrame()
    thresholds = _metric_thresholds(df)
    summaries = []
    clustered = df[df[cluster_column] >= 0]
    for cluster_id, group in clustered.groupby(cluster_column):
        stats = {
            col: float(group[col].fillna(0.0).mean())
            for col in METRIC_COLUMNS
            if col in group.columns
        }
        descriptors = _describe_cluster(stats, thresholds)
        label = _label_cluster(descriptors)
        signature = _signature_from_descriptors(descriptors)
        family = None
        if "law_family" in group.columns:
            family_counts = group["law_family"].dropna().value_counts()
            if not family_counts.empty:
                family = str(family_counts.idxmax())
                descriptors.append(f"{family} dynamics")
        summaries.append({
            "cluster_id": int(cluster_id),
            "size": int(group.shape[0]),
            "mean_probability": float(group.get(probability_column, pd.Series(0.0, index=group.index)).mean()),
            "label": label,
            "descriptors": ", ".join(descriptors),
            "regime_signature": signature,
            "law_family": family,
            **stats,
        })
    if not summaries:
        return pd.DataFrame()
    return pd.DataFrame(summaries).sort_values("size", ascending=False).reset_index(drop=True)
