# Guida al Retrieval dei Dati

Questa guida spiega in parole semplici e chiare come usare la pipeline di retrieval. L'obiettivo di questo script è "copiare in modo intelligente" le immagini cerebrali dal server centrale (EBRAIN) al tuo computer locale (nella cartella `data/`), preparandole per l'analisi.

## Esecuzione (Locale vs Server/SLURM)

**1. Esecuzione sul Server (con SLURM)**
Sul server, lancia lo script inviandolo alla coda tramite SLURM (così non si interrompe se chiudi la connessione). Trovi lo script in `jobs/`:
```bash
sbatch jobs/run_retrieve_data.sh
```

**2. Esecuzione in Locale (senza SLURM)**
Dal tuo PC locale, dopo aver attivato l'ambiente `nemesis`, lancia la pipeline direttamente da terminale:
```bash
python -m src.pipeline.retrieve_data --config config/pipelines/retrieval_local.json
```
Esistono due varianti di config, non una sola: `retrieval_server.json` (path EBRAIN reale, `/data/corbetta/Clinical_connectome/...`, usato in produzione da `jobs/run_retrieve_data.sh`) e `retrieval_local.json` (stesso contenuto, path Windows per un mount locale). Ognuna punta al proprio registro (`file_patterns_server.json`/`file_patterns_local.json`) — vanno tenuti allineati a mano quando cambi una voce in uno dei due.

Tutte le regole su cosa scaricare, quali pazienti scegliere, e dove salvare i file si definiscono nel file JSON di configurazione indicato nel comando.
---

## Retrieve Data (`src/pipeline/retrieve_data.py`)

**Cosa fa**: La pipeline si collega alla tua sorgente dati, legge quali pazienti o gruppi le hai chiesto di cercare, ispeziona le loro cartelle, verifica che i file richiesti (come le maschere di lesione) siano effettivamente presenti e, infine, li copia sul tuo computer preservando l'esatta struttura BIDS delle cartelle. È progettato per essere "sicuro": se mancano dei file o ci sono problemi, non si blocca ma annota tutto in un report dettagliato per farti sapere chi manca all'appello.
**File di Configurazione**: `config/pipelines/retrieval_server.json` (produzione) / `retrieval_local.json` (locale)
**Input**: I file sorgente sul mount EBRAIN (es. `/data/corbetta/Clinical_connectome`).
**Output**: Le copie locali dei file in `data/`, e un utilissimo report di sintesi in `summaries/data_retrieval/`.

### Spiegazione dei Parametri (`retrieval_server.json`/`retrieval_local.json`)

Ecco tutti i valori possibili e cosa significano, riga per riga:

- `output_root`: Dove vuoi posizionare le copie. Solitamente si lascia `"data/"`.
- `project`: Il nome del progetto, usato per creare la sottocartella principale. Mettendo `"clinical_connectome"`, i file andranno in `data/clinical_connectome/derivatives/<dataset>/<pipeline>/<soggetto>/...` — sempre sotto un unico livello `derivatives/` comune a tutti i dataset (perché tutto ciò che questa pipeline scarica è per definizione un derivato, mai un'acquisizione grezza), e **prima il nome della pipeline, poi il soggetto** (ordine BIDS-Derivatives reale): es. `data/clinical_connectome/derivatives/UNIPD/WashU/manual_masks/sub-STUNIPD0001/anat/...` per le lesioni, `.../features/sub-STUNIPD0131/func/...` per le feature (`features` è un nome scelto da noi per comodità locale, dato che questi dati non hanno un vero nome di pipeline alla sorgente — vedi `docs/dev/retrieval.md`).
- `file_patterns`: Il percorso del "registro" delle regole di nomenclatura (`"config/registry/file_patterns_server.json"` o `_local.json`, coerente con la variante di `retrieval_*.json` che stai usando). Non serve modificarlo per un run normale, serve al codice per tradurre i concetti logici (es. "FC-pearson") nei percorsi file esatti richiesti dal sistema.
- `datasets`: Un elenco delle raccolte di pazienti da includere. I 4 dataset noti sono: `UNIPD/WashU`, `UNIPD/PASPORT`, `UNIPD/PSP`, `UKLFR/stroke_UKLFR` — ma **non tutti supportano gli stessi `object`**: `lesion` (maschere di lesione) è disponibile su tutti e 4, mentre `feature` (matrici di connettività funzionale) esiste **solo su `UNIPD/WashU`** (gli altri 3 non hanno affatto un albero `features/` alla sorgente). Se il tuo `retrieve` chiede solo `feature`, `datasets` deve limitarsi a `["UNIPD/WashU"]` — includere un dataset che non supporta *nessuno* degli item richiesti è un errore bloccante (probabile refuso), non un semplice avviso.
- `group_filter`: Filtra il gruppo dei soggetti.
  - Usa `["ST"]` se vuoi estrarre solo i pazienti affetti da Stroke.
  - Usa `["HC"]` se vuoi estrarre solo i controlli sani (Healthy Controls).
  - Usa `null` per estrarre tutti i gruppi in modo indiscriminato.
- `subjects`: Usalo se vuoi estrarre solo una lista specifica di codici identificativi (es. `["sub-STUNIPD0001", "sub-STUNIPD0002"]`). Se invece vuoi che la pipeline trovi tutti i soggetti in automatico in base al filtro `group_filter`, imposta questo valore a `null`.

#### La sezione `retrieve`
Questo è il cuore della configurazione. È una lista di blocchi tra parentesi graffe `{}`, in cui decidi quali tipologie esatte di dati vuoi scaricare per i pazienti selezionati.

1. **Per copiare le maschere manuali delle lesioni**:
   ```json
   { "object": "lesion", "pipeline": "manual_masks", "datatype": "anat", "suffix": "lesion_mask" }
   ```
   Questa combinazione di parametri dice al sistema di andare a cercare il volume anatomico della lesione che è già stato segmentato manualmente e normalizzato.

2. **Per copiare le matrici di connettività funzionale (FC-pearson)**:
   ```json
   { "object": "feature", "datatype": "func", "suffix": "FC-pearson" }
   ```
   Questo blocco indica al sistema di recuperare **tutte** le matrici di connettività già calcolate per il soggetto, per ogni atlante di parcellazione registrato (oggi 12: `Yan{100,200,300,400}TianS{1,2,3}Buckner7N` — un sottoinsieme scelto delle varianti disponibili alla sorgente). Un soggetto con un file mancante per un solo atlante non blocca nulla: quell'atlante viene semplicemente segnalato come "non trovato" per quel soggetto nel report, gli altri 11 vengono comunque copiati. Si noti che per `feature` non si inserisce il valore `pipeline` per ragioni di standardizzazione.

3. **Per copiare i dati di controllo qualità del preprocessing funzionale (motion/outliers)**:
   ```json
   { "object": "feature", "datatype": "func", "suffix": "motion" },
   { "object": "feature", "datatype": "func", "suffix": "outliers" }
   ```
   Ogni voce recupera sia il file dati (`.tsv`) sia il relativo sidecar di metadati (`.json`) — utili per filtrare i soggetti con troppo movimento prima di usare le matrici FC in un'analisi.

- `include_tabular_data`: (`true` o `false`) Se messo a `true`, la pipeline scaricherà anche il file di riepilogo clinico `participants.tsv` del dataset, se disponibile alla sorgente.
- `overwrite`: (`true` o `false`). Un parametro di sicurezza importante.
  - Se `false`, la pipeline si accorge se ha già scaricato quel file nei run precedenti e lo salta risparmiando moltissimo tempo.
  - Se `true`, la pipeline cancella i file pregressi e li ricopia da zero. Utile solo se sai che il file originario sul server centrale è stato corretto o aggiornato.

### Controllare i risultati

A fine operazione, troverai i tuoi dati scaricati esplorando la cartella `data/`.
Ancora più importante, guarda il report generato in **`summaries/data_retrieval/clinical_connectome/copy_summary__<data>.md`**.
Invece di farti spulciare migliaia di file, il report ti darà una chiara lista umana di cosa è andato storto: "Paziente X, lesione non trovata; Paziente Y, cartella saltata", permettendoti di correggere immediatamente i problemi alla radice o di tenere conto di dati mancanti.
