# PCA on the covariance or correlation matrix, for wide matrices — technical reference

Audience: developers/agents working on `src/analysis/covariance_pca.py` (the numerical core), `src/analysis/pca_method.py` (the `pca` method of `dim_reduction.py`, built on it) and the notebook that uses the core, `notebooks/pipeline_building/thiebaut_2020_replication.ipynb` (varimax, the paper's method, with the unrotated PCA alongside for comparison).

The core replicates the "Data compression" step of Thiebaut de Schotten et al. 2020 (PCA on the covariance matrix, then varimax rotation with at most 500 iterations, component scores by multiple regression) on matrices too wide for `sklearn.decomposition.PCA`, such as the voxel-wise SDC matrix (5845 x 291345 float32 = 6.8 GB): sklearn copies the matrix several times (about 25.7 GB of memory on it).

What PCA, covariance vs correlation and varimax mean (concepts, not code): [`knowledge/dim_reduction_clustering/employed_dim_reduction_methods.md`](../../knowledge/dim_reduction_clustering/employed_dim_reduction_methods.md) (section "PCA e rotazione varimax"). The params of the `pca` method and how to choose them: [`docs/guides/dim_reduction.md`](../guides/dim_reduction.md), section "Il metodo `pca`".

## How the PCA is computed

Two paths to the same components, picked with `dual`. Why the small matrix gives the same eigenvalues (the SVD identity, what is checked and the numerical limit): section "PCA su una matrice più larga che alta" in `employed_dim_reduction_methods.md`.

- **`fit_covariance_pca(X, standardize=False, dual=True, chunk_columns, max_matrix_gib)`** returns a `CovariancePca`. With `Z = (X - column mean) [/ column std]`:
  - `dual=True` accumulates the n x n Gram matrix `Z Z^T` over blocks of columns and decomposes it; the eigenvectors of the feature-side matrix are `Z^T u / s`. Peak memory is one block plus the Gram matrix (about 270 MB for 5845 subjects). On the real voxel-wise matrix: about 3 minutes.
  - `dual=False` accumulates the p x p covariance matrix `Z^T Z` over row chunks (about as many values as a column block) and decomposes it.
  - `standardize=True` divides every column by its standard deviation (ddof=1, so the matrix is a correlation matrix with unit diagonal). A constant column raises. Not standardized, as in the paper, by default.
- **Refusals.** NaN or infinite values raise (the PCA is undefined on them, nothing is imputed or dropped). A square matrix above `max_matrix_gib` (default 8) raises with the size and the other `dual` value to try, instead of trying to allocate it (e.g. `dual=False` on 291345 features would be about 680 GB).
- **`CovariancePca`** holds the eigenvalues (descending, `n` of them if dual, `p` if not), the column means and scales, `n_samples`, and the eigenvector matrix on the side that was decomposed (`left_vectors` if dual, `right_vectors` if not; exactly one). `save(path)` writes it to a `.npz` (temp file then rename), `load(path)` reads it back.
- **`pca_scores(X, pca, n_components)`** are the unrotated scores (the same values as `sklearn.decomposition.PCA.transform` of the scaled matrix, up to the sign of each column).
- **`rotated_scores(X, pca, n_components, rotation, max_iter)`** rebuilds the factor loadings (`eigenvector * sqrt(eigenvalue)`, never the raw unit-norm eigenvectors) block by block, rotates them with `factor_analyzer.Rotator`, and gets the scores by solving the normal equations `(R^T R) B = R^T Z^T`, accumulated block by block. Only the orthogonal rotations of `factor_analyzer` are accepted (`SUPPORTED_ROTATIONS`): the regression assumes uncorrelated rotated components, an oblique rotation would need a different score formula. Scores of a rotated component have variance 1; the variance a rotated component explains is the sum of its squared loadings over the total variance.
- **`pca_embedding(X, pca, n_components, rotation, max_iter)`** dispatches: unrotated scores for `"none"`, rotated ones otherwise.
- **`resolve_n_components(eigenvalues, n_components, variance_share)`** is the count to keep: exactly one of the two must be given, `n_components` must be an integer within the components with non-zero variance, and `variance_share` gives the smallest count whose cumulative share reaches it (`components_for_share`).
- **`squared_correlation(scores, covariate)`** is R^2 per component.

Memory is one block of columns plus one square matrix, never the matrix: X may be a read-only `np.memmap` (`load_matrix(..., mmap=True)`, which `dim_reduction.py` uses for `pca` with the `blocks` solver).

## Component maps (the paper's Fig. 3 and Supplementary section B)

- **`component_t_maps(X, scores, row_sets)`** fits, for every voxel, `values ~ intercept + all component scores` on each subset of subjects and returns the t-statistic of every component's coefficient: a multiple regression (the components enter together), as the paper describes. One pass over `X` serves every subset. The scores are those of the whole sample from `rotated_scores`: a half-sample map does not re-derive the components.
- **`map_reproducibility(maps_a, maps_b)`** is the Pearson correlation across voxels between the two maps of each component, from two random halves of the subjects (the paper: two halves of 666, average 0.813).
- **`positive_peak_signs(t_maps)`** orients each component so its largest-magnitude voxel is positive: the sign of a component is arbitrary, and the paper reports positive correlations only.
- **Degenerate voxels.** A voxel with no residual variance within a subset (constant there, or fitted exactly) has no defined t-statistic. Its t is 0.0 and it is counted in `ComponentMaps.n_degenerate_voxels`, never dropped.
- **Not the paper's.** The paper's maps come from `randomise` (1000 permutations, FSL), and its figures lie on white matter with anatomical and functional labels. Here the maps are unthresholded t-statistics shown on the MNI T1 template, with no permutation test and no labels (the functional ones come from 590 Neurosynth maps that are not in the repo).

## What is checked

`tests/unit/test_covariance_pca.py`: eigenvalues, ratios and scores against `sklearn.decomposition.PCA` for each of the four combinations of `standardize` and `dual` (also on data with a large common offset, where the Gram identities lose precision, see `lessons_learned.md` #42); the same rotated scores from both `dual` values and from an in-memory sklearn + `Rotator` + least-squares reference; result independent of the block size; every orthogonal rotation keeping the total variance of the loadings; varimax recovering known factor blocks; model save and load; every `ValueError`. `tests/unit/test_pca_method.py` covers the params contract of the `pca` method and both solvers against each other.

## Choices that are not the paper's

- **Number of components.** The paper reports "30 components, out of 46 in total, explained more than 90%" without saying how the 46 was chosen. Here the number to rotate is the smallest that reaches a chosen share of variance (0.9 in the notebook). On `s2.4-vol` that is 42 components.
- **Features.** The paper works on 372 regions; this works on voxels. Curves and R^2 are compared as tendencies, not as numbers.
