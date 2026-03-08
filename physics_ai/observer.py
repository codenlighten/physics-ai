"""Observation utilities for simulation states."""

from __future__ import annotations

from typing import Dict, Any, List, Iterable

import numpy as np

from .backend import as_xp, get_xp, to_numpy

from .geometry_frequency import geometry_frequency_features
from .group_theory import classify_group, rotation_symmetry, reflection_symmetry, so2_symmetry_score
from .defect_detector import defect_summary
from .particle_detector import particle_summary


def observe(grid: np.ndarray) -> Dict[str, Any]:
    spectrum = np.abs(np.fft.fft2(grid))
    dominant_index = np.unravel_index(np.argmax(spectrum), spectrum.shape)
    dominant_freq = float(max(dominant_index))
    spectrum_sum = float(np.sum(spectrum))
    if spectrum_sum == 0:
        spectral_entropy = 0.0
    else:
        probs = spectrum.flatten() / spectrum_sum
        entropy = -np.sum(probs * np.log(probs + 1e-12))
        spectral_entropy = float(entropy / np.log(probs.size)) if probs.size > 1 else 0.0
    energy = grid ** 2
    energy_sum = float(np.sum(energy)) if np.sum(energy) != 0 else 1.0
    energy_localization = float(np.max(energy) / energy_sum)
    rotation_order, rotation_score = rotation_symmetry(grid)
    reflection_score = reflection_symmetry(grid)
    so2_score = so2_symmetry_score(grid)

    metrics: Dict[str, Any] = {
        "energy": float(np.sum(grid ** 2)),
        "variance": float(np.var(grid)),
        "peak": float(np.max(grid)),
        "dominant_frequency": dominant_freq,
        "spectrum_mean": float(np.mean(spectrum)),
        "spectral_entropy": spectral_entropy,
        "energy_localization": energy_localization,
        "symmetry_group": classify_group(grid),
        "rotation_order": rotation_order,
        "rotation_score": rotation_score,
        "reflection_score": reflection_score,
        "so2_score": so2_score,
    }
    metrics.update(geometry_frequency_features(grid))
    metrics.update(defect_summary(grid))
    return metrics


def observe_multifield(fields: Dict[str, np.ndarray]) -> Dict[str, Any]:
    combined: Dict[str, Any] = {}
    energies = []
    variances = []
    entropies = []
    localizations = []
    defect_densities = []
    vortex_counts = []
    for name, field in fields.items():
        metrics = observe(field)
        for key, value in metrics.items():
            combined[f"{name}_{key}"] = value
        energies.append(float(metrics.get("energy", 0.0)))
        variances.append(float(metrics.get("variance", 0.0)))
        entropies.append(float(metrics.get("spectral_entropy", 0.0)))
        localizations.append(float(metrics.get("energy_localization", 0.0)))
        defect_densities.append(float(metrics.get("defect_density", 0.0)))
        vortex_counts.append(float(metrics.get("vortex_count", 0.0)))

    if variances:
        combined["variance"] = float(np.mean(variances))
    if energies:
        combined["energy"] = float(np.mean(energies))
    if entropies:
        combined["spectral_entropy"] = float(np.mean(entropies))
    if localizations:
        combined["energy_localization"] = float(np.max(localizations))
    if defect_densities:
        combined["defect_density"] = float(np.mean(defect_densities))
    if vortex_counts:
        combined["vortex_count"] = float(np.sum(vortex_counts))

    field_names = list(fields.keys())
    if len(field_names) >= 2:
        first = fields[field_names[0]].ravel()
        second = fields[field_names[1]].ravel()
        if first.size and second.size:
            first_norm = (first - first.mean()) / (first.std() + 1e-6)
            second_norm = (second - second.mean()) / (second.std() + 1e-6)
            corr = float(np.mean(first_norm * second_norm))
        else:
            corr = 0.0
        combined["cross_field_corr"] = corr
    return combined


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
    metrics = {
        "temporal_energy_start": start_energy,
        "temporal_energy_end": end_energy,
        "temporal_energy_drift": end_energy - start_energy,
        "temporal_energy_drift_ratio": energy_drift_ratio,
        "temporal_momentum_drift_ratio": momentum_drift_ratio,
        "temporal_fft": temporal_fft(frames),
        "temporal_signal": [float(value) for value in signal],
    }
    metrics.update(particle_summary(frames))
    return metrics


def observe_temporal_multi(frames: np.ndarray, field_names: Iterable[str]) -> Dict[str, Any]:
    metrics: Dict[str, Any] = {}
    names = list(field_names)
    if frames.ndim < 4:
        return metrics
    for idx, name in enumerate(names):
        field_frames = frames[:, idx]
        field_metrics = observe_temporal(field_frames)
        for key, value in field_metrics.items():
            metrics[f"{name}_{key}"] = value
        if "temporal_signal" in field_metrics:
            metrics[f"temporal_signal_{name}"] = field_metrics["temporal_signal"]
    if names:
        first_signal = metrics.get(f"{names[0]}_temporal_signal", [])
        if len(names) > 1:
            second_signal = metrics.get(f"{names[1]}_temporal_signal", [])
        else:
            second_signal = []
        if first_signal and second_signal:
            first_arr = np.array(first_signal, dtype=float)
            second_arr = np.array(second_signal, dtype=float)
            if first_arr.size == second_arr.size:
                first_norm = (first_arr - first_arr.mean()) / (first_arr.std() + 1e-6)
                second_norm = (second_arr - second_arr.mean()) / (second_arr.std() + 1e-6)
                metrics["cross_field_temporal_corr"] = float(np.mean(first_norm * second_norm))
        signals = [
            np.array(metrics.get(f"{name}_temporal_signal", []), dtype=float) for name in names
        ]
        if signals and all(signal.size for signal in signals):
            combined_signal = np.mean(signals, axis=0)
            metrics["temporal_signal"] = [float(value) for value in combined_signal]
        ffts = [metrics.get(f"{name}_temporal_fft", []) for name in names]
        if ffts and all(len(fft) for fft in ffts):
            min_len = min(len(fft) for fft in ffts)
            fft_arrays = np.array([fft[:min_len] for fft in ffts], dtype=float)
            metrics["temporal_fft"] = [float(value) for value in np.mean(fft_arrays, axis=0)]
    particle_counts = [
        float(metrics.get(f"{name}_particle_count", 0.0)) for name in names
    ]
    particle_scores = [
        float(metrics.get(f"{name}_particle_score", 0.0)) for name in names
    ]
    temporal_drifts = [
        float(metrics.get(f"{name}_temporal_energy_drift_ratio", 0.0)) for name in names
    ]
    if particle_counts:
        metrics["particle_count"] = float(np.mean(particle_counts))
    if particle_scores:
        metrics["particle_score"] = float(np.mean(particle_scores))
    if temporal_drifts:
        metrics["temporal_energy_drift_ratio"] = float(np.mean(temporal_drifts))
    return metrics
