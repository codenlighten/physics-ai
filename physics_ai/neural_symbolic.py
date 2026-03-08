"""Neural-guided symbolic discovery helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Iterable, Dict, Tuple
import json
from pathlib import Path


EQUATION_TEMPLATES = [
    "k*x",
    "k/x",
    "k*x**2",
    "k/x**2",
    "k*sqrt(x)",
    "k*log(x)",
    "k*exp(x)",
]


@dataclass
class ProposalConfig:
    input_dim: int
    hidden: int = 64
    output_dim: int = len(EQUATION_TEMPLATES)


def build_proposal_network(config: ProposalConfig):
    try:
        import torch
        import torch.nn as nn
    except ImportError as exc:
        raise RuntimeError(
            "PyTorch is required for neural proposals. Install it with `pip install -r requirements-train.txt`."
        ) from exc

    return nn.Sequential(
        nn.Linear(config.input_dim, config.hidden),
        nn.ReLU(),
        nn.Linear(config.hidden, config.hidden),
        nn.ReLU(),
        nn.Linear(config.hidden, config.output_dim),
    )


def save_proposal_network(model, path: str) -> None:
    try:
        import torch
    except ImportError as exc:
        raise RuntimeError(
            "PyTorch is required for neural proposals. Install it with `pip install -r requirements-train.txt`."
        ) from exc

    torch.save(model.state_dict(), path)


def load_proposal_network(model, path: str) -> None:
    try:
        import torch
    except ImportError as exc:
        raise RuntimeError(
            "PyTorch is required for neural proposals. Install it with `pip install -r requirements-train.txt`."
        ) from exc

    state = torch.load(path, map_location="cpu")
    model.load_state_dict(state)


def template_subset(indices: List[int]) -> List[str]:
    return [EQUATION_TEMPLATES[idx] for idx in indices if 0 <= idx < len(EQUATION_TEMPLATES)]


def append_discovery_log(path: str, features: List[float], template: str, mse: float) -> None:
    record = {"features": features, "template": template, "mse": mse}
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(record) + "\n")


def load_discovery_log(path: str) -> List[Dict[str, object]]:
    entries: List[Dict[str, object]] = []
    if not Path(path).exists():
        return entries
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries


def build_training_dataset(entries: Iterable[Dict[str, object]]) -> Tuple[List[List[float]], List[int]]:
    features: List[List[float]] = []
    labels: List[int] = []
    for entry in entries:
        template = entry.get("template")
        if template in EQUATION_TEMPLATES:
            features.append(list(entry.get("features", [])))
            labels.append(EQUATION_TEMPLATES.index(template))
    return features, labels


def train_proposal_net(model, features: List[List[float]], labels: List[int], epochs: int = 10) -> None:
    if not features:
        return
    try:
        import torch
        import torch.nn as nn
        import torch.optim as optim
    except ImportError as exc:
        raise RuntimeError(
            "PyTorch is required for neural proposals. Install it with `pip install -r requirements-train.txt`."
        ) from exc

    optimizer = optim.Adam(model.parameters(), lr=1e-3)
    loss_fn = nn.CrossEntropyLoss()
    x = torch.tensor(features, dtype=torch.float32)
    y = torch.tensor(labels, dtype=torch.long)

    for _ in range(epochs):
        logits = model(x)
        loss = loss_fn(logits, y)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()


def propose_templates(model, feature_vector: List[float], top_k: int = 3) -> List[str]:
    try:
        import torch
    except ImportError as exc:
        raise RuntimeError(
            "PyTorch is required for neural proposals. Install it with `pip install -r requirements-train.txt`."
        ) from exc

    logits = model(torch.tensor(feature_vector, dtype=torch.float32))
    indices = torch.topk(logits, k=min(top_k, logits.numel())).indices.tolist()
    return template_subset(indices)
