# PaCMAP

## Cosa fa

- Come UMAP, porta ogni soggetto a 2 o 3 coordinate, pensato per la **visualizzazione**.
- Lo scopo dichiarato è preservare **insieme la struttura locale e quella globale**. UMAP e t-SNE tendono a privilegiare la prima.
- Lo fa guidando l'ottimizzazione con **tre tipi di coppie di soggetti**:

| coppia | come si sceglie | effetto |
|---|---|---|
| **neighbor** | i `n_neighbors` vicini più prossimi | tiene vicini i simili: struttura locale |
| **mid-near** | soggetti a distanza intermedia | tiene insieme i gruppi: struttura globale |
| **further** | soggetti casuali e lontani | vengono respinti |

- Le proporzioni tra i tipi sono due parametri: `MN_ratio` (mid-near) e `FP_ratio` (further). Sono quelli che bilanciano locale e globale.

## Che tipo di metodo è

- **Non lineare** e **non supervisionato**: usa solo la matrice.
- Parte da una **PCA** (`init="pca"`) e ottimizza con Adam (il README della libreria dice AdaGrad, il codice usa Adam). Per accelerare fa anche una PCA preliminare (`apply_pca=True`): sui voxel i vicini si cercano sulle prime 100 componenti, non sui voxel.
- `n_neighbors` si scala da solo sopra i 10.000 punti solo se vale `None`; il progetto passa sempre un numero.
- Funziona su dati molto diversi: immagini, RNA di singola cellula, nuvole di punti.
- Metrica: di default euclidea (`distance`). Non esiste Dice né `precomputed`. `hamming` su vettori 0/1 ordina i vicini come l'euclidea e, con il backend `faiss` di default, non funziona.

## Cosa restituisce

| Oggetto | Cos'è | Dimensione |
|---|---|---|
| **Embedding** | le coordinate di ogni soggetto nello spazio ridotto | soggetti × `n_components` |

- Come per UMAP, non ci sono pesi sui voxel.
- Nel tuning la qualità è la **trustworthiness**: quanto i vicini nell'embedding erano vicini anche nello spazio originale. Il tuning non sceglie in automatico.

## Esempio concreto

Le tre fasi dell'ottimizzazione (`num_iters = (100, 100, 250)`):

| Fase | Iterazioni | Cosa pesa di più |
|---|---|---|
| 1 | 100 | le coppie mid-near: si fissa la struttura globale |
| 2 | 100 | equilibrio tra i tipi di coppia |
| 3 | 250 | le coppie neighbor: si rifinisce il locale |

- Prima si decide dove stanno i grandi gruppi, poi si sistemano i dettagli dentro ciascuno.
- Nel progetto si varia `n_neighbors` (5, 10, 20, 50), mentre `MN_ratio` e `FP_ratio` restano ai valori di default (0,5 e 2,0).

Approfondimento: `knowledge/notes/dim_reduction_clustering/dim_reduction_methods/pacmap.md`.
