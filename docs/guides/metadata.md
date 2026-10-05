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
| `excluded_subjects.csv` | quali soggetti tenere fuori dalle matrici di produzione, con il motivo | `src/pipeline/build_excluded_subjects.py`, dalla lista che scrivi **tu** nel config `build_excluded_subjects.json` |

---

## Come si lancia, in ordine

Tre passaggi, in quest'ordine: chi esiste, cosa misurano le maschere, e infine il join che riempie il registro. Un quarto, indipendente, genera la lista delle esclusioni (`excluded_subjects.csv`) quando cambia.

```bash
conda activate nemesis
cd "$PROJECT_ROOT"

PYTHONPATH="$PROJECT_ROOT" python -m src.pipeline.populate_metadata --config config/pipelines/populate_metadata.json
python -m src.pipeline.compute_lesion_metadata --config config/pipelines/compute_lesion_metadata.json
python -m src.pipeline.enrich_metadata --config config/pipelines/enrich_metadata.json

# quando cambia la lista dei soggetti esclusi:
python -m src.pipeline.build_excluded_subjects --config config/pipelines/build_excluded_subjects.json
```

Entrambe le pipeline accettano `--dry-run`: eseguono ogni controllo e scrivono il report, senza toccare nulla. **Usalo la prima volta dopo aver cambiato un config.**

Su cluster: `sbatch jobs/run_compute_lesion_metadata.sh`, `sbatch jobs/run_enrich_metadata.sh`, `sbatch jobs/run_build_excluded_subjects.sh` (le cartelle `logs/slurm/<pipeline>/` devono già esistere).

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

**Due griglie in produzione, `1mm` e `2mm`, e non è ridondanza.** Le maschere manuali sono tutte a 1 mm, il template di produzione è a 2 mm con ricampionamento `nearest`, che tiene un voxel su 8: a 1 mm il conteggio è nativo ed esatto, a 2 mm è un sottocampionamento in cui una lesione minuscola può ridursi o sparire. Confrontare i due volumi è l'unico modo per dire se una maschera a 0 voxel a 2 mm sia vuota nel file originale o abbia perso la lesione nel ricampionamento. Come il codice ricampiona, passo per passo: [`docs/dev/lesion_matrix.md`](../dev/lesion_matrix.md), sezione *Resampling onto the common grid*.

**Attenzione: la colonna a 1 mm è informativa solo per 2 dataset su 8 (PASPORT e WAKEUP).** `manual_masks/` contiene la lesione già ricampionata da BCBToolKit su griglia 1 mm, e per i dataset la cui segmentazione originale era a 2 mm quel ricampionamento non aggiunge dettaglio: i voxel sono costanti in blocchi 2×2×2, quindi il conteggio *grezzo* a 1 mm è esattamente 8 × quello a 2 mm. Vale per **5150 soggetti su 5853** (UCL-UK, UKLFR, WashU, NEMESIS_T0, SFB936). Le colonne del csv, però, sono contate dopo l'azzeramento dei voxel fuori dal cervello, con una maschera cerebrale per griglia: `lesion_volume_voxels_1mm = 8 × lesion_volume_voxels_2mm` vale esattamente solo per chi non ha voxel fuori dal brain (3501 soggetti su 3501 in questi 5 dataset), mentre per gli altri 1608 le due colonne differiscono di pochi voxel per un bordo diverso, non per perdita di dettaglio (differenza relativa mediana 0,2%, 95° percentile 2,3%, massima 12,8%). Una lesione può sparire nel sottocampionamento solo per PASPORT e WAKEUP (534 soggetti). **PSP fa caso a sé**: la sua maschera è a 2 mm interpolata a 1 mm, con valori frazionari. La colonna a 2 mm è esatta; quella a 1 mm è sottostimata (mediana −17%, fino a −66%) perché la binarizzazione `> 0,5` scarta i voxel di bordo che valgono 0,5. Le colonne a 1 mm di PSP (volume, frazione fuori dal brain, indice e lato) non sono affidabili. Tabella per dataset e verifica in [`docs/guides/datasets.md`](datasets.md).

**`side_threshold` è 0.20, calibrato e non inventato**: riproduce il 97.4% di 1445 soggetti con etichetta clinica vera sulla griglia a 2 mm (metodo, letteratura e limiti in [`knowledge/neuroimaging/lesion_laterality.md`](../../knowledge/neuroimaging/lesion_laterality.md)). La stessa soglia è applicata anche a 1 mm, dove **non è ancora verificata**: `lesion_side_1mm` è indicativa finché non si esegue `python -m src.pipeline.calibrate_lesion_side_threshold --grid 1mm --datasets ...`.

**Costo**: una lettura da disco per soggetto e un ricampionamento per griglia. Il calcolo è in streaming, un soggetto per volta, quindi la memoria non dipende da quanti soggetti ci sono. `overwrite: false` lascia intatto un csv esistente e la run esce subito, così rilanciarla per sbaglio non ripaga il costo.

Accanto al csv viene scritto `lesion_metadata.config.json`, il config esatto della run che l'ha prodotto: un csv di cui non si sappia su quali griglie e con quale correzione è stato calcolato non è interpretabile.

---

## `excluded_subjects.csv` — chi resta fuori dalle matrici

La lista è una **decisione**, e vive nel config `config/pipelines/build_excluded_subjects.json`: la pipeline `build_excluded_subjects` ne genera il csv, che **non si modifica a mano** (la run successiva lo riscrive per intero). Ogni soggetto è elencato esplicitamente, senza soglie: i dati non hanno un salto naturale su cui mettere una soglia, e quale soggetto limite valga la pena di scartare è un giudizio, non un confronto numerico. L'ultima cella del notebook `lesion_analysis`, dopo aver guardato le distribuzioni di `lesion_metadata.csv`, stampa i blocchi da incollare nel config.

```csv
subject_id,dataset,reason,scope,value
sub-STUKE0146,UKE/WAKEUP_acute,empty_mask,all,0
sub-STUCLUK2160,UCL-UK/UCLStrokeData,all_zero_features,sdc-streamline,0
```

- **`reason`** ha un vocabolario chiuso: `empty_mask`, `lesion_too_small`, `out_of_brain_fraction_too_high`, `all_zero_features` (la riga di feature del soggetto è tutta zero nella rappresentazione indicata da `scope`: sotto qualunque distanza risulta indistinguibile o massimamente lontana dagli altri). Un motivo non in elenco fa fallire la run.
- **`scope`** dice a quale matrice si applica la riga, con vocabolario chiuso: `all`, `lesion`, `sdc-parcellated`, `sdc-voxelwise`, `sdc-streamline`. Serve perché un soggetto può essere inutilizzabile in uno spazio di feature e perfettamente valido negli altri: uno zero nel CSV streamline può essere una misura vera (una lesione che non interseca nessuna streamline di nessun tratto), non un dato rotto, e non deve far sparire il soggetto dalla matrice lesionale né da quella voxelwise. `all` dichiara esplicitamente "ovunque"; un soggetto con una riga `all` **non può** averne anche una più stretta (le due righe si contraddirebbero).
- **`value`** è la metrica che ha motivato l'esclusione. Serve a rivedere la decisione a mesi di distanza: "sub-X escluso" non si può giudicare, "sub-X escluso a 2 voxel" sì.
- **Ogni riga è validata** contro il registro: ID inesistente, coppia (ID, scope) duplicata, `dataset` in disaccordo col registro, `scope` o `reason` non registrati, `value` non numerico fanno fallire la run. La validazione copre **tutto il file**, non solo le righe della matrice che sta girando: un refuso in una riga destinata a un'altra matrice fa fallire anche questa, invece di restare dormiente fino a quando qualcuno costruisce quell'altra.

### Il config: `config/pipelines/build_excluded_subjects.json`

```json
{
  "output_path": "assets/metadata/excluded_subjects.csv",
  "lesion_metadata_path": "assets/metadata/lesion_metadata.csv",
  "exclusions": [
    {"reason": "empty_mask", "scope": "all", "value_column": "lesion_volume_voxels_1mm", "subjects": ["sub-STUKLFR0671"]},
    {"reason": "all_zero_features", "scope": "sdc-streamline", "value": 0, "subjects": ["sub-STUCLUK0383", "..."]}
  ]
}
```

| Parametro | Descrizione |
| :--- | :--- |
| **`output_path`** | Il csv generato. È riscritto per intero a ogni run, in modo atomico: un crash non lo lascia a metà. |
| **`lesion_metadata_path`** | Il csv da cui si legge il `value` dei motivi di lesione. |
| **`exclusions`** | Lista di blocchi. Una lista vuota è valida e genera un file con la sola intestazione ("nessuna esclusione, deliberatamente"). |
| ↳ **`reason`**, **`scope`** | Dal vocabolario chiuso sopra; una coppia (`reason`, `scope`) compare in un solo blocco. |
| ↳ **`subjects`** | Gli ID, esplicitamente; non vuota, senza ripetizioni. |
| ↳ **`value_column`** *oppure* **`value`** | Esattamente uno dei due: una colonna di `lesion_metadata.csv`, letta per ogni soggetto, oppure una costante (`0` per `all_zero_features`: il numero di feature non nulle, per definizione). |
| **`run_notes`** | Nota libera, finisce nel report. |

La pipeline ricava da sola il `dataset` (dal registro) e il `value`; un ID sconosciuto al registro, o senza riga in `lesion_metadata.csv` quando serve il `value`, fa fallire la run. Un soggetto elencato come `empty_mask` deve avere `value` 0, altrimenti la run fallisce: sarebbe un ID sbagliato che esclude un soggetto con una lesione vera.

Prima di sostituire il file, il risultato passa dallo stesso validatore delle pipeline di matrice, su un file temporaneo: un config che produrrebbe un file rifiutato fallisce qui, e il file esistente resta com'è. `--dry-run` esegue ogni controllo e scrive il report in `summaries/build_excluded_subjects/` (con le righe aggiunte e rimosse rispetto al file attuale), ma non il csv.

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
  "lesion_side_from": "lesion_side_2mm",
  "geometric_override_datasets": ["UNIPD/WashU"]
}
```

`enrich_metadata` **non apre nessuna maschera**: copia numeri già calcolati. Ogni scelta su *come* una maschera è misurata (quali griglie, se azzerare i voxel fuori dal brain, quale soglia per il lato) vive nel config di `compute_lesion_metadata`, non qui.

- **`copy_columns`**: colonne copiate **con lo stesso nome**, per tutti i soggetti in scope, sovrascrivendo. Ogni nome deve esistere nel csv, e non può essere una colonna di `populate_metadata.py`. Una colonna non elencata non viene portata nel registro e resta disponibile nel csv per il notebook: oggi il volume a 1 mm, le due frazioni e i due indici di lateralità stanno solo lì.
- **`lesion_side_from`**: quale colonna del csv riempie `lesion_side`. Ha una regola diversa da `copy_columns`, per questo è una chiave a sé: scrive **solo dove la risoluzione clinica ha lasciato la cella vuota**, e scrive anche `lesion_side_source = "geometric"`. Un valore clinico non viene sovrascritto, salvo l'eccezione di `geometric_override_datasets` (sotto). `null` disattiva il riempimento e lascia `lesion_side` solo clinico. Richiede `lesion_side` in `variables`.
- **`geometric_override_datasets`**: lista di dataset dove un lato clinico opposto a quello della maschera viene **forzato** a quello geometrico. Obbligatoria; `[]` la disattiva; se non vuota richiede `lesion_side_from`. Un nome non presente nel registro fa fallire la run. Spiegata nella sezione seguente.

Nel registro la colonna resta **`lesion_side`, senza suffisso di griglia**, perché per i soggetti con etichetta clinica quel valore non viene da nessuna griglia: un suffisso sarebbe falso per la maggioranza delle celle. `lesion_side_from` dice da quale griglia viene la parte geometrica, `lesion_side_source` dice quale delle due provenienze ha vinto per ogni soggetto.

### Il lato forzato dalla geometria (`geometric_override_datasets`)

> **Forzatura deliberata.** Per i dataset elencati in `geometric_override_datasets` (oggi solo `UNIPD/WashU`), `participants.csv` **contraddice il tsv sorgente** su alcuni soggetti: ne scrive il lato opposto, preso dalla maschera.

**Perché.** In WashU 11 soggetti su 162 con un lato clinico (6,8%) hanno il lato **opposto** a quello della maschera: 6 `left` → `right` e 5 `right` → `left`. Sono tutti inversioni piene (`|laterality_index_2mm| ≥ 0,95`, la lesione sta tutta dall'altra parte). Le 195 maschere WashU hanno lo stesso header (RAS, stessa affine), e negli altri dataset il tasso è quasi nullo (UKLFR 0/120, UKE 1/120, PSP 1/95): non è rumore di misura. L'ipotesi adottata è che l'**etichetta clinica** sia sbagliata alla fonte, non la maschera.

**Regola.** Un soggetto di un dataset elencato, con lato clinico `left`/`right`, il cui lato in `lesion_side_from` è l'opposto (`left` contro `right`), riceve nel registro il lato **geometrico** e `lesion_side_source = "geometric"`. Un `both` geometrico non fa scattare nulla: è un disaccordo di grado, non un'inversione.

**Come riconoscerli.**

- Nel registro: `lesion_side_source = "geometric"` per un soggetto che nel tsv ha un valore.
- Nel log di ogni run (`logs/enrich_metadata/`): un `WARNING` con il numero e gli ID dei soggetti forzati.

**Cosa non è.** Non è una misura: è un'assunzione. Non è verificata sulla T1 dei soggetti, quindi non si sa se a sbagliare sia l'etichetta o la maschera. Se risultasse la maschera, la lista va svuotata (`[]`) e la run rifatta: il registro torna al lato clinico.

**Cosa cambia a valle.** `lesion_side_source = "clinical"` non vuol più dire "ogni etichetta del tsv": le inversioni di WashU ne sono escluse. `calibrate_lesion_side_threshold.py` usa quelle righe come verità, quindi non vede più questi soggetti. L'accordo che calcola ora è più alto del 97,4% di `knowledge/neuroimaging/lesion_laterality.md` (calcolato su tutte le etichette del tsv, inversioni comprese) e non è confrontabile con esso.


### Il join è stretto nei due sensi

Tre disaccordi fermano la run, nessuno viene ignorato:

| Situazione | Cosa significa |
| :--- | :--- |
| soggetto in scope con `has_lesion` vero e senza riga nel csv | il csv è vecchio: rilancia `compute_lesion_metadata` |
| riga nel csv per un soggetto che il registro non conosce | i due file non sono d'accordo su chi esiste |
| riga nel csv per un soggetto con `has_lesion` falso | i due file non sono d'accordo su chi ha una maschera |

Il primo controllo è limitato ai `datasets` della run (arricchire un sottoinsieme della coorte è legittimo); gli altri due sono globali, perché una riga che non corrisponde a nessuno è sbagliata comunque.

### Come sapere se registro e csv sono allineati

`participants.csv` è una **copia** dei valori di `lesion_metadata.csv`, non un riferimento: è allineato solo se `enrich_metadata` è girato **dopo** l'ultima scrittura del csv. Il join stretto qui sopra intercetta i disaccordi su *chi* ha una maschera, non su un valore diverso (un volume o un lato) per lo stesso soggetto: un csv rigenerato senza rilanciare `enrich_metadata` lascia nel registro i valori precedenti, senza errori.

Due controlli, uno per file:

- **Registro contro csv**: `lesion_volume_voxels_2mm` del registro deve coincidere con quello del csv per ogni soggetto. Se no, rilancia `enrich_metadata`.
- **Csv contro maschere e config**: il csv è aggiornato se `lesion_metadata.config.json` (accanto al csv) coincide con `config/pipelines/compute_lesion_metadata.json` e nessuna maschera è più recente del csv:

  ```bash
  find data/clinical_connectome/derivatives -path '*manual_masks*' -name '*_label-lesion_mask.nii.gz' -newer assets/metadata/lesion_metadata.csv | wc -l   # 0 = nessuna maschera più recente
  ```

  Questi controlli non vedono un cambio di **codice** in `src/features/lesion.py` che alteri le misure: dopo una modifica a come si misura una maschera, `compute_lesion_metadata` va rilanciata.

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
| `notebooks/exploration/lesion_analysis.ipynb` | `lesion_metadata.csv`, per decidere le esclusioni |

Conseguenza pratica: se aggiungi `NIHSS` al registro oggi, **anche le run vecchie** si possono colorare per NIHSS, senza rigenerarle.

---

## Attenzione: `has_*` descrive il disco, e il disco può essere potato

`populate_metadata.py` scandisce le cartelle per riempire `has_lesion`/`has_sdc`/`has_features`, e una scansione non vede dentro un `.tar.gz`. Le cartelle archiviate localmente per spazio (oggi `UNIPD/WashU/features/` e `data/derived/features/masked_fc/`) vanno quindi decompresse prima, oppure i `has_*` interessati vanno corretti a mano. Vedi [`docs/guides/datasets.md`](datasets.md).
