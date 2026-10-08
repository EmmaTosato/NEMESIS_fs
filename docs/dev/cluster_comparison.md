# Cluster comparison — technical reference

Audience: developers/agents working on `src/analysis/cluster_comparison.py` and the "Confronto tra run" section it feeds in `src/analysis/embedding_app.py`. For how the section looks from a user's point of view, see `docs/guides/embedding_app.md`.

## Split of responsibilities

- `src/analysis/cluster_comparison.py`: the numbers and the heatmaps. It receives two runs' metadata (and embeddings, for centroids) and never reads from disk or knows the run layout.
- `src/analysis/embedding_app.py`: which pairs of runs may be compared, loading them, and the HTML. It knows `ProductionRun`, `config.md` and the params registry.

## Which pairs are comparable

`comparison_incompatibility(run_a, run_b, mode, clustering_params_file)` returns the reason a pair is not comparable, or `None`. `comparable_runs` applies it to every candidate to fill the Run B dropdown, and `comparison_content_for` checks it again before computing anything, so a stale selection can never produce a comparison.

| Mode | Rule |
|---|---|
| `embedding` | both runs are clustering runs, neither is `raw`, and `config.md` carries the same `input_path` |
| `modality` | different modality; same clustering method; same value of the method's registered `tag_param` (`params_clustering.json`); same `reduction_method` and same `(metric, n_components)` of the upstream embedding (`run_reduction_axis`) |

The identity of an embedding is its `input_path`, not the pair `(session_name, reduction_*)`: it names the exact dim_reduction output. A run whose `config.md` has no `input_path` raises `ValueError`; the dropdown logs it and leaves it out, like every other picker.

## `cluster_comparison.py`

| Function | What it does |
|---|---|
| `align_runs(metadata_a, metadata_b)` | inner join on `subject_id`, in run A's order; returns `AlignedRuns` with labels, row positions in each run, and `n_a`/`n_b`/`n_common`. Raises on an empty intersection, a repeated `subject_id`, or missing columns |
| `contingency_tables(labels_a, labels_b)` | counts, row % and column % |
| `agreement_metrics(labels_a, labels_b)` | ARI, NMI, homogeneity, completeness |
| `agreement_level(metric, value)` | the reading of ARI/NMI from `AGREEMENT_SCALE` (`None` for the other two) |
| `chi_square_independence(counts)` | chi-square, p, dof, standardized residuals; raises if either side has a single cluster |
| `purity_table(counts)` | per source cluster: size, dominant target, share; `counts.T` gives the other direction |
| `centroid_distances(emb_a, emb_b, aligned)` | centroids and their Euclidean distances on the common subjects; raises if the two embeddings differ in shape or in any common subject's coordinates |
| `build_table_heatmap(table, ...)` | heatmap with the value in every cell; `diverging=True` centers it on 0 |

### Homogeneity and completeness: which way round

sklearn's `homogeneity_score(labels_true, labels_pred)` is defined on the *predicted* clusters. The module passes B as "true" and A as "predicted", so:

- **homogeneity** = every cluster of A contains subjects of a single cluster of B (1 when A refines B);
- **completeness** = the subjects of a cluster of B stay together in one cluster of A (1 when B refines A).

A test pins both directions on a pair where one run refines the other.

## Colors

Counts, percentages and distances use one blue hue from light (zero) to dark. Residuals use blue to a neutral gray to red, centered on 0. Text inside a cell turns white past 50% of the one-hue scale and past 75% of either arm of the diverging one.

## Clinical profile

The "Tra modalità" profile reuses `cluster_description.clusters_comparison_stats` and `embedding_app._clusters_comparison_table`, applied to a frame holding only the common subjects and each run's labels. No second implementation of those statistics.
