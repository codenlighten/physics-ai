import numpy as np

from physics_ai.observer import observe_temporal, observe_temporal_batch


def test_observe_temporal_batch_matches_single() -> None:
    frames = np.random.default_rng(0).random((6, 8, 8))
    batch = np.stack([frames, frames], axis=1)

    single = observe_temporal(frames)
    batch_metrics = observe_temporal_batch(batch)

    assert len(batch_metrics) == 2
    for metrics in batch_metrics:
        assert metrics["temporal_energy_start"] == single["temporal_energy_start"]
        assert metrics["temporal_energy_end"] == single["temporal_energy_end"]
        assert metrics["temporal_fft"] == single["temporal_fft"]
        assert metrics["temporal_signal"] == single["temporal_signal"]
