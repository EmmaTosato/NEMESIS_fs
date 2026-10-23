# Metriche di valutazione del clustering

Riferimento condiviso per le note dei singoli metodi in questa cartella. Definisce, con la fonte, gli indici che il progetto calcola o che la letteratura propone per i metodi gerarchici e di densità: silhouette, correlazione cofenetica, DBCV, frazione di rumore, stabilità, Calinski-Harabasz e Davies-Bouldin (più Dunn, usato nel notebook di valutazione e nell'Embedding Explorer).

- **Cosa questa nota non fa**: non dice come leggere i grafici di un tuning (quello è in [`clustering_tuning_guide.md`](../clustering_tuning_guide.md)) e non descrive i notebook ([`docs/guides/evaluation.md`](../../../../docs/guides/evaluation.md)).
- **Regola del progetto**: i report non danno verdetti con soglie scelte da noi. Le uniche fasce citate sono quelle della silhouette (Kaufman & Rousseeuw 1990), e sono una convenzione di letteratura, non un risultato.

---

## 1. Tre famiglie di indici

- **Interni**: usano solo i dati e le etichette. Silhouette, Calinski-Harabasz, Davies-Bouldin, Dunn, DBCV. Rispondono a "quanto sono compatti e separati i cluster in questo spazio".
- **Del modello**: esistono solo per un certo metodo e descrivono il suo fit. Correlazione cofenetica (agglomerativo), stabilità dei cluster e frazione di rumore (HDBSCAN), il plateau in `Z` (ADP).
- **Esterni o di accordo**: confrontano due partizioni (ARI, NMI). Definiti in [`clustering_literature_survey.md`](../clustering_literature_survey.md), §6; qui servono solo per la stabilità (§7).

Nessun indice interno è neutrale rispetto al metodo. Ognuno contiene un'idea di cluster, e premia i metodi che condividono quell'idea [3, 11].

---

## 2. Silhouette (Rousseeuw 1987)

**Definizione** [1]. Per il soggetto $i$ nel cluster $A$:

$$
a(i) = \frac{1}{|A|-1} \sum_{j \in A,\, j \neq i} d(i,j), \qquad
b(i) = \min_{C \neq A} \frac{1}{|C|} \sum_{j \in C} d(i,j)
$$

$$
s(i) = \frac{b(i) - a(i)}{\max\{a(i),\, b(i)\}} \in [-1, 1]
$$

- $a(i)$ è la distanza media dai compagni di cluster, $b(i)$ quella dal cluster più vicino.
- Se $|A| = 1$, Rousseeuw pone $s(i) = 0$ [1].
- La silhouette di una partizione è la media degli $s(i)$. `sklearn.metrics.silhouette_score` restituisce questa media su tutti i soggetti e richiede tra 2 e $n-1$ cluster [12].
- Rousseeuw propone la media della silhouette (*average silhouette width*) come criterio per scegliere il numero di cluster e il grafico delle silhouette per cluster come diagnostica [1].

**Tre nomi per cose vicine.** In letteratura e nei programmi "silhouette" indica tre numeri diversi, e conviene tenerli separati:

| Nome | Cosa è | Dove compare |
|---|---|---|
| *silhouette* (o *Silhouette Coefficient* di un campione) $s(i)$ | il valore di **un soggetto** | Rousseeuw 1987 [1]; in scikit-learn il valore per campione si chiama *Silhouette Coefficient* (`silhouette_samples`) [12] |
| *average silhouette width* $\bar{s}(k)$ | la **media** degli $s(i)$ su tutti i soggetti di una partizione in $k$ cluster | Rousseeuw 1987 [1]; in scikit-learn è `silhouette_score`, "la media del Silhouette Coefficient su tutti i campioni" [12] |
| *silhouette coefficient* SC | il **massimo** di $\bar{s}(k)$ al variare di $k$: il miglior risultato su tutti i $k$ provati | Kaufman & Rousseeuw 1990, p. 87, secondo [18]; il libro non è stato consultato |

L'esempio di scikit-learn su Affinity Propagation stampa la media con l'etichetta "Silhouette Coefficient: 0.753", calcolata con `metric="sqeuclidean"` perché quell'algoritmo usa la distanza euclidea al quadrato [12]. Nel progetto i grafici scrivono "Average silhouette coefficient" per la media dei soggetti, come scikit-learn; per Kaufman & Rousseeuw quel nome indicherebbe un'altra cosa (il massimo su $k$), e i testi del progetto non usano mai quel significato.

**Le fasce di lettura.** La letteratura associa alla silhouette una scala di interpretazione, attribuita a Kaufman & Rousseeuw (1990) [2]:

| Silhouette | Lettura |
|---|---|
| 0,71 - 1,00 | struttura forte |
| 0,51 - 0,70 | struttura ragionevole |
| 0,26 - 0,50 | struttura debole, forse artificiale |
| ≤ 0,25 | nessuna struttura sostanziale |

- **Fonte indiretta.** Il testo del 1990 non è nel repo: le fasce sono riportate da fonti secondarie, una tabella di un articolo PLOS ONE [19] e, in forma discorsiva (sopra 0,7 forte, sopra 0,5 ragionevole, sopra 0,25 debole, senza citare una fonte), Wikipedia [18]. Gli estremi cambiano da una fonte all'altra (0,25 oppure 0,26).
- **A cosa si riferiscono.** Nella definizione di Kaufman & Rousseeuw il numero che si legge con la scala è SC, cioè il massimo su $k$ [18]. Applicarla alla media di una singola partizione, o a ogni $k$ di un tuning, è un'estensione dell'uso originale, non una lettura prevista da loro.
- **È una convenzione, non un test.** Non dice se i cluster sono reali: una nuvola senza cluster ha comunque una silhouette positiva con k-means o con un clustering gerarchico (il caso è nei problemi aperti del progetto, "modello nullo per la silhouette").
- **Dipende dalla forma dei cluster.** Vale quanto detto sotto: premia cluster compatti e convessi.
- **Il progetto non la usa.** I report del tuning e le tabelle non classificano nessuna combinazione in una fascia: danno i valori, il numero di silhouette negative e il valore al primo e all'ultimo $k$. Il report di tuning dice solo che le fasce esistono e rimanda a questa nota. L'interpretazione dei valori si costruisce caso per caso, sui dati.

**Cosa assume.** La silhouette confronta distanze **medie** su interi cluster. Funziona bene con cluster compatti e convessi, e premia meno un cluster allungato o a forma irregolare, anche se reale [1, 11].

**Come la usa il progetto.**
- Il rumore (`-1`) è escluso prima del calcolo (`compute_clustering_metrics`, `src/analysis/clustering_tuning.py`). Va sempre letta con la frazione di rumore (§6).
- Con una metrica non euclidea (agglomerativo con `cosine`/`manhattan`, ADP con `dice`) la silhouette è calcolata con **la stessa** distanza del clustering, non con l'euclidea (`compute_clustering_metrics_metric_aware`; `adp._scores`).
- Due silhouette calcolate con distanze diverse, o su spazi diversi (due embedding), non si confrontano: ogni spazio ha la sua scala.
- Nelle run di produzione `silhouette_plot.png` ha un pannello per cluster con la silhouette di ogni soggetto, la media nel titolo e la distanza con cui è misurata; per agglomerative la media è anche in `config.md` e la media di ogni cluster in `silhouette_per_cluster.csv` (`docs/guides/clustering.md`). Una media grande può nascondere un cluster debole: per questo la tabella dà anche la media del singolo cluster e la quota di soggetti negativi.
- Per ADP sulla matrice delle lesioni, l'84% delle coppie è a distanza dice esattamente 1 (`saturated_pair_share`, `docs/guides/evaluation.md`): la distanza media da un cluster è allora dominata da quelle coppie e la silhouette resta vicina a 0 quale che sia la struttura. È un'osservazione sul nostro dato, non della letteratura.

**Esempio.** Cinque punti su una retta: 0, 1, 2 (cluster 1) e 6, 7 (cluster 2). Per il punto 0: $a = (1+2)/2 = 1{,}5$, $b = (6+7)/2 = 6{,}5$, $s = (6{,}5 - 1{,}5)/6{,}5 = 0{,}77$. La media sui cinque punti è 0,78 (calcolata con scikit-learn 1.8.0).

---

## 3. Calinski-Harabasz (1974)

**Definizione** [4]. Con $n$ soggetti, $k$ cluster, $B$ la matrice di dispersione tra i cluster e $W$ quella dentro i cluster:

$$
\mathrm{CH} = \frac{\operatorname{tr}(B)/(k-1)}{\operatorname{tr}(W)/(n-k)}, \qquad
\operatorname{tr}(W) = \sum_{q=1}^{k} \sum_{i \in C_q} \lVert x_i - c_q \rVert^2, \qquad
\operatorname{tr}(B) = \sum_{q=1}^{k} n_q \lVert c_q - c \rVert^2
$$

dove $c_q$ è il centroide del cluster $q$ e $c$ quello di tutti i dati.

- **Direzione**: più alto è meglio. Non ha un massimo né una scala assoluta.
- **Cosa assume**: centroidi e somme di quadrati, quindi geometria euclidea e cluster compatti attorno a un centro. Per questo il progetto lo registra come `NaN` con ogni metrica non euclidea (agglomerativo, ADP).
- Nel progetto ADP lo calcola dalla sola matrice delle distanze al quadrato, con identità esatte (`adp._euclidean_dispersion_scores`), per non convertire in `float64` una matrice di centinaia di migliaia di colonne. È una scelta d'implementazione verificata contro scikit-learn (`lessons_learned.md`, #42).

---

## 4. Davies-Bouldin (1979)

**Definizione** [5]. Per ogni cluster $i$ una dispersione $S_i$ e, per ogni coppia, la distanza tra i centroidi $M_{ij}$:

$$
S_i = \Big( \frac{1}{|C_i|} \sum_{x \in C_i} \lVert x - c_i \rVert^{q} \Big)^{1/q}, \qquad
R_{ij} = \frac{S_i + S_j}{M_{ij}}, \qquad
\mathrm{DB} = \frac{1}{k} \sum_{i=1}^{k} \max_{j \neq i} R_{ij}
$$

- Davies e Bouldin lasciano liberi gli esponenti di $S_i$ e di $M_{ij}$ [5]. scikit-learn usa la distanza media dal centroide ($q = 1$) e la distanza euclidea tra i centroidi [12].
- **Direzione**: più basso è meglio; 0 è il minimo.
- **Cosa misura**: per ogni cluster il caso peggiore, cioè il cluster che gli è più simile. Per questo penalizza due cluster vicini anche se ciascuno è compatto, e a volte non è d'accordo con la silhouette.
- Come CH, è basato sui centroidi: nel progetto vale `NaN` con metriche non euclidee.

**Esempio** (stessi 5 punti del §2): $S_1 = 2/3$, $S_2 = 0{,}5$, $M_{12} = 6{,}5 - 1 = 5{,}5$, $\mathrm{DB} = (2/3 + 0{,}5)/5{,}5 = 0{,}21$; CH vale 43,6 (scikit-learn 1.8.0).

---

## 5. Correlazione cofenetica (Sokal & Rohlf 1962)

Serve solo ai metodi che producono un albero (agglomerativo).

**Definizione** [6]. La distanza **cofenetica** $c_{ij}$ tra due soggetti è l'altezza del dendrogramma alla quale i due finiscono per la prima volta nello stesso cluster. La correlazione cofenetica è la correlazione di Pearson tra le distanze originali $d_{ij}$ e le $c_{ij}$, su tutte le coppie:

$$
r_c = \frac{\sum_{i<j} (d_{ij} - \bar d)(c_{ij} - \bar c)}{\sqrt{\sum_{i<j} (d_{ij} - \bar d)^2 \, \sum_{i<j} (c_{ij} - \bar c)^2}}
$$

- Sokal & Rohlf la introducono per confrontare dendrogrammi ottenuti con metodi diversi [6].
- **Range**: come ogni correlazione di Pearson, da -1 a 1; vicino a 1 l'albero rispetta le distanze. Nel progetto: `cophenetic_correlation` in `src/analysis/clustering_tuning.py` (`scipy.cluster.hierarchy.cophenet`).
- **Cosa non dice**: niente sul numero di cluster né sull'utilità dei cluster. Misura la fedeltà dell'albero intero, quindi è dominata dalle coppie lontane (che sono la maggioranza).
- Si confronta tra linkage della **stessa** metrica: le altezze di ward e quelle di average non sono nella stessa unità (vedi [`agglomerative.md`](agglomerative.md), §2).

**Esempio** (5 punti del §2, scipy 1.17.0): single 0,935, complete 0,937, average 0,938, ward 0,938. Differenze di questa entità non bastano a scegliere un linkage.

---

## 6. Frazione di rumore

Per i metodi che possono non assegnare un soggetto (HDBSCAN, ADP con le righe a zero):

$$
\text{noise\_fraction} = \frac{|\{i : \ell_i = -1\}|}{n}
$$

- Non è un indice della letteratura con un nome proprio: è la quota di soggetti etichettati come rumore, riportata dal progetto accanto a ogni indice (`compute_clustering_metrics`).
- **Perché conta**: silhouette, CH, DB e Dunn si calcolano sui soli soggetti clusterizzati. Una combinazione che manda nel rumore i soggetti difficili lascia i più facili e fa salire gli indici senza che la partizione sia migliore. Per questo il progetto non li calcola per HDBSCAN: DBCV (§8) evita il problema pesando ogni cluster per la sua quota sul **totale** dei soggetti, rumore compreso [7].
- **Cosa ne fa il progetto**: la quota di rumore è una misura, sempre riportata accanto agli altri indici, senza soglia: nessun limite di rumore filtra i risultati o fa comparire un avviso.
- In ADP il rumore viene solo dalle righe tutte a zero (distanza dice non definita), perché il progetto usa `halo=False` (vedi [`adp.md`](adp.md)).

---

## 7. Stabilità

"Stabilità" indica in letteratura cose diverse. Nel contesto di questi metodi:

| Tipo | Domanda | Fonte | Nel progetto |
|---|---|---|---|
| Stabilità di un cluster HDBSCAN | quanto a lungo, al variare della densità, il cluster esiste come tale | Campello et al. 2013 [8] | `cluster_persistence_` → `persistence_mean` (solo `hdbscan_soft`) |
| Plateau di un parametro | la partizione cambia se il parametro cambia di poco? | scelta del progetto | `ari_vs_prev_z` (ADP) |
| Accordo tra varianti | linkage o embedding diversi danno la stessa partizione? | ARI, Hubert & Arabie 1985 [9] | `linkage_agreement.csv`; il confronto tra embedding non è nel report |
| Stabilità al ricampionamento | i cluster si ritrovano su sottocampioni o dati perturbati? | Hennig 2007 [10]; Monti et al. 2003 [13] | non implementata per agglomerativo, HDBSCAN e ADP |

**Stabilità di un cluster in HDBSCAN** [8]. Con $\lambda = 1/\varepsilon$ (l'inverso della distanza di taglio), un cluster $C$ nasce a $\lambda_{\min}(C)$ e ogni suo punto $x$ ne esce a $\lambda_{\max}(x, C)$:

$$
S(C) = \sum_{x \in C} \big( \lambda_{\max}(x, C) - \lambda_{\min}(C) \big)
$$

È il criterio con cui HDBSCAN sceglie i cluster (vedi [`hdbscan.md`](hdbscan.md), §2), non un indice esterno: un cluster stabile è uno che persiste su un ampio intervallo di densità. Il pacchetto `hdbscan` la normalizza in [0, 1] in `cluster_persistence_`, dividendo per la taglia del cluster e per il $\lambda$ massimo dell'albero (codice di `hdbscan` 0.8.44, `_hdbscan_tree.pyx::get_stability_scores`).

**Ricampionamento.** Hennig (2007) misura la stabilità di ogni cluster come la similarità di Jaccard media con il cluster più simile ottenuto su campioni bootstrap [10]. Monti et al. (2003) costruiscono una matrice di consenso su sottocampioni, e la applicano anche al clustering gerarchico [13]. Nel progetto queste diagnostiche esistono solo per kmeans, gmm e spectral (`CONSENSUS_ELIGIBLE_METHODS`): è una scelta del progetto, non un limite dei metodi deterministici (vedi [`clustering_literature_survey.md`](../clustering_literature_survey.md), §4).

**RSC e Monti nel progetto** (blocco opzionale `"consensus"` di `params_clustering.json`, `src/analysis/consensus_clustering.py`). Entrambi ripetono il metodo e costruiscono una matrice di co-occorrenza $C$, dove $C_{ij}$ è la quota di ripetizioni in cui $i$ e $j$ finiscono nello stesso cluster. Non producono etichette: dicono quanto è riproducibile un $k$ scelto per kmeans, gmm o spectral.

- **RSC** (Tshimanga et al. 2025, citato da Zanola et al. 2026): ripetizioni a semi diversi sugli stessi dati; punteggio $\lambda_{k+1} - \lambda_k$ del Laplaciano normalizzato di $C$ (`compute_rsc_eigengap`, colonna `rsc_eigengap`).
- **Monti** [13]: ripetizioni su sottocampioni casuali; $C_{ij}$ è la co-assegnazione divisa per il numero di volte in cui $i$ e $j$ sono stati campionati insieme; punteggio $1 - \mathrm{PAC}$ (`compute_monti_stability`, colonna `monti_stability`).

Il *Proportion of Ambiguous Clustering* è la quota di coppie con co-occorrenza in una banda ambigua, per default $(0.1, 0.9)$ [17]:

$$
\mathrm{PAC} = \frac{\#\{(i<j) : 0.1 < C_{ij} < 0.9\}}{n(n-1)/2} .
$$

Șenbabaoğlu, Michailidis & Li lo propongono al posto dell'area sotto la CDF di Monti et al., che mostrano essere distorta verso $k$ grandi [17]. Con spectral, `assign_labels="cluster_qr"` e grafo di affinità connesso le ripetizioni a semi diversi danno la stessa partizione ([`spectral.md`](spectral.md), sezione 3): $C$ contiene solo 0 e 1 e l'RSC non aggiunge informazione (a grafo non connesso le partizioni cambiano col seme); è informativa solo la versione su sottocampioni (Monti).

---

## 8. DBCV (Moulavi et al. 2014)

**Perché esiste.** Gli indici del §2-4 premiano cluster convessi. DBCV (*Density-Based Clustering Validation*) è pensato per cluster di forma arbitraria e per partizioni con rumore [7].

**Definizione** [7]. Per un oggetto $o$ in un cluster di $n_i$ oggetti, in dimensione $d$, la *all-points core distance* è una media armonica generalizzata delle distanze dai vicini nel cluster:

$$
a_{\text{core}}(o) = \left( \frac{\sum_{j=2}^{n_i} \big(1/\mathrm{KNN}(o, j)\big)^{d}}{n_i - 1} \right)^{-1/d}
$$

Con questa core distance si definisce una distanza di raggiungibilità reciproca (come in HDBSCAN, [`hdbscan.md`](hdbscan.md) §2) e l'albero di copertura minimo (MST) di ogni cluster. Poi:

- **sparsità** $\mathrm{DSC}(C_i)$: l'arco più pesante tra i nodi interni dell'MST di $C_i$;
- **separazione** $\mathrm{DSPC}(C_i, C_j)$: la minima distanza di raggiungibilità tra i nodi interni dei due MST;

$$
V_C(C_i) = \frac{\min_{j \neq i} \mathrm{DSPC}(C_i, C_j) - \mathrm{DSC}(C_i)}{\max\big\{\min_{j \neq i} \mathrm{DSPC}(C_i, C_j),\ \mathrm{DSC}(C_i)\big\}}, \qquad
\mathrm{DBCV} = \sum_{i} \frac{|C_i|}{|O|}\, V_C(C_i)
$$

- $|O|$ è il numero di **tutti** gli oggetti, rumore compreso: il rumore abbassa DBCV.
- Range da -1 a 1, più alto è meglio.
- **Implementazioni**: `hdbscan.validity.validity_index` (pacchetto `hdbscan`, con l'argomento `d` per la dimensione); `relative_validity_`, un'approssimazione veloce sul solo MST di HDBSCAN che la documentazione del pacchetto dichiara utile **solo** per confrontare iperparametri, non come misura assoluta (docstring di `hdbscan.HDBSCAN`, 0.8.44) [14].
- **Esempio**: per i punti 0, 1, 2, 6, 7, 15 partizionati da HDBSCAN in {0, 1, 2}, {6, 7} e il rumore {15}, `validity_index` dà 0,63 (`hdbscan` 0.8.44).

**Nel progetto: è l'indice interno di `hdbscan` e `hdbscan_soft`.** Sostituisce silhouette, Calinski-Harabasz, Davies-Bouldin e Dunn per questi due metodi, per due motivi: si calcolano sui soli soggetti non rumore (§6) e presuppongono cluster compatti. DBCV non ha né l'uno né l'altro limite.

- **Dove**: è una colonna di `density_metrics.csv` (valutazione `density_metrics` del tuning, anche su un tuning già salvato), una riga di `config.md` e `dbcv_per_cluster.csv` + `dbcv_plot.png` in una run di produzione, e un pannello dell'Embedding Explorer. Una sola funzione, `src/analysis/dbcv.py`, usa `hdbscan.validity.validity_index` con distanza euclidea.
- **Con meno di 2 cluster non è definito**: il progetto scrive NaN (cella vuota nei report), mai 0. `validity_index` restituisce l'intero `0` per "tutto rumore", indistinguibile da un punteggio vero di 0; con un solo cluster restituisce `nan` e un avviso. Un cluster di un solo soggetto fa sollevare un `ValueError`.
- **Come si legge**: nessun valore di riferimento in letteratura e nessuna soglia nel progetto. Non è confrontabile tra embedding diversi. Il valore della run non è la media dei cluster: ogni cluster pesa per la sua quota di tutti i soggetti, rumore compreso.
- **Costo**: circa 1-2 secondi per combinazione (5845 soggetti, 12-30 componenti), fino a una quindicina di secondi con un cluster molto grande: una griglia di 56 combinazioni richiede circa un minuto e mezzo.
- **Limite di fatto**: $a_{\text{core}}$ dipende dalla dimensione $d$, che per una distanza `dice` su voxel non è definita in modo ovvio: il progetto lo calcola solo sugli embedding euclidei.

---

## 9. Dunn (1974)

Usato dal notebook `clustering_evaluation` (`dunn_index`, `src/analysis/clustering_tuning.py`), non dal tuning.

$$
D = \frac{\min_{i \neq j} \delta(C_i, C_j)}{\max_{q} \Delta(C_q)}
$$

con $\delta$ la minima distanza tra due punti di cluster diversi e $\Delta$ il diametro massimo di un cluster [15]. Più alto è meglio. Dipende da un solo arco e da un solo diametro, quindi un solo outlier lo sposta molto.

---

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

---

## 11. Insidie comuni

1. **Gli indici interni non sono un giudice neutrale.** Silhouette, CH e DB premiano cluster compatti e convessi; un metodo di densità può trovare un gruppo reale e avere indici bassi [1, 11].
2. **Su un embedding si misura l'embedding.** UMAP non preserva la densità e può creare "false tears" (fratture) [16]: indici alti su un embedding con `min_dist` basso possono dire più dei parametri di UMAP che dei dati (vedi [`challenge_of_clustering_after_dim_reduction.md`](../challenge_of_clustering_after_dim_reduction.md)).
3. **Il rumore fa salire gli indici.** Va sempre letto `noise_fraction` accanto (§6).
4. **Spazi diversi, numeri non confrontabili.** Stessa silhouette su due embedding, o con due metriche, non è la stessa cosa.
5. **Nessun indice sceglie k da solo.** Ogni indice ha una sua idea di cluster; il progetto non sceglie in automatico.

---

## Fonti

1. Rousseeuw, P. J. (1987). Silhouettes: a graphical aid to the interpretation and validation of cluster analysis. *Journal of Computational and Applied Mathematics*, 20, 53-65. doi:10.1016/0377-0427(87)90125-7
2. Kaufman, L., Rousseeuw, P. J. (1990). *Finding Groups in Data: An Introduction to Cluster Analysis*. Wiley. doi:10.1002/9780470316801 (non consultato direttamente: le fasce sono riportate dalle fonti secondarie [18], [19])
3. Bicego, M. (2021). *Il clustering, parte 2* (dispense, Università di Verona), sezione "Indici di validità" - `knowledge/papers/methods/Slides_Bicego/`
4. Caliński, T., Harabasz, J. (1974). A dendrite method for cluster analysis. *Communications in Statistics*, 3(1), 1-27. doi:10.1080/03610927408827101
5. Davies, D. L., Bouldin, D. W. (1979). A cluster separation measure. *IEEE Transactions on Pattern Analysis and Machine Intelligence*, PAMI-1(2), 224-227. doi:10.1109/TPAMI.1979.4766909
6. Sokal, R. R., Rohlf, F. J. (1962). The comparison of dendrograms by objective methods. *Taxon*, 11(2), 33-40. doi:10.2307/1217208
7. Moulavi, D., Jaskowiak, P. A., Campello, R. J. G. B., Zimek, A., Sander, J. (2014). Density-based clustering validation. *Proceedings of the 2014 SIAM International Conference on Data Mining*, 839-847. doi:10.1137/1.9781611973440.96
8. Campello, R. J. G. B., Moulavi, D., Sander, J. (2013). Density-based clustering based on hierarchical density estimates. *PAKDD 2013*, LNCS 7819, 160-172. doi:10.1007/978-3-642-37456-2_14
9. Hubert, L., Arabie, P. (1985). Comparing partitions. *Journal of Classification*, 2(1), 193-218. doi:10.1007/BF01908075
10. Hennig, C. (2007). Cluster-wise assessment of cluster stability. *Computational Statistics & Data Analysis*, 52(1), 258-271. doi:10.1016/j.csda.2006.11.025
11. Dinh, T., Hauchi, W., Lisik, D. et al. (2025). Data clustering: an essential technique in data science. *Expert Systems with Applications*, §4.2 - `knowledge/papers/methods/Dinh et al - 2025 - Data clustering an essential technique in data science/`
12. scikit-learn 1.8.0, *Clustering performance evaluation* (silhouette, Calinski-Harabasz, Davies-Bouldin): https://scikit-learn.org/stable/modules/clustering.html#clustering-performance-evaluation
13. Monti, S., Tamayo, P., Mesirov, J., Golub, T. (2003). Consensus clustering: a resampling-based method for class discovery and visualization of gene expression microarray data. *Machine Learning*, 52, 91-118. doi:10.1023/A:1023949509487
14. Documentazione del pacchetto `hdbscan` (0.8.44), API reference e docstring di `hdbscan.HDBSCAN` (`relative_validity_`) e `hdbscan.validity.validity_index`: https://hdbscan.readthedocs.io/en/latest/api.html
15. Dunn, J. C. (1974). Well-separated clusters and optimal fuzzy partitions. *Journal of Cybernetics*, 4(1), 95-104. doi:10.1080/01969727408546059
16. Documentazione di `umap-learn` (0.5), *Using UMAP for Clustering*: https://umap-learn.readthedocs.io/en/latest/clustering.html (copia in `knowledge/papers/methods/websites/Using_UMAP_for_Clustering.html`)
17. Șenbabaoğlu, Y., Michailidis, G., Li, J. Z. (2014). Critical limitations of consensus clustering in class discovery. *Scientific Reports*, 4, 6207. doi:10.1038/srep06207
18. Wikipedia, *Silhouette (clustering)*: https://en.wikipedia.org/wiki/Silhouette_(clustering) (fonte secondaria: definizione di $s(i)$, il nome *silhouette coefficient* come massimo su $k$ attribuito a Kaufman & Rousseeuw 1990 p. 87, le soglie 0,7, 0,5 e 0,25 senza fonte; consultata il 21-10-26)
19. Tabella con le fasce di Kaufman & Rousseeuw in un articolo PLOS ONE (fonte secondaria): https://pmc.ncbi.nlm.nih.gov/articles/PMC5978888/table/pone.0198245.t001 (indicata da una ricerca web il 21-10-26: la pagina non è stata aperta, le fasce sono quelle riportate nel riassunto della ricerca)
