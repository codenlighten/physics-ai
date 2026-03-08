"""Renormalization utilities for multi-scale analysis."""

from __future__ import annotations

from typing import Dict, Any, List

import numpy as np


def coarse_grain(field: np.ndarray) -> np.ndarray:
    return (
        field[0::2, 0::2]
        + field[1::2, 0::2]
        + field[0::2, 1::2]
        + field[1::2, 1::2]
    ) / 4.0


def coarse_grain_frames(frames: np.ndarray) -> np.ndarray:
    return np.array([coarse_grain(frame) for frame in frames])


def _temporal_stats(frames: np.ndarray) -> Dict[str, float | int]:
    magnitudes = np.abs(frames)
    signal = magnitudes.mean(axis=(1, 2))
    spectrum = np.abs(np.fft.rfft(signal))
    dominant = int(np.argmax(spectrum)) if spectrum.size else 0
    energy_series = np.sum(magnitudes ** 2, axis=(1, 2))
    mean_energy = float(np.mean(energy_series)) if np.mean(energy_series) != 0 else 1.0
    energy_drift_ratio = float(np.std(energy_series) / mean_energy)
    return {
        "dominant_temporal_freq": dominant,
        "energy_drift_ratio": energy_drift_ratio,
        "variance": float(np.var(magnitudes)),
    }


def build_scales(frames: np.ndarray, min_size: int = 8) -> List[np.ndarray]:
    scales: List[np.ndarray] = []
    current = np.abs(frames)
    while current.shape[1] >= min_size and current.shape[2] >= min_size:
        scales.append(current)
        if current.shape[1] < 2 or current.shape[2] < 2:
            break
        current = coarse_grain_frames(current)
    return scales


def analyze_scales(frames: np.ndarray) -> Dict[str, Any]:
    scales = build_scales(frames)
    metrics = []
    for scale in scales:
        stat = _temporal_stats(scale)
        stat["size"] = int(scale.shape[1])
        metrics.append(stat)
    if not metrics:
        return {"scales": [], "invariance_score": 0.0, "energy_flow": []}
    dominant_freqs = [m["dominant_temporal_freq"] for m in metrics]
    drift_ratios = [m["energy_drift_ratio"] for m in metrics]
    freq_std = float(np.std(dominant_freqs))
    drift_std = float(np.std(drift_ratios))
    invariance_score = float(1.0 / (1.0 + freq_std + drift_std))
    return {
        "scales": metrics,
        "invariance_score": invariance_score,
        "energy_flow": drift_ratios,
    }
