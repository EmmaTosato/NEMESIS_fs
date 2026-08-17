# Tuning della dim reduction — come leggere plot e indici

> **Implementazione:** `src/analysis/tuning.py` (calcolo indici, sweep), `src/analysis/plotting.py` (`plot_tuning_curve`, `plot_embedding_grid_blocks`), `src/analysis/embedding_plots.py`/`embedding_coloring.py` (colorazione embedding). Orchestrazione in `src/pipeline/dim_reduction.py` quando `fine_tuning: true`.
> **Guida d'uso:** `docs/guides/dim_reduction.md`. **Cosa fanno i metodi**: `dim_reduction.md`, `umap_tsne_guide.md`. **Letteratura di riferimento**: `dim_reduction_literature_survey.md`.

## Cos'è il tuning

Per `umap`/`tsne`/`pacmap`/`pca`/`pca_varimax`, il tuning esegue lo stesso metodo su una griglia di iperparametri (`config/registry/params_reduction.json`'s `tuning_grid`) e calcola, per ogni combinazione, un solo numero di qualità. **Nessuna selezione automatica**: la scelta finale resta sempre umana, guardando `tuning_results.csv` e i plot, poi scritta a mano in `params_reduction.json`'s `"params"`.

## Le due metriche

| Metodo | Metrica | Perché |
|---|---|---|
| `umap`, `tsne`, `pacmap` | **Trustworthiness** (Venna & Kaski, 2006) | Nessun ground truth noto — l'unica cosa verificabile è se l'embedding ha distorto la vicinanza locale rispetto ai dati originali |
| `pca`, `pca_varimax` | **Varianza cumulativa spiegata** | Criterio nativo di PCA — quanta informazione sopravvive comprimendo a `n_components` |

**Varianza cumulativa spiegata**: somma delle prime `n_components` `explained_variance_ratio_` di sklearn. Cresce monotonicamente — si legge come curva a **gomito**. Thiebaut de Schotten et al. 2020 usa soglia fissa >90%.

## Trustworthiness, in dettaglio

`umap`, `tsne` e `pacmap` non hanno una nozione nativa di "varianza spiegata" (non sono decomposizioni lineari) — l'unica metrica di qualità disponibile senza un ground truth di riferimento è la **trustworthiness** (Venna & Kaski 2006, implementata in `sklearn.manifold.trustworthiness`, unica metrica di questo tipo nella libreria).

**Definizione formale** (dalla documentazione scikit-learn):

```
T(k) = 1 − 2 / (n·k·(2n − 3k − 1)) · Σᵢ Σⱼ∈N(i,k) max(0, r(i,j) − k)
```

dove `n` è il numero di campioni, `k` il numero di vicini considerati (`n_neighbors`), `N(i,k)` l'insieme dei `k` vicini di `i` **nell'embedding** (spazio di output), e `r(i,j)` il rango di `j` come vicino di `i` **nello spazio originale** (input). In parole: per ogni punto `i`, si guarda chi sono i suoi `k` vicini nell'embedding, e per ciascuno si penalizza quanto era *lontano* nello spazio originale (rango `> k`) — un vicino "inaspettato" nell'embedding che nello spazio originale era molto distante costa di più di uno che era solo leggermente fuori dai primi `k`. Range `[0,1]`, più alto = meglio; `n_neighbors` deve restare `< n_samples/2` perché la formula sia garantita in quel range.

**Cosa misura, e cosa NON misura**: trustworthiness conta solo le **intrusioni** — punti che sono vicini nell'embedding ma non lo erano nello spazio originale (falsi positivi di vicinanza). Non misura l'opposto (punti vicini nello spazio originale che l'embedding ha allontanato, cioè le "omissioni") — quella è la **continuity**, la metrica complementare, che scikit-learn non implementa direttamente (va calcolata scambiando i ruoli di spazio di input e output nella stessa formula). NEMESIS oggi calcola solo trustworthiness, non continuity — un punteggio alto garantisce "quello che vedo vicino nell'embedding è affidabile", non "tutto quello che era vicino nei dati originali è ancora visibile come tale".

**Caveat pratici, validi per l'uso in `src/analysis/tuning.py`**:

- `k` è un parametro a parte (`trustworthiness_n_neighbors`), **non** lo stesso `n_neighbors` di UMAP (`docs/dev/config.md`) — sono due grafi k-NN concettualmente diversi, uno costruito dall'algoritmo di riduzione, l'altro usato solo per valutare il risultato a posteriori.
- Va calcolata con la **stessa metrica** con cui è costruito l'embedding (jaccard con jaccard, non l'euclidea di default di sklearn) — bug reale trovato e corretto in una sessione precedente (vedi `lessons_learned.md` #15): la formula sopra usa `r(i,j)`, il rango nello spazio di input, che dipende interamente da quale nozione di distanza si usa per calcolarlo.
- **Non comparabile tra `n_components` diversi**: cresce quasi meccanicamente con più dimensioni (più spazio disponibile, meno intrusioni forzate) — confrontare solo a parità di `n_components` (da qui la scelta di tenerlo tra i `nested_params`).
- Un punteggio alto non garantisce un pattern *clinico* interessante (può essere un artefatto strutturale, es. jaccard/dice che separa nettamente per lato lesione) — va sempre incrociato con i plot colorati.

## Cosa ottimizzano internamente UMAP e t-SNE

Il motivo per cui trustworthiness + ispezione visiva sono gli unici strumenti di validazione disponibili (non un ripiego, ma l'unica cosa possibile) è legato a **come** questi due metodi trovano il loro embedding — utile da tenere presente quando si interpretano risultati instabili al variare del seed.

**t-SNE** (van der Maaten & Hinton, 2008): converte le distanze in probabilità di vicinato — `P` nello spazio originale (gaussiane centrate su ogni punto, la cui larghezza è calibrata dalla `perplexity`), `Q` nell'embedding (una distribuzione t di Student, a code pesanti, che è la differenza chiave rispetto a SNE, il metodo precedente). L'embedding finale è quello che minimizza la **divergenza di Kullback-Leibler** `KL(P‖Q)`, tramite discesa del gradiente (con accorgimenti pratici come *early exaggeration* — nelle prime iterazioni le probabilità `P` vengono amplificate per favorire la formazione di cluster ben separati prima di raffinare i dettagli — e momentum).

**UMAP** (McInnes et al., 2018): costruisce un grafo topologico *fuzzy* (insieme simpliciale, basato su k-NN) sia nello spazio originale sia nell'embedding, e minimizza la **cross-entropy** tra le due rappresentazioni:

```
Σₑ  wₕ(e)·log(wₕ(e)/wₗ(e)) + (1−wₕ(e))·log((1−wₕ(e))/(1−wₗ(e)))
```

dove `wₕ(e)`/`wₗ(e)` sono i pesi (interpretati come probabilità) assegnati allo stesso arco `e` nel grafo in alta e in bassa dimensione. Il primo termine genera una **forza attrattiva** (avvicina i punti quando il peso in alta dimensione è alto), il secondo una **forza repulsiva** (allontana i punti quando il peso in alta dimensione è basso) — l'ottimizzazione è una discesa del gradiente stocastica con *negative sampling* (la stessa tecnica di word2vec, per evitare di dover considerare tutte le coppie di punti a ogni iterazione).

**Il punto in comune, rilevante per il tuning**: sia t-SNE sia UMAP si possono leggere come un sistema fisico di punti soggetti a forze attrattive (tra vicini) e repulsive (tra tutti gli altri) fino a un equilibrio — UMAP usa forze attrattive più marcate, il che produce cluster visivamente più compatti e netti di t-SNE, ma i due metodi appartengono allo stesso spettro attrazione-repulsione, non a due logiche indipendenti (de Bodt et al. 2025, §3.5). In entrambi i casi la funzione di perdita è **non convessa**: a differenza di PCA (autovalori, ottimo globale garantito) o dei metodi spettrali (Isomap, Laplacian eigenmaps), non c'è garanzia che la discesa del gradiente trovi l'ottimo globale — run diversi (seed diversi, inizializzazioni diverse) possono fermarsi in minimi locali diversi. L'unica mitigazione nota in letteratura è un'**inizializzazione informata** (es. via spectral embedding, non punti casuali — Kobak & Linderman 2021, citato sia da de Bodt et al. sia da Wani 2025), non una garanzia.

Questo è il motivo metodologico, non solo pratico, per cui NEMESIS non si affida mai a un singolo run: senza un ottimo globale garantito, un numero di trustworthiness alto per una singola combinazione di iperparametri/seed non basta a escludere che un seed diverso avrebbe trovato un embedding sostanzialmente diverso (si veda `challenge_of_clustering_after_dim_reduction.md` per le implicazioni quando su quell'embedding si clusterizza a valle).

## Numero e plot, mai uno solo

Il numero è cieco a *come* è fatto l'embedding — `dim_reduction.py` produce anche gli scatter reali (`embeddings_grid_*.png`, uno per parametro libero, meccanismo `nested_params` in `docs/guides/dim_reduction.md`). Il numero dice "quale combinazione preserva meglio il vicinato"; il plot dice "che forma ha l'embedding" — utile per scartare combinazioni tecnicamente valide ma degeneri, o per notare se una struttura netta coincide con dataset/lato/volume (confondimento) invece che un pattern reale. **Leggerli sempre insieme.**

## File di output

- `tuning_results.csv`: una riga per combinazione (colonna metrica secondo la tabella sopra). Se `nested_params` è dichiarato, una copia filtrata per ogni foglia.
- `tuning_plot.png`: curva a 1 parametro (solo se **non** c'è `nested_params` e la griglia libera ha 1 solo parametro — es. PCA/PaCMAP).
- `embeddings_grid_<colore>.png`: scatter reali per foglia, quando `nested_params` **è** dichiarato (umap/tsne).
- `embeddings.npz` (opt-in, `save_tuning_embeddings: true`): l'embedding vero di **ogni** combinazione sweeppata, indicizzato da una chiave `"chiave1=valore1,..."` — pensato per un futuro plot interattivo stile Figura 4 di [pair-code.github.io/understanding-umap](https://pair-code.github.io/understanding-umap/) (griglia `n_neighbors`×`min_dist`, solo lettura/plotting, mai rifit lato browser — non ancora implementato).
- `metadata.csv` (stesso trigger di `embeddings.npz`): anagrafica arricchita (`lesion_volume_voxels`/`lesion_side`/`nihss`), necessaria perché `embeddings_grid_*.png` colora i punti al volo.
- `config.md`: snapshot di `tuning_grid`/`nested_params`/parametri fissi per l'intero run.
