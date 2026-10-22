# Cluster composition — technical reference

Audience: developers/agents working on `src/analysis/cluster_composition.py` and the "Cluster composition" panel it feeds in `src/analysis/embedding_app.py`. For how the panel looks from a user's point of view, see `docs/guides/embedding_app.md`. Its sibling for one chosen cluster is `docs/dev/cluster_description.md`.

## What it is

Where `cluster_description.py` describes the cluster picked in the dropdown, this module compares **every cluster of a run at once**: one plot per variable, one bar or box per cluster. The panel does not depend on the cluster picker, so its callback listens to the run picker only.

## `COMPOSITION_VARIABLES: list[CompositionVariable]`

Declarative registry (same idea as `CLUSTER_DESCRIPTION_VARIABLES`): adding a variable is one line.

| Name | Kind | Registry column | Notes |
|---|---|---|---|
| `dataset` | categorical | `dataset` | categories sorted |
| `lesion_side` | categorical | `lesion_side` | closed order left, right, both |
| `location_dominant` | categorical | `location_dominant_2mm` | categories sorted |
| `nihss` | continuous | `NIHSS` | |
| `lesion_volume` | continuous | `lesion_volume_voxels_2mm` | log axis |
| `disconnection_load` | continuous | `disconnection_load_voxels_2mm` | |

Every column is read from `assets/metadata/participants.csv`, never from a run's own `metadata.csv`, for the reasons in `docs/dev/cluster_description.md`.

## `composition_frame(metadata) -> (frame, unregistered)`

One row per subject of the run with its `cluster_label` and every variable. A subject with no registry row stays in the frame with missing values, is returned in `unregistered`, and is logged at WARNING, so each variable's `n_total` is the run's true size. Raises `ValueError` if `metadata` has no cluster labels, or if the registry lacks a column a variable needs (the message points to `enrich_metadata.py`).

## `build_composition_figure(frame, variable) -> go.Figure`

- Categorical: horizontal bars, `barnorm="percent"`, one trace per category, so each cluster sums to 100%. A value outside a closed `category_order` raises instead of being drawn in a surprise color.
- Continuous: one `go.Box` per cluster, in the cluster's scatter color (`cluster_colors`, the same `_palette_for_labels` the embedding uses; noise `-1` is gray).
- The subtitle `n=available/total` always says how many subjects the plot is built on.
- Backgrounds are transparent (the app page is white). A notebook with a dark theme overrides `paper_bgcolor`/`plot_bgcolor`.

## Panel wiring

`cluster_composition_content_for(metadata)` returns an `html.Div` with a CSS grid (`.composition-grid`, 440px minimum column) of one `dcc.Graph` per variable, plus an `_unregistered_subjects_warning` line when needed, or an `html.P` status message on `ValueError` (the same never-raises-into-the-callback contract as every other panel). Its visibility is the 7th output of `_update_cluster_picker`: shown for a clustering run, hidden otherwise.
