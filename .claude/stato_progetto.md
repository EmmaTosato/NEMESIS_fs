# Stato progetto — NEMESIS

Ultimo aggiornamento: 2026-08-11. **Snapshot dello stato attuale — non un log cronologico.** Riscritto in place a ogni sessione (nessuna sezione per-sessione, nessun accumulo): descrive solo ciò che è vero *oggi*. La narrativa di cosa è successo sessione per sessione **non vive più qui** — è coperta da git log/commit message (cosa è cambiato e perché, a livello di codice), `docs/debugging/` (narrativa completa per sessione di debug), `.claude/lessons_learned.md` (pattern di errore generalizzabili, deduplicati), `runs.csv`/`runs_tuning.csv` + `logs/`/`summaries/` (provenienza di ogni esecuzione pipeline: parametri, output, log grezzo). Le sessioni registrate prima della conversione a snapshot (10/08) restano, congelate, in `.claude/stato_progetto_archive.md` (sola lettura, non più aggiornato). Le regole di sincronizzazione col cluster vivono in `.claude/branch_alignment.md`. `.claude/decision_log.md` è stato rimosso (commit `ce74909`, "chore: remove unused decision_log.md") — i pivot strategici/architetturali di alto livello non hanno più una casa dedicata separata al momento.

## Architettura / cosa è implementato

Sintesi corrente in `README.md` ("What's implemented so far") — non ripetuta qui. Riferimento architetturale sviluppatore: `docs/dev/` (`retrieval.md`, `models.md`, `config.md`, `plotting.md`, `lesion_matrix.md`, `fc_matrix.md`, `design_patterns.md`). Note metodologiche/di letteratura ora tutte sotto `docs/knowledge/` (`docs/methods/` è stato rimosso e il suo contenuto — `clustering.md`, `dim_reduction.md` — fuso lì dentro, tradotto in italiano).

## Lavoro attivo / thread aperti

- **Branch `fix/high-tuning-dir-reuse-and-stale-symlink`** pushato su `origin`, non ancora mergiato in `main` e senza PR aperta (link di GitHub per crearla già disponibile all'ultimo push). Contiene tutti e 4 i commit della deep code review conclusa questa sessione (2 CRITICAL, 3 HIGH, 5 MEDIUM, 5 LOW — vedi `docs/debugging/debug_11_08_26.md` per la narrativa completa) + il commit di questo stesso report. Suite: 572 passed, 12 skipped, 0 failed (esclusi i 2 file `bcblib`-dipendenti).
- **Working tree condiviso con una sessione parallela** attiva su `docs/` e `.claude/` (non committata al momento di questo snapshot): `.claude/CLAUDE.md`/`code_standards.md` modificati (nuova regola "mai commit automatico senza richiesta esplicita", vedi sotto), `DOCS_AUDIT.md` eliminato (non committato), `management/notes/TODO.md` in riscrittura attiva dall'utente stesso. Non toccare questi file senza prima verificare `git status`/`git diff` — non sono di questa sessione.
- **Stato dell'audit `docs/` (Tier 4/5, avviato sessioni precedenti) incerto**: il file di piano che lo tracciava (`.claude/plans/velvety-dazzling-lark.md`) non esiste più sul filesystem — non è chiaro dallo stato attuale se l'audit sia stato completato o il piano abbandonato/sostituito da altro lavoro (la sessione parallela ha nel frattempo riscritto/tradotto buona parte di `docs/guides/`+`docs/knowledge/`). Da chiarire con l'utente prima di riprenderlo.

## Vincoli/regole in vigore oggi

- **Nessun commit automatico da parte dell'agente**: commit solo su richiesta esplicita dell'utente (regola non ancora committata in `.claude/CLAUDE.md`/`code_standards.md` §9, ma già in vigore nel working tree condiviso).
- **Creazione di branch git**: una nota preesistente in questo file diceva "mai creare branch senza chiedere prima, commit diretti su `main` salvo indicazione esplicita" — non seguita alla lettera nella sessione appena conclusa (4 branch `fix/*` creati come parte di un workflow fix→test→commit esplicitamente autorizzato dall'utente con "risolvi"/"commit e push", mai con una richiesta esplicita per-branch). Da chiarire con l'utente se la regola è ancora quella originale o se il workflow appena tenuto va bene.
- **Working tree condiviso con sessioni parallele** (stesso autore git, `EmmaTosato`): sempre verificare `git status --short`/`git log` prima di stage/commit — mai dare per scontato che un file modificato sia proprio.
- **Esecuzione locale vs SLURM**: regola spostata in `.claude/CLAUDE.md` § "Running pipelines (local vs. SLURM)" (locale diretto è il default attuale, non proporre `sbatch`/jobs cluster senza richiesta esplicita) — non ripetuta qui per evitare due fonti di verità.
- **`src/sdc/`/`src/pipeline/compute_sdc.py`** non eseguibili/testabili in locale (richiedono `bcblib`, solo sul cluster) — `pytest --ignore` su `tests/unit/test_sdc_staging_and_check.py`/`tests/integration/test_compute_sdc_pipeline.py` fuori dal cluster.
- **Documentazione**: niente dump di tabelle/dati completi nei `.md` — solo tabelle corte + puntatore a `results/*.csv`.

## Prossimo passo esatto

Decidere con l'utente cosa fare del branch `fix/high-tuning-dir-reuse-and-stale-symlink`: aprire una PR verso `main` (link già fornito da GitHub all'ultimo push) o mergiare direttamente — nessuna delle due è stata fatta. In parallelo, chiarire lo stato reale dell'audit `docs/` (vedi sopra) prima di assumere sia da riprendere o sia già superato.
