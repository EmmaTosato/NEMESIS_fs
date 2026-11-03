# Guida alla documentazione

Come orientarsi in `docs/`: dove cercare in base a cosa vuoi fare. Obiettivo del progetto e stato di avanzamento sono nel [`README.md`](../README.md) alla radice.

## Cosa cerco?

| Voglio... | Vai a |
|---|---|
| creare l'ambiente conda | [`guides/setup.md`](guides/setup.md) |
| capire il metodo di ogni pipeline, in breve | [`guides/pipeline_overview.md`](guides/pipeline_overview.md) |
| sapere in che ordine lanciare le pipeline, con i comandi | [`guides/pipeline_order.md`](guides/pipeline_order.md) |
| sapere quali coorti e dati esistono | [`guides/datasets.md`](guides/datasets.md) |
| lanciare una pipeline precisa | la sua guida in [`guides/`](#guides--come-si-usa) |
| capire come è fatto il codice di un modulo | [`dev/`](#dev--come-è-fatto) |
| sapere cosa è stato provato su una matrice e perché | [`experiments/`](#experiments--cosa-è-stato-fatto-e-deciso) |
| capire un bug passato | [`debugging/`](#debugging--bug-trovati-e-corretti) |
| il perché di un metodo o la letteratura | [`knowledge/notes/`](../knowledge/notes/) |

Le tre sezioni `guides/`, `dev/` e `experiments/` rispondono a tre domande diverse: **come si usa**, **come è fatto**, **cosa abbiamo deciso**. Una stessa pipeline compare in tutte e tre.

## `guides/` — come si usa

Per chi lancia le pipeline. Ogni guida dà comando, parametri del config, input e output.

**Percorso consigliato per partire:** [`setup.md`](guides/setup.md), poi [`pipeline_overview.md`](guides/pipeline_overview.md), poi [`pipeline_order.md`](guides/pipeline_order.md).

| Area | Guida |
|---|---|
| Ambiente e panoramica | [`setup.md`](guides/setup.md), [`pipeline_overview.md`](guides/pipeline_overview.md), [`pipeline_order.md`](guides/pipeline_order.md), [`datasets.md`](guides/datasets.md) |
| Metadati dei soggetti | [`metadata.md`](guides/metadata.md) |
| Matrici | [`matrix_building.md`](guides/matrix_building.md) (lesione), [`sdc_matrix_building.md`](guides/sdc_matrix_building.md) (disconnessione), [`fc_matrix_building.md`](guides/fc_matrix_building.md) (connettività funzionale) |
| Riduzione dimensionale | [`dim_reduction.md`](guides/dim_reduction.md), [`evaluate_dim_reduction_tuning.md`](guides/evaluate_dim_reduction_tuning.md) |
| Clustering | [`clustering.md`](guides/clustering.md), [`evaluate_clustering_tuning.md`](guides/evaluate_clustering_tuning.md) |
| Esplorazione e confronto dei risultati | [`embedding_app.md`](guides/embedding_app.md) (app Dash), [`evaluation.md`](guides/evaluation.md) (confronto tra run), [`understanding_umap_report.md`](guides/understanding_umap_report.md), [`exploration.md`](guides/exploration.md) (indice dei notebook) |

## `dev/` — come è fatto

Per chi modifica il codice: architettura, scelte implementative, invarianti. Si parte da [`pipeline_flow.md`](dev/pipeline_flow.md).

| Tema | File |
|---|---|
| Flusso tra le pipeline, fonti di verità, `overwrite` | [`pipeline_flow.md`](dev/pipeline_flow.md) |
| Schemi ricorrenti nel codice | [`design_patterns.md`](dev/design_patterns.md), [`config.md`](dev/config.md) |
| Matrici | [`lesion_matrix.md`](dev/lesion_matrix.md), [`sdc_matrix.md`](dev/sdc_matrix.md), [`fc_matrix.md`](dev/fc_matrix.md) |
| Metadati | [`metadata.md`](dev/metadata.md) |
| Modelli di riduzione e clustering | [`models.md`](dev/models.md), [`covariance_pca.md`](dev/covariance_pca.md) |
| Grafici | [`plotting.md`](dev/plotting.md) |
| Struttura dell'app Dash | [`embedding_app.md`](dev/embedding_app.md) |
| Pannelli dell'app Dash | [`anatomical_maps.md`](dev/anatomical_maps.md), [`cluster_description.md`](dev/cluster_description.md), [`cluster_composition.md`](dev/cluster_composition.md), [`cluster_comparison.md`](dev/cluster_comparison.md), [`cluster_drivers.md`](dev/cluster_drivers.md) |

## `experiments/` — cosa è stato fatto e deciso

Un file per **sessione** (`sX.Y-<formato>.md`): la coorte, la matrice e tutto ciò che ci è stato fatto sopra, in ordine. Qui stanno le scelte e il perché, non le tabelle complete dei tuning (restano in `tuning_results.csv` nella cartella della run).

- [`README.md`](experiments/README.md): tabella delle sessioni e vocabolario dei tag di formato.
- [`lineage.md`](experiments/lineage.md): quale sessione deriva da quale, e quali coorti si possono confrontare.
- [`pipelines.md`](experiments/pipelines.md): quali pipeline ha attraversato ogni matrice.

## `debugging/` — bug trovati e corretti

Un report datato per sessione di debug (`debug_GG_MM_AA.md`), un bug per sezione. Insieme a `experiments/` è la parte di `docs/` che racconta il passato: sono registri cronologici per sessione. I pattern di errore generalizzabili sono raccolti in [`.claude/lessons_learned.md`](../.claude/lessons_learned.md).

## Fuori da `docs/`

| Cartella | Contenuto |
|---|---|
| [`knowledge/notes/`](../knowledge/notes/) | Note nostre: metodologia di riduzione e clustering, neuroimaging, riassunti della letteratura sull'ictus. |
| [`knowledge/papers/`](../knowledge/papers/) | Paper estratti, in sola lettura, con indice in `index.md`. |
| [`management/meetings/`](../management/meetings/) | Appunti grezzi delle riunioni, fonte primaria di ciò che non è ancora in `docs/`. |
| [`.claude/history/`](../.claude/history/) | Archivio dei cambiamenti ai dati, ai metodi e all'impianto del progetto. |

## Regola di scrittura

`guides/` e `dev/` descrivono il **presente**: niente «prima faceva», niente date di modifiche. Il passato sta in `debugging/` e `experiments/` (registri cronologici per sessione), in `.claude/history/` e in `git log`.
