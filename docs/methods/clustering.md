# Clustering — what these methods actually do

Plain-language reference for the methods wired into `src/analysis/clustering.py` (`config/registry/params_clustering.json`). Not a general ML textbook chapter — just enough to read a config's hyperparameters and know what they're actually controlling. For dimensionality reduction, see `docs/methods/dimensionality_reduction.md`.

## The problem it solves

Clustering groups subjects into a fixed number of groups based on similarity, without knowing the "right" answer in advance (unsupervised) — the hypothesis being that clusters correspond to distinct lesion/disconnection topographies. It runs either on a dimensionality-reduction embedding (`dim_reduction_clustering.py`) or directly on a feature matrix (`clustering.py`) — see `docs/guides/analysis.md` for when each script applies.

## KMeans (`kmeans_cluster`, `"kmeans"`)

Partitions subjects into `n_clusters` groups by iteratively placing a centroid per cluster and assigning each subject to its nearest centroid, then re-computing centroids, until stable.

- **Must decide `n_clusters` upfront** — KMeans doesn't discover the number of clusters, it enforces exactly the number given. Choosing it is a separate step (e.g. inspecting a t-SNE/UMAP plot first, or a systematic criterion like silhouette score or elbow-on-inertia — not automated by this pipeline today).
- **Assumes roughly spherical, similar-sized clusters** in whatever space it's run on. This is exactly why `dim_reduction_clustering.py` clusters the *embedding* rather than the raw voxel/parcel matrix by default in this pipeline's typical use — clustering directly on hundreds of thousands of raw voxel columns is both computationally wasteful and geometrically unreliable for KMeans (`clustering.py`, the no-reduction script, exists for when that's still the deliberate choice, e.g. clustering directly on a small parcellated matrix).
- **Sensitive to feature scale**: features with a larger numeric range dominate the distance calculation. Not a concern for `fraction_lesioned`-parcellated features (all already in `[0, 1]`) or for a PCA/UMAP/t-SNE embedding (already on a comparable scale) — would matter if clustering directly on raw voxel counts of very different magnitudes.
- **Stochastic centroid initialization**: set `random_state` for reproducibility; `n_init` controls how many random initializations are tried before keeping the best (higher = more robust to bad initial placement, slower).
