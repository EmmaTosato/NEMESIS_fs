# Covariance PCA + varimax on a wide matrix — technical reference

Audience: developers/agents working on `src/analysis/covariance_pca.py` and the notebook that uses it, `notebooks/pipeline_building/thiebaut_2020_replication.ipynb` (varimax, the paper's method, with the unrotated PCA alongside for comparison).

This module replicates the "Data compression" step of Thiebaut de Schotten et al. 2020 (PCA on the covariance matrix, then varimax rotation with at most 500 iterations, component scores by multiple regression) on matrices too wide for `pca_varimax_embed` (`src/analysis/reduction.py`), such as the voxel-wise SDC matrix (5845 x 291345 float32 = 6.8 GB).

What PCA, covariance vs correlation and varimax mean (concepts, not code): [`knowledge/dim_reduction_clustering/employed_dim_reduction_methods.md`](../../knowledge/dim_reduction_clustering/employed_dim_reduction_methods.md) (section "PCA e rotazione varimax").

## Why `pca_varimax_embed` is not enough

`pca_varimax_embed` centers `X` into a second full copy, `sklearn.PCA` copies it again, and the score step solves a least-squares problem on a float64 transpose of `X` (about 13 GB for the matrix above). It is the right tool for the matrices that go through `dim_reduction.py`; it does not fit in memory here.

## How the same PCA is computed

Why the small matrix gives the same eigenvalues (the SVD identity, what is checked and the numerical limit): section "PCA su una matrice più larga che alta" in [`employed_dim_reduction_methods.md`](../../knowledge/dim_reduction_clustering/employed_dim_reduction_methods.md).

The covariance matrix over features would be 291345 x 291345. With `Xc = X - column mean`, the eigenvectors of `Xc^T Xc / (n-1)` with non-zero eigenvalue are `Xc^T u / s`, where `u` and `s` are the eigenvectors and singular values of the small Gram matrix `Xc Xc^T` (n x n); the eigenvalues are `s^2 / (n-1)`. So:

- **`fit_covariance_pca(X)`** accumulates the Gram matrix over blocks of columns (`DEFAULT_CHUNK_COLUMNS`), takes its eigendecomposition, and returns a `CovariancePca` (eigenvalues, left vectors, column means). Not scaled, as in the paper. On the real matrix: about 4 minutes.
- **`varimax_scores(X, pca, n_components, max_iter)`** rebuilds the factor loadings (`eigenvector * sqrt(eigenvalue)`, never the raw unit-norm eigenvectors) block by block, rotates them with `factor_analyzer.Rotator`, and gets the scores by solving the normal equations `(R^T R) B = R^T Xc^T`, accumulated block by block. Same result as `pca_varimax_embed`, without a full-size copy of `X`.
- **`CovariancePca.pca_scores(k)`** are the unrotated scores; **`squared_correlation(scores, covariate)`** is R^2 per component.

Peak memory is one block of columns plus the n x n Gram matrix, not the matrix.

## Component maps (the paper's Fig. 3 and Supplementary section B)

- **`component_t_maps(X, scores, row_sets)`** fits, for every voxel, `values ~ intercept + all component scores` on each subset of subjects and returns the t-statistic of every component's coefficient: a multiple regression (the components enter together), as the paper describes. One pass over `X` serves every subset. The scores are those of the whole sample from `varimax_scores`: a half-sample map does not re-derive the components.
- **`map_reproducibility(maps_a, maps_b)`** is the Pearson correlation across voxels between the two maps of each component, from two random halves of the subjects (the paper: two halves of 666, average 0.813).
- **`positive_peak_signs(t_maps)`** orients each component so its largest-magnitude voxel is positive: the sign of a component is arbitrary, and the paper reports positive correlations only.
- **Degenerate voxels.** A voxel with no residual variance within a subset (constant there, or fitted exactly) has no defined t-statistic. Its t is 0.0 and it is counted in `ComponentMaps.n_degenerate_voxels`, never dropped.
- **Not the paper's.** The paper's maps come from `randomise` (1000 permutations, FSL), and its figures lie on white matter with anatomical and functional labels. Here the maps are unthresholded t-statistics shown on the MNI T1 template, with no permutation test and no labels (the functional ones come from 590 Neurosynth maps that are not in the repo).

## What is checked

`tests/unit/test_covariance_pca.py`: eigenvalues and ratios against `sklearn.decomposition.PCA` (also on data with a large common offset, where the Gram identities lose precision, see `lessons_learned.md` #42); result independent of the block size; scores against `pca_varimax_embed` up to the sign and order of each component; varimax recovering known factor blocks; every `ValueError`.

## Choices that are not the paper's

- **Number of components.** The paper reports "30 components, out of 46 in total, explained more than 90%" without saying how the 46 was chosen. Here the number to rotate is the smallest that reaches a chosen share of variance (0.9 in the notebook). On `s2.4-vol` that is 42 components.
- **Features.** The paper works on 372 regions; this works on voxels. Curves and R^2 are compared as tendencies, not as numbers.
