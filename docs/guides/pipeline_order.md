# L'ordine delle pipeline

Dal dato grezzo a `dim_reduction` e `clustering`: in che ordine lanciare le pipeline, cosa fa ciascuna, cosa legge e cosa scrive. I parametri stanno nella guida di ogni pipeline (link a ogni passo); il perché e le regole di `overwrite` sono in [`docs/dev/pipeline_flow.md`](../dev/pipeline_flow.md).

## Il workflow in una tabella

| # | Pipeline | Cosa fa | Output |
|---|---|---|---|
| 1 | `populate_metadata` | elenca i soggetti presenti nei tsv e su disco | `participants.csv` |
| 2a | `compute_lesion_metadata` | misura le maschere di lesione | `lesion_metadata.csv` |
| 2b | `compute_sdc_metadata` | misura la disconnessione di ogni soggetto | `sdc_metadata.csv` |
| 3 | `enrich_metadata` | aggiunge le variabili (cliniche, volumi, disconnessione) al registro | `participants.csv` arricchito |
| 4 | `build_excluded_subjects` | scrive chi resta fuori dalle matrici | `excluded_subjects.csv` |
| 5a | `build_lesion_matrix` | matrice soggetti × voxel delle lesioni | `data/derived/lesion_matrix/` |
| 5b | `build_sdc_matrix` | matrice di disconnessione (regioni, voxel o tratti) | `data/derived/sdc_matrix/` |
| 5c | `mask_fc`, poi `build_fc_matrix` | matrice di connettività funzionale con i nodi lesionati mascherati | `data/derived/features/fc_matrix/` |
| 6 | `dim_reduction` | embedding a bassa dimensione della matrice | `results/<modalità>/dim_reduction/` |
| 7 | `clustering` | cluster sulla matrice o sull'embedding | `results/<modalità>/clustering/` |

I passi 5a, 5b e 5c sono indipendenti tra loro: ognuno produce una matrice, e da ciascuna si va a 6 e 7. Il passo 3 non serve per far girare 5, 6 e 7, ma per usarne i risultati.

## Come si lancia

```bash
conda activate nemesis
cd "$PROJECT_ROOT"
python -m src.pipeline.<nome> --config config/pipelines/<nome>.json
```

- `populate_metadata` richiede anche `PYTHONPATH="$PROJECT_ROOT"` davanti al comando.
- `--dry-run` (controlli e report, nessuna scrittura) esiste solo per `compute_lesion_metadata`, `compute_sdc_metadata`, `enrich_metadata` e `build_excluded_subjects`.
- Su cluster: `sbatch jobs/run_<nome>.sh`.

## La mappa

```
dati grezzi (copia a mano da EBRAIN)
   │
   ▼
[1] populate_metadata ───────► participants.csv  (chi esiste)
   │
   ├──► [2a] compute_lesion_metadata ──► lesion_metadata.csv ──┐
   ├──► [2b] compute_sdc_metadata ─────► sdc_metadata.csv ─────┤
   │                                                           ▼
   │                                       [3] enrich_metadata ──► participants.csv (variabili)
   │
   └──► [4] build_excluded_subjects (usa 2a) ──► excluded_subjects.csv
                          │
        ┌─────────────────┼───────────────────────┐
        ▼                 ▼                       ▼
 [5a] build_lesion_  [5b] build_sdc_        [5c] mask_fc
      matrix              matrix                  │
        │                 │                       ▼
        │                 │                 build_fc_matrix
        └─────────────────┼───────────────────────┘
                          ▼
            [6] dim_reduction ──► [7] clustering
```

`clustering` può leggere anche direttamente la matrice del passo 5.

- **Per far girare matrici, `dim_reduction` e `clustering` servono i passi 1, 2a e 4.**
- **Il passo 3 serve per usare i risultati:** `participants.csv` è la fonte di verità delle variabili per i colori dei grafici, la descrizione dei cluster e i notebook. Senza, `dim_reduction` gira ma salta i grafici colorati per lato, volume o NIHSS.
- **Il ramo FC (5c)** non legge né il registro né la lista delle esclusioni.

---

## 1. `populate_metadata` — chi esiste

```bash
PYTHONPATH="$PROJECT_ROOT" python -m src.pipeline.populate_metadata --config config/pipelines/populate_metadata.json
```

Unisce i tsv grezzi alle cartelle dei soggetti su disco.
**Input:** tsv in `data/clinical_connectome/metadata_tsv/` e cartelle dei soggetti. **Output:** `assets/metadata/participants.csv` (id, dataset, flag `has_lesion`, `has_sdc`, `has_features`). Guida: [`metadata.md`](metadata.md).

## 2a. `compute_lesion_metadata` — le misure sulle maschere

```bash
python -m src.pipeline.compute_lesion_metadata --config config/pipelines/compute_lesion_metadata.json
```

Misura ogni maschera su due griglie (1 e 2 mm): volume, frazione fuori dal brain, lateralità e lato. Circa 15 minuti sull'intera coorte.
**Input:** maschere di lesione, template. **Output:** `assets/metadata/lesion_metadata.csv`.

## 2b. `compute_sdc_metadata` — quanto è disconnesso ogni soggetto

```bash
python -m src.pipeline.compute_sdc_metadata --config config/pipelines/compute_sdc_metadata.json
```

Calcola carico e media di disconnessione su due griglie.
**Input:** registro (`has_sdc`) e mappe di disconnessione. **Output:** `assets/metadata/sdc_metadata.csv`.

## 3. `enrich_metadata` — le variabili in `participants.csv`

```bash
python -m src.pipeline.enrich_metadata --config config/pipelines/enrich_metadata.json
```

Aggiunge al registro età, sesso, istruzione, NIHSS, data clinica, lato, volumi e disconnessione. Non apre immagini: è un join.
**Input:** `participants.csv`, tsv grezzi, `lesion_metadata.csv`, `sdc_metadata.csv`. **Output:** `participants.csv` aggiornato sul posto. `overwrite: false` scrive solo le celle vuote, `true` le sostituisce; ciò che è in `assets/metadata/participants_protected.json` non si tocca mai. Guida: [`metadata.md`](metadata.md).

## 4. `build_excluded_subjects` — chi resta fuori dalle matrici

```bash
python -m src.pipeline.build_excluded_subjects --config config/pipelines/build_excluded_subjects.json
```

Scrive la lista dei soggetti esclusi (elencati nel config) con motivo e valore. Non si escludono le lesioni piccole; si escludono quelle con più del 30% dei voxel fuori dal brain.
**Input:** il config, `lesion_metadata.csv`, il registro. **Output:** `assets/metadata/excluded_subjects.csv`. Guida: [`metadata.md`](metadata.md).

---

## 5. Le matrici

Tre rami indipendenti. Ognuno scrive una cartella con `matrix.npy`, `metadata.csv`, `manifest.json` e `config.md`, che `dim_reduction` e `clustering` leggono tramite `input_path`. La coorte è il registro meno le righe di `excluded_subjects.csv` valide per quella matrice.

### 5a. `build_lesion_matrix`

```bash
python -m src.pipeline.build_lesion_matrix --config config/pipelines/build_lesion_matrix.json
```

Matrice binaria soggetti × voxel delle lesioni. `correct_out_of_brain` (`true` o `false`) azzera o no i voxel fuori dal brain.
**Input:** maschere, template 2 mm, `excluded_subjects.csv`. **Output:** `data/derived/lesion_matrix/<gg-mm>_<sessione>/`. Guida: [`matrix_building.md`](matrix_building.md).

### 5b. `build_sdc_matrix`

```bash
python -m src.pipeline.build_sdc_matrix --config config/pipelines/build_sdc_matrix.json
```

Matrice di disconnessione; `representation` sceglie `parcellated` (per regione), `voxelwise` (per voxel) o `streamline` (per tratto).
**Input:** output SDC, registro, `excluded_subjects.csv`, etichette in `assets/atlases/sdc_labels/`. **Output:** `data/derived/sdc_matrix/<gg-mm>_<sessione>/`. Guida: [`sdc_matrix_building.md`](sdc_matrix_building.md).

### 5c. `mask_fc`, poi `build_fc_matrix`

```bash
python -m src.pipeline.mask_fc --config config/pipelines/mask_fc.json
python -m src.pipeline.build_fc_matrix --config config/pipelines/build_fc_matrix.json
```

`mask_fc` marca come mancanti (NaN) i nodi di connettività coperti da lesione; `build_fc_matrix` impila i risultati.
**Input:** CSV FC, maschere, atlanti. **Output:** `data/derived/features/masked_fc/<atlas_combo>/`, poi `data/derived/features/fc_matrix/<atlas_combo>/`. Guida: [`fc_matrix_building.md`](fc_matrix_building.md).

---

## 6. `dim_reduction` — l'embedding

```bash
python -m src.pipeline.dim_reduction --config config/pipelines/dim_reduction.json
```

Riduce la matrice a poche dimensioni (`umap`, `tsne`, `pca`, `pacmap`). `fine_tuning: true` prova una griglia di parametri e scrive una tabella; `false` produce l'embedding.
**Input:** la matrice (`input_path`) e il registro dei parametri (`params_reduction.json` per la lesione, `params_reduction_sdc.json` per l'SDC). **Output:** `results/<modalità>/dim_reduction/{production,tuning}/<metodo>/...`. Guida: [`dim_reduction.md`](dim_reduction.md).

## 7. `clustering` — i cluster

```bash
python -m src.pipeline.clustering --config config/pipelines/clustering.json
```

Raggruppa i soggetti con `kmeans`, `agglomerative`, `gmm`, `hdbscan`, `spectral` o `evidence_accumulation`.
**Input:** la matrice (`reduced_data: false`) o un embedding del passo 6 (`true`), più `params_clustering.json`. **Output:** `results/<modalità>/clustering/{production,tuning}/<metodo>/<riduzione>/...`. Se la matrice ha più di 3 componenti, per i grafici dei cluster serve un `viz_embedding_path`, cioè un run 2D di `dim_reduction` sugli stessi soggetti. Guida: [`clustering.md`](clustering.md).

Per esplorare i risultati salvati:

```bash
python -m src.pipeline.embedding_app
```

---

## Prima di lanciare `dim_reduction` o `clustering`

- [ ] La matrice esiste e ha la coorte attesa.
- [ ] `params_file` è il registro giusto (lesione o SDC) e ne ho letto i valori: tiene quelli dell'ultima run.
- [ ] `session_name` è coerente con `input_path` (nessun controllo lo verifica) ed è registrata in [`data_sessions.md`](../experiments/data_sessions.md).
- [ ] `output_root` è quello giusto (`results/lesion/...` o `results/sdc/...`).
- [ ] Per colori e analisi: `enrich_metadata` è stato eseguito dopo l'ultimo cambio di maschere o tsv.

## Quando rilanciare cosa

| Cosa cambia | Passi |
|---|---|
| Soggetti nuovi | 1, 2a, 2b, 3 |
| Nuovi dati per soggetti già presenti | 1 con `overwrite: true` (con `false` i flag `has_*` esistenti non si aggiornano), poi 2a, 2b, 3 |
| Maschere o mappe SDC | 2a, 2b, 3 |
| Un tsv grezzo corretto | 3 |
| Criteri di esclusione | 4, poi le matrici |

`compute_lesion_metadata` e `compute_sdc_metadata` con `overwrite: false` escono subito se il csv esiste: per misurare soggetti nuovi o maschere cambiate serve `overwrite: true`. `enrich_metadata` con `false` scrive solo le celle vuote, con `true` le sostituisce.
