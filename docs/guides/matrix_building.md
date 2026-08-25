# Guida al Matrix Building (Costruzione della Matrice di Lesione)

Questa guida illustra in modo dettagliato come utilizzare la pipeline `build_lesion_matrix.py` per trasformare singole maschere di lesione 3D in una matrice numerica strutturata. **La matrice è il formato di base necessario** per tutti gli algoritmi successivi.

- **Script**: `src/pipeline/build_lesion_matrix.py`
- **Configurazione**: `config/pipelines/build_lesion_matrix.json` *(usata sia per locale che server)*

La produzione attuale (`session_name: "yan300s2"`) copre tutte e 5 le coorti in-scope, incluso
`UCL-UK/UCLStrokeData` (4119 soggetti stroke, retrieved e verificati 21/08/26) — elenco completo
e dettagli per-coorte in [`docs/guides/datasets.md`](datasets.md), non ripetuti qui. Struttura dati
identica su tutte e 5 (`manual_masks/{subject_id}/anat/{subject_id}_space-MNI152NLin6Asym_label-lesion_mask.nii.gz`,
stesso spazio MNI152NLin6Asym), quindi nessun cambio di logica nella pipeline dovuto al nuovo
dataset — solo un `datasets` più lungo nel config. Atlante usato in produzione: `Yan300TianS2Buckner7N`
(339 regioni), non l'atlante combinato Glasser+Harvard-Oxford (372 regioni) usato come esempio nella
sezione "Categoria 2" sotto — entrambi esistono in `assets/atlases/` e sono intercambiabili via
`atlas_path`, la scelta di produzione è solo quella indicata da `atlas_path` nel config corrente.

---

## Esecuzione

### 1. Sul Server (tramite SLURM)
L'esecuzione tramite SLURM previene interruzioni dovute alla chiusura della connessione.
Con l'aggiunta di UCL-UK la coorte totale sale da ~1150 a ~5270 soggetti stroke — **eseguire
sempre via SLURM**, non in locale, con questa configurazione:
```bash
sbatch jobs/run_build_lesion_matrix.sh
```

### 2. In Locale
Dal PC locale, dopo aver attivato l'ambiente `nemesis` — indicato solo per config ridotte
(subset di `datasets`/`group_filter`, o iterazione rapida su pochi soggetti), non per la
config di produzione a 5 coorti:
```bash
python -m src.pipeline.build_lesion_matrix --config config/pipelines/build_lesion_matrix.json
```

---

## Cos'è il "Matrix Building"?

Le lesioni 3D binarie (sano=0, rotto=1) dei pazienti devono essere allineate e standardizzate. Lo script estrae i dati spaziali e li "appiattisce" in una tabella matematica a 2 Dimensioni:
- **Righe**: Rappresentano i singoli pazienti.
- **Colonne**: Rappresentano le caratteristiche della lesione, che possono essere classificate in due Categorie operative (Voxel-wise o Parcellated).

---

## Categorie (Le due Vie del Matrix Building)

### Categoria 1: Matrice Voxel-wise (Massima Risoluzione)
Il cervello viene mantenuto in alta definizione.
- **Colonne**: Un singolo voxel millimetrico (fino a 800.000 colonne).
- **Valori**: `0` o `1`.
- **Ideale per**: Analisi statistiche micro-strutturali, non indicato per raggruppamento veloce.
- **JSON**: `"parcellate": false, "atlas_path": null`

### Categoria 2: Matrice Parcellated (Per Aree Anatomiche)
La lesione viene sovrapposta a un Atlante che divide la materia grigia e bianca in Macro Aree.
- **Colonne**: Le regioni logiche (Es. l'atlante combinato Glasser possiede 372 regioni/colonne).
- **Valori**: Frazioni da `0.0` a `1.0` (indicanti la percentuale di area distrutta dalla lesione).
- **Ideale per**: Clustering macroscopico veloce e studi cognitivi.
- **JSON**: `"parcellate": true, "atlas_path": "path_all_atlante"`

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
| **`resample_interpolation`**| La matematica della deformazione spaziale **solo per le maschere di lesione** (`"linear"`/`"nearest"`/`"continuous"` — vedi `_KNOWN_INTERPOLATIONS` in `src/analysis/build_config.py`). **Non governa il resampling dell'atlante**: quando `parcellate: true`, l'atlante viene sempre resampiato con `"nearest"`, indipendentemente da questo valore (un atlante di label discrete non può essere interpolato linearmente senza inventare valori — vedi `docs/dev/lesion_matrix.md`/`AUDIT_FINDINGS.md` #67). |
| **`parcellate`** | `true` (Categoria 2) o `false` (Categoria 1). |
| **`atlas_path`** | Necessario solo se parcellate=true. Il NIfTI dell'atlante desiderato. |
| **`parcel_aggregation`** | Attualmente supportato solo `"fraction_lesioned"`. |
| **`save_parcellated_volumes`** | (Solo Cat 2) Genera le visualizzazioni NIfTI 3D di controllo QC del paziente "riempito" a colori. |
| **`output_root`** | Sede file (di base: `"data/derived/lesion_matrix"`). |
| **`session_name`** | Nome univoco per distinguere i batch es. `"s_voxelwise_01"`. |
| **`overwrite`** | `true` sovrascrive output di run passati. |

---

## Struttura dell'Output Finale

L'output vive in `data/derived/lesion_matrix/<GIORNO-MESE>_<session_name>/` e contiene:

1. **`matrix.npy`**: La matrice matematicamente pura da processare.
2. **`metadata.csv`**: L'anagrafica che relaziona ogni riga della matrice al paziente (Es. Riga 5 della matrice appartiene a Sub-ID-X).
3. **`non_constant_mask.npy`**: Le lesioni su migliaia di pazienti hanno zone in cui "nessuno ha mai avuto un danno". Vengono tolte dalla matrice per tagliare dimensioni inutili di calcolo. Questo array ricorda quali colonne esatte sono state tagliate, per riposizionarle al momento dei report visivi su immagini del cervello.
4. **`parcel_ids.npy`**: (Solo Parcellated). Indica l'ID dell'atlante corrispondente alla colonna.
5. **`manifest.json`**: Il "Certificato di Integrità". Se manca, la pipeline ha fallito. 
6. **`config.md`**: File riassuntivo stampabile dei settaggi di questa sessione.
