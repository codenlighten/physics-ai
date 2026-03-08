from pathlib import Path

import numpy as np

from physics_ai.checkpoint import init_run, save_batch


def test_save_run_creates_artifacts(tmp_path: Path) -> None:
    results = {
        "dataset": [
            {
                "config": {"universe_type": "random", "dynamics_type": "wave"},
                "observation": {
                    "energy": 1.0,
                    "variance": 0.1,
                    "dominant_frequency": 2.0,
                    "particles": {
                        "particle_count": 1,
                        "tracks": [
                            {
                                "lifetime": 2,
                                "displacement": 1.5,
                                "positions": [(1, 1), (2, 2)],
                                "frames": [0, 1],
                            }
                        ],
                    },
                },
            }
        ],
        "inverse_law": {"equation": "omega = c/k", "confidence": 0.9, "error": 0.1},
        "symbolic_law": None,
        "lagrangian": None,
    }
    run_dir, metadata = init_run(tmp_path, {"dynamics_type": "wave"})
    assert metadata["batches_completed"] == 0
    save_batch(run_dir, results, start_index=5, batch_index=0)
    save_batch(run_dir, results, start_index=6, batch_index=1)
    assert (run_dir / "config.json").exists()
    assert (run_dir / "universes_batch_0000.parquet").exists()
    assert (run_dir / "particles_batch_0000.parquet").exists()
    assert (run_dir / "universes_batch_0001.parquet").exists()
    assert (run_dir / "particles_batch_0001.parquet").exists()
    assert (run_dir / "laws.json").exists()
    assert (run_dir / "metadata.json").exists()
