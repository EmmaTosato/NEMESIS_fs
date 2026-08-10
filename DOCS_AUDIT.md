# Audit documentazione `docs/` — file temporaneo di lavoro

Non fa parte della documentazione stabile del progetto — da cancellare a fine revisione.
Per ogni file: cosa è confermato corretto, cosa è obsoleto/errato (con riferimento file:riga sia nel `.md` sia nel codice reale), cosa non è verificabile da questo Mac.

---

## `docs/guides/retrieval.md` — ✅ FATTO

## `docs/guides/datasets.md` — ✅ FATTO

---

## `docs/guides/atlas_building.md` — ✅ FATTO 

---

## `docs/guides/matrix_building.md` — ✅ FATTO
(10/08: aggiunto `manifest.json` all'elenco output; rimossa la nota fuorviante su `build_lesion_matrix_local.json`, sostituita con un avviso generale di controllare/aggiornare il config prima di ogni run, su indicazione dell'utente — il punto 3, sullo snapshot config non ancora lanciato, non è un problema da correggere in sé, solo un promemoria)

---

## `docs/guides/fc_matrix_building.md` — ✅ FATTO. 
(10/08: righe 13 e 60 riscritte per riflettere che la soglia di esclusione paziente è una decisione chiusa — utente ha confermato che non la implementerà — non più presentata come "da decidere"; resto del file già confermato corretto, nessun'altra discrepanza)

---

## `docs/guides/compute_sdc.md` — ✅ FATTO  
(10/08: comando corretto a `jobs/run_compute_sdc_no_slurm.sh` invece di `scripts/...`, aggiornato anche il commento header dello script stesso che diceva la stessa cosa sbagliata; schema `runs.csv` corretto a `session, id, timestamp, params, output, notes`. Non verificabile da qui, richiede cluster/bcblib: conteggio 15 atlanti EBRAINS, comportamento Stage 1/2 reale)

---

## `docs/guides/dim_reduction.md` — ✅ FATTO 
(10/08: sezione runs.csv riscritta per descrivere correttamente i due file separati `runs.csv`/`runs_tuning.csv` con schema `session, id, timestamp, params, output, notes`. Nota collaterale non toccata, fuori scope docs/: anche i docstring interni di `src/pipeline/dim_reduction.py` e `src/utils/run_log.py` hanno la stessa descrizione obsoleta)

---

## `docs/guides/clustering.md` — ✅ FATTO 
(10/08: riga 101 corretta per descrivere i due file separati `runs.csv`/`runs_tuning.csv`, stesso fix di `dim_reduction.md`. Resto del file già confermato corretto in dettaglio, incluso il comportamento noto/documentato di `cluster_plot.png` che disegna solo le prime 2 colonne)

---

## `docs/guides/dim_reduction_clustering.md` — ✅ FATTO 
(10/08: rimosso il riferimento residuo a "k-distance" tra le diagnosi di fine-tuning, feature rimossa insieme a DBSCAN→HDBSCAN in sessione 2026-07-29. La descrizione di `runs.csv`/`runs_tuning.csv` era già corretta in questo file - è servita da riferimento per correggere `dim_reduction.md`/`clustering.md`)

---

## `docs/dev/retrieval.md` — ✅ FATTO (10/08: atlanti FC-pearson Glasser/Schaefer→Yan corretti come puntatori al registro; sezione "Known follow-up" riscritta come risolta; riga 7 "Windows path" corretta; riga 9 "176/196" rimossa e sostituita col conteggio reale confermato dall'utente — 225 cartelle WashU `features/`, 169 stroke + 56 controlli sani)

---

## `docs/dev/analysis.md` — ✅ FATTO, poi **spezzato in 5 file** (10/08)

Prima corretti i 3 errori trovati (riga 7 "Status" `feature` falsamente descritto come non registrato, sezione `run_log.py` con lo schema `runs.csv` a due file, righe 318-319 sulla soglia FC "not yet decided"/"not yet run for real" — vedi commit precedenti). Poi, su richiesta esplicita dell'utente (file "troppo lungo", 321 righe che coprivano 3 pipeline concettualmente diverse), **spezzato in 5 nuovi file** invece di restare un unico doc:
- `docs/dev/models.md` — `reduction.py`/`clustering.py`, `tuning.py`, `clustering_tuning.py`, `consensus_clustering.py`, `distances.py`, `covariates.py`, + i 3 CLI (`dim_reduction.py`/`clustering.py`/`dim_reduction_clustering.py`)
- `docs/dev/config.md` — `params.py`, `model_config.py`, `run_log.py`/`SESSIONS.md`, `logging_setup.py`
- `docs/dev/plotting.md` — `plotting.py`, `embedding_coloring.py`/`embedding_plots.py`, le funzioni di arricchimento metadata (`clinical.py::join_lesion_side`/`join_nihss`/`enrich_metadata_with_lesion_info`)
- `docs/dev/lesion_matrix.md` — `features/lesion.py`, `build_config.py`, CLI `build_lesion_matrix.py`
- `docs/dev/fc_matrix.md` — `features/functional.py`, CLI `mask_fc.py`/`build_fc_matrix.py`

`docs/dev/analysis.md` originale rimosso (`git rm -f`). **Tutti i 17 riferimenti incrociati trovati** verso il vecchio file sono stati aggiornati al file giusto tra i 5 nuovi (README.md, `docs/guides/fc_matrix_building.md`, `docs/knowledge/dim_reduction_tuning_guide.md`/`fc_lesion_masking.md`, `docs/dev/design_patterns.md`, `.claude/CLAUDE.md` — struttura `docs/dev/` aggiornata —, e 9 file `src/`/`tests/`) — **tranne** `.claude/stato_progetto.md` e `docs/debugging/debug_27_07_26.md`, lasciati intatti perché narrativa storica (descrivono correttamente cosa esisteva *allora*, non vanno riscritti per lo stato di oggi, stesso principio già applicato alla sezione `docs/debugging/` di questo audit). Colte anche 2 occasioni per correggere di striscio la stessa imprecisione "soglia FC non ancora decisa" trovata altrove, in `README.md` e nel commento sorgente di `src/features/functional.py::drop_constant_edges`.

---

## `docs/methods/dimensionality_reduction.md` — ✅ FATTO (10/08: aggiunta nota all'inizio della sezione `pca_varimax` che segnala non essere raggiungibile da CLI oggi, pur essendo implementato/testato — stessa lacuna trasversale segnalata e corretta in tutti e 5 i documenti coinvolti: questo, `dim_reduction_tuning_guide.md`, `docs/dev/analysis.md`, `docs/guides/dim_reduction.md`, `docs/guides/dim_reduction_clustering.md`)

---

## `docs/methods/clustering.md` — ✅ FATTO (10/08: riga 7, link morto a `docs/guides/analysis.md` inesistente, sostituito con `docs/guides/clustering.md`/`docs/guides/dim_reduction_clustering.md`)

---

## `docs/knowledge/fc_lesion_masking.md` — ✅ FATTO (10/08: riga 82 aggiornata — tutte e 12 le combinazioni di atlante sono state effettivamente girate sui dati reali, masking e matrice finale, non solo `Yan200TianS2Buckner7N`)

---

## `docs/knowledge/Siegel2016_Reproduction.md` — 🗑️ ELIMINATO il 10/08 su richiesta esplicita dell'utente (non solo corretto — il file non esiste più). Rimosso anche il riferimento morto a questo file in `docs/guides/datasets.md` (riga 35).

---

## `docs/knowledge/dim_reduction_tuning_guide.md` — ✅ FATTO (10/08: aggiunta nota inline sulla stessa lacuna `pca_varimax` di cui sopra)

---

## `docs/knowledge/clustering_tuning_guide.md` — ✅ FATTO — nessuna discrepanza era stata trovata, nessuna modifica necessaria

---

# `docs/debugging/` — narrativa storica, criterio di verifica diverso

Questi file non descrivono lo stato attuale del codice — sono report di sessioni di debug passate. "Vero" qui significa: coerente con `.claude/lessons_learned.md` (che li cita come fonte), coerente con la storia git reale (funzioni/nomi citati devono essere esistiti davvero, anche se poi rimossi/rinominati), e internamente coerente — **non** deve corrispondere al codice di oggi, che nel frattempo è stato ampiamente rifattorizzato (es. `space`/`modality` di questi vecchi report sono diventati `datatype`/`suffix`, `native()`/`mni_mask()` sono spariti in favore di `resolve()`, la sezione "Ambiguous" del report è stata rimossa del tutto). Non mi aspetto quindi di trovare "bug nel codice attuale" qui — l'obiettivo è verificare che il racconto di ciò che successe sia fedele, non che descriva l'oggi.

## `docs/debugging/debug_09_07_26.md`

**✅ Confermato corretto**
- **Tutte e 7 le categorie di bug (§1-7) hanno un riscontro esatto in `.claude/lessons_learned.md`** (pattern #1-7, ciascuno con `debug_09_07_26.md` citato come fonte) — verificato incrociando testo per testo: descrizione dell'errore, criticità, e persino il dettaglio "2 istanze nella stessa sessione" per il pattern #5 (duplicati) combaciano esattamente tra i due documenti.
- **Grounding storico reale**: cercato con `git log --all -S"mni_mask"` e `-S"_parse_retrieve_item"` (pickaxe search, trova i commit che hanno introdotto/rimosso quella stringa) — entrambi i nomi di funzione citati nel report **sono realmente esistiti** nel codice in quel periodo, non inventati a posteriori. Coerente con l'affermazione della doc che oggi quelle funzioni non esistono più (sostituite da `resolve()` con la convenzione `datatype`/`suffix`).
- La sezione "Ambiguous" del report che il fix di §3 introduce ("si segnala esplicitamente l'ambiguità... mai risolta in silenzio") è coerente con quanto trovato in `docs/dev/retrieval.md` — che oggi dice esplicitamente *"There is no 'Ambiguous' category anymore"* — quindi quella sezione è stata introdotta qui e poi rimossa in un refactor successivo, non una descrizione ora falsa ma una fase intermedia reale della storia del codice.

**⚠️ Discrepanza reale (minore)**
- **Riga 100 — riferimento a un file che non esiste**: *"Skill generale estratta da queste categorie: `silent-failure-audit` (vedi `~/.claude/skills/silent-failure-audit/SKILL.md`)"* — verificato `ls ~/.claude/skills/`: quella cartella/skill **non esiste** oggi (il contenuto reale è `README.md`, `convert_paper`, `export_full_md`, `git_committer.md`, `paper_downloader` — nessuna traccia di `silent-failure-audit`). O la skill non è mai stata effettivamente creata dopo questa sessione, o è stata rimossa/rinominata in seguito senza aggiornare questo riferimento.

**❓ Non verificabile da qui**: i dettagli specifici del fix (es. il codice esatto di `RetrieveItem.__post_init__` di allora) — il commit esatto di quella sessione non è stato identificato/isolato, solo confermata l'esistenza storica dei nomi citati.

---
