"""Behavioral regime clustering utilities using physics metrics."""

from __future__ import annotations

from typing import List, Tuple

import numpy as np
import pandas as pd

from .regime_clustering import _lazy_import_hdbscan, _cluster_sizes


def build_behavior_matrix(df: pd.DataFrame) -> Tuple[np.ndarray, List[str]]:
    columns = [
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
    features = []
    feature_names: List[str] = []
    for col in columns:
        if col in df.columns:
            values = df[col].fillna(0.0).to_numpy(dtype=float)
            features.append(values)
            feature_names.append(col)
    if not features:
        return np.empty((df.shape[0], 0)), []
    matrix = np.stack(features, axis=1)
    mean = matrix.mean(axis=0)
    std = matrix.std(axis=0)
    std[std == 0] = 1.0
    matrix = (matrix - mean) / std
    return matrix, feature_names


def cluster_behavior(
    df: pd.DataFrame,
    min_cluster_size: int = 15,
    min_samples: int = 5,
    probability_threshold: float = 0.3,
    cluster_column: str = "behavior_cluster_id",
    probability_column: str = "behavior_cluster_probability",
    size_column: str = "behavior_cluster_size",
    outlier_column: str = "behavior_cluster_outlier",
) -> Tuple[pd.DataFrame, np.ndarray]:
    """Cluster behavior metrics and return annotated dataframe + labels."""
    features, _ = build_behavior_matrix(df)
    if features.size == 0 or features.shape[0] < 2:
        annotated = df.copy()
        annotated[cluster_column] = -1
        annotated[probability_column] = 0.0
        annotated[size_column] = 0
        annotated[outlier_column] = True
        return annotated, np.array([-1] * df.shape[0])

    hdbscan = _lazy_import_hdbscan()
    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=min_cluster_size,
        min_samples=min_samples,
    )
    labels = clusterer.fit_predict(features)
    probabilities = getattr(clusterer, "probabilities_", np.zeros_like(labels, dtype=float))
    sizes = _cluster_sizes(labels)
    outliers = (labels == -1) | (probabilities < probability_threshold)

    annotated = df.copy()
    annotated[cluster_column] = labels
    annotated[probability_column] = probabilities
    annotated[size_column] = sizes
    annotated[outlier_column] = outliers
    return annotated, labels
