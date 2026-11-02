"""What every callback of the Embedding Explorer needs besides the values of the components:
the runs, the two anatomy configs, the stores that read images off disk, and the memos of
whatever is too slow to recompute on a click.

Built once per app (`AppContext.build`) and passed explicitly, never a module-level global
(code_standards.md section 1) - so the memos are shared by every callback of one app and by
nothing else: two apps in one process do not see each other's.

Frozen, so no field can be rebound after the app is built. The memo dicts are mutable by
design, which is what makes them memos; what the dataclass guarantees is that a callback
cannot swap one for another.

What is NOT here: anything that raises a Dash exception. A guard that answers "this value is
left over from the run shown before, do nothing" belongs to the callback that reads the
component, not to the object holding the data.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import nibabel as nib
import numpy as np
import pandas as pd
from dash import html
from nilearn.plotting.html_stat_map import StatMapView

from src.analysis.anatomical_maps import BinaryMaskStore, DiscoveredFiles
from src.analysis.clustering_evaluation import AdpSummary, SilhouetteBreakdown, SoftMembership
from src.analysis.component_maps import ComponentMapStore
from src.analysis.dendrogram_splits import SplitTree
from src.analysis.embedding_app.anatomy import (
    DEFAULT_DISCONNECTION_MAP_MODE,
    DISCONNECTION_PERCENT_MODE,
    DISCONNECTION_PROBABILITY_THRESHOLD,
    _ANATOMY_VIEWER_WIDTH,
    LesionViewerConfig,
    SdcViewerConfig,
    _build_cluster_disconnection_view,
    _build_cluster_overlap_view,
)
from src.analysis.embedding_app.panels.dendrogram import build_run_split_tree, run_compatible_tunings
from src.analysis.embedding_app.panels.pca_maps import ComponentMapData, _build_component_map_view, run_component_maps
from src.analysis.embedding_app.panels.quality import run_adp_summary, run_silhouette_samples, run_soft_membership
from src.analysis.embedding_app.picker import IndexedRun, index_runs
from src.analysis.embedding_app.runs import ProductionRun, UndisplayableRunError, load_run
from src.analysis.raw_distances import RawDistanceStore
from src.analysis.tuning_match import TuningMatch

AnatomyView = tuple[StatMapView, int, nib.Nifti1Image, list[str]]


@dataclass(frozen=True)
class AppContext:
    """The runs and the stores of one app, plus its memos. See the module docstring."""

    runs_by_key: dict[str, ProductionRun]
    indexed_runs: list[IndexedRun]
    lesion_cfg: LesionViewerConfig
    sdc_cfg: SdcViewerConfig
    lesion_store: BinaryMaskStore
    disconnection_store: BinaryMaskStore
    discovered_files: DiscoveredFiles
    raw_distance_store: RawDistanceStore
    component_map_store: ComponentMapStore

    # One memo per thing that is slow enough to be worth keeping, each keyed by everything the
    # result depends on. A failed build is never stored, so a transient or fixable problem can
    # be retried on the next click.
    cluster_views: dict[tuple[str, int, int], AnatomyView] = field(default_factory=dict)
    disconnection_views: dict[tuple[str, int, str, int], AnatomyView] = field(default_factory=dict)
    dendrogram_views: dict[tuple, AnatomyView] = field(default_factory=dict)
    representatives: dict[tuple[str, int], html.Div] = field(default_factory=dict)
    silhouettes: dict[str, SilhouetteBreakdown] = field(default_factory=dict)
    soft_memberships: dict[str, SoftMembership] = field(default_factory=dict)
    adp_summaries: dict[str, AdpSummary] = field(default_factory=dict)
    tunings_of_run: dict[str, list[TuningMatch]] = field(default_factory=dict)
    split_trees: dict[tuple[str, str], SplitTree] = field(default_factory=dict)
    component_maps_of_run: dict[str, ComponentMapData] = field(default_factory=dict)
    component_views: dict[tuple[str, int], tuple[StatMapView, float]] = field(default_factory=dict)

    @classmethod
    def build(
        cls,
        runs: list[ProductionRun],
        lesion_cfg: LesionViewerConfig,
        sdc_cfg: SdcViewerConfig,
        clustering_params_file: str | Path,
        cache_dir: str | Path,
    ) -> AppContext:
        """Reads what is fixed for the life of the app: the runs' own selector values, and the
        stores whose on-disk cache outlives the process. Raises ValueError if no run has
        readable params (index_runs), because a picker offering nothing is a broken start."""
        cache_root = Path(cache_dir)
        return cls(
            runs_by_key={run.key: run for run in runs},
            # Each run's value at every filter selector, read once here and not on every click.
            indexed_runs=index_runs(runs, clustering_params_file),
            lesion_cfg=lesion_cfg,
            sdc_cfg=sdc_cfg,
            # Per-subject "voxels above threshold" memos shared by every run and cluster of this
            # app, kept on disk too so they survive a restart - see BinaryMaskStore.
            lesion_store=BinaryMaskStore(
                lesion_cfg.reference_img, lesion_cfg.resample_interpolation, lesion_cfg.binarize_threshold,
                cache_dir=cache_root / "binary_masks",
            ),
            disconnection_store=BinaryMaskStore(
                sdc_cfg.reference_img, sdc_cfg.resample_interpolation, DISCONNECTION_PROBABILITY_THRESHOLD,
                cache_dir=cache_root / "binary_masks",
            ),
            # Which files each dataset holds: found once per app, shared by every per-cluster map and the preload.
            discovered_files=DiscoveredFiles(),
            raw_distance_store=RawDistanceStore(cache_root / "raw_distances"),
            component_map_store=ComponentMapStore(cache_root / "component_maps"),
        )

    # --- The anatomy maps of a cluster ---------------------------------------------------

    def cluster_overlap_view(
        self,
        run: ProductionRun,
        metadata: pd.DataFrame,
        cluster_label: int,
        lesion_cfg: LesionViewerConfig,
        width_view: int = _ANATOMY_VIEWER_WIDTH,
    ) -> AnatomyView:
        """The lesion-overlap map of one cluster, built once.

        About 40 ms per subject to load and resample, which dominates the panel's response time
        for a real several-hundred-subject cluster - so coming back to a cluster already seen,
        or saving it after looking at it, is instant instead of reading every mask again.

        `lesion_cfg` is a parameter and not read from `self` because the panel builders declare
        this shape for their own `build_view` (see overlap_map_content_for): they are given the
        config and hand it on. The width is part of the key - the same cluster is drawn big in
        its own panel and smaller in the overview of all of them."""
        key = (run.key, cluster_label, width_view)
        if key not in self.cluster_views:
            self.cluster_views[key] = _build_cluster_overlap_view(
                run, metadata, cluster_label, lesion_cfg,
                mask_store=self.lesion_store, discovered=self.discovered_files, width_view=width_view,
            )
        return self.cluster_views[key]

    def cluster_disconnection_view(
        self,
        run: ProductionRun,
        metadata: pd.DataFrame,
        cluster_label: int,
        sdc_cfg: SdcViewerConfig,
        map_mode: str = DEFAULT_DISCONNECTION_MAP_MODE,
        width_view: int = _ANATOMY_VIEWER_WIDTH,
    ) -> AnatomyView:
        """The disconnection map of one cluster, built once - same cost and same reasoning as
        cluster_overlap_view, averaging instead of counting.

        Its own memo, not a shared one: a (run, cluster) pair says nothing about which of the
        two anatomy families produced the entry, so one dict would serve a lesion map for a
        disconnection one. `map_mode` is part of the key for the same reason - the same cluster
        has two different maps, and keying without it would serve whichever was built first."""
        key = (run.key, cluster_label, map_mode, width_view)
        if key not in self.disconnection_views:
            self.disconnection_views[key] = _build_cluster_disconnection_view(
                run, metadata, cluster_label, sdc_cfg, map_mode,
                mask_store=self.disconnection_store, discovered=self.discovered_files, width_view=width_view,
            )
        return self.disconnection_views[key]

    def dendrogram_view(
        self,
        run: ProductionRun,
        metadata_at_k: pd.DataFrame,
        label: int,
        modality: str,
        name: str,
        width: int,
        tuning_dir: Path,
    ) -> AnatomyView:
        """The map of one cluster of one split of the tree.

        Keyed by the cluster's own name - the leaves it holds - and not by k: a cluster that
        survives several splits is the same subjects at each of them, so it is built once per
        map width (the overview draws it smaller than the steps do)."""
        key = (run.key, str(tuning_dir), modality, name, width)
        if key not in self.dendrogram_views:
            if modality == "lesion":
                self.dendrogram_views[key] = _build_cluster_overlap_view(
                    run, metadata_at_k, label, self.lesion_cfg,
                    mask_store=self.lesion_store, discovered=self.discovered_files, width_view=width,
                )
            else:
                self.dendrogram_views[key] = _build_cluster_disconnection_view(
                    run, metadata_at_k, label, self.sdc_cfg, DISCONNECTION_PERCENT_MODE,
                    mask_store=self.disconnection_store, discovered=self.discovered_files, width_view=width,
                )
        return self.dendrogram_views[key]

    # --- The dendrogram's own tuning run -------------------------------------------------

    def compatible_tunings(self, run: ProductionRun) -> list[TuningMatch]:
        """The tuning runs `run`'s own combination can be matched to, looked up once: the runs
        themselves are fixed at startup. Raises ValueError for a run whose params cannot be
        matched at all, and that is not memoised."""
        if run.key not in self.tunings_of_run:
            self.tunings_of_run[run.key] = run_compatible_tunings(run)
        return self.tunings_of_run[run.key]

    def split_tree(self, run: ProductionRun, tuning_dir: Path) -> SplitTree:
        """The tree of `run` as read from `tuning_dir` - seconds, so kept per (run, tuning)."""
        key = (run.key, str(tuning_dir))
        if key not in self.split_trees:
            self.split_trees[key] = build_run_split_tree(run, tuning_dir)
        return self.split_trees[key]

    # --- One run's own numbers -----------------------------------------------------------

    def embedding(self, run: ProductionRun) -> tuple[np.ndarray | None, str | None]:
        """(embedding, None), or (None, why it cannot be drawn): the overview of every cluster
        still draws the maps of a run whose embedding is missing, and says so. Not memoised -
        reading matrix.npy is fast, and every other panel re-reads it too."""
        try:
            embedding, _metadata = load_run(run)
        except UndisplayableRunError as exc:
            return None, str(exc)
        return embedding, None

    def silhouette(self, run: ProductionRun) -> SilhouetteBreakdown:
        """Every subject's silhouette: about a second for a 5845-subject run. A run it is not
        defined for raises ValueError and is not memoised."""
        if run.key not in self.silhouettes:
            self.silhouettes[run.key] = run_silhouette_samples(run)
        return self.silhouettes[run.key]

    def soft_membership(self, run: ProductionRun) -> SoftMembership:
        if run.key not in self.soft_memberships:
            self.soft_memberships[run.key] = run_soft_membership(run)
        return self.soft_memberships[run.key]

    def adp_summary(self, run: ProductionRun) -> AdpSummary | None:
        """Seconds once the distance matrix exists. None means it is still being computed in the
        background, which is not memoised - the next poll has to look again."""
        if run.key not in self.adp_summaries:
            summary = run_adp_summary(run, self.raw_distance_store)
            if summary is None:
                return None
            self.adp_summaries[run.key] = summary
        return self.adp_summaries[run.key]

    # --- The component maps of a PCA run -------------------------------------------------

    def component_maps(self, run: ProductionRun) -> ComponentMapData | None:
        """The maps of every component, memoised once computed - reading the entry back is
        cheap, not free. None (still computing) is not memoised."""
        if run.key not in self.component_maps_of_run:
            data = run_component_maps(run, self.component_map_store)
            if data is None:
                return None
            self.component_maps_of_run[run.key] = data
        return self.component_maps_of_run[run.key]

    def component_view(self, data: ComponentMapData, component: int) -> tuple[StatMapView, float]:
        """The viewer of one component: a second of nilearn, keyed by the maps' identity through
        the run key they were computed for."""
        key = next(run_key for run_key, cached in self.component_maps_of_run.items() if cached is data), component
        if key not in self.component_views:
            self.component_views[key] = _build_component_map_view(data, component)
        return self.component_views[key]
