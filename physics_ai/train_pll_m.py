"""Train a minimal PLL-M operator predictor from atlas datasets."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, List, Tuple

import numpy as np

from .pll_m_dataset import FEATURE_COLUMNS, build_pll_m_metadata, load_records
from .model_card import generate_pll_m_model_card
from .model_registry import create_registry_entry, save_config, save_metadata, write_provenance


@dataclass
class PLLMTrainConfig:
    dataset_path: str
    epochs: int = 60
    batch_size: int = 64
    learning_rate: float = 1e-3
    model_type: str = "transformer"
    model_dim: int = 64
    num_heads: int = 4
    num_layers: int = 2
    dropout: float = 0.1
    tags: List[str] | None = None
    model_path: str | None = None
    metrics_path: str | None = None
    vocab_path: str | None = None


def _build_vocab(records: List[Dict[str, Any]]) -> List[str]:
    tokens: List[str] = []
    for record in records:
        operators = record.get("operator_tokens") or []
        if not operators and record.get("law_family"):
            operators = [f"family:{record['law_family']}"]
        for token in operators:
            if token not in tokens:
                tokens.append(token)
    return tokens


def _build_arrays(records: List[Dict[str, Any]], vocab: List[str]) -> Tuple[np.ndarray, np.ndarray]:
    features = np.array(
        [[float(record.get("features", {}).get(col, 0.0)) for col in FEATURE_COLUMNS] for record in records],
        dtype=np.float32,
    )
    labels = np.zeros((len(records), len(vocab)), dtype=np.float32)
    index = {token: idx for idx, token in enumerate(vocab)}
    for row_idx, record in enumerate(records):
        tokens = record.get("operator_tokens") or []
        if not tokens and record.get("law_family"):
            tokens = [f"family:{record['law_family']}"]
        for token in tokens:
            if token in index:
                labels[row_idx, index[token]] = 1.0
    return features, labels


def _build_model(
    input_dim: int,
    vocab_size: int,
    config: PLLMTrainConfig,
):
    import torch
    from torch import nn

    if config.model_type == "mlp":
        return nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, vocab_size),
        )

    class FeatureTransformer(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.feature_proj = nn.Linear(1, config.model_dim)
            self.feature_embed = nn.Parameter(torch.randn(input_dim, config.model_dim))
            encoder_layer = nn.TransformerEncoderLayer(
                d_model=config.model_dim,
                nhead=config.num_heads,
                dropout=config.dropout,
                batch_first=True,
            )
            self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=config.num_layers)
            self.head = nn.Sequential(
                nn.LayerNorm(config.model_dim),
                nn.Linear(config.model_dim, vocab_size),
            )

        def forward(self, features: torch.Tensor) -> torch.Tensor:
            tokens = self.feature_proj(features.unsqueeze(-1))
            tokens = tokens + self.feature_embed.unsqueeze(0)
            encoded = self.encoder(tokens)
            pooled = encoded.mean(dim=1)
            return self.head(pooled)

    return FeatureTransformer()


def train_pll_m(config: PLLMTrainConfig) -> Dict[str, Any]:
    try:
        import torch
        from torch import nn
        from torch.utils.data import DataLoader, TensorDataset
    except ImportError as exc:
        raise RuntimeError(
            "PyTorch is required for PLL-M training. Install it with `pip install -r requirements-train.txt`."
        ) from exc

    records = load_records(config.dataset_path)
    if not records:
        raise ValueError("Dataset is empty.")
    vocab = _build_vocab(records)
    features, labels = _build_arrays(records, vocab)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    dataset = TensorDataset(torch.from_numpy(features), torch.from_numpy(labels))
    loader = DataLoader(dataset, batch_size=config.batch_size, shuffle=True)

    model = _build_model(features.shape[1], labels.shape[1], config).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=config.learning_rate)
    loss_fn = nn.BCEWithLogitsLoss()

    for _ in range(config.epochs):
        model.train()
        for batch_x, batch_y in loader:
            batch_x = batch_x.to(device)
            batch_y = batch_y.to(device)
            optimizer.zero_grad()
            logits = model(batch_x)
            loss = loss_fn(logits, batch_y)
            loss.backward()
            optimizer.step()

    model.eval()
    with torch.no_grad():
        logits = model(torch.from_numpy(features).to(device))
        probs = torch.sigmoid(logits).cpu().numpy()

    predictions = (probs >= 0.5).astype(int)
    targets = labels.astype(int)
    exact_match = float(np.mean(np.all(predictions == targets, axis=1))) if targets.size else 0.0
    jaccard = []
    for pred, target in zip(predictions, targets):
        union = np.logical_or(pred, target).sum()
        if union == 0:
            jaccard.append(1.0)
        else:
            jaccard.append(float(np.logical_and(pred, target).sum()) / float(union))
    mean_jaccard = float(np.mean(jaccard)) if jaccard else 0.0

    metrics = {
        "records": len(records),
        "operator_vocab": len(vocab),
        "exact_match": exact_match,
        "mean_jaccard": mean_jaccard,
        "device": str(device),
        "model_type": config.model_type,
    }

    registry_entry = create_registry_entry()
    dataset_meta = build_pll_m_metadata(records)
    tags = sorted(set(config.tags or []))
    save_metadata(registry_entry, {"training": metrics, "dataset": dataset_meta, "tags": tags})
    save_config(
        registry_entry,
        {
            "dataset_path": config.dataset_path,
            "epochs": config.epochs,
            "batch_size": config.batch_size,
            "learning_rate": config.learning_rate,
            "model_type": config.model_type,
            "model_dim": config.model_dim,
            "num_heads": config.num_heads,
            "num_layers": config.num_layers,
            "dropout": config.dropout,
            "tags": tags,
        },
    )

    if config.model_path:
        torch.save(model.state_dict(), config.model_path)
    if config.metrics_path:
        Path(config.metrics_path).write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    if config.vocab_path:
        Path(config.vocab_path).write_text(json.dumps(vocab, indent=2), encoding="utf-8")

    model_name = Path(config.model_path).stem if config.model_path else "pll_m"
    card = generate_pll_m_model_card(model_name, metrics, dataset_meta, vocab)
    card_path = registry_entry.artifacts_dir / f"{model_name}.md"
    card_path.write_text(card, encoding="utf-8")

    artifacts = {"model_card": card_path}
    if config.model_path:
        artifacts["model_state"] = Path(config.model_path)
    if config.metrics_path:
        artifacts["metrics"] = Path(config.metrics_path)
    if config.vocab_path:
        artifacts["vocab"] = Path(config.vocab_path)
    if artifacts:
        write_provenance(registry_entry, artifacts)

    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description="Train PLL-M from atlas datasets.")
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--epochs", type=int, default=60)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--learning-rate", type=float, default=1e-3)
    parser.add_argument("--model-type", default="transformer", choices=["transformer", "mlp"])
    parser.add_argument("--model-dim", type=int, default=64)
    parser.add_argument("--num-heads", type=int, default=4)
    parser.add_argument("--num-layers", type=int, default=2)
    parser.add_argument("--dropout", type=float, default=0.1)
    parser.add_argument("--tags", default=None, help="Comma-separated tag list for registry metadata.")
    parser.add_argument("--model-path", default=None)
    parser.add_argument("--metrics-path", default=None)
    parser.add_argument("--vocab-path", default=None)
    args = parser.parse_args()

    tags = [tag.strip() for tag in args.tags.split(",") if tag.strip()] if args.tags else None

    metrics = train_pll_m(
        PLLMTrainConfig(
            dataset_path=args.dataset,
            epochs=args.epochs,
            batch_size=args.batch_size,
            learning_rate=args.learning_rate,
            model_type=args.model_type,
            model_dim=args.model_dim,
            num_heads=args.num_heads,
            num_layers=args.num_layers,
            dropout=args.dropout,
            tags=tags,
            model_path=args.model_path,
            metrics_path=args.metrics_path,
            vocab_path=args.vocab_path,
        )
    )
    print("PLL-M training metrics:", metrics)


if __name__ == "__main__":
    main()
