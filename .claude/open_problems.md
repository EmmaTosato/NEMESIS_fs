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

Unico caso su 1570. Per risolverlo va rilanciato il calcolo SDC (BCBToolKit) per quel soggetto, **che gira solo sul cluster** (la pipeline `compute_sdc.py` è stata ritirata da questo repo). Nel frattempo va escluso a valle.

---

## Note

- **Build SDC `s2.2-vol`**: **eseguita** il 07-09-26 — 1570 × 290940, `float32` continua, stessa griglia 2mm di s1.3-vol. Composizione ed esclusioni in `docs/experiments/processing/matrices.md`.

- **Sezioni "Decisioni" di `s1_production.md`**: **compilate** il 07-09-26 per s1.1-vol e s1.2-vol. La decisione registrata è che *non* si sceglie un k unico: tenere aperte più granularità in parallelo è la scelta, perché nessun criterio interno converge e k va deciso insieme a `n_components`.

- **Audit naming dei plot**: **chiuso** il 07-09-26 senza rinominare niente. Inventariati tutti i nomi di file di plot prodotti: sono formalmente disomogenei (tre suffissi diversi) ma ognuno è inequivocabile dentro la propria directory, e ogni nome è referenziato in 5-15 file tra doc, test e risultati — rinominare sarebbe costo puro. La convenzione è ora scritta in `docs/dev/plotting.md` ("Naming dei file di plot") e vale per i nomi nuovi.

- **Righe tutte-zero in `s1.3-vol`** (`sub-STUKE0146`, `sub-STUKE0201`): **non** è un problema aperto — deciso il 07-09-26 di lasciarle, 2 su 5720. Documentate in `docs/experiments/processing/matrices.md`; vanno filtrate a valle da chi ne ha bisogno, soprattutto sotto metriche binarie.
- **Branch `viz-niivue`** eliminato il 07-09-26 con i suoi 4 commit non mergeati (renderer alternativo per i pannelli di anatomia). Recuperabile da `facef6f` finché il reflog lo tiene: `git checkout -b viz-niivue facef6f`.
