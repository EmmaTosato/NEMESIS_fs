"""Unit tests for src/analysis/dendrogram_splits.py."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from scipy.cluster.hierarchy import fcluster
from sklearn.metrics import adjusted_rand_score

from src.analysis.clustering_tuning import compute_dendrogram_linkage
from src.analysis.clustering_tuning_analysis import ClusteringTuningRun
from src.analysis.dendrogram_splits import (
    MAX_LEAVES,
    PALETTE,
    build_split_tree,
    build_step_embedding_figure,
    build_tree_figure,
    check_tree_reproduces_labels,
    colors_at,
    cut_height,
    labels_by_k_from,
    leaf_name,
    leaves_of_truncated_tree,
    replay_splits,
    saved_labels_for,
    split_at,
)

BLOB_SIZES = (20, 23, 27, 31, 36, 42)  # all different: a split of two equal clusters has no "bigger piece"
N_SUBJECTS = sum(BLOB_SIZES)
LAST_P = 5


@pytest.fixture(scope="module")
def tree():
    """Six well-separated 2D blobs of different spread, so the splits come in a fixed, non-degenerate order."""
    rng = np.random.default_rng(0)
    centres = np.array([[0, 0], [10, 0], [20, 0], [0, 30], [10, 30], [60, 60]], dtype=float)
    spread = np.array([0.3, 0.5, 0.8, 1.2, 1.6, 2.0])
    embedding = np.vstack([rng.normal(c, s, size=(n, 2)) for c, s, n in zip(centres, spread, BLOB_SIZES)])
    Z = compute_dendrogram_linkage(embedding, {"linkage": "ward", "metric": "euclidean"})
    layout, members, leaf_of_subject = leaves_of_truncated_tree(Z, LAST_P)
    saved = {k: fcluster(Z, k, "maxclust") for k in range(2, LAST_P + 1)}
    return {"embedding": embedding, "Z": Z, "layout": layout, "members": members, "leaf_of_subject": leaf_of_subject,
            "labels_by_k": labels_by_k_from(saved, LAST_P, Z)}


def test_leaves_cover_every_subject_exactly_once(tree):
    assert len(tree["members"]) == LAST_P
    assert sorted(np.concatenate(tree["members"])) == list(range(N_SUBJECTS))
    assert set(tree["leaf_of_subject"]) == set(range(LAST_P))


def test_more_leaves_than_colours_raises(tree):
    with pytest.raises(ValueError, match="colours"):
        leaves_of_truncated_tree(tree["Z"], MAX_LEAVES + 1)


def test_leaf_name_is_one_leaf_or_a_range(tree):
    leaf_of_subject = np.array([0, 0, 1, 2, 3])
    assert leaf_name(np.array([0, 1]), leaf_of_subject) == "L1"
    assert leaf_name(np.array([2, 3, 4]), leaf_of_subject) == "L2–L4"


def test_split_at_undoes_the_merge_into_the_two_clusters_of_k(tree):
    split = split_at(tree["Z"], 4, tree["labels_by_k"][4], tree["leaf_of_subject"])

    child_a, child_b = split["children"]
    assert split["parent"]["n"] == child_a["n"] + child_b["n"]
    assert child_a["label"] != child_b["label"]
    assert split["distance"] == tree["Z"][-3, 2]
    for child in split["children"]:  # a child is a whole cluster of the cut at k
        assert set(np.flatnonzero(tree["labels_by_k"][4] == child["label"])) == set(child["members"])


def test_cut_height_is_between_the_last_merge_kept_and_the_first_dropped(tree):
    Z = tree["Z"]
    assert Z[-4, 2] < cut_height(Z, 4) < Z[-3, 2]


def test_every_k_has_exactly_k_colours_and_the_bigger_piece_keeps_the_colour(tree):
    previous, _ = colors_at(tree["Z"], tree["labels_by_k"], tree["leaf_of_subject"], LAST_P, 2)
    for k in range(3, LAST_P + 1):
        leaf_color, split = colors_at(tree["Z"], tree["labels_by_k"], tree["leaf_of_subject"], LAST_P, k)
        assert len(set(leaf_color)) == k
        bigger, smaller = sorted(split["children"], key=lambda child: child["n"], reverse=True)
        bigger_leaves = np.unique(tree["leaf_of_subject"][bigger["members"]])
        smaller_leaves = np.unique(tree["leaf_of_subject"][smaller["members"]])
        assert set(leaf_color[bigger_leaves]) == set(previous[bigger_leaves]) == set(previous[smaller_leaves])
        assert set(leaf_color[smaller_leaves]).isdisjoint(set(previous))
        previous = leaf_color


def test_colors_at_k_below_the_first_split_raises(tree):
    with pytest.raises(ValueError, match="first split"):
        colors_at(tree["Z"], tree["labels_by_k"], tree["leaf_of_subject"], LAST_P, 1)


def test_a_k_the_tuning_did_not_sweep_is_the_cut_of_the_tree_into_k_clusters(tree):
    # A sweep over 2, 3, 5 has a hole at 4: the walk down the tree still needs the cut there.
    saved = {k: fcluster(tree["Z"], k, "maxclust") for k in (2, 3, 5)}

    labels = labels_by_k_from(saved, 5, tree["Z"])

    assert sorted(labels) == [1, 2, 3, 4, 5]
    assert len(np.unique(labels[4])) == 4
    assert adjusted_rand_score(labels[4], fcluster(tree["Z"], 4, "maxclust")) == 1.0
    for k in (2, 3, 5):  # the labels the tuning saved are kept as they are
        assert labels[k] is saved[k] or np.array_equal(labels[k], saved[k])


def test_labels_of_another_number_of_subjects_than_the_tree_raise(tree):
    with pytest.raises(ValueError, match="subjects"):
        labels_by_k_from({2: np.zeros(N_SUBJECTS - 1, dtype=int)}, 2, tree["Z"])


def test_there_is_a_colour_for_each_of_the_thirty_clusters_a_tuning_sweeps():
    assert MAX_LEAVES >= 30 and len(set(PALETTE)) == len(PALETTE)


def test_split_at_gives_the_members_of_the_parent_cluster(tree):
    split = split_at(tree["Z"], 4, tree["labels_by_k"][4], tree["leaf_of_subject"])

    parent_label = np.unique(tree["labels_by_k"][3][split["parent"]["members"]])
    assert len(parent_label) == 1  # the parent is one whole cluster of the cut at k-1
    assert set(np.flatnonzero(tree["labels_by_k"][3] == parent_label[0])) == set(split["parent"]["members"])
    assert split["parent"]["n"] == len(split["parent"]["members"])


def test_replay_splits_gives_one_step_per_k_with_the_colours_of_that_k(tree):
    steps = replay_splits(tree["Z"], tree["labels_by_k"], tree["leaf_of_subject"], LAST_P, LAST_P)

    assert [k for k, _colors, _split in steps] == list(range(2, LAST_P + 1))
    for k, leaf_color, _split in steps:
        assert len(set(leaf_color[leaf_color >= 0])) == k  # k colours at k, not the final ones
    by_hand = [colors_at(tree["Z"], tree["labels_by_k"], tree["leaf_of_subject"], LAST_P, k)[0] for k in range(2, LAST_P + 1)]
    assert all(np.array_equal(a, b) for (_k, a, _s), b in zip(steps, by_hand))


def test_tree_reproducing_the_saved_labels_passes_even_with_other_label_names(tree):
    renamed = {k: (labels + 7) % 11 for k, labels in tree["labels_by_k"].items()}
    check_tree_reproduces_labels(tree["Z"], renamed, tree["members"], range(2, LAST_P + 1))


def test_labels_of_another_partition_make_the_check_raise(tree):
    # Regression guard for "same matrix, so same tree": a tuning rewritten later keeps the keys and changes the labels.
    wrong = {k: labels.copy() for k, labels in tree["labels_by_k"].items()}
    wrong[3][0], wrong[3][-1] = wrong[3][-1], wrong[3][0]

    with pytest.raises(ValueError, match="k=3"):
        check_tree_reproduces_labels(tree["Z"], wrong, tree["members"], range(2, LAST_P + 1))


def test_a_leaf_cut_in_two_by_the_labels_raises(tree):
    # Fine-grained labels at k=2 inside one leaf: ARI of the tree cut is no longer 1 either way, so build the case
    # the check names explicitly: labels equal to the tree cut, but members taken from a leaf that spans two clusters.
    members = [np.concatenate(tree["members"][:2])] + list(tree["members"][2:])
    with pytest.raises(ValueError, match="leaf"):
        check_tree_reproduces_labels(tree["Z"], tree["labels_by_k"], members, range(2, LAST_P + 1))


def _embedding_figure(tree, k, highlighted=(), embedding=None, note=""):
    leaf_color, _split = colors_at(tree["Z"], tree["labels_by_k"], tree["leaf_of_subject"], LAST_P, k)
    figure = build_step_embedding_figure(
        tree["embedding"] if embedding is None else embedding, tree["labels_by_k"][k], leaf_color,
        tree["leaf_of_subject"], set(highlighted), note,
    )
    return figure, leaf_color


def test_embedding_figure_has_one_trace_per_cluster_with_the_colour_of_its_leaves_and_no_legend(tree):
    figure, leaf_color = _embedding_figure(tree, 4)

    assert len(figure.data) == 4
    assert sum(len(t.x) for t in figure.data) == N_SUBJECTS
    assert {t.marker.color for t in figure.data} == {PALETTE[c] for c in set(leaf_color)}
    assert figure.layout.showlegend is False
    assert all(type(t).__name__ == "Scatter" for t in figure.data)  # SVG: many WebGL figures on a page break


def test_embedding_figure_names_every_cluster_and_makes_the_highlighted_ones_bigger_and_bold(tree):
    leaf_color, split = colors_at(tree["Z"], tree["labels_by_k"], tree["leaf_of_subject"], LAST_P, 4)
    new = {child["label"] for child in split["children"]}

    figure, _ = _embedding_figure(tree, 4, highlighted=new, note="i due nuovi")

    labels = list(figure.layout.annotations)
    assert len(labels) == 4
    bold = [a for a in labels if a.text.startswith("<b>")]
    assert len(bold) == 2 and all(a.font.size > 10 for a in bold)
    assert all(a.font.size == 12 for a in labels if a not in bold)
    assert "i due nuovi" in figure.layout.title.text and "4 cluster" in figure.layout.title.text


def test_embedding_figure_refuses_a_three_component_embedding_instead_of_slicing_it(tree):
    three = np.hstack([tree["embedding"], np.zeros((len(tree["embedding"]), 1))])

    with pytest.raises(ValueError, match="2 components"):
        _embedding_figure(tree, 3, embedding=three)


def test_tree_figure_colours_each_leaf_as_its_cluster_and_cuts_at_k(tree):
    leaf_color, _split = colors_at(tree["Z"], tree["labels_by_k"], tree["leaf_of_subject"], LAST_P, 4)

    figure = build_tree_figure(tree["Z"], tree["layout"], tree["members"], leaf_color, 4)

    leaves = figure.data[1]
    assert list(leaves.marker.color) == [PALETTE[c] for c in leaf_color]
    (cut,) = figure.layout.shapes
    assert cut.y0 == cut.y1 == pytest.approx(cut_height(tree["Z"], 4))
    assert list(figure.layout.xaxis.ticktext) == [f"L{i + 1}" for i in range(LAST_P)]


def _tuning(tree, linkage="ward", metric="euclidean", method="agglomerative"):
    """A ClusteringTuningRun holding the labels of `tree` for the combination (linkage, metric), plus a decoy
    combination with other labels that must never be picked up."""
    rows, labels = [], {}
    for k, saved in tree["labels_by_k"].items():
        if k == 1:
            continue
        rows.append({"n_clusters": k, "linkage": linkage, "metric": metric})
        labels[f"n_clusters={k},linkage={linkage},metric={metric}"] = saved
        rows.append({"n_clusters": k, "linkage": "average", "metric": "cosine"})
        labels[f"n_clusters={k},linkage=average,metric=cosine"] = np.zeros(len(saved), dtype=int)
    return ClusteringTuningRun(Path("tuning_dir"), method, Path("matrix"), pd.DataFrame(rows), labels)


def test_saved_labels_are_those_of_the_requested_combination_only(tree):
    saved = saved_labels_for(_tuning(tree), "ward", "euclidean")

    assert sorted(saved) == list(range(2, LAST_P + 1))
    assert all(np.array_equal(saved[k], tree["labels_by_k"][k]) for k in saved)


def test_saved_labels_of_a_combination_never_swept_raise(tree):
    with pytest.raises(ValueError, match="linkage=single"):
        saved_labels_for(_tuning(tree), "single", "euclidean")


def test_saved_labels_of_a_non_agglomerative_tuning_raise(tree):
    with pytest.raises(ValueError, match="hdbscan"):
        saved_labels_for(_tuning(tree, method="hdbscan"), "ward", "euclidean")


def test_build_split_tree_follows_the_saved_labels_up_to_the_highest_k(tree):
    saved = saved_labels_for(_tuning(tree), "ward", "euclidean")

    built = build_split_tree(tree["embedding"], "ward", "euclidean", saved)

    assert built.k_max == LAST_P
    assert len(built.members) == LAST_P
    assert set(built.labels_by_k) == set(range(1, LAST_P + 1))
    assert built.saved_ks == tuple(range(2, LAST_P + 1))


def test_build_split_tree_of_a_sweep_with_holes_offers_only_the_swept_k_and_follows_every_split(tree):
    saved = {k: fcluster(tree["Z"], k, "maxclust") for k in (3, 5)}

    built = build_split_tree(tree["embedding"], "ward", "euclidean", saved)

    assert built.saved_ks == (3, 5)
    assert set(built.labels_by_k) == set(range(1, 6))  # 1, 2 and 4 are cuts of the tree


def test_build_split_tree_refuses_a_hole_filled_with_labels_that_are_not_the_tree(tree):
    wrong = fcluster(tree["Z"], 3, "maxclust").copy()
    wrong[0], wrong[-1] = wrong[-1], wrong[0]

    with pytest.raises(ValueError, match="k=3"):
        build_split_tree(tree["embedding"], "ward", "euclidean", {3: wrong, 5: fcluster(tree["Z"], 5, "maxclust")})


def test_build_split_tree_caps_the_leaves_at_the_number_of_colours(tree):
    # 30 saved k on a matrix with few subjects is not needed: only the cap matters, so check it on the arithmetic.
    saved = {k: fcluster(tree["Z"], k, "maxclust") for k in range(2, MAX_LEAVES + 3) if k <= N_SUBJECTS}

    built = build_split_tree(tree["embedding"], "ward", "euclidean", saved)

    assert built.k_max == MAX_LEAVES


def test_build_split_tree_refuses_a_matrix_that_is_not_the_one_clustered(tree):
    saved = saved_labels_for(_tuning(tree), "ward", "euclidean")
    other_matrix = np.random.default_rng(1).normal(size=tree["embedding"].shape)

    with pytest.raises(ValueError, match="does not reproduce"):
        build_split_tree(other_matrix, "ward", "euclidean", saved)


def test_build_split_tree_refuses_labels_of_another_number_of_subjects(tree):
    saved = saved_labels_for(_tuning(tree), "ward", "euclidean")

    with pytest.raises(ValueError, match="subjects"):
        build_split_tree(tree["embedding"][:-1], "ward", "euclidean", saved)


def test_build_split_tree_with_no_saved_labels_raises(tree):
    with pytest.raises(ValueError, match="no saved labels"):
        build_split_tree(tree["embedding"], "ward", "euclidean", {})
