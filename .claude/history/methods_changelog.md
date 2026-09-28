# Changelog dei metodi

Decisioni su **come analizziamo**: proxy per variabili mancanti, feature calcolate, soglie, metodi adottati o abbandonati — con le alternative scartate e il perché.

**Cosa NON va qui**: i risultati di un esperimento (`docs/experiments/`), i parametri di una singola run (`runs.csv`), il funzionamento corrente di una pipeline (`docs/`, sempre al presente).

Voci in ordine cronologico inverso.

---

## 28-09-26 — `build_lesion_matrix.json` riportato alla griglia a 2mm, era scivolato a 1mm

**Decisione**: `reference_template_path`/`brain_mask_path` in `config/pipelines/build_lesion_matrix.json` passati da `tpl-MNI152NLin6Asym_res-1_*` (1mm) a `tpl-MNI152NLin6Asym_res-2_*` (2mm). Aggiornati anche i due path hardcoded nella sezione "Lesione fuori dal brain" di `notebooks/exploration/dataset_exploration.ipynb`, per restare sulla stessa griglia della produzione.

**Perché**: la voce del 06-09-26 in questo stesso file fissa la griglia a 2mm per `build_lesion_matrix.py` (e per `build_sdc_matrix.py` in modalità `voxelwise`), con alternative misurate e scartate esplicitamente. Lo swap del 23-09-26 da un singolo file paziente a un template versionato (`project_changelog.md`) ha però impostato `res-1` (1mm) — non una scelta di risoluzione deliberata, solo la prima opzione disponibile al momento di rendere il riferimento stabile — introducendo una deviazione silenziosa dalla griglia già decisa. Richiesto esplicitamente dall'utente ("voglio risoluzione a 2mm"), verificato prima di applicare che `res-2` T1w e brain mask condividano shape/affine (91×109×91, 2mm isotropo).

**Conseguenza ancora vera oggi**: `config/pipelines/build_sdc_matrix.json` (rappresentazione `voxelwise`) ha la **stessa** deviazione — `reference_template_path` è ancora su `res-1` — e non è stato toccato in questa sessione (fuori scope, riguarda solo `build_lesion_matrix.json`). Da allineare quando si torna a lavorare su quella pipeline. Nessun impatto su matrici già costruite (`data/derived/lesion_matrix/<sessione>/`): la griglia è fissata al momento del build, questo è solo un cambio di config per le run future.

---

## 28-09-26 — Filtro di qualità della lesione (volume minimo, frazione fuori dal brain): solo per `build_lesion_matrix.py`, non per `build_sdc_matrix.py`

**Decisione**: `build_lesion_matrix.py` guadagna due soglie opzionali di ammissione soggetto, entrambe `null` di default (nessun filtro): `min_lesion_volume_voxels` (esclude lesioni troppo piccole) e `max_out_of_brain_fraction` (esclude soggetti con troppi voxel di lesione fuori dalla maschera cerebrale MNI152, stessa logica di `scripts/lesion_fix.py`, richiede `brain_mask_path`). Entrambe calcolate in-run, dai dati voxel già caricati/binarizzati di quella specifica run (`src/features/lesion.py::_filter_by_lesion_quality`), non da `assets/metadata/participants.csv` — la cui colonna `lesion_volume_voxels` potrebbe riflettere una griglia/`binarize_threshold` di una run diversa. Un soggetto a 0 voxel di lesione ottiene `out_of_brain_fraction = 0.0` per convenzione esplicita (vacuosamente vero), mai `NaN`. I soggetti esclusi sono elencati in due nuove sezioni di `config.md`/`summaries/build_lesion_matrix/*/build_summary__*.md` ("Excluded by min_lesion_volume_voxels"/"Excluded by max_out_of_brain_fraction"), stesso schema già in uso per `group_filter`.

**Alternativa scartata**: implementare lo stesso meccanismo anche in `build_sdc_matrix.py`/`src/features/sdc.py`, come inizialmente richiesto. Scartata perché `sdc.py` risolve deliberatamente la presenza della lesion mask da `assets/metadata/participants.csv` (`has_lesion`), mai da un glob su `manual_masks/` — scelta presa apposta dopo un bug reale (debug 27-08-26, vedi `docs/dev/sdc_matrix.md` §"Why participants.tsv, not manual_masks/ on disk": una copia locale parziale dei dati falsava l'ammissione). Aggiungere qui le due soglie avrebbe richiesto o ricaricare `manual_masks/` direttamente (reintroducendo esattamente quel rischio) o precalcolare le metriche in `participants.csv` (un nuovo componente pipeline, fuori scope). Interpellato esplicitamente, l'utente ha confermato che le due soglie derivano dalla lesione e servono solo a `lesion_matrix`.

**Conseguenza ancora vera oggi**: una matrice già costruita in `data/derived/lesion_matrix/<sessione>/` non viene mai filtrata a posteriori — impostare/cambiare queste soglie non ha alcun effetto su un output già scritto. Se ci si accorge di aver dimenticato una soglia, la run va cancellata (cartella di output + riga in `runs.csv`) e rifatta da capo, mai patchata in-place.

---

## 07-09-26 — Clustering lesionale: nessun k unico di produzione, per scelta

**Decisione**: per s1.1-vol e s1.2-vol non viene eletto un k di produzione. Le opzioni prodotte (k=4/5/6 su più metodi, più le varianti hdbscan e, su s1.1-vol, spectral a k=8) restano tutte valide in parallelo, ognuna come una lettura diversa della stessa struttura. Scritta nelle sezioni `Decisioni` di `docs/experiments/clustering/s1_production.md`, che erano rimaste vuote.

**Perché**: nessun criterio interno converge su un k solo — la silhouette premia k alti per costruzione, CH cresce quasi sempre con k, l'inertia non ha un gomito netto (`s1_tuning.md`). Restringere a un valore significherebbe delegare a una metrica di comodo una scelta che quella metrica non sa fare. In più il k non è separabile da `n_components` dell'embedding: il k migliore non converge tra n2/n3/n10, quindi i due vanno decisi insieme, a valle.

**Alternativa scartata**: eleggere un k unico su una metrica interna (tipicamente il massimo di silhouette). Scartata perché produrrebbe una scelta apparentemente oggettiva ma guidata da un artefatto della metrica, non dalla struttura dei dati.

**Conseguenza ancora vera oggi**: il confronto tra opzioni avviene in `notebooks/post-results_analysis/clustering_evaluation.ipynb`, che ne carica un sottoinsieme alla volta in `SELECTED_RUNS`. Una run di produzione presente in `results/` non è quindi "la" scelta: è una delle opzioni tenute aperte apposta.

---

## 06-09-26 — Ricampionamento a 2mm con `nearest`: confermato, alternative misurate

**Decisione**: ogni matrice voxel-wise resta sulla griglia MNI152NLin6Asym a 2mm con `resample_interpolation: "nearest"`. Vale per `build_lesion_matrix.py` e per `build_sdc_matrix.py` in modalità `voxelwise`.

**Contesto**: 2 soggetti UKE sono entrati in `lesion_matrix` s1.3-vol come righe tutte-zero (voce del 06-09-26 in `data_changelog.md`), il che ha aperto la domanda se `nearest` fosse la scelta sbagliata per tutte le run future.

**Misurato prima di decidere** (griglie native: UCL-UK e WashU già a 2mm, UKLFR a 1.5mm, PASPORT/PSP/UKE a 1mm — 1399 soggetti su 5720 vengono effettivamente ricampionati):

| | bias sul volume totale | errore mediano per soggetto | lesioni azzerate (48 più piccole) |
|---|---:|---:|---:|
| `nearest` | −1,5% | 1,6% | 2 |
| `linear` | −1,6% | 1,8% | 2 |

**Alternative scartate:**

- **`linear`**: misurata equivalente, e marginalmente peggiore in aggregato. Azzera *esattamente le stesse* 2 lesioni. Il motivo è che `nilearn.image.resample_to_img` con `linear` interpola tra i vicini del punto campionato, non media il blocco di 8 voxel: in downsampling si comporta quasi come `nearest`. E anche una media vera non salverebbe una lesione da 3 voxel, che resta sotto `binarize_threshold` 0.5 (3/8 = 0,375).
- **`continuous`**: già esclusa in precedenza per un motivo indipendente — lascia rumore di arrotondamento (~1e-17) attorno allo zero che impedisce a `_drop_constant_features` di scartare i voxel costanti.
- **Griglia a 1mm**: scartata per due ragioni. Una matrice SDC voxel-wise su ~1570 soggetti a 1mm sarebbe dell'ordine delle decine di GB (7,2M voxel per soggetto), non trattabile in locale; e la griglia comune a 2mm tiene la matrice lesionale e quella SDC allineate voxel per voxel, che è il presupposto della rappresentazione multimodale.

**Conseguenza ancora vera oggi**: la perdita non dipende dalla dimensione della lesione ma da *dove cade rispetto alla griglia* — nei dati misurati una lesione da 15 mm³ sopravvive e una da 16 mm³ sparisce. Non esiste quindi una soglia di volume sotto la quale "si sa" che il soggetto verrà perso: va controllato il volume post-ricampionamento, non quello nativo.

**Deciso di non intervenire sul codice** (07-09-26): `build_lesion_matrix.py` continua ad ammettere una riga tutta-zero senza segnalarla, a differenza di `build_sdc_matrix.py` che per il rischio equivalente esclude esplicitamente e traccia l'esclusione. Valutato non proporzionato: 2 soggetti su 5720 (0,035%). I due casi noti restano in `06-09_s1.3-vol` e sono documentati in `docs/experiments/processing/matrices.md`; chi userà quella matrice li filtra a valle se gli serve. Da rivedere se un dataset futuro ne producesse un numero non trascurabile — il segnale da guardare è il volume minimo *dopo* il ricampionamento, non quello nativo.

---

## 27-08-26 — Ammissione soggetti in `build_sdc_matrix.py`: controllo su `participants.csv`, non su `manual_masks/` su disco

**Decisione**: l'ammissione di un soggetto alla matrice SDC controlla `has_lesion` nel registro (`assets/metadata/participants.csv`), non l'esistenza del file su `manual_masks/` in locale.

**Perché**: su questa macchina locale `manual_masks/` conteneva solo un campione di 10 soggetti per dataset, mentre `sdc/` era già completo — un controllo sul disco locale ammetteva solo 40/1151 soggetti, escludendo erroneamente soggetti con una lesion mask reale ma non ancora retrievata localmente.

**Alternativa scartata**: controllare `manual_masks/` su disco direttamente — inaffidabile perché un retrieval locale parziale non riflette la disponibilità reale dei dati alla fonte.

**Conseguenza ancora vera oggi**: con il criterio sul registro, la run reale di allora ammetteva 1119/1151 soggetti; i 32 esclusi erano confermati genuinamente assenti dal registro clinico, non un artefatto di retrieval locale. La regola corrente (controllo su registro, non su disco) è documentata in `docs/guides/sdc_matrix_building.md`/`docs/dev/sdc_matrix.md`.

---

## 25-08-26 — `build_lesion_matrix.py`: rimossa la modalità `parcellated`

**Decisione**: `build_lesion_matrix.py` produce solo matrici voxel-wise; la modalità `parcellated` (matrice per macro-aree anatomiche via atlante) è stata rimossa dalla pipeline.

**Perché/dettagli**: vedi `management/notes/TODO.md`.

**Conseguenza ancora vera oggi**: non esiste un parametro di rappresentazione per questa pipeline — la matrice lesionale prodotta è sempre voxel-wise (a differenza di `build_sdc_matrix.py`, che ha sia `parcellated` sia `voxelwise`).
