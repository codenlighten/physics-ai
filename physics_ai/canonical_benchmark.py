"""Pass/fail benchmark for canonical rediscovery runs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List

from .canonical_runner import CanonicalResult, run_canonical_suite


@dataclass
class BenchmarkCase:
    dynamics_type: str
    equation_checks: List[Callable[[str | None], bool]]
    requires_lagrangian: bool = True
    conserved_quantities: List[str] | None = None


@dataclass
class BenchmarkResult:
    dynamics_type: str
    passed: bool
    failures: List[str]


def _contains_any(text: str | None, tokens: List[str]) -> bool:
    if not text:
        return False
    lowered = text.lower()
    return any(token in lowered for token in tokens)


def default_cases() -> List[BenchmarkCase]:
    return [
        BenchmarkCase(
            dynamics_type="oscillator",
            equation_checks=[
                lambda eq: _contains_any(eq, ["x", "q"]),
            ],
            conserved_quantities=["energy"],
        ),
        BenchmarkCase(
            dynamics_type="diffusion",
            equation_checks=[
                lambda eq: _contains_any(eq, ["x", "k*"]) or _contains_any(eq, ["/x"]),
            ],
            conserved_quantities=None,
        ),
        BenchmarkCase(
            dynamics_type="wave",
            equation_checks=[
                lambda eq: _contains_any(eq, ["x", "k*"]),
            ],
            conserved_quantities=["energy"],
        ),
        BenchmarkCase(
            dynamics_type="schrodinger",
            equation_checks=[
                lambda eq: eq is not None,
            ],
            requires_lagrangian=False,
            conserved_quantities=None,
        ),
    ]


def evaluate_case(result: CanonicalResult, case: BenchmarkCase) -> BenchmarkResult:
    failures: List[str] = []
    for idx, check in enumerate(case.equation_checks):
        if not check(result.equation):
            failures.append(f"equation_check_{idx}")
    if case.requires_lagrangian and not result.lagrangian:
        failures.append("lagrangian_missing")
    if case.conserved_quantities:
        for quantity in case.conserved_quantities:
            if quantity not in result.conserved_quantities:
                failures.append(f"missing_conservation_{quantity}")
    return BenchmarkResult(
        dynamics_type=result.dynamics_type,
        passed=not failures,
        failures=failures,
    )


def run_benchmark(seed: int | None = 0, universe_count: int = 12) -> List[BenchmarkResult]:
    results = run_canonical_suite(seed=seed, universe_count=universe_count)
    cases = {case.dynamics_type: case for case in default_cases()}
    benchmark_results: List[BenchmarkResult] = []
    for result in results:
        case = cases.get(result.dynamics_type)
        if case:
            benchmark_results.append(evaluate_case(result, case))
    return benchmark_results


def main() -> None:
    results = run_benchmark()
    all_passed = True
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        print(f"{result.dynamics_type}: {status} {result.failures}")
        if not result.passed:
            all_passed = False
    if not all_passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
