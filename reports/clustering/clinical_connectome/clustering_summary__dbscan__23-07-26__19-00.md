# clinical_connectome_23-07-26
## 19:00 (dbscan)

## Config

```json
{
  "project": "clinical_connectome",
  "input_path": "data/derived/lesion_matrix/21-07_s1.1",
  "clustering_method": "dbscan",
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
Clusters found: 0 (+ 1150 noise points, label -1)
Params used: {"eps": 0.5, "min_samples": 5}