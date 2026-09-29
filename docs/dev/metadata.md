# Metadati clinici — riferimento tecnico

Audience: chi lavora su `scripts/populate_metadata.py`, `src/pipeline/enrich_metadata.py`, `src/utils/participants.py`, o chi deve capire dove vive un dato valore clinico/anagrafico (age, sex, NIHSS, lesion_side...) e come ci è arrivato.

Il ridisegno è **in vigore**: la fonte di verità unica esiste e i consumatori la leggono. Per quali campi esistono in quale dataset, vedi `docs/guides/datasets.md`.

## Come funziona

Una sola fonte di verità: **`assets/metadata/participants.csv`**, una riga per soggetto, versionata in git. Due script la scrivono, ognuno risponde a una domanda diversa, e nient'altro nel repo ricalcola valori clinici per conto proprio.

```
data/clinical_connectome/metadata_tsv/participants_*.tsv        (grezzi, uno per dataset, gitignored)
data/clinical_connectome/derivatives/<dataset>/{manual_masks,sdc,features}/   (cosa c'è su disco)
        │  scripts/populate_metadata.py          — chi esiste
        ▼
assets/metadata/participants.csv
        ▲
        │  src/pipeline/enrich_metadata.py       — cosa sappiamo di lui
        │
data/clinical_connectome/derivatives/<dataset>/manual_masks/    (lesion_volume_voxels e, in fallback,
                                                                   lesion_side geometrico - entrambi calcolati fresco)
```

`lesion_volume_voxels` e, in fallback, `lesion_side` sono calcolati **freschi dalle maschere** (`config.lesion_metrics`, vedi sotto), non più copiati da un artefatto `data/derived/lesion_matrix/<sessione>/` già costruito — quella scelta si è rivelata generare esattamente la seconda fonte di verità che voleva evitare (28-09-26, `.claude/history/methods_changelog.md`: 900/5721 soggetti con valore diverso tra le due fonti, fino a 38x, dopo che la griglia era cambiata senza ricostruire l'artefatto).

| | `populate_metadata.py` | `enrich_metadata.py` |
|---|---|---|
| Domanda | chi esiste | cosa sappiamo di lui |
| Scrive | `subject_id`, `original_id`, `dataset`, `disease_id`, `has_lesion`, `has_sdc`, `has_features` | `age`, `sex`, `lesion_side`, `lesion_side_source`, `NIHSS`, `education`, `clinical_date`, `lesion_volume_voxels` |
| Flag di idempotenza | `overwrite` — false: aggiunge solo soggetti nuovi, righe esistenti intatte; true: ricalcola le proprie colonne preservando quelle dell'altro script | `fill` — true: riempie solo le celle vuote delle variabili richieste; false: ricalcola tutto il richiesto |

Registry condiviso: **`config/registry/metadata_sources.json`** — per ogni dataset, il path del tsv grezzo e quello della cartella derivatives. Lo leggono entrambi gli script, così la corrispondenza dataset↔path esiste in un posto solo (non è derivabile meccanicamente: `participants_UCL.tsv` ↔ `UCL-UK/UCLStrokeData`).

### Scelte da conoscere

- **CSV, non Excel.** Excel converte le date e mangia gli zeri iniziali a ogni ciclo di lettura/scrittura, e in questo repo è già costato una perdita di dati (vedi `.claude/lessons_learned.md`). Il CSV dà anche diff git leggibili, che è ciò che rende utile versionare la fonte di verità. Leggerlo sempre con `dtype=str`.
- **`subject_id`, non `participant_id`.** La forma canonica `sub-{disease}{site}{num}`, la stessa di ogni `metadata.csv` e di `src/retrieval/dataset.py::group_of`. Il `participant_id` grezzo dei tsv resta in `original_id` — utile solo per UCL-UK, il cui valore grezzo è l'id legacy del sito (`ST_UCL-UK_0001`). Chiamare la colonna `participant_id` l'avrebbe fatta sembrare joinabile coi tsv grezzi pur contenendo un valore *diverso* per UCL-UK — la trappola di `.claude/lessons_learned.md` #30.
- **`disease_id` viene dal subject id**, estratto da `group_of()`, non copiato dal tsv. Il valore del tsv viene confrontato con quello e ogni disaccordo è segnalato come problema di dati, invece di sceglierne uno in silenzio.
- **Solo stroke.** `group_filter: ["ST"]`; i controlli sani sono deliberatamente fuori scope e avranno un file a parte.
- **Inner join.** Un soggetto solo nel tsv (nessun dato su disco) e uno solo su disco (nessuna riga clinica) sono entrambi esclusi ed entrambi elencati nel report del run.

### ⚠️ `has_*` descrive il disco, e il disco può essere potato

`populate_metadata.py` risponde a "cosa ha questo soggetto" scandendo le cartelle. `scripts/archive_local_raw_data.py` comprime via la maggior parte dei soggetti di alcune cartelle per liberare spazio locale (vedi `docs/guides/datasets.md`) — e una scansione non vede dentro un `.tar.gz`.

Ogni cartella potata porta quindi un **manifest**, `<nome>_archive_subjects.tsv` (`subject_id`, `source` ∈ {`kept_in_place`, `archive`}), scritto da `archive_local_raw_data.py`: il registro macchina-leggibile della popolazione reale, leggibile senza decomprimere gigabyte. `populate_metadata.py` deliberatamente **non** lo legge: la potatura è una misura temporanea di spazio locale, non una proprietà permanente del progetto, e cablarla nella pipeline significherebbe incastonare un workaround nel contratto.

**Quindi: dopo aver lanciato `populate_metadata.py` o `enrich_metadata.py`, controlla se qualche cartella è potata e correggi a mano i `has_*` interessati** — oppure decomprimi prima e lancia con `overwrite=true`. Le cartelle potate oggi sono `UNIPD/WashU/features/` e `data/derived/features/masked_fc/`. Il gruppo del soggetto non è memorizzato nel manifest perché derivabile: `group_of(subject_id)`.

## Cosa esiste davvero adesso

- **`assets/metadata/participants.csv`** — 5853 soggetti stroke, con le colonne di entrambi gli script: `subject_id`, `original_id`, `dataset`, `disease_id`, `has_lesion`, `has_sdc`, `has_features` (populate) e `age`, `sex`, `education`, `lesion_side`, `lesion_side_source`, `NIHSS`, `clinical_date`, `lesion_volume_voxels` (enrich).
- **I tsv per-dataset `assets/metadata/<DATASET>_participants_*.tsv` non esistono più**: cancellati. Ogni consumatore è stato spostato sul file unico.
- **`data/derived/<pipeline>/<sessione>/metadata.csv`** — contiene solo ciò che appartiene a quella run (`subject_id`, `dataset`, `lesion_volume_voxels` per `build_lesion_matrix.py`). Non è più la fonte da cui `enrich_metadata.py` copia `lesion_volume_voxels` in `participants.csv` (fino al 28-09-26 lo era, vedi sopra) — resta solo l'artefatto della run stessa, la sua colonna può differire da quella nel registro se le due griglie non coincidono.

### Chi legge il registro

| Consumatore | Cosa ci prende |
|---|---|
| `src/features/sdc.py` | `has_lesion`, criterio di ammissione di `build_sdc_matrix.py` |
| `src/analysis/embedding_coloring.py` | `lesion_side`/`NIHSS` per i color mode `side`/`nihss`, risolti al momento del plot |
| `notebooks/post-results_analysis/clustering_evaluation.ipynb` | age/sex/NIHSS per le demografiche per cluster |

Il join con i tsv grezzi avviene su **`original_id`**, non su `subject_id`: il `participant_id` grezzo è l'id canonico per quasi tutti i dataset ma è l'id legacy di sito per UCL-UK (`ST_UCL-UK_0001`). `participants.csv` fa da ponte perché li contiene entrambi — vedi `.claude/lessons_learned.md` #30.

I valori mancanti sono una **cella vuota**, uniformemente. Il registro non è un input di plotting: chi ha bisogno di una sentinella categorica (`"unknown"` per una legenda) se la applica in lettura. L'unica colonna che porta informazione in più è `lesion_side_source`.

### Sostituzioni di colonna registrate

Quando una variabile non esiste con il suo nome canonico in un dataset, `enrich_metadata.py` la legge da un'altra colonna **solo** se la sostituzione è scritta a mano in `VARIABLE_SOURCE_OVERRIDES`; non viene mai dedotta da un nome simile. Ogni sostituzione applicata finisce nel log a `WARNING` e in una sezione dedicata del report di run, perché è un'assunzione di equivalenza clinica e non deve restare invisibile.

Una sola oggi:

| Dataset | Variabile | Letta da | Perché |
|---|---|---|---|
| `UNIPD/PASPORT` | `NIHSS` | `NIHSS_at_presentation` | PASPORT non ha un NIHSS baseline, solo at_presentation/24H/3m |

UCL-UK resta comunque vuoto: non ha nessuna colonna NIHSS-correlata.

## `lesion_metrics`: tutto ciò che si calcola fresco dalle maschere

Un unico blocco di config (opzionale, `null` disattiva tutto), non un campo separato per metadato — condivide una sola fonte (`build_matrix_config`, un `build_lesion_matrix.json`) e una sola impostazione di correzione, invece di duplicarle per ogni metrica:

| Chiave | Effetto |
|---|---|
| `build_matrix_config` | Config `build_lesion_matrix.json`-shaped da cui leggere `data_root`/`datasets`/`reference_template_path`/`lesion_glob`/`binarize_threshold`/`resample_interpolation`/`brain_mask_path`. |
| `correct_out_of_brain` | Azzera i voxel di lesione fuori dal cervello (`src.features.lesion_correction.zero_out_of_brain_voxels`) **prima** di calcolare qualunque metrica sotto — stessa correzione che `build_lesion_matrix.py` applica alla matrice di produzione, ma flag indipendente: le due pipeline hanno scopi diversi (questo registro serve a plot/demografia, `build_lesion_matrix.py` costruisce l'input dell'embedding, rilanciabile più volte con impostazioni proprie) e possono avere valori diversi per scelta, senza che vada considerato un disallineamento da correggere. |
| `compute_volume` | Scrive `lesion_volume_voxels`. |
| `compute_side` | Riempie `lesion_side` **solo** dove il passaggio clinico l'ha lasciato vuoto (un valore clinico non viene mai toccato) — richiede `lesion_side` in `variables`. |
| `side_threshold` | Soglia di bilateralità per `compute_side` — vedi sotto. |

`lesion_side` ha quindi due fonti possibili, mai in conflitto perché la seconda scrive solo dove la prima non ha scritto nulla: **clinica** (dal tsv grezzo, `lesion_side_source = "clinical"`) e **geometrica** (`compute_side`, `lesion_side_source = "geometric"`) — conta i voxel di lesione ai due lati della midline MNI (world-x, non indice di voxel grezzo — vedi `src/features/lesion.py::_hemisphere_masks`) e calcola `laterality_index = (left − right) / (left + right)`; sopra `side_threshold` in valore assoluto → `left`/`right` (a seconda del segno), sotto → `both`.

La soglia (`0.20` in produzione) non è inventata: è calibrata contro 1445 soggetti con etichetta clinica vera (97.4% di accordo) — dettagli, letteratura di riferimento e limiti (la classe "bilaterale" resta debole, 3/24 corretti a qualunque soglia) in `knowledge/neuroimaging/lesion_laterality.md` e `.claude/history/methods_changelog.md` (28-09-26).

Un dataset fuori dalla lista `datasets` di `build_matrix_config` non riceve né volume né lato, con un `WARNING` nel log per nome, mai un errore — un'`enrich_metadata.py` può legittimamente avere uno scope più ampio di quello che un dato `build_lesion_matrix.json` copre oggi.

**Nessuna lista di esclusione per soggetto** (rimossa 29-09-26, `.claude/history/project_changelog.md`): un valore che risultasse inaffidabile in analisi si corregge **a mano direttamente in `participants.csv`** (un CSV versionato in git) — `fill: true` alla run successiva lo lascia intatto. Più semplice di un ciclo config-modifica/rilancia per un giudizio caso-per-caso che appartiene all'analisi, non alla configurazione di questa pipeline.
