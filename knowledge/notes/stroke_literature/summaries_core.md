
# Zanola et al. (2026)
_Beyond proportional recovery in wake-up stroke: Unsupervised recovery clusters based on the NIHSS_

## Riassunto brevissimo
Il paper mette in discussione la tradizionale Regola del Recupero Proporzionale (PRR) nell'ictus, che divide rigidamente i pazienti in "fitters" e "non-fitters" tramite modelli lineari, esposti a problemi come l'accoppiamento matematico e l'effetto ceiling. 
Utilizzando tecniche di apprendimento non supervisionato (Repeated Spectral Clustering) su 201 pazienti del trial WAKE-UP, gli autori identificano **6 cluster distinti di recupero**, dimostrando che la maggior parte dei pazienti non recupera secondo un'unica quota fissa e proporzionale al deficit iniziale, ma secondo traiettorie eterogenee. 
Questo approccio guidato dai dati offre una visione più sfumata e clinicamente validata della prognosi riabilitativa.

## Domande scientifiche e Obiettivi
- Come superare i limiti statistici (l'"accoppiamento matematico" e la divisione arbitraria in due sole categorie) tipici dei classici modelli lineari di recupero post-ictus?
- È possibile raggruppare i pazienti in base alla reale somiglianza delle loro traiettorie di recupero, piuttosto che forzarli in un singolo modello matematico globale?
- **Obiettivo principale:** utilizzare algoritmi di clustering per identificare fenotipi (cluster) di recupero eterogenei in modo completamente guidato dai dati, validandone poi la rilevanza clinica rispetto a noti fattori prognostici (volume/lato lesione, trattamento rtPA, mRS a 90 giorni, classificazione Heidelberg).

## Metodologie
- **Campione:** 201 pazienti (su 503 totali) dal trial clinico WAKE-UP (ictus al risveglio), selezionati per LOC-V=0, dati NIHSS completi a tutti e 4 i time point (esordio, 22-36h, 7 giorni, 90 giorni), gravità moderata (NIHSS > 4 all'esordio) e deficit ancora presente a 22-36h (NIHSS > 0).
- **Recovery Ratio (RR):** RR = 1 − (NIHSS cronico a 90 giorni / NIHSS sub-acuto a 22-36h), cioè la frazione del deficit iniziale (misurato a 22-36h) effettivamente recuperata a 90 giorni; i valori negativi (peggioramento) sono stati posti a zero nell'analisi descrittiva della media.
- **Clustering (RSC):** algoritmo di *Repeated Spectral Clustering* (spectral clustering + consensus clustering su k-means ripetuti), applicato a una matrice di similarità costruita sulle differenze assolute (distanza di Manhattan) tra i RR dei pazienti. Il numero ottimale di cluster (k=6) è stato scelto tramite il criterio del massimo "spectral gap".
- **Validazione:** i cluster (basati solo su RR) sono stati confrontati con la classica regressione lineare PRR e con variabili esterne non usate nel clustering — lato/volume lesione, trattamento rtPA, mRS a 90 giorni, classificazione Heidelberg, fattori di rischio cardiovascolare — tramite test di Kruskal-Wallis/Mann-Whitney U (variabili numeriche/ordinali) e χ² (variabili categoriali), con correzione FDR Benjamini-Hochberg.

## Risultati
- **Sei traiettorie di recupero:** C0 (recupero totale, 100%, 54 pazienti), C1 (sopra la media, 34), C2 e C3 (nella media, in linea con le stime del modello lineare PRR; 40 e 33 pazienti), C4 (sotto la media, 21) e C5 (nessun recupero/deterioramento, RR medio ≈1%, 19 pazienti, con NIHSS che peggiora tra 22-36h e 90 giorni).
- **Coerenza con la letteratura sul PRR classico:** correlazione tra punteggio sub-acuto e cronico ρs(201)=0.73, p<0.001; circa il 70% dei pazienti rientrava nell'intervallo di predizione al 70% ("fitters"), con RR medio dei fitters ≈0.69.
- **Nessun impatto significativo di volume lesionale e trattamento sui cluster:** il volume della lesione all'ingresso in ospedale (Kruskal-Wallis, p=0.22) e il trattamento trombolitico rtPA (χ², p=0.33) non erano associati all'appartenenza ai cluster. Il rtPA migliora comunque NIHSS/mRS in fase acuta e a 3 mesi: semplicemente non modifica la traiettoria di recupero spontaneo tra 22-36h e 90 giorni.
- **Asimmetria emisferica:** il lato della lesione era significativamente associato ai cluster (χ²(5,201)=25.6, p=0.004). I pazienti con recupero perfetto (C0) avevano più lesioni destre del previsto, mentre i pazienti nel cluster C3 (recupero nella media) avevano più lesioni sinistre del previsto.
- **Associazione con la disabilità a 90 giorni:** RR e mRS a 90 giorni erano fortemente correlati (ρs=0.56, p<0.001), con associazione significativa tra cluster e mRS (H(5)=74.3, p<0.001, η²=0.36) — validazione clinica importante dei cluster ottenuti.
- **Predittività precoce:** un Recovery Ratio precoce (calcolato tra 22-36h e 7 giorni) ≥0.3 ha permesso di prevedere l'appartenenza ai cluster favorevoli (C0-C3) in circa il 90% dei casi.

## Breve Discussione
- La classificazione binaria in "fitters" e "non-fitters" imposta dai modelli PRR dipende fortemente dal metodo usato ed è altamente soggettiva; il clustering evita questo problema raggruppando i pazienti in fenotipi naturali basati sulla similarità delle traiettorie.
- La maggioranza dei pazienti non segue una regola di recupero fisso e proporzionale; la natura del recupero è più complessa ed eterogenea, pur restando coerente con una quota di recupero avvenuta nei primi 3 mesi.
- Il clustering dei tassi di recupero si è rivelato un modo efficiente per incorporare la variabile "tempo" nell'algoritmo, offrendo un quadro molto più granulare della ripresa post-ictus.
- Limiti dichiarati: l'effetto "ceiling" rende i cluster poco discriminabili per NIHSS<6 a 22-36h; il clustering usa una sola variabile (il RR, per quanto derivata da due time point); servono repliche su coorti indipendenti e l'integrazione di altri dati (fase cronica oltre i 3 mesi, neuroimaging della disconnessione lesionale, indici neurofisiologici).
- L'identificazione precoce dei pazienti destinati ai cluster meno favorevoli potrebbe rivelarsi fondamentale in futuro per personalizzare le terapie riabilitative e massimizzare la neuroplasticità.

---

# Santoro et al. (2026)
_Individual connectome fingerprints reveal early stabilization and long-term circuit remodeling after stroke_

## Riassunto brevissimo
Questo studio longitudinale (coorte TiMeS, fino a N=64 pazienti) analizza l'evoluzione dei pattern di connettività cerebrale specifici del singolo individuo ("**brain fingerprints**") durante il primo anno post-ictus. Nonostante uno scostamento persistente dall'architettura sana (significativo a T1, T2, T4; solo un trend marginale non significativo a T3), il connettoma funzionale unico di ciascun paziente si stabilizza precocemente, entro circa tre settimane dall'evento (T2). 
Questa precoce stabilizzazione a livello globale maschera un rimodellamento a lungo termine specifico per rete (aumento iniziale/transitorio nei sistemi sensoriali/attentivi - in particolare ventrale-attentivo, limbico e somatomotorio - seguito da un declino più graduale e prolungato nelle reti associative di alto livello e nelle strutture sottocorticali), guidato da una riconfigurazione funzionale dinamica che avviene al di sopra di una lesione strutturale sostanzialmente stabile.

---

## Domande scientifiche e Obiettivi
- In che modo l'ictus altera nel tempo le caratteristiche di connettività uniche e specifiche del singolo individuo ("impronte digitali" del connettoma funzionale)?
- Come si articola la relazione dinamica tra un danno strutturale sostanzialmente statico (la lesione biologica) e un fenotipo funzionale plastico e mutevole durante il recupero?
- **Obiettivo principale:** Tracciare l'evoluzione temporale delle impronte digitali connettomiche dei pazienti post-ictus nel primo anno dall'evento, valutando la loro stabilità, il rimodellamento dei circuiti a livello di rete e il loro valore prognostico per i deficit clinico-comportamentali cronici.

## Metodologie
- **Campione e disegno longitudinale:** Coorte TiMeS, fino a N=64 pazienti (disponibilità variabile per timepoint/modalità), valutati a T1 (fase acuta, ~1 settimana), T2 (fase subacuta precoce, ~3 settimane), T3 (fase subacuta tardiva, ~3 mesi) e T4 (fase cronica, ~1 anno); lesioni eterogenee, spesso sottocorticali. Confronto con due coorti di controllo sani acquisite con protocolli armonizzati: ECONS (N=31, riferimento primario per identifiability e deviazione funzionale) e TrainStim (N=10).
- **Brain Fingerprinting:** FC calcolata su parcellazione di 377 regioni (360 aree corticali Glasser + 17 sottocorticali). `Iclinical` = correlazione media della FC del paziente con la FC di ciascun controllo sano (ECONS), a misura della somiglianza col gruppo sano. `Iself` = correlazione within-subject tra la FC dello stesso paziente a due timepoint qualsiasi; nei risultati principali è soprattutto confrontata rispetto all'endpoint cronico T4. Viene inoltre calcolata la similarità between-subject (`Iothers`) e la differential identifiability `Idiff = Iself - Iothers`. Un'analisi complementare edge-wise (intraclass correlation, ICC>0.6, con bootstrap) localizza le connessioni più "identity-stabilizing".
- **Reti canoniche:** le analisi a livello di rete si basano sulle sette reti di Yeo (visiva, somatomotoria, attenzione dorsale/ventrale, limbica, frontoparietale, default mode) più le strutture sottocorticali.
- **Gestione dei confondenti:** i risultati principali sono riportati SENZA correggere la FC per età, sesso o volume di lesione; una correzione tramite modelli lineari a effetti misti (età/sesso su tutti i soggetti, poi volume di lesione sui soli pazienti) è stata applicata solo come analisi di robustezza secondaria, con risultati sostanzialmente concordanti.
- **Struttura-Funzione ed Embedding:** ogni paziente/timepoint è proiettato in uno spazio bidimensionale di similarità (SC e FC, da DWI e fMRI resting-state rispettivamente) rispetto a un template sano medio (ECONS); un inviluppo "sano" è definito soglando al 95% una stima di densità kernel (KDE) della distribuzione dei controlli.
- **Predizione multivariata:** framework a due stadi - PLSC (Partial Least Squares Correlation) identifica, a un dato timepoint (soprattutto T1, fase acuta), una maschera di connettività latente covariante con i punteggi comportamentali (NMF, detrendizzati nel tempo); la maschera viene poi usata per vincolare modelli di ridge regression, validati con leave-one-subject-out, per predire i punteggi comportamentali a timepoint successivi indipendenti (T2, T3, T4), con separazione temporale rigorosa tra scoperta delle feature e predizione per minimizzare il data leakage.

## Risultati
- **Stabilizzazione precoce del fingerprint:** `Iclinical` è significativamente più basso nei pazienti rispetto ai controlli sani a T1, T2 e T4 (p<0.01, FDR-corretto), mentre a T3 la differenza è solo un trend marginale non significativo (p=0.053) - non quindi uniforme "a tutti i timepoint". Nonostante questo scostamento globale persistente, `Iself` resta sempre superiore a `Iothers`; l'identificazione supera il 75% già confrontando T1 con gli stadi cronici, e sale all'80% a T2. Il fingerprint individuale è sostanzialmente consolidato già a T2 (nessuna differenza significativa ulteriore rispetto a T3/T4).
- **Rimodellamento dei circuiti specifico per sistema:** le reti associative (default mode e frontoparietale) mostrano la maggiore stabilità within-network nel tempo, mentre i circuiti sottocorticali e somatomotori sono meno affidabili. L'aumento relativo più marcato di `Iself` tra T1 e T2 riguarda in particolare le reti di attenzione ventrale (VA), limbica (L) e somatomotoria (SM) (p<0.05). A livello di alterazioni funzionali rispetto ai controlli sani, l'iper-connettività è precoce e transitoria (picco a T2, soprattutto in sistemi sensoriali/attentivi), mentre l'ipo-connettività cresce più gradualmente, raggiunge il massimo a T3 e coinvolge soprattutto le reti associative di alto livello (FP, DMN) e le strutture sottocorticali, persistendo parzialmente fino a T4.
- **Dissociazione struttura-funzione:** la disconnessione strutturale (da DWI) resta topologicamente stabile nel primo anno, mentre le alterazioni funzionali continuano a evolvere. Nello spazio di embedding struttura-funzione, la percentuale di pazienti fuori dall'inviluppo "sano" scende progressivamente dal 42% (T1) al 28% (T2), 24% (T3) e 18% (T4) - un avvicinamento guidato quasi esclusivamente dall'aumento della similarità funzionale, mentre la similarità strutturale resta comparabilmente stabile.
- **Recupero comportamentale dominio-specifico:** i punteggi comportamentali compositi (sei domini) migliorano nel complesso da T1 a T4, ma in modo non uniforme: motorio e sensoriale restano bassi e poco variabili fin da T1, mentre attenzione e funzioni esecutive mostrano ampia variabilità interindividuale. Il volume di lesione correla significativamente con la maggior parte dei domini comportamentali acuti, tranne il motorio (r=0.19, p=0.14).
- **Predittività prognostica delle impronte precoci:** la maschera PLSC derivata a T1 (fase acuta) predice selettivamente, tramite ridge regression LOSO, gli esiti a follow-up (T2, T3, T4) nei domini linguaggio, funzioni esecutive e attenzione; motorio e neglect non sono predetti in modo significativo dalla stessa maschera. Per lo score composito globale, l'accuratezza predittiva (R²) raggiunge il picco nella transizione tardiva T3→T4 (R²=0.584), superando T1→T2 (R²=0.444) e T1→T4 (R²=0.322).

## Breve Discussione
- Il connettoma post-ictus si comporta come un sistema dinamico vincolato: la lesione strutturale rigida impone dei limiti alla riorganizzazione, ma la dinamica funzionale conserva una flessibilità sufficiente per stabilirsi rapidamente in una nuova configurazione stabile personale, un fingerprint consolidato entro circa tre settimane (T2).
- Questa stabilità globale coesiste con - e forse dipende da - la plasticità di specifiche "ancore" funzionali: le reti associative di alto livello (DMN, FPN) restano le più stabili nel tempo, mentre i circuiti sottocorticali e sensomotori, più vulnerabili alla lesione, si riconfigurano maggiormente.
- Il connettoma rimodellato acutamente non è rumore: la maschera di connettività ottenuta già a T1 (fase acuta, ~1 settimana) racchiude informazioni prognostiche selettive su linguaggio, funzioni esecutive e attenzione a distanza di mesi/un anno (mentre non predice bene motorio e neglect, anche per la scarsa variabilità dei punteggi motori in questa coorte).
- Poiché il fingerprint individuale si stabilizza già a ~3 settimane e una firma prognostica selettiva è già rilevabile in fase acuta (~1 settimana), lo studio suggerisce una finestra temporale precoce (prime settimane) utile per ricavare biomarcatori prognostici stabili e per personalizzare interventi riabilitativi o di neurostimolazione.

---
# Pini et al. (2026)  
_Longitudinal Degeneration of Microstructural and Structural Connectivity Patterns Following Stroke_

## Riassunto brevissimo
- **Degenerazione progressiva a lungo termine**: Lo studio monitora longitudinalmente l'evoluzione della materia bianca (WM) post-ictus a 2 settimane (fase subacuta) e a 3 mesi (fase cronica) dall'evento, dimostrando che il danno strutturale a distanza e la degenerazione microstrutturale continuano a progredire nel tempo, estendendosi ben oltre la lesione iniziale e coinvolgendo anche l'emisfero sano (contralesionale).
- **Doppia dissociazione struttura-comportamento**: I risultati rivelano che le alterazioni globali della connettività strutturale (SC) sono associate a deficit cognitivi (ma non motori) soprattutto nella fase acuta; a 3 mesi il legame si indebolisce fortemente per la maggior parte dei domini, pur restando un'associazione residua debole per i fattori visuospaziale-memoria-attenzione e neglect lateralizzato. Al contrario, le alterazioni microstrutturali locali all'interno dei tratti disconnessi predicono stabilmente e a lungo termine i deficit del dominio motorio sinistro sia a 2 settimane sia a 3 mesi (il dominio motorio destro mostra solo un trend non significativo al follow-up cronico).
- **Disaccoppiamento della traiettoria strutturale**: Mentre la connettività funzionale (FC) tende storicamente, secondo lavori precedenti dello stesso gruppo, a normalizzarsi in parallelo al recupero comportamentale, la connettività strutturale (SC) mostra qui una traiettoria divergente di progressiva degenerazione tra 2 settimane e 3 mesi, suggerendo che il recupero clinico tardivo si basi su un ricalibramento sinaptico dei circuiti superstiti piuttosto che su una restaurazione strutturale del connettoma.

---

## Domande scientifiche e Obiettivi
- In che modo le alterazioni della connettività strutturale globale (SC) e le alterazioni microstrutturali locali (DTI e NODDI) mostrano traiettorie temporali accoppiate o divergenti post-ictus?
- Le alterazioni strutturali distali rispetto alla lesione iniziale spiegano le differenze interindividuali nella traiettoria di recupero cognitivo e motorio dei pazienti?
- **Obiettivo principale**: misurare l'effetto della lesione da ictus sia sulla connettività strutturale whole-brain (tramite gradienti di trattografia) sia sui parametri microstrutturali locali (DTI/NODDI) nei tratti disconnessi e nella materia grigia contralesionale, mettendo in relazione entrambe le misure con le traiettorie comportamentali a 2 settimane e 3 mesi post-ictus.

---

## Metodologie
- **Campione**: Studio prospettico longitudinale su 79 pazienti con primo ictus (ischemico o emorragico) (età 60.1±11.5 anni), di cui 48 valutati con risonanza magnetica a 2 settimane e 26 che hanno ripetuto la scansione a 3 mesi, confrontati con 33 controlli sani abbinati per età, sesso ed educazione.
- **Fattori Comportamentali Latenti**: Una vasta batteria neuropsicologica multivariata (memoria, linguaggio, attenzione visuospaziale, funzioni esecutive, motricità) è stata ridotta tramite analisi fattoriale gerarchica con rotazione varimax (KMO=0.813) in 5 macro-fattori, spiegando circa il 50% della varianza comportamentale complessiva: F1 linguaggio-memoria verbale-funzioni esecutive, F2 motorio destro, F3 motorio sinistro, F4 memoria visuospaziale/di lavoro e attenzione generale, F5 attenzione visuospaziale lateralizzata (Posner).
- **Gradienti di Connettività Strutturale (SC)**: Calcolo di matrici strutturali con la pipeline MICAPIPE a partire da trattografia whole-brain, proiettate tramite diffusion map embedding (metodo non-lineare) per estrarre i primi 3 gradienti strutturali principali (intra- ed inter-emisferici); i dettagli tecnici della trattografia (numero di streamline, eventuale refinement) sono rimandati dagli autori al materiale supplementare. La deviazione individuale dal connettoma di controllo sano è stata quantificata tramite la metrica di Gradient Divergence (GD), basata sulla distanza euclidea parcel-wise rispetto ai template dei controlli, normalizzata 0-1.
- **Modellazione Microstrutturale Locale (DTI-NODDI)**: Estrazione voxel-wise di parametri di diffusione DTI (FA, MD, AD, RD) e NODDI (NDI/ICVF, ODI, ISOVF). I parametri sono stati sintetizzati tramite analisi fattoriale in 3 mappe latenti: dwiF1 (acqua libera/CSF), dwiF2 (anisotropia e dispersione dell'orientamento delle fibre), dwiF3 (mielinizzazione, per somiglianza spaziale con mappe di mielina di riferimento). Il modello fattoriale è stato validato in un secondo campione indipendente di n=1064 soggetti dell'Human Connectome Project (HCP).
- **Disconnessione Strutturale (SDC)**: Le lesioni di ciascun paziente sono state proiettate su un connettoma sano di riferimento per stimare le mappe di disconnessione strutturale probabilistica (SDC) a diverse soglie (40%, 60%, 80%), con una "shell" di esclusione di 4 voxel attorno alla lesione per limitare gli effetti di volume parziale.
- **Analisi Statistiche**: Modelli Lineari a Effetti Misti (LMM) per la degenerazione longitudinale (subacuto vs. cronico), regressioni lineari con bootstrapping (n=1000) per associare neuroimaging e fattori comportamentali, SEM per confrontare pattern di gradiente tra gruppi, UMAP + MANCOVA + SVM per la classificazione stroke vs. controlli.

---

## Risultati
- **Gradienti e mappe microstrutturali stabili**: 3 gradienti strutturali che mappano l'organizzazione delle fibre (antero-posteriore, ventro-dorsale e callosale/sinistra-destra) e 3 fattori microstrutturali replicabili test-retest e tra i due dataset indipendenti (WashU-HCP), con correlazioni tra circa 0.94 e 0.99 a seconda del fattore e del confronto.
- **Alterazioni diffuse e accuratezza diagnostica**: Nella fase acuta, i pazienti presentano estese alterazioni dei gradienti globali in entrambi gli emisferi (ipsilesionale e contralesionale) e in tutte le reti di Yeo, consentendo di classificare i pazienti rispetto ai controlli con un'accuratezza dell'89% (connettività inter-emisferica) e del 96% (connettività intra-emisferica) nel set di test.
- **Degenerazione strutturale progressiva**: I modelli LMM mostrano che le alterazioni della connettività globale (GD) continuano a progredire significativamente tra le 2 settimane e i 3 mesi in entrambi gli emisferi (ipsi- e contralesionale, sia per gradienti intra- che inter-emisferici).
- **Perdita di mielina nei tratti disconnessi**: All'interno delle maschere di disconnessione (SDC), si osserva una riduzione longitudinale significativa del fattore microstrutturale dwiF3 (indicativo di mielinizzazione) a tutte le soglie di SDC testate, suggestiva di degenerazione progressiva delle fibre disconnesse.
- **Legame disconnessione focale - connettoma globale**: Le alterazioni microstrutturali locali dei tratti disconnessi (soglia SDC 40%) predicono in modo significativo (ma solo parziale, secondo gli stessi autori) il grado di divergenza globale (GD) dell'intero connettoma strutturale in entrambi gli emisferi (R² tra 0.17 e 0.23 circa).
- **Doppia dissociazione cervello-comportamento**:
    - _Gradienti globali e cognizione (fase acuta)_: Nella fase acuta, l'alterazione dei gradienti globali (soprattutto intra-emisferici, e inter-emisferici per i domini visuospaziali) predice significativamente i deficit in linguaggio-memoria verbale, memoria spaziale/visuospaziale e attenzione-neglect; i deficit motori non sono associati ai gradienti in questa fase. A 3 mesi il legame non è più significativo per la maggior parte dei domini, ma resta un'associazione debole per i fattori visuospaziale-memoria-attenzione e neglect lateralizzato - non una scomparsa totale.
    - _Microstruttura locale e motricità_: I parametri microstrutturali locali all'interno delle aree disconnesse predicono stabilmente e in modo robusto i deficit del dominio motorio sinistro sia nella fase acuta (R² = 0.37) sia nella fase cronica a 3 mesi (R² = 0.415); il dominio motorio destro mostra solo un trend non significativo al follow-up cronico (R² = 0.133) e nessuna associazione riportata in fase acuta.

---

## Breve Discussione
- **Divergenza struttura-funzione nella plasticità**: Gli autori propongono una dissociazione nei meccanismi di recupero post-ictus: mentre la connettività funzionale (FC), secondo lavori precedenti dello stesso gruppo, si riorganizza e tende a normalizzarsi in parallelo al recupero, la materia bianca strutturale (SC) osservata in questo studio va incontro a un declino progressivo tra 2 settimane e 3 mesi. Gli autori suggeriscono che questo pattern sia coerente con un recupero funzionale basato su ricalibramento sinaptico dei circuiti superstiti, più che su una riparazione anatomica delle connessioni.
- **L'ictus come patologia diffusa del connettoma**: Il lavoro fornisce evidenza diretta in vivo che l'interruzione focale di tratti assonali si associa a un'alterazione diffusa dell'architettura del connettoma strutturale, che coinvolge anche l'emisfero contralesionale e va oltre i confini della sola area lesa.
- **Limiti e punti di forza dichiarati dagli autori**: Il gradient mapping è sensibile alle scelte metodologiche e la sua interpretazione manca ancora di un consenso consolidato in letteratura. Punti di forza citati: l'uso di dati di diffusione multi-shell ad alta qualità, il disegno longitudinale, e l'approccio integrativo che combina dati microstrutturali, organizzazione strutturale globale e dati comportamentali in un unico modello.

---

# Cinetto et al. (2026)
_Clinical variables surpass lesion and disconnection features predicting multi-domain stroke outcomes_

## Riassunto brevissimo
Questo studio affronta la sfida della **prognosi a lungo termine** post-ictus. I ricercatori hanno valutato in modo sistematico se l'aggiunta di complesse metriche di neuroimaging (topografia della lesione e stime di disconnessione strutturale a livello dell'intero cervello, SDC) migliori la previsione del recupero rispetto all'uso delle sole variabili demografiche e cliniche acute (in primis l'NIHSS). Seguendo 199 pazienti su otto domini funzionali fino a un anno dall'ictus, lo studio mostra che le variabili neurologiche acute restano il predittore singolo più solido nella maggioranza dei domini e timepoint, mentre lesione e disconnettoma aggiungono solo un guadagno statisticamente significativo ma modesto (mediana +1.4% a 2 settimane, +7.1% a 3 mesi, +2.6% a 1 anno di varianza spiegata).

---

## Domande scientifiche e Obiettivi
- Qual è il reale valore prognostico aggiuntivo (incrementale) delle mappe avanzate di lesione e di disconnessione strutturale (SDC) rispetto ai predittori clinici standard (es. punteggio NIHSS, età)?
- È possibile prevedere in modo affidabile il recupero del paziente non in un singolo dominio, ma trasversalmente in **molteplici domini cognitivi e funzionali** all'interno della stessa coorte clinica?
- **Obiettivo principale:** Confrontare testa a testa e in modo gerarchico (demografico → neurologico acuto → lesione/SDC) l'accuratezza predittiva di 4 categorie di dati (demografici, clinico-neurologici acuti, topografia della lesione e disconnettoma) per stimare gli esiti dei pazienti a 2 settimane, 3 mesi e 12 mesi di distanza dall'ictus.

## Metodologie

- **Campione:** Una coorte prospettica di 199 pazienti al primo ictus (90 donne; età 19-83 anni) e 68 controlli sani abbinati per età e istruzione.
- **Elaborazione Neuroimaging:** Le lesioni sono state segmentate su scansioni T1/T2/FLAIR; maschera lesionale e T1 sono stati registrati in spazio MNI con il _BCB Toolkit_. Le mappe di disconnessione strutturale (SDC) sono state calcolate con il BCB Toolkit usando dati di diffusione di 178 soggetti sani dello _Human Connectome Project_ come campione normativo.
- **Modellistica Predittiva (Machine Learning):** Le mappe di lesione e SDC (alta dimensionalità) sono state ridotte con un'Analisi delle Componenti Principali (PCA, soglia 80% della varianza spiegata, con analisi di robustezza al 90%), **fittata su un dataset esterno indipendente (ATLAS, N=655 lesioni segmentate manualmente)** per evitare data leakage — passaggio esplicitamente definito dagli autori "critical, novel step". È stata utilizzata una _ridge regression_ penalizzata con validazione incrociata (Leave-One-Out per il tuning del parametro di penalità λ; 10-fold ripetuta 25 volte per la stima delle performance) per prevedere i punteggi in **otto domini** (motorio destro/sinistro, bias del campo visivo, attenzione generale, memoria spaziale e verbale, linguaggio, indipendenza funzionale/FIM). I predittori sono stati inseriti nel modello a strati (demografico → neurologico acuto → lesione o SDC) per testarne il valore aggiunto incrementale.

## Risultati
- **Fattori latenti di danno:** La PCA sulle mappe ha catturato le distribuzioni tipiche del danno da ictus. Per le lesioni, la PC1 (22% della varianza) ha distinto gli ictus emisferici (destra vs sinistra); la PC2 (12%) ha isolato gli ictus sinistri con interessamento dell'arteria cerebrale media. Per le disconnessioni (SDC), la PC1 (27%) ha replicato la distinzione emisferica, la PC2 (17%) ha riflesso il danno diffuso ai tratti dell'emisfero sinistro incluso il corpo calloso, e la PC3 (5%) ha contrapposto disconnessioni bilaterali (corona radiata, tratto cortico-spinale, cingolo, corpo calloso) a disconnessioni del fascicolo longitudinale inferiore, del fascicolo fronto-occipitale inferiore e della commissura anteriore.
- **Superiorità della clinica, con eccezioni dominio-specifiche:** Nel confronto "testa a testa", la gravità clinica acuta misurata con l'NIHSS è emersa costantemente come il predittore singolo più forte per linguaggio, motricità e indipendenza funzionale nella maggior parte dei timepoint, risultando statisticamente superiore a lesione e SDC nella maggioranza dei confronti diretti. Nei modelli gerarchici, l'aggiunta di lesione o SDC ai dati clinici ha prodotto incrementi statisticamente significativi ma modesti di varianza spiegata (mediana **+1.4%** a 2 settimane, **+7.1%** a 3 mesi, **+2.6%** a 1 anno). Il guadagno del neuroimaging è stato più marcato nei domini dove l'NIHSS è meno sensibile (attenzione, memoria, linguaggio a 3 mesi), ma non si è mantenuto a 1 anno. Il recupero cognitivo cronico (linguaggio, memoria, attenzione) a 1 anno è stato invece meglio predetto da variabili demografiche (età, istruzione, etnia) piuttosto che da variabili neurologiche o neuroanatomiche acute.

## Breve Discussione
- Il paper lancia un messaggio clinico di forte impatto (in leggero contrasto o integrazione rispetto agli studi precedenti di questo gruppo): sebbene la stima dettagliata del "disconnettoma" e della topografia della lesione offra preziose intuizioni sui meccanismi patofisiologici dell'ictus, per quanto riguarda la pura **previsione degli esiti clinici**, i fattori clinico-demografici tradizionali rimangono superiori nella maggior parte dei domini e timepoint.
- Gli autori attribuiscono questo risultato a due fattori: (1) l'NIHSS, essendo esso stesso un dato comportamentale, incorpora implicitamente fattori confondenti (riserva cognitiva, storia medica, complicanze sistemiche acute) invisibili alla sola anatomia strutturale; (2) l'alta dimensionalità delle mappe neuroanatomiche aumenta il rischio di overfitting, nonostante le contromisure adottate (PCA fittata su dataset esterno indipendente, ridge regression penalizzata).
- I modelli predittivi più complessi e ad alta dimensionalità non battono, nella maggior parte dei casi, le variabili standard raccolte al letto del paziente. Tuttavia età, istruzione ed etnia restano i predittori più solidi per gli esiti cognitivi cronici (memoria, attenzione, linguaggio a 1 anno) — un ambito in cui né l'NIHSS né le mappe neuroanatomiche funzionano bene.

# Volpi et al. (2025) 
_The brain's "dark energy" puzzle upgraded: FDG uptake, delivery and phosphorylation, and their coupling with resting-state brain activity_

## Riassunto brevissimo
- **Evoluzione della "dark energy"**: Il lavoro estende la comprensione del consumo energetico intrinseco del cervello sano superando la semplice misurazione semi-quantitativa dell'uptake (SUVR) per mappare i singoli parametri cinetici del glucosio ad alta risoluzione.
- **Profili cinetici indipendenti**: Tramite un ampio database di soggetti sani, gli autori dimostrano che la consegna di glucosio (K1) e la sua fosforilazione intracellulare (k3) hanno distribuzioni spaziali distinte e non ridondanti (correlazione spaziale K1 vs k3 solo r=0.19, contro r=0.88 tra Ki e k3).
- **Accoppiamento multimodale**: Combinando la PET dinamica e la rs-fMRI, lo studio rivela come la consegna e l'elaborazione del glucosio cerebrale siano regolate in modo differenziale dall'attività neuronale spontanea locale e dal metabolismo dell'ossigeno.

## Domande scientifiche e Obiettivi
- **Regolazione dell'energia a riposo**: In che modo le fluttuazioni spontanee dell'attività neuronale (valutate tramite rs-fMRI) determinano e si accoppiano al consumo di glucosio a riposo?
- **Scomposizione della cinetica**: La consegna del glucosio attraverso la barriera emato-encefalica (K1) e la sua fosforilazione enzimatica (k3) presentano profili spaziali diversi e accoppiamenti emodinamici o metabolici differenziati?
- **Obiettivo principale**: Creare modelli predittivi multivariati basati su rs-fMRI e PET con ossigeno (CBF e CMRO2) per mappare e spiegare accuratamente la variabilità spaziale e individuale di ciascun parametro cinetico (Ki, K1, k3).

## Metodologie
- **Campione e PET multimodale**: Coinvolgimento di 47 controlli sani (22 F; 57.4±14.8 anni) sottoposti a PET dinamica con FDG (metabolismo del glucosio), PET con H2O (flusso ematico cerebrale, CBF) e PET con O2 (tasso metabolico dell'ossigeno, CMRO2) in un'unica sessione, e a risonanza magnetica funzionale a riposo (rs-fMRI) effettuata lo stesso giorno della PET per 42 dei 47 partecipanti.
- **Modellazione cinetica compartimentale**: Stima voxel-wise dei parametri compartimentali di Sokoloff (K1, k2, k3, e il macroparametro di uptake irreversibile Ki) tramite un algoritmo di inferenza Bayesiana variazionale; le mappe parametriche sono poi state parcellizzate in 216 regioni della materia grigia (atlante Schaefer + 16 regioni sottocorticali).
- **Integrazione di caratteristiche rs-fMRI**: Estrazione di 50 metriche fMRI raggruppate in quattro pool: (1) caratteristiche del segnale locale (es. ReHo, ALFF, peaks-BOLD), (2) rete della risposta emodinamica (HRF), (3) connettività funzionale statica (sFC) e (4) connettività funzionale variabile nel tempo (tvFC).
- **Modellistica statistica multilivello**: A livello di gruppo (group-average), regressione multilineare per stimare la varianza spaziale spiegata da rs-fMRI e/o CBF, CMRO2; a livello individuale/di popolazione, modelli completi a effetti misti (full mixed-effects modeling, MEM, con effetti fissi θ ed effetti casuali individuali η), applicati sia con predittori fMRI-only sia integrando CBF o CMRO2.

## Risultati
- **Distribuzioni spaziali uniche**: Il parametro K1 (consegna) è risultato il meno ridondante, caratterizzato da un forte pattern posteromediale; al contrario, Ki e k3 hanno mostrato discrepanze regionali uniche a livello delle cortecce occipitali, del talamo e del cervelletto.
- **L'effetto fMRI-only**: I modelli basati esclusivamente su rs-fMRI hanno spiegato una quota moderata ma significativa della varianza individuale dei parametri: il 35% per l'importazione (Ki), il 21% per la fosforilazione (k3) e solo il 14% per la consegna (K1).
- **Il ruolo dominante di ReHo**: L'omogeneità regionale (ReHo), che misura la sincronizzazione dell'attività locale, è emersa come la singola metrica funzionale più importante, spiegando da sola gran parte della varianza di Ki (R²=0.30) e k3 (R²=0.16).
- **Upgrade metabolico con ossigeno**: L'inclusione di CMRO2 ha notevolmente migliorato la varianza spiegata a livello individuale (l'R² pooled sale al 46% per Ki e al 28% per K1), mostrando un'associazione moderata ma specifica tra il tasso metabolico dell'ossigeno e il tasso di consegna del glucosio (K1) — a differenza del CBF, che migliora Ki in modo simile a CMRO2 ma non porta lo stesso beneficio per K1.

## Breve Discussione
- **Cinetiche non ridondanti**: La scomposizione dell'uptake complessivo del glucosio nei suoi parametri elementari di consegna e fosforilazione dimostra che l'analisi dei microparametri non è ridondante e rivela meccanismi fisiologici altrimenti nascosti dal SUVR.
- **Separazione funzionale dei processi**: La fosforilazione intracellulare del glucosio (k3) è strettamente accoppiata alla sincronia dell'attività locale (ReHo), mentre la consegna del glucosio attraverso la barriera emato-encefalica (K1) è guidata soprattutto dal metabolismo dell'ossigeno (CMRO2), con differenze individuali legate anche a sesso, superficie corporea e livelli di insulina.
- **Rilevanza clinico-applicativa**: Questi risultati arricchiscono la nostra comprensione dell'accoppiamento tra flusso, metabolismo e attività neurale spontanea, suggerendo l'utilità futura di mappare K1 e k3 (con scanner PET ad alte prestazioni) per valutare precocemente patologie come l'Alzheimer o i traumi cerebrali.


---
# Bisogno et al. (2025)
_Large-scale network topography of stroke predicts functional outcome after mechanical thrombectomy_

## Riassunto brevissimo
- **Prevedere gli esiti dopo la trombectomia**: Nonostante l'efficacia clinica della trombectomia meccanica (MT) nel ripristinare il flusso sanguigno nell'ictus ischemico acuto da occlusione di grandi vasi (LVO), la letteratura riporta che una percentuale compresa tra il 35% e il 60% dei pazienti presenta ancora disabilità residue a 3 mesi dall'evento; in questa specifica coorte, il 56% dei pazienti ha mostrato un esito sfavorevole (mRS 3-6) a 3 mesi.
- **La superiorità dell'approccio di rete**: La disabilità a 3 mesi (misurata con la scala Rankin modificata, mRS) viene prevista in modo significativamente migliore mappando la lesione all'interno dell'atlante funzionale corticale di Yeo (R² = 0.382) o dell'atlante strutturale della sostanza bianca di Figley (R² = 0.338), mentre la classica zonizzazione vascolare fornisce la predizione più debole in assoluto (R² = 0.146). Tuttavia, quando i dati clinico-demografici vengono aggiunti a ciascun atlante, è proprio il modello vascolare (partendo da una base più bassa) a guadagnare di più, e tutti i modelli combinati convergono verso una performance simile (R² ≈ 0.6).
- **Il disconnettoma della disabilità**: Lo studio rivela che la disconnessione funzionale delle reti visive, somatomotorie e attentive dorsali, unitamente alla disconnessione strutturale di grandi fasci di sostanza bianca (fascio corticospinale, corpo calloso, corona radiata, radiazioni talamiche e, in misura minore, fascicolo uncinato e forceps major), costituisce il principale substrato biologico e predittivo del danno funzionale a lungo termine. Lo studio è definito dagli autori stessi come esplorativo.

---

## Domande scientifiche e Obiettivi
- La localizzazione spaziale della lesione ischemica post-trombectomia all'interno di atlanti di network funzionali o strutturali fornisce una previsione dell'outcome clinico a 3 mesi superiore rispetto alle classiche mappe vascolari?
- Quali specifici pattern di disconnessione strutturale e funzionale indiretta (SDC e FDC) si associano in modo significativo alla gravità della disabilità a lungo termine (mRS) nei pazienti sottoposti a MT?
- **Obiettivo principale**: Valutare il valore prognostico incrementale della topografia lesionale basata su network rispetto a quella basata su mappe vascolari e ai predittori clinici tradizionali, offrendo un modello predittivo con una forte vocazione alla traducibilità clinica.

---

## Metodologie
- **Campione**: Studio retrospettivo ed esplorativo condotto su 70 pazienti con primo ictus ischemico acuto da occlusione di grandi vasi (LVO) nella circolazione anteriore, trattati con trombectomia meccanica presso l'Azienda Ospedaliera Università di Padova tra gennaio 2018 e giugno 2022. Età media 73 ± 12 anni, 53% femmine; NIHSS all'ammissione 13.8 ± 6.8; ASPECTS mediano 8 (IQR 6-9); tasso di ricanalizzazione riuscita 95%.
- **Neuroimaging e Segmentazione**: Le lesioni sub-acute sono state segmentate manualmente su scansioni TC o risonanze MRI-FLAIR eseguite in media a 7 ± 3.5 giorni dall'evento. Le maschere lesionali sono state normalizzate nello spazio standard MNI.
- **Atlanti di Riferimento**: La lesione di ciascun paziente è stata proiettata su tre spazi: (1) un atlante vascolare ad alta risoluzione con 32 suddivisioni (inclusi i territori dell'arteria cerebrale media), (2) l'atlante funzionale corticale di Yeo a 7 e 17 network, e (3) l'atlante strutturale della sostanza bianca di Figley con 13 sistemi di connessione.
- **Modellistica Predittiva**: È stata applicata una regressione Lasso con cross-validazione leave-one-out (LOO) per prevedere il punteggio mRS a 3 mesi, calcolando la percentuale di sovrapposizione lesione-atlante ed escludendo le regioni con overlap inferiore al 5%. Le performance dei modelli sono state valutate tramite il coefficiente di determinazione (R²).
- **Analisi Voxel-wise e Disconnessioni**: La disconnessione strutturale (SDC) indiretta è stata stimata tramite il BCB Toolkit, embeddando la lesione in un connettoma strutturale normativo. La disconnessione funzionale (FDC) è stata invece calcolata con una procedura distinta (metodo delle stesse pubblicazioni precedenti degli autori): la lesione, ridotta tramite PCA della matrice di connettività within-lesion, è stata usata come seed su un connettoma normativo funzionale HCP di 173 soggetti scansionati a 7T. Le associazioni voxel-wise con l'mRS a 3 mesi sono state calcolate tramite permutazioni (n = 1000) corrette per errore family-wise (FWE) con soglia P < 0.01.

---

## Risultati

- **Superiorità predittiva dei network**: La predizione dell'mRS a 3 mesi è risultata decisamente più robusta utilizzando l'atlante funzionale di Yeo a 7 network (R² = 0.382), seguito dall'atlante strutturale di Figley (R² = 0.338). L'atlante vascolare ha mostrato le performance peggiori (R² = 0.146). I risultati per l'atlante funzionale sono stati confermati anche con la parcellizzazione a 17 network (R² = 0.363).
- **Il fallimento dell'ASPECTS**: In linea con le scarse performance dell'atlante vascolare, il punteggio ASPECTS misurato all'ammissione ha mostrato una correlazione quasi nulla con l'mRS a 3 mesi (r = 0.130), spiegando una quota di varianza del tutto trascurabile (R² = 0.017).
- **Confronto e integrazione con il modello di benchmark**: Il modello clinico di riferimento (età, sesso, NIHSS all'ammissione) ha spiegato da solo il 48.4% della varianza (R² = 0.484), la quota più alta tra i singoli modelli. Aggiungendo le variabili cliniche a ciascun atlante, è l'atlante vascolare a mostrare il guadagno maggiore (partendo da una base bassa), mentre i modelli basati su network, già più performanti alla base, guadagnano meno. Il risultato finale è che tutti i modelli combinati convergono a una performance simile, R² ≈ 0.6.
- **I correlati della disfunzione funzionale e strutturale**:
    - A livello voxel-wise, il danno lesionale diretto associato a peggiori esiti clinici si localizza bilateralmente nella corona radiata e nel fascio corticospinale sinistro.
    - La disconnessione funzionale (FDC) si associa significativamente a disabilità nei network visivo (VIS, R² = 0.379, P < 0.05), somatomotorio (SMN, R² = 0.340, P < 0.05) e attentivo dorsale (DAN, R² = 0.318, P < 0.05).
    - La disconnessione strutturale (SDC) voxel-wise mostra come correlati primari il fascio corticospinale, il corpo calloso, la corona radiata, le radiazioni talamiche e il fascicolo longitudinale inferiore/superiore sinistro; estensioni riportate in Discussione includono anche le fibre callosali anteriori, il fascicolo uncinato, il forceps major e i fascicoli longitudinali superiori e inferiori bilateralmente.
    - A 3 mesi, il 56% dei pazienti della coorte presentava un esito sfavorevole (mRS 3-6).

---

## Breve Discussione
- **Oltre i territori vascolari**: Lo studio dimostra che la prognosi e il recupero a lungo termine del paziente dopo trombectomia non dipendono strettamente dal danno strutturato secondo i classici confini vascolari (come l'ASPECTS), ma sono governati dall'integrità dei grandi network funzionali e strutturali che tali vasi irrorano.
- **La "riserva strutturale" come motore di plasticità**: I risultati supportano l'importanza clinica della riserva strutturale e funzionale del connettoma cerebrale: preservare i canali strategici di comunicazione sani (nonostante la lesione vascolare primaria) fornisce al cervello il substrato neurofisiologico necessario per riorganizzarsi e compensare i deficit.
- **Implicazioni cliniche per la riabilitazione**: Spostare l'attenzione dalla mera volumetria o topografia lesionale in fase acuta verso l'analisi dei network risparmiati ("capacità residua") apre la strada ad approcci terapeutici personalizzati, come la stimolazione cerebrale non invasiva guidata matematicamente su regioni funzionalmente rilevanti ma strutturalmente intatte.
- **Limiti**: studio esplorativo, retrospettivo, campione piccolo-medio (57% delle scansioni erano TC anziché RM); soglia di disconnessione strutturale arbitraria; il Lasso tende a trattenere una sola variabile tra predittori fortemente correlati, con possibile esclusione arbitraria di feature informative; necessari studi prospettici per validare l'uso pre-trattamento del framework network-based.

---

# Volpi et al. (2024)
_The brain’s “dark energy” puzzle: How strongly is glucose metabolism linked to resting-state brain activity?_

## Riassunto brevissimo
- **Il puzzle dell'energia oscura**: Il cervello consuma a riposo circa il 25% del glucosio corporeo, pur rappresentando solo il 2% del peso corporeo. Questo studio indaga in che misura questa notevole spesa energetica regionale sia guidata dall'attività neuronale spontanea.
- **Accoppiamento non-lineare e locale**: Integrando 50 metriche di risonanza magnetica funzionale a riposo (rs-fMRI) in due dataset indipendenti di controlli sani, gli autori dimostrano che l'accoppiamento spaziale funzionale-metabolico (misurato con [18F]FDG PET SUVR) è non-lineare (confermato nell'86% dei casi via model selection), eterogeneo e dominato da indici di sincronizzazione locale (come la Regional Homogeneity, ReHo).
- **Influenza del metabolismo periferico**: La forza di questo accoppiamento spaziale (espressa dall'R² individuale, variabile da 0.05-0.45 nel Dataset 1 e 0.01-0.54 nel Dataset 2) varia tra i soggetti ed è inversamente correlata a parametri metabolici periferici, in particolare peso corporeo e area di superficie corporea (BSA) - le uniche a sopravvivere alla correzione per confronti multipli - oltre a BMI e insulina plasmatica a riposo (correlazioni nominali).

---

## Domande scientifiche e Obiettivi
- In che misura l'immensa spesa energetica del cervello a riposo è legata e spiegata dalle fluttuazioni e dalle reti dell'attività neuronale spontanea (rs-fMRI)?
- Quali specifiche caratteristiche del segnale BOLD (locali, emodinamiche, o di connettività statica/dinamica a lungo termine) si associano più strettamente al metabolismo regionale?
- **Obiettivo principale**: Costruire e validare in modo out-of-sample (su un secondo dataset indipendente) un modello predittivo multivariato e multilivello (MEM) in grado di mappare la variabilità spaziale dell'uptake di glucosio ([18F]FDG PET SUVR) a partire dalle fluttuazioni rs-fMRI, analizzando anche l'influenza di fattori costituzionali e periferici.

## Metodologie
- **Campione e Dataset**: Studio condotto su due dataset indipendenti di soggetti sani. Il Dataset 1 (n = 26, 13 F, 59.3±10.9 anni; PET e fMRI acquisiti simultaneamente) è usato per l'addestramento e la selezione delle caratteristiche. Il Dataset 2 (n = 33, 22 F, 58.4±13.7 anni; AMBR study; PET e fMRI acquisiti sequenzialmente) è usato come test per verificare la riproducibilità out-of-sample.
- **Caratteristiche funzionali (fMRI)**: Estrazione di 50 metriche derivate dal segnale BOLD a riposo, suddivise a priori in 4 categorie: (1) caratteristiche del segnale locale/sincronia, (2) risposta emodinamica (HRF), (3) connettività funzionale statica (sFC) e (4) connettività funzionale variabile nel tempo (tvFC).
- **Modellistica statistica e Selezione**: Selezione delle caratteristiche eseguita esclusivamente sul Dataset 1 (training), tra 11 strategie testate, mediante algoritmi robusti quali NNLS (non-negative least squares) combinato con Elastic Net (per il modello a 9 parametri) e NNLS combinato con GETS (general-to-specific modeling, per il modello a 3 parametri), scelti per minimizzare multicollinearità (condition number, VIF) e sovra-parametrizzazione. Il modello con tutte e 50 le feature raggiungeva un R² di 0.62 (Dataset 1) e 0.79 (Dataset 2), ma con forte multicollinearità.
- **Multilevel Modeling (MEM)**: Implementazione di modelli lineari a effetti misti (MEM) per catturare simultaneamente gli effetti a livello di popolazione (effetti fissi) e la variabilità tra i singoli soggetti (effetti random).

## Extracted rs-fMRI features
Nei lavori di Volpi et al. (2024, 2025), l'attività cerebrale spontanea a riposo viene sviscerata in modo estremamente approfondito estraendo 50 metriche funzionali diverse a livello di singola regione d'interesse (ROI). L'obiettivo di questo "arsenale" di misure è superare la classica e parziale visione della connettività media per catturare ogni possibile sfaccettatura fisica, dinamica e temporale del segnale rs-fMRI BOLD.

Queste 50 caratteristiche vengono classificate a priori in quattro categorie o "pool" funzionali, ciascuna dotata di un preciso significato di teoria dei segnali o di teoria dei grafi:

### 1. Signal Pool (Proprietà Locali e Temporali del Segnale) — 11 feature
Questo gruppo misura le caratteristiche statistiche di base, la complessità temporale e la sincronizzazione spaziale a cortissimo raggio del segnale BOLD di ogni singola area:

- **Statistiche di base:** med-BOLD (mediana della serie temporale BOLD), MAD-BOLD (deviazione assoluta mediana, indicatore di variabilità/fluttuazione locale) e skew-BOLD (asimmetria della distribuzione del segnale).
- **ALFF (_Amplitude of Low-Frequency Fluctuations_):** Calcola la magnitudo delle fluttuazioni spontanee a bassa frequenza, riflettendo l'intensità energetica dell'oscillazione locale.
- **ReHo (_Regional Homogeneity_):** Misura il grado di sincronizzazione temporale locale tra i segnali BOLD di voxel adiacenti all'interno della stessa ROI.
- **Variabilità della ReHo nel tempo:** MAD-ReHo e CV-ReHo (MAD e coefficiente di variazione percentuale della ReHo calcolata a finestre scorrevoli, tvReHo) descrivono quanto la sincronia locale sia flessibile e fluttui nel tempo.
- **peaks-BOLD:** Conta il numero di "pseudo-eventi" (picchi di grande ampiezza) nel segnale BOLD.
- **Entropia e Complessità:** ApEn-BOLD (_Approximate Entropy_) e rApEn-BOLD (_Range Approximate Entropy_) quantificano la regolarità e imprevedibilità temporale del segnale.
- **AR-BOLD:** Coefficiente di riflessione di un modello autoregressivo di primo ordine AR(1) applicato alla serie BOLD.

### 2. HRF Pool (Funzione di Risposta Emodinamica) — 8 feature
Questo pool estrae ed esamina la risposta emodinamica (HRF) regionale, stimata tramite deconvoluzione cieca del segnale BOLD:

- **peak-HRF:** L'altezza massima del picco dell'HRF, potenziale proxy del flusso ematico locale (CBF).
- **Reti Emodinamiche (hrf-DEG, hrf-STR, hrf-CC, hrf-BC, hrf-EC, hrf-LE, hrf-GE):** Correlazione tra le serie temporali HRF di diverse aree - introdotte per la prima volta in questo lavoro per descrivere reti di potenziale attività "puramente vascolare". Su queste reti vengono applicate metriche di teoria dei grafi: Degree, Strength, Clustering Coefficient, Betweenness Centrality, Eigenvector Centrality, Local Efficiency, Global Efficiency.

### 3. sFC Pool (Connettività Funzionale Statica) — 8 feature
Rappresenta l'approccio di rete classico, calcolato come correlazione tra i segnali BOLD di coppie di regioni sull'intera durata della scansione:
- **Proprietà di rete (s-DEG, s-STR, s-CC, s-BC, s-EC, s-LE, s-GE):** Le stesse metriche di teoria dei grafi del pool HRF, applicate qui alla matrice di connettività funzionale statica classica.
- **med-LEig (_Leading Eigenvector_):** Mediana temporale del primo autovettore (Leading Eigenvector) della coerenza di fase del segnale BOLD.

### 4. tvFC Pool (Connettività Funzionale Variabile nel Tempo) — 23 feature
Questo pool descrive come la connettività di rete si riorganizzi nel tempo applicando un approccio a finestre scorrevoli (_sliding windows_), sulle stesse 7 metriche di grafo (DEG, STR, CC, BC, EC, LE, GE):
- **Variabilità temporale delle metriche di rete:** mdiff-DEG/STR/CC/BC/EC/LE/GE (mediana temporale dei differenziali) e CV-DEG/STR/CC/BC/EC/LE/GE (coefficiente di variazione percentuale).
- **SampEn (_Sample Entropy_) delle metriche di rete:** SampEn-DEG/STR/CC/BC/LE/GE quantifica la complessità/regolarità temporale delle riconfigurazioni istante per istante.
- **Variabilità di fase (MAD-LEig, CV-LEig, mdiff-LEig):** MAD, coefficiente di variazione e differenziale temporale del Leading Eigenvector.

## Risultati
- **Il ruolo dominante di ReHo**: La sincronizzazione locale misurata con ReHo emerge come il predittore più forte e stabile. Da sola spiega il 32% (R²=0.321, Dataset 1) e il 53% (R²=0.527, Dataset 2) della varianza spaziale dell'uptake del glucosio a livello di gruppo.
- **Modelli multivariati (9p e 3p)**:
    - Il modello a 9 parametri (9p: ApEn-BOLD, rApEn-BOLD, ReHo, CV-ReHo, peaks-BOLD, hrf-LE, s-BC, med-LEig, CV-BC) spiega il 41% della varianza nel Dataset 1 (training), e il 69% nel Dataset 2 (test), ma con una precisione delle stime molto bassa (%SE medio 179±227%) e instabilità/inversione di segno per diversi parametri, indicando overfitting.
    - Il modello parsimonioso a 3 parametri (3p: ReHo, CV-ReHo, CV-BC) è più robusto: R²=0.37 nel Dataset 1 (training) e R²=0.59 nel Dataset 2 (test), con precisione delle stime nettamente migliore.
- **Eterogeneità dei residui**: Il modello sottostima sistematicamente il consumo energetico nella corteccia posteromediale (in particolare la corteccia cingolata posteriore), nel talamo e nel caudato, mentre lo sovrastima in ippocampi e cervelletto. Le aree ad altissimo metabolismo possiedono peculiarità biologiche (es. densità sinaptica e di recettori, metabolismo del glucosio non-ossidativo, navetta del lattato astrocita-neurone) che la fMRI BOLD non riesce a catturare completamente.
- **Variabilità individuale**: l'R² individuale del modello 9p (R²i) varia notevolmente tra soggetti, da 0.05 a 0.45 nel Dataset 1 e da 0.01 a 0.54 nel Dataset 2.
- **Legame con il metabolismo periferico**: Nel Dataset 2, la forza dell'accoppiamento funzionale-metabolico del singolo soggetto (R²i, modello 9p) correla negativamente con il peso corporeo (r = -0.495, sopravvive a correzione FDR), l'area di superficie corporea (BSA, r = -0.492, sopravvive a FDR), il BMI (r = -0.382, non sopravvive a FDR) e i livelli di insulina plasmatica a riposo (r = -0.473, non sopravvive a FDR). Combinando peso e insulina si spiega il 39% della varianza di R²i. Nessun effetto di età o sesso è stato rilevato.
- **Riproducibilità generale**: il pattern di correlazioni bivariate SUVR-fMRI è ben riprodotto tra i due dataset (r = 0.88 tra correlazioni z-trasformate); la relazione non-lineare è stata confermata nell'86% dei confronti tra modelli.

## Breve Discussione
- Coerentemente con l'ipotesi di partenza, la sincronia locale rs-fMRI (ReHo) risulta il predittore più forte e consistente del metabolismo regionale, sia in analisi bivariate sia multivariate/multilivello, in entrambi i dataset - a supporto dell'idea che il mantenimento dei potenziali di membrana a riposo e la trasmissione sinaptica costituiscano la quota principale dell'energia oscura del cervello sano.
- I residui positivi stabili (soprattutto nella corteccia posteromediale) confermano che l'fMRI fornisce solo un'immagine parziale dell'attività neurale; le aree metabolicamente più voraci dipendono anche da processi non ben catturati dal segnale BOLD (densità sinaptica/recettoriale, metabolismo del glucosio non-ossidativo, dinamiche gliali/astrocitarie).
- La correlazione inversa tra R² individuale e parametri di metabolismo periferico (in modo robusto per peso e BSA, più nominale per BMI/insulina) suggerisce che differenze individuali nel metabolismo sistemico possano alterare il modo in cui il glucosio viene consumato per sostenere l'attività funzionale cerebrale, con possibili implicazioni per il legame tra malattie metaboliche e rischio di disturbi neurologici.

---

# Talozzi et al. (2023) 
_Latent disconnectome prediction of long-term cognitive-behavioural symptoms in stroke_

## Riassunto brevissimo
Prevedere l'evoluzione cognitiva a lungo termine dopo un ictus è estremamente complesso a livello individuale. 
Questo studio introduce un nuovo approccio basato sul "**disconnettoma**" (la mappa delle disconnessioni della materia bianca) per **prevedere i sintomi** a un anno di distanza. Comprimendo i dati di migliaia di lesioni in uno spazio bidimensionale (morfospazio), gli autori hanno sviluppato il _Disconnectome Symptoms Discoverer_ (**DSD**), un modello che supera le tradizionali metriche predittive.
Il lavoro ha prodotto il primo Atlante Neuropsicologico della Materia Bianca (**NWMA**) e un'app web interattiva per la pratica clinica.

---

## Domande scientifiche e Obiettivi
- Come si possono prevedere in modo affidabile i deficit cognitivo-comportamentali a lungo termine a partire dai dati di neuroimaging raccolti nella fase acuta?
- È possibile mappare sistematicamente la relazione tra le disconnessioni cerebrali e le misurazioni cognitivo-comportamentali a livello del singolo individuo?
- **Obiettivo principale:** Creare un "morfospazio" del disconnettoma per prevedere i punteggi clinici a un anno di distanza, mettendo a disposizione della comunità un atlante completo e uno strumento predittivo open-access.

## Metodologie
- **Campione:** Sono stati utilizzati 5 diversi database (dataset 1-5, acquisiti in 5 centri internazionali). Il dataset 1 (1333 lesioni da ictus, Londra) è servito esclusivamente per costruire il morfospazio UMAP (nessun punteggio neuropsicologico associato). Il dataset 2 (Washington University, St. Louis) è diviso in dataset 2-training (n = 119, 86 test neuropsicologici) per addestrare il DSD, e dataset 2-validation (n = 20, stessa coorte tenuta fuori) per un test out-of-sample. Il dataset 3 (Iowa, n = 26) è una vera coorte esterna, testata solo sulla fluenza semantica. I dataset 4 (Lille, n = 190) e 5 (Grenoble, n = 193) formano una seconda coppia training/validazione esterna indipendente, testata sul Bells Test.
- **Creazione del Disconnettoma:** Le lesioni dei pazienti sono state proiettate su dati trattografici ad alta risoluzione di soggetti sani (HCP a 7T, n = 176) per stimare quali tratti di materia bianca fossero interrotti.
- **Riduzione dimensionale (UMAP):** È stato applicato l'algoritmo UMAP (Uniform Manifold Approximation and Projection) per comprimere la complessità delle disconnessioni in uno spazio latente bidimensionale, ovvero il morfospazio.
- **Sviluppo del modello (DSD):** Le coordinate dei pazienti nel morfospazio sono state correlate ai punteggi neuropsicologici (correlazioni pixel-wise, |R| > 0.2), sintetizzate con una PCA a 3 componenti e usate come variabili in formule di regressione multipla per prevedere le performance cliniche future. Il DSD è stato confrontato con 6 modelli concorrenti: disconnettoma voxel-based (D-VB), embedding della sola lesione (L-SD), lesione voxel-based (L-VB), disconnessione funzionale fMRI voxel-based (f-VB), volume della lesione + età combinati (VolAge-SD), e la media di gruppo.

## Risultati
- **Elevata precisione predittiva:** Il modello DSD è stato in grado di prevedere le prestazioni neuropsicologiche dei pazienti su dati non visti (dataset 2-validation) con un Errore Assoluto Medio (MAE) medio del 16.1 ± 7% (range 4.4-39.2%); più di tre quarti dei punteggi disponibili (65 su 83) sono stati predetti con MAE < 20%.
- **Superiorità del DSD:** L'approccio basato sul disconnettoma ha superato in accuratezza (varianza spiegata, R²) tutti e 6 i modelli concorrenti confrontati statisticamente, inclusi quelli basati solo sul volume della lesione/età, sulla topologia locale della lesione o sulla disconnessione funzionale.
- **Atlante della Materia Bianca (NWMA):** Lo studio ha generato il primo atlante che correla specifiche disconnessioni della materia bianca a 86 differenti punteggi cognitivi e comportamentali, con una riproducibilità tra le due metà del dataset 1 di R = 0.82 (correlazione di Pearson).
- **Morfospazio composito:** ha predetto in modo affidabile (effect size medio-grande) 70 punteggi neuropsicologici su 86.
- **Validazione esterna:** ottenendo un R² = 0.201 per la fluenza semantica sulla coorte esterna Iowa (dataset 3), e un R² = 0.18 (0.1797) per il Bells Test nella replica esterna Grenoble (dataset 5, dopo training su dataset 4 con R² = 0.2985).

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
- **Prognosi e diagnosi potenziate:** La reversibilità calcolata nello spazio latente dell'autoencoder dimostra una netta superiorità rispetto ai metodi lineari come la PCA e alle classiche misure di connettività funzionale (FC) nello spazio di origine (source space), raggiungendo un'accuratezza (AUC) dell'84% nel distinguere controlli sani e pazienti, del 73% nella classificazione della severità della lesione e fino al 76-79% nella previsione del recupero clinico a un anno.

## Domande scientifiche e Obiettivi
- È possibile mappare l'attività neuronale ad alta dimensionalità post-ictus in uno spazio latente a bassa dimensionalità senza perdere informazioni fisiologiche e cliniche fondamentali?
- I modelli di deep learning non lineari (come gli autoencoder) sono più efficienti dei metodi lineari tradizionali (come l'Analisi delle Componenti Principali, PCA) nel catturare e preservare la complessa geometria (manifold curvo) delle fluttuazioni BOLD?
- L'integrazione di metriche di complessità temporale, in particolare la non-reversibilità temporale del segnale (freccia del tempo), all'interno dello spazio latente può migliorare l'identificazione precoce dei deficit e la prognosi del recupero comportamentale a lungo termine rispetto ai classici modelli statici di FC?

## Metodologie
- **Campione e Dati:** Utilizzo del database della coorte di pazienti post-ictus della Washington University (WU Stroke Cohort, Barnes-Jewish Hospital). Sono stati selezionati 96 pazienti con primo ictus (studiati mediamente a 13.4 ± 4.8 giorni dall'evento) e 27 controlli sani età-matched, con 896 punti temporali totali estratti per soggetto.
- **Parcellazione:** Le serie temporali BOLD sono state proiettate su una parcellazione comprendente 235 regioni di interesse (ROI, composte da 200 aree corticali e 35 strutture sottocorticali).
- **Autoencoder (AE):** Addestramento di una rete neurale profonda con strati densi e funzioni di attivazione lineari rettificate (ReLU) per comprimere la matrice dei dati rs-fMRI (235 × 896). La selezione della dimensionalità ottimale ha identificato lo spazio latente a 6 dimensioni, punto in cui l'errore di ricostruzione si stabilizza e la correlazione tra spazio di origine e spazio latente supera 0.9. L'addestramento ha previsto una suddivisione 80/20% per training e test e tecniche di arresto precoce (early stopping) per prevenire l'overfitting.
- **TENET (Temporal Evolution NETwork):** Calcolo della reversibilità del segnale analizzando l'asimmetria temporale tra le matrici di cross-correlazione "forward" (in avanti) e "reversed" (all'indietro) delle serie storiche BOLD. Questa metrica funge da proxy dello stato di non-equilibrio termodinamico del sistema cerebrale.
- **Classificazione e Predizione:** Applicazione di classificatori Random Forest (1000 alberi, cross-validation sull'80% dei soggetti; le "accuratezze" riportate sono l'area sotto la curva ROC, AUC) sia nello spazio di origine (source space) sia nello spazio latente (AE a 6 dimensioni) per:
    1. Classificare i soggetti in controlli sani o pazienti in fase acuta.
    2. Classificare i pazienti in base alla gravità del volume della lesione (alto vs. basso volume).
    3. Prevedere l'andamento del recupero a un anno (alto vs. basso recupero) definito tramite tre criteri: miglioramento dei punteggi comportamentali in 9 domini, riduzione della distanza funzionale rispetto ai sani (distanza di Frobenius, FC distance) o recupero dell'accoppiamento struttura-funzione (correlazione SC/FC).

## Risultati

- **Conservazione e potenziamento dei biomarcatori:** Lo spazio latente a 6 dimensioni non solo conserva i pattern dinamici essenziali del segnale (metastabilità, co-fluttuazioni di picco, modularità, complessità funzionale e dinamica di connettività, FCD), ma mostra performance superiori rispetto alla PCA. Quest'ultima, a parità di dimensioni (6 componenti principali), spiega solo l'85% della varianza complessiva, confermando l'efficacia della compressione non lineare eseguita dall'autoencoder.
- **Classificazione acuta ed effetto lesione:** Nel discriminare i pazienti dai controlli a due settimane dall'evento, la reversibilità nello **spazio latente** ha raggiunto l'accuratezza (AUC) più elevata, pari all'**84%** (SD = 11%), seguita dalla reversibilità nel source space (70%, SD = 10%), dalla FC media nello spazio latente (67%, SD = 13%) e dalla FC media nel source space (61%, SD = 11%). Nel distinguere i pazienti con alto o basso volume di lesione acuta, la reversibilità nello spazio latente a 6 dimensioni ha mostrato di nuovo l'accuratezza più elevata, pari al 73% (SD = 9%), superando la FC media dello spazio latente (72%), la reversibilità nel source space (65%) e la FC media nel source space (59%).
    
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

## Riassunto brevissimo
- **Struttura cognitiva a bassa dimensionalità comune**: Lo studio dimostra che i deficit cognitivi post-lesionali si raggruppano in un set di sintomi a bassa dimensionalità altamente sovrapponibile tra ictus e tumori cerebrali, con tre componenti principali (PC) che spiegano circa il 41.5% della varianza totale della popolazione.
- **Profili clinici parzialmente divergenti**: Nonostante la struttura latente comune, l'ictus colpisce maggiormente funzioni che richiedono un'elaborazione più localizzata come la denominazione e il calcolo, mentre i tumori compromettono più severamente la memoria episodica, il recupero verbale e la fluenza fonemica.
- **Disaccoppiamento lesione-comportamento nei tumori**: La sola localizzazione del danno predice in modo significativo i deficit cognitivi individuali nell'ictus (fino al 30% di varianza spiegata per la PC2), ma fallisce quasi completamente nel nucleo dei tumori a causa dei lenti meccanismi di riorganizzazione funzionale e plasticità di rete.

---

## Domande scientifiche e Obiettivi
- I pazienti affetti da tumori cerebrali primitivi e quelli colpiti da ictus mostrano profili di compromissione cognitiva sovrapponibili quando valutati con la medesima batteria neuropsicologica multivariata?
- In che misura la localizzazione anatomica e il volume del danno strutturale predicono le prestazioni cognitive individuali nelle due diverse patologie?
- **Obiettivo principale**: Confrontare in modo sistematico la struttura latente dei deficit cognitivi e l'associazione lesione-comportamento tra una coorte prospettica di pazienti con ictus e una con tumori cerebrali, testando se la bassa dimensionalità si generalizzi oltre la patologia vascolare.

---

## Metodologie
- **Campione**: Sono stati arruolati inizialmente 133 pazienti con primo ictus ischemico o emorragico e 76 pazienti con tumore cerebrale primitivo di nuova diagnosi. Solo i pazienti in grado di completare l'intera batteria di test sono stati inclusi nelle analisi: tutti i 76 pazienti oncologici vi sono riusciti, ma solo 77 dei 133 pazienti con ictus (per afasia grave, emiplegia dell'arto dominante, barriere linguistiche o trasferimento precoce in altro reparto). Questo rende il campione ictus finale (n = 77) sistematicamente più lieve della popolazione generale post-ictus (NIHSS medio = 2.08; 80% con NIHSS < 4) — un limite esplicitamente riconosciuto dagli autori. I pazienti con ictus sono stati valutati entro due settimane dall'evento; quelli oncologici entro due settimane dal ricovero e prima della chirurgia.
- **Valutazione Comportamentale**: Somministrazione di un set multivariato di test per esplorare molteplici domini cognitivi, tra cui l'Oxford Cognitive Screen (OCS), l'Esame Neuropsicologico Breve 2 (TMT A e B, fluenza fonemica, memoria di prosa, test di interferenza), il Boston Naming Test (BNT) e i test di digit span e Corsi block-tapping.
- **Segmentazione e Normalizzazione**: Le lesioni sono state tracciate manualmente su scansioni MRI o TC e normalizzate nello spazio standard MNI152. Per i tumori, sono state segmentate separatamente la regione del nucleo tumorale (core) e la circostante area di edema perilesionale.
- **Analisi Statistiche**:
    1. È stata applicata l'Analisi delle Componenti Principali (PCA) con rotazione obliqua per estrarre i fattori comportamentali latenti.
    2. Una regressione logistica è stata implementata per verificare la discriminabilità neuropsicologica delle due eziologie, controllando per età, istruzione, sesso e lato della lesione.
    3. Modelli di regressione ridge (RR) sono stati addestrati per prevedere i punteggi comportamentali individuali (le PC) a partire dai voxel cerebrali danneggiati, condotti sul sottocampione con dati completi di imaging e neuropsicologia (tumore n = 66, ictus n = 67).

---

## Risultati
- **Le tre componenti cognitive latenti**: La PCA sull'intero campione (n = 153) ha estratto tre fattori che spiegano il 41.5% della varianza totale:
    - **PC1 (25% di varianza)**: carica principalmente compiti di linguaggio (denominazione, lettura di frasi), memoria verbale, memoria episodica e memoria di lavoro/funzioni esecutive.
    - **PC2 (9% di varianza)**: mappa l'attenzione visuo-spaziale, il neglect allocentrico ed egocentrico, la memoria di lavoro (Corsi, digit span) e le funzioni esecutive (TMT A e B).
    - **PC3 (7.5% di varianza)**: carica su calcolo, lettura, scrittura di numeri, orientamento temporale e aspetti visuospaziali (neglect egocentrico sinistro, funzione esecutiva).
- **Consistenza e sovrapponibilità delle PC**: Le PCA condotte separatamente hanno mostrato un'architettura e varianza spiegata simili (ictus: 44.6%; tumori: 48%). Proiettando i dati dei pazienti oncologici nello spazio delle PC dell'ictus, i due gruppi sono risultati indistinguibili in uno spazio tridimensionale, con le PC dell'ictus capaci di spiegare il 30.3% della varianza dei punteggi dei tumori. Un'ANOVA a misure miste ha confermato che i pesi dei test sulle PC non differiscono significativamente tra le due patologie (F(2, 296) = 1.47; p = 0.23).
- **Profilo di differenziazione clinica**: La regressione logistica (AUC = 0.889) ha identificato cinque test capaci di discriminare significativamente le due eziologie:
    - L'ictus si associa a una maggiore compromissione nella denominazione OCS-denomination (z = 2.79; p = 0.005) e nel calcolo OCS-calculation (z = 3.17; p = 0.001) — punteggi più normali in questi test sono associati ai tumori.
    - I tumori mostrano deficit peggiori nella memoria episodica OCS-episodic memory (z = 2.75; p = 0.005), nei test di interferenza di memoria a 10 s (z = 2.28; p = 0.022) e nella fluenza fonemica (z = 2.21; p = 0.027) — punteggi più normali in questi test sono associati all'ictus.
- **Mappatura Lesione-Comportamento (Ridge Regression)**:
    - Nell'ictus, la sola mappa lesionale predice in modo significativo la PC1 (R² = 0.13, p = 0.04, localizzata nell'area perisilviana sinistra) e la PC2 (R² = 0.30, p < 0.001, localizzata nella regione parieto-occipitale destra). La PC3 non risulta significativa nonostante un R² numericamente elevato (R² = 0.39, p = 0.06).
    - Nei tumori, l'anatomia del solo nucleo tumorale (core) non mostra alcuna capacità predittiva dei sintomi (R² < 10%). Una relazione significativa per la PC1 emerge unicamente quando viene aggiunta all'analisi la regione di edema perilesionale (R² = 0.16, p = 0.01), localizzandosi nell'area perisilviana sinistra, come nell'ictus.

---

## Breve Discussione
- **Confutazione del bias anatomico**: Alcuni ricercatori (Sperber et al., 2023) hanno criticato la bassa dimensionalità dei sintomi post-ictus come un possibile artefatto della sola anatomia lesionale. Questo studio indebolisce tale critica dimostrando che la stessa identica struttura latente a tre fattori emerge nei tumori cerebrali, sebbene questi presentino una topografia lesionale completamente differente (giunzione grigio-bianca fronto-temporale vs. gangli della base e materia bianca profonda dell'ictus) e un basso overlap lesionale globale.
- **Lentezza di crescita e riorganizzazione funzionale**: Nei tumori, la mancanza di predittività del solo core lesionale è giustificata dalla loro crescita lenta (settimane/mesi), che consente dinamiche di plasticità e rimodellamento funzionale su larga scala in aree sane remote. Al contrario, l'insorgenza acuta dell'ictus (minuti/ore) interrompe improvvisamente i flussi di informazione tramite perdita di flusso ematico.
- **L'impatto clinico dell'edema e delle disconnessioni**: La predittività della PC1 nei tumori, che emerge solo includendo l'edema perilesionale, suggerisce che i sintomi cognitivi dipendono anche dalla disconnessione causata dall'edema sulle vie associative che transitano nella sostanza bianca circostante. Entrambe le patologie supportano dunque un approccio clinico e riabilitativo che superi il localizzazionismo classico a favore di una neuropsicologia basata sul connettoma e sulle interazioni di rete su larga scala.
- **Limiti**: campione di dimensioni contenute, coorte ictus deliberatamente più lieve della popolazione generale (non generalizzabile), assenza di nested cross-validation nella ridge regression (risultati potenzialmente sample-specific, da replicare su coorte indipendente).

---

# Bisogno et al. (2021)
_A low-dimensional structure of neurological impairment in stroke_

## Riassunto brevissimo
Tradizionalmente, i deficit causati da ictus vengono classificati come sindromi distinte legate a danni focali. Questo studio conferma invece che le menomazioni si raggruppano in una "struttura a bassa dimensionalità" (tre cluster principali). Valutando 237 pazienti arruolati prospetticamente (di cui 180 hanno soddisfatto i criteri di inclusione e 158 hanno completato l'intera valutazione comportamentale) con test rapidi eseguibili al letto del malato (NIHSS + OCS), gli autori hanno replicato i risultati ottenuti in passato con batterie di test molto lunghe. Il lavoro dimostra che deficit complessi riflettono un'alterazione diffusa dei network e che l'OCS, un test cognitivo di soli 10-15 minuti (da affiancare alla NIHSS), è sufficiente a catturare in modo robusto queste dimensioni — anche se la replicabilità anatomica risulta forte solo per il primo fattore, e più modesta per gli altri due.

---

## Domande scientifiche e Obiettivi
- La struttura a tre fattori dei deficit post-ictus (già osservata in coorti americane con test di oltre 2 ore) è riproducibile in una diversa popolazione clinica utilizzando una valutazione rapida al letto del paziente?
- È possibile mappare la neuroanatomia di questi fattori usando un approccio multivariato di _machine learning_ (Ridge Regression) e confermarne la coerenza spaziale?
- **Obiettivo principale:** Validare l'uso combinato di NIHSS e Oxford Cognitive Screen (OCS) come strumento pratico per ricavare "biomarcatori comportamentali" affidabili e applicabili nelle frenetiche _Stroke Unit_.

## Metodologie

- **Campione:** 237 pazienti al primo ictus arruolati in modo prospettico in Veneto (Padova); 180 hanno soddisfatto i criteri di inclusione post-arruolamento (campione di studio effettivo); 158 hanno completato l'intera batteria comportamentale (88% dei 180, usati per la PCA); 148 avevano sia dati comportamentali sia di neuroimaging (usati per l'analisi lesione-comportamento). Valutazione nella fase acuta (5 ± 3.3 giorni post-ictus).
- **Valutazione Comportamentale:** Uso della scala clinica standard NIHSS combinata all'Oxford Cognitive Screen (OCS), un test cognitivo specifico per l'ictus che richiede da solo 10-15 minuti.
- **Analisi dei dati:** Analisi delle Componenti Principali (PCA, rotazione obliqua PROMAX) per comprimere i numerosi punteggi clinici in fattori latenti (i primi 3 PC, per coerenza con lo studio WU precedente).
- **Mappatura Anatomica:** Le lesioni (su risonanza o TAC) sono state messe in relazione con i punteggi comportamentali usando modelli multivariati di _Ridge Regression_.
- **Validazione Esterna:** Tutti i risultati comportamentali e anatomici sono stati confrontati direttamente con la coorte indipendente della Washington University (WU, n=132), testata in precedenza con una batteria di 2,5 ore.

## Risultati
- **Tre dimensioni del deficit:** La PCA ha rivelato che circa il 50% della variabilità clinica è spiegabile da soli 3 fattori (PC1 23.5%, PC2 14%, PC3 7.5%): PC1 (linguaggio, calcolo, prassia, memoria e neglect allocentrico destro), PC2 (deficit motori sinistri, neglect visivo/spaziale sinistro e performance generale) e PC3 (deficit motori destri).
- **Forte replicabilità comportamentale:** I tre fattori estratti con il test rapido hanno mostrato una notevole somiglianza (dominio funzionale e ordine di varianza spiegata) con quelli della batteria estesa della coorte WU (PC1 22.5%, PC2 15%, PC3 11.4%, per un totale del 49%).
- **Replicabilità anatomica disomogenea tra i tre fattori:** Le mappe di _Ridge Regression_ hanno localizzato questi tre fattori in specifiche aree cortico-sottocorticali (PC1 prevalentemente sinistre, PC2 controlaterali destre, PC3 sinistre sottocorticali). La correlazione spaziale con l'anatomia delle lesioni della coorte WU è risultata **forte per PC1 (r = 0.66)**, **moderata per PC2 (r = 0.35)** e **debole per PC3 (r = 0.11)** (tutte P < 10⁻⁵) — solo il primo fattore mostra quindi una replicabilità anatomica davvero elevata. I modelli di Ridge Regression spiegavano comunque solo una parte della varianza comportamentale (Padova: PC1 38%, PC2 44%, PC3 9%; WU: PC1 13%, PC2 56%, PC3 35%).
- **Controllo vascolare:** i territori dell'arteria cerebrale media non spiegano in modo robusto le differenze nei punteggi PC, a supporto dell'idea di un danno di network piuttosto che di sindromi vascolari focali.

## Breve Discussione
- I deficit neurologici post-ictus non si presentano come sindromi focali isolate, ma sono strettamente correlati in una struttura a bassa dimensionalità che riflette un danno di network su larga scala, non riconducibile a specifici territori vascolari.
- Questa architettura del danno è stabile e specifica per l'ictus, indipendentemente dalla popolazione studiata, dal momento della valutazione o dalla batteria di test utilizzata — anche se la coerenza anatomica tra le due coorti è netta solo per il primo fattore, più debole per gli altri due.
- Mentre la sola scala NIHSS spesso manca di sensibilità per i domini cognitivi, la sua integrazione con il test OCS si è dimostrata uno strumento con altissima _compliance_ (completato dall'88% dei pazienti idonei, contro il 51% osservato con la batteria WU più lunga), ideale per guidare futuri studi di popolazione e trial clinici. Resta comunque non spiegato circa il 50% della varianza comportamentale, forse per l'assenza di domini non testati (emozione, decision making, cognizione sociale).

# Thiebaut de Schotten et al. (2020) 
_Brain disconnections link structural connectivity with function and behaviour_

## Riassunto brevissimo
Il paper dimostra che i deficit cognitivi post-ictus derivano non solo dal danno tissutale locale, ma dalla disconnessione delle reti di materia bianca. 
Poiché gli ictus colpiscono il cervello seguendo schemi non casuali, la classificazione clinica storica delle funzioni cerebrali risulta distorta. 
Mappando 1333 lesioni con reti fMRI, gli autori hanno creato un "Atlante della Funzione della Materia Bianca" per 590 funzioni cognitive.

---

## Domande scientifiche e Obiettivi
- Qual è il ruolo specifico delle connessioni di materia bianca nel supportare le funzioni cerebrali e il comportamento?
- La nostra comprensione storica delle funzioni cerebrali, derivata dall'osservazione clinica dei pazienti, è stata distorta dal fatto che le lesioni da ictus non si distribuiscono in modo casuale?
- **Obiettivo principale:** Creare un "Disconnettoma" umano per mappare sistematicamente le funzioni cognitive sui tratti di materia bianca e migliorare le previsioni cliniche.

## Metodologie
- **Campione:** 1333 lesioni reali da ictus ischemico (pazienti UCLH, 2001-2014; età 18-97 anni, media 63.89±15.91; 56.1% maschi). Per confronto, sono state generate 1333 lesioni "sintetiche" (basate su k-means sulle coordinate voxel, poi smussate/binarizzate), pseudo-casuali ma identiche per volume e lateralizzazione a quelle reali.
- **Creazione del Disconnettoma:** per ogni lesione, sono state tracciate le fibre di materia bianca che vi passano attraverso in 163 controlli sani (dati trattografici a 7T dello _Human Connectome Project_), con le mappe binarizzate e mediate per ottenere una probabilità di disconnessione voxel-per-voxel (0-1).
- **Visualizzazione della ridondanza (t-SNE):** un embedding non lineare (t-distributed stochastic neighbour embedding) è stato usato per visualizzare la somiglianza/ridondanza spaziale tra lesioni e disconnessioni, reali vs sintetiche.
- **Riduzione dimensionale (PCA):** lesioni e disconnettomi (stroke e sintetico) sono stati caratterizzati tramite la parcellazione multimodale MMP (360 aree corticali) più 12 aree sottocorticali definite manualmente, poi sottoposti a PCA con rotazione varimax per riassumere i pattern di disconnessione in componenti/"profili".
- **Confronto Funzionale:** i profili di disconnessione sono stati correlati spazialmente (Pearson) con 590 mappe meta-analitiche di attivazione cerebrale funzionale (fMRI) curate manualmente dal database _Neurosynth_ (11.406 sorgenti di letteratura fMRI).

## Risultati
- **Distribuzione non casuale:** le lesioni da ictus e le conseguenti disconnessioni mostrano un'alta ridondanza (si raggruppano in cluster molto più delle lesioni sintetiche) e tendono a colpire la materia bianca profonda con distribuzione concentrica (probabilità di danno crescente dalla superficie alla materia bianca profonda).
- **Componenti e varianza spiegata:** la PCA ha estratto 46 componenti totali; **30 di queste 46** spiegano oltre il 90% della varianza delle disconnessioni da ictus (a confronto, con lo stesso numero di componenti la PCA della lesione diretta spiegava solo il 70% della varianza, e quella della disconnessione sintetica l'80%).
- **Correlazione Struttura-Funzione:** su tutte le 46 componenti, **40** correlano in modo significativo con specifiche mappe funzionali fMRI Neurosynth (effect size da piccolo a grande, tutte r > 0.202, p < 0.00008 dopo correzione di Bonferroni), coprendo funzioni come calcolo, navigazione spaziale, campo oculare, linguaggio articolatorio.
- **Confronto statistico disconnettoma vs lesione vs sintetico:** il disconnettoma da ictus ha una relazione con l'attivazione funzionale significativamente più forte della sola lesione (t = 24.107, p < 0.001) e del disconnettoma sintetico (t = 4.620, p < 0.001).
- **Atlante della Materia Bianca:** è stato generato un atlante completo che mappa 590 funzioni cognitive direttamente sui tratti di materia bianca. Emerge una forte asimmetria: si sa molto di più sulle funzioni della materia bianca dell'emisfero sinistro rispetto al destro.

## Breve Discussione
- La forte corrispondenza tra le disconnessioni da ictus e le mappe fMRI suggerisce che l'organizzazione della materia bianca guida la segregazione funzionale del cervello.
- Poiché l'associazione tra disconnessione e funzione è significativamente più forte nel disconnettoma reale rispetto a quello sintetico, e nel disconnettoma rispetto alla sola lesione, gli autori concludono che questo derivi dalla natura non casuale e concentrica con cui gli ictus colpiscono il cervello — un bias che ha condizionato anche la tassonomia storica delle funzioni cerebrali usata nei paradigmi fMRI.
- L'Atlante creato rappresenta un nuovo strumento clinico, liberamente scaricabile (via NeuroVault), utilizzabile per proiettare qualsiasi attivazione funzionale sulla materia bianca e prevedere i deficit dei pazienti in base al loro specifico danno strutturale.

# Salvalaggio et al. (2020)
_Post-stroke deficit prediction from lesion and indirect structural and functional disconnection_

## Riassunto brevissimo
Questo studio valuta l'accuratezza di diversi approcci di neuroimaging per **prevedere i deficit** **comportamentali** post-ictus nella fase subacuta. 
Analizzando 132 pazienti, gli autori confrontano i modelli predittivi basati sulla lesione focale, sulle stime indirette della disconnessione strutturale (SDC) e funzionale (FDC) – ottenute proiettando la lesione su atlanti sani – e sulla connettività funzionale misurata direttamente con fMRI in un sottogruppo di pazienti (dimensione variabile per dominio, da 20 a 88 soggetti). 
--> I risultati dimostrano che la stima della disconnessione strutturale indiretta (SDC) ha un potere predittivo paragonabile alla lesione stessa, mentre la disconnessione funzionale indiretta (FDC) fallisce nel prevedere i deficit, indicando che non può sostituire le vere acquisizioni fMRI.

---

## Domande scientifiche e Obiettivi
- Qual è il valore clinico e predittivo dei nuovi metodi che stimano _indirettamente_ le disconnessioni cerebrali (proiettando le lesioni su connettomi sani) rispetto all'uso delle sole mappe delle lesioni?
- Lesione e SDC, usate singolarmente o in combinazione, spiegano fonti di varianza diverse o ridondanti?
- I metodi di disconnessione funzionale indiretta (FDC) possono sostituire le più costose e complesse misurazioni dirette di connettività funzionale (fMRI)?
- **Obiettivo principale:** Valutare e quantificare l'accuratezza nella previsione della variabilità dei deficit post-ictus in molteplici domini (visivo, motorio, linguaggio, memoria, attenzione) utilizzando la lesione anatomica, la SDC, la FDC e, in un sottogruppo, i dati fMRI diretti.

## Metodologie
- **Campione:** 132 pazienti al primo ictus (coorte Washington University/Barnes-Jewish Hospital), valutati prospetticamente entro 2 settimane dall'evento acuto in vari domini neuropsicologici. Un sottogruppo di pazienti aveva anche dati completi di fMRI in resting-state, con dimensione variabile a seconda del dominio comportamentale considerato (da n=20 per il campo visivo sinistro a n=88 per il linguaggio).
- **Calcolo delle Disconnessioni Indirette:** Le lesioni segmentate sulle risonanze anatomiche sono state proiettate, tramite BCBtoolkit, su un atlante di 176 soggetti sani (Human Connectome Project, diffusion 7T) per stimare i tratti di materia bianca interrotti (SDC) e le reti funzionali disconnesse (FDC, tramite correlazione media del segnale resting-state fMRI negli stessi 176 soggetti).
- **Analisi multivariata:** I dati sono stati compressi tramite Analisi delle Componenti Principali (PCA, 95% di varianza spiegata) e poi inseriti in una Ridge Regression con validazione leave-one-out (LOOCV) per generare previsioni individuali dei punteggi clinici; la significatività è stata valutata con test di permutazione e i modelli confrontati a coppie con il test di Wilcoxon.

## Risultati
- **Lesione e SDC predittive:** Le mappe della lesione e della disconnessione strutturale (SDC) si sono dimostrate capaci di prevedere le alterazioni comportamentali in quasi tutti i domini (attenzione, memoria spaziale, linguaggio, deficit visivi e motori), spiegando una varianza (R²) che va dal 16% al 58%. Nessuna delle due è risultata efficace per la memoria verbale (R² 5-6%).
- **Modelli combinati (lesione + SDC):** unire le due mappe non migliora quasi mai la previsione rispetto al modello singolo migliore, con l'unica eccezione del dominio attenzione (lesione R²=0.18; SDC R²=0.16; lesione+SDC R²=0.60).
- **Fallimento della FDC:** La mappa di disconnessione funzionale indiretta (FDC) si è rivelata scarsa o nulla nel prevedere i deficit (R² tra 0.01 e 0.18, con l'unica eccezione dei deficit del campo visivo destro, R²=0.38), nonostante le reti generate dall'algoritmo sembrassero anatomicamente molto plausibili (es. sovrapposizione significativa, r=0.485, con un circuito dell'amnesia pubblicato indipendentemente da Ferguson et al., 2019, pur con R²=0.01 non significativo per la memoria).
- **Connettività Diretta (fMRI) superiore:** Nel sottogruppo di pazienti con dati fMRI, i cambiamenti diretti di connettività funzionale hanno previsto i deficit complessi, come quelli del linguaggio (R² = 0.42), con un'accuratezza significativamente superiore alla stima indiretta della FDC (R² = 0.16).

## Breve Discussione
- L'utilizzo della stima indiretta della disconnessione strutturale (SDC) rappresenta uno strumento solido e utile a livello clinico per prevedere l'impatto dell'ictus sull'intero network, raggiungendo una precisione paragonabile all'analisi della lesione anatomica, ma senza spiegare varianza indipendente da essa (tranne che per l'attenzione).
- Il grande vantaggio dei metodi indiretti (SDC e FDC) è che richiedono solo scansioni cliniche strutturali, evitando esami di diffusione o fMRI complessi e costosi.
- Al contrario, le misurazioni indirette della disconnessione funzionale (FDC) non sono dei _proxy_ validi: producono mappe a bassa dimensionalità (poche componenti principali), sia per ragioni biologiche (le reti funzionali sono intrinsecamente poco numerose, ~7-13 anche nei soggetti sani) sia metodologiche (mixing di reti diverse nelle lesioni sottocorticali/di sostanza bianca, basso rapporto segnale/rumore del BOLD in queste regioni). Per questo non catturano adeguatamente la disfunzione dinamica dei network necessaria per fare previsioni, specialmente per i sintomi cognitivi; in questi casi, la misurazione diretta con fMRI rimane insostituibile.


# Griffis et al. (2020)
_Damage to the shortest structural paths between brain regions is associated with disruptions of resting-state functional connectivity after stroke_

## Riassunto brevissimo
Questo studio esamina come le lesioni cerebrali focali alterino la connettività funzionale a riposo (FC) attraverso disconnessioni strutturali sia dirette che indirette. 
Analizzando 114 pazienti con ictus in fase subacuta, gli autori stimano l'impatto del danno proiettando le lesioni su un atlante trattografico derivato da individui sani.
I risultati dimostrano che la **FC** subisce gravi **alterazioni** non solo quando le connessioni strutturali dirette vengono distrutte, ma anche quando la lesione va ad allungare i "percorsi strutturali più brevi" (Shortest Structural Path Length, SSPL) tra due regioni, creando una **disconnessione indiretta**. 
--> Entrambe le disconnessioni compromettono significativamente l'attività e la sincronizzazione delle reti cerebrali, sebbene l'effetto diretto tenda a prevalere per le connessioni FC positive.

---

## Domande scientifiche e Obiettivi
- Quali sono i precisi meccanismi strutturali alla base delle interruzioni della connettività funzionale (FC) causate da lesioni cerebrali focali?
- In che modo i danni focali alterano la comunicazione funzionale globale, specialmente tra regioni che non sono collegate direttamente da fasci di materia bianca ma si affidano a percorsi indiretti?
- **Obiettivo principale:** Stimare l'impatto dell'ictus sul connettoma strutturale e testare l'ipotesi che l'aumento della distanza nei percorsi strutturali (danno alle connessioni intermedie o "disconnessione indiretta") contribuisca in modo significativo alle alterazioni della connettività funzionale post-ictus, analogamente alle disconnessioni dirette.

## Metodologie
- **Campione:** 132 pazienti al primo ictus e 36 controlli sani della Washington University considerati inizialmente; dopo controlli di qualità (almeno 180 frame fMRI utilizzabili), il campione finale è di 114 pazienti (67% ischemici, 14% emorragici, 19% altre eziologie) e 24 controlli sani, valutati in fase subacuta (media 13.09 giorni, SD 4.75, dall'evento).
- **Creazione del Connettoma Strutturale:** È stato utilizzato l'atlante trattografico HCP-842 (costruito sui dati di diffusion MRI di 842 soggetti sani) combinato con la parcellizzazione corticale Gordon333 (333 regioni, ridotte a 324 dopo l'esclusione di 9 regioni con pochi vertici) e 35 regioni sottocorticali/cerebellari (34 dall'atlante AAL + 1 tronco encefalico dall'Harvard-Oxford Atlas), per un totale di 359 regioni volumetriche.
- **Calcolo delle Disconnessioni:** Le lesioni dei pazienti sono state incorporate nell'atlante per determinare le _disconnessioni strutturali dirette_ (streamline che intersecano la lesione). Applicando la teoria dei grafi, gli autori hanno poi misurato le _disconnessioni strutturali indirette_, calcolate quando una lesione causava un aumento della lunghezza del percorso strutturale più breve (SSPL) tra due regioni prive di connessione diretta.
- **Analisi Funzionale:** Dopo aver replicato nel gruppo di controllo la nota dipendenza della FC normale dalla SSPL, i ricercatori hanno applicato un'ANOVA a tre vie a misure ripetute (fattori: stato della connessione [risparmiata/disconnessa], tipo di connessione [diretta/indiretta], segno della FC normativa [positivo/negativo]) su 84 pazienti con dati completi.

## Risultati
- **Danno esteso su larga scala:** Nel sottoinsieme di 92 pazienti con almeno una disconnessione diretta cortico-corticale, in media il 19.03% delle coppie di regioni con connessione diretta e il 20.0% delle coppie con connessione indiretta risultavano rispettivamente disconnesse direttamente o indirettamente. L'estensione delle disconnessioni dirette e indirette è fortemente correlata tra loro (R²=0.78); le disconnessioni più estese derivavano principalmente da danni localizzati nella materia bianca profonda frontale, temporale e parietale.
- **Impatto funzionale a cascata:** Sia le regioni con disconnessione strutturale diretta sia quelle con disconnessione indiretta hanno mostrato deficit di FC significativamente più severi rispetto alle regioni con connessioni risparmiate.
- **Gerarchia del danno:** Per le connessioni FC di segno positivo, l'interruzione è risultata significativamente più severa per le coppie con disconnessione diretta rispetto a quelle con disconnessione indiretta; per le connessioni FC di segno negativo, invece, l'effetto delle disconnessioni dirette e indirette non è risultato significativamente diverso.

## Breve Discussione
- Le lesioni cerebrali innescano conseguenze ben oltre la zona necrotica primaria: i danni ai collegamenti strutturali intermedi allontanano "topologicamente" le regioni intatte, interferendo gravemente con la normale trasmissione di segnali in rete.
- I risultati espandono il concetto classico di "diaschisi" (la disfunzione remota dovuta a un danno focale), indicando chiaramente che queste alterazioni dipendono dai percorsi strutturali indiretti di materia bianca.
- Calcolare l'aumento della distanza nei percorsi strutturali più brevi (SSPL) offre una spiegazione meccanicistica più potente e completa per le anomalie funzionali a livello di network rispetto alla sola misurazione del volume o della topologia della lesione corticale focale.

# Bonkhoff et al. (2020)
_Acute ischaemic stroke alters the brain's preference for distinct dynamic connectivity states_

## Riassunto brevissimo
Questo studio utilizza la risonanza magnetica funzionale (**fMRI**) a riposo con un approccio **_dinamico_** (ad alta risoluzione temporale) per esplorare come l'ictus ischemico acuto alteri le reti del sistema motorio. 
Analizzando 31 pazienti e 17 controlli sani, gli autori scoprono tre "**stati di connettività**" **transitori**. 
I risultati dimostrano che l'ictus non altera solo la connettività globale in modo statico, ma modifica le preferenze temporali del cervello per specifici stati di attivazione, rivelando pattern nettamente diversi basati sulla gravità del deficit motorio iniziale (moderato vs grave) che i metodi classici non riuscivano a cogliere pienamente. I risultati principali sono stati confermati in un campione di replica indipendente.

---

## Domande scientifiche e Obiettivi
- In che modo l'ictus ischemico acuto altera le fluttuazioni temporali della connettività (connettività funzionale dinamica, dFNC) all'interno delle reti cerebrali motorie rispetto alle classiche misurazioni "statiche" (che mediano il segnale sull'intera scansione)?
- Le alterazioni nelle configurazioni dinamiche della connettività sono correlate alla gravità clinica del deficit (es. moderato vs grave)?
- **Obiettivo principale:** Utilizzare un'analisi a "finestra scorrevole" (_sliding window_) sui dati fMRI resting-state per identificare stati transitori di connettività e capire come le reti si riorganizzino dinamicamente nella primissima fase post-ictus.

## Metodologie
- **Campione:** 31 pazienti con un primo ictus ischemico acuto (scansionati in media a 7.2 giorni dall'esordio) con deficit motori alla mano (18 moderati, 13 gravi, valutati tramite ARAT) e 17 controlli sani abbinati per età.
- **Connettività Dinamica (dFNC):** A differenza della connettività statica, la dFNC è stata stimata su 13 componenti di rete motoria, analizzando i dati fMRI tramite finestre temporali di 44 secondi, shiftate di un TR (2.2 s) alla volta lungo tutta la scansione.
- **Clustering:** È stato applicato un algoritmo di apprendimento non supervisionato (_k-means clustering_) su tutte le finestre temporali per raggruppare i pattern di connettività ricorrenti. Questa analisi ha permesso di individuare 3 specifici "stati di connettività".
- **Metriche:** Sono state misurate svariate dinamiche: il tempo di permanenza in uno stato (_dwell time_), la frequenza globale (_fraction time_), la probabilità di transizione tra stati e un indice di segregazione dei network (calcolato sia sulla connettività statica sia su ciascuna finestra dinamica).
- **Replica:** le analisi principali sono state ripetute su un campione indipendente di 24 pazienti con ictus e deficit motori vs 30 pazienti con ictus ma senza deficit motori.

## Risultati
- **Tre stati dinamici:** Stato 1, densamente connesso localmente e fortemente segregato tra domini diversi — è anche lo stato il cui pattern complessivo assomiglia di più alla connettività statica dello studio. Stato 2, debolmente connesso sia localmente che a distanza. Stato 3, intermedio — non il più simile alla connettività statica in assoluto, ma quello le cui alterazioni paziente-vs-controllo ricalcano più da vicino i risultati precedentemente riportati in letteratura da studi di connettività statica post-ictus.
- **Pazienti moderati:** hanno trascorso un tempo significativamente maggiore (fraction time e dwell time) nello Stato 2 rispetto ai controlli sani; rispetto ai pazienti gravi la differenza è solo una tendenza (fraction time) o non significativa (dwell time). La probabilità di rimanere nello Stato 2 è invece significativamente più alta sia rispetto ai controlli sia rispetto ai gravi.
- **Pazienti gravi:** hanno mostrato una probabilità significativamente maggiore di transitare verso lo Stato 1 rispetto ai moderati, coerente con la loro maggiore segregazione dominio-dominio.
- **Superiorità dell'analisi dinamica:** nell'analisi statica non emerge alcuna differenza di segregazione dominio-dominio tra i tre gruppi, pur avendo comunque rilevato alterazioni significative in singole coppie di connettività between/within-network. Nell'analisi dinamica, invece, la segregazione differisce significativamente tra i gruppi: moderati < controlli < gravi. Risultato inatteso: i pazienti moderati mostrano complessivamente più alterazioni di connettività (statiche e dinamiche) rispetto ai controlli di quanto non facciano i pazienti gravi, nonostante il deficit clinico meno marcato.
- **Replica:** nel campione indipendente sono stati confermati lo stesso pattern a 3 stati, il maggior dwell time nello Stato 2 per i pazienti moderati, e le stesse differenze di segregazione.

## Breve Discussione
- L'ictus acuto non riduce solo le connessioni fisiche o funzionali statiche, ma altera profondamente la flessibilità temporale della rete, ovvero la "preferenza" del cervello nel transitare e sostare tra i vari stati di connettività.
- La preferenza dei pazienti gravi per uno stato altamente segregato (Stato 1) potrebbe riflettere un primo tentativo di riorganizzazione o compensazione mirata per recuperare le funzioni perse (isolando le reti compromesse). Al contrario, la bassa segregazione nei pazienti moderati (Stato 2) potrebbe rappresentare una firma di plasticità precoce in cui reti meno vincolate facilitano lo stabilirsi di nuove connessioni flessibili — non necessariamente una firma di disfunzione.
- L'approccio dFNC si rivela un biomarcatore più sensibile della connettività statica, con risultati confermati in un secondo campione indipendente. Capire queste dinamiche temporali apre nuove prospettive sui meccanismi neurali del recupero, fornendo informazioni critiche che un giorno potrebbero guidare interventi di neuromodulazione precoce (es. rTMS, tDCS) per favorire le traiettorie riabilitative ottimali.


# Griffis et al. (2019) 
_Structural Disconnections Explain Brain Network Dysfunction after Stroke_

## Riassunto brevissimo
Questo studio sfida l'assunto tradizionale secondo cui le disfunzioni delle reti cerebrali post-ictus (misurate tramite fMRI) derivino principalmente dal danno locale a specifiche regioni critiche di materia grigia. 
Analizzando 114 pazienti (con 24 controlli sani abbinati per i confronti di FC), gli autori dimostrano invece che le **alterazioni della connettività** **funzionale** dipendono in modo preponderante dalla disconnessione strutturale (**SDC**) dei fasci di **materia bianca**. 
--> I risultati evidenziano che le disconnessioni fisiche dei tratti, in particolare quelli **interemisferici**, causano diffuse interruzioni funzionali a cascata, spiegando il crollo della modularità e dell'integrazione delle reti molto meglio di quanto non faccia il danno locale alla corteccia, e che questo pattern strutturo-funzionale correla con i deficit comportamentali in più domini clinici.

---

## Domande scientifiche e Obiettivi
- Le disfunzioni delle reti cerebrali (alterazioni della connettività funzionale) che seguono un ictus focale sono causate principalmente dal danno locale alla materia grigia (compresi i cosiddetti "hub" corticali) o dall'interruzione delle connessioni di materia bianca?
- Esiste una relazione coerente e topografica tra i pattern di disconnessione strutturale (SDC) e il crollo della connettività funzionale (FC)?
- **Obiettivo principale:** Confrontare direttamente il potere esplicativo dei modelli basati sul danno locale (materia grigia) con quelli basati sulle disconnessioni strutturali della materia bianca, per spiegare i deficit di connettività funzionale a riposo.

## Metodologie

- **Campione:** 114 pazienti con ictus in fase subacuta (media 13.09 giorni, SD 4.75, dall'evento) valutati con risonanza magnetica strutturale e funzionale (fMRI resting-state); 24 controlli sani abbinati usati per i confronti di FC e per definire le misure di hub corticale.
- **Mappatura del danno e delle disconnessioni:** Le lesioni sono state mappate calcolando sia il danno focale diretto (a livello di voxel e di regioni di materia grigia), sia proiettandole su un atlante trattografico (842 soggetti HCP) di soggetti sani per stimare le disconnessioni strutturali (SDC) a livello di tratto e di connessione regione-regione.
- **Analisi Statistiche (PLSR e PLSC):** Il confronto tra danno agli "hub" corticali e SDC totale sulla perdita di modularità è stato condotto con regressioni lineari multiple nidificate e correlazioni parziali. Successivamente, la _Partial Least Squares Regression_ (PLSR) è stata usata per confrontare quattro misure strutturali (danno voxel/region-based, SDC tract/region-based) come predittori di 12 misure di FC di rete. Infine, la _Partial Least Squares Correlation_ (PLSC) è stata impiegata sui dati completi di SDC e FC per estrarre variabili latenti e analizzare la covarianza multivariata tra i pattern strutturali e quelli funzionali.

## Risultati
- **Superiorità delle SDC:** I modelli basati sulle disconnessioni strutturali (SDC) hanno spiegato in modo nettamente superiore le disfunzioni di rete post-ictus rispetto ai modelli basati sul danno focale alla materia grigia o agli "hub" (nodi centrali) corticali; l'aggiunta della SDC totale al modello di modularità aumentava la varianza spiegata di un fattore ~2.5 (R²=0.10→0.25).
- **Il ruolo chiave delle fibre interemisferiche:** Le disconnessioni strutturali interemisferiche si sono rivelate le principali responsabili delle diffuse interruzioni della connettività funzionale, portando a una riduzione globale dell'integrazione e della segregazione all'interno e tra i network.
- **Relazione topografica a bassa dimensionalità:** L'analisi PLSC ha rivelato che i pattern di disconnessione strutturale e di disfunzione funzionale sono strettamente collegati da una struttura a bassa dimensionalità: la prima componente latente (LV1) spiegava il 45% della covarianza totale, con punteggi SDC/FC fortemente correlati tra pazienti (99% CI = 0.73-0.78). La sovrapposizione topografica tra i loading SDC e FC di LV1 era però debole seppur significativa, pronunciata quasi solo per le connessioni all'interno dello stesso network.
- **Correlazione con il comportamento:** L'espressione di LV1 correlava significativamente con i deficit comportamentali in più domini (linguaggio, attenzione, memoria spaziale, motorio), anche correggendo per il volume della lesione.

## Breve Discussione
- Il paper ribalta un dogma classico: non è la "morte" o il danno del tessuto corticale in sé a generare i più gravi deficit di network su larga scala, ma la recisione dei "cavi di comunicazione" di materia bianca che collegano le aree intatte.
- Le lesioni focali innescano una disfunzione globale e stereotipata (perdita di modularità) che dipende intimamente dall'architettura delle connessioni strutturali distrutte, con i tratti interemisferici che giocano un ruolo critico.
- Il singolo pattern strutturo-funzionale individuato (LV1) ricapitola le principali disfunzioni di FC già note in letteratura per la loro relazione col comportamento.
- L'inclusione delle stime di disconnessione della materia bianca è un passo imprescindibile per comprendere le basi neurali dei deficit funzionali post-ictus; basarsi unicamente sulla posizione della lesione corticale fornisce un quadro parziale e con minor potere esplicativo.

# Corbetta et al. (2018) 
_On the low dimensionality of behavioral deficits and alterations of brain network connectivity after focal injury_
## Riassunto brevissimo
Questo articolo di rassegna (_review_) propone un modello concettuale a tre vie che collega il danno anatomico strutturale, le alterazioni fisiologiche dei network e i deficit comportamentali post-ictus. Gli autori sostengono che la natura prevalentemente sottocorticale e di materia bianca delle lesioni da ictus, insieme alla diffusione degli effetti fisiologici ben oltre il sito di danno, induca alterazioni diffuse di connettività funzionale (inclusa una riduzione di modularità). Questa disfunzione fisiologica diffusa riduce l'entropia (ovvero la variabilità) degli stati neurali che il cervello può esplorare, spiegando perché i molteplici deficit clinici si manifestino in una struttura a bassa dimensionalità.

---

## Domande scientifiche e Obiettivi
- In che modo il danno strutturale focale (che colpisce principalmente la materia bianca e le regioni sottocorticali) si traduce in disfunzioni fisiologiche diffuse a livello di network remoti?
- Qual è il meccanismo neurale alla base della bassa dimensionalità dei deficit comportamentali post-ictus e come questo si relaziona con le alterazioni della connettività funzionale (FC)?
- **Obiettivo principale:** Proporre una sintesi teorica e un modello fisiologico (basato sulla riduzione dell'entropia degli stati neurali) per spiegare la mappatura a tre vie fra lesione strutturale, connettività funzionale e fenotipi comportamentali a livello di popolazione.

## Metodologie
- **Sintesi e integrazione di dati di popolazione:** Trattandosi di un articolo di rassegna, gli autori integrano e discutono dati empirici longitudinali e trasversali di più coorti prospettiche di pazienti con ictus, in particolare un campione Washington University di n = 132 pazienti acuti valutati con una batteria neuropsicologica dettagliata (42 test, 6 domini) (Corbetta et al., 2015; Ramsey et al., 2017); i dati di connettività funzionale (resting-state fMRI) discussi provengono da studi correlati sulla stessa popolazione clinica (Baldassarre et al., 2014; Siegel et al., 2016).
- **Modellistica computazionale _whole-brain_:** Vengono discussi modelli computazionali realistici che simulano l'effetto delle lesioni sul connettoma strutturale (Adhikari et al., 2017; Saenger et al., 2017), valutando metriche di integrazione, segregazione ed entropia dei nodi.
- **Analisi di rete e teoria dei grafi:** Discussione dell'applicazione di metriche globali di rete, in particolare la modularità (bilancio tra integrazione interna ed estesa segregazione dei network), come potenziale biomarcatore neurofisiologico del danno e del recupero.

## Risultati
- **Conferma della bassa dimensionalità:** Già la NIHSS (batteria grossolana) mostra 2 fattori che spiegano oltre l'80% della varianza (Zandieh et al., 2012). Con una batteria molto più estesa (42 test su 6 domini), la maggior parte della varianza comportamentale post-ictus resta comunque catturata da pochi fattori principali, sintetizzabili in una componente motoria-attentiva e una componente cognitiva linguaggio-memoria. Gli autori escludono esplicitamente che questa struttura sia spiegata dalla semplice appartenenza a uno stesso territorio vascolare (memoria spaziale e verbale sono scarsamente predette dalla topografia lesionale); la spiegano invece con il danno preferenziale a sostanza bianca/sottocorticale e con la diffusione fisiologica degli effetti ben oltre il sito di lesione.
- **Fenotipi di FC anomala:** Le alterazioni della connettività funzionale si manifestano in pattern diffusi e topograficamente specifici, caratterizzati principalmente da due anomalie: (1) perdita di connettività interemisferica homotopic e (2) un aumento anomalo della connettività intraemisferica tra network normalmente segregati (es. default mode network e dorsal attention network).
- **Perdita di entropia e di stati neurali:** Sia i dati empirici fMRI sia le simulazioni computazionali dimostrano che le lesioni provocano una riduzione dell'entropia dei nodi (variabilità dei segnali) non solo nell'emisfero danneggiato ma anche in quello sano, correlata alla perdita di FC interemisferica, riducendo la complessità e la capacità di esplorazione degli stati neurali del cervello.
- **La modularità correla con il recupero:** Il ripristino/normalizzazione della connettività funzionale su larga scala, in particolare un aumento della modularità, è fortemente associato al recupero neurologico longitudinale (Siegel, Seitzman et al., 2018) ed è proposto dagli autori come possibile biomarcatore/target — non presentato nel testo come "il" fattore predittivo principale in senso comparativo rispetto ad altri.

## Breve Discussione
- **Dalla specificità locale all'interazione di network:** La neuropsicologia deve evolvere da una visione puramente modulare e focalizzata su singoli casi di dissociazioni "pure" verso modelli che considerino le interazioni dinamiche tra sistemi distribuiti su larga scala.
- **La variabilità come target riabilitativo:** Se la ridotta variabilità degli stati neurali limita il repertorio comportamentale del paziente, l'obiettivo primario della riabilitazione e della neurostimolazione (es. TMS o tDCS) dovrebbe essere la normalizzazione di questa variabilità e il ripristino della modularità globale, piuttosto che la stimolazione di un singolo sito focale.
- **Necessità di stimolazione multi-sito:** Data la natura intrinsecamente diffusa delle alterazioni di FC che supportano i deficit cognitivi, i protocolli terapeutici futuri dovranno probabilmente affidarsi a stimolazioni multi-sito, guidate da modelli computazionali personalizzati.

# Siegel et al. (2016) - Siegel et al. (2018)
- *Disruptions of network connectivity predict impairment in multiple behavioral domains after stroke*
- *Re-emergence of modular brain networks in stroke recovery*

## Riassunto brevissimo
Questi due lavori complementari dimostrano che l'ictus non causa solo danni focali, ma altera profondamente l'**organizzazione globale e dinamica dei network** cerebrali. 
Nel 2016, gli autori scoprono che la disfunzione dei network (misurata con fMRI) predice i deficit cognitivi complessi (come la memoria) molto meglio della sola mappa strutturale della lesione, che è invece più accurata per i deficit sensomotori. 
Nel 2018, lo studio longitudinale rivela che l'architettura dei network, in particolare la loro "modularità", crolla nella fase subacuta ma riemerge nel tempo — soprattutto tra le 2 settimane e i 3 mesi, per poi stabilizzarsi. Fondamentalmente, il ripristino di questa modularità va di pari passo con il recupero clinico delle funzioni cognitive superiori (linguaggio, memoria spaziale, attenzione), ma non di quelle motorie o visive.

---

## Domande scientifiche e Obiettivi
- Le lesioni anatomiche strutturali e le alterazioni della connettività funzionale (FC) predicono in modo diverso l'impatto dell'ictus su svariati domini comportamentali?
- Come cambia l'architettura globale del cervello, in termini di integrazione e segregazione ("modularità"), durante le diverse fasi del recupero post-ictus?
- C'è una correlazione tra il ripristino della normale architettura di rete (modularità) e il recupero clinico del paziente in domini specifici?
- **Obiettivo combinato:** Collegare le caratteristiche organizzative su larga scala dei network cerebrali ai deficit iniziali (2016) e mapparne l'evoluzione nel tempo per prevedere le traiettorie di guarigione (2018).

## Metodologie
- **Campione:** Coorte di 132 pazienti al primo ictus (2016, valutati 1-2 settimane dopo l'evento) e 31 controlli sani abbinati reclutati; dopo esclusioni per lag emodinamico e motion, le analisi FC del 2016 sono condotte su n=100 pazienti e n=27 controlli. Il paper del 2018 segue longitudinalmente la stessa coorte di partenza applicando propri criteri di qualità-dati, arrivando a n=107 (2 settimane), n=85 (3 mesi) e n=67 (1 anno).
- **Valutazione Comportamentale:** È stata somministrata un'estesa batteria di test in molteplici domini (attenzione, memoria verbale e spaziale/visiva, linguaggio, motricità e visione), poi ridotta tramite Analisi delle Componenti Principali (PCA) in punteggi globali per dominio.
- **Neuroimaging e Machine Learning (2016):** Sono state acquisite risonanze strutturali e funzionali (fMRI a riposo). Gli autori hanno utilizzato modelli di _machine learning_ (Ridge Regression e Multi-Task Learning) per prevedere il grado di deficit neurologico di ogni singolo soggetto partendo o dalla topografia della lesione o dalla connettività funzionale.
- **Analisi Longitudinale dei Grafi (2018):** Utilizzando la teoria dei grafi, i ricercatori hanno calcolato la "modularità" (Newman's Q) dei network nel corso del tempo, ovvero la misura in cui i sistemi cerebrali mostrano un'alta integrazione (connessioni dense al proprio interno) e un'alta segregazione (poche connessioni verso altre reti).

## Risultati
- **Doppia dissociazione predittiva (2016):** I deficit di memoria (visiva/spaziale e verbale) sono previsti in modo decisamente migliore dalle alterazioni della connettività funzionale. Al contrario, i danni motori e visivi sono previsti meglio dalla topografia della lesione strutturale. Il linguaggio è predetto in modo equivalente da entrambi gli approcci; l'attenzione mostra invece solo un trend (non significativo) verso una predizione migliore da parte della FC.
- **Alterazione globale dei network (2016 e 2018):** L'ictus causa un pattern generale di disfunzione di rete caratterizzato dalla diminuzione dell'integrazione interemisferica (FC omotopica) e dalla perdita di segregazione intraemisferica. Questa perdita di architettura modulare si presenta già in fase subacuta ed è correlata alla dimensione della lesione (non alla sua topografia specifica).
- **Recupero della Modularità (2018):** Mentre le aree corticali mantengono i loro confini anatomici, la modularità dei sistemi cerebrali, gravemente compromessa a due settimane dall'evento (soprattutto nell'emisfero ipsilesionale), mostra un recupero significativo tra le 2 settimane e i 3 mesi; tra i 3 mesi e 1 anno il recupero si stabilizza, senza ulteriore aumento significativo.
- **Correlazione con la clinica (2018):** Il recupero della modularità correla significativamente con il recupero dei deficit di linguaggio, memoria spaziale e attenzione (la memoria verbale mostra solo un trend). Al contrario, non vi è associazione significativa tra il recupero della modularità globale e il recupero delle funzioni più basiche, come quelle motorie o visive.

## Breve Discussione
- Questi studi stabiliscono un principio fondamentale nella neurobiologia dell'ictus: mentre le funzioni sensomotorie primarie dipendono in gran parte dall'integrità anatomica di aree e fasci specifici, le funzioni cognitive superiori (come la memoria, l'attenzione e il linguaggio) emergono dalla complessa e flessibile interazione di network distribuiti.
- Il cervello sano si affida a un'architettura "modulare" ad alta efficienza; la distruzione e la successiva "riemersione" di questa modularità (ovvero la capacità delle reti di tornare a comunicare bene al proprio interno e a isolarsi correttamente dalle altre) rappresenta un potentissimo biomarcatore fisiologico per il recupero cognitivo, in parte indipendente dai marcatori di FC già noti.
- A livello clinico e terapeutico, questi dati suggeriscono che le future strategie di riabilitazione orientate al recupero delle funzioni cognitive superiori non dovrebbero limitarsi a stimolare l'area perilesionale, ma dovrebbero mirare a normalizzare il flusso di informazioni e l'organizzazione dei sistemi cerebrali su larga scala.

# Corbetta et al. (2015)
_Common Behavioral Clusters and Subcortical Anatomy in Stroke_

## Riassunto brevissimo
Questo studio fondamentale sfida la visione neurologica tradizionale secondo cui l'ictus causa sindromi comportamentali altamente specifiche dovute a danni corticali focali. 
Analizzando 132 pazienti in fase acuta (1-2 settimane dall'evento), gli autori dimostrano che i deficit post-ictus sono in realtà fortemente correlati tra loro e si raggruppano in un numero ridotto di "cluster" comportamentali. Inoltre, la topografia tipica dell'ictus non è corticale, ma prevalentemente sottocorticale e coinvolge massicciamente la materia bianca. 
I risultati evidenziano che la mera localizzazione del danno strutturale predice molto bene i deficit motori e linguistici, ma è molto meno efficace per memoria (specialmente spaziale) e attenzione, sottolineando il ruolo critico e spesso sottovalutato delle disconnessioni della materia bianca nel generare deficit multipli.

---

## Domande scientifiche e Obiettivi
- I deficit neurologici post-ictus si presentano davvero come sindromi modulari e isolate, o sono fortemente correlati tra loro all'interno della popolazione?
- Qual è la topografia anatomica reale dell'ictus in un ampio campione clinico rappresentativo?
- Quanto della variabilità dei deficit in diversi domini (motorio, linguaggio, memoria, attenzione) può essere spiegata unicamente dalla localizzazione spaziale del danno strutturale?
- **Obiettivo principale:** Utilizzare un approccio multivariato (_machine learning_) per esaminare le relazioni tra lesione e comportamento su domini multipli, al fine di quantificare la varianza clinica spiegata dal danno anatomico strutturale.

## Metodologie

- **Campione:** 132 pazienti al primo ictus (ischemico o emorragico, su 172 arruolati), valutati in modo prospettico in fase acuta (media 13 ± 4.9 giorni dall'esordio), confrontati con un gruppo di controlli sani e con una popolazione sorgente di 1.209 pazienti dello stesso ospedale (usata per verificare la rappresentatività clinica del campione).
- **Valutazione Comportamentale:** È stata somministrata un'ampia batteria di test per misurare attenzione, memoria (verbale e spaziale), linguaggio, funzioni motorie e visive. I dati clinici sono stati compressi tramite Analisi delle Componenti Principali (PCA), prima separatamente per ciascun dominio (within-domain), poi con una PCA di ordine superiore sui fattori così ottenuti, per individuare fattori comportamentali latenti trasversali ai domini.
- **Mappatura Anatomica:** Le lesioni sono state segmentate su risonanze strutturali (T1, T2, FLAIR) e classificate (corticale, cortico-sottocorticale, sottocorticale, solo materia bianca, tronco encefalico, cervelletto). Per studiare le disconnessioni, i danni sono stati sovrapposti a un atlante probabilistico trattografico (57 tratti) costruito su 40 soggetti sani.
- **Machine Learning:** È stato utilizzato un algoritmo multivariato di _Ridge Regression_ (con validazione _leave-one-out_) per prevedere i punteggi comportamentali individuali partendo unicamente dalla distribuzione dei voxel danneggiati, permettendo di quantificare la percentuale esatta di varianza clinica spiegata dall'anatomia.
- **Analisi di controllo:** la struttura di correlazione comportamentale è stata verificata come indipendente dal volume lesionale (correlazione parziale), dall'esclusione di lesioni di tronco encefalico/cervelletto, e confrontando un sottogruppo puramente sottocorticale con uno corticale (struttura di correlazione simile in entrambi).

## Risultati

- **Analisi within-domain:** all'interno di ciascun dominio, pochi fattori spiegano la maggior parte della varianza: motorio (n=117), 2 fattori (lato sinistro/destro) per il 77%; linguaggio (n=124), 1 fattore per il 76%; memoria (n=98), 2 fattori (verbale/spaziale) per il 66%; attenzione (n=101), 3 fattori per il 57%.
- **Tre macro-cluster comportamentali trasversali:** l'analisi across-domain (su n=67 pazienti con dati completi in tutti i domini) ha rivelato che il 69% della variabilità clinica globale si riduce a soli tre macro-fattori correlati ("uber-factors"): (1) linguaggio associato a memoria verbale e spaziale, (2) deficit motori sinistri associati a bias del campo visivo e prestazioni attentive generali (lateralizzato all'emisfero destro), e (3) deficit motori destri associati a bias del campo visivo e spostamento dell'attenzione ("attention shifting", lateralizzato all'emisfero sinistro).
- **Danno prevalentemente sottocorticale:** la topografia tipica dell'ictus ha mostrato che le lesioni puramente corticali sono rare (13%). Le altre categorie: tronco encefalico 7%, cervelletto 17%, cortico-sottocorticale 23%, sottocorticale 16%, solo materia bianca 23%; sommando le due categorie sottocorticali, il 39% delle lesioni ha topografia sottocorticale.
- **Potere predittivo della struttura:** la sola localizzazione del danno (dati di _Ridge Regression_) ha spiegato in modo eccellente la varianza dei deficit motori (54% lato sinistro, 27% destro) e del linguaggio (44%), in modo moderato l'attenzione (34%), e in modo molto più debole la memoria verbale (17%) e soprattutto la memoria spaziale (solo il 4%, il valore più basso dello studio). Il solo volume lesionale non ha mai spiegato più del 20% della varianza in nessun dominio.
- **Disconnessione ai crocevia:** le regioni in cui il danno strutturale causava i deficit più severi e multipli (in 5 o 6 domini contemporaneamente) si localizzavano bilateralmente nella materia bianca frontale dorsale, nei talami e nei gangli della base — corrispondendo ai "crocevia" dove transitano e si sovrappongono numerosi tratti di fibre.

## Breve Discussione
- Mentre la neurologia storica si è concentrata su casi rari di pazienti con lesioni corticali focali che mostrano sindromi "pure" (la "punta dell'iceberg"), la stragrande maggioranza dei pazienti clinici (la "massa dell'iceberg") presenta deficit fortemente correlati.
- La correlazione comportamentale è attribuita alla topografia prevalentemente sottocorticale/materia bianca dell'ictus e al danno di tratti di materia bianca, specialmente nelle regioni di crocevia ad alta sovrapposizione di tratti — non spiegata dal solo volume lesionale né dalla mera prevalenza di lesioni sottocorticali nel campione.
- Vi è una fondamentale distinzione neurobiologica: funzioni come il movimento e il linguaggio dipendono ancora fortemente dall'integrità strutturale di vie specifiche (es. fascio cortico-spinale). Al contrario, funzioni cognitive distribuite come la memoria e l'attenzione dipendono da network globali, per i quali il semplice danno strutturale focale non è sufficiente a spiegare il deficit clinico. Questo lavoro ha quindi posto le basi fisiologiche per comprendere la necessità di esplorare le disconnessioni di rete (es. con fMRI, come faranno i successivi lavori di Siegel et al., 2016 e Griffis et al., 2019) per capire i danni cognitivi complessi.