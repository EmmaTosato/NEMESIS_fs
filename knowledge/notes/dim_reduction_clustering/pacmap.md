# PaCMAP

Fonte: [github.com/YingfanWang/PaCMAP](https://github.com/YingfanWang/PaCMAP). Versione installata nel repo: 0.9.1.

Implementazione nel repo: `pacmap_embed` in `src/analysis/reduction.py`, parametri in `config/registry/params_reduction.json` (chiave `pacmap`).

## Che cosa fa

- Metodo di riduzione dimensionale (Pairwise Controlled Manifold Approximation), pensato per la visualizzazione in 2D o 3D.
- Scopo dichiarato: preservare **insieme struttura locale e globale**. UMAP e t-SNE tendono a privilegiare la prima.

## Che tecniche usa

- **Tre tipi di coppie di punti**, che guidano l'ottimizzazione:
  - *Neighbor pairs*: i k vicini più prossimi, per la struttura locale.
  - *Mid-near pairs*: punti a distanza intermedia, per la struttura globale.
  - *Further pairs*: punti scelti a caso e lontani, che vengono respinti.
- **Pesi che cambiano in tre fasi** (`num_iters=(100, 100, 250)`):
  - all'inizio pesano i mid-near, per fissare la struttura globale;
  - poi si bilancia;
  - alla fine dominano i neighbor, per rifinire il locale.
- **Inizializzazione con PCA** (`init="pca"` di default nella libreria).
- **Ottimizzazione con AdaGrad**, ricerca dei vicini con FAISS (il default al posto di Annoy, non più mantenuto).
- **PCA preliminare** (`apply_pca=True`) per accelerare il calcolo.

## Per quali dati è adatto

- Funziona su dati molto diversi: immagini, dati biologici (RNA di singola cellula), nuvole di punti.
- Regge anche dataset grandi: sopra i 10.000 punti `n_neighbors` si scala automaticamente.

## Come si fa il fine-tuning

| Parametro | Default libreria | Nel repo | Effetto |
|---|---|---|---|
| `n_neighbors` | 10 | sweeppato: `[5, 10, 20, 50]` | dimensione del grafo dei vicini |
| `MN_ratio` | 0.5 | fisso | proporzione di coppie mid-near |
| `FP_ratio` | 2.0 | fisso | proporzione di coppie further |
| `distance` | `euclidean` | non passato, quindi euclidea | metrica dei vicini |
| `lr`, `num_iters`, `init`, `apply_pca` | vedi libreria | `apply_pca=true`, gli altri a default | di solito poco effetto |

- `MN_ratio` e `FP_ratio` sono i parametri che bilanciano locale e globale.
- Qualità dell'embedding nel tuning: trustworthiness (`trustworthiness_n_neighbors: 10`), nessuna selezione automatica.

## Sui nostri dati

- `data/derived/lesion_matrix/25-08_s1.2-vol`: 5269 × 264274, `uint8` (binaria).
- `PaCMAP.__init__` accetta `distance` (es. `'hamming'`). Non ho verificato l'elenco dei valori ammessi.
- Ipotesi, non risultato: per lesioni binarie la distanza di Hamming potrebbe essere più adatta dell'euclidea.
- Non ancora eseguito su `25-08_s1.2-vol`.
