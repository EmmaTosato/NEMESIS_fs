"""`density_summary` e `membership_confidence` di `src/analysis/clustering_evaluation.py`, tolti da `src/` il 29-10-26 e tenuti qui per poterli recuperare.

L'Embedding Explorer le chiamava per il pannello "Clustering evaluation" di `hdbscan` e `hdbscan_soft`; il pannello ora legge i numeri che la
produzione salva in `production_results.csv` e `production_results_per_cluster.csv` (`src/analysis/production_results.py`) e nessuno
chiama più le due funzioni. `density_summary` dà il DBCV di una run e le quote di cluster e rumore; `membership_confidence` rifitta
HDBSCAN e dà la probabilità media per cluster.

Non è raccolto da pytest (il nome non inizia con `test_`). Per eseguirlo:
    pytest tests/legacy/density_membership_summaries.py
Per recuperare le funzioni: rimetterle (con `DensitySummary` e `MembershipConfidence`) in `src/analysis/clustering_evaluation.py`, rimettere
nel registro `EVALUATIONS` la voce di `EVALUATIONS_TO_RESTORE` e i test in `tests/unit/test_clustering_evaluation.py`.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
import pytest
from sklearn.cluster import HDBSCAN

from src.analysis.clustering_evaluation import EVALUATIONS, Evaluation, require_applicable
from src.analysis.clustering_tuning import hdbscan_labels_and_probabilities
from src.analysis.dbcv import run_dbcv
from src.analysis.partition_shape import partition_shape

# La voce del registro che apparteneva a `membership_confidence` (quella di `density_summary`, `dbcv`, è rimasta in `src/`).
EVALUATIONS_TO_RESTORE: dict[str, Evaluation] = {
    "membership_confidence": Evaluation(
        frozenset({"hdbscan"}),
        "probabilities_ is an output of HDBSCAN only (strength of membership of each subject in its own cluster, "
        "normalized within the cluster); the other methods assign a subject to a cluster without a degree of membership",
    ),
}


# --- funzioni ------------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class MembershipConfidence:
    """How firmly the subjects of an hdbscan run belong to their cluster, from `probabilities_`.

    `clusters` has one row per non-noise cluster: `n` and `probability_mean`. No threshold: the literature has
    no reference value for a probability, so the table reports the mean only.
    """

    clusters: pd.DataFrame  # index: cluster label; columns: n, probability_mean
    n_noise: int


def membership_confidence(method: str, X: np.ndarray, params: dict, labels: np.ndarray) -> MembershipConfidence:
    """Membership strength of an already-produced hdbscan run.

    `probabilities_` is a lambda value normalised to [0, 1] inside each cluster (0 for noise), so it
    says how close a subject sits to the core of *its* cluster, not how likely it is to belong to this
    cluster rather than another. It exists only on the fitted estimator, which a run does not store: it
    is refit with the run's own params and accepted only if it reproduces the stored labels exactly, as
    in model_fit_metrics. It is a description of the density in the space clustered (an embedding with
    min_dist=0 is already packed), not a validity index. Noise is left out of every number (its
    probability is 0 by construction).

    Raises ValueError for a method other than hdbscan, a refit that does not reproduce the labels, or a
    run where every subject is noise.
    """
    require_applicable("membership_confidence", method)
    labels = np.asarray(labels)
    noise = labels == -1
    if noise.all():
        raise ValueError("every subject is noise (label -1): there is no cluster to describe")

    refit_labels, probabilities = hdbscan_labels_and_probabilities(X, params)
    if not np.array_equal(refit_labels, labels):
        raise ValueError(
            f"refitting 'hdbscan' with params={params} does not reproduce the stored labels - "
            "its probabilities would describe a different fit than the run"
        )

    frame = pd.DataFrame({"cluster": labels[~noise], "probability": probabilities[~noise]})
    grouped = frame.groupby("cluster")["probability"]
    return MembershipConfidence(clusters=pd.DataFrame({"n": grouped.size(), "probability_mean": grouped.mean()}), n_noise=int(noise.sum()))


@dataclass(frozen=True)
class DensitySummary:
    """The evaluation of one hdbscan / hdbscan_soft run: DBCV over all the subjects (noise included in the weights)
    and the cluster/noise shares. `clusters` has one row per cluster, indexed by its label, with `n` and `dbcv` (its
    own score). `dbcv` is NaN, `clusters` empty and `note` the reason when DBCV is not defined for the run: fewer
    than 2 clusters, or a non-Euclidean metric (src/analysis/dbcv.py::run_dbcv). `note` is "" otherwise."""

    n_subjects: int
    n_components: int
    n_clusters: int
    largest_cluster_share: float
    noise_fraction: float
    dbcv: float
    clusters: pd.DataFrame  # index: cluster label; columns: n, dbcv
    note: str = ""


def density_summary(X: np.ndarray, labels: np.ndarray, combo_params: dict) -> DensitySummary:
    """DBCV and the cluster/noise shares of a density run, as the Embedding Explorer panel shows them.

    `combo_params` is the run's own params. A run for which DBCV is not defined (fewer than 2 clusters, or clustered
    under a non-Euclidean metric) is not refused: it comes back with the shares, `dbcv` NaN and the reason in `note`
    (src/analysis/dbcv.py::run_dbcv). Raises ValueError for a `labels`/`X` length mismatch, for a cluster of one
    subject and for non-finite values.
    """
    labels = np.asarray(labels)
    if X.ndim != 2 or len(X) != len(labels):
        raise ValueError(f"X must be 2D with one row per label, got X.shape={X.shape} and {len(labels)} labels")
    shape = partition_shape(labels)
    result = run_dbcv(X, labels, combo_params)
    clusters = result.clusters.set_index("cluster") if not result.clusters.empty else pd.DataFrame(
        {"n": [], "dbcv": []}, index=pd.Index([], name="cluster")
    )
    return DensitySummary(
        n_subjects=shape.n_subjects, n_components=X.shape[1], n_clusters=shape.n_clusters,
        largest_cluster_share=shape.largest_cluster_share, noise_fraction=shape.noise_fraction,
        dbcv=result.score, clusters=clusters, note=result.note,
    )


# --- test ------------------------------------------------------------------------------------------------------------


@pytest.fixture
def registered(monkeypatch):
    """Il registro con la voce rimessa: in `src/` non c'è più."""
    for name, evaluation in EVALUATIONS_TO_RESTORE.items():
        monkeypatch.setitem(EVALUATIONS, name, evaluation)


# --- membership_confidence --------------------------------------------------

_HDBSCAN_PARAMS = {"min_cluster_size": 15, "min_samples": 5}


def _blobs_of_mixed_density():
    """Two tight blobs and a loose one, plus a few far outliers: HDBSCAN finds three clusters,
    some noise, and probabilities below 1 inside the loose cluster."""
    rng = np.random.default_rng(0)
    return np.vstack(
        [
            rng.normal(loc=[0, 0], scale=0.2, size=(60, 2)),
            rng.normal(loc=[8, 0], scale=1.0, size=(60, 2)),
            rng.normal(loc=[0, 8], scale=0.2, size=(60, 2)),
            [[30.0, 30.0], [-30.0, 30.0], [30.0, -30.0]],
        ]
    )


def _fit_hdbscan(X):
    fitted = HDBSCAN(**_HDBSCAN_PARAMS).fit(X)
    return fitted.labels_, fitted.probabilities_


def test_membership_confidence_summarises_hdbscans_own_probabilities_per_cluster(registered):
    X = _blobs_of_mixed_density()
    labels, probabilities = _fit_hdbscan(X)
    assert (labels == -1).any() and len(set(labels) - {-1}) == 3  # the fixture is what the test assumes

    result = membership_confidence("hdbscan", X, _HDBSCAN_PARAMS, labels)

    for cluster, row in result.clusters.iterrows():
        p = probabilities[labels == cluster]
        assert row["n"] == len(p)
        assert row["probability_mean"] == pytest.approx(p.mean())
    assert list(result.clusters.columns) == ["n", "probability_mean"]  # no threshold: the literature has no reference value
    assert result.n_noise == int((labels == -1).sum())


def test_membership_confidence_refuses_a_refit_that_does_not_reproduce_the_labels(registered):
    X = _blobs_of_mixed_density()
    labels, _ = _fit_hdbscan(X)

    with pytest.raises(ValueError, match="does not reproduce the stored labels"):
        membership_confidence("hdbscan", X, _HDBSCAN_PARAMS, np.roll(labels, 1))


def test_membership_confidence_refuses_a_method_without_membership_probabilities(registered):
    with pytest.raises(ValueError, match="'kmeans'"):
        membership_confidence("kmeans", np.zeros((4, 2)), {}, np.zeros(4, dtype=int))


def test_membership_confidence_refuses_a_run_that_is_all_noise(registered):
    X = _blobs_of_mixed_density()

    with pytest.raises(ValueError, match="every subject is noise"):
        membership_confidence("hdbscan", X, _HDBSCAN_PARAMS, np.full(len(X), -1))


def test_membership_confidence_is_registered_for_hdbscan_only(registered):
    require_applicable("membership_confidence", "hdbscan")
    with pytest.raises(ValueError, match="'agglomerative'"):
        require_applicable("membership_confidence", "agglomerative")


# --- density_summary / DBCV -------------------------------------------------------------------------


def _density_fixture():
    rng = np.random.default_rng(0)
    X = np.vstack([rng.normal(centre, 0.3, (30, 2)) for centre in (0.0, 8.0)] + [rng.uniform(-20, 30, (6, 2))])
    return X, np.array([0] * 30 + [1] * 30 + [-1] * 6)


def test_density_summary_has_the_dbcv_the_shares_and_one_row_per_cluster():
    from src.analysis.dbcv import dbcv

    X, labels = _density_fixture()
    result = density_summary(X, labels, {"min_cluster_size": 5})

    assert result.dbcv == pytest.approx(dbcv(X, labels)[0])
    assert result.n_clusters == 2 and result.n_subjects == 66 and result.n_components == 2
    assert result.largest_cluster_share == pytest.approx(30 / 66) and result.noise_fraction == pytest.approx(6 / 66)
    assert result.clusters["n"].tolist() == [30, 30] and list(result.clusters.columns) == ["n", "dbcv"]


def test_density_summary_of_a_run_dbcv_is_not_defined_for_keeps_the_shares_and_says_why():

    X, labels = _density_fixture()
    one = density_summary(X, np.where(labels == 0, 0, -1), {})
    cosine = density_summary(X, labels, {"metric": "cosine"})

    assert np.isnan(one.dbcv) and one.clusters.empty and "fewer than 2 clusters" in one.note and one.n_clusters == 1
    assert np.isnan(cosine.dbcv) and cosine.clusters.empty and "Euclidean" in cosine.note
    assert cosine.n_clusters == 2 and cosine.noise_fraction == pytest.approx(6 / 66)
    assert density_summary(X, labels, {}).note == ""


def test_density_summary_raises_for_a_length_mismatch():

    X, labels = _density_fixture()
    with pytest.raises(ValueError, match="one row per label"):
        density_summary(X, labels[:-1], {})


def test_the_tuning_and_the_app_count_clusters_and_noise_the_same_way():
    from src.analysis.clustering_evaluation import model_fit_metrics
    from src.analysis.clustering_tuning import compute_noise_metrics

    X, labels = _density_fixture()

    fit = model_fit_metrics("hdbscan", X, {}, labels)
    summary = density_summary(X, labels, {})

    assert compute_noise_metrics(labels)["noise_fraction"] == fit["noise_fraction"] == summary.noise_fraction
    assert fit["n_clusters_found"] == summary.n_clusters == 2
