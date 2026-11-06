# Clustering validation

Bozza nella radice del repo, destinata a `knowledge/`.

**Fonti**: le slide di Bicego (*Clustering - parte 1 e 2*, 2021, in `knowledge/papers/methods/Slides_Bicego/`, citate come «Bicego L4a:N» e «Bicego L4b:N» con il numero di slide) e la letteratura (numeri tra parentesi quadre, elenco in fondo). La tabella del §8 dice quali indici usa il progetto (NEMESIS) e quali Bicego.

---

## 1. Che cos'è la validazione

**Il problema** (Bicego L4a:19, 40). Ogni algoritmo di clustering genera *sempre* un risultato, quindi ci si chiede se esista una giustificazione per quel clustering o se i dati siano senza struttura. Approcci diversi portano di solito a clustering diversi: quelli trovati sono ottimali, e in che senso? Manca il *ground truth* (il processo non è supervisionato): i cluster trovati sono significativi, quanti gruppi ci sono, esiste davvero una struttura? La soluzione tipica, dice Bicego, è la conoscenza del settore applicativo.

**Definizione** (Bicego L4b:57). La validazione del clustering è l'insieme di procedure che valutano il risultato di un'analisi di clustering in modo **quantitativo e oggettivo**.

- **Validazione soggettiva**: è diversa. È data dal contesto applicativo, con la conoscenza a priori sul problema, e coincide con l'«interpretazione dei risultati». Per Bicego l'interpretabilità dei metodi e delle soluzioni è spesso fondamentale per validare (L4a:43).
- **Validazione oggettiva**: è la parte che Bicego sviluppa. È una misura quantitativa della capacità della struttura trovata di spiegare i dati, indipendentemente dal contesto.

Questa nota tratta la validazione oggettiva.

**Domande a cui rispondono gli indici per partizioni** (Bicego L4b:60):

- La partizione ha un buon match con le categorie?
- Quanti cluster ci sono nel dataset?
- Dove deve essere tagliato il dendrogramma?
- Quale tra due partizioni date fitta meglio il dataset?

---

## 2. Tassonomia

**Cosa si valida** (Bicego L4b:58). Gli indici cambiano secondo l'oggetto:

- **Gerarchie**: il risultato degli algoritmi gerarchici, o una gerarchia esistente (per esempio un modello teorico).
- **Partizioni**: il risultato degli algoritmi partizionali, o una partizione esistente derivata da informazioni di categoria.
- **Clusters**: sottoinsiemi di pattern, derivati da una cluster analysis o da informazione di categorie.

**Tipi di indici** (Bicego L4b:59):

| Tipo | Cosa fa | Sezione |
|---|---|---|
| Esterni | confrontano il risultato con etichette note a priori | §4 |
| Interni | usano solo i dati, in modo completamente non supervisionato | §5 |
| Relativi | confrontano due risultati di clustering | Bicego li definisce e non nomina indici; le formule degli esterni valgono anche per due clustering |

**Oltre i tre tipi di Bicego**, la letteratura e l'uso distinguono:

- **Prima del clustering**: la *cluster tendency*, cioè se i dati hanno una struttura da cercare (§3).
- **Indici specifici di una famiglia di algoritmi**: esistono solo per i metodi gerarchici o per quelli a densità (§6).
- **Dopo il clustering, sulla robustezza**: la stabilità al ricampionamento (§7).

---

## 3. Cluster tendency

Bicego L4b:72-75. Gli algoritmi di clustering producono sempre un output, qualunque sia il dataset. La *cluster tendency* è l'identificazione, **senza effettuare il clustering**, della predisposizione dei dati ad aggregarsi in gruppi naturali. È un'operazione preliminare cruciale: evita di applicare metodologie elaborate di clustering e di validazione a dati in cui i cluster sono certamente artefatti dell'algoritmo.

- **Idea**: studiare lo spazio delle feature per distinguere tre situazioni: pattern disposti **a caso** (*spatial randomness*), **aggregati** (mutua attrazione), **spaziati regolarmente** (mutua repulsione). Nei casi di disposizione casuale e regolare non ha senso fare clustering.
- **Test**: si verifica se esiste una struttura, per esempio testando una distribuzione uniforme in una finestra (*sampling window*).
- **Scan test**: si conta il numero di pattern nella sottoregione più popolosa; se è inusualmente grande, esiste un clustering. **Problemi** dichiarati da Bicego: come definire le sottoregioni e che cosa significhi «inusualmente grande».

---

## 4. Indici esterni

Confrontano due partizioni degli stessi soggetti: U (il risultato del clustering) e V (il clustering «vero», derivato dalle etichette note a priori) (Bicego L4b:61, 63). Il confronto è a **coppie** di soggetti, quindi non dipende dai nomi dei cluster, che sono arbitrari.

**Quantità di base** (Bicego L4b:62-65).

- **Funzione indicatrice**: $I_U(i,j)$ vale 1 se i soggetti $i$ e $j$ stanno nello stesso cluster secondo $U$ (0 altrimenti); lo stesso per $I_V$.
- **Contingenza delle coppie**:

| | stesso cluster in V | cluster diversi in V |
|---|---|---|
| **stesso cluster in U** | $a$ | $b$ |
| **cluster diversi in U** | $c$ | $d$ |

- $a$: coppie nello stesso cluster in entrambe le partizioni. $b$: nello stesso cluster in U ma non in V. $c$: nello stesso cluster in V ma non in U. $d$: in cluster diversi in entrambe.
- Matematicamente $a = \sum I_U I_V$, $b = \sum I_U (1 - I_V)$, $c = \sum (1 - I_U) I_V$, $d = \sum (1 - I_U)(1 - I_V)$.
- Quantità derivate: $m_1 = a+b$ (coppie unite in U), $m_2 = a+c$ (coppie unite in V), $M = a+b+c+d$ (tutte le coppie).
- Le somme delle slide sono scritte su $i, j$, ma le formule dividono per $\binom{n}{2}$: si intendono coppie non ordinate, $i < j$.

**Gli indici di Bicego** (L4b:66): «l'idea generale è quella di misurare quanto vanno d'accordo le due partizioni».

| Indice | Formula | Intervallo | Cosa misura (lettura nostra: le slide danno solo la formula) |
|---|---|---|---|
| Rand | $\dfrac{a+d}{\binom{n}{2}}$ | 0-1 | quota di coppie su cui le due partizioni concordano, unite in entrambe o separate in entrambe |
| Jaccard | $\dfrac{a}{a+b+c}$ | 0-1 | come Rand ma ignora $d$: tra le coppie unite in almeno una partizione, quante lo sono in entrambe |
| Fowlkes & Mallows | $\dfrac{a}{\sqrt{m_1 m_2}}$ | 0-1 | media geometrica di $\frac{a}{a+b}$ e $\frac{a}{a+c}$: quanto le coppie unite in una partizione lo sono anche nell'altra |
| Γ statistic | $\dfrac{Ma - m_1 m_2}{\sqrt{m_1 m_2 (M-m_1)(M-m_2)}}$ | -1-1 | correlazione di Pearson tra le due matrici di coppie 0/1; usa anche $d$ attraverso $M$ |

Sono tutti simmetrici in U e V (scambiare le due partizioni scambia $b$ e $c$).

**Rand corretto per il caso: l'ARI** [1]. Due partizioni casuali hanno comunque un Rand alto, perché con molti cluster quasi tutte le coppie sono separate in entrambe ($d$ grande); il valore di base dipende dal numero e dalla dimensione dei cluster. L'*Adjusted Rand Index* toglie quel valore di base:

$$
\mathrm{ARI} = \frac{\mathrm{RI} - \mathbb{E}[\mathrm{RI}]}{\max \mathrm{RI} - \mathbb{E}[\mathrm{RI}]} = \frac{2(ad - bc)}{(a+b)(b+d) + (a+c)(c+d)}
$$

con il valore atteso calcolato su partizioni con le stesse dimensioni dei cluster scelte a caso [1]. Vale circa 0 per partizioni casuali, 1 per partizioni identiche, e può essere negativo. Jaccard e Fowlkes-Mallows non sono corretti per il caso.

**Esempio.** Dalla slide 62 (Bicego L4b:62), U = {1,2,4} | {3,5,6}. Come V prendo {1,2} | {3,4,5,6}, inventato per l'esempio. Delle 15 coppie, $a=4$, $b=2$, $c=3$, $d=6$; $m_1=6$, $m_2=7$.

| Indice | Valore |
|---|---|
| Rand | 0,667 |
| Jaccard | 0,444 |
| Fowlkes-Mallows | 0,617 |
| Γ | 0,327 |
| ARI | 0,324 |

Calcolati a mano; Rand, Fowlkes-Mallows e ARI coincidono con scikit-learn 1.8.0 (`rand_score`, `fowlkes_mallows_score`, `adjusted_rand_score`) [2].

**Serve un ground truth?** Per Bicego sì: V è il clustering «vero» ricavato dalle etichette. Le formule però chiedono solo due partizioni degli stessi soggetti, senza sapere se una sia vera. Senza ground truth l'indice misura l'**accordo** tra le due, non la correttezza di una: per questo vale anche come indice relativo.

---

## 5. Indici interni

Misurano il fitting tra una partizione data e il dataset, senza etichette. Bicego li dichiara «difficili da stimare» (L4b:67):

- **Il problema fondamentale** è stimare il numero di cluster. Esistono molti metodi (per esempio quelli di *model selection* per modelli probabilistici).
- **Stima della baseline**: richiederebbe di campionare molti dataset e stimare un indice interno su ciascuno, ma con quale modello si campionano i dati?
- **Dipendenza dai parametri**: gli indici interni dipendono strettamente dal numero di feature, di pattern e di cluster.

### 5.1 Silhouette (Rousseeuw 1987)

**Definizione** [3]. Per il soggetto $i$ nel cluster $A$:

$$
a(i) = \frac{1}{|A|-1} \sum_{j \in A,\, j \neq i} d(i,j), \qquad
b(i) = \min_{C \neq A} \frac{1}{|C|} \sum_{j \in C} d(i,j)
$$

$$
s(i) = \frac{b(i) - a(i)}{\max\{a(i),\, b(i)\}} \in [-1, 1]
$$

- $a(i)$ è la distanza media dai compagni di cluster, $b(i)$ quella dal cluster più vicino.
- Se $|A| = 1$, Rousseeuw pone $s(i) = 0$ [3].
- La silhouette di una partizione è la media degli $s(i)$. `sklearn.metrics.silhouette_score` restituisce questa media su tutti i soggetti e richiede tra 2 e $n-1$ cluster [2].
- Rousseeuw propone la media della silhouette (*average silhouette width*) come criterio per scegliere il numero di cluster e il grafico delle silhouette per cluster come diagnostica [3].

**Tre nomi per cose vicine.** In letteratura e nei programmi «silhouette» indica tre numeri diversi:

| Nome | Cosa è | Dove compare |
|---|---|---|
| *silhouette* (o *Silhouette Coefficient* di un campione) $s(i)$ | il valore di **un soggetto** | Rousseeuw 1987 [3]; in scikit-learn il valore per campione è `silhouette_samples` [2] |
| *average silhouette width* $\bar{s}(k)$ | la **media** degli $s(i)$ su una partizione in $k$ cluster | Rousseeuw 1987 [3]; in scikit-learn `silhouette_score` [2] |
| *silhouette coefficient* SC | il **massimo** di $\bar{s}(k)$ al variare di $k$ | Kaufman & Rousseeuw 1990, p. 87, secondo [5]; il libro non è stato consultato |

**Le fasce di lettura**, attribuite a Kaufman & Rousseeuw (1990) [4]:

| Silhouette | Lettura |
|---|---|
| 0,71 - 1,00 | struttura forte |
| 0,51 - 0,70 | struttura ragionevole |
| 0,26 - 0,50 | struttura debole, forse artificiale |
| ≤ 0,25 | nessuna struttura sostanziale |

- **Fonte indiretta.** Il testo del 1990 non è nel repo: le fasce sono riportate da fonti secondarie, una tabella di un articolo PLOS ONE [6] e, in forma discorsiva, Wikipedia [5]. Gli estremi cambiano da una fonte all'altra (0,25 oppure 0,26).
- **A cosa si riferiscono.** Nella definizione di Kaufman & Rousseeuw il numero che si legge con la scala è SC, il massimo su $k$ [5]. Applicarla alla media di una singola partizione è un'estensione dell'uso originale.
- **È una convenzione, non un test.** Una nuvola senza cluster ha comunque una silhouette positiva con un clustering gerarchico.
- **Dipende dalla forma dei cluster**: premia cluster compatti e convessi.
- **Due silhouette** calcolate con distanze diverse, o su spazi diversi, non si confrontano.

**Esempio.** Cinque punti su una retta: 0, 1, 2 (cluster 1) e 6, 7 (cluster 2). Per il punto 0: $a = (1+2)/2 = 1{,}5$, $b = (6+7)/2 = 6{,}5$, $s = (6{,}5 - 1{,}5)/6{,}5 = 0{,}77$. La media sui cinque punti è 0,78 (scikit-learn 1.8.0).

### 5.2 Calinski-Harabasz (1974)

**Definizione** [7]. Con $n$ soggetti, $k$ cluster, $B$ la matrice di dispersione tra i cluster e $W$ quella dentro i cluster:

$$
\mathrm{CH} = \frac{\operatorname{tr}(B)/(k-1)}{\operatorname{tr}(W)/(n-k)}, \qquad
\operatorname{tr}(W) = \sum_{q=1}^{k} \sum_{i \in C_q} \lVert x_i - c_q \rVert^2, \qquad
\operatorname{tr}(B) = \sum_{q=1}^{k} n_q \lVert c_q - c \rVert^2
$$

dove $c_q$ è il centroide del cluster $q$ e $c$ quello di tutti i dati.

- **Direzione**: più alto è meglio. Non ha un massimo né una scala assoluta.
- **Cosa assume**: centroidi e somme di quadrati, quindi geometria euclidea e cluster compatti attorno a un centro.

### 5.3 Davies-Bouldin (1979)

**Come lo presenta Bicego** (L4b:68-71). Davies e Bouldin (1979) lo usarono inizialmente per decidere quando fermare un clustering sequenziale. L'indice si calcola **al variare del numero di cluster** e il miglior clustering corrisponde al **valore minimo**. Con $\{x_1, \dots, x_N\}$ i punti e $C_1, \dots, C_K$ la partizione da valutare ($n_j$ soggetti nel cluster $j$):

$$
m_j = \frac{1}{n_j} \sum_{x_i \in C_j} x_i, \qquad
e_j^2 = \frac{1}{n_j} \sum_{x_i \in C_j} (x_i - m_j)^T (x_i - m_j), \qquad
dm(j,h) = d(m_j, m_h)
$$

- $m_j$ è il centroide, $e_j^2$ la *within cluster variation*, $dm(j,h)$ la *between cluster variation*.
- Per ogni coppia di cluster $R_{jh} = \dfrac{e_j + e_h}{dm(j,h)}$; per ogni cluster $R_j = \max_{h \neq j} R_{jh}$; infine $\mathrm{DB} = \dfrac{1}{K} \sum_{j=1}^{K} R_j$.
- **Più piccolo è il valore, migliore è il clustering.**
- Bicego lo usa anche per capire se c'è struttura: con dati a cluster forti la curva di DB al variare di $K$ ha un minimo netto (vicino a 0, a $K = 4$ nell'esempio della slide 71), con cluster deboli il minimo è più alto, e la figura confronta i due casi con dati casuali (valori letti dalla descrizione della figura, approssimati).

**Come lo definisce la letteratura** [8]. Per ogni cluster $i$ una dispersione $S_i$ e, per ogni coppia, la distanza tra i centroidi $M_{ij}$:

$$
S_i = \Big( \frac{1}{|C_i|} \sum_{x \in C_i} \lVert x - c_i \rVert^{q} \Big)^{1/q}, \qquad
R_{ij} = \frac{S_i + S_j}{M_{ij}}, \qquad
\mathrm{DB} = \frac{1}{k} \sum_{i=1}^{k} \max_{j \neq i} R_{ij}
$$

- Davies e Bouldin lasciano liberi gli esponenti [8]. scikit-learn usa la distanza media dal centroide ($q = 1$) [2].
- **Differenza con Bicego** (lettura nostra dei due testi): in Bicego $e_j$ è la radice di $e_j^2$, cioè la radice della distanza quadratica media dal centroide, che corrisponde a $q = 2$. I due numeri non coincidono.
- **Cosa misura**: per ogni cluster il caso peggiore, cioè il cluster che gli è più simile. Penalizza due cluster vicini anche se ciascuno è compatto, e a volte non è d'accordo con la silhouette.
- Come CH, usa i centroidi: presuppone geometria euclidea.

**Esempio** (stessi 5 punti del §5.1): $S_1 = 2/3$, $S_2 = 0{,}5$, $M_{12} = 5{,}5$. Con scikit-learn ($q = 1$) $\mathrm{DB} = (2/3 + 0{,}5)/5{,}5 = 0{,}21$. Con la formula di Bicego $e_1 = \sqrt{2/3} = 0{,}82$, $e_2 = 0{,}5$ e $\mathrm{DB} = 1{,}32/5{,}5 = 0{,}24$. CH vale 43,6 (scikit-learn 1.8.0).

### 5.4 Dunn (1974)

$$
D = \frac{\min_{i \neq j} \delta(C_i, C_j)}{\max_{q} \Delta(C_q)}
$$

con $\delta$ la minima distanza tra due punti di cluster diversi e $\Delta$ il diametro massimo di un cluster [9]. Più alto è meglio. Dipende da un solo arco e da un solo diametro, quindi un solo outlier lo sposta molto.

### 5.5 DBCV (Moulavi et al. 2014)

**Perché esiste.** Gli indici dei §5.1-5.4 premiano cluster convessi. DBCV (*Density-Based Clustering Validation*) è pensato per cluster di forma arbitraria e per partizioni con rumore [10].

**Definizione** [10]. Per un oggetto $o$ in un cluster di $n_i$ oggetti, in dimensione $d$, la *all-points core distance* è una media armonica generalizzata delle distanze dai vicini nel cluster:

$$
a_{\text{core}}(o) = \left( \frac{\sum_{j=2}^{n_i} \big(1/\mathrm{KNN}(o, j)\big)^{d}}{n_i - 1} \right)^{-1/d}
$$

Con questa core distance si definisce una distanza di raggiungibilità reciproca (come in HDBSCAN) e l'albero di copertura minimo (MST) di ogni cluster. Poi:

- **sparsità** $\mathrm{DSC}(C_i)$: l'arco più pesante tra i nodi interni dell'MST di $C_i$;
- **separazione** $\mathrm{DSPC}(C_i, C_j)$: la minima distanza di raggiungibilità tra i nodi interni dei due MST;

$$
V_C(C_i) = \frac{\min_{j \neq i} \mathrm{DSPC}(C_i, C_j) - \mathrm{DSC}(C_i)}{\max\big\{\min_{j \neq i} \mathrm{DSPC}(C_i, C_j),\ \mathrm{DSC}(C_i)\big\}}, \qquad
\mathrm{DBCV} = \sum_{i} \frac{|C_i|}{|O|}\, V_C(C_i)
$$

- $|O|$ è il numero di **tutti** gli oggetti, rumore compreso: il rumore abbassa DBCV. Ogni cluster pesa per la sua quota di tutti gli oggetti, quindi il valore complessivo non è la media dei cluster.
- Range da -1 a 1, più alto è meglio. Nessun valore di riferimento in letteratura.
- $a_{\text{core}}$ dipende dalla dimensione $d$: per distanze diverse dall'euclidea (per esempio `dice` su dati binari) $d$ non è definita in modo ovvio.
- **Implementazioni**: `hdbscan.validity.validity_index` (con l'argomento `d` per la dimensione); `relative_validity_`, un'approssimazione veloce sul solo MST di HDBSCAN che la documentazione del pacchetto dichiara utile **solo** per confrontare iperparametri, non come misura assoluta [11].
- **Esempio**: per i punti 0, 1, 2, 6, 7, 15 partizionati da HDBSCAN in {0, 1, 2}, {6, 7} e il rumore {15}, `validity_index` dà 0,63 (`hdbscan` 0.8.44).

---

## 6. Indici specifici di una famiglia di algoritmi

Descrivono il fit di un certo tipo di modello.

### 6.1 Metodi gerarchici

**Correlazione cofenetica (Sokal & Rohlf 1962)** [12]. La distanza **cofenetica** $c_{ij}$ tra due soggetti è l'altezza del dendrogramma alla quale i due finiscono per la prima volta nello stesso cluster. La correlazione cofenetica è la correlazione di Pearson tra le distanze originali $d_{ij}$ e le $c_{ij}$, su tutte le coppie:

$$
r_c = \frac{\sum_{i<j} (d_{ij} - \bar d)(c_{ij} - \bar c)}{\sqrt{\sum_{i<j} (d_{ij} - \bar d)^2 \, \sum_{i<j} (c_{ij} - \bar c)^2}}
$$

- Sokal & Rohlf la introducono per confrontare dendrogrammi ottenuti con metodi diversi [12].
- **Range**: da -1 a 1; vicino a 1 l'albero rispetta le distanze (`scipy.cluster.hierarchy.cophenet`).
- **Cosa non dice**: niente sul numero di cluster né sull'utilità dei cluster. Misura la fedeltà dell'albero intero, quindi è dominata dalle coppie lontane (la maggioranza).
- Si confronta tra linkage della **stessa** metrica: le altezze di ward e quelle di average non sono nella stessa unità.
- **Esempio** (5 punti del §5.1, scipy 1.17.0): single 0,935, complete 0,937, average 0,938, ward 0,938. Differenze di questa entità non bastano a scegliere un linkage.

**Salto del dendrogramma** (diagnostica nostra, non una definizione di letteratura). Risponde alla domanda di Bicego «dove deve essere tagliato il dendrogramma?» (L4b:60): l'altezza della fusione da $k$ a $k-1$ divisa per quella da $k+1$ a $k$. Vicino a 1 non c'è un taglio naturale a $k$; più è alto, più il taglio è netto. Le altezze sono nelle unità di ogni linkage, quindi non si confronta tra linkage diversi.

### 6.2 Metodi a densità (HDBSCAN)

**Stabilità di un cluster (Campello et al. 2013)**. Con $\lambda = 1/\varepsilon$ (l'inverso della distanza di taglio), un cluster $C$ nasce a $\lambda_{\min}(C)$ e ogni suo punto $x$ ne esce a $\lambda_{\max}(x, C)$ [13]:

$$
S(C) = \sum_{x \in C} \big( \lambda_{\max}(x, C) - \lambda_{\min}(C) \big)
$$

È il criterio con cui HDBSCAN sceglie i cluster, non un indice esterno: un cluster stabile è uno che persiste su un ampio intervallo di densità. Il pacchetto `hdbscan` la normalizza in [0, 1] in `cluster_persistence_`, dividendo per la taglia del cluster e per il $\lambda$ massimo dell'albero (`hdbscan` 0.8.44, `_hdbscan_tree.pyx::get_stability_scores`). Nessuna soglia: in letteratura non c'è un riferimento.

**Probabilità di appartenenza.** Per ogni soggetto, da 0 a 1, calcolata **dentro il cluster**: vicino a 1 il soggetto sta nel cuore, vicino a 0 sta al margine. **Non** è la probabilità di stare in questo cluster invece che in un altro, e non è confrontabile tra cluster di densità diversa. Su un embedding molto compatto (per esempio UMAP con `min_dist` = 0) misura anche quanto l'embedding ha impacchettato il cluster. La versione *soft* di HDBSCAN dà in più la matrice soggetti × cluster dell'appartenenza.

**Frazione di rumore** (diagnostica nostra, non un indice di letteratura con un nome proprio):

$$
\text{noise\_fraction} = \frac{|\{i : \ell_i = -1\}|}{n}
$$

È la quota di soggetti etichettati come rumore. Conta perché silhouette, CH, DB e Dunn si calcolano sui soli soggetti clusterizzati: una combinazione che manda nel rumore i soggetti difficili lascia i più facili e fa salire gli indici senza che la partizione sia migliore. DBCV evita il problema pesando ogni cluster sul **totale** dei soggetti, rumore compreso [10].

---

## 7. Stabilità al ricampionamento

«Stabilità» indica in letteratura cose diverse. Quella al ricampionamento chiede se i cluster si ritrovano su dati perturbati.

- **Bootstrap, come lo presenta Bicego** (L4a:41-42, esempio della filogenesi). Si creano $N$ nuovi dataset (per esempio 1000) campionando a caso le **colonne** con rimpiazzo, così ogni dataset ha le stesse specie con alcuni nucleotidi duplicati e altri rimossi. Per ognuno si costruisce l'albero (il clustering) e si calcola la frequenza con cui ogni gruppo o sottogruppo compare. Un gruppo trovato spesso è robusto, quindi significativo.
- **Hennig 2007** [14]: la stabilità di ogni cluster è la similarità di Jaccard media con il cluster più simile ottenuto su campioni bootstrap. Ricampiona i soggetti, a differenza di Bicego che ricampiona le colonne.
- **Monti et al. 2003** [15]: matrice di consenso su sottocampioni: $C_{ij}$ è la co-assegnazione di $i$ e $j$ divisa per il numero di volte in cui sono stati campionati insieme. Applicabile anche al clustering gerarchico.
- **PAC** (*Proportion of Ambiguous Clustering*): la quota di coppie con co-occorrenza in una banda ambigua, per default $(0.1, 0.9)$ [16]:

$$
\mathrm{PAC} = \frac{\#\{(i<j) : 0.1 < C_{ij} < 0.9\}}{n(n-1)/2}
$$

  Șenbabaoğlu, Michailidis & Li lo propongono al posto dell'area sotto la CDF di Monti et al., che mostrano essere distorta verso $k$ grandi [16].

---

## 8. Tabella riassuntiva

«NEMESIS» indica un indice calcolato dal progetto.

| Indice | Tipo | Bicego | NEMESIS |
|---|---|---|---|
| Rand | esterno | sì | no (sostituito dall'ARI) |
| ARI | esterno | no | sì |
| Jaccard | esterno | sì | no |
| Fowlkes-Mallows | esterno | sì | no |
| Γ statistic | esterno | sì | no |
| Davies-Bouldin | interno | sì | sì |
| Silhouette | interno | no | sì |
| Calinski-Harabasz | interno | no | sì |
| Dunn | interno | no | sì |
| DBCV | interno, per la densità | no | sì |
| Correlazione cofenetica | metodi gerarchici | no | sì |
| Salto del dendrogramma | metodi gerarchici | no | sì (diagnostica nostra) |
| Stabilità del cluster (persistenza) | metodi a densità | no | sì |
| Probabilità di appartenenza | metodi a densità | no | sì |
| Frazione di rumore | metodi a densità | no | sì (diagnostica nostra) |
| Cluster tendency (scan test) | prima del clustering | sì | no |
| Bootstrap sulle colonne | stabilità | sì | no |
| Hennig, Monti, PAC | stabilità | no | no (solo letteratura) |

---

## 9. Insidie comuni

1. **Ogni indice interno assume una forma dei cluster.** Silhouette, Calinski-Harabasz, Davies-Bouldin e Dunn presuppongono cluster compatti e convessi; per cluster di forma arbitraria o con rumore serve un indice a densità (DBCV).
2. **Il rumore falsa gli indici.** Gli indici calcolati sui soli soggetti clusterizzati salgono se il rumore assorbe i soggetti difficili. Negli indici a coppie, contare il rumore come un cluster unico conta come «unite» tutte le sue coppie, e inventa una somiglianza tra soggetti che nessun cluster ha accolto.
3. **Spazi e metriche diverse, numeri non confrontabili.** Gli indici interni dipendono da numero di feature, di pattern e di cluster (Bicego L4b:67): la stessa silhouette su due spazi, o con due distanze, non è la stessa cosa.
4. **Su un embedding si misura l'embedding.** UMAP non preserva la densità e può creare «false tears» (fratture) [17]: indici alti su un embedding molto compatto possono dire più dei suoi parametri che dei dati.
5. **Un ottimo al variare di k è un candidato, non una prova.** La silhouette media massima o il minimo di Davies-Bouldin esistono anche su una nuvola senza cluster.
6. **Partizioni degeneri.** Con un solo cluster, o con ogni soggetto da solo, molti indici sono indefiniti (la silhouette richiede tra 2 e $n-1$ cluster, il denominatore di Γ si annulla, DBCV richiede almeno 2 cluster). In `hdbscan.validity.validity_index` il caso «tutto rumore» restituisce l'intero `0`, indistinguibile da un punteggio vero; con un solo cluster restituisce `nan` e un avviso; con un cluster di un solo soggetto solleva un errore.
7. **Accordo non vuol dire correttezza.** Un ARI alto tra due partizioni dice che coincidono, non che siano giuste.

---

## Fonti

**Slide**

- Bicego, M. (2021). *4. Clustering - parte 1* e *4. Clustering - parte 2* (dispense, Università di Verona) - `knowledge/papers/methods/Slides_Bicego/`. Le citazioni «L4a:N» e «L4b:N» rimandano al numero di slide.

**Letteratura**

1. Hubert, L., Arabie, P. (1985). Comparing partitions. *Journal of Classification*, 2(1), 193-218. doi:10.1007/BF01908075
2. scikit-learn 1.8.0, *Clustering performance evaluation* (silhouette, Calinski-Harabasz, Davies-Bouldin, Rand, ARI, Fowlkes-Mallows): https://scikit-learn.org/stable/modules/clustering.html#clustering-performance-evaluation
3. Rousseeuw, P. J. (1987). Silhouettes: a graphical aid to the interpretation and validation of cluster analysis. *Journal of Computational and Applied Mathematics*, 20, 53-65. doi:10.1016/0377-0427(87)90125-7
4. Kaufman, L., Rousseeuw, P. J. (1990). *Finding Groups in Data: An Introduction to Cluster Analysis*. Wiley. doi:10.1002/9780470316801 (non consultato direttamente: le fasce sono riportate dalle fonti secondarie [5], [6])
5. Wikipedia, *Silhouette (clustering)*: https://en.wikipedia.org/wiki/Silhouette_(clustering) (fonte secondaria: definizione di $s(i)$, il nome *silhouette coefficient* come massimo su $k$ attribuito a Kaufman & Rousseeuw 1990 p. 87, le soglie 0,7, 0,5 e 0,25 senza fonte; consultata il 21-10-26)
6. Tabella con le fasce di Kaufman & Rousseeuw in un articolo PLOS ONE (fonte secondaria): https://pmc.ncbi.nlm.nih.gov/articles/PMC5978888/table/pone.0198245.t001 (indicata da una ricerca web il 21-10-26: la pagina non è stata aperta, le fasce sono quelle riportate nel riassunto della ricerca)
7. Caliński, T., Harabasz, J. (1974). A dendrite method for cluster analysis. *Communications in Statistics*, 3(1), 1-27. doi:10.1080/03610927408827101
8. Davies, D. L., Bouldin, D. W. (1979). A cluster separation measure. *IEEE Transactions on Pattern Analysis and Machine Intelligence*, PAMI-1(2), 224-227. doi:10.1109/TPAMI.1979.4766909
9. Dunn, J. C. (1974). Well-separated clusters and optimal fuzzy partitions. *Journal of Cybernetics*, 4(1), 95-104. doi:10.1080/01969727408546059
10. Moulavi, D., Jaskowiak, P. A., Campello, R. J. G. B., Zimek, A., Sander, J. (2014). Density-based clustering validation. *Proceedings of the 2014 SIAM International Conference on Data Mining*, 839-847. doi:10.1137/1.9781611973440.96
11. Documentazione del pacchetto `hdbscan` (0.8.44), API reference e docstring di `hdbscan.HDBSCAN` (`relative_validity_`) e `hdbscan.validity.validity_index`: https://hdbscan.readthedocs.io/en/latest/api.html
12. Sokal, R. R., Rohlf, F. J. (1962). The comparison of dendrograms by objective methods. *Taxon*, 11(2), 33-40. doi:10.2307/1217208
13. Campello, R. J. G. B., Moulavi, D., Sander, J. (2013). Density-based clustering based on hierarchical density estimates. *PAKDD 2013*, LNCS 7819, 160-172. doi:10.1007/978-3-642-37456-2_14
14. Hennig, C. (2007). Cluster-wise assessment of cluster stability. *Computational Statistics & Data Analysis*, 52(1), 258-271. doi:10.1016/j.csda.2006.11.025
15. Monti, S., Tamayo, P., Mesirov, J., Golub, T. (2003). Consensus clustering: a resampling-based method for class discovery and visualization of gene expression microarray data. *Machine Learning*, 52, 91-118. doi:10.1023/A:1023949509487
16. Șenbabaoğlu, Y., Michailidis, G., Li, J. Z. (2014). Critical limitations of consensus clustering in class discovery. *Scientific Reports*, 4, 6207. doi:10.1038/srep06207
17. Documentazione di `umap-learn` (0.5), *Using UMAP for Clustering*: https://umap-learn.readthedocs.io/en/latest/clustering.html (copia in `knowledge/papers/methods/websites/Using_UMAP_for_Clustering.html`)
