"""PLL-M dataset utilities for atlas-driven physics language modeling."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List
import re

import pandas as pd

from .universe_atlas import load_universe_shards


FEATURE_COLUMNS = [
    "score_raw",
    "score",
    "particle_count",
    "resonance_strength",
    "curvature_strength",
    "variance",
    "spectral_entropy",
    "energy_localization",
    "diversity_penalty",
    "novelty_bonus",
    "rotation_score",
    "reflection_score",
    "so2_score",
    "translation_invariance",
    "scale_invariance",
    "phase_invariance",
    "temporal_energy_drift_ratio",
    "temporal_momentum_drift_ratio",
    "psi_defect_density",
    "phi_defect_density",
    "cross_field_corr",
    "cross_field_temporal_corr",
    "atlas_x",
    "atlas_y",
]


@dataclass
class PLLMDatasetConfig:
    run_dir: str
    atlas_path: str | None = None
    output_path: str | None = None
    output_format: str = "jsonl"


def _load_laws(run_dir: str | Path) -> List[Dict[str, Any]]:
    law_path = Path(run_dir) / "laws.json"
    if not law_path.exists():
        return []
    with open(law_path, "r", encoding="utf-8") as handle:
        return json.load(handle) or []


def _select_run_level_equation(laws: Iterable[Dict[str, Any]]) -> tuple[str | None, str | None]:
    selected_equation = None
    selected_family = None
    for law in laws:
        if law.get("type") in {"symbolic", "lagrangian"}:
            selected_equation = law.get("equation")
            selected_family = law.get("type")
            break
    if selected_equation is None:
        for law in laws:
            if law.get("equation"):
                selected_equation = law.get("equation")
                selected_family = law.get("type")
                break
    return selected_equation, selected_family


def _extract_operator_tokens(equation: str | None, law_terms: Any) -> List[str]:
    tokens: List[str] = []
    if isinstance(law_terms, list):
        tokens.extend(str(term) for term in law_terms)
    elif isinstance(law_terms, str):
        tokens.extend([term.strip() for term in law_terms.split(",") if term.strip()])
    if equation:
        tokens.extend(re.findall(r"[A-Za-z_]+(?:\^\d+)?", equation))
    cleaned = []
    for token in tokens:
        if token and token not in cleaned:
            cleaned.append(token)
    return cleaned


def _attach_atlas(df: pd.DataFrame, atlas_path: str | None) -> pd.DataFrame:
    if atlas_path is None:
        return df
    path = Path(atlas_path)
    if not path.exists():
        raise FileNotFoundError(f"Atlas file not found: {path}")
    if path.suffix == ".parquet":
        atlas = pd.read_parquet(path)
    else:
        atlas = pd.read_csv(path)
    if "atlas_x" in df.columns and "atlas_y" in df.columns:
        return df
    if "universe_id" in df.columns and "universe_id" in atlas.columns:
        merged = df.merge(atlas[["universe_id", "atlas_x", "atlas_y"]], on="universe_id", how="left")
        return merged
    return atlas


def build_pll_m_records(run_dir: str, atlas_path: str | None = None) -> List[Dict[str, Any]]:
    df = load_universe_shards(run_dir)
    df = _attach_atlas(df, atlas_path)
    laws = _load_laws(run_dir)
    fallback_equation, fallback_family = _select_run_level_equation(laws)

    records: List[Dict[str, Any]] = []
    for _, row in df.iterrows():
        equation = row.get("law_equation") or fallback_equation
        law_family = row.get("law_family") or fallback_family
        tokens = _extract_operator_tokens(equation, row.get("law_terms"))
        operator_signature = " ".join(sorted(set(tokens))) if tokens else "unknown"
        features = {col: float(row.get(col, 0.0) or 0.0) for col in FEATURE_COLUMNS}
        records.append({
            "universe_id": int(row.get("universe_id")) if not pd.isna(row.get("universe_id")) else None,
            "universe_type": row.get("universe_type"),
            "dynamics_type": row.get("dynamics_type"),
            "features": features,
            "feature_names": list(features.keys()),
            "law_equation": equation,
            "law_family": law_family,
            "operator_tokens": tokens,
            "operator_signature": operator_signature,
        })
    return records


def build_pll_m_metadata(records: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    records = list(records)
    return {
        "record_count": len(records),
        "feature_names": FEATURE_COLUMNS,
        "law_families": sorted({rec.get("law_family") for rec in records if rec.get("law_family")}),
        "generated_at": pd.Timestamp.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def records_to_frame(records: Iterable[Dict[str, Any]]) -> pd.DataFrame:
    flat_rows: List[Dict[str, Any]] = []
    for record in records:
        row = {
            "universe_id": record.get("universe_id"),
            "universe_type": record.get("universe_type"),
            "dynamics_type": record.get("dynamics_type"),
            "law_equation": record.get("law_equation"),
            "law_family": record.get("law_family"),
            "operator_signature": record.get("operator_signature"),
            "operator_tokens": json.dumps(record.get("operator_tokens") or []),
        }
        features = record.get("features") or {}
        row.update(features)
        flat_rows.append(row)
    return pd.DataFrame(flat_rows)


def export_records(records: Iterable[Dict[str, Any]], output_path: str, output_format: str) -> Path:
    path = Path(output_path)
    output_format = output_format.lower()
    if output_format == "jsonl":
        with open(path, "w", encoding="utf-8") as handle:
            for record in records:
                handle.write(json.dumps(record) + "\n")
        return path
    frame = records_to_frame(records)
    if output_format == "parquet":
        frame.to_parquet(path, index=False)
    else:
        frame.to_csv(path, index=False)
    return path


def load_records(dataset_path: str | Path) -> List[Dict[str, Any]]:
    path = Path(dataset_path)
    if path.suffix == ".jsonl":
        records: List[Dict[str, Any]] = []
        with open(path, "r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    records.append(json.loads(line))
        return records
    if path.suffix == ".parquet":
        frame = pd.read_parquet(path)
    else:
        frame = pd.read_csv(path)
    records: List[Dict[str, Any]] = []
    for _, row in frame.iterrows():
        features = {col: float(row.get(col, 0.0) or 0.0) for col in FEATURE_COLUMNS}
        tokens = json.loads(row.get("operator_tokens", "[]")) if isinstance(row.get("operator_tokens"), str) else []
        records.append({
            "universe_id": row.get("universe_id"),
            "universe_type": row.get("universe_type"),
            "dynamics_type": row.get("dynamics_type"),
            "features": features,
            "feature_names": list(features.keys()),
            "law_equation": row.get("law_equation"),
            "law_family": row.get("law_family"),
            "operator_tokens": tokens,
            "operator_signature": row.get("operator_signature"),
        })
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description="Build PLL-M training datasets from run checkpoints.")
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--atlas", default=None)
    parser.add_argument("--output", default="pll_m_dataset.jsonl")
    parser.add_argument("--format", default="jsonl", choices=["jsonl", "csv", "parquet"])
    args = parser.parse_args()

    records = build_pll_m_records(args.run_dir, atlas_path=args.atlas)
    export_path = export_records(records, args.output, args.format)
    print(f"PLL-M dataset saved to: {export_path}")


if __name__ == "__main__":
    main()
