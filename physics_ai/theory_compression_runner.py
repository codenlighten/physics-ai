"""CLI entrypoint for theory compression from checkpoint shards."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from .theory_compression_engine import sindy_fit


def main() -> None:
    parser = argparse.ArgumentParser(description="Run SINDy-style theory compression.")
    parser.add_argument("--input", required=True, help="Path to a universes_batch parquet file")
    parser.add_argument("--output", default="theory_compression.json")
    parser.add_argument("--max-universes", type=int, default=10)
    args = parser.parse_args()

    path = Path(args.input)
    df = pd.read_parquet(path)
    output = []
    for _, row in df.head(args.max_universes).iterrows():
        signal = row.get("temporal_signal")
        if signal is None:
            continue
        result = sindy_fit(signal, dt=1.0)
        output.append({
            "universe_id": row.get("universe_id"),
            "equation": result.equation,
            "residual": result.residual,
        })

    Path(args.output).write_text("\n".join([str(item) for item in output]), encoding="utf-8")
    print(f"Saved theory compression output to {args.output}")


if __name__ == "__main__":
    main()
