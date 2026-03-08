import pandas as pd

from physics_ai.ratio_analyzer import analyze_ratios, match_constant


def test_match_constant_phi() -> None:
    name, confidence = match_constant(1.618)
    assert name == "phi"
    assert confidence > 0.9


def test_analyze_ratios_extracts_clusters() -> None:
    df = pd.DataFrame(
        {
            "universe_id": [1, 2, 3],
            "temporal_fft": [
                [1.0, 1.618, 2.618],
                [1.0, 1.62, 2.62],
                [1.0, 1.61, 2.60],
            ],
        }
    )
    annotated, ratio_df, clusters = analyze_ratios(df, eps=0.1, min_samples=1)
    assert not ratio_df.empty
    assert "dominant_ratio" in annotated.columns
    assert not clusters.empty
    assert "constant_match" in clusters.columns
