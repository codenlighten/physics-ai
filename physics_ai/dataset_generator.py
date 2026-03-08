"""Synthetic dataset generator for physics foundation training."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from typing import Dict, Any, Iterable, List
import time
import hashlib

from .universe_engine import explore_universes


@dataclass
class DatasetConfig:
    universe_count: int = 100
    seed: int | None = None
    universe_type: str | None = None
    dynamics_type: str | None = None


def build_records(dataset: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    for item in dataset:
        config = item["config"]
        obs = item["observation"]
        records.append({
            "universe_type": config.get("universe_type", "random"),
            "dynamics_type": config.get("dynamics_type", "static"),
            "wave_speed": config["wave_speed"],
            "wavelength": config["wavelength"],
            "frequency": obs.get("frequency", 0.0),
            "node_count": obs.get("node_count", 0),
            "node_spacing": obs.get("node_spacing", 0.0),
            "symmetry_score": obs.get("symmetry", 0.0),
            "peak_count": obs.get("peak_count", 0),
        })
    return records


def generate_dataset(config: DatasetConfig) -> List[Dict[str, Any]]:
    dataset = explore_universes(
        config.universe_count,
        seed=config.seed,
        universe_type=config.universe_type,
        dynamics_type=config.dynamics_type,
    )
    return build_records(dataset)


def export_csv(records: Iterable[Dict[str, Any]], path: str) -> None:
    records = list(records)
    if not records:
        return
    fieldnames = list(records[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)


def build_metadata(records: Iterable[Dict[str, Any]], config: DatasetConfig) -> Dict[str, Any]:
    records = list(records)
    feature_names = list(records[0].keys()) if records else []
    schema_hash = hashlib.sha256(
        ",".join(feature_names).encode("utf-8")
    ).hexdigest()
    return {
        "record_count": len(records),
        "feature_names": feature_names,
        "schema_hash": schema_hash,
        "universe_count": config.universe_count,
        "seed": config.seed,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def export_metadata(metadata: Dict[str, Any], path: str) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        for key, value in metadata.items():
            handle.write(f"{key}: {value}\n")


def validate_schema(records: Iterable[Dict[str, Any]], required: Iterable[str]) -> None:
    records = list(records)
    required_set = set(required)
    if not records:
        raise ValueError("No records available for schema validation.")
    missing = required_set.difference(records[0].keys())
    if missing:
        raise ValueError(f"Missing required fields: {sorted(missing)}")
