# Guida a compute_sdc (Structural Disconnectome via BCBToolKit)

Questa pipeline calcola la **SDC (Structural Disconnectome)** per ogni soggetto lanciando BCBToolKit/BCBlib (Stage 1 + Stage 2) su ogni maschera di lesione, processando i soggetti in batch in parallelo.

- **Moduli Base**: `src/sdc/` (config, manifest, staging, runner, status)
- **CLI / Script Principale**: `src/pipeline/compute_sdc.py`
- **Configurazione**: `config/pipelines/compute_sdc.json`

---

## 🔄 Flusso in 3 Fasi (`manifest`, `run`, `aggregate`)

Dato che i tool sottostanti lavorano su intere directory e non singoli file, lo script usa tre fasi eseguite in sequenza per gestire staging e parallelismo.

### 1. Fase `--mode manifest`
- Esplora i dataset e crea un **`manifest.csv`** con tutti i soggetti trovati.
- Soggetti invalidi/esclusi finiscono in `manifest_excluded.json` con motivo esplicito.

### 2. Fase `--mode run --task-id I --task-count N`
- È l'unità di parallelismo. Elabora una frazione dei soggetti.
- **Resampling**: Ricampiona ogni maschera non in `182×218×182` alla griglia MNI152NLin6Asym 1mm.
- **Stage 1 (Preprocess)**: Lancia e verifica l'output.
- **Stage 2 (Features)**: Se Stage 1 è ok, lancia l'estrazione ed effettua i controlli.
- Genera uno **status file** in `_status/<subject_id>.json` (esito e tempi).
- *Nota*: Errori sul singolo paziente non bloccano il batch; l'intero processo abortisce solo se nessun paziente viene completato con successo.

### 3. Fase `--mode aggregate`
- Raccoglie gli status json.
- Unisce/linka i risultati validi nella cartella di output del paziente.
- Scrive un report aggregato (`config.md`, `manifest.json`) e aggiorna `runs.csv`.

---

## 🚀 Esecuzione

### Tramite SLURM (Produzione)
Si tratta di tre job in sequenza (il secondo è un array):

```bash
# 1. Manifest
sbatch jobs/run_compute_sdc_manifest.sh

# 2. Array Job (verifica cores e limiti in run_compute_sdc.sh)
sbatch jobs/run_compute_sdc.sh

# 3. Aggregate (DA LANCIARE SOLO A COMPLETAMENTO DELL'ARRAY)
sbatch jobs/run_compute_sdc_aggregate.sh
```

### In Locale (Senza SLURM)
Per test rapidi o PC locali. Concatena le 3 fasi in un colpo solo.
```bash
conda activate nemesis
jobs/run_compute_sdc_no_slurm.sh config/pipelines/compute_sdc.json
```
*(Supporta flag come `--dry-run` o `--background`)*.

---

## ⚙️ Dettaglio Parametri JSON

| Campo | Tipo | Descrizione |
| :--- | :--- | :--- |
| **`project`** | *Stringa* | Nome progetto (`"clinical_connectome"`). |
| **`file_patterns`** | *Stringa* | Percorso al registry, es. `file_patterns_server.json`. |
| **`datasets`** | *Lista* | Coorti da includere. |
| **`group_filter`** | *Lista* | Es. `["ST"]` o `null`. |
| **`bcbtoolkit_path`** | *Stringa* | Percorso a BCBToolKit (deve contenere `run_disco.sh` e `MNI152.nii.gz`). |
| **`tracks_dir`** | *Stringa* | Atlante trattografie custom, o `null` per default BCBToolKit. |
| **`cores_per_subject`** | *Intero* | Core dedicati a paziente. DEVE combaciare con `cpus-per-task` SLURM. |
| **`stage2_ebrains`** | *Booleano* | `true` usa tutti e 15 gli atlanti EBRAINS predefiniti. |
| **`stage2_presets`** | *Lista* | Preset atlas aggiuntivi desiderati. |
| **`output_root`** | *Stringa* | Dove salvare (es. `"data/derived/sdc"`). |
| **`session_name`** | *Stringa* | Etichetta dell'elaborazione (es. `"s1.1"`). Nessuna data automatica. |
| **`overwrite`** | *Booleano* | Se `false`, la fase `manifest` fallisce se il csv esiste già. |

---

## 📂 Struttura Cartelle di Output

```text
data/derived/sdc/<session_name>/
├── manifest.csv                 # Lista totale pz considerati
├── manifest_excluded.json       # Pazienti esclusi e motivazioni
├── _status/                     # Cartella degli esiti paziente (.json)
├── _work/                       # Workspace temporaneo, non rimosso in auto
├── manifest.json                # Report riassuntivo finale
├── config.md                    # Dettagli configurazione run
└── <subject_id>/lesion/         # Risultati validi combinati per il paziente
    ├── <pz>_desc-disconnectome.nii.gz
    ├── <pz>_desc-disconnectome_mapstats.tsv
    └── <pz>_LF-disconnectome_atlas-<nome>.csv
```

> **Dry-Run**: In `mode run`, il parametro `--dry-run` pianifica ed espone i path senza lanciare le operazioni pesanti. Ottimo per verificare l'integrità dei dati prima della produzione.
