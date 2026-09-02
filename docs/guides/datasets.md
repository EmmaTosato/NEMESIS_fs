# Guida ai Dataset

Questa guida chiarisce quali sono i Dataset (coorti cliniche) utilizzati nel progetto NEMESIS, come sono composti e cosa viene effettivamente trasferito nel workspace locale per l'analisi.

I dati grezzi e processati risiedono sul server **EBRAIN**, accessibili tramite il punto di montaggio remoto `/data/corbetta/Clinical_connectome`.

---

## Coorti Cliniche Supportate

Attualmente sono gestite 5 coorti. Sebbene sia in corso un processo di armonizzazione (usando lo standard `BIDS`), storicamente derivano da acquisizioni diverse. Le risoluzioni geometriche differiscono tra gli ospedali.

| Dataset | Soggetti stroke stimati | Voxel Size (Ris. 3D) | Maschera Manuale Normalizzata |
| :--- | :---: | :--- | :---: |
| **`UNIPD/WashU`** | ~251 | 2.0 mm | Presente (maggior parte) |
| **`UNIPD/PSP`** | ~237 | 1.0 mm | Presente (maggior parte) |
| **`UNIPD/PASPORT`** | ~97 | 1.0 mm | Presente (maggior parte) |
| **`UKLFR/stroke_UKLFR`**| ~735 | 1.5 mm | Presente (quasi totalità) |
| **`UCL-UK/UCLStrokeData`** | 4119 | 2.0 mm | Presente (verificato 21/08: 4119/4119 soggetti) |
| **`UKE/WAKEUP_acute`** | ~451 | — | Registrato solo per l'oggetto `sdc` (vedi punto 5 sotto) — nessuna maschera manuale/lesion retrieval definita per questo dataset oggi |

> **Nota vitale per la matrice lesionale**: 
> Data la disparità del Voxel Size (da 1 a 2 mm), durante l'esecuzione di `build_lesion_matrix` viene effettuato un **resampling spaziale**. Le lesioni vengono "deformate" e allineate su un'unica griglia omogenea (il `reference_template_path`), tipicamente a 2mm per rispettare lo standard MNI152 di FSL.

---

## Copie Locali: Campione Ridotto

Le matrici finali (`build_lesion_matrix.py`; `mask_fc.py`+`build_fc_matrix.py`) sono già calcolate a partire da questi dati grezzi — tenerli integri in locale non serve più per l'uso quotidiano, solo occupa spazio. `scripts/archive_local_raw_data.py` (26/08/26) aveva ridotto in locale più cartelle a **10 soggetti campione** (per notebook/esplorazione), comprimendo il resto in un `.tar.gz` verificato (contenuto riletto e confrontato con quanto tarrato, prima di cancellare l'originale) accanto alla cartella stessa. I 5 `manual_masks/` di questa pagina (WashU, PSP, PASPORT, UKLFR, UCL-UK) sono stati **riscompattati per intero il 01-09-26** — restano ridotte solo:

- `UNIPD/WashU/features/`
- `data/derived/features/masked_fc/` (10 soggetti comuni a tutte e 12 le combinazioni di atlante — `mask_summary.csv`/`runs.csv`/`demo/` non toccati)

Ogni cartella ancora ridotta ha un `README_ARCHIVE.md` con l'elenco esatto dei soggetti tenuti e il comando di ripristino (`tar -xzf <nome>_archive.tar.gz -C .`). Per `features` i dati completi restano comunque sempre recuperabili da EBRAIN via `retrieve_data.py` (vedi `docs/guides/retrieval.md`) — `masked_fc` non è su EBRAIN (è output calcolato da `mask_fc.py`), quindi lì il ripristino è: decomprimere l'archivio, oppure rilanciare `mask_fc.py` da zero (vedi `docs/guides/fc_matrix_building.md`).

`sub-STUNIPD0001` (WashU) è garantito sempre presente in chiaro nelle cartelle ancora ridotte, non per coincidenza d'ordinamento: è il `reference_template_path` hardcoded in `config/pipelines/build_lesion_matrix.json` (pinned esplicitamente in `scripts/archive_local_raw_data.py`).

> Se rilanci una di queste pipeline sull'intera coorte (non solo il campione locale), la discovery vedrà solo i soggetti superstiti per questi dataset finché non decomprimi l'archivio pertinente o non ri-recuperi da EBRAIN.

---

## Tipi di Dato (Objects) Esistenti

La pipeline *Retrieve Data* pesca "oggetti" da sorgenti asimmetriche. Questo significa che non tutte le informazioni esistono contemporaneamente per ogni dataset.

### 1. Maschere Manuali delle Lesioni (`lesion`)
- **Path logico**: `lesion/manual_masks/anat/lesion_mask`
- **Descrizione**: L'oggetto centrale del progetto. Sono state disegnate a mano e collocate nello spazio MNI. Presenti trasversalmente su **tutti e 5 i dataset**.

### 2. Dati Clinici e Anagrafici
- **Path logico**: `participants.tsv`
- **Descrizione**: Informazioni sui pazienti. Disponibile per tutti e 5 i dataset (incluso WashU con 319 pazienti; per UCL-UK/UCLStrokeData 4119 righe, verificato 21/08).
- **UCL-UK, unica eccezione sul formato ID**: negli altri 4 dataset `participant_id` è già nel formato canonico `sub-*` usato ovunque nel progetto. Solo UCL-UK ha `participant_id` grezzo nel formato legacy del sito (`ST_UCL-UK_0001`) — vedi `docs/dev/metadata.md` per come questo viene riconciliato in `assets/metadata/`.
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
- Se il *Retrieval Data* richiede le `feature` per tutti e 5 i dataset, agirà "in modo intelligente" scaricando solo WashU e restituendo dei Warning per i restanti quattro, senza fermarsi in errore.

### 4. Lesioni Grezze (Raw)
- **Descrizione**: Lesioni in spazio nativo non normalizzato (path logico: `lesion/raw/anat/lesion_roi`).
- **Disponibilità Locale**: Pur esistendo sul server, per decisione architetturale **non vengono mai copiate nel workspace locale**. Tutto il nostro studio richiede tassativamente coordinate spaziali omogenee.

### 5. Structural Disconnectome calcolato esternamente (`sdc`)
- **Path logico**: `sdc/dwi/{disconnectome,lesion}-{map,mapstats,LF}`
- **Descrizione**: Output Stage1+2 di BCBToolKit — la stessa computazione che fa la nostra `compute_sdc.py`/`src/sdc/`, ma questo run specifico non è passato dalla nostra CLI (`--mode manifest/run/aggregate`), quindi non ha `manifest.csv`/`_status/`/riga in `runs.csv` scritti da noi per questo run. Include il volume di disconnessione voxel-wise (`res-1_desc-disconnectome.nii.gz`), le statistiche aggregate (`mapstats.tsv`) e le parcellazioni per 15 atlanti (`LF-disconnectome_atlas-*.csv`), più gli equivalenti per la lesione stessa ricampionata (`LF-lesion_atlas-*.csv`, 16 atlanti — include anche `yeh_hcp1065_streamline`).
- **Disponibilità**: `UNIPD/WashU` (195), `UNIPD/PASPORT` (83), `UNIPD/PSP` (168), `UKLFR/stroke_UKLFR` (705), `UKE/WAKEUP_acute` (451) — tutti solo pazienti stroke (nessun HC in queste cartelle). Sorgente: `Clinical_connectome/features/Clinical_connectome_stroke/<dataset>/lesion/{subject_id}/...` (un `project_root` diverso da quello di `lesion`/`feature`, vedi `docs/dev/retrieval.md`).
- **Locale**: copiato via `config/pipelines/retrieval_sdc.json` sotto `sdc/` (stessa struttura pipeline-first di `lesion`/`feature`, vedi `docs/dev/retrieval.md`).
- **Peso** (1602 soggetti, tutti e 5 i dataset, verificato 26/08): `disconnectome-map` (.nii.gz voxel-wise) 61% del totale, `disconnectome-LF` (15 CSV parcellati) 25%, `lesion-map` (.nii.gz maschera ricampionata) 12%, `lesion-LF` (16 CSV) 2%, mapstats trascurabile — totale ~3 GB. Per scaricare solo un sottoinsieme (es. solo i CSV già parcellati, ~793 MB, sufficienti per una matrice tipo `build_lesion_matrix.py`), usa `scripts/download_sdc.py --categories disconnectome-LF lesion-LF ...` invece della config completa — vedi `docs/guides/retrieval.md`.