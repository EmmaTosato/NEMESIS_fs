
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
---

# Santoro et al. (2026)
_Individual connectome fingerprints reveal early stabilization and long-term circuit remodeling after stroke_

## Riassunto brevissimo
Questo studio longitudinale analizza l'evoluzione dei pattern di connettività cerebrale specifici del singolo individuo ("brain fingerprints") durante il primo anno post-ictus. Nonostante lo scostamento persistente dall'architettura sana, il connettoma funzionale unico di ciascun paziente si stabilizza precocemente, entro sole tre settimane dall'evento. Questa precoce stabilizzazione a livello globale maschera un rimodellamento a lungo termine specifico per ciascuna rete (con aumento iniziale nei sistemi sensoriali/attentivi e declino in quelli associativi di alto livello), guidato da una riconfigurazione funzionale dinamica che avviene al di sopra di una lesione strutturale stabile.

---

## Domande scientifiche e Obiettivi
- In che modo l'ictus altera nel tempo le caratteristiche di connettività uniche e specifiche del singolo individuo ("impronte digitali" del connettoma funzionale)?
- Come si articola la relazione dinamica tra un danno strutturale sostanzialmente statico (la lesione biologica) e un fenotipo funzionale plastico e mutevole durante il recupero?
- **Obiettivo principale:** Tracciare l'evoluzione temporale delle impronte digitali connettomiche dei pazienti post-ictus nel primo anno dall'evento, valutando la loro stabilità, il rimodellamento dei circuiti a livello di rete e il loro valore prognostico per i deficit cognitivi cronici.

## Metodologie
- **Campione e disegno longitudinale:** Valutazione longitudinale di pazienti post-ictus seguiti in quattro sessioni temporali chiave: T1 (fase acuta, ~1 settimana), T2 (fase subacuta precoce, ~3 settimane), T3 (fase subacuta tardiva, ~3 mesi) e T4 (fase cronica, ~1 anno), confrontati con soggetti sani di controllo.
- **Brain Fingerprinting (Impronte cerebrali):** Calcolo di due indici connettomici principali: (1) `Iclinical` (clinical similarity) per misurare la somiglianza globale del connettoma del paziente rispetto a un gruppo di controllo sano; (2) `Iself` (self-identifiability) per valutare quanto la connettività di ogni singolo paziente rimanga stabile e riconoscibile nel tempo rispetto al proprio baseline cronico (T4).
- **Residualizzazione e Teoria dei Grafi:** Le matrici di connettività funzionale (FC) sono state residualizzate per eliminare l'effetto di confondi come età, sesso e volume della lesione; le analisi a livello di rete si sono basate sulle sette reti canoniche di Yeo (visiva, somatomotoria, attenzione dorsale/ventrale, limbica, frontoparietale, default mode) e strutture sottocorticali.
- **Struttura-Funzione ed Embedding:** Analisi congiunta di matrici strutturali (SC, da risonanza di diffusione) e funzionali (FC, da fMRI resting-state) per mappare lo scostamento e il progressivo riavvicinamento dei pazienti verso il manifold di connettività dei soggetti sani.
- **Predizione multivariata:** Addestramento di modelli di _machine learning_ per verificare se le impronte funzionali precoci (T1-T2) potessero prevedere i punteggi clinico-comportamentali cronici a un anno di distanza.

## Risultati
- **Stabilizzazione precoce del fingerprint:** Anche se l'ictus allontana bruscamente il cervello dall'architettura sana (riduzione di `Iclinical` a tutti i timepoint), il connettoma funzionale specifico di ciascun paziente si consolida precocemente, mostrando un forte incremento di somiglianza a se stesso (`Iself`) già a partire da T2 (3 settimane post-ictus).
- **Rimodellamento dei circuiti specifico per sistema:** Sotto la stabilità globale si nasconde una complessa riorganizzazione. I sistemi somatomotori (SM) e di attenzione ventrale (VA) mostrano forti variazioni e riconfigurazioni rapide nelle prime 3 settimane (T1 \(\rightarrow\) T2). Successivamente, si osserva un declino graduale di connettività nelle reti associative di alto livello (es. Default Mode Network, DMN e rete frontoparietale, FPN).
- **Dissociazione struttura-funzione:** La similarità strutturale (SC) con i soggetti sani rimane fissa e invariata nel tempo (lesione stabile), mentre la similarità funzionale (FC) aumenta in modo continuo, riflettendo una plasticità dinamica "sopra" lo scheletro strutturale danneggiato.
- **Predittività prognostica delle impronte precoci:** Le "firme" funzionali acute sono altamente informative e predicono in modo selettivo le performance cognitive a lungo termine (a 1 anno) in domini neuropsicologici complessi come il linguaggio, le funzioni esecutive e l'attenzione.

## Breve Discussione
- Il connettoma post-ictus si comporta come un sistema dinamico vincolato: la lesione strutturale rigida impone dei limiti alla riorganizzazione, ma la dinamica funzionale conserva una flessibilità sufficiente per stabilire una nuova configurazione stabile personale (fingerprint consolidato a 3 settimane).
- Questo studio evidenzia l'importanza clinica del brain fingerprinting: lungi dall'essere solo rumore o disorganizzazione caotica, il connettoma rimodellato acutamente rappresenta un'impronta stabile e individuale, che racchiude informazioni cruciali sulla futura traiettoria di recupero del paziente.
- L'individuazione di questa precoce identità funzionale consolidata offre ai clinici una finestra temporale ottimale (entro le prime tre settimane) per ricavare biomarcatori prognostici stabili e personalizzare gli interventi riabilitativi o di neurostimolazione precoce.

---
# Pini et al. (2026)  
_Longitudinal Degeneration of Microstructural and Structural Connectivity Patterns Following Stroke_

### ## Riassunto brevissimo
- **Degenerazione progressiva a lungo termine**: Lo studio monitora longitudinalmente l'evoluzione della materia bianca (WM) post-ictus a `$2$` settimane (fase subacuta) e a `$3$` mesi (fase cronica) dall'evento, dimostrando che il danno strutturale a distanza e la degenerazione microstrutturale continuano a progredire nel tempo, estendendosi ben oltre la lesione iniziale e coinvolgendo anche l'emisfero sano (contralesionale).
- **Doppia dissociazione struttura-comportamento**: I risultati rivelano che le alterazioni globali della connettività strutturale (SC) sono associate a deficit cognitivi (ma non motori) esclusivamente nella fase acuta. Al contrario, le alterazioni microstrutturali locali all'interno dei tratti disconnessi (in particolare il fascio corticospinale) predicono stabilmente e a lungo termine i deficit motori controlaterali sia a `$2$` settimane sia a `$3$` mesi.
- **Disaccoppiamento della traiettoria strutturale**: Mentre la connettività funzionale (FC) tende storicamente a normalizzarsi in parallelo al recupero comportamentale, la connettività strutturale (SC) mostra una traiettoria divergente di progressiva degenerazione, suggerendo che il recupero clinico tardivo si basa sul ricalibramento funzionale e sinaptico dei circuiti superstiti piuttosto che su una restaurazione strutturale del connettoma.

---

### ## Domande scientifiche e Obiettivi
- In che modo le alterazioni della connettività strutturale globale (SC) e le alterazioni microstrutturali locali (DTI e NODDI) mostrano traiettorie temporali accoppiate o divergenti post-ictus?
- La degenerazione progressiva a lungo termine della materia bianca a distanza dalla lesione iniziale (connectional diaschisis strutturale) spiega le differenze interindividuali nella traiettoria di recupero cognitivo e motorio dei pazienti?
- **Obiettivo principale**: Integrare in un unico modello quantitativo e longitudinale la riorganizzazione globale della connettività strutturale (tramite gradienti di trattografia) e la degenerazione microstrutturale locale dei tratti disconnessi per mappare sistematicamente la relazione tra integrità del trattoma e traiettorie comportamentali a `$2$` settimane e `$3$` mesi post-ictus.

---

### ## Metodologie
- **Campione**: Studio prospettico longitudinale su `$79$` pazienti con primo ictus ischemico o emorragico (di cui `$48$` valutati con risonanza magnetica a `$2$` settimane e `$26$` che hanno ripetuto la scansione a `$3$` mesi) confrontati con `$33$` controlli sani abbinati.
- **Fattori Comportamentali Latenti**: Una vasta batteria neuropsicologica multivariata (motorio, linguaggio, attenzione, neglect e memoria) è stata ridotta tramite analisi fattoriale latente in `$5$` macro-fattori, spiegando circa il `$50\%$` della varianza comportamentale complessiva.
- **Gradienti di Connettività Strutturale (SC)**: Calcolo di matrici strutturali a partire da trattografia probabilistica dell'intero cervello (con `$10$` milioni di linee di flusso e raffinamento `$SIFT2$`) proiettate su uno spazio di embedding a bassa dimensionalità (_diffusion map embedding_) per estrarre i primi `$3$` gradienti strutturali principali (intra- ed inter-emisferici). La deviazione individuale dal connettoma di controllo sano è stata quantificata tramite la metrica di _Gradient Divergence_ (\(GD\)).
- **Modellazione Microstrutturale Locale (DTI-NODDI)**: Estrazione voxel-wise di parametri di diffusione DTI (fractional anisotropy `$FA$`, mean diffusivity `$MD$`, axial diffusivity `$AD$`, radial diffusivity `$RD$`) e NODDI (neurite density index `$NDI$`/`$ICVF$`, orientation dispersion index `$ODI$`, isotropic volume fraction `$ISOVF$`). I parametri sono stati sintetizzati tramite analisi fattoriale in `$3$` mappe latenti stabili: `$dwiF1$` (acqua libera), `$dwiF2$` (anisotropia e dispersione dell'orientamento delle fibre) e `$dwiF3$` (mielinizzazione).
- **Disconnessione Strutturale (SDC)**: Le lesioni di ciascun paziente sono state proiettate su un connettoma sano di riferimento per stimare le mappe di disconnessione strutturale probabilistica (SDC) e tracciare i tratti di sostanza bianca disconnessi a diverse soglie (`$40\%$`, `$60\%$`, `$80\%$`).
- **Analisi Statistiche**: Utilizzo di Modelli Lineari a Effetti Misti (LMM) per analizzare la degenerazione strutturale e microstrutturale longitudinale (subacuto vs. cronico) controllando per covariate demografiche, e regressioni lineari robuste con bootstrapping (`$n = 1000$`) per associare i dati di neuroimaging ai fattori comportamentali.

---

### ## Risultati
- **Gradienti e mappe microstrutturali stabili**: La scomposizione matematica ha identificato `$3$` gradienti strutturali che mappano l'organizzazione delle fibre (antero-posteriore, ventro-dorsale e callosale) e `$3$` fattori microstrutturali stabili e replicabili test-retest (`$r > 0.94$`).
- **Alterazioni diffuse e accuratezza diagnostica**: Nella fase acuta (a `$2$` settimane), i pazienti presentano estese alterazioni dei gradienti globali in entrambi gli emisferi (ipsilesionale e contralesionale) ben oltre i confini del territorio vascolare della lesione, consentendo di classificare i pazienti rispetto ai controlli con un'accuratezza del `$90\%$`.
- **Degenerazione strutturale progressiva**: I modelli LMM mostrano che le alterazioni della connettività globale (\(GD\)) continuano a progredire significativamente tra le `$2$` settimane e i `$3$` mesi in entrambi gli emisferi, confermando una progressiva degenerazione secondaria del connettoma.
- **Perdita di mielina nei tratti disconnessi**: All'interno delle maschere di disconnessione (SDC), si assiste a una riduzione longitudinale significativa del fattore microstrutturale `$dwiF3$`, indice di progressivi processi di demielinizzazione e degenerazione assonale secondaria (Walleriana) a carico delle fibre disconnesse.
- **Legame disconnessione focale - connettoma globale**: Le alterazioni microstrutturali locali dei tratti disconnessi correlano significativamente e predicono il grado di divergenza globale (\(GD\)) dell'intero connettoma strutturale in entrambi gli emisferi (`$R^2$` tra `$0.16$` e `$0.23$`), dimostrando come la disconnessione locale guidi a cascata il collasso dei network globali.
- **Doppia dissociazione cervello-comportamento**:
    - _Gradienti globali e cognizione (fase acuta)_: Nella fase acuta, l'alterazione dei gradienti globali (\(GD\)) predice significativamente i deficit in domini cognitivi complessi, quali linguaggio-memoria verbale, memoria spaziale e attenzione-neglect. Questa associazione **scompare completamente** a `$3$` mesi, evidenziando il disaccoppiamento tra la continua degenerazione strutturale e il recupero cognitivo.
    - _Microstruttura locale e motricità_: Al contrario, i parametri microstrutturali locali (`$dwiF2$`, che mappa l'anisotropia e la coerenza delle fibre) all'interno delle aree disconnesse (principalmente il tratto corticospinale) predicono stabilmente e in modo robusto i deficit motori controlaterali sia nella fase acuta (`$R^2 = 0.37$`) sia nella fase cronica a `$3$` mesi (`$R^2 = 0.42$`).

---

### ## Breve Discussione
- **Divergenza struttura-funzione nella plasticità**: Esiste una chiara dissociazione nei meccanismi biologici del recupero post-ictus. Mentre la connettività funzionale (FC) si riorganizza e tende a normalizzarsi guidando il recupero clinico, la materia bianca strutturale (SC) va incontro a un declino e a una degenerazione degenerativa inarrestabile. Questo dimostra che il cervello recupera le proprie funzioni cognitive "sfruttando" in modo flessibile ed efficiente lo scheletro strutturale danneggiato rimasto (ricalibramento sinaptico), piuttosto che riparando le connessioni anatomiche spezzate.
- **L'ictus come patologia diffusa del connettoma**: Il lavoro conferma sperimentalmente in vivo che l'ictus non deve essere considerato un danno locale. L'interruzione focale di tratti assonali strategici innesca una degenerazione trans-sinaptica e microstrutturale remota (comprese alterazioni nella corteccia contralesionale sana) che altera l'architettura globale del connettoma strutturale dell'intero cervello.
- **Implicazioni cliniche per la riabilitazione**: Dal momento che la degenerazione strutturale della materia bianca a `$3$` mesi è disaccoppiata dal recupero cognitivo dei pazienti, gli sforzi terapeutici della neuroriabilitazione (e delle tecniche di stimolazione magnetica/elettrica cerebrale) non dovrebbero mirare all'inversione del danno anatomico, ma al potenziamento della riserva funzionale e all'adattamento dinamico dei network corticali risparmiati.

---

# Cinetto et al.  (2026)
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

# Volpi et al. (2025) 
_The brain’s “dark energy” puzzle upgraded: FDG uptake, delivery and phosphorylation, and their coupling with resting-state brain activity_

## Riassunto brevissimo
- **Evoluzione della "dark energy"**: Il lavoro estende la comprensione del consumo energetico intrinseco del cervello sano superando la semplice misurazione semi-quantitativa dell'uptake (SUVR) per mappare i singoli parametri cinetici del glucosio ad alta risoluzione.
- **Profili cinetici indipendenti**: Tramite un ampio database di soggetti sani, gli autori dimostrano che la consegna di glucosio (\(K_1\)) e la sua fosforilazione intracellulare (\(k_3\)) hanno distribuzioni spaziali distinte e non ridondanti.
- **Accoppiamento multimodale**: Combinando la PET dinamica e la rs-fMRI, lo studio rivela come la consegna e l'elaborazione del glucosio cerebrale siano regolate in modo differenziale dall'attività neuronale spontanea locale e dal metabolismo dell'ossigeno.

---

## Domande scientifiche e Obiettivi
- **Regolazione dell'energia a riposo**: In che modo le fluttuazioni spontanee dell'attività neuronale (valutate tramite rs-fMRI) determinano e si accoppiano al consumo di glucosio a riposo?
- **Scomposizione della cinetica**: La consegna del glucosio attraverso la barriera emato-encefalica (\(K_1\)) e la sua fosforilazione enzimatica (\(k_3\)) presentano profili spaziali diversi e accoppiamenti emodinamici o metabolici differenziati?
- **Obiettivo principale**: Creare modelli predittivi multivariati basati su rs-fMRI e PET con ossigeno (\(CBF\) e \(CMRO_2\)) per mappare e spiegare accuratamente la variabilità spaziale e individuale di ciascun parametro cinetico (\(K_i\), \(K_1\), \(k_3\)).

## Metodologie
- **Campione e PET multimodale**: Coinvolgimento di 47 controlli sani sottoposti nella stessa giornata a PET dinamica con \(FDG\) (metabolismo del glucosio), PET con \(H_2O\) (flusso ematico cerebrale, CBF), PET con \(O_2\) (tasso metabolico dell'ossigeno, \(CMRO_2\)) e risonanza magnetica funzionale a riposo (rs-fMRI).
- **Modellazione cinetica compartimentale**: Calcolo voxel-wise dei parametri compartimentali di Sokoloff (\(K_1\), \(k_3\), e il macroparametro d'importazione \(K_i\)) integrato con un algoritmo Bayesiano variazionale su 216 regioni della materia grigia.
- **Integrazione di caratteristiche rs-fMRI**: Estrazione di 50 metriche fMRI raggruppate in quattro pool: (1) caratteristiche del segnale locale (es. ReHo, ALFF,peaks-BOLD), (2) rete della risposta emodinamica (HRF), (3) connettività funzionale statica (sFC) e (4) connettività funzionale variabile nel tempo (tvFC).
- **Modellistica statistica multilivello**: Utilizzo di modelli lineari a effetti misti (MEM) e regressione ridge per stimare la varianza spaziale di ciascun parametro \(FDG\) a livello individuale e di popolazione, sia con predittori fMRI-only sia integrando CBF e \(CMRO_2\).

## Risultati

- **Distribuzioni spaziali uniche**: Il parametro \(K_1\) (consegna) è risultato il meno ridondante, caratterizzato da un forte pattern posteromediale; al contrario, \(K_i\) e \(k_3\) hanno mostrato discrepanze regionali uniche a livello delle cortecce occipitali, del talamo e del cervelletto.
- **L'effetto fMRI-only**: I modelli basati esclusivamente su rs-fMRI hanno spiegato una quota moderata ma significativa della varianza individuale dei parametri: il \(35%\) per l'importazione (\(K_i\)), il \(21%\) per la fosforilazione (\(k_3\)) e solo il \(14%\) per la consegna (\(K_1\)).
- **Il ruolo dominante di ReHo**: L'omogeneità regionale (ReHo), che misura la sincronizzazione dell'attività locale, è emersa come la singola metrica funzionale più importante, spiegando da sola gran parte della varianza di \(K_i\) e \(k_3\).
- **Upgrade metabolico con ossigeno**: L'inclusione di \(CMRO_2\) ha notevolmente migliorato la varianza spiegata (l'R² pooled sale al \(46%\) per \(K_i\) e al \(28%\) per \(K_1\)), mostrando come il tasso metabolico dell'ossigeno sia fortemente e direttamente accoppiato al tasso di consegna del glucosio (\(K_1\)).

## Breve Discussione
- **Cinetiche non ridondanti**: La scomposizione dell'uptake complessivo del glucosio nei suoi parametri elementari di consegna e fosforilazione dimostra che l'analisi dei microparametri non è ridondante e rivela meccanismi fisiologici altrimenti nascosti dal SUVR.
- **Separazione funzionale dei processi**: La fosforilazione intracellulare del glucosio (\(k_3\)) è strettamente accoppiata alla sincronia dell'attività locale (ReHo), mentre la consegna del glucosio attraverso la barriera emato-encefalica (\(K_1\)) è guidata dal metabolismo dell'ossigeno (\(CMRO_2\)).
- **Rilevanza clinico-applicativa**: Questi risultati arricchiscono la nostra comprensione dell'accoppiamento tra flusso, metabolismo e attività neurale spontanea, suggerendo l'utilità futura di mappare \(K_1\) e \(k_3\) per valutare precocemente patologie come l'Alzheimer o i traumi cerebrali.

---
# Bisogno et al. (2025)
_Large-scale network topography of stroke predicts functional outcome after mechanical thrombectomy_

### ## Riassunto brevissimo
- **Prevedere gli esiti dopo la trombectomia**: Nonostante l'efficacia clinica della trombectomia meccanica (MT) nel ripristinare il flusso sanguigno nell'ictus ischemico acuto da occlusione di grandi vasi (LVO), una percentuale compresa tra il `$35\%$` e il `$60\%$` dei pazienti presenta ancora disabilità residue a `$3$` mesi di distanza dall'evento.
- **La superiorità dell'approccio di rete**: La disabilità a `$3$` mesi (misurata con la scala Rankin modificata, mRS) viene prevista in modo significativamente migliore mappando la lesione all'interno dell'atlante funzionale corticale di Yeo (`$R^2 = 0.382$`) o dell'atlante strutturale della sostanza bianca di Figley (`$R^2 = 0.338$`), mentre la classica zonizzazione vascolare fornisce la predizione più debole in assoluto (`$R^2 = 0.146$`).
- **Il disconnettoma della disabilità**: Lo studio rivela che la disconnessione funzionale delle reti visive, somatomotorie e attentive dorsali, unitamente alla disconnessione strutturale di grandi fasci di sostanza bianca (come il fascio corticospinale e il corpo calloso), costituisce il principale substrato biologico e predittivo del danno funzionale a lungo termine.

---

### ## Domande scientifiche e Obiettivi
- La localizzazione spaziale della lesione ischemica post-trombectomia all'interno di atlanti di network funzionali o strutturali fornisce una previsione dell'outcome clinico a `$3$` mesi superiore rispetto alle classiche mappe vascolari?
- Quali specifici pattern di disconnessione strutturale e funzionale indiretta (SDC e FDC) si associano in modo significativo alla gravità della disabilità a lungo termine (mRS) nei pazienti sottoposti a MT?
- **Obiettivo principale**: Valutare il valore prognostico incrementale della topografia lesionale basata su network rispetto a quella basata su mappe vascolari e ai predittori clinici tradizionali, offrendo un modello predittivo con una forte vocazione alla traducibilità clinica.

---

### ## Metodologie
- **Campione**: Studio retrospettivo condotto su `$70$` pazienti con primo ictus ischemico acuto da occlusione di grandi vasi (LVO) nella circolazione anteriore, trattati con trombectomia meccanica presso l'Azienda Ospedaliera Università di Padova tra gennaio `$2018$` e giugno `$2022$`.
- **Neuroimaging e Segmentazione**: Le lesioni sub-acute sono state segmentate manualmente su scansioni TC o risonanze MRI-FLAIR eseguite in media a `$7 \pm 3.5$` giorni dall'evento. Le maschere lesionali sono state normalizzate nello spazio standard MNI.
- **Atlanti di Riferimento**: La lesione di ciascun paziente è stata proiettata su tre spazi: (1) un atlante vascolare ad alta risoluzione con `$32$` suddivisioni (inclusi i territori dell'arteria cerebrale media), (2) l'atlante funzionale corticale di Yeo a `$7$` e `$17$` network, e (3) l'atlante strutturale della sostanza bianca di Figley con `$13$` sistemi di connessione.
- **Modellistica Predittiva**: È stata applicata una regressione Lasso con cross-validazione _leave-one-out_ (LOO) per prevedere il punteggio mRS a `$3$` mesi, calcolando la percentuale di sovrapposizione lesione-atlante ed escludendo le regioni con overlap inferiore al `$5\%$`. Le performance dei modelli sono state valutate tramite il coefficiente di determinazione (`$R^2$`).
- **Analisi Voxel-wise e Disconnessioni**: Sono state stimate le mappe probabilistiche di disconnessione strutturale (SDC) e funzionale (FDC) indiretta tramite il _BCB Toolkit_. Le associazioni voxel-wise con l'mRS a `$3$` mesi sono state calcolate tramite permutazioni (`$n = 1000$`) corrette per errore family-wise (FWE) con soglia `$P < 0.01$`.

---

### ## Risultati

- **Superiorità predittiva dei network**: La predizione dell'mRS a `$3$` mesi è risultata decisamente più robusta utilizzando l'atlante funzionale di Yeo a `$7$` network (`$R^2 = 0.382$`), seguito dall'atlante strutturale di Figley (`$R^2 = 0.338$`). L'atlante vascolare ha mostrato le performance peggiori (`$R^2 = 0.146$`). I risultati per l'atlante funzionale sono stati confermati anche con la parcellizzazione a `$17$` network (`$R^2 = 0.363$`).
- **Il fallimento dell'ASPECTS**: In linea con le scarse performance dell'atlante vascolare, il punteggio ASPECTS misurato all'ammissione ha mostrato una correlazione quasi nulla con l'mRS a `$3$` mesi (`$r = 0.130$`), spiegando una quota di varianza del tutto trascurabile (`$R^2 = 0.017$`).
- **Confronto e integrazione con il modello di benchmark**: Il modello clinico di riferimento (età, sesso, NIHSS all'ammissione) ha spiegato da solo il `$48.4\%$` della varianza (`$R^2 = 0.484$`). L'aggiunta dei dati di network (ad esempio Yeo a `$7$` network) a questo modello clinico di base ha fornito un incremento significativo dell'accuratezza predittiva, portando il modello combinato a spiegare circa il `$60\%$` della varianza (`$R^2 \approx 0.6$`).
- **I correlati della disfunzione funzionale e strutturale**:
    - A livello voxel-wise, il danno lesionale diretto associato a peggiori esiti clinici si localizza bilateralmente nella corona radiata e nel fascio corticospinale sinistro.
    - La disconnessione funzionale (FDC) si associa significativamente a disabilità nei network visivo (VIS, `$R^2 = 0.379, P < 0.05$`), somatomotorio (SMN, `$R^2 = 0.340, P < 0.05$`) e attentivo dorsale (DAN, `$R^2 = 0.318, P < 0.05$`).
    - La disconnessione strutturale (SDC) mostra associazioni critiche con la compromissione delle fibre callosali anteriori, delle radiazioni talamiche, del fascicolo uncinato, del forceps major e dei fascicoli longitudinali superiori e inferiori bilateralmente.

---

### ## Breve Discussione
- **Oltre i territori vascolari**: Lo studio dimostra che la prognosi e il recupero a lungo termine del paziente dopo trombectomia non dipendono strettamente dal danno strutturato secondo i classici confini vascolari (come l'ASPECTS), ma sono governati dall'integrità dei grandi network funzionali e strutturali che tali vasi irrorano.
- **La "riserva strutturale" come motore di plasticità**: I risultati supportano l'importanza clinica della riserva strutturale e funzionale del connettoma cerebrale: preservare i canali strategici di comunicazione sani (nonostante la lesione vascolare primaria) fornisce al cervello il substrato neurofisiologico necessario per riorganizzarsi e compensare i deficit.
- **Implicazioni cliniche per la riabilitazione**: Spostare l'attenzione dalla mera volumetria o topografia lesionale in fase acuta verso l'analisi dei network risparmiati ("capacità residua") apre la strada ad approcci terapeutici personalizzati, come la stimolazione cerebrale non invasiva guidata matematicamente su regioni funzionalmente rilevanti ma strutturalmente intatte.

---

# Volpi et al. (2024)
_The brain’s “dark energy” puzzle: How strongly is glucose metabolism linked to resting-state brain activity?_

## Riassunto brevissimo
- **Il puzzle dell'energia oscura**: Il cervello consuma a riposo circa il 25% del glucosio corporeo, pur rappresentando solo il 2% del peso corporeo. Questo studio indaga in che misura questa notevole spesa energetica regionale sia guidata dall'attività neuronale spontanea.
- **Accoppiamento non-lineare e locale**: Integrando 50 metriche di risonanza magnetica funzionale a riposo (rs-fMRI) in due dataset indipendenti di controlli sani, gli autori dimostrano che l'accoppiamento spaziale funzionale-metabolico (misurato con \($[^{18}\text{F}]\text{FDG PET})$ SUVR) è non-lineare, eterogeneo e dominato da indici di sincronizzazione locale (come la Regional Homogeneity, ReHo).
- **Influenza del metabolismo periferico**: La forza di questo accoppiamento spaziale (espressa dall' $R^2$ individuale) varia tra i soggetti ed è direttamente influenzata e inversamente correlata a parametri metabolici periferici, quali il peso corporeo, il BMI e l'insulina plasmatica a riposo.

---

## Domande scientifiche e Obiettivi
- In che misura l'immensa spesa energetica del cervello a riposo è legata e spiegata dalle fluttuazioni e dalle reti dell'attività neuronale spontanea (rs-fMRI)?
- Quali specifiche caratteristiche del segnale BOLD (locali, emodinamiche, o di connettività statica/dinamica a lungo termine) si associano più strettamente al metabolismo regionale?
- **Obiettivo principale**: Costruire e validare in modo _out-of-sample_ (su un secondo dataset indipendente) un modello predittivo multivariato e multilivello (MEM) in grado di mappare la variabilità spaziale dell'uptake di glucosio  \($[^{18}\text{F}]\text{FDG PET})$ SUVR) a partire dalle fluttuazioni rs-fMRI, analizzando anche l'influenza di fattori costituzionali e periferici.

## Metodologie
- **Campione e Dataset**: Studio condotto su due dataset indipendenti di soggetti sani: il Dataset 1 (utilizzato per l'addestramento e la selezione delle caratteristiche) e il Dataset 2 (utilizzato come test per verificare la riproducibilità out-of-sample).
- **Caratteristiche funzionali (fMRI)**: Estrazione di 50 metriche derivate dal segnale BOLD a riposo, suddivise a priori in 4 categorie: (1) caratteristiche del segnale locale/sincronia, (2) risposta emodinamica (HRF), (3) connettività funzionale statica (sFC) e (4) connettività funzionale variabile nel tempo (tvFC).
- **Modellistica statistica e Selezione**: Selezione delle caratteristiche eseguita sul Dataset 1 mediante algoritmi robusti (NNLS, Elastic Net, GETS) per minimizzare la multicollinearità e la sovra-parametrizzazione.
- **Multilevel Modeling (MEM)**: Implementazione di modelli lineari a effetti misti (MEM) per catturare simultaneamente gli effetti a livello di popolazione (effetti fissi) e la variabilità tra i singoli soggetti (effetti random).

## Extracted rs-fMRI features
Nei lavori di Volpi et al. (2024, 2025), l'attività cerebrale spontanea a riposo viene sviscerata in modo estremamente approfondito estraendo **\(50\) metriche funzionali diverse** a livello di singola regione d'interesse (ROI). L'obiettivo di questo "arsenale" di misure è superare la classica e parziale visione della connettività media per catturare ogni possibile sfaccettatura fisica, dinamica e temporale del segnale rs-fMRI BOLD.

Queste \(50\) caratteristiche vengono classificate a priori in **quattro categorie o "pool" funzionali**, ciascuna dotata di un preciso significato di teoria dei segnali o di teoria dei grafi:

### 1. Signal Pool (Proprietà Locali e Temporali del Segnale)
Questo gruppo misura le caratteristiche statistiche di base, la complessità temporale e la sincronizzazione spaziale a cortissimo raggio del segnale BOLD di ogni singola area:

- **Statistiche di base:** `med-BOLD` (mediana della serie temporale BOLD), `MAD-BOLD` (deviazione assoluta mediana, indicatore di variabilità/fluttuazione locale) e `skew-BOLD` (asimmetria della distribuzione del segnale).
- **ALFF (_Amplitude of Low-Frequency Fluctuations_):** Calcola la magnitudo delle fluttuazioni spontanee a bassa frequenza (tipicamente nell'intervallo \(0.01 - 0.1 \text{ Hz}\)), riflettendo l'intensità energetica dell'oscillazione locale.
- **ReHo (_Regional Homogeneity_):** Utilizzando il coefficiente di concordanza di Kendall, misura il grado di sincronizzazione temporale locale tra i segnali BOLD di una serie di voxel adiacenti all'interno della stessa ROI.
- **Variabilità della ReHo nel tempo:** `MAD-ReHo` e `CV-ReHo` (coefficiente di variazione percentuale della ReHo calcolata a finestre scorrevoli o _sliding windows_) descrivono quanto la sincronia locale sia flessibile e fluttui nel tempo.
- **peaks-BOLD:** Conta il numero di "pseudo-eventi" (picchi di grandissima ampiezza nel segnale BOLD), catturando dinamiche non-lineari ed eventi estremi di attivazione locale.
- **Entropia e Complessità:** `ApEn-BOLD` (_Approximate Entropy_) e `rApEn-BOLD` (_Range Approximate Entropy_) quantificano la regolarità e la imprevedibilità temporale del segnale: valori più alti indicano segnali più complessi, caotici e ricchi di informazione.
- **AR-BOLD:** Il coefficiente di riflessione di un modello autoregressivo di primo ordine \(\text{AR}(1)\) applicato alla serie BOLD, che riassume la memoria a breve termine o autocorrelazione del segnale.

### 2. HRF Pool (Funzione di Risposta Emodinamica)
Questo pool estrae ed esamina la **risposta emodinamica (HRF)** regionale, che funge da interfaccia tra l'attività neuronale e il segnale fMRI BOLD:

- **peak-HRF:** L'altezza massima del picco dell'HRF (stimato tramite deconvolution cieca del segnale BOLD), considerata un potenziale proxy del flusso ematico locale (\(\text{CBF}\)).
- **Reti Emodinamiche (`hrf-DEG`, `hrf-STR`, `hrf-CC`, `hrf-BC`, `hrf-EC`, `hrf-LE`, `hrf-GE`):** Invece di mappare la connettività classica tra i segnali fMRI, gli autori calcolano la correlazione spaziale tra le **forme d'onda delle HRF** deconvolute delle diverse aree, descrivendo per la prima volta delle reti "puramente vascolari". Su queste reti vengono applicate metriche di teoria dei grafi per estrarre la centralità dei nodi (Degree, Strength, Betweenness, Eigenvector) e l'efficienza della topografia vascolare (Clustering Coefficient, Local e Global Efficiency).

### 3. sFC Pool (Connettività Funzionale Statica)
Rappresenta l'approccio di rete classico, calcolato come la correlazione di Pearson tra i segnali BOLD di coppie di regioni sull'intera durata della scansione:

- **Proprietà di rete (`s-DEG`, `s-STR`, `s-CC`, `s-BC`, `s-EC`, `s-LE`, `s-GE`):** Misure di teoria dei grafi applicate alla matrice statica di connettività funzionale per valutare il ruolo di ciascun nodo nell'integrazione e segregazione cerebrale globale.
- **med-LEig (_Leading Eigenvector_):** La mediana temporale del primo autovettore (Leading Eigenvector) estratto dalla coerenza di fase istantanea del segnale BOLD. Rappresenta la configurazione di sincronizzazione di fase dominante e stabile durante la scansione.

### 4. tvFC Pool (Connettività Funzionale Variabile nel Tempo)
Questo pool descrive come la connettività di rete si riorganizzi e fluttui secondo dopo secondo (chronnectome) applicando un approccio a finestre scorrevoli (_sliding windows_):

- **Variabilità temporale delle metriche di rete:** `mdiff-DEG/STR/...` (mediana temporale dei differenziali delle metriche dei grafi) e `CV-DEG/STR/...` (coefficiente di variazione temporale), che quantificano la tendenza di una regione a cambiare la propria centralità nel corso del tempo.
- **SampEn (_Sample Entropy_) delle metriche di rete:** `SampEn-DEG/STR/...` quantifica la complessità temporale e la regolarità delle riconfigurazioni delle metriche dei grafi istante per istante.
- **Variabilità di fase (`MAD-LEig`, `CV-LEig`, `mdiff-LEig`):** Deviazione assoluta mediana, coefficiente di variazione e differenziale temporale del Leading Eigenvector, usati per mappare l'instabilità temporale degli stati di sincronizzazione di fase istantanei.

## Risultati
- **Il ruolo dominante di ReHo**: La sincronizzazione locale misurata con ReHo (Regional Homogeneity) emerge come il predittore più forte e stabile. Da sola spiega il 32% (Dataset 1) e il 53% (Dataset 2) della varianza spaziale dell'uptake del glucosio a livello di gruppo.
- **Modelli multivariati (9p e 3p)**:
    - Il modello a 9 parametri (9p; inclusivo di entropia, ReHo, picchi BOLD, connettività statica e dinamica) spiega il 41% della varianza nel Dataset 1, ma mostra instabilità nel Dataset 2.
    - Il modello parsimonioso a 3 parametri (3p; ReHo, CV-ReHo e connettività dinamica) si dimostra altamente riproducibile, spiegando il 59% della varianza nel Dataset 2 out-of-sample.
- **Eterogeneità dei residui**: Il modello sottostima sistematicamente il consumo energetico a livello della corteccia posteromediale (in particolare il cingolo posteriore e il precuneo), del talamo e del caudato. Queste aree ad altissimo metabolismo possiedono peculiarità biologiche (es. densità sinaptica, navetta del lattato astrocita-neurone o metabolismo dell'ossigeno) che la fMRI BOLD non riesce a catturare completamente.
- **Legame con il metabolismo periferico**: Nel Dataset 2, la forza dell'accoppiamento funzionale-metabolico del singolo soggetto ($R^2$ individuale) correla negativamente con il peso corporeo ($r = -0.495$), l'area di superficie corporea (BSA, $r = -0.492$), il BMI ($r = -0.382$) e i livelli di insulina plasmatica a riposo ($r = -0.473$).

## Breve Discussione
- L'accoppiamento spaziale dimostra che il mantenimento dei potenziali di membrana a riposo e la trasmissione sinaptica (espressi dalla sincronia locale rs-fMRI) costituiscono la quota principale dell'energia oscura del cervello sano.
- I residui positivi stabili confermano che l'fMRI fornisce solo un'immagine parziale dell'attività neurale; aree metabolicamente voraci dipendono anche da flussi metabolici non-ossidativi e dinamiche gliali complesse.
- La correlazione inversa con l'insulina periferica e il peso corporeo suggerisce che variazioni metaboliche sistemiche (es. l'insulino-resistenza precoce) si riflettono in un disallineamento precoce tra attività neuronale e consumo di glucosio nel cervello, ponendo le basi per l'identificazione di biomarcatori precoci di declino cognitivo e metabolico.

---

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

---
# Idesis et al. (2023)
_A low dimensional embedding of brain dynamics enhances diagnostic accuracy and behavioral prediction in stroke_
## Riassunto brevissimo
- **Comprimere la complessità del cervello:** Per superare l'elevata dimensionalità e la ridondanza dei segnali di risonanza magnetica funzionale a riposo (rs-fMRI) post-ictus, gli autori propongono un metodo di riduzione non lineare basato su autoencoder (AE) per mappare la dinamica cerebrale in uno spazio latente a sole 6 dimensioni.
- **La freccia del tempo nel cervello:** Sfruttando il framework Temporal Evolution NETwork (TENET), lo studio misura la non-reversibilità temporale del segnale BOLD (ovvero l'asimmetria del segnale nel tempo, considerata un indice della distanza del sistema dall'equilibrio termodinamico).
- **Prognosi e diagnosi potenziate:** La reversibilità calcolata nello spazio latente dell'autoencoder dimostra una netta superiorità rispetto ai metodi lineari come la PCA e alle classiche misure di connettività funzionale (FC) nello spazio di origine (source space), raggiungendo un'accuratezza del 73% nella classificazione della severità della lesione e fino al 76-79% nella previsione del recupero clinico a un anno.
    

## Domande scientifiche e Obiettivi
- È possibile mappare l'attività neuronale ad alta dimensionalità post-ictus in uno spazio latente a bassa dimensionalità senza perdere informazioni fisiologiche e cliniche fondamentali?
- I modelli di deep learning non lineari (come gli autoencoder) sono più efficienti dei metodi lineari tradizionali (come l'Analisi delle Componenti Principali, PCA) nel catturare e preservare la complessa geometria (manifold curvo) delle fluttuazioni BOLD?
- L'integrazione di metriche di complessità temporale, in particolare la non-reversibilità temporale del segnale (freccia del tempo), all'interno dello spazio latente può migliorare l'identificazione precoce dei deficit e la prognosi del recupero comportamentale a lungo termine rispetto ai classici modelli statici di FC?

## Metodologie
- **Campione e Dati:** Utilizzo del database della coorte di pazienti post-ictus della Washington University (WU Stroke Cohort). Sono state analizzate le scansioni fMRI resting-state (rs-fMRI) di pazienti in fase acuta (2 settimane dall'evento) e controlli sani, con 896 punti temporali totali estratti per soggetto.
- **Parcellazione:** Le serie temporali BOLD sono state proiettate su una parcellazione comprendente 235 regioni di interesse (ROI, composte da 200 aree corticali e 35 strutture sottocorticali).
- **Autoencoder (AE):** Addestramento di una rete neurale profonda con strati densi e funzioni di attivazione lineari rettificate (ReLU) per comprimere la matrice dei dati rs-fMRI (235 × 896). La selezione della dimensionalità ottimale ha identificato lo spazio latente a 6 dimensioni, punto in cui l'errore di ricostruzione si stabilizza e la correlazione tra spazio di origine e spazio latente supera 0.9. L'addestramento ha previsto una suddivisione 80/20% per training e test e tecniche di arresto precoce (early stopping) per prevenire l'overfitting.
- **TENET (Temporal Evolution NETwork):** Calcolo della reversibilità del segnale analizzando l'asimmetria temporale tra le matrici di cross-correlazione "forward" (in avanti) e "reversed" (all'indietro) delle serie storiche BOLD. Questa metrica funge da proxy dello stato di non-equilibrio termodinamico del sistema cerebrale.
- **Classificazione e Predizione:** Applicazione di classificatori Random Forest sia nello spazio di origine (source space) sia nello spazio latente (AE a 6 dimensioni) per:
    1. Classificare i soggetti in controlli sani o pazienti in fase acuta.
    2. Classificare i pazienti in base alla gravità del volume della lesione (alto vs. basso volume).
    3. Prevedere l'andamento del recupero a un anno (alto vs. basso recupero) definito tramite tre criteri: miglioramento dei punteggi comportamentali in 9 domini, riduzione della distanza funzionale rispetto ai sani (distanza di Frobenius, FC distance) o recupero dell'accoppiamento struttura-funzione (correlazione SC/FC).
        

## Risultati

- **Conservazione e potenziamento dei biomarcatori:** Lo spazio latente a 6 dimensioni non solo conserva i pattern dinamici essenziali del segnale (metastabilità, co-fluttuazioni di picco, modularità, complessità funzionale e dinamica di connettività, FCD), ma mostra performance superiori rispetto alla PCA. Quest'ultima, a parità di dimensioni (6 componenti principali), spiega solo l'85% della varianza complessiva, confermando l'efficacia della compressione non lineare eseguita dall'autoencoder.
- **Classificazione acuta ed effetto lesione:** Nel discriminare i pazienti dai controlli a due settimane dall'evento, la reversibilità nel source space ha raggiunto un'accuratezza del 79%. Nel distinguere i pazienti con alto o basso volume di lesione acuta, la reversibilità nello spazio latente a 6 dimensioni ha mostrato l'accuratezza più elevata, pari al 73% (SD = 9%), superando la FC media dello spazio latente (72%), la reversibilità nel source space (65%) e la FC media nel source space (59%).
    
- **Miglioramento radicale della prognosi a un anno:** Nella predizione del recupero clinico a lungo termine (1 anno), l'integrazione di spazio latente e reversibilità temporale ha demolito le performance delle metriche convenzionali:
    - _Miglioramento comportamentale:_ La reversibilità latente ha predetto il recupero con un'accuratezza del 76% (SD = 9%) (che sale al 79% utilizzando la prima componente principale dei punteggi comportamentali). Al contrario, la connettività funzionale media nel source space si è attestata a livelli di pura casualità (52%).
    - _Distanza funzionale (FC distance):_ La reversibilità latente ha predetto la riduzione della distanza dal profilo sano con un'accuratezza del 71% (SD = 11%), contro il 55% della FC media nel source space.
    - _Accoppiamento (SC/FC):_ La reversibilità latente ha predetto il ripristino dell'accoppiamento struttura-funzione con un'accuratezza del 70% (SD = 12%), contro il 55% della FC del source space.
        
- **Associazioni cervello-comportamento specifiche:** Mentre la FC e la reversibilità nello spazio originale mostrano deboli associazioni limitate a pochissimi domini comportamentali (come la motricità sinistra e l'attenzione visiva), la reversibilità nello spazio latente correla in modo robusto e diffuso con il recupero a lungo termine in molteplici domini complessi: motricità sinistra (r = 0.48), orientamento attentivo e disimpegno (r = 0.40), memoria spaziale (r = 0.34) e controllo motorio (r = 0.36).
    

## Breve Discussione
- **La natura non lineare della dinamica cerebrale:** Il lavoro dimostra che il funzionamento del cervello a riposo poggia su un manifold dinamico non lineare e a bassa dimensionalità. L'applicazione di reti neurali non lineari (autoencoder) consente di rimuovere il rumore di fondo e la ridondanza spaziale tipica dei dati fMRI, isolando le coordinate "essenziali" della patologia.
- **Il significato termodinamico della reversibilità:** Un cervello sano elabora le informazioni rimanendo lontano dall'equilibrio termodinamico, uno stato caratterizzato da una marcata asimmetria temporale (elevata non-reversibilità). Il danno da ictus altera la reversibilità del segnale, avvicinando patologicamente il sistema verso l'equilibrio termodinamico e riducendo l'entropia. Questo crollo dell'equilibrio dinamico si traduce, sul piano clinico, nel ridotto repertorio di stati dinamici e comportamentali tipici del deficit neurologico.
- **Traduzione per la medicina di precisione:** L'abbattimento della complessità spaziale della rs-fMRI a sole 6 coordinate latenti e interpretabili apre prospettive cliniche rivoluzionarie. Ridurre un connettoma ad altissima dimensionalità in una mappa latente stabile semplifica enormemente l'identificazione di biomarcatori prognostici affidabili anche a livello di singolo paziente, fornendo una bussola matematica per individuare in modo personalizzato i target della stimolazione cerebrale non invasiva (TMS o tDCS).

---

# Facchini et al. (2023)
_A common low dimensional structure of cognitive impairment in stroke and brain tumors_

### ## Riassunto brevissimo
- **Struttura cognitiva a bassa dimensionalità comune**: Lo studio dimostra che i deficit cognitivi post-lesionali si raggruppano in un set di sintomi a bassa dimensionalità altamente sovrapponibile tra ictus e tumori cerebrali, con tre componenti principali (PC) che spiegano circa il `$41.5\%$` della varianza totale della popolazione.
- **Profili clinici parzialmente divergenti**: Nonostante la struttura latente comune, l'ictus ischemico o emorragico colpisce maggiormente funzioni che richiedono un'elaborazione più localizzata come la denominazione e il calcolo, mentre i tumori compromettono più severamente la memoria episodica, il recupero verbale e la fluenza fonemica.
- **Disaccoppiamento lesione-comportamento nei tumori**: La sola localizzazione del danno predice in modo significativo i deficit cognitivi individuali nell'ictus (fino al `$30\%$` per la PC2), ma fallisce quasi completamente nel nucleo dei tumori a causa dei lenti meccanismi di riorganizzazione funzionale e plasticità di rete.

---

### ## Domande scientifiche e Obiettivi
- I pazienti affetti da tumori cerebrali primitivi e quelli colpiti da ictus mostrano profili di compromissione cognitiva sovrapponibili quando valutati con la medesima batteria neuropsicologica multivariata?
- In che misura la localizzazione anatomica e il volume del danno strutturale predicono le prestazioni cognitive individuali nelle due diverse patologie?
- **Obiettivo principale**: Confrontare in modo sistematico la struttura latente dei deficit cognitivi e l'associazione lesione-comportamento tra una coorte prospettica di pazienti con ictus e una con tumori cerebrali, testando se la bassa dimensionalità si generalizzi oltre la patologia vascolare.

---

### ## Metodologie
- **Campione**: Sono stati inclusi `$77$` pazienti con primo ictus ischemico o emorragico (valutati entro due settimane dall'evento) e `$76$` pazienti con tumore cerebrale primitivo (gliomi e meningiomi) di nuova diagnosi (valutati prima della chirurgia), selezionando solo coloro in grado di completare l'intera batteria di test.
- **Valutazione Comportamentale**: Somministrazione di un set multivariato di test per esplorare molteplici domini cognitivi, tra cui l'Oxford Cognitive Screen (OCS), l'Esame Neuropsicologico Breve 2 (TMT A e B, fluenza fonemica, memoria di prosa, test di interferenza), il Boston Naming Test (BNT) e i test di digit span e Corsi block-tapping.
- **Segmentazione e Normalizzazione**: Le lesioni sono state tracciate manualmente su scansioni MRI o TC e normalizzate nello spazio standard MNI152. Per i tumori, sono state segmentate separatamente la regione del nucleo tumorale (_core_) e la circostante area di edema perilesionale.
- **Analisi Statistiche**:
    1. È stata applicata l'Analisi delle Componenti Principali (PCA) con rotazione obliqua per estrarre i fattori comportamentali latenti.
    2. Una regressione logistica è stata implementata per verificare la discriminabilità neuropsicologica delle due eziologie, controllando per età, istruzione, sesso e lato della lesione.
    3. Modelli di regressione ridge (RR) sono stati addestrati per prevedere i punteggi comportamentali individuali (le PC) partendo unicamente dai voxel cerebrali danneggiati.

---

### ## Risultati
- **Le tre componenti cognitive latenti**: La PCA sull'intero campione (`$n = 153$`) ha estratto tre fattori che spiegano il `$41.5\%$` della varianza totale:
    - **PC1 (`$25\%$` di varianza)**: carica principalmente compiti di linguaggio (denominazione, lettura), memoria verbale, memoria episodica e memoria di lavoro.
    - **PC2 (`$9\%$` di varianza)**: mappa l'attenzione visuo-spaziale, il neglect allocentrico ed egocentrico, e le funzioni esecutive (TMT A e B).
    - **PC3 (`$7.5\%$` di varianza)**: carica prevalentemente prove di calcolo, scrittura di numeri e orientamento temporale.
- **Consistenza e sovrapponibilità delle PC**: Le PCA condotte separatamente hanno mostrato un'architettura e varianza spiegata simili (ictus: `$44.6\%$`; tumori: `$48\%$`). Proiettando i dati dei pazienti oncologici nello spazio delle PC dell'ictus, i due gruppi sono risultati indistinguibili in uno spazio tridimensionale, con le PC dell'ictus capaci di spiegare ben il `$30.3\%$` della varianza dei punteggi dei tumori. Un'ANOVA a misure miste ha confermato che i pesi dei test sulle PC non differiscono significativamente tra le due patologie (`$F(2, 296) = 1.47; p = 0.23$`).
- **Profilo di differenziazione clinica**: La regressione logistica (AUC = `$0.889$`) ha identificato cinque test capaci di discriminare significativamente le due eziologie:
    - L'**ictus** si associa a una maggiore compromissione nella denominazione OCS-denomination (`$z = -2.79; p = 0.005$`) e nel calcolo OCS-calculation (`$z = -3.17; p = 0.001$`).
    - I **tumori** mostrano deficit peggiori nella memoria episodica OCS-episodic memory (`$z = 2.75; p = 0.005$`), nei test di interferenza di memoria a `$10\text{ s}$` (`$z = 2.28; p = 0.022$`) e nella fluenza fonemica (`$z = 2.21; p = 0.027$`).
- **Mappatura Lesione-Comportamento (Ridge Regression)**:
    - Nell'**ictus**, la sola mappa lesionale predice in modo significativo la PC1 (`$R^2 = 0.13, p = 0.04$`, localizzata nell'area perisilviana sinistra) e la PC2 (`$R^2 = 0.30, p < 0.001$`, localizzata nella regione parieto-occipitale destra).
    - Nei **tumori**, l'anatomia del solo nucleo tumorale (_core_) non mostra alcuna capacità predittiva dei sintomi (`$R^2 < 10\%$`). Una relazione significativa per la PC1 emerge unicamente quando viene aggiunta all'analisi la regione del cono edematoso perilesionale (`$R^2 = 0.16, p = 0.01$`), localizzandosi nell'area perisilviana sinistra.

---

### ## Breve Discussione
- **Confutazione del bias anatomico**: Alcuni ricercatori hanno ipotizzato che la bassa dimensionalità dei sintomi post-ictus sia un artefatto dovuto alla natura vascolare delle lesioni. Questo studio smentisce tale critica dimostrando che la stessa identica struttura latente a tre fattori emerge nei tumori cerebrali, sebbene questi presentino una topografia lesionale completamente differente (giunzione grigio-bianca fronto-temporale vs. gangli della base e materia bianca profonda dell'ictus) e un basso overlap lesionale globale.
- **Lentezza di crescita e riorganizzazione funzionale**: Nei tumori, la mancanza di predittività del solo _core_ lesionale è giustificata dalla loro crescita lenta (settimane/mesi), che consente dinamiche di plasticità e rimodellamento funzionale su larga scala in aree sane remote. Al contrario, l'insorgenza acuta dell'ictus (minuti/ore) interrompe improvvisamente i flussi di informazione impedendo un compenso immediato.
- **L'impatto clinico dell'edema e delle disconnessioni**: La predittività della PC1 nei tumori, che emerge solo includendo l'edema perilesionale, suggerisce che i sintomi cognitivi dipendono in massima parte dalla disconnessione causata dalla pressione edematosa sulle grandi vie associative profonde che transitano sotto la corteccia. Entrambe le patologie, dunque, supportano un approccio clinico e riabilitativo che superi il localizzazionismo classico a favore di una moderna neuropsicologia basata sul connettoma e sulle interazioni di rete su larga scala.

---

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

# Corbetta et al. (2018) 
_On the low dimensionality of behavioral deficits and alterations of brain network connectivity after focal injury_
## Riassunto brevissimo
Questo articolo di rassegna (_review_) propone un modello concettuale a tre vie che collega il danno anatomico strutturale, le alterazioni fisiologiche dei network e i deficit comportamentali post-ictus. Gli autori sostengono che la natura prevalentemente sottocorticale e di materia bianca delle lesioni da ictus induca una perdita generalizzata della modularità cerebrale. Questa disfunzione fisiologica diffusa riduce l'entropia (ovvero la variabilità) degli stati neurali che il cervello può esplorare, spiegando perché i molteplici deficit clinici si manifestino in una struttura a bassa dimensionalità.

---

## Domande scientifiche e Obiettivi
- In che modo il danno strutturale focale (che colpisce principalmente la materia bianca e le regioni sottocorticali) si traduce in disfunzioni fisiologiche diffuse a livello di network remoti?
- Qual è il meccanismo neurale alla base della bassa dimensionalità dei deficit comportamentali post-ictus e come questo si relaziona con le alterazioni della connettività funzionale (FC)?
- **Obiettivo principale:** Proporre una sintesi teorica e un modello fisiologico (basato sulla riduzione dell'entropia degli stati neurali) per spiegare la mappatura a tre vie fra lesione strutturale, connettività funzionale e fenotipi comportamentali a livello di popolazione.

## Metodologie
- **Sintesi e integrazione di dati di popolazione:** Trattandosi di un articolo di rassegna, gli autori integrano e discutono i dati empirici longitudinali e trasversali di ampie coorti prospettiche di pazienti con ictus (in particolare la coorte della _Washington University_ con n = 132 pazienti valutati con batterie neuropsicologiche dettagliate, MRI strutturale e resting-state fMRI).
- **Modellistica computazionale _whole-brain_:** Viene analizzato l'uso di modelli computazionali realistici che simulano l'effetto delle lesioni sul connettoma strutturale per studiare l'emergere di pattern dinamici globali, valutando metriche di integrazione, segregazione ed entropia dei nodi.
- **Analisi di rete e teoria dei grafi:** Discussione dell'applicazione di metriche globali di rete, in particolare la modularità (bilancio tra integrazione interna ed estesa segregazione dei network), come biomarcatori neurofisiologici del danno e del recupero.

## Risultati
- **Conferma della bassa dimensionalità:** Nonostante l'uso di batterie neuropsicologiche molto estese (es. 42 test su 6 domini), la maggior parte della varianza comportamentale post-ictus è catturata da pochissimi fattori principali (es. una componente motoria-attentiva e una componente cognitiva-linguaggio), riflettendo la struttura vascolare e l'impatto sui grandi fasci di materia bianca.
- **Fenotipi di FC anomala:** Le alterazioni della connettività funzionale si manifestano in pattern diffusi e topograficamente specifici, caratterizzati principalmente da due anomalie: (1) perdita di connettività interemisferica homotopic e (2) un aumento anomalo della connettività intraemisferica tra network normalmente segregati (es. default mode network e dorsal attention network).
- **Perdita di entropia e di stati neurali:** Sia i dati empirici fMRI sia le simulazioni computazionali dimostrano che le lesioni provocano una riduzione dell'entropia dei nodi (variabilità dei segnali) non solo nell'emisfero danneggiato ma anche in quello sano, riducendo la complessità e la capacità di esplorazione degli stati neurali del cervello.
- **La modularità correla con il recupero:** Il ripristino o la normalizzazione della connettività funzionale su larga scala (misurata tramite l'aumento della modularità) è il principale fattore predittivo del recupero cognitivo longitudinale.

## Breve Discussione
- **Dalla specificità locale all'interazione di network:** La neuropsicologia deve evolvere da una visione puramente modulare e focalizzata su singoli casi di dissociazioni "pure" verso modelli che considerino le interazioni dinamiche tra sistemi distribuiti su larga scala.
- **La variabilità come target riabilitativo:** Se la ridotta variabilità degli stati neurali limita il repertorio comportamentale del paziente, l'obiettivo primario della riabilitazione e della neurostimolazione (es. TMS o tDCS) dovrebbe essere la normalizzazione di questa variabilità e il ripristino della modularità globale, piuttosto che la stimolazione di un singolo sito focale.
- **Necessità di stimolazione multi-sito:** Data la natura intrinsecamente diffusa delle alterazioni di FC che supportano i deficit cognitivi, i protocolli terapeutici futuri dovranno probabilmente affidarsi a stimolazioni multi-sito, guidate da modelli computazionali personalizzati.

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