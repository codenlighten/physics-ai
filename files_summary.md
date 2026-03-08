# Physics AI File Summary

This document captures a rolling summary of the `physics_ai` module files, reviewed in order of most recently modified first.

## 2026-03-08 (Batch 1: most recent files)

### `physics_ai/main_loop.py`
- Orchestrates the end-to-end experiment loop: universe exploration, observation enrichment, symbolic law discovery, evolutionary hypothesis search, and theory compression ranking.
- Builds and enriches a `ConceptGraph` with relations from symbolic laws, Noether results, renormalization, gauge, resonance/dispersion, particles, and interactions.
- Supports YAML run presets, checkpoint resume, batching, optional CUDA flag, and appends run metadata to `runs.jsonl` via the run registry.

### `physics_ai/run_registry.py`
- Minimal JSONL run registry writer with UTC timestamps for recording experiment metadata.

### `physics_ai/observer.py`
- Computes per-field observation metrics (energy, variance, spectra, symmetry, defects, geometry frequency).
- Adds temporal analysis utilities: FFT, energy/momentum drift ratios, particle summaries, and batch-capable temporal feature extraction.
- Provides multi-field temporal aggregation (cross-field correlation, combined signals/FFTs) and multi-field batch metrics.

### `physics_ai/benchmark_runner.py`
- CLI benchmark harness for batched wave/diffusion dynamics, reporting elapsed time and per-step latency.
- Optional CSV append mode with backend/mode parameters.

### `physics_ai/universe_engine.py`
- Core universe exploration pipeline for single and batched universes across multiple dynamics types.
- Handles initial condition generation, run batching, temporal observation integration, renormalization/gauge/particle/interactions, and phase scoring.
- Supports multi-field and reaction-diffusion paths with dedicated temporal metrics and per-universe scoring plus diversity/novelty bonuses.

## 2026-03-08 (Batch 2)

### `physics_ai/field_dynamics.py`
- Batched-friendly PDE solvers for wave, diffusion, reaction-diffusion, oscillator, Schrödinger, and coupled-field systems.
- Uses backend abstraction (`get_xp`, `as_xp`) for CPU/GPU parity and returns NumPy arrays.

### `physics_ai/spectral_lagrangian.py`
- Spectral-mode simulator for Lagrangian-style oscillators; generates eigenmodes, evolves amplitudes, and reconstructs spatial fields.
- Supports configurable modes/omegas and backend-aware operations for GPU readiness.

### `physics_ai/spectral_universe.py`
- Generates initial universe fields via random, spectral, harmonic, or golden-ratio ($\phi$) constructions.
- Backend-aware array generation with dataclass configs.

### `physics_ai/simulation.py`
- Core `WaveSimulation` initializer/stepper for 2D wave grids with optional pulse seeding and boundary controls.
- Backend-aware compute and returns final grid as NumPy.

### `physics_ai/live_dashboard.py`
- Streamlit/Plotly atlas dashboard with extensive controls for clustering, surprise detection, comparisons, and temporal signal inspection.
- Includes Knowledge Graph tab that renders graph summary/relations, filters by node/relation, and visualizes confidence-weighted edges.

## 2026-03-08 (Batch 3)

### `physics_ai/checkpoint.py`
- Checkpointing layer for experiment runs: writes parquet universe/particle shards, laws JSON, and graph artifacts.
- Maintains run metadata, supports resume, and captures family drift summaries for atlas analytics.

### `physics_ai/knowledge_graph.py`
- In-memory concept graph with evidence tracking, relation confidence, node listing, and summary statistics.
- Provides concise summary strings for dashboard/printing.

### `physics_ai/regime_summarizer.py`
- Generates human-readable labels and signatures for behavioral clusters based on percentile thresholds.
- Emits summaries with dominant law-family tagging when present.

### `physics_ai/symbolic_law_extractor.py`
- Fits sparse symbolic laws per regime (single or coupled fields) using Lasso and operator libraries.
- Produces law signatures, equations, and validation/behavioral scores for atlas analytics.

### `physics_ai/law_validator.py`
- Validates candidate laws by simulating fields/ODEs and comparing metric drift vs. reference regimes.
- Supports single-field and coupled-field evaluation with regime match scoring utilities.

## 2026-03-08 (Batch 4)

### `physics_ai/scoring.py`
- Computes universe interestingness scores, diversity penalties, and novelty bonuses from observation signatures.
- Includes dispersion complexity scoring and signature extraction for multi-field runs.

### `physics_ai/universe_atlas.py`
- Loads universe shards, builds feature matrices, and embeds regimes via UMAP/t-SNE for atlas visualization.
- Provides utilities to save atlas outputs and select sparse seed points.

### `physics_ai/operator_library.py`
- Constructs operator matrices for single-field and coupled-field symbolic law regression.
- Encodes polynomial terms, Laplacians, and nonlinear interactions into regression-ready features.

### `physics_ai/experiment_planner.py`
- Proposes randomized experiment configs (universe + dynamics types, wave params, coupled-field params).
- Central source of default ranges for exploration sweeps.

### `physics_ai/regime_data_sampler.py`
- Samples top-scoring observations per regime for symbolic law extraction.
- Handles absent regime/score columns gracefully.

## 2026-03-08 (Batch 5)

### `physics_ai/seed_perturbations.py`
- Applies localized perturbations (gaussian, dipole, ring, spiral) to break symmetries in initial fields.
- Used to seed emergent dynamics with randomized amplitude/radius settings.

### `physics_ai/phase_detector.py`
- Heuristic phase classifier that labels regimes (e.g., turbulent, soliton, resonant standing wave) with confidence.
- Uses particle, spectral entropy, localization, and drift metrics.

### `physics_ai/particle_detector.py`
- Detects particle-like structures via energy density peaks and tracks them across frames.
- Outputs particle counts, tracks, and derived scores (localization, coherence, persistence).

### `physics_ai/ratio_analyzer.py`
- Extracts dominant frequency ratios from temporal FFTs, clusters them, and matches known constants (e.g., $\phi$, $\pi$).
- Annotates universe rows with dominant ratio features for atlas analysis.

### `physics_ai/regime_evolution.py`
- Detects regime merge/split events across generations using signature overlap similarity.
- Returns event tables for atlas “discovery evolution” analytics.

## 2026-03-08 (Batch 6)

### `physics_ai/behavior_clustering.py`
- Builds normalized feature matrices from behavior metrics and clusters them using HDBSCAN.
- Produces behavior cluster IDs, probabilities, sizes, and outlier flags.

### `physics_ai/regime_clustering.py`
- HDBSCAN-based clustering for atlas coordinates, with helper utilities for cluster sizes.
- Provides annotated dataframe outputs with cluster probabilities.

### `physics_ai/surprise_detector.py`
- Computes atlas distances and local density scores to flag novel regimes.
- Annotates dataframe with surprise flags, density metrics, and cluster outlier indicators.

### `physics_ai/equation_evolution.py`
- Handles equation term mutation for evolutionary search (laplacian/nonlinear/biharmonic toggles).
- Provides helpers to apply term choices to config.

### `physics_ai/evolutionary_runner.py`
- CLI entrypoint for evolutionary universe search with atlas-guided and equation-evolution options.
- Builds `EvolutionConfig` and triggers `run_evolution`.

## 2026-03-08 (Batch 7)

### `physics_ai/evolutionary_search.py`
- Core evolutionary search loop with random/CMA-ES mutation, atlas-guided seeding, and equation-term evolution.
- Handles population evaluation, elite selection, and optional checkpointing per generation.

### `physics_ai/defect_detector.py`
- Detects vortices, nodal loops, and coherence length in fields to quantify topological defects.
- Returns defect densities for downstream scoring and clustering.

### `physics_ai/theory_compression_runner.py`
- CLI for running SINDy-style theory compression on checkpoint shards.
- Writes per-universe compressed equations to a JSON text output.

### `physics_ai/theory_compression_engine.py`
- Implements sparse regression (SINDy) for temporal signals and provides theory compression summaries.
- Exposes `sindy_fit` and `compress_theory` helpers.

### `physics_ai/atlas_runner.py`
- CLI to build and optionally plot atlas embeddings from checkpointed universes.
- Uses `embed_universes` and saves CSV/plot output.

## 2026-03-08 (Batch 8)

### `physics_ai/distributed_runner.py`
- CLI entrypoint for Ray-based distributed universe exploration with batching and checkpointing options.
- Wraps `run_distributed` with standard run arguments.

### `physics_ai/distributed.py`
- Implements Ray-distributed batch execution, optional checkpoint saves per shard.
- Lazily imports Ray and orchestrates parallel `explore_universes` calls.

### `physics_ai/backend.py`
- Backend selector for CPU/NumPy vs optional GPU/CuPy acceleration using `PHYSICS_AI_CUDA`.
- Provides `get_xp`, `as_xp`, and `to_numpy` helpers for device-agnostic code.

### `physics_ai/dispersion_extractor.py`
- Extracts dispersion law fits from dominant modes and temporal signals.
- Classifies laws (wave/diffusion/flat) and returns summary dictionaries.

### `physics_ai/resonant_spectrum.py`
- Computes spectral power, dominant modes, and resonance strength for geometry fields.
- Produces spectrum summaries used in resonance/dispersion analysis.

## 2026-03-08 (Batch 9)

### `physics_ai/visualization.py`
- Matplotlib-based visualization helpers for fields, spectra, temporal signals, dispersion fits, particle tracks, and trajectories.
- `render_summary` saves figures or renders inline for a subset of universes.

### `physics_ai/interaction_detector.py`
- Detects particle interactions (collisions, merges, splits) from tracked positions across frames.
- Produces summarized interaction event counts and details.

### `physics_ai/mode_coupling.py`
- Builds mode triads and estimates coupling strength from temporal energy series.
- Returns coupling summaries used in nonlinear interaction analysis.

### `physics_ai/geometry_universe.py`
- Simulates geometry-driven universes with evolving metrics, geodesic trajectories, and resonance spectra.
- Provides both standard and resonant geometry runs with curvature/trajectory metrics.

### `physics_ai/gauge_discovery.py`
- Tests global and local phase gauge invariance via action proxies on complex fields.
- Returns gauge invariance metrics and summary dicts.

## 2026-03-08 (Batch 10)

### `physics_ai/renormalization.py`
- Multi-scale analysis with coarse-graining, temporal stats, and invariance scoring across scales.
- Produces energy-flow and scale metrics used in atlas/graph summaries.

### `physics_ai/canonical_benchmark.py`
- Pass/fail benchmark suite for canonical rediscovery runs with equation and conservation checks.
- Evaluates outputs from `run_canonical_suite` and exits non-zero on failures.

### `physics_ai/canonical_runner.py`
- Runs canonical rediscovery experiments across standard dynamics types and extracts equations/Noether results.
- Provides a CLI for reporting symbolic laws and conserved quantities.

### `physics_ai/theory_compression.py`
- Ranks candidate theories by error + complexity to select compact explanations.
- Defines `TheoryCandidate`/`TheoryScore` and ranking utilities.

### `physics_ai/noether_inference.py`
- Infers conserved quantities from symmetry cues and temporal drift metrics.
- Supports Lagrangian-based energy drift evaluation via SymPy.

## 2026-03-08 (Batch 11)

### `physics_ai/lagrangian_discovery.py`
- Evaluates candidate Lagrangians against time series using Euler–Lagrange residuals.
- Returns best-fit lagrangian strings with residual metrics.

### `physics_ai/worker.py`
- Distributed worker that explores universes and appends symbolic discovery log entries.
- Aggregates observation features and logs template errors for proposal training.

### `physics_ai/dataset_generator.py`
- Generates synthetic datasets from universe explorations and exports CSV + metadata.
- Includes schema validation and feature hashing for reproducibility.

### `physics_ai/coordinator.py`
- Coordinator CLI that trains the shared proposal network from discovery logs.
- Wraps `train_from_log` with CLI parameters.

### `physics_ai/train_proposal.py`
- Trains/persists neural proposal network weights from discovery logs.
- Loads existing weights if present and saves updated models.

## 2026-03-08 (Batch 12)

### `physics_ai/neural_symbolic.py`
- Neural proposal network helpers (PyTorch) for suggesting equation templates.
- Manages discovery log I/O, dataset building, and training/serialization utilities.

### `physics_ai/symbolic_discovery.py`
- Symbolic inverse-law discovery via candidate templates and least-squares fitting.
- Supports templated search with callbacks for logging errors.

### `physics_ai/geometry_frequency.py`
- Extracts node counts, frequency peaks, harmonic ratios, and symmetry metrics from fields.
- Returns feature dictionaries used in observation summaries.

### `physics_ai/hypothesis_engine.py`
- Generates inverse-law hypotheses and evaluates them against dataset errors.
- Adds symmetry/harmonic hypothesis helpers used in graph building.

### `physics_ai/group_theory.py`
- Computes rotation/reflection symmetry metrics and classifies groups (C/D/SO2).
- Provides continuous symmetry scoring and standard transform library.

## 2026-03-08 (Batch 13)

### `physics_ai/train_model.py`
- Full training pipeline for a small physics foundation model (PyTorch) with dataset generation, metrics logging, and registry entries.
- Supports YAML configs, checkpoints, model cards, and provenance tracking.

### `physics_ai/model_registry.py`
- Versioned model registry for artifacts/configs with checksum provenance.
- Creates run directories and saves metadata/configs/provenance JSON.

### `physics_ai/model_card.py`
- Generates markdown model cards summarizing training metrics and dataset metadata.

### `physics_ai/train_stub.py`
- Lightweight baseline trainer using least squares for quick experimentation.
- Outputs MAE and fitted weights.

### `physics_ai/reality_interface.py`
- Loads external wave datasets and validates inverse-law hypotheses against them.
- Computes mean absolute error on real data.

## 2026-03-08 (Batch 14)

### `physics_ai/evolution_engine.py`
- Simple evolutionary hypothesis search for inverse-law forms using mutation and selection.
- Evaluates candidate equations against observed wavelength/frequency data.

### `physics_ai/pattern_detector.py`
- Minimal k-means clustering implementation for observation feature grouping.
- Returns labels and centroids.

### `physics_ai/axioms.py`
- Defines core axioms and validates basic metrics for axiom compliance.
- Currently checks non-negative energy and finite variance.

### `physics_ai/__init__.py`
- Package entry exporting `run_experiment` for external use.

## 2026-03-08 (Batch 15)

### `physics_ai/discovery_log.jsonl`
- JSONL log of neural-symbolic discovery runs with feature vectors, equation templates, and MSE scores.
- Used to train proposal networks and track template performance over time.
