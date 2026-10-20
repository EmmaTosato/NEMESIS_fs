# Evidence accumulation

## Cosa fa

- **Consensus clustering**: invece di fidarsi di un singolo clustering, ne combina molti. Ogni run è un'"evidenza" su come sono organizzati i soggetti, e le evidenze si accumulano. Metodo di Fred & Jain 2002.
- Schema **split-and-merge**, nato per superare il limite di KMeans (cluster solo sferici):
  - **Split**: si ripete un metodo di base (`base_method`: KMeans, GMM o spectral) `n_repeats` volte con inizializzazioni casuali diverse, con molti cluster piccoli.
  - **Combine**: si costruisce la **matrice di co-associazione**, soggetti × soggetti. Ogni cella è la frazione di run in cui i due soggetti sono finiti nello stesso cluster.
  - **Merge**: si uniscono i soggetti la cui co-associazione supera la soglia `threshold` (default 0,5, cioè almeno metà delle run), con un single-link.
- Il numero di cluster finali **non è un parametro**: emerge dalla soglia.

## Che tipo di metodo è

- **Ensemble / consensus**, **non supervisionato**.
- Due parametri con due ruoli diversi: il `k` del metodo di base (granularità dello split) e `threshold` (il taglio).
- Il `k` dello split va scelto **più alto** del numero di cluster atteso: il merge ricompone ciò che è stato frammentato.
- Con `base_method="spectral"` coincide con l'RSC di Zanola et al. 2026.
- Non va confuso con le diagnostiche di stabilità (RSC e "Monti"): usano la stessa matrice di co-associazione, ma per dare un punteggio di affidabilità a un `k` scelto altrove, non per produrre le etichette.

## Cosa restituisce

| Oggetto | Cos'è | Dimensione |
|---|---|---|
| **Etichetta** | il cluster finale di ogni soggetto | una per soggetto |
| **Matrice di co-associazione** | quanto spesso due soggetti stanno insieme | soggetti × soggetti |

- Due diagnostiche si scrivono a ogni run:
  - **convergenza**: la matrice si stabilizza al crescere di `n_repeats`, o il valore scelto è arbitrario?
  - **matrice di consenso** riordinata per cluster finale: blocchi netti sulla diagonale = cluster affidabili, zone sfumate = taglio ambiguo.

## Esempio concreto

Quattro soggetti A, B, C, D e quattro run del metodo di base (esempio costruito):

| Run | Cluster |
|---|---|
| 1 | {A, B}, {C, D} |
| 2 | {A, B}, {C}, {D} |
| 3 | {A}, {B}, {C, D} |
| 4 | {A, B}, {C, D} |

- Co-associazione di A e B: 3 run su 4 = **0,75**. Stesso valore per C e D. Tutte le coppie tra i due gruppi: **0**.
- Con `threshold` = 0,5 si ottengono 2 cluster: {A, B} e {C, D}.
- Con `threshold` = 0,8 nessuna coppia supera la soglia: restano 4 soggetti isolati.
- Anche se la run 3 ha separato A da B, le altre tre run li tengono insieme: il voto di maggioranza assorbe l'instabilità di una singola run.

**Limite dichiarato dagli autori**: fatica sui cluster che si toccano, perché lo split iniziale non li separa nemmeno localmente. Se le lesioni formano un continuum e non gruppi discreti, il metodo non lo mostrerà come tale. Su blob già ben separati il merge aggiunge poco rispetto al single-link da solo.

Approfondimento: `knowledge/notes/dim_reduction_clustering/clustering_literature_survey.md`, sezioni 3 (evidence accumulation) e 4 (diagnostiche RSC e Monti).
