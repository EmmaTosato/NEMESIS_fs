"""Codice morto di `src/analysis/dendrogram_splits.py`, tolto da `src/` il 29-10-26 e tenuto qui per poterlo recuperare.

`colors_at(Z, labels_by_k, leaf_of_subject, n_leaves, k)`: l'ultimo passo di `replay_splits`, cioè i colori delle foglie
a k e lo split k-1 -> k. Nessun codice di `src/` la chiamava (solo i test, che ora usano un helper locale
`_colors_at` con lo stesso corpo).

Non è raccolto da pytest (il nome non inizia con `test_`). Per eseguirlo:
    pytest tests/legacy/dendrogram_colors_at.py
Per recuperarla: rimettere la funzione in `src/analysis/dendrogram_splits.py`.
"""

from __future__ import annotations

from collections.abc import Mapping

import numpy as np
import pytest

from src.analysis.clustering_tuning import compute_dendrogram_linkage
from src.analysis.dendrogram_splits import leaves_of_truncated_tree, replay_splits
from src.analysis.dendrogram_splits import labels_by_k_from

LAST_P = 5


def colors_at(
    Z: np.ndarray, labels_by_k: Mapping[int, np.ndarray], leaf_of_subject: np.ndarray, n_leaves: int, k: int
) -> tuple[np.ndarray, dict]:
    """The leaf colours at k and the split k-1 -> k (the last of replay_splits). Raises ValueError for k < 2."""
    _k, leaf_color, split = replay_splits(Z, labels_by_k, leaf_of_subject, n_leaves, k)[-1]
    return leaf_color, split


# --- test ---------------------------------------------------------------------------------------------------


@pytest.fixture(scope="module")
def tree():
    rng = np.random.default_rng(0)
    centres = np.array([[0, 0], [10, 0], [20, 0], [0, 30], [10, 30], [60, 60]], dtype=float)
    embedding = np.vstack([rng.normal(c, s, size=(n, 2)) for c, s, n in zip(centres, (0.3, 0.5, 0.8, 1.2, 1.6, 2.0), (20, 23, 27, 31, 36, 42))])
    Z = compute_dendrogram_linkage(embedding, {"linkage": "ward", "metric": "euclidean"})
    _layout, members, leaf_of_subject = leaves_of_truncated_tree(Z, LAST_P)
    from scipy.cluster.hierarchy import fcluster

    labels_by_k = labels_by_k_from({k: fcluster(Z, k, "maxclust") for k in range(2, LAST_P + 1)}, LAST_P, Z)
    return {"Z": Z, "labels_by_k": labels_by_k, "leaf_of_subject": leaf_of_subject, "n_leaves": len(members)}


def test_colors_at_is_the_last_step_of_replay_splits(tree):
    leaf_color, split = colors_at(tree["Z"], tree["labels_by_k"], tree["leaf_of_subject"], LAST_P, 4)
    _k, expected_color, expected_split = replay_splits(tree["Z"], tree["labels_by_k"], tree["leaf_of_subject"], LAST_P, 4)[-1]
    assert np.array_equal(leaf_color, expected_color)
    assert split["children"][0]["n"] == expected_split["children"][0]["n"]


def test_colors_at_k_below_the_first_split_raises(tree):
    with pytest.raises(ValueError, match="first split"):
        colors_at(tree["Z"], tree["labels_by_k"], tree["leaf_of_subject"], LAST_P, 1)
