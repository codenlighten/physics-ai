"""Model card generation helpers."""

from __future__ import annotations

from typing import Dict, Any


def generate_model_card(
    model_name: str,
    metrics: Dict[str, Any],
    dataset_metadata: Dict[str, Any],
) -> str:
    lines = [
        f"# Model Card: {model_name}",
        "",
        "## Training Summary",
        f"- MAE: {metrics.get('mae')}",
        f"- Records: {metrics.get('records')}",
        f"- Device: {metrics.get('device')}",
        "",
        "## Dataset Metadata",
        f"- Record count: {dataset_metadata.get('record_count')}",
        f"- Feature names: {dataset_metadata.get('feature_names')}",
        f"- Schema hash: {dataset_metadata.get('schema_hash')}",
        f"- Generated at: {dataset_metadata.get('generated_at')}",
    ]
    return "\n".join(lines)
