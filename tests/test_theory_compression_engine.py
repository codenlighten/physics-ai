from physics_ai.theory_compression_engine import sindy_fit


def test_sindy_fit_returns_equation() -> None:
    signal = [0.0, 0.2, 0.4, 0.3, 0.1]
    result = sindy_fit(signal, dt=1.0)
    assert "dx/dt" in result.equation
    assert result.residual >= 0.0
