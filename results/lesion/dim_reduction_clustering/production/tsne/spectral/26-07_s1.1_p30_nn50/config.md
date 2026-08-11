# clinical_connectome dim_reduction_clustering (tsne+spectral) — 26-07-26 17:11

## Config

```json
{
  "project": "clinical_connectome",
  "input_path": "data/derived/lesion_matrix/21-07_s1.1",
  "reduction_method": "tsne",
  "reduction_params_file": "config/registry/params_reduction.json",
  "clustering_method": "spectral",
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
  "run_notes": "production run with tuned values from TUNING_ANALYSIS.md/RUNNING_STRATEGIES.md (session s1.1): kmeans k=5, agglomerative k=2, gmm n=2, spectral n=5. dbscan excluded - open question, see RUNNING_STRATEGIES.md"
}
```

## Summary

Input matrix shape: 1150 subjects x 254865 features
Embedding shape: 1150 subjects x 2 components
Clusters found: 5
Reduction params used: {"n_components": 2, "perplexity": 30, "early_exaggeration": 12, "learning_rate": 200, "max_iter": 1000, "random_state": 0}
Clustering params used: {"n_clusters": 5, "affinity": "nearest_neighbors", "n_neighbors": 50, "random_state": 0}
