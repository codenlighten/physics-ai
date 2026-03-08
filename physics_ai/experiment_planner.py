"""Experiment planner for proposing new simulation configurations."""

from __future__ import annotations

import random
from typing import Dict, Any


UNIVERSE_TYPES = ["random", "spectral", "harmonic", "phi"]
DYNAMICS_TYPES = [
    "static",
    "wave",
    "diffusion",
    "reaction_diffusion",
    "multi_field",
    "oscillator",
    "schrodinger",
    "spectral_lagrangian",
    "geometry",
    "resonant_geometry",
]


def propose_experiment(
    seed: int | None = None,
    universe_type: str | None = None,
    dynamics_type: str | None = None,
) -> Dict[str, Any]:
    if seed is not None:
        random.seed(seed)
    chosen_type = universe_type or random.choice(UNIVERSE_TYPES)
    if chosen_type == "mixed":
        chosen_type = random.choice(UNIVERSE_TYPES)
    chosen_dynamics = dynamics_type or random.choice(DYNAMICS_TYPES)
    return {
        "wave_speed": random.uniform(0.5, 2.0),
        "wavelength": random.uniform(6.0, 16.0),
        "amplitude": random.uniform(0.5, 1.5),
        "wave_nonlinear": random.uniform(0.0, 0.4),
        "wave_biharmonic": random.uniform(0.0, 0.2),
        "pulse_position": random.randint(8, 56),
        "steps": random.randint(80, 160),
        "boundary": random.choice(["square", "torus"]),
        "size": random.choice([48, 64]),
        "universe_type": chosen_type,
        "dynamics_type": chosen_dynamics,
        "seed_count": random.randint(1, 3),
        "seed_types": ["gaussian", "dipole", "ring", "spiral"],
        "seed_amplitude_range": (0.4, 2.2),
        "seed_radius_range": (2.0, 8.0),
        "diffusion_psi": random.uniform(0.05, 0.25),
        "diffusion_phi": random.uniform(0.03, 0.2),
        "coupling_linear": random.uniform(0.3, 0.8),
        "coupling_quadratic": random.uniform(0.1, 0.5),
        "coupling_cross": random.uniform(0.1, 0.4),
        "psi_cubic": random.uniform(0.05, 0.3),
        "phi_cubic": random.uniform(0.05, 0.25),
        "psi_decay": random.uniform(0.01, 0.1),
        "phi_decay": random.uniform(0.01, 0.1),
        "dt": random.uniform(0.03, 0.08),
    }
