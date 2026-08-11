# Guida al Retrieval dei Dati

Questa guida illustra il funzionamento della pipeline di Retrieval. L'obiettivo è analizzare e copiare in modo intelligente i dati grezzi dal server master EBRAIN all'ambiente di lavoro locale, verificandone l'integrità e preservando lo standard architetturale (BIDS).

- **Script**: `src/pipeline/retrieve_data.py`
- **Configurazioni**: `config/pipelines/retrieval_server.json` e `config/pipelines/retrieval_local.json` (Sono lo stesso file logico, ma con path puntati per i rispettivi ambiti di calcolo).

---

## 🚀 Esecuzione

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

---

## 🧠 Flusso e Funzionamento dello Script

Lo script consulta le regole passate nel JSON e scansiona il mount indicato in cerca delle informazioni (Es. Maschere di lesione o Matrici FC).
Non si "interrompe in errore" se a un paziente mancano dei file; bensì estrae tutto il possibile e genera un solido e utilissimo report log per l'umano indicante chi manca all'appello. 

Tutti i dati estratti sono considerati "Derivati" in quanto soggetti ad elaborazione e non raw scans.

---

## ⚙️ Dettaglio Parametri JSON

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

---

## 📂 Output e Report

- I dati prelevati finiscono riorganizzati sotto la struttura standard `data/<project_name>/derivatives/...` nel tuo locale.
- **Fondamentale**: Terminato il job, analizza `summaries/data_retrieval/<project_name>/copy_summary__<data>.md`. Questo file in chiaro descriverà quante cartelle sono state scansionate, chi è incompleto, chi manca di file lesione e il perché. Essenziale per il troubleshooting senza sfogliare a mano 300 pazienti.
