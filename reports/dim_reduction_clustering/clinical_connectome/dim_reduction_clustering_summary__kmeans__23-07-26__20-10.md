# clinical_connectome_23-07-26
## 20:10 (umap+kmeans)

## Config

```json
{
  "project": "clinical_connectome",
  "input_path": "data/derived/lesion_matrix/21-07_s1.1",
  "reduction_method": "umap",
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
  "run_notes": "umap (n_neighbors=5, min_dist=0.0) + all 5 clustering methods, voxel-wise matrix"
}
```

## Summary

Input matrix shape: 1150 subjects x 254865 features
Embedding shape: 1150 subjects x 2 components
Clusters found: 4
Reduction params used: {"n_neighbors": 5, "min_dist": 0.0, "n_components": 2, "random_state": 0}
Clustering params used: {"n_clusters": 4, "random_state": 0, "n_init": "auto"}