# Guida al Matrix Building (Costruzione della Matrice SDC)

Questa guida illustra come usare `build_sdc_matrix.py` per trasformare l'output SDC (`sdc/<subject_id>/*`, prodotto a monte da BCBToolKit) in una matrice numerica pronta per `dim_reduction.py` (Task 2), in una di tre **rappresentazioni** scelte dal campo `representation` della config:

- **`parcellated`** (originale): un CSV per atlante già parcellato (`sdc/<subject_id>/*.csv`) → matrice **soggetti × regioni**, allineamento per **nome regione**, non per posizione (righe non in ordine stabile tra soggetti — verificato sui dati reali). A differenza di `build_lesion_matrix.py`, nessuna colonna viene mai scartata.
- **`voxelwise`**: il `disconnectome-map` `.nii.gz` non ancora parcellato → matrice **soggetti × voxel**, stesso approccio di `build_lesion_matrix.py` (resampling su griglia comune), ma valori **continui** (probabilità di disconnessione 0-1), mai binarizzati. Colonne costanti (voxel fuori dal cervello di ogni soggetto ammesso) vengono scartate come in `build_lesion_matrix.py`.
- **`streamline`**: il CSV `LF-lesion_atlas-yeh_hcp1065_streamline.csv` (colonne `tract,streamline_ratio`) → matrice **soggetti × tratti** (87 tratti di sostanza bianca), un valore per tratto: la quota di streamline di quel tratto colpite. Allineamento per **nome del tratto**; nessuna colonna scartata, come in `parcellated`. Nonostante la famiglia `LF-lesion` è una misura di disconnessione, quindi appartiene alla track `s2.x` (vedi [`data_sessions.md`](../experiments/data_sessions.md)).

- **Script**: `src/pipeline/build_sdc_matrix.py` (stesso entry point per tutte e tre le modalità)
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

**Modalità `streamline`**: ogni soggetto ha un CSV `LF-lesion_atlas-yeh_hcp1065_streamline.csv` con 87 righe, una per tratto di sostanza bianca, e una colonna `streamline_ratio` (la quota di streamline di quel tratto colpite). Lo script riallinea il CSV alla lista fissa dei tratti (`assets/atlases/sdc_labels/yeh_hcp1065_streamline.csv`) e impila tutto in una matrice **soggetti × 87 tratti**, senza mai scartare colonne.

A differenza di `parcellated`, qui un tratto **mancante** dal CSV fa fallire la run invece di essere riempito a `0.0`: questo file elenca sempre tutti i tratti, zeri inclusi (verificato su tutti i 1734 file reali, 30-09-26), quindi un file incompleto è troncato o corrotto, non una omissione legittima.

**Ammissione soggetti (uguale per tutte e tre le modalità)**: un soggetto entra nella matrice solo se ha **entrambi**: una lesion mask **registrata** nel registro soggetti (`assets/metadata/participants.csv`, colonna `has_lesion == True`) e il file SDC richiesto (CSV o `.nii.gz` a seconda della modalità), **e** non compare nella lista degli esclusi (`excluded_subjects_path`, obbligatorio nel config: `assets/metadata/excluded_subjects.csv`). Non si controlla `manual_masks/` su disco direttamente — una copia locale parziale renderebbe quel controllo inaffidabile. Un soggetto con output SDC ma senza lesion mask registrata viene escluso esplicitamente, non trattato come "disconnessione zero" — vedi `docs/dev/sdc_matrix.md`.

La lista degli esclusi è **la stessa** che legge `build_lesion_matrix.py`, quindi le due matrici tengono fuori gli stessi soggetti per costruzione: senza di questo un confronto lesione/SDC confronterebbe due coorti diverse. Formato e validazioni in [`docs/guides/metadata.md`](metadata.md); un file assente ferma la run, "nessuna esclusione" si dichiara tenendolo con la sola intestazione.

---

## Dettaglio Parametri JSON

Comuni a entrambe le modalità:

| Parametro | Descrizione |
| :--- | :--- |
| **`project`** | Nome del progetto (es. `"clinical_connectome"`). |
| **`data_root`** | Sede dei dati grezzi estratti (es. `"data/clinical_connectome/derivatives"`). |
| **`datasets`** | Lista delle coorti da includere — solo quelle con `sdc/` (oggi tutti e 8 i dataset stroke: WashU, PASPORT, PSP, stroke_UKLFR, UCL-UK, UKE/WAKEUP_acute, NEMESIS_T0, SFB936_ses01; il CSV streamline `yeh_hcp1065_streamline` manca solo a UCL-UK). |
| **`group_filter`** | Lista per filtrare i pazienti sani vs malati (`["ST"]` = solo stroke). `null` non applica filtri. |
| **`object`** | `"disconnectome"` (probabilità di disconnessione) o `"lesion"` (proporzione di danno diretto, parcellata). Vincolato dalla `representation`: solo `"disconnectome"` con `"voxelwise"`, solo `"lesion"` con `"streamline"`. |
| **`representation`** | `"parcellated"`, `"voxelwise"` o `"streamline"` — sceglie quali campi sotto sono richiesti. |
| **`output_root`** | Sede output (default: `"data/derived/sdc_matrix"`). |
| **`session_name`** | Nome univoco per il batch, es. `"s1.1-vol"`. |
| **`overwrite`** | `true` sovrascrive output di run passati. |

Solo per `representation: "parcellated"`:

| Parametro | Descrizione |
| :--- | :--- |
| **`atlas`** | Uno degli atlanti disponibili in `sdc/` (es. `"schaefer_200_tian_s2"`), **uno per run**. |
| **`value_column`** | Quale statistica per-regione estrarre: `"fraction_covered"`, `"mean_overlap"` (default consigliato), `"weighted_mean_overlap"`, `"sum_overlap"`, `"p90_overlap"`, `"p95_overlap"`. |
| **`reference_labels_path`** | File con l'elenco autoritativo e fisso delle regioni per l'atlante scelto, es. `"assets/atlases/sdc_labels/schaefer_200_tian_s2.csv"` — vedi sotto per aggiungerne uno nuovo. |

Solo per `representation: "streamline"`:

| Parametro | Descrizione |
| :--- | :--- |
| **`reference_labels_path`** | File con l'elenco autoritativo e fisso degli 87 tratti: `"assets/atlases/sdc_labels/yeh_hcp1065_streamline.csv"` (una colonna `tract`). |

Non prende né `atlas` né `value_column`: c'è un solo file streamline per soggetto e una sola colonna di valori, quindi non c'è nulla da scegliere (l'atlante è fissato a `yeh_hcp1065_streamline` nel codice e registrato comunque in `config.md`).

Solo per `representation: "voxelwise"`:

| Parametro | Descrizione |
| :--- | :--- |
| **`reference_template_path`** | Immagine `.nii.gz` che fissa la griglia comune di ricampionamento (stesso campo/ruolo di `build_lesion_matrix.json`). |
| **`resample_interpolation`** | `"linear"`, `"nearest"` o `"continuous"`. **Si usa `"nearest"`**, coerentemente con le altre pipeline che ricampionano (`build_lesion_matrix.py`, `mask_fc.py`). I `disconnectome-map` sono a 1mm e il template di riferimento del progetto è a 2mm (vedi [`docs/experiments/processing/matrices.md`](../experiments/processing/matrices.md)), quindi qui avviene un vero downsampling: `"nearest"` tiene 1 voxel su 8 invece di mediarli, e **non** è equivalente a `"linear"`. La perdita è accettata perché i valori di disconnessione variano gradualmente nello spazio. **Non usare `"continuous"`**: lascia rumore di arrotondamento (~1e-17) attorno allo zero che impedisce a `_drop_constant_features` di scartare i voxel costanti — vedi [`docs/dev/sdc_matrix.md`](../dev/sdc_matrix.md). |

### Atlanti attualmente supportati (solo `parcellated`)
Solo quelli con un file di reference in `assets/atlases/sdc_labels/`: `schaefer_200_tian_s2` (232 regioni), `schaefer_400_tian_s2` (432 regioni). Per aggiungerne un altro, vedi `docs/dev/sdc_matrix.md` § "Adding a new atlas". **Escluso strutturalmente**: `buckner_7n` (il CSV ha una sola riga per soggetto, non parcellato per network — anomalia nota). `yeh_hcp1065_streamline` ha uno schema completamente diverso (tratti invece di regioni) e non è gestito qui, ma dalla sua `representation: "streamline"`.

---

## Struttura dell'Output Finale

L'output vive in `data/derived/sdc_matrix/<GIORNO-MESE>_<session_name>/`:

1. **`matrix.npy`**: matrice soggetti × regioni (`parcellated`), soggetti × tratti (`streamline`) — in entrambi i casi nessuna colonna mai scartata — o soggetti × voxel (`voxelwise`, colonne costanti scartate).
2. **`metadata.csv`**: `subject_id`, `dataset` per ogni riga della matrice, stesso ordine.
3. **`region_names.npy`** (solo `parcellated`), **`tract_names.npy`** (solo `streamline`) o **`non_constant_mask.npy`** (solo `voxelwise`, come in `build_lesion_matrix.py`) — mai più di uno nella stessa run.
4. **`manifest.json`**: certificato di integrità della run.
5. **`config.md`**: config completa + esclusioni tracciate esplicitamente (per `group_filter`, per mancanza di lesion mask, e soggetti con lesion mask ma SDC non ancora calcolato).
