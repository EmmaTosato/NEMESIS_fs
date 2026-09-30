# Changelog dei metodi

Decisioni su **come analizziamo**: proxy per variabili mancanti, feature calcolate, soglie, metodi adottati o abbandonati — con le alternative scartate e il perché.

**Cosa NON va qui**: i risultati di un esperimento (`docs/experiments/`), i parametri di una singola run (`runs.csv`), il funzionamento corrente di una pipeline (`docs/`, sempre al presente).

Voci in ordine cronologico inverso.

---

## 30-09-26 — Cache condivisa e ricampionamento single-pass per le mappe anatomiche in Embedding Explorer

**Decisione**: `BinaryMaskStore` (`src/analysis/anatomical_maps.py`) passa da precalcolo per-singola-run a cache in-memoria condivisa fra tutti i run/cluster aperti nella stessa sessione app: per ogni soggetto tiene solo gli indici dei voxel sopra soglia (lesione, o disconnessione >0.5), riempiti una sola volta per soggetto indipendentemente da quanti run/cluster lo richiedono. `_GridResampler`, stessa classe, calcola una sola volta la corrispondenza voxel→voxel fra griglia sorgente e reference (invece che per ogni soggetto) — bit-identico a `resample_to_img`, verificato con test dedicato. Nuovo flag `--preload` in `src/pipeline/embedding_app.py`: all'avvio, in background, legge tutti i soggetti di tutti i run di clustering (maschere lesionali sempre, disconnettomi SDC solo per i run sdc) e riempie i due store una volta per l'intera sessione. Inoltre, `_masked_for_view_colorbar` (`src/analysis/embedding_app.py`) rimuove il grigio dalla colorbar interattiva della mappa "probabilità media": pre-azzera i voxel sotto soglia (0.02) e passa un epsilon a `view_img` invece della soglia reale.

**Perché**: con un precalcolo per-singola-run, ogni cluster di ogni run ripeteva il ricampionamento e il filtraggio per voxel per gli stessi soggetti già visti in run precedenti nella stessa sessione — costo che cresce con il numero di run aperti, non con il numero di soggetti distinti. Condividere la cache per soggetto (indipendente dal run) elimina il lavoro ripetuto: con `--preload`, qualunque cluster di qualunque run mostra la mappa in ~1s. Sul colorbar: `view_img` di nilearn colora di grigio opaco tutto l'intervallo sotto soglia quando gli si passa la soglia reale, e questo comportamento non è configurabile dai suoi parametri pubblici — pre-azzerare a monte e passare un epsilon aggira il problema senza patch a nilearn.

**Alternative scartate**: mantenere il precalcolo per-run e limitarsi a velocizzare il ricampionamento (`_GridResampler` da solo) — avrebbe comunque ripetuto il lavoro per ogni run sullo stesso soggetto, non risolvendo il caso reale (più run aperti in una sessione lunga).

**Conseguenza ancora vera oggi**: i due store (`BinaryMaskStore` per lesioni e per disconnettomi SDC) vivono per la durata del processo `embedding_app`, non per singola run — un riavvio dell'app senza `--preload` torna al comportamento lazy (primo accesso più lento, poi cache calda per quel soggetto). Bug noto e non corretto: il download PNG statico della mappa di disconnessione (`_download_disconnection_png`) usa sempre `_DISCONNECTOME_DISPLAY_THRESHOLD` anche in modalità "percent", dove dovrebbe usare `1e-6` come la vista interattiva.

---

## 30-09-26 — Streamline per tratto come terza rappresentazione SDC, nella track s2.x

**Decisione**: `build_sdc_matrix.json` accetta `representation: "streamline"`, che legge `sdc/<subject>/*_LF-lesion_atlas-yeh_hcp1065_streamline.csv` (colonne `tract,streamline_ratio`) in una matrice soggetti x 87 tratti di sostanza bianca — un valore per tratto, la quota delle sue streamline colpite. Nuovo builder dedicato (`src.features.sdc.build_sdc_streamline_matrix`), non un parametro di quello parcellato. Lista autoritativa dei tratti in `assets/atlases/sdc_labels/yeh_hcp1065_streamline.csv` (colonna `tract`, 87 righe), derivata dall'unione su tutti i 1734 file reali. Il dato appartiene alla track **s2.x** (disconnettoma), non s1.x, nonostante il nome `LF-lesion`: quello che misura è una disconnessione, cioè streamline interrotte dalla lesione, non danno diretto al tessuto. Prima sessione: `s2.3-stream`, 7 dataset (UCL-UK non ha questo CSV).

**Perché un builder separato**: lo schema non ha nulla in comune con i CSV parcellati — nessuna colonna `region_name`, e una sola colonna di valori invece delle 6 statistiche interscambiabili di `KNOWN_VALUE_COLUMNS`. Di conseguenza la config non espone né `atlas` né `value_column` per questa modalità: non c'è niente da scegliere, e un campo non letto è vietato (`code_standards.md` §5).

**Perché un tratto mancante solleva invece di valere 0.0**: è l'unica differenza di comportamento reale rispetto al builder parcellato, che riempie a `0.0` perché BCBToolKit omette davvero le regioni a overlap nullo. Questo file invece scrive **tutti** i tratti, zeri compresi: verificato su tutti i 1734 file dei 7 dataset, stessi 87 tratti nello stesso ordine, da 2 a 42 non nulli per soggetto. Un file incompleto è quindi troncato o corrotto, e riempirlo sarebbe il fallback silenzioso che `code_standards.md` §0 esclude.

**Alternative scartate**: (a) generalizzare `build_sdc_matrix` con nomi di colonna configurabili — mette un parametro che non varia quasi mai sul percorso caldo della rappresentazione usata da ogni run esistente, senza guadagno; (b) un secondo file di config (`build_sdc_matrix_stream.json`) accanto a quello voxelwise — scartata su richiesta, si cambia `representation` nello stesso file; (c) trattarlo come atlante parcellato aggiungendone solo il file di reference — impossibile, manca `region_name`; (d) allineare per posizione di riga, dato che l'ordine è stabile su tutta la coorte — l'ordine non è garantito dal formato (`lessons_learned.md` #3), e dopo il controllo di completezza il `reindex` per nome non può comunque riempire niente, solo riordinare.

**Conseguenza ancora vera oggi**: nessuna colonna viene mai scartata, nemmeno se costante su tutti i soggetti ammessi — stessa regola del parcellato, la colonna `j` deve sempre indicare lo stesso tratto. Il clustering su questa matrice gira sui 87 tratti grezzi, senza dim reduction (`reduced_data: false`, `reduction_method: "raw"`): 87 dimensioni sono già basse, quindi `n_components` non entra in gioco.

## 29-09-26 — Esclusione dei soggetti: lista curata a mano al posto delle soglie in config

**Decisione**: `min_lesion_volume_voxels` e `max_out_of_brain_fraction` sono usciti da `build_lesion_matrix.json` (e da `BuildMatrixConfig`, `build_lesion_matrix()`, `_filter_by_lesion_quality`, ora cancellata). Chi escludere dalle matrici di produzione è deciso **a mano**, guardando le distribuzioni in `assets/metadata/lesion_metadata.csv` dal notebook `lesion_quality.ipynb`, e scritto in `assets/metadata/excluded_subjects.csv` (`subject_id, dataset, reason, value`; vocabolario chiuso dei motivi: `empty_mask`, `lesion_too_small`, `out_of_brain_fraction_too_high`). Quel file è letto sia da `build_lesion_matrix.py` sia da `build_sdc_matrix.py`, quindi le due matrici escludono gli stessi soggetti per costruzione.

**Perché**: i dati non hanno un salto naturale su cui mettere una soglia. Su 5853 soggetti: 3 maschere a 0 voxel a 2 mm, 132 con volume ≤ 10 voxel, e una coda continua senza discontinuità; il test IQR per dataset (log1p, Tukey 1.5) ne segnala solo 3, un quantile fisso al 2% ne prende 115. Sulla frazione fuori dal brain, 234 soggetti sopra il 5%, 73 sopra il 10%, 5 sopra il 30%. Una soglia in un config sceglie un numero arbitrario su quella coda e lo applica a tutti i dataset insieme; la decisione è invece caso per caso e appartiene all'analisi, non alla config di una pipeline. Il `value` per ogni riga tiene la decisione verificabile a distanza di mesi: "sub-X escluso" non si può rivedere, "sub-X escluso a 2 voxel" sì.

**Alternative scartate**: (a) tenere le soglie e affiancarci la lista — due meccanismi di ammissione attivi insieme, con il rischio che una soglia dimenticata in un config escluda soggetti che il notebook aveva deciso di tenere; (b) una lista per pipeline (una per la matrice lesionale, una per l'SDC) — due file che divergono, e un confronto lesione/SDC che silenziosamente confronta due coorti diverse; (c) far generare la lista da uno script a partire da soglie — sarebbe la soluzione (a) con un passaggio in più. Reintroduce `excluded_subjects`, scartata la mattina dello stesso giorno (vedi `project_changelog.md`, voce su `lesion_metrics`): allora l'argomento era che editare un config e rilanciare una pipeline di minuti fosse più macchinoso che correggere la cella a mano; ora la lista non fa rilanciare niente (è letta dalle pipeline di matrice, non da `enrich_metadata`) e la correzione a mano non è più possibile, perché ogni run di `enrich_metadata` ricopia le colonne derivate dalle maschere.

**Conseguenza ancora vera oggi**: un file assente **solleva**, non significa "non escludere nessuno" — le due cose sono indistinguibili, e costruire una matrice di produzione con tutti i soggetti limite dentro è esattamente ciò che la lista esiste per evitare. Per dire "nessuna esclusione" si tiene il file con la sola intestazione. Ogni riga è validata contro il registro (ID inesistente, ID duplicato, `dataset` in disaccordo, motivo non registrato, `value` non numerico sollevano): il file è scritto a mano e i dati ridondanti scritti a mano divergono. Oggi il file contiene solo l'intestazione: nessuna esclusione è ancora stata decisa.

---

## 29-09-26 — Metriche dalle maschere: quattro per griglia, su due griglie, con la correzione applicata prima del conteggio

**Decisione**: `assets/metadata/lesion_metadata.csv` registra, per ogni soggetto con maschera e **per ogni griglia dichiarata**, quattro valori: `lesion_volume_voxels_<g>`, `out_of_brain_fraction_<g>`, `laterality_index_<g>`, `lesion_side_<g>`. Le griglie in produzione sono due, `1mm` e `2mm`. Ordine di calcolo per ogni maschera e ogni griglia: ricampiona se e solo se la griglia della maschera differisce, binarizza, **misura la frazione fuori dal brain sulla maschera grezza**, azzera i voxel fuori dal brain (`correct_out_of_brain: true`), poi conta volume e lateralità. Un solo passaggio: una lettura da disco per soggetto, un ricampionamento per griglia.

**Perché due griglie**: le maschere manuali sono tutte a 1 mm (verificato sugli header di tutte e 5853: `182x218x182`, voxel `1.0`), il template di produzione è a 2 mm con ricampionamento `nearest`, che tiene un voxel su 8. Il conteggio a 2 mm è quindi un sottocampionamento in cui una lesione minuscola può ridursi o sparire; a 1 mm è nativo ed esatto. Confrontare i due volumi è l'unico modo per dire se una maschera a 0 voxel a 2 mm (3 soggetti: `sub-STUKLFR0671`, `sub-STUKE0146`, `sub-STUKE0201`) sia vuota nel file originale o abbia perso la lesione nel ricampionamento.

**Perché la frazione è pre-correzione e il resto post**: la correzione porta la frazione a 0 per costruzione, quindi misurarla dopo renderebbe inutile la sola colonna che serve a decidere chi escludere. Viceversa un voxel fuori dal cervello non è lesione: non va contato nel volume e non deve poter decidere il lato. Verificato che il caso è reale: senza correzione, 3 voxel di destra fuori dal brain contro 2 di sinistra dentro danno indice −0.2 e lato `right`; con la correzione, +1.0 e `left`.

**Alternative scartate**: contare senza correzione (contare voxel fuori dal cervello non ha senso, e il volume divergerebbe da quello di una matrice costruita con `correct_out_of_brain: true`); il lato solo sulla griglia a 2 mm, quella su cui la soglia è calibrata (a 1 mm il conteggio è esatto, quindi è la griglia *migliore* per attribuire il lato, non la peggiore — tenerle entrambe permette di ricalibrare senza rileggere le maschere); salvare il volume in mm³ (indipendente dalla griglia ma non risolve la perdita per sottocampionamento).

**Verificato dopo la prima run completa (30-09-26)**: per 5150 dei 5853 soggetti la griglia a 1 mm **non porta informazione in più**. `manual_masks/` contiene la lesione già ricampionata da BCBToolKit su griglia 1 mm (`docs/dev/retrieval.md`), e per i dataset segmentati originariamente a 2 mm i voxel risultano costanti in blocchi 2x2x2 allineati (fase `(1,1,1)`, zero blocchi misti, verificato su tutti i soggetti): UCL-UK, UKLFR, WashU, NEMESIS_T0, SFB936. Il conteggio a 2 mm ricostruisce esattamente la maschera nativa, quindi per loro nessuna lesione può sparire nel sottocampionamento. Le due colonne differiscono davvero solo per i 702 soggetti di PASPORT, PSP e WAKEUP. **Il disegno resta giustificato**: dei 4 soggetti con volume 0 sulla griglia di produzione, solo `sub-STUKLFR0671` ha la maschera davvero vuota; `sub-STUKE0146` (8 voxel) e `sub-STUKE0201` (3 voxel) hanno una lesione reale persa a 2 mm, ed entrambi stanno in WAKEUP, cioè fra i 702. Il quarto, `sub-STUNIPD0558`, arriva a 0 per la correzione (99,94% di lesione fuori dal cervello), non per la risoluzione. La ridondanza cade quindi esattamente dove è inevitabile, e l'informazione dove serve.

**Conseguenza ancora vera oggi**: `side_threshold=0.20` è calibrata **solo sulla griglia a 2 mm** (97.4% di accordo su 1445 soggetti, voce del 28-09-26) e viene applicata anche a 1 mm, dove non è verificata: `lesion_side_1mm` è indicativa finché `scripts/calibrate_lesion_side_threshold.py --grid 1mm` non viene eseguito. Il piano mediano escluso da entrambi gli emisferi è spesso 1 mm su una griglia e 2 mm sull'altra (la griglia a 1 mm ha 91 fette a sinistra e 90 a destra, quella a 2 mm 45 e 45), quindi per una lesione quasi tutta mediana i due indici non sono interscambiabili. `out_of_brain_fraction` è `NaN`, non `0.0`, per una maschera vuota: 0.0 metterebbe una maschera vuota tra i soggetti più puliti della distribuzione usata per scegliere le esclusioni. Nel registro `participants.csv` arrivano solo `lesion_volume_voxels_2mm` e `lesion_side`: il volume a 1 mm, le due frazioni e i due indici vivono solo nel csv, che è quello che legge il notebook.

---

## 29-09-26 — `correct_out_of_brain`: correggere (azzerare i voxel) invece di escludere il soggetto

**Decisione**: `build_lesion_matrix.json`/`BuildMatrixConfig` guadagna `correct_out_of_brain` (bool, default `false`) — invece di escludere un soggetto contaminato (`max_out_of_brain_fraction`), azzera i suoi voxel di lesione fuori dalla maschera cerebrale (`src/features/lesion_correction.py::zero_out_of_brain_voxels`) e lo mantiene nella matrice, con `lesion_volume_voxels` ricalcolato dai dati corretti. Applicato in `src/features/lesion.py::_apply_out_of_brain_correction`, eseguito **prima** di `min_lesion_volume_voxels` così quel filtro vede il volume già corretto, non quello grezzo. **Mutuamente esclusivo con `max_out_of_brain_fraction`**: entrambi attivi sollevano `ValueError`, sia a config-load (`src/analysis/build_config.py`) sia dentro `build_lesion_matrix` stesso (`lessons_learned.md` #2, validazione non ancorata a un solo punto di chiamata).

**Perché**: combinare le due strategie sullo stesso soggetto sarebbe ambiguo — se si corregge prima e si esclude dopo, la soglia `max_out_of_brain_fraction` controllerebbe una frazione già portata a ~0 dalla correzione, diventando silenziosamente inutile; se si esclude prima sulla frazione grezza, la correzione non avrebbe più nulla da fare sui sopravvissuti in caso di soglie strette. Richiesto esplicitamente dall'utente come alternativa all'esclusione pura introdotta nella voce del 28-09-26 in questo stesso file.

**Alternativa scartata**: combinare i due meccanismi (esclusione sulla frazione grezza + correzione sui sopravvissuti). Scartata su richiesta esplicita dell'utente per restare più semplice e priva di ambiguità — un solo criterio di ammissione attivo alla volta, mai due che interagiscono implicitamente.

**Conseguenza ancora vera oggi**: `config/pipelines/build_lesion_matrix.json` ha `correct_out_of_brain: false` — comportamento di produzione invariato, nessuna matrice già costruita è affetta (i thresholds/la correzione contano solo per run non ancora fatte, stessa nota della voce del 28-09-26). Il vecchio script standalone `scripts/lesion_fix.py`, che faceva la stessa correzione ma non era mai integrato in nessuna pipeline, è stato eliminato in questa stessa sessione (vedi `project_changelog.md`).

**Aggiornamento, stessa giornata**: la mutua esclusione descritta sopra **non esiste più**, perché `max_out_of_brain_fraction` è stata rimossa del tutto (voce "Esclusione dei soggetti: lista curata a mano", in cima a questo file). `correct_out_of_brain` resta, come unico uso di `brain_mask_path` in `build_lesion_matrix.json`, ed è attiva anche in `compute_lesion_metadata.json` (lì `true`). La ragione per cui le due strategie non andavano combinate resta valida e spiega perché non è stata tenuta una soglia accanto alla lista.

---

## 28-09-26 — `lesion_side` geometrico: soglia di bilateralità 0.20, dal protocollo standard di letteratura

**Decisione**: implementato il fallback geometrico per `lesion_side` (per i soggetti privi di dato clinico), con soglia di bilateralità **0.20** sul laterality index `LI = (left_voxels - right_voxels) / (left_voxels + right_voxels)` — la formula/soglia standard in letteratura per lesioni/attivazione fMRI (LI-toolbox di Wilke & Lidzba; protocollo Rorden/GigaScience per lesioni stroke), non calcolata da zero per questo progetto.

**Perché**: prima di questa sessione la variabile era esplicitamente non implementata (`docs/dev/metadata.md`), in attesa di una calibrazione della soglia contro dati clinici veri (`code_standards.md` §0 — mai un valore "dall'aria plausibile"). Calibrazione eseguita (`scripts/calibrate_lesion_side_threshold.py`) su 1445 soggetti con `lesion_side` clinico nei 5 dataset che lo hanno (`UNIPD/WashU`, `UNIPD/PSP`, `UKLFR/stroke_UKLFR`, `UKE/WAKEUP_acute`, `UKE/SFB936_ses01` - quest'ultimo onboardato nella stessa sessione, portando il set di calibrazione da 4 a 5 dataset): 0.20 riproduce il 97.4% delle etichette vere. Dettagli completi, matrice di confusione e letteratura in `knowledge/neuroimaging/lesion_laterality.md`.

**Alternativa scartata**: la soglia "ottimale" trovata per grid search sui nostri dati (0.36, accuratezza 97.5%, +2 soggetti su 1445 rispetto a 0.20). Scartata perché il guadagno è marginale e rischierebbe di overfittare sui soli 24 esempi di `both` (la classe bilaterale) disponibili nel set di calibrazione — usare il valore di letteratura resta anche più difendibile in caso di pubblicazione.

**Conseguenza ancora vera oggi**: la classe `both` resta debole a qualunque soglia testata (3/24 corretti anche alla soglia ottimale) - non un difetto della soglia scelta, un limite intrinseco del metodo per una lesione bilaterale che comunque pende leggermente da un lato nel conteggio voxel. `UNIPD/NEMESIS_T0` (onboardato lo stesso giorno, nessun `lesion_side` clinico) non riceve ancora il fallback: `build_lesion_matrix.json` non include questo dataset nella propria lista `datasets` (stesso gap già noto per `lesion_volume_voxels`, task separato non ancora fatto) - il fallback lo salta con un `WARNING`, non un errore, finché quella lista non viene estesa.

---

## 28-09-26 — `build_lesion_matrix.json` riportato alla griglia a 2mm, era scivolato a 1mm

**Decisione**: `reference_template_path`/`brain_mask_path` in `config/pipelines/build_lesion_matrix.json` passati da `tpl-MNI152NLin6Asym_res-1_*` (1mm) a `tpl-MNI152NLin6Asym_res-2_*` (2mm). Aggiornati anche i due path hardcoded nella sezione "Lesione fuori dal brain" di `notebooks/exploration/dataset_exploration.ipynb`, per restare sulla stessa griglia della produzione.

**Perché**: la voce del 06-09-26 in questo stesso file fissa la griglia a 2mm per `build_lesion_matrix.py` (e per `build_sdc_matrix.py` in modalità `voxelwise`), con alternative misurate e scartate esplicitamente. Lo swap del 23-09-26 da un singolo file paziente a un template versionato (`project_changelog.md`) ha però impostato `res-1` (1mm) — non una scelta di risoluzione deliberata, solo la prima opzione disponibile al momento di rendere il riferimento stabile — introducendo una deviazione silenziosa dalla griglia già decisa. Richiesto esplicitamente dall'utente ("voglio risoluzione a 2mm"), verificato prima di applicare che `res-2` T1w e brain mask condividano shape/affine (91×109×91, 2mm isotropo).

**Conseguenza ancora vera oggi**: `config/pipelines/build_sdc_matrix.json` (rappresentazione `voxelwise`) ha la **stessa** deviazione — `reference_template_path` è ancora su `res-1` — e non è stato toccato in questa sessione (fuori scope, riguarda solo `build_lesion_matrix.json`). Da allineare quando si torna a lavorare su quella pipeline. Nessun impatto su matrici già costruite (`data/derived/lesion_matrix/<sessione>/`): la griglia è fissata al momento del build, questo è solo un cambio di config per le run future.

---

## 28-09-26 — Filtro di qualità della lesione (volume minimo, frazione fuori dal brain): solo per `build_lesion_matrix.py`, non per `build_sdc_matrix.py`

**Decisione**: `build_lesion_matrix.py` guadagna due soglie opzionali di ammissione soggetto, entrambe `null` di default (nessun filtro): `min_lesion_volume_voxels` (esclude lesioni troppo piccole) e `max_out_of_brain_fraction` (esclude soggetti con troppi voxel di lesione fuori dalla maschera cerebrale MNI152, stessa logica di `scripts/lesion_fix.py`, richiede `brain_mask_path`). Entrambe calcolate in-run, dai dati voxel già caricati/binarizzati di quella specifica run (`src/features/lesion.py::_filter_by_lesion_quality`), non da `assets/metadata/participants.csv` — la cui colonna `lesion_volume_voxels` potrebbe riflettere una griglia/`binarize_threshold` di una run diversa. Un soggetto a 0 voxel di lesione ottiene `out_of_brain_fraction = 0.0` per convenzione esplicita (vacuosamente vero), mai `NaN`. I soggetti esclusi sono elencati in due nuove sezioni di `config.md`/`summaries/build_lesion_matrix/*/build_summary__*.md` ("Excluded by min_lesion_volume_voxels"/"Excluded by max_out_of_brain_fraction"), stesso schema già in uso per `group_filter`.

**Alternativa scartata**: implementare lo stesso meccanismo anche in `build_sdc_matrix.py`/`src/features/sdc.py`, come inizialmente richiesto. Scartata perché `sdc.py` risolve deliberatamente la presenza della lesion mask da `assets/metadata/participants.csv` (`has_lesion`), mai da un glob su `manual_masks/` — scelta presa apposta dopo un bug reale (debug 27-08-26, vedi `docs/dev/sdc_matrix.md` §"Why participants.tsv, not manual_masks/ on disk": una copia locale parziale dei dati falsava l'ammissione). Aggiungere qui le due soglie avrebbe richiesto o ricaricare `manual_masks/` direttamente (reintroducendo esattamente quel rischio) o precalcolare le metriche in `participants.csv` (un nuovo componente pipeline, fuori scope). Interpellato esplicitamente, l'utente ha confermato che le due soglie derivano dalla lesione e servono solo a `lesion_matrix`.

**Conseguenza ancora vera oggi**: una matrice già costruita in `data/derived/lesion_matrix/<sessione>/` non viene mai filtrata a posteriori — cambiare il criterio di ammissione non ha alcun effetto su un output già scritto. Se ci si accorge di aver dimenticato un'esclusione, la run va cancellata (cartella di output + riga in `runs.csv`) e rifatta da capo, mai patchata in-place.

**Superseduta il 29-09-26, stessa giornata**: le due soglie non esistono più, sostituite da una lista di soggetti curata a mano (voce in cima a questo file). L'alternativa scartata qui sopra — portare lo stesso meccanismo in `build_sdc_matrix.py` — è invece stata realizzata nella nuova forma, e per il motivo opposto a quello che allora la bloccava: una lista di `subject_id` non richiede a `sdc.py` di caricare nessuna maschera, quindi non reintroduce il rischio del glob su `manual_masks/`.

---

## 07-09-26 — Clustering lesionale: nessun k unico di produzione, per scelta

**Decisione**: per s1.1-vol e s1.2-vol non viene eletto un k di produzione. Le opzioni prodotte (k=4/5/6 su più metodi, più le varianti hdbscan e, su s1.1-vol, spectral a k=8) restano tutte valide in parallelo, ognuna come una lettura diversa della stessa struttura. Scritta nelle sezioni `Decisioni` di `docs/experiments/clustering/s1_production.md`, che erano rimaste vuote.

**Perché**: nessun criterio interno converge su un k solo — la silhouette premia k alti per costruzione, CH cresce quasi sempre con k, l'inertia non ha un gomito netto (`s1_tuning.md`). Restringere a un valore significherebbe delegare a una metrica di comodo una scelta che quella metrica non sa fare. In più il k non è separabile da `n_components` dell'embedding: il k migliore non converge tra n2/n3/n10, quindi i due vanno decisi insieme, a valle.

**Alternativa scartata**: eleggere un k unico su una metrica interna (tipicamente il massimo di silhouette). Scartata perché produrrebbe una scelta apparentemente oggettiva ma guidata da un artefatto della metrica, non dalla struttura dei dati.

**Conseguenza ancora vera oggi**: il confronto tra opzioni avviene in `notebooks/post-results_analysis/clustering_evaluation.ipynb`, che ne carica un sottoinsieme alla volta in `SELECTED_RUNS`. Una run di produzione presente in `results/` non è quindi "la" scelta: è una delle opzioni tenute aperte apposta.

---

## 06-09-26 — Ricampionamento a 2mm con `nearest`: confermato, alternative misurate

**Decisione**: ogni matrice voxel-wise resta sulla griglia MNI152NLin6Asym a 2mm con `resample_interpolation: "nearest"`. Vale per `build_lesion_matrix.py` e per `build_sdc_matrix.py` in modalità `voxelwise`.

**Contesto**: 2 soggetti UKE sono entrati in `lesion_matrix` s1.3-vol come righe tutte-zero (voce del 06-09-26 in `data_changelog.md`), il che ha aperto la domanda se `nearest` fosse la scelta sbagliata per tutte le run future.

**Misurato prima di decidere** (griglie native: UCL-UK e WashU già a 2mm, UKLFR a 1.5mm, PASPORT/PSP/UKE a 1mm — 1399 soggetti su 5720 vengono effettivamente ricampionati):

| | bias sul volume totale | errore mediano per soggetto | lesioni azzerate (48 più piccole) |
|---|---:|---:|---:|
| `nearest` | −1,5% | 1,6% | 2 |
| `linear` | −1,6% | 1,8% | 2 |

**Alternative scartate:**

- **`linear`**: misurata equivalente, e marginalmente peggiore in aggregato. Azzera *esattamente le stesse* 2 lesioni. Il motivo è che `nilearn.image.resample_to_img` con `linear` interpola tra i vicini del punto campionato, non media il blocco di 8 voxel: in downsampling si comporta quasi come `nearest`. E anche una media vera non salverebbe una lesione da 3 voxel, che resta sotto `binarize_threshold` 0.5 (3/8 = 0,375).
- **`continuous`**: già esclusa in precedenza per un motivo indipendente — lascia rumore di arrotondamento (~1e-17) attorno allo zero che impedisce a `_drop_constant_features` di scartare i voxel costanti.
- **Griglia a 1mm**: scartata per due ragioni. Una matrice SDC voxel-wise su ~1570 soggetti a 1mm sarebbe dell'ordine delle decine di GB (7,2M voxel per soggetto), non trattabile in locale; e la griglia comune a 2mm tiene la matrice lesionale e quella SDC allineate voxel per voxel, che è il presupposto della rappresentazione multimodale.

**Conseguenza ancora vera oggi**: la perdita non dipende dalla dimensione della lesione ma da *dove cade rispetto alla griglia* — nei dati misurati una lesione da 15 mm³ sopravvive e una da 16 mm³ sparisce. Non esiste quindi una soglia di volume sotto la quale "si sa" che il soggetto verrà perso: va controllato il volume post-ricampionamento, non quello nativo.

**Deciso di non intervenire sul codice** (07-09-26): `build_lesion_matrix.py` continua ad ammettere una riga tutta-zero senza segnalarla, a differenza di `build_sdc_matrix.py` che per il rischio equivalente esclude esplicitamente e traccia l'esclusione. Valutato non proporzionato: 2 soggetti su 5720 (0,035%). I due casi noti restano in `06-09_s1.3-vol` e sono documentati in `docs/experiments/processing/matrices.md`; chi userà quella matrice li filtra a valle se gli serve. Da rivedere se un dataset futuro ne producesse un numero non trascurabile — il segnale da guardare è il volume minimo *dopo* il ricampionamento, non quello nativo.

---

## 27-08-26 — Ammissione soggetti in `build_sdc_matrix.py`: controllo su `participants.csv`, non su `manual_masks/` su disco

**Decisione**: l'ammissione di un soggetto alla matrice SDC controlla `has_lesion` nel registro (`assets/metadata/participants.csv`), non l'esistenza del file su `manual_masks/` in locale.

**Perché**: su questa macchina locale `manual_masks/` conteneva solo un campione di 10 soggetti per dataset, mentre `sdc/` era già completo — un controllo sul disco locale ammetteva solo 40/1151 soggetti, escludendo erroneamente soggetti con una lesion mask reale ma non ancora retrievata localmente.

**Alternativa scartata**: controllare `manual_masks/` su disco direttamente — inaffidabile perché un retrieval locale parziale non riflette la disponibilità reale dei dati alla fonte.

**Conseguenza ancora vera oggi**: con il criterio sul registro, la run reale di allora ammetteva 1119/1151 soggetti; i 32 esclusi erano confermati genuinamente assenti dal registro clinico, non un artefatto di retrieval locale. La regola corrente (controllo su registro, non su disco) è documentata in `docs/guides/sdc_matrix_building.md`/`docs/dev/sdc_matrix.md`.

---

## 25-08-26 — `build_lesion_matrix.py`: rimossa la modalità `parcellated`

**Decisione**: `build_lesion_matrix.py` produce solo matrici voxel-wise; la modalità `parcellated` (matrice per macro-aree anatomiche via atlante) è stata rimossa dalla pipeline.

**Perché/dettagli**: vedi `management/notes/TODO.md`.

**Conseguenza ancora vera oggi**: non esiste un parametro di rappresentazione per questa pipeline — la matrice lesionale prodotta è sempre voxel-wise (a differenza di `build_sdc_matrix.py`, che ha sia `parcellated` sia `voxelwise`).
