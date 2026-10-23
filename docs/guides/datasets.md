# Guida ai Dataset

Quali coorti cliniche usa NEMESIS, quanti soggetti hanno **davvero**, quali tipi di dato esistono per ciascuna e cosa di tutto questo è presente nel workspace locale.

I dati risiedono sul server **EBRAIN** (`/data/corbetta/Clinical_connectome`) e vengono copiati in locale a mano sotto `data/clinical_connectome/derivatives/<centro>/<coorte>/`. Una pipeline di retrieval (`retrieve_data.py`) lo faceva in automatico: è stata ritirata, resta in git.

Tutti i numeri di questa pagina sono **verificati sul disco e sui tsv**, non stimati.

Per rigenerarli: `notebooks/exploration/dataset_availability.ipynb` (esplorazione diretta del filesystem) o `assets/metadata/participants.csv` (vedi sotto).

---

## Vocabolario

Le parole che questa pagina e `notebooks/exploration/dataset_availability.ipynb` ([`exploration.md`](exploration.md)) usano sempre nello stesso senso:

- **Dataset**: una cartella a profondità 2 sotto `derivatives/`, cioè `<centro>/<coorte>` (centro clinico e sua coorte, per esempio `UNIPD/WashU`). Più coorti possono stare nello stesso centro (UNIPD ne ha quattro).
- **Tipologia di dato**: una sottocartella di primo livello di un dataset. I nomi su disco sono `manual_masks`, `bcbtoolkit` e `features`; è sempre il nome su disco che si usa in codice, notebook e path. `bcbtoolkit/` è la tipologia dell'output SDC (disconnettoma e lesione parcellati): "SDC" indica il concetto e compare in nomi come `has_sdc` o `build_sdc_matrix`, ma la tipologia non si chiama `sdc`.
- **Soggetto**: una cartella dentro una tipologia, con il nome dell'ID (`sub-...`). Un soggetto può avere una tipologia e non un'altra.
- **Pattern di file**: il percorso di un file relativo alla cartella del soggetto, con l'ID sostituito da `{subject_id}`. Serve a confrontare soggetti diversi: i pattern attesi per una tipologia sono l'unione di quelli di tutti i suoi soggetti.
- **Assenza strutturale**: un pattern che un dataset non ha mai, per nessun soggetto, mentre esiste in altri dataset. Descrive la forma del dataset, non un guasto.
- **Assenza sporadica**: un pattern che manca a un soggetto mentre gli altri soggetti dello stesso dataset lo hanno. È il segnale di un file perso o di un soggetto incompleto.
- **Popolazione reale e popolazione su disco**: possono differire (vedi *Copie locali ridotte*). Per `UNIPD/WashU/features/` il conteggio reale viene dal manifest `features_archive_subjects.tsv`, non dalle cartelle in chiaro.
- **WashU ST e HC**: WashU mescola pazienti (`ST`) e controlli sani (`HC`) nella stessa cartella. Per confrontare le tipologie si trattano come due insiemi distinti, perché i controlli sani non hanno mai `manual_masks` né `bcbtoolkit` (nessuna lesione da segnare); il gruppo di ogni soggetto viene da `disease_id` in `participants_WashU.tsv`.

---

## Le 8 coorti, in numeri

| Dataset | Registro clinico (`participants_*.tsv`) | `manual_masks` | `bcbtoolkit` | `features` (FC) | Griglia | Dettaglio |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **`UCL-UK/UCLStrokeData`** | 4119 (4119 ST) | **4119** | 4119 | — | 1.0 mm | reticolo 2 mm |
| **`UKLFR/stroke_UKLFR`** | 735 (735 ST) | 705 | 705 | — | 1.0 mm | reticolo 2 mm |
| **`UKE/WAKEUP_acute`** | 503 (503 ST) | 451 | 451 | — | 1.0 mm | **1 mm** |
| **`UNIPD/WashU`** | 319 (251 ST + 68 HC) | 195 | 195 | **225** (169 ST + 56 HC) | 1.0 mm | reticolo 2 mm |
| **`UNIPD/PSP`** | 237 (237 ST) | 168 | 168 | — | 1.0 mm | **2 mm interpolata** |
| **`UNIPD/PASPORT`** | 97 (97 ST) | 83 | 83 | — | 1.0 mm | **1 mm** |
| **`UNIPD/NEMESIS_T0`** | 104 (76 con maschera in `participants.csv`) | 76 | 76 | — | 1.0 mm | reticolo 2 mm |
| **`UKE/SFB936_ses01`** | 57 (56 con maschera in `participants.csv`) | 56 | 56 | — | 1.0 mm | reticolo 2 mm |

Tutte le maschere sono in spazio `MNI152NLin6Asym` su griglia **1.0 mm**, `182x218x182`: verificato sugli header NIfTI di tutte e 5853.

**L'orientamento degli header non è uniforme.** A parità di shape, le maschere hanno 3 header (censimento di tutte e 5853):

| Header | Offset x | Soggetti |
|---|---|---|
| LAS | `+90` | UCL-UK (4119), parte di UNIPD (251) |
| RAS | `-90` (un voxel di scarto dal template MNI) | UKLFR (705), parte di UNIPD (271), parte di UKE (56) |
| RAS | `-91` (identico al template MNI res-1) | UKE/WAKEUP (451) |

Lo stesso indice d'array è quindi un voxel fisico diverso (LAS e RAS sono specchiati sull'asse x). Chi legge una maschera deve confrontare **shape e affine** col riferimento e ricampionare (`resample_to_img`) se differiscono, mai assumere un orientamento o confrontare la sola shape.

### ⚠️ La griglia è 1 mm per tutti, il dettaglio no

`manual_masks/` non contiene segmentazioni disegnate a mano: è la lesione **già ricampionata da BCBToolKit** sulla propria griglia di lavoro a 1 mm, rinominata togliendo `res-1` dal nome (`..._res-1_label-lesion_mask.nii.gz`); `bcbtoolkit/` non contiene la maschera, solo il disconnettoma e le tabelle parcellate (vedi sotto); vedi anche `data/clinical_connectome/derivatives/README.md`, non versionato.

Un ricampionamento non crea dettaglio che non c'era. Per i dataset la cui segmentazione originale era a 2 mm, il risultato è un volume su griglia da 1 mm i cui voxel sono **costanti in blocchi 2x2x2 allineati** — ogni voxel originale replicato 8 volte. È questo che distingue le due colonne:

- **`reticolo 2 mm`** — 5150 soggetti (UCL-UK, UKLFR, WashU, NEMESIS_T0, SFB936; i 705 di UKLFR contano 704 perché `sub-STUKLFR0671` ha la maschera vuota e non è classificabile). Nessun dettaglio sotto i 2 mm.
- **`1 mm`** — 534 soggetti (PASPORT, WAKEUP). Segmentazione genuinamente a 1 mm, binaria (solo 0 e 1).
- **`2 mm interpolata`** — 168 soggetti (PSP). Maschera a 2 mm portata a 1 mm con interpolazione lineare: i valori non sono solo 0 e 1 ma multipli di 1/8, e valgono 0 o 1 solo i voxel che coincidono con i centri della griglia a 2 mm (la somma dei valori è esattamente 8 × il volume a 2 mm). Conseguenze per le colonne a 1 mm in [`docs/dev/metadata.md`](../dev/metadata.md).

Verificato su **tutti e 5853** i soggetti, non a campione: per ciascuno si cerca, tra gli 8 allineamenti possibili, se esiste un raggruppamento in blocchi 2x2x2 con zero blocchi misti. Il verdetto è **uniforme dentro ogni dataset** (nessun dataset misto) e l'allineamento pulito è sempre `(1,1,1)`. L'unica eccezione non classificabile è `sub-STUKLFR0671`, la cui maschera è vuota.

**Perché conta.** `assets/metadata/lesion_metadata.csv` misura ogni maschera su due griglie, 1 mm e 2 mm, per distinguere una maschera vuota da una lesione minuscola persa nel sottocampionamento ([`docs/guides/metadata.md`](metadata.md)). Per i dataset a reticolo 2 mm il conteggio sulla griglia di produzione a 2 mm **ricostruisce esattamente** la maschera originale, quindi nessuna lesione può sparire e `lesion_volume_voxels_1mm` è esattamente `8 x lesion_volume_voxels_2mm`: non aggiunge informazione. La perdita per sottocampionamento è possibile **solo** per i 534 soggetti a 1 mm genuino — e infatti 2 dei 4 soggetti con volume 0 sulla griglia di produzione stanno in WAKEUP, con lesioni reali di 8 e 3 voxel.

**UKLFR e WashU sono a 1mm**: `manual_masks/` viene dalla stessa sorgente usata per l'SDC (`Clinical_connectome_stroke/<dataset>/lesion/`, già a 1mm) e coincide esattamente con `bcbtoolkit/` per questi due dataset (0 discrepanze, vedi sotto). Il **dettaglio** attuale di entrambi è su reticolo 2 mm (vedi la nota sopra): la griglia a 1 mm viene da quel ricampionamento, non da una segmentazione a 1 mm.

### Perché le colonne non coincidono

Il registro clinico e i dati su disco rispondono a due domande diverse, e vanno tenute separate:

- **Registro clinico** = quante persone sono arruolate nella coorte e hanno una riga di dati clinici. 
- **`manual_masks`/`bcbtoolkit`/`features`** = per quanti di quei soggetti abbiamo effettivamente quel tipo di dato in locale.

Le differenze non sono errori, sono la realtà del dato. Due esempi concreti:

- **WashU**: 251 pazienti nel registro, 195 con maschera — **tutti e 195 hanno anche l'SDC** (corrispondenza esatta). Le FC coprono 225 soggetti (169 pazienti + 56 controlli sani) — un insieme che si sovrappone solo in parte a chi ha la maschera.
- **UKLFR**: 705 con maschera, 705 con SDC — **corrispondenza esatta**.

### Il conteggio unico: `assets/metadata/participants.csv`

Un soggetto per riga, con le colonne `has_lesion`/`has_sdc`/`has_features`, per i soli pazienti stroke presenti su disco — **5853 in totale**, uno per ciascun soggetto con maschera delle 8 coorti della tabella sopra. È la fonte da interrogare invece di ricontare a mano; generata da `src/pipeline/populate_metadata.py`, vedi `docs/dev/metadata.md`.

### `UKE/SFB936_ses01` e `UNIPD/NEMESIS_T0`

I due dataset (56 e 76 soggetti con maschera) hanno `manual_masks/` e `bcbtoolkit/` completi, a 1 mm, con lo stesso schema di file degli altri. Sono in `config/registry/metadata_sources.json`, in `assets/metadata/participants.csv` e nella tabella sopra come gli altri sei. Il loro tsv clinico sta in `data/clinical_connectome/metadata_tsv/`:

- **`participants_UKE_SFB.tsv`** ha lo schema normalizzato (57 righe).
- **`participants_NEMESIS_T0.tsv`** (104 righe) non è ancora normalizzato: vedi i campi comuni sotto.

---

## Naming dei soggetti

Ogni soggetto ha un ID `sub-<DISEASE><SITE>[HC]<NUM>`, ad esempio `sub-STUNIPD0001` (paziente) o `sub-STUNIPDHC0002` (controllo sano). `src/utils/subject_ids.py::group_of(subject_id)` lo trasforma nel gruppo `ST`, `HC`, `PD` o `GM`; è l'unico punto del progetto che interpreta un ID, riusato da `features/`, da `populate_metadata.py` e dagli script. Metadati e matrici ne derivano il gruppo (`disease_id`, `group_filter`) invece di copiarlo da una tabella (`docs/dev/metadata.md`).

`KNOWN_SITES = ("UNIPD", "UKLFR", "UCLUK", "UKE")` è una **lista chiusa**, non un pattern libero. Un pattern libero non distingue un sito il cui nome termina in "HC" da un sito seguito dal marcatore `HC`: un ipotetico `MONTREALHC` verrebbe letto come sito `MONTREAL` più controllo sano, e tutti i suoi pazienti risulterebbero controlli, senza alcun errore. Un sito non registrato fa invece sollevare `ValueError`: un sito nuovo va aggiunto a mano in `KNOWN_SITES`, mai dedotto.

---

## Tipi di dato

Ogni tipo vive in una sottocartella dedicata dentro `derivatives/<centro>/<coorte>/`, con un numero fisso di file per soggetto.

### 1. Maschere di lesione — `manual_masks/` (1 file per soggetto)

- **File**: `manual_masks/{subject_id}/anat/{subject_id}_space-MNI152NLin6Asym_label-lesion_mask.nii.gz`
- L'oggetto centrale del progetto: maschere disegnate a mano e normalizzate in spazio MNI. Presenti per tutti e 8 i dataset.

### 2. Dati clinici e anagrafici — `data/clinical_connectome/metadata_tsv/participants_*.tsv`

Un file per dataset.

**Campi comuni ai dataset con schema normalizzato (7 su 8)**: `participant_id`, `dataset`, `center_id`, `disease_id`, `age`, `sex`.

Un tsv il cui schema non ha ancora quei campi (manca almeno uno tra `center_id`, `dataset`, `disease_id`) non è ancora normalizzato: `participants_NEMESIS_T0.tsv` ha solo `participant_id`, `age`, `sex`, `group`, `participant_id_dmp`. `notebooks/exploration/metadata_raw.ipynb` lo salta dichiarando le colonne mancanti.

**`disease_id`**: `ST` (stroke) o `HC` (controlli sani). Solo WashU ha controlli sani (68 nel registro, 56 con FC).

**Copertura dei campi principali** (% sulle sole righe ST del tsv; la tabella copre i 6 dataset di più lunga data, non `UKE/SFB936_ses01` né `UNIPD/NEMESIS_T0`):

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
- **Nei tsv `lesion_side` ha il valore `both` solo in UKE** (30 righe, di cui 25 con maschera in `participants.csv`, tutte in `UKE/WAKEUP_acute`): è l'etichetta del tsv e non coincide con una maschera bilaterale; vedi [`metadata.md`](metadata.md), sezione sul valore `both`.

**Punteggi comportamentali — solo WashU** (% sui 251 ST): `ARAT_L`/`ARAT_R` 94%, `Boston_nam` 92%, `NIHSS` 74%, `9HPT_L`/`9HPT_R` 65%, `Clock` 65%, `Corsi` 34%. `GDS_15` esiste come colonna ma è vuota al 100% per questa coorte.

**UCL-UK, unica eccezione sul formato ID**: negli altri dataset `participant_id` è già nel formato canonico `sub-*`. UCL-UK ha il formato legacy del sito (`ST_UCL-UK_0001`), riconciliato in `participants.csv` (`subject_id` canonico + `original_id` col valore grezzo).

### 3. Connettività funzionale — `features/` (16 file per soggetto)

- **Disponibile solo per WashU** (225 soggetti: 169 ST + 56 HC). I 16 file per soggetto sono le 12 matrici FC (una per combinazione di atlante `Yan<n>TianS<n>Buckner7N`) più i sidecar di motion/outliers.

### 4. Output BCBToolKit: disconnettoma e lesione parcellati — `bcbtoolkit/` (34 file per soggetto)

- Output Stage1+2 di BCBToolKit: la cartella raccoglie sia le misure di disconnessione sia quelle sulla lesione, per questo si chiama come lo strumento che le produce.
- I 34 file per soggetto: 
  - il volume di disconnessione voxel-wise (`res-1_desc-disconnectome.nii.gz`),
  - le parcellazioni per 15 atlanti (`LF-disconnectome_atlas-*.csv`),
  - gli equivalenti per la lesione ricampionata (`LF-lesion_atlas-*.csv`, 16 atlanti — include `yeh_hcp1065_streamline`),
  - i 2 `mapstats.tsv`.
- **Il reticolo di voxel del disconnettoma non è lo stesso per tutti i dataset.** Tutte le mappe sono 182×218×182 a 1 mm, ma gli header sono 3: LAS con offset x `+90` (UCL-UK, PASPORT, PSP), RAS con `-90`, cioè traslato di 1 voxel (UKE-SFB936, UKLFR, NEMESIS_T0, WashU), RAS con `-91`, identico al template MNI (UKE-WAKEUP). Gli stessi voxel fisici stanno quindi a indici diversi: chi legge una mappa deve portarla sulla griglia di riferimento col **suo** header (`resample_to_img`), mai assumere un flip o un'identità fissi. Dettagli in [`docs/dev/metadata.md`](../dev/metadata.md).
- **Disponibile per tutti e 8 i dataset**, solo pazienti stroke.
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

## Ingombro su disco (locale)

`data/clinical_connectome/derivatives/` pesa **11,9 GB** in totale. Le dimensioni sono quelle reali dei file (somma dei byte, 1 GB = 10⁹ byte), non lo spazio allocato da `du`, che per i file piccoli è più alto (blocchi da 4 KB):

| Tipo | Peso |
| :--- | ---: |
| `bcbtoolkit/` (8 dataset, 5853 soggetti) | 8,45 GB |
| `features_archive.tar.gz` (i 215 soggetti WashU compressi) | 2,22 GB |
| `manual_masks/` (8 dataset, 5853 soggetti) | 0,95 GB |
| `features/` (solo WashU, i 10 soggetti in chiaro) | 0,23 GB |

Dentro l'SDC, il peso è dominato dalla mappa voxel-wise: `res-1_desc-disconnectome.nii.gz` 5,72 GB (68% di `bcbtoolkit/`), i 15 CSV `LF-disconnectome` 2,57 GB (30%), i 16 CSV `LF-lesion` 0,15 GB (2%), i `mapstats.tsv` 3 MB (0,03%). Non c'è una mappa di lesione per soggetto. I soli CSV parcellati (2,7 GB) bastano per una matrice tipo `build_sdc_matrix.py`.
