# Changelog dei dati

Cosa è successo ai dati sotto `data/` — trasferimenti, potature, ripristini, spostamenti, correzioni.

**Perché esiste**: `data/` è gitignored, quindi `git log` non sa niente di cosa gli è successo. La storia del *codice* sta in git e non va duplicata qui; questo file copre solo ciò che git non può raccontare.

**Cosa NON va qui**: lo stato attuale dei dati (quello sta in `docs/guides/datasets.md`, sempre al presente) e i pattern di errore generalizzabili (`.claude/lessons_learned.md`).

Voci in ordine cronologico inverso.

---

## 04-11-26 — Eliminate 11 cartelle e 3 file di `tmp/` (593 MB)

**Cosa è cambiato**: cancellate per scelta dell'utente, senza copia altrove (`tmp/` è gitignored). `tmp/` passa da 858 MB a 265 MB; restano `fc_nan_analysis/` (lavoro in corso) e `s2.4_raw_clustering/` (262 MB).

| Voce | Dimensione | Contenuto |
|---|---|---|
| `s2.4_pca42_clustering/` | 526 MB | prototipo di clustering su score PCA a 42 componenti (16-10) |
| `s2.4_umap_nc50_tuning/` | 34 MB | tuning UMAP a 50 componenti (18-10) |
| `anatomy_rendering/` | 23 MB | 83 file di prototipi del rendering anatomico (29-09) |
| `hdbscan_old_flow_19-10-26/`, `cluster_tuning_notebooks_backup_19-10-26/`, `report_samples_19-10-26/`, `cluster_tuning_residual_tables_19-10-26/`, `cluster_reports_commented_19-10-26/`, `summary_md_19-10-26/` | 8,5 MB | backup e campioni del vecchio flusso di clustering (19-10). `cluster_tuning_notebooks_backup_19-10-26/` era l'**unico posto** con i generatori dei vecchi notebook e `plot_labels_on_2d` |
| `hdbscan_condensed_tree/` | 428 KB | script di analisi dell'albero condensato di HDBSCAN (21-10) |
| `verifica_contenuto_21_10_26/` | 228 KB | brief, prompt, stato e rapporti della verifica di contenuto |
| `pca_variance_table.{pdf,png,tex}` | 56 KB | tabella della varianza PCA |

**Conseguenza ancora vera**: restano riferimenti a questi percorsi in `src/analysis/embedding_app/anatomy.py` (quattro commenti citano le immagini di confronto di `tmp/anatomy_rendering/`), in `.claude/audit/` e nelle voci precedenti dei changelog (`project_changelog.md` 19-10-26 cita il backup dei notebook e `SUMMARY.md`; `methods_changelog.md` i report commentati).

## 04-11-26 — Eliminate 4 cartelle di `results/legacy/` (25 GB)

**Cosa è cambiato**: cancellate per scelta dell'utente, senza copia altrove. `results/legacy/` passa da 50 GB a 25 GB (resta `clustering_spectral_kmeans_gmm_adp_28-10-26/`, più una cartella vuota `legacy/`).

| Cartella | Dimensione | Contenuto |
|---|---|---|
| `sdc_s2.4-vol_07-10/` | 25 GB | sessione s2.4-vol del 07-10 (matrice vecchia, senza `correct_out_of_brain`): dim reduction UMAP e clustering di agglomerative, HDBSCAN, HDBSCAN soft, ADP, più i `runs*.csv` con le 39 righe spostate il 02-11-26 |
| `clustering_prodotti_flusso_vecchio_26-10-26/` | 95 MB | prodotti del vecchio flusso di clustering (`old_products*`, `old_interclass`, `old_membership_share`) |
| `cluster_tuning_notebooks_flusso_vecchio_26-10-26/` | 460 KB | `all_candidates.csv` del 18-10 (lesione e SDC) e 8 file di confronto tra embedding `nc2`/`nc3`/`nc10`; **erano le uniche copie** |
| `management_cheatsheets_26-10-26/` | 36 KB | `clustering_metrics_report.md` e una copia risalvata (la versione in git resta nella storia) |

**Perché**: spazio. La s2.4-vol del 07-10 è su una matrice superata (la ricostruisce la s2.4-vol del 16-10) e non sarebbe mai stata utilizzata. Le altre tre erano copie di sicurezza che nessun codice legge.

**Conseguenza ancora vera**: le voci di `project_changelog.md` e `data_changelog.md` dal 26-10-26 al 02-11-26 che citano queste cartelle descrivono percorsi che non esistono più. I `runs*.csv` delle 39 righe s2.4-vol spostate il 02-11-26 sono andati con la cartella. `docs/experiments/s2.4-vol.md` non ha link a queste cartelle (verificato con `grep`).

## 02-11-26 — 39 righe di `runs*.csv` di `results/sdc/` spostate nei log di `results/legacy/sdc_s2.4-vol_07-10/`

**Cosa è cambiato**: le 39 righe `s2.4-vol` dei log di `results/sdc/` con `output` verso cartelle già spostate in `results/legacy/sdc_s2.4-vol_07-10/` (28-10-26) sono state tolte dai log originali e scritte, verbatim e con la stessa intestazione, in un `runs.csv`/`runs_tuning.csv` nello stesso percorso relativo sotto `results/legacy/sdc_s2.4-vol_07-10/` (prima la cartella non aveva nessun log). La colonna `output` delle righe spostate resta il percorso vecchio sotto `results/sdc/`, come nei log dei quattro metodi spostati il 28-10-26.

| Log (percorso relativo) | Righe spostate | Righe rimaste |
|---|---|---|
| `clustering/production/agglomerative/runs.csv` | 14 | 127 |
| `clustering/production/hdbscan/runs.csv` | 7 | 36 |
| `clustering/production/hdbscan_soft/runs.csv` | 5 | 24 |
| `clustering/tuning/{agglomerative,hdbscan}/runs_tuning.csv` | 3 + 3 | 14 + 14 |
| `clustering/tuning/hdbscan_soft/runs_tuning.csv` | 3 | 10 |
| `dim_reduction/production/umap/runs.csv` | 3 | 9 |
| `dim_reduction/tuning/umap/runs_tuning.csv` | 1 | 3 |

**Come**: script nello scratchpad che separa le righe per CSV (taglio sulle righe grezze, nessuna riserializzazione). Prima di scrivere ha verificato che ogni `output` spostato esista sotto `results/legacy/sdc_s2.4-vol_07-10/` e dopo che i conteggi di righe tornino (39 spostate; 237 rimaste negli otto file toccati). Dopo lo spostamento nessuna riga di `results/{lesion,sdc}/**/runs*.csv` ha un `output` inesistente.

**Perché**: la voce del 28-10-26 afferma che in `results/` non restano righe con `output` verso percorsi inesistenti; per queste 39 non era vero (`lessons_learned.md` #24).

**Conseguenza ancora vera oggi**: nessuna sulle cartelle. Un lettore dei log di `results/sdc/` non conta più run che non ci sono; le run `07-10_s2.4-vol` si leggono nei log di `results/legacy/sdc_s2.4-vol_07-10/`.

---

## 29-10-26 — `production_results*.csv` scritti in 36 produzioni hdbscan_soft (con persistenza)

**Cosa è cambiato**:
- In tutte le 36 cartelle sotto `results/{lesion,sdc}/clustering/production/hdbscan_soft/` sono stati aggiunti `production_results.csv` (`n_clusters_found`, `noise_fraction`, `largest_cluster_share`, `dbcv`, `membership_mean`, `persistence_mean`) e `production_results_per_cluster.csv` (`cluster,n,dbcv,membership_mean,persistence`).
- Cancellati i 20 `dbcv_per_cluster.csv`: stesse colonne e valori nel nuovo file per cluster (verificato run per run prima di cancellare).
- `metadata.csv` non toccato: `membership_own` c'era già in tutte le 36 e coincide con il ricalcolo.

**Come**: refit del `HDBSCAN` del pacchetto `hdbscan` (`hdbscan_soft_fit`) sulla `matrix.npy` di ogni run. `persistence` è `cluster_persistence_` del fit. Il refit è accettato perché riproduce le etichette salvate (36 su 36) e la matrice `membership.npy` (differenza massima 0.0).

**Allineamento della persistenza**: il pacchetto non documenta l'ordine di `cluster_persistence_`. Assunto: indice = etichetta del cluster. Verificato in modo indipendente su 6 run con almeno 3 cluster, ricostruendo la stabilità di ogni cluster dall'albero condensato: stabilità / (persistenza × dimensione del cluster) è costante tra i cluster con l'ordine per etichetta, e non lo è con l'ordine spostato di uno.

**Casi limite**: 16 run hanno 0 cluster (tutti rumore): `largest_cluster_share`, `dbcv`, `membership_mean`, `persistence_mean` vuoti con la nota, file per cluster con la sola intestazione. Nessuna run con 1 solo cluster.

**Verifica**: `Clusters found` e rumore del `config.md` coincidono in 36 su 36; `persistence_mean` = media di `persistence`; `membership_mean` per cluster = media di `membership_own`. Zero errori, zero `.tmp`.

**Conseguenza ancora vera oggi**: le persistenze di hdbscan_soft non sono confrontabili con nulla di hdbscan (sklearn non le ha).

---

## 29-10-26 — `production_results*.csv` e `membership_own` scritti in 79 produzioni hdbscan

**Cosa è cambiato**:
- In 79 cartelle sotto `results/{lesion,sdc}/clustering/production/hdbscan/` (tutte tranne le 2 del 10-09) sono stati aggiunti `production_results.csv` (`n_clusters_found`, `noise_fraction`, `largest_cluster_share`, `dbcv`, `membership_mean`) e `production_results_per_cluster.csv` (`cluster,n,dbcv,membership_mean`).
- Aggiunta la colonna `membership_own` (ultima) a `metadata.csv` delle stesse 79 run: probabilità del soggetto nel proprio cluster, vuota per il rumore.
- Cancellati i 63 `dbcv_per_cluster.csv`: il nuovo file per cluster ha le stesse colonne `cluster,n,dbcv` con gli stessi valori (verificato run per run prima della cancellazione), più `membership_mean`.

**Come**: refit di `HDBSCAN(**params)` sulla `matrix.npy` di ogni run (stessa chiamata della produzione, `hdbscan_labels_and_probabilities`), accettato solo perché le etichette ricalcolate coincidono con `cluster_label` salvate: 79 su 79. Nessuna produzione rigenerata, nessun `config.md` modificato.

**Casi limite**: 16 run hanno 0 cluster (tutti i soggetti rumore): `largest_cluster_share`, `dbcv` e `membership_mean` vuoti con la nota, file per cluster con la sola intestazione. Nessuna run ha 1 solo cluster.

**Verifica**: `Clusters found` e numero di punti rumore del `config.md` coincidono con il ricalcolato in 79 su 79; `membership_own` è vuota esattamente dove `cluster_label` è -1; `membership_mean` per cluster coincide con la media di `membership_own`. Zero errori, zero file `.tmp`.

**Conseguenza ancora vera oggi**: `dbcv_plot.png` resta; la run del 10-09 (2 cartelle hdbscan) non ha né `production_results*.csv` né `membership_own`.

---

## 29-10-26 — `production_results*.csv` scritti in 151 produzioni agglomerative; `noise_fraction` tolta da 28 `tuning_results.csv`

**Cosa è cambiato**:
- In 151 cartelle sotto `results/{lesion,sdc}/clustering/production/agglomerative/` (tutte tranne le 5 del 10-09) sono stati aggiunti `production_results.csv` (`metric,value,note`: silhouette, calinski_harabasz, davies_bouldin, dunn, largest_cluster_share, cophenetic_correlation, dendrogram_jump) e `production_results_per_cluster.csv` (`cluster,n,silhouette_mean,share_negative`). Con distanza non euclidea CH/DB/Dunn sono vuoti con la nota `Euclidean distance only` (62 run).
- Cancellati i 151 `silhouette_per_cluster.csv`, sostituiti dal nuovo file per cluster, che ha lo stesso contenuto (colonne e valori identici, verificato run per run prima della cancellazione).
- Tolta la colonna `noise_fraction` da tutte le 28 `tuning_results.csv` di agglomerative (16 con `report.md`, poi le 12 senza, su ordine esplicito dell'utente); era 0.0 in tutte le righe, verificato prima di riscrivere, e il resto della tabella è identico dopo la rilettura.

**Come**: calcolo con `src/analysis/production_results.py` (lo stesso codice della produzione) su `matrix.npy` e `metadata.csv` di ogni run; nessuna produzione rigenerata, nessun `config.md` modificato.

**Verifica**: per le 61 run del 26-10, ogni indice ricalcolato coincide con la riga del proprio `config.md` (tolleranza 1% / 5e-4, `—` ↔ vuoto); per le 151, il file per cluster ricalcolato coincide con il vecchio `silhouette_per_cluster.csv`. Zero errori, zero file `.tmp`.

**Conseguenza ancora vera oggi**: i `config.md` delle run precedenti al 28-10 conservano ancora gli indici nella sezione Summary (e `Clusters found`), le run nuove no: la fonte unica dei numeri è `production_results.csv`.

---

## 28-10-26 — `dbcv_per_cluster.csv` e `dbcv_plot.png` scritti in 83 produzioni hdbscan / hdbscan_soft che non li avevano

**Cosa è cambiato**: in 83 cartelle sotto `results/{lesion,sdc}/clustering/production/{hdbscan,hdbscan_soft}/` (63 `hdbscan`, 20 `hdbscan_soft`) sono stati aggiunti `dbcv_per_cluster.csv` (colonne `cluster`, `n`, `dbcv`) e `dbcv_plot.png`, 166 file in tutto. Nient'altro è stato toccato: `config.md` (senza la riga `DBCV:`), `cluster_plot.png`, `matrix.npy`, `metadata.csv`, `membership.npy` sono invariati. Restano senza i due file: le 32 cartelle con 0 o 1 cluster (16 `hdbscan`, 16 `hdbscan_soft`; la pipeline non li scrive in quel caso) e 2 cartelle `hdbscan` del 10-09, escluse come per agglomerative. Totali oggi: `hdbscan` 63 su 81, `hdbscan_soft` 20 su 36.

**Perché**: il codice del DBCV in produzione è del 22-10-26 (commit `a91c300`); tutte le produzioni precedenti non lo hanno mai avuto. Le produzioni non si rigenerano: i file sono stati calcolati da `matrix.npy` e `cluster_label` di ciascuna run con le stesse funzioni della produzione (`run_dbcv` per i numeri, `_write_dbcv_per_cluster` per CSV e figura, titolo da `compose_cluster_plot_title`), da uno script nello scratchpad, senza toccare `src/`. Distanza euclidea, la sola in cui il DBCV è definito. Scrittura in una cartella temporanea dentro la run e spostamento dei due file, mai sopra file esistenti; il calcolo di tutte le run e il confronto con il tuning precedono la prima scrittura (un solo scarto oltre 1e-6 avrebbe fermato tutto).

**Verifica**: il DBCV della run è stato confrontato con la colonna `dbcv` del tuning sulla stessa matrice e stessa combinazione di parametri (`min_cluster_size`, `min_samples`, e `cluster_selection_method` per le soft): 78 run confrontate, differenza massima 8,3e-17. Cinque run `hdbscan` della lesione (01-09: `mcs20_ms10`, `mcs15_ms5`; 03-09: `mcs100_ms20`, `mcs200_ms5`, `mcs75_ms20`) non hanno un tuning con colonna `dbcv` sulla stessa matrice e non sono confrontate.

**Conseguenza ancora vera oggi**: `config.md` di queste 83 run non ha la riga `DBCV: x (euclidean)`, che le produzioni nuove scrivono; il valore della run sta solo nell'app (calcolato dal vivo) e nel `dbcv_plot.png`. L'app non legge i due file.

---

## 27-10-26 — `silhouette_per_cluster.csv` scritto in 90 produzioni agglomerative che non lo avevano

**Cosa è cambiato**: in 90 cartelle sotto `results/{lesion,sdc}/clustering/production/agglomerative/` è stato aggiunto `silhouette_per_cluster.csv` (colonne `cluster`, `n`, `silhouette_mean`, `share_negative`, lo stesso formato delle 26-10). Cartelle per data: lesione 01-09 (3), 03-09 (3), 12-10 (23); sdc 30-09 (7), 14-10 (7), 16-10 (14), 18-10 (2), 19-10 (31). Nient'altro è stato toccato: `config.md`, `silhouette_plot.png`, `cluster_plot.png`, `matrix.npy` e `metadata.csv` sono invariati. Restano senza CSV le 5 cartelle del 10-09 (sdc, `umap`, `s2.2-vol`), escluse su richiesta dell'utente; le 61 del 26-10 lo avevano già. Totale oggi: 151 CSV su 156 cartelle.

**Perché**: il file lo scrive `clustering.py` dal commit `43a0ac4` (21-10-26); le produzioni precedenti non lo hanno mai avuto. Le produzioni non si rigenerano (regola in vigore): il CSV è stato calcolato dalla `matrix.npy` e dalla colonna `cluster_label` di `metadata.csv` di ciascuna run, con le stesse funzioni della produzione (`compute_silhouette_samples`, `silhouette_breakdown`), da uno script temporaneo nello scratchpad, senza toccare `src/`. Scrittura via file temporaneo e rinomina, mai sopra un file esistente.

**Distanza**: quella della run (`metric` dei `Params used` di `config.md`; euclidea dove manca, 6 run del 01-09 e 03-09, il cui nome dice `mk_euclidean`). Scartata la distanza sempre euclidea: coinciderebbe con la figura vecchia ma non con la distanza con cui agglomerative ha formato i cluster. Scelta dell'utente.

**Verifica**: lo stesso script ha ricalcolato le 61 run del 26-10 e confrontato con i loro CSV: differenza massima 2,96e-8. Sulla PCA 19-10 nc12 k3 la media pesata del CSV è 0,382, uguale al valore stampato in `silhouette_plot.png`.

**Conseguenza ancora vera oggi**: per le 31 run con `metric=cosine` (24 del 19-10, 7 del 14-10) il CSV è in distanza coseno, mentre la loro `silhouette_plot.png` precede il commit `43a0ac4` ed è calcolata in euclidea: la media del CSV non coincide con la media scritta in quella figura. Per le altre 59 coincidono. Il `config.md` di queste 90 run non ha le righe degli indici (le hanno solo le 26-10).

---

## 27-10-26 — `config.md` di 16 tuning agglomerative: aggiunta la riga `Evaluations applied`

**Cosa è cambiato**: in 16 `config.md` sotto `results/{lesion,sdc}/clustering/tuning/agglomerative/` (le 16 cartelle con `report.md`: lesione `08-10_s1.4-vol_m_{dice,euclidean}_nc{2,3,10}`, sdc `pca/` 17-10 nc30 e nc42, 18-10 nc12 e nc2, 19-10 nc12_varimax e nc2_varimax, `raw/09-10_s2.4-stream`, `umap/16-10_s2.4-vol_m_euclidean_nc{2,3,10}`) è stata inserita nel `## Summary`, subito dopo `Metrics:`, una riga:

`Evaluations applied: ['k_curves', 'cophenetic_correlation', 'dendrogram_jump', 'linkage_agreement', 'largest_cluster_share', 'dunn_index']`

Nient'altro è cambiato: il blocco JSON e la riga `Metrics:` sono intatti. Le 12 cartelle senza report e le cartelle `hdbscan`/`hdbscan_soft` non sono state toccate.

**Perché**: le 28 `config.md` precedono i campi che `clustering.py` scrive oggi (`tuning_evaluations`, `Evaluations applied`), quindi non dicevano quali valutazioni fossero girate. L'elenco è **dedotto dai log**, non letto dalla run: `logs/evaluate_clustering_tuning/` del 23-10-26, un log per cartella, stesse 6 valutazioni nello stesso ordine in tutte e 16. Scelta dell'utente: riscrittura a mano, scartate "lasciare com'è" (raccomandata) e "rilanciare `evaluate_clustering_tuning` con `overwrite: true`" (circa 48 minuti, non è chiaro se riscrive `config.md`). Non aggiunti `evaluations_file` e `write_report` al JSON: il valore di `evaluations_file` non è nei log e andava indovinato.

**Conseguenza ancora vera oggi**: la riga è la lista delle valutazioni del 23-10-26, non scritta dalla pipeline. La valutazione `dendrograms` non è in elenco perché non è mai girata: i `dendrogram_metric=<metric>.png` di queste cartelle sono quelli dello sweep. In `hdbscan`/`hdbscan_soft` la riga `Metrics:` dei `config.md` esistenti elenca ancora `silhouette`, `calinski_harabasz` e `davies_bouldin`, che non sono più colonne del CSV (il codice oggi scrive `noise_fraction`, `n_clusters_found`, e per `hdbscan_soft` anche `membership_mean`, `persistence_mean`).

---

## 16-10-26 — `lesion_matrix/07-10_s1.4-vol` e `sdc_matrix/07-10_s2.4-vol`: righe riordinate alfabeticamente per dataset

**Cosa è cambiato**: in `matrix.npy` e `metadata.csv` di entrambe le matrici le 5845 righe sono passate dall'ordine dei dataset del config (WashU, PASPORT, PSP, UKLFR, UCL-UK, WAKEUP, NEMESIS_T0, SFB936) all'ordine alfabetico per nome del dataset (UCL-UK, SFB936, WAKEUP, UKLFR, NEMESIS_T0, PASPORT, PSP, WashU), poi `subject_id`. Nessun valore è cambiato: è una permutazione delle righe (la colonna `lesion_volume_voxels` del lesion `metadata.csv` si è mossa con la sua riga). `non_constant_mask.npy`, `manifest.json` e `config.md` sono invariati.

**Perché**: richiesta dell'utente, un solo criterio per le due pipeline. `build_sdc_matrix` ordinava già per (dataset, `subject_id`), `build_lesion_matrix` seguiva l'ordine di `datasets` nel config; il codice lesionale è stato allineato lo stesso giorno (`project_changelog.md` 16-10-26). Così anche la nuova `16-10_s2.4-vol`, scritta in ordine alfabetico dal builder, ha le stesse righe nello stesso ordine di entrambe. Sostituisce il riordino a mano del 07-10 (voce sotto), che portava la matrice SDC all'ordine del config.

**Verifica**: permutazione completa e ogni riga nuova bit a bit uguale alla riga vecchia da cui proviene (0 differenze su 5845, per entrambe), fatta prima di sostituire i file; poi 26 righe per matrice (3 soggetti per dataset, prima e ultima riga incluse) ricalcolate dal `.nii.gz` grezzo con codice indipendente dalla pipeline (`resample_to_img` nearest, per la lesione binarizzazione e azzeramento fuori dal brain) e confrontate con la riga del file finale: 0 differenze. Copie originali (`*.orig`) cancellate solo dopo.

**Conseguenza ancora vera oggi**: i risultati già prodotti sul 07-10 (tuning, produzioni, clustering) hanno ancora le righe nell'ordine del config: ognuno ha il suo `metadata.csv`, quindi restano coerenti con sé stessi e i confronti tra run allineano per `subject_id`. Ma non sono più riproducibili bit a bit dalla sorgente: UMAP non è invariante alla permutazione delle righe, quindi lo stesso `random_state` su matrice riordinata dà un embedding diverso. Un clustering con `viz_embedding_path` che mescola un embedding vecchio e una matrice nuova viene fermato dal controllo sull'ordine dei `metadata.csv`.

---

## 14-10-26 — `derivatives/<sito>/<dataset>/sdc/` rinominata `bcbtoolkit/`

**Cosa è cambiato**: in ognuno degli 8 dataset la cartella `sdc/` è stata rinominata `bcbtoolkit/` sul posto (`mv`, nessun file toccato). Sottocartelle soggetto contate dopo la rinomina: UCL-UK 4119, UKE/SFB936 56, UKE/WAKEUP 451, UKLFR 705, UNIPD/NEMESIS_T0 76, UNIPD/PASPORT 83, UNIPD/PSP 168, UNIPD/WashU 195 (5853, uguali a prima). Aggiornati anche:

- `data/clinical_connectome/file_types_cache.json`: chiave `sdc` → `bcbtoolkit` in `file_types_by_type` (1 chiave) e in `file_types_by_subject` (5853 chiavi `sdc|...`), valori invariati.
- `data/clinical_connectome/derivatives/README.md`: il percorso sorgente di `manual_masks/`.
- `assets/metadata/sdc_metadata.config.json` (versionato): `disconnectome_glob` dello snapshot di config con cui fu scritto `sdc_metadata.csv`. Il csv non è stato ricalcolato.

**Perché**: la cartella contiene l'intero output di BCBToolKit (disconnettoma e lesione, `LF-*` per atlante, `lesion-map`, mapstats), non solo l'SDC. `sdc` era un nome locale: EBRAIN non lo usa. Serve perché `build_lesion_matrix` possa leggere i `LF-lesion` senza che la lesione stia sotto un nome SDC. Scartato: spostare i `LF-lesion` in `manual_masks/` (mescola un prodotto calcolato con le maschere e il glob che le trova); lasciare `sdc/`.

**Conseguenza ancora vera oggi**: ogni nuova copia dei dati deve usare `bcbtoolkit/`. Il nome è in `BCBTOOLKIT_DIR` (`src/features/sdc.py`), nella chiave di `PRESENCE_COLUMN_BY_DATA_TYPE` (`src/pipeline/populate_metadata.py`), in `SDC_DISCONNECTOME_GLOB` (`src/analysis/embedding_app/anatomy.py`) e in `disconnectome_glob` dei config. La colonna `has_sdc` del registro non cambia: indica la modalità SDC, non la cartella. Le voci precedenti di questo file e i report in `docs/debugging/` parlano di `sdc/`: era il nome di allora.

---

## 07-10-26 — `sdc_matrix/07-10_s2.4-vol`: righe riordinate come `lesion_matrix/07-10_s1.4-vol`

**Cosa è cambiato**: in `matrix.npy` e `metadata.csv` le 5845 righe sono state riordinate dall'ordine alfabetico per dataset (quello con cui la pipeline le aveva scritte) all'ordine di `lesion_matrix/07-10_s1.4-vol/metadata.csv` (dataset nell'ordine del config: WashU, PASPORT, PSP, UKLFR, UCL-UK, WAKEUP, NEMESIS_T0, SFB936). Nessun valore è cambiato: è una permutazione delle righe. `non_constant_mask.npy`, `manifest.json` e `config.md` sono invariati (colonne e forma non toccate).

**Perché**: richiesta dell'utente, così le due matrici sono allineate per posizione oltre che per `subject_id` (stesso insieme di 5845 soggetti, stesso dataset per ciascuno).

**Verifica prima della sostituzione**: permutazione completa (ogni riga vecchia usata una volta); le 5845 righe nuove sono identiche bit a bit alla riga vecchia da cui provengono (0 differenze); 16 soggetti, tra cui prima e ultima riga, ricalcolati dal loro `.nii.gz` con `_load_disconnectome_voxels` e confrontati con la riga corrispondente nell'ordine nuovo (16/16). Il file è stato scritto a parte e sostituito solo dopo.

**Verifica dopo la sostituzione**: tutte e 5845 le righe ricalcolate dal `.nii.gz` del proprio soggetto (un file per soggetto, nome che contiene il `subject_id`) e confrontate bit a bit con la riga del file finale: 0 righe non corrispondenti (354 s). Fatta a partire dal `metadata.csv` finale, quindi indipendente dalla permutazione usata per scrivere il file. Solo dopo è stata cancellata la copia temporanea in ordine alfabetico.

**Conseguenza ancora vera oggi**: superata il 16-10-26 (voce sopra): l'ordine delle due matrici è ora alfabetico per dataset, quello che i builder producono da soli. L'ordine del config descritto qui non esiste più.

---

## 28-09-26 — Rimossa `data/derived/enrich_lesion_metadata/`

Cancellata la directory (conteneva solo un `runs.csv` residuo, 2.9KB, mtime 02-09-26) —
leftover della pipeline `enrich_lesion_metadata.py`, cancellata durante il ridisegno
metadati del 06-09-26 e sostituita da `src/pipeline/enrich_metadata.py`, che scrive
direttamente in `assets/metadata/participants.csv` senza produrre un proprio artefatto
sotto `data/derived/`.

Verificato con `grep -rn` prima della cancellazione: nessun codice/config attivo
referenziava più quel path — solo menzioni narrative in `docs/debugging/`,
`lessons_learned.md` e `stato_progetto.md`. Rimozione confermata dall'utente.

## 23-09-26 — `UNIPD/NEMESIS_T0`: subject id grezzi rinominati in forma canonica

**Perché era necessario**: i subject id grezzi di NEMESIS_T0 (`sub-p001`, `sub-c002`, ...)
non rispettano la convenzione `sub-<ST|PD|GM><SITE>[HC]<NUM>` che `group_of()`
(`src/retrieval/dataset.py`) richiede — ogni modulo che scopre i soggetti scandendo
`sub-*` direttamente (`src/features/lesion.py`, `sdc.py`, `subject_discovery.py`)
chiama `group_of()` senza condizioni e solleverebbe `ValueError` sul primo soggetto.

**Cosa è cambiato**: script one-off `scripts/rename_nemesis_t0_subjects.py` (dry-run di
default, `--execute` per scrivere). Copre l'unione dei `sub-p*` visti nel tsv grezzo e su
disco (82 id distinti: 72 in comune, 6 solo nel tsv, 4 solo su disco — non un semplice
sottoinsieme). Numerazione: `UNIPD` è un contatore unico condiviso da WashU/PSP/PASPORT
(0001-0585 già occupati, verificato su disco senza buchi riusati), quindi i nuovi id
continuano da 0586. Assegnati in ordine crescente del numero originale.

Eseguito su:
- **76 cartelle** rinominate sia sotto `manual_masks/` che sotto `sdc/` (`sub-p001`→
  `sub-STUNIPD0586` ... `sub-p090`→`sub-STUNIPD0666`, più `sub-p123`→`sub-STUNIPD0667`),
  ogni file dentro ciascuna cartella rinominato di conseguenza (prefisso del nome file).
- **`data/clinical_connectome/metadata_tsv/participants_NEMESIS_T0.tsv`**: colonna
  `participant_id` riscritta in forma canonica per le 82 righe `sub-p*`; l'id grezzo
  originale preservato in una nuova colonna `participant_id_dmp` (stesso schema già usato
  dal tsv di `UKE_SFB`). Aggiunte anche **4 righe mancanti** (`sub-p010`, `sub-p047`,
  `sub-p076`, `sub-p077`) per soggetti che avevano la scansione su disco ma nessuna riga
  clinica nel tsv originale — età/sesso/gruppo lasciati vuoti, nessun dato clinico noto
  per loro. Le **6 righe rimaste solo-tsv** (`sub-p032`, `sub-p033`, `sub-p053`,
  `sub-p081`, `sub-p084`, `sub-p123`) non hanno scansione sul disco: nessuna azione
  possibile, restano escluse dal join di `populate_metadata.py` (comportamento atteso,
  riportato nel report del run, non un errore).
- I 22 `sub-c*` (controlli sani) **non toccati**: nessun dato su disco per loro (0
  cartelle), e comunque fuori scope per `group_filter: ["ST"]` come ogni altro HC del
  progetto (`docs/dev/metadata.md`).

**Conseguenza ancora vera oggi**: `config/registry/metadata_sources.json` ha già la voce
`UNIPD/NEMESIS_T0`, ma il dataset **non è ancora** in `datasets` di
`config/pipelines/populate_metadata.json` — `assets/metadata/participants.csv` non
riflette ancora questi 76 (o 72, al netto dei 6 solo-tsv) soggetti finché quella run non
viene lanciata.

---

## 23-09-26 — Aggiunti 2 dataset nuovi, sostituite le lesion mask di 6 dataset esistenti

**2 dataset nuovi aggiunti a `data/clinical_connectome/derivatives/`**: UKE/SFB936_ses01
(56 soggetti) e UNIPD/NEMESIS_T0 (76 soggetti), copiati da `sdc_download/lesion/` —
`manual_masks/<sub>/anat/` (solo lesion mask, `res-1` rimosso) + `sdc/<sub>/` (disconnectome
map con `res-1` mantenuto, 2 mapstats.tsv, 30 CSV parcellati per atlante). Output SDC già
completo per entrambi, nessun run di `compute_sdc.py` necessario. **Non ancora in-scope**:
assenti da `docs/guides/datasets.md`, `config/registry/`, `assets/metadata/participants.csv`
— onboarding non fatto, `participants.tsv` reali non ancora recuperati (a carico dell'utente).

**Lesion mask sostituite per 6 dataset esistenti** (`manual_masks/*/anat/`, vecchi file
eliminati prima della sostituzione, sorgente una copia `rsync` fresca in `sdc_download/`,
`res-1` rimosso): UCL-UK/UCLStrokeData 4119→4119, UKE/WAKEUP_acute 451→451,
UKLFR/stroke_UKLFR 697→705, UNIPD/PASPORT 83→83, UNIPD/PSP 168→168, UNIPD/WashU 202→195.

UKLFR non è un semplice swap 1:1: persi 24 soggetti con maschera manuale ma senza dato SDC,
guadagnati 32 nuovi. WashU perde 7 soggetti senza sostituto disponibile (accettato
esplicitamente dall'utente) — verificato che nessuno dei 7 è HC (nessun soggetto HC esiste
per WashU in `manual_masks/`, `features/`, `sdc/` né in `participants.csv`, solo ST).

`sdc_download/lesion/`: i 2 dataset nuovi mantengono la propria copia (sorgente di verità,
non spostata); i 6 dataset solo-maschera sono stati spostati (`mv`), quindi `sdc_download`
non ne contiene più i file — dettagli di rinomina in `sdc_download/lesion/README.md`.

Conseguenza ancora vera oggi: `assets/metadata/participants.csv` non riflette ancora questi
cambiamenti (né i 2 dataset nuovi, né il delta di UKLFR/WashU) — va rigenerato. Risoluzione
voxel di UKLFR/WashU passata da 1.5mm/2.0mm nativo a 1mm (stessa fonte dell'SDC) — ha esposto
una fragilità di `reference_template_path` risolta lo stesso giorno, vedi `project_changelog.md`
23-09-26.

**Superata il 29-10-26**: `participants.csv` oggi ha tutti e 8 i dataset (`populate_metadata.json` li elenca). **Indagine su due soggetti** (sola lettura): (1) `sub-STUKE0146` ha oggi nella maschera 16 voxel a 1 mm, come il 06-09: il `lesion_volume_voxels_1mm = 8` di `lesion_metadata.csv` è il conteggio dopo l'azzeramento dei voxel fuori dal brain (`out_of_brain_fraction_1mm = 0,5`), non un cambio dei dati; `sub-STUKE0201` resta a 3. (2) `sub-STUKLFR0671` ha oggi una maschera **vuota** (0 voxel, `float64`, file del 05-08). Le matrici costruite prima del 23-09 (`21-07_s1.1-vol`, `25-08_s1.2-vol`, `06-09_s1.3-vol`) hanno per lui una riga con 23.960 voxel a 2 mm, quindi la maschera è cambiata con la sostituzione del 23-09. Anche gli output di BCBToolKit nella cartella `bcbtoolkit/` sono nulli: i CSV `LF-lesion` (26-08) hanno sovrapposizione 0 e la mappa di disconnessione (03-09) ha 0 voxel non nulli. BCBToolKit ha quindi lavorato su una maschera vuota, non su una lesione grande.
**Chiusa il 29-10-26** (decisione dell'utente): la maschera vuota di `sub-STUKLFR0671` è **corretta**. La vecchia copia locale da 23.960 voxel a 2 mm (56.785 a 1 mm) non era la maschera giusta; il soggetto ha lesione vuota ed è escluso (`empty_mask`, `scope=all`). L'utente non ha il file originale del server e non indica la provenienza della vecchia copia: non è stata ricostruita.

---

## 07-09-26 — `sub-STUKLFR0671`: mappa di disconnessione vuota nonostante una lesione grande

Emerso costruendo `sdc_matrix` s2.2-vol (prima run voxel-wise): il soggetto entra in matrice come riga interamente nulla.

Non è un artefatto del ricampionamento. Il file sorgente
`UKLFR/stroke_UKLFR/sdc/sub-STUKLFR0671/..._res-1_desc-disconnectome.nii.gz` ha
**0 voxel non nulli su 7.221.032**, mentre la sua maschera di lesione ne ha
**56.785**. Una lesione di quelle dimensioni che produce zero disconnessione non è
plausibile: è output degenere di BCBToolKit, non una proprietà del soggetto.

È l'unico caso tra i 1570 soggetti ammessi. Non è stato ricalcolato (`compute_sdc.py`
gira solo sul cluster) né rimosso dalla matrice.

**Riletta il 29-10-26**: la causa più probabile non è un output degenere su una lesione grande. I CSV `LF-lesion` di BCBToolKit (26-08) per questo soggetto hanno sovrapposizione 0, e la maschera attuale (copiata il 23-09 dalla fonte) è vuota: BCBToolKit ha processato una maschera vuota. La maschera con 56.785 voxel era la vecchia copia locale, che sembra diversa da quella usata per l'SDC (poi confermato dall'utente il 29-10-26: la maschera vuota è quella corretta). `sub-STUKLFR0671` è in `excluded_subjects.csv` (`empty_mask`).

Nota: lo stesso soggetto compare in `docs/dev/sdc_matrix.md` come l'esempio verificato
di chi *ha* una maschera registrata pur mancando dal `manual_masks/` locale — quel
fatto resta vero e non c'entra con questo. Qui il problema è a valle: la maschera c'è,
l'SDC è stato calcolato, ma il risultato è vuoto.

Conseguenza ancora vera oggi: chi usa `07-09_s2.2-vol` deve escluderlo, o accettare una
riga a zero indistinguibile da "nessuna disconnessione" — con metriche di distanza è un
outlier garantito.

---

## 06-09-26 — `lesion_matrix` s1.3-vol: 2 soggetti UKE entrano come righe tutte-zero

`build_lesion_matrix.py` (run `06-09_s1.3-vol`, 5720 soggetti) ha ammesso in matrice
`sub-STUKE0146` e `sub-STUKE0201` con `lesion_volume_voxels = 0`: righe interamente
nulle, indistinguibili da "nessuna lesione" pur essendo pazienti stroke.

Causa: sono le due lesioni piu' piccole della coorte. Le maschere raw sono valide
(1mm isotropo, 182x218x182, valori binari 0/1) ma contengono rispettivamente **16 e
3 voxel**. Il template di riferimento e' a 2mm (91x109x91, la maschera WashU
`sub-STUNIPD0001`) e `resample_interpolation` e' `nearest`, che campiona invece di
mediare: una lesione da 3 voxel a 1mm non sopravvive al ricampionamento se non cade
su un punto della griglia 2mm. Nessun altro dataset era finora sceso sotto questa
soglia, quindi il caso non si era mai presentato: s1.2-vol (5269 soggetti, gli stessi
dataset meno UKE) ha 0 righe nulle, con volume minimo 1 voxel (`sub-STUNIPD0208`) —
verificato ricalcolando le somme di riga da `25-08_s1.2-vol/matrix.npy`, che non ha
la colonna `lesion_volume_voxels` (aggiunta dopo quella run).

Non e' un bug di codice: e' perdita di segnale legittima del downsampling su lesioni
sotto-risoluzione. **Non e' stata presa alcuna decisione** su come trattarli — i due
soggetti restano in `06-09_s1.3-vol/matrix.npy`. Alternative sul tavolo, nessuna
adottata: escluderli in fase di build (il builder SDC ha gia' un guard-rail
equivalente, esclude esplicitamente chi non ha lesion mask registrata invece di
inserire una riga a zero; quello lesionale no), oppure tenerli e filtrarli a valle.

Conseguenza ancora vera oggi: chiunque usi `06-09_s1.3-vol` per dim reduction o
clustering ha 2 righe identicamente nulle nella matrice. Con metriche binarie
(jaccard/dice) una riga tutta-zero ha distanza indefinita o massima da chiunque —
vanno gestite prima, non dopo aver visto un outlier strano nell'embedding.

---

## 05-09-26 — `populate_metadata.py`: conteggi FC sbagliati per cartella potata

Prima run di `scripts/populate_metadata.py`: ha scritto `has_features=False` per 192 soggetti WashU che le FC ce l'hanno, perché `UNIPD/WashU/features/` era potata al campione di 10 e una scansione del disco non vede dentro un `.tar.gz`.

Corretto decomprimendo l'archivio, rilanciando con `overwrite=true` (`has_features` da 10 → 169 ST) e ricomprimendo. Da qui la scelta di **non** far leggere il manifest alla pipeline (la potatura è una misura temporanea di spazio locale, non una proprietà del progetto): la correzione resta manuale e documentata in `docs/dev/metadata.md`.

**Superata il 29-10-26**: con `features/` di nuovo potata, `participants.csv` ha `has_features=True` per 10 soggetti WashU su 195 (il resync del 23-09 con `overwrite: true` ha letto il disco potato). Decisione dell'utente: la correzione manuale non si rifà. `has_features` descrive il disco locale; la popolazione reale si legge dal manifest `<nome>_archive_subjects.tsv` della cartella potata, perché i dati sono archiviati per spazio finché non servono.

Introdotti nello stesso giorno i manifest `<nome>_archive_subjects.tsv` in ogni cartella potata, e corretto il comando di ripristino nei `README_ARCHIVE.md` (diceva `tar -xzf <archivio> -C .` ma l'archivio sta un livello sopra la cartella, quindi non lo trovava mai).

## 04-09-26 — `participants.tsv` accorpati in `metadata_tsv/`

I 6 `participants.tsv` sono stati spostati da `derivatives/<centro>/<coorte>/participants.tsv` a `data/clinical_connectome/metadata_tsv/participants_<SITO>.tsv`. La corrispondenza nome-file ↔ dataset non è più derivabile meccanicamente (`participants_UCL.tsv` ↔ `UCL-UK/UCLStrokeData`), da cui il registry esplicito `config/registry/metadata_sources.json`.

## 04-09-26 — SDC: appiattito il livello `dwi/`

Fino a questa data la copia locale annidava ogni file sotto `sdc/{subject_id}/dwi/{subject_id}_...` — una cartella `dwi/` fabbricata dal layout locale, non presente alla sorgente. Tutti i file dei 1602 soggetti nei 5 dataset sono stati spostati su di un livello (`sdc/{subject_id}/{subject_id}_...`) e le `dwi/` vuote rimosse.

## 03-09-26 — Onboarding di `UKE/WAKEUP_acute`

**SDC**: primo trasferimento via `rsync` risultato incompleto/corrotto — 221/451 soggetti con tutti i file a 0 byte. Scoperto e bloccato prima di toccare `derivatives/` grazie a un controllo di stabilità della dimensione nel tempo, **non** da un errore esplicito (rsync non ha segnalato nulla). Rifatto con `scp -r` diretto da `/data/corbetta/Clinical_connectome/features/Clinical_connectome_stroke/UKE/WAKEUP_acute/lesion`, verificato al 100% (451 × 35 file, nessuno a 0 byte, dimensione stabile su ricontrolli ripetuti) prima di sostituire la cartella.

**Maschere di lesione**: UKE non ha un oggetto `lesion` sul server, quindi nessun retrieval è possibile. Il `lesion-map` di ogni soggetto (la lesione ricampionata che BCBToolKit usa come input) è stato copiato sotto `manual_masks/{subject_id}/anat/` e **rinominato** togliendo `res-1` — necessario perché `Dataset.resolve()` cerca il template esatto, non basta che il file esista. L'originale è stato poi rimosso da `sdc/{subject_id}/` per non duplicarlo. Non riproducibile rilanciando una pipeline: solo ripetendo gli stessi passi a mano.

**SDC per gli altri 4 dataset**: aggiunti i `disconnectome-map` (.nii.gz voxel-wise) che mancavano; fino a quel momento la copia locale conteneva solo i CSV parcellati (`disconnectome-LF`/`lesion-LF`).

## 01-09-26 — `manual_masks/` ripristinate per intero

Le 5 cartelle `manual_masks/` (WashU, PSP, PASPORT, UKLFR, UCL-UK), potate il 26/08, sono state riportate al set completo. Restano potate solo `UNIPD/WashU/features/` e `data/derived/features/masked_fc/`.

## 26-08-26 — Prima potatura delle copie locali

`scripts/archive_local_raw_data.py` ha ridotto a 10 soggetti campione le 5 `manual_masks/`, `UNIPD/WashU/features/` e `data/derived/features/masked_fc/`, comprimendo il resto in `.tar.gz` verificati accanto a ciascuna cartella.
