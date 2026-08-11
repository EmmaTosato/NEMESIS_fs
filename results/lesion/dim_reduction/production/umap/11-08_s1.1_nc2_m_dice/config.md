# clinical_connectome dim_reduction (umap) — 11-08-26 19:14

## Config

```json
{
  "project": "clinical_connectome",
  "input_path": "data/derived/lesion_matrix/21-07_s1.1",
  "reduction_method": "umap",
  "params_file": "config/registry/params_reduction.json",
  "output_root": "results/lesion/dim_reduction",
  "session_name": "s1.1_nc2",
  "overwrite": true,
  "fine_tuning": false,
  "regress_out_volume": false,
  "color_by": [
    "dataset",
    "side",
    "volume",
    "nihss"
  ],
  "viz_n_components": 2,
  "run_notes": "first production of dimensionality reduction after specialized tuning - metric=dice, n_components=2"
}
```

## Summary

Input matrix shape: 1150 subjects x 254865 features
Embedding shape: 1150 subjects x 2 components
Params used: {"n_neighbors": 15, "min_dist": 0.0, "n_components": 2, "random_state": 0, "metric": "dice"}
