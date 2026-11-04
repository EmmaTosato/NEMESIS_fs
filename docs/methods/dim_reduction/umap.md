# UMAP in NEMESIS

- **Teoria:** [UMAP (Uniform Manifold Approximation and Projection)](../../../knowledge/concepts/Machine_Learning/Unsupervised/Dimensionality_Reduction/umap.md)
  (Learning: `2_Concepts/Machine_Learning/Unsupervised/Dimensionality_Reduction/umap.md`)
- **Letteratura:** nei `sources` della nota teorica
- **Spiegazione rapida:** [cheatsheet](../../../management/cheatsheets/umap.md) (derivata, non è una fonte)

Funzione `umap_embed` in `src/analysis/reduction.py`, cioè `umap.UMAP(**params)` di `umap-learn` 0.5.12.
Parametri: `config/registry/params_reduction.json` e `params_reduction_sdc.json` (chiave `umap`).
Altri metodi: [README](README.md). Criterio con cui si leggono le griglie `n_neighbors` × `min_dist`:
[employed_dim_reduction_methods](employed_dim_reduction_methods.md), "Scegliere `n_neighbors` e `min_dist` di UMAP guardando le griglie".

## Su cosa lo applichiamo
- **Dati:** lesioni binarie voxel-wise ($n$ = 5269-5845, $p \approx$ 220-260 mila) con `metric` ∈ {`dice`, `euclidean`};
  disconnettoma continuo con `euclidean` (`params_reduction_sdc.json`).
- **Distanze precalcolate:** il repo calcola una volta la matrice $n\times n$ e passa `metric="precomputed"`, così il grafo dei vicini è **esatto**.
  Senza, sopra 4096 punti `umap-learn` passa alla ricerca approssimata (NN-descent); la soglia è nel sorgente (`X[index].shape[0] < 4096`),
  non nella documentazione. Misure e motivazione: [models](../../dev/models.md), `embed`.
- **Euclidea su maschere binarie misura il volume:** la distanza euclidea al quadrato tra due maschere $A, B$ è il numero di voxel in cui differiscono,
  $|A| + |B| - 2|A\cap B|$. Due lesioni piccole sono vicine anche se non si toccano, due lesioni grandi nello stesso posto restano lontane.
  Dice attenua ma non elimina la dipendenza dal volume (`employed_dim_reduction_methods.md`, "Il bias-volume di jaccard/dice").
- **Uso a valle:** l'embedding (2, 3 o 10 componenti) è l'ingresso di `clustering.py`. La documentazione `umap-learn` indica questo uso
  come possibile, "somewhat controversial", da fare "with care".
- **Riferimento:** Talozzi et al. 2023 usano UMAP con i parametri di default ("an approximation of 15 neighbours and a minimum 0.1 Euclidean distance")
  per un embedding 2D dei disconnettomi.

## Parametri usati (significato: documentazione `umap-learn`)
| Parametro | Nel progetto (lesione / SDC) |
|---|---|
| `n_neighbors` | base 5 / 15; griglia 5, 15, 30, 50, 100 |
| `min_dist` | base 0,0; griglia 0,0, 0,01, 0,05, 0,1, 0,5, 1,0 |
| `n_components` | griglia 2, 3, 10 |
| `metric` | `dice`, `euclidean`, sempre via `precomputed` |
| `n_epochs` | default (quindi 500, perché $n \le 10000$) |
| `init` | default (`"spectral"`) |
| `spread`, `learning_rate`, `negative_sample_rate`, `local_connectivity`, `set_op_mix_ratio`, `repulsion_strength` | default (1,0; 1,0; 5; 1,0; 1,0; 1,0) |
| `densmap` | non usato |
| `random_state` | 0 (impostarlo spegne il multithreading) |

Default verificati sulla firma installata di `umap.UMAP.__init__`.

## Come lo ottimizziamo
1. **Griglie `n_neighbors` × `min_dist`** (valori nella tabella), lette con il criterio di `employed_dim_reduction_methods.md`.
2. **`n_components` nidificato:** la trustworthiness non si confronta tra dimensioni diverse ([dim_reduction_tuning_guide](dim_reduction_tuning_guide.md), "guadagno marginale").
3. **`metric`:** scelta di dominio; sulle lesioni `dice` contro `euclidean`.
4. **`min_dist` basso:** rende i gruppi netti per costruzione; si accetta solo se la stessa struttura resta a `min_dist` vicini (criterio del plateau, `employed_dim_reduction_methods.md`).
5. **Seed:** più seed per la stessa combinazione, perché il costo non è convesso.

## Come leggiamo l'output
- **Trustworthiness** a `k = 10` sulla stessa matrice di distanze dell'embedding (punteggio del tuning;
  [teoria della valutazione](../../../knowledge/concepts/Machine_Learning/Unsupervised/Dimensionality_Reduction/evaluation.md)). Non confrontabile tra `n_components` diversi.
- **`plot_hdbscan`:** numero di cluster e quota di rumore di HDBSCAN su ogni combinazione, letti come sonda di stabilità tra celle vicine della griglia
  ([dim_reduction_tuning_guide](dim_reduction_tuning_guide.md)).
- **Gemello 2D:** un embedding a più componenti si guarda solo con un fit separato a `n_components=2` con gli stessi iperparametri,
  mai con le prime due colonne (`lessons_learned.md` #16).
- **Non calcolati nel repo:** continuity, conservazione dei $k$ vicini, correlazione delle distanze. Nei benchmark di de Bodt et al.
  UMAP in 2D ha una conservazione dei 10 vicini (0,08-0,25 sui quattro dataset) inferiore a t-SNE e superiore a PCA (Tabella 2).

## Attenzioni specifiche
- Con `random_state` fissato UMAP è single-thread; la riproducibilità esatta richiede `random_state`.
- Senza `metric="precomputed"`, sopra 4096 punti il grafo dei vicini diventa approssimato.
- Con `euclidean` sulle maschere binarie la distanza misura anche il volume delle lesioni; `dice` lo attenua soltanto.
