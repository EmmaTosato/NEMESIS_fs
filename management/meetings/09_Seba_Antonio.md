
Date: 14/10/2026
People: Sebastiano, Antonio

---

# TO DO
- [ ] Rivedi molti errori di dash
- [ ] Probabilità nei cluster HDBSCAN
- [ ] Rivedi un attimo la categorizzazione con cortex
- [ ] Pasport NIHSS?
- [ ] Provare evidence accumulation
- [ ] PCA
- [ ] Componente di membership



# STATEMENTS
L'idea è che vorremmo:
- Ho la lesione, prendo la sua disconnessione
- Faccio PCA o altro metodo di riduzione
- Ottengo componenti a maggior varianza
- Ci applico clustering
- Andiamo a così a vedere come il soggetto si colloca
	- accuratezza di membership
	- profilo funzionale e clinico
- Parallelamente, per sopperire alla mancanza di FC, ho un modello DL sdc/fmri per stimare FC medio a partire dalla sdc 
	- generative ai (GAN)
	- semi-supervised: ho un subsample di 400 features che compongono il mio labelled sample
	- il resto delle feature, per i soggetti rimanenti, deve essere stimato

--> L'idea è che, data una lesione, riesco a con una certa accuratezza ad assegnargli un cluster e stimare la sua FC



# GOALS


