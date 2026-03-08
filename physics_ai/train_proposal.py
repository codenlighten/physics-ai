"""Train and persist the neural proposal network from the discovery log."""

from __future__ import annotations

import argparse
from pathlib import Path

from .neural_symbolic import (
    ProposalConfig,
    build_proposal_network,
    build_training_dataset,
    load_discovery_log,
    load_proposal_network,
    save_proposal_network,
    train_proposal_net,
)


def train_from_log(log_path: Path, model_path: Path, epochs: int = 20) -> bool:
    entries = load_discovery_log(str(log_path))
    features, labels = build_training_dataset(entries)
    if not features:
        return False

    input_dim = len(features[0]) if features else 0
    model = build_proposal_network(ProposalConfig(input_dim=input_dim))
    if model_path.exists():
        load_proposal_network(model, str(model_path))

    train_proposal_net(model, features, labels, epochs=epochs)
    save_proposal_network(model, str(model_path))
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Train the neural proposal network.")
    parser.add_argument("--log-path", default="physics_ai/discovery_log.jsonl")
    parser.add_argument("--model-path", default="physics_ai/proposal_net.pt")
    parser.add_argument("--epochs", type=int, default=20)
    args = parser.parse_args()

    log_path = Path(args.log_path)
    model_path = Path(args.model_path)
    trained = train_from_log(log_path, model_path, epochs=args.epochs)
    if trained:
        print(f"Saved proposal network to {model_path}")
    else:
        print("No discovery log entries found; skipping training.")


if __name__ == "__main__":
    main()
