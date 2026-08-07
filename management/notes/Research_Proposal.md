
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

|Assunzione|Fonte|
|---|---|
|Le lesioni da ictus non colpiscono il cervello a caso ma seguono la vascolarizzazione → si clusterizzano naturalmente, molto più delle lesioni sintetiche/casuali|Thiebaut de Schotten 2020|
|La disconnessione strutturale (SDC) spiega le disfunzioni di rete funzionale meglio del danno locale alla materia grigia, specialmente per le fibre interemisferiche|Griffis 2019|
|Conta non solo la disconnessione diretta (fibre tagliate) ma anche quella indiretta (percorsi più lunghi per danno a una tappa intermedia) — entrambe peggiorano la FC|Griffis 2020|
|SDC ha potere predittivo comportamentale paragonabile alla lesione stessa (R² 16–58% a seconda del dominio); la FDC (disconnessione funzionale stimata indirettamente) invece fallisce quasi sempre|Salvalaggio 2020|

## B. Embedding e riduzione dimensionale: la compressione preserva informazione clinicamente utile

|Assunzione|Fonte|
|---|---|
|Comprimere migliaia di mappe di disconnessione in uno spazio a bassa dimensionalità (UMAP, 2D) preserva informazione sufficiente a predire sintomi a 1 anno (MAE <20%), superando 6 modelli concorrenti incluso il volume lesionale|Talozzi 2023|
|La stessa logica si applica alla dinamica del segnale (non alla lesione): comprimere fMRI resting-state in 6 dimensioni via autoencoder non lineare batte nettamente la PCA lineare a parità di dimensioni (spiega di più della varianza) e predice meglio il recupero a 1 anno|Idesis 2023|
|Anche la connettività strutturale (matrici SC intere) si lascia comprimere in pochi gradienti principali interpretabili (antero-posteriore, ventro-dorsale, callosale), stabili test-retest (r > 0.94)|Pini 2026|
|La SDC abbassa la dimensionalità rispetto alla lesione grezza: lesioni topograficamente diverse finiscono nello stesso cluster una volta calcolata la SDC, perché condividono lo stesso streamline disconnesso|Seba_Meeting_1|
|Assunzione sulla numerosità campionaria: aumentare il numero di lesioni migliora la copertura della distribuzione empirica reale dello stroke (motivazione per l'aggregazione multi-sito fino a ~5800 lesioni)|Seba_Meeting_1|

**Nota (da verificare)**: Idesis 2023 comprime la *dinamica* BOLD grezza (235 ROI × 896 timepoint) via autoencoder, non una matrice FC statica. Quello che abbiamo già implementato (`mask_fc.py`/`build_fc_matrix.py`) parte da matrici FC statiche già calcolate (XCP-D). Un embedding FC "come Idesis" in senso stretto richiede le timeseries BOLD grezze — non confermato se disponibili/già recuperate per WU+PD+Friburgo (Seba_Meeting_2 cita ALFF/ReHo "che derivano dal BOLD", che implicherebbero l'esistenza delle timeseries da qualche parte, ma non la loro disponibilità nella pipeline attuale). Nel frattempo un embedding PCA/UMAP sulla matrice FC statica (edges come feature) è già fattibile con l'infrastruttura esistente, riusando `dim_reduction`/`clustering` come per lesione/SDC — non fedele a Idesis, ma stessa logica di "terzo branch indipendente".

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

|Assunzione|Fonte|
|---|---|
|La FC non va guardata solo come media statica: esistono stati dinamici distinti (finestre scorrevoli + k-means) la cui prevalenza si associa alla gravità del deficit motorio, invisibili all'analisi statica|Bonkhoff 2020|
|La modularità di rete, crollata in fase acuta, si ripristina progressivamente (2 settimane → 3 mesi → 1 anno) e questo recupero correla con linguaggio/memoria/attenzione ma non con motorio/visione|Siegel 2018|
|Il "fingerprint" di connettività individuale si stabilizza precocemente (~3 settimane), pur restando persistentemente diverso dalla norma sana; il rimodellamento a lungo termine è specifico per network (SM/VA cambiano presto, DMN/FPN declinano più tardi). Il fingerprint è stabile e unico nei soggetti sani; nello stroke si osserva una riconfigurazione|Santoro 2026|

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

|Assunzione|Fonte|
|---|---|
|Proiettare la lesione su atlanti di rete funzionale (Yeo) o strutturale (Figley) predice l'outcome post-trombectomia molto meglio della classica mappa vascolare (R²=0.382 vs 0.146); l'aggiunta ai dati clinici di base migliora ulteriormente (0.484→~0.6)|Bisogno 2025|
|Le variabili cliniche/demografiche di base (età, NIHSS, lato) battono lesione e SDC nella previsione multi-dominio a 2 settimane/3 mesi/12 mesi|Cinetto (in bozza)|

**Nota**: il valore incrementale del neuroimaging rispetto alla clinica non è un dato acquisito in letteratura, dipende dall'outcome e dal disegno.

## I. Clustering di traiettorie di recupero

|Assunzione|Fonte|
|---|---|
|Il clustering (Repeated Spectral Clustering) su tassi di recupero individuali supera la dicotomia rigida fitters/non-fitters del modello lineare PRR, rivelando 6 traiettorie distinte, con un RR precoce predittivo dell'appartenenza al cluster (~90% accuratezza)|Zanola 2026|

## J. Integrazione multimodale / generalizzabilità

|Assunzione|Fonte|
|---|---|
|L'armonizzazione statistica tra scanner (neuroCombat) è necessaria per il confronto tra coorte ST e coorte HC di Washu, che hanno scanner diversi|Seba_Meeting_3|

## K. Framing epistemico del progetto

|Statement|Fonte|Perché è rilevante|
|---|---|---|
|"Fino ad ora il comportamento è stato l'asse per la predizione delle lesioni"|Corbetta_Meeting_1|Non è un'assunzione di background ma una critica esplicita alla letteratura corrente: la maggior parte dei paper (Siegel, Corbetta 2015, Bisogno) usa la lesione/SDC per predire il comportamento come outcome finale. NEMESIS, nella sua componente esplorativa (Task multimodale, inferenza anatomia→funzione), propone invece di **usare l'anatomia per inferire il fenotipo funzionale**, spostando l'asse. Va esplicitato nella nota come giustificazione della novità metodologica.|


# Cosa possiamo fare noi

## Dati per modalità

| Modalità                                                              | N stimata                          | Dataset coperti                                                                                            | Note                                                         |
| --------------------------------------------------------------------- | ---------------------------------- | ---------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------ |
| Lesioni (mask binarie)                                                | fino a ~5800                       | Washu(200), PASPORT(100), PSP(200), UKLFR(700), Amburgo(500, in arrivo), UCL(4100, da negoziare), Santiago | La N più grande e più eterogenea per sito                    |
| SDC (da lesione via BCB Toolkit)                                      | stessa N delle lesioni disponibili | idem                                                                                                       | Derivata, non richiede dati aggiuntivi oltre la lesione      |
| Feature funzionali (matrici FC)                                       | sottoinsieme, ordine di ~500       | Washu + Padova + Friburgo                                                                                  | Richiede coorte sana di riferimento per costruire le matrici |
| Feature EEG                                                           | ~80                                | Padova                                                                                                     | In arrivo (TBD, settembre/ottobre);                          |
| Dati clinico/comportamentali (tsv: NIHSS + subitem, dati demografici) | variabile per dataset              | tutti quelli con participants.tsv                                                                          | Copertura da verificare dataset per dataset                  |
| Longitudinale                                                         | **da definire**                    | non chiaro quali dataset abbiano più timepoint, né a quali distanze (2 sett? 3 mesi? 1 anno?)              |                                                              |


##  Workflow possibile

```
LESIONI (mask binarie, ~5750)     SDC (via BCB Toolkit, stessa N)     FC (embedding+clustering indipendente, sottoinsieme fMRI ~500 WU+PD+Fri)
              |                                |                                       |
              v                                v                                       v
   Embedding lesioni (PCA/UMAP/t-SNE)   Embedding SDC (PCA/UMAP/t-SNE)   Embedding FC (PCA/UMAP su matrice statica; autoencoder su dinamica se disponibile)
              |                                |                                       |
              v                                v                                       v
      Clustering lesioni (*)             Clustering SDC (*)                    Clustering FC (*)
              |                                |                                       |
              +----------------+---------------+-------------------+-------------------+
                               |                                   |
                               v                                   v
            Confronto a coppie: lesione vs SDC / lesione vs FC / SDC vs FC (ARI, NMI, contingency table)
                                                |
                                                v
                Cluster anatomico di riferimento (*) (lesione e/o SDC, in base al confronto sopra)
                                                |
                +-------------------------------+--------------------------------+
                |                                                                |
                v                                                                v
   Sottoinsieme con fMRI (~500, WU+PD+Fri —                          Tutti i soggetti del cluster
   ha già un'etichetta di cluster FC indipendente)                    (anche senza fMRI diretta)
                |                                                                |
                v                                                                |
   FC mascherata su lesione + z-score vs coorte sana (Siegel 2016)                |
                |                                                                |
                v                                                                |
   Feature locali vs globali (ReHo, ALFF, GFC media/varianza — Volpi 2024/2025)    |
                |                                                                |
                v                                                                |
   Fingerprint funzionale medio per cluster, confrontato col cluster FC           |
   indipendente (ARI/NMI di sopra, qui usata come validazione)                    |
                |                                                                |
                +--------------------------------+-------------------------------+
                                                  |
                                                  v
                        Inferenza fenotipo funzionale (cluster anatomico -> fingerprint atteso)
                                                  |
                                                  v
        Correlazione con outcome clinico-comportamentale (NIHSS, subitem, domini;
        Kruskal-Wallis/chi2 + FDR, schema Zanola 2026)


EEG (Task 4, n~80, Padova) — deferred a Sett/Ott 2026

(*) per ogni clustering: analisi/visualizzazione dedicata (mappe su MNI, scatter colorato,
    overlap con atlanti, radar plot, matrici FC per cluster...) — dettaglio nella colonna
    "Metodo candidato" della tabella sotto
```


## Tabella riepilogativa per fasi del workflow

Per ogni fase, tre ruoli possibili della letteratura: **base** (perché lo facciamo), **confronto** (cosa replichiamo sui nostri dati), **trampolino** (idea nuova/estensione, ancora da discutere col gruppo). La colonna "Metodo candidato" include, dove pertinente, anche le analisi/visualizzazioni previste sul clustering stesso (validazione, confronto tra clustering, interpretazione) — non solo il metodo di embedding/clustering in senso stretto.

| Fase                                                                                                     | Task (meeting/README) | Metodi candidati                                                                                                                                                                                                                                                                                                                               | Base fondante                                                                                                                                             | Confronto/replica                                                                                                                                                                | Trampolino di lancio                                                                                                                                                                                                                                                                                        |
| -------------------------------------------------------------------------------------------------------- | --------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1. **Embedding lesioni** (n~5750)                                                                        | Task 1                | PCA(varimax) / UMAP / t-SNE su lesioni parcellizzate; <br>analisi/viz sul clustering risultante: mappa di probabilità delle lesioni per cluster su MNI, scatter dell'embedding colorato per variabili cliniche, overlap % con atlanti (vascolare/Yeo/Figley), radar/spider plot per centroide                                                  | **Thiebaut** de Schotten 2020 (lesioni non casuali, seguono la vascolarizzazione → clusterizzano)                                                         | Replicare la PCA varimax di Thiebaut de Schotten (46 componenti, 30 spiegano >90% varianza) sulla nostra N molto più ampia; confrontare i cluster con i territori vascolari noti | Confrontare sistematicamente più combinazioni embedding×clustering alla scala n~5750                                                                                                                                                                                                                        |
| 2. **Embedding SDC**                                                                                     | Task 2                | Stessi metodi di riduzione, su SDC parcellizzata (BCB Toolkit); <br>stessa analisi/viz della fase 1 (mappa su MNI, scatter colorato, overlap atlanti, radar plot)                                                                                                                                                                              | **Griffis** 2019/2020 (SDC spiega la disfunzione di rete meglio del danno locale); <br>**Salvalaggio** 2020 (SDC ≈ lesione come predittore, FDC fallisce) | Replicare il morfospazio **UMAP** di Talozzi 2023, ma partendo da SDC (non lesione grezza) e sulla nostra coorte                                                                 | —                                                                                                                                                                                                                                                                                                           |
| 2b. **Embedding + clustering FC indipendente** (n~500, WU+PD+Fri)                                        | Task 3                | PCA/UMAP su matrice FC statica (fattibile ora, riusa `dim_reduction`); <br>autoencoder su dinamica BOLD se disponibile; <br>analisi/viz: matrice FC media per cluster e diff vs coorte sana, riassunto per network Yeo (within/between), feature locali (ReHo/ALFF) su superficie, composizione per dataset/sito (controllo artefatto scanner) | **Idesis** 2023 (autoencoder su dinamica BOLD batte PCA lineare, predice recupero a 1 anno)                                                               |                                                                                                                                                                                  | Dà un clustering FC indipendente da usare come "vero" fenotipo per validare l'inferenza anatomia→funzione (fase 5), in aggiunta al ruolo descrittivo che la FC ha già in fase 4                                                                                                                             |
| 3. **Confronto cluster** lesione vs SDC vs FC                                                            | Task 1+2+3            | ARI, NMI, contingency table, a coppie (lesione-SDC, lesione-FC, SDC-FC); <br>contingency table/heatmap cross-modale; copertura per dataset nell'embedding (quanti soggetti per dataset in ciascun cluster)                                                                                                                                     |                                                                                                                                                           |                                                                                                                                                                                  | **Candidato per analisi originale**:<br>- *lesioni topograficamente diverse condividono lo stesso streamline disconnesso*<br>- quantificare quanto la SDC comprime cluster lesionali distinti in uno stesso cluster, <br>- e quanto lesione/SDC predicono davvero il cluster FC  (fenotipi generalizzabili) |
| 4. **Feature funzionali per cluster anatomico** (n~500, WU+PD+Fri) — ruolo originale della FC, invariato | Task 3                | FC mascherata                                                                                                                                                                                                                                                                                                                                  | **Griffis** 2019 (PLSC struttura-funzione); <br>**Santoro** 2026 (fingerprint individuale stabile ma persistentemente diverso dalla norma sana)           | Riprodurre l'approccio di **Siegel** 2016 di mascheramento FC su estensione lesionale                                                                                            | Calcolo z-score per singolo paziente vs template sano, poi mediato per cluster anatomico                                                                                                                                                                                                                    |
| 5. **Inferenza fenotipo funzionale** da cluster anatomico                                                | Task 3                | Media delle feature funzionali (FC/ALFF/ReHo) all'interno di ciascun cluster anatomico, validata contro il cluster FC indipendente (fase 2b/3) sul sottoinsieme che ce l'ha                                                                                                                                                                    | —                                                                                                                                                         | —                                                                                                                                                                                | **Goals**: <br>- "cluster anatomico → fingerprint funzionale stimato" per soggetti senza fMRI diretta; <br>- capovolge l'asse comportamento→lesione tipico della letteratura corrente (vedi K); <br>target 4-5 fenotipi funzionali (feasibility, da validare)                                               |
| 6. **Feature locali vs. globali** del segnale FC                                                         | Task 3                | ReHo, ALFF, ampiezza/covarianza, media/varianza GFC (catalogo di 50 feature, Volpi 2024/2025)                                                                                                                                                                                                                                                  | Volpi 2024 (ReHo = predittore locale più forte del metabolismo)                                                                                           | Volpi lavora su soggetti sani: da noi sarebbe la prima applicazione a una coorte stroke                                                                                          | Domanda esplicita e ancora aperta: non è chiaro come le feature locali siano correlate con le feature globali" --> usare il catalogo Volpi come punto di partenza per costruire predittori locali intra-cluster                                                                                             |
| 7. **Correlazione con outcome clinico-comportamentale**                                                  | Task 5                | Ridge regression / PCA sui punteggi comportamentali; <br>test non parametrici + FDR per validare i cluster contro variabili esterne; <br>boxplot/violin delle variabili cliniche per cluster                                                                                                                                                   | Corbetta 2015<br>Bisogno 2021<br>Facchini 2023 (struttura a 3 fattori, bassa dimensionalità); <br>Talozzi 2023 (DSD)                                      | Validare i nostri cluster (anatomici/SDC) contro NIHSS e subitem con lo schema statistico di Zanola 2026 (Kruskal-Wallis/χ² + correzione FDR)                                    | Testare sulla nostra coorte la tensione clinica-vs-imaging emersa in H (Bisogno 2025 vs Cinetto): i cluster anatomici/SDC aggiungono valore incrementale ai soli dati clinico-demografici, o no?                                                                                                            |
| 8. **EEG** (n~80, Padova)                                                                                | Task 4                | TBD                                                                                                                                                                                                                                                                                                                                            | —                                                                                                                                                         | —                                                                                                                                                                                | Deferred a settembre/ottobre 2026                                                                                                                                                                                                                                                                           |
