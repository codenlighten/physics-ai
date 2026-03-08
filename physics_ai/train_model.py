"""Train a small physics foundation model on synthetic datasets."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, List, Tuple
import argparse
import csv
from pathlib import Path

import numpy as np

from .dataset_generator import DatasetConfig, generate_dataset, build_metadata, validate_schema
from .model_card import generate_model_card
from .model_registry import create_registry_entry, save_metadata, save_config, write_provenance


@dataclass
class TrainConfig:
    universe_count: int = 500
    seed: int | None = None
    epochs: int = 50
    batch_size: int = 64
    learning_rate: float = 1e-3
    validation_split: float = 0.2
    checkpoint_path: str | None = None
    model_path: str | None = None
    metrics_path: str | None = None
    resume_checkpoint: str | None = None


def build_arrays(records: List[Dict[str, Any]]) -> tuple[np.ndarray, np.ndarray]:
    features = np.array(
        [
            [
                r["wave_speed"],
                r["wavelength"],
                r["node_count"],
                r["node_spacing"],
                r["symmetry_score"],
                r["peak_count"],
            ]
            for r in records
        ],
        dtype=np.float32,
    )
    targets = np.array([r["frequency"] for r in records], dtype=np.float32).reshape(-1, 1)
    return features, targets


def train_val_split(
    features: np.ndarray, targets: np.ndarray, validation_split: float, seed: int | None = None
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    indices = rng.permutation(len(features))
    split_idx = int(len(features) * (1 - validation_split))
    train_idx = indices[:split_idx]
    val_idx = indices[split_idx:]
    return (
        features[train_idx],
        targets[train_idx],
        features[val_idx],
        targets[val_idx],
    )


def train_model(config: TrainConfig) -> Dict[str, Any]:
    try:
        import torch
        from torch import nn
        from torch.utils.data import DataLoader, TensorDataset
    except ImportError as exc:
        raise RuntimeError(
            "PyTorch is required for training. Install it with `pip install -r requirements-train.txt`."
        ) from exc

    records = generate_dataset(DatasetConfig(universe_count=config.universe_count, seed=config.seed))
    validate_schema(records, ["wave_speed", "wavelength", "frequency"])
    dataset_meta = build_metadata(records, DatasetConfig(universe_count=config.universe_count, seed=config.seed))
    features, targets = build_arrays(records)
    train_x, train_y, val_x, val_y = train_val_split(
        features, targets, config.validation_split, seed=config.seed
    )

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    train_dataset = TensorDataset(torch.from_numpy(train_x), torch.from_numpy(train_y))
    val_dataset = TensorDataset(torch.from_numpy(val_x), torch.from_numpy(val_y))
    train_loader = DataLoader(train_dataset, batch_size=config.batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=config.batch_size, shuffle=False)

    model = nn.Sequential(
        nn.Linear(features.shape[1], 32),
        nn.ReLU(),
        nn.Linear(32, 16),
        nn.ReLU(),
        nn.Linear(16, 1),
    ).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=config.learning_rate)
    loss_fn = nn.MSELoss()

    best_val = float("inf")
    start_epoch = 0
    if config.resume_checkpoint:
        checkpoint = torch.load(config.resume_checkpoint, map_location=device)
        model.load_state_dict(checkpoint["model_state"])
        start_epoch = int(checkpoint.get("epoch", 0))

    metrics_writer = None
    metrics_handle = None
    if config.metrics_path:
        metrics_handle = open(config.metrics_path, "w", newline="", encoding="utf-8")
        metrics_writer = csv.DictWriter(metrics_handle, fieldnames=["epoch", "train_loss", "val_loss"])
        metrics_writer.writeheader()

    for epoch in range(start_epoch, config.epochs):
        model.train()
        train_losses = []
        for batch_x, batch_y in train_loader:
            batch_x = batch_x.to(device)
            batch_y = batch_y.to(device)
            optimizer.zero_grad()
            preds = model(batch_x)
            loss = loss_fn(preds, batch_y)
            loss.backward()
            optimizer.step()
            train_losses.append(loss.item())

        model.eval()
        val_losses = []
        with torch.no_grad():
            for batch_x, batch_y in val_loader:
                batch_x = batch_x.to(device)
                batch_y = batch_y.to(device)
                val_losses.append(loss_fn(model(batch_x), batch_y).item())
        val_loss = float(np.mean(val_losses)) if val_losses else float("inf")

        if metrics_writer:
            metrics_writer.writerow({
                "epoch": epoch,
                "train_loss": float(np.mean(train_losses)) if train_losses else None,
                "val_loss": val_loss,
            })

        if config.checkpoint_path and val_loss < best_val:
            best_val = val_loss
            torch.save(
                {"model_state": model.state_dict(), "val_loss": val_loss, "epoch": epoch},
                config.checkpoint_path,
            )

    with torch.no_grad():
        preds = model(torch.from_numpy(val_x).to(device)).cpu()
        mae = torch.mean(torch.abs(preds - torch.from_numpy(val_y))).item()

    if config.model_path:
        torch.save(model.state_dict(), config.model_path)

    if metrics_handle:
        metrics_handle.close()

    metrics = {
        "mae": mae,
        "records": len(records),
        "device": str(device),
        "val_loss": best_val if config.checkpoint_path else None,
    }
    registry_entry = create_registry_entry()
    save_metadata(registry_entry, {"training": metrics, "dataset": dataset_meta})
    save_config(
        registry_entry,
        {
            "universe_count": config.universe_count,
            "seed": config.seed,
            "epochs": config.epochs,
            "batch_size": config.batch_size,
            "learning_rate": config.learning_rate,
            "validation_split": config.validation_split,
        },
    )

    artifacts = {}
    if config.model_path:
        model_stem = Path(config.model_path).stem
        card = generate_model_card(model_stem, metrics, dataset_meta)
        card_path = registry_entry.artifacts_dir / f"{model_stem}.md"
        card_path.write_text(card, encoding="utf-8")
        artifacts["model_card"] = card_path
        artifacts["model_state"] = Path(config.model_path)

    if config.checkpoint_path:
        artifacts["checkpoint"] = Path(config.checkpoint_path)

    if artifacts:
        write_provenance(registry_entry, artifacts)

    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description="Train a physics foundation model.")
    parser.add_argument("--universe-count", type=int, default=500)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--learning-rate", type=float, default=1e-3)
    parser.add_argument("--validation-split", type=float, default=0.2)
    parser.add_argument("--checkpoint-path", type=str, default=None)
    parser.add_argument("--model-path", type=str, default=None)
    parser.add_argument("--metrics-path", type=str, default=None)
    parser.add_argument("--resume-checkpoint", type=str, default=None)
    parser.add_argument("--config", type=str, default=None)
    args = parser.parse_args()

    config_data: Dict[str, Any] = {}
    if args.config:
        try:
            import yaml
        except ImportError as exc:
            raise RuntimeError(
                "PyYAML is required for --config. Install it with `pip install -r requirements-train.txt`."
            ) from exc
        with open(args.config, "r", encoding="utf-8") as handle:
            config_data = yaml.safe_load(handle) or {}

    def pick(name: str, fallback: Any) -> Any:
        return config_data.get(name, fallback)

    model_path = Path(pick("model_path", args.model_path)).as_posix() if pick("model_path", args.model_path) else None
    checkpoint_path = Path(pick("checkpoint_path", args.checkpoint_path)).as_posix() if pick("checkpoint_path", args.checkpoint_path) else None
    metrics_path = Path(pick("metrics_path", args.metrics_path)).as_posix() if pick("metrics_path", args.metrics_path) else None

    metrics = train_model(
        TrainConfig(
            universe_count=pick("universe_count", args.universe_count),
            seed=pick("seed", args.seed),
            epochs=pick("epochs", args.epochs),
            batch_size=pick("batch_size", args.batch_size),
            learning_rate=pick("learning_rate", args.learning_rate),
            validation_split=pick("validation_split", args.validation_split),
            checkpoint_path=checkpoint_path,
            model_path=model_path,
            metrics_path=metrics_path,
            resume_checkpoint=pick("resume_checkpoint", args.resume_checkpoint),
        )
    )
    print("Training metrics:", metrics)


if __name__ == "__main__":
    main()
