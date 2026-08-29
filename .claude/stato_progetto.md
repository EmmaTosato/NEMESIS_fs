# Stato progetto — NEMESIS

Ultimo aggiornamento: 2026-08-28. **Snapshot dello stato attuale — non un log cronologico.** Riscritto in place a ogni sessione (nessuna sezione per-sessione, nessun accumulo): descrive solo ciò che è vero *oggi*. La narrativa di cosa è successo sessione per sessione **non vive più qui** — è coperta da git log/commit message, `docs/debugging/` (narrativa completa per sessione di debug), `.claude/lessons_learned.md` (pattern di errore generalizzabili, deduplicati), `runs.csv`/`runs_tuning.csv` + `logs/`/`summaries/` (provenienza di ogni esecuzione pipeline). Le sessioni registrate prima della conversione a snapshot (10/08) restano, congelate, in `.claude/stato_progetto_archive.md` (sola lettura, non più aggiornato).

## Architettura / cosa è implementato

Sintesi corrente in `README.md` ("What's implemented so far") — non ripetuta qui. Riferimento architetturale sviluppatore: `docs/dev/` (`retrieval.md`, `models.md`, `config.md`, `plotting.md`, `lesion_matrix.md`, `fc_matrix.md`, `sdc_matrix.md`, `design_patterns.md`). Note metodologiche/di letteratura sotto `knowledge/dim_reduction_clustering/` e `knowledge/neuroimaging/`.
Strumenti accessori: `scripts/plot_tuning_embedding_3d.py` (visual testing interattivo 3D on-demand), `archive_local_raw_data.py` (archiviazione raw locale). `generate_understanding_umap_report.py` (28-08) ora offre solo i color-mode effettivamente presenti nel `metadata.csv` di una run, non un set fisso — necessario per matrici non-lesion-derived (es. `build_sdc_matrix.py`, senza `lesion_volume_voxels`).

## Lavoro attivo / thread aperti

- **Task 2 (SDC)**: dim reduction (UMAP + t-SNE, tuning + `understanding_umap_report`) completata per `s2.1` (`schaefer_200_tian_s2`, `data/derived/sdc_matrix/27-08_s2.1`, sessione 28-08). Prossimo passo del task non ancora iniziato: clustering su questo embedding (vedi `TODO.md`, sezione SDC).
- Elenco completo dei task aperti in `TODO.md` (non duplicato qui): visualizzazioni anatomiche UMAP/t-SNE (lesion) e clustering, PCA da implementare, SDC clustering, provenienza del file `..._streamline.csv` in `sub_BCB_example/` da chiarire con l'utente, notebook di comparison (statistica + visiva) non iniziato.
- Working tree con modifiche non committate (fix `understanding_umap_report.py`, checkbox `TODO.md`, run SDC in `dim_reduction.json`/docs/experiments) — da committare solo su richiesta esplicita.

## Vincoli/regole in vigore oggi

- **`AUDIT_FINDINGS.md`** (audit 15/08) interamente chiuso/triageato — nessun lavoro residuo.
- **Commit automatici**: solo su richiesta esplicita dell'utente (`.claude/CLAUDE.md`, `code_standards.md` §9).
- **Esecuzione locale vs SLURM**: locale diretto è il default, non proporre `sbatch`/jobs cluster senza richiesta esplicita.
- **`src/sdc/`/`src/pipeline/compute_sdc.py`** non eseguibili/testabili in locale (richiedono `bcblib`) — `pytest --ignore` su `tests/unit/test_sdc_staging_and_check.py`/`tests/integration/test_compute_sdc_pipeline.py` fuori dal cluster.
- **Documentazione e Codice**: niente dump di tabelle o dati completi nei `.md` (solo pointer a `results/*.csv`). Rationale/logica verbosa confinata in `docs/dev/`, il sorgente python deve rimanere conciso e snello.
- **Diagnostic grid oltre 2D**: `n_components > 2` non emette un diagnostic grid automatico (schiacciato in 2D sarebbe fuorviante) — ispezione solo on-demand via `scripts/plot_tuning_embedding_3d.py`, non è un bug.
- **Diagnostici standalone dei tuning di clustering** (dendrogramma agglomerative, eigengap spectral): ora rifatti per ogni valore dell'asse che sweepano (metric/affinity), non più una singola immagine da `base_params` — vedi `lessons_learned.md` #31.

## Prossimo passo esatto

Avviare il clustering SDC su `results/sdc/dim_reduction/tuning/umap/28-08_s2.1` (o sull'equivalente t-SNE `28-08_s2.1`) con `clustering.py --reduced_data true`, seguendo lo stesso schema già maturo usato per il lesion embedding (Task 1). In alternativa, se si riprende la discussione di tuning/evaluation del clustering lesion (thread in corso in conversazione, non ancora scritto su file), continuare da lì.
