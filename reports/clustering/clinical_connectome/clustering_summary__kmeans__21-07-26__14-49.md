# clinical_connectome_21-07-26
## 14:49 (kmeans)

## Config

```json
{
  "project": "clinical_connectome",
  "input_path": "results/dim_reduction/umap/21-07_umap_run1",
  "clustering_method": "kmeans",
  "clustering_methods_requested": [
    "kmeans",
    "agglomerative",
    "gmm"
  ],
  "params_file": "config/registry/params_clustering.json",
  "output_root": "results/clustering",
  "run_name": "umap_run1",
  "overwrite": true,
  "run_notes": "Clustering on the UMAP embedding of the voxel-wise matrix"
}
```

## Summary

Matrix shape: 1150 subjects x 2 features
Clusters found: 4
Params used: {"n_clusters": 4, "random_state": 0, "n_init": "auto"}