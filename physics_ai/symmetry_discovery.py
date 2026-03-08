"""Symmetry discovery utilities for invariance detection."""

from __future__ import annotations

from typing import Iterable, Dict

import numpy as np


def _normalized_error(base: np.ndarray, compare: np.ndarray) -> float:
    magnitude = np.mean(np.abs(base)) + 1e-8
    return float(np.mean(np.abs(base - compare)) / magnitude)


def translation_invariance(grid: np.ndarray, shifts: Iterable[int] = (1, 2, 3)) -> float:
    base = np.asarray(grid)
    if base.size == 0:
        return 0.0
    magnitude = np.abs(base)
    errors = []
    for shift in shifts:
        rolled_x = np.roll(magnitude, shift, axis=0)
        rolled_y = np.roll(magnitude, shift, axis=1)
        errors.append(_normalized_error(magnitude, rolled_x))
        errors.append(_normalized_error(magnitude, rolled_y))
    mean_error = float(np.mean(errors)) if errors else 1.0
    return float(1.0 / (1.0 + mean_error))


def scale_invariance(grid: np.ndarray, scales: Iterable[int] = (2, 4)) -> float:
    base = np.asarray(grid)
    if base.size == 0:
        return 0.0
    magnitude = np.abs(base)
    errors = []
    for scale in scales:
        if scale <= 1:
            continue
        size_x, size_y = magnitude.shape[:2]
        trimmed_x = size_x - (size_x % scale)
        trimmed_y = size_y - (size_y % scale)
        if trimmed_x < scale or trimmed_y < scale:
            continue
        trimmed = magnitude[:trimmed_x, :trimmed_y]
        down = trimmed.reshape(trimmed_x // scale, scale, trimmed_y // scale, scale).mean(axis=(1, 3))
        up = np.repeat(np.repeat(down, scale, axis=0), scale, axis=1)
        errors.append(_normalized_error(trimmed, up))
    mean_error = float(np.mean(errors)) if errors else 1.0
    return float(1.0 / (1.0 + mean_error))


def phase_invariance(grid: np.ndarray, phases: Iterable[float] = (np.pi / 2, np.pi)) -> float:
    base = np.asarray(grid)
    if base.size == 0 or not np.iscomplexobj(base):
        return 0.0
    errors = []
    for phase in phases:
        rotated = base * np.exp(1j * phase)
        errors.append(_normalized_error(base, rotated))
    mean_error = float(np.mean(errors)) if errors else 1.0
    return float(1.0 / (1.0 + mean_error))


def symmetry_profile(grid: np.ndarray) -> Dict[str, float]:
    return {
        "translation_invariance": translation_invariance(grid),
        "scale_invariance": scale_invariance(grid),
        "phase_invariance": phase_invariance(grid),
    }
