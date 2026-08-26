# Piano di migrazione: eliminazione di `dim_reduction_clustering.py`

> **Stato**: piano, non ancora implementato. Diverso dal resto di `docs/dev/` (che descrive
> l'architettura *attuale*, mai un piano futuro) — questo file va aggiornato via via che i punti
> vengono completati, e **cancellato o fuso in `docs/guides/clustering.md`** a
> migrazione conclusa, non lasciato a vivere accanto alla nuova architettura come doc parallela.
>
> Deciso in sessione 14-08-26 (discussione, non ancora eseguito). Contesto letteratura/gap
> identificati: `knowledge/dim_reduction_clustering/clustering_literature_survey.md`,
> `challenge_of_clustering_after_dim_reduction.md`.

## Perché

`dim_reduction_clustering.py` è oggi "lo script più utilizzato nell'intero progetto NEMESIS"
(`docs/guides/dim_reduction_clustering.md`) ma duplica quasi per intero l'orchestrazione CLI di
`clustering.py` (stesso `_run_one_method`, stesso `_write_tuning_output`, stessa logica di
run-log) solo per aggiungere un embed() a monte. La logica algoritmica vera
(`CLUSTERING_METHODS`, `clustering_tuning.py`, `consensus_clustering.py`, `embed()`/
`embedding_for_viz()`) è **già condivisa** in `src/analysis/` — la duplicazione è solo nel layer
`src/pipeline/`. Obiettivo: un solo entry point (`clustering.py`), stessa capacità, nessuna
duplicazione CLI.

## 1. Come cambia il config

**Semplificato in sessione (14-08-26)**: niente `embed()` dentro `clustering.py`. Ricalcolare una
riduzione al volo dentro `clustering.py` è stato scartato per ora come troppo complesso da
implementare bene subito — `clustering.py` non chiama mai `embed()`, in nessun ramo. `reduced_data`
resta, ma cambia scopo: non più "ricomputa la riduzione", solo **una dichiarazione esplicita di
cosa rappresenta `input_path`** — coerente con "niente fallback silenziosi" (§0
`code_standards.md`): il codice non deve indovinare se sta clusterizzando un embedding o una
matrice grezza, l'operatore lo dichiara.

`ClusteringConfig` (`src/analysis/model_config.py`) guadagna 2 campi nuovi:

| Campo | Tipo | Obbligatorio se |
|---|---|---|
| `reduced_data` | `bool` | sempre presente, nessun default silenzioso — va dichiarato esplicitamente |
| `color_by` | `tuple[str, ...]` | opzionale, default vuoto |

- `reduced_data=true`: `input_path` punta a un embedding **già calcolato** (es. da
  `dim_reduction.py`, con qualunque `n_components`). Nessun ricalcolo — `clustering.py` legge e
  clusterizza `X` così com'è.
- `reduced_data=false`: `input_path` punta a una matrice grezza, clusterizzata direttamente
  (opzione permessa ma sconsigliata, già documentata in
  `knowledge/dim_reduction_clustering/clustering_tuning_guide.md`).

`~~reduction_method~~`/`~~reduction_params_file~~` **non servono più** — eliminati dal design,
non solo dal config. `~~viz_n_components~~` come campo di config **non serve più**: la
dimensionalità della viz non si configura, **si scopre dalla forma di `X` a runtime** (vedi §3) —
un campo di config in meno da tenere sincronizzato con la realtà dell'embedding caricato.

`config/pipelines/dim_reduction_clustering.json` **sparisce**. `config/pipelines/clustering.json`
assorbe solo `reduced_data` + `color_by` — non due file di parametri di riduzione, il design non li
prevede più. I registry per-metodo (`params_reduction.json`, `params_clustering.json`) restano
invariati, ma `clustering.json` non referenzia più il primo in nessun caso.

## 2. Come si armonizza il codice sull'input

**Molto più semplice del design iniziale**, ora che `embed()` non entra più in `clustering.py`:
`load_matrix(config.input_path)` resta l'**unico** modo in cui `clustering.py` ottiene `X`, in
entrambi i valori di `reduced_data` — nessun ramo di calcolo diverso. `reduced_data` non cambia
*come* si carica `X`, cambia solo *come lo si dichiara/logga* e come si tratta la sua
dimensionalità per la viz (§3).

`X_cluster = X`, sempre. Non esiste più un `X_viz` calcolato per rifit — vedi §3 per come si
decide se e cosa disegnare, dato che questo è esattamente il punto lasciato aperto in sessione.

Questo sostituisce comunque l'uso attuale di `X[:, :2]` in `clustering.py` per `cluster_plot.png`
— oggi silenzioso e "innocuo per caso" solo perché finora `clustering.py` non è mai stato usato in
produzione su un embedding salvato a >2 componenti (nessun run reale sotto
`results/lesion/clustering/`, verificato). Va corretto comunque, non solo quando succede — vedi §3.

## 3. Comportamento con 2, 3 o più componenti

**Non più un campo di config** (`viz_n_components` rimosso, vedi §1) — la dimensionalità della viz
si scopre a runtime da `X.shape[1]` dopo il caricamento, non si dichiara a priori.

Verificato lo stato attuale prima di scrivere questo piano: `write_embedding_plots`
(`src/analysis/embedding_plots.py`) già oggi **non produce PNG statici per un embedding a 3
componenti** ("a non-rotatable 3D scatter is unreadable") — l'esplorazione 3D passa dal nuovo
`src.pipeline.embedding_app` (Dash, Plotly 3D interattivo, appena introdotto, commit `1da77e4`),
che oggi però scopre solo run di produzione di `dim_reduction.py` (`discover_production_runs`,
pattern `results/*/dim_reduction/production/*/*`) e non ha `cluster_label` come color mode.

| `X.shape[1]` | Comportamento |
|---|---|
| `2` | Come oggi: `cluster_plot.png`, `cluster_plot_interactive.html`, `silhouette_plot.png`, confronto statico e interattivo — invariati, si disegna direttamente su `X`. |
| `3` | Nessun PNG statico colorato per cluster (stessa regola di `write_embedding_plots`, invariato) — ma **deciso e implementato (15-08-26)** per l'esplorazione interattiva: `embedding_app.py` scopre ora anche i run di `clustering.py` (`PRODUCTION_PIPELINES = ("dim_reduction", "clustering")`, `discover_production_runs` generalizzato sul segmento `<pipeline>` del path — la cartella `comparison/` di `clustering.py` è esclusa automaticamente, non ha mai `manifest.json`), e `cluster_label` è stato aggiunto a `embedding_coloring.COLOR_MODES`. Il picker guadagna un passo "Pipeline" selezionabile (prima un'etichetta fissa); "Metrica"/"Componenti" restano visibili per uniformità ma collassano al loro sentinel `NO_METRIC`/`NO_N_COMPONENTS` per i run di clustering (nessun asse metrica/componenti in quel dominio — un metodo di clustering non ha `n_components` nei suoi `params`). Implementato in `src/analysis/embedding_app.py`/`embedding_coloring.py`, testato in `tests/unit/test_embedding_app.py`/`test_embedding_coloring.py`, documentato in `docs/guides/embedding_app.md`. |
| `> 3` (o `< 2`) | **Deciso e implementato (14-08-26)**: opzione (a). Nuovo campo config opzionale `viz_embedding_path` — un embedding "gemello" 2D/3D calcolato **a parte** dall'utente (es. via `dim_reduction.py`, stessi `random_state`/`n_neighbors`/`metric`, solo `n_components` diverso), sugli stessi soggetti nello stesso ordine. `clustering.py::_resolve_viz_embedding` lo carica e valida (numero componenti 2/3, stesso `subject_id` in stesso ordine di `input_path` — altrimenti `ValueError`); se `X.shape[1]` è già 2 o 3 lo ignora e usa `X` direttamente. Se né l'uno né l'altro vale, **nessun plot** (`cluster_plot.png`/`cluster_plot_interactive.html`/`silhouette_plot.png`/`cluster_comparison.png` tutti saltati con warning esplicito) — mai una slice di `X` (`lessons_learned.md` #16). Implementato in `src/pipeline/clustering.py`, testato in `tests/integration/test_clustering_pipeline.py`. **Esteso (26-08-26)**: le due verifiche strutturali sopra (forma, ordine soggetti) non garantiscono che `viz_embedding_path` sia davvero un "gemello" dell'embedding di `X` — un companion costruito con un metodo o iperparametri diversi le supera comunque, producendo un layout geometricamente scorrelato su cui vengono disegnate etichette di cluster reali, senza errore a segnalarlo. Quando `reduced_data` è `True` (`input_path` è anch'esso un run di `dim_reduction.py`, quindi c'è qualcosa da confrontare), `_resolve_viz_embedding` chiama in più `_require_matching_reduction_run(input_path, viz_embedding_path)`, che solleva `ValueError` a meno che i due run non condividano lo stesso `reduction_method` (`src.utils.artifacts.read_dim_reduction_method`) e gli stessi parametri risolti a parte `n_components` (`src.utils.artifacts.read_run_params`, confronto simmetrico via dict). Saltato quando `reduced_data` è `False` (`input_path` è una matrice grezza, il cui `config.md` non ha un metodo/parametri di riduzione da confrontare). `read_run_params` è anche il punto di estrazione condiviso con `embedding_app.py::run_params` (ora un thin wrapper). |

## 4. Struttura output

Senza più `reduction_method` in config (§1), non c'è più un campo da cui derivare
automaticamente un annidamento a due livelli — **schema piatto sempre**,
`<output_root>/production/<method>/...`, identico indipendentemente da `reduced_data`. Il
raggruppamento "questi metodi vengono tutti dalla stessa riduzione" resta possibile solo tramite
`session_name`/tag scelti dall'utente (come già oggi in `clustering.py`), non forzato dalla
struttura di cartelle.

I risultati storici sotto `results/lesion/dim_reduction_clustering/` **non vanno spostati/rinominati**
— restano un archivio del vecchio pipeline. I nuovi run scrivono sotto un nuovo root
(`results/lesion/clustering/production/<method>/...`), dominio distinto, nessuna collisione.

## 5. Checklist di eliminazione (ordine, non tutto insieme)

L'ordine conta: non si cancella `dim_reduction_clustering.py` finché `clustering.py` non ha parità
di feature *verificata da test*, altrimenti si perde temporaneamente lo script più usato del
progetto senza sostituto funzionante.

1. Estendere `ClusteringConfig`/`load_clustering_config` con `reduced_data`/`color_by` (§1).
2. Nessuna logica di calcolo nuova da portare (§2) — `clustering.py` continua a usare solo
   `load_matrix`, `reduced_data` è dichiarativo. Va solo aggiunto un log esplicito all'avvio
   ("clustering su embedding già calcolato" / "clustering su matrice grezza") per rendere visibile
   quale caso è in corso.
3. **Decidere** (non ancora fatto, vedi §3) come gestire la viz quando `X.shape[1] > 3`, poi
   implementare la regola della tabella in §3 (incluso il task separato di estendere
   `embedding_app.py` per il caso 3D+cluster).
4. Scrivere/portare test che coprano il nuovo ramo (mirror di
   `tests/integration/test_dim_reduction_clustering_pipeline.py` su `test_clustering_pipeline.py`)
   — parità dimostrata da test verdi, non da ispezione a occhio.
5. Aggiornare config/doc/job:
   - eliminare `config/pipelines/dim_reduction_clustering.json`
   - aggiornare `config/pipelines/clustering.json` con i nuovi campi
   - eliminare `docs/guides/dim_reduction_clustering.md`, fondere le istruzioni d'uso rilevanti in
     `docs/guides/clustering.md`
   - eliminare `jobs/run_dim_reduction_clustering.sh`
   - aggiornare ogni riferimento incrociato in `knowledge/dim_reduction_clustering/clustering_tuning_guide.md`,
     `docs/dev/config.md`, `docs/dev/models.md`, `README.md` ("what's implemented so far") —
     `clustering.md`/`dim_reduction.md` (root) non esistono più dal 14-08-26, contenuto già confluito
     in `knowledge/dim_reduction_clustering/`
   - **non** rinominare `knowledge/dim_reduction_clustering/` né
     `docs/experiments/dim_reduction_clustering/` — sono cartelle sul *tema* (letteratura,
     esperimenti), non sul nome dello script; restano valide a prescindere dalla sua eliminazione.
6. Eliminare `src/pipeline/dim_reduction_clustering.py` e
   `tests/integration/test_dim_reduction_clustering_pipeline.py`.
7. **Grep finale di verifica** (pattern #12 di `lessons_learned.md`): `grep -rn
   "dim_reduction_clustering"` su tutto il repo, confermare che ogni hit rimasto è intenzionale
   (cartelle di knowledge/experiments, risultati storici) e non un riferimento morto a codice/config
   che non esiste più.

## 6. `results/dim_reduction_strategies.csv` — indice degli embedding esistenti

**Fatto 15-08-26** (versione minima, vedi scope dichiarato sotto). Problema: con la migrazione,
gli embedding (prodotti da `dim_reduction.py` o da `clustering.py --reduced_data`) cresceranno
di numero — serve un modo per l'utente di vedere a colpo d'occhio "cosa esiste già" senza aprire
N cartelle/`runs.csv`.

**Non va scritto a mano** — un secondo file mantenuto manualmente accanto a `runs.csv` va
inevitabilmente fuori sincrono con la realtà su disco (stesso pattern già visto in
`lessons_learned.md` #18, un riepilogo che smette di riflettere i run veri). Va **generato** da
uno script che legge tutti i `runs.csv`/`runs_tuning.csv` reali sotto `results/**/` + `SESSIONS.md`
per il join su sessione.

**Spostamento propedeutico (fatto 15-08-26)**: `SESSIONS.md` si è spostato da `data/SESSIONS.md`
a `docs/experiments/SESSIONS.md` (narrativa umana su cosa significa una sessione, sta meglio lì
che tra i dati grezzi) — il symlink `results/SESSIONS.md` è stato rimosso, la sua informazione
confluisce nelle colonne 1-3 del CSV generato. Aggiornati in questo spostamento: `docs/dev/config.md`,
`docs/guides/dim_reduction.md` (`docs/dev/models.md` e il docstring di `src/utils/run_log.py`
citavano già il path nuovo, scritti in anticipo in una sessione precedente).

Per essere parsabile da uno script, `SESSIONS.md` è stato irrigidito quel poco che basta: chiavi
fisse per riga (`- Starting date:`, `- Datasets:`, `- Modality:`) invece della prosa libera di
prima — resta scrivibile a mano, è anche regex-abile (`scripts/build_dim_reduction_strategies_csv.py::parse_sessions_md`,
`ValueError` se manca una chiave o una sessione è documentata due volte).

**Schema** (formato long/tidy, una riga per combinazione — non colonne con liste annidate, più
facile da filtrare/pivotare con pandas):

```
session | modality | datasets | reduction_method | metric | n_components
```

- `session`/`modality`/`datasets`: da `SESSIONS.md` (join su `session`).
- `reduction_method`/`metric`/`n_components`: da `params` (JSON) nei `runs.csv`/`runs_tuning.csv`
  di `dim_reduction.py` (e, dopo la migrazione, dal ramo `reduced_data=true` di `clustering.py`).
- **Niente colonna `production_runs`/`tuning_runs`** (rimosse 16-08-26, su richiesta, dalla
  versione inizialmente implementata) **né `latest_output`**: una riga per combinazione
  esistente (produzione o tuning, deduplicata), non un conteggio né un path — per quello si va
  sul `runs.csv` puntuale, questo file resta un indice di esistenza, non una scorciatoia verso i
  singoli risultati o la loro storia.

Il file vive in `results/dim_reduction_strategies.csv` (non uno per dominio) — un solo file
generalizza già a `fc`/`sdc` quando quei domini avranno risultati sotto `results/`, non solo
`lesion`.

**Dipendenza**: per essere davvero completo (join affidabile "stessi parametri → stesso output
riusabile"), beneficia della colonna `input_path` in `runs.csv` discussa in sessione (**fatta,
§7**) — ma la versione implementata non la usa ancora: `scripts/build_dim_reduction_strategies_csv.py`
oggi legge solo `runs.csv`/`runs_tuning.csv` di `dim_reduction.py` (non il ramo `reduced_data=true`
di `clustering.py`, che richiederebbe risolvere l'`input_path` di ogni run di clustering contro
l'`output` del run di `dim_reduction.py` che lo ha prodotto — join reale, non ancora scritto,
deliberatamente rimandato). Testato in `tests/unit/test_build_dim_reduction_strategies_csv.py`,
girato sui dati reali del progetto (14 righe, `results/lesion/dim_reduction/`) dopo 2 giri di
correzione: (1) le righe di `runs.csv`/`runs_tuning.csv` il cui `output` non esiste più su
disco vengono scartate, non contate come esistenti (`_output_dir_exists`, 16-08-26 - risolto
anche `scripts/backfill_stale_tuning_output_paths.py`, che corregge i path di
`runs_tuning.csv` rimasti sul vecchio layout `<metodo>/tuning/` pre-riorganizzazione, solo
quando il path scambiato esiste davvero); (2) una riga di tuning il cui `tuning_grid` sweepa
davvero `metric`/`n_components` genera una riga per ogni valore esplorato, non solo per il
valore di partenza in `base_params` (`_strategy_variants`, 16-08-26 - il bug precedente faceva
sparire dal CSV 2 metriche su 3 realmente esplorate per `tsne`, dato che i suoi run di
produzione sono tutti orfani e l'unica prova della loro esistenza è nel tuning).

## 7. Colonna `input_path` in `runs.csv` (propedeutica al §6, non solo a lookup manuali)

**Fatto 14-08-26.** `scripts/backfill_runs_csv_input_path.py` (nuovo) ha eseguito il backfill:
21 righe storiche esaminate, 9 recuperate da `config.md`, 12 lasciate vuote con warning esplicito
(righe pre-riorganizzazione produzione/tuning la cui cartella `output` originale non esiste più
allo stesso path — un gap storico pre-esistente, non introdotto qui, isolato per riga senza
bloccare il resto del file, coerente con `lessons_learned.md` #21). Nota a parte: durante questo
lavoro è emerso che `results/lesion/dim_reduction_clustering/` e le sottocartelle `pca`/`pacmap`
di `results/lesion/dim_reduction/production/` **non esistono più su disco** rispetto a quanto
verificato a inizio sessione — non causato da questo piano, segnalato all'utente separatamente
(nessuna azione qui, `results/` non è tracciato da git quindi non c'è modo di verificarne la causa
da qui).

Dettagli implementativi:
- `FIELDNAMES` in `src/utils/run_log.py`: `session, id, timestamp, input_path, params, output, notes`
  (nuova colonna tra `timestamp` e `params`).
- `append_run_log_entry` guadagna un parametro `input_path: Path`, scritto nella riga — ogni
  `Config` dataclass del progetto ha già `input_path` disponibile, nessun dato nuovo da calcolare.
- 6 call site da aggiornare (`dim_reduction_clustering.py` eliminato nel frattempo, §5 già fatto,
  quindi non è più uno di questi): `dim_reduction.py`, `clustering.py`, `build_lesion_matrix.py`,
  `compute_sdc.py`, `mask_fc.py`, `build_fc_matrix.py`.
- **Backfill dei 15 `runs.csv`/`runs_tuning.csv` già su disco** (`results/lesion/dim_reduction*/`):
  per ognuno, leggere `output` → aprire `<output>/config.md` → estrarre `input_path` da lì →
  aggiungerlo come colonna. Script una tantum, non a mano riga per riga.
- Aggiornare `tests/unit/test_run_log.py` per il nuovo schema.

Uso concreto (oltre al §6): un helper che, prima di far girare `embed()`, cerca in `runs.csv` un
run con `params` identici **e** stesso `input_path`, e se lo trova propone di riusare `output`
invece di ricalcolare — informativo, nessun riuso automatico silenzioso (coerente con "nessuna
selezione automatica silenziosa" del progetto). Limite noto e dichiarato: un match su `input_path`
è per path, non per contenuto — non rileva una matrice rigenerata con lo stesso path ma dati
diversi; da tenere presente, non da risolvere subito.

## Fuori scope di questo piano (discusso ma non dettagliato qui)

- Fase di **Evaluation** post-tuning (indici calcolati sul clustering di produzione scelto, non
  solo durante lo sweep) — vedi report di sessione 14-08-26.
- Controllo di **cluster tendency** prima del clustering — gap dichiarato in
  `knowledge/dim_reduction_clustering/clustering_literature_survey.md`, non ancora implementato.
