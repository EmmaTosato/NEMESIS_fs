
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
LESIONI                              SDC
 (mask binarie,                   (via BCB Toolkit,
  ~5750 soggetti)                  stessa N lesioni)
      |                                   |
      v                                   v
 Embedding lesioni                  Embedding SDC
 (PCA / UMAP / t-SNE / ...)          (PCA / UMAP / t-SNE / ...)          
      |                                   |
      v                                   v
 Clustering lesioni                 Clustering SDC
 (k-means/ HDBSCAN / ...)       (k-means/ HDBSCAN / ...)
      |                                   |
      +-----------------+-----------------+
                        |
                        v
         Confronto cluster lesione vs SDC
           (ARI, NMI, contingency table)
                                 
```


## Tabella riepilogativa per fasi del workflow

Per ogni fase, tre ruoli possibili della letteratura: **base** (perché lo facciamo), **confronto** (cosa replichiamo sui nostri dati), **trampolino** (idea nuova/estensione, ancora da discutere col gruppo).

| Fase | Task (meeting/README) | Metodo candidato | Base fondante | Confronto/replica | Trampolino di lancio |
|---|---|---|---|---|---|
| 1. Embedding lesioni (n~5750) | Task 1 | PCA(varimax) / UMAP / t-SNE su lesioni parcellizzate (atlante combinato Glasser+HO, già implementato) | Thiebaut de Schotten 2020 (lesioni non casuali, seguono la vascolarizzazione → clusterizzano) | Replicare la PCA varimax di Thiebaut de Schotten (46 componenti, 30 spiegano >90% varianza) sulla nostra N molto più ampia; confrontare i cluster con i territori vascolari noti | Confrontare sistematicamente più combinazioni embedding×clustering alla scala n~5750 (pipeline `dim_reduction`/`clustering` già supporta il fine-tuning) — scala non coperta dai paper raccolti finora |
| 2. Embedding SDC (n~3000) | Task 2 | Stessi metodi di riduzione, su SDC parcellizzata (BCB Toolkit) | Griffis 2019/2020 (SDC spiega la disfunzione di rete meglio del danno locale); Salvalaggio 2020 (SDC ≈ lesione come predittore, FDC fallisce) | Replicare il morfospazio UMAP di Talozzi 2023, ma partendo da SDC (non lesione grezza) e sulla nostra coorte | — |
| 3. Confronto cluster lesione vs SDC | Task 1+2 | ARI, NMI, contingency table | Intuizione qualitativa in `Seba_Meeting_1` ("lesioni topograficamente diverse condividono lo stesso streamline disconnesso") | Nessun paper della raccolta attuale fa questo confronto quantitativo diretto (da verificare estendendo la rassegna, TODO `Corbetta_Meeting_1`) | **Candidato per analisi originale**: quantificare quanto la SDC comprime cluster lesionali distinti in uno stesso cluster — risponde direttamente alla Domanda 2 (fenotipi generalizzabili) |
| 4. Feature funzionali per cluster anatomico (n~500, WU+PD+Fri) | Task 3 | FC mascherata su lesione (già implementato, `mask_fc.py`/`build_fc_matrix.py`), z-score rispetto a coorte sana | Griffis 2019 (PLSC struttura-funzione); Santoro 2026 (fingerprint individuale stabile ma persistentemente diverso dalla norma sana) | Riprodurre l'approccio di Siegel 2016 di mascheramento FC su estensione lesionale, come richiesto esplicitamente in `Seba_Meeting_3` | Calcolo z-score per singolo paziente vs template sano (richiesto in `Corbetta_Meeting_1`), poi mediato per cluster anatomico — non ancora fatto in nessun paper della raccolta su questa scala multi-sito |
| 5. Inferenza fenotipo funzionale da cluster anatomico | Task 3 | Media delle feature funzionali (FC/ALFF/ReHo) all'interno di ciascun cluster anatomico | — | — | **Goal esplicito di `Seba_Meeting_2`**: "cluster anatomico → fingerprint funzionale stimato" per soggetti senza fMRI diretta; capovolge l'asse comportamento→lesione tipico della letteratura corrente (vedi K); target 4-5 fenotipi funzionali (feasibility, da validare) |
| 6. Feature locali vs. globali del segnale FC | Task 3 | ReHo, ALFF, ampiezza/covarianza, media/varianza GFC (catalogo di 50 feature, Volpi 2024/2025) | Volpi 2024 (ReHo = predittore locale più forte del metabolismo, R²=32-53% su sani); Volpi 2025 (k3 legato a ReHo, K1 a CMRO2) | — (Volpi lavora su soggetti sani, non stroke: da noi sarebbe la prima applicazione a una coorte lesionale) | Domanda esplicita e ancora aperta in `Corbetta_Meeting_1` ("non è chiaro come le feature locali siano correlate con le feature globali") — usare il catalogo Volpi come punto di partenza per costruire predittori locali intra-cluster |
| 7. Correlazione con outcome clinico-comportamentale | Task 5 | Ridge regression / PCA sui punteggi comportamentali; test non parametrici + FDR per validare i cluster contro variabili esterne | Corbetta 2015/Bisogno 2021/Facchini 2023 (struttura a 3 fattori, bassa dimensionalità); Talozzi 2023 (DSD) | Validare i nostri cluster (anatomici/SDC) contro NIHSS e subitem con lo schema statistico di Zanola 2026 (Kruskal-Wallis/χ² + correzione FDR) | Testare sulla nostra coorte la tensione clinica-vs-imaging emersa in H (Bisogno 2025 vs Cinetto): i cluster anatomici/SDC aggiungono valore incrementale ai soli dati clinico-demografici, o no? |
| 8. EEG (n~80, Padova) | Task 4 | TBD | — | — | Deferred a settembre/ottobre 2026 |

---

# Workflow discorsivo

Il punto di partenza è la constatazione (base fondante, sezione A) che lesione e SDC non sono ridondanti tra loro, e che entrambe si lasciano comprimere in spazi a bassa dimensionalità senza perdere informazione clinicamente utile (sezione B). Questo giustifica l'impianto a doppio binario del workflow grafico sopra: lesione e SDC vengono ridotte ed embeddate separatamente, clusterizzate separatamente, e solo dopo confrontate.

1. **Embedding + clustering lesioni (Task 1)**. Punto di partenza naturale perché è la modalità con la N più alta (~5750, potenzialmente) e la più matura nella pipeline attuale (`dim_reduction`/`clustering`, atlante combinato Glasser+HO già pronto). L'obiettivo qui non è solo descrittivo: verificare se i cluster lesionali replicano una segmentazione essenzialmente vascolare (come atteso da Thiebaut de Schotten 2020) o se emergono raggruppamenti che il solo territorio arterioso non spiega — questo è già di per sé un primo test della Domanda 2 (fenotipi generalizzabili).
2. **Embedding + clustering SDC (Task 2)**, appena `compute_sdc.py` avrà prodotto un batch reale sul cluster (dipendenza bloccante, vedi "Prossimi passi"). Stessa logica del punto 1, ma sullo spazio di disconnessione.
3. **Confronto cluster lesione vs SDC** (ARI/NMI/contingency table): è il primo risultato realmente originale del progetto rispetto alla letteratura raccolta. L'intuizione di partenza (Seba_Meeting_1: lesioni topograficamente diverse possono condividere lo stesso streamline disconnesso, quindi finire nello stesso cluster SDC pur avendo cluster lesionali diversi) va qui trasformata in una misura quantitativa.
4. **Estensione funzionale (Task 3)**, sul sottoinsieme con fMRI (~500, WU+PD+Friburgo). Per ciascun cluster anatomico (lesione o SDC), si descrive la FC media dei soggetti che vi appartengono, mascherata sull'estensione lesionale (Siegel 2016, già implementato) e confrontata con la norma sana tramite z-score per soggetto (richiesta esplicita di Corbetta in meeting). Questo è il passaggio che permette di rispondere al goal di Seba_Meeting_2: dato un cluster anatomico, quale fingerprint funzionale gli si può associare — utile in particolare per i soggetti privi di fMRI diretta, che sono la maggioranza della coorte totale.
5. **Feature locali vs. globali (Task 3, in parallelo al punto 4)**. Qui entra il catalogo di Volpi 2024/2025 (ReHo, ALFF, ampiezza/covarianza, GFC media/varianza): non testato finora su una coorte stroke, ma un candidato naturale per rispondere alla Domanda 3 (locale vs. globale), esplicitamente aperta da Corbetta.
6. **Correlazione con l'outcome clinico (Task 5)**: validazione dei cluster (anatomici, SDC, e — se emergono — funzionali) contro le variabili cliniche disponibili (NIHSS e subitem, domini comportamentali dove presenti), con lo schema statistico già validato in letteratura da Zanola 2026 per problemi analoghi (cluster su dato continuo → validazione con variabili esterne non usate nel clustering).
7. **EEG (Task 4)**: deferred, nessun'azione richiesta ora.

Questo ordine non è vincolante: è pensato per essere aggiornato via via che SDC reale, feature funzionali su scala e nuova letteratura diventano disponibili.

---

# Domande aperte / tensioni da portare al gruppo

- Estendere la rassegna oltre i paper già raccolti nella cerchia NEMESIS (TODO esplicito, `Corbetta_Meeting_1`), in particolare cercando lavori di **clustering longitudinale** (es. Fallani, citato a meeting) e letteratura recente su fingerprinting/z-score individuale.
- Longitudinale non ancora mappato: non è chiaro quali dataset abbiano più timepoint e a quali distanze (2 settimane? 3 mesi? 1 anno?) — condiziona sia il disegno di Task 3/5 sia il confronto con Santoro 2026/Siegel 2018/Pini 2026, che sono tutti longitudinali.
- Armonizzazione tra scanner (neuroCombat, `Seba_Meeting_2`): necessaria almeno per WashU ST vs HC (scanner diversi); da verificare se serve anche per gli altri dataset multi-sito una volta aggregati.
- Standard di parcellizzazione da adottare: Yan200/Tian S2/Buckner in spazio fMRIPrep (`Seba_Meeting_3`, per le feature funzionali) vs. l'atlante combinato Glasser+HarvardOxford già implementato per le lesioni — va capito se servono due atlanti per due scopi diversi o se conviene armonizzare.
- Feasibility del numero target di fenotipi funzionali (4-5, `Seba_Meeting_2`) — dichiarato come da validare, non un vincolo.
- Radar/spider plot per centroide di lesione (metriche + connettività + demografici + score clinici), richiesto in `Seba_Meeting_2`: non ancora implementato, utile come strumento di comunicazione per il progress report.
- La tensione clinica-vs-imaging (sezione H: Bisogno 2025 vs Cinetto) non è risolta in letteratura — va trattata come domanda empirica da testare sui nostri dati, non come assunzione di partenza.

---

# Prossimi passi immediati (in vista del progress report)

- Eseguire un primo giro end-to-end di embedding+clustering lesioni (Task 1) su un sottoinsieme già disponibile localmente, per avere un primo risultato preliminare mostrabile.
- Sbloccare Task 2 lanciando `compute_sdc.py` su un batch reale sul cluster (attualmente non testabile in locale, richiede `bcblib`).
- Validare i cluster lesionali preliminari contro variabili esterne disponibili (lato, volume, NIHSS) con lo schema di Zanola 2026, come primo controllo di sanità.
- Una volta disponibile la SDC reale, avviare il confronto cluster lesione vs SDC (fase 3 del workflow discorsivo).
- Portare al gruppo le tensioni/domande aperte elencate sopra, in particolare l'estensione della rassegna e la mappatura del longitudinale. 

