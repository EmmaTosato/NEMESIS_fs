# clinical_connectome_23-07-26
## 17:55

## Config

```json
{
  "project": "clinical_connectome",
  "input_path": "data/derived/lesion_matrix/21-07_s1.1",
  "reduction_method": "umap",
  "params_file": "config/registry/params_reduction.json",
  "output_root": "results/lesion/dim_reduction",
  "session_name": "s1.1",
  "overwrite": true,
  "fine_tuning": false,
  "run_notes": "UMAP production run on voxel-wise lesion matrix (21-07_s1.1), best params from existing tuning sweep (n_neighbors=5, min_dist=0.0, trustworthiness=0.740)"
}
```

## Summary

Input matrix shape: 1150 subjects x 254865 features
Embedding shape: 1150 subjects x 2 components
Params used: {"n_neighbors": 5, "min_dist": 0.0, "n_components": 2, "random_state": 0}