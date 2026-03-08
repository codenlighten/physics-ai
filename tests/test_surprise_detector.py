import pandas as pd

from physics_ai.surprise_detector import annotate_surprise, detect_surprises


def test_surprise_detector_flags_far_novel_points() -> None:
    df = pd.DataFrame(
        {
            "score": [9.5, 1.0, 9.1],
            "novelty_bonus": [2.0, 0.2, 1.6],
            "atlas_x": [0.0, 0.1, 5.0],
            "atlas_y": [0.0, 0.1, 5.0],
            "cluster_id": [0, 0, -1],
            "cluster_probability": [0.95, 0.8, 0.05],
        }
    )
    annotated = annotate_surprise(
        df,
        score_threshold=8.0,
        novelty_threshold=1.0,
        distance_threshold=1.0,
        density_threshold=0.51,
        density_k=2,
        cluster_probability_threshold=0.3,
    )
    assert "atlas_distance" in annotated.columns
    assert "local_density" in annotated.columns
    assert "density_score" in annotated.columns
    assert "density_surprise" in annotated.columns
    assert "cluster_outlier" in annotated.columns
    assert bool(annotated.loc[0, "density_surprise"]) is False
    assert bool(annotated.loc[2, "density_surprise"]) is True

    surprises = detect_surprises(
        df,
        score_threshold=8.0,
        novelty_threshold=1.0,
        distance_threshold=1.0,
        density_threshold=0.51,
        density_k=2,
        cluster_probability_threshold=0.3,
    )
    assert len(surprises) == 1
    assert surprises.index[0] == 2
