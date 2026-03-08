# Registry Charts

The Model Registry tab includes summary charts to help compare training runs quickly.

## Charts

- **Models by type**: counts of `model_type` across registry runs.
- **Models by device**: counts of `device` (cpu/cuda) used during training.
- **Records histogram**: distribution of training record counts.

These charts update automatically based on the filtered registry table.

## Tips

- Use tags to segment runs (e.g., `baseline`, `gpu`, `ablation`).
- Export CSV summaries for offline plotting.
- Archive old runs to keep the registry focused on recent experiments.
