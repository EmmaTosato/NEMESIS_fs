# Lesions - Umap - Agglomerative

## Config

```json
{
  "project": "clinical_connectome",
  "input_path": "data/derived/lesion_matrix/21-07_s1.1",
  "reduction_method": "umap",
  "reduction_params_used": {
    "n_neighbors": 5,
    "min_dist": 0.0,
    "n_components": 2,
    "random_state": 0
  },
  "clustering_method": "agglomerative",
  "clustering_params_file": "config/registry/params_clustering.json",
  "session_name": "s1.1"
}
```

## Summary

Embedding shape: 1150 subjects x 2 components (reduction fixed, not swept)
Swept parameters: ['n_clusters']
Combinations evaluated: 7
Metrics: ['silhouette', 'calinski_harabasz', 'davies_bouldin']

No automatic selection - inspect tuning_results.csv/tuning_plot.png and pick parameters by hand.
