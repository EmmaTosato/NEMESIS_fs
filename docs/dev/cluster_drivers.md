# Cluster drivers — technical reference

Audience: developers/agents working on `src/analysis/cluster_drivers.py`, used, for two clusters against each other, by `cluster_pair.pair_regression` (`docs/dev/cluster_comparison.md`). It is an *interpretative* analysis (`docs/guides/exploration.md`): it brings in variables the clustering never saw.

## `cluster_vs_rest_regression(features, in_cluster, *, numeric, categorical, references) -> RegressionResult`

Question answered: which variables distinguish one cluster from the rest, **all considered together**. Per-variable tests cannot say whether a difference in one variable is only the reflection of another (lesion volume, disconnection load and lesion side overlap).

A logistic regression with outcome 1 = "in this cluster", 0 = "in another cluster", fitted with no regularization (`C=np.inf`).

- **Numeric** columns are standardized (mean 0, standard deviation 1, over the subjects used): each odds ratio is per standard deviation, and variables are comparable. Transformations such as a log for a skewed quantity are the caller's.
- **Categorical** columns become one 0/1 column per level except the reference level (`references[column]`, default the most frequent). Terms are named `column: level (rif. reference)`.
- **Missing values**: subjects missing any used column are dropped (`n_dropped_missing` reports how many), not imputed.
- **Inference**: Wald standard errors from the Fisher information `X' W X` (W = p(1-p)), 95% confidence interval and two-sided p on the log-odds scale. For a single binary term the standard error equals Woolf's formula for the log odds ratio, which a test checks.
- **Diagnostics** in `RegressionResult`: McFadden pseudo-R², in-sample AUC, `events_per_term`, and per-term `vif` (variance inflation factor, from the inverse of the terms' correlation matrix; above ~5 a term's odds ratio is unstable).

### Errors

`ValueError` for mismatched lengths, unknown columns, no variables, a single class after dropping missing values, a constant numeric column, an unknown reference level, fewer than `MIN_EVENTS_PER_TERM` (10) subjects in the rarer class per term (Peduzzi et al. 1996), collinear terms (condition number of the correlation matrix above 1e8), or a coefficient beyond `MAX_ABS_COEFFICIENT` (15 per standard deviation: one variable almost separates the groups and the likelihood has no finite maximum). The caller prints the message (`embedding_app._cluster_pair_regression_block` does, for `pair_regression`; the "Confronto" section that holds it is not mounted, see `docs/dev/cluster_comparison.md`).

### How to read the result

- An **odds ratio above 1** means the variable makes "in this cluster" more likely, below 1 less likely; for a numeric column it is per standard deviation, so the odds ratios of different variables are comparable.
- The odds-ratio figure of `cluster_pair.build_odds_ratio_figure` draws a term blue when its 95% confidence interval excludes 1, gray when it contains it, on a log axis. With the clusters of a pair, an odds ratio above 1 favours the first cluster.
- `pseudo_r2`, `auc` and `events_per_term` say how well the model separates the groups and whether it has enough subjects per term; `vif` says whether a term's odds ratio is unstable because of correlated variables.
- When the model cannot be estimated the call raises `ValueError` with the reason (see "Errors") instead of returning a fit that looks fine; the page prints that message.

### What it does not say

- It is association, not cause.
- A variable derived from the clustering input is associated with the cluster partly by construction (lesion summaries for a lesion run, disconnection summaries for an sdc run).
- A category that is absent from the cluster (no infratentorial lesion, say) gives an odds ratio near 0 with a very wide interval: instability, not a result. That is the case when an interval spans several orders of magnitude.
- Lesion volume and disconnection load correlate 0.88 on the current cohort: using both gives VIF above 8, so a model should keep only one of the two.
