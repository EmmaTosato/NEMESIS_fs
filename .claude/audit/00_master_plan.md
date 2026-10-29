# 00 — Master plan dell'audit

Legenda: `[ ] TODO` · `[~] IN CORSO` · `[x] COMPLETATO`. Righe = `wc -l` al momento del bootstrap (2026-10-26); `bin` = binario, non letto riga per riga.
Ordine di lettura Fase 1: `.claude/` → `docs/` → `knowledge/notes/`, nell'ordine indicato dall'utente.

## FASE 1 — Doc, Knowledge & `.claude`

### 1.1 `.claude/` (file principali, ordine dell'utente) (6 file)

| File | Stato | Righe | Ultima riga analizzata |
|---|---|---|---|
| `.claude/CLAUDE.md` | [x] COMPLETATO | 76 | 76 |
| `.claude/stato_progetto.md` | [x] COMPLETATO | 50 | 50 |
| `.claude/code_standards.md` | [x] COMPLETATO | 123 | 123 |
| `.claude/branch_alignment.md` | [x] COMPLETATO | 40 | 40 |
| `.claude/open_problems.md` | [x] COMPLETATO | 215 | 215 |
| `.claude/lessons_learned.md` | [x] COMPLETATO | 191 | 191 |

### 1.1b `.claude/history/` (4 file)

| File | Stato | Righe | Ultima riga analizzata |
|---|---|---|---|
| `.claude/history/data_changelog.md` | [x] COMPLETATO | 223 | 223 |
| `.claude/history/methods_changelog.md` | [x] COMPLETATO | 992 | 992 |
| `.claude/history/project_changelog.md` | [x] COMPLETATO | 972 | 972 |
| `.claude/history/stato_progetto_archive.md` | [x] COMPLETATO (sola lettura: solo riferimenti) | 587 | 587 |

### 1.1c `.claude/` extra, non elencati dall'utente (skills, impostazioni) (4 file)

| File | Stato | Righe | Ultima riga analizzata |
|---|---|---|---|
| `.claude/skills/history/SKILL.md` | [x] COMPLETATO | 79 | 79 |
| `.claude/skills/stato-progetto/SKILL.md` | [x] COMPLETATO | 53 | 53 |
| `.claude/settings.local.json` | [x] COMPLETATO | 8 | 8 |
| `.claude/scheduled_tasks.lock` | [x] COMPLETATO (stantio, C-104) | bin | - |

### 1.2a `docs/setup.md` (1 file)

| File | Stato | Righe | Ultima riga analizzata |
|---|---|---|---|
| `docs/setup.md` | [x] COMPLETATO | 36 | 36 |

### 1.2 `docs/guides/` (14 file)

| File | Stato | Righe | Ultima riga analizzata |
|---|---|---|---|
| `docs/guides/clustering.md` | [x] COMPLETATO | 281 | 281 |
| `docs/guides/datasets.md` | [x] COMPLETATO | 198 | 198 |
| `docs/guides/dim_reduction.md` | [x] COMPLETATO | 134 | 134 |
| `docs/guides/embedding_app.md` | [x] COMPLETATO | 433 (432 al bootstrap) | 433 |
| `docs/guides/evaluate_clustering_tuning.md` | [x] COMPLETATO | 121 | 121 |
| `docs/guides/evaluate_dim_reduction_tuning.md` | [x] COMPLETATO | 43 | 43 |
| `docs/guides/evaluation.md` | [x] COMPLETATO | 123 (259 al bootstrap; riscritto da `591e078`) | 123 |
| `docs/guides/exploration.md` | [x] COMPLETATO | 215 (216 al bootstrap) | 215 |
| `docs/guides/fc_matrix_building.md` | [x] COMPLETATO | 57 | 57 |
| `docs/guides/matrix_building.md` | [x] COMPLETATO | 139 | 139 |
| `docs/guides/metadata.md` | [x] COMPLETATO | 392 | 392 |
| `docs/guides/pipeline_order.md` | [x] COMPLETATO | 198 | 198 |
| `docs/guides/sdc_matrix_building.md` | [x] COMPLETATO | 117 | 117 |
| `docs/guides/understanding_umap_report.md` | [x] COMPLETATO | 59 | 59 |

### 1.2 `docs/dev/` (15 file)

| File | Stato | Righe | Ultima riga analizzata |
|---|---|---|---|
| `docs/dev/anatomical_maps.md` | [x] COMPLETATO | 104 | 104 |
| `docs/dev/cluster_comparison.md` | [x] COMPLETATO | 115 | 115 |
| `docs/dev/cluster_composition.md` | [x] COMPLETATO | 37 | 37 |
| `docs/dev/cluster_description.md` | [x] COMPLETATO | 205 | 205 |
| `docs/dev/cluster_drivers.md` | [x] COMPLETATO | 33 | 33 |
| `docs/dev/config.md` | [x] COMPLETATO | 81 | 81 |
| `docs/dev/covariance_pca.md` | [x] COMPLETATO | 129 | 129 |
| `docs/dev/design_patterns.md` | [x] COMPLETATO | 64 | 64 |
| `docs/dev/fc_matrix.md` | [x] COMPLETATO | 57 (55 al bootstrap) | 57 |
| `docs/dev/lesion_matrix.md` | [x] COMPLETATO | 135 | 135 |
| `docs/dev/metadata.md` | [x] COMPLETATO | 334 | 334 |
| `docs/dev/models.md` | [x] COMPLETATO | 340 (342 al bootstrap) | 340 (scansione automatica dei simboli; paragrafi lunghi letti a campione) |
| `docs/dev/pipeline_flow.md` | [x] COMPLETATO | 111 | 111 |
| `docs/dev/plotting.md` | [x] COMPLETATO | 118 | 118 |
| `docs/dev/sdc_matrix.md` | [x] COMPLETATO | 164 | 164 |

### 1.2 `docs/experiments/` (12 file)

| File | Stato | Righe | Ultima riga analizzata |
|---|---|---|---|
| `docs/experiments/README.md` | [x] COMPLETATO | 48 | 48 |
| `docs/experiments/lineage.md` | [x] COMPLETATO | 49 | 49 |
| `docs/experiments/pipelines.md` | [x] COMPLETATO | 256 | 256 |
| `docs/experiments/s1.1-vol.md` | [x] COMPLETATO | 90 | 90 |
| `docs/experiments/s1.2-vol.md` | [x] COMPLETATO | 122 | 122 |
| `docs/experiments/s1.3-vol.md` | [x] COMPLETATO | 32 | 32 |
| `docs/experiments/s1.4-vol.md` | [x] COMPLETATO | 122 | 122 |
| `docs/experiments/s2.1-schaefer-200-tian-s2.md` | [x] COMPLETATO | 71 | 71 |
| `docs/experiments/s2.2-vol.md` | [x] COMPLETATO | 120 | 120 |
| `docs/experiments/s2.3-stream.md` | [x] COMPLETATO | 33 | 33 |
| `docs/experiments/s2.4-stream.md` | [x] COMPLETATO | 61 | 61 |
| `docs/experiments/s2.4-vol.md` | [x] COMPLETATO | 251 | 251 |

### 1.2 `docs/debugging/` (15 file)

| File | Stato | Righe | Ultima riga analizzata |
|---|---|---|---|
| `docs/debugging/debug_02_09_26.md` | [x] COMPLETATO | 76 | 76 |
| `docs/debugging/debug_09_07_26.md` | [x] COMPLETATO | 100 | 100 |
| `docs/debugging/debug_10_09_26.md` | [x] COMPLETATO | 83 | 83 |
| `docs/debugging/debug_11_08_26.md` | [x] COMPLETATO | 253 | 253 |
| `docs/debugging/debug_13_07_26.md` | [x] COMPLETATO | 65 | 65 |
| `docs/debugging/debug_16_07_26.md` | [x] COMPLETATO | 23 | 23 |
| `docs/debugging/debug_17_08_26.md` | [x] COMPLETATO | 2320 | 2320 |
| `docs/debugging/debug_21_07_26.md` | [x] COMPLETATO | 65 | 65 |
| `docs/debugging/debug_21_10_26.md` | [x] COMPLETATO | 300 | 300 (sezioni lette a campione; tutti i 19 fix verificati nel codice, G-451) |
| `docs/debugging/debug_22_08_26.md` | [x] COMPLETATO | 555 | 555 |
| `docs/debugging/debug_23_07_26.md` | [x] COMPLETATO | 35 | 35 |
| `docs/debugging/debug_25_08_26.md` | [x] COMPLETATO | 25 | 25 |
| `docs/debugging/debug_26_08_26.md` | [x] COMPLETATO | 131 | 131 |
| `docs/debugging/debug_27_07_26.md` | [x] COMPLETATO | 32 | 32 |
| `docs/debugging/debug_28_07_26.md` | [x] COMPLETATO | 30 | 30 |

### 1.2e altri file direttamente in `docs/`: nessuno

### 1.3 `knowledge/notes/dim_reduction_clustering/` (22 file)

| File | Stato | Righe | Ultima riga analizzata |
|---|---|---|---|
| `knowledge/notes/dim_reduction_clustering/challenge_of_clustering_after_dim_reduction.md` | [x] COMPLETATO (ciclo 23: letto riga per riga; formule, parametri e citazioni verificati, G-503…G-531) | 76 | -|
| `knowledge/notes/dim_reduction_clustering/clustering_literature_survey.md` | [x] COMPLETATO (ciclo 23: letto riga per riga; formule, parametri e citazioni verificati, G-503…G-531) | 112 | -|
| `knowledge/notes/dim_reduction_clustering/clustering_methods/README.md` | [x] COMPLETATO (ciclo 23: letto riga per riga; formule, parametri e citazioni verificati, G-503…G-531) | 50 | -|
| `knowledge/notes/dim_reduction_clustering/clustering_methods/adp.md` | [x] COMPLETATO (ciclo 23: letto riga per riga; formule, parametri e citazioni verificati, G-503…G-531) | 219 | -|
| `knowledge/notes/dim_reduction_clustering/clustering_methods/agglomerative.md` | [x] COMPLETATO (ciclo 23: letto riga per riga; formule, parametri e citazioni verificati, G-503…G-531) | 195 | -|
| `knowledge/notes/dim_reduction_clustering/clustering_methods/evaluation_metrics.md` | [x] COMPLETATO (ciclo 23: letto riga per riga; formule, parametri e citazioni verificati, G-503…G-531) | 270 | -|
| `knowledge/notes/dim_reduction_clustering/clustering_methods/gmm.md` | [x] COMPLETATO (ciclo 23: letto riga per riga; formule, parametri e citazioni verificati, G-503…G-531) | 175 | -|
| `knowledge/notes/dim_reduction_clustering/clustering_methods/hdbscan.md` | [x] COMPLETATO (ciclo 23: letto riga per riga; formule, parametri e citazioni verificati, G-503…G-531) | 246 | -|
| `knowledge/notes/dim_reduction_clustering/clustering_methods/kmeans.md` | [x] COMPLETATO (ciclo 23: letto riga per riga; formule, parametri e citazioni verificati, G-503…G-531) | 153 | -|
| `knowledge/notes/dim_reduction_clustering/clustering_methods/spectral.md` | [x] COMPLETATO (ciclo 23: letto riga per riga; formule, parametri e citazioni verificati, G-503…G-531) | 174 | -|
| `knowledge/notes/dim_reduction_clustering/clustering_tuning_guide.md` | [x] COMPLETATO (letto per intero, ciclo 22) | 232 | -|
| `knowledge/notes/dim_reduction_clustering/dim_reduction_literature_survey.md` | [x] COMPLETATO (ciclo 23: letto riga per riga; formule, parametri e citazioni verificati, G-503…G-531) | 104 | -|
| `knowledge/notes/dim_reduction_clustering/dim_reduction_methods/README.md` | [x] COMPLETATO (ciclo 23: letto riga per riga; formule, parametri e citazioni verificati, G-503…G-531) | 56 | -|
| `knowledge/notes/dim_reduction_clustering/dim_reduction_methods/evaluation.md` | [x] COMPLETATO (ciclo 23: letto riga per riga; formule, parametri e citazioni verificati, G-503…G-531) | 85 | -|
| `knowledge/notes/dim_reduction_clustering/dim_reduction_methods/pacmap.md` | [x] COMPLETATO (ciclo 23: letto riga per riga; formule, parametri e citazioni verificati, G-503…G-531) | 121 | -|
| `knowledge/notes/dim_reduction_clustering/dim_reduction_methods/pca.md` | [x] COMPLETATO (ciclo 23: letto riga per riga; formule, parametri e citazioni verificati, G-503…G-531) | 119 | -|
| `knowledge/notes/dim_reduction_clustering/dim_reduction_methods/pca_varimax.md` | [x] COMPLETATO (ciclo 23: letto riga per riga; formule, parametri e citazioni verificati, G-503…G-531) | 104 | -|
| `knowledge/notes/dim_reduction_clustering/dim_reduction_methods/tsne.md` | [x] COMPLETATO (ciclo 23: letto riga per riga; formule, parametri e citazioni verificati, G-503…G-531) | 140 | -|
| `knowledge/notes/dim_reduction_clustering/dim_reduction_methods/umap.md` | [x] COMPLETATO (ciclo 23: letto riga per riga; formule, parametri e citazioni verificati, G-503…G-531) | 130 | -|
| `knowledge/notes/dim_reduction_clustering/dim_reduction_tuning_guide.md` | [x] COMPLETATO (ciclo 23: letto riga per riga; formule, parametri e citazioni verificati, G-503…G-531) | 100 | -|
| `knowledge/notes/dim_reduction_clustering/employed_dim_reduction_methods.md` | [x] COMPLETATO (ciclo 23: letto riga per riga; formule, parametri e citazioni verificati, G-503…G-531) | 339 | -|
| `knowledge/notes/dim_reduction_clustering/hdbscan_package.md` | [x] COMPLETATO (ciclo 23: letto riga per riga; formule, parametri e citazioni verificati, G-503…G-531) | 108 | -|

### 1.3 `knowledge/notes/neuroimaging/` (7 file)

| File | Stato | Righe | Ultima riga analizzata |
|---|---|---|---|
| `knowledge/notes/neuroimaging/disconnectome_bcbtoolkit.md` | [x] COMPLETATO (ciclo 23: letto riga per riga; formule, parametri e citazioni verificati, G-503…G-531) | 268 | -|
| `knowledge/notes/neuroimaging/fc_lesion_masking.md` | [x] COMPLETATO (ciclo 23: letto riga per riga; formule, parametri e citazioni verificati, G-503…G-531) | 217 | -|
| `knowledge/notes/neuroimaging/lesion_laterality.md` | [x] COMPLETATO (ciclo 23: letto riga per riga; formule, parametri e citazioni verificati, G-503…G-531) | 145 | -|
| `knowledge/notes/neuroimaging/lesion_location.md` | [x] COMPLETATO (ciclo 23: letto riga per riga; formule, parametri e citazioni verificati, G-503…G-531) | 122 | -|
| `knowledge/notes/neuroimaging/lesion_metrics.md` | [x] COMPLETATO (ciclo 23: letto riga per riga; formule, parametri e citazioni verificati, G-503…G-531) | 161 | -|
| `knowledge/notes/neuroimaging/lesion_resampling.md` | [x] COMPLETATO (ciclo 23: letto riga per riga; formule, parametri e citazioni verificati, G-503…G-531) | 175 | -|
| `knowledge/notes/neuroimaging/template_and_grids.md` | [x] COMPLETATO (ciclo 23: letto riga per riga; formule, parametri e citazioni verificati, G-503…G-531) | 221 | -|

### 1.3 `knowledge/notes/stroke_literature/` (3 file)

| File | Stato | Righe | Ultima riga analizzata |
|---|---|---|---|
| `knowledge/notes/stroke_literature/scope_by_category.md` | [x] COMPLETATO (ciclo 24: letto riga per riga; numeri e affermazioni qualitative confrontati con i paper, G-533…G-552) | 71 | -|
| `knowledge/notes/stroke_literature/summaries_core.md` | [x] COMPLETATO (ciclo 24: letto riga per riga; numeri e affermazioni qualitative confrontati con i paper, G-533…G-552) | 721 | -|
| `knowledge/notes/stroke_literature/summaries_related.md` | [x] COMPLETATO (ciclo 24: letto riga per riga; numeri e affermazioni qualitative confrontati con i paper, G-533…G-552) | 216 | -|

## FASE 2 — Codebase, Config, Tests, Notebooks, Summaries & Logs

### 2.1 `config/` (18 file)

| File | Stato | Righe | Ultima riga analizzata |
|---|---|---|---|
| `config/pipelines/build_excluded_subjects.json` | [ ] TODO | 54 | 0 |
| `config/pipelines/build_fc_matrix.json` | [ ] TODO | 22 | 0 |
| `config/pipelines/build_lesion_matrix.json` | [ ] TODO | 36 | 0 |
| `config/pipelines/build_sdc_matrix.json` | [ ] TODO | 28 | 0 |
| `config/pipelines/clustering.json` | [ ] TODO | 43 | 0 |
| `config/pipelines/compute_lesion_metadata.json` | [ ] TODO | 58 | 0 |
| `config/pipelines/compute_sdc_metadata.json` | [ ] TODO | 36 | 0 |
| `config/pipelines/dim_reduction.json` | [ ] TODO | 22 | 0 |
| `config/pipelines/enrich_metadata.json` | [ ] TODO | 43 | 0 |
| `config/pipelines/evaluate_clustering_tuning.json` | [ ] TODO | 27 | 0 |
| `config/pipelines/evaluate_dim_reduction_tuning.json` | [ ] TODO | 10 | 0 |
| `config/pipelines/mask_fc.json` | [ ] TODO | 36 | 0 |
| `config/pipelines/populate_metadata.json` | [ ] TODO | 20 | 0 |
| `config/registry/clustering_evaluations.json` | [ ] TODO | 12 | 0 |
| `config/registry/metadata_sources.json` | [ ] TODO | 34 | 0 |
| `config/registry/params_clustering.json` | [ ] TODO | 73 | 0 |
| `config/registry/params_reduction.json` | [ ] TODO | 72 | 0 |
| `config/registry/params_reduction_sdc.json` | [ ] TODO | 129 | 0 |

### 2.2 `src/` (sorgenti, esclusi `__init__.py` vuoti inclusi per completezza) (76 file)

| File | Stato | Righe | Ultima riga analizzata |
|---|---|---|---|
| `src/analysis/__init__.py` | [ ] TODO | 0 | 0 |
| `src/analysis/adp.py` | [ ] TODO | 364 | 0 |
| `src/analysis/anatomical_maps.py` | [ ] TODO | 393 | 0 |
| `src/analysis/background_cache.py` | [ ] TODO | 67 | 0 |
| `src/analysis/build_config.py` | [ ] TODO | 718 | 0 |
| `src/analysis/cluster_comparison.py` | [ ] TODO | 273 | 0 |
| `src/analysis/cluster_composition.py` | [ ] TODO | 177 | 0 |
| `src/analysis/cluster_description.py` | [ ] TODO | 399 | 0 |
| `src/analysis/cluster_drivers.py` | [ ] TODO | 157 | 0 |
| `src/analysis/cluster_overview.py` | [ ] TODO | 77 | 0 |
| `src/analysis/cluster_pair.py` | [ ] TODO | 302 | 0 |
| `src/analysis/cluster_quality.py` | [ ] TODO | 156 | 0 |
| `src/analysis/clustering.py` | [ ] TODO | 100 | 0 |
| `src/analysis/clustering_evaluation.py` | [ ] TODO | 599 | 0 |
| `src/analysis/clustering_tuning.py` | [ ] TODO | 1007 | 0 |
| `src/analysis/clustering_tuning_analysis.py` | [ ] TODO | 415 | 0 |
| `src/analysis/clustering_tuning_evaluations.py` | [ ] TODO | 320 | 0 |
| `src/analysis/clustering_tuning_report.py` | [ ] TODO | 550 | 0 |
| `src/analysis/component_map_plots.py` | [ ] TODO | 53 | 0 |
| `src/analysis/component_maps.py` | [ ] TODO | 168 | 0 |
| `src/analysis/consensus_clustering.py` | [ ] TODO | 190 | 0 |
| `src/analysis/covariance_pca.py` | [ ] TODO | 521 | 0 |
| `src/analysis/dbcv.py` | [ ] TODO | 95 | 0 |
| `src/analysis/dendrogram_splits.py` | [ ] TODO | 309 | 0 |
| `src/analysis/distances.py` | [ ] TODO | 215 | 0 |
| `src/analysis/embedding_app.py` | [ ] TODO | 5540 | 0 |
| `src/analysis/embedding_coloring.py` | [ ] TODO | 387 | 0 |
| `src/analysis/embedding_plots.py` | [ ] TODO | 135 | 0 |
| `src/analysis/model_config.py` | [ ] TODO | 352 | 0 |
| `src/analysis/params.py` | [ ] TODO | 374 | 0 |
| `src/analysis/partition_shape.py` | [ ] TODO | 45 | 0 |
| `src/analysis/pca_evaluation.py` | [ ] TODO | 252 | 0 |
| `src/analysis/pca_method.py` | [ ] TODO | 187 | 0 |
| `src/analysis/plotting.py` | [ ] TODO | 1300 | 0 |
| `src/analysis/prediction.py` | [ ] TODO | 180 | 0 |
| `src/analysis/raw_distances.py` | [ ] TODO | 88 | 0 |
| `src/analysis/reduction.py` | [ ] TODO | 215 | 0 |
| `src/analysis/tuning.py` | [ ] TODO | 222 | 0 |
| `src/analysis/tuning_embeddings.py` | [ ] TODO | 159 | 0 |
| `src/analysis/tuning_evaluations.py` | [ ] TODO | 256 | 0 |
| `src/analysis/tuning_match.py` | [ ] TODO | 152 | 0 |
| `src/analysis/understanding_umap_report.py` | [ ] TODO | 1202 | 0 |
| `src/features/__init__.py` | [ ] TODO | 0 | 0 |
| `src/features/functional.py` | [ ] TODO | 460 | 0 |
| `src/features/lesion.py` | [ ] TODO | 723 | 0 |
| `src/features/lesion_correction.py` | [ ] TODO | 32 | 0 |
| `src/features/lesion_location.py` | [ ] TODO | 280 | 0 |
| `src/features/parcellated_csv.py` | [ ] TODO | 303 | 0 |
| `src/features/sdc.py` | [ ] TODO | 634 | 0 |
| `src/features/subject_discovery.py` | [ ] TODO | 133 | 0 |
| `src/pipeline/__init__.py` | [ ] TODO | 0 | 0 |
| `src/pipeline/build_excluded_subjects.py` | [ ] TODO | 420 | 0 |
| `src/pipeline/build_fc_matrix.py` | [ ] TODO | 275 | 0 |
| `src/pipeline/build_lesion_matrix.py` | [ ] TODO | 386 | 0 |
| `src/pipeline/build_sdc_matrix.py` | [ ] TODO | 450 | 0 |
| `src/pipeline/calibrate_lesion_side_threshold.py` | [ ] TODO | 281 | 0 |
| `src/pipeline/clustering.py` | [ ] TODO | 1210 | 0 |
| `src/pipeline/compute_lesion_metadata.py` | [ ] TODO | 303 | 0 |
| `src/pipeline/compute_sdc_metadata.py` | [ ] TODO | 253 | 0 |
| `src/pipeline/dim_reduction.py` | [ ] TODO | 688 | 0 |
| `src/pipeline/embedding_app.py` | [ ] TODO | 169 | 0 |
| `src/pipeline/enrich_metadata.py` | [ ] TODO | 1125 | 0 |
| `src/pipeline/evaluate_clustering_tuning.py` | [ ] TODO | 93 | 0 |
| `src/pipeline/evaluate_dim_reduction_tuning.py` | [ ] TODO | 78 | 0 |
| `src/pipeline/generate_understanding_umap_report.py` | [ ] TODO | 54 | 0 |
| `src/pipeline/mask_fc.py` | [ ] TODO | 247 | 0 |
| `src/pipeline/plot_tuning_embedding_3d.py` | [ ] TODO | 144 | 0 |
| `src/pipeline/populate_metadata.py` | [ ] TODO | 446 | 0 |
| `src/pipeline/replot_dim_reduction.py` | [ ] TODO | 186 | 0 |
| `src/utils/__init__.py` | [ ] TODO | 0 | 0 |
| `src/utils/artifacts.py` | [ ] TODO | 227 | 0 |
| `src/utils/logging_setup.py` | [ ] TODO | 45 | 0 |
| `src/utils/metadata_sources.py` | [ ] TODO | 47 | 0 |
| `src/utils/participants.py` | [ ] TODO | 233 | 0 |
| `src/utils/run_log.py` | [ ] TODO | 141 | 0 |
| `src/utils/subject_ids.py` | [ ] TODO | 34 | 0 |

### 2.3 `scripts/` (2 file)

| File | Stato | Righe | Ultima riga analizzata |
|---|---|---|---|
| `scripts/archive_local_raw_data.py` | [ ] TODO | 404 | 0 |
| `scripts/build_dataset_summary_table.py` | [ ] TODO | 164 | 0 |

### 2.4 `jobs/` (non elencato dall'utente, richiesto da `CLAUDE.md`) (18 file)

| File | Stato | Righe | Ultima riga analizzata |
|---|---|---|---|
| `jobs/run_build_dataset_summary_table.sh` | [ ] TODO | 25 | 0 |
| `jobs/run_build_excluded_subjects.sh` | [ ] TODO | 25 | 0 |
| `jobs/run_build_fc_matrix.sh` | [ ] TODO | 25 | 0 |
| `jobs/run_build_lesion_matrix.sh` | [ ] TODO | 25 | 0 |
| `jobs/run_build_sdc_matrix.sh` | [ ] TODO | 25 | 0 |
| `jobs/run_calibrate_lesion_side_threshold.sh` | [ ] TODO | 31 | 0 |
| `jobs/run_clustering.sh` | [ ] TODO | 25 | 0 |
| `jobs/run_compute_lesion_metadata.sh` | [ ] TODO | 32 | 0 |
| `jobs/run_compute_sdc_metadata.sh` | [ ] TODO | 32 | 0 |
| `jobs/run_dim_reduction.sh` | [ ] TODO | 25 | 0 |
| `jobs/run_enrich_metadata.sh` | [ ] TODO | 25 | 0 |
| `jobs/run_evaluate_clustering_tuning.sh` | [ ] TODO | 25 | 0 |
| `jobs/run_evaluate_dim_reduction_tuning.sh` | [ ] TODO | 25 | 0 |
| `jobs/run_generate_understanding_umap_report.sh` | [ ] TODO | 29 | 0 |
| `jobs/run_mask_fc.sh` | [ ] TODO | 25 | 0 |
| `jobs/run_plot_tuning_embedding_3d.sh` | [ ] TODO | 34 | 0 |
| `jobs/run_populate_metadata.sh` | [ ] TODO | 25 | 0 |
| `jobs/run_replot_dim_reduction.sh` | [ ] TODO | 25 | 0 |

### 2.5 `tests/` (135 file)

| File | Stato | Righe | Ultima riga analizzata |
|---|---|---|---|
| `tests/__init__.py` | [ ] TODO | 0 | 0 |
| `tests/conftest.py` | [ ] TODO | 39 | 0 |
| `tests/factories/__init__.py` | [ ] TODO | 6 | 0 |
| `tests/factories/ids.py` | [ ] TODO | 18 | 0 |
| `tests/factories/lesion_dataset.py` | [ ] TODO | 101 | 0 |
| `tests/factories/matrices.py` | [ ] TODO | 42 | 0 |
| `tests/integration/__init__.py` | [ ] TODO | 0 | 0 |
| `tests/integration/test_build_fc_matrix_paths.py` | [ ] TODO | 222 | 0 |
| `tests/integration/test_build_fc_matrix_pipeline.py` | [ ] TODO | 194 | 0 |
| `tests/integration/test_build_lesion_matrix_pipeline.py` | [ ] TODO | 414 | 0 |
| `tests/integration/test_build_sdc_matrix_pipeline.py` | [ ] TODO | 511 | 0 |
| `tests/integration/test_clustering_pipeline.py` | [ ] TODO | 2318 | 0 |
| `tests/integration/test_compute_sdc_metadata_paths.py` | [ ] TODO | 198 | 0 |
| `tests/integration/test_dim_reduction_pipeline.py` | [ ] TODO | 1261 | 0 |
| `tests/integration/test_enrich_metadata_paths.py` | [ ] TODO | 498 | 0 |
| `tests/integration/test_evaluate_clustering_tuning_pipeline.py` | [ ] TODO | 259 | 0 |
| `tests/integration/test_evaluate_dim_reduction_tuning_paths.py` | [ ] TODO | 176 | 0 |
| `tests/integration/test_mask_fc_paths.py` | [ ] TODO | 226 | 0 |
| `tests/integration/test_mask_fc_pipeline.py` | [ ] TODO | 264 | 0 |
| `tests/integration/test_pipeline_chain_e2e.py` | [ ] TODO | 183 | 0 |
| `tests/integration/test_plot_tuning_embedding_3d_paths.py` | [ ] TODO | 196 | 0 |
| `tests/integration/test_populate_metadata_paths.py` | [ ] TODO | 312 | 0 |
| `tests/unit/__init__.py` | [ ] TODO | 0 | 0 |
| `tests/unit/location_fixtures.py` | [ ] TODO | 128 | 0 |
| `tests/unit/test_adp.py` | [ ] TODO | 220 | 0 |
| `tests/unit/test_anatomical_maps.py` | [ ] TODO | 447 | 0 |
| `tests/unit/test_archive_local_raw_data.py` | [ ] TODO | 352 | 0 |
| `tests/unit/test_artifacts.py` | [ ] TODO | 202 | 0 |
| `tests/unit/test_background_cache.py` | [ ] TODO | 66 | 0 |
| `tests/unit/test_build_config.py` | [ ] TODO | 525 | 0 |
| `tests/unit/test_build_dataset_summary_table_paths.py` | [ ] TODO | 169 | 0 |
| `tests/unit/test_build_excluded_subjects.py` | [ ] TODO | 440 | 0 |
| `tests/unit/test_calibrate_lesion_side_threshold.py` | [ ] TODO | 85 | 0 |
| `tests/unit/test_calibrate_lesion_side_threshold_paths.py` | [ ] TODO | 209 | 0 |
| `tests/unit/test_cluster_comparison.py` | [ ] TODO | 194 | 0 |
| `tests/unit/test_cluster_composition.py` | [ ] TODO | 177 | 0 |
| `tests/unit/test_cluster_description.py` | [ ] TODO | 384 | 0 |
| `tests/unit/test_cluster_drivers.py` | [ ] TODO | 151 | 0 |
| `tests/unit/test_cluster_overview.py` | [ ] TODO | 104 | 0 |
| `tests/unit/test_cluster_pair.py` | [ ] TODO | 267 | 0 |
| `tests/unit/test_cluster_quality.py` | [ ] TODO | 141 | 0 |
| `tests/unit/test_clustering.py` | [ ] TODO | 106 | 0 |
| `tests/unit/test_clustering_evaluation.py` | [ ] TODO | 771 | 0 |
| `tests/unit/test_clustering_tuning.py` | [ ] TODO | 754 | 0 |
| `tests/unit/test_clustering_tuning_analysis.py` | [ ] TODO | 454 | 0 |
| `tests/unit/test_clustering_tuning_evaluations.py` | [ ] TODO | 305 | 0 |
| `tests/unit/test_clustering_tuning_report.py` | [ ] TODO | 416 | 0 |
| `tests/unit/test_component_maps.py` | [ ] TODO | 165 | 0 |
| `tests/unit/test_compute_lesion_metadata.py` | [ ] TODO | 304 | 0 |
| `tests/unit/test_compute_sdc_metadata.py` | [ ] TODO | 272 | 0 |
| `tests/unit/test_consensus_clustering.py` | [ ] TODO | 148 | 0 |
| `tests/unit/test_covariance_pca.py` | [ ] TODO | 515 | 0 |
| `tests/unit/test_dbcv.py` | [ ] TODO | 119 | 0 |
| `tests/unit/test_dendrogram_splits.py` | [ ] TODO | 300 | 0 |
| `tests/unit/test_distances.py` | [ ] TODO | 153 | 0 |
| `tests/unit/test_embedding_app.py` | [ ] TODO | 2020 | 0 |
| `tests/unit/test_embedding_app_all_clusters.py` | [ ] TODO | 329 | 0 |
| `tests/unit/test_embedding_app_comparison.py` | [ ] TODO | 475 | 0 |
| `tests/unit/test_embedding_app_dendrogram.py` | [ ] TODO | 523 | 0 |
| `tests/unit/test_embedding_app_pca_maps.py` | [ ] TODO | 233 | 0 |
| `tests/unit/test_embedding_app_pickers.py` | [ ] TODO | 413 | 0 |
| `tests/unit/test_embedding_app_quality.py` | [ ] TODO | 539 | 0 |
| `tests/unit/test_embedding_app_tabs.py` | [ ] TODO | 194 | 0 |
| `tests/unit/test_embedding_coloring.py` | [ ] TODO | 433 | 0 |
| `tests/unit/test_embedding_plots.py` | [ ] TODO | 151 | 0 |
| `tests/unit/test_embedding_plots_paths.py` | [ ] TODO | 150 | 0 |
| `tests/unit/test_enrich_metadata.py` | [ ] TODO | 1213 | 0 |
| `tests/unit/test_features_functional.py` | [ ] TODO | 644 | 0 |
| `tests/unit/test_features_lesion.py` | [ ] TODO | 909 | 0 |
| `tests/unit/test_features_parcellated_csv.py` | [ ] TODO | 137 | 0 |
| `tests/unit/test_features_sdc.py` | [ ] TODO | 1364 | 0 |
| `tests/unit/test_generate_understanding_umap_report_pipeline.py` | [ ] TODO | 94 | 0 |
| `tests/unit/test_lesion_correction.py` | [ ] TODO | 42 | 0 |
| `tests/unit/test_lesion_location.py` | [ ] TODO | 231 | 0 |
| `tests/unit/test_logging_setup.py` | [ ] TODO | 56 | 0 |
| `tests/unit/test_model_config.py` | [ ] TODO | 713 | 0 |
| `tests/unit/test_params.py` | [ ] TODO | 471 | 0 |
| `tests/unit/test_participants_registry.py` | [ ] TODO | 230 | 0 |
| `tests/unit/test_partition_shape.py` | [ ] TODO | 38 | 0 |
| `tests/unit/test_pca_evaluation.py` | [ ] TODO | 396 | 0 |
| `tests/unit/test_pca_method.py` | [ ] TODO | 237 | 0 |
| `tests/unit/test_pipeline_embedding_app.py` | [ ] TODO | 185 | 0 |
| `tests/unit/test_plotting.py` | [ ] TODO | 843 | 0 |
| `tests/unit/test_populate_metadata.py` | [ ] TODO | 297 | 0 |
| `tests/unit/test_prediction.py` | [ ] TODO | 126 | 0 |
| `tests/unit/test_prop_adp.py` | [ ] TODO | 533 | 0 |
| `tests/unit/test_prop_artifacts.py` | [ ] TODO | 349 | 0 |
| `tests/unit/test_prop_build_config.py` | [ ] TODO | 490 | 0 |
| `tests/unit/test_prop_cluster_comparison.py` | [ ] TODO | 279 | 0 |
| `tests/unit/test_prop_cluster_composition.py` | [ ] TODO | 197 | 0 |
| `tests/unit/test_prop_cluster_description.py` | [ ] TODO | 207 | 0 |
| `tests/unit/test_prop_cluster_drivers.py` | [ ] TODO | 184 | 0 |
| `tests/unit/test_prop_cluster_pair.py` | [ ] TODO | 287 | 0 |
| `tests/unit/test_prop_cluster_quality.py` | [ ] TODO | 173 | 0 |
| `tests/unit/test_prop_clustering.py` | [ ] TODO | 174 | 0 |
| `tests/unit/test_prop_clustering_evaluation.py` | [ ] TODO | 432 | 0 |
| `tests/unit/test_prop_clustering_tuning.py` | [ ] TODO | 355 | 0 |
| `tests/unit/test_prop_clustering_tuning_analysis.py` | [ ] TODO | 300 | 0 |
| `tests/unit/test_prop_clustering_tuning_report.py` | [ ] TODO | 84 | 0 |
| `tests/unit/test_prop_compute_metadata.py` | [ ] TODO | 228 | 0 |
| `tests/unit/test_prop_consensus_clustering.py` | [ ] TODO | 224 | 0 |
| `tests/unit/test_prop_covariance_pca.py` | [ ] TODO | 551 | 0 |
| `tests/unit/test_prop_distances.py` | [ ] TODO | 357 | 0 |
| `tests/unit/test_prop_functional.py` | [ ] TODO | 476 | 0 |
| `tests/unit/test_prop_lesion.py` | [ ] TODO | 509 | 0 |
| `tests/unit/test_prop_lesion_location.py` | [ ] TODO | 250 | 0 |
| `tests/unit/test_prop_logging_metadata_sources.py` | [ ] TODO | 189 | 0 |
| `tests/unit/test_prop_model_config.py` | [ ] TODO | 373 | 0 |
| `tests/unit/test_prop_params.py` | [ ] TODO | 473 | 0 |
| `tests/unit/test_prop_parcellated_csv.py` | [ ] TODO | 304 | 0 |
| `tests/unit/test_prop_participants.py` | [ ] TODO | 240 | 0 |
| `tests/unit/test_prop_pca_evaluation.py` | [ ] TODO | 283 | 0 |
| `tests/unit/test_prop_pca_method.py` | [ ] TODO | 294 | 0 |
| `tests/unit/test_prop_prediction.py` | [ ] TODO | 268 | 0 |
| `tests/unit/test_prop_raw_distances.py` | [ ] TODO | 167 | 0 |
| `tests/unit/test_prop_reduction.py` | [ ] TODO | 175 | 0 |
| `tests/unit/test_prop_run_log.py` | [ ] TODO | 167 | 0 |
| `tests/unit/test_prop_sdc.py` | [ ] TODO | 388 | 0 |
| `tests/unit/test_prop_subject_discovery.py` | [ ] TODO | 251 | 0 |
| `tests/unit/test_prop_subject_ids.py` | [ ] TODO | 112 | 0 |
| `tests/unit/test_prop_tuning.py` | [ ] TODO | 150 | 0 |
| `tests/unit/test_prop_tuning_embeddings.py` | [ ] TODO | 330 | 0 |
| `tests/unit/test_prop_tuning_evaluations.py` | [ ] TODO | 267 | 0 |
| `tests/unit/test_raw_distances.py` | [ ] TODO | 108 | 0 |
| `tests/unit/test_reduction.py` | [ ] TODO | 406 | 0 |
| `tests/unit/test_replot_dim_reduction.py` | [ ] TODO | 87 | 0 |
| `tests/unit/test_replot_dim_reduction_paths.py` | [ ] TODO | 145 | 0 |
| `tests/unit/test_run_log.py` | [ ] TODO | 205 | 0 |
| `tests/unit/test_subject_discovery.py` | [ ] TODO | 99 | 0 |
| `tests/unit/test_subject_ids.py` | [ ] TODO | 43 | 0 |
| `tests/unit/test_tuning.py` | [ ] TODO | 431 | 0 |
| `tests/unit/test_tuning_embeddings.py` | [ ] TODO | 106 | 0 |
| `tests/unit/test_tuning_evaluations.py` | [ ] TODO | 228 | 0 |
| `tests/unit/test_tuning_match.py` | [ ] TODO | 174 | 0 |
| `tests/unit/test_understanding_umap_report.py` | [ ] TODO | 270 | 0 |

### 2.6 `notebooks/` (13 file)

| File | Stato | Righe | Ultima riga analizzata |
|---|---|---|---|
| `notebooks/exploration/dataset_availability.ipynb` | [ ] TODO | 1055 | 0 |
| `notebooks/exploration/fc_analysis.ipynb` | [ ] TODO | 1164 | 0 |
| `notebooks/exploration/lesion_analysis.ipynb` | [ ] TODO | 6179 | 0 |
| `notebooks/exploration/metadata_raw.ipynb` | [ ] TODO | 1484 | 0 |
| `notebooks/exploration/sdc_analysis.ipynb` | [ ] TODO | 1358 | 0 |
| `notebooks/pipeline_building/dim_reduction.ipynb` | [ ] TODO | 1077 | 0 |
| `notebooks/pipeline_building/fc_lesion_masking.ipynb` | [ ] TODO | 412 | 0 |
| `notebooks/pipeline_building/lesion_matrix_build.ipynb` | [ ] TODO | 976 | 0 |
| `notebooks/pipeline_building/thiebaut_2020_replication.ipynb` | [ ] TODO | 684 | 0 |
| `notebooks/post-results_analysis/clustering_comparison.ipynb` | [ ] TODO | 5549 | 0 |
| `notebooks/post-results_analysis/clustering_evaluation.ipynb` | [-] ELIMINATO da `591e078` (27-10): non c'è più, niente da auditare | 1001 | - |
| `notebooks/post-results_analysis/dendrogram_embedding_explorer.ipynb` | [ ] TODO | 1227 | 0 |
| `notebooks/post-results_analysis/pca_evaluation.ipynb` | [ ] TODO | 1071 | 0 |

### 2.7 `assets/` (50 file)

| File | Stato | Righe | Ultima riga analizzata |
|---|---|---|---|
| `assets/atlases/fmriprep/atlas-Yan100TianS1Buckner7N/atlas-Yan100TianS1Buckner7N_dseg.tsv` | [ ] TODO | 124 | 0 |
| `assets/atlases/fmriprep/atlas-Yan100TianS1Buckner7N/atlas-Yan100TianS1Buckner7N_space-MNI152NLin6Asym_res-2_dseg.nii.gz` | [ ] TODO | bin | 0 |
| `assets/atlases/fmriprep/atlas-Yan100TianS2Buckner7N/atlas-Yan100TianS2Buckner7N_dseg.tsv` | [ ] TODO | 140 | 0 |
| `assets/atlases/fmriprep/atlas-Yan100TianS2Buckner7N/atlas-Yan100TianS2Buckner7N_space-MNI152NLin6Asym_res-2_dseg.nii.gz` | [ ] TODO | bin | 0 |
| `assets/atlases/fmriprep/atlas-Yan100TianS3Buckner7N/atlas-Yan100TianS3Buckner7N_dseg.tsv` | [ ] TODO | 158 | 0 |
| `assets/atlases/fmriprep/atlas-Yan100TianS3Buckner7N/atlas-Yan100TianS3Buckner7N_space-MNI152NLin6Asym_res-2_dseg.nii.gz` | [ ] TODO | bin | 0 |
| `assets/atlases/fmriprep/atlas-Yan200TianS1Buckner7N/atlas-Yan200TianS1Buckner7N_dseg.tsv` | [ ] TODO | 224 | 0 |
| `assets/atlases/fmriprep/atlas-Yan200TianS1Buckner7N/atlas-Yan200TianS1Buckner7N_space-MNI152NLin6Asym_res-2_dseg.nii.gz` | [ ] TODO | bin | 0 |
| `assets/atlases/fmriprep/atlas-Yan200TianS2Buckner7N/atlas-Yan200TianS2Buckner7N_dseg.tsv` | [ ] TODO | 240 | 0 |
| `assets/atlases/fmriprep/atlas-Yan200TianS2Buckner7N/atlas-Yan200TianS2Buckner7N_space-MNI152NLin6Asym_res-2_dseg.nii.gz` | [ ] TODO | bin | 0 |
| `assets/atlases/fmriprep/atlas-Yan200TianS3Buckner7N/atlas-Yan200TianS3Buckner7N_dseg.tsv` | [ ] TODO | 258 | 0 |
| `assets/atlases/fmriprep/atlas-Yan200TianS3Buckner7N/atlas-Yan200TianS3Buckner7N_space-MNI152NLin6Asym_res-2_dseg.nii.gz` | [ ] TODO | bin | 0 |
| `assets/atlases/fmriprep/atlas-Yan300TianS1Buckner7N/atlas-Yan300TianS1Buckner7N_dseg.tsv` | [ ] TODO | 324 | 0 |
| `assets/atlases/fmriprep/atlas-Yan300TianS1Buckner7N/atlas-Yan300TianS1Buckner7N_space-MNI152NLin6Asym_res-2_dseg.nii.gz` | [ ] TODO | bin | 0 |
| `assets/atlases/fmriprep/atlas-Yan300TianS2Buckner7N/atlas-Yan300TianS2Buckner7N_dseg.tsv` | [ ] TODO | 340 | 0 |
| `assets/atlases/fmriprep/atlas-Yan300TianS2Buckner7N/atlas-Yan300TianS2Buckner7N_space-MNI152NLin6Asym_res-2_dseg.nii.gz` | [ ] TODO | bin | 0 |
| `assets/atlases/fmriprep/atlas-Yan300TianS3Buckner7N/atlas-Yan300TianS3Buckner7N_dseg.tsv` | [ ] TODO | 358 | 0 |
| `assets/atlases/fmriprep/atlas-Yan300TianS3Buckner7N/atlas-Yan300TianS3Buckner7N_space-MNI152NLin6Asym_res-2_dseg.nii.gz` | [ ] TODO | bin | 0 |
| `assets/atlases/fmriprep/atlas-Yan400TianS1Buckner7N/atlas-Yan400TianS1Buckner7N_dseg.tsv` | [ ] TODO | 424 | 0 |
| `assets/atlases/fmriprep/atlas-Yan400TianS1Buckner7N/atlas-Yan400TianS1Buckner7N_space-MNI152NLin6Asym_res-2_dseg.nii.gz` | [ ] TODO | bin | 0 |
| `assets/atlases/fmriprep/atlas-Yan400TianS2Buckner7N/atlas-Yan400TianS2Buckner7N_dseg.tsv` | [ ] TODO | 440 | 0 |
| `assets/atlases/fmriprep/atlas-Yan400TianS2Buckner7N/atlas-Yan400TianS2Buckner7N_space-MNI152NLin6Asym_res-2_dseg.nii.gz` | [ ] TODO | bin | 0 |
| `assets/atlases/fmriprep/atlas-Yan400TianS3Buckner7N/atlas-Yan400TianS3Buckner7N_dseg.tsv` | [ ] TODO | 458 | 0 |
| `assets/atlases/fmriprep/atlas-Yan400TianS3Buckner7N/atlas-Yan400TianS3Buckner7N_space-MNI152NLin6Asym_res-2_dseg.nii.gz` | [ ] TODO | bin | 0 |
| `assets/atlases/fsl/Cerebellum/Cerebellum-MNIfnirt-maxprob-thr25-1mm.nii.gz` | [ ] TODO | bin | 0 |
| `assets/atlases/fsl/Cerebellum/Cerebellum-MNIfnirt-maxprob-thr25-2mm.nii.gz` | [ ] TODO | bin | 0 |
| `assets/atlases/fsl/Cerebellum/Cerebellum_MNIfnirt.xml` | [ ] TODO | 46 | 0 |
| `assets/atlases/fsl/HarvardOxford/HarvardOxford-Cortical.xml` | [ ] TODO | 66 | 0 |
| `assets/atlases/fsl/HarvardOxford/HarvardOxford-Subcortical.xml` | [ ] TODO | 39 | 0 |
| `assets/atlases/fsl/HarvardOxford/HarvardOxford-cort-maxprob-thr25-1mm.nii.gz` | [ ] TODO | bin | 0 |
| `assets/atlases/fsl/HarvardOxford/HarvardOxford-cort-maxprob-thr25-2mm.nii.gz` | [ ] TODO | bin | 0 |
| `assets/atlases/fsl/HarvardOxford/HarvardOxford-sub-maxprob-thr25-1mm.nii.gz` | [ ] TODO | bin | 0 |
| `assets/atlases/fsl/HarvardOxford/HarvardOxford-sub-maxprob-thr25-2mm.nii.gz` | [ ] TODO | bin | 0 |
| `assets/atlases/fsl/README.md` | [ ] TODO | 32 | 0 |
| `assets/atlases/sdc_labels/schaefer_200_tian_s2.csv` | [ ] TODO | 233 | 0 |
| `assets/atlases/sdc_labels/schaefer_300_tian_s2.csv` | [ ] TODO | 333 | 0 |
| `assets/atlases/sdc_labels/schaefer_400_tian_s2.csv` | [ ] TODO | 433 | 0 |
| `assets/atlases/sdc_labels/yeh_hcp1065_streamline.csv` | [ ] TODO | 88 | 0 |
| `assets/metadata/columns_by_dataset.xlsx` | [ ] TODO | bin | 0 |
| `assets/metadata/excluded_subjects.csv` | [ ] TODO | 23 | 0 |
| `assets/metadata/lesion_metadata.config.json` | [ ] TODO | 51 | 0 |
| `assets/metadata/lesion_metadata.csv` | [ ] TODO | 5854 | 0 |
| `assets/metadata/participants.csv` | [ ] TODO | 5854 | 0 |
| `assets/metadata/participants_protected.json` | [ ] TODO | 4 | 0 |
| `assets/metadata/sdc_metadata.config.json` | [ ] TODO | 31 | 0 |
| `assets/metadata/sdc_metadata.csv` | [ ] TODO | 5854 | 0 |
| `assets/templates/tpl-MNI152NLin6Asym_res-1_T1w.nii.gz` | [ ] TODO | bin | 0 |
| `assets/templates/tpl-MNI152NLin6Asym_res-1_desc-brain_mask.nii.gz` | [ ] TODO | bin | 0 |
| `assets/templates/tpl-MNI152NLin6Asym_res-2_T1w.nii.gz` | [ ] TODO | bin | 0 |
| `assets/templates/tpl-MNI152NLin6Asym_res-2_desc-brain_mask.nii.gz` | [ ] TODO | bin | 0 |

### 2.8 `summaries/` (51 file, raggruppati per cartella)

| Cartella | Stato | N. file | Note |
|---|---|---|---|
| `summaries/` | [ ] TODO | 1 | campionamento, non riga per riga |
| `summaries/build_excluded_subjects/` | [ ] TODO | 7 | campionamento, non riga per riga |
| `summaries/build_sdc_matrix/clinical_connectome/` | [ ] TODO | 1 | campionamento, non riga per riga |
| `summaries/calibrate_lesion_side_threshold/` | [ ] TODO | 4 | campionamento, non riga per riga |
| `summaries/compute_lesion_metadata/` | [ ] TODO | 3 | campionamento, non riga per riga |
| `summaries/compute_sdc_metadata/` | [ ] TODO | 6 | campionamento, non riga per riga |
| `summaries/enrich_metadata/` | [ ] TODO | 24 | campionamento, non riga per riga |
| `summaries/populate_metadata/` | [ ] TODO | 5 | campionamento, non riga per riga |

### 2.9 `logs/` (792 file, raggruppati per cartella)

| Cartella | Stato | N. file | Note |
|---|---|---|---|
| `logs/analyze_clustering_tuning/` | [ ] TODO | 172 | campionamento, non riga per riga |
| `logs/build_excluded_subjects/` | [ ] TODO | 7 | campionamento, non riga per riga |
| `logs/build_fc_matrix/clinical_connectome/` | [ ] TODO | 2 | campionamento, non riga per riga |
| `logs/build_lesion_matrix/clinical_connectome/` | [ ] TODO | 4 | campionamento, non riga per riga |
| `logs/build_sdc_matrix/clinical_connectome/` | [ ] TODO | 9 | campionamento, non riga per riga |
| `logs/calibrate_lesion_side_threshold/` | [ ] TODO | 4 | campionamento, non riga per riga |
| `logs/clustering/clinical_connectome/` | [ ] TODO | 398 | campionamento, non riga per riga |
| `logs/compute_lesion_metadata/` | [ ] TODO | 4 | campionamento, non riga per riga |
| `logs/compute_sdc_metadata/` | [ ] TODO | 6 | campionamento, non riga per riga |
| `logs/data_retrieval/clinical_connectome/` | [ ] TODO | 7 | campionamento, non riga per riga |
| `logs/dim_reduction/clinical_connectome/` | [ ] TODO | 52 | campionamento, non riga per riga |
| `logs/dim_reduction/temp_s2.4_pca42/` | [ ] TODO | 2 | campionamento, non riga per riga |
| `logs/dim_reduction/temp_s2.4_umap_nc50/` | [ ] TODO | 2 | campionamento, non riga per riga |
| `logs/enrich_metadata/` | [ ] TODO | 27 | campionamento, non riga per riga |
| `logs/evaluate_clustering_tuning/` | [ ] TODO | 77 | campionamento, non riga per riga |
| `logs/evaluate_tuning_embeddings/` | [ ] TODO | 6 | campionamento, non riga per riga |
| `logs/mask_fc/clinical_connectome/` | [ ] TODO | 2 | campionamento, non riga per riga |
| `logs/populate_metadata/` | [ ] TODO | 5 | campionamento, non riga per riga |
| `logs/slurm/data_summary/` | [ ] TODO | 2 | campionamento, non riga per riga |
| `logs/slurm/download_sdc/` | [ ] TODO | 2 | campionamento, non riga per riga |
| `logs/slurm/retrieve_data/` | [ ] TODO | 2 | campionamento, non riga per riga |

## Fuori perimetro dichiarato (da decidere)

`pytest.ini`, `environment.yml`, `.gitignore`, `README.md` (root), `management/`, `knowledge/papers/`, `results/`, `data/`, `tmp/`. `README.md` e `environment.yml` sono citati da `CLAUDE.md`: verificati come riferimenti puntuali, non letti riga per riga.

## Aggiunta ciclo 21 — file nuovi o spostati dall'utente (Fase 1)

| File | Stato | Righe | Ultima riga analizzata |
|---|---|---|---|
| `docs/README.md` | [x] COMPLETATO | 73 | 73 |
| `docs/guides/pipeline_overview.md` | [x] COMPLETATO | 138 | 138 |
| `docs/guides/setup.md` | [x] COMPLETATO | 43 | 43 |
