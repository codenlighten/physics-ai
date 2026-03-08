"""Resonant spectrum extraction for geometry fields."""

from __future__ import annotations

from typing import Dict, Any, Tuple

import numpy as np

from .backend import as_xp, get_xp, to_numpy


def geometry_spectrum(field: np.ndarray) -> np.ndarray:
    xp = get_xp()
    fft = xp.fft.fft2(as_xp(field))
    power = xp.abs(fft) ** 2
    return to_numpy(power)


def dominant_modes(power: np.ndarray, k: int = 5) -> Tuple[np.ndarray, np.ndarray]:
    flat = power.flatten()
    if flat.size == 0:
        return np.array([], dtype=int), np.array([], dtype=int)
    idx = np.argsort(flat)[-k:]
    return np.unravel_index(idx, power.shape)


def resonance_strength(power: np.ndarray) -> float:
    total = float(np.sum(power))
    if total == 0:
        return 0.0
    peak = float(np.max(power))
    return peak / total


def spectrum_summary(field: np.ndarray, k: int = 5) -> Dict[str, Any]:
    power = geometry_spectrum(field)
    modes = dominant_modes(power, k=k)
    mode_pairs = list(zip(modes[0].tolist(), modes[1].tolist())) if modes[0].size else []
    return {
        "dominant_modes": mode_pairs,
        "resonance_strength": resonance_strength(power),
        "spectrum_mean": float(np.mean(power)),
    }
