# Changelog dell'impianto di progetto

Decisioni su **come è organizzato il repo**: fonti di verità uniche, pipeline ritirate, convenzioni di naming, formati degli artefatti — con le alternative scartate.

**Cosa NON va qui**: la storia del codice (già in `git log`), lo stato attuale (`docs/`, al presente), i cambiamenti ai dati (`data_changelog.md`).

Voci in ordine cronologico inverso.

## 21-10-26 — Note sui metodi divise per metodo: `dim_reduction_methods/` e `clustering_methods/`

**Cosa è cambiato**: in `knowledge/notes/dim_reduction_clustering/` sono nate due cartelle con una nota per metodo, fonti in coda a ogni nota:
- `dim_reduction_methods/`: `README.md`, `evaluation.md`, `pca.md`, `pca_varimax.md`, `tsne.md`, `umap.md`, `pacmap.md`. `pacmap.md` è spostato qui dal livello superiore (contenuto conservato e completato);
- `clustering_methods/`: `README.md`, `evaluation_metrics.md`, `agglomerative.md`, `hdbscan.md` (hard e soft), `adp.md`, `kmeans.md`, `gmm.md`, `spectral.md`. La nota `evidence_accumulation.md` fu scritta nella stessa sessione e tolta insieme al metodo (voce del 21-10-26 in `methods_changelog.md`): non è mai stata committata.

Link aggiornati in `docs/guides/dim_reduction.md`, `docs/dev/models.md`, `management/cheatsheets/pacmap.md` e nelle note di livello superiore. Le note esistenti (`employed_dim_reduction_methods.md`, `clustering_literature_survey.md`, ecc.) restano e rimandano alle cartelle.

**Perché**: l'utente vuole ogni metodo documentato con lo stesso schema (cosa fa, perché, parametri e range, tuning, valutazione, quando usarlo, pro e contro, esempio), solo da letteratura e documentazione ufficiale. Il nome `dim_reduction_methods/` (non `methods/`) evita la confusione con `knowledge/papers/methods/` e fa il paio con `clustering_methods/`.

**Conseguenza ancora vera oggi**: la voce del 21-10-26 più sotto cita `knowledge/notes/dim_reduction_clustering/pacmap.md`; il percorso attuale è `dim_reduction_methods/pacmap.md`.

## 21-10-26 — Cancellato `assets/metadata/lesion_quality_metrics.csv`, rimasto su disco dopo la sua sostituzione

**Cosa è cambiato**: il file (5853 righe di dati, colonne `subject_id`, `dataset`, `out_of_brain_fraction`; ultimo commit 29-09-26 `028205e`) è stato cancellato, e il suo paragrafo è stato tolto da `docs/guides/metadata.md`. La cancellazione è registrata nel commit `b4c643f` (21-10-26).

**Perché**: la voce del 29-09-26 più sotto dichiarava che il file «non esiste più», ma era rimasto su disco e tracciato in git. Il grep su `src/`, `config/`, `tests/`, `scripts/`, `docs/` e `notebooks/` non trovava nessuno che lo scrivesse o lo leggesse; la stessa misura è la colonna `out_of_brain_fraction_<griglia>` di `lesion_metadata.csv`. Cancellazione chiesta esplicitamente dall'utente.

**Conseguenza ancora vera oggi**: la frazione di lesione fuori dal brain si legge solo da `lesion_metadata.csv`; il recupero del vecchio file è possibile da `git` (`028205e`).

## 21-10-26 — `management/notes/` dissolta: le note si separano per stato (verificate / derivate), non per argomento

**Cosa è cambiato** (`git mv`, nessun contenuto riscritto):
- `management/notes/slides_metodi.md` (4 metodi: PCA, varimax, agglomerative, HDBSCAN) diviso in `management/cheatsheets/{pca,pca-varimax,agglomerative,hdbscan}.md` più un `README.md` con la tabella di confronto;
- `management/notes/pacmap.md` → `knowledge/notes/dim_reduction_clustering/pacmap.md` (è una nota con fonte e versione installata, cioè verificata);
- `management/notes/proposal.md` → `management/nemesis_project/proposal.md` (documento di progetto, come gli altri lì);
- aggiunte le schede `umap`, `pacmap`, `kmeans`, `evidence-accumulation`, `adp` (commit `28ec2aa`; nove in tutto, otto dopo che `evidence-accumulation.md` è stata tolta con il metodo, vedi `methods_changelog.md` 21-10-26) e verificate le quattro esistenti contro `knowledge/notes/` e `docs/`: corretti in `hdbscan.md` l'effetto di `min_samples` sul numero di cluster (la fonte non lo dice, descrive solo rumore ed estensione) e la stabilità, che esiste solo in `hdbscan_soft`; in `agglomerative.md` "ward con euclidea sugli UMAP" (nel progetto linkage e metrica si sweeppano insieme); in `pca-varimax.md` le 500 iterazioni (sono il parametro `rotation_max_iter`). "Deterministico" per PCA e varimax non aveva fonte: aggiunto a `employed_dim_reduction_methods.md`;
- aggiornati i riferimenti vivi: `README.md` (albero), `.claude/CLAUDE.md`, `challenge_of_clustering_after_dim_reduction.md`.

**Perché**: `notes` compariva sia in `knowledge/notes/` (fonti di verità, costruite da letteratura e documentazione) sia in `management/notes/` (riassunti personali per sé e per le presentazioni): il nome nascondeva la differenza di stato. Una scheda è una vista derivata e non contiene fatti assenti da `knowledge/notes/`.

**Scartato**: rinominare `knowledge/notes/` (27 file lo citano; il lato personale ne costava 10) · `management/summaries/` (esiste già `summaries/` alla radice, output per run) · `personal/`, `appunti/`, `presentations/` (generici o troppo stretti) · un file unico per tutte le schede (500+ righe a regime).

**Ancora vero oggi**: `management/notes/` non esiste più; `clustering_metrics_report.md` (analisi del 20-10 sulle metriche di valutazione del clustering, entrata con il commit `34fdd81`) è stato messo in `management/cheatsheets/` su indicazione dell'utente, anche se non è una scheda per metodo. I riferimenti vivi a `management/notes/TODO.md` (inesistente) sono stati sostituiti col commit `2ed3dcb` (`.claude/CLAUDE.md`, `src/features/lesion.py`) o tolti (`src/analysis/prediction.py`: la voce "Fase 7" non ha più un posto dove essere tracciata, la limitazione resta nel docstring; `docs/dev/lesion_matrix.md`: il rimando è sparito con la riscrittura al presente; `proposal.md`: tolto il rimando a `workflow.md`, che non esiste, nel paragrafo della tabella per fasi. Resta quello della nota `(***)` sotto il diagramma, non toccato). Quelli nei changelog e in `docs/debugging/` sono storici e restano com'erano.

## 19-10-26 — Eliminata `results/reports/cluster_tuning_notebooks/`: il report di una run sta nella cartella della run

**Cosa è cambiato** (a mano su `results/`, ignorato da git): eliminata la cartella con i 13 `cluster_*.md` per embedding, `README.md`, `MOVES_18-10-26.json`, `MOVES_19-10-26.json`, `_shared/` (generatori `generate_reports/*.py`, `cluster_tools.py`, 10 bozze di testo di `hdbscan_soft`) e le sottocartelle `images/`/`tables/`. Prima:
- le 4 immagini di riferimento sono state spostate nelle cartelle `dim_reduction` di produzione: `embedding_reference.png` in `lesion/.../umap/08-10_s1.4-vol_m_euclidean_nc2/`, `umap_covariates.png` in `sdc/.../umap/16-10_s2.4-vol_m_euclidean_nc2/`, `pca_covariates.png` in `sdc/.../pca/17-10_s2.4-vol_nc30/` e `sdc/.../pca/16-10_s2.4-vol_nc42/`;
- i 10 residui di `tables/` (`candidates.csv` del vecchio metodo con le soglie, `what_explains_partition.csv`, `subjects_metadata_joined.csv`, `metadata_merged_nc2.csv`, `association_agglomerative_candidates.csv`, `pca2d_view.npy`) sono in `tmp/cluster_tuning_residual_tables_19-10-26/`;
- le 2 immagini `view2d_*.png` dello streamline sono state eliminate (restano solo nel backup);
- copia integrale della cartella (51 file, verificata con `diff -r`) in `tmp/cluster_tuning_notebooks_backup_19-10-26/`: è l'unico posto dove restano i generatori e `plot_labels_on_2d`.

Eliminati anche `results/lesion/clustering/tuning/SUMMARY.md` e `results/sdc/clustering/tuning/SUMMARY.md` (contenevano il filtro `usabile` del vecchio metodo); copie in `tmp/summary_md_19-10-26/`. `all_candidates.csv` (accanto ai due `SUMMARY.md`) non è stato toccato.

**Perché**: un report per run, scritto da `analyze_clustering_tuning` come `report.md` nella cartella della run (voce `methods_changelog.md` del 19-10-26), sostituisce i report per embedding con i quattro metodi; il codice che li generava stava sotto `results/`, non versionato.

**Conseguenza ancora vera oggi**: le voci storiche di questo e del `methods_changelog.md` che citano `results/reports/cluster_tuning_notebooks/` descrivono un percorso che non esiste più. I link nei `docs/experiments/{README,s1.4-vol,s2.4-vol,s2.4-stream}.md` puntano ai `report.md` delle run; quelli di agglomerative (lesione `08-10 euclidean nc10`, SDC `16-10 nc2/nc3/nc10`) e quelli dello streamline raw (`agglomerative`, `hdbscan`, `hdbscan_soft`, `adp`) esistono solo dopo aver rigenerato i report. I due `SUMMARY.md` vanno riscritti senza `usabile`; il confronto tra le matrici 07-10 e 16-10 della voce del 17-10-26 non ha più un file di sintesi.

---

## 19-10-26 — Confronti tra embedding in una cartella propria, report in file piatti, niente `k_evaluation_map`

**Cosa è cambiato** (a mano su `results/`, ignorato da git): i confronti tra embedding (curve e ARI tra nc2, nc3 e nc10, heatmap HDBSCAN per `n_components`) stanno in `results/lesion/clustering/tuning/comparison/umap/<data>_<sessione>_m_<metrica>_comparison_nc/`: una cartella per metrica (`08-10_s1.4-vol_m_dice_comparison_nc`, `08-10_s1.4-vol_m_euclidean_comparison_nc`), con lo stesso nome delle run in cui `nc<N>` diventa `comparison_nc`. Le tre immagini `nb_c52/54/58_0.png` hanno nomi descrittivi (`agglomerative_curves_by_embedding.png`, `ward_ari_by_k.png`, `hdbscan_grids_by_embedding.png`). I `report.md` sono saliti di una cartella (`cluster_<...>.md`) con i percorsi relativi accorciati; `scripts/` dei report e quattro file di `_shared/` (`hdbscan_all.py`, `k_evaluation.py`, `k_evaluation_all.csv`, `make_detail_reports.py`) sono stati cancellati. Origine e destinazione sono in `results/reports/cluster_tuning_notebooks/MOVES_19-10-26.json`.

**Scartato**: `k_evaluation_map.png` (mappa dei k da 3 a 30): cancellato in 4 cartelle di run e non più generato, perché il solo script che lo scriveva (`_shared/k_evaluation.py`) è stato cancellato. Le tabelle `k_evaluation_*.csv` restano.

**Conseguenza ancora vera**: `_shared/generate_reports/` (generatori attuali e commenti scritti a mano in `hdbscan_soft_text/`) e `_shared/cluster_tools.py` (importato da `images_1610.py`) restano, ma scrivono ancora `<report>/report.md`: vanno allineati ai file piatti prima di rigenerare un report.

## 18-10-26 — I file dei report di clustering vanno nelle cartelle delle run, i riepiloghi per modalità accanto ai tuning

**Cosa è cambiato** (a mano, senza rilanciare niente; `results/` è ignorato da git): da `results/reports/cluster_tuning_notebooks/cluster_*/{images,tables,adp}/` sono stati spostati 307 file nelle cartelle delle run in `results/{lesion,sdc}/clustering/tuning/<metodo>/...` (agglomerative, hdbscan, adp), assegnati per nome del file; i file ADP di più report della stessa matrice condividono la cartella ADP e hanno il prefisso del report (`lesion_dice_nc2_07-10__...`). 12 file erano copie byte-identiche di file già presenti nella run (sha256) e sono stati cancellati. Restano nei report 24 file che non appartengono a una run sola (confronti tra embedding, immagini di riferimento, tabelle ausiliarie del metodo vecchio). `report.md` cita i file con percorso relativo (nessun riferimento rotto). L'elenco completo, con origine e destinazione, è in `results/reports/cluster_tuning_notebooks/MOVES_18-10-26.json`.

`SUMMARY.md` è diviso in `results/lesion/clustering/tuning/SUMMARY.md` e `results/sdc/clustering/tuning/SUMMARY.md` (lo streamline è in `sdc`); `all_candidates.csv` (208 righe) è diviso per modalità (128 lesione, 80 SDC). Gli originali sono in `results/legacy/cluster_tuning_notebooks_pre-split_18-10-26/`.

**Perché**: una cartella report doveva contenere solo ciò che non esiste altrove; le immagini e le tabelle di una run appartengono alla run.

**Conseguenza ancora vera**: due intervalli di `hdbscan_soft` (26-209 cluster, rumore 15.6-38.9%; leaf 40.2-54.3%) erano calcolati su lesione e SDC insieme e non si possono separare senza ricalcolo: compaiono in entrambi i riepiloghi con la nota. Non spostati: `scripts/` dei report e `_shared/` (codice del metodo precedente, non versionato sotto `results/`). Una nuova run di tuning con `overwrite: true` cancella la cartella della run e i file spostati lì dentro.

## 18-10-26 — Lo scree plot della PCA esce dalla pipeline e si disegna nel notebook

**Cosa è cambiato**: `dim_reduction.py` non scrive più `scree_plot.png` e `scree_plot_zoom.png` nel tuning della PCA, e `plotting.plot_scree`, `_scree_components` e `SCREE_ZOOM_COMPONENTS` sono stati cancellati insieme ai loro test. Resta `eigenvalues.npz` (lo spettro intero, 47 KB), da cui `notebooks/post-results_analysis/pca_evaluation.ipynb` disegna il grafico con il numero di componenti che si vuole. I due png di `results/sdc/dim_reduction/tuning/pca/16-10_s2.4-vol/` sono stati cancellati a mano.

**Perché**: il numero di componenti mostrate (il massimo della griglia, con uno zoom fisso a 50) era una scelta della pipeline per un grafico che si guarda e si rifà a occhio; nel notebook si cambia in un'istruzione.

**Conseguenza ancora vera**: i tuning PCA già su disco con `scree_plot*.png` li tengono; quelli nuovi no.

## 18-10-26 — Le analisi dopo un tuning di clustering diventano una pipeline che scrive nella cartella della run

**Cosa è cambiato**: `src/pipeline/analyze_clustering_tuning.py` (logica in `src/analysis/clustering_tuning_analysis.py`, config `config/pipelines/analyze_clustering_tuning.json`, `jobs/run_analyze_clustering_tuning.sh`) calcola su un tuning di clustering già salvato ciò che il notebook `clustering_tuning_explorer` mostrava soltanto: cophenetic e salto del dendrogramma per agglomerative, quota del cluster più grande e flag `usable` per HDBSCAN/`hdbscan_soft`, più le curve per k e le curve filtrate sul rumore. I file stanno nella cartella della run (`cophenetic_correlation.csv`, `dendrogram_jump.csv`, `k_curves_metric=<metric>.png`, `candidates.csv`, `noise_filtered_curves*.png`). ADP è escluso.

**Perché**: i generatori dei report stavano in `results/reports/cluster_tuning_notebooks/_shared/`, cioè sotto `results/`, che git ignora: il codice non era versionato. I risultati finivano in un report separato, con tabelle ordinate per silhouette che duplicano `tuning_results.csv`. Decisione presa il 18-10-26: i risultati per run vanno nella cartella della run, il codice nel repo, e `results/reports/cluster_tuning_notebooks/` tiene solo ciò che non esiste altrove (testo scritto a mano, confronti tra run).

**Scartato**: mettere il codice in `scripts/`, come proposto in chat: `scripts/` è per utilità accessorie, mai per passi di analisi (`.claude/CLAUDE.md`); questo è un passo, quindi sta in `src/pipeline/` con la logica in `src/analysis/`, come `evaluate_tuning_embeddings`.

**Conseguenza ancora vera**: rilanciare un tuning con `overwrite: true` ricrea la cartella da zero (`_write_tuning_output`, lessons_learned #18) e cancella questi file: vanno rigenerati con la pipeline. Non ancora fatto: i riepiloghi per modalità (`SUMMARY.md`, `all_candidates.csv` sotto `results/{lesion,sdc}/clustering/tuning/`) e lo svuotamento dei report dalle tabelle duplicate.

## 17-10-26 — La rotazione compare nel tag della PCA solo quando c'è

**Cosa è cambiato**: nella voce `pca` di `config/registry/params_reduction.json` e `params_reduction_sdc.json`, `tag_param` è `["n_components", "rotation"]`, `tag_prefix` `["nc", ""]`, e un campo nuovo `"tag_omit": {"rotation": "none"}` toglie quella parte dal tag quando la rotazione è `none`. Le cartelle sono `nc42` (non ruotata) e `nc42_varimax` (ruotata), per la produzione e per il tag dell'embedding in `clustering.py` (`params.py::_tag_omit`, `_join_tag`).

`rotation` entra anche tra le colonne di `runs.csv` di produzione della PCA, e l'intestazione deve restare identica tra le righe: `results/sdc/dim_reduction/production/pca/runs.csv` (una riga, la run nc42 del 16-10) è stato migrato a mano aggiungendo `rotation=none`.

**Perché**: due run con lo stesso numero di componenti ma rotazione diversa avevano lo stesso nome (lo stesso giorno la seconda si fermava con `FileExistsError`, in giorni diversi le distingueva solo la data). Scelta dell'utente: la rotazione nel nome solo quando c'è, così i nomi esistenti non cambiano.

**Conseguenza ancora vera**: il tag della PCA non contiene `standardize` né `solver`: una PCA standardizzata e una no, con lo stesso numero di componenti, hanno lo stesso nome. Si distinguono solo dal `config.md` dell'embedding.

## 17-10-26 — Risultati di `s2.4-vol` sulla matrice pre-correzione spostati in `results/legacy/`

**Cosa è cambiato**: 44 cartelle sotto `results/sdc/` (circa 25 GB) sono state spostate in `results/legacy/sdc_s2.4-vol_07-10/`, con la stessa struttura di `results/sdc/` (`clustering/{tuning,production}/...`, `dim_reduction/{tuning,production}/...`). Sono tutte le run di `s2.4-vol` costruite sulla matrice `data/derived/sdc_matrix/07-10_s2.4-vol` (voxel fuori dal cervello non azzerati): tuning UMAP 07-10, embedding di produzione 08-10 (nc2, nc3, nc10), tuning di agglomerative/HDBSCAN 09-10, di `hdbscan_soft` 15-10 e di ADP 08-10, produzioni 12-10 (agglomerative 14, HDBSCAN 7, ADP 4) e `hdbscan_soft` 15-10 (4). Restano in `results/sdc/` le 50 cartelle sulla matrice del 16-10 (compresa la PCA 16-10/17-10) e tutto `s2.4-stream`. `data/` non è cambiato.

**Come si è scelto cosa spostare**: dall'`input_path` di ogni `config.md` (la matrice 07-10 oppure un embedding `08-10_s2.4-vol_m_euclidean_nc*`), non dalla data nel nome. Questo ha preso anche `hdbscan_soft/umap/16-10_s2.4-vol_m_euclidean_nc10_mcs100_ms20_sel_eom`, che per il nome sembrava del 16-10 ma aveva input `08-10_s2.4-vol_m_euclidean_nc10`: una run sulla matrice vecchia fatta dopo mezzanotte del 16-10. Il suo nome in `results/sdc/` è ora libero per la run sul 16-10, che non è stata prodotta.

**Perché**: dopo `correct_out_of_brain` (`methods_changelog.md`, 16-10-26) la matrice del 07-10 non descrive la stessa quantità di `sdc_metadata.csv`; le sue run restano come storico ma non devono stare accanto a quelle valide. Spostate, non cancellate: sono il termine di confronto di `SUMMARY.md` (report di tuning) e di `docs/experiments/s2.4-vol.md`.

**Scartato**: cancellarle (non richiesto); riscrivere i `runs.csv`/`runs_tuning.csv` per togliere o aggiornare le righe spostate (sono registri, non toccati).

**Conseguenza ancora vera oggi**: i `runs.csv`/`runs_tuning.csv` di `results/sdc/` hanno ancora 44 righe (una per cartella spostata) con la colonna `output` che punta a un percorso non più esistente (`lessons_learned.md` #24): chi legge quei registri deve verificare `Path(output).is_dir()`. I link di `docs/experiments/` alle run del 07-10 puntano a `results/legacy/`. `results/legacy/` non è tracciato da git (`legacy/` in `.gitignore`).

## 17-10-26 — Report di tuning: suffisso con la data della matrice; report SDC del 07-10 eliminati

**Cosa è cambiato**: in `results/reports/cluster_tuning_notebooks/` ogni cartella porta come suffisso la data della matrice di input: `cluster_lesion_{dice,euclidean}_nc{2,3,10}_07-10` (6) e `cluster_streamline_raw_07-10` (rinominate), `cluster_sdc_euclidean_nc{2,3,10}_16-10` (3 nuove, sulla matrice `s2.4-vol` del 16-10). Le tre cartelle `cluster_sdc_euclidean_nc{2,3,10}` sulla matrice del 07-10 (circa 9.6 MB) sono state **eliminate**, su richiesta dell'utente; `results/` è gitignorato, quindi non c'è modo di recuperarle. Gli script di generazione (`_shared/generate_reports/`) conoscono solo i report esistenti: `common.py` (`RUNS`), `content.py`, `images_text.py`, `hdbscan_soft.py`, `hdbscan_soft_text/` e il nuovo `images_1610.py` (viste 2D e copie dei png di tuning).

**Perché**: esistevano due matrici con lo stesso nome di sessione (`s2.4-vol`), distinte solo dalla data; senza suffisso il report di una era indistinguibile da quello dell'altra. Il suffisso è la data della matrice, non della run.

**Scartato**: lasciare i report SDC del 07-10 accanto ai nuovi (richiesta di eliminarli); rinominare solo i nuovi.

**Conseguenza ancora vera oggi**: i file del metodo precedente (`scripts/` e `tables/` di ogni cartella, `all_candidates.csv`, `_shared/k_evaluation*.py`, `hdbscan_all.py`, `make_detail_reports.py`) contengono ancora i vecchi nomi di cartella: il README della cartella li dichiara non più letti, non vanno rieseguiti. I report del 16-10 non hanno i grafici delle celle di `clustering_tuning_explorer` (notebook human-in-the-loop, non eseguito).

## 16-10-26 — Sezione "Confronto" tolta dall'Embedding Explorer (acerba, non pronta per la produzione)

**Cosa è cambiato**: il blocco `comparison-section` (layout), le 7 callback `comparison-*`/`selected-comparison-mode` e la voce "Confronto" dell'indice sono stati rimossi da `build_app` in `src/analysis/embedding_app.py`. Restano, non montati: `src/analysis/cluster_comparison.py`, `src/analysis/cluster_pair.py`, i builder del Confronto in `embedding_app.py` (`comparison_content_for`, `cluster_pair_content_for`, `cluster_pair_anatomy_for`, `COMPARISON_MODE_*`...) e i loro test unitari. Rimossi i 3 test end-to-end sulle callback non più montate (`tests/unit/test_embedding_app_comparison.py`).

**Perché**: decisione dell'utente, la parte di confronto è ancora acerba. È un ritiro **temporaneo**, non definitivo: per reintrodurla bastano layout + callback, i builder non vanno riscritti.

**Conseguenza ancora vera oggi**: i builder del Confronto sono codice non raggiunto dall'app (solo i test li usano) finché la sezione non torna; non cancellarli come codice morto. Il valore `homogeneity`/`completeness` scambiato del notebook `clustering_comparison` (`lessons_learned.md` #41) resta un problema a sé.

## 16-10-26 — `knowledge/` divisa per funzione: `notes/` (nostre sintesi) e `papers/` (fonti estratte)

**Cosa è cambiato**: le 4 cartelle per argomento (`nemesis/`, `nemesis_related/`, `dim_reduction_clustering/`, `neuroimaging/`) sono diventate due. `knowledge/notes/` ha le note scritte da noi (`dim_reduction_clustering/`, `neuroimaging/`, `stroke_literature/`); `knowledge/papers/` ha le fonti estratte da PDF (`stroke_core/` 21 cartelle, `stroke_related/` 4, `methods/` 5 paper più `Slides_Bicego/` e `websites/`). `Paper_Summaries.md`, `Papers_Schema.md` e il `Paper_Summaries.md` di `nemesis_related/` sono in `notes/stroke_literature/` come `summaries_core.md`, `scope_by_category.md`, `summaries_related.md`. `paper_lists.md` è `papers/index.md` e ora elenca anche `stroke_related/` e `methods/`. Aggiunti `knowledge/README.md`, 8 `.DS_Store` rimossi. Spostamenti con `git mv` (600 rinomine al 100%). Aggiornati i riferimenti in `.claude/CLAUDE.md`, `README.md`, `docs/`, `src/` (commenti), `config/pipelines/compute_lesion_metadata.json` e i link relativi `../../` delle note (ora `../../../`).

**Perché**: le note nostre (da mantenere) stavano accanto a cartelle di paper estratti (archivio), e l'indice dei paper era dentro `nemesis/` mentre `CLAUDE.md` lo dava in `knowledge/paper_lists.md`. Due riferimenti in `src/` puntavano a `knowledge/sota/`, inesistente.

**Scartato**: uniformare il layout interno di ogni paper (alcuni hanno `<Autore> et al - <Anno>.md` nella radice, altri `markdown/_full.md`) e rinominare le cartelle con underscore: toccherebbe i `manifest.json`/`figures.json` per nessun guadagno di lettura. I `manifest.json` conservano i vecchi percorsi di estrazione (`knowledge/sota/...`, `knowledge/related/...`), lasciati come metadati.

**Conseguenza ancora vera oggi**: i vecchi percorsi (`knowledge/nemesis/`, `knowledge/neuroimaging/`, ...) compaiono ancora in `docs/debugging/`, `.claude/history/` e `stato_progetto_archive.md`, lasciati com'erano perché sono registri datati. Un percorso lì che non esiste è questa riorganizzazione, non un file perso. L'indice di `stroke_core/` e la cartella non coincidono, dall'origine: la voce 14 (Idesis 2024, *Whole-brain model...*) non ha cartella, e la cartella `Cinetto et al - 2026/` (solo `Manuscript.docx`) non ha voce.

## 16-10-26 — Un solo ordine delle righe per le matrici lesione e SDC: alfabetico per dataset, poi `subject_id`

**Cosa è cambiato**: `build_lesion_matrix` ordina le righe per nome del dataset e poi `subject_id` (`src/features/lesion.py::_stack_voxel_matrix`, `sorted(lesion_files.items())`), come già facevano `build_sdc_matrix` (tutte e tre le rappresentazioni) e il builder parcellato. Prima seguiva l'ordine di `datasets` nel config, e l'unica ragione per cui `s1.4-vol` e `s2.4-vol` del 07-10 avevano lo stesso ordine era un riordino a mano dell'SDC (`data_changelog.md`). Test di regressione: `test_build_lesion_matrix_rows_are_ordered_by_dataset_name_not_by_config_order`, che fallisce col codice vecchio.

**Perché**: con due criteri diversi, una nuova build SDC usciva in un ordine diverso dalla lesione e il confronto per posizione si rompeva senza errori; l'ordine del config è anche una scelta di chi scrive il json, non una proprietà dei dati. **Scartato**: allineare l'SDC all'ordine del config (dipenderebbe dall'ordine in cui si elencano i dataset) e riordinare a mano a ogni build.

**Conseguenza ancora vera oggi**: ogni confronto tra run continua ad allineare per `subject_id` (`align_runs`); l'uguaglianza di posizione vale solo per matrici costruite dopo questa data o riordinate (le due del 07-10 lo sono). Il FC (`build_fc_matrix`) ordina per `subject_id` senza dataset e non è toccato.

## 16-10-26 — Il tuning della PCA scrive lo spettro (`eigenvalues.npz`) e lo scree plot

**Cosa è cambiato**: un tuning `pca` scrive, accanto a `tuning_results.csv`, `eigenvalues.npz` (un array per ogni decomposizione fittata dalla griglia, chiave `solver=blocks,standardize=False,dual=True`), `scree_plot.png` e, se la griglia tiene più di 50 componenti, `scree_plot_zoom.png` sulle prime 50 (`SCREE_ZOOM_COMPONENTS`, costante in `dim_reduction.py`). Lo scrive sempre, anche con `save_tuning_embeddings: false`. Codice: `pca_method.decomposition_spectra`, `plotting.plot_scree`, `run_tuning_sweep(..., model_cache=None)`.

**Perché**: `tuning_results.csv` campiona la varianza cumulata solo ai valori della griglia; per scegliere `n_components`/`variance_share` serve l'intero spettro, che prima usciva solo da una produzione (`eigenvalues.npy`). Pesa 47 KB, quindi non è opt-in. Scelto `.npz` con chiavi e non `.npy`: una griglia su `standardize`/`dual`/`solver` fitta più decomposizioni, ognuna con il suo spettro, e il confronto covarianza contro correlazione è proprio ciò che uno scree plot deve mostrare.

**Scartato**: salvare i pesi ruotati (`rotated_loadings`) nel tuning. Dipendono da `rotation` e da `n_components` (la rotazione delle prime 42 componenti non è un sottoinsieme di quella delle prime 100), quindi ogni combinazione ne avrebbe di propri: circa 2 GB con la griglia di 20 valori sulla matrice del 07-10 di `s2.4-vol` (291345 colonne; circa 1,5 GB sulla corretta del 16-10, 227235). Servono solo alla varianza per componente dopo il varimax; non servono né agli embedding né alle mappe t.

**Conseguenza ancora vera**: lo spettro nel tuning è sempre quello della decomposizione non ruotata; la varianza per componente dopo il varimax non si ricava da un tuning.

## 16-10-26 — Prefisso `nc` per `n_components` nelle cartelle della PCA

**Cosa è cambiato**: `tag_prefix` della voce `pca` è `["nc"]` (era `["c"]`) in `config/registry/params_reduction.json` e `params_reduction_sdc.json`. Le cartelle di produzione diventano `<data>_<sessione>_nc<k>` (es. `nc42`) e il tag passa a `clustering.py` con lo stesso prefisso.

**Perché**: stesso prefisso di UMAP (`nc`) per lo stesso parametro, `n_components`. Scelta dell'utente.

**Conseguenza ancora vera**: nessuna run PCA esisteva in `results/` al momento del cambio, quindi nessuna cartella da rinominare. L'esperimento in `tmp/s2.4_pca42_clustering/` ha usato il prefisso `c` (cartella `..._c42`): resta com'è, è fuori da `results/`.

## 16-10-26 — Eliminato `build_dim_reduction_strategies_csv.py` e il suo indice

**Cosa è cambiato**: cancellati `scripts/build_dim_reduction_strategies_csv.py`, `jobs/run_build_dim_reduction_strategies_csv.sh` e `tests/unit/test_build_dim_reduction_strategies_csv.py`. Tolte le descrizioni di `results/dim_reduction_strategies.csv` da `docs/dev/config.md` e da `docs/guides/dim_reduction.md`.

**Perché**: lo script generava `results/dim_reduction_strategies.csv`, un indice di esistenza con una riga per combinazione `(session, reduction_method, metric, n_components)` già prodotta. Era morto da tempo: fermo al commit del 02-09-26, con il suo output cancellato dall'utente l'08-10-26 e mai più rigenerato. La riorganizzazione di `docs/experiments/` della stessa giornata lo avrebbe comunque rotto, perché parsava `data_sessions.md` con una regex sul formato `### Session <id>` + campi fissi.

**Conseguenza ancora vera**: per sapere quali combinazioni di dim reduction esistono si aprono i `runs.csv`/`runs_tuning.csv` di ogni metodo sotto `results/*/dim_reduction/`, oppure si legge il file della sessione in `docs/experiments/`. Le voci #24 e #25 di `lessons_learned.md` citano questo script nei loro "Seen in": restano, descrivono pattern di errore ancora validi.

## 16-10-26 — `docs/experiments/`: un file per sessione al posto di 11 file divisi per pipeline

**Cosa è cambiato**: le 1582 righe su 11 file (`data_sessions.md`, `data_employing.md`, `processing/matrices.md`, più `{clustering,dim_reduction}/s{1,2}_{tuning,production}.md` con 31 entry datate dentro) sono diventati 11 file: un file per sessione (`s1.1-vol.md`, `s1.2-vol.md`, `s1.3-vol.md`, `s1.4-vol.md`, `s2.1-schaefer-200-tian-s2.md`, `s2.2-vol.md`, `s2.4-vol.md`, `s2.4-stream.md`), più `README.md` (indice, tabella delle sessioni, vocabolario dei tag di formato), `pipelines.md` (i due mermaid di `data_employing.md`, rinominato) e `lineage.md` (nuovo: da quale sessione deriva quale e quali coorti sono confrontabili). Ogni file di sessione va dalla coorte alle decisioni passando per dim reduction e clustering, tuning e produzione.

Aggiunto in questo giro il lavoro su `hdbscan_soft` del 15-10/16-10 (10 tuning, 17 run di produzione), che non era in nessun diario: stava solo in `data_employing.md` e in `methods_changelog.md`.

**Perché**: l'unità di lavoro è la sessione, non la pipeline. Prima, per sapere cosa era successo a `s1.4-vol`, servivano 5 file di `docs/experiments/` più i 4 report in `results/`; ogni diario conteneva entry di 2-3 sessioni diverse e ogni sessione era spezzata su 4-5 diari. Scelta dell'utente tra: un file per sessione (scelto), unire solo dim reduction e clustering tenendo la divisione tuning/produzione (4 file), lasciare la struttura e togliere solo le duplicazioni.

**Le tabelle complete restano fuori da `docs/`**: i 7 report per run del tuning clustering del 12-10 (tabelle ordinate per silhouette, lettura per gruppi di k, immagini) restano in `results/reports/cluster_tuning_notebooks/`, linkati dai file di sessione, che ne riportano solo la lettura. Rispetta la regola "niente dump di dati nei `.md`". Alternative scartate: spostare i report interi in git (circa 1000 righe di tabelle già presenti nei `tuning_results.csv`), lasciare tutto in `results/` (fuori da git, quindi perso a ogni pulizia).

**Conseguenze ancora vere**:

- `docs/experiments/data_sessions.md` non esiste più. Il significato di un `session_name` sta nella tabella di `docs/experiments/README.md` e nel file della sessione. 26 riferimenti aggiornati in `README.md`, `docs/dev/{config,models,pipeline_flow,sdc_matrix}.md`, `docs/guides/{dim_reduction,pipeline_order,sdc_matrix_building}.md`, `.claude/{CLAUDE,open_problems,stato_progetto}.md` e 5 docstring in `src/`. I riferimenti dentro `.claude/history/` sono narrativa storica e restano com'erano.
- **`scripts/build_dim_reduction_strategies_csv.py` non funziona più**: parsava `data_sessions.md` con una regex sul formato `### Session <id>` + `- Starting date:`/`- Datasets:`/`- Modality:`, e solleva `FileNotFoundError` se il file non c'è. Era già di fatto morto — fermo dal 02-09-26 e il suo output `results/dim_reduction_strategies.csv` è stato cancellato dall'utente l'08-10-26 — ed è stato eliminato lo stesso giorno (voce sopra).
- Un riferimento in `docs/dev/config.md` puntava alla "naming discussion" di `clustering/s1_production.md`, che quel file non conteneva più già da prima: ora punta a `docs/guides/clustering.md`, "Nome della cartella finale".

## 15-10-26 — `cluster_interpretation.ipynb` eliminato: la descrizione dei cluster passa in `clustering_evaluation` §4

**Cosa è cambiato**: eliminato `notebooks/post-results_analysis/cluster_interpretation.ipynb`. Le sue tabelle per cluster (soggetti con il dato, media ± deviazione standard, mediana [Q1–Q3], percentuali per categoria, sulle variabili di `participants.csv`; carico di disconnessione per le run sdc) sono ora la sezione 4 di `clustering_evaluation.ipynb` (`describe_clusters`, `DESCRIBED_RUN`), che le mostra per una run alla volta con gli stessi numeri (verificato su `12-10_s1.4-vol_m_dice_nc10_k7_link_ward`, `03-09_s1.2-vol_m_euclidean_nc2_mcs100_ms20` e `30-09_s2.3-stream_k5_link_ward`). Le funzioni stanno nel notebook, come prima, non in `src/`.

**Perché**: dopo la rimozione dei test (`methods_changelog.md`, 15-10-26) e della sezione «cluster contro resto» il notebook conteneva solo una descrizione per cluster, già vicina a quello che `clustering_evaluation` fa per le metriche. Il criterio empirica/interpretativa del 08-10-26 (`docs/guides/exploration.md`) non ha più un notebook interpretativo: l'interpretazione (mappe, soggetti rappresentativi, composizione, confronto tra cluster) vive nell'app Dash, e la sezione 4 è l'unica descrizione con variabili esterne nei notebook, senza test.

**Alternative scartate**: tenere il notebook per le sole tabelle descrittive (un notebook per una sezione); una sezione 4 che descrive tutte le run caricate insieme (una decina di tabelle per run, illeggibile con molte run).

**Conseguenza ancora vera**: il notebook è recuperabile da `git` (ultimo commit con il file: `439a709`). Le righe di `docs/guides/evaluation.md` sulle distanze nello spazio delle mappe e su A∩B, A\B, B\A non hanno più un notebook: sono previste e non implementate. Le voci precedenti di questo file e di `methods_changelog.md` che nominano `cluster_interpretation` descrivono il notebook com'era.

## 15-10-26 — Logica dei CSV parcellati spostata in `src/features/parcellated_csv.py`; `build_lesion_matrix` guadagna `representation`

**Cosa**: `build_sdc_matrix` (ora `build_parcellated_matrix`) e gli helper di ammissione dei soggetti (`registered_subjects`, `subjects_with_lesion_mask`, `discover_by_dataset`, `load_reference_regions`, `KNOWN_OBJECTS`, `KNOWN_VALUE_COLUMNS`, `BCBTOOLKIT_DIR`) escono da `src/features/sdc.py` e vanno in un modulo nuovo. `sdc.py` e la pipeline `build_lesion_matrix` lo importano entrambi. Il terzo ritorno di `build_parcellated_matrix` si chiama `csv_not_yet_computed` (era `sdc_not_yet_computed`).

**Perché un modulo e non due copie**: `sdc.py` importa `src.features.lesion`, quindi `lesion.py` non poteva importare da `sdc.py` (circolare). Alternative scartate: delegare nel layer pipeline a `build_sdc_matrix(object_="lesion")` (la lesione parcellata userebbe lo scope di esclusione SDC e `lesion.py` non possederebbe la rappresentazione); copiare la logica.

**Config**: `build_lesion_matrix.json` ha ora `representation` obbligatorio (`voxelwise` o `parcellated`, nessun default silenzioso); un campo dell'altra rappresentazione è rifiutato invece che ignorato. L'Embedding Explorer rifiuta un config lesione non voxelwise.

**Stato**: la rappresentazione `parcellated` è implementata e testata (1421 passed al momento della modifica) ma non è mai stata eseguita su dati reali: l'utente ha messo in pausa la lesione parcellata il 15-10-26 prima di `s1.5`/`s2.5`. L'atlante `schaefer_300_tian_s2` ha il suo elenco regioni (`assets/atlases/sdc_labels/schaefer_300_tian_s2.csv`, 332 regioni, unione su 5853 CSV lesione e 5853 disconnettoma). Decisioni rimaste aperte: 716 soggetti con lesione non vuota ma zero regioni colpite (riga tutta a zero) restano nella matrice o escono con un nuovo scope; dove va il config di `s1.5`; `value_column` (`fraction_covered` è gonfiata nei dataset con maschere non binarie come PSP, `mean_overlap`/`sum_overlap` sono fuori scala per `sub-STUKLFR0088`). La rimozione del 25-08-26 era una scelta di scope dell'utente, non un bug (commit `2ed3dcb`); `management/notes/TODO.md`, citato dalla voce di allora, non esiste più.

## 15-10-26 — `clustering_evaluation`: tolti i grafici e il registro `produced_plots`

La sezione 6 del notebook (6.1 plot prodotti da `clustering.py`, `cluster_plot.png` e `silhouette_plot.png`) e l'helper `plot_production_runs` sono stati tolti, con gli import `matplotlib`/`seaborn` e `%matplotlib inline`. Il notebook resta fatto di tabelle. Via anche la voce `produced_plots` di `EVALUATIONS` (nessun consumatore).

Perché: i due plot sono già scritti in ogni cartella di run (95 run lesion su 95 li hanno) e si aprono da lì; il notebook li rileggeva da disco senza calcolare niente. In più il testo era sbagliato: diceva che le run a 10 componenti non hanno i plot, ma `clustering.py` le disegna su un UMAP 2D separato (`viz_embedding_path`), e `silhouette_plot.png` di adp (media 0,030, distanza dice saturata) compariva accanto alla purezza 0,922 che sostituisce la silhouette.

Conseguenza ancora vera: restano senza consumatori `clinical_association`, `centroids` e `representative_maps` in `EVALUATIONS` (sezioni passate a `cluster_interpretation`).

## 08-10-26 — Confronto tra run: sezione dell'Embedding Explorer, non una seconda pagina

Il confronto tra due run di clustering (`docs/guides/embedding_app.md`, "Confronto tra run") vive in fondo alla stessa pagina dell'app, con un menu "Indice" a scomparsa per navigare, invece che in una seconda pagina con il Clustering Explorer spostato lì.

Scartata la seconda pagina: il Clustering Explorer ha circa 40 callback agganciati ai selettori della pagina principale (`run-picker`, `cluster-picker`); spostarlo voleva dire riagganciarli tutti a un nuovo selettore, con rischio alto e nessun guadagno per chi legge. La sezione di confronto ha selettori propri (Run A, Run B), quindi non dipende dal run scelto in alto.

## 08-10-26 — `tuning_evaluations`: registro delle valutazioni del tuning di dim reduction e `evaluate_tuning_embeddings`

**Cosa è cambiato**: `dim_reduction.json` ha una chiave obbligatoria `tuning_evaluations` che elenca, un meccanismo per chiave, tutto ciò con cui il tuning è valutato: il punteggio dello sweep (`trustworthiness`, o `cumulative_explained_variance` per PCA) e `plot_hdbscan`. Il registro è `src/analysis/tuning_evaluations.py` (una `EvaluationSpec` per meccanismo: aggiungerne uno è aggiungere una voce). Le convenzioni su disco condivise tra chi scrive e chi rilegge un tuning (formato delle chiavi di `embeddings.npz`, cartelle delle foglie, caricamento di un run) stanno in `src/analysis/tuning_embeddings.py`; `_combo_key` è uscito da `dim_reduction.py`. Nuova pipeline `src/pipeline/evaluate_tuning_embeddings.py` (config `config/pipelines/evaluate_tuning_embeddings.json`, job `jobs/run_evaluate_tuning_embeddings.sh`): le valutazioni sugli embedding si rilanciano su un tuning già salvato, lesione e SDC, senza rifare lo sweep. Stessa esecuzione in entrambi i casi (`run_embedding_evaluations`).

**Perché**: richiesta di avere in config tutti i meccanismi di valutazione applicati, di poterli rilanciare a posteriori (uno sweep da ore non si rifà per aggiungere un grafico) e di aggiungerne altri senza toccare la pipeline.

**Scartato**:
- *Spostare `trustworthiness_n_neighbors` dai registri dei parametri al blocco*: tocca i due registri, il loader e i test, e non serve a dichiarare il meccanismo. Resta accanto al metodo a cui appartiene; il blocco elenca `trustworthiness` con `{}`.
- *Rendere disattivabile il punteggio dello sweep*: viene sempre calcolato, una chiave disattivabile non farebbe niente. Il blocco è validato contro ciò che lo sweep fa davvero, prima dello sweep.
- *Riusare `dim_reduction.json` come config dello standalone*: richiederebbe `input_path`, `session_name` e altri campi senza senso per una valutazione a posteriori.
- *Una riga in `runs_tuning.csv` per ogni valutazione a posteriori*: i file stanno nella cartella del tuning con le impostazioni nel nome, il log in `logs/evaluate_tuning_embeddings/`.

**Conseguenze che fanno sbagliare chi non le conosce**: ogni config di `dim_reduction`, anche di produzione, deve avere la chiave (può essere `{}`). Il tuning del clustering non ha ancora lo stesso (`.claude/open_problems.md`).

## 08-10-26 — Pannello "Composizione dei cluster" nell'app Dash; notebook di interpretazione rivisto

**Cosa è cambiato**: l'app Dash ha un nuovo pannello in fondo alla pagina, "Composizione dei cluster" (`src/analysis/cluster_composition.py`, `embedding_app.cluster_composition_content_for`): per un run di clustering, un grafico per variabile con tutti i cluster affiancati (dataset, lato, localizzazione dominante come barre al 100%; NIHSS, volume, carico di disconnessione come box plot nei colori dello scatter). `cluster_interpretation.ipynb` è stato riscritto: scelta della run seguendo i rami di `results/`, composizione dei cluster, soggetti rappresentativi di tutti i cluster in una figura, regressione logistica al posto dell'importanza per permutazione (`.claude/history/methods_changelog.md`).

**Rimosso dal notebook**: la mappa differenza cluster − resto (richiesta dell'utente) e la configurazione letta dai json delle pipeline: i percorsi dei dati e la griglia sono costanti scritte a mano nel notebook.

**Perché a mano**: le mappe si costruiscono dai file originali dei soggetti, non dalla matrice; servono solo cartella dati, glob e griglia. Le matrici dei cluster oggi guardati (s1.2-vol, s2.2-vol) sono a 1 mm, le più recenti (s1.4-vol, s2.4-vol) a 2 mm: il notebook disegna a 2 mm, con la griglia res-1 come alternativa dichiarata.

**Conseguenza**: l'app non dipende più da `build_sdc_matrix.json` solo per la composizione dei cluster (il pannello legge `participants.csv`); i pannelli delle mappe SDC continuano a richiedere un config `voxelwise`.

## 07-10-26 — Scope dei notebook di post-results: empirico contro interpretativo

**Cosa è stato deciso**: i notebook sotto `notebooks/post-results_analysis/` si separano per un criterio solo. Un'analisi che usa solo etichette e spazio del clustering è *empirica* (`clustering_evaluation` per una run, `clustering_comparison` per più run); una che porta variabili o immagini esterne (cliniche, demografiche, mappe) è *interpretativa* (`cluster_interpretation`). Scritto in `docs/guides/exploration.md` (criterio, tabella) e `docs/guides/evaluation.md` (dove vive ogni analisi, casi di confine).

**Casi di confine**: le distanze tra cluster nello spazio dell'embedding sono empiriche; nello spazio delle mappe o del profilo clinico sono interpretative. Il confronto tra le interpretazioni di due cluster abbinati (A∩B, A\B, B\A) sta in `cluster_interpretation`, che riceve l'abbinamento dal comparison; l'abbinamento è una funzione in `src/analysis/` perché i notebook non si importano.

**Scartato**: un notebook unico (vecchio `clustering_evaluation`, 101 celle, scope misti); due soli notebook con l'interpretazione dentro evaluation (la stessa analisi finiva in due posti, contro la regola "niente duplicati tra notebook").

**Conseguenza ancora vera**: `clustering_evaluation` §5, §6.2 e §6.3 duplicano `cluster_interpretation` e vanno tolte; `clustering_comparison` ha ancora la numerazione della versione unica. Entrambe le pulizie sono da fare.

## 07-10-26 — `cluster_interpretation.ipynb`: il notebook è il banco di prova dell'app Dash per interpretare i cluster

**Cosa è cambiato**: nuovo `notebooks/post-results_analysis/cluster_interpretation.ipynb`. Si sceglie la run (`RUN_KEY`) e il cluster (`CLUSTER`) in cima; riusa le stesse funzioni dell'app (`cluster_description`, `anatomical_maps`, `embedding_app.discover_production_runs`/`run_metadata`/`load_run`), quindi tabella, figura, overlap e mappe di disconnessione coincidono con quelle dell'app. Le mappe SDC si attivano da sole per una run `sdc` (`SHOW_SDC_MAPS`). In più, solo qui: composizione per dataset/lato/localizzazione, mappa differenza cluster − resto, test cluster contro resto con effect size. Eseguito end-to-end su una run sdc (cluster 0, 2m50) e su una run lesion hdbscan con il cluster di rumore (-1).

**Perché**: richiesta dell'utente. Le analisi nuove si provano nel notebook e, se servono, passano in `src/analysis/` con i test e poi nel pannello dell'app. L'ultima sezione del notebook elenca cosa è già nell'app e cosa è solo qui.

**Conseguenza**: `config/pipelines/build_sdc_matrix.json` oggi è `streamline` e l'app richiede un config `voxelwise` per le mappe SDC (`src/pipeline/embedding_app.py` fallisce all'avvio altrimenti). Il notebook non dipende da quel file: dichiara la griglia SDC (2mm, `nearest`, la stessa delle matrici `s2.x-vol`) nella cella di configurazione.

## 07-10-26 — `clustering_evaluation.ipynb` diviso in evaluation (una run) e comparison (più run)

**Cosa è cambiato**: il notebook unico (101 celle) è diventato due. `clustering_evaluation.ipynb` valuta una run alla volta, in sezioni per metodo di valutazione (geometriche, modello, stabilità, cliniche, grafici), ciascuna con metodo/cosa fa/come si legge/metodi applicabili. `clustering_comparison.ipynb` contiene ARI/NMI, match matrix, distanze tra centroidi e tutta la parte cross-modalità, spostate senza modifiche (71 celle), in attesa di riorganizzazione. Entrambi eseguiti end-to-end senza errori.

L'applicabilità per metodo è nel codice: `src/analysis/clustering_evaluation.py` (registro `EVALUATIONS`, `require_applicable`, `model_fit_metrics`) con `tests/unit/test_clustering_evaluation.py`; suite completa 1165/1165.

**Perché**: richiesta dell'utente. Non tutte le valutazioni valgono per tutti i metodi (inertia solo kmeans, BIC/AIC solo gmm, rumore solo hdbscan); il registro rende il vincolo verificabile invece che scritto soltanto nel testo.

**Scartato/rinviato**: le funzioni non committate in `clustering_tuning.py` (ICL, cophenetic, gap statistic) non sono state aggiunte come sezioni per-metodo, perché in lavorazione. Una stabilità al seed (kmeans/gmm/spectral) non c'è: non esisteva nel notebook originale.

**Conseguenza**: `docs/guides/evaluation.md` descrive entrambi i notebook. I numeri di sezione del comparison sono ancora quelli della vecchia versione unica, quindi alcuni rimandi interni ("Parte 1 §3") sono sfasati finché non viene riorganizzato.

## 07-10-26 — `build_lesion_matrix`: eliminato il summary in `summaries/`, resta il `config.md` accanto alla matrice

**Cosa è cambiato**: la pipeline non scrive più `summaries/build_lesion_matrix/<project>/build_summary__*.md`. Restano il `config.md` nella cartella della matrice, il log in `logs/build_lesion_matrix/<project>/` e la riga in `runs.csv`. Rimossi `REPORTS_ROOT`, `_build_report`, `_write_report`; `REPORT_FILENAME_PREFIX` rinominata `LOG_FILENAME_PREFIX`, stesso valore (`build_summary`), perché i nomi dei log restino uguali a quelli delle pipeline sorelle.

**Perché**: richiesta dell'utente. Il summary era il `config.md` con la sola intestazione diversa (verificato con `diff` sulla run `s1.4-vol`): stesso contenuto in due posti, nessuna informazione in più.

**Alternativa scartata**: tenere il summary come copia indipendente dalla cartella dei dati. Il log di ogni run riporta già esclusi e corretti e vive fuori da `data/`, quindi una copia fuori dalla cartella della matrice non serve.

**Non fatto**: le altre pipeline con lo stesso meccanismo (`build_sdc_matrix`, `build_fc_matrix`, `mask_fc` e le altre che definiscono `REPORTS_ROOT`) producono ancora il loro summary. Le cartelle `summaries/build_lesion_matrix/` già scritte restano su disco, non più alimentate.

## 06-10-26 — `enrich_metadata`: `overwrite` + file delle celle protette al posto di `fill`

**Cosa è cambiato**: il flag `fill` di `config/pipelines/enrich_metadata.json` è eliminato. Al suo posto, due campi obbligatori: `overwrite` (`false` = append, scrive solo le celle vuote; `true` = riscrittura, sostituisce ogni cella in scope) e `protected_path` (un json `{"columns": [...], "subjects": [...]}`, oggi `assets/metadata/participants_protected.json`, vuoto; `null` = nessuna protezione). Una cella la cui colonna o il cui soggetto è elencato non viene mai scritta, né in append né in riscrittura, nemmeno se è vuota. La regola vale per **tutte** le colonne che la run scrive, comprese quelle copiate da `lesion_metadata.csv` e `sdc_metadata.csv`, che con `fill` venivano sempre sovrascritte. Valore in uso: `overwrite: true`, cioè lo stesso comportamento di `fill: false` che c'era prima. Codice: `src/pipeline/enrich_metadata.py` (`_apply`, `_check_write_rules`, `ProtectedCells`), 92 test in `tests/unit/test_enrich_metadata.py`.

**Perché**: richiesta dell'utente. `participants.csv` è un join ma anche un file in cui si possono correggere a mano colonne o soggetti, e `fill` copriva solo una parte dei casi (le colonne cliniche; le derivate erano un'eccezione cablata nel codice). Stesso nome e stesso significato di `overwrite` in `populate_metadata` e in `build_excluded_subjects`.

**Alternative scartate**: (a) un terzo flag `update` accanto a `fill`: `fill: false` già propagava le correzioni dei tsv, e nessun flag può sia propagare le fonti sia proteggere le celle ritoccate a mano, perché il file non registra quali lo siano; (b) un `mode` a due valori al posto del booleano: stesso contenuto di `overwrite`, ma un nome diverso da quello che le altre due pipeline già usano; (c) protezione per cella (soggetto × colonna): più casi da validare di quelli che servono.

**Conseguenze ancora vere oggi**: (1) in append una colonna derivata resta al valore vecchio se la maschera è cambiata: la run lo segnala a `WARNING` per colonna (valori esistenti diversi dal fresco) ma non lo corregge, serve `overwrite: true`; la regola "le colonne derivate si sovrascrivono sempre" non esiste più. (2) Con `overwrite: true` una cella vuota nella fonte svuota quella del registro, senza avviso: ciò che esiste solo nel registro va protetto. (3) `geometric_override_datasets` non vuota richiede `overwrite: true`; `lesion_side` e `lesion_side_source` si proteggono insieme. (4) Il commit `9eca847` contiene una versione intermedia di queste modifiche al codice, rilasciata prima che config, test e doc fossero allineati: il working tree successivo è quello coerente.

## 05-10-26 — `build_excluded_subjects`: modo predefinito append, `overwrite: true` per ricostruire dal solo config

**Cosa è cambiato**: la pipeline `build_excluded_subjects` (voce successiva) riscriveva il csv per intero a ogni run, quindi il config doveva contenere tutti i soggetti esclusi. Ora ha un flag obbligatorio `overwrite` nel config. Con `false` (valore in uso) il csv esistente resta com'è, comprese le righe aggiunte o tolte a mano, e le righe del config vengono **aggiunte**: una riga già presente per lo stesso soggetto, scope e motivo non si tocca (se il `value` calcolato dal config è diverso resta quello del file, con una nota nel log e nel report), lo stesso soggetto e scope sotto un altro motivo solleva, un file assente viene creato, uno con lo schema vecchio non si può estendere. Con `true` il csv è ricostruito dal solo config. Il validatore delle pipeline di matrice gira sempre, sul risultato, prima di sostituire il file.

**Perché**: richiesta dell'utente. Con la scrittura per intero il config diventava lungo e andava tenuto allineato al csv; così il csv, una volta scritto, resta tale, il config contiene solo i soggetti da aggiungere e per togliere una riga basta cancellarla dal csv. Stesso schema di `overwrite` in `populate_metadata`.

**Alternativa scartata**: il csv sempre derivato dal config (modo unico `overwrite`), che dava una sola fonte di verità ma obbligava a tenere nel config anche i soggetti già scritti.

**Conseguenza ancora vera oggi**: con `overwrite: false` la fonte di verità è il **csv**, non il config: un soggetto tolto dal config resta nel csv, e uno tolto dal csv a mano ricompare alla run successiva se è ancora nel config (conviene svuotare il config dopo l'uso). Con `overwrite: true` la fonte torna a essere il config e ciò che il csv conteneva d'altro è perso. Config attuale: le stesse 15 righe di HEAD, già nel csv (la run in append le salta); il csv è identico a HEAD.

## 05-10-26 — `excluded_subjects.csv` è generato da una pipeline, `build_excluded_subjects`, da un config che elenca i soggetti

**Cosa è cambiato**: nuova pipeline `src/pipeline/build_excluded_subjects.py` (+ `config/pipelines/build_excluded_subjects.json`, `jobs/run_build_excluded_subjects.sh`, `tests/unit/test_build_excluded_subjects.py`). Il config contiene, per ogni coppia (motivo, scope), gli ID dei soggetti esclusi e da dove viene il `value` (una colonna di `lesion_metadata.csv`, oppure una costante). La pipeline ricava `dataset` dal registro, controlla il risultato con `load_excluded_subjects` su un file temporaneo e sostituisce il csv in modo atomico. Il csv non si modifica più a mano. Config iniziale: le 15 righe di HEAD (1 `empty_mask` con scope `all`, 14 `all_zero_features` con scope `sdc-streamline`); la prima run ha rigenerato un file identico a HEAD.

**Perché**: l'ultima cella di `lesion_analysis` possedeva solo tre dei quattro motivi del file e lo riscriveva per intero, cancellando le righe che non conosceva (voce precedente, stesso giorno). Una pipeline che possiede **tutto** il file, con tutti i motivi nel config, elimina il problema alla radice: non c'è più nessun altro scrittore del csv, quindi nessuna fusione.

**Alternative scartate**: (a) pipeline che possiede solo i tre motivi di lesione e lascia il resto del csv: rimette in gioco la fusione, due scrittori sullo stesso file; (b) regole con soglie invece di ID espliciti: contraddice la scelta del 29-09 (`cf6e1fe`) di sostituire le soglie di qualità con una lista curata a mano. Per `all_zero_features` il `value` è la costante `0` (numero di feature non nulle, per definizione): calcolarlo vorrebbe dire aprire la matrice SDC.

**Conseguenza ancora vera oggi**: la decisione sta nel config, non nel csv. Aggiungere o togliere un soggetto = modificare `exclusions` e rilanciare la pipeline; una modifica a mano al csv viene persa alla run successiva. L'ultima cella di `lesion_analysis` non scrive: stampa i blocchi da incollare nel config (la voce successiva descrive la versione precedente, "solo stampa" delle righe CSV).

## 05-10-26 — L'ultima cella di `lesion_analysis` non scrive più `excluded_subjects.csv`: stampa le righe da incollare

**Cosa è cambiato**: la cella finale del notebook (l'unica di esplorazione che scriveva un file di produzione) riscriveva `excluded_subjects.csv` per intero con le sole liste `EXCLUSIONS`, che partivano vuote, e non conosceva la colonna `scope`. Ora calcola `dataset` e `value` per gli ID dati (tre motivi: `empty_mask`, `lesion_too_small`, `out_of_brain_fraction_too_high`, scope `all`) e **stampa** le righe CSV da incollare a mano; non legge né scrive il file.

**Perché**: il file ha 15 righe in HEAD, 14 delle quali (`all_zero_features`, scope `sdc-streamline`) non vengono da questa cella, che non conosce quel motivo: qualunque esecuzione le cancellava. È successo due volte (la seconda il 05-10-26 alle 10:30: il file è rimasto alla sola intestazione `subject_id,dataset,reason,value`, senza `scope`).

**Alternativa scartata**: una cella che fonde i propri tre motivi nel file esistente, con `CONFIRM_WRITE` e validazione prima di scrivere. Implementata e collaudata, ma più complessa di quanto serva: dipendeva dallo schema del file (sollevava finché il file non era ripristinato) e aggiungeva parametri da tenere a mente. Scartata su richiesta dell'utente a favore della sola stampa.

**Conseguenza ancora vera oggi**: il file `assets/metadata/excluded_subjects.csv` in lavoro ha ancora lo schema vecchio e nessuna riga (HEAD ne ha 15 con `scope`): il notebook non lo tocca più, quindi va ripristinato o riscritto a mano.

## 05-10-26 — Ritirate le pipeline di retrieval e di calcolo SDC; la regola di naming dei soggetti passa a `src/utils/subject_ids.py`

**Cosa è cambiato**:
- Eliminati `src/retrieval/` (config, dataset, output_layout, verify), `src/sdc/` (config, manifest, resample, runner, staging, status), `src/pipeline/retrieve_data.py`, `src/pipeline/compute_sdc.py` (~2850 righe), `src/atlases/` (solo un `__pycache__` residuo: la pipeline atlas era già stata ritirata il 25-08-26).
- Config: `config/pipelines/{retrieval_server,retrieval_local,retrieval_sdc,compute_sdc}.json`, `config/registry/file_patterns_{local,server}.json`. Jobs: 6 (`run_retrieve_data`, `run_retrieve_sdc`, `run_compute_sdc{,_manifest,_aggregate,_no_slurm}`). Test: 16 file (12 unit, 4 integration; 183 test, di cui 22 in 2 file che giravano solo sul cluster per `bcblib`). Doc: `docs/guides/retrieval.md`, `docs/dev/retrieval.md`, `docs/guides/compute_sdc.md`.
- Suite: prima 1076 passed + 12 skipped (con i 2 file cluster esclusi con `--ignore`), dopo 918 passed, nessuno skipped, nessuna esclusione necessaria.

**Perché**: nessun codice vivo dipendeva da queste pipeline tranne un punto — `group_of`/`KNOWN_GROUPS`/`KNOWN_SITES`, la regola che dal nome di un soggetto (`sub-<DISEASE><SITE>[HC]<NUM>`) ricava il gruppo ST/HC/PD/GM, importata da `features/lesion.py`, `features/subject_discovery.py`, `features/sdc.py`, `populate_metadata.py`, `analysis/build_config.py` e `scripts/build_dataset_summary_table.py`. Spostata in `src/utils/subject_ids.py` (il livello più basso), con i suoi test di regressione (sito inventato che termina in "HC", lessons_learned #20). La spiegazione della regola vive ora in `docs/guides/datasets.md` ("Naming dei soggetti"), richiamata da `docs/dev/metadata.md`.

**Scartato**: tenere `src/retrieval/` solo per `group_of` (un pacchetto intero per una funzione, con la dipendenza `analysis → retrieval` che resterebbe senza motivo); documentare `compute_sdc` in una guida ridotta (deciso: la guida resta solo in git, nei doc una nota breve).

**Conseguenze ancora vere**:
- I dati si copiano a mano sotto `data/clinical_connectome/`; il formato delle cartelle non è cambiato ed è il contratto che i builder leggono.
- L'output SDC (`sdc/<subject_id>/*`) arriva da BCBToolKit fuori da questo repo; `build_sdc_matrix.py` lo legge come prima. Per rilanciare un soggetto (es. `sub-STUKLFR0671`, `open_problems.md`) non c'è più una pipeline qui.
- `assets/atlases/` NON è stato toccato: `fmriprep/` serve a `mask_fc.json`, `sdc_labels/` a `build_sdc_matrix.json`.
- `lessons_learned.md` e `docs/debugging/*` citano ancora i path eliminati nelle voci "Seen in": sono archivio, lasciati com'erano.

## 01-10-26 — Notebook riorganizzati per oggetto sotto ispezione: `lesion_analysis` si scioglie, `lesion_quality` ne prende il nome

**Cosa è cambiato**:
- Il vecchio `exploration/lesion_analysis.ipynb` (prototipo preistorico del costruttore di matrice + volumetria + overlap voxel-wise) è sciolto. Setup, caricamento maschere, costruzione di `X`, fast loading, sanity check, riduzione ai voxel non costanti, matrix visualization e frequenza voxel-wise → nuovo `pipeline_building/lesion_matrix_build.ipynb`.
- `exploration/lesion_quality.ipynb` è rinominato `exploration/lesion_analysis.ipynb` e riordinato per sezioni: Volume → Lateralità → Fuori dal brain → Soggetti esclusi. `show_scrollable` spostata nelle utilità in cima. La volumetria del vecchio notebook (ml, boxplot, violin/ECDF, percentili, coda lunga) vi è stata **riscritta su `lesion_metadata.csv`** (`lesion_volume_voxels_2mm` × 8 / 1000), non spostata: dipendeva da `X.sum(axis=1)`, cioè dalla matrice costruita nel notebook.
- `exploration/clinical_metadata_raw.ipynb` → `exploration/metadata_raw.ipynb`, con scope dichiarato in testa (legge i TSV grezzi, non `participants.csv`); titoli `###` → `##`.
- Nuova guida `docs/guides/exploration.md` (indice: domanda / legge / scrive per ogni notebook); rimandi in `README.md`, `.claude/CLAUDE.md`, 4 doc e 3 docstring aggiornati. Via le intestazioni "Parte X di 3".

**Perché**: gli scope si sovrapponevano (la distribuzione dei volumi stava in due notebook, calcolata in due modi). Criterio adottato: un notebook = un oggetto sotto ispezione + una domanda. Alternativa scartata: rinominare `lesion_quality` in `lesion_volume` — avrebbe descritto solo un terzo del contenuto (c'è anche lateralità, fuori dal brain e la cella che scrive `excluded_subjects.csv`, che legge soglie da tutte le sezioni); scissione in due notebook scartata per lo stesso motivo.

**Conseguenza ancora vera oggi**: l'ultima cella di `lesion_analysis` sovrascrive `assets/metadata/excluded_subjects.csv` con le sole liste `EXCLUSIONS` del notebook. Il file su disco ha una colonna `scope` che la cella non scrive e il notebook ha `EXCLUSIONS` vuoto: la cella è **indietro** rispetto al file e rieseguirla lo azzera. Non toccata in questa sessione.

## 30-09-26 — Embedding Explorer: per i colori il registro `participants.csv` vince sul `metadata.csv` della run

**Cosa è cambiato**: in `src/analysis/embedding_coloring.py` (commit `89de145`, 30-09-26) ogni modalità di colore che dichiara una `registry_column` legge il valore da `assets/metadata/participants.csv`, non più dal `metadata.csv` della run; le modalità senza colonna di registro continuano a leggere dalla run. Prima l'ordine era inverso. Nello stesso commit è stata aggiunta la modalità volume con un bottone per griglia (default `2mm`).

**Perché**: una run costruita prima del 06-09-26 porta nel proprio `metadata.csv` una **copia** di `lesion_side`, `nihss` e volume che può divergere dal registro; con l'ordine vecchio due run degli stessi soggetti si coloravano in modo diverso. È la stessa scelta di fonte unica per il dato del soggetto già presa per `build_sdc_matrix` e `dim_reduction` (README, sezione metadati).

**Conseguenza ancora vera oggi**: un dato del soggetto viene dal registro, un dato della run dal `metadata.csv` di quella run (`docs/guides/embedding_app.md`, «Regola unica»). Un registro non aggiornato cambia il colore di tutte le run, comprese quelle vecchie.

## 30-09-26 — Embedding Explorer: il selettore Cluster esce dal primo pannello e pilota tutta la sezione

**Cosa è cambiato**: il menu «Cluster» (`cluster-picker`) stava dentro il primo pannello della sezione clustering ed è passato a livello di sezione (commit `89de145`, 30-09-26), con un callback che mostra o nasconde l'intera sezione (`clustering-section`). Ora pilota tutti i pannelli che seguono: overlap map, frequency map, soggetto rappresentativo, descrizione del cluster.

**Perché**: dentro il primo pannello sembrava un controllo di quel pannello soltanto. È una scelta di layout dell'interfaccia, archiviata su richiesta dell'utente (21-10-26) perché i docs descrivono ormai solo il comportamento attuale, senza la data.

**Conseguenza ancora vera oggi**: nessuna sul codice o sui dati. Il comportamento attuale è in `docs/guides/embedding_app.md`.

## 29-09-26 — Embedding Explorer: pannello «Descrizione del cluster», scelte di layout fatte su richiesta

**Cosa è stato deciso** (commit `2cfb871` e, per il fondo grigio del riquadro di avviso, `7bb7892`; `src/analysis/cluster_description.py` e `embedding_app.py`; ogni voce nacque da un'osservazione dell'utente sul risultato a schermo):
- **Griglia a 3 colonne** (`_GRID_COLUMNS = 3`) invece di una riga sola per le 5 variabili. Con la pagina a 1100 px ogni sotto-grafico veniva ~200 px, troppo stretto per assi leggibili, e tick e titoli andavano rimpiccioliti («così non si capisce niente, con label e assi così piccoli»). Font alzati su tutto il pannello («in generale aumenta un po' il font»).
- **Un colore per variabile**, lo stesso per il grafico e per l'intestazione della sua colonna nella tabella sotto, senza legenda («vorrei più varietà nei colori dato che stiamo plottando variabili diverse»).
- **Tabella delle statistiche numeriche sotto i grafici, con tutti i cluster a confronto** (`ClusterStats` per ogni cluster) invece del solo cluster selezionato.
- **Avvisi di risultato parziale in un riquadro unico**: etichetta ATTENZIONE in maiuscolo, superficie **grigio neutro** (`#f4f4f3`) e non un fondo ambra, perché un fondo colorato si leggeva come uno stato.
- **Niente barre né colore dentro le celle**: le barre dati in cella erano state costruite e poi tolte, insieme alla sottolineatura colorata dell'intestazione, perché confondevano la lettura della tabella («non voglio quelle righe colorate nella tabella, mi confondono la lettura»).
- **Numeri in formato italiano** (`_format_number`: `.` per le migliaia, `,` per i decimali, `5.265,4`), perché l'intera app è in italiano e `5265.4` si leggeva male.

**Conseguenza ancora vera oggi**: la descrizione dei dati sta in `docs/dev/cluster_description.md`; qui restano le ragioni, che altrimenti sembrerebbero arbitrarie. Le dimensioni e i colori non vanno riportati a un layout a riga unica senza rivedere la larghezza utile (1100 px).

---

## 29-09-26 — Embedding Explorer: soggetti non risolvibili avvisano invece di fermare i pannelli aggregati

**Cosa è cambiato** (commit `2cfb871`): `anatomical_maps.py` guadagna `resolve_available_lesion_paths(...) -> (resolved, missing)`: per le mappe aggregate per cluster (overlap della lesione, frequenza di disconnessione) un soggetto di cui non c'è il file non blocca più la mappa; viene scritto un WARNING con i soggetti esclusi, e solleva solo se **nessuno** dei soggetti richiesti è risolvibile. `resolve_lesion_paths` resta severa (un viewer di singolo soggetto con risultato parziale non ha senso). Nello stesso commit, il pannello «Descrizione del cluster» tiene un soggetto assente da `participants.csv` come riga tutta mancante (`n_total` resta la dimensione vera del cluster) e mostra un avviso, invece del `ValueError` che prima fermava l'intero pannello (richiesta esplicita dell'utente).

**Perché**: rifiutare di descrivere gli altri soggetti di un cluster perché alcuni sono più recenti del registro è una risposta peggiore di descriverli nominando i mancanti. Il caso non è ipotetico: la sostituzione delle maschere locali del 23-09-26 (`data_changelog.md`) ha tolto il file locale a 24 soggetti UKLFR e 7 WashU, che restano però nel `metadata.csv` delle run di `lesion_matrix`/`clustering.py` costruite prima di quella data.

**Conseguenza ancora vera oggi**: una mappa o una tabella per cluster può essere calcolata su meno soggetti del cluster; il numero escluso è nell'avviso e nel log, mai taciuto.

---

## 29-09-26 — `scripts/` ridotto a 3 accessori: 4 entry point promossi a `src/pipeline/`, 6 script cancellati

`scripts/` conteneva 13 file (12 `.py` + 1 `.sh`) di tre nature diverse mescolate: veri entry point di pipeline, utility accessorie e one-off già eseguiti. Ora ne restano **3**, tutti e soli accessori: `archive_local_raw_data.py` (potatura/archiviazione della cache locale sotto `data/`), `build_dataset_summary_table.py` (tabelle LaTeX dei conteggi per dataset), `build_dim_reduction_strategies_csv.py` (indice derivato `results/dim_reduction_strategies.csv`).

**Promossi a `src/pipeline/`** (ora 16 entry point), per `code_standards.md` §1 "entry point centralizzati": `populate_metadata.py`, `calibrate_lesion_side_threshold.py`, `replot_dim_reduction.py`, `plot_tuning_embedding_3d.py`. Tutti e 4 avevano già la forma di una pipeline (argparse, report sotto `summaries/`, log sotto `logs/`, job in `jobs/`); `populate_metadata.py` in particolare ha config dedicata, `log_duration` e semantica `overwrite`, cioè la stessa struttura funzione-per-funzione di `enrich_metadata.py`, che stava già in `src/pipeline/`. Invocazione passata da `PYTHONPATH=. python scripts/X.py` a `python -m src.pipeline.X` ovunque (docstring, 3 job, guide, README, notebook, test); i 3 job hanno perso l'`export PYTHONPATH`, non più necessario. Aggiunto `jobs/run_calibrate_lesion_side_threshold.sh`, che mancava (ora 21 job).

**Cancellati (6)**, tutti recuperabili da `git log`:
- `download_sdc.py` (+ `jobs/run_download_sdc.sh`, `tests/unit/test_download_sdc.py`) — duplicava `config/pipelines/retrieval_sdc.json` + `jobs/run_retrieve_sdc.sh`: stessi 5 dataset, stessi 6 suffissi, stesso motore `retrieve_data.run()`. La lista dei 5 dataset era ricopiata a mano nello script, seconda fonte di verità per un elenco che sta già nella config. Il sottoinsieme che lo script otteneva via flag CLI si ottiene ora copiando la config e riducendone `datasets`/`retrieve` (documentato in `docs/guides/retrieval.md`).
- `download_lesions.sh` — `scp` in loop con IP, utente e path locale assoluto hardcoded, nessuna gestione errori, nome fuorviante (scaricava `desc-disconnectome.nii.gz`, cioè SDC). La sua destinazione `sdc_download/` era vuota (0 B): mai andato a buon fine.
- `verify_retrieval.py` (+ job + test) — la stessa `verify.verify_dataset` gira già in automatico nella fase post-copy di ogni run di `retrieve_data.py`; lo script serviva solo a ri-verificare senza fare una run, e per farlo importava tre funzioni **private** di `retrieve_data` (`_build_datasets`, `_select_subjects`, `_validate_upfront`).
- `backfill_runs_csv_input_path.py`, `backfill_stale_tuning_output_paths.py` (+ test), `rename_nemesis_t0_subjects.py` — one-off già eseguiti (i primi due ad agosto, il terzo il 23-09-26), non ripetibili con effetto: le cartelle `sub-p*` di NEMESIS_T0 sono già rinominate, le colonne `input_path` già riempite, i path pre-riorganizzazione già corretti.

**Alternative scartate**: (a) spostare in `src/pipeline/` anche i 3 accessori rimasti — `archive_local_raw_data.py` gestisce la cache locale e non produce nessun artefatto scientifico, gli altri due sono reporting/indici derivati: non sono passi di analisi e metterli fra gli entry point renderebbe `src/pipeline/` un contenitore indistinto; (b) conservare i 3 one-off in un `scripts/oneoff/` — la narrativa di cosa hanno fatto ai dati sta già in `data_changelog.md`, e il codice in `git log`: tenerli sarebbe codice morto (§2) con l'aggravante di sembrare rilanciabili.

**Conseguenza ancora vera oggi**: le voci più vecchie di `.claude/history/` e di `docs/debugging/` nominano questi file ai loro path di allora (`scripts/populate_metadata.py`, `scripts/replot_dim_reduction.py`, ...). Sono corrette per la data in cui sono state scritte e **non vanno riscritte**: questa voce è il punto di raccordo fra i vecchi path e quelli attuali.

---

## 29-09-26 — `enrich_metadata.py` diventa un join: non legge più nessuna maschera

`enrich_metadata` calcolava da sé i valori derivati dalle maschere, attraverso il blocco `lesion_metrics` (che nella prima versione della giornata ereditava perfino il config di `build_lesion_matrix.py`, poi reso autonomo — vedi la voce sostituita da questa). Ora è un **join fra sorgenti**: i tsv clinici per le variabili anagrafiche, e `assets/metadata/lesion_metadata.csv` per tutto ciò che viene dalle maschere. Rimossi `LesionMetricsConfig`, `MaskGrid`, `_load_lesion_metrics_config`, `_load_grids`, `compute_fresh_lesion_volumes`, `compute_geometric_lesion_sides` e gli import di `nibabel` e `src.features.lesion`: la pipeline non apre più nessun file NIfTI.

Il blocco di config è `lesion_metadata`, con tre chiavi: `path`, `copy_columns` (colonne copiate **con lo stesso nome**, per tutti i soggetti in scope, sovrascrivendo) e `lesion_side_from` (quale colonna del csv riempie `lesion_side`, **solo dove la risoluzione clinica ha lasciato la cella vuota**, scrivendo anche `lesion_side_source="geometric"`). In produzione: `copy_columns: ["lesion_volume_voxels_2mm"]`, `lesion_side_from: "lesion_side_2mm"`.

**Perché due chiavi invece di una lista sola**: `lesion_side` ha una regola di scrittura diversa da tutte le altre colonne (condizionale, e scrive anche una seconda colonna). Metterla in `copy_columns` avrebbe richiesto che la pipeline conoscesse per nome quella voce e la trattasse diversamente dalle altre — una regola implicita nel codice invece che dichiarata nel config. Discusso con l'utente, che ha prima chiesto di unificare e poi di tornare a due chiavi, per una ragione ulteriore: in `participants.csv` la colonna resta `lesion_side` **senza suffisso di griglia**, perché per i circa 1445 soggetti con etichetta clinica il valore non viene da nessuna griglia — un suffisso `_2mm` sarebbe falso per la maggioranza delle celle. `lesion_side_from` dice da quale griglia viene la parte geometrica, e `lesion_side_source` dice quale delle due provenienze ha vinto per ogni soggetto.

**Alternativa scartata**: rinominare la colonna del registro in `lesion_side_2mm`, così che sorgente e destinazione avessero sempre lo stesso nome e `copy_columns` fosse uniforme. Costava un rename in `embedding_coloring.py`, `calibrate_lesion_side_threshold.py`, 6 asserzioni di test, due notebook e tre docs — ma soprattutto avrebbe attribuito una risoluzione a valori clinici che non ne hanno una.

**Conseguenza ancora vera oggi**: il join è **stretto nei due sensi** e solleva invece di saltare: un soggetto in scope con `has_lesion=True` e senza riga nel csv significa csv vecchio; una riga per un soggetto che il registro non conosce, o che conosce come `has_lesion=False`, significa che i due file sono in disaccordo su chi ha una maschera. Le colonne derivate dalle maschere **non sono più correggibili a mano** in `participants.csv`: ogni run le ricopia. Un valore inaffidabile si sistema sulla maschera e si ricalcola, oppure il soggetto va in `excluded_subjects.csv`. `main()` legge il registro tramite `src.utils.participants.load_participants_registry`, non con un `read_csv` grezzo, perché il join ha bisogno di `has_lesion` come booleano vero: su un registro `dtype=str` un `astype(bool)` mapperebbe la stringa `"False"` a `True` e invertirebbe silenziosamente tutti i controlli (bug trovato e corretto durante l'implementazione, con test dedicato).

---

## 29-09-26 — `assets/metadata/lesion_metadata.csv`: le metriche dalle maschere diventano un livello a sé, `check_lesion_quality` ritirata

**Cosa è cambiato**: nuova pipeline `src/pipeline/compute_lesion_metadata.py` (config `config/pipelines/compute_lesion_metadata.json`, job `jobs/run_compute_lesion_metadata.sh`, log e summaries propri) che produce `assets/metadata/lesion_metadata.csv`: una riga per ogni soggetto con maschera, quattro colonne per griglia. È **agnostica del clinico**: non apre nessun `participants.tsv` e non sa cosa sia un NIHSS.

Ritirata `src/pipeline/check_lesion_quality.py` con il suo test, il suo job e le sue cartelle in `logs/`/`summaries/` (spostata sotto `src/pipeline/` solo poche ore prima, vedi la voce sotto — il nuovo file la sostituisce interamente e ne assorbe l'unica metrica, `out_of_brain_fraction`). `assets/metadata/lesion_quality_metrics.csv` resta su disco finché il nuovo csv non è prodotto e il notebook non gira. Cancellate da `src/features/lesion.py` le quattro funzioni rimaste senza chiamanti — `compute_lesion_volumes`, `compute_lesion_quality_metrics`, `compute_lesion_laterality_metrics`, `_out_of_brain_fractions`, 158 righe — sostituite da una sola `compute_lesion_metadata`.

**Perché**: prima le metriche derivate dalle maschere erano sparse su tre posti con tre scopi diversi (una cache diagnostica in `lesion_quality_metrics.csv`, due colonne nel registro scritte da `enrich_metadata`, una colonna nel `metadata.csv` di ogni matrice) e nessuno dei tre le aveva tutte. Tre funzioni di libreria rileggevano indipendentemente le stesse maschere, una per metrica. Un livello solo, prodotto da una pipeline sola, con `enrich_metadata` che ne copia un sottoinsieme nel registro: ogni metrica ha un posto dove nasce e uno solo.

**Alternativa scartata**: tenere il calcolo dentro `enrich_metadata` e aggiungerci le metriche mancanti. Avrebbe lasciato una pipeline che fa due lavori diversi (leggere imaging e leggere tsv clinici) e nessun posto dove stiano `out_of_brain_fraction` e l'indice di lateralità, che al registro non servono ma al notebook sì.

**Conseguenza ancora vera oggi**: il calcolo è **in streaming**, un soggetto per volta, e non passa per `_voxelwise_matrix_with_volume` come fa `build_lesion_matrix`. Quella funzione impila in memoria il volume appiattito di ogni soggetto: circa 5,3 GB sulla griglia a 2 mm (902.629 voxel x 5853 soggetti, uint8) e circa **42 GB** su quella a 1 mm, che non è eseguibile da nessuna parte. Chi in futuro volesse "riusare la funzione che c'è già" per aggiungere una griglia fine sbatterebbe esattamente lì. Accanto al csv la pipeline scrive `lesion_metadata.config.json`, il config risolto della run che l'ha prodotto: un csv di cui non si sappia su quali griglie e con quale correzione è stato calcolato non è interpretabile (`lessons_learned.md` #18/#36).

---

## 29-09-26 — `check_lesion_quality.py` spostato da `scripts/` a `src/pipeline/`

**Cosa è cambiato**: `git mv scripts/check_lesion_quality.py src/pipeline/check_lesion_quality.py` (storia git preservata). Invocazione aggiornata da `PYTHONPATH=... python scripts/check_lesion_quality.py` a `python -m src.pipeline.check_lesion_quality`, coerentemente con ogni altro entry point in `src/pipeline/`. Aggiornati tutti i riferimenti al vecchio path: `jobs/run_check_lesion_quality.sh`, `tests/unit/test_check_lesion_quality.py` (import), `docs/guides/matrix_building.md`, `docs/dev/lesion_matrix.md`, `docs/guides/metadata.md`, commenti in `src/features/lesion.py`/`src/pipeline/enrich_metadata.py`/`src/analysis/build_config.py`/`scripts/calibrate_lesion_side_threshold.py`, `tests/unit/test_build_config.py`, e due celle markdown di `notebooks/exploration/dataset_exploration.ipynb` (una delle quali citava anche, per errore ormai superato, "il calcolo geometrico di lesion_side resta da fare" - corretta nella stessa modifica).

**Perché**: richiesto esplicitamente dall'utente - lo script è un vero entry point di pipeline (CLI con `--config`/`--output-path`/`--overwrite`, report/log propri, stessa forma di `enrich_metadata.py`/`build_lesion_matrix.py`), non uno script accessorio/one-off. `code_standards.md` §1: "Entry point centralizzati - punto d'ingresso unico in `src/pipeline/`, niente script sparsi". Era finito sotto `scripts/` solo perché creato lì il 28-09-26 (voce sotto), non per una scelta architetturale deliberata.

**Conseguenza ancora vera oggi**: nessuna - `src/pipeline/check_lesion_quality.py` è stato **ritirato poche ore dopo**, nella stessa giornata (voce in cima a questo file): la pipeline che lo sostituisce, `compute_lesion_metadata.py`, è nata direttamente sotto `src/pipeline/`. Resta valida solo la convenzione che quello spostamento applicava, e che vale per il nuovo file: gli entry point stanno in `src/pipeline/`, e i loro test sotto `tests/unit/` piatto, senza specchiare la sottocartella di `src/`.

---

## 29-09-26 — `enrich_metadata.json`: `lesion_volume_config`/`lesion_side_geometric` unificati in `lesion_metrics`

**Cosa è cambiato**: i due campi di config separati per i metadati calcolati dalle maschere (`lesion_volume_config`, `lesion_side_geometric`, ognuno con la propria copia di `build_matrix_config`) sono diventati un unico blocco `lesion_metrics`, con due flag booleane indipendenti (`compute_volume`/`compute_side`) e una sola fonte condivisa (`build_matrix_config`). Aggiunta anche `correct_out_of_brain` (condivisa da entrambe le metriche): prima `compute_lesion_volumes()`/`compute_lesion_laterality_metrics()` bypassavano del tutto la correzione fuori-cervello di `build_lesion_matrix()` (`src/features/lesion_correction.py`, aggiunta lo stesso giorno da un'altra sessione), un gap silenzioso che avrebbe fatto tornare a divergere `lesion_volume_voxels`/`lesion_side` in `participants.csv` rispetto a una matrice di produzione costruita con quella correzione attiva — stessa famiglia di bug della voce "artefatto vs calcolo fresco" del 28-09-26 in `methods_changelog.md`, questa volta per omissione invece che per staleness. Rimossa anche `excluded_subjects` (era solo su `lesion_side_geometric`): mai popolata, nessun caso reale l'ha richiesta.

**Perché**: discusso esplicitamente con l'utente. Motivazione per l'unificazione: i due metadati condividono la stessa fonte (le maschere) e la stessa scelta di correzione — due config separati duplicavano `build_matrix_config` e rischiavano di far divergere `correct_out_of_brain` tra le due metriche senza alcun controllo. Motivazione per la rimozione di `excluded_subjects`: un'esclusione decisa dopo aver ispezionato la distribuzione in analisi richiede comunque di editare un config e rilanciare la pipeline (minuti di calcolo) — più macchinoso che correggere a mano la cella in `participants.csv` (un CSV versionato in git), che `fill: true` già lascia intatta alla run successiva. Stesso pattern già in uso nel progetto per `lesion_quality_metrics.csv` (`scripts/check_lesion_quality.py`): calcolo completo senza filtri, decisione a valle.

**Alternativa scartata**: mantenere `excluded_subjects` "per il futuro". Scartata per `code_standards.md` (non costruire per un bisogno ipotetico) — se un caso reale la richiederà, si reintroduce con un caso concreto in mano, non a priori.

**Aggiornamento, stessa giornata**: il caso concreto è arrivato nel giro di poche ore, e l'esclusione per soggetto è stata reintrodotta in forma diversa — non come campo di `enrich_metadata` ma come file unico letto dalle due pipeline di matrice (`assets/metadata/excluded_subjects.csv`, vedi `methods_changelog.md`). L'intero blocco `lesion_metrics` descritto in questa voce non esiste più: `enrich_metadata` è diventato un join (voce in cima a questo file).

**Conseguenza ancora vera oggi**: `correct_out_of_brain` è una flag indipendente in `enrich_metadata.json` e in `build_lesion_matrix.json` — **non c'è bisogno di tenerle allineate**. Le due pipeline hanno scopi diversi (registro anagrafico/demografico contro input dell'embedding, quest'ultimo rilanciabile più volte con impostazioni diverse tra una sessione e l'altra), quindi possono legittimamente divergere per scelta. Non è lo stesso problema del 28-09-26: lì un valore veniva copiato da un artefatto vecchio e spacciato per aggiornato; qui entrambe calcolano il proprio valore fresco con la propria configurazione esplicita. (Correzione della voce originale, scritta erroneamente come un vincolo di sincronizzazione.)

---

## 29-09-26 — Eliminato `scripts/lesion_fix.py`, superseduto da `src/features/lesion_correction.py`

**Cosa è cambiato**: rimosso `scripts/lesion_fix.py` — script standalone mai integrato in nessuna pipeline (nessun riferimento da `src/`/test), con un path hardcoded a `/Users/sebastiano/fsl/data/standard/MNI152_T1_2mm_brain_mask.nii.gz` (macchina di un altro utente, mai esistito su questo repo). Faceva esattamente la stessa correzione (azzerare i voxel di lesione fuori da una maschera cerebrale) ora implementata correttamente, testata e wired nella pipeline dal nuovo `src/features/lesion_correction.py`, attivabile via `correct_out_of_brain` — vedi la voce del 29-09-26 in `methods_changelog.md` per la decisione metodologica.

**Perché**: codice morto per `code_standards.md` §2 (nessun chiamante reale, path rotto) una volta che la stessa funzionalità esiste come modulo proprio, testato e raggiungibile da config.

**Conseguenza ancora vera oggi**: nessuna — la correzione va fatta tramite `correct_out_of_brain` in `build_lesion_matrix.json`, non più tramite quello script.

---

## 28-09-26 — Nuovo script `scripts/check_lesion_quality.py` + cache `assets/metadata/lesion_quality_metrics.csv`

**Cosa è cambiato**: `src/features/lesion.py` guadagna `compute_lesion_quality_metrics` (pubblica, senza soglie di ammissione - riusa `_voxelwise_matrix_with_volume`/`_load_and_binarize_brain_mask`/`_out_of_brain_fractions`, già scritte per `build_lesion_matrix.py`'s `min_lesion_volume_voxels`/`max_out_of_brain_fraction`, vedi voce del 28-09-26 in `methods_changelog.md`). Due nuovi consumatori la chiamano invece di ricalcolare da zero: `scripts/check_lesion_quality.py` (CLI, riusa `config/pipelines/build_lesion_matrix.json` come sorgente di configurazione, scrive `assets/metadata/lesion_quality_metrics.csv` in modo atomico, `--overwrite` per forzare il ricalcolo) e la sezione "Lesione fuori dal brain" di `notebooks/exploration/dataset_exploration.ipynb`, che prima usava una propria implementazione copiata (con `nilearn.datasets.load_mni152_brain_mask()`, una maschera MNI generica scaricata da internet, non l'asset di progetto) - ora importa la stessa funzione e usa lo stesso `assets/templates/tpl-MNI152NLin6Asym_res-1_desc-brain_mask.nii.gz` della pipeline di produzione, quindi notebook e script vedono esattamente gli stessi numeri. Aggiunto anche `jobs/run_check_lesion_quality.sh`.

**Perché**: il calcolo (un caricamento+resampling nibabel/nilearn per soggetto) è costoso - minuti sull'intera coorte di ~5700 soggetti, verificato eseguendo la vecchia versione nel notebook. Serve poterlo eseguire una volta sola e riusare il risultato, sia da script standalone sia da notebook, senza duplicare la logica di calcolo (solo il calcolo, non l'I/O: la cache CSV è nel chiamante, `compute_lesion_quality_metrics` resta puro, nessuna scrittura su disco).

**Superseduta il 29-09-26, stessa giornata**: `assets/metadata/lesion_quality_metrics.csv` e lo script che lo produceva non esistono più. Il file che ne prende il posto è `assets/metadata/lesion_metadata.csv` (voce in cima a questo file), che contiene *tutte* le metriche derivabili da una maschera invece della sola frazione fuori dal brain, e su ogni griglia. Resta valida l'idea per cui quel file era nato: la decisione di ammissione si prende guardando la distribuzione reale, non indovinando un valore — cambiato solo *come* la decisione viene registrata (una lista curata a mano, non una soglia in un config).

---

## 23-09-26 — `reference_template_path` sostituito con un vero template MNI152 versionato

**Cosa è cambiato**: `config/pipelines/build_lesion_matrix.json` e `build_sdc_matrix.json`
puntavano entrambi `reference_template_path` alla lesion mask di un singolo paziente
(`sub-STUNIPD0001`, WashU, sotto `data/`, gitignored) — funzionava solo perché shape/affine
di quel file coincidevano con una griglia MNI152 nota. Sostituito con due template reali,
versionati, sotto `assets/templates/` (`tpl-MNI152NLin6Asym_res-1_T1w.nii.gz` 1mm e
`_res-2_T1w.nii.gz` 2mm, scaricati da TemplateFlow, shape/affine verificati contro i dati del
progetto). Entrambi i config ora puntano al `_res-1_` (1mm). Nessuna modifica a codice:
`load_reference_image`/`resample_to_img` leggono solo shape+affine, mai il contenuto voxel —
un template T1w funziona in modo identico a una maschera binaria come riferimento di griglia.
Rimosso anche il pin `must_keep={"sub-STUNIPD0001"}` in `scripts/archive_local_raw_data.py`,
non più necessario. Scaricate anche le brain mask corrispondenti (`_res-1_desc-brain_mask.nii.gz`/
`_res-2_desc-brain_mask.nii.gz`, stessa fonte, griglia/affine verificati identici alle T1w) — non
ancora usate da nessun codice, disponibili sotto `assets/templates/` per quando servirà.

**Perché**: fragilità già segnalata come TODO aperta (`docs/dev/lesion_matrix.md`, sezione
"Known open question") — l'intera griglia voxel di produzione dipendeva dalla sopravvivenza
di un file paziente specifico, non versionato. Il rischio si è concretizzato lo stesso giorno:
una sostituzione non correlata delle lesion mask WashU/UKLFR (vedi `data_changelog.md`,
23-09-26) ha cambiato silenziosamente quel file da 2mm a 1mm, quindi la griglia di riferimento
per *ogni* dataset in ogni run futuro — scoperto solo verificando la risoluzione dei nuovi
file prima di aggiornare `docs/guides/datasets.md`, non da un errore/crash.

**Alternative scartate**: patchare l'affine del template scaricato per farlo combaciare
bit-per-bit con la griglia post-swap di `sub-STUNIPD0001` (origin -90 invece di -91) — scartata
perché quella griglia non era mai stata "la" griglia canonica del progetto, solo un artefatto
incidentale di un file paziente; adottare la griglia autoritativa TemplateFlow è più corretto,
e `resample_to_img` riallinea comunque correttamente qualunque sorgente al nuovo riferimento.

**Conseguenza ancora vera oggi**: le matrici già costruite in passato non sono toccate (la loro
griglia era fissata al momento del build); solo i nuovi run raccolgono il nuovo riferimento. La
scelta 1mm/2mm è un edit di config (`reference_template_path` punta a `_res-1_` o `_res-2_`),
non richiede codice.

---

## 23-09-26 — `main` riportato al passo e adottato come branch di lavoro di default

**Cosa è cambiato**: `main` era rimasto indietro di 121 file (+16516/-21005 righe) rispetto al lavoro reale, che da settimane continuava solo su branch di task mai rimersi. Fast-forward di `main` sulla punta di `fix/sdc-drop-dwi-folder` (nessun conflitto: `main` non aveva nemmeno un commit unico non già contenuto nel branch), pushato su `origin/main`. Ripuliti 6 branch locali: 4 già completamente mergeati (`clustering-embedding-tag-naming`, `clustering-runs-csv-reduction-columns`, `embedding-app-anatomy-panels`, `tag-params-multi-key` — cancellazione sicura), `fix/sdc-drop-dwi-folder` stesso (ridondante dopo il fast-forward, cancellato anche dal remoto), e `backup-pre-split` (non mergeato — 2 commit isolati su un punto vecchio pre-refactor "split", cancellazione forzata).

**Perché**: nessuno rimergeva mai i branch di task in `main`, che restava una fotografia vecchia mentre il lavoro vero viveva altrove — scoperto controllando lo stato reale dei branch dopo che `.claude/stato_progetto.md` è risultato disallineato (citava un branch, `metadata-restructuring`, che non era nemmeno più il checkout corrente).

**Decisione per il futuro**: si lavora su `main` di default; un branch nasce solo per un task specifico e viene mergeato/cancellato appena concluso — mai tenuto in vita come branch parallelo permanente. Vedi `.claude/branch_alignment.md`.

**Conseguenza ancora vera oggi**: `main` locale e `origin/main` sono allineati (stesso commit). `backup-pre-split` è recuperabile da `068d2ff` (`git checkout -b backup-pre-split 068d2ff`) finché il reflog lo conserva.

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

---

## 01-09-26 — Palette categorica dei cluster estesa da 5 a 10 colori, validata solo sulle coppie adiacenti

**Cosa è cambiato** (commit `4b4111e`, `_CATEGORICAL_PALETTE` in `src/analysis/plotting.py`): da 5 a 10 tonalità. Le 5 originali erano validate su **tutte le coppie** (ΔE peggiore 8,6/18,3, sopra le soglie 8,0/15,0); le 10 solo sulle coppie **adiacenti** (visione dei colori compromessa inclusa).

**Perché**: le run HDBSCAN di produzione su s1.1-vol trovano di norma 8-20 cluster reali (rumore escluso) a `min_cluster_size`/`min_samples` ragionevoli, e 5 colori si ripetevano 2-4 volte rendendo illeggibile `cluster_plot.png`.

**Alternative scartate**: la linea guida dataviz dice che una palette categorica sicura su tutte le coppie arriva a 3-4 slot per uno scatter, qualunque sia la dimensione della palette: nessuna palette distingue 8-20 cluster in un solo scatter. Le soluzioni vere sarebbero piccoli multipli (un pannello per cluster) o accorpare i cluster minori in «Altro». Scelta dell'utente: l'espansione a 10 colori solo-adiacenti come compromesso, non come soluzione.

**Conseguenza ancora vera oggi**: oltre 10 cluster i colori si ripetono ancora. Non cambiare i colori senza rieseguire la validazione (`validate_palette.js`, citato nel commento della costante).

---

## 01-09-26 — `clustering.py`: il tag dell'embedding si deriva da `input_path`, `session_name` non lo contiene più

**Cosa è cambiato** (commit `7c56ad6`): `ClusteringConfig` guadagna `reduction_params_file` (obbligatorio se `reduced_data` è true, vietato altrimenti): il `config/registry/params_reduction*.json` che ha prodotto `input_path`. `clustering.py::_embedding_tag` ne legge `tag_param`/`tag_prefix` e ricostruisce il tag (es. `m_euclidean_nc2`) dai parametri realmente registrati nel `config.md` di `input_path`, e lo inserisce nei nomi delle cartelle di produzione e tuning. `session_name` porta solo l'id di sessione (es. `s1.1`).

**Perché**: prima il tag andava digitato a mano dentro `session_name` senza nulla che lo validasse contro l'`input_path` vero: un rischio di deriva silenziosa, trovato producendo i primi risultati di clustering lesionale.

**Alternativa scartata**: dedurre quale dei due registri (`params_reduction.json` per la lesione, `params_reduction_sdc.json` per l'SDC) ha prodotto l'embedding dal testo del percorso di `input_path`, o da una convenzione sul numero di sessione (s1 = lesione, s2 = SDC). Scartata perché `docs/experiments/` è narrativa scritta a mano, mai pensata per essere letta da una pipeline di produzione (`lessons_learned.md` #20/#22, stessa disciplina di `reduction_method`): il registro si dichiara in `reduction_params_file`.

**Conseguenza ancora vera oggi**: `reduction_params_file` va dichiarato in ogni config di clustering su un embedding; il tag nei nomi cartella è quello vero dell'embedding, non quello che qualcuno ha scritto.

---

## 01-09-26 — Rimossa `production/comparison/` da `clustering.py`

**Cosa è cambiato**: `clustering.py` non genera più, su richiesta, la cartella `comparison/` sotto `production/` (il plot di confronto cross-metodo `cluster_comparison.png`/`cluster_comparison_interactive.html`).

**Perché**: per confrontare più metodi oggi si aprono i `cluster_plot.png` di ciascuno, oppure si usa `embedding_app.py` (un run alla volta) — il confronto cross-metodo dedicato è stato ritenuto non necessario.

**Conseguenza ancora vera oggi**: nessuna pipeline produce un artefatto di confronto multi-metodo. Un'eventuale cartella `comparison/` residua da prima di questa data resta sul disco ma è esclusa automaticamente dalla discovery di `embedding_app.py` (non ha mai un `manifest.json`).

---

## 31-08-26 — `clustering.py`: `reduction_method` obbligatorio con un segmento in più nell'albero dei risultati, e tre colonne `reduction_*` in `runs.csv`

**Cosa è cambiato** (commit `5ac2243` e `29233db`):
- `ClusteringConfig.reduction_method` è obbligatorio (convalidato contro `REDUCTION_METHODS | {"raw"}`) e dichiara quale metodo di riduzione ha prodotto la matrice di `input_path` (`"raw"` se `reduced_data` è falso). Mai dedotto dal testo del percorso. Aggiunge un segmento: `production/<metodo>/<reduction_method>/<gg-mm>_<sessione>/` e `tuning/<metodo>/<reduction_method>/...`.
- `runs.csv`/`runs_tuning.csv` di `clustering.py` e il `config.md` di ogni run registrano `reduction_method`, `reduction_n_components`, `reduction_metric`, letti dal `config.md` dell'embedding sorgente (`read_run_params`) e confrontati con `reduction_method` dichiarato, mai ridichiarati come campo di config a parte.

**Perché**: risultati prodotti da embedding sorgente diversi non devono finire nella stessa cartella. I tre campi hanno il prefisso `reduction_` perché `gmm` ha come iperparametro proprio `n_components` (`lessons_learned.md` #33).

**Conseguenza ancora vera oggi**: `embedding_app.py::discover_production_runs` ha una profondità di glob che dipende dalla pipeline; senza quell'adattamento ogni run di clustering sarebbe sparita dal selettore senza errori. Risultati scritti prima del 31-08-26 sono sul layout senza il segmento; 30 foglie di clustering/tuning sono state spostate a mano sotto `umap/` e 5 `runs_tuning.csv` hanno guadagnato la colonna (dal messaggio del commit, `results/` è ignorato da git).

---

## 31-08-26 — `runs.csv`: tolta la colonna `id`

**Cosa è cambiato** (commit `29233db`): `FIELDNAMES` in `src/utils/run_log.py` passa da `session, id, timestamp, input_path, params, output, notes` a `session, timestamp, input_path, params, output, notes`; `extra_columns` si inserisce subito dopo `session`. `id` era la seconda metà di `run_id` (il tag dopo il primo `_`, es. `m_euclidean_nc2`).

**Perché**: duplicava un'informazione già recuperabile dal nome della cartella `output` e dalle colonne `tag_param` esplose in `extra_columns`; un controllo con `grep` su tutto il repo non ha trovato nessun lettore che la riparsasse.

**Alternativa scartata, nello stesso giro**: descrivere l'input di `clustering.py` come JSON annidato dentro `input_path`. Provato e annullato nella stessa sessione, su richiesta, per tenere `input_path` della stessa forma (un `Path`) per ogni chiamante; la descrizione ricca sta in `extra_columns`.

**Conseguenza ancora vera oggi**: `append_run_log_entry` solleva `ValueError` se l'header di un `runs.csv` esistente non coincide con lo schema corrente (`lessons_learned.md` #32): un file con la vecchia colonna `id` va migrato a mano. Con quel commit sono stati migrati 22 `runs.csv`/`runs_tuning.csv`, 35 `config.md` di tuning di clustering e 2 `runs.csv` di `masked_fc`/`fc_matrix` precedenti a qualunque schema attuale (dal messaggio del commit; `results/` e `data/derived/` non sono in git).

---

## 26-08-26 — `write_embeddings_grid` eliminato: con la regola su `n_components` era ridondante

**Cosa è cambiato**: il campo obbligatorio `write_embeddings_grid: bool` di `DimReductionConfig` (aggiunto il 04-08-26 come interruttore manuale per saltare `embeddings_grid_*.png` e i rifit costosi di una foglia annidata) non esiste più; la sua rimozione dal codice è nel commit `b6d972b` (data del commit 27-08-26). La griglia non viene mai prodotta per una combinazione con `n_components != 2`, in nessun caso: `_build_grid_blocks` non chiama più `embedding_for_viz`, scarta la cella (loggata) e le celle sorelle a 2 componenti restano. La regola e le due richieste dell'utente sono in `docs/debugging/debug_26_08_26.md`.

**Perché**: a `random_state` fisso un rifit a 2 componenti è identico byte per byte alla foglia gemella già calcolata a `n_components=2` (verificato a vista il 04-08-26), e la vista 3D reale di una combinazione si ottiene su richiesta con `scripts/plot_tuning_embedding_3d.py`. Un opt-out più grossolano che spegne l'intera griglia a prescindere da `n_components` diventa ridondante.

**Conseguenza ancora vera oggi**: nessun flag di config controlla la griglia; il test `test_dim_reduction_fine_tuning_free_n_components_drops_non_viz_cells` fissa la regola.

---

## 15-08-26 — `embedding_plot_interactive.html`/`plot_clusters_interactive` per-run rimossi, sostituiti da `embedding_app.py`

**Cosa è cambiato**: `dim_reduction.py` (14-08-26) e poi `clustering.py` (15-08-26, quando `embedding_app.py` è stato esteso a scoprire anche i run di `clustering.py`) hanno smesso di scrivere un file `.html` interattivo per-run (`embedding_plot_interactive.html`, `plot_clusters_interactive`). Un solo processo live, l'app Dash `src.pipeline.embedding_app`, copre invece tutti i run di produzione già scritti (di entrambe le pipeline), con un selettore di run e bottoni di colorazione.

**Perché**: un file HTML per-run va rigenerato ad ogni run e non scala con il numero di run prodotti; un'app che legge `matrix.npy`/`metadata.csv` già su disco copre tutti i run esistenti e futuri senza rigenerazione.

**Correzione (21-10-26, verificata su git)**: per `plot_embedding_interactive` la data è giusta (rimossa il 14-08-26, commit `2c997b9`). Per `clustering.py` no: `plot_clusters_interactive` e le sue chiamate in `clustering.py` erano ancora presenti al commit `2991ec1` (15-08-26) e sono state tolte dal commit `b6d972b` del 27-08-26 («remove interactive HTML plots»). `docs/dev/plotting.md` e la memoria del progetto datavano la rimozione di `plot_clusters_interactive` al 27-08-26, che è la data corretta; dal 15-08-26 è giusto solo che `embedding_app.py` scoprisse anche le run di `clustering.py`.

**Conseguenza ancora vera oggi**: nessuna pipeline di dim reduction/clustering scrive più un file `.html` interattivo per singolo run — l'esplorazione interattiva 2D/3D di qualunque run di produzione passa sempre da `embedding_app.py` (`docs/guides/embedding_app.md`).

---

## 15-08-26 — `data_sessions.md` spostato da `data/` a `docs/experiments/`

**Cosa è cambiato**: il diario umano delle sessioni (`data_sessions.md`, cosa significa un `session_name` — dataset, modalità, cosa è cambiato) si è spostato da `data/data_sessions.md` a `docs/experiments/data_sessions.md`. Il symlink `results/data_sessions.md` è stato rimosso.

**Perché**: è narrativa di progetto scritta a mano, non un dato grezzo/derivato — sta meglio con il resto di `docs/` che nell'albero `data/` (gitignored). La sua informazione confluisce anche nelle colonne `session`/`modality`/`datasets` di `results/dim_reduction_strategies.csv`, generato da `scripts/build_dim_reduction_strategies_csv.py`.

**Conseguenza ancora vera oggi**: `docs/experiments/data_sessions.md` è l'unica fonte per il significato di un `session_name`; non esiste più un symlink sotto `results/`.

---

## 14-08-26 — `dim_reduction_clustering.py` ritirato, capacità assorbita da `clustering.py`

**Cosa è cambiato**: lo script "riduci poi cluster" in un solo comando (`dim_reduction_clustering.py`, allora il più usato del progetto) è stato eliminato. `clustering.py` guadagna un campo di config obbligatorio `reduced_data: bool` — dichiara se `input_path` è un embedding già calcolato o una matrice grezza — e (26-08-26) `viz_embedding_path` per disegnare i cluster quando `X` non ha 2/3 colonne. Il flusso in due passi (`dim_reduction.py` poi `clustering.py --reduced_data true`) sostituisce integralmente il comando unico.

**Perché**: `dim_reduction_clustering.py` duplicava quasi per intero l'orchestrazione CLI di `clustering.py` (stesso `_run_one_method`, stesso `_write_tuning_output`, stessa run-log) solo per aggiungere un `embed()` a monte — la logica algoritmica vera era già condivisa in `src/analysis/`, la duplicazione era solo nel layer `src/pipeline/`.

**Alternativa scartata**: far ricalcolare la riduzione al volo dentro `clustering.py` stesso (un `embed()` interno). Scartata in sessione come troppo complessa da implementare bene subito — `clustering.py` non chiama mai `embed()`, in nessun ramo; `reduced_data` è puramente dichiarativo, mai un trigger di calcolo.

**Conseguenza ancora vera oggi**: `src/pipeline/dim_reduction_clustering.py`, il suo config e il suo job non esistono più. La logica di viz a 2/3/>3 componenti (`_resolve_viz_embedding` in `clustering.py`, `embedding_for_viz` in `reduction.py`) e i campi `reduced_data`/`viz_embedding_path` sono documentati in `docs/dev/models.md`/`config.md`. I risultati storici sotto `results/lesion/dim_reduction_clustering/` restano un archivio del vecchio pipeline, non spostati.

---

## 2026-08 — Produzione e tuning separati in due rami sotto `output_root` (`dim_reduction.py`/`clustering.py`)

**Cosa è cambiato**: `results/lesion/dim_reduction/production/<metodo>/...` e `results/lesion/dim_reduction/tuning/<metodo>/...` (stesso schema per `clustering.py`) sono due rami separati sotto `output_root`, mai mescolati. Prima di questa riorganizzazione, `tuning/` viveva dentro la cartella del metodo (`<metodo>/tuning/...`).

**Conseguenza ancora vera oggi**: risultati scritti prima di questa riorganizzazione possono trovarsi sul vecchio layout (`<metodo>/tuning/...`) invece che sotto un ramo `tuning/` di primo livello — chi ispeziona risultati storici più vecchi di questa riorganizzazione deve tenerlo a mente; i risultati nuovi seguono sempre lo schema a due rami.
