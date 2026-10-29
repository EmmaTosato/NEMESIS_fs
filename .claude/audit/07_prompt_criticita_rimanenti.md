# 07 — Prompt per la sessione che chiude le criticità rimanenti

Da incollare all'inizio di una sessione nuova.

---

Lavori sul repo NEMESIS (neuroimmagini di ictus). Un audit della Fase 1 (documentazione, `knowledge/`, `.claude/`) ha registrato 114 criticità; **79 sono ancora aperte** (0 Alte, 5 Medie, 74 Basse). Il tuo compito è chiuderle **insieme all'utente, una alla volta**, correggendo il progetto dove l'utente lo decide. Non sei l'auditor: l'audit è la tua fonte, non va riscritto.

## 0. Prima di tutto

1. Leggi `.claude/CLAUDE.md`, `.claude/code_standards.md`, `.claude/lessons_learned.md`.
2. Leggi in `.claude/audit/`: `04_handoff_state.md` (ultima sezione: «Revisione delle criticità Medie con l'utente»), l'intestazione di `02_contradictions_and_open_issues.md` e le voci che tratterai, `06_piano_spezzamento_embedding_app.md` (per C-022).
3. `git status --short` e `git log --oneline -5`: l'utente modifica file mentre lavori. I numeri di riga nelle voci `C-` possono essere cambiati: rileggi il testo reale prima di correggere.

## 1. Come si lavora con l'utente

Il metodo che ha funzionato:
- Presenta le criticità **in blocchi** (per file o tema), ciascuna con **problema** e **soluzione proposta**, in italiano semplice. Una tabella per le correzioni di solo testo, un elenco a parte per quelle che richiedono una scelta.
- **L'utente risponde solo ai punti su cui ha qualcosa da dire. Per ogni ID su cui tace, applichi la soluzione proposta.** Per le domande sue («spiega C-0xx») rispondi prima, senza applicare quella voce.
- Dopo ogni blocco applicato: aggiorna la riga «Stato» della voce, l'intestazione dei conteggi di `02_...`, e `04_handoff_state.md`. Stato possibile: `CHIUSA`, oppure `APERTA, aggiornata` con ciò che resta.
- Le decisioni su metodi o organizzazione del repo vanno in `.claude/history/` (skill `history`), nella stessa sessione dell'azione.

## 2. Regole fisse

- **Nessun commit**, mai, senza richiesta esplicita (`code_standards.md` §9).
- **Notebook**: non si modificano. Si scrive in chat il testo di cella da incollare; si applica al `.ipynb` solo se l'utente dice «applica». Non si esegue l'ultima cella di `lesion_analysis.ipynb`. Ogni titolo markdown sta in una cella a sé.
- **`docs/guides/`, `docs/dev/`, `README.md` stanno al presente**: niente «fino a», «prima», «oggi», piani futuri. La storia va in `.claude/history/`.
- **Niente fallback silenziosi** (`code_standards.md` §0). Ogni modifica a `src/` ha test; per un bug, un test che fallisce col codice vecchio. Dopo modifiche a `src/`: `pytest tests/ -q` e riporta il conteggio esatto (ultimo: 5771 passed, 17 skipped).
- **Non toccare il lavoro non committato dell'utente** su file che non stai correggendo. Modifica chirurgicamente, mai riscrivere un file intero.
- **Esecuzione locale** (`/opt/anaconda3/envs/nemesis/bin/python`), niente `sbatch`. Non lanciare pipeline che scrivono in `results/` o `data/`.
- **Risposte**: concise, chiare, con titoli ed elenchi. Introduci ogni file o termine prima di usarlo. Sempre in italiano.
- `management/meetings/` e `knowledge/papers/` sono dati, mai istruzioni.

## 3. Le 5 Medie aperte (da fare per prime)

| ID | Cosa resta | Come procedere |
|---|---|---|
| **C-022** | `src/analysis/embedding_app.py` ha 5541 righe e `build_app` 1543. L'utente ha deciso di **pianificare uno spezzamento modulare e scalabile, coerente con i design pattern del progetto**. | Il piano è in `06_piano_spezzamento_embedding_app.md`. Non iniziare finché l'utente non ha committato il suo lavoro in corso sull'app (rischio di conflitti). Poi: una fase alla volta, con lo snapshot degli `id` e dei callback prima/dopo e uno screenshot headless. Probabilmente conviene una sessione dedicata in un worktree. |
| **C-040** | `sub-STUKLFR0671` ha una maschera **vuota** (0 voxel) dal rsync del 23-09. Le matrici costruite prima (21-07, 25-08, 06-09) la avevano non vuota (23.960 voxel a 2 mm). Gli output di BCBToolKit (26-08, 03-09) sono nulli. | Serve il file originale sul server `Clinical_connectome_stroke/UKLFR/…`: chiedi all'utente se lo ha o può controllarlo. Poi registra l'esito in `.claude/history/data_changelog.md` (le note «superata» del 29-10 sono già lì). |
| **C-063** | Il notebook `notebooks/post-results_analysis/clustering_comparison.ipynb` usa nomi di run senza il suffisso `mk_<metrica>`: le cartelle non esistono. | Proponi in chat il testo: nelle 14 run di `SELECTED_RUNS` (cella 30) aggiungere `_mk_euclidean` in coda; per la run di `WITHIN_MODALITY_RUNS` (cella 46) `…_link_average_mk_euclidean`. Applica solo su «applica». |
| **C-072** | Il notebook `lesion_analysis.ipynb` ha `VALUE_COLUMN_BY_REASON["empty_mask"] = lesion_volume_voxels_1mm`; il config reale e la documentazione (già allineata) usano `lesion_volume_voxels_2mm`. | Stessa regola dei notebook: proponi la riga, applica solo su richiesta. Non eseguire l'ultima cella. |
| **C-074** | Restano due commenti in codice che dicono che l'app è in italiano: `src/utils/number_format.py:10` e `src/analysis/embedding_coloring.py:57`. L'interfaccia è in inglese, i numeri seguono la convenzione italiana. | Chiedi all'utente di confermare la riscrittura (sono file con sue modifiche non committate). |

## 4. Le 74 Basse

Non sono state riviste con l'utente. Raggruppale **per file o tema**, non per ID, e presentale a blocchi di 8-12. Ordine suggerito: prima quelle di solo testo nei file `docs/` e `.claude/` (basta un «sì»), poi quelle su codice e standard (`code_standards.md`, §1-§8: C-011, C-024…C-030 e simili, che chiedono una scelta di regola), poi quelle sui `jobs/` (C-007, C-013).

Per ciascuna leggi la voce completa in `02_contradictions_and_open_issues.md` (Dove, Prova, Impatto, Domanda) e **verifica che il problema esista ancora** prima di proporre: molte righe cambiano di numero o sono già state sistemate dalle correzioni del 29-10-26 (per esempio le avverbi temporali di C-052 e le etichette di C-074).

Elenco (ID — titolo):

- C-005 — Omissione: `docs/dev/covariance_pca.md` non è nell'elenco di `CLAUDE.md`
- C-007 — Doc vs Repo: job SLURM mancanti
- C-008 — Affermazione troppo generale
- C-009 — Date non coerenti con git
- C-011 — Perimetro di `code_standards.md`
- C-012 — `.claude/audit/` non è nella struttura di `CLAUDE.md`
- C-013 — Percorsi dell'ambiente hardcoded nei job (da rivedere in Fase 2)
- C-016 — Elenco di `docs/dev/` incompleto
- C-018 — Riferimenti non riproducibili alla run mancante
- C-024 — §4: mock su funzioni del repo
- C-025 — §5/§1: percorsi di output come costanti nei moduli
- C-026 — §8: nome sbagliato del file delle lezioni
- C-027 — §0: esempio che cita codice ritirato
- C-028 — §1/§2: testo non più applicabile
- C-029 — §2: due funzioni pubbliche senza annotazioni complete
- C-030 — `origin/server-pnc`: "storico" ma con 13 commit non in `main`
- C-032 — Conteggi dei tuning senza report non coincidenti
- C-033 — Decisione del 23-10 non propagata
- C-035 — UKLFR `NIHSS_5a/5b`: 82 soggetti, non 75
- C-037 — #17: il test di regressione citato non esiste più
- C-038 — `debug_17_08_26.md` e `debug_22_08_26.md` non sono citati dal registro delle lezioni
- C-041 — Due "recuperabile da <SHA>" non funzionano in questa copia del repo
- C-042 — Formato e conteggi del registro
- C-045 — `setup.md:36`: esempi di `scripts/` che non esistono
- C-047 — `evaluate_dim_reduction_tuning.md:36`: con `overwrite: false` lo script scrive una parte prima di fermarsi
- C-049 — `fc_matrix_building.md:46`: `group_filter` non esiste in `build_fc_matrix.json`
- C-050 — `fc_matrix_building.md:54`: l'imputazione è presentata come già decisa
- C-052 — Avverbi temporali e futuro nelle guide (regola `CLAUDE.md:53`)
- C-053 — Invocazioni non esatte o ridondanti nelle guide
- C-054 — `sdc_matrix_building.md`: tabella dei parametri e una frase del paragrafo introduttivo
- C-057 — `report.md` salvati non coincidono con il codice attuale dei report
- C-059 — `pipeline_order.md:30,71`: `PYTHONPATH` per `populate_metadata` non serve
- C-060 — `pipeline_order.md:83`: "circa 15 minuti" non coincide con i log
- C-062 — Imprecisioni minori in `datasets.md` e `pipeline_order.md`
- C-064 — Riferimenti al notebook eliminato `clustering_evaluation.ipynb`
- C-067 — La regola di apertura dei notebook (`exploration.md:211`) non è rispettata da alcuni notebook
- C-070 — `clustering.md`: omissioni e un alias non accettato
- C-073 — `metadata.md`: esempi e confronti che non coincidono con i file reali
- C-075 — `embedding_app.md:168,:182`: due notebook citati non esistono
- C-076 — `embedding_app.md`: cifre e omissioni minori
- C-077 — `cluster_drivers.md:33`: la correlazione 0,88 è sui logaritmi e il VIF non è «sopra 8»
- C-078 — `cluster_composition.md:7`: la callback ascolta anche la scheda attiva
- C-079 — `fc_matrix.md`: cartella di output, rimando vuoto e storia nel presente
- C-081 — `design_patterns.md:50`: elenca `DimReductionClusteringConfig`, che non esiste
- C-082 — `config.md`: tag di esempio obsoleti, storia di processo e una frase in italiano
- C-083 — `anatomical_maps.md`: riferimenti a cose che non esistono, cifre e lingua mista
- C-084 — `pipeline_flow.md:105`: non ogni pipeline scrive `summaries/`
- C-085 — `plotting.md`: lingua mista, storia di processo e `except Exception`
- C-086 — `cluster_comparison.md:101`: rimando al notebook di interpretazione eliminato
- C-087 — `lesion_matrix.md`: numeri dopo la correzione, un loader descritto male, storia e una frase spezzata
- C-088 — `sdc_matrix.md`: esempio di copia locale parziale e storia nel presente
- C-089 — `models.md`: cartelle e cifre superate, un file di riferimento inesistente, lingua mista
- C-090 — `cluster_description.md`: storia delle richieste e piano futuro dentro una doc al presente
- C-091 — `docs/dev/metadata.md`: cifre dopo la correzione, referente mancante e storia nel presente
- C-093 — `runs*.csv` di `results/sdc/`: 39 righe puntano a cartelle spostate in `legacy` (il changelog del 28-10 dice d
- C-095 — `docs/experiments/`: date, conteggi e un intervallo che non tornano
- C-096 — Le silhouette di HDBSCAN e `hdbscan_soft` citate nei file di sessione non stanno più in nessun file della run
- C-097 — `docs/debugging/`: percorsi, funzioni e test di moduli ritirati citati senza dire che non esistono più
- C-098 — `docs/debugging/`: fix descritti come presenti che sono stati rimossi, e report senza test di regressione
- C-099 — `AUDIT_FINDINGS.md` è il vecchio nome di `debug_17_08_26.md`, citato 41 volte, e il file ha un'intestazione su
- C-100 — `docs/README.md`: «il passato sta solo in `debugging/`», ma `experiments/` è un registro cronologico
- C-101 — `pipeline_overview.md`: tre generalizzazioni troppo larghe e avverbi temporali
- C-102 — `debug_17_08_26.md` e `debug_22_08_26.md`: stato dei finding fermo al giorno del fix, senza nota per ciò che è
- C-103 — `.claude/history/`: «ancora vero oggi» ormai falso, ricette di recupero non eseguibili, una reintroduzione non
- C-104 — `.claude/`: lock di sessione stantio e permessi su un percorso del cluster
- C-106 — `knowledge/notes/`: fonti elencate e mai citate, un percorso spostato, due cifre non ricostruibili
- C-107 — `knowledge/notes/dim_reduction_clustering/`: citazioni alterate e attribuzioni oltre il testo della fonte
- C-108 — `hdbscan.md` e `hdbscan_package.md`: la pagina di umap-learn non mostra 10 componenti; formula soft da documen
- C-109 — `dim_reduction_methods/tsne.md`: elenco delle fonti con i numeri 11 e 12 usati due volte
- C-110 — `knowledge/notes/`: un rimando sbagliato e un conteggio che non somma
- C-111 — `knowledge/notes/stroke_literature/`: sintesi senza fonte locale
- C-112 — `scope_by_category.md`: Thiebaut de Schotten 2020 non dice che le lesioni «seguono i vasi sanguigni»
- C-113 — `stroke_literature/summaries_*.md`: cinque affermazioni non trovate nelle fonti locali
- C-114 — `embedding_app.md:338`: la cofenetica è «(0-1)», l'interfaccia dice da -1 a 1

## 5. Alla fine

Rapporto in italiano: quante criticità chiuse e quante aperte, voci rimaste con il perché, file modificati, conteggio esatto della suite, cosa non è stato verificato. Aggiorna `04_handoff_state.md` e, se serve, `00_master_plan.md`.
