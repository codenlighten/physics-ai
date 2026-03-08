"""Ray-based distributed batch execution helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from .checkpoint import init_run, save_batch
from .universe_engine import explore_universes


@dataclass
class DistributedConfig:
    universe_count: int = 128
    batch_size: int = 32
    seed: int | None = None
    universe_type: str | None = None
    dynamics_type: str | None = None
    store_fields: bool = False
    debug_batch: bool = False
    checkpoint_dir: str | None = None
    resume: bool = False


def _lazy_import_ray():
    try:
        import ray  # type: ignore
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("Ray is not installed. Install ray to use distributed execution.") from exc
    return ray


def run_distributed(config: DistributedConfig) -> List[Dict[str, Any]]:
    ray = _lazy_import_ray()
    if not ray.is_initialized():
        ray.init(ignore_reinit_error=True)

    run_dir = None
    batch_index = 0
    if config.checkpoint_dir:
        run_config = {
            "universe_count": config.universe_count,
            "seed": config.seed,
            "universe_type": config.universe_type,
            "dynamics_type": config.dynamics_type,
            "batch_size": config.batch_size,
            "resume": config.resume,
        }
        run_dir, metadata = init_run(config.checkpoint_dir, run_config, resume=config.resume)
        batch_index = int(metadata.get("batches_completed", 0))

    @ray.remote
    def _run_batch(batch_count: int, batch_seed: int | None, start_index: int, shard_index: int) -> List[Dict[str, Any]]:
        results = explore_universes(
            batch_count,
            seed=batch_seed,
            universe_type=config.universe_type,
            dynamics_type=config.dynamics_type,
            store_fields=config.store_fields,
            batch_size=config.batch_size,
            debug_batch=config.debug_batch,
            start_index=start_index,
        )
        if run_dir is not None:
            save_batch(run_dir, {"dataset": results}, start_index=start_index, batch_index=shard_index)
        return results

    remaining = config.universe_count
    tasks = []
    shard_index = batch_index
    while remaining > 0:
        count = min(config.batch_size, remaining)
        seed = config.seed + shard_index * count if config.seed is not None else None
        start_index = shard_index * count
        tasks.append(_run_batch.remote(count, seed, start_index, shard_index))
        remaining -= count
        shard_index += 1

    results = ray.get(tasks)
    flattened: List[Dict[str, Any]] = []
    for batch in results:
        flattened.extend(batch)
    return flattened
