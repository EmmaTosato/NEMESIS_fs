# Guida al notebook di confronto tra run di clustering

`clustering_comparison.ipynb`, sotto `notebooks/post-results_analysis/`, lavora su run di clustering già **prodotte** (`fine_tuning: false`, lette da `results/<lesion|sdc>/clustering/production/<metodo>/<embedding>/<run_name>/`). La scelta di `k`/iperparametri è fatta altrove (`clustering.py --fine_tuning true`, `tuning_results.csv`/`tuning_plot.png`): qui non si sceglie niente in automatico (`code_standards.md` §0), si leggono tabelle e grafici.

La valutazione di **una run alla volta** non ha un notebook: sta nell'app Dash, nei pannelli "Clustering evaluation" (indici geometrici o DBCV, statistica del modello, appartenenza ai cluster; `docs/guides/embedding_app.md`) e "Cluster description" (variabili cliniche per cluster, senza test; `docs/dev/cluster_description.md`). Per scegliere i parametri si leggono invece `report.md` e le figure del tuning (`docs/guides/evaluate_clustering_tuning.md`).

## Scope: dove vive ogni analisi

Il criterio (empirica contro interpretativa) è in [`exploration.md`](exploration.md). Il confronto è **empirico**; l'interpretazione (mappe, soggetti rappresentativi, composizione dei cluster) è nell'app Dash.

| Analisi | Dove |
|---|---|
| Metriche geometriche e del modello di una run | app Dash, pannello "Clustering evaluation" |
| Tabelle descrittive per cluster su età, sesso, NIHSS, volume, dataset, lato, sede dominante (nessun test) | app Dash, pannello "Cluster description" |
| Accordo tra partizioni (ARI/NMI/VI), contingency, abbinamento e Jaccard tra cluster di run diverse | `clustering_comparison` |
| Distanze tra cluster **nello spazio dell'embedding** (centroidi, Mahalanobis, linkage) | `clustering_comparison` |
| Mappe di overlap e disconnessione, soggetti rappresentativi | app Dash |
| Distanze tra cluster **nello spazio delle mappe o del profilo clinico** | nessun notebook (non implementato) |
| Perché due cluster abbinati differiscono (A∩B, A\B, B\A descritti con le variabili esterne) | nessun notebook (non implementato) |

I casi di confine seguono il criterio: una distanza calcolata sulle coordinate dell'embedding è empirica; una calcolata su mappe anatomiche o variabili cliniche descrive i cluster ed è interpretativa. Un'analisi che serve a più di un posto (l'abbinamento dei cluster) vive come funzione in `src/analysis/`, perché i notebook non si importano tra loro.

È un notebook locale, non una pipeline CLI:

```bash
conda activate nemesis
jupyter lab notebooks/post-results_analysis/clustering_comparison.ipynb
```

Nessun dataset sintetico: le run si scelgono a mano in `SELECTED_RUNS` (path della colonna `output` di `list_production_runs`).

---

## `clustering_comparison.ipynb` — due o più run

Contiene le analisi che mettono a confronto più run:

- Parte 1, **stessa pipeline** (stesso `object_type`; varia il metodo di clustering e/o `k`, mai la pipeline a monte): ARI/NMI a coppie (heatmap) e match matrix (contingency) tra due run sugli stessi soggetti, e distanza centroide-centroide tra run che condividono lo stesso embedding (`require_shared_embedding` solleva altrimenti);
- Parte 2, **cross-modalità** lesion vs sdc sull'intersezione dei `subject_id` (`aligned_labels_intersection` stampa N per lato, intersezione ed esclusi, mai un merge silenzioso): contingency grezza e normalizzata, ARI/NMI/homogeneity/completeness, chi-quadro con residui standardizzati, purezza per cluster, profilo clinico per cluster;
- Parte 3, **centroidi a selezione libera**: i centroidi di ogni run scelta, una alla volta (senza vincoli), e la distanza centroide-centroide solo per le coppie che condividono lo stesso embedding (le altre sono saltate stampando il perché, mai in silenzio);
- Parte 4, **due cluster della stessa run** (stesse funzioni di `src/analysis/cluster_pair.py`; la sezione corrispondente dell'app Dash non è montata, vedi `docs/dev/cluster_comparison.md`): profilo demografico e clinico (Mann-Whitney e Fisher, p corretto Benjamini-Hochberg), regressione logistica del cluster 1 contro il cluster 2 con grafico degli odds ratio, distanza tra i centroidi nell'embedding rapportata al raggio dei cluster, mappe di overlap della lesione dei due cluster e loro differenza. Si sceglie la run (`PAIR_RUN`) e i due cluster (`LABEL_1`, `LABEL_2`); il primo è il riferimento per il segno di `r`, degli odds ratio e della differenza. Le mappe leggono le maschere di tutti i soggetti dei due cluster (circa 1 minuto su ~900 soggetti) e richiedono i `.nii.gz` in `data/`. La disconnessione per le run sdc non è nel notebook.

Le Parti 1-3 sono ancora quelle della versione unica del notebook, in attesa di riorganizzazione.

### Come si leggono le sezioni

Le definizioni di ARI, NMI, homogeneity e completeness sono in `knowledge/notes/dim_reduction_clustering/clustering_literature_survey.md` (§6, indici esterni). Sono indici **esterni**: confrontano due partizioni tra loro, non misurano la qualità di una sola.

**Prima di confrontare**

- Le due run devono avere lo stesso ordine di `subject_id` (`aligned_labels` solleva altrimenti): run su soggetti diversi vanno allineate con un merge su `subject_id` prima di confrontare le etichette per posizione.
- Per run di pipeline diverse (lesion vs sdc) i soggetti sono diversi per costruzione: `lesion` include soggetti senza un disconnettoma SDC calcolato, e viceversa. Il confronto si fa quindi sull'**intersezione** dei `subject_id`, riportata esplicitamente.
- Si confrontano lesion e sdc con lo **stesso metodo e lo stesso k**, così l'unica cosa che varia è la pipeline a monte e non anche il criterio di clustering.

**Heatmap ARI/NMI** (una cella per coppia di run)

- La matrice è simmetrica (l'ordine delle due run non conta) e la diagonale vale sempre 1 (una run con se stessa): si ignora. Il notebook mostra solo il triangolo sotto la diagonale, diagonale esclusa.
- Scala viridis da 0 a 1: viola/blu scuro = accordo basso, verde = medio, giallo = alto.
- A parità di somiglianza reale NMI esce di solito più alto di ARI: i colori dei due pannelli non coincidono cella per cella.
- Scala di lettura del numero (`AGREEMENT_SCALE` in `src/analysis/cluster_comparison.py`): una **regola empirica** nostra, senza una fonte in letteratura.

  | ARI | NMI | Lettura |
  |---|---|---|
  | < 0,2 | < 0,3 | accordo debole/trascurabile |
  | 0,2-0,4 | 0,3-0,5 | moderato |
  | 0,4-0,6 | 0,5-0,7 | discreto |
  | 0,6-0,8 | 0,7-0,85 | forte |
  | > 0,8 | > 0,85 | quasi identiche |

**Match matrix** (contingency tra due run)

- Righe = cluster della run A, colonne = cluster della run B; la cella (i, j) è il numero di soggetti che stanno nel cluster i di A **e** nel cluster j di B. È sovrapposizione soggetto per soggetto ed è la base da cui derivano ARI e NMI.
- Le etichette numeriche sono assegnate arbitrariamente da ciascun algoritmo: "cluster 0 di A" non è "cluster 0 di B". Non si cerca una corrispondenza tra numeri: si guarda dove va la massa.
- Massa concentrata in una colonna: quel cluster di A corrisponde (quasi) per intero a un cluster di B, accordo. Massa sparsa su più colonne: i due metodi lo dividono diversamente, disaccordo.
- Non è simmetrica come ARI/NMI: righe e colonne sono due run diverse, l'ordine conta. La somma di riga è la dimensione del cluster in A, la somma di colonna quella del cluster in B.

**Percentuali per riga e per colonna** (cross-modalità)

- **Per riga** (somma 100 su ogni riga): per ogni cluster lesionale, come si distribuisce nei cluster sdc. Risponde a: "il cluster X finisce prevalentemente in un solo cluster sdc o si spalma su più?".
- **Per colonna** (somma 100 su ogni colonna): per ogni cluster sdc, da quali cluster lesionali proviene. Risponde alla domanda simmetrica: "il cluster Y è fatto di soggetti di un solo cluster lesionale o è un mix?".
- Servono entrambe perché con cluster di dimensioni molto diverse un conteggio alto in una cella può essere "quasi tutto il cluster" in un verso e "una frazione minima" nell'altro, a seconda delle somme di riga e di colonna.

**ARI, NMI, homogeneity, completeness**

- NMI, con la normalizzazione di default di scikit-learn, è la media armonica di homogeneity e completeness. Per questo **nasconde l'asimmetria** tra le due: due coppie di run con la stessa NMI possono avere pattern di disaccordo opposti, e uno scenario "homogeneity bassa + completeness alta" (o il contrario) è invisibile guardando solo ARI/NMI. Si guardano quindi homogeneity e completeness **separatamente**.
- **Homogeneity**: quanto ogni cluster di A contiene soggetti di un solo cluster di B (1 quando A raffina B). **Completeness**: quanto i soggetti di un cluster di B restano insieme in un solo cluster di A (1 quando B raffina A). La direzione è fissata in `docs/dev/cluster_comparison.md`.
- Lettura: tutte in [0, 1] (ARI può scendere sotto 0); vicino a 1 = corrispondenza forte, vicino a 0 = nessuna relazione. Se sono tutte alte, le due pipeline catturano la stessa struttura; se sono sbilanciate o basse, si torna alla contingency e ai residui per vedere quali cluster causano lo squilibrio.

**Chi-quadro e residui standardizzati**

- Test chi-quadro di indipendenza sulla contingency. H0: l'appartenenza al cluster lesion è indipendente da quella al cluster sdc. La tabella degli **attesi** è quella che ci si aspetterebbe sotto H0, calcolata dai totali di riga e di colonna.
- Il **residuo standardizzato** di Pearson di una cella è (osservato - atteso) / radice(atteso): lo scarto in unità di deviazione standard, come uno z-score.
- Il p-value dice **se** le due partizioni sono associate (p basso: non indipendenti); i residui dicono **dove**, cioè quali coppie di cluster determinano l'associazione. Heatmap dei residui: rosso = la coppia co-occorre **più** del previsto, blu = **meno**, vicino a 0 = in linea con l'indipendenza.
- Il test richiede almeno 2 cluster per lato (`chi_square_independence` solleva altrimenti).

**Purezza per cluster**

- Per ogni cluster sorgente (riga della tabella per riga): `dominant_target_cluster` è il cluster di destinazione con la quota più alta, `purity_pct` quella quota in %. La tabella è ordinata dal cluster **meno puro** (disperso su più destinazioni) al più puro (converge quasi tutto in uno).
- Purezza alta: corrispondenza netta con un solo cluster di destinazione. Bassa o moderata: il cluster si spezza su più destinazioni. Le prime righe sono i cluster da investigare, le ultime le corrispondenze più solide.
- È **metà del quadro**: dice quanto un cluster sorgente converge in una destinazione (circa l'homogeneity del singolo cluster), non se quella destinazione è a sua volta "posseduta" solo da quel sorgente (il corrispettivo della completeness, da leggere sulla tabella per colonna).

**Centroidi**

- Un confronto diretto dei centroidi tra lesion e sdc **non ha senso**: vivono in spazi di feature diversi (voxel della lesione contro regioni SDC) e le coordinate, anche se entrambi gli embedding sono 2D, non sono la stessa grandezza. Il sostituto valido è il **fenotipo clinico di ciascun cluster** (profilo per cluster, Parte 2), che non dipende dalle coordinate.
- La distanza centroide-centroide ha senso solo se le due run condividono lo stesso embedding: stessi `session_name`, `reduction_method`, `reduction_n_components`, `reduction_metric` (quindi stesso `input_path` della dim reduction). Non basta che il metodo di clustering sia diverso: due embedding diversi condividono lo stesso spazio solo per coincidenza numerica. `require_shared_embedding` solleva se una delle quattro chiavi differisce; nella Parte 3 le coppie incompatibili sono saltate stampando il motivo.

**Parte 4, due cluster della stessa run**

- Il **primo cluster** (`LABEL_1`) è il riferimento: il segno di `r`, degli odds ratio e della mappa di differenza dipende da lui, e scambiare i due cluster inverte tutto. Le variabili cliniche vengono sempre da `participants.csv`, mai dal `metadata.csv` della run.
- **Variabili numeriche**: Mann-Whitney; `r` è la correlazione rank-biserial, tra -1 e 1, positiva se il cluster 1 ha valori più alti. **Categoriche**: test esatto di Fisher per ogni categoria; l'odds ratio è sopra 1 se la categoria è più frequente nel cluster 1.
- `p_fdr` è corretto per tutti i test insieme (Benjamini-Hochberg): si legge quello, non `p`.
- **Regressione logistica** sui soli soggetti dei due cluster, esito "sta nel cluster 1": odds ratio sopra 1 = la variabile rende più probabile il cluster 1, sotto 1 il cluster 2; per le numeriche è per una deviazione standard in più. Il punto è blu se l'intervallo di confidenza al 95% non contiene 1. È un'associazione, non una causa; se il volume della lesione è l'input del clustering (run lesion) è associato ai cluster anche per costruzione. Se la regressione non è stimabile (pochi soggetti, collinearità, separazione perfetta) solleva `ValueError` col motivo (`docs/dev/cluster_drivers.md`).
- **Distanza tra i centroidi**: euclidea nello spazio dell'embedding, da leggere rispetto al **raggio** di ciascun cluster (la distanza media dei suoi soggetti dal proprio centroide): se la distanza è molto maggiore dei raggi, i cluster sono ben separati. Solo per le run su embedding, perché su una run su dato grezzo la matrice è lo spazio delle feature.
- **Mappe**: per ogni cluster la % di soggetti con lesione in ogni voxel, e la differenza cluster 1 - cluster 2 (rosso = lesione più frequente nel cluster 1, blu nel cluster 2).

---

## Lettura consigliata

- Le metriche intrinseche dicono se *quella* run è compatta e separata, non se è "giusta" rispetto a un'altra.
- ARI/NMI alti tra metodi diversi sono un segnale di convergenza, non una prova che `k` sia corretto. ARI/NMI bassi tra lesion e sdc non sono un errore: feature space diversi non hanno obbligo di produrre la stessa partizione.

Metodologia e letteratura: `knowledge/notes/dim_reduction_clustering/clustering_literature_survey.md`.
