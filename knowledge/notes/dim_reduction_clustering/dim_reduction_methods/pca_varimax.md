# PCA con rotazione varimax

Indice dei metodi: [README.md](README.md). Presuppone [pca.md](pca.md). La spiegazione passo per passo (perché ruotare non costa nulla, l'esempio delle quarte potenze, i punteggi dopo la rotazione, la tabella PCA contro ruotate, le mappe *t*) è in [`../employed_dim_reduction_methods.md`](../employed_dim_reduction_methods.md), sezione "La rotazione varimax"; il calcolo a blocchi e le scelte che non sono del paper sono in [`docs/dev/covariance_pca.md`](../../../../docs/dev/covariance_pca.md). Qui si raccolgono formule, parametri, tuning, valutazione e insidie.

## 1. Cosa fa

Prende le prime *k* componenti di una PCA e ne **ruota gli assi** dentro lo stesso sottospazio, finché ogni variabile pesa molto su una sola componente e quasi zero sulle altre ("struttura semplice") [1]. Il sottospazio, e quindi la ricostruzione dei dati, resta lo stesso; cambia solo come la varianza è distribuita tra le componenti [2, §2.2.4].

## 2. Perché lo fa: l'obiettivo matematico

Sia $\Lambda$ ($p \times k$) la matrice dei *loadings* delle prime *k* componenti (autovettori moltiplicati per $\sqrt{\lambda_j}$, la scelta del repo, vedi §4). Per ogni matrice ortogonale $R$ ($R^\top R = I$) le componenti ruotate $B = \Lambda R$ danno la stessa approssimazione della covarianza:

$$
B B^\top = \Lambda R R^\top \Lambda^\top = \Lambda \Lambda^\top .
$$

Tra tutte le $R$ equivalenti, il **varimax** (Kaiser 1958 [1]) sceglie quella che massimizza la somma, sulle componenti, della varianza dei *loadings* al quadrato:

$$
V(R) = \sum_{j=1}^{k} \left[ \frac{1}{p} \sum_{i=1}^{p} b_{ij}^4 - \left( \frac{1}{p} \sum_{i=1}^{p} b_{ij}^2 \right)^{\!2} \right], \qquad B = \Lambda R .
$$

La varianza dei $b_{ij}^2$ di una colonna è alta quando pochi *loadings* sono grandi e gli altri vicini a zero. Poiché una rotazione conserva $h_i^2 = \sum_j b_{ij}^2$ (la comunalità della variabile *i*), massimizzare $V$ spinge ogni variabile verso una sola componente.

**Normalizzazione di Kaiser.** Kaiser propone di applicare il criterio alle righe normalizzate $b_{ij}/h_i$, così le variabili con comunalità grande non dominano la rotazione, e di riscalare dopo [1]. `factor_analyzer.Rotator` lo fa per default (`normalize=True`) [3].

**Come si calcola.** Non c'è soluzione in forma chiusa oltre due componenti: si itera partendo da $R = I$; a ogni passo si calcola il gradiente $G$ di $V$, se ne fa la SVD $G = U\Sigma W^\top$ e si pone $R = UW^\top$, fino a convergenza o a `max_iter` [3]. Si trova un massimo locale; partendo sempre da $I$ il risultato è deterministico.

**Punteggi.** Il repo stima i punteggi ruotati per minimi quadrati, $\hat{\mathbf s} = (B^\top B)^{-1} B^\top \mathbf z$ per ogni riga centrata $\mathbf z$; con $\Lambda$ scalato per $\sqrt\lambda$ ne escono punteggi a varianza 1 e scorrelati. Derivazione e differenza dallo stimatore di Thurstone: [`docs/dev/covariance_pca.md`](../../../../docs/dev/covariance_pca.md), "Choices that are not the paper's".

**Famiglia.** Il varimax è un caso del criterio *orthomax*; `factor_analyzer` offre anche `quartimax`, `equamax`, `oblimax`, `geomin_ort` come rotazioni ortogonali [3]. Le rotazioni oblique (componenti correlate, es. promax) sono l'alternativa [2, 4]; il repo le rifiuta, perché lo stimatore dei punteggi presuppone componenti scorrelate.

## 3. Il nostro contesto

- **Perché c'è.** È il metodo di "Data compression" di Thiebaut de Schotten et al. 2020: PCA sulla matrice di covarianza con rotazione varimax, al massimo 500 iterazioni, 30 componenti su 46 per superare il 90% della varianza [5]. Il repo lo replica su voxel invece che su regioni (`docs/dev/covariance_pca.md`).
- **Disconnettoma voxel-wise.** L'obiettivo è leggere le componenti come territori di disconnessione (un fascio, un emisfero), cosa che i pesi PCA non ruotati, distribuiti su tutto il cervello, non permettono [2, §2.2.4].
- **Configurazione attuale** (`params_reduction_sdc.json`, scelta del progetto): si ruotano 150 componenti (`rotation_n_components: 150`) e si tengono le 12 ruotate con più varianza (`n_components: 12`).
- **A valle.** Per il clustering il progetto consiglia i punteggi **non ruotati** (`employed_dim_reduction_methods.md`, "Quando usare cosa"), per i motivi del §10.

## 4. I parametri

| Parametro | Significato | Valore nel repo | Default della libreria |
|---|---|---|---|
| `rotation` | criterio di rotazione ortogonale | `"varimax"` (SDC), `"none"` (lesione) | `Rotator(method="varimax")` [3] |
| `rotation_max_iter` | iterazioni massime | 500, come in [5] | `max_iter=500` [3] |
| tolleranza | arresto quando il criterio migliora meno di una frazione relativa | non esposta | `tol=1e-05` [3] |
| normalizzazione di Kaiser | rotazione sulle righe normalizzate | non esposta, quindi attiva | `normalize=True` [3] |
| `rotation_n_components` | quante componenti ruotare; assente, si ruotano tutte le `n_components` tenute | 150 (SDC) | — (parametro del repo) |
| `n_components` | quante tenere; con `rotation_n_components`, le ruotate con più varianza | 12 (SDC) | — |
| *loadings* passati alla rotazione | autovettori × $\sqrt{\lambda}$ | fisso nel codice | — |

Il repo non passa `normalize`, `tol`, `power`, `kappa`, `gamma`: valgono i default di `factor_analyzer` 0.5.1 (verificati sulla firma installata). Che il paper usasse la normalizzazione di Kaiser non è detto [5].

## 5. Come si fa il tuning

- **Quante componenti ruotare** è la scelta che conta: il varimax è congiunto su tutte le componenti ruotate, quindi ruotarne 14 o 42 dà profili diversi (`employed_dim_reduction_methods.md`, "Cosa si guadagna e cosa si perde"). Il criterio del paper è la quota di varianza (>90%) [5]; nel repo `variance_share: 0.9` dà 42 componenti su `07-10_s2.4-vol` (`docs/dev/covariance_pca.md`).
- Se le componenti ruotate sono quelle tenute, la quota di varianza totale delle *k* è la stessa con e senza rotazione, quindi il punteggio del tuning (`cumulative_explained_variance`) non distingue `none` da `varimax`: la scelta tra i due si fa sulle mappe e sui controlli del §6. Con `rotation_n_components` le *k* tenute sono un sottoinsieme delle ruotate e la loro quota è minore di quella delle prime *k* della PCA (le prime *k* massimizzano la varianza di qualunque sottospazio di dimensione *k*): il punteggio distingue i due casi.
- Un tuning ha senso su `rotation_n_components`, non su `n_components` a rotazione fissa: cambiare *k* senza `rotation_n_components` cambia la rotazione stessa.

## 6. Come si valuta l'output

- **Struttura semplice**: quanto i *loadings* al quadrato di ogni componente sono concentrati su poche variabili (il criterio $V$ stesso).
- **Varianza per componente dopo la rotazione**: somma dei $b_{ij}^2$ della colonna divisa per la varianza totale; serve per ordinare le componenti ruotate, che non hanno un ordine proprio.
- **Indipendenza dal volume e dal lato** (R², come in [5]) e **riproducibilità** delle mappe su due metà dei soggetti (Pearson tra mappe; nel paper 0,813 ± 0,079 [5]). Implementazione: `notebooks/post-results_analysis/pca_evaluation.ipynb`, descritta in `employed_dim_reduction_methods.md`.
- Le misure dei vicinati ([evaluation.md](evaluation.md)) vanno lette con cautela: la rotazione non cambia il sottospazio delle componenti ruotate (con `rotation_n_components`, le tenute ne sono un sottoinsieme: il sottospazio è diverso da quello delle prime *k* della PCA), e i punteggi ruotati sono riscalati a varianza 1, quindi le distanze euclidee tra soggetti calcolate sui punteggi cambiano rispetto alla PCA non ruotata (vedi §10).

## 7. Quando usarla

| Obiettivo | Scelta | Fonte |
|---|---|---|
| Interpretare le componenti come territori, confrontarsi con il paper | PCA + varimax | [2, §2.2.4; 5] |
| Ingresso di un clustering o di un'altra riduzione | PCA non ruotata | scelta del progetto (§10) |
| Componenti che si sospettano correlate tra loro | rotazione obliqua (non supportata dal repo) | [2, 4] |

Richman 1986, in una rassegna sulla rotazione delle componenti principali, sostiene che le componenti non ruotate possono produrre pattern che riflettono la forma del dominio più che la fisica del fenomeno, e che la rotazione dà pattern più stabili e interpretabili [4].

## 8. Pro e contro

| Pro | Contro |
|---|---|
| Componenti leggibili, ognuna su poche variabili [1] | Si perde l'ordine per varianza: la prima componente ruotata non è la più importante |
| Stessa ricostruzione e stessa varianza totale della PCA [2, §2.2.4] | Il risultato dipende da quante componenti si ruotano |
| Deterministica (parte da $R = I$) | Massimo locale, non necessariamente globale |
| È il metodo del paper di riferimento [5] | Produce componenti "pulite" anche quando i dati non hanno una struttura a gruppi: la pulizia non è prova di struttura |

## 9. Un esempio semplice

Due variabili, due componenti, *loadings* PCA $\Lambda = \begin{pmatrix} 0{,}7 & 0{,}7 \\ 0{,}7 & -0{,}7 \end{pmatrix}$: ogni variabile pesa uguale su entrambe le componenti. Ruotando di 45° ($R = \tfrac{1}{\sqrt2}\begin{pmatrix} 1 & 1 \\ 1 & -1 \end{pmatrix}$) si ottiene $B \approx \begin{pmatrix} 0{,}99 & 0 \\ 0 & 0{,}99 \end{pmatrix}$: la prima componente ruotata è la variabile 1, la seconda la variabile 2. $\sum_i b_{ij}^4$ passa da $2 \cdot 0{,}49^2 \approx 0{,}48$ a circa $0{,}96$ per colonna; la comunalità di ogni variabile ($\approx 0{,}98$) non cambia.

## 10. Insidie note

- **Pesi uguali nel clustering.** I punteggi ruotati hanno varianza 1 per costruzione: in una distanza euclidea ogni componente pesa uguale, anche una che spiega poca varianza. È il motivo per cui il progetto non usa i punteggi ruotati come ingresso del clustering (`employed_dim_reduction_methods.md`).
- **Niente slice delle prime colonne.** Una rotazione che tiene le componenti che ha ruotato non ha colonne ordinate: le prime due non sono un riassunto legittimo (`docs/dev/models.md`, `embedding_for_viz`; `lessons_learned.md` #16). Con `rotation_n_components` il repo riordina per varianza.
- **Loadings o autovettori.** Ruotare gli autovettori di norma 1 invece dei *loadings* scalati dà un'altra soluzione, e i punteggi per regressione degenerano in una proiezione (`docs/dev/models.md`, test di regressione citato lì).
- **Segni.** Una rotazione può invertire il segno di una componente: punteggi e mappe vanno orientati insieme.
- **Normalizzazione non dichiarata.** Due implementazioni di "varimax" possono differire per la normalizzazione di Kaiser [1, 3]; confrontando con un paper va verificato (qui non è verificabile [5]).

## Fonti

1. Kaiser, H. F. (1958). *The varimax criterion for analytic rotation in factor analysis.* Psychometrika 23(3): 187-200. https://doi.org/10.1007/BF02289233
2. Sorzano, C. O. S., Vargas, J., Pascual-Montano, A. (2014). *A survey of dimensionality reduction techniques.* arXiv:1403.2877 (in `knowledge/papers/methods/`), §2.2.4 "PCA rotations and Sparse PCA".
3. `factor_analyzer` 0.5.1, `factor_analyzer.rotator.Rotator` (firma e sorgente installati: `method='varimax', normalize=True, max_iter=500, tol=1e-05`). https://factor-analyzer.readthedocs.io/en/latest/factor_analyzer.html
4. Richman, M. B. (1986). *Rotation of principal components.* Journal of Climatology 6(3): 293-335. https://doi.org/10.1002/joc.3370060305
5. Thiebaut de Schotten, M., Foulon, C., Nachev, P. (2020). *Brain disconnections link structural connectivity with function and behaviour.* Nature Communications 11. https://doi.org/10.1038/s41467-020-18920-9 (Methods, "Data compression"; Results).
