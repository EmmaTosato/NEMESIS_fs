# Guida al Masking FC e Costruzione della Matrice di Connettività

Questa guida illustra l'uso di due pipeline accoppiate per processare le Matrici di Connettività Funzionale (FC) — disponibili per la coorte WashU — sovrapponendovi le maschere di lesione (pazienti) e preparando una matrice aggregata unica per gruppo di soggetti.

- **Scripts**: `src/pipeline/mask_fc.py` e `src/pipeline/build_fc_matrix.py`
- **Configurazioni**: `config/pipelines/mask_fc.json` e `config/pipelines/build_fc_matrix.json`

---

## Perché Due Pipeline Separate?

Per ragioni di flessibilità e ispezione clinica, il processo è diviso:

1. **`mask_fc.py` (Mascheramento)**: Sovrappone fisicamente la lesione del paziente alla sua rete connettiva (FC) grezza. Macchia come `NaN` (non disponibile/compromessa) tutte le zone danneggiate dalla lesione.
2. **`build_fc_matrix.py` (Vettorizzazione)**: Prende le reti di un gruppo di soggetti, scarta la parte ridondante della matrice e le impila in una matrice numerica univoca pronta per l'analisi. Per i pazienti (`ST`) legge le reti macchiate dalla Fase 1; per i controlli sani (`HC`) legge le reti grezze, perché non hanno lesione e quindi niente da mascherare.

*Questa divisione ti permette di analizzare quanti e quali nodi sono stati distrutti dal trauma per ogni paziente (guardando il `mask_summary.csv` della prima pipeline) **prima** di avviare il raggruppamento vero e proprio.*

---

## Esecuzione in Produzione

### Fase 1. Masking (sul server, via SLURM)
```bash
sbatch jobs/run_mask_fc.sh
```
**Output Fase 1:** Scrive un file `masked_fc.csv` per paziente in `data/derived/features/masked_fc/...` e un riassunto dei nodi distrutti `mask_summary.csv`.

### Fase 2. Costruzione Matrice (sul server, via SLURM)
Per i pazienti, dopo aver controllato i dati del punto 1 (i controlli sani non passano dalla Fase 1):
```bash
sbatch jobs/run_build_fc_matrix.sh
```
**Output Fase 2:** Unifica tutti i file del gruppo scelto in un'unica `matrix.npy` (con relativi `metadata.csv` e `manifest.json`) situata in `data/derived/features/fc_matrix/...` - identico allo standard del "Lesion Matrix Building".

In locale, dalla radice del repo con l'ambiente `nemesis` attivo, in sequenza:
```bash
python -m src.pipeline.mask_fc --config config/pipelines/mask_fc.json
python -m src.pipeline.build_fc_matrix --config config/pipelines/build_fc_matrix.json
```

---

## Dettaglio Parametri Importanti

### Scegliere i soggetti: `group_filter` e `group`
Dataset come `UNIPD/WashU` contengono sia pazienti con ictus (`ST`) sia controlli sani (`HC`). I controlli sani hanno una connessione funzionale ma nessuna lesione. I gruppi non si mescolano mai nella stessa matrice: ogni matrice è di un solo gruppo.

- **`mask_fc.json`**, campo `group_filter` (lista): seleziona i soggetti da mascherare. Serve a soggetti con FC **e** maschera di lesione, quindi si usa `["ST"]`. Con `["HC"]` la pipeline si ferma (`no subject … has both a lesion mask and an FC file`); con `["ST","HC"]` i sani sono saltati con un avviso.
- **`build_fc_matrix.json`**, campo `group` (`"ST"` o `"HC"`): sceglie i soggetti della matrice e, con loro, l'input.

| `group` | Campi richiesti | Input |
|---|---|---|
| `"ST"` | `masked_fc_root` | le reti già mascherate da `mask_fc.py` |
| `"HC"` | `data_root`, `dataset`, `fc_glob_template` | le reti grezze del dataset (stessi campi di `mask_fc.json`) |

I campi dell'altro gruppo sono rifiutati. Per costruire pazienti e sani servono due run con `session_name` diversi (per esempio `s3.1` e `s3.1-hc`). La matrice dei sani non ha `NaN` da archi compromessi.

---

## Cosa C'è e Cosa Manca nell'Output (Per Design)

- **I Valori NaN restano NaN**: Al termine di questa pipeline, le connessioni distrutte dei pazienti rimangono vuote (`NaN`). **Nessuna pipeline imputa i `NaN`**: la scelta dell'imputazione è aperta (vedi `README.md`). `dim_reduction` non ha un controllo sui `NaN`: cosa fa con una matrice FC che ne contiene non è verificato.
- **Pulizia Connessioni**: Connessioni che restano magicamente costanti identiche per tutti i pazienti (rarissimo, ma possibile) vengono automaticamente rimosse e loggate per ottimizzare i dati per il Machine Learning.
- **Soglie di Esclusione Paziente**: Nonostante in `mask_summary.csv` si sappia quanti nodi il paziente ha distrutto, **è una decisione progettuale non implementare una soglia**. Nessun paziente viene "escluso" per troppi danni in questa fase. Per ispezionare comunque la distribuzione dei nodi compromessi (percentili, soglie candidate, nodi vs connessioni perse) si usa `notebooks/exploration/fc_analysis.ipynb`; come si legge è in [`knowledge/notes/neuroimaging/fc_lesion_masking.md`](../../knowledge/notes/neuroimaging/fc_lesion_masking.md), sezione "Scegliere una soglia di esclusione paziente".
- **Copia locale ridotta**: `data/derived/features/masked_fc/` tiene in locale solo 10 soggetti campione (comuni a tutte e 12 le combinazioni di atlante) — il resto è compresso in `masked_fc_archive.tar.gz`, verificato prima della cancellazione (vedi `README_ARCHIVE.md` nella stessa cartella). Non è un dato EBRAIN: per riaverlo per intero, decomprimi l'archivio o rilancia `mask_fc.py` da capo. Dettagli in `docs/guides/datasets.md`.
