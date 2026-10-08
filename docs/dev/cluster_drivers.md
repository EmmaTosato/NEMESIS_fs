# Cluster drivers — technical reference

Audience: developers/agents working on `src/analysis/cluster_drivers.py`, used by section 8 of `notebooks/post-results_analysis/cluster_interpretation.ipynb`. It is an *interpretative* analysis (`docs/guides/exploration.md`): it brings in variables the clustering never saw.

## `cluster_vs_rest_regression(features, in_cluster, *, numeric, categorical, references) -> RegressionResult`

Question answered: which variables distinguish one cluster from the rest, **all considered together**. The per-variable tests of section 7 cannot say whether a difference in one variable is only the reflection of another (lesion volume, disconnection load and lesion side overlap).

A logistic regression with outcome 1 = "in this cluster", 0 = "in another cluster", fitted with no regularization (`C=np.inf`).

- **Numeric** columns are standardized (mean 0, standard deviation 1, over the subjects used): each odds ratio is per standard deviation, and variables are comparable. Transformations such as a log for a skewed quantity are the caller's.
- **Categorical** columns become one 0/1 column per level except the reference level (`references[column]`, default the most frequent). Terms are named `column: level (rif. reference)`.
- **Missing values**: subjects missing any used column are dropped (`n_dropped_missing` reports how many), not imputed.
- **Inference**: Wald standard errors from the Fisher information `X' W X` (W = p(1-p)), 95% confidence interval and two-sided p on the log-odds scale. For a single binary term the standard error equals Woolf's formula for the log odds ratio, which a test checks.
- **Diagnostics** in `RegressionResult`: McFadden pseudo-R², in-sample AUC, `events_per_term`, and per-term `vif` (variance inflation factor, from the inverse of the terms' correlation matrix; above ~5 a term's odds ratio is unstable).

### Errors

`ValueError` for mismatched lengths, unknown columns, no variables, a single class after dropping missing values, a constant numeric column, an unknown reference level, fewer than `MIN_EVENTS_PER_TERM` (10) subjects in the rarer class per term (Peduzzi et al. 1996), collinear terms (condition number of the correlation matrix above 1e8), or a coefficient beyond `MAX_ABS_COEFFICIENT` (15 per standard deviation: one variable almost separates the groups and the likelihood has no finite maximum). The notebook catches the error per cluster when it loops over all clusters, prints it, and skips that cluster.

### What it does not say

- It is association, not cause.
- A variable derived from the clustering input is associated with the cluster partly by construction (lesion summaries for a lesion run, disconnection summaries for an sdc run).
- A category that is absent from the cluster (no infratentorial lesion, say) gives an odds ratio near 0 with a very wide interval: instability, not a result. That is the case when an interval spans several orders of magnitude.
- Lesion volume and disconnection load correlate 0.88 on the current cohort: using both gives VIF above 8, so the notebook keeps only the volume.
- The laterality index is almost always near -1 (right) or +1 (left): its odds ratio per standard deviation is huge and reads as "left versus right".
