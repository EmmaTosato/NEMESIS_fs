# Changelog dell'impianto di progetto

Decisioni su **come è organizzato il repo**: fonti di verità uniche, pipeline ritirate, convenzioni di naming, formati degli artefatti — con le alternative scartate.

**Cosa NON va qui**: la storia del codice (già in `git log`), lo stato attuale (`docs/`, al presente), i cambiamenti ai dati (`data_changelog.md`).

Voci in ordine cronologico inverso.

---

## 07-09-26 — Eliminato il branch `viz-niivue`

Esplorazione di **niivue** come renderer alternativo ai pannelli di anatomia di `embedding_app.py` (oggi su nilearn), 4 commit mai mergeati: prova iniziale, fix dell'hang al caricamento del volume (mancava l'hint di formato), template MNI152 anatomico reale come sfondo, fix del canvas che collassava a 150px.

Chiuso senza adottare niivue e senza una valutazione conclusiva dei due renderer: l'esplorazione era ferma da tempo e teneva aperto un branch che nessuno stava portando avanti. `main` resta su nilearn.

La punta era **`facef6f`**: `git checkout -b viz-niivue facef6f` lo ricrea finché il reflog lo conserva (~90 giorni). Lo SHA è annotato qui proprio perché un branch cancellato non compare in `git log`.

---

## 06-09-26 — I metadati clinici passano a una fonte di verità unica; ritirata la join per-run

**Cosa è cambiato.** I valori clinici (age, sex, education, lesion_side, NIHSS, clinical_date, lesion_volume_voxels) vivono ora in `assets/metadata/participants.csv`, una riga per soggetto, versionata. Prima venivano uniti dentro il `metadata.csv` di *ogni* run da `enrich_lesion_metadata.py`, che leggeva un tsv curato per dataset.

Nuovo: `src/pipeline/enrich_metadata.py` (+ config, job, 16 test), `src/utils/participants.py` (lettura del registro), `src/utils/metadata_sources.py` (parser del registry condiviso, estratto da `populate_metadata.py` perché un entry point non ne importi un altro), `docs/guides/metadata.md`.

Cancellati: `src/pipeline/enrich_lesion_metadata.py` + config + job, `src/features/clinical.py`, `EnrichLesionMetadataConfig`, i relativi test (51 test rimossi, 16 aggiunti; suite 928 passed).

Ricablati sul registro: `src/features/sdc.py` (`has_lesion` come criterio di ammissione), `src/analysis/embedding_coloring.py::color_values` (`side`/`nihss` risolti al plot), `notebooks/post-results_analysis/clustering_evaluation.ipynb`.

**Perché adesso.** I tsv per-dataset erano già stati cancellati dal commit `014dc2a`, ma nessun consumatore era stato spostato: `build_sdc_matrix.py` e `enrich_lesion_metadata.py` erano entrambi **non eseguibili** e nessun test se ne accorgeva, perché ogni test si scriveva da sé le fixture col nome ritirato dopo aver ridiretto `METADATA_ROOT` su `tmp_path`. Suite verde, due pipeline morte.

**Alternativa scartata**: ripuntare `src/features/clinical.py` ai tsv grezzi in `data/clinical_connectome/metadata_tsv/`. Sarebbe stato fattibile (il join corretto passa da `original_id`), ma avrebbe resuscitato proprio il meccanismo che il ridisegno stava smantellando — una join per-dataset ripetuta a ogni run, con N copie degli stessi valori che possono divergere.

**Due difetti trovati solo rilanciando la pipeline una seconda volta** (`.claude/lessons_learned.md` #17 — il ramo di merge esiste solo quando la colonna c'è già, quindi la prima run non lo esegue mai): un `TypeError` nello scrivere un NaN dentro una colonna di dtype `str`, e `lesion_volume_voxels` serializzato come `4616.0` invece di `4616` (la NaN dei soggetti non appaiati promuoveva la colonna a float64). Entrambi corretti, entrambi con test di regressione.

**Conseguenze ancora vere oggi.**

- Il `metadata.csv` di una run contiene solo ciò che appartiene alla run (`subject_id`, `dataset`, `lesion_volume_voxels`). Le run vecchie hanno ancora le colonne cliniche: `color_values` preferisce la colonna della run quando c'è, e altrimenti va al registro — quindi entrambe le generazioni si colorano.
- Colorare per `side`/`nihss` non richiede più nessuno step per-run: **anche le run vecchie** si colorano, e arricchire il registro oggi le migliora retroattivamente.
- Il join coi tsv grezzi passa da `original_id`, non da `subject_id` (per UCL-UK il `participant_id` grezzo è l'id legacy di sito) — `.claude/lessons_learned.md` #30.
- `lesion_side` è popolato solo dove il dato clinico esiste. Il calcolo geometrico previsto dal disegno **non è stato implementato**: serve calibrare la soglia "bilaterale" sui 4 dataset che hanno l'etichetta, e inventarne una avrebbe prodotto un valore plausibile e senza basi. `lesion_side_source` esiste già per distinguere le due provenienze.
