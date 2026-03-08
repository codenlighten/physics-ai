import json

import pytest

from physics_ai.pll_m_dataset import FEATURE_COLUMNS, export_records
from physics_ai.train_pll_m import PLLMTrainConfig, train_pll_m


torch = pytest.importorskip("torch")


def test_train_pll_m_transformer(tmp_path) -> None:
    record = {
        "universe_id": 0,
        "universe_type": "random",
        "dynamics_type": "wave",
        "features": {col: 0.1 for col in FEATURE_COLUMNS},
        "feature_names": FEATURE_COLUMNS,
        "law_equation": "dpsi/dt = psi",
        "law_family": "test",
        "operator_tokens": ["psi"],
        "operator_signature": "psi",
    }
    dataset_path = tmp_path / "pll_m.jsonl"
    export_records([record], dataset_path.as_posix(), "jsonl")

    model_path = tmp_path / "pll_m.pt"
    metrics_path = tmp_path / "pll_m_metrics.json"
    vocab_path = tmp_path / "pll_m_vocab.json"

    metrics = train_pll_m(
        PLLMTrainConfig(
            dataset_path=dataset_path.as_posix(),
            epochs=1,
            batch_size=1,
            model_type="transformer",
            model_dim=32,
            num_heads=4,
            num_layers=1,
            dropout=0.0,
            model_path=model_path.as_posix(),
            metrics_path=metrics_path.as_posix(),
            vocab_path=vocab_path.as_posix(),
        )
    )

    assert metrics["model_type"] == "transformer"
    saved = json.loads(metrics_path.read_text(encoding="utf-8"))
    assert saved["records"] == 1
