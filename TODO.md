- [ ] SDC toolkit c'è, leggi come è stato fatta
- [ ] sessione di debug intensa

## To see

- [ ] `build_lesion_matrix.py` non fa nessuno step di preprocessing neuroimaging oltre a resample (sulla griglia di `reference_template_path`) + ri-binarizzazione — nessuno skull-stripping, denoising, o altro step di preprocessing. Assume che le lesion mask siano già in uno spazio comune (naming BIDS `space-MNI152NLin6Asym`, prodotto a monte dalla pipeline `manual_masks`, fuori da questo repo). Da valutare se/quando serve implementare uno di questi step direttamente nella pipeline.
