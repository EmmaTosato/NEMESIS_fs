
Date: 30/09/2026
People: Sebastiano, Antonio

---

# TO DO

### SEBA
Nel notebook lesion quality

* [ ] Scala reale al posto del log
* [ ] Controlla calcolo voxel mm cubo
* [ ] Metti le statistiche sotto plot dei volumi
* [ ] Togli i pazienti con voxel a 0
* [ ] No soglia dalla letteratura per eliminare le lesioni molto piccole: anche le lesioni focali e minime possono essere fatali
* [ ] Metti a 30% la soglia di voxel fuori dal brain
* [ ] Per i cluster possiamo andare a k=20/30 per vedere come si comportano le metriche
* [ ] Forse togli k=2 dal tuning


### ANTONIO
* [ ] Plottare la disconnessione oltre che volume lesione
* [ ] Sistemare plot centroide
* [ ] Caratterizziamo i pazienti per lesione corticale / sotto-corticale / sotto-tentrionale
* [ ] Caratterizziamo i pazienti per lesione anteriore e posteriore


### EMMA
* [ ] Nuovi dati
* [ ] Ridefinire le Pipelines
* [ ] Comparazione risultati: la lesione rispiecchia il clsuter sdc (distanze / metriche )
* [ ] PCA Michel



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
