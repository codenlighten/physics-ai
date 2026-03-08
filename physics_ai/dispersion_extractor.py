"""Dispersion law extraction utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, Iterable, List, Tuple

import numpy as np

from .backend import as_xp, get_xp, to_numpy


@dataclass
class DispersionResult:
    coefficients: List[float]
    law_type: str
    omega: float
    k_values: List[float]


def wave_number(kx: int, ky: int) -> float:
    return float(np.sqrt(kx ** 2 + ky ** 2))


def extract_k_values(dominant_modes: Iterable[Tuple[int, int]]) -> List[float]:
    return [wave_number(kx, ky) for kx, ky in dominant_modes]


def temporal_frequency(signal: Iterable[float]) -> float:
    values = np.array(list(signal), dtype=float)
    if values.size == 0:
        return 0.0
    xp = get_xp()
    spectrum = xp.abs(xp.fft.rfft(as_xp(values)))
    return float(np.argmax(to_numpy(spectrum)))


def fit_dispersion(k_vals: List[float], omega_vals: List[float]) -> List[float]:
    if not k_vals or not omega_vals or len(k_vals) != len(omega_vals):
        return [0.0, 0.0, 0.0]
    degree = 2 if len(k_vals) >= 3 else 1
    coeffs = np.polyfit(k_vals, omega_vals, degree)
    if degree == 1:
        return [float(coeffs[0]), float(coeffs[1]), 0.0]
    return [float(coeff) for coeff in coeffs]


def classify_dispersion(coeffs: List[float], tol: float = 0.01) -> str:
    a, b, c = coeffs
    if abs(a) < tol and abs(b) >= tol:
        return "wave"
    if abs(a) >= tol and abs(b) < tol:
        return "diffusion"
    if abs(a) < tol and abs(b) < tol and abs(c) < tol:
        return "flat"
    return "unknown"


def dispersion_summary(dominant_modes: Iterable[Tuple[int, int]], signal: Iterable[float]) -> Dict[str, Any]:
    k_vals = extract_k_values(dominant_modes)
    omega = temporal_frequency(signal)
    omega_vals = [omega for _ in k_vals]
    coeffs = fit_dispersion(k_vals, omega_vals)
    law_type = classify_dispersion(coeffs)
    return {
        "coefficients": coeffs,
        "law_type": law_type,
        "omega": omega,
        "k_values": k_vals,
    }
