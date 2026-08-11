# clinical_connectome dim_reduction_clustering (pacmap+agglomerative) — 26-07-26 16:46

## Config

```json
{
  "project": "clinical_connectome",
  "input_path": "data/derived/lesion_matrix/21-07_s1.1",
  "reduction_method": "pacmap",
  "reduction_params_file": "config/registry/params_reduction.json",
  "clustering_method": "agglomerative",
  "clustering_methods_requested": [
    "kmeans",
    "agglomerative",
    "gmm"
  ],
  "clustering_params_file": "config/registry/params_clustering.json",
  "output_root": "results/lesion/dim_reduction_clustering",
  "session_name": "s1.1",
  "overwrite": true,
  "fine_tuning": false,
  "run_notes": "production run with tuned values from TUNING_ANALYSIS.md/RUNNING_STRATEGIES.md (session s1.1): kmeans k=6, agglomerative k=2 (macro split, dendrogram-consistent, chosen over k=5 alternative), gmm n=6. spectral excluded (fuses satellite groups on this embedding, known issue). dbscan excluded - open question, see RUNNING_STRATEGIES.md"
}
```

## Summary

Input matrix shape: 1150 subjects x 254865 features
Embedding shape: 1150 subjects x 2 components
Clusters found: 2
Reduction params used: {"n_components": 2, "n_neighbors": 5, "MN_ratio": 0.5, "FP_ratio": 2.0, "random_state": 0}
Clustering params used: {"n_clusters": 2, "linkage": "ward"}
