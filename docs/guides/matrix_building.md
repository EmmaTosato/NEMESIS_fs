# Guida al Matrix Building (Costruzione della Matrice)

Questa guida illustra in modo dettagliato come utilizzare la pipeline `build_lesion_matrix.py` per trasformare singole maschere di lesione 3D in una matrice numerica strutturata. La matrice è il formato di base necessario per tutti gli algoritmi successivi (riduzione della dimensionalità e clustering).

**Script**: `src/pipeline/build_lesion_matrix.py`
**Configurazione**: `config/pipelines/build_lesion_matrix.json`

## Esecuzione (Locale vs Server/SLURM)

**1. Esecuzione sul Server (con SLURM)**
Sul server (es. cluster HPC), si consiglia di lanciare lo script inviandolo alla coda tramite SLURM, in modo che l'elaborazione non si interrompa se chiudi il terminale. Trovi lo script già pronto nella cartella `jobs/`:
```bash
sbatch jobs/run_build_lesion_matrix.sh
```
*(Ricordati di verificare che il file `run_build_lesion_matrix.sh` punti al JSON di configurazione che intendi usare).*

**2. Esecuzione in Locale (senza SLURM)**
Se ti trovi sul tuo PC locale (o se vuoi avviare lo script direttamente senza passare per la coda SLURM), esegui semplicemente il comando Python da terminale. Assicurati prima di aver attivato l'ambiente `nemesis` (es. `conda activate nemesis`):
```bash
python -m src.pipeline.build_lesion_matrix --config config/pipelines/build_lesion_matrix.json
```
*(Nota: in locale userai probabilmente un file di configurazione specifico, come `config/pipelines/build_lesion_matrix_local.json` se hai adattato i percorsi).*

## Il concetto: cosa significa "Matrix Building"?

Ogni paziente ha una lesione tridimensionale (una "maschera" NIfTI) in cui alcuni voxel (i "pixel" in 3D) sono sani (valore 0) e altri sono lesionati (valore 1). 
Il "Matrix Building" prende i cervelli di centinaia di pazienti e li allinea su un'unica griglia spaziale. Successivamente, estrae questi dati 3D e li "appiattisce" in una tabella 2D (una matrice):
- **Righe**: rappresentano i singoli pazienti (soggetti).
- **Colonne**: rappresentano le caratteristiche della lesione.

Le "caratteristiche" (colonne) possono essere calcolate in due modi completamente diversi, ovvero le **due categorie** di questa pipeline.

---

## Categoria 1: Matrice Voxel-wise (per singolo Voxel)

In questo approccio, il cervello viene mantenuto alla sua massima risoluzione.
- **Le Colonne**: Ogni colonna della matrice rappresenta un singolo e specifico voxel millimetrico del cervello. 
- **I Valori**: Saranno `0` (sano) o `1` (lesionato) per quel paziente in quel millimetro esatto.
- **Risultato**: Una matrice gigantesca (es. 1000 righe e 800.000 colonne). È utile per analisi statistiche precise al millimetro.

**Come si configura in `build_lesion_matrix.json`:**
```json
"parcellate": false,
"atlas_path": null,
"parcel_aggregation": null,
"save_parcellated_volumes": false
```

---

## Categoria 2: Matrice Parcellated (raggruppata per Regioni dell'Atlante)

In questo approccio, il cervello viene sovrapposto a un "Atlante" (una mappa che divide il cervello in regioni anatomiche macroscopiche, es. area di Broca, Talamo, ecc.).
- **Le Colonne**: Ogni colonna rappresenta una singola macro-regione dell'atlante (es. se l'atlante ha 372 regioni, ci saranno 372 colonne).
- **I Valori**: Saranno percentuali da `0.0` a `1.0`. Indicano **quale frazione** di quella determinata area è stata distrutta dalla lesione.
- **Risultato**: Una matrice compatta (es. 1000 righe e 372 colonne). È ideale per il clustering rapido e per capire l'impatto funzionale della lesione.

**Come si configura in `build_lesion_matrix.json`:**
```json
"parcellate": true,
"atlas_path": "assets/atlases/glasser_hcp_harvardoxford_subcortical_372.nii.gz",
"parcel_aggregation": "fraction_lesioned",
"save_parcellated_volumes": true
```
*Se abiliti `save_parcellated_volumes`, il programma salverà anche dei file 3D che mostrano a colori quali regioni si sono riempite per ciascun paziente, molto utile per ispezione visiva.*

---

## Dettaglio di tutti i Parametri JSON

Ecco la traduzione e spiegazione esatta di ogni riga nel file `config/pipelines/build_lesion_matrix.json`:

- **`project`**: `(Stringa)` Il nome del tuo progetto, usato per creare le sottocartelle. Es: `"clinical_connectome"`.
- **`data_root`**: `(Stringa)` Il percorso in cui il *Retrieve Data* ha precedentemente scaricato i dati. Es: `"data/clinical_connectome/derivatives"` (nota il livello `derivatives/`: tutto ciò che il retrieval scarica è per definizione un derivato, mai un'acquisizione grezza - vedi `docs/dev/retrieval.md`).
- **`datasets`**: `(Lista di Stringhe)` Quali coorti ospedaliere includere nella matrice. Es: `["UNIPD/WashU", "UNIPD/PASPORT", "UNIPD/PSP", "UKLFR/stroke_UKLFR"]`.
- **`reference_template_path`**: `(Stringa)` Il percorso di un file immagine NIfTI usato come "Griglia Universale". Dato che ospedali diversi acquisiscono le RM a risoluzioni diverse (1mm, 1.5mm, 2mm), tutte le lesioni verranno deformate per coincidere esattamente con questa griglia. Solitamente si usa l'immagine di un paziente WashU a 2mm, oppure un template MNI standard.
- **`lesion_glob`**: `(Stringa)` La regola per pescare i file corretti nelle cartelle dei pazienti. Lasciare sempre: `"manual_masks/*/anat/*_label-lesion_mask.nii.gz"` (layout pipeline-first: prima il nome della pipeline, poi il soggetto — vedi `docs/dev/retrieval.md`).
- **`binarize_threshold`**: `(Numero Decimale)` Valore tra 0.0 e 1.0. Quando la lesione viene deformata sulla nuova griglia (resampling), alcuni bordi potrebbero sfocarsi diventando grigi (es. 0.4). Questo parametro dice: "Tutto ciò che ha un valore sopra 0.5 diventa 1 (lesionato), tutto il resto diventa 0 (sano)".
- **`resample_interpolation`**: `(Stringa)` La matematica della deformazione spaziale. Dato che lavoriamo con maschere binarie nette (0 o 1), va usato sempre e solo `"nearest"` (arrotonda al vicino più prossimo) e non `"linear"`.
- **`parcellate`**: `(Booleano)` Scegli se fare la matrice per Atlante (`true`) o per singolo Voxel (`false`).
- **`atlas_path`**: `(Stringa)` Il file NIfTI dell'atlante desiderato. Obbligatorio se `parcellate` è `true`.
- **`parcel_aggregation`**: `(Stringa)` La matematica di raggruppamento per le regioni. Al momento supportiamo solo `"fraction_lesioned"`.
- **`save_parcellated_volumes`**: `(Booleano)` Crea dei NIfTI 3D di controllo (QC) visualizzabili con FSleyes per vedere l'atlante "riempito".
- **`output_root`**: `(Stringa)` La cartella finale per il risultato. Mettiamo `"data/derived/lesion_matrix"`.
- **`session_name`**: `(Stringa)` Un'etichetta per distinguere questa specifica matrice. Es: `"s_voxelwise_01"`. 
- **`overwrite`**: `(Booleano)` Se imposti `true`, cancella silenziosamente i risultati precedenti con lo stesso `session_name`. Se `false`, va in errore per proteggere i tuoi dati pregressi.
- **`run_notes`**: `(Stringa o null)` Eventuali note discorsive che vuoi appuntarti (es. "Matrice creata escludendo UKLFR per test").

---

## File di Input e di Output

**Input**: 
La pipeline leggerà dinamicamente le cartelle dentro `data_root` cercandovi maschere NIfTI corrispondenti a `lesion_glob`.

**Output**:
I risultati verranno generati all'interno di: `data/derived/lesion_matrix/<GIORNO-MESE>_<session_name>/`.
Troverai i seguenti file:
1. `matrix.npy`: I dati matematici puri e crudi (la matrice vera e propria). Non apribile con un editor di testo, ma leggibile tramite script Python.
2. `metadata.csv`: Una riga per paziente, con `subject_id` e `dataset` di provenienza. La riga 5 di questo file corrisponde esattamente alla riga 5 della matrice `matrix.npy`.
3. `non_constant_mask.npy`: Quando sovrapponi le lesioni di migliaia di pazienti su un cervello standard, ci sono tantissimi voxel (pixel 3D) in cui nessun paziente ha mai avuto una lesione, oppure voxel in cui tutti hanno una lesione. Queste colonne "costanti" non portano alcuna informazione utile agli algoritmi di machine learning (come PCA, UMAP o clustering), ma occupano una quantità enorme di memoria inutile. Per questo motivo, la pipeline rimuove queste colonne durante la creazione della matrice. Il file `non_constant_mask.npy` è un array booleano (Vero/Falso) lungo quanto l'intero cervello originale, che ti dice per ogni voxel se è stato "tenuto" o "scartato". Ti servirà in futuro, alla fine dell'analisi, quando vorrai prendere i tuoi risultati (es. i pesi di una PCA) e "spalmarli" di nuovo su un'immagine del cervello per poterli visualizzare spazialmente.
4. `parcel_ids.npy`: (Solo per Categoria Parcellated) Mostra l'ID dell'atlante a cui corrisponde ogni colonna della matrice.
5. `config.md`: Un mini-report che riassume le impostazioni esatte e la forma finale della matrice.
6. `parcellated_volumes/`: (Solo se richiesto) Una sottocartella con le copie 3D visualizzabili per ogni paziente.
