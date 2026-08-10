# Stato progetto — NEMESIS

Ultimo aggiornamento: 2026-08-10. **Snapshot dello stato attuale — non un log cronologico.** Riscritto in place a ogni sessione (nessuna sezione per-sessione, nessun accumulo): descrive solo ciò che è vero *oggi*. La narrativa di cosa è successo sessione per sessione **non vive più qui** — è coperta da git log/commit message (cosa è cambiato e perché, a livello di codice), `docs/debugging/` (narrativa completa per sessione di debug), `.claude/decision_log.md` (solo i pivot strategici/architetturali di alto livello), `.claude/lessons_learned.md` (pattern di errore generalizzabili, deduplicati), `runs.csv`/`runs_tuning.csv` + `logs/`/`summaries/` (provenienza di ogni esecuzione pipeline: parametri, output, log grezzo). Le sessioni registrate prima di questo cambio restano, congelate, in `.claude/stato_progetto_archive.md` (sola lettura, non più aggiornato). Le regole di sincronizzazione col cluster vivono in `.claude/branch_alignment.md`.

## Architettura / cosa è implementato

Sintesi corrente in `README.md` ("What's implemented so far") — non ripetuta qui per evitare due fonti di verità. Riferimento architetturale sviluppatore: `docs/dev/` (`retrieval.md`, `models.md`, `config.md`, `plotting.md`, `lesion_matrix.md`, `fc_matrix.md`, `design_patterns.md`).

## Lavoro attivo / thread aperti

- **Audit sistematico di `docs/`** (piano in `.claude/plans/velvety-dazzling-lark.md`, 31 file): completati Tier 1 (guide + dev), Tier 2 (methods), Tier 3 (knowledge) — 18/31. Restano Tier 4 (`docs/experiments/dim_reduction_clustering/`, 3 file) e parte del Tier 5 (7 `docs/debugging/debug_*.md` + `docs/setup.md`).
- **Ristrutturazione dei file di continuità di sessione** (questa sessione, 2026-08-10): `stato_progetto.md` convertito da log cronologico a snapshot puro (skill `.claude/skills/stato-progetto/SKILL.md` aggiornata di conseguenza); storico pre-esistente spostato in `.claude/stato_progetto_archive.md`. `.claude/decision_log.md` lasciato invariato nello scopo (solo pivot strategici, mai lavoro ordinario).

## Vincoli/regole in vigore oggi

- **Working tree condiviso con sessioni parallele** (stesso autore git, `EmmaTosato`): sempre verificare `git status --short`/`git log` prima di stage/commit — mai dare per scontato che un file modificato sia proprio.
- **Mai creare branch git senza chiedere prima** — commit diretti su `main` salvo indicazione esplicita.
- **Esecuzione locale, non SLURM**: le pipeline si lanciano direttamente in locale per ora, non proporre `sbatch`/jobs cluster senza richiesta esplicita.
- **`src/sdc/`/`src/pipeline/compute_sdc.py`** non eseguibili/testabili in locale (richiedono `bcblib`, solo sul cluster) — `pytest --ignore` su quei 2 file di test fuori dal cluster.
- **Documentazione**: niente dump di tabelle/dati completi nei `.md` — solo tabelle corte + puntatore a `results/*.csv`.

## Prossimo passo esatto

Riprendere l'audit `docs/` dal Tier 4/5 (vedi piano): `docs/knowledge/dimensionality_reduction_methods.md`, `docs/knowledge/umap_tsne_guide.md`, poi i 3 file di `docs/experiments/dim_reduction_clustering/`, poi i 7 `docs/debugging/debug_*.md` restanti (narrativa storica — verificare solo coerenza interna/git history, non riscrivere per lo stato di oggi) e infine `docs/setup.md` contro `environment.yml`.
