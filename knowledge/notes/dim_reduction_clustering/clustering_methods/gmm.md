# Gaussian Mixture Model (GMM)

> Metodo a modello: `"gmm"` in `CLUSTERING_METHODS` (`src/analysis/clustering.py`), implementato con `sklearn.mixture.GaussianMixture` (scikit-learn 1.8.0 nell'ambiente `nemesis`). Parametri in `config/registry/params_clustering.json`, voce `"gmm"`.
>
> Indice di tutti i metodi: [`README.md`](README.md). Metriche condivise (silhouette, Calinski-Harabasz, Davies-Bouldin, ARI, NMI): [`evaluation_metrics.md`](evaluation_metrics.md). BIC, AIC e ICL, specifiche di questo metodo, sono definite qui.

## 1. Cosa fa

Assume che i dati siano stati generati da una **mistura di $k$ distribuzioni Gaussiane**, una per cluster, e ne stima i parametri: pesi, medie e matrici di covarianza [4, 5, 6]. Ogni soggetto riceve una **probabilità di appartenenza** a ciascuna componente (*soft clustering*); l'etichetta finale è la componente con la probabilità più alta [5, 7].

Nella tassonomia di Dinh et al. è il metodo di riferimento del clustering **model-based**: si sceglie un modello generativo, lo si stima con Expectation-Maximization e si sceglie $k$ con BIC o AIC [4].

## 2. Perché lo fa: modello, EM e scelta del modello

### Il modello

$$
p(x) = \sum_{j=1}^{k} \pi_j\, \mathcal{N}(x \mid \mu_j, \Sigma_j),
\qquad \pi_j \ge 0,\; \sum_j \pi_j = 1 .
$$

I parametri $\theta = \{\pi_j, \mu_j, \Sigma_j\}$ si stimano massimizzando la log-verosimiglianza dei dati [5, 6]:

$$
\ell(\theta) = \sum_{i=1}^{n} \log \sum_{j=1}^{k} \pi_j\, \mathcal{N}(x_i \mid \mu_j, \Sigma_j).
$$

Il logaritmo di una somma non si massimizza in forma chiusa [5]: si usa l'algoritmo EM.

### Expectation-Maximization

EM (Dempster, Laird & Rubin [1]) tratta l'appartenenza di ogni punto a una componente come una variabile nascosta e alterna due passi:

- **E-step**: con i parametri correnti calcola la **responsabilità** di ogni componente per ogni punto,
$$
\gamma_{ij} = \frac{\pi_j\, \mathcal{N}(x_i \mid \mu_j, \Sigma_j)}{\sum_{l=1}^{k} \pi_l\, \mathcal{N}(x_i \mid \mu_l, \Sigma_l)} .
$$
- **M-step**: riaggiorna i parametri usando le responsabilità come pesi, con $N_j = \sum_i \gamma_{ij}$:
$$
\pi_j = \frac{N_j}{n}, \qquad
\mu_j = \frac{1}{N_j}\sum_i \gamma_{ij}\, x_i, \qquad
\Sigma_j = \frac{1}{N_j}\sum_i \gamma_{ij}\,(x_i-\mu_j)(x_i-\mu_j)^\top .
$$

Dempster et al. dimostrano che ogni iterazione non fa diminuire la verosimiglianza [1]. Come per K-means, la convergenza è verso un massimo **locale**, quindi l'inizializzazione conta [5, 7]. Bicego descrive EM come "simile a K-means, ma con un grado di appartenenza" invece di un'assegnazione rigida [5].

scikit-learn aggiunge `reg_covar` alla diagonale di ogni $\Sigma_j$ per garantire che le covarianze restino positive [7].

### Forma delle covarianze (`covariance_type`)

Vincolare $\Sigma_j$ cambia la forma possibile dei cluster e il numero di parametri da stimare: più flessibilità, stima meno stabile [5]. Fraley & Raftery [3] descrivono una famiglia di parametrizzazioni basata sulla decomposizione di $\Sigma_j$ in volume, forma e orientamento; le 4 opzioni di scikit-learn sono un sottoinsieme di quella famiglia.

| `covariance_type` | Significato [7] | Parametri di covarianza (codice sklearn, $d$ dimensioni) |
|---|---|---|
| `full` | ogni componente ha la sua matrice generale | $k\,\frac{d(d+1)}{2}$ |
| `tied` | tutte le componenti condividono la stessa matrice generale | $\frac{d(d+1)}{2}$ |
| `diag` | ogni componente ha la sua matrice diagonale | $k\,d$ |
| `spherical` | ogni componente ha una sola varianza | $k$ |

Il numero totale di parametri liberi $p$ aggiunge $k\,d$ medie e $k-1$ pesi (metodo `_n_parameters` di scikit-learn 1.8.0, letto nel codice installato).

### BIC e AIC

Per scegliere $k$ e `covariance_type` si confrontano modelli diversi con un criterio che bilancia adattamento e complessità. Con $\hat{L}$ la verosimiglianza massima raggiunta, $p$ i parametri liberi e $n$ i soggetti:

$$
\mathrm{BIC} = -2\ln \hat{L} + p \ln n \quad \text{(Schwarz [2])},
\qquad
\mathrm{AIC} = -2\ln \hat{L} + 2p \quad \text{(Akaike [8])}.
$$

Queste sono esattamente le formule del codice di scikit-learn (`bic` e `aic`, "the lower the better") [7]. Con $n \approx 5000$, $\ln n \approx 8.5$: il BIC penalizza ogni parametro circa 4 volte più dell'AIC, quindi tende a scegliere modelli più piccoli.

Fraley & Raftery [3] usano il BIC come criterio principale del clustering a modello (è il criterio del pacchetto R `mclust`, [4]), ma con il **segno opposto**: $2\ln\hat{L} - p\ln n$, da massimizzare. Stessa quantità, direzione invertita.

### ICL

BIC misura quanto bene la mistura descrive la **densità**, non quanto sono separati i cluster: se un gruppo vero non è Gaussiano, il BIC può usare più componenti per descriverlo e sovrastimare il numero di cluster. È la motivazione dell'*Integrated Completed Likelihood* di Biernacki, Celeux & Govaert [9], che aggiunge al BIC una penalità per le assegnazioni incerte. Nella forma implementata in `integrated_completed_likelihood` (`src/analysis/clustering_tuning.py`, funzione post-hoc non collegata alla pipeline), con la convenzione di segno di scikit-learn:

$$
\mathrm{ICL} = \mathrm{BIC} + 2\,\mathrm{EN}, \qquad \mathrm{EN} = -\sum_{i}\sum_{j}\gamma_{ij}\ln\gamma_{ij} .
$$

$\mathrm{EN}$ vale 0 se ogni soggetto appartiene con certezza a una componente e cresce con la sovrapposizione.

## 3. Il nostro contesto

- **Input**: embedding UMAP a 2, 3 o 10 componenti o score PCA (fino a 12 componenti in `s2.4-vol`), con circa 1570-5845 soggetti.
- **Numero di parametri**: con $d=2$ e $k=6$ `full` sono $18 + 12 + 5 = 35$; con $d=12$ e $k=30$ `full` sono $2340 + 360 + 29 = 2729$. Su 5845 soggetti è ancora stimabile, ma `full` ad alto $k$ si avvicina al limite in cui ogni componente ha pochi soggetti per parametro.
- **Forma dei gruppi**: la mistura assume gruppi ellissoidali [5]. Gli embedding UMAP non conservano del tutto la densità [10]: un gruppo visibile in UMAP non è necessariamente Gaussiano, e il BIC può spezzarlo in più componenti (sezione 2, ICL).
- **Produzione**: `gmm_cluster` usa `fit_predict`, cioè solo l'etichetta più probabile. Le probabilità soft (`predict_proba`) non vengono salvate (scelta del progetto).
- **Dimensione della sweep**: 29 valori di $k$ x 4 `covariance_type` = 116 fit per run. Il tempo per fit non è stato misurato separatamente.

## 4. Parametri

Default verificati con `inspect.signature(GaussianMixture)` su scikit-learn 1.8.0. "Progetto" è il valore in `params_clustering.json` (scelta del progetto).

| Parametro | Significato [7] | Range | Default sklearn | Progetto |
|---|---|---|---|---|
| `n_components` | Numero di componenti della mistura. | intero $\ge 1$ | 1 | base 6; griglia 2-30 |
| `covariance_type` | Forma delle covarianze (tabella in sezione 2). | `full`, `tied`, `diag`, `spherical` | `full` | base `spherical`; griglia tutte e 4 |
| `tol` | Soglia di convergenza sul guadagno medio del lower bound. | float $>0$ | 1e-3 | default |
| `reg_covar` | Regolarizzazione non negativa aggiunta alla diagonale delle covarianze. | float $\ge 0$ | 1e-6 | default |
| `max_iter` | Iterazioni EM massime. | intero | 100 | default |
| `n_init` | Inizializzazioni; si tiene la migliore. | intero $\ge 1$ | 1 | default (1) |
| `init_params` | Inizializzazione: `kmeans` (responsabilità da K-means), `k-means++`, `random` (responsabilità casuali), `random_from_data` (medie = punti dei dati). | 4 stringhe | `kmeans` | default |
| `random_state` | Seme dell'inizializzazione. | intero o `None` | `None` | 0 |

Il blocco `"stability"` del progetto prova `init_params` in `["kmeans", "random"]` con `n_init` in `[1, 5, 10, 15, 20]` e 5 semi, registrando il BIC.

## 5. Come si fa il tuning

1. **Stabilità dell'inizializzazione** (blocco `"stability"`, scelta del progetto): se il BIC a parità di $k$ varia molto tra semi a `n_init=1`, la sweep principale va letta con cautela o `n_init` va alzato. Lettura: `clustering_tuning_guide.md`.
2. **Sweep congiunta di `n_components` x `covariance_type`**: è legittima perché BIC e AIC sono fatti per confrontare modelli con numeri di parametri diversi sugli stessi dati [2, 3].
3. **Lettura di BIC e AIC**: più basso è meglio (convenzione sklearn). Si cerca un minimo, o il punto in cui la curva smette di scendere. Se la curva scende fino all'ultimo $k$ della griglia, la griglia non arriva al punto di svolta e il criterio non indica nulla in quel range (`clustering_tuning_guide.md`).
4. **ICL** come controllo post-hoc: se il BIC favorisce un $k$ alto ma l'ICL un $k$ basso, le componenti in più servono a descrivere la forma della densità, non gruppi separati [9].
5. **Indici geometrici** (silhouette, CH, DB) come confronto: [`evaluation_metrics.md`](evaluation_metrics.md).
6. **Stabilità del numero di cluster** (opzionale, blocco `"consensus"`): si veda [`evaluation_metrics.md`](evaluation_metrics.md), sezione 7.

## 6. Come si valuta l'output

- **BIC/AIC**: confrontabili solo tra modelli stimati sugli **stessi** dati $X$. Non si confrontano tra embedding o sessioni diverse.
- **Certezza dell'assegnazione**: le responsabilità $\gamma_{ij}$ dicono quanto ogni soggetto è vicino a un confine. Una quota alta di soggetti con probabilità massima vicina a $1/k$ indica componenti sovrapposte. Oggi la pipeline non le salva: si ricalcolano con `predict_proba`.
- **Dimensione e pesi delle componenti**: una componente con $\pi_j$ molto piccolo o pochi soggetti può servire solo a descrivere code o outlier.
- **Indici geometrici e riproducibilità tra semi** (ARI): [`evaluation_metrics.md`](evaluation_metrics.md).

## 7. Quando usarlo

- Quando i gruppi possono essere **ellissoidali, di dimensioni e orientamenti diversi** (`full`), cosa che K-means non rappresenta [5].
- Quando serve una **probabilità di appartenenza**, non solo un'etichetta [5].
- Quando si vuole un **criterio statistico** (BIC) per confrontare numero di cluster e forma delle covarianze [3, 4].
- Non quando i gruppi sono chiaramente non Gaussiani (forme curve, densità non ellissoidali) o quando molti soggetti dovrebbero restare non assegnati: lì [`hdbscan.md`](hdbscan.md) o [`adp.md`](adp.md).

## 8. Pro e contro

**Pro**
- Flessibile: la forma della covarianza controlla il compromesso tra flessibilità e stabilità della stima [5].
- Soft clustering: dà le probabilità di appartenenza [5].
- Criteri di selezione del modello con base statistica (BIC, AIC, ICL) [2, 8, 9].

**Contro**
- Funziona bene solo se i cluster sono approssimabili da Gaussiane [5].
- Stimare il numero di cluster resta un problema [5]; BIC misura la densità, non la separazione [9].
- Massimi locali: l'inizializzazione conta, anche se meno che per K-means [5].
- Il numero di parametri con `full` cresce come $d^2$.
- Ogni soggetto riceve un'etichetta: non esiste una classe "rumore".

## 9. Esempio semplice

Una dimensione, due componenti già stimate: $\pi_1 = \pi_2 = 0.5$, $\mu_1 = 0$, $\mu_2 = 4$, $\sigma_1 = \sigma_2 = 1$.

- Soggetto in $x=1$: le densità (a meno della costante comune) sono $e^{-1/2} \approx 0.607$ e $e^{-9/2} \approx 0.011$. Responsabilità: $\gamma_1 = 0.607 / (0.607 + 0.011) \approx 0.98$. Etichetta 1, con quasi certezza.
- Soggetto in $x=2$: è equidistante dalle due medie, $\gamma_1 = \gamma_2 = 0.5$. L'etichetta finale dipende da un pareggio: K-means lo assegnerebbe senza segnalare nulla, il GMM dice che il soggetto è sul confine.

## 10. Insidie

- **Segno del BIC**: scikit-learn lo minimizza [7], `mclust` e Fraley & Raftery lo massimizzano [3]. Leggere sempre la convenzione prima di confrontare con la letteratura.
- **BIC che scende sempre**: con gruppi non Gaussiani o tanti soggetti, componenti in più migliorano sempre la densità stimata. È un'informazione sulla forma dei dati, non un $k$ da scegliere [9].
- **`n_init=1` di default**: un solo massimo locale per combinazione, se la stability analysis non mostra che basta.
- **Covarianze degeneri**: una componente che collassa su pochi punti molto vicini ha varianza quasi zero; `reg_covar` serve proprio a mantenerle positive [7]. Un BIC molto basso con una componente minuscola va controllato.
- **`spherical` come base**: dà cluster simili a K-means; la differenza con K-means emerge solo con `diag`, `tied` o `full`.
- **Solo l'etichetta in produzione**: l'informazione di incertezza, il vantaggio principale del metodo, oggi non arriva ai risultati salvati.

## Fonti

1. Dempster, A. P., Laird, N. M., Rubin, D. B. (1977). *Maximum likelihood from incomplete data via the EM algorithm.* Journal of the Royal Statistical Society B, 39(1), 1-38. doi:10.1111/j.2517-6161.1977.tb01600.x.
2. Schwarz, G. (1978). *Estimating the dimension of a model.* Annals of Statistics, 6(2), 461-464. doi:10.1214/aos/1176344136.
3. Fraley, C., Raftery, A. E. (2002). *Model-based clustering, discriminant analysis, and density estimation.* Journal of the American Statistical Association, 97(458), 611-631. doi:10.1198/016214502760047131.
4. Dinh, T., Hauchi, W., Lisik, D., et al. (2025). *Data clustering: an essential technique in data science.* Expert Systems with Applications; arXiv:2412.18760. Copia locale: `knowledge/papers/methods/Dinh et al - 2025 - Data clustering an essential technique in data science/` (paragrafi su model-based clustering e MClust).
5. Bicego, M. (2021). *Il clustering, parte 2* (dispense, Università di Verona), sezione "Misture di Gaussiane". Copia locale: `knowledge/papers/methods/Slides_Bicego/`.
6. scikit-learn 1.8, guida utente "Gaussian mixture models". https://scikit-learn.org/1.8/modules/mixture.html.
7. scikit-learn 1.8, `sklearn.mixture.GaussianMixture`. https://scikit-learn.org/1.8/modules/generated/sklearn.mixture.GaussianMixture.html (default verificati con `inspect.signature`; formule di `bic`, `aic` e `_n_parameters` lette nel codice installato).
8. Akaike, H. (1974). *A new look at the statistical model identification.* IEEE Transactions on Automatic Control, 19(6), 716-723. doi:10.1109/TAC.1974.1100705.
9. Biernacki, C., Celeux, G., Govaert, G. (2000). *Assessing a mixture model for clustering with the integrated completed likelihood.* IEEE Transactions on Pattern Analysis and Machine Intelligence, 22(7), 719-725. doi:10.1109/34.865189.
10. McInnes, L., et al. *UMAP documentation: Using UMAP for clustering.* https://umap-learn.readthedocs.io/en/latest/clustering.html (copia locale: `knowledge/papers/methods/websites/Using_UMAP_for_Clustering.html`).
