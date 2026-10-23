"""An agglomerative tree followed k by k: which cluster splits when k-1 becomes k, and where the two pieces sit.

Passing from k-1 to k clusters exactly one cluster splits in two (the highest merge still standing is undone). The
functions here work on the scipy linkage matrix of a stored agglomerative tuning (src/analysis/clustering_tuning.py's
compute_dendrogram_linkage) and on the labels that tuning saved for every k, and build what the Embedding Explorer and
notebooks/post-results_analysis/dendrogram_embedding_explorer.ipynb draw:

- the last `last_p` leaves of the tree, numbered `L1`, `L2`, ... from left to right. Leaves stay the same at every k,
  while the numeric labels of a clustering (0, 1, 2...) change at every k, so a cluster is named by the leaves it holds
  (`L5-L6`): the only name that can be followed from one k to the next;
- a colour per cluster that follows the big cluster: the bigger piece of a split keeps the colour of the cluster it
  came from, the smaller one takes a new one;
- two figures, the tree and the embedding, one colour per cluster in both.

The tree is not stored by the tuning, so it is recomputed; `check_tree_reproduces_labels` is what makes that safe.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass

import numpy as np
import plotly.graph_objects as go
from scipy.cluster.hierarchy import cut_tree, dendrogram, fcluster, to_tree
from sklearn.metrics import adjusted_rand_score

from src.analysis.clustering_tuning import compute_dendrogram_linkage
from src.analysis.clustering_tuning_analysis import AGGLOMERATIVE, SWEPT_COLUMNS, ClusteringTuningRun, combo_key

# One distinct colour per cluster. The first 10 are matplotlib's tab10, the most distinguishable; the rest are only
# needed beyond k=10. 30 colours: the clustering tunings sweep n_clusters up to 30.
PALETTE = (
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",
    "#ffe119", "#000075", "#800000", "#f032e6", "#008080", "#aaffc3", "#e6beff", "#ffd8b1", "#4363d8", "#222222",
    "#e6194b", "#3cb44b", "#42d4f4", "#911eb4", "#9a6324", "#808000", "#fabed4", "#469990", "#a9a9a9", "#fffac8",
)
MAX_LEAVES = len(PALETTE)  # a colour per cluster: with k <= last_p <= MAX_LEAVES none repeats


def leaves_of_truncated_tree(Z: np.ndarray, last_p: int) -> tuple[dict, list[np.ndarray], np.ndarray]:
    """The `last_p` leaves of the truncated dendrogram (last last_p-1 merges), left to right, and the subjects of each.
    Returns (scipy layout to draw it, subjects per leaf, leaf index of every subject). Raises if the leaves do not
    cover every subject exactly once."""
    if last_p > MAX_LEAVES:
        raise ValueError(f"last_p={last_p}: beyond {MAX_LEAVES} there are not enough distinct colours")
    n_subjects = Z.shape[0] + 1
    layout = dendrogram(Z, truncate_mode="lastp", p=last_p, no_plot=True)
    _root, nodes = to_tree(Z, rd=True)
    members = [np.array(nodes[leaf].pre_order()) for leaf in layout["leaves"]]
    leaf_of_subject = np.full(n_subjects, -1)
    for leaf_index, subjects in enumerate(members):
        if (leaf_of_subject[subjects] != -1).any():
            raise ValueError("a subject appears in two leaves")
        leaf_of_subject[subjects] = leaf_index
    if (leaf_of_subject == -1).any():
        raise ValueError("some subjects are in no leaf")
    return layout, members, leaf_of_subject


def cut_height(Z: np.ndarray, cut_k: int) -> float:
    """Height of a horizontal cut giving cut_k clusters: halfway between the last merge kept and the first dropped."""
    return float((Z[-(cut_k - 1), 2] + Z[-cut_k, 2]) / 2)


def single_label(labels: np.ndarray, subjects: np.ndarray, what: str) -> int:
    """The only label present among `subjects`; raises if there is more than one (the group is not a whole cluster)."""
    found = np.unique(labels[subjects])
    if len(found) != 1:
        raise ValueError(f"{what}: the subjects have {len(found)} different labels, not one")
    return int(found[0])


def leaf_name(subjects: np.ndarray, leaf_of_subject: np.ndarray) -> str:
    """Stable name of a group of subjects: the leaves it holds (L5, or L5–L6)."""
    leaves = np.unique(leaf_of_subject[subjects]) + 1
    return f"L{leaves[0]}" if len(leaves) == 1 else f"L{leaves[0]}–L{leaves[-1]}"


def split_at(Z: np.ndarray, k: int, labels_k: np.ndarray, leaf_of_subject: np.ndarray) -> dict:
    """The cluster that splits going from k-1 to k: merge Z[-(k-1)] undone. Returns the merge distance, the cluster of
    k-1 and its two children, each with its leaf name and the label it has in the cut at k (the one the run saved)."""
    row = Z[-(k - 1)]
    _root, nodes = to_tree(Z, rd=True)
    child_members = [np.array(nodes[int(child)].pre_order()) for child in row[:2]]
    parent_members = np.concatenate(child_members)
    return {
        "distance": float(row[2]),
        "parent": {"name": leaf_name(parent_members, leaf_of_subject), "n": len(parent_members), "members": parent_members},
        "children": [
            {"name": leaf_name(members, leaf_of_subject), "label": single_label(labels_k, members, f"k={k}, child"),
             "members": members, "n": len(members)}
            for members in child_members
        ],
    }


def initial_leaf_colors(labels: np.ndarray, leaf_of_subject: np.ndarray, n_leaves: int) -> tuple[np.ndarray, int]:
    """A colour (index into PALETTE) per leaf, one per cluster of `labels`, ordered left to right. Returns the colours
    and the first free index."""
    leaf_color = np.full(n_leaves, -1)
    first_leaf = {lab: leaf_of_subject[labels == lab].min() for lab in np.unique(labels)}
    for color, lab in enumerate(sorted(first_leaf, key=first_leaf.get)):
        leaf_color[np.unique(leaf_of_subject[labels == lab])] = color
    return leaf_color, int(leaf_color.max()) + 1


def recolor_after_split(leaf_color: np.ndarray, split: dict, leaf_of_subject: np.ndarray, next_color: int) -> int:
    """After a split the bigger piece keeps the colour of the cluster it came from and the smaller takes a new one, so
    the colour of the big cluster can be followed from one k to the next. Modifies `leaf_color`, returns the first free
    index."""
    smaller = min(split["children"], key=lambda child: child["n"])
    leaf_color[np.unique(leaf_of_subject[smaller["members"]])] = next_color
    return next_color + 1


def labels_by_k_from(saved: Mapping[int, np.ndarray], k_max: int, Z: np.ndarray) -> dict[int, np.ndarray]:
    """The labels of every k from 1 to k_max. The colours of k depend on every split before it, so a k the tuning did
    not sweep (a sweep over 2, 3, 4, 5, 6, 8, 10 has holes) is the cut of the tree `Z` into k clusters: the tree is
    what the saved labels are verified against (check_tree_reproduces_labels), so the cut is the one the tuning would
    have saved. The labels a tuning did save are kept as they are. Raises if a saved labelling does not cover the
    subjects of `Z`."""
    n_subjects = Z.shape[0] + 1
    wrong = {k: len(labels) for k, labels in saved.items() if len(labels) != n_subjects}
    if wrong:
        raise ValueError(f"the tree has {n_subjects} subjects, the saved labels of k={sorted(wrong)} have {sorted(set(wrong.values()))}")
    return {
        k: np.asarray(saved[k]) if k in saved else cut_tree(Z, n_clusters=k).ravel() for k in range(1, k_max + 1)
    }


def check_tree_reproduces_labels(
    Z: np.ndarray, labels_by_k: Mapping[int, np.ndarray], members: list[np.ndarray], saved_ks: Iterable[int]
) -> None:
    """Raises ValueError unless cutting the recomputed tree at k gives exactly the labels the run saved for k (adjusted
    Rand index 1.0) for every k in `saved_ks`, and no leaf is cut in two at any k from 2 to the last (the k the run
    did not sweep are cuts of this same tree, so only their leaves are checked). The tree is not stored by the run, so
    this is what shows it is the tree the run's labels came from: a tuning rewritten later, or a matrix that is not
    the one clustered, fails here instead of drawing splits that never happened."""
    k_max = max(labels_by_k)
    for k in saved_ks:
        ari = adjusted_rand_score(labels_by_k[k], fcluster(Z, k, "maxclust"))
        if ari != 1.0:
            raise ValueError(f"k={k}: the recomputed tree does not reproduce the saved labels (ARI={ari:.4f})")
    for k in range(2, k_max + 1):
        for leaf_index, subjects in enumerate(members):
            single_label(labels_by_k[k], subjects, f"k={k}, leaf L{leaf_index + 1}")


def replay_splits(
    Z: np.ndarray, labels_by_k: Mapping[int, np.ndarray], leaf_of_subject: np.ndarray, n_leaves: int, k_last: int
) -> list[tuple[int, np.ndarray, dict]]:
    """Every split from k=2 to `k_last`, replayed in order: (k, leaf colours at k, split k-1 -> k). The colour of a
    cluster depends on the history that led to it, so the colours of k cannot be had without the splits before it.
    Raises ValueError for k_last < 2."""
    if k_last < 2:
        raise ValueError(f"k={k_last}: the first split is k=2")
    leaf_color, next_color = initial_leaf_colors(labels_by_k[1], leaf_of_subject, n_leaves)
    steps = []
    for k in range(2, k_last + 1):
        split = split_at(Z, k, labels_by_k[k], leaf_of_subject)
        next_color = recolor_after_split(leaf_color, split, leaf_of_subject, next_color)
        steps.append((k, leaf_color.copy(), split))
    return steps


def colors_at(
    Z: np.ndarray, labels_by_k: Mapping[int, np.ndarray], leaf_of_subject: np.ndarray, n_leaves: int, k: int
) -> tuple[np.ndarray, dict]:
    """The leaf colours at k and the split k-1 -> k (the last of replay_splits). Raises ValueError for k < 2."""
    _k, leaf_color, split = replay_splits(Z, labels_by_k, leaf_of_subject, n_leaves, k)[-1]
    return leaf_color, split


@dataclass(frozen=True)
class SplitTree:
    """What is computed once per (matrix, tuning, linkage, metric) and reused at every k: the linkage matrix, the
    truncated tree's leaves, the labels of every k from 1 (one cluster) to `k_max` and which of those k the tuning
    swept (`saved_ks`, the ones worth offering: the others are in between, to follow the splits)."""

    Z: np.ndarray
    layout: dict
    members: list[np.ndarray]
    leaf_of_subject: np.ndarray
    labels_by_k: dict[int, np.ndarray]
    saved_ks: tuple[int, ...]

    @property
    def k_max(self) -> int:
        return max(self.labels_by_k)


def saved_labels_for(tuning: ClusteringTuningRun, linkage: str, metric: str) -> dict[int, np.ndarray]:
    """The labels `tuning` saved for every n_clusters of the combination (`linkage`, `metric`), keyed by n_clusters.
    Raises ValueError if the tuning is not an agglomerative one or never swept that combination."""
    if tuning.method != AGGLOMERATIVE:
        raise ValueError(f"{tuning.run_dir}: method is {tuning.method!r}, expected {AGGLOMERATIVE!r}")
    columns = SWEPT_COLUMNS[AGGLOMERATIVE]
    rows = tuning.results[(tuning.results["linkage"] == linkage) & (tuning.results["metric"] == metric)]
    if rows.empty:
        raise ValueError(f"{tuning.run_dir}: the tuning never swept linkage={linkage}, metric={metric}")
    return {int(row["n_clusters"]): tuning.labels[combo_key(row, columns)] for row in rows.to_dict("records")}


def build_split_tree(X: np.ndarray, linkage: str, metric: str, saved: Mapping[int, np.ndarray]) -> SplitTree:
    """The tree of `X` (the matrix the run clustered) for (`linkage`, `metric`), with the labels the tuning saved. The
    tree has `min(MAX_LEAVES, highest saved k)` leaves. Raises ValueError when X and the labels disagree on the number
    of subjects, when no k from 2 is saved, or when the recomputed tree does not reproduce the saved labels
    (check_tree_reproduces_labels)."""
    saved_ks = tuple(sorted(k for k in saved if k >= 2))
    if not saved_ks:
        raise ValueError("no saved labels: nothing to follow")
    k_max = min(MAX_LEAVES, saved_ks[-1])
    for k, labels in saved.items():
        if len(labels) != len(X):
            raise ValueError(f"the matrix has {len(X)} subjects, the saved labels of k={k} {len(labels)}")
    Z = compute_dendrogram_linkage(X, {"linkage": linkage, "metric": metric})
    labels_by_k = labels_by_k_from({k: saved[k] for k in saved_ks if k <= k_max}, k_max, Z)
    layout, members, leaf_of_subject = leaves_of_truncated_tree(Z, k_max)
    check_tree_reproduces_labels(Z, labels_by_k, members, [k for k in saved_ks if k <= k_max])
    return SplitTree(
        Z=Z, layout=layout, members=members, leaf_of_subject=leaf_of_subject, labels_by_k=labels_by_k,
        saved_ks=tuple(k for k in saved_ks if k <= k_max),
    )


_FONT = {"family": "system-ui, -apple-system, sans-serif", "size": 14}


def build_tree_figure(
    Z: np.ndarray, layout: dict, members: list[np.ndarray], leaf_color: np.ndarray, cut_k: int, height: int = 380
) -> go.Figure:
    """The tree truncated to its leaves (`L1`, `L2`, ... from the left), each leaf a square of the colour of the
    cluster of the cut at `cut_k` it belongs to, and a red dashed line at that cut. A figure of its own, not a subplot
    next to the embedding: two subplots in one figure shared the margins and their axis titles overlapped."""
    xs: list[float | None] = []
    ys: list[float | None] = []
    for segment_x, segment_y in zip(layout["icoord"], layout["dcoord"]):
        xs += [*segment_x, None]
        ys += [*segment_y, None]
    n_leaves = len(members)
    leaf_x = [5 + 10 * i for i in range(n_leaves)]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line={"color": "#595959", "width": 1}, hoverinfo="skip"))
    fig.add_trace(
        go.Scatter(
            x=leaf_x, y=[0] * n_leaves, mode="markers",
            marker={"symbol": "square", "size": 11, "color": [PALETTE[leaf_color[i]] for i in range(n_leaves)]},
            hovertext=[f"L{i + 1}: {len(m)} subjects" for i, m in enumerate(members)], hoverinfo="text",
        )
    )
    fig.add_hline(
        y=cut_height(Z, cut_k), line={"color": "red", "dash": "dash", "width": 1},
        annotation_text=f"cut k={cut_k}", annotation_position="top left", annotation_font={"color": "red", "size": 13},
    )
    fig.update_xaxes(
        tickmode="array", tickvals=leaf_x, ticktext=[f"L{i + 1}" for i in range(n_leaves)], tickangle=-90,
        tickfont={"size": 12}, title_text="leaf", title_standoff=6, showgrid=False, zeroline=False,
    )
    fig.update_yaxes(title_text="merge distance", title_standoff=6, zeroline=False)
    fig.update_layout(
        height=height, template="plotly_white", showlegend=False, font=_FONT, margin={"l": 64, "r": 12, "t": 24, "b": 64},
        title={"text": "Tree (last merges)", "x": 0.5, "y": 0.98, "font": {"size": 16}},
    )
    return fig


def build_step_embedding_figure(
    embedding: np.ndarray,
    labels_k: np.ndarray,
    leaf_color: np.ndarray,
    leaf_of_subject: np.ndarray,
    highlighted: set[int],
    note: str,
    height: int = 440,
) -> go.Figure:
    """The embedding of the cut `labels_k`, one colour per cluster (the colour of its leaves in the tree), the name of
    each at its median on a white label. No legend: it grows with k. The names of the `highlighted` clusters (the ones
    that divide) are bigger and bold; `note` is said in the title. `embedding` must have 2 columns: a 3-component
    embedding is not sliced."""
    if embedding.ndim != 2 or embedding.shape[1] != 2:
        raise ValueError(f"the embedding has shape {embedding.shape}: only 2 components can be drawn, never a slice of more")
    cut_k = len(np.unique(labels_k))
    fig = go.Figure()
    first_leaf = {lab: leaf_of_subject[labels_k == lab].min() for lab in np.unique(labels_k)}
    for lab in sorted(first_leaf, key=first_leaf.get):
        subjects = np.flatnonzero(labels_k == lab)
        color = PALETTE[single_label(leaf_color[leaf_of_subject], subjects, f"cluster {lab}, colour")]
        name = leaf_name(subjects, leaf_of_subject)
        bold = lab in highlighted
        fig.add_trace(  # SVG on purpose: a page of many Scattergl graphs runs out of WebGL contexts
            go.Scatter(
                x=embedding[subjects, 0], y=embedding[subjects, 1], mode="markers", marker={"size": 4, "color": color},
                hovertemplate=f"{name} (n={len(subjects)})<extra></extra>",
            )
        )
        centre = np.median(embedding[subjects], axis=0)
        fig.add_annotation(  # a label with its own background: points drawn under a plain text trace hide it
            x=centre[0], y=centre[1], text=f"<b>{name}</b>" if bold else name, showarrow=False,
            bgcolor="rgba(255,255,255,0.9)", bordercolor=color, borderwidth=2 if bold else 1, borderpad=3 if bold else 2,
            font={"size": 18 if bold else 12, "color": "#222"},
        )
    fig.update_xaxes(title_text="dim 1", title_standoff=6, zeroline=False)
    fig.update_yaxes(title_text="dim 2", title_standoff=6, zeroline=False)
    fig.update_layout(
        height=height, template="plotly_white", showlegend=False, font=_FONT, margin={"l": 56, "r": 12, "t": 36, "b": 48},
        title={"text": f"Embedding, {cut_k} clusters" + (f" ({note})" if note else ""), "x": 0.5, "y": 0.97, "font": {"size": 16}},
    )
    return fig
