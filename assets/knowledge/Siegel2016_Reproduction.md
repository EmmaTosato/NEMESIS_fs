# Siegel et al. 2016 — analisi metodologica passo per passo, in vista di una riproduzione

> Fonte: `assets/papers/Siegel et al - 2016 - Disruptions of network connectivity predict impairment in multiple behavioral domains after stroke/markdown/_full.md`. Obiettivo del documento: scomporre il paper sezione per sezione, isolando ogni step metodologico (cosa fanno, con quale test statistico, per rispondere a quale domanda), per valutare cosa è direttamente riproducibile con i dati NEMESIS (`data/derived/features/fc_matrix/`, in prospettiva `data/derived/features/lesion_matrix/`) e cosa manca.

Il paper in sintesi: coorte di 132 pazienti stroke subacuti (100 dopo esclusioni) + 27 controlli, confronto tra danno strutturale (lesione) e disfunzione fisiologica distribuita (FC a riposo) nello spiegare il deficit comportamentale in 6 domini (attenzione, memoria visiva, memoria verbale, linguaggio, motorio, visivo). Risultato chiave: memoria (visiva/verbale) meglio spiegata da FC, motorio/visivo meglio spiegati da lesione, linguaggio da entrambi.

---

## Sezione: Results — "Abnormal FC Patterns in Stroke"

Domanda a cui risponde questa sezione: **lo stroke produce un pattern fisiologico di disfunzione della connettività riconoscibile e consistente a livello di popolazione?** (prima di chiedersi se questo pattern predice il comportamento, sezione successiva).

### Step 1 — Coorte ed esclusioni
132 pazienti stroke acuti (1-2 settimane post-evento) + 31 controlli sani età-matched.
- **21 pazienti esclusi** per hemodynamic lag (ritardo nel segnale BOLD dovuto a stenosi/occlusione vascolare, artefatto vascolare non neuronale)
- **11 pazienti + 4 controlli esclusi** per eccessivo movimento in scanner

→ campione per le analisi FC di questa sezione: **100 pazienti, 27 controlli** (sottoinsieme diverso, più piccolo, di quello usato più avanti per le ridge regression lesion-deficit/FC-deficit, dove n varia per dominio tra 53 e 98).

### Step 2 — Parcellazione e classificazione delle connessioni
Parcellazione corticale a 324 ROI (Gordon et al.), raggruppate in 13 reti (RSN: DAN, DMN, CON, VAN, somatomotoria dorsale/ventrale, ecc.). Ogni connessione **dentro la stessa rete** è classificata in 3 categorie:
1. **Omotopica interemisferica** — stessa regione, emisferi opposti
2. **Intraemisferica ipsilesionale** — stesso emisfero del danno
3. **Intraemisferica controlesionale** — emisfero opposto al danno

Prerequisito per tutte le analisi successive: senza sapere "che tipo" di connessione è, non si possono testare ipotesi specifiche su interemisferico vs intraemisferico.

### Step 3 — Test principale: pazienti vs controlli su FC omotopica
T-test a due code, **FDR-corretto**, su FC omotopica: pazienti vs controlli (t=4.26, P=10⁻⁴) — l'effetto più forte del paper. Ripetuto **per singola rete**: significativo in tutte tranne CON, VAN, DMN.

**ANOVA a 3 fattori** (gruppo × rete × head motion) come controllo di confondimento: motion non significativo (P=0.26), nessuna interazione — l'effetto non è guidato dal movimento.

Contrasto: la connettività **intraemisferica** entro-rete (ipsi- e contralesionale) **non cambia** — l'effetto è specificamente interemisferico, non un decadimento generico di tutta la FC.

### Step 4 — Controllo metodologico: GSR vs CompCor
Preprocessing FC rifatto **senza** global signal regression (GSR), usando CompCor come alternativa per rimuovere rumore non-neuronale. Motivo: la GSR è nota per poter introdurre correlazioni negative artificiali. Risultato: pattern replicato → non è un artefatto della pipeline di preprocessing.

### Step 5 — Confronto tra reti (non più dentro-rete)
99 t-test (45 ipsilesionali + 45 contralesionali + 9 omotopiche) tra coppie di reti diverse, soglia calibrata con **permutation test** (10.000 permutazioni dell'assegnazione gruppo — scelta robusta con tanti test correlati). Risultato: **solo una coppia sopravvive**, DAN-DMN ipsilesionale (t=-3.15, P=0.0021): negativa nei controlli (normale segregazione task-positive/task-negative), meno negativa nei pazienti.

### Step 6 — Collegare i due fenomeni (correlazione cross-subject)
Domanda: i due effetti (calo omotopico DAN, aumento DAN-DMN ipsilesionale) sono collegati **nello stesso soggetto**, o sono due effetti di gruppo indipendenti? Correlazione soggetto-per-soggetto: r=-0.61 nei pazienti, r=0.25 (non sig.) nei controlli, differenza testata con **Fisher r-to-z** (z=-4.24). Ripetuto per altre reti (SMD, SMV, CON, VAN), FDR corretto su 8 confronti — stesso pattern, più debole.

### Step 7 — Lesione generica o lesione specifica? (il test più rilevante per noi)
**Univariata** (FC omotopica media ~ dimensione della lesione, un singolo numero) vs **multivariata** (FC omotopica media ~ topografia completa della lesione, voxel-wise). Risultato: r=0.46 in entrambi i casi — **aggiungere la topografia non migliora la predizione oltre alla sola dimensione**.

Interpretazione: il calo di FC omotopica è una conseguenza generica di "quanto tessuto è danneggiato", non di "dove" — mentre la topografia specifica di *quali* connessioni calano probabilmente sì dipende da dove è la lesione (non testato qui, resta un'inferenza).

Nota di metodo: questo è lo stesso schema logico di parsimonia ("un predittore semplice spiega quanto uno complesso?") che il paper userà su scala più larga per il confronto lesion-deficit vs FC-deficit (sezione successiva). Applicabile anche a noi: il numero di nodi FC compromessi da lesione (già calcolato in `mask_summary.csv`, vedi `assets/knowledge/fc_lesion_masking.md`) spiega la performance quanto l'intera topografia della lesione?

### Step 8 — Escludere confondimenti residui
Motion, percentuale di tempo a occhi aperti, lateralità del lag — nessuno spiega le differenze di FC omotopica, né tra gruppi né tra individui.

### Schema generale del ragionamento
Stabilisci l'effetto (step 3) → escludi che sia un artefatto di metodo (step 4) → localizzalo con precisione, dentro-rete e tra-reti (step 3, 5) → mostra che è collegato in uno stesso soggetto a un secondo fenomeno (step 6) → testa se è un effetto generico o location-specifico (step 7) → escludi covariate residue (step 8).

---

## Sezione: Results — "Prediction of Behavioral Deficits Based on Lesion and FC"

Domanda a cui risponde: la fisiologia (FC) e la struttura (lesione) predicono davvero il deficit comportamentale a livello di singolo soggetto — e in che misura, per ciascun dominio? Qui si passa dal "il pattern fisiologico esiste" (sezione precedente) al "il pattern fisiologico ha valore predittivo clinico".

### Step 1 — Setup del modello (accennato qui, dettaglio completo in Experimental Procedures)
Due input per soggetto: mappa di lesione (struttura) e matrice FC vettorizzata (funzione). Per ciascun dominio comportamentale vengono addestrati **due modelli separati** — lesion-deficit e FC-deficit — con **ridge regression leave-one-out** (Fig. 2).

### Step 2 — 6 domini concettuali → 8 modelli
Motorio e visivo vengono splittati per lato (sinistro/destro): da 6 domini nominali si arriva a **8 modelli** (attenzione, memoria visiva, memoria verbale, linguaggio, motorio-sx, motorio-dx, visivo-sx, visivo-dx), ciascuno con il proprio n (53-98 soggetti, in base a quali batterie il paziente ha completato).

### Step 3 — Verifica che ogni singolo modello sia meglio del caso
Sia la versione lesion-deficit che quella FC-deficit sono testate con **permutation test** (permutando lo score comportamentale, non l'imaging) per ciascuno degli 8 modelli. Tutti superano la soglia (anche il più debole, right visual FC, P=0.09, borderline). Controllo di base prima di poter confrontare due modelli tra loro.

### Step 4 — Controllo di confondimento: la FC non è solo un proxy della lesione
Analisi di controllo aggiuntiva (Supporting Information): l'accuratezza del modello FC-deficit resta sopra il caso anche quando l'informazione sulla posizione della lesione è inclusa in modelli nulli. Necessario perché la lesione danneggia sia il tessuto sia, indirettamente, la FC delle zone vicine/collegate — senza questo controllo non si potrebbe escludere che il modello FC stia solo "vedendo" la lesione indirettamente.

### Step 5 — Il confronto testa (Fig. 3): lesion-deficit vs FC-deficit
**Wilcoxon signed-rank** a due code, appaiato, sull'**errore di predizione** (non sull'accuratezza aggregata), **FDR corretto** sulle 8 comparazioni. Appaiato perché dentro ogni dominio i due modelli usano esattamente gli stessi soggetti.

| Dominio | Lesione | FC | Vince | P (FDR) |
|---|---|---|---|---|
| Memoria visiva | 10.9% | 36.4% | **FC** | 0.015 |
| Memoria verbale | 18.7% | 41.6% | **FC** | 0.007 |
| Motorio | 44.8% | 23.4% | **Lesione** | 0.009 |
| Visivo | 49.9% | 13.3% | **Lesione** | 0.013 |
| Attenzione | 32.3% | 45.0% | trend FC (non sig.) | 0.074 |
| Linguaggio | 64.6% | 51.1% | pari | 0.21 |

### Step 6 — Generalizzazione oltre il punteggio composito
I domini sono punteggi compositi (prima componente PCA su più test). Per escludere che il risultato sia un artefatto di come è costruito lo score composito, ripetono il confronto sui singoli task grezzi (Fig. S6): le differenze di dominio si generalizzano ai task individuali predetti con buona accuratezza.

**Perché è il cuore del paper per noi**: è esattamente lo schema a cui puntiamo — un modello per lesione, uno per FC, stesso soggetto, stesso dominio comportamentale, confronto appaiato dell'errore. Resta il vincolo dei dati comportamentali per WashU da chiarire (vedi nota finale del documento).

---

## Sezione: Results — "Topography of Behaviorally Predictive FC"

Domanda a cui risponde: una volta stabilito che la FC predice il comportamento, quali connessioni contano, e c'è un pattern comune tra i domini? Si passa dal "quanto bene predice" (r²) al "cosa" predice — l'interpretabilità del modello.

### Step 1 — Consolidare i pesi del modello
Il modello ridge LOOCV produce un vettore di pesi ω per ogni fold lasciato fuori. Per ottenere un'unica mappa interpretabile, i pesi vengono **mediati su tutti i fold LOOCV** → un vettore di pesi "consenso" per modello/dominio.

### Step 2 — Proiezione anatomica e convenzione di colore (Fig. 4)
Pesi consenso proiettati sul cervello come edge colorati: **verde** = peso positivo (più FC → **miglior** comportamento), **arancione** = peso negativo (più FC → **peggior** comportamento). Chiarimento esplicito nel paper: il segno del peso non dice se la FC stessa è positiva o negativa, solo la direzione della relazione col comportamento. Mostrate solo le 200 connessioni più forti; dimensione del nodo ∝ somma dei pesi di tutte le sue connessioni.

### Step 3 — Classificazione a 4 vie e test di dominanza
Top 1% dei pesi di ogni modello FC-deficit diviso in 4 gruppi: interemisferico-positivo, interemisferico-negativo, intraemisferico-positivo, intraemisferico-negativo. **ANOVA** attraverso gli 8 modelli (P=1.6×10⁻⁶): domina l'**interemisferico-positivo**, seguito da **intraemisferico-negativo**. **Eccezione: linguaggio** — domina l'intraemisferico-positivo, ma solo nell'**emisfero sinistro** (coerente con la lateralizzazione nota del linguaggio).

### Step 4 — Aggregazione a livello di rete (RSN, Fig. 5)
Pesi positivi aggregati per rete: raggio del cerchio = peso totale dentro una RSN, spessore linea = peso totale tra coppie di RSN. **Attenzione e memoria** → molto peso tra reti diverse (processo distribuito). **Linguaggio** → quasi solo dentro auditory. **Motorio** → dentro auditory + somatomotoria. **Visivo** → dentro visiva + somatomotoria.

### Step 5 — Quantificare l'osservazione qualitativa
Rapporto peso-dentro-RSN / peso-tra-RSN per dominio: attenzione 1.431, memoria visiva 1.526, memoria verbale 1.499, **linguaggio 1.768**, motorio 1.605, **visivo 1.624**. Rapporto basso = più peso distribuito tra reti (attenzione più "integrativa"); rapporto alto = più peso concentrato dentro una singola rete (linguaggio/visivo più "localizzati").

### Step 6 — Il filo che porta alla sezione successiva
Guardando tutte le mappe insieme, pattern comune: i pesi più forti tendono a essere **positivi-interemisferici** e **negativi-intraemisferici** — stesso segno di effetto già osservato a livello di gruppo in "Abnormal FC Patterns". Qui però è il pattern che predice il comportamento a livello di singolo soggetto, non solo la differenza media pazienti-controlli. Cerniera concettuale verso la sezione successiva (multi-task learning).

---

## Sezione: Results — "Prediction of Common Behavioral Impairment" (multi-task learning)

Domanda a cui risponde: la sezione precedente nota **a occhio** (Fig. 4) che i pesi più forti tendono a essere sempre dello stesso tipo across quasi tutti i domini. Qui formalizzano statisticamente quell'osservazione: si può separare, dentro il modello stesso, una componente "generica" (comune a tutti i domini) da una "specifica" (propria di ciascun dominio)?

### Step 1 — Perché serve un modello diverso
Gli 8 modelli ridge della sezione precedente sono **indipendenti** — non c'è modo, dentro quella struttura, di chiedere "quanto di questo peso è condiviso vs. specifico", solo confrontare le mappe a posteriori. Il multi-task learning (MTL) risolve il problema a monte, nella struttura del modello.

### Step 2 — Struttura del modello: due set di pesi, una previsione
Invece di un ω per dominio, il modello stima due componenti per dominio k: un peso condiviso **ω₀** (identico per tutti i domini) e un peso specifico **ωₖ**. Previsione per il soggetto i nel dominio k:

y_i = (ω₀ + ωₖ)ᵀ x_i

deficit previsto = contributo generico + contributo specifico di quel dominio, sulla stessa FC (in spazio PCA).

### Step 3 — Regolarizzazione: non favorire arbitrariamente l'uno o l'altro
Nell'equazione (Eq. 1) compaiono termini λ‖ω₀‖² e λ‖ωₖ‖², stesso λ per entrambi — il testo dice "L1 regularization... such that the model is not biased toward using either shared or domain-specific weights". **Nota di lettura**: la formula come scritta sembra norma-2 al quadrato (ridge/L2), mentre il testo dice "L1" — incongruenza nel paper stesso tra prosa e formula (probabile refuso). L'idea chiave, indipendente da L1/L2, resta valida: stesso coefficiente λ per entrambe le componenti, quindi è il modello sui dati a decidere quanto affidarsi al condiviso vs. allo specifico.

### Step 4 — Ottimizzazione di λ
Stessa strategia leave-one-out delle sezioni precedenti: λ scelto empiricamente su un range di valori, minimizzando l'errore di predizione lasciato fuori.

### Step 5 — Risultato aggregato
Il modello MTL ottimizzato spiega **28.7%** di varianza su tutti i pazienti e tutti i domini insieme — un unico numero, non un r² per dominio. **Nota di lettura, seconda incongruenza**: lo stesso paragrafo dice prima "these eight domains" e poi "across all patients and all five domains" — non è chiarito se per l'MTL abbiano ricombinato motorio/visivo per lato o se sia un refuso. Ambiguità del testo originale, non risolta.

### Step 6 — Interpretare la componente condivisa (ω₀)
Una volta stimato ω₀ (unico), proiettato sul cervello come nella sezione precedente (Fig. 6B, D, E). Le connessioni condivise sono **quasi tutte interemisferiche**.

### Step 7 — Un dettaglio metodologico diverso rispetto a Fig. 4
Per riassumere "quanto conta ogni nodo" nella componente condivisa, qui usano il **root-mean-square** dei pesi di tutte le connessioni di quel nodo — non la somma dei valori assoluti come in Fig. 4. Scelta statistica diversa e non equivalente (l'RMS enfatizza relativamente di più pochi pesi molto forti). Non chiarito nel paper perché le due figure usino metriche diverse.

### Step 8 — Quali reti dominano, e perché è la chiusura del cerchio
Reti con peso condiviso più alto: **dorsal attention network (DAN), cingulo-opercular (CON), auditory, somatomotoria dorsale**. DAN è esattamente la rete protagonista della primissima sezione (calo omotopico più forte, relazione più forte con l'aumento FC DAN-DMN ipsilesionale). Catena logica completa del paper:

calo FC omotopica DAN (fisiologia di gruppo) → correlato nello stesso soggetto con aumento FC DAN-DMN ipsilesionale (sez. 1) → stesso tipo di connessioni (interemisferiche positive) pesano di più nei modelli per singolo dominio (sez. 2) → e pesano di più nel predire il deficit condiviso a più domini insieme (questa sezione) — DAN, CON, auditory, somatomotoria dorsale in testa.

---

## Experimental Procedures — dettaglio tecnico esatto di ogni metodo

Questa sezione non argomenta più (nessuna domanda-risposta come nei Results) — è il riferimento tecnico preciso, parametro per parametro, di come ogni analisi sopra è stata effettivamente calcolata. Riportata qui in dettaglio perché è la parte più direttamente riusabile per una riproduzione.

### Subject Enrollment
- Reclutamento: prima ictus sintomatico, ischemico o emorragico intraparenchimale, età ≥18, evidenza clinica di deficit (motorio/linguaggio/attenzione/visivo/memoria), arruolamento <2 settimane poststroke.
- Esclusioni: incapacità di restare svegli durante il test, altre condizioni neuro/psichiatriche/mediche che precludono la partecipazione o alterano l'interpretazione, malattia della sostanza bianca periventricolare ≥ grado 5, controindicazioni MRI.
- **6.260 cartelle cliniche screenate → 132 pazienti** hanno soddisfatto tutti i criteri (età media 52.8, range 22-77; 119 destrimani, 63 donne, 64 con lesione nell'emisfero destro).
- Controlli: n=31, matched per età/sesso/lateralità/istruzione, stesso protocollo comportamentale+imaging (età media 55.7, SD 11.5, range 21-83).

### Neuropsychological Assessment — come nascono i punteggi di dominio
Punteggio registrato solo per i task completati → **n diverso per dominio** (causa diretta degli n che variano 53-98 nelle tabelle precedenti). Riduzione dimensionale via **PCA per categoria** (dettaglio completo in un lavoro precedente, ref. 19):
- **Attenzione**: 1ª componente = 26.1% varianza, legata a bias di campo visivo (Posner L/R accuracy diff, r=0.83; Mesulam center of cancellation, r=0.75) e performance generale (r=-0.41).
- **Memoria**: prime 2 componenti = 66.2% varianza. 1ª componente → richiamo differito visivo (BVMT, r=0.81) = **memoria visiva**. 2ª componente → richiamo differito verbale (HVLT, r=0.93) = **memoria verbale**.
- **Linguaggio**: 1ª componente = 77.3% varianza, legata a comprensione e produzione.
- **Motorio**: prime 2 componenti → deficit corpo sinistro/destro, 43.0%/34.6% varianza rispettivamente.
- **Visivo**: nessuna PCA (un solo test funzionale, perimetria computerizzata Humphrey Field Analysis) — score = deviazione media di pattern nei campi emisferici sinistro/destro, presi direttamente.

Punteggi continui, **z-normalizzati (media 0, SD 1) nei pazienti**, punteggio più basso = deficit maggiore. Soglia di "deficit" = ≥2 SD sotto i controlli: attenzione 31/88, memoria visiva 27/88, memoria verbale 30/88, linguaggio 33/112, motorio-sx 37/106, motorio-dx 39/106, visivo-sx 13/58, visivo-dx 10/58.

### MRI and Lesion Analysis
T1 registrato a MNI via FSL FNIRT. Segmentazione manuale della lesione su T1 MPRAGE + T2 spin echo + FLAIR (acquisiti 1-3 settimane poststroke), software Analyze. **Doppia revisione**: due neurologi certificati revisionano tutte le segmentazioni indipendentemente, poi un neurologo (M.C.) fa una seconda review focalizzata su bordi/malattia della sostanza bianca. Attenzione esplicita a distinguere lesione da CSF, ed edema vasogenico da emorragia. **Negli stroke emorragici, l'edema è incluso nella lesione.** Staff di segmentazione **blind ai dati comportamentali**. Lesioni: 0.02-82.97 cm³, media 10.15 cm³ (SD 13.94).

### R-fMRI Acquisition
Siemens 3T Tim-Trio, bobina 12 canali. Pazienti scansionati a 3 timepoint (~2 settimane, ~3 mesi, ~1 anno poststroke) — **nel paper viene usato solo il primo timepoint** per le analisi qui descritte. BOLD a riposo: EPI gradient echo, TR=2000ms, TE=27ms, 32 slice da 4mm, risoluzione in-piano 4×4mm, **6-8 run da 128 volumi ciascuno (30 min totali)**.

### fMRI Data Preprocessing
Sequenza: correzione slice-timing (sinc interpolation) → correzione intensità slice pari/dispari (acquisizione interleaved) → normalizzazione intensità whole-brain (moda=1000) → correzione distorsione (field map sintetica) + realignment within/across run → resampling a voxel cubici 3mm in un solo step (motion correction + atlas transform combinati).

### Functional Connectivity Processing
Passi di pulizia del segnale, in ordine: **(i)** regressori da segmentazione FreeSurfer; **(ii)** rimozione per regressione di: 6 parametri di motion (rigid body), segnale medio whole-brain (**global signal regression**), segnale ventricoli/CSF, segnale materia bianca; **(iii)** filtro temporale 0.009-0.08 Hz; **(iv)** frame censoring — prime 4 volumi di ogni run esclusi, censura frame-per-frame via framewise displacement con **soglia 0.5mm**, applicata uniformemente a pazienti e controlli. **Soggetti con meno di 120 frame utilizzabili esclusi** (13 pazienti, 3 controlli) — un criterio di qualità distinto e più a monte rispetto all'esclusione per hemodynamic lag.

### Surface Processing
FreeSurfer per-soggetto (estrazione cervello, segmentazione, superfici WM/pial, gonfiaggio a sfera, registrazione spherica a fsaverage), **controllo qualità manuale**. **Per 7 pazienti** in cui lo stroke disturbava la segmentazione automatica: i voxel lesionati sono stati temporaneamente riempiti con valori atlas normali prima della segmentazione, poi **mascherati subito dopo** — un dettaglio operativo esplicito per gestire il caso "il danno rompe l'algoritmo di segmentazione stesso", non solo l'interpretazione dei risultati. Emisferi ricampionati a 164.000 vertici, poi a 10.242 vertici ciascuno per la proiezione funzionale.

Volumi BOLD campionati sulla superficie individuale (ribbon-constrained, tra materia bianca e pial). Voxel con coefficiente di variazione alto (>0.5 SD sopra la media locale, vicinato gaussiano 5mm) **esclusi dal mapping volume→superficie** — un ulteriore controllo qualità specifico per il campionamento superficiale, indipendente dal frame censoring temporale. Time course smussati (kernel gaussiano 6mm FWHM) poi mediati dentro ogni parcel → **serie temporale per-parcel**.

### Calcolo della FC e gestione della lesione (il passo più rilevante per `mask_fc.py`)
FC tra parcel = **correlazione di Pearson Fisher-z-trasformata**. **Regola esplicita di gestione lesione**: la connettività di qualunque parcel che cade dentro la lesione viene **rimossa dalle analisi univariate** e **posta a zero nei modelli multivariati** — è la fonte diretta della decisione "zero vs NaN" già discussa in `fc_lesion_masking.md` (dove NEMESIS ha scelto diversamente: NaN esplicito + imputazione separata, invece di zero diretto alla sorgente).

FC omotopica = FC di ogni regione con i vertici corrispondenti nell'emisfero opposto. **Esclusione per hemodynamic lag**: soggetti con lag interemisferico >0.5s esclusi da **tutte** le analisi FC successive — 21 soggetti esclusi, risultato finale n=100 pazienti / n=27 controlli. Nota: questo criterio è concettualmente diverso e più a valle del frame-censoring per motion sopra.

### Parcellation (ROI) and Community Assignments
Parcellazione corticale di superficie Gordon et al., basata su R-fMRI boundary mapping, **324 ROI (159 emisfero sinistro, 165 destro)** — parcellazione originale 333 regioni, escluse quelle <20 vertici (~50mm²). Generata su giovani adulti 18-33 anni, **applicata qui ad adulti 21-83** (assunzione esplicita: nessuna evidenza che i confini tra aree corticali si spostino nell'invecchiamento sano — un'assunzione, non una verifica diretta sui loro dati).

Validazione: modularity optimization su controlli e pazienti — la struttura di community osservata è "in gran parte, ma non completamente" consistente con le assegnazioni predefinite (le regioni che cambiano assegnazione sono tipicamente al confine tra reti). **Le community assignment non influenzano i modelli FC-deficit** — usate solo per l'interpretazione/visualizzazione a livello di rete (Fig. 5), non come feature del modello.

### Univariate Network FC Analysis (dettaglio statistico dei test già visti in "Abnormal FC Patterns")
Tre tipi di connettività entro-rete confrontati a livello whole-brain (omotopica, ipsilesionale, contralesionale) — **t-test a due code, FDR corretto sulle 3 statistiche**. Per le 9 RSN individuali: **99 t-test** (45 ipsilesionali + 45 contralesionali + 9 omotopiche), soglie di significatività via **10.000 permutazioni** dell'assegnazione di gruppo. Relazione FC omotopica ↔ FC ipsilesionale DMN valutata per 8 RSN (le 9 meno la DMN stessa), FDR corretto su 8 test.

### Multivariate Ridge Regression — l'architettura esatta del modello
1. **Perché ridge lineare**: scelto esplicitamente per minimizzare bias pur mantenendo la possibilità di proiettare i pesi predittivi indietro sull'anatomia cerebrale (interpretabilità) — un vincolo di design, non solo una scelta di performance.
2. **PCA transduttiva pre-modello**, eseguita **indipendentemente per ogni modello** (ogni dominio ha la propria PCA), **95% di varianza spiegata trattenuta**:
   - Lesione: PCA su mappe di lesione voxel-wise, **65.549 voxel 3mm³**.
   - FC: PCA su matrice vettorizzata, **324-scegli-2 = 52.326 edge**.
   - Componenti trattenute per modello (lesione, FC): attenzione (50, 74), memoria visiva (43, 72), memoria verbale (43, 72), linguaggio (56, 90), motorio-sx (50, 84), motorio-dx (50, 84), visivo-sx (28, 49), visivo-dx (28, 49).
3. **Loop LOOCV**: per ogni fold, λ ottimizzato tra 1 e 10⁵ minimizzando l'errore di predizione leave-one-out **sul solo training set** (non sul test set — evita data leakage); poi i pesi ottimali risolti su tutto il training set via gradient descent; i pesi applicati al soggetto lasciato fuori per generare la sua predizione. Ripetuto per ogni soggetto.
4. **Accuratezza** = quadrato della correlazione di Pearson tra punteggio misurato e predetto (r²).
5. **Mappa dei pesi consenso**: la matrice dei pesi viene mediata su **tutti gli n loop LOOCV** → un singolo vettore ω per modello, usato per tutte le visualizzazioni (Fig. 4, 5, 6).
6. Motorio e visivo: **modelli separati per lato**, poi **combinati** per riportare un'unica % di varianza spiegata per "motorio"/"visivo" complessivi (i modelli separati per lato restano in Fig. S8); i modelli combinati sono quelli usati a valle per l'analisi di contributo per-RSN.
7. Confronto lesion-deficit vs FC-deficit: **Wilcoxon signed-rank a due code sull'errore di predizione al quadrato**, indicizzato per soggetto (non sull'accuratezza aggregata — è un test appaiato soggetto-per-soggetto).
8. Contributo per-RSN: pesi entro e tra ciascuna rete mediati → **matrice di pesi RSN×RSN (7×7)** per ogni modello FC-deficit.
9. Top 1% dei pesi classificato in 4 tipi (interemisferico ±, intraemisferico ±), poi **ANOVA "su tutti e sette i modelli"** per testare la differenza di contributo tra i 4 tipi.
   > **Nota di lettura, terza incongruenza**: il testo dice qui "seven models", ma altrove nel paper si parla di 8 modelli/domini (attenzione, memoria visiva, memoria verbale, linguaggio, motorio-sx, motorio-dx, visivo-sx, visivo-dx). Anche usando i modelli combinati per lato (motorio, visivo) si arriverebbe a 6, non 7. Non risolvibile dal solo testo — probabile refuso o conteggio non esplicitato altrove nel paper (es. un dominio esclude da questa specifica analisi). Da tenere a mente insieme alle altre due incongruenze già segnalate (L1 vs formula L2 nell'MTL, "eight" vs "five" domini nell'MTL) — pattern di imprecisione numerica nel testo, non nostro errore di lettura.
10. **Modello post-hoc aggiuntivo**: predire la FC omotopica globale (media su tutti i parcel) dalla sola posizione della lesione — stessa architettura ridge/PCA/LOOCV dei modelli lesion-deficit, è il modello dietro al test "lesione generica vs specifica" già visto nello step 7 di "Abnormal FC Patterns".

### Multitask Learning
Dettaglio completo già coperto nella sezione Results corrispondente sopra — qui il paper aggiunge solo un dettaglio implementativo: **il contributo nodale ai pesi condivisi (ω₀) per le 324 ROI è calcolato come root-mean-square dei pesi di tutte le connessioni di quel nodo** (già annotato sopra, step 7 della sezione Results).

---

## Discussion e Conclusions — sintesi interpretativa

A differenza delle sezioni Results, qui non ci sono nuovi step metodologici — è l'interpretazione dei risultati e, soprattutto, i **limiti espliciti dichiarati dagli autori stessi**, la parte più utile da tenere a mente per una riproduzione onesta.

**Il filo conduttore interemisferico, ribadito**: gli autori chiudono il cerchio esplicitamente — il calo di FC omotopica interemisferica è (i) il cambiamento fisiologico più consistente tra pazienti e controlli, (ii) il singolo feature che meglio predice il deficit comportamentale in quasi tutti i domini, e (iii) quello condiviso tra domini nel modello multi-task. La loro interpretazione causale (non dimostrata direttamente, solo discussa): potrebbe riflettere danno alle vie di trasferimento interemisferico (es. corpo calloso — supportato indirettamente da uno studio di manganese-transfer citato) oppure alterazioni emisfero-specifiche del segnale che ne riducono la correlazione, senza un danno strutturale diretto alla via di comunicazione. Nessuna delle due è verificata nei loro dati — resta un'ipotesi aperta. Notano anche un parallelo con un fenomeno simile osservato nella scimmia dopo sezione chirurgica di corpo calloso e commessura anteriore.

**Struttura vs funzione, incorniciato storicamente**: richiamano l'osservazione di Wernicke (1885) — funzioni sensomotorie localizzabili, funzioni cognitive superiori dipendenti da comunicazione distribuita — come la prima formulazione (pre-quantitativa) della stessa distinzione che loro dimostrano con dati e machine learning. Poi la declinano per dominio:
- **Sensomotorio** (motorio, visivo): lesione spiega ~45-50% della varianza, coerente con reti motorie/visive **periferiche** nel grafo cerebrale complessivo — il danno a nodi periferici non si propaga (letteratura di network science citata). I pesi FC, quando contano, restano **dentro** la rete danneggiata, non tra reti.
- **Memoria (visiva e verbale)**: nessun lesion-symptom mapping ha mai isolato un sito lesionale critico per la memoria — coerente con l'idea che siano funzioni distribuite (letteratura di single-unit recording e neuroimaging citata). I pesi FC nei loro modelli sono infatti distribuiti su molti sistemi cerebrali, non concentrati.
- **Linguaggio**: caso intermedio — sia lesione che FC >40% varianza, nessuna differenza significativa tra i due. Dipendenza sostanziale da connettività intraemisferica **sinistra** (diverso da tutti gli altri domini, dove domina l'interemisferico). Interpretato come: il linguaggio dipende sia da regioni molto localizzate, sia da reti bilaterali di supporto (uditivo, attenzione visiva per la lettura, pianificazione motoria per l'eloquio) — danno a una qualsiasi di queste può compromettere il sistema nel suo complesso.

**Limiti dichiarati esplicitamente (i più rilevanti per una riproduzione)**:
1. **Scelta della parcellazione**: la parcellazione Gordon usata **non include cervelletto e gangli della base** — gli autori stessi notano che includerli potrebbe migliorare i modelli FC-deficit in studi futuri. Rilevante per noi: il nostro atlante combinato a 372 regioni (Glasser+Harvard-Oxford subcorticale) **include già** talamo/caudato/putamen/pallido/ippocampo/amigdala — un potenziale miglioramento strutturale rispetto al paper originale, non solo una replica.
2. **Parcel homogeneity diversa tra gruppi**: misurata esplicitamente (Fig. S2) — i pazienti hanno omogeneità di parcel significativamente più bassa dei controlli (t=8.0, P<0.0001), il che significa che la stessa parcellazione "si adatta" leggermente peggio al cervello di un paziente che a quello di un controllo sano (aree funzionali reali meno allineate ai confini fissi della parcellazione). Gli autori concludono che l'effetto è piccolo e improbabile spieghi la larga differenza di FC osservata — ma lo dichiarano come limite aperto, non lo negano.
3. **Campione non uniformemente distribuito**: la coorte è stata scelta per rappresentare la popolazione clinica reale, quindi le lesioni **non sono distribuite uniformemente sulla corteccia** — l'accuratezza lesion-deficit potrebbe migliorare con un campionamento più uniforme. Diretttamente rilevante per NEMESIS: anche la nostra coorte (WashU + altre) riflette una distribuzione clinica reale, non un disegno bilanciato per topografia.
4. **Dimensione campionaria limitata per dominio**: esplicitamente citato il dominio visivo (solo 58 soggetti) come il più a rischio di sottostima. Però notano che confronti lesion-vs-FC restano robusti **perché usano identici soggetti nei due modelli per lo stesso dominio** — un argomento di validità interna che vale anche per un'eventuale riproduzione nostra.
5. **Possibile confondimento stabilità-fedeltà**: la FC omotopica è nota in letteratura per essere più stabile nel tempo/condizioni di altri tipi di connessione — potrebbe essere che i modelli pesino di più sull'interemisferico semplicemente perché è **misurato con più fedeltà**, non perché sia biologicamente più importante. Gli autori argomentano (non dimostrano definitivamente) che questo non è l'unica spiegazione, portando a supporto sia la differenza gruppo-vs-gruppo sia la capacità di predire deficit sottili nell'emisfero controlesionale.

**Conclusions (sintesi in una frase)**: l'integrazione interemisferica e la segregazione intraemisferica — e la loro rottura poststroke — sono il fenomeno fisiologico centrale del lavoro; i deficit per dominio riflettono FC anomala nelle reti corrispondenti, i deficit condivisi tra domini riflettono FC omotopica in un piccolo insieme di regioni chiave, e la connettività conta di più per funzioni associative (memoria) mentre la lesione conta di più per funzioni sensomotorie.

---

## Sezioni ancora da analizzare

- [x] Results — "Prediction of Behavioral Deficits Based on Lesion and FC"
- [x] Results — "Topography of Behaviorally Predictive FC"
- [x] Results — "Prediction of Common Behavioral Impairment" (multi-task learning)
- [x] Experimental Procedures (dettaglio tecnico di ogni metodo: PCA transduttiva, ridge regression, LOOCV, MTL)
- [x] Discussion / Conclusions

Lettura del paper completa. Prossimo passo: valutare la riproducibilità con i dati NEMESIS reali (vedi discussione in sessione, non ancora trascritta qui in dettaglio).

## Vincolo aperto per una riproduzione NEMESIS

Replicare questo schema (lesion-deficit vs FC-deficit, per dominio comportamentale) richiede punteggi comportamentali per dominio per soggetto (attenzione, memoria visiva/verbale, linguaggio, motorio, visivo). Da `docs/guides/datasets.md`: **WashU (l'unico dataset con FC oggi) non ha `participants.tsv`/dati clinici** nel formato disponibile — gli altri 3 dataset (PSP, PASPORT, UKLFR) hanno dati clinici ma non FC. Da chiarire prima di disegnare la pipeline di modeling: che punteggi comportamentali esistono realmente per i soggetti WashU (altrove, non in `participants.tsv` standard), o se il piano è aspettare le altre coorti fMRI (Task 3, Padova/Freiburg).
