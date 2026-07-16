# Stato progetto — NEMESIS

Ultimo aggiornamento: 2026-07-16. Snapshot dello stato attuale del progetto — non un log cronologico. Errori passati, bug risolti e strade scartate vivono in `.claude/lessons_learned.md` (pattern generalizzabili) e `docs/debugging/` (narrativa completa per sessione di debug); qui restano solo le regole e i vincoli in vigore oggi.

## Core Context

NEMESIS è il repo di lavoro per un progetto di ricerca in neuroimaging dello stroke (Corbetta lab): costruisce embedding a bassa dimensionalità di lesioni cerebrali e disconnettomi strutturali/funzionali, li clusterizza, e mette in relazione i cluster con outcome clinico-comportamentali (NIHSS, linguaggio, neglect, dominio motorio). Serve il team di ricerca per testare l'ipotesi lesione↔disconnessione↔outcome su 4 coorti cliniche reali (~1300 soggetti totali).

## Architettura e Tech Stack

- **Linguaggio**: Python 3.11, ambiente conda `nemesis` (`environment.yml`): numpy, scipy, pandas, scikit-learn, umap-learn, matplotlib, seaborn, networkx, jupyterlab, nibabel, nilearn.
- **Esecuzione**: cluster SLURM condiviso — ogni pipeline/script gira solo tramite job `sbatch` (`jobs/<name>/run_<name>.sh`), mai `python` diretto sul login node.
- **Dati**: sorgente grezza (`*.nii`, `*.nii.gz`, `.csv` di feature) su EBRAIN, mount `/data/corbetta/Clinical_connectome/` — non versionata nel repo. 4 dataset in scope: `UNIPD/WashU`, `UNIPD/PASPORT`, `UNIPD/PSP`, `UKLFR/stroke_UKLFR`, tutti in formato BIDS reale (raw + `derivatives/manual_masks/`).
- **Config**: JSON versionato sotto `config/`, un file per pipeline/dominio.
- **Testing**: `pytest`, `tests/unit/` + `tests/integration/`.
- **Versionamento**: git.

## Decisioni e Vincoli Architetturali

- **Niente fallback silenziosi**: ogni caso limite (input mancante, file assente, formato inatteso) solleva un errore esplicito con messaggio che identifica cosa manca, oppure è gestito con una strategia intenzionale e documentata — mai una toppa che nasconde il problema.
- **Architettura a livelli**: `utils` → `retrieval` → `features` → `models`/`analysis` → `pipeline`. I livelli alti dipendono dai bassi, mai il contrario.
- **Entry point centralizzati**: un solo punto d'ingresso per pipeline in `src/pipeline/`, niente script sparsi. Ogni pipeline/script (`src/pipeline/*.py`, `scripts/*.py`) ha il proprio `jobs/<name>/run_<name>.sh` gemello, aggiunto insieme al codice, non dopo.
- **Config = single source of truth**: nessun valore ambiente-dipendente (path, soglie, iperparametri) hardcoded nel codice; ogni valore vive in un solo posto.
- **Schema di retrieval in vocabolario BIDS**: un `RetrieveItem` ha campi `object` (`lesion`/`feature`), `pipeline`, `datatype`, `suffix` — la *forma* dei campi non è uniforme tra `object`: `pipeline` è obbligatorio per `lesion` (nome di pipeline BIDS-Derivatives reale, oggi `manual_masks`) e vietato per `feature` (nessun `dataset_description.json` sotto `features/`, nessuna pipeline reale da nominare). Questa regola è validata sia a livello di modulo sia per-istanza, mai con un branching implicito a 2 vie.
- **Un dataset che non ha affatto un `object` richiesto è un WARNING per-dataset** (quel `retrieve` item viene saltato solo per quel dataset, il run continua) — non uno STOP globale. Se un dataset non supporta **nessuno** dei `retrieve` item richiesti, resta invece uno STOP upfront (probabile errore nella lista `datasets` del config).
- **`resolve()` ritorna sempre tutti i match** registrati per un item — mai un concetto di priorità/ambiguità tra template.
- **Verifica checksum post-copia è una fase distinta**, eseguita solo dopo che *tutti* i dataset richiesti hanno finito la fase di copia, mai interlacciata.
- **`participants.tsv` è tracciato separatamente** dai conteggi dei file dati (colonna propria nel report) — mai sommato a `copied`/`skipped_existing` dei file immagine/feature.
- **Retrieval nativo/raw (anat/dwi/func grezzi) è fuori scope** per il momento — variabilità troppo alta tra dataset (naming dei run func, varianti di acquisizione dwi, presenza incostante di `lesion_roi`) per generalizzare ora senza dati concreti da cui derivare i template.
- **Pipeline di analisi**: registry degli step (`src.analysis.steps.STEP_REGISTRY`) deliberatamente vuoto — è uno scheletro (config parsing, checkpointing, CLI), non contiene ancora nessuno step di dominio reale.
- **Testing**: `tests/unit/` con fixture sintetiche isolate (no I/O esterno); `tests/integration/` contro il mount EBRAIN reale, skippati automaticamente se non raggiungibile, mai con conteggi hardcoded — sempre un confronto differenziale ricalcolato dal filesystem al momento del test.

## Mappa dello Stato Attuale

**Retrieval — stabile, verificato con run reali in produzione.**
`config/retrieval.json` + `config/file_patterns.json` → `src.retrieval.config.load_config` → `Dataset` (`src/retrieval/dataset.py`, risoluzione file pigra, nessun I/O alla costruzione) → `src.pipeline.retrieve_data.main()` (valida upfront su tutti i dataset richiesti, copia, verifica checksum post-copia via `src/retrieval/verify.py`, scrive `copy_summary` + log). `src/retrieval/matrix.py` + `scripts/data_summary.py` generano CSV di disponibilità dati per l'intero registro, indipendenti dal report di un singolo run. Copertura dati attuale: `lesion/manual_masks/anat/lesion_mask` su tutti e 4 i dataset; `feature/func/FC-pearson` (2 atlanti su ~30 disponibili) solo su `UNIPD/WashU`.

**Pipeline di analisi — solo scheletro, non ancora operativa.**
`src/analysis/config.py` (parsing config), `src/analysis/steps.py` (registry vuoto), `src/pipeline/run_analysis_pipeline.py` (CLI), `src/pipeline/checkpoint.py` (cache per step con hash a catena), `src/utils/` (step/hashing/artifact_store): infrastruttura completa e testata, ma nessuno step di dominio reale (feature extraction da lesion mask, PCA/UMAP, clustering) esiste ancora.

**Non esiste ancora**: nessun modulo di embedding, clustering, o analisi clinica reale.

## Work In Progress

Nessuna modifica di codice in corso al momento. L'ultimo lavoro (refactor dello schema di retrieval verso vocabolario BIDS) è concluso, testato (148/148 in `tests/unit/`+`tests/integration/`) e verificato con run `sbatch` reali su tutti e 4 i dataset — ma **non ancora committato** (working tree modificata, verificare con `git status`/`git diff` prima di procedere).

## Prossimi Passi

1. Commit del refactor retrieval corrente in working tree (nulla ancora committato).
2. Decidere se/quando riaggiungere l'item `feature`/`FC-pearson` a `config/retrieval.json` (rimosso su richiesta esplicita per il giro attuale — resta solo `lesion`).
3. Iniziare a popolare `src/analysis/steps.py` con il primo step reale (es. feature extraction dalle lesion mask) per sbloccare la pipeline di analisi, oggi solo scheletro.
