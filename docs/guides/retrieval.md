# Guida al Retrieval dei Dati

Questa guida illustra il funzionamento della pipeline di Retrieval. L'obiettivo è analizzare e copiare in modo intelligente i dati grezzi dal server master EBRAIN all'ambiente di lavoro locale, verificandone l'integrità e preservando lo standard architetturale (BIDS).

- **Script**: `src/pipeline/retrieve_data.py`
- **Configurazioni**: `config/pipelines/retrieval_server.json` e `config/pipelines/retrieval_local.json` (Sono lo stesso file logico, ma con path puntati per i rispettivi ambiti di calcolo).

---

## Esecuzione

### 1. Sul Server (tramite SLURM)
Questa è l'esecuzione di Produzione, lavora direttamente sulla master source.
```bash
sbatch jobs/run_retrieve_data.sh
```

### 2. In Locale
Dal PC locale, per recuperare file da un mount di rete (es. copia locale).
```bash
python -m src.pipeline.retrieve_data --config config/pipelines/retrieval_local.json
```

Per l'SDC (vedi sotto), stessa CLI ma con la config dedicata (scarica tutto, 5 dataset × 6 categorie, ~3 GB):
```bash
python -m src.pipeline.retrieve_data --config config/pipelines/retrieval_sdc.json
```
Su SLURM: `sbatch jobs/run_retrieve_sdc.sh`.

**In alternativa**, per scaricare solo un sottoinsieme (dataset e/o categorie di file — vedi la tabella pesi/categorie in `docs/guides/datasets.md`), c'è uno script standalone dedicato, `scripts/download_sdc.py` — niente file di config in `config/`, tutte le opzioni sono flag CLI (riusa comunque la stessa registry `file_patterns_server.json` e lo stesso motore di `retrieve_data.py`, non duplica nulla):
```bash
PYTHONPATH=. python scripts/download_sdc.py \
    --datasets UNIPD/WashU UKLFR/stroke_UKLFR \
    --categories disconnectome-LF lesion-LF \
    --output-root data/
# --overwrite per riscaricare file già presenti; --help per l'elenco completo
```
Su SLURM: `sbatch jobs/run_download_sdc.sh` (modifica le variabili `DATASETS`/`CATEGORIES`/`OVERWRITE` in cima allo script prima di sottomettere).

### 3. Scaricare sul proprio Mac (dal server, via rsync)
`download_sdc.py`/`retrieve_data.py` girano *sul server* (dove il mount EBRAIN è visibile) — non copiano nulla sul tuo Mac. Per portare in locale solo un sottoinsieme, senza tirarti dietro tutto `data/`:

1. **Sul server**, scarica in una cartella temporanea e piatta, isolata dal resto (già gitignored via `data/*`, nessuna modifica necessaria):
   ```bash
   PYTHONPATH=. python scripts/download_sdc.py \
       --datasets UNIPD/WashU UKLFR/stroke_UKLFR \
       --categories disconnectome-LF lesion-LF \
       --output-root data/_sdc_staging
   ```
2. **Dal Mac**, `rsync` tira giù solo quella cartella (la struttura interna è già quella che userebbe `retrieval_local.json`, quindi puoi farla atterrare direttamente sotto `data/clinical_connectome/derivatives/`):
   ```bash
   rsync -avz etosato@<host-server>:/home/etosato/Projects/NEMESIS_fs/data/_sdc_staging/ \
       "/Users/emmatosato/Local Projects/Local PhD Projects/NEMESIS_fs/data/_sdc_staging/"
   ```
3. **Sul server**, ripulisci la cartella temporanea:
   ```bash
   rm -rf data/_sdc_staging
   ```

---

## Flusso e Funzionamento dello Script

Lo script consulta le regole passate nel JSON e scansiona il mount indicato in cerca delle informazioni (Es. Maschere di lesione o Matrici FC).
Non si "interrompe in errore" se a un paziente mancano dei file; bensì estrae tutto il possibile e genera un solido e utilissimo report log per l'umano indicante chi manca all'appello. 

Tutti i dati estratti sono considerati "Derivati" in quanto soggetti ad elaborazione e non raw scans.

---

## Dettaglio Parametri JSON

I parametri decidono esattamente cosa e per chi estrarre.

| Parametro | Descrizione |
| :--- | :--- |
| **`output_root`** | La directory radice locale. Solitamente `"data/"`. |
| **`project`** | Nome progetto. Salva in `data/<project>/derivatives/<dataset>/...`. |
| **`file_patterns`** | Regole di scansione logica file (Non alterare - `"file_patterns_server.json"`). |
| **`datasets`** | Le coorti su cui scansionare (Es. `["UNIPD/WashU", ...]`). |
| **`group_filter`** | Seleziona Pazienti Malati (`["ST"]`), Sani (`["HC"]`) o tutti (`null`). |
| **`subjects`** | (Opzionale). Permette di recuperare 1 solo paziente (passando il `["sub-id"]`). `null` li scansiona tutti. |
| **`include_tabular_data`** | Se `true` estrae anche il `participants.tsv` (età, sesso, punteggi clinici). |
| **`overwrite`** | Se `false` non riscarica file già localmente presenti, saltandoli istantaneamente (Ottimo e Veloce). `true` pialla e ricopia forzatamente la sorgente. |

### La Chiave Maestra: `retrieve`
È il blocco (lista di dizionari `{}`) dove indichi gli elementi specifici (objects) di cui hai bisogno:

- **Per le Lesioni Manuali**
  ```json
  { "object": "lesion", "pipeline": "manual_masks", "datatype": "anat", "suffix": "lesion_mask" }
  ```
- **Per le Matrici Funzionali FC** (NB: Ricorda che *solo WashU* possiede questi file). Scaricherà autonomamente tutti i sottotipi di atlanti registrati senza spezzarsi se uno specifico manca al soggetto.
  ```json
  { "object": "feature", "datatype": "func", "suffix": "FC-pearson" }
  ```
- **Per dati QA/Controllo Movimento Paziente (Motion)**
  ```json
  { "object": "feature", "datatype": "func", "suffix": "motion" }
  ```
- **Per l'SDC (Structural Disconnectome)** (NB: stesso output Stage1+Stage2 di BCBToolKit che produce la nostra `compute_sdc.py` — questo run specifico però non è passato dalla nostra CLI (`--mode manifest/run/aggregate`), quindi non ha `manifest.csv`/`_status/`/riga in `runs.csv` scritti da noi. Arriva in locale sotto `sdc/`). Config dedicata: `config/pipelines/retrieval_sdc.json` (5 dataset: `UNIPD/WashU`, `UNIPD/PASPORT`, `UNIPD/PSP`, `UKLFR/stroke_UKLFR`, `UKE/WAKEUP_acute`).
  ```json
  { "object": "sdc", "datatype": "dwi", "suffix": "disconnectome-map" }
  { "object": "sdc", "datatype": "dwi", "suffix": "disconnectome-mapstats" }
  { "object": "sdc", "datatype": "dwi", "suffix": "disconnectome-LF" }
  { "object": "sdc", "datatype": "dwi", "suffix": "lesion-map" }
  { "object": "sdc", "datatype": "dwi", "suffix": "lesion-mapstats" }
  { "object": "sdc", "datatype": "dwi", "suffix": "lesion-LF" }
  ```

---

## Output e Report

- I dati prelevati finiscono riorganizzati sotto la struttura standard `data/<project_name>/derivatives/...` nel tuo locale.
- **Fondamentale**: Terminato il job, analizza `summaries/data_retrieval/<project_name>/copy_summary__<data>.md`. Questo file in chiaro descriverà quante cartelle sono state scansionate, chi è incompleto, chi manca di file lesione e il perché. Essenziale per il troubleshooting senza sfogliare a mano 300 pazienti.
