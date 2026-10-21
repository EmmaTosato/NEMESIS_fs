# PCA on the covariance or correlation matrix, for wide matrices — technical reference

Audience: developers/agents working on `src/analysis/covariance_pca.py` (the numerical core), `src/analysis/pca_method.py` (the `pca` method of `dim_reduction.py`, built on it) and the notebook that uses the core, `notebooks/pipeline_building/thiebaut_2020_replication.ipynb` (varimax, the paper's method; the unrotated PCA appears only in the comparison with lesion volume, section 5).

The core replicates the "Data compression" step of Thiebaut de Schotten et al. 2020 (PCA on the covariance matrix, then varimax rotation with at most 500 iterations, component scores by multiple regression) on matrices too wide for `sklearn.decomposition.PCA`, such as the voxel-wise SDC matrix: `07-10_s2.4-vol` is 5845 x 291345 float32 = 6.8 GB (out-of-brain voxels not zeroed; the replication notebook runs on it), `16-10_s2.4-vol` is 5845 x 227235 = 5.3 GB (out-of-brain voxels zeroed, the matrix of the `pca` method's tuning and production runs). sklearn copies the matrix several times (about 25.7 GB of memory on the 07-10 one).

What PCA, covariance vs correlation and varimax mean (concepts, not code): [`knowledge/notes/dim_reduction_clustering/employed_dim_reduction_methods.md`](../../knowledge/notes/dim_reduction_clustering/employed_dim_reduction_methods.md) (section "PCA e rotazione varimax"). The params of the `pca` method and how to choose them: [`docs/guides/dim_reduction.md`](../guides/dim_reduction.md), section "Il metodo `pca`".

## How the PCA is computed

Two paths to the same components, picked with `dual`. Why the small matrix gives the same eigenvalues (the SVD identity, what is checked and the numerical limit): section "PCA su una matrice più larga che alta" in `employed_dim_reduction_methods.md`.

- **`fit_covariance_pca(X, standardize=False, dual=True, chunk_columns, max_matrix_gib)`** returns a `CovariancePca`. With `Z = (X - column mean) [/ column std]`:
  - `dual=True` accumulates the n x n Gram matrix `Z Z^T` over blocks of columns and decomposes it; the eigenvectors of the feature-side matrix are `Z^T u / s`. Peak memory is one block plus the Gram matrix (about 270 MB for 5845 subjects). On the real voxel-wise matrix: about 3 minutes.
  - `dual=False` accumulates the p x p covariance matrix `Z^T Z` over row chunks (about as many values as a column block) and decomposes it.
  - `standardize=True` divides every column by its standard deviation (ddof=1, so the matrix is a correlation matrix with unit diagonal). A constant column raises. Not standardized by default, as in the paper, which writes only "covariance matrix" and says nothing else about standardization.
- **Refusals.** NaN or infinite values raise (the PCA is undefined on them, nothing is imputed or dropped). A square matrix above `max_matrix_gib` (default 8) raises with the size and the other `dual` value to try, instead of trying to allocate it (e.g. `dual=False` on the 291345 features of `07-10_s2.4-vol` would be about 680 GB, on the 227235 of `16-10_s2.4-vol` about 413 GB).
- **`CovariancePca`** holds the eigenvalues (descending, `n` of them if dual, `p` if not), the column means and scales, `n_samples`, and the eigenvector matrix on the side that was decomposed (`left_vectors` if dual, `right_vectors` if not; exactly one). `save(path)` writes it to a `.npz` (temp file then rename), `load(path)` reads it back.
- **`pca_scores(X, pca, n_components)`** are the unrotated scores (the same values as `sklearn.decomposition.PCA.transform` of the scaled matrix, up to the sign of each column).
- **`rotated_scores(X, pca, n_components, rotation, max_iter)`** rebuilds the factor loadings (`eigenvector * sqrt(eigenvalue)`, never the raw unit-norm eigenvectors) block by block, rotates them with `factor_analyzer.Rotator`, and gets the scores by solving the normal equations `(R^T R) B = R^T Z^T`, accumulated block by block. Only the orthogonal rotations of `factor_analyzer` are accepted (`SUPPORTED_ROTATIONS`): the regression assumes uncorrelated rotated components, an oblique rotation would need a different score formula. Scores of a rotated component have variance 1; the variance a rotated component explains is the sum of its squared loadings over the total variance (the notebook ranks the rotated components by it, since the scores cannot rank them). For an orthogonal rotation `T` the least-squares scores equal the unit-variance PCA scores rotated by `T`, so they are uncorrelated with each other even though the columns of the rotated loadings are not orthogonal (on `s2.4-vol` the largest off-diagonal correlation is about 1e-14).
- **`pca_embedding(X, pca, n_components, rotation, max_iter)`** dispatches: unrotated scores for `"none"`, rotated ones otherwise.
- **`resolve_n_components(eigenvalues, n_components, variance_share)`** is the count to keep: exactly one of the two must be given, `n_components` must be an integer within the components with non-zero variance, and `variance_share` gives the smallest count whose cumulative share reaches it (`components_for_share`, which raises on a spectrum without variance, for both solvers).
- **`squared_correlation(scores, covariate)`** is R^2 per component. Raises `ValueError` if the covariate or a score column is constant (the correlation is 0/0).

Memory is one block of columns plus one square matrix, never the matrix: X may be a read-only `np.memmap` (`load_matrix(..., mmap=True)`, which `dim_reduction.py` uses for `pca` with the `blocks` solver).

## Component maps (the paper's Fig. 3 and Supplementary section B)

- **`component_t_maps(X, scores, row_sets)`** fits, for every voxel, `values ~ intercept + all component scores` on each subset of subjects and returns the t-statistic of every component's coefficient: a multiple regression (the components enter together), as the paper describes. One pass over `X` serves every subset. The scores are those of the whole sample from `rotated_scores`: a half-sample map does not re-derive the components.
- **`map_reproducibility(maps_a, maps_b)`** is the Pearson correlation across voxels between the two maps of each component, from two random halves of the subjects (the paper: two halves of 666, average 0.813 ± 0.079, components from 0.39 to 0.98; here the halves are about 2900 subjects and the scores are shared, so the values are not directly comparable).
- **t-map and weights map.** The t-map of a component is close to, but not the same as, the map of its rotated loadings: the t divides each voxel by its own uncertainty. On `07-10_s2.4-vol` (the replication notebook's matrix) the correlation between the two goes from 0.74 to 0.91 per component (median 0.84).
- **Display.** A voxel is coloured when its |t| reaches `MAP_THRESHOLD_FRACTION` (0.3 in the notebook) of the component's peak |t|: with thousands of subjects even small effects have a high t, and a fixed |t| > 3 would colour almost the whole brain. The three sections cross at the peak voxel, and each figure's title gives the peak t and the component's reproducibility; the background is the MNI T1 template at 1 mm, because the 2 mm file has truncated data. Map columns go back to voxels through `non_constant_mask.npy`, in C order, on the 2 mm grid of the template header.
- **Reading the maps.** Red is a positive t (the voxel is more disconnected the more the subject has the component), blue a negative one. A compact red zone means the component is a zone of the brain. The sign of a component is arbitrary, so each map is oriented with its peak positive and is read by its shape, not its colour.
- **`positive_peak_signs(t_maps)`** orients each component so its largest-magnitude voxel is positive: the sign of a component is arbitrary, and the paper reports positive correlations only.
- **Degenerate voxels.** A voxel with no residual variance within a subset (constant there, or fitted exactly) has no defined t-statistic. Its t is 0.0 and it is counted in `ComponentMaps.n_degenerate_voxels`, never dropped.
- **Not the paper's.** The paper's maps come from `randomise` (1000 permutations, FSL), and its figures lie on white matter with anatomical and functional labels. Here the maps are unthresholded t-statistics shown on the MNI T1 template, with no permutation test and no labels (the functional ones come from 590 Neurosynth maps that are not in the repo).

## The component maps in the Embedding Explorer

`src/analysis/component_maps.py` computes the same maps for a `pca` run of `dim_reduction.py`, for the app's "Mappe delle componenti" panel (`embedding_app.run_component_maps`, `component_maps_content_for`).

- **Inputs.** The scores are the run's own `matrix.npy` (rotated or not, whatever the run saved); the matrix they are regressed against is the run's `input_path` (read from its `config.md`, relative to the working directory). `load_map_geometry(source_dir)` gives where its columns are in the brain: `non_constant_mask.npy` (flat, over the template grid, C order) and the header of the `reference_template_path` named in the matrix's own `config.md`. A matrix without either (parcellated, streamline, FC) raises with that cause. `to_volume(values, geometry)` puts one value per column back on the grid.
- **What is computed.** `ComponentMapStore.request(source_dir, scores, subject_ids)` runs `component_t_maps` once with three row sets (all subjects and two random halves, `SPLIT_SEED` = 0), orients every component with `positive_peak_signs` (the same signs for the halves), and stores the oriented whole-sample t-maps (float32, memory-mapped on read), the per-component `map_reproducibility` and the number of degenerate voxels.
- **Refusals.** The subject ids of the run and of the source matrix's `metadata.csv` must be equal *and in the same order* (row i of the scores is regressed against row i of the matrix), and the numbers of rows must agree: otherwise `ValueError` naming the first difference, never a map built on the wrong pairing. A subset too small for the number of components raises in `component_t_maps`.
- **Cache.** `BackgroundDiskCache` (`src/analysis/background_cache.py`): one worker thread, the entry written into a temporary directory renamed into place, `request` returns None while computing, raises a failed computation once and retries on the next call. The entry name is a hash of the algorithm version (`_ALGORITHM`, bump it when what is computed changes), the seed, the scores, the subject ids and the shape/dtype/64 sampled rows of the source matrix. Not detected by the key: values of the source matrix that changed outside the sampled rows after the run's scores were computed from it. The panel compares the matrix's modification time with the run's `created_at` and warns when it is later (`ComponentMapData.source_modified_after_run`).
- **Display.** `_build_component_map_view` zeroes the voxels below `COMPONENT_MAP_THRESHOLD_FRACTION` (0.3) of the component's peak |t| (`_masked_for_view_colorbar`), draws it with `view_img` (`cold_hot`, symmetric, `vmax` = peak, MNI152 background, cut on the peak voxel); `component_map_plots.build_reproducibility_figure` draws the bars with the paper's mean (0.813) as a dashed reference.
- **Number of components.** An unrotated pca production run can keep any number (`embedding_for_viz` draws its first `viz_n_components`), and the panel then offers all of them. With a rotation the columns have no order, so `dim_reduction.py` only accepts `n_components` equal to `viz_n_components` (2 or 3): a rotated production run has 2 or 3 maps.

## The notebook

`thiebaut_2020_replication.ipynb` reads `matrix.npy` (memory-mapped) and `metadata.csv` of `SESSION_DIR` and the lesion volume column of `assets/metadata/participants.csv`. It writes only a cache.

- **Parameters.** `SESSION_DIR` (`07-10_s2.4-vol`), `VARIANCE_SHARE_FOR_VARIMAX` (0.9), `VARIMAX_MAX_ITER` (500), `LESION_VOLUME_COLUMN` (`lesion_volume_voxels_2mm`), `USE_CACHE`, and for the maps `COMPONENTS_TO_PLOT`, `MAP_THRESHOLD_FRACTION` (0.3) and `SPLIT_SEED` (0).
- **Cache.** `results/pipeline_building/thiebaut_2020_replication/<session>/` holds `pca.npz`, `varimax.npz` and `maps.npz`, each next to a JSON fingerprint (session, matrix shape and mtime; plus the number of components and `max_iter` for the varimax; plus the split seed for the maps). A cache from another matrix or other parameters raises instead of being reused.
- **Sections.** 1 parameters; 2 PCA on the covariance; 3 components needed for 50%, 80% and 90% of the variance (`CovariancePca.n_components_for`); 4 varimax on the smallest number of components reaching `VARIANCE_SHARE_FOR_VARIMAX`; 5 R^2 of the scores with the lesion volume, rotated and unrotated (the paper: all rotated R^2 below 0.1); 6 t-maps, their reproducibility between two halves and the figures.

## Evaluating a PCA run (`pca_evaluation`)

`notebooks/post-results_analysis/pca_evaluation.ipynb` judges one PCA already written by `dim_reduction.py`, from [`src/analysis/pca_evaluation.py`](../../src/analysis/pca_evaluation.py); it recomputes no PCA. Its sections 3-6 are those of the replication notebook, applied to a run instead of a fit.

- **`load_pca_run(run_dir, rotation=None, n_components=None)`** reads either place a PCA is left in, into one `PcaRun` (scores, whole variance spectrum, subject ids, rotation, `standardize`, and `source_dir`, the `input_path` the PCA was computed on):
  - a **production run**: `matrix.npy` is the scores, `eigenvalues.npy` the spectrum, `config.md` the params; `rotation` and `n_components` are the run's own and passing them raises;
  - a **tuning run** with `save_tuning_embeddings`: `embeddings.npz` holds the scores of every swept combination and `eigenvalues.npz` the spectrum of the one decomposition; `rotation` and `n_components` pick the combination (a parameter the grid did not sweep is the base one). A tuning that swept anything but `rotation` and `n_components`, or that has nested leaves, or a combination that was not swept raises, naming what is there.
- **`load_source_matrix(run)`** memory-maps the matrix the PCA came from after checking that its rows are the run's subjects in the run's order. `source_dir` that is not on disk raises `FileNotFoundError`.
- **`rotated_variance_shares(X, scores, eigenvalues, standardize)`** is the share of the total variance each rotated component explains. The scores of a rotated run are uncorrelated with variance 1, so the loading of a voxel on a component is its covariance with the component's scores, and the share is the sum of the squared loadings over the sum of `eigenvalues`: the same numbers as the rotated loadings of `rotated_scores`, from one pass over `X` and without the loadings, which a run does not save. Scores that do not have variance 1 (an unrotated run's) raise.
- **`default_embedding_components`** picks the two components to draw: the first two of an unrotated run, the two with most variance of a rotated one (its columns have no order).
- **`registry_values(subject_ids, column)`** reads a participants.csv column for the subjects, raising for one that is not registered or has no value.
- **`registry_side_indicator(subject_ids)`** is the lesion side as a number for the left-right R² of section 5: 1 for a left lesion, 0 for a right one, over the subjects with a single side. It returns the indicator and the mask of the kept subjects: a bilateral lesion or an empty side lies on neither end and is left out, and the notebook prints how many. A side outside `KNOWN_LESION_SIDES` raises, so a misspelt value is not dropped like an empty one.

### Sections of the notebook

The notebook does not choose the number of components: it shows the data to choose it.

| Section | Content | Applies to |
|---|---|---|
| 1 | Choice of the run and the parameters | all runs |
| 2 | What the run holds | all runs |
| 3 | How many components to keep | all runs |
| 4 | Varimax: variance of each rotated component | rotated runs |
| 5 | How much each component depends on lesion volume (and side) | all runs |
| 6 | Component maps in the brain | voxel-wise matrices |
| 7 | Embedding | all runs |

A section that does not apply to the chosen run says so and is skipped: 4 on an unrotated run; 6 when the source matrix has no `non_constant_mask.npy` (parcellated, streamline, FC).

**Parameters** (section 1):

- `RUN_PATH`: the run folder, production or tuning.
- `ROTATION`, `N_COMPONENTS`: the `rotation` and `n_components` passed to `load_pca_run`; only for a tuning, to pick the combination. For a production run they are the run's own and passing them raises.
- `COMPARE_WITH_UNROTATED`: for a tuning with varimax only. When `True`, section 5 also shows the same combination without rotation, so the tuning must contain it (the same `n_components`, `rotation="none"`).
- `UNROTATED_RUN_PATH`: for a varimax production run only. The unrotated run of the same subjects to compare in section 5, or `None`; a path whose run is rotated raises.
- `LESION_VOLUME_COLUMN`: the volume column of `participants.csv`, in 2 mm voxels.
- `COMPONENTS_TO_PLOT`, `MAP_THRESHOLD_FRACTION` (section 6): the components to draw, numbered from 1 up to the run's `n_components`, and the share of the peak |t| under which a voxel is not coloured.
- `EMBEDDING_COMPONENTS` (section 7): the two components to draw, numbered from 1, e.g. `(1, 3)`; `None` lets `default_embedding_components` pick.

**Section 2.** If there is an unrotated comparison, it must have the same subjects in the same order as the run, otherwise the notebook raises.

**Section 3.** A table gives, for each of the 50%, 80% and 90% shares, the smallest number of components that reaches it (`components_for_share`), and two plots show the variance per component and the cumulative one. The eigenvalues are the unrotated PCA's: rotation keeps the total variance of the first k components, but they no longer describe single components, which section 4 does. Where the per-component curve flattens, further components add little; the choice stays manual.

**Section 4.** The table of rotated against PCA components is read as in `employed_dim_reduction_methods.md` (paragraph "Come si legge la tabella PCA contro ruotate"): each row is a place in the variance ranking, the PCA component on the left and the rotated one that occupies it on the right; *n.* is the label the following sections use.

**Section 5.** R^2 of every component with the lesion volume (`squared_correlation`) and, in a second plot, with the lesion side (`registry_side_indicator`, 1 left, 0 right): it says how much a component separates the two sides, not which one, because the sign of a component is arbitrary. A third table gives the cumulative R^2 of the first k components taken together (volume and side), for k up to the run's `n_components`. The first k are the first k columns for an unrotated run and the k with most variance after rotation (section 4) for a rotated one, so at equal k the two sets differ. If the R^2 rises at small k the effect is in the first components; if it rises slowly it is spread over many. Why a high R^2 matters for a clustering: `employed_dim_reduction_methods.md`, "Quanto dipende dal volume della lesione". The dashed line at 0.1 in both R^2 plots is the paper's reference value for the lesion volume ("all R^2 < 0.1", Thiebaut de Schotten et al. 2020, on the rotated components), not a threshold of ours; in the side plot it is only the same reference line, the paper has no side criterion.

**Section 6.** The maps are requested from `ComponentMapStore`: the first time they are computed in the background and take a few minutes, then they come from the cache (`results/cache/component_maps`). The reproducibility bars and one figure per component in `COMPONENTS_TO_PLOT` follow, as described in "Component maps" above.

**Section 7.** One point per subject in the two chosen components, one panel per colour mode: lesion side, volume and dataset (`COLOR_MODES_TO_SHOW`, resolved by `embedding_coloring`). The point is to see whether the components separate the subjects by something known. Without rotation the default is the first two components, the directions that separate the subjects most; with varimax, the two with most variance (section 4). In the volume panel grey is a value not available. The default for a rotated run needs the shares of section 4: run section 4 first, otherwise `rotated_share` is `None` and `default_embedding_components` raises; with `EMBEDDING_COMPONENTS` set the shares are not needed.

The brain maps are [`component_maps.py`](../../src/analysis/component_maps.py)'s (`ComponentMapStore`, in `results/cache/component_maps`, shared with the Embedding Explorer): the notebook skips them for a matrix with no `non_constant_mask.npy`. The tests are `tests/unit/test_pca_evaluation.py`.

## What is checked

`tests/unit/test_covariance_pca.py`: eigenvalues, ratios and scores against `sklearn.decomposition.PCA` for each of the four combinations of `standardize` and `dual` (also on data with a large common offset, where the Gram identities lose precision, see `lessons_learned.md` #42); the same rotated scores from both `dual` values and from an in-memory sklearn + `Rotator` + least-squares reference; result independent of the block size; every orthogonal rotation keeping the total variance of the loadings; varimax recovering known factor blocks; model save and load; every `ValueError`. `tests/unit/test_pca_method.py` covers the params contract of the `pca` method and both solvers against each other.

## Choices that are not the paper's

- **Number of components.** The paper reports "30 components, out of 46 in total, explained more than 90%" without saying how the 46 was chosen. Here the number to rotate is the smallest that reaches a chosen share of variance (0.9 in the notebook). On `07-10_s2.4-vol` that is 42 components.
- **Features.** The paper works on 372 regions; this works on voxels. Curves and R^2 are compared as tendencies, not as numbers.
- **Kaiser normalization.** `rotated_scores` calls `factor_analyzer.Rotator(method=..., max_iter=...)` without `normalize`, and the `Rotator` default is `normalize=True`: the loadings are Kaiser-normalized before the rotation and scaled back after it. The paper does not say whether it did.
- **Score estimator.** The scores are ordinary least squares of each subject's row on the rotated loadings, `(B^T B)^-1 B^T z`. In factor analysis the "regression method" usually means Thurstone's `Λ^T Σ^-1 x`, a different estimator; the paper writes only "multiple regression" and does not say which.

## References for rotation and scores

What the literature and the tools say about rotating PCA components and recomputing the scores:

- **Rotation keeps the subspace.** Sorzano et al. 2014, section 2.2.4 ("PCA rotations and Sparse PCA", in `knowledge/papers/methods/`): the rotated vectors span the same subspace, so the approximation is the same, "although the feature vector must be modified to account for the rotation". Varimax (Kaiser 1958, *Psychometrika* 23, 187-200) is the most popular criterion of the orthomax family; oblique rotations (Promax) are the alternative.
- **Scores from rotated loadings.** With PCA loadings `L`, `L^T L = D` (the eigenvalues on the diagonal), so the least-squares scores are `(L^T L)^-1 L^T`; being orthogonal, the rotation applies to the rotated loadings the same way ([FSU course notes on factor scores](https://ani.stat.fsu.edu/~jfrade/HOMEWORKS/STA5707/STA5707-fall07/files/project/tex_files/presentation4.pdf), derived for the unrotated case). The same formula as `employed_dim_reduction_methods.md`, section "I punteggi dopo la rotazione".
- **Thurstone's regression scores.** For an orthogonal rotation the factor correlation matrix is the identity, so `f = Λ^T Σ^-1 x` keeps its simple form; Harman, *Modern Factor Analysis*, pp. 351-352 ([R-help, `factanal`](https://stat.ethz.ch/pipermail/r-help/2003-May/033184.html); [R-help, scores after varimax](https://mailman.stat.ethz.ch/pipermail/r-help/2011-December/299268.html)).
- **Signs.** A rotation can flip the sign of a component; the scores must follow the loadings ([Real Statistics, factor scores](https://real-statistics.com/multivariate-statistics/factor-analysis/factor-scores/)).
- **Tool.** [`factor_analyzer.Rotator`](https://factor-analyzer.readthedocs.io/en/latest/factor_analyzer.html): varimax is its default method, with Kaiser normalization on.
