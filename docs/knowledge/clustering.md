# Clustering — cosa fanno questi metodi

> **Implementazione:** `src/analysis/clustering.py`, `config/registry/params_clustering.json`.
> **Come leggere gli indici di tuning** (silhouette, dendrogramma, eigengap...): `docs/knowledge/clustering_tuning_guide.md`.
> **Riduzione dimensionale**: `docs/knowledge/dim_reduction.md`.

Guida in linguaggio semplice a cosa fa ciascun metodo di clustering usato nel progetto — non un manuale di ML, solo il minimo per capire cosa controlla un iperparametro in config.

## Il problema

Il clustering raggruppa i soggetti per somiglianza, senza sapere in anticipo la risposta giusta (*unsupervised*) — l'ipotesi è che i cluster corrispondano a topografie di lesione/disconnessione distinte. Gira o su un embedding già ridotto (`dim_reduction_clustering.py`) o direttamente su una matrice di feature (`clustering.py`).

La maggior parte dei metodi (KMeans, Agglomerative, GMM, Spectral) richiede di decidere **in anticipo** quanti gruppi cercare (`n_clusters`). HDBSCAN è l'eccezione: scopre da solo il numero di gruppi dalla densità dei dati.

## KMeans

Piazza un centroide per cluster, assegna ogni soggetto al centroide più vicino, ricalcola i centroidi, ripete finché non si stabilizza.

- Bisogna decidere `n_clusters` in anticipo.
- Assume cluster tondeggianti e di dimensioni simili — per questo di solito gira su un embedding (2-15 dimensioni) e non sulla matrice voxel grezza (centinaia di migliaia di colonne, geometricamente inaffidabile per KMeans).
- Sensibile alla scala delle feature — non un problema se già in `[0, 1]` o su un embedding, lo sarebbe su voxel grezzi di scale molto diverse.
- Stocastico (inizializzazione casuale dei centroidi): fissare `random_state` per la riproducibilità.

## Agglomerative (gerarchico)

Parte da ogni soggetto come cluster a sé, fonde via via i due cluster più vicini finché non ne restano `n_clusters`.

- Bisogna decidere `n_clusters` in anticipo, come KMeans.
- `linkage` controlla come si misura la "distanza" tra due cluster durante la fusione: `ward` (il default qui, tende a cluster simili per forma a KMeans) minimizza l'aumento di varianza interna; `average`/`complete`/`single` sono meno vincolati nella forma ma più sensibili a outlier (`single` in particolare, tende a incatenare gruppi distinti).
- Deterministico — nessun `random_state`.
- Il tuning produce anche un dendrogramma (`dendrogram.png`): si legge dal basso verso l'alto, il salto verticale più grande tra due fusioni indica il taglio più naturale.

## GaussianMixture (GMM)

Modella i dati come una miscela di `n_components` distribuzioni gaussiane, assegna ogni soggetto alla componente più probabile.

- Bisogna decidere `n_components` in anticipo (stesso ruolo di `n_clusters`).
- Permette cluster ellittici e di dimensioni diverse (ogni componente ha una propria forma), a differenza di KMeans che assume cluster tondi e simili.
- Stocastico: fissare `random_state`.
- Nel tuning ha 2 indici propri, `bic`/`aic` — basati sulla verosimiglianza, penalizzano modelli troppo complessi. Più basso = meglio.

## HDBSCAN

Raggruppa punti densamente vicini tra loro; chi non appartiene a nessuna zona densa viene etichettato "rumore" (`-1`) — non un errore, un risultato legittimo ("questo soggetto non si inquadra in nessun gruppo").

- **Non richiede `n_clusters`** — lo scopre da solo dalla struttura di densità.
- Ha sostituito DBSCAN: niente `eps` (soglia di distanza globale, da ritarare per ogni spazio di feature e che si rompeva con cluster di densità diverse) — al suo posto `min_cluster_size`, la dimensione minima perché un gruppo sia considerato un vero cluster.
- Nessun grafico diagnostico a sé — `min_cluster_size` si giudica direttamente dagli indici sweeppati (silhouette, `noise_fraction`).
- Va sempre letto insieme a `noise_fraction`: un `min_cluster_size` alto può dare indici ottimi solo perché scarta molti soggetti "difficili" come rumore — è un vero compromesso qualità/copertura, non un pranzo gratis.

## SpectralClustering

Costruisce un grafo di somiglianza tra soggetti (collega ogni soggetto ai suoi vicini più prossimi), clusterizza sugli autovettori del Laplaciano di quel grafo, poi un ultimo passaggio di KMeans sul risultato.

- Bisogna decidere `n_clusters` in anticipo, come KMeans/Agglomerative.
- Trova cluster non convessi (a mezzaluna, forme irregolari) che KMeans sbaglierebbe, perché lavora sulla connettività del grafo e non sulla distanza euclidea grezza.
- Il tuning produce un `eigengap_plot.png`: il `k` consigliato è dove c'è il salto più grande tra due autovalori consecutivi — un criterio più fondato teoricamente degli indici generici, specifico per questo metodo.
- Più pesante computazionalmente di KMeans/Agglomerative — più pratico su coorti più piccole (es. le ~500 di Task 3) che sull'intera coorte lesioni.

## RSC (Repeated Spectral Clustering)

Non è un metodo indipendente da zero: è SpectralClustering (sopra) + un trucco preso dal "consensus clustering" (vedi sezione sotto), pubblicato da Tshimanga et al. (2025) e usato da Zanola et al. (2026, `papers/nemesis/Zanola et al - 2026...`) per raggruppare traiettorie di recupero post-ictus.

- L'unico punto realmente casuale dentro SpectralClustering è il k-means finale (dopo aver trasformato i dati sugli autovettori del grafo — vedi sopra). RSC ripete **solo quel passo** `n_repeats` volte con semi diversi, e conta quante volte ogni coppia di soggetti finisce nello stesso cluster → matrice di co-occorrenza `C`.
- Le etichette finali **non** vengono da una singola delle `n_repeats` run, ma derivate da `C` stessa — qui il paper di Zanola non specifica l'algoritmo esatto (rimanda a Tshimanga et al. 2025, non disponibile in `papers/`). Implementato come clustering gerarchico (average linkage) su `1 - C`, tagliato a `n_clusters` — lo step standard di letteratura per questo tipo di matrice (Fred & Jain 2002, la stessa referenza che Zanola cita per la parte "consensus" di RSC).
- Per scegliere `n_clusters`: **non** si sweeppa `"rsc"` direttamente per questo — si sweeppa `"spectral"` con la diagnostica di stabilità RSC attiva (vedi sezione sotto), che implementa esattamente il criterio di Zanola (massimo spectral gap sulla matrice di co-occorrenza), poi si scrive il valore scelto nella config di `"rsc"`.
- Più pesante di SpectralClustering da solo (rifà l'intera procedura `n_repeats` volte) — pratico su coorti piccole/medie, non sull'intera coorte lesioni.

## Come si scelgono gli iperparametri

**Nessuna selezione automatica, mai.** `clustering.py --fine_tuning true` sweeppa una griglia di valori e scrive `tuning_results.csv`/i plot — sei tu a guardarli e a scegliere il valore, scrivendolo poi a mano in `params_clustering.json`. Come leggere gli indici generici (silhouette, Calinski-Harabasz, Davies-Bouldin) e le diagnostiche per metodo è spiegato in dettaglio in `docs/knowledge/clustering_tuning_guide.md` — qui basti sapere che nessun indice da solo è definitivo, vanno sempre letti insieme.

## Clustering di stabilità (RSC e Monti)

Gli indici sopra dicono "quanto è buono" un singolo risultato di clustering. Due metodi dalla letteratura dicono invece "quanto è **stabile**" un certo numero di cluster `k`, ripetendo il clustering più volte:

- **RSC** (diagnostica) — stessi dati, semi casuali diversi: quanto viene riprodotto lo stesso risultato al variare solo dell'inizializzazione.
- **Monti** — sottocampioni casuali diversi di soggetti: quanto il risultato dipende da chi capita nel campione.

Disponibili solo per KMeans/GMM/Spectral (gli unici con vera casualità interna da sfruttare — Agglomerative/HDBSCAN sono deterministici, ripeterli non direbbe nulla di nuovo). Sono opzionali, si attivano aggiungendo un blocco `"consensus"` in config — vedi `docs/guides/clustering.md` per il formato JSON esatto.

**Nota**: questa è solo la diagnostica ("quanto fidarsi di k"), calcolata dentro lo sweep di un altro metodo (tipicamente `"spectral"`). Il metodo `"rsc"` sopra è una cosa diversa: usa la stessa identica matrice di co-occorrenza, ma per produrre davvero le etichette finali dei cluster, non solo un punteggio di stabilità.
