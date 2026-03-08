import pandas as pd

from physics_ai.behavior_clustering import cluster_behavior


def test_cluster_behavior_assigns_labels() -> None:
    df = pd.DataFrame(
        {
            "defect_density": [0.1, 0.12, 0.11, 0.8, 0.78, 0.82],
            "vortex_count": [1, 2, 1, 10, 12, 11],
            "coherence_length": [0.5, 0.55, 0.52, 0.1, 0.12, 0.09],
            "spectral_entropy": [0.3, 0.28, 0.32, 0.9, 0.88, 0.92],
        }
    )
    clustered, labels = cluster_behavior(df, min_cluster_size=2, min_samples=1)
    assert "behavior_cluster_id" in clustered.columns
    assert "behavior_cluster_probability" in clustered.columns
    assert "behavior_cluster_size" in clustered.columns
    assert "behavior_cluster_outlier" in clustered.columns
    assert len(labels) == len(df)
    assert clustered["behavior_cluster_probability"].between(0.0, 1.0).all()
