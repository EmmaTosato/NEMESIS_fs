# ADP

## Cosa fa

- *Advanced Density Peaks* (d'Errico et al. 2021, libreria DADApy): cerca i **picchi di densità** tra i soggetti, cioè i punti con molti vicini intorno.
- Ogni soggetto viene assegnato al picco a cui è collegato. **Il numero di cluster non si sceglie: emerge dai dati.**
- L'unica manopola è **`Z`**, la soglia di significatività: un picco resta un cluster a sé solo se la sua densità supera quella del punto più basso che lo collega a un picco vicino di più di `Z` volte l'incertezza della stima.
  - `Z` basso: molti cluster piccoli.
  - `Z` alto: i picchi si fondono, pochi cluster.
- Si usa sulla **matrice grezza** (lesione, SDC voxelwise o streamline), non su un embedding. È l'unico metodo che clusterizza direttamente le distanze `dice` e `jaccard`.

## Che tipo di metodo è

- **Basato sulla densità** e **non supervisionato**, come HDBSCAN: non richiede il numero di cluster.
- La **metrica** si sceglie: `dice`, `jaccard` o `euclidean`. Su una matrice binaria `dice` e `jaccard` misurano la sovrapposizione tra due mappe.
- Un secondo parametro, `maxk`, è il tetto ai vicini usati per stimare la densità di ogni soggetto.
- Gira da solo, in un ambiente conda separato da `nemesis` (dipende da `jax`).
- Memoria: una matrice soggetti × soggetti per ogni metrica richiesta (circa 270 MB a 5800 soggetti).

## Cosa restituisce

| Oggetto | Cos'è | Dimensione |
|---|---|---|
| **Etichetta** | il cluster di ogni soggetto; −1 = rumore | una per soggetto |

- Sono rumore (−1) le **righe tutte a zero**, perché `dice` e `jaccard` non sono definite su di esse.
- Le **righe duplicate** si clusterizzano una volta sola e ogni duplicato prende l'etichetta del gemello.
- Come si legge lo sweep di `Z`:
  - si cerca un **plateau**: un tratto con lo stesso numero di cluster e `ari_vs_prev_z` vicino a 1, cioè il risultato non dipende dalla soglia;
  - se la partizione cambia a ogni passo, dipende dalla soglia e non dai dati;
  - un solo cluster a `Z` alto è il limite atteso;
  - un numero di cluster che compare per un solo `Z` è un caso dello sweep, non un risultato.

## Esempio concreto

Due picchi collegati da un punto più basso (numeri inventati per illustrare). Il picco più basso ha densità 10, il punto che lo collega all'altro ha densità 8, e l'incertezza della stima è 0,5:

| `Z` | Soglia (`Z` × 0,5) | Differenza 10 − 8 = 2 | Risultato |
|---|---|---|---|
| 1,65 (default) | 0,83 | 2 > 0,83 | il picco resta un cluster a sé |
| 16 | 8 | 2 < 8 | il picco si fonde con l'altro |

- Con `Z` basso i due picchi sono due cluster, con `Z` alto uno solo. Lo sweep varia `Z` da 0,25 a 16.
- Nessun numero di cluster è scelto a mano: sta a noi decidere se c'è un tratto stabile di `Z`.

Approfondimento: `knowledge/notes/dim_reduction_clustering/clustering_tuning_guide.md`, sezione "ADP"; i parametri sono in `docs/guides/clustering.md`.
