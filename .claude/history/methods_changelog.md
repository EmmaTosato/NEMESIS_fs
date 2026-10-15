# Changelog dei metodi

Decisioni su **come analizziamo**: proxy per variabili mancanti, feature calcolate, soglie, metodi adottati o abbandonati — con le alternative scartate e il perché.

**Cosa NON va qui**: i risultati di un esperimento (`docs/experiments/`), i parametri di una singola run (`runs.csv`), il funzionamento corrente di una pipeline (`docs/`, sempre al presente).

Voci in ordine cronologico inverso.

---

## 16-10-26 — PCA nella pipeline: una voce `pca` con le scelte come parametri, `pca_varimax` eliminato

**Cosa è cambiato**: `pca` in `REDUCTION_METHODS` ha ora `solver` (`blocks`: `covariance_pca.py`, legge la matrice a blocchi; `sklearn`: `sklearn.decomposition.PCA` in memoria), `standardize` (correlazione invece di covarianza), `dual` (matrice soggetti × soggetti o covarianza tra variabili, esplicito), `rotation` (`none` o una rotazione ortogonale di `factor_analyzer`, `rotation_max_iter` con una rotazione) e `n_components` oppure `variance_share` (esattamente uno). `pca_varimax` è eliminato (codice, tuning, registro, test, doc): è `pca` con `rotation: "varimax"`. Con `blocks` la matrice resta su disco (`np.memmap`); il tuning fitta la decomposizione una volta per griglia su `n_components`/`variance_share`/`rotation`. La produzione registra in `Params used` il numero di componenti effettivo e salva lo spettro in `eigenvalues.npy`. Il plot di una `pca` non ruotata prende le prime `viz_n_components` componenti.

**Perché**: `sklearn.PCA` non regge il disconnettoma voxelwise (5845 × 291.345, 6,8 GB: circa 25,7 GB di RAM). Il percorso a blocchi, con i parametri del registro (duale, 150 componenti), ci mette 179 s e spiega il 96,0% della varianza. Le matrici parcellate hanno meno variabili che soggetti e vogliono il percorso sulla covarianza tra variabili: su `s2.4-stream` (5831 × 87) è meno di 1 s contro circa 24 s del duale, con gli stessi risultati (verificato contro sklearn su `s2.1` e `s2.4-stream`, per tutte le combinazioni di `standardize` e `dual`). È il prerequisito per clusterizzare sulle componenti.

**Alternative scartate**: una voce di registro per variante (le combinazioni raddoppiano a ogni scelta nuova); `dual` o `solver` in modalità "auto" (un fallback: la scelta resta nel config, la regola — duale se le variabili superano i soggetti — sta nella guida); un `null` come "assente" (finisce nei parametri registrati dei run e viene riletto come valore: la chiave va tolta); le rotazioni oblique (i punteggi per regressione assumono componenti non correlate, servirebbe un'altra formula); salvare l'intero modello per run (la matrice dei vettori pesa circa 273 MB contro i 7 MB dell'embedding: salvo solo lo spettro, e la curva basta a scegliere `variance_share`); lasciare sklearn solo nei test (tenuto come `solver`, resta anche riferimento dei test).

**Visualizzazione**: la regola "mai tagliare le prime colonne" (`lessons_learned.md` #16) ha come unica eccezione la PCA non ruotata, le cui colonne sono ordinate per varianza. Una PCA ruotata non ha ordine: tagliarla o rifittarla a un'altra dimensione è rifiutato. Prima di questa voce una `pca` con più componenti di `viz_n_components` (come le 150 del registro) si fermava al plot.

## 15-10-26 — clustering_evaluation 3.1: la probabilità di HDBSCAN descrive la posizione nel cluster; tolti p10 e confronto delle silhouette

**Cosa è cambiato** (`membership_confidence`, sezione 3.1): `clusters` ha solo `n`, `probability_mean` e `share_below_threshold`; via `probability_p10`, `silhouette_all` e `silhouette_confident`. Via anche il rifiuto delle run non euclidee e il vincolo di almeno 2 cluster, che esistevano solo per la silhouette; resta il rifit che deve riprodurre le etichette, e una run tutta rumore solleva. La sezione si chiama «Posizione nel cluster», non più «Confidenza di appartenenza».

**Perché**: l'utente voleva la probabilità che un soggetto appartenga al suo cluster, e `probabilities_` non è quello: è un lambda normalizzato dentro il cluster, cioè quanto il soggetto è vicino al nucleo (1 = cuore, vicino a 0 = margine, per poco non rumore). Non dice se un altro cluster starebbe meglio. Il nome «confidenza di appartenenza» e il confronto delle due silhouette lo facevano leggere come un'appartenenza vera. Scelta dell'utente tra: riscrivere solo il testo, semplificare (scelto), appartenenza vera ai cluster.

**Alternativa tenuta aperta (C)**: l'appartenenza a tutti i cluster esiste come `all_points_membership_vectors` del pacchetto `hdbscan` standalone, che non è in `environment.yml` (verificato: `import hdbscan` fallisce nell'ambiente `nemesis`) e richiede un rifit; l'utente ha chiesto di provarla. Prototipo (scratchpad, non in `src/`; `pip install hdbscan` 0.8.44 nell'ambiente `nemesis`, `environment.yml` non toccato) su lesione dice nc2 `12-10_s1.4-vol_m_dice_nc2_mcs100_ms20` (5845 soggetti, 8 cluster, 47 rumore): `hdbscan.HDBSCAN(**params, prediction_data=True)` dà la stessa partizione di sklearn a meno di una permutazione degli id dei cluster e di **1 soggetto su 5845** (etichetta diversa), quindi il criterio «il rifit deve riprodurre le etichette esattamente» non vale così com'è; `all_points_membership_vectors` dà una matrice soggetti x cluster le cui righe sommano da 0,135 a 1 (il resto è rumore). Probabilità media di stare nel proprio cluster 0,78-0,99 per cluster; 190 soggetti su 5798 non-rumore sotto 0,5.

**Conseguenza ancora vera**: il nome della funzione resta `membership_confidence` e la voce di registro `membership_confidence`, anche se la sezione ha un altro titolo.

## 15-10-26 — Nuovo metodo `hdbscan_soft` (pacchetto `hdbscan`) con tuning dedicato, non confrontabile con `hdbscan` (sklearn)

**Cosa è stato fatto**: `hdbscan_soft` in `CLUSTERING_METHODS` (`hdbscan_soft_fit` restituisce lo stimatore con `prediction_data=True`, `hdbscan_soft_cluster` solo le etichette), blocco `hdbscan_soft` in `params_clustering.json`, `hdbscan` in `environment.yml`. Griglia dedicata, 56 combinazioni: `min_cluster_size` {10, 15, 20, 30, 50, 75, 100} x `min_samples` {1, 5, 10, 20} x `cluster_selection_method` {eom, leaf}, con `approx_min_span_tree=False` fisso; `alpha` e `allow_single_cluster` ai default del pacchetto (la documentazione sconsiglia il primo; il secondo serve per dati omogenei). Tre colonne nuove in `tuning_results.csv` dal pacchetto: `membership_mean`, `membership_share_below_half` (soglia fissa 0,5), `persistence_mean`; NaN se la combinazione non trova cluster. Con tre parametri variati il pipeline scrive una heatmap per valore di `cluster_selection_method` (`tuning_plot_cluster_selection_method=<valore>.png`). Dieci tuning sulle stesse matrici dell'08-10 (lesione `s1.4-vol` UMAP dice/euclidean nc2/nc3/nc10) e del 09-10 (sdc `s2.4-vol` UMAP euclidean nc2/nc3/nc10, `s2.4-stream` raw), output in `results/<lesion|sdc>/clustering/tuning/hdbscan_soft/`; 30-55 secondi ciascuno sugli embedding, 3 minuti la raw. Solo tuning: la produzione e la matrice soft salvata non ci sono.

**Perché un nome e una griglia propri**: con gli stessi numeri di `hdbscan` le due implementazioni **non** danno la stessa partizione. ARI per combinazione contro le run sklearn: mediana 0,998 (lesione dice nc2), 0,81 (lesione euclidean nc2), 0,67 (lesione euclidean nc3), 0,86-0,98 (sdc); minimi tra 0,000 e 0,67; fino a 19 combinazioni su 28 con ARI < 0,8. Cause: (1) la convenzione di `min_samples` (il pacchetto con `min_samples - 1` riproduce sklearn, ARI 0,95-1,00 per `min_samples` >= 5; per 1 serve 1, perché 0 è rifiutato; il docstring della classe dice "include il punto stesso" ma il comportamento misurato corrisponde alla pagina *How HDBSCAN Works*, k-esimo vicino); (2) `approx_min_span_tree=True` di default, che da solo sposta poco (ARI 0,988 contro 1,000 a mcs=10, ms=1, dice nc2). Alternativa scartata dall'utente: tradurre `min_samples` dentro `hdbscan_soft` per far coincidere le partizioni con sklearn. L'utente non vuole confrontare run vecchie e nuove: il tuning di `hdbscan_soft` è fatto per il pacchetto e si legge da solo.

**Run precedenti cancellate**: un primo giro di 10 tuning con la griglia di `hdbscan` (28 combinazioni, MST approssimato, senza colonne nuove) è stato cancellato e rifatto con la griglia dedicata, su richiesta.

**Produzione, 17 run** (15-10 e 16-10, la mezzanotte è passata a metà lancio: l'ultima ha la data 16-10), in `results/<lesion|sdc>/clustering/production/hdbscan_soft/umap/`. Scelta dal tuning dedicato con i criteri "usabile" del 12-10 (`results/reports/cluster_tuning_notebooks/README.md`: 3-30 cluster, rumore <= 25%, cluster più grande <= 60%), una combinazione per famiglia di numero di cluster (pochi e netti, intermedi, frammentati); la stabilità per sottocampionamento ("buono") non è stata applicata. Sono "usabili", non "buoni".

| Matrice | Combinazioni `mcs/ms/selezione` |
|---|---|
| lesione dice nc2 | 75/5/eom (8 cluster), 20/20/eom (11), 50/5/eom (21) |
| lesione dice nc10 | 100/1/eom (8), 50/10/eom (10), 30/10/eom (21) |
| lesione euclidean nc2 | 100/20/eom (12), 75/5/eom (15), 75/1/eom (19) |
| lesione euclidean nc10 | 100/20/eom (12), 100/10/eom (15), 50/20/eom (19) |
| sdc `s2.4-vol` nc2 | 75/10/eom (16), 50/10/eom (21), 100/5/leaf (24, rumore 24,2%) |
| sdc `s2.4-vol` nc10 | 75/5/eom (8), 100/20/eom (7) |

Fuori dalla produzione: lesione e sdc nc3 (1 combinazione usabile ciascuna) e `s2.4-stream` raw (0 usabili). L'utente ha aggiunto lesione euclidean nc2/nc10 e sdc nc2 a una lista corta che le escludeva (appartenenza più bassa: `membership_mean` 0,54-0,73 sulla lesione euclidean, quasi metà dei soggetti sotto 0,5 su nc10). Ogni run riproduce il suo candidato del tuning (cluster, rumore e `membership_mean` coincidono, verificato sulle 17).

**Cosa salva la produzione di `hdbscan_soft`**: `membership.npy` (soggetti x cluster, array extra di `save_matrix`) e la colonna `membership_own` in `metadata.csv` (NaN per il rumore: non ha un cluster proprio, e uno 0 si leggerebbe come improbabilità misurata); i marker di `cluster_plot.png` seguono `membership_own`. Una run senza cluster salva una matrice (n, 0), non fallisce: tutto rumore è un esito legittimo, come per `hdbscan`. I parametri di ogni run sono stati messi nel `params` del blocco `hdbscan_soft` di `params_clustering.json` uno alla volta e il file è stato ripristinato (base 100/10/eom) a fine lancio.

**Lettura**: sezione 3.2 di `clustering_evaluation.ipynb` (`soft_membership_summary`, registro `soft_membership`); `hdbscan_soft` entra anche nella sezione 3 (rumore e numero di cluster). La 3.1 resta solo per `hdbscan` (sklearn).

**Documentazione**: `knowledge/dim_reduction_clustering/hdbscan_package.md` (algoritmo, parametri, soft clustering, differenze da sklearn), sezione "HDBSCAN soft" in `docs/guides/clustering.md` e `docs/dev/models.md`.

**Conseguenza ancora vera**: DBCV (`relative_validity_` del pacchetto) resta escluso; non è stato aggiunto alle colonne. I vettori soft hanno righe che non sommano a 1 (la parte mancante è la probabilità di essere rumore).

## 15-10-26 — clustering_evaluation: tolto il confronto con dati senza cluster (2.2); silhouette di adp fusa nella purezza dei vicini

**Cosa è cambiato**: il nullo (ex 2.2) è stato tolto dal notebook e da `src/`: `null_reference_silhouette`, `NullReference`, `_null_sample`, `NULL_KINDS`, la voce `null_reference` di `EVALUATIONS` e i 6 test relativi (`tests/unit/test_clustering_evaluation.py`). La silhouette sulla distanza dice di adp (ex 2.4) non è più una sezione: è nella 2.2 (ex 2.3, purezza dei vicini), stessa tabella, con le colonne `silhouette`, `silhouette_macro`, `silhouette_min` e `pairs_at_distance_1`, e due colonne per cluster (`silhouette_mean`, `share_negative`). Via anche la voce `adp_silhouette` di `EVALUATIONS` e l'helper `adp_knn_purity` del notebook (non più usato). Suite: 1454 passed, 17 skipped.

**Perché il nullo**: la silhouette resta senza riferimento di scala, e va bene così. Il nullo costava 2 x `N_NULL` rifit per run e non aveva un indicatore di incertezza sul margine; i due nulli davano letture diverse (ward, 20 cluster, 2 componenti: margine 0,195 gaussiano contro 0,112 permutato); con hdbscan fino a 24 fit su 30 erano degeneri e fuori dalla media (voce del 15-10-26 sul p empirico); non copriva adp né evidence_accumulation. Scelta dell'utente: sacrificarlo. Il testo della sezione 2 dice ora che nessuno dei quattro indici ha un riferimento e che anche una nuvola senza cluster ha silhouette positiva (ward, 3 cluster, gaussiana a 2 componenti: circa 0,4).

**Perché la fusione**: l'informazione della silhouette di adp (separazione globale dei cluster, che la purezza non vede: su sdc 0,07 contro purezza 0,97) resta, ma non occupa una sezione a sé; `pairs_at_distance_1` accanto ricorda quando ignorarla (lesioni: 84%). Alternative scartate: togliere la silhouette di adp (si perdeva la lettura sulla separazione globale su sdc); lasciarla come sezione separata.

**Conseguenza ancora vera**: nessuna sezione del notebook dà una scala di riferimento alla silhouette euclidea. La numerazione è 2, 2.1, 2.2 (adp), 3, 3.1, 4. Il filtro di `warnings` sul `copy` di HDBSCAN resta (serve anche alla 3.1).

## 15-10-26 — Confidenza di appartenenza di HDBSCAN (`probabilities_`) come valutazione, non come validazione

**Decisione**: `clustering_evaluation` ottiene una valutazione solo per HDBSCAN, `membership_confidence` (`src/analysis/clustering_evaluation.py`): per cluster, probabilità media, 10° percentile e quota di soggetti sotto una soglia; e la silhouette per soggetto mediata su tutti i non-rumore contro i soli soggetti sopra la soglia. Appartiene a `clustering_evaluation` (empirica: usa solo etichette e spazio clusterizzato, nessuna variabile esterna), non a `cluster_interpretation`.

**Cosa è e cosa non è**: `probabilities_` è un lambda normalizzato dentro ogni cluster (0 per il rumore): dice quanto un soggetto è vicino al nucleo del *suo* cluster. Nessuna fonte trovata la usa come indice di validità né propone una soglia: la soglia la dichiara chi chiama la funzione, come `MAX_NOISE_FRACTION`. È calcolata sulla densità dello spazio clusterizzato: su un UMAP con `min_dist=0.0` misura quanto UMAP ha impacchettato il cluster, non una proprietà dei dati di lesione.

**Alternative scartate**: (1) pacchetto `hdbscan` standalone, per persistenza dei cluster, albero condensato, GLOSH e `relative_validity_`: `sklearn.cluster.HDBSCAN` (1.8.0 qui) espone solo `labels_`, `probabilities_`, `centroids_`, `medoids_` e `dbscan_clustering`; il pacchetto non è in `environment.yml`, costerebbe una dipendenza e rifare le run, e per il notebook solo descrittivo non serve (DBCV era già scartato, `docs/guides/clustering.md`). (2) Probabilità mediana per cluster: scartata perché vale 1.0 in tutti i cluster quando la maggior parte è nucleo (lesione dice nc2, `min_cluster_size=100, min_samples=20`: 8 cluster su 5845 soggetti, 47 rumore, mediana 1.0 ovunque); si riportano media e 10° percentile.

**Misurato sul prototipo**: lesione dice nc2 (100, 20): i due cluster grandi (2652 e 2173) hanno p10 = 1.00 e nessun soggetto sotto 0.5; i frammenti da 132-188 hanno p10 tra 0.34 e 1.00 e fino al 22.4% sotto 0.5. Silhouette 0.648 su tutti i non-rumore, 0.650 sui soggetti con probabilità ≥ 0.5: su questa run la silhouette non dipende dai soggetti periferici. Lesione euclidean nc10 (100, 20): 12 cluster, 946 rumore, fino al 68% dei soggetti di un cluster sotto 0.9.

**Conseguenza ancora vera oggi**: la valutazione è la sezione 3.1 di `clustering_evaluation.ipynb` (`LOW_PROBABILITY = 0.5` è un esempio, non una scelta); provata sulle run di produzione `12-10_s1.4-vol_m_dice_nc2_mcs75_ms10` e `_ms20`. La mediana delle probabilità non si riporta: satura a 1.

---

## 15-10-26 — Replica della PCA varimax di Thiebaut de Schotten 2020 sul disconnettoma voxelwise `s2.4-vol`

**Decisione**: la replica del paper si fa sulla matrice voxelwise `s2.4-vol` (5845 × 291345), non sulla lesione parcellata (messa in pausa dall'utente lo stesso giorno). Metodo: PCA sulla covarianza (centrata, non scalata), varimax con al più 500 iterazioni sulle prime 42 componenti, punteggi per regressione multipla; R² di ogni componente contro `lesion_volume_voxels_2mm`. Codice in `src/analysis/covariance_pca.py`, notebook `notebooks/pipeline_building/thiebaut_2020_replication.ipynb`.

**Numero di componenti**: il paper non dice come ha scelto le 46 componenti totali; riporta solo che 30 superano il 90% della varianza, letto dalla curva cumulata (Fig. 2a). Si ruota quindi il numero minimo di componenti che raggiunge il 90%: 42 su `s2.4-vol` (50% con 2, 80% con 14). Scelto dall'utente tra: curva prima e numero dopo, 90%, 30 fisso.

**Alternative scartate**: `pca_varimax_embed` (`reduction.py`) — fa copie full-size di `X` (circa 13 GB in float64 solo per i punteggi), non entra nei 25,7 GB di RAM. La matrice di covarianza tra voxel (291345²) è impossibile; si usa la matrice soggetti × soggetti, che dà gli stessi autovalori (verificato contro `sklearn.decomposition.PCA`, scarto relativo massimo 8e-15 su 400 × 30000).

**Primo risultato** (non un giudizio sul metodo): R² con il volume massimo 0.251 sulle ruotate e 0.452 sulle non ruotate, 2 componenti su 42 sopra 0.1 in entrambi i casi. Il paper riporta R² < 0.1 per tutte; qui lo spazio è diverso (voxel, non 372 regioni), quindi è un confronto di tendenza.

## 15-10-26 — clustering_evaluation: silhouette di adp riammessa, con la quota di coppie a distanza 1

Per adp la sezione 2.4 calcola di nuovo la silhouette (`distance_matrix_silhouette`, sulla distanza dice già in cache), accanto a `saturated_pair_share`: la quota di coppie di soggetti a distanza esattamente 1. La purezza dei vicini (2.3) resta. La decisione del 13-10-26 ("per adp la silhouette è sostituita dalla purezza") valeva per le lesioni.

Perché (misurato il 14-10-26): la saturazione è una proprietà della matrice, non di adp. Lesioni `s1.4-vol`: 84,3% delle coppie a distanza 1, silhouette 0,030 contro purezza 0,922. Disconnessione voxelwise `s2.4-vol` (continua, dice pesata): ogni mappa copre in mediana 109734 voxel su 291345 e solo lo 0,0015% delle coppie ha supporto disgiunto, quindi la silhouette non è schiacciata. Il testo generico "distanza 1 per la gran parte delle coppie" era falso per sdc.

Alternativa scartata: decidere per matrice se mostrare o no la silhouette. Si mostra sempre, con `pairs_at_distance_1` accanto: la lettura è dei dati, non di una regola scritta nel notebook.

Conseguenza ancora vera: la silhouette di adp (distanza dice) non è confrontabile con quella euclidea delle run su embedding.

## 15-10-26 — clustering_evaluation: tolti il p empirico e la stabilità al sottocampionamento; nullo non per evidence_accumulation

Tolti dal notebook e da `src/`: `NullReference.empirical_p`, `consensus_clustering.subsampling_stability_ensemble` con `StabilityEnsemble`, `DISSOLVED_JACCARD` e `_best_jaccard_per_cluster` (ARI ripetuto e Jaccard per cluster, sezione 4), la voce `subsampling_stability` di `EVALUATIONS`. Resta `subsampling_stability_index` (usato da `clustering_tuning_explorer.ipynb`). Il nullo (2.2) ora esclude anche `evidence_accumulation`, oltre ad adp.

Perché (misurato il 14-10-26):
- **p empirico**: i fit del nullo con meno di 2 cluster sono scartati dal denominatore, quindi il minimo non è 1/(N_NULL+1) ma 1/(fit validi + 1). Su `hdbscan 12-10_s1.4-vol_m_dice_nc10_mcs100_ms10` 24 fit su 30 sono degeneri e `gaussian_p` vale 1/7 = 0,143: il p risultava "non significativo" proprio perché il nullo, che di solito non trova cluster, veniva scartato. Il margine sulla media del nullo resta.
- **stabilità**: ricampiona solo il passo di clustering sull'embedding salvato, che UMAP ha costruito su tutti i soggetti (i soggetti tolti hanno già influenzato la posizione degli altri): l'ARI 0,92 non dice che il risultato non dipenda dal campione. Il Jaccard per cluster di hdbscan `03-09_s1.2-vol mcs200_ms5` smentiva il testo "Jaccard 0 in tutte le ripetizioni": tre cluster da 209/239/209 soggetti hanno Jaccard medio 0,006/0,049/0,346 (dissolti nel 99%/95%/54% delle ripetizioni), quindi la dimensione sola non spiega. Per adp il rifit rifà la distanza a ogni ripetizione (sdc, continua: stimato circa 17 minuti ciascuna, non misurato senza `dadapy`).
- **evidence_accumulation nel nullo**: con `N_NULL = 2` la cella non finiva in 25 minuti (ogni fit ripete spectral 50 volte).

Alternative scartate: contare i fit degeneri come "non buoni quanto l'osservato" (p minimo 1/31); ripetere anche UMAP in ogni ripetizione della stabilità (minuti per ripetizione su 5845 x 220 mila).

Conseguenza ancora vera: il notebook non ha nessuna misura di stabilità né un indicatore di incertezza sul margine del nullo; la voce del 13-10-26 qui sotto descrive ciò che c'era prima.

## 15-10-26 — cluster_interpretation: tolti tutti i test statistici e la sezione «cluster contro resto», il notebook è solo descrittivo

**Cosa è stato fatto** in `notebooks/post-results_analysis/cluster_interpretation.ipynb`, dopo una revisione che ha riprodotto i problemi sulle run `12-10_s1.4-vol_m_dice_nc10_k7_link_ward` (7 cluster), `03-09_s1.2-vol_m_euclidean_nc2_mcs100_ms20` (hdbscan, 15 cluster) e `30-09_s2.3-stream_k5_link_ward` (sdc):
- **via la sezione 2.2** (Kruskal-Wallis con ε², chi-quadro con V di Cramér, controllo senza UCL-UK) e **via da §3** `p`, `p_fdr`, la correzione Benjamini-Hochberg, `r` (rank-biserial), `pari_merito`, `lettura` e `odds_ratio`. Resta §2 (copertura, media ± sd, mediana [Q1–Q3], percentuali per categoria). La sezione 3 «cluster contro resto» (n, mediana e quota nei due gruppi, in 3.1 anagrafiche e 3.2 derivate) è stata tolta subito dopo, su richiesta: le mediane per cluster sono già in §2, quindi non aggiungeva niente. Con lei vanno via `cluster_vs_rest`, `BLOCK_OF` e le quote di localizzazione nel frame (`LOCATION_FRACTIONS` non è più importato);
- **NIHSS e istruzione** non sono più "non testati": non c'è più un test, compaiono in §2 con il loro `n` nella tabella di copertura;
- **`disconnection_mean_2mm` non è più una variabile del notebook**: è `disconnection_load_voxels_2mm` × 4.3767e-6 per ogni soggetto (rapporto minimo = massimo, Spearman 1.0 sulla run sdc), cioè gli stessi valori in un'altra scala. Resta solo il carico; la colonna resta nel registro.

**Perché** (verificato):
- ε² e V di Cramér hanno un valore atteso sotto l'ipotesi nulla che cresce con il numero di cluster e cala con n, mentre le soglie di lettura (Cohen) sono fisse. Con le etichette dei cluster rimescolate a caso, sulla run hdbscan a 15 cluster `Dataset` veniva letto "debole" in 188 prove su 200, `Sesso` senza UCL-UK in 168/200, `Età` senza UCL-UK in 171/200;
- il controllo senza UCL-UK confrontava effetti su n molto diversi (5194 contro 1716 soggetti per il sesso): V da 0.089 a 0.114 (+0.025) contro un aumento atteso per solo caso di 0.024 (0.032 → 0.056);
- la famiglia FDR di §3 era fatta di test dipendenti: le sette quote di localizzazione sommano esattamente a 1, `Sede dominante` deriva dalle stesse quote, e le categorie di una variabile sono confronti uno-contro-resto sulla stessa colonna;
- con migliaia di soggetti i p-value sono quasi sempre minuscoli, e per volume, localizzazione e disconnessione l'associazione è in parte per costruzione;
- `r` e `pari_merito` richiedevano una spiegazione lunga e non erano di uso immediato. `odds_ratio` era instabile (96, 206) e il testo doveva già dire di non leggerlo senza le quote.

**Alternative scartate**: sottrarre il pavimento di caso calcolato per permutazione e leggere l'effetto rispetto a quello; ripetere il controllo su un sottocampione dello stesso n; una soglia minima di soggetti per cluster in §3 (29 delle 183 run di produzione hanno un cluster sotto i 30 soggetti, 17 sotto i 10, minimo 2); tenere `r` e `pari_merito` come descrizione. Tutte più complesse del guadagno, e l'utente ha deciso di togliere i test: "non riusciamo a farli".

**Conseguenza ancora vera**: sostituisce le tre decisioni del 13-10-26 su `cluster_interpretation` che riguardano i test (effetto prima del p-value, NIHSS e istruzione non testati, §3 con p_fdr e pari merito). Il confronto tra due cluster dell'app (`cluster_pair`) fa ancora Mann-Whitney, Fisher e p corretto, con il sesso su due righe (stesso confronto due volte). Il confronto di un cluster contro tutti gli altri non esiste più nel notebook; resta nell'app solo come confronto tra due cluster. Le quote di localizzazione per cluster non sono più in nessuna tabella del notebook (resta la sede dominante in percentuale). Anche la scelta del cluster (`CLUSTER`, con il bordo nero nel grafico delle dimensioni) è stata tolta: §2 descrive tutti i cluster, quindi il notebook ora lavora su una run, non su un cluster. Il notebook assume che la disconnessione media resti proporzionale al carico: se il registro la ricalcolasse in un altro modo, non se ne accorge.

---

## 13-10-26 — clustering_evaluation: purezza dei vicini, nullo e stabilità ripetuta (funzioni in `src/` e notebook)

**Cosa è stato aggiunto** (`clustering_evaluation.py`, `consensus_clustering.py`): `per_cluster_silhouette` (micro, macro, minimo e quota di negativi per cluster), `null_reference_silhouette` (silhouette osservata contro lo stesso metodo rifittato su dati senza cluster, nullo `gaussian` o `permute`), `knn_purity` (quota dei k vicini nello stesso cluster, su matrice di distanze precalcolata), `subsampling_stability_ensemble` (n ripetizioni di sottocampione contro le etichette salvate, ARI e Jaccard per cluster).

**Perché** (misurato su `s1.4-vol`):
- La silhouette di adp con distanza dice è inutilizzabile: l'84,3% delle coppie di soggetti ha distanza esattamente 1 (nessun voxel in comune). Run `Z25`: silhouette 0,03, ma 89% dei 30 vicini nello stesso cluster contro il 21% atteso a caso. Decisione: per adp si tiene la purezza dei vicini, non la silhouette. Il `silhouette` di `tuning_results.csv` e `silhouette_plot.png` per adp usano la stessa distanza dice e hanno lo stesso limite; non sono stati toccati.
- Una silhouette assoluta non dice se c'è struttura: ward k=3/9/20 su nuvole senza cluster dà 0,39/0,23/0,28 (gaussiano) o 0,33/0,16/0,37 (colonne permutate), contro 0,68/0,52/0,48 osservate. A k=20 su 2 componenti il margine è 0,195 con il nullo gaussiano e 0,112 con quello permutato: il tipo di nullo cambia la lettura, quindi vanno riportati entrambi.
- La stabilità con un solo seed nasconde la dispersione: ward k=9, 100 ripetizioni, ARI medio 0,920, sd 0,061, intervallo 0,741–0,990. A k=20 (2 componenti) l'ARI medio è 0,732 e i cluster 7 e 18 si dissolvono (Jaccard < 0,5) nell'85% e 90% delle ripetizioni: informazione che l'ARI globale non dà.

**Alternative scartate**: per adp, una silhouette su distanza tagliata ai soli vicini (non è la metrica con cui adp decide); come riferimento della stabilità, il rifit sul 100% (non è detto che riproduca le etichette salvate; `subsampling_stability_index` lo fa e resta per `clustering_tuning_explorer`).

**Conseguenza ancora vera**: `knn_purity` risolve i pareggi a distanza uguale con il valore atteso sotto scelta casuale, non per posizione, e riporta `tied_share`; i cluster con k o meno membri non sono valutabili. Il registro `EVALUATIONS` ha due voci nuove (`null_reference` tutti i metodi tranne adp, `knn_purity` solo adp); `geometric_metrics` non include più adp: il notebook lo valuta con la purezza dei vicini (sezione 2.3), la stabilità con `N_REPEATS = 100` (`ADP_N_REPEATS = 3` per adp, non cronometrato: `dadapy` manca nell'ambiente `nemesis`) e un avviso stampato quando il rumore supera `NOISE_WARNING_FRACTION = 0.10`. Nella stabilità di hdbscan un cluster vicino a `min_cluster_size` ottiene Jaccard 0 perché il parametro è un conteggio assoluto (run `03-09_s1.2-vol mcs200_ms5`: cluster da 209 e 239 soggetti); non è corretto scalando il parametro.

---

## 13-10-26 — cluster_interpretation: regressione logistica tolta dal notebook

**Cosa è stato fatto**: la sezione "Regressione logistica" (§4: modello per cluster, grafico degli odds ratio, mappa di tutti i cluster) è stata tolta da `notebooks/post-results_analysis/cluster_interpretation.ipynb`. Con lei vanno via la lettura della lateralità da `lesion_metadata.csv` (serviva solo lì) e l'import di `cluster_vs_rest_regression`. `src/analysis/cluster_drivers.py` e i suoi test restano: li usa `cluster_pair.pair_regression`, cioè il confronto tra due cluster nell'app e nella Parte 4 di `clustering_comparison.ipynb`.

**Perché**, sulla run `12-10_s1.4-vol_m_dice_nc10_k7_link_ward` (5845 soggetti, 7 cluster):
- il modello completo (con NIHSS) stimava **2 cluster su 7**: il NIHSS manca per interi dataset (UCL-UK, 0%), quindi lo scarto dei mancanti lasciava 1579 soggetti su 5845, nessuno di UCL-UK;
- il blocco clinico (età, sesso, dataset) ha AUC 0.54-0.59 e pseudo-R² 0.004-0.016: non aggiunge niente a quello che §2 e §3 già mostrano (effetti deboli o trascurabili);
- il blocco anatomico (volume, lateralità, quote di localizzazione) ha AUC 0.88-1.00 e pseudo-R² 0.32-0.96: ricostruisce la partizione, cioè l'input del clustering, quindi non spiega nulla di esterno;
- due cluster (1 e 6) erano rifiutati come "separazione perfetta" per una cella vuota (PASPORT assente dal cluster 1, SFB936 dal 6), non per una separazione vera;
- la direzione era opposta alla domanda del progetto: prevedeva il cluster dalle variabili cliniche, mentre la domanda è se i cluster differiscono per esito clinico.

**Alternative scartate**: tenere solo il modello clinico (non aggiunge informazione); dividere in due modelli clinico/anatomico con avvisi sulla circolarità (complessità senza guadagno).

**Conseguenza ancora vera**: la domanda sul NIHSS resta aperta e va fatta con il cluster come predittore e il dataset come covariata (NIHSS ~ cluster + dataset), dentro i dataset che lo misurano, in una sezione a parte. Il campo sui livelli persi dopo lo scarto, il parametro `min_level_count` e i messaggi di rifiuto migliori proposti per `cluster_drivers.py` non sono stati implementati.

---

## 13-10-26 — cluster_interpretation §3 (cluster contro resto): stessa popolazione di §2, due gruppi di variabili, pari merito visibili

**Cosa è stato adottato** nella sezione 3 di `notebooks/post-results_analysis/cluster_interpretation.ipynb`:
- il «resto» sono gli altri cluster della run **senza il rumore HDBSCAN** (prima `frame`, rumore incluso); `-1` come cluster solleva;
- **NIHSS e istruzione non testati** (stessa `NOT_TESTED_VARIABLES` di §2); le variabili di disconnessione solo sulle run sdc (prima testate sempre);
- le variabili sono divise per origine in `BLOCK_OF`: **3.1 anagrafiche e di sito** (età, sesso, dataset) e **3.2 derivate dalla lesione o dal disconnettoma** (volume, quote di localizzazione, lato, sede dominante, disconnessione). Il 3.2 è presentato come descrizione del cluster, non come spiegazione;
- una sola famiglia di correzione Benjamini-Hochberg per cluster, su 3.1 e 3.2 insieme; nelle tabelle si mostra solo `p_fdr`, non il `p` grezzo (come in §2);
- **una variabile con due sole categorie ha una riga sola** (la prima in ordine alfabetico, es. sesso = F): l'altra era lo stesso test con odds ratio rovesciato e p identico, e contava due volte nella correzione (cluster 0 di `12-10_s1.4-vol_m_dice_nc10_k7_link_ward`: 28 test invece di 27);
- colonna `lettura` per `r` con le stesse parole di §2 (trascurabile < 0.1, debole < 0.3, moderato < 0.5, forte; convenzioni di Cohen per r); le variabili con categorie non ne hanno, la differenza tra le due quote è già la misura;
- colonna `pari_merito` accanto a `r`: la quota di coppie (soggetto del cluster, soggetto fuori) con lo stesso valore. Il massimo di |r| è 1 meno questa quota. Cluster 0 di `12-10_s1.4-vol_m_dice_nc10_k7_link_ward`: `loc_infratentorial` 75% di pari merito (tetto 0.25, r = −0.149), `loc_subcortical_gray` 6%.

**Correzione al testo**: «(r+1)/2 è la probabilità che un soggetto del cluster superi uno esterno» è vera solo contando i pari merito per metà (la U di scipy li conta 0.5); il testo ora lo dice.

**Alternative scartate**: una sezione 3.3 con tutti i cluster in una mappa (non voluta); una famiglia di correzione separata per gruppo; normalizzare r per il suo tetto (cambierebbe il significato della grandezza).

**Conseguenza ancora vera**: non c'è l'intervallo di confidenza dell'odds ratio, e `r` si ordina ancora per |r| (colonna `pari_merito` da leggere insieme). Le funzioni stanno nel notebook, non in `src/`.

---

## 13-10-26 — cluster_interpretation §2: effetto prima del p-value, NIHSS e istruzione non testati

**Cosa è stato adottato** nella sezione "Associazione con variabili cliniche e anatomiche" di `notebooks/post-results_analysis/cluster_interpretation.ipynb`:
- accanto a ogni test una **dimensione dell'effetto con la sua lettura**: ε² = H/(n−1) per il Kruskal-Wallis (trascurabile < 0.01, debole < 0.06, moderato < 0.14, forte oltre: soglie di η² di Cohen 1988), V di Cramér per il chi-quadro;
- la V si legge con le soglie di Cohen 0.1/0.3/0.5 **divise per √d**, d = min(righe, colonne) − 1. Prima si usava la scala di una tabella 2×2 su tabelle 7×2…7×8. Sulla run `12-10_s1.4-vol_m_dice_nc10_k7_link_ward` cambia solo `dataset` (V = 0.089: da trascurabile a debole);
- si mostra solo il **p-value corretto (FDR)**, non il p grezzo né H/χ²;
- tolta la quota di celle attese < 5 e il suo avviso;
- **NIHSS e istruzione non testati** (restano nelle tabelle descrittive e di copertura): mancano per interi dataset, NIHSS 0% in UCL-UK (4119 soggetti su 5853), istruzione assente in 5 dataset su 8 (15% di copertura), quindi il test confronterebbe anche mix di siti. Le variabili non testate e il motivo sono in `NOT_TESTED_VARIABLES`, stampato a ogni run;
- **controllo di sensibilità senza UCL-UK** per età e sesso (`SENSITIVITY_VARIABLES`, `SENSITIVITY_EXCLUDED_DATASET`): lo stesso test su 1726 soggetti. Sulla run `12-10_s1.4-vol_m_dice_nc10_k7_link_ward` età ε² 0.012 → 0.015 (debole in entrambi), sesso V 0.089 → 0.114 (la lettura passa da trascurabile a debole perché la soglia è 0.10: i due numeri sono vicini);
- **i test non scartano cluster in silenzio**: Kruskal-Wallis e chi-quadro sollevano se un cluster non ha nessun dato sulla variabile, e il controllo senza UCL-UK confronta gli stessi cluster del test principale (altrimenti perdere un cluster intero cambierebbe la domanda senza dirlo);
- tabelle descrittive: una tabella di **copertura** (soggetti con il dato e quota sul cluster, con la riga "Tutti i cluster"; una variabile a cui mancano al più `MAX_MISSING_LISTED` = 10 soggetti non è nella tabella ma ha una riga di avviso, con gli id di chi manca), poi media ± sd **e** mediana [Q1–Q3] senza l'n nelle celle. Le quote delle categoriche sono sui soli soggetti con il dato.

**Perché**: con 5845 soggetti il p-value è quasi sempre minuscolo (età p = 3·10⁻¹¹ con ε² = 0.012, volume ε² = 0.132): da solo non distingue un effetto trascurabile da uno grande. Il p corretto resta perché a pari effetto distingue 856 soggetti (istruzione, p = 0.13, ε² = 0.011) da 5000.

**Alternative scartate**: tenere l'avviso sulle celle attese < 5 (riguarda l'affidabilità del p, non l'effetto; con χ² = 8188 su `location_dominant` nessuna lettura cambia); soglia minima di 30 soggetti per cluster per il test sul NIHSS (nessun cluster sarebbe stato escluso, e non risolve la mancanza per sito); imputare NIHSS e istruzione (nei dataset che non le hanno mai misurate non c'è informazione da cui imputare: si inventerebbe il dato del 70% della coorte).

**Conseguenza ancora vera**: §3 (cluster contro resto) e §4 (regressione) usano ancora il NIHSS, e `kruskal_by_cluster` scarta ancora in silenzio i cluster senza dati validi (rimandato). Il NIHSS merita un'analisi dedicata (dentro i dataset che lo misurano, con il dataset come covariata), in una sezione a parte. Le funzioni stanno nel notebook, non in `src/`.

---

## 14-10-26 — Produzione clustering s2.4-stream: HDBSCAN "meno peggio" incluso su richiesta, UMAP 2D creato solo per la vista

**Cosa è stato adottato**: 19 run sulla matrice grezza s2.4-stream (7 agglomerative `average`/`cosine` k=3-9; 6 HDBSCAN; 6 ADP `dice` Z = 2.5-6.0). Criterio "buoni e discreti" come s1.4/s2.4-vol, con due scostamenti:
- **HDBSCAN**: nessuna riga è usabile (rumore 71-83%); sono state prodotte lo stesso le 6 righe "meno peggio" con 8-20 cluster, su richiesta. Descrivono il 17-29% dei soggetti. **Alternativa scartata**: non produrre HDBSCAN per lo streamline.
- **ADP Z=5.0 e 6.0** (9 e 7 cluster): inclusi perché hanno 7-20 cluster e un cluster più grande sotto il 60%, senza averli letti nel report del tuning.

**UMAP 2D**: per il grafico e per Dash serviva una vista con gli stessi 5831 soggetti. È stato creato `14-10_s2.4-stream_m_euclidean_nc2` (`n_neighbors=15`, `min_dist=0.0`, come quello di s2.3-stream), senza tuning. **Alternativa scartata**: usare l'UMAP di s2.3-stream (5838 soggetti, altro ordine) o produrre senza grafici (e poi dover rifare le run).

**Conseguenza ancora vera**: l'UMAP è solo una vista; i cluster sono calcolati sui 87 tratti. Altri linkage (ward, complete) hanno solo k parziali instabili e non sono stati prodotti.

---

## 12-10-26 — Produzione clustering s2.4-vol (SDC voxelwise): stesso criterio "buoni e discreti" di s1.4, con HDBSCAN non stabile incluso

**Cosa è stato adottato**: 25 run (14 agglomerative, 7 HDBSCAN, 4 ADP dice) scelte dal tuning del 12-10-26 con lo stesso criterio di s1.4-vol:
- agglomerative: nc2 `ward` k = 5, 7, 9, 13, 15, 18; nc10 `average` k = 3, 6, 7, 8, 10, 13, 14, 15 (average perché è l'unico linkage con k stabili su nc10);
- HDBSCAN: le 7 righe usabili con 8-20 cluster;
- ADP: `dice`, Z = 2.0, 2.5, 3.0, 3.5 (16, 9, 7, 7 cluster).

**Differenza con s1.4**: su SDC **nessuna riga HDBSCAN è stabile** (ARI minimo 0.12-0.30 al sottocampionamento). Le 7 run sono state prodotte lo stesso, per coerenza con s1.4 e perché lo scopo è descrivere i soggetti, non dichiarare sottotipi. **Alternativa scartata**: escluderle (17-18 run).

**Conseguenza ancora vera**:
- ADP Z=3.0 e Z=3.5 sono la stessa partizione (7 cluster, ARI ~1): la seconda è un duplicato, tenuto per simmetria con s1.4.
- Z=4.0 (5 cluster) e Z=5.0 (3 cluster) sono "buoni" nel tuning ma non sono stati prodotti: l'intervallo scelto è 7-20 cluster.
- Una run ADP su SDC dura circa 48 minuti e copia 6.3 GB: `production/adp` pesa 25 GB. Ogni Z ricalcola le distanze dice, anche se cambia solo il taglio.

---

## 12-10-26 — Embedding Explorer: run con più di 3 componenti disegnate sul gemello 2D, centroidi nello spazio del clustering

**Cosa è stato adottato**: una run `clustering.py` il cui `matrix.npy` non è 2D/3D (clusterizzata su un UMAP a 10 componenti o su una matrice grezza) si disegna sulle coordinate dell'embedding gemello registrato nel suo `config.md` (`viz_embedding_path`), con una nota sotto il grafico. Prima risultava "non mostrabile". Il gemello viene ricontrollato (2D/3D, stessi soggetti nello stesso ordine) a ogni apertura.

Il centroide di un cluster e il suo soggetto reale più vicino (cerchio nel grafico, pannello "Soggetto rappresentativo") si calcolano nello **spazio del clustering** (le 10 componenti), e il cerchio sta sulla posizione disegnata di quel soggetto. **Alternativa scartata**: la media delle coordinate disegnate. In 2D la media di un cluster non è il suo centro nello spazio dove i cluster sono stati calcolati, e il "più vicino" cambia (test: stessi punti, rappresentante diverso).

**Eccezione**: una run su matrice grezza (ADP su 221955 colonne, metrica dice) non ha uno spazio dove la media sia coerente con la metrica del clustering, quindi i centroidi restano calcolati sulle coordinate disegnate.

**Conseguenza ancora vera**: il disegno non è la geometria del clustering. Due cluster vicini nel disegno possono essere lontani nelle 10 componenti, e viceversa. Il gemello di dice nc10 è `12-10_s1.4-vol_m_dice_nc2` (`n_neighbors=50`), non il dice nc2 scelto dal tuning (`n_neighbors=100`).

---

## 12-10-26 — Produzione clustering s1.4-vol: candidati "buoni e discreti", non un solo k

**Cosa è stato adottato**: la produzione di s1.4-vol (lesione) comprende 67 run, scelte dal tuning del 12-10-26 con un criterio a due livelli, **buono + discreto**:
- agglomerative: `ward`/`euclidean`, k nei livelli "buono" e "parziale" del tuning fino a k=20 (23 run: dice nc2 7, dice nc10 7, euclidean nc10 6, euclidean nc2 3);
- HDBSCAN: ogni riga "usabile" (3-30 cluster, rumore ≤ 25%, cluster più grande ≤ 60%) con 8-20 cluster (40 run);
- ADP: `dice`, Z = 2.5, 3.0, 3.5, 4.0 (7-17 cluster, 4 run).

Perché: lo stesso di `docs/experiments/clustering/s1_production.md` (01-09-26): nessun criterio interno indica un k solo e k non è separabile da `n_components`, quindi si tengono aperte più risoluzioni. Un k non stabile resta una partizione valida per descrivere i soggetti: non sostiene "esistono N sottotipi".

**Alternative scartate**:
- solo i k "buoni" (circa 13 run per s1.4-vol): lascia fuori le risoluzioni intermedie su cui si vuole guardare come si divide un gruppo grande;
- una sola riga HDBSCAN per numero di cluster (24 run invece di 40): scelta di quale riga è "la migliore" non necessaria, ma molte righe condividono la stessa partizione (ARI ≥ 0.995 tra le righe a 8 cluster dei dice), quindi le 40 non sono 40 letture indipendenti;
- ADP `euclidean`: degenere su ogni Z (un cluster al 93-99% dei soggetti).

**Conseguenza ancora vera**:
- Le 19 run su dice nc10 usano come vista 2D `12-10_s1.4-vol_m_dice_nc2` (UMAP dice nc2 con `n_neighbors=50`, `min_dist=0.0`), creato solo per visualizzarle: è il gemello di dice nc10. Il dice nc2 "tuned" (`08-10_s1.4-vol_m_dice_nc2`, `n_neighbors=100`) resta quello per cui si clusterizza su nc2. I due hanno lo stesso tag `m_dice_nc2` e differiscono solo per data e `n_neighbors`: non confonderli.
- I parametri di ogni run stanno in `config.md`/`runs.csv`, ma `params_file` nel `config.md` punta a un file temporaneo: `params_clustering.json` non è stato toccato.
- Non è stata fatta nessuna scelta sul lato lesionale (fattore di disturbo o risultato): l'input è quello di s1.4-vol, senza riflessione.

---

## 08-10-26 — Agglomerative: griglia `metric` riaperta (euclidean, cosine, manhattan) sugli embedding s1.4-vol

**Cosa è stato adottato**: il tuning di agglomerative sui 6 embedding UMAP di s1.4-vol (`{dice,euclidean}` x `n_components` 2/3/10) usa `metric` ∈ {`euclidean`, `cosine`, `manhattan`} invece del solo `euclidean`. Sono 290 combinazioni valide per embedding (29 `n_clusters` da 2 a 30 x 4 linkage; 116 euclidean, 87 cosine, 87 manhattan): `ward` esiste solo con `euclidean`, le altre 58 combinazioni sono saltate. Le 6 run con il solo `euclidean` (116 combinazioni, stesso giorno, 16:49-17:07) sono state sostituite con `overwrite: true`: cartelle riscritte (`results/lesion/clustering/tuning/agglomerative/umap/08-10_s1.4-vol_*`) e le 6 righe vecchie tolte da `runs_tuning.csv` di agglomerative (14 righe prima e dopo: 8 delle sessioni precedenti + le 6 nuove, una per output). HDBSCAN non è stato rilanciato: la sua griglia non cambia.

Perché: test di sensibilità sulla scelta della metrica. **Alternativa scartata**: tenere solo `euclidean`, che lascia senza risposta se il k di agglomerative dipende dalla metrica.

**Conseguenza ancora vera**: i tre insiemi di risultati non si leggono come un unico punteggio.
- `cosine` su un embedding UMAP è difficile da interpretare: l'origine dello spazio non ha significato, la metrica misura solo l'angolo.
- La silhouette non è confrontabile tra metriche (ogni metrica definisce le proprie distanze): il confronto tra metriche va fatto su ARI a parità di k e su `lesion_side`.

---

## 08-10-26 — Confronto tra due cluster della stessa run al posto del confronto "stesso embedding"

**Cosa è stato adottato**: la modalità "Dentro lo stesso embedding" della sezione di confronto dell'Embedding Explorer (due run con lo stesso `input_path`, sullo stesso embedding) è sostituita da "Dentro lo stesso clustering": si sceglie **una** run e due suoi cluster (anche il rumore `-1`). Il confronto avviene sui soli soggetti dei due cluster (`src/analysis/cluster_pair.py`):

- profilo demografico e clinico: Mann-Whitney per ogni variabile numerica (effetto: correlazione rank-biseriale, positiva se il primo cluster ha valori più alti), Fisher esatto per ogni categoria di ogni variabile categorica, p corretto con Benjamini-Hochberg su tutti i test insieme;
- regressione logistica "sta nel primo cluster" contro "sta nel secondo" (`cluster_drivers.cluster_vs_rest_regression` sui soli due cluster), con età, NIHSS, log10 del volume, quote corticale/sottocorticale grigia/infratentoriale, sesso e dataset;
- distanza euclidea tra i centroidi, con il raggio medio di ciascun cluster come scala di lettura;
- anatomia: overlap map di ciascun cluster e la loro differenza in punti percentuali (rosso = più frequente nel primo cluster), per la lesione e, in una run sdc, per la disconnessione in modalità "percent".

Perché: la domanda che si pone è «in cosa il cluster 1 è diverso dal cluster 2», non «due clustering sullo stesso embedding si accordano?». La seconda restava possibile solo via notebook (`clustering_comparison.ipynb`).

**Alternative scartate**:
- *Terza modalità accanto alle altre due*: la modalità "stesso embedding" non serviva più a nessuno; tenerla avrebbe lasciato un ramo mai usato (`centroid_distances` e il controllo `input_path` sono stati cancellati).
- *Il confronto dentro il pannello "Descrizione del cluster"*: quel pannello è guidato dal selettore di cluster condiviso con le mappe, e dovrebbe poi scegliere un secondo cluster.
- *Variabili del notebook `cluster_interpretation` in toto* (indice di lateralità da `lesion_metadata.csv`): non nel registro soggetti, richiederebbe un secondo file; la lateralità entra con `lesion_side`.

**Conseguenza ancora vera**: il segno di r, dell'odds ratio e della differenza di mappe dipende da quale cluster è il «primo»: scambiarli inverte il segno e lascia invariati distanza, p e AUC. Le mappe dei due cluster si costruiscono con gli stessi builder (e la stessa cache) dei pannelli per cluster: la prima volta leggono ogni NIfTI, per questo stanno in un pannello a parte, sotto i numeri. La sezione si chiama ora "Confronto", non più "Confronto tra run". Dettagli: `docs/guides/embedding_app.md`, `docs/dev/cluster_comparison.md`.

---

## 08-10-26 — ADP (DADApy) adottato come metodo di clustering, sulla matrice grezza e con la sua distanza

**Cosa è stato adottato**: Advanced Density Peaks (`dadapy` 0.3.4) è `CLUSTERING_METHODS["adp"]` (`src/analysis/adp.py`), usato dalla pipeline `clustering.py` come gli altri metodi. Il numero di cluster non si sceglie: lo sweep di tuning è su `Z` (soglia di significatività, 18 valori da 0.25 a 16, `maxk=100`) e su `metric` (`dice` ed `euclidean` nella stessa run, per confrontare le distanze). Gira sulla matrice **grezza** (lesione, SDC voxelwise, SDC streamline), con distanza `dice` come default (`jaccard`/`euclidean` disponibili), non su un embedding. Prima run reale: `results/sdc/clustering/tuning/adp/raw/08-10_s2.2-vol` (1570 x 290940, `dice`), che riproduce k e silhouette del prototipo (`tmp/dadapy_test/`) per tutti i 18 valori di `Z`.

**Alternative scartate**:
- *Pipeline separata `src/pipeline/adp_clustering.py`*: avrebbe duplicato albero di output, `runs.csv`/`runs_tuning.csv`, `config.md`, silhouette plot, tuning plot e lettura del notebook `clustering_tuning_explorer`/`embedding_app`. Come metodo di `clustering.py` eredita tutto. Il costo è che l'ambiente con `dadapy` (separato da `nemesis`, dipende da `jax`) è richiesto solo per le run `"adp"`: import lazy, un config per matrice (`config/pipelines/clustering_adp_<sessione>.json`), nessuna run mista con gli altri metodi.
- *Una fit per combinazione, come gli altri metodi*: ricalcolerebbe le distanze N x N (~2 minuti su SDC voxelwise) a ogni `Z`. Distanze e densità si calcolano una volta per `(metric, maxk)`, ogni `Z` rifà solo il taglio dei picchi.
- *Righe a zero eliminate in silenzio, o sollevate come errore*: `dice`/`jaccard` non esistono per una riga a zero, ma la matrice SDC voxelwise ne contiene una (`sub-STUKLFR0671`) e sollevare impedirebbe di usarla. Prendono l'etichetta `-1` (rumore) per **ogni** metrica, così tutte clusterizzano gli stessi soggetti; `noise_fraction` la riporta.
- *Righe duplicate esatte perturbate*: DADApy divide per la distanza dal primo vicino (0 tra gemelli). Si clusterizzano una volta e il gemello eredita l'etichetta (nella run SDC stream: `sub-STUCLUK1950`/`sub-STUCLUK2303`).
- *`dice`/`jaccard` binari soltanto*: la SDC è continua (`float32`, 24% di celle non nulle in un soggetto di esempio). Per matrici continue `>= 0` si usano le versioni pesate (Czekanowski/Ruzicka), che sulle 0/1 coincidono con le classiche (test).

**Conseguenza ancora vera**: la `silhouette` del tuning è calcolata con la distanza usata per clusterizzare, non con l'euclidea; `calinski_harabasz`/`davies_bouldin` esistono solo per `euclidean`. Le metriche geometriche del notebook di valutazione rifiutano un ADP `dice`/`jaccard`. L'UMAP di produzione su cui si proiettano i cluster è `euclidean`: le due viste non condividono la metrica. Funzionamento e parametri: `docs/guides/clustering.md` (sezione "ADP"), `docs/dev/models.md`.

---

## 08-10-26 — Confronto tra run di clustering: due modalità, identità dell'embedding da `input_path`, homogeneity/completeness orientate

**Cosa è stato adottato**: il confronto tra due run di clustering (sezione "Confronto tra run" dell'Embedding Explorer, `src/analysis/cluster_comparison.py`) ha due modalità, con regole di compatibilità fisse:

- **Stesso embedding**: due run con lo stesso `input_path` in `config.md`; possono cambiare metodo e parametri. Metriche, contingency, chi², purezza, distanza tra centroidi.
- **Tra modalità (lesion vs sdc)**: stesso metodo, stessi valori dei `tag_param`, stesso metodo di riduzione, stesse componenti e metrica; cambia solo la modalità. Metriche, contingency, chi², purezza, profilo clinico dei cluster. Niente centroidi: gli spazi di feature sono diversi.

Il confronto avviene sempre e solo sull'intersezione dei `subject_id`, dichiarata contro la dimensione piena di ciascuna run.

**Alternative scartate**:
- *Confronto libero tra metodi diversi sullo stesso `k`* (la vecchia Parte 1 del notebook, ARI/NMI tra kmeans/agglomerative/spectral/gmm): il notebook non avrà più metodi confrontabili tra pipeline diverse (decisione dell'utente); il confronto tra metodi resta solo dentro lo stesso embedding, dove i centroidi hanno senso.
- *Identità dell'embedding come `(session_name, reduction_method, reduction_n_components, reduction_metric)`* (come in `require_shared_embedding` del notebook): quattro chiavi che coincidono non garantiscono lo stesso file (per esempio due dim_reduction della stessa sessione rilanciate con parametri diversi). `input_path` nomina l'output esatto. In più `centroid_distances` verifica sulle coordinate dei soggetti comuni, e solleva se differiscono.

**Correzione rispetto al notebook**: `clustering_comparison.ipynb` chiama `homogeneity_score(labels_a, labels_b)`, che in sklearn è definita sui cluster *predetti* (B): misura se ogni cluster di **B** contiene un solo cluster di A. Il testo del notebook la descrive invece come "ogni cluster di A contiene soggetti di un solo cluster di B". Le due letture sono invertite (stesso per completeness). Il modulo nuovo passa B come "true" e A come "predicted", così il calcolo coincide con la definizione scritta; un test fissa le due direzioni. I valori homogeneity/completeness già letti dal notebook vanno scambiati tra loro.

---

## 08-10-26 — Tuning di dim reduction: HDBSCAN su ogni combinazione, nello spazio proprio, disegnato sul gemello 2D

**Cosa è stato adottato**: oltre alla trustworthiness, ogni combinazione di uno sweep di `dim_reduction` viene clusterizzata con HDBSCAN (`plot_hdbscan`, `min_cluster_size=100`, `min_samples=10`: i valori di produzione di `params_clustering.json` di allora, un punto di partenza, non una scelta fatta su questo sweep). Per combinazione si registrano numero di cluster e frazione di rumore, e si disegna una griglia per foglia (`metric × n_components`) con una riga per `n_neighbors` e una colonna per `min_dist`. HDBSCAN gira nello spazio dell'embedding stesso, anche a 3 o 10 componenti; i cluster si disegnano sul **gemello 2D** (stessi iperparametri, `n_components=2`, un fit separato già presente nello sweep).

**Perché**: la trustworthiness dice se il vicinato è conservato, non se la struttura è clusterizzabile; `n_components` e iperparametri si scelgono per il clustering a valle, e a 5-10 componenti (`knowledge/dim_reduction_clustering/challenge_of_clustering_after_dim_reduction.md`) il clustering sull'embedding a più componenti è proprio ciò che si userà.

**Scartato**:
- *Disegnare l'embedding a 10 componenti tagliandolo alle prime 2 colonne*: le colonne di UMAP non sono ordinate per importanza, il taglio è arbitrario (`lessons_learned.md` #16).
- *Clusterizzare il gemello 2D invece dello spazio proprio*: i cluster non sarebbero quelli che il clustering vedrebbe a valle. Lo copre `test_plot_hdbscan_clusters_in_the_embeddings_own_space_not_on_its_2d_twin`, verificato per mutazione.
- *Aggiungere `n_clusters_found`/`noise_fraction` a `tuning_results.csv`*: quel file è letto da report, notebook e `build_dim_reduction_strategies_csv`; le colonne stanno in un CSV a parte per foglia.

**Conseguenze che fanno sbagliare chi non le conosce**: i colori dei cluster valgono dentro un solo subplot (HDBSCAN numera i cluster a caso). Uno sweep con combinazioni a più di 2 componenti e senza `n_components: 2` in griglia viene rifiutato prima di iniziare.

## 08-10-26 — "Cosa distingue un cluster": regressione logistica cluster contro resto, al posto dell'importanza per permutazione

**Cosa è stato adottato**: per un cluster scelto, una regressione logistica con esito "il soggetto è in questo cluster" e come predittori età, NIHSS, log10 del volume della lesione, indice di lateralità, tre quote di localizzazione (corticale, sottocorticale grigia, infratentoriale), sesso e dataset. Numeriche standardizzate (odds ratio per deviazione standard), categoriche contro il livello più frequente, soggetti con dati mancanti esclusi e contati. Si riportano odds ratio con intervallo di confidenza al 95% (Wald), VIF, pseudo-R² di McFadden e AUC. Codice in `src/analysis/cluster_drivers.py`, sezione 8 di `cluster_interpretation.ipynb`; una regressione per cluster, riassunte in una mappa di colori.

**Perché**: il confronto cluster contro resto (sezione 7) è una variabile alla volta, e volume, lato, disconnessione e dataset si spiegano a vicenda. La regressione dà l'effetto di ciascuna a parità delle altre, in una grandezza (odds ratio) con un'interpretazione diretta.

**Scartato**:
- *Importanza per permutazione di una foresta casuale* (provata il 07-10-26, mai committata): l'utente non riusciva a leggerla ("non ho capito niente"). Con variabili ridondanti una delle due risultava a ~0 pur portando tutto il segnale, quindi servivano anche i blocchi: troppo da spiegare per una domanda semplice.
- *Carico di disconnessione insieme al volume*: correlazione 0.88 sulla coorte di s2.2-vol, VIF tra 8 e 11, stime instabili. Resta il volume.
- *Lato della lesione insieme all'indice di lateralità*: il lato deriva dall'indice. Resta l'indice.
- *Istruzione*: manca per l'85% dei soggetti.

**Conseguenze che fanno sbagliare chi non le conosce**:
- Le variabili di lesione (volume, lateralità, localizzazione) riassumono i dati con cui è fatta una run lesion: sono legate al cluster anche per costruzione.
- L'indice di lateralità è quasi sempre vicino a -1 (destra) o +1 (sinistra, `LI = (L - R) / (L + R)`): il suo odds ratio per deviazione standard è enorme e si legge come "sinistra contro destra".
- Una categoria assente dal cluster (nessuna lesione infratentoriale) dà un odds ratio vicino a 0 con un intervallo larghissimo: instabilità, non un risultato.
- Un cluster con meno di 10 soggetti per termine viene saltato con un messaggio (regola di Peduzzi): su run hdbscan con cluster piccoli la mappa di colori ha poche colonne.

## 07-10-26 — Matrice lesionale `s1.4-vol` costruita con `correct_out_of_brain: true`

**Decisione**: `07-10_s1.4-vol` è la prima matrice lesionale costruita con la correzione dei voxel fuori dal brain attiva (`brain_mask_path` = maschera res-2). I voxel di lesione fuori dalla maschera cerebrale sono azzerati e il soggetto resta in matrice, con `lesion_volume_voxels` ricalcolato sui dati corretti.

**Numeri**: 5845 soggetti × 221955 feature (5853 − 8 esclusi da `excluded_subjects.csv`, `scope=all`: 3 `empty_mask`, 5 `out_of_brain_fraction_too_high`). **1501 soggetti corretti** (25,7%): 177031 voxel azzerati in totale, mediana 18 voxel per soggetto, massimo 2938, 361 soggetti con almeno 100 voxel.

**Perché**: un voxel fuori dal cervello non è lesione, quindi non deve entrare né nelle feature né nel volume. Le esclusioni per frazione >30% togliono i casi troppo contaminati (i 5 esclusi hanno frazione 0,41–1,0; con la correzione `sub-STUNIPD0558`, frazione 1,0, sarebbe diventato una riga tutta a zero); sotto soglia si corregge invece di escludere.

**Alternativa scartata**: lasciare la correzione spenta. Terrebbe la matrice confrontabile voxel per voxel con `s1.1`–`s1.3`, ma lascerebbe in matrice voxel fuori dal brain per 1501 soggetti.

**Conseguenza ancora vera oggi**: `s1.4-vol` **non è confrontabile voxel per voxel** con `s1.1-vol`, `s1.2-vol`, `s1.3-vol`: costruite prima del 29-09-26, quando il flag non esisteva (`e7ba077`), quindi senza alcuna correzione. Vale per ogni confronto di risultati di `dim_reduction`/`clustering` tra le sessioni: la differenza può dipendere dalla correzione e non solo dai dataset in più.

---

## 07-10-26 — Sede della lesione: sovrapposizione corticale/bianca come categoria a parte (opzione C); layout in `lesion_metadata.csv`, solo 2 mm

**Decisione**: i voxel che HO corticale chiama corteccia e HO sotto-corticale chiama `Cerebral White Matter` non vanno né alla corteccia né alla bianca: formano una **settima categoria**, `cortex_white_boundary`. Le sette: infratentoriale, sotto-corticale grigia, `cortex_only`, `cortex_white_boundary`, `white_matter_only`, ventricolo, non etichettato (infratentoriale e sotto-corticale grigia restano prioritarie su tutto).

**Alternative scartate**: (A) corteccia prioritaria, com'era: sposta la classe "corticale pura" più di ogni altra scelta e non ha un motivo forte; (B) bianca prioritaria: stesso arbitrio specchiato; (D) HO corticale a soglia 50% invece di 25%, per ridurre la sovrapposizione alla fonte: tenuta in riserva, cambierebbe un atlante già deciso e non so se il pacchetto FSL lo contiene (non verificato). Provenienza: i due atlanti sono due file HO distribuiti separatamente, i bordi non sono garantiti coerenti; la fascia corticale a thr25 è generosa.

**Layout in `assets/metadata/lesion_metadata.csv`** (implementato lo stesso giorno in `compute_lesion_metadata`, vedi sotto): da 10 a 18 colonne, **solo a 2 mm**. `location_dominant_2mm` (la categoria con la frazione più alta, vuota con maschera vuota) più sette frazioni `location_<categoria>_2mm` sulla lesione dentro il brain mask (denominatore: `lesion_volume_voxels_2mm`). Scartate: una sola colonna di etichetta senza frazioni (una lesione tocca quasi sempre più aree: a >10% il 63% ne tocca due, il 7% tre; l'etichetta non permette di ricostruire le quote); etichette a soglia nel file (le soglie non sono decise, scriverle le congelerebbe).

**Solo 2 mm, per ora, perché la sede a 1 mm non serve** (motivo dato dall'utente): niente colonne `_1mm` di sede. Il 1 mm resta controllo del prototipo e dei test. Il codice assumeva le stesse colonne per ogni griglia (`_GRID_METRIC_PREFIXES`): la sede ha un blocco `location` suo nel config (griglia + tre atlanti, obbligatorio) e le sue colonne in coda, dopo quelle di tutte le griglie.

**Implementazione (07-10-26, a richiesta esplicita dell'utente di andare in produzione)**: `src/features/lesion_location.py` (mappa delle categorie e frazioni), collegato in `src/features/lesion.py`; `location` nel config e in `LesionMetadataConfig`; report con la distribuzione per categoria. Scelte non ovvie: (1) il denominatore è la lesione dentro il brain mask, con o senza `correct_out_of_brain`, quindi con la correzione attiva è `lesion_volume_voxels_2mm`; (2) la parità nell'etichetta prevalente si risolve con l'ordine delle categorie (infratentoriale prima): era la proposta e l'utente non l'ha contestata, ma non l'ha neppure confermata esplicitamente, resta una convenzione facile da cambiare (`LOCATION_CATEGORIES`); (3) l'allineamento rifiuta un atlante che non sia una mappa di voxel intera sulla griglia, e controlla che il baricentro di ogni etichetta Left/Right stia dal lato giusto (il controllo che un flip sbagliato rompe); (4) la regola dei ventricoli cerca `Lateral Vent` perché l'XML di HO scrive "Left Lateral Ventrical". Verifica: la mappa delle categorie costruita da `src/` coincide voxel per voxel con quella del prototipo (cortico = `cortex_only` + confine).

**Run di produzione (07-10-26, 12:08, 32 min 24 s, `overwrite` solo in una copia del config)**: `assets/metadata/lesion_metadata.csv` ricalcolato per tutti i 5853 soggetti, 18 colonne. Le 10 colonne preesistenti sono identiche al csv di HEAD in 5853/5853 righe per ciascuna colonna; le 8 nuove coincidono col prototipo indipendente (`tmp/lesion_location/07_cohort_counts.py`) in 5853/5853 righe per ciascuna. 4 soggetti senza sede (nessun voxel dentro il brain: `sub-STUNIPD0558`, `sub-STUKLFR0671`, `sub-STUKE0146`, `sub-STUKE0201`). Dominante: `white_matter_only` 2746, `cortex_only` 1903, `infratentorial` 645, `subcortical_gray` 507, `unlabeled` 27, `cortex_white_boundary` 21. Il csv precedente (30-09-26) era identico per le 10 colonne, quindi nessuna misura già esistente è cambiata. `participants.csv` non è stato rigenerato: le colonne di sede non sono in `copy_columns` di `enrich_metadata`.

**Non deciso**: soglie di coinvolgimento e di "pura" (`open_problems.md`).

---

## 07-10-26 — Sede della lesione: classificazione sulla griglia a 2 mm, 1 mm come controllo; prima misura sull'intera coorte

**Decisione (OK dell'utente, 07-10-26)**: le frazioni per categoria si calcolano sulla **griglia a 2 mm** (quella di produzione); la griglia a 1 mm resta solo un controllo. **Scartato**: classificare a 1 mm. Motivo: per WashU/UKLFR (e probabilmente NEMESIS_T0/SFB936) le maschere a 1 mm sono ricampionamenti delle originali (2 mm / 1,5 mm) con scarti di 0,5-1,2 mm in y/z e volume ×1,09 / ×0,85, mentre a 2 mm ricostruiscono l'originale; le PSP frazionarie perdono voxel a 1 mm con `> 0,5`.

**Popolazione**: tutte le 5853 maschere in `lesion_metadata.csv` sono state calcolate; si classificano **5845**, cioè fuori solo le 8 righe di `excluded_subjects.csv` con `scope = all`. Le 14 righe con `scope = sdc-streamline` hanno lesioni valide (la loro esclusione riguarda solo la matrice SDC streamline) e restano. Interpretazione mia di "escludendo excluded_subjects.csv", da confermare. Nessuno dei 5845 ha 0 voxel dentro il brain a 2 mm; 27 hanno meno di 5 voxel (mediana 434).

**Controlli sull'intera coorte (tutti i 5853, entrambe le griglie)**: volume dentro il brain mask = volume di produzione 5853/5853; frazione fuori dal brain = produzione 5853/5853; somma delle categorie = volume 5853/5853. Lato dell'atlante = `lesion_side_2mm` in 5465/5483 decidabili (68 `both` e 7 vuoti non decidibili), 1 mm 5493/5511; con L/R scambiati l'accordo crolla a 18/5483 (il controllo può fallire). Le 18 discordanze a 2 mm non sono state esaminate.

**Misurato (2 mm, n = 5845)**:
- Frazione media: corticale 0,309, sotto-corticale grigia 0,114, infratentoriale 0,103, bianca 0,444, ventricolo 0,004, non etichettato 0,026. Categoria dominante: bianca 2551, corticale 2117, infratentoriale 643, sotto-corticale 507, non etichettata 27. 121 lesioni hanno >20% non etichettato.
- Quota "pura" (frazione dominante ≥ t): 0,935 (t=0,5), 0,734 (0,6), 0,543 (0,7), 0,378 (0,8), 0,246 (0,9). Nessun plateau, il calo è graduale (−20, −19, −17, −13 punti): la sweep non indica una soglia naturale.
- Quota "coinvolta" (frazione > m): a m=0 corticale 0,678, sotto-corticale 0,502, infratentoriale 0,180, bianca 0,870; a m=0,10: 0,557 / 0,270 / 0,126 / 0,813. A 0 la sotto-corticale è instabile (0,502 contro 0,270 a 0,10), conferma la proposta provvisoria di partire da >10%. A >10% le categorie anatomiche coinvolte sono 1 nel 30,3%, 2 nel 62,8%, 3 nel 6,7%.
- Per dataset (`out/cohort_dataset_summary.csv`) la composizione è molto diversa: dominante corticale UKLFR 64%, PASPORT 69%, UCL-UK 31%; lesioni con infratentoriale >10% UKLFR 0,1%, PASPORT 0%, contro 15-18% di UCL-UK/WashU/SFB936. Perché UKLFR/PASPORT non abbiano lesioni infratentoriali (selezione della coorte?) non è verificato.

**Sovrapposizione corticale/bianca di HO: misurata, e pesa.** Quota della lesione in voxel reclamati da entrambe: media 0,046, mediana 0,023, p90 0,119, max 0,70; 836 soggetti sopra 0,10. Dando la precedenza alla sostanza bianca invece che alla corticale: la categoria dominante cambia in 455/5845 (7,8%; per dataset da 1,8% a 10,7%); le lesioni "pure corticali" scendono da 905 a 511 a t=0,7 (da 1972 a 1496 a 0,5; da 200 a 101 a 0,9); "corticale coinvolta" a >0,10 da 3255 a 3098. La precedenza corticale > bianca, scelta il 06-10-26 senza misurarne l'effetto, è quindi la leva che più sposta la classe "corticale pura". Non è stata cambiata.

**1 mm contro 2 mm**: la categoria dominante differisce in 143/5845 (2,4%; per dataset 1,5-2,7%, per header LAS+90 2,6% / RAS −90 1,7% / RAS −91 2,5%); |Δfrazione| massima per soggetto: mediana 0,017, p95 0,072, max 0,48. L'etichetta (dominante, pura) differisce per 268 / 422 / 307 soggetti (4,6 / 7,2 / 5,3%) a t = 0,5 / 0,7 / 0,9. **Limite del controllo**: confronta due griglie della *stessa* maschera locale, non maschera locale contro originale (le originali a 2 mm di WashU non sono in locale), quindi non dice se il ricampionamento a 1 mm di WashU/UKLFR sposti la sede; dice solo che 1 mm e 2 mm raccontano la stessa storia per oltre il 97%.

**Conseguenza ancora vera**: le soglie e la precedenza corticale/bianca restano **non decise** (`open_problems.md`); nulla è in `src/`. Script e numeri completi in `tmp/lesion_location/` (`07_cohort_counts.py` → `out/cohort_counts.csv`; `08_cohort_summary.py` → `out/08_summary.txt`), locale, gitignored.

---

## 07-10-26 — Header RAS −90: nessuna traslazione in x rispetto alle originali; T1 non utilizzabili

**Fatto**: un agente sul cluster (sola lettura) ha trovato che per UNIPD/WashU le T1 sono native (nessuna in MNI, per nessun gruppo di header, in nessun dataset) e non esiste alcuna trasformazione native→MNI: il test T1→template non è eseguibile. Ha invece confrontato i baricentri delle maschere locali con le `manual_masks` originali (tabella in `open_problems.md`): per WashU la differenza in x ha mediana +0,05 mm (sd 0,98), quindi nessuna traslazione di 1 mm in x; in y/z restano scarti di 0,5-1,2 mm e il volume cambia (×1,09 WashU, ×0,85 UKLFR), compatibili con un ricampionamento da 2 mm (WashU) o 1,5 mm (UKLFR). Per PASPORT e PSP il confronto dà 0,000 (calibrazione: il metodo funziona).

**Decisione**: nessuna correzione dell'header; il problema "traslazione di 1 mm in x" è considerato non supportato (insieme al test sui bordi del cervello della voce precedente). Resta aperto l'effetto del ricampionamento a 1 mm per i 4 dataset RAS −90.

**Non verificato da me**: i numeri sono del report dell'agente; l'origine delle maschere locali per ciascun dataset (copia `lesion` di BCBToolKit) è dedotta dal `data_changelog.md`, non controllata sul server.

---

## 06-10-26 — Header RAS −90: test statistico inconclusivo, header lasciato come verità

**Decisione**: le 1032 maschere con header RAS −90 restano trattate col loro header (nessuna traslazione applicata).

**Fatto**: per 5852 maschere (una vuota esclusa) si sono spostati i soli voxel lesionali di −3..+3 mm lungo x (y e z come controlli negativi) contando quelli fuori dal brain mask del template a 1mm. Ipotesi testata: griglia vera = −91 (identica al template), quindi minimo atteso a −1 mm in x per i 4 dataset RAS −90. Osservato: minimo a +1 (UKLFR, SFB936), +2 (NEMESIS_T0), −1 (WashU); sul gruppo intero la frazione fuori dal brain è 0,0463 a −1, 0,0422 a 0, 0,0421 a +1. Gruppi di riferimento: WAKEUP (identico al template) minimo a +1, LAS +90 (4370) a 0 con stima sub-voxel −0,26. Assi di controllo: minimi a ±1-2 mm in y e z in più dataset (WashU y=2, z=2; NEMESIS_T0 y=1).

**Perché inconclusivo**: il criterio "fuori dal brain mask" ha risoluzione di circa ±1-2 mm, perché i cervelli normalizzati differiscono dal template di più di 1 mm e la distribuzione delle lesioni vicino al bordo non è simmetrica; un controllo che sbaglia di ±1 mm sul gruppo di riferimento e sugli assi di controllo non può rivelare uno spostamento di 1 mm. Non conferma la traslazione ipotizzata (il minimo non è a −1) ma non la esclude.

**Conseguenza ancora vera**: l'unico controllo decisivo resta la T1 normalizzata sul server o l'informazione su come sono state scritte le maschere (`open_problems.md`). Script in `tmp/lesion_location/06_header_shift_test.py` (locale, gitignored).

---

## 06-10-26 — Sede della lesione: atlanti FSL e sei categorie esclusive (prototipo in `tmp/`, non ancora in `src/`)

**Decisione**: ogni lesione si classifica per sede con tre atlanti FSL, in `assets/atlases/fsl/` (provenienza nel suo `README.md`): Harvard-Oxford corticale (48 etichette), Harvard-Oxford sotto-corticale (21), Cerebellum-MNIfnirt (28), tutti `maxprob-thr25` a 1mm e 2mm. Sei categorie esclusive per voxel dentro il brain mask, in ordine di precedenza: infratentoriale (`Brain-Stem` HO + cervelletto) > sotto-corticale grigia (talamo, caudato, putamen, pallido, ippocampo, amigdala, accumbens) > corticale > sostanza bianca (`Cerebral White Matter` HO) > ventricolo > non etichettato. Per lesione si tengono le **frazioni continue** per categoria (sui voxel lesionali dentro il brain mask) e la quota fuori dal brain mask a parte; le etichette discrete si derivano dopo, a soglie diverse. Il tronco encefalico intero conta infratentoriale. Anteriore/posteriore: **messo in stop**.

**Alternative scartate**: AAL3 (un solo file con cervelletto e vermis, ma costruito sul template Colin27, un MNI diverso: rischio di disallineamento proprio nel cervelletto); SUIT (spazio proprio, scomodo per lesioni già in MNI); Schaefer/Yan + Tian (già in locale, ma parcellazioni funzionali, e Tian non ha cervelletto né tronco); Arterial Territories Atlas (Liu et al. 2023, NITRC, CC-BY): rinviato, serve al circolo anteriore/posteriore, cioè alla parte in stop. JHU per la sostanza bianca profonda: non ora, HO la separa già.

**Misurato (prototipo, 48 soggetti = 6 per dataset, seed 0)**: gli atlanti sono LAS, i template RAS; la corrispondenza di griglia è un flip x con offset intero (181 a 1mm, 90 a 2mm), quindi il ricampionamento `nearest` tramite affine è senza perdite (conteggi per etichetta identici). Segno emisferico in coordinate mondo corretto per tutte le etichette Left/Right; un flip naive dell'array viene rilevato (20 violazioni per atlante). Controlli contro `lesion_metadata.csv`: frazione fuori dal brain 48/48; volume dentro il brain mask 48/48 (il volume di produzione è post-correzione); lato 46/46 sui decidibili (2 lesioni solo di tronco non hanno etichette L/R); categoria dominante uguale a 1mm e 2mm in 47/48. Volumi delle categorie a 1mm: corticale 1.035.841, sotto-corticale 63.699, infratentoriale 204.154, bianca 389.870, ventricolo 10.705, non etichettato 122.974 (brain mask 1.827.243). Sovrapposizioni tra atlanti: corticale/infratentoriale 2.440 voxel, corticale/sotto-corticale 485, corticale/bianca 109.621 (la fascia corticale HO è generosa al confine); sui 48 soggetti solo lo 0,08% dei voxel lesionali (max 1,9%) cade in voxel reclamati da più di una tra corticale/sotto-corticale/infratentoriale. L'effetto della sovrapposizione corticale/bianca sulle lesioni **non è misurato**.

**Soglie: non decise.** La letteratura non ha uno standard per la quota *della lesione* in una categoria: la pratica clinica classifica per coinvolgimento (sotto-corticale / cortico-sottocorticale / corticale) senza percentuali; le soglie quantitative trovate sono sulla frazione della *regione* danneggiata (>0, >1, >10, >20%), un'altra quantità (solo riassunti di ricerca, paper non letti per intero). Nel campione "pura" = 43/48 a soglia 50%, 31 a 60%, 23 a 70%, 13 a 80%, 8 a 90%, senza salto naturale. Da decidere con una sweep sull'intera coorte; proposta provvisoria: coinvolgimento a >10% della lesione (a >0% è instabile: la corticale tocca 38/48 contro 29/48).

**Conseguenza ancora vera**: (1) il gruppo di header RAS −90 (1032 maschere, vedi la voce SDC qui sotto) è trattato col suo header come verità; se fosse sbagliato di 1 voxel la categoria dominante cambia in 1 soggetto su 24 (max |Δfrazione| 0,08), aperto in `open_problems.md`. (2) Le 168 maschere PSP sono frazionarie e a 1mm la binarizzazione `> 0,5` ne perde voxel (`open_problems.md`): le frazioni di PSP a 1mm sono indicative. (3) Mesencefalo: il tentorio lo taglia, HO non permette di dividerlo, il tronco intero conta infratentoriale.

---

## 06-10-26 — Disconnessione per soggetto su due griglie (2mm e 1mm), come il volume lesionale

**Decisione**: `sdc_metadata.csv` ha le due colonne (`disconnection_load_voxels_<g>`, `disconnection_mean_<g>`) su **2mm e 1mm**, config `grids` come `compute_lesion_metadata.json`; `enrich_metadata.json` copia nel registro entrambe le griglie sia per la disconnessione sia per il volume lesionale (`lesion_volume_voxels_1mm` prima restava solo in `lesion_metadata.csv`). L'Embedding Explorer offre la scelta 1mm/2mm (default 2mm) per volume, disconnection load e mean disconnection.

**Perché**: la voce "Disconnessione per soggetto: carico/media" qui sotto aveva fissato la sola griglia 1mm senza alcun confronto con il 2mm: era la risoluzione nativa delle mappe (`res-1` nel nome del file), non una scelta di risoluzione deliberata, mentre la griglia di produzione del progetto è 2mm (voce 06-09-26 sulle griglie delle matrici). Richiesto esplicitamente di avere entrambe, non di sostituire l'una con l'altra.

**Misurato sull'intera coorte (5853 soggetti, 19m54s di run)**: il carico a 2mm ordina i soggetti quasi come quello a 1mm (Spearman 0,9999994); `8 × carico_2mm / carico_1mm` ha mediana 1,001, intervallo 0,989-1,017, quindi `nearest` a 2mm sottocampiona ma la mappa è abbastanza liscia da non cambiare il numero in modo sensibile; la media sul cervello coincide (rapporto mediano 1,000). Nessun soggetto sparisce nel ricampionamento: l'unico con carico 0 (`sub-STUKLFR0671`) è 0 su entrambe le griglie, a differenza del volume lesionale dove una lesione piccola può azzerarsi a 2mm.

**Conseguenza ancora vera**: il `csv` è stato rigenerato con `overwrite: true` da una copia del config nella scratchpad; il config del repo resta `overwrite: false`. I valori sono a precisione piena, senza arrotondamento: il `round(…, 3)` introdotto in giornata è stato tolto (a 3 decimali la media a 1 mm aveva 229 valori distinti su 5853 e 26 soggetti a `0.000`; senza, 5853 distinti) e il csv è stato ricalcolato su entrambe le griglie (20m25s). I nomi delle colonne dell'app (`DEFAULT_GRID`, `grid_column`, `available_grids` in `src/analysis/embedding_coloring.py`) sostituiscono i vecchi `*_volume_grid*`: nessun alias.

---

## 06-10-26 — Criteri di esclusione dalle matrici: nessuna esclusione per lesione piccola, soglia > 30% fuori dal brain

**Decisione**: (1) le lesioni piccole **non** si escludono: anche una lesione focale o minima può avere conseguenze cliniche gravi, quindi il volume non è un proxy di rilevanza clinica; per volume si scarta solo la maschera vuota (`empty_mask`, 3 soggetti). Il motivo `lesion_too_small` resta nel vocabolario ma non è usato. (2) Si escludono i soggetti con **più del 30%** dei voxel di lesione fuori dalla maschera cerebrale (`out_of_brain_fraction_2mm`, misurata prima dell'azzeramento), motivo `out_of_brain_fraction_too_high`.

**Verificato su `lesion_metadata.csv`/`excluded_subjects.csv`**: 5 soggetti sopra il 30%, tutti e soli quelli esclusi per questo motivo (frazione minima 0,41); tra i non esclusi il massimo è esattamente 0,30, quindi la soglia è stretta (`>`). Tra gli inclusi il volume minimo a 2 mm è 1 voxel, 122 soggetti stanno a 10 voxel o meno.

**Perché**: la voce del 29-09-26 ("Esclusione dei soggetti: lista curata a mano al posto delle soglie in config") spiega perché non esiste una soglia automatica sui dati (nessun salto naturale); la 30% è un criterio di analisi applicato a mano quando si compila il config, non un parametro di pipeline. Sotto la soglia il soggetto resta; i voxel fuori dal brain sono azzerati solo con `correct_out_of_brain: true`, flag che resta configurabile (`true` o `false`) in `build_lesion_matrix.json`.

**Config ripristinato nella stessa sessione**: `build_lesion_matrix.json` aveva `excluded_subjects_path` assente (tolto da `4b297d3`) e due chiavi morte `min_lesion_volume_voxels`/`max_out_of_brain_fraction` a `null`; il loader sollevava `missing required field 'excluded_subjects_path'`. Chiavi morte cancellate, `excluded_subjects_path` rimesso.

**Conseguenza ancora vera**: la regola è documentata in `docs/dev/metadata.md` ("Criteri di esclusione adottati") e `docs/guides/metadata.md`; la pipeline non la applica, quindi un soggetto nuovo sopra il 30% entra in matrice finché non è aggiunto a mano al config.

---

## 06-10-26 — Disconnessione per soggetto: carico/media come analogo del volume lesionale

**Decisione**: `assets/metadata/sdc_metadata.csv` (nuova pipeline `compute_sdc_metadata.py`, `src/features/sdc.py::compute_sdc_metadata`) misura, per ogni soggetto con disconnettoma (5853/5853), due colonne sulla griglia 1 mm: `disconnection_load_voxels_1mm` (somma della probabilità di disconnessione sui voxel dentro il cervello) e `disconnection_mean_1mm` (la stessa somma divisa per il numero di voxel cerebrali, costante di griglia — le due ordinano i soggetti in modo identico). `enrich_metadata.py` le copia in `participants.csv` (blocco `sdc_metadata`, stesso meccanismo di `lesion_metadata`, join stretto su `has_sdc`); l'Embedding Explorer le offre come due bottoni di colore, scala lineare.

**Alternative scartate**: volume sogliato a `p > 0.5` (la soglia che il pannello "Disconnessione per cluster" dell'app già usa — su 200 soggetti ordina quasi come la somma, Spearman 0,993, ma è una soglia in più da giustificare e introduce zeri assenti dalla somma); `n_nonzero_voxels` di BCBToolKit (misura quanto si *diffonde* la disconnessione, non quanta ce n'è: il minimo non nullo è costante a 1/178, un solo donatore su 178, quindi conta qualunque traccia — mediana 36% del cervello, fino al 91%); `map_mean_nonzero` (intensità con denominatore per-soggetto, non un carico); leggere `mapstats.tsv` di BCBToolKit invece di aprire i NIfTI (`map_sum` coincide al decimale col ricalcolo, verificato su 5 soggetti, ma non è mascherato sul cervello e non permette soglie).

**Scoperta corretta prima di entrare in `src/`**: le mappe disconnettoma non condividono un reticolo di voxel. Censimento sull'intera popolazione (5853 header, letti senza aprire i dati): 3 affine distinti per dataset — LAS con offset x `+90` (UCL-UK/PASPORT/PSP, 4370 soggetti), RAS con `-90` cioè traslato di 1 voxel (UKE-SFB936/UKLFR/NEMESIS_T0/WashU, 1032), RAS con `-91` identico al template MNI (UKE-WAKEUP, 451). Un primo prototipo assumeva uno specchio fisso dedotto da un campione di 6 soggetti per caso in maggioranza LAS: corretto per 4370, speculare per gli altri 1483, senza errore (`.claude/lessons_learned.md` #40). Ogni mappa viene ora portata sulla griglia di riferimento col **suo** header (`resample_to_img`, `nearest`), mai con un flip o un'identità presunti.

**Verificato**: somma ricalcolata contro `map_sum` di BCBToolKit, scarto 0.0 su 5 soggetti; riallineamento verificato con un calcolo geometrico indipendente per gruppo di header, scarto 0.0 su 12 soggetti (4 per gruppo); quota di massa fuori dal cervello misurata su 400 soggetti casuali (mediana 0,80%, max 8,9%) invece di stimata sui 5-6 soggetti del prototipo iniziale. Run di produzione: 5853/5853 soggetti, 18m24s, nessun NaN.

**Conseguenza ancora vera**: scala **lineare**, non log come il volume — misurato sull'intera coorte, asimmetria del carico 1,5 e massimo/mediana 7,6, contro 4,1 e 97 per il volume lesionale; un log sovra-correggerebbe (asimmetria del log10 -0,8). Un carico di 0 è un valore vero (nessuna disconnessione), non un "missing" come il volume a 0 sulla griglia 2mm.

---

## 06-10-26 — Forzatura del lato geometrico (WashU) spenta; controlli sulle immagini sui 15 disaccordi

**Decisione**: `geometric_override_datasets` in `config/pipelines/enrich_metadata.json` da `["UNIPD/WashU"]` a `[]`, `enrich_metadata` rilanciato: cambiano esattamente le 11 righe WashU (`lesion_side` e `lesion_side_source` tornano al valore del tsv, `clinical`), nient'altro. La funzione resta nel codice, spenta (testata, riattivabile).

**Perché**: la voce precedente mostra che i test comportamentali (ARAT, 9HPT) danno ragione all'etichetta in 6 degli 8 casi decidibili: forzare la maschera scriveva il lato sbagliato nella maggioranza dei casi. **Alternativa scartata**: tenere la forzatura accesa in attesa di prove sulla T1: le prove sulle T1 non sono arrivate (sotto).

**Controlli sulle immagini, svolti da un agente sul cluster (sola lettura, T1 non presenti in locale)**:
- lesione nativa e maschera MNI stanno dallo stesso lato in tutti gli 11 WashU (`sform` e `qform` concordi): la normalizzazione non inverte;
- nessuna proprietà degli header delle T1 native (orientamento RAS/LAS, segno del determinante, software di conversione, scanner) distingue gli 11 da 20 controlli concordi (8 RAS e 3 LAS contro 16 e 4);
- contrasto maschera/specchio sulla T1 in MNI (griglia a 2 mm): controlli tra -0,18 e +0,11 (mediana -0,05); 10 degli 11 dentro quell'intervallo, solo `sub-STUNIPD0187` a +0,51. Non discrimina;
- le nostre maschere locali sono l'output SDC a 1 mm (`features/.../lesion/<sub>/..._res-1_...`), non le `manual_masks` del server, che sono sul reticolo originale a 2 mm (circa un ottavo dei voxel); i 15 md5 locali coincidono con i file `res-1` (riferito dall'agente). Il confronto con il server mostra `sub-STUKLFR0403`: maschera manuale a sinistra (7300 voxel; lato dell'etichetta e dell'afasia), maschera SDC a destra (27984 voxel). Per gli 11 WashU manuale e SDC stanno dallo stesso lato;
- sette soggetti WashU (`0222`, `0179`, `0187`, `0216`, `0233`, `0242`, `0251`) hanno la T1w con identici `AcquisitionTime` (11:31:53.6725), orientamento DICOM, scanner (Prisma_fit) e shape: probabilmente la stessa immagine assegnata a più soggetti. Non verificato sui dati.

**Conseguenza ancora vera oggi**: i controlli sulle immagini non decidono il lato. Resta un'ipotesi non verificata sul dove nasca l'inversione per gli 11 WashU. Aperti: confronto manuale/SDC su tutti i soggetti (controllo E), identità delle 7 T1 (controllo F), maschere capovolte nelle matrici.

## 06-10-26 — Controlli E e F: il passaggio SDC non spiega gli 11 WashU; le "7 T1 identiche" sono un artefatto di metadato

**Fatto**: i due controlli lasciati aperti dalla voce precedente, eseguiti da un agente sul cluster (sola lettura, T1 non presenti in locale).

**Controllo E** (lato world di manuale vs SDC, su ogni soggetto con entrambe le maschere in MNI): WashU 1/195 discorde (`sub-STUNIPD0094`), UKLFR 3/673 (`sub-STUKLFR0253`, `0403`, `0463`), PSP 0/168, PASPORT 0/83; UKE 0 soggetti con entrambe le maschere disponibili sul server; `NEMESIS_T0` non esiste come cartella. MD5 dei 15 file locali contro l'SDC (`res-1`) del server: match su tutti e 15 — confermato su tutta la popolazione, non solo sul campione, che i file locali sono l'output SDC e non le `manual_masks` originali.

**Conseguenza**: il passaggio SDC inverte il lato raramente (0,2-0,5% dove misurabile) e **non per nessuno degli 11 WashU in disaccordo** (`sub-STUNIPD0094` non è tra gli 11). Non è il meccanismo dell'inversione.

**Controllo F** (identità delle T1 con `AcquisitionTime`/orientamento/scanner identici): il gruppo da 104 soggetti (che includeva le 7 segnalate) condivide un timestamp **placeholder** nel JSON ma ha dati anatomici tutti distinti (md5 e array diversi per ogni coppia) — un artefatto di metadato statico, non immagini duplicate. Trovate invece, per caso, due coppie di T1 realmente identiche byte per byte ma con `lesion_roi` diverso: `sub-STUNIPD0053`/`0060` e `sub-STUNIPD0066`/`0077`.

**Perché conta**: `sub-STUNIPD0077` è uno degli 11 WashU in disaccordo (maschera capovolta secondo il test comportamentale di questa stessa giornata). Condividere la T1 nativa con un altro soggetto (`0066`), con una maschera di lesione diversa sopra, è un'anomalia di dati reale nel sottoinsieme che ci interessa — non spiega di per sé l'inversione, ma non è capita.

**Non verificato**: se le due coppie di T1 duplicate siano uno scambio di identità tra soggetti o un placeholder riusato quando lo scan originale manca. Nessuna conseguenza per la decisione di spegnere la forzatura (voce precedente): resta valida.

## 06-10-26 — Verifica del lato forzato (WashU) con test comportamentali; soglia a 1 mm verificata; calibrazione rifatta

**Cosa è stato fatto**: (1) verificata l'ipotesi della voce del 05-10-26 (sbaglia l'etichetta clinica, non la maschera), senza T1 locali, con deficit controlaterali presenti nei tsv; (2) esteso il controllo ai disaccordi degli altri dataset su dati completi; (3) rifatta la calibrazione della soglia, a 2 mm e a 1 mm.

**Metodo e risultati del punto 1-2**: WashU `ARAT_L/R` e `9HPT_L/R`: la mano più debole indica il lato della lesione (controlaterale). Calibrazione del test sui 151 soggetti con etichetta e maschera concordi: ARAT 90/92 (98%), 9HPT 102/119 (86%, valore alto = meglio). UKE: `NIHSS_5a/5b` + `6a/6b` sui 409 concordi, 259/273 (95%). UKLFR: afasia (`NIHSS_9 ≥ 1`) nei destrimani con etichetta e maschera concordi, lesione sinistra in 128/129 (99%). Applicati ai 15 disaccordi pieni: **etichetta giusta in 8, maschera giusta in 3, non decidibili 4** (WashU: 6/2/3; UKE e UKLFR: 2/1/1). Sui 9HPT degli 11 WashU, 5 dei 6 informativi indicano l'etichetta: sotto "maschera giusta" la probabilità di quel risultato è ~3e-4 (accuratezza di base 86%, indipendenza assunta). In WashU il disaccordo è associato alla manualità (mancini 5/16, destrimani 6/146, Fisher p = 0,0016). Numeri completi dei disaccordi a 2 mm: WashU 11/162, UKLFR 2/700, UKE-WAKEUP 2/411, PSP 0/94, UKE-SFB936 0/53 (i campioni citati prima, 1/120 e 1/95, erano stime).

**Conclusione**: l'assunzione della forzatura è contraddetta dai dati nella maggior parte dei casi decidibili: la regola `geometric_override_datasets` scrive il lato sbagliato in 6 casi su 8 decidibili WashU. Non rimossa in questa voce: la decisione spetta all'utente (vedi `.claude/open_problems.md`). Conseguenza non voluta: le maschere capovolte sono nelle matrici (lesione, SDC).

**Soglia a 1 mm** (`calibrate_lesion_side_threshold.py`, verità = `participants.csv` salvato prima della forzatura, con gli 11 ancora `clinical`): 2 mm con tutti e 5 i dataset, 1445 soggetti, soglia 0.20 → **97,4%** (identico alla calibrazione del 28-09-26; ottima 0.28, 97,5%). Senza PSP, sugli stessi 1350 soggetti: 97,3% a 1 mm e a 2 mm, **stesso lato per tutti i 1350**, 97,4% a 0.28 su entrambe. Senza le 15 inversioni piene (non correggibili da nessuna soglia) 98,4%. La soglia vale quindi a 1 mm. La classe `both` resta debole (24 etichette cliniche, 3 predette).

**Script rotto, ripristinato**: `calibrate_lesion_side_threshold.py` importava `KNOWN_LESION_SIDES` da `src/features/lesion.py`, cancellata il 29-09-26 (commit `cf6e1fe`) e mai ripristinata: falliva all'import e nessun test lo copriva. Ripristinata la costante, aggiunto `tests/unit/test_calibrate_lesion_side_threshold.py` (5 test).

## 05-10-26 — `lesion_side` di WashU: dove clinico e maschera sono opposti, il registro prende la geometria

*(Spenta il 06-10-26: vedi la voce sopra. Il testo che segue descrive la decisione com'era allora.)*

**Decisione**: in `participants.csv`, per i dataset di `geometric_override_datasets` (oggi solo `UNIPD/WashU`, `config/pipelines/enrich_metadata.json`), un soggetto con lato clinico `left`/`right` e lato in `lesion_side_2mm` l'opposto riceve il lato **geometrico** e `lesion_side_source = "geometric"`. È l'unica eccezione a "un valore clinico non si sovrascrive". Un `both` geometrico non scatta mai.

**Misurato**: su 162 WashU con lato clinico, 11 (6,8%) sono opposti alla maschera, 6 `left`→`right` e 5 `right`→`left`, tutti con `|laterality_index_2mm| ≥ 0,95`. Le 195 maschere WashU hanno header identico (RAS, affine con origine -90, shape 182×218×182). Negli altri dataset il tasso è quasi nullo (UKLFR 0/120, UKE 1/120, PSP 1/95, campioni di `.claude/open_problems.md`). Applicato alla run del 05-10-26: i 11 soggetti sono `sub-STUNIPD0002/0008/0026/0056/0077/0131/0147/0151/0179/0187/0222`.

**Perché**: l'ipotesi è che sbagli l'etichetta clinica (errore alla fonte, magari una convenzione di visualizzazione radiologica), non la maschera. Il motivo per preferire questa ipotesi: un capovolgimento delle maschere sarebbe sistematico per un processo comune a tutto il dataset, non confinato a 11 soggetti in entrambe le direzioni. **Non è verificata sulla T1** (verificata con test comportamentali il 06-10-26: la contraddicono, vedi voce successiva).

**Alternative scartate**:
- *Elenco di ID in config*: va rifatto a mano a ogni cambio delle maschere e non dice perché quei soggetti. La regola si rilegge da `lesion_metadata.csv` a ogni run.
- *Regola globale su tutti i dataset*: UKE e PSP hanno un caso ciascuno, mai indagati; un default globale cambierebbe il registro su dati che nessuno ha guardato.
- *Lasciare il lato clinico e usare la geometria solo dove manca* (comportamento precedente): le inversioni restavano nei plot per `side` e nella descrizione dei cluster.

**Conseguenza ancora vera oggi**: `lesion_side_source = "clinical"` non indica più tutte le etichette del tsv. `src/pipeline/calibrate_lesion_side_threshold.py` usa quelle righe come verità, quindi non vede più le 11 inversioni: l'accordo che calcola ora è più alto del 97,4% (su 1445, inversioni incluse) della voce del 28-09-26 e non è confrontabile. Se la T1 mostrasse che sbaglia la maschera, la lista va svuotata e la run rifatta.

---

## 30-09-26 — Cache condivisa e ricampionamento single-pass per le mappe anatomiche in Embedding Explorer

**Decisione**: `BinaryMaskStore` (`src/analysis/anatomical_maps.py`) passa da precalcolo per-singola-run a cache in-memoria condivisa fra tutti i run/cluster aperti nella stessa sessione app: per ogni soggetto tiene solo gli indici dei voxel sopra soglia (lesione, o disconnessione >0.5), riempiti una sola volta per soggetto indipendentemente da quanti run/cluster lo richiedono. `_GridResampler`, stessa classe, calcola una sola volta la corrispondenza voxel→voxel fra griglia sorgente e reference (invece che per ogni soggetto) — bit-identico a `resample_to_img`, verificato con test dedicato. Nuovo flag `--preload` in `src/pipeline/embedding_app.py`: all'avvio, in background, legge tutti i soggetti di tutti i run di clustering (maschere lesionali sempre, disconnettomi SDC solo per i run sdc) e riempie i due store una volta per l'intera sessione. Inoltre, `_masked_for_view_colorbar` (`src/analysis/embedding_app.py`) rimuove il grigio dalla colorbar interattiva della mappa "probabilità media": pre-azzera i voxel sotto soglia (0.02) e passa un epsilon a `view_img` invece della soglia reale.

**Perché**: con un precalcolo per-singola-run, ogni cluster di ogni run ripeteva il ricampionamento e il filtraggio per voxel per gli stessi soggetti già visti in run precedenti nella stessa sessione — costo che cresce con il numero di run aperti, non con il numero di soggetti distinti. Condividere la cache per soggetto (indipendente dal run) elimina il lavoro ripetuto: con `--preload`, qualunque cluster di qualunque run mostra la mappa in ~1s. Sul colorbar: `view_img` di nilearn colora di grigio opaco tutto l'intervallo sotto soglia quando gli si passa la soglia reale, e questo comportamento non è configurabile dai suoi parametri pubblici — pre-azzerare a monte e passare un epsilon aggira il problema senza patch a nilearn.

**Alternative scartate**: mantenere il precalcolo per-run e limitarsi a velocizzare il ricampionamento (`_GridResampler` da solo) — avrebbe comunque ripetuto il lavoro per ogni run sullo stesso soggetto, non risolvendo il caso reale (più run aperti in una sessione lunga).

**Conseguenza ancora vera oggi**: i due store (`BinaryMaskStore` per lesioni e per disconnettomi SDC) vivono per la durata del processo `embedding_app`, non per singola run — un riavvio dell'app senza `--preload` torna al comportamento lazy (primo accesso più lento, poi cache calda per quel soggetto). Bug noto e non corretto: il download PNG statico della mappa di disconnessione (`_download_disconnection_png`) usa sempre `_DISCONNECTOME_DISPLAY_THRESHOLD` anche in modalità "percent", dove dovrebbe usare `1e-6` come la vista interattiva.

---

## 30-09-26 — Lista delle esclusioni con `scope`: un soggetto può essere inutilizzabile in una sola rappresentazione

**Decisione**: `assets/metadata/excluded_subjects.csv` ha una colonna in più, `scope` (vocabolario chiuso: `all`, `lesion`, `sdc-parcellated`, `sdc-voxelwise`, `sdc-streamline`), e un nuovo motivo `all_zero_features` (la riga di feature del soggetto è tutta zero nella rappresentazione dello scope). `load_excluded_subjects(path, scope)` restituisce le righe `all` più quelle del proprio scope; lo scope è un argomento obbligatorio, senza default. `build_lesion_matrix.py` chiede `lesion`, `build_sdc_matrix.py` chiede `sdc-<representation>`. Prima riga scritta: `sub-STUKLFR0671` (`empty_mask`, `all` — maschera a 0 voxel, vuoto ovunque) più 14 soggetti `all_zero_features` / `sdc-streamline`, cioè 15 escluse da `s2.3-stream` (5853 → 5838).

**Perché**: 14 soggetti hanno il CSV streamline interamente a zero mentre la loro mappa di disconnessione voxelwise non è vuota (10.498–214.149 voxel, lesioni fino a 284 voxel). Non è un difetto del calcolo: `streamline_ratio` conta le streamline effettivamente intersecate, e in quei soggetti la lesione tocca solo la frangia probabilistica dei tratti (probabilità massima dell'atlante 0,001–0,55, contro 0,997–1,000 nei soggetti con streamline non nullo). Sono misure vere ("nessuna streamline tagliata"), inutilizzabili nello spazio dei tratti perché una riga tutta zero è massimamente distante da tutte le altre, ma validi nella matrice lesionale e in quella voxelwise. Una lista globale li avrebbe fatti sparire da entrambe.

**Alternative scartate**: (a) una lista di esclusioni per pipeline — due file che divergono; (b) uno scope grossolano `lesion`/`sdc` — un'esclusione `sdc` toglierebbe i 14 anche da `s2.4-vol`, dove hanno disconnessione reale; (c) non escludere in fase di build e toglierli a valle nel notebook — sposta la decisione fuori dall'artefatto, che non dice più da solo chi contiene.

**Conseguenza ancora vera oggi**: la garanzia "le matrici lesione e SDC escludono gli stessi soggetti per costruzione" vale ora per le righe `all`; una riga con scope stretto restringe volutamente il confronto a un solo spazio di feature, e `config.md` di ogni matrice registra lo scope usato (`excluded_subjects_scope`). La validazione del file copre l'intero file, non solo le righe dello scope richiesto, così un refuso destinato a un'altra matrice fa fallire anche questa.

---

## 30-09-26 — Streamline per tratto come terza rappresentazione SDC, nella track s2.x

**Decisione**: `build_sdc_matrix.json` accetta `representation: "streamline"`, che legge `sdc/<subject>/*_LF-lesion_atlas-yeh_hcp1065_streamline.csv` (colonne `tract,streamline_ratio`) in una matrice soggetti x 87 tratti di sostanza bianca — un valore per tratto, la quota delle sue streamline colpite. Nuovo builder dedicato (`src.features.sdc.build_sdc_streamline_matrix`), non un parametro di quello parcellato. Lista autoritativa dei tratti in `assets/atlases/sdc_labels/yeh_hcp1065_streamline.csv` (colonna `tract`, 87 righe), derivata dall'unione su tutti i 1734 file reali. Il dato appartiene alla track **s2.x** (disconnettoma), non s1.x, nonostante il nome `LF-lesion`: quello che misura è una disconnessione, cioè streamline interrotte dalla lesione, non danno diretto al tessuto. Prima sessione: `s2.3-stream`, 7 dataset (UCL-UK non ha questo CSV).

**Perché un builder separato**: lo schema non ha nulla in comune con i CSV parcellati — nessuna colonna `region_name`, e una sola colonna di valori invece delle 6 statistiche interscambiabili di `KNOWN_VALUE_COLUMNS`. Di conseguenza la config non espone né `atlas` né `value_column` per questa modalità: non c'è niente da scegliere, e un campo non letto è vietato (`code_standards.md` §5).

**Perché un tratto mancante solleva invece di valere 0.0**: è l'unica differenza di comportamento reale rispetto al builder parcellato, che riempie a `0.0` perché BCBToolKit omette davvero le regioni a overlap nullo. Questo file invece scrive **tutti** i tratti, zeri compresi: verificato su tutti i 1734 file dei 7 dataset, stessi 87 tratti nello stesso ordine, da 2 a 42 non nulli per soggetto. Un file incompleto è quindi troncato o corrotto, e riempirlo sarebbe il fallback silenzioso che `code_standards.md` §0 esclude.

**Alternative scartate**: (a) generalizzare `build_sdc_matrix` con nomi di colonna configurabili — mette un parametro che non varia quasi mai sul percorso caldo della rappresentazione usata da ogni run esistente, senza guadagno; (b) un secondo file di config (`build_sdc_matrix_stream.json`) accanto a quello voxelwise — scartata su richiesta, si cambia `representation` nello stesso file; (c) trattarlo come atlante parcellato aggiungendone solo il file di reference — impossibile, manca `region_name`; (d) allineare per posizione di riga, dato che l'ordine è stabile su tutta la coorte — l'ordine non è garantito dal formato (`lessons_learned.md` #3), e dopo il controllo di completezza il `reindex` per nome non può comunque riempire niente, solo riordinare.

**Conseguenza ancora vera oggi**: nessuna colonna viene mai scartata, nemmeno se costante su tutti i soggetti ammessi — stessa regola del parcellato, la colonna `j` deve sempre indicare lo stesso tratto. Il clustering su questa matrice gira sui 87 tratti grezzi, senza dim reduction (`reduced_data: false`, `reduction_method: "raw"`): 87 dimensioni sono già basse, quindi `n_components` non entra in gioco.

## 29-09-26 — Esclusione dei soggetti: lista curata a mano al posto delle soglie in config

**Decisione**: `min_lesion_volume_voxels` e `max_out_of_brain_fraction` sono usciti da `build_lesion_matrix.json` (e da `BuildMatrixConfig`, `build_lesion_matrix()`, `_filter_by_lesion_quality`, ora cancellata). Chi escludere dalle matrici di produzione è deciso **a mano**, guardando le distribuzioni in `assets/metadata/lesion_metadata.csv` dal notebook `lesion_quality.ipynb`, e scritto in `assets/metadata/excluded_subjects.csv` (`subject_id, dataset, reason, value`; vocabolario chiuso dei motivi: `empty_mask`, `lesion_too_small`, `out_of_brain_fraction_too_high`). Quel file è letto sia da `build_lesion_matrix.py` sia da `build_sdc_matrix.py`, quindi le due matrici escludono gli stessi soggetti per costruzione.

**Perché**: i dati non hanno un salto naturale su cui mettere una soglia. Su 5853 soggetti: 3 maschere a 0 voxel a 2 mm, 132 con volume ≤ 10 voxel, e una coda continua senza discontinuità; il test IQR per dataset (log1p, Tukey 1.5) ne segnala solo 3, un quantile fisso al 2% ne prende 115. Sulla frazione fuori dal brain, 234 soggetti sopra il 5%, 73 sopra il 10%, 5 sopra il 30%. Una soglia in un config sceglie un numero arbitrario su quella coda e lo applica a tutti i dataset insieme; la decisione è invece caso per caso e appartiene all'analisi, non alla config di una pipeline. Il `value` per ogni riga tiene la decisione verificabile a distanza di mesi: "sub-X escluso" non si può rivedere, "sub-X escluso a 2 voxel" sì.

**Alternative scartate**: (a) tenere le soglie e affiancarci la lista — due meccanismi di ammissione attivi insieme, con il rischio che una soglia dimenticata in un config escluda soggetti che il notebook aveva deciso di tenere; (b) una lista per pipeline (una per la matrice lesionale, una per l'SDC) — due file che divergono, e un confronto lesione/SDC che silenziosamente confronta due coorti diverse; (c) far generare la lista da uno script a partire da soglie — sarebbe la soluzione (a) con un passaggio in più. Reintroduce `excluded_subjects`, scartata la mattina dello stesso giorno (vedi `project_changelog.md`, voce su `lesion_metrics`): allora l'argomento era che editare un config e rilanciare una pipeline di minuti fosse più macchinoso che correggere la cella a mano; ora la lista non fa rilanciare niente (è letta dalle pipeline di matrice, non da `enrich_metadata`) e la correzione a mano non è più possibile, perché ogni run di `enrich_metadata` ricopia le colonne derivate dalle maschere.

**Conseguenza ancora vera oggi**: un file assente **solleva**, non significa "non escludere nessuno" — le due cose sono indistinguibili, e costruire una matrice di produzione con tutti i soggetti limite dentro è esattamente ciò che la lista esiste per evitare. Per dire "nessuna esclusione" si tiene il file con la sola intestazione. Ogni riga è validata contro il registro (ID inesistente, ID duplicato, `dataset` in disaccordo, motivo non registrato, `value` non numerico sollevano): il file è scritto a mano e i dati ridondanti scritti a mano divergono. Oggi il file contiene solo l'intestazione: nessuna esclusione è ancora stata decisa.

---

## 29-09-26 — Metriche dalle maschere: quattro per griglia, su due griglie, con la correzione applicata prima del conteggio

**Decisione**: `assets/metadata/lesion_metadata.csv` registra, per ogni soggetto con maschera e **per ogni griglia dichiarata**, quattro valori: `lesion_volume_voxels_<g>`, `out_of_brain_fraction_<g>`, `laterality_index_<g>`, `lesion_side_<g>`. Le griglie in produzione sono due, `1mm` e `2mm`. Ordine di calcolo per ogni maschera e ogni griglia: ricampiona se e solo se la griglia della maschera differisce, binarizza, **misura la frazione fuori dal brain sulla maschera grezza**, azzera i voxel fuori dal brain (`correct_out_of_brain: true`), poi conta volume e lateralità. Un solo passaggio: una lettura da disco per soggetto, un ricampionamento per griglia.

**Perché due griglie**: le maschere manuali sono tutte a 1 mm (verificato sugli header di tutte e 5853: `182x218x182`, voxel `1.0`), il template di produzione è a 2 mm con ricampionamento `nearest`, che tiene un voxel su 8. Il conteggio a 2 mm è quindi un sottocampionamento in cui una lesione minuscola può ridursi o sparire; a 1 mm è nativo ed esatto. Confrontare i due volumi è l'unico modo per dire se una maschera a 0 voxel a 2 mm (3 soggetti: `sub-STUKLFR0671`, `sub-STUKE0146`, `sub-STUKE0201`) sia vuota nel file originale o abbia perso la lesione nel ricampionamento.

**Perché la frazione è pre-correzione e il resto post**: la correzione porta la frazione a 0 per costruzione, quindi misurarla dopo renderebbe inutile la sola colonna che serve a decidere chi escludere. Viceversa un voxel fuori dal cervello non è lesione: non va contato nel volume e non deve poter decidere il lato. Verificato che il caso è reale: senza correzione, 3 voxel di destra fuori dal brain contro 2 di sinistra dentro danno indice −0.2 e lato `right`; con la correzione, +1.0 e `left`.

**Alternative scartate**: contare senza correzione (contare voxel fuori dal cervello non ha senso, e il volume divergerebbe da quello di una matrice costruita con `correct_out_of_brain: true`); il lato solo sulla griglia a 2 mm, quella su cui la soglia è calibrata (a 1 mm il conteggio è esatto, quindi è la griglia *migliore* per attribuire il lato, non la peggiore — tenerle entrambe permette di ricalibrare senza rileggere le maschere); salvare il volume in mm³ (indipendente dalla griglia ma non risolve la perdita per sottocampionamento).

**Verificato dopo la prima run completa (30-09-26)**: per 5150 dei 5853 soggetti la griglia a 1 mm **non porta informazione in più**. `manual_masks/` contiene la lesione già ricampionata da BCBToolKit su griglia 1 mm (`docs/dev/retrieval.md`), e per i dataset segmentati originariamente a 2 mm i voxel risultano costanti in blocchi 2x2x2 allineati (fase `(1,1,1)`, zero blocchi misti, verificato su tutti i soggetti): UCL-UK, UKLFR, WashU, NEMESIS_T0, SFB936. Il conteggio a 2 mm ricostruisce esattamente la maschera nativa, quindi per loro nessuna lesione può sparire nel sottocampionamento. Le due colonne differiscono davvero solo per i 702 soggetti di PASPORT, PSP e WAKEUP. **Il disegno resta giustificato**: dei 4 soggetti con volume 0 sulla griglia di produzione, solo `sub-STUKLFR0671` ha la maschera davvero vuota; `sub-STUKE0146` (8 voxel) e `sub-STUKE0201` (3 voxel) hanno una lesione reale persa a 2 mm, ed entrambi stanno in WAKEUP, cioè fra i 702. Il quarto, `sub-STUNIPD0558`, arriva a 0 per la correzione (99,94% di lesione fuori dal cervello), non per la risoluzione. La ridondanza cade quindi esattamente dove è inevitabile, e l'informazione dove serve.

**Conseguenza ancora vera oggi**: `side_threshold=0.20` è calibrata **solo sulla griglia a 2 mm** (97.4% di accordo su 1445 soggetti, voce del 28-09-26) e viene applicata anche a 1 mm, dove non è verificata: `lesion_side_1mm` è indicativa finché `scripts/calibrate_lesion_side_threshold.py --grid 1mm` non viene eseguito. Il piano mediano escluso da entrambi gli emisferi è spesso 1 mm su una griglia e 2 mm sull'altra (la griglia a 1 mm ha 91 fette a sinistra e 90 a destra, quella a 2 mm 45 e 45), quindi per una lesione quasi tutta mediana i due indici non sono interscambiabili. `out_of_brain_fraction` è `NaN`, non `0.0`, per una maschera vuota: 0.0 metterebbe una maschera vuota tra i soggetti più puliti della distribuzione usata per scegliere le esclusioni. Nel registro `participants.csv` arrivano solo `lesion_volume_voxels_2mm` e `lesion_side`: il volume a 1 mm, le due frazioni e i due indici vivono solo nel csv, che è quello che legge il notebook.

---

## 29-09-26 — `correct_out_of_brain`: correggere (azzerare i voxel) invece di escludere il soggetto

**Decisione**: `build_lesion_matrix.json`/`BuildMatrixConfig` guadagna `correct_out_of_brain` (bool, default `false`) — invece di escludere un soggetto contaminato (`max_out_of_brain_fraction`), azzera i suoi voxel di lesione fuori dalla maschera cerebrale (`src/features/lesion_correction.py::zero_out_of_brain_voxels`) e lo mantiene nella matrice, con `lesion_volume_voxels` ricalcolato dai dati corretti. Applicato in `src/features/lesion.py::_apply_out_of_brain_correction`, eseguito **prima** di `min_lesion_volume_voxels` così quel filtro vede il volume già corretto, non quello grezzo. **Mutuamente esclusivo con `max_out_of_brain_fraction`**: entrambi attivi sollevano `ValueError`, sia a config-load (`src/analysis/build_config.py`) sia dentro `build_lesion_matrix` stesso (`lessons_learned.md` #2, validazione non ancorata a un solo punto di chiamata).

**Perché**: combinare le due strategie sullo stesso soggetto sarebbe ambiguo — se si corregge prima e si esclude dopo, la soglia `max_out_of_brain_fraction` controllerebbe una frazione già portata a ~0 dalla correzione, diventando silenziosamente inutile; se si esclude prima sulla frazione grezza, la correzione non avrebbe più nulla da fare sui sopravvissuti in caso di soglie strette. Richiesto esplicitamente dall'utente come alternativa all'esclusione pura introdotta nella voce del 28-09-26 in questo stesso file.

**Alternativa scartata**: combinare i due meccanismi (esclusione sulla frazione grezza + correzione sui sopravvissuti). Scartata su richiesta esplicita dell'utente per restare più semplice e priva di ambiguità — un solo criterio di ammissione attivo alla volta, mai due che interagiscono implicitamente.

**Conseguenza ancora vera oggi**: `config/pipelines/build_lesion_matrix.json` ha `correct_out_of_brain: false` — comportamento di produzione invariato, nessuna matrice già costruita è affetta (i thresholds/la correzione contano solo per run non ancora fatte, stessa nota della voce del 28-09-26). Il vecchio script standalone `scripts/lesion_fix.py`, che faceva la stessa correzione ma non era mai integrato in nessuna pipeline, è stato eliminato in questa stessa sessione (vedi `project_changelog.md`).

**Aggiornamento, stessa giornata**: la mutua esclusione descritta sopra **non esiste più**, perché `max_out_of_brain_fraction` è stata rimossa del tutto (voce "Esclusione dei soggetti: lista curata a mano", in cima a questo file). `correct_out_of_brain` resta, come unico uso di `brain_mask_path` in `build_lesion_matrix.json`, ed è attiva anche in `compute_lesion_metadata.json` (lì `true`). La ragione per cui le due strategie non andavano combinate resta valida e spiega perché non è stata tenuta una soglia accanto alla lista.

---

## 28-09-26 — `lesion_side` geometrico: soglia di bilateralità 0.20, dal protocollo standard di letteratura

**Decisione**: implementato il fallback geometrico per `lesion_side` (per i soggetti privi di dato clinico), con soglia di bilateralità **0.20** sul laterality index `LI = (left_voxels - right_voxels) / (left_voxels + right_voxels)` — la formula/soglia standard in letteratura per lesioni/attivazione fMRI (LI-toolbox di Wilke & Lidzba; protocollo Rorden/GigaScience per lesioni stroke), non calcolata da zero per questo progetto.

**Perché**: prima di questa sessione la variabile era esplicitamente non implementata (`docs/dev/metadata.md`), in attesa di una calibrazione della soglia contro dati clinici veri (`code_standards.md` §0 — mai un valore "dall'aria plausibile"). Calibrazione eseguita (`scripts/calibrate_lesion_side_threshold.py`) su 1445 soggetti con `lesion_side` clinico nei 5 dataset che lo hanno (`UNIPD/WashU`, `UNIPD/PSP`, `UKLFR/stroke_UKLFR`, `UKE/WAKEUP_acute`, `UKE/SFB936_ses01` - quest'ultimo onboardato nella stessa sessione, portando il set di calibrazione da 4 a 5 dataset): 0.20 riproduce il 97.4% delle etichette vere. Dettagli completi, matrice di confusione e letteratura in `knowledge/neuroimaging/lesion_laterality.md`.

**Alternativa scartata**: la soglia "ottimale" trovata per grid search sui nostri dati (0.36, accuratezza 97.5%, +2 soggetti su 1445 rispetto a 0.20). Scartata perché il guadagno è marginale e rischierebbe di overfittare sui soli 24 esempi di `both` (la classe bilaterale) disponibili nel set di calibrazione — usare il valore di letteratura resta anche più difendibile in caso di pubblicazione.

**Conseguenza ancora vera oggi**: la classe `both` resta debole a qualunque soglia testata (3/24 corretti anche alla soglia ottimale) - non un difetto della soglia scelta, un limite intrinseco del metodo per una lesione bilaterale che comunque pende leggermente da un lato nel conteggio voxel. `UNIPD/NEMESIS_T0` (onboardato lo stesso giorno, nessun `lesion_side` clinico) non riceve ancora il fallback: `build_lesion_matrix.json` non include questo dataset nella propria lista `datasets` (stesso gap già noto per `lesion_volume_voxels`, task separato non ancora fatto) - il fallback lo salta con un `WARNING`, non un errore, finché quella lista non viene estesa.

---

## 28-09-26 — `build_lesion_matrix.json` riportato alla griglia a 2mm, era scivolato a 1mm

**Decisione**: `reference_template_path`/`brain_mask_path` in `config/pipelines/build_lesion_matrix.json` passati da `tpl-MNI152NLin6Asym_res-1_*` (1mm) a `tpl-MNI152NLin6Asym_res-2_*` (2mm). Aggiornati anche i due path hardcoded nella sezione "Lesione fuori dal brain" di `notebooks/exploration/dataset_exploration.ipynb`, per restare sulla stessa griglia della produzione.

**Perché**: la voce del 06-09-26 in questo stesso file fissa la griglia a 2mm per `build_lesion_matrix.py` (e per `build_sdc_matrix.py` in modalità `voxelwise`), con alternative misurate e scartate esplicitamente. Lo swap del 23-09-26 da un singolo file paziente a un template versionato (`project_changelog.md`) ha però impostato `res-1` (1mm) — non una scelta di risoluzione deliberata, solo la prima opzione disponibile al momento di rendere il riferimento stabile — introducendo una deviazione silenziosa dalla griglia già decisa. Richiesto esplicitamente dall'utente ("voglio risoluzione a 2mm"), verificato prima di applicare che `res-2` T1w e brain mask condividano shape/affine (91×109×91, 2mm isotropo).

**Conseguenza ancora vera oggi**: `config/pipelines/build_sdc_matrix.json` (rappresentazione `voxelwise`) ha la **stessa** deviazione — `reference_template_path` è ancora su `res-1` — e non è stato toccato in questa sessione (fuori scope, riguarda solo `build_lesion_matrix.json`). Da allineare quando si torna a lavorare su quella pipeline. Nessun impatto su matrici già costruite (`data/derived/lesion_matrix/<sessione>/`): la griglia è fissata al momento del build, questo è solo un cambio di config per le run future.

---

## 28-09-26 — Filtro di qualità della lesione (volume minimo, frazione fuori dal brain): solo per `build_lesion_matrix.py`, non per `build_sdc_matrix.py`

**Decisione**: `build_lesion_matrix.py` guadagna due soglie opzionali di ammissione soggetto, entrambe `null` di default (nessun filtro): `min_lesion_volume_voxels` (esclude lesioni troppo piccole) e `max_out_of_brain_fraction` (esclude soggetti con troppi voxel di lesione fuori dalla maschera cerebrale MNI152, stessa logica di `scripts/lesion_fix.py`, richiede `brain_mask_path`). Entrambe calcolate in-run, dai dati voxel già caricati/binarizzati di quella specifica run (`src/features/lesion.py::_filter_by_lesion_quality`), non da `assets/metadata/participants.csv` — la cui colonna `lesion_volume_voxels` potrebbe riflettere una griglia/`binarize_threshold` di una run diversa. Un soggetto a 0 voxel di lesione ottiene `out_of_brain_fraction = 0.0` per convenzione esplicita (vacuosamente vero), mai `NaN`. I soggetti esclusi sono elencati in due nuove sezioni di `config.md`/`summaries/build_lesion_matrix/*/build_summary__*.md` ("Excluded by min_lesion_volume_voxels"/"Excluded by max_out_of_brain_fraction"), stesso schema già in uso per `group_filter`.

**Alternativa scartata**: implementare lo stesso meccanismo anche in `build_sdc_matrix.py`/`src/features/sdc.py`, come inizialmente richiesto. Scartata perché `sdc.py` risolve deliberatamente la presenza della lesion mask da `assets/metadata/participants.csv` (`has_lesion`), mai da un glob su `manual_masks/` — scelta presa apposta dopo un bug reale (debug 27-08-26, vedi `docs/dev/sdc_matrix.md` §"Why participants.tsv, not manual_masks/ on disk": una copia locale parziale dei dati falsava l'ammissione). Aggiungere qui le due soglie avrebbe richiesto o ricaricare `manual_masks/` direttamente (reintroducendo esattamente quel rischio) o precalcolare le metriche in `participants.csv` (un nuovo componente pipeline, fuori scope). Interpellato esplicitamente, l'utente ha confermato che le due soglie derivano dalla lesione e servono solo a `lesion_matrix`.

**Conseguenza ancora vera oggi**: una matrice già costruita in `data/derived/lesion_matrix/<sessione>/` non viene mai filtrata a posteriori — cambiare il criterio di ammissione non ha alcun effetto su un output già scritto. Se ci si accorge di aver dimenticato un'esclusione, la run va cancellata (cartella di output + riga in `runs.csv`) e rifatta da capo, mai patchata in-place.

**Superseduta il 29-09-26, stessa giornata**: le due soglie non esistono più, sostituite da una lista di soggetti curata a mano (voce in cima a questo file). L'alternativa scartata qui sopra — portare lo stesso meccanismo in `build_sdc_matrix.py` — è invece stata realizzata nella nuova forma, e per il motivo opposto a quello che allora la bloccava: una lista di `subject_id` non richiede a `sdc.py` di caricare nessuna maschera, quindi non reintroduce il rischio del glob su `manual_masks/`.

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
