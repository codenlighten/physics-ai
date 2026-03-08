import numpy as np

from physics_ai.symbolic_discovery import discover_inverse_law


def test_symbolic_inverse_law() -> None:
    x = np.array([1.0, 2.0, 4.0])
    y = 1.0 / x
    law = discover_inverse_law(x, y)
    assert law is not None
    assert law.error < 1e-6


def test_symbolic_on_result_callback() -> None:
    x = np.array([1.0, 2.0, 4.0])
    y = 2.0 / x
    calls = []

    def handle(template: str, error: float) -> None:
        calls.append((template, error))

    law = discover_inverse_law(x, y, templates=["k/x"], on_result=handle)
    assert law is not None
    assert calls
    assert calls[0][0] == "k/x"
