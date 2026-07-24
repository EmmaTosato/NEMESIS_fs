# clinical_connectome — lesion › dim_reduction_clustering › tsne › kmeans › tuning › 24-07_s1.1_p30

## Config

```json
{
  "project": "clinical_connectome",
  "input_path": "data/derived/lesion_matrix/21-07_s1.1",
  "reduction_method": "tsne",
  "reduction_params_used": {
    "n_components": 2,
    "perplexity": 30,
    "early_exaggeration": 12,
    "learning_rate": 200,
    "max_iter": 1000,
    "random_state": 0
  },
  "clustering_method": "kmeans",
  "clustering_params_file": "config/registry/params_clustering.json",
  "session_name": "s1.1"
}
```

## Summary

Embedding shape: 1150 subjects x 2 components (reduction fixed, not swept)
Swept parameters: ['n_clusters']
Combinations evaluated: 7
Metrics: ['silhouette', 'calinski_harabasz', 'davies_bouldin', 'inertia']

No automatic selection - inspect tuning_results.csv/tuning_plot.png and pick parameters by hand.
