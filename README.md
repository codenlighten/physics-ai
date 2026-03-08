# Physics-AI

**Physics-AI** is an experimental platform for automated discovery of physical laws from simulated universes.

Instead of training on static datasets, Physics-AI generates synthetic physical worlds, observes their behavior, detects emergent structures, and infers governing equations using symbolic regression and validation loops. The system is designed as a **physics-first machine scientist** for exploring nonlinear dynamical systems and uncovering candidate laws.

## Core idea

Physics-AI implements a closed scientific discovery loop:

```
Generate universes
	-> Simulate fields and dynamics
	-> Observe structures and metrics
	-> Detect patterns (particles, waves, defects)
	-> Infer candidate equations
	-> Re-simulate inferred laws
	-> Validate physical behavior
	-> Store discoveries in a knowledge graph
	-> Explore discoveries in a live dashboard
```

## Key features

### Universe generation

Physics-AI can generate many classes of universes:

- random fields
- spectral eigenmode universes
- harmonic universes
- golden-ratio resonance universes
- geometry-driven universes

Supported dynamics include:

- static
- wave equation
- diffusion
- reaction-diffusion
- Schrodinger equation
- spectral Lagrangian systems
- geometry curvature dynamics

### Multi-field simulations

The engine supports coupled fields ($\psi$, $\phi$) with cross-terms such as:

```
psi*phi
psi^2*phi
phi^2*psi
```

This enables discovery of interaction-driven regimes.

### Emergent structure detection

Observers analyze simulation frames and extract:

- vortex count
- nodal loops
- defect density
- coherence length
- spectral entropy
- resonance peaks
- translation/scale/phase invariance

The engine can detect particle-like structures, solitons, interference patterns, nonlinear interactions, and particle collisions.

### Symbolic law discovery

The system attempts to infer governing equations from observed signals. Example output:

```
dpsi/dt = -0.98 psi + 0.51 psi^3
```

The symbolic discovery engine:

- builds an operator library
- fits sparse regression models
- evaluates candidate equations
- performs behavioral validation

Spatial operators include:

```
psi
psi^3
psi^5
laplacian(psi)
biharmonic(psi)
abs(psi)^2 * psi
psi*phi
psi^2*phi
```

### Behavioral validation

Discovered equations are validated by re-simulating the system and comparing:

- defect density
- spectral entropy
- vortex count
- cross-field correlation
- temporal structure

This produces:

```
law_fit_score
law_validation_score
law_regime_match_score
law_coupled_match_score
```

### Knowledge graph of discoveries

All discoveries are stored in a lightweight concept graph. Relations include:

```
field --emergent_particle--> particle
particle --interaction--> particle
dynamics --lagrangian--> equation
symmetry --conserves--> quantity
resonance --dispersion_law--> relation
theory --compressed--> equation
```

Graph exports include:

```
graph_summary.json
graph_relations.json
```

### Universe atlas

Physics-AI builds a map of discovered regimes with:

- UMAP / t-SNE embedding
- regime clustering
- novelty detection
- density-based surprise detection
- behavioral clustering

This atlas acts as a map of nonlinear physics regimes.

### Live dashboard

A Streamlit dashboard allows interactive exploration. Panels include:

- Universe Atlas
- Regime Explorer
- Regime Compare
- Law Discovery
- Resonance Ratios
- Atlas Statistics
- Knowledge Graph Explorer
- Model Registry

Example launch:

```bash
streamlit run physics_ai/live_dashboard.py -- --run-dir experiments
```

### Dashboard screenshots

Add images under `docs/screenshots/` and reference them here. Suggested names:

- `docs/screenshots/atlas.png`
- `docs/screenshots/regime_explorer.png`
- `docs/screenshots/knowledge_graph.png`

## Project architecture

```mermaid
flowchart TD
	A[Experiment Planner] --> B[Universe Engine]
	B --> C[Physics Simulation]
	C --> D[Observer]
	D --> E[Pattern Detection]
	E --> F[Symbolic Law Discovery]
	F --> G[Behavioral Validation]
	G --> H[Knowledge Graph]
	H --> I[Atlas Intelligence]
	I --> J[Live Dashboard]
```

The source diagram lives in `docs/architecture.mmd`.

```
physics_ai/
|
|-- universe_engine.py        universe generation
|-- field_dynamics.py         PDE dynamics
|-- simulation.py             grid simulation
|
|-- observer.py               structure metrics
|-- defect_detector.py        topology detection
|-- particle_detector.py      emergent particles
|-- interaction_detector.py   particle interactions
|
|-- symbolic_law_extractor.py symbolic regression
|-- operator_library.py       operator generation
|-- law_validator.py          behavioral validation
|
|-- regime_clustering.py      structural clustering
|-- behavior_clustering.py    behavioral clustering
|-- regime_summarizer.py      regime labeling
|
|-- universe_atlas.py         regime embedding
|-- live_dashboard.py         Streamlit dashboard
|
|-- knowledge_graph.py        discovery graph
|-- checkpoint.py             experiment persistence
|
|-- evolutionary_runner.py    evolutionary search
|-- distributed_runner.py     distributed simulation
```

## Quick start

Create environment:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Research lab onboarding

For a fast clone-and-run flow, use the lab setup guide and bootstrap script:

- `docs/lab_setup.md`
- `scripts/bootstrap_lab.sh`
- `scripts/run_lab_pipeline.sh`
- `Makefile` (optional: `make setup`, `make run`, `make atlas`, `make gpu`, `make clean`)

Run a discovery experiment:

```bash
python -m physics_ai.main_loop
```

Run with a preset config:

```bash
python -m physics_ai.main_loop --config configs/run_quick.yaml
```

Additional presets:

- `configs/run_deep.yaml`
- `configs/run_gpu.yaml`
- `configs/run_multifield.yaml`
- `configs/run_reaction.yaml`

Run a wave universe:

```bash
python -m physics_ai.main_loop --dynamics-type wave
```

Launch the dashboard:

```bash
streamlit run physics_ai/live_dashboard.py -- --run-dir experiments
```

Run tests:

```bash
pytest -q
```

## Benchmarking

Measure batched dynamics throughput with:

```bash
python -m physics_ai.benchmark_runner --mode wave --batch 64 --size 64 --steps 80
```

Run on GPU by enabling the CUDA backend:

```bash
PHYSICS_AI_CUDA=1 python -m physics_ai.benchmark_runner --mode wave --batch 64 --size 64 --steps 80
```

Write results to CSV for later plotting:

```bash
python -m physics_ai.benchmark_runner --mode wave --batch 64 --size 64 --steps 80 --output benchmarks/results.csv
```

## Run registry

When you run with `--checkpoint-dir`, the lab writes a `runs.jsonl` file in that directory with the run config and summary metadata for later analysis.

## PLL-M dataset + training

Build a PLL-M dataset from checkpointed runs and an atlas export:

```bash
python -m physics_ai.pll_m_dataset --run-dir experiments/run_*/ --atlas atlas.csv --output datasets/pll_m.jsonl
```

Train the minimal operator predictor:

```bash
python -m physics_ai.train_pll_m --dataset datasets/pll_m.jsonl --model-path models/pll_m.pt --vocab-path models/pll_m_vocab.json
```

Trainer options (transformer by default):

```bash
python -m physics_ai.train_pll_m \
	--dataset datasets/pll_m.jsonl \
	--model-type transformer \
	--model-dim 64 \
	--num-heads 4 \
	--num-layers 2 \
	--dropout 0.1
```

### Model registry

Each PLL-M training run writes a model card, config, and provenance file in `models/run-*`.

List registry entries:

```bash
python -m physics_ai.model_registry_cli list
```

Show a registry entry:

```bash
python -m physics_ai.model_registry_cli show run-YYYYMMDDThhmmssZ
```

Export registry summary:

```bash
python -m physics_ai.model_registry_cli export --output registry_export.json
```

You can export CSV summaries as well:

```bash
python -m physics_ai.model_registry_cli export --format csv --output registry_export.csv
```

Archive a registry run:

```bash
python -m physics_ai.model_registry_cli archive run-YYYYMMDDThhmmssZ
```

Restore an archived registry run:

```bash
python -m physics_ai.model_registry_cli restore run-YYYYMMDDThhmmssZ
```

Tag a registry run:

```bash
python -m physics_ai.model_registry_cli tag run-YYYYMMDDThhmmssZ --tags baseline,gpu
```

See `docs/registry_summary.md` for a registry layout overview.
See `docs/registry_charts.md` for registry chart descriptions.

## GPU acceleration

Install CuPy for your CUDA version and enable GPU execution with:

```bash
PHYSICS_AI_CUDA=1 python -m physics_ai.main_loop --dynamics-type wave
```

If CUDA is requested but CuPy is not installed, the engine falls back to CPU execution.

## Evolutionary universe search

The engine can evolve universes across generations:

```bash
python -m physics_ai.evolutionary_runner \
	--generations 3 \
	--population-size 20 \
	--elite-count 5 \
	--dynamics-type wave
```

This mutates high-scoring universes to explore promising regions of the physics space.

## Distributed discovery

Experiments can be parallelized:

```bash
python -m physics_ai.distributed_runner \
	--universe-count 256 \
	--batch-size 64
```

Ray can be used for cluster execution.

## Canonical physics rediscovery

Physics-AI includes benchmarks for rediscovering known systems:

```bash
python -m physics_ai.canonical_runner
```

Target systems include:

- harmonic oscillator
- diffusion equation
- wave equation
- Schrodinger equation

## Research goals

Physics-AI explores whether automated systems can:

- rediscover known physical laws
- discover new nonlinear regimes
- classify universality classes
- infer Lagrangians
- detect conserved quantities
- map the space of dynamical systems

## Status

This repository is a research prototype exploring automated physics discovery. The architecture is modular and designed to support large-scale universe exploration, symbolic discovery loops, and human-in-the-loop inspection.

## License

TBD

## Future directions

Potential extensions include:

- GPU simulation
- multi-scale renormalization
- symmetry discovery
- automated theorem extraction
- large-scale atlas construction

## Citation

If you use this repository for research, please cite:

```
Physics-AI: Automated Discovery of Physical Laws from Simulated Universes
```

## Author

Greg
Founder of CodeNLighten
