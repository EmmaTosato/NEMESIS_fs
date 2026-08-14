# Dimensionality Reductions — cosa fanno, come si interpretano, i parametri

> **Uso pratico nel progetto** (parametri effettivamente sweeppati, criteri di scelta): `dim_reduction.md`.
> **Rassegna più ampia della letteratura DR**: `knowledge/dim_reduction_clustering/dim_reduction_literature_survey.md`.
> **Rischi di clusterizzare sopra t-SNE/UMAP** (approfondimento dedicato, non solo un accenno): `knowledge/dim_reduction_clustering/challenge_of_clustering_after_dim_reduction.md`.

Qui: solo la meccanica dei due metodi e perché si comportano così, secondo i paper originali e la letteratura successiva che ne ha corretto alcuni luoghi comuni.

## L'idea comune a entrambi

Entrambi partono dallo stesso problema: dato un punto, chi sono i suoi vicini più prossimi nello spazio originale (alta dimensionalità)? Costruiscono una rappresentazione dei rapporti di vicinato (una distribuzione di probabilità per t-SNE, un grafo/simplicial set fuzzy per UMAP), poi ottimizzano una mappa a bassa dimensionalità che riproduca quei rapporti il più fedelmente possibile. **Nessuno dei due preserva le distanze globali per costruzione** — preservano vicinati locali, non una metrica assoluta.

## t-SNE (van der Maaten & Hinton, 2008)

**Meccanica**: converte le distanze in probabilità di essere "vicini" — gaussiane nello spazio originale, t-distribuzione (code pesanti) nello spazio a bassa dimensione. La t-distribuzione è la scelta chiave: risolve il *crowding problem* (in poche dimensioni non c'è spazio sufficiente per rappresentare fedelmente tutte le distanze medie di uno spazio ad alta dimensionalità; le code pesanti permettono a punti moderatamente lontani di stare più distanti nella mappa senza penalità eccessiva). Ottimizza minimizzando la divergenza KL tra le due distribuzioni.

**Parametri chiave**:

| Parametro               | Cosa controlla                                                                          | Note pratiche                                                                                                                                                                                                                                                             |
| ----------------------- | --------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `perplexity`          | Numero effettivo di vicini considerati per punto (una sorta di "quanti vicini contano") | Tipico 5-50, dev'essere « del numero di soggetti. Troppo basso → frammenta cluster reali in rumore; troppo alto → fonde cluster distinti.**La letteratura raccomanda di provare più valori, mai fidarsi di uno solo** (van der Maaten stesso lo nota nel paper) |
| `early_exaggeration`  | Amplifica le probabilità di vicinato nelle prime iterazioni                            | Aiuta cluster genuini a separarsi nettamente prima del raffinamento fine; raramente va ritoccato dal default                                                                                                                                                              |
| `learning_rate`       | Passo di gradiente nell'ottimizzazione                                                  | Troppo basso → convergenza lenta/incompleta; troppo alto → punti "esplodono" in una nuvola uniforme                                                                                                                                                                     |
| `max_iter`/`n_iter` | Iterazioni di ottimizzazione                                                            | Se troppo basso, l'embedding non ha ancora convergiuto (i punti "si muovono" ancora se rilanci con più iterazioni)                                                                                                                                                       |
| `metric`              | Definizione di distanza nello spazio originale                                          | Determina cosa conta come "vicino" prima ancora che t-SNE entri in gioco                                                                                                                                                                                                  |

**Come interpretarlo (e come NON farlo)** — riferimento classico: Wattenberg, Viégas & Johnson, *"How to Use t-SNE Effectively"* (Distill, 2016):

- **Le dimensioni dei cluster nel plot non sono significative** — t-SNE espande cluster densi e comprime quelli radi, la dimensione visiva non riflette la dispersione reale.
- **Le distanze *tra* cluster non sono significative** — due cluster disegnati vicini non sono necessariamente più simili di due disegnati lontani.
- **Perplexity multiple danno letture diverse dello stesso dato** — nessun valore singolo è "quello vero"; un pattern che appare solo a una perplexity specifica è meno affidabile di uno stabile su un range.
- **È stocastico**: run diversi (senza seed fissato) possono produrre layout ruotati/specchiati o con cluster in posizioni diverse — la topologia locale (chi è vicino a chi) è ciò che deve restare stabile, non l'orientamento.

## UMAP (McInnes, Healy & Melville, 2018)

**Meccanica**: fondamento matematico diverso da t-SNE — teoria dei fuzzy simplicial set (topologia), non probabilità gaussiane. Costruisce un grafo pesato dei k-vicini-più-prossimi nello spazio originale, poi ottimizza un layout a bassa dimensione che minimizza una cross-entropia tra il grafo originale e quello nell'embedding (invece della KL-divergenza di t-SNE). Il paper originale sostiene che questo preservi meglio la struttura *globale* rispetto a t-SNE — un punto rivisto criticamente in letteratura successiva (vedi sotto).

**Parametri chiave**:

| Parametro        | Cosa controlla                                                                                  | Note pratiche                                                                                                                                                                             |
| ---------------- | ----------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `n_neighbors`  | Analogo alla`perplexity` di t-SNE — quanti vicini definiscono il vicinato locale di un punto | Basso → più struttura locale/frammentata; alto → più struttura globale, meno dettaglio fine                                                                                           |
| `min_dist`     | Quanto i punti possono impacchettarsi nello spazio di output                                    | Basso → cluster visivamente più compatti e separati; alto → distribuzione più uniforme, utile per vedere gradienti continui invece di gruppi discreti                                 |
| `metric`       | Definizione di distanza nello spazio originale                                                  | Come per t-SNE — determina cosa conta come "vicino" a monte                                                                                                                              |
| `n_components` | Dimensionalità di output                                                                       | A differenza di t-SNE (quasi sempre 2-3), UMAP è usato correntemente anche a dimensionalità più alte (5-15) come step di preprocessing prima del clustering, non solo per visualizzare |
| `n_epochs`     | Iterazioni di ottimizzazione                                                                    | Analogo a`max_iter` di t-SNE                                                                                                                                                            |

**Come interpretarlo**:

- Stesso avvertimento di t-SNE su dimensioni/distanze tra cluster nel plot — non affidabili come misura assoluta.
- **La presunta superiorità di UMAP nel preservare la struttura globale è stata ridimensionata**: Kobak & Linderman (*"Initialization is critical for preserving global data structure in both t-SNE and UMAP"*, Nature Biotechnology 2021) mostrano che gran parte del vantaggio percepito di UMAP deriva dalla sua **inizializzazione di default basata su spectral embedding** (non casuale), non dalla funzione di costo in sé — inizializzando t-SNE allo stesso modo, la differenza si riduce molto. **Implicazione pratica**: l'inizializzazione (`init`) conta quanto l'algoritmo stesso; non assumere "struttura globale affidabile" solo perché è UMAP.
- **Generalmente più veloce e scalabile di t-SNE** su dataset grandi (migliaia di soggetti) — motivo pratico, non solo teorico, per cui è spesso la scelta di default quando N è alto.
- **Anche stocastico** — stesso discorso di t-SNE su seed/riproducibilità.

## Confronto rapido

|                   | t-SNE                                         | UMAP                                                                                                          |
| ----------------- | --------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| Fondamento        | Probabilistico (gaussiane → t-distribuzione) | Topologico (fuzzy simplicial sets)                                                                            |
| Costo             | Divergenza KL                                 | Cross-entropia                                                                                                |
| Struttura globale | Storicamente considerata più debole          | Storicamente considerata migliore, ma il divario dipende molto dall'inizializzazione (Kobak & Linderman 2021) |
| Scalabilità      | Più lento su N grandi                        | Generalmente più veloce, preferibile a migliaia di soggetti                                                  |
| Uso tipico        | Solo visualizzazione 2D/3D                    | Visualizzazione**e** preprocessing per clustering a più dimensioni (5-15D)                             |

## Quando usare quale (in generale)

- **N piccolo/medio, solo visualizzazione**: entrambi vanno bene: t-SNE ha spesso cluster visivamente più "puliti/separati", UMAP è più veloce.
- **N grande (migliaia di soggetti)**: UMAP preferibile per velocità.
- **Serve un embedding come input per un altro step (clustering, modello a valle)**: UMAP, perché supporta nativamente `n_components` più alti di 2-3 senza dover cambiare metodo di ottimizzazione (t-SNE con `n_components > 3` richiede il metodo "exact", molto più lento — niente Barnes-Hut oltre 3 dimensioni).
- **In entrambi i casi**: mai fidarsi di un solo run/parametro — confrontare più valori (perplexity/n_neighbors, eventualmente più seed) prima di leggere una struttura come reale, e verificare sempre che un pattern visivo non coincida con un confondimento noto (dataset, lato, volume) prima di interpretarlo come biologico.
