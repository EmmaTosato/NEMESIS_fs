# Riduzione dimensionale — cosa fanno questi metodi

> **Implementazione:** `src/analysis/reduction.py`, `config/registry/params_reduction.json`.
> **Meccanica dettagliata UMAP/t-SNE** (letteratura, come interpretarli): `docs/knowledge/umap_tsne_guide.md`.
> **Come leggere gli indici di tuning** (trustworthiness, varianza spiegata): `docs/knowledge/dim_reduction_tuning_guide.md`.
> **Rassegna più ampia di metodi** (anche non usati nel progetto): `docs/knowledge/dim_reduction_literature_survey.md`.
> **Clustering**: `docs/knowledge/clustering.md`.

Guida in linguaggio semplice a cosa fa ciascun metodo di riduzione dimensionale usato nel progetto — non un manuale di ML, solo il minimo per capire cosa controlla un iperparametro in config e con qualche criterio per scegliere tra i metodi.

## Il problema

Ogni soggetto ha centinaia di migliaia di voxel (o poche centinaia di parcelle, se parcellato) come feature — troppe per essere visualizzate o clusterizzate direttamente. La riduzione dimensionale comprime ogni soggetto in un numero di coordinate che catturano il più possibile ciò che rende i soggetti diversi tra loro — o per visualizzarli su un plot 2D, o per dare un input più piccolo e meno rumoroso al clustering. **Quante coordinate tenere non ha un default universale**: dipende dal metodo e dal caso specifico (vedi i criteri per ciascun metodo sotto) — nessun numero "tipico" è assunto qui in generale.

## PCA

Trova le direzioni (combinazioni lineari delle feature originali) lungo cui i soggetti variano di più, e proietta su quelle.

- Puramente lineare — l'unico metodo qui i cui componenti si possono reinterpretare sui voxel/parcelle originali (es. "la componente 1 pesa soprattutto sul territorio dell'arteria cerebrale media sinistra").
- Veloce, deterministico — nessuna casualità, stesso input dà sempre lo stesso output.
- Assume che le differenze reali tra soggetti siano lineari — se non lo sono (es. due topografie di lesione distinte che non differiscono per una semplice somma di voxel), PCA può appiattirle insieme invece di separarle.
- Parametro chiave: `n_components` — quante direzioni tenere. Non c'è un valore "corretto"; si sceglie guardando la varianza cumulativa spiegata (Thiebaut de Schotten et al. 2020 usa una soglia del 90%), oppure si fissa a 2 solo per visualizzare.

## t-SNE

Non lineare. Cerca di posizionare i soggetti su una mappa 2D (o 3D) in modo che chi era vicino nello spazio originale resti vicino sulla mappa — preserva solo la struttura *locale*, non le distanze globali.

- Spesso produce cluster visivamente più netti/separati di PCA/UMAP sugli stessi dati.
- **Le distanze *tra* cluster nel plot non sono affidabili**, né le dimensioni dei cluster — solo "questi punti sono vicini tra loro" lo è. Il fraintendimento più comune di t-SNE: non dedurre quanto due cluster siano simili da quanto appaiono vicini/lontani nel disegno.
- Stocastico: fissare `random_state` per la riproducibilità.
Parametri, divisi per motivo — **non tutti riguardano la replica del paper**:

- **Dal paper di riferimento (Thiebaut de Schotten et al. 2020)**:
  - `early_exaggeration`, `learning_rate`, `max_iter` — parametri di ottimizzazione, **fissati** ai valori del paper, mai sweeppati.
  - `perplexity` — grosso modo, quanti vicini contano per punto (tipico 5-50, deve essere minore del numero di soggetti; troppo basso frammenta cluster reali in rumore, troppo alto fonde cluster distinti). **Sweeppato**, ma proprio perché è l'unico parametro che anche il materiale supplementare del paper fa variare — qui sweeppare *replica* il paper, non se ne discosta.
- **Aggiunte proprie di NEMESIS, indipendenti dal paper** (introdotte in sessioni successive per un problema che il paper non affronta — su maschere di lesione binarie, la metrica euclidea di default è dominata dal volume della lesione più che dalla sua forma):
  - `metric` — `euclidean` (default) è dominato dal **volume** in modo pesante e illimitato (la differenza di volume tra due lesioni può dominare la distanza euclidea senza alcun limite superiore). `jaccard`/`dice` **attenuano ma non eliminano** questa dipendenza — **correzione (2026-08, verificata in letteratura)**: non è vero che rendono "ugualmente vicine" due lesioni di volume diverso nella stessa zona. Per costruzione, `Dice(A,B) ≤ 2·min(|A|,|B|)/(|A|+|B|)` — una lesione piccola e una grande nello stesso identico posto restano comunque a distanza significativa, proprio a causa della differenza di volume, non della posizione. È un bias noto e documentato (da cui varianti come nDSC, pensate apposta per correggerlo), non un'invenzione di questa nota. jaccard/dice restano comunque preferibili all'euclidea grezza (che non ha alcun limite superiore al bias-volume), ma vanno letti come "meno peggio", non come "risolto". Sweeppato.

(`metric` è organizzato come "parametro annidato" nel tuning — una sottocartella per valore invece di una griglia unica con `perplexity`; vedi `docs/knowledge/dim_reduction_tuning_guide.md`.)

## UMAP

Anch'esso non lineare e basato sui vicini, ma con un fondamento matematico diverso da t-SNE (topologia) che tende a preservare un po' meglio la struttura *globale* — anche se non bisogna fidarsene troppo (vedi sotto). Generalmente più veloce di t-SNE e scala meglio a migliaia di soggetti.

- Parametri chiave:
  - `n_neighbors` — analogo alla `perplexity` di t-SNE: quanti punti vicini definiscono il vicinato locale di un soggetto.
  - `min_dist` — quanto i punti possono impacchettarsi nello spazio di output. Basso = cluster più compatti e visivamente separati; alto = distribuzione più uniforme, utile per vedere gradienti continui invece di gruppi discreti.
  - `metric` — stesso discorso di t-SNE sopra: euclidea dominata pesantemente dal volume, jaccard/dice attenuano ma non eliminano quella dipendenza (vedi la correzione nella sezione t-SNE).
- Stocastico: fissare `random_state`.
- A differenza di t-SNE, può essere usato anche a più dimensioni come step di preprocessing prima del clustering, non solo per la visualizzazione a 2D — **quante, e con quali rischi, vedi la sezione dedicata subito sotto**.
- **La presunta superiorità di UMAP nel preservare la struttura globale è ridimensionata in letteratura**: gran parte del vantaggio percepito viene dalla sua inizializzazione di default (basata su spectral embedding), non dalla funzione di costo in sé (Kobak & Linderman 2021) — vedi `docs/knowledge/umap_tsne_guide.md` per i dettagli.

### UMAP e clustering: quante componenti?

**Nessun numero fisso** — verificato su 4 fonti (2026-08 review), nessuna prescrive un default valido in generale:

- **Talozzi et al. 2023** (paper di riferimento diretto per NEMESIS Task 2): usa UMAP a **2D**, esplicitamente. Definisce dimensionalità più alta come non ancora esplorata ("future research").
- **de Bodt, Diaz-Papkovich, Kobak et al. 2025** (arXiv:2508.15929, review — McInnes tra gli autori): principio generale a favore di non clusterizzare su un embedding pensato solo per la viz 2D, ma la cifra 5-10D che riportano è presentata come pratica **emergente**, non consolidata ("more work is needed to validate this clustering approach"). Su cosa rappresentino davvero le componenti oltre la 2ª/3ª: **problema esplicitamente aperto** (§6.1) — solo un rimando concettuale, mai reso operativo, alla "dimensionalità intrinseca" dei dati (Levina & Bickel 2004; Camastra & Staiano 2016).
- **Documentazione ufficiale `umap-learn`** (stessi autori della libreria): sì, si può ridurre a più di 2D per il clustering, ma **"in general you should explore different embedding dimension options"** — nessun default. Consiglia anche di cambiare `n_neighbors`/`min_dist` per un run orientato al clustering rispetto a uno orientato alla viz (non solo `n_components`). **Avvertimento esplicito degli stessi autori**: *"this is somewhat controversial, and should be attempted with care"* — UMAP non preserva bene la densità, può creare *"false tears"* (cluster più frammentati di quanto siano nei dati reali); raccomandano di validare sempre i cluster ottenuti.
- Una critica indipendente (blog, non peer-reviewed, nessuna citazione — quindi non usabile come fonte a sé) solleva la stessa preoccupazione con più forza ("self-affirming bias": l'embedding crea la struttura che poi il clustering "conferma") — non aggiunge autorità, ma la sua tesi centrale coincide con l'avvertimento sopra, che viene dagli stessi autori di UMAP.


## PCA con rotazione varimax

Stessa base di PCA (autoscomposizione della matrice di covarianza), ma le componenti vengono poi ruotate (rotazione **varimax**) prima di calcolare i punteggi via regressione multipla — è esattamente la metodologia di Thiebaut de Schotten et al. 2020.

- **Perché ruotare**: le componenti di una PCA normale sono matematicamente comode ma poco interpretabili — una componente grezza spesso pesa un po' su quasi ogni parcella. La rotazione varimax rende ogni componente il più possibile "poche parcelle pesano tanto, il resto quasi zero" — più facile da leggere come "questa componente è sostanzialmente il territorio MCA sinistro".
- Richiede `n_components >= 2` — la rotazione avviene *tra* componenti, quindi serve almeno una coppia da ruotare.
- Deterministico, come PCA normale — nessun `random_state`.
- **Non ancora raggiungibile da config oggi**: implementato e testato nel codice, ma `params_reduction.json` non ha una entry per questo metodo — va aggiunta prima di poterlo usare dalla CLI.
- **Bug corretto (2026-08)**: la rotazione varimax va applicata ai *loadings* (autovettore × radice dell'autovalore), non agli autovettori grezzi di `PCA.components_` — il codice faceva quest'ultimo, il che pesava ogni componente allo stesso modo indipendentemente da quanta varianza spiegasse davvero, e degradava silenziosamente il passo di "regressione multipla" successivo in una semplice proiezione. Corretto in `src/analysis/reduction.py::pca_varimax_embed` prima che il metodo fosse mai raggiungibile in produzione — nessun risultato esistente è quindi affetto.

## PaCMAP

Altro metodo non lineare basato sui vicini, pensato dai suoi autori per bilanciare meglio struttura locale e globale rispetto a t-SNE/UMAP separatamente, pesando esplicitamente durante l'ottimizzazione tre tipi di coppie di punti (vicine, medio-vicine, lontane) invece delle sole coppie vicine.

- Parametri chiave: `n_neighbors` (stesso ruolo di UMAP), `MN_ratio`/`FP_ratio` — controllano quante coppie medio-vicine/lontane campionare rispetto alle vicine (un `MN_ratio` più alto spinge verso più struttura globale preservata).
- Stocastico: fissare `random_state`.
- Serve un numero di soggetti sufficiente perché `n_neighbors` e le coppie derivate abbiano senso — su coorti molto piccole la proiezione non è affidabile.
- **`apply_pca`** (reso esplicito in config, 2026-08 — prima lasciato al default della libreria): quando `true` (default di PaCMAP stesso), prima di costruire il grafo dei vicini viene applicata una PCA di preprocessing a 100 componenti — un passaggio non banale su dati binari ad alta dimensionalità come i voxel di lesione, mai stato visibile in `params_reduction.json` finché non è stato aggiunto qui esplicitamente (`code_standards.md` §5: nessun iperparametro implicito). Attenzione se si valuta `trustworthiness` sull'embedding: quest'ultima confronta i vicinati dell'embedding con quelli di `X` grezza, non con quelli dello spazio PCA-100 su cui PaCMAP ha effettivamente costruito il grafo — un disallineamento della stessa famiglia già corretto per UMAP/t-SNE (vedi sopra), non ancora affrontato per PaCMAP.

## Come scegliere tra i metodi

**PCA per prima, sempre** — è il test lineare economico e interpretabile che dice quanto della struttura è già spiegabile linearmente, prima di passare a qualcosa di non lineare. Se i soggetti non si separano bene con PCA ma si sospetta un raggruppamento reale, il passo successivo è t-SNE/UMAP; **UMAP è la scelta pratica di default** alla scala di NEMESIS (migliaia di soggetti) ed è anche l'input tipico prima del clustering, non solo per visualizzare. **PCA-varimax** è l'opzione da usare quando serve leggere il *significato* delle componenti (quali parcelle/voxel contribuiscono), non solo separare i soggetti — riproduce esattamente la metodologia del paper di riferimento. **PaCMAP** è un'alternativa da provare accanto a UMAP quando il suo bilanciamento locale/globale non convince su un run specifico — non un default, dato che UMAP è già lo standard qui.
