# Metadati clinici — riferimento tecnico

Audience: chi lavora su `scripts/populate_metadata.py`, `src/pipeline/enrich_metadata.py`, `src/utils/participants.py`, o chi deve capire dove vive un dato valore clinico/anagrafico (age, sex, NIHSS, lesion_side...) e come ci è arrivato.

Il ridisegno è **in vigore**: la fonte di verità unica esiste e i consumatori la leggono. Resta una sola cosa non implementata, il `lesion_side` calcolato geometricamente (vedi in fondo). Per quali campi esistono in quale dataset, vedi `docs/guides/datasets.md`.

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
data/derived/lesion_matrix/<sessione>/matrix.npy                (volume lesionale)
data/clinical_connectome/derivatives/<dataset>/manual_masks/    (lato lesione, calcolato)
```

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

- **`assets/metadata/participants.csv`** — 5752 soggetti stroke, con le colonne di entrambi gli script: `subject_id`, `original_id`, `dataset`, `disease_id`, `has_lesion`, `has_sdc`, `has_features` (populate) e `age`, `sex`, `education`, `lesion_side`, `lesion_side_source`, `NIHSS`, `clinical_date`, `lesion_volume_voxels` (enrich).
- **I tsv per-dataset `assets/metadata/<DATASET>_participants_*.tsv` non esistono più**: cancellati. Ogni consumatore è stato spostato sul file unico.
- **`data/derived/<pipeline>/<sessione>/metadata.csv`** — contiene solo ciò che appartiene alla run (`subject_id`, `dataset`, `lesion_volume_voxels`); i valori clinici non ci vengono più copiati. Le run vecchie li hanno ancora, per storia: chi legge preferisce la colonna della run quando c'è, e altrimenti va al registro.

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

## Cosa manca ancora

**`lesion_side` calcolato geometricamente.** Oggi `lesion_side` è popolato solo dove il dato clinico esiste (`lesion_side_source = "clinical"`); PASPORT e UCL-UK non hanno affatto la colonna, e ~230 soggetti tra WashU e PSP hanno la cella vuota pur avendo il dataset la colonna. Il calcolo dalla maschera (conteggio voxel ai due lati della midline MNI, x=0) è meccanico, ma la soglia oltre cui una lesione è "bilaterale" va **calibrata** sui 4 dataset che hanno l'etichetta clinica (i 30 `both` di UKE inclusi) prima di poterla applicare agli altri. Finché quella calibrazione non è fatta, la variabile non viene scritta: inventare una soglia darebbe un valore dall'aria plausibile e senza basi. `lesion_side_source` esiste già per distinguere le due provenienze quando arriverà.

## Smantellato (per riferimento)

Il vecchio meccanismo — una join per-dataset ripetuta dentro il `metadata.csv` di ogni run — è stato rimosso il 06-09-26:

| Cosa | Fine |
|---|---|
| `src/pipeline/enrich_lesion_metadata.py` + config + job | cancellati, sostituiti da `enrich_metadata.py` |
| `src/features/clinical.py` (`join_lesion_side`, `join_nihss`, `join_participant_variables`, `check_participant_variable_coverage`, `participants_tsv_path`, `load_participants`, `extract_target`) | cancellato; la parte ancora viva (lettura del registro) è in `src/utils/participants.py` |
| `EnrichLesionMetadataConfig` in `src/analysis/build_config.py` | cancellata |
| `assets/metadata/*_participants_*.tsv` | cancellati |
