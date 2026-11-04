# PCA in NEMESIS

- **Teoria:** [PCA (analisi delle componenti principali)](../../../knowledge/concepts/Machine_Learning/Unsupervised/Dimensionality_Reduction/pca.md)
  (Learning: `2_Concepts/Machine_Learning/Unsupervised/Dimensionality_Reduction/pca.md`)
- **Letteratura:** nei `sources` della nota teorica
- **Spiegazione rapida:** [cheatsheet](../../../management/cheatsheets/pca.md) (derivata, non è una fonte)

Metodo `pca` con un proprio contratto (`src/analysis/pca_method.py`) e due solutori. Parametri: `params_reduction.json`.
Altri metodi: [README](README.md). Rotazione: [pca_varimax](pca_varimax.md). Spiegazione passo per passo (pesi e punteggi, scree plot, snapshot, covarianza o correlazione): [employed_dim_reduction_methods](employed_dim_reduction_methods.md), sezione "PCA e rotazione varimax".

## Su cosa lo applichiamo
- **Dimensioni:** le matrici voxel-wise hanno $n \approx 5000$-5800 e $p \approx$ 220-290 mila. La covarianza $p \times p$ (circa 413 GB in float64 per $p = 227.235$) non entra in memoria, quindi si usa la via duale ($n \times n$) con `solver: "blocks"` (`src/analysis/covariance_pca.py`).
  Le matrici parcellate o per tratto ($p$ = 87 o 232) usano la covarianza tra variabili (`dual: false`). Scelta e numeri: [dim_reduction](../../guides/dim_reduction.md), "Il metodo `pca`".
- **Disconnettoma (continuo, [0, 1]):** si usa la covarianza, non la correlazione. Le variabili sono probabilità sulla stessa scala e, standardizzando, i voxel quasi sempre a zero peserebbero quanto gli altri.
  È anche la scelta di Thiebaut de Schotten et al. 2020; la motivazione è del progetto.
- **Lesioni (binarie):** la PCA si applica; su dati 0/1 le componenti sono dominate dai voxel colpiti più spesso e la prima tende a misurare il volume (da verificare caso per caso con l'R² con il volume;
  vedi `employed_dim_reduction_methods.md`, "Quanto dipende dal volume della lesione").
- **Uso a valle:** i punteggi PCA sono l'ingresso del clustering; per quello scopo si usano le componenti non ruotate (`employed_dim_reduction_methods.md`, "Quando usare cosa").

## Parametri usati (significato: documentazione della libreria)
| Parametro | Nel progetto |
|---|---|
| `solver` | `"blocks"` (PCA propria a blocchi di colonne); l'alternativa è `"sklearn"` |
| `standardize` | `false`: covarianza (solo centraggio) |
| `dual` | `true` sulle voxel-wise (solo con `blocks`) |
| `n_components` o `variance_share` | `150` (lesione), `12` (SDC, con varimax) |
| `rotation` | `"none"` (le rotazioni sono in [pca_varimax](pca_varimax.md)) |
| `chunk_columns`, `max_matrix_gib` | default del modulo (16384 colonne per blocco, soglia 8 GiB); solo memoria |
| `whiten` | non usato |

## Come lo ottimizziamo
L'unico iperparametro di sostanza è quante componenti tenere. La decomposizione è una sola e non cambia con $k$: si calcola una volta per sweep (`model_cache`).
1. **Griglia su `n_components`:** da 2 a 150 per le lesioni.
2. **Soglia di varianza:** `variance_share: 0.9` oppure la griglia su `n_components`.
3. **Scree plot:** lo spettro intero è salvato (`eigenvalues.npz`); `notebooks/post-results_analysis/pca_evaluation.ipynb` disegna lo scree plot.
4. Nessuna scelta automatica. Criterio di Kaiser e parallel analysis non sono implementati.

## Come leggiamo l'output
- **Varianza spiegata** cumulata delle componenti tenute: la misura del tuning (`cumulative_explained_variance`).
- **Dipendenza da variabili note:** R² delle componenti con volume e lato della lesione.
- **Riproducibilità:** correlazione delle mappe stimate su due metà dei soggetti, come in Thiebaut de Schotten et al. 2020.

## Attenzioni specifiche
- Il segno delle componenti è arbitrario: il repo fissa una convenzione per le mappe.
- Gli autovalori piccoli calcolati per la via duale sono meno precisi; non si usano oltre la soglia di varianza (`employed_dim_reduction_methods.md`, "Limite numerico").
