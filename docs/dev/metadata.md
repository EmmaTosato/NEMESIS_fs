# Metadati clinici — riferimento tecnico

Audience: chi lavora su `src/pipeline/populate_metadata.py`, `src/pipeline/compute_lesion_metadata.py`, `src/pipeline/enrich_metadata.py`, `src/utils/participants.py`, o chi deve capire dove vive un dato valore clinico/anagrafico (age, sex, NIHSS, lesion_side...) o derivato dalle maschere (volume, lato) e come ci è arrivato.

Il ridisegno è **in vigore**: la fonte di verità unica esiste e i consumatori la leggono. Per quali campi esistono in quale dataset, vedi `docs/guides/datasets.md`.

## Come funziona

Una sola fonte di verità: **`assets/metadata/participants.csv`**, una riga per soggetto, versionata in git. Due script la scrivono, ognuno risponde a una domanda diversa, e nient'altro nel repo ricalcola valori clinici per conto proprio.

```
data/clinical_connectome/metadata_tsv/participants_*.tsv        (grezzi, uno per dataset, gitignored)
data/clinical_connectome/derivatives/<dataset>/{manual_masks,sdc,features}/   (cosa c'è su disco)
        │  src/pipeline/populate_metadata.py               — chi esiste
        ▼
assets/metadata/participants.csv ◄──────────────┐
                                                │  src/pipeline/enrich_metadata.py
                                                │  — cosa sappiamo di lui (un JOIN, non un calcolo)
        ┌───────────────────────────────────────┴───────────┐
        │                                                   │
data/clinical_connectome/metadata_tsv/*.tsv       assets/metadata/lesion_metadata.csv
   (variabili cliniche)                              ▲
                                                     │  src/pipeline/compute_lesion_metadata.py
                                                     │  — cosa misurano le maschere
                                          data/clinical_connectome/derivatives/<dataset>/manual_masks/

assets/metadata/excluded_subjects.csv   — chi resta fuori dalle matrici (generato da build_excluded_subjects)
        │  letto da build_lesion_matrix.py e build_sdc_matrix.py, non da enrich
```

**Quattro file, quattro domande.** Il registro (`participants.csv`) risponde a "chi esiste" e "cosa sappiamo di lui"; `lesion_metadata.csv` a "cosa misurano le sue maschere"; `excluded_subjects.csv` a "chi entra in analisi".

`enrich_metadata.py` **non apre nessun file NIfTI**: i valori derivati dalle maschere li copia da `lesion_metadata.csv`. Non li copia più nemmeno da un artefatto `data/derived/lesion_matrix/<sessione>/` già costruito — quella scelta, più vecchia, generava esattamente la seconda fonte di verità che voleva evitare (28-09-26, `.claude/history/methods_changelog.md`: 900/5721 soggetti con valore diverso tra le due fonti, fino a 38x, dopo che la griglia era cambiata senza ricostruire l'artefatto). Il punto fisso attuale è diverso: il valore nasce **in un posto solo**, la pipeline che misura le maschere, e il registro ne tiene una copia dichiarata.

| | `populate_metadata.py` | `enrich_metadata.py` |
|---|---|---|
| Domanda | chi esiste | cosa sappiamo di lui |
| Scrive | `subject_id`, `original_id`, `dataset`, `disease_id`, `has_lesion`, `has_sdc`, `has_features` | `age`, `sex`, `lesion_side`, `lesion_side_source`, `NIHSS`, `education`, `clinical_date`, `lesion_volume_voxels_2mm` |
| Flag di idempotenza | `overwrite` — false: aggiunge solo soggetti nuovi, righe esistenti intatte; true: ricalcola le proprie colonne preservando quelle dell'altro script | `fill` — true: riempie solo le celle vuote delle variabili richieste; false: ricalcola tutto il richiesto |

Registry condiviso: **`config/registry/metadata_sources.json`** — per ogni dataset, il path del tsv grezzo e quello della cartella derivatives. Lo leggono entrambi gli script, così la corrispondenza dataset↔path esiste in un posto solo (non è derivabile meccanicamente: `participants_UCL.tsv` ↔ `UCL-UK/UCLStrokeData`).

### Scelte da conoscere

- **CSV, non Excel.** Excel converte le date e mangia gli zeri iniziali a ogni ciclo di lettura/scrittura, e in questo repo è già costato una perdita di dati (vedi `.claude/lessons_learned.md`). Il CSV dà anche diff git leggibili, che è ciò che rende utile versionare la fonte di verità. Leggerlo sempre con `dtype=str`.
- **`subject_id`, non `participant_id`.** La forma canonica `sub-{disease}{site}{num}`, la stessa di ogni `metadata.csv` e di `src/utils/subject_ids.py::group_of` (regola di naming in `docs/guides/datasets.md`). Il `participant_id` grezzo dei tsv resta in `original_id` — utile solo per UCL-UK, il cui valore grezzo è l'id legacy del sito (`ST_UCL-UK_0001`). Chiamare la colonna `participant_id` l'avrebbe fatta sembrare joinabile coi tsv grezzi pur contenendo un valore *diverso* per UCL-UK — la trappola di `.claude/lessons_learned.md` #30.
- **`disease_id` viene dal subject id**, estratto da `group_of()`, non copiato dal tsv. Il valore del tsv viene confrontato con quello e ogni disaccordo è segnalato come problema di dati, invece di sceglierne uno in silenzio.
- **Solo stroke.** `group_filter: ["ST"]`; i controlli sani sono deliberatamente fuori scope e avranno un file a parte.
- **Inner join.** Un soggetto solo nel tsv (nessun dato su disco) e uno solo su disco (nessuna riga clinica) sono entrambi esclusi ed entrambi elencati nel report del run.

### ⚠️ `has_*` descrive il disco, e il disco può essere potato

`populate_metadata.py` risponde a "cosa ha questo soggetto" scandendo le cartelle. `scripts/archive_local_raw_data.py` comprime via la maggior parte dei soggetti di alcune cartelle per liberare spazio locale (vedi `docs/guides/datasets.md`) — e una scansione non vede dentro un `.tar.gz`.

Ogni cartella potata porta quindi un **manifest**, `<nome>_archive_subjects.tsv` (`subject_id`, `source` ∈ {`kept_in_place`, `archive`}), scritto da `archive_local_raw_data.py`: il registro macchina-leggibile della popolazione reale, leggibile senza decomprimere gigabyte. `populate_metadata.py` deliberatamente **non** lo legge: la potatura è una misura temporanea di spazio locale, non una proprietà permanente del progetto, e cablarla nella pipeline significherebbe incastonare un workaround nel contratto.

**Quindi: dopo aver lanciato `populate_metadata.py` o `enrich_metadata.py`, controlla se qualche cartella è potata e correggi a mano i `has_*` interessati** — oppure decomprimi prima e lancia con `overwrite=true`. Le cartelle potate oggi sono `UNIPD/WashU/features/` e `data/derived/features/masked_fc/`. Il gruppo del soggetto non è memorizzato nel manifest perché derivabile: `group_of(subject_id)`.

## Cosa esiste davvero adesso

- **`assets/metadata/participants.csv`** — 5853 soggetti stroke, con le colonne di entrambi gli script: `subject_id`, `original_id`, `dataset`, `disease_id`, `has_lesion`, `has_sdc`, `has_features` (populate) e `age`, `sex`, `education`, `lesion_side`, `lesion_side_source`, `NIHSS`, `clinical_date`, `lesion_volume_voxels_2mm` (enrich).
- **`assets/metadata/lesion_metadata.csv`** — una riga per soggetto con maschera, quattro colonne per griglia (`lesion_volume_voxels_<g>`, `out_of_brain_fraction_<g>`, `laterality_index_<g>`, `lesion_side_<g>`), più `lesion_metadata.config.json` accanto: il config della run che l'ha prodotto.
- **`assets/metadata/excluded_subjects.csv`** — `subject_id, dataset, reason, scope, value`, generato da `src/pipeline/build_excluded_subjects.py` dal suo config.
- **I tsv per-dataset `assets/metadata/<DATASET>_participants_*.tsv` non esistono più**: cancellati. Ogni consumatore è stato spostato sul file unico.
- **`data/derived/<pipeline>/<sessione>/metadata.csv`** — contiene solo ciò che appartiene a quella run (`subject_id`, `dataset`, `lesion_volume_voxels` per `build_lesion_matrix.py`). Non è più la fonte da cui `enrich_metadata.py` copia `lesion_volume_voxels` in `participants.csv` (fino al 28-09-26 lo era, vedi sopra) — resta solo l'artefatto della run stessa, la sua colonna può differire da quella nel registro se le due griglie non coincidono.

### Chi legge il registro

| Consumatore | Cosa ci prende |
|---|---|
| `src/features/sdc.py` | `has_lesion`, criterio di ammissione di `build_sdc_matrix.py` |
| `src/analysis/embedding_coloring.py` | `lesion_side`/`NIHSS` per i color mode `side`/`nihss`, risolti al momento del plot |
| `src/analysis/cluster_description.py` | age/sex/education/NIHSS/`lesion_volume_voxels_2mm` per la composizione dei cluster nel pannello di `embedding_app.py` |
| `notebooks/post-results_analysis/clustering_evaluation.ipynb` | age/sex/NIHSS per le demografiche per cluster |

Il join con i tsv grezzi avviene su **`original_id`**, non su `subject_id`: il `participant_id` grezzo è l'id canonico per quasi tutti i dataset ma è l'id legacy di sito per UCL-UK (`ST_UCL-UK_0001`). `participants.csv` fa da ponte perché li contiene entrambi — vedi `.claude/lessons_learned.md` #30.

I valori mancanti sono una **cella vuota**, uniformemente. Il registro non è un input di plotting: chi ha bisogno di una sentinella categorica (`"unknown"` per una legenda) se la applica in lettura. L'unica colonna che porta informazione in più è `lesion_side_source`.

### Sostituzioni di colonna registrate

Quando una variabile non esiste con il suo nome canonico in un dataset, `enrich_metadata.py` la legge da un'altra colonna **solo** se la sostituzione è scritta a mano in `VARIABLE_SOURCE_OVERRIDES`; non viene mai dedotta da un nome simile. Ogni sostituzione applicata finisce nel log a `WARNING` e in una sezione dedicata del report di run, perché è un'assunzione di equivalenza clinica e non deve restare invisibile.

Una sola oggi:

| Dataset | Variabile | Letta da | Perché |
|---|---|---|---|
| `UNIPD/PASPORT` | `NIHSS` | `NIHSS_at_presentation` | PASPORT non ha un NIHSS baseline, solo at_presentation/24H/3m |

UCL-UK resta comunque vuoto: non ha nessuna colonna NIHSS-correlata.

## `lesion_metadata.csv`: il livello delle misure sulle maschere

Prodotto da `src/pipeline/compute_lesion_metadata.py`, config `config/pipelines/compute_lesion_metadata.json`. Una riga per **ogni** soggetto con maschera discoverabile, nessuna soglia applicata: le esclusioni sono un livello a parte.

È **agnostico del clinico**: non apre nessun `participants.tsv`, non sa cosa sia un NIHSS. Questa separazione è il motivo per cui esiste come pipeline propria e non come blocco di `enrich_metadata`: leggere imaging e leggere tsv clinici sono due lavori diversi, e prima della separazione le metriche derivate dalle maschere erano sparse su tre posti (una cache diagnostica, due colonne nel registro, una colonna nel `metadata.csv` di ogni matrice) senza che nessuno le avesse tutte.

### Quattro colonne per griglia

| Colonna | Cosa è | Misurata |
|---|---|---|
| `lesion_volume_voxels_<g>` | voxel di lesione | **dopo** l'azzeramento fuori dal brain |
| `out_of_brain_fraction_<g>` | quota di voxel fuori dalla maschera cerebrale | **prima** dell'azzeramento |
| `laterality_index_<g>` | `(sinistra − destra) / (sinistra + destra)` | dopo l'azzeramento |
| `lesion_side_<g>` | `left`/`right`/`both` da `lesion_side_from_laterality_index` | dopo l'azzeramento |

Il nome della griglia diventa il suffisso, quindi `validate_lesion_grids` pretende che sia alfanumerico e unico. Il vocabolario delle griglie è **aperto**: aggiungerne una terza è una voce nel config, non una modifica al codice.

L'ordine "frazione prima, conteggi dopo" non è un dettaglio: la correzione porta la frazione a 0 per costruzione, quindi misurarla dopo renderebbe inutile la sola colonna che serve a scegliere le esclusioni; viceversa un voxel fuori dal cervello non è lesione, quindi non va contato nel volume né deve poter decidere il lato (verificato: senza correzione, 3 voxel di destra fuori dal brain contro 2 di sinistra dentro danno indice −0.2 e lato `right`; con la correzione, +1.0 e `left`).

`NaN` sono casi di dominio espliciti, non buchi: una maschera senza voxel non ha una frazione (0.0 la metterebbe tra i soggetti più puliti della distribuzione usata per scegliere le soglie), e una lesione confinata al piano mediano ha entrambi i conteggi a 0 — quel piano non appartiene a nessuno dei due emisferi (`_hemisphere_masks`), quindi non c'è lato da attribuire pur essendoci un volume reale.

### Perché due griglie, e perché il calcolo è in streaming

Le maschere manuali hanno voxel di 1 mm (verificato sugli header di tutte e 5853: `182x218x182`). Una maschera già sulla griglia richiesta non viene ricampionata (`_needs_resample`), quindi il conteggio a 1 mm è nativo ed esatto. A 2 mm il ricampionamento è `nearest`: ogni voxel prende il valore di uno solo degli 8 sottostanti, quindi il volume a 2 mm è un sottocampionamento e **non** `volume nativo / 8` — una lesione di pochi voxel può ridursi o sparire, e 0 voxel a 2 mm non implica maschera vuota nel file originale. Le due colonne insieme distinguono i due casi.

`compute_lesion_metadata` in `src/features/lesion.py` è **streaming**, un soggetto per volta, e deliberatamente **non** passa per `_voxelwise_matrix_with_volume` come fa `build_lesion_matrix`. Quella funzione impila in memoria il volume appiattito di ogni soggetto: circa 5,3 GB sulla griglia a 2 mm (902.629 voxel × 5853 soggetti, uint8) e circa **42 GB** su quella a 1 mm, che non è eseguibile. Qui restano solo scalari per soggetto, quindi il picco è una maschera più le maschere per griglia — decine di MB, indipendenti da quanti soggetti ci sono. Chi in futuro volesse "riusare la funzione che c'è già" per aggiungere una griglia fine sbatterebbe esattamente lì.

Il costo che scala è il tempo, non la memoria: una lettura da disco per soggetto (la maschera è letta **una volta** e ricampionata una volta per griglia, non riletta per griglia) più un ricampionamento per griglia.

**La colonna a 1 mm è ridondante per 5 dataset su 8.** `manual_masks/` contiene la lesione già ricampionata da BCBToolKit su griglia 1 mm (`docs/guides/datasets.md`), e per i dataset segmentati originariamente a 2 mm i voxel risultano costanti in blocchi 2x2x2 allineati: il conteggio *grezzo* a 1 mm è esattamente `8 x` quello a 2 mm, e il conteggio a 2 mm **ricostruisce esattamente** la maschera nativa, quindi nessuna lesione può sparire. Sono 5150 soggetti su 5853 (UCL-UK, UKLFR, WashU, NEMESIS_T0, SFB936); le due colonne portano informazione diversa solo per i 534 di PASPORT e WAKEUP. **Le colonne del csv non sono il conteggio grezzo**: sono contate dopo l'azzeramento dei voxel fuori dal cervello, e ogni griglia ha la propria maschera cerebrale (`brain_mask_path` in `grids` di `compute_lesion_metadata.json`), quindi `lesion_volume_voxels_1mm == 8 x lesion_volume_voxels_2mm` vale esattamente solo per chi non ha voxel fuori dal brain (3501 su 3501 in questi 5 dataset). Per gli altri 1608 le due colonne differiscono di pochi voxel (differenza relativa mediana 0,2%, 95° percentile 2,3%, massima 12,8%): è un effetto di bordo dell'azzeramento, non una perdita di dettaglio.

**PSP: maschere frazionarie.** Le 168 maschere PSP sono a 2 mm e interpolate linearmente a 1 mm, quindi hanno valori multipli di 1/8 invece di solo 0/1 (negli altri 7 dataset sono binarie). `_binarize_on_grid` binarizza con `> binarize_threshold` (0,5): a 1 mm scarta i voxel che valgono esattamente 0,5 (circa il 23% di quelli di lesione), e `lesion_volume_voxels_1mm` risulta in mediana 0,83 volte il volume vero (da 0,34 a 0,94). A 2 mm `nearest` campiona proprio i voxel che valgono 0 o 1 e ricostruisce la maschera originale: la colonna a 2 mm è esatta. Le colonne a 1 mm di PSP non sono affidabili. Non è noto come BCBToolKit usi la stessa mappa frazionaria per calcolare la disconnessione (vedi `.claude/open_problems.md`). Verificato su tutti i soggetti, uniforme dentro ogni dataset - tabella e metodo in `docs/guides/datasets.md`. Il disegno a due griglie resta giustificato proprio da quei 534: 2 dei 4 soggetti con volume 0 sulla griglia di produzione stanno in WAKEUP e hanno una lesione reale di 8 e 3 voxel.

**Un soggetto per caso, stesso volume letto sulle due griglie** (voxel × 0,001 ml a 1 mm, × 0,008 ml a 2 mm):

| soggetto | griglia | voxel | ml |
|---|---|---|---|
| `sub-STUCLUK0729` (UCL-UK, maschera binaria) | 1 mm | 15976 | 15,976 |
| | 2 mm | 1997 | 15,976 |
| `sub-STUNIPD0252` (PSP, maschera frazionaria) | 1 mm | 10970 | 10,97 |
| | 2 mm | 1538 | 12,30 |

In UCL-UK le due griglie coincidono (1997 × 8 = 15976); in PSP il volume a 1 mm è 0,89 volte quello a 2 mm. Sui soggetti non PSP con più di 500 voxel a 2 mm il rapporto 1 mm / 2 mm ha mediana tra 0,998 e 1,000 in ogni dataset, in PSP 0,83.

### La soglia del lato

`side_threshold` (`0.20` in produzione) non è inventata: è calibrata contro 1445 soggetti con etichetta clinica vera, 97.4% di accordo, **sulla griglia a 2 mm** — dettagli, letteratura e limiti (la classe "bilaterale" resta debole, 3/24 corretti a qualunque soglia) in `knowledge/neuroimaging/lesion_laterality.md` e `.claude/history/methods_changelog.md`.

La stessa soglia vale anche a 1 mm: sugli stessi 1350 soggetti con lato clinico (PSP esclusa: le sue maschere a 1 mm sono frazionarie) la soglia 0.20 dà la stessa accuratezza a 1 mm e a 2 mm (97,3%) e attribuisce a **tutti** lo stesso lato. Il motivo per cui non era scontato: il piano mediano escluso da entrambi gli emisferi è spesso 1 mm su una griglia e 2 mm sull'altra (la griglia a 1 mm ha 91 fette a sinistra e 90 a destra, quella a 2 mm 45 e 45), quindi per una lesione quasi tutta mediana i due indici non sono interscambiabili.

Quello script ora legge `laterality_index_<grid>` dal csv e **non apre nessuna maschera**: ricalibrare su un'altra griglia è un cambio di `--grid`, non un secondo passaggio su 5853 maschere.

## `enrich_metadata`: il join

`lesion_metadata` (config, opzionale, `null` salta del tutto le colonne derivate dalle maschere) ha quattro chiavi:

| Chiave | Effetto |
|---|---|
| `path` | Il csv da cui copiare. |
| `copy_columns` | Colonne copiate **con lo stesso nome**, per ogni soggetto in scope, sovrascrivendo. Ogni nome deve esistere nel csv e non può essere una colonna di `populate_metadata.py`. |
| `lesion_side_from` | Quale colonna del csv riempie `lesion_side`: **solo dove la risoluzione clinica ha lasciato la cella vuota**, scrivendo anche `lesion_side_source = "geometric"`. `null` disattiva. Richiede `lesion_side` in `variables`. |
| `geometric_override_datasets` | Dataset dove un lato clinico `left`/`right` **opposto** a quello di `lesion_side_from` viene sostituito da quest'ultimo (`lesion_side_source = "geometric"`). L'unica eccezione a "un valore clinico non si sovrascrive". Obbligatoria; `[]` la disattiva ed è il valore in uso. |

Le due chiavi sono separate perché le regole di scrittura sono diverse, e la seconda scrive anche in una colonna ulteriore. Metterle nella stessa lista avrebbe richiesto che il codice conoscesse per nome la voce speciale — una regola implicita invece che dichiarata.

`lesion_side` nel registro resta **senza suffisso di griglia** anche se nel csv le colonne sono `lesion_side_1mm`/`lesion_side_2mm`: per i circa 1445 soggetti con etichetta clinica quel valore non viene da nessuna griglia, quindi un suffisso sarebbe falso per la maggioranza delle celle. `lesion_side_from` registra da quale griglia viene la parte geometrica; `lesion_side_source` dice, per ogni soggetto, quale delle due provenienze ha vinto. Le due fonti non entrano in conflitto perché la seconda scrive solo dove la prima non ha scritto nulla, con una sola eccezione dichiarata: `geometric_override_datasets` (sotto).

### `geometric_override_datasets`: perché è per dataset e per regola

La forzatura è una **regola per dataset**, non un elenco di ID. Un elenco di ID andrebbe rifatto a mano a ogni cambio delle maschere e non direbbe a un lettore perché quei soggetti; la regola (lato clinico `left`/`right` opposto a quello geometrico) si rilegge da `lesion_metadata.csv` a ogni run. È **per dataset** perché un default globale cambierebbe il registro su dati che nessuno ha guardato. Oggi è spenta (`[]`): i test indipendenti dal lato dicono che per WashU l'etichetta clinica è più spesso quella giusta. Motivazione, regola e verifica sono in `docs/guides/metadata.md`, sezione "Forzare il lato geometrico". Ogni soggetto forzato è un `WARNING` nel log: la forzatura contraddice il tsv di un dataset e non deve essere invisibile (come le sostituzioni di `VARIABLE_SOURCE_OVERRIDES`).

### Il join è stretto nei due sensi

| Situazione | Esito |
|---|---|
| soggetto in scope, `has_lesion=True`, nessuna riga nel csv | `ValueError` — il csv è vecchio |
| riga nel csv per un `subject_id` che il registro non conosce | `ValueError` — disaccordo su chi esiste |
| riga nel csv per un soggetto con `has_lesion=False` | `ValueError` — disaccordo su chi ha una maschera |
| soggetto con `has_lesion=False` e nessuna riga nel csv | caso normale |

Il primo controllo è limitato ai `datasets` della run (arricchire un sottoinsieme della coorte è legittimo); gli altri due sono globali, perché una riga che non corrisponde a nessuno è sbagliata indipendentemente da quali dataset questa run tocchi.

`main()` legge il registro tramite `src.utils.participants.load_participants_registry`, non con un `pd.read_csv(dtype=str)` grezzo: il join ha bisogno di `has_lesion` come booleano vero. Su una colonna di stringhe un `astype(bool)` mapperebbe `"False"` a `True` — qualunque stringa non vuota è vera — invertendo silenziosamente tutti e tre i controlli. `_check_agrees_with_registry` pretende quindi dtype booleano e solleva altrimenti, invece di convertire per conto proprio.

### Le colonne derivate dalle maschere non si correggono a mano

`fill: true` protegge una cella **clinica** corretta a mano; le colonne copiate da `lesion_metadata.csv` vengono sovrascritte a ogni run, quindi `_apply` le scrive con `fill=False` indipendentemente da `config.fill`. Onorare `fill: true` anche per quelle congelerebbe in silenzio un numero vecchio dopo che le maschere sono cambiate.

La conseguenza è deliberata: un volume o un lato inaffidabile ha la sua causa nella maschera, non nel registro. Si sistema la maschera e si ricalcola, oppure il soggetto va in `excluded_subjects.csv`. Un meccanismo per proteggere singole celle significherebbe due fonti di verità per lo stesso numero, senza nulla che dica quale vince.

## `excluded_subjects.csv`: chi entra in analisi

`subject_id, dataset, reason, scope, value`, generato da `src/pipeline/build_excluded_subjects.py` a partire dal config `config/pipelines/build_excluded_subjects.json`, dove ogni soggetto è elencato esplicitamente (nessuna soglia). Il modo usuale (`overwrite: false`) **aggiunge** al csv esistente senza toccarne le righe, quindi il csv è la fonte di verità e togliere una riga si fa a mano; con `overwrite: true` il csv è ricostruito dal solo config, che diventa allora la fonte. La modalità distruttiva è un flag esplicito, mai il comportamento di partenza: una pipeline che conosce solo alcune righe di un file condiviso non deve riscriverlo per intero senza che lo si sia chiesto. L'ultima cella di `notebooks/exploration/lesion_analysis.ipynb` non scrive nulla: stampa i blocchi da incollare nel config. Letto da `src/utils/participants.py::load_excluded_subjects`, e da lì da `build_lesion_matrix.py` e `build_sdc_matrix.py` tramite il campo `excluded_subjects_path` dei loro config — vedi `docs/dev/lesion_matrix.md`.

Nessuna pipeline lo genera: i dati non hanno un salto naturale su cui mettere una soglia (su 5853 soggetti, 3 maschere a 0 voxel a 2 mm, 132 con volume ≤ 10 voxel, coda continua; 234 soggetti sopra il 5% di frazione fuori dal brain, 73 sopra il 10%), e quale soggetto limite valga la pena di scartare è un giudizio che appartiene all'analisi.

`reason` ha un vocabolario chiuso in `KNOWN_EXCLUSION_REASONS` (`empty_mask`, `lesion_too_small`, `out_of_brain_fraction_too_high`, `all_zero_features`), pensato per crescere: aggiungerne uno è una voce lì più una riga in `docs/guides/metadata.md`. Chiuso e non libero perché la lista dei soggetti è scritta a mano nel config e un motivo con un typo diventerebbe in silenzio una categoria nuova che nessuno conta.

Un file **assente solleva**; con la sola intestazione è valido e significa "nessuna esclusione, deliberatamente". Le due cose non sono lo stesso fatto, e trattare un file mai scritto come "non escludere nessuno" produce esattamente la matrice di produzione con tutti i soggetti limite dentro che la lista esiste per evitare.

Ogni riga è validata contro il registro (ID inesistente, ID duplicato, `subject_id` vuoto, `dataset` in disaccordo, motivo non registrato, `value` non numerico sollevano): la pipeline deriva `dataset` e `value` da registro e `lesion_metadata.csv`, ma il validatore (lo stesso che gira sul file temporaneo prima della sostituzione) li controlla comunque: i dati ridondanti divergono, e il file letto dalle matrici può essere stato toccato fuori dalla pipeline.

I soggetti esclusi **restano** in `participants.csv` con `has_lesion`/`has_sdc` intatti e restano in `lesion_metadata.csv`: l'esclusione riguarda solo cosa entra in una matrice.
