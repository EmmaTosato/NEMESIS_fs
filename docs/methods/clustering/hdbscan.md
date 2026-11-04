# HDBSCAN in NEMESIS

- **Teoria:** [HDBSCAN: versione hard (`hdbscan`) e soft (`hdbscan_soft`)](../../../knowledge/concepts/Machine_Learning/Unsupervised/Clustering/hdbscan.md)
  (Learning: `2_Concepts/Machine_Learning/Unsupervised/Clustering/hdbscan.md`)
- **Letteratura:** nei `sources` della nota teorica
- **Spiegazione rapida:** [cheatsheet](../../../management/cheatsheets/hdbscan.md) (derivata, non è una fonte)

Due metodi di `CLUSTERING_METHODS` (`src/analysis/clustering.py`) con lo stesso algoritmo e due implementazioni:
- **`hdbscan`:** `sklearn.cluster.HDBSCAN` (scikit-learn 1.8.0, ambiente `nemesis`). Un'etichetta per soggetto.
- **`hdbscan_soft`:** `hdbscan.HDBSCAN` del pacchetto `hdbscan` (0.8.44), l'implementazione di riferimento di McInnes, Healy & Astels.
  In più dà, per ogni soggetto, una probabilità per ogni cluster (*soft clustering*).

Parametri: `config/registry/params_clustering.json`. Cosa offre il pacchetto e come si legge dopo il fit: [hdbscan_package](hdbscan_package.md).
Altri metodi: [README](README.md). Metriche condivise: [evaluation_metrics](../../../knowledge/concepts/Machine_Learning/Unsupervised/Clustering/evaluation_metrics.md).

## Su cosa lo applichiamo
- **Input:** embedding UMAP (`n_components` 2, 3, 10), punteggi PCA (2-42 componenti) o la matrice SDC "stream" a 87 colonne; circa 5000-5850 soggetti.
- **Distanza:** euclidea (non è passata `metric`).
- **Dimensioni:** la FAQ del pacchetto indica HDBSCAN adatto fino a circa 50-100 dimensioni; i nostri spazi (2-87) rientrano.
  Sulle matrici di voxel (centinaia di migliaia di colonne) la densità sarebbe poco informativa: per quelle il progetto usa ADP ([adp](adp.md)).
- **Tempi** ([guida al clustering](../../guides/clustering.md)): circa 30-55 secondi per 56 combinazioni su un embedding UMAP di 5845 soggetti.

## Parametri usati (significato: documentazione scikit-learn e `hdbscan`)
Griglie:
- `hdbscan`: `min_cluster_size` ∈ {10, 15, 20, 30, 50, 75, 100} × `min_samples` ∈ {1, 5, 10, 20} = 28 combinazioni; base 100/10.
- `hdbscan_soft`: le stesse × `cluster_selection_method` ∈ {eom, leaf} = 56 combinazioni.

| Parametro | Nel progetto |
|---|---|
| `min_cluster_size` | sweep 10-100 |
| `min_samples` | sweep 1-20 |
| `cluster_selection_method` | `eom` (hard, resta il default); sweep (soft) |
| `approx_min_span_tree` | `False` fisso (soft); il default del pacchetto è `True` |
| `prediction_data` | `True` (soft), forzato in `hdbscan_soft_fit`; il default del pacchetto è `False` |
| `cluster_selection_epsilon`, `alpha`, `allow_single_cluster`, `max_cluster_size`, `metric`, `algorithm`, `cluster_selection_persistence`, `cluster_selection_epsilon_max`, `match_reference_implementation` | default |

Requisiti del soft clustering: `prediction_data=True`; non funziona con `metric="precomputed"`.

## Come lo ottimizziamo
La documentazione del pacchetto consiglia di partire da `min_cluster_size` (la taglia più piccola che si vuole chiamare cluster) e di usare `min_samples`
per rendere il metodo più o meno conservativo. Il progetto li sweepa insieme in una sola run:
1. **Colonne di `tuning_results.csv`** (valutazione `density_metrics`, dopo lo sweep o su un tuning già salvato): `largest_cluster_share` (sul totale dei soggetti)
   e `dbcv`, accanto a `n_clusters_found` dello sweep.
2. **Heatmap** `min_cluster_size` × `min_samples` (valutazione `tuning_heatmaps`, `tuning_plot.png`; per `hdbscan_soft` una per `cluster_selection_method`)
   di DBCV, rumore, quota del cluster più grande, numero di cluster e, per `hdbscan_soft`, probabilità media e persistenza.
3. **Curve** (valutazione `dbcv_curves`, `dbcv_curves*.png`): DBCV, rumore, quota del cluster più grande e numero di cluster contro `min_cluster_size`,
   una linea per `min_samples`. Tutte le combinazioni, nessun limite sul rumore.
4. **Per `hdbscan_soft`:** `membership_mean` e `persistence_mean`, senza soglia sulla probabilità.
5. **Tra embedding:** ARI tra le run (`agreement_metrics` conta il rumore come un gruppo a sé; confronto tra più run: non è nel `report.md` di una singola run).

Cosa cercare: una zona della griglia dove numero di cluster e partizione cambiano poco e il rumore resta basso.
Lettura dei grafici: [clustering_tuning_guide](clustering_tuning_guide.md), "HDBSCAN".

## Come leggiamo l'output
- **Frazione di rumore** e **numero di cluster trovati**, sempre ([evaluation_metrics](../../../knowledge/concepts/Machine_Learning/Unsupervised/Clustering/evaluation_metrics.md), §6).
- **DBCV** ([evaluation_metrics](../../../knowledge/concepts/Machine_Learning/Unsupervised/Clustering/evaluation_metrics.md), §8): pesa il rumore, quindi non premia chi scarta i soggetti difficili.
  Silhouette, CH, DB e Dunn non si calcolano per HDBSCAN: sui soli soggetti non rumore salgono con il rumore, e presuppongono cluster compatti.
- **Stabilità** (`persistence_mean`, solo soft): i cluster persistono su un ampio intervallo di densità?
- **`probabilities_`** (hard) e **vettori soft**, nel pannello "Clustering evaluation" dell'app Dash: quanti soggetti stanno al margine del loro cluster, e quali cluster si contendono soggetti.
- **Soft, soggetto con etichetta $c$:** la colonna $c$ è "quanto appartiene al proprio cluster" (`membership_own`); il rumore riceve comunque un vettore,
  che dice a quale cluster è più vicino (`soft_membership_matrix`, `own_cluster_membership`).
- **`outlier_scores_`** (GLOSH) non è usato dal progetto.

## Attenzioni specifiche
- **`min_samples` ha convenzioni diverse nei due metodi.** scikit-learn conta il punto stesso tra i vicini e il suo docstring dice che, per avere lo stesso risultato,
  il suo `min_samples` deve essere **1 in più** di quello del pacchetto. Il pacchetto, nel codice, cerca `min_samples + 1` vicini e prende l'ultimo: il punto stesso non conta.
  Il suo docstring dice il contrario; il comportamento corrisponde al codice e alla pagina "How HDBSCAN Works" (misurato anche sui dati NEMESIS, vedi [hdbscan_package](hdbscan_package.md)).
- **`min_samples = 1` non significa la stessa cosa nei due metodi.** In scikit-learn la core distance è la distanza da sé stessi, cioè 0, e HDBSCAN diventa single linkage
  sulle distanze originali più la condensazione; nel pacchetto è la distanza dal primo vicino vero. Le run `hdbscan` e `hdbscan_soft` della stessa griglia non si confrontano combinazione per combinazione.
- **`min_samples` non fissato** vale `min_cluster_size` e cambia insieme a lui: il progetto lo fissa sempre.
- **Dopo UMAP:** `probabilities_` su un embedding molto impacchettato descrive l'impacchettamento, non la densità dei dati originali (`docs/guides/embedding_app.md`).
- **Molti cluster minuscoli:** con `min_cluster_size` piccolo rispetto a $n$ si possono ottenere decine o centinaia di cluster (`docs/experiments/s1.2-vol.md`, 143 cluster);
  `n_clusters_found` va guardato sempre.
- **`cluster_selection_epsilon`** è in unità dello spazio: su un embedding UMAP la scala delle coordinate non ha significato fisico, il progetto non lo usa.
