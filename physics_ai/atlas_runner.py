"""CLI entrypoint for building a universe atlas."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

if not matplotlib.get_backend().lower().startswith("agg"):
    matplotlib.use("Agg")

import matplotlib.pyplot as plt

from .universe_atlas import embed_universes, load_universe_shards, save_atlas


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a universe atlas embedding.")
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--method", default="umap", choices=["umap", "tsne"])
    parser.add_argument("--output", default="atlas.csv")
    parser.add_argument("--plot", default=None)
    parser.add_argument("--color", default="phase")
    args = parser.parse_args()

    df = load_universe_shards(args.run_dir)
    embedded = embed_universes(df, method=args.method)
    output_path = save_atlas(embedded, args.output)
    print(f"Atlas saved to: {output_path}")

    if args.plot:
        fig, ax = plt.subplots(figsize=(6, 5))
        colors = embedded[args.color] if args.color in embedded.columns else embedded["score"]
        scatter = ax.scatter(embedded["atlas_x"], embedded["atlas_y"], c=colors, cmap="viridis", s=18)
        ax.set_title("Universe atlas")
        ax.set_xlabel("atlas_x")
        ax.set_ylabel("atlas_y")
        fig.colorbar(scatter, ax=ax, label=args.color)
        plot_path = Path(args.plot)
        fig.savefig(plot_path, dpi=160, bbox_inches="tight")
        print(f"Atlas plot saved to: {plot_path}")


if __name__ == "__main__":
    main()
