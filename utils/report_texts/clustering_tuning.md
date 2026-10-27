# Testi di `report.md` del tuning del clustering

Il report (`src/analysis/clustering_tuning_report.py`) legge da qui le spiegazioni degli indici: cosa misura ciascuno, come si legge, cosa non dice. Nessun giudizio di merito e nessuna soglia nostra: sono descrizioni. Il codice scrive solo tabelle e collegamenti alle figure.

Come è fatto il file:

- Ogni testo è una sezione `## <tipo>: <nome>`. I tipi sono `term` (definizione di una colonna o di un indice), `note` (nota in fondo al report), `fragment` (pezzo di una frase che il codice completa) e `hint` (riquadro «Come leggerlo» sotto una tabella o una figura).
- `term`, `note` e `fragment` sono un solo paragrafo, senza righe vuote. `hint` è un elenco: una riga `- ` per ogni punto, e una riga che continua il punto prima va rientrata.
- Il codice si ferma con un errore se manca un testo che gli serve, se un titolo è ripetuto o se c'è un titolo che non conosce. Per aggiungere un testo serve anche toccare il codice che lo usa.
- Tra graffe c'è un valore che il codice inserisce (`{metric}`, `{silhouette_min}`, ...): non va cambiato.

## term: silhouette

per ogni soggetto confronta la distanza media dai compagni del suo cluster con quella dal cluster più vicino; qui è la media su tutti i soggetti. Va da -1 a 1: più alta è meglio; sotto 0 i soggetti sono in media più vicini a un altro cluster che al proprio.

## term: davies_bouldin

media, sui cluster, del rapporto tra quanto il cluster è disperso e quanto è vicino al cluster più simile. Più bassa è meglio.

## term: calinski_harabasz

rapporto tra la separazione dei cluster e la compattezza di ciascuno. Più alto è meglio; tende a crescere con il numero di cluster.

## term: dunn

rapporto tra la distanza minima tra due cluster e il diametro massimo di un cluster (la distanza più grande tra due soggetti dello stesso cluster). Più alto è meglio.

## term: noise_fraction

quota dei soggetti non assegnati a nessun cluster (rumore).

## term: n_clusters_found

numero di cluster, rumore escluso.

## term: largest_cluster_share

quota dei soggetti, rumore compreso, nel cluster più grande.

## term: n_small_clusters

cluster con meno di 10 soggetti.

## term: id_2nn

dimensione intrinseca stimata dei dati; costante per `metric`.

## term: ari_vs_prev_z

ARI (accordo tra due partizioni, 1 = identiche) con la partizione al valore di `Z` immediatamente più basso, sui soli soggetti clusterizzati.

## term: membership_mean

media, sui soggetti non rumore, della probabilità di appartenere al proprio cluster. Le righe del vettore non sommano a 1 (il resto è la probabilità di essere rumore). Di norma scende al crescere del numero di cluster e la sua scala dipende dallo spazio clusterizzato: si confronta a parità di `n_clusters_found`, non contro 1.

## term: persistence_mean

media semplice, sui cluster, della stabilità `cluster_persistence_` del pacchetto (da 0, effimero, a 1, presente su tutte le scale di densità): un cluster piccolo pesa quanto uno grande. Di norma scende al crescere del numero di cluster e la sua scala dipende dallo spazio clusterizzato: si confronta a parità di `n_clusters_found`, non contro 1.

## term: dbcv

indice di validità basato sulla densità (Moulavi et al. 2014): per ogni cluster confronta quanto è rado al suo interno con quanto è separato dal cluster più vicino; la media è pesata sulla dimensione dei cluster, con il rumore nel denominatore, quindi il rumore abbassa il punteggio. Va da -1 a 1: più alto è meglio. Non definito con meno di 2 cluster.

## term: cophenetic_correlation

correlazione tra le distanze vere tra i soggetti e le distanze che l'albero implica. Va da -1 a 1: vicino a 1 l'albero rispetta bene le distanze. Un valore per `metric` e `linkage`, non si confronta tra `metric` diverse. Nessuna fascia con fonte in letteratura.

## term: ari

adjusted Rand index: accordo tra due partizioni degli stessi soggetti, 1 = identiche, 0 = quanto il caso. Qui tra i linkage della stessa `metric`, allo stesso k; non dipende dai nomi dei cluster.

## term: jump

per ogni k, altezza della fusione che porta da k a k-1 cluster divisa per quella della fusione che porta da k+1 a k. Vicino a 1: nessun taglio netto a k; più è alto, più il taglio a k è netto. Le altezze sono in unità diverse per ogni linkage, quindi i linkage non si confrontano. Nessuna fascia con fonte in letteratura.

## note: silhouette_convention

**Fasce della silhouette**: esistono fasce di lettura (Kaufman & Rousseeuw 1990, *Finding Groups in Data*); questo report non le usa. Spiegazione e fonti in `knowledge/notes/dim_reduction_clustering/clustering_methods/evaluation_metrics.md`.

## note: density_indices

**Indici non calcolati**: silhouette, Calinski-Harabasz, Davies-Bouldin e Dunn non sono calcolati per HDBSCAN: si calcolano sui soli soggetti non rumore (se l'algoritmo scarta i soggetti più difficili, salgono) e presuppongono cluster compatti. Il DBCV pesa il rumore. Spiegazione in `knowledge/notes/dim_reduction_clustering/clustering_methods/evaluation_metrics.md`.

## note: non_euclidean

Calinski-Harabasz, Davies-Bouldin e Dunn non sono definiti per `{metric}`: richiedono la distanza euclidea (cella vuota).

## fragment: curves_panels_both

silhouette (a sinistra) e Davies-Bouldin (a destra)

## fragment: curves_panels_silhouette_only

silhouette; Davies-Bouldin non c'è perché per questa `metric` non esiste

## fragment: curves_axes_both

silhouette da {silhouette_min} a {silhouette_max}, Davies-Bouldin da {davies_bouldin_min} a {davies_bouldin_max}

## fragment: curves_axes_silhouette_only

silhouette da {silhouette_min} a {silhouette_max}

## hint: curves

- Cosa mostra: come cambiano silhouette e Davies-Bouldin al crescere di `n_clusters`, con una linea per ogni linkage. `single` non è disegnato: i suoi valori sono nelle tabelle sotto.
- I pannelli: {panels}.
- Gli assi sono gli stessi in tutti i grafici di questa serie: {axes}. Sono l'intervallo dei dati di tutte le `metric` della run con un margine dell'8%, arrotondato al decimo. Il confronto è tra le forme delle linee: una silhouette di `metric` diverse non si confronta nel valore.
- Come si legge: conta la forma della linea su tutti i k, non un punto solo. Silhouette: più alta è meglio. Davies-Bouldin: più bassa è meglio.

## hint: cophenetic

- Cosa mostra: quanto l'albero di ogni linkage rispetta le distanze vere tra i soggetti. Serve a confrontare i linkage tra loro (stessa `metric`): più è alto, più l'albero è fedele.
- Cosa non dice: niente su quanti cluster scegliere.

## hint: agreement

- Cosa mostra: per ogni k, quanto due linkage producono la stessa partizione dei soggetti (ARI: 1 = identiche, 0 = quanto il caso).
- Come si legge: dove l'ARI è vicino a 1 per tutte le coppie, scegliere il linkage cambia poco; dove è basso, la partizione dipende dal linkage.
- Cosa non dice: quale dei due linkage sia quello giusto.

## hint: jump

- Cosa mostra: per ogni k, quanto è netto il taglio dell'albero in k cluster. Vicino a 1 non c'è un taglio netto; più è alto, più è netto.
- Cosa non dice: i linkage non si confrontano tra loro (altezze in unità diverse); e non dice se i cluster hanno senso clinico.

## hint: dendrogram

- Cosa mostra: l'albero delle fusioni; l'asse verticale è l'altezza a cui due gruppi si uniscono.
- Come si legge: una fusione molto più alta della precedente separa gruppi distinti; tagliare l'albero a una certa altezza dà quel numero di cluster.
- Limiti: sono mostrate solo le ultime fusioni (quante, sta sull'asse orizzontale della figura), quindi i k piccoli; le altezze non si confrontano tra linkage.

## hint: heatmap

- Cosa mostra: gli stessi numeri delle tabelle su tutta la griglia `min_cluster_size` × `min_samples`, un riquadro per metrica.
- Attenzione: ogni riquadro ha una sua scala di colore adattata ai dati, quindi le differenze piccole sembrano grandi.

## hint: dbcv_curves

- Cosa mostra: DBCV, quota di rumore, quota del cluster più grande e numero di cluster contro `min_cluster_size`, una linea per `min_samples`. Tutte le combinazioni, nessun filtro sul rumore.
- Un punto manca dove i cluster sono meno di 2: il DBCV non è definito, non vale 0.
- Cosa non dice: da solo il DBCV non dice quale combinazione scegliere; va letto accanto al rumore.
