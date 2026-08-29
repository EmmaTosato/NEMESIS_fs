# Dim reduction
- [x] Letteratura
- [x] Completare visualizzazioni semplici UMAP
- [x] Completare visualizzazioni  semplici t-sne
- [ ] Fare visualizzazioni anatomiche UMAP
- [ ] Fare visualizzazioni anatomiche t-sne
- [ ] Implementare PCA
	- [ ] Capire che PCA
	- [ ] Notebook
	- [ ] Visualizzazione


## Clustering
- [x] Letteratura
- [x] Tuning
- [x] Run
- [x] Completare visualizzazioni semplici
- [ ] Fare visualizzazioni anatomiche

# Clustering

### SDC
- [x] Vai sul server 
- [x] Copia prima sul server
- [x] Copia in locale
- [x] Notebook esplorativo
- [x] Costruzione matrice 2D
- [x] Integrazione dato nella pipeline (da capire)
- [x] Dim reduction
- [ ] Clustering
- [ ] Chiarire provenienza del file `..._LF-lesion_atlas-yeh_hcp1065_streamline.csv` presente in `sub_BCB_example/` (35 file/soggetto) ma assente nell'output reale di `compute_sdc` (34 file/soggetto): non generato da `bcb-lesion-features` (zero riferimenti a "streamline" nei moduli `lesion_features`/`damage_profile` di bcblib) e non coincide col formato nativo documentato di Tractotron (`probability.csv`/`proportion.csv`, matrice 68 tratti dell'atlante bundled) nonostante il naming per-tratto (`AF_L`/`AF_R`...) ricordi la convenzione Yeh HCP1065. Chiedere all'utente come `sub_BCB_example/` è stato generato. Decidere se integrare Tractotron come Stage 3 in `compute_sdc.py` o lasciarlo fuori scope.

### Comparison
- [ ] Su notebook iniziare comparison statistica numerica
- [ ] Su notebook iniziare comparison visiva

