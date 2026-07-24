# clinical_connectome_23-07-26
## 18:31

## Config

```json
{
  "project": "clinical_connectome",
  "input_path": "data/derived/lesion_matrix/21-07_s1.1",
  "reduction_method": "tsne",
  "params_file": "config/registry/params_reduction.json",
  "output_root": "results/lesion/dim_reduction",
  "session_name": "s1.1",
  "overwrite": true,
  "fine_tuning": false,
  "run_notes": "t-SNE production run on voxel-wise lesion matrix (21-07_s1.1), params per Thiebaut de Schotten 2020 (perplexity swept manually: 30/40/60/80, early_exaggeration=12, learning_rate=200)"
}
```

## Summary

Input matrix shape: 1150 subjects x 254865 features
Embedding shape: 1150 subjects x 2 components
Params used: {"n_components": 2, "perplexity": 40, "early_exaggeration": 12, "learning_rate": 200, "max_iter": 1000, "random_state": 0}