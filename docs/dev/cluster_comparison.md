# Cluster comparison — technical reference

Audience: developers/agents working on `src/analysis/cluster_comparison.py`, `src/analysis/cluster_pair.py` and the "Confronto" section they feed in `src/analysis/embedding_app.py`. For how the section looks from a user's point of view, see `docs/guides/embedding_app.md`.

**The section is not mounted in the app**: `build_app` has no layout block and no callback for it, and the index does not list it. The numbers and the page builders below are complete and tested, and stay in place for when it returns; the pickers and callbacks described under "The page" are not wired.

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

The numeric variables and their registry columns are `CLUSTER_DESCRIPTION_VARIABLES` plus `LOCATION_FRACTIONS`; categorical ones are `CATEGORICAL_VARIABLES`. The laterality index of the interpretation notebook is not used: it lives in `lesion_metadata.csv`, not in the registry.

### The page (`embedding_app.py`)

- `cluster_pair_content_for(run, label_1, label_2)`: summary, clinical profile, regression, centroids. Never raises: a non-clustering run, an empty or repeated cluster or an unreadable registry is an `html.P` naming the cause. A run on raw data gets a message instead of the centroid block (its matrix is the feature space, not an embedding).
- `cluster_pair_anatomy_for(run, label_1, label_2, lesion_cfg, sdc_cfg, build_overlap_view, build_disconnection_view)`: the lesion maps and, for an `sdc` run, the disconnection maps in `percent` mode, each as the two clusters and their difference. It is a **separate callback and Div** from the numbers because the first build of a cluster reads every subject's NIfTI; `build_app` passes the same cached builders as the single-cluster panels. The run is a `State` of that callback, so choosing another run (which resets both clusters to `None`) never builds the maps of a stale cluster choice.
- Pickers: `comparison-run-a`, `comparison-run-b` (only in `modality`), `comparison-cluster-1`/`-2` (only in `clusters`; options from `pair_cluster_option_label`, filled by `_update_comparison_clusters`). `_show_comparison_mode` swaps which are visible.

## Colors

Counts, percentages and distances use one blue hue from light (zero) to dark. Residuals use blue to a neutral gray to red, centered on 0. Text inside a cell turns white past 50% of the one-hue scale and past 75% of either arm of the diverging one. The map difference uses `RdBu_r`, symmetric around 0.

## Clinical profile (mode `modality`)

The "Tra modalità" profile reuses `cluster_description.clusters_comparison_stats` and `embedding_app._clusters_comparison_table`, applied to a frame holding only the common subjects and each run's labels. No second implementation of those statistics.
