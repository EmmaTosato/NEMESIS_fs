# Bicego vs NEMESIS: valutazione del clustering

Promemoria personale: cosa dice Bicego sulla valutazione del clustering e cosa facciamo noi. Non è una fonte di verità né materiale didattico: le definizioni degli indici stanno in `knowledge/notes/dim_reduction_clustering/`, cosa fa il codice in `docs/`.

- **Data**: 05-11-26.
- **Fonte Bicego**: slide del corso triennale *Riconoscimento e recupero dell'informazione per Bioinformatica*, L4a (slide 19, 40-44) e L4b (slide 56-75). Altre slide di Bicego sono in `knowledge/papers/methods/` e non sono state confrontate.
- **Metodi considerati**: Agglomerative, HDBSCAN e HDBSCAN-soft. ADP e gli altri metodi sono fuori, per ora.

## Come Bicego divide gli indici (L4b:59)

| Tipo | Che cosa fa | Indici che Bicego nomina |
|---|---|---|
| Esterni | confrontano il clustering con etichette note a priori | Rand, Jaccard, Fowlkes-Mallows, Γ statistic (L4b:61-66) |
| Interni | usano solo i dati | Davies-Bouldin, l'unico sviluppato (L4b:68-71) |
| Relativi | confrontano due risultati di clustering | nessuno: solo la definizione |

Gli indici esterni si calcolano su **coppie** di oggetti, da due partizioni U (clustering) e V (etichette): a = coppie unite in entrambe, b = unite solo in U, c = unite solo in V, d = separate in entrambe. Rand = (a+d)/C(n,2); Jaccard = a/(a+b+c); Fowlkes-Mallows = a/√(m₁m₂), con m₁ = a+b e m₂ = a+c.

## Indici esterni (due partizioni)

| Bicego | NEMESIS | Differenza |
|---|---|---|
| Rand | non usato | sostituito dall'ARI, il Rand corretto per il caso |
| Jaccard | non usato | nel repo compare solo come overlap tra cluster di run diverse |
| Fowlkes-Mallows | non usato | nessun equivalente |
| Γ statistic | non usato | nessun equivalente |
| nessuno | ARI, NMI | l'ARI è corretto per il caso; l'NMI è più intuitivo ma può sovrastimare con molti cluster |
| nessuno | homogeneity e completeness | l'NMI ne nasconde l'asimmetria, quindi si leggono separate |
| nessuno | chi-quadro con residui, purezza per cluster, match matrix | dicono dove le due partizioni concordano |

- Nei documenti non c'è scritto perché Rand, Jaccard, Fowlkes-Mallows e Γ non siano stati adottati. La ragione più probabile è la correzione per il caso, ma è un'inferenza.
- **L'uso è diverso**: Bicego confronta con etichette vere. Noi non abbiamo ground truth, quindi ARI e NMI si usano solo **tra due run** (metodi o k diversi; lesion contro sdc sui soggetti comuni).
- Un ARI/NMI alto tra metodi diversi è convergenza, non prova che il clustering sia corretto.

## Indici interni (solo dati)

| Bicego | Agglomerative | HDBSCAN / HDBSCAN-soft |
|---|---|---|
| Davies-Bouldin | Davies-Bouldin, solo con distanza euclidea | non calcolato |
| nessuno | silhouette (nella metrica del clustering, per soggetto e per cluster) | non calcolata |
| nessuno | Calinski-Harabasz e Dunn, solo euclidea | non calcolati |
| nessuno | quota del cluster più grande, numero di cluster | stesse due misure |
| nessuno | | DBCV, frazione di rumore, probabilità media nel proprio cluster |

- Per HDBSCAN silhouette, Calinski-Harabasz, Davies-Bouldin e Dunn non si calcolano: girerebbero sui soli soggetti non rumore e presuppongono cluster compatti. Il DBCV invece non assume cluster compatti e pesa ogni cluster sulla quota di tutti i soggetti, rumore compreso.
- Con una metrica non euclidea Calinski-Harabasz, Davies-Bouldin e Dunn restano vuoti, mai un numero sbagliato.

## Indici del modello

Bicego non ne ha. Da noi:

- **Agglomerative**: correlazione cofenetica, ARI tra linkage diversi, salto del dendrogramma al k scelto, Dendrogram Explorer (albero k dopo k, con le mappe anatomiche dei due cluster che nascono da ogni divisione).
- **HDBSCAN-soft**: persistenza del cluster e matrice di appartenenza ai cluster.

## Indici relativi

Bicego li definisce senza indici. Da noi il confronto tra due run (ARI, NMI, chi-quadro, purezza) fa di fatto questo lavoro, ma sono indici esterni applicati a due run, non una categoria a sé. Che i relativi usino le formule degli esterni è una lettura mia: le slide non lo dicono.

## Altre procedure di validazione

| Bicego | NEMESIS |
|---|---|
| Cluster tendency (scan test, L4b:72-75) | assente |
| Bootstrap per la robustezza (L4a:41) | assente: la stabilità al ricampionamento esiste solo per kmeans, gmm e spectral, non per i tre metodi di riferimento |
| Validazione soggettiva, solo nominata (L4b:57, L4a:43) | implementata: profilo clinico, composizione dei cluster, mappe di overlap e disconnessione, regressione logistica tra due cluster (notebook) |
| Criteri come J_SSE | usati nel clustering, non nella valutazione |

## In sintesi

- **In comune**: solo Davies-Bouldin (per l'agglomerative), più l'idea di confrontare due partizioni a coppie, che da noi vale per ARI e NMI.
- **Bicego ha e noi no**: Rand, Jaccard, Fowlkes-Mallows e Γ in forma grezza, cluster tendency, bootstrap.
- **Noi abbiamo e Bicego no**: indici per la densità (DBCV, rumore, persistenza), indici del modello gerarchico (cofenetica, salto, accordo tra linkage), la validazione soggettiva.
- **Scoperto per i tre metodi di riferimento**: la stabilità (nessun bootstrap né consenso) e la cluster tendency.

## Dove guardare

- Guida al confronto tra run: `docs/guides/evaluation.md`.
- Valutazione di un tuning: `docs/guides/evaluate_clustering_tuning.md`.
- Pannello "Clustering evaluation" dell'app: `docs/guides/embedding_app.md`.
- Definizioni e fonti degli indici: `knowledge/notes/dim_reduction_clustering/clustering_methods/evaluation_metrics.md`.
