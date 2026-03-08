import numpy as np

from physics_ai.observer import observe


def test_observe_includes_symmetry_group() -> None:
    grid = np.zeros((8, 8))
    metrics = observe(grid)
    assert "symmetry_group" in metrics
    assert "rotation_order" in metrics
    assert "reflection_score" in metrics
    assert "so2_score" in metrics
    assert "spectral_entropy" in metrics
    assert "energy_localization" in metrics
    assert "defect_density" in metrics
    assert "coherence_length" in metrics
    assert "harmonic_ratios" in metrics
    assert "integer_harmonics" in metrics
    assert "phi_harmonics" in metrics
