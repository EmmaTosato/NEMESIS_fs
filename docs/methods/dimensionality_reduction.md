# Dimensionality reduction — what these methods actually do

Plain-language reference for the methods wired into `src/analysis/reduction.py` (`config/registry/params_reduction.json`). Not a general ML textbook chapter — just enough to read a config's hyperparameters and know what they're actually controlling, and to pick a method with some intuition for its trade-offs. For clustering, see `docs/methods/clustering.md`. For *why* these specific methods were chosen for NEMESIS (varimax PCA on parcellated lesion damage), see Thiebaut de Schotten et al. 2020 (`papers/Thiebaut de Schotten et al - 2020 - ...`).

t-SNE's parameters below are fixed from that paper - not something to fine-tune. UMAP/PCA's `n_neighbors`/`min_dist`/`n_components` don't have a paper-given answer for this data, so `dim_reduction.py` supports a manual fine-tuning sweep over them (`fine_tuning: true`, `docs/guides/analysis.md` "Fine-tuning") - a human still picks the final value by inspecting the sweep's results, never automatic.

## The problem it solves

`build_lesion_matrix.py` produces one row per subject with hundreds of thousands of voxel columns (or a few hundred parcel columns, if parcellated) — far more columns than subjects. Dimensionality reduction compresses each subject's row into a handful of numbers (2-30, typically) that still capture most of what makes subjects different from each other — either to visualize subjects on a 2D plot, or to feed a smaller, less noisy input into clustering.

## PCA — Principal Component Analysis (`pca_embed`, `"pca"`)

Finds the directions (linear combinations of the original features) along which subjects vary the *most*, and projects onto the top few. Purely linear: each output component is literally `w1*feature1 + w2*feature2 + ...` for some fixed weights — which also makes it the only method here whose output components can be interpreted back in terms of the original voxels/parcels (e.g. "component 1 loads heavily on left MCA territory").

- **Fast, deterministic** (no randomness, same input always gives the same output — unlike UMAP/t-SNE).
- **Assumes linear structure**: if the real differences between subjects are non-linear (e.g. two distinct lesion topographies that don't differ by a simple additive combination of voxels), PCA can blur them together instead of separating them.
- **Key parameter**: `n_components` — how many top directions to keep. There's no "correct" value; it's chosen by how much cumulative variance is explained (see Thiebaut de Schotten et al. 2020's approach: enough components to explain >90% of variance) or simply fixed at 2 for visualization.

## t-SNE — t-distributed Stochastic Neighbor Embedding (`tsne_embed`, `"tsne"`)

Non-linear. Tries to place subjects on a 2D (or 3D) map such that subjects that were close neighbors in the original high-dimensional space stay close on the map — it optimizes *local* neighborhood structure, not a fixed linear projection.

- **Good at revealing tight local clusters visually** — often produces visually crisper-looking separated blobs than PCA/UMAP on the same data.
- **Distances *between* clusters on the plot are not meaningful** — two clusters drawn far apart aren't necessarily more different than two drawn close together. Cluster *sizes* on the plot aren't meaningful either. This is t-SNE's most common misreading: don't infer relative similarity between clusters from the plot, only "these points are neighbors" within a cluster.
- **Stochastic**: results differ between runs unless `random_state` (or `init="random"`'s seed) is fixed — set once and kept in `config/registry/params_reduction.json` for a reproducible run.
- **Key parameters**:
  - `perplexity` — roughly, the expected number of close neighbors per point; controls the local/global balance. Too low → fragments genuine clusters into noise; too high → smears distinct clusters together. Typical range 5-50; must be smaller than the number of subjects.
  - `early_exaggeration` — inflates distances between clusters early in optimization to help them separate cleanly before fine-tuning; rarely needs tuning away from the library default range.
  - `learning_rate`, `max_iter` — standard optimization controls; `max_iter` too low can leave the embedding under-converged (points still visibly drifting if you re-ran with more iterations).

## UMAP — Uniform Manifold Approximation and Projection (`umap_embed`, `"umap"`)

Also non-linear and also neighbor-based, but built on a different mathematical foundation than t-SNE (manifold learning / topological data analysis) that tends to preserve more of the *global* arrangement (roughly: relative distances between clusters are somewhat more trustworthy than in t-SNE, though still not to be over-interpreted). Generally faster than t-SNE on larger datasets and scales better to thousands of subjects.

- **Key parameters**:
  - `n_neighbors` — analogous to t-SNE's `perplexity`: how many nearby points define a subject's local neighborhood. Small values focus on fine local structure (risk: fragmenting real clusters); large values favor broad global structure (risk: blurring real distinctions).
  - `min_dist` — how tightly points are allowed to pack together in the low-dimensional output. Low values produce tighter, more visually separated clusters; high values spread points more evenly, useful for seeing continuous gradients rather than discrete groups.
  - `metric` — what counts as "close". Production default `euclidean`; on binary voxel-wise lesion data this is dominated by lesion **volume** more than topography (a PCA component was found to correlate r=0.92 with lesion volume on this same data, see `results/lesion/dim_reduction_clustering/TUNING_ANALYSIS.md`) — `jaccard`/`dice` normalize by each subject's own lesion size instead, so two small lesions in the same spot and two large lesions in the same spot score equally close. The fine-tuning grid (`config/registry/params_reduction.json`) sweeps `metric` alongside `n_neighbors` for exactly this comparison.
- **Also stochastic** — fix `random_state` for reproducibility, same caveat as t-SNE.
- **Binary metrics are precomputed, not passed as a raw string**: `jaccard`/`dice` on a 250k+-voxel feature matrix via `scipy`'s per-pair boolean distance is prohibitively slow (~19 minutes extrapolated for 1150 subjects); `src/analysis/distances.py::binary_pairwise_distance` computes the same result via a matrix multiplication (binary overlap counts = `X @ X.T`) in seconds instead, used internally by `evaluate_umap` (`src/analysis/tuning.py`) whenever the swept `metric` is `jaccard`/`dice` — both the embedding *and* its `trustworthiness` score are computed from that same precomputed matrix, so a binary-metric embedding is scored against neighborhoods defined the same way it was built (not silently judged by trustworthiness's own euclidean default).

## PCA with varimax rotation (`pca_varimax_embed`, `"pca_varimax"`)

Same starting point as plain PCA (covariance-matrix eigendecomposition), but the loadings are then rotated with an orthogonal **varimax** rotation before scores are computed by multiple regression - this is the exact methodology of Thiebaut de Schotten et al. 2020's "Data compression" step (parcellate with MMP + 12 subcortical ROIs, then varimax-rotated PCA), which `build_lesion_matrix.py`'s parcellated output is designed to match.

- **Why rotate at all**: plain PCA's components are mathematically convenient (orthogonal, maximal variance) but not necessarily easy to *interpret* - a raw component often loads a little on almost every parcel. Varimax rotates the components (without changing the subspace they span, or the total variance they explain - it's an orthogonal rotation) to make each component's loadings as close as possible to "a few parcels load heavily, the rest near zero" - easier to read as "this component is basically left MCA territory".
- **Two-step estimator, not one**: unlike the other strategies here, `pca_varimax_embed` doesn't blindly unpack `params` into a single constructor - it wraps two distinct steps (`sklearn.decomposition.PCA`, then `factor_analyzer.Rotator(method="varimax")`), so `params` requires both `n_components` and `rotation_max_iter` explicitly (`ValueError` if either is missing).
- **`n_components` must be >= 2** - varimax rotates loadings *between* components, so there's nothing to rotate with only one.
- **Component scores via multiple regression**: after rotation, each subject's row is regressed onto the rotated loadings to get that subject's component scores (`np.linalg.lstsq`) - the same "multiple regression" step the paper describes, not just re-projecting through the (now rotated) loadings directly.
- **Deterministic**, like plain PCA - no `random_state` needed.
- Supports the same manual fine-tuning sweep as plain PCA (`n_components` vs. cumulative explained variance - the rotation doesn't change that criterion, since it's orthogonal).

## PaCMAP — Pairwise Controlled Manifold Approximation (`pacmap_embed`, `"pacmap"`)

Another non-linear, neighbor-based method (github.com/YingfanWang/PaCMAP), positioned by its authors as balancing local and global structure preservation better than either t-SNE or UMAP alone, by explicitly weighting three kinds of point pairs during optimization (nearby, mid-near, and further pairs) instead of just nearby ones.

- **Key parameters**: `n_neighbors` (same role as UMAP's), `MN_ratio`/`FP_ratio` - control how many mid-near/further pairs are sampled relative to nearby pairs, which is what lets PaCMAP balance local vs. global structure (higher `MN_ratio` pulls towards preserving more global relationships).
- **Also stochastic** - fix `random_state` for reproducibility.
- **Needs enough subjects to be meaningful**: `n_neighbors` (and the derived mid-near/further pair counts) must fit within the number of subjects; on very small datasets (e.g. a handful of subjects) the library reorganizes/warns rather than failing outright, but the projection is not meaningful at that scale.
- Supports the same manual fine-tuning sweep as UMAP (`n_neighbors` vs. trustworthiness - a generic neighbor-preservation metric, not specific to UMAP's own algorithm).

## Choosing between them, briefly

PCA first, always — it's the cheap, interpretable baseline that tells you how much of the variance is linear before reaching for something non-linear. If subjects don't separate well under PCA but a real grouping is suspected, t-SNE/UMAP are the next step for visualization; UMAP is the more practical default at NEMESIS's scale (thousands of subjects) and is what to reach for first ahead of clustering (`docs/methods/clustering.md`) rather than pure visualization. `pca_varimax` is the interpretable option when the goal is reading component *meaning* off parcels/voxels (matching the paper's own methodology exactly), not just separating subjects. `pacmap` is an alternative to try alongside UMAP when UMAP's local/global trade-off looks off for a given run - not a default, since UMAP is already established here.
