# Lesions - Umap - Dbscan

## Config

```json
{
  "project": "clinical_connectome",
  "input_path": "data/derived/lesion_matrix/21-07_s1.1",
  "reduction_method": "umap",
  "reduction_params_used": {
    "n_neighbors": 15,
    "min_dist": 0.0,
    "n_components": 2,
    "random_state": 0,
    "metric": "euclidean"
  },
  "clustering_method": "dbscan",
  "clustering_params_file": "config/registry/params_clustering.json",
  "session_name": "s1.1_volOFF",
  "clustering_base_params": {
    "eps": 0.5,
    "min_samples": 5
  },
  "clustering_tuning_grid": {
    "eps": [
      0.3,
      0.5,
      0.7,
      1.0,
      1.5,
      2.0
    ]
  }
}
```

## Summary

Embedding shape: 1150 subjects x 2 components (reduction fixed, not swept)
Swept parameters: ['eps']
Combinations evaluated: 6
Metrics: ['silhouette', 'calinski_harabasz', 'davies_bouldin', 'noise_fraction']

Warning: no automatic selection - inspect tuning_results.csv/tuning_plot.png and pick parameters by hand.
