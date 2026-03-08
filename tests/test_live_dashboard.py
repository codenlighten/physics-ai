from pathlib import Path

import pandas as pd

from physics_ai.live_dashboard import build_live_atlas


def test_build_live_atlas(tmp_path: Path) -> None:
    df = pd.DataFrame(
        {
            "score": [1.0, 2.0, 3.0, 4.0, 5.0],
            "score_raw": [1.1, 2.1, 3.1, 4.1, 5.1],
            "particle_count": [0, 1, 2, 1, 0],
            "resonance_strength": [0.1, 0.2, 0.3, 0.2, 0.1],
            "variance": [0.05, 0.1, 0.2, 0.15, 0.05],
            "dispersion_type": ["wave", "diffusion", "wave", "wave", "diffusion"],
            "phase": ["LINEAR_WAVE", "SOLITON_FIELD", "TURBULENT_FIELD", "PARTICLE_SYSTEM", "LINEAR_WAVE"],
        }
    )
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    shard = run_dir / "universes_batch_0000.parquet"
    df.to_parquet(shard, index=False)

    embedded = build_live_atlas(run_dir, method="umap")
    assert "atlas_x" in embedded.columns
    assert "atlas_y" in embedded.columns
