"""Firing one callback of the Embedding Explorer, the way the browser does.

A callback body cannot be called from Python directly: Dash wraps it, and the wrapper needs the
request context the function reads (`ctx.triggered_id`) plus the output spec it writes back
into. The faithful way to run one is the request the browser itself makes, so this posts to
`/_dash-update-component` on the app's own Flask test client and hands back what the callback
returned.

An input is written `"component-id.property"` with its value; a pattern-matching id is written
as its JSON (`'{"mode":"dataset","type":"color-mode-btn"}.n_clicks'`), and an entry that is
already a list or a dict is passed through untouched - which is how a wildcard input, one entry
per matching component, is given. The order matters: Dash maps the inputs to the function's
parameters by position, exactly as declared in the decorator.

A callback is looked up by a key Dash builds itself: several outputs are joined with "..", and
a wildcard id carries ALL as `["ALL"]`. Rebuilding that by hand is how you get a key that is one
dot off and a KeyError that says nothing, so `key_for` asks the app for it instead.
"""

from __future__ import annotations

import json
from typing import Any

PREVENTED = object()
"""What a callback that raised PreventUpdate returns: Dash answers 204 with no body."""


def key_for(app, output: str) -> str:
    """The key `app.callback_map` holds for the callback that writes `output`.

    Raises if no callback writes it, or more than one does - both mean the test is asking for
    something that does not exist rather than something that quietly does the wrong thing."""
    matches = [key for key in app.callback_map if output in key.split("...") or key == output]
    if len(matches) != 1:
        raise ValueError(f"{output!r}: {len(matches)} callback lo scrivono, atteso 1 - trovati {matches}")
    return matches[0]


def _split(name: str) -> tuple[str | dict, str]:
    """("component-id", "property"), the id parsed back to a dict when it is a pattern id."""
    component_id, prop = name.rsplit(".", 1)
    return (json.loads(component_id) if component_id.startswith("{") else component_id), prop


def _dependency(entry: tuple[str, Any] | list | dict) -> list | dict:
    if isinstance(entry, (list, dict)):
        return entry
    name, value = entry
    component_id, prop = _split(name)
    return {"id": component_id, "property": prop, "value": value}


def _one_output(name: str) -> dict:
    component_id, prop = _split(name)
    return {"id": component_id, "property": prop}


def _output_spec(names: list[str | list[str]]) -> tuple[str, list | dict]:
    """Dash reads a single output and several outputs differently, and a list of one is misread
    as a wildcard multi-output spec (checked against its own _validate.validate_multi_return),
    so a single output must be a bare dict and a bare "id.property" string.

    The spec must also mirror the callback's own grouping: one `Output` on a wildcard id is ONE
    output holding every component it matches, so it is written as a nested list of names and
    stays nested here - flattening it gives "Wrong length output_spec"."""
    if len(names) == 1 and isinstance(names[0], str):
        spec = _one_output(names[0])
        return f"{spec['id'] if isinstance(spec['id'], str) else names[0].rsplit('.', 1)[0]}.{spec['property']}", spec
    flat = [name for entry in names for name in ([entry] if isinstance(entry, str) else entry)]
    joined = ".." + "...".join(flat) + ".."
    spec = [
        [_one_output(name) for name in entry] if isinstance(entry, list) else _one_output(entry)
        for entry in names
    ]
    return joined, spec


def fire(
    app,
    outputs: str | list[str | list[str]],
    inputs: list[tuple[str, Any] | list | dict],
    changed: list[str] | None = None,
    state: list[tuple[str, Any] | list | dict] | None = None,
    key: str | None = None,
) -> dict:
    """Runs the callback that writes `outputs` and returns `{component_id: {property: value}}`,
    or PREVENTED if it raised PreventUpdate.

    `changed` is what the browser reports as having just changed ("run-picker.value"); it is
    what `ctx.triggered_id` is read from, so a callback that branches on it needs it set. The
    default - every input - matches the first render, when everything is new.
    """
    names = [outputs] if isinstance(outputs, str) else list(outputs)
    output, output_spec = _output_spec(names)
    if key is not None:
        output = key
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
    key: str | None = None,
):
    """The single value a one-output callback returned, or PREVENTED."""
    result = fire(app, output, inputs, changed, state, key)
    if result is PREVENTED:
        return PREVENTED
    component_id, prop = output.rsplit(".", 1)
    return result[component_id][prop]
