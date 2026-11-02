"""The Embedding Explorer's wiring, pinned: every callback with what it writes, reads and
watches, and every component id its layout has.

Generated, never edited by hand. A refactor that only moves callbacks or panels between modules
must leave the literals below untouched - that is what makes it a move and not a rewrite. When
the wiring is genuinely meant to change, regenerate them in the same commit as the change, so
the diff says exactly which callback changed and how:

    PYTHONPATH=. python -m tests.unit.embedding_app_contract

tests/unit/test_embedding_app_contract.py builds the same app and compares it against these.
The heavy imports sit inside the functions on purpose: reading the literals must not build a
Dash app.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

# Each entry: the components a callback writes, the ones whose change fires it, and the ones it
# reads without firing on ("id.property"). A pattern-matching id keeps its dict form, as JSON.
CALLBACKS: tuple[dict[str, tuple[str, ...]], ...] = (
    {
        "outputs": ('cluster-composition-content.children',),
        "inputs": (
            'run-picker.value',
            'selected-page-tab.data',
        ),
        "state": (),
    },
    {
        "outputs": ('cluster-description-content.children',),
        "inputs": (
            'cluster-picker.value',
            'run-picker.value',
            'selected-page-tab.data',
        ),
        "state": (),
    },
    {
        "outputs": ('cluster-download.data',),
        "inputs": ('cluster-save-btn.n_clicks',),
        "state": (
            'cluster-picker.value',
            'run-picker.value',
        ),
    },
    {
        "outputs": ('cluster-map-content.children',),
        "inputs": (
            'cluster-picker.value',
            'run-picker.value',
            'selected-page-tab.data',
        ),
        "state": (),
    },
    {
        "outputs": (
            'cluster-picker.options',
            'cluster-picker.value',
            'clustering-section.style',
            'cluster-map-panel.style',
            'representative-subject-panel.style',
            'cluster-description-panel.style',
            'cluster-composition-panel.style',
            'cluster-quality-panel.style',
        ),
        "inputs": ('run-picker.value',),
        "state": (),
    },
    {
        "outputs": ('cluster-png-download.data',),
        "inputs": ('cluster-png-btn.n_clicks',),
        "state": (
            'cluster-picker.value',
            'run-picker.value',
        ),
    },
    {
        "outputs": (
            'cluster-quality-content.children',
            'cluster-quality-poll.disabled',
        ),
        "inputs": (
            'cluster-quality-poll.n_intervals',
            'run-picker.value',
            'selected-page-tab.data',
        ),
        "state": (),
    },
    {
        "outputs": ('color-description.children',),
        "inputs": ('selected-color-mode.data',),
        "state": (),
    },
    {
        "outputs": ('color-grid-row.style',),
        "inputs": ('selected-color-mode.data',),
        "state": (),
    },
    {
        "outputs": (
            'dendrogram-k-picker.options',
            'dendrogram-k-picker.value',
        ),
        "inputs": (
            'dendrogram-tuning-picker.value',
            'run-picker.value',
        ),
        "state": (),
    },
    {
        "outputs": (
            'dendrogram-panel.style',
            'dendrogram-tuning-picker.options',
            'dendrogram-tuning-picker.value',
            'dendrogram-tuning-note.children',
            'dendrogram-map-picker.value',
        ),
        "inputs": ('run-picker.value',),
        "state": (),
    },
    {
        "outputs": ('dendrogram-steps-content.children',),
        "inputs": (
            'dendrogram-k-picker.value',
            'dendrogram-map-picker.value',
            'dendrogram-tuning-picker.value',
            'run-picker.value',
            'selected-page-tab.data',
        ),
        "state": (),
    },
    {
        "outputs": ('disconnection-download.data',),
        "inputs": ('disconnection-save-btn.n_clicks',),
        "state": (
            'cluster-picker.value',
            'run-picker.value',
        ),
    },
    {
        "outputs": ('disconnection-map-content.children',),
        "inputs": (
            'cluster-picker.value',
            'run-picker.value',
            'selected-disconnection-mode.data',
            'selected-page-tab.data',
        ),
        "state": (),
    },
    {
        "outputs": ('disconnection-map-panel.style',),
        "inputs": ('run-picker.value',),
        "state": (),
    },
    {
        "outputs": ('disconnection-png-download.data',),
        "inputs": ('disconnection-png-btn.n_clicks',),
        "state": (
            'cluster-picker.value',
            'run-picker.value',
        ),
    },
    {
        "outputs": ('disconnectome-download.data',),
        "inputs": ('disconnectome-save-btn.n_clicks',),
        "state": (
            'disconnectome-viewer-subject.data',
            'run-picker.value',
        ),
    },
    {
        "outputs": ('disconnectome-glass-png-download.data',),
        "inputs": ('disconnectome-glass-png-btn.n_clicks',),
        "state": (
            'disconnectome-viewer-subject.data',
            'run-picker.value',
        ),
    },
    {
        "outputs": ('disconnectome-panel.style',),
        "inputs": ('run-picker.value',),
        "state": (),
    },
    {
        "outputs": ('disconnectome-png-download.data',),
        "inputs": ('disconnectome-png-btn.n_clicks',),
        "state": (
            'disconnectome-viewer-subject.data',
            'run-picker.value',
        ),
    },
    {
        "outputs": (
            'disconnectome-viewer-content.children',
            'disconnectome-viewer-subject.data',
        ),
        "inputs": (
            'embedding-graph.clickData',
            'run-picker.value',
        ),
        "state": (),
    },
    {
        "outputs": ('graph-area.children',),
        "inputs": (
            'run-picker.value',
            'selected-color-mode.data',
            'selected-grid.data',
        ),
        "state": (),
    },
    {
        "outputs": ('lesion-download.data',),
        "inputs": ('lesion-save-btn.n_clicks',),
        "state": (
            'lesion-viewer-subject.data',
            'run-picker.value',
        ),
    },
    {
        "outputs": ('lesion-glass-png-download.data',),
        "inputs": ('lesion-glass-png-btn.n_clicks',),
        "state": (
            'lesion-viewer-subject.data',
            'run-picker.value',
        ),
    },
    {
        "outputs": ('lesion-png-download.data',),
        "inputs": ('lesion-png-btn.n_clicks',),
        "state": (
            'lesion-viewer-subject.data',
            'run-picker.value',
        ),
    },
    {
        "outputs": (
            'lesion-viewer-content.children',
            'lesion-viewer-subject.data',
        ),
        "inputs": (
            'embedding-graph.clickData',
            'run-picker.value',
        ),
        "state": (),
    },
    {
        "outputs": (
            'modality-picker.options',
            'modality-picker.value',
            'pipeline-picker.options',
            'pipeline-picker.value',
            'method-picker.options',
            'method-picker.value',
            'reduction-picker.options',
            'reduction-picker.value',
            'n-subjects-picker.options',
            'n-subjects-picker.value',
            'metric-picker.options',
            'metric-picker.value',
            'n-components-picker.options',
            'n-components-picker.value',
            'tag-params-picker.options',
            'tag-params-picker.value',
            'tag-params-rest-picker.options',
            'tag-params-rest-picker.value',
            'run-picker.options',
            'run-picker.value',
        ),
        "inputs": (
            'method-picker.value',
            'metric-picker.value',
            'modality-picker.value',
            'n-components-picker.value',
            'n-subjects-picker.value',
            'pipeline-picker.value',
            'reduction-picker.value',
            'reset-pickers-btn.n_clicks',
            'run-picker.value',
            'tag-params-picker.value',
            'tag-params-rest-picker.value',
        ),
        "state": (),
    },
    {
        "outputs": ('page-index-links.children',),
        "inputs": (
            'run-picker.value',
            'selected-page-tab.data',
        ),
        "state": (),
    },
    {
        "outputs": (
            'pca-map-content.children',
            'pca-map-poll.disabled',
        ),
        "inputs": (
            'pca-component-picker.value',
            'pca-map-poll.n_intervals',
            'run-picker.value',
        ),
        "state": (),
    },
    {
        "outputs": (
            'pca-map-panel.style',
            'pca-component-picker.options',
            'pca-component-picker.value',
        ),
        "inputs": ('run-picker.value',),
        "state": (),
    },
    {
        "outputs": ('reduction-picker-field.style',),
        "inputs": ('pipeline-picker.value',),
        "state": (),
    },
    {
        "outputs": ('representative-download.data',),
        "inputs": ('representative-save-btn.n_clicks',),
        "state": (
            'cluster-picker.value',
            'run-picker.value',
        ),
    },
    {
        "outputs": ('representative-png-download.data',),
        "inputs": ('representative-png-btn.n_clicks',),
        "state": (
            'cluster-picker.value',
            'run-picker.value',
        ),
    },
    {
        "outputs": ('representative-subject-content.children',),
        "inputs": (
            'cluster-picker.value',
            'run-picker.value',
            'selected-page-tab.data',
        ),
        "state": (),
    },
    {
        "outputs": (
            'run-content.style',
            'no-run-message.style',
        ),
        "inputs": ('run-picker.value',),
        "state": (),
    },
    {
        "outputs": ('selected-color-mode.data',),
        "inputs": ('{"mode":["ALL"],"type":"color-mode-btn"}.n_clicks',),
        "state": (),
    },
    {
        "outputs": ('selected-disconnection-mode.data',),
        "inputs": ('{"mode":["ALL"],"type":"disconnection-mode-btn"}.n_clicks',),
        "state": (),
    },
    {
        "outputs": ('selected-grid.data',),
        "inputs": ('{"grid":["ALL"],"type":"grid-btn"}.n_clicks',),
        "state": (),
    },
    {
        "outputs": ('selected-page-tab.data',),
        "inputs": (
            'run-picker.value',
            '{"tab":["ALL"],"type":"page-tab-btn"}.n_clicks',
        ),
        "state": ('selected-page-tab.data',),
    },
    {
        "outputs": (
            'tag-params-label.children',
            'tag-params-rest-field.style',
        ),
        "inputs": (
            'method-picker.value',
            'pipeline-picker.value',
        ),
        "state": (),
    },
    {
        "outputs": ('{"grid": "ALL", "type": "grid-btn"}.className',),
        "inputs": ('selected-grid.data',),
        "state": ('{"grid":["ALL"],"type":"grid-btn"}.id',),
    },
    {
        "outputs": ('{"mode": "ALL", "type": "color-mode-btn"}.className',),
        "inputs": ('selected-color-mode.data',),
        "state": ('{"mode":["ALL"],"type":"color-mode-btn"}.id',),
    },
    {
        "outputs": ('{"mode": "ALL", "type": "disconnection-mode-btn"}.className',),
        "inputs": ('selected-disconnection-mode.data',),
        "state": ('{"mode":["ALL"],"type":"disconnection-mode-btn"}.id',),
    },
    {
        "outputs": (
            '{"tab": "ALL", "type": "page-tab-btn"}.className',
            '{"tab": "ALL", "type": "page-tab-btn"}.style',
            'page-tab-bar.style',
            'tab-embedding.style',
            'tab-clustering.style',
            'tab-dendrogram.style',
        ),
        "inputs": (
            'run-picker.value',
            'selected-page-tab.data',
        ),
        "state": ('{"tab":["ALL"],"type":"page-tab-btn"}.id',),
    },
)

LAYOUT_IDS: tuple[str, ...] = (
    'cluster-composition-content',
    'cluster-composition-panel',
    'cluster-description-content',
    'cluster-description-panel',
    'cluster-download',
    'cluster-map-content',
    'cluster-map-panel',
    'cluster-picker',
    'cluster-png-btn',
    'cluster-png-download',
    'cluster-quality-content',
    'cluster-quality-panel',
    'cluster-quality-poll',
    'cluster-save-btn',
    'clustering-section',
    'color-description',
    'color-grid-row',
    'controls-section',
    'dendrogram-k-picker',
    'dendrogram-map-picker',
    'dendrogram-panel',
    'dendrogram-steps-content',
    'dendrogram-tuning-note',
    'dendrogram-tuning-picker',
    'disconnection-download',
    'disconnection-map-content',
    'disconnection-map-panel',
    'disconnection-png-btn',
    'disconnection-png-download',
    'disconnection-save-btn',
    'disconnectome-download',
    'disconnectome-glass-png-btn',
    'disconnectome-glass-png-download',
    'disconnectome-panel',
    'disconnectome-png-btn',
    'disconnectome-png-download',
    'disconnectome-save-btn',
    'disconnectome-viewer-content',
    'disconnectome-viewer-subject',
    'embedding-section',
    'graph-area',
    'lesion-download',
    'lesion-glass-png-btn',
    'lesion-glass-png-download',
    'lesion-panel',
    'lesion-png-btn',
    'lesion-png-download',
    'lesion-save-btn',
    'lesion-viewer-content',
    'lesion-viewer-subject',
    'method-picker',
    'metric-picker',
    'modality-picker',
    'n-components-picker',
    'n-subjects-picker',
    'no-run-message',
    'page-index',
    'page-index-links',
    'page-tab-bar',
    'pca-component-picker',
    'pca-map-content',
    'pca-map-panel',
    'pca-map-poll',
    'pipeline-picker',
    'reduction-picker',
    'reduction-picker-field',
    'representative-download',
    'representative-png-btn',
    'representative-png-download',
    'representative-save-btn',
    'representative-subject-content',
    'representative-subject-panel',
    'reset-pickers-btn',
    'run-content',
    'run-picker',
    'selected-color-mode',
    'selected-disconnection-mode',
    'selected-grid',
    'selected-page-tab',
    'tab-clustering',
    'tab-dendrogram',
    'tab-embedding',
    'tag-params-label',
    'tag-params-picker',
    'tag-params-rest-field',
    'tag-params-rest-picker',
    '{"grid": "1mm", "type": "grid-btn"}',
    '{"grid": "2mm", "type": "grid-btn"}',
    '{"mode": "cluster_label", "type": "color-mode-btn"}',
    '{"mode": "dataset", "type": "color-mode-btn"}',
    '{"mode": "disconnection_load", "type": "color-mode-btn"}',
    '{"mode": "disconnection_mean", "type": "color-mode-btn"}',
    '{"mode": "location", "type": "color-mode-btn"}',
    '{"mode": "mean", "type": "disconnection-mode-btn"}',
    '{"mode": "neutral", "type": "color-mode-btn"}',
    '{"mode": "nihss", "type": "color-mode-btn"}',
    '{"mode": "percent", "type": "disconnection-mode-btn"}',
    '{"mode": "side", "type": "color-mode-btn"}',
    '{"mode": "volume", "type": "color-mode-btn"}',
    '{"tab": "clustering", "type": "page-tab-btn"}',
    '{"tab": "dendrogram", "type": "page-tab-btn"}',
    '{"tab": "embedding", "type": "page-tab-btn"}',
)


def build_fixture_app(tmp_path: Path):
    """The app the literals above describe: four runs covering every (modality, pipeline) pair
    the panels branch on, so a callback that only exists for some runs is still registered."""
    import tests.unit.test_embedding_app as fixtures
    from src.analysis.embedding_app import build_app
    from src.analysis.embedding_app.runs import ProductionRun

    results, data = tmp_path / "results", tmp_path / "data"
    clusters = {"cluster_label": [0, 0, 1, 1]}
    runs = [
        ProductionRun(
            "lesion", "dim_reduction", "umap", "lesion-run",
            fixtures._make_run_dir(results, modality="lesion", run_name="lesion-run"),
        ),
        ProductionRun(
            "sdc", "dim_reduction", "umap", "sdc-dr-run",
            fixtures._make_run_dir(results, modality="sdc", run_name="sdc-dr-run"),
        ),
        ProductionRun(
            "sdc", "clustering", "kmeans", "sdc-cl-run",
            fixtures._make_run_dir(
                results, modality="sdc", pipeline="clustering", run_name="sdc-cl-run",
                extra_metadata=clusters,
            ),
            reduction_method="umap",
        ),
        ProductionRun(
            "lesion", "clustering", "kmeans", "cl-run",
            fixtures._make_run_dir(results, pipeline="clustering", run_name="cl-run", extra_metadata=clusters),
            reduction_method="umap",
        ),
    ]
    return build_app(
        runs, fixtures._lesion_cfg(data), fixtures._sdc_cfg(data),
        fixtures._clustering_params_file(tmp_path), tmp_path / "cache",
    )


def _dep_name(dep) -> str:
    """"id.property" of one callback dependency, however Dash happens to hold it."""
    component_id = dep["id"] if isinstance(dep, dict) else dep.component_id
    prop = dep["property"] if isinstance(dep, dict) else dep.component_property
    if isinstance(component_id, dict):
        component_id = json.dumps({key: str(value) for key, value in sorted(component_id.items())})
    return f"{component_id}.{prop}"


def _outputs_of(output) -> tuple[str, ...]:
    """A callback writes one component or several; Dash stores the two cases differently."""
    if isinstance(output, (list, tuple)):
        return tuple(_dep_name(dep) for dep in output)
    if hasattr(output, "component_id"):
        return (_dep_name(output),)
    return (str(output),)


def _layout_ids(component) -> set[str]:
    """Every id in the static layout tree, walked by hand: Dash's own walker skips the ids of a
    component held inside a plain list."""
    found: set[str] = set()
    stack = [component]
    while stack:
        node = stack.pop()
        if isinstance(node, (list, tuple)):
            stack.extend(node)
            continue
        node_id = getattr(node, "id", None)
        if isinstance(node_id, str):
            found.add(node_id)
        elif isinstance(node_id, dict):
            found.add(json.dumps({key: str(value) for key, value in sorted(node_id.items())}))
        children = getattr(node, "children", None)
        if children is not None:
            stack.append(children)
    return found


def observed(app) -> tuple[tuple[dict[str, tuple[str, ...]], ...], tuple[str, ...]]:
    """`app`'s own wiring in the shape of CALLBACKS/LAYOUT_IDS, ordered so two apps with the
    same wiring compare equal whatever order their callbacks were registered in."""
    callbacks = [
        {
            "outputs": _outputs_of(spec["output"]),
            "inputs": tuple(sorted(_dep_name(dep) for dep in spec["inputs"])),
            "state": tuple(sorted(_dep_name(dep) for dep in spec.get("state", []))),
        }
        for spec in app.callback_map.values()
    ]
    callbacks.sort(key=lambda record: record["outputs"])
    return tuple(callbacks), tuple(sorted(_layout_ids(app.layout)))


def _write() -> None:
    """Rewrites this file's literals from the app as it is now (see the module docstring)."""
    with tempfile.TemporaryDirectory() as tmp:
        callbacks, ids = observed(build_fixture_app(Path(tmp)))

    body = []
    for record in callbacks:
        body.append("    {")
        for field in ("outputs", "inputs", "state"):
            values = record[field]
            if not values:
                body.append(f'        "{field}": (),')
            elif len(values) == 1:
                body.append(f'        "{field}": ({values[0]!r},),')
            else:
                body.append(f'        "{field}": (')
                body.extend(f"            {value!r}," for value in values)
                body.append("        ),")
        body.append("    },")

    path = Path(__file__)
    source = path.read_text()
    start = source.index("CALLBACKS: tuple[dict[str, tuple[str, ...]], ...] = (\n")
    end = source.index("\n\n\ndef build_fixture_app(")
    new = (
        "CALLBACKS: tuple[dict[str, tuple[str, ...]], ...] = (\n"
        + "\n".join(body)
        + "\n)\n\nLAYOUT_IDS: tuple[str, ...] = (\n"
        + "".join(f"    {name!r},\n" for name in ids)
        + ")"
    )
    path.write_text(source[:start] + new + source[end:])
    print(f"{path}: {len(callbacks)} callback, {len(ids)} id")


if __name__ == "__main__":
    _write()
