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
| **`excluded_subjects_path`** | La lista dei soggetti da tenere fuori (`assets/metadata/excluded_subjects.csv`). **Obbligatorio.** Vedi sotto. |
| **`correct_out_of_brain`** | `false` (default) oppure `true`: azzera i voxel di lesione fuori dalla maschera cerebrale e tiene il soggetto nella matrice, con `lesion_volume_voxels` ricalcolato sui dati corretti. Richiede `brain_mask_path`. |
| **`brain_mask_path`** | Maschera cerebrale MNI di riferimento, sulla stessa griglia di `reference_template_path` (es. `assets/templates/tpl-MNI152NLin6Asym_res-2_desc-brain_mask.nii.gz` per la griglia a 2mm attualmente in uso). **Obbligatoria** se `correct_out_of_brain` è `true`, ignorata altrimenti. |
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
5. **`config.md`**: File riassuntivo stampabile dei settaggi di questa sessione — include sempre due sezioni "Excluded by ..." (`group_filter` e la lista degli esclusi, quest'ultima con motivo e valore per ogni soggetto) e una sezione "Corrected by correct_out_of_brain", con l'elenco dei soggetti esclusi/corretti da ciascun criterio ("None." se non ha toccato nessuno).

---

## Chi entra nella matrice

Due criteri, valutati prima di scrivere la matrice:

- **`group_filter`**: chi non appartiene ai gruppi richiesti (es. i controlli sani con `["ST"]`) viene saltato in fase di scoperta.
- **`excluded_subjects_path`**: la lista curata a mano dei soggetti da tenere fuori, `assets/metadata/excluded_subjects.csv`. La maschera di un soggetto escluso **non viene nemmeno letta**.

Chi viene escluso è elencato per nome nelle sezioni "Excluded by ..." di `config.md` e nei `summaries/build_lesion_matrix/<project>/build_summary__*.md`, con motivo e valore per gli esclusi da lista.

### La lista degli esclusi

**Non ci sono soglie di qualità in questo config, di proposito.** I dati non hanno un salto naturale su cui metterne una, e quale soggetto limite valga la pena di scartare è un giudizio caso per caso che appartiene all'analisi, non alla configurazione di una pipeline.

Il file lo scrivi **a mano**, dopo aver guardato le distribuzioni in `assets/metadata/lesion_metadata.csv` dal notebook `notebooks/exploration/lesion_analysis.ipynb` — formato, vocabolario dei motivi e validazioni in [`docs/guides/metadata.md`](metadata.md).

Lo stesso file è letto anche da `build_sdc_matrix.py`, quindi **le due matrici escludono gli stessi soggetti per costruzione**: senza di questo un confronto lesione/SDC confronterebbe due coorti diverse.

Un file **assente ferma la run**: "mai scritto" e "nessuna esclusione" sono indistinguibili, e la seconda si dichiara tenendo il file con la sola intestazione.

### `correct_out_of_brain`: correggere invece di escludere

`correct_out_of_brain: true` azzera i voxel di lesione che cadono fuori dalla maschera cerebrale (`src/features/lesion_correction.py`) e mantiene il soggetto nella matrice, con `lesion_volume_voxels` ricalcolato sui dati corretti. È l'unico uso di `brain_mask_path` in questa pipeline.

È una **correzione**, non un criterio di ammissione: chi va escluso del tutto perché troppo contaminato va in `excluded_subjects.csv` con motivo `out_of_brain_fraction_too_high`. Le due cose sono compatibili, e la frazione su cui basare quella decisione sta in `lesion_metadata.csv`, misurata sulla maschera grezza.

**Una matrice già costruita non viene mai filtrata a posteriori**: aggiungere un soggetto alla lista non ha alcun effetto su un `data/derived/lesion_matrix/<sessione>/` già scritto su disco — modificherebbe silenziosamente le basi di analisi a valle già eseguite su quell'output. Se ci si accorge di aver dimenticato un'esclusione, la run va rifatta da capo (cancellare la cartella di output e la relativa riga in `runs.csv`, poi rilanciare), mai patchata in-place.

**Prima di decidere le esclusioni** serve `assets/metadata/lesion_metadata.csv`, che per ogni soggetto e ogni griglia contiene volume, frazione fuori dal brain, indice di lateralità e lato:

```bash
python -m src.pipeline.compute_lesion_metadata --config config/pipelines/compute_lesion_metadata.json
```

Il calcolo è costoso (una lettura per soggetto, un ricampionamento per griglia) — con `overwrite: false` nel config, se il csv esiste già la run esce subito senza ricalcolare. Le distribuzioni con i grafici sono in `notebooks/exploration/lesion_analysis.ipynb`, che legge quello stesso file.
