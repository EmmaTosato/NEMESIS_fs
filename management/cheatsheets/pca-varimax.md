# PCA con rotazione varimax

## Cosa fa

- Parte dalla PCA e **ruota le prime k componenti**, mantenendole ortogonali.
- L'obiettivo è che ogni componente abbia pesi forti su poche variabili e quasi nulli sulle altre.
- La **varianza totale** spiegata dalle k componenti non cambia, ma si ridistribuisce tra loro.
- Le componenti diventano più interpretabili: "regioni" o pattern distinti.

## Che tipo di metodo è

- **Lineare**, **deterministico** e **non supervisionato**, come la PCA da cui parte.
- Dopo la rotazione le componenti **non sono più ordinate per varianza**.
- Nel progetto il massimo di iterazioni è un parametro (`rotation_max_iter`), 500 come in Thiebaut de Schotten et al. 2020.
- Per un clustering sulle componenti l'input consigliato sono i punteggi PCA non ruotati.

## Cosa restituisce

| Oggetto | Cos'è | Dimensione |
|---|---|---|
| **Pesi ruotati** | il peso di ogni voxel nella componente ruotata | voxel × componenti |
| **Score ruotati** | la posizione di ogni soggetto sulla componente ruotata; si ottengono per regressione e hanno tutti varianza 1 | soggetti × componenti |
| **Quota di varianza** | somma dei pesi al quadrato della componente, divisa per la varianza totale | una per componente |

## Esempio concreto

Quattro voxel e due componenti. Prima della rotazione ogni voxel pesa su entrambe; dopo, ognuno pesa su una sola:

| Voxel | PCA comp. 1 | PCA comp. 2 | Varimax A | Varimax B |
|---|---|---|---|---|
| 1 | 0,71 | 0,71 | 1 | 0 |
| 2 | 0,71 | 0,71 | 1 | 0 |
| 3 | −0,71 | 0,71 | 0 | 1 |
| 4 | −0,71 | 0,71 | 0 | 1 |

- Prima: "un mix di tutto". Dopo: A è la zona dei voxel 1-2, B quella dei voxel 3-4.
- Ogni voxel ha la stessa energia prima e dopo (0,71² + 0,71² = 1² + 0² = 1): cambia solo come si divide tra le componenti.
- Nei dati veri la struttura non è mai così pulita: l'esempio è costruito per mostrare l'effetto.

Approfondimento: `employed_dim_reduction_methods.md`, sezione "La rotazione varimax".
