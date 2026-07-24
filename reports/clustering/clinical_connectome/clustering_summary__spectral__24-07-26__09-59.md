# clinical_connectome_24-07-26
## 09:59 (spectral)

## Config

```json
{
  "project": "clinical_connectome",
  "input_path": "results/lesion/dim_reduction/pacmap/23-07_s1.1_n5",
  "clustering_method": "spectral",
  "clustering_methods_requested": [
    "spectral"
  ],
  "params_file": "config/registry/params_clustering.json",
  "output_root": "results/lesion/clustering",
  "session_name": "pacmap_n5_spectral_nn50",
  "overwrite": true,
  "run_notes": "Re-testing spectral on the pacmap (n_neighbors=5) embedding with an even wider affinity graph (n_neighbors=50) - nn=20 still triggered the disconnected-graph warning and left the small top-right satellite fused into the main blob"
}
```

## Summary

Matrix shape: 1150 subjects x 2 features
Clusters found: 4
Params used: {"n_clusters": 4, "affinity": "nearest_neighbors", "n_neighbors": 50, "random_state": 0}