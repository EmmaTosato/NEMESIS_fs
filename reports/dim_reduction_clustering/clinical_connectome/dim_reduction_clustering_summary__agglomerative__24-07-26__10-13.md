# clinical_connectome_24-07-26
## 10:13 (pacmap+agglomerative)

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
    "gmm",
    "dbscan"
  ],
  "clustering_params_file": "config/registry/params_clustering.json",
  "output_root": "results/lesion/dim_reduction_clustering",
  "session_name": "s1.1",
  "overwrite": true,
  "run_notes": "pacmap (n_neighbors=5, best trustworthiness from tuning, see results/lesion/dim_reduction/pacmap/tuning/23-07_s1.1_pacmap_tune) + kmeans/agglomerative/gmm/dbscan, voxel-wise matrix. spectral excluded from this embedding: with n_clusters=4 it always fuses one of two disconnected satellite groups into the main blob, regardless of n_neighbors (tried 10/20/50)"
}
```

## Summary

Input matrix shape: 1150 subjects x 254865 features
Embedding shape: 1150 subjects x 2 components
Clusters found: 4
Reduction params used: {"n_components": 2, "n_neighbors": 5, "MN_ratio": 0.5, "FP_ratio": 2.0, "random_state": 0}
Clustering params used: {"n_clusters": 4, "linkage": "ward"}