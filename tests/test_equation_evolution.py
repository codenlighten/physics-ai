import numpy as np

from physics_ai.equation_evolution import apply_terms, default_terms, mutate_terms


def test_mutate_terms_keeps_laplacian() -> None:
    rng = np.random.default_rng(0)
    terms = mutate_terms(rng, ["laplacian"], p_toggle=1.0)
    assert "laplacian" in terms


def test_apply_terms_zeroes_coeffs() -> None:
    config = {"wave_nonlinear": 0.5, "wave_biharmonic": 0.2}
    updated = apply_terms(config, ["laplacian"])
    assert updated["wave_nonlinear"] == 0.0
    assert updated["wave_biharmonic"] == 0.0
