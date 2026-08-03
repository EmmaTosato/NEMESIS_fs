# clinical_connectome — lesion › dim_reduction › umap › tuning › 03-08_s1.1

## Config

```json
{
  "project": "clinical_connectome",
  "input_path": "data/derived/lesion_matrix/21-07_s1.1",
  "reduction_method": "umap",
  "params_file": "config/registry/params_reduction.json",
  "session_name": "s1.1",
  "base_params": {
    "n_neighbors": 15,
    "min_dist": 0.0,
    "n_components": 2,
    "random_state": 0,
    "metric": "jaccard"
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
    "n_neighbors": [
      5,
      15,
      30,
      50,
      100
    ],
    "min_dist": [
      0.0,
      0.1,
      0.25
    ]
  },
  "nested_params": [
    "metric",
    "regress_out_volume"
  ]
}
```

## Summary

Swept parameters: ['metric', 'regress_out_volume', 'n_neighbors', 'min_dist']
Nested parameters (one subfolder per real combination): ['metric', 'regress_out_volume']
Free/grid parameters (embeddings_grid.png per leaf): ['n_neighbors', 'min_dist']
Combinations evaluated: 60
Metric: trustworthiness

Warning: no automatic selection - inspect tuning_results.csv/tuning_plot.png (or the per-leaf embeddings_grid_*.png) and pick parameters by hand.
