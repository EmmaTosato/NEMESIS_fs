# Dimensionality reduction — what these methods actually do

Plain-language reference for the methods wired into `src/analysis/reduction.py` (`config/registry/params_reduction.json`). Not a general ML textbook chapter — just enough to read a config's hyperparameters and know what they're actually controlling, and to pick a method with some intuition for its trade-offs. For clustering, see `docs/methods/clustering.md`. For *why* these specific methods were chosen for NEMESIS (varimax PCA on parcellated lesion damage), see Thiebaut de Schotten et al. 2020 (`assets/papers/Thiebaut de Schotten et al - 2020 - ...`).

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
- **Also stochastic** — fix `random_state` for reproducibility, same caveat as t-SNE.

## Choosing between them, briefly

PCA first, always — it's the cheap, interpretable baseline that tells you how much of the variance is linear before reaching for something non-linear. If subjects don't separate well under PCA but a real grouping is suspected, t-SNE/UMAP are the next step for visualization; UMAP is the more practical default at NEMESIS's scale (thousands of subjects) and is what to reach for first ahead of clustering (`docs/methods/clustering.md`) rather than pure visualization.
