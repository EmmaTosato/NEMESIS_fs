
Date: 30/09/2026
People: Sebastiano, Antonio

---

# TO DO

### SEBA
Nel notebook lesion quality

* [x] Scala reale al posto del log
* [x] Controlla calcolo voxel mm cubo
* [x] Metti le statistiche sotto plot dei volumi
* [x] Togli i pazienti con voxel a 0
* [x] No soglia dalla letteratura per eliminare le lesioni molto piccole: anche le lesioni focali e minime possono essere fatali
* [x] Metti a 30% la soglia di voxel fuori dal brain
* [x] Per i cluster possiamo andare a k=20/30 per vedere come si comportano le metriche
* [x] Forse togli k=2 dal tuning


### ANTONIO
* [x] Plottare la disconnessione oltre che volume lesione
* [x] Sistemare plot centroide
* [x] Caratterizziamo i pazienti per lesione corticale / sotto-corticale / sotto-tentrionale
* [x] Caratterizziamo i pazienti per lesione anteriore e posteriore


### EMMA
* [x] Nuovi dati
* [x] Ridefinire le Pipelines
* [ ] Comparazione risultati: la lesione rispiecchia il clsuter sdc (distanze / metriche )
* [x] PCA Michel



# STATEMENTS

* Input:
  * Lesione
  * SDC voxel wise
  * SDC streamline
* Clustering scelti
  * Agglomerative
  * HDBSCAN
  * (Michele)
  * (Autoencoder)
* Potrebbe essere che il clustering sia guidato dall'asse lateralità/volume
* Anche le lesioni focali e minime possono essere fatali



# GOALS

* Arriva un soggetto con una lesione e voglio poter sapere a che cluster appartiene e con confidenza / probabilità
* Domande correlate:
  * E' possibile individuare le feature che guidano queste cluster
  * At which extent do the they drive the clustering?
