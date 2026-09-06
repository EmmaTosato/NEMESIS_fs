# Guida al Matrix Building (Costruzione della Matrice SDC)

Questa guida illustra come usare `build_sdc_matrix.py` per trasformare l'output SDC (`sdc/<subject_id>/*`, prodotto a monte da `compute_sdc.py`) in una matrice numerica pronta per `dim_reduction.py` (Task 2), in una di due **rappresentazioni** scelte dal campo `representation` della config (aggiunto 03/09):

- **`parcellated`** (originale): un CSV per atlante già parcellato (`sdc/<subject_id>/*.csv`) → matrice **soggetti × regioni**, allineamento per **nome regione**, non per posizione (righe non in ordine stabile tra soggetti — verificato sui dati reali). A differenza di `build_lesion_matrix.py`, nessuna colonna viene mai scartata.
- **`voxelwise`**: il `disconnectome-map` `.nii.gz` non ancora parcellato → matrice **soggetti × voxel**, stesso approccio di `build_lesion_matrix.py` (resampling su griglia comune), ma valori **continui** (probabilità di disconnessione 0-1), mai binarizzati. Colonne costanti (voxel fuori dal cervello di ogni soggetto ammesso) vengono scartate come in `build_lesion_matrix.py`.

- **Script**: `src/pipeline/build_sdc_matrix.py` (stesso entry point per entrambe le modalità)
- **Configurazione**: `config/pipelines/build_sdc_matrix.json`
- **Dettagli architetturali/perché è fatto così**: [`docs/dev/sdc_matrix.md`](../dev/sdc_matrix.md)

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

**Modalità `parcellated`**: ogni soggetto ha, per un dato atlante, un CSV `LF-disconnectome` (probabilità di disconnessione per regione) e uno `LF-lesion` (proporzione di danno diretto per regione). Lo script:
1. legge la lista di regioni autoritativa per l'atlante scelto (`assets/atlases/sdc_labels/<atlas>.csv`),
2. per ogni soggetto ammesso, riallinea il suo CSV a quella lista fissa (`reindex`), riempiendo a `0.0` le regioni omesse dal file (BCBToolKit omette le regioni a disconnessione nulla invece di scriverle esplicitamente — verificato sui dati reali),
3. impila tutto in una matrice **soggetti × regioni**, senza mai scartare colonne (anche se costanti a zero per tutti i soggetti ammessi — qui la colonna `j` deve sempre significare la stessa regione, indipendentemente da quali soggetti include una data run).

**Modalità `voxelwise`**: per ogni soggetto ammesso, il `disconnectome-map` `.nii.gz` viene ricampionato (se serve) sulla griglia di `reference_template_path`, appiattito e impilato in una matrice **soggetti × voxel** — mai binarizzato (a differenza della lesion mask di `build_lesion_matrix.py`, qui i valori sono una probabilità continua 0-1). I voxel costanti (fuori dal cervello per ogni soggetto ammesso) vengono scartati, con `non_constant_mask` salvato per recuperare la mappatura.

**Ammissione soggetti (uguale per entrambe le modalità)**: un soggetto entra nella matrice solo se ha **entrambi**: una lesion mask **registrata** nel TSV clinico del suo dataset (`assets/metadata/<dataset>_participants_lesions.tsv`, colonna `lesion/manual_masks/anat/lesion_mask == "present"`) e il file SDC richiesto (CSV o `.nii.gz` a seconda della modalità). Non si controlla `manual_masks/` su disco direttamente — un retrieval locale parziale renderebbe quel controllo inaffidabile (trovato 27/08/26). Un soggetto con output SDC ma senza lesion mask registrata viene escluso esplicitamente, non trattato come "disconnessione zero" — vedi `docs/dev/sdc_matrix.md`.

---

## Dettaglio Parametri JSON

Comuni a entrambe le modalità:

| Parametro | Descrizione |
| :--- | :--- |
| **`project`** | Nome del progetto (es. `"clinical_connectome"`). |
| **`data_root`** | Sede dei dati grezzi estratti (es. `"data/clinical_connectome/derivatives"`). |
| **`datasets`** | Lista delle coorti da includere — solo quelle con `sdc/` (oggi: WashU, PASPORT, PSP, stroke_UKLFR, UKE/WAKEUP_acute; **non** UCL-UK, che non ha SDC calcolato). |
| **`group_filter`** | Lista per filtrare i pazienti sani vs malati (`["ST"]` = solo stroke). `null` non applica filtri. |
| **`object`** | `"disconnectome"` (probabilità di disconnessione) o `"lesion"` (proporzione di danno diretto, parcellata) — solo `"disconnectome"` è valido con `representation: "voxelwise"`. |
| **`representation`** | `"parcellated"` o `"voxelwise"` — sceglie quali campi sotto sono richiesti. |
| **`output_root`** | Sede output (default: `"data/derived/sdc_matrix"`). |
| **`session_name`** | Nome univoco per il batch, es. `"s1.1-vol"`. |
| **`overwrite`** | `true` sovrascrive output di run passati. |

Solo per `representation: "parcellated"`:

| Parametro | Descrizione |
| :--- | :--- |
| **`atlas`** | Uno degli atlanti disponibili in `sdc/` (es. `"schaefer_200_tian_s2"`), **uno per run**. |
| **`value_column`** | Quale statistica per-regione estrarre: `"fraction_covered"`, `"mean_overlap"` (default consigliato), `"weighted_mean_overlap"`, `"sum_overlap"`, `"p90_overlap"`, `"p95_overlap"`. |
| **`reference_labels_path`** | File con l'elenco autoritativo e fisso delle regioni per l'atlante scelto, es. `"assets/atlases/sdc_labels/schaefer_200_tian_s2.csv"` — vedi sotto per aggiungerne uno nuovo. |

Solo per `representation: "voxelwise"`:

| Parametro | Descrizione |
| :--- | :--- |
| **`reference_template_path`** | Immagine `.nii.gz` che fissa la griglia comune di ricampionamento (stesso campo/ruolo di `build_lesion_matrix.json`). |
| **`resample_interpolation`** | `"linear"`, `"nearest"` o `"continuous"`. **Si usa `"nearest"`**, coerentemente con le altre pipeline che ricampionano (`build_lesion_matrix.py`, `mask_fc.py`, `src/sdc/resample.py`): sui 5 dataset SDC attuali le griglie sono tutte allineate (1mm isotropo, solo flip d'asse e shift interi), quindi `"nearest"` e `"linear"` danno output bit-identici. **Non usare `"continuous"`**: lascia rumore di arrotondamento (~1e-17) attorno allo zero che impedisce a `_drop_constant_features` di scartare i voxel costanti — vedi [`docs/dev/sdc_matrix.md`](../dev/sdc_matrix.md). |

### Atlanti attualmente supportati (solo `parcellated`)
Solo quelli con un file di reference in `assets/atlases/sdc_labels/`: `schaefer_200_tian_s2` (232 regioni), `schaefer_400_tian_s2` (432 regioni). Per aggiungerne un altro, vedi `docs/dev/sdc_matrix.md` § "Adding a new atlas". **Esclusi strutturalmente**: `buckner_7n` (il CSV ha una sola riga per soggetto, non parcellato per network — anomalia nota) e `yeh_hcp1065_streamline` (schema completamente diverso, tratti invece di regioni).

---

## Struttura dell'Output Finale

L'output vive in `data/derived/sdc_matrix/<GIORNO-MESE>_<session_name>/`:

1. **`matrix.npy`**: matrice soggetti × regioni (`parcellated`, nessuna colonna mai scartata) o soggetti × voxel (`voxelwise`, colonne costanti scartate).
2. **`metadata.csv`**: `subject_id`, `dataset` per ogni riga della matrice, stesso ordine.
3. **`region_names.npy`** (solo `parcellated`) o **`non_constant_mask.npy`** (solo `voxelwise`, come in `build_lesion_matrix.py`) — mai entrambi nella stessa run.
4. **`manifest.json`**: certificato di integrità della run.
5. **`config.md`**: config completa + esclusioni tracciate esplicitamente (per `group_filter`, per mancanza di lesion mask, e soggetti con lesion mask ma SDC non ancora calcolato).

---

## Nota (27/08/26): perché il controllo è sul TSV clinico, non su `manual_masks/`

Su questa macchina locale, `manual_masks/` (lesion mask) contiene solo un piccolo campione (10 soggetti per dataset), mentre `sdc/` è già completo — un controllo basato sul disco locale ammetteva quindi solo 40 soggetti su 1151, ed escludeva erroneamente soggetti che in realtà hanno una lesion mask reale (solo non ancora retrievata su questa macchina). Risolto controllando `assets/metadata/<dataset>_participants_lesions.tsv` invece del disco: con questo criterio la run reale ammette 1119/1151 soggetti, e i 32 esclusi sono confermati genuinamente assenti dal registro clinico (non un artefatto di retrieval locale).
