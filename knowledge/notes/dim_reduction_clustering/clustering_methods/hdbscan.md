# HDBSCAN: versione hard (`hdbscan`) e soft (`hdbscan_soft`)

Due metodi di `CLUSTERING_METHODS` (`src/analysis/clustering.py`) con lo stesso algoritmo e due implementazioni:

- **`hdbscan`**: `sklearn.cluster.HDBSCAN` (scikit-learn 1.8.0 nell'ambiente `nemesis`). Un'etichetta per soggetto.
- **`hdbscan_soft`**: `hdbscan.HDBSCAN` del pacchetto `hdbscan` (0.8.44), l'implementazione di riferimento di McInnes, Healy & Astels [4]. In più dà, per ogni soggetto, una probabilità per ogni cluster (*soft clustering*).

Cosa offre il pacchetto e come si legge dopo il fit: [`hdbscan_package.md`](../hdbscan_package.md). Metriche: [`evaluation_metrics.md`](evaluation_metrics.md).

**In breve**
- Cerca zone dense a densità diverse. Il numero di cluster non si sceglie: emerge dai dati.
- I soggetti fuori da ogni zona densa sono **rumore** (`-1`), non vengono forzati in un cluster.
- Due parametri: `min_samples` (quanto deve essere denso l'intorno di un punto) e `min_cluster_size` (quanto grande deve essere un gruppo).

---

## 1. Cosa fa

HDBSCAN\* (Campello, Moulavi & Sander 2013) costruisce una gerarchia di tutte le partizioni che DBSCAN\* darebbe al variare del raggio $\varepsilon$, poi ne estrae i cluster più stabili [1, 2]. I passi, come li descrive la documentazione del pacchetto ("How HDBSCAN Works") [5]:

1. **Trasforma lo spazio**: sostituisce la distanza con la *mutual reachability distance*, che allontana i punti nelle zone rade.
2. **Albero di copertura minimo** (MST) del grafo pesato con quella distanza.
3. **Gerarchia**: togliendo gli archi dell'MST dal più pesante al più leggero, il grafo si spezza in componenti sempre più piccole (equivalente a un single linkage sulla nuova distanza).
4. **Condensa** l'albero con `min_cluster_size`.
5. **Sceglie i cluster** per stabilità (EOM) o prende le foglie (`leaf`).
6. Ciò che resta fuori è **rumore**.

---

## 2. Perché lo fa: le formule

**Core distance** [1, 2]. Con $m$ = `min_samples`, la core distance di $x$ è la distanza dal suo $m$-esimo vicino. Nella definizione di Campello et al. il conteggio **include** $x$ stesso:

$$
d_{\text{core}}(x) = d\big(x,\, \mathrm{NN}_m(x)\big)
$$

È una stima inversa della densità: una core distance piccola vuol dire un intorno denso. Un punto è *core* al livello $\varepsilon$ se $d_{\text{core}}(x) \le \varepsilon$ [2].

**Mutual reachability distance** [2, 5]:

$$
d_{\text{mreach}}(a, b) = \max\{\, d_{\text{core}}(a),\ d_{\text{core}}(b),\ d(a, b) \,\}
$$

- Tra due punti in una zona densa vale la loro distanza.
- Un punto in una zona rada ha core distance grande, quindi è lontano da tutti: "abbassa il livello del mare" sul rumore [5].
- Se $d_{\text{core}} = 0$ per tutti, $d_{\text{mreach}} = d$ e la gerarchia diventa un semplice single linkage sulle distanze originali (conseguenza diretta della formula).

**Gerarchia e DBSCAN\*.** Tagliare la gerarchia al livello $\varepsilon$ dà esattamente la partizione di DBSCAN\* con `minPts` = $m$ e raggio $\varepsilon$ [2]. HDBSCAN\* le contiene quindi tutte, e non chiede di scegliere $\varepsilon$.

**Il livello λ.** Si lavora con $\lambda = 1/\varepsilon$: più $\lambda$ è alto, più la soglia di densità è severa [1, 5].

**Albero condensato** [2, 5]. Scendendo nella gerarchia, a ogni divisione:
- se entrambi i figli hanno almeno `min_cluster_size` punti, il cluster si divide davvero in due cluster nuovi;
- se un figlio ne ha meno, quei punti "cadono fuori" dal cluster padre, che continua a esistere con un nome invariato. Nell'etichetta finale restano nel padre (di solito con probabilità bassa) se il padre è un cluster scelto; sono rumore se non lo è (verificato con `hdbscan` 0.8.44 e scikit-learn 1.8.0: un gruppo di 30 punti vicino a un cluster viene assorbito, uno lontano da tutto è rumore);
- se tutti e due ne hanno meno, il cluster scompare.

**Stabilità di un cluster** [1, 2]. Un cluster $C$ nasce a $\lambda_{\min}(C)$; ogni suo punto $x$ ne esce a $\lambda_{\max}(x, C)$ (cade fuori, o il cluster si divide):

$$
S(C) = \sum_{x \in C} \big( \lambda_{\max}(x, C) - \lambda_{\min}(C) \big)
$$

È l'area del ramo nell'albero condensato: larghezza (punti) per lunghezza (persistenza in $\lambda$) [5].

**Selezione EOM** (*Excess of Mass*) [1, 2]. Si scelgono i cluster che massimizzano la somma delle stabilità, con il vincolo che un punto stia in un solo cluster scelto. La soluzione si ottiene risalendo dalle foglie:

$$
\hat S(C) =
\begin{cases}
S(C) & \text{se } C \text{ è una foglia} \\
\max\Big\{ S(C),\ \sum_{C' \in \text{figli}(C)} \hat S(C') \Big\} & \text{altrimenti}
\end{cases}
$$

Un cluster viene scelto se la sua stabilità non è inferiore alla **somma** delle stabilità (già ottimizzate) dei figli; altrimenti si tengono i figli (a parità si tiene il padre). Il codice del pacchetto fa esattamente questo confronto e, con `allow_single_cluster=False`, esclude la radice dalla scelta (`_hdbscan_tree.pyx::get_clusters`, 0.8.44).

**Selezione `leaf`.** Prende le foglie dell'albero condensato: cluster più piccoli e omogenei, e di solito più rumore [5, 6].

**Forza di appartenenza** (`probabilities_`). Per un punto del cluster $C$, $\lambda_p / \lambda_{\max}(C)$, con $\lambda_{\max}(C)$ il $\lambda$ massimo a cui un punto lascia $C$ (codice `_hdbscan_tree.pyx`, 0.8.44; scikit-learn la descrive come "proporzionale a quanto il punto persiste nel cluster" [7]). È 0 per il rumore. Dice quanto il punto sta nel **nucleo** del suo cluster, non quanto è probabile che stia lì piuttosto che in un altro.

**GLOSH** (outlier score) [2]: $\mathrm{GLOSH}(x) = \big(\lambda_{\max}(C) - \lambda(x)\big) / \lambda_{\max}(C)$, dove $\lambda(x)$ è il livello a cui $x$ esce dal cluster $C$. Nel pacchetto è `outlier_scores_`; non è usato dal progetto.

---

## 3. La versione soft (`hdbscan_soft`)

`hdbscan.all_points_membership_vectors` restituisce una matrice soggetti × cluster. La documentazione del pacchetto ("How Soft Clustering Works") la costruisce così [8]:

1. **Parte di distanza**: per ogni cluster $j$, $1/d_j$, con $d_j$ la distanza minima del punto dagli *exemplars* del cluster (i punti che vi restano più a lungo); normalizzata a somma 1.
2. **Parte di outlier**: per ogni cluster, un punteggio che cresce con l'altezza $h_j$ dell'albero a cui il punto si unisce a quel cluster, relativa al $\lambda_{\max}$ del cluster; normalizzata.
3. **Combinazione**: il prodotto delle due, rinormalizzato: la probabilità *condizionata* a stare in qualche cluster.
4. **Probabilità di stare in un cluster**: il vettore è moltiplicato per $P(\text{in un cluster}) = \max_j h_j / \lambda_{\max}$ del cluster più vicino. Per questo **le righe non sommano a 1**: la parte mancante è la probabilità di essere rumore.

**Discrepanza tra documentazione e codice installato.** Per la parte di outlier la pagina descrive il punteggio $\lambda_{\max}/(\lambda_{\max} - h_j)$; nella funzione `all_points_membership_vectors` di 0.8.44 il punteggio è $\exp(-\lambda_{\max}/h_j)$ seguito da una softmax (`_prediction_utils.pyx::all_points_per_cluster_scores` e `all_points_outlier_membership_vector`) [12]. La parte di distanza è $1/d_j$ normalizzata, come nella documentazione. La forma esatta non cambia la lettura qualitativa (più vicino all'albero di un cluster, più probabilità), ma i numeri non si ricavano dalla formula della pagina.

**Requisiti** [8]: `prediction_data=True` (il progetto lo forza in `hdbscan_soft_fit`); non funziona con `metric="precomputed"`.

**Lettura nel progetto**: per un soggetto con etichetta $c$, la colonna $c$ è "quanto appartiene al proprio cluster" (`membership_own`); il rumore riceve comunque un vettore, che dice a quale cluster è più vicino (`soft_membership_matrix`, `own_cluster_membership`).

---

## 4. Il nostro contesto

- **Input**: embedding UMAP (`n_components` 2, 3, 10) o la matrice SDC "stream" a 87 colonne; circa 5000-5850 soggetti. Distanza euclidea (non è passata `metric`).
- **Dimensioni**: la FAQ del pacchetto indica HDBSCAN adatto fino a circa 50-100 dimensioni [6]; i nostri spazi (2-87) rientrano. Sulle matrici di voxel (centinaia di migliaia di colonne) la densità sarebbe poco informativa: per quelle il progetto usa ADP ([`adp.md`](adp.md)).
- **Griglie** (`config/registry/params_clustering.json`):
  - `hdbscan`: `min_cluster_size` ∈ {10, 15, 20, 30, 50, 75, 100} × `min_samples` ∈ {1, 5, 10, 20} = 28 combinazioni; base 100/10; `cluster_selection_method` resta il default `eom`.
  - `hdbscan_soft`: le stesse × `cluster_selection_method` ∈ {eom, leaf} = 56 combinazioni; `approx_min_span_tree: false` fisso.
- **Tempi** (`docs/guides/clustering.md`): circa 30-55 secondi per 56 combinazioni su un embedding UMAP di 5845 soggetti.

---

## 5. I parametri e le differenze tra i due pacchetti

Default verificati con `inspect.signature` sulle versioni installate.

| Parametro | Significato | Default sklearn 1.8.0 | Default `hdbscan` 0.8.44 | Nel progetto |
|---|---|---|---|---|
| `min_cluster_size` | taglia minima di un cluster nell'albero condensato | `5` | `5` | sweep 10-100 |
| `min_samples` | il $m$ della core distance (§2) | `None` (= `min_cluster_size`) | `None` (= `min_cluster_size`) | sweep 1-20 |
| `cluster_selection_method` | `eom` o `leaf` | `"eom"` | `"eom"` | `eom` (hard); sweep (soft) |
| `cluster_selection_epsilon` | fonde i cluster più vicini di questa distanza (Malzer & Baum [9]) | `0.0` | `0.0` | default |
| `alpha` | scala le distanze (*robust single linkage*, Chaudhuri & Dasgupta [10]) | `1.0` | `1.0` | default |
| `allow_single_cluster` | permette di scegliere la radice | `False` | `False` | default |
| `max_cluster_size` | tetto alla taglia dei cluster scelti da `eom` | `None` (nessun limite) | `0` (nessun limite) | default |
| `metric` | distanza tra soggetti | `"euclidean"` | `"euclidean"` | default |
| `algorithm` | come si calcolano le core distance | `"auto"` | `"best"` | default |
| `approx_min_span_tree` | accetta un MST approssimato | — (MST esatto) | `True` | `False` |
| `prediction_data` | prepara soft clustering e predizione | — | `False` | `True` (soft) |
| `cluster_selection_persistence`, `cluster_selection_epsilon_max` | altri criteri di potatura | — | `0.0`, `inf` | default |
| `match_reference_implementation` | riproduce l'implementazione Java degli autori | — | `False` | default |

**La differenza che conta: `min_samples`.**
- scikit-learn conta il punto stesso tra i vicini, come la definizione di Campello et al. [2]. Il suo docstring (sezione *Notes*) dice che, per avere lo stesso risultato, il suo `min_samples` deve essere **1 in più** di quello del pacchetto `hdbscan` [7].
- Il pacchetto, nel codice, cerca `min_samples + 1` vicini e prende l'ultimo (`hdbscan_.py`, `query(X, k=min_samples + 1)`): il punto stesso non conta. Il suo docstring dice il contrario ("This includes the point itself"); il comportamento corrisponde al codice e alla pagina "How HDBSCAN Works", non al docstring (misurato anche sui dati NEMESIS, vedi [`hdbscan_package.md`](../hdbscan_package.md)).
- Conseguenza: **`min_samples = 1` non significa la stessa cosa nei due metodi.** In scikit-learn la core distance è la distanza da sé stessi, cioè 0, e HDBSCAN diventa single linkage sulle distanze originali più la condensazione (§2). Nel pacchetto è la distanza dal primo vicino vero. Le run `hdbscan` e `hdbscan_soft` della stessa griglia non si confrontano combinazione per combinazione.

**Le altre differenze**: MST approssimato di default nel pacchetto (il progetto lo spegne); `cluster_persistence_`, `outlier_scores_`, `exemplars_`, soft clustering e `relative_validity_` esistono solo nel pacchetto [4, 5].

**Effetto dei due parametri** (documentazione del pacchetto, "Parameter Selection" e FAQ [6]): `min_cluster_size` più alto dà meno cluster e alcuni si fondono; `min_samples` più alto dà più rumore e cluster ristretti alle zone più dense. `min_cluster_size` si comporta secondo l'intuizione solo se `min_samples` è fissato, perché altrimenti lo segue.

---

## 6. Come si fa il tuning

La documentazione del pacchetto consiglia di partire da `min_cluster_size` (il parametro intuitivo: la taglia più piccola che si vuole chiamare cluster) e di usare `min_samples` per rendere il metodo più o meno conservativo [6]. Il progetto li sweepa insieme in una sola run:

1. **Heatmap** `min_cluster_size` × `min_samples` per ogni indice, `noise_fraction` e `n_clusters_found` (`tuning_plot.png`; per `hdbscan_soft` una per `cluster_selection_method`).
2. **`density_metrics.csv`** (`analyze_clustering_tuning`): in più `largest_cluster_share`, sul totale dei soggetti.
3. **Curve con poco rumore** (`noise_filtered_curves*.png`): silhouette e DB contro `min_cluster_size`, solo per le combinazioni con `noise_fraction` sotto `curves_max_noise_fraction`, un limite di esempio scelto dall'utente, non una soglia di merito.
4. **Per `hdbscan_soft`**: `membership_mean`, `membership_share_below_half` (la soglia 0,5 è fissa nel codice, `SOFT_MEMBERSHIP_LOW`: una scelta del progetto) e `persistence_mean`.
5. **Tra embedding**: ARI sui soli soggetti non rumore in entrambe le run (notebook `clustering_tuning_explorer`).

Cosa cercare: una zona della griglia dove numero di cluster e partizione cambiano poco e il rumore resta basso. Lettura dei grafici: [`clustering_tuning_guide.md`](../clustering_tuning_guide.md), "HDBSCAN".

---

## 7. Come si valuta l'output

- **Frazione di rumore** e **numero di cluster trovati**, sempre ([`evaluation_metrics.md`](evaluation_metrics.md), §6).
- **Silhouette, CH, DB** sui soli soggetti non rumore: alti con rumore alto non sono un buon segno, sono un sottoinsieme facile.
- **Stabilità** (`persistence_mean`, solo soft): i cluster persistono su un ampio intervallo di densità?
- **`probabilities_`** (hard, sezione 3.1 del notebook di valutazione) e **vettori soft** (sezione 3.2): quanti soggetti stanno al margine del loro cluster, e quali cluster si contendono soggetti.
- **DBCV** è l'indice proposto in letteratura per questi cluster [3]; il progetto non lo usa ([`evaluation_metrics.md`](evaluation_metrics.md), §8).

---

## 8. Quando usarlo

| Situazione | HDBSCAN |
|---|---|
| Non si sa quanti gruppi aspettarsi | sì, k emerge dalla densità |
| Si sospettano soggetti atipici da non forzare in un gruppo | sì, vanno nel rumore |
| Cluster di forma irregolare e densità diverse | sì, è il caso per cui è pensato [1, 2] |
| Serve un grado di appartenenza a ogni cluster | `hdbscan_soft` |
| Serve assegnare **tutti** i soggetti | no: il rumore resta tale (il vettore soft dà solo il cluster più vicino) |
| Dati senza zone dense (un continuum) | rischia un cluster unico più rumore, o tanti cluster piccoli instabili |
| Spazi con centinaia di migliaia di dimensioni | no [6] |

---

## 9. Pro e contro

**Pro**
- Nessun numero di cluster da fissare; un solo parametro intuitivo (`min_cluster_size`) [6].
- Rumore esplicito invece di assegnazioni forzate.
- Densità variabili gestite (al contrario di DBSCAN, che fissa un solo $\varepsilon$) [2].
- Deterministico.
- Il pacchetto aggiunge stabilità, outlier score e soft clustering [4].

**Contro**
- La densità richiede punti: in molte dimensioni servono molti più soggetti [6].
- Il rumore può essere una quota grande del campione e va dichiarato in ogni risultato.
- `eom` tende a dare pochi cluster grandi e alcuni piccoli; `leaf` cluster fini con più rumore [5, 6].
- Due implementazioni con convenzioni diverse (§5).
- Gli indici geometrici classici lo penalizzano o lo premiano in modo non neutrale ([`evaluation_metrics.md`](evaluation_metrics.md), §11).

---

## 10. Esempio

Sei soggetti su una retta: 0, 1, 2, 6, 7, 15. `min_cluster_size = 2`, scikit-learn con `min_samples = 2` (il punto più il suo primo vicino).

1. **Core distance**: 1 per 0, 1, 2, 6, 7 (il primo vicino è a distanza 1); 8 per 15.
2. **Mutual reachability** sugli archi dell'MST: 0-1, 1-2, 6-7 valgono 1; 2-6 vale $\max(1, 1, 4) = 4$; 7-15 vale $\max(1, 8, 8) = 8$.
3. **Gerarchia**, togliendo gli archi dal più pesante:
   - a $\varepsilon = 8$ ($\lambda = 0{,}125$) il punto 15 cade fuori (1 punto < 2);
   - a $\varepsilon = 4$ ($\lambda = 0{,}25$) il gruppo si divide in {0, 1, 2} e {6, 7}, entrambi ≥ 2: due cluster nuovi;
   - a $\varepsilon = 1$ ($\lambda = 1$) i punti si separano tutti.
4. **Stabilità**: radice $0{,}125 + 5 \times 0{,}25 = 1{,}375$; {0, 1, 2}: $3 \times (1 - 0{,}25) = 2{,}25$; {6, 7}: $2 \times 0{,}75 = 1{,}5$. La somma dei figli (3,75) supera la radice: si scelgono i due figli, 15 è rumore.
5. **Uscite** (scikit-learn 1.8.0 e `hdbscan` 0.8.44 con `min_samples = 1`, cioè la stessa core distance): etichette `[0 0 0 1 1 -1]`; `probabilities_` 1 per i cinque punti (escono tutti allo stesso $\lambda$), 0 per 15; `cluster_persistence_` 0,75 e 0,75; GLOSH di 15 = $(1 - 0{,}125)/1 = 0{,}875$. Vettore soft di 15: 0,048 e 0,077, somma 0,125: è più vicino a {6, 7} ma è quasi tutto rumore.
6. **La trappola della convenzione**: il pacchetto con `min_samples = 2` usa il secondo vicino vero; la core distance di 7 diventa 5 e quella di 6 diventa 4, la radice non si divide mai in due gruppi di almeno 2 punti e **tutti** i soggetti risultano rumore.

---

## 11. Insidie

1. **Clustering di densità dopo UMAP.** La documentazione di `umap-learn` dice che UMAP, come t-SNE, non preserva completamente la densità e può creare "false tears", fratture in un cluster unico, che portano a cluster più fini di quelli presenti [11]. La stessa pagina consiglia, per il clustering, `n_neighbors` più alto, `min_dist` vicino a 0 e più di 2 componenti, e mostra HDBSCAN su UMAP a 10 componenti [11]. Conseguenze per NEMESIS:
   - una zona densa nell'embedding può essere prodotta da UMAP (con `min_dist` basso i punti vengono impacchettati di proposito);
   - `probabilities_` su un embedding molto impacchettato descrive l'impacchettamento, non la densità dei dati originali (`docs/guides/evaluation.md`);
   - un cluster che compare a un solo `n_components` o a un solo `min_dist` va trattato come possibile artefatto ([`challenge_of_clustering_after_dim_reduction.md`](../challenge_of_clustering_after_dim_reduction.md)).
2. **Indici alti grazie al rumore.** Silhouette, CH e DB escludono il rumore ([`evaluation_metrics.md`](evaluation_metrics.md), §6).
3. **`min_samples` non fissato.** Vale `min_cluster_size` e cambia insieme a lui [6, 7]: il progetto lo fissa sempre.
4. **Confrontare `hdbscan` e `hdbscan_soft`.** Convenzione di `min_samples` diversa (§5).
5. **`probabilities_` letta come probabilità di classe.** Non lo è (§2); il confronto tra cluster è possibile solo con i vettori soft, che sono un'altra grandezza.
6. **Molti cluster minuscoli.** Con `min_cluster_size` piccolo rispetto a $n$ si possono ottenere decine o centinaia di cluster (`docs/experiments/s1.2-vol.md`, 143 cluster); `n_clusters_found` va guardato sempre.
7. **`cluster_selection_epsilon` in unità dello spazio.** Su un embedding UMAP la scala delle coordinate non ha significato fisico: il progetto non lo usa.
8. **Un continuum non ha picchi.** Se le lesioni formano un continuum, HDBSCAN non lo rivela come tale (vedi [`clustering_literature_survey.md`](../clustering_literature_survey.md), §7).

---

## Fonti

1. Campello, R. J. G. B., Moulavi, D., Sander, J. (2013). Density-based clustering based on hierarchical density estimates. *PAKDD 2013*, LNCS 7819, 160-172. doi:10.1007/978-3-642-37456-2_14
2. Campello, R. J. G. B., Moulavi, D., Zimek, A., Sander, J. (2015). Hierarchical density estimates for data clustering, visualization, and outlier detection. *ACM Transactions on Knowledge Discovery from Data*, 10(1), 5. doi:10.1145/2733381
3. Moulavi, D., Jaskowiak, P. A., Campello, R. J. G. B., Zimek, A., Sander, J. (2014). Density-based clustering validation. *SIAM SDM 2014*, 839-847. doi:10.1137/1.9781611973440.96
4. McInnes, L., Healy, J., Astels, S. (2017). hdbscan: Hierarchical density based clustering. *Journal of Open Source Software*, 2(11), 205. doi:10.21105/joss.00205
5. Documentazione `hdbscan`, *How HDBSCAN Works*: https://hdbscan.readthedocs.io/en/latest/how_hdbscan_works.html
6. Documentazione `hdbscan`, *Parameter Selection for HDBSCAN\** e *FAQ*: https://hdbscan.readthedocs.io/en/latest/parameter_selection.html, https://hdbscan.readthedocs.io/en/latest/faq.html
7. scikit-learn 1.8.0, `sklearn.cluster.HDBSCAN` (documentazione e docstring, sezione *Notes*): https://scikit-learn.org/stable/modules/generated/sklearn.cluster.HDBSCAN.html
8. Documentazione `hdbscan`, *Soft Clustering for HDBSCAN\** e *How Soft Clustering for HDBSCAN Works*: https://hdbscan.readthedocs.io/en/latest/soft_clustering.html, https://hdbscan.readthedocs.io/en/latest/soft_clustering_explanation.html
9. Malzer, C., Baum, M. (2020). A hybrid approach to hierarchical density-based cluster selection. arXiv:1911.02282 (citato dal docstring di `sklearn.cluster.HDBSCAN`)
10. Chaudhuri, K., Dasgupta, S. (2010). Rates of convergence for the cluster tree. *NeurIPS 2010*: https://papers.nips.cc/paper/2010/hash/b534ba68236ba543ae44b22bd110a1d6-Abstract.html (citato dal docstring di `sklearn.cluster.HDBSCAN`)
11. Documentazione `umap-learn` (0.5), *Using UMAP for Clustering*: https://umap-learn.readthedocs.io/en/latest/clustering.html (copia in `knowledge/papers/methods/websites/Using_UMAP_for_Clustering.html`)
12. Codice installato: `hdbscan` 0.8.44 (`hdbscan_.py`, `_hdbscan_tree.pyx`, `_prediction_utils.pyx`, `prediction.py`) e scikit-learn 1.8.0 (`sklearn/cluster/_hdbscan/hdbscan.py`), ambiente conda `nemesis`
