# t-SNE in NEMESIS

- **Teoria:** [t-SNE (t-distributed Stochastic Neighbor Embedding)](../../../knowledge/concepts/Machine_Learning/Unsupervised/Dimensionality_Reduction/tsne.md)
  (Learning: `2_Concepts/Machine_Learning/Unsupervised/Dimensionality_Reduction/tsne.md`)
- **Letteratura:** nei `sources` della nota teorica

Funzione `tsne_embed` in `src/analysis/reduction.py`, cioè `sklearn.manifold.TSNE(**params)` di scikit-learn 1.8.0 (Barnes-Hut). Parametri: `config/registry/params_reduction.json`, chiave `tsne`.
Altri metodi: [README](README.md). Sintesi più breve: [employed_dim_reduction_methods](employed_dim_reduction_methods.md).

**Stato.** Registrato in `REDUCTION_METHODS` ma non usato nelle analisi correnti (si usano PCA e UMAP). I tuning salvati (sessioni `s1.1`, `s1.2`, `s2.1`, `s2.2` in `docs/experiments/`) usano inizializzazione casuale e `learning_rate` 200;
il codice attuale usa l'MDS classico e `"auto"`. Un nuovo tuning non è quindi confrontabile punto per punto con quelli salvati.

## Su cosa lo applichiamo
- **Dati:** matrici voxel-wise con $n \approx 5000$-5800 e $p \approx$ 220-260 mila. In tuning `metric` ∈ {`dice`, `euclidean`} (lesioni binarie) o solo `euclidean` (`params_reduction_sdc.json`, disconnettoma continuo).
- **Distanze precalcolate:** il repo calcola una volta la matrice $n\times n$ delle distanze e passa `metric="precomputed"` (`src/analysis/distances.py`, `reduction.py::embed`). In quel caso scikit-learn non accetta `init="pca"`,
  quindi si parte dalle prime coordinate dell'**MDS classico** della matrice di distanze (`reduction.py::tsne_init_from_distances`), scalate come fa scikit-learn per la PCA (prima colonna con deviazione standard $10^{-4}$).
  Per distanze euclidee coincide con i punteggi della PCA, quindi è la stessa inizializzazione del default di scikit-learn (verificato: a meno del segno, test `test_tsne_init_from_euclidean_distances_equals_pca_scores_up_to_sign`); per `dice` è la stessa ricetta sulle distanze Dice.
  Costo su 5269 soggetti: meno di 1 s. Se i primi autovalori non sono positivi, l'inizializzazione solleva un errore invece di ripiegare su una casuale.
- **Distanze al quadrato:** nel percorso Barnes-Hut scikit-learn eleva al quadrato le distanze dei vicini qualunque sia la metrica (`distances_nn.data **= 2`). Per `euclidean` è la definizione del paper; per `dice` la gaussiana lavora su $d_\text{Dice}^2$. L'insieme dei vicini non cambia, cambia la forma delle $p_{j|i}$.
- **Solo 2D:** `n_components` è fisso a 2 (Barnes-Hut non accetta più di 3 dimensioni). Un clustering a valle di t-SNE lavora quindi su un embedding 2D, ciò che de Bodt et al. sconsigliano.
- **Riferimento:** Thiebaut de Schotten et al. 2020 usano t-SNE in 2D con perplexity 30, exaggeration 12, learning rate 200 e 1000 iterazioni (scikit-learn 0.23); il materiale supplementare replica la figura a perplexity 40, 60 e 80.
  Il repo fissa perplexity 30, exaggeration 12 e 1000 iterazioni come loro e varia solo `perplexity` (scelta del progetto); il learning rate è `"auto"`.

## Parametri usati (significato: documentazione scikit-learn)
| Parametro | Nel progetto |
|---|---|
| `perplexity` | griglia 5, 15, 30, 50, 75, 100, 200; base 30 |
| `early_exaggeration` | 12 (default) |
| `learning_rate` | `"auto"` (default) |
| `max_iter` | 1000 (default) |
| `init` | MDS classico delle distanze precalcolate (array passato da `embed`); default `"pca"` |
| `metric` | `dice`, `euclidean`, sempre via `"precomputed"` |
| `method`, `angle` | default (`"barnes_hut"`, 0,5) |
| `random_state` | 0 |

**Learning rate `"auto"`:** con $N = 5269$ e $\alpha = 12$ vale $5269/12/4 \approx 110$. Il paper di riferimento usa 200, circa il doppio: è un valore fisso, non derivato da $N$.
Le run di tuning fatte prima del passaggio a `"auto"` usavano 200 e non sono confrontabili punto per punto con quelle nuove.

## Come lo ottimizziamo
1. Si varia solo `perplexity`, nidificata per `metric`; gli altri parametri restano fissi (`docs/dev/models.md`, [dim_reduction_tuning_guide](dim_reduction_tuning_guide.md)).
2. Griglia di `perplexity`: 5, 15, 30, 50, 75, 100, 200 (base 30).
3. Per dataset grandi Kobak & Berens combinano 30 con $n/100$ (circa 50 per noi).

## Come leggiamo l'output
- **Trustworthiness** a `k = 10` sulla stessa matrice di distanze usata per l'embedding: è il punteggio del tuning.
- **Conservazione dei 10 vicini** e **correlazione delle distanze** (de Bodt et al., Kobak & Berens): il repo non le calcola. Nei benchmark t-SNE ha la conservazione dei vicini più alta (0,20-0,46) e una correlazione delle distanze inferiore a PCA.
- **Colori per metadati** (lato, volume, dataset) per riconoscere i confondenti.

## Attenzioni specifiche
- Tuning salvati e tuning nuovi non sono confrontabili punto per punto (inizializzazione casuale e learning rate 200 contro MDS classico e `"auto"`).
- L'inizializzazione informata (MDS classico) è una scelta del repo, non casuale.
- Con `dice` la gaussiana lavora sulle distanze Dice al quadrato.
