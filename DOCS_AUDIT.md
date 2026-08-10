# Audit documentazione `docs/` — file temporaneo di lavoro

Non fa parte della documentazione stabile del progetto — da cancellare a fine revisione.
Per ogni file: cosa è confermato corretto, cosa è obsoleto/errato (con riferimento file:riga sia nel `.md` sia nel codice reale), cosa non è verificabile da questo Mac.

---

## `docs/guides/retrieval.md` — ✅ FATTO

## `docs/guides/datasets.md` — ✅ FATTO

---

## `docs/guides/atlas_building.md` — ✅ FATTO 

---

## `docs/guides/matrix_building.md` — ✅ FATTO
(10/08: aggiunto `manifest.json` all'elenco output; rimossa la nota fuorviante su `build_lesion_matrix_local.json`, sostituita con un avviso generale di controllare/aggiornare il config prima di ogni run, su indicazione dell'utente — il punto 3, sullo snapshot config non ancora lanciato, non è un problema da correggere in sé, solo un promemoria)

---

## `docs/guides/fc_matrix_building.md` — ✅ FATTO. 
(10/08: righe 13 e 60 riscritte per riflettere che la soglia di esclusione paziente è una decisione chiusa — utente ha confermato che non la implementerà — non più presentata come "da decidere"; resto del file già confermato corretto, nessun'altra discrepanza)

---

## `docs/guides/compute_sdc.md` — ✅ FATTO  
(10/08: comando corretto a `jobs/run_compute_sdc_no_slurm.sh` invece di `scripts/...`, aggiornato anche il commento header dello script stesso che diceva la stessa cosa sbagliata; schema `runs.csv` corretto a `session, id, timestamp, params, output, notes`. Non verificabile da qui, richiede cluster/bcblib: conteggio 15 atlanti EBRAINS, comportamento Stage 1/2 reale)

---

## `docs/guides/dim_reduction.md` — ✅ FATTO 
(10/08: sezione runs.csv riscritta per descrivere correttamente i due file separati `runs.csv`/`runs_tuning.csv` con schema `session, id, timestamp, params, output, notes`. Nota collaterale non toccata, fuori scope docs/: anche i docstring interni di `src/pipeline/dim_reduction.py` e `src/utils/run_log.py` hanno la stessa descrizione obsoleta)

---

## `docs/guides/clustering.md` — ✅ FATTO 
(10/08: riga 101 corretta per descrivere i due file separati `runs.csv`/`runs_tuning.csv`, stesso fix di `dim_reduction.md`. Resto del file già confermato corretto in dettaglio, incluso il comportamento noto/documentato di `cluster_plot.png` che disegna solo le prime 2 colonne)

---

## `docs/guides/dim_reduction_clustering.md` — ✅ FATTO 
(10/08: rimosso il riferimento residuo a "k-distance" tra le diagnosi di fine-tuning, feature rimossa insieme a DBSCAN→HDBSCAN in sessione 2026-07-29. La descrizione di `runs.csv`/`runs_tuning.csv` era già corretta in questo file - è servita da riferimento per correggere `dim_reduction.md`/`clustering.md`)

---

## `docs/dev/retrieval.md`

File molto denso e per lo più eccellente (spiega bene *perché*, non solo *cosa*) — ma contiene l'errore più significativo trovato finora nell'intero audit, **internamente incoerente con se stesso**.

**✅ Confermato corretto**
- `KNOWN_OBJECTS = ("lesion", "feature")`, `_OBJECTS_REQUIRING_PIPELINE`/`_OBJECTS_FORBIDDING_PIPELINE`, profondità variabile 3 vs 2 livelli — confermato in `src/retrieval/config.py`.
- `KNOWN_GROUPS`: qui la doc elenca correttamente **tutti e 4** i gruppi (`ST, HC, PD, GM`, riga 228) — a differenza di `docs/guides/retrieval.md` che ne omette 2 (vedi sopra). Questo file è la fonte corretta.
- Layout output pipeline-first, `output_layout.local_relative_path`/`local_dataset_root` — combacia esattamente col codice (già verificato per `docs/guides/retrieval.md`).
- Percorso `assets/dataset_summaries/data_summary__<dataset>.csv`, non timestampato, non annidato per progetto — confermato sui file reali (`ls assets/dataset_summaries/`).
- `_reject_duplicate_retrieve_items`, `RetrieveItem.__post_init__` con `if/elif/else: raise` — confermato in `config.py`.
- Tabella STOP/WARNING/ERROR/FATAL — coerente con `retrieve_data.py` (già verificato in dettaglio per la guida utente).

**⚠️ Errore maggiore — conteggio/nomi atlanti FC-pearson, il documento si contraddiceva da solo — RISOLTO il 10/08**
Il registro reale (`config/registry/file_patterns_{server,local}.json`, contato a mano) ha **12 template Yan-based**: `Yan{100,200,300,400}TianS{1,2,3}Buckner7N`.
- Righe 91, 128, 346 descrivevano **15 template Glasser+Schaefer-based**, un registro mai esistito sul disco reale (nessuna traccia di "Glasser"/"Schaefer" in `file_patterns_server.json`; via `git log` il registro usa Yan almeno dal 21/07, mai cambiato da allora). Righe 275, 304 dicevano invece correttamente "12", senza nominare gli atlanti — il documento era quindi incoerente al proprio interno (3 punti dicevano 15/Glasser-Schaefer, 2 dicevano 12).
- **Fix applicato**, su indicazione esplicita dell'utente di non "bloccare" di nuovo un numero/nome specifico che potrebbe ricambiare in futuro: le 3 righe sbagliate sono state corrette per riflettere lo stato Yan-based di oggi, ma **formulate come puntatori al registro** ("vedi `file_patterns_server.json` per la lista corrente, questo insieme è già cambiato una volta ed è previsto possa ricambiare"), non come un nuovo conteggio fisso destinato a ridiventare stale alla prossima modifica dell'atlante.

**⚠️ Sezione "Known follow-up, not yet done" (riga 338) — completamente superata — RISOLTO il 10/08**
Entrambi i problemi descritti come "non ancora sistemati" erano **già risolti** nel codice (verificato su `tests/integration/test_resolution_counts.py` reale: `FILE_PATTERNS_PATH` punta già a `file_patterns_server.json`, e il test FC-pearson deriva i template dinamicamente dal registro invece di hardcodare nomi/conteggi). **Fix applicato**: sezione riscritta per documentare che è stata risolta, invece di restare descritta come lavoro ancora da fare.

**⚠️ Riga 7 — stesso errore già trovato nella guida utente — RISOLTO il 10/08**: *"`_local.json` (Windows path convention, for a laptop-mounted copy)"* era falso. **Fix applicato**: riformulato per non affermare "Windows", e per riflettere la decisione dell'utente che i due `retrieval_*.json` restano allineati per contenuto (stesso `datasets`/`group_filter`/`retrieve`), differendo solo nel puntatore al registro — coerente con l'allineamento di `retrieval_server.json` applicato in `docs/guides/retrieval.md`.

**❓ Non verificabile da qui / dato ambiguo (non ancora toccato, in attesa di nuova evidenza)**
- Riga 9: *"176/196 subject folders actually populated"* per WashU `features/` alla sorgente — la copia locale ha **225** cartelle `sub-*` sotto `features/` (verificato `ls`), un numero diverso da entrambi quelli citati. Non è una prova di errore (la copia locale non è necessariamente uno snapshot identico all'istante in cui questa cifra fu misurata, ed EBRAIN è "attivamente curato" per stessa ammissione della doc, riga 336) ma il numero citato non è più riscontrabile oggi con i dati disponibili — da ri-misurare se questa cifra serve ancora a qualcosa.

---

## `docs/dev/analysis.md`

File enorme (321 righe) e per la maggior parte di qualità eccellente — molto probabilmente il documento più denso e accurato dell'intero audit finora. Ma la sezione "Status" iniziale e la sezione `run_log.py` contengono errori chiari e verificabili, in netto contrasto con la cura del resto del file.

**✅ Confermato corretto (verifica estesa)**
- `REDUCTION_METHODS`/`CLUSTERING_METHODS` (5 e 5, nomi esatti) — confermato.
- `params["metric"]` di produzione: `umap` → `"jaccard"`, `tsne` → `"euclidean"` — confermato esattamente su `config/registry/params_reduction.json` reale.
- `PARCEL_AGGREGATIONS` con solo `"fraction_lesioned"` — confermato (già verificato per `matrix_building.md`).
- I 2 bug reali di `nilearn.NiftiLabelsMasker` (overflow `uint8`, parcel scomparso invece di leggere 0) — coerenti con `lessons_learned.md` #13 e `debug_23_07_26.md`, verificabili nel codice.
- Struttura output/nomi (`embeddings_grid_*.png`, `consensus_suggestions.md`, `CONSENSUS_ELIGIBLE_METHODS = {kmeans, gmm, spectral}`, `STANDALONE_DIAGNOSTIC_METHODS = {agglomerative, spectral}`, rimozione di `compute_k_distance`/`plot_k_distance`) — tutto confermato nel codice reale già ispezionato per i file precedenti.
- `data/SESSIONS.md` come unico path sotto `data/` non ignorato da git (`!data/SESSIONS.md`) — verificabile in `.gitignore`, coerente col resto del progetto.

**⚠️ Errore confermato #1 — riga 7, sezione "Status" (proprio quella che dichiara di essere sempre aggiornata)**
*"`feature` not currently registered in `config/registry/file_patterns_local.json`/`file_patterns_server.json`"* — **falso**: verificato che entrambi i file hanno oggi `{"lesion": ..., "feature": ...}` come chiavi di primo livello, con `feature.func.FC-pearson`/`motion`/`outliers` pienamente popolati (12 template Yan-based). Ironico dato che l'introduzione del file dichiara esplicitamente *"This file documents what is actually implemented today... not a restatement of the plan"*.

**⚠️ Errore confermato #2 — schema `runs.csv`, ripetuto 3 volte nello stesso file (righe 110, 211, 220)**
Il file descrive esplicitamente e più volte, con motivazione dettagliata, che produzione e tuning finiscono **nello stesso file** `<output_root>/<method>/runs.csv`, distinti solo da una colonna `run_type` (*"the point is seeing... in one place, not two separate histories to cross-reference"*, riga 110). Questo **contraddice il codice reale** già verificato (`src/utils/run_log.py`: `file_name = "runs.csv" if run_type == "production" else "runs_tuning.csv"`, più gli header reali `session,id,timestamp,params,output,notes` senza `run_id`/`run_type` su `results/lesion/dim_reduction/*/runs.csv`). È lo stesso errore già trovato in `docs/guides/dim_reduction.md`/`docs/guides/clustering.md`, ma qui è più esteso: l'intera sezione "`src/utils/run_log.py`" (righe 106-114) descrive un design (`FIELDNAMES` include `run_id`/`run_type`, un solo file) che il codice reale ha da tempo sostituito con lo split `runs.csv`/`runs_tuning.csv` — `docs/guides/dim_reduction_clustering.md` (verificato sopra) ha invece la descrizione corretta.

**⚠️ Righe 318-319 — framing "non ancora deciso" doppiamente stale, stesso pattern già trovato in `fc_matrix_building.md`**
*"A per-subject exclusion threshold... not yet run for real; only synthetic/small-sample data so far"*: falso su entrambi i punti.
1. `mask_fc.py` **è stato eseguito su dati reali** (169 soggetti WashU reali, `mask_summary.csv` con numeri reali — confermato già nel file precedente e in `stato_progetto.md` sessione 2026-07-25).
2. La decisione sulla soglia di esclusione è stata **chiusa esplicitamente** in sessione 2026-07-27 ("non si esclude nessun paziente, nessuna soglia implementata... non è un lavoro rimasto da fare, è chiusa") — non è più "not yet decided".

**❓ Non verificabile da qui**: dettagli implementativi minori (es. formule esatte di `compute_monti_stability`/RSC) — plausibili e ben referenziati alla letteratura (`papers/Zanola et al - 2026`), non riverificati matematicamente riga per riga.

---

---

## `docs/methods/dimensionality_reduction.md` — ✅ FATTO (10/08: aggiunta nota all'inizio della sezione `pca_varimax` che segnala non essere raggiungibile da CLI oggi, pur essendo implementato/testato — stessa lacuna trasversale già notata in `dim_reduction_tuning_guide.md`/`docs/dev/analysis.md`/`docs/guides/dim_reduction.md`/`docs/guides/dim_reduction_clustering.md`, questi ultimi 3 non ancora corretti)

---

## `docs/methods/clustering.md` — ✅ FATTO (10/08: riga 7, link morto a `docs/guides/analysis.md` inesistente, sostituito con `docs/guides/clustering.md`/`docs/guides/dim_reduction_clustering.md`)

---

## `docs/knowledge/fc_lesion_masking.md` — ✅ FATTO (10/08: riga 82 aggiornata — tutte e 12 le combinazioni di atlante sono state effettivamente girate sui dati reali, masking e matrice finale, non solo `Yan200TianS2Buckner7N`)

---

## `docs/knowledge/Siegel2016_Reproduction.md` — 🗑️ ELIMINATO il 10/08 su richiesta esplicita dell'utente (non solo corretto — il file non esiste più). Rimosso anche il riferimento morto a questo file in `docs/guides/datasets.md` (riga 35).

---

## `docs/knowledge/dim_reduction_tuning_guide.md` — ✅ FATTO (10/08: aggiunta nota inline sulla stessa lacuna `pca_varimax` di cui sopra)

---

## `docs/knowledge/clustering_tuning_guide.md` — ✅ FATTO — nessuna discrepanza era stata trovata, nessuna modifica necessaria

---

# `docs/debugging/` — narrativa storica, criterio di verifica diverso

Questi file non descrivono lo stato attuale del codice — sono report di sessioni di debug passate. "Vero" qui significa: coerente con `.claude/lessons_learned.md` (che li cita come fonte), coerente con la storia git reale (funzioni/nomi citati devono essere esistiti davvero, anche se poi rimossi/rinominati), e internamente coerente — **non** deve corrispondere al codice di oggi, che nel frattempo è stato ampiamente rifattorizzato (es. `space`/`modality` di questi vecchi report sono diventati `datatype`/`suffix`, `native()`/`mni_mask()` sono spariti in favore di `resolve()`, la sezione "Ambiguous" del report è stata rimossa del tutto). Non mi aspetto quindi di trovare "bug nel codice attuale" qui — l'obiettivo è verificare che il racconto di ciò che successe sia fedele, non che descriva l'oggi.

## `docs/debugging/debug_09_07_26.md`

**✅ Confermato corretto**
- **Tutte e 7 le categorie di bug (§1-7) hanno un riscontro esatto in `.claude/lessons_learned.md`** (pattern #1-7, ciascuno con `debug_09_07_26.md` citato come fonte) — verificato incrociando testo per testo: descrizione dell'errore, criticità, e persino il dettaglio "2 istanze nella stessa sessione" per il pattern #5 (duplicati) combaciano esattamente tra i due documenti.
- **Grounding storico reale**: cercato con `git log --all -S"mni_mask"` e `-S"_parse_retrieve_item"` (pickaxe search, trova i commit che hanno introdotto/rimosso quella stringa) — entrambi i nomi di funzione citati nel report **sono realmente esistiti** nel codice in quel periodo, non inventati a posteriori. Coerente con l'affermazione della doc che oggi quelle funzioni non esistono più (sostituite da `resolve()` con la convenzione `datatype`/`suffix`).
- La sezione "Ambiguous" del report che il fix di §3 introduce ("si segnala esplicitamente l'ambiguità... mai risolta in silenzio") è coerente con quanto trovato in `docs/dev/retrieval.md` — che oggi dice esplicitamente *"There is no 'Ambiguous' category anymore"* — quindi quella sezione è stata introdotta qui e poi rimossa in un refactor successivo, non una descrizione ora falsa ma una fase intermedia reale della storia del codice.

**⚠️ Discrepanza reale (minore)**
- **Riga 100 — riferimento a un file che non esiste**: *"Skill generale estratta da queste categorie: `silent-failure-audit` (vedi `~/.claude/skills/silent-failure-audit/SKILL.md`)"* — verificato `ls ~/.claude/skills/`: quella cartella/skill **non esiste** oggi (il contenuto reale è `README.md`, `convert_paper`, `export_full_md`, `git_committer.md`, `paper_downloader` — nessuna traccia di `silent-failure-audit`). O la skill non è mai stata effettivamente creata dopo questa sessione, o è stata rimossa/rinominata in seguito senza aggiornare questo riferimento.

**❓ Non verificabile da qui**: i dettagli specifici del fix (es. il codice esatto di `RetrieveItem.__post_init__` di allora) — il commit esatto di quella sessione non è stato identificato/isolato, solo confermata l'esistenza storica dei nomi citati.

---
