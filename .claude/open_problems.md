# Problemi aperti e cose da fare — NEMESIS

Ultimo aggiornamento: 06-10-26.

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

### Lato clinico e maschera opposti in 11 soggetti WashU: spesso è la maschera a essere capovolta

**Fatti.** In WashU 11 soggetti su 162 con un lato clinico (6,8%) hanno il `lesion_side` opposto alla maschera: 6 `left`→`right` e 5 `right`→`left`, tutte inversioni piene (`|laterality_index_2mm| ≥ 0,95`, lesione tutta dall'altra parte). L'header delle 195 maschere è identico (RAS, stessa affine). Il disaccordo è associato alla manualità: mancini 5/16 (31%), destrimani 6/146 (4%), Fisher p = 0,0016.

**Verifica indipendente (06-10-26).** Senza T1 locali, il lato si controlla con deficit controlaterali: `ARAT_L/R` e `9HPT_L/R` del tsv (sui 151 concordi indicano il lato giusto nel 98% e nell'86%). Sugli 11 i test sono informativi in 8: **etichetta giusta, quindi maschera capovolta, in 6** (`sub-STUNIPD0002`, `0026`, `0056`, `0077`, `0147`, `0222`); **maschera giusta, quindi etichetta sbagliata, in 2** (`0008`, `0179`); non decidibili `0131`, `0151`, `0187`. Metodo e numeri in `.claude/history/methods_changelog.md` (06-10-26).

**Cosa vale oggi**: la forzatura del lato geometrico è **spenta** (`geometric_override_datasets: []` in `config/pipelines/enrich_metadata.json`, 06-10-26): `participants.csv` riporta per gli 11 il lato clinico (`lesion_side_source = "clinical"`). Le maschere restano quelle che sono, nelle matrici.

**Controlli sulle immagini (06-10-26)**: nelle immagini dei WashU la lesione nativa e la maschera MNI stanno dallo stesso lato, quindi la normalizzazione non inverte; nessuna proprietà degli header delle T1 native (orientamento, software, scanner) distingue gli 11 da 20 controlli concordi; il contrasto maschera/specchio sulla T1 non discrimina (controlli e disaccordi sovrapposti). Le maschere locali non sono le `manual_masks` del server: sono l'output SDC (1 mm), mentre il server ha le originali sul reticolo a 2 mm (circa un ottavo dei voxel). Per `sub-STUKLFR0403` la maschera manuale del server è a sinistra (come etichetta e afasia) e quella derivata dall'SDC, che usiamo, a destra: un caso in cui il passaggio SDC inverte il lato. Sette soggetti WashU (`0222`, `0179`, `0187`, `0216`, `0233`, `0242`, `0251`) hanno la T1 nativa con identici `AcquisitionTime`, orientamento DICOM e scanner: probabilmente la stessa immagine assegnata a più soggetti.

**Aperto**:
- confronto sistematico tra maschera manuale del server e maschera derivata dall'SDC su tutti i soggetti, per sapere in quanti casi il passaggio SDC inverte il lato (controllo E);
- verificare se le 7 T1 con la stessa acquisizione sono lo stesso file (controllo F);
- le maschere capovolte, qualunque ne sia l'origine, entrano nelle matrici (lesione voxel-wise, SDC): almeno 6 su 162 WashU con etichetta (3,7%); non si sa quante siano tra i 33 WashU senza etichetta clinica, dove la geometria è l'unico dato;
- il meccanismo: la manualità è un indizio, ma tra i 4 mancini decidibili 2 hanno l'etichetta giusta e 2 la maschera.

### Colonne `NIHSS_5a/5b` di UKLFR probabilmente scambiate

Nel tsv UKLFR il braccio più deficitario corrisponde alla lesione **omolaterale** (75/75 sui soggetti con asimmetria: braccio "a" peggiore → lesione sinistra, "b" peggiore → destra), il contrario dello standard NIHSS (5a sinistro, 5b destro). Verificato solo per 5a/5b, non per 6a/6b. Nessun codice del repo usa questi item oggi (solo il `NIHSS` totale); conta se qualcuno li usa.

### `sub-STUKLFR0671`: SDC vuoto con lesione grande

Nella matrice `sdc_matrix` s2.2-vol questo soggetto è una riga interamente nulla. La causa è a monte: la sua mappa `disconnectome-map` ha **0 voxel non nulli** pur avendo una lesione da **56.785 voxel**. Output degenere di BCBToolKit, non una proprietà del soggetto.

Unico caso su 1570. Per risolverlo va rilanciato il calcolo SDC (BCBToolKit) per quel soggetto, **che gira solo sul cluster** (la pipeline `compute_sdc.py` è stata ritirata da questo repo). Nel frattempo va escluso a valle.

---

## Note

- **Build SDC `s2.2-vol`**: **eseguita** il 07-09-26 — 1570 × 290940, `float32` continua, stessa griglia 2mm di s1.3-vol. Composizione ed esclusioni in `docs/experiments/processing/matrices.md`.

- **Sezioni "Decisioni" di `s1_production.md`**: **compilate** il 07-09-26 per s1.1-vol e s1.2-vol. La decisione registrata è che *non* si sceglie un k unico: tenere aperte più granularità in parallelo è la scelta, perché nessun criterio interno converge e k va deciso insieme a `n_components`.

- **Audit naming dei plot**: **chiuso** il 07-09-26 senza rinominare niente. Inventariati tutti i nomi di file di plot prodotti: sono formalmente disomogenei (tre suffissi diversi) ma ognuno è inequivocabile dentro la propria directory, e ogni nome è referenziato in 5-15 file tra doc, test e risultati — rinominare sarebbe costo puro. La convenzione è ora scritta in `docs/dev/plotting.md` ("Naming dei file di plot") e vale per i nomi nuovi.

- **Righe tutte-zero in `s1.3-vol`** (`sub-STUKE0146`, `sub-STUKE0201`): **non** è un problema aperto — deciso il 07-09-26 di lasciarle, 2 su 5720. Documentate in `docs/experiments/processing/matrices.md`; vanno filtrate a valle da chi ne ha bisogno, soprattutto sotto metriche binarie.
- **Branch `viz-niivue`** eliminato il 07-09-26 con i suoi 4 commit non mergeati (renderer alternativo per i pannelli di anatomia). Recuperabile da `facef6f` finché il reflog lo tiene: `git checkout -b viz-niivue facef6f`.
