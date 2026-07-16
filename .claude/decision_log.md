# Log Strategico e Decisionale — NEMESIS

Cronologia dei pivot strategici, dei cambi di paradigma e delle decisioni architetturali di alto livello del progetto — la storia del **perché** abbiamo cambiato rotta, non lo stato attuale (`.claude/stato_progetto.md`, che mostra solo l'oggi) e non gli errori da evitare (`.claude/lessons_learned.md`, che elenca solo i pattern di bug). Non contiene log di codice, bug minori o task quotidiani — solo macro-cambiamenti e bivi decisionali.

Ordine cronologico: dalla voce più vecchia alla più recente. Ogni voce è permanente — quando una decisione viene superata, se ne aggiunge una nuova in fondo, non si modifica quella precedente.

---

## Data / Fase di Sviluppo
2026-07-13 — Fase iniziale della pipeline di retrieval dati

### Contesto / Visione Originale
Il modello dati della pipeline di retrieval aveva un solo asse variabile oltre al nome del file (`space`: nativo/normalizzato, `modality`: tipo di scansione) — sufficiente perché l'unico tipo di dato gestito all'epoca erano le maschere di lesione.

### Il Bivio (Trigger)
È emersa la necessità di includere in futuro anche le feature funzionali (matrici di connettività), la cui struttura non è riconducibile allo stesso schema "spazio nativo/normalizzato" delle lesioni. In parallelo, si è scoperto un limite del vecchio modello: un soggetto la cui derivata esisteva senza il corrispondente file nativo risultava invisibile all'intera pipeline.

### La Nuova Decisione (Il Pivot)
Introdotto un asse strutturale superiore, `object` (lesione vs. feature), sopra il vecchio schema — reso il modello dati estensibile a tipi di dato eterogenei invece che specifico per le sole lesioni.

### Impatto Atteso
La pipeline di retrieval diventa il punto di ingresso unico per qualunque tipo di dato del progetto, non solo le lesioni — ponendo le basi per integrare in futuro, nello stesso flusso, anche le feature strutturali/funzionali necessarie all'analisi di embedding e clustering.

---

## Data / Fase di Sviluppo
2026-07-13 — Fase iniziale della pipeline di retrieval dati

### Contesto / Visione Originale
Quando più file corrispondevano alla stessa richiesta, la pipeline ne sceglieva uno come "prioritario" e segnalava gli altri come ambigui — trattando la molteplicità di file come un'anomalia da risolvere.

### Il Bivio (Trigger)
Analizzando le feature funzionali reali (decine di atlanti di parcellizzazione per le matrici di connettività), è emerso che avere più file per la stessa richiesta è la norma, non un'eccezione: sono dati genuinamente distinti, non varianti di naming dello stesso file.

### La Nuova Decisione (Il Pivot)
Abbandonato il concetto di priorità/ambiguità nella risoluzione dei file: la pipeline ora recupera integralmente tutto ciò che corrisponde a una richiesta, senza scegliere un "vincitore".

### Impatto Atteso
La pipeline smette di scartare implicitamente dati legittimi, allineandosi a una realtà multi-atlante che diventerà centrale quando l'integrazione delle feature funzionali sarà completa su tutti i dataset.

---

## Data / Fase di Sviluppo
2026-07-16 — Consolidamento del modello dati di retrieval

### Contesto / Visione Originale
Il modello dati (nomi dei campi, struttura delle cartelle) era una convenzione interna del progetto, definita prima di un'ispezione approfondita del formato reale dei dati sorgente su EBRAIN.

### Il Bivio (Trigger)
Ispezionando direttamente i 4 dataset sorgente è emerso che sono organizzati secondo lo standard neuroimaging BIDS — e che parte della nomenclatura interna del progetto era in conflitto con il significato che BIDS assegna agli stessi termini. Nella stessa ispezione è emerso anche che i dati grezzi (non derivati) variano troppo tra i 4 siti di acquisizione per essere generalizzati in sicurezza in questa fase.

### La Nuova Decisione (Il Pivot)
Il modello dati è stato riallineato al vocabolario ufficiale BIDS, e lo scope della pipeline è stato deliberatamente ristretto ai soli dati derivati/curati (maschere di lesione validate manualmente, un sottoinsieme già verificato di feature funzionali) — i dati grezzi restano fuori scope, rimandati a una fase futura esplicita.

### Impatto Atteso
Il progetto adotta uno standard riconosciuto dalla comunità neuroimaging invece di una convenzione ad-hoc, riducendo il rischio di errori di interpretazione e facilitando la collaborazione con gruppi esterni che usano BIDS. Restringere lo scope ai soli dati curati riduce il rischio di introdurre rumore nella fase di embedding/clustering, spostando la complessità dei dati grezzi a un momento in cui varrà la pena affrontarla.

---

## Data / Fase di Sviluppo
2026-07-16 — Consolidamento del modello dati di retrieval

### Contesto / Visione Originale
La pipeline trattava qualunque tipo di dato strutturalmente assente per un intero dataset come un errore bloccante, fermando l'intera esecuzione anche quando il resto del lavoro richiesto era comunque realizzabile.

### Il Bivio (Trigger)
Con l'introduzione delle feature funzionali — oggi disponibili per uno solo dei 4 dataset — applicare la stessa regola avrebbe reso impossibile recuperare le maschere di lesione ovunque, semplicemente perché le feature non esistono ancora per 3 dataset su 4.

### La Nuova Decisione (Il Pivot)
La pipeline distingue ora tra un'assenza strutturale attesa (un dataset che semplicemente non ha ancora quel tipo di dato — segnalata esplicitamente ma non bloccante) e una richiesta impossibile su tutta la linea (bloccante, probabile errore di configurazione).

### Impatto Atteso
Il progetto può lavorare fin da subito con coperture dati asimmetriche tra le 4 coorti cliniche, invece di dover attendere che tutti i siti raggiungano la stessa copertura prima di fare qualunque progresso — condizione realistica, dato che i 4 siti di acquisizione difficilmente convergeranno mai su una copertura identica.
