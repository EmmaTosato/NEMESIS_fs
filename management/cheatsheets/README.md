# Cheatsheets

Schede brevi per afferrare un concetto prima o durante una presentazione, scritte per essere ridette a voce. Sono una vista derivata: non contengono fatti che non stiano anche in `knowledge/notes/`, che resta la fonte di verità (costruita da letteratura e documentazione). Ogni scheda rimanda, in fondo, alla sezione di approfondimento.

Ogni metodo ha le stesse quattro parti: cosa fa, che tipo di metodo è, cosa restituisce, esempio concreto.

## Confronto

| Scheda | Tipo | Cosa si sceglie in anticipo | Cosa restituisce |
|---|---|---|---|
| [pca.md](pca.md) | riduzione, lineare, deterministica | il numero *k* di componenti | varianza spiegata, pesi, score |
| [pca-varimax.md](pca-varimax.md) | riduzione, lineare, deterministica | il numero *k* di componenti ruotate | pesi ruotati, score ruotati, quota di varianza |
| [agglomerative.md](agglomerative.md) | clustering gerarchico, deterministico | metrica e linkage; il numero di cluster si decide dopo, tagliando il dendrogramma | etichetta, dendrogramma |
| [hdbscan.md](hdbscan.md) | clustering per densità | `min_cluster_size` e `min_samples`; il numero di cluster non si fissa | etichetta (−1 = rumore), probabilità di appartenenza, stabilità |

Tutti e quattro sono non supervisionati: usano solo la matrice.
