# Guida al masking FC e alla costruzione della matrice di connettività

Questa guida spiega come usare le due pipeline che trasformano le matrici di connettività funzionale (FC) già calcolate per la coorte WashU in una matrice numerica pronta per la riduzione dimensionale — mascherando prima le zone compromesse dalla lesione di ciascun paziente.

**Script**: `src/pipeline/mask_fc.py` + `src/pipeline/build_fc_matrix.py` (due pipeline separate, anche a livello di config)
**Configurazione**: `config/pipelines/mask_fc.json` + `config/pipelines/build_fc_matrix.json`

## Perché due pipeline separate

1. **`mask_fc.py`** — legge le lesion mask e le matrici FC grezze, marca come mancanti (NaN) le zone compromesse dalla lesione, scrive una matrice mascherata per soggetto.
2. **`build_fc_matrix.py`** — legge *solo* l'output già mascherato del passo 1 (non tocca più lesioni o atlanti), la vettorizza e la impila in un'unica matrice.

Sono separate apposta: dopo aver mascherato tutta la coorte, si può analizzare quanti nodi risultano compromessi per soggetto (file `mask_summary.csv`, uno per combinazione di atlante) e decidere con calma una soglia di esclusione paziente, **prima** di costruire la matrice finale — senza dover rifare il masking ogni volta che si cambia idea sulla soglia.

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

## Cosa contiene l'output

- **Ancora nessuna imputazione**: la matrice finale contiene ancora dei NaN per le connessioni compromesse dalla lesione — non vengono sostituiti con zero o altro in questa fase. La sostituzione è un passo separato, deliberatamente non ancora implementato, che avverrà solo subito prima della riduzione dimensionale (`dim_reduction.py`).
- **Connessioni costanti rimosse**: se una connessione ha lo stesso identico valore per tutti i pazienti (senza nessun NaN), viene tolta e loggata — per dati FC continui questo non dovrebbe quasi mai succedere; se capita, è probabilmente un sintomo di un problema a monte, non un caso da ignorare.

## Cosa manca ancora (deciso di proposito, non un bug)

1. **Soglia di esclusione paziente**: nessun paziente viene ancora escluso per "troppi nodi compromessi" — va decisa guardando i `mask_summary.csv` reali su tutta la coorte.
2. **Imputazione dei NaN**: non implementata in queste pipeline, per design — vedi `docs/dev/analysis.md` per la motivazione (letteratura Griffis et al. 2019 / Siegel et al. 2016).

Vedi anche `notebooks/fc_lesion_masking.ipynb` per una spiegazione passo-passo, in linguaggio semplice, dell'intero procedimento (compresi i due bug di `nilearn` trovati e corretti durante la validazione).
