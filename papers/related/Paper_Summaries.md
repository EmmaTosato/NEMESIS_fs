# Keator et al. (2021)
_Independent contributions of structural and functional connectivity: Evidence from a stroke model_

## Riassunto brevissimo
Questo studio analizza 97 pazienti con ictus cronico all'emisfero sinistro per comprendere il ruolo indipendente della connettività funzionale a riposo (rsFC) rispetto alla connettività strutturale. I risultati mostrano che una ridotta rsFC nella "via ventrale" (ventral stream) dell'emisfero sinistro - in particolare nelle regioni temporoparietali e frontotemporali - è associata a deficit nella comprensione del linguaggio (Auditory Verbal Comprehension). L'effetto si mantiene significativo anche dopo aver controllato per il volume della lesione locale e per l'integrità dei tratti di materia bianca strutturali diretti. Questo suggerisce che la rsFC catturi un segnale indipendente dal mero danno strutturale (affidandosi probabilmente a connessioni indirette residue) e rappresenti un biomarcatore predittivo importante per il recupero.

## Domande scientifiche e Obiettivi
- Il deficit di comprensione correla con la rsFC nelle regioni bilaterali del ventral stream?
- La produzione del linguaggio (spontaneous speech) correla con la rsFC nel dorsal stream sinistro?
- La rsFC spiega i punteggi di comprensione o produzione in modo indipendente, dopo aver controllato per i fattori confondenti anatomici (volume totale della lesione e connettività strutturale danneggiata)?

## Metodologie
- **Campione:** 97 pazienti in fase cronica (> 1 anno, media 54.64 mesi) con ictus all'emisfero sinistro (40 donne, età 56.01 ± 11.83 anni).
- **Valutazione Comportamentale:** Punteggi estratti dal Western Aphasia Battery-Revised (WAB-R) per Auditory Verbal Comprehension (basato su domande Sì/No, riconoscimento di parole, comandi sequenziali, max 10) e Spontaneous Speech (fluenza e contenuto, max 20).
- **Imaging:** T1, T2 (per le maschere lesionali), DTI (per trattografia probabilistica della connettività strutturale) e rs-fMRI (connettività funzionale).
- **Parcellizzazione:** 108 ROIs dall'atlante AICHA (26 dorsali, 82 ventrali, bilanciate o lateralizzate secondo il dual-stream model di Hickok & Poeppel).
- **Analisi Statistiche (GLM):** Regressioni lineari multiple con 5000 permutazioni per il controllo delle comparazioni multiple. Modelli a complessità crescente controllando prima per il solo volume lesionale totale, poi per volume + numero di fibre strutturali (DTI), e infine per volume limitato alle sole 'critical areas' temporoparietali + DTI.

## Risultati
- **Lesion-Symptom Mapping:** Il danno all'area STG (z = 2.97) correla con ridotta comprensione, mentre il danno all'opercolo rolandico (z = -2.92 e -2.97) correla con ridotta produzione (Spontaneous Speech).
- **Connettività Strutturale:** L'integrità di 7 pathway strutturali ipsilesionali ha predetto i punteggi di comprensione (z = 3.81-4.40; in particolare tra superior temporal sulcus sinistro e middle temporal gyrus sinistro). 6 pathway (molti dei quali interemisferici) hanno predetto la produzione (z = 3.84-4.56). Nessun tratto intraemisferico destro era predittivo.
- **rsFC controllata per volume lesionale:** 5 connessioni funzionali temporoparietali esclusive del ventral stream sinistro (es. inferior parietal gyrus - middle temporal gyrus) hanno predetto i punteggi di comprensione (z = 4.32-4.96). Nessuna connessione funzionale ha predetto significativamente la produzione.
- **rsFC controllata per volume + connettività strutturale:** 4 delle connessioni temporoparietali precedenti sono rimaste predittori significativi (z = 4.29-4.64), dimostrando un contributo indipendente dalla disconnessione strutturale diretta.
- **rsFC controllata per 'critical areas' + strutturale:** Anche limitando la rimozione della varianza al volume lesionale delle specifiche aree temporoparietali colpite, 2 connessioni (inferior parietal - middle temporal, z = 3.94; e inferior frontal - superior temporal sulcus) sono rimaste predittori significativi del deficit di comprensione.

## Breve Discussione
- La connettività funzionale a riposo (rsFC) fornisce informazioni predittive sulle prestazioni linguistiche (comprensione) che non sono spiegabili unicamente dai dati lesionali o dalla perdita di connessioni strutturali dirette.
- Poiché la predittività funzionale resiste alla covariazione strutturale, gli autori suggeriscono che tali connessioni rsFC debbano basarsi su pathway strutturali "indiretti" intatti che aggirano il danno, forse a testimonianza di processi plastici compensatori sviluppati nella fase cronica.
- Mancano evidenze per la produzione verbale, forse a causa della natura troppo "grossolana" o soggettiva del punteggio Spontaneous Speech della WAB-R.
- Tra i limiti vengono evidenziati l'assenza di un gruppo di controllo sano (che impedisce il confronto con l'architettura di rete standard), i limiti della trattografia probabilistica nel ricostruire fasci specifici, e l'utilizzo di test clinici di base invece di test linguistici discreti e controllati.

---

# Zhou et al. (2025)
_Structural and EEG motor networks distinguish level of motor impairment after stroke_

## Riassunto brevissimo
Questo studio su 57 pazienti post-ictus indaga i network motori integrando la connettività strutturale (derivata dalla proiezione delle lesioni su trattografie sane) con la connettività funzionale EEG (informata dai vincoli strutturali individuali). I risultati dimostrano che la disconnessione strutturale tra tronco encefalico e le aree M1/PMd ipsilesionali predice fortemente un deficit motorio severo (Fugl-Meyer < 42). I pazienti con recupero migliore (high status) presentano metriche di rete globale (centralità, efficienza) maggiori nelle aree motorie ipsilesionali (soprattutto nella banda funzionale EEG delta 1-3 Hz) e un'attivazione compensatoria nelle aree motorie contralesionali nella banda beta (14-29 Hz). Grazie a una nuova metrica ("motor betweenness centrality"), gli autori dimostrano che il cattivo recupero è associato a una plasticità maladattiva, in cui i segnali motori vengono reindirizzati attraverso regioni corticali non motorie molto distanti e meno efficienti.

## Domande scientifiche e Obiettivi
- Quali specifici pattern di connettività cerebrale (strutturale e funzionale) si associano alla gravità del deficit motorio post-ictus?
- Come varia l'efficienza della rete motoria, analizzando il network tra il tronco encefalico e 3 aree corticali chiave (corteccia motoria primaria M1, corteccia premotoria dorsale PMd, area motoria supplementare SFG) in entrambi gli emisferi?
- Può la connettività funzionale EEG identificare i percorsi di "rerouting" (plasticità neurale compensatoria) dei segnali motori al di fuori delle aree motorie primarie?

## Metodologie
- **Campione:** 57 pazienti post-ictus valutati con il Fugl-Meyer Assessment (FMA-UE) per l'arto superiore, divisi in due gruppi: High (H, n=28, FM ≥ 42) e Low (L, n=29, FM < 42).
- **Connettività Strutturale:** Il "reduced structural connectome" di ogni paziente è stato calcolato proiettando la maschera della lesione su un connettoma sano di riferimento (463 ROIs da atlante Lausanne, 133.815 streamline da HCP 842). 50 pazienti sono stati usati per l'analisi delle centralità corticali (escludendo il tronco encefalico per evitare connessioni spurie).
- **Connettività Funzionale EEG:** Dati a riposo da 256 canali, mappati su 448 ROIs corticali (usando la PCA per aggregare i dipoli). La coerenza parziale è stata stimata tramite un modello grafico (cGGM) penalizzato dal ridotto connettoma strutturale di ogni paziente, isolando le connessioni dirette per minimizzare la conduzione di volume, suddivise in 6 bande di frequenza (delta, theta, alpha, mu, beta1, beta2).
- **Metriche di Rete:** degree centrality, average efficiency e betweenness centrality per le 3 aree motorie (M1, PMd, SFG). È stata inoltre introdotta la "motor betweenness centrality" per quantificare quante delle vie più brevi in partenza dal sistema motorio passino per una data regione non motoria.

## Risultati
- **Disconnessioni Strutturali:** La recisione strutturale tra tronco encefalico e PMd ipsilesionale (associata quasi sempre anche a M1) è il miglior predittore del gruppo L. Le aree M1, PMd e SFG ipsilesionali nel gruppo L hanno un netto calo di degree centrality, average efficiency e betweenness centrality strutturali.
- **Rerouting Strutturale:** Nel gruppo L, la "motor betweenness centrality" aumenta in aree corticali non-motorie distanti, segno che il cervello reindirizza le informazioni lungo percorsi indiretti e inefficienti.
- **Connettività Funzionale (Aree Motorie):** Il gruppo H mostra network funzionali motori potenziati. La differenza più marcata emerge nella banda delta (1-3 Hz) per l'M1 ipsilesionale (centralità ed efficienza maggiori). Nella banda beta (14-29 Hz), il gruppo H si distingue per una connettività aumentata nelle aree motorie contralesionali, indicando plasticità compensatoria utile.
- **Rerouting Funzionale:** Nella banda beta1 (14-20 Hz), i pazienti migliori (H) usano aree corticali immediatamente adiacenti all'M1 ipsilesionale per l'instradamento, mentre nelle bande delta e beta2 i pazienti più gravi (L) ripiegano su aree lontane.

## Breve Discussione
- L'integrità strutturale del circuito motorio definisce la gravità biologica di partenza (extent of injury), mentre la connettività EEG riflette la successiva plasticità adattiva nel tempo (e a vari stadi cronici).
- Le oscillazioni a bassa frequenza (delta) marcano le dinamiche di recupero ipsilesionale, mentre le frequenze beta catturano il contributo compensatorio dell'emisfero sano.
- La nuova metrica di "motor betweenness centrality" supporta l'ipotesi della plasticità maladattiva: i buoni recuperi dipendono dall'uso di circuiti locali prossimali, mentre i recuperi scarsi si poggiano su "strade secondarie" inefficienti in distretti non motori.
- Tra i limiti dello studio figurano l'esclusione di strutture critiche come il cervelletto e i gangli della base nei modelli EEG corticali, e la non differenziazione tra dinamiche di fase e di ampiezza nella stima della coerenza funzionale.

---

# Wang et al. (2025)
_Neuroimaging and biological markers of different paretic hand outcomes after stroke_

## Riassunto brevissimo
Questo studio ha analizzato 65 pazienti cronici con ictus sottocorticale (32 con mano parzialmente paretica - PPH, 33 con mano completamente paretica - CPH) per identificare biomarcatori fMRI a riposo (rs-fMRI) e associarli a profili trascrittomici e di neurotrasmettitori. L'Amplitude of Low-Frequency Fluctuation (ALFF) è emersa come la migliore metrica per classificare e predire l'esito motorio (accuratezza 0.88), superando significativamente ReHo, DC e VMHC. Le regioni più discriminanti includono il giro precentrale ipsilesionale, il lobo posteriore del cervelletto contralesionale e il lobulo parietale inferiore ipsilesionale. L'analisi spaziale ha collegato questi biomarcatori ALFF ai pathway dei recettori accoppiati a proteine G, a un'alta espressione specifica negli astrociti e ha evidenziato una significativa correlazione spaziale positiva unicamente con la distribuzione del trasportatore della noradrenalina (NAT).

## Domande scientifiche e Obiettivi
- Quale singola metrica rs-fMRI (tra ALFF, ReHo, DC e VMHC) costituisce il miglior biomarcatore per classificare e predire a livello individuale il recupero della mano paretica post-ictus?
- Quali processi biologici, tipi cellulari e stadi di sviluppo (derivati dai dati trascrittomici dell'Allen Human Brain Atlas) sono spazialmente associati ai pattern di classificazione del neuroimaging?
- Esiste una correlazione macroscopica tra i biomarcatori neurofunzionali (ALFF) e la topologia di specifici recettori e trasportatori di neurotrasmettitori?

## Metodologie
- **Campione:** 65 pazienti post-ictus sottocorticale cronico, suddivisi funzionalmente in PPH (n=32, Fugl-Meyer Hand/Wrist: 11.25 ± 6.15) e CPH (n=33, FMA-HW: 1.24 ± 1.22).
- **Analisi di Neuroimaging:** Estrazione di 4 metriche da scansioni rs-fMRI: ALFF, ReHo, Degree Centrality (DC) e Voxel-Mirrored Homotopic Connectivity (VMHC).
- **Machine Learning:** Modelli a Macchine a Vettori di Supporto (SVM lineare per la classificazione PPH vs CPH e SVR per la predizione dei punteggi clinici continui FMA-HW) valutati tramite validazione leave-one-out (LOOCV).
- **Analisi Multi-Omica (Neuroimaging-Trascrittoma):** Modelli Partial Least Squares (PLS) per relazionare i pesi spaziali discriminanti dell'ALFF con i trascrittomi corticali standardizzati (15.633 geni su 233 regioni). Successiva Gene Ontology enrichment, analisi di espressione cell-type specifica (es. astrociti, neuroni eccitatori/inibitori) e mappatura su 13 mappe in vivo di neurotrasmettitori (JuSpace).

## Risultati
- **Performance delle Metriche:** L'ALFF ha superato nettamente le altre (accuratezza 0.88 vs 0.68 di ReHo, 0.61 di DC, 0.57 di VMHC). È risultato anche il miglior predittore continuo per i punteggi FMA-HW (R² = 0.36, MAE = 3.95).
- **Regioni Discriminanti (ALFF):** Per la classe CPH, le regioni a maggior impatto negativo (minor ALFF) sono state il giro precentrale ipsilesionale e il lobulo parietale inferiore ipsilesionale. Aree contralesionali compensatorie (es. lobo posteriore del cervelletto e giro temporale medio) supportavano l'identificazione della classe PPH.
- **Associazioni Trascrittomiche:** I geni correlati alle mappe di classificazione ALFF (Componente PLS 2) erano fortemente arricchiti per funzioni di percezione sensoriale chimica e per il pathway di signaling dei recettori accoppiati a proteine G (G protein-coupled receptor signaling pathway).
- **Substrati Cellulari:** I geni positivamente associati all'ALFF hanno mostrato un'espressione predominante e specifica negli astrociti.
- **Neurotrasmettitori:** Tra le 13 mappe chimiche analizzate, le mappe di classificazione ALFF hanno mostrato una correlazione spaziale positiva significativa esclusivamente con il Trasportatore della Noradrenalina (NAT).

## Breve Discussione
- L'ALFF, riflettendo le oscillazioni neurali spontanee a bassa frequenza e il metabolismo locale del glucosio, si conferma il biomarcatore fMRI a riposo più sensibile per predire il grado di recupero della mano a valle di danni strutturali sub-corticali.
- Il coinvolgimento di estese aree non motorie (es. insula, regioni parieto-occipitali) evidenzia che la scarsa performance della mano nei casi gravi (CPH) può essere parzialmente attribuita ad aberrazioni nelle interazioni con i network di Default Mode (DMN) ed Executive Control.
- L'associazione cellulare con gli astrociti suggerisce che queste cellule gliali giochino un ruolo critico (modulazione sinaptica, omeostasi) nella stabilizzazione della plasticità neurale osservata macroscopicamente tramite ALFF.
- La specifica correlazione col sistema noradrenergico rafforza precedenti evidenze cliniche/farmacologiche che identificano la noradrenalina come modulatore chiave per potenziare la connettività di rete e l'esito sensomotorio riabilitativo post-ictus.

---

# Park et al. (2016)
_EEG response varies with lesion location in patients with chronic stroke_

## Riassunto brevissimo
Questo studio ha valutato come le risposte elettroencefalografiche (EEG) durante compiti motori varino in base alla sede della lesione in 12 pazienti con ictus cronico, divisi in 3 gruppi: lesioni sopratentoriali che includono la corteccia motoria primaria M1 (SM1+), lesioni sopratentoriali che escludono M1 (SM1-), e lesioni sottotentoriali (INF). Attraverso l'analisi della desincronizzazione evento-correlata (ERD) e del coefficiente di lateralità (LC) in banda beta durante compiti motori (attivi e immaginati), è emerso che i pazienti SM1+ mostrano un LC negativo (maggiore attivazione compensatoria dell'emisfero contralesionale intatto), mentre i pazienti SM1- e INF (con M1 intatta) presentano un LC positivo simile a quello dei 12 controlli sani. La topografia EEG varia drasticamente: il gruppo INF ha mappe molto simili ai sani, SM1- mostra un'attivazione controlaterale ma più diffusa, e SM1+ ha un'attivazione fortemente sbilanciata verso l'emisfero ipsilaterale (sano), suggerendo che la neuroriabilitazione BCI debba sempre essere personalizzata in base alla posizione della lesione.

## Domande scientifiche e Obiettivi
- I pattern di attivazione cerebrale misurati tramite EEG (in particolare la desincronizzazione/sincronizzazione evento-correlata ERD/ERS e i relativi coefficienti di lateralità) variano sistematicamente a seconda della localizzazione neuroanatomica della lesione nei pazienti post-ictus?
- Come si differenzia la distribuzione topografica della potenza della banda beta durante compiti motori (attivi, passivi, e motor imagery) tra pazienti con danno primario a M1, pazienti con danni corticali/sottocorticali che risparmiano M1, e pazienti con lesioni infratentoriali rispetto ai controlli sani?

## Metodologie
- **Campione:** 12 pazienti con ictus cronico suddivisi radiologicamente in 3 gruppi (4 per gruppo): SM1+ (lesione sopratentoriale che include M1), SM1- (lesione sopratentoriale che esclude M1), INF (lesione infratentoriale/tronco encefalico), confrontati con 12 controlli sani (HCs) age-matched.
- **Protocollo Motorio:** Compiti di movimento dell'arto paretico declinati in 3 modalità: attivo (volontario), passivo (assistito da un dispositivo robotico), e motor imagery (immaginazione del movimento). Sono stati testati due movimenti base: supinazione e prensione (grasping).
- **Acquisizione ed Elaborazione EEG:** Dati registrati tramite sistema a 64 canali, focalizzandosi sulle bande del ritmo sensomotorio mu (8-13 Hz) e beta (13-32 Hz).
- **Metriche Analitiche:** Calcolo della desincronizzazione/sincronizzazione evento-correlata (ERD/ERS) e del Coefficiente di Lateralità (LC). Un LC negativo indica un'attivazione più forte nell'emisfero ipsilaterale (sano, o contralesionale), mentre un LC positivo indica attivazione fisiologica più forte nell'emisfero controlaterale (leso). Le mappe topografiche (su 28 canali) sono state confrontate statisticamente (correlazione di Pearson e ANOVA) per quantificare la somiglianza con i controlli sani.

## Risultati
- **Coefficiente di Lateralità (LC):** Nella banda beta (soprattutto nei task attivi e di motor imagery), il gruppo SM1+ ha presentato sistematicamente un valore LC negativo, indicando che la corteccia motoria dell'emisfero sano era molto più attiva di quella dell'emisfero leso. I gruppi SM1- e INF hanno invece mostrato un LC positivo, statisticamente diverso da SM1+ e sovrapponibile a quello dei controlli sani.
- **Pattern Temporali ERD:** Le correlazioni tra le curve di attivazione temporale (ERD) dei pazienti e dei soggetti sani decrescevano linearmente in base al livello del danno strutturale: INF > SM1- > SM1+.
- **Topografia EEG (Banda Beta):** Le distribuzioni spaziali differivano nettamente tra i sottogruppi. Il gruppo INF presentava topografie quasi identiche ai sani (ERD forte, definita e lateralizzata controlateralmente). Il gruppo SM1- mostrava un'ERD controlaterale ma strutturalmente più diffusa. Il gruppo SM1+ aveva invece il focus dell'ERD fortemente spostato sull'emisfero ipsilaterale (sano). Nessuna differenza significativa è emersa nella banda mu.

## Breve Discussione
- La profonda variabilità inter-gruppo delle risposte EEG dipende fondamentalmente dall'integrità strutturale della corteccia M1 e dai conseguenti squilibri nell'inibizione interemisferica (IHI). Nei pazienti SM1+, il collasso dell'IHI dall'emisfero leso a quello sano disinibisce l'emisfero contralesionale, causando una iperattivazione compensatoria asimmetrica (LC negativo).
- Pazienti con lesioni sottocorticali (SM1-) o del tronco (INF) che risparmiano M1 preservano in parte la dinamica inibitoria interemisferica, mantenendo un'attivazione primariamente controlaterale (anche se spesso con un reclutamento spaziale diffuso per far fronte ai deficit dei tratti piramidali).
- Questi risultati sottolineano l'errore metodologico di trattare i pazienti con ictus come un gruppo monolitico negli studi EEG e BCI: le topologie delle anomalie di rete (e dunque i target terapeutici/decodificativi) dipendono in maniera cruciale dalla localizzazione anatomica specifica della lesione.

---

# Jimenez-Marin et al. (2022)
_Multimodal and multidomain lesion network mapping enhances prediction of sensorimotor behavior in stroke patients_

## Riassunto brevissimo
Lo studio estende la tecnica di Lesion Network Mapping (LNM) applicandola in modo multimodale (combinando connettività funzionale - FC - e strutturale - SC) per predire i deficit sensomotori in una coorte di 54 pazienti post-ictus. Utilizzando la Canonical Correlation Analysis (CCA) e i connettomi di 1000 soggetti sani (Human Connectome Project), gli autori correlano le mappe di "disconnessione putativa" indotte dalle lesioni a molteplici punteggi comportamentali (motori e sensoriali). I risultati mostrano che l'LNM multimodale (FC + SC) supera l'analisi unimodale e il tradizionale Lesion Symptom Mapping (LSM), catturando meglio la natura multidominio del deficit. In particolare, la componente funzionale contribuisce maggiormente alla predizione rispetto a quella strutturale. Inoltre, le mappe funzionali risultano robuste indipendentemente dalla rimozione dell'effetto "dimensione della lesione", mentre la predittività delle mappe strutturali e dell'LSM crolla senza tale correzione.

## Domande scientifiche e Obiettivi
- Può un approccio multimodale (connettività funzionale + strutturale) al Lesion Network Mapping (LNM) migliorare la predizione del comportamento sensomotorio multidominio nei pazienti colpiti da ictus, rispetto alle analisi unimodali o al classico Lesion Symptom Mapping (LSM basato solo sulla topologia della lesione)?
- Qual è il contributo relativo delle modalità funzionali (FC) rispetto a quelle strutturali (SC) nello spiegare la varianza nei punteggi comportamentali post-ictus?
- In che modo il volume anatomico della lesione influisce in modo differenziale sulla capacità predittiva dei network strutturali rispetto a quelli funzionali?

## Metodologie
- **Campione:** 54 pazienti (mix di emisfero dx e sx) al primo ictus, valutati con un set di test sensomotori multidominio: ARAT e Fugl-Meyer per la componente motoria; Erasmus-modified Nottingham Sensory Assessment (Em-NSA) e Perceptual Threshold of Touch (PTT) per l'aspetto somatosensoriale.
- **LNM e HCP:** Le maschere delle lesioni dei pazienti sono state co-registrate in uno spazio standard e utilizzate come "seed" sui dati fMRI a riposo (FC) e di diffusione (SC) di 1000 soggetti sani (HCP). Questo ha generato le mappe di "disconnessione putativa" che la lesione avrebbe causato in un cervello sano normativo.
- **Analisi Statistica Multivariata:** Dopo una riduzione della dimensionalità tramite PCA, è stata applicata un'analisi di correlazione canonica predittiva (LOOCV-CCA) per associare i profili di disconnessione cerebrale combinati (X) ai 4 punteggi clinici (Y), preventivamente regrediti per età, tempo dall'ictus e dimensione della lesione.

## Risultati
- **Predizione Migliorata:** L'LNM multimodale (SC + FC) ha ottenuto la correlazione massima assoluta col comportamento (T=0.56, Varianza spiegata 87.92%) e il miglior bilanciamento nel predire simultaneamente i domini motori e sensoriali, superando l'LNM unimodale FC (T=0.54), l'LNM unimodale SC (T=0.42) e il classico LSM (T=0.38).
- **Dominanza della Connettività Funzionale:** Nel modello multimodale combinato, i pesi (contributi) assegnati ai network funzionali erano significativamente maggiori rispetto a quelli dei network strutturali.
- **Tratti Rivelati:** Solo con l'approccio multimodale sono emersi tratti "nascosti" come il tratto corticospinale (CST), l'area motoria primaria (M1) e il peduncolo cerebellare medio, mentre le reti unimodali tendevano a omettere queste aree critiche.
- **Effetto Dimensione Lesione:** Le performance del Lesion Symptom Mapping e del network strutturale (SC) decadevano drammaticamente quando veniva rimosso matematicamente l'effetto della dimensione della lesione. Al contrario, i network funzionali (FC) hanno mantenuto un'elevata capacità predittiva totalmente indipendente dal volume lesionale.

## Breve Discussione
- L'utilizzo combinato della connettività strutturale e funzionale permette un'analisi "olistica" che spiega meglio la sintomatologia clinica complessa dell'ictus. Il network totale compromesso si dimostra funzionalmente più grande (e più ricco di informazioni predittive) della semplice somma delle singole disconnessioni anatomiche.
- La robustezza della connettività funzionale (FC) rispetto alle dimensioni della lesione suggerisce che la FC elabori le funzioni sensomotorie in modo più distribuito e ridondante rispetto alle rigide vie di trasmissione strutturali (SC), fortemente vincolate all'integrità spaziale (e quindi al volume) della lesione.
- L'elevata eterogeneità clinica dei deficit ictali richiede metodologie multivariate avanzate (come la CCA combinata a LNM multimodale) per mappare molteplici output comportamentali su reti cerebrali complesse, fornendo un biomarker promettente per guidare protocolli di stimolazione (es. DBS o TMS) verso target di rete normativi.

---

# Filatova et al. (2018)
_Dynamic Information Flow Based on EEG and Diffusion MRI in Stroke: A Proof-of-Principle Study_

## Riassunto brevissimo
Questo studio proof-of-principle presenta l'applicazione di una tecnica di neuroimaging multimodale chiamata Variational Bayesian Multimodal Encephalography (VBMEG) per tracciare il flusso dinamico delle informazioni nel cervello dopo un ictus. Il metodo combina l'alta risoluzione temporale dell'EEG con i vincoli anatomici della Risonanza Magnetica strutturale (MRI) e di diffusione (dMRI). L'analisi su due pazienti con ictus cronico ed emiparesi e due controlli sani ha mostrato un'elevata precisione nella localizzazione delle sorgenti corticali (Variance Accounted For - VAF > 80%) e nella stima del flusso di informazioni (VAF > 90%). I risultati preliminari rivelano che, mentre nei soggetti sani l'informazione sensoriale è elaborata prevalentemente nell'emisfero controlaterale, nei pazienti post-ictus si assiste a una riconfigurazione dei network sensoriali con un sensibile aumento della comunicazione interemisferica, fornendo un nuovo potenziale biomarcatore dinamico per valutare il recupero neurale.

## Domande scientifiche e Obiettivi
- Può il metodo computazionale VBMEG (che integra dati funzionali EEG e dati strutturali MRI/dMRI) migliorare la localizzazione spaziale delle sorgenti EEG e tracciare accuratamente la direzionalità e le dinamiche temporali del flusso di informazioni tra le aree corticali?
- È possibile utilizzare questa tecnica multimodale avanzata per identificare e quantificare la riconfigurazione funzionale (plasticità) dei network somatosensoriali in pazienti post-ictus rispetto a soggetti sani, durante un compito passivo di stimolazione elettrica periferica?

## Metodologie
- **Campione:** 2 pazienti post-ictus cronico con emiparesi e 2 individui sani di controllo pareggiati per età.
- **Acquisizione Dati:** Registrazione EEG ad alta densità (64 canali) durante 500 trial di stimolazione elettrica dell'indice (mano paretica per i pazienti, mano dominante per i controlli). Acquisizione separata di MRI strutturale (T1) e di diffusione (dMRI) per tracciare la connettività anatomica della sostanza bianca.
- **Algoritmo VBMEG:** Utilizzato per risolvere il problema inverso dell'EEG mediante una stima Bayesiana Gerarchica (hVB) vincolata anatomicamente dalla superficie corticale.
- **Flusso Dinamico (Linear Connectome Dynamics - LCD):** I modelli autoregressivi multivariati sono stati vincolati matematicamente utilizzando solo le connessioni fisiche dei tratti di sostanza bianca (dMRI) e i relativi ritardi di conduzione assonale (stimati a 6 m/s), per calcolare la connettività effettiva (causale) tra le regioni. La precisione predittiva del modello è stata quantificata tramite la Variance Accounted For (VAF).

## Risultati
- **Precisione del Modello:** Il metodo ha localizzato con grande precisione le sorgenti attivate dallo stimolo (VAF > 80% per l'EEG inverso) e ha modellato con estremo rigore le dinamiche del flusso informativo (VAF > 90%), filtrando ed eliminando efficacemente le false connettività spurie tipiche dei metodi EEG classici non vincolati anatomicamente.
- **Pattern nei Controlli Sani:** L'attivazione corticale e il flusso di informazioni (tra i picchi P50 e N100, ovvero 50-100 ms post-stimolo) sono rimasti confinati in modo fisiologico nell'area sensomotoria dell'emisfero controlaterale.
- **Pattern nei Pazienti Ictus:** Si è osservata una marcata attivazione anomala in entrambi gli emisferi e un incremento statisticamente e topograficamente rilevante delle interazioni interemisferiche. In particolare, il flusso di informazione è stato trasmesso dall'emisfero controlaterale (ipsilesionale) a quello ipsilaterale (contralesionale) nella medesima finestra temporale.

## Breve Discussione
- L'utilizzo combinato dell'EEG e della dMRI nel metodo VBMEG supera i limiti spaziali dell'EEG standard e i limiti temporali dell'fMRI, consentendo di mappare flussi di informazione somatosensoriale velocissimi (nell'ordine dei millisecondi) esclusivamente lungo i tratti neurali fisicamente intatti.
- L'aumento del crosstalk interemisferico osservato nei pazienti cronici, persino in quelli con un buon recupero motorio clinico, dimostra che la riorganizzazione plastica del network somatosensoriale (plasticità maladattiva o compensatoria) è complessa e persiste a lungo termine.
- Sebbene si tratti di uno studio proof-of-principle su piccolo campione, la robustezza analitica dei risultati candida il metodo VBMEG come potente strumento neuroradiologico per estrarre biomarcatori precoci e quantitativi delle dinamiche di rete (effective connectivity), fondamentali per monitorare oggettivamente il recupero neurobiologico o guidare futuri protocolli mirati di neuroriabilitazione.

---
