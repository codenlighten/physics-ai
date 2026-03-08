"""Multi-universe exploration utilities."""

from __future__ import annotations

from typing import Dict, Any, List

import numpy as np

from .experiment_planner import propose_experiment
from .observer import observe, observe_temporal
from .simulation import WaveSimulation
from .spectral_universe import generate_universe_field
from .field_dynamics import (
    DiffusionConfig,
    OscillatorConfig,
    ReactionDiffusionConfig,
    SchrodingerConfig,
    WaveConfig,
    simulate_diffusion,
    simulate_oscillator,
    simulate_reaction_diffusion,
    simulate_schrodinger,
    simulate_wave,
)
from .spectral_lagrangian import SpectralConfig, simulate_field_from_modes
from .renormalization import analyze_scales
from .gauge_discovery import gauge_invariance, gauge_summary
from .geometry_universe import GeometryConfig, simulate_geometry, simulate_resonant_geometry
from .particle_detector import particle_summary
from .interaction_detector import interaction_summary


def run_universe(config: Dict[str, Any]) -> Dict[str, Any]:
    initial_field = None
    universe_type = config.get("universe_type", "random")
    if universe_type != "random":
        initial_field = generate_universe_field(
            universe_type,
            size=config["size"],
            seed=config.get("seed"),
        )
    dynamics_type = config.get("dynamics_type", "static")
    sim = WaveSimulation(
        size=config["size"],
        steps=config["steps"],
        wave_speed=config["wave_speed"],
        wavelength=config["wavelength"],
        amplitude=config["amplitude"],
        pulse_position=config["pulse_position"],
        boundary=config["boundary"],
        initial_field=initial_field,
    )
    temporal_metrics: Dict[str, Any] = {}
    frames = None
    extra_observation: Dict[str, Any] = {}
    store_field = bool(config.get("store_field", False))
    if dynamics_type == "wave":
        start_field, _ = sim.initialize()
        frames = simulate_wave(start_field, WaveConfig(steps=config["steps"], wave_speed=config["wave_speed"]))
        grid = frames[-1]
        temporal_metrics = observe_temporal(frames)
    elif dynamics_type == "diffusion":
        start_field, _ = sim.initialize()
        frames = simulate_diffusion(start_field, DiffusionConfig(steps=config["steps"]))
        grid = frames[-1]
        temporal_metrics = observe_temporal(frames)
    elif dynamics_type == "reaction_diffusion":
        start_field, _ = sim.initialize()
        secondary_field = np.random.default_rng(config.get("seed")).random(start_field.shape)
        field_a, field_b = simulate_reaction_diffusion(
            start_field,
            secondary_field,
            ReactionDiffusionConfig(steps=config["steps"]),
        )
        grid = field_a
        frames = np.stack([field_a, field_b])
        temporal_metrics = observe_temporal(frames)
    elif dynamics_type == "oscillator":
        series = simulate_oscillator(
            OscillatorConfig(
                steps=config["steps"],
                k=config.get("oscillator_k", 1.0),
                dt=config.get("dt", 0.01),
                q0=config.get("q0", 1.0),
            )
        )
        frames = series[:, None, None] * np.ones((series.size, config["size"], config["size"]))
        grid = frames[-1]
        temporal_metrics = observe_temporal(frames)
    elif dynamics_type == "schrodinger":
        start_field, _ = sim.initialize()
        frames = simulate_schrodinger(start_field, SchrodingerConfig(steps=config["steps"], dt=config.get("dt", 0.01)))
        grid = np.real(frames[-1])
        temporal_metrics = observe_temporal(frames)
    elif dynamics_type == "spectral_lagrangian":
        spectral_config = SpectralConfig(
            modes=config.get("spectral_modes", 6),
            steps=config["steps"],
            dt=config.get("dt", 0.05),
            seed=config.get("seed"),
        )
        frames, omegas, _ = simulate_field_from_modes(config["size"], spectral_config)
        grid = frames[-1]
        temporal_metrics = observe_temporal(frames)
        extra_observation["spectral_omegas"] = [float(value) for value in omegas]
    elif dynamics_type == "geometry":
        geometry = simulate_geometry(
            GeometryConfig(
                size=config["size"],
                steps=config["steps"],
                dt=config.get("dt", 0.05),
                alpha=config.get("geometry_alpha", 0.2),
                seed=config.get("seed"),
            )
        )
        grid = geometry["rho"]
        extra_observation.update({
            "curvature_strength": geometry["curvature_strength"],
            "trajectory_length": geometry["trajectory_length"],
            "trajectory": geometry["trajectory"],
        })
    elif dynamics_type == "resonant_geometry":
        geometry = simulate_resonant_geometry(
            GeometryConfig(
                size=config["size"],
                steps=config["steps"],
                dt=config.get("dt", 0.05),
                alpha=config.get("geometry_alpha", 0.2),
                seed=config.get("seed"),
                resonance_modes=config.get("resonance_modes", 4),
            )
        )
        grid = geometry["rho"]
        extra_observation.update({
            "curvature_strength": geometry["curvature_strength"],
            "trajectory_length": geometry["trajectory_length"],
            "resonance_strength": geometry["resonance_strength"],
            "resonance_spectrum": geometry["resonance_spectrum"],
            "trajectory": geometry["trajectory"],
        })
    else:
        grid = sim.run()
    observation = observe(grid)
    if extra_observation:
        observation.update(extra_observation)
    if temporal_metrics:
        observation.update(temporal_metrics)
    if frames is not None and frames.shape[1] >= 8 and frames.shape[2] >= 8:
        observation["renormalization"] = analyze_scales(frames)
    if frames is not None and np.iscomplexobj(frames):
        observation["gauge"] = gauge_summary(gauge_invariance(frames))
    if frames is not None:
        observation["particles"] = particle_summary(frames)
        observation["interactions"] = interaction_summary(observation["particles"])
    if store_field:
        observation["field"] = np.real(grid) if np.iscomplexobj(grid) else grid
    wave_speed = float(config["wave_speed"])
    wavelength = float(config["wavelength"])
    observation.update({
        "wavelength": wavelength,
        "wave_speed": wave_speed,
        "frequency": wave_speed / wavelength,
    })
    return {"config": config, "observation": observation}


def explore_universes(
    count: int,
    seed: int | None = None,
    universe_type: str | None = None,
    dynamics_type: str | None = None,
    store_fields: bool = False,
) -> List[Dict[str, Any]]:
    dataset: List[Dict[str, Any]] = []
    for idx in range(count):
        run_seed = seed + idx if seed is not None else None
        config = propose_experiment(
            seed=run_seed,
            universe_type=universe_type,
            dynamics_type=dynamics_type,
        )
        config["store_field"] = store_fields
        config["seed"] = run_seed
        dataset.append(run_universe(config))
    return dataset
