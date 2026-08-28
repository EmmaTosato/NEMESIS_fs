# Guida rapida al tuning del clustering

Manuale operativo: come leggere gli indici e i grafici prodotti da una sweep di tuning, e come decidere cosa fare a partire da quello che vedi.

## Regola d'oro

Il tuning **non sceglie mai il valore migliore per te**. Per ogni valore testato calcola indici e grafici diagnostici, li salva su disco, e si ferma lì. La scelta finale del parametro da usare in produzione è sempre una decisione umana, guidata dai plot.

Ogni sweep testa un solo iperparametro principale per metodo:

| Metodo | Parametro testato |
|---|---|
| KMeans, Agglomerative, Spectral | `n_clusters` |
| GMM | `n_components` |
| HDBSCAN | `min_cluster_size` |
| Evidence Accumulation | `threshold` |

Agglomerative in più testa `linkage` e `metric` insieme a `n_clusters`. Non tutte le combinazioni sono valide: `linkage="ward"` accetta solo la metrica euclidea, quindi ogni combinazione che li accoppia diversamente viene scartata in automatico (con un avviso in log), non silenziosamente.

---

## I 3 indici universali

Calcolati per tutti e 6 i metodi, sempre nello stesso file (`tuning_plot.png`), uno per sotto-grafico.

| Indice | Range | Direzione | Come leggerlo |
|---|---|---|---|
| **Silhouette** | −1 → 1 | più alto = meglio | Vicino a 1: cluster compatti e separati. Vicino a 0: cluster che si sovrappongono. Negativo: punti probabilmente nel cluster sbagliato. È l'unico dei tre con un valore assoluto interpretabile da solo — gli altri due si leggono solo per confronto tra valori diversi dello stesso sweep. |
| **Calinski-Harabasz** | 0 → +∞ | più alto = meglio | Rapporto tra separazione fra i cluster e compattezza dentro ciascun cluster. Tende quasi sempre a crescere insieme al numero di cluster: da solo non basta per scegliere il numero di cluster, usalo come conferma. |
| **Davies-Bouldin** | 0 → +∞ | più basso = meglio | Media di quanto ogni cluster è disperso rispetto a quanto è vicino al suo "vicino" più simile. È l'unico dei tre che penalizza esplicitamente due cluster troppo ravvicinati — per questo a volte non è d'accordo con Silhouette. |

**Come decidere:**

1. Se tutti e tre puntano allo stesso valore, la scelta è solida: usalo.
2. Se **Silhouette e Davies-Bouldin non sono d'accordo** (capita spesso), non è un errore — è un segnale reale sulla struttura dei dati:
   - Silhouette alto a un valore basso → pochi macro-gruppi, molto separati tra loro.
   - Davies-Bouldin basso a un valore alto → sottogruppi più fini, compatti al loro interno.
3. In caso di conflitto non esiste una regola meccanica. Guarda anche la diagnostica specifica del metodo (dendrogramma, eigengap, ecc. — sotto) prima di decidere, e valuta il risultato anche dal punto di vista clinico.

### Attenzione a questi tre casi particolari

- **HDBSCAN**: i punti classificati come rumore vengono esclusi dai 3 indici. La frazione di rumore è sempre riportata a parte (`noise_fraction`) — mai nascosta, mai fusa nel calcolo.
- **Clustering fatto direttamente sui voxel grezzi (non su un embedding)**: i 3 indici usano distanza euclidea, che su dati binari di lesione è dominata dal volume della lesione più che dalla sua forma o posizione. Il workflow raccomandato è ridurre la dimensionalità prima e poi clusterizzare sull'embedding: il bias si attenua (ma non sparisce del tutto).
- **Agglomerative con `metric` non euclidea**: Silhouette resta sempre calcolabile, ma Calinski-Harabasz e Davies-Bouldin sono per costruzione legati alla geometria euclidea e vengono registrati come vuoti per ogni combinazione che usa una metrica diversa. Se stai leggendo una sweep con più metriche, aspettati colonne vuote per le righe non euclidee: è normale, non un bug.

---

## Diagnostiche specifiche per metodo

### KMeans — curva "inertia" (elbow)

- **Dove**: colonna in più nello stesso `tuning_plot.png`.
- **Cosa misura**: quanto ogni punto è lontano dal centroide del proprio cluster.
- **Come leggerla**: scende sempre all'aumentare del numero di cluster, quindi non cercare il minimo — cerca il "gomito", il punto dove la curva smette di scendere ripidamente. Da sola è poco decisiva se non c'è un gomito netto: incrociala sempre con Silhouette o Davies-Bouldin.

### Agglomerative — dendrogramma

- **Dove**: un file a parte per ogni `linkage` testato, indipendente dal numero di cluster scelto.
- **Come si legge**: dal basso verso l'alto. Ogni fusione verticale unisce due sotto-gruppi all'altezza (asse y) della loro distanza di fusione.
- **Cosa cercare**: il salto verticale più grande tra due fusioni consecutive indica il taglio più naturale.
  - Salto grande vicino alla cima → la struttura più forte è binaria (2 cluster).
  - Salto grande più in basso → suggerisce un numero di cluster maggiore.
- **Attenzione**: il colore dei rami non indica il numero di cluster consigliato — conta solo l'altezza dei salti.
- **Confronta i linkage tra loro**: `ward` tende a fusioni regolari, simili a KMeans. `average`/`complete` sono più sensibili agli outlier. `single` tende a incatenare gruppi distinti attraverso pochi punti-ponte, producendo un dendrogramma meno affidabile per la scelta del numero di cluster.
- **Attenzione — calcolato sempre a `metric="euclidean"`**: anche quando `metric` è sweepata (`cosine`/`manhattan`), il dendrogramma per ogni `linkage` resta calcolato con la metrica di default/`base_params` (euclidea), mai con quella iterata nella sweep (`clustering.py::_write_agglomerative_diagnostics`). Per una sweep `metric`-mista, quindi, il dendrogramma è una diagnostica valida solo per giudicare `linkage` nella geometria euclidea — per `cosine`/`manhattan` l'unico segnale su `linkage` resta `tuning_results.csv` (solo Silhouette, dato che CH/DB sono vuoti per quelle righe).

### Agglomerative — matrice di distanza interclasse

- **Dove**: un heatmap per ogni `metric` testata, indipendente dal numero di cluster. Generata solo se i metadati includono un raggruppamento noto a priori (es. il dataset di provenienza).
- **Cosa misura**: usa quel raggruppamento come proxy debole di verità nota, e calcola la distanza media dentro ogni gruppo e tra coppie di gruppi diverse, per ciascuna metrica candidata.
- **Come si legge**: la metrica migliore tiene la diagonale (dentro-gruppo) bassa e le celle fuori diagonale (tra-gruppo) alte. Non ti dice nulla sul numero di cluster: usala **prima** di guardare Silhouette/CH/DB, per capire quale metrica approfondire.

### Evidence Accumulation — convergenza e matrice di consenso

Entrambe calcolate una sola volta, indipendenti dalla soglia (`threshold`) sweepata:

- **Convergenza**: verifica se la matrice di co-occorrenza tra soggetti si stabilizza man mano che aumentano le ripetizioni del clustering di base, o se il numero di ripetizioni scelto è ancora arbitrario.
- **Matrice di consenso**: quante volte ogni coppia di soggetti finisce nello stesso cluster, riordinata secondo l'assegnazione finale. Blocchi diagonali netti = cluster puliti e affidabili a quella soglia. Zone sfumate = un taglio ambiguo.

### GMM — BIC / AIC

- **Dove**: colonne in più nello stesso `tuning_plot.png`.
- **Cosa misurano**: a differenza dei 3 indici geometrici, penalizzano la complessità del modello (più componenti = rischio di overfitting) bilanciandola con quanto bene il modello descrive i dati.
- **Come si leggono**: più basso = meglio.
- **Attenzione**: se scendono in modo monotono per tutta la griglia senza mai risalire, in quel range non stanno dando informazione utile — la griglia non arriva al punto di svolta. In questo caso appoggiati ai 3 indici generici.

### HDBSCAN — frazione di rumore

- Colonna in più nello stesso `tuning_plot.png`. Va sempre letta insieme agli altri indici, mai da sola: un `min_cluster_size` grande può dare indici ottimi solo perché scarta molti soggetti "difficili" come rumore. È un vero trade-off tra qualità e copertura del campione.
- Non esiste un grafico standalone dedicato: il valore giusto di `min_cluster_size` si giudica direttamente dalla curva di frazione di rumore incrociata con Silhouette.

### Spectral — eigengap

- **Dove**: file a parte, calcolato una volta sola, indipendente dal numero di cluster.
- **Cosa misura**: gli autovalori del grafo di affinità tra i punti.
- **Come si legge**: il numero di cluster consigliato è l'indice giusto prima del salto più grande tra due autovalori consecutivi (spesso marcato visivamente nel plot). È un criterio più fondato dei 3 indici generici per questo metodo, perché riflette direttamente la connettività del grafo che l'algoritmo usa internamente.

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

Entrambe restano un punteggio diagnostico per ogni valore testato: non producono etichette finali di cluster (a differenza di Evidence Accumulation, che è un metodo di produzione a sé stante, con le sue diagnostiche standalone viste sopra).

---

## Cosa trovi nella cartella di output di una sweep

Generati sempre:

| File | Contenuto |
|---|---|
| `tuning_results.csv` | Una riga per ogni valore testato, con tutti gli indici calcolati. |
| `tuning_plot.png` | Griglia di sotto-grafici, uno per indice — **solo se la sweep varia 1 o 2 parametri**. Con 3 o più parametri sweepati non viene generato un plot aggregato (solo un avviso in log): il CSV e le diagnostiche standalone del metodo restano l'unico modo di leggere quella sweep. |
| `config.md` | Snapshot dei parametri usati per quella run. |

Diagnostiche standalone (indipendenti dal valore scelto), solo per il metodo indicato:

| File | Metodo | Sempre presente? |
|---|---|---|
| Dendrogramma (uno per `linkage`) | Agglomerative | Sì |
| Matrice di distanza interclasse | Agglomerative | Solo se è disponibile un raggruppamento noto a priori nei metadati |
| Eigengap | Spectral | Sì |
| Convergenza + matrice di consenso | Evidence Accumulation | Sì |

Output opzionali, solo se attivati in config:

| File | Metodo | Attivato da |
|---|---|---|
| Grafico e tabella di stabilità dell'inizializzazione | KMeans, GMM | opzione "stability" |
| Colonne di stabilità del numero di cluster nel CSV principale | KMeans, GMM, Spectral | opzione "consensus" |

Un'opzione aggiuntiva permette di salvare anche le etichette effettive prodotte da ogni combinazione testata, per riutilizzarle senza dover ricalcolare. Non è supportata quando Spectral viene testato variando anche il tipo di grafo di affinità.
