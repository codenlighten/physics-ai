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
from .backend import backend_name
from .scoring import diversity_penalty, novelty_bonus, signature_from_observation, universe_score
from .phase_detector import detect_phase


def _initial_field(config: Dict[str, Any]) -> np.ndarray:
    universe_type = config.get("universe_type", "random")
    if universe_type != "random":
        return generate_universe_field(
            universe_type,
            size=config["size"],
            seed=config.get("seed"),
        )
    sim = WaveSimulation(
        size=config["size"],
        steps=config["steps"],
        wave_speed=config["wave_speed"],
        wavelength=config["wavelength"],
        amplitude=config["amplitude"],
        pulse_position=config["pulse_position"],
        boundary=config["boundary"],
        initial_field=None,
    )
    grid, _ = sim.initialize()
    return grid


def _build_batch_configs(
    base_config: Dict[str, Any],
    seeds: List[int | None],
    store_fields: bool,
) -> List[Dict[str, Any]]:
    configs: List[Dict[str, Any]] = []
    for seed in seeds:
        config = dict(base_config)
        config["seed"] = seed
        config["store_field"] = store_fields
        if seed is not None:
            rng = np.random.default_rng(seed)
            if config["size"] > 16:
                config["pulse_position"] = int(rng.integers(8, config["size"] - 8))
        configs.append(config)
    return configs


def _finalize_observation(
    config: Dict[str, Any],
    grid: np.ndarray,
    frames: np.ndarray | None,
    extra_observation: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    observation = observe(grid)
    if extra_observation:
        observation.update(extra_observation)
    if frames is not None:
        temporal_metrics = observe_temporal(frames)
        observation.update(temporal_metrics)
        if frames.shape[1] >= 8 and frames.shape[2] >= 8:
            observation["renormalization"] = analyze_scales(frames)
        if np.iscomplexobj(frames):
            observation["gauge"] = gauge_summary(gauge_invariance(frames))
        observation["particles"] = particle_summary(frames)
        observation["interactions"] = interaction_summary(observation["particles"])
    if config.get("store_field"):
        observation["field"] = np.real(grid) if np.iscomplexobj(grid) else grid
    wave_speed = float(config["wave_speed"])
    wavelength = float(config["wavelength"])
    observation.update({
        "wavelength": wavelength,
        "wave_speed": wave_speed,
        "frequency": wave_speed / wavelength,
    })
    observation["score_raw"] = universe_score(observation)
    observation["score"] = observation["score_raw"]
    observation.update(detect_phase(observation))
    return observation


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
        terms = config.get("wave_terms", ["laplacian"])
        frames = simulate_wave(
            start_field,
            WaveConfig(
                steps=config["steps"],
                wave_speed=config["wave_speed"],
                nonlinear_coeff=config.get("wave_nonlinear", 0.0) if "nonlinear" in terms else 0.0,
                biharmonic_coeff=config.get("wave_biharmonic", 0.0) if "biharmonic" in terms else 0.0,
            ),
        )
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
    observation = _finalize_observation(config, grid, frames, extra_observation)
    return {"config": config, "observation": observation}


def run_universe_batch(
    base_config: Dict[str, Any],
    seeds: List[int | None],
    store_fields: bool = False,
    debug_batch: bool = False,
) -> List[Dict[str, Any]]:
    configs = _build_batch_configs(base_config, seeds, store_fields)
    dynamics_type = base_config.get("dynamics_type", "static")
    if dynamics_type not in {"wave", "diffusion", "schrodinger"}:
        return [run_universe(config) for config in configs]

    initial_fields = np.stack([_initial_field(config) for config in configs])
    if initial_fields.ndim != 3:
        raise ValueError("Expected batch field shape [B, X, Y].")
    if debug_batch:
        print(
            f"Batch size: {initial_fields.shape[0]} | Field shape: {initial_fields.shape} | "
            f"Backend: {backend_name()}"
        )
    frames: np.ndarray | None = None
    grids: np.ndarray
    if dynamics_type == "wave":
        terms = base_config.get("wave_terms", ["laplacian"])
        frames = simulate_wave(
            initial_fields,
            WaveConfig(
                steps=base_config["steps"],
                wave_speed=base_config["wave_speed"],
                nonlinear_coeff=base_config.get("wave_nonlinear", 0.0) if "nonlinear" in terms else 0.0,
                biharmonic_coeff=base_config.get("wave_biharmonic", 0.0) if "biharmonic" in terms else 0.0,
            ),
        )
        grids = frames[-1]
    elif dynamics_type == "diffusion":
        frames = simulate_diffusion(
            initial_fields,
            DiffusionConfig(steps=base_config["steps"]),
        )
        grids = frames[-1]
    else:
        frames = simulate_schrodinger(
            initial_fields,
            SchrodingerConfig(steps=base_config["steps"], dt=base_config.get("dt", 0.01)),
        )
        grids = np.real(frames[-1])

    results: List[Dict[str, Any]] = []
    for idx, config in enumerate(configs):
        batch_frames = frames[:, idx] if frames is not None else None
        grid = grids[idx]
        observation = _finalize_observation(config, grid, batch_frames)
        results.append({"config": config, "observation": observation})
    return results


def explore_universes(
    count: int,
    seed: int | None = None,
    universe_type: str | None = None,
    dynamics_type: str | None = None,
    store_fields: bool = False,
    batch_size: int = 1,
    debug_batch: bool = False,
    start_index: int = 0,
) -> List[Dict[str, Any]]:
    dataset: List[Dict[str, Any]] = []
    batch_size = max(1, int(batch_size))
    idx = start_index
    target = start_index + count
    diversity_signatures: List[Dict[str, float | str]] = []
    while idx < target:
        batch_count = min(batch_size, target - idx)
        run_seed = seed + idx if seed is not None else None
        base_config = propose_experiment(
            seed=run_seed,
            universe_type=universe_type,
            dynamics_type=dynamics_type,
        )
        seeds = [run_seed + offset if run_seed is not None else None for offset in range(batch_count)]
        if batch_count > 1:
            batch_results = run_universe_batch(base_config, seeds, store_fields, debug_batch)
        else:
            base_config["store_field"] = store_fields
            base_config["seed"] = run_seed
            batch_results = [run_universe(base_config)]
        for item in batch_results:
            observation = item["observation"]
            signature = signature_from_observation(observation)
            observation["diversity_penalty"] = diversity_penalty(signature, diversity_signatures)
            observation["novelty_bonus"] = novelty_bonus(signature, diversity_signatures)
            observation["score"] = universe_score(observation, diversity_signatures)
            diversity_signatures.append(signature)
        dataset.extend(batch_results)
        idx += batch_count
    return dataset
