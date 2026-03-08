import numpy as np

from physics_ai.lagrangian_discovery import discover_lagrangian


def test_discover_lagrangian_harmonic() -> None:
    t = np.linspace(0, 2 * np.pi, 100)
    q = np.sin(t)
    result = discover_lagrangian(q, dt=t[1] - t[0])
    assert result is not None
    assert "qd" in result.lagrangian or "q" in result.lagrangian
    assert result.residual_mse < 1.0
