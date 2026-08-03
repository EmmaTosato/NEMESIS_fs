# clinical_connectome — lesion › dim_reduction › umap › tuning › 03-08_preview

## Config

```json
{
  "project": "clinical_connectome",
  "input_path": "data/derived/lesion_matrix/21-07_s1.1",
  "reduction_method": "umap",
  "params_file": "/private/tmp/claude-501/-Users-emmatosato-Local-Projects-Local-PhD-Projects-NEMESIS-fs/798b1f1d-220f-4780-9696-f90f9b3b340c/scratchpad/params_reduction_preview.json",
  "session_name": "preview",
  "base_params": {
    "n_neighbors": 15,
    "min_dist": 0.0,
    "n_components": 2,
    "random_state": 0,
    "metric": "jaccard"
  },
  "tuning_grid": {
    "metric": [
      "euclidean"
    ],
    "n_components": [
      2
    ],
    "regress_out_volume": [
      false
    ],
    "n_neighbors": [
      15,
      30
    ],
    "min_dist": [
      0.0,
      0.1
    ]
  },
  "nested_params": [
    "metric",
    "n_components",
    "regress_out_volume"
  ]
}
```

## Summary

Swept parameters: ['metric', 'n_components', 'regress_out_volume', 'n_neighbors', 'min_dist']
Nested parameters (one subfolder per real combination): ['metric', 'n_components', 'regress_out_volume']
Free/grid parameters (embeddings_grid.png per leaf): ['n_neighbors', 'min_dist']
Combinations evaluated: 4
Metric: trustworthiness

Warning: no automatic selection - inspect tuning_results.csv/tuning_plot.png (or the per-leaf embeddings_grid_*.png) and pick parameters by hand.
