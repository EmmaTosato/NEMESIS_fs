# Metodi di riduzione dimensionale usati in NEMESIS — teoria e interpretazione

> Fonte: paper metodologici originali (t-SNE: van der Maaten & Hinton 2008, *JMLR*; UMAP: McInnes, Healy & Melville 2018, arXiv; PaCMAP: Wang, Huang, Rudin & Shaposhnik 2021, *JMLR*) + un paper del corpus NEMESIS che applica t-SNE su dati di disconnessione da stroke (`papers/Thiebaut de Schotten et al - 2020 - .../markdown/_full.md`) — usato qui come precedente diretto per l'interpretazione, non solo come fonte dei parametri. Panoramica più ampia (metodi non usati nel progetto): [dimensionality_reduction_methods.md](dimensionality_reduction_methods.md).

## t-SNE
**Cosa fa**: converte le distanze ad alta dimensione in probabilità di "essere vicini", poi cerca un layout a bassa dimensione che riproduca quelle probabilità il più fedelmente possibile (minimizzando la divergenza KL tra le due distribuzioni). Usa una distribuzione a code pesanti in bassa dimensione per evitare che punti moderatamente distanti collassino tutti insieme (*crowding problem*).

**Come interpretarlo**: solo il **vicinato locale** è affidabile — due punti vicini nell'embedding erano vicini anche nei dati originali. **Le distanze tra cluster diversi e le loro dimensioni relative non sono interpretabili**: t-SNE le distorce per costruzione. La `perplexity` fissa il numero effettivo di vicini considerati per punto; valori diversi possono produrre configurazioni visivamente diverse dagli stessi dati.

**Uso nel progetto** (`config/registry/params_reduction.json`, `tsne`): `perplexity=30, early_exaggeration=12, learning_rate=200, max_iter=1000` — **parametri identici** a quelli usati da Thiebaut de Schotten et al. 2020 su 1333 lesioni stroke reali, dove t-SNE ha mostrato che le lesioni reali si aggregano più delle lesioni sintetiche di controllo (evidenza di ridondanza spaziale nella distribuzione delle lesioni stroke).

## UMAP
**Cosa fa**: costruisce un grafo pesato dei k-vicini più prossimi nello spazio originale (assumendo i dati distribuiti su una varietà Riemanniana), poi ottimizza un layout a bassa dimensione che riproduce quella topologia il più fedelmente possibile. Rispetto a t-SNE, bilancia meglio struttura locale e globale.

**Come interpretarlo**: come t-SNE, il vicinato locale è il segnale affidabile; le distanze globali restano meno garantite (anche se UMAP le preserva meglio di t-SNE). `n_neighbors` controlla il bilanciamento locale/globale (basso → più frammentato/locale, alto → più smussato/globale); `min_dist` controlla quanto i punti dello stesso cluster restano compatti.

**Uso nel progetto**: `n_neighbors=5, min_dist=0.0` (`config/registry/params_reduction.json`, `umap`) — più basso del default della libreria (`n_neighbors=15, min_dist=0.1`), quindi un embedding orientato maggiormente verso la struttura locale/fine piuttosto che quella globale. **Nessun paper del corpus NEMESIS applica UMAP su dati stroke**: a differenza di t-SNE (vedi sopra) non c'è un precedente diretto in letteratura clinica per interpretare gli assi su questo tipo di dati — da trattare con la stessa cautela di PaCMAP.

## PaCMAP
**Cosa fa** (Wang et al. 2021): a differenza di t-SNE/UMAP, che usano solo coppie di punti "vicini" per definire cosa preservare, PaCMAP usa esplicitamente **tre tipi di coppie** durante l'ottimizzazione — vicine (*near*, struttura locale), **mid-near** (punti moderatamente distanti, campionati tra i vicini più lontani, per preservare struttura *globale*) e lontane (*further*, per repulsione/separazione). I pesi relativi cambiano nel corso dell'ottimizzazione: più peso al mid-near all'inizio, poi si rifinisce il locale. Obiettivo dichiarato dagli autori: preservare sia struttura locale sia globale meglio di t-SNE/UMAP.

**Come interpretarlo**: il vicinato locale resta il segnale principale, ma — grazie al termine mid-near — **le distanze relative tra cluster diversi sono più affidabili** che in t-SNE/UMAP. `n_neighbors` controlla la scala locale, `MN_ratio`/`FP_ratio` il peso relativo delle coppie mid-near/further.

**Uso nel progetto**: `n_neighbors=5` (scelto per trustworthiness massima, vedi `results/lesion/dim_reduction/pacmap/tuning/`), `MN_ratio=0.5, FP_ratio=2.0` (default di libreria). **Nessun paper del corpus NEMESIS usa PaCMAP su dati stroke** — a differenza di t-SNE/UMAP non c'è un precedente diretto in letteratura clinica per interpretare gli assi su questo tipo di dati: da trattare con cautela extra.

## PCA
**Cosa fa**: trova le direzioni ortogonali di varianza massima nei dati (autovettori della matrice di covarianza). Lineare, deterministico, nessuna ottimizzazione stocastica.

**Come interpretarlo**: ogni componente è un asse di varianza, **ma non etichettato** — cosa rappresenti va sempre stabilito correlandolo con variabili note (età, volume lesione, ecc.), mai assunto a priori. A differenza degli altri tre metodi, PCA non ha alcuna nozione di "vicinato": due punti vicini nell'embedding PCA non erano necessariamente vicini nei dati originali, lo sono solo lungo le direzioni di massima varianza.

**Uso nel progetto**: sia come riduzione diretta pre-clustering (150 o 2 componenti, vedi `TUNING_ANALYSIS.md`), sia — in Thiebaut de Schotten 2020 — come step **successivo** a un embedding (PCA varimax-rotated dopo t-SNE), un uso diverso dal nostro. **Verifica empirica fatta in questo progetto** (`TUNING_ANALYSIS.md`): un caso concreto del principio "va sempre correlato con variabili note" — una delle due componenti PCA su lesioni voxel-wise si è rivelata correlata al 92% (Pearson r) col volume lesionale, non con la topografia della lesione.

## Confronto sintetico

| Metodo | Preserva | Distanze tra cluster affidabili? | Iperparametro chiave nel progetto |
|---|---|---|---|
| t-SNE | solo vicinato locale | no | `perplexity` |
| UMAP | vicinato locale + parte del globale | parziale | `n_neighbors`, `min_dist` |
| PaCMAP | locale + globale (esplicito, via mid-near) | sì, più delle prime due | `n_neighbors` |
| PCA | varianza globale (lineare) | sì, ma assi non etichettati | `n_components` |

## Nota interpretativa generale

Nessuno dei quattro metodi etichetta gli assi per te — l'interpretazione richiede sempre un confronto esterno con una variabile nota (clinica, demografica, o come nel caso PCA-volume qui sopra). Per t-SNE applicato a dati di disconnessione/lesione da stroke esiste un precedente diretto in letteratura (Thiebaut de Schotten 2020); per UMAP, PaCMAP e per PCA usata come riduzione diretta (non come step successivo a un embedding) non c'è ancora un precedente equivalente nel corpus NEMESIS — da trattare con cautela extra nell'interpretazione degli assi.
