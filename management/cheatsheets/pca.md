# PCA

## Cosa fa

- Trova nuovi assi, le **componenti**, lungo cui i soggetti differiscono di più.
- Ogni componente è una **combinazione lineare** delle variabili originali: una somma pesata dei voxel.
- Le componenti sono **ordinate per varianza spiegata**: la prima conta più della seconda.
- Tenendo le prime *k* componenti, ogni soggetto è riassunto da *k* numeri invece che da centinaia di migliaia di voxel, perdendo il meno possibile della variabilità.

## Che tipo di metodo è

- **Lineare**: non trova strutture curve.
- **Deterministico**: stessi dati, stesso risultato.
- **Non supervisionato**: usa solo la matrice, non conosce lato, NIHSS o altre variabili.
- Le componenti sono **ortogonali** per costruzione, e pochi soggetti con valori estremi possono dominarne una.
- Nel progetto è calcolata sulla **covarianza**: colonne centrate, non standardizzate, perché tutti i voxel sono sulla stessa scala.

## Cosa restituisce

| Oggetto | Cos'è | Dimensione |
|---|---|---|
| **Varianza spiegata** | quanta variabilità cattura ogni componente | una per componente |
| **Loadings** (pesi) | il peso di ogni voxel nella componente; uguali per tutti i soggetti. | voxel × componenti |
| **Score** | la posizione di ogni soggetto sulla componente | soggetti × componenti |

- Lo score dice quanto il pattern del soggetto si allinea alla mappa, e con che intensità. Alto in valore assoluto vuol dire che la mappa è molto presente nel soggetto.
- Il **segno** indica la direzione rispetto alla mappa, ma il segno della componente stessa è arbitrario.
- Nota di vocabolario: tecnicamente i pesi sono gli autovettori, e i *loadings* in senso stretto sono gli autovettori scalati per la radice dell'autovalore. Nella slide si possono usare come sinonimi.

## Esempio concreto

Tre voxel (valori già centrati) e una componente con pesi (0,6; 0,0; 0,8):

| Soggetto | voxel₁ | voxel₂ | voxel₃ | Score |
|---|---|---|---|---|
| 1 | 2 | −1 | 1 | 0,6·2 + 0,0·(−1) + 0,8·1 = **2,0** |
| 2 | −1 | 3 | −2 | 0,6·(−1) + 0,0·3 + 0,8·(−2) = **−2,2** |

- I pesi sono gli stessi per tutti i soggetti:
  - tra le due righe cambiano i valori dei voxel, quindi cambia lo score;
  - i pesi cambiano solo passando da una componente all'altra.
- Un peso nullo (voxel₂) esclude quel voxel dalla componente.
- Il soggetto 1 ha lo score positivo e il soggetto 2 negativo: stanno ai due lati opposti della stessa componente.

Approfondimento: `knowledge/notes/dim_reduction_clustering/employed_dim_reduction_methods.md`, sezione "PCA e rotazione varimax".
