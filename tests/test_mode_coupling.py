from physics_ai.mode_coupling import coupling_summary, triad_interactions


def test_triad_interactions() -> None:
    triads = triad_interactions([(1, 0), (0, 1)])
    assert triads


def test_coupling_summary_outputs() -> None:
    summary = coupling_summary([(1, 0), (0, 1)], [1.0, 0.5, -0.2])
    assert "coupling_strength" in summary
