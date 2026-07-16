# Lessons Learned — NEMESIS

Cumulative, concise index of recurring error patterns and best practices found while debugging or reviewing code in this repo. **One entry per pattern** — if the same pattern resurfaces in a different context in a later session, it is NOT duplicated here, only appended to that entry's "Seen in" list. This file only grows when a genuinely new pattern is found; it stays short by design.

Read this before starting a debugging session or writing new code in `src/`. For the full narrative behind an entry (the concrete bug, the exact fix, the test added), follow its "Seen in" reference into `docs/debugging/`.

## Patterns

### 1. Implicit fallback in `if/else` with no explicit handling of the unknown case
**Rule**: a two-branch `if/else` (or ternary) is only safe if the domain truly has exactly 2 values. If it can have more, use `if/elif/else: raise`, or better, make the invalid value unconstructable at the type level (e.g. validate in a constructor).
**Seen in**: `debug_09_07_26.md` (§1)

### 2. Validation anchored to one call site, not guaranteed by the data itself
**Rule**: if a value/object can be constructed from more than one place (tests routinely bypass loaders), validation belongs in the constructor/type when the rule is static, or in exactly one always-run cross-validation step when the rule depends on external/runtime data — never left to a single "well-behaved" caller to remember.
**Seen in**: `debug_09_07_26.md` (§2)

### 3. Ambiguous multi-match resolved arbitrarily (glob/wildcard/first-hit)
**Rule**: never `next(glob(...), None)`, `results[0]`, or similar without checking whether a second match exists. Register known naming variants explicitly with a declared priority order; if more than one still matches for the same real input, use the first by priority but surface the ambiguity (log + report) — never resolve it invisibly.
**Seen in**: `debug_09_07_26.md` (§3)

### 4. Same bad input, different behavior depending on which code path reaches it
**Rule**: if a validation/normalization step only runs on some branches (e.g. only when an optional filter is active), the same bad input can crash one path and be silently accepted as valid on another. Move the check to the shared source of the data, not to individual consumers. Watch specifically for the *default/most common* branch being the unvalidated one (e.g. "no filter set" is usually the common case, not the edge case) - it's easy to validate every *optional* branch and forget the plain one has no validation trigger at all.
**Seen in**: `debug_09_07_26.md` (§4), `debug_13_07_26.md` (§2 - subject discovery/template validation skipped entirely when `group_filter` was unset, the most common config)

### 5. Undetected duplicates in an input list corrupt aggregate counts/reports
**Rule**: reject duplicate entries in user/config-provided lists explicitly (clear error) rather than silently deduplicating, whenever that list feeds counts or report lines — a repeated entry processed twice produces misleading numbers (e.g. looks like overlap with a previous run that never happened). Also applies when the list feeds a `dict` keyed by its entries (e.g. dataset names) — a duplicate there doesn't corrupt a count, but collapses invisibly into one, silently ignoring what's very likely a copy-paste mistake. Re-check this pattern after fixing it once elsewhere in the same session — easy to reintroduce in a sibling list handled by different code.
**Seen in**: `debug_09_07_26.md` (§5, two instances in the same session), `debug_13_07_26.md` (§4 - duplicate dataset names silently collapsed via dict-keyed construction)

### 6. Aggregate ("collection has it") vs per-item ("this item has it") availability
**Rule**: an upfront/aggregate availability check that's deliberately permissive (avoids false negatives on otherwise-valid requests) is fine — but only if per-item gaps are tracked and reported separately, and the aggregate check is documented as "possible", not "guaranteed for every item".
**Seen in**: `debug_09_07_26.md` (§6)

### 7. External data shape not validated before its content
**Rule**: validate that parsed external data (JSON/config) has the expected top-level shape (e.g. is actually a dict) before indexing into it — otherwise a malformed file produces a raw `TypeError`/`AttributeError` instead of a clear domain error, and may not even be caught by surrounding error handling written for the domain exception type.
**Seen in**: `debug_09_07_26.md` (§7)

### 8. External JSON leaf values not type-checked before use as a hash key
**Rule**: a field parsed from external JSON and later used as a `dict` key or `set` element (directly, or packed into a tuple that is) must have its *value type* checked at parse time, not just that the key is present — JSON allows a list/object anywhere a string is expected, and using one as a hash key raises `TypeError: unhashable type`, not a domain `ValueError`. That error looks nothing like a config-validation failure and is confusing to debug from the message alone. Distinct from pattern #7 (top-level container shape) — this is about validating each individual leaf value before it reaches code that assumes it's hashable.
**Seen in**: `debug_13_07_26.md` (§3)

### 9. A CLI entry point's later-added phases aren't automatically inside the error boundary
**Rule**: when a CLI `main()` accumulates phases over time (validate → copy → verify → write report → write log), each filesystem-touching phase needs its *own* explicit try/except around the exception types it can legitimately raise (typically `OSError` for mkdir/write failures) — being adjacent to, or downstream of, an already-protected phase does not extend that protection. Re-audit every phase after adding a new one: "if this specific line raises, is it inside a try/except that produces a clean STOP, or does it propagate as a raw traceback?"
**Seen in**: `debug_13_07_26.md` (§1, §5 — two separate instances in the same session: `_copy_one`'s `mkdir()` sitting just outside its neighboring try/except, and `main()`'s log/report setup having no try/except at all)

### 10. Widening a shared function's scope to fix one consumer's visibility gap can silently break another consumer's already-documented scope
**Rule**: a shared helper used by several consumers (a report, a validation, a selection) sometimes gets *broadened* to fix a real problem for one of them ("subject X invisible when only Y is requested") - but if another consumer already declares a narrower contract elsewhere (a docstring, a doc section, a test), the broadening silently contradicts it instead of raising anything. Before widening a shared function's scope, `grep -rn` every call site and read each consumer's own stated scope (docstring/doc/test) - not just confirm the original problem is fixed.
**Seen in**: `debug_16_07_26.md` (§1 - `_known_object_spaces` broadened in a prior session to fix a real invisibility gap, but this made `copy_summary` report subjects outside the exact `(object, space, modality)` combinations in `retrieve`, contradicting that report's own already-documented scope in `_missing_message`'s docstring and `docs/dev/retrieval.md`)
