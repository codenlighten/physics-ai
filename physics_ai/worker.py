"""Distributed worker that runs simulations and appends symbolic discovery logs."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Dict, List

import numpy as np

from .neural_symbolic import append_discovery_log
from .symbolic_discovery import discover_from_dataset
from .universe_engine import explore_universes


def _aggregate_symbolic_features(observations: List[Dict[str, Any]]) -> List[float]:
    keys = [
        "energy",
        "variance",
        "dominant_frequency",
        "rotation_score",
        "reflection_score",
        "so2_score",
        "node_count",
        "node_spacing",
        "peak_count",
    ]
    if not observations:
        return [0.0] * len(keys)
    matrix = np.array(
        [[float(obs.get(key, 0.0)) for key in keys] for obs in observations],
        dtype=float,
    )
    return [float(value) for value in np.mean(matrix, axis=0)]


def run_worker(
    universe_count: int,
    seed: int | None,
    log_path: Path,
    universe_type: str | None,
    dynamics_type: str | None,
) -> None:
    dataset = explore_universes(
        universe_count,
        seed=seed,
        universe_type=universe_type,
        dynamics_type=dynamics_type,
    )
    observations: List[Dict[str, Any]] = [item["observation"] for item in dataset]
    feature_vector = _aggregate_symbolic_features(observations)

    def _log_result(template: str, error: float) -> None:
        append_discovery_log(str(log_path), feature_vector, template, error)

    discover_from_dataset(observations, on_result=_log_result)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a discovery worker.")
    parser.add_argument("--universe-count", type=int, default=30)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--log-path", default="physics_ai/discovery_log.jsonl")
    parser.add_argument("--universe-type", default=None)
    parser.add_argument("--dynamics-type", default=None)
    args = parser.parse_args()

    run_worker(
        args.universe_count,
        args.seed,
        Path(args.log_path),
        args.universe_type,
        args.dynamics_type,
    )
    print("Worker finished logging discoveries.")


if __name__ == "__main__":
    main()
