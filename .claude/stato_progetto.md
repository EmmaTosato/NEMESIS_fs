# Stato progetto — NEMESIS

Ultimo aggiornamento: 2026-08-22. **Snapshot dello stato attuale — non un log cronologico.** Riscritto in place a ogni sessione (nessuna sezione per-sessione, nessun accumulo): descrive solo ciò che è vero *oggi*. La narrativa di cosa è successo sessione per sessione **non vive più qui** — è coperta da git log/commit message, `docs/debugging/` (narrativa completa per sessione di debug), `.claude/lessons_learned.md` (pattern di errore generalizzabili, deduplicati), `runs.csv`/`runs_tuning.csv` + `logs/`/`summaries/` (provenienza di ogni esecuzione pipeline). Le sessioni registrate prima della conversione a snapshot (10/08) restano, congelate, in `.claude/stato_progetto_archive.md` (sola lettura, non più aggiornato).

## Architettura / cosa è implementato

Sintesi corrente in `README.md` ("What's implemented so far") — non ripetuta qui. Riferimento architetturale sviluppatore: `docs/dev/` (`retrieval.md`, `models.md`, `config.md`, `plotting.md`, `lesion_matrix.md`, `fc_matrix.md`, `design_patterns.md`). Note metodologiche/di letteratura sotto `knowledge/dim_reduction_clustering/` e `knowledge/neuroimaging/` (`docs/notes/` non esiste più, dissolta nel merge del 18/08 — riferimenti stale corretti in sessione 21-22/08).

## Lavoro attivo / thread aperti

- **Audit di correttezza teorica del 15/08/26**, tracciato in `AUDIT_FINDINGS.md` (repo root): **CRITICAL, HIGH, MEDIUM (#1-49) e LOW (#50-68) tutti chiusi/triageati** (sessioni 17-18/08, 21/08, 22/08). Restano deliberatamente aperti solo 2 finding HIGH pre-esistenti, mai nello scope delle sessioni MEDIUM/LOW: **HIGH #14** (`docs/dev/models.md` dichiara `assign_clusters_from_cooccurrence` tagliare a `n_clusters` fisso, il codice reale taglia a `threshold` — mismatch doc/codice) e **HIGH #15** (`clustering.py`'s comparison-plot in `main()` fuori da try/except). Nessun altro lavoro dell'audit resta da fare.
- **`management/notes/TODO.md`**: rimozione della feature `parcellate` da `build_lesion_matrix.py`/`src/features/lesion.py` — decisione loggata 17/08, non implementata. Tensione esplicita e irrisolta: la produzione attuale (`config/pipelines/build_lesion_matrix.json`, sessione `yan300s1`) usa `parcellate: true` per riprodurre Thiebaut de Schotten 2020; va deciso se questa rimozione sostituisce l'obiettivo di replica prima di procedere.
- **`docs/debugging/debug_22_08_26.md`**: scritto in questa sessione, copre ogni bug con un vero cambio di codice dei giri MEDIUM (#26-49) e LOW (#50-68) — un bug per sezione, criticità e lesson learned per ciascuno, per `code_standards.md` §8.
- **`AUDIT_FINDINGS.md` #69** (fuori audit, chiuso 22/08): 2 vecchie voci `git stash` (mesi fa, non applicabili — 2 file target non esistono più, 3 in conflitto) hanno rivelato che la feature RSC/Monti consensus clustering, già implementata e in produzione, non aveva test diretti — 14 test nuovi scritti contro l'API attuale, stash scartati.

## Vincoli/regole in vigore oggi

- **`AUDIT_FINDINGS.md` è la fonte di verità sullo stato dei finding dell'audit 15/08** — ora interamente chiuso/triageato tranne HIGH #14/#15 (sopra). Non fidarsi del titolo/riga citati senza riverificare contro il codice attuale: più volte in questa serie di sessioni un finding il cui titolo citava un file poi rimosso (`dim_reduction_clustering.py`) si è rivelato moot, oppure il difetto reale viveva altrove (#14/#18 HIGH, #39/#40/#59/#60 MEDIUM/LOW).
- **`.claude/lessons_learned.md` #28** (21/08): tightening di una validazione condivisa a basso livello (`group_of()` sempre validato, MEDIUM #26/#46) ha rotto 44 test in 5 file non correlati al codice toccato — il vero raggio d'impatto era invisibile dal diff, visibile solo eseguendo la suite intera. Vale come promemoria per qualunque futuro tightening di validazione simile.
- **Commit automatici**: solo su richiesta esplicita dell'utente (`.claude/CLAUDE.md`, `code_standards.md` §9). Nella sessione 21/08 l'utente ha esplicitamente richiesto commit+push per permettere la ripresa autonoma (schedulata via `CronCreate`, non un agente cloud — `/schedule`'s routine ha fallito con 403, il repo non è connesso a claude.ai per quel meccanismo) — non un'eccezione permanente al vincolo.
- **Esecuzione locale vs SLURM**: locale diretto è il default, non proporre `sbatch`/jobs cluster senza richiesta esplicita.
- **`src/sdc/`/`src/pipeline/compute_sdc.py`** non eseguibili/testabili in locale (richiedono `bcblib`) — `pytest --ignore` su `tests/unit/test_sdc_staging_and_check.py`/`tests/integration/test_compute_sdc_pipeline.py` fuori dal cluster.
- **Documentazione**: niente dump di tabelle/dati completi nei `.md` — solo tabelle corte + puntatore a `results/*.csv`.

## Prossimo passo esatto

Suite verde confermata (762 passed, 0 failed, 12 skipped, esclusi i 2 file `bcblib`-dipendenti) subito prima del commit di questa sessione. Nessuna azione bloccante in corso sull'audit — i thread realmente aperti sono solo quelli elencati sopra (HIGH #14/#15 lasciati deliberatamente, decisione `parcellate` in `management/notes/TODO.md`). Nessuno stash residuo (verificato `git stash list` vuoto). Prossimo lavoro dipende dalla direzione dell'utente.
