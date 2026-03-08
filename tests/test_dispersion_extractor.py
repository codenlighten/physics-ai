from physics_ai.dispersion_extractor import classify_dispersion, dispersion_summary


def test_dispersion_summary_outputs() -> None:
    summary = dispersion_summary([(1, 0), (0, 1)], [1.0, 0.0, -1.0, 0.0])
    assert "coefficients" in summary
    assert "law_type" in summary


def test_classify_dispersion_wave() -> None:
    law = classify_dispersion([0.0, 1.0, 0.0])
    assert law == "wave"
