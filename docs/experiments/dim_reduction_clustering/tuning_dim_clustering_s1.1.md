# Dimensionality Reduction  + Clustering S1.1 

## 26-07-2026 Tuning
Ecco la sintesi dell'analisi strutturata per punti chiave, senza l'uso di emoji.

### Metodi Validi 
**UMAP** (n_neighbors=5, euclidean)
- **KMeans & GMM:** Solidi a **k=4** / **n=4** (confermati).
- **Agglomerative:** **k=5**.
- **Spectral:** **n=8** (l'eigengap suggeriva 11, ma i dati non lo supportano).
- **DBSCAN:** Inaffidabile (silhouette ~0 su tutto il range).

**PACMAP** (n_neighbors=5)
- **KMeans & GMM:** **k=6** / **n=6** (oppure **k=2** / **n=2** per split macro).
- **Agglomerative:** Incoerente tra metriche (**k=5**) e dendrogramma (**k=2**).
- **DBSCAN:** Forte trade-off. `eps=0.3` favorisce la qualità (ma 36% noise), `eps=0.5` favorisce la copertura (8% noise, qualità inferiore).
- **Spectral:** Escluso di proposito (tende a fondere i cluster satelliti). 

**t-SNE** (perplexity=30)
- **KMeans & Spectral:** **k=5** / **n=5** (quest'ultimo confermato su griglia estesa).
- **Agglomerative & GMM:** **k=2** / **n=2**.
- **DBSCAN:** Attenzione agli artefatti. `eps=0.5` crea un falso segnale (silhouette 0.988 ma 98.9% di noise, salva solo 13 soggetti). `eps=1.5` è il compromesso migliore (33% noise).
    

### PCA: Scartata 
La PCA è risultata inefficace sia ad alta che a bassa dimensionalità:
- **PCA 150 componenti:**
    - Soffre della _curse of dimensionality_.
    - Nessuna struttura reale rilevata (Spectral inefficace, DBSCAN >90% noise).
    - Clustering debole e sbilanciato (es. Agglomerative k=2 mette 563/1150 soggetti in un'unica foglia).
        
- **PCA 2 componenti (Test di controllo):**
    - Il segnale predominante (silhouette elevato) **non è topografico ma volumetrico**.
    - La PC2 ha una correlazione di Pearson elevatissima (r=0.92) con il volume lesionale.    
    - Tutti gli algoritmi (KMeans, Agglomerative, DBSCAN, Spectral a 3 cluster) isolano semplicemente il gruppo delle "lesioni piccole", rendendo la topografia irrilevante.

---
