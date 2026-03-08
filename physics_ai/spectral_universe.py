"""Eigenmode-driven universe generators."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np

from .backend import as_xp, get_xp, to_numpy


UniverseType = Literal["random", "spectral", "harmonic", "phi"]


@dataclass
class SpectralConfig:
    size: int = 64
    modes: int = 5
    k_min: int = 1
    k_max: int = 8
    seed: int | None = None


@dataclass
class HarmonicConfig:
    size: int = 64
    base: float = 2.0
    harmonics: int = 5


@dataclass
class PhiConfig:
    size: int = 64


def generate_spectral_field(config: SpectralConfig) -> np.ndarray:
    rng = np.random.default_rng(config.seed)
    xp = get_xp()
    x = xp.linspace(0, 2 * xp.pi, config.size)
    y = xp.linspace(0, 2 * xp.pi, config.size)
    xx, yy = xp.meshgrid(x, y)
    field = xp.zeros((config.size, config.size))

    for _ in range(config.modes):
        kx = rng.integers(config.k_min, config.k_max + 1)
        ky = rng.integers(config.k_min, config.k_max + 1)
        phase = rng.random() * 2 * np.pi
        amp = rng.random()
        field += amp * xp.sin(kx * xx + ky * yy + phase)

    return to_numpy(field)


def generate_harmonic_field(config: HarmonicConfig) -> np.ndarray:
    xp = get_xp()
    x = xp.linspace(0, 2 * xp.pi, config.size)
    xx, yy = xp.meshgrid(x, x)
    field = xp.zeros((config.size, config.size))
    for n in range(1, config.harmonics + 1):
        field += (1 / n) * xp.sin(config.base * n * xx) * xp.sin(config.base * n * yy)
    return to_numpy(field)


def generate_phi_field(config: PhiConfig) -> np.ndarray:
    phi = (1 + 5 ** 0.5) / 2
    xp = get_xp()
    x = xp.linspace(0, 2 * xp.pi, config.size)
    base = xp.sin(x) + xp.sin(phi * x) + xp.sin(x / phi)
    field = xp.outer(base, base)
    return to_numpy(field)


def generate_universe_field(
    universe_type: UniverseType,
    size: int = 64,
    seed: int | None = None,
) -> np.ndarray:
    if universe_type == "spectral":
        return generate_spectral_field(SpectralConfig(size=size, seed=seed))
    if universe_type == "harmonic":
        return generate_harmonic_field(HarmonicConfig(size=size))
    if universe_type == "phi":
        return generate_phi_field(PhiConfig(size=size))
    return np.random.default_rng(seed).random((size, size))
