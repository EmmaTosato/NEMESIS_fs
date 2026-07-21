# Guida ai Dataset

Questa guida spiega in modo chiaro quali sono i Dataset attualmente utilizzati nel progetto NEMESIS, come sono composti alla sorgente, e cosa viene effettivamente trasferito nel tuo workspace per l'analisi.

I dati grezzi e processati vivono sul server `EBRAIN` e sono accessibili tramite il punto di montaggio remoto `/data/corbetta/Clinical_connectome`.

## Cosa c'è dentro ai Dataset

Esistono 4 coorti cliniche (Dataset) supportate. Anche se stiamo portando avanti un imponente sforzo di armonizzazione (usando lo standard `BIDS`), storicamente questi dati provengono da acquisizioni diverse, quindi la risoluzione geometrica dei cervelli è leggermente diversa per ciascun ospedale.

Ecco la copertura attuale delle lesioni per dataset:

| Dataset | Soggetti stroke previsti | Voxel Size delle lesioni | Lesione Manuale Normalizzata Presente |
|---|---:|---|---:|
| `UNIPD/WashU` | ~251 | 2.0 mm | Sì (sulla maggior parte) |
| `UNIPD/PSP` | ~237 | 1.0 mm | Sì (sulla maggior parte) |
| `UNIPD/PASPORT` | ~97 | 1.0 mm | Sì (sulla maggior parte) |
| `UKLFR/stroke_UKLFR`| ~735 | 1.5 mm | Sì (sulla quasi totalità) |

*Nota vitale per la matrice lesionale: dato che i voxel size (le "dimensioni dei pixel" 3D) variano da 1 mm a 2 mm a seconda dell'ospedale, quando la pipeline `build_lesion_matrix` unisce le lesioni, esegue internamente un "Resampling" spaziale per deformarle dolcemente tutte alla stessa identica griglia, usando il `reference_template_path` (tipicamente quello a 2mm per standardizzazione sul formato FSL MNI152).*

## Tipi di Dato (Objects) Esistenti

Quando chiediamo dei file tramite la pipeline di *Retrieval Data*, andiamo a pescare oggetti da sorgenti asimmetriche. Questo significa che non tutti i dataset posseggono tutto.

### 1. Maschere Manuali delle Lesioni
- **Path logico**: `lesion/manual_masks/anat/lesion_mask`
- È l'oggetto d'oro del progetto. Queste sono state disegnate, processate, e incasellate nel formato spazio MNI. È presente trasversalmente su tutti e 4 i dataset. Ed è quello che copiamo di base per tutte le analisi.

### 2. Dati Clinici e Anagrafici
- **Path logico**: `participants.tsv`
- Contiene età, sesso, punteggi clinici dei soggetti. È fornito per PSP, PASPORT e UKLFR, ma ad oggi la sorgente di WashU ne è sprovvista in questo formato per come sono state generate le derivate.

### 3. Matrici di Connettività (Feature Funzionali)
- **Path logico**: `feature/func/FC-pearson`
- Questi dati contengono le connessioni sinaptiche/funzionali dei pazienti espresse tramite matrici. Attualmente, le feature funzionali esistono sui server **SOLO per la coorte WashU**.
- Se esegui un comando di *Retrieval Data* chiedendo la connettività per tutti e 4 i dataset, la pipeline è sufficientemente intelligente da capire che mancano strutturalmente in tre dataset: si limiterà a scaricare la parte WashU notificandoti un warning per le restanti.

### 4. Lesioni Grezze (Raw)
- Esistono anche le lesioni a crudo (nello spazio nativo non normalizzato) in `lesion/raw/anat/lesion_roi`. Pur esistendo sul server, per precise decisioni progettuali, **non vengono copiate nel workspace locale**. Tutto il nostro studio di analisi, embedding e clustering richiede dati in coordinate spaziali omogenee e standardizzate.