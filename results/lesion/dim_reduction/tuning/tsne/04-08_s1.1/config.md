# clinical_connectome — lesion › dim_reduction › tsne › tuning › 04-08_s1.1

## Config

```json
{
  "project": "clinical_connectome",
  "input_path": "data/derived/lesion_matrix/21-07_s1.1",
  "reduction_method": "tsne",
  "params_file": "config/registry/params_reduction.json",
  "session_name": "s1.1",
  "base_params": {
    "n_components": 2,
    "perplexity": 30,
    "early_exaggeration": 12,
    "learning_rate": 200,
    "max_iter": 1000,
    "random_state": 0,
    "metric": "euclidean"
  },
  "tuning_grid": {
    "metric": [
      "euclidean",
      "jaccard",
      "dice"
    ],
    "regress_out_volume": [
      false,
      true
    ],
    "perplexity": [
      5,
      15,
      30,
      50,
      75
    ]
  },
  "nested_params": [
    "metric",
    "regress_out_volume"
  ]
}
```

## Summary

Swept parameters: ['metric', 'regress_out_volume', 'perplexity']
Nested parameters (one subfolder per real combination): ['metric', 'regress_out_volume']
Free/grid parameters (embeddings_grid.png per leaf): ['perplexity']
Combinations evaluated: 20
Metric: trustworthiness

Warning: no automatic selection - inspect tuning_results.csv/tuning_plot.png (or the per-leaf embeddings_grid_*.png) and pick parameters by hand.
