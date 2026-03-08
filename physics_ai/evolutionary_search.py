"""Evolutionary universe search utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

import numpy as np

from .checkpoint import init_run, save_batch
from .experiment_planner import propose_experiment
from .universe_engine import explore_universes
from .universe_atlas import embed_universes, select_sparse_seeds
from .equation_evolution import apply_terms, default_terms, mutate_terms


@dataclass
class EvolutionConfig:
    generations: int = 3
    population_size: int = 20
    elite_count: int = 5
    seed: int | None = None
    universe_type: str | None = None
    dynamics_type: str | None = None
    batch_size: int = 1
    checkpoint_dir: str | None = None
    mutation_strategy: str = "random"
    sigma: float = 0.3
    target_phase: str | None = None
    phase_bonus: float = 1.5
    atlas_guided: bool = False
    atlas_method: str = "umap"
    atlas_seed_count: int = 5
    equation_evolution: bool = False
    term_toggle_prob: float = 0.2


PARAM_BOUNDS: Dict[str, Tuple[float, float]] = {
    "wave_speed": (0.3, 3.0),
    "wavelength": (3.0, 20.0),
    "amplitude": (0.2, 2.0),
    "steps": (40.0, 200.0),
    "wave_nonlinear": (0.0, 1.0),
    "wave_biharmonic": (0.0, 0.5),
}


@dataclass
class CMAESState:
    mean: np.ndarray
    cov: np.ndarray
    sigma: float


def _mutate_value(rng: np.random.Generator, value: float, scale: float, lower: float, upper: float) -> float:
    mutated = value * rng.uniform(1 - scale, 1 + scale)
    return float(np.clip(mutated, lower, upper))


def mutate_config(rng: np.random.Generator, config: Dict[str, Any]) -> Dict[str, Any]:
    mutated = dict(config)
    mutated["wave_speed"] = _mutate_value(rng, float(config["wave_speed"]), 0.2, 0.3, 3.0)
    mutated["wavelength"] = _mutate_value(rng, float(config["wavelength"]), 0.2, 3.0, 20.0)
    mutated["amplitude"] = _mutate_value(rng, float(config["amplitude"]), 0.3, 0.2, 2.0)
    mutated["steps"] = int(_mutate_value(rng, float(config["steps"]), 0.1, 40.0, 200.0))
    mutated["wave_nonlinear"] = _mutate_value(
        rng,
        float(config.get("wave_nonlinear", 0.0)),
        0.4,
        0.0,
        1.0,
    )
    mutated["wave_biharmonic"] = _mutate_value(
        rng,
        float(config.get("wave_biharmonic", 0.0)),
        0.4,
        0.0,
        0.5,
    )
    if "wave_terms" not in mutated:
        mutated["wave_terms"] = default_terms()
    mutated["pulse_position"] = int(np.clip(mutated["pulse_position"], 0, mutated["size"] - 1))
    return mutated


def _config_to_vector(config: Dict[str, Any]) -> np.ndarray:
    return np.array(
        [
            float(config["wave_speed"]),
            float(config["wavelength"]),
            float(config["amplitude"]),
            float(config["steps"]),
            float(config.get("wave_nonlinear", 0.0)),
            float(config.get("wave_biharmonic", 0.0)),
        ],
        dtype=float,
    )


def _vector_to_config(vector: np.ndarray, template: Dict[str, Any]) -> Dict[str, Any]:
    updated = dict(template)
    values = vector.tolist()
    keys = ["wave_speed", "wavelength", "amplitude", "steps", "wave_nonlinear", "wave_biharmonic"]
    for key, value in zip(keys, values):
        lower, upper = PARAM_BOUNDS[key]
        updated[key] = float(np.clip(value, lower, upper))
    updated["steps"] = int(updated["steps"])
    updated["pulse_position"] = int(np.clip(updated["pulse_position"], 0, updated["size"] - 1))
    return updated


def init_cmaes(population: List[Dict[str, Any]], sigma: float) -> CMAESState:
    vectors = np.stack([_config_to_vector(item) for item in population])
    mean = np.mean(vectors, axis=0)
    cov = np.cov(vectors.T) if vectors.shape[0] > 1 else np.eye(vectors.shape[1])
    return CMAESState(mean=mean, cov=cov, sigma=sigma)


def evolve_generation_cmaes(
    rng: np.random.Generator,
    elites: List[Dict[str, Any]],
    population_size: int,
    state: CMAESState,
) -> Tuple[List[Dict[str, Any]], CMAESState]:
    elite_vectors = np.stack([_config_to_vector(item["config"]) for item in elites])
    mean = np.mean(elite_vectors, axis=0)
    cov = np.cov(elite_vectors.T) if elite_vectors.shape[0] > 1 else state.cov
    sigma = max(state.sigma * 0.95, 0.05)
    new_state = CMAESState(mean=mean, cov=cov, sigma=sigma)
    template = elites[0]["config"]
    next_population: List[Dict[str, Any]] = []
    for _ in range(population_size):
        sample = rng.multivariate_normal(mean, cov * (sigma ** 2))
        next_population.append(_vector_to_config(sample, template))
    return next_population, new_state


def evolve_generation_atlas_guided(
    rng: np.random.Generator,
    results: List[Dict[str, Any]],
    population_size: int,
    method: str,
    seed_count: int,
) -> List[Dict[str, Any]]:
    if len(results) < 4:
        seeds = [item["config"] for item in results]
        next_population: List[Dict[str, Any]] = []
        while len(next_population) < population_size:
            parent = rng.choice(seeds)
            next_population.append(mutate_config(rng, parent))
        return next_population
    try:
        import pandas as pd
    except ImportError:
        raise RuntimeError("pandas is required for atlas-guided evolution.")
    records = []
    for item in results:
        obs = item["observation"]
        record = {
            "score_raw": obs.get("score_raw"),
            "score": obs.get("score"),
            "particle_count": (obs.get("particles") or {}).get("particle_count"),
            "resonance_strength": obs.get("resonance_strength"),
            "curvature_strength": obs.get("curvature_strength"),
            "variance": obs.get("variance"),
            "spectral_entropy": obs.get("spectral_entropy"),
            "energy_localization": obs.get("energy_localization"),
            "diversity_penalty": obs.get("diversity_penalty"),
            "novelty_bonus": obs.get("novelty_bonus"),
            "dispersion_type": (obs.get("dispersion") or {}).get("law_type"),
            "phase": obs.get("phase"),
            "config": item["config"],
        }
        records.append(record)
    frame = pd.DataFrame(records)
    if method == "tsne" and len(frame) <= 3:
        method = "umap"
    embedded = embed_universes(frame, method=method, perplexity=max(2.0, min(10.0, len(frame) - 1)))
    sparse = select_sparse_seeds(embedded, k=seed_count)
    seeds = [row["config"] for _, row in sparse.iterrows()]
    next_population: List[Dict[str, Any]] = []
    while len(next_population) < population_size:
        parent = rng.choice(seeds)
        next_population.append(mutate_config(rng, parent))
    return next_population


def generate_population(
    rng: np.random.Generator,
    population_size: int,
    universe_type: str | None,
    dynamics_type: str | None,
    seed_offset: int = 0,
) -> List[Dict[str, Any]]:
    population: List[Dict[str, Any]] = []
    for idx in range(population_size):
        config = propose_experiment(
            seed=int(rng.integers(0, 1_000_000)) + seed_offset + idx,
            universe_type=universe_type,
            dynamics_type=dynamics_type,
        )
        config["wave_terms"] = default_terms()
        population.append(config)
    return population


def evaluate_population(population: List[Dict[str, Any]], config: EvolutionConfig) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    for item in population:
        if config.equation_evolution:
            item["wave_terms"] = mutate_terms(
                np.random.default_rng(int(item.get("seed", 0))),
                item.get("wave_terms", default_terms()),
                p_toggle=config.term_toggle_prob,
            )
            item.update(apply_terms(item, item["wave_terms"]))
        result = explore_universes(
            1,
            seed=item.get("seed"),
            universe_type=item.get("universe_type"),
            dynamics_type=item.get("dynamics_type"),
            batch_size=config.batch_size,
        )[0]
        if config.target_phase:
            phase = result["observation"].get("phase")
            if phase == config.target_phase:
                result["observation"]["score"] = float(result["observation"].get("score", 0.0)) + config.phase_bonus
                result["observation"]["phase_bonus"] = config.phase_bonus
            else:
                result["observation"]["phase_bonus"] = 0.0
        result["config"] = item
        results.append(result)
    return results


def select_elites(results: List[Dict[str, Any]], elite_count: int) -> List[Dict[str, Any]]:
    ordered = sorted(results, key=lambda item: item["observation"].get("score", 0.0), reverse=True)
    return ordered[: max(1, elite_count)]


def evolve_generation(
    rng: np.random.Generator,
    elites: List[Dict[str, Any]],
    population_size: int,
) -> List[Dict[str, Any]]:
    next_population: List[Dict[str, Any]] = []
    while len(next_population) < population_size:
        parent = rng.choice(elites)
        next_population.append(mutate_config(rng, parent["config"]))
    return next_population


def run_evolution(config: EvolutionConfig) -> List[Dict[str, Any]]:
    rng = np.random.default_rng(config.seed)
    run_dir = None
    if config.checkpoint_dir:
        run_config = {
            "generations": config.generations,
            "population_size": config.population_size,
            "elite_count": config.elite_count,
            "seed": config.seed,
            "universe_type": config.universe_type,
            "dynamics_type": config.dynamics_type,
            "batch_size": config.batch_size,
            "mutation_strategy": config.mutation_strategy,
            "sigma": config.sigma,
            "target_phase": config.target_phase,
            "phase_bonus": config.phase_bonus,
            "atlas_guided": config.atlas_guided,
            "atlas_method": config.atlas_method,
            "atlas_seed_count": config.atlas_seed_count,
            "equation_evolution": config.equation_evolution,
            "term_toggle_prob": config.term_toggle_prob,
        }
        run_dir, _ = init_run(config.checkpoint_dir, run_config, resume=False)

    population = generate_population(rng, config.population_size, config.universe_type, config.dynamics_type)
    cma_state = init_cmaes(population, config.sigma)
    all_results: List[Dict[str, Any]] = []
    for generation in range(config.generations):
        results = evaluate_population(population, config)
        all_results.extend(results)
        if run_dir is not None:
            save_batch(run_dir, {"dataset": results}, start_index=generation * config.population_size, batch_index=generation)
        elites = select_elites(results, config.elite_count)
        if config.atlas_guided:
            population = evolve_generation_atlas_guided(
                rng,
                results,
                config.population_size,
                method=config.atlas_method,
                seed_count=config.atlas_seed_count,
            )
        elif config.mutation_strategy == "cmaes":
            population, cma_state = evolve_generation_cmaes(rng, elites, config.population_size, cma_state)
        else:
            population = evolve_generation(rng, elites, config.population_size)
    return all_results
