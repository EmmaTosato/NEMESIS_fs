# Agglomerative

## Cosa fa

- Parte con **ogni punto come cluster a sé**, poi fonde ripetutamente i **due cluster più vicini**, costruendo un dendrogramma.
- Il numero di cluster si sceglie **tagliando il dendrogramma** (`n_clusters`).
- `metric` misura la distanza tra due punti (euclidea, cosine, manhattan, dice...).
- `linkage` trasforma le distanze tra punti nella distanza tra due cluster, che contengono molti punti:

| linkage | distanza tra due cluster | effetto |
|---|---|---|
| single | la coppia di punti più vicina | tende a formare catene |
| complete | la coppia di punti più lontana | cluster compatti, ma un outlier può dominare |
| average | la media di tutte le coppie | compromesso tra single e complete |
| ward | fonde i due cluster che fanno crescere meno la varianza interna totale | cluster compatti e di taglia simile; richiede la distanza euclidea |

## Che tipo di metodo è

- **Gerarchico**, dal basso verso l'alto, **deterministico** e **non supervisionato**.
- Il numero di cluster non è nell'algoritmo: si decide dopo, tagliando l'albero.
- Nel progetto `linkage` e `metric` si variano insieme a `n_clusters`; `ward` esiste solo con la metrica euclidea, quindi le altre combinazioni con `ward` vengono scartate.

## Cosa restituisce

| Oggetto | Cos'è | Dimensione |
|---|---|---|
| **Etichetta** | il cluster di ogni soggetto, dato `n_clusters` | una per soggetto |
| **Dendrogramma** | l'albero delle fusioni, con l'altezza (distanza) a cui avviene ciascuna | n − 1 fusioni |

## Esempio concreto

Quattro punti su una retta, in posizione 0, 1, 5 e 7:

| Passo | Fusione | Altezza |
|---|---|---|
| 1 | {0} e {1} | 1 |
| 2 | {5} e {7} | 2 |
| 3 | {0, 1} e {5, 7} | dipende dal linkage |

Altezza del passo 3, dalle quattro distanze tra i due gruppi (0-5 = 5, 0-7 = 7, 1-5 = 4, 1-7 = 6):

| linkage | altezza |
|---|---|
| single | 4 (la più piccola) |
| complete | 7 (la più grande) |
| average | 5,5 (la media) |

- Tagliando a `n_clusters` = 2 si ottengono {0, 1} e {5, 7}, qualunque sia il linkage.
- Il linkage cambia a che altezza si fondono i due gruppi, e con più punti anche quali gruppi si fondono per primi.

Approfondimento: `clustering_literature_survey.md` (sezione sul clustering gerarchico), `clustering_tuning_guide.md` (dendrogramma, regola di ward).
