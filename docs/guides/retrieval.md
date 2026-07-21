# Guida al Retrieval dei Dati

Questa guida spiega in parole semplici e chiare come usare la pipeline di retrieval. L'obiettivo di questo script è "copiare in modo intelligente" le immagini cerebrali dal server centrale (EBRAIN) al tuo computer locale (nella cartella `data/`), preparandole per l'analisi.

Il comando per lanciare la pipeline dal terminale, dopo aver attivato l'ambiente `nemesis`, è:
```bash
python -m src.pipeline.retrieve_data --config config/pipelines/retrieval.json
```

Tutte le regole su cosa scaricare, quali pazienti scegliere, e dove salvare i file si definiscono nel file JSON di configurazione indicato nel comando.

---

## Retrieve Data (`src/pipeline/retrieve_data.py`)

**Cosa fa**: La pipeline si collega alla tua sorgente dati, legge quali pazienti o gruppi le hai chiesto di cercare, ispeziona le loro cartelle, verifica che i file richiesti (come le maschere di lesione) siano effettivamente presenti e, infine, li copia sul tuo computer preservando l'esatta struttura BIDS delle cartelle. È progettato per essere "sicuro": se mancano dei file o ci sono problemi, non si blocca ma annota tutto in un report dettagliato per farti sapere chi manca all'appello.
**File di Configurazione**: `config/pipelines/retrieval.json`
**Input**: I file sorgente sul mount EBRAIN (es. `/data/corbetta/Clinical_connectome`).
**Output**: Le copie locali dei file in `data/`, e un utilissimo report di sintesi in `reports/data_retrieval/`.

### Spiegazione dei Parametri (`retrieval.json`)

Ecco tutti i valori possibili e cosa significano, riga per riga:

- `output_root`: Dove vuoi posizionare le copie. Solitamente si lascia `"data/"`.
- `project`: Il nome del progetto, usato per creare la sottocartella principale. Mettendo `"clinical_connectome"`, i file andranno in `data/clinical_connectome/`.
- `file_patterns`: Il percorso del "registro" delle regole di nomenclatura (`"config/registry/file_patterns.json"`). Non serve modificarlo, serve al codice per tradurre i concetti logici (es. "FC-pearson") nei percorsi file esatti richiesti dal sistema.
- `datasets`: Un elenco delle raccolte di pazienti da includere. I valori attualmente supportati sono: `["UNIPD/WashU", "UNIPD/PASPORT", "UNIPD/PSP", "UKLFR/stroke_UKLFR"]`.
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

2. **Per copiare le matrici di connettività funzionale**:
   ```json
   { "object": "feature", "datatype": "func", "suffix": "FC-pearson" }
   ```
   Questo blocco indica al sistema di recuperare le matrici calcolate (`FC-pearson`). Si noti che per `feature` non si inserisce il valore `pipeline` per ragioni di standardizzazione.

- `include_tabular_data`: (`true` o `false`) Se messo a `true`, la pipeline scaricherà anche il file di riepilogo clinico `participants.tsv` del dataset, se disponibile alla sorgente.
- `overwrite`: (`true` o `false`). Un parametro di sicurezza importante.
  - Se `false`, la pipeline si accorge se ha già scaricato quel file nei run precedenti e lo salta risparmiando moltissimo tempo.
  - Se `true`, la pipeline cancella i file pregressi e li ricopia da zero. Utile solo se sai che il file originario sul server centrale è stato corretto o aggiornato.

### Controllare i risultati

A fine operazione, troverai i tuoi dati scaricati esplorando la cartella `data/`.
Ancora più importante, guarda il report generato in **`reports/data_retrieval/clinical_connectome/copy_summary__<data>.md`**.
Invece di farti spulciare migliaia di file, il report ti darà una chiara lista umana di cosa è andato storto: "Paziente X, lesione non trovata; Paziente Y, cartella saltata", permettendoti di correggere immediatamente i problemi alla radice o di tenere conto di dati mancanti.
