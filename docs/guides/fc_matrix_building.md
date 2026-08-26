# Guida al Masking FC e Costruzione della Matrice di Connettività

Questa guida illustra l'uso di due pipeline accoppiate per processare le Matrici di Connettività Funzionale (FC) — disponibili attualmente per la coorte WashU — sovrapponendovi le maschere di lesione e preparando una matrice aggregata unica.

- **Scripts**: `src/pipeline/mask_fc.py` e `src/pipeline/build_fc_matrix.py`
- **Configurazioni**: `config/pipelines/mask_fc.json` e `config/pipelines/build_fc_matrix.json`

---

## Perché Due Pipeline Separate?

Per ragioni di flessibilità e ispezione clinica, il processo è diviso:

1. **`mask_fc.py` (Mascheramento)**: Sovrappone fisicamente la lesione del paziente alla sua rete connettiva (FC) grezza. Macchia come `NaN` (non disponibile/compromessa) tutte le zone danneggiate dalla lesione.
2. **`build_fc_matrix.py` (Vettorizzazione)**: Prende tutte queste reti macchiate dai pazienti, scarta la parte ridondante della matrice e le impila in una matrice numerica univoca pronta per l'analisi.

*Questa divisione ti permette di analizzare quanti e quali nodi sono stati distrutti dal trauma per ogni paziente (guardando il `mask_summary.csv` della prima pipeline) **prima** di avviare il raggruppamento vero e proprio.*

---

## Esecuzione in Produzione

### Fase 1. Masking (sul server, via SLURM)
```bash
sbatch jobs/run_mask_fc.sh
```
**Output Fase 1:** Scrive un file `masked_fc.csv` per paziente in `data/derived/features/masked_fc/...` e un riassunto dei nodi distrutti `mask_summary.csv`.

### Fase 2. Costruzione Matrice (sul server, via SLURM)
Dopo aver controllato i dati del punto 1:
```bash
sbatch jobs/run_build_fc_matrix.sh
```
**Output Fase 2:** Unifica tutti i file in un'unica `matrix.npy` (con relativi `metadata.csv` e `manifest.json`) situata in `data/derived/features/fc_matrix/...` - identico allo standard del "Lesion Matrix Building".

*(In locale, possono essere lanciate in sequenza tramite `python -m src.pipeline...`)*.

---

## Dettaglio Parametri Importanti

### Il Filtro `group_filter`
Dataset come `UNIPD/WashU` contengono sia pazienti affetti da ictus (`ST`) sia controlli sani (`HC`).
I controlli sani hanno una connessione funzionale, ma nessuna lesione.

In `mask_fc.json` e `build_fc_matrix.json` puoi specificare:
- `"group_filter": ["ST"]`: Produce matrici FC mascherate SOLO per i pazienti traumatizzati (Standard). I sani vengono saltati di proposito.
- `"group_filter": ["ST", "HC"]`: Esegue su tutti (Utile per task comparativi). I sani verranno aggiunti con 0 nodi compromessi.

---

## Cosa C'è e Cosa Manca nell'Output (Per Design)

- **I Valori NaN restano NaN**: Al termine di questa pipeline, le connessioni distrutte rimangono vuote (`NaN`). **Non vi è ancora imputazione**. L'imputazione intelligente dei dati mancanti avverrà in un passaggio separato appena prima della *Dim Reduction*.
- **Pulizia Connessioni**: Connessioni che restano magicamente costanti identiche per tutti i pazienti (rarissimo, ma possibile) vengono automaticamente rimosse e loggate per ottimizzare i dati per il Machine Learning.
- **Soglie di Esclusione Paziente**: Nonostante in `mask_summary.csv` si sappia quanti nodi il paziente ha distrutto, **è una decisione progettuale non implementare una soglia**. Nessun paziente viene "escluso" per troppi danni in questa fase.
- **Copia locale ridotta (dal 26/08/26)**: `data/derived/features/masked_fc/` tiene in locale solo 10 soggetti campione (comuni a tutte e 12 le combinazioni di atlante) — il resto è compresso in `masked_fc_archive.tar.gz`, verificato prima della cancellazione (vedi `README_ARCHIVE.md` nella stessa cartella). Non è un dato EBRAIN: per riaverlo per intero, decomprimi l'archivio o rilancia `mask_fc.py` da capo. Dettagli in `docs/guides/datasets.md`.
