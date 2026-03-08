import numpy as np

from physics_ai.symmetry_discovery import (
    translation_invariance,
    scale_invariance,
    phase_invariance,
    symmetry_profile,
)


def test_symmetry_invariance_scores() -> None:
    grid = np.ones((16, 16), dtype=float)
    assert translation_invariance(grid) > 0.9
    assert scale_invariance(grid) > 0.9

    complex_grid = np.zeros((8, 8), dtype=complex)
    assert phase_invariance(complex_grid) >= 0.9

    profile = symmetry_profile(grid)
    assert "translation_invariance" in profile
    assert "scale_invariance" in profile
    assert "phase_invariance" in profile
