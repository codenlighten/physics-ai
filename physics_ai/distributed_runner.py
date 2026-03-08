"""CLI entrypoint for distributed universe exploration."""

from __future__ import annotations

import argparse

from .distributed import DistributedConfig, run_distributed


def main() -> None:
    parser = argparse.ArgumentParser(description="Run distributed universe batches with Ray.")
    parser.add_argument("--universe-count", type=int, default=128)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--universe-type", default=None)
    parser.add_argument("--dynamics-type", default=None)
    parser.add_argument("--store-fields", action="store_true")
    parser.add_argument("--debug-batch", action="store_true")
    parser.add_argument("--checkpoint-dir", default=None)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    config = DistributedConfig(
        universe_count=args.universe_count,
        batch_size=args.batch_size,
        seed=args.seed,
        universe_type=args.universe_type,
        dynamics_type=args.dynamics_type,
        store_fields=args.store_fields,
        debug_batch=args.debug_batch,
        checkpoint_dir=args.checkpoint_dir,
        resume=args.resume,
    )
    results = run_distributed(config)
    print(f"Distributed run completed: {len(results)} universes")


if __name__ == "__main__":
    main()