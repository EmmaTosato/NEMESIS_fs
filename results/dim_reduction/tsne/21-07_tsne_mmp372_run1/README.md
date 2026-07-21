# clinical_connectome dim_reduction (tsne) — 21-07-26 14:20

## Config

```json
{
  "project": "clinical_connectome",
  "input_path": "data/derived/lesion_matrix/21-07_mmp372_run1",
  "reduction_method": "tsne",
  "params_file": "config/registry/params_reduction.json",
  "output_root": "results/dim_reduction",
  "run_name": "tsne_mmp372_run1",
  "overwrite": true,
  "fine_tuning": false,
  "run_notes": "t-SNE on the parcellated (372-feature) matrix"
}
```

## Summary

Input matrix shape: 1150 subjects x 372 features
Embedding shape: 1150 subjects x 2 components
Params used: {"perplexity": 30, "early_exaggeration": 12, "learning_rate": 200, "max_iter": 1000, "init": "random", "random_state": 0}
