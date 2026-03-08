import os

import numpy as np
import pytest

from physics_ai.spectral_universe import SpectralConfig, generate_spectral_field


pytest.importorskip("cupy")


def test_spectral_field_gpu_parity() -> None:
    os.environ.pop("PHYSICS_AI_CUDA", None)
    cpu = generate_spectral_field(SpectralConfig(size=16, modes=3, seed=1))

    os.environ["PHYSICS_AI_CUDA"] = "1"
    gpu = generate_spectral_field(SpectralConfig(size=16, modes=3, seed=1))

    np.testing.assert_allclose(cpu, gpu, atol=1e-5)

    os.environ.pop("PHYSICS_AI_CUDA", None)
