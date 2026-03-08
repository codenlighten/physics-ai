"""Spectral Lagrangian engine operating on eigenmode amplitudes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

import numpy as np


@dataclass
class SpectralConfig:
    modes: int = 6
    steps: int = 120
    dt: float = 0.05
    omega_min: float = 0.5
    omega_max: float = 2.0
    seed: int | None = None


def generate_modes(size: int, modes: int, seed: int | None = None) -> List[np.ndarray]:
    rng = np.random.default_rng(seed)
    x = np.linspace(0, 2 * np.pi, size)
    y = np.linspace(0, 2 * np.pi, size)
    xx, yy = np.meshgrid(x, y)
    basis: List[np.ndarray] = []
    for _ in range(modes):
        kx = rng.integers(1, 6)
        ky = rng.integers(1, 6)
        phase = rng.random() * 2 * np.pi
        basis.append(np.sin(kx * xx + ky * yy + phase))
    return basis


def step_modes(a: np.ndarray, v: np.ndarray, omegas: np.ndarray, dt: float) -> Tuple[np.ndarray, np.ndarray]:
    accel = -(omegas ** 2) * a
    v = v + accel * dt
    a = a + v * dt
    return a, v


def simulate_modes(config: SpectralConfig) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(config.seed)
    omegas = rng.uniform(config.omega_min, config.omega_max, size=config.modes)
    amplitudes = rng.normal(scale=0.5, size=config.modes)
    velocities = np.zeros(config.modes)
    history = []
    for _ in range(config.steps):
        amplitudes, velocities = step_modes(amplitudes, velocities, omegas, config.dt)
        history.append(amplitudes.copy())
    return np.array(history), omegas, velocities


def reconstruct_field(amplitudes: np.ndarray, basis: List[np.ndarray]) -> np.ndarray:
    field = np.zeros_like(basis[0])
    for amp, mode in zip(amplitudes, basis):
        field += amp * mode
    return field


def simulate_field_from_modes(size: int, config: SpectralConfig) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    basis = generate_modes(size=size, modes=config.modes, seed=config.seed)
    history, omegas, velocities = simulate_modes(config)
    frames = []
    for amplitudes in history:
        frames.append(reconstruct_field(amplitudes, basis))
    return np.array(frames), omegas, velocities
