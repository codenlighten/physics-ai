"""Backend selection for optional GPU acceleration."""

from __future__ import annotations

import os
from typing import Any

import numpy as np

try:
    import cupy as _cupy  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    _cupy = None


def use_cuda() -> bool:
    return os.environ.get("PHYSICS_AI_CUDA") == "1"


def backend_name() -> str:
    if use_cuda() and _cupy is not None:
        return "cupy"
    return "numpy"


def get_xp():
    if use_cuda() and _cupy is not None:
        return _cupy
    if use_cuda() and _cupy is None:
        print("⚠ CUDA requested but CuPy not installed — falling back to CPU.")
    return np


def as_xp(array: Any):
    xp = get_xp()
    if xp is np:
        return np.asarray(array)
    return xp.asarray(array)


def to_numpy(array: Any) -> np.ndarray:
    if _cupy is not None and isinstance(array, _cupy.ndarray):
        return array.get()
    return np.asarray(array)
