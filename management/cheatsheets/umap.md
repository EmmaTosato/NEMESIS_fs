# UMAP

## Cosa fa

- Porta ogni soggetto da centinaia di migliaia di voxel a poche coordinate (di solito 2 o 3), **mantenendo vicini i soggetti che erano vicini**.
- **Passo 1**: costruisce un grafo in cui ogni soggetto è collegato ai suoi `n_neighbors` vicini più prossimi. Ogni collegamento ha un peso: la probabilità che esista davvero.
- **Passo 2**: dispone i punti nello spazio ridotto in modo che il loro grafo assomigli a quello di partenza. I punti collegati si attraggono, tutti gli altri si respingono, come in un layout di grafo con forze.
- Due parametri contano:

| parametro | effetto |
|---|---|
| `n_neighbors` basso | si guarda solo il locale: tante isole piccole, che possono essere rumore |
| `n_neighbors` alto | si guarda il quadro d'insieme: pochi blob grandi, si perde il dettaglio fine |
| `min_dist` basso | punti molto impacchettati: i gruppi sembrano netti per costruzione |
| `min_dist` alto | punti più sparsi: i vuoti tra i gruppi si chiudono |

## Che tipo di metodo è

- **Non lineare**: segue strutture curve, a differenza della PCA.
- **Stocastico**: due run senza seed fissato possono dare layout ruotati o specchiati. Conta chi è vicino a chi, non l'orientamento.
- **Non supervisionato**: usa solo la matrice.
- La **metrica** del grafo si sceglie: sulle lesioni binarie `jaccard` e `dice` confrontano la sovrapposizione. L'euclidea è dominata dal volume della lesione. `jaccard` e `dice` attenuano questo effetto ma non lo eliminano.
- Il grafo dipende da `n_neighbors` e `metric`, non da `min_dist`, che agisce solo sul disegno.

## Cosa restituisce

| Oggetto | Cos'è | Dimensione |
|---|---|---|
| **Embedding** | le coordinate di ogni soggetto nello spazio ridotto | soggetti × `n_components` |

- Le colonne **non hanno un ordine di importanza**, a differenza delle componenti della PCA. Per vedere una dimensione più bassa si rifà il fit con meno componenti, non si prendono le prime colonne.
- Non ci sono pesi sui voxel: un asse dell'embedding non ha una mappa cerebrale associata.
- **Non si leggono**: la dimensione dei gruppi e la distanza tra gruppi.
- Un gruppo che coincide con una variabile di confondimento (lato, dataset, volume) non è un pattern.

## Esempio concreto

Quattro soggetti su una retta, in posizione 0, 1, 5 e 7 (esempio costruito per illustrare):

| `n_neighbors` | Collegamenti | Cosa si vede |
|---|---|---|
| 1 | {0, 1} e {5, 7} | due isole separate |
| 2 | in più anche 1 → 5 | le due isole sono collegate: nell'embedding stanno vicine |

- Con `n_neighbors` basso i due gruppi sono mondi separati. Con valori più alti il grafo li lega e si vede che sono parte dello stesso insieme.
- Per questo non esiste un valore "giusto": si prova una griglia e si cerca un **plateau**, cioè un blocco di valori vicini che dà lo stesso disegno.
- Un riquadro che salta rispetto ai vicini (per esempio da 8 a 18 cluster) è sul bordo di un'instabilità.

Approfondimento: `knowledge/notes/dim_reduction_clustering/employed_dim_reduction_methods.md`, sezioni sul confronto con t-SNE e "Scegliere `n_neighbors` e `min_dist` di UMAP guardando le griglie".
