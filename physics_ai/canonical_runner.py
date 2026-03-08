"""Run canonical rediscovery suite for core physics targets."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, List

from .main_loop import run_experiment


@dataclass
class CanonicalResult:
    dynamics_type: str
    equation: str | None
    lagrangian: str | None
    conserved_quantities: List[str]


def _extract_equation(result: Dict[str, Any]) -> str | None:
    if result.get("symbolic_law"):
        return result["symbolic_law"].law
    return result.get("inverse_law", {}).get("equation")


def run_canonical_suite(seed: int | None = 0, universe_count: int = 12) -> List[CanonicalResult]:
    dynamics_types = ["oscillator", "diffusion", "wave", "schrodinger"]
    results: List[CanonicalResult] = []
    for dynamics in dynamics_types:
        output = run_experiment(
            universe_count=universe_count,
            seed=seed,
            generations=5,
            dynamics_type=dynamics,
        )
        equation = _extract_equation(output)
        lagrangian = output.get("lagrangian").lagrangian if output.get("lagrangian") else None
        conserved = [item.conserved_quantity for item in output.get("noether", [])]
        results.append(
            CanonicalResult(
                dynamics_type=dynamics,
                equation=equation,
                lagrangian=lagrangian,
                conserved_quantities=conserved,
            )
        )
    return results


def main() -> None:
    results = run_canonical_suite()
    for result in results:
        print(
            f"{result.dynamics_type}: equation={result.equation}, "
            f"lagrangian={result.lagrangian}, conserved={result.conserved_quantities}"
        )


if __name__ == "__main__":
    main()
