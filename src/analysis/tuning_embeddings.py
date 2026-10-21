"""On-disk conventions of a dim_reduction tuning run's embeddings, shared by the pipeline that
writes them (src/pipeline/dim_reduction.py) and every reader that works from them afterwards
(src/analysis/tuning_evaluations.py, src/pipeline/evaluate_tuning_embeddings.py).

A tuning run directory holds embeddings.npz (one array per swept combination, keyed by
combo_key), config.md (a fenced JSON block snapshotting the run's own base_params/tuning_grid/
nested_params) and, per nested leaf, a subfolder named after each nested parameter's value
(leaf_dir). Keeping these three conventions in one module is what lets an evaluation run the same
way right after a sweep (in memory) and long after it (from disk, no refit).
"""

from __future__ import annotations

import itertools
import json
import zipfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np

CONFIG_FILENAME = "config.md"
EMBEDDINGS_FILENAME = "embeddings.npz"


def combo_key(keys: Sequence[str], combo: Sequence) -> str:
    """Self-describing string key for one tuning combination, e.g.
    'metric=dice,n_components=10,n_neighbors=15,min_dist=0.1' - same names/order as the run's
    tuning_grid.keys(), and the values rendered with str() (so str(bool) is 'True'/'False',
    identical to pandas' own CSV serialization of tuning_results.csv). Identical character for
    character to the string a reader rebuilds from one row of that CSV: no separate index file
    joins the two.
    """
    return ",".join(f"{key}={value}" for key, value in zip(keys, combo))


def parse_combo_key(key: str) -> dict[str, str]:
    """Inverse of combo_key, values left as the strings they were written as (the caller compares
    them against str() of the typed tuning_grid values, never against a re-parsed float). Raises
    ValueError for a part that is not exactly one 'name=value' pair or for a repeated name.
    """
    tokens: dict[str, str] = {}
    for part in key.split(","):
        pieces = part.split("=")
        if len(pieces) != 2 or not pieces[0]:
            raise ValueError(f"malformed combination key {key!r}: part {part!r} is not a 'name=value' pair")
        if pieces[0] in tokens:
            raise ValueError(f"malformed combination key {key!r}: name {pieces[0]!r} is repeated")
        tokens[pieces[0]] = pieces[1]
    return tokens


def leaf_dir(output_dir: Path, nested_params: Sequence[str], leaf: Mapping[str, object]) -> Path:
    """Folder of one nested leaf, one level per nested parameter: <output_dir>/metric=dice/
    n_components=10. With no nested_params the leaf is the run directory itself.
    """
    path = output_dir
    for name in nested_params:
        path = path / f"{name}={leaf[name]}"
    return path


@dataclass(frozen=True)
class TuningRun:
    """Everything an embedding-based evaluation needs about one tuning sweep: where it lives, the
    grid that produced it and every combination's embedding, keyed by combo_key.
    """

    run_dir: Path
    reduction_method: str
    base_params: dict
    tuning_grid: dict[str, list]
    nested_params: list[str]
    embeddings: dict[str, np.ndarray]


def read_tuning_config_block(config_path: Path) -> dict:
    """Parses the fenced ```json block of a tuning run's config.md and checks it has the fields a
    reader needs, each of the right type. Raises FileNotFoundError / ValueError with the exact path and
    missing or malformed piece.
    """
    if not config_path.is_file():
        raise FileNotFoundError(f"tuning config not found: {config_path}")
    text = config_path.read_text()
    if "```json" not in text:
        raise ValueError(f"{config_path} has no ```json config block")
    block = text.split("```json", 1)[1].split("```", 1)[0]
    config = json.loads(block)

    if not isinstance(config, dict):
        raise ValueError(f"{config_path}: config block must be a JSON object, got {config!r}")
    for field in ("reduction_method", "base_params", "tuning_grid", "nested_params"):
        if field not in config:
            raise ValueError(f"{config_path}: config block is missing {field!r}")
    if not isinstance(config["reduction_method"], str) or not config["reduction_method"]:
        raise ValueError(f"{config_path}: 'reduction_method' must be a non-empty string, got {config['reduction_method']!r}")
    if not isinstance(config["base_params"], dict):
        raise ValueError(f"{config_path}: 'base_params' must be an object, got {config['base_params']!r}")
    if not isinstance(config["tuning_grid"], dict) or not config["tuning_grid"]:
        raise ValueError(f"{config_path}: 'tuning_grid' must be a non-empty object, got {config['tuning_grid']!r}")
    if not isinstance(config["nested_params"], list) or not all(isinstance(name, str) for name in config["nested_params"]):
        raise ValueError(f"{config_path}: 'nested_params' must be a list of strings, got {config['nested_params']!r}")
    unknown_nested = [name for name in config["nested_params"] if name not in config["tuning_grid"]]
    if unknown_nested:
        raise ValueError(f"{config_path}: nested_params {unknown_nested} are not in tuning_grid {list(config['tuning_grid'])}")
    return config


def expected_combo_keys(tuning_grid: Mapping[str, Sequence]) -> set[str]:
    keys = list(tuning_grid)
    return {combo_key(keys, combo) for combo in itertools.product(*tuning_grid.values())}


def load_tuning_run(run_dir: Path) -> TuningRun:
    """Loads a tuning run from disk: embeddings.npz plus the grid declared in its config.md.

    config.md alone is not proof of what is in a tuning directory (a directory reused by a second
    run with a different grid keeps a config.md that describes only the last writer -
    lessons_learned.md #18), so the keys actually present in embeddings.npz must be exactly the
    Cartesian product of the declared tuning_grid; anything else raises instead of evaluating a
    layout the files do not have.
    """
    npz_path = run_dir / EMBEDDINGS_FILENAME
    if not npz_path.is_file():
        raise FileNotFoundError(
            f"{npz_path} not found - embeddings are only persisted by a tuning run with save_tuning_embeddings=true"
        )
    config_path = run_dir / CONFIG_FILENAME
    config = read_tuning_config_block(config_path)
    for axis, values in config["tuning_grid"].items():
        if not isinstance(values, list):
            raise ValueError(f"{config_path}: 'tuning_grid'[{axis!r}] must be a list of values, got {values!r}")

    try:
        with np.load(npz_path) as data:
            embeddings = {key: data[key] for key in data.files}
    except (zipfile.BadZipFile, EOFError) as exc:
        raise ValueError(f"{npz_path} is truncated or not a valid npz archive ({type(exc).__name__}: {exc})") from exc

    expected = expected_combo_keys(config["tuning_grid"])
    found = set(embeddings)
    if found != expected:
        missing = sorted(expected - found)
        unexpected = sorted(found - expected)
        raise ValueError(
            f"{npz_path} does not match the tuning_grid in {run_dir / CONFIG_FILENAME}: "
            f"{len(missing)} combination(s) missing (e.g. {missing[:2]}), {len(unexpected)} unexpected "
            f"(e.g. {unexpected[:2]}) - the directory was probably reused by a run with a different grid"
        )

    return TuningRun(
        run_dir=run_dir,
        reduction_method=config["reduction_method"],
        base_params=config["base_params"],
        tuning_grid=config["tuning_grid"],
        nested_params=list(config["nested_params"]),
        embeddings=embeddings,
    )
