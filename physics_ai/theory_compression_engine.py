"""Sparse regression (SINDy-style) for theory compression."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, List, Tuple

import numpy as np


@dataclass
class SINDyResult:
    coefficients: List[float]
    terms: List[str]
    equation: str
    residual: float


def _library(x: np.ndarray) -> Tuple[np.ndarray, List[str]]:
    terms = ["1", "x", "x^2", "x^3"]
    lib = np.stack([np.ones_like(x), x, x ** 2, x ** 3], axis=1)
    return lib, terms


def _sparse_regression(lib: np.ndarray, y: np.ndarray, threshold: float = 0.05) -> np.ndarray:
    coeffs, *_ = np.linalg.lstsq(lib, y, rcond=None)
    coeffs[np.abs(coeffs) < threshold] = 0.0
    return coeffs


def _format_equation(coeffs: np.ndarray, terms: List[str]) -> str:
    pieces = []
    for coeff, term in zip(coeffs, terms):
        if coeff == 0:
            continue
        pieces.append(f"{coeff:.3f}*{term}")
    return " + ".join(pieces) if pieces else "0"


def sindy_fit(signal: List[float], dt: float = 1.0, threshold: float = 0.05) -> SINDyResult:
    values = np.array(signal, dtype=float)
    if values.size < 3:
        return SINDyResult(coefficients=[0.0], terms=["x"], equation="0", residual=0.0)
    dx = np.gradient(values, dt)
    lib, terms = _library(values)
    coeffs = _sparse_regression(lib, dx, threshold=threshold)
    prediction = lib @ coeffs
    residual = float(np.mean((prediction - dx) ** 2))
    equation = f"dx/dt = {_format_equation(coeffs, terms)}"
    return SINDyResult(
        coefficients=[float(c) for c in coeffs],
        terms=terms,
        equation=equation,
        residual=residual,
    )


def compress_theory(observation: Dict[str, Any]) -> Dict[str, Any] | None:
    signal = observation.get("temporal_signal")
    if not signal:
        return None
    result = sindy_fit(signal, dt=1.0)
    return {
        "equation": result.equation,
        "residual": result.residual,
        "coefficients": result.coefficients,
        "terms": result.terms,
    }
