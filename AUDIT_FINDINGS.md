# Audit findings — 17/08/26

Documento di lavoro (non un report di debug concluso — quello vive in `docs/debugging/` solo a
fix effettivamente implementati, per convenzione del repo, §8 `code_standards.md`). Elenca i
findings emersi dall'audit di correttezza teorica del 15/08/26 (8 agenti paralleli, uno per
pipeline — `retrieve_data`, `build_combined_atlas`, `compute_sdc` esclusi su richiesta esplicita;
template riusabile in `docs/debugging/` una volta formalizzato, per ora in scratchpad di sessione).

I fix vengono decisi e annotati uno alla volta con l'utente, non tutti insieme a fine sessione —
lo stato di ciascun finding è tracciato inline. Da spostare/rinominare come report di debug
standard in `docs/debugging/` solo a lavoro concluso.

Organizzato per severità, un finding per sezione. Ogni sezione ha uno stato:
- **Aperto** — non ancora discusso
- **Deciso** — fix concordato con l'utente, non ancora implementato
- **Implementato** — fix applicato, test di regressione aggiunto/verificato

---

## CRITICAL

### 1. `clustering.json`: `session_name` vuoto, la CLI non parte

**Pipeline**: `clustering` — [config/pipelines/clustering.json:9](config/pipelines/clustering.json#L9)

**Difetto**: `session_name: ""` nella config di produzione committata — quella puntata sia dalla
guida ([docs/guides/clustering.md:21](docs/guides/clustering.md#L21)) sia da
[jobs/run_clustering.sh:14](jobs/run_clustering.sh#L14)). Riprodotto lanciando il comando
esatto della guida: `ERROR: config: field 'session_name' must be a non-empty string, got ''`.
Confrontata con le altre 7 config di produzione nel repo (tutte con `session_name` reale:
`s1.1`, `s2`, `yan300s1`, `s1`...) — nessuna convenzione di "vuoto = placeholder da compilare",
è l'unica lasciata così.

**Il validatore è corretto** ([src/analysis/model_config.py:147-153](src/analysis/model_config.py#L147-L153))
— rifiuta rumorosamente un campo obbligatorio vuoto, come da §0 code_standards. Il problema è
solo lo stato del file di config committato.

**Stato: Deciso — nessuna azione da parte mia.** L'utente compilerà `session_name` a mano al
prossimo run. Non è un bug di codice.

---

### 2. `embedding_app`: non funzionante su `main`

**Pipeline**: `embedding_app` — [src/analysis/embedding_app.py:678,288,300,314](src/analysis/embedding_app.py#L678)

**Difetto**: migrazione a metà — parametro `pipeline` aggiunto ad alcune funzioni ma non
propagato ai callback che le invocano → `TypeError` al primo click. Confermato: 22/33 test
falliscono sul commit corrente di `main`.

**Causa esatta, verificata dal vivo** (17/08):
`ProductionRun` è diventato a 5 campi (`modality, pipeline, method, run_name, path`) e
`runs_for(runs, modality, pipeline, method)`/`method_options(runs, modality, pipeline)`
richiedono `pipeline` — ma i loro chiamanti in `build_app` non sono stati aggiornati:
- `_update_method_picker` chiama `method_options(runs, modality)` →
  `TypeError: method_options() missing 1 required positional argument: 'pipeline'`
- `metric_options`/`n_components_options`/`runs_matching` (che NON hanno `pipeline` nella
  propria firma) passano `method` al posto di `pipeline` a `runs_for(runs, modality, method)` →
  `TypeError: runs_for() missing 1 required positional argument: 'method'`
- il layout (`build_app`) non ha mai un vero `pipeline-picker`: è ancora testo statico
  `"Dim Reduction · Produzione"` — `pipeline_options()` esiste ma non è cablato a nessun
  componente Dash.

**Requisito confermato con l'utente (17/08)**: l'app deve funzionare sia per `dim_reduction`
produzione sia per `clustering` produzione, sempre con dato `lesion`. **Nota di design
esplicita**: questa è un'app incrementale — verranno aggiunte visualizzazioni/feature nel tempo,
quindi anche il codice va scritto per essere esteso senza altre migrazioni a metà (es. un
`pipeline` aggiunto ovunque insieme, non modulo per modulo).

**Stato: Implementato (17/08).** `metric_options`/`n_components_options`/`runs_matching` ora
prendono `pipeline` e lo passano a `runs_for` (che già lo richiedeva) - `n_components_options`
usava anche `params["n_components"]` a indicizzazione diretta, mai `NO_N_COMPONENTS`, quindi
sarebbe comunque esploso con `KeyError` sul primo run `clustering.py` incontrato: ora usa
`.get(..., NO_N_COMPONENTS)` ovunque, coerente col resto del modulo. Aggiunto un vero
`dcc.Dropdown` "Pipeline" (era testo statico) in
[src/analysis/embedding_app.py:642-648](src/analysis/embedding_app.py#L642), cablato con un
nuovo callback `_update_pipeline_picker` e propagato a tutti i callback a cascata sotto.
Verificato dal vivo contro `results/` reale: `discover_production_runs` + `build_app` non
sollevano più eccezioni, `pipeline_options`/`method_options` restituiscono i valori attesi.
Design volutamente generico (nessun nome di pipeline/modalità hardcoded nei callback - tutto
deriva da `PRODUCTION_PIPELINES`/dai run scoperti su disco, come richiesto). Test:
`tests/unit/test_embedding_app.py` riscritto (42 test, incl. 9 nuovi mirati al bug: scoperta di
run misti dim_reduction+clustering, dropdown Pipeline reale, sentinel NO_N_COMPONENTS per
clustering) + `tests/unit/test_embedding_coloring.py::test_registry_has_expected_modes`
allineato (mancava `cluster_label`). Suite intera: **632 passed, 12 skipped, 0 failed**
(esclusi i 2 file `bcblib`-dipendenti).

---

### 3. `build_lesion_matrix`: check "già allineato" ignora l'affine

**Pipeline**: `build_lesion_matrix` — [src/features/lesion.py:229](src/features/lesion.py#L229), [:102](src/features/lesion.py#L102)

**Difetto**: il check di allineamento confronta solo la *shape* delle immagini, mai l'affine —
due immagini con la stessa shape ma affine diverso vengono trattate come già co-registrate,
producendo un disallineamento anatomico silenzioso tra lesione e spazio di riferimento.

**Verificato sui dati reali (17/08)**, script in
`scratchpad/repro_affine_only_check.py`: su 1150 file lesion mask della coorte attuale
(config di produzione corrente), 202 hanno shape+affine identici al reference, 948 hanno shape
diversa (correttamente resampiati dal codice attuale), **0 rientrano nella zona di bug** (shape
uguale, affine diversa). Il difetto non produce quindi disallineamento osservabile *oggi* su
questa coorte specifica, ma resta strutturale: un dataset futuro/aggiornato con stessa
risoluzione voxel ma diversa origine/orientamento lo innescherebbe silenziosamente, senza log né
eccezione.

**Stato: Implementato (17/08).** Nuovo helper `_needs_resample(img, reference_img)` -
[src/features/lesion.py:87-97](src/features/lesion.py#L87) - confronta shape **e** affine
(`np.allclose`, tolleranza 1e-3), usato sia in `load_and_resample_atlas` che in
`_load_and_binarize_lesion`. **Nessun effetto sui dati odierni**: lo script di riproduzione
conferma 0 soggetti nella "zona di bug" nella coorte attuale (vedi finding sopra), quindi
questo fix non altera nessun output di produzione esistente - è una rete di sicurezza per dati
futuri. Test di regressione geometrico
`test_load_and_binarize_lesion_resamples_when_affine_differs_but_shape_matches` (maschera
sintetica, stessa shape del reference ma origine spostata di un voxel/2mm lungo x) - verificato
fallire sul codice pre-fix (`assert np.uint8(1) == 0` → il voxel leso restava silenziosamente
alla posizione grezza invece di essere ricollocato dal resample), passa col fix (il voxel
finisce nella posizione fisicamente corretta, confermata indipendentemente via
`nilearn.resample_to_img` diretto). Suite intera: 632 passed, 0 failed.

---

### 4. `build_lesion_matrix`: dataset con path errato contribuisce silenziosamente 0 soggetti

**Pipeline**: `build_lesion_matrix` — [src/features/lesion.py:185](src/features/lesion.py#L185)

**Difetto**: `Path.glob` su una directory inesistente ritorna `[]` senza sollevare eccezione — un
dataset con nome/path sbagliato o non ancora recuperato da `retrieve_data.py` sparisce
dall'intera coorte senza nessun segnale.

**Stato: Implementato (17/08).** `_discover_lesion_files` ora controlla `subject_dirs` (prima di
applicare `group_filter`, per non confondere "dataset irraggiungibile" con "dataset
legittimamente senza soggetti nel gruppo richiesto") e solleva `FileNotFoundError` se è vuoto —
[src/features/lesion.py:192-206](src/features/lesion.py#L192). Test di regressione
`test_build_lesion_matrix_missing_dataset_root_raises` in
[tests/unit/test_features_lesion.py](tests/unit/test_features_lesion.py) — verificato fallire
(`DID NOT RAISE`) sul codice pre-fix via `git stash`, passa col fix.

---

### 5. `build_fc_matrix`: file stale in `masked_fc/` sopravvivono a un re-run

**Pipeline**: `build_fc_matrix` — [src/pipeline/mask_fc.py:64](src/pipeline/mask_fc.py#L64), [src/features/functional.py:260](src/features/functional.py#L260)

**Difetto**: `overwrite=True` non fa `rmtree` della directory di output — file di un run
precedente restano e finiscono silenziosamente inclusi nella matrice finale di
`build_fc_matrix.py`. Riprodotto empiricamente (lesson #18, già risolto altrove per un caso
gemello).

**Esempio concreto (17/08)**: run 1 con `group_filter=None` include per errore soggetti HC
"trapelati" sotto `manual_masks`/`features` (scenario reale, lesson #14). Ci si accorge
dell'errore, si stringe la config a `group_filter=["ST"]`, si rilancia con `overwrite=True`
sullo stesso `output_root`/`session_name`. Il nuovo run correttamente non ricalcola più gli HC —
ma [src/pipeline/mask_fc.py:63](src/pipeline/mask_fc.py#L63) salta l'unico controllo esistente
(`if not config.overwrite and any(...)`) senza mai fare pulizia, e
[src/features/functional.py:260-273](src/features/functional.py#L260) scrive solo
`{subject}_masked_fc.csv` per i soggetti del run corrente — i `sub-XXHCyyyy_masked_fc.csv` del
run 1 restano fisicamente sul disco. `build_fc_matrix.py` legge poi *tutti* i
`*_masked_fc.csv` presenti nella cartella (`discover_masked_fc_files`,
[src/features/functional.py:280-286](src/features/functional.py#L280)) — reintroducendo
silenziosamente esattamente la contaminazione che il fix del `group_filter` doveva eliminare,
senza errore né warning.

**Soluzione proposta (da confermare, non ancora implementata)**: stesso fix già applicato altrove
per lo stesso pattern (lesson #18, `dim_reduction.py::_write_tuning_output`) — in
`mask_fc.py`, quando `config.overwrite=True` e `output_dir` esiste già, `shutil.rmtree(output_dir)`
prima di chiamare `mask_dataset_fc` (che poi ricrea la directory da zero via
`mkdir(parents=True, exist_ok=True)`). Garantisce semantica "tutto o niente": o la directory non
esiste ancora, o contiene esattamente i file scritti dal run corrente, mai un misto.

**Stato: Chiuso, vedi HIGH #10 (18/08) — stessa soluzione proposta qui implementata lì, testo
di stato non aggiornato in questa sezione fino ad ora (trovato per inconsistenza durante il
giro LOW del 21/08).**

---

### 6. `dim_reduction`: `enrich_metadata_with_lesion_info` blocca produzione su matrici non binarie

**Pipeline**: `dim_reduction` — [src/pipeline/dim_reduction.py:135](src/pipeline/dim_reduction.py#L135)

**Difetto**: la modalità produzione va in errore su qualunque matrice non binaria — rompe la
riproduzione della metodologia Thiebaut de Schotten 2020 (`pca_varimax`), che il README cita
esplicitamente come motivazione dell'atlante combinato. Riprodotto end-to-end.

**Perché si rompe, nel dettaglio (17/08)**: `_run_production` ([src/pipeline/dim_reduction.py:135](src/pipeline/dim_reduction.py#L135))
chiama `enrich_metadata_with_lesion_info(metadata, X)` **incondizionatamente**, per qualunque
`reduction_method`. Quella funzione ([src/features/clinical.py:241-248](src/features/clinical.py#L241))
valida esplicitamente `np.all((X == 0) | (X == 1))` e solleva `ValueError` altrimenti — corretto
in isolamento (§0: `lesion_volume_voxels = X.sum(axis=1)` è un conteggio voxel solo se X è
binaria), ma la produzione con `parcellate: true`/`parcel_aggregation: "fraction_lesioned"`
(build_lesion_matrix.py) genera esattamente una matrice continua in [0,1] — che è il tipo di
input che `pca_varimax` è *pensato* per ricevere (proporzione di danno per ROI, come nel paper).
Risultato: la pipeline fallisce PRIMA di scrivere qualunque embedding/plot, anche se `embed()`
stesso avrebbe funzionato perfettamente su quella X. Riprodotto dal vivo
(`scratchpad/repro_parcellated_pca_varimax.py`):
```
ERROR: enrich_metadata_with_lesion_info requires a strictly binary (0/1) X - ...
RETURN CODE: 1
```

**Stato: Implementato e chiuso (17/08).** `build_lesion_matrix()` calcola **sempre**
`lesion_volume_voxels` da `X_voxelwise` (prima di un'eventuale parcellazione —
[src/features/lesion.py:68-79](src/features/lesion.py#L68)) — nessuna dipendenza nuova da
`assets/metadata/*.tsv` dentro `build_lesion_matrix()`. `lesion_side`/`nihss`/altre variabili
cliniche disaccoppiate in [src/pipeline/enrich_lesion_metadata.py](src/pipeline/enrich_lesion_metadata.py) (vedi finding #7). La
chiamata a `enrich_metadata_with_lesion_info` è stata **rimossa** da `dim_reduction.py`
(produzione + il ramo `save_tuning_embeddings` in tuning) e da `dim_reduction_clustering.py` —
`metadata` ora passa inalterata da `input_path` a valle, mai ricalcolata. La funzione
`enrich_metadata_with_lesion_info` stessa resta in `src/features/clinical.py` ma non è più
chiamata da nessuna pipeline (nessun consumatore rimasto — verificato via `grep -rn`).

**Verificato dal vivo**: `scratchpad/repro_parcellated_pca_varimax.py` (produzione
`pca_varimax` su matrice parcellata continua, `n_components=viz_n_components=2`) →
`RETURN CODE: 0` (prima: `ERROR: ... requires a strictly binary (0/1) X`, `RETURN CODE: 1`).

Test: `tests/unit/test_features_lesion.py` — nuove asserzioni su `metadata["lesion_volume_voxels"]`
sia nel caso voxel-wise che parcellato (`[2, 1, 1]` in entrambi, a dimostrazione che il valore
resta il vero conteggio voxel anche quando l'output finale è continuo). Suite intera: **646
passed, 0 failed, 12 skipped** (esclusi i 2 file `bcblib`-dipendenti; 1 test in
`test_clustering_pipeline.py` aggiornato per il nuovo schema di colonne, non era un bug — solo
un'assert su uno schema ormai cambiato di proposito).

---

### 7. `dim_reduction`: color mode "volume" senza guard di binarietà

**Pipeline**: `dim_reduction` — [src/analysis/embedding_coloring.py:58](src/analysis/embedding_coloring.py#L58)

**Difetto**: su dati continui (non binari) produce silenziosamente un numero sbagliato, nessuna
eccezione. Riprodotto.

**Dove esattamente (17/08)**: `COLOR_MODES["volume"].compute = lambda metadata, X: X.sum(axis=1)`
([src/analysis/embedding_coloring.py:58-70](src/analysis/embedding_coloring.py#L58)) — zero
controllo di binarietà, a differenza di `enrich_metadata_with_lesion_info` che fa lo stesso
identico calcolo con un guard esplicito (finding #6). Chiamato *live* su X da
`write_embedding_plots`/`write_embedding_grid`
([src/analysis/embedding_plots.py:83,131](src/analysis/embedding_plots.py#L83)) — non legge mai
la colonna già persistita `lesion_volume_voxels`. Il tuning di default
(`save_tuning_embeddings=False`, il caso comune) non chiama mai
`enrich_metadata_with_lesion_info` (vedi [src/pipeline/dim_reduction.py:210-215](src/pipeline/dim_reduction.py#L210)) — quindi per un tuning `pca_varimax` con `color_by: ["volume"]`
su matrice parcellata, questa è l'UNICA guardia che dovrebbe esistere e non esiste. Riprodotto
(`scratchpad/repro_volume_mode_no_guard.py`, X continua random in [0,1], 372 colonne):
```
no exception raised. 'volume' values (meaningless for continuous X):
[197.30484 188.96724 183.68463 ...]
```
Numeri plausibili come "voxel count" ma in realtà somma di frazioni casuali — plottati come
"lesion volume (voxels)" su colorbar log-scale, senza nessun segnale che siano privi di senso.

**Punto (a) — segnalare con eccezione**: proposta immediata, stesso guard di
`enrich_metadata_with_lesion_info` dentro `"volume"`'s compute (o appena prima di chiamarlo in
`embedding_plots.py`) — impedisce il numero silenziosamente sbagliato. Effetto collaterale: la
colorazione "volume" diventerebbe sempre assente (catturata dal `try/except Exception` già
presente in `write_embedding_plots`/`write_embedding_grid`, che logga WARNING e salta quel solo
plot) per qualunque run parcellato — non fallisce l'intero run, ma "volume" non è mai
disponibile per `pca_varimax`.

**Punto (b) — gestione alternativa per il caso non binario (da decidere insieme)**: 3 opzioni,
nessuna ancora scelta:
  - **(A)** solo l'eccezione sopra — "volume" semplicemente non esiste mai per run parcellati.
    Più semplice, ma perde una colorazione potenzialmente utile anche per `pca_varimax`.
  - **(B)** disaccoppiare "volume" da X: farlo leggere `metadata["lesion_volume_voxels"]` già
    persistita (come già fanno "dataset"/"side"), invece di ricalcolare da X — richiede che
    `build_lesion_matrix.py` calcoli e persista `lesion_volume_voxels` nella metadata **anche**
    quando `parcellate=True` (il dato binario voxel-wise esiste comunque un istante prima della
    parcellazione, dentro `build_lesion_matrix()`). Consistente col resto del registro, valido
    anche per `pca_varimax` in produzione.
  - **(C)** vietare esplicitamente `"volume"` in `color_by` quando la config ha
    `parcellate: true`, validato al caricamento della config (fail-fast esplicito invece di un
    plot mancante silenzioso via except).
  Opinione: (B) è la soluzione corretta a lungo termine (coerente con come "dataset"/"side" già
  funzionano, nessuna dipendenza da quale X è stata usata per la riduzione), ma tocca
  `build_lesion_matrix.py` oltre a `embedding_coloring.py` - da confermare prima di procedere.

**Stato: Opzione (B) scelta e la sua metà "produttrice" implementata (17/08)** —
`build_lesion_matrix()` calcola sempre `lesion_volume_voxels` (vedi finding #6). **La metà
"consumatrice" manca ancora**: `"volume"`'s `compute` in `embedding_coloring.py` continua a fare
`X.sum(axis=1)` dal vivo, non legge `metadata["lesion_volume_voxels"]` — quindi il bug è ancora
presente com'era (nessuna guardia, nessuna eccezione) finché quella riga non viene cambiata.

Per `lesion_side`/`nihss`/altre variabili cliniche (non toccati da questo finding ma stesso
pattern) esiste ora un'alternativa concreta e testata, passata per 4 iterazioni di design con
l'utente prima di arrivare alla forma finale: [src/pipeline/enrich_lesion_metadata.py](src/pipeline/enrich_lesion_metadata.py) — pipeline
a `--config` (non argomenti CLI diretti come nella primissima versione — rivisto su richiesta,
per essere coerente con tutte le altre pipeline del repo: `metadata_path` di sola lettura,
output sempre in una cartella nuova e indipendente `output_root/<dd-mm>_<session_name>`, mai una
mutazione in place). Fa il join di variabili cliniche configurabili
(`age`/`sex`/`education`/`lesion_side`/`clinical_date`/`NIHSS`/qualunque colonna esista) da
`assets/metadata/*_participants_lesions.tsv`, con un report di copertura scritto **prima** di
scrivere qualunque output (`summaries/enrich_lesion_metadata/`) e un controllo esplicito a due
livelli: dataset senza tsv o
soggetto assente nel tsv → errore duro, nessuna scrittura; variabile assente nel tsv di un solo
dataset (gap strutturale noto, es. PASPORT senza NIHSS/lesion_side) → quel dataset prende NaN per
quella colonna, non blocca. Logica condivisa in `src/features/clinical.py`
(`check_participant_variable_coverage`/`join_participant_variables`), mai duplicata tra script e
funzione. Output scritto atomicamente (dir temporanea + rename), mai una mutazione in place.
`--dry-run` per vedere il report senza scrivere. `jobs/run_enrich_lesion_metadata.sh` aggiunto.

`compute_volume: true` (facoltativo, un solo campo bool in config) somma direttamente il
`matrix.npy` che `save_matrix` scrive sempre accanto a `metadata.csv` — **niente rilettura di
maschere grezze**: prima idea (config a 7 campi tipo `build_lesion_matrix.json`, poi un campo
solo `lesion_discovery_config` puntato a `build_lesion_matrix.json`) scartata dopo discussione
con l'utente — per una matrice voxel-wise (`21-07_s1.1`) `matrix.npy` **è già** la matrice
binaria (le colonne scartate da `_drop_constant_features` sono 0 per tutti, non alterano nessuna
somma), quindi rileggere le maschere grezze non serviva mai per il caso reale. Solo per una
matrice parcellata (continua, `fraction_lesioned`) l'informazione voxel-per-voxel è
irrimediabilmente persa — in quel caso lo script solleva un errore esplicito invece di tentare
un fallback. Risultato pratico: sulla coorte reale (1150 soggetti), passato da 45s (rilettura
maschere) a 3.3s (somma diretta della matrice già su disco).

Test: 8 in `tests/unit/test_features_clinical.py` (coverage report, join multi-colonna, gap
strutturale → NaN + warning, dataset/soggetto irrisolvibile → eccezione) + 10 in
`tests/integration/test_enrich_lesion_metadata_pipeline.py` (E2E via `main()`: successo,
`compute_volume` da matrice reale, matrice mancante/parcellata → eccezione, dry-run, fallimento
duro senza scrittura, gap strutturale non bloccante, overwrite, `metadata_path` mancante,
convenzione colonne identica a `results/lesion/dim_reduction/**/metadata.csv`) + 3 in
`tests/unit/test_build_config.py`.

**Eseguito per davvero (17/08)**: `data/derived/clinical_metadata/17-08_s1/metadata.csv` (1150
soggetti) generato da `21-07_s1.1`; le 4 colonne nuove (`age`/`sex`/`education`/`clinical_date`)
copiate a mano (merge per `subject_id`, verificato 0 mismatch su `lesion_side`/`nihss`/
`lesion_volume_voxels` già presenti) in tutti e 8 i `metadata.csv` sotto
`results/lesion/dim_reduction/`. `lesion_side` usa il sentinella `"unknown"` (mai `NaN` —
romperebbe il color mode categorico), `NIHSS`→`nihss` rinominata in output, entrambi via
funzioni dedicate (`join_lesion_side`, generico per il resto) non il joiner generico, per
garantire byte-per-byte la stessa convenzione già in uso.

**`embedding_coloring.py` collegato (17/08, chiude anche la parte rimanente di questo
finding)**: `ColorMode` ha ora un campo `column` (non più `compute` callable) — `"volume"`,
`"side"`, `"nihss"`, `"dataset"`, `"cluster_label"` leggono tutti direttamente da `metadata`
via la nuova `color_values()`, mai ricalcolati da X o rigiuntati da tsv. Collassa i due registri
precedenti (`compute()` per i writer di produzione/tuning, `PERSISTED_COLUMN_BY_MODE` per
`embedding_app.py`) in uno solo. `X` rimosso dalla firma di `write_embedding_plots`/
`write_embedding_grid` (non più necessario, nessun color mode lo usa più) — aggiornati tutti i
chiamanti (`dim_reduction.py`, `dim_reduction_clustering.py`) e l'altro consumatore
(`scripts/replot_dim_reduction.py`, stesso `PERSISTED_COLUMN_BY_MODE` rimosso).

**Verificato dal vivo**: `scratchpad/repro_volume_mode_no_guard.py` — `color_values` su
metadata senza `lesion_volume_voxels` → `ValueError` esplicito (prima: nessuna eccezione,
numero sbagliato); su metadata con la colonna già presente → valori corretti, verbatim,
indipendenti da X.

Test aggiornati per la nuova API in `test_embedding_coloring.py` (riscritto,
`mode.compute()` → `color_values()`), `test_embedding_plots.py` (riscritto, firma senza `X`),
più i fixture di 3 test di integrazione (`test_dim_reduction_pipeline.py`,
`test_dim_reduction_clustering_pipeline.py`) che simulavano l'arricchimento con un
`participants.tsv` fittizio ora sostituiti da una patch diretta di `metadata.csv` (coerente col
nuovo disaccoppiamento). Suite intera: **654 passed, 0 failed, 12 skipped**.

---

### 8. `dim_reduction_clustering`: refit `embedding_for_viz` non valido per `pca_varimax`

**Pipeline**: `dim_reduction_clustering` — [src/analysis/reduction.py:172](src/analysis/reduction.py#L172)

**Difetto**: la rotazione varimax non è "nested" come gli autovettori PCA grezzi — il refit a
dimensionalità diversa non è matematicamente equivalente. Dormiente oggi (`pca_varimax` non è
nemmeno ancora presente in `config/registry/params_reduction.json` — nessun run, di tuning o
produzione, esiste oggi), esploderà (in senso di risultato silenziosamente fuorviante, non di
crash) al primo caso reale.

**Chiarimento importante (17/08, risposta diretta alla domanda "vale anche per UMAP/t-SNE?"):
NO, il refit è corretto e voluto per UMAP/t-SNE/PaCMAP** — è precisamente il fix del pattern
lesson #16 (mai `embedding[:, :2]`, sempre un refit reale). Per questi 3 metodi un secondo fit a
`viz_n_components` con stessi `metric`/`n_neighbors`/`min_dist`/`random_state` è, per citare il
docstring, "UMAP/t-SNE's own best-effort layout for exactly that many dimensions" - una vista
onesta e indipendentemente valida, non tenuta a coincidere con il fit a piena dimensionalità (per
questi metodi nessuno interpreta "dim 1"/"dim 2" come assi semanticamente fissi). Per `pca`
semplice, il refit è anche matematicamente equivalente a uno slice (proprietà nested/greedy della
varianza di PCA) - il docstring lo dice esplicitamente.

**Il problema è specifico di `pca_varimax`**, per un motivo diverso da "non-nested" generico: la
rotazione varimax ottimizza un criterio ("simple structure") *congiuntamente su tutti i K
componenti trattenuti* — non è una rotazione asse-per-asse. Un refit a `viz_n_components=2` con
`n_components` di produzione es. 10 non estrae "i primi 2 fattori ruotati veri" - risolve un
problema di ottimizzazione completamente diverso (ruotare 2 assi vs ruotare 10), producendo 2
fattori senza nessuna relazione con "fattore 1"/"fattore 2" della soluzione di produzione a 10
componenti. A differenza di UMAP/t-SNE, qui l'interpretazione conta: l'intero punto della
metodologia Thiebaut de Schotten 2020 è che ogni fattore ruotato ha un significato anatomico
specifico (fattore 1 = un sistema, fattore 2 = un altro...) - un plot 2D etichettato
"pca_varimax dim 1/dim 2" che in realtà mostra una rotazione a K=2 indipendente rischia di essere
letto come "una vista dei fattori reali di produzione", quando non lo è affatto.

**Decisione presa (17/08, confermata dall'utente dopo due chiarimenti mirati)**: il refit resta
**solo** per `umap`/`tsne`. Esclusi esplicitamente anche `pacmap` (pur essendo anch'esso basato
su grafo di vicinato, stessa logica di umap/tsne in teoria - escluso comunque su richiesta
esplicita, per non cambiare il comportamento di un metodo di produzione reale senza conferma) e
`pca` semplice (per cui il refit sarebbe in realtà equivalente allo slice, ma escluso comunque
per coerenza con la lettura stretta "solo umap e t-sne"). Per i 3 metodi esclusi, quando
`n_components` di produzione ≠ `viz_n_components`: **eccezione esplicita** (non un plot mancante
silenzioso), coerente con §0 code_standards.

**Stato: Implementato (17/08).** Nuovo `_REFITTABLE_FOR_VIZ = frozenset({"umap", "tsne"})` -
[src/analysis/reduction.py:156-180](src/analysis/reduction.py#L156) - `embedding_for_viz` ora
solleva `ValueError` per qualunque altro metodo quando le dimensioni non coincidono già. Questo
introduce un nuovo percorso di eccezione in 2 call site che prima non erano protetti da
try/except ([src/pipeline/dim_reduction.py:133](src/pipeline/dim_reduction.py#L133) in
produzione, [src/pipeline/dim_reduction_clustering.py:157](src/pipeline/dim_reduction_clustering.py#L157))
- avrebbero altrimenti propagato come traceback grezzo invece del consueto
`logging.error`+`return 1`; entrambi ora avvolti (il call site gemello in tuning,
`_build_grid_blocks`, era già coperto da un try/except `ValueError` esistente attorno a
`_write_tuning_output`). Test: `test_reduction.py` - un test rimosso (equivalenza
refit/slice per pca, non più applicabile visto che pca ora solleva) sostituito da 4 nuovi
(refit reale per t-SNE; eccezione parametrizzata su pca/pca_varimax/pacmap; pass-through
quando le dimensioni già coincidono, per ognuno dei 3 metodi esclusi). Suite intera: 632
passed, 0 failed. Dormiente in produzione: `pca_varimax` non ha ancora nessuna config con
`n_components` reale, quindi questo comportamento non è ancora stato esercitato da un run vero.

---

## HIGH

### 9. `mask_fc`: nessun isolamento per-soggetto nel loop di masking

**Target**: [src/features/functional.py:264-274](src/features/functional.py#L264)

```python
rows = []
for subject, (lesion_path, fc_path) in subject_files.items():
    lesion_img = nib.load(lesion_path)
    fc = pd.read_csv(fc_path, sep="\t", index_col=0)
    if list(fc.index) != list(node_names):
        raise ValueError(f"{subject}: FC node order in {fc_path} does not match the atlas order")
    fc_masked, compromised_names = mask_subject_fc(...)
    fc_masked.to_csv(output_dir / f"{subject}_masked_fc.csv")
    rows.append(...)
```

Nessun `try/except` per-soggetto: `nib.load`, `pd.read_csv` o il `raise ValueError` sull'ordine
dei nodi propagano fuori dal loop senza isolamento (lesson #21 — stesso pattern già corretto
altrove, es. `src/sdc/status.py::read_all_statuses`).

**Esempio concreto**: `mask_dataset_fc` su `Yan300TianS2Buckner7N` (WashU, ~200 soggetti). Il
250° soggetto in ordine alfabetico ha un file FC scritto da XCP-D con una riga di header extra
(corruzione nota su un run XCP-D interrotto e ripreso) — `fc.index` non combacia più con
`node_names` e il `ValueError` esplicitamente sollevato per QUEL soggetto abortisce l'intera
combo: i 249 soggetti già mascherati correttamente in questo stesso ciclo `for` vengono comunque
scartati (mai scritti su disco, dato che `mask_dataset_fc` ritorna solo a fine loop) — un singolo
file malformato costa il ricalcolo completo della combo, non solo di quel soggetto.

**Stato: Implementato (18/08).** `mask_dataset_fc` ora avvolge il corpo per-soggetto in
`try/except (OSError, ValueError, ImageFileError, pd.errors.ParserError)`, accumula i
fallimenti in un dict `failed: dict[str, str]` (subject_id -> motivo) e continua con gli altri
— firma cambiata a `(summary, missing_lesion, excluded_by_group, failed)`, `mask_fc.py`
aggiornato per loggare `failed` come WARNING. Test: `test_mask_dataset_fc_one_bad_subject_does_not_abort_the_others`
(`tests/unit/test_features_functional.py`) — un soggetto con FC node order scrambled, verificato
fallire su codice pre-fix (l'intero `ValueError` si propagava, `sub-01` mai scritto), passa col
fix (`sub-01` scritto, `sub-02` in `failed` con motivo).

### 10. `mask_fc`: output dir non ripulita con `overwrite=True`

**Target**: [src/pipeline/mask_fc.py:63-71](src/pipeline/mask_fc.py#L63)

```python
for combo in config.atlas_combos:
    output_dir = config.output_root / combo
    if not config.overwrite and any(output_dir.glob("*_masked_fc.csv")):
        logging.error(...)
        return 1
    ...
    summary, missing_lesion, excluded_by_group = mask_dataset_fc(..., output_dir=output_dir, ...)
```

Quando `overwrite=True` il controllo viene semplicemente saltato — non c'è nessun
`shutil.rmtree(output_dir)` prima di richiamare `mask_dataset_fc` (che scrive via
`output_dir.mkdir(parents=True, exist_ok=True)`, mai pulendo). Stesso pattern esatto del
CRITICAL #5, ma qui il gap è nella cartella `masked_fc/<combo>/` stessa, non solo nel
consumatore a valle.

**Esempio concreto**: run 1 con `group_filter=None` (typo, dovrebbe essere `["ST"]`) scrive
`sub-STUNIPD0001_masked_fc.csv`...`sub-HCUNIPD0099_masked_fc.csv` per una combo. Ci si accorge
dell'errore (soggetti HC "trapelati" — lesson #14), si corregge `group_filter=["ST"]` nel
config e si rilancia con `overwrite=True` sullo stesso `output_root`/`session_name`. Il nuovo
run scrive solo i file `*_masked_fc.csv` dei soggetti ST — ma i `sub-HCUNIPD*_masked_fc.csv`
del run 1 restano fisicamente in `masked_fc/<combo>/`, pronti per essere raccolti dal
`build_fc_matrix.py` (CRITICAL #5) o da qualunque altra ispezione manuale della cartella.

**Stato: Implementato (18/08) — chiude anche CRITICAL #5, stesso gap.** `mask_fc.py`'s
`main()` ora fa `shutil.rmtree(output_dir)` prima di richiamare `mask_dataset_fc` quando
`output_dir.exists()` e `config.overwrite=True` (semantica "tutto o niente", identica al
pattern già usato altrove per lo stesso problema, lesson #18). Test:
`test_mask_fc_overwrite_true_removes_stale_files_from_previous_run`
(`tests/integration/test_mask_fc_pipeline.py`) — run 1 con `group_filter=None` include un
soggetto HC, run 2 con `group_filter=["ST"]`+`overwrite=True` sullo stesso `output_root`;
verificato fallire su codice pre-fix (il file HC restava), passa col fix (rimosso).

### 11. `dim_reduction`: `TypeError` da iperparametro non riconosciuto non catturato

**Target**: [src/pipeline/dim_reduction.py:109-124](src/pipeline/dim_reduction.py#L109)

```python
try:
    params, tag = load_method_params(config.params_file, config.reduction_method)
    if params.get("metric") in SUPPORTED_BINARY_METRICS:
        require_binary_matrix(X, params["metric"])
except (FileNotFoundError, ValueError) as exc:
    logging.error(str(exc))
    return 1
...
embedding = embed(config.reduction_method, X, params, distance_cache)   # <- nessun try/except
```

`load_method_params` è protetta, ma la chiamata a `embed()` subito dopo (che fa
`umap.UMAP(**params)`/`TSNE(**params)`/`PCA(**params)`) non lo è.

**Esempio concreto**: `config/registry/params_reduction.json`'s `umap.params` contiene, per un
copia-incolla mal fatto durante una sessione di tuning, la chiave `n_neighbor` invece di
`n_neighbors`. `load_method_params`/`require_binary_matrix` non validano il *contenuto* dei
parametri (solo che il file/metodo esistano), quindi il `TypeError:
UMAP.__init__() got an unexpected keyword argument 'n_neighbor'` sollevato da `umap.UMAP(**params)`
propaga come traceback grezzo fuori da `main()`. Poiché `attach_file_handler(log_path)` è già
stato agganciato alla riga 90, ci si aspetterebbe che l'errore finisca nel file di log — ma
un'eccezione Python non catturata va sull'excepthook di default (stderr), mai attraverso il
modulo `logging`: il file di log esiste (creato vuoto da `attach_file_handler`) ma non contiene
nulla, mentre il processo termina con un traceback su console — violazione diretta di §6
("ogni eccezione loggata con contesto completo"). Un job SLURM che redirige solo lo stderr di
sistema in `-e` lo vedrebbe comunque, ma chi si aspetta di trovare la causa nel `.log`
dedicato del pipeline resterebbe senza risposta.

**Stato: Implementato (18/08).** La chiamata a `embed()` in `_run_production` è ora avvolta
in `try/except (TypeError, ValueError)`, `logging.error` + `return 1`, con il messaggio che
include `params` per riconoscere subito la chiave errata. Test:
`test_dim_reduction_unrecognized_hyperparameter_returns_1_not_raw_traceback`
(`tests/integration/test_dim_reduction_pipeline.py`) — `params_reduction.json` con
`"n_neighbor"` invece di `"n_neighbors"`, verificato fallire su codice pre-fix
(`TypeError` grezzo da `umap.UMAP(**params)`), passa col fix (`return 1`, nessun `dr_out/`
creato).

### 12. `dim_reduction`: suite rossa al momento dell'audit

Alla data dell'audit (17/08, stesso commit del CRITICAL #2), `test_embedding_coloring.py::
test_registry_has_expected_modes` falliva: il test si aspettava `cluster_label` nel registro
`COLOR_MODES` (`src/analysis/embedding_coloring.py`) che a quel commit non c'era ancora — la
migrazione a metà del CRITICAL #2 aveva aggiornato l'app ma non il registro dei color mode.

**Verifica dal vivo (oggi, in questa sessione)**: `conda run -n nemesis python -m pytest
tests/unit/test_embedding_coloring.py::test_registry_has_expected_modes -q` → `1 passed`. Il
fix del CRITICAL #7 (`ColorMode` con `column`, registro con `cluster_label` incluso, test
riscritto) ha risolto questo finding come effetto collaterale — **non riproducibile più sullo
stato attuale del branch**, andrebbe chiuso in triage invece di restare "Aperto" senza verifica.

**Stato: Chiuso in triage (18/08).** Suite intera confermata verde end-to-end del lavoro di
questa sessione (merge `docs/dr-clustering-literature-migration` + tutti i fix HIGH sotto):
**698 passed, 0 failed, 12 skipped**. Nessuna azione di codice necessaria.

### 13. `clustering`: metriche di validazione sempre euclidee

**Target**: [src/analysis/clustering_tuning.py:104-109](src/analysis/clustering_tuning.py#L104)

```python
return {
    "silhouette": float(silhouette_score(non_noise_X, non_noise_labels)),
    "calinski_harabasz": float(calinski_harabasz_score(non_noise_X, non_noise_labels)),
    "davies_bouldin": float(davies_bouldin_score(non_noise_X, non_noise_labels)),
    "noise_fraction": noise_fraction,
}
```

Le 3 chiamate passano `non_noise_X` (le feature grezze) senza mai un parametro `metric=` —
`silhouette_score` di default usa la distanza euclidea. Stesso pattern di lesson #15
(`trustworthiness` in `tuning.py`, già corretto lì).

**Esempio concreto**: un tuning `spectral` con `affinity="precomputed"` alimentato da una
matrice di distanza Jaccard/Dice (coerente con `params_reduction.json`'s `umap.metric=jaccard`,
vedi finding #33) produce cluster ottimizzati per la struttura di vicinato *Jaccard* — ma
`compute_clustering_metrics` valuta ogni combinazione del tuning con silhouette/Calinski-
Harabasz/Davies-Bouldin calcolati sulla distanza *euclidea* di quello stesso X binario. Un
partizionamento che separa bene i soggetti secondo l'overlap di voxel (Jaccard) può ottenere un
punteggio euclideo mediocre (e viceversa) — il tuning finisce per scegliere l'iperparametro che
sembra migliore secondo un metro diverso da quello che il clustering ha effettivamente usato,
silenziosamente, un numero plausibile senza nessun segnale che sia calcolato contro il metro
sbagliato.

**Verificato sui dati reali (18/08)**: produzione `clustering.json` gira sempre con
`reduced_data: true` su un embedding PaCMAP (spazio Euclideo per costruzione) e `spectral` usa
`affinity="nearest_neighbors"` (mai `"precomputed"`) — nessun mismatch attivo oggi, a
differenza dell'esempio ipotetico sopra. Rimane comunque un difetto reale, dormiente.

**Decisione presa con l'utente (18/08)**: a differenza di `dim_reduction`'s `metric` (lesson
#15, una singola chiave uniforme presente su ogni metodo), il clustering non ha un campo
"metric" uniforme — KMeans/Ward/GMM/HDBSCAN non hanno affatto questo concetto (Ward *richiede*
Euclidea). Scelto quindi un **guard esplicito** (opzione più semplice delle 3 proposte) invece
di un thread-through generico.

**Stato: Implementato (18/08).** `compute_clustering_metrics` prende ora un `combo_params:
dict | None = None` opzionale; `_require_euclidean_compatible` (nuovo helper) solleva
`ValueError` esplicito se `combo_params.get("affinity")` non è in un allow-list registrato
(`None`/`"nearest_neighbors"`/`"rbf"`, lesson #20) o se `combo_params.get("metric")` non è
`None`/`"euclidean"` — mai un guess silenzioso. `run_clustering_tuning_sweep` passa sempre
`combo_params`, già protetto dal `try/except ValueError` esistente in `clustering.py`'s
`_run_one_method_tuning`. Test: 3 nuovi in `tests/unit/test_clustering_tuning.py`
(`affinity="precomputed"`/`metric` non-euclideo → `ValueError`; valori noti-sicuri passano;
propagazione end-to-end attraverso `run_clustering_tuning_sweep`) — verificati fallire su
codice pre-fix (`TypeError`: `combo_params` non ancora un parametro accettato). Suite intera:
698 passed, 0 failed.

### 14. `clustering`/`dim_reduction_clustering`: doc `assign_clusters_from_cooccurrence` invertita

**Target**: [docs/dev/models.md:77](docs/dev/models.md#L77) vs.
[src/analysis/consensus_clustering.py:167-204](src/analysis/consensus_clustering.py#L167)

`docs/dev/models.md` riga 77 dichiara esplicitamente:

> "One deliberate deviation from the paper: cut at a fixed `n_clusters`
> (`fcluster(..., criterion="maxclust")`) rather than the paper's own fixed similarity
> *threshold t*"

Il codice reale fa **l'esatto opposto**:

```python
def assign_clusters_from_cooccurrence(co_occurrence_matrix: np.ndarray, threshold: float) -> np.ndarray:
    ...
    labels = fcluster(linkage_matrix, t=1.0 - threshold, criterion="distance")
```

`criterion="distance"` con un `threshold` (non `n_clusters`) — cioè implementa esattamente la
formula del paper (Fred & Jain 2002, taglio a soglia di co-associazione fissa `t`) che la doc
dice di *non* aver implementato. Confermato anche in `config/registry/params_clustering.json`'s
`"evidence_accumulation"` (`"tag_param": "threshold"`, `"params": {"threshold": 0.5, ...}`, mai
`n_clusters` passato ad `assign_clusters_from_cooccurrence`).

**Esempio concreto**: uno sviluppatore che legge `docs/dev/models.md` prima di estendere
`evidence_accumulation` per un nuovo config (es. per far scegliere un `n_clusters` finale fisso)
si aspetterebbe di dover passare `n_clusters` a `assign_clusters_from_cooccurrence` — ma la
funzione richiede `threshold` e solleverebbe `TypeError`/comportamento diverso da quanto letto,
un'ora persa a ricapire perché il codice "non corrisponde alla doc" che invece descrive il design
mai adottato. **Stato: Aperto.**

### 15. `clustering`: comparison-plot in `main()` fuori da try/except

**Target**: [src/pipeline/clustering.py:132-145](src/pipeline/clustering.py#L132)

```python
if X.shape[1] >= 2:
    comparison_dir = _comparison_dir(config, now)
    plot_clusters_comparison(
        X[:, :2], labels_by_method, comparison_dir / "cluster_comparison.png", ...
    )
    _write_comparison_readme(comparison_dir, config, now)
```

Nessun `try/except` attorno — a differenza di ogni altra fase filesystem-toccante in questo
stesso `main()` (`save_matrix`, `append_run_log_entry`, entrambe protette). Lesson #9.

**Esempio concreto**: `config.clustering_methods = ["kmeans", "hdbscan", "spectral"]`, tutti e 3
i run per-metodo completano con successo (righe 126-130 del loop), ma il disco si riempie
proprio mentre `plot_clusters_comparison` scrive `cluster_comparison.png` (`matplotlib` solleva
`OSError: [Errno 28] No space left on device`) — l'eccezione non è tra quelle catturate da
nessun `except` in quella funzione, propaga fuori da `main()` come traceback grezzo, anche se i
3 run individuali (l'output "vero" della pipeline) sono già scritti correttamente su disco e
loggati in `runs.csv`. **Stato: Aperto.**

### 16. `clustering`: `comparison/` ignora `config.overwrite`

**Target**: [src/pipeline/clustering.py:249-252,315-326](src/pipeline/clustering.py#L249)

```python
def _comparison_dir(config: ClusteringConfig, now: datetime) -> Path:
    return config.output_root / "production" / "comparison" / f"{now.strftime('%d-%m')}_{config.session_name}"
...
def _write_comparison_readme(comparison_dir: Path, config: ClusteringConfig, now: datetime) -> None:
    ...
    comparison_dir.mkdir(parents=True, exist_ok=True)
    (comparison_dir / "config.md").write_text("\n".join(lines) + "\n")
```

Nessun controllo `if comparison_dir.exists() and not config.overwrite: raise` — a differenza di
`save_matrix` (usato dai run per-metodo, righe 173-180) e di `_write_tuning_output` (righe
402-407), `comparison/` scrive sempre e comunque, silenziosamente sovrascrivendo
`cluster_comparison.png`/`config.md` di un run precedente con lo stesso `session_name`.

**Esempio concreto**: `overwrite=False` in config (il default prudente), un run del
14/08 con `session_name="s1"` produce `comparison/14-08_s1/cluster_comparison.png`. Un secondo
run lo stesso giorno, stesso `session_name` per errore di copia-incolla ma con
`clustering_methods` diverso (es. solo `["kmeans", "gmm"]` invece di 3 metodi), fallisce
correttamente su ogni singolo metodo già esistente (`FileExistsError` da `save_matrix`,
`overwrite=False`) — ma se anche solo uno dei metodi genuinamente nuovi va a buon fine e il loop
arriva al blocco comparison, quel blocco sovrascrive silenziosamente il plot/report del run
precedente, l'unico artefatto di questa pipeline che `overwrite=False` non protegge affatto.

**Stato: Implementato (18/08), stesso fix di #15.** Aggiunto il guard `if comparison_dir.exists()
and not config.overwrite: logging.error(...); return 1` prima di scrivere qualunque file di
comparison — stessa semantica di `save_matrix`/`_write_tuning_output`. Test:
`test_clustering_comparison_dir_overwrite_false_rerun_fails_without_clobbering`
(`tests/integration/test_clustering_pipeline.py`) — run 1 con `["kmeans"]`, run 2 stesso
`session_name` con `["agglomerative"]` (metodo genuinamente nuovo, quindi supera il proprio
`save_matrix`); verificato fallire su codice pre-fix (comparison sovrascritto silenziosamente,
`return 0`), passa col fix (`return 1`, `config.md` del run 1 invariato byte-per-byte).

### 17. `clustering`: non produce mai l'HTML interattivo del confronto

**Target**: `src/pipeline/clustering.py` (l'intero modulo)

`clustering.py` chiama solo `plot_clusters_comparison` (statico, PNG) — mai
`plot_clusters_comparison_interactive`, a differenza del sibling `dim_reduction_clustering.py`
che genera sia `cluster_comparison.png` che `cluster_comparison_interactive.html`
([src/pipeline/dim_reduction_clustering.py:201-220](src/pipeline/dim_reduction_clustering.py#L201)).
`docs/dev/models.md` descrive però il comparison output come simmetrico tra i due script
("`plotting.plot_clusters_comparison_interactive` writes a companion
`cluster_comparison_interactive.html` alongside it").

**Esempio concreto**: un utente che ha già usato `dim_reduction_clustering.py` e trovato utile
aprire `cluster_comparison_interactive.html` (hover sui punti, dropdown per metodo) lancia
`clustering.py` con 3 metodi aspettandosi lo stesso file — non lo trova, solo il PNG statico,
senza nessun errore o avviso che segnali la mancanza rispetto a quanto la doc promette per
"the comparison output" in generale.

**Stato: Già risolto, non da questa sessione.** Il merge di `docs/dr-clustering-literature-migration`
(18/08) ha portato `clustering.py` a chiamare già `plot_clusters_comparison_interactive`
subito dopo `plot_clusters_comparison` (vedi `src/pipeline/clustering.py`, blocco comparison) —
confermato dal vivo: `comparison_dir / "cluster_comparison_interactive.html"` scritto e testato
in `test_clustering_end_to_end_multiple_methods_writes_comparison_plot`. Nessuna azione
necessaria in questa sessione oltre ad avvolgerlo in try/except + overwrite guard (#15/#16
sopra).

### 18. `dim_reduction_clustering`: `embed`/clustering non protette da try/except

**Target**: [src/pipeline/dim_reduction_clustering.py:147](src/pipeline/dim_reduction_clustering.py#L147),
[:263](src/pipeline/dim_reduction_clustering.py#L263)

```python
distance_cache: dict[str, np.ndarray] = {}
embedding = embed(config.reduction_method, X, reduction_params, distance_cache)   # <- non protetta
...
try:
    viz_embedding = embedding_for_viz(...)          # <- QUESTA è già protetta (fix CRITICAL #8)
except ValueError as exc:
    ...
...
cluster_labels = CLUSTERING_METHODS[method](embedding, clustering_params)   # <- non protetta (_run_one_method)
```

**Nota di accuratezza**: il fix del CRITICAL #8 ha già avvolto la chiamata a
`embedding_for_viz` (riga 155-161) in un `try/except ValueError` — quella parte del finding
risulta quindi già risolta come effetto collaterale. Restano scoperte le altre due chiamate
citate dal finding originale: `embed()` (riga 147, stesso tipo di gap del finding #11 ma qui
in `dim_reduction_clustering.py`) e `CLUSTERING_METHODS[method](embedding, clustering_params)`
dentro `_run_one_method` (riga 263).

**Esempio concreto**: `params_clustering.json`'s `"hdbscan".params` contiene
`min_cluster_size` con un valore non intero per un typo di config (`"5.0"` invece di `5`,
scritto a mano) — `HDBSCAN(**params).fit_predict(X)` solleva `TypeError`/`ValueError` interno
di sklearn non previsto da nessun `except` circostante in `_run_one_method`, che propaga fuori
da `main()` come traceback grezzo dopo che l'embedding (potenzialmente costoso, un fit UMAP su
1150 soggetti) è già stato calcolato e scartato senza essere mai salvato.

**Stato: parte moot, parte Implementato (18/08).** `embed()` (riga 147 del finding originale)
era specifico a `dim_reduction_clustering.py`, eliminato nel merge di
`docs/dr-clustering-literature-migration` — moot, nessuna azione. `CLUSTERING_METHODS[method](...)`
non protetta invece **non era affatto specifico a quel file**: lo stesso identico gap esiste
tuttora in `src/pipeline/clustering.py::_run_one_method` (produzione) e in
`src/analysis/clustering_tuning.py`'s `run_clustering_tuning_sweep` (tuning, chiamata da
`_run_one_method_tuning`) — trovato durante questa sessione controllando se il finding fosse
davvero interamente moot. Entrambi ora avvolti in `try/except (TypeError, ValueError)`,
`logging.error` + `return None`/`False` (stesso pattern di #11). Test:
`test_clustering_unrecognized_hyperparameter_returns_1_not_raw_traceback`
(`tests/integration/test_clustering_pipeline.py`) — `params_clustering.json` con `"n_cluster"`
invece di `"n_clusters"`, verificato fallire su codice pre-fix (`TypeError` grezzo da
`KMeans(**params)`), passa col fix (`return 1`, nessun `cl_out/` creato).

### 19. `build_lesion_matrix`: `discover_files_by_subject` non incrocia subject_id con la cartella

**Target**: [src/features/subject_discovery.py:56-61](src/features/subject_discovery.py#L56)

```python
dataset_root = Path(data_root) / dataset
files = sorted(dataset_root.glob(glob_pattern))

matches_by_subject: dict[str, list[Path]] = {}
for f in files:
    matches_by_subject.setdefault(f.name.split("_")[0], []).append(f)
```

`subject_id` è ricavato solo dal **nome del file** (`f.name.split("_")[0]`), mai confrontato
con la cartella genitore (`sub-<id>/anat/...`) in cui quel file effettivamente si trova —
variante di lesson #22 (placeholder ripetuto non vincolato alla stessa occorrenza).

**Esempio concreto**: durante un copia-incolla manuale di file per riparare un retrieval
parziale, un file lesion mask di `sub-STUNIPD0042` viene copiato per errore dentro la cartella
`sub-STUNIPD0043/anat/` (nome del file lasciato invariato:
`sub-STUNIPD0042_space-...-mask.nii.gz`, solo la cartella è sbagliata).
`discover_files_by_subject` lo assocerebbe comunque a `sub-STUNIPD0042` (dal nome del file), non
segnalando affatto che il file fisicamente non vive più nella cartella del soggetto che
dichiara — un disallineamento cartella/nome-file che passerebbe silenzioso attraverso l'intera
pipeline.

**Stato: Implementato (18/08).** Nuovo helper `_subject_dir_segment_index(glob_pattern)` trova
il segmento bare `"*"` di `glob_pattern` (la posizione della cartella soggetto, es. indice 1 in
`"manual_masks/*/anat/..."`) — solleva `ValueError` se ce n'è più di uno (ambiguo, lesson #3,
mai il primo per default). Per ogni file scoperto, il `subject_id` derivato dal nome viene
confrontato con quello derivato dalla cartella (`f.relative_to(dataset_root).parts[index]`);
un mismatch solleva `ValueError` con entrambi i valori. Pattern senza segmento `"*"` bare (es.
i glob "flat" già usati da alcuni test) restano non verificabili — `None`, non un errore, dato
che non c'è nulla da incrociare. Test: `test_discover_files_by_subject_folder_filename_mismatch_raises`
+ `test_discover_files_by_subject_nested_glob_folder_matches_filename` (`tests/unit/test_subject_discovery.py`)
— verificato fallire su codice pre-fix (`DID NOT RAISE`), passa col fix. Suite mask_fc/lesion
completa riverificata verde dopo il cambio (55 test).

### 20. `build_lesion_matrix`: `nibabel.ImageFileError` non coperto dal boundary

**Target**: [src/pipeline/build_lesion_matrix.py:68-83](src/pipeline/build_lesion_matrix.py#L68),
[src/features/lesion.py:160,305](src/features/lesion.py#L160)

```python
try:
    X, metadata, non_constant_mask, parcel_ids, excluded_by_group = build_lesion_matrix(...)
except (FileNotFoundError, ValueError) as exc:
    logging.error(str(exc))
    return 1
```

`build_lesion_matrix` chiama internamente `nib.load(path)` sia per l'atlante
(`load_and_resample_atlas`, riga 160) sia per ogni maschera di lesione
(`_load_and_binarize_lesion`, riga 305) — `nibabel.load` solleva `nib.filebasedimages.
ImageFileError` per un file `.nii.gz` troncato/corrotto, un'eccezione che non è né
`FileNotFoundError` né `ValueError` (lesson #9).

**Esempio concreto**: un trasferimento di rete interrotto durante un `retrieve_data.py` lascia
`sub-STUNIPD0512_..._mask.nii.gz` troncato a metà (il file esiste, non è vuoto, ma l'header
gzip è incompleto). Un run successivo di `build_lesion_matrix.py` su quella coorte arriva a
quel soggetto in `_stack_voxel_matrix` e `nib.load` solleva `ImageFileError: ... not a gzip
file` — non catturato da `except (FileNotFoundError, ValueError)`, propaga come traceback
grezzo invece del consueto `logging.error` + `return 1`.

**Stato: Implementato (18/08).** `nib.filebasedimages.ImageFileError` aggiunta alla tupla di
eccezioni catturate in `build_lesion_matrix.py`'s `main()`. Test:
`test_build_lesion_matrix_corrupt_lesion_mask_returns_1_not_raw_traceback`
(`tests/integration/test_build_lesion_matrix_pipeline.py`) — un file `.nii.gz` con contenuto
non valido ("not a gzip file", esattamente il messaggio dell'esempio sopra), verificato fallire
su codice pre-fix (`ImageFileError` grezza), passa col fix (`return 1`, nessun `out/` creato).

### 21. `understanding_umap_report`: NaN nel color mode "nihss" mai gestiti

**Target**: [src/analysis/understanding_umap_report.py:211-235](src/analysis/understanding_umap_report.py#L211)

```python
values = metadata[column].to_numpy(dtype=float)
if mode in _LOG_SCALE_MODES:
    positive = values[~np.isnan(values)]
    if (positive <= 0).any():
        raise ValueError(...)
    values = np.log10(values)
return {"color": values.tolist(), "colorscale": CONTINUOUS_COLORSCALE, "opacity": 1.0}
```

Per `mode="nihss"` (non in `_LOG_SCALE_MODES`), `values` passa direttamente a Plotly senza mai
filtrare/segnalare i `NaN` — a differenza di `embedding_app.py`'s `build_embedding_figure`, che
per lo stesso color mode disegna un trace separato "missing" (`is_missing.any()`). Plotly
riceve `NaN` letterali nella lista `color` serializzata in JSON dentro l'HTML.

**Confermato sui dati reali (17/08)**: 139 occorrenze letterali di `NaN` nell'HTML di
produzione — coerente con PASPORT (uno dei 4 dataset) che non ha NIHSS nel proprio
`participants.tsv` (gap strutturale noto, vedi CRITICAL #7's `enrich_lesion_metadata.py`), ogni
soggetto PASPORT genera un `NaN` qui. `json.dumps({"nihss": [...NaN...]})` produce JSON non
standard (JavaScript `JSON.parse` rifiuta `NaN` nudo) — a seconda di come Plotly.js gestisce
quello specifico punto della color list, il punto può sparire silenziosamente dal grafico o
colorarsi in modo indefinito, senza nessun errore visibile nella pagina.

**Stato: Implementato (18/08), scope ridotto rispetto a embedding_app.py — vedi nota.**
`_color_values_for_mode` converte ora ogni `NaN` in `None` prima di restituire la lista
`"color"` (`json.dumps(None)` → `null`, JSON valido; `json.dumps(nan)` → token `NaN`, non
valido). **Non replica** il trace "missing" separato/grigio di `embedding_app.py` (questo
modulo genera HTML statico con un solo trace per cella + color-switch via JS `setColor()`,
condiviso da tutte le celle della griglia — sdoppiare in 2 trace per modo avrebbe richiesto
un refactor del JS/legend fuori scope per questo fix) — Plotly.js gestisce un `null` in
`marker.color` non disegnando quel punto, non più con un colore arbitrariamente sbagliato.
Test: `test_color_values_for_mode_continuous_nan_becomes_json_safe_none`
(`tests/unit/test_understanding_umap_report.py`) — verificato fallire su codice pre-fix
(`color[2] is nan`, non `None`), passa col fix.

### 22. `understanding_umap_report`: report multi-metrica scritto parzialmente se un metric fallisce

**Target**: [src/analysis/understanding_umap_report.py:1110-1124](src/analysis/understanding_umap_report.py#L1110)

```python
def generate_report(umap_tuning_dir: Path, tsne_tuning_dir: Path, output_dir: Path) -> list[Path]:
    data = load_tuning_data(umap_tuning_dir, tsne_tuning_dir)
    output_paths = []
    for metric in data.metrics:
        output_path = output_dir / f"understanding_umap_{metric}.html"
        build_leaf_page(metric, ..., output_path)   # <- nessun try/except per-metrica
        output_paths.append(output_path)
    return output_paths
```

Nessun cleanup né isolamento per-metrica: se `build_leaf_page` fallisce a metà (es. il
metric successivo) i file già scritti per i metric precedenti restano sul disco, non rimossi.

**Esempio concreto**: `metrics = ["dice", "euclidean"]` (`nested_params=["metric",
"n_components"]`). `understanding_umap_dice.html` viene scritto con successo. Per `euclidean`,
`build_2d_vs_3d_section` solleva `ValueError` perché quel run di tuning non ha mai avuto una
foglia `n_components=3` per quel metric (sweep interrotto prematuramente) — `generate_report`
si interrompe, ma `understanding_umap_dice.html` resta sul disco come se il report fosse
completo. Un secondo lancio della CLI dopo aver corretto il tuning per `euclidean` rigenera
`understanding_umap_dice.html` da capo (nessuna vera perdita), ma nel frattempo chiunque apra
la cartella vede un report "a metà" che sembra completo senza nessun indicatore che manchi
`understanding_umap_euclidean.html`.

**Stato: Implementato (18/08).** `generate_report` avvolge ora ogni `build_leaf_page` in
`try/except (ValueError, OSError)`: al primo fallimento, ogni `understanding_umap_<metric>.html`
già scritto in *questa stessa chiamata* viene rimosso (`Path.unlink(missing_ok=True)`) prima di
ri-sollevare — tutto-o-niente, mai un report che sembra completo ma non lo è. Cleanup mirato
(solo i file HTML scritti da questa funzione, mai `rmtree` di `output_dir`, che spesso coincide
con `umap_tuning_dir` stesso e conterrebbe anche `tuning_results.csv`/`embeddings.npz`). Test:
`test_generate_report_removes_partial_output_when_a_later_metric_fails`
(`tests/unit/test_understanding_umap_report.py`) — 2 metriche, la seconda fallisce via
`build_leaf_page` monkeypatchata; verificato fallire su codice pre-fix (l'HTML della prima
metrica restava), passa col fix (entrambi assenti).

### 23. `understanding_umap_report`: `KeyError` non catturato invece di `ValueError`

**Target**: [src/analysis/understanding_umap_report.py:147-152](src/analysis/understanding_umap_report.py#L147)

```python
def _read_base_n_components(tuning_dir: Path) -> int:
    config_md = (tuning_dir / "config.md").read_text()
    match = re.search(r"```json\n(.*?)\n```", config_md, re.DOTALL)
    if match is None:
        raise ValueError(...)
    return json.loads(match.group(1))["base_params"]["n_components"]
```

Il blocco JSON viene parsato e indicizzato direttamente (`["base_params"]["n_components"]`)
senza verificare che quelle chiavi esistano — lesson #7 (forma esterna non validata prima del
contenuto).

**Esempio concreto**: `config.md` di un tuning `pca_varimax` (una volta che quel metodo avrà
una vera config, vedi CRITICAL #8) ha un blocco JSON con `base_params` ma senza
`rotation_max_iter`/`n_components` esattamente in quella posizione se qualcuno modifica a mano
`_write_tuning_output`'s formato in futuro — `json.loads(...)["base_params"]["n_components"]`
solleva `KeyError: 'n_components'`, non catturato da nessun `except ValueError` nella catena di
chiamata (`load_tuning_data` → `generate_report` → `main()` in
`generate_understanding_umap_report.py`, che cattura solo `(FileNotFoundError, ValueError)`) —
propaga come traceback grezzo.

**Stato: Implementato (18/08).** L'indicizzazione è ora dentro un `try/except (KeyError,
TypeError)` (`TypeError` in più: se il blocco fenced non è nemmeno un oggetto JSON, es. una
lista — lesson #7), che ri-solleva `ValueError` con un messaggio che nomina il file e cosa
manca. Test: `test_read_base_n_components_raises_valueerror_not_keyerror_when_key_missing` +
`test_read_base_n_components_raises_valueerror_when_block_is_not_an_object`
(`tests/unit/test_understanding_umap_report.py`) — verificati fallire su codice pre-fix
(`KeyError`/`TypeError` grezze), passano col fix.

### 24. `understanding_umap_report`: `embeddings.npz` non atomico + `np.load` senza try/except

**Target**: [src/pipeline/dim_reduction.py:354-363](src/pipeline/dim_reduction.py#L354) (scrittura),
[src/analysis/understanding_umap_report.py:1085,1090](src/analysis/understanding_umap_report.py#L1085) (lettura)

```python
# scrittura (_write_tuning_embeddings):
arrays = {_combo_key(keys, combo): embedding for combo, embedding in embeddings_by_combo.items()}
np.savez(output_dir / "embeddings.npz", **arrays)          # non temp-file-then-rename

# lettura (load_tuning_data):
real_data = np.load(umap_tuning_dir / "embeddings.npz")    # nessun try/except
```

Lesson #9 (scrittura non atomica) + lesson #21 (lettura senza isolamento) applicate insieme
allo stesso file: `np.savez` scrive direttamente nel percorso finale (non
`tmp`-poi-`rename` come `save_matrix`), e `np.load` non è avvolto in nessun `try/except`.

**Esempio concreto**: un tuning UMAP con `save_tuning_embeddings=true` viene interrotto (job
SLURM ucciso per timeout, o `Ctrl+C` locale) esattamente durante `np.savez` — `embeddings.npz`
resta troncato/corrotto sul disco, ma la directory esiste già con `tuning_results.csv` e
`config.md` completi (scritti prima), quindi sembra un run riuscito. Un lancio successivo di
`generate_understanding_umap_report.py` su quella stessa cartella arriva a
`np.load(embeddings.npz)`, che solleva `zipfile.BadZipFile`/`OSError: Failed to interpret file`
— non `FileNotFoundError` né `ValueError`, propaga come traceback grezzo invece del consueto
`logging.error`+`return 1`.

**Stato: Implementato (18/08), entrambi i lati.** Scrittura: `_write_tuning_embeddings`
(`dim_reduction.py`) ora scrive `np.savez` su un file temporaneo (`.embeddings_tmp_<uuid>.npz`,
stessa directory) e fa `Path.replace()` verso `embeddings.npz` solo a scrittura completata —
stesso pattern di `save_matrix`, già protetto dal `try/except (FileExistsError, OSError,
ValueError)` esistente attorno a `_write_tuning_output`. Lettura: nuovo helper
`_load_embeddings_npz(path)` in `understanding_umap_report.py`, usato da entrambe le chiamate
in `load_tuning_data`, cattura `(OSError, zipfile.BadZipFile)` e ri-solleva `ValueError`. Test:
`test_dim_reduction_save_tuning_embeddings_interrupted_write_leaves_no_truncated_npz`
(`tests/integration/test_dim_reduction_pipeline.py`, `np.savez` monkeypatchato per scrivere e
poi sollevare `OSError` — verificato fallire su codice pre-fix, `embeddings.npz` restava
troncato, passa col fix: nessun file) +
`test_generate_report_raises_valueerror_on_corrupt_embeddings_npz` (`tests/unit/test_understanding_umap_report.py`,
npz reale troncato a metà — verificato riprodurre `zipfile.BadZipFile` grezzo su codice pre-fix,
`ValueError` pulito col fix).

### 25. `embedding_app`: un solo run con `config.md` corrotto nasconde tutti gli altri

**Target**: [src/analysis/embedding_app.py:263-284](src/analysis/embedding_app.py#L263)
(`run_params`), consumato da `metric_options`/`n_components_options`/`runs_matching`
(righe 287-323)

```python
def run_params(run: ProductionRun) -> dict:
    config_path = run.path / "config.md"
    if not config_path.exists():
        raise ValueError(...)
    for line in config_path.read_text().splitlines():
        if line.startswith(_PARAMS_USED_PREFIX):
            return json.loads(line[len(_PARAMS_USED_PREFIX):])
    raise ValueError(...)
```

`metric_options` (riga 290) chiama `run_params(run)` per **ogni** run in un list-comprehension
(`{run_params(run).get(...) for run in runs_for(...)}`) — un solo `run_params` che solleva
propaga fuori dall'intera comprehension, senza isolamento per-run (lesson #21).

**Esempio concreto**: dropdown "Tipo di riduzione" = `umap` ha 8 run di produzione salvati sotto
`results/lesion/dim_reduction/production/umap/`. Uno di questi (`13-08_s1.1_nc3_m_dice`) ha un
`config.md` con la riga `Params used: {...}` troncata a metà (editor esterno aperto e salvato
per errore mentre l'app Dash teneva il file in lettura — scenario realistico su una cartella
`results/` condivisa via mount di rete). Il callback `_update_metric_picker` chiama
`metric_options(...)`, che itera su tutti gli 8 run e solleva `json.JSONDecodeError` sull'unico
run corrotto — il dropdown "Metrica" fallisce a popolarsi per **tutti e 8** i run `umap`, non
solo per quello corrotto, rendendo l'intero metodo `umap` inesplorabile nell'app finché quel
singolo `config.md` non viene riparato o rimosso a mano.

**Stato: Implementato (18/08).** Nuovo helper `_run_params_or_none(run)` avvolge `run_params(run)`
in `try/except ValueError` (che copre anche `json.JSONDecodeError`, sottoclasse di `ValueError`),
logga un WARNING col path del run e ritorna `None` invece di propagare — `metric_options`/
`n_components_options`/`runs_matching` filtrano i `None` invece di lasciarli interrompere la
comprehension. Test: `test_metric_options_one_corrupt_run_does_not_hide_the_others`
(`tests/unit/test_embedding_app.py`) — un `config.md` troncato a metà su un run, verificato
fallire su codice pre-fix (`JSONDecodeError` grezzo, entrambi i run persi), passa col fix
(`run-a` resta visibile, WARNING loggato per `run-b`).

---

## MEDIUM

### 26. `mask_fc`: validazione naming soggetto incoerente tra branch `group_filter`

**Target**: [src/features/subject_discovery.py:75-78](src/features/subject_discovery.py#L75)

```python
excluded_by_group: list[str] = []
if group_filter is not None:
    excluded_by_group = sorted(s for s in by_subject if group_of(s) not in group_filter)
    by_subject = {s: p for s, p in by_subject.items() if group_of(s) in group_filter}
return by_subject, excluded_by_group
```

`group_of(s)` (che valida la convenzione di naming ST/HC/PD/GM) viene chiamata solo quando
`group_filter is not None` — lesson #4, variante specifica di questo modulo: con
`group_filter=None` un `subject_id` che non rispetta affatto la convenzione (es. un file
copiato a mano con un nome malformato) non viene mai fatto passare da `group_of`, quindi non
solleva mai l'errore che solleverebbe con un `group_filter` impostato.

**Esempio concreto**: `mask_fc.json` con `group_filter=null` (dataset noto per non mischiare
gruppi, es. un dataset futuro tutto-ST) — un file rinominato a mano
`subSTUNIPD9999_...-mask.nii.gz` (trattino mancante dopo "sub", errore di battitura) supera
comunque `discover_files_by_subject` come soggetto valido (il naming malformato non viene mai
controllato), mentre lo stesso identico file con `group_filter=["ST"]` impostato farebbe
fallire `group_of()` con un errore esplicito. Lo stesso identico input, comportamento diverso a
seconda del branch di config.

**Stato: Implementato (21/08).** `discover_files_by_subject` costruisce ora
`groups = {s: group_of(s) for s in by_subject}` **incondizionatamente**, prima del branch
`if group_filter is not None` — la validazione del naming avviene sempre, il filtro (quando
impostato) legge poi da quel dizionario già calcolato invece di richiamare `group_of()` una
seconda volta. **Impatto collaterale rilevante, non previsto dalla stima iniziale del
finding**: 44 test in tutta la suite usavano ID soggetto sintetici tipo `sub-01`/`sub-00`
(mai conformi alla naming convention ST/HC/...) che passavano solo perché `group_filter=None`
saltava la validazione — la fix li ha rotti tutti. Sistemati sostituendo gli ID sintetici con
ID realistici (`sub-STUNIPD0001` ecc.) nei fixture helper di 5 file di test
(`test_clustering_pipeline.py`, `test_dim_reduction_pipeline.py`,
`test_build_lesion_matrix_pipeline.py`, `test_mask_fc_pipeline.py`,
`test_features_functional.py`), non nei singoli test. Nuova lezione aggiunta a
`lessons_learned.md` (#28) per questo pattern. Test:
`test_discover_files_by_subject_malformed_name_raises_even_without_group_filter`
(`tests/unit/test_subject_discovery.py`) — verificato fallire su codice pre-fix
(`DID NOT RAISE`), passa col fix. Suite intera: 727 passed, 0 failed, 12 skipped.

### 27. `mask_fc`: `load_atlas` non valida index tsv↔volume prima di indicizzare

**Target**: [src/features/functional.py:78-104](src/features/functional.py#L78) (`compute_parcel_coverage`)

```python
label_ids = label_table["index"].tolist()
...
return np.array([healthy_by_label.get(lbl, 0.0) / total_by_label[lbl] for lbl in label_ids])
```

`total_by_label[lbl]` (accesso diretto, non `.get`) presuppone che ogni `index` del tsv
corrisponda a un'etichetta effettivamente presente nel volume atlante — mai verificato
esplicitamente al caricamento (`load_atlas`), solo implicitamente al primo utilizzo. Lesson #7,
non attivo sui dati reali oggi (i 12 atlanti `Yan{...}TianS{...}Buckner7N` sono internamente
coerenti).

**Esempio concreto**: un futuro atlas combo scaricato con un `_dseg.tsv` disallineato dal
proprio `.nii.gz` (es. un aggiornamento di versione dell'atlante che rinumera le label senza
aggiornare il volume in coppia) — un `index` presente nel tsv ma assente dal volume produce
`KeyError` diretto su `total_by_label[lbl]`, un traceback poco informativo rispetto a un
controllo esplicito al caricamento che direbbe "atlas X ha N label nel tsv ma M nel volume".

**Stato: Implementato (21/08).** `load_atlas` calcola ora `np.unique(atlas_img.get_fdata())`
(esclude lo 0, background) e verifica che ogni `index` del tsv sia un sottoinsieme delle
label realmente presenti nel volume — `ValueError` esplicito con gli index mancanti e il
conteggio label del volume, altrimenti nessun impatto (0 index fuori sync sui 12 atlanti
reali). Chiude anche #28 nello stesso punto (stesso `load_atlas`, unica sorgente di
`label_table`). Test: `test_load_atlas_index_absent_from_volume_raises`
(`tests/unit/test_features_functional.py`) — verificato fallire su codice pre-fix
(`DID NOT RAISE`), passa col fix.

### 28. `mask_fc`: `label_table["index"]` duplicati non validati

**Target**: [src/features/functional.py:251-254](src/features/functional.py#L251)

```python
label_ids = label_table["index"].tolist()
id_to_name = dict(zip(label_table["index"], label_table["label"]))
node_names = np.array([id_to_name[i] for i in label_ids])
```

Nessun controllo di unicità su `label_table["index"]` prima di costruire `id_to_name` (un
`dict`, che collassa silenziosamente un duplicato) — lesson #5, non attivo sui dati reali oggi.

**Esempio concreto**: un `_dseg.tsv` con due righe che condividono lo stesso `index` per errore
di generazione a monte (es. un merge di due atlanti parziali con numerazione non
riconciliata) — `id_to_name` mantiene solo l'ultima delle due (`dict` sovrascrive), `node_names`
finisce con un nome ripetuto due volte per lo stesso indice reale invece di due nomi distinti,
gonfiando artificialmente il conteggio di parcelle senza nessun errore.

**Stato: Implementato (21/08), stesso fix di #27.** `load_atlas` verifica
`label_table["index"].duplicated()` prima di ritornare — `ValueError` esplicito con gli
index duplicati, unica sorgente di `label_table` per `mask_dataset_fc`. Test:
`test_load_atlas_duplicate_index_raises` (`tests/unit/test_features_functional.py`) —
verificato fallire su codice pre-fix (`DID NOT RAISE`), passa col fix.

### 29. `build_fc_matrix`: loop su `atlas_combos` non isolato

**Target**: [src/pipeline/build_fc_matrix.py:66-136](src/pipeline/build_fc_matrix.py#L66)

```python
for combo in config.atlas_combos:
    ...
    try:
        X, metadata, edge_names, dropped_info = build_fc_matrix_from_masked(input_dir)
    except (FileNotFoundError, ValueError) as exc:
        logging.error("%s: %s", combo, exc)
        return 1          # <- interrompe l'intero run, non solo questo combo
```

`return 1` invece di `continue`: un combo fallito interrompe l'intero comando anche se gli 11
combo configurati sono indipendenti tra loro (ognuno legge una cartella `masked_fc/<combo>/`
separata). Lesson #21.

**Esempio concreto**: `build_fc_matrix.json`'s `atlas_combos` elenca 11 combo in ordine
alfabetico. `Yan100TianS1Buckner7N` (il primo) non ha ancora `masked_fc/` popolata (mask_fc.py
non è stato ancora rilanciato per quella combo dopo un cambio di `min_coverage`) —
`discover_masked_fc_files` solleva `FileNotFoundError`, il run si interrompe immediatamente:
gli altri 10 combo, tutti pronti e completi, non vengono processati affatto in questo lancio,
anche se non hanno nulla in comune con il combo mancante.

**Stato: Implementato (21/08).** Il `try/except (FileNotFoundError, ValueError)` attorno a
`build_fc_matrix_from_masked` ora fa `continue` (accumulando in `failed_combos: dict[str,
str]`) invece di `return 1` — lesson #21, stesso schema di HIGH #9. `save_matrix`/
`append_run_log_entry` restano invece fatali (`return 1`) per quel combo: sono guasti
infrastrutturali (disco pieno, permessi) verosimilmente ricorrenti su ogni combo successivo,
non un gap di input per-combo. `main()` ritorna 1 solo se **tutti** i combo falliscono
(nessun output prodotto); un run parziale ritorna 0, con `failed_combos` loggato (WARNING) e
persistito in una nuova sezione "Skipped (build failed)" del report. Test:
`test_build_fc_matrix_one_combo_not_ready_does_not_abort_the_others`
(`tests/integration/test_build_fc_matrix_pipeline.py`) — 2 combo, uno pronto uno mai
processato da mask_fc.py; verificato fallire su codice pre-fix (`exit_code == 1`, nessun
output), passa col fix (`exit_code == 0`, `ComboReady` scritto, `ComboMissing` nel report).

### 30. `build_fc_matrix`: nessuna verifica di simmetria prima di estrarre il triangolo superiore

**Target**: [src/features/functional.py:145-156](src/features/functional.py#L145) (`vectorize_upper_triangle`)

```python
def vectorize_upper_triangle(matrix_df: pd.DataFrame, node_names: np.ndarray) -> pd.Series:
    n = len(node_names)
    row_idx, col_idx = np.triu_indices(n, k=1)
    edge_names = [f"{node_names[i]}__{node_names[j]}" for i, j in zip(row_idx, col_idx)]
    values = matrix_df.values[row_idx, col_idx]
    return pd.Series(values, index=edge_names)
```

Nessun controllo `np.allclose(matrix_df.values, matrix_df.values.T)` prima di assumere che il
triangolo superiore rappresenti l'intera informazione (il docstring del modulo dichiara
esplicitamente "the matrix is symmetric" come fatto assunto, mai verificato).

**Esempio concreto**: un file `*_masked_fc.csv` con una riga/colonna asimmetrica per un bug in
una versione futura di `mask_fc.py`, o per un errore di scrittura manuale durante un debug —
`vectorize_upper_triangle` scarta silenziosamente il triangolo inferiore (che nel caso rotto
conterrebbe valori diversi), producendo un vettore di edge "valido" nella forma ma che ignora
metà dell'informazione realmente presente nel file, senza nessun segnale che la matrice non
fosse effettivamente simmetrica.

**Stato: Implementato (21/08).** `np.allclose(matrix, matrix.T, equal_nan=True)` (equal_nan
perché `mask_fc_by_lesion` NaN-a righe/colonne compromesse simmetricamente per costruzione —
un NaN su entrambi i lati è atteso, non un'asimmetria) prima di estrarre il triangolo
superiore — `ValueError` esplicito se falso. Test:
`test_vectorize_upper_triangle_asymmetric_matrix_raises` +
`test_vectorize_upper_triangle_tolerates_symmetric_nan_from_masking`
(`tests/unit/test_features_functional.py`) — il primo verificato fallire su codice pre-fix
(`DID NOT RAISE`), passa col fix; il secondo conferma che il NaN simmetrico da masking non
fa scattare il nuovo controllo.

### 31. `build_fc_matrix`: `load_build_fc_matrix_config` senza test unitari dedicati

**Target**: `src/analysis/build_config.py::load_build_fc_matrix_config`

**Verificato**: `grep -rln "load_build_fc_matrix_config" tests/` non restituisce nessun file —
a differenza di `load_mask_fc_config` (3 test in `test_build_config.py`, per quanto limitati,
vedi #51) e `load_build_matrix_config`, questo loader di config non ha nessun test diretto,
solo copertura indiretta via `tests/integration/test_*` che passano un config valido end-to-end.

**Esempio concreto**: un refactor futuro che aggiunge un campo obbligatorio a
`BuildFcMatrixConfig` (es. `min_edges_expected`) può rompere silenziosamente la validazione
(o dimenticare di validarlo affatto) senza che nessun test unitario lo segnali — solo un test
di integrazione che carica per caso un config privo di quel campo lo scoprirebbe, e solo se il
comportamento di default scelto produce un errore visibile a valle.

**Stato: Implementato (21/08).** 13 nuovi test in `tests/unit/test_build_config.py` (config
valido, `atlas_combos` multipli, `run_notes` passthrough, file mancante, top-level non-oggetto,
7 casi di config invalida parametrizzati: stringhe vuote, `atlas_combos` vuoto/duplicato,
`overwrite` non-bool) — stesso schema di `load_build_matrix_config`/`load_mask_fc_config`
sopra. Nessun fix di codice (`load_build_fc_matrix_config` era già corretto) — solo copertura
mancante colmata, come richiesto dal finding.

### 32. `dim_reduction`: riferimenti stale a `docs/notes/` sparsi in README/CLAUDE.md/docs/dev/docstring

**Verificato**: `ls docs/notes/` → `No such file or directory`. `.claude/CLAUDE.md` cita
esplicitamente `docs/notes/` come cartella esistente ("guide per-metodo... `clustering.md`/
`dim_reduction.md`... decisions log"), e diversi docstring di `dim_reduction.py`/moduli
`src/analysis/` rimandano a `docs/notes/dim_reduction.md` per il razionale metodologico.

**Esempio concreto**: uno sviluppatore che legge il docstring di `pca_varimax_embed`
(`src/analysis/reduction.py`) o la sezione "Working in this repo" di CLAUDE.md e prova ad
aprire `docs/notes/dim_reduction.md` per il razionale della metodologia Thiebaut de Schotten
2020 trova una cartella inesistente — la sostanza di quel contenuto può darsi viva altrove
(`knowledge/dim_reduction_clustering/`?), ma nessun rimando lo dice esplicitamente, quindi la
ricerca si conclude in un vicolo cieco invece che con un redirect.

**Stato: Implementato (21/08), insieme a #38 (stesso gap).** Verificato riferimento per
riferimento (`grep -rln "docs/notes"`) invece di fidarsi del titolo del finding — trovati e
corretti 6 riferimenti stale reali: `.claude/CLAUDE.md` (elenco struttura repo, riscritto per
dichiarare `docs/notes/` dissolta con redirect a `knowledge/dim_reduction_clustering/`/
`knowledge/neuroimaging/`), `docs/guides/clustering.md`/`dim_reduction.md`, `docs/dev/
fc_matrix.md`/`models.md` (redirect ai file successori reali già presenti su disco:
`clustering_literature_survey.md`, `dim_reduction_tuning_guide.md`,
`knowledge/neuroimaging/fc_lesion_masking.md`), `src/features/clinical.py` (riferimento a
`docs/notes/Siegel2016_Reproduction.md`, verificato in `.claude/stato_progetto_archive.md`
come **eliminato deliberatamente, non migrato** — nessun successore da linkare, il docstring
lo dice esplicitamente ora). `management/notes/TODO.md` (voce diversa da `docs/notes/`, stesso
gap) corretta allo stesso modo. **Nuovo, trovato solo verificando i file citati esistano
ancora** (non nel finding originale): `knowledge/dim_reduction_clustering/
clustering_tuning_guide.md` citava ancora `docs/guides/dim_reduction_clustering.md` (guida
rimossa) e `dim_reduction_clustering.py` come "workflow raccomandato" — entrambi corretti.
`docs/dev/lesion_matrix.md`'s riferimento a `docs/notes/analysis_pipeline_v2_handoff.md`
lasciato invariato: è esplicitamente dichiarato "intentionally-frozen historical snapshot",
non manutenuto per scelta. Nessun test (fix di sola documentazione).

### 33. `dim_reduction`: `docs/dev/models.md` dichiara `metric=jaccard` per UMAP produzione, registry reale ha `euclidean`

**Target**: [docs/dev/models.md:42](docs/dev/models.md#L42) vs.
`config/registry/params_reduction.json`

`docs/dev/models.md` afferma: "`metric` is an explicit key in both `umap`/`tsne`'s `"params"`
in `params_reduction.json`... production `umap` runs with `metric="jaccard"` as of session
s1.1's 26-07 tuning round".

**Verificato dal vivo**: `config/registry/params_reduction.json`'s `umap.params` reale, oggi:

```json
"params": { "n_neighbors": 5, "min_dist": 0.0, "n_components": 2, "random_state": 0, "metric": "euclidean" }
```

`"metric": "euclidean"`, non `"jaccard"` — la doc è rimasta al valore deciso durante il round
di tuning del 26/07 ma il registry è stato aggiornato successivamente (o mai allineato) senza
aggiornare la doc. Chiunque legga `docs/dev/models.md` per capire con quale metrica la
produzione UMAP attuale è stata imbastita (es. per interpretare i plot di produzione, o per
riprodurre lo stesso embedding altrove) userebbe il valore sbagliato.

**Stato: Implementato (21/08).** Riverificato che il registry ha tuttora `metric="euclidean"`
per `umap` **e** `tsne` — riscritta la frase in `docs/dev/models.md` per riflettere lo stato
reale odierno, con nota esplicita che il valore `jaccard` è stato reimpostato dopo il round
s1.1 senza aggiornare questa doc (riferimento a questo finding per la prossima volta). Nessun
test (fix di sola documentazione).

### 34. `dim_reduction`: refit di viz nella griglia di tuning non riusa `distance_cache`

**Target**: [src/pipeline/dim_reduction.py:430-480](src/pipeline/dim_reduction.py#L430)
(`_build_grid_blocks`)

```python
def _build_grid_blocks(
    free_params, tuning_grid, keys, leaf, base_params, embeddings_by_combo, config, X,
) -> list[...]:
    ...
    viz_embedding = embedding_for_viz(
        config.reduction_method, X, combo_params, embedding, _TUNING_GRID_N_COMPONENTS
    )   # <- nessun distance_cache passato, a differenza di _run_production/_run_fine_tuning
```

A differenza di `_run_production` (righe 123, 134) e del percorso principale di
`_run_fine_tuning`, `_build_grid_blocks` non riceve né passa un `distance_cache` — ogni cella
della griglia `embeddings_grid_*.png` che richiede un refit (`n_components` della combinazione
≠ 2) ricalcola `binary_pairwise_distance(X, metric)` da zero.

**Esempio concreto**: un tuning `umap` con `nested_params=["metric", "n_components"]`,
`free_params=["n_neighbors", "min_dist"]` (5×6=30 celle per foglia) su `metric=jaccard`,
`n_components=5` (leaf diversa da `_TUNING_GRID_N_COMPONENTS=2`) — ognuna delle 30 celle passa
per `embedding_for_viz`, che essendo `n_components` sempre diverso da 2 in questa foglia,
rifitta *ogni singola cella* chiamando `embed()` senza cache: la matrice di distanza Jaccard
(n_subjects² per la coorte, es. 1150×1150 float64 ≈ 10.5 MB, ma il *calcolo* è O(n²·n_features))
viene ricalcolata identica 30 volte invece di una sola, un costo evitabile puramente per un
parametro di funzione mancante.

**Stato: Implementato (21/08).** `distance_cache: dict[str, np.ndarray] = {}` creato una
sola volta in `_write_nested_tuning_leaves` (condiviso tra **tutte** le foglie della griglia,
non uno per foglia — un `metric` può ripetersi tra foglie diverse quando `nested_params`
include anche `n_components`), passato a `_build_grid_blocks` e da lì a ogni chiamata
`embedding_for_viz`. Stesso pattern già usato da `_run_production`/`_run_fine_tuning`. Test:
`test_dim_reduction_fine_tuning_grid_refit_reuses_distance_cache_across_cells`
(`tests/integration/test_dim_reduction_pipeline.py`) — sweep `nested_params=["n_components"]`
con `metric="jaccard"` fisso, 3 valori di `n_neighbors` nella foglia `n_components=3` (tutti
richiedono un refit) — `binary_pairwise_distance` monkeypatchata con un contatore; verificato
fallire su codice pre-fix (3 chiamate), passa col fix (≤1 chiamata).

### 35. `clustering`: tuning `evidence_accumulation` — 350 fit invece di 50

**Target**: [src/analysis/clustering.py:119-120](src/analysis/clustering.py#L119)
(`evidence_accumulation_cluster`) chiamata da
[src/analysis/clustering_tuning.py:195-205](src/analysis/clustering_tuning.py#L195)
(`run_clustering_tuning_sweep`)

```python
# clustering.py, ad ogni chiamata (una per combo del tuning_grid):
co_occurrence = run_rsc_repeats(base_method, X, params, n_repeats, base_seed=base_seed)
return assign_clusters_from_cooccurrence(co_occurrence, threshold)
```

`config/registry/params_clustering.json`'s `"evidence_accumulation".tuning_grid` sweeppa
**solo** `"threshold": [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]` (7 valori), con `"n_repeats": 50`
fisso in `params`. La matrice di co-occurrence (il costo vero: 50 fit `spectral` ripetuti) **non
dipende da `threshold`** — solo l'ultimo passo (`assign_clusters_from_cooccurrence`, un
linkage/`fcluster` economico) lo usa. `run_clustering_tuning_sweep` non lo sa: chiama
`CLUSTERING_METHODS["evidence_accumulation"]` una volta per ognuna delle 7 combinazioni,
ricalcolando `run_rsc_repeats` (50 fit `spectral` da zero) 7 volte — **350 fit** in totale
invece dei 50 realmente necessari (calcolare la co-occurrence una volta, applicare
`assign_clusters_from_cooccurrence` 7 volte sul risultato già in memoria).

**Esempio concreto**: un tuning `evidence_accumulation` su 1150 soggetti con `base_method=
"spectral"`, `n_neighbors=50` — ogni fit `spectral` su una matrice di quella dimensione richiede
qualche secondo; 350 fit invece di 50 significa un tuning che impiega ~7× più tempo del
necessario, un run che potrebbe durare 10 minuti invece di ~90 secondi, puramente per come lo
sweep genérico ignora che `threshold` è "a valle" del costo reale.

**Stato: Implementato (21/08), chiude anche #40 (stesso meccanismo, call site gemello ormai
rimosso — vedi sotto).** `evidence_accumulation_cluster` refattorizzata: la
validazione/estrazione parametri (`base_method`, `split_params`, `n_repeats`, `base_seed`,
`threshold`) isolata in `_validate_evidence_accumulation_params` (nuova funzione condivisa in
`clustering.py`), riusata sia dalla funzione originale sia dal nuovo fast path del sweep.
`run_clustering_tuning_sweep` ora, solo per `method == "evidence_accumulation"`, raggruppa le
combinazioni per la chiave `(base_method, n_repeats, base_seed, split_params)` — tutto ciò che
`run_rsc_repeats` legge davvero, **mai** `threshold` — e riusa la matrice di co-occurrence già
calcolata per ogni combinazione che condivide quella chiave, chiamando
`assign_clusters_from_cooccurrence` (economico) per ognuna. Generalizza correttamente anche se
in futuro venissero sweeppati altri parametri oltre a `threshold` (raggruppa comunque per
tutto tranne `threshold`). Test:
`test_run_clustering_tuning_sweep_evidence_accumulation_reuses_cooccurrence_across_thresholds`
(`tests/unit/test_clustering_tuning.py`) — sweep a 4 valori di `threshold`,
`run_rsc_repeats` monkeypatchata con un contatore; verificato fallire su codice pre-fix (4
chiamate), passa col fix (1 chiamata). Suite `clustering`/`clustering_tuning`/`consensus_
clustering` intera riverificata verde (78 test).

### 36. `clustering`: `tag_param` di `spectral` non corrisponde al parametro realmente swept

**Target**: `config/registry/params_clustering.json`'s `"spectral"`

```json
"spectral": {
  "tag_param": "n_neighbors",
  "tag_prefix": "nn",
  "params": { "n_clusters": 5, "affinity": "nearest_neighbors", "n_neighbors": 50, "random_state": 0 },
  "tuning_grid": { "n_clusters": [2, 3, 4, 5, 6, 8, 10, 11, 12, 13, 14, 15] }
}
```

`tag_param` è `"n_neighbors"` (`tag_prefix="nn"`) ma `tuning_grid` sweeppa **`n_clusters`**, mai
`n_neighbors` (che resta fisso a 50 in ogni run). `load_method_params` usa `tag_param` per
costruire il tag del `session_name` in produzione (`effective_session_name = f"{session_name}_
{tag}"`, dove `tag` è derivato dal valore scelto in `params[tag_param]`, vedi
`src/analysis/params.py`).

**Esempio concreto**: due run di produzione `spectral` lanciati con `n_clusters=5` e
`n_clusters=8` rispettivamente (modificando `params.n_clusters` a mano tra un run e l'altro, il
modo previsto per scegliere il valore dopo un tuning) generano lo **stesso identico tag**
(`nn50`, dato che `n_neighbors` non cambia mai) — le due cartelle di output finiscono con
`effective_session_name` identico se `session_name` di base è lo stesso, collidendo su disco
(`FileExistsError` con `overwrite=False`, o sovrascrittura silenziosa con `overwrite=True`)
anche se rappresentano due configurazioni di clustering genuinamente diverse.

**Stato: Implementato (21/08).** `config/registry/params_clustering.json`'s `"spectral"`:
`tag_param` da `"n_neighbors"` a `"n_clusters"`, `tag_prefix` da `"nn"` a `"n_clust"` (stessa
convenzione già usata da `"agglomerative"` per lo stesso parametro) — allineato a ciò che il
`tuning_grid` sweeppa realmente. Fix di puro config, nessun codice toccato (nessun test
asseriva il vecchio `tag_param`/`tag_prefix`, verificato via `grep -rn`).

### 37. `clustering`: budget split di `evidence_accumulation` (6) coincide col K finale

**Target**: `config/registry/params_clustering.json`'s `"evidence_accumulation".params` vs.
[src/analysis/clustering.py:50-54](src/analysis/clustering.py#L50) (docstring)

Il docstring di `evidence_accumulation_cluster` è esplicito: il parametro Split
(`K_PARAM_NAME[base_method]`, qui `n_clusters` per `base_method="spectral"`) "should be
*larger* than the true expected number of clusters (a large number of small, compact clusters
to combine), not the final cluster count." La config reale:

```json
"evidence_accumulation": {
  "params": { "base_method": "spectral", "n_clusters": 6, ..., "threshold": 0.5, ... }
}
```

`n_clusters=6` per la fase Split — lo stesso identico valore di default usato da `kmeans`/`gmm`
per il *K finale* (entrambi impostati a 6 in questo stesso file), non un numero "grande" di
micro-cluster da fondere come richiede l'algoritmo Fred & Jain 2002.

**Esempio concreto**: con `n_clusters=6` in fase Split, ogni ripetizione di `spectral` produce
al massimo 6 cluster — la matrice di co-occurrence non può mai distinguere sotto-strutture più
fini di 6 gruppi, il passo Merge (`threshold`) può solo *fondere* quei 6 gruppi in meno cluster
finali, mai risolvere più dettaglio. Se il vero numero di cluster atteso nella coorte è
effettivamente ~6, il metodo Evidence Accumulation degenera a "kmeans/spectral ripetuto 50 volte
e quasi sempre d'accordo con se stesso" — perdendo l'intero vantaggio del metodo (scoprire
struttura più fine tramite tanti micro-cluster, poi fusi solo dove davvero stabili).

**Stato: Documentato, valore non cambiato (21/08, decisione utente).** Scelta di parametro
scientifico, non un bug di codice — non modificabile a mia discrezione senza una decisione
esplicita su quale nuovo valore usare (impatterebbe risultati di ricerca reali). Nota aggiunta
in `docs/dev/models.md` (sezione evidence_accumulation) che documenta esplicitamente il
problema e rimanda a questo finding — resta un promemoria per chi riprende in mano il tuning
di `evidence_accumulation`, nessun cambiamento silenzioso ai risultati.

### 38. `clustering`: `docs/notes/` (incl. `clustering.md`) non esiste pur essendo citata come obbligatoria

**Target**: stesso gap di #32, applicato a `docs/notes/clustering.md` — citata da
`README.md`'s "What's implemented so far" ("methodology: `docs/notes/dim_reduction.md`/
`clustering.md`") e da CLAUDE.md come sede delle "guide per-metodo... decisions log". Confermato
`docs/notes/` assente sul disco (vedi #32).

**Stato: Implementato (21/08) — vedi #32, stesso giro di fix.** `README.md` verificato: già
punta a `knowledge/dim_reduction_clustering/` (non a `docs/notes/`), nessuna azione lì
necessaria — il riferimento stale era solo in `.claude/CLAUDE.md`, corretto insieme a #32.

### 39. `dim_reduction_clustering`: `viz_embedding` calcolato incondizionatamente anche in `fine_tuning`, mai usato lì

**Target**: [src/pipeline/dim_reduction_clustering.py:146-166](src/pipeline/dim_reduction_clustering.py#L146)

```python
distance_cache: dict[str, np.ndarray] = {}
embedding = embed(config.reduction_method, X, reduction_params, distance_cache)
try:
    viz_embedding = embedding_for_viz(
        config.reduction_method, X, reduction_params, embedding, config.viz_n_components, distance_cache
    )
except ValueError as exc:
    logging.error(str(exc))
    return 1

if config.fine_tuning:
    return _run_fine_tuning(config, embedding, reduction_params, now, log_path)   # <- viz_embedding mai passato/usato
```

`viz_embedding` è calcolato **prima** del branch `if config.fine_tuning`, quindi sempre — ma
`_run_fine_tuning` (chiamata subito dopo per il ramo tuning) riceve solo `embedding`, mai
`viz_embedding`: il calcolo (potenzialmente un intero secondo refit UMAP/t-SNE per i metodi in
`_REFITTABLE_FOR_VIZ`) è puro spreco per ogni run in modalità `fine_tuning=true`.

**Esempio concreto**: `dim_reduction_clustering.json` con `fine_tuning=true`,
`reduction_method="umap"`, `n_components=10` di produzione ma `viz_n_components=2` — ogni
lancio del tuning di clustering (che deve solo sweeppare gli iperparametri di clustering
sull'embedding a 10 componenti già fissato) paga comunque il costo di un secondo fit UMAP a 2
componenti (il refit di `embedding_for_viz`) il cui risultato non viene mai letto in nessun
punto del percorso `fine_tuning`, raddoppiando inutilmente il tempo di avvio di ogni sweep di
clustering-tuning.

**Stato: Moot (21/08).** `dim_reduction_clustering.py` non esiste più (rimosso 14/08). La
struttura che causava lo spreco (calcolo di `viz_embedding` prima del branch `if
config.fine_tuning`, poi ignorato in quel branch) non ha un gemello vivo: `dim_reduction.py`
(`main()`) biforca in `_run_fine_tuning`/`_run_production` **prima** di calcolare qualunque
`viz_embedding` — nessuno spreco strutturalmente possibile. `clustering.py`, per design, non
chiama mai `embed()`/`embedding_for_viz()` (vedi `docs/dev/models.md`'s sezione
"reduced_data"). Verificato leggendo entrambi i moduli riga per riga prima di chiudere, non
solo confidando nel titolo del finding. Nessuna azione.

### 40. `dim_reduction_clustering`: stesso spreco `evidence_accumulation` del #35

**Target**: [src/pipeline/dim_reduction_clustering.py:472-476](src/pipeline/dim_reduction_clustering.py#L472)
(`_run_one_method_tuning`) → stessa `run_clustering_tuning_sweep` di #35, qui applicata
all'embedding invece che alla matrice grezza. Stesso meccanismo, stesso fix mancante (separare
il costo di `run_rsc_repeats` da quello di `assign_clusters_from_cooccurrence` per riusare la
co-occurrence tra i valori di `threshold`).

**Stato: Chiuso, sussunto da #35 (21/08).** `dim_reduction_clustering.py` non esiste più —
nessun call site separato da correggere. Il fix di #35 (`run_clustering_tuning_sweep` in
`clustering_tuning.py`, condiviso da `clustering.py`'s tuning e — prima della rimozione — da
`dim_reduction_clustering.py`'s tuning) copre per intero ciò che questo finding avrebbe
richiesto. Nessuna azione separata.

### 41. `understanding_umap_report`: nessun caveat comunicato su come leggere UMAP/t-SNE

**Target**: `src/analysis/understanding_umap_report.py::build_leaf_page` (l'HTML generato)

Il report riproduce il layout di pair-code.github.io/understanding-umap (grid, slider,
confronto UMAP-vs-t-SNE) ma non ne riproduce il testo esplicativo — la pagina originale PAIR
include avvertimenti espliciti ("Cluster sizes in a UMAP plot mean nothing", "Distances between
clusters might not mean anything", "You may need more than one plot"), che qui non compaiono in
nessuna forma (né nel testo statico né nelle didascalie "Figure N:").

**Esempio concreto**: l'utente finale del progetto (non tecnico, per cui `docs/notes/` esiste
proprio a questo scopo, vedi #32/#38) apre `understanding_umap_dice.html`, vede due cluster
visivamente vicini nella Figure 1 e conclude che i due gruppi di pazienti sono "simili" — senza
nessun avviso sulla pagina che le distanze tra cluster in UMAP non sono generalmente
interpretabili in quel modo, un'inferenza clinica plausibile ma metodologicamente scorretta che
il report stesso non fa nulla per prevenire, a differenza della pagina PAIR che lo dice
esplicitamente proprio per questo motivo.

**Stato: Implementato (21/08).** Box `.caveats` aggiunto subito sotto il titolo della pagina
(prima di "UMAP across parameters"), con i 3 avvertimenti PAIR tradotti/adattati verbatim nel
contenuto ("Cluster sizes... mean nothing", "Distances between clusters might not mean
anything", "You may need more than one plot" — quest'ultimo riformulato per collegarsi
esplicitamente alla Figure 1 di questo stesso report). Non rimuove l'ambiguità interpretativa
di UMAP/t-SNE in sé (nessun codice può farlo), ma la rende esplicita per il lettore non
tecnico a cui il report è indirizzato. Test:
`test_generate_report_includes_umap_interpretation_caveats`
(`tests/unit/test_understanding_umap_report.py`) — verificato fallire su codice pre-fix
(testo assente dall'HTML generato), passa col fix.

### 42. `understanding_umap_report`: riferimenti morti a `run_understanding_umap_dash`

**Target**: [src/pipeline/embedding_app.py:9,33](src/pipeline/embedding_app.py#L9),
`docs/guides/embedding_app.md:13`

**Verificato**: `find src/pipeline -iname "*understanding_umap_dash*"` non trova nessun file
sorgente (solo `__pycache__/run_understanding_umap_dash.cpython-311.pyc`, un residuo di
bytecode di un modulo ormai rimosso) — ma `src/pipeline/embedding_app.py` lo cita ancora due
volte nel proprio docstring:

```python
# src.pipeline.run_understanding_umap_dash: an interactive app with no batch-job shape has
# nothing for SLURM to do...
# 8060, not Dash's own default 8050 - src.pipeline.run_understanding_umap_dash already
# binds 8050 by default...
```

e `docs/guides/embedding_app.md:13` lo cita come alternativa possibile
("`src.pipeline.generate_understanding_umap_report`/`run_understanding_umap_dash` - se
presente"). Lesson #12.

**Esempio concreto**: chi legge `embedding_app.py`'s docstring per capire perché la porta di
default è 8060 (non 8050) segue il riferimento a `src.pipeline.run_understanding_umap_dash` per
vedere l'altra app e capire il conflitto di porta che l'8060 evita — il modulo non esiste più
sotto `src/pipeline/`, la spiegazione del "perché 8060" fa riferimento a un fatto non più
verificabile nel codice attuale.

**Stato: Implementato (21/08).** Entrambi i riferimenti rimossi. `embedding_app.py`'s
docstring/commento riscritti senza menzionare `run_understanding_umap_dash` (che non è mai
esistito come modulo sorgente in `src/pipeline/`, solo un residuo di bytecode `.pyc`) — il
motivo "niente sbatch" resta (vero indipendentemente), il motivo "porta 8060 non-default"
riformulato in modo generico ("per non collidere con un'altra istanza Dash locale già in
esecuzione", vero anche senza citare un secondo tool specifico). `docs/guides/embedding_app.md`
aggiornato per rimandare al vero tool sibling (`generate_understanding_umap_report.py`, HTML
statico pre-generato, non un'app Dash — `docs/guides/understanding_umap_report.md`), non più
citato come "se presente". Nessun test (fix di sola documentazione/docstring).

### 43. `embedding_app`: messaggio errore per embedding >3D indica il campo di config sbagliato

**Target**: [src/analysis/embedding_app.py:340-345](src/analysis/embedding_app.py#L340)
(`load_run`, classe `UndisplayableRunError`)

```python
if n_dims not in (2, 3):
    raise UndisplayableRunError(
        f"Run {run.path} has a saved embedding with {n_dims} components - this app can only display an "
        "already-2-or-3-component embedding: Rerun dim_reduction pipeline with viz_n_components 2 or 3 and, "
        "or pick a different run."
    )
```

**Verificato**: `ClusteringConfig` (`src/analysis/model_config.py:40-49`) **non ha nessun campo
`viz_n_components`** — quel parametro esiste solo in `DimReductionConfig`/
`DimReductionClusteringConfig`. `discover_production_runs` scopre run sia di `dim_reduction.py`
che di `clustering.py` (vedi CRITICAL #2), ma questo messaggio di errore è scritto come se ogni
run indisplayable venisse sempre da una pipeline con `viz_n_components`.

**Esempio concreto**: un run `clustering.py` su una matrice voxel-wise non parcellata (es.
`input_path` punta direttamente all'output di `build_lesion_matrix.py`, `parcellate=false`, ~1
milione di feature) salva `matrix.npy` con la dimensionalità grezza di X (`clustering.py` non
riduce mai la dimensionalità, la matrice non cambia forma). L'utente apre quel run nell'app,
vede il messaggio "Rerun dim_reduction pipeline with viz_n_components 2 or 3" — ma
`clustering.json` non ha affatto un campo `viz_n_components` da impostare, e anche rilanciando
`clustering.py` la dimensionalità di `matrix.npy` resterebbe quella di X (fissata a monte da
`build_lesion_matrix.py`, non da nessuna opzione di `clustering.py`): il messaggio indica
un'azione che non risolverebbe il problema.

**Stato: Implementato (21/08) — vedi #44, stesso fix nello stesso punto.**

### 44. `embedding_app`: messaggio "rerun dim_reduction pipeline" impreciso per un run `clustering.py`

Stesso messaggio del #43 — generalizza anche al caso più comune (non solo la matrice
voxel-wise): qualunque run `clustering.py` la cui X salvata abbia >3 colonne (es. un embedding
UMAP a 10 componenti passato come `input_path` a `clustering.py`, che lo clusterizza e lo
risalva inalterato) genera lo stesso messaggio fuorviante — "Rerun dim_reduction pipeline"
implica che la pipeline produttrice sia `dim_reduction.py`, quando in questo scenario è
`clustering.py` a non aver mai avuto motivo/modo di ridurre la dimensionalità. Lesson #12
(messaggio scritto per un solo consumatore, mai aggiornato quando l'app è stata estesa
all'altro).

**Stato: Implementato (21/08), stesso fix di #43.** `load_run` biforca ora sul `run.pipeline`
del run indisplayable: per `"dim_reduction"` il messaggio resta quello originale
("rerun dim_reduction.py with viz_n_components 2 or 3"); per ogni altra pipeline (oggi solo
`"clustering"`) il messaggio dice esplicitamente che quella pipeline non riduce la
dimensionalità da sé, e suggerisce di puntare `input_path` a una matrice già 2-o-3
componenti (es. un output `dim_reduction.py`). Test:
`test_load_run_undisplayable_clustering_run_does_not_suggest_viz_n_components`
(`tests/unit/test_embedding_app.py`) — verificato fallire su codice pre-fix (messaggio
conteneva `viz_n_components`), passa col fix.

### 45. `embedding_app`: `app.run()` non protetto da try/except

**Target**: [src/pipeline/embedding_app.py:60](src/pipeline/embedding_app.py#L60)

```python
logging.info("serving %d run(s) on http://127.0.0.1:%d - Ctrl+C to stop", len(runs), args.port)
app.run(debug=args.debug, port=args.port)     # <- nessun try/except
return 0
```

Lesson #9: nessuna protezione attorno alla chiamata che avvia il server Dash/Flask.

**Esempio concreto**: `--port 8060` è già occupato (l'utente ha lasciato un'istanza precedente
dell'app aperta in un altro terminale, o `run_understanding_umap_dash`/un altro servizio locale
usa quella porta) — `app.run(...)` solleva `OSError: [Errno 48] Address already in use` come
traceback grezzo, invece di un messaggio chiaro tipo "porta 8060 già in uso, scegli
`--port` diverso o chiudi l'istanza precedente" con `return 1` pulito.

**Stato: Implementato (21/08).** `app.run(...)` avvolta in `try/except OSError` →
`logging.error` + `return 1`. `KeyboardInterrupt` (Ctrl+C, il meccanismo di stop documentato
dell'app) deliberatamente **non** catturato — uno shutdown pulito, non un fallimento da
segnalare. Nuovo file di test (`src/pipeline/embedding_app.py::main()` non aveva alcuna
copertura diretta prima d'ora, solo `src/analysis/embedding_app.py` era testato):
`tests/unit/test_pipeline_embedding_app.py` — 3 test (nessun run trovato, `build_app`
ValueError, e la regressione `test_main_server_port_in_use_returns_1_not_raw_traceback`,
`app.run()` monkeypatchato per sollevare `OSError`) — verificato fallire su codice pre-fix
(`OSError` grezza), passa col fix (`return 1`).

### 46. `build_lesion_matrix`: `group_filter=None` salta la validazione naming soggetto

**Target**: [src/features/lesion.py:267-268](src/features/lesion.py#L267) — stesso pattern del
#26, qui in `_discover_lesion_files`:

```python
if group_filter is not None:
    subject_dirs = [s for s in subject_dirs if group_of(s) in group_filter]
```

`group_of(s)` chiamata solo se `group_filter` è impostato — lesson #4/#17. **Esempio
concreto**: identico al #26 ma per `build_lesion_matrix.py`: con `group_filter=null`, un nome
di cartella soggetto malformato (`sub_STUNIPD0099` invece di `sub-STUNIPD0099`, trattino
sostituito da underscore in una copia manuale) non viene mai validato da `group_of`, entra
silenziosamente nella matrice come se fosse un soggetto valido.

**Stato: Implementato (21/08), stesso giro di #26.** `_discover_lesion_files` costruisce ora
`dir_groups = {s: group_of(s) for s in subject_dirs}` incondizionatamente, prima del branch
`if group_filter is not None` — stesso schema esatto di #26, qui applicato a `subject_dirs`
(che `discover_files_by_subject` non copre, essendo popolato da un glob di cartelle
indipendente). Nota: per una cartella soggetto senza alcun file lesione al suo interno (0
contributo a `by_subject`), il gap era comunque già parzialmente coperto dal controllo
esistente "N subject dirs ma M lesion masks" (`ValueError` generico) — il fix rende
l'errore specifico ("does not match expected naming") invece che un mismatch di conteggio
poco informativo. Test:
`test_build_lesion_matrix_malformed_subject_dir_name_raises_even_without_group_filter`
(`tests/unit/test_features_lesion.py`) — verificato fallire su codice pre-fix (messaggio
generico di mismatch, non la naming), passa col fix (messaggio esplicito sul naming).

### 47. `build_lesion_matrix`: `reference_template_path` di produzione è la maschera di un singolo paziente

**Target**: `config/pipelines/build_lesion_matrix.json:13`

```json
"reference_template_path": "data/clinical_connectome/derivatives/UNIPD/WashU/manual_masks/sub-STUNIPD0001/anat/sub-STUNIPD0001_space-MNI152NLin6Asym_label-lesion_mask.nii.gz"
```

**Verificato**: la config di produzione reale (`yan300s1`, quella citata da `docs/guides/
matrix_building.md`) usa come griglia di riferimento comune la maschera di lesione del
soggetto `sub-STUNIPD0001` — non un template MNI152 canonico (es.
`MNI152_T1_2mm_brain.nii.gz` di FSL). Il docstring di `load_reference_image`
(`src/features/lesion.py:280-299`) motiva esplicitamente la scelta di un `reference_template_
path` esplicito come "e.g. a canonical MNI152 2mm template" — la config reale non rispetta
quell'aspettativa, anche se lo spazio (`MNI152NLin6Asym`) è coerente.

**Esempio concreto**: se `sub-STUNIPD0001` venisse mai rimosso dalla coorte (es. escluso per
qualità dei dati, o il dataset WashU riorganizzato), l'intera griglia voxel di produzione
dipenderebbe dal file di un singolo paziente che potrebbe non esistere più — un fallimento
inatteso (`FileNotFoundError` su un percorso che sembra "template", non "soggetto specifico")
per chiunque non sappia che quel path punta in realtà a dati di un paziente reale.

**Stato: Documentato, valore non cambiato (21/08, decisione utente).** Scelta di dato/config,
non un bug di codice — cambiare a un vero template MNI152 altererebbe la griglia voxel di
ogni matrice di produzione futura, una decisione che non mi compete prendere da solo. Nota
aggiunta in `docs/dev/lesion_matrix.md` che documenta esplicitamente il rischio e rimanda a
questo finding — promemoria per chi tocca `build_lesion_matrix.json` la prossima volta.

### 48. `build_lesion_matrix`: `excluded_by_group` mai persistito in `config.md`/manifest

**Target**: [src/pipeline/build_lesion_matrix.py:85-91,152-190](src/pipeline/build_lesion_matrix.py#L85)

```python
if excluded_by_group:
    logging.info("%d subject(s) excluded by group_filter=%s: %s", len(excluded_by_group), config.group_filter, excluded_by_group)
```

`excluded_by_group` viene solo **loggato** (INFO, nel file di log della run) — mai scritto in
`_config_summary`/`_summary_lines`/`_build_readme_lines`, quindi mai presente nel `config.md`
persistito accanto a `matrix.npy`, a differenza di ogni altro parametro rilevante della run.

**Esempio concreto**: 6 mesi dopo un run di produzione, qualcuno ispeziona
`data/derived/lesion_matrix/21-07_s1.1/config.md` per capire perché quella matrice ha 1150
soggetti invece dei ~1200 attesi per quei 4 dataset — il `config.md` non menziona affatto quanti
soggetti sono stati esclusi da `group_filter` né chi erano, l'unica fonte è il file di log
grezzo sotto `logs/build_lesion_matrix/`, che potrebbe essere stato pulito/ruotato nel
frattempo (i log non sono un artefatto "permanente" allo stesso titolo di `config.md`).

**Stato: Implementato (21/08), insieme a #49 (stesso file, stesso giro di edit).**
`_summary_lines` ora aggiunge sempre una sezione "## Excluded by group_filter" — lista i
subject_id esclusi (con `config.group_filter` per contesto) o "None." se nessuno escluso.
`excluded_by_group` propagato attraverso `_build_readme_lines`/`_build_report`/`_write_report`
(nuovo parametro in ciascuna). Test:
`test_build_lesion_matrix_group_filter_excludes_hc` (`tests/integration/
test_build_lesion_matrix_pipeline.py`, esteso con nuove assert) — verificato fallire su
codice pre-fix (`config.md` senza traccia dell'esclusione), passa col fix.

### 49. `build_lesion_matrix`: `params_summary` più povero dei sibling

**Target**: [src/pipeline/build_lesion_matrix.py:178-190](src/pipeline/build_lesion_matrix.py#L178)
(`_summary_lines`)

A differenza di `dim_reduction.py`/`clustering.py`, che includono sempre una riga esplicita
`f"Params used: {json.dumps(params)}"` nel proprio summary (usata anche come contratto
programmatico da `embedding_app.py::run_params`, vedi finding #25), `build_lesion_matrix.py`'s
`_summary_lines` non include l'equivalente — solo la config JSON generica in `_config_summary`
(che include già `binarize_threshold`/`resample_interpolation`/etc., quindi l'informazione
*c'è*, ma non nella forma "Params used: {...}" a riga singola che gli altri script standardizzano
e che un consumatore automatico potrebbe cercare per coerenza tra le 4 pipeline di modellazione.

**Stato: Implementato (21/08), vedi #48.** Nuovo helper `_params_used(config)` — stesso dict
già passato ad `append_run_log_entry` (`{"parcellate": ..., "binarize_threshold": ...}`, i
campi che davvero controllano la costruzione della matrice) — esposto anche come riga
`f"Params used: {json.dumps(...)}"` in `_summary_lines`, stessa convenzione a riga singola di
`dim_reduction.py`/`clustering.py`. `embedding_app.py::run_params` non scopre comunque run
`build_lesion_matrix.py` oggi (`PRODUCTION_PIPELINES` include solo `dim_reduction`/
`clustering`) — questo fix è per coerenza tra le 4 pipeline, non chiude un gap funzionale
attivo. Test: `test_build_lesion_matrix_config_md_has_params_used_line`
(`tests/integration/test_build_lesion_matrix_pipeline.py`) — verificato fallire su codice
pre-fix (riga assente), passa col fix.

---

## LOW

### 50. `mask_fc`: check ridondante/parziale su `fc.index`

**Target**: [src/features/functional.py:266-268](src/features/functional.py#L266) (`mask_dataset_fc`)
vs. [:134-137](src/features/functional.py#L134) (`mask_fc_by_lesion`)

```python
# mask_dataset_fc, prima di chiamare mask_subject_fc:
if list(fc.index) != list(node_names):
    raise ValueError(f"{subject}: FC node order in {fc_path} does not match the atlas order")
...
# mask_subject_fc -> mask_fc_by_lesion, ricontrolla COMPLETAMENTE:
if list(fc.index) != list(node_names):
    raise ValueError(...)
if list(fc.columns) != list(node_names):
    raise ValueError(...)
```

`mask_dataset_fc` ricontrolla solo `.index` (non `.columns`) subito prima di chiamare
`mask_subject_fc`, che internamente rifà lo stesso identico controllo su `.index` **e** aggiunge
quello su `.columns` — il controllo esterno è ridondante (mai l'unico a bloccare qualcosa,
`mask_fc_by_lesion` lo rifà comunque) e al tempo stesso parziale (non copre `.columns`, che
resta scoperto se mai qualcuno rimuovesse il controllo interno pensando che quello esterno
bastasse). Non un bug funzionale oggi, solo doppio lavoro e superficie di manutenzione confusa.

**Stato: Implementato (22/08).** Rimosso il controllo ridondante/parziale in `mask_dataset_fc`
(solo `.index`) — `mask_subject_fc` → `mask_fc_by_lesion` fa già il controllo completo
(`.index` **e** `.columns`), stesso tipo di eccezione già catturato dallo stesso
`except (OSError, ValueError, ImageFileError, pd.errors.ParserError)`. Nessun cambio di
comportamento osservabile (solo il messaggio d'errore cambia leggermente, mai asserito da
nessun test) — pura semplificazione, nessun test di regressione necessario. Suite
`test_features_functional.py` riverificata verde (33/33 al momento di questo fix — 34/34 a
fine sessione, dopo l'aggiunta del test di #55 allo stesso file; incl. il test del soggetto con
node-order mismatch che esercita esattamente questo percorso).

### 51. `mask_fc`: test coverage di `load_mask_fc_config` limitata al solo `group_filter`

**Verificato**: `grep -n "^def test_mask_fc" tests/unit/test_build_config.py` restituisce
esattamente 3 test, tutti su `group_filter`
(`test_mask_fc_group_filter_defaults_to_none_when_absent`,
`test_mask_fc_group_filter_restricts_to_declared_groups`,
`test_mask_fc_group_filter_unknown_group_raises`) — nessun test dedicato per
`min_coverage`/`atlas_combos`/`resample_interpolation`/`binarize_threshold`/`fc_glob_template`,
tutti campi obbligatori dello stesso loader.

**Stato: Implementato (22/08).** 14 nuovi test in `tests/unit/test_build_config.py` (config
valido, `atlas_combos` multipli, 9 casi invalidi parametrizzati coprendo tutti i campi
elencati). Nessun fix di codice (`load_mask_fc_config` era già corretto) — solo copertura
mancante colmata, stesso schema di #31.

### 52. `mask_fc`: docstring ambiguo su combo successive dopo errore

**Target**: [src/pipeline/mask_fc.py:12-16](src/pipeline/mask_fc.py#L12) (docstring del modulo)

> "a subject-count mismatch or a missing atlas file for one combo stops that combo's
> processing (raises), but does not touch combos already written successfully earlier in the
> same run."

Il testo dice solo cosa succede ai combo **già scritti**, non chiarisce esplicitamente cosa
succede ai combo **non ancora processati** nello stesso lancio — dal codice (`return 1`
immediato dentro il `for combo in config.atlas_combos` in `main()`, righe 89-91) quei combo
successivi non vengono mai nemmeno tentati, comportamento identico al finding #29 di
`build_fc_matrix.py` ma qui non descritto affatto, lasciando la lettura ambigua tra "salta solo
questo combo e continua" e "interrompe tutto da qui in poi" (la seconda è quella vera).

**Stato: Implementato (22/08).** Docstring di `mask_fc.py` esteso per dichiarare esplicitamente
che un raise interrompe **tutti** i combo restanti nella stessa config, con una nota sul
perché questo modulo non replica l'isolamento per-combo di `build_fc_matrix.py` (#29): un
fallimento qui (atlante/lesione/FC) è più spesso un problema di config/dati che si ripeterebbe
identico su ogni combo successivo, a differenza del gap genuinamente per-combo di
`build_fc_matrix.py`. Nessun cambio di comportamento, solo doc.

### 53. `build_fc_matrix`: combo di riferimento `Yan200TianS2Buckner7N` assente dalle config di produzione

**Verificato**: sia `config/pipelines/mask_fc.json` che `config/pipelines/build_fc_matrix.json`
elencano esattamente gli stessi 11 `atlas_combos` — ogni combinazione `Yan{100,200,300,400}
TianS{1,2,3}Buckner7N` tranne **`Yan200TianS2Buckner7N`**, l'unico buco in una griglia altrimenti
completa 4×3=12. Nessun commento nel config né in `docs/dev/fc_matrix.md` spiega l'esclusione
(deliberata? un atlante mai scaricato su `assets/atlases/fmriprep/`? un errore di trascrizione
one-off in un `sed`/copia-incolla che ha generato la lista?).

**Stato: Documentato, config non cambiato (22/08).** Riverificato dal vivo: l'atlante
`atlas-Yan200TianS2Buckner7N` **esiste** su disco (`assets/atlases/fmriprep/`), escludendo
"mai scaricato" come spiegazione — e questo stesso combo è citato in `docs/dev/fc_matrix.md`
come quello verificato per primo contro dati WashU reali, rafforzando l'ipotesi di un gap di
trascrizione accidentale piuttosto che un'esclusione deliberata. Nota aggiunta in
`docs/dev/fc_matrix.md` con questa evidenza. Non aggiunto io stesso ai config di produzione:
cambierebbe lo scope reale di run di ricerca già in uso, una decisione per l'utente.

### 54. `build_fc_matrix`: citazione "Griffis et al. 2021 LQT" non verificabile in `knowledge/`

**Target**: `docs/dev/fc_matrix.md:13`

> "the field-standard overlap threshold for stroke lesion studies — Lesion Quantification
> Toolkit, Griffis et al. 2021"

**Verificato**: `knowledge/nemesis/` contiene `Griffis et al - 2019 - Structural
Disconnections...` e `Griffis et al - 2020 - Damage to the shortest structural paths...`, ma
**nessun** `Griffis et al - 2021` — la specifica citazione usata per giustificare
`min_coverage=0.5` (il valore di default per ogni run di `mask_fc.py`) non ha un paper
corrispondente estratto in `knowledge/`, quindi non è verificabile/rintracciabile da questo
repo senza cercare la fonte altrove. Facile scambiarla per "già verificata" perché altri paper
dello stesso autore sono effettivamente presenti.

**Stato: Documentato, non risolvibile da codice (22/08).** Riconfermato: `knowledge/` ha solo
Griffis 2019/2020, nessun 2021. Nota aggiunta in `docs/dev/fc_matrix.md` che segnala
esplicitamente la citazione come non verificabile da questo repo — recuperare/estrarre il
paper reale è un task di letteratura, non un fix di codice.

### 55. `build_fc_matrix`: `drop_constant_edges` degenera con 1 solo soggetto nella cartella

**Target**: [src/features/functional.py:320-324](src/features/functional.py#L320)

```python
fully_observed = ~np.isnan(X).any(axis=0)
is_constant = np.zeros(X.shape[1], dtype=bool)
if fully_observed.any():
    observed = X[:, fully_observed]
    is_constant[fully_observed] = observed.min(axis=0) == observed.max(axis=0)
```

Con `X.shape[0] == 1` (un solo soggetto in `masked_fc/<combo>/`), ogni colonna senza `NaN` ha
banalmente `min == max` (un solo valore) → `is_constant` è `True` per **ogni** edge completamente
osservato, `keep_mask` li scarta tutti. **Esempio concreto**: un debug in cui `mask_fc.py` è
stato rilanciato con `group_filter` ristretto a un solo soggetto per test rapido, poi
`build_fc_matrix.py` lanciato per errore sulla stessa cartella invece che su quella completa —
il matrice risultante ha 0 (o quasi 0) edge, nessun errore esplicito segnala che la causa è "solo
1 soggetto", solo un log generico "N edge dropped" che con N = quasi tutte le colonne
sembrerebbe un problema nei dati piuttosto che nel numero di soggetti.

**Stato: Implementato (22/08).** `drop_constant_edges` ora rileva `X.shape[0] <= 1` all'inizio
e ritorna `X` invariato (nessun edge scartato) con un `logging.warning` esplicito che nomina
la causa reale, invece di far scattare il controllo "min==max" degenere. Test:
`test_drop_constant_edges_single_subject_keeps_all_edges`
(`tests/unit/test_features_functional.py`) — verificato fallire su codice pre-fix (0 edge
sopravvissuti), passa col fix (tutti gli edge mantenuti, warning loggato).

### 56. `dim_reduction`: `load_tuning_grid` non valida valori hashable

**Target**: [src/analysis/params.py:61-63](src/analysis/params.py#L61)

```python
for key, values in grid.items():
    if not isinstance(values, list) or not values:
        raise ValueError(...)
```

Valida che `values` sia una lista non vuota, ma non che ogni **elemento** al suo interno sia
hashable — lesson #8 (valore foglia JSON non tipizzato prima di finire come chiave di
dizionario/tupla). `run_tuning_sweep`/`run_clustering_tuning_sweep` costruiscono
`combo = tuple(combo_values)` e lo usano come chiave di `embeddings_by_combo`/nei `groupby`.

**Esempio concreto**: un `tuning_grid` scritto a mano con un valore JSON annidato per errore di
battitura (`"n_neighbors": [5, 15, [30]]` invece di `[5, 15, 30]`, una parentesi quadra di
troppo) supera `load_tuning_grid` (è comunque una lista non vuota) ma fa fallire
`itertools.product`/`tuple(combo_values)` con `TypeError: unhashable type: 'list'` nel primo
punto in cui quel valore viene usato come chiave — un errore criptico rispetto a un messaggio di
validazione esplicito al caricamento del config.

**Stato: Implementato (22/08).** `load_tuning_grid` verifica ora che ogni valore di ogni lista
non sia una lista/dict annidati (`isinstance(value, (list, dict))`) — `ValueError` esplicito
al caricamento, con la chiave e il valore incriminati. Test:
`test_load_tuning_grid_nested_list_value_raises` + `test_load_tuning_grid_nested_dict_value_raises`
(`tests/unit/test_params.py`) — entrambi verificati fallire su codice pre-fix
(`DID NOT RAISE`), passano col fix.

### 57. `dim_reduction`: `evaluate_pca_varimax` fitta PCA due volte per combinazione

**Target**: [src/analysis/tuning.py:157-161](src/analysis/tuning.py#L157)

```python
def evaluate_pca_varimax(X: np.ndarray, params: dict) -> tuple[np.ndarray, float]:
    fitted = PCA(n_components=params["n_components"]).fit(X)        # fit #1 (solo per lo score)
    embedding = pca_varimax_embed(X, params)                        # fit #2, interno a pca_varimax_embed
    score = float(fitted.explained_variance_ratio_.sum())
    return embedding, score
```

`pca_varimax_embed` (`src/analysis/reduction.py:76-77`) fa **anche lei** internamente
`PCA(n_components=params["n_components"]).fit(X)` — la stessa identica PCA viene quindi fittata
due volte per ogni combinazione del tuning, una volta solo per leggere
`explained_variance_ratio_.sum()` (che potrebbe essere letto dal fit interno a
`pca_varimax_embed`, se questa lo esponesse). **Esempio concreto**: un tuning `pca_varimax` con
`n_components` che sweeppa `[2, 5, 10, 20]` su una matrice a 372 feature (parcellata) — ogni
combinazione paga il costo di 2 decomposizioni SVD invece di 1, un raddoppio evitabile del tempo
di calcolo per l'intero sweep.

**Stato: Implementato (22/08).** `pca_varimax_embed` refattorizzata: la logica condivisa
(fit PCA + loadings scalati + rotazione varimax + regressione) isolata in una nuova
`_pca_varimax_fit(X, params) -> (embedding, fitted_pca)`, riusata sia da `pca_varimax_embed`
(ritorna solo l'embedding, contratto invariato per il registry `REDUCTION_METHODS`) sia da
`evaluate_pca_varimax` (legge `fitted.explained_variance_ratio_` dallo stesso fit, mai un
secondo `PCA(...).fit(X)` separato). Test: `test_evaluate_pca_varimax_fits_pca_only_once`
(`tests/unit/test_tuning.py`, `PCA.fit` monkeypatchata con un contatore) — verificato fallire
su codice pre-fix (2 chiamate), passa col fix (1 chiamata).

### 58. `clustering`: docstring `compute_rsc_eigengap` disallineato di un indice

**Target**: [src/analysis/consensus_clustering.py:129-146](src/analysis/consensus_clustering.py#L129)

```python
def compute_rsc_eigengap(cooccurrence_matrix: np.ndarray, k: int) -> float:
    """Gap between the k-th and (k-1)-th (1-indexed) sorted eigenvalues ..."""
    ...
    eigenvalues = eigh(laplacian, eigvals_only=True, subset_by_index=[0, k])
    eigenvalues = np.sort(eigenvalues)
    return float(eigenvalues[k] - eigenvalues[k - 1])
```

Il docstring dichiara "the k-th and (k-1)-th (1-indexed)" eigenvalue — ma `eigenvalues` è un
array 0-indicizzato: `eigenvalues[k]` è il **(k+1)-esimo** autovalore (1-indexed), non il
k-esimo. Il codice è internamente coerente (usa `k`/`k-1` come indici 0-based in modo
consistente con `subset_by_index=[0, k]`, che prende k+1 autovalori), ma la *descrizione a
parole* nel docstring è sfalsata di una posizione rispetto a cosa il codice calcola realmente.
Non un bug funzionale — solo una fonte di confusione per chi legge il docstring per capire
l'indice esatto senza rileggere il codice.

**Stato: Implementato (22/08).** Prima riga del docstring corretta da "k-th and (k-1)-th" a
"(k+1)-th and k-th" — allineata alla frase, già corretta, due righe sotto ("difference between
k+1-th and k-th ordered eigenvalues") che prima la contraddiceva. Solo testo, nessun cambio di
codice (il codice era già internamente coerente).

### 59. `clustering`: plot sempre sulle prime 2 colonne grezze

**Target**: [src/pipeline/clustering.py:189-196](src/pipeline/clustering.py#L189)
(`_run_one_method`) — `plot_clusters_2d(X[:, :2], cluster_labels, ...)`.

Lesson #16, variante latente: qui non è un embedding UMAP/t-SNE sliced (quel caso specifico è
già gestito correttamente altrove via `embedding_for_viz`), ma `clustering.py` disegna sempre
`X[:, :2]` — le prime 2 colonne **grezze** della matrice di input, qualunque essa sia. Il
docstring del modulo lo dichiara esplicitamente come "a coarse sanity check only, since those 2
features are not a meaningful projection" — quindi non è un bug nascosto, ma resta un caso
latente di lesson #16 non attivo con la config di default odierna (dove `clustering.py` riceve
tipicamente un embedding già a 2 componenti come `input_path`, rendendo `X[:, :2]` l'intero X).

**Esempio concreto**: `clustering.json` con `input_path` puntato direttamente a una matrice di
lesione parcellata a 372 colonne (nessun `dim_reduction.py` in mezzo, uso legittimo secondo il
docstring di `clustering.py`: "Reads a matrix artifact... a raw/parcellated matrix or an
already-computed dim_reduction embedding, this script doesn't care which") — `cluster_plot.png`
mostrerebbe le prime 2 delle 372 parcelle (probabilmente le prime 2 in ordine di label
dell'atlante, senza nessun significato particolare), un plot "vero" ma privo di qualunque
capacità diagnostica reale sulla struttura dei cluster nello spazio a 372 dimensioni.

**Stato: Moot (22/08).** Verificato dal vivo: `clustering.py`'s `_run_one_method` non chiama
più `plot_clusters_2d(X[:, :2], ...)` — usa `_resolve_viz_embedding(X, metadata,
viz_embedding_path)` (aggiunta in una sessione precedente al 15/08, 14-08-26 secondo
`docs/dev/models.md`): riusa X se già 2/3 componenti, legge un embedding companion via
`viz_embedding_path` se X ha altre dimensioni, altrimenti ritorna `None` e **salta** il plot
con un warning — mai più uno slice di X. Il finding era già risolto come effetto collaterale
di lavoro precedente a questa sessione di triage, non da un'azione di questo giro.

### 60. `dim_reduction_clustering`: asimmetria naming tag tra produzione e tuning

**Target**: [src/pipeline/dim_reduction_clustering.py:268-269](src/pipeline/dim_reduction_clustering.py#L268)
(produzione) vs. [:456-462](src/pipeline/dim_reduction_clustering.py#L456) (tuning, docstring)

In produzione, `effective_session_name` include sia il tag di riduzione che quello di clustering
(`tags = [t for t in (reduction_tag, clustering_tag) if t]`), mentre in tuning
(`_run_one_method_tuning`) l'output dir è deliberatamente `<dd-mm>_<session_name>` **senza**
tag di riduzione — documentato esplicitamente nel docstring come scelta intenzionale ("which
reduction produced the embedding is already unambiguous from the enclosing
`<reduction_method>/<method>/` folders"). Non un bug, solo un'asimmetria di naming tra i due
modi della stessa pipeline che vale la pena notare per chi si aspetta convenzioni identiche tra
`production/` e `tuning/`.

**Stato: Moot (22/08).** `src/pipeline/dim_reduction_clustering.py` non esiste più (rimosso
14/08) — verificato `ls`, nessun file. L'asimmetria descritta era interna a quel modulo
specifico (produzione vs. tuning dello stesso CLI combinato); `dim_reduction.py`/`clustering.py`
sono ora due pipeline separate, ognuna con la propria convenzione di naming interna coerente
(non un'asimmetria fra due modi della stessa pipeline, dato che quella pipeline combinata non
esiste più). Nessuna azione.

### 61. `understanding_umap_report`: nessun test per la CLI (`main()`)

**Verificato**: `grep -n "main(" tests/unit/test_understanding_umap_report.py` non restituisce
nessuna occorrenza — il test file copre le funzioni di `src/analysis/understanding_umap_report.py`
(`build_grid_figure`, `build_slider_section`, `load_tuning_data`, ecc.) ma non
`src/pipeline/generate_understanding_umap_report.py::main()` (parsing argomenti, gestione
`FileNotFoundError`/`ValueError` a livello CLI, messaggi di log). Un bug introdotto solo nel
livello CLI (es. un argomento mal gestito, un cambio nell'except handling) non verrebbe
intercettato da nessun test esistente.

**Stato: Implementato (22/08).** Nuovo file `tests/unit/test_generate_understanding_umap_report_pipeline.py`
— 3 test su `main()`: successo end-to-end, `--umap-tuning-dir` mancante (`FileNotFoundError` →
`return 1`), mismatch di coorte fra UMAP e t-SNE (`ValueError` → `return 1`). Nessun fix di
codice (`main()` era già corretto) — solo copertura mancante colmata, stesso schema di #31/#51.

### 62. `understanding_umap_report`: lista `metrics` non deduplicata

**Target**: [src/analysis/understanding_umap_report.py:1099](src/analysis/understanding_umap_report.py#L1099)

```python
metrics = sorted(p.name.split("=")[1] for p in umap_tuning_dir.glob("metric=*"))
```

Nessun `set()` esplicito prima di `sorted()` — oggi innocuo perché ogni elemento viene da un
nome di cartella reale sul filesystem (intrinsecamente unico), ma la costruzione non è
difensiva: se in futuro questa lista venisse costruita concatenando più sorgenti (es. unendo i
metric di più `umap_tuning_dir` in un report aggregato), un duplicato non verrebbe scartato e
`build_leaf_page` verrebbe chiamata due volte per lo stesso metric, sovrascrivendo il proprio
output senza errore.

**Stato: Implementato (22/08).** `set()` esplicito prima di `sorted()`. Puramente difensivo —
confermato ancora oggi innocuo (ogni elemento viene da un glob reale su filesystem,
intrinsecamente unico) e non facilmente testabile senza mockare `Path.glob` per iniettare un
duplicato artificiale che non può esistere su un filesystem reale — nessun test di regressione
aggiunto per questo motivo (nessun bug attivo da riprodurre). Suite
`test_understanding_umap_report.py` riverificata verde (16/16).

### 63. `understanding_umap_report`: README non menziona questa pipeline

**Verificato**: `README.md`'s "What's implemented so far" elenca retrieval, atlas building, FC
masking/matrix building, SDC, dim_reduction/clustering — nessuna menzione di
`generate_understanding_umap_report.py`/`understanding_umap_report.py`, nonostante sia una
pipeline CLI completa (`src/pipeline/generate_understanding_umap_report.py`) con una propria
guida implicita nel proprio docstring. Chi legge solo il README per farsi un'idea di "cosa c'è"
non scoprirebbe che questo strumento esiste.

**Stato: Implementato (22/08).** Nuovo paragrafo "Embedding exploration tools" in `README.md`
(dopo la sezione dim_reduction/clustering) che nomina esplicitamente sia `embedding_app.py`
(app Dash live) sia `generate_understanding_umap_report.py` (report HTML statico), con
puntatori alle rispettive guide (`docs/guides/embedding_app.md`/`understanding_umap_report.md`,
entrambe già esistenti). Solo doc, nessun cambio di codice.

### 64. `embedding_app`: sentinella `-1` trapelerebbe in UI una volta ricollegata l'app

**Target**: [src/analysis/embedding_app.py:258,724-726](src/analysis/embedding_app.py#L258)

```python
NO_N_COMPONENTS = -1
...
n_components_values = n_components_options(runs, modality, pipeline, method, metric)
options = [{"label": str(n), "value": n} for n in n_components_values]
```

Per un run `clustering.py` (i cui parametri non hanno mai `n_components`, vedi CRITICAL #2's
fix con `.get(..., NO_N_COMPONENTS)`), `n_components_values` contiene letteralmente `-1` —
`{"label": str(-1), "value": -1}` mostra la stringa **"-1"** come opzione nel dropdown
"Componenti" dell'app, un dettaglio implementativo interno (il sentinel) che finisce visibile
nell'interfaccia utente senza nessuna etichetta più leggibile tipo "N/D"/"—" (come invece fa
`NO_METRIC = "—"` per il caso analogo sulla metrica).

**Stato: Implementato (22/08).** Nuovo helper `_n_components_option_label(n)` — ritorna
`NO_METRIC` ("—") quando `n == NO_N_COMPONENTS`, altrimenti `str(n)` — usato dal callback
`_update_n_components_picker` al posto di `str(n)` diretto. `value` del dropdown resta `-1`
invariato (la logica di filtro a valle non cambia), solo la `label` mostrata cambia. Test:
`test_n_components_option_label_maps_sentinel_to_readable_placeholder`
(`tests/unit/test_embedding_app.py`) — verificato fallire su codice pre-fix
(`ImportError`, la funzione non esisteva), passa col fix.

### 65. `embedding_app`: traccia Plotly vuota per color mode interamente NaN

**Target**: [src/analysis/embedding_app.py:463-478](src/analysis/embedding_app.py#L463)
(`build_embedding_figure`)

```python
if is_missing.any():
    fig.add_trace(scatter_cls(**_trace_kwargs(is_missing), ..., name="missing", ...))
fig.add_trace(
    scatter_cls(**_trace_kwargs(~is_missing), ..., name=mode.label, ...)   # <- sempre aggiunta, anche se vuota
)
```

La seconda `add_trace` non è condizionata su `(~is_missing).any()` — se **ogni** valore del
color mode è `NaN` per il run selezionato, questa traccia riceve `x=[], y=[]` (array vuoti) ma
viene comunque aggiunta al grafico, con una voce di legenda (`name=mode.label`) senza nessun
punto associato.

**Esempio concreto**: un run `dim_reduction.py` su un dataset che non ha ancora ricevuto
`enrich_lesion_metadata.py` (metadata.csv senza colonna `nihss` popolata, o con `nihss`
interamente `NaN` per un sottoinsieme di dataset senza quel campo) — selezionando color mode
"nihss" nell'app, il grafico mostra correttamente la traccia "missing" con tutti i punti in
grigio, ma la legenda include anche una voce fantasma "NIHSS (severity)" senza marker visibile,
confusa per l'utente che si chiede perché ci sia una seconda voce di legenda che non corrisponde
a nulla sul grafico.

**Stato: Implementato (22/08).** La seconda `add_trace` (la traccia colorata) è ora condizionata
su `(~is_missing).any()` — se ogni valore è NaN, solo la traccia "missing" viene aggiunta,
nessuna voce di legenda fantasma. Test:
`test_build_embedding_figure_all_missing_skips_empty_colored_trace`
(`tests/unit/test_embedding_app.py`) — verificato fallire su codice pre-fix (traccia
"NIHSS (severity)" presente con 0 punti), passa col fix (solo "missing" in legenda).

### 66. `build_lesion_matrix`: campo config `data_modality` morto

**Target**: `config/pipelines/build_lesion_matrix.json:21` (`"data_modality": "lesion"`),
`src/analysis/build_config.py:36,69,84`

**Verificato**: `data_modality` viene parsato in `BuildMatrixConfig.data_modality` e incluso in
`_config_summary`'s JSON dump (`src/pipeline/build_lesion_matrix.py:158`, solo per logging) —
ma non è mai passato a `build_lesion_matrix()` né usato per derivare `output_dir`/naming di
alcun file. A differenza di quanto il nome suggerirebbe (distinguere lesion/SDC/FC quando quelle
pipeline condivideranno lo stesso entry point), oggi non ha nessun effetto sul comportamento —
cambiarlo in un valore diverso da `"lesion"` non altera l'output in nessun modo osservabile.

**Stato: Implementato (22/08).** Campo rimosso interamente: da `BuildMatrixConfig` (dataclass),
da `load_build_matrix_config` (nessuna lettura/default residuo), da `_config_summary`
(build_lesion_matrix.py), e dal config di produzione reale
(`config/pipelines/build_lesion_matrix.json`) — coerente con code_standards §5 ("Niente campi
di config non letti da nessun codice attivo"). Verificato via `grep -rn` che nessun test lo
settava esplicitamente (era `_optional_str`, default "lesion" se assente) e nessuna doc lo
cita più. Nessun test di regressione necessario (rimozione di codice/campo morto, nessun
cambio di comportamento osservabile) — suite `test_build_config.py`/
`test_build_lesion_matrix_pipeline.py`/`test_features_lesion.py` riverificata verde
(75/75 al momento di questo fix — 76/76 a fine sessione, dopo l'aggiunta del test di #68 a
`test_features_lesion.py`).

### 67. `build_lesion_matrix`: guida dichiara un vincolo che il codice non applica

**Target**: `docs/guides/matrix_building.md` (claim su `resample_interpolation`) vs.
[src/features/lesion.py:141-148](src/features/lesion.py#L141) (`load_and_resample_atlas`)

Il codice **forza** `interpolation="nearest"` per il resample dell'atlante indipendentemente da
`config.resample_interpolation` (che si applica solo alle maschere di lesione, mai
all'atlante — il docstring di `load_and_resample_atlas` lo dice esplicitamente: "Nearest is
forced regardless of the lesion masks' resample_interpolation"). Se la guida utente descrive
`resample_interpolation` come un'opzione che governa "il resampling" in generale (senza
specificare che l'atlante ne è sempre escluso), un utente che imposta
`resample_interpolation: "linear"` aspettandosi che valga anche per l'atlante otterrebbe un
comportamento diverso da quanto la guida lascia intendere, anche se il codice è corretto (un
atlante di label discrete non può essere interpolato linearmente senza inventare valori).

**Stato: Implementato (22/08).** Riga della tabella parametri in `docs/guides/matrix_building.md`
riscritta: chiarisce che `resample_interpolation` governa **solo** il resampling delle
maschere di lesione (valori validi: `linear`/`nearest`/`continuous`), mai l'atlante (sempre
`nearest`, indipendentemente dal config, quando `parcellate: true`) — la vecchia riga
("Deve sempre essere 'nearest'") era essa stessa fattualmente scorretta in un altro modo
(il campo può legittimamente essere `linear`/`continuous` per le maschere). Solo doc.

### 68. `build_lesion_matrix`: `binarize_threshold=1.0` degenere senza messaggio chiaro

**Target**: [src/features/lesion.py:310-312](src/features/lesion.py#L310) (`_load_and_binarize_lesion`),
[src/features/functional.py:120](src/features/functional.py#L120) (`resample_lesion_to_atlas`, stesso pattern)

```python
data = img.get_fdata() > binarize_threshold
return data.ravel().astype(np.uint8)
```

Nessuna validazione che `binarize_threshold` sia in un range sensato (es. `(0, 1)` per una
maschera già normalizzata) prima di usarlo nel confronto `>`.

**Esempio concreto**: un valore di config `binarize_threshold: 1.0` scritto per errore
(intendendo "soglia al 100%", un'interpretazione plausibile ma sbagliata per un confronto `>`
stretto) su una maschera i cui valori dopo il resampling non superano mai esattamente 1.0 (il
caso tipico: valori in `[0, 1]` con interpolazione) produce `data > 1.0` sempre `False` — una
maschera di lesione binarizzata interamente a zero per **ogni** soggetto, silenziosamente:
`X_voxelwise` è tutta zero, `lesion_volume_voxels` è 0 per tutti, e più a valle
`_drop_constant_features` scarterebbe ogni colonna (tutte costanti a 0), producendo una matrice
a 0 feature — un fallimento che si manifesterebbe altrove (es. `X.shape[1] == 0`) con un
messaggio che non indica affatto la causa reale (`binarize_threshold` troppo alto).

**Stato: Implementato (22/08).** `_voxelwise_matrix_with_volume` verifica ora, in aggregato
(non per singolo soggetto — un soggetto con 0 voxel lesi è un caso di dominio legittimo,
lesson #6), se `lesion_volume_voxels` è 0 per **ogni** soggetto della coorte — `ValueError`
esplicito che nomina `binarize_threshold` come causa probabile. Test:
`test_build_lesion_matrix_binarize_threshold_one_raises`
(`tests/unit/test_features_lesion.py`) — verificato fallire su codice pre-fix
(`DID NOT RAISE`, matrice costruita silenziosamente a 0 voxel per tutti), passa col fix.

---

### 69. `clustering`: `load_consensus_config`/`consensus_suggestion_lines`/`consensus_config` senza test unitari dedicati

**Non un finding dell'audit del 15/08** — trovato il 22/08 mentre si verificava (su richiesta
dell'utente) 2 voci `git stash` residue da mesi prima, riferite a commit non più raggiungibili
dalla storia di `main` (`5b5a7b1`/`9beba89`). Gli stash contenevano un draft (doc + test) per la
feature RSC/Monti consensus clustering — verificato che la feature stessa
(`load_consensus_config` in `src/analysis/params.py`, `consensus_suggestion_lines`/
`CONSENSUS_METRIC_COLUMNS` in `src/analysis/clustering_tuning.py`, wiring `consensus_config` in
`run_clustering_tuning_sweep`) è **già implementata e in uso in produzione**
(`src/pipeline/clustering.py`) — evidentemente completata per un'altra via, non da questi
stash. Gli stash stessi non si applicano più puliti (`git apply --check` fallisce: 2 file
target non esistono più — `docs/dev/analysis.md`/`docs/methods/clustering.md`, rimossi in
riorganizzazioni successive; 3 file hanno conflitti, l'implementazione reale è cambiata da
allora — es. `"dbscan"` non è più un metodo esistente, sostituito da `"hdbscan"`).

**Verificato però un gap reale e vivo**: `grep` su `test_load_consensus_config`/
`test_run_clustering_tuning_sweep_adds_rsc`/`consensus_suggestion_lines` in tutta `tests/`
non restituiva nulla — la feature, già shippata e usata, non aveva **nessuna** copertura di
test diretta (solo indiretta, se un config reale avesse mai impostato un blocco `"consensus"`
— nessuno dei config di produzione committati lo fa).

**Stato: Implementato (22/08).** Stash scartati (`git stash drop` su entrambi — contenuto
superato, non applicabile). Test freschi scritti contro l'API attuale (non applicando il vecchio
patch): 8 nuovi in `tests/unit/test_params.py` (`load_consensus_config` — assente→`None`,
valido rsc+monti, solo rsc, metodo non eleggibile con `"hdbscan"` come esempio aggiornato,
chiave sconosciuta, non-dict, `n_repeats`/`subsample_fraction` invalidi) + 6 nuovi in
`tests/unit/test_clustering_tuning.py` (`consensus_config=None` invariato, metodo non
eleggibile rifiutato, colonne rsc+monti aggiunte, solo rsc omette monti,
`consensus_suggestion_lines` vuota/con suggerimenti). Nessun fix di codice (l'implementazione
era già corretta) — solo copertura mancante colmata. Suite intera: **762 passed, 0 failed, 12
skipped**.

---

## Verificato e corretto

**MEDIUM (#26-#49) — giro chiuso il 21/08/26.** 18 finding implementati con fix di
codice/config + test di regressione (#26, #27, #28, #29, #30, #31 [solo test coverage,
nessun bug], #34, #35, #36, #41, #43, #44, #45, #46, #48, #49), 4 di sola documentazione
(#32, #33, #38, #42), 2 documentati senza cambiare valori scientifici su decisione utente
(#37, #47), 2 chiusi in triage come moot/sussunti dalla rimozione di `dim_reduction_clustering.py`
(#39, #40). Suite intera riverificata verde: **727 passed, 0 failed, 12 skipped** (esclusi i 2
file `bcblib`-dipendenti).

**LOW (#50-68) — giro chiuso il 22/08/26 (esecuzione autonoma, wakeup schedulato senza utente
disponibile).** 19 finding triageati: 12 implementati con fix di codice reale + test di
regressione (#55, #56, #57, #64, #65, #68 — bug veri; #50, #66 — semplificazione/rimozione
codice morto, nessun test necessario, comportamento invariato; #52, #58, #63, #67 — solo
documentazione), 3 di puro test-coverage senza bug (#51, #61, e #62 difensivo senza bug attivo
né test aggiunto), 2 documentati senza modificare config/dati (#53 — combo atlante
verosimilmente omesso per errore, verificato che l'atlante esiste comunque su disco; #54 —
citazione non verificabile in `knowledge/`), 2 chiusi in triage come moot (#59 — già risolto da
lavoro precedente al 15/08, `_resolve_viz_embedding`; #60 — targettava
`dim_reduction_clustering.py`, rimosso). Trovata e corretta anche un'inconsistenza di stato
residua in CRITICAL #5 (testo "Aperto" mai aggiornato dopo la chiusura reale via HIGH #10).
Suite intera riverificata verde: **748 passed, 0 failed, 12 skipped** (esclusi i 2 file
`bcblib`-dipendenti).

**#69 (fuori audit) — chiuso il 22/08/26.** Trovato mentre si verificavano 2 stash residui
(non correlati alla sessione, richiesta esplicita dell'utente di verificarli prima di
scartarli) — gap di test reale per una feature (RSC/Monti consensus clustering) già
implementata e in uso, mai coperta da test diretti. Stash scartati, 14 nuovi test scritti
contro l'API attuale. Suite intera riverificata verde: **762 passed, 0 failed, 12 skipped**.

## Lezioni apprese

Aggiunta `lessons_learned.md` #28 (21/08): tightening di una validazione condivisa e a basso
livello (`group_of()` sempre chiamata, #26/#46) ha rotto 44 test in 5 file, tutti non
correlati al codice toccato — il vero raggio d'impatto era invisibile leggendo solo il diff,
visibile solo eseguendo la suite. Vedi `lessons_learned.md` per il testo completo.

Nessun pattern genuinamente nuovo emerso durante il giro LOW (22/08) — i fix ricadono tutti in
pattern già coperti (validazione mancante, error handling, doc stale, test coverage);
`lessons_learned.md` non aggiornato per questo giro.
