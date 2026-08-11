# Guida ai Dataset

Questa guida chiarisce quali sono i Dataset (coorti cliniche) utilizzati nel progetto NEMESIS, come sono composti e cosa viene effettivamente trasferito nel workspace locale per l'analisi.

I dati grezzi e processati risiedono sul server **EBRAIN**, accessibili tramite il punto di montaggio remoto `/data/corbetta/Clinical_connectome`.

---

## 📊 Coorti Cliniche Supportate

Attualmente sono gestite 4 coorti. Sebbene sia in corso un processo di armonizzazione (usando lo standard `BIDS`), storicamente derivano da acquisizioni diverse. Le risoluzioni geometriche differiscono tra gli ospedali.

| Dataset | Soggetti stroke stimati | Voxel Size (Ris. 3D) | Maschera Manuale Normalizzata |
| :--- | :---: | :--- | :---: |
| **`UNIPD/WashU`** | ~251 | 2.0 mm | Presente (maggior parte) |
| **`UNIPD/PSP`** | ~237 | 1.0 mm | Presente (maggior parte) |
| **`UNIPD/PASPORT`** | ~97 | 1.0 mm | Presente (maggior parte) |
| **`UKLFR/stroke_UKLFR`**| ~735 | 1.5 mm | Presente (quasi totalità) |

> ⚠️ **Nota vitale per la matrice lesionale**: 
> Data la disparità del Voxel Size (da 1 a 2 mm), durante l'esecuzione di `build_lesion_matrix` viene effettuato un **resampling spaziale**. Le lesioni vengono "deformate" e allineate su un'unica griglia omogenea (il `reference_template_path`), tipicamente a 2mm per rispettare lo standard MNI152 di FSL.

---

## 🗂️ Tipi di Dato (Objects) Esistenti

La pipeline *Retrieve Data* pesca "oggetti" da sorgenti asimmetriche. Questo significa che non tutte le informazioni esistono contemporaneamente per ogni dataset.

### 1. Maschere Manuali delle Lesioni (`lesion`)
- **Path logico**: `lesion/manual_masks/anat/lesion_mask`
- **Descrizione**: L'oggetto centrale del progetto. Sono state disegnate a mano e collocate nello spazio MNI. Presenti trasversalmente su **tutti e 4 i dataset**.

### 2. Dati Clinici e Anagrafici
- **Path logico**: `participants.tsv`
- **Descrizione**: Informazioni sui pazienti. Disponibile per tutti e 4 i dataset (incluso WashU con 319 pazienti).
- **Campi Principali**: `age`, `sex`, `handedness`, `education`, `lesion_side`.
- **Gruppo soggetto (`disease_id`)**: `ST` (Stroke) e `HC` (Healthy Controls). 
- **Punteggi Clinici (solo WashU)**: 
  - *Gravità Globale*: `NIHSS` e suoi sotto-item (copertura ~73%).
  - *Motorio*: `ARAT_L/R` (~98%), `9HPT_L/R` (~66%).
  - *Linguaggio*: `Boston_nam` (~96%).
  - *Cognitivo*: `Clock` (~66%), `Corsi` (~34%).
  - *(GDS_15 assente per questa specifica coorte FC).*

### 3. Matrici di Connettività Funzionale (`feature`)
- **Path logico**: `feature/func/FC-pearson`
- **Descrizione**: Dati sulle connessioni sinaptiche/funzionali dei pazienti espresse come matrici numeriche.
- **Disponibilità**: Attualmente, esistono sul server **SOLO per la coorte WashU**.
- Se il *Retrieval Data* richiede le `feature` per tutti e 4 i dataset, agirà "in modo intelligente" scaricando solo WashU e restituendo dei Warning per i restanti tre, senza fermarsi in errore.

### 4. Lesioni Grezze (Raw)
- **Descrizione**: Lesioni in spazio nativo non normalizzato (path logico: `lesion/raw/anat/lesion_roi`).
- **Disponibilità Locale**: Pur esistendo sul server, per decisione architetturale **non vengono mai copiate nel workspace locale**. Tutto il nostro studio richiede tassativamente coordinate spaziali omogenee.