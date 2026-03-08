import os

from physics_ai.backend import get_xp, use_cuda


def test_backend_defaults_to_numpy() -> None:
    os.environ.pop("PHYSICS_AI_CUDA", None)
    xp = get_xp()
    assert xp.__name__ == "numpy"
    assert use_cuda() is False


def test_backend_cuda_env_without_cupy() -> None:
    os.environ["PHYSICS_AI_CUDA"] = "1"
    xp = get_xp()
    assert xp.__name__ == "numpy"
    assert use_cuda() is True
    os.environ.pop("PHYSICS_AI_CUDA", None)
