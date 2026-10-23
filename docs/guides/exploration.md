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
| `metadata_raw` | cosa dicono i metadati clinici/demografici come arrivano dai dataset, prima della nostra normalizzazione? | i TSV `data/clinical_connectome/metadata_tsv/participants_*.tsv`, non `participants.csv` | solo `assets/metadata/columns_by_dataset.xlsx` (tabella colonna × dataset, versionata in git) |
| `lesion_analysis` | com'è fatta ogni maschera di lesione (volume, lateralità, fuori dal brain) e chi va escluso dalle matrici? | `assets/metadata/lesion_metadata.csv`, `participants.csv`; il file di una maschera a scelta da `derivatives/` (sezione "Lesion mask file exploring") | nulla (l'ultima cella stampa i blocchi da incollare nel config di `build_excluded_subjects`) |
| `sdc_analysis` | l'output SDC è valido e com'è fatta la matrice di disconnessione? | output SDC (`bcbtoolkit/`); costruisce la matrice in memoria | nulla |
| `fc_analysis` | quanto danneggia la lesione la FC e dove va la soglia di mascheramento? | FC pre-masking e output di `mask_fc.py`/`build_fc_matrix.py` | nulla |

**`lesion_analysis` e `excluded_subjects.csv`.** L'ultima cella è quella che *decide*, ma non scrive: per gli ID che le si danno (tre motivi: `empty_mask`, `lesion_too_small`, `out_of_brain_fraction_too_high`, scope `all`) stampa i blocchi da incollare in `exclusions` di `config/pipelines/build_excluded_subjects.json`. La pipeline `build_excluded_subjects` genera poi il csv. Tutto sopra è esplorazione. Formato, vocabolario dei motivi e validazioni in [`metadata.md`](metadata.md).

### `dataset_availability`

Vocabolario (dataset, tipologia di dato, pattern di file, assenza strutturale/sporadica): [`datasets.md`](datasets.md), sezione *Vocabolario*. Il notebook ha quattro parti:

1. **Dataset e tipologie.** Scopre i dataset (cartelle a profondità 2 sotto `derivatives/`) e, per ciascuno, le tipologie di dato (sue sottocartelle di primo livello). La tabella dataset × tipologia dice con `True`/`False` chi possiede cosa. Una tipologia è "presente" se la cartella esiste, anche se vuota.
2. **Tipologie di file per soggetto (controllo di consistenza).** Per ogni tipologia, l'insieme dei *pattern di file* attesi è l'unione dei pattern di tutti i soggetti di tutti i dataset che la possiedono; poi si verifica che ogni soggetto li abbia tutti. Un pattern è il percorso relativo alla cartella del soggetto, con l'ID del soggetto sostituito da `{subject_id}`. Il dettaglio si stampa solo se ci sono eccezioni, di due tipi:
   - **assenza strutturale** (`ℹ️`): il dataset non ha *nessun* soggetto con quel pattern, che esiste solo in altri dataset. Non è un errore: è la forma del dataset.
   - **assenza sporadica** (`⚠️`): il pattern c'è per altri soggetti dello stesso dataset ma manca a questo. È il caso da guardare: file perso in una copia, soggetto incompleto. Il notebook elenca i primi 10 soggetti e conta gli altri.
   - `✅` = tutti i soggetti del dataset hanno tutti i pattern attesi.
3. **Soggetti per dataset e tipologia.** Tabella dataset × tipologia con il numero di soggetti (una cartella soggetto = un soggetto) e riga `Totale`. Un controllo sui duplicati confronta il numero di cartelle con quello dei nomi distinti: è ridondante (un filesystem non ha due cartelle con lo stesso nome nella stessa cartella) ed è tenuto come garanzia. **WashU è mostrata già corretta**, divisa in due righe `UNIPD/WashU (ST)` e `UNIPD/WashU (HC)`: `features/` su disco è solo il campione locale ridotto, quindi il conteggio reale viene dal manifest `features/features_archive_subjects.tsv`, e il gruppo (ST/HC) di ogni soggetto viene da `disease_id` in `participants_WashU.tsv`. I controlli sani non hanno mai `manual_masks` né `bcbtoolkit` (nessuna lesione da segnare).
4. **Confronto a coppie.** `MOD_A` e `MOD_B` sono due tipologie (con il nome che hanno su disco, per esempio `manual_masks` e `bcbtoolkit`; `features` esiste solo per WashU). Per ogni dataset che le ha entrambe, la cella elenca i soggetti presenti in una e non nell'altra, nei due sensi; i dataset senza eccezioni non compaiono. Usa gli stessi dataset della parte 3, quindi WashU è già divisa in ST e HC (sottosezione *Correzione soggetti per WashU*, che si ferma con `ValueError` se un soggetto non ha `disease_id`).

**Parametri.** `OVERWRITE_FILE_TYPES_CACHE` (`False`: se `data/clinical_connectome/file_types_cache.json` esiste lo rilegge; `True`: riscandisce il filesystem e lo sovrascrive) e `MOD_A`/`MOD_B`.

**La cache.** Il controllo di consistenza attraversa ricorsivamente la cartella di ogni soggetto (migliaia di cartelle): per questo il risultato è salvato in `file_types_cache.json` (i pattern per tipologia e per soggetto) e riletto nelle esecuzioni successive. La cache non si invalida da sola: dopo aver aggiunto, tolto o ricopiato dati su disco va rigenerata con `OVERWRITE_FILE_TYPES_CACHE = True`.

**Cosa il controllo non vede.** Il controllo di consistenza lavora su ciò che c'è sul disco, quindi per `WashU/features` guarda solo i soggetti in chiaro (la correzione col manifest vale per i conteggi e per il confronto a coppie, non per i pattern di file).

### `metadata_raw`

Ogni sezione confronta tutti i dataset fianco a fianco, un subplot per dataset (griglia `dataset_grid`: più righe di tre colonne, subplot in eccesso nascosti).

**Quali TSV entrano.** Tutti i `participants_*.tsv` di `metadata_tsv/`, tranne quelli il cui schema non è ancora normalizzato: ne manca almeno una tra `disease_id`, `center_id`, `dataset`. È il caso di `participants_NEMESIS_T0.tsv`, che ha solo `participant_id`, `age`, `sex`, `group`, `participant_id_dmp`. Il notebook li esclude in modo esplicito e stampa quali colonne mancano, invece di lasciare le celle sotto rompersi con un `KeyError`. Un TSV nuovo entra da solo appena ha le tre colonne.

**Sezioni e come leggerle.**

- **Columns.** Numero di colonne per dataset, le colonne comuni a tutti e una tabella colonna × dataset (`True`/`False`) per le altre, ordinata da chi è condivisa da più dataset a chi è specifica di uno solo. La stessa tabella è esportata in `assets/metadata/columns_by_dataset.xlsx` (foglio `colonne`, una colonna per dataset, `X` verde = presente, cella grigia = assente; intestazioni in grassetto, prima riga e prima colonna bloccate). Il file è versionato perché è un artefatto condiviso, non di lavoro; ogni esecuzione lo riscrive.
- **Integrità del dato.** Per dataset, le colonne con più valori mancanti (massimo 15, barre più lunghe = più mancanti); "nessun missing" se non ce ne sono.
- **Sani vs malati.** Conteggio dei soggetti per `disease_id` in ogni dataset.
- **Analisi demografica.** Istogramma dell'età con curva di densità (colorato per `disease_id` solo se il dataset ha più di un gruppo) e conteggio per sesso; se la colonna `sex` non c'è, il subplot lo dice.
- **Test clinici e comportamentali.** Le colonne clinico/comportamentali sono rilevate da una regola, non da una lista per dataset: sono le colonne che (1) **non** sono nell'insieme `NON_CLINICAL_COLUMNS` (identificativi, demografia, date, lato e tipo di lesione, esami di laboratorio, farmaci, comorbilità) e (2) hanno almeno un valore numerico (`pd.to_numeric(..., errors="coerce")`: il testo diventa mancante). Per ognuna la barra è la **percentuale di soggetti del tsv con un valore valido** (numerico non mancante), da 0 a 100; si mostrano le 20 con copertura più alta, e il titolo dice `top 20/N` quando ce ne sono di più. Una colonna nuova che non è clinica (un ID, una data) e finisce nel grafico si esclude aggiungendola a `NON_CLINICAL_COLUMNS`. La percentuale è sulle righe dell'intero tsv, controlli sani compresi.
- **Gravità clinica (NIHSS).** Istogramma della colonna `NIHSS` grezza, sui soli `ST` se il dataset ha più gruppi. Nessun proxy: dove la colonna manca il subplot dice "NIHSS non disponibile" (PASPORT e UCL), e il proxy di produzione (`NIHSS_at_presentation` per PASPORT, in `enrich_metadata.py`) qui non si applica di proposito.
- **Matrice di correlazione.** Correlazione di Pearson, per dataset, tra `age`, `education` (se esistono) e le colonne cliniche rilevate sopra; triangolo inferiore, scala da -1 a +1. Ogni matrice ha le sue variabili (titolo: `n var`). Si tengono le colonne con almeno due valori validi; la correlazione di ogni coppia usa i soli soggetti che hanno entrambi i valori; con meno di due variabili il subplot dice "dati insufficienti".

### `sdc_analysis`

Lavora su un sottoinsieme di dataset, scelto in `DATASETS` (sezioni 1-5, output parcellato) e `DATASETS_ALL` (sezione 6, mappe voxel-wise). Dà per fatto che l'SDC sia stato calcolato a monte: controlla che l'output sia valido, non lo produce.

**Parametri che si modificano:** `DATA_ROOT`, `DATASETS`, `TARGET_ATLAS` (l'atlante di cui si costruisce la matrice in memoria; di default `schaefer_200_tian_s2`), le liste `ATLASES_DISCONNECTOME` (15) e `ATLASES_LESION` (le stesse 15 più `yeh_hcp1065_streamline`, 16), `DATASETS_ALL`, `REFERENCE_DATASET`, `N_SAMPLE` (soggetti per dataset nei controlli voxel-wise) e `KNOWN_ATLAS_SIZES` (dizionario vuoto da compilare a mano).

**Sezioni e come leggerle.** Ogni controllo che fallisce solleva `ValueError`, non stampa un avviso.

1. **Validazione strutturale.** Ogni soggetto di `bcbtoolkit/` deve avere esattamente 15 CSV `LF-disconnectome` e 16 `LF-lesion` (31). Si confronta l'**insieme dei nomi** attesi, non solo il conteggio: 31 file con un atlante sbagliato o duplicato passerebbero un controllo sul numero. In `bcbtoolkit/` ogni voce deve essere una cartella `sub-*`; qualunque altra cosa ferma la cella. I CSV stanno direttamente nella cartella del soggetto, senza sottocartella intermedia.
2. **Cross-check con il registro.** Per ogni dataset, i soggetti in `bcbtoolkit/` e quelli con `has_sdc` in `participants.csv` devono coincidere nei due sensi; se no il registro è vecchio e va rilanciato `populate_metadata.py`. Poi conta quanti soggetti ammetterebbe `build_sdc_matrix.py` per quel dataset: servono `has_sdc` **e** `has_lesion`. Il conto non applica `excluded_subjects.csv` né `group_filter`, quindi è il massimo ammissibile, non il numero esatto di righe di una matrice.
3. **EDA e costruzione della matrice.** Un CSV di esempio ispezionato (shape, NaN, regioni duplicate), poi la lista maestra delle regioni (unione dei `region_name` osservati) e la matrice soggetti × regioni con `reindex` sul nome della regione (mai sulla posizione della riga). BCBToolKit omette le regioni a sovrapposizione nulla invece di scriverle a 0: il notebook lo verifica sui dati (nessuna riga con `mean_overlap == 0` scritta esplicitamente; se ce n'è una solleva) prima di riempire i mancanti con 0. La lista maestra osservata è solo un limite inferiore delle regioni dell'atlante (una regione mai disconnessa in nessun soggetto non compare); la lista autoritativa usata in produzione è `assets/atlases/sdc_labels/<atlas>.csv` ([`sdc_matrix.md`](../dev/sdc_matrix.md)). Un CSV senza righe è un caso valido: il soggetto ha disconnessione nulla ovunque (vettore di zeri).
4. **Sanity check.** Sulla matrice: nessun valore fuori da [0, 1], nessun NaN (se no solleva), e il **conteggio** delle regioni con varianza zero. Quest'ultimo è un controllo da leggere, non una garanzia né un errore: la matrice di produzione `parcellated` può avere colonne costanti perché non scarta mai nessuna colonna ([`sdc_matrix.md`](../dev/sdc_matrix.md)).
5. **EDA approfondita.** Metriche per soggetto sul valore `mean_overlap` dell'atlante scelto:
   - `n_regions_hit`: numero di regioni con valore > 0 (senza soglia: basta una traccia). È l'ampiezza topologica; il grafico a sinistra è la sua densità per dataset.
   - `disco_load`: somma dei valori su tutte le regioni, cioè il carico di disconnessione parcellato.
   - Tabella per dataset: numero di soggetti, `Mediana_Regioni` (mediana di `n_regions_hit`), `Soggetti_Intatti_Perc` (% di soggetti con `n_regions_hit == 0`, cioè nessuna regione colpita), `Carico_Medio` e `Carico_Max` (media e massimo di `disco_load`).
   - Frequenza regionale: per ogni regione, la % di soggetti con valore > 0; le 10 con frequenza più alta sono le più "vulnerabili", cioè quelle colpite più spesso.
   - `asymmetry_index = load_left - load_right`: somma dei valori delle regioni dell'emisfero sinistro meno quella delle destre. Positivo = più disconnessione a sinistra, negativo = a destra, 0 (linea rossa del boxplot) = simmetrico. È una differenza assoluta, non normalizzata sul carico totale: a parità di asimmetria relativa, un soggetto con più carico ha un indice più grande. Le regioni sono assegnate a un emisfero cercando `lh`/`rh` nel nome (senza distinzione tra maiuscole e minuscole): per `schaefer_200_tian_s2` ogni regione cade in un emisfero, per un altro atlante va verificato che i nomi seguano la stessa convenzione.
6. **Validazione voxel-wise.** Controlla le mappe `*_res-1_desc-disconnectome.nii.gz` (volume prima della parcellazione) con lo stesso approccio di `build_lesion_matrix.py`/`build_sdc_voxelwise_matrix` (`resample_to_img`). **Guarda solo un campione**: `N_SAMPLE` soggetti per dataset (i primi in ordine di id), non l'intera coorte. Tre passi: (a) forma e affine di un soggetto per dataset contro `REFERENCE_DATASET`, con `needs_resample` vero dove differiscono (stesso criterio di `_needs_resample`: shape **e** affine); (b) intervallo dei valori in [0, 1] e assenza di NaN sul campione, dati nativi; (c) prova di ricampionamento `nearest` di una mappa con affine diversa (PASPORT) sulla griglia della reference, che deve mantenere la shape attesa, non introdurre NaN e restare in [0, 1] senza tolleranza (`nearest` copia il valore del voxel sorgente più vicino, nessuna aritmetica). La reference qui è la griglia a 1 mm delle mappe di `REFERENCE_DATASET`; la griglia di produzione (template a 2 mm) è un'altra, quindi il passo (c) verifica il meccanismo, non la griglia finale.

### `lesion_analysis`

Legge `assets/metadata/lesion_metadata.csv` (misure per griglia) unito a `participants.csv` (solo `lesion_side` e `lesion_side_source`), e ha una sezione che apre il file di una maschera. Il volume si converte in millilitri (1 ml = 1000 mm³: un voxel vale 0,001 ml a 1 mm, 0,008 ml a 2 mm). Le due griglie e perché PSP è esclusa dalle viste a 1 mm: [`datasets.md`](datasets.md) e [`metadata.md`](metadata.md).

**Parametri che si modificano.**

| Parametro | Dove | Cosa fa |
| :--- | :--- | :--- |
| `DATASET` + `SUBJECT_INDEX`, oppure `SUBJECT_ID` | *Lesion mask file exploring* | sceglie la maschera: dataset e posizione nel dataset (0 = il primo, in ordine di id), oppure un id preciso. `SUBJECT_ID` ha la precedenza se impostato |
| `SLICE_AXIS` | idem | asse di taglio: `"x"`, `"y"` o `"z"` (indici 0, 1, 2 dell'array) |
| `SLICE_INDEX` | idem | indice voxel della slice; `None` = la slice con più voxel non nulli |
| `MAX_SIDE` | idem | lato massimo (in voxel) della matrice mostrata; oltre, si vede solo il centro e il notebook avvisa |
| `VOLUME_GRID` | *Volume* | `"1mm"` o `"2mm"`: griglia di tutte le viste di volume (quadro numerico, distribuzione, confronto). A 1 mm PSP esce |
| `LARGE_QUANTILE` | *Quadro numerico* | quantile sopra cui una lesione è "grande" (0,75) |
| `MAX_ML` | *Lesioni piccole* | soglie "al più X ml", uguali per le due griglie |
| `OUT_OF_BRAIN_COLUMN` | *Lesione fuori dal brain* | colonna della frazione (`out_of_brain_fraction_2mm`; cambiandola si guarda un'altra griglia) |
| `EXCLUSIONS` | *I soggetti esclusi* | gli ID da escludere, per motivo |

Le soglie candidate della frazione fuori dal brain sono una lista fissa scritta in due celle (la conta e l'elenco degli ID): per cambiarle si modificano entrambe.

**Lesion mask file exploring.** Ispeziona **una** maschera così com'è sul disco, senza binarizzare né ricampionare. La prima cella mostra l'header, i **valori non nulli** presenti con il loro numero di voxel (una maschera binaria ne ha uno solo, `1`; se ce ne sono altri la maschera è frazionaria, come in PSP) e i confini della lesione, in indici voxel e in mm. La seconda mostra una slice come **matrice**: celle rosse = voxel non nulli, grigie = zeri. Gli indici sono **voxel**, non millimetri; le colonne in mm della tabella dei confini sono nello spazio MNI. Una maschera vuota o una slice tutta a zero fa sollevare un errore alla seconda cella.

**Volume.**

- **Quadro numerico.** Una riga per dataset e una per l'intera coorte. `min` e `max` sono i valori estremi (un solo soggetto ciascuno); `pNN` è il volume sotto cui sta il NN% dei soggetti, con `p50` = mediana, quindi i percentili descrivono una distribuzione asimmetrica meglio di `mean` e `std`. La tabella include le maschere a 0 ml (a differenza dei grafici in scala log). L'ultima colonna è la quota di ciascun dataset che supera la soglia di "lesione grande": `LARGE_QUANTILE` è un quantile del volume calcolato su **tutta** la coorte, con 0,75 "grande" vuol dire nel 25% più grande, e la soglia in ml è scritta nel nome della colonna. Se i dataset fossero omogenei la quota sarebbe circa 25% ovunque: una quota molto diversa da 25% segnala un dataset con lesioni sistematicamente più grandi (sopra) o più piccole (sotto).
- **Distribuzione per dataset.** Due viste dello stesso volume, un subplot per dataset con `n=` nel titolo. La **scala logaritmica** mostra la forma della distribuzione: i volumi coprono più ordini di grandezza e su scala lineare la maggior parte dei soggetti si schiaccia a sinistra. Lo 0 non esiste su un asse log, quindi le maschere a 0 ml non compaiono e `n` conta solo i soggetti rappresentati (le vuote hanno la loro sezione). La **scala lineare** mostra invece la coda lunga e le dimensioni assolute: quante lesioni sono davvero grandi e quanto. La prima dice com'è fatta la maggior parte dei soggetti, la seconda quanto pesa la coda.
- **Confronto tra dataset** (log, vuote escluse). Il **boxplot** mostra mediana, quartili e outlier di ciascun dataset. L'**ECDF** dà, per ogni volume `x`, la quota di soggetti con volume ≤ `x`: una curva più a destra indica lesioni più grandi, e dove la curva incrocia 0,9 si legge il `p90` del dataset.
- **Maschere vuote** (volume 0), contate su **entrambe le griglie**: vuota già a 1 mm = nessun voxel nel file originale, vuota davvero; vuota a 2 mm ma non a 1 mm = la lesione c'era ed è sparita nel ricampionamento `nearest` (un voxel su 8). Sono i casi più netti da escludere. PSP non è inclusa su nessuna delle due griglie.
- **Lesioni piccole: quante e quanto.** Nessuna soglia di dimensione viene applicata alle matrici: la tabella serve a capire quante lesioni sono piccole. Per ogni soglia di `MAX_ML` (con il numero di voxel equivalente a quella griglia) mostra la **quota dei soggetti di ciascun dataset** con una lesione non più grande di così, escluse le maschere vuote; `n soggetti` è il numero totale di soggetti sotto la soglia. È **cumulativa**: la riga 0,8 ml include anche le righe sopra. Si usa la quota e non il conteggio perché i dataset hanno dimensioni molto diverse; le soglie sono in ml (non in voxel) perché i voxel a 1 e a 2 mm hanno volumi diversi, quindi le due tabelle (una per griglia) sono confrontabili. Le due tabelle praticamente coincidono per i dataset con maschere su reticolo 2 mm e differiscono per quelli a 1 mm genuino (PASPORT, WAKEUP), dove `nearest` a 2 mm tiene un voxel su 8 e il volume può salire o scendere.

**Lateralità.** Il lato (`left`/`right`/`both`) serve a colorare per lato i plot degli embedding (color mode `side`) e a descrivere i cluster (quanti soggetti di ciascun lato contengono); le due fonti (`clinical`, `geometric`) e la regola `both` sono in [`metadata.md`](metadata.md). Il grafico a barre conta, per dataset, i soggetti per `lesion_side` del registro (clinico e geometrico insieme, senza distinguere la fonte); i soggetti senza valore (né dato clinico né indice calcolabile) sono contati nel titolo del subplot.

*Il lato cambia tra le due griglie?* La domanda è se lo stesso soggetto riceve lo stesso `lesion_side` con l'indice $LI$ a 1 mm e a 2 mm. Può cambiare perché il piano mediano MNI non appartiene a nessun emisfero ed è spesso di 1 mm su una griglia e di 2 mm sull'altra (per una lesione quasi tutta mediana i due indici non sono interscambiabili), e perché `side_threshold` è calibrata a 2 mm e a 1 mm applicata uguale. La cella lavora sui soggetti con un lato attribuibile su **entrambe** le griglie (PSP esclusa) e: conta quanti cambiano lato; mostra la correlazione tra i due indici; mostra la tabella di confusione (righe = lato a 1 mm, colonne = lato a 2 mm; fuori diagonale = soggetti che cambiano); confronta il volume dei soggetti in disaccordo con quello di tutti; elenca gli ID in disaccordo dal volume più piccolo. Come leggerla:

- **Pochi disaccordi, concentrati nelle lesioni piccole, e indici molto correlati**: la risoluzione non cambia l'attribuzione del lato e la soglia calibrata a 2 mm vale anche a 1 mm.
- **Molti disaccordi, o sparsi anche tra le lesioni grandi**: la soglia non si trasferisce e va ricalibrata con `python -m src.pipeline.calibrate_lesion_side_threshold --grid 1mm`.
- **`both` è la classe più instabile**, perché è quella che dipende dalla soglia.

**Lesione fuori dal brain.** I voxel fuori dal cervello si trattano in due modi che si combinano. La **correzione** li azzera e il soggetto resta nella matrice con una maschera pulita: è il comportamento di default. L'**esclusione** riguarda i casi che la correzione non salva: se la frazione fuori è troppo alta c'è probabilmente un errore grave di segmentazione o normalizzazione, non rumore ai bordi, e il soggetto va segnalato. L'istogramma mostra la percentuale di voxel di lesione fuori dal brain per dataset; i soggetti con maschera vuota non hanno una frazione (`NaN`) e non compaiono (sono trattati come maschere vuote). Convenzioni e criteri adottati: [`metadata.md`](metadata.md), sezione *Criteri adottati*.

La cella delle **soglie candidate** non è un test statistico: le soglie (1, 5, 10, 30, 50, 70%) sono valori fissi e per ognuna si legge quanti soggetti la superano, sul totale, e in quali dataset. La cella degli **ID sopra soglia** li elenca per ogni soglia, per frazione decrescente, con dataset e percentuale: serve ad aprire le maschere una a una e giudicare a occhio se è un errore di normalizzazione.

**I soggetti esclusi.** `EXCLUSIONS` ha come chiavi i tre motivi (`empty_mask`, `lesion_too_small`, `out_of_brain_fraction_too_high`) e come valori le liste di ID; `SCOPE` è `all`. Gli ID ripetuti sotto motivi diversi o assenti da `lesion_metadata.csv` fermano la cella. Per ogni blocco la cella stampa `value_column`, cioè la colonna di `lesion_metadata.csv` da cui la pipeline legge il `value`: `lesion_volume_voxels_1mm` per `empty_mask` (il conteggio nativo, 0 = vuota davvero), `lesion_volume_voxels_2mm` per `lesion_too_small` (la griglia che entra nella matrice), `OUT_OF_BRAIN_COLUMN` per `out_of_brain_fraction_too_high`. **Con `EXCLUSIONS` vuoto la cella non stampa nessun blocco, solo il messaggio «Nessun ID in EXCLUSIONS: nessun blocco da stampare.».** I motivi che la cella non copre (per esempio `all_zero_features`) si scrivono direttamente nel config.

### `fc_analysis`

Lavora solo su WashU, atlante `Yan200TianS2Buckner7N` (239 nodi). Non scrive nulla. Sezioni:

1. **FC pre-masking.** Una matrice grezza di esempio 239×239 con la heatmap; controlli di struttura: diagonale = 1, simmetria.
2. **FC mascherata, caricamento.** Legge `mask_summary.csv`: per ogni paziente, quanti nodi (parcelle) hanno meno del 50% di tessuto sano.
3. **Distribuzione e percentili.** Istogramma in valore assoluto e in % della rete. Una massa di pazienti puliti con una coda significa che una soglia taglia solo la coda. Il percentile p*P* è il valore sotto cui sta il *P*% dei pazienti: serve a capire quanto in profondità nella coda si entrerebbe, non a decidere se tagliare una massa.
4. **Analisi delle soglie.** Curva dei pazienti esclusi in funzione della soglia e tabella delle candidate (`soglia_nodi`, `soglia_%_rete`, `pazienti_esclusi`, `pazienti_rimasti`). Le candidate sono ipotesi, non scelte. Più si alza la soglia, meno pazienti si escludono; i salti non sono costanti, e dove la curva si appiattisce si è nella coda rara.
5. **Dai nodi compromessi alle connessioni perse.** Un nodo compromesso rende NaN fino a 238 connessioni su 28.441; le connessioni condivise contano una volta. Scatter nodi compromessi (proxy) contro % NaN della matrice finale (esatta), uniti per `subject_id`, e classifica dei primi 10 candidati all'esclusione.

I parametri da modificare sono `DATA_ROOT`, `atlas_combo`, `n_total_nodes`, il percorso della matrice di `fc_matrix` e la lista `candidate_thresholds`. `mask_summary.csv` e la matrice devono venire dalla stessa run di `mask_fc.py`. Le regole di lettura sono in [`fc_lesion_masking.md`](../../knowledge/notes/neuroimaging/fc_lesion_masking.md), sezione *Scegliere una soglia di esclusione paziente*; la decisione presa (nessuna soglia) è in [`fc_matrix.md`](../dev/fc_matrix.md).

---

## `notebooks/pipeline_building/`

| Notebook | Prototipo di |
|---|---|
| `lesion_matrix_build` | `src/pipeline/build_lesion_matrix.py`: maschere → griglia comune → matrice soggetti × voxel, sanity check, riduzione ai voxel non costanti, frequenza voxel-wise. Non scrive l'artefatto: legge quello già prodotto dalla cache |
| `fc_lesion_masking` | `src/pipeline/mask_fc.py`/`build_fc_matrix.py`: mascheramento della FC in funzione della lesione (scrive CSV mascherati e di matrice) |
| `dim_reduction` | tuning rapido degli iperparametri di UMAP/t-SNE su una matrice già costruita: sweep, griglie di embedding, guadagno marginale su `n_components` |
| `thiebaut_2020_replication` | replica della PCA varimax di Thiebaut de Schotten et al. 2020 sul disconnettoma voxelwise `s2.4-vol`: quante componenti per il 50/80/90% della varianza, e quanto ogni componente dipende dal volume della lesione, e le mappe delle componenti nel cervello con la loro riproducibilità tra due metà dei soggetti (le componenti da disegnare si scelgono a mano, `COMPONENTS_TO_PLOT`). Legge `matrix.npy`/`metadata.csv` e `participants.csv`; scrive solo una cache in `results/pipeline_building/thiebaut_2020_replication/<sessione>/` (`USE_CACHE`; una cache che viene da un'altra matrice ferma il notebook con `ValueError`). Il calcolo è in `src/analysis/covariance_pca.py` ([`covariance_pca.md`](../dev/covariance_pca.md)) |

### `lesion_matrix_build`

Prototipo del costruttore (produzione: `src/pipeline/build_lesion_matrix.py`, guida [`matrix_building.md`](matrix_building.md)). Sezioni:

1. **Lesions Loading.** Una maschera per cartella soggetto, conteggio per dataset.
2. **Allineamento e costruzione di X.** Ricampiona su una griglia comune, ribinarizza, impila `X` e `metadata` con lo stesso ordine di riga.
3. **Fast loading.** Ricostruisce la `X` completa dalla cache con `X[:, non_constant] = X_reduced`.
4. **Sanity check.** Valori {0,1}, nessun NaN, nessun soggetto con somma zero.
5. **Riduzione.** Scarta i voxel mai lesionati.
6. **Visualizzazione.** Tabella e heatmap dei voxel più frequenti, perché la matrice è sparsa.
7. **Frequenza voxel-wise.** Overlap lesionale globale; il "core" è il 10% della coorte, scelta del notebook.

I parametri da modificare sono `DATA_ROOT`, `DATASETS`, `LESION_GLOB`, `CACHE_DIR` e `LOAD_DIR`. Le regole di lettura sono in [`matrix_building.md`](matrix_building.md), sezione *Come leggere la matrice*.

### `fc_lesion_masking`

Prototipo passo-passo su 3 pazienti WashU, uno per volta: setup dell'atlante, step 1-8 (il ruolo di `mask_fc.py`), step 9-12 (il ruolo di `build_fc_matrix.py`). Si esegue per capire ogni passo prima di leggere il codice. La teoria e l'esempio numerico sono in [`fc_lesion_masking.md`](../../knowledge/notes/neuroimaging/fc_lesion_masking.md). I parametri da modificare sono `SUBJECTS`, `ATLAS_COMBO`, `MIN_COVERAGE` (0,5) e `DEMO_OUTPUT_NAME`; scrive in una cartella `demo`, distinta dalla run reale.

### `dim_reduction`

Fissa i parametri di `nested_params` del registry (`metric` per t-SNE; `metric` e `n_components` per UMAP) e fa variare gli altri parametri della `tuning_grid`, come in produzione. I parametri da modificare sono `input_matrix_dir`, `reduction_method` e `fixed_metric` (più `tuning_session` per l'ultima sezione). Produce una tabella ordinata per trustworthiness e la griglia di subplot degli embedding, da ispezionare a occhio. L'ultima sezione legge un `tuning_results.csv` già su disco e mostra il guadagno marginale di trustworthiness tra `n_components` consecutivi: si legge la pendenza, non il valore assoluto, e vale solo per UMAP (t-SNE resta a 2 componenti). Le regole di lettura sono in [`dim_reduction_tuning_guide.md`](../../knowledge/notes/dim_reduction_clustering/dim_reduction_tuning_guide.md).

---

## `notebooks/post-results_analysis/`

Leggono run già **prodotte**: di clustering (due notebook di analisi, una run o più run, più l'esplorazione di un tuning) e di PCA (`pca_evaluation`). Per il clustering un criterio separa le analisi: se usano dati *interni* al clustering o dati *esterni* a esso.

- **Empirica**: usa solo le etichette e lo spazio su cui la run è stata costruita (embedding o matrice). Risponde a "com'è fatta e quanto è affidabile questa partizione, quanto si accorda con un'altra".
- **Interpretativa**: porta variabili o immagini che il clustering non ha visto (cliniche, demografiche, mappe anatomiche). Risponde a "cosa rappresentano questi cluster". Vive nell'app Dash (mappe, soggetti rappresentativi, composizione dei cluster); nei notebook le parti interpretative sono la sezione 4 di `clustering_evaluation`, che descrive i cluster con le variabili cliniche e non fa nessun test, `dendrogram_embedding_explorer`, che mostra le mappe anatomiche dei due cluster nati da ogni divisione dell'albero, e le parti 2 (profilo clinico/demografico) e 4 (due cluster della stessa run) di `clustering_comparison`.

| Notebook | Scope | Domanda | Legge | Scrive |
|---|---|---|---|---|
| `clustering_evaluation` | empirica, **una** run | quanto è buona questa run? (metriche geometriche e del modello, confidenza di appartenenza) e come sono distribuite le variabili cliniche nei suoi cluster (sezione 4, solo descrittiva, nessun test) | la run (`matrix.npy`, `metadata.csv`, `config.md`), `participants.csv` per la sezione 4 | nulla |
| `clustering_comparison` | empirica, **più** run (le parti 2 e 4 portano anche variabili esterne) | in cosa differiscono queste run? (accordo tra partizioni, corrispondenza dei cluster, confronto cross-modalità lesion/sdc sull'intersezione dei soggetti con il profilo clinico/demografico dei cluster, distanze tra cluster nell'embedding, confronto di due cluster della stessa run con dati clinici e mappa di differenza) | le run scelte, `participants.csv` (profilo clinico e parte 4), i file delle lesioni (mappa di differenza della parte 4) | nulla |
| `dendrogram_embedding_explorer` | interpretativa, **una** run di tuning agglomerative | passando da k-1 a k cluster quale cluster si divide, dove stanno i due pezzi nell'embedding e che anatomia hanno (sovrapposizione delle lesioni o disconnessione, a scelta con `MAP_MODALITY`)? | la run di tuning (`config.md`, `metadata.csv`, `clusterings.npz`), l'embedding 2D di `input_path`, i file dei soggetti su disco | nulla (cache delle mappe condivisa con l'app, `results/cache/binary_masks`) |
| `pca_evaluation` | valutazione di **una** PCA, di produzione o di tuning (una combinazione) | quante componenti tenere (varianza cumulata), quanta varianza spiega ogni componente ruotata, quanto dipende ciascuna dal volume e dal lato della lesione, dove sta nel cervello (mappe *t* e riproducibilità tra metà), come separa i soggetti (embedding) | la run (`matrix.npy`/`embeddings.npz`, `eigenvalues.npy`/`.npz`, `metadata.csv`, `config.md`), la matrice su cui la PCA è stata calcolata (sezioni 4 e 6), `participants.csv` | solo la cache delle mappe in `results/cache/component_maps`, la stessa dell'app |

**`pca_evaluation`: sezioni e parametri.** Il notebook non sceglie il numero di componenti: mostra i dati per sceglierlo. Una sezione che non si applica alla run scelta lo dice e salta.

| Sezione | Contenuto | Si applica a |
|---|---|---|
| 1 | Scelta della run e dei parametri | tutte |
| 2 | Cosa contiene la run | tutte |
| 3 | Quante componenti tenere | tutte |
| 4 | Varimax: varianza di ogni componente ruotata | run ruotate |
| 5 | Dipendenza dal volume (e dal lato) della lesione | tutte |
| 6 | Component maps nel cervello | matrici voxelwise |
| 7 | Embedding | tutte |

I parametri da modificare sono `RUN_PATH` (cartella della run, di produzione o di tuning); `ROTATION` e `N_COMPONENTS` (solo per un tuning: quale combinazione valutare); `COMPARE_WITH_UNROTATED` (tuning con varimax: la sezione 5 confronta anche la stessa combinazione senza rotazione, che il tuning deve contenere); `UNROTATED_RUN_PATH` (run di produzione con varimax: la run senza rotazione degli stessi soggetti, oppure `None`); `LESION_VOLUME_COLUMN` (volume in voxel a 2 mm); `COMPONENTS_TO_PLOT` e `MAP_THRESHOLD_FRACTION` (mappe); `EMBEDDING_COMPONENTS` (le due componenti, numerate da 1; `None` le sceglie da solo). Il dettaglio di lettura delle sezioni è in [`covariance_pca.md`](../dev/covariance_pca.md), *Evaluating a PCA run*.

**`dendrogram_embedding_explorer`.** Segue l'agglomerative k dopo k su un tuning già eseguito: per ogni k un cluster si divide in due, e il notebook mostra albero ed embedding (un colore per cluster) e la mappa anatomica dei due figli. Non rifà nessun tuning: ricalcola solo l'albero sull'embedding 2D e verifica che coincida con le etichette salvate (ARI = 1, altrimenti si ferma). Parametri e lettura: [`evaluate_clustering_tuning.md`](evaluate_clustering_tuning.md).

Guida di evaluation e comparison, e dove vive ogni analisi: [`evaluation.md`](evaluation.md).

---

## Regole di scrittura dei notebook

- **Apertura**: il titolo sta da solo nella sua cella (ogni intestazione sta sola in una cella di markdown); la **prima cella sotto il titolo** dice la domanda, cosa legge, cosa scrive, e cosa *non* fa (rimandando al notebook che lo fa).
- **Titoli**: `#` solo per il titolo, `##` per le sezioni, `###` e oltre per le sottosezioni.
- **Niente duplicati tra notebook**: una stessa analisi (per esempio la distribuzione del volume) vive in un solo notebook. Se ne serve il risultato altrove, si legge il file che la contiene.
- Un notebook che diventa codice di produzione resta come prototipo in `pipeline_building/`, con il rimando alla pipeline nella prima cella sotto il titolo.
- **Il markdown di un notebook non è mai una fonte di informazione nuova**: tutto ciò che dice è scritto anche in `docs/` e/o in `knowledge/notes/`, e il notebook lo ripete. Gli output delle celle sono un'altra cosa: l'utente decide quando aggiornare i documenti con ciò che mostrano.
