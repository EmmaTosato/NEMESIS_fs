# 04 — Passaggio di consegne

**Ultimo aggiornamento**: 2026-10-26, fine dell'undicesimo ciclo (`docs/guides/`: 6 file su 14 fatti).

## Stato
- **Fase**: 1 (Doc, Knowledge & `.claude`).
- **Completati**: `.claude/CLAUDE.md` (76/76), `.claude/stato_progetto.md` (50/50), `.claude/code_standards.md` (123/123), `.claude/branch_alignment.md` (40/40), `.claude/open_problems.md` (215/215), `.claude/lessons_learned.md` (191/191), `.claude/history/data_changelog.md` (223/223), `.claude/skills/history/SKILL.md` (79/79), `docs/setup.md` (36/36), `docs/guides/evaluate_dim_reduction_tuning.md` (43), `fc_matrix_building.md` (57), `understanding_umap_report.md` (59), `sdc_matrix_building.md` (117), `dim_reduction.md` (134), `evaluate_clustering_tuning.md` (121).
- **Prossimo file**: `docs/guides/` restanti (8): `matrix_building.md` 139, `pipeline_order.md` 198, `datasets.md` 198, `exploration.md` 216, `evaluation.md` 259, `clustering.md` 281, `metadata.md` 392, `embedding_app.md` 432. Proposta: `matrix_building` + `pipeline_order` (collegati ad A-006/A-008) poi `datasets`. Rinviato a fine Fase 1: `.claude/history/*` (vedi sotto).
- **Ordine completo e righe**: `00_master_plan.md`.

## DECISIONE DELL'UTENTE (fine ciclo 8): ordine cambiato
La Fase 1 prosegue con **`docs/` adesso**: `docs/setup.md` (36), poi `docs/guides/` (14 file), `docs/dev/` (15), `docs/experiments/` (12), `docs/debugging/` (15). Restano **in fondo alla Fase 1**: `.claude/history/project_changelog.md` (da riga 64), `methods_changelog.md`, `stato_progetto_archive.md` (sola lettura), `.claude/skills/stato-progetto/SKILL.md`, `settings.local.json`, `scheduled_tasks.lock`. Poi `knowledge/notes/`. Motivo: i changelog sono archivi (non descrivono il presente), lunghi e in modifica attiva.

## Prima azione della prossima sessione
1. Leggere `01_assertions_ledger.md` e `02_contradictions_and_open_issues.md` (57 voci, C-001…C-057) prima di auditare.
2. Auditare `docs/guides/` un file alla volta (setup.md è fatto, ciclo 9): ogni comando va confrontato con `src/pipeline/*.py` (`--help`), `config/pipelines/*.json` e `jobs/*.sh`; ogni file/percorso citato deve esistere. Prima: `git status --short | wc -l` e `git diff --stat` (l'utente modifica il codice del clustering) e, se serve, rilanciare `pytest`.

## Esiti già acquisiti
- **Test**: `pytest tests -q` = 5668 passed, 17 skipped, 0 failed (V-022). `code_standards.md` §4 chiede il conteggio esatto: già registrato.
- **Aperti**: 57 voci (C-001…C-057), 0 alte, 24 medie, 33 basse. Ciclo 11: C-054 (tabella parametri SDC), C-055 (media: metadati non arricchiti), C-056 (media: `viz_n_components: 3`), C-057 (`report.md` salvati vs codice). Ciclo 9: C-043…C-046. Ciclo 10: C-047 (partial write con `overwrite:false`), C-048 (media: HC saltati, non aggiunti a 0 nodi), C-049, C-050, C-051 (media: modi `side`/`nihss` mai disponibili), C-052, C-053.
- **Git a inizio ciclo 9**: HEAD `d0ff0b2`; 6 file modificati (`.claude/open_problems.md`, `docs/experiments/{pipelines,s1.4-vol,s2.4-stream}.md`, `.claude/audit/`). I 36 file del ciclo 8 sono stati committati (`57ef5e9`, `d0ff0b2`). I numeri di riga di C-019…C-029 e le righe di `docs/experiments/*` possono essere cambiati: ricontrollare prima di agire. `pytest` non rilanciato nel ciclo 9 (ultimo esito: 5668 passed, 17 skipped a `f577b6a`).
- **(vecchio) ATTENZIONE ciclo 8**: l'utente stava modificando 36 file (clustering tuning, app, test, doc) non committati (B-019). I numeri di riga in C-019…C-029 vanno ricontrollati prima di qualsiasi correzione, e la suite `pytest` va rilanciata.
- **Git**: `logs/` e `summaries/` sono tracciati dal commit `f577b6a` (23-10); `.gitignore` non li ignora più (C-003).
- **Metodo riusabile**: le scansioni AST sono in scratchpad (non versionate): `scan_standards.py` valuta livelli, annotazioni, lunghezza, `except`, codice morto, log. Da riscrivere se serve in Fase 2 (era lenta per la ricerca di riferimenti nei notebook: ~4 min).

## Note da portare avanti
- `lessons_learned.md` #41, ultima frase ("il notebook non è ancora corretto"): probabilmente obsoleta (C-015).
- Per la Fase 2: C-013 (percorsi nei `jobs/`), C-019 (`embedding_plots.py`), C-023 (codice morto), C-024 (mock su funzioni del repo), C-022 (`embedding_app.py` 5540 righe).
- `lessons_learned.md`: verificare #20 (cita `src/retrieval/dataset.py`, ritirato) e #41 (C-015); ogni voce cita un `debug_*.md` o un file: controllare che esistano.
- `.claude/history/project_changelog.md` risulta modificato e non committato (+17 righe) dopo l'inizio dell'audit: non l'ho toccato; se l'utente lo sta modificando, rileggerlo prima di auditarlo.
- `docs/dev/models.md:76` cita una "memory" privata (C-010). `guides/pipeline_order.md:30`: `PYTHONPATH` per `populate_metadata` (A-006). `guides/matrix_building.md`: invocazione vs `jobs/run_build_lesion_matrix.sh` (A-008).
- `results/sdc/clustering/production/` usa nomi `19-10_s2.4-vol_nc{2,12,30}`: confrontare con `docs/experiments/s2.4-vol.md` (C-018).

## Regole operative
- Un file (o ≤150 righe) per ciclo; dopo 1 file grande o 2-3 piccoli fermarsi e aggiornare i 5 file.
- Nessun fix ai file del progetto senza decisione dell'utente. Nessun commit.

- Cose lasciate da `open_problems.md` da riprendere in altri file: `:154` (le voci di `history/` con motivazione ricavata dai vecchi docs), `:187-195` (note di `knowledge/notes/` con citazioni sbagliate: `evaluation_metrics.md` §§1-2 su Dinh 2025/Bicego 2021, `clustering_tuning_guide.md` r.30, `evaluation.md` fonte [6], `lesion_metrics.md` §3.3), `:170` (`docs/experiments/s2.4-vol.md` incompleto), `:198` (cache `thiebaut_2020_replication`), `:200-201` (notebook): verificare ciascuna quando si audita quel file. Non verificabili in locale: X-012 (misure sul cluster).

## Note del ciclo 9 (`docs/setup.md`)
- Nel `docs/` la lista dei pacchetti compare in 3 copie (`setup.md:7`, `README.md:118`, `CLAUDE.md:11`): correggerle insieme (C-002, C-043).
- `docs/guides/clustering.md:158-161` ripete i dati di `nemesis_fallback` (verificati: dadapy 0.3.4, numpy 1.26.4, scikit-learn 1.9.1, python 3.11): da non rifare, vedi P-011.
- Strumenti: su macOS non c'è `timeout`; `conda env create ... --dry-run` funziona (~1 min) e non crea l'ambiente. Dry-run di riferimento in scratchpad (non versionato).
- `pyc` in `scripts/__pycache__` è ignorato da `.gitignore:1`, nessun problema.

## Note del ciclo 10 (`docs/guides/`: tre file piccoli)
- Prefisso ledger `G-` per le guide (G-001…G-041).
- Metodo per le prove eseguibili: copiare la cartella di tuning in `.../scratchpad/<nome>/results/...` e lanciare con `cwd` = scratchpad, `PYTHONPATH` = radice del repo, `python` = `/opt/anaconda3/envs/nemesis/bin/python`. I log e gli output vanno nello scratchpad; verificare con `git status` che il repo non cambi.
- Da riprendere: C-051 si lega a C-023 (codice morto) e al tema "metadata.csv dei tuning": quando si audita `dim_reduction.md`/`docs/dev/models.md` controllare cosa dicono delle colonne di `metadata.csv`. C-050: verificare in `dim_reduction.md` cosa succede con i NaN.
- `docs/dev/fc_matrix.md:38` rimanda a `fc_matrix_building.md` per il caso HC: rileggere insieme a C-048 quando si audita quel file.
- Le guide restanti con `PYTHONPATH` o `--config` mancanti: tenere C-053 come modello.

## Note del ciclo 11 (`sdc_matrix_building`, `dim_reduction`, `evaluate_clustering_tuning`)
- Prefisso `G-` fino a G-082. C-052 (avverbi) è stato esteso, non duplicato.
- **`CLAUDE.md` è cambiato** (riga 49 nuova: `utils/`): tutti i `CLAUDE.md:NN` con NN ≥ 49 nei file di audit sono +1 rispetto ai cicli 1-10 (es. regola "presente" `:54`, notebook `:64`, `@code_standards` `:69`, `@lessons_learned` `:75`). Da riallineare quando si correggono i riferimenti; C-012 (struttura non documenta `.claude/audit/`) resta valido, `utils/` ora è documentato.
- Il working tree contiene lavoro non committato dell'utente su report/testi (`utils/report_texts/`, `src/utils/text_registry.py`, `clustering_tuning_report.py`): le verifiche sui report vanno rifatte se cambia ancora.
- Da verificare più avanti: `dev/models.md` e `dev/config.md` (cosa dicono dei metadati del tuning, C-055); `knowledge/notes/.../tsne.md` (tuning "salvati con init casuale e lr 200", G-059); soglia 0,5 del disconnettoma (G-081) in `dev/anatomical_maps.md`.
- Prova con copia + cwd=scratchpad vale anche per `clustering` (cartella da 14 MB per il tuning più piccolo); i log restano nello scratchpad.
