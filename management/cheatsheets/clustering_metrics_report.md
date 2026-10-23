# Metriche di valutazione del clustering: stato e proposta di convergenza

Data: 2026-10-20. Metodi coperti: `agglomerative`, `hdbscan` (sklearn), `hdbscan_soft` (pacchetto `hdbscan`).
Fonte: lettura del codice (`src/analysis/clustering_tuning.py`, `clustering_tuning_analysis.py`, `clustering_evaluation.py`, `cluster_quality.py`, `embedding_app.py`, `src/pipeline/clustering.py`), dei notebook sotto `notebooks/post-results_analysis/` e dei docs. Niente è stato rieseguito.

(23-10-26, superata in parte dal commit `a91c300`, 22-10-26: per `hdbscan` e `hdbscan_soft` silhouette, CH, DB e Dunn non si calcolano più, in nessuna delle sei superfici; l'indice interno è il DBCV (`src/analysis/dbcv.py`, `evaluation_metrics.md` §8). Quindi le righe «Silhouette, CH, DB» di 3.2 e 3.3 e il nucleo comune di 5.1 non valgono più per i due metodi di densità. Sono tolti anche `membership_share_below_half` (soglia 0.5), le curve filtrate per rumore (soglia 0.1), `NOISE_WARNING_FRACTION`, `LOW_PROBABILITY`, `LOW_MEMBERSHIP` e `curves_max_noise_fraction`: nessuna di queste costanti compare più in `src/`, `config/` o nei notebook, quindi 4.3 è chiusa. Il resto vale per agglomerative.)

---

## 1. Sintesi

- Le metriche **non sono un insieme unico**: sono calcolate in 3 momenti (sweep di tuning, analisi del tuning, produzione) e mostrate in 6 posti diversi, ognuno con un sottoinsieme diverso.
- Le **formule sono le stesse** dove i nomi coincidono (silhouette, CH, DB usano le stesse funzioni in tuning e in produzione). Il disordine non è numerico, è di **copertura e di soglie**.
- Il problema più concreto: **gli indici del tuning e quelli della produzione non si possono mettere a confronto riga per riga**. Il tuning non ha Dunn, silhouette macro/minima né, per agglomerative, la quota del cluster più grande. La produzione ha tutto questo ma non le curve per k.
- Le **soglie sono sparse e duplicate** (rumore 0.1 in 4 punti, 0.5 in 5 punti) e il criterio "usabile" dei docs sperimentali **non esiste nel codice**.
- Un debito aperto confermato: in `clustering_comparison.ipynb` homogeneity e completeness sono **ancora scambiate** (c'è solo una nota, la cella non è cambiata).

---

## 2. Dove compaiono le metriche

| # | Superficie | Quando | Cosa legge/calcola |
|---|---|---|---|
| A | `tuning_results.csv` + `tuning_plot.png` | sweep di `clustering.py --fine_tuning true` | indici per combinazione, calcolati durante lo sweep |
| B | `evaluate_clustering_tuning` → `report.md`, `cophenetic_correlation.csv`, `dendrogram_jump.csv`, `linkage_agreement.csv`, `density_metrics.csv`, curve | dopo lo sweep, dalle etichette salvate | indici aggiuntivi senza rifare il clustering |
| C | `clustering_tuning_explorer.ipynb` (e `dendrogram_embedding_explorer.ipynb`) | a mano, su tuning già fatto | rilegge A, ricalcola cophenetic da `X`, filtra per rumore |
| D | cartella di **produzione** (`cluster_plot.png`, `silhouette_plot.png`, `config.md`) | `clustering.py` produzione | silhouette per soggetto (euclidea), conteggio cluster e rumore |
| E | App Dash, pannello "Valutazione del clustering" | su run di produzione | `geometric_summary`, `model_fit_metrics`, membership (solo matrici ≤ 1000 colonne) |
| F | `clustering_evaluation.ipynb` | su run di produzione | stesse funzioni di E, senza il limite di colonne |

E ed F usano le **stesse funzioni** (`clustering_evaluation.py`), quindi tra loro non divergono. La divergenza è tra A/B/C (tuning) e D/E/F (produzione).

---

## 3. Matrice metrica × metodo

Legenda: ✔ presente · ✘ assente · (e) solo con distanza euclidea.

### 3.1 Agglomerative

| Metrica | A sweep | B analisi tuning | C explorer | D/E/F produzione |
|---|---|---|---|---|
| Silhouette (media sui soggetti) | ✔ qualsiasi `metric` | ✔ + fasce Kaufman-Rousseeuw | ✔ | ✔ (e) |
| Silhouette macro / cluster peggiore / per cluster | ✘ | ✘ | ✘ | ✔ (e) |
| Calinski-Harabasz | ✔ (e), NaN altrimenti | ✔ | ✔ | ✔ (e) |
| Davies-Bouldin | ✔ (e), NaN altrimenti | ✔ | ✔ | ✔ (e) |
| Dunn | ✘ | ✘ | ✘ | ✔ (e) |
| Quota del cluster più grande | ✘ | ✘ | ✘ | ✔ |
| Correlazione cofenetica | ✘ | ✔ per (metric, linkage) | ✔ ricalcolata da `X` | ✔ per il linkage della run (rifit) |
| Salto del dendrogramma | ✘ | ✔ per k nel `k_range` | ✘ | ✔ al k della run (rifit) |
| ARI tra linkage | ✘ | ✔ | ✘ | ✘ |

### 3.2 HDBSCAN (sklearn)

| Metrica | A sweep | B analisi tuning | C explorer | D/E/F produzione |
|---|---|---|---|---|
| Silhouette, CH, DB (rumore escluso) | ✔ | ✔ | ✔ | ✔ |
| Silhouette macro / peggiore / per cluster | ✘ | ✘ | ✘ | ✔ |
| Dunn | ✘ | ✘ | ✘ | ✔ |
| `noise_fraction` | ✔ | ✔ | ✔ | ✔ |
| `n_clusters_found` | ✔ | ✔ (ricontato dalle etichette) | ✘ | ✔ |
| Quota del cluster più grande | ✘ | ✔ (`density_metrics.csv`) | ✘ | ✔ |
| Curve filtrate per rumore | ✘ | ✔ (soglia 0.1 nel config) | ✔ (soglia 0.1 nel notebook) | ✘ |
| `probabilities_` (vicinanza al nucleo del proprio cluster) | ✘ | ✘ | ✘ | ✔ (soglia 0.5) |

### 3.3 HDBSCAN soft (pacchetto `hdbscan`)

Come 3.2 più le metriche del soft clustering. Non confrontabile con 3.2: altra implementazione, altre partizioni.

| Metrica | A sweep | B analisi tuning | C explorer | D/E/F produzione |
|---|---|---|---|---|
| Tutte quelle di 3.2 (tranne `probabilities_`) | ✔ | ✔ | ✘ (nessuna sezione per `hdbscan_soft`) | ✔ |
| `membership_mean` | ✔ media su tutti i soggetti non-rumore | ✔ | ✘ | ✘ a livello di run; per cluster c'è `own_mean` |
| `membership_share_below_half` | ✔ soglia fissa 0.5 | ✔ | ✘ | per cluster, soglia `LOW_MEMBERSHIP` = 0.5 |
| `persistence_mean` | ✔ | ✔ | ✘ | ✘ (in nessun punto di produzione) |
| Cluster "altro" più probabile, vettori medi, soggetti più deboli | ✘ | ✘ | ✘ | ✔ |

Su `membership_mean`: il tuning dà **un numero per combinazione**, la produzione dà **un numero per cluster**. Sono la stessa grandezza aggregata in modo diverso, e non c'è il passaggio dall'una all'altra.

---

## 4. Incoerenze trovate

Ordinate per quanto incidono sulla convergenza.

### 4.1 Copertura diversa tra tuning e produzione
Quando si sceglie una combinazione dal tuning si guardano silhouette, CH, DB. Quando la si guarda in produzione compaiono anche Dunn, silhouette macro e minima, quota del cluster più grande. Chi sceglie non ha visto quegli indici; chi valuta non ha le curve. Nei docs sperimentali (`docs/experiments/s2.4-vol.md`) la quota del cluster più grande è già un criterio di scelta, ma per agglomerative non esce dallo sweep.

### 4.2 "Usabile" non esiste nel codice
- `docs/experiments/s2.4-vol.md` usa "usabile = 3-30 cluster, rumore ≤ 25%, cluster più grande ≤ 60%" e conta le righe usabili.
- `README.md` (riga 97) dice che l'analisi del tuning scrive "a `usable` flag (HDBSCAN)": **non esiste più**. `clustering_tuning_analysis.py` dichiara l'opposto ("nothing classifies a combination as good, usable or stable").
- Il criterio vive quindi solo nella prosa dei docs, applicato a mano. È una soglia nostra, in contrasto con la regola "niente soglie arbitrarie nei report" (memoria di progetto).

### 4.3 Soglie duplicate, tutte "di esempio"

| Valore | Dove |
|---|---|
| rumore 0.10 | `embedding_app.py` (`NOISE_WARNING_FRACTION`), `clustering_evaluation.ipynb` cella 19, `clustering_tuning_explorer.ipynb` (`MAX_NOISE_FRACTION`), `config/pipelines/evaluate_clustering_tuning.json` (`curves_max_noise_fraction`) |
| probabilità 0.5 | `clustering_tuning.py` (`SOFT_MEMBERSHIP_LOW`, fissa nella definizione della colonna), `embedding_app.py` (`LOW_PROBABILITY`, `LOW_MEMBERSHIP`), `clustering_evaluation.ipynb` (stesse due, ridefinite) |

Cambiarne una non cambia le altre: il notebook può mostrare un 10% e l'app un 15% senza accorgersene.

### 4.4 Le fasce di Kaufman-Rousseeuw compaiono solo nel report del tuning
`report.md` (B) colloca la silhouette in fasce (0.71-1.00 forte, 0.51-0.70 ragionevole, 0.26-0.50 debole, ≤ 0.25 nessuna struttura). L'app (E) dice invece "nessuno dei quattro indici ha un valore di riferimento" e che una nuvola gaussiana senza cluster, divisa da ward, ha comunque silhouette ~0.4. Il notebook C dice che la silhouette "è l'unico che si legge da solo". Tre messaggi diversi sullo stesso numero. Le fasce sono una convenzione pubblicata, non una nostra soglia, ma la scelta di mostrarle in un posto solo va decisa. (21-10-26, superata in parte: le fasce sono ora anche in `knowledge/notes/dim_reduction_clustering/clustering_tuning_guide.md`, sezione «Fasce di valori: cosa dice la letteratura», e `docs/guides/evaluation.md` rimanda a quella sezione per la silhouette. Ricontrollato il resto: l'app dice ancora che nessuno dei quattro indici ha un valore di riferimento e che una nuvola senza cluster ha comunque silhouette ~0.4 (`embedding_app.py`, «Come leggere questi indici»; `docs/guides/embedding_app.md`, che rimanda alla guida per le fasce), e `clustering_evaluation.ipynb` (F) dice lo stesso. Il notebook C (`clustering_tuning_explorer.ipynb`, «Gli indici che compaiono») dice ancora che la silhouette «è l'unico dei tre che si legge da solo» e non cita le fasce: il disaccordo con l'app resta. `dendrogram_embedding_explorer.ipynb` non commenta la silhouette. 22-10-26, ulteriore aggiornamento: dal commit `417a852` il `report.md` non colloca più la silhouette nelle fasce, le cita soltanto; la decisione 3 del §6 non riguarda più il report.)

### 4.5 Geometria non euclidea: produzione incoerente col tuning
- Lo sweep di agglomerative calcola la silhouette nella `metric` giusta (matrice precomputata per cosine/manhattan).
- `silhouette_plot.png` di produzione usa `"euclidean"` fisso per ogni metodo tranne adp (`src/pipeline/clustering.py:427`). (22-10-26, superata dal commit `43a0ac4`: `_run_silhouette` usa la `metric` della run per agglomerative e ADP, `SILHOUETTE_OWN_METRIC_METHODS`; il pannello dell'app continua a rifiutare una run non euclidea.)
- Il pannello dell'app rifiuta invece una run non euclidea (`require_euclidean_compatible`).
- Oggi è **latente**: il registro ha `metric: euclidean` per agglomerative. Non ho controllato la `metric` di ogni singola run di produzione su disco, solo il registro e i nomi delle cartelle. Stessa famiglia di `lessons_learned.md` #15.

### 4.6 `clustering_comparison.ipynb`: homogeneity/completeness ancora scambiate
La cella 55 chiama `homogeneity_score(labels_a, labels_b)`, mentre il testo la descrive nella direzione opposta. La cella 54 è una nota "da sistemare"; il codice non è stato toccato. Risponde al thread aperto in `stato_progetto.md` ("verificare se il calcolo è stato corretto o solo annotato"): **solo annotato**. (21-10-26, superata: la cella 55 chiama ora `agreement_metrics(labels_a, labels_b)` di `src/analysis/cluster_comparison.py`, che passa B come «true» e A come «predicted», e la nota «da sistemare» è stata eliminata. Gli output salvati delle celle 37, 55, 69 e 71 sono ancora quelli vecchi finché il notebook non viene rieseguito.)

### 4.7 Tre posti per leggere il tuning, con contenuti diversi
- `report.md` (B): cophenetic, salto, ARI tra linkage, fasce, curve filtrate, `hdbscan_soft` incluso.
- Notebook C: ricalcola cophenetic da `X` invece di leggere `cophenetic_correlation.csv`; niente salto, niente ARI tra linkage; **nessuna sezione per `hdbscan_soft`**; soglia rumore propria.
- `tuning_plot.png` (A): heatmap/curve sugli indici dello sweep.

### 4.8 Una stabilità citata ma non prodotta da una pipeline
`s2.4-vol.md` (Decisioni) usa "ARI minimo al sottocampionamento 0.12-0.30" per HDBSCAN. Nel codice ho trovato la stabilità di Monti e il co-occurrence solo per kmeans/gmm/spectral (`consensus_clustering.py`), non per HDBSCAN o agglomerative. Il calcolo potrebbe venire da prototipi in `tmp/`: non l'ho verificato. Se non entra in `src/`, quella decisione non è riproducibile.

### 4.9 Minori
- L'app non calcola nulla su matrici con più di 1000 colonne (`MAX_QUALITY_COLUMNS`); per quelle serve il notebook F.
- `persistence_mean` esiste solo nel tuning di `hdbscan_soft`.
- Dunn è euclideo e quadratico: nessun problema sulle PCA/embedding (5845 soggetti), da non estendere alla matrice grezza.

---

## 5. Proposta: un insieme canonico

Idea: ogni metrica ha **una definizione, un punto di calcolo, una soglia (se serve) dichiarata una volta**. Tuning e produzione usano gli stessi nomi e le stesse funzioni.

### 5.1 Nucleo comune (tutti e tre i metodi, tuning e produzione)

| Metrica | Note |
|---|---|
| `n_clusters_found` | rumore escluso |
| `noise_fraction` | sempre accanto agli indici geometrici |
| `largest_cluster_share` | su tutti i soggetti, rumore compreso |
| `silhouette` (media sui soggetti) | nella `metric` della run |
| `silhouette_macro`, `silhouette_min` | oggi solo produzione |
| `davies_bouldin`, `calinski_harabasz` | solo euclidea, NaN altrimenti |
| `dunn` | da decidere se entra nel tuning (4.1) |

### 5.2 Specifiche per metodo

| Metodo | Metriche proprie |
|---|---|
| agglomerative | `cophenetic_correlation`, `dendrogram_jump`; ARI tra linkage resta una lettura del solo tuning |
| hdbscan | `probabilities_` (produzione) |
| hdbscan_soft | `membership_mean`, `membership_share_below_half`, `persistence_mean`; per cluster `own_mean`, cluster "altro" più probabile |

### 5.3 Soglie
Una sola fonte (config o costanti in un modulo), letta da app, notebook e `evaluate_clustering_tuning`. Nessuna soglia nuova: si tolgono i duplicati.

---

## 6. Decisioni che servono da te

1. **Nucleo comune**: ti va bene l'elenco di 5.1? In particolare, `silhouette_macro`/`silhouette_min`, `largest_cluster_share` e `dunn` devono entrare nello sweep, o restano solo di produzione?
2. **"Usabile"**: si abbandona del tutto (e si corregge il README), oppure diventa un filtro esplicito, parametrico e documentato, con i tre valori nel config?
3. **Fasce Kaufman-Rousseeuw**: restano solo nel report del tuning, vanno anche in app/notebook, o si tolgono?
4. **Soglie**: confermi di volerle in un'unica fonte? (rumore, probabilità 0.5)
5. **Dove si legge il tuning**: il `report.md` è la fonte canonica e il notebook C si riduce a ciò che il report non può fare (dendrogrammi interattivi)? Oppure il contrario?
6. **Stabilità per sottocampionamento** (4.8): va resa una funzione in `src/`, o la decisione su HDBSCAN si riscrive senza?
7. **Fix isolati** da fare a prescindere: scambio homogeneity/completeness (4.6), `silhouette_plot.png` euclideo fisso (4.5), riga sbagliata del README (4.2). (4.6 e 4.5: già corretti, vedi le note; 4.2: la riga del README non cita più il flag `usable`)

---

## 7. Cosa non ho verificato

- I valori reali delle metriche sulle run su disco (non ho riletto nessun `tuning_results.csv` se non la testata di uno).
- La `metric` di ogni run di produzione di agglomerative.
- Se i prototipi in `tmp/` calcolano già la stabilità citata in 4.8.
- Lo stato dei test per le funzioni citate.
