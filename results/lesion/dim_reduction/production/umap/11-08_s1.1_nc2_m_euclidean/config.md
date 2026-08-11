# clinical_connectome dim_reduction (umap) — 11-08-26 20:56

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
  "run_notes": "first production of dimensionality reduction after specialized tuning - metric=euclidean, n_components=2 (re-run 11-08, same params as the 23-07 run, so every production leaf shares the same session date)"
}
```

## Summary

Input matrix shape: 1150 subjects x 254865 features
Embedding shape: 1150 subjects x 2 components
Params used: {"n_neighbors": 5, "min_dist": 0.0, "n_components": 2, "random_state": 0, "metric": "euclidean"}
