"""Particle-like structure detection in field frames."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, List, Tuple

import numpy as np


@dataclass
class ParticleTrack:
    positions: List[Tuple[int, int]]
    frames: List[int]

    @property
    def lifetime(self) -> int:
        return len(self.positions)

    @property
    def displacement(self) -> float:
        if len(self.positions) < 2:
            return 0.0
        start = np.array(self.positions[0], dtype=float)
        end = np.array(self.positions[-1], dtype=float)
        return float(np.linalg.norm(end - start))


def energy_density(field: np.ndarray) -> np.ndarray:
    grad_x, grad_y = np.gradient(field)
    return grad_x ** 2 + grad_y ** 2 + field ** 2


def _local_maxima(field: np.ndarray) -> np.ndarray:
    padded = np.pad(field, 1, mode="edge")
    center = padded[1:-1, 1:-1]
    maxima = np.ones_like(center, dtype=bool)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            if dx == 0 and dy == 0:
                continue
            neighbor = padded[1 + dx : 1 + dx + center.shape[0], 1 + dy : 1 + dy + center.shape[1]]
            maxima &= center >= neighbor
    return maxima


def detect_peaks(energy: np.ndarray, threshold: float = 0.6) -> np.ndarray:
    if energy.size == 0:
        return np.empty((0, 2), dtype=int)
    max_val = float(np.max(energy))
    if max_val == 0:
        return np.empty((0, 2), dtype=int)
    mask = _local_maxima(energy) & (energy >= threshold * max_val)
    return np.argwhere(mask)


def track_particles(peaks_by_frame: List[np.ndarray]) -> List[ParticleTrack]:
    tracks: List[ParticleTrack] = []
    for frame_idx, peaks in enumerate(peaks_by_frame):
        if peaks.size == 0:
            continue
        if not tracks:
            tracks.extend(
                ParticleTrack(positions=[tuple(p)], frames=[frame_idx]) for p in peaks
            )
            continue
        assigned = set()
        for track in tracks:
            last = np.array(track.positions[-1])
            distances = np.linalg.norm(peaks - last, axis=1)
            idx = int(np.argmin(distances))
            if idx not in assigned:
                track.positions.append(tuple(peaks[idx]))
                track.frames.append(frame_idx)
                assigned.add(idx)
        for idx, peak in enumerate(peaks):
            if idx not in assigned:
                tracks.append(ParticleTrack(positions=[tuple(peak)], frames=[frame_idx]))
    return tracks


def particle_summary(frames: np.ndarray, threshold: float = 0.6) -> Dict[str, Any]:
    if frames.size == 0:
        return {"particle_count": 0, "tracks": []}
    magnitudes = np.abs(frames)
    peaks_by_frame = []
    for frame in magnitudes:
        energy = energy_density(frame)
        peaks_by_frame.append(detect_peaks(energy, threshold=threshold))
    tracks = track_particles(peaks_by_frame)
    return {
        "particle_count": len(tracks),
        "tracks": [
            {
                "lifetime": track.lifetime,
                "displacement": track.displacement,
                "positions": track.positions,
                "frames": track.frames,
            }
            for track in tracks
        ],
    }
