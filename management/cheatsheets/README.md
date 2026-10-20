# Cheatsheets

Schede brevi per afferrare un concetto prima o durante una presentazione, scritte per essere ridette a voce. Sono una vista derivata: non contengono fatti che non stiano anche in `knowledge/notes/` (o, per i parametri del progetto, in `docs/`), che restano la fonte di verità. Ogni scheda rimanda, in fondo, alla sezione di approfondimento.

Ogni metodo ha le stesse quattro parti: cosa fa, che tipo di metodo è, cosa restituisce, esempio concreto. Gli esempi numerici sono costruiti per illustrare, non vengono dai dati.

## Riduzione dimensionale

| Scheda | Tipo | Cosa si sceglie in anticipo | Cosa restituisce |
|---|---|---|---|
| [pca.md](pca.md) | lineare, deterministica | il numero *k* di componenti | varianza spiegata, pesi, score |
| [pca-varimax.md](pca-varimax.md) | lineare, deterministica | il numero *k* di componenti ruotate | pesi ruotati, score ruotati, quota di varianza |
| [umap.md](umap.md) | non lineare, stocastica | `n_neighbors` e `min_dist` | embedding |
| [pacmap.md](pacmap.md) | non lineare | `n_neighbors`, `MN_ratio`, `FP_ratio` | embedding |

## Clustering

| Scheda | Tipo | Cosa si sceglie in anticipo | Cosa restituisce |
|---|---|---|---|
| [kmeans.md](kmeans.md) | partizionale, non deterministico | il numero *k* di cluster | etichetta, inertia |
| [agglomerative.md](agglomerative.md) | gerarchico, deterministico | metrica e linkage; il numero di cluster si decide dopo, tagliando il dendrogramma | etichetta, dendrogramma |
| [hdbscan.md](hdbscan.md) | per densità | `min_cluster_size` e `min_samples`; il numero di cluster non si fissa | etichetta (−1 = rumore), probabilità di appartenenza, stabilità |
| [evidence-accumulation.md](evidence-accumulation.md) | ensemble / consensus | `base_method`, `n_repeats`, `threshold`; il numero di cluster finali emerge | etichetta, matrice di co-associazione |
| [adp.md](adp.md) | per picchi di densità | `Z` e la metrica; il numero di cluster non si fissa | etichetta (−1 = rumore) |

Tutti i metodi sono non supervisionati: nel progetto le funzioni di riduzione e di clustering ricevono solo la matrice (`docs/dev/models.md`).

## Altri riassunti

Non sono schede per metodo e non derivano dalla letteratura.

- [clustering_metrics_report.md](clustering_metrics_report.md): dove compaiono le metriche di valutazione del clustering (sweep di tuning, analisi del tuning, produzione) e una proposta di convergenza. Fonte: lettura del codice e dei docs del 20-10-26, niente è stato rieseguito.
