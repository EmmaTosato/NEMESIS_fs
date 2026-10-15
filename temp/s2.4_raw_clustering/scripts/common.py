"""Shared paths and loaders for the s2.4-vol raw-clustering experiment (everything lives in temp/s2.4_raw_clustering/)."""
from __future__ import annotations

import resource
import sys
import time
from contextlib import contextmanager
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

OUT = REPO / "temp" / "s2.4_raw_clustering"
CACHE, TABLES, IMAGES = OUT / "cache", OUT / "tables", OUT / "images"
MATRIX_DIR = REPO / "data/derived/sdc_matrix/07-10_s2.4-vol"
PARTICIPANTS = REPO / "assets/metadata/participants.csv"
METRICS = ("euclidean", "cosine")

# Usability criteria for a clustering (task brief)
MIN_K, MAX_K, MAX_NOISE, MAX_LARGEST = 3, 30, 0.25, 0.60


def load_subjects() -> pd.DataFrame:
    meta = pd.read_csv(MATRIX_DIR / "metadata.csv")
    if meta["subject_id"].duplicated().any():
        raise ValueError("duplicate subject_id in metadata.csv")
    return meta


def load_participants(subject_ids: pd.Series) -> pd.DataFrame:
    part = pd.read_csv(PARTICIPANTS).set_index("subject_id")
    missing = sorted(set(subject_ids) - set(part.index))
    if missing:
        raise ValueError(f"{len(missing)} subjects of metadata.csv missing from participants.csv, e.g. {missing[:5]}")
    cols = ["lesion_side", "lesion_volume_voxels_2mm", "location_infratentorial_2mm", "disconnection_load_voxels_2mm"]
    return part.loc[subject_ids, cols].reset_index()


def load_distance(metric: str) -> np.ndarray:
    path = CACHE / f"D_{metric}.npy"
    if not path.exists():
        raise FileNotFoundError(f"{path} missing - run scripts/01_distances.py first")
    return np.load(path)


def peak_rss_gb() -> float:
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss  # bytes on macOS
    return rss / 1024**3


@contextmanager
def timed(label: str):
    t0 = time.perf_counter()
    yield
    print(f"[{label}] {time.perf_counter() - t0:.1f}s  peak_rss={peak_rss_gb():.2f} GB", flush=True)
