# Physics-First AI Prototype

This repo contains a minimal, runnable prototype of a physics-first discovery loop that mirrors the architecture described in `Physics-First AI Architecture.md`.

## What it does

- Simulates 2D wave fields across multiple universes.
- Observes energy, frequency, and geometry metrics.
- Clusters observations to detect patterns.
- Discovers inverse frequency laws and evolves candidate equations.
- Stores relations in a small concept graph with evidence.

## Project layout

- `physics_ai/`: core modules (simulation, observation, evolution, experiments, reality validation).
- `physics_ai/dataset_generator.py`: synthetic dataset export.
- `physics_ai/train_stub.py`: baseline training stub for a foundation model.
- `physics_ai/train_model.py`: PyTorch training loop for a foundation model.
- `physics_ai/symbolic_discovery.py`: symbolic equation discovery helpers.
- `physics_ai/neural_symbolic.py`: neural-guided template proposal scaffolding.
- `tests/`: minimal smoke tests.
- `requirements.txt`: runtime + test dependencies.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m physics_ai.main_loop
```

## Generate a synthetic dataset

```bash
python -c "from physics_ai.dataset_generator import DatasetConfig, generate_dataset, export_csv, build_metadata, export_metadata; records = generate_dataset(DatasetConfig(universe_count=50, seed=1, universe_type='spectral')); export_csv(records, 'synthetic_dataset.csv'); export_metadata(build_metadata(records, DatasetConfig(universe_count=50, seed=1, universe_type='spectral')), 'synthetic_dataset.meta')"
```

## Run the training stub

```bash
python -m physics_ai.train_stub
```

## Train the foundation model (PyTorch)

```bash
pip install -r requirements-train.txt
python -m physics_ai.train_model
```

### Training options

The training script supports optional checkpointing and model export via `TrainConfig` in `physics_ai/train_model.py`.

#### Example with checkpoints + metrics

```bash
python -m physics_ai.train_model \
	--epochs 100 \
	--checkpoint-path models/best.pt \
	--model-path models/foundation.pt \
	--metrics-path models/metrics.csv
```

#### Example with YAML config

```bash
python -m physics_ai.train_model --config configs/train.yaml
```

### Model registry

Each training run writes metadata and model cards under `models/run-<timestamp>/`.

The registry captures:

* training config (`configs/train_config.json`)
* run metadata (`metadata.json`)
* model card (`artifacts/*.md`)
* provenance checksums (`provenance.json`)

## Run tests

```bash
pytest -q
```

## Neural-guided symbolic loop

Each experiment run logs symbolic template evaluations to `physics_ai/discovery_log.jsonl`. The log is used to train a lightweight proposal network (when PyTorch is installed) that suggests promising templates for the next run.

To enable neural-guided proposals:

1. Install training dependencies with `requirements-train.txt`.
2. Run the experiment loop multiple times to populate the discovery log.
3. The next run will automatically train a proposal network and pass the suggested templates into symbolic discovery.

### Persisting the proposal model

The proposal network is saved to `physics_ai/proposal_net.pt` after training, and it is reloaded automatically on subsequent runs. You can also train it directly from the log:

```bash
python -m physics_ai.train_proposal --log-path physics_ai/discovery_log.jsonl --model-path physics_ai/proposal_net.pt
```

### Distributed discovery (minimal scaffolding)

Use lightweight workers to append discoveries and a coordinator to train the shared proposal network:

```bash
# run workers
python -m physics_ai.worker --universe-count 50 --seed 1 --universe-type spectral
python -m physics_ai.worker --universe-count 50 --seed 2 --universe-type harmonic

# update the shared proposal model
python -m physics_ai.coordinator --log-path physics_ai/discovery_log.jsonl --model-path physics_ai/proposal_net.pt
```

## Spectral universe generation

The engine can now generate universes with controlled eigenmode spectra. Available universe types are:

- `random` (baseline)
- `spectral` (sum of random eigenmodes)
- `harmonic` (harmonic ladders)
- `phi` (golden-ratio interference patterns)

You can pass `universe_type` into `run_experiment` or `DatasetConfig` to bias discovery toward structured spectra.

## Field dynamics (time-evolving universes)

Universes can evolve in time using simple dynamics models:

- `static` (default)
- `wave` (discrete wave equation)
- `diffusion` (heat equation)
- `reaction_diffusion` (Turing patterns)

These dynamics add temporal observations (FFT + energy drift):

```bash
python -m physics_ai.main_loop --universe-type spectral --dynamics-type wave
```

You can also use the same option in `DatasetConfig` and `worker.py`.

## Lagrangian discovery

For time-evolving universes, the engine now scores candidate Lagrangians against the observed temporal signal and stores the best result in the knowledge graph.

```bash
python -m physics_ai.main_loop --dynamics-type wave
```

The resulting relation appears under `dynamics --lagrangian-->` in the graph summary.

## Noether / conserved-quantity inference

When temporal observations and symmetry information are available, the engine infers conserved quantities (energy, angular momentum proxies) and stores them in the knowledge graph.

```bash
python -m physics_ai.main_loop --dynamics-type wave
```

Look for `symmetry --conserves-->` relations in the graph summary.

## Theory compression

The engine ranks discovered laws by error plus a complexity penalty and stores the top-ranked equation as a compressed theory.

```bash
python -m physics_ai.main_loop --dynamics-type wave
```

Look for `theory --compressed-->` relations in the graph summary.

## Canonical dynamics targets

The dynamics layer now supports canonical systems for rediscovery runs:

- `oscillator` (harmonic oscillator)
- `diffusion`
- `wave`
- `schrodinger` (complex wave)

Example:

```bash
python -m physics_ai.main_loop --dynamics-type oscillator
python -m physics_ai.main_loop --dynamics-type schrodinger
```

## Canonical discovery runner

Run the four target systems in a single sweep and print the discovered equation, Lagrangian, and conserved quantities:

```bash
python -m physics_ai.canonical_runner
```

## Spectral Lagrangian engine

Run eigenmode-space universes where amplitudes evolve under a spectral Lagrangian:

```bash
python -m physics_ai.main_loop --dynamics-type spectral_lagrangian
```

## Renormalization engine

When temporal frames are available, the engine coarse-grains them across scales and reports a scale invariance score.

```bash
python -m physics_ai.main_loop --dynamics-type wave
```

## Gauge symmetry discovery

For complex-valued dynamics (e.g., Schrödinger universes), the engine checks phase invariance and records gauge symmetry evidence.

```bash
python -m physics_ai.main_loop --dynamics-type schrodinger
```

## Geometry-driven universes

Run geometry-curvature dynamics where trajectories follow a metric field:

```bash
python -m physics_ai.main_loop --dynamics-type geometry
```

## Resonant geometry universes

Generate metric curvature from standing-wave resonance patterns:

```bash
python -m physics_ai.main_loop --dynamics-type resonant_geometry
```

The resonance spectra are stored as a `geometry --resonance-->` relation in the knowledge graph.

Spectrum extraction utilities live in `physics_ai/resonant_spectrum.py` and expose dominant modes plus resonance strength.

## Dispersion law extraction

When resonance spectra and temporal signals are available, the engine fits a dispersion relation and records it as `resonance --dispersion_law-->`.

## Mode coupling analysis

For resonant universes with temporal signals, the engine detects nonlinear triad interactions and records them as `resonance --nonlinear_interaction-->`.

## Particle-like structure detection

The engine identifies localized, persistent peaks in temporal frames and records them as `field --emergent_particle-->` relations.

## Particle interaction detection

When particle tracks are available, the engine detects proximity-based collisions plus simple merge/split events and stores them as `particle --interaction-->` relations in the knowledge graph.

## Visualization

Generate quick-look plots for fields, spectra, dispersion fits, particle tracks, and geometry trajectories:

```bash
python -m physics_ai.main_loop --dynamics-type wave --visualize --output-dir outputs
```

Use `--no-show` to skip opening windows (useful on headless machines) and `--max-universes` to control how many universes are plotted.

## Optional CUDA backend

The engine can use a NumPy-compatible GPU backend for FFT-heavy steps. Install CuPy for your CUDA version and enable it with the CLI flag or environment variable:

```bash
python -m physics_ai.main_loop --cuda --dynamics-type wave
```

Or set `PHYSICS_AI_CUDA=1` in the environment.

If CUDA is requested but CuPy is not installed, the engine will emit a warning and fall back to CPU execution.

## Canonical pass/fail benchmark

Run the canonical suite with explicit pass/fail checks suitable for CI regression gates:

```bash
python -m physics_ai.canonical_benchmark
```

## Notes

This prototype is intentionally lightweight. The hypothesis relation uses the simulation’s known wave speed to make the discovery loop deterministic and easy to validate. You can later replace this with a frequency estimator that is derived purely from observed state (e.g., FFT peak extraction) once you’re ready for a higher-fidelity model.
