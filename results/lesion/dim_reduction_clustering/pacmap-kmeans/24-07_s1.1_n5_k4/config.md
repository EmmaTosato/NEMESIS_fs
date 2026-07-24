# clinical_connectome dim_reduction_clustering (pacmap+kmeans) — 24-07-26 09:56

## Config

```json
{
  "project": "clinical_connectome",
  "input_path": "data/derived/lesion_matrix/21-07_s1.1",
  "reduction_method": "pacmap",
  "reduction_params_file": "config/registry/params_reduction.json",
  "clustering_method": "kmeans",
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
  "run_notes": "pacmap (n_neighbors=5, best trustworthiness from tuning, see results/lesion/dim_reduction/pacmap/tuning/23-07_s1.1_pacmap_tune) + all 5 clustering methods, voxel-wise matrix"
}
```

## Summary

Input matrix shape: 1150 subjects x 254865 features
Embedding shape: 1150 subjects x 2 components
Clusters found: 4
Reduction params used: {"n_components": 2, "n_neighbors": 5, "MN_ratio": 0.5, "FP_ratio": 2.0, "random_state": 0}
Clustering params used: {"n_clusters": 4, "random_state": 0, "n_init": "auto"}
