import json
from pathlib import Path

import pandas as pd

from physics_ai.pll_m_dataset import build_pll_m_records, export_records, load_records


def test_pll_m_dataset_build_and_load(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    data = pd.DataFrame(
        [
            {
                "universe_id": 0,
                "universe_type": "random",
                "dynamics_type": "wave",
                "score_raw": 0.5,
                "score": 0.55,
                "spectral_entropy": 0.2,
                "rotation_score": 0.1,
                "translation_invariance": 0.8,
                "law_equation": "dpsi/dt = -psi + psi^3",
                "law_terms": ["psi", "psi^3"],
                "law_family": "nonlinear-wave",
            }
        ]
    )
    data.to_parquet(run_dir / "universes_batch_0000.parquet", index=False)
    (run_dir / "laws.json").write_text(
        json.dumps([{"equation": "dpsi/dt = -psi + psi^3", "type": "symbolic"}]),
        encoding="utf-8",
    )

    records = build_pll_m_records(str(run_dir))
    assert records
    assert "operator_tokens" in records[0]
    assert records[0]["law_equation"]

    output_path = export_records(records, str(run_dir / "dataset.jsonl"), "jsonl")
    loaded = load_records(output_path)
    assert loaded
    assert loaded[0]["operator_signature"]
