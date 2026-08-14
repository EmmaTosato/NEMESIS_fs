# Piano di migrazione: eliminazione di `dim_reduction_clustering.py`

> **Stato**: piano, non ancora implementato. Diverso dal resto di `docs/dev/` (che descrive
> l'architettura *attuale*, mai un piano futuro) — questo file va aggiornato via via che i punti
> vengono completati, e **cancellato o fuso in `clustering.md`/`docs/guides/clustering.md`** a
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

`ClusteringConfig` (`src/analysis/model_config.py`) guadagna 4 campi nuovi, tutti opzionali salvo
dove indicato:

| Campo | Tipo | Obbligatorio se |
|---|---|---|
| `reduced_data` | `bool` | sempre presente, default `false` |
| `reduction_method` | `str \| None` | **richiesto** se `reduced_data=true` |
| `reduction_params_file` | `Path \| None` | **richiesto** se `reduced_data=true` |
| `viz_n_components` | `int` | sempre presente, **deve essere 2 o 3** (validare, non assumere) |
| `color_by` | `tuple[str, ...]` | opzionale, default vuoto |

Validazione esplicita in `load_clustering_config` (coerente con `code_standards.md` §0 — niente
fallback silenziosi):
- `reduced_data=true` senza `reduction_method`/`reduction_params_file` → `ValueError` chiaro.
- `reduced_data=false` **con** `reduction_method`/`reduction_params_file` valorizzati → `ValueError`
  (quasi certamente un errore di configurazione, non un campo da ignorare in silenzio).
- `viz_n_components` fuori da `{2, 3}` → `ValueError` (vedi §3).

`config/pipelines/dim_reduction_clustering.json` **sparisce**. `config/pipelines/clustering.json`
assorbe i suoi campi (`reduction_method`/`reduction_params_file`, stessi nomi/semantica di oggi).
I registry per-metodo (`params_reduction.json`, `params_clustering.json`) restano invariati — solo
`clustering.json` referenzia entrambi quando `reduced_data=true`.

## 2. Come si armonizza il codice sull'input

Oggi il significato di `config.input_path` è ambiguo tra le due pipeline. Dopo la migrazione,
`clustering.py` risolve **una sola volta**, all'inizio di `main()`, una coppia
`(X_cluster, X_viz)` a seconda di `reduced_data`:

- **`reduced_data=true`**: `input_path` è la matrice **grezza pre-riduzione** (stesso significato
  di oggi in `dim_reduction_clustering.py`). `X_cluster = embed(reduction_method, X, reduction_params,
  distance_cache)`; `X_viz = embedding_for_viz(reduction_method, X, reduction_params, X_cluster,
  viz_n_components, distance_cache)` — stessa logica di oggi, portata dentro `clustering.py`.
- **`reduced_data=false`**: `input_path` è una matrice **già pronta da clusterizzare così com'è**
  (grezza o un embedding già salvato da `dim_reduction.py` — `clustering.py` non lo sa e non gli
  serve saperlo). `X_cluster = X`. Per `X_viz`:
  - se `X.shape[1] == viz_n_components` → `X_viz = X` (nessun costo aggiuntivo, caso comune:
    input già a 2D/3D).
  - se `X.shape[1] != viz_n_components` → **`ValueError` esplicito**, non uno slicing silenzioso.
    `clustering.py` non conosce il metodo/parametri che hanno prodotto questa matrice, quindi non
    può rifittare una vista valida (lo stesso principio già applicato a
    `scripts/replot_dim_reduction.py`, vedi `lessons_learned.md` #16) — un taglio `X[:, :2]` su un
    embedding UMAP/t-SNE a N>2 dimensioni non è una proiezione valida. Il messaggio d'errore deve
    suggerire l'alternativa: produrre un embedding a `viz_n_components` esatti via `dim_reduction.py`,
    oppure usare `reduced_data=true` per lasciare che sia `clustering.py` a controllare la proiezione.

  **Nota**: questo sostituisce l'uso attuale di `X[:, :2]` in `clustering.py` per
  `cluster_plot.png` — oggi silenzioso e "innocuo per caso" solo perché finora `clustering.py` non
  è mai stato usato in produzione su un embedding salvato a >2 componenti (nessun run reale sotto
  `results/lesion/clustering/`, verificato). Va corretto comunque, non solo quando succede.

## 3. Comportamento con 2, 3 o più componenti

Due concetti **indipendenti**, da non confondere nel codice come nella doc:
- `n_components` del metodo di riduzione (dentro `reduction_params_file`) — quante dimensioni ha
  l'embedding su cui *si clusterizza* (può essere 2, 10, 15... nessun vincolo).
- `viz_n_components` — quante dimensioni ha la proiezione usata *solo per disegnare* i plot.
  **Sempre 2 o 3**, mai di più (un plot a 4+ dimensioni non esiste).

Verificato lo stato attuale prima di scrivere questo piano:
`write_embedding_plots` (`src/analysis/embedding_plots.py`) già oggi **non produce PNG statici per
un embedding a 3 componenti** ("a non-rotatable 3D scatter is unreadable") — l'esplorazione 3D
passa dal nuovo `src.pipeline.embedding_app` (Dash, Plotly 3D interattivo, appena introdotto,
commit `1da77e4`), che oggi però scopre solo run di produzione di `dim_reduction.py`
(`discover_production_runs`, pattern `results/*/dim_reduction/production/*/*`) e non ha
`cluster_label` come color mode.

`clustering.py` post-migrazione deve seguire la stessa regola, non reinventarne una diversa:

| `viz_n_components` | Comportamento |
|---|---|
| `2` | Comportamento di oggi: `cluster_plot.png`, `cluster_plot_interactive.html`, `silhouette_plot.png`, confronto statico e interattivo tra metodi — tutti invariati. |
| `3` | **Nessun PNG statico colorato per cluster** (stessa regola di `write_embedding_plots`). Serve estendere `embedding_app.py`: (a) far scoprire anche i run di produzione di `clustering.py`/`clustering.py --reduced_data`, (b) aggiungere `cluster_label` al registro color mode (`embedding_coloring.py`). **Task esplicito da tracciare a parte**, non implicito nella migrazione — oggi l'app non sa nulla di clustering. |

Il numero di componenti della riduzione (10, 15...) usato per il clustering vero e proprio non è
mai vincolato da questa tabella — resta libero, `viz_n_components` proietta sempre e solo per la
visualizzazione, indipendentemente da quante dimensioni ha `X_cluster`.

## 4. Struttura output

Stessa logica condizionale di `reduced_data` decide anche l'annidamento cartelle, senza
introdurre un terzo schema:
- `reduced_data=false`: schema piatto di oggi, `<output_root>/production/<method>/...`.
- `reduced_data=true`: schema annidato di oggi (da `dim_reduction_clustering.py`),
  `<output_root>/production/<reduction_method>/<method>/...`, un `runs.csv` condiviso per
  riduzione (via `extra_columns`, come oggi).

I risultati storici sotto `results/lesion/dim_reduction_clustering/` **non vanno spostati/rinominati**
- restano un archivio del vecchio pipeline. I nuovi run con `reduced_data=true` scrivono sotto un
nuovo root (es. `results/lesion/clustering/production/<reduction_method>/<method>/...`), dominio
distinto, nessuna collisione.

## 5. Checklist di eliminazione (ordine, non tutto insieme)

L'ordine conta: non si cancella `dim_reduction_clustering.py` finché `clustering.py` non ha parità
di feature *verificata da test*, altrimenti si perde temporaneamente lo script più usato del
progetto senza sostituto funzionante.

1. Estendere `ClusteringConfig`/`load_clustering_config` (§1).
2. Implementare il ramo `reduced_data=true` in `clustering.py` (§2) — riusa `embed()`/
   `embedding_for_viz()` da `src/analysis/reduction.py`, non li reimplementa.
3. Portare `viz_n_components ∈ {2,3}` + la regola della tabella in §3 (incluso il task separato di
   estendere `embedding_app.py` per il caso 3D+cluster).
4. Scrivere/portare test che coprano il nuovo ramo (mirror di
   `tests/integration/test_dim_reduction_clustering_pipeline.py` su `test_clustering_pipeline.py`)
   — parità dimostrata da test verdi, non da ispezione a occhio.
5. Aggiornare config/doc/job:
   - eliminare `config/pipelines/dim_reduction_clustering.json`
   - aggiornare `config/pipelines/clustering.json` con i nuovi campi
   - eliminare `docs/guides/dim_reduction_clustering.md`, fondere le istruzioni d'uso rilevanti in
     `docs/guides/clustering.md`
   - eliminare `jobs/run_dim_reduction_clustering.sh`
   - aggiornare ogni riferimento incrociato in `clustering.md`, `clustering_tuning_guide.md`,
     `dim_reduction.md`, `docs/dev/config.md`, `docs/dev/models.md`, `README.md` ("what's
     implemented so far")
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

Problema: con la migrazione, gli embedding (prodotti da `dim_reduction.py` o da `clustering.py
--reduced_data`) cresceranno di numero — serve un modo per l'utente di vedere a colpo d'occhio
"cosa esiste già" senza aprire N cartelle/`runs.csv`.

**Non va scritto a mano** — un secondo file mantenuto manualmente accanto a `runs.csv` va
inevitabilmente fuori sincrono con la realtà su disco (stesso pattern già visto in
`lessons_learned.md` #18, un riepilogo che smette di riflettere i run veri). Va **generato** da
uno script che legge tutti i `runs.csv`/`runs_tuning.csv` reali sotto `results/**/` + `SESSIONS.md`
per il join su sessione.

**Spostamento propedeutico**: `SESSIONS.md` si sposta da `data/SESSIONS.md` a
`docs/experiments/SESSIONS.md` (narrativa umana su cosa significa una sessione, sta meglio lì che
tra i dati grezzi) — il symlink `results/SESSIONS.md` viene rimosso, la sua informazione confluisce
nelle colonne 1-3 del CSV generato. Da aggiornare in questo spostamento (grep già fatto in
sessione): `docs/dev/config.md`, `docs/guides/dim_reduction.md`, `docs/dev/models.md`, il docstring
di `src/utils/run_log.py` (che oggi cita anche un path leggermente sbagliato,
`data/derived/lesion_matrix/SESSIONS.md` invece di `data/SESSIONS.md`).

Per essere parsabile da uno script, `SESSIONS.md` va irrigidito quel poco che basta: chiavi fisse
per riga (`- Modality:`, `- Datasets:`) invece della prosa libera di oggi — resta scrivibile a
mano, diventa anche regex-abile.

**Schema** (formato long/tidy, una riga per combinazione — non colonne con liste annidate, più
facile da filtrare/pivotare con pandas):

```
session | modality | datasets | reduction_method | metric | n_components | production_runs | tuning_runs
```

- `session`/`modality`/`datasets`: da `SESSIONS.md` (join su `session`).
- `reduction_method`/`metric`/`n_components`: da `params` (JSON) nei `runs.csv`/`runs_tuning.csv`
  di `dim_reduction.py` (e, dopo la migrazione, dal ramo `reduced_data=true` di `clustering.py`).
- `production_runs`/`tuning_runs`: conteggio righe corrispondenti in ciascun file — non un path
  (niente colonna `latest_output`, deciso in sessione: per il path esatto si va sul `runs.csv`
  puntuale, questo file resta un indice, non una scorciatoia verso i singoli risultati).

Il file vive in `results/dim_reduction_strategies.csv` (non uno per dominio) — un solo file
generalizza già a `fc`/`sdc` quando quei domini avranno risultati sotto `results/`, non solo
`lesion`.

**Dipendenza**: per essere davvero completo (join affidabile "stessi parametri → stesso output
riusabile"), beneficia della colonna `input_path` in `runs.csv` discussa in sessione (non ancora
implementata, vedi §7) — ma non la richiede in senso stretto: lo script può partire anche solo con
lo schema attuale di `runs.csv`, aggiungendo la precisione di `input_path` come miglioria successiva.

## 7. Colonna `input_path` in `runs.csv` (propedeutica al §6, non solo a lookup manuali)

Discusso in sessione, non ancora implementato:
- `FIELDNAMES` in `src/utils/run_log.py`: `session, id, timestamp, input_path, params, output, notes`
  (nuova colonna tra `timestamp` e `params`).
- `append_run_log_entry` guadagna un parametro `input_path: Path`, scritto nella riga — ogni
  `Config` dataclass del progetto ha già `input_path` disponibile, nessun dato nuovo da calcolare.
- 6 call site da aggiornare: `dim_reduction.py`, `clustering.py`, `dim_reduction_clustering.py` (finché
  esiste), `build_lesion_matrix.py`, `compute_sdc.py`, `mask_fc.py`, `build_fc_matrix.py`.
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
  `clustering_literature_survey.md`/`clustering.md`, non ancora implementato.
