# Clustering diretto della matrice SDC voxelwise `s2.4-vol` (senza UMAP)

Matrice `data/derived/sdc_matrix/07-10_s2.4-vol/matrix.npy` (5845 × 291345, float32), HDBSCAN e agglomerative su distanze precalcolate euclidean e cosine. Tutto è in questa cartella; il resto del repo è stato solo letto.

## Come riprodurre

Dalla radice del repo (~6 min in totale, picco RAM 9,1 GB nel passo 1):

```bash
PY=/opt/anaconda3/envs/nemesis/bin/python
$PY temp/s2.4_raw_clustering/scripts/01_distances.py            # D_euclidean.npy, D_cosine.npy in cache/ (gitignorata, 2 × 137 MB)
$PY temp/s2.4_raw_clustering/scripts/02_hdbscan.py              # 56 fit, ~1 s l'uno
$PY temp/s2.4_raw_clustering/scripts/03_agglomerative.py        # 5 linkage × k = 3..30
$PY temp/s2.4_raw_clustering/scripts/04_candidates_compare_describe.py
$PY temp/s2.4_raw_clustering/scripts/05_figures.py
```

## Verdetto

**Non c'è una struttura a cluster nella matrice grezza che questi metodi riescano a separare.** HDBSCAN non dà nessuna partizione usabile; l'agglomerative dà solo la partizione già nota (lato × volume/carico di disconnessione), e solo con ward/euclidean.

| Metodo / metrica | Verdetto | Numeri |
|---|---|---|
| HDBSCAN / euclidean | **Non utilizzabile** | 0/28 usabili. Rumore 19-100%. Zero cluster (rumore 100%) in 13 punti su 28, cioè `min_cluster_size` ≥ 75 sempre e 30-50 con `min_samples` ≥ 5-10: nulla è più denso del blob unico. Il migliore (mcs=20, ms=5): 3 cluster, rumore 23%, ma cluster più grande 76% (e due cluster da 34-39 soggetti) |
| HDBSCAN / cosine | **Non utilizzabile** | 0/28 usabili. Rumore 51-75% in 27 punti su 28; l'unico a 26% (mcs=75, ms=1) ha 2 cluster, il più grande 73%. Silhouette 0,19-0,57 ma solo sui non-rumore |
| Agglomerative ward / euclidean | **Utilizzabile solo a k=3, ma debole e già noto** | cophenetic 0,67; silhouette 0,29 a k=3 (gap 1,62), 0,17 a k=4, ≈ 0,1 da k=6 in poi (nessun picco) |
| Agglomerative complete / euclidean | Come ward a k=3 (silhouette 0,30), **non utilizzabile** da k=4 | cophenetic 0,77; da k=4 il cluster più piccolo è < 1% (58 soggetti a k=4, 24 a k=5) |
| Agglomerative average / euclidean | **Non utilizzabile** | cophenetic 0,84 (alta, ma per chaining): a ogni k il cluster più piccolo ha 1-3 soggetti, a k=3 il 96,7% dei soggetti è in un solo cluster |
| Agglomerative average / cosine | **Non utilizzabile** | Stesso chaining: a k=3 il 99,7% in un cluster, cluster da 1 soggetto |
| Agglomerative complete / cosine | **Non utilizzabile** | silhouette ≤ 0,10 per ogni k, cophenetic 0,39; k=3..5 in pareggio di altezza (4 fusioni finali a 1,0) |

Criterio di "non usabile" per HDBSCAN, come da consegna: meno di 3 o più di 30 cluster, rumore > 25%, cluster più grande > 60% (quota sul totale dei 5845 soggetti). Per l'agglomerative il solo criterio era cluster più piccolo ≥ 1%.

**HDBSCAN con rumore alto ovunque è il risultato**, non un difetto della griglia: la nuvola è un unico continuo allungato lungo volume della lesione e carico di disconnessione (`images/clusters_volume_load.png`), senza buchi di densità. Come da consegna non ho cercato altri parametri.

## Tabelle chiave

### HDBSCAN (28 combinazioni per metrica, tabella completa in `tables/hdbscan_grid.csv`, mappa in `images/hdbscan_grid.png`)

Il punto "meno peggio" per metrica (meno criteri violati, poi meno rumore):

| Metrica | mcs / ms | Cluster | Rumore | Più grande | Più piccolo | Silhouette (non-rumore) | Criteri violati |
|---|---|---|---|---|---|---|---|
| euclidean | 20 / 5 | 3 | 23,2% | 75,6% | 34 | 0,49 | cluster più grande |
| cosine | 50 / 20 | 5 | 50,7% | 23,8% | 50 | 0,29 | rumore |

### Agglomerative, silhouette e cluster più piccolo (tabella completa k=3..30 in `tables/agglomerative_k.csv`, curve in `images/agglomerative_k.png`)

| Linkage / metrica | k | Silhouette | Più piccolo | Più grande | Gap |
|---|---|---|---|---|---|
| ward / euclidean | 3 | 0,293 | 549 (9,4%) | 73,4% | 1,62 |
| ward / euclidean | 4 | 0,167 | 549 | 50,0% | 1,28 |
| ward / euclidean | 5 | 0,160 | 266 | 50,0% | 1,16 |
| complete / euclidean | 3 | 0,304 | 325 (5,6%) | 77,5% | 1,11 |
| average / euclidean | 3 | 0,381 | 3 | 96,7% | 1,11 |
| complete / cosine | 3 | 0,043 | 901 | 57,8% | 1,00 (pareggio) |

La silhouette alta di average/euclidean a k=3 (0,38) è un artefatto: due cluster sono da 3 e circa 190 soggetti, il resto è un blocco unico.

## Cosa ordinano i cluster (descrittivo, nessun test)

Profili per cluster in `tables/cluster_profile.csv`; riassunto in `tables/structure_summary.csv`. Il lato è in gran parte calcolato dalla maschera, quindi cluster puri per lato sono attesi. Quote di lato calcolate sui soggetti con lato noto (3 NaN, più 89 "both" riportati a parte).

**ward / euclidean, k=3** (la partizione migliore dell'agglomerative):

| Cluster | n | Sinistra | Destra | Volume mediano (voxel 2 mm) | Infratentoriale | Carico di disconnessione mediano |
|---|---|---|---|---|---|---|
| 0 | 1004 | 0,4% | 98,6% | 3064 | 0,3% | 19 517 |
| 1 | 4292 | 59,5% | 38,8% | 201 | 14,0% | 5 170 |
| 2 | 549 | 99,6% | 0,0% | 3779 | 0,1% | 23 061 |

- **Struttura: lesioni grandi destre / lesioni grandi sinistre / tutto il resto (piccole, miste).** Stesso quadro delle run UMAP (`s1.4`: sinistra / destra / misto piccolo).
- **I cluster ordinano anche per quantità di disconnessione, non solo per pattern**: la varianza spiegata dall'appartenenza al cluster è η² = 0,38 per log10(volume) e 0,37 per log10(carico) a k=3 (0,52 e 0,52 a k=4). Volume e carico sono quasi collineari (`images/clusters_volume_load.png`), quindi la matrice grezza non separa "dove" da "quanto".
- A k=4 il cluster piccolo si spezza in un gruppo sinistro da 1371 (volume 738) e il resto; i cluster infratentoriali non emergono come cluster a sé (infratentoriale 20% nel cluster misto).

**HDBSCAN / cosine (mcs=50, ms=20)**: 5 cluster densi su 2883 soggetti (49%). Due sono lato-puri e grandi (1266 destra, 1393 sinistra, volume mediano ≈ 1700-2000); due sono infratentoriali (84 sinistra, 90 destra, ≈ 98% infratentoriali, volume ≈ 90); uno da 50 destra/infratentoriale. ARI contro il solo lato (L/R, non-rumore) = 0,85: sono i nuclei densi ai due lati, non una novità. Il rumore (2962 soggetti) è fatto di lesioni piccole.

**HDBSCAN / euclidean (mcs=20, ms=5)**: 2 cluster da 39 (sinistra) e 34 (destra) soggetti con lesioni enormi (volume mediano 13-17 mila voxel), più un cluster da 4416 (pratica­mente tutto il resto). Sono le code della distribuzione di volume, non gruppi.

## Confronto con le run già fatte

Stessi 5845 soggetti, stesso ordine (controllato su `metadata.csv` di ogni run, solleva se diverso). ARI sui soggetti non-rumore in entrambe le partizioni (`n` indicato nelle tabelle). Chiavi "di punta" fisse, tabella `tables/ari_vs_headline_runs.csv`:

| Candidato | UMAP hdbscan nc2 (mcs=100, ms=10) | UMAP hdbscan nc10 | UMAP agglom. nc2 (ward k=5) | UMAP agglom. nc10 | ADP raw (euclid, Z=3.0) |
|---|---|---|---|---|---|
| ward/euclid k=3 | 0,02 | 0,01 | 0,07 | 0,07 | −0,05 |
| ward/euclid k=4 | 0,14 | 0,13 | 0,20 | 0,20 | −0,01 |
| complete/euclid k=3 | −0,04 | −0,01 | 0,03 | 0,03 | −0,06 |
| HDBSCAN/cosine (50/20) | 0,55 | 0,88 | 0,76 | 0,76 | −0,01 |
| HDBSCAN/euclid (20/5) | 0,00 | −0,01 | 0,00 | 0,00 | −0,02 |

- **Le partizioni dirette non coincidono con quelle su UMAP né con l'ADP euclideo**: ARI ≤ 0,20 per tutte le righe agglomerative (0,01-0,07 per ward k=3). L'unico accordo alto (HDBSCAN/cosine con le run UMAP) è su un sottoinsieme di 2600-2900 soggetti, i nuclei lato-puri e infratentoriali.
- **Cautela sul massimo**: `tables/ari_vs_existing_runs_best.csv` riporta il massimo su centinaia di chiavi e non va letto come accordo (per esempio HDBSCAN/cosine contro ADP dice Z=5.0 dà 0,99 su 2883 soggetti, ma è il massimo di 36 chiavi ed è ARI su un sottoinsieme che per costruzione ha già tolto il rumore).

## Costi

| Passo | Tempo | RAM di picco |
|---|---|---|
| Distanza euclidean (`pairwise_distance`) | 123 s | 8,7 GB |
| Distanza cosine (blocchi di 20 000 colonne) | 177 s | 9,1 GB |
| HDBSCAN, 56 fit | 57 s (~1 s a fit) | 1,4 GB |
| Agglomerative, 5 linkage (0,4 s l'uno) + silhouette k=3..30 | tempo totale non misurato separatamente | 1,2 GB |

Validazione delle distanze (`tables/distances_validation.csv`): simmetriche, diagonale 0, finite, nessuna coppia a distanza 0, nessuna riga a norma 0. Errore massimo contro `scipy.cdist` su 200 righe a caso: 7,6e-6 (euclidean, scala 1-205), 3,0e-8 (cosine).

## Cosa non ho verificato

- **Dice pesato non lanciato**, come da consegna: i due casi sopra non danno niente di utilizzabile, e su 5845 righe richiederebbe molto più dei ~2 minuti dati per 1570.
- **Confronto con `cdist` solo su un blocco 200 × 200** (le 200 righe contro sé stesse), non su 200 × 5845: il confronto completo richiedeva una copia float64 di tutta X (13,6 GB). Il primo tentativo, con il confronto completo, è stato fermato e riscritto per questo motivo.
- **HDBSCAN: solo i parametri della griglia** e `allow_single_cluster=False`, `cluster_selection_method` di default (`eom`). Con `allow_single_cluster=True` o `leaf` i risultati potrebbero cambiare; non provati perché la consegna chiedeva di non cercare altri parametri.
- **Il 100% di rumore a mcs alti** significa "nessun cluster trovato" (la radice non può essere l'unico cluster), non che tutti i soggetti siano outlier.
- **Silhouette HDBSCAN solo sui non-rumore**: ottimistica per costruzione, non confrontabile con quella dell'agglomerative, che copre tutti i soggetti.
- **Agglomerative: tagli per ordine di fusione** (`cut_tree`) e non per altezza, perché complete/cosine ha 4 fusioni a distanza 1,0 e `fcluster` non restituisce esattamente k cluster. Dove non c'è pareggio ho controllato che le due partizioni coincidano (solleva altrimenti). Nei tagli in pareggio (`tied_at_cut` in `agglomerative_k.csv`) la scelta tra cluster a pari altezza segue l'ordine dell'albero.
- **Ward solo con euclidean**, come da consegna; ward su cosine non è definito.
- **Nessuna stabilità** per sottocampionamento (esclusa dalla consegna) e nessun controllo di robustezza al seme (le procedure sono deterministiche).
- **Candidati scelti con una regola, non a mano**: migliore silhouette, migliore silhouette per k ≥ 4, miglior gap (agglomerative, solo partizioni con cluster più piccolo ≥ 1%); punto "meno peggio" (HDBSCAN). Altre partizioni non sono state profilate.
- **ADP**: ho assunto che le etichette < 0 siano rumore; nelle chiavi confrontate l'ADP non ha etichette negative (il numero di soggetti confrontati coincide con i non-rumore del candidato).
- **Metadati**: 3 soggetti senza `lesion_side` (esclusi dalle quote di lato e dall'ARI contro il lato), 89 "both" inclusi nelle quote ma non nell'ARI L/R. η² è calcolato su log10 di volume e carico, con il rumore trattato come un gruppo a sé.
- **Non ho commesso nulla né lanciato sbatch**; `cache/` (261 MB) e `logs/` sono ignorate da un `.gitignore` locale, ma il resto di `temp/` risulta non tracciato in git.
