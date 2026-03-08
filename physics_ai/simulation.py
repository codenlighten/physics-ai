"""Wave-based physics simulation utilities."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .backend import as_xp, get_xp, to_numpy


@dataclass
class WaveSimulation:
    size: int = 64
    dt: float = 0.1
    steps: int = 120
    wave_speed: float = 1.0
    wavelength: float = 8.0
    amplitude: float = 1.0
    pulse_position: int | None = None
    boundary: str = "torus"
    initial_field: np.ndarray | None = None

    def initialize(self) -> tuple[np.ndarray, np.ndarray]:
        xp = get_xp()
        if self.initial_field is not None:
            if self.initial_field.shape != (self.size, self.size):
                raise ValueError("Initial field shape does not match simulation size.")
            grid = as_xp(self.initial_field).astype(float, copy=True)
        else:
            x = xp.linspace(0, self.size - 1, self.size)
            y = xp.linspace(0, self.size - 1, self.size)
            xx, yy = xp.meshgrid(x, y)
            phase = 2 * xp.pi * (xx / self.wavelength)
            grid = self.amplitude * xp.sin(phase)
        if self.pulse_position is not None:
            pulse = max(0, min(self.size - 1, self.pulse_position))
            grid[pulse, pulse] += self.amplitude
        velocity = xp.zeros_like(grid)
        return grid, velocity

    def step(self, grid: np.ndarray, velocity: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        xp = get_xp()
        grid = as_xp(grid)
        velocity = as_xp(velocity)
        laplacian = (
            xp.roll(grid, 1, 0)
            + xp.roll(grid, -1, 0)
            + xp.roll(grid, 1, 1)
            + xp.roll(grid, -1, 1)
            - 4 * grid
        )
        velocity = velocity + (self.wave_speed ** 2) * laplacian * self.dt
        grid = grid + velocity * self.dt
        if self.boundary == "square":
            grid[0, :] = 0.0
            grid[-1, :] = 0.0
            grid[:, 0] = 0.0
            grid[:, -1] = 0.0
        return grid, velocity

    def run(self) -> np.ndarray:
        grid, velocity = self.initialize()
        for _ in range(self.steps):
            grid, velocity = self.step(grid, velocity)
        return to_numpy(grid)
