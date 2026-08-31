# Stato progetto — NEMESIS

Ultimo aggiornamento: 2026-08-31. **Snapshot dello stato attuale — non un log cronologico.** Riscritto in place a ogni sessione (nessuna sezione per-sessione, nessun accumulo): descrive solo ciò che è vero *oggi*. La narrativa di cosa è successo sessione per sessione **non vive più qui** — è coperta da git log/commit message, `docs/debugging/` (narrativa completa per sessione di debug), `.claude/lessons_learned.md` (pattern di errore generalizzabili, deduplicati), `runs.csv`/`runs_tuning.csv` + `logs/`/`summaries/` (provenienza di ogni esecuzione pipeline). Le sessioni registrate prima della conversione a snapshot (10/08) restano, congelate, in `.claude/stato_progetto_archive.md` (sola lettura, non più aggiornato).

## Architettura / cosa è implementato

Sintesi corrente in `README.md` ("What's implemented so far") — non ripetuta qui. Riferimento architetturale sviluppatore: `docs/dev/` (`retrieval.md`, `models.md`, `config.md`, `plotting.md`, `lesion_matrix.md`, `fc_matrix.md`, `sdc_matrix.md`, `design_patterns.md`). Note metodologiche/di letteratura sotto `knowledge/dim_reduction_clustering/` e `knowledge/neuroimaging/`.

Schema `runs.csv`/`runs_tuning.csv` rivisto (31-08-26, `docs/dev/config.md` per il dettaglio completo): colonna `id` rimossa ovunque (ridondante, mai letta da nessun consumer); `clustering.py` logga ora `reduction_method`/`reduction_n_components`/`reduction_metric` (prefisso `reduction_` per non collidere con l'omonimo hyperparameter di un metodo di clustering, es. `gmm.n_components`) sia in `runs.csv`/`runs_tuning.csv` che nel `config.md` di ogni run — risolti automaticamente dal `config.md` del run dim_reduction sorgente, mai dichiarati a mano.

## Lavoro attivo / thread aperti

- **SDC clustering (Task 2)**: fine-tuning avviato su `s2.1` (embedding UMAP `31-08_s2.1_m_euclidean_nc2`) — completo per tutti e 5 i metodi (kmeans/agglomerative/gmm/hdbscan/spectral). `nc3` preparato in `config/pipelines/clustering.json` (kmeans/agglomerative/gmm/hdbscan insieme, spectral a parte — stesso schema di `nc2`) ma non ancora lanciato. `TODO.md` sezione "Fase 2" dice ancora "bloccata per intero" — non più vero, va aggiornato quando si riprende quel file.
- **Audit naming**: chiuso il giro a livello di CSV/`config.md` (commit `8c6a4de` su `main` — id rimossa, colonne `reduction_*`, 6 path stale da rename `tag-params-multi-key` corretti, bug pre-esistente in `mask_fc.py`/`build_fc_matrix.py` risolto). Prossimo giro: stesso audit a livello di **plot** (titoli/etichette/legende/filename immagini) — prompt già preparato per una nuova chat, non ancora lanciato.

## Vincoli/regole in vigore oggi

- **Branch**: lavoro attuale mergeato direttamente su `main` (branch `clustering-runs-csv-reduction-columns`, merge commit `8c6a4de`) — `main` è avanti di 7 commit locali rispetto a `origin/main`, mai pushato finora (nessuna richiesta esplicita in tal senso).
- **Commit automatici**: solo su richiesta esplicita dell'utente (`.claude/CLAUDE.md`, `code_standards.md` §9). Se si commit di nuovo stando su `main`: branch dedicato prima, mai commit diretto sul default branch.
- **Esecuzione locale vs SLURM**: locale diretto è il default, non proporre `sbatch`/jobs cluster senza richiesta esplicita.
- **`src/sdc/`/`src/pipeline/compute_sdc.py`** non eseguibili/testabili in locale (richiedono `bcblib`) — `pytest --ignore` su `tests/unit/test_sdc_staging_and_check.py`/`tests/integration/test_compute_sdc_pipeline.py` fuori dal cluster.
- **Documentazione e Codice**: niente dump di tabelle o dati completi nei `.md` (solo pointer a `results/*.csv`). Rationale/logica verbosa confinata in `docs/dev/`, il sorgente python deve rimanere conciso e snello.
- **Diagnostic grid oltre 2D**: `n_components > 2` non emette un diagnostic grid automatico (schiacciato in 2D sarebbe fuorviante) — ispezione solo on-demand via `scripts/plot_tuning_embedding_3d.py`, non è un bug.

## Prossimo passo esatto

Lanciare `clustering.py --config config/pipelines/clustering.json` (tuning kmeans/agglomerative/gmm/hdbscan su `nc3` SDC), seguito da un run separato di `spectral` sullo stesso `nc3` (stesso schema già usato per `nc2` — `save_tuning_clusterings: true` non supporta `affinity` sweeppata). In alternativa, avviare la nuova chat con il prompt già preparato per l'audit naming a livello di plot (vedi sopra).
