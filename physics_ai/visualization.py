"""Visualization helpers for physics-first simulations."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence
import os

import numpy as np
import matplotlib

if not os.environ.get("DISPLAY"):
    matplotlib.use("Agg")

import matplotlib.pyplot as plt


def _prepare_field(field: np.ndarray) -> np.ndarray:
    if np.iscomplexobj(field):
        return np.abs(field)
    return np.asarray(field, dtype=float)


def plot_field(field: np.ndarray, title: str | None = None, cmap: str = "viridis") -> plt.Figure:
    data = _prepare_field(field)
    fig, ax = plt.subplots(figsize=(5, 4))
    im = ax.imshow(data, cmap=cmap, origin="lower")
    fig.colorbar(im, ax=ax, shrink=0.8)
    ax.set_title(title or "Field snapshot")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    return fig


def plot_spectrum(field: np.ndarray, title: str | None = None) -> plt.Figure:
    data = _prepare_field(field)
    spectrum = np.abs(np.fft.fftshift(np.fft.fft2(data)))
    fig, ax = plt.subplots(figsize=(5, 4))
    im = ax.imshow(np.log1p(spectrum), cmap="magma", origin="lower")
    fig.colorbar(im, ax=ax, shrink=0.8)
    ax.set_title(title or "Field spectrum")
    ax.set_xlabel("k_x")
    ax.set_ylabel("k_y")
    return fig


def plot_temporal_signal(signal: Sequence[float], title: str | None = None) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(5, 3))
    ax.plot(signal, color="tab:blue")
    ax.set_title(title or "Temporal signal")
    ax.set_xlabel("t")
    ax.set_ylabel("mean |field|")
    return fig


def plot_dispersion(dispersion: Dict[str, Any], title: str | None = None) -> Optional[plt.Figure]:
    k_vals = dispersion.get("k_values") if dispersion else None
    omega = dispersion.get("omega") if dispersion else None
    if not k_vals:
        return None
    fig, ax = plt.subplots(figsize=(5, 3))
    ax.scatter(k_vals, [omega for _ in k_vals], color="tab:orange", label="samples")
    coeffs = dispersion.get("coefficients", [])
    if coeffs:
        k_grid = np.linspace(min(k_vals), max(k_vals), 50)
        a, b, c = (coeffs + [0.0, 0.0, 0.0])[:3]
        omega_fit = a * k_grid ** 2 + b * k_grid + c
        ax.plot(k_grid, omega_fit, color="tab:red", label="fit")
    ax.set_title(title or f"Dispersion ({dispersion.get('law_type', 'unknown')})")
    ax.set_xlabel("k")
    ax.set_ylabel("omega")
    ax.legend(loc="best")
    return fig


def plot_particles(particles: Dict[str, Any], title: str | None = None) -> Optional[plt.Figure]:
    if not particles:
        return None
    tracks = particles.get("tracks", [])
    if not tracks:
        return None
    fig, ax = plt.subplots(figsize=(5, 4))
    for track in tracks:
        raw_positions = track.get("positions", [])
        if raw_positions and len(raw_positions[0]) == 3:
            positions = np.array([[p[1], p[2]] for p in raw_positions], dtype=float)
        else:
            positions = np.array(raw_positions, dtype=float)
        if positions.size == 0:
            continue
        ax.plot(positions[:, 1], positions[:, 0], marker="o", markersize=3, linewidth=1)
    ax.set_title(title or "Particle tracks")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.invert_yaxis()
    return fig


def plot_trajectory(trajectory: np.ndarray, title: str | None = None) -> Optional[plt.Figure]:
    if trajectory is None or np.asarray(trajectory).size == 0:
        return None
    data = np.asarray(trajectory, dtype=float)
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.plot(data[:, 1], data[:, 0], color="tab:green")
    ax.set_title(title or "Geometry trajectory")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.invert_yaxis()
    return fig


def render_summary(
    results: Dict[str, Any],
    output_dir: str | Path | None = None,
    show: bool = True,
    max_universes: int = 1,
) -> List[Path]:
    dataset = results.get("dataset", [])
    saved: List[Path] = []
    figures: List[plt.Figure] = []

    for idx, item in enumerate(dataset[:max_universes]):
        obs = item.get("observation", {})
        field = obs.get("field")
        if field is not None:
            figures.append(plot_field(field, title=f"Field (universe {idx})"))
            figures.append(plot_spectrum(field, title=f"Spectrum (universe {idx})"))
        signal = obs.get("temporal_signal")
        if signal:
            figures.append(plot_temporal_signal(signal, title=f"Temporal signal (universe {idx})"))
        trajectory = obs.get("trajectory")
        trajectory_fig = plot_trajectory(trajectory, title=f"Trajectory (universe {idx})")
        if trajectory_fig:
            figures.append(trajectory_fig)
        particles = obs.get("particles")
        particle_fig = plot_particles(particles, title=f"Particles (universe {idx})")
        if particle_fig:
            figures.append(particle_fig)

    dispersion_fig = plot_dispersion(results.get("dispersion"), title="Dispersion law")
    if dispersion_fig:
        figures.append(dispersion_fig)

    if output_dir:
        path = Path(output_dir)
        path.mkdir(parents=True, exist_ok=True)
        for idx, fig in enumerate(figures, start=1):
            out_path = path / f"figure_{idx:02d}.png"
            fig.savefig(out_path, dpi=160, bbox_inches="tight")
            saved.append(out_path)
            plt.close(fig)
    else:
        if show:
            plt.show()
        else:
            for fig in figures:
                plt.close(fig)
    return saved
