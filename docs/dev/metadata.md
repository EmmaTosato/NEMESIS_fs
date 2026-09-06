# Metadati clinici — riferimento tecnico

Audience: chi lavora su `scripts/populate_metadata.py`, `src/pipeline/enrich_lesion_metadata.py`, `src/features/clinical.py`, o chi deve capire dove vive un dato valore clinico/anagrafico (age, sex, NIHSS, lesion_side...) e come ci è arrivato.

**Il modulo è in ridisegno.** Qui sotto: prima il disegno di arrivo, poi cosa esiste davvero adesso, poi cosa resta da smantellare — i tre non coincidono ancora. Per quali campi esistono in quale dataset, vedi `docs/guides/datasets.md`.

## Disegno di arrivo

Una sola fonte di verità: **`assets/metadata/participants.csv`**, una riga per soggetto, versionata in git. Due script la scrivono, ognuno risponde a una domanda diversa, e nient'altro nel repo ricalcola valori clinici per conto proprio.

```
data/clinical_connectome/metadata_tsv/participants_*.tsv        (grezzi, uno per dataset, gitignored)
data/clinical_connectome/derivatives/<dataset>/{manual_masks,sdc,features}/   (cosa c'è su disco)
        │  scripts/populate_metadata.py          — chi esiste
        ▼
assets/metadata/participants.csv
        ▲
        │  src/pipeline/enrich_metadata.py       — cosa sappiamo di lui  [DA SCRIVERE]
        │
data/derived/lesion_matrix/<sessione>/matrix.npy                (volume lesionale)
data/clinical_connectome/derivatives/<dataset>/manual_masks/    (lato lesione, calcolato)
```

| | `populate_metadata.py` (fatto) | `enrich_metadata.py` (da scrivere) |
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

**Quindi: dopo aver lanciato `populate_metadata.py` (e più avanti `enrich_metadata.py`), controlla se qualche cartella è potata e correggi a mano i `has_*` interessati** — oppure decomprimi prima e lancia con `overwrite=true`. Le cartelle potate oggi sono `UNIPD/WashU/features/` e `data/derived/features/masked_fc/`. Il gruppo del soggetto non è memorizzato nel manifest perché derivabile: `group_of(subject_id)`.

## Cosa esiste davvero adesso

- **`assets/metadata/participants.csv`** — 5752 soggetti stroke, scritto da `populate_metadata.py`. Ci sono solo le colonne di populate; quelle di enrich non ancora.
- **`assets/metadata/<DATASET>_participants_{lesions,features,join}.tsv`** — la generazione precedente di file curati, ora ferma: nessuno li rigenera più. Sono però ancora ciò che leggono `src/features/clinical.py` e `src/features/sdc.py`, motivo per cui non sono stati cancellati — vedi "Da smantellare".
- **`data/derived/<pipeline>/<sessione>/metadata.csv`** e **`results/**/metadata.csv`** — portano ancora le colonne cliniche unite dal vecchio meccanismo.

### Due eccezioni che enrich dovrà codificare esplicitamente

- **Proxy NIHSS per PASPORT.** `NIHSS_at_presentation` viene usato come sostituto del `NIHSS` baseline, che PASPORT non ha. Questo contraddice `src/features/clinical.py::join_nihss`, che si rifiuta deliberatamente di farlo ("un'assunzione di equivalenza clinica che questa funzione non ha basi per fare"). È una **eccezione consapevole e rivedibile**, non una regola generale che i proxy vadano bene. UCL-UK resta comunque vuoto: non ha nessuna colonna NIHSS-correlata.
- **`lesion_side` calcolato dove il clinico manca**, geometricamente dalla maschera (conteggio voxel ai due lati della midline MNI, x=0), con una soglia "bilaterale" calibrata sui 4 dataset che hanno l'etichetta clinica (i 30 `both` di UKE inclusi) prima di applicarla a PASPORT/UCL. `lesion_side_source` (`clinical`/`computed`) registra da dove viene ogni cella — serve perché il buco è per-soggetto, non solo per-dataset (~230 soggetti tra WashU e PSP).

## Da smantellare

Quando `enrich_metadata.py` esiste, tutto ciò che risolve valori clinici per conto proprio sparisce — il senso di una fonte unica è che nessun consumer ricalcoli niente:

| Dove | Cosa |
|---|---|
| `src/features/clinical.py` | `join_lesion_side`, `join_nihss`, `join_participant_variables`, `check_participant_variable_coverage`, `VariableCoverageReport`, `participants_tsv_path`, `load_participants`, `extract_target` |
| `src/features/sdc.py` | legge `has_lesion` da `participants.csv` invece che da `<DATASET>_participants_lesions.tsv` |
| `src/analysis/build_config.py` | `EnrichLesionMetadataConfig` riscritta sul nuovo schema di config |
| `src/analysis/embedding_coloring.py` | `color_values()` smette di leggere colonne cliniche dal `metadata.csv` di un run |
| `src/pipeline/dim_reduction.py` | via la chiamata a `enrich_metadata_with_lesion_info` in produzione |
| `assets/metadata/*_participants_*.tsv` | cancellati |
| `data/derived/**/metadata.csv`, `results/**/metadata.csv` | ridotti a `subject_id`, `dataset` (+ `cluster_label` dove il clustering ne ha scritto uno) — l'ordine delle righe accanto a `matrix.npy` è l'unica cosa che sono strutturalmente obbligati a portare (`src/utils/artifacts.py::save_matrix` lo verifica) |

## Report e log

`populate_metadata.py` scrive un report per run in `summaries/populate_metadata/` e il log corrispondente in `logs/populate_metadata/`: i conteggi per dataset più, soggetto per soggetto, tutto ciò che è stato escluso (solo nel tsv, solo su disco, filtrato per gruppo) e ogni disaccordo su `disease_id`. **Non c'è nessun `runs.csv`**: è una pipeline di metadati, non un run di analisi, e il suo output è versionato in git dove il diff è leggibile.
