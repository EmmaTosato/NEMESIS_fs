# Metadati dei soggetti — come si usano

Tutto ciò che sappiamo dei soggetti sta in **un file solo**: `assets/metadata/participants.csv`, versionato in git, una riga per soggetto.

Lo scrivono due script, che rispondono a due domande diverse e non si sovrascrivono mai a vicenda:

| Script | Domanda | Colonne che scrive |
| :--- | :--- | :--- |
| `src/pipeline/populate_metadata.py` | chi esiste | `subject_id`, `original_id`, `dataset`, `disease_id`, `has_lesion`, `has_sdc`, `has_features` |
| `src/pipeline/enrich_metadata.py` | cosa sappiamo di lui | `age`, `sex`, `education`, `lesion_side`, `lesion_side_source`, `NIHSS`, `clinical_date`, `lesion_volume_voxels_2mm` |

- **Dettagli architetturali/perché è fatto così**: [`docs/dev/metadata.md`](../dev/metadata.md)
- **Quali campi esistono in quale dataset**: [`docs/guides/datasets.md`](datasets.md)

`assets/metadata/` contiene altri due file, **separati** dal registro:

| File | Cosa c'è | Chi lo scrive |
| :--- | :--- | :--- |
| `lesion_metadata.csv` | tutto ciò che si misura su una maschera di lesione: volume, frazione fuori dal brain, indice di lateralità e lato, **per ogni griglia** | `src/pipeline/compute_lesion_metadata.py` |
| `excluded_subjects.csv` | quali soggetti tenere fuori dalle matrici di produzione, con il motivo | **tu, a mano**, dal notebook `notebooks/exploration/lesion_quality.ipynb` |

---

## Come si lancia, in ordine

Tre passaggi, in quest'ordine: chi esiste, cosa misurano le maschere, e infine il join che riempie il registro.

```bash
conda activate nemesis
cd "$PROJECT_ROOT"

PYTHONPATH="$PROJECT_ROOT" python -m src.pipeline.populate_metadata --config config/pipelines/populate_metadata.json
python -m src.pipeline.compute_lesion_metadata --config config/pipelines/compute_lesion_metadata.json
python -m src.pipeline.enrich_metadata --config config/pipelines/enrich_metadata.json
```

Entrambe le pipeline accettano `--dry-run`: eseguono ogni controllo e scrivono il report, senza toccare nulla. **Usalo la prima volta dopo aver cambiato un config.**

Su cluster: `sbatch jobs/run_compute_lesion_metadata.sh`, `sbatch jobs/run_enrich_metadata.sh` (le cartelle `logs/slurm/<pipeline>/` devono già esistere).

---

## `compute_lesion_metadata.py` — le misure sulle maschere

Produce `assets/metadata/lesion_metadata.csv`: una riga per **ogni** soggetto con una maschera, nessuna soglia applicata. È volutamente agnostica del clinico — non apre nessun `participants.tsv` e non sa cosa sia un NIHSS.

### Cosa contiene il csv

`subject_id`, `dataset`, e per **ogni griglia dichiarata** quattro colonne col nome della griglia come suffisso:

| Colonna | Cosa è | Quando |
| :--- | :--- | :--- |
| `lesion_volume_voxels_<g>` | voxel di lesione | dopo l'azzeramento fuori dal brain |
| `out_of_brain_fraction_<g>` | quota di voxel di lesione fuori dalla maschera cerebrale | **sulla maschera grezza**, prima dell'azzeramento |
| `laterality_index_<g>` | `(sinistra − destra) / (sinistra + destra)` | dopo l'azzeramento |
| `lesion_side_<g>` | `left`/`right`/`both` | dopo l'azzeramento |

La frazione è misurata **prima** della correzione di proposito: la correzione la porterebbe a 0 per costruzione, e quella colonna serve proprio a decidere chi escludere. Volume e lato sono invece misurati **dopo**: un voxel fuori dal cervello non è lesione, quindi non va contato né deve poter decidere il lato.

Celle vuote o `NaN` non sono buchi ma casi di dominio espliciti: una maschera senza voxel non ha una frazione (0.0 la metterebbe tra i soggetti più puliti della distribuzione), e una lesione confinata al piano mediano non ha un lato attribuibile, perché quel piano non appartiene a nessuno dei due emisferi.

### Parametri di `config/pipelines/compute_lesion_metadata.json`

| Parametro | Descrizione |
| :--- | :--- |
| **`data_root`, `datasets`, `group_filter`, `lesion_glob`** | dove sono le maschere e quali soggetti considerare. Un dataset senza cartelle soggetto ferma la run. |
| **`binarize_threshold`, `resample_interpolation`** | come ogni maschera diventa un array binario di voxel. |
| **`grids`** | oggetto `{nome: {reference_template_path, brain_mask_path}}`. Il **nome diventa il suffisso** delle quattro colonne, quindi deve essere alfanumerico. Entrambi i path sono obbligatori per ogni griglia. Aggiungere una terza griglia è una voce qui, non una modifica al codice. |
| **`correct_out_of_brain`** | azzera i voxel di lesione fuori dalla maschera cerebrale prima di contare. `true` in produzione. |
| **`side_threshold`** | soglia di bilateralità: sotto, il lato è `both`. |
| **`output_path`, `overwrite`, `run_notes`** | dove scrivere, se sovrascrivere un csv esistente, nota libera per il report. |

**Due griglie in produzione, `1mm` e `2mm`, e non è ridondanza.** Le maschere manuali sono tutte a 1 mm, il template di produzione è a 2 mm con ricampionamento `nearest`, che tiene un voxel su 8: a 1 mm il conteggio è nativo ed esatto, a 2 mm è un sottocampionamento in cui una lesione minuscola può ridursi o sparire. Confrontare i due volumi è l'unico modo per dire se una maschera a 0 voxel a 2 mm sia vuota nel file originale o abbia perso la lesione nel ricampionamento.

**Attenzione: la colonna a 1 mm è informativa solo per 3 dataset su 8.** `manual_masks/` contiene la lesione già ricampionata da BCBToolKit su griglia 1 mm, e per i dataset la cui segmentazione originale era a 2 mm quel ricampionamento non aggiunge dettaglio: i voxel sono costanti in blocchi 2×2×2, quindi `lesion_volume_voxels_1mm` è esattamente `8 × lesion_volume_voxels_2mm`. Vale per **5150 soggetti su 5853** (UCL-UK, UKLFR, WashU, NEMESIS_T0, SFB936). Le due colonne differiscono davvero solo per PASPORT, PSP e WAKEUP (702 soggetti), ed è lì che una lesione può sparire nel sottocampionamento. Tabella per dataset e verifica in [`docs/guides/datasets.md`](datasets.md).

**`side_threshold` è 0.20, calibrato e non inventato**: riproduce il 97.4% di 1445 soggetti con etichetta clinica vera sulla griglia a 2 mm (metodo, letteratura e limiti in [`knowledge/neuroimaging/lesion_laterality.md`](../../knowledge/neuroimaging/lesion_laterality.md)). La stessa soglia è applicata anche a 1 mm, dove **non è ancora verificata**: `lesion_side_1mm` è indicativa finché non si esegue `python -m src.pipeline.calibrate_lesion_side_threshold --grid 1mm --datasets ...`.

**Costo**: una lettura da disco per soggetto e un ricampionamento per griglia. Il calcolo è in streaming, un soggetto per volta, quindi la memoria non dipende da quanti soggetti ci sono. `overwrite: false` lascia intatto un csv esistente e la run esce subito, così rilanciarla per sbaglio non ripaga il costo.

Accanto al csv viene scritto `lesion_metadata.config.json`, il config esatto della run che l'ha prodotto: un csv di cui non si sappia su quali griglie e con quale correzione è stato calcolato non è interpretabile.

---

## `excluded_subjects.csv` — chi resta fuori dalle matrici

Lo scrivi **a mano**, dopo aver guardato le distribuzioni di `lesion_metadata.csv` dal notebook. Non lo genera nessuna pipeline: i dati non hanno un salto naturale su cui mettere una soglia, e quale soggetto limite valga la pena di scartare è un giudizio, non un confronto numerico.

```csv
subject_id,dataset,reason,scope,value
sub-STUKE0146,UKE/WAKEUP_acute,empty_mask,all,0
sub-STUCLUK2160,UCL-UK/UCLStrokeData,all_zero_features,sdc-streamline,0
```

- **`reason`** ha un vocabolario chiuso: `empty_mask`, `lesion_too_small`, `out_of_brain_fraction_too_high`, `all_zero_features` (la riga di feature del soggetto è tutta zero nella rappresentazione indicata da `scope`: sotto qualunque distanza risulta indistinguibile o massimamente lontana dagli altri). Un motivo non in elenco fa fallire la run.
- **`scope`** dice a quale matrice si applica la riga, con vocabolario chiuso: `all`, `lesion`, `sdc-parcellated`, `sdc-voxelwise`, `sdc-streamline`. Serve perché un soggetto può essere inutilizzabile in uno spazio di feature e perfettamente valido negli altri: uno zero nel CSV streamline può essere una misura vera (una lesione che non interseca nessuna streamline di nessun tratto), non un dato rotto, e non deve far sparire il soggetto dalla matrice lesionale né da quella voxelwise. `all` dichiara esplicitamente "ovunque"; un soggetto con una riga `all` **non può** averne anche una più stretta (le due righe si contraddirebbero).
- **`value`** è la metrica che ha motivato l'esclusione. Serve a rivedere la decisione a mesi di distanza: "sub-X escluso" non si può giudicare, "sub-X escluso a 2 voxel" sì.
- **Ogni riga è validata** contro il registro: ID inesistente, coppia (ID, scope) duplicata, `dataset` in disaccordo col registro, `scope` o `reason` non registrati, `value` non numerico fanno fallire la run. La validazione copre **tutto il file**, non solo le righe della matrice che sta girando: un refuso in una riga destinata a un'altra matrice fa fallire anche questa, invece di restare dormiente fino a quando qualcuno costruisce quell'altra.

Il file è **l'unica fonte** letta sia da `build_lesion_matrix.py` sia da `build_sdc_matrix.py` (campo `excluded_subjects_path` nei due config). Ogni matrice legge le righe `all` più quelle del proprio scope: `build_lesion_matrix.py` quelle `lesion`, `build_sdc_matrix.py` quelle `sdc-<representation>`. Le righe `all` sono quindi ciò che garantisce la stessa coorte tra lesione e SDC; una riga più stretta restringe volutamente il confronto a un solo spazio di feature, e `config.md` di ogni matrice registra lo scope usato (`excluded_subjects_scope`).

**Un file assente è un errore, non "nessuna esclusione"**: le due cose sono indistinguibili, e costruire una matrice con tutti i soggetti limite dentro è ciò che questa lista esiste per evitare. Per dire "nessuna esclusione" si tiene il file con la sola intestazione.

I soggetti esclusi **restano nel registro** con `has_lesion` e `has_sdc` intatti, e restano nel csv delle misure: l'esclusione riguarda solo cosa entra in analisi.

---

## Parametri di `config/pipelines/enrich_metadata.json`

| Parametro | Descrizione |
| :--- | :--- |
| **`metadata_sources`** | Path del registry `config/registry/metadata_sources.json`, che mappa ogni dataset al suo tsv grezzo. Condiviso con `populate_metadata.py`. |
| **`participants_path`** | Il file da arricchire (`assets/metadata/participants.csv`). Deve esistere già: lo crea `populate_metadata.py`. |
| **`datasets`** | Lista di dataset da processare, oppure `null` per tutti quelli presenti nel file. Un dataset fuori scope **non viene toccato**: le sue celle restano quelle che erano. |
| **`variables`** | Quali variabili leggere dai tsv clinici. Ammesse: `age`, `sex`, `education`, `lesion_side`, `NIHSS`, `clinical_date`. Un nome non in elenco fa fallire il config subito. |
| **`lesion_metadata`** | Oggetto opzionale (`null` salta del tutto le colonne derivate dalle maschere) — il join su `lesion_metadata.csv`. Vedi sotto. |
| **`fill`** | `true`: scrive **solo** le celle vuote delle variabili cliniche, ogni valore già presente resta intatto. `false`: le ricalcola tutte. Non ha effetto sulle colonne copiate da `lesion_metadata.csv`, che vengono sempre sovrascritte. |
| **`run_notes`** | Nota libera, finisce nel report. |

### `lesion_metadata`: il join sul csv delle misure

```json
"lesion_metadata": {
  "path": "assets/metadata/lesion_metadata.csv",
  "copy_columns": ["lesion_volume_voxels_2mm"],
  "lesion_side_from": "lesion_side_2mm"
}
```

`enrich_metadata` **non apre nessuna maschera**: copia numeri già calcolati. Ogni scelta su *come* una maschera è misurata (quali griglie, se azzerare i voxel fuori dal brain, quale soglia per il lato) vive nel config di `compute_lesion_metadata`, non qui.

- **`copy_columns`**: colonne copiate **con lo stesso nome**, per tutti i soggetti in scope, sovrascrivendo. Ogni nome deve esistere nel csv, e non può essere una colonna di `populate_metadata.py`. Una colonna non elencata non viene portata nel registro e resta disponibile nel csv per il notebook: oggi il volume a 1 mm, le due frazioni e i due indici di lateralità stanno solo lì.
- **`lesion_side_from`**: quale colonna del csv riempie `lesion_side`. Ha una regola diversa da `copy_columns`, per questo è una chiave a sé: scrive **solo dove la risoluzione clinica ha lasciato la cella vuota**, e scrive anche `lesion_side_source = "geometric"`. Un valore clinico non viene mai sovrascritto. `null` disattiva il riempimento e lascia `lesion_side` solo clinico. Richiede `lesion_side` in `variables`.

Nel registro la colonna resta **`lesion_side`, senza suffisso di griglia**, perché per i soggetti con etichetta clinica quel valore non viene da nessuna griglia: un suffisso sarebbe falso per la maggioranza delle celle. `lesion_side_from` dice da quale griglia viene la parte geometrica, `lesion_side_source` dice quale delle due provenienze ha vinto per ogni soggetto.

### Il join è stretto nei due sensi

Tre disaccordi fermano la run, nessuno viene ignorato:

| Situazione | Cosa significa |
| :--- | :--- |
| soggetto in scope con `has_lesion` vero e senza riga nel csv | il csv è vecchio: rilancia `compute_lesion_metadata` |
| riga nel csv per un soggetto che il registro non conosce | i due file non sono d'accordo su chi esiste |
| riga nel csv per un soggetto con `has_lesion` falso | i due file non sono d'accordo su chi ha una maschera |

Il primo controllo è limitato ai `datasets` della run (arricchire un sottoinsieme della coorte è legittimo); gli altri due sono globali, perché una riga che non corrisponde a nessuno è sbagliata comunque.

### Le colonne derivate dalle maschere non si correggono a mano

`fill: true` protegge una cella **clinica** corretta a mano, non una copiata dal csv: quelle vengono sovrascritte a ogni run. Se un volume o un lato è inaffidabile, la causa è nella maschera, non nel registro — si sistema la maschera e si ricalcola, oppure il soggetto va in `excluded_subjects.csv`.

---

## Cosa aspettarsi nell'output

**Valori mancanti = cella vuota.** Sempre, per ogni variabile. Il file è un registro, non un input di plotting: chi ha bisogno di una sentinella (`"unknown"` in una legenda) se la applica in lettura.

**Due tipi di buco, entrambi normali e riportati, nessuno dei due è un errore:**

1. *Il dataset non ha proprio quella colonna* — es. UCL-UK non registra NIHSS. Tutti i suoi soggetti restano vuoti, con un `WARNING` nel log.
2. *Il singolo soggetto ha la cella vuota o `n/a`* in un dataset che invece la colonna ce l'ha.

**Un errore vero, invece**: un soggetto presente in `participants.csv` ma assente dal tsv grezzo del suo dataset. Vuol dire che i due file non sono d'accordo su chi esiste, cosa che l'inner join di `populate_metadata.py` dovrebbe rendere impossibile. La run si ferma.

### Sostituzioni di colonna

Se una variabile non esiste col nome canonico in un dataset, viene letta da un'altra colonna **solo** se la sostituzione è registrata a mano nel codice (`VARIABLE_SOURCE_OVERRIDES`), mai dedotta da un nome somigliante. Oggi ce n'è una: PASPORT non ha un NIHSS baseline, quindi `NIHSS` viene da `NIHSS_at_presentation`. È un'assunzione di equivalenza clinica, quindi compare a `WARNING` nel log e in una sezione dedicata del report.

---

## Chi legge questi file

Non serve copiare i valori altrove: i consumatori leggono il registro direttamente.

| Consumatore | Cosa ci prende |
| :--- | :--- |
| `build_sdc_matrix.py` | `has_lesion`, per decidere quali soggetti ammettere |
| `build_lesion_matrix.py` / `build_sdc_matrix.py` | `excluded_subjects.csv`, per escludere gli stessi soggetti |
| `dim_reduction.py` / `clustering.py` | `lesion_side`/`NIHSS` per i color mode `side`/`nihss`, risolti al momento del plot |
| `src/analysis/cluster_description.py` (pannello di `embedding_app.py`) | età, sesso, istruzione, NIHSS, `lesion_volume_voxels_2mm` per la composizione dei cluster |
| `notebooks/exploration/lesion_quality.ipynb` | `lesion_metadata.csv`, per decidere le esclusioni |

Conseguenza pratica: se aggiungi `NIHSS` al registro oggi, **anche le run vecchie** si possono colorare per NIHSS, senza rigenerarle.

---

## Attenzione: `has_*` descrive il disco, e il disco può essere potato

`populate_metadata.py` scandisce le cartelle per riempire `has_lesion`/`has_sdc`/`has_features`, e una scansione non vede dentro un `.tar.gz`. Le cartelle archiviate localmente per spazio (oggi `UNIPD/WashU/features/` e `data/derived/features/masked_fc/`) vanno quindi decompresse prima, oppure i `has_*` interessati vanno corretti a mano. Vedi [`docs/guides/datasets.md`](datasets.md).
