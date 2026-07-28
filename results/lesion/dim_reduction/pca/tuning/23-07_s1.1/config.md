# clinical_connectome — lesion › dim_reduction › pca › tuning › 23-07_s1.1_pca_tune

## Config

```json
{
  "project": "clinical_connectome",
  "input_path": "data/derived/lesion_matrix/21-07_s1.1",
  "reduction_method": "pca",
  "params_file": "config/registry/params_reduction.json",
  "session_name": "s1.1_pca_tune"
}
```

## Summary

Swept parameters: ['n_components']
Combinations evaluated: 20
Metric: cumulative_explained_variance

No automatic selection - inspect tuning_results.csv/tuning_plot.png and pick parameters by hand.
