# Elenco completo dei metodi e tecniche

## 1. Metodi per stimare la disconnessione

|Metodo|Paper|Dati di input|Obiettivo|
|---|---|---|---|
|**SDC (Structural Disconnection) via BCB Toolkit**|Thiebaut de Schotten 2020, Salvalaggio 2020, Bisogno 2025, Cinetto|Lesione del paziente + connettoma trattografico di soggetti sani (HCP)|Stimare quali fasci di materia bianca sono probabilmente interrotti dalla lesione, senza bisogno di risonanza di diffusione del paziente|
|**FDC (Functional Disconnection) indiretta**|Salvalaggio 2020, Bisogno 2025|Lesione + atlante di connettività funzionale sano|Stimare quali reti funzionali dovrebbero essere disconnesse in base alla posizione della lesione|
|**Disconnessione diretta vs indiretta (SSPL)**|Griffis 2020|Lesione + atlante trattografico HCP-842, teoria dei grafi|Distinguere fibre tagliate fisicamente (dirette) da percorsi allungati perché una tappa intermedia è danneggiata (indirette)|
|**SDC/danno diretto via atlante trattografico HCP-842 (streamline count)**|Griffis 2019, Griffis 2020|Lesione + atlante trattografico HCP-842 (842 soggetti sani)|Stimare le disconnessioni strutturali contando le streamline che intersecano la lesione — metodo distinto dal BCB Toolkit (atlante e pipeline propri, non citato per questi due paper)|
|**Lesioni sintetiche (random, size/lateralization-matched)**|Thiebaut de Schotten 2020|K-means clustering su coordinate voxel per generare 1333 lesioni sintetiche (pari al numero di lesioni reali)|Gruppo di controllo per isolare l'effetto della distribuzione non casuale delle lesioni reali|

## 2. Metodi di riduzione dimensionale / embedding

|Metodo|Paper|Dati di input|Obiettivo|
|---|---|---|---|
|**PCA (rotazione varimax o obliqua a seconda del paper)**|Thiebaut de Schotten 2020 (varimax), Talozzi 2023, Corbetta 2015, Corbetta 2018, Bisogno 2021 (PROMAX/obliqua), Facchini 2023 (obliqua), Salvalaggio 2020, Cinetto|Mappe di lesione/SDC parcellizzate; punteggi comportamentali|Comprimere alta dimensionalità in componenti principali interpretabili, sia lato imaging che lato comportamento|
|**t-SNE**|Thiebaut de Schotten 2020|Mappe di lesione e disconnettoma (grezze, non parcellizzate)|Visualizzazione qualitativa 2D della ridondanza/clustering spaziale tra lesioni reali e sintetiche|
|**UMAP**|Talozzi 2023, Pini 2026|SDC parcellizzata (Talozzi); gradienti strutturali/microstrutturali (Pini, per la classificazione stroke vs controlli)|Creare un morfospazio 2D compresso su cui allenare modelli predittivi (DSD, Talozzi) o classificare pazienti/controlli (Pini)|
|**Autoencoder (rete neurale, layer densi + ReLU)**|Idesis 2023|Serie temporali BOLD (235 ROI × 896 timepoint)|Comprimere non linearmente la dinamica del segnale fMRI in 6 dimensioni latenti, preservando più varianza della PCA|
|**Diffusion map embedding**|Pini 2026|Matrici di connettività strutturale da trattografia whole-brain|Estrarre gradienti strutturali principali (assi di organizzazione delle fibre) preservando la geometria del connettoma|

## 3. Metodi di trattografia e ricostruzione della connettività strutturale

|Metodo|Paper|Dati di input|Obiettivo|
|---|---|---|---|
|**Trattografia probabilistica whole-brain**|Pini 2026|DWI (dettagli su n. streamline/eventuale refinement non specificati nel testo principale, rimandati dagli autori al materiale supplementare — non verificabili dal riassunto)|Ricostruire il connettoma strutturale individuale|
|**Trattografia HCP a 7T (163-176 soggetti sani)**|Thiebaut de Schotten 2020 (163 soggetti), Talozzi 2023 (176 soggetti)|DWI 7T di soggetti sani, usata come riferimento per proiettare le lesioni|Fungere da atlante di riferimento per stimare la SDC senza bisogno di DWI del paziente|
|**Trattografia HCP (842 o 178 soggetti sani; campo magnetico non specificato nei riassunti)**|Griffis 2020 (842 soggetti), Cinetto (178 soggetti)|DWI di soggetti sani, usata come riferimento per proiettare le lesioni|Fungere da atlante di riferimento per stimare la SDC senza bisogno di DWI del paziente|
|**DTI (FA, MD, AD, RD)**|Pini 2026|DWI voxel-wise|Misurare parametri di diffusione classici per la microstruttura della materia bianca|
|**NODDI (NDI/ICVF, ODI, ISOVF)**|Pini 2026|DWI voxel-wise|Modellare in modo più specifico densità dei neuriti e dispersione dell'orientamento delle fibre|
|**Fattorializzazione dei parametri microstrutturali**|Pini 2026|Output DTI/NODDI|Sintetizzare in 3 fattori latenti stabili (acqua libera, anisotropia/dispersione, mielinizzazione)|

## 4. Metodi di modellistica predittiva / machine learning

|Metodo|Paper|Dati di input|Obiettivo|
|---|---|---|---|
|**Ridge Regression**|Siegel 2016, Corbetta 2015, Bisogno 2021, Salvalaggio 2020, Facchini 2023, Cinetto, Santoro 2026|Voxel di lesione/SDC o feature di rete|Predire punteggi comportamentali individuali da mappe ad alta dimensionalità, quantificando varianza spiegata (R²) — Cinetto usa nello specifico una ridge regression **penalizzata**|
|**Multi-Task Learning**|Siegel 2016|Lesione, FC|Predire simultaneamente più domini comportamentali condividendo informazione tra i task|
|**Regressione Lasso**|Bisogno 2025|Overlap lesione-atlante (vascolare/Yeo/Figley)|Predire mRS a 3 mesi selezionando automaticamente le feature più rilevanti|
|**Regressione multipla (nel morfospazio UMAP)**|Talozzi 2023|Coordinate del morfospazio, sintetizzate con una PCA a 3 componenti|Predire punteggi neuropsicologici a 1 anno|
|**Modelli Lineari a Effetti Misti (LMM/MEM)**|Volpi 2024, Volpi 2025, Pini 2026|Feature fMRI locali; parametri di diffusione longitudinali|Modellare simultaneamente effetti di popolazione (fissi) e variabilità individuale (random), anche nel tempo|
|**Regressione lineare robusta con bootstrapping**|Pini 2026|Feature neuroimaging vs fattori comportamentali|Associare neuroimaging e comportamento controllando per outlier|
|**Random Forest**|Idesis 2023|Feature nello spazio source vs spazio latente AE|Classificare pazienti/controlli e predire recupero a 1 anno (accuratezze riportate come AUC)|
|**SVM (Support Vector Machine)**|Pini 2026|Gradienti strutturali (connettività inter-/intra-emisferica)|Classificare pazienti vs controlli (89% inter-emisferica, 96% intra-emisferica)|
|**Selezione feature: NNLS, Elastic Net, GETS**|Volpi 2024|50 metriche fMRI|Selezionare feature non ridondanti minimizzando multicollinearità prima della modellizzazione|
|**Validazione Leave-One-Out (LOO-CV) / Leave-One-Subject-Out (LOSO)**|Corbetta 2015, Salvalaggio 2020, Bisogno 2025, Cinetto (LOO per il tuning del parametro di penalità λ), Santoro 2026 (LOSO)|Modelli predittivi lesione/SDC/connettività|Stimare la performance predittiva su dati non visti con campioni piccoli|
|**PLSR (Partial Least Squares Regression)**|Griffis 2019|Danno locale vs SDC come predittori di FC|Confrontare quale rappresentazione del danno spiega meglio le alterazioni funzionali|
|**PLSC (Partial Least Squares Correlation)**|Griffis 2019, Santoro 2026|Matrici di disconnessione e di FC insieme (Griffis); connettività e punteggi comportamentali NMF (Santoro)|Estrarre componenti latenti condivise tra struttura e funzione, o tra connettività e comportamento (covarianza multivariata)|

## 5. Metodi di clustering

|Metodo|Paper|Dati di input|Obiettivo|
|---|---|---|---|
|**K-means clustering**|Bonkhoff 2020, Thiebaut de Schotten 2020 (per generare lesioni sintetiche)|Finestre temporali di FC dinamica; coordinate voxel|Raggruppare pattern di connettività ricorrenti in "stati"; generare lesioni sintetiche|
|**Repeated Spectral Clustering (RSC), con consensus clustering interno**|Zanola 2026|Differenze assolute nei tassi di recupero NIHSS tra pazienti|Identificare traiettorie di recupero (fenotipi) guidate dai dati, superando la dicotomia fitters/non-fitters — il RSC combina spectral clustering e consensus clustering su k-means ripetuti, non è quindi solo un'estensione futura ma parte del metodo già usato|

## 6. Metodi per l'analisi della connettività funzionale (FC)

|Metodo|Paper|Dati di input|Obiettivo|
|---|---|---|---|
|**FC statica (correlazione di Pearson tra ROI)**|Siegel 2016, Siegel 2018, Griffis 2019, Griffis 2020, Salvalaggio 2020|Serie temporali BOLD resting-state|Misurare sincronizzazione media tra regioni su tutta la scansione|
|**FC dinamica (sliding window)**|Bonkhoff 2020|BOLD resting-state, finestre di 44 secondi|Catturare come la connettività cambia istante per istante|
|**Leading Eigenvector (fase istantanea)**|Volpi 2024, Volpi 2025|BOLD resting-state|Rappresentare la configurazione dominante di sincronizzazione di fase in un dato momento|
|**Analisi di modularità (teoria dei grafi)**|Siegel 2018, Griffis 2019, Corbetta 2018|Matrici di FC|Misurare integrazione/segregazione della rete e come cambia nel tempo o col danno|
|**Brain Fingerprinting (Iclinical, Iself)**|Santoro 2026|FC longitudinale (4 timepoint)|Misurare somiglianza al gruppo sano (Iclinical) e stabilità individuale nel tempo (Iself)|
|**Residualizzazione per covariate (età, sesso, volume lesione)**|Santoro 2026|Matrici FC|Analisi di **robustezza secondaria**: i risultati principali sono riportati SENZA questa correzione, la residualizzazione serve solo a verificare che non dipendano dai confondenti|
|**Reti canoniche di Yeo (7/17 network)**|Santoro 2026, Seba_Meeting_2, Bisogno 2025|Parcellizzazione corticale|Framework di riferimento per organizzare l'analisi per network funzionali|

## 7. Metriche di teoria dei grafi (network analysis)

|Metrica|Paper|Applicata a|Obiettivo|
|---|---|---|---|
|**Degree, Strength, Clustering Coefficient, Betweenness, Eigenvector Centrality, Local/Global Efficiency**|Volpi 2024, Volpi 2025|Matrici sFC, tvFC, reti HRF|Descrivere il ruolo topologico di ciascun nodo nella rete|
|**Shortest Structural Path Length (SSPL)**|Griffis 2020|Connettoma strutturale|Quantificare l'allungamento del percorso tra regioni per la disconnessione indiretta|
|**Modularità**|Siegel 2018, Corbetta 2018, Griffis 2019|Matrici FC|Misurare bilancio tra integrazione interna e segregazione tra reti|

## 8. Metodi di estrazione di feature locali dal segnale BOLD

|Metodo|Paper|Dati di input|Obiettivo|
|---|---|---|---|
|**ALFF (Amplitude of Low-Frequency Fluctuations)**|Volpi 2024, Volpi 2025|BOLD resting-state|Misurare l'ampiezza delle oscillazioni spontanee a bassa frequenza in una regione|
|**ReHo (Regional Homogeneity, coeff. di Kendall)**|Volpi 2024, Volpi 2025|BOLD resting-state, voxel adiacenti|Misurare sincronizzazione locale a corto raggio|
|**Statistiche di base (mediana, MAD, skewness del BOLD)**|Volpi 2024, Volpi 2025|Serie temporale BOLD|Caratterizzare proprietà distribuzionali di base del segnale|
|**Entropia approssimata (ApEn, rApEn)**|Volpi 2024, Volpi 2025|Serie temporale BOLD|Quantificare regolarità/imprevedibilità temporale del segnale|
|**Modello autoregressivo AR(1)**|Volpi 2024, Volpi 2025|Serie temporale BOLD|Misurare memoria a breve termine/autocorrelazione del segnale|
|**Peak-BOLD (conteggio pseudo-eventi)**|Volpi 2024, Volpi 2025|Serie temporale BOLD|Catturare dinamiche non lineari ed eventi estremi|
|**Deconvoluzione cieca dell'HRF**|Volpi 2024, Volpi 2025|Serie temporale BOLD|Stimare la risposta emodinamica regionale come proxy del flusso ematico locale|
|**Reti "vascolari" da correlazione spaziale delle forme d'onda HRF**|Volpi 2024, Volpi 2025|HRF deconvolute per regione|Costruire un grafo di connettività basato sulla vascolarizzazione, non sull'attività neurale — introdotte per la prima volta in Volpi 2024, riprese in Volpi 2025|
|**TENET (Temporal Evolution NETwork) — reversibilità temporale**|Idesis 2023|Serie temporale BOLD (forward vs reversed cross-correlation)|Misurare l'asimmetria temporale del segnale come proxy della distanza dall'equilibrio termodinamico|

## 9. Metodi statistici di confronto e validazione

|Metodo|Paper|Dati di input|Obiettivo|
|---|---|---|---|
|**Bootstrap resampling (1000 campioni)**|Griffis 2019, Griffis 2020, Pini 2026|Statistiche varie|Stimare intervalli di confidenza robusti|
|**Test di permutazione con correzione FWE**|Bisogno 2025|Associazioni voxel-wise con outcome|Controllare errore family-wise in analisi massicciamente univariate|
|**ANOVA a tre vie (repeated measures)**|Griffis 2020|FC per categorie di connessione (diretta/indiretta, spared/disconnected, segno FC)|Confrontare l'effetto di più fattori categoriali sulla FC|
|**Wilcoxon signed-rank test**|Salvalaggio 2020|Confronto R² tra modelli (lesione vs SDC vs FDC)|Verificare se le differenze di potere predittivo sono significative|
|**Correzione di Bonferroni**|Thiebaut de Schotten 2020|Correlazioni tra componenti di disconnessione e mappe funzionali|Controllare per confronti multipli|
|**ANOVA a misure miste**|Facchini 2023|Pesi dei test sulle componenti principali (stroke vs tumori)|Verificare se la struttura fattoriale differisce tra le due patologie|
|**Regressione logistica**|Facchini 2023|Punteggi comportamentali|Discriminare tra eziologia stroke vs tumore (AUC)|
|**Analisi fattoriale (oblique rotation)**|Facchini 2023, Pini 2026|Punteggi comportamentali; parametri di diffusione|Estrarre fattori latenti da misure correlate tra loro|
|**Test non parametrici (Kruskal-Wallis, Mann-Whitney U, χ²) + correzione FDR Benjamini-Hochberg**|Zanola 2026|Cluster RSC vs variabili esterne (lato/volume lesione, rtPA, mRS, classificazione Heidelberg)|Validare l'associazione tra cluster di recupero e variabili cliniche esterne non usate nel clustering|
|**SEM (Structural Equation Modeling)**|Pini 2026|Pattern di gradienti strutturali tra gruppi|Confrontare formalmente i pattern di gradiente tra pazienti e controlli|

## 10. Atlanti e parcellizzazioni utilizzate

|Atlante|Paper|Contenuto|Uso|
|---|---|---|---|
|**Glasser HCP-MMP1.0** (360 aree corticali)|Thiebaut de Schotten 2020|Parcellizzazione corticale multimodale|Caratterizzare lesioni/SDC per regione|
|**12 ROI sottocorticali manuali**|Thiebaut de Schotten 2020|Amigdala, caudato, ippocampo, pallido, putamen, talamo (bilaterali)|Completare la parcellizzazione con strutture sottocorticali|
|**Parcellizzazione Gordon333** (333 regioni corticali, ridotte a 324 dopo esclusione di 9 regioni con pochi vertici)|Griffis 2019, Griffis 2020|Corticale|Costruire il connettoma strutturale/funzionale|
|**Atlante trattografico HCP-842**|Griffis 2019, Griffis 2020|Connettoma di riferimento (842 soggetti sani)|Stimare connessioni strutturali dirette/indirette|
|**Atlante vascolare (32 territori)**|Bisogno 2025|Territori arteriosi|Confronto "classico" con approccio a network|
|**Atlante funzionale di Yeo (7/17 network)**|Bisogno 2025, Santoro 2026, Seba_Meeting_2|Reti funzionali canoniche|Localizzare lesione/FC in termini di sistemi funzionali|
|**Atlante strutturale di Figley (13 sistemi)**|Bisogno 2025|Sistemi di materia bianca|Localizzare lesione in termini di fasci strutturali|
|**Atlanti menzionati nei meeting (non ancora nei paper): Yan200, Tian S2, Buckner**|Seba_Meeting_2|Parcellizzazione cortico-sottocorticale in spazio fMRIPrep|Standard di riferimento pianificato per il tuo progetto|
