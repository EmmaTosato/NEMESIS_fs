# Stato progetto — NEMESIS

Ultimo aggiornamento: 2026-07-21. Snapshot dello stato attuale del progetto — non un log cronologico. Errori passati, bug risolti e strade scartate vivono in `.claude/lessons_learned.md` (pattern generalizzabili) e `docs/debugging/` (narrativa completa per sessione di debug); l'evoluzione delle decisioni strategiche vive in `.claude/decision_log.md`; qui restano solo le regole/vincoli in vigore oggi e la mappa dello stato attuale.

## Core Context

NEMESIS è il repo di lavoro per un progetto di ricerca in neuroimaging dello stroke (Corbetta lab): costruisce embedding a bassa dimensionalità di lesioni cerebrali e disconnettomi strutturali/funzionali, li clusterizza, e mette in relazione i cluster con outcome clinico-comportamentali (NIHSS, linguaggio, neglect, dominio motorio). Serve il team di ricerca per testare l'ipotesi lesione↔disconnessione↔outcome su 4 coorti cliniche reali (~1300 soggetti totali).

## Architettura e Tech Stack

- **Linguaggio**: Python 3.11, ambiente conda `nemesis` (`environment.yml`): numpy, scipy, pandas, scikit-learn, umap-learn, matplotlib, seaborn, networkx, jupyterlab, nibabel, nilearn.
- **Esecuzione**: cluster SLURM condiviso — ogni pipeline/script gira solo tramite job `sbatch` (`jobs/run_<name>.sh`, file singolo direttamente sotto `jobs/` — una sottocartella `jobs/<name>/` solo se quella pipeline arriva ad avere più di uno `.sh`), mai `python` diretto sul login node.
- **Dati**: sorgente grezza (`*.nii`, `*.nii.gz`, `.csv` di feature) su EBRAIN, mount `/data/corbetta/Clinical_connectome/` — non versionata nel repo. 4 dataset in scope: `UNIPD/WashU`, `UNIPD/PASPORT`, `UNIPD/PSP`, `UKLFR/stroke_UKLFR`, tutti in formato BIDS reale (raw + `derivatives/manual_masks/`).
- **Config**: JSON versionato sotto `config/`, un file per pipeline/dominio.
- **Testing**: `pytest`, `tests/unit/` + `tests/integration/`.
- **Versionamento**: git.

## Decisioni e Vincoli Architetturali

- **Niente fallback silenziosi**: ogni caso limite (input mancante, file assente, formato inatteso) solleva un errore esplicito con messaggio che identifica cosa manca, oppure è gestito con una strategia intenzionale e documentata — mai una toppa che nasconde il problema.
- **Architettura a livelli**: `utils` → `retrieval` → `features` → `models`/`analysis` → `pipeline`. I livelli alti dipendono dai bassi, mai il contrario.
- **Entry point centralizzati**: un solo punto d'ingresso per pipeline in `src/pipeline/`, niente script sparsi. Ogni pipeline/script (`src/pipeline/*.py`, `scripts/*.py`) ha il proprio `jobs/run_<name>.sh` gemello, aggiunto insieme al codice, non dopo.
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
`config/pipelines/retrieval.json` + `config/registry/file_patterns.json` → `src.retrieval.config.load_config` → `Dataset` (`src/retrieval/dataset.py`, risoluzione file pigra, nessun I/O alla costruzione) → `src.pipeline.retrieve_data.main()` (valida upfront su tutti i dataset richiesti, copia, verifica checksum post-copia via `src/retrieval/verify.py`, scrive `copy_summary` + log). `src/retrieval/matrix.py` + `scripts/data_summary.py` generano CSV di disponibilità dati per l'intero registro, indipendenti dal report di un singolo run.

**Copertura dati attuale (registro `config/registry/file_patterns.json`)**: **solo** `lesion/manual_masks/anat/lesion_mask`, su tutti e 4 i dataset. `feature`/`FC-pearson` è stato rimosso dal registro (era limitato a `UNIPD/WashU`, 2 atlanti su ~30 disponibili) — non richiesto per ora, non nei piani immediati. Provata e poi scartata nella stessa sessione anche una voce `lesion/raw/anat/lesion_roi` (lesione in spazio nativo, verificata su disco: WashU 202/319, PASPORT 83/97, PSP **0/237**, UKLFR 735/735) — rimossa su richiesta esplicita, non è nel registro oggi.

**Nota**: `docs/dev/retrieval.md` e `docs/guides/retrieval.md` descrivono ancora `feature`/`FC-pearson` in dettaglio (esempi, tabelle, sezione "Writing retrieve items") come se fosse registrato — è un disallineamento noto tra doc e config reale, segnalato all'utente, non ancora risolto (decisione in sospeso: aggiornare la doc per riflettere lo stato attuale, o lasciarla come riferimento per una reintroduzione a breve).

**Pipeline di analisi — solo scheletro, non ancora operativa.**
`src/analysis/config.py` (parsing config), `src/analysis/steps.py` (registry vuoto), `src/pipeline/run_analysis_pipeline.py` (CLI), `src/pipeline/checkpoint.py` (cache per step con hash a catena), `src/utils/` (step/hashing/artifact_store): infrastruttura completa e testata, ma nessuno step di dominio reale (feature extraction da lesion mask, PCA/UMAP, clustering) esiste ancora.

**Non esiste ancora**: nessun modulo di embedding, clustering, o analisi clinica reale.

## Infrastruttura Esterna — BCBToolKit/BCBlib (calcolo SDC)

**Non è codice del repo** (nessun file sotto `src/`) — è un tool esterno di terze parti (BCBlab)
necessario per calcolare le SDC (structural disconnectome), installato **localmente
nell'account `etosato`** invece che a livello di server condiviso, perché l'utente non ha i
permessi di sistema per il setup condiviso descritto dal maintainer (Chris Foulon): niente
accesso a `/data/tshimanga/BCBToolKit` (copia esistente di un altro utente), niente scrittura
sotto `/shared/`, niente `/etc/environment`. Richiesta di setup condiviso già inviata
all'amministratore del server, risposta non ancora pervenuta.

**Stato**: installazione locale **funzionante e verificata end-to-end su un soggetto reale del
progetto** (`sub-STUNIPD0001`, 20/07): Stage 1 (`bcb-lf-preprocess`, calcolo SDC) e Stage 2
(`bcb-lesion-features`, estrazione feature per 14 atlanti EBRAINS) entrambi riusciti via `sbatch`
(job SLURM `332206`/`332207`). Nel farlo, emerso e risolto un mismatch glibc tra login node
(2.35) e nodi di calcolo (2.27): `h5py` installato via `pip` portava un `libhdf5` binario
incompatibile coi nodi di calcolo — fix: reinstallato da `conda-forge`
(`conda install -n nemesis -c conda-forge h5py --force-reinstall -y`).

**Dettaglio completo, passo per passo, con ogni comando eseguito e il comando esatto di
rimozione per ciascuno**: `/data/etosato/tools/INSTALL_LOG.md` (fuori dal repo Nemesis, vive
insieme all'installazione stessa; include la tabella di confronto punto-per-punto con la mail
originale del maintainer e le domande metodologiche aperte, vedi sotto). La documentazione
"come si usa" (Stage 1/Stage 2, script diretti quando il wrapper non basta) è stata separata in
`/data/etosato/tools/USAGE.md`; `README.md` è ora solo un indice tra i due.

**Punto tecnico non ovvio, utile a chi riprende**: il pacchetto scaricato da `toolkit.bcblab.com`
è in realtà un repository git congelato a un commit del 2017, mancante di `run_disco.sh`/
`tractotron_cli.sh`/`nulldeform.mat`. Risolto inizialmente con un `git checkout` mirato dei soli
file mancanti (non un `git pull` pieno, per prudenza su binari FSL/librerie con contenuto diverso
dal commit registrato). **21/07**: verificato con `git diff` contro `origin/master` che quei
binari erano in realtà già identici alla `master` corrente (non una patch custom, solo un
pacchetto scaricato più aggiornato del commit congelato) — fatto quindi un `git pull` pieno
(via stash/pull/stash-pop, un solo conflitto su uno script legacy non usato da BCBlib, risolto
tenendo la versione upstream). Repo ora allineato a `origin/master` (HEAD `17456eb`).

**Riorganizzazione `/data/etosato/` (21/07)**: rimosso `BCBToolKitLINUX.tar.gz` (7.6GB, morto dal
`git pull`), spostate le cache `bcblib_atlases/`/`templateflow/` da top-level a dentro `tools/`
(env var aggiornate in `~/.bashrc`). `data/etosato/data/` e `results/{lorenzo_data,paper_trial}`
non toccati (materiale di altri lavori).

**Domande metodologiche aperte** (dettaglio in `INSTALL_LOG.md` §9), da decidere prima di usare
la pipeline su dati reali su scala: (1) atlante trattografie di riferimento — oggi solo 10
soggetti (sottoinsieme parziale del 2017), ⏳ download in corso dell'atlante Dropbox completo a
1mm (180 soggetti, quello raccomandato per lesioni a 1mm come le nostre); (2) se applicare una
soglia alla probabilità di disconnessione continua (oggi nessuna, il flag `-t` di `run_disco.sh`
non è esposto dal wrapper); (3) se Task 2 (embedding) debba consumare l'output voxelwise di
Stage 1 o le tabelle per-atlante di Stage 2; (4) quale sottoinsieme dei 14 atlanti EBRAINS serva
davvero per Task 5, in base ai domini clinici da spiegare.

## Work In Progress

Il refactor dello schema di retrieval verso vocabolario BIDS (config, codice, test, doc, run reali) è stato **committato** (10 commit separati per categoria). Da lì, in questa sessione, `config/registry/file_patterns.json` è stato modificato ulteriormente in working tree (non ancora committato): rimosso `feature`, provata e rimossa `lesion/raw` — il file ora ha solo `lesion/manual_masks`. I 4 CSV di `data_summary` (ora in `reports/datasets/`, senza sottocartella `<project>` — spostati fuori da `reports/data_retrieval/` in una sessione successiva, `scripts/data_summary.py` ha oggi un `REPORTS_ROOT` proprio invece di importarlo da `retrieve_data.py`) sono stati rigenerati (`sbatch jobs/run_data_summary.sh`) mentre `raw` era ancora nel registro, quindi contengono una colonna `lesion/raw/anat/lesion_roi` ormai stale rispetto al registro attuale — vanno rigenerati un'altra volta prima di committare, per riflettere lo stato finale (solo `manual_masks`).

In parallelo (fuori dal repo): setup locale di BCBToolKit/BCBlib per il calcolo SDC, vedi sezione
dedicata sopra — Stage 2 del test da completare.

## Prossimi Passi

1. Rilanciare `sbatch jobs/run_data_summary.sh` per aggiornare i 4 CSV allo stato attuale del registro (solo `lesion/manual_masks`, senza la colonna `raw` stale).
2. Decidere sul disallineamento doc/config per `feature` (vedi "Mappa dello Stato Attuale") — poi committare `config/registry/file_patterns.json` + i CSV rigenerati.
3. Decidere se/quando riaggiungere `feature`/`FC-pearson` (o `lesion/raw`) a `config/pipelines/retrieval.json` — oggi `retrieve` chiede solo `lesion/manual_masks/anat/lesion_mask`.
4. Iniziare a popolare `src/analysis/steps.py` con il primo step reale (es. feature extraction dalle lesion mask) per sbloccare la pipeline di analisi, oggi solo scheletro.
5. A download dell'atlante trattografie completato (180 soggetti 1mm), sostituire
   `Tools/extraFiles/tracks/` e aggiornare il punto 1 delle domande metodologiche in
   `INSTALL_LOG.md` §9.
6. Decidere le altre 3 domande metodologiche aperte su BCBToolKit (soglia disconnessione,
   voxelwise vs per-atlante per Task 2, quali atlanti servono per Task 5) — richiede input dal
   team/letteratura, non risolvibile da soli.
7. Seguire la risposta dell'amministratore del server sulla richiesta di setup condiviso di
   BCBToolKit/BCBlib (mail inviata, risposta non ancora arrivata).
8. Decidere l'architettura del modulo `src/` che orchestrerà `bcb-lf-preprocess`/
   `bcb-lesion-features` sui dati reali già recuperati da `retrieve_data.py` (nessun codice
   scritto finora in questa direzione — solo il tool esterno è stato validato end-to-end).
