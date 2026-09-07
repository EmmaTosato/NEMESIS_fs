# Diario Esperimenti

**Pipeline:** Dim Reduction (Produzione)

**Dati:** Matrice raw (feature matrix, pre-riduzione)

**Sessione:** s2

**Tipo di dati**: Structural Disconnection (SDC) Data

**Origine**: data/derived/sdc_matrix

**Note**
- Parametri scelti a valle del tuning ([`s2_tuning.md`](s2_tuning.md)).
- Vedi data_sessions.md per specifica sulle sessioni

---

## 31-08-2026 — s2.1-schaefer-200-tian-s2

### Prima produzione UMAP + t-sne 

##### Input
- s2.1-schaefer-200-tian-s2
- Dati raw: matrice SDC region-wise 
	- `schaefer_200_tian_s2`
	- `disconnectome`/`mean_overlap
- Path: `data/derived/sdc_matrix/27-08_s2.1-schaefer-200-tian-s2`
- 1119 soggetti × 232 regioni
##### Metodi
umap, tsne

##### Obiettivo
- Produrre i primi embedding SDC di produzione dopo il tuning (28-08)

##### Risultati

| ID | Metodo | n_neighbors | min_dist | perplexity | n_components | Link |
| --- | --- | --- | --- | --- | --- | --- |
| s2.1-schaefer-200-tian-s2_nc2 | UMAP | 15 | 0.0 | — | 2 | [config.md](../../../results/sdc/dim_reduction/production/umap/31-08_s2.1-schaefer-200-tian-s2_m_euclidean_nc2/config.md) |
| s2.1-schaefer-200-tian-s2_nc3 | UMAP | 15 | 0.0 | — | 3 | [config.md](../../../results/sdc/dim_reduction/production/umap/31-08_s2.1-schaefer-200-tian-s2_m_euclidean_nc3/config.md) |
| s2.1-schaefer-200-tian-s2 | t-SNE | — | — | 30 | 2 | [config.md](../../../results/sdc/dim_reduction/production/tsne/31-08_s2.1-schaefer-200-tian-s2_m_euclidean_p_30/config.md) |

- `s2.1-schaefer-200-tian-s2_nc3`: stessi parametri baseline della run 2D gemella (`s2.1-schaefer-200-tian-s2_nc2`),

---

## 07-09-2026 — s2.2-vol

### Produzione UMAP + t-SNE su SDC voxel-wise

##### Input
- s2.2-vol
- Dati raw: matrice SDC **voxel-wise** (`disconnectome-map` non parcellate, valori continui 0-1)
- Path: `data/derived/sdc_matrix/07-09_s2.2-vol`
- 1570 soggetti × 290.940 voxel

##### Metodi
umap, tsne

##### Obiettivo
- Produrre gli embedding di riferimento della rappresentazione voxel-wise, con **gli stessi tre artefatti e gli stessi parametri** di s2.1 — così l'unica variabile tra le due sessioni resta la rappresentazione

##### Risultati

| ID | Metodo | n_neighbors | min_dist | perplexity | n_components | Link |
| --- | --- | --- | --- | --- | --- | --- |
| s2.2-vol_nc2 | UMAP | 15 | 0.0 | — | 2 | [config.md](../../../results/sdc/dim_reduction/production/umap/07-09_s2.2-vol_m_euclidean_nc2/config.md) |
| s2.2-vol_nc3 | UMAP | 15 | 0.0 | — | 3 | [config.md](../../../results/sdc/dim_reduction/production/umap/07-09_s2.2-vol_m_euclidean_nc3/config.md) |
| s2.2-vol | t-SNE | — | — | 30 | 2 | [config.md](../../../results/sdc/dim_reduction/production/tsne/07-09_s2.2-vol_m_euclidean_p_30/config.md) |

Parametri identici a s2.1, per tre ragioni distinte:

- **`n_neighbors=15`** è l'ottimo reale del tuning 07-09, non un'eredità: coincide con quello di s2.1 sia per trustworthiness sia per giudizio visivo.
- **`min_dist=0.0`** è fisso in ogni produzione UMAP del progetto (s1.1-vol, s1.2-vol, s2.1), anche quando il tuning premia valori più alti: influenza solo quanto i punti si addensano, non la struttura dei vicinati, e tenerlo costante rende le run confrontabili.
- **`perplexity=30`** non è l'argmax (50): 15/30/50 sono un plateau entro 0.00024, e 30 è il valore usato in ogni produzione precedente. Sopra 50 la separazione `lesion_side` si degrada visivamente pur restando la metrica accettabile ([`s2_tuning.md`](s2_tuning.md)).

**Solo `metric=euclidean`**, nessuna run `dice` a differenza di s1.x: `dice` misura sovrapposizione tra insiemi e richiede dati binari, mentre qui il 28,7% dei valori sta strettamente tra 0 e 1. Usarlo imporrebbe una binarizzazione arbitraria che cancella la distinzione tra disconnessione lieve e grave.

- Durata: 29s (nc3), 23s (nc2), 19s (t-SNE).
- **Separazione `lesion_side` netta** nell'embedding 2D: due lobi, destra e sinistra, con un ponte stretto al centro. I casi `both` e `unknown` si concentrano proprio su quel ponte — coerente con l'interpretazione geometrica, e un controllo indipendente che l'asse principale dell'embedding sia davvero la lateralità.
- Il `metadata.csv` di queste run contiene solo `subject_id`/`dataset`: le colorazioni `side`/`nihss` sono risolte al momento del plot dal registro soggetti (`assets/metadata/participants.csv`), non da colonne copiate nella run.

##### Decisioni
