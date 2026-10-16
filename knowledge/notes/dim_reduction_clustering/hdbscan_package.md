# Il pacchetto `hdbscan`: come funziona, cosa si legge dopo il fit, come lo usa NEMESIS

> Fonti (lette integralmente): la documentazione ufficiale del pacchetto, [hdbscan.readthedocs.io](https://hdbscan.readthedocs.io/en/latest/), pagine *Basic Usage*, *Getting More Information About a Clustering*, *Parameter Selection*, *Outlier Detection*, *Predicting clusters for new points*, *Soft Clustering*, *How Soft Clustering Works*, *Combining HDBSCAN\* with DBSCAN* (`cluster_selection_epsilon`), *Extracting DBSCAN\**, *How to Detect Branches*, *FAQ*, *How HDBSCAN Works*, *Comparing Python Clustering Algorithms*, *Performance and Scaling*, *API Reference*. Più il docstring della classe `hdbscan.HDBSCAN` (versione 0.8.44, installata nell'ambiente `nemesis`).
>
> Questo pacchetto è l'implementazione di riferimento di McInnes, Healy e Astels (2017, *JOSS* 2(11)) di HDBSCAN\* di Campello, Moulavi e Sander. NEMESIS lo usa nel metodo `hdbscan_soft`; il metodo `hdbscan` usa invece `sklearn.cluster.HDBSCAN`, un'altra implementazione (vedi la fine di questa nota).

**In breve**:
- **Cosa fa**: trova zone dense a densità diverse, senza scegliere il numero di cluster. I soggetti fuori da ogni zona densa sono rumore (`-1`), non sono forzati in un cluster.
- **Cosa ha in più di sklearn**: il *soft clustering* (un vettore di probabilità per ogni soggetto, una per cluster), il punteggio di outlier locale GLOSH, la stabilità di ogni cluster, la predizione su soggetti nuovi, il rilevamento di rami dentro un cluster.
- **Dove sta bene**: dimensioni basse (la FAQ indica "fino a circa 50 o 100 dimensioni"), decine di migliaia di punti o meno. Gli embedding UMAP di NEMESIS (2-10 componenti, circa 5800 soggetti) rientrano largamente.

---

## Come funziona

I sei passi della pagina *How HDBSCAN Works*:

1. **Trasformare lo spazio.** La *core distance* di un punto è la distanza dal suo `k`-esimo vicino (`k` = `min_samples`). La *distanza di raggiungibilità reciproca* tra due punti è `max(core(a), core(b), d(a, b))`: spinge lontano i punti in zone rade e lascia invariate le distanze tra punti in zone dense ("abbassa il livello del mare" sul rumore).
2. **Albero di copertura minimo** (MST) del grafo con quelle distanze.
3. **Gerarchia**: gli archi dell'MST, in ordine di peso crescente, fondono i cluster a due a due (un single linkage robusto).
4. **Condensare l'albero** con `min_cluster_size`: quando uno dei due rami di una divisione ha meno punti della soglia, quei punti "cadono fuori" dal cluster invece di formare un cluster nuovo. L'albero si riduce molto.
5. **Stabilità e scelta dei cluster.** Si usa `λ = 1 / distanza`. La stabilità di un cluster è `Σ (λ_p − λ_nascita)` sui suoi punti, dove `λ_p` è il valore a cui il punto esce. Con *Excess of Mass* (`eom`) si risale dalle foglie: un cluster figlio sostituisce il genitore se la sua stabilità è maggiore, altrimenti resta il genitore.
6. **Rumore e probabilità.** Ogni punto fuori dai cluster scelti è rumore (`-1`). Per gli altri, i `λ_p` normalizzati dentro il cluster danno `probabilities_` in [0, 1].

---

## I parametri, secondo la documentazione

| Parametro | Cosa fa | Note della documentazione |
|---|---|---|
| `min_cluster_size` | Dimensione minima di un gruppo perché conti come cluster. | Il parametro intuitivo; cambiarlo riusa l'albero già calcolato. |
| `min_samples` | Il `k` della core distance. Più alto: più rumore, zone dense più ristrette. | Se non è fissato vale `min_cluster_size`, e allora cambia tutto insieme. Cambiarlo ricalcola l'albero (costoso). Per esplorare `min_cluster_size` va tenuto fisso. |
| `cluster_selection_method` | `eom` (default): tende a pochi cluster grandi e tanti piccoli. `leaf`: cluster fini e omogenei, dalle foglie dell'albero. | La FAQ consiglia `leaf` se si ottiene un solo cluster grande. |
| `cluster_selection_epsilon` | Fonde i cluster più vicini di una soglia di distanza (ibrido DBSCAN/HDBSCAN\*). | Nella stessa unità della metrica: dipende dalla scala dello spazio. `0` = HDBSCAN\* puro. |
| `alpha` | Scala le distanze (single linkage robusto). | Gli autori lo sconsigliano: "fermati, ripensa, e riprova con `min_samples` o `cluster_selection_epsilon`". Ricalcola l'albero. |
| `allow_single_cluster` | Permette un risultato a un solo cluster. | Spento di default per un bias di `eom`. |
| `approx_min_span_tree` | Accetta un MST solo approssimato. | Acceso di default per velocità; "marginalmente peggiore". Con `False` il risultato è quello esatto. |
| `gen_min_span_tree` | Conserva l'MST per analisi successive. | Serve a `relative_validity_`. |
| `prediction_data` | Calcola i dati extra per il soft clustering e la predizione. | Necessario per `all_points_membership_vectors`. |

Il docstring della classe elenca anche `cluster_selection_persistence`, `cluster_selection_epsilon_max` e `max_cluster_size`, che le pagine della guida non discutono.

**Alzare o abbassare i due parametri** (pagine *Parameter Selection* e FAQ):

| Parametro | Più basso | Più alto |
|---|---|---|
| `min_cluster_size` | anche gruppi piccoli contano come cluster | meno cluster, alcuni si fondono; sotto soglia un gruppo non è un cluster e i suoi punti escono dal cluster padre |
| `min_samples` | meno rumore (a 1 quasi tutti i punti sono in un cluster) | più rumore, cluster ristretti alle zone più dense |

- `min_samples` agisce sulla densità del **singolo punto**, `min_cluster_size` sulla taglia del **gruppo**.
- La documentazione non dice come `min_samples` cambia il *numero* di cluster: descrive solo l'effetto su rumore ed estensione dei cluster.
- Se `min_samples` non è fissato vale `min_cluster_size`, quindi alzare `min_cluster_size` alza anche `min_samples` e il rumore. La pagina precisa che `min_cluster_size` si comporta secondo l'intuizione solo se `min_samples` è fissato.

**Dalla FAQ.** Troppo rumore: `min_samples` di default è uguale a `min_cluster_size`, abbassarlo riduce il rumore. Un cluster enorme e pochi piccoli: provare `leaf`. Cluster attesi non separati: la densità richiede abbastanza punti, e servono più punti in più dimensioni.

---

## Cosa si legge dopo il fit

| Attributo / funzione | Cosa dà |
|---|---|
| `labels_` | Etichetta per soggetto; `-1` = rumore. I cluster sono numerati da 0 a k−1. |
| `probabilities_` | Forza di appartenenza al **proprio** cluster, da 0 a 1; 0 per il rumore. È il `λ` del punto normalizzato dentro il cluster: dice quanto sta nel nucleo, non quanto è probabile che stia in quel cluster invece che in un altro. |
| `cluster_persistence_` | Stabilità di ogni cluster, da 0 (effimero) a 1 (persiste su tutte le scale). |
| `outlier_scores_` | Punteggio GLOSH: più alto, più il punto è un outlier **locale**. Un punto al bordo di un cluster denso può avere punteggio alto pur essendo clusterizzato. Non coincide con l'etichetta `-1`. |
| `exemplars_` | Punti rappresentativi di ogni cluster (quelli che restano più a lungo). |
| `relative_validity_` | Approssimazione veloce del DBCV. Richiede `gen_min_span_tree=True`. NEMESIS non la usa. |
| `condensed_tree_`, `single_linkage_tree_`, `minimum_spanning_tree_` | Gli alberi dei passi 2-4, con conversione in pandas/NetworkX e grafici. Larghezza di un ramo = numero di punti; lunghezza = persistenza. |
| `hdbscan.validity.validity_index` | Indice di validità basato sulla densità (DBCV). |
| `hdbscan.prediction.approximate_predict` | Etichetta e forza per punti **nuovi**, senza modificare l'albero (il metodo è transduttivo: riaddestrare ogni tanto per evitare derive). Richiede `prediction_data=True`. |
| `hdbscan.branches.BranchDetector` | Rami (forme a Y) dentro un cluster, sull'eccentricità invece che sulla densità. |

### Soft clustering

`hdbscan.all_points_membership_vectors(clusterer)` restituisce una matrice soggetti × cluster: la probabilità che il soggetto `i` sia nel cluster `j`. Richiede `prediction_data=True` e non funziona con `metric="precomputed"`.

Come è calcolata (pagina *How Soft Clustering Works*):
- **Parte basata sulla distanza**: per ogni cluster, l'inverso della distanza minima dagli *exemplars* del cluster, normalizzato a somma 1.
- **Parte basata sull'outlier** (derivata da GLOSH): per ogni cluster, il punteggio `λ_max / (λ_max − altezza di fusione)`, normalizzato.
- **Combinazione**: le due distribuzioni si combinano con Bayes, `(distanza × outlier) / somma`. Dà una probabilità *condizionata* a stare in un cluster, che somma a 1.
- **Probabilità non condizionata**: il vettore si moltiplica per `P(il punto è in qualche cluster) = altezza massima di fusione / λ_max del cluster più vicino`. Per questo **le righe non sommano a 1**: i punti rumore hanno probabilità bassa su tutti i cluster, e la parte mancante è la probabilità di essere rumore.

Limiti dichiarati: la sola parte basata sulla distanza non segue bene la varietà e perde probabilità tra cluster vicini; la sola parte basata sull'outlier dà molti punti "grigi"; non c'è una scelta ottimale tra softmax e normalizzazione semplice.

**Lettura in NEMESIS.** Per un soggetto con etichetta `c`, la probabilità nella colonna `c` è "quanto è soggetto di quel cluster". Il rumore riceve comunque un vettore: si vede a quale cluster è più vicino, ma resta rumore per la partizione.

---

## Differenze dall'HDBSCAN di scikit-learn

I due non danno la stessa partizione con gli stessi numeri. Misurato sui 10 embedding e matrici di NEMESIS (griglia `min_cluster_size` × `min_samples` di 28 combinazioni):

- **Convenzione di `min_samples`.** Nel pacchetto la core distance è la distanza dal `k`-esimo vicino (pagina *How HDBSCAN Works*); con `min_samples − 1` il pacchetto riproduce sklearn quasi esattamente (ARI 0,95-1,00 su `min_samples` ≥ 5); con `min_samples = 1` serve 1, perché 0 non è accettato. Il docstring della classe dice invece che `min_samples` "include il punto stesso": il comportamento misurato corrisponde alla pagina della guida, non al docstring.
- **MST approssimato.** Il pacchetto lo accetta di default (`approx_min_span_tree=True`); sklearn calcola l'MST esatto. Da solo sposta poco (ARI 0,988 contro 1,000 in una combinazione).
- **Esito.** Con gli stessi numeri l'ARI per combinazione contro le run sklearn ha mediana tra 0,67 e 0,998 a seconda della matrice, con minimi vicini a 0. Le run `hdbscan` e `hdbscan_soft` non si confrontano combinazione per combinazione.

---

## Come lo usa NEMESIS (`hdbscan_soft`)

- **Perché esiste**: per la probabilità di appartenere a ciascun cluster (soft clustering), che sklearn non offre.
- **Griglia di tuning** (`config/registry/params_clustering.json`): `min_cluster_size` × `min_samples` × `cluster_selection_method` (`eom`, `leaf`), con `approx_min_span_tree=False` fisso: il risultato non dipende dall'approssimazione, e su queste dimensioni costa poco. `alpha` resta a 1 e `allow_single_cluster` a falso: la documentazione sconsiglia il primo e il secondo serve solo per dati omogenei.
- **Colonne in più** in `tuning_results.csv`, rispetto a `hdbscan`: `membership_mean` (media, sui non-rumore, della probabilità di stare nel proprio cluster), `membership_share_below_half` (quota di non-rumore sotto 0,5) e `persistence_mean` (media di `cluster_persistence_`).
- **Produzione**: una run salva `membership.npy` (la matrice soggetti × cluster) e `membership_own` in `metadata.csv`; la sezione 3.2 di `clustering_evaluation.ipynb` le legge.
- **Cosa non usa**: `relative_validity_`/DBCV (scartato in tutto il progetto), `approximate_predict`, `cluster_selection_epsilon` (dipende dalla scala dell'embedding), rilevamento dei rami.
- **Quando i cluster sono zero** (tutto rumore): le colonne di silhouette e quelle del pacchetto valgono NaN, e il log lo dice.
