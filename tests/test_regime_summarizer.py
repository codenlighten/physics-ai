import pandas as pd

from physics_ai.regime_summarizer import summarize_behavior_clusters


def test_summarize_behavior_clusters_returns_labels() -> None:
    df = pd.DataFrame(
        {
            "behavior_cluster_id": [0, 0, 1, 1],
            "behavior_cluster_probability": [0.8, 0.9, 0.7, 0.6],
            "defect_density": [0.5, 0.6, 0.1, 0.12],
            "vortex_count": [10, 12, 1, 2],
            "coherence_length": [0.8, 0.85, 0.2, 0.25],
            "spectral_entropy": [0.2, 0.25, 0.9, 0.88],
            "variance": [0.4, 0.35, 0.9, 0.95],
            "particle_count": [5, 4, 1, 1],
            "law_family": ["reaction-diffusion", "reaction-diffusion", "nonlinear-wave", "nonlinear-wave"],
        }
    )
    summary = summarize_behavior_clusters(df)
    assert not summary.empty
    assert "label" in summary.columns
    assert "descriptors" in summary.columns
    assert "regime_signature" in summary.columns
    assert "law_family" in summary.columns
    assert summary.loc[0, "size"] == 2
    assert "reaction-diffusion" in summary.loc[0, "descriptors"]
