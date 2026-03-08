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


def detect_surprises(
    df: pd.DataFrame,
    score_threshold: float = 8.0,
    novelty_threshold: float = 1.0,
    distance_threshold: float = 0.5,
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
    mask = (scores > score_threshold) & (novelty > novelty_threshold) & (distances > distance_threshold)
    return df.loc[mask]


def annotate_surprise(
    df: pd.DataFrame,
    score_threshold: float = 8.0,
    novelty_threshold: float = 1.0,
    distance_threshold: float = 0.5,
    score_column: str = "score",
    novelty_column: str = "novelty_bonus",
    x_column: str = "atlas_x",
    y_column: str = "atlas_y",
) -> pd.DataFrame:
    """Add atlas distance + surprise flags to the dataframe."""
    if x_column not in df.columns or y_column not in df.columns:
        annotated = df.copy()
        annotated["atlas_distance"] = 0.0
        annotated["surprise"] = False
        return annotated
    coords = df[[x_column, y_column]].to_numpy(dtype=float)
    distances = compute_atlas_distance(coords)
    scores = df.get(score_column, pd.Series(0.0, index=df.index)).fillna(0.0)
    novelty = df.get(novelty_column, pd.Series(0.0, index=df.index)).fillna(0.0)
    surprise = (scores > score_threshold) & (novelty > novelty_threshold) & (distances > distance_threshold)
    annotated = df.copy()
    annotated["atlas_distance"] = distances
    annotated["surprise"] = surprise
    return annotated
