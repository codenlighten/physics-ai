"""Detect particle interaction events from tracked particles."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, List, Tuple

import numpy as np


@dataclass
class InteractionEvent:
    event_type: str
    frame: int
    particles: Tuple[int, ...]
    distance: float | None = None


def _positions_by_frame(particles: Dict[str, Any]) -> Dict[int, List[Tuple[int, Tuple[int, int]]]]:
    frames: Dict[int, List[Tuple[int, Tuple[int, int]]]] = {}
    tracks = particles.get("tracks", []) if particles else []
    for track_idx, track in enumerate(tracks):
        positions = track.get("positions", [])
        frame_indices = track.get("frames", list(range(len(positions))))
        for frame, pos in zip(frame_indices, positions):
            frames.setdefault(int(frame), []).append((track_idx, tuple(pos)))
    return frames


def detect_collisions(particles: Dict[str, Any], radius: float = 2.0) -> List[InteractionEvent]:
    events: List[InteractionEvent] = []
    positions_by_frame = _positions_by_frame(particles)
    for frame, entries in positions_by_frame.items():
        for i, (idx_a, pos_a) in enumerate(entries):
            for idx_b, pos_b in entries[i + 1 :]:
                dist = float(np.linalg.norm(np.array(pos_a) - np.array(pos_b)))
                if dist <= radius:
                    events.append(InteractionEvent("collision", frame, (idx_a, idx_b), dist))
    return events


def detect_count_events(particles: Dict[str, Any]) -> List[InteractionEvent]:
    events: List[InteractionEvent] = []
    positions_by_frame = _positions_by_frame(particles)
    if not positions_by_frame:
        return events
    frames_sorted = sorted(positions_by_frame)
    prev_count = len(positions_by_frame[frames_sorted[0]])
    for frame in frames_sorted[1:]:
        count = len(positions_by_frame[frame])
        if count < prev_count:
            events.append(InteractionEvent("merge", frame, tuple(range(count))))
        elif count > prev_count:
            events.append(InteractionEvent("split", frame, tuple(range(count))))
        prev_count = count
    return events


def interaction_summary(particles: Dict[str, Any], radius: float = 2.0) -> Dict[str, Any]:
    if not particles:
        return {"events": [], "collision_count": 0, "merge_count": 0, "split_count": 0}
    collisions = detect_collisions(particles, radius=radius)
    count_events = detect_count_events(particles)
    events = collisions + count_events
    return {
        "events": [
            {
                "type": event.event_type,
                "frame": event.frame,
                "particles": event.particles,
                "distance": event.distance,
            }
            for event in events
        ],
        "collision_count": sum(1 for event in collisions if event.event_type == "collision"),
        "merge_count": sum(1 for event in count_events if event.event_type == "merge"),
        "split_count": sum(1 for event in count_events if event.event_type == "split"),
    }
