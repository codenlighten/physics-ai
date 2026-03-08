"""Mode coupling analysis for nonlinear interactions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, Iterable, List, Tuple

import numpy as np


@dataclass
class CouplingResult:
    triads: List[Tuple[Tuple[int, int], Tuple[int, int], Tuple[int, int]]]
    coupling_strength: float


def triad_interactions(modes: Iterable[Tuple[int, int]]) -> List[Tuple[Tuple[int, int], Tuple[int, int], Tuple[int, int]]]:
    mode_list = list(modes)
    triads: List[Tuple[Tuple[int, int], Tuple[int, int], Tuple[int, int]]] = []
    for k1 in mode_list:
        for k2 in mode_list:
            k3 = (k1[0] + k2[0], k1[1] + k2[1])
            triads.append((k1, k2, k3))
    return triads


def energy_transfer(energy_series: np.ndarray) -> np.ndarray:
    return np.diff(energy_series, axis=0)


def coupling_strength(energy_series: np.ndarray) -> float:
    if energy_series.size == 0:
        return 0.0
    return float(np.var(energy_series))


def coupling_summary(
    dominant_modes: Iterable[Tuple[int, int]],
    temporal_signal: Iterable[float],
) -> Dict[str, Any]:
    modes = list(dominant_modes)
    triads = triad_interactions(modes)
    signal = np.array(list(temporal_signal), dtype=float)
    if signal.size == 0:
        return {
            "triads": triads,
            "coupling_strength": 0.0,
        }
    energy_series = np.stack([signal for _ in range(max(1, len(modes)))], axis=1)
    strength = coupling_strength(energy_series)
    return {
        "triads": triads,
        "coupling_strength": strength,
    }
