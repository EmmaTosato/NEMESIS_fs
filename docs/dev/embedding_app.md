# Embedding Explorer — architecture reference

Audience: developers/agents working on `src/analysis/embedding_app/`. For how the app looks and what each panel shows, see `docs/guides/embedding_app.md` — this file does not repeat it. For what the panels compute, see the technical reference of each: `docs/dev/anatomical_maps.md`, `cluster_description.md`, `cluster_composition.md`, `cluster_comparison.md`, `models.md` (the dendrogram and the overview of every cluster).

The app is one Dash page served by `src/pipeline/embedding_app.py`. The logic is a package of one module per piece, which is what makes a panel readable on its own: anything a panel needs from another is an import, not a line further down the same file.

## The layers

Every module depends only on the ones above it in this list.

| Module | What it is |
|---|---|
| `style.py` | The design tokens, the page's CSS, the HTML skeleton, and the number format every figure is given. Imports nothing from its siblings |
| `blocks.py` | The small page pieces more than one panel is built from: a warning callout, the sentence for subjects left out of a map, a table of numbers, the background-poll interval |
| `runs.py` | Finding the production runs under `results/` and reading one: its matrix, metadata and params, or why it cannot be displayed |
| `picker.py` | The ten cascading selectors that narrow the runs down to the one on screen |
| `embedding_view.py` | The scatter of one run: the colours it can be read by, the figure, the cluster centroids drawn on it, the graph area |
| `anatomy.py` | One subject's lesion or disconnectome: resolving the image, putting it on the panel's grid, rendering it interactively or as a PNG |
| `tabs.py` | Which tab a section sits in, which sections a run has at all, and the index |
| `panels/*.py` | One module per panel of the page (see below) |
| `context.py` | `AppContext`: the runs, the two anatomy configs, the on-disk stores and the memos of what is too slow to recompute on a click |
| `__init__.py` | `build_app`: the Dash object, the controls, the layout, and one call to each panel's `register_callbacks` |

`panels/` holds `description.py` (who the subjects of a cluster are), `cluster_maps.py` (the maps of a whole cluster and its representative subject), `overview.py` (every cluster side by side), `quality.py` (silhouette, density, ADP, the saved model), `pca_maps.py` (the brain map of each component of a PCA run), `dendrogram.py` (the walk down an agglomerative tree), and `comparison.py`/`cluster_pair.py` (the parked "Confronto" section — built and tested, not mounted, `code_standards.md` §2).

## What a panel module looks like

Two functions with the same shape in every panel:

- `layout() -> html.Div` — the components of the panel. `build_app` places it by calling it; the panel does not know where on the page it goes.
- `register_callbacks(app: Dash, context: AppContext) -> None` — its callbacks. `build_app` calls it once.

Plus whatever that panel computes, as plain functions of a run — directly testable without Dash, which is how most of the suite tests the panels.

## Two rules that are not obvious

**`AppContext` is imported under `TYPE_CHECKING`.** A panel needs the type for its `register_callbacks` signature, but importing it for real closes a loop: `context.py` imports the panels (it builds what they memoise), so a panel importing `context.py` back would be circular. Under `from __future__ import annotations` the annotation is never evaluated, so the import can stay inside `if TYPE_CHECKING:`.

**`ctx` means Dash's callback context, never the app's.** `from dash import ctx` is in several of these modules and `ctx.triggered_id` is how a callback knows which input fired. The app's own context is `context` (the parameter) or `app_ctx`; naming it `ctx` shadows Dash's and the failure is an `AttributeError` far from the cause.

## What holds the structure in place

`tests/unit/embedding_app_contract.py` pins every callback — what it writes, what fires it, what it reads without firing — and every component id the layout has, as generated literals; `test_embedding_app_contract.py` rebuilds the app and compares. This exists because the app is built with `suppress_callback_exceptions=True`: a callback wired to an id that no longer exists simply never fires, and nothing says so. Moving a callback or a panel between modules must leave those literals untouched. When the wiring is meant to change, regenerate them in the same commit:

```bash
PYTHONPATH=. python -m tests.unit.embedding_app_contract
```

A callback body is fired in a test through `tests/unit/embedding_app_callbacks.py` (`fire`/`fire_one`), which posts the request the browser itself would — the only faithful way to run one, since Dash's wrapper needs a request context.
