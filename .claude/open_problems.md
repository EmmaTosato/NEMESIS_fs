# Problemi aperti e cose da fare — NEMESIS

Ultimo aggiornamento: 07-09-26.

Elenco vivo di ciò che è **aperto adesso**: problemi noti non risolti, decisioni non prese, lavori iniziati e non finiti. Una voce si cancella quando è chiusa — non si tiene lo storico qui.

**Dove va invece il resto**: cosa è già implementato → `README.md`; stato tecnico corrente → `.claude/stato_progetto.md`; perché una decisione è stata presa così → `.claude/history/`; risultati di un esperimento → `docs/experiments/`.

---

## 🔴 Problemi di dati

### Lato della lesione invertito in ~6% di WashU

Su 120 soggetti WashU controllati, **7 hanno il `lesion_side` clinico opposto alla geometria della maschera**, e non sono casi dubbi: sono inversioni piene (lesione interamente dal lato contrario). Confermati: `sub-STUNIPD0002`, `0026`, `0077`, `0179`, `0187`, `0056`, `0151`.

Il tasso negli altri dataset è ~0% (UKLFR 0/120, UKE 1/120, PSP 1/95), quindi non è rumore di misura: o sono errori di etichetta, o un sottoinsieme di WashU segue una convenzione di lato invertita.

**Impatto**: qualunque analisi che usi `lesion_side` di WashU è sospetta finché non si chiarisce. Da capire anche se il problema riguarda solo i 120 campionati o tutti i 166 etichettati.

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

## 🔵 Lavori pronti ma non lanciati

### Build SDC voxelwise `s2.2-vol`

Il config `config/pipelines/build_sdc_matrix.json` è pronto e validato: `representation: voxelwise`, disconnettoma, 5 dataset (con UKE), griglia 2mm, `nearest`. Attesi **1570 soggetti** (WashU 195, PASPORT 83, PSP 168, UKLFR 673, UKE 451).

Prima di lanciare: aggiungere la entry `### Session 2.2-vol` in `docs/experiments/data_sessions.md`, come fatto per s1.3-vol.

### Clustering SDC s2.1: estensione a `nc3`

`docs/experiments/clustering/s2_tuning.md` documenta `nc2` e indica `nc3` come passo successivo. Non fatto.

---

## ⚪ Piccole cose

### Le sezioni "Decisioni" di `s1_production.md` sono vuote

La scelta del k di produzione per il clustering lesionale **è stata fatta**, ma entrambe le sezioni `##### Decisioni` di `docs/experiments/clustering/s1_production.md` (s1.1-vol e s1.2-vol) sono vuote: la decisione non risulta scritta da nessuna parte. Da riportarci quale opzione è stata scelta e perché.

### Audit naming a livello di plot

Aperto da tempo, mai affrontato.

---

## Note

- **Righe tutte-zero in `s1.3-vol`** (`sub-STUKE0146`, `sub-STUKE0201`): **non** è un problema aperto — deciso il 07-09-26 di lasciarle, 2 su 5720. Documentate in `docs/experiments/processing/matrices.md`; vanno filtrate a valle da chi ne ha bisogno, soprattutto sotto metriche binarie.
- **Branch `viz-niivue`** eliminato il 07-09-26 con i suoi 4 commit non mergeati (renderer alternativo per i pannelli di anatomia). Recuperabile da `facef6f` finché il reflog lo tiene: `git checkout -b viz-niivue facef6f`.
