# clinical_connectome_21-07-26
## 14:06

## Config

```json
{
  "project": "clinical_connectome",
  "input_path": "data/derived/lesion_matrix/21-07_run1",
  "reduction_method": "tsne",
  "params_file": "config/registry/params_reduction.json",
  "output_root": "results/dim_reduction",
  "run_name": "tsne_run1",
  "overwrite": false,
  "fine_tuning": false,
  "run_notes": "t-SNE on the voxel-wise (254865-feature) matrix, not the parcellated one; params fixed from Thiebaut de Schotten et al. 2020, not fine-tuned"
}
```

## Summary

Input matrix shape: 1150 subjects x 254865 features
Embedding shape: 1150 subjects x 2 components
Params used: {"perplexity": 30, "early_exaggeration": 12, "learning_rate": 200, "max_iter": 1000, "init": "random", "random_state": 0}