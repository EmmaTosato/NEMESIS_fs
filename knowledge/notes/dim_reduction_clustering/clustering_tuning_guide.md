# Guida rapida al tuning del clustering

Manuale operativo: come leggere gli indici e i grafici prodotti da una sweep di tuning, e come decidere cosa fare a partire da quello che vedi.

Definizioni e fonti degli indici: [`clustering_methods/evaluation_metrics.md`](clustering_methods/evaluation_metrics.md). Formule e parametri dei singoli metodi: cartella [`clustering_methods/`](clustering_methods/), indice in [`README.md`](clustering_methods/README.md) (es. [`kmeans.md`](clustering_methods/kmeans.md), [`gmm.md`](clustering_methods/gmm.md), [`spectral.md`](clustering_methods/spectral.md), [`agglomerative.md`](clustering_methods/agglomerative.md), [`hdbscan.md`](clustering_methods/hdbscan.md), [`adp.md`](clustering_methods/adp.md)).

## Regola d'oro

Il tuning **non sceglie mai il valore migliore per te**. Per ogni valore testato calcola indici e grafici diagnostici, li salva su disco, e si ferma lì. La scelta finale del parametro da usare in produzione è sempre una decisione umana, guidata dai plot.

Ogni sweep ha un iperparametro principale per metodo:

| Metodo                          | Parametro testato    |
| ------------------------------- | -------------------- |
| KMeans, Agglomerative, Spectral | `n_clusters`       |
| GMM                             | `n_components`     |
| HDBSCAN, HDBSCAN soft           | `min_cluster_size` |
| ADP                             | `Z`                |

Altri iperparametri si sweepano insieme (griglie in `config/registry/params_clustering.json`): `linkage` e `metric` per Agglomerative, `affinity` per Spectral, `covariance_type` per GMM, `min_samples` per HDBSCAN (HDBSCAN soft anche `cluster_selection_method`), `metric` per ADP. Non tutte le combinazioni sono valide: `linkage="ward"` accetta solo la metrica euclidea, quindi ogni combinazione che li accoppia diversamente viene scartata in automatico (con un avviso in log), non silenziosamente.

---

## I 3 indici universali

Calcolati per KMeans, GMM, Spectral, Agglomerative e ADP (non per HDBSCAN e HDBSCAN soft, vedi sotto), sempre nello stesso file (`tuning_plot.png`), uno per sotto-grafico.

| Indice                      | Range    | Direzione           | Come leggerlo                                                                                                                                                                                                                                                                                  |
| --------------------------- | -------- | ------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Silhouette**        | −1 → 1 | più alto = meglio  | Vicino a 1: cluster compatti e separati. Vicino a 0: cluster che si sovrappongono. Negativo: punti probabilmente nel cluster sbagliato. È l'unico dei tre con un valore assoluto interpretabile da solo — gli altri due si leggono solo per confronto tra valori diversi dello stesso sweep. |
| **Calinski-Harabasz** | 0 → +∞ | più alto = meglio  | Rapporto tra separazione fra i cluster e compattezza dentro ciascun cluster. Tende quasi sempre a crescere insieme al numero di cluster: da solo non basta per scegliere il numero di cluster, usalo come conferma.                                                                            |
| **Davies-Bouldin**    | 0 → +∞ | più basso = meglio | Media di quanto ogni cluster è disperso rispetto a quanto è vicino al suo "vicino" più simile. È l'unico dei tre che penalizza esplicitamente due cluster troppo ravvicinati — per questo a volte non è d'accordo con Silhouette.                                                        |

**Come decidere:**

1. Se tutti e tre puntano allo stesso valore, la scelta è solida: usalo.
2. Se **Silhouette e Davies-Bouldin non sono d'accordo** (capita spesso), non è un errore — è un segnale reale sulla struttura dei dati:
   - Silhouette alto a un valore basso → pochi macro-gruppi, molto separati tra loro.
   - Davies-Bouldin basso a un valore alto → sottogruppi più fini, compatti al loro interno.
3. In caso di conflitto non esiste una regola meccanica. Guarda anche la diagnostica specifica del metodo (dendrogramma, eigengap, ecc. — sotto) prima di decidere, e valuta il risultato anche dal punto di vista clinico.

### Fasce di valori: cosa dice la letteratura

Solo la silhouette ha una scala di interpretazione citata in letteratura (Kaufman & Rousseeuw 1990: 0.71-1.00 forte, 0.51-0.70 ragionevole, 0.26-0.50 debole, fino a 0.25 nessuna struttura; riportata da fonti secondarie, il libro non è nel repo). È una **convenzione**, non un risultato: il progetto **non la usa** e il `report.md` del tuning si limita a dire che esiste. Cosa dice, a cosa si riferisce (il massimo della silhouette media su tutti i k, non una singola partizione), perché gli estremi cambiano da fonte a fonte e quali sono i suoi limiti: [`clustering_methods/evaluation_metrics.md`](clustering_methods/evaluation_metrics.md), §2.

- **Limiti noti**: funziona meglio con cluster convessi; con dati ad alta dimensione tende a dare valori più bassi (Wikipedia, "Silhouette (clustering)").
- **Davies-Bouldin e Calinski-Harabasz**: nessuna fascia con fonte. Le fonti secondarie consultate li descrivono come indici da usare per confronto tra partizioni degli stessi dati (Davies-Bouldin: più basso è meglio; Calinski-Harabasz: si prende il k che lo massimizza). Le pagine che parlano di "vicino a 0" per Davies-Bouldin o di "sotto 1" per Calinski-Harabasz non citano una fonte. I testi originali (Davies & Bouldin 1979; Caliński & Harabasz 1974) non sono stati consultati.
- **Calinski-Harabasz** favorisce gruppi globulari e di dimensioni simili; **Davies-Bouldin** è sensibile a outlier e rumore.

Fonti consultate (secondarie): [Wikipedia, Silhouette (clustering)](https://en.wikipedia.org/wiki/Silhouette_(clustering)), [tabella PLOS ONE](https://pmc.ncbi.nlm.nih.gov/articles/PMC5978888/table/pone.0198245.t001), [Wikipedia, Davies–Bouldin index](https://en.wikipedia.org/wiki/Davies%E2%80%93Bouldin_index), [MetricGate, Calinski-Harabasz](https://metricgate.com/calculator/calinski-harabasz-index), [GraphPad, Calinski-Harabasz](https://www.graphpad.com/guides/prism/latest/statistics/stat_clustering_calinski_harabasz.htm).

### Attenzione a questi tre casi particolari

- **HDBSCAN e HDBSCAN soft**: i 3 indici non si calcolano (escluderebbero il rumore e presuppongono cluster compatti). L'indice interno è il DBCV, che pesa il rumore (sezione "HDBSCAN", sotto). La frazione di rumore è sempre riportata a parte (`noise_fraction`) — mai nascosta, mai fusa nel calcolo.
- **Clustering fatto direttamente sui voxel grezzi (non su un embedding)**: i 3 indici usano distanza euclidea, che su dati binari di lesione è dominata dal volume della lesione più che dalla sua forma o posizione. Il workflow raccomandato è ridurre la dimensionalità prima e poi clusterizzare sull'embedding: il bias si attenua (ma non sparisce del tutto).
- **Agglomerative con `metric` non euclidea**: Silhouette resta sempre calcolabile, ma Calinski-Harabasz e Davies-Bouldin sono per costruzione legati alla geometria euclidea e vengono registrati come vuoti per ogni combinazione che usa una metrica diversa. Se stai leggendo una sweep con più metriche, aspettati colonne vuote per le righe non euclidee: è normale, non un bug. Lo stesso vale per ADP con la distanza `dice` o `jaccard`.

### Due limiti comuni ai tre indici

- **Assumono cluster compatti e rotondeggianti.** Una zona densa di forma irregolare (come quelle che trova HDBSCAN) può avere indici bassi pur essendo un gruppo reale: gli indici la sottovalutano.
- **I valori assoluti non si confrontano tra embedding o matrici diversi.** Ogni embedding (o matrice) è uno spazio con le sue distanze, quindi la stessa silhouette in due spazi non misura la stessa cosa. Conta come l'indice cambia *dentro* la stessa run (al variare di `n_clusters`, di `min_cluster_size`, di `Z`). Per confrontare run su spazi diversi si confrontano le partizioni e le dimensioni dei cluster (sezione "Confrontare la stessa run su embedding diversi", sotto).

---

## Diagnostiche specifiche per metodo

### KMeans — curva "inertia" (elbow)

- **Dove**: colonna in più nello stesso `tuning_plot.png`.
- **Cosa misura**: quanto ogni punto è lontano dal centroide del proprio cluster.
- **Come leggerla**: scende sempre all'aumentare del numero di cluster, quindi non cercare il minimo — cerca il "gomito", il punto dove la curva smette di scendere ripidamente. Da sola è poco decisiva se non c'è un gomito netto: incrociala sempre con Silhouette o Davies-Bouldin.

### Agglomerative — dendrogramma

- **Dove**: un file `dendrogram_metric=<metric>.png` per ogni `metric` testata, con un subplot per ogni `linkage` valido per quella metrica (`ward` con metrica non euclidea è scartato, stessa regola della sweep) — indipendente dal numero di cluster scelto. Il dendrogramma è calcolato per ogni combinazione (`linkage`, `metric`) sweepata, quindi ogni file riflette la propria metrica e ogni subplot il proprio `linkage`.
- **Come si legge**: dal basso verso l'alto. Ogni fusione verticale unisce due sotto-gruppi all'altezza (asse y) della loro distanza di fusione.
- **Cosa cercare**: il salto verticale più grande tra due fusioni consecutive indica il taglio più naturale.
  - Salto grande vicino alla cima → la struttura più forte è binaria (2 cluster).
  - Salto grande più in basso → suggerisce un numero di cluster maggiore.
- **Attenzione**: il colore dei rami non indica il numero di cluster consigliato — conta solo l'altezza dei salti.
- **Confronta i linkage tra loro**: `ward` tende a fusioni regolari, simili a KMeans. `average`/`complete` sono più sensibili agli outlier. `single` tende a incatenare gruppi distinti attraverso pochi punti-ponte, producendo un dendrogramma meno affidabile per la scelta del numero di cluster.

**Come leggere un dendrogramma troncato**

- Con migliaia di soggetti l'albero completo è illeggibile: si disegna solo la parte alta, le ultime 30 foglie (cioè le ultime 29 fusioni). In basso non ci sono soggetti ma rami, e il numero tra parentesi sotto ogni ramo è quanti soggetti contiene.
- L'asse y è la distanza di fusione: più una fusione è in alto, più i due cluster erano lontani.
- **Ogni linkage ha una scala sua** (ward misura un aumento di varianza, single una distanza minima): si confronta la *forma* dell'albero tra pannelli, non l'altezza.
- Una linea orizzontale taglia l'albero e ogni linea verticale che attraversa è un cluster. Nel Dendrogram Explorer (`docs/guides/embedding_app.md`) una linea rossa tratteggiata (`cut_k`) mostra dove cade il taglio che dà quel numero di cluster; i PNG `dendrogram_metric=<metric>.png` non ce l'hanno.
- Il taglio è naturale dove, prima di quelle fusioni, c'è un salto grande: i cluster che stanno per unirsi sono molto più lontani di quelli già uniti. Il rapporto tra due altezze consecutive è esattamente la colonna `jump` di `dendrogram_jump.csv` (`docs/guides/evaluate_clustering_tuning.md`).
- **Esempio didattico.** Le ultime fusioni sono a 20, 8, 1,5, 1,2, 1,0. I salti tra altezze consecutive sono 20 → 8 (2,5 volte) e 8 → 1,5 (circa 5 volte, il più netto): tagliare tra 8 e 1,5 disfa le due fusioni più alte e lascia **3 cluster**.
- Se le fusioni scendono gradualmente, senza un salto che spicchi, l'albero non indica nessun k: la scelta resta una decisione tua, da prendere con gli indici e con la clinica.
- Il dendrogramma dice dove l'albero si divide, non se i cluster sono utili. Sotto le ultime 30 foglie non si vede niente.
- **Seguire l'albero k dopo k.** Passando da k-1 a k cluster esattamente un cluster si divide in due (si disfa la fusione più alta ancora in piedi). Guardare quale cluster si divide, dove stanno i due pezzi nell'embedding e che anatomia hanno aiuta a capire da cosa è fatto un cluster grande (notebook `dendrogram_embedding_explorer`, `docs/guides/evaluate_clustering_tuning.md`).

### Agglomerative — cophenetic correlation

- **Domanda a cui risponde**: quale `linkage` riassume meglio le distanze tra soggetti? Il dendrogramma è una versione semplificata dei dati: nel riassumere migliaia di distanze in un albero qualcosa si deforma, e la cophenetic dice quanto, per ogni linkage.
- **Cosa misura.** Per ogni coppia di soggetti si hanno due distanze: la **distanza vera** (nei dati, calcolata con la `metric`) e la **distanza dell'albero** (*cophenetic*), cioè l'altezza del dendrogramma alla quale i due finiscono per la prima volta nello stesso cluster. La cophenetic correlation è la correlazione tra le due liste, calcolate su tutte le coppie. Un numero per linkage.
- **Esempio didattico.** A e B sono vicinissimi (distanza vera 1) e si fondono subito, a quota 1,2; C è lontano da entrambi (distanza vera 9) e si unisce solo alla fine, a quota 9,5. Le due liste vanno d'accordo, quindi la correlazione è alta. Se invece A e B, pur vicini, si unissero solo in cima all'albero, la correlazione sarebbe bassa: l'albero li tratta come lontani.
- **Come si legge.**
  - Vicino a 1: soggetti vicini si fondono presto e soggetti lontani tardi, l'albero rispetta i dati.
  - Più basso: l'albero ha deformato le distanze. Esempio tipico `single`, che incatena (*chaining*) e fonde gruppi lontani attraverso pochi soggetti-ponte.
  - Differenze di pochi centesimi tra due linkage non permettono di sceglierne uno.
  - Si confrontano solo linkage calcolati con la stessa `metric`; `ward` esiste solo con `euclidean`, quindi le combinazioni non valide non compaiono.
- **Cosa non dice**: misura la fedeltà dell'albero ai dati, non se i cluster sono utili o coerenti con la clinica.

### Agglomerative — indici per `n_clusters`

Per ogni `n_clusters` e `linkage` (per una sola `metric`, di solito `euclidean`; `single` si lascia fuori dal confronto perché la sua silhouette scende molto sotto quella degli altri) silhouette e Davies-Bouldin (le curve `k_curves_metric=<metric>.png`; Calinski-Harabasz sta in `tuning_results.csv` e nelle tabelle del `report.md`, non nelle curve) dicono quanto i cluster sono compatti e separati. Si leggono insieme al dendrogramma.

- Si cerca un `n_clusters` dove la silhouette ha un **picco** (più alta dei k vicini) e Davies-Bouldin una **valle** (più basso dei vicini), e dove i linkage concordano.
- Una silhouette che sale sempre verso i k grandi, senza picchi, segnala che non c'è un k naturale.
- Nessun indice basta da solo: vanno confrontati con il dendrogramma.

### Agglomerative — matrice di distanza interclasse

- **Dove**: un heatmap per ogni `metric` testata, indipendente dal numero di cluster. Generata solo se i metadati includono un raggruppamento noto a priori (es. il dataset di provenienza).
- **Cosa misura**: usa quel raggruppamento come proxy debole di verità nota, e calcola la distanza media dentro ogni gruppo e tra coppie di gruppi diverse, per ciascuna metrica candidata.
- **Come si legge**: la metrica migliore tiene la diagonale (dentro-gruppo) bassa e le celle fuori diagonale (tra-gruppo) alte. Non ti dice nulla sul numero di cluster: usala **prima** di guardare Silhouette/CH/DB, per capire quale metrica approfondire.

### GMM — BIC / AIC

- **Dove**: colonne in più nello stesso `tuning_plot.png`.
- **Cosa misurano**: a differenza dei 3 indici geometrici, penalizzano la complessità del modello (più componenti = rischio di overfitting) bilanciandola con quanto bene il modello descrive i dati.
- **Come si leggono**: più basso = meglio.
- **Attenzione**: se scendono in modo monotono per tutta la griglia senza mai risalire, in quel range non stanno dando informazione utile — la griglia non arriva al punto di svolta. In questo caso appoggiati ai 3 indici generici.

### HDBSCAN — DBCV, rumore e numero di cluster

- **DBCV** è l'indice interno di `hdbscan` e `hdbscan_soft` (valutazione `density_metrics`, colonna `dbcv` di `density_metrics.csv`): da -1 a 1, più alto è meglio, pesa il rumore. Silhouette, Calinski-Harabasz, Davies-Bouldin e Dunn non si calcolano per HDBSCAN ([`evaluation_metrics.md`](clustering_methods/evaluation_metrics.md), §8). Non è definito con meno di 2 cluster: cella vuota, non 0.
- **Frazione di rumore** (`noise_fraction`): colonna di `tuning_results.csv`. Si legge sempre insieme al DBCV: un `min_cluster_size` grande può dare cluster netti scartando molti soggetti come rumore. È un vero trade-off tra qualità e copertura del campione. Nessun limite di rumore filtra i risultati.
- **Come si leggono `tuning_plot.png` e `dbcv_curves.png`.** Lo sweep varia `min_cluster_size` e `min_samples` insieme.
  - `tuning_plot.png` è una griglia di tabelle colorate (heatmap), una per DBCV, rumore, quota del cluster più grande, numero di cluster e, per `hdbscan_soft`, probabilità media e persistenza: `min_cluster_size` sull'asse x, `min_samples` sull'asse y, il colore è il valore. Ogni riquadro ha la sua scala di colore, quindi le differenze piccole sembrano grandi.
  - `dbcv_curves.png` ha gli stessi numeri come curve contro `min_cluster_size`, una linea per `min_samples`. Un punto manca dove i cluster sono meno di 2.
  - Si cercano le celle con DBCV alto e si controlla il rumore *di quella stessa cella*.
- **I due parametri.**
  - `min_cluster_size`: soggetti minimi perché un gruppo conti come cluster. Con 50, un gruppo di 30 non è un cluster (resta rumore).
  - `min_samples`: quanto il metodo è severo nel decidere che un soggetto sta in una zona densa. Più è alto, più soggetti finiscono nel rumore.
- **Il rumore può far salire gli indici calcolati sui soli soggetti clusterizzati** (silhouette e simili): per questo non sono usati qui. Il DBCV pesa il rumore, quindi una combinazione che scarta molti soggetti non viene premiata.
- **Il DBCV non ha un valore di riferimento** e non si confronta tra embedding diversi: si leggono le forme sulla griglia, non un valore assoluto.

### Spectral — eigengap

- **Dove**: un file `eigengap_affinity=<affinity>.png` per ogni `affinity` testata (`nearest_neighbors`/`rbf`), con un subplot per ogni valore sweepato del suo iperparametro (`n_neighbors` o `gamma`) — indipendente dal numero di cluster. L'eigengap è calcolato per ogni `affinity` e per ogni valore sweepato del suo iperparametro, non una volta sola dai parametri di base (`base_params`): ogni file riflette la propria `affinity` e ogni subplot il proprio valore.
- **Cosa misura**: gli autovalori del grafo di affinità tra i punti.
- **Come si legge**: il numero di cluster consigliato è l'indice giusto prima del salto più grande tra due autovalori consecutivi (spesso marcato visivamente nel plot). È un criterio più fondato dei 3 indici generici per questo metodo, perché riflette direttamente la connettività del grafo che l'algoritmo usa internamente.

### ADP — dipendenza da `Z` e plateau

ADP (*Advanced Density Peaks*) non ha un numero di cluster da scegliere: lo decidono i dati, e l'unica manopola è `Z` (definizione e campi di `tuning_results.csv` in `docs/guides/clustering.md`). Per questo il tuning varia `Z` e non `n_clusters`. La domanda a cui risponde la lettura è: **quanto il risultato dipende da `Z`**, e c'è un tratto di `Z` in cui è stabile (un *plateau*)?

- **Dove**: `tuning_plot.png`, un pannello per ogni misura con `Z` in scala logaritmica sull'asse x (una linea per metrica, se la run ne prova più di una).
  - `n_clusters_found`: quanti cluster ha prodotto quel `Z`.
  - `largest_cluster_share`: quota di soggetti nel cluster più grande. Vicino a 1, tutto è collassato in un gruppo.
  - `ari_vs_prev_z`: quanto la partizione somiglia a quella del `Z` immediatamente più basso (1 = identica, 0 = quanto il caso). Vicino a 1 è un plateau.
  - `silhouette`: calcolata con la distanza usata per clusterizzare, quindi **non confrontabile tra metriche**. CH e DB esistono solo con `euclidean`; con `dice` restano vuoti.
- **Come si legge**: si cerca un tratto di `Z` con `n_clusters_found` fisso e `ari_vs_prev_z` vicino a 1, dove il risultato non dipende dalla soglia. Se la partizione cambia a ogni passo, dipende dalla soglia e non dai dati.
- **Tabella dei plateau** (nessuno script la produce: si ricava da `tuning_results.csv`). Riassume il grafico: per ogni numero di cluster trovato, l'intervallo di `Z` che lo produce (minimo e massimo) e quanti valori dello sweep ci cadono.
  - Un intervallo largo (per esempio da 4 a 10) vuol dire che quel numero di cluster non dipende dalla soglia.
  - Un numero che compare per un solo `Z` è un caso dello sweep, non un risultato.
  - Un solo cluster (tutti insieme) a `Z` alto è il limite atteso: con una soglia severa nessun picco è significativo.
  - Minimo e massimo non dicono se i valori intermedi di `Z` hanno dato lo stesso numero di cluster: il conteggio dei valori nello sweep serve a controllarlo.
- **Dove cadono i cluster.** ADP lavora sulla matrice grezza e non ha un embedding suo: per vederli si proiettano le etichette di più valori di `Z` su un UMAP 2D già esistente degli stessi soggetti (le croci nere sono il rumore, `-1`). Serve a *vedere*, non a validare: l'embedding è un'altra rappresentazione dei dati, e cluster che occupano zone distinte vanno nella stessa direzione senza essere una prova.

---

## Confrontare la stessa run su embedding diversi

Lo stesso metodo, sugli stessi soggetti, su embedding UMAP di dimensione diversa (`n_components` = 2, 3, 10), con la stessa metrica UMAP. Se il risultato cambia molto con l'embedding, non è affidabile.

Il progetto non ha uno strumento che produca questi confronti in un colpo: si fanno sui `tuning_results.csv` (e `density_metrics.csv`) di ogni run e, per le partizioni, con il notebook `clustering_comparison` (`docs/guides/evaluation.md`). Il `tuning_plot.png` di ogni run ha la propria scala di colore: le heatmap di run diverse non si confrontano a colpo d'occhio.

- **Cosa si confronta.** I valori assoluti degli indici non si confrontano tra embedding (ogni embedding è uno spazio diverso): si confrontano le partizioni, le dimensioni dei cluster e la struttura.
- **ARI (*adjusted Rand index*).** Misura l'accordo tra due divisioni degli stessi soggetti: 1 = identiche, 0 = quanto il caso. Un ARI alto a un certo k vuol dire che quel taglio non dipende da `n_components`.
- **Attenzione ai parametri UMAP.** `n_neighbors` e `min_dist` possono cambiare insieme a `n_components`: va guardato quali valgono per ciascuna run, per non attribuire a `n_components` una differenza dovuta a loro.
- **Agglomerative.**
  - Curve di silhouette e Davies-Bouldin per `n_clusters`, un pannello per `n_components`, ognuno col proprio asse y: si confronta la *forma* (dove sta il picco, dove crolla), non l'altezza. Un picco allo stesso `n_clusters` in tutti i pannelli è un taglio che si ripete.
  - ARI tra le partizioni di due embedding a parità di `n_clusters`, `linkage` e `metric`.
  - Dimensioni dei cluster a un k scelto, per ogni run, e *contingenza* tra due run: tabella che incrocia i loro cluster (righe = prima run, colonne = seconda), dove ogni cella conta i soggetti in comune. Gruppi con la stessa dimensione in tutte le run si ritrovano; un cluster che finisce quasi tutto in una colonna è lo stesso gruppo.
- **HDBSCAN.**
  - Una heatmap per run, per cluster trovati e per `noise_fraction`, su `min_cluster_size` × `min_samples`, da riportare sulla stessa scala di colore per tutte le run. La stessa coppia di parametri dà numeri simili nelle heatmap se la struttura si ripete; molti cluster e rumore alto in una sola run segnalano un embedding frammentato.
  - ARI tra le partizioni di due run. In `agreement_metrics` (`src/analysis/cluster_comparison.py`) il rumore conta come un gruppo a sé; calcolato sui soli soggetti non-rumore in entrambe, l'ARI descrive solo una parte del campione, quindi si riporta anche quanti soggetti sono (nessuna tabella del progetto lo fa). ARI vicino a 1 = stessa struttura. Si affianca alle dimensioni dei cluster di ogni run.

---

## Diagnostiche di stabilità (opzionali)

Rispondono a una domanda diversa da quella degli indici sopra: non "quanto è buono questo clustering", ma "quanto ci si può fidare che sia riproducibile".

### 1. Stabilità dell'inizializzazione (solo KMeans, GMM)

KMeans e GMM partono da un'inizializzazione casuale. Prima di fidarti della sweep principale, verifica se il risultato dipende troppo dal seed usato.

- **Come si legge**: un pannello per ogni valore rappresentativo del parametro target, con una linea per ogni strategia di inizializzazione. Una linea che si appiattisce presto e resta bassa = inizializzazione stabile. Una linea che resta alta anche con molte ripetizioni = i punteggi della sweep principale per quel valore sono meno affidabili di quanto sembrino, perché dipendono più dal seed che dal vero numero di cluster.

### 2. Stabilità del numero di cluster (KMeans, GMM, Spectral)

Domanda diversa: il numero di cluster scelto è supportato dai dati, o cambierebbe con un campione o un'inizializzazione diversi?

- **Riproducibilità rispetto al seed**: stessi dati, inizializzazioni diverse — quanto si ottiene lo stesso risultato.
- **Riproducibilità rispetto al campione**: sottocampioni casuali di soggetti — quanto il risultato dipende da chi capita nel campione.

Entrambe restano un punteggio diagnostico per ogni valore testato: non producono etichette finali di cluster.

---

## Cosa trovi nella cartella di output di una sweep

Generati sempre:

| File                   | Contenuto                                                                                                                                                                                                                                                                               |
| ---------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `tuning_results.csv` | Una riga per ogni valore testato, con tutti gli indici calcolati.                                                                                                                                                                                                                       |
| `tuning_plot.png`    | Griglia di sotto-grafici, uno per indice (per HDBSCAN e HDBSCAN soft lo scrive la valutazione `tuning_heatmaps`) —**solo se la sweep varia 1 o 2 parametri**. Con 3 o più parametri sweepati non viene generato un plot aggregato (solo un avviso in log): il CSV e le diagnostiche standalone del metodo restano l'unico modo di leggere quella sweep. |
| `config.md`          | Snapshot dei parametri usati per quella run.                                                                                                                                                                                                                                            |

Diagnostiche standalone (indipendenti dal valore scelto), solo per il metodo indicato:

| File                                                             | Metodo                | Sempre presente?                                                    |
| ---------------------------------------------------------------- | --------------------- | ------------------------------------------------------------------- |
| Dendrogramma (uno per`metric`, subplot per `linkage`)        | Agglomerative         | Sì                                                                 |
| Matrice di distanza interclasse                                  | Agglomerative         | Solo se è disponibile un raggruppamento noto a priori nei metadati |
| Eigengap (uno per`affinity`, subplot per il suo iperparametro) | Spectral              | Sì                                                                 |

Output opzionali, solo se attivati in config:

| File                                                           | Metodo                | Attivato da         |
| -------------------------------------------------------------- | --------------------- | ------------------- |
| Grafico e tabella di stabilità dell'inizializzazione          | KMeans, GMM           | opzione "stability" |
| Colonne di stabilità del numero di cluster nel CSV principale | KMeans, GMM, Spectral | opzione "consensus" |

Un'opzione aggiuntiva permette di salvare anche le etichette effettive prodotte da ogni combinazione testata, per riutilizzarle senza dover ricalcolare. Non è supportata quando Spectral viene testato variando anche il tipo di grafo di affinità.
