# NEMESIS — TODO di progetto

Lista di lavoro derivata **alla lettera** dalla struttura di [`Research_Proposal.md`](Research_Proposal.md) (Domande → Basi fondanti A-K → workflow → tabella per fasi 1-8), integrata con lo stato reale di implementazione (`workflow.md`), i TO-DO grezzi dei meeting (`management/meetings/*.md`), il `TODO.md` tecnico a livello di codice (repo root) e le sessioni recenti di `.claude/stato_progetto.md`. Non è un log — è una lista di lavoro aperta, da spuntare/aggiornare mano a mano.

**Legenda stato** — checkbox vuota senza icona = da iniziare (default), checkbox piena = fatto; le icone segnalano solo gli stati non-default:

- `[ ]` da iniziare · `[x]` fatto
- `[ ]` 🔄 in corso
- `[ ]` ⛔ bloccato (dipendenza esterna)
- `[ ]` 💭 decisione aperta (nessun codice ancora necessario, va solo decisa)
- `[ ]` ⬛ deferred (rimandato esplicitamente, fuori scope per ora)

---

## 0. Prerequisiti trasversali

Item che bloccano o condizionano più fasi della tabella del proposal — vanno risolti prima o durante, non alla fine.

- [ ] **Copertura dati incompleta rispetto alla N target** (~5750, sezione "Cosa possiamo fare noi")
  Il retrieval (`config/pipelines/retrieval_server.json`) copre oggi solo 4 dataset — UNIPD/WashU, PASPORT, PSP, UKLFR/stroke_UKLFR (N reale nella lesion matrix: 1150). Amburgo (~500) "in arrivo", UCL (~4100) "da negoziare", Santiago senza N — nessuno dei tre è ancora nel config.

---> Bisogna aspettare 

- [ ] ⛔ **SDC in produzione** (Task 2)
  Installato e validato end-to-end su 1 soggetto reale + manifest su tutti i 1150 soggetti (0 esclusioni), ma il run di produzione su scala completa non è partito. Sotto-blocchi:
  - [ ] ⛔ installazione condivisa di `bcblib` sul server — richiesta all'amministratore ancora senza risposta (oggi gira solo sotto l'account personale)
  - [ ] 💭 sogliare la probabilità continua di disconnessione, o tenerla continua?
  - [ ] 💭 il Task 2 (embedding) usa l'output voxelwise di Stage 1 o le tabelle per-atlante di Stage 2?
  - [ ] 💭 quale sottoinsieme dei (fino a 15) atlanti EBRAINS serve davvero (rilevante anche per Fase 7/Task 5)?

--> stanno arrivando, ricordati di fare l'upgrade del tuo bcbtolitt

- [ ] **Imputazione NaN nella matrice FC**
  Deliberatamente non ancora implementata; va collocata accanto a `dim_reduction.py` (i NaN vengono dal mascheramento lesione in `mask_fc.py`, incompatibili con quasi tutti i metodi di riduzione/clustering a valle). Blocca de facto la Fase 2b.

---> spiega meglio

- [ ] 💭 **Dimensionalità dell'embedding per il clustering** (n_components: 2 vs 5 vs 10)
  Infrastruttura pronta (`nested_params`, `embedding_for_viz`, `viz_n_components`) ed eseguita sperimentalmente su UMAP/t-SNE reali (03-08/04-08), ma manca un plot aggregato trustworthiness-vs-n_components tra le foglie per decidere; nessun valore promosso a `params_reduction.json` di produzione.

---> spiega meglio

- [ ] 💭 **Scelta finale `n_neighbors`/`min_dist` di produzione UMAP** (e perplexity t-SNE)
  Dai risultati di tuning `03-08_s1.1`/`04-08_s1.1` - solo un primo sguardo fatto, nessuna scelta di produzione.


- [ ] **Clustering di consenso/stabilità** (`src/analysis/consensus_clustering.py`, RSC + Monti et al. 2003)
  Implementato e documentato, mai eseguito sulla coorte reale a 1150 soggetti per scegliere effettivamente un k di produzione.
  *Fonte: workflow.md §3.*

- [ ] **Armonizzazione neuroCombat** tra scanner diversi (WashU ST vs HC hanno scanner diversi)
  Nessuna traccia in `src/` (verificato via grep, nessun modulo/riferimento a `combat`). Necessaria almeno per la Fase 2b e per qualunque confronto multi-sito aggregato.
  *Fonte: Seba Meeting non datato — "Meeting_3" nel nome ma probabilmente antecedente a Seba_Meeting_2, vedi §9; Research_Proposal.md sezione J.*

- [ ] 💭 **Soglia minima di frequenza voxel** prima della dim reduction sulla lesion matrix
  Oggi si tiene qualunque voxel lesionato in ≥1 soggetto su 1150 (254.865 colonne, di cui solo 3642 lesionate in ≥10% della coorte). Pratica standard in lesion-symptom-mapping (Sperber & Karnath), non citata nella letteratura NEMESIS raccolta finora — buona pratica generale, non un gap validato dal gruppo. Da esplorare empiricamente prima di fissare un valore.
  *Fonte: workflow.md, `TODO.md` root, stato_progetto.md sessione 2026-07-28.*

- [ ] 💭 **Step di preprocessing neuroimaging mancanti in `build_lesion_matrix.py`**
  Oggi solo resample + ribinarizzazione, nessuno skull-stripping/denoising. Assume che le maschere siano già pulite a monte (`manual_masks`, fuori scope repo). Da valutare se/quando serve intervenire direttamente nella pipeline.
  *Fonte: `TODO.md` root.*

- [ ] **Config obsoleta `config/pipelines/build_lesion_matrix.json`**
  Ha oggi `"parcellate": true` con `atlas_path` sull'atlante funzionale `Yan300TianS2Buckner7N` (lo stesso delle matrici FC) — combinazione mai usata per nessuna run di produzione né per il tuning documentato (tutto il tuning riassunto in workflow.md gira sulla matrice voxel-wise, `"parcellate": false`). Non blocca nulla oggi, ma va sistemata esplicitamente prima del prossimo rilancio.
  *Fonte: workflow.md, nota finale.*

- [ ] **Pipeline Task 5 senza entry point** (predizione outcome, riproduzione Siegel et al. 2016)
  `src/analysis/prediction.py` implementa l'intero algoritmo (PCA per tipo di feature, ridge regression LOO-CV nested, r² di Siegel, permutation test, confronto Wilcoxon lesione-vs-FC, correzione Benjamini-Hochberg) e `src/features/clinical.py` carica i target da `participants.tsv` — ma non esiste `src/pipeline/predict_deficit.py`, nessuna config, nessun `jobs/run_predict_deficit.sh`. Blocca l'intera Fase 7.
  *Fonte: workflow.md §3.*

---

## Fase 1 — Embedding lesioni + clustering (Task 1, n~5750)

*Base: Thiebaut de Schotten 2020. Confronto/replica: PCA varimax dello stesso paper. Trampolino: confronto sistematico embedding×clustering a scala piena.*

- [x] Matrice lesione voxel-wise costruita (1150×254.865, 4 dataset, `group_filter=["ST"]`) — `data/derived/lesion_matrix/21-07_s1.1`.
- [x] Primo giro di tuning reale UMAP/t-SNE (`03-08_s1.1`/`04-08_s1.1`) su dati veri, con `nested_params` (metric × n_components × regress_out_volume).
- [x] `regress_out_volume` (residualizzazione OLS del volume sull'embedding) implementato e verificato incompatibile con jaccard/dice.
- [x] Coloring embedding per dataset, lato lesione, volume (scala log), NIHSS (punteggio totale).
- [x] Overlap map/mappa di probabilità delle lesioni per cluster su MNI (`clusters_analysis.ipynb`, sessione 04-08).
- [ ] Estendere la N a tutti i dataset disponibili una volta recuperati (Amburgo/UCL/Santiago) — dipende da §0.1.
- [ ] Chiudere le decisioni aperte in §0 (n_components di produzione, n_neighbors/min_dist finali, soglia voxel, consensus clustering) prima di considerare "di produzione" il clustering di Fase 1.
- [ ] **Replicare la PCA varimax di Thiebaut de Schotten 2020** (46 componenti, 30 spiegano >90% varianza) sulla lesion matrix NEMESIS
  `pca_varimax` è già un metodo disponibile in `dim_reduction.py`, ma non risulta lanciato con questo obiettivo esplicito di replica.
- [ ] **Confronto cluster vs territori vascolari noti**
  Nessun atlante vascolare presente nel repo (solo citato in Bisogno 2025); da procurare/costruire se si vuole questo confronto.
- [ ] **Coloring per subitem NIHSS specifici** (non solo il totale già fatto)
  Item 9 = linguaggio, item 11 = neglect, 5a-6b = motorio — ciascuno mappa un dominio comportamentale specifico. Verificare disponibilità dei subitem per dataset (nota già in `join_nihss`/`clinical.py`: PASPORT non ha NIHSS semplice, solo `NIHSS_at_presentation`/`24H`/`3m`, stesso gap da gestire).
  *Fonte: Seba_Meeting_1.*
- [ ] **Overlap % con atlanti** (vascolare/Yeo/Figley) per cluster — non implementato.
- [ ] **Radar/spider plot del centroide di cluster** (metriche, connettività, demografici, score clinici)
  Non implementato, nessuna traccia in `src/`/notebook.
  *Fonte: Seba_Meeting_1, `TODO.md` root.*
- [ ] **Numero di pazienti con lesione bilaterale** — non calcolato, nessuna traccia in `src/`/notebook.
  *Fonte: Seba Meeting non datato.*
- [ ] **Confronto sistematico embedding×clustering alla scala n~5750** (trampolino) — richiede prima la N piena (§0.1).

## Fase 2 — Embedding SDC + clustering (Task 2)

*Base: Griffis 2019/2020, Salvalaggio 2020. Confronto/replica: morfospazio UMAP di Talozzi 2023, ma su SDC invece di lesione grezza.*

- [ ] ⛔ **Bloccata per intero da §0.2** (SDC non ancora in produzione) — manifest già pronto (1150 soggetti, 0 esclusioni), ma zero output SDC reali su cui lavorare oggi.
- [ ] Una volta disponibile l'output SDC: stessi metodi di riduzione/clustering della Fase 1, stesse analisi/viz (mappa MNI, scatter colorato, overlap atlanti, radar plot).
- [ ] Replicare il morfospazio UMAP di Talozzi 2023 (2D) partendo dalla SDC NEMESIS invece che dalla lesione grezza.

## Fase 2b — Embedding + clustering FC indipendente (Task 3, n~500 WU+PD+Fri)

*Base: Idesis 2023 (autoencoder su dinamica BOLD).*

- [x] `mask_fc.py`/`build_fc_matrix.py` in produzione su WashU (169 soggetti con lesione+FC, 12 combinazioni di atlante).
- [ ] **Copertura dati incompleta**: solo WashU ha FC oggi nella pipeline reale
  Padova e Friburgo, nominalmente "coperti" nella tabella del proposal, non risultano ancora recuperati/costruiti per questa modalità. Verificare stato reale prima di procedere.
- [ ] ⛔ Imputazione NaN (§0.3) — blocca qualunque embedding sulla matrice FC mascherata.
- [ ] Embedding PCA/UMAP sulla matrice FC statica — infrastruttura pronta, riusa `dim_reduction.py`, ma non risulta ancora lanciata su una matrice FC (nessun output in `results/` sotto una modalità "fc").
- [ ] Verificare disponibilità delle **timeseries BOLD grezze** (235 ROI × N timepoint) per un embedding autoencoder "alla Idesis" in senso stretto
  Nota aperta già nel proposal (sezione B): non confermato se recuperate per WU+PD+Fri, solo ALFF/ReHo "che derivano dal BOLD" citati a meeting come concetto, non come dato disponibile in pipeline.
- [ ] Armonizzazione neuroCombat (§0.6) tra scanner ST/HC WashU, prerequisito per un clustering FC pulito.
- [ ] Clustering FC (5 metodi, come Fase 1) — non lanciato.
- [ ] Viz dedicate: matrice FC media per cluster e diff vs coorte sana, riassunto per network di Yeo (within/between), feature locali (ReHo/ALFF, vedi Fase 6) su superficie, composizione per dataset/sito (controllo artefatto scanner).

## Fase 3 — Confronto cluster lesione vs SDC vs FC

*Trampolino esplicito nel proposal: quantificare quanto la SDC comprime cluster lesionali distinti in uno stesso cluster, e quanto lesione/SDC predicono il cluster FC.*

- [ ] ⛔ Dipende per intero dal completamento di Fase 1, 2, 2b.
- [ ] Nessun modulo di confronto cross-clustering (ARI, NMI, contingency table) presente in `src/` oggi
  Verificato via grep, va scritto da zero (probabilmente `src/analysis/cluster_comparison.py` o simile, coerente con l'architettura a livelli del progetto).
- [ ] Contingency table/heatmap cross-modale.
- [ ] Copertura per dataset nell'embedding (quanti soggetti per dataset in ciascun cluster) — parzialmente coperto dal coloring per dataset già esistente (Fase 1), ma non come conteggio esplicito per cluster.

## Fase 4 — Feature funzionali per cluster anatomico (Task 3, n~500 WU+PD+Fri)

*Base: Griffis 2019 (PLSC struttura-funzione), Santoro 2026 (fingerprint). Confronto: mascheramento FC di Siegel 2016.*

- [x] FC mascherata su estensione lesionale (`mask_fc.py`, riproduce Siegel 2016) — già in produzione.
- [ ] ⛔ Dipende dal cluster anatomico di riferimento (Fase 1/3 completate).
- [ ] **z-score per singolo paziente vs template sano** (Siegel 2016), poi mediato per cluster anatomico
  Non risulta implementato: `prediction.py` implementa l'algoritmo predittivo di Siegel ma non questo specifico step di normalizzazione per template sano. Da verificare/scrivere.

## Fase 5 — Inferenza fenotipo funzionale da cluster anatomico

*Trampolino centrale del progetto (sezione K del proposal — capovolge l'asse comportamento→lesione tipico della letteratura corrente). Target dichiarato: 4-5 fenotipi funzionali (feasibility, da validare).*

- [ ] ⛔ Dipende per intero da Fase 1-4.
- [ ] Media delle feature funzionali (FC/ALFF/ReHo) per cluster anatomico.
- [ ] Validazione contro il cluster FC indipendente di Fase 2b/3 (ARI/NMI, qui usata come validazione non come confronto esplorativo).

## Fase 6 — Feature locali vs globali del segnale FC (Task 3)

*Base: Volpi 2024 (ReHo predittore locale più forte). Domanda di ricerca esplicita e ancora aperta (Corbetta_Meeting_1: "non è chiaro come le feature locali siano correlate con le feature globali").*

- [ ] **Nessuna delle 50 feature del catalogo Volpi 2024/2025 è implementata nel repo**
  `src/features/functional.py` fa solo mascheramento/vettorizzazione FC, non ALFF/ReHo/HRF/tvFC (verificato via grep, nessun riferimento a "reho"/"alff" in `src/`). Da costruire da zero: almeno il pool "Signal" (ALFF, ReHo, statistiche di base del BOLD) come punto di partenza minimo, dato che ReHo è il predittore singolo più forte in entrambi i paper Volpi.
- [ ] Prima applicazione di queste feature a una coorte stroke (Volpi lavora solo su soggetti sani) — nessun precedente diretto da replicare 1:1, è esplorazione.
- [ ] Costruire predittori locali intra-cluster usando il catalogo Volpi come punto di partenza
  Collegamento esplicito con Corbetta_Meeting_1: "covarianza concetto centrale", "MediaGFC"/"VarianzaGFC" citate a meeting come candidati.
- [ ] Requisito dati: verificare se le timeseries BOLD grezze necessarie per calcolare queste feature sono già recuperate/recuperabili per WU+PD+Fri (stesso gap di Fase 2b).

## Fase 7 — Correlazione con outcome clinico-comportamentale (Task 5)

*Base: Corbetta 2015, Bisogno 2021, Facchini 2023 (struttura a 3 fattori), Talozzi 2023 (DSD). Trampolino: testare la tensione clinica-vs-imaging (Bisogno 2025 vs Cinetto) sulla coorte NEMESIS.*

- [ ] ⛔ **Pipeline mancante** — vedi §0.9 (nessun entry point CLI per `prediction.py`/`clinical.py`, nessuna config, nessun job SLURM).
- [ ] Una volta agganciata la pipeline: Ridge regression / PCA sui punteggi comportamentali (algoritmo già scritto).
- [ ] Test non parametrici (Kruskal-Wallis/Mann-Whitney/χ²) + correzione FDR per validare i cluster (anatomici/SDC) contro NIHSS e subitem, con lo schema statistico di Zanola 2026 — non implementato.
- [ ] Boxplot/violin delle variabili cliniche per cluster — non implementato.
- [ ] Testare esplicitamente sulla coorte NEMESIS se i cluster anatomici/SDC aggiungono valore incrementale ai soli dati clinico-demografici (replicando lo schema gerarchico demografico→clinico→imaging di Cinetto), o se prevale la clinica come in Cinetto — domanda aperta, esito non scontato.

## Fase 8 — EEG (Task 4, n~80, Padova)

- [ ] ⬛ **Deferred esplicitamente a settembre/ottobre 2026** — nessuna azione da intraprendere ora. Metodi TBD.

---

## 9. Letteratura e mantenimento del proposal

- [ ] **Estendere la letteratura oltre la cerchia NEMESIS**
  Richiesta esplicita di Corbetta (Corbetta_Meeting_1, 29/07): cercare lavori di clustering non ancora nella libreria `papers/nemesis/`, in particolare **Fallani, clustering longitudinale** (nome citato a meeting, paper non ancora presente in `papers/nemesis/` né in `paper_lists.md` — da identificare e recuperare).
- [ ] Rivedere quali paper già presenti (oltre Bonkhoff 2020) fanno clustering, per completare la mappatura richiesta a meeting ("vedere quali lavori fanno clustering, tra quelli presenti tipo Bonkhoff, tra quelli da cercare").
- [ ] 💭 **Verificare la nota "da verificare" della sezione B del proposal** (Idesis 2023)
  Le timeseries BOLD grezze sono disponibili per WU+PD+Fri o no? Condiziona sia Fase 2b che Fase 6 (stesso dato sottostante).
- [ ] 💭 **Cinetto (sezione H) è citato "in bozza"** — verificare se è uscita una versione pubblicata/finale e aggiornare la citazione/i numeri nel proposal se cambiano.
- [ ] 💭 **Chiarire l'ordine cronologico reale dei meeting con Sebastiano**
  `Seba Meeting_3.md` non ha data in testa e, per contenuto (TO-DO "leggere Volpi/Siegel 2018-2019/Griffis 2020"), sembra precedere `Seba_Meeting_2.md` (22/07, che dà quelle letture per acquisite) e `Corbetta_Meeting_1.md` (29/07, dove Volpi è già citato come acquisito). Valutare se rinominare il file per riflettere l'ordine reale, o quantomeno annotarlo esplicitamente nel file stesso.

## 10. Debiti tecnici minori (da `.claude/stato_progetto.md`, non bloccanti per il proposal)

- [ ] Irrobustire `_write_tuning_output`/`output_dir.mkdir(exist_ok=True)` contro il riuso incoerente di una cartella di output tra run con `nested_params` diversi (proposto in sessione 2026-08-04 (2), non implementato — vedi `lessons_learned.md` #18).
- [ ] Verificare con chi ha modificato `notebooks/dim_reduction_clustering.ipynb` (modifiche non committate, non della sessione che le ha notate) prima di committarle o scartarle.
