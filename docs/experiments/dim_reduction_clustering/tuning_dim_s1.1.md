
#  Dimensionality Reduction S1.1
- **Pipeline:** `dim_reduction`
- **Dati in ingresso:** Matrice lesionale voxel-wise, 1150 soggetti (`data/derived/lesion_matrix/21-07_s1.1`)
- **Riferimento Log (CSV):** `results/lesion/dim_reduction/<riduzione>/runs_tuning.csv`
- **Parametri in input**: `config.md` in ogni risultato di output
- **Output:** I risultati di questa sessione sono stati scritti nella directory `tuning`


## 03-08-2026 Tuning
- **Data Run Produzione:** 03 Agosto 2026
- **Riduzioni:** UMAP, t-SNE
- **Cartelle risultati:** `results/lesion/dim_reduction/umap/tuning/03-08_s1.1/`, `results/lesion/dim_reduction/tsne/tuning/04-08_s1.1/`
- **Griglia esplorata** (dettaglio completo in `config.md` di ogni cartella, non duplicato qui)
	- UMAP: `metric` (euclidean/jaccard/dice) × `regress_out_volume` (F/T, incompatibile con jaccard/dice) × `n_components` (2/5/10) × `n_neighbors` (5/15/30/50/100) × `min_dist` (0/0.1/0.25) — 180 combinazioni
	- t-SNE: `metric` × `regress_out_volume` × `perplexity` (5/15/30/50/75), `n_components` fisso a 2 — 20 combinazioni
- **Metrica:** trustworthiness (Venna & Kaski) — **non confrontabile tra `n_components` diversi**, solo a parità (vedi `docs/knowledge/dim_reduction_tuning_guide.md`)
- **Osservazioni per combinazione**
	- euclidean: trustworthiness più bassa (~0.72) ma struttura visivamente continua ("a ragno")
	- jaccard/dice: alta (~0.93) ma si spacca sempre in 2 blob per lato lesione — confondimento noto, non pattern clinico
- **Confronto n_components (rendimenti marginali, non valore assoluto)**
	- dice/jaccard/euclidean(no regress): saturano già a `n_components=5` (Δ5→10 ≈ 0)
	- euclidean + `regress_out_volume=True`: continua a guadagnare anche a 10 (Δ5→10 ≈ +0.011)
	- dettaglio calcolo: sezione 6 di `notebooks/dim_reduction.ipynb`
- **Decisioni:**
	- Vengono restituiti plot con diverse colorazioni (dataset/side/volume/nihss)
- **Decisione presa:** —
- **Decisione aperta:** scelta di produzione di `n_neighbors`/`min_dist` (UMAP) e `perplexity` (t-SNE); scelta di `n_components` per l'embedding di clustering
- **Prossimo passo:** —


## 04-08-2026 Tuning
- **Data Run Produzione:** 04 Agosto 2026
- **Riduzioni:** UMAP (sweep aggiuntivi `n_components=5/10` per euclidean, poi jaccard/dice), t-SNE (rerun con coloring `nihss`)
- **Cartelle risultati:** t-SNE in `results/lesion/dim_reduction/tsne/tuning/04-08_s1.1/`; gli sweep UMAP aggiuntivi sono stati lanciati in cartelle datate 04-08 a parte, poi **fusi a mano** dentro `03-08_s1.1/` (schema unificato `metric=.../regress_out_volume=.../n_components=.../`, CSV aggregato ricostruito, cartelle temporanee cancellate — su richiesta esplicita, per non sporcare `results/` con nomi di sessione ad-hoc)
- **Bug fix reale:** `regress_out_volume` (flag di pipeline) finiva nei parametri passati al costruttore UMAP durante il rifit per il plot quando `n_components≠2` → crash. Mai emerso prima perché fino a questa sessione `n_components` era sempre uguale a `viz_n_components` (2), quindi il ramo di rifit non era mai stato eseguito per davvero. Fix: flag tolto prima del rifit, riapplicato dopo. Pattern generalizzabile → `lessons_learned.md` #17. Test di regressione: `test_dim_reduction_fine_tuning_nested_n_components_and_regress_out_volume_refits_viz`.
- **Nuovo flag `write_embeddings_grid`** (`DimReductionConfig`): opt-out manuale per saltare `embeddings_grid_*.png` (e il rifit costoso) in una foglia annidata quando è garantito identico a una foglia gemella già fatta — a `metric`/`n_neighbors`/`min_dist`/`random_state` fissi, UMAP con seed fisso è deterministico byte-per-byte, verificato a vista.
- **t-SNE**: tentativo di sweeppare anche lì `n_components` scartato **prima di lanciare nulla** — `sklearn.manifold.TSNE` con `n_components > 3` richiede `method="exact"`, mai gestito nel codice. Resta fisso a 2 (solo visualizzazione, mai input di clustering a più dimensioni per questo metodo).
- **Nuovi doc di letteratura:** `docs/knowledge/dim_reduction_tuning_guide.md` (trustworthiness vs varianza spiegata, perché un numero solo non basta), `umap_tsne_guide.md` (meccanica dei due metodi, nota Kobak & Linderman 2021 su UMAP)
- **Osservazioni preliminari (n_components=2):** euclidean trustworthiness ~0.70-0.74, jaccard/dice ~0.91-0.945 ma sempre spaccati per lato lesione — stesso artefatto già noto dal 29-07, non un pattern nuovo
- **Nota (sessione successiva, stessa cartella):** trovati e corretti 2 bug preesistenti in `plot_embedding_grid_blocks` (colorbar mancante sul ramo continuo, nessun NaN-handling), scala log aggiunta per `"volume"` (distribuzione molto skewed) — le 4 foglie `n_components=2` con `embeddings_grid_volume.png` sono state rigenerate e arricchite con `embeddings_grid_nihss.png` (nuova colorazione), verificando prima che i punteggi di trustworthiness già in CSV restassero identici.
- **Decisione presa:** —
- **Decisione aperta:** stessa del 03-08 — scelta di produzione di `n_neighbors`/`min_dist`/`perplexity`/`n_components`
- **Prossimo passo:** —