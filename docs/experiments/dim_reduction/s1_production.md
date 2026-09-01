# Diario Esperimenti

**Pipeline:** Dim Reduction (Produzione)

**Dati:** Matrice raw (feature matrix, pre-riduzione)

**Sessione:** s1

**Tipo di dati**: Lesion Data (matrice voxel-wise volumetrica)

**Origine**: data/derived/lesion_matrix

**Note**
- Parametri scelti a valle del tuning ([`s1_tuning.md`](s1_tuning.md)).
- Vedi data_sessions.md per specifica sulle sessioni

---

## 11-08-2026 — s1.1

#### Prima produzione UMAP (n_components 2 e 10)

- **Input:**
    - s1.1
    - Dati raw: matrice lesionale voxel-wise
    - Path: `data/derived/lesion_matrix/21-07_s1.1`
    - 1150 soggetti
- **Metodi:** umap
- **Obiettivo:**
    - Produrre i primi embedding UMAP dopo il tuning (03/04-08), fissando i parametri migliori per ogni combo metric × n_components

**Risultati**

| ID | metric | n_neighbors | min_dist | n_components | Link |
| --- | --- | --- | --- | --- | --- |
| nc2_m_dice | dice | 15 | 0.0 | 2 | [config.md](../../../results/lesion/dim_reduction/production/umap/11-08_s1.1_m_dice_nc2/config.md) |
| nc2_m_euclidean | euclidean | 5 | 0.0 | 2 | [config.md](../../../results/lesion/dim_reduction/production/umap/11-08_s1.1_m_euclidean_nc2/config.md) |
| nc10_m_dice | dice | 30 | 0.0 | 10 | [config.md](../../../results/lesion/dim_reduction/production/umap/11-08_s1.1_m_dice_nc10/config.md) |
| nc10_m_euclidean | euclidean | 30 | 0.0 | 10 | [config.md](../../../results/lesion/dim_reduction/production/umap/11-08_s1.1_m_euclidean_nc10/config.md) |

- `nc2_m_euclidean` è un re-run dell'embedding 2D del 23-07 (stessi parametri) — per questo condivide la data di sessione con le altre 3 run.

---

## 13-08-2026 — s1.1

#### Produzione UMAP 3D (n_components=3)

- **Input:**
    - s1.1
    - Dati raw: matrice lesionale voxel-wise
    - Path: `data/derived/lesion_matrix/21-07_s1.1`
    - 1150 soggetti
- **Metodi:** umap
- **Obiettivo:**
    - Produrre l'embedding UMAP a 3 componenti per visualizzazione 3D

**Risultati**

| ID | metric | n_neighbors | min_dist | n_components | Link |
| --- | --- | --- | --- | --- | --- |
| nc3_m_euclidean | euclidean | 5 | 0.0 | 3 | [config.md](../../../results/lesion/dim_reduction/production/umap/13-08_s1.1_m_euclidean_nc3/config.md) |
| nc3_m_dice | dice | 30 | 0.0 | 3 | [config.md](../../../results/lesion/dim_reduction/production/umap/13-08_s1.1_m_dice_nc3/config.md) |

- `nc3_m_euclidean` — stessi parametri baseline della produzione 2D euclidean (11-08), solo `n_components` cambiato.
- `nc3_m_dice` — combo a trustworthiness migliore per dice+n_components=3 nel tuning del 13-08 (0.9509), `min_dist` fissato a 0.0 (non l'argmax 0.1/0.9519) per coerenza con la run euclidean gemella.
- Scelto euclidean come baseline nonostante trustworthiness più bassa del dice: lo split artificiale per lato lesione di dice è documentato in [`s1_tuning.md`](s1_tuning.md) (03-08).

---

## 23-07-2026 — s1.1

#### t-SNE — stale, da riverificare

- **Nota:** 4 run loggate in `results/lesion/dim_reduction/production/tsne/runs.csv` (`p30`/`p40`/`p60`/`p80`, perplexity 30/40/60/80) puntano a `results/lesion/dim_reduction/tsne/23-07_s1.1_p*` — path non presente su disco (verificato 28-08, probabilmente pre-riorganizzazione in `production/`). Non trattare come output valido senza prima ricontrollare/rilanciare. Sostituite dalla produzione reale sotto (28-08).

---

## 28-08-2026 — s1.1

#### Prima produzione t-SNE reale

- **Input:**
    - s1.1
    - Dati raw: matrice lesionale voxel-wise
    - Path: `data/derived/lesion_matrix/21-07_s1.1`
    - 1150 soggetti
- **Metodi:** tsne
- **Obiettivo:**
    - Prima produzione t-SNE valida per s1.1 — i 4 run del 23-07 sono stale/assenti su disco (vedi sopra)

**Risultati**

| ID | metric | perplexity | Link |
| --- | --- | --- | --- |
| s1.1_m_dice | dice | 30 | [config.md](../../../results/lesion/dim_reduction/production/tsne/28-08_s1.1_m_dice_p_30/config.md) |
| s1.1_m_euclidean | euclidean | 30 | [config.md](../../../results/lesion/dim_reduction/production/tsne/28-08_s1.1_m_euclidean_p_30/config.md) |

- `perplexity=30` per entrambe le metriche (non l'argmax per-metrica) — coerenza tra le due run compagne, stessa logica del `min_dist=0.0` condiviso in produzione UMAP.
- Verifica visiva dell'artefatto `dice`/`lesion_side` eseguita sulla coorte s1.2 (vedi sotto), non ripetuta separatamente su s1.1 — stessa metrica, stesso pattern già noto per UMAP su questa coorte.
- Tutte e 4 le `color_by` popolate su entrambi i run.

---

## 28-08-2026 — s1.2

#### Prima produzione UMAP (6 embedding, replica esatta della struttura s1.1)

- **Input:**
    - s1.2
    - Dati raw: matrice lesionale voxel-wise (+ UCL-UK/UCLStrokeData)
    - Path: `data/derived/lesion_matrix/25-08_s1.2`
    - 5269 soggetti
- **Metodi:** umap
- **Obiettivo:**
    - Riprodurre su s1.2 gli stessi 6 embedding di produzione già fatti su s1.1 (`{dice,euclidean}×{2,3,10}`), stessi `n_neighbors`/`min_dist` per combo — non ri-derivati dallo sweep `26-08_s1.2`, replicati identici a s1.1 su richiesta esplicita

**Prerequisito:** `data/derived/lesion_matrix/25-08_s1.2/metadata.csv` non aveva mai `lesion_side`/`nihss` in place — arricchito in place con `enrich_lesion_metadata.py --write_in_place true` prima di lanciare le 6 run.

**Risultati**

| ID | metric | n_neighbors | min_dist | n_components | Link |
| --- | --- | --- | --- | --- | --- |
| nc2_m_dice | dice | 15 | 0.0 | 2 | [config.md](../../../results/lesion/dim_reduction/production/umap/28-08_s1.2_m_dice_nc2/config.md) |
| nc2_m_euclidean | euclidean | 5 | 0.0 | 2 | [config.md](../../../results/lesion/dim_reduction/production/umap/28-08_s1.2_m_euclidean_nc2/config.md) |
| nc3_m_dice | dice | 30 | 0.0 | 3 | [config.md](../../../results/lesion/dim_reduction/production/umap/28-08_s1.2_m_dice_nc3/config.md) |
| nc3_m_euclidean | euclidean | 5 | 0.0 | 3 | [config.md](../../../results/lesion/dim_reduction/production/umap/28-08_s1.2_m_euclidean_nc3/config.md) |
| nc10_m_dice | dice | 30 | 0.0 | 10 | [config.md](../../../results/lesion/dim_reduction/production/umap/28-08_s1.2_m_dice_nc10/config.md) |
| nc10_m_euclidean | euclidean | 30 | 0.0 | 10 | [config.md](../../../results/lesion/dim_reduction/production/umap/28-08_s1.2_m_euclidean_nc10/config.md) |

- `nc10_*`: nessuno sweep di tuning ha mai coperto `n_components=10` (né s1.1 né s1.2) — `n_neighbors` estrapolato da `nc3`, stesso valore di s1.1.
- Stesso caveat noto per `dice`: alto trustworthiness, split artificiale per `lesion_side`.
- Tutte e 4 le `color_by` (`dataset`/`side`/`volume`/`nihss`) popolate.

---

## 28-08-2026 — s1.2

#### Prima produzione t-SNE reale

- **Input:**
    - s1.2
    - Dati raw: matrice lesionale voxel-wise (+ UCL-UK/UCLStrokeData)
    - Path: `data/derived/lesion_matrix/25-08_s1.2`
    - 5269 soggetti
- **Metodi:** tsne
- **Obiettivo:**
    - Prima produzione t-SNE valida per s1.2 (nessuna produzione precedente esisteva per questa coorte — solo tuning, `26-08_s1.2`)

**Verifica preliminare (su richiesta):** l'argmax trustworthiness per `dice` è `perplexity=15` in tutti e 3 gli sweep storici, ma i grid `embeddings_grid_side.png` (backfillati su `26-08_s1.2` con `lesion_side` ora disponibile) mostrano lo stesso artefatto già noto su UMAP: con `dice`, i soggetti `right`/`left` si separano in due bande nette, stabili a **ogni** valore di perplexity testato (5→200) — non è un effetto della perplexity, è strutturale alla metrica. Con `euclidean` nessuna banda, `left`/`right` interspersi.

**Risultati**

| ID | metric | perplexity | Link |
| --- | --- | --- | --- |
| s1.2_m_dice | dice | 30 | [config.md](../../../results/lesion/dim_reduction/production/tsne/28-08_s1.2_m_dice_p_30/config.md) |
| s1.2_m_euclidean | euclidean | 30 | [config.md](../../../results/lesion/dim_reduction/production/tsne/28-08_s1.2_m_euclidean_p_30/config.md) |

- `perplexity=30` per entrambe le metriche (non l'argmax per-metrica) — coerenza tra le due run compagne, stessa logica del `min_dist=0.0` condiviso in produzione UMAP.
- Tutte e 4 le `color_by` popolate su entrambi i run; stesso caveat `dice`/`lesion_side` di UMAP, qui confermato visivamente (non solo per analogia).
