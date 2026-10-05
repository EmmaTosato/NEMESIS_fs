# Guida ai notebook

I notebook sono strumenti di **ispezione umana**, non pipeline CLI: si eseguono solo in locale (`conda activate nemesis`, poi `jupyter lab <notebook>`) e non hanno un job `sbatch`. Ogni notebook ha **un oggetto sotto ispezione e una domanda a cui risponde**, dichiarati nella sua prima cella.

---

## Come sono divisi

| Cartella | Cosa contiene |
|---|---|
| `notebooks/exploration/` | guardare un dato esistente: disponibilità, qualità, distribuzioni. Nessun artefatto di produzione, salvo l'eccezione indicata sotto |
| `notebooks/pipeline_building/` | prototipi passo-passo di una pipeline: vedere ogni passo prima che diventi codice in `src/`. La versione di produzione è sempre in `src/pipeline/` |
| `notebooks/post-results_analysis/` | leggere i risultati di run già prodotte (clustering) |

Ordine logico dei dati: **input grezzi** (cosa esiste su disco, cosa dicono i TSV) → **per modalità** (lesione, SDC, FC) → **risultati** (clustering).

---

## `notebooks/exploration/`

| Notebook | Domanda | Legge | Scrive |
|---|---|---|---|
| `dataset_availability` | quali dati esistono su disco, per dataset, tipologia e soggetto? | `data/clinical_connectome/derivatives` (filesystem) | solo la cache `data/clinical_connectome/file_types_cache.json` |
| `metadata_raw` | cosa dicono i metadati clinici/demografici come arrivano dai dataset, prima della nostra normalizzazione? | i TSV `data/clinical_connectome/metadata_tsv/participants_*.tsv`, non `participants.csv` | nulla |
| `lesion_analysis` | com'è fatta ogni maschera di lesione (volume, lateralità, fuori dal brain) e chi va escluso dalle matrici? | `assets/metadata/lesion_metadata.csv`, `participants.csv`; il file di una maschera a scelta da `derivatives/` (sezione "Lesion mask file exploring") | nulla (l'ultima cella stampa i blocchi da incollare nel config di `build_excluded_subjects`) |
| `sdc_analysis` | l'output SDC è valido e com'è fatta la matrice di disconnessione? | output SDC (`sdc/`); costruisce la matrice in memoria | nulla |
| `fc_analysis` | quanto danneggia la lesione la FC e dove va la soglia di mascheramento? | FC pre-masking e output di `mask_fc.py`/`build_fc_matrix.py` | nulla |

**`lesion_analysis` e `excluded_subjects.csv`.** L'ultima cella è quella che *decide*, ma non scrive: per gli ID che le si danno (tre motivi: `empty_mask`, `lesion_too_small`, `out_of_brain_fraction_too_high`, scope `all`) stampa i blocchi da incollare in `exclusions` di `config/pipelines/build_excluded_subjects.json`. La pipeline `build_excluded_subjects` genera poi il csv. Tutto sopra è esplorazione. Formato, vocabolario dei motivi e validazioni in [`metadata.md`](metadata.md).

---

## `notebooks/pipeline_building/`

| Notebook | Prototipo di |
|---|---|
| `lesion_matrix_build` | `src/pipeline/build_lesion_matrix.py`: maschere → griglia comune → matrice soggetti × voxel, sanity check, riduzione ai voxel non costanti, frequenza voxel-wise. Non scrive l'artefatto: legge quello già prodotto dalla cache |
| `fc_lesion_masking` | `src/pipeline/mask_fc.py`/`build_fc_matrix.py`: mascheramento della FC in funzione della lesione (scrive CSV mascherati e di matrice) |
| `dim_reduction` | tuning della riduzione dimensionale |

---

## `notebooks/post-results_analysis/`

| Notebook | Domanda |
|---|---|
| `clustering_evaluation` | quale tra più run di clustering già prodotte descrive meglio i dati? Guida dedicata: [`evaluation.md`](evaluation.md) |
| `clustering_tuning_explorer` | esplorazione dei risultati di uno sweep di tuning del clustering |

---

## Regole di scrittura dei notebook

- **Prima cella**: titolo, domanda, cosa legge, cosa scrive, e cosa *non* fa (rimandando al notebook che lo fa).
- **Titoli**: `#` solo per il titolo, `##` per le sezioni, `###` e oltre per le sottosezioni.
- **Niente duplicati tra notebook**: una stessa analisi (per esempio la distribuzione del volume) vive in un solo notebook. Se ne serve il risultato altrove, si legge il file che la contiene.
- Un notebook che diventa codice di produzione resta come prototipo in `pipeline_building/`, con il rimando alla pipeline nella prima cella.
