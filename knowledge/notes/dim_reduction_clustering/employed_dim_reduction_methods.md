# PCA, t-SNE e UMAP: i metodi di riduzione dimensionale impiegati in NEMESIS

> Fonti (lette integralmente): van der Maaten & Hinton 2008, *"Visualizing Data using t-SNE"* ([paper originale, JMLR](https://jmlr.org/papers/volume9/vandermaaten08a/vandermaaten08a.pdf)); McInnes, Healy & Melville 2018, *"UMAP: Uniform Manifold Approximation and Projection"*; [documentazione ufficiale UMAP, "How UMAP Works"](https://umap-learn.readthedocs.io/en/latest/how_umap_works.html); Wattenberg, Viégas & Johnson 2016, *"How to Use t-SNE Effectively"* (Distill); Kobak & Linderman 2021, *"Initialization is critical for preserving global data structure in both t-SNE and UMAP"* (Nature Biotechnology).
>
> Meccanica dei due metodi non lineari che NEMESIS usa effettivamente (`umap`/`tsne` in `REDUCTION_METHODS`, `src/analysis/reduction.py`), più, in fondo, la PCA con la rotazione varimax (il metodo lineare) — non coperta in questo dettaglio dalla rassegna più ampia in `dim_reduction_literature_survey.md` (tassonomia completa dei metodi di riduzione dimensionale, PCA/spettrali/neurali inclusi), a cui questo file si affianca.

**In breve**:
- **t-SNE, in una frase**: converte le distanze tra i punti in "probabilità di essere vicini" (gaussiane nello spazio originale, t di Student nello spazio ridotto) e sposta i punti nello spazio a bassa dimensione finché le due distribuzioni di probabilità non si assomigliano il più possibile (minimizzando la divergenza KL) — il risultato tipico sono cluster ben separati, pensati per la visualizzazione 2D/3D. Parametro chiave: `perplexity` (grosso modo quanti vicini "contano" per punto, tipicamente 5-50).
- **UMAP, in una frase**: costruisce un grafo pesato dei k-vicini-più-prossimi di ogni punto (i pesi sono probabilità che un collegamento esista, un "fuzzy simplicial set"), poi ottimizza le posizioni nello spazio a bassa dimensione minimizzando la cross-entropia tra questo grafo e il grafo equivalente nell'embedding — punti collegati si attraggono, tutti gli altri si respingono, come in un layout di grafo force-directed. Parametri chiave: `n_neighbors` (dimensione del vicinato considerato, default 15 — valori piccoli catturano dettaglio locale, valori grandi struttura più globale) e `min_dist` (quanto vicini possono stare i punti nell'embedding finale).

**t-SNE (van der Maaten & Hinton 2008)**: converte le distanze in probabilità di essere "vicini" — gaussiane nello spazio originale, t-distribuzione (code pesanti) nello spazio a bassa dimensione. La t-distribuzione è la scelta chiave: risolve il *crowding problem* (in poche dimensioni non c'è spazio sufficiente per rappresentare fedelmente tutte le distanze medie di uno spazio ad alta dimensionalità; le code pesanti permettono a punti moderatamente lontani di stare più distanti nella mappa senza penalità eccessiva). Ottimizza minimizzando la divergenza KL tra le due distribuzioni. Parametro chiave: `perplexity`, grosso modo "quanti vicini contano" per punto — l'autore stesso raccomanda nel paper di provarne più di uno, mai fidarsi di un valore singolo.

**UMAP (McInnes, Healy & Melville 2018)**: fondamento matematico diverso — teoria dei fuzzy simplicial set (topologia), non probabilità gaussiane. Costruisce un grafo pesato dei k-vicini-più-prossimi nello spazio originale, poi ottimizza un layout a bassa dimensione minimizzando una cross-entropia tra il grafo originale e quello nell'embedding (invece della KL-divergenza di t-SNE). Il paper originale sostiene che questo preservi meglio la struttura *globale* rispetto a t-SNE.

**Come interpretare entrambi (Wattenberg, Viégas & Johnson 2016, *"How to Use t-SNE Effectively"*, Distill — riferimento classico, esteso in pratica anche a UMAP)**:
- Le dimensioni dei cluster nel plot **non sono significative** — t-SNE (e UMAP) espande cluster densi e comprime quelli radi, la dimensione visiva non riflette la dispersione reale.
- Le distanze *tra* cluster **non sono significative** — due cluster disegnati vicini non sono necessariamente più simili di due disegnati lontani.
- Perplexity/`n_neighbors` multipli danno letture diverse dello stesso dato — nessun valore singolo è "quello vero"; un pattern che appare solo a un valore specifico è meno affidabile di uno stabile su un range.
- Entrambi i metodi sono stocastici: run diversi (senza seed fissato) possono produrre layout ruotati/specchiati o con cluster in posizioni diverse — la topologia locale (chi è vicino a chi) è ciò che deve restare stabile, non l'orientamento.

**La presunta superiorità di UMAP nel preservare la struttura globale è stata ridimensionata**: Kobak & Linderman 2021 mostrano che gran parte del vantaggio percepito di UMAP deriva dalla sua **inizializzazione di default basata su spectral embedding** (non casuale), non dalla funzione di costo in sé — inizializzando t-SNE allo stesso modo, la differenza si riduce molto. Implicazione pratica: l'inizializzazione (`init`) conta quanto l'algoritmo stesso; non va assunta "struttura globale affidabile" solo perché è UMAP.

**Jaccard e Dice, in breve**: per due maschere binarie *A* e *B* (gli insiemi dei loro voxel di lesione) confrontano i voxel in comune con i voxel totali, non la distanza geometrica tra i punti. Jaccard = |A ∩ B| / |A ∪ B| (in comune su unione); Dice = 2 |A ∩ B| / (|A| + |B|) (il doppio dei voxel in comune su somma dei volumi). Valgono 1 per due maschere identiche e 0 se non hanno nessun voxel in comune; la distanza usata è 1 meno il valore. Due lesioni che non si sovrappongono sono quindi a distanza massima (1) per quanto siano vicine nello spazio: è per questo che sulle lesioni la quota di coppie a distanza esattamente 1 è alta (84% con Dice sulla matrice grezza, vedi `docs/guides/evaluation.md`).

**Il bias-volume di jaccard/dice su maschere binarie (correzione 2026-08, verificata in letteratura)**: la metrica euclidea di default è dominata dal **volume** di una maschera di lesione in modo pesante e illimitato (la differenza di volume tra due lesioni può dominare la distanza euclidea senza alcun limite superiore). `jaccard`/`dice` attenuano ma **non eliminano** questa dipendenza — non è vero che rendono "ugualmente vicine" due lesioni di volume diverso nella stessa zona. Per costruzione, `Dice(A,B) ≤ 2·min(|A|,|B|)/(|A|+|B|)`: una lesione piccola e una grande nello stesso identico posto restano comunque a distanza significativa, proprio a causa della differenza di volume, non della posizione. È un bias noto e documentato in letteratura (da cui varianti come nDSC, pensate apposta per correggerlo), non un'osservazione isolata di NEMESIS — jaccard/dice restano comunque preferibili all'euclidea grezza (che non ha alcun limite superiore al bias-volume), ma vanno letti come "meno peggio", non come "risolto".

## Scegliere `n_neighbors` e `min_dist` di UMAP guardando le griglie

**Cosa fanno** (Coenen & Pearce, *Understanding UMAP*, Google PAIR — `websites/Understanding_UMAP.html`):

- **`n_neighbors`** è "il parametro più importante": il numero di vicini approssimati con cui si costruisce il grafo iniziale, e quindi l'equilibrio tra struttura locale e globale. Con valori bassi UMAP si concentra sul locale e la nozione di struttura globale "è quasi completamente persa"; con valori alti rappresenta il quadro d'insieme perdendo il dettaglio fine.
- **`min_dist`** è la distanza minima tra due punti nello spazio ridotto: valori bassi danno embedding strettamente impacchettati, valori alti punti più sparsi. Agisce solo sul layout: il grafo dei vicini dipende da `n_neighbors` e `metric`, non da `min_dist` (`lessons_learned.md` #16).
- Gli stessi autori traggono due conseguenze: "hyperparameters really matter" e vanno provati più valori, perché l'algoritmo è stocastico e "you need more than one plot".

**Per clustering, non per visualizzare** (documentazione `umap-learn`, *Using UMAP for Clustering* — `websites/Using_UMAP_for_Clustering.html`): vanno scelti `n_neighbors` più alto, perché i valori piccoli sono "more prone to producing fine grained cluster structure that may be more a result of patterns of noise in the data than actual clusters", e `min_dist` molto basso (l'esempio usa 0), perché si vuole densità e separazioni pulite.

**Il rischio del `min_dist` basso** (Geelen 2025, blog non peer-reviewed — `challenge_of_clustering_after_dim_reduction.md` §5): impacchettare i punti rende i gruppi visivamente netti per costruzione, e il clustering a valle li "conferma" in modo circolare.

### Come si leggono le griglie

Le indicazioni delle fonti diventano un metodo di lettura dei plot dello sweep. Ogni tassello viene dalle fonti sopra (Coenen & Pearce, `umap-learn`, Geelen, Wattenberg et al. 2016); la loro composizione in un criterio di scelta è nostra.

- **Come è fatta una griglia.** Una griglia per foglia (`metric × n_components`): righe = `n_neighbors`, colonne = `min_dist`. Nei plot con HDBSCAN ogni titolo riporta numero di cluster `k` e quota di rumore; il grigio è rumore e i colori sono indipendenti tra riquadri (lo stesso colore in due riquadri non indica lo stesso gruppo). Con `n_components > 2` il disegno è il fit gemello a 2D, mentre HDBSCAN lavora nello spazio completo: colori che si sovrappongono nel disegno non sono un difetto.
- **Scendendo lungo una colonna (`n_neighbors` sale).** Da molte isole piccole a pochi blob grandi: un blob che a `n_neighbors` basso è spezzato in più pezzi diventa un unico gruppo. È il passaggio dal locale al globale di Coenen & Pearce. La frammentazione che sparisce al crescere di `n_neighbors` è quella che `umap-learn` avverte poter essere rumore, non sottostruttura robusta.
- **Lungo una riga (`min_dist` sale).** Da isole compatte separate da spazio vuoto a blob allargati che si toccano: i vuoti si chiudono, HDBSCAN non riesce più a separare i gruppi e la quota di rumore sale. Le colonne a `min_dist` alto si scartano.
- **Cosa si cerca: un plateau.** Un blocco contiguo di riquadri con lo stesso disegno e gli stessi `k` e rumore. Il numero di cluster di HDBSCAN è una sonda di stabilità, non un punteggio da massimizzare: serve a vedere dove il disegno resta uguale, non quale combinazione "trova più cluster".
- **Si guardano i vicini del riquadro scelto, non solo il riquadro.** Se un riquadro adiacente salta (per esempio `k` da 8 a 18 e rumore da 1% a 14%), quel riquadro è sul bordo di un'instabilità e non dentro il plateau. Il bordo della griglia (`min_dist` = 0, `n_neighbors` massimo) non è invece una cella che salta: lì non c'è un vicino che smentisce.
- **Pulito non vuol dire affidabile.** I riquadri a `min_dist` ≈ 0 sembrano più netti per costruzione (Geelen). Un `min_dist` basso è legittimo solo se le colonne vicine mostrano gli stessi gruppi: in quel caso la struttura non è prodotta dal parametro.
- **Più plateau con `k` diverso.** A `n_neighbors` diversi possono esistere due livelli stabili (uno fine, uno grosso): sono due granularità, non un errore. La scelta dipende da ciò che si vuole studiare; se si vogliono confrontare più `n_components`, ha senso tenere lo stesso livello.
- **Nessun plateau.** Se il disegno cambia a ogni riquadro e il rumore è alto ovunque, nessuna combinazione è robusta: non si forza una scelta dal `k`.
- **Cosa non si legge nei riquadri.** Le dimensioni dei cluster e le distanze tra cluster non sono significative (Coenen & Pearce, Wattenberg et al.). Prima di interpretare un gruppo si guardano le griglie colorate per metadati (lato, dataset, volume): una struttura netta che coincide con una variabile di confondimento non è un pattern.

## PCA e rotazione varimax

> Il metodo lineare tra quelli impiegati (`pca` in `REDUCTION_METHODS`, `src/analysis/reduction.py`, con la rotazione come parametro), a differenza di t-SNE e UMAP sopra. Il calcolo per matrici troppo larghe per `sklearn` (disconnettoma voxelwise) è in [`docs/dev/covariance_pca.md`](../../../docs/dev/covariance_pca.md); il notebook che lo usa è in [`docs/guides/exploration.md`](../../../docs/guides/exploration.md) (`thiebaut_2020_replication`).

### La PCA

#### L'idea

Una matrice con *n* soggetti e *p* variabili (qui: voxel) è difficile da guardare. La PCA (*Principal Component Analysis*) trova nuovi assi, le **componenti**, lungo cui i soggetti differiscono di più:

- la prima componente è la direzione di massima variabilità;
- la seconda è la direzione di massima variabilità tra quelle perpendicolari alla prima;
- e così via.

Tenendo le prime *k* componenti si riassume ogni soggetto con *k* numeri invece di *p*, perdendo il meno possibile della variabilità.

#### I passi

1. **Centrare.** Si toglie a ogni variabile la sua media sui soggetti: `Xc = X - media`.
2. **Covarianza.** Si calcola la matrice `C = Xcᵀ Xc / (n-1)`, di dimensione *p* × *p*. Il suo elemento (i, j) dice quanto i voxel *i* e *j* variano insieme tra i soggetti.
3. **Autovettori e autovalori di C.** Ogni autovettore è una componente, ogni autovalore è la varianza che quella componente cattura. Si ordinano dal più grande.

Dai risultati si leggono quattro cose:

| Oggetto | Cos'è | Dimensione |
|---|---|---|
| **Autovalore** | varianza catturata dalla componente | uno per componente |
| **Quota di varianza spiegata** | autovalore / somma di tutti gli autovalori | uno per componente |
| **Pesi** (*loadings*) | quanto ogni variabile contribuisce alla componente (l'autovettore, eventualmente moltiplicato per √autovalore) | *p* × *k* |
| **Punteggi** (*scores*) | la posizione di ogni soggetto sulla componente | *n* × *k* |

**Pesi e punteggi, in parole.** I pesi sono un numero per voxel e per componente, e sono **gli stessi per tutti i soggetti**: descrivono la componente. Il punteggio è un numero per soggetto e per componente: la somma dei voxel di quel soggetto, pesati con i pesi della componente.

> punteggio(soggetto *i*, componente *j*) = peso₁ⱼ · voxel₁(*i*) + peso₂ⱼ · voxel₂(*i*) + … + peso_pⱼ · voxel_p(*i*)

Questa somma è la **combinazione lineare delle variabili originali**: i pesi sono i coefficienti, il punteggio è il risultato. Su tutti i soggetti insieme, la componente è una nuova colonna lunga *n*, somma pesata delle *p* colonne dei voxel. Riportati sulla griglia del cervello, i pesi di una componente formano la sua mappa spaziale.

Esempio con 3 voxel (valori già centrati) e una componente con pesi (0,6; 0,0; 0,8):

| Soggetto | voxel₁ | voxel₂ | voxel₃ | Punteggio |
|---|---|---|---|---|
| 1 | 2 | −1 | 1 | 0,6·2 + 0,0·(−1) + 0,8·1 = **2,0** |
| 2 | −1 | 3 | −2 | 0,6·(−1) + 0,0·3 + 0,8·(−2) = **−2,2** |

I pesi sono uguali nelle due righe; cambiano i valori dei voxel, quindi cambia il punteggio. Un peso nullo (voxel₂) esclude quel voxel dalla componente.

Il grafico degli autovalori in ordine decrescente si chiama *scree plot*; la quota cumulata dice quante componenti servono per arrivare, ad esempio, al 90% della varianza.

#### Equivalenze utili

- La PCA è la decomposizione ai valori singolari (SVD) di `Xc`: gli autovalori di C sono i valori singolari al quadrato diviso `n-1`. `sklearn.decomposition.PCA` fa questo.
- **Matrice più larga che alta (*p* > *n*).** Gli autovalori si ottengono dalla matrice piccola *n* × *n* invece che da quella *p* × *p*: vedi la sezione successiva. È ciò che fa [`covariance_pca.py`](../../../src/analysis/covariance_pca.py) su 5845 soggetti × 291.345 voxel.
- **Il segno di una componente è arbitrario.** Moltiplicarla per −1 è una soluzione equivalente. Per leggere una mappa si fissa una convenzione (qui: il voxel con |valore| massimo positivo).

#### PCA su una matrice più larga che alta (metodo degli snapshot)

**Il problema.** La covarianza tra i voxel ha *p* × *p* valori. Con *p* = 227.235 sono circa 413 GB in float64: non entra in memoria, e `sklearn.decomposition.PCA` non regge nemmeno la tabella dei dati (5845 × 227.235, 5,3 GB) perché ne fa più copie.

**Il trucco.** Si scrive la tabella centrata con la SVD: `Xc = U · S · Vᵀ`, con `U` (*n* × *n*, i soggetti), `S` (i valori singolari) e `V` (*p* × *n*, i voxel). Allora:

- `Xc · Xcᵀ = U · S² · Uᵀ`: la matrice *n* × *n* che confronta i soggetti tra loro (ogni valore è il prodotto scalare tra le righe centrate di due soggetti, detta matrice di Gram);
- `Xcᵀ · Xc = V · S² · Vᵀ`: la matrice *p* × *p* da cui parte la PCA.

Compare lo stesso `S²` in entrambe, quindi hanno **gli stessi autovalori non nulli**. La varianza della componente *j* è `S²ⱼ / (n-1)`.

**Gli autovettori dei voxel** (i pesi) si ricavano da quelli dei soggetti: `V = Xcᵀ · U / S`. Nel codice sono calcolati a blocchi di colonne, quindi la matrice *p* × *p* non viene mai costruita ([`covariance_pca.py`](../../../src/analysis/covariance_pca.py), `fit_covariance_pca` e `rotated_scores`). In memoria restano la matrice *n* × *n* (circa 270 MB) e un blocco di colonne.

**Perché non si perde nulla.** Una tabella con *n* righe, dopo il centraggio, ha al massimo `n-1` componenti con varianza non nulla: le *p* dimensioni dei voxel non possono produrne di più. La matrice piccola contiene quindi tutta l'informazione utile.

**Duale o sulla covarianza tra variabili.** Sono due strade per lo stesso risultato: stessi autovalori, stesse componenti. Il metodo degli snapshot, o PCA duale, parte dalla matrice *n* × *n* tra i soggetti; la strada classica parte dalla matrice *p* × *p* di covarianza tra le variabili.

**Come si sceglie.** Si usa la matrice più piccola: il duale quando le variabili sono più dei soggetti (*p* > *n*), la covarianza tra variabili quando sono meno (*p* < *n*). La memoria cresce con il quadrato della dimensione della matrice scelta, quindi per matrici larghe come le nostre il duale è l'unico percorso praticabile.

Matrici del progetto:

| Sessione | Soggetti (*n*) | Variabili (*p*) | Percorso conveniente |
|---|---|---|---|
| `s1.4-vol` (lesione voxelwise) | 5845 | 221.955 | duale |
| `s2.4-vol` (disconnettoma voxelwise, voxel fuori dal brain azzerati) | 5845 | 227.235 | duale |
| `s2.1-schaefer-200-tian-s2` (SDC parcellato) | 1119 | 232 | covarianza tra variabili |
| `s2.4-stream` (SDC per tratto) | 5831 | 87 | covarianza tra variabili |

**Cosa implementa il codice.** [`covariance_pca.py`](../../../src/analysis/covariance_pca.py) implementa **entrambi i percorsi**, scelti con `dual` (`true`: duale, `false`: covarianza tra variabili), con o senza `standardize`. Su `s2.4-stream` (5831 × 87) il percorso sulla covarianza tra variabili impiega meno di un secondo, il duale circa 24.

**Cosa è verificato.**

- I test (`tests/unit/test_covariance_pca.py`) confrontano autovalori e quote di varianza con `sklearn.decomposition.PCA` su matrici piccole, per ognuna delle quattro combinazioni di `standardize` e `dual`, anche con un grande offset comune, dove le identità di questo tipo perdono precisione (`lessons_learned.md` #42).
- Sulla matrice vera il confronto con sklearn non è possibile, per la memoria. Il risultato si basa sull'identità algebrica e sui test su matrici piccole.

**Limite numerico.** Gli autovalori grandi sono precisi. Quelli vicini a zero (le ultime componenti) lo sono meno: non servono, perché ci si ferma alla quota di varianza scelta.

#### Limiti

- È **lineare**: non trova strutture curve.
- È sensibile ai **valori estremi**: pochi soggetti con valori enormi possono dominare una componente.
- Le componenti sono **ortogonali per costruzione**: non è detto che corrispondano a processi distinti nei dati.

### Covarianza o correlazione

**Non sono due tecniche diverse.** È la stessa PCA applicata a due versioni dei dati:

| | PCA sulla covarianza | PCA sulla correlazione |
|---|---|---|
| Preparazione | si toglie la media di ogni variabile | si toglie la media **e** si divide per la deviazione standard |
| Scala delle variabili | conta | non conta |
| Equivale a | `sklearn.PCA` così com'è | `StandardScaler` + `PCA` |

**Perché cambia il risultato.** La PCA cerca le direzioni di massima varianza.

- Con la covarianza, una variabile che varia molto domina le prime componenti.
- Con la correlazione tutte le variabili hanno varianza 1, quindi nessuna domina per scala.

**Quando usare l'una o l'altra:**

- **Correlazione**: variabili in unità diverse (età in anni, volume in mm³). Senza standardizzare, vincerebbe quella con i numeri più grandi per puro accidente di unità.
- **Covarianza**: variabili nella stessa unità, dove la differenza di variabilità è informazione vera.

**Nel nostro caso: covarianza.** Ogni voxel del disconnettoma è una probabilità di disconnessione, tutti sulla stessa scala. Un voxel che varia di più tra i soggetti è davvero più informativo. Standardizzando, i voxel quasi sempre a zero (e quindi con variabilità minuscola, spesso solo rumore) peserebbero quanto gli altri. È anche la scelta di Thiebaut de Schotten et al. 2020.

### La rotazione varimax

#### L'idea in una frase

**Gli assi della PCA sono una scelta tra tante equivalenti. Il varimax li gira finché non diventano facili da leggere.**

In 2D: una nuvola di punti si può descrivere con due assi dritti, storti o ruotati di 30°. La nuvola non cambia, cambia solo il riferimento. La PCA sceglie gli assi con un criterio di varianza, che non garantisce che siano interpretabili. Il varimax ne sceglie altri, equivalenti per l'informazione, con un criterio di semplicità.

#### Perché ruotare non costa nulla

Le prime *k* componenti hanno una matrice di pesi Λ, di dimensione *p* × *k*. La PCA approssima la covarianza con:

> C ≈ Λ Λᵀ

Se R è una matrice **ortogonale** (RᵀR = I: una rotazione, eventualmente con riflessione), le componenti ruotate B = ΛR danno:

> B Bᵀ = Λ R Rᵀ Λᵀ = Λ Λᵀ

La stessa ricostruzione, quindi la stessa varianza totale spiegata dalle *k* componenti insieme. Ruotare cambia *come* quella varianza è divisa tra le componenti, non quanta ce n'è.

#### Cosa significa "facile da leggere"

| | Ricetta della PCA | Ricetta dopo il varimax |
|---|---|---|
| Variabili coinvolte | tutte un po' | poche molto, le altre quasi zero |
| Come si legge | "un mix di tutto" | "questa è la zona X" |

Il varimax cerca la rotazione in cui ogni variabile appartiene soprattutto a **una** componente (*struttura semplice*).

#### Il criterio

Si cerca la R che massimizza:

> V(R) = Σⱼ [ media_i(bᵢⱼ⁴) − ( media_i(bᵢⱼ²) )² ]

con B = ΛR, dove *i* scorre sulle variabili e *j* sulle componenti. Dentro la parentesi c'è la **varianza dei pesi al quadrato** della componente *j*: alta quando pochi pesi sono grandi e molti sono vicini a zero.

**Perché spinge verso la concentrazione.** Una rotazione conserva la lunghezza di ogni riga: Σⱼ bᵢⱼ² è fisso per ogni variabile. Cambia solo come quell'energia si divide tra le componenti. Con una variabile di energia 1 e due componenti:

| Distribuzione | Pesi | Σ b⁴ |
|---|---|---|
| Spalmata | (0,7; 0,7) | 0,49² + 0,49² ≈ 0,48 |
| Concentrata | (1; 0) | 1² + 0² = 1 |

A energia fissa, la somma delle quarte potenze è massima quando l'energia sta su una sola componente. Massimizzare V significa far scegliere a ogni variabile una componente.

#### Come si calcola

Non c'è formula chiusa (salvo con due componenti). Si itera:

1. si parte da R = I;
2. si calcola il gradiente di V rispetto a R (matrice *k* × *k*);
3. dalla sua SVD, G = U Σ Vᵀ, si pone R = U Vᵀ, la rotazione ortogonale più vicina al gradiente;
4. si ripete fino a convergenza o fino al numero massimo di iterazioni (500 nel paper).

Trova un massimo **locale**, non necessariamente globale.

#### I punteggi dopo la rotazione

Le colonne di B non sono più ortogonali nei dati, quindi la semplice proiezione non basta. Il punteggio di un soggetto con riga centrata **x** è il vettore **s** che ricostruisce meglio **x** come combinazione dei profili ruotati, cioè la regressione multipla:

> **s** = (BᵀB)⁻¹ Bᵀ **x**

Con una rotazione ortogonale i punteggi che ne escono sono i punteggi PCA a varianza 1, ruotati: restano **scorrelati tra loro**, anche se le colonne di B non sono ortogonali. Per la letteratura sui punteggi dopo la rotazione vedi i riferimenti in [`docs/dev/covariance_pca.md`](../../../docs/dev/covariance_pca.md).

#### Cosa si guadagna e cosa si perde

**Si guadagna:** componenti leggibili come zone (per il disconnettoma: gruppi di voxel che si disconnettono insieme, ad esempio un emisfero o un fascio).

**Si perde:**

- **L'ordine per varianza.** Dopo la rotazione la prima componente non è più la più importante. I punteggi hanno tutti varianza 1, quindi non servono per ordinarle: si ordina per la quota di varianza che ogni componente spiega, cioè la somma dei pesi al quadrato della sua colonna divisa per la varianza totale. La somma sulle componenti è quella di prima della rotazione, cambia come è ripartita.
- **L'uguaglianza dei pesi nel clustering.** Con la regressione, i punteggi ruotati hanno varianza 1 per costruzione: ogni componente pesa uguale, anche quelle che spiegano poca varianza. Per un clustering sulle componenti l'input consigliato sono i punteggi PCA non ruotati.
- **L'indipendenza dalla scelta di *k*.** Ruotare 14 o 42 componenti dà profili diversi.

**Non si scopre nulla di nuovo.** I dati e l'informazione sono gli stessi. Il varimax sceglie la descrizione più semplice anche quando nei dati non c'è una struttura a gruppi, e produce comunque componenti dall'aspetto pulito: che i gruppi siano reali va verificato altrove (ad esempio con la riproducibilità tra due metà dei soggetti).

#### Quando usare cosa

| Obiettivo | Scelta |
|---|---|
| Interpretare le componenti, confrontarsi con il paper | PCA + varimax |
| Input di un clustering o di un'altra riduzione | PCA non ruotata |

### Dalle componenti alle mappe nel cervello

Il disconnettoma voxelwise permette di riportare ogni componente sul cervello. Due controlli e una mappa, come in Thiebaut de Schotten et al. 2020.

#### Quanto dipende dal volume della lesione

Una componente potrebbe misurare solo quanto è grande la lesione. Per verificarlo si calcola, per ogni componente, **R²**: il quadrato della correlazione tra il punteggio dei soggetti e il volume della lesione. Si legge come la quota della variabilità del punteggio che si spiega conoscendo il volume.

- R² = 0,04: componente quasi indipendente dalla dimensione della lesione.
- R² = 0,50: componente che misura soprattutto la dimensione.

Si calcola sulle componenti ruotate e su quelle non ruotate, per vedere cosa cambia con la rotazione. Il paper lo calcola sulle ruotate e riporta R² < 0,1 per tutte.

#### La mappa *t*

- **Come si fa.** Per ogni voxel, una regressione mette in relazione la sua disconnessione nei soggetti con i punteggi di tutte le componenti insieme, e dice di quanto cambia quando sale il punteggio di ciascuna. Quel cambiamento, diviso per la sua incertezza (l'errore standard), è il *t* del voxel. I *t* di tutti i voxel sul cervello formano la mappa della componente.
- **Mappa dei pesi e mappa *t*.** I pesi di una componente riportati sul cervello formano la mappa dei pesi. La mappa *t* è simile ma non uguale, perché tiene conto dell'incertezza di ogni voxel (su `s2.4-vol` la correlazione tra le due va da 0,74 a 0,91 per componente).
- **Il paper** usa `randomise` di FSL con 1000 permutazioni; il repo calcola le statistiche *t* senza test di permutazione.

#### Come si leggono

| Cosa si vede | Significa |
|---|---|
| **Rosso** (*t* positivo) | più il soggetto ha la componente, più quel voxel è disconnesso |
| **Blu** (*t* negativo) | più il soggetto ha la componente, meno quel voxel è disconnesso |
| **Colore forte** (|*t*| alto) | effetto solido |
| **Colore assente** | effetto sotto la soglia, o nessun effetto |

- **Cosa si cerca**: dove sta la zona rossa. Se è compatta, la componente è una zona del cervello.
- **Segno**: arbitrario (vedi sopra). Ogni mappa è orientata con il voxel di |*t*| massimo positivo, quindi si guarda la forma e non il colore.
- **Soglia**: con tanti soggetti anche effetti piccoli hanno *t* alto, e una soglia fissa come |*t*| > 3 colorerebbe quasi tutto il cervello. Si colorano invece i voxel con |*t*| almeno una frazione (qui 0,3) del massimo di quella componente.

#### Riproducibilità

La mappa dipende dai soggetti scelti? Si dividono a caso i soggetti in due metà, si rifà la regressione in ciascuna e si correlano (Pearson, sui voxel) le due mappe di ogni componente: 1 se uguali, 0 se non hanno nulla in comune.

- I punteggi sono quelli calcolati su tutti i soggetti: si verifica che la componente si ritrovi, non che la PCA sia stabile.
- Il paper riporta 0,813 ± 0,079 in media (da 0,39 a 0,98), con metà da 666 soggetti. Qui le metà sono da circa 2900: i valori non sono direttamente confrontabili.

### Nel repo

- Calcolo su matrici larghe (covarianza, varimax, punteggi per regressione, R², mappe t): [`src/analysis/covariance_pca.py`](../../../src/analysis/covariance_pca.py), riferimento tecnico in [`docs/dev/covariance_pca.md`](../../../docs/dev/covariance_pca.md).
- `pca` in `src/analysis/reduction.py` (parametri e scelte: [`docs/guides/dim_reduction.md`](../../../docs/guides/dim_reduction.md)) usa questo calcolo con `solver: blocks`, oppure `sklearn.decomposition.PCA` con `solver: sklearn`; la rotazione passa da `factor_analyzer.Rotator`.
- Notebook: `notebooks/pipeline_building/thiebaut_2020_replication.ipynb` (PCA con varimax; la PCA senza rotazione compare solo nel confronto con il volume della lesione).
- Valutazione di una PCA già prodotta (di produzione o di tuning): `notebooks/post-results_analysis/pca_evaluation.ipynb`, con le sezioni su varianza, varimax, volume della lesione, mappe ed embedding; il codice è in [`src/analysis/pca_evaluation.py`](../../../src/analysis/pca_evaluation.py).
- Fonte del metodo: Thiebaut de Schotten et al. 2020, *Brain disconnections link structural connectivity with function and behaviour* (cartella in `knowledge/papers/stroke_core/`).
