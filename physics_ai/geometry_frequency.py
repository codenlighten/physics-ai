"""Geometry- and frequency-based analysis helpers."""

from __future__ import annotations

from typing import Dict, List, Tuple

import numpy as np


def detect_nodes(grid: np.ndarray, threshold: float = 1e-3) -> np.ndarray:
    return np.argwhere(np.abs(grid) < threshold)


def node_spacing(nodes: np.ndarray) -> float | None:
    if len(nodes) < 2:
        return None
    distances = np.linalg.norm(nodes[1:] - nodes[:-1], axis=1)
    return float(np.mean(distances)) if len(distances) > 0 else None


def symmetry_score(grid: np.ndarray) -> float:
    flipped = np.flip(grid)
    return float(np.mean(np.abs(grid - flipped)))


def frequency_peaks(grid: np.ndarray, count: int = 5) -> Tuple[np.ndarray, np.ndarray]:
    spectrum = np.abs(np.fft.fft2(grid))
    flat = spectrum.flatten()
    if flat.size == 0:
        return np.array([]), spectrum
    peak_indices = np.argsort(flat)[-count:]
    return peak_indices, spectrum


def harmonic_ratios(frequencies: List[float]) -> List[float]:
    ratios: List[float] = []
    if not frequencies:
        return ratios
    base = frequencies[0]
    if base == 0:
        return ratios
    for freq in frequencies[1:]:
        ratios.append(float(freq / base))
    return ratios


def detect_integer_harmonics(ratios: List[float], tol: float = 0.05) -> List[int]:
    matches: List[int] = []
    for ratio in ratios:
        nearest = round(ratio)
        if nearest > 1 and abs(ratio - nearest) < tol:
            matches.append(int(nearest))
    return matches


def detect_phi_ratios(ratios: List[float], tol: float = 0.05) -> List[str]:
    phi = (1 + 5 ** 0.5) / 2
    return ["phi" for ratio in ratios if abs(ratio - phi) < tol]


def peak_frequencies(spectrum: np.ndarray, peak_indices: np.ndarray) -> List[float]:
    if peak_indices.size == 0:
        return []
    coords = np.array(np.unravel_index(peak_indices, spectrum.shape)).T
    fx = np.fft.fftfreq(spectrum.shape[0])
    fy = np.fft.fftfreq(spectrum.shape[1])
    freqs = []
    for x, y in coords:
        freqs.append(float(np.sqrt(fx[x] ** 2 + fy[y] ** 2)))
    freqs = [f for f in freqs if f > 0]
    return sorted(freqs)


def geometry_frequency_features(grid: np.ndarray) -> Dict[str, float | int | List[float]]:
    nodes = detect_nodes(grid)
    spacing = node_spacing(nodes)
    peaks, spectrum = frequency_peaks(grid)
    freqs = peak_frequencies(spectrum, peaks)
    ratios = harmonic_ratios(freqs) if len(freqs) > 1 else []
    integer_harmonics = detect_integer_harmonics(ratios)
    phi_harmonics = detect_phi_ratios(ratios)

    return {
        "node_count": int(len(nodes)),
        "node_spacing": spacing if spacing is not None else 0.0,
        "symmetry": symmetry_score(grid),
        "peak_count": int(len(peaks)),
        "harmonic_ratios": ratios,
        "integer_harmonics": integer_harmonics,
        "phi_harmonics": phi_harmonics,
    }
