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
*(Le griglie sono definite in `config/registry/params_clustering.json`)*

Per ogni valore calcola un set di indici di validazione interna. Non essendoci un ground truth clinico disponibile, non ci sono metriche di accuratezza, ma solo misure di "quanto sono compatti e separati i cluster trovati".

**Il tuning non sceglie mai automaticamente il valore migliore.** 
Scrive solo i risultati (`tuning_results.csv` + `tuning_plot.png` + eventuali diagnostiche extra) sotto `<metodo>/tuning/<tag>/`. La scelta del valore da usare in produzione resta sempre una decisione umana, basata sull'osservazione dei plot — coerente con la filosofia generale del progetto (niente selezione automatica silenziosa).

Ogni `tuning_plot.png` è una griglia quadrata (definita da `_square_grid_shape`) di sotto-grafici a linea, uno per indice. Tutti i grafici condividono lo stesso asse x (il valore dell'iperparametro testato), ma non sono mai sovrapposti su un unico asse perché vivono su scale incomparabili tra loro.

## I 3 indici generici (calcolati per tutti e 5 i metodi)

| Indice | Range | Direzione | Cosa misura |
|---|---|---|---|
| **Silhouette** | `[-1, 1]` | Più alto = meglio | Per ogni punto, quanto è più vicino al proprio cluster rispetto al cluster estraneo più vicino.<br><br>• **Vicino a 1**: cluster compatti e separati<br>• **Vicino a 0**: cluster che si sovrappongono<br>• **Negativo**: punto probabilmente nel cluster sbagliato<br><br>*È l'unico dei tre con un range assoluto interpretabile.* Gli altri due si leggono solo per confronto relativo. |
| **Calinski-Harabasz** | `[0, +∞)` | Più alto = meglio | Rapporto tra dispersione *tra* i cluster e dispersione *dentro* i cluster. Tende quasi sempre a **crescere con k** (più cluster piccoli = più dispersione tra loro). Da solo non è affidabile per scegliere k, va letto come tendenza/conferma. |
| **Davies-Bouldin** | `[0, +∞)` | Più basso = meglio | Media del rapporto tra "quanto è disperso al suo interno" e "quanto è vicino al cluster più simile a lui". È l'unico dei tre che penalizza esplicitamente due cluster troppo vicini tra loro, motivo per cui a volte diverge dal Silhouette. |

> **Nota per HDBSCAN:** I punti classificati come rumore (label `-1`) sono **esclusi** da questi 3 indici, poiché non avrebbero senso per una "non-classe". La frazione di rumore è sempre riportata separatamente (`noise_fraction`), mai nascosta.

> **Nota su `clustering.py` lanciato direttamente sulla matrice voxel grezza** (non sull'embedding, opzione permessa ma sconsigliata dalla guida d'uso): tutti e 3 gli indici usano di default la distanza **euclidea** (per Calinski-Harabasz/Davies-Bouldin non è nemmeno configurabile — sono definiti solo su quella geometria). Su voxel binari l'euclidea è dominata dal **volume** della lesione più che dalla sua forma/posizione, in modo pesante e senza alcun limite superiore — lo stesso identico problema per cui `dim_reduction.py` offre `metric: jaccard/dice`. Non è un disallineamento tra "come clusterizzo" e "come valuto" (KMeans/Agglomerative-ward/GMM sono anche loro intrinsecamente euclidei, quindi indice e algoritmo restano coerenti tra loro) — è che entrambi condividono lo stesso bias di fondo. Su un **embedding** (workflow raccomandato: `dim_reduction.py` seguito da `clustering.py --reduced_data true`) il bias è **attenuato**, non eliminato: anche se costruito con jaccard/dice, quelle metriche restano dipendenti dal volume per costruzione (`Dice(A,B) ≤ 2·min(|A|,|B|)/(|A|+|B|)` — vedi `dim_reduction_literature_survey.md`), quindi un residuo di segnale legato al volume può sopravvivere nell'embedding e propagarsi al clustering fatto sopra. Le coordinate finali sono comunque uno spazio continuo per costruzione, quindi l'euclidea lì resta la scelta geometricamente corretta (nessun disallineamento metrico) — solo il bias-volume a monte non è garantito essere del tutto sparito.

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

### Agglomerative — dendrogramma (`dendrogram.png`)
- **Dove:** Diagnostica **standalone**, indipendente dal `k` scelto. È calcolata una sola volta (troncata alle ultime 30 fusioni per leggibilità).
- **Come si legge:** Dal basso verso l'alto. Ogni fusione verticale unisce due sotto-cluster alla "merge distance" (asse y).
- **Interpretazione:** **Il salto verticale più grande tra due fusioni consecutive indica il taglio più naturale**.
  - Salto grande vicino alla radice (in cima) ➔ la struttura più forte è binaria (`k=2`).
  - Salto grande più in basso ➔ suggerisce un `k` maggiore.
- **Attenzione:** Il colore dei rami (default matplotlib) segue una soglia automatica e non va interpretato come "numero di cluster consigliato". Ciò che conta è la dimensione dei salti sull'asse y.
- **Forma del dendrogramma dipende dal `linkage` usato** — da tenere presente quando lo si legge: `ward` (default nel progetto) minimizza l'aumento di varianza interna e tende a fusioni più regolari, simili per forma a KMeans; `average`/`complete` sono meno vincolati nella forma dei cluster ma più sensibili a outlier; `single` in particolare tende a incatenare gruppi distinti attraverso pochi punti-ponte (*chaining effect*), producendo salti meno netti e un dendrogramma meno affidabile per scegliere `k` a colpo d'occhio.

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

## Diagnostica di stabilità (RSC/Monti) — distinta dal tuning sopra

Gli indici sopra dicono "quanto è buono" un singolo risultato di clustering a un dato `k`. Un blocco `"consensus"` opzionale in config (formato JSON in `docs/guides/clustering.md`) attiva invece due diagnostiche che dicono "quanto è **stabile**" un certo `k`, ripetendo il clustering più volte — disponibili solo per KMeans/GMM/Spectral (gli unici con vera casualità interna da sfruttare):

- **RSC** — stessi dati, semi casuali diversi: quanto viene riprodotto lo stesso risultato al variare solo dell'inizializzazione.
- **Monti** — sottocampioni casuali diversi di soggetti: quanto il risultato dipende da chi capita nel campione (dettagli letteratura: `clustering_literature_survey.md`).

Entrambe usano la stessa matrice di co-associazione dell'evidence accumulation (`clustering_literature_survey.md` §3-4), ma qui restano un punteggio diagnostico — non producono etichette finali, a differenza del metodo `"evidence_accumulation"` che è un metodo di produzione a sé.

## File di output per una run di tuning

Per ogni combinazione `<riduzione>/<metodo>/tuning/<tag>/` vengono generati:

- `tuning_results.csv`: una riga per ogni valore testato, contiene tutte le colonne previste in `METHOD_METRIC_COLUMNS[metodo]`.
- `tuning_plot.png`: griglia di sotto-grafici (es. 2×2 o 3×3), uno per indice. L'uso della griglia evita di comprimere eccessivamente i grafici. Le eventuali celle vuote in eccesso vengono nascoste.
- **Diagnostiche standalone:**
  - `dendrogram.png` (solo per Agglomerative)
  - `eigengap_plot.png` (solo per Spectral)
- `config.md`: snapshot dei parametri utilizzati per quella specifica run.
