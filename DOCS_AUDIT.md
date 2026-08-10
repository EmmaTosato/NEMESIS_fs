# Audit documentazione `docs/` — file temporaneo di lavoro

Non fa parte della documentazione stabile del progetto — da cancellare a fine revisione.
Per ogni file: cosa è confermato corretto, cosa è obsoleto/errato (con riferimento file:riga sia nel `.md` sia nel codice reale), cosa non è verificabile da questo Mac.

---

## `docs/guides/retrieval.md` — ✅ FATTO

## `docs/guides/datasets.md` — ✅ FATTO

---

## `docs/guides/atlas_building.md` — ✅ FATTO 

---

## `docs/guides/matrix_building.md` — ✅ FATTO (10/08: aggiunto `manifest.json` all'elenco output; rimossa la nota fuorviante su `build_lesion_matrix_local.json`, sostituita con un avviso generale di controllare/aggiornare il config prima di ogni run, su indicazione dell'utente — il punto 3, sullo snapshot config non ancora lanciato, non è un problema da correggere in sé, solo un promemoria)

---

## `docs/guides/fc_matrix_building.md` — ✅ FATTO (10/08: righe 13 e 60 riscritte per riflettere che la soglia di esclusione paziente è una decisione chiusa — utente ha confermato che non la implementerà — non più presentata come "da decidere"; resto del file già confermato corretto, nessun'altra discrepanza)

---

## `docs/guides/compute_sdc.md` — ✅ FATTO (10/08: comando corretto a `jobs/run_compute_sdc_no_slurm.sh` invece di `scripts/...`, aggiornato anche il commento header dello script stesso che diceva la stessa cosa sbagliata; schema `runs.csv` corretto a `session, id, timestamp, params, output, notes`. Non verificabile da qui, richiede cluster/bcblib: conteggio 15 atlanti EBRAINS, comportamento Stage 1/2 reale)

---

## `docs/guides/dim_reduction.md` — ✅ FATTO (10/08: sezione runs.csv riscritta per descrivere correttamente i due file separati `runs.csv`/`runs_tuning.csv` con schema `session, id, timestamp, params, output, notes`. Nota collaterale non toccata, fuori scope docs/: anche i docstring interni di `src/pipeline/dim_reduction.py` e `src/utils/run_log.py` hanno la stessa descrizione obsoleta)

---

## `docs/guides/clustering.md` — ✅ FATTO (10/08: riga 101 corretta per descrivere i due file separati `runs.csv`/`runs_tuning.csv`, stesso fix di `dim_reduction.md`. Resto del file già confermato corretto in dettaglio, incluso il comportamento noto/documentato di `cluster_plot.png` che disegna solo le prime 2 colonne)

---

## `docs/guides/dim_reduction_clustering.md` — ✅ FATTO (10/08: rimosso il riferimento residuo a "k-distance" tra le diagnosi di fine-tuning, feature rimossa insieme a DBSCAN→HDBSCAN in sessione 2026-07-29. La descrizione di `runs.csv`/`runs_tuning.csv` era già corretta in questo file - è servita da riferimento per correggere `dim_reduction.md`/`clustering.md`)

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

## `docs/dev/design_patterns.md`

File breve, concettuale, e **interamente confermato corretto** — nessuna discrepanza trovata.

**✅ Confermato corretto**
- Pattern Strategy/Registry (`REDUCTION_METHODS`/`CLUSTERING_METHODS`/`PARCEL_AGGREGATIONS` come `dict[str, Callable]`) — confermato ripetutamente nei file precedenti.
- Boundary validation (`resample_interpolation` contro l'insieme esatto accettato da nilearn, `binarize_threshold` in `[0.0, 1.0]`) — confermato in `src/analysis/build_config.py`.
- Atomic write: *"`load_matrix` ... treats 'no manifest.json' as 'this artifact was never successfully built'"* — confermato esattamente: `load_matrix` (`src/utils/artifacts.py`) solleva `FileNotFoundError` se `manifest.json` è assente.
- Layered architecture: *"`src/analysis/build_config.py` importing `PARCEL_AGGREGATIONS` from `src/features/lesion.py` è una dipendenza discendente legale"* — confermato: `from src.features.lesion import PARCEL_AGGREGATIONS` è realmente presente in `build_config.py`.

**❓ Non verificabile da qui**: nessuno.

---

## `docs/methods/dimensionality_reduction.md`

**✅ Confermato corretto**
- `metric` di produzione: `umap`→`jaccard`, `tsne`→`euclidean` — confermato (già verificato più volte).
- `regress_out_volume`: incompatibile con jaccard/dice, oggi "no-op" perché `dim_reduction.json`/`dim_reduction_clustering.json` hanno entrambi `"regress_out_volume": false` — confermato sui config reali.
- `pca_varimax_embed`: richiede `n_components`/`rotation_max_iter` in `params`, solleva `ValueError` se mancanti o se `n_components < 2` — confermato esattamente in `src/analysis/reduction.py`.
- `pacmap`: parametri `n_neighbors`/`MN_ratio`/`FP_ratio` — confermato sul registro reale (`config/registry/params_reduction.json`).
- `binary_pairwise_distance` (Jaccard/Dice via `X @ X.T`, ~19 minuti→pochi secondi) — coerente con quanto già verificato per `docs/dev/analysis.md`.

**⚠️ Scoperta significativa (non un errore di questo file specifico, ma una lacuna che questo file — insieme ad altri 4 — non segnala)**
Il documento presenta `pca_varimax` come uno dei 5 metodi pienamente disponibili, con tanto di guida al fine-tuning (`n_components` vs. varianza spiegata, righe 44-53). **Ma `pca_varimax` non è più configurabile oggi**: `config/registry/params_reduction.json` (il file che sia questo documento sia `docs/guides/dim_reduction.md` indicano come "l'unico posto" da modificare) **non ha più una entry `pca_varimax`** — rimossa nel commit `b6d0434` (21/07/26, "feat: add interactive plotly embeddings, param tags, and replotting script") durante un riordino del file, mai più reintrodotta. Verificato: `python -c "json.load(open('config/registry/params_reduction.json')).keys()"` → `['tsne', 'umap', 'pacmap', 'pca']`, nessun `pca_varimax`. Se qualcuno oggi impostasse `"reduction_method": "pca_varimax"` in `dim_reduction.json`, `load_method_params`/`load_tuning_grid` solleverebbero `ValueError` (metodo non registrato).
- **Il codice supporta ancora pienamente il metodo** (`REDUCTION_METHODS["pca_varimax"] = pca_varimax_embed` esiste in `src/analysis/reduction.py`, coperto da test unitari — `tests/unit/test_reduction.py`/`test_tuning.py` — che però costruiscono i `params` a mano, mai leggendo `params_reduction.json`, motivo per cui la suite non ha mai rilevato la lacuna).
- **La stessa incoerenza appare, verificato con `grep -rl pca_varimax`, in altri 4 documenti**: `docs/dev/analysis.md` (sezione "Status", lo elenca tra i `REDUCTION_METHODS` "oggi"), `docs/guides/dim_reduction.md`, `docs/guides/dim_reduction_clustering.md`, `docs/knowledge/dim_reduction_tuning_guide.md` — nessuno dei quali segnala che il metodo, pur implementato e testato, non è raggiungibile da CLI/config reale al momento. Non ancora corretto retroattivamente nei report di quei file sopra in questo audit — segnalato qui come scoperta trasversale, valida per tutti loro.

**❓ Non verificabile da qui**: contenuto puramente concettuale (differenze PCA/t-SNE/UMAP/PaCMAP) — corretto per quanto di dominio pubblico, non fact-checkabile riga per riga contro il codice.

---

## `docs/methods/clustering.md`

**✅ Confermato corretto**
- Default reali del registro: `agglomerative.linkage: "ward"`, `hdbscan.min_cluster_size: 5`, `spectral.affinity: "nearest_neighbors"` — tutti confermati esattamente su `config/registry/params_clustering.json`.
- `CONSENSUS_ELIGIBLE_METHODS = {kmeans, gmm, spectral}`, colonne `rsc_eigengap`/`monti_stability`, `consensus_suggestions.md` — confermato (già verificato per `docs/guides/clustering.md`/`docs/dev/analysis.md`).
- HDBSCAN senza diagnostica standalone, `-1` riportato separatamente da "Clusters found" — confermato nel codice.
- Spiegazioni concettuali di ciascun metodo (KMeans/Agglomerative/GMM/HDBSCAN/Spectral) — corrette per quanto di dominio pubblico/letteratura citata (Campello, Moulavi & Sander 2013 per HDBSCAN, Tshimanga et al. 2025/Zanola et al. 2026/Monti et al. 2003/Șenbabaoğlu et al. 2014 per il consensus clustering).

**⚠️ Discrepanza reale**
- **Riga 7 — riferimento a un file inesistente**: *"...see `docs/guides/analysis.md` for when each script applies"*. Questo file **non esiste** (`docs/guides/` non ha alcun `analysis.md` — verificato `ls`); la guida più vicina per lo scopo descritto è probabilmente `docs/guides/dim_reduction_clustering.md` o una combinazione di `dim_reduction.md`+`clustering.md`. Link morto.

**❓ Non verificabile da qui**: nessuno oltre a quanto sopra.

---

## `docs/knowledge/fc_lesion_masking.md`

**✅ Confermato corretto**
- `find_compromised_nodes`: confronto stretto `parcel_coverage < min_coverage` — confermato carattere per carattere in `src/features/functional.py`.
- `min_coverage` obbligatorio, validato in `[0.0, 1.0]`, nessun default implicito — confermato (`_require_float_in_range(raw, "min_coverage", 0.0, 1.0)` in `build_config.py`).
- "239 nodi, 28.441 connessioni uniche" per `Yan200TianS2Buckner7N` — confermato (`edge_names.npy` reale ha shape 28441, verificato nel file `fc_matrix_building.md` sopra).
- "mediana 1, media 3.9" nodi compromessi su 169 pazienti — coerente con `stato_progetto.md` sessione 2026-07-25 (stessa cifra).
- Notazione `NodoA__NodoB`, doppio masker `NiftiLabelsMasker`, NaN non azzerato, verifica allineamento etichette prima di impilare — tutto confermato nei file precedenti.

**⚠️ Discrepanza reale — riga 82, stessa area della sezione "Non ancora deciso" già trovata stale altrove**
*"12 combinazioni di atlante sono disponibili... oggi solo `Yan200TianS2Buckner7N` è stata validata/usata sui dati reali"* — **non più vero**: verificato che `data/derived/features/masked_fc/` contiene oggi **tutte e 12** le combinazioni Yan-based, ciascuna con **169 CSV mascherati reali** (non solo cartelle vuote/scaffolding) — il lavoro "ripetere su le altre 11 combinazioni" indicato come prossimo passo in `stato_progetto.md` (sessione 2026-07-25) risulta completato, ma questo documento di teoria non è stato aggiornato di conseguenza.

**❓ Non verificabile da qui**: nessuno oltre a quanto sopra.

---

## `docs/knowledge/Siegel2016_Reproduction.md`

Documento diverso dagli altri: è per lo più una **sintesi fedele di un paper esterno** (Siegel et al. 2016), non una descrizione del codice NEMESIS — la maggior parte del contenuto non è "vera/falsa" rispetto al nostro codebase, ma rispetto al testo del paper stesso. Ho fatto uno **spot-check di fedeltà** sulla prima sezione (Results, "Abnormal FC Patterns") contro il markdown reale del paper, poi verificato i 2 punti dove il documento tocca davvero il progetto NEMESIS.

**✅ Fedeltà al paper — spot-check positivo**
Confrontato riga per riga contro `papers/nemesis/Siegel et al - 2016 - .../Siegel et al - 2016.md` reale: **132 pazienti + 31 controlli** iniziali, **21 esclusi per hemodynamic lag**, **11 pazienti + 4 controlli esclusi per motion**, campione finale **100 pazienti/27 controlli**, **324 ROI**/**13 reti** (Gordon et al.), **t=4.26, P=10⁻⁴** sul t-test omotopico, **P=0.26** per l'effetto motion nell'ANOVA — **ogni singolo numero verificato combacia esattamente** con il testo del paper. Alta fiducia che il resto del documento (non riverificato riga per riga per limiti di tempo, ~250 righe restanti) sia altrettanto fedele, data la densità e precisione di questi primi riscontri. Il documento segnala inoltre onestamente 3 "incongruenze di lettura" trovate nel paper stesso (L1 vs formula L2 nell'MTL, "eight" vs "five" domini, "seven models" vs 8 modelli attesi) — non verificate contro il paper (richiederebbe leggere le sezioni esatte citate), ma presentate con onestà come letture aperte, non spacciate per certezze.

**⚠️ Discrepanza reale — riga 3, citazione del path del paper obsoleta**
*"Fonte: `papers/Siegel et al - 2016 - .../markdown/_full.md`"* — questo percorso **non esiste più**: la cartella `papers/` è stata riorganizzata (verificato `ls papers/`: oggi solo `papers/nemesis/` e `papers/related/`, nessun paper direttamente sotto `papers/`) e il file estratto non si chiama più `markdown/_full.md` ma `<Nome Paper>.md` direttamente nella cartella del paper (verificato: `papers/nemesis/Siegel et al - 2016 - .../Siegel et al - 2016.md`, senza sottocartella `markdown/`). Coerente con una serie di commit recenti (`2026-08-05/06/07`, "papers: fact-check and correct all 19 nemesis paper summaries", "papers reorganization") successivi alla stesura di questo documento — e nota bene, questa stessa convenzione (`markdown/_full.md`) è quella descritta come attuale anche in `.claude/CLAUDE.md` stesso, che quindi risulterebbe anch'esso stale su questo punto specifico (fuori scope di questo audit, che riguarda solo `docs/`, ma segnalato per completezza).

**⚠️ Discrepanza reale, più rilevante — riga 259, sezione "Vincolo aperto per una riproduzione NEMESIS"**
*"Da `docs/guides/datasets.md`: **WashU (l'unico dataset con FC oggi) non ha `participants.tsv`/dati clinici** nel formato disponibile"* — **falso oggi, e falso anche nel documento che cita**: `docs/guides/datasets.md` (verificato per intero in questo stesso audit, sezione sopra) dice oggi l'esatto contrario — *"È fornito per tutti e 4 i dataset, inclusa **WashU** (verificato 27/07: ... 319 soggetti — nota precedente su questa pagina, che lo dava assente per WashU, era stale/errata)"* — e riporta persino le percentuali di copertura per singolo punteggio clinico (NIHSS 73%, ARAT 98%, ecc.), tutte **verificate su dati reali** in questo stesso audit. Il file `data/clinical_connectome/derivatives/UNIPD/WashU/participants.tsv` esiste realmente con 319 righe. Questo documento sta quindi citando una versione ormai superata di `docs/guides/datasets.md` (probabilmente la "nota precedente... stale/errata" a cui quel file stesso fa riferimento) — il "vincolo aperto" descritto qui non è più un vincolo reale nella forma indicata (WashU ha dati clinici disponibili, anche se non organizzati negli stessi punteggi compositi per dominio di Siegel et al.).

**❓ Non verificabile da qui**: il resto della sintesi del paper (Experimental Procedures, Discussion) — non riletto integralmente contro il testo originale per limiti di tempo, ma nessun segnale di inaccuratezza dato l'alto tasso di fedeltà nello spot-check.

---

## `docs/knowledge/dim_reduction_tuning_guide.md`

**✅ Confermato corretto**
- Tabella metriche per metodo (`umap`/`tsne`/`pacmap` → trustworthiness, `pca`/`pca_varimax` → varianza cumulativa spiegata) — confermato esattamente su `TUNING_METRIC_NAMES` reale in `src/analysis/tuning.py`.
- `trustworthiness_n_neighbors` come parametro distinto da `n_neighbors` sweeppato — confermato (già verificato per `docs/dev/analysis.md`).
- Fix del bug metric-aware (jaccard/dice valutati con la stessa metrica, non l'euclidea di default) — coerente con quanto già verificato su `evaluate_umap`/`evaluate_tsne`.
- Meccanismo `nested_params`/`embeddings_grid_*.png`, file di output (`tuning_results.csv`, `tuning_plot.png` solo senza `nested_params` e con 1 parametro libero, `config.md`) — tutto confermato nei file precedenti di questo audit.
- Riferimenti incrociati (`docs/guides/dim_reduction.md`, `docs/knowledge/umap_tsne_guide.md`) — entrambi i file esistono davvero.

**⚠️ Nota già segnalata altrove, ripetuta qui per coerenza**
- **Riga 15** elenca `pca_varimax` tra i metodi con tuning disponibile — stesso problema già documentato nella sezione `docs/methods/dimensionality_reduction.md` di questo audit: `pca_varimax` non ha più una entry in `config/registry/params_reduction.json` da fine luglio, quindi il suo tuning non è oggi eseguibile da CLI nonostante il codice/i test lo supportino ancora. Non un errore specifico di questo file — è il 5° documento (su 5 già noti) con la stessa lacuna non segnalata.

**❓ Non verificabile da qui**: nessuno oltre a quanto sopra.

---

## `docs/knowledge/clustering_tuning_guide.md`

**✅ Confermato corretto — nessuna discrepanza trovata, incluso un riscontro empirico specifico verificato sul dato reale**
- `_square_grid_shape`, `plot_dendrogram(..., truncate_last_p=30)`, `plot_eigengap` — tutti confermati esattamente in `src/analysis/plotting.py`.
- I 3 indici generici, colonne extra per metodo (`inertia` KMeans, `bic`/`aic` GMM, `noise_fraction` HDBSCAN) — confermato su `METHOD_METRIC_COLUMNS` reale (già verificato più volte in questo audit).
- HDBSCAN senza diagnostica standalone, motivazione (nessun `eps` singolo da leggere) — confermato.
- **Esempio empirico specifico verificato sul dato reale**: *"Silhouette preferisce un k diverso da Davies-Bouldin... es. con pacmap: Silhouette premia k=2, Davies-Bouldin premia k=6"* — controllato su `results/lesion/dim_reduction_clustering/pacmap/kmeans/tuning/25-07_s1.1_n5/tuning_results.csv` reale: silhouette massimo a k=2 (0.506, k=6 vicino a 0.504), davies_bouldin minimo (migliore) a k=6 (0.581 contro 0.746 di k=2) — l'esempio nella doc è **esattamente riscontrabile** sul CSV reale, non un'illustrazione inventata.

**❓ Non verificabile da qui**: nessuno.

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
