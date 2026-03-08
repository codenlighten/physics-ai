import numpy as np

from physics_ai.observer import observe_temporal_multi, observe_temporal_multi_batch


def test_observe_temporal_multi_batch_matches_single() -> None:
    rng = np.random.default_rng(1)
    frames = rng.random((5, 2, 8, 8))
    batch = np.stack([frames, frames], axis=2)

    single = observe_temporal_multi(frames, ["psi", "phi"])
    batch_metrics = observe_temporal_multi_batch(batch, ["psi", "phi"])

    assert len(batch_metrics) == 2
    for metrics in batch_metrics:
        assert metrics["psi_temporal_fft"] == single["psi_temporal_fft"]
        assert metrics["phi_temporal_fft"] == single["phi_temporal_fft"]
        assert metrics["temporal_fft"] == single["temporal_fft"]
        assert metrics["temporal_signal"] == single["temporal_signal"]
        assert metrics["cross_field_temporal_corr"] == single["cross_field_temporal_corr"]
