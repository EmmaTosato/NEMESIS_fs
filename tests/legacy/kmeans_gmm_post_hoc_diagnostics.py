"""Codice morto di `src/analysis/clustering_tuning.py`, tolto da `src/` il 29-10-26 e tenuto qui per poterlo recuperare.

Tre funzioni che nessuna pipeline, config o notebook chiamava (solo i test), tutte dei metodi in stand by `kmeans` e
`gmm`: `integrated_completed_likelihood` (ICL, Biernacki et al. 2000), `compute_gap_statistic` e
`gap_statistic_suggested_k` (gap statistic, Tibshirani et al. 2001). Sono pensate per essere richiamate a mano da
un notebook su un tuning già prodotto.

Non è raccolto da pytest (il nome non inizia con `test_`). Per eseguirlo:
    pytest tests/legacy/kmeans_gmm_post_hoc_diagnostics.py
Per recuperare le funzioni: rimetterle in `src/analysis/clustering_tuning.py` e i test in `tests/unit/`.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from sklearn.cluster import KMeans
from sklearn.mixture import GaussianMixture


def _three_blobs():
    rng = np.random.default_rng(0)
    return np.vstack(
        [
            rng.normal(loc=[0, 0], scale=0.3, size=(15, 2)),
            rng.normal(loc=[5, 5], scale=0.3, size=(15, 2)),
            rng.normal(loc=[0, 5], scale=0.3, size=(15, 2)),
        ]
    )


# --- funzioni ------------------------------------------------------------------------------------------------------


# Literature-established, per-parameter justification metrics (07-10-26 chat decision): unlike
# everything above, these are deliberately *not* wired into run_clustering_tuning_sweep/
# clustering.py - they're reusable, tested functions meant to be called post-hoc from a
# notebook against an already-produced tuning run's matrix.npy/
# tuning_results.csv, same contract as dunn_index. No pipeline/
# config/docs changes, no reruns needed. One per method's own hardest-to-justify parameter -
# HDBSCAN deliberately excluded (its own relative_validity_ overlaps with DBCV, already
# rejected in docs/guides/clustering.md, so adding it here would silently contradict that
# decision - flagged explicitly to the user instead of added).


def integrated_completed_likelihood(X: np.ndarray, params: dict) -> float:
    """Integrated Completed Likelihood (ICL, Biernacki, Celeux & Govaert 2000) for GMM's
    n_components/covariance_type - same lower-is-better convention as bic/aic, but adds an
    entropy penalty for ambiguous (low-confidence) soft assignments on top of BIC's plain
    likelihood-vs-complexity trade-off: ICL = BIC + 2 * entropy, entropy = -sum_i,k z_ik *
    log(z_ik) over the fitted posterior responsibilities z. Answers "BIC favors this
    n_components, but are the resulting components actually well separated, or just a better
    fit to overlapping data?" - a question BIC/AIC alone cannot answer, since both only score
    log-likelihood and model complexity, never how confidently each point is assigned.

    Fits its own GaussianMixture(**params) on X (not given a pre-fitted estimator) - cheap
    enough for a single post-hoc call per already-tested combination, and keeps this function's
    contract identical to the rest of this module's params-in functions (never takes a fitted
    sklearn object as an argument). responsibilities are clipped away from exactly 0 before the
    log (entropy's own convention: 0 * log(0) contributes 0, but numpy raises a divide-by-zero
    warning for the literal log(0) rather than silently producing -inf*0=nan).
    """
    fitted = GaussianMixture(**params).fit(X)
    responsibilities = fitted.predict_proba(X)
    nonzero = responsibilities[responsibilities > 0.0]
    entropy = -float(np.sum(nonzero * np.log(nonzero)))
    return float(fitted.bic(X)) + 2.0 * entropy


def compute_gap_statistic(
    X: np.ndarray, k_values: list[int], kmeans_params: dict, n_references: int = 10, random_state: int = 0
) -> pd.DataFrame:
    """Gap statistic (Tibshirani, Walther & Hastie 2001) for KMeans' n_clusters - a formal
    reference-distribution criterion in place of eyeballing the inertia elbow: at each k, the
    observed within-cluster dispersion log(Wk) (= KMeans' own inertia_, Tibshirani's Wk is
    exactly the standard within-cluster sum of squares) is compared against its expectation
    under `n_references` uniform-random reference datasets of the same shape (sampled
    feature-by-feature within X's own min/max range - the simplified reference distribution
    most implementations use, not the paper's optional PCA-aligned box). Gap(k) = mean_b(log
    Wkb) - log(Wk): a large gap means the real data clusters far tighter than random noise would
    at that k.

    Returns one row per k_values with columns [n_clusters, log_wk, log_wk_ref_mean, gap,
    gap_sk] - gap_sk is the reference standard deviation scaled by sqrt(1 + 1/n_references),
    feeding the 1-SE selection rule in gap_statistic_suggested_k. Never picks k itself - purely
    the numbers, same "no automatic selection" convention as every other tuning diagnostic here.
    """
    rng = np.random.default_rng(random_state)
    mins, maxs = X.min(axis=0), X.max(axis=0)

    rows = []
    for k in k_values:
        observed_log_wk = np.log(KMeans(n_clusters=k, **kmeans_params).fit(X).inertia_)

        reference_log_wks = []
        for b in range(n_references):
            reference_X = rng.uniform(mins, maxs, size=X.shape)
            reference_params = {**kmeans_params, "random_state": kmeans_params.get("random_state", 0) + b}
            reference_log_wks.append(np.log(KMeans(n_clusters=k, **reference_params).fit(reference_X).inertia_))

        log_wk_ref_mean = float(np.mean(reference_log_wks))
        gap_sk = float(np.std(reference_log_wks) * np.sqrt(1 + 1 / n_references))
        rows.append(
            {
                "n_clusters": k,
                "log_wk": float(observed_log_wk),
                "log_wk_ref_mean": log_wk_ref_mean,
                "gap": log_wk_ref_mean - float(observed_log_wk),
                "gap_sk": gap_sk,
            }
        )
    return pd.DataFrame(rows)


def gap_statistic_suggested_k(gap_results: pd.DataFrame) -> int | None:
    """Tibshirani et al. 2001's own 1-SE selection rule: the smallest k (among consecutive pairs
    in gap_results, sorted by n_clusters) such that Gap(k) >= Gap(k+1) - gap_sk(k+1). Returns
    None, not the largest k swept, when no k in the swept range satisfies the rule (e.g. gap is
    still rising at the largest k tested) - a legitimate "inconclusive, widen k_values" domain
    outcome (code_standards.md §0), not a fallback guess.
    """
    sorted_results = gap_results.sort_values("n_clusters").reset_index(drop=True)
    for i in range(len(sorted_results) - 1):
        current, nxt = sorted_results.iloc[i], sorted_results.iloc[i + 1]
        if current["gap"] >= nxt["gap"] - nxt["gap_sk"]:
            return int(current["n_clusters"])
    return None


# --- test ------------------------------------------------------------------------------------------------------------

# --- literature-established per-parameter justification metrics (07-10-26 chat decision):
# notebook-only post-hoc diagnostics, not wired into run_clustering_tuning_sweep/clustering.py --


def test_integrated_completed_likelihood_penalizes_overlapping_components_more_than_bic():
    """3 well-separated blobs: a GMM fit with the true n_components=3 should have confident
    (near 0/1) responsibilities, so ICL stays close to BIC (small entropy penalty). Forcing
    n_components=6 on the same data splits at least one blob into overlapping sub-components
    with genuinely ambiguous responsibilities - ICL's extra entropy term must open a larger
    gap above BIC there than at the true n_components."""
    X = _three_blobs()

    icl_3 = integrated_completed_likelihood(X, {"n_components": 3, "random_state": 0})
    bic_3 = GaussianMixture(n_components=3, random_state=0).fit(X).bic(X)
    icl_6 = integrated_completed_likelihood(X, {"n_components": 6, "random_state": 0})
    bic_6 = GaussianMixture(n_components=6, random_state=0).fit(X).bic(X)

    assert (icl_6 - bic_6) > (icl_3 - bic_3) >= 0


def test_compute_gap_statistic_shape_and_columns():
    X = _three_blobs()

    df = compute_gap_statistic(X, [2, 3, 4, 5], {"random_state": 0, "n_init": "auto"}, n_references=5, random_state=0)

    assert list(df["n_clusters"]) == [2, 3, 4, 5]
    assert set(df.columns) == {"n_clusters", "log_wk", "log_wk_ref_mean", "gap", "gap_sk"}
    assert (df["gap_sk"] >= 0).all()


def test_gap_statistic_suggested_k_picks_true_cluster_count():
    X = _three_blobs()

    df = compute_gap_statistic(X, [1, 2, 3, 4, 5, 6], {"random_state": 0, "n_init": "auto"}, n_references=15, random_state=0)
    suggested_k = gap_statistic_suggested_k(df)

    assert suggested_k == 3  # the fixture's true number of blobs


def test_gap_statistic_suggested_k_returns_none_when_rule_never_satisfied():
    # a single k has no "next" k to compare against -> the 1-SE rule can never fire
    df = pd.DataFrame({"n_clusters": [3], "gap": [1.0], "gap_sk": [0.1], "log_wk": [0.0], "log_wk_ref_mean": [1.0]})

    assert gap_statistic_suggested_k(df) is None



# ---- gap_statistic_suggested_k --------------------------------------------------------------------------------------------------------------------------


def _gap_frame(ks, gaps, sks):
    return pd.DataFrame({"n_clusters": ks, "gap": gaps, "gap_sk": sks})


def _oracle(frame):
    ordered = frame.sort_values("n_clusters").reset_index(drop=True)
    for i in range(len(ordered) - 1):
        if ordered.loc[i, "gap"] >= ordered.loc[i + 1, "gap"] - ordered.loc[i + 1, "gap_sk"]:
            return int(ordered.loc[i, "n_clusters"])
    return None


@settings(max_examples=200)
@given(
    ks=st.lists(st.integers(1, 30), min_size=1, max_size=8, unique=True),
    data=st.data(),
)
def test_the_one_se_rule_matches_its_definition_and_never_picks_the_last_k(ks, data):
    gaps = [data.draw(st.floats(-2, 2, allow_nan=False)) for _ in ks]
    sks = [data.draw(st.floats(0, 1, allow_nan=False)) for _ in ks]
    frame = _gap_frame(ks, gaps, sks)
    out = gap_statistic_suggested_k(frame)
    assert out == _oracle(frame)
    assert out is None or (out in ks and out != max(ks))  # l'ultimo k non ha un successore con cui confrontarsi


@settings(max_examples=60)
@given(ks=st.lists(st.integers(1, 30), min_size=2, max_size=8, unique=True), seed=st.integers(0, 10**6))
def test_the_row_order_of_the_gap_table_does_not_change_the_answer(ks, seed):
    rng = np.random.default_rng(seed)
    frame = _gap_frame(ks, rng.normal(size=len(ks)), rng.uniform(0, 1, size=len(ks)))
    shuffled = frame.sample(frac=1.0, random_state=seed)
    assert gap_statistic_suggested_k(shuffled) == gap_statistic_suggested_k(frame)


def test_the_gap_rule_with_an_empty_table_is_none_not_an_error():
    assert gap_statistic_suggested_k(_gap_frame([], [], [])) is None
