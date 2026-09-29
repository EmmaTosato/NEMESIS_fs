# Metadati dei soggetti — come si usano

Tutto ciò che sappiamo dei soggetti sta in **un file solo**: `assets/metadata/participants.csv`, versionato in git, una riga per soggetto.

Lo scrivono due script, che rispondono a due domande diverse e non si sovrascrivono mai a vicenda:

| Script | Domanda | Colonne che scrive |
| :--- | :--- | :--- |
| `scripts/populate_metadata.py` | chi esiste | `subject_id`, `original_id`, `dataset`, `disease_id`, `has_lesion`, `has_sdc`, `has_features` |
| `src/pipeline/enrich_metadata.py` | cosa sappiamo di lui | `age`, `sex`, `education`, `lesion_side`, `lesion_side_source`, `NIHSS`, `clinical_date`, `lesion_volume_voxels` |

- **Dettagli architetturali/perché è fatto così**: [`docs/dev/metadata.md`](../dev/metadata.md)
- **Quali campi esistono in quale dataset**: [`docs/guides/datasets.md`](datasets.md)

`assets/metadata/` contiene anche `lesion_quality_metrics.csv`, un file **separato** (non una colonna di `participants.csv`): volume della lesione e frazione fuori dal brain per ogni soggetto, prodotto da `src/pipeline/check_lesion_quality.py` — non "chi esiste"/"cosa sappiamo di lui", ma una cache diagnostica per decidere le soglie `min_lesion_volume_voxels`/`max_out_of_brain_fraction` di `build_lesion_matrix.py` prima di lanciare una run di produzione. Dettagli in [`docs/dev/lesion_matrix.md`](../dev/lesion_matrix.md), come lanciarlo in [`docs/guides/matrix_building.md`](matrix_building.md).

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
| **`lesion_metrics`** | Oggetto opzionale (`null` disattiva tutto) — tutto ciò che si calcola fresco dalle maschere: `lesion_volume_voxels` e, in fallback, `lesion_side`. Vedi sotto. |
| **`fill`** | `true`: scrive **solo** le celle vuote, ogni valore già presente resta intatto. `false`: ricalcola tutto il richiesto. |
| **`run_notes`** | Nota libera, finisce nel report. |

### Quando usare `fill: true`

Se hai corretto a mano una cella in `participants.csv` e vuoi che sopravviva a una rilanciata. Con `fill: false` verrebbe sovrascritta col valore del tsv grezzo.

### `lesion_metrics`: tutto ciò che si calcola fresco dalle maschere

```json
"lesion_metrics": {
  "build_matrix_config": "config/pipelines/build_lesion_matrix.json",
  "correct_out_of_brain": false,
  "compute_volume": true,
  "compute_side": true,
  "side_threshold": 0.2
}
```

Un unico blocco (invece di un config per metadato) perché tutto viene dalla stessa fonte — le maschere — e condivide la stessa scelta di correzione:

- **`build_matrix_config`**: config `build_lesion_matrix.json`-shaped (di norma lo stesso file di produzione) da cui si leggono `data_root`/`reference_template_path`/`lesion_glob`/`binarize_threshold`/`resample_interpolation`/`brain_mask_path`. Un dataset fuori dalla sua lista `datasets` non riceve né volume né lato — `WARNING` nel log per nome, mai un errore.
- **`correct_out_of_brain`**: azzera i voxel di lesione fuori dal cervello prima di contare — stessa correzione che `build_lesion_matrix.py` applica alla matrice di produzione (`correct_out_of_brain` nel suo stesso config), ma è una flag **indipendente**: non c'è alcun obbligo di tenerla allineata a quella di `build_lesion_matrix.json`. Le due pipeline hanno scopi diversi — questo registro serve per colorare i plot e per la demografia, `build_lesion_matrix.py` costruisce l'input per l'embedding, e può essere rilanciato più volte con `session_name`/impostazioni diverse tra loro. Non è come il caso del 28-09-26 (sotto): lì un valore veniva *copiato* da un artefatto vecchio spacciandolo per aggiornato; qui entrambe le pipeline calcolano il proprio valore fresco, con la propria configurazione esplicita — differire è una scelta legittima, non un bug.
- **`compute_volume`**: scrive `lesion_volume_voxels`. Fino al 28-09-26 questo valore veniva copiato dal `metadata.csv` di uno specifico artefatto `build_lesion_matrix.py` già costruito — scelta presa per evitare "una seconda definizione della stessa quantità", rivelatasi l'opposto (quell'artefatto usava una griglia ormai diversa da quella corrente, 900/5721 soggetti con un valore diverso tra le due fonti, fino a 38x). Ora si ricalcola fresco (`src.features.lesion.compute_lesion_volumes`), riusata anche da `build_lesion_matrix.py` e `src/pipeline/check_lesion_quality.py`.
- **`compute_side`**: riempie `lesion_side` **solo** per i soggetti ancora vuoti dopo la risoluzione clinica — un valore clinico non viene mai sovrascritto. Per ognuno, conta i voxel di lesione a sinistra/destra della midline MNI dalla sua maschera e calcola un indice di lateralità; sopra `side_threshold` classifica `left`/`right`, sotto classifica `both` (bilaterale). Il risultato è marcato `lesion_side_source = "geometric"`, distinguibile per sempre da un valore clinico. Richiede `lesion_side` in `variables`.
- **`side_threshold`**: **0.20 in produzione, calibrato, non inventato** — riproduce il 97.4% di 1445 soggetti con etichetta clinica vera (metodo, letteratura di riferimento e limiti in [`knowledge/neuroimaging/lesion_laterality.md`](../../knowledge/neuroimaging/lesion_laterality.md)). Non cambiarlo senza aver ricalibrato con `scripts/calibrate_lesion_side_threshold.py`.

**Nessuna lista di esclusione per soggetto.** Se in analisi trovi un valore inaffidabile (volume o lato), correggilo **a mano direttamente in `participants.csv`** — `fill: true` alla run successiva lo lascia intatto, come qualunque altra cella corretta manualmente.

**Costo**: un caricamento+resampling nibabel per soggetto — pochi minuti sull'intera coorte quando entrambe le flag sono `true`. `lesion_metrics: null` è il default sensato per un lancio che aggiorna solo le variabili cliniche (età, sesso, NIHSS, ...).

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
