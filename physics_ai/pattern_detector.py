"""Simple clustering for observation patterns."""

from __future__ import annotations

from typing import Tuple

import numpy as np


def kmeans(points: np.ndarray, k: int, max_iter: int = 50, seed: int = 0) -> Tuple[np.ndarray, np.ndarray]:
    if len(points) == 0:
        return np.array([]), np.array([])
    rng = np.random.default_rng(seed)
    indices = rng.choice(len(points), size=k, replace=False)
    centroids = points[indices]
    labels = np.zeros(len(points), dtype=int)

    for _ in range(max_iter):
        distances = np.linalg.norm(points[:, None, :] - centroids[None, :, :], axis=2)
        new_labels = np.argmin(distances, axis=1)
        if np.array_equal(labels, new_labels):
            break
        labels = new_labels
        for idx in range(k):
            cluster_points = points[labels == idx]
            if len(cluster_points) > 0:
                centroids[idx] = cluster_points.mean(axis=0)
    return labels, centroids
