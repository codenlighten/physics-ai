from pathlib import Path

import numpy as np
import pandas as pd

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


def test_save_run_includes_cluster_fields(tmp_path: Path) -> None:
    results = {
        "dataset": [
            {
                "config": {"universe_type": "random", "dynamics_type": "wave"},
                "observation": {
                    "score": 9.0,
                    "novelty_bonus": 1.4,
                    "local_density": 0.12,
                    "density_score": 3.2,
                    "cluster_id": -1,
                    "cluster_probability": 0.05,
                    "cluster_size": 0,
                    "behavior_cluster_id": 2,
                    "behavior_cluster_probability": 0.4,
                    "behavior_cluster_size": 5,
                    "regime_signature": "high_vortex_count",
                    "dominant_ratio": 1.618,
                    "ratio_cluster_id": 1,
                    "ratio_constant_match": "phi",
                    "ratio_confidence": 0.9,
                    "law_equation": "dpsi/dt = -1.000 psi",
                    "law_terms": "psi",
                    "law_coefficients": "-1.000",
                    "law_fit_score": 0.9,
                    "law_validation_score": 0.85,
                },
            }
        ],
        "inverse_law": None,
        "symbolic_law": None,
        "lagrangian": None,
    }
    run_dir, _ = init_run(tmp_path, {"dynamics_type": "wave"})
    save_batch(run_dir, results, start_index=0, batch_index=0)
    df = pd.read_parquet(run_dir / "universes_batch_0000.parquet")
    assert "local_density" in df.columns
    assert "density_score" in df.columns
    assert "cluster_id" in df.columns
    assert "cluster_probability" in df.columns
    assert "cluster_size" in df.columns
    assert "behavior_cluster_id" in df.columns
    assert "behavior_cluster_probability" in df.columns
    assert "behavior_cluster_size" in df.columns
    assert "regime_signature" in df.columns
    assert "dominant_ratio" in df.columns
    assert "ratio_cluster_id" in df.columns
    assert "ratio_constant_match" in df.columns
    assert "ratio_confidence" in df.columns
    assert "law_equation" in df.columns
    assert "law_terms" in df.columns
    assert "law_coefficients" in df.columns
    assert "law_fit_score" in df.columns
    assert "law_validation_score" in df.columns
    assert df.loc[0, "cluster_id"] == -1


def test_save_batch_writes_graph_summary(tmp_path: Path) -> None:
    from physics_ai.knowledge_graph import ConceptGraph

    graph = ConceptGraph()
    graph.add_relation(
        "frequency",
        "inverse_law",
        {"equation": "omega = c/k"},
        object="omega = c/k",
        evidence="simulation",
    )

    results = {
        "dataset": [],
        "inverse_law": None,
        "symbolic_law": None,
        "lagrangian": None,
        "graph": graph,
    }
    run_dir, _ = init_run(tmp_path, {"dynamics_type": "wave"})
    save_batch(run_dir, results, start_index=0, batch_index=0)
    assert (run_dir / "graph_summary.json").exists()
    assert (run_dir / "graph_relations.json").exists()
