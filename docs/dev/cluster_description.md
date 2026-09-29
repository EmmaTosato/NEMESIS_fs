# Cluster description — technical reference

Audience: developers/agents working on `src/analysis/cluster_description.py` and the "Descrizione del cluster" panel it feeds in `src/analysis/embedding_app.py` (29-09-26). For how the panel looks/behaves from a user's point of view, see `docs/guides/embedding_app.md` ("Descrizione del cluster"). For the anatomy panels (lesion/SDC maps) this one sits alongside, see `docs/dev/anatomical_maps.md` — this panel is deliberately **not** documented there: it never touches a lesion mask or disconnectome file, only `assets/metadata/participants.csv`.

## Why every variable comes from `participants.csv`, never a run's own `metadata.csv`

Two separate reasons, not one:

1. **Age/sex/education/NIHSS are properties of the subject, not of the run** — the same reasoning `src/analysis/embedding_coloring.py`'s own `registry_column` modes (`"side"`, `"nihss"`) already follow. A subject's age doesn't change depending on which `dim_reduction.py`/`clustering.py` run you're looking at.
2. **Lesion volume specifically is *not* read from a run's own `metadata.csv`**, even though `embedding_coloring.py`'s `"volume"` mode can be — a run's own `lesion_volume_voxels` column reflects whichever resample grid (1mm/2mm) that particular `build_lesion_matrix.py` call used, not guaranteed the same across runs (see `docs/dev/lesion_matrix.md`). `participants.csv`'s own `lesion_volume_voxels_2mm` is computed once, on one fixed grid, for every admitted subject (100% coverage as of 29-09-26) — the one source that's comparable across every run this panel could ever be shown for, where "which grid" is a distinction that matters for the overlap-map's own voxel-level display but not for a demographic summary.

## `CLUSTER_DESCRIPTION_VARIABLES: list[ClusterDescriptionVariable]`

A declarative registry, same shape as `embedding_coloring.py`'s own `COLOR_MODES` — deliberately not the same registry (see "Why not extend `COLOR_MODES` instead" below). Each entry: `name` (internal key), `label` (Italian, shown as that variable's subplot title), `kind` (`"continuous"` | `"categorical"`), `registry_column` (the exact `assets/metadata/participants.csv` column).

As of 29-09-26, 5 of the 7 originally-requested dimensions:

| name | registry_column | kind | coverage (5853 stroke subjects, project-wide) |
|---|---|---|---|
| `age` | `age` | continuous | 89.0% |
| `sex` | `sex` | categorical | 88.9% |
| `education` | `education` | continuous | 14.7% |
| `nihss` | `NIHSS` | continuous | 27.1% (0% for UCL-UK — dataset-wide gap, not per-subject) |
| `lesion_volume_voxels` | `lesion_volume_voxels_2mm` | continuous | 100% |

Two requested dimensions are **not** in this list:

- **Istruzione/NIHSS were kept despite low coverage**, on request — never hidden, but always shown next to their own `n_available/n_total` (see `variable_summary` below), since a *per-cluster* coverage can differ wildly from the *project-wide* one (a cluster drawn mostly from one well-NIHSS'd dataset can be 90%+ populated even though the project-wide figure is 27%).
- **Hemorrhagic/ischemic stroke type has no column in `assets/metadata/participants.csv`** as of 29-09-26, so it cannot be registered here yet. The datum itself is *not* missing from the project, only from the registry: `participants_PSP.tsv` carries it per subject in its own `lesion_type` column (189 `ischemic` / 18 `hemorrhagic` / 30 `n/a` of 237). UKLFR states it only cohort-wide (`disease_notes` = `"ischemic stroke"` for all 735), and UKE's `Ischemic_stroke`/`Intracranial_haemorrhage` are **not** this variable — they sit in that file's risk-factor/anamnesis block (alongside `Arterial_hypertension`, `Atrial_fibrillation`, `TIA`) and mean *prior* stroke, not the type of the index event. Surfacing it is `enrich_metadata.py`'s job first (see "Next session"), one `ClusterDescriptionVariable` line here second.

### Why not extend `COLOR_MODES` instead of a new registry

`embedding_coloring.py`'s `COLOR_MODES` drives two other things this feature has nothing to do with: the interactive app's scatter-coloring button row, and `dim_reduction.py`'s own `color_by` production config. Adding `age`/`sex`/`education` there would silently grow *those* surfaces too (a new "color by age" button appearing in the scatter) — not requested, and not this panel's job. `cluster_composition`/`variable_summary` instead call `src.utils.participants.load_participants_registry()` directly, independent of `COLOR_MODES` (only `COLOR_MODES["cluster_label"].column` is reused, for the one thing genuinely shared: which column names the cluster grouping).

## `cluster_composition(metadata, cluster_label) -> tuple[pd.DataFrame, list[str]]`

One registry read + one join (not one per variable) — filters `metadata` to `cluster_label`'s subjects, joins them against `load_participants_registry()` by `subject_id`, returns one row per subject with every `CLUSTER_DESCRIPTION_VARIABLES` entry's raw value (numeric for continuous via `pd.to_numeric(errors="coerce")`, raw string for categorical), plus the sorted list of the cluster's subjects that have **no row at all** in the registry.

Raises `ValueError` only if `cluster_label` has no subjects in `metadata` — an empty cluster has nothing to describe.

### A subject absent from the registry is reported, not fatal

A clustering run legitimately outlives the registry it was built against (subjects added to a run before the next `populate_metadata.py` pass). Refusing to describe a cluster's other ~300 subjects because 13 of them have no registry row is a worse answer than describing them and naming exactly who is missing, so this is a warning path, not a failure.

It is **not** a silent fallback (`code_standards.md` §0) — the gap is surfaced twice: logged at `WARNING` (with the cluster label, the count, and the registry path), and returned to the caller, which the app renders as a visible line above the figure.

Such a subject is **kept as a row** with a missing value for every variable, never dropped, so:

- `variable_summary`'s `n_total` stays the cluster's **true** size,
- the subject is counted as missing exactly once per variable.

Dropping it instead would shrink the reported denominator — precisely what this panel's whole `n_available`/`n_total` contract exists to prevent. Implemented with `registry.reindex(subject_ids)` rather than `.loc[...]`, which is what turns an absent id into a row of `NaN` instead of a `KeyError`.

A subject *with* a registry row but a blank cell for one specific variable is a third, distinct case — `variable_summary`'s ordinary "not available", unrelated to either of the above.

## `variable_summary(composition, variable) -> dict`

`n_total` = the cluster's own size (every row of `composition`), `n_available` = how many of those have a non-missing value for *this* variable specifically — always reported together, never just one. Continuous: `mean`/`median`/`std`/`min`/`max` over the available values (all `None` if `n_available == 0`). Categorical: `counts` (a plain `{category: count}` dict) — an empty-string/NaN cell is excluded from `counts` entirely (missing, not its own category), matching `embedding_coloring.py`'s own `UNKNOWN_CATEGORICAL` philosophy in spirit, though this panel omits missing values from the bar chart rather than giving them a visible "unknown" bar (a design choice, not yet reconsidered — see "Next session").

## `build_cluster_description_figure(composition, cluster_label, color=None) -> go.Figure`

One `plotly.subplots.make_subplots` figure, one subplot per `CLUSTER_DESCRIPTION_VARIABLES` entry, in declared order. Continuous → `go.Box` with `boxpoints="all"` and `boxmean=True` (every subject drawn as a jittered point, informative at real cluster sizes of a few dozen to a few hundred — a bare box hides genuine outliers and small-cluster sparsity). Categorical → `go.Bar` of `variable_summary`'s own `counts`.

### Layout: 3 per row, not 1 row of 5

The 5 variables sat in a single row until 29-09-26 ("così non si capisce niente, con label e assi così piccoli"). At the app's 1100px page width that left each subplot ~200px wide — too narrow for a readable axis, so every tick and title had to be shrunk to fit. `_GRID_COLUMNS = 3` gives ~290px each, which is what pays for the type sizes below. Any unused trailing cell (the 6th, today) has both axes set `visible=False`; an empty *framed* box reads as a subplot whose data failed to load.

| Element | Size |
|---|---|
| Figure title (`**Cluster N** · M soggetti`) | 24, `<b>` on the cluster name |
| Subplot title (variable label) | 17, bold, in the variable's color |
| Coverage line (`n=avail/total`, 2nd line of the subplot title) | 13.5, `_MUTED_COLOR` |
| y-axis ticks | 13 |
| Bar direct labels | 14 |

Sizes were raised across the board on 29-09-26 ("in generale aumenta un po' il font"). The title is pinned to the top (`y=0.975, yanchor="top"`) with `margin.t=170`, so the extra top margin becomes a **gap between the heading and the first row of panels** rather than padding above the heading.

**Coverage sits in the subplot title, not the x-axis title.** As an axis title it rendered lower under the one subplot that has tick labels (the categorical bar chart — its `F`/`M` labels push the title down) than under the box plots, which have none: five coverage figures meant to be scanned together, sitting on two different baselines. In the title they align by construction. Found by rendering the figure and looking at it, not by any numeric check — the geometry assertions all passed; a regression test now guards it.

Height is `_ROW_HEIGHT * n_rows + 110`, i.e. it grows with the grid instead of clipping the x-axis band off a fixed-height container.

### Color

Each **variable** owns a hue (`ClusterDescriptionVariable.color`), carried by its subplot's marks, its subplot title, and its column header in the table below — so a panel and its column read as the same thing without a legend (29-09-26: *"vorrei più varietà nei colori dato che stiamo plottando variabili diverse"*).

| Variable | Color |
|---|---|
| Età | `#1a6bab` navy |
| Sesso | `#d97a29` orange |
| Istruzione | `#7b4fa0` purple |
| NIHSS | `#008300` green |
| Volume lesione | `#b03d68` deep rose |

These are members of `plotting._CATEGORICAL_PALETTE` (a test pins that), but **not its first five and not its order**. Both were chosen by running the `dataviz` validator over candidate subsets: the palette's own first five fail its 3:1 contrast check (the pink and sky slots sit at 2.62 and 2.58 against white — too washed for a 2px box outline), and several orderings fail CVD adjacency. This set passes lightness, chroma, CVD adjacency (worst pair ΔE 8.6 deutan) **and** contrast.

| Mark | Treatment |
|---|---|
| Box outline | the variable's color, 2px |
| Box fill | same color at `_BOX_FILL_ALPHA` (0.13) |
| Points | same color at `_POINT_ALPHA` (0.45), 5px — a few hundred jittered points read as density, not a solid block |
| Bars | same color at `_BAR_FILL_ALPHA` (0.22) with a 2px outline, `width=_BAR_WIDTH` (0.42) |
| Gridlines | `_GRIDLINE_COLOR` `#ececec`, solid — recessive, one shade off the surface; never dashed (a dashed grid reads as a threshold) |

`_rgba()` derives every fill from the variable's single declared color rather than a second hex literal per mark, so the two can't drift apart; it raises on a malformed color instead of emitting an `rgba()` string the browser silently ignores.

**The categorical subplot uses one color for every bar, not one per category.** It is a single series, and its categories are already named by the tick labels and counted by the direct labels above them, so a per-category hue would re-encode what is already unambiguous — and it would make one palette mean two different things in one figure ("which variable" in the box plots, "which category" here). The bars also get the boxes' pale-fill treatment rather than a solid block: two saturated bars at this size read far heavier than the light boxes beside them, and large saturated fills are exactly what the mark rules reserve saturation against.

`color` is the cluster's own color in the embedding scatter (`plotting._palette_for_labels`) and is used **only** for a `■` swatch in the title, never for the marks — inside this figure the categorical palette already means "sex category", and letting the box outlines also carry cluster identity would make one palette mean two different things at once. The swatch sits outside the plotting area, so it ties the panel to the scatter without competing.

Every bar is direct-labeled. With 2–3 categories that is a handful of numbers, not the "a value on every point" clutter the rule warns against — and the palette's lighter slots sit below 3:1 against a white surface, which obliges a visible label rather than making it optional.

Rendered in `embedding_app.py` as a plain `dcc.Graph` with the same minimal `modeBarButtons=[["toImage"]]` config as the main embedding scatter — no custom "Salva HTML"/"Salva PNG" buttons. Those exist on the anatomy panels specifically because `nilearn`'s `view_img` HTML has no built-in static-image export (see `docs/dev/anatomical_maps.md`); a Plotly figure already has one (the camera icon), so duplicating it here would be redundant, not more consistent.

## `clusters_comparison_stats(metadata) -> list[ClusterStats]`

Every cluster of the run, ascending by label, each a `ClusterStats(cluster_label, n_total, n_unregistered, summaries)` where `summaries` maps a variable's `name` to its own `variable_summary` dict (29-09-26, on request: *"statistiche numeriche, più sotto, a confronto tra tutti i vari cluster"*).

Built on `variable_summary` — the **same** function the figure calls, never a parallel reimplementation that could drift from it. A regression test asserts the two agree for the same cluster.

One registry read for the whole table, not one per cluster: `cluster_composition` and this function share the private `_join_registry(subject_ids, registry)`, which takes an already-loaded registry. Re-reading a 5853-row CSV once per cluster on every panel render would be pure waste.

`_join_registry` is deliberately **silent** about unregistered subjects. `cluster_composition` logs their ids (a caller of the single-cluster path may need to chase them down); this function reports the same gap per cluster as a visible `n_unregistered` column instead. Logging inside the shared helper would re-emit the whole set once per cluster on every render, drowning the one line that matters.

Noise (`cluster_label == -1`) is included like any other row rather than filtered: it is a real group of this run's subjects, and seeing how it differs is the point. Naming it as noise is the caller's job.

Raises `ValueError` if `metadata` has no `cluster_label` column at all.

## Panel wiring in `embedding_app.py`

`cluster_description_content_for(metadata, cluster_label) -> html.Div | html.P` — same never-raises contract as every other `*_content_for` function in that module (a `ValueError`, i.e. an empty cluster or a non-clustering run, becomes a status message, never a crashed callback). The panel is always an `html.Div`, holding in order:

1. `_unregistered_subjects_warning` — **only** when some subject is missing from the registry (`.anatomy-warning`, amber);
2. the `dcc.Graph`;
3. `_clusters_comparison_table` — always.

### `_warning_box(message, detail=None)`

Every "partial result" warning on the page goes through one boxed callout (29-09-26: *"warning tipo questo devono essere renderizzati un po' meglio"*): an uppercase vivid **ATTENZIONE** label, then the message in **black** body text, then the long non-prose tail (the subject ids) set apart in `.warning-detail`.

The label/body color split is deliberate. Coloring the whole block would make the information read as decoration and cost it contrast — the label alone is enough to say "this is not routine caption text", which is exactly how the previous thin amber line failed. The box carries a 5px left rule, a soft gradient and a low shadow to lift it off the page.

Shared with the two anatomy panels: `_anatomy_viewer` renders its own `warning` string through the same box, so a data gap looks identical wherever it appears.

`_unregistered_subjects_warning` is a deliberate **sibling** of `_missing_subjects_warning`, not a reuse of it — the two report different gaps and are worded so they can't be confused: `_missing_subjects_warning` means "this subject's lesion/disconnectome file isn't on disk, so it's excluded from that map", while `_unregistered_subjects_warning` means "this subject has no row in `participants.csv`, so it still counts in every `n/total` here but contributes no value".

### The comparison table

One row per cluster, one column per variable, so a variable is read *down a column* across clusters instead of by flipping the dropdown between them.

A **table rather than a second figure**: the request was for the numbers themselves, and a 5-8 cluster × 5 variable grid is past the point where a reader can hold that many color classes apart. It also serves as the table view the figure's fills require for accessibility.

**No bars, no color in the cells.** In-cell data bars were built and then removed on request (29-09-26: *"non voglio quelle righe colorate nella tabella, mi confondono la lettura"*), together with the per-variable colored header underline. The cells are numbers only; the figure above is the visual read, the table is the exact one. What makes the numbers scannable instead is their formatting and size, not added graphics.

| Cell | Content |
|---|---|
| Continuous | `media` (17px, 600) + `± ds` in secondary ink |
| Categorical | counts per category, sorted **by name** so a category keeps the same position in every row |
| Empty | `—` in muted ink, never `nan ± nan` and never a blank that could read as a rendering gap |

`std` is `None` for a single-subject cluster and renders as the mean alone: a standard deviation of one value does not exist, which is a different statement from `0`.

**Numbers are formatted Italian-style** (`_format_number`): `.` groups thousands, `,` is the decimal separator — `5.265,4`, not `5 265.4` (29-09-26: *"i numeri non sono ben scritti, non si capisce molto bene"*). The whole app is in Italian, so English-formatted numbers read as a foreign convention exactly where the eye is scanning fastest. Implemented by swapping Python's own grouped format rather than with `locale`, which is process-global, depends on what is installed on the machine, and would silently change every other number this process formats.

**Coverage (`n_available/n_total`) prints under a value only where that variable is genuinely incomplete** (`_coverage_note`). It used to sit under every cell: 25 near-identical fractions competing with the values they annotated, which is how a coverage note stops being read at all. Printed only when it says something, it is a signal again — and the caption states the rule, so full coverage is never silently assumed.

Hover on a continuous cell gives median/min/max. Tooltips enhance, never gate: the value and the coverage are both readable without hovering.

The `Cluster` column carries a 13px swatch in that cluster's own scatter color (`_palette_for_labels`) — the table's only color, and it encodes identity, nothing else. The selected cluster's row is highlighted (`.selected`). `tabular-nums` throughout, which is the whole reason to read it as a table. The caption is one rule per line with a bold lead-in, not a paragraph.

`ClusterDescriptionVariable.decimals` (default `1`, `0` for the voxel count) is declared per variable rather than inferred from the values at render time: a column whose precision changed per row would defeat reading it downwards, and a voxel count with a decimal reads as false precision.

## Next session

### Stroke type (hemorrhagic/ischemic)

The one originally-requested dimension still absent. Order of work, unchanged by anything above:

1. Add it to `enrich_metadata.py`'s `KNOWN_VARIABLES` and to `variables` in `config/pipelines/enrich_metadata.json`, so it is written into `participants.csv`. Only PSP has a canonical per-subject column (`lesion_type`); whether UKLFR's cohort-wide `disease_notes` should be promoted to a per-subject value is a clinical-equivalence judgement, and if taken it belongs in `VARIABLE_SOURCE_OVERRIDES` where every such assumption is already logged and reported, never inferred from a similar-looking name.
2. **Only then** add one `ClusterDescriptionVariable` entry (`kind="categorical"`) to `CLUSTER_DESCRIPTION_VARIABLES`. Nothing else in this module or in `embedding_app.py`'s wiring changes, by design.
3. Re-run `pytest tests/unit/test_cluster_description.py tests/unit/test_embedding_app.py -v` and report the exact count (`code_standards.md` §4).

Coverage caveat: on today's registry population that variable would sit at ~2.9% (168/5853 subjects, PSP only) — below `education`'s 14.7%. The panel handles it correctly either way (`n_available/n_total` is shown per variable), but it is worth deciding deliberately whether a 6th subplot that is empty for 97% of clusters earns its width.

### Deferred design choices

Worth revisiting once richer real data is in hand:

- whether a missing categorical value (e.g. `sex`) should get its own visible "unknown" bar instead of being excluded from `counts` — note this now interacts with the unregistered-subject path above, since such a subject is missing for *every* variable at once;
- whether `education`/`NIHSS` coverage has improved enough to settle the earlier sparsity concern.

### Registry coverage

Improved coverage of the 5 registered variables needs **no code change here** — every stat and plot already reports `n_available/n_total` rather than assuming full coverage. Likewise, subjects newly added to `participants.csv` simply stop appearing in the unregistered-subjects warning; nothing in this module is keyed to a fixed population.
