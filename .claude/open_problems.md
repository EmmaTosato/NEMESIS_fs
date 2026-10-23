# Problemi aperti e cose da fare — NEMESIS

Ultimo aggiornamento: 23-10-26 (lateralità tutta geometrica; guida del pannello «Clustering evaluation» da riscrivere).

Elenco vivo di ciò che è **aperto adesso**: problemi noti non risolti, decisioni non prese, lavori iniziati e non finiti. Una voce si cancella quando è chiusa — non si tiene lo storico qui.

**Dove va invece il resto**: cosa è già implementato → `README.md`; stato tecnico corrente → `.claude/stato_progetto.md`; perché una decisione è stata presa così → `.claude/history/`; risultati di un esperimento → `docs/experiments/`.

---

## 🔴 Problemi di dati

### Maschere PSP frazionarie (non binarie)

Le 168 maschere `UNIPD/PSP` hanno valori tra 0 e 1 (multipli di 1/8) invece di solo 0/1: sono maschere a 2 mm interpolate linearmente a 1 mm. Gli altri 7 dataset sono binari.

- **A 1 mm** (le 4 colonne `_1mm` di `lesion_metadata.csv`): `> 0,5` scarta i voxel da 0,5 esatto, quindi il volume è 0,83 volte il vero (mediana). Nessuna soglia lo ripara: a 1 mm l'informazione non c'è.
- **A 2 mm** (produzione, matrici lesionali): corretto, `nearest` ricostruisce la maschera originale.
- **SDC**: BCBToolKit ha ricevuto la mappa frazionaria (`map_min_nonzero = 0,125`). Non si sa se la binarizzi o usi pesi continui; se binarizza, la lesione effettiva di PSP differisce da quella degli altri dataset.

**Da fare**: verificare sul cluster come `bcb-lf-preprocess` (bcblib 0.6.1) tratta una mappa non binaria; errore esplicito sulle maschere non binarie (`code_standards.md` §0); chiedere gli originali a 2 mm.

### Lato clinico e maschera opposti in 11 soggetti WashU: la maschera è probabilmente capovolta in 6, lasciata com'è nelle matrici

**Fatti.** In WashU 11 soggetti su 162 con un lato clinico (6,8%) hanno il `lesion_side` opposto alla maschera: 6 `left`→`right` e 5 `right`→`left`, tutte inversioni piene (`|laterality_index_2mm| ≥ 0,95`, lesione tutta dall'altra parte). L'header delle 195 maschere è identico (RAS, stessa affine). Il disaccordo è associato alla manualità: mancini 5/16 (31%), destrimani 6/146 (4%), Fisher p = 0,0016.

**Perché crediamo che in 6 casi sia la maschera, non l'etichetta clinica, a essere sbagliata (06-10-26).** Senza T1 locali, il lato si verifica con un metodo indipendente dall'immagine: un deficit motorio da ictus colpisce l'arto **controlaterale** alla lesione, quindi il braccio/mano più deficitario in `ARAT_L/R` e `9HPT_L/R` (tsv) indica il lato della lesione a prescindere da qualunque maschera.

- *Calibrazione del metodo*: sui 151 WashU dove etichetta e maschera già concordano (quindi il lato vero è noto), `ARAT` indica il lato giusto nel 98% (90/92), `9HPT` nell'86% (102/119) — questa è la sola fonte d'errore del test stesso.
- *Applicato agli 11 discordi*: almeno un test è informativo in 8 casi. In **6** (`sub-STUNIPD0002`, `0026`, `0056`, `0077`, `0147`, `0222`) il lato indicato dal test coincide con l'**etichetta clinica**, non con la maschera — quindi è la maschera a essere capovolta. In **2** (`0008`, `0179`) è il contrario: coincide con la **maschera**, quindi è l'etichetta a sbagliare. Non decidibili: `0131`, `0151`, `0187`.
- *Forza della prova*: sul solo 9HPT, 5 dei 6 casi WashU informativi indicano l'etichetta. Se la maschera fosse quella giusta (quindi il test dovrebbe sbagliare), vedere questo risultato per caso — dato l'86% di accuratezza di base del test — ha probabilità ≈ 3×10⁻⁴ (assumendo indipendenza tra soggetti). È un'evidenza, non una conferma radiologica: nessuna T1 è stata guardata direttamente per questi 6.
- *Segnale di contorno*: l'associazione con la manualità (mancini 31% vs destrimani 4% di disaccordo) è compatibile con un errore di lato commesso più facilmente su un soggetto codificato come mancino, non con un artefatto di scanner o di geometria (che non dovrebbe distinguere per manualità). Metodo e numeri completi in `.claude/history/methods_changelog.md` (06-10-26).

**Decisione (A, 06-10-26): non si interviene sui dati.** `participants.csv` riporta per gli 11 il lato clinico (`lesion_side_source = "clinical"`, forzatura geometrica spenta — `geometric_override_datasets: []` in `config/pipelines/enrich_metadata.json`). Le maschere restano quelle che sono nelle matrici di produzione (lesione voxel-wise, SDC), comprese le 6 probabilmente capovolte: nessuna esclusione, nessuna correzione geometrica. Motivo: un'inferenza comportamentale, per quanto forte (p ≈ 3×10⁻⁴), non è una conferma diretta sull'immagine — correggere o escludere sulla base di un'inferenza sposterebbe il problema (rischio di agire sui soggetti sbagliati) senza risolverlo. Resta un limite noto, documentato qui, non un'azione sui dati.

**Controlli sulle immagini (06-10-26)**: nelle immagini dei WashU la lesione nativa e la maschera MNI stanno dallo stesso lato, quindi la normalizzazione non inverte; nessuna proprietà degli header delle T1 native (orientamento, software, scanner) distingue gli 11 da 20 controlli concordi; il contrasto maschera/specchio sulla T1 non discrimina (controlli e disaccordi sovrapposti). Le maschere locali non sono le `manual_masks` del server: sono l'output SDC (1 mm), mentre il server ha le originali sul reticolo a 2 mm (circa un ottavo dei voxel).

**Controlli E e F (06-10-26), estesi a tutti i soggetti con entrambe le maschere**: il passaggio SDC inverte il lato, ma raramente e **non per nessuno degli 11 WashU in disaccordo** — WashU 1/195 (`sub-STUNIPD0094`, non tra gli 11), UKLFR 3/673 (`sub-STUKLFR0253`, `0403`, `0463`; include il `sub-STUKLFR0403` già trovato a campione), PSP 0/168, PASPORT 0/83; UKE 0 soggetti con entrambe le maschere disponibili sul server. Le sette T1 WashU con `AcquisitionTime` identico (`0222`, `0179`, `0187`, `0216`, `0233`, `0242`, `0251`) **non sono la stessa immagine**: fanno parte di un gruppo di 104 soggetti con un timestamp placeholder condiviso nel JSON, ma dati anatomici tutti distinti (md5 e contenuto diversi a coppie). Trovate invece, per caso, due coppie di T1 WashU realmente identiche byte per byte con `lesion_roi` diverso: `sub-STUNIPD0053`/`0060` e `sub-STUNIPD0066`/`0077` — `0077` è uno degli 11 in disaccordo. Non verificato se sia uno scambio di identità tra soggetti o un placeholder riusato quando lo scan originale manca.

**Aperto**:
- le due coppie di T1 WashU duplicate byte per byte (sopra), in particolare quella che coinvolge `0077`: scambio di soggetto o placeholder?
- quante maschere capovolte sono oggi nelle matrici: almeno 6 su 162 WashU con etichetta (3,7%); sconosciuto tra i 33 WashU senza etichetta clinica, dove la geometria è l'unico dato e non c'è modo di applicare la verifica comportamentale;
- il meccanismo dell'inversione resta senza causa nota: esclusi normalizzazione, header T1, passaggio SDC (controllo E) e T1 duplicate (controllo F, tranne `0077`); la manualità resta un indizio statistico, non un meccanismo — tra i 4 mancini decidibili 2 hanno l'etichetta giusta e 2 la maschera.

### Maschere a 1 mm di WashU/UKLFR: ricampionamenti delle originali, con offset di 0,5-1,2 mm in y/z e volume cambiato

Le maschere locali dei dataset con header RAS −90 (UKE/SFB936, UKLFR, NEMESIS_T0, WashU: 1032) non sono le `manual_masks` originali: le originali di WashU stanno a 2 mm e quelle di UKLFR a 1,5 mm, entrambe LAS +90 (griglia FSL standard); le locali sono a 1 mm, RAS −90, e provengono dalla copia `lesion` usata come input da BCBToolKit (`.claude/history/data_changelog.md`, 23-09-26 e 03-09-26: da verificare per ciascun dataset). Confronto dei baricentri in coordinate mondo, locale meno originale, riferito dall'agente sul cluster (non rieseguito qui):

| Dataset | n | x (mm) | y (mm) | z (mm) | volume locale/originale |
|---|---|---|---|---|---|
| WashU | 195 | mediana +0,05 (sd 0,98) | −0,51 | −1,22 | 1,09 |
| UKLFR | 672 | mediana −0,76 (sd 4,0) | +0,57 | +1,20 | 0,85 |

Per PASPORT e PSP (gruppo LAS +90, originali già a 1 mm) la differenza è 0,000 su tutti i soggetti. Un header RAS −90 che spostasse l'anatomia di 1 mm in x darebbe una mediana vicino a ±1: per WashU è +0,05, quindi **nessuna traslazione di 1 mm in x** rispetto all'originale (errore standard della mediana stimato intorno a 0,1 mm, assumendo distribuzione circa normale). Le differenze in y/z e di volume non sono una traslazione costante e sono compatibili con un ricampionamento da griglia più grossa. T1 in MNI non esistono per nessun gruppo, né trasformazioni native→MNI: il controllo su anatomia non è eseguibile.

Effetto: a 2 mm (griglia di produzione) la maschera ricostruisce esattamente l'originale per i dataset a reticolo 2 mm (`docs/guides/datasets.md`); a 1 mm le frazioni di sede e `lesion_volume_voxels_1mm` risentono del ricampionamento. Per la sede della lesione si usa la griglia a 2 mm, con 1 mm come controllo (`docs/dev/metadata.md`, sezione "La sede della lesione"). Non misurato: lo spostamento della sede dovuto al ricampionamento a 1 mm, perché le originali a 2 mm non sono in locale (il confronto 1 mm contro 2 mm della stessa maschera locale non lo vede).

### Soglie per la classificazione della lesione per sede

Quota minima della lesione in una categoria per dirla "coinvolta" e per dirla "pura" contro "mista": non decisa, la letteratura non ha uno standard per questa quantità. La sweep sull'intera coorte (5845 lesioni, 2 mm) non mostra nessun plateau per "pura" (da 93,5% a t=0,5 a 24,6% a t=0,9) e conferma che "coinvolta" a >0 è instabile; proposta provvisoria invariata: coinvolta a >10%. Numeri in `.claude/history/methods_changelog.md` (07-10-26).

**Sovrapposizione corticale/bianca di HO**: decisa il 07-10-26, i voxel in disaccordo sono una categoria a parte (`cortex_white_boundary`, nessuna precedenza; `.claude/history/methods_changelog.md`). Aperto: se "corticale coinvolta" si dichiara in versione stretta (solo corteccia sicura) o larga (con il confine), da decidere con le soglie; per questo si misura quante lesioni cambiano tra le due versioni. Layout in `lesion_metadata.csv` (solo 2 mm, `docs/dev/metadata.md`) implementato in `compute_lesion_metadata`; la regola per la parità nell'etichetta prevalente (vince la prima categoria nell'ordine) è una convenzione, non confermata. Altri punti aperti dalla coorte: le 18 discordanze tra lato dell'atlante e `lesion_side_2mm` non sono esaminate; perché UKLFR e PASPORT non abbiano quasi lesioni infratentoriali (0,1% / 0% a >10%) non è verificato; le 27 lesioni con categoria dominante "non etichettato" (17 UCL-UK, 9 WAKEUP, 1 PSP) e le 121 con >20% non etichettato non sono ispezionate.

### Colonne `NIHSS_5a/5b` di UKLFR probabilmente scambiate

Nel tsv UKLFR il braccio più deficitario corrisponde alla lesione **omolaterale** (75/75 sui soggetti con asimmetria: braccio "a" peggiore → lesione sinistra, "b" peggiore → destra), il contrario dello standard NIHSS (5a sinistro, 5b destro). Verificato solo per 5a/5b, non per 6a/6b. Nessun codice del repo usa questi item oggi (solo il `NIHSS` totale); conta se qualcuno li usa.

### `sub-STUKLFR0671`: SDC vuoto con lesione grande

Nella matrice `sdc_matrix` s2.2-vol questo soggetto è una riga interamente nulla. La causa è a monte: la sua mappa `disconnectome-map` ha **0 voxel non nulli** pur avendo una lesione da **56.785 voxel**. Output degenere di BCBToolKit, non una proprietà del soggetto.

Aggiornamento della verifica del 23-10-26: oggi la maschera di lesione di questo soggetto ha **0 voxel non nulli** (header, `mapstats.tsv` di BCBToolKit, `lesion_metadata.csv`, `excluded_subjects.csv`). I 56.785 voxel (qui, in `docs/experiments/s2.2-vol.md:25` e in `data_changelog.md:143`) sono stati misurati il 07-09-26 su una maschera sostituita il 23-09-26. Non è deciso se la maschera attuale è vuota per errore (rsync, versione diversa) o se quella del 07-09 era sbagliata; da questo dipende se il disconnettoma vuoto è un output degenere di BCBToolKit o il risultato corretto di una lesione vuota.

Unico caso su 1570. Per risolverlo va rilanciato il calcolo SDC (BCBToolKit) per quel soggetto, **che gira solo sul cluster** (la pipeline `compute_sdc.py` è stata ritirata da questo repo). Nel frattempo va escluso a valle.

### `mask_summary.csv` di WashU non descrive i file che hanno alimentato la matrice FC

Per l'atlante `Yan200TianS2Buckner7N` esiste una sola run di `mask_fc.py` (24-07, `masked_fc/runs.csv`) e una sola matrice costruita da essa (`fc_matrix/24-07_s3.1-Yan200TianS2Buckner7N`, 24-07). Ma `mask_summary.csv` ha data 02-09, mentre i CSV mascherati ancora presenti in `masked_fc/` sono del 24-07. Sui 10 soggetti locali, il numero di nodi con riga interamente NaN nei CSV mascherati coincide con i nodi compromessi del summary per 7 soggetti (0002, 0003, 0008, 0011, 0012, 0013, 0014) e non coincide per 3 (0005: 3 contro 2; 0006: 10 contro 9; 0009: 2 contro 0). Il confronto nodi compromessi contro NaN di `fc_analysis.ipynb` mescola quindi due stati dei dati.

Rilettura del 23-10-26 su tutta la combinazione: per 52 soggetti su 169 `n_compromised_nodes` del summary è inferiore ai nodi realmente mascherati in `matrix.npy` (esempi: `sub-STUNIPD0005` 2 contro 3, `sub-STUNIPD0009` 0 contro 2); la formula k(N−1) − k(k−1)/2 torna con la matrice (238 e 711 NaN per N=239), non con il summary. Le cifre «mediana 1 nodo, media 3,9» (`fc_lesion_masking.md`, `fc_analysis.ipynb`) e la decisione «nessuna soglia di esclusione» poggiano sul summary; dalla matrice la mediana è 2 e la media 4,4. Lo scatter di `fc_analysis.ipynb` mostra 52 punti fuori dalla relazione teorica che sono un artefatto del disallineamento.

Decisione dell'utente (21-10-26): **non** rilanciare `mask_fc.py` per ora. Non è stata verificata la causa della discrepanza; un rilancio di `mask_fc.py` e `build_fc_matrix.py` allineerebbe summary e matrice.

## 🟡 Lavori da fare

### Lateralità: calcolarla tutta dalla maschera (geometrica), non tenere il lato clinico del tsv

**Decisione (23-10-26, da implementare)**: `lesion_side` va calcolato per **tutti** i soggetti dalla maschera (indice di lateralità geometrico), senza conservare il lato clinico del tsv dove esiste. Oggi il registro tiene il valore clinico e usa quello geometrico solo per riempire le celle vuote (`lesion_side_from`, `lesion_side_source`).

- **Perché**: una sola definizione per tutta la coorte, calcolata allo stesso modo ovunque. Il lato clinico esiste solo per ~1445 soggetti, ha un significato diverso (il `both` clinico non coincide con una maschera bilaterale) e per WashU è in disaccordo con la maschera in 11 soggetti su 162.
- **Da fare**: togliere la precedenza al clinico in `enrich_metadata` (`lesion_side_from` scrive sempre, `geometric_override_datasets` e la distinzione `clinical`/`geometric` in `lesion_side_source` perdono senso), aggiornare `docs/guides/metadata.md`, `docs/dev/metadata.md` e `lesion_laterality.md`, rigenerare `participants.csv`.
- **Legame con la voce WashU** (sopra): la decisione A («`participants.csv` riporta il lato clinico per gli 11») viene superata. Le 6 maschere probabilmente capovolte restano un limite noto: con il lato geometrico il `lesion_side` di quei soggetti segue la maschera, non l'etichetta clinica.
- **Da decidere**: soglia per `both` sull'indice di lateralità (oggi non c'è un valore che riduca la differenza col `both` clinico, vedi `knowledge/notes/neuroimaging/lesion_laterality.md`).

### Sede della lesione: ricategorizzare l'etichetta «cortex»

**Da fare (23-10-26)**: rivedere come l'etichetta corticale entra nelle categorie di sede. Oggi `cortex_only` e `cortex_white_boundary` (i voxel in cui i due atlanti Harvard-Oxford, corticale e «Cerebral White Matter», si sovrappongono) sono due categorie separate (`src/features/lesion_location.py`), e i voxel con la sola etichetta `Cerebral Cortex` dell'atlante sotto-corticale finiscono in `unlabeled` (7.862 dei 15.409 voxel `unlabeled` a 2 mm, `docs/dev/metadata.md`).

- **Non ancora deciso**: la nuova ripartizione (per esempio fondere o spostare `cortex_white_boundary`, assegnare a `cortex_only` i voxel `Cerebral Cortex` oggi `unlabeled`).
- **Legame**: la scelta stretta/larga di «corticale coinvolta» nella voce sulle soglie di sede (sopra) e le colonne `location_cortex_*` di `participants.csv`. Una ricategorizzazione cambia `lesion_metadata.csv`, `participants.csv`, i colori dell'app (`embedding_coloring.py`) e `cluster_pair.py`.

### Tuning del clustering: cosa resta dopo il registro delle valutazioni

Fatto (21-10-26): blocco `tuning_evaluations` nel config, registro in `src/analysis/clustering_tuning_evaluations.py`, parametri in `config/registry/clustering_evaluations.json`, stessa funzione nello sweep e in `evaluate_clustering_tuning` (`.claude/history/project_changelog.md`). Resta:

- **Regola: tutto ciò che si fa durante lo sweep si può rifare con `evaluate_clustering_tuning.json`, e viceversa.** Le colonne che lo sweep scrive in `tuning_results.csv` si ricalcolano con la valutazione `internal_metrics` (dalle etichette salvate, solo con `overwrite: true`); lo sweep le calcola ancora da sé con le stesse funzioni.
  - Non si ricalcolano dalle etichette: `membership_mean` e `persistence_mean` di `hdbscan_soft`, che nascono dal fit (`hdbscan_soft_fit`). Nessuna valutazione le rifà.
  - In stand by, per scelta del 23-10-26 (non si toccano finché la catena non è chiusa per agglomerative, hdbscan e hdbscan_soft): la regola vale per agglomerative e HDBSCAN; kmeans, gmm, spectral e adp scrivono nello sweep colonne (`inertia`, `bic`/`aic`, ...) che nessuna valutazione ricalcola.
  - `k_curves` di agglomerative legge `silhouette` e `davies_bouldin` da `tuning_results.csv`: se `internal_metrics` li riscrive, i valori nuovi arrivano alle curve solo con `internal_metrics` dichiarata prima.
- agglomerative: `dunn_index` e `largest_cluster_share` sono valutazioni del registro (23-10-26); la silhouette per cluster resta solo in produzione e nell'app, per scelta. Il report le legge: sono due colonne (`dunn`, `largest_cluster_share`) delle tabelle per linkage;
- **Embedding Explorer, pannello «Clustering evaluation»: la guida «How to read these indices» (`_quality_guide` in `embedding_app.py`) descrive le metriche di oggi** (silhouette nelle tre sintesi, Calinski-Harabasz, Davies-Bouldin, Dunn, grafico per cluster, i quattro limiti) **e va riscritta quando la scelta delle metriche è fatta**; stessa sorte per la guida di `adp` (`_adp_guide`) e per la tabella degli indici sopra. Oggi, per un run con `metric` non euclidea (es. cosine), il pannello mostra la silhouette nella metrica del run e «—» per Calinski-Harabasz, Davies-Bouldin e Dunn (come nello sweep): anche questa regola segue la scelta;
- i testi del report (`HINT_*`, `REPORT_TERMS`) sono costanti in `src/analysis/clustering_tuning_report.py`: farli arrivare da `docs/` e `knowledge/` perché non divergano;
- **cartelle di tuning di agosto-10 settembre senza report** (12 di agglomerative, 12 di HDBSCAN): non rigenerate, precedono la catena delle valutazioni. Le 48 cartelle con report sono state rigenerate il 23-10-26 con i flussi attuali. Restano, non toccati, i prodotti d'analisi dentro 4 cartelle di agglomerative (`composition_*`, `tracts_*`, `nb_*`, `view2d_*`, `k_table_*`: `08-10_s1.4-vol_m_dice_nc2`, `08-10_s1.4-vol_m_dice_nc10`, `08-10_s1.4-vol_m_euclidean_nc2`, `09-10_s2.4-stream`);
- il report è scritto dal codice (sweep con `write_report`, o `evaluate_clustering_tuning`), non da un notebook: `clustering_tuning_explorer` è stato eliminato il 21-10-26; ciò che provava lo si prova in `clustering_evaluation` (da spostare in `pipeline_building`) e poi entra nel registro e nel modulo del report;
- le figure delle valutazioni sono salvate a 150 dpi (`FIGURE_DPI` in `clustering_tuning_evaluations.py`): alzare la qualità;
- la produzione e Dash con le stesse funzioni e soglie; `clustering_evaluation.ipynb` verso `pipeline_building`;
- ICL, gap statistic e self-tuning eigengap sono nello stesso modulo di `clustering_tuning.py` ma senza una valutazione nel registro (si recuperano da `46c3123`).

### Modello nullo per la silhouette dei report di tuning del clustering

Il report di agglomerative documenta la silhouette con il valore per combinazione e con la curva su `n_clusters`. Un riferimento nullo darebbe un punto di confronto che non dipende da soglie: quale silhouette produce lo stesso clustering, con gli stessi parametri, su dati senza struttura. **Non è deciso come costruirlo**; due candidati misurano cose diverse:

- **Etichette permutate** (stesse dimensioni dei cluster, assegnazione casuale): dà la silhouette di una partizione a caso, vicina a 0 o negativa per costruzione. Non dice cosa fa l'algoritmo su dati senza struttura.
- **Clustering rifatto su dati senza struttura** (ad esempio colonne dell'embedding permutate in modo indipendente, o campioni gaussiani con la stessa covarianza): l'algoritmo trova comunque dei cluster, e la silhouette risulta positiva. È il riferimento più vicino alla domanda, ma costa un tuning per ogni riferimento e dipende da come si genera il dato nullo.

Da decidere: quale dei due (o un altro), se si applica anche a Davies-Bouldin e Calinski-Harabasz, e come si tiene conto che UMAP stesso produce blob compatti.

### Cosa aggiungere ai report di tuning di agglomerative, oltre alle tabelle degli indici

Fuori dal primo giro di implementazione (19-10-26), da riprendere dopo aver deciso come leggere dendrogramma, cophenetic e salto:

- **Dimensioni dei cluster nelle tabelle**: `largest_cluster_share` e `n_small_clusters` (meno di 10 soggetti, la definizione già usata da HDBSCAN e ADP in `clustering_tuning_analysis.py` e `adp.py`) non sono calcolati per agglomerative. Sulla run SDC `16-10 nc10` la quota del cluster più grande va, con euclidean, dal 64-70% a k=2 al 7-8% a k=30; `single` ha il 97% a k=2 e 20 cluster sotto l'1% a k=30.
- **Scree plot**: altezza di fusione contro k. Oggi c'è solo il rapporto in `dendrogram_jump.csv`.
- **Dimensione del cluster che si divide da k a k+1**: non esiste nel codice.
- **Accordo tra embedding** (ARI tra nc2, nc3 e nc10, a parità di k e linkage): esiste solo in `src/analysis/cluster_comparison.py` (il notebook `clustering_tuning_explorer`, eliminato il 21-10-26, lo calcolava anche per i tuning) (sezione "Confronto" tolta dall'app); confronta più run, quindi non entra nel `report.md` di una singola run.
- **Composizione dei cluster per dataset e lato**: esiste in `src/analysis/cluster_composition.py` e nel pannello dell'app, non nei report.
- **Dove riprodurre dendrogrammi, matrice interclasse e `labels_2d_*`**: li scrive `clustering.py`, non `evaluate_clustering_tuning`; il report non li cita.

---

### Documentazione e notebook: cosa resta aperto dopo il giro del 21-10-26

Il giro ha allineato docs, note e notebook alla regola «il markdown di un notebook non è fonte di informazione nuova». Restano questi punti.

**Verifiche non fatte**
- **Verifica di contenuto del 23-10-26**: ogni file riscritto il 20-21 ottobre è stato riletto riga per riga contro codice, config, dati su disco e storico (rapporti completi in `tmp/verifica_contenuto_21_10_26/report/`, uno per lotto). Le misure ad alto rischio tornano: bcbtoolkit 8,447 GB e totale 11,85 GB, 5853 righe, 8 coorti (7 su 8 con schema normalizzato), 31 CSV (15+16) e 34 file per soggetto, reference con 232/332/432 regioni, colonne di `s2.4-vol` (227.235, 291.345, 64.110 di differenza), 42 componenti per il 90% su entrambe le matrici. Il «52 su 169» non compare in nessun file: è il numero di soggetti per cui la formula k(N−1) − k(k−1)/2 non torna tra `mask_summary.csv` e `matrix.npy` (vedi «`mask_summary.csv` di WashU» sopra).
- **Cifre di `docs/dev/covariance_pca.md` senza output salvato**: i circa 25,7 GB di memoria di `sklearn.decomposition.PCA` sul `07-10_s2.4-vol` e la correlazione 0,74-0,91 (mediana 0,84) tra mappa *t* e mappa dei pesi. I GB delle matrici (6,8 e 5,3) e delle matrici quadrate (413 e 680) tornano, in GB decimali; `max_matrix_gib` è invece in GiB.
- **Cifre delle note sul clustering non ricalcolate**: in `knowledge/notes/dim_reduction_clustering/clustering_methods/` l'84% di coppie a distanza dice 1 sulle lesioni e lo 0,0015% sulle mappe SDC (`adp.md`, `docs/guides/evaluation.md`), i 30-55 secondi per 56 combinazioni HDBSCAN (`hdbscan.md`), la quota 89% con γ=5 (`spectral.md`; per γ=0,1 e γ=1 il ricalcolo dà 7% e 66%, come scritto) e il «Silhouette Coefficient: 0.753» dell'esempio di scikit-learn (`evaluation_metrics.md`). Le fasce di Kaufman & Rousseeuw restano da fonti secondarie (libro non consultato).
- **Riferimenti a riga nel debug report**: `docs/debugging/debug_21_10_26.md` cita `src/analysis/consensus_clustering.py:260-276`, righe che esistevano al commit `0b49ccc` (276 righe) e non più dopo `1e43759` (191 righe, rimozione di Evidence Accumulation). Per un report storico è accettabile; non va riletto contro il file attuale.
- `management/cheatsheets/`: ogni numero e ogni termine tra apici delle schede di metodo compare nella nota da cui deriva, tranne i valori degli esempi giocattolo, di cui è stata controllata l'aritmetica (`adp.md`, `kmeans.md`, `pca-varimax.md`, `hdbscan.md`); per `umap.md` e `pacmap.md` sono controllati parametri e valori numerici contro le note, non ogni frase (rilettura del 23-10-26: nessuna divergenza residua per `adp.md`, `kmeans.md`, `agglomerative.md`, `pca.md`, `pca-varimax.md`). Non verificato il rimando delle schede alle sezioni di approfondimento. `clustering_metrics_report.md` è un audit dello stato precedente (soglie sparse, criterio «usabile», silhouette di HDBSCAN): non è una scheda e non è riallineato.
- **Il criterio «usabile»** (3-30 cluster, rumore ≤ 25%, cluster più grande ≤ 60%) è tolto da `docs/experiments/s2.4-vol.md`; resta in `docs/experiments/s1.4-vol.md`, `s2.4-stream.md` e nel diagramma di `docs/experiments/pipelines.md`. Le tabelle di `s2.4-vol.md` e `s1.4-vol.md` citano silhouette di tuning di HDBSCAN scritte quando la silhouette si calcolava ancora per quel metodo: sono i valori delle run di allora.
- **Valori di de Bodt et al. 2025 (Tabella 2)** citati in `dim_reduction_methods/pca.md` e `evaluation.md` (conservazione dei 10 vicini 0,02-0,04 per PCA e 0,20-0,46 per t-SNE, correlazione delle distanze 0,83-0,92): la tabella è un'immagine nella copia estratta, non verificabili dal testo; è verificato solo l'enunciato qualitativo (t-SNE migliore sul locale, PCA/MDS sul globale).
- **«42 componenti» in `pca_varimax.md` e `covariance_pca.md`**: stessa attribuzione al `07-10_s2.4-vol` già annotata sopra; il 42 è confermato solo per il `16-10_s2.4-vol`.
- `dendrogram_embedding_explorer.ipynb`: la modifica al codice (`split_at` senza `labels_previous`) non è stata provata con una riesecuzione.
- **Voci nuove di `.claude/history/` con motivazione ricavata dai vecchi docs e non dai commit**: git conferma le date e i commit, non le frasi. Riguarda `methods_changelog.md` (03-09-26 agglomerative: «ore per combinazione» con jaccard/dice è una stima non misurata; 06-09-26 SDC voxel-wise: «5 dataset, 1 mm, ribaltamenti e traslazioni intere» non riletto sugli header su disco; 29-09-26 mappe anatomiche: i prototipi `.py` di `tmp/anatomy_rendering/` esistono ancora e `renders/` contiene 72 PNG, ma non risulta quali siano le immagini di confronto citate dalla voce) e `project_changelog.md` (26-08-26 `write_embeddings_grid`: il doc dava 26-08, il commit che toglie il flag è del 27-08, tenuto 26-08 nel titolo; 29-09-26 pannello «Descrizione del cluster»; 01-09-26 palette e tag dell'embedding).
- **Design record «project-clustering-tuning-redesign»**: i docs lo citano, ma il file di memoria non esiste più. Se il design non è scritto nei docs, non è scritto da nessuna parte.
- **Non archiviati nello storico** (decisioni minori): rimozione dei `summaries/` di `dim_reduction` e `clustering` (commit `567630d`, la ragione è ancora in `docs/dev/models.md`) e `tag_param`/`tag_prefix` come liste parallele (commit `625b2c1`, la storia è nel messaggio del commit).

**Incoerenze note, da decidere**
- **`.claude/CLAUDE.md`** non contiene la regola sul markdown dei notebook; sta solo in `docs/guides/exploration.md`, «Regole di scrittura dei notebook».
- **Link a `results/legacy/`** in `docs/experiments/s2.4-vol.md`: verificato, `results/legacy/sdc_s2.4-vol_07-10/` esiste e i file linkati ci sono (`config.md`, `tuning_results.csv`). Le sole voci non risolvibili sono i pattern con `*` e le cartelle generiche scritti nel testo.

**Dubbi emersi dalla verifica di contenuto (23-10-26)**

*Dati e sessioni*
- **5150 contro 5151 maschere a reticolo 2 mm**: i cinque dataset elencati in `lesion_resampling.md` §8 sommano 4119+705+195+76+56 = 5151, `datasets.md:59` dice 5150, e le tre righe della tabella sommano 5852 su 5853. La differenza è con ogni probabilità `sub-STUKLFR0671` (maschera vuota, non classificabile): dichiararlo.
- **N1/(8·N2) di PSP**: 0,79 sul sottoinsieme «tutto dentro il cervello» (`template_and_grids.md` §10, `lesion_resampling.md` §9) e 0,83 su tutta la coorte PSP (`docs/dev/metadata.md`, `lesion_resampling.md` §13): due basi diverse nello stesso documento, da esplicitare in §13.
- **Voxel d'atlante fuori dalla maschera cerebrale a 2 mm** (6.722, di cui 540 del cervelletto): non è misurato se coincidano con voxel di lesione tagliati da `correct_out_of_brain`, cioè se la sede delle lesioni di bordo (cervelletto in particolare) sia sottostimata.
- **`bcbtoolkit/` non contiene più una mappa di lesione per soggetto** (34 file, solo il disconnettoma), ma `docs/dev/sdc_matrix.md` parla del `lesion-map` che BCBToolKit ha usato e `data/clinical_connectome/derivatives/README.md:10-13` descrive ancora la maschera come copiata da lì: allineare README e frase.
- **`docs/guides/datasets.md`**: `mapstats.tsv` pesa 3 MB, 0,036% del totale (scritto 0,03%).
- **`s2.3-stream` esiste su disco** (matrice `30-09_s2.3-stream`, 5838 × 87, UMAP nc2, circa 16 run di produzione sul grezzo) ma `README.md`, `lineage.md`, `s2.4-stream.md` e `pipelines.md` la dicono non costruita o non lanciata: documentarla (file `s2.3-stream.md`, nodi aggiornati) oppure ritirarla.
- **`s2.4-vol.md` non documenta** il t-SNE di tuning del 18-10 (anche assente in `tsne.md`), le 20 run di agglomerative del 19-10 su UMAP nc2/nc10, la PCA varimax in produzione (nc12 e nc2, 19-10) con i suoi tuning, e 2 agglomerative su PCA nc2. In `pipelines.md` (s2.4-stream) l'arco che fa discendere il clustering sul grezzo dall'UMAP «solo per la vista» non è uniforme con s2.4-vol; in `lineage.md` s1.2-vol è datata 27-07 (inizio) e le altre sessioni con la data della matrice.
- **HDBSCAN su punteggi PCA/varimax** (2-42 componenti, `results/sdc/clustering/tuning/hdbscan/pca`): verificare che `docs/guides/clustering.md` e `docs/experiments/` non lo descrivano come «solo su UMAP». Nessuna run di gmm o spectral su PCA, anche se `gmm.md` la cita come input possibile.
- **Cifre storiche «36% del cervello, fino al 91%»** in `.claude/history/methods_changelog.md` (voce 06-10-26): ricalcolate sulle 5853 mappe danno 35% e 95% (34% e 85% dentro la maschera); la voce è storica e non è stata riscritta.

*Codice (`src/`, non toccato)*
- **`tuning.py::evaluate_pca`**: la docstring dice «unchanged by a rotation», falso con `rotation_n_components` (le k ruotate tenute spiegano meno delle prime k della PCA: 0,483 contro 0,824 su dati sintetici).
- **`clustering_tuning.py`**: `_WARD_SAFE_METRICS` contiene `l2`, che scikit-learn 1.8.0 rifiuta con ward (`ValueError`); nessuna griglia lo usa. Quattro funzioni (`integrated_completed_likelihood`, `compute_gap_statistic`, `gap_statistic_suggested_k`, `compute_self_tuning_eigengap`) e `consensus_clustering.py::subsampling_stability_index` sono chiamate solo dai test: tenerle e documentarle, o cancellarle (`code_standards.md` §2).
- **Docstring e commenti obsoleti**: `evaluate_clustering_tuning.py` elenca `noise_filtered_curves[...].png` per HDBSCAN (le valutazioni scrivono `dbcv_curves*.png`); `dim_reduction.py:396-399` dice «already enriched» ma `metadata` è quello letto da `load_matrix`; `embedding_app.py` chiama «Composizione dei cluster» e «Salva PNG» i pannelli che si chiamano «Cluster composition» e «Save PNG» (file in lavorazione).
- **`clustering.py:1050` `_combo_key`** duplica `tuning_embeddings.combo_key` (la docstring cita un `_combo_key` di `dim_reduction.py` che non esiste più).
- **`raw_distances._cache_key`** campiona 64 righe su circa 5800: una modifica confinata alle altre righe darebbe una distanza stantia. Valutare un digest su tutta la matrice (1,3 GB di lettura) o la data di modifica.
- **Silhouette di agglomerative con metrica coseno/manhattan** misurata in euclidea (`SILHOUETTE_OWN_METRIC_METHODS = ("adp",)`), mentre `compute_silhouette_samples` le supporta già.
- **`report.md` linka `labels_2d_<linkage>_<metric>.png`** (`clustering_tuning_report.py:300`) che nessun codice scrive: residuo del notebook eliminato?
- **`anatomical_maps.py` non committato**: `DiscoveredFiles` e `discovered=None` sono già importati da `embedding_app.py` committato (`embedding_app.py:68`): committare i due file insieme, altrimenti HEAD non si importa.
- **Spectral su grafi non connessi**: lo sweep con `n_neighbors=10` su UMAP 2D di `s2.2-vol` dà un grafo a 4 componenti e le etichette cambiano col seme (ARI minimo da −0,02 a 0,87); la pipeline non controlla la connettività (sklearn emette solo un avviso). Decidere se registrarla in `tuning_results.csv`. Le note ora dicono che il determinismo vale solo a grafo connesso.
- **ADP**: la nota `adp.md` §2.4 descrive picchi e selle dal codice Python di DADApy 0.3.4, il progetto usa la versione Cython (`v2=False`): la selezione dei picchi non è stata confrontata riga per riga. Con `dice` saturato a 1 (84% delle coppie) i pareggi tra vicini sono molti e DADApy aggiunge rumore: non è misurato quanto pesino su densità e `id_2nn`.
- **`pca_method.py`**: il commit `0b49ccc` ha cambiato `rotation_n_components` (ora ignorato con `rotation: "none"`, prima sollevava `ValueError`) senza riportarlo in `debug_21_10_26.md`; ha anche riscritto i docstring sulla lateralità (Seghier 2008 al posto di Rorden/Gigascience) in `lesion.py` e `calibrate_lesion_side_threshold.py` senza motivarlo. Decidere se è un bug trovato dai test o una scelta da registrare in `methods_changelog.md`.

*Note, docs e storico*
- **Fonti primarie assenti da `knowledge/papers/`**: Rousseeuw, Kaufman & Rousseeuw, Caliński & Harabasz, Davies & Bouldin, Moulavi, Monti, Hubert & Arabie, Vinh, Rosenberg & Hirschberg, Jolliffe & Cadima, Kaiser, Dempster, Schwarz, Shi & Malik, Ng-Jordan-Weiss, von Luxburg, Rodriguez & Laio, d'Errico, Ward, Lloyd, Arthur & Vassilvitskii e altri: le formule delle note non sono verificabili contro il testo originale. Le più utili da aggiungere: Moulavi 2014 e Monti 2003 (reggono le metriche in produzione).
- **`evaluation_metrics.md` §§1-2** attribuisce a Dinh et al. 2025 (§4.2) e a Bicego 2021 [3, 11] l'idea che silhouette, CH e DB premino cluster compatti; i due testi dicono altro. Togliere le citazioni o trovare una fonte.
- **`clustering_metrics_report.md`** (scheda in `management/cheatsheets/`): resta un audit del 20-10-26 con note «superata» crescenti; le sezioni 3.2, 3.3, 4.3 e 5.1 descrivono un'implementazione che non esiste più per HDBSCAN. Riscriverla sul codice attuale o archiviarla.
- **`clustering_tuning_guide.md` r.30** dice che la silhouette è «l'unico dei tre con un valore assoluto interpretabile da solo», mentre la regola del progetto e `evaluation_metrics.md` §2 dicono che nessun valore è classificato in fasce e che i valori non si confrontano tra spazi. Ammorbidire.
- **ARI «sui soli soggetti non rumore»**: le note (`hdbscan.md` §6, `clustering_tuning_guide.md`) ora descrivono `agreement_metrics`, che conta il rumore come gruppo a sé; il calcolo sui soli non-rumore stava nel notebook eliminato. Decidere se reintrodurlo.
- **`clustering_comparison.ipynb`**: la Parte 2 usa `scipy.stats.chi2_contingency` (p-value, residui) sulla tabella di contingenza tra modalità: la regola «niente test statistici» è scritta per la descrizione clinica, da chiarire se vale anche qui. Il notebook è classificato «empirica» ma la Parte 2 §3 (profilo clinico) e la Parte 4 sono interpretative, e la Parte 4 usa builder parcheggiati dall'app. In `docs/guides/evaluation.md` la tabella «Scope» assegna al notebook analisi che nessun notebook implementa.
- **`dataset_availability.ipynb` cella 20**: un soggetto senza `disease_id` non entra in nessun gruppo e i conteggi WashU non sommano al totale; solo la cella 23 solleva.
- **`evaluation.md`** (`dim_reduction_methods/`): la fonte [6] (Lee & Verleysen 2009) non è citata nel testo e «Lee et al. 2015» manca dalla lista. `lesion_metrics.md` §3.3 cita [5,7] per «mascherare» il tessuto lesionato, mentre i due paper descrivono solo la sostituzione con tessuto controlaterale sano. L'indice delle schede (`management/cheatsheets/README.md`) elenca per UMAP solo `n_neighbors` e `min_dist`, ma `metric` è scelta in anticipo (`params_reduction.json`).
- **`docs/dev/models.md`**: il paragrafo «Today» di `tuning_match.py` riporta conteggi (95/82/7/6) che invecchiano a ogni run; la voce `embed` di `reduction.py` (circa 600 parole) si può spezzare in tre bullet.
- **Storico**: `lessons_learned.md` #41 è obsoleta (il notebook non ha più homogeneity e completeness scambiate) e #44 cita il §18 di `debug_21_10_26.md`, il cui controllo `sum(n) == 0` non esiste più dal commit `ea619d0`. In `debug_21_10_26.md` la criticità del §2 (media) contraddice la definizione di «alta» in intestazione e il fix del §5 è nel commit `1e43759`, non in `0b49ccc`. In `methods_changelog.md` tre voci hanno un instradamento dubbio (28-09-26 `lesion_volume_voxels`, 03-09-26 agglomerative, 29-09-26 mappe anatomiche, forse `project_changelog.md`) e gli intervalli di silhouette per rumore della voce 22-10-26 non sono ricalcolabili in modo univoco, perché i `tuning_results.csv` di `hdbscan` e `hdbscan_soft` mescolano `eom` e `leaf`.

**Notebook**
- `thiebaut_2020_replication.ipynb` ha salvato un errore alla cella 8 (`ValueError`: la cache in `results/pipeline_building/thiebaut_2020_replication/07-10_s2.4-vol` viene da un'altra matrice). È la guardia voluta del notebook; per farlo ripartire si cancella la cartella della cache oppure si imposta `USE_CACHE = False`. Non rieseguito in questo giro, e non è stato modificato. Il codice (cella 5) scrive la cache in `results/pipeline_building/thiebaut_2020_replication/<sessione>/`, come dicono `docs/dev/covariance_pca.md` e `docs/guides/exploration.md`, ma su disco la cache sta in `results/cache/thiebaut_2020_replication/` (file piatti, nessuna cartella di sessione) e `results/pipeline_building/thiebaut_2020_replication/` non esiste: da decidere se spostare la cache o cambiare il codice.
- `fc_analysis.ipynb` non è stato rieseguito: il confronto nodi compromessi contro NaN dipende dal problema `mask_summary.csv` descritto più su.
- In `dim_reduction.ipynb` la metrica del test rapido è `jaccard`, che non è nella griglia attuale del registro (`dice`, `euclidean`); resta supportata. L'import `plot_tuning_curve` non è usato.
- In `sdc_analysis.ipynb` le stringhe di `print` della cella 5 dicono «ammessi» mentre il testo dice «massimo ammissibile».
- Le celle markdown riscritte hanno applicato in modo non sistematico la regola dei backtick (solo per i nomi che l'utente modifica).
- I risultati delle riesecuzioni non sono stati riportati nei docs (decide l'utente quando): curva di varianza, R² e riproducibilità della replica di Thiebaut e di `pca_evaluation` per `s2.4-vol` (`docs/experiments/s2.4-vol.md`), cophenetic e ARI tra embedding del tuning explorer, conteggi di `lesion_matrix_build`, metriche descrittive di `sdc_analysis`.

## Note

- **Build SDC `s2.2-vol`**: **eseguita** il 07-09-26 — 1570 × 290940, `float32` continua, stessa griglia 2mm di s1.3-vol. Composizione ed esclusioni in `docs/experiments/s2.2-vol.md`.

- **Sezioni "Decisioni" di `s1_production.md`**: **compilate** il 07-09-26 per s1.1-vol e s1.2-vol. La decisione registrata è che *non* si sceglie un k unico: tenere aperte più granularità in parallelo è la scelta, perché nessun criterio interno converge e k va deciso insieme a `n_components`.

- **Audit naming dei plot**: **chiuso** il 07-09-26 senza rinominare niente. Inventariati tutti i nomi di file di plot prodotti: sono formalmente disomogenei (tre suffissi diversi) ma ognuno è inequivocabile dentro la propria directory, e ogni nome è referenziato in 5-15 file tra doc, test e risultati — rinominare sarebbe costo puro. La convenzione è ora scritta in `docs/dev/plotting.md` ("Naming dei file di plot") e vale per i nomi nuovi.

- **Righe tutte-zero in `s1.3-vol`** (`sub-STUKE0146`, `sub-STUKE0201`): **non** è un problema aperto — deciso il 07-09-26 di lasciarle, 2 su 5720. Documentate in `docs/experiments/s1.3-vol.md`; vanno filtrate a valle da chi ne ha bisogno, soprattutto sotto metriche binarie.
- **Branch `viz-niivue`** eliminato il 07-09-26 con i suoi 4 commit non mergeati (renderer alternativo per i pannelli di anatomia). Recuperabile da `facef6f` finché il reflog lo tiene: `git checkout -b viz-niivue facef6f`.
