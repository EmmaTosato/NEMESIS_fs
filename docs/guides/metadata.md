# Metadati dei soggetti — come si usano

Tutto ciò che sappiamo dei soggetti sta in **un file solo**: `assets/metadata/participants.csv`, versionato in git, una riga per soggetto.

Lo scrivono due script, che rispondono a due domande diverse e non si sovrascrivono mai a vicenda:

| Script | Domanda | Colonne che scrive |
| :--- | :--- | :--- |
| `scripts/populate_metadata.py` | chi esiste | `subject_id`, `original_id`, `dataset`, `disease_id`, `has_lesion`, `has_sdc`, `has_features` |
| `src/pipeline/enrich_metadata.py` | cosa sappiamo di lui | `age`, `sex`, `education`, `lesion_side`, `lesion_side_source`, `NIHSS`, `clinical_date`, `lesion_volume_voxels` |

- **Dettagli architetturali/perché è fatto così**: [`docs/dev/metadata.md`](../dev/metadata.md)
- **Quali campi esistono in quale dataset**: [`docs/guides/datasets.md`](datasets.md)

`assets/metadata/` contiene anche `lesion_quality_metrics.csv`, un file **separato** (non una colonna di `participants.csv`): volume della lesione e frazione fuori dal brain per ogni soggetto, prodotto da `scripts/check_lesion_quality.py` — non "chi esiste"/"cosa sappiamo di lui", ma una cache diagnostica per decidere le soglie `min_lesion_volume_voxels`/`max_out_of_brain_fraction` di `build_lesion_matrix.py` prima di lanciare una run di produzione. Dettagli in [`docs/dev/lesion_matrix.md`](../dev/lesion_matrix.md), come lanciarlo in [`docs/guides/matrix_building.md`](matrix_building.md).

---

## Come si lancia

Prima `populate_metadata.py` (crea il file), poi `enrich_metadata.py` (aggiunge le colonne cliniche).

```bash
conda activate nemesis
cd "$PROJECT_ROOT"

PYTHONPATH="$PROJECT_ROOT" python scripts/populate_metadata.py --config config/pipelines/populate_metadata.json
python -m src.pipeline.enrich_metadata --config config/pipelines/enrich_metadata.json
```

`enrich_metadata.py` accetta anche `--dry-run`: esegue ogni controllo e scrive il report, senza toccare `participants.csv`. **Usalo sempre la prima volta dopo aver cambiato il config** — il report ti dice esattamente quante celle resteranno vuote e per quale dataset, prima di scrivere.

Su cluster: `sbatch jobs/run_enrich_metadata.sh` (la cartella `logs/slurm/enrich_metadata/` deve già esistere).

---

## Parametri di `config/pipelines/enrich_metadata.json`

| Parametro | Descrizione |
| :--- | :--- |
| **`metadata_sources`** | Path del registry `config/registry/metadata_sources.json`, che mappa ogni dataset al suo tsv grezzo. Condiviso con `populate_metadata.py`. |
| **`participants_path`** | Il file da arricchire (`assets/metadata/participants.csv`). Deve esistere già: lo crea `populate_metadata.py`. |
| **`datasets`** | Lista di dataset da processare, oppure `null` per tutti quelli presenti nel file. Un dataset fuori scope **non viene toccato**: le sue celle restano quelle che erano. |
| **`variables`** | Quali variabili scrivere. Ammesse: `age`, `sex`, `education`, `lesion_side`, `NIHSS`, `clinical_date`. Un nome non in elenco fa fallire il config subito. |
| **`lesion_volume_config`** | Path a un config `build_lesion_matrix.json`-shaped (di norma `config/pipelines/build_lesion_matrix.json` stesso) da cui ricalcolare `lesion_volume_voxels` **fresco dalle maschere** — non più copiato da un artefatto già costruito (vedi sotto). `null` non tocca quella colonna in questa run (è il "flag" per evitare di ripagare il calcolo costoso a ogni lancio quando serve solo aggiornare le variabili cliniche). |
| **`fill`** | `true`: scrive **solo** le celle vuote, ogni valore già presente resta intatto. `false`: ricalcola tutto il richiesto. |
| **`run_notes`** | Nota libera, finisce nel report. |

### Quando usare `fill: true`

Se hai corretto a mano una cella in `participants.csv` e vuoi che sopravviva a una rilanciata. Con `fill: false` verrebbe sovrascritta col valore del tsv grezzo.

### `lesion_volume_config`: perché non più un artefatto

Fino al 28-09-26 `lesion_volume_voxels` veniva copiato dal `metadata.csv` di uno specifico artefatto `build_lesion_matrix.py` già costruito — scelta presa per evitare "una seconda definizione della stessa quantità". Si è rivelata l'opposto: quell'artefatto usava una griglia diversa da quella corrente (`build_lesion_matrix.json` era passato da 1mm a 2mm nel frattempo, e l'artefatto non era stato ricostruito), e il confronto sui dati reali ha mostrato 900/5721 soggetti (15.7%) con un valore diverso tra le due fonti, fino a 38x. Ora `enrich_metadata.py` ricalcola `lesion_volume_voxels` fresco dalle maschere, riusando la stessa funzione (`src.features.lesion.compute_lesion_volumes`) di `build_lesion_matrix.py` e `scripts/check_lesion_quality.py` — un'unica implementazione, tre chiamanti, mai due fonti indipendenti che possono scivolare.

`lesion_volume_config` punta a un config `build_lesion_matrix.json`-shaped (di norma lo stesso file di produzione) da cui si leggono `data_root`/`reference_template_path`/`lesion_glob`/`binarize_threshold`/`resample_interpolation` — solo i dataset in comune tra lo scope di questa run e la lista `datasets` di quel config vengono ricalcolati; gli altri restano intoccati (warning nel log, non un errore).

**Costo**: un caricamento+resampling nibabel per soggetto — pochi minuti sull'intera coorte. Per questo `null` è il default sensato per un lancio che aggiorna solo le variabili cliniche (età, sesso, NIHSS, ...): il volume non viene ricalcolato a meno di impostarlo esplicitamente.

---

## Cosa aspettarsi nell'output

**Valori mancanti = cella vuota.** Sempre, per ogni variabile. Il file è un registro, non un input di plotting: chi ha bisogno di una sentinella (`"unknown"` in una legenda) se la applica in lettura.

**Due tipi di buco, entrambi normali e riportati, nessuno dei due è un errore:**

1. *Il dataset non ha proprio quella colonna* — es. UCL-UK non registra NIHSS. Tutti i suoi soggetti restano vuoti, con un `WARNING` nel log.
2. *Il singolo soggetto ha la cella vuota o `n/a`* in un dataset che invece la colonna ce l'ha.

**Un errore vero, invece**: un soggetto presente in `participants.csv` ma assente dal tsv grezzo del suo dataset. Vuol dire che i due file non sono d'accordo su chi esiste, cosa che l'inner join di `populate_metadata.py` dovrebbe rendere impossibile. La run si ferma.

### Sostituzioni di colonna

Se una variabile non esiste col nome canonico in un dataset, viene letta da un'altra colonna **solo** se la sostituzione è registrata a mano nel codice (`VARIABLE_SOURCE_OVERRIDES`), mai dedotta da un nome somigliante. Oggi ce n'è una: PASPORT non ha un NIHSS baseline, quindi `NIHSS` viene da `NIHSS_at_presentation`. È un'assunzione di equivalenza clinica, quindi compare a `WARNING` nel log e in una sezione dedicata del report.

---

## Chi legge questo file

Non serve copiare i valori altrove: i consumatori leggono il registro direttamente.

| Consumatore | Cosa ci prende |
| :--- | :--- |
| `build_sdc_matrix.py` | `has_lesion`, per decidere quali soggetti ammettere |
| `dim_reduction.py` / `clustering.py` | `lesion_side`/`NIHSS` per i color mode `side`/`nihss`, risolti al momento del plot |
| `notebooks/post-results_analysis/clustering_evaluation.ipynb` | età/sesso/NIHSS per le demografiche per cluster |

Conseguenza pratica: se aggiungi `NIHSS` al registro oggi, **anche le run vecchie** si possono colorare per NIHSS, senza rigenerarle.

---

## Attenzione: `has_*` descrive il disco, e il disco può essere potato

`populate_metadata.py` scandisce le cartelle per riempire `has_lesion`/`has_sdc`/`has_features`, e una scansione non vede dentro un `.tar.gz`. Le cartelle archiviate localmente per spazio (oggi `UNIPD/WashU/features/` e `data/derived/features/masked_fc/`) vanno quindi decompresse prima, oppure i `has_*` interessati vanno corretti a mano. Vedi [`docs/guides/datasets.md`](datasets.md).
