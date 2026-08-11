# Lesions - Pca - Kmeans

## Config

```json
{
  "project": "clinical_connectome",
  "input_path": "data/derived/lesion_matrix/21-07_s1.1",
  "reduction_method": "pca",
  "reduction_params_used": {
    "n_components": 2,
    "random_state": 0
  },
  "clustering_method": "kmeans",
  "clustering_params_file": "config/registry/params_clustering.json",
  "session_name": "s1.1",
  "clustering_base_params": {
    "n_clusters": 4,
    "random_state": 0,
    "n_init": "auto"
  },
  "clustering_tuning_grid": {
    "n_clusters": [
      2,
      3,
      4,
      5,
      6,
      8,
      10
    ]
  }
}
```

## Summary

Embedding shape: 1150 subjects x 2 components (reduction fixed, not swept)
Swept parameters: ['n_clusters']
Combinations evaluated: 7
Metrics: ['silhouette', 'calinski_harabasz', 'davies_bouldin', 'inertia']

Warning: no automatic selection - inspect tuning_results.csv/tuning_plot.png and pick parameters by hand.
