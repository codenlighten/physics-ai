import numpy as np

from physics_ai.gauge_discovery import gauge_invariance


def test_gauge_invariance_detects_global() -> None:
    frames = np.ones((2, 4, 4), dtype=np.complex128)
    result = gauge_invariance(frames, epsilon=1e-6)
    assert result.global_phase_invariant
