# clinical_connectome_26-07-26
## 16:42 (umap+agglomerative)

## Config

```json
{
  "project": "clinical_connectome",
  "input_path": "data/derived/lesion_matrix/21-07_s1.1",
  "reduction_method": "umap",
  "reduction_params_file": "config/registry/params_reduction.json",
  "clustering_method": "agglomerative",
  "clustering_methods_requested": [
    "kmeans",
    "agglomerative",
    "gmm",
    "spectral"
  ],
  "clustering_params_file": "config/registry/params_clustering.json",
  "output_root": "results/lesion/dim_reduction_clustering",
  "session_name": "s1.1",
  "overwrite": true,
  "fine_tuning": false,
  "run_notes": "production run with tuned values from TUNING_ANALYSIS.md/RUNNING_STRATEGIES.md (session s1.1): kmeans k=4 (default confirmed), agglomerative k=5, gmm n=4 (default confirmed), spectral n=8. dbscan excluded - open question, see RUNNING_STRATEGIES.md"
}
```

## Summary

Input matrix shape: 1150 subjects x 254865 features
Embedding shape: 1150 subjects x 2 components
Clusters found: 5
Reduction params used: {"n_neighbors": 5, "min_dist": 0.0, "n_components": 2, "random_state": 0}
Clustering params used: {"n_clusters": 5, "linkage": "ward"}