# Research lab setup

This guide gets a new researcher from clone to first run quickly.

## 1) Clone the repo

```bash
git clone <REPO_URL>
cd physics-ai
```

## 2) Bootstrap the environment

Run the bootstrap script to create a virtual environment, install dependencies, and run a quick sanity test:

```bash
bash scripts/bootstrap_lab.sh
```

Alternatively, use the Makefile:

```bash
make setup
```

GPU run shortcut:

```bash
make gpu
```

Cleanup helper:

```bash
make clean
```

## 3) Activate the environment

```bash
source .venv/bin/activate
```

## 4) Run a discovery experiment

```bash
python -m physics_ai.main_loop
```

You can also use preset configs:

```bash
python -m physics_ai.main_loop --config configs/run_quick.yaml
```

Other presets:

- `configs/run_deep.yaml`
- `configs/run_gpu.yaml`
- `configs/run_multifield.yaml`
- `configs/run_reaction.yaml`

## 4b) Run the lab pipeline (recommended)

The lab pipeline runs a small batched experiment and builds an atlas snapshot:

```bash
bash scripts/run_lab_pipeline.sh
```

Or use:

```bash
make atlas
```

## 5) Launch the dashboard

```bash
streamlit run physics_ai/live_dashboard.py -- --run-dir experiments
```

## Run registry

When you run with `--checkpoint-dir`, the lab appends a summary entry to `runs.jsonl` in that directory. This is useful for tracking experiment outcomes across the team.

## Optional: GPU acceleration

Install CuPy for your CUDA version and enable the backend:

```bash
PHYSICS_AI_CUDA=1 python -m physics_ai.main_loop --dynamics-type wave
```

## Troubleshooting

- If you see missing dependencies, re-run `pip install -r requirements.txt`.
- If CuPy is missing, the engine will fall back to CPU automatically.
