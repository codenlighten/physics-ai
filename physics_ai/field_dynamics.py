"""Field dynamics simulators for time-evolving universes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

import numpy as np

from .backend import as_xp, get_xp, to_numpy


def laplacian(field: np.ndarray) -> np.ndarray:
    xp = get_xp()
    data = as_xp(field)
    return (
        xp.roll(data, 1, 0)
        + xp.roll(data, -1, 0)
        + xp.roll(data, 1, 1)
        + xp.roll(data, -1, 1)
        - 4 * data
    )


@dataclass
class WaveConfig:
    steps: int = 60
    wave_speed: float = 1.0
    dt: float = 0.1


@dataclass
class DiffusionConfig:
    steps: int = 60
    diffusion: float = 0.1


@dataclass
class ReactionDiffusionConfig:
    steps: int = 80
    feed: float = 0.055
    kill: float = 0.062
    diffusion_a: float = 1.0
    diffusion_b: float = 0.5


@dataclass
class OscillatorConfig:
    steps: int = 200
    k: float = 1.0
    dt: float = 0.01
    q0: float = 1.0


@dataclass
class SchrodingerConfig:
    steps: int = 80
    dt: float = 0.01


def simulate_wave(field: np.ndarray, config: WaveConfig) -> np.ndarray:
    xp = get_xp()
    field = as_xp(field)
    velocity = xp.zeros_like(field)
    frames = []
    for _ in range(config.steps):
        accel = (config.wave_speed ** 2) * laplacian(field)
        velocity = velocity + accel * config.dt
        field = field + velocity * config.dt
        frames.append(field.copy())
    return to_numpy(xp.stack(frames))


def simulate_diffusion(field: np.ndarray, config: DiffusionConfig) -> np.ndarray:
    xp = get_xp()
    field = as_xp(field)
    frames = []
    for _ in range(config.steps):
        field = field + config.diffusion * laplacian(field)
        frames.append(field.copy())
    return to_numpy(xp.stack(frames))


def simulate_reaction_diffusion(
    field_a: np.ndarray,
    field_b: np.ndarray,
    config: ReactionDiffusionConfig,
) -> Tuple[np.ndarray, np.ndarray]:
    field_a = as_xp(field_a)
    field_b = as_xp(field_b)
    for _ in range(config.steps):
        lap_a = laplacian(field_a)
        lap_b = laplacian(field_b)
        reaction = field_a * field_b * field_b
        field_a = field_a + config.diffusion_a * lap_a - reaction + config.feed * (1 - field_a)
        field_b = field_b + config.diffusion_b * lap_b + reaction - config.kill * field_b
    return to_numpy(field_a), to_numpy(field_b)


def simulate_oscillator(config: OscillatorConfig) -> np.ndarray:
    q = config.q0
    v = 0.0
    positions = []
    for _ in range(config.steps):
        accel = -config.k * q
        v += accel * config.dt
        q += v * config.dt
        positions.append(q)
    return np.array(positions, dtype=float)


def simulate_schrodinger(field: np.ndarray, config: SchrodingerConfig) -> np.ndarray:
    frames = []
    xp = get_xp()
    state = as_xp(field).astype(np.complex128)
    for _ in range(config.steps):
        lap = laplacian(state)
        state = state + 1j * config.dt * lap
        frames.append(state.copy())
    return to_numpy(xp.stack(frames))
