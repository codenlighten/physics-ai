"""Observation utilities for simulation states."""

from __future__ import annotations

from typing import Dict, Any, List

import numpy as np

from .backend import as_xp, get_xp, to_numpy

from .geometry_frequency import geometry_frequency_features
from .group_theory import classify_group, rotation_symmetry, reflection_symmetry, so2_symmetry_score


def observe(grid: np.ndarray) -> Dict[str, Any]:
    spectrum = np.abs(np.fft.fft2(grid))
    dominant_index = np.unravel_index(np.argmax(spectrum), spectrum.shape)
    dominant_freq = float(max(dominant_index))
    rotation_order, rotation_score = rotation_symmetry(grid)
    reflection_score = reflection_symmetry(grid)
    so2_score = so2_symmetry_score(grid)

    metrics: Dict[str, Any] = {
        "energy": float(np.sum(grid ** 2)),
        "variance": float(np.var(grid)),
        "peak": float(np.max(grid)),
        "dominant_frequency": dominant_freq,
        "spectrum_mean": float(np.mean(spectrum)),
        "symmetry_group": classify_group(grid),
        "rotation_order": rotation_order,
        "rotation_score": rotation_score,
        "reflection_score": reflection_score,
        "so2_score": so2_score,
    }
    metrics.update(geometry_frequency_features(grid))
    return metrics


def temporal_fft(frames: np.ndarray) -> List[float]:
    if frames.size == 0:
        return []
    xp = get_xp()
    signal = xp.mean(as_xp(frames), axis=(1, 2))
    spectrum = xp.abs(xp.fft.rfft(signal))
    return [float(value) for value in to_numpy(spectrum)]


def observe_temporal(frames: np.ndarray) -> Dict[str, Any]:
    if frames.size == 0:
        return {
            "temporal_energy_start": 0.0,
            "temporal_energy_end": 0.0,
            "temporal_energy_drift": 0.0,
            "temporal_energy_drift_ratio": 0.0,
            "temporal_momentum_drift_ratio": 0.0,
            "temporal_fft": [],
            "temporal_signal": [],
        }
    magnitudes = np.abs(frames)
    signal = magnitudes.mean(axis=(1, 2))
    energy_series = np.sum(magnitudes ** 2, axis=(1, 2))
    start_energy = float(energy_series[0])
    end_energy = float(energy_series[-1])
    mean_energy = float(np.mean(energy_series)) if np.mean(energy_series) != 0 else 1.0
    energy_drift_ratio = float(np.std(energy_series) / mean_energy)
    momentum_series = []
    for frame in magnitudes:
        grad_x, grad_y = np.gradient(frame)
        momentum_series.append(float(np.sum(grad_x ** 2 + grad_y ** 2)))
    momentum_mean = float(np.mean(momentum_series)) if np.mean(momentum_series) != 0 else 1.0
    momentum_drift_ratio = float(np.std(momentum_series) / momentum_mean)
    return {
        "temporal_energy_start": start_energy,
        "temporal_energy_end": end_energy,
        "temporal_energy_drift": end_energy - start_energy,
        "temporal_energy_drift_ratio": energy_drift_ratio,
        "temporal_momentum_drift_ratio": momentum_drift_ratio,
        "temporal_fft": temporal_fft(frames),
        "temporal_signal": [float(value) for value in signal],
    }
