# clinical_connectome_23-07-26
## 19:00 (agglomerative)

## Config

```json
{
  "project": "clinical_connectome",
  "input_path": "data/derived/lesion_matrix/21-07_s1.1",
  "clustering_method": "agglomerative",
  "clustering_methods_requested": [
    "kmeans",
    "agglomerative",
    "dbscan",
    "spectral"
  ],
  "params_file": "config/registry/params_clustering.json",
  "output_root": "results/lesion/clustering",
  "session_name": "s1.1_raw",
  "overwrite": true,
  "run_notes": "Clustering directly on the raw voxel-wise lesion matrix (21-07_s1.1), no dimensionality reduction, all 5 methods for comparison"
}
```

## Summary

Matrix shape: 1150 subjects x 254865 features
Clusters found: 4
Params used: {"n_clusters": 4, "linkage": "ward"}