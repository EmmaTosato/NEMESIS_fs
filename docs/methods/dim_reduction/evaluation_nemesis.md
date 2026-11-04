# Come si valuta un embedding

> Teoria: [Come si valuta un embedding](../../../knowledge/concepts/Machine_Learning/Unsupervised/Dimensionality_Reduction/evaluation.md) (second brain). Questa nota contiene solo la parte specifica di NEMESIS.

Nota comune ai metodi di [README.md](README.md). Spiega le misure di qualità che la letteratura usa per un embedding, con le formule, e dice quali calcola oggi il repo. Per come si leggono i numeri del tuning nel progetto: [`../dim_reduction_tuning_guide.md`](../dim_reduction_tuning_guide.md).

## Cosa calcola il repo

| Metodo | Misura nel tuning (`tuning_results.csv`) | Spazio originale usato per i ranghi |
|---|---|---|
| `umap`, `tsne` | trustworthiness, `trustworthiness_n_neighbors: 10` | la stessa matrice di distanze precalcolata usata per l'embedding (`dice` o `euclidean`) |
| `pacmap` | trustworthiness, `trustworthiness_n_neighbors: 10` | euclidea sulla matrice grezza |
| `pca` | varianza cumulata spiegata | — |

Implementazione: `src/analysis/tuning.py` (`evaluate_umap`, `evaluate_tsne`, `evaluate_pacmap`, `evaluate_pca`). Scelte del progetto:

- `k = 10` è una scelta del progetto (il default di scikit-learn è 5 [3]).
- La continuity, la conservazione dei vicini $Q(k)$/$R(k)$ e la correlazione delle distanze **non** sono calcolate. Una trustworthiness alta non dice quindi nulla sulle omissioni.
- Per `pacmap` i ranghi originali sono euclidei sulla matrice grezza, mentre PaCMAP costruisce i suoi vicini su una proiezione a 100 componenti (vedi [pacmap.md](pacmap.md)): il punteggio è coerente nella metrica ma misura i vicini di uno spazio leggermente diverso da quello che PaCMAP ha visto.
- La trustworthiness cresce con le dimensioni dell'embedding: si confronta solo a parità di `n_components` ([`../dim_reduction_tuning_guide.md`](../dim_reduction_tuning_guide.md)).

## Righe tolte dalla nota teorica (Misure globali)

- **KNC** (Kobak & Berens): quota dei 10 centroidi di classe più vicini conservata. Richiede classi note [5]; nel nostro caso le classi non ci sono.

## Righe tolte dalla nota teorica (Fonti)

1. de Bodt, C., Diaz-Papkovich, A., Kobak, D. et al. (2025). *Low-dimensional embeddings of high-dimensional data.* arXiv:2508.15929 (in `knowledge/papers/methods/`).
