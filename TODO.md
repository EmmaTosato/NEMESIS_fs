# To see

- [ ] `build_lesion_matrix.py` non fa nessuno step di preprocessing neuroimaging oltre a resample (sulla griglia di `reference_template_path`) + ri-binarizzazione — nessuno skull-stripping, denoising, o altro step di preprocessing. Assume che le lesion mask siano già in uno spazio comune (naming BIDS `space-MNI152NLin6Asym`, prodotto a monte dalla pipeline `manual_masks`, fuori da questo repo). Da valutare se/quando serve implementare uno di questi step direttamente nella pipeline.
- [ ] Inserire `lesion_volume_ml` come covariata nei futuri step di analisi (UMAP/t-SNE e modelli predittivi) per fare il regress-out dell'effetto "volume puro". (Esito fondamentale dell'EDA su lesioni: PASPORT ha volumi sistematicamente molto più ampi).
- [ ] Valutare una soglia minima di frequenza voxel prima della dim reduction: oggi `build_lesion_matrix.py` tiene qualunque voxel lesionato in ≥1 soggetto su 1150 (`non_constant = X.any(axis=0)`) — sui dati reali (`data/derived/lesion_matrix/21-07_s1.1`) questo tiene 254865 colonne, di cui solo 3642 lesionate in ≥10% della coorte. La maggior parte delle feature usate oggi da UMAP/PCA/Jaccard-Dice sono quindi voxel lesionati in pochissimi soggetti (spesso uno solo), che non possono contribuire a un pattern condiviso ma contano comunque nella distanza. Pratica standard in lesion-symptom-mapping (Sperber & Karnath), non citata nei paper della libreria del progetto — quindi buona pratica generale, non gap validato dalla letteratura del gruppo. Non ancora deciso se/come implementarla: da esplorare empiricamente sui dati reali prima di fissare un valore (stessa logica già usata per la soglia di esclusione paziente nel masking FC, poi chiusa senza soglia — vedi sessione 2026-07-28 in `.claude/stato_progetto.md`).
- [ ] trova numero di pazienti che hanno lesione bilaterale
- [ ] radar plot / spider plot centroide lesione

- metriche
- connettività
- demografici, e score clinici
