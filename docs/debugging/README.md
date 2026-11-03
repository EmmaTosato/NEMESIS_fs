# Report di debug

Un report per sessione di debug (`debug_GG_MM_AA.md`), un bug per sezione. Sono un registro cronologico: descrivono il codice **com'era alla data del report**. Questa pagina dice cosa, tra ciò che i report citano, non esiste più.

I pattern di errore generalizzabili stanno in [`.claude/lessons_learned.md`](../../.claude/lessons_learned.md); le decisioni sull'organizzazione del repo in [`.claude/history/project_changelog.md`](../../.claude/history/project_changelog.md).

## Cosa è stato ritirato

| Data | Cosa | Commit |
|---|---|---|
| 15-08-26 | `src/pipeline/dim_reduction_clustering.py`, il suo config e il suo job | `2991ec1` |
| 18-08-26 | `docs/notes/`, `docs/methods/`, `docs/dev/analysis.md`; `knowledge/neuroimaging/` e `knowledge/dim_reduction_clustering/` ora sotto `knowledge/notes/` | |
| 28-08-26 | il box «caveats» di `understanding_umap_report` e il suo test | `fbafb8b` |
| 07-09-26 | `enrich_lesion_metadata.py` (ora `enrich_metadata.py`), `src/features/clinical.py`, i tsv per dataset, `data/derived/clinical_metadata/` | `4de0935` |
| 05-10-26 | `src/retrieval/`, `src/sdc/`, `retrieve_data`, `compute_sdc`, `verify_retrieval`, `data_summary`, `config/{file_patterns,retrieval}*.json`, i job `run_{retrieve_data,compute_sdc,…}.sh`, `docs/dev/retrieval.md`; la funzione `group_of` sta in `src/utils/subject_ids.py` | `d8dbdee` |
| 16-10-26 | `pca_varimax` e `evaluate_pca_varimax`, sostituiti dal metodo `pca` configurabile | `14b6968` |
| 21-10-26 | Evidence Accumulation (`evidence_accumulation`, `assign_clusters_from_cooccurrence`) e i suoi test | `1e43759` |
| 22-10-26 | il controllo `sum(n) == 0` di `build_silhouette_figure`, che ora riceve silhouette per soggetto | `ea619d0` |
| 02-11-26 | `src/analysis/embedding_app.py` (5541 righe): ora è il pacchetto `src/analysis/embedding_app/`, un modulo per pannello. I collegamenti a riga nei report del 17-08 e del 22-08 non si risolvono più; `docs/dev/embedding_app.md` dice quale modulo tiene cosa. `src/pipeline/embedding_app.py` è invariato | `9db71c3`..`2ebaa1b` |

Non esistono neppure `notebooks/fc_lesion_masking.ipynb`, `management/notes/TODO.md` e la skill `~/.claude/skills/silent-failure-audit/SKILL.md`, citati nei report indicati sotto.

Il test di regressione di una sezione che cita un modulo ritirato è stato rimosso con il modulo.

## Quali report ne sono toccati

| Report | Sessione | Cita |
|---|---|---|
| `debug_09_07_26.md` | audit di `src/retrieval/` | `retrieve_data`, skill `silent-failure-audit` |
| `debug_13_07_26.md` | fuzzing della config di retrieval | `retrieve_data`, `config/retrieval.json` |
| `debug_16_07_26.md` | primo run reale di `retrieve_data` | `retrieve_data` |
| `debug_21_07_26.md` | verifica di due atlanti per il paper di Thiebaut de Schotten | `retrieve_data`, `compute_sdc`, `dim_reduction_clustering`, `pca_varimax` |
| `debug_23_07_26.md` | masking FC (WashU) | `notebooks/fc_lesion_masking.ipynb` |
| `debug_27_07_26.md` | controlli sani nella stessa cartella `features/` | `src/retrieval/dataset.py` (ora `src/utils/subject_ids.py`), `compute_sdc`, `docs/notes/` |
| `debug_28_07_26.md` | regress-out del volume lesionale | `dim_reduction_clustering`, `compute_sdc`, `docs/methods/` |
| `debug_11_08_26.md` | code review dell'intero repo | `src/retrieval/`, `src/sdc/`, `dim_reduction_clustering` |
| `debug_17_08_26.md` | audit di correttezza teorica (prima `AUDIT_FINDINGS.md`) | quasi tutti gli elementi della tabella sopra, `src/analysis/embedding_app.py` compreso (7 volte, con numero di riga) |
| `debug_22_08_26.md` | triage dei finding MEDIUM e LOW dell'audit del 17-08 | `dim_reduction_clustering`, `enrich_lesion_metadata`, `pca_varimax`, Evidence Accumulation, `docs/notes/`, `embedding_app.py` |
| `debug_25_08_26.md` | tuning UMAP su `25-08_s1.2` | `management/notes/TODO.md`, Evidence Accumulation |
| `debug_26_08_26.md` | report «Understanding UMAP» | `enrich_lesion_metadata`, `clinical.py` |
| `debug_02_09_26.md` | ristrutturazione dei metadati | `enrich_lesion_metadata`, `clinical_metadata` |
| `debug_10_09_26.md` | tuning del clustering su `s2.2-vol` | nessuno |
| `debug_21_10_26.md` | suite `hypothesis` e bug trovati | Evidence Accumulation (§4, superata) |

In `debug_21_10_26.md` le sezioni superate lo dicono nel testo (§4, §18, §15). Nei report del 17-08 e del 22-08 le sezioni ritirate sono segnate «Superato» e i cambiamenti successivi stanno nelle righe «Stato attuale».
