# Guida al masking FC e alla costruzione della matrice di connettività

Questa guida spiega come usare le due pipeline che trasformano le matrici di connettività funzionale (FC) già calcolate per la coorte WashU in una matrice numerica pronta per la riduzione dimensionale — mascherando prima le zone compromesse dalla lesione di ciascun paziente.

**Script**: `src/pipeline/mask_fc.py` + `src/pipeline/build_fc_matrix.py` (due pipeline separate, anche a livello di config)
**Configurazione**: `config/pipelines/mask_fc.json` + `config/pipelines/build_fc_matrix.json`

## Perché due pipeline separate

1. **`mask_fc.py`** — legge le lesion mask e le matrici FC grezze, marca come mancanti (NaN) le zone compromesse dalla lesione, scrive una matrice mascherata per soggetto.
2. **`build_fc_matrix.py`** — legge *solo* l'output già mascherato del passo 1 (non tocca più lesioni o atlanti), la vettorizza e la impila in un'unica matrice.

Sono separate apposta: dopo aver mascherato tutta la coorte, si può analizzare quanti nodi risultano compromessi per soggetto (file `mask_summary.csv`, uno per combinazione di atlante) **prima** di costruire la matrice finale — utile per ispezionare a occhio quanto è compromesso un singolo paziente, anche se oggi nessuna soglia di esclusione viene applicata (vedi sotto, decisione già chiusa).

## Esecuzione

**1. Masking (sul server, via SLURM)**
```bash
sbatch jobs/run_mask_fc.sh
```
Scrive, per ciascuna combinazione di atlante elencata in `atlas_combos` (config), un file `<subject>_masked_fc.csv` per ogni paziente in `data/derived/features/masked_fc/<combo>/`, più un `mask_summary.csv` con il numero di nodi compromessi per paziente.

**2. Costruzione della matrice (dopo aver analizzato i risultati del punto 1)**
```bash
sbatch jobs/run_build_fc_matrix.sh
```
Legge `data/derived/features/masked_fc/<combo>/`, vettorizza (solo il triangolo superiore, senza diagonale) e impila tutti i pazienti, scrivendo il risultato in `data/derived/features/fc_matrix/<combo>/<data>_<session_name>/` nello stesso formato già usato da `build_lesion_matrix.py` (`matrix.npy`, `metadata.csv`, `manifest.json`, più `edge_names.npy` con i nomi delle connessioni).

In locale (senza SLURM), stesso comando ma diretto:
```bash
conda activate nemesis
python -m src.pipeline.mask_fc --config config/pipelines/mask_fc.json
python -m src.pipeline.build_fc_matrix --config config/pipelines/build_fc_matrix.json
```

## Filtro per gruppo (`group_filter`)

Alcuni dataset (es. `UNIPD/WashU`) hanno, sotto la stessa cartella `features/`, sia pazienti (`ST`) sia controlli sani (`HC`) - un healthy control ha una FC calcolata ma nessuna lesione da mascherare. `mask_fc.json` ha un campo opzionale `group_filter`, stessa sintassi già usata da `retrieval_local.json`/`retrieval_server.json`:

```json
"group_filter": ["ST"]
```

restringe la discovery ai soli soggetti il cui gruppo (dedotto dal nome, es. `sub-STUNIPDHC0004` → `HC`, `sub-STUNIPD0237` → `ST`) è nell'elenco. Un HC escluso così compare nel log come `excluded_by_group`, mai come `missing_lesion` (quella dicitura resta riservata a un paziente a cui manca davvero la maschera). Omettere il campo (o metterlo a `null`) equivale a nessun filtro - da usare solo se il dataset non mescola gruppi.

Per includere anche i controlli sani (es. per l'analisi di confronto del Task 3):
```json
"group_filter": ["ST", "HC"]
```

`build_lesion_matrix.json` ha lo stesso campo, con la stessa semantica (vedi `docs/guides/matrix_building.md`).

## Cosa contiene l'output

- **Ancora nessuna imputazione**: la matrice finale contiene ancora dei NaN per le connessioni compromesse dalla lesione — non vengono sostituiti con zero o altro in questa fase. La sostituzione è un passo separato, deliberatamente non ancora implementato, che avverrà solo subito prima della riduzione dimensionale (`dim_reduction.py`).
- **Connessioni costanti rimosse**: se una connessione ha lo stesso identico valore per tutti i pazienti (senza nessun NaN), viene tolta e loggata — per dati FC continui questo non dovrebbe quasi mai succedere; se capita, è probabilmente un sintomo di un problema a monte, non un caso da ignorare.

## Cosa manca ancora (deciso di proposito, non un bug)

1. **Soglia di esclusione paziente**: **decisione chiusa, non un lavoro da riprendere** — nessun paziente viene escluso per "troppi nodi compromessi", e non è previsto implementare una soglia. `mask_summary.csv` resta comunque disponibile per un'ispezione manuale caso per caso, se mai servisse in futuro.
2. **Imputazione dei NaN**: non implementata in queste pipeline, per design — vedi `docs/dev/analysis.md` per la motivazione (letteratura Griffis et al. 2019 / Siegel et al. 2016).

Vedi anche `notebooks/fc_lesion_masking.ipynb` per una spiegazione passo-passo, in linguaggio semplice, dell'intero procedimento (compresi i due bug di `nilearn` trovati e corretti durante la validazione).
