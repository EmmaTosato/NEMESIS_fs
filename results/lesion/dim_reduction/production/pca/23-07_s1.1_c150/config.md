# clinical_connectome dim_reduction (pca) — 23-07-26 18:20

## Config

```json
{
  "project": "clinical_connectome",
  "input_path": "data/derived/lesion_matrix/21-07_s1.1",
  "reduction_method": "pca",
  "params_file": "config/registry/params_reduction.json",
  "output_root": "results/lesion/dim_reduction",
  "session_name": "s1.1",
  "overwrite": true,
  "fine_tuning": false,
  "run_notes": "PCA production run on voxel-wise lesion matrix (21-07_s1.1), n_components=150 (76% cumulative explained variance, max tested in the tuning sweep - 90% not reached on voxel-wise data)"
}
```

## Summary

Input matrix shape: 1150 subjects x 254865 features
Embedding shape: 1150 subjects x 150 components
Params used: {"n_components": 150, "random_state": 0}
