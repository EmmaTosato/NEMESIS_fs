# Guida al Matrix Building (Costruzione della Matrice di Lesione)

Questa guida illustra in modo dettagliato come utilizzare la pipeline `build_lesion_matrix.py` per trasformare singole maschere di lesione 3D in una matrice numerica strutturata (voxel-wise). **La matrice è il formato di base necessario** per tutti gli algoritmi successivi.

- **Script**: `src/pipeline/build_lesion_matrix.py`
- **Configurazione**: `config/pipelines/build_lesion_matrix.json` *(usata sia per locale che server)*

La produzione attuale (`session_name: "voxelwise_s2"`) copre tutte le coorti in-scope — elenco
completo, N e dettagli per-coorte in [`docs/guides/datasets.md`](datasets.md), non ripetuti qui
(così un dataset aggiunto/rimosso non richiede modifiche a questa guida). Struttura dati identica
su ogni coorte in-scope (`manual_masks/{subject_id}/anat/{subject_id}_space-MNI152NLin6Asym_label-lesion_mask.nii.gz`,
stesso spazio MNI152NLin6Asym), quindi nessun cambio di logica nella pipeline dovuto
all'aggiunta/rimozione di una coorte — solo il campo `datasets` nel config.

> **Nota**: `build_lesion_matrix.py` produce solo matrici voxel-wise — non esiste una modalità
> *parcellated* (matrice per macro-aree anatomiche via atlante) per questa pipeline.

---

## Esecuzione

### 1. Sul Server (tramite SLURM)
L'esecuzione tramite SLURM previene interruzioni dovute alla chiusura della connessione:
```bash
sbatch jobs/run_build_lesion_matrix.sh
```

### 2. In Locale
Dal PC locale, dopo aver attivato l'ambiente `nemesis`:
```bash
python -m src.pipeline.build_lesion_matrix --config config/pipelines/build_lesion_matrix.json
```

---

## Cos'è il "Matrix Building"?

Le lesioni 3D binarie (sano=0, rotto=1) dei pazienti devono essere allineate e standardizzate. Lo script estrae i dati spaziali e li "appiattisce" in una tabella matematica a 2 Dimensioni:
- **Righe**: Rappresentano i singoli pazienti.
- **Colonne**: Rappresentano un singolo voxel millimetrico (fino a 800.000 colonne).
- **Valori**: `0` o `1`.
- **Ideale per**: Analisi statistiche micro-strutturali, embedding/clustering a piena risoluzione.

---

## Dettaglio Parametri JSON

Spiegazione delle chiavi di `config/pipelines/build_lesion_matrix.json`:

| Parametro | Descrizione |
| :--- | :--- |
| **`project`** | Nome del progetto (es. `"clinical_connectome"`). |
| **`data_root`** | Sede dei dati grezzi estratti (es. `"data/clinical_connectome/derivatives"`). |
| **`datasets`** | Lista delle coorti da includere (es. `["UNIPD/WashU", ...]`). |
| **`group_filter`** | Lista per filtrare i pazienti sani vs malati. `["ST"]` include solo gli "Stroke". `null` non applica filtri. |
| **`reference_template_path`** | File MNI di riferimento spaziale per la "Deformazione/Resampling" di tutte le lesioni. |
| **`lesion_glob`** | Il percorso fisso dei file (non toccare): `"manual_masks/*/anat/*_label-lesion_mask.nii.gz"`. |
| **`binarize_threshold`** | (Solitamente `0.5`). Trasforma contorni grigi della deformazione spaziale in lesione netta (1 o 0). |
| **`resample_interpolation`**| La matematica della deformazione spaziale (`"linear"`/`"nearest"`/`"continuous"` — vedi `_KNOWN_INTERPOLATIONS` in `src/analysis/build_config.py`). **Per una maschera binaria si usa `"nearest"`** — motivazione, sfumature del downsampling e interazione con `binarize_threshold` in [`knowledge/neuroimaging/lesion_resampling.md`](../../knowledge/neuroimaging/lesion_resampling.md). |
| **`min_lesion_volume_voxels`** | `null` (default, nessun filtro) oppure un intero ≥ 0: i soggetti con `lesion_volume_voxels` sotto questa soglia vengono esclusi dalla matrice. |
| **`max_out_of_brain_fraction`** | `null` (default, nessun filtro) oppure un valore in `[0.0, 1.0]`: i soggetti con più di questa frazione di voxel di lesione fuori dalla maschera cerebrale vengono esclusi. Richiede `brain_mask_path`. |
| **`brain_mask_path`** | Maschera cerebrale MNI di riferimento, sulla stessa griglia di `reference_template_path` (es. `assets/templates/tpl-MNI152NLin6Asym_res-2_desc-brain_mask.nii.gz` per la griglia a 2mm attualmente in uso). **Obbligatoria** solo se `max_out_of_brain_fraction` non è `null`, ma resta letta (non ignorata) anche a soglia disattivata — la usa anche `scripts/check_lesion_quality.py`, indipendentemente da questa soglia. |
| **`output_root`** | Sede file (di base: `"data/derived/lesion_matrix"`). |
| **`session_name`** | Nome univoco per distinguere i batch es. `"voxelwise_s2"`. |
| **`overwrite`** | `true` sovrascrive output di run passati. |

---

## Struttura dell'Output Finale

L'output vive in `data/derived/lesion_matrix/<GIORNO-MESE>_<session_name>/` e contiene:

1. **`matrix.npy`**: La matrice matematicamente pura da processare.
2. **`metadata.csv`**: L'anagrafica che relaziona ogni riga della matrice al paziente (Es. Riga 5 della matrice appartiene a Sub-ID-X).
3. **`non_constant_mask.npy`**: Le lesioni su migliaia di pazienti hanno zone in cui "nessuno ha mai avuto un danno". Vengono tolte dalla matrice per tagliare dimensioni inutili di calcolo. Questo array ricorda quali colonne esatte sono state tagliate, per riposizionarle al momento dei report visivi su immagini del cervello.
4. **`manifest.json`**: Il "Certificato di Integrità". Se manca, la pipeline ha fallito.
5. **`config.md`**: File riassuntivo stampabile dei settaggi di questa sessione — include sempre tre sezioni "Excluded by ..." (`group_filter`, `min_lesion_volume_voxels`, `max_out_of_brain_fraction`), con l'elenco dei soggetti esclusi da ciascun criterio ("None." se il filtro non è attivo o non ha escluso nessuno).

---

## Filtri di qualità della lesione (soglie opzionali)

`min_lesion_volume_voxels` e `max_out_of_brain_fraction` sono due criteri di ammissione opzionali, valutati per ogni soggetto prima di scrivere la matrice finale:

- **`min_lesion_volume_voxels`**: esclude i soggetti con lesione troppo piccola (in voxel, sulla griglia comune di `reference_template_path`).
- **`max_out_of_brain_fraction`**: esclude i soggetti con troppi voxel di lesione fuori dalla maschera cerebrale (`brain_mask_path`) — un indizio di errore di normalizzazione/segmentazione, stessa logica di `scripts/lesion_fix.py`.

Entrambi sono `null` di default (nessun filtro). I soggetti risultanti dopo l'applicazione dei filtri sono quelli che compaiono in `metadata.csv`; chi viene escluso è elencato per nome nelle sezioni "Excluded by ..." di `config.md` e nei `summaries/build_lesion_matrix/<project>/build_summary__*.md`.

**Una matrice già costruita non viene mai filtrata a posteriori**: cambiare queste soglie non ha alcun effetto su un `data/derived/lesion_matrix/<sessione>/` già scritto su disco — modificherebbe silenziosamente le basi di analisi a valle già eseguite su quell'output. Se ci si accorge di aver dimenticato di impostare una soglia, la run va rifatta da capo (cancellare la cartella di output e la relativa riga in `runs.csv`, poi rilanciare la pipeline con il config corretto), mai patchata in-place.

**Prima di fissare una soglia**, conviene ispezionare la distribuzione reale invece di indovinare un valore: `scripts/check_lesion_quality.py` calcola `lesion_volume_voxels`/`out_of_brain_fraction` per ogni soggetto (stesso config `build_lesion_matrix.json`, nessuna soglia applicata) e li salva in `assets/metadata/lesion_quality_metrics.csv`:

```bash
PYTHONPATH="$PROJECT_ROOT" python scripts/check_lesion_quality.py --config config/pipelines/build_lesion_matrix.json
```

Il calcolo è costoso (minuti sull'intera coorte) — di default, se `assets/metadata/lesion_quality_metrics.csv` esiste già, lo script non ricalcola nulla; `--overwrite` forza il ricalcolo. La stessa esplorazione, con grafici della distribuzione, è in `notebooks/exploration/dataset_exploration.ipynb` ("Lesione fuori dal brain"), che legge/scrive lo stesso file.
