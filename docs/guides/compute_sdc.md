# Guida a compute_sdc — Structural Disconnectome via BCBToolKit

Questa pipeline calcola la **SDC (Structural Disconnectome)** per ogni soggetto in `clinical_connectome`, lanciando BCBToolKit/BCBlib (Stage 1 + Stage 2, vedi `/data/etosato/tools/USAGE.md`) su ogni lesion mask retrievabile. Non è un tool a sé: orchestrata da questa repo per girare su tutti i soggetti in batch, con parallelismo e con un controllo esplicito tra Stage 1 e Stage 2.

**Moduli**: `src/sdc/` (config, manifest, staging, runner, status) + `src/pipeline/compute_sdc.py` (CLI)
**Configurazione**: `config/pipelines/compute_sdc.json`

## Perché tre modalità (`manifest` / `run` / `aggregate`) invece di un unico comando

`bcb-lf-preprocess`/`bcb-lesion-features` non hanno un flag per processare un singolo soggetto — operano su un'intera cartella. Per parallelizzare per soggetto, ogni invocazione di `compute_sdc.py --mode run` costruisce quindi una cartella di staging che contiene **solo i soggetti assegnati a quel task**, e ci lancia sopra i due tool. Questo richiede tre fasi separate, eseguite in sequenza (anche a distanza di giorni, per via della coda SLURM):

1. **`--mode manifest`** — scopre tutti i soggetti una sola volta (stessa logica di `retrieve_data.py`, via `Dataset`/`file_patterns`), scrive `manifest.csv` (ordine fisso). I soggetti esclusi (lesion mask assente, ambigua, o `subject_id` duplicato tra dataset diversi) vanno in `manifest_excluded.json` con il motivo — mai scartati in silenzio.
2. **`--mode run --task-id I --task-count N`** — l'unità di parallelismo. Prende `manifest.csv`, seleziona i soggetti `I::N` (stride slice — copertura completa e disgiunta per qualunque N), costruisce lo staging BIDS via symlink, lancia Stage 1, **verifica** l'output (shape NIfTI attesa 182×218×182, non solo "il file esiste"), e solo per i soggetti che passano lancia Stage 2. Ogni soggetto ottiene uno stato scritto in `_status/<subject_id>.json` (`ok`, `failed_stage1_process`, `failed_stage1_check`, `failed_stage2_process`, `dry_run`).
3. **`--mode aggregate`** — unico passo finale: legge tutti gli `_status/*.json`, fa il merge (symlink) degli output dei soggetti `ok` in `<output_dir>/{prep,features}/`, scrive `config.md`/`manifest.json` e una riga in `data/derived/sdc/runs.csv`.

Un fallimento per singolo soggetto (Stage 1 non converge, check fallito, Stage 2 crash su quel soggetto) **non ferma gli altri** — è tracciato nello status e basta. Un fallimento strutturale (config sbagliata, `bcbtoolkit_path` inesistente, il processo Stage 1/2 crasha per l'intero task) fa fallire il task con exit code ≠ 0.

## Output

```
data/derived/sdc/<session_name>/
├── manifest.csv                 # subject_id, dataset, lesion_mask_path
├── manifest_excluded.json       # subject_id -> perché escluso
├── _status/<subject_id>.json    # esito per soggetto
├── _work/task_<I>/{staging,prep,validated_prep,features}/  # scratch per task, non pulito automaticamente
├── prep/<subject_id>/           # simlink all'output Stage 1 verificato
├── features/<subject_id>/       # simlink all'output Stage 2
├── manifest.json                # conteggi per stato
└── config.md
data/derived/sdc/runs.csv            # storico run (append-only, CSV: run_id, timestamp, run_type, params, output, notes)
```

`SESSIONS.md` (cosa significa un `session_name`, es. `s1.1`: dataset, modalità, cosa è cambiato) non è qui — è scritto a mano, canonico in `data/SESSIONS.md`, condiviso da tutte le pipeline (non solo SDC), con una copia/symlink in `results/SESSIONS.md`.

Nota: a differenza di `build_lesion_matrix.py`, la cartella di output **non** è datata (`<dd-mm>_<session_name>`) ma è solo `<session_name>` — le tre fasi possono girare a distanza di giorni (coda SLURM) e devono risolvere sempre alla stessa cartella partendo solo dal config.

`_work/` non viene ripulito automaticamente dopo l'aggregate (sono simlink verso `_work/`, cancellarlo romperebbe `prep/`/`features/`) — se serve liberare spazio dopo aver verificato l'output finale, valutare caso per caso, non è automatizzato.

## Esecuzione — SLURM (produzione)

Tre job in sequenza, il secondo è un array:

```bash
# 1. manifest — controlla quanti soggetti sono stati scoperti
sbatch jobs/run_compute_sdc_manifest.sh
wc -l data/derived/sdc/s1/manifest.csv   # N soggetti + 1 header

# 2. array — editare #SBATCH --array=0-<N-1> in jobs/run_compute_sdc.sh
#    (un task per soggetto: --cpus-per-task deve combaciare con
#    cores_per_subject nel config)
sbatch jobs/run_compute_sdc.sh

# 3. aggregate — solo dopo che TUTTI i task dell'array sono completati
#    (controllare con: sacct -j <array_job_id>)
sbatch jobs/run_compute_sdc_aggregate.sh
```

## Esecuzione — locale, senza SLURM

Per test rapidi su pochi soggetti o su una macchina senza scheduler:

```bash
conda activate nemesis
scripts/run_compute_sdc_no_slurm.sh config/pipelines/compute_sdc.json
```

Fa manifest → run (pool locale, `xargs -P`, dimensionato come `nproc / cores_per_subject`, mai sovrasottoscritto) → aggregate, tutto in un unico comando. `--dry-run` per un giro a vuoto, `--background` per lanciarlo con `nohup` e liberare il terminale. Vive in `scripts/`, non in `jobs/`, perché non passa da `sbatch` — la regola "sempre via sbatch" di `.claude/CLAUDE.md` riguarda l'esecuzione in produzione sul cluster, non i test locali.

## `--dry-run`

Applicabile solo a `--mode run`. Passa `--dry-run` a `bcb-lf-preprocess` (che stampa il piano senza eseguire — flag nativo del tool) e **non invoca affatto** `bcb-lesion-features` (che non ha un `--dry-run` proprio), limitandosi a loggare il comando che verrebbe lanciato. Utile per validare velocemente che discovery, staging e wiring dei path siano corretti prima di un run reale su centinaia di soggetti — vedi sotto per un esempio eseguito sui dati reali.

## Parametri di `compute_sdc.json`

| Campo | Descrizione |
|---|---|
| `project` | Nome progetto (`"clinical_connectome"`) |
| `file_patterns` | Path al registry `file_patterns_{local,server}.json` (stesso usato da `retrieval.json`) |
| `datasets` | Coorti da includere |
| `group_filter` | Lista gruppi (`["ST"]`) o `null` |
| `bcbtoolkit_path` | Path a BCBToolKit (deve contenere `run_disco.sh`, validato al load) |
| `tracks_dir` | Atlante trattografie custom, o `null` per usare quello bundled in BCBToolKit |
| `cores_per_subject` | Core per soggetto (`--ncores` di `bcb-lf-preprocess`) — deve combaciare con `--cpus-per-task` dell'array SLURM o essere usato per calcolare il pool locale |
| `stage2_ebrains` | `true` per usare tutti e 14 gli atlanti EBRAINS di default in Stage 2 |
| `stage2_presets` | Lista di preset atlas aggiuntivi (`--preset`, ripetibile) |
| `output_root` | `"data/derived/sdc"` |
| `session_name` | Etichetta del run — determina la cartella di output (non datata, vedi sopra) |
| `overwrite` | Se `false`, `--mode manifest` rifiuta di sovrascrivere un `manifest.csv` esistente |
| `run_notes` | Note libere |

## Verifica eseguita (dry-run)

Vedi sezione "Dry-run di verifica" più sotto/nello stato progetto per l'esito dell'esecuzione contro i dati reali.
