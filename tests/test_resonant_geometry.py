import numpy as np

from physics_ai.geometry_universe import GeometryConfig, resonant_rho, simulate_resonant_geometry


def test_resonant_rho_shape() -> None:
    rho = resonant_rho(10, modes=3, seed=0)
    assert rho.shape == (10, 10)
    assert np.all(rho >= 0)


def test_simulate_resonant_geometry_outputs() -> None:
    result = simulate_resonant_geometry(GeometryConfig(size=10, steps=4, seed=1, resonance_modes=2))
    assert result["rho"].shape == (10, 10)
    assert "resonance_strength" in result
