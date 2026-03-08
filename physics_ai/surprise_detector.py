"""Surprise detection utilities for novel physics regimes."""

from __future__ import annotations

from typing import Iterable

import numpy as np
import pandas as pd


def compute_atlas_distance(coords: np.ndarray) -> np.ndarray:
    """Compute distance to nearest neighbor for each point."""
    if coords.size == 0:
        return np.array([])
    if coords.shape[0] == 1:
        return np.array([0.0])
    diffs = coords[:, None, :] - coords[None, :, :]
    distances = np.linalg.norm(diffs, axis=2)
    np.fill_diagonal(distances, np.inf)
    return np.min(distances, axis=1)


def _mean_knn_distance(coords: np.ndarray, k: int = 10) -> np.ndarray:
    if coords.size == 0:
        return np.array([])
    if coords.shape[0] == 1:
        return np.array([0.0])
    diffs = coords[:, None, :] - coords[None, :, :]
    distances = np.linalg.norm(diffs, axis=2)
    np.fill_diagonal(distances, np.inf)
    k = max(1, min(k, coords.shape[0] - 1))
    nearest = np.partition(distances, kth=k, axis=1)[:, :k]
    return np.mean(nearest, axis=1)


def compute_density_scores(
    coords: np.ndarray,
    k: int = 10,
    epsilon: float = 1e-6,
) -> tuple[np.ndarray, np.ndarray]:
    """Return (local_density, density_score) from k-NN distances."""
    if coords.size == 0:
        return np.array([]), np.array([])
    mean_dist = _mean_knn_distance(coords, k=k)
    density_score = 1.0 / (mean_dist + epsilon)
    max_score = float(np.max(density_score)) if density_score.size else 1.0
    if max_score <= 0.0:
        local_density = np.zeros_like(density_score)
    else:
        local_density = density_score / max_score
    return local_density, density_score


def detect_surprises(
    df: pd.DataFrame,
    score_threshold: float = 8.0,
    novelty_threshold: float = 1.0,
    distance_threshold: float = 0.5,
    density_threshold: float | None = None,
    density_percentile: float = 10.0,
    density_k: int = 10,
    cluster_probability_threshold: float = 0.3,
    cluster_id_column: str = "cluster_id",
    cluster_probability_column: str = "cluster_probability",
    score_column: str = "score",
    novelty_column: str = "novelty_bonus",
    x_column: str = "atlas_x",
    y_column: str = "atlas_y",
) -> pd.DataFrame:
    """Return rows that pass the surprise thresholds."""
    if x_column not in df.columns or y_column not in df.columns:
        return df.iloc[0:0]
    scores = df.get(score_column, pd.Series(0.0, index=df.index)).fillna(0.0)
    novelty = df.get(novelty_column, pd.Series(0.0, index=df.index)).fillna(0.0)
    coords = df[[x_column, y_column]].to_numpy(dtype=float)
    distances = compute_atlas_distance(coords)
    local_density, _ = compute_density_scores(coords, k=density_k)
    if density_threshold is None:
        density_threshold = float(np.percentile(local_density, density_percentile))
    if cluster_id_column in df.columns and cluster_probability_column in df.columns:
        cluster_id = df[cluster_id_column].fillna(-1).astype(int)
        cluster_prob = df[cluster_probability_column].fillna(0.0).astype(float)
        cluster_mask = (cluster_id == -1) | (cluster_prob < cluster_probability_threshold)
    else:
        cluster_mask = pd.Series(True, index=df.index)
    mask = (
        (scores > score_threshold)
        & (novelty > novelty_threshold)
        & (distances > distance_threshold)
        & (local_density < density_threshold)
        & (cluster_mask)
    )
    return df.loc[mask]


def annotate_surprise(
    df: pd.DataFrame,
    score_threshold: float = 8.0,
    novelty_threshold: float = 1.0,
    distance_threshold: float = 0.5,
    density_threshold: float | None = None,
    density_percentile: float = 10.0,
    density_k: int = 10,
    cluster_probability_threshold: float = 0.3,
    cluster_id_column: str = "cluster_id",
    cluster_probability_column: str = "cluster_probability",
    score_column: str = "score",
    novelty_column: str = "novelty_bonus",
    x_column: str = "atlas_x",
    y_column: str = "atlas_y",
) -> pd.DataFrame:
    """Add atlas distance + surprise flags to the dataframe."""
    if x_column not in df.columns or y_column not in df.columns:
        annotated = df.copy()
        annotated["atlas_distance"] = 0.0
        annotated["local_density"] = 0.0
        annotated["density_score"] = 0.0
        annotated["density_surprise"] = False
        annotated["cluster_outlier"] = False
        annotated["surprise"] = False
        return annotated
    coords = df[[x_column, y_column]].to_numpy(dtype=float)
    distances = compute_atlas_distance(coords)
    local_density, density_score = compute_density_scores(coords, k=density_k)
    if density_threshold is None:
        density_threshold = float(np.percentile(local_density, density_percentile))
    scores = df.get(score_column, pd.Series(0.0, index=df.index)).fillna(0.0)
    novelty = df.get(novelty_column, pd.Series(0.0, index=df.index)).fillna(0.0)
    if cluster_id_column in df.columns and cluster_probability_column in df.columns:
        cluster_id = df[cluster_id_column].fillna(-1).astype(int)
        cluster_prob = df[cluster_probability_column].fillna(0.0).astype(float)
        cluster_outlier = (cluster_id == -1) | (cluster_prob < cluster_probability_threshold)
    else:
        cluster_outlier = pd.Series(True, index=df.index)
    density_surprise = (
        (scores > score_threshold)
        & (novelty > novelty_threshold)
        & (distances > distance_threshold)
        & (local_density < density_threshold)
        & (cluster_outlier)
    )
    annotated = df.copy()
    annotated["atlas_distance"] = distances
    annotated["local_density"] = local_density
    annotated["density_score"] = density_score
    annotated["density_surprise"] = density_surprise
    annotated["cluster_outlier"] = cluster_outlier
    annotated["surprise"] = density_surprise
    return annotated
