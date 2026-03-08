"""Checkpointing utilities for experiment runs."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple
import json
import uuid

import pandas as pd


def _serialize(obj: Any) -> Any:
    if is_dataclass(obj):
        return asdict(obj)
    if hasattr(obj, "__dict__"):
        return obj.__dict__
    return obj


def _universe_rows(
    dataset: Iterable[Dict[str, Any]],
    start_index: int = 0,
    generation: int | None = None,
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for idx, item in enumerate(dataset):
        obs = item.get("observation", {})
        dispersion = obs.get("dispersion") or obs.get("dispersion_law")
        config = item.get("config", {})
        rows.append({
            "universe_id": start_index + idx,
            "universe_type": config.get("universe_type"),
            "dynamics_type": config.get("dynamics_type"),
            "generation": generation,
            "wave_terms": config.get("wave_terms"),
            "energy": obs.get("energy"),
            "variance": obs.get("variance"),
            "dominant_frequency": obs.get("dominant_frequency"),
            "resonance_strength": obs.get("resonance_strength"),
            "dispersion_type": (dispersion or {}).get("law_type"),
            "particle_count": (obs.get("particles") or {}).get("particle_count"),
            "score": obs.get("score"),
            "score_raw": obs.get("score_raw"),
            "diversity_penalty": obs.get("diversity_penalty"),
            "novelty_bonus": obs.get("novelty_bonus"),
            "spectral_entropy": obs.get("spectral_entropy"),
            "energy_localization": obs.get("energy_localization"),
            "phase": obs.get("phase"),
            "phase_confidence": obs.get("phase_confidence"),
            "temporal_signal": obs.get("temporal_signal"),
            "vortex_count": obs.get("vortex_count"),
            "nodal_loop_count": obs.get("nodal_loop_count"),
            "defect_density": obs.get("defect_density"),
            "coherence_length": obs.get("coherence_length"),
        })
    return rows


def _particle_rows(dataset: Iterable[Dict[str, Any]], start_index: int = 0) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for idx, item in enumerate(dataset):
        particles = item.get("observation", {}).get("particles") or {}
        for particle_id, track in enumerate(particles.get("tracks", [])):
            rows.append({
                "particle_id": particle_id,
                "universe_id": start_index + idx,
                "lifetime": track.get("lifetime"),
                "displacement": track.get("displacement"),
                "positions": track.get("positions"),
                "frames": track.get("frames"),
            })
    return rows


def _law_rows(results: Dict[str, Any]) -> List[Dict[str, Any]]:
    laws: List[Dict[str, Any]] = []
    inverse_law = results.get("inverse_law")
    if inverse_law:
        laws.append({
            "equation": inverse_law.get("equation"),
            "type": "inverse_law",
            "confidence": inverse_law.get("confidence", 1.0),
            "error": inverse_law.get("error"),
        })
    symbolic = results.get("symbolic_law")
    if symbolic:
        laws.append({
            "equation": symbolic.law,
            "type": "symbolic",
            "confidence": symbolic.confidence,
            "error": symbolic.error,
        })
    lagrangian = results.get("lagrangian")
    if lagrangian:
        laws.append({
            "equation": lagrangian.lagrangian,
            "type": "lagrangian",
            "confidence": 1.0,
            "error": lagrangian.residual_mse,
        })
    return laws


def _latest_run_dir(checkpoint_dir: str | Path) -> Path | None:
    root = Path(checkpoint_dir)
    if not root.exists():
        return None
    runs = [path for path in root.iterdir() if path.is_dir() and path.name.startswith("run_")]
    if not runs:
        return None
    return max(runs, key=lambda path: path.stat().st_mtime)


def load_checkpoint_config(checkpoint_dir: str | Path) -> Dict[str, Any] | None:
    latest = _latest_run_dir(checkpoint_dir)
    if not latest:
        return None
    config_path = latest / "config.json"
    if not config_path.exists():
        return None
    with open(config_path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def load_checkpoint_metadata(checkpoint_dir: str | Path) -> Dict[str, Any] | None:
    latest = _latest_run_dir(checkpoint_dir)
    if not latest:
        return None
    metadata_path = latest / "metadata.json"
    if not metadata_path.exists():
        return None
    with open(metadata_path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def init_run(
    checkpoint_dir: str | Path,
    config: Dict[str, Any],
    resume: bool = False,
) -> Tuple[Path, Dict[str, Any]]:
    root = Path(checkpoint_dir)
    root.mkdir(parents=True, exist_ok=True)
    if resume:
        latest = _latest_run_dir(root)
        if latest is None:
            raise FileNotFoundError("No checkpoint run found to resume.")
        metadata = load_checkpoint_metadata(root) or {}
        return latest, metadata

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    run_id = uuid.uuid4().hex[:6]
    run_dir = root / f"run_{timestamp}_{run_id}"
    run_dir.mkdir(parents=True, exist_ok=True)
    with open(run_dir / "config.json", "w", encoding="utf-8") as handle:
        json.dump(config, handle, indent=2)
    metadata = {
        "run_id": f"{timestamp}_{run_id}",
        "generated_at": datetime.utcnow().isoformat(),
        "batches_completed": 0,
        "universes_processed": 0,
    }
    with open(run_dir / "metadata.json", "w", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2)
    return run_dir, metadata


def save_batch(
    run_dir: str | Path,
    results: Dict[str, Any],
    start_index: int,
    batch_index: int,
    resume_from: str | None = None,
) -> None:
    run_path = Path(run_dir)
    dataset = results.get("dataset", [])
    universes = pd.DataFrame(_universe_rows(dataset, start_index=start_index, generation=batch_index))
    particles = pd.DataFrame(_particle_rows(dataset, start_index=start_index))

    universes.to_parquet(run_path / f"universes_batch_{batch_index:04d}.parquet", index=False)
    particles.to_parquet(run_path / f"particles_batch_{batch_index:04d}.parquet", index=False)

    with open(run_path / "laws.json", "w", encoding="utf-8") as handle:
        json.dump(_law_rows(results), handle, indent=2, default=_serialize)

    metadata_path = run_path / "metadata.json"
    metadata = {}
    if metadata_path.exists():
        with open(metadata_path, "r", encoding="utf-8") as handle:
            metadata = json.load(handle)
    metadata.update({
        "generated_at": datetime.utcnow().isoformat(),
        "batches_completed": int(metadata.get("batches_completed", 0)) + 1,
        "universes_processed": int(metadata.get("universes_processed", 0)) + len(dataset),
        "start_index": start_index,
        "particle_count": int(particles.shape[0]) if not particles.empty else 0,
    })
    if resume_from:
        metadata["resume_from"] = resume_from
    with open(metadata_path, "w", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2)
