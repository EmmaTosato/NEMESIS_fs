# Problemi aperti e cose da fare — NEMESIS

Ultimo aggiornamento: 05-10-26.

Elenco vivo di ciò che è **aperto adesso**: problemi noti non risolti, decisioni non prese, lavori iniziati e non finiti. Una voce si cancella quando è chiusa — non si tiene lo storico qui.

**Dove va invece il resto**: cosa è già implementato → `README.md`; stato tecnico corrente → `.claude/stato_progetto.md`; perché una decisione è stata presa così → `.claude/history/`; risultati di un esperimento → `docs/experiments/`.

---

## 🔴 Problemi di dati

### Maschere PSP frazionarie (non binarie)

Le 168 maschere `UNIPD/PSP` in `manual_masks/` hanno valori tra 0 e 1 (multipli di 1/8) invece di solo 0/1; negli altri 7 dataset sono binarie (controllato su 25 file per dataset). Sono maschere a 2 mm interpolate linearmente a 1 mm: i voxel che coincidono con i centri della griglia a 2 mm valgono 0 o 1, gli altri sono medie. La somma dei valori è esattamente 8 × `lesion_volume_voxels_2mm` su tutti e 168.

**Conseguenze note**
- **Colonne a 1 mm di PSP in `lesion_metadata.csv`**: la binarizzazione `> 0,5` scarta i voxel da 0,5 esatto, quindi il volume a 1 mm è 0,83 volte il vero (mediana; da 0,34 a 0,94). Le colonne a 2 mm, la matrice lesionale di produzione e il suo volume sono corretti.
- **SDC**: le statistiche di BCBToolKit (`desc-lesion_mapstats.tsv`) hanno `map_min_nonzero = 0,125` e `n_nonzero_voxels` conta i voxel con valore > 0: BCBToolKit ha ricevuto la mappa frazionaria. **Non si sa** come la usi per la disconnessione (pesi continui, `> 0` o `> 0,5`): se binarizza, la lesione effettiva di PSP è ingrandita o rimpicciolita rispetto agli altri dataset.

**Da fare**: verificare sul cluster come `bcb-lf-preprocess` (bcblib 0.6.1) tratta una mappa non binaria; far sollevare un errore esplicito al codice per maschere non binarie (`code_standards.md` §0); chiedere gli originali a 2 mm a chi ha prodotto le maschere.

### Lato della lesione invertito in ~7% di WashU — forzato a valle, causa non verificata

In WashU **11 soggetti su 162** con un lato clinico (6,8%) hanno il `lesion_side` opposto alla maschera: 6 `left`→`right` e 5 `right`→`left`, tutte inversioni piene (`|laterality_index_2mm| ≥ 0,95`). Le 195 maschere hanno header identico (RAS, stessa affine). Negli altri dataset il tasso è quasi nullo (UKLFR 0/120, UKE 1/120, PSP 1/95, su campioni).

**Il dato arriva così dalla sorgente** (`data/clinical_connectome/metadata_tsv/participants_WashU.tsv`). Non è correggibile da questo repo.

**Cosa vale oggi**: `participants.csv` forza il lato geometrico su questi 11 (`geometric_override_datasets` in `config/pipelines/enrich_metadata.json`, `lesion_side_source = "geometric"`). Regola e conseguenze in `docs/guides/metadata.md`, motivazione in `.claude/history/methods_changelog.md` (05-10-26).

**Aperto**: la forzatura assume che sbagli l'etichetta, non la maschera, ed è un'ipotesi. Si verifica guardando la T1 di quegli 11 con la maschera sovrapposta, oppure chiedendo a chi ha curato i metadati WashU. UKE e PSP hanno un caso ciascuno, non indagato.

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
