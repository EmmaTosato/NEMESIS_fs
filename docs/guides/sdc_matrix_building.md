# Guida al Matrix Building (Costruzione della Matrice SDC)

Questa guida illustra come usare `build_sdc_matrix.py` per trasformare l'output SDC già parcellato (`sdc/<subject_id>/dwi/*.csv`, prodotto a monte da `compute_sdc.py`) in una matrice numerica soggetti × regioni, pronta per `dim_reduction.py` (Task 2).

- **Script**: `src/pipeline/build_sdc_matrix.py`
- **Configurazione**: `config/pipelines/build_sdc_matrix.json`
- **Dettagli architetturali/perché è fatto così**: [`docs/dev/sdc_matrix.md`](../dev/sdc_matrix.md)

A differenza di `build_lesion_matrix.py` (voxel-wise, allineamento per griglia spaziale), qui ogni soggetto è già rappresentato come un CSV per atlante con una riga per regione anatomica — l'allineamento tra soggetti avviene per **nome regione**, non per posizione (righe non in ordine stabile tra soggetti — verificato sui dati reali).

---

## Esecuzione

### 1. Sul Server (tramite SLURM)
```bash
sbatch jobs/run_build_sdc_matrix.sh
```

### 2. In Locale
```bash
python -m src.pipeline.build_sdc_matrix --config config/pipelines/build_sdc_matrix.json
```

---

## Cos'è il "SDC Matrix Building"?

Ogni soggetto ha, per un dato atlante, un CSV `LF-disconnectome` (probabilità di disconnessione per regione) e uno `LF-lesion` (proporzione di danno diretto per regione). Lo script:
1. legge la lista di regioni autoritativa per l'atlante scelto (`assets/atlases/sdc_labels/<atlas>.csv`),
2. per ogni soggetto ammesso, riallinea il suo CSV a quella lista fissa (`reindex`), riempiendo a `0.0` le regioni omesse dal file (BCBToolKit omette le regioni a disconnessione nulla invece di scriverle esplicitamente — verificato sui dati reali),
3. impila tutto in una matrice **soggetti × regioni**, senza mai scartare colonne (anche se costanti a zero per tutti i soggetti ammessi — a differenza di `build_lesion_matrix.py`, qui la colonna `j` deve sempre significare la stessa regione, indipendentemente da quali soggetti include una data run).

**Un soggetto entra nella matrice solo se ha ENTRAMBI**: una lesion mask reale (stesso `lesion_glob` di `build_lesion_matrix.json`) e il CSV SDC richiesto. Un soggetto con output SDC ma senza lesion mask (caso reale trovato in coorte: `sub-STUKLFR0671`) viene escluso esplicitamente, non trattato come "disconnessione zero" — vedi `docs/dev/sdc_matrix.md`.

---

## Dettaglio Parametri JSON

| Parametro | Descrizione |
| :--- | :--- |
| **`project`** | Nome del progetto (es. `"clinical_connectome"`). |
| **`data_root`** | Sede dei dati grezzi estratti (es. `"data/clinical_connectome/derivatives"`). |
| **`datasets`** | Lista delle coorti da includere — solo quelle con `sdc/` (oggi: WashU, PASPORT, PSP, stroke_UKLFR; **non** UCL-UK, che non ha SDC calcolato). |
| **`group_filter`** | Lista per filtrare i pazienti sani vs malati (`["ST"]` = solo stroke). `null` non applica filtri. |
| **`lesion_glob`** | Stesso glob di `build_lesion_matrix.json`: `"manual_masks/*/anat/*_label-lesion_mask.nii.gz"` — usato per verificare che un soggetto abbia una lesion mask reale. |
| **`object`** | `"disconnectome"` (probabilità di disconnessione) o `"lesion"` (proporzione di danno diretto, parcellata). |
| **`atlas`** | Uno degli atlanti disponibili in `sdc/` (es. `"schaefer_200_tian_s2"`), **uno per run**. |
| **`value_column`** | Quale statistica per-regione estrarre: `"fraction_covered"`, `"mean_overlap"` (default consigliato), `"weighted_mean_overlap"`, `"sum_overlap"`, `"p90_overlap"`, `"p95_overlap"`. |
| **`reference_labels_path`** | File con l'elenco autoritativo e fisso delle regioni per l'atlante scelto, es. `"assets/atlases/sdc_labels/schaefer_200_tian_s2.csv"` — vedi sotto per aggiungerne uno nuovo. |
| **`output_root`** | Sede output (default: `"data/derived/sdc_matrix"`). |
| **`session_name`** | Nome univoco per il batch, es. `"s1.1"`. |
| **`overwrite`** | `true` sovrascrive output di run passati. |

### Atlanti attualmente supportati
Solo quelli con un file di reference in `assets/atlases/sdc_labels/`: `schaefer_200_tian_s2` (232 regioni), `schaefer_400_tian_s2` (432 regioni). Per aggiungerne un altro, vedi `docs/dev/sdc_matrix.md` § "Adding a new atlas". **Esclusi strutturalmente**: `buckner_7n` (il CSV ha una sola riga per soggetto, non parcellato per network — anomalia nota) e `yeh_hcp1065_streamline` (schema completamente diverso, tratti invece di regioni).

---

## Struttura dell'Output Finale

L'output vive in `data/derived/sdc_matrix/<GIORNO-MESE>_<session_name>/`:

1. **`matrix.npy`**: matrice soggetti × regioni (nessuna colonna mai scartata).
2. **`metadata.csv`**: `subject_id`, `dataset` per ogni riga della matrice, stesso ordine.
3. **`region_names.npy`**: nome di ogni colonna della matrice, nello stesso ordine — non c'è un "drop mask" da riapplicare, a differenza di `build_lesion_matrix.py`.
4. **`manifest.json`**: certificato di integrità della run.
5. **`config.md`**: config completa + esclusioni tracciate esplicitamente (per `group_filter`, per mancanza di lesion mask, e soggetti con lesion mask ma SDC non ancora calcolato).

---

## Nota nota (27/08/26): dati locali parziali

Su questa macchina locale, `manual_masks/` (lesion mask) contiene solo un piccolo campione (10 soggetti per dataset), mentre `sdc/` è già completo. Una run in locale ammette quindi solo l'intersezione disponibile localmente (40 soggetti) — non è un bug, verificato indipendentemente dal codice. Una run di produzione reale (server, o dopo un retrieval locale completo) ammetterà la quasi totalità della coorte SDC.
