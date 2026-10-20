# KMeans

## Cosa fa

- Divide i soggetti in **k gruppi** scelti in anticipo, ognuno rappresentato dal suo **centroide**, cioè la media dei suoi soggetti.
- L'algoritmo ripete due passi finché non cambia più nulla:
  - **assegna** ogni soggetto al centroide più vicino;
  - **ricalcola** ogni centroide come media dei soggetti assegnati.
- Cerca di minimizzare la somma delle distanze al quadrato tra ogni soggetto e il proprio centroide (*inertia*).

## Che tipo di metodo è

- **Partizionale**: una sola divisione, ogni soggetto in un solo cluster. Il numero `k` si fissa prima.
- **Non deterministico**: parte da un'inizializzazione casuale e converge a un **ottimo locale**, quindi il seme conta. `k-means++` sceglie i centroidi iniziali ben distribuiti.
- **Non supervisionato**.
- Produce solo **cluster convessi e di taglia simile**: fallisce su strutture come un anello esterno.
- Funziona solo su dati vettoriali numerici e soffre della curse of dimensionality: sui voxel grezzi le distanze euclidee sono dominate dal volume della lesione, quindi il workflow raccomandato è ridurre prima la dimensionalità e clusterizzare sull'embedding.
- Veloce: il costo è lineare nel numero di punti.

## Cosa restituisce

| Oggetto | Cos'è | Dimensione |
|---|---|---|
| **Etichetta** | il cluster di ogni soggetto, dato `k` | una per soggetto |
| **Inertia** | quanto i soggetti sono lontani dal proprio centroide (calcolata nel tuning) | una per valore di `k` |

- L'inertia scende sempre al crescere di `k`: non si cerca il minimo ma il **gomito**, dove la curva smette di scendere ripida. Da sola decide poco, quindi si incrocia con silhouette e Davies-Bouldin.
- Prima di fidarsi della sweep si può controllare che il risultato non dipenda troppo dal seme (opzione `stability`).

## Esempio concreto

Quattro soggetti su una retta, in posizione 0, 1, 5 e 7, con `k` = 2 e centroidi iniziali in 0 e 1:

| Passo | Assegnazione | Nuovi centroidi |
|---|---|---|
| 1 | {0}, {1, 5, 7} | 0 e 4,33 |
| 2 | {0, 1}, {5, 7} | 0,5 e 6 |
| 3 | nessun cambiamento | convergenza |

- Inertia finale: (0,5² + 0,5²) + (1² + 1²) = **2,5**.
- Qui qualsiasi partenza ragionevole arriva allo stesso risultato. Su dati veri partenze diverse possono fermarsi su divisioni diverse: per questo si ripete con più `n_init`.
- Il valore di `k` non esce dall'algoritmo: lo si sceglie guardando gomito e indici.

Approfondimento: `knowledge/notes/dim_reduction_clustering/clustering_literature_survey.md` (sezione sulla meccanica degli algoritmi), `clustering_tuning_guide.md` (inertia, stabilità di inizializzazione).
