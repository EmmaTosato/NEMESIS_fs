# 04 — Handoff

- **Data**: 2026-10-23 · **Branch**: `claude/bold-ritchie-7ekm6v` · **Fase attuale**: FASE 1
- **Completati**: `.claude/CLAUDE.md` (76/76). Prossimo: `.claude/stato_progetto.md` (42 righe, riga 1).
- **Ordine successivo (da master plan)**: stato_progetto.md → code_standards.md → branch_alignment.md → open_problems.md → lessons_learned.md → `.claude/history/*` → `.claude/skills/*` → docs/setup.md → docs/guides → docs/dev → docs/experiments → docs/debugging → knowledge/notes.

## Primissima azione nella prossima chat
1. Leggere `.claude/audit/04_handoff_state.md`, poi `02_contradictions_and_open_issues.md` e `01_assertions_ledger.md` (incl. "Nota per file futuri").
2. Auditare `.claude/stato_progetto.md` (snapshot: verificare branch/ultimo stato con `git log`/`git status`, path e comandi citati). Poi `code_standards.md` (123 righe): controllare i riferimenti a `src/utils/subject_ids.py`, `src/utils/logging_setup.py::log_duration`, `docs/debugging/debug_25_08_26.md`, §8 `lesson_learned.md` (ISS-006).
3. Soglia di handoff: dopo 2–3 file piccoli o 1 grande, aggiornare i 5 file e fermarsi.

## Anomalie scoperte finora (9 aperte, vedi file 02)
ALTA: ISS-002 (`dash` assente da environment.yml). MEDIA: ISS-003 (job mancanti per archive_local_raw_data/embedding_app). BASSA: ISS-001 (clone shallow), 004 (covariance_pca.md non indicizzato), 005 (.nii gitignore impreciso), 006 (lesson_learned.md refuso), 007 (elenco pacchetti), 008 (summaries/ assente), 009 (pytest non eseguibile).

## Decisioni in attesa dall'utente (bloccanti per verifiche successive)
- ISS-001: `git fetch --unshallow`?
- ISS-009: creare ambiente per eseguire `pytest` nel container, o fornirmi l'output dei test?
