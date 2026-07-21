# clinical_connectome — umap fine-tuning (21-07-26 14:23)

## Config

```json
{
  "project": "clinical_connectome",
  "input_path": "data/derived/lesion_matrix/21-07_s1",
  "reduction_method": "umap",
  "params_file": "config/registry/params_reduction.json",
  "session_name": "umap_tuning_s1"
}
```

## Summary

Swept parameters: ['n_neighbors', 'min_dist']
Combinations evaluated: 16
Metric: trustworthiness

No automatic selection - inspect tuning_results.csv/tuning_plot.png and pick parameters by hand.
