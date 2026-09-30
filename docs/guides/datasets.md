# Guida ai Dataset

Quali coorti cliniche usa NEMESIS, quanti soggetti hanno **davvero**, quali tipi di dato esistono per ciascuna e cosa di tutto questo è presente nel workspace locale.

I dati risiedono sul server **EBRAIN** (`/data/corbetta/Clinical_connectome`) e vengono copiati in locale sotto `data/clinical_connectome/derivatives/<centro>/<coorte>/` dalla pipeline di retrieval.

Tutti i numeri di questa pagina sono **verificati sul disco e sui tsv il 23-09-26**, non stimati. 



Per rigenerarli: `notebooks/exploration/dataset_availability.ipynb` (esplorazione diretta del filesystem) o `assets/metadata/participants.csv` (vedi sotto).

---

## Le 6 coorti, in numeri

| Dataset | Registro clinico (`participants_*.tsv`) | `manual_masks` | `sdc` | `features` (FC) | Griglia | Dettaglio |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **`UCL-UK/UCLStrokeData`** | 4119 (4119 ST) | **4119** | 4119 | — | 1.0 mm | reticolo 2 mm |
| **`UKLFR/stroke_UKLFR`** | 735 (735 ST) | 705 | 705 | — | 1.0 mm | reticolo 2 mm |
| **`UKE/WAKEUP_acute`** | 503 (503 ST) | 451 ️ | 451 | — | 1.0 mm | **1 mm** |
| **`UNIPD/WashU`** | 319 (251 ST + 68 HC) | 195 | 195 | **225** (169 ST + 56 HC) | 1.0 mm | reticolo 2 mm |
| **`UNIPD/PSP`** | 237 (237 ST) | 168 | 168 | — | 1.0 mm | **1 mm** |
| **`UNIPD/PASPORT`** | 97 (97 ST) | 83 | 83 | — | 1.0 mm | **1 mm** |
| **`UNIPD/NEMESIS_T0`** | 104 (76 ST nel registro) | 76 | 76 | — | 1.0 mm | reticolo 2 mm |
| **`UKE/SFB936_ses01`** | 57 (56 ST nel registro) | 56 | 56 | — | 1.0 mm | reticolo 2 mm |

Tutte le maschere sono in spazio `MNI152NLin6Asym` su griglia **1.0 mm**, `182x218x182`: verificato sugli header NIfTI di tutte e 5853.

### ⚠️ La griglia è 1 mm per tutti, il dettaglio no

`manual_masks/` non contiene segmentazioni disegnate a mano: è la lesione **già ricampionata da BCBToolKit** sulla propria griglia di lavoro a 1 mm, copiata dal `lesion-map` dell'output SDC e rinominata togliendo `res-1` (provenienza completa in [`docs/dev/retrieval.md`](../dev/retrieval.md); vedi anche `data/clinical_connectome/derivatives/README.md`, non versionato).

Un ricampionamento non crea dettaglio che non c'era. Per i dataset la cui segmentazione originale era a 2 mm, il risultato è un volume su griglia da 1 mm i cui voxel sono **costanti in blocchi 2x2x2 allineati** — ogni voxel originale replicato 8 volte. È questo che distingue le due colonne:

- **`reticolo 2 mm`** — 5150 soggetti (UCL-UK, UKLFR, WashU, NEMESIS_T0, SFB936). Nessun dettaglio sotto i 2 mm.
- **`1 mm`** — 702 soggetti (PASPORT, PSP, WAKEUP). Segmentazione genuinamente a 1 mm.

Verificato su **tutti e 5853** i soggetti, non a campione: per ciascuno si cerca, tra gli 8 allineamenti possibili, se esiste un raggruppamento in blocchi 2x2x2 con zero blocchi misti. Il verdetto è **uniforme dentro ogni dataset** (nessun dataset misto) e l'allineamento pulito è sempre `(1,1,1)`. L'unica eccezione non classificabile è `sub-STUKLFR0671`, la cui maschera è vuota.

**Perché conta.** `assets/metadata/lesion_metadata.csv` misura ogni maschera su due griglie, 1 mm e 2 mm, per distinguere una maschera vuota da una lesione minuscola persa nel sottocampionamento ([`docs/guides/metadata.md`](metadata.md)). Per i dataset a reticolo 2 mm il conteggio sulla griglia di produzione a 2 mm **ricostruisce esattamente** la maschera originale, quindi nessuna lesione può sparire e `lesion_volume_voxels_1mm` è esattamente `8 x lesion_volume_voxels_2mm`: non aggiunge informazione. La perdita per sottocampionamento è possibile **solo** per i 702 soggetti a 1 mm genuino — e infatti 2 dei 4 soggetti con volume 0 sulla griglia di produzione stanno in WAKEUP, con lesioni reali di 8 e 3 voxel.

**UKLFR e WashU sono passati a 1mm il 23-09-26** (prima 1.5mm/2.0mm nativo): `manual_masks/` è stata ri-sincronizzata da una copia fresca della stessa sorgente usata per l'SDC (`Clinical_connectome_stroke/<dataset>/lesion/`, già a 1mm), che ora coincide esattamente con `sdc/` per questi due dataset (0 discrepanze, vedi sotto) invece di essere un sottoinsieme diverso. Il **dettaglio** attuale di entrambi è su reticolo 2 mm (vedi la nota sopra): la griglia a 1 mm viene da quel ricampionamento, non da una segmentazione a 1 mm.

### Perché le colonne non coincidono

Il registro clinico e i dati su disco rispondono a due domande diverse, e vanno tenute separate:

- **Registro clinico** = quante persone sono arruolate nella coorte e hanno una riga di dati clinici. 
- **`manual_masks`/`sdc`/`features`** = per quanti di quei soggetti abbiamo effettivamente quel tipo di dato in locale.

Le differenze non sono errori, sono la realtà del dato. Due esempi concreti:

- **WashU**: 251 pazienti nel registro, 195 con maschera — **tutti e 195 hanno anche l'SDC** (corrispondenza esatta dal 23-09-26, prima 202 maschere di cui solo 195 con SDC). Le FC coprono 225 soggetti (169 pazienti + 56 controlli sani) — un insieme che si sovrappone solo in parte a chi ha la maschera.
- **UKLFR**: 705 con maschera, 705 con SDC — **corrispondenza esatta dal 23-09-26** (prima 697 maschere/705 SDC, con solo 673 in comune, 24 solo-maschera e 32 solo-SDC).

### Il conteggio unico: `assets/metadata/participants.csv`

Un soggetto per riga, con le colonne `has_lesion`/`has_sdc`/`has_features`, per i soli pazienti stroke presenti su disco — **5752 in totale**. È la fonte da interrogare invece di ricontare a mano; generata da `src/pipeline/populate_metadata.py`, vedi `docs/dev/metadata.md`. Non riflette ancora i 2 dataset sotto (onboarding non fatto) né il delta UKLFR/WashU del 23-09-26 — va rigenerata.

### 2 dataset aggiuntivi, non ancora onboarded

`UKE/SFB936_ses01` (56 soggetti) e `UNIPD/NEMESIS_T0` (76 soggetti) sono presenti in locale (`manual_masks/` + `sdc/` completo, 1mm, stesso schema di file degli altri) dal 23-09-26, ma **non fanno parte delle "6 coorti" sopra**: assenti da `config/registry/`, `assets/metadata/participants.csv` e dalla tabella dei tipi di dato sopra. Mancano ancora i `participants_*.tsv` clinici reali. Dettagli in `.claude/history/data_changelog.md` (23-09-26).

---

## Tipi di dato

Ogni tipo vive in una sottocartella dedicata dentro `derivatives/<centro>/<coorte>/`, con un numero fisso di file per soggetto.

### 1. Maschere di lesione — `manual_masks/` (1 file per soggetto)

- **Path logico retrieval**: `lesion/manual_masks/anat/lesion_mask`
- **File**: `manual_masks/{subject_id}/anat/{subject_id}_space-MNI152NLin6Asym_label-lesion_mask.nii.gz`
- L'oggetto centrale del progetto: maschere disegnate a mano e normalizzate in spazio MNI. Presenti per tutti e 6 i dataset.

### 2. Dati clinici e anagrafici — `data/clinical_connectome/metadata_tsv/participants_*.tsv`

Un file per dataset.

**Campi comuni a tutti e 6**: `participant_id`, `dataset`, `center_id`, `disease_id`, `age`, `sex`.

**`disease_id`**: `ST` (stroke) o `HC` (controlli sani). Solo WashU ha controlli sani (68 nel registro, 56 con FC).

**Copertura dei campi principali** (% sulle sole righe ST del tsv):

| Dataset | n (ST) | age | sex | handedness | education | lesion_side | NIHSS | clinical_date |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| UCL-UK | 4119 | 85% | 84% | assente | assente | assente | assente | assente |
| UKLFR | 735 | 100% | 100% | 68% | 72% | 99% | 99% | 32% |
| UKE | 503 | 100% | 100% | 0% | 0% | 95% | 100% | assente |
| WashU | 251 | 99% | 100% | 99% | 98% | 84% | 74% | 80% |
| PSP | 237 | 100% | 100% | 93% | 90% | 47% | 87% | 96% |
| PASPORT | 97 | 100% | 100% | assente | 0% | assente | assente | assente |

"assente" = la colonna non esiste proprio in quel tsv; `0%` = la colonna c'è ma è vuota per tutti.

Due conseguenze pratiche, entrambe gestite in `docs/dev/metadata.md`:
- **PASPORT non ha `NIHSS`** (solo `NIHSS_at_presentation`/`_24H`/`_3m`) né `lesion_side`; **UCL-UK non ha nessuno dei due**, e nemmeno una colonna sostitutiva.
- **`lesion_side` è incompleto anche dove esiste** (PSP 47%, WashU 84%): per questo verrà calcolato geometricamente dalla maschera dove manca.

**Punteggi comportamentali — solo WashU** (% sui 251 ST): `ARAT_L`/`ARAT_R` 94%, `Boston_nam` 92%, `NIHSS` 74%, `9HPT_L`/`9HPT_R` 65%, `Clock` 65%, `Corsi` 34%. `GDS_15` esiste come colonna ma è vuota al 100% per questa coorte.

**UCL-UK, unica eccezione sul formato ID**: negli altri 5 dataset `participant_id` è già nel formato canonico `sub-*`. UCL-UK ha il formato legacy del sito (`ST_UCL-UK_0001`), riconciliato in `participants.csv` (`subject_id` canonico + `original_id` col valore grezzo).

### 3. Connettività funzionale — `features/` (16 file per soggetto)

- **Path logico retrieval**: `feature/func/FC-pearson`
- **Disponibile solo per WashU** (225 soggetti: 169 ST + 56 HC). I 16 file per soggetto sono le 12 matrici FC (una per combinazione di atlante `Yan<n>TianS<n>Buckner7N`) più i sidecar di motion/outliers.
- Se una config di retrieval chiede `feature` per tutti i dataset, la pipeline scarica solo WashU e segnala gli altri con un WARNING, senza fermarsi (vedi `docs/dev/retrieval.md`).

### 4. Structural disconnectome — `sdc/` (34 file per soggetto)

- **Path logico retrieval**: `sdc/{disconnectome,lesion}-{map,mapstats,LF}` (`datatype="dwi"` è solo un'etichetta BIDS nello schema di `file_patterns.json`, non una cartella reale)
- Output Stage1+2 di BCBToolKit.
- I 34 file per soggetto: 
  - il volume di disconnessione voxel-wise (`res-1_desc-disconnectome.nii.gz`),
  - le parcellazioni per 15 atlanti (`LF-disconnectome_atlas-*.csv`),
  - gli equivalenti per la lesione ricampionata (`LF-lesion_atlas-*.csv`, 16 atlanti — include `yeh_hcp1065_streamline`),
  - i 2 `mapstats.tsv`.
- **Disponibile per tutti e 6 i dataset** (UCL-UK incluso dal 29-09-26), solo pazienti stroke.
- Sorgente: `Clinical_connectome/features/Clinical_connectome_stroke/<dataset>/lesion/{subject_id}/...` — un `project_root` diverso da quello di `lesion`/`feature`.

### 5. Lesioni grezze (raw) — mai copiate

Le lesioni in spazio nativo non normalizzato (`lesion/raw/anat/lesion_roi`) esistono sul server ma **per decisione architetturale non entrano mai nel workspace locale**: tutta l'analisi richiede coordinate spaziali omogenee.

---

## Copie locali ridotte

Le matrici finali (`build_lesion_matrix.py`; `mask_fc.py`+`build_fc_matrix.py`) sono già calcolate a partire dai dati grezzi, che quindi in locale servono solo per notebook/esplorazione. `scripts/archive_local_raw_data.py` riduce una cartella a **10 soggetti campione**, comprimendo il resto in un `.tar.gz` verificato (contenuto riletto e confrontato con quanto tarrato, prima di cancellare gli originali).

Le 5 `manual_masks/` sono complete. Restano ridotte solo due cartelle:

| Cartella | Popolazione reale | In chiaro | Nell'archivio |
| :--- | :---: | :---: | :---: |
| `UNIPD/WashU/features/` | 225 | 10 | 215 |
| `data/derived/features/masked_fc/` | 169 | 10 | 159 |

Ogni cartella ridotta contiene due file, entrambi generati dallo script:

- **`<nome>_archive_subjects.tsv`** — il registro macchina-leggibile della popolazione reale: una riga per soggetto con `source` = `kept_in_place` o `archive`. Serve a sapere chi esiste davvero **senza decomprimere niente**. Il gruppo del soggetto non è memorizzato perché derivabile: `group_of(subject_id)`.
- **`README_ARCHIVE.md`** — la versione per umani: totali, elenco dei soggetti in chiaro, comando di ripristino.

**Ripristino** (l'archivio sta *un livello sopra* la cartella, quindi si lancia da dentro la cartella stessa):

```bash
tar -xzf ../<nome>_archive.tar.gz -C .
```

## Ingombro su disco (locale, 29-09-26)

`data/clinical_connectome/derivatives/` pesa **10 GB** in totale:

| Tipo | Peso |
| :--- | ---: |
| `sdc/` (8 dataset, 5853 soggetti) | ~6.9 GB |
| `features_archive.tar.gz` (i 215 soggetti WashU compressi) | 2.1 GB |
| `features/` (solo WashU, i 10 soggetti in chiaro) | 222 MB |
| `manual_masks/` (8 dataset, 5853 soggetti) | ~919 MB |

Il salto di `manual_masks/` (da ~169 MB a ~919 MB) non è un errore: UKLFR e WashU sono passati a 1mm (vedi sopra), file molto più pesanti della loro risoluzione nativa precedente.

Dentro l'SDC, il peso è dominato dai `.nii.gz`: `disconnectome-map` ~61% del totale, `disconnectome-LF` (15 CSV) ~25%, `lesion-map` ~12%, `lesion-LF` (16 CSV) ~2%, mapstats trascurabile. Per scaricarne solo un sottoinsieme (es. i soli CSV parcellati, ~793 MB, sufficienti per una matrice tipo `build_sdc_matrix.py`) copia `config/pipelines/retrieval_sdc.json` riducendone la lista `retrieve` alle sole categorie che ti servono — vedi `docs/guides/retrieval.md`.
