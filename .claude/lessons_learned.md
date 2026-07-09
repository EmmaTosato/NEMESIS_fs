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
**Rule**: if a validation/normalization step only runs on some branches (e.g. only when an optional filter is active), the same bad input can crash one path and be silently accepted as valid on another. Move the check to the shared source of the data, not to individual consumers.
**Seen in**: `debug_09_07_26.md` (§4)

### 5. Undetected duplicates in an input list corrupt aggregate counts/reports
**Rule**: reject duplicate entries in user/config-provided lists explicitly (clear error) rather than silently deduplicating, whenever that list feeds counts or report lines — a repeated entry processed twice produces misleading numbers (e.g. looks like overlap with a previous run that never happened). Re-check this pattern after fixing it once elsewhere in the same session — easy to reintroduce in a sibling list handled by different code.
**Seen in**: `debug_09_07_26.md` (§5, two instances in the same session)

### 6. Aggregate ("collection has it") vs per-item ("this item has it") availability
**Rule**: an upfront/aggregate availability check that's deliberately permissive (avoids false negatives on otherwise-valid requests) is fine — but only if per-item gaps are tracked and reported separately, and the aggregate check is documented as "possible", not "guaranteed for every item".
**Seen in**: `debug_09_07_26.md` (§6)

### 7. External data shape not validated before its content
**Rule**: validate that parsed external data (JSON/config) has the expected top-level shape (e.g. is actually a dict) before indexing into it — otherwise a malformed file produces a raw `TypeError`/`AttributeError` instead of a clear domain error, and may not even be caught by surrounding error handling written for the domain exception type.
**Seen in**: `debug_09_07_26.md` (§7)
