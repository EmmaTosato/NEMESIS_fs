# Metriche di valutazione del clustering

> Teoria: [Metriche di valutazione del clustering](../../../knowledge/concepts/Machine_Learning/Unsupervised/Clustering/evaluation_metrics.md) (second brain). Questa nota contiene solo la parte specifica di NEMESIS.

Riferimento condiviso per le note dei singoli metodi in questa cartella. Definisce, con la fonte, gli indici che il progetto calcola o che la letteratura propone per i metodi gerarchici e di densità: silhouette, correlazione cofenetica, DBCV, frazione di rumore, stabilità, Calinski-Harabasz e Davies-Bouldin (più Dunn, usato nell'Embedding Explorer).

- **Cosa questa nota non fa**: non dice come leggere i grafici di un tuning (quello è in [`clustering_tuning_guide.md`](../clustering_tuning_guide.md)) e non descrive i notebook ([`docs/guides/evaluation.md`](../../../../docs/guides/evaluation.md)).
- **Regola del progetto**: i report non danno verdetti con soglie scelte da noi. Le uniche fasce citate sono quelle della silhouette (Kaufman & Rousseeuw 1990), e sono una convenzione di letteratura, non un risultato.

---

## Righe di progetto del §2 (Silhouette)

L'esempio di scikit-learn su Affinity Propagation stampa la media con l'etichetta "Silhouette Coefficient: 0.753", calcolata con `metric="sqeuclidean"` perché quell'algoritmo usa la distanza euclidea al quadrato [12]. Nel progetto i grafici scrivono "Average silhouette coefficient" per la media dei soggetti, come scikit-learn; per Kaufman & Rousseeuw quel nome indicherebbe un'altra cosa (il massimo su $k$), e i testi del progetto non usano mai quel significato.
- **Fonte indiretta.** Il testo del 1990 non è nel repo: le fasce sono riportate da fonti secondarie, una tabella di un articolo PLOS ONE [19] e, in forma discorsiva (sopra 0,7 forte, sopra 0,5 ragionevole, sopra 0,25 debole, senza citare una fonte), Wikipedia [18]. Gli estremi cambiano da una fonte all'altra (0,25 oppure 0,26).
- **È una convenzione, non un test.** Non dice se i cluster sono reali: una nuvola senza cluster ha comunque una silhouette positiva con k-means o con un clustering gerarchico (il caso è nei problemi aperti del progetto, "modello nullo per la silhouette").
- **Il progetto non la usa.** I report del tuning e le tabelle non classificano nessuna combinazione in una fascia: danno i valori, il numero di silhouette negative e il valore al primo e all'ultimo $k$. Il report di tuning dice solo che le fasce esistono e rimanda a questa nota. L'interpretazione dei valori si costruisce caso per caso, sui dati.

**Come la usa il progetto.**
- Il rumore (`-1`) è escluso prima del calcolo (`compute_clustering_metrics`, `src/analysis/clustering_tuning.py`). Va sempre letta con la frazione di rumore (§6).
- Con una metrica non euclidea (agglomerativo con `cosine`/`manhattan`, ADP con `dice`) la silhouette è calcolata con **la stessa** distanza del clustering, non con l'euclidea (`compute_clustering_metrics_metric_aware`; `adp._scores`).
- Nelle run di produzione `silhouette_plot.png` ha un pannello per cluster con la silhouette di ogni soggetto, la media nel titolo e la distanza con cui è misurata; per agglomerative la media è anche in `config.md` e la media di ogni cluster in `silhouette_per_cluster.csv` (`docs/guides/clustering.md`). Una media grande può nascondere un cluster debole: per questo la tabella dà anche la media del singolo cluster e la quota di soggetti negativi.
- Per ADP sulla matrice delle lesioni, l'84% delle coppie è a distanza dice esattamente 1 (`saturated_pair_share`, `docs/guides/embedding_app.md`): la distanza media da un cluster è allora dominata da quelle coppie e la silhouette resta vicina a 0 quale che sia la struttura. È un'osservazione sul nostro dato, non della letteratura.

## Righe di progetto del §3 (Calinski-Harabasz)

- **Cosa assume**: centroidi e somme di quadrati, quindi geometria euclidea e cluster compatti attorno a un centro. Per questo il progetto lo registra come `NaN` con ogni metrica non euclidea (agglomerativo, ADP).
- Nel progetto ADP lo calcola dalla sola matrice delle distanze al quadrato, con identità esatte (`adp._euclidean_dispersion_scores`), per non convertire in `float64` una matrice di centinaia di migliaia di colonne. È una scelta d'implementazione verificata contro scikit-learn (`lessons_learned.md`, #42).

## Righe di progetto del §4 (Davies-Bouldin)

- Come CH, è basato sui centroidi: nel progetto vale `NaN` con metriche non euclidee.

## Righe di progetto del §5 (Correlazione cofenetica)

- **Range**: come ogni correlazione di Pearson, da -1 a 1; vicino a 1 l'albero rispetta le distanze. Nel progetto: `cophenetic_correlation` in `src/analysis/clustering_tuning.py` (`scipy.cluster.hierarchy.cophenet`).

## Righe di progetto del §6 (Frazione di rumore)

- Non è un indice della letteratura con un nome proprio: è la quota di soggetti etichettati come rumore, riportata dal progetto accanto a ogni indice (`compute_clustering_metrics`).
- **Perché conta**: silhouette, CH, DB e Dunn si calcolano sui soli soggetti clusterizzati. Una combinazione che manda nel rumore i soggetti difficili lascia i più facili e fa salire gli indici senza che la partizione sia migliore. Per questo il progetto non li calcola per HDBSCAN: DBCV (§8) evita il problema pesando ogni cluster per la sua quota sul **totale** dei soggetti, rumore compreso [7].
- **Cosa ne fa il progetto**: la quota di rumore è una misura, sempre riportata accanto agli altri indici, senza soglia: nessun limite di rumore filtra i risultati o fa comparire un avviso.
- In ADP il rumore viene solo dalle righe tutte a zero (distanza dice non definita), perché il progetto usa `halo=False` (vedi [`adp.md`](adp.md)).

## Righe di progetto del §7 (Stabilità)

| Tipo | Domanda | Fonte | Nel progetto |
|---|---|---|---|
| Stabilità di un cluster HDBSCAN | quanto a lungo, al variare della densità, il cluster esiste come tale | Campello et al. 2013 [8] | `cluster_persistence_` → `persistence_mean` (solo `hdbscan_soft`) |
| Plateau di un parametro | la partizione cambia se il parametro cambia di poco? | scelta del progetto | `ari_vs_prev_z` (ADP) |
| Accordo tra varianti | linkage o embedding diversi danno la stessa partizione? | ARI, Hubert & Arabie 1985 [9] | `linkage_agreement.csv`; il confronto tra embedding non è nel report |
| Stabilità al ricampionamento | i cluster si ritrovano su sottocampioni o dati perturbati? | Hennig 2007 [10]; Monti et al. 2003 [13] | non implementata per agglomerativo, HDBSCAN e ADP |

**Ricampionamento.** Hennig (2007) misura la stabilità di ogni cluster come la similarità di Jaccard media con il cluster più simile ottenuto su campioni bootstrap [10]. Monti et al. (2003) costruiscono una matrice di consenso su sottocampioni, e la applicano anche al clustering gerarchico [13]. Nel progetto queste diagnostiche esistono solo per kmeans, gmm e spectral (`CONSENSUS_ELIGIBLE_METHODS`): è una scelta del progetto, non un limite dei metodi deterministici (vedi [`clustering_literature_survey.md`](../clustering_literature_survey.md), §4).

**RSC e Monti nel progetto** (blocco opzionale `"consensus"` di `params_clustering.json`, `src/analysis/consensus_clustering.py`). Entrambi ripetono il metodo e costruiscono una matrice di co-occorrenza $C$, dove $C_{ij}$ è la quota di ripetizioni in cui $i$ e $j$ finiscono nello stesso cluster. Non producono etichette: dicono quanto è riproducibile un $k$ scelto per kmeans, gmm o spectral.
- **RSC** (Tshimanga et al. 2025, citato da Zanola et al. 2026): ripetizioni a semi diversi sugli stessi dati; punteggio $\lambda_{k+1} - \lambda_k$ del Laplaciano normalizzato di $C$ (`compute_rsc_eigengap`, colonna `rsc_eigengap`).
- **Monti** [13]: ripetizioni su sottocampioni casuali; $C_{ij}$ è la co-assegnazione divisa per il numero di volte in cui $i$ e $j$ sono stati campionati insieme; punteggio $1 - \mathrm{PAC}$ (`compute_monti_stability`, colonna `monti_stability`).

## Righe di progetto del §8 (DBCV)

**Nel progetto: è l'indice interno di `hdbscan` e `hdbscan_soft`.** Sostituisce silhouette, Calinski-Harabasz, Davies-Bouldin e Dunn per questi due metodi, per due motivi: si calcolano sui soli soggetti non rumore (§6) e presuppongono cluster compatti. DBCV non ha né l'uno né l'altro limite.
- **Dove**: è una colonna di `tuning_results.csv` (valutazione `density_metrics` del tuning, anche su un tuning già salvato), una riga di `config.md` e `dbcv_per_cluster.csv` + `dbcv_plot.png` in una run di produzione, e un pannello dell'Embedding Explorer. Una sola funzione, `src/analysis/dbcv.py`, usa `hdbscan.validity.validity_index` con distanza euclidea.
- **Con meno di 2 cluster non è definito**: il progetto scrive NaN (cella vuota nei report), mai 0. `validity_index` restituisce l'intero `0` per "tutto rumore", indistinguibile da un punteggio vero di 0; con un solo cluster restituisce `nan` e un avviso. Un cluster di un solo soggetto fa sollevare un `ValueError`.
- **Come si legge**: nessun valore di riferimento in letteratura e nessuna soglia nel progetto. Non è confrontabile tra embedding diversi. Il valore della run non è la media dei cluster: ogni cluster pesa per la sua quota di tutti i soggetti, rumore compreso.
- **Costo**: circa 1-2 secondi per combinazione (5845 soggetti, 12-30 componenti), fino a una quindicina di secondi con un cluster molto grande: una griglia di 56 combinazioni richiede circa un minuto e mezzo.
- **Limite di fatto**: $a_{\text{core}}$ dipende dalla dimensione $d$, che per una distanza `dice` su voxel non è definita in modo ovvio: il progetto lo calcola solo sugli embedding euclidei.

## Righe di progetto del §9 (Dunn)

Calcolato da `dunn_index` (`src/analysis/clustering_tuning.py`): colonna `dunn` del tuning di agglomerative, riga di `config.md` di una run di produzione e tabella dell'Embedding Explorer.

## 10. Cosa vale per quale metodo

| Indice | agglomerative | hdbscan / hdbscan_soft | adp |
|---|---|---|---|
| Silhouette | sì, con la metrica del clustering | no (rumore escluso, cluster compatti: vedi DBCV) | sì, con la distanza del clustering |
| Calinski-Harabasz, Davies-Bouldin | solo `euclidean`, indefiniti con un'altra metrica | no | solo `euclidean` |
| Correlazione cofenetica | sì | no (l'albero è sulla raggiungibilità reciproca) | no |
| Salto del dendrogramma | sì (diagnostica del progetto) | no | no |
| Frazione di rumore | sempre 0 | sì | solo righe a zero |
| Stabilità propria | no | `persistence_mean` (`hdbscan_soft`) | plateau in `Z` (`ari_vs_prev_z`) |
| Dunn | sì (notebook e Embedding Explorer) | no | no |
| DBCV | non usato | sì, euclideo | non usato |

## Righe di progetto del §11 (Insidie comuni)

4. **Nessun indice sceglie k da solo.** Il progetto non sceglie in automatico.

## Righe di progetto di Fonti

3. Bicego, M. (2021). *Il clustering, parte 2* (dispense, Università di Verona), sezione "Indici di validità" - `knowledge/papers/methods/Slides_Bicego/` (non citata nel testo)

11. Dinh, T., Hauchi, W., Lisik, D. et al. (2025). Data clustering: an essential technique in data science. *Expert Systems with Applications*, §4.2 - `knowledge/papers/methods/Dinh et al - 2025 - Data clustering an essential technique in data science/` (non citata nel testo)

16. Documentazione di `umap-learn` (0.5), *Using UMAP for Clustering*: https://umap-learn.readthedocs.io/en/latest/clustering.html (copia in `knowledge/papers/methods/websites/Using_UMAP_for_Clustering.html`)
