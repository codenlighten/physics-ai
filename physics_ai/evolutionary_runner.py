"""CLI entrypoint for evolutionary universe search."""

from __future__ import annotations

import argparse

from .evolutionary_search import EvolutionConfig, run_evolution


def main() -> None:
    parser = argparse.ArgumentParser(description="Run evolutionary universe search.")
    parser.add_argument("--generations", type=int, default=3)
    parser.add_argument("--population-size", type=int, default=20)
    parser.add_argument("--elite-count", type=int, default=5)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--universe-type", default=None)
    parser.add_argument("--dynamics-type", default=None)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--checkpoint-dir", default=None)
    parser.add_argument("--mutation-strategy", default="random", choices=["random", "cmaes"])
    parser.add_argument("--sigma", type=float, default=0.3)
    parser.add_argument("--target-phase", default=None)
    parser.add_argument("--phase-bonus", type=float, default=1.5)
    parser.add_argument("--atlas-guided", action="store_true")
    parser.add_argument("--atlas-method", default="umap", choices=["umap", "tsne"])
    parser.add_argument("--atlas-seed-count", type=int, default=5)
    parser.add_argument("--equation-evolution", action="store_true")
    parser.add_argument("--term-toggle-prob", type=float, default=0.2)
    args = parser.parse_args()

    config = EvolutionConfig(
        generations=args.generations,
        population_size=args.population_size,
        elite_count=args.elite_count,
        seed=args.seed,
        universe_type=args.universe_type,
        dynamics_type=args.dynamics_type,
        batch_size=args.batch_size,
        checkpoint_dir=args.checkpoint_dir,
        mutation_strategy=args.mutation_strategy,
        sigma=args.sigma,
        target_phase=args.target_phase,
        phase_bonus=args.phase_bonus,
        atlas_guided=args.atlas_guided,
        atlas_method=args.atlas_method,
        atlas_seed_count=args.atlas_seed_count,
        equation_evolution=args.equation_evolution,
        term_toggle_prob=args.term_toggle_prob,
    )
    results = run_evolution(config)
    print(f"Evolutionary run complete: {len(results)} universes evaluated")


if __name__ == "__main__":
    main()
