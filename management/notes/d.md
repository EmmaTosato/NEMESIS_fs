
# Domande 

1. **Integrazione multimodale**: come si combinano in un quadro unico i segnali anatomico (lesione), strutturale (SDC), funzionale (FC/FDC) e fisiologico (EEG)? In particolare:
    - come costruire uno spazio (o modello) che integri le modalità invece di trattarle come storie separate;
    - come si sovrappongono/divergono spazialmente e informativamente le diverse modalità tra loro.
2. **Alterazioni canoniche di connettività**: esistono pattern di alterazione della FC ricorrenti e generalizzabili tra pazienti, distinti dalla variabilità idiosincratica del singolo caso?
	- **Fenotipi generalizzabili tra dataset**: i pattern identificati (anatomici e/o funzionali) si riproducono across siti/scanner diversi, o richiedono armonizzazione (es. neuroCombat) per essere confrontabili?
	- **Inferenza anatomia → funzione**: dato un paziente di cui si conosce solo lesione/SDC (senza fMRI), è possibile stimare a quale fenotipo funzionale ("fingerprint") appartiene probabilmente, sulla base del cluster anatomico di appartenenza?
3. **Locale vs. globale**: come si collegano le caratteristiche locali del segnale funzionale alle alterazioni globali dell'organizzazione di rete post-ictus?
	 - **Quale feature locale predice meglio il comportamento?** Tra i candidati: ampiezza del segnale, covarianza, ALFF, Regional Homogeneity (ReHo), media/varianza della Global Functional Connectivity (GFC), e parametri locali in funzione della distanza dalla lesione.


# Basi fondanti

## A. Lesione → Disconnessione: la SDC non è ridondante rispetto alla lesione

| Assunzione                                                                                                                                                                                          | Fonte                         |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------- |
| Le lesioni da ictus non colpiscono il cervello a caso ma seguono la vascolarizzazione → si clusterizzano naturalmente, molto più delle lesioni sintetiche/casuali                                   | Thiebaut de Schotten 2020<br> |
| La disconnessione strutturale (SDC) spiega le disfunzioni di rete funzionale meglio del danno locale alla materia grigia, specialmente per le fibre interemisferiche                                | Griffis 2019                  |
| Conta non solo la disconnessione diretta (fibre tagliate) ma anche quella indiretta (percorsi più lunghi per danno a una tappa intermedia) — entrambe peggiorano la FC                              | Griffis 2020                  |
| SDC ha potere predittivo comportamentale paragonabile alla lesione stessa (R² 16–58% a seconda del dominio); la FDC (disconnessione funzionale stimata indirettamente) invece fallisce quasi sempre | Salvalaggio 2020              |

## B. Embedding e riduzione dimensionale: la compressione preserva informazione clinicamente utile

| Assunzione                                                                                                                                                                                                                                                                      | Fonte          |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------- |
| Comprimere migliaia di mappe di disconnessione in uno spazio a bassa dimensionalità (UMAP, 2D) preserva informazione sufficiente a predire sintomi a 1 anno (MAE <20%), superando 6 modelli concorrenti incluso il volume lesionale                                             | Talozzi 2023   |
| La stessa logica si applica alla dinamica del segnale (non alla lesione): comprimere fMRI resting-state in 6 dimensioni via autoencoder non lineare batte nettamente la PCA lineare a parità di dimensioni (spiega di più della varianza) e predice meglio il recupero a 1 anno | Idesis 2023    |
| Anche la connettività strutturale (matrici SC intere) si lascia comprimere in pochi gradienti principali interpretabili (antero-posteriore, ventro-dorsale, callosale), stabili test-retest (r > 0.94)                                                                          | Pini 2026      |
| La SDC abbassa la dimensionalità rispetto alla lesione grezza: lesioni topograficamente diverse finiscono nello stesso cluster una volta calcolata la SDC, perché condividono lo stesso streamline disconnesso                                                                  | Seba_Meeting_1 |
| Assunzione sulla numerosità campionaria: aumentare il numero di lesioni migliora la copertura della distribuzione empirica reale dello stroke (motivazione per l'aggregazione multi-sito fino a ~5800 lesioni)                                                                  | Seba_Meeting_1 |


## C. Feature locali del segnale funzionale

|Assunzione|Fonte|
|---|---|
|ReHo (sincronizzazione locale tra voxel vicini) è il singolo predittore più forte e stabile del metabolismo del glucosio locale (32–53% varianza spiegata) in soggetti sani|Volpi 2024|
|Il consumo di glucosio si scompone in due processi indipendenti — consegna (K1) e fosforilazione (k3) — con determinanti diversi: k3 legato a ReHo, K1 legato al metabolismo dell'ossigeno (CMRO2). Fornisce anche il catalogo completo delle 50 feature funzionali (Signal, HRF, sFC, tvFC pool)|Volpi 2025|


## D. Organizzazione globale delle reti funzionali

|Assunzione|Fonte|
|---|---|
|Lesione e FC predicono domini comportamentali diversi: la lesione è migliore per motorio/visivo, la FC per memoria; attenzione e linguaggio sono ben predetti da entrambe|Siegel 2016|
|Il danno da ictus riduce la modularità e l'entropia degli stati neurali esplorabili dal cervello (anche nell'emisfero sano); questo framework teorico spiega perché i deficit si raggruppano in poche dimensioni|Corbetta 2018|


## E. Dinamica temporale e stabilità individuale

| Assunzione                                                                                                                                                                                                                                                                                                                                                                                                      | Fonte         |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------- |
| La FC non va guardata solo come media statica: esistono stati dinamici distinti (finestre scorrevoli + k-means) la cui prevalenza si associa alla gravità del deficit motorio, invisibili all'analisi statica                                                                                                                                                                                                   | Bonkhoff 2020 |
| La modularità di rete, crollata in fase acuta, si ripristina progressivamente (2 settimane → 3 mesi → 1 anno) e questo recupero correla con linguaggio/memoria/attenzione ma non con motorio/visione                                                                                                                                                                                                            | Siegel 2018   |
| Il "fingerprint" di connettività individuale si stabilizza precocemente (~3 settimane), pur restando persistentemente diverso dalla norma sana; il rimodellamento a lungo termine è specifico per network (SM/VA cambiano presto, DMN/FPN declinano più tardi).<br>l fingerprint di connettività individuale è stabile e unico nei soggetti sani; nello stroke si osserva una riconfigurazione del fingerprint. | Santoro 2026  |


## F. Evoluzione strutturale a lungo termine

|Assunzione|Fonte|
|---|---|
|Mentre la FC tende a normalizzarsi nel tempo, la SC (materia bianca) mostra una traiettoria divergente: degenerazione progressiva anche a distanza dalla lesione, incluso l'emisfero contralesionale. Doppia dissociazione: alterazioni SC globali predicono deficit cognitivi solo in acuto; la microstruttura locale nei tratti disconnessi predice stabilmente i deficit motori sia in acuto che a 3 mesi|Pini 2026|

## G. Struttura del comportamento (bassa dimensionalità)

|Assunzione|Fonte|
|---|---|
|I sintomi post-ictus si riducono a 3 macro-fattori (69% varianza spiegata); danno prevalentemente sottocorticale/materia bianca (solo 13% lesioni puramente corticali)|Corbetta 2015|
|Stessa struttura a 3 fattori replicata su coorte indipendente con test rapido (NIHSS+OCS, 15 min) invece della batteria estesa (2.5h)|Bisogno 2021|
|Stessa struttura a 3 fattori trovata anche nei tumori cerebrali → non è un artefatto della distribuzione vascolare tipica dello stroke, ma riflette un'architettura cognitiva più generale|Facchini 2023|

## H. Valore predittivo clinico — tensione interna alla letteratura del gruppo

| Assunzione                                                                                                                                                                                                                                                   | Fonte              |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------ |
| Proiettare la lesione su atlanti di rete funzionale (Yeo) o strutturale (Figley) predice l'outcome post-trombectomia molto meglio della classica mappa vascolare (R²=0.382 vs 0.146); l'aggiunta ai dati clinici di base migliora ulteriormente (0.484→~0.6) | Bisogno 2025       |
| Le variabili cliniche/demografiche di base (età, NIHSS, lato) battono lesione e SDC nella previsione multi-dominio a 2 settimane/3 mesi/12 mesi                                                                                                              | Cinetto (in bozza) |
|                                                                                                                                                                                                                                                              |                    |

**Nota**:  il valore incrementale del neuroimaging rispetto alla clinica non è un dato acquisito in letteratura, dipende dall'outcome e dal disegno.

## I. Clustering di traiettorie di recupero

|Assunzione|Fonte|
|---|---|
|Il clustering (Repeated Spectral Clustering) su tassi di recupero individuali supera la dicotomia rigida fitters/non-fitters del modello lineare PRR, rivelando 6 traiettorie distinte, con un RR precoce predittivo dell'appartenenza al cluster (~90% accuratezza)|Zanola 2026|
#### J. Integrazione multimodale / generalizzabilità 

| Assunzione                                                                                                                                        | Fonte          |
| ------------------------------------------------------------------------------------------------------------------------------------------------- | -------------- |
| L'armonizzazione statistica tra scanner (neuroCombat) è necessaria per il confronto tra coorte ST e coorte HC di Washu, che hanno scanner diversi | Seba_Meeting_3 |
#### K. Framing epistemico del progetto — sezione nuova

|Statement|Fonte|Perché è rilevante|
|---|---|---|
|"Fino ad ora il comportamento è stato l'asse per la predizione delle lesioni"|Corbetta_Meeting_1|Non è un'assunzione di background ma una critica esplicita alla letteratura corrente: la maggior parte dei paper (Siegel, Corbetta 2015, Bisogno) usa la lesione/SDC per predire il comportamento come outcome finale. NEMESIS, nella sua componente esplorativa (Task multimodale, inferenza anatomia→funzione), propone invece di **usare l'anatomia per inferire il fenotipo funzionale**, spostando l'asse. Va esplicitato nella nota come giustificazione della novità metodologica.|


# Cosa possiamo riprodurre/validare con i nostri dati — revisione

Il punto chiave da esplicitare, prima della tabella: **non tutte le modalità hanno la stessa N**. Questo non è un dettaglio tecnico ma vincola direttamente quali confronti sono fattibili e quali no.

## Dati per modalità

| Modalità                                                              | N stimata                          | Dataset coperti                                                                                            | Note                                                         |
| --------------------------------------------------------------------- | ---------------------------------- | ---------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------ |
| Lesioni (mask binarie)                                                | fino a ~5800                       | Washu(200), PASPORT(100), PSP(200), UKLFR(700), Amburgo(500, in arrivo), UCL(4100, da negoziare), Santiago | La N più grande e più eterogenea per sito                    |
| SDC (da lesione via BCB Toolkit)                                      | stessa N delle lesioni disponibili | idem                                                                                                       | Derivata, non richiede dati aggiuntivi oltre la lesione      |
| Feature funzionali (matrici FC)                                       | sottoinsieme, ordine di ~500       | Washu + Padova + Friburgo                                                                                  | Richiede coorte sana di riferimento per costruire le matrici |
| Feature EEG                                                           | ~80                                | Padova                                                                                                     | In arrivo (TBD, settembre/ottobre);                          |
| Dati clinico/comportamentali (tsv: NIHSS + subitem, dati demografici) | variabile per dataset              | tutti quelli con participants.tsv                                                                          | Copertura da verificare dataset per dataset                  |
| Longitudinale                                                         | **da definire**                    | non chiaro quali dataset abbiano più timepoint, né a quali distanze (2 sett? 3 mesi? 1 anno?)              |                                                              |

## Cosa si può fare
### Domanda 1 — Integrazione multimodale

_(come si combinano lesione, SDC, FC/FDC, EEG in un quadro unico; come si sovrappongono/divergono le modalità)_

| Cosa replicare                                                            | Riferimento  | Perché serve a questa domanda                                                                                                                                                                                                                                               |
| ------------------------------------------------------------------------- | ------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Relazionare pattern SDC e pattern FC nella stessa coorte (approccio PLSC) | Griffis 2019 | È il test minimo a due modalità: prima di poter dire come si "sovrappongono/divergono" più modalità insieme, bisogna sapere come si relazionano due alla volta. Senza questo passaggio non si può nemmeno interpretare cosa succede aggiungendo una terza o quarta modalità |


---

### Domanda 2 — Alterazioni canoniche di connettività

_(pattern ricorrenti e generalizzabili tra pazienti; generalizzabilità tra dataset; inferenza anatomia→funzione)_

| Cosa replicare                                                                               | Riferimento                             | Perché serve a questa domanda                                                                                                                                                                                                                                                                             |
| -------------------------------------------------------------------------------------------- | --------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Embedding UMAP/t-SNE + clustering topografico di lesioni e SDC                               | Thiebaut de Schotten 2020, Talozzi 2023 | È il prerequisito: un "pattern canonico" o un "fenotipo" richiede prima di tutto una struttura di cluster su cui poi verificare se è ricorrente/generalizzabile                                                                                                                                           |
| Confronto tra soluzione di clustering su lesione vs su SDC (ARI/NMI)                         | Idea originale                          | Verifica se il pattern "canonico" trovato dipende dalla rappresentazione usata (lesione grezza vs SDC) — un pattern robusto dovrebbe emergere in entrambe le rappresentazioni, o la divergenza stessa è informativa su cosa la SDC aggiunge                                                               |
| Repliche longitudinali (Siegel 2018, Santoro 2026, Pini 2026)                                | —                                       | Un pattern "canonico" trovato in acuto ha senso come fenotipo stabile solo se sappiamo se persiste nel tempo o si riorganizza — altrimenti "canonico" descriverebbe solo un istante, non una caratteristica del paziente                                                                                  |

---

### Domanda 3 — Locale vs. globale

_(come si collegano le feature locali del segnale funzionale alle alterazioni globali di rete; quale feature locale predice meglio il comportamento)_

| Cosa replicare                                                                                | Riferimento        | Perché serve a questa domanda                                                                                                                                                                                                                                 |
| --------------------------------------------------------------------------------------------- | ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Adattare il catalogo delle 4 pool di feature locali (Signal, HRF, sFC, tvFC) al comportamento | Volpi 2024/2025    | Risponde direttamente alla seconda parte della domanda: è l'unico framework esistente che confronta sistematicamente più feature locali candidate — va solo ri-targettizzato dal metabolismo al comportamento                                                 |


---

### Non legate direttamente a una domanda di ricerca, ma di supporto trasversale

|Cosa replicare|Riferimento|Ruolo|
|---|---|---|
|Siegel replication in parallelo (lesione→comportamento; SDC→comportamento)|Siegel 2016|Non risponde a nessuna delle tre domande direttamente — è la validazione clinica del framework lesione/SDC che sostiene l'intero progetto (l'obiettivo scientifico dichiarato a monte delle tre domande esplorative)|

---


