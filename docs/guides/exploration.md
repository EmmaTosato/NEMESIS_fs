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
| `sdc_analysis` | l'output SDC è valido e com'è fatta la matrice di disconnessione? | output SDC (`bcbtoolkit/`); costruisce la matrice in memoria | nulla |
| `fc_analysis` | quanto danneggia la lesione la FC e dove va la soglia di mascheramento? | FC pre-masking e output di `mask_fc.py`/`build_fc_matrix.py` | nulla |

**`lesion_analysis` e `excluded_subjects.csv`.** L'ultima cella è quella che *decide*, ma non scrive: per gli ID che le si danno (tre motivi: `empty_mask`, `lesion_too_small`, `out_of_brain_fraction_too_high`, scope `all`) stampa i blocchi da incollare in `exclusions` di `config/pipelines/build_excluded_subjects.json`. La pipeline `build_excluded_subjects` genera poi il csv. Tutto sopra è esplorazione. Formato, vocabolario dei motivi e validazioni in [`metadata.md`](metadata.md).

---

## `notebooks/pipeline_building/`

| Notebook | Prototipo di |
|---|---|
| `lesion_matrix_build` | `src/pipeline/build_lesion_matrix.py`: maschere → griglia comune → matrice soggetti × voxel, sanity check, riduzione ai voxel non costanti, frequenza voxel-wise. Non scrive l'artefatto: legge quello già prodotto dalla cache |
| `fc_lesion_masking` | `src/pipeline/mask_fc.py`/`build_fc_matrix.py`: mascheramento della FC in funzione della lesione (scrive CSV mascherati e di matrice) |
| `dim_reduction` | tuning della riduzione dimensionale |
| `thiebaut_2020_replication` | replica della PCA varimax di Thiebaut de Schotten et al. 2020 sul disconnettoma voxelwise `s2.4-vol`: quante componenti per il 50/80/90% della varianza, e quanto ogni componente dipende dal volume della lesione, e le mappe delle componenti nel cervello con la loro riproducibilità tra due metà dei soggetti (le componenti da disegnare si scelgono a mano, `COMPONENTS_TO_PLOT`). Legge `matrix.npy`/`metadata.csv` e `participants.csv`; scrive solo una cache in `results/pipeline_building/thiebaut_2020_replication/`. Il calcolo è in `src/analysis/covariance_pca.py` ([`covariance_pca.md`](../dev/covariance_pca.md)) |

---

## `notebooks/post-results_analysis/`

Leggono run già **prodotte**: di clustering (due notebook di analisi, una run o più run, più l'esplorazione di un tuning) e di PCA (`pca_evaluation`). Per il clustering un criterio separa le analisi: se usano dati *interni* al clustering o dati *esterni* a esso.

- **Empirica**: usa solo le etichette e lo spazio su cui la run è stata costruita (embedding o matrice). Risponde a "com'è fatta e quanto è affidabile questa partizione, quanto si accorda con un'altra".
- **Interpretativa**: porta variabili o immagini che il clustering non ha visto (cliniche, demografiche, mappe anatomiche). Risponde a "cosa rappresentano questi cluster". Vive nell'app Dash (mappe, soggetti rappresentativi, composizione dei cluster); l'unica eccezione nei notebook è la sezione 4 di `clustering_evaluation`, che descrive i cluster con le variabili cliniche e non fa nessun test.

| Notebook | Scope | Domanda | Legge | Scrive |
|---|---|---|---|---|
| `clustering_evaluation` | empirica, **una** run | quanto è buona questa run? (metriche geometriche e del modello, confidenza di appartenenza) e come sono distribuite le variabili cliniche nei suoi cluster (sezione 4, solo descrittiva, nessun test) | la run (`matrix.npy`, `metadata.csv`, `config.md`), `participants.csv` per la sezione 4 | nulla |
| `clustering_comparison` | empirica, **più** run | in cosa differiscono queste run? (accordo tra partizioni, corrispondenza dei cluster, distanze tra cluster nell'embedding) | le run scelte | nulla |
| `clustering_tuning_explorer` | esplorazione di uno sweep di tuning | come variano le metriche al variare degli iperparametri? | l'output di un tuning | nulla |
| `pca_evaluation` | valutazione di **una** PCA, di produzione o di tuning (una combinazione) | quante componenti tenere (varianza cumulata), quanta varianza spiega ogni componente ruotata, quanto dipende ciascuna dal volume e dal lato della lesione, dove sta nel cervello (mappe *t* e riproducibilità tra metà), come separa i soggetti (embedding) | la run (`matrix.npy`/`embeddings.npz`, `eigenvalues.npy`/`.npz`, `metadata.csv`, `config.md`), la matrice su cui la PCA è stata calcolata (sezioni 4 e 6), `participants.csv` | solo la cache delle mappe in `results/cache/component_maps`, la stessa dell'app |

Guida di evaluation e comparison, e dove vive ogni analisi: [`evaluation.md`](evaluation.md).

---

## Regole di scrittura dei notebook

- **Prima cella**: titolo, domanda, cosa legge, cosa scrive, e cosa *non* fa (rimandando al notebook che lo fa).
- **Titoli**: `#` solo per il titolo, `##` per le sezioni, `###` e oltre per le sottosezioni.
- **Niente duplicati tra notebook**: una stessa analisi (per esempio la distribuzione del volume) vive in un solo notebook. Se ne serve il risultato altrove, si legge il file che la contiene.
- Un notebook che diventa codice di produzione resta come prototipo in `pipeline_building/`, con il rimando alla pipeline nella prima cella.
