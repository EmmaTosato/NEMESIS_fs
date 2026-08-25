# Design patterns used in this repo

Cross-cutting reference: the recurring design patterns/idioms used across `src/`, named explicitly, with one canonical example each and pointers to the fuller module-level writeups (`docs/dev/retrieval.md`, `docs/dev/models.md`, `docs/dev/config.md`, `docs/dev/plotting.md`, `docs/dev/lesion_matrix.md`, `docs/dev/fc_matrix.md`). Not a general design-patterns tutorial — only the ones this repo actually uses, and why each was chosen here specifically.

## Strategy

**A family of interchangeable algorithms, selected at runtime by a name, sharing one call signature.**

```python
REDUCTION_METHODS: dict[str, Callable[[np.ndarray, dict], np.ndarray]] = {
    "umap": umap_embed, "tsne": tsne_embed, "pca": pca_embed,
}
```

Used for: `REDUCTION_METHODS`/`CLUSTERING_METHODS` (`src/analysis/reduction.py`/`clustering.py`).

Implemented as a **plain `dict[str, Callable]`**, not classes/interfaces/ABCs — each strategy is a pure function (`(X, params) -> array`), no shared base class, no state. This is a deliberate simplification over the textbook OOP version of Strategy: with no per-strategy state or lifecycle to manage, a class hierarchy would add indirection without buying anything. Same shape as the **Registry** pattern below because a `dict[str, Callable]` *is* simultaneously a strategy-selection table and a registry — the two patterns coincide here rather than layering on top of each other.

## Registry (explicit, over hardcoded dispatch)

**A single, explicit table of "known valid values," consulted instead of an `if/elif` chain or a hardcoded assumption.**

The original and broadest example: `config/registry/file_patterns.json`, which replaced hardcoded `glob()` calls in `Dataset` with a data-driven table of `object → pipeline? → datatype → suffix → filename template(s)` (`docs/dev/retrieval.md`, "The `file_patterns.json` registry"). Every `dict[str, Callable]` Strategy table above follows the same precedent for methods instead of file paths.

Why explicit over hardcoded: adding a new value (a new reduction method, a new file-naming variant) means adding one entry, not touching dispatch logic - and an unknown value is rejected with a clear "known: [...]" error message (every `_validate_method`/`load_method_params` in `src/analysis/`) instead of silently falling through or raising a confusing `KeyError`.

## Boundary validation (fail fast at the config boundary)

**External input (a JSON config a human wrote by hand) is fully validated the moment it's loaded — never partway through a run, never left to whatever library call happens to choke on a bad value first.**

Every `load_*_config` function in `src/retrieval/config.py` and `src/analysis/{build_config,model_config}.py` follows this: hand-written `_require_*`/`_optional_*` helpers, one per field, each raising `ValueError` naming exactly what's wrong. Two representative examples of *why* this matters more than it might look:

- `build_config.py`'s `resample_interpolation` check (against nilearn's exact accepted set `{"linear", "nearest", "continuous"}`) turns a typo into an instant, zero-cost rejection instead of a crash potentially hundreds of subjects into a real run.
- `binarize_threshold`'s `[0.0, 1.0]` range check catches a config mistake that would otherwise silently produce a degenerate (all-zero or all-one) matrix, only visible much later as an oddly-shaped/empty result far from the actual cause.

This is the concrete mechanism behind `code_standards.md` §0 ("niente fallback silenziosi") applied specifically to config loading - see also `lessons_learned.md` #7 (validate external data's *shape* before its content).

## Immutable value object (frozen dataclass)

**Config, once parsed, is a plain, immutable, typed record — not a dict, not mutated after construction.**

```python
@dataclass(frozen=True)
class BuildMatrixConfig:
    project: str
    data_root: Path
    ...
```

Every `load_*_config` function returns one of these (`RetrievalConfig`, `RetrieveItem`, `FilePatterns` in `src/retrieval/config.py`; `BuildMatrixConfig`, `DimReductionConfig`, `ClusteringConfig`, `DimReductionClusteringConfig` in `src/analysis/`). `frozen=True` makes "config changed after validation" a class of bug that can't happen - nothing downstream can accidentally mutate a shared config object and desync it from what was actually validated.

## Atomic write (temp-directory swap)

**A multi-file output directory is either fully absent or fully present and correct — never half-written.**

`src/utils/artifacts.py`'s `save_matrix`: write every file (`matrix.npy`, `metadata.csv`, extra arrays, `config.md`, `manifest.json` last) into a temporary sibling directory, then `rename()` it into place as the final step. A crash or interruption at any point before the rename leaves only an orphaned temp directory - the real output path never exists in a partial state. `load_matrix` relies on this: it treats "no `manifest.json`" as "this artifact was never successfully built," which is only a valid inference because of the atomic swap.

Contrast with the pipeline scripts' own `summaries/`/`logs/` writes - **not** atomic, deliberately: they're secondary/informational outputs written after the real artifact already landed successfully, so a partial write there doesn't corrupt anything that matters.

## Layered architecture

**`utils` → `retrieval`/`features` → `analysis` → `pipeline`. Higher layers depend on lower ones, never the reverse.**

Stated in `code_standards.md` §1 and enforced by convention rather than tooling. Concrete example of the rule in action: `src/analysis/build_config.py` importing `KNOWN_GROUPS` from `src/retrieval/config.py` is a legal downward dependency (`analysis` sits above `retrieval`); the reverse (`retrieval`/`features` importing from `analysis`) would violate it and was avoided throughout - `features/lesion.py` has no knowledge that `analysis`/`pipeline` exist at all.
