# Stato progetto — NEMESIS

Ultimo aggiornamento: 2026-07-26. Snapshot dello stato attuale del progetto — non un log cronologico. Errori passati, bug risolti e strade scartate vivono in `.claude/lessons_learned.md` (pattern generalizzabili) e `docs/debugging/` (narrativa completa per sessione di debug); l'evoluzione delle decisioni strategiche vive in `.claude/decision_log.md`; qui restano solo le regole/vincoli in vigore oggi e la mappa dello stato attuale.

## Sessione 2026-07-26 — Esplorazione soglia di esclusione paziente (masked FC) + separazione teoria/notebook

**Obiettivo**: continuare dal punto lasciato in sospeso il 25/07 (soglia di esclusione paziente su `mask_summary.csv`, vedi sessione 2026-07-25 sotto) — analizzare i dati reali (169 pazienti WashU) prima di fissare una soglia, senza ancora deciderla. Nel farlo, l'utente (guidata passo-passo, non esperta di codice) ha chiesto più volte chiarimenti sulla teoria del masking FC e una riorganizzazione di dove quella teoria vive.

**Decisioni prese / concetti discussi**:
- **Nessuna soglia di esclusione decisa in questa sessione** — l'utente ha chiesto esplicitamente di guardare i dati reali prima di scegliere un numero, non di fissarlo di getto. Resta il prossimo passo esatto (vedi sotto), con i grafici già pronti per farlo.
- **Dove va l'analisi esplorativa sui dati reali**: dopo un primo tentativo sbagliato (aggiunta a `notebooks/artifacts_inspection.ipynb`, poi rimossa perché l'utente pensava andasse in `fc_lesion_masking.ipynb`), chiarito e confermato con l'utente che `fc_lesion_masking.ipynb` documenta lo **sviluppo del metodo** (prototipo chiuso, su 3 pazienti demo) mentre l'analisi su dati reali/decisioni operative (soglia di esclusione) va in `artifacts_inspection.ipynb`, organizzato per tipo di artefatto prodotto — sezione "Masked FC matrices" aggiunta lì.
- **Un nodo compromesso non è 1 connessione persa**: emerso e mostrato esplicitamente all'utente che un singolo nodo compromesso invalida fino a 238 connessioni (tutta la sua riga/colonna in una rete da 239 nodi) — il conteggio "nodi compromessi" non è quindi proporzionale alla frazione reale di dati persi. La sezione aggiunta mostra sia la curva soglia→pazienti-esclusi sia lo scatter nodi-compromessi vs. %-NaN-reale nella matrice finale, per decidere la soglia con questo in mente.
- **Teoria del metodo separata dal notebook prototipo**: su richiesta esplicita dell'utente, la teoria/letteratura/decisioni di `fc_lesion_masking.ipynb` (cos'è una matrice FC, notazione `NodoA__NodoB`, Siegel/Griffis/XCP-D, decisioni di metodo, esempio numerico) è stata spostata in un nuovo documento `assets/knowledge/fc_lesion_masking.md`. Il notebook resta come esecuzione/prototipo, con le celle markdown ridotte a indicazioni di step + link alla sezione corrispondente del `.md`; nessuna cella di codice toccata, notebook ri-eseguito e output numerici verificati identici a prima del trimming.
- Aggiunto al `.md`, su richiesta dell'utente, un esempio concreto in voxel per spiegare "percentuale di zona sana" (zona fatta di 50 voxel, 10 sani → 20%) — chiarimento nato da un dubbio reale dell'utente sul significato letterale di "percentuale di una zona cerebrale".
- **Proposta di ulteriore sfoltimento del `.md` rifiutata dall'utente** (accorpare 2 step implementativi nell'esempio numerico, per ridurre ridondanza) — l'utente ha chiesto di aggiungere solo l'esempio voxel e lasciare il resto invariato. Da tenere a mente: non riproporre quel trimming senza che lo richieda di nuovo.

**File modificati/creati**:
- Nuovo: `assets/knowledge/fc_lesion_masking.md` — teoria del masking FC (matrice di connettività con esempio numerico, notazione edge, letteratura, decisioni di metodo, esempio passo-passo con voxel, atlante, riferimento rapido pipeline).
- `notebooks/fc_lesion_masking.ipynb` — celle markdown sfoltite (link al `.md` per la teoria), nessuna cella di codice toccata.
- `notebooks/artifacts_inspection.ipynb` — nuova sezione "Masked FC matrices": distribuzione nodi compromessi per paziente, curva soglia→pazienti-esclusi, scatter nodi-compromessi vs. %-connessioni-NaN, tutto su dati reali (169 pazienti, atlante `Yan200TianS2Buckner7N`).

**Nota — attività di auto-commit/parallela, stesso pattern già visto in sessioni precedenti** (vedi sessione 2026-07-21 (2) più sotto per il primo caso documentato): le modifiche a entrambi i notebook e la prima versione di `fc_lesion_masking.md` sono comparse già committate in `482c270` "Update clustering tuning results, notebooks, and plotting scripts" (18:23, 25/07) — un commit-bundle che include anche lavoro non fatto da questa sessione (tuning clustering, altri notebook, risultati). Nessun comando git eseguito da questo agente. Solo l'ultima modifica al `.md` (esempio voxel) risultava non committata al momento di scrivere questa sezione — verificare `git status`.

**Stato dei test**: nessun codice in `src/` toccato in questa sessione (solo notebook e documentazione) — `pytest` non rilanciato, non necessario.

**Prossimo passo esatto**: decidere la soglia di esclusione paziente guardando i grafici già pronti in `notebooks/artifacts_inspection.ipynb`, sezione "Masked FC matrices" (dati reali, 169 pazienti, atlante `Yan200TianS2Buckner7N`):
1. Aprire quella sezione, guardare la curva "pazienti esclusi in funzione della soglia" e la tabella soglie candidate (es. soglia 12 nodi/5% della rete esclude 13/169; soglia 24 nodi/10% esclude 4/169), insieme allo scatter nodi-compromessi vs. %-connessioni-NaN reali (un nodo compromesso costa fino a 238 connessioni, non 1).
2. Una volta scelta la soglia con l'utente: implementarla come parametro esplicito e configurabile in `config/pipelines/build_fc_matrix.json` + `src/pipeline/build_fc_matrix.py` (oggi non filtra nessun paziente — la matrice include tutti i 169), con test unitario/regressione per il nuovo comportamento di esclusione.
3. Rilanciare `build_fc_matrix.py` sui dati reali per rigenerare la matrice finale filtrata (nuovo `run_name`, per non sovrascrivere `24-07_s1`).
4. Solo dopo, riprendere gli altri due punti aperti dalla sessione 2026-07-25 sotto: le altre 11 combinazioni di atlante, l'imputazione NaN vicino a `dim_reduction.py`.

## Sessione 2026-07-25 (2) — Tuning `dim_reduction_clustering`: fix titoli plot, analisi risultati, log spariti

**Obiettivo**: proseguire il lavoro (sessione precedente) di aggiunta della modalità `fine_tuning` a `dim_reduction_clustering.py`/`clustering.py` — fix di un mismatch nei titoli dei plot di tuning, poi analisi dei risultati di tuning sulle 4 riduzioni (umap/tsne/pacmap/pca) × 5 metodi di clustering.

**Decisioni prese / concetti discussi**:
- **Fix titolo plot di tuning**: `_write_tuning_output` in `dim_reduction_clustering.py` usava ancora `compose_run_title` (vecchio formato) mentre la modalità produzione nello stesso file era già stata migrata a `compose_cluster_plot_title` (sessione parallela). Corretto a `compose_cluster_plot_title(output_dir, config.reduction_method, method)`; aggiunto styling coerente (grassetto, stessa fontsize/pad) alle 4 funzioni di plot condivise in `plotting.py` (`plot_clustering_tuning_metrics`, `plot_dendrogram`, `plot_eigengap`, `plot_k_distance`).
- **Il fix non è retroattivo**: i plot già su disco (generati prima del fix) restano col titolo vecchio finché non si rilancia il tuning con `overwrite: true`. Rilanciato per tutte e 4 le riduzioni (prima solo 4 metodi kmeans/agglomerative/gmm/dbscan, poi un secondo giro con anche `spectral` per umap/tsne/pca — pacmap resta senza spectral, escluso di proposito per il problema noto dei gruppi satellite disconnessi).
- **Log spariti dal disco senza causa nota**: dopo il primo giro di rerun, i log corrispondenti (incluse le run originali delle 12:43-12:49 del 24/07) non erano più presenti in `logs/dim_reduction_clustering/clinical_connectome/` — stesso pattern di sparizioni non spiegate già osservato in sessioni precedenti (non causato dal codice di questa sessione, verificato che il tuning non tocca cartelle sorelle). Rilanciato il tuning di pacmap una terza volta per rigenerare il log; essendo cambiata la data (24→25 luglio) il tag di output è cambiato (`24-07_s1.1_n5`→`25-07_s1.1_n5`), creando cartelle duplicate — le vecchie (dati identici, senza log) sono state rimosse su richiesta.

**Analisi dei risultati di tuning** (silhouette/Calinski-Harabasz/Davies-Bouldin su 1150 soggetti, matrice voxel-wise):
- **Umap** è la riduzione più affidabile: kmeans e gmm confermano `k=4` (default registry) come ottimo locale reale. dbscan invece non trova struttura (silhouette ~0 o negativo).
- **Pacmap**: tutti i metodi a k variabile preferiscono `k=2` come silhouette massimo assoluto (coerente col pattern blob+satelliti già noto), con massimo locale secondario a k=6; il default k=4 non è il picco ma resta una scelta ragionevole più fine.
- **Tsne**: struttura debole ovunque, il massimo è quasi sempre banalmente k=2; i valori alti di dbscan sono un artefatto (96-99% dei punti classificati come noise).
- **Pca (150 componenti)**: nessun metodo trova struttura robusta — dbscan e spectral falliscono quasi del tutto (curse of dimensionality), gmm ha BIC/AIC instabili. Conferma indiretta del perché la pipeline clusterizza su proiezioni 2D e non sui componenti PCA grezzi.
- **Nessun valore "tuned" è stato applicato alla produzione** — il tuning resta puramente diagnostico (nessuna selezione automatica), coerente con la filosofia del progetto. I risultati di produzione su disco per tutte e 4 le riduzioni usano ancora i default del registry.

**File modificati**: `src/pipeline/dim_reduction_clustering.py` (fix titolo tuning), `src/analysis/plotting.py` (styling titoli tuning). `config/pipelines/dim_reduction_clustering.json` modificato ripetutamente per i rerun, poi ripristinato allo stato di produzione (`reduction_method: pacmap`, `fine_tuning: false`).

**Stato dei test**: non rilanciati in questa sessione (nessuna modifica a logica di dominio, solo styling titoli — il fix era già coperto dai test esistenti sulla sessione precedente).

**Prossimo passo esatto**: decidere se applicare uno dei valori suggeriti dal tuning (es. `k=2` per pacmap) a una run di produzione, o lasciare tutto ai default finché non emerge una motivazione clinica/metodologica più forte per cambiarli. Da tenere d'occhio: il pattern di log/risultati che spariscono dal disco senza azione dell'agente — non ancora capito da dove venga, segnalarlo esplicitamente se si ripresenta.

## Sessione 2026-07-25 — Masking FC per lesione: da "va fatto" a pipeline in produzione, girata su tutta la coorte WashU

**Obiettivo**: l'utente (non esperta del dominio tecnico, guidata passo-passo) ha chiesto di mascherare le feature di connettività funzionale (FC) già calcolate per la coorte WashU (`data/clinical_connectome/derivatives/UNIPD/WashU/features/`) in funzione della lesione di ciascun paziente, poi costruire una matrice 2D pronta per la riduzione dimensionale (Task 3).

**Decisioni prese / concetti discussi** (in ordine, ognuna verificata prima di procedere, mai assunta):
- **Metodologia non inventata**: cercata in letteratura prima di scrivere codice. Riferimenti chiave: Siegel et al. 2016 (stessa coorte WashU — connessioni lesionate azzerate nei modelli multivariati), Griffis et al. 2019 (soglia 50% overlap per escludere un nodo, già in `assets/papers/`), XCP-D (`xcp_d/interfaces/connectivity.py`, classe `NiftiParcellate` — stesso schema `min_coverage` già usato dal tool che ha generato queste stesse FC).
- **Zero vs NaN, poi deciso NaN**: prima ipotesi era azzerare (stile Siegel). Approfondendo la letteratura (Griffis et al. 2019: *"the PLSC approach cannot accommodate missing values ... set to 0"*) emerso che il campo marca NaN e sostituisce con zero **solo** subito prima di un metodo che non tollera dati mancanti — non alla sorgente. Deciso di separare: `mask_fc.py` marca NaN e si ferma lì; l'imputazione (passo "Fase C") resta **non implementata**, deliberatamente fuori scope, da collocare vicino a `dim_reduction.py` quando si deciderà la strategia (default previsto: `"zero"`).
- **Due pipeline separate, anche a livello di config** (non una sola): `mask_fc.py` (lesione+FC grezza → CSV mascherati con NaN, per soggetto) e `build_fc_matrix.py` (solo CSV già mascherati → matrice impilata). Motivo: permettere di analizzare `mask_summary.csv` su tutta la coorte e decidere una soglia di esclusione paziente **prima** di costruire la matrice finale, senza dover rifare il masking ogni volta.
- **Atlante**: 12 combinazioni (`Yan{100,200,300,400}TianS{1,2,3}Buckner7N`) recuperate da `/data/corbetta/Clinical_connectome/Atlases/fmriprep/` (server, via SSH `pnc-vpn` — funziona non-interattivo, `BatchMode=yes`) e committate in `assets/atlases/fmriprep/` (formato BIDS-Derivatives `dseg.tsv`+`dseg.nii.gz`, verificato che l'ordine nodi combaci esattamente con le CSV FC reali). Solo `Yan200TianS2Buckner7N` validata/usata finora.
- **Parcellizzazione**: niente funzione scritta a mano — riusato `nilearn.maskers.NiftiLabelsMasker` con lo stesso schema a doppio masker di XCP-D (un masker senza maschera conta tutti i voxel, uno con `mask_img=healthy_img` conta i sani, il rapporto è la coverage).
- **Vettorizzazione**: solo triangolo superiore (no diagonale, la matrice FC è simmetrica) — nomi connessione `nodoA__nodoB`.
- **Output su disco confermati dall'utente**: `data/derived/features/masked_fc/<combo>/` (CSV mascherati per soggetto, con NaN) e `data/derived/features/fc_matrix/<combo>/<data>_<session>/` (matrice finale, stesso formato atomico di `build_lesion_matrix.py` — `matrix.npy`/`metadata.csv`/`manifest.json`/`config.md` + `edge_names.npy`).
- **`drop_constant_edges`**: una colonna con **qualunque** NaN non viene mai valutata per costanza — tenuta a prescindere (punto di design volutamente non ancora deciso, vedi soglia di esclusione sotto). Un edge identico per tutti i pazienti tra quelli senza NaN è invece un'anomalia per dati continui (non normale come nel caso binario delle lesioni) — loggato a `WARNING`, non silenzioso.

**File creati** (tutti già committati dall'utente stesso in commit paralleli — `b031c81` "functional masking", `6eb2311`/`97daffe`/`0382c02` "results" — nessuna azione di commit fatta da questa sessione agente):
- Codice: `src/features/functional.py`, `src/pipeline/mask_fc.py`, `src/pipeline/build_fc_matrix.py`, `src/analysis/build_config.py` (aggiunte `MaskFcConfig`/`BuildFcMatrixConfig`)
- Config/job: `config/pipelines/mask_fc.json`, `config/pipelines/build_fc_matrix.json`, `jobs/run_mask_fc.sh`, `jobs/run_build_fc_matrix.sh`
- Test: `tests/unit/test_features_functional.py` (25 test, incluso un regression test per ciascuno dei 2 bug sotto), `tests/integration/test_mask_fc_pipeline.py` (3 test E2E), `tests/integration/test_build_fc_matrix_pipeline.py` (3 test E2E)
- Doc: `docs/dev/analysis.md` (sezione aggiornata da "planned" a "implemented"), `docs/guides/fc_matrix_building.md` (nuova), `README.md` (paragrafo aggiunto), `docs/debugging/debug_23_07_26.md` (nuovo), `.claude/lessons_learned.md` (pattern #13, nuovo)
- Esplorativo: `notebooks/fc_lesion_masking.ipynb` (prototipo eseguito realmente, con spiegazioni in linguaggio semplice per utente non tecnica — precede e motiva il codice in `src/`)
- Dati reali generati (run locale su tutta la coorte WashU, 169 soggetti, combo `Yan200TianS2Buckner7N`): `data/derived/features/masked_fc/Yan200TianS2Buckner7N/` (169 CSV + `mask_summary.csv`) e `data/derived/features/fc_matrix/Yan200TianS2Buckner7N/24-07_s1/` (matrice 169×28441)

**Errori trovati e corretti** (narrativa completa in `docs/debugging/debug_23_07_26.md`):
1. Overflow silenzioso in `uint8` nel conteggio voxel-per-parcel via `NiftiLabelsMasker(strategy="sum")` — un parcel da 695 voxel risultava 183 (`695 mod 256`). Fix: `int32`.
2. Un parcel completamente lesionato **sparisce** dall'output del masker mascherato invece di leggere 0 — rischio di crash (shape mismatch) o disallineamento silenzioso. Fix: indicizzare per label id/nome, mai per posizione.
3. (minore, in `build_fc_matrix.py`) `np.save` su un array `edge_names` con `dtype=object` produce un file non rileggibile da `np.load` senza `allow_pickle=True` — fix: lasciare che numpy inferisca il proprio dtype stringa nativo (nessun `dtype=object`).

**Stato dei test**: 344 passed, 12 skipped, 0 failed (`pytest tests/ -q`, rilanciata più volte durante la sessione, ultima volta dopo tutte le modifiche).

**Run reale eseguita** (in locale su questo Mac, non su cluster — richiesta esplicita dell'utente "voglio runnare solo qua"): `mask_fc.py` + `build_fc_matrix.py` su tutta la coorte WashU reale (169 soggetti con sia lesione che FC per la combo `Yan200TianS2Buckner7N`). Distribuzione nodi compromessi per paziente: mediana 1, media 3.9, max 42/239 (~18%), 0 pazienti sopra 50 nodi compromessi, 80/169 pazienti senza nessun nodo compromesso.

**Prossimi passi esatti**:
1. Analizzare `data/derived/features/masked_fc/Yan200TianS2Buckner7N/mask_summary.csv` (già generato, numeri sopra) per decidere una soglia di esclusione paziente — non ancora implementata in `build_fc_matrix.json`/`build_fc_matrix.py` di proposito.
2. Ripetere `mask_fc.py`/`build_fc_matrix.py` sulle altre 11 combinazioni di atlante (oggi solo `Yan200TianS2Buckner7N` in `atlas_combos`) — bastano modifica dei due config e rilancio, nessun cambio di codice.
3. Implementare il passo di imputazione NaN (Fase C, non ancora scritto) come funzione separata e configurabile vicino a `src/analysis/reduction.py`/`dim_reduction.py` — default `"zero"`, loggando quanti valori vengono sostituiti.
4. Sul cluster: il branch lì (`server-pnc`) è diverso da `main` e ha modifiche proprie non committate (`src/pipeline/compute_sdc.py`) — se/quando si vorrà lanciare queste pipeline via SLURM invece che in locale, andrà prima sincronizzato `main` dentro `server-pnc` (non fatto in questa sessione, l'utente ha chiesto di lanciare solo in locale).

## Sessione 2026-07-21 (3) — Audit di allineamento docs/config/src/tests + fix bug reali

**Obiettivo**: l'utente ha chiesto di verificare se `.claude/stato_progetto.md`, `docs/`, `config/`, `src/` e `tests/` sono allineati tra loro, e di sistemare tutto quello che non lo è.

**Decisioni prese / concetti discussi**:
- `stato_progetto.md` (nella versione letta a inizio sessione, prima della sessione (2) sopra) descriveva uno stato ampiamente superato: pipeline di analisi come "solo scheletro" (in realtà pienamente implementata), nessun codice di orchestrazione BCBToolKit (in realtà `src/sdc/` + `compute_sdc.py` esistono), nomi di config pre-split (`retrieval.json`/`file_patterns.json` invece di `_local`/`_server`).
- `.claude/CLAUDE.md` stesso (le istruzioni canoniche del progetto) referenziava `docs/project/{overview,tasks,datasets}.md`, una cartella che non esiste più — sostituita da `README.md` (overview/task breakdown) + `docs/guides/datasets.md`. Anche l'affermazione "There is no source code yet" era falsa (`src/` ha 7 sottomoduli, `tests/` 282 test). Corretto.
- Lanciata la suite reale (`pytest tests/ -q`) per la prima volta in questa sessione: **11 test falliti su 282** (259 passed, 12 skipped) — non "227 passing" come dichiarato in `docs/dev/analysis.md`. Causa: refactor recenti (rename di una variabile locale, rename `README.md`→`config.md`, split `retrieval.json`/`file_patterns.json`→`_local`/`_server`) applicati solo al call site più ovvio, mai grep'ati su tutto il repo. Narrativa completa in `docs/debugging/debug_21_07_26.md` §2-4, pattern generale aggiunto in `.claude/lessons_learned.md` #12.
- **Sovrapposizione con sessione parallela**: mentre si indagavano questi bug, una sessione parallela (stesso utente, altro terminale — pattern già noto, vedi sessione atlante sotto) ha committato in autonomia fix **identici** per lo stesso `NameError` su `base_params` e lo stesso rename `README.md`→`config.md` (commit `6cc0add` "bugs fix", `5174ff9`, `4865f65` — quest'ultimo con lo stesso identico testo che questa sessione aveva scritto per `docs/dev/analysis.md`). Nessun conflitto: le due working tree sono convergute sullo stesso contenuto. Il contributo di questa sessione **non coperto** da quei commit paralleli: gli script `sbatch` reali (`jobs/run_retrieve_data.sh`, `run_data_summary.sh`, `run_verify_retrieval.sh`) puntavano ancora a `config/pipelines/retrieval.json`, file non più esistente dopo lo split locale/server di un commit precedente — avrebbero fallito al primo lancio reale con `FileNotFoundError`, nessuno l'aveva notato. Corretti a `retrieval_server.json`, insieme a `README.md`, `docs/dev/retrieval.md`, `docs/guides/retrieval.md`, `src/pipeline/retrieve_data.py` e i due script accessori (`scripts/verify_retrieval.py`/`data_summary.py`).

**File modificati in questa sessione (non ancora committati)**:
- Job/script: `jobs/run_retrieve_data.sh`, `jobs/run_data_summary.sh`, `jobs/run_verify_retrieval.sh` (`retrieval.json`→`retrieval_server.json`), `scripts/verify_retrieval.py`, `scripts/data_summary.py` (docstring/help text)
- Doc: `README.md`, `docs/dev/retrieval.md`, `docs/guides/retrieval.md` (path split locale/server), `.claude/CLAUDE.md` (rimossi riferimenti a `docs/project/` inesistente e all'affermazione "nessun codice sorgente"), `docs/debugging/debug_21_07_26.md` (nuove sezioni §2-4), `.claude/lessons_learned.md` (pattern #12)
- Codice: nessuna modifica propria oltre a quanto già convergente con la sessione parallela (vedi sopra — `dim_reduction.py`/`clustering.py`/`dim_reduction_clustering.py` e 5 file di test, già in commit `6cc0add`)

**Stato dei test**: 270/282 passano, 12 skipped (integration contro mount EBRAIN reale) — 0 failed, verificato rilanciando `pytest tests/ -q` due volte (prima e dopo i fix).

**Prossimo passo esatto**: rivedere e committare le modifiche elencate sopra (`git status` per la lista esatta) — nessuna committata da questa sessione agente. Dopodiché, riprendere dalla mappa "Work In Progress"/"Prossimi Passi" più sotto in questo file (non toccati da questa sessione, restano validi).

## Sessione 2026-07-21 (2) — Riorganizzazione architettura: risultati e tag di sessione per multi-modalità

**Obiettivo**: Riorganizzare la struttura dei salvataggi (dati derivati e risultati) per supportare future modalità (FC, SDC) in parallelo alle matrici lesionali, standardizzando il tracciamento dei parametri di sessione.

**Decisioni prese / concetti discussi**:
- **Directory dei risultati compartimentalizzata**: I risultati dei modelli (dim_reduction, clustering) sono stati spostati da una cartella root condivisa (es. `results/clustering`) a sotto-cartelle specifiche per modalità (es. `results/lesion/clustering`). Questo permetterà di avere pipeline distinte (es. regressione per FC) senza sporcare l'albero delle directory.
- **SESSIONS.md vs RUNS.md**: Il file originario `RUNS.md` dei "matrix builder" in `data/derived/...` è stato formalmente rinominato in `SESSIONS.md` per chiarire la sua funzione: definire i metadati della *coorte/sessione* usata, separandolo dal concetto di `RUNS.md` (che rimane nelle cartelle dei modelli a valle in `results/` per loggare i tuning e gli step). Non si è usato un unico SESSIONS.md globale, ma uno separato per modalità per mantenere l'architettura decouplata.
- **Auto-propagazione del log**: `run_log.py` è stato reso intelligente. Quando un modello a valle scrive il suo log, cerca dinamicamente il file `SESSIONS.md` corretto in `data/derived/*/SESSIONS.md` e copia in automatico l'intestazione della sessione.
- **Configurazioni Parametriche**: Il costruttore di matrice ora accetta un campo `data_modality: lesion` configurato nei `.json`, che viene automaticamente stampato come metadato quando crea una nuova entry in `SESSIONS.md`.

**File modificati/creati**:
- **Codice**: `src/pipeline/build_lesion_matrix.py`, `src/utils/run_log.py`, `src/analysis/build_config.py`, `src/pipeline/compute_sdc.py`
- **Config**: `config/pipelines/build_lesion_matrix.json`, `config/pipelines/clustering.json`, `config/pipelines/dim_reduction.json`, `config/pipelines/dim_reduction_clustering.json` (root puntati a `results/lesion/`)
- **Documentazione**: `docs/dev/analysis.md`, `docs/guides/compute_sdc.md`
- **FS**: Spostate fisicamente le cartelle dei risultati in `results/lesion/` e rinominato `data/derived/lesion_matrix/RUNS.md` -> `SESSIONS.md`.

**Errori trovati e corretti**: 
- Nessun errore, solo refactoring preventivo per la scalabilità del progetto verso FC e SDC.

**Stato dei test**:
- I test non sono stati rilanciati esplicitamente in questa sessione focalizzata su refactoring I/O.

**Prossimo passo esatto**:
- Procedere con l'organizzazione dei commit Git per isolare le modifiche in step logici e versionare il progetto in questo nuovo stato "multi-modalità ready".

## Sessione 2026-07-21 (2) — Integrazione BCBToolKit come pipeline orchestrata (compute_sdc)

**Obiettivo**: integrare BCBToolKit/BCBlib (Stage 1+2, vedi sessioni precedenti su `/data/etosato/tools/`) come pipeline NEMESIS orchestrata su tutti i soggetti di `data/clinical_connectome`, invece di lanci manuali per singolo soggetto.

**Decisioni prese / concetti discussi**:
- Tre modalità separate (`manifest`/`run`/`aggregate`) invece di un comando unico: `bcb-lf-preprocess`/`bcb-lesion-features` non hanno un flag per-soggetto, operano su intere directory (confermato via `--help`). Il parallelismo per soggetto si ottiene quindi costruendo, per ogni task, una staging dir BIDS (symlink) contenente solo i soggetti assegnati a quel task — mai un parametro/flag inventato che questi tool non hanno.
- `manifest.csv` costruito una sola volta (`--mode manifest`) e riletto da ogni task run (stride slice `task_id::task_count`) — copertura completa e disgiunta qualunque sia N, e la stessa lista è condivisa tra tutti i task senza che debbano coordinarsi.
- Check esplicito tra Stage 1 e Stage 2: verifica che il disconnectome sia un NIfTI caricabile con shape 182×218×182 prima di passare il soggetto a Stage 2 — un soggetto che fallisce è escluso e loggato (`_status/<subject_id>.json`), non blocca gli altri soggetti dello stesso task né degli altri task (isolamento per-soggetto, mai un fallimento silenzioso — coerente con `code_standards.md` §0).
- `output_dir` = `<output_root>/<run_name>`, **non datata** (a differenza di `<dd-mm>_<run_name>` usato da `build_lesion_matrix.py`): le tre fasi possono girare a distanza di giorni per via della coda SLURM e devono risolvere sempre alla stessa cartella dal solo config, non dall'istante di esecuzione.
- Parallelismo: SLURM job array (`jobs/run_compute_sdc.sh`, un task per soggetto) in produzione; pool locale con `xargs -P` dimensionato su `nproc/cores_per_subject` per lo script non-SLURM (`scripts/run_compute_sdc_no_slurm.sh`) — quest'ultimo vive deliberatamente in `scripts/` e non `jobs/`, perché non passa da `sbatch` (`jobs/` è riservato alla convenzione sbatch da `CLAUDE.md`).
- `cores_per_subject` nel config deve combaciare con `--cpus-per-task` dell'array SLURM (o essere usato per calcolare il pool locale) — documentato esplicitamente per evitare oversottoscrizione della macchina.

**File modificati/creati**:
- Codice: `src/sdc/{config,manifest,staging,runner,status}.py` (nuovo package), `src/pipeline/compute_sdc.py` (CLI: `manifest`/`run`/`aggregate`, `--dry-run`)
- Config/job: `config/pipelines/compute_sdc.json`, `jobs/run_compute_sdc_manifest.sh`, `jobs/run_compute_sdc.sh` (array), `jobs/run_compute_sdc_aggregate.sh`, `scripts/run_compute_sdc_no_slurm.sh`
- Test: `tests/unit/test_sdc_config.py`, `test_sdc_manifest.py`, `test_sdc_staging_and_check.py` (28 test nuovi)
- Doc: `docs/guides/compute_sdc.md`

**Stato dei test**: 264/271 passano (28 nuovi tutti verdi + 236 preesistenti). 7 fallimenti preesistenti e NON correlati a questo lavoro, non toccati: `tests/integration/test_resolution_counts.py` (6 test) e `test_retrieve_pipeline.py::test_end_to_end_small_real_run` puntano a `config/registry/file_patterns.json`, che nel repo attuale esiste solo nelle varianti `_local`/`_server` — problema preesistente da investigare in una sessione dedicata, non causato né risolto qui.

**Verifica dry-run su dati reali** (richiesta esplicita dell'utente: non testare Stage 1/2 per davvero su tutti i soggetti):
- `--mode manifest` su `clinical_connectome` reale: **1150 soggetti** scoperti (4 dataset, `group_filter=["ST"]`), 0 esclusi.
- Primo tentativo con lo script locale a piena parallelizzazione (pool dimensionato su `nproc=32`/`cores_per_subject=4` = 8 task concorrenti) è fallito per esaurimento risorse della sandbox interattiva (`OpenBLAS pthread_create failed`, limite processi) — **non un bug del codice**: ogni task fallito ha comunque scritto correttamente lo status `failed_stage1_process` per i propri soggetti invece di far crashare l'intero run, confermando che l'isolamento per-soggetto funziona anche sotto stress.
- Retest controllato, un solo soggetto (`--task-id 0 --task-count 1150 --dry-run`): `bcb-lf-preprocess` ha risposto correttamente `"Would preprocess 1 lesion(s)"` per `sub-STUNIPD0001`, confermando che staging/symlink, `bcbtoolkit_path`, `--skip-existing`/`--dry-run` sono cablati correttamente end-to-end sui dati reali.
- Scratch di verifica (`data/derived/sdc/run1/`) ripulito dopo il test (comunque gitignored, `data/*` in `.gitignore`) — il `run_name="run1"` del config è quindi pronto per un run reale senza conflitti con l'output di verifica.

**Nota — attività di auto-commit non spiegata**: durante la sessione, i file nuovi (`src/sdc/*`, `config/pipelines/compute_sdc.json`, `jobs/run_compute_sdc*.sh`, `scripts/run_compute_sdc_no_slurm.sh`) sono comparsi come già committati in git (commit con messaggi informali: "sdc pipeline", "launching", "laucning", "mix") **senza che l'agente abbia eseguito alcun comando git in questa sessione** — nessun hook è configurato in `.claude/settings.json`/`settings.local.json`. Stesso pattern già osservato nella sessione precedente (vedi sotto, "Nota importante — attività parallela nello stesso working tree"): sembra un meccanismo di auto-commit esterno attivo sulla macchina dell'utente, non un'azione di questo agente. Da chiarire con l'utente se non già noto.

**Prossimo passo esatto**: lancio reale in produzione quando l'atlante trattografie completo sarà pronto (il config attuale punta ancora al bundled parziale, 10 soggetti — vedi sessioni precedenti su `/data/etosato/tools/`): `sbatch jobs/run_compute_sdc_manifest.sh` → controllare N soggetti in `manifest.csv` → editare `#SBATCH --array=0-<N-1>` in `jobs/run_compute_sdc.sh` → `sbatch jobs/run_compute_sdc.sh` → `sbatch jobs/run_compute_sdc_aggregate.sh` una volta che l'array è completo (verificare con `sacct -j <array_job_id>`).
## Sessione 2026-07-21 — Atlante combinato Glasser+subcorticale (372 regioni) per il metodo del paper Thiebaut de Schotten 2020

**Obiettivo**: preparare l'atlante di parcellazione usato dal paper Thiebaut de Schotten et al. 2020 prima della loro PCA varimax (360 parcelle corticali MMP/Glasser + 12 regioni subcorticali) per poterlo passare come `atlas_path` a `build_lesion_matrix.py`.

**Decisioni prese / concetti discussi**:
- Verificato `assets/atlases/MNI_Glasser_HCP_v1.0.nii.gz`: 360 label non-zero corrette, ma il range destro reale è **1001–1180**, non 1000–1180 come inizialmente assunto dall'utente (nessun voxel vale 1000 — l'omologo di `L_V1=1` è `R_V1=1001`).
- Letto il paper (`assets/papers/Thiebaut de Schotten .../markdown/_full.md`, sezione "Data compression"): confermate le 12 regioni subcorticali (talamo, caudato, ippocampo, pallido, putamen, amigdala, bilaterali) ma il paper le dice "defined manually" — **nessun atlante sorgente citato**. Scelto Harvard-Oxford subcortical (`HarvardOxford-sub-maxprob-thr25-2mm.nii.gz`) come sostituto pratico documentato, non riproduzione fedele — va segnalato come limite se/quando si scrive la metodologia in `docs/methods/`.
- Un dizionario di indici Harvard-Oxford proposto da un agente esterno (non di questa sessione) aveva un **bug off-by-one** su `R_Hippocampus`/`R_Amygdala` (offset +11 uniforme assunto per tutte le 6 strutture, valido solo per Thalamus/Caudate/Putamen/Pallidum — rotto dal `Brain-Stem`, struttura non bilaterale, che sfalsa la numerazione). Corretto leggendo `/data/sw/fsl/data/atlases/HarvardOxford-Subcortical.xml` (fonte autoritativa) e confermato sui dati reali (dimensione dei cluster: ippocampo 700 voxel > amigdala 366 voxel). Vedi `docs/debugging/debug_21_07_26.md` e `.claude/lessons_learned.md` pattern #11.
- Nuovo modulo `src/atlases/` (nuovo layer, non incastrabile in `retrieval`/`features` esistenti): numerazione output delle 12 subcorticali continua la convenzione di Glasser (sinistra 181–186, destra 1181–1186, nessuna collisione con 1–180/1001–1180). Politica sovrapposizioni cortex/subcortex dopo il resampling (Harvard-Oxford 2mm → griglia Glasser 1mm, nearest-neighbor): **cortex vince** (MMP è la parcellazione primaria nel paper), loggato non silenzioso (8791 voxel di overlap nel run reale).

**File modificati/creati** (già committati dall'utente stesso in `19191f9` "Add combined atlas build pipeline", non da questa sessione agente):
- Codice: `src/atlases/{__init__,combine,config}.py`, `src/pipeline/build_combined_atlas.py`
- Config/job: `config/pipelines/build_combined_atlas.json`, `jobs/run_build_combined_atlas.sh`
- Test: `tests/unit/test_combine_atlas.py` (8 test, incluso regression test esplicito sul bug off-by-one), `tests/integration/test_build_combined_atlas_pipeline.py` (E2E sui file reali)
- Doc: `docs/debugging/debug_21_07_26.md` (nuovo), `.claude/lessons_learned.md` (pattern #11), `README.md`, `assets/atlases/README.md` (sezione "Derived / combined atlases") — la sezione aggiunta in `docs/guides/analysis.md` §0 è stata poi riorganizzata dall'utente in commit successivi (vedi nota sotto)
- Output reale generato (non in git, `.nii.gz` gitignored): `assets/atlases/glasser_hcp_harvardoxford_subcortical_372.nii.gz` + `..._labels.csv` (quest'ultimo committato)

**Stato dei test**: 10/10 passano (`tests/unit/test_combine_atlas.py` + `tests/integration/test_build_combined_atlas_pipeline.py`), suite completa non rilanciata (per preferenza nota dell'utente, vedi memoria `feedback_test_pace`).

**Nota importante — attività parallela nello stesso working tree**: durante questa sessione sono comparse ed è stato committato molto lavoro non fatto da questo agente (probabile altra sessione Claude/terminale in parallelo, poi confermato essere l'utente stesso via commit `git log`): refactor `reference_dataset`→`reference_template_path` in `src/analysis/`+`src/features/lesion.py`, nuovi atlanti scaricati (Schaefer, Tian, Buckner) in `assets/atlases/`, notebook rifatto (`notebooks/dataset_exploration.ipynb` sostituisce `metadata_analysis.ipynb`), un primo run reale di `build_lesion_matrix.py` (**voxel-wise, non parcellato — non ha ancora usato l'atlante combinato**, 1150 soggetti × 254865 feature, commit "first run"). **In corso, non committato**: `docs/guides/analysis.md` è stato cancellato e diviso in `docs/guides/atlas_building.md` + `docs/guides/matrix_building.md` — riorganizzazione dell'utente, non toccare finché non è lui a dire che è conclusa.

**Prossimo passo esatto**: per usare davvero l'atlante a 372 regioni, editare `config/pipelines/build_lesion_matrix.json` (oggi resettato a `parcellate: false, atlas_path: null`) impostando `"parcellate": true`, `"atlas_path": "assets/atlases/glasser_hcp_harvardoxford_subcortical_372.nii.gz"`, `"parcel_aggregation": "fraction_lesioned"` (e un `run_name` diverso da `run1` per non confliggere con l'output voxel-wise già scritto in `data/derived/lesion_matrix/21-07_run1`), poi `sbatch jobs/run_build_lesion_matrix.sh`.

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

Il refactor dello schema di retrieval verso vocabolario BIDS (config, codice, test, doc, run reali) è stato **committato** (10 commit separati per categoria). Da lì, in questa sessione, `config/registry/file_patterns.json` è stato modificato ulteriormente in working tree (non ancora committato): rimosso `feature`, provata e rimossa `lesion/raw` — il file ora ha solo `lesion/manual_masks`. I 4 CSV di `data_summary` (ora in `summaries/datasets/`, senza sottocartella `<project>` — spostati fuori da `summaries/data_retrieval/` in una sessione successiva, `scripts/data_summary.py` ha oggi un `REPORTS_ROOT` proprio invece di importarlo da `retrieve_data.py`) sono stati rigenerati (`sbatch jobs/run_data_summary.sh`) mentre `raw` era ancora nel registro, quindi contengono una colonna `lesion/raw/anat/lesion_roi` ormai stale rispetto al registro attuale — vanno rigenerati un'altra volta prima di committare, per riflettere lo stato finale (solo `manual_masks`).

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
