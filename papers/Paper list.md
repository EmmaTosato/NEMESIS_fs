# Cinetto et al. 
_Clinical variables surpass lesion and disconnection features predicting multi-domain stroke outcomes_

## Riassunto brevissimo
Questo studio affronta la sfida della prognosi a lungo termine post-ictus. 
I ricercatori hanno valutato in modo sistematico se l'aggiunta di complesse metriche di neuroimaging (topografia della lesione e stime di disconnessione strutturale a livello dell'intero cervello) migliori la previsione del recupero rispetto all'uso delle sole variabili cliniche e demografiche di base. Tracciando 199 pazienti su otto domini funzionali per un anno, lo studio dimostra (come suggerisce chiaramente il titolo) che i dati clinici e demografici superano le complesse misurazioni del danno e delle disconnessioni anatomiche nel prevedere gli esiti a lungo termine.

---

## Domande scientifiche e Obiettivi
- Qual è il reale valore prognostico aggiuntivo (incrementale) delle mappe avanzate di lesione e di disconnessione strutturale (SDC) rispetto ai predittori clinici standard (es. punteggio NIHSS, età)?
- È possibile prevedere in modo affidabile il recupero del paziente non in un singolo dominio, ma trasversalmente in **molteplici domini cognitivi e funzionali** all'interno della stessa coorte clinica?
- **Obiettivo principale:** Confrontare testa a testa e in modo gerarchico l'accuratezza predittiva di 4 categorie di dati (demografici, clinico-neurologici acuti, topografia della lesione e disconnettoma) per stimare gli esiti dei pazienti a 2 settimane, 3 mesi e 12 mesi di distanza dall'ictus.

## Metodologie

- **Campione:** Una coorte prospettica di 199 pazienti al primo ictus (età 19-83 anni) e 68 controlli sani abbinati per età e istruzione.
- **Elaborazione Neuroimaging:** Le lesioni dei pazienti sono state segmentate su scansioni anatomiche standard e proiettate su un connettoma sano (derivato da 178 soggetti dello _Human Connectome Project_) utilizzando il _BCB Toolkit_. Questo ha generato mappe probabilistiche indirette dei tratti di materia bianca disconnessi (SDC) per ogni paziente.
- **Modellistica Predittiva (Machine Learning):** La vastissima quantità di dati spaziali (lesioni e SDC) è stata compressa utilizzando un'Analisi delle Componenti Principali (PCA). Successivamente, è stato applicato un algoritmo di _Ridge Regression_ con validazione incrociata per prevedere i punteggi in ben **otto domini** (motorio destro/sinistro, linguaggio, attenzione generale e spaziale, memoria verbale e spaziale, e indipendenza funzionale). I predittori sono stati inseriti nel modello a strati (partendo dalle basi demografiche fino ai dati di neuroimaging) per testarne il valore aggiunto.

## Risultati
- **Fattori latenti di danno:** L'analisi PCA sulle mappe ha catturato in modo eccellente le distribuzioni tipiche dei danni da ictus. Per le lesioni, ha distinto gli ictus emisferici (destra vs sinistra) e l'interessamento dell'arteria cerebrale media. Per le disconnessioni (SDC), ha estratto modelli tipici di danno ai grandi fasci di materia bianca, come il corpo calloso, il tratto cortico-spinale, il fascicolo arcuato e il fascicolo fronto-occipitale inferiore.
- **Superiorità della clinica:** Come anticipato programmaticamente dal titolo del manoscritto, nella competizione "testa a testa" le variabili cliniche misurate nella fase acuta (come la gravità misurata dalla scala NIHSS o il lato della lesione) combinate alle caratteristiche demografiche, hanno superato le sofisticate metriche del danno anatomico (lesione) e del disconnettoma (SDC) nel prevedere l'andamento del paziente nei mesi successivi.

## Breve Discussione
- Il paper lancia un messaggio clinico di forte impatto (in leggero contrasto o integrazione rispetto agli studi precedenti di questo gruppo): sebbene la stima dettagliata del "disconnettoma" e della topografia della lesione offra preziose intuizioni sui meccanismi patofisiologici dell'ictus, per quanto riguarda la pura **previsione degli esiti clinici**, i fattori tradizionali rimangono superiori.
- I modelli predittivi più complessi e ad alta dimensionalità non battono le variabili standard raccolte al letto del paziente. Fattori come l'età, l'educazione e la severità clinica acuta misurata con l'NIHSS inglobano già al loro interno l'effetto del danno neurale e sono sufficienti (e persino migliori) per stimare con successo le traiettorie di recupero multi-dominio del paziente.

# Thiebaut de Schotten et al. (2020) 
_Brain disconnections link structural connectivity with function and behaviour_

## Riassunto brevissimo
Il paper dimostra che i deficit cognitivi post-ictus derivano non solo dal danno tissutale locale, ma dalla disconnessione delle reti di materia bianca. 
Poiché gli ictus colpiscono il cervello seguendo schemi non casuali, la classificazione clinica storica delle funzioni cerebrali risulta distorta. 
Mappando 1333 lesioni con reti fMRI, gli autori hanno quindi creato il primo "Atlante della Funzione della Materia Bianca" per 590 funzioni cognitive.

---

## Domande scientifiche e Obiettivi
- Qual è il ruolo specifico delle connessioni di materia bianca nel supportare le funzioni cerebrali e il comportamento?
- La nostra comprensione storica delle funzioni cerebrali, derivata dall'osservazione clinica dei pazienti, è stata distorta dal fatto che le lesioni da ictus non si distribuiscono in modo casuale?
- **Obiettivo principale:** Creare un "Disconnettoma" umano per mappare sistematicamente le funzioni cognitive sui tratti di materia bianca e migliorare le previsioni cliniche.

## Metodologie
- **Campione:** È stato utilizzato un database di 1333 lesioni reali da ictus. Per confronto, sono state generate 1333 lesioni "sintetiche" (casuali, ma identiche per volume e lateralizzazione a quelle reali).
- **Creazione del Disconnettoma:** Le lesioni sono state proiettate su una mappa ad alta risoluzione della materia bianca di individui sani (dati trattografici a 7T dello _Human Connectome Project_) per stimare la probabilità di disconnessione dei tratti.
- **Riduzione dimensionale (PCA):** È stata applicata un'Analisi delle Componenti Principali per raggruppare e riassumere i complessi pattern di disconnessione in un numero ridotto di "profili".
- **Confronto Funzionale:** I profili di disconnessione sono stati correlati spazialmente con 590 mappe meta-analitiche di attivazione cerebrale funzionale (fMRI) tratte dal database _Neurosynth_.

## Risultati
- **Distribuzione non casuale:** Le lesioni da ictus e le conseguenti disconnessioni mostrano un'alta ridondanza (si raggruppano in cluster molto più delle lesioni sintetiche) e tendono a colpire la materia bianca profonda.
- **Correlazione Struttura-Funzione:** 46 componenti principali spiegano oltre il 90% delle disconnessioni da ictus. Ben 40 di queste componenti correlano in modo significativo con specifiche reti funzionali fMRI (es. calcolo, navigazione spaziale, campo visivo, linguaggio).
- **Atlante della Materia Bianca:** È stato generato un atlante completo che mappa 590 funzioni cognitive direttamente sui tratti di materia bianca. I risultati mostrano anche una forte asimmetria: si sa molto di più sulle funzioni della materia bianca dell'emisfero sinistro rispetto a quello destro.

## Breve Discussione
- La forte corrispondenza tra le disconnessioni da ictus e le mappe fMRI suggerisce che l'organizzazione della materia bianca guida la segregazione funzionale del cervello.
- Poiché l'associazione tra disconnessione e funzione è molto più forte nelle lesioni reali rispetto a quelle sintetiche, gli autori concludono che 
" dalla natura non casuale e concentrica in cui gli ictus colpiscono il cervello.
- L'Atlante creato rappresenta un nuovo, potente strumento clinico, scaricabile e utilizzabile per proiettare qualsiasi attivazione funzionale sulla materia bianca e prevedere i deficit dei pazienti in base al loro specifico danno strutturale.

# Zanola et al. (2026) 
_Beyond proportional recovery in wake-up stroke: Unsupervised recovery clusters based on the NIHSS_

## Riassunto brevissimo
Il paper mette in discussione la tradizionale Regola del Recupero Proporzionale (PRR) nell'ictus, che divide rigidamente i pazienti in "fitters" e "non-fitters" tramite modelli lineari. Utilizzando tecniche di apprendimento non supervisionato (clustering) su 201 pazienti, gli autori identificano 6 traiettorie distinte di recupero, dimostrando che la maggior parte dei pazienti recupera in modo eterogeneo e non strettamente proporzionale al deficit iniziale. Questo approccio guidato dai dati offre una visione più sfumata e oggettiva della prognosi riabilitativa.

---

## Domande scientifiche e Obiettivi
- Come superare i limiti statistici (come il cosiddetto "accoppiamento matematico" e la divisione arbitraria in due sole categorie) tipici dei classici modelli lineari di recupero post-ictus?
- È possibile raggruppare i pazienti in base alla reale somiglianza delle loro traiettorie di recupero, piuttosto che forzarli in un singolo modello matematico globale?
- **Obiettivo principale:** Utilizzare algoritmi di clustering per identificare fenotipi (cluster) di recupero eterogenei in modo completamente guidato dai dati, validandone poi la rilevanza clinica rispetto a noti fattori prognostici (volume/lato lesione, trattamento).

## Metodologie
- **Campione:** 201 pazienti dal trial clinico WAKE-UP (ictus al risveglio), selezionati per gravità moderata (NIHSS > 4 all'esordio) e con deficit ancora presenti a 22-36 ore.
- **Calcolo del Recovery Ratio (RR):** La misura del recupero è stata calcolata come rapporto tra il punteggio NIHSS sub-acuto (22-36 h) e quello cronico (a 90 giorni).
- **Clustering (RSC):** È stato applicato un algoritmo di _Repeated Spectral Clustering_ basato sulle differenze assolute dei tassi di recupero tra i vari pazienti per raggrupparli in base alla similarità clinica.
- **Validazione:** I cluster ottenuti sono stati confrontati con la classica regressione lineare (PRR) e correlati a variabili cliniche esterne (es. lato e volume della lesione, trattamento con rtPA).

## Risultati
- **Sei traiettorie di recupero:** L'algoritmo ha individuato 6 cluster ottimali: C0 (recupero totale, 100%), C1 (recupero sopra la media), C2 e C3 (nella media, in linea con le stime del modello lineare PRR), C4 (sotto la media) e C5 (nessun recupero o deterioramento).
- **Nessun impatto per volume e trattamento:** Il volume della lesione all'ingresso in ospedale e il trattamento trombolitico (rtPA) non hanno mostrato associazioni significative con l'appartenenza ai diversi cluster di recupero.
- **Asimmetria emisferica:** Il lato della lesione ha influenzato il recupero. I pazienti con recupero perfetto (C0) avevano più lesioni destre del previsto, mentre i pazienti nei cluster a recupero medio-basso (C3) avevano più lesioni sinistre.
- **Predittività precoce:** Un Recovery Ratio precoce (\ge) 0.3 (valutato nelle prime fasi) ha permesso di prevedere l'appartenenza ai cluster favorevoli (C0-C3) in circa il 90% dei casi.

## Breve Discussione
- La classificazione binaria in "fitters" e "non-fitters" imposta dai modelli PRR dipende fortemente dal metodo usato ed è altamente soggettiva. Il clustering evita questo problema raggruppando i pazienti in fenotipi naturali.
- La maggioranza dei pazienti non segue una regola di recupero fisso e proporzionale; la natura del recupero è più complessa ed eterogenea.
- Il clustering dei tassi di recupero si è rivelato un modo efficiente per incorporare la variabile "tempo" nell'algoritmo, offrendo un quadro molto più granulare della ripresa post-ictus.
- L'identificazione precoce dei pazienti destinati ai cluster meno favorevoli potrebbe rivelarsi fondamentale in futuro per personalizzare le terapie riabilitative e massimizzare la neuroplasticità.



# Talozzi et al. (2023) 
_Latent disconnectome prediction of long-term cognitive-behavioural symptoms in stroke_

## Riassunto brevissimo
Prevedere l'evoluzione cognitiva a lungo termine dopo un ictus è estremamente complesso a livello individuale. Questo studio introduce un nuovo approccio basato sul "disconnettoma" (la mappa delle disconnessioni della materia bianca) per prevedere i sintomi a un anno di distanza. Comprimendo i dati di migliaia di lesioni in uno spazio bidimensionale (morfospazio), gli autori hanno sviluppato il _Disconnectome Symptoms Discoverer_ (DSD), un modello che supera le tradizionali metriche predittive. Il lavoro ha prodotto il primo Atlante Neuropsicologico della Materia Bianca (NWMA) e un'app web interattiva per la pratica clinica.

---

## Domande scientifiche e Obiettivi
- Come si possono prevedere in modo affidabile i deficit cognitivo-comportamentali a lungo termine a partire dai dati di neuroimaging raccolti nella fase acuta?
- È possibile mappare sistematicamente la relazione tra le disconnessioni cerebrali e le misurazioni cognitivo-comportamentali a livello del singolo individuo?
- **Obiettivo principale:** Creare un "morfospazio" del disconnettoma per prevedere i punteggi clinici a un anno di distanza, mettendo a disposizione della comunità un atlante completo e uno strumento predittivo open-access.

## Metodologie
- **Campione:** Sono stati utilizzati 5 diversi database. Il dataset principale (1333 lesioni da ictus) è servito per mappare la variabilità delle lesioni. Un secondo dataset (132 pazienti valutati a 1 anno con 86 test neuropsicologici) è stato usato per addestrare il modello, mentre gli altri dataset sono serviti per la validazione esterna.
- **Creazione del Disconnettoma:** Le lesioni dei pazienti sono state proiettate su dati trattografici ad alta risoluzione di soggetti sani (HCP a 7T) per stimare quali tratti di materia bianca fossero interrotti.
- **Riduzione dimensionale (UMAP):** È stato applicato l'algoritmo UMAP (Uniform Manifold Approximation and Projection) per comprimere la complessità delle disconnessioni in uno spazio latente bidimensionale, ovvero il morfospazio.
- **Sviluppo del modello (DSD):** Formule di regressione multipla sono state addestrate in questo morfospazio per prevedere le performance cliniche future e poi confrontate con 6 modelli standard (es. volume della lesione, disconnessione funzionale fMRI, età).

## Risultati
- **Elevata precisione predittiva:** Il modello DSD è stato in grado di prevedere le prestazioni neuropsicologiche dei pazienti su dati non visti con un Errore Assoluto Medio (MAE) inferiore al 20%.
- **Superiorità del DSD:** L'approccio basato sul disconnettoma ha superato in accuratezza ben 6 modelli concorrenti, inclusi quelli basati solo sul volume della lesione, sulla topologia locale o sulla disconnessione funzionale.
- **Atlante della Materia Bianca (NWMA):** Lo studio ha generato il primo atlante che correla specifiche disconnessioni della materia bianca a 86 differenti punteggi cognitivi e comportamentali.
- **Validazione esterna:** La validazione su coorti cliniche esterne ha confermato l'efficacia del modello (es. ottenendo un (R^2 = 0.201) per la fluenza semantica e (R^2 = 0.18) per le abilità visuospaziali).

## Breve Discussione
- Il "disconnettoma" strutturale, arricchito dal metodo UMAP, si rivela un predittore prognostico decisamente più affidabile rispetto alla sola localizzazione del danno o alla connettività funzionale.
- Questo strumento permette di estrarre un profilo neuropsicologico altamente personalizzato per il singolo paziente, fondamentale per pianificare strategie riabilitative e terapeutiche su misura.
- Il rilascio del modello sotto forma di applicazione web gratuita (_Disconnectome Studio_) fornisce una risorsa immediata per l'uso clinico e accademico, con un database che potrà essere costantemente aggiornato in futuro grazie al crowdsourcing globale.


# Bisogno et al. (2021)
_A low-dimensional structure of neurological impairment in stroke_

## Riassunto brevissimo
Tradizionalmente, i deficit causati da ictus vengono classificati come sindromi distinte legate a danni focali,. Questo studio conferma invece che le menomazioni si raggruppano in una "struttura a bassa dimensionalità" (tre cluster principali),. Valutando 237 pazienti con test rapidi eseguibili al letto del malato (NIHSS + OCS), gli autori hanno replicato perfettamente i risultati ottenuti in passato con batterie di test molto lunghe,. Il lavoro dimostra che deficit complessi riflettono un'alterazione diffusa dei network e che una valutazione clinica di soli 15 minuti è sufficiente per catturare in modo robusto queste dimensioni,

---

## Domande scientifiche e Obiettivi
- La struttura a tre fattori dei deficit post-ictus (già osservata in coorti americane con test di oltre 2 ore) è riproducibile in una diversa popolazione clinica utilizzando una valutazione rapida al letto del paziente?,-
- È possibile mappare la neuroanatomia di questi fattori usando un approccio multivariato di _machine learning_ (Ridge Regression) e confermarne la coerenza spaziale?
- **Obiettivo principale:** Validare l'uso combinato di NIHSS e Oxford Cognitive Screen (OCS) come strumento pratico per ricavare "biomarcatori comportamentali" affidabili e applicabili nelle frenetiche _Stroke Unit_,.

## Metodologie

- **Campione:** 237 pazienti al primo ictus (158 con dataset completo) arruolati in modo prospettico in Veneto, valutati nella fase acuta (circa 5 giorni post-ictus),,.
- **Valutazione Comportamentale:** Uso della scala clinica standard NIHSS combinata all'Oxford Cognitive Screen (OCS), un test cognitivo specifico per l'ictus che richiede solo 10-15 minuti,,.
- **Analisi dei dati:** Analisi delle Componenti Principali (PCA) per comprimere i numerosi punteggi clinici in fattori latenti,.
- **Mappatura Anatomica:** Le lesioni (su risonanza o TAC) sono state messe in relazione con i punteggi comportamentali usando modelli multivariati di _Ridge Regression_,.
- **Validazione Esterna:** Tutti i risultati comportamentali e anatomici sono stati confrontati direttamente con la coorte indipendente della Washington University (WU), testata in precedenza con una batteria di 2,5 ore,.

## Risultati
- **Tre dimensioni del deficit:** La PCA ha rivelato che circa il 50% della variabilità clinica è spiegabile da soli 3 fattori: PC1 (linguaggio, calcolo, prassia, memoria e neglect destro), PC2 (deficit motori sinistri, neglect visivo e spaziale sinistro) e PC3 (deficit motori destri),,-.
- **Forte replicabilità comportamentale:** I tre fattori estratti con il test rapido hanno mostrato una straordinaria somiglianza con quelli della batteria estesa della coorte WU,.
- **Forte replicabilità anatomica:** Le mappe di _Ridge Regression_ hanno localizzato questi tre fattori in specifiche aree cortico-sottocorticali, mostrando un'elevata correlazione spaziale con l'anatomia delle lesioni della coorte WU (r = 0.66 per PC1, r = 0.65 per PC2)-.

## Breve Discussione
- I deficit neurologici post-ictus non si presentano come sindromi focali isolate, ma sono strettamente correlati in una struttura a bassa dimensionalità che riflette un danno di network su larga scala,.
- Questa architettura del danno è estremamente stabile e specifica per l'ictus, indipendentemente dalla popolazione studiata, dal tempo trascorso (acuto vs cronico) o dalla batteria di test utilizzata-.
- Mentre la sola scala NIHSS spesso manca di sensibilità per i domini cognitivi, la sua integrazione con il test OCS si è dimostrata uno strumento eccellente e con altissima _compliance_ (completato dall'88% dei pazienti contro il 51% dei test lunghi), ideale per guidare futuri studi di popolazione e trial clinici-.


# Salvalaggio et al. (2020)
_Post-stroke deficit prediction from lesion and indirect structural and functional disconnection_

## Riassunto brevissimo
Questo studio valuta l'accuratezza di diversi approcci di neuroimaging per prevedere i deficit comportamentali post-ictus nella fase subacuta. Analizzando 132 pazienti, gli autori confrontano i modelli predittivi basati sulla lesione focale, sulle stime indirette della disconnessione strutturale (SDC) e funzionale (FDC) – ottenute proiettando la lesione su atlanti sani – e sulla connettività funzionale misurata direttamente con fMRI. 
I risultati dimostrano che la stima della disconnessione strutturale indiretta (SDC) ha un potere predittivo paragonabile alla lesione stessa, mentre la disconnessione funzionale indiretta (FDC) fallisce nel prevedere i deficit, indicando che non può sostituire le vere acquisizioni fMRI.

---

## Domande scientifiche e Obiettivi
- Qual è il valore clinico e predittivo dei nuovi metodi che stimano _indirettamente_ le disconnessioni cerebrali (proiettando le lesioni su connettomi sani) rispetto all'uso delle sole mappe delle lesioni?
- I metodi di disconnessione funzionale indiretta (FDC) possono sostituire le più costose e complesse misurazioni dirette di connettività funzionale (fMRI)?
- **Obiettivo principale:** Valutare e quantificare l'accuratezza nella previsione della variabilità dei deficit post-ictus in molteplici domini (visivo, motorio, linguaggio, memoria, attenzione) utilizzando la lesione anatomica, la SDC, la FDC e, in un sottogruppo, i dati fMRI diretti.

## Metodologie
- **Campione:** 132 pazienti al primo ictus (provenienti dalla coorte della _Washington University_), valutati prospetticamente a 2 settimane di distanza dall'evento acuto in vari domini neuropsicologici. Un sottogruppo di 88 pazienti aveva anche dati completi di fMRI in resting-state.
- **Calcolo delle Disconnessioni Indirette:** Le lesioni segmentate sulle normali risonanze anatomiche sono state proiettate su atlanti ad alta risoluzione del cervello sano per stimare i tratti di materia bianca interrotti (SDC) e i network funzionali disconnessi (FDC).
- **Analisi multivariata:** I dati sono stati compressi tramite Analisi delle Componenti Principali (PCA) e poi inseriti in algoritmi di _machine learning_ (_Ridge Regression_ con validazione _leave-one-out_) per generare previsioni individuali dei punteggi clinici.

## Risultati
- **Lesione e SDC predittive:** Le mappe della lesione e della disconnessione strutturale (SDC) si sono dimostrate capaci di prevedere le alterazioni comportamentali in quasi tutti i domini (attenzione spaziale, linguaggio, deficit visivi e motori), spiegando una varianza (R²) che va dal 16% al 58%. Nessuna delle due è risultata efficace solo per la memoria verbale.
- **Fallimento della FDC:** La mappa di disconnessione funzionale indiretta (FDC) si è rivelata scarsa o nulla nel prevedere i deficit (R² tra 0.01 e 0.18, con l'unica eccezione dei deficit del campo visivo destro), nonostante le reti generate dall'algoritmo sembrassero anatomicamente molto plausibili.
- **Connettività Diretta (fMRI) superiore:** Nel sottogruppo di pazienti analizzati, i cambiamenti diretti misurati con la fMRI hanno previsto i deficit complessi, come quelli del linguaggio (R² = 0.42), con un'accuratezza nettamente superiore alla stima indiretta della FDC (R² = 0.16).

## Breve Discussione
- L'utilizzo della stima indiretta della disconnessione strutturale (SDC) rappresenta uno strumento solido e utile a livello clinico per prevedere l'impatto dell'ictus sull'intero network, raggiungendo una precisione paragonabile all'analisi della lesione anatomica, ma offrendo un quadro più ampio sui tratti danneggiati.
- Il grande vantaggio della SDC è che può essere applicata su normali scansioni cliniche strutturali (senza la necessità di complessi esami di diffusione o fMRI), rendendola accessibile a chiunque.
- Al contrario, le misurazioni indirette della disconnessione funzionale (FDC) non sono dei _proxy_ validi e non catturano adeguatamente la disfunzione dinamica dei network necessaria per fare previsioni, specialmente per i sintomi cognitivi; in questi casi, la misurazione diretta con fMRI rimane insostituibile.


# Griffis et al. (2020)
_Damage to the shortest structural paths between brain regions is associated with disruptions of resting-state functional connectivity after stroke_

## Riassunto brevissimo
Questo studio esamina come le lesioni cerebrali focali alterino la connettività funzionale a riposo (FC) attraverso disconnessioni strutturali sia dirette che indirette. 
Analizzando 114 pazienti con ictus in fase subacuta, gli autori stimano l'impatto del danno proiettando le lesioni su un atlante trattografico derivato da individui sani.
I risultati dimostrano che la FC subisce gravi alterazioni non solo quando le connessioni strutturali dirette vengono distrutte, ma anche quando la lesione va ad allungare i "percorsi strutturali più brevi" (Shortest Structural Path Length, SSPL) tra due regioni, creando una disconnessione indiretta. Entrambe le disconnessioni compromettono significativamente l'attività e la sincronizzazione delle reti cerebrali.

---

## Domande scientifiche e Obiettivi
- Quali sono i precisi meccanismi strutturali alla base delle interruzioni della connettività funzionale (FC) causate da lesioni cerebrali focali?
- In che modo i danni focali alterano la comunicazione funzionale globale, specialmente tra regioni che non sono collegate direttamente da fasci di materia bianca ma si affidano a percorsi indiretti?
- **Obiettivo principale:** Stimare l'impatto dell'ictus sul connettoma strutturale e testare l'ipotesi che l'aumento della distanza nei percorsi strutturali (danno alle connessioni intermedie o "disconnessione indiretta") contribuisca in modo significativo alle alterazioni della connettività funzionale post-ictus, analogamente alle disconnessioni dirette.

## Metodologie
- **Campione:** 114 pazienti al primo ictus, valutati in fase subacuta (media di circa 13 giorni dall'evento), e 24 controlli sani della _Washington University_.
- **Creazione del Connettoma Strutturale:** È stato utilizzato l'atlante trattografico HCP-842 (costruito sui dati di 842 soggetti sani) combinato con la parcellizzazione corticale Gordon (324 regioni) e alcune aree sottocorticali.
- **Calcolo delle Disconnessioni:** Le lesioni dei pazienti sono state incorporate nell'atlante per determinare le _disconnessioni strutturali dirette_ (numero di fibre interrotte dalla lesione). Applicando la teoria dei grafi, gli autori hanno misurato poi le _disconnessioni strutturali indirette_, calcolate quando una lesione causava un aumento nella lunghezza del percorso strutturale più breve (SSPL) necessario per far comunicare due regioni tra loro non adiacenti.
- **Analisi Funzionale:** Utilizzando dati fMRI resting-state, i ricercatori hanno applicato analisi della varianza (ANOVA a tre vie) per valutare i cambiamenti della FC, confrontando reti di regioni con connessioni risparmiate rispetto a regioni colpite da disconnessione diretta o indiretta.

## Risultati
- **Danno esteso su larga scala:** In media, circa il 20% di tutte le possibili coppie di regioni cerebrali in un paziente ha subito una disconnessione strutturale diretta o indiretta; le disconnessioni più estese derivavano principalmente dai danni localizzati nella materia bianca profonda.
- **Impatto funzionale a cascata:** Sia le regioni che hanno subito una disconnessione strutturale _diretta_, sia quelle che hanno subito una disconnessione _indiretta_, hanno mostrato deficit di connettività funzionale significativamente più severi rispetto alle regioni con percorsi intatti.
- **Gerarchia del danno:** Sebbene le disconnessioni indirette siano risultate determinanti, l'interruzione funzionale più grave (maggiore crollo della FC) è stata generalmente registrata tra le coppie di regioni colpite da disconnessioni strutturali _dirette_.

## Breve Discussione
- Le lesioni cerebrali innescano conseguenze ben oltre la zona necrotica primaria: i danni ai collegamenti strutturali intermedi allontanano "topologicamente" le regioni intatte, interferendo gravemente con la normale trasmissione di segnali in rete.
- I risultati espandono il concetto classico di "diaschisi" (la disfunzione remota dovuta a un danno focale), indicando chiaramente che queste alterazioni dipendono dai percorsi strutturali indiretti di materia bianca.
- Calcolare l'aumento della distanza nei percorsi strutturali più brevi (SSPL) offre una spiegazione meccanicistica molto più potente e completa per le anomalie funzionali a livello di network rispetto alla sola misurazione del volume o della topologia della lesione corticale focale.

# Bonkhoff et al. (2020)
_Acute ischaemic stroke alters the brain's preference for distinct dynamic connectivity states_

## Riassunto brevissimo
Questo studio utilizza la risonanza magnetica funzionale (fMRI) a riposo con un approccio _dinamico_ (ad alta risoluzione temporale) per esplorare come l'ictus ischemico acuto alteri le reti del sistema motorio. 
Analizzando 31 pazienti e 17 controlli sani, gli autori scoprono tre "stati di connettività" transitori. 
I risultati dimostrano che l'ictus non altera solo la connettività globale in modo statico, ma modifica le preferenze temporali del cervello per specifici stati di attivazione, rivelando pattern nettamente diversi basati sulla gravità del deficit motorio iniziale (moderato vs grave) che i metodi classici non riuscivano a cogliere.

---

## Domande scientifiche e Obiettivi
- In che modo l'ictus ischemico acuto altera le fluttuazioni temporali della connettività (connettività funzionale dinamica, dFNC) all'interno delle reti cerebrali motorie rispetto alle classiche misurazioni "statiche" (che mediano il segnale sull'intera scansione)?
- Le alterazioni nelle configurazioni dinamiche della connettività sono correlate alla gravità clinica del deficit (es. moderato vs grave)?
- **Obiettivo principale:** Utilizzare un'analisi a "finestra scorrevole" (_sliding window_) sui dati fMRI resting-state per identificare stati transitori di connettività e capire come le reti si riorganizzino dinamicamente nella primissima fase post-ictus.

## Metodologie
- **Campione:** 31 pazienti con un primo ictus ischemico acuto (scansionati in media a 7 giorni dall'esordio) con deficit motori alla mano (18 moderati, 13 gravi) e 17 controlli sani abbinati per età.
- **Connettività Dinamica (dFNC):** A differenza della connettività statica, la dFNC è stata stimata analizzando i dati fMRI tramite finestre temporali di 44 secondi, fatte scorrere lungo tutto il tempo della scansione per valutare i cambiamenti di rete secondo per secondo.
- **Clustering:** È stato applicato un algoritmo di apprendimento non supervisionato (_k-means clustering_) su tutte le finestre temporali per raggruppare i pattern di connettività ricorrenti. Questa analisi ha permesso di individuare 3 specifici "stati di connettività".
- **Metriche:** Sono state misurate svariate dinamiche: il tempo di permanenza in uno stato (_dwell time_), la frequenza globale (_fraction time_), il numero di transizioni tra stati e un indice di segregazione dei network.

## Risultati
- **Tre stati dinamici:** Sono state identificate tre configurazioni temporali: Stato 1 (densamente connesso localmente e altamente segregato tra domini diversi), Stato 2 (debolmente connesso, sia localmente che a distanza) e Stato 3 (intermedio, con caratteristiche simili alla connettività statica).
- **Pazienti moderati:** I pazienti con deficit motorio moderato hanno trascorso un tempo significativamente maggiore (sia in termini di frequenza che di permanenza continua) nello Stato 2 (connettività debole e bassa segregazione) rispetto ai controlli e ai pazienti gravi.
- **Pazienti gravi:** I pazienti con deficit grave hanno mostrato una maggiore probabilità di transitare verso lo Stato 1 (spazialmente molto segregato, con forte disconnessione tra reti appartenenti a domini cerebrali diversi).
- **Superiorità dell'analisi dinamica:** A differenza dell'approccio dinamico, la classica analisi fMRI statica _non_ è riuscita a rilevare alcuna differenza significativa nella segregazione globale dei network tra i vari gruppi, omettendo così dettagli cruciali sulle riorganizzazioni in corso.

## Breve Discussione
- L'ictus acuto non riduce solo le connessioni fisiche o funzionali statiche, ma altera profondamente la flessibilità temporale della rete, ovvero la "preferenza" del cervello nel transitare e sostare tra i vari stati di connettività.
- La preferenza dei pazienti gravi per uno stato altamente segregato (Stato 1) potrebbe riflettere un primo tentativo di riorganizzazione o compensazione mirata per recuperare le funzioni perse (isolando le reti compromesse). Al contrario, la bassa segregazione nei pazienti moderati (Stato 2) potrebbe rappresentare una firma di plasticità precoce in cui reti meno vincolate facilitano lo stabilirsi di nuove connessioni flessibili.
- L'approccio dFNC si rivela un biomarcatore estremamente più sensibile della connettività statica. Capire queste dinamiche temporali apre nuove prospettive sui meccanismi neurali del recupero, fornendo informazioni critiche che un giorno potrebbero guidare interventi di neuromodulazione precoce (es. rTMS, tDCS) per favorire le traiettorie riabilitative ottimali.


# Griffis et al. (2019) 
_Structural Disconnections Explain Brain Network Dysfunction after Stroke_

## Riassunto brevissimo
Questo studio sfida l'assunto tradizionale secondo cui le disfunzioni delle reti cerebrali post-ictus (misurate tramite fMRI) derivino principalmente dal danno locale a specifiche regioni critiche di materia grigia. 
Analizzando 114 pazienti, gli autori dimostrano invece che le alterazioni della connettività funzionale dipendono in modo preponderante dalla disconnessione strutturale (SDC) dei fasci di materia bianca. 
I risultati evidenziano che le disconnessioni fisiche dei tratti, in particolare quelli interemisferici, causano diffuse interruzioni funzionali a cascata, spiegando il crollo della modularità e dell'integrazione delle reti molto meglio di quanto non faccia il danno locale alla corteccia.

---

## Domande scientifiche e Obiettivi
- Le disfunzioni delle reti cerebrali (alterazioni della connettività funzionale) che seguono un ictus focale sono causate principalmente dal danno locale alla materia grigia (compresi i cosiddetti "hub" corticali) o dall'interruzione delle connessioni di materia bianca?
- Esiste una relazione coerente e topografica tra i pattern di disconnessione strutturale (SDC) e il crollo della connettività funzionale (FC)?
- **Obiettivo principale:** Confrontare direttamente il potere esplicativo dei modelli basati sul danno locale (materia grigia) con quelli basati sulle disconnessioni strutturali della materia bianca, per spiegare i deficit di connettività funzionale a riposo.

## Metodologie

- **Campione:** 114 pazienti con ictus in fase subacuta (circa 1-2 settimane dall'evento) valutati con risonanza magnetica strutturale e funzionale (fMRI resting-state).
- **Mappatura del danno e delle disconnessioni:** Le lesioni sono state mappate calcolando sia il danno focale diretto (a livello di voxel e di regioni di materia grigia/hub), sia proiettandole su un atlante trattografico di soggetti sani per stimare le disconnessioni strutturali (SDC) dei tratti di materia bianca.
- **Analisi Statistiche (PLSR e PLSC):** È stata utilizzata la _Partial Least Squares Regression_ (PLSR) per stabilire se il danno locale o le SDC prevedessero meglio le alterazioni di FC (es. calo della modularità). Successivamente, la _Partial Least Squares Correlation_ (PLSC) è stata impiegata per estrarre le variabili latenti e analizzare la covarianza multivariata tra i pattern strutturali e quelli funzionali.

## Risultati
- **Superiorità delle SDC:** I modelli basati sulle disconnessioni strutturali (SDC) hanno spiegato in modo nettamente superiore le disfunzioni di rete post-ictus rispetto ai modelli basati sul danno focale alla materia grigia o agli "hub" (nodi centrali) corticali.
- **Il ruolo chiave delle fibre interemisferiche:** Le disconnessioni strutturali interemisferiche si sono rivelate le principali responsabili delle diffuse interruzioni della connettività funzionale, portando a una riduzione globale dell'integrazione e della segregazione all'interno e tra i network.
- **Relazione topografica a bassa dimensionalità:** L'analisi PLSC ha rivelato che i pattern di disconnessione strutturale e di disfunzione funzionale sono strettamente collegati da una struttura a bassa dimensionalità (una singola componente latente spiegava ben il 45% della varianza), dimostrando una sovrapposizione topografica tra l'interruzione del cavo fisico e l'anomalia di comunicazione funzionale.

## Breve Discussione
- Il paper ribalta un dogma classico: non è la "morte" o il danno del tessuto corticale in sé a generare i più gravi deficit di network su larga scala, ma la recisione dei "cavi di comunicazione" di materia bianca che collegano le aree intatte.
- Le lesioni focali innescano una disfunzione globale e stereotipata (perdita di modularità) che dipende intimamente dall'architettura delle connessioni strutturali distrutte, con i tratti interemisferici che giocano un ruolo critico.
- L'inclusione delle stime di disconnessione della materia bianca è un passo imprescindibile per comprendere le basi neurali dei deficit funzionali post-ictus; basarsi unicamente sulla posizione della lesione corticale fornisce un quadro parziale e con minor potere esplicativo.

# Siegel et al. (2016) - Siegel et al. (2018)
- *Disruptions of network connectivity predict impairment in multiple behavioral domains after stroke*
- *Re-emergence of modular brain networks in stroke recovery*

## Riassunto brevissimo
Questi due lavori complementari dimostrano che l'ictus non causa solo danni focali, ma altera profondamente l'organizzazione globale e dinamica dei network cerebrali. Nel 2016, gli autori scoprono che la disfunzione dei network (misurata con fMRI) predice i deficit cognitivi complessi (come la memoria) molto meglio della sola mappa strutturale della lesione, che è invece più accurata per i deficit sensomotori. Nel 2018, lo studio longitudinale rivela che l'architettura dei network, in particolare la loro "modularità", crolla nella fase acuta ma riemerge progressivamente nel tempo. Fondamentalmente, il ripristino di questa modularità va di pari passo con il recupero clinico delle funzioni cognitive superiori (linguaggio, memoria, attenzione), ma non di quelle motorie o visive.

---

## Domande scientifiche e Obiettivi
- Le lesioni anatomiche strutturali e le alterazioni della connettività funzionale (FC) predicono in modo diverso l'impatto dell'ictus su svariati domini comportamentali?
- Come cambia l'architettura globale del cervello, in termini di integrazione e segregazione ("modularità"), durante le diverse fasi del recupero post-ictus?
- C'è una correlazione tra il ripristino della normale architettura di rete (modularità) e il recupero clinico del paziente in domini specifici?
- **Obiettivo combinato:** Collegare le caratteristiche organizzative su larga scala dei network cerebrali ai deficit iniziali (2016) e mapparne l'evoluzione nel tempo per prevedere le traiettorie di guarigione (2018).

## Metodologie
- **Campione:** Un'ampia coorte di 132 pazienti con ictus valutati inizialmente (nel paper del 2016) e seguiti longitudinalmente a 2 settimane (n=107), 3 mesi (n=85) e 1 anno (n=67) per il paper del 2018, confrontati con controlli sani abbinati.
- **Valutazione Comportamentale:** È stata somministrata un'estesa batteria di test in molteplici domini (attenzione, memoria verbale e visiva, linguaggio, motricità e visione), poi ridotta tramite Analisi delle Componenti Principali (PCA) in punteggi globali per dominio.
- **Neuroimaging e Machine Learning (2016):** Sono state acquisite risonanze strutturali e funzionali (fMRI a riposo). Gli autori hanno utilizzato modelli di _machine learning_ (Ridge Regression e Multi-Task Learning) per prevedere il grado di deficit neurologico di ogni singolo soggetto partendo o dalla topografia della lesione o dalla connettività funzionale.
- **Analisi Longitudinale dei Grafi (2018):** Utilizzando la teoria dei grafi, i ricercatori hanno calcolato la "modularità" dei network nel corso del tempo, ovvero la misura in cui i sistemi cerebrali mostrano un'alta integrazione (connessioni dense al proprio interno) e un'alta segregazione (poche connessioni verso altre reti).

## Risultati

- **Doppia dissociazione predittiva (2016):** I deficit di memoria (visiva e verbale) sono previsti in modo decisamente migliore dalle alterazioni della connettività funzionale. Al contrario, i danni motori e visivi sono previsti meglio dalla topografia della lesione strutturale. L'attenzione e il linguaggio sono ben predetti da entrambi gli approcci.
- **Alterazione globale dei network (2016 e 2018):** L'ictus causa un pattern generale di disfunzione di rete caratterizzato dalla diminuzione dell'integrazione interemisferica e dalla perdita di segregazione intraemisferica. Questa perdita di architettura modulare si presenta già in fase subacuta.
- **Recupero della Modularità (2018):** Mentre le aree corticali mantengono i loro confini anatomici, la modularità dei sistemi cerebrali, gravemente compromessa a due settimane dall'evento, mostra un recupero significativo a 3 mesi e fino a 1 anno di distanza.
- **Correlazione con la clinica (2018):** Il progressivo recupero della modularità correla fortemente con il recupero dei deficit di linguaggio, memoria spaziale e attenzione. Al contrario, non vi è associazione significativa tra il recupero della modularità globale e il recupero delle funzioni più basiche, come quelle motorie o visive.

## Breve Discussione

- Questi studi stabiliscono un principio fondamentale nella neurobiologia dell'ictus: mentre le funzioni sensomotorie primarie dipendono in gran parte dall'integrità anatomica di aree e fasci specifici, le funzioni cognitive superiori (come la memoria, l'attenzione e il linguaggio) emergono dalla complessa e flessibile interazione di network distribuiti.
- Il cervello sano si affida a un'architettura "modulare" ad alta efficienza; la distruzione e la successiva "riemersione" di questa modularità (ovvero la capacità delle reti di tornare a comunicare bene al proprio interno e a isolarsi correttamente dalle altre) rappresenta un potentissimo biomarcatore fisiologico per il recupero cognitivo.
- A livello clinico e terapeutico, questi dati suggeriscono che le future strategie di riabilitazione orientate al recupero delle funzioni cognitive superiori non dovrebbero limitarsi a stimolare l'area perilesionale, ma dovrebbero mirare a normalizzare il flusso di informazioni e l'organizzazione dei sistemi cerebrali su larga scala.

# Corbetta et al. (2015)
_Common Behavioral Clusters and Subcortical Anatomy in Stroke_

## Riassunto brevissimo
Questo studio fondamentale sfida la visione neurologica tradizionale secondo cui l'ictus causa sindromi comportamentali altamente specifiche dovute a danni corticali focali. 
Analizzando 132 pazienti in fase subacuta (1-2 settimane dall'evento), gli autori dimostrano che i deficit post-ictus sono in realtà fortemente correlati tra loro e si raggruppano in un numero ridotto di "cluster" comportamentali. Inoltre, la topografia tipica dell'ictus non è corticale, ma prevalentemente sottocorticale e coinvolge massicciamente la materia bianca. 
I risultati evidenziano che la mera localizzazione del danno strutturale predice molto bene i deficit motori e linguistici, ma è meno efficace per memoria e attenzione, sottolineando il ruolo critico e spesso sottovalutato delle disconnessioni della materia bianca nel generare deficit multipli.

---

## Domande scientifiche e Obiettivi
- I deficit neurologici post-ictus si presentano davvero come sindromi modulari e isolate, o sono fortemente correlati tra loro all'interno della popolazione?
- Qual è la topografia anatomica reale dell'ictus in un ampio campione clinico rappresentativo?
- Quanto della variabilità dei deficit in diversi domini (motorio, linguaggio, memoria, attenzione) può essere spiegata unicamente dalla localizzazione spaziale del danno strutturale?
- **Obiettivo principale:** Utilizzare un approccio multivariato (_machine learning_) per esaminare le relazioni tra lesione e comportamento su domini multipli, al fine di quantificare la varianza clinica spiegata dal danno anatomico strutturale.

## Metodologie

- **Campione:** 132 pazienti al primo ictus (ischemico o emorragico), valutati in modo prospettico nella fase acuta/subacuta (1-2 settimane dall'esordio), e confrontati con un gruppo di controlli sani.
- **Valutazione Comportamentale:** È stata somministrata un'ampia batteria di test per misurare attenzione, memoria (verbale e spaziale), linguaggio, funzioni motorie e visive. I dati clinici sono stati poi compressi tramite Analisi delle Componenti Principali (PCA) per individuare fattori comportamentali latenti all'interno e trasversalmente ai domini.
- **Mappatura Anatomica:** Le lesioni sono state segmentate su risonanze strutturali (T1, T2, FLAIR) e classificate. Per studiare le disconnessioni, i danni sono stati sovrapposti a un atlante probabilistico trattografico di cervelli sani.
- **Machine Learning:** È stato utilizzato un algoritmo multivariato di _Ridge Regression_ (con validazione _leave-one-out_) per prevedere i punteggi comportamentali individuali partendo unicamente dai voxel danneggiati, permettendo di quantificare la percentuale esatta di varianza clinica spiegata dall'anatomia.

## Risultati

- **Tre macro-cluster comportamentali:** L'analisi trasversale sui domini ha rivelato che ben il 69% della variabilità clinica globale si riduce a soli tre macro-fattori correlati ("uber-factors"): (1) linguaggio associato a memoria verbale e spaziale, (2) deficit motori sinistri associati a bias del campo visivo e prestazioni attentive generali, e (3) deficit motori destri associati ad attenzione spaziale.
- **Danno prevalentemente sottocorticale:** La topografia tipica dell'ictus ha mostrato che le lesioni puramente corticali sono rare (solo il 13%). La maggioranza dei danni si concentra nei gangli della base, nel talamo e, in ben il 39% dei casi, nella materia bianca sottocorticale.
- **Potere predittivo della struttura:** La sola localizzazione del danno (dati di _Ridge Regression_) ha spiegato in modo eccellente la varianza dei deficit motori (fino al 54%) e del linguaggio (44%), ma ha previsto in modo assai più debole i deficit di attenzione (34%) e di memoria (solo il 17%).
- **Disconnessione ai crocevia:** Le regioni in cui il danno strutturale causava i deficit più severi e multipli (in 5 o 6 domini contemporaneamente) corrispondevano in modo quasi perfetto ai "crocevia" della materia bianca profonda (come il fascicolo longitudinale superiore o il tratto cortico-spinale), dove transitano e si sovrappongono numerosi tratti di fibre.

## Breve Discussione
- Mentre la neurologia storica si è concentrata su casi rari di pazienti con lesioni corticali focali che mostrano sindromi "pure", la stragrande maggioranza dei pazienti clinici (la "massa dell'iceberg") presenta deficit fortemente correlati.
- Questa correlazione non deriva dalla morte della corteccia in sé, ma dalla natura concentrica dell'ictus che recide prevalentemente le "autostrade" della materia bianca (i tratti sottocorticali) che collegano le diverse reti cerebrali.
- Vi è una fondamentale distinzione neurobiologica: funzioni come il movimento e il linguaggio dipendono ancora fortemente dall'integrità strutturale di vie specifiche (es. fascio cortico-spinale). Al contrario, funzioni cognitive distribuite come la memoria e l'attenzione dipendono da network globali, per i quali il semplice danno strutturale focale non è sufficiente a spiegare il deficit clinico. Questo lavoro ha quindi posto le basi fisiologiche per comprendere la necessità di esplorare le disconnessioni di rete (es. con fMRI, come faranno i successivi lavori di Siegel et al., 2016 e Griffis et al., 2019) per capire i danni cognitivi complessi.

Cinetto et al. (Manoscritto in bozza) _Clinical variables surpass lesion and disconnection features predicting multi-domain stroke outcomes_

## Riassunto brevissimo

Questo studio affronta la sfida della prognosi a lungo termine post-ictus. I ricercatori hanno valutato in modo sistematico se l'aggiunta di complesse metriche di neuroimaging (topografia della lesione e stime di disconnessione strutturale a livello dell'intero cervello) migliori la previsione del recupero rispetto all'uso delle sole variabili cliniche e demografiche di base. Tracciando 199 pazienti su otto domini funzionali per un anno, lo studio dimostra (come suggerisce chiaramente il titolo) che i dati clinici e demografici superano le complesse misurazioni del danno e delle disconnessioni anatomiche nel prevedere gli esiti a lungo termine.

---

## Domande scientifiche e Obiettivi

- Qual è il reale valore prognostico aggiuntivo (incrementale) delle mappe avanzate di lesione e di disconnessione strutturale (SDC) rispetto ai predittori clinici standard (es. punteggio NIHSS, età)?
- È possibile prevedere in modo affidabile il recupero del paziente non in un singolo dominio, ma trasversalmente in **molteplici domini cognitivi e funzionali** all'interno della stessa coorte clinica?
- **Obiettivo principale:** Confrontare testa a testa e in modo gerarchico l'accuratezza predittiva di 4 categorie di dati (demografici, clinico-neurologici acuti, topografia della lesione e disconnettoma) per stimare gli esiti dei pazienti a 2 settimane, 3 mesi e 12 mesi di distanza dall'ictus.

## Metodologie

- **Campione:** Una coorte prospettica di 199 pazienti al primo ictus (età 19-83 anni) e 68 controlli sani abbinati per età e istruzione.
- **Elaborazione Neuroimaging:** Le lesioni dei pazienti sono state segmentate su scansioni anatomiche standard e proiettate su un connettoma sano (derivato da 178 soggetti dello _Human Connectome Project_) utilizzando il _BCB Toolkit_. Questo ha generato mappe probabilistiche indirette dei tratti di materia bianca disconnessi (SDC) per ogni paziente.
- **Modellistica Predittiva (Machine Learning):** La vastissima quantità di dati spaziali (lesioni e SDC) è stata compressa utilizzando un'Analisi delle Componenti Principali (PCA). Successivamente, è stato applicato un algoritmo di _Ridge Regression_ con validazione incrociata per prevedere i punteggi in ben **otto domini** (motorio destro/sinistro, linguaggio, attenzione generale e spaziale, memoria verbale e spaziale, e indipendenza funzionale). I predittori sono stati inseriti nel modello a strati (partendo dalle basi demografiche fino ai dati di neuroimaging) per testarne il valore aggiunto.

## Risultati

- **Fattori latenti di danno:** L'analisi PCA sulle mappe ha catturato in modo eccellente le distribuzioni tipiche dei danni da ictus. Per le lesioni, ha distinto gli ictus emisferici (destra vs sinistra) e l'interessamento dell'arteria cerebrale media. Per le disconnessioni (SDC), ha estratto modelli tipici di danno ai grandi fasci di materia bianca, come il corpo calloso, il tratto cortico-spinale, il fascicolo arcuato e il fascicolo fronto-occipitale inferiore.
- **Superiorità della clinica:** Come anticipato programmaticamente dal titolo del manoscritto, nella competizione "testa a testa" le variabili cliniche misurate nella fase acuta (come la gravità misurata dalla scala NIHSS o il lato della lesione) combinate alle caratteristiche demografiche, hanno superato le sofisticate metriche del danno anatomico (lesione) e del disconnettoma (SDC) nel prevedere l'andamento del paziente nei mesi successivi.

## Breve Discussione

- Il paper lancia un messaggio clinico di forte impatto (in leggero contrasto o integrazione rispetto agli studi precedenti di questo gruppo): sebbene la stima dettagliata del "disconnettoma" e della topografia della lesione offra preziose intuizioni sui meccanismi patofisiologici dell'ictus, per quanto riguarda la pura **previsione degli esiti clinici**, i fattori tradizionali rimangono superiori.
- I modelli predittivi più complessi e ad alta dimensionalità non battono le variabili standard raccolte al letto del paziente. Fattori come l'età, l'educazione e la severità clinica acuta misurata con l'NIHSS inglobano già al loro interno l'effetto del danno neurale e sono sufficienti (e persino migliori) per stimare con successo le traiettorie di recupero multi-dominio del paziente.