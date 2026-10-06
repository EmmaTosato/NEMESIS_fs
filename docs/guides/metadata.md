# Metadati dei soggetti — come si usano

Tutto ciò che sappiamo dei soggetti sta in **un file solo**: `assets/metadata/participants.csv`, versionato in git, una riga per soggetto.

Lo scrivono due script, che rispondono a due domande diverse e non si sovrascrivono mai a vicenda:

| Script | Domanda | Colonne che scrive |
| :--- | :--- | :--- |
| `src/pipeline/populate_metadata.py` | chi esiste | `subject_id`, `original_id`, `dataset`, `disease_id`, `has_lesion`, `has_sdc`, `has_features` |
| `src/pipeline/enrich_metadata.py` | cosa sappiamo di lui | `age`, `sex`, `education`, `lesion_side`, `lesion_side_source`, `NIHSS`, `clinical_date`, `lesion_volume_voxels_{2mm,1mm}`, `disconnection_load_voxels_{2mm,1mm}`, `disconnection_mean_{2mm,1mm}` |

- **Dettagli architetturali/perché è fatto così**: [`docs/dev/metadata.md`](../dev/metadata.md)
- **Quali campi esistono in quale dataset**: [`docs/guides/datasets.md`](datasets.md)

`assets/metadata/` contiene altri tre file, **separati** dal registro:

| File | Cosa c'è | Chi lo scrive |
| :--- | :--- | :--- |
| `lesion_metadata.csv` | tutto ciò che si misura su una maschera di lesione: volume, frazione fuori dal brain, indice di lateralità e lato, **per ogni griglia** | `src/pipeline/compute_lesion_metadata.py` |
| `sdc_metadata.csv` | quanto è disconnesso ciascun soggetto, in totale: carico e media sul cervello, dal suo disconnettoma | `src/pipeline/compute_sdc_metadata.py` |
| `excluded_subjects.csv` | quali soggetti tenere fuori dalle matrici di produzione, con il motivo | `src/pipeline/build_excluded_subjects.py`, dalla lista che scrivi **tu** nel config `build_excluded_subjects.json` |

---

## Come si lancia, in ordine

Quattro passaggi, in quest'ordine: chi esiste, cosa misurano le maschere, quanto sono disconnessi i soggetti, e infine il join che riempie il registro. Un quarto, indipendente, genera la lista delle esclusioni (`excluded_subjects.csv`) quando cambia.

```bash
conda activate nemesis
cd "$PROJECT_ROOT"

PYTHONPATH="$PROJECT_ROOT" python -m src.pipeline.populate_metadata --config config/pipelines/populate_metadata.json
python -m src.pipeline.compute_lesion_metadata --config config/pipelines/compute_lesion_metadata.json
python -m src.pipeline.compute_sdc_metadata --config config/pipelines/compute_sdc_metadata.json
python -m src.pipeline.enrich_metadata --config config/pipelines/enrich_metadata.json

# quando cambia la lista dei soggetti esclusi:
python -m src.pipeline.build_excluded_subjects --config config/pipelines/build_excluded_subjects.json
```

Tutte le pipeline accettano `--dry-run`: eseguono ogni controllo e scrivono il report, senza toccare nulla. **Usalo la prima volta dopo aver cambiato un config.**

Su cluster: `sbatch jobs/run_compute_lesion_metadata.sh`, `sbatch jobs/run_compute_sdc_metadata.sh`, `sbatch jobs/run_enrich_metadata.sh`, `sbatch jobs/run_build_excluded_subjects.sh` (le cartelle `logs/slurm/<pipeline>/` devono già esistere).

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

**`side_threshold` è 0.20, calibrato e non inventato**: riproduce il 97.4% di 1445 soggetti con etichetta clinica vera sulla griglia a 2 mm (metodo, letteratura e limiti in [`knowledge/neuroimaging/lesion_laterality.md`](../../knowledge/neuroimaging/lesion_laterality.md)). La stessa soglia vale anche a 1 mm: sugli stessi 1350 soggetti con lato clinico (PSP esclusa: le sue maschere a 1 mm sono frazionarie) la soglia 0.20 dà la stessa accuratezza a 1 mm e a 2 mm (97,3%) e attribuisce a **tutti** lo stesso lato (0 differenze su 1350). Il confronto si rifà con `python -m src.pipeline.calibrate_lesion_side_threshold --grid 1mm --datasets ...`.

**Costo**: una lettura da disco per soggetto e un ricampionamento per griglia. Il calcolo è in streaming, un soggetto per volta, quindi la memoria non dipende da quanti soggetti ci sono. `overwrite: false` lascia intatto un csv esistente e la run esce subito, così rilanciarla per sbaglio non ripaga il costo.

Accanto al csv viene scritto `lesion_metadata.config.json`, il config esatto della run che l'ha prodotto: un csv di cui non si sappia su quali griglie e con quale correzione è stato calcolato non è interpretabile.

---

## `compute_sdc_metadata.py` — quanto è disconnesso un soggetto

Produce `assets/metadata/sdc_metadata.csv`: una riga per **ogni** soggetto con un disconnettoma (`has_sdc` vero nel registro), nessuna esclusione applicata. Come `lesion_metadata.csv`, è agnostica del clinico.

Due colonne per griglia, su **2 mm** (la griglia di produzione) e **1 mm** (quella nativa delle mappe: `res-1` è nel nome del file). Qui sotto il suffisso `<g>` è il nome della griglia:

| Colonna | Cos'è |
| :--- | :--- |
| `disconnection_load_voxels_<g>` | La somma della probabilità di disconnessione sui voxel **dentro il cervello**. È l'analogo del volume lesionale: per una mappa binaria sarebbe un conteggio di voxel; qui ogni voxel pesa la sua probabilità, quindi l'unità è "voxel pesati per probabilità" (1 mm³ a 1 mm, 8 mm³ a 2 mm). |
| `disconnection_mean_<g>` | La stessa somma divisa per il numero di voxel del cervello: la probabilità media di disconnessione sul cervello, tra 0 e 1. |

Su una stessa griglia le due colonne **ordinano i soggetti allo stesso modo**: il divisore è una costante della griglia. Cambia solo il numero che si legge (`~60 000` oppure `~0,033`). Il carico si legge come un volume, la media come "quanta parte del cervello, in media".

### Cosa viene misurato, e cosa no

- **Solo dentro la maschera cerebrale.** Il disconnettoma di BCBToolKit ha una quota di massa fuori dal cervello (mediana 0,80% della massa totale, fino all'8,9% in un caso, misurato su 400 soggetti casuali): è tractografia che esce dal cervello, non disconnessione. È la stessa scelta di `correct_out_of_brain` per le lesioni.
- **Senza soglia.** Ogni voxel pesa la sua probabilità. È diverso dal pannello "Disconnessione per cluster" dell'Embedding Explorer, che conta un voxel come disconnesso solo sopra `0.5`: le due quantità ordinano i soggetti quasi allo stesso modo (Spearman 0,99 su 200 soggetti) ma non sono la stessa formula.
- **Ogni mappa con il suo header.** Le mappe non stanno tutte sullo stesso reticolo di voxel: tra gli 8 dataset ci sono **3 header distinti** (orientamento LAS con offset x `+90`; RAS con `-90`, cioè traslato di 1 voxel; RAS con `-91`, identico al template MNI). Ogni mappa viene portata sulla griglia con il proprio header (`nearest`; a 1 mm è una rimappatura intera esatta, la somma non cambia), mai con un flip fisso: un flip è giusto per un solo gruppo e specchierebbe gli altri senza alcun errore.

### Parametri di `config/pipelines/compute_sdc_metadata.json`

| Parametro | Descrizione |
| :--- | :--- |
| **`project`**, **`data_root`** | Dove stanno i dati (`data/clinical_connectome/derivatives`). |
| **`output_path`** | Il csv da scrivere (`assets/metadata/sdc_metadata.csv`). |
| **`datasets`** | Lista di dataset da misurare. Un nome duplicato o sconosciuto al registro fa fallire la run. |
| **`group_filter`** | Gruppi ammessi (`["ST"]`: solo i pazienti con ictus). |
| **`disconnectome_glob`** | Come si trova la mappa di un soggetto, relativo alla cartella del dataset. |
| **`resample_interpolation`** | `nearest` (consigliata: l'unica che non altera la somma). |
| **`grids`** | Oggetto `{nome: {reference_template_path, brain_mask_path}}`, entrambi i path obbligatori per ogni griglia, nell'ordine in cui compariranno le colonne. Il nome diventa il suffisso delle due colonne, quindi dev'essere alfanumerico e unico. Stessa forma di `grids` in `compute_lesion_metadata.json`. |
| **`overwrite`** | `false`: se il csv esiste la run esce subito (la misura costa una lettura e un ricampionamento per soggetto, circa 20 minuti sull'intera coorte con due griglie). `true` lo ricalcola e lo sostituisce. |
| **`run_notes`** | Nota libera, finisce nel report. |

Accanto al csv viene scritto `sdc_metadata.config.json`, il config esatto della run che l'ha prodotto.

### Registro e disco devono essere d'accordo

La run si ferma, elencando tutti i dataset coinvolti, se:

| Situazione | Cosa significa |
| :--- | :--- |
| un soggetto con `has_sdc` vero non ha la mappa su disco | i dati sono incompleti, oppure `data/` è una copia locale parziale |
| una mappa su disco per un soggetto senza `has_sdc` | il registro è vecchio: rilancia `populate_metadata` |
| una mappa con valori fuori da [0, 1] o non finiti | non è una probabilità: una scala in percento darebbe un carico ~100 volte più grande e passerebbe ogni altro controllo |

---

## `excluded_subjects.csv` — chi resta fuori dalle matrici

Il csv è scritto dalla pipeline `build_excluded_subjects` a partire dal config `config/pipelines/build_excluded_subjects.json`, dove elenchi i soggetti da escludere. Una volta scritto, **il csv resta com'è**: la pipeline gli **aggiunge** i soggetti nuovi senza toccare le righe che ci sono, e per togliere una riga la cancelli a mano dal csv. Con `overwrite: true` il csv è invece ricostruito dal solo config. Ogni soggetto è elencato esplicitamente, senza soglie: i dati non hanno un salto naturale su cui mettere una soglia, e quale soggetto limite valga la pena di scartare è un giudizio, non un confronto numerico. L'ultima cella del notebook `lesion_analysis`, dopo aver guardato le distribuzioni di `lesion_metadata.csv`, stampa i blocchi da incollare nel config.

**Criteri adottati.** Le lesioni piccole **non** vengono escluse: anche una lesione focale o minima può essere clinicamente grave, quindi per volume si scarta solo la maschera vuota. Si escludono invece i soggetti con più del **30%** dei voxel di lesione fuori dal brain (`out_of_brain_fraction_2mm`, misurata prima dell'azzeramento); sotto quella soglia il soggetto resta, e i suoi voxel fuori dal brain sono azzerati solo se la matrice è costruita con `correct_out_of_brain: true`. Il razionale è in [`docs/dev/metadata.md`](../dev/metadata.md#criteri-di-esclusione-adottati).

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
  "overwrite": false,
  "exclusions": [
    {"reason": "empty_mask", "scope": "all", "value_column": "lesion_volume_voxels_1mm", "subjects": ["sub-STUKLFR0671"]},
    {"reason": "all_zero_features", "scope": "sdc-streamline", "value": 0, "subjects": ["sub-STUCLUK0383", "..."]}
  ]
}
```

| Parametro | Descrizione |
| :--- | :--- |
| **`output_path`** | Il csv scritto. La scrittura è atomica: un crash non lo lascia a metà. |
| **`overwrite`** | `false` (il modo usuale): il csv esistente resta com'è, comprese le righe aggiunte o tolte a mano, e le righe del config vengono **aggiunte**. Una riga già presente per lo stesso soggetto, scope e motivo non viene toccata (resta il suo `value`, e se il config ne calcola uno diverso la run lo segnala); lo stesso soggetto e scope sotto un altro motivo è un conflitto e fa fallire la run. Un file assente viene creato, uno con le colonne vecchie (senza `scope`) non si può estendere. `true`: il csv è ricostruito dal solo config, e ciò che conteneva d'altro è perso. |
| **`lesion_metadata_path`** | Il csv da cui si legge il `value` dei motivi di lesione. |
| **`exclusions`** | Lista di blocchi. Con `overwrite: true`, una lista vuota genera un file con la sola intestazione ("nessuna esclusione, deliberatamente"); con `overwrite: false` non aggiunge nulla. |
| ↳ **`reason`**, **`scope`** | Dal vocabolario chiuso sopra; una coppia (`reason`, `scope`) compare in un solo blocco. |
| ↳ **`subjects`** | Gli ID, esplicitamente; non vuota, senza ripetizioni. |
| ↳ **`value_column`** *oppure* **`value`** | Esattamente uno dei due: una colonna di `lesion_metadata.csv`, letta per ogni soggetto, oppure una costante (`0` per `all_zero_features`: il numero di feature non nulle, per definizione). |
| **`run_notes`** | Nota libera, finisce nel report. |

La pipeline ricava da sola il `dataset` (dal registro) e il `value`; un ID sconosciuto al registro, o senza riga in `lesion_metadata.csv` quando serve il `value`, fa fallire la run. Un soggetto elencato come `empty_mask` deve avere `value` 0, altrimenti la run fallisce: sarebbe un ID sbagliato che esclude un soggetto con una lesione vera.

Prima di sostituire il file, il risultato passa dallo stesso validatore delle pipeline di matrice, su un file temporaneo: un config che produrrebbe un file rifiutato fallisce qui, e il file esistente resta com'è. `--dry-run` esegue ogni controllo e scrive il report in `summaries/build_excluded_subjects/` (con le righe aggiunte e rimosse rispetto al file attuale), ma non il csv. In modalità `overwrite: false` il config può contenere solo i soggetti **nuovi**: quelli già nel csv non servono, e se restano nel config vengono saltati.

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
| **`sdc_metadata`** | Oggetto opzionale (`null` salta le colonne di disconnessione) — il join su `sdc_metadata.csv`. Vedi sotto. |
| **`fill`** | `true`: scrive **solo** le celle vuote delle variabili cliniche, ogni valore già presente resta intatto. `false`: le ricalcola tutte. Non ha effetto sulle colonne copiate da `lesion_metadata.csv` e `sdc_metadata.csv`, che vengono sempre sovrascritte. |
| **`run_notes`** | Nota libera, finisce nel report. |

### `lesion_metadata`: il join sul csv delle misure

```json
"lesion_metadata": {
  "path": "assets/metadata/lesion_metadata.csv",
  "copy_columns": ["lesion_volume_voxels_2mm", "lesion_volume_voxels_1mm"],
  "lesion_side_from": "lesion_side_2mm",
  "geometric_override_datasets": []
}
```

`enrich_metadata` **non apre nessuna maschera**: copia numeri già calcolati. Ogni scelta su *come* una maschera è misurata (quali griglie, se azzerare i voxel fuori dal brain, quale soglia per il lato) vive nel config di `compute_lesion_metadata`, non qui.

- **`copy_columns`**: colonne copiate **con lo stesso nome**, per tutti i soggetti in scope, sovrascrivendo. Ogni nome deve esistere nel csv, e non può essere una colonna di `populate_metadata.py`. Una colonna non elencata non viene portata nel registro e resta disponibile nel csv per il notebook: oggi le due frazioni fuori dal brain e i due indici di lateralità stanno solo lì. Il volume è copiato su entrambe le griglie perché l'Embedding Explorer offre la scelta 1 mm/2 mm.
- **`lesion_side_from`**: quale colonna del csv riempie `lesion_side`. Ha una regola diversa da `copy_columns`, per questo è una chiave a sé: scrive **solo dove la risoluzione clinica ha lasciato la cella vuota**, e scrive anche `lesion_side_source = "geometric"`. Un valore clinico non viene sovrascritto, salvo l'eccezione di `geometric_override_datasets` (sotto). `null` disattiva il riempimento e lascia `lesion_side` solo clinico. Richiede `lesion_side` in `variables`.
- **`geometric_override_datasets`**: lista di dataset dove un lato clinico opposto a quello della maschera viene **forzato** a quello geometrico. Obbligatoria; `[]` (il valore in uso) la disattiva; se non vuota richiede `lesion_side_from`. Un nome non presente nel registro fa fallire la run. Spiegata, e motivata, nella sezione seguente.

Nel registro la colonna resta **`lesion_side`, senza suffisso di griglia**, perché per i soggetti con etichetta clinica quel valore non viene da nessuna griglia: un suffisso sarebbe falso per la maggioranza delle celle. `lesion_side_from` dice da quale griglia viene la parte geometrica, `lesion_side_source` dice quale delle due provenienze ha vinto per ogni soggetto.

### Il valore `both` ha due origini, e non sono equivalenti

`lesion_side` assume i valori `left`, `right` e `both`. Il `both` del registro viene da due fonti, distinte da `lesion_side_source`:

- **`clinical`**: il valore del tsv. Esiste solo in UKE-WAKEUP (25 soggetti nel registro). Il tsv non spiega cosa indichi (`disease_notes` è vuoto) e il registro lo riporta com'è, senza metterlo in discussione.
- **`geometric`**: la maschera ha `|laterality_index| < side_threshold` (64 soggetti, quasi tutti UCL-UK), cioè una lesione che occupa i due emisferi in modo simile.

I due significati non coincidono: il `both` clinico non implica una maschera bilaterale (per 14 dei 24 `both` clinici con un indice calcolabile la lesione sta quasi tutta da un lato, `|laterality_index| ≥ 0,9`) e una maschera bilaterale non ha un `both` clinico (la soglia ritrova 3 dei 24). Nessuna soglia riduce la differenza (limiti in [`knowledge/neuroimaging/lesion_laterality.md`](../../knowledge/neuroimaging/lesion_laterality.md)). Chi usa `lesion_side` per un'analisi sul lato legge `both` insieme a `lesion_side_source`, e non lo tratta come "lesione bilaterale" senza controllare da dove viene.

### Forzare il lato geometrico (`geometric_override_datasets`, oggi spenta)

> **Opzione disponibile, spenta.** `geometric_override_datasets` è `[]`: nessun lato clinico viene sovrascritto e `participants.csv` riporta, per ogni soggetto con etichetta, il valore del tsv (`lesion_side_source = "clinical"`).

**Cosa fa quando è accesa.** Per i dataset elencati, un soggetto con lato clinico `left`/`right` il cui lato in `lesion_side_from` è l'opposto (`left` contro `right`) riceve il lato **geometrico** e `lesion_side_source = "geometric"`. Un `both` geometrico non fa scattare nulla: è un disaccordo di grado, non un'inversione. Ogni soggetto forzato è un `WARNING` nel log di `enrich_metadata` (`logs/enrich_metadata/`).

**Perché è spenta.** In WashU 11 soggetti su 162 con un lato clinico (6,8%) hanno il lato opposto a quello della maschera (6 `left` → `right`, 5 `right` → `left`), tutte inversioni piene (`|laterality_index_2mm| ≥ 0,95`). Il disaccordo è associato alla manualità (mancini 5/16, 31%; destrimani 6/146, 4%; Fisher p = 0,0016). La regola presuppone che sbagli l'etichetta clinica, e i dati indipendenti dal lato non lo confermano. Il tsv di WashU ha `ARAT_L/R` e `9HPT_L/R` (arto superiore, mano sinistra e destra): il deficit è controlaterale alla lesione. Sui 151 soggetti dove etichetta e maschera concordano, l'ARAT indica il lato giusto nel 98% dei casi (90/92) e il 9HPT nell'86% (102/119). Sugli 11 in disaccordo i test sono informativi in 8: **in 6 indicano il lato clinico** (`sub-STUNIPD0002`, `0026`, `0056`, `0077`, `0147`, `0222`), in 2 il lato della maschera (`0008`, `0179`), 3 non sono decidibili (`0131`, `0151`, `0187`). Forzare il lato geometrico scriverebbe quindi il lato sbagliato per la maggior parte dei casi decidibili.

Dove sta l'inversione non è accertato. Nelle immagini dei soggetti WashU la lesione nativa e la maschera in MNI sono dallo stesso lato (la normalizzazione non inverte), e le proprietà degli header delle T1 native (orientamento, software di conversione, scanner) non distinguono gli 11 da 20 controlli concordi. Per i soggetti degli altri dataset in disaccordo (sui dati completi, a 2 mm: UKLFR 2/700, UKE-WAKEUP 2/411, PSP 0/94, UKE-SFB936 0/53) la stessa verifica dà `sub-STUKE0164` e `sub-STUKLFR0403` etichetta giusta, `sub-STUKLFR0576` maschera giusta, `sub-STUKE0154` non decidibile; per `sub-STUKLFR0403` la maschera manuale sul server è dal lato dell'etichetta e quella derivata dall'SDC, che è la nostra, dal lato opposto.

**Calibrazione della soglia.** `calibrate_lesion_side_threshold.py` usa come verità le righe `lesion_side_source = "clinical"`: con la forzatura spenta sono tutte le etichette del tsv, quindi il suo accordo (97,4% a 2 mm su 1445 soggetti, soglia 0.20) è direttamente confrontabile con `knowledge/neuroimaging/lesion_laterality.md`. Con la forzatura accesa gli invertiti ne uscirebbero e l'accordo risulterebbe più alto. Le inversioni piene sbagliano a qualunque soglia: senza i 15 casi dei dataset con etichetta clinica l'accordo a 0.20 è del 98,4%.

### `sdc_metadata`: il join sul csv della disconnessione

```json
"sdc_metadata": {
  "path": "assets/metadata/sdc_metadata.csv",
  "copy_columns": [
    "disconnection_load_voxels_2mm", "disconnection_mean_2mm",
    "disconnection_load_voxels_1mm", "disconnection_mean_1mm"
  ]
}
```

Stessa idea di `lesion_metadata`: `enrich_metadata` **non apre nessuna mappa**, copia numeri già calcolati da `compute_sdc_metadata`. Ogni scelta su *come* si misura la disconnessione (griglia, maschera cerebrale, interpolazione) sta nel config di quella pipeline. Solo `path` e `copy_columns`, entrambi obbligatori: non c'è un equivalente di `lesion_side_from`, perché nessuna colonna riempie un buco in una variabile clinica.

`copy_columns` non può essere vuoto, non può contenere una colonna di `populate_metadata.py`, né una che `enrich_metadata` scrive già da un'altra parte (una variabile clinica, `lesion_side_source`, o una `copy_columns` di `lesion_metadata`): due scrittori per una colonna lascerebbero il valore del secondo, senza errori. Le colonne copiate sono float e restano tali.

### Il join è stretto nei due sensi

Tre disaccordi fermano la run, nessuno viene ignorato:

| Situazione | Cosa significa |
| :--- | :--- |
| soggetto in scope con `has_lesion` vero e senza riga nel csv | il csv è vecchio: rilancia `compute_lesion_metadata` |
| riga nel csv per un soggetto che il registro non conosce | i due file non sono d'accordo su chi esiste |
| riga nel csv per un soggetto con `has_lesion` falso | i due file non sono d'accordo su chi ha una maschera |

Il primo controllo è limitato ai `datasets` della run (arricchire un sottoinsieme della coorte è legittimo); gli altri due sono globali, perché una riga che non corrisponde a nessuno è sbagliata comunque.

Il join su `sdc_metadata.csv` applica gli stessi tre controlli contro `has_sdc` invece di `has_lesion`: un soggetto con una maschera ma senza disconnettoma (o il contrario) è legittimo per il join che non lo riguarda.

### Come sapere se registro e csv sono allineati

`participants.csv` è una **copia** dei valori di `lesion_metadata.csv` e `sdc_metadata.csv`, non un riferimento: è allineato solo se `enrich_metadata` è girato **dopo** l'ultima scrittura del csv. Il join stretto qui sopra intercetta i disaccordi su *chi* ha una maschera, non su un valore diverso (un volume o un lato) per lo stesso soggetto: un csv rigenerato senza rilanciare `enrich_metadata` lascia nel registro i valori precedenti, senza errori.

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
