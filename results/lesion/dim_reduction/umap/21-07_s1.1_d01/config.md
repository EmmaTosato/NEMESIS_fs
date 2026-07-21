# clinical_connectome dim_reduction (umap) — 21-07-26 14:45

## Config

```json
{
  "project": "clinical_connectome",
  "input_path": "data/derived/lesion_matrix/21-07_s1",
  "reduction_method": "umap",
  "params_file": "config/registry/params_reduction.json",
  "output_root": "results/dim_reduction",
  "session_name": "umap_s1",
  "overwrite": true,
  "fine_tuning": false,
  "run_notes": "UMAP production run with fine-tuned params (n_neighbors=15, min_dist=0.1)"
}
```

## Summary

Input matrix shape: 1150 subjects x 254865 features
Embedding shape: 1150 subjects x 2 components
Params used: {"n_neighbors": 15, "min_dist": 0.1, "n_components": 2, "random_state": 0}
