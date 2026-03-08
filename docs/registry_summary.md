# Model Registry Summary

The model registry stores training artifacts for PLL-M runs under `models/run-*`.
Each run contains:

- `metadata.json` — training metrics and dataset summary.
- `configs/train_config.json` — training hyperparameters.
- `artifacts/` — model cards, saved weights, vocab, and metrics.
- `provenance.json` — checksums for artifacts.

## Typical workflow

1. Train a PLL-M model:
   - `python -m physics_ai.train_pll_m --dataset datasets/pll_m.jsonl --model-path models/pll_m.pt`
2. Inspect runs in the dashboard (Model Registry tab).
3. Export a summary with:
   - `python -m physics_ai.model_registry_cli export --format csv --output registry_export.csv`
4. Archive old runs with:
   - `python -m physics_ai.model_registry_cli archive run-YYYYMMDDThhmmssZ`
5. Restore archived runs with:
   - `python -m physics_ai.model_registry_cli restore run-YYYYMMDDThhmmssZ`
6. Tag runs for filtering in the dashboard:
   - `python -m physics_ai.model_registry_cli tag run-YYYYMMDDThhmmssZ --tags baseline,gpu`

## Fields to monitor

- `records`: number of training examples.
- `operator_vocab`: size of the operator vocabulary.
- `model_type`, `model_dim`: architecture.
- `device`: CPU or GPU used in training.

Use this summary to compare model runs and keep track of experiment history.