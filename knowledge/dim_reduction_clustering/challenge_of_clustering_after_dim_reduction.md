# La sfida del clustering sopra una riduzione dimensionale

> Fonti (lette integralmente): Coenen & Pearce (Google PAIR), *"Understanding UMAP"*; documentazione ufficiale `umap-learn`, *"Using UMAP for Clustering"*; Geelen 2025 (blog Medium, non peer-reviewed), *"UMAP and Clustering: When Dimensionality Reduction Becomes Self-Affirming"*; discussione StackExchange/Cross Validated, *"Clustering on the output of t-SNE"* (165+ upvote sulla risposta principale, di Erich Schubert, coautore di HDBSCAN/OPTICS revisitati); più le sezioni rilevanti di de Bodt et al. 2025 (§5-6) e Wani 2025 (sezione "reliability triad") — vedi `dim_reduction_literature_survey.md`.
>
> Le prime tre fonti sono materiale "grigio" (blog, documentazione tecnica), non articoli peer-reviewed: qui sono trattate come testimonianza pratica/di comunità, non come letteratura scientifica primaria. La discussione StackExchange in particolare non è un punto di vista unico — raccoglie risposte in disaccordo tra loro da esperti del campo (Erich Schubert; "amoeba", moderatore molto citato su Cross Validated) — ed è proprio quel disaccordo il contenuto rilevante.

**In una frase**: NEMESIS clusterizza sistematicamente sopra un embedding, non sulla matrice voxel grezza — quindi è esposto in pieno alla domanda che questo documento tratta: *quando un cluster visto dopo t-SNE/UMAP corrisponde a una vera struttura nei dati, e quando è invece un artefatto del metodo di riduzione stesso?*

La motivazione pratica per cui si passa sempre da un embedding, non solo metodologica: la maggior parte dei metodi di clustering usati nel progetto (KMeans, Agglomerative-ward, GMM) assume cluster tondeggianti/di dispersione comparabile e diventa geometricamente inaffidabile su centinaia di migliaia di colonne (voxel grezzi) — da qui la scelta di girare quasi sempre su un embedding a 2-15 dimensioni. Questa scelta risolve un problema (affidabilità geometrica dell'algoritmo di clustering) ma ne apre un altro — proprio quello di questo documento: l'embedding stesso può introdurre distorsioni che il clustering a valle poi "conferma" senza che nulla lo segnali come tale.

## 1. Il problema di fondo

t-SNE e UMAP sono costruiti per preservare **vicinati locali** (chi è vicino a chi) — non densità, non distanze globali. Un algoritmo di clustering density-based o distance-based (K-Means, DBSCAN, HDBSCAN) applicato sopra quell'embedding lavora però esattamente su ciò che questi metodi *non* garantiscono (densità, distanza), non su ciò che garantiscono (vicinato locale).

Questo scollamento — tra cosa preserva davvero il metodo di riduzione e cosa assume l'algoritmo di clustering a valle — è la radice di ogni caveat che segue.

## 2. La tesi scettica: non clusterizzare sull'output (Schubert, Cross Validated)

Erich Schubert (la risposta più votata sulla discussione StackExchange) sostiene che clusterizzare dopo t-SNE/UMAP è rischioso perché **non si può mai sapere se i cluster trovati sono reali o artefatti del metodo**. Lo dimostra con tre esempi costruiti ad hoc:

1. **Una singola gaussiana multivariata** proiettata con t-SNE diventa visivamente un cerchio quasi uniforme: gli outlier, chiaramente periferici nello spazio originale, diventano indistinguibili dal resto.
2. **Due gaussiane sovrapposte** (250 punti a −2, 750 punti a +2): con perplexity troppo bassa (20) t-SNE inventa pattern che non esistono (DBSCAN a valle trova 4 cluster invece di 2). Con la perplexity "ottimale" per quel dataset (~80) il risultato è più pulito visivamente, ma **K-Means fallisce comunque** su un caso che un EM diretto sui dati originali risolverebbe facilmente: la densità — l'informazione che K-Means/EM userebbero — è stata "appiattita" dalla proiezione.
3. **Un'immagine "pesce" segmentata a colori**, proiettata con SNE/t-SNE, si **frammenta in pezzi disconnessi** anche partendo da un'inizializzazione "perfetta" (le coordinate originali): la repulsione più forte del kernel t-distribuito nello spazio di output vince sull'affinità gaussiana originale, rompendo letteralmente una struttura che nei dati di partenza era connessa.

**Conclusione di Schubert**: usare t-SNE/UMAP solo per *visualizzare*, non per clusterizzare a valle con metodi distance/density-based. Se serve un approccio basato su vicinato, meglio usare direttamente il grafo k-NN che t-SNE/UMAP costruiscono internamente, senza passare dalla proiezione 2D.

## 3. La controtesi empirica: a volte funziona meglio di ogni alternativa nota (amoeba, Cross Validated)

Una seconda risposta molto votata sulla stessa discussione (utente "amoeba") non nega i rischi di Schubert, ma li ridimensiona con un controesempio concreto: **MNIST** (70.000 cifre scritte a mano, 10 classi note).

- Nessun algoritmo di clustering diretto sui 784 pixel originali, né alcuna euristica nota per stimare il numero di cluster, riesce a recuperare in modo affidabile le 10 classi vere.
- **t-SNE seguito da HDBSCAN**, con parametri ben scelti (perplexity=50, "late exaggeration"), separa visivamente 10 cluster che corrispondono quasi esattamente alle etichette vere — un risultato che nessun metodo "senza proiezione" eguaglia su questo dataset.

amoeba estende l'osservazione a dati reali con ground truth ignoto (RNA-seq a singola cellula, Shekhar et al. 2016): un algoritmo di clustering sofisticato applicato direttamente ai dati produceva risultati che "sembravano sbagliati" sul plot t-SNE (un grande cluster centrale spezzato arbitrariamente in tanti pezzi) — e gli autori originali hanno finito per **fidarsi di più del pattern visto su t-SNE** che dei propri algoritmi di clustering diretto. Non perché t-SNE sia oggettivamente più affidabile, ma perché nessuna delle due fonti di verità è oggettivamente superiore in assenza di un ground truth indipendente.

**La sintesi** (esplicitata da un commento di Schubert in risposta ad amoeba): il vero disaccordo non è "t-SNE mente sempre" contro "t-SNE dice sempre la verità", ma *quanta fiducia riporre in un pattern visivo senza una verifica indipendente* — un giudizio caso per caso, non una regola generale.

## 4. La posizione "ufficiale": si può fare, con cautela esplicita (documentazione `umap-learn`)

La documentazione ufficiale di UMAP (stessi autori della libreria) tratta esplicitamente il caso d'uso "UMAP + HDBSCAN per clustering", con un esempio completo su MNIST — introdotto da un disclaimer diretto: *"this is somewhat controversial, and should be attempted with care"*, che rimanda proprio alla discussione StackExchange riassunta sopra.

Punti tecnici principali:

- **UMAP, come t-SNE, non preserva completamente la densità** e può creare **"false tears"** — fratture in un cluster che nei dati originali era unico. Stesso fenomeno del "pesce spezzato" di Schubert, riconosciuto dagli stessi autori del metodo.
- **Dimostrazione pratica su MNIST**: K-Means diretto sui 784 pixel raggiunge Adjusted Rand Index (ARI) 0.37. HDBSCAN dopo una PCA a 50 componenti raggiunge ARI 0.05, e clusterizza solo il 17% dei dati (il resto è "rumore" per la scarsità di densità in 50 dimensioni — la stessa *curse of dimensionality* che limita ogni metodo density-based). **HDBSCAN dopo UMAP** (10 componenti, `n_neighbors=30`, `min_dist=0.0` — parametri **diversi** da quelli usati per la sola visualizzazione) raggiunge invece ARI 0.92, clusterizzando il 99% dei dati.
- **Parametri per clustering ≠ parametri per visualizzazione**: `n_neighbors` più alto (meno struttura fine/rumorosa), `min_dist` vicino a 0 (punti impacchettati densamente, separazioni più nette tra cluster). Un embedding "bello da vedere" a 2D non è necessariamente quello giusto da dare in pasto a un clustering.
- **Non serve limitarsi a 2-3 componenti** se l'obiettivo è il clustering, non la visualizzazione — a differenza di t-SNE, il costo computazionale di UMAP resta contenuto anche a 10+ dimensioni.

## 5. La critica più recente: "self-affirming bias" (Geelen 2025, blog — non peer-reviewed)

Un post recente (novembre 2025, community Medium AImonks) formalizza empiricamente il rischio di cui sopra con un esperimento sistematico: dataset sintetici noti (blob gaussiani, classi sovrapposte, gaussiane anisotrope) proiettati con UMAP a diversi `min_dist`, poi clusterizzati con DBSCAN/OPTICS/Hierarchical Clustering (HCA) a diverse soglie.

**Conclusione** (coerente con Schubert, con enfasi diversa): un `min_dist` basso comprime artificialmente i punti in gruppi visivamente netti che il clustering "conferma" — ma la conferma è circolare, perché il clustering non fa altro che ritrovare la struttura che l'embedding ha già imposto per costruzione degli iperparametri, non una struttura indipendentemente presente nei dati.

Osservazione operativa, non solo teorica: DBSCAN e HCA restano relativamente stabili al variare della soglia (`eps`/distance threshold), mentre OPTICS degrada rapidamente — un dato pratico da tenere a mente nella scelta dell'algoritmo di clustering a valle, oltre che dei parametri UMAP.

Trattato qui come indicazione di community, non come risultato validato tra pari (nessuna citazione formale, metodologia non descritta in dettaglio nel post stesso) — ma la sua tesi centrale converge con l'avvertimento esplicito degli autori di UMAP (§4) e con Schubert (§2), quindi non è isolata.

## 6. Cosa dice la letteratura accademica sullo stesso problema

Le fonti sopra (blog/community) sono la voce pratica di un problema che la letteratura peer-reviewed formalizza in modo più cauto:

- **de Bodt et al. 2025** (`dim_reduction_literature_survey.md`) tratta il clustering su embedding a dimensionalità intermedia (5-10D) come pratica **emergente**, non consolidata: *"More work is needed to benchmark and to study the theoretical properties of such approaches"* (§6.1). Un giudizio quasi identico a quello della documentazione `umap-learn`, ma con un livello di certezza più basso. Nella lista delle best practice (§5, item 10) il paper è netto: *"Do not perform downstream analysis on 2D embeddings"* — un embedding 2D pensato per la visualizzazione introduce distorsioni che si propagano a qualunque analisi successiva; se serve clusterizzare va usato un embedding a dimensionalità più alta costruito *per quello scopo specifico*, non riciclato da un plot.
- **Wani 2025** inquadra lo stesso fenomeno nella sua "reliability triad" (instabilità, overfitting, generalizzazione): run diversi di t-SNE/UMAP sullo stesso dato, anche a parità di iperparametri, possono fondere o separare cluster diversamente per via della stocasticità dell'ottimizzazione. Un cluster "trovato" in un run e "sparito" nel successivo non è un errore del clustering a valle — è l'instabilità dell'embedding che lo precede.
- **Sperber et al. 2023** (citato in `knowledge/nemesis/Paper_Summaries.md`, discussione di Facchini et al. 2023) sollevano una critica concettualmente parallela per la bassa dimensionalità dei *sintomi* post-ictus, che potrebbe essere un artefatto della sola anatomia lesionale piuttosto che una vera struttura comportamentale. Stesso schema logico del problema qui discusso — una bassa dimensionalità osservata può riflettere il metodo, non il fenomeno — applicato a un layer diverso della pipeline NEMESIS.

## 7. Implicazioni pratiche per NEMESIS

1. **Mai un solo embedding/run**: multi-seed, multi-iperparametro, come già raccomandato in `dim_reduction_tuning_guide.md`/`dim_reduction_literature_survey.md` — non solo per stabilità numerica ma proprio perché un cluster che appare a un solo `n_neighbors`/`perplexity` e sparisce agli altri è precisamente il tipo di artefatto descritto da Schubert e da Geelen.
2. **Parametri di clustering ≠ parametri di visualizzazione**: se l'obiettivo di un run UMAP è dare input a `clustering.py` (non produrre uno scatter da leggere a occhio), i parametri (`n_neighbors` più alto, `min_dist` più basso, `n_components` >2) vanno scelti per quello scopo — coerente con quanto già impostato per il tuning nel progetto, ma da tenere esplicito ogni volta che si interpretano i risultati.
3. **Nessun cluster va accettato solo perché "si vede bene"**: la validazione (indici interni/esterni, `clustering_tuning_guide.md`) resta necessaria ma non sufficiente — un `min_dist` basso può produrre indici di validazione ottimi (Silhouette alto) proprio perché l'embedding ha reso i cluster artificialmente compatti, lo stesso meccanismo circolare descritto da Geelen.
4. **Un pattern anatomico-clinico plausibile è la miglior prova indipendente disponibile** — analogo a come amoeba si fida di più di un pattern t-SNE quando corrisponde a etichette note (MNIST) o è confermato da un metodo indipendente (persistence diagram, citato da un'altra risposta nella stessa discussione): per NEMESIS, un cluster che corrisponde a un territorio vascolare noto o a un dominio comportamentale coerente è una conferma più forte di un silhouette score alto da solo.
5. **La domanda "questa è struttura reale o un artefatto del metodo?" non ha una risposta metodologica definitiva** — nessuna delle fonti qui riassunte (accademiche o di community) offre un test decisivo. È una lettura clinica/di dominio, non un numero da calcolare — coerente con l'approccio "clustering + interpretazione clinica" già proposto in `management/notes/proposal.md` e nei meeting notes del progetto.
