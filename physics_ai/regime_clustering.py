"""Regime clustering utilities using HDBSCAN."""

from __future__ import annotations

from typing import Tuple

import numpy as np
import pandas as pd


def _lazy_import_hdbscan():
    try:
        import hdbscan  # type: ignore
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("hdbscan is required for regime clustering.") from exc
    return hdbscan


def _cluster_sizes(labels: np.ndarray) -> np.ndarray:
    sizes = np.zeros_like(labels, dtype=int)
    if labels.size == 0:
        return sizes
    unique, counts = np.unique(labels[labels >= 0], return_counts=True)
    size_map = dict(zip(unique.tolist(), counts.tolist()))
    for idx, label in enumerate(labels):
        sizes[idx] = size_map.get(int(label), 0)
    return sizes


def cluster_atlas(
    df: pd.DataFrame,
    min_cluster_size: int = 15,
    min_samples: int = 5,
    cluster_column: str = "cluster_id",
    probability_column: str = "cluster_probability",
    size_column: str = "cluster_size",
    x_column: str = "atlas_x",
    y_column: str = "atlas_y",
) -> Tuple[pd.DataFrame, np.ndarray]:
    """Cluster atlas coordinates and return annotated dataframe + labels."""
    if x_column not in df.columns or y_column not in df.columns:
        annotated = df.copy()
        annotated[cluster_column] = -1
        annotated[probability_column] = 0.0
        annotated[size_column] = 0
        return annotated, np.array([])

    coords = df[[x_column, y_column]].to_numpy(dtype=float)
    if coords.shape[0] < 2:
        annotated = df.copy()
        annotated[cluster_column] = -1
        annotated[probability_column] = 0.0
        annotated[size_column] = 0
        return annotated, np.array([-1] * coords.shape[0])

    hdbscan = _lazy_import_hdbscan()
    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=min_cluster_size,
        min_samples=min_samples,
    )
    labels = clusterer.fit_predict(coords)
    probabilities = getattr(clusterer, "probabilities_", np.zeros_like(labels, dtype=float))
    sizes = _cluster_sizes(labels)

    annotated = df.copy()
    annotated[cluster_column] = labels
    annotated[probability_column] = probabilities
    annotated[size_column] = sizes
    return annotated, labels
