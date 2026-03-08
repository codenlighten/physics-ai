import numpy as np

from physics_ai.interaction_detector import detect_collisions, interaction_summary


def test_detect_collisions_with_close_tracks() -> None:
    particles = {
        "tracks": [
            {"positions": [(2, 2), (2, 3)], "frames": [0, 1]},
            {"positions": [(3, 2), (3, 3)], "frames": [0, 1]},
        ]
    }
    events = detect_collisions(particles, radius=1.5)
    assert events


def test_interaction_summary_counts() -> None:
    particles = {
        "tracks": [
            {"positions": [(0, 0), (0, 1)], "frames": [0, 1]},
            {"positions": [(4, 4)], "frames": [0]},
        ]
    }
    summary = interaction_summary(particles, radius=2.0)
    assert "events" in summary
    assert summary["merge_count"] + summary["split_count"] >= 0
