import pandas as pd

from physics_ai.regime_evolution import detect_regime_transitions


def test_detect_regime_transitions_finds_split() -> None:
    df = pd.DataFrame(
        {
            "generation": [0, 0, 0, 1, 1, 1, 1],
            "regime_signature": [
                "high_vortex_count",
                "high_vortex_count",
                "high_vortex_count",
                "high_vortex_count_low_entropy",
                "high_vortex_count_low_entropy",
                "high_vortex_count_high_entropy",
                "high_vortex_count_high_entropy",
            ],
        }
    )
    transitions = detect_regime_transitions(df, min_count=2, min_similarity=0.3)
    assert not transitions.empty
    assert "split" in transitions["event"].values
