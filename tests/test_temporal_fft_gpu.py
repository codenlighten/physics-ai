import os

import numpy as np
import pytest

from physics_ai.observer import temporal_fft


pytest.importorskip("cupy")


def test_temporal_fft_gpu_parity() -> None:
    frames = np.random.default_rng(0).random((8, 8, 8))

    os.environ.pop("PHYSICS_AI_CUDA", None)
    cpu = temporal_fft(frames)

    os.environ["PHYSICS_AI_CUDA"] = "1"
    gpu = temporal_fft(frames)

    np.testing.assert_allclose(cpu, gpu, atol=1e-5)

    os.environ.pop("PHYSICS_AI_CUDA", None)
