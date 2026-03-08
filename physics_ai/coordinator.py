"""Coordinator that trains the shared proposal network from discovery logs."""

from __future__ import annotations

import argparse
from pathlib import Path

from .train_proposal import train_from_log


def main() -> None:
    parser = argparse.ArgumentParser(description="Train the shared proposal network.")
    parser.add_argument("--log-path", default="physics_ai/discovery_log.jsonl")
    parser.add_argument("--model-path", default="physics_ai/proposal_net.pt")
    parser.add_argument("--epochs", type=int, default=20)
    args = parser.parse_args()

    trained = train_from_log(Path(args.log_path), Path(args.model_path), epochs=args.epochs)
    if trained:
        print("Coordinator updated the proposal network.")
    else:
        print("No discovery log entries found; coordinator skipped training.")


if __name__ == "__main__":
    main()
