import pandas as pd

from physics_ai.regime_clustering import cluster_atlas


def test_cluster_atlas_assigns_clusters() -> None:
    df = pd.DataFrame(
        {
            "atlas_x": [0.0, 0.1, -0.1, 5.0, 5.1, 4.9],
            "atlas_y": [0.0, 0.1, -0.1, 5.0, 5.1, 4.9],
        }
    )
    clustered, labels = cluster_atlas(df, min_cluster_size=2, min_samples=1)
    assert "cluster_id" in clustered.columns
    assert "cluster_probability" in clustered.columns
    assert "cluster_size" in clustered.columns
    assert len(labels) == len(df)
    assert clustered["cluster_probability"].between(0.0, 1.0).all()
    assert clustered["cluster_size"].ge(0).all()
