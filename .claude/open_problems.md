# Problemi aperti e cose da fare — NEMESIS

Ultimo aggiornamento: 07-09-26.

Elenco vivo di ciò che è **aperto adesso**: problemi noti non risolti, decisioni non prese, lavori iniziati e non finiti. Una voce si cancella quando è chiusa — non si tiene lo storico qui.

**Dove va invece il resto**: cosa è già implementato → `README.md`; stato tecnico corrente → `.claude/stato_progetto.md`; perché una decisione è stata presa così → `.claude/history/`; risultati di un esperimento → `docs/experiments/`.

---

## 🔴 Problemi di dati

### Lato della lesione invertito in ~6% di WashU — *non risolvibile internamente*

Su 120 soggetti WashU controllati, **7 hanno il `lesion_side` clinico opposto alla geometria della maschera**, e non sono casi dubbi: sono inversioni piene (lesione interamente dal lato contrario). Confermati: `sub-STUNIPD0002`, `0026`, `0077`, `0179`, `0187`, `0056`, `0151`.

Il tasso negli altri dataset è ~0% (UKLFR 0/120, UKE 1/120, PSP 1/95), quindi non è rumore di misura: o sono errori di etichetta all'origine, o un sottoinsieme di WashU segue una convenzione di lato invertita.

**Il dato arriva così dalla sorgente**: `data/clinical_connectome/metadata_tsv/participants_WashU.tsv`. Non è correggibile da questo repo — va segnalato a chi cura quei metadati. Fino ad allora resta un limite noto, non un lavoro in coda.

**Mitigazione pratica**: non usare il `lesion_side` clinico di WashU come verità. La geometria della maschera è disponibile e concorda con l'etichetta nel 98% dei casi complessivi, quindi è il riferimento più affidabile per questo dataset — è anche il motivo in più per implementare il `lesion_side` geometrico qui sotto. Da chiarire anche se il problema riguardi solo i 120 campionati o tutti i 166 etichettati.

### `sub-STUKLFR0671`: SDC vuoto con lesione grande

Nella matrice `sdc_matrix` s2.2-vol questo soggetto è una riga interamente nulla. La causa è a monte: la sua mappa `disconnectome-map` ha **0 voxel non nulli** pur avendo una lesione da **56.785 voxel**. Output degenere di BCBToolKit, non una proprietà del soggetto.

Unico caso su 1570. Per risolverlo va rilanciato `compute_sdc.py` per quel soggetto, **che gira solo sul cluster**. Nel frattempo va escluso a valle.

---

## 🟡 Decisioni non prese

### `lesion_side` calcolato geometricamente

`lesion_side` oggi è popolato solo dove il dato clinico esiste. Mancano PASPORT e UCL-UK (nessuna colonna) e ~230 soggetti tra WashU e PSP (cella vuota).

Il disegno originale (`docs/dev/metadata.md`) prevedeva di calcolarlo dalla maschera con una soglia "bilaterale" calibrata sui dataset che hanno l'etichetta. **Misurato il 06-09-26: quella calibrazione non è possibile.** Il `both` clinico e la geometria non misurano la stessa cosa — metà dei soggetti etichettati `both` ha la lesione essenzialmente tutta da un lato, e anche una soglia assurdamente permissiva ne recupera 10 su 25. In più `both` esiste solo in UKE.

Cosa invece funziona benissimo: il **segno** dell'indice di lateralità `LI = (R−L)/(R+L)` concorda con l'etichetta clinica nel **98%** dei casi (446/455).

**Proposta sul tavolo, non ancora approvata:**
1. salvare `lesion_laterality_index` continuo — è il dato vero, e lascia rivedibile qualunque soglia senza ricalcolare 5720 maschere;
2. derivare `lesion_side` geometrico **solo** come left/right dal segno;
3. se serve una categoria bilaterale, definirla come descrittore geometrico dichiarato (es. `|LI| < 0.5`), mai spacciata per una ricostruzione del `both` clinico.

Contesto completo: `.claude/history/methods_changelog.md`.

---

## Note

- **Build SDC `s2.2-vol`**: **eseguita** il 07-09-26 — 1570 × 290940, `float32` continua, stessa griglia 2mm di s1.3-vol. Composizione ed esclusioni in `docs/experiments/processing/matrices.md`.

- **Sezioni "Decisioni" di `s1_production.md`**: **compilate** il 07-09-26 per s1.1-vol e s1.2-vol. La decisione registrata è che *non* si sceglie un k unico: tenere aperte più granularità in parallelo è la scelta, perché nessun criterio interno converge e k va deciso insieme a `n_components`.

- **Audit naming dei plot**: **chiuso** il 07-09-26 senza rinominare niente. Inventariati tutti i nomi di file di plot prodotti: sono formalmente disomogenei (tre suffissi diversi) ma ognuno è inequivocabile dentro la propria directory, e ogni nome è referenziato in 5-15 file tra doc, test e risultati — rinominare sarebbe costo puro. La convenzione è ora scritta in `docs/dev/plotting.md` ("Naming dei file di plot") e vale per i nomi nuovi.

- **Righe tutte-zero in `s1.3-vol`** (`sub-STUKE0146`, `sub-STUKE0201`): **non** è un problema aperto — deciso il 07-09-26 di lasciarle, 2 su 5720. Documentate in `docs/experiments/processing/matrices.md`; vanno filtrate a valle da chi ne ha bisogno, soprattutto sotto metriche binarie.
- **Branch `viz-niivue`** eliminato il 07-09-26 con i suoi 4 commit non mergeati (renderer alternativo per i pannelli di anatomia). Recuperabile da `facef6f` finché il reflog lo tiene: `git checkout -b viz-niivue facef6f`.
