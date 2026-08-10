Revisione di ## Tabella riepilogativa per fasi del workflow
- Evitare tutta questa introduzione:
	Per ogni fase, tre ruoli possibili della letteratura: **base** (perché lo facciamo), **confronto** (cosa replichiamo sui nostri dati), **trampolino** (idea nuova/estensione, ancora da discutere col gruppo). La colonna "Metodo candidato" include, dove pertinente, anche le analisi/visualizzazioni previste sul clustering stesso (validazione, confronto tra clustering, interpretazione) — non solo il metodo di embedding/clustering in senso stretto.

	Nella colonna "Metodi candidati", ogni riga separa dove pertinente **Riduzione**, **Clustering** e **Analisi/viz** (o l'equivalente per fasi che non fanno embedding/clustering in senso stretto) — non più un unico paragrafo indistinto. Le voci marcate **[fatto]** sono già implementate e verificate su dati reali (dettagli in `management/notes/workflow.md`), il resto è ancora pianificato.


### Note generali
- Siccome i task non sono ancora ben suddivisi, eviterei di mettere la colonna
- Evita di scrivere [fatto]
- prima della tabella di che questo è una bozza del workflow operativo e ogni step è dettagliato in documentazione e note a parte
- Rendi tutte le informazioni nelal tabella più schematiche e leggibili, magari organizzandole per punti

#### Fase 0
- Nei metodi di che fai EDA con statistiche e plotting
	- disponibilit dati
	- demografia
	- --> sii più ago
- ok 
	- **Frequenza voxel-wise** 
	**Soglia di mascheramento 

- metti — su "Trampolino di lancio"

#### Fase 1
- ok le riduzioni che hai messo ma accenna che possono essere trovatr altre
- riduzione può essere fattoa su lesioni parcellizzate o meno
- clustering ok
- su analisi e vizualizzazione
	- non essere così specifico, in virtù del:  questo è una bozza del workflow operativo e ogni step è dettagliato in documentazione e note a parte
	- metti i tipi di analisi e di plot (per punti che si possono fare)
	- mantieni la questione centroide 
	- le questioni specifiche che hai scritto tipo:  scatter dell'embedding colorato per dataset (copertura reciproca) e per subitem NIHSS specifici — es. item 9=linguaggio, item 11=neglect, 5a-6b=motorio, dato che ogni subitem mappa un dominio comportamentale specifico (`Seba_Meeting_1`) --> vanno nei TO DO
	- 
#### Fase 2
- fai un bullet point appostio sul fatto che le lesioni hanno passato BCB Toolkit che fornisce sia lesione che parcellazzione
- il morfospazio di Talozzi si può fare sia su lesione grezza che SDC suppongo

#### Fase 2.b
- per ora abbiamo solo WU
- Riduzione:** PCA/UMAP/altri --> ricorda sempre di menzionare la possibilità di altri metodi
- stesso discorso di fase uno per i metodi di analisi 
- evita di menzionare l'inferenza qui e concentrati sul fenotipo: Dà un clustering FC indipendente da usare come "vero" fenotipo per validare l'inferenza anatomia→funzione (fase 5), in aggiunta al ruolo descrittivo che la FC ha già in fase 4

#### Fase 3
- 

#### Fase 4
- chiarire meglio cosa intendi: **Metodo:** FC mascherata (soglia coverage 50% per nodo, mascheramento NaN **[fatto]** su tutta la coorte WashU, `mask_fc.py`)
- chiarire meglio in che modo useremmo
	- griffis
	- santoro
	- siegel
	- Calcolo z-score per singolo paziente vs template sano, poi mediato per cluster anatomico --> in che senso trampolino di lanio

#### Fase 5
- Capovolge l'asse comportamento→lesione tipico della letteratura corrente (vedi K); 
target 4-5 fenotipi funzionali (feasibility, da validare) ---> spiega meglio e togli riferimento a K
#### Fase 6
- non si capisce bene come questa fase si differenzia dalle precedenti
#### Fase 7
- bene il contenuto, soltanto da strutturare meglio e da chiarire qual è lo scopo dei metodi --> una votla fatto possiamo pensare ad altri tipi di metodi oltre a ridge regression / PCA sui punteggi comportamentali
#### Fase 8
TBD


-----



