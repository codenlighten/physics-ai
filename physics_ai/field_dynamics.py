"""Field dynamics simulators for time-evolving universes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

import numpy as np

from .backend import as_xp, get_xp, to_numpy


def laplacian(field: np.ndarray) -> np.ndarray:
    xp = get_xp()
    data = as_xp(field)
    axis0 = -2
    axis1 = -1
    return (
        xp.roll(data, 1, axis0)
        + xp.roll(data, -1, axis0)
        + xp.roll(data, 1, axis1)
        + xp.roll(data, -1, axis1)
        - 4 * data
    )


@dataclass
class WaveConfig:
    steps: int = 60
    wave_speed: float = 1.0
    dt: float = 0.1
    nonlinear_coeff: float = 0.0
    biharmonic_coeff: float = 0.0


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


@dataclass
class CoupledFieldConfig:
    steps: int = 80
    dt: float = 0.05
    diffusion_psi: float = 0.15
    diffusion_phi: float = 0.08
    coupling_linear: float = 0.6
    coupling_quadratic: float = 0.3
    coupling_cross: float = 0.25
    psi_cubic: float = 0.2
    phi_cubic: float = 0.15
    psi_decay: float = 0.05
    phi_decay: float = 0.04


def simulate_wave(field: np.ndarray, config: WaveConfig, return_xp: bool = False):
    xp = get_xp()
    field = as_xp(field)
    velocity = xp.zeros_like(field)
    frames = []
    for _ in range(config.steps):
        lap = laplacian(field)
        biharmonic = laplacian(lap) if config.biharmonic_coeff != 0 else 0.0
        nonlinear = -config.nonlinear_coeff * (field ** 3) if config.nonlinear_coeff != 0 else 0.0
        accel = (config.wave_speed ** 2) * lap + config.biharmonic_coeff * biharmonic + nonlinear
        velocity = velocity + accel * config.dt
        field = field + velocity * config.dt
        frames.append(field.copy())
    stacked = xp.stack(frames)
    return stacked if return_xp else to_numpy(stacked)


def simulate_diffusion(field: np.ndarray, config: DiffusionConfig, return_xp: bool = False):
    xp = get_xp()
    field = as_xp(field)
    frames = []
    for _ in range(config.steps):
        field = field + config.diffusion * laplacian(field)
        frames.append(field.copy())
    stacked = xp.stack(frames)
    return stacked if return_xp else to_numpy(stacked)


def simulate_reaction_diffusion(
    field_a: np.ndarray,
    field_b: np.ndarray,
    config: ReactionDiffusionConfig,
    return_xp: bool = False,
):
    xp = get_xp()
    field_a = as_xp(field_a)
    field_b = as_xp(field_b)
    for _ in range(config.steps):
        lap_a = laplacian(field_a)
        lap_b = laplacian(field_b)
        reaction = field_a * field_b * field_b
        field_a = field_a + config.diffusion_a * lap_a - reaction + config.feed * (1 - field_a)
        field_b = field_b + config.diffusion_b * lap_b + reaction - config.kill * field_b
    if return_xp:
        return field_a, field_b
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


def simulate_schrodinger(field: np.ndarray, config: SchrodingerConfig, return_xp: bool = False):
    frames = []
    xp = get_xp()
    state = as_xp(field).astype(np.complex128)
    for _ in range(config.steps):
        lap = laplacian(state)
        state = state + 1j * config.dt * lap
        frames.append(state.copy())
    stacked = xp.stack(frames)
    return stacked if return_xp else to_numpy(stacked)


def simulate_coupled_fields(
    psi_field: np.ndarray,
    phi_field: np.ndarray,
    config: CoupledFieldConfig,
    return_xp: bool = False,
):
    xp = get_xp()
    psi = as_xp(psi_field)
    phi = as_xp(phi_field)
    frames = []
    for _ in range(config.steps):
        lap_psi = laplacian(psi)
        lap_phi = laplacian(phi)
        dpsi = (
            config.diffusion_psi * lap_psi
            + config.coupling_linear * psi * phi
            + config.coupling_quadratic * (psi ** 2) * phi
            - config.psi_cubic * (psi ** 3)
            - config.psi_decay * psi
        )
        dphi = (
            config.diffusion_phi * lap_phi
            + config.coupling_cross * (phi ** 2) * psi
            - config.phi_cubic * (phi ** 3)
            - config.phi_decay * phi
        )
        psi = psi + dpsi * config.dt
        phi = phi + dphi * config.dt
        frames.append(xp.stack([psi.copy(), phi.copy()]))
    stacked = xp.stack(frames)
    return stacked if return_xp else to_numpy(stacked)
