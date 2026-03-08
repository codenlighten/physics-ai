"""Geometry-driven universe utilities for emergent gravity."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple, Dict, Any

import numpy as np

from .resonant_spectrum import spectrum_summary


@dataclass
class GeometryConfig:
    size: int = 64
    steps: int = 60
    dt: float = 0.05
    alpha: float = 0.2
    seed: int | None = None
    resonance_modes: int = 4


def metric_field(size: int) -> np.ndarray:
    g = np.zeros((size, size, 2, 2))
    g[:, :, 0, 0] = 1.0
    g[:, :, 1, 1] = 1.0
    return g


def curvature_update(metric: np.ndarray, rho: np.ndarray, alpha: float) -> np.ndarray:
    updated = metric.copy()
    updated[:, :, 0, 0] += alpha * rho
    updated[:, :, 1, 1] += alpha * rho
    return updated


def geodesic_step(position: np.ndarray, velocity: np.ndarray, metric: np.ndarray, dt: float) -> Tuple[np.ndarray, np.ndarray]:
    grad_x, grad_y = np.gradient(metric[:, :, 0, 0])
    x_idx = int(np.clip(position[0], 0, metric.shape[0] - 1))
    y_idx = int(np.clip(position[1], 0, metric.shape[1] - 1))
    acceleration = -np.array([grad_x[x_idx, y_idx], grad_y[x_idx, y_idx]])
    velocity = velocity + acceleration * dt
    position = position + velocity * dt
    position = np.clip(position, 0, metric.shape[0] - 1)
    return position, velocity


def simulate_geometry(config: GeometryConfig) -> Dict[str, Any]:
    rng = np.random.default_rng(config.seed)
    metric = metric_field(config.size)
    rho = rng.random((config.size, config.size))
    metric = curvature_update(metric, rho, config.alpha)

    position = np.array([config.size / 2, config.size / 2], dtype=float)
    velocity = rng.normal(scale=0.3, size=2)
    trajectory = []

    for _ in range(config.steps):
        position, velocity = geodesic_step(position, velocity, metric, config.dt)
        trajectory.append(position.copy())

    trajectory = np.array(trajectory)
    curvature_strength = float(np.mean(rho))
    return {
        "metric": metric,
        "rho": rho,
        "trajectory": trajectory,
        "curvature_strength": curvature_strength,
        "trajectory_length": float(len(trajectory)),
    }


def resonant_rho(size: int, modes: int, seed: int | None = None) -> np.ndarray:
    rng = np.random.default_rng(seed)
    x = np.linspace(0, 2 * np.pi, size)
    y = np.linspace(0, 2 * np.pi, size)
    xx, yy = np.meshgrid(x, y)
    field = np.zeros((size, size))
    for _ in range(modes):
        kx = rng.integers(1, 6)
        ky = rng.integers(1, 6)
        phase = rng.random() * 2 * np.pi
        amp = rng.random()
        field += amp * np.sin(kx * xx + ky * yy + phase)
    return np.abs(field)


def resonance_spectrum(field: np.ndarray, top_k: int = 5) -> Dict[str, Any]:
    return spectrum_summary(field, k=top_k)


def simulate_resonant_geometry(config: GeometryConfig) -> Dict[str, Any]:
    rng = np.random.default_rng(config.seed)
    metric = metric_field(config.size)
    rho = resonant_rho(config.size, config.resonance_modes, seed=config.seed)
    metric = curvature_update(metric, rho, config.alpha)

    position = np.array([config.size / 2, config.size / 2], dtype=float)
    velocity = rng.normal(scale=0.3, size=2)
    trajectory = []

    for _ in range(config.steps):
        position, velocity = geodesic_step(position, velocity, metric, config.dt)
        trajectory.append(position.copy())

    trajectory = np.array(trajectory)
    curvature_strength = float(np.mean(rho))
    resonance_strength = float(np.std(rho))
    spectrum = resonance_spectrum(rho)
    return {
        "metric": metric,
        "rho": rho,
        "trajectory": trajectory,
        "curvature_strength": curvature_strength,
        "trajectory_length": float(len(trajectory)),
        "resonance_strength": resonance_strength,
        "resonance_spectrum": spectrum,
    }
