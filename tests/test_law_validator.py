import numpy as np

from physics_ai.law_validator import behavior_validation_score, regime_match_score


def test_behavior_validation_score_matches_linear_growth() -> None:
    signal = np.array([0.0, 1.0, 2.0, 3.0])
    operator_matrix = np.ones((signal.size, 1))
    coeffs = np.array([1.0])

    score = behavior_validation_score(coeffs, operator_matrix, signal)

    assert score == 1.0


def test_regime_match_score_identical_metrics() -> None:
    metrics = {
        "vortex_count": 2.0,
        "coherence_length": 1.5,
        "spectral_entropy": 0.4,
        "defect_density": 0.1,
    }
    score = regime_match_score(metrics, metrics)
    assert score == 1.0
