# clinical_connectome_24-07-26
## 09:53 (tsne+dbscan)

## Config

```json
{
  "project": "clinical_connectome",
  "input_path": "data/derived/lesion_matrix/21-07_s1.1",
  "reduction_method": "tsne",
  "reduction_params_file": "config/registry/params_reduction.json",
  "clustering_method": "dbscan",
  "clustering_methods_requested": [
    "kmeans",
    "agglomerative",
    "gmm",
    "dbscan",
    "spectral"
  ],
  "clustering_params_file": "config/registry/params_clustering.json",
  "output_root": "results/lesion/dim_reduction_clustering",
  "session_name": "s1.1",
  "overwrite": true,
  "run_notes": "tsne (perplexity=30, paper value) + all 5 clustering methods, voxel-wise matrix"
}
```

## Summary

Input matrix shape: 1150 subjects x 254865 features
Embedding shape: 1150 subjects x 2 components
Clusters found: 2 (+ 1137 noise points, label -1)
Reduction params used: {"n_components": 2, "perplexity": 30, "early_exaggeration": 12, "learning_rate": 200, "max_iter": 1000, "random_state": 0}
Clustering params used: {"eps": 0.5, "min_samples": 5}