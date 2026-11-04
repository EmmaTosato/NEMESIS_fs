# PCA con rotazione varimax in NEMESIS

- **Teoria:** [PCA con rotazione varimax](../../../knowledge/concepts/Machine_Learning/Unsupervised/Dimensionality_Reduction/pca_varimax.md)
  (Learning: `2_Concepts/Machine_Learning/Unsupervised/Dimensionality_Reduction/pca_varimax.md`)
- **Letteratura:** nei `sources` della nota teorica
- **Spiegazione rapida:** [cheatsheet](../../../management/cheatsheets/pca-varimax.md) (derivata, non è una fonte)

Rotazione con `factor_analyzer` 0.5.1 (`Rotator`), configurazione SDC in `params_reduction_sdc.json`. Replica il metodo di "Data compression" di Thiebaut de Schotten et al. 2020
(PCA sulla matrice di covarianza con rotazione varimax, al massimo 500 iterazioni, 30 componenti su 46 per superare il 90% della varianza), su voxel invece che su regioni: [covariance_pca](../../dev/covariance_pca.md).
Altri metodi: [README](README.md). Prerequisito: [pca](pca.md). Spiegazione passo per passo: [employed_dim_reduction_methods](employed_dim_reduction_methods.md), sezione "La rotazione varimax".

## Su cosa lo applichiamo
- **Disconnettoma voxel-wise (SDC):** serve a leggere le componenti come territori di disconnessione (un fascio, un emisfero), cosa che i pesi PCA non ruotati, distribuiti su tutto il cervello, non permettono.
- **Lesione:** `rotation` è `"none"`.
- **Configurazione attuale** (scelta del progetto): si ruotano 150 componenti (`rotation_n_components: 150`) e si tengono le 12 ruotate con più varianza (`n_components: 12`).
- **A valle:** per il clustering il progetto consiglia i punteggi **non ruotati** (`employed_dim_reduction_methods.md`, "Quando usare cosa").

## Parametri usati (significato: documentazione della libreria)
| Parametro | Nel progetto |
|---|---|
| `rotation` | `"varimax"` (SDC), `"none"` (lesione) |
| `rotation_max_iter` | 500, come nel paper |
| tolleranza | non esposta (default della libreria `tol=1e-05`) |
| normalizzazione di Kaiser | non esposta, quindi attiva (default `normalize=True`) |
| `rotation_n_components` | 150 (SDC); se assente si ruotano tutte le `n_components` tenute |
| `n_components` | 12 (SDC); con `rotation_n_components`, le ruotate con più varianza |
| *loadings* passati alla rotazione | autovettori × $\sqrt{\lambda}$, fisso nel codice |

Il repo non passa `normalize`, `tol`, `power`, `kappa`, `gamma`: valgono i default di `factor_analyzer` 0.5.1 (verificati sulla firma installata). Che il paper usasse la normalizzazione di Kaiser non è detto.

## Come lo ottimizziamo
1. **Quante componenti ruotare** è la scelta che conta: il varimax è congiunto su tutte le componenti ruotate, quindi ruotarne 14 o 42 dà profili diversi (`employed_dim_reduction_methods.md`, "Cosa si guadagna e cosa si perde").
   Il paper tiene 30 componenti su 46 senza una soglia dichiarata; nel repo `variance_share: 0.9` dà 42 componenti su `07-10_s2.4-vol` ([covariance_pca](../../dev/covariance_pca.md)).
2. **Punteggio del tuning** (`cumulative_explained_variance`): se le componenti ruotate sono quelle tenute, la quota di varianza totale delle $k$ è la stessa con e senza rotazione, quindi non distingue `none` da `varimax`; la scelta si fa sulle mappe e sui controlli di valutazione.
   Con `rotation_n_components` le $k$ tenute sono un sottoinsieme delle ruotate e la loro quota è minore di quella delle prime $k$ della PCA: il punteggio distingue i due casi.
3. **Dove ha senso il tuning:** su `rotation_n_components`, non su `n_components` a rotazione fissa; cambiare $k$ senza `rotation_n_components` cambia la rotazione stessa.

## Come leggiamo l'output
- **Indipendenza dal volume e dal lato** (R², come nel paper) e **riproducibilità** delle mappe su due metà dei soggetti (Pearson tra mappe; nel paper 0,813 ± 0,079). Implementazione: `notebooks/post-results_analysis/pca_evaluation.ipynb`, descritta in `employed_dim_reduction_methods.md`.
- **Misure dei vicinati** ([evaluation_nemesis](evaluation_nemesis.md)): da leggere con cautela. Con `rotation_n_components` il sottospazio delle tenute è diverso da quello delle prime $k$ della PCA, e i punteggi ruotati sono riscalati a varianza 1, quindi le distanze euclidee tra soggetti cambiano rispetto alla PCA non ruotata.

## Attenzioni specifiche
- **Pesi uguali nel clustering:** i punteggi ruotati hanno varianza 1 per costruzione, quindi in una distanza euclidea ogni componente pesa uguale, anche una che spiega poca varianza. Per questo il progetto non usa i punteggi ruotati come ingresso del clustering.
- **Niente slice delle prime colonne:** una rotazione che tiene le componenti che ha ruotato non ha colonne ordinate, quindi le prime due non sono un riassunto legittimo (`docs/dev/models.md`, `embedding_for_viz`; `lessons_learned.md` #16). Con `rotation_n_components` il repo riordina per varianza.
- **Loadings o autovettori:** ruotare gli autovettori di norma 1 invece dei *loadings* scalati dà un'altra soluzione, e i punteggi per regressione degenerano in una proiezione (`docs/dev/models.md`).
- **Punteggi ruotati:** il repo li stima per minimi quadrati; derivazione in [covariance_pca](../../dev/covariance_pca.md), "Choices that are not the paper's".
- **Rotazioni oblique:** il repo le rifiuta, perché lo stimatore dei punteggi presuppone componenti scorrelate.
