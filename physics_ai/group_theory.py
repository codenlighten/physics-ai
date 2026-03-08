"""Symmetry group detection utilities."""

from __future__ import annotations

from typing import Dict, Callable, Iterable, Tuple

import numpy as np
from scipy.ndimage import rotate


def group_invariance(grid: np.ndarray, transform: Callable[[np.ndarray], np.ndarray]) -> float:
    """Return mean absolute difference between grid and a transformed version."""
    transformed = transform(grid)
    return float(np.mean(np.abs(grid - transformed)))


def rotation_symmetry(grid: np.ndarray, max_order: int = 12) -> Tuple[int, float]:
    """Detect rotational symmetry order by testing discrete rotations."""
    best_order = 1
    best_score = float("inf")
    for order in range(2, max_order + 1):
        angle = 360 / order
        rotated = np.rot90(grid, k=int(angle / 90) % 4)
        diff = np.mean(np.abs(grid - rotated))
        if diff < best_score:
            best_score = float(diff)
            best_order = order
    return best_order, best_score


def reflection_symmetry(grid: np.ndarray) -> float:
    """Measure reflection symmetry across the y-axis."""
    flipped = np.flip(grid, axis=1)
    return float(np.mean(np.abs(grid - flipped)))


def classify_group(grid: np.ndarray, max_order: int = 12, reflection_threshold: float = 0.05) -> str:
    """Classify a basic rotational/dihedral symmetry group."""
    rot_order, _ = rotation_symmetry(grid, max_order=max_order)
    ref_score = reflection_symmetry(grid)
    so2_score = so2_symmetry_score(grid)
    if so2_score < 0.02:
        return "SO2"
    if rot_order > 1 and ref_score < reflection_threshold:
        return f"D{rot_order}"
    if rot_order > 1:
        return f"C{rot_order}"
    return "C1"


def evaluate_group(
    grid: np.ndarray,
    transforms: Dict[str, Callable[[np.ndarray], np.ndarray]],
) -> Dict[str, float]:
    """Evaluate multiple transforms to build a symmetry signature."""
    return {name: group_invariance(grid, transform) for name, transform in transforms.items()}


def so2_symmetry_score(grid: np.ndarray, samples: int = 36) -> float:
    """Estimate continuous rotational symmetry by averaging rotation errors."""
    scores = []
    for i in range(1, samples):
        angle = 360 * i / samples
        rotated = rotate(grid, angle, reshape=False, order=1, mode="nearest")
        scores.append(float(np.mean(np.abs(grid - rotated))))
    return float(np.mean(scores)) if scores else float("inf")


def standard_transforms() -> Dict[str, Callable[[np.ndarray], np.ndarray]]:
    """Return a small library of basic transforms."""
    return {
        "translate": lambda g: np.roll(g, 1, axis=0),
        "rotate": lambda g: np.rot90(g),
        "reflect": lambda g: np.flip(g, axis=1),
    }
