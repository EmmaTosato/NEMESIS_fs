# Riduzione dimensionale — cosa fanno questi metodi

> **Implementazione:** `src/analysis/reduction.py`, `config/registry/params_reduction.json`.
> **Meccanica dettagliata UMAP/t-SNE** (letteratura, come interpretarli): `docs/knowledge/umap_tsne_guide.md`.
> **Come leggere gli indici di tuning** (trustworthiness, varianza spiegata): `docs/knowledge/dim_reduction_tuning_guide.md`.
> **Rassegna più ampia di metodi** (anche non usati nel progetto): `docs/knowledge/dimensionality_reduction_methods.md`.
> **Clustering**: `docs/knowledge/clustering.md`.

Guida in linguaggio semplice a cosa fa ciascun metodo di riduzione dimensionale usato nel progetto — non un manuale di ML, solo il minimo per capire cosa controlla un iperparametro in config e con qualche criterio per scegliere tra i metodi.

## Il problema

Ogni soggetto ha centinaia di migliaia di voxel (o poche centinaia di parcelle, se parcellato) come feature — troppe per essere visualizzate o clusterizzate direttamente. La riduzione dimensionale comprime ogni soggetto in poche coordinate (2-30, tipicamente) che catturano il più possibile ciò che rende i soggetti diversi tra loro — o per visualizzarli su un plot 2D, o per dare un input più piccolo e meno rumoroso al clustering.

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
  - `metric` — `euclidean` (default) è appunto dominato dal **volume**; `jaccard`/`dice` normalizzano invece per la dimensione della lesione di ciascun soggetto, così due lesioni piccole nello stesso posto e due lesioni grandi nello stesso posto risultano ugualmente vicine. Sweeppato.
  - `regress_out_volume` — stesso meccanismo spiegato sotto per UMAP (toglie l'effetto del volume dall'embedding già calcolato, incompatibile con `metric: jaccard/dice`). Sweeppato.

(`metric`/`regress_out_volume` sono organizzati come "parametri annidati" nel tuning — una sottocartella per valore invece di una griglia unica con `perplexity`; vedi `docs/knowledge/dim_reduction_tuning_guide.md`.)

## UMAP

Anch'esso non lineare e basato sui vicini, ma con un fondamento matematico diverso da t-SNE (topologia) che tende a preservare un po' meglio la struttura *globale* — anche se non bisogna fidarsene troppo (vedi sotto). Generalmente più veloce di t-SNE e scala meglio a migliaia di soggetti.

- Parametri chiave:
  - `n_neighbors` — analogo alla `perplexity` di t-SNE: quanti punti vicini definiscono il vicinato locale di un soggetto.
  - `min_dist` — quanto i punti possono impacchettarsi nello spazio di output. Basso = cluster più compatti e visivamente separati; alto = distribuzione più uniforme, utile per vedere gradienti continui invece di gruppi discreti.
  - `metric` — stesso discorso di t-SNE sopra (euclidea dominata dal volume, jaccard/dice normalizzano per volume).
- Stocastico: fissare `random_state`.
- A differenza di t-SNE, si usa correntemente anche a più dimensioni (5-15) come step di preprocessing prima del clustering, non solo per la visualizzazione a 2D.
- **La presunta superiorità di UMAP nel preservare la struttura globale è ridimensionata in letteratura**: gran parte del vantaggio percepito viene dalla sua inizializzazione di default (basata su spectral embedding), non dalla funzione di costo in sé (Kobak & Linderman 2021) — vedi `docs/knowledge/umap_tsne_guide.md` per i dettagli.
- `regress_out_volume` (opzione di pipeline, non un parametro di UMAP): correzione opzionale applicata *dopo* aver calcolato l'embedding, che toglie l'effetto lineare del volume lesionale da ogni sua dimensione. **Incompatibile con `metric: jaccard`/`dice`** — quelle metriche già normalizzano per il volume di ciascun soggetto a livello di distanza; farlo anche qui toglierebbe segnale topografico vero, non solo un confondimento.

## PCA con rotazione varimax

Stessa base di PCA (autoscomposizione della matrice di covarianza), ma le componenti vengono poi ruotate (rotazione **varimax**) prima di calcolare i punteggi via regressione multipla — è esattamente la metodologia di Thiebaut de Schotten et al. 2020.

- **Perché ruotare**: le componenti di una PCA normale sono matematicamente comode ma poco interpretabili — una componente grezza spesso pesa un po' su quasi ogni parcella. La rotazione varimax rende ogni componente il più possibile "poche parcelle pesano tanto, il resto quasi zero" — più facile da leggere come "questa componente è sostanzialmente il territorio MCA sinistro".
- Richiede `n_components >= 2` — la rotazione avviene *tra* componenti, quindi serve almeno una coppia da ruotare.
- Deterministico, come PCA normale — nessun `random_state`.
- **Non ancora raggiungibile da config oggi**: implementato e testato nel codice, ma `params_reduction.json` non ha una entry per questo metodo — va aggiunta prima di poterlo usare dalla CLI.

## PaCMAP

Altro metodo non lineare basato sui vicini, pensato dai suoi autori per bilanciare meglio struttura locale e globale rispetto a t-SNE/UMAP separatamente, pesando esplicitamente durante l'ottimizzazione tre tipi di coppie di punti (vicine, medio-vicine, lontane) invece delle sole coppie vicine.

- Parametri chiave: `n_neighbors` (stesso ruolo di UMAP), `MN_ratio`/`FP_ratio` — controllano quante coppie medio-vicine/lontane campionare rispetto alle vicine (un `MN_ratio` più alto spinge verso più struttura globale preservata).
- Stocastico: fissare `random_state`.
- Serve un numero di soggetti sufficiente perché `n_neighbors` e le coppie derivate abbiano senso — su coorti molto piccole la proiezione non è affidabile.

## Come scegliere tra i metodi

**PCA per prima, sempre** — è il test lineare economico e interpretabile che dice quanto della struttura è già spiegabile linearmente, prima di passare a qualcosa di non lineare. Se i soggetti non si separano bene con PCA ma si sospetta un raggruppamento reale, il passo successivo è t-SNE/UMAP; **UMAP è la scelta pratica di default** alla scala di NEMESIS (migliaia di soggetti) ed è anche l'input tipico prima del clustering, non solo per visualizzare. **PCA-varimax** è l'opzione da usare quando serve leggere il *significato* delle componenti (quali parcelle/voxel contribuiscono), non solo separare i soggetti — riproduce esattamente la metodologia del paper di riferimento. **PaCMAP** è un'alternativa da provare accanto a UMAP quando il suo bilanciamento locale/globale non convince su un run specifico — non un default, dato che UMAP è già lo standard qui.
