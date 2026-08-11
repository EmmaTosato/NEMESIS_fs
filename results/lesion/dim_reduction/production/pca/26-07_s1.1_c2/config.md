# clinical_connectome dim_reduction (pca) — 26-07-26 16:25

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
  "run_notes": "PCA n_components=2, run for consistency with the other 3 reductions (umap/pacmap/tsne already have a standalone embedding saved here) - see TUNING_ANALYSIS.md pca-2D control test for why this isn't the production PCA config (150 components stays the default)"
}
```

## Summary

Input matrix shape: 1150 subjects x 254865 features
Embedding shape: 1150 subjects x 2 components
Params used: {"n_components": 2, "random_state": 0}
