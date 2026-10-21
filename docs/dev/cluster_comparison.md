# Cluster comparison — technical reference

Audience: developers/agents working on `src/analysis/cluster_comparison.py`, `src/analysis/cluster_pair.py` and the "Confronto" section they feed in `src/analysis/embedding_app.py`. For how the section looks from a user's point of view, see `docs/guides/embedding_app.md`.

**The section is not mounted in the app**: `build_app` has no layout block and no callback for it, and the index does not list it. The numbers and the page builders below are complete and tested, and stay in place for when it returns; the pickers and callbacks of the section do not exist in `build_app` (see "The page").

The section has two modes:

- **`clusters`** ("Dentro lo stesso clustering"): two clusters of one run. Numbers in `cluster_pair.py`, page in `cluster_pair_content_for` and `cluster_pair_anatomy_for`.
- **`modality`** ("Tra modalità"): two runs of different modalities on their common subjects. Numbers in `cluster_comparison.py`, page in `comparison_content_for`.

## Split of responsibilities

- `src/analysis/cluster_comparison.py`: the numbers and the heatmaps of the `modality` mode. It receives two runs' metadata and never reads from disk or knows the run layout.
- `src/analysis/cluster_pair.py`: the numbers of the `clusters` mode. It reads the subject registry (`participants.csv`) and nothing else from disk; maps and embeddings come in as arguments.
- `src/analysis/embedding_app.py`: which pairs of runs may be compared, loading them, and the HTML. It knows `ProductionRun`, `config.md` and the params registry.

## Which pairs of runs are comparable (mode `modality`)

`comparison_incompatibility(run_a, run_b, clustering_params_file)` returns the reason a pair is not comparable, or `None`. `comparable_runs` applies it to every candidate to fill the Run B dropdown, and `comparison_content_for` checks it again before computing anything, so a stale selection can never produce a comparison. `comparison_candidates` (every clustering run, raw ones included) fills the first dropdown in both modes.

Rule: different modality; same clustering method; same value of the method's registered `tag_param` (`params_clustering.json`); same `reduction_method` and same `(metric, n_components)` of the upstream embedding (`run_reduction_axis`).

A run whose `config.md` cannot be read raises `ValueError` from the rule; the dropdown logs it and leaves it out, like every other picker.

Why the rule is this strict:

- **Same method and same `tag_param`**: the only thing that may differ between the two runs is the upstream pipeline (lesion vs sdc), so a disagreement cannot be blamed on the clustering criterion.
- **Common subjects only**: the two modalities cover different subjects by construction (`lesion` includes subjects without a computed SDC output, and the other way round), so the comparison runs on the intersection and `align_runs` reports `n_a`, `n_b` and `n_common`; it never merges silently.
- **Centroids are never compared across modalities**: the embeddings live in different feature spaces (lesion voxels vs SDC regions), so two coordinates are not the same quantity even when both are 2D. The valid stand-in is the clinical phenotype of each cluster (see "Clinical profile"), which does not depend on coordinates.
- **Centroid distance between two runs** (`clustering_comparison.ipynb`, Part 1 section 5 and Part 3) needs a shared embedding: the same `session_name`, `reduction_method`, `reduction_n_components` and `reduction_metric` (hence the same upstream `input_path`). Two embeddings share a space only by numerical coincidence, never by guarantee; the notebook's `require_shared_embedding` raises on any differing key, and Part 3 skips the incompatible pairs printing the reason.

## `cluster_comparison.py`

| Function | What it does |
|---|---|
| `align_runs(metadata_a, metadata_b)` | inner join on `subject_id`, in run A's order; returns `AlignedRuns` with labels and `n_a`/`n_b`/`n_common`. Raises on an empty intersection, a repeated `subject_id`, or missing columns |
| `contingency_tables(labels_a, labels_b)` | counts, row % and column % |
| `agreement_metrics(labels_a, labels_b)` | ARI, NMI, homogeneity, completeness |
| `agreement_level(metric, value)` | the reading of ARI/NMI from `AGREEMENT_SCALE` (`None` for the other two) |
| `chi_square_independence(counts)` | chi-square, p, dof, standardized residuals; raises if either side has a single cluster |
| `purity_table(counts)` | per source cluster: size, dominant target, share; `counts.T` gives the other direction |
| `cluster_centroids(embedding, labels)` | mean embedding coordinates of each cluster (used by `cluster_pair.centroid_separation`) |
| `build_table_heatmap(table, ...)` | heatmap with the value in every cell; `diverging=True` centers it on 0 |

### Reading scale of ARI and NMI

`AGREEMENT_SCALE` holds the upper bound of the first four of the five `AGREEMENT_LEVELS` (a value equal to a bound belongs to the level above):

| Level | ARI | NMI |
|---|---|---|
| debole/trascurabile | below 0.2 | below 0.3 |
| moderato | 0.2 to 0.4 | 0.3 to 0.5 |
| discreto | 0.4 to 0.6 | 0.5 to 0.7 |
| forte | 0.6 to 0.8 | 0.7 to 0.85 |
| quasi identiche | above 0.8 | above 0.85 |

It is a **rule of thumb of ours**, without a source in the literature consulted: a way to put a word on a number, not a threshold of validity. NMI is less severe than ARI, so its bounds are higher for the same level.

### What the numbers mean

- **ARI**: agreement of two partitions over pairs of subjects (together in both, apart in both, or discordant), corrected for chance; not inflated by many clusters; it can be negative. **NMI**: shared information normalized to [0, 1]; more intuitive, but it can overestimate with many clusters. Both are external indices (they compare two partitions, not a partition with the data). Definitions: `knowledge/notes/dim_reduction_clustering/clustering_literature_survey.md`, section 6.
- **NMI** (sklearn default normalization) equals the harmonic mean of homogeneity and completeness. A harmonic mean hides the imbalance between the two, so a pair of runs with high homogeneity and low completeness (or the other way round) looks the same as the opposite pair in ARI and NMI; the two are read separately.
- **Contingency table**: row = cluster of A, column = cluster of B, cell = subjects in both. Labels are arbitrary across runs, so only the distribution of the mass matters, not the label numbers. It is not symmetric; its row sums are the sizes of A's clusters and its column sums those of B's.
- **Row % and column %** answer different questions: where each cluster of A goes in B (row), and which clusters of A each cluster of B is made of (column). With very different cluster sizes the same count can be "almost all of a cluster" in one direction and a small fraction in the other, so both are shown.
- **Chi-square** (`chi_square_independence`): H0 is that membership in A and in B are independent; the expected table comes from the row and column totals; the standardized (Pearson) residual of a cell, `(observed - expected) / sqrt(expected)`, reads like a z-score. The p says *whether* the partitions are associated, the residuals say *where* (positive: the pair co-occurs more than expected, drawn red; negative: less, drawn blue).
- **Purity** (`purity_table`): the share of a source cluster that lands in its dominant target, sorted from the least pure to the purest. It is half the picture, roughly the homogeneity of a single cluster; whether the target is in turn owned only by that source is the completeness side, read with `counts.T`.
- **Heatmap of ARI/NMI** across several runs: symmetric, with 1 on the diagonal (a run against itself, ignored); NMI is usually higher than ARI at equal similarity, so the colors of the two panels differ.

### Homogeneity and completeness: which way round

sklearn's `homogeneity_score(labels_true, labels_pred)` is defined on the *predicted* clusters. The module passes B as "true" and A as "predicted", so:

- **homogeneity** = every cluster of A contains subjects of a single cluster of B (1 when A refines B);
- **completeness** = the subjects of a cluster of B stay together in one cluster of A (1 when B refines A).

A test pins both directions on a pair where one run refines the other.

## `cluster_pair.py`

"First cluster" is the one passed as `label_1`; the sign of `r`, of an odds ratio and of the map difference depends on it, and swapping the two inverts them (tests pin this).

| Function | What it does |
|---|---|
| `pair_frame(metadata, label_1, label_2)` | one row per subject of the two clusters with every variable, read from `participants.csv` (never from the run's `metadata.csv`). A subject missing from the registry stays with missing values and is listed in `unregistered`. Raises on equal labels, an empty cluster, metadata without `cluster_label`, or a registry without one of the needed columns |
| `pair_clinical_comparison(pair, label_1)` | Mann-Whitney per numeric variable (age, education, NIHSS, volume, the seven lesion-location shares) with the rank-biserial `r = 2U/(n1 n2) - 1`; Fisher exact per category of sex/dataset/lesion side/dominant location; Benjamini-Hochberg over all tests together. A side with fewer than 2 values leaves `r`, `p` and `p_fdr` missing, never 0 |
| `pair_regression(pair, label_1)` | `cluster_vs_rest_regression` on the two clusters only, outcome "in the first cluster"; numeric `REGRESSION_NUMERIC`, categorical `REGRESSION_CATEGORICAL`. Its refusals (see `docs/dev/cluster_drivers.md`) propagate as `ValueError` and the page prints them |
| `build_odds_ratio_figure(result, label_1, label_2)` | odds ratio with 95% interval per term, log axis, blue when the interval excludes 1 |
| `regression_term_label(term)` | readable name of a coefficient; raises on an unknown one |
| `centroid_separation(embedding, metadata, label_1, label_2)` | Euclidean distance between the two centroids and each cluster's mean distance of its subjects from its own centroid |
| `difference_image(image_1, image_2)` | voxelwise subtraction; raises if the two images are not on the same grid |

### How to read the outputs

- **Signs follow the first cluster**: `r` (rank-biserial) is positive when cluster 1 has the higher values; an odds ratio (Fisher, or the regression's) is above 1 when the category or the variable is more frequent in, or makes more likely, cluster 1. The same holds in `pair_clinical_comparison` and in the odds-ratio figure.
- **`p_fdr`, not `p`**: the Benjamini-Hochberg correction is applied to all the tests together; the corrected value is the one to read.
- **Regression**: an odds ratio is per standard deviation for a numeric variable; the figure paints a point blue when its 95% interval excludes 1. It is an association, not a cause. When the lesion volume is part of the clustering input (a lesion run) it is associated with the clusters partly by construction. A fit that cannot be estimated (too few subjects, collinearity, perfect separation) raises `ValueError` with the reason (`docs/dev/cluster_drivers.md`).
- **Centroid distance**: read against each cluster's radius (`radius_1`, `radius_2`, the mean distance of its subjects from its own centroid); a distance much larger than both radii means well separated clusters. Only for a run on an embedding: on a raw run the matrix is the feature space.
- **Maps**: per cluster, the % of subjects with a lesion in each voxel; the difference is cluster 1 minus cluster 2, red where the lesion is more frequent in cluster 1 and blue where it is in cluster 2 (`RdBu_r`, symmetric around 0).

The numeric variables and their registry columns are `CLUSTER_DESCRIPTION_VARIABLES` plus `LOCATION_FRACTIONS`; categorical ones are `CATEGORICAL_VARIABLES`. The laterality index of the interpretation notebook is not used: it lives in `lesion_metadata.csv`, not in the registry.

### The page (`embedding_app.py`)

- `cluster_pair_content_for(run, label_1, label_2)`: summary, clinical profile, regression, centroids. Never raises: a non-clustering run, an empty or repeated cluster or an unreadable registry is an `html.P` naming the cause. A run on raw data gets a message instead of the centroid block (its matrix is the feature space, not an embedding).
- `cluster_pair_anatomy_for(run, label_1, label_2, lesion_cfg, sdc_cfg, build_overlap_view, build_disconnection_view)`: the lesion maps and, for an `sdc` run, the disconnection maps in `percent` mode, each as the two clusters and their difference. It is a **separate callback and Div** from the numbers because the first build of a cluster reads every subject's NIfTI; `build_app` passes the same cached builders as the single-cluster panels. The run is a `State` of that callback, so choosing another run (which resets both clusters to `None`) never builds the maps of a stale cluster choice.
- Pickers: none exist in `build_app`. `comparable_runs` gives the options of a run B picker (`modality` mode) and `pair_cluster_option_label(label, metadata)` the text of a cluster option (`clusters` mode); the pickers, the mode switch and their callbacks have to be written when the section is mounted.

## Colors

Counts, percentages and distances use one blue hue from light (zero) to dark. Residuals use blue to a neutral gray to red, centered on 0. Text inside a cell turns white past 50% of the one-hue scale and past 75% of either arm of the diverging one. The map difference uses `RdBu_r`, symmetric around 0.

## Clinical profile (mode `modality`)

The "Tra modalità" profile reuses `cluster_description.clusters_comparison_stats` and `embedding_app._clusters_comparison_table`, applied to a frame holding only the common subjects and each run's labels. No second implementation of those statistics.
