import numpy as np

from physics_ai.renormalization import analyze_scales, coarse_grain


def test_coarse_grain_shape() -> None:
    field = np.random.default_rng(0).random((8, 8))
    coarse = coarse_grain(field)
    assert coarse.shape == (4, 4)


def test_analyze_scales_outputs() -> None:
    frames = np.random.default_rng(1).random((4, 16, 16))
    result = analyze_scales(frames)
    assert "invariance_score" in result
    assert result["scales"]
