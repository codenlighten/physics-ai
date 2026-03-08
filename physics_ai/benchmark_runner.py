"""Simple performance benchmark harness for batched dynamics."""

from __future__ import annotations

import argparse
import csv
import time
from pathlib import Path
from typing import Dict

import numpy as np

from .backend import backend_name
from .field_dynamics import DiffusionConfig, WaveConfig, simulate_diffusion, simulate_wave


def _benchmark_wave(batch: int, size: int, steps: int) -> Dict[str, float]:
    rng = np.random.default_rng(0)
    fields = rng.random((batch, size, size))
    config = WaveConfig(steps=steps)
    start = time.perf_counter()
    simulate_wave(fields, config)
    elapsed = time.perf_counter() - start
    return {"elapsed_s": elapsed, "per_step_ms": (elapsed / steps) * 1000}


def _benchmark_diffusion(batch: int, size: int, steps: int) -> Dict[str, float]:
    rng = np.random.default_rng(0)
    fields = rng.random((batch, size, size))
    config = DiffusionConfig(steps=steps)
    start = time.perf_counter()
    simulate_diffusion(fields, config)
    elapsed = time.perf_counter() - start
    return {"elapsed_s": elapsed, "per_step_ms": (elapsed / steps) * 1000}


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark batched dynamics.")
    parser.add_argument("--batch", type=int, default=32)
    parser.add_argument("--size", type=int, default=64)
    parser.add_argument("--steps", type=int, default=50)
    parser.add_argument("--mode", choices=["wave", "diffusion"], default="wave")
    parser.add_argument("--output", type=str, default=None, help="Optional CSV output path.")
    args = parser.parse_args()

    print(f"Backend: {backend_name()} | Batch: {args.batch} | Size: {args.size} | Steps: {args.steps}")
    if args.mode == "wave":
        metrics = _benchmark_wave(args.batch, args.size, args.steps)
    else:
        metrics = _benchmark_diffusion(args.batch, args.size, args.steps)
    print(f"Elapsed: {metrics['elapsed_s']:.4f}s | Per-step: {metrics['per_step_ms']:.3f} ms")

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        write_header = not output_path.exists()
        with output_path.open("a", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=["backend", "mode", "batch", "size", "steps", "elapsed_s", "per_step_ms"],
            )
            if write_header:
                writer.writeheader()
            writer.writerow({
                "backend": backend_name(),
                "mode": args.mode,
                "batch": args.batch,
                "size": args.size,
                "steps": args.steps,
                "elapsed_s": f"{metrics['elapsed_s']:.6f}",
                "per_step_ms": f"{metrics['per_step_ms']:.6f}",
            })


if __name__ == "__main__":
    main()
