# Tuning del clustering — come leggere plot e indici

> **Implementazione:** 
> - `src/analysis/clustering_tuning.py` (calcolo indici/diagnostiche)
> - `src/analysis/plotting.py` (`plot_clustering_tuning_metrics`, `plot_dendrogram`, `plot_eigengap`)
> - Orchestrazione in `src/pipeline/clustering.py` quando `fine_tuning: true` (`dim_reduction_clustering.py`, il precedente CLI unico "riduci poi clusterizza", è stato ritirato il 14-08-26 — vedi `docs/dev/clustering_migration_plan.md`).
> 
> **Guida d'uso:** `docs/guides/clustering.md`.
> **Rassegna della letteratura** (origine di Davies-Bouldin, Silhouette, Rand/Jaccard/Fowlkes-Mallows, evidence accumulation): `knowledge/dim_reduction_clustering/clustering_literature_survey.md`. **Sfida "clusterizzare sopra un embedding"**: `knowledge/dim_reduction_clustering/challenge_of_clustering_after_dim_reduction.md`.

## Cos'è il tuning (e cosa NON è)

Per ogni metodo di clustering, il tuning esegue lo stesso algoritmo su una griglia di valori del suo iperparametro principale:
- `n_clusters` per KMeans, Agglomerative, Spectral
- `n_components` per GMM
- `min_cluster_size` per HDBSCAN
- `threshold` per Evidence Accumulation
*(Le griglie sono definite in `config/registry/params_clustering.json`)*

**Agglomerative sweepa anche `linkage` e `metric`** (non solo `n_clusters`) — ogni combinazione che accoppia `linkage="ward"` con una metrica diversa da euclidean/l2 è **scartata automaticamente** (con warning nel log), perché sklearn stesso non l'ammette (`AgglomerativeClustering`: "If linkage is 'ward', only 'euclidean' and 'l2' are accepted"). Le altre combinazioni (`average`/`complete`/`single` con qualunque metrica) sono tutte valide e vengono valutate.

Per ogni valore calcola un set di indici di validazione interna. Non essendoci un ground truth clinico disponibile, non ci sono metriche di accuratezza, ma solo misure di "quanto sono compatti e separati i cluster trovati".

**Il tuning non sceglie mai automaticamente il valore migliore.** 
Scrive solo i risultati (`tuning_results.csv` + `tuning_plot.png` + eventuali diagnostiche extra) sotto `<metodo>/tuning/<tag>/`. La scelta del valore da usare in produzione resta sempre una decisione umana, basata sull'osservazione dei plot — coerente con la filosofia generale del progetto (niente selezione automatica silenziosa).

Ogni `tuning_plot.png` è una griglia quadrata (definita da `_square_grid_shape`) di sotto-grafici a linea, uno per indice. Tutti i grafici condividono lo stesso asse x (il valore dell'iperparametro testato), ma non sono mai sovrapposti su un unico asse perché vivono su scale incomparabili tra loro.

## I 3 indici generici (calcolati per tutti e 6 i metodi)

| Indice | Range | Direzione | Cosa misura |
|---|---|---|---|
| **Silhouette** | `[-1, 1]` | Più alto = meglio | Per ogni punto, quanto è più vicino al proprio cluster rispetto al cluster estraneo più vicino.<br><br>• **Vicino a 1**: cluster compatti e separati<br>• **Vicino a 0**: cluster che si sovrappongono<br>• **Negativo**: punto probabilmente nel cluster sbagliato<br><br>*È l'unico dei tre con un range assoluto interpretabile.* Gli altri due si leggono solo per confronto relativo. |
| **Calinski-Harabasz** | `[0, +∞)` | Più alto = meglio | Rapporto tra dispersione *tra* i cluster e dispersione *dentro* i cluster. Tende quasi sempre a **crescere con k** (più cluster piccoli = più dispersione tra loro). Da solo non è affidabile per scegliere k, va letto come tendenza/conferma. |
| **Davies-Bouldin** | `[0, +∞)` | Più basso = meglio | Media del rapporto tra "quanto è disperso al suo interno" e "quanto è vicino al cluster più simile a lui". È l'unico dei tre che penalizza esplicitamente due cluster troppo vicini tra loro, motivo per cui a volte diverge dal Silhouette. |

> **Nota per HDBSCAN:** I punti classificati come rumore (label `-1`) sono **esclusi** da questi 3 indici, poiché non avrebbero senso per una "non-classe". La frazione di rumore è sempre riportata separatamente (`noise_fraction`), mai nascosta.

> **Nota su `clustering.py` lanciato direttamente sulla matrice voxel grezza** (non sull'embedding, opzione permessa ma sconsigliata dalla guida d'uso): tutti e 3 gli indici usano di default la distanza **euclidea** (per Calinski-Harabasz/Davies-Bouldin non è nemmeno configurabile — sono definiti solo su quella geometria). Su voxel binari l'euclidea è dominata dal **volume** della lesione più che dalla sua forma/posizione, in modo pesante e senza alcun limite superiore — lo stesso identico problema per cui `dim_reduction.py` offre `metric: jaccard/dice`. Non è un disallineamento tra "come clusterizzo" e "come valuto" (KMeans/Agglomerative-ward/GMM sono anche loro intrinsecamente euclidei, quindi indice e algoritmo restano coerenti tra loro) — è che entrambi condividono lo stesso bias di fondo. Su un **embedding** (workflow raccomandato: `dim_reduction.py` seguito da `clustering.py --reduced_data true`) il bias è **attenuato**, non eliminato: anche se costruito con jaccard/dice, quelle metriche restano dipendenti dal volume per costruzione (`Dice(A,B) ≤ 2·min(|A|,|B|)/(|A|+|B|)` — vedi `dim_reduction_literature_survey.md`), quindi un residuo di segnale legato al volume può sopravvivere nell'embedding e propagarsi al clustering fatto sopra. Le coordinate finali sono comunque uno spazio continuo per costruzione, quindi l'euclidea lì resta la scelta geometricamente corretta (nessun disallineamento metrico) — solo il bias-volume a monte non è garantito essere del tutto sparito.
>
> Corollario pratico: **`dice`/`jaccard` non vanno mai messi nella `tuning_grid.metric` di Agglomerative quando l'input è un embedding** (`reduced_data: true`) — sono metriche per vettori booleani, non per coordinate continue; sklearn/scipy le applicherebbero comunque, binarizzando silenziosamente i valori non-zero, producendo un numero senza significato geometrico invece di un errore. `config/registry/params_clustering.json` tiene `agglomerative.tuning_grid.metric` a `["euclidean", "cosine", "manhattan"]` per questo — indipendentemente dalla metrica (euclidean/dice/...) usata a monte per costruire l'embedding stesso.

> **Nota su Agglomerative e `metric` non-euclidea**: quando `metric` è sweepato, Silhouette resta sempre calcolabile per qualunque metrica (thread della stessa metrica usata per il fit dentro `silhouette_score`, coerente con la lezione sul disallineamento metrica-di-fit/metrica-di-score) — ma Calinski-Harabasz e Davies-Bouldin sono per costruzione basati su centroidi/geometria euclidea (non esiste nemmeno un parametro `metric` per loro in sklearn) e vengono registrati come `NaN`, non stimati approssimativamente, per ogni combinazione con `metric != "euclidean"`. Nella lettura dei plot/CSV di una sweep `metric`-mista, aspettarsi colonne CH/DB vuote per le righe non-euclidee è normale, non un bug.

**Come leggerli insieme:**
- Se Silhouette, Calinski-Harabasz e Davies-Bouldin concordano tutti sullo stesso `k`, la scelta è solida.
- Se **Silhouette preferisce un k diverso da Davies-Bouldin** (pattern osservato spesso nei dati NEMESIS, es. con pacmap: Silhouette premia `k=2`, Davies-Bouldin premia `k=6`), è un segnale reale di tensione strutturale nei dati:
  - *Pochi macro-gruppi molto separati*: favoriscono `k` piccolo e alto Silhouette.
  - *Sottogruppi più compatti al loro interno*: favoriscono `k` alto e basso Davies-Bouldin.
- **Risoluzione:** Non c'è una regola meccanica per risolvere il conflitto. Va deciso guardando anche la diagnostica standalone del metodo (dendrogramma, eigengap) e il contesto clinico.

## Diagnostiche extra per metodo

### KMeans — `inertia` (elbow)
- **Dove:** Colonna aggiuntiva nello stesso `tuning_plot.png`.
- **Cosa misura:** Somma delle distanze al quadrato di ogni punto dal centroide del proprio cluster.
- **Come si legge:** **Scende sempre** all'aumentare di `k`, quindi non si cerca il minimo ma il "gomito" (dove la curva smette di scendere ripidamente e rallenta, indicando che aggiungere altri cluster non spiega molta varianza aggiuntiva). Da solo tende a essere poco decisivo se non c'è un gomito netto; va incrociato con Silhouette o Davies-Bouldin.

### Agglomerative — dendrogramma (`dendrogram.png` / `dendrogram_<linkage>.png`)
- **Dove:** Diagnostica **standalone**, indipendente dal `k` scelto. **Un dendrogramma per ogni valore di `linkage` sweepato** (`dendrogram_ward.png`, `dendrogram_average.png`, ... — se `linkage` non è nella `tuning_grid`, un solo `dendrogram.png` sul `linkage` di `base_params`). Ognuno è calcolato una sola volta e troncato alle ultime 30 fusioni per leggibilità.
- **Come si legge:** Dal basso verso l'alto. Ogni fusione verticale unisce due sotto-cluster alla "merge distance" (asse y).
- **Interpretazione:** **Il salto verticale più grande tra due fusioni consecutive indica il taglio più naturale**.
  - Salto grande vicino alla radice (in cima) ➔ la struttura più forte è binaria (`k=2`).
  - Salto grande più in basso ➔ suggerisce un `k` maggiore.
- **Attenzione:** Il colore dei rami (default matplotlib) segue una soglia automatica e non va interpretato come "numero di cluster consigliato". Ciò che conta è la dimensione dei salti sull'asse y.
- **Forma del dendrogramma dipende dal `linkage` usato** — confrontare i diversi `dendrogram_<linkage>.png` tra loro è parte della lettura, non solo guardarne uno: `ward` (default nel progetto) minimizza l'aumento di varianza interna e tende a fusioni più regolari, simili per forma a KMeans; `average`/`complete` sono meno vincolati nella forma dei cluster ma più sensibili a outlier; `single` in particolare tende a incatenare gruppi distinti attraverso pochi punti-ponte (*chaining effect*), producendo salti meno netti e un dendrogramma meno affidabile per scegliere `k` a colpo d'occhio.

### Agglomerative — interclass distance matrix (`interclass_distance_matrix.png`)
- **Dove:** Diagnostica **standalone**, indipendente dal `k` scelto — un pre-check di selezione della `metric`, non del clustering vero e proprio (modellata su `plot_agglomerative_clustering_metrics` di sklearn). **Un heatmap per ogni valore di `metric` sweepato** (o la sola metrica di `base_params`/`"euclidean"` se `metric` non è sweepato). **Scritta solo se `metadata` ha una colonna `dataset`** — altrimenti saltata con un warning nel log, non è un fallimento della sweep.
- **Cosa misura:** Usa `dataset` come proxy debole di "ground truth" (non è un clustering, solo un raggruppamento noto a priori) e calcola la distanza media dentro ogni gruppo (diagonale) e tra coppie di gruppi (fuori diagonale), per ciascuna `metric` candidata.
- **Come si legge:** Una `metric` "migliore" per quello spazio tiene la diagonale bassa (gruppi compatti al loro interno) e le celle fuori diagonale alte (gruppi ben separati tra loro). Non dice nulla sul `k` scelto — è un criterio per scegliere quale voce di `tuning_grid.metric` guardare più da vicino, prima ancora di leggere Silhouette/CH/DB per quella metrica.

### Evidence Accumulation — convergenza e consensus matrix
Diagnostiche **standalone**, calcolate una sola volta da `base_params` (indipendenti dal `threshold`/`n_clusters` sweepati):
- **`n_repeats_convergence.csv`/`.png`**: verifica se la matrice di co-occorrenza si stabilizza davvero al crescere di `n_repeats`, o se il valore in `base_params` è arbitrario — checkpoint incrementali (10/25/50/75/100% di `base_params.n_repeats`), mai rifittato da zero per ciascun valore.
- **`consensus_matrix_heatmap.png`**: la visualizzazione originale di Monti et al. 2003 — la matrice di co-occorrenza (quante volte due soggetti finiscono nello stesso cluster tra le `n_repeats` ripetizioni) riordinata secondo l'assegnazione finale (`base_params.threshold`). Blocchi diagonali netti = cluster confidenti/puliti a quella soglia; zone sfumate = un taglio ambiguo.

### GMM — `bic` / `aic` (criteri basati su verosimiglianza)
- **Dove:** Colonne aggiuntive nello stesso `tuning_plot.png`.
- **Cosa misurano:** A differenza dei 3 indici puramente geometrici, penalizzano la complessità del modello (più componenti = rischio di overfitting) bilanciandola con quanto bene il modello spiega i dati.
- **Come si leggono:** Più basso = meglio. 
- **Attenzione:** Se scendono in modo monotono su tutta la griglia senza mai risalire, non stanno dando un'informazione utile in quel range (la griglia non arriva al punto di svolta). In questo caso, usare i 3 indici generici.

### HDBSCAN — `noise_fraction` (nessuna diagnostica standalone)
- **Noise fraction:** Colonna aggiuntiva in `tuning_plot.png`. **Va sempre letta insieme agli altri indici, mai da sola**. Un `min_cluster_size` grande può dare indici ottimi solo perché scarta molti soggetti difficili considerandoli rumore (i pochi rimasti sembrano ben separati). È un vero **trade-off qualità/copertura**.
- **Nessun grafico standalone**: a differenza del vecchio DBSCAN (che aveva un k-distance plot per stimare `eps` a occhio), HDBSCAN non ha una singola soglia di distanza da leggere su un grafico — `min_cluster_size` si giudica direttamente dalla curva `noise_fraction`/silhouette già sweepata.

### Spectral — eigengap (`eigengap_plot.png`)
- **Dove:** Diagnostica **standalone**, calcolata una sola volta e indipendente dal `k`.
- **Cosa misura:** Si basa sugli autovalori del Laplaciano normalizzato del grafo di affinità tra i punti.
- **Come si legge:** Il `k` consigliato è l'indice giusto prima del **salto più grande** tra due autovalori consecutivi (spesso marcato in rosso nel plot). È un criterio più fondato rispetto agli indici generici per lo spectral clustering, poiché riflette la connettività del grafo usata dall'algoritmo internamente.

## Diagnostiche di stabilità — due meccanismi distinti, entrambi opzionali

Gli indici sopra dicono "quanto è buono" un singolo risultato di clustering a un dato `k`. Ci sono due meccanismi separati, entrambi opt-in via una chiave opzionale nell'entry del metodo in `config/registry/params_clustering.json`, che invece dicono "quanto è **stabile**" — rispondono a due domande diverse e non vanno confusi:

### 1. Stability analysis (`"stability"`, solo KMeans/GMM) — nuisance parameter init/n_init

Domanda: *prima ancora di fidarsi della sweep sul parametro target (`n_clusters`/`n_components`), il risultato dipende in modo instabile dall'inizializzazione casuale?* KMeans e GMM sono gli unici 2 metodi la cui fit dipende da un'inizializzazione casuale che la sweep normale non valida da sola — `n_clusters`/`n_components` è l'iperparametro target, `init`/`n_init` è un "nuisance parameter" da controllare a parte, mai in una griglia congiunta target×init (esplicitamente scartata in fase di design, vedi memoria `project-clustering-tuning-redesign`).

- **Dove:** `stability_results.csv` + `stability_plot.png`, scritti nella stessa cartella della sweep — **solo se il metodo ha una chiave `"stability"` in `params_clustering.json`** (oggi presente per `kmeans`/`gmm`, quindi generati automaticamente a ogni loro run di tuning, non serve richiederli a parte).
- **Cosa fa:** Ripete il fit `n_repeats` volte per ogni combinazione (valore rappresentativo di `n_clusters`/`n_components` — min/mediana/max della `tuning_grid`, non l'intera griglia × valore di `init`/`init_params` × valore di `n_init`), variando solo il seed, e registra `inertia` (kmeans) / `bic` (gmm).
- **Come si legge:** Un pannello per valore rappresentativo del parametro target; dentro, una linea per valore di `init`/`init_params`, errorbar (media ± std) su `n_init`. Una linea che si appiattisce presto (bassa varianza già a `n_init` piccolo) e resta bassa indica un'inizializzazione stabile — se invece la varianza resta alta anche a `n_init` grande, i punteggi della sweep principale per quel target value sono meno affidabili di quanto sembrino, perché dipendono dal seed più che dal vero `k`/`n_components`.

### 2. Consensus/RSC/Monti (`"consensus"`, KMeans/GMM/Spectral) — stabilità del `k` stesso

Domanda diversa: *il `k` scelto è supportato dai dati, o dipenderebbe da chi capita nel campione/nell'inizializzazione?* Un blocco `"consensus"` opzionale in config (formato JSON in `docs/guides/clustering.md`) attiva due diagnostiche aggiuntive nello stesso `tuning_results.csv` (colonne `rsc_eigengap`/`monti_stability`) — disponibili solo per KMeans/GMM/Spectral (gli unici con vera casualità interna da sfruttare):

- **RSC** — stessi dati, semi casuali diversi: quanto viene riprodotto lo stesso risultato al variare solo dell'inizializzazione.
- **Monti** — sottocampioni casuali diversi di soggetti: quanto il risultato dipende da chi capita nel campione (dettagli letteratura: `clustering_literature_survey.md`).

Entrambe usano la stessa matrice di co-associazione dell'evidence accumulation (`clustering_literature_survey.md` §3-4), ma qui restano un punteggio diagnostico per-`k` — non producono etichette finali, a differenza del metodo `"evidence_accumulation"` che è un metodo di produzione a sé (e ha le proprie diagnostiche standalone, vedi sopra).

## File di output per una run di tuning

Per ogni combinazione `<metodo>/tuning/<tag>/` vengono sempre generati:

- `tuning_results.csv`: una riga per ogni valore testato, contiene tutte le colonne previste in `METHOD_METRIC_COLUMNS[metodo]` (più `rsc_eigengap`/`monti_stability` se `"consensus"` è configurato).
- `tuning_plot.png`: griglia di sotto-grafici (es. 2×2 o 3×3), uno per indice. L'uso della griglia evita di comprimere eccessivamente i grafici. Le eventuali celle vuote in eccesso vengono nascoste. **Generato solo se la `tuning_grid` ha esattamente 1 o 2 parametri sweepati** (per Spectral con `affinity` sweepato, la regola si applica ai parametri sweepati *oltre* `affinity`/`n_neighbors`/`gamma`) — con 3+ parametri (es. Agglomerative con `n_clusters` × `linkage` × `metric`, la config di default in `params_clustering.json`) **non viene generato nessun plot aggregato**, solo un warning nel log: `tuning_results.csv` + le diagnostiche standalone del metodo restano l'unico modo di leggere quella sweep.
- `config.md`: snapshot dei parametri utilizzati per quella specifica run.

Diagnostiche **standalone** (indipendenti dal valore scelto nella griglia), solo per il metodo indicato:

| File | Metodo | Sempre presente? |
|---|---|---|
| `dendrogram_<linkage>.png` (uno per `linkage` sweepato) o `dendrogram.png` (fallback se `linkage` non è sweepato) | Agglomerative | Sì |
| `interclass_distance_matrix.png` | Agglomerative | Solo se `metadata` ha una colonna `dataset` |
| `eigengap_plot.png` | Spectral | Sì |
| `n_repeats_convergence.csv`/`.png` | Evidence Accumulation | Sì |
| `consensus_matrix_heatmap.png` | Evidence Accumulation | Sì |

Output **opt-in** (solo se la chiave corrispondente è presente per quel metodo in `params_clustering.json` — vedi sezione "Diagnostiche di stabilità" sopra):

| File | Metodo | Chiave config |
|---|---|---|
| `stability_results.csv`/`stability_plot.png` | KMeans, GMM | `"stability"` |
| Colonne `rsc_eigengap`/`monti_stability` in `tuning_results.csv` (nessun file a parte) | KMeans, GMM, Spectral | `"consensus"` |

`save_tuning_clusterings: true` in config aggiunge anche `clusterings.npz` (le etichette effettive di ogni combinazione, per riuso successivo — non ricalcolate) — **non supportato per Spectral quando `affinity` è sweepato** (le chiavi delle sotto-sweep per-affinity non sono allineabili in modo affidabile, vedi `src/pipeline/clustering.py::_run_one_method_tuning`); in quel caso va disattivato o si lancia Spectral in una run separata dagli altri metodi.
