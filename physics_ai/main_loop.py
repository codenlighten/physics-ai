"""Main experiment loop for the physics-first prototype."""

from __future__ import annotations

from typing import Dict, List, Any
from pathlib import Path
import argparse
import os

import numpy as np

from .axioms import validate_axioms
from .evolution_engine import evolve, initialize_population
from .hypothesis_engine import discover_inverse_law, symmetry_hypotheses, harmonic_hypotheses
from .knowledge_graph import ConceptGraph
from .pattern_detector import kmeans
from .universe_engine import explore_universes
from .symbolic_discovery import discover_from_dataset
from .lagrangian_discovery import discover_lagrangian
from .noether_inference import infer_noether
from .theory_compression import TheoryCandidate, rank_theories
from .dispersion_extractor import dispersion_summary
from .mode_coupling import coupling_summary
from .checkpoint import (
    init_run,
    load_checkpoint_config,
    load_checkpoint_metadata,
    save_batch,
)


def _aggregate_symbolic_features(observations: List[Dict[str, Any]]) -> List[float]:
    keys = [
        "energy",
        "variance",
        "dominant_frequency",
        "rotation_score",
        "reflection_score",
        "so2_score",
        "node_count",
        "node_spacing",
        "peak_count",
    ]
    if not observations:
        return [0.0] * len(keys)
    matrix = np.array(
        [[float(obs.get(key, 0.0)) for key in keys] for obs in observations],
        dtype=float,
    )
    return [float(value) for value in np.mean(matrix, axis=0)]


def run_experiment(
    universe_count: int = 30,
    seed: int | None = None,
    generations: int = 10,
    discovery_log_path: str | Path | None = None,
    proposal_model_path: str | Path | None = None,
    universe_type: str | None = None,
    dynamics_type: str | None = None,
    store_fields: bool = False,
    batch_size: int = 1,
    debug_batch: bool = False,
    start_index: int = 0,
) -> Dict[str, Any]:
    dataset = explore_universes(
        universe_count,
        seed=seed,
        universe_type=universe_type,
        dynamics_type=dynamics_type,
        store_fields=store_fields,
        batch_size=batch_size,
        debug_batch=debug_batch,
        start_index=start_index,
    )
    observations: List[Dict[str, Any]] = [item["observation"] for item in dataset]

    for obs in observations:
        obs["axiom_checks"] = validate_axioms(obs)

    features = np.array(
        [[obs["energy"], obs["variance"], obs["dominant_frequency"]] for obs in observations]
    )
    labels, centroids = kmeans(features, k=min(3, len(observations)))

    inverse_law = discover_inverse_law(observations)
    feature_vector = _aggregate_symbolic_features(observations)
    templates = None
    log_path = Path(discovery_log_path) if discovery_log_path else Path(__file__).with_name(
        "discovery_log.jsonl"
    )
    model_path = (
        Path(proposal_model_path)
        if proposal_model_path
        else Path(__file__).with_name("proposal_net.pt")
    )
    on_result = None
    try:
        from .neural_symbolic import (
            ProposalConfig,
            append_discovery_log,
            build_proposal_network,
            build_training_dataset,
            load_discovery_log,
            load_proposal_network,
            propose_templates,
            save_proposal_network,
            train_proposal_net,
        )

        def _log_result(template: str, error: float) -> None:
            append_discovery_log(str(log_path), feature_vector, template, error)

        on_result = _log_result
        entries = load_discovery_log(str(log_path))
        features, labels = build_training_dataset(entries)
        input_dim = len(feature_vector)
        filtered = [(feat, label) for feat, label in zip(features, labels) if len(feat) == input_dim]
        model = build_proposal_network(ProposalConfig(input_dim=input_dim))
        if model_path.exists():
            load_proposal_network(model, str(model_path))
        if filtered:
            features, labels = zip(*filtered)
            train_proposal_net(model, list(features), list(labels), epochs=20)
            save_proposal_network(model, str(model_path))
        templates = propose_templates(model, feature_vector, top_k=3)
    except RuntimeError:
        pass
    symbolic_law = discover_from_dataset(observations, templates=templates, on_result=on_result)
    temporal_signal = next(
        (obs.get("temporal_signal") for obs in observations if obs.get("temporal_signal")),
        None,
    )
    lagrangian_result = (
        discover_lagrangian(temporal_signal, dt=1.0) if temporal_signal else None
    )
    noether_results = []
    temporal_observation = next(
        (obs for obs in observations if obs.get("temporal_signal")),
        None,
    )
    if temporal_observation:
        noether_results = infer_noether(
            temporal_observation,
            lagrangian=lagrangian_result.lagrangian if lagrangian_result else None,
            dt=1.0,
        )
    population = initialize_population(seed=seed)
    best_hypothesis = evolve(population, observations, generations=generations)

    theory_candidates = [
        TheoryCandidate(
            name="inverse_law",
            equation=inverse_law["equation"],
            error=float(inverse_law.get("error", 0.0)),
        )
    ]
    if symbolic_law:
        theory_candidates.append(
            TheoryCandidate(
                name="symbolic_law",
                equation=symbolic_law.law,
                error=float(symbolic_law.error),
            )
        )
    if lagrangian_result:
        theory_candidates.append(
            TheoryCandidate(
                name="lagrangian",
                equation=lagrangian_result.lagrangian,
                error=float(lagrangian_result.residual_mse),
            )
        )
    theory_scores = rank_theories(theory_candidates) if theory_candidates else []

    symmetry_rules = []
    harmonic_rules = []
    for obs in observations:
        symmetry_rules.extend(symmetry_hypotheses(obs))
        harmonic_rules.extend(harmonic_hypotheses(obs))

    graph = ConceptGraph()
    graph.add_relation("frequency", "inverse_wavelength", inverse_law, evidence="simulation")
    if symbolic_law:
        graph.add_relation(
            "frequency",
            "symbolic_law",
            {
                "equation": symbolic_law.law,
                "confidence": symbolic_law.confidence,
                "error": symbolic_law.error,
            },
            evidence="symbolic",
        )
    if lagrangian_result:
        graph.add_relation(
            "dynamics",
            "lagrangian",
            {
                "equation": lagrangian_result.lagrangian,
                "residual_mse": lagrangian_result.residual_mse,
                "residual_mean": lagrangian_result.residual_mean,
            },
            evidence="lagrangian",
        )
    for result in noether_results:
        graph.add_relation(
            "symmetry",
            "conserves",
            {
                "symmetry": result.symmetry,
                "quantity": result.conserved_quantity,
                "drift_ratio": result.drift_ratio,
                "lagrangian": lagrangian_result.lagrangian if lagrangian_result else None,
            },
            evidence="noether",
        )
    graph.add_relation(
        "frequency",
        "evolved_relation",
        {"equation": best_hypothesis.equation, "k": best_hypothesis.params["k"]},
        evidence="evolution",
    )
    for rule in sorted(set(symmetry_rules)):
        graph.add_relation("symmetry_group", "implies", {"equation": rule}, evidence="symmetry")
    for rule in sorted(set(harmonic_rules)):
        graph.add_relation("harmonic_ladder", "implies", {"equation": rule}, evidence="harmonics")
    if theory_scores:
        top = theory_scores[0]
        graph.add_relation(
            "theory",
            "compressed",
            {
                "equation": top.equation,
                "score": top.score,
                "complexity": top.complexity,
            },
            evidence="compression",
        )
    renormalization = next(
        (obs.get("renormalization") for obs in observations if obs.get("renormalization")),
        None,
    )
    if renormalization:
        graph.add_relation(
            "renormalization",
            "scale_invariance",
            {
                "invariance_score": renormalization.get("invariance_score"),
                "energy_flow": renormalization.get("energy_flow"),
            },
            evidence="renormalization",
        )
    gauge = next(
        (obs.get("gauge") for obs in observations if obs.get("gauge")),
        None,
    )
    if gauge:
        graph.add_relation(
            "symmetry",
            "gauge_invariance",
            gauge,
            evidence="gauge",
        )
    resonance = next(
        (obs.get("resonance_spectrum") for obs in observations if obs.get("resonance_spectrum")),
        None,
    )
    if resonance:
        graph.add_relation(
            "geometry",
            "resonance",
            resonance,
            evidence="geometry",
        )
    dispersion = None
    if resonance and temporal_signal:
        dispersion = dispersion_summary(resonance.get("dominant_modes", []), temporal_signal)
        graph.add_relation(
            "resonance",
            "dispersion_law",
            dispersion,
            evidence="dispersion",
        )
    coupling = None
    if resonance and temporal_signal:
        coupling = coupling_summary(resonance.get("dominant_modes", []), temporal_signal)
        graph.add_relation(
            "resonance",
            "nonlinear_interaction",
            coupling,
            evidence="coupling",
        )
    particles = next(
        (obs.get("particles") for obs in observations if obs.get("particles")),
        None,
    )
    interactions = next(
        (obs.get("interactions") for obs in observations if obs.get("interactions")),
        None,
    )
    if particles:
        graph.add_relation(
            "field",
            "emergent_particle",
            {
                "particle_count": particles.get("particle_count"),
                "tracks": particles.get("tracks"),
            },
            evidence="particles",
        )
    if interactions:
        graph.add_relation(
            "particle",
            "interaction",
            interactions,
            evidence="interactions",
        )

    return {
        "dataset": dataset,
        "observations": observations,
        "labels": labels,
        "centroids": centroids,
        "inverse_law": inverse_law,
        "symbolic_law": symbolic_law,
        "lagrangian": lagrangian_result,
        "noether": noether_results,
        "theory_scores": theory_scores,
        "renormalization": renormalization,
        "gauge": gauge,
        "resonance": resonance,
        "dispersion": dispersion,
        "coupling": coupling,
        "particles": particles,
    "interactions": interactions,
        "best_hypothesis": best_hypothesis,
        "symmetry_rules": symmetry_rules,
        "harmonic_rules": harmonic_rules,
        "graph": graph,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the physics-first experiment loop.")
    parser.add_argument("--universe-count", type=int, default=30)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--generations", type=int, default=10)
    parser.add_argument("--discovery-log-path", default=None)
    parser.add_argument("--proposal-model-path", default=None)
    parser.add_argument("--universe-type", default=None)
    parser.add_argument("--dynamics-type", default=None)
    parser.add_argument("--visualize", action="store_true")
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--no-show", action="store_true")
    parser.add_argument("--max-universes", type=int, default=1)
    parser.add_argument("--cuda", action="store_true")
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--debug-batch", action="store_true")
    parser.add_argument("--checkpoint-dir", default=None)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    if args.cuda:
        os.environ["PHYSICS_AI_CUDA"] = "1"
    if args.batch_size > 512:
        raise ValueError("Batch size too large for typical GPU memory (max 512).")

    resume_start = 0
    resume_from = None
    resume_config: Dict[str, Any] | None = None
    run_dir = None
    batch_index = 0
    if args.checkpoint_dir:
        resume_config = load_checkpoint_config(args.checkpoint_dir) if args.resume else None
        metadata = load_checkpoint_metadata(args.checkpoint_dir) if args.resume else None
        if metadata:
            resume_start = int(metadata.get("universes_processed", 0))
            batch_index = int(metadata.get("batches_completed", 0))
        if metadata and metadata.get("resume_from"):
            resume_from = str(metadata["resume_from"])

    base_config = resume_config or {}
    universe_type = args.universe_type if args.universe_type is not None else base_config.get("universe_type")
    dynamics_type = args.dynamics_type if args.dynamics_type is not None else base_config.get("dynamics_type")
    seed = args.seed if args.seed is not None else base_config.get("seed")
    batch_size = args.batch_size if args.batch_size is not None else base_config.get("batch_size", 1)

    results = run_experiment(
        universe_count=args.universe_count,
        seed=seed,
        generations=args.generations,
        discovery_log_path=args.discovery_log_path,
        proposal_model_path=args.proposal_model_path,
        universe_type=universe_type,
        dynamics_type=dynamics_type,
        store_fields=args.visualize,
        batch_size=batch_size,
        debug_batch=args.debug_batch,
        start_index=resume_start,
    )
    print("Discovered relation:", results["inverse_law"])
    print("Best evolved hypothesis:", results["best_hypothesis"])
    print("Concept graph:\n", results["graph"].summary())

    if args.checkpoint_dir:
        run_config = {
            "universe_count": args.universe_count,
            "seed": args.seed,
            "generations": args.generations,
            "discovery_log_path": args.discovery_log_path,
            "proposal_model_path": args.proposal_model_path,
            "universe_type": args.universe_type,
            "dynamics_type": args.dynamics_type,
            "batch_size": args.batch_size,
            "cuda": args.cuda,
            "resume": bool(args.resume),
            "resume_start": resume_start,
        }
        run_dir, _ = init_run(args.checkpoint_dir, run_config, resume=args.resume)
        save_batch(
            run_dir,
            results,
            start_index=resume_start,
            batch_index=batch_index,
            resume_from=resume_from,
        )
        print(f"Checkpoint saved to: {run_dir}")

    if args.visualize:
        from .visualization import render_summary

        render_summary(
            results,
            output_dir=args.output_dir,
            show=not args.no_show,
            max_universes=max(1, args.max_universes),
        )


if __name__ == "__main__":
    main()
