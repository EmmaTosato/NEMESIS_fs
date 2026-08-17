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

**Stato: Aperto.**

---

### 3. `build_lesion_matrix`: check "già allineato" ignora l'affine

**Pipeline**: `build_lesion_matrix` — [src/features/lesion.py:229](src/features/lesion.py#L229), [:102](src/features/lesion.py#L102)

**Difetto**: il check di allineamento confronta solo la *shape* delle immagini, mai l'affine —
due immagini con la stessa shape ma affine diverso vengono trattate come già co-registrate,
producendo un disallineamento anatomico silenzioso tra lesione e spazio di riferimento.

**Stato: Aperto.**

---

### 4. `build_lesion_matrix`: dataset con path errato contribuisce silenziosamente 0 soggetti

**Pipeline**: `build_lesion_matrix` — [src/features/lesion.py:185](src/features/lesion.py#L185)

**Difetto**: `Path.glob` su una directory inesistente ritorna `[]` senza sollevare eccezione — un
dataset con nome/path sbagliato o non ancora recuperato da `retrieve_data.py` sparisce
dall'intera coorte senza nessun segnale.

**Stato: Aperto.**

---

### 5. `build_fc_matrix`: file stale in `masked_fc/` sopravvivono a un re-run

**Pipeline**: `build_fc_matrix` — [src/pipeline/mask_fc.py:64](src/pipeline/mask_fc.py#L64), [src/features/functional.py:260](src/features/functional.py#L260)

**Difetto**: `overwrite=True` non fa `rmtree` della directory di output — file di un run
precedente restano e finiscono silenziosamente inclusi nella matrice finale di
`build_fc_matrix.py`. Riprodotto empiricamente (lesson #18, già risolto altrove per un caso
gemello).

**Stato: Aperto.**

---

### 6. `dim_reduction`: `enrich_metadata_with_lesion_info` blocca produzione su matrici non binarie

**Pipeline**: `dim_reduction` — [src/pipeline/dim_reduction.py:135](src/pipeline/dim_reduction.py#L135)

**Difetto**: la modalità produzione va in errore su qualunque matrice non binaria — rompe la
riproduzione della metodologia Thiebaut de Schotten 2020 (`pca_varimax`), che il README cita
esplicitamente come motivazione dell'atlante combinato. Riprodotto end-to-end.

**Stato: Aperto.**

---

### 7. `dim_reduction`: color mode "volume" senza guard di binarietà

**Pipeline**: `dim_reduction` — [src/analysis/embedding_coloring.py:58](src/analysis/embedding_coloring.py#L58)

**Difetto**: su dati continui (non binari) produce silenziosamente un numero sbagliato, nessuna
eccezione. Riprodotto.

**Stato: Aperto.**

---

### 8. `dim_reduction_clustering`: refit `embedding_for_viz` non valido per `pca_varimax`

**Pipeline**: `dim_reduction_clustering` — [src/analysis/reduction.py:172](src/analysis/reduction.py#L172)

**Difetto**: la rotazione varimax non è "nested" come gli autovettori PCA grezzi — il refit a
dimensionalità diversa non è matematicamente equivalente. Dormiente oggi (nessun run con
`pca_varimax` e `n_components` diverso da `viz_n_components` ancora eseguito), esploderà al
primo caso reale.

**Stato: Aperto.**

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
