"""Model card generation helpers."""

from __future__ import annotations

from typing import Dict, Any, List


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


def generate_pll_m_model_card(
    model_name: str,
    metrics: Dict[str, Any],
    dataset_metadata: Dict[str, Any],
    vocab: List[str],
) -> str:
    lines = [
        f"# Model Card: {model_name}",
        "",
        "## Training Summary",
        f"- Records: {metrics.get('records')}",
        f"- Operator vocab: {metrics.get('operator_vocab')}",
        f"- Exact match: {metrics.get('exact_match')}",
        f"- Mean Jaccard: {metrics.get('mean_jaccard')}",
        f"- Model type: {metrics.get('model_type')}",
        f"- Device: {metrics.get('device')}",
        "",
        "## Dataset Metadata",
        f"- Record count: {dataset_metadata.get('record_count')}",
        f"- Feature names: {dataset_metadata.get('feature_names')}",
        f"- Law families: {dataset_metadata.get('law_families')}",
        f"- Generated at: {dataset_metadata.get('generated_at')}",
        "",
        "## Operator Vocabulary (sample)",
        ", ".join(vocab[:25]) + (" ..." if len(vocab) > 25 else ""),
    ]
    return "\n".join(lines)
