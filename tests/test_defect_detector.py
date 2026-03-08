import numpy as np

from physics_ai.defect_detector import defect_summary, nodal_loop_count


def test_nodal_loop_count_nonzero() -> None:
    field = np.array([[1.0, -1.0], [-1.0, 1.0]])
    assert nodal_loop_count(field) > 0


def test_defect_summary_keys() -> None:
    field = np.random.default_rng(0).random((6, 6))
    summary = defect_summary(field)
    assert "defect_density" in summary
    assert "coherence_length" in summary
