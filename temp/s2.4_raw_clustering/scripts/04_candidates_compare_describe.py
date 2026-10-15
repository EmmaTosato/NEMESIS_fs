"""Candidates (explicit selection rule), ARI vs. the existing UMAP/ADP runs, descriptive cluster profile."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score

from common import CACHE, REPO, TABLES, load_participants, load_subjects

RESULTS = REPO / "results/sdc/clustering/tuning"
REFERENCES = {
    "umap_hdbscan_nc2": RESULTS / "hdbscan/umap/09-10_s2.4-vol_m_euclidean_nc2",
    "umap_hdbscan_nc10": RESULTS / "hdbscan/umap/09-10_s2.4-vol_m_euclidean_nc10",
    "umap_agglomerative_nc2": RESULTS / "agglomerative/umap/09-10_s2.4-vol_m_euclidean_nc2",
    "umap_agglomerative_nc10": RESULTS / "agglomerative/umap/09-10_s2.4-vol_m_euclidean_nc10",
    "adp_raw": RESULTS / "adp/raw/08-10_s2.4-vol",
}


def select_candidates() -> pd.DataFrame:
    """Rule, no hand-picking. Agglomerative (only partitions whose smallest cluster is >= 1%): per linkage/metric the k
    with best silhouette (k>=3), best silhouette with k>=4, and best dendrogram gap. HDBSCAN: per metric the grid
    point violating the fewest usability criteria (ties: lowest noise) - labelled 'least bad', not usable."""
    cands = []
    agg = pd.read_csv(TABLES / "agglomerative_k.csv")
    for (linkage, metric), g in agg[agg["min_size_ok"]].groupby(["linkage", "metric"], sort=False):
        picks = {"best_silhouette": g.loc[g["silhouette"].idxmax()], "best_silhouette_k>=4": None if (g["k"] >= 4).sum() == 0 else g[g["k"] >= 4].loc[lambda x: x["silhouette"].idxmax()], "best_gap": g.loc[g["gap"].idxmax()]}
        for rule, row in picks.items():
            if row is not None:
                cands.append({"method": "agglomerative", "metric": metric, "param": f"linkage={linkage},k={int(row['k'])}", "rule": rule, "key": f"linkage={linkage},metric={metric},k={int(row['k'])}", "silhouette": row["silhouette"]})
    hdb = pd.read_csv(TABLES / "hdbscan_grid.csv")
    hdb["violations"] = (hdb["n_clusters"] < 3).astype(int) + (hdb["n_clusters"] > 30) + (hdb["noise_share"] > 0.25) + (hdb["largest_share"] > 0.60)
    for metric, g in hdb.groupby("metric", sort=False):
        row = g.sort_values(["violations", "noise_share"]).iloc[0]
        cands.append({"method": "hdbscan", "metric": metric, "param": f"mcs={row['min_cluster_size']},ms={row['min_samples']}", "rule": f"least_bad({int(row['violations'])} criteria violated)", "key": f"metric={metric},min_cluster_size={row['min_cluster_size']},min_samples={row['min_samples']}", "silhouette": row["silhouette_nonnoise"]})
    df = pd.DataFrame(cands).drop_duplicates(subset=["method", "key"]).reset_index(drop=True)
    df["name"] = df["method"].str[:4] + "|" + df["metric"].str[:3] + "|" + df["param"]
    return df


def candidate_labels(cands: pd.DataFrame) -> dict[str, np.ndarray]:
    agg, hdb = np.load(CACHE / "agglomerative_partitions.npz"), np.load(CACHE / "hdbscan_partitions.npz")
    return {r["name"]: (agg if r["method"] == "agglomerative" else hdb)[r["key"]] for _, r in cands.iterrows()}


def ari(a: np.ndarray, b: np.ndarray) -> tuple[float, int]:
    """ARI on the subjects that are non-noise (label >= 0) in both partitions; also returns how many."""
    keep = (a >= 0) & (b >= 0)
    if keep.sum() < 2 or len(np.unique(a[keep])) < 2 or len(np.unique(b[keep])) < 2:
        return float("nan"), int(keep.sum())
    return float(adjusted_rand_score(a[keep], b[keep])), int(keep.sum())


def compare(labels: dict[str, np.ndarray], subjects: pd.Series) -> pd.DataFrame:
    rows = []
    for ref_name, path in REFERENCES.items():
        ref_subjects = pd.read_csv(path / "metadata.csv")["subject_id"]
        if not ref_subjects.equals(subjects):
            raise ValueError(f"{ref_name}: subject order differs from the s2.4-vol metadata.csv")
        z = np.load(path / "clusterings.npz")
        for key in z.files:
            ref = z[key]
            if ref.shape != (len(subjects),):
                raise ValueError(f"{ref_name}/{key}: shape {ref.shape}")
            for name, lab in labels.items():
                value, n_used = ari(lab, ref)
                rows.append({"candidate": name, "reference": ref_name, "ref_key": key, "ari": value, "n_compared": n_used, "ref_n_clusters": len(np.unique(ref[ref >= 0]))})
    return pd.DataFrame(rows)


def describe(labels: dict[str, np.ndarray], part: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for name, lab in labels.items():
        frame = part.assign(cluster=lab)
        for cl, g in frame.groupby("cluster"):
            side = g["lesion_side"].value_counts(normalize=False) / max(g["lesion_side"].notna().sum(), 1)  # shares among subjects with a known side
            rows.append({
                "candidate": name, "cluster": "noise" if cl < 0 else int(cl), "n": len(g),
                "left": side.get("left", 0.0), "right": side.get("right", 0.0), "both": side.get("both", 0.0), "side_missing": int(g["lesion_side"].isna().sum()),
                "lesion_volume_median": g["lesion_volume_voxels_2mm"].median(), "infratentorial_share": g["location_infratentorial_2mm"].mean(),
                "disconnection_load_median": g["disconnection_load_voxels_2mm"].median(),
            })
    return pd.DataFrame(rows)


HEADLINE = {  # fixed reference keys (those quoted in the brief), so the comparison does not depend on a max over hundreds of keys
    "umap_hdbscan_nc2": "min_cluster_size=100,min_samples=10", "umap_hdbscan_nc10": "min_cluster_size=100,min_samples=10",
    "umap_agglomerative_nc2": "n_clusters=5,linkage=ward,metric=euclidean", "umap_agglomerative_nc10": "n_clusters=5,linkage=ward,metric=euclidean",
    "adp_raw": "metric=euclidean,Z=3.0",
}


def headline(cmp: pd.DataFrame) -> pd.DataFrame:
    keep = pd.concat([cmp[(cmp["reference"] == r) & (cmp["ref_key"] == k)] for r, k in HEADLINE.items()])
    if len(keep) != len(HEADLINE) * cmp["candidate"].nunique():
        raise ValueError("a headline reference key is missing from the existing runs")
    return keep


def eta_squared(values: np.ndarray, labels: np.ndarray) -> float:
    """Share of the variance of `values` explained by cluster membership (descriptive, not a test); noise is its own group."""
    grand = values.mean()
    between = sum((labels == c).sum() * (values[labels == c].mean() - grand) ** 2 for c in np.unique(labels))
    return float(between / ((values - grand) ** 2).sum())


def structure_summary(labels: dict[str, np.ndarray], part: pd.DataFrame) -> pd.DataFrame:
    log_vol, log_load = np.log10(part["lesion_volume_voxels_2mm"].to_numpy()), np.log10(part["disconnection_load_voxels_2mm"].to_numpy())
    lr = part["lesion_side"].isin(["left", "right"]).to_numpy()
    side = part["lesion_side"].map({"left": 0, "right": 1}).fillna(-1).to_numpy().astype(int)
    rows = []
    for name, lab in labels.items():
        a, n_used = ari(lab[lr], side[lr])
        rows.append({"candidate": name, "n_clusters": len(np.unique(lab[lab >= 0])), "noise_share": float((lab < 0).mean()), "ari_vs_lesion_side(L/R, non-noise)": a, "n_used": n_used, "eta2_log10_volume": eta_squared(log_vol, lab), "eta2_log10_load": eta_squared(log_load, lab)})
    return pd.DataFrame(rows)


def main() -> None:
    meta = load_subjects()
    part = load_participants(meta["subject_id"])
    cands = select_candidates()
    cands.to_csv(TABLES / "candidates.csv", index=False)
    labels = candidate_labels(cands)
    cmp = compare(labels, meta["subject_id"])
    cmp.to_csv(TABLES / "ari_vs_existing_runs_all.csv", index=False)
    best = cmp.loc[cmp.groupby(["candidate", "reference"])["ari"].idxmax()].sort_values(["candidate", "reference"])
    best.to_csv(TABLES / "ari_vs_existing_runs_best.csv", index=False)
    headline(cmp).sort_values(["candidate", "reference"]).to_csv(TABLES / "ari_vs_headline_runs.csv", index=False)
    structure_summary(labels, part).to_csv(TABLES / "structure_summary.csv", index=False)
    desc = describe(labels, part)
    desc.to_csv(TABLES / "cluster_profile.csv", index=False)
    # the descriptive columns are also needed to read the side/volume/load structure at the whole-sample level
    print(cands[["name", "rule", "silhouette"]].to_string())
    print(part.isna().sum().to_string())


if __name__ == "__main__":
    main()
