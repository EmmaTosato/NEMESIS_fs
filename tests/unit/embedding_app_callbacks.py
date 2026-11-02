"""Firing one callback of the Embedding Explorer, the way the browser does.

A callback body cannot be called from Python directly: Dash wraps it, and the wrapper needs the
request context the function reads (`ctx.triggered_id`) plus the output spec it writes back
into. The faithful way to run one is the request the browser itself makes, so this posts to
`/_dash-update-component` on the app's own Flask test client and hands back what the callback
returned.

An input is written `"component-id.property"` with its value; an entry that is already a list
or a dict is passed through untouched, which is how a pattern-matching input (one entry per
matching component) is given. The order matters: Dash maps the inputs to the function's
parameters by position, exactly as declared in the decorator.
"""

from __future__ import annotations

import json
from typing import Any

PREVENTED = object()
"""What a callback that raised PreventUpdate returns: Dash answers 204 with no body."""


def _dependency(entry: tuple[str, Any] | list | dict) -> list | dict:
    if isinstance(entry, (list, dict)):
        return entry
    name, value = entry
    component_id, prop = name.rsplit(".", 1)
    return {"id": component_id, "property": prop, "value": value}


def _output_spec(names: list[str]) -> tuple[str, list | dict]:
    """Dash reads a single output and several outputs differently, and a list of one is misread
    as a wildcard multi-output spec (checked against its own _validate.validate_multi_return),
    so a single output must be a bare dict and a bare "id.property" string."""
    pairs = [name.rsplit(".", 1) for name in names]
    if len(pairs) == 1:
        component_id, prop = pairs[0]
        return f"{component_id}.{prop}", {"id": component_id, "property": prop}
    joined = ".." + "...".join(f"{cid}.{prop}" for cid, prop in pairs) + ".."
    return joined, [{"id": cid, "property": prop} for cid, prop in pairs]


def fire(
    app,
    outputs: str | list[str],
    inputs: list[tuple[str, Any] | list | dict],
    changed: list[str] | None = None,
    state: list[tuple[str, Any] | list | dict] | None = None,
) -> dict:
    """Runs the callback that writes `outputs` and returns `{component_id: {property: value}}`,
    or PREVENTED if it raised PreventUpdate.

    `changed` is what the browser reports as having just changed ("run-picker.value"); it is
    what `ctx.triggered_id` is read from, so a callback that branches on it needs it set. The
    default - every input - matches the first render, when everything is new.
    """
    names = [outputs] if isinstance(outputs, str) else list(outputs)
    output, output_spec = _output_spec(names)
    input_specs = [_dependency(entry) for entry in inputs]
    if changed is None:
        changed = [
            f"{spec['id']}.{spec['property']}" for spec in input_specs if isinstance(spec, dict)
        ]
    body = {
        "output": output,
        "outputs": output_spec,
        "inputs": input_specs,
        "changedPropIds": changed,
        "state": [_dependency(entry) for entry in (state or [])],
    }
    app.server.config["TESTING"] = True
    client = app.server.test_client()
    response = client.post("/_dash-update-component", data=json.dumps(body), content_type="application/json")
    if response.status_code == 204:
        return PREVENTED
    assert response.status_code == 200, f"{output}: HTTP {response.status_code}\n{response.get_data(as_text=True)}"
    return response.get_json()["response"]


def fire_one(
    app,
    output: str,
    inputs: list[tuple[str, Any] | list | dict],
    changed: list[str] | None = None,
    state: list[tuple[str, Any] | list | dict] | None = None,
):
    """The single value a one-output callback returned, or PREVENTED."""
    result = fire(app, output, inputs, changed, state)
    if result is PREVENTED:
        return PREVENTED
    component_id, prop = output.rsplit(".", 1)
    return result[component_id][prop]
