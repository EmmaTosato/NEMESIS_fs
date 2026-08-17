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

**Stato: Aperto** (analisi completa, fix non ancora implementato).

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

**Stato: Aperto** (fix di codice non ancora implementato — il rischio è confermato reale ma non
osservato nella coorte odierna).

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
(`DID NOT RAISE`) sul codice pre-fix via `git stash`, passa col fix. Suite completa:
`tests/unit/test_features_lesion.py` 16/16 passed; suite intera (esclusi i 2 file
`bcblib`-dipendenti) 593 passed, 23 failed (tutti preesistenti — `embedding_app`/
`embedding_coloring`, CRITICAL #2/HIGH #12, non toccati da questo fix), 12 skipped.

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

**Stato: Aperto** (soluzione proposta, in attesa di conferma prima di implementare).

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

**Stato: Aperto** (nessun fix implementato — serve decidere come, non solo se, gestire il caso
non-binario: vedi anche finding #7, stesso nodo).

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

**Stato: Aperto** (nessun fix implementato).

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

**Fix non ancora deciso** - opzioni da discutere quando si arriva a `n_components` di produzione
> 2 per `pca_varimax` (oggi non ancora configurato): (a) non offrire mai un refit-viz per
`pca_varimax`, mostrare solo `unico.png`/nessun plot 2D quando `n_components != viz_n_components`,
con messaggio esplicito del perché; (b) refittare ma etichettare chiaramente il plot come
"proiezione 2D indipendente, non i fattori di produzione"; (c) restringere `viz_n_components`
lato config a dover sempre coincidere con `n_components` per questo metodo specifico (nessun
refit necessario, ma perde la possibilità di un preview 2D quando K è alto).

**Stato: Aperto** (nessun fix implementato - dormiente, non urgente finché `pca_varimax` non ha
una config di produzione reale con K>2).

---

## HIGH

### 9. `mask_fc`: nessun isolamento per-soggetto nel loop di masking
[src/features/functional.py:264](src/features/functional.py#L264) — un soggetto
problematico abortisce l'intero run, non solo la sua combo. **Stato: Aperto.**

### 10. `mask_fc`: output dir non ripulita con `overwrite=True`
[src/pipeline/mask_fc.py:63](src/pipeline/mask_fc.py#L63) — stesso pattern del CRITICAL
#5, qui non ancora sfruttato empiricamente ma stesso meccanismo. **Stato: Aperto.**

### 11. `dim_reduction`: `TypeError` da iperparametro non riconosciuto non catturato
[src/pipeline/dim_reduction.py:126,133](src/pipeline/dim_reduction.py#L126) — il file di
log resta vuoto (violazione §6). Riprodotto. **Stato: Aperto.**

### 12. `dim_reduction`: suite rossa oggi
`test_embedding_coloring.py::test_registry_has_expected_modes` fallisce — causa: stesso commit
del CRITICAL #2 (`embedding_app`). **Stato: Aperto.**

### 13. `clustering`: metriche di validazione sempre euclidee
[src/analysis/clustering_tuning.py:104](src/analysis/clustering_tuning.py#L104) — mai a
conoscenza della metrica reale usata dal clustering (lesson #15). **Stato: Aperto.**

### 14. `clustering`/`dim_reduction_clustering`: doc `assign_clusters_from_cooccurrence` invertita
[docs/dev/models.md:77](docs/dev/models.md#L77) — descrive semantica opposta a quella
implementata, in entrambi i sibling. **Stato: Aperto.**

### 15. `clustering`: comparison-plot in `main()` fuori da try/except
[src/pipeline/clustering.py:132](src/pipeline/clustering.py#L132) (lesson #9). **Stato: Aperto.**

### 16. `clustering`: `comparison/` ignora `config.overwrite`
[src/pipeline/clustering.py:249](src/pipeline/clustering.py#L249). **Stato: Aperto.**

### 17. `clustering`: non produce mai l'HTML interattivo del confronto
Contraddice la doc, a differenza del sibling `dim_reduction_clustering.py`. **Stato: Aperto.**

### 18. `dim_reduction_clustering`: `embed`/`embedding_for_viz`/clustering non protette da try/except
[src/pipeline/dim_reduction_clustering.py:149,157,273](src/pipeline/dim_reduction_clustering.py#L149)
— stesso gap nei 3 script della famiglia (lesson #9). **Stato: Aperto.**

### 19. `build_lesion_matrix`: `discover_files_by_subject` non incrocia subject_id con la cartella
`src/features/subject_discovery.py` (lesson #22, variante). **Stato: Aperto.**

### 20. `build_lesion_matrix`: `nibabel.ImageFileError` non coperto dal boundary
[src/pipeline/build_lesion_matrix.py:81,115](src/pipeline/build_lesion_matrix.py#L81)
(lesson #9). **Stato: Aperto.**

### 21. `understanding_umap_report`: NaN nel color mode "nihss" mai gestiti
[src/analysis/understanding_umap_report.py:211](src/analysis/understanding_umap_report.py#L211)
— confermato 139 occorrenze letterali nell'HTML di produzione reale. **Stato: Aperto.**

### 22. `understanding_umap_report`: report multi-metrica scritto parzialmente se un metric fallisce
[src/analysis/understanding_umap_report.py:1103](src/analysis/understanding_umap_report.py#L1103)
— nessun cleanup. **Stato: Aperto.**

### 23. `understanding_umap_report`: `KeyError` non catturato invece di `ValueError`
[src/analysis/understanding_umap_report.py:152](src/analysis/understanding_umap_report.py#L152)
(lesson #7). **Stato: Aperto.**

### 24. `understanding_umap_report`: `embeddings.npz` non atomico + `np.load` senza try/except
lesson #9/#21. **Stato: Aperto.**

### 25. `embedding_app`: un solo run con `config.md` corrotto nasconde tutti gli altri
[src/analysis/embedding_app.py:288,300,314](src/analysis/embedding_app.py#L288) (lesson
#21). **Stato: Aperto.**

---

## MEDIUM

### 26. `mask_fc`: validazione naming soggetto incoerente tra branch `group_filter` (lesson #4) — `src/features/subject_discovery.py`. **Stato: Aperto.**
### 27. `mask_fc`: `load_atlas` non valida index tsv↔volume prima di indicizzare (lesson #7, non attivo sui dati reali oggi). **Stato: Aperto.**
### 28. `mask_fc`: `label_table["index"]` duplicati non validati (lesson #5, non attivo sui dati reali oggi). **Stato: Aperto.**
### 29. `build_fc_matrix`: loop su `atlas_combos` non isolato (lesson #21) — un combo fallito abortisce tutti i successivi. **Stato: Aperto.**
### 30. `build_fc_matrix`: nessuna verifica di simmetria prima di estrarre il triangolo superiore. **Stato: Aperto.**
### 31. `build_fc_matrix`: `load_build_fc_matrix_config` senza test unitari dedicati. **Stato: Aperto.**
### 32. `dim_reduction`: riferimenti stale a `docs/notes/` sparsi in README/CLAUDE.md/docs/dev/docstring. **Stato: Aperto.**
### 33. `dim_reduction`: `docs/dev/models.md` dichiara `metric=jaccard` per UMAP produzione, registry reale ha `euclidean` — drift non documentato. **Stato: Aperto.**
### 34. `dim_reduction`: refit di viz nella griglia di tuning non riusa `distance_cache` — O(n²) evitabile. **Stato: Aperto.**
### 35. `clustering`: tuning `evidence_accumulation` — 350 fit invece di 50 (threshold non influenza la co-occurrence matrix). **Stato: Aperto.**
### 36. `clustering`: `tag_param` di `spectral` non corrisponde al parametro realmente swept — rischio di collisione silenziosa. **Stato: Aperto.**
### 37. `clustering`: budget split di `evidence_accumulation` (6) coincide col K finale, contraddice il proprio docstring. **Stato: Aperto.**
### 38. `clustering`: `docs/notes/` (incl. `clustering.md`) non esiste pur essendo citata come obbligatoria. **Stato: Aperto.**
### 39. `dim_reduction_clustering`: `viz_embedding` calcolato incondizionatamente anche in `fine_tuning`, mai usato lì. **Stato: Aperto.**
### 40. `dim_reduction_clustering`: stesso spreco `evidence_accumulation` del #35. **Stato: Aperto.**
### 41. `understanding_umap_report`: nessun caveat comunicato su come leggere UMAP/t-SNE. **Stato: Aperto.**
### 42. `understanding_umap_report`: riferimenti morti a `run_understanding_umap_dash` (lesson #12). **Stato: Aperto.**
### 43. `embedding_app`: messaggio errore per embedding >3D indica il campo di config sbagliato. **Stato: Aperto.**
### 44. `embedding_app`: messaggio "rerun dim_reduction.py" errato per un run `clustering.py` (lesson #12). **Stato: Aperto.**
### 45. `embedding_app`: `app.run()` non protetto da try/except (lesson #9). **Stato: Aperto.**
### 46. `build_lesion_matrix`: `group_filter=None` salta la validazione naming soggetto (lesson #4/#17). **Stato: Aperto.**
### 47. `build_lesion_matrix`: `reference_template_path` di produzione è la maschera di un singolo paziente, non un template MNI canonico — contraddice la doc. **Stato: Aperto.**
### 48. `build_lesion_matrix`: `excluded_by_group` mai persistito in `config.md`/manifest. **Stato: Aperto.**
### 49. `build_lesion_matrix`: `params_summary` più povero dei sibling. **Stato: Aperto.**

---

## LOW

### 50. `mask_fc`: check ridondante/parziale su `fc.index`. **Stato: Aperto.**
### 51. `mask_fc`: test coverage di `load_mask_fc_config` limitata al solo `group_filter`. **Stato: Aperto.**
### 52. `mask_fc`: docstring ambiguo su combo successive dopo errore. **Stato: Aperto.**
### 53. `build_fc_matrix`: combo di riferimento `Yan200TianS2Buckner7N` assente dalle config di produzione, senza spiegazione tracciata. **Stato: Aperto.**
### 54. `build_fc_matrix`: citazione "Griffis et al. 2021 LQT" non verificabile in `knowledge/`. **Stato: Aperto.**
### 55. `build_fc_matrix`: `drop_constant_edges` degenera con 1 solo soggetto nella cartella. **Stato: Aperto.**
### 56. `dim_reduction`: `load_tuning_grid` non valida valori hashable (lesson #8, latente). **Stato: Aperto.**
### 57. `dim_reduction`: `evaluate_pca_varimax` fitta PCA due volte per combinazione. **Stato: Aperto.**
### 58. `clustering`: docstring `compute_rsc_eigengap` disallineato di un indice. **Stato: Aperto.**
### 59. `clustering`: plot sempre sulle prime 2 colonne grezze (lesson #16, latente, non attivo con config di default). **Stato: Aperto.**
### 60. `dim_reduction_clustering`: asimmetria naming tag tra produzione e tuning (nota di manutenibilità, non bug). **Stato: Aperto.**
### 61. `understanding_umap_report`: nessun test per la CLI (`main()`). **Stato: Aperto.**
### 62. `understanding_umap_report`: lista `metrics` non deduplicata. **Stato: Aperto.**
### 63. `understanding_umap_report`: README non menziona questa pipeline. **Stato: Aperto.**
### 64. `embedding_app`: sentinella `-1` trapelerebbe in UI una volta ricollegata l'app. **Stato: Aperto.**
### 65. `embedding_app`: traccia Plotly vuota per color mode interamente NaN. **Stato: Aperto.**
### 66. `build_lesion_matrix`: campo config `data_modality` morto. **Stato: Aperto.**
### 67. `build_lesion_matrix`: guida dichiara un vincolo che il codice non applica (`resample_interpolation`). **Stato: Aperto.**
### 68. `build_lesion_matrix`: `binarize_threshold=1.0` degenere senza messaggio chiaro. **Stato: Aperto.**

---

## Verificato e corretto

(da riempire a lavoro concluso)

## Lezioni apprese

(da appendere a `.claude/lessons_learned.md` solo per pattern genuinamente nuovi emersi durante i
fix — non ancora applicabile, nessun fix implementato in questa sessione)
