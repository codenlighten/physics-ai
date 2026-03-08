"""Localized perturbations for symmetry-breaking initial conditions."""

from __future__ import annotations

from typing import Iterable, Sequence

import numpy as np


def apply_seed_perturbations(
    field: np.ndarray,
    rng: np.random.Generator,
    seed_count: int,
    seed_types: Sequence[str],
    amplitude_range: tuple[float, float],
    radius_range: tuple[float, float],
) -> np.ndarray:
    if seed_count <= 0:
        return field
    size_x, size_y = field.shape
    yy, xx = np.indices(field.shape)
    amp_min, amp_max = amplitude_range
    rad_min, rad_max = radius_range
    for _ in range(seed_count):
        seed_type = rng.choice(seed_types)
        x0 = int(rng.integers(0, size_x))
        y0 = int(rng.integers(0, size_y))
        radius = float(rng.uniform(rad_min, rad_max))
        amplitude = float(rng.uniform(amp_min, amp_max))
        dx = xx - y0
        dy = yy - x0
        r = np.sqrt(dx ** 2 + dy ** 2)

        if seed_type == "gaussian":
            field += amplitude * np.exp(-(r ** 2) / (2 * radius ** 2))
        elif seed_type == "dipole":
            offset = radius / 2
            r1 = np.sqrt((dx - offset) ** 2 + dy ** 2)
            r2 = np.sqrt((dx + offset) ** 2 + dy ** 2)
            field += amplitude * (
                np.exp(-(r1 ** 2) / (2 * radius ** 2))
                - np.exp(-(r2 ** 2) / (2 * radius ** 2))
            )
        elif seed_type == "ring":
            width = max(1.0, radius / 3)
            field += amplitude * np.exp(-((r - radius) ** 2) / (2 * width ** 2))
        elif seed_type == "spiral":
            angle = np.arctan2(dy, dx)
            field += amplitude * np.exp(-(r ** 2) / (2 * radius ** 2)) * np.sin(angle * 3 + r / radius)
    return field