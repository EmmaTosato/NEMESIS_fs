# clinical_connectome — lesion › dim_reduction › umap › tuning › 29-07_s1.1

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
    "n_neighbors": [
      5,
      15,
      30,
      50,
      100
    ],
    "metric": [
      "euclidean",
      "jaccard",
      "dice"
    ],
    "regress_out_volume": [
      false,
      true
    ]
  }
}
```

## Summary

Swept parameters: ['n_neighbors', 'metric', 'regress_out_volume']
Combinations evaluated: 20
Metric: trustworthiness

Warning: no automatic selection - inspect tuning_results.csv/tuning_plot.png and pick parameters by hand.
