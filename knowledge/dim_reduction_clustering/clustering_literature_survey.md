# Clustering — rassegna della letteratura

> Fonti (lette integralmente): Dinh, Hauchi, Lisik et al. 2025, *"Data clustering: an essential technique in data science"* (Expert Systems with Applications); Fred & Jain 2002, *"Data clustering using evidence accumulation"* (ICPR); Bicego 2021, dispense del corso *"Riconoscimento e Recupero dell'informazione per Bioinformatica"* — Il clustering, parte 1 e 2 (Università di Verona).
>
> Rassegna ampia sul clustering come campo, non filtrata sui soli metodi implementati in NEMESIS. Per cosa fanno concretamente i metodi usati nel progetto: `clustering.md`. Per come leggere gli indici di tuning: `knowledge/dim_reduction_clustering/clustering_tuning_guide.md`. Per la sfida specifica di clusterizzare *sopra* un embedding: `knowledge/dim_reduction_clustering/challenge_of_clustering_after_dim_reduction.md`.

Le tre fonti si completano per ruolo più che per contenuto: Dinh et al. (2025) è la rassegna panoramica più recente — tassonomia, algoritmi, strumenti, applicazioni; Fred & Jain (2002) è un singolo paper metodologico che introduce l'*evidence accumulation clustering*, il metodo di consensus clustering effettivamente implementato in `src/analysis/clustering.py`; le dispense di Bicego (2021) sono un corso universitario completo che copre la meccanica interna degli algoritmi (K-means e varianti, gerarchico agglomerativo, misture di Gaussiane) e — capitolo interamente assente in Dinh et al. — la **validazione quantitativa** del clustering (indici esterni/interni, cluster tendency).

## 1. Perché il clustering è "difficile" — la cornice concettuale

Bicego apre con tre problemi fondativi che nessuna delle tre fonti nega mai, solo se ne fanno carico in modo diverso:

1. **Il concetto di "cluster" è vago e soggettivo** — cambiare la misura di similarità cambia il risultato (esempio didattico: lo stesso set di frutti si raggruppa per specie *o* per colore, a seconda della similarità scelta). Non è un difetto risolvibile, è intrinseco al problema non supervisionato.
2. **Nessuna informazione a priori** — a differenza della classificazione, non c'è (di norma) un numero di gruppi noto in anticipo.
3. **Nessun ground truth** — un algoritmo di clustering produce *sempre* un risultato, anche su dati completamente casuali; la domanda "questi cluster sono reali?" richiede una validazione dedicata (§4 sotto), non è mai automatica.

Un tipico sistema di clustering (Bicego, seguendo Jain, Murty & Flynn 1999, la stessa survey citata anche da Dinh et al.) si scompone in passi sequenziali con feedback: rappresentazione del pattern → definizione della similarità → design dell'algoritmo → validazione → interpretazione dei risultati. Dinh et al. formalizzano lo stesso schema come workflow a 6 fasi (EDA → preprocessing → selezione dell'algoritmo → ottimizzazione → valutazione → interpretazione) — stesso ciclo, terminologia più moderna orientata alla data science industriale.

## 2. Tassonomia dei metodi (Dinh et al. 2025)

Dinh et al. classificano il clustering su due assi — tipo di dato (numerico/categorico/misto/testo/spatio-temporale/rete/sequenze genomiche) e **tecnica**:

| Famiglia | Idea | Esempi |
|---|---|---|
| **Partizionale** | Una singola partizione, `k` fissato in anticipo | K-Means, K-Modes/K-Prototypes (dati categorici/misti), Fuzzy C-Means |
| **Gerarchico** | Serie di partizioni annidate (dendrogramma), agglomerativo (bottom-up) o divisivo (top-down) | Single/Complete/Average/Ward Linkage |
| **Density-based** | Cluster = regioni dense separate da regioni sparse, nessun `k` richiesto | DBSCAN, e la sua evoluzione HDBSCAN |
| **Model-based** | Si assume un modello generativo (tipicamente misture di Gaussiane), si stima via Expectation-Maximization | GMM/MClust |
| **Subspace** | I cluster esistono solo in sottoinsiemi di dimensioni, non nello spazio completo — pensato per l'alta dimensionalità | CLIQUE |
| **Graph-based** | Dati come grafo pesato, cluster = sottografi densamente connessi | Louvain (community detection) |
| **Data stream** | Clustering incrementale su dati che arrivano in continuo, con gestione del *concept drift* | ClueStream |
| **Ensemble/consensus** | Combina più clustering (algoritmi diversi o run multipli) in un risultato unico | Cluster Ensembles (Strehl & Ghosh 2002) — la stessa famiglia di **evidence accumulation** (Fred & Jain 2002, §3 sotto) |

Un punto rilevante per NEMESIS: Dinh et al. collocano esplicitamente **t-SNE e UMAP dentro la tassonomia del clustering stesso** ("Base on data characteristics → High-dimensional clustering → Dimensional reduction techniques"), non solo come preprocessing esterno — coerente con l'osservazione (approfondita in `challenge_of_clustering_after_dim_reduction.md`) che riduzione dimensionale e clustering, nella pratica moderna, sono spesso un'unica pipeline concettuale, non due passi indipendenti.

## 3. Evidence Accumulation Clustering (Fred & Jain 2002) — il metodo che usiamo

Fred & Jain propongono uno schema **split-and-merge**, motivato da un limite specifico di K-Means: impone cluster sferici e non riesce a separare forme complesse (es. due mezzelune annidate).

- **Split**: si decompone il dataset in un numero *grande* di cluster piccoli e compatti, tramite K-Means ripetuto `N` volte con inizializzazioni casuali diverse (`N=200` negli esperimenti del paper).
- **Combine**: si costruisce una **matrice di co-associazione** `n×n`, dove `co-assoc(i,j) = votes(i,j) / N` — quante volte, sulle `N` run, i pattern `i` e `j` sono finiti nello stesso cluster. È una nuova misura di similarità tra pattern, derivata dal *voto* delle clusterizzazioni multiple, non da una distanza originale.
- **Merge**: si applica un metodo single-link (equivalente a tagliare un minimum spanning tree) sulla matrice di co-associazione, tagliando i legami deboli a una soglia `t` (default `0.5` — due pattern finiscono nello stesso cluster finale solo se sono stati raggruppati insieme in almeno metà delle `N` run).

Due parametri, due ruoli diversi (`k` per la fase di split, `t` per la fase di merge) — la stessa distinzione concettuale che il nostro `src/analysis/clustering.py` implementa (`n_clusters`/`n_components` del `base_method` vs `threshold`, vedi `clustering.md`). Il paper dimostra il metodo su dataset sintetici a forma complessa (mezzelune, spirali) dove K-Means fallisce per costruzione, oltre che sul dataset Iris (indice di consistenza 0.84 con `k=3`, contro 0.68 del single-link diretto sui dati grezzi).

**Limite dichiarato dagli stessi autori**: il metodo fatica sui *cluster che si toccano* (gaussiane 2D sovrapposte con distanza di Mahalanobis piccola) — proprio perché lo split iniziale via K-Means non riesce a separarli nemmeno localmente, e non c'è nulla da "fondere" in un secondo tempo. Riportato esplicitamente perché rilevante per NEMESIS: se le topografie di lesione formano un continuum più che gruppi discreti, questo metodo (come qualunque metodo di clustering discreto) non lo rivelerà come tale.

## 4. Validazione del clustering (Bicego 2021)

Capitolo che Dinh et al. toccano solo di sfuggita (una singola figura con l'elenco degli indici) mentre Bicego lo tratta in profondità — colma un vuoto reale nella rassegna panoramica.

**Tipi di indici**:
- **Esterni** — confrontano il clustering trovato con etichette note a priori (non disponibili per NEMESIS in modo diretto, dato che non abbiamo un ground truth di "fenotipo vero"): Rand Index, Jaccard, Fowlkes-Mallows, Γ statistic — tutti costruiti a partire da una matrice di contingenza 2×2 (coppie di oggetti concordi/discordi tra le due partizioni).
- **Interni** — usano solo i dati, nessuna etichetta esterna: l'indice discusso in dettaglio da Bicego è **Davies-Bouldin** (1979) — per ogni coppia di cluster, rapporto tra dispersione interna combinata e distanza tra i centroidi; l'indice finale è la media del "caso peggiore" per ciascun cluster. Più basso = meglio. È l'indice usato anche nel nostro `clustering_tuning_guide.md`.
- **Relativi** — confrontano due risultati di clustering diversi tra loro (non un singolo risultato contro un riferimento esterno).

**Cluster tendency**: un concetto che né Dinh et al. né la nostra pipeline attuale affrontano esplicitamente — prima ancora di clusterizzare, verificare se i dati hanno *davvero* una tendenza ad aggregarsi (contro casualità spaziale pura, o contro una distribuzione regolare/repulsiva) — perché un algoritmo di clustering produce sempre un output, anche su rumore puro. Bicego cita gli *scan test* come esempio (contare i punti nella sottoregione più popolosa, verificare se il numero è "inusualmente" alto). Nota per NEMESIS: non implementato oggi in `src/analysis/`, un gap esplicito da segnalare, non da nascondere.

## 5. Cosa portiamo in NEMESIS

- **Evidence accumulation** (Fred & Jain 2002) è già implementato fedelmente in `src/analysis/clustering.py` — vedi `clustering.md` per il mapping preciso dei parametri.
- **RSC (Zanola et al. 2026)**, uno dei paper di riferimento diretti di NEMESIS (`knowledge/nemesis/`), è la stessa famiglia di metodo con `base_method="spectral"` — non un algoritmo separato, come già documentato in `clustering.md`.
- **Davies-Bouldin, Silhouette** e gli altri indici interni già usati nel nostro tuning derivano direttamente da questa letteratura (Bicego cita Davies-Bouldin 1979 come riferimento originale).
- **Cluster tendency** è un gap identificato qui, non ancora coperto da nessun modulo `src/analysis/` — da valutare se aggiungere prima di investire ulteriormente nel tuning dei metodi di clustering.
- **Limite dei cluster che si toccano** (Fred & Jain) è direttamente rilevante per l'ipotesi clinica di NEMESIS: se il continuum lesionale non ha vere discontinuità, nessuno dei metodi discreti in `clustering.md` lo rivelerà come tale — un'assunzione da tenere esplicita quando si interpretano i risultati, non un limite tecnico dell'implementazione.
