import os

import numpy as np
import pytest

from physics_ai.observer import observe


pytest.importorskip("cupy")


def test_observe_gpu_parity() -> None:
    grid = np.random.default_rng(0).random((16, 16))

    os.environ.pop("PHYSICS_AI_CUDA", None)
    cpu = observe(grid)

    os.environ["PHYSICS_AI_CUDA"] = "1"
    gpu = observe(grid)

    assert cpu["dominant_frequency"] == gpu["dominant_frequency"]
    np.testing.assert_allclose(cpu["energy"], gpu["energy"], atol=1e-5)
    np.testing.assert_allclose(cpu["spectral_entropy"], gpu["spectral_entropy"], atol=1e-5)

    os.environ.pop("PHYSICS_AI_CUDA", None)
