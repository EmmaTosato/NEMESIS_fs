# Scope dei paper per macro-categoria

### A. Framework lesione → disconnessione

| Paper                         | Scope                                                                                                                                                                                                                                                                                               |
| ----------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Thiebaut de Schotten 2020** | Dimostra che le lesioni da ictus non colpiscono il cervello a caso, ma seguono i vasi sanguigni. Usa questo per mostrare che guardare la disconnessione (non solo la lesione) spiega meglio le funzioni cerebrali, e crea un atlante che collega 590 funzioni cognitive ai fasci di materia bianca. |
| **Griffis 2019**              | Chiede se il danno alle reti funzionali dipenda dalla distruzione della materia grigia o dal taglio dei collegamenti di materia bianca. Risposta: è il taglio dei collegamenti (SDC) a spiegare meglio il problema, specialmente tra i due emisferi.                                                |
| **Griffis 2020**              | Approfondisce cosa conta come "disconnessione": non solo le fibre tagliate direttamente, ma anche i percorsi che diventano più lunghi perché una tappa intermedia è danneggiata. Entrambi i tipi peggiorano la connettività funzionale.                                                             |
| **Salvalaggio 2020**          | Mette a confronto diretto 4 modi di misurare il danno (lesione, SDC, FDC, FC reale) per vedere quale predice meglio i sintomi. Lesione e SDC funzionano bene e in modo simile; la FDC (stima indiretta della funzione) fallisce quasi sempre.                                                       |


### B. Embedding e riduzione dimensionale

| Paper            | Scope                                                                                                                                                                                                               |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Talozzi 2023** | Comprime migliaia di mappe di disconnessione in uno spazio 2D (con UMAP) e usa questo spazio compresso per prevedere i sintomi dei pazienti a 1 anno, con buona accuratezza.                                        |
| **Idesis 2023**  | Comprime la dinamica del segnale fMRI nel tempo (non lesioni) in soli 6 numeri per paziente, usando un autoencoder invece della PCA classica. Questo spazio compresso predice bene il recupero a 1 anno.            |
| **Pini 2026**    | Comprime le matrici di connettività strutturale in pochi "gradienti" principali che descrivono l'organizzazione delle fibre. Segue anche come questi gradienti e la microstruttura cambiano nel tempo dopo l'ictus. |


### C. Feature locali del segnale funzionale

| Paper          | Scope                                                                                                                                                                                                                             |
| -------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Volpi 2024** | Su persone sane, testa quali caratteristiche locali del segnale fMRI (es. ReHo, sincronia tra voxel vicini) spiegano meglio quanto glucosio consuma ogni zona del cervello.                                                       |
| **Volpi 2025** | Estende il lavoro precedente scomponendo il consumo di glucosio in due processi separati (consegna e utilizzo), mostrando che dipendono da fattori diversi. Fornisce anche un catalogo completo di 50 feature funzionali usabili. |

### D. Organizzazione globale delle reti funzionali

|Paper|Scope|
|---|---|
|**Siegel 2016**|Confronta lesione e connettività funzionale (FC) come predittori dei sintomi. Trova che ognuna delle due predice meglio domini diversi: la lesione per motorio/visivo, la FC per memoria.|
|**Corbetta 2018**|Review teorica che propone una spiegazione del perché i sintomi post-ictus si raggruppano in poche categorie: il danno riduce la modularità e la variabilità dell'attività cerebrale.|

### E. Dinamica temporale e stabilità individuale

| Paper             | Scope                                                                                                                                                                             |
| ----------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Bonkhoff 2020** | Guarda come la connettività funzionale cambia momento per momento (non solo la sua media), trovando stati diversi legati alla gravità del deficit motorio.                        |
| **Siegel 2018**   | Segue nel tempo il recupero della modularità della rete cerebrale, mostrando che questo recupero va di pari passo col miglioramento cognitivo, ma non con quello motorio.         |
| **Santoro 2026**  | Studia quanto il pattern di connettività di ogni singolo paziente resta stabile nel tempo. Trova che si stabilizza presto (3 settimane), anche se resta diverso dalla norma sana. |

### F. Evoluzione strutturale a lungo termine

|Paper|Scope|
|---|---|
|**Pini 2026** _(lato risultati)_|Mostra che la struttura della materia bianca continua a peggiorare nel tempo (degenerazione progressiva tra 2 settimane e 3 mesi), specialmente nelle zone disconnesse — in contrasto con il miglioramento funzionale (FC) documentato in lavori precedenti dello stesso gruppo (non una misura diretta di questo paper).|

### G. Struttura del comportamento

|Paper|Scope|
|---|---|
|**Corbetta 2015**|Trova che i tanti sintomi post-ictus si riducono a soli 3 fattori principali, e che la localizzazione della lesione li spiega bene per motorio/linguaggio, meno per memoria/attenzione.|
|**Bisogno 2021**|Ripete lo stesso risultato di Corbetta 2015 su un'altra coorte e con un test più rapido: la struttura comportamentale a 3 fattori si replica bene, ma la replicabilità anatomica (correlazione spaziale delle mappe di Ridge Regression con la coorte WU) è forte solo per il primo fattore (r=0.66); per gli altri due è moderata (r=0.35) o debole (r=0.11) — quindi i 3 fattori non dipendono dallo strumento comportamentale usato, ma la loro base anatomica è confermata solo parzialmente.|
|**Facchini 2023**|Trova la stessa struttura a 3 fattori anche nei tumori cerebrali, dimostrando che non è un effetto specifico della distribuzione vascolare tipica dello stroke.|

### H. Valore predittivo clinico

| Paper                      | Scope                                                                                                                                                                                                                |
| -------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Bisogno 2025**           | Confronta diversi modi di localizzare la lesione (vascolare vs reti funzionali/strutturali) per predire l'esito dopo trombectomia. Da sole, le reti funzionali/strutturali vincono nettamente sulla mappa vascolare classica; ma aggiungendo dati clinico-demografici a ciascun atlante, è proprio quello vascolare (partendo più basso) a guadagnare di più, e tutti convergono a una performance simile (R²≈0.6). |
| _(Cinetto, per contrasto)_ | Trova invece che le variabili neurologiche acute (soprattutto NIHSS) restano il predittore singolo più solido nella maggioranza dei domini/timepoint, con lesione e SDC che aggiungono solo un guadagno modesto (seppur significativo) — una domanda diversa da quella di Bisogno 2025 (clinica vs neuroimaging, non atlante vascolare vs network), ma con un esito che va nella direzione opposta sul peso relativo dell'imaging.                                                                        |

### I. Clustering di traiettorie

|Paper|Scope|
|---|---|
|**Zanola 2026**|Invece di dividere i pazienti in due categorie rigide di recupero, usa il clustering per trovare 6 traiettorie di recupero diverse, più realistiche e meno arbitrarie.|


