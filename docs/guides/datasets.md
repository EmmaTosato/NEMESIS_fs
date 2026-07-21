# Dataset guide

Questa guida descrive i dataset stroke che usiamo in NEMESIS: la sorgente di partenza, le caratteristiche che li distinguono e cosa copiamo davvero nel workspace locale.

La sorgente usata in questo repo è il mount di `Clinical_connectome` disponibile sul cluster, qui montato come `/data/corbetta/Clinical_connectome`.

## Cosa copiamo localmente

Il flusso di retrieval copia i dati dentro `data/clinical_connectome/` mantenendo la struttura dei dataset. In pratica, oggi copiamo:

* le lesioni manuali normalizzate in spazio MNI, cioè `lesion/manual_masks/anat/lesion_mask`
* `participants.tsv` quando è presente nella sorgente del dataset
* le feature funzionali `feature/func/FC-pearson` solo per `UNIPD/WashU`

Non copiamo, nel flusso standard, le maschere `lesion/raw/anat/lesion_roi`: esistono come informazione di sorgente e sono utili per il controllo qualità, ma non fanno parte del set locale usato dai pipeline correnti.

## Risoluzione delle lesioni nella sorgente

Le maschere lesionali sono già in spazio MNI152NLin6Asym, ma la risoluzione cambia tra dataset:

| dataset | voxel size | shape tipica | note |
|---|---|---|---|
| `UNIPD/PSP` | 1.0 mm isotropica | 182 × 218 × 182 | uniforme in tutto il dataset |
| `UNIPD/PASPORT` | 1.0 mm isotropica | 182 × 218 × 182 | uniforme in tutto il dataset |
| `UNIPD/WashU` | 2.0 mm isotropica | 91 × 109 × 91 | uniforme in tutto il dataset |
| `UKLFR/stroke_UKLFR` | 1.5 mm isotropica | 121 × 145 × 121 | due soggetti hanno una shape più piccola, ma la voxel size resta 1.5 mm |

Questo è importante perché il build della matrice lesionale lavora resamplando le maschere sul riferimento scelto: la risoluzione d’ingresso non è identica tra dataset, quindi non va mai assunta per convenzione.

## Copertura dei dataset

Il riepilogo corrente dei file di lesione nella sorgente mostra:

| dataset | soggetti nel summary | `lesion/manual_masks/anat/lesion_mask` presente | `lesion/raw/anat/lesion_roi` presente |
|---|---:|---:|---:|
| `UNIPD/WashU` | 251 | 202 | 202 |
| `UNIPD/PSP` | 237 | 168 | 0 |
| `UNIPD/PASPORT` | 97 | 83 | 83 |
| `UKLFR/stroke_UKLFR` | 735 | 697 | 735 |

Interpretazione pratica:

* `UNIPD/PSP`, `UNIPD/PASPORT` e `UNIPD/WashU` hanno una parte di soggetti senza maschera manuale nella sorgente corrente.
* `UKLFR` è il dataset più completo per la lesione grezza (`lesion_roi`), ma anche lì il flusso standard usa la maschera manuale normalizzata quando presente.
* La presenza di `lesion_roi` non implica che venga copiata: serve come confronto con la sorgente e per capire eventuali divergenze tra versioni del dato.

## Dati che entrano nel workspace locale

### `UNIPD/PSP`

* Lesioni copiate: sì, con voxel size 1 mm.
* `participants.tsv`: sì.
* Feature `FC-pearson`: no.
* `lesion_roi` grezza: no, non nel flusso standard.

### `UNIPD/PASPORT`

* Lesioni copiate: sì, con voxel size 1 mm.
* `participants.tsv`: sì.
* Feature `FC-pearson`: no.
* `lesion_roi` grezza: no, non nel flusso standard.

### `UNIPD/WashU`

* Lesioni copiate: sì, con voxel size 2 mm.
* `participants.tsv`: no, la sorgente non lo espone in questo dataset.
* Feature `FC-pearson`: sì, per le due atlanti registrate nel file patterns.
* `lesion_roi` grezza: no, non nel flusso standard.

### `UKLFR/stroke_UKLFR`

* Lesioni copiate: sì, con voxel size 1.5 mm.
* `participants.tsv`: sì.
* Feature `FC-pearson`: no.
* `lesion_roi` grezza: no, non nel flusso standard.

## Relazione con la matrice lesionale

Quando costruiamo la matrice lesionale, le maschere vengono prima allineate a un dataset di riferimento scelto come grid comune. Questo significa che:

* la differenza di risoluzione tra dataset è normale e attesa;
* la scelta del reference dataset influenza la griglia finale su cui tutte le lesioni vengono confrontate;
* per analisi voxel-wise, la voxel size di ingresso conta solo fino al resampling;
* per analisi parcellate, la lesione viene poi aggregata sulla parcellazione scelta.

Per il dettaglio operativo su come copiare i file dalla sorgente al workspace locale, vedi la guida di retrieval.