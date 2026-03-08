"""Minimal training stub for a physics foundation model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, List

import numpy as np

from .dataset_generator import DatasetConfig, generate_dataset


@dataclass
class TrainingConfig:
    universe_count: int = 200
    seed: int | None = None


def build_arrays(records: List[Dict[str, Any]]) -> tuple[np.ndarray, np.ndarray]:
    features = np.array(
        [
            [
                r["wave_speed"],
                r["wavelength"],
                r["node_count"],
                r["symmetry_score"],
                r["peak_count"],
            ]
            for r in records
        ]
    )
    targets = np.array([r["frequency"] for r in records])
    return features, targets


def train_baseline(config: TrainingConfig) -> Dict[str, float]:
    records = generate_dataset(DatasetConfig(universe_count=config.universe_count, seed=config.seed))
    features, targets = build_arrays(records)
    weights, *_ = np.linalg.lstsq(features, targets, rcond=None)
    preds = features @ weights
    error = float(np.mean(np.abs(preds - targets)))
    return {"mae": error, "weights": weights.tolist()}


def main() -> None:
    metrics = train_baseline(TrainingConfig())
    print("Baseline training metrics:", metrics)


if __name__ == "__main__":
    main()
