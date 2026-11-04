# Disconnettoma strutturale e BCBToolKit — teoria, calcolo, carico di disconnessione

> Teoria: [Disconnettoma strutturale e BCBToolKit — teoria, calcolo, carico di disconnessione](../../../knowledge/concepts/Neuroimaging_Connectivity/disconnectome_bcbtoolkit.md) (second brain). Questa nota contiene solo la parte specifica di NEMESIS.

> Nota di metodo, pensata come base per la sezione Metodi di un paper. Ogni affermazione fattuale ha una fonte, numerata nella sezione [Fonti](#fonti) in fondo. Le scelte del progetto sono dichiarate come tali; i punti non verificati sono segnalati come tali.
>
> Implementazione nel repo: [`docs/dev/sdc_matrix.md`](../../../docs/dev/sdc_matrix.md) (le tre matrici) e [`docs/dev/metadata.md`](../../../docs/dev/metadata.md), sezione `sdc_metadata.csv` (il carico di disconnessione).

La nota è in tre parti:

- **[Parte 1 — BCBToolKit](#parte-1--bcbtoolkit)**: cos'è, chi lo sviluppa, i moduli, la trattografia normativa, come il progetto lo usa.
- **[Parte 2 — Il disconnettoma strutturale (SDC)](#parte-2--il-disconnettoma-strutturale-sdc)**: perché si usa, come si calcola, cosa vuol dire un valore, i limiti, le tre rappresentazioni del repo.
- **[Parte 3 — Il carico di disconnessione](#parte-3--il-carico-di-disconnessione)**: definizione, formula, differenza dal volume della lesione, equivalenti in letteratura.

---

## 5. Come il progetto usa BCBToolKit

**Provenienza dei file letti oggi.** Le cartelle `bcbtoolkit/<soggetto>/` degli 8 dataset (34 file per soggetto) sono copiate dall'output condiviso sul server EBRAIN (`Clinical_connectome/features/Clinical_connectome_stroke/<dataset>/lesion/`, vedi `docs/guides/datasets.md` e `.claude/history/data_changelog.md`, voci 03-09-26 e 23-09-26). Il repo non le calcola.

**Come il progetto ha eseguito BCBToolKit** (pipeline `compute_sdc.py`, ritirata nel commit `d8dbdee`; codice leggibile nel commit precedente, `8c964da` = `d8dbdee^`: `src/sdc/runner.py`, `src/sdc/resample.py`, `config/pipelines/compute_sdc.json`). Fatti verificati sul codice di quel commit:

- **Stage 1**:
  ```
  bcb-lf-preprocess --bids-dir <staging> --output-dir <prep> --bcbtoolkit /data/etosato/tools/BCBToolKit \
      --ncores 4 --skip-existing --tracks-dir /data/corbetta/Clinical_connectome/BCBToolkit/TRK/tracks7T
  ```
  `run_notes` del config: le trattografie sono "l'atlante completo (178 soggetti, HCP 7T, 1mm)".
- **Controllo tra i due stage**: ogni disconnettoma deve esistere, essere un NIfTI leggibile e avere shape 182 × 218 × 182 (griglia MNI152NLin6Asym a 1 mm); chi non passa non entra in Stage 2.
- **Stage 2**:
  ```
  bcb-lesion-features --prep-dir <validated_prep> --output-dir <validated_prep> --assume-yes --skip-existing --ebrains
  ```
  `stage2_ebrains: true`, `stage2_presets: []`: i 15 atlanti EBRAINS di default di bcblib, nessun preset aggiuntivo.
- **Prima di Stage 1**: le maschere che non stanno sulla griglia MNI a 1 mm vengono ricampionate con *nearest neighbour* sul `MNI152.nii.gz` di BCBToolKit, perché `bcb-lf-preprocess` riconosce solo alcune shape canoniche (docstring di `src/sdc/resample.py`, bcblib 0.6.1).
- **Soglia sulla probabilità**: nessuna. Il comando non passa la soglia; il README documenta per `run_disco.sh` una soglia `-t` con default 0, "nessuna soglia" [2], e il codice corrente di BCBlib non passa `-t` [3].
- **Scope**: 4 dataset (WashU, PASPORT, PSP, UKLFR), 1150 soggetti (`.claude/history/stato_progetto_archive.md`).

**Coerenza con i file di oggi.** Che i file copiati dal server siano stati prodotti con questi stessi comandi **non è verificato**: coprono 8 dataset invece di 4 e contengono il CSV `yeh_hcp1065_streamline`, che la run del progetto non chiedeva. Due proprietà però coincidono, misurate sui file: il minimo non nullo è 1/178 (stesso numero di soggetti normativi di `tracks7T`, e nessuna soglia applicata, altrimenti il minimo sarebbe almeno la soglia); la griglia è 182 × 218 × 182 a 1 mm.

---

## 11. Le tre rappresentazioni del repo

Il repo costruisce dall'output di BCBToolKit tre matrici soggetti × feature (`build_sdc_matrix.py`, campo `representation`; dettagli in `docs/dev/sdc_matrix.md`).

**Voxelwise.** La mappa $d(v)$ stessa (`*_res-1_desc-disconnectome.nii.gz`), ricampionata sulla griglia di produzione a 2 mm, appiattita, mai binarizzata. È la rappresentazione più vicina all'oggetto di [5] e [7], che usano le mappe voxel per voxel come feature (UMAP su mappe vettorizzate in [7]).

**Parcellizzata.** Un valore per regione di un atlante (`LF-disconnectome_atlas-<atlante>.csv`, Stage 2 di BCBlib). Nel codice di BCBlib [3] (versione corrente del repository, non la 0.6.1: vedi sotto), per una regione $R$:

$$\text{mean\_overlap}(R) = \frac{1}{|R|} \sum_{v \in R} d(v)$$

cioè la probabilità media di disconnessione su tutti i voxel della regione, zeri compresi; `sum_overlap` è la somma; `p90_overlap`/`p95_overlap` sono percentili sui soli voxel non nulli. Le regioni con meno di un voxel non nullo vengono scartate dal file (`min_overlap_voxels = 1`) [3], il che è coerente con quanto il repo osserva sui file (le regioni a sovrapposizione nulla mancano). È lo stesso principio di Thiebaut de Schotten et al. 2020, che stimano "la probabilità di disconnessione per ogni regione" con una parcellazione corticale [5].

**Streamline.** Un valore per tratto (`LF-lesion_atlas-yeh_hcp1065_streamline.csv`, 87 tratti, colonne `tract,streamline_ratio`). Nel codice di BCBlib [3], `streamline_ratio` è la frazione delle streamline di un tratto che attraversano la lesione:

$$\text{streamline\_ratio}(T) = \frac{\#\{\text{streamline di } T \text{ che intersecano la lesione}\}}{\#\{\text{streamline di } T\}}$$

calcolata sulle trattografie "Yeh HCP1065" dopo aver portato la maschera binaria da MNI152NLin6Asym a MNI152NLin2009cAsym, lo spazio di quei file [3]. È una misura **diversa** dalle altre due: non passa dai 178 soggetti normativi né da una probabilità di popolazione, ma interseca la lesione con un'unica trattografia di popolazione per tratto. Per questo il file appartiene alla famiglia `LF-lesion` pur misurando una disconnessione.

Sulla fonte delle trattografie Yeh:

- Yeh et al. 2018 costruiscono un atlante di trattografia di popolazione da 842 soggetti HCP (550.000 traiettorie, 80 etichette anatomiche, verificate da neuroanatomisti) [14];
- Yeh 2022 ricostruisce con tractografia automatica 52 fasci in ciascuno di 1065 soggetti HCP (22-37 anni) [15].

Quale pubblicazione descriva esattamente i file "HCP1065" usati da BCBlib, e da dove vengano i loro 87 tratti, **non è verificato**.

**Versione del codice.** Le definizioni di questa sezione vengono dal codice di BCBlib sul ramo `master` [3], letto il 21-10-26. Il progetto ha usato bcblib 0.6.1 (sezione 5). Le due versioni non sono state confrontate: il nome del disconnettoma prodotto dal codice corrente (`_desc-disconnectome`, senza `res-1`) differisce già da quello dei nostri file (`_res-1_desc-disconnectome`).

---

## 15. Scelte del progetto, in breve

- Somma **dentro la maschera cerebrale**: la parte fuori è trattografia che esce dal cervello, non disconnessione (stessa scelta di `correct_out_of_brain` per le lesioni).
- **Nessuna soglia** sulla probabilità.
- **Due griglie**, 1 mm (nativa) e 2 mm (produzione).
- Ogni mappa è portata sulla griglia col **suo** header: le mappe hanno tre orientamenti diversi tra i dataset.

Motivazioni, alternative scartate e numeri: `docs/dev/metadata.md`, sezione `sdc_metadata.csv`, e `.claude/history/methods_changelog.md`.

---

## Righe tolte dalla nota teorica (rimandi, dati e confronti del progetto)

| Modulo | Cosa fa | Usato dal progetto |
|---|---|---|
| *Normalisation* | Porta l'immagine T1 del paziente nello spazio MNI152. Usa un approccio **enantiomorfico**: il tessuto lesionato viene sostituito dal tessuto sano controlaterale prima di calcolare la deformazione, perché la lesione altererebbe la registrazione [1, 6]. | No (le maschere arrivano già in MNI) |
| *Tractotron* | Confronta la lesione con un atlante di tratti di sostanza bianca e dà, per ogni tratto, la probabilità che sia disconnesso. Nel paper un tratto è "coinvolto" se la lesione cade dove la probabilità di presenza del tratto supera il 50% [1]. Da riga di comando (`tractotron_cli.sh`) scrive due matrici lesioni × tratti: *probability* e *proportion* (quota del volume del tratto binarizzato coperta dalla lesione); la soglia di binarizzazione del tratto è 0,5 di default [2]. | No |
| *Disconnectome map* | Usa la lesione come seme della trattografia in un gruppo di soggetti sani e produce una mappa voxel per voxel della probabilità di disconnessione [1]. Da riga di comando: `run_disco.sh` [2]. | **Sì**: è la mappa da cui nasce tutto l'SDC del repo |
| *AnaCOM2* | Identifica le disconnessioni associate a un deficit: raggruppa i pazienti per regione disconnessa e confronta le loro prestazioni con quelle dei controlli [1]. | No |
| *Funcon* | Calcola reti di connettività funzionale a riposo, *seed-based*, nei soggetti sani [1]. | No |
| Spessore corticale | Stima lo spessore corticale con il metodo DiReCT, dopo il riempimento enantiomorfico della lesione [1]. Il nome del modulo nel toolkit non è verificato. | No |

| Fonte | Soggetti normativi |
|---|---|
| **Mappe di questo progetto** | **178** (vedi sotto) |

Il valore 178 delle nostre mappe è **verificato sui dati**, non preso da una fonte: il minimo valore non nullo di ogni disconnettoma (`map_min_nonzero` nei `mapstats.tsv`) è sempre 0,005618 = 1/178, cioè un solo soggetto su 178 (controllato sui `mapstats.tsv` dei disconnettomi di tutti e 5852 i soggetti con mappa non vuota, degli 8 dataset; `sub-STUKLFR0671` ha la mappa vuota; vedi anche `docs/dev/metadata.md`). Quale dei rilasci elencati sopra corrisponda esattamente a queste 178 trattografie **non è verificato**.

**Il deficit dipende dalla disconnessione, non solo dalla sede.** Tre risultati su cui il progetto si appoggia (sintesi in `knowledge/notes/stroke_literature/summaries_core.md`):

- $d(v) = 1/N$ (nelle nostre mappe 1/178): succede in un solo soggetto;

- **La soglia di probabilità.** Non c'è una soglia unica: 50% in [1] e [4], nessuna soglia di default in `run_disco.sh` [2], soglia 0,5 per un conteggio di voxel in Ulrichsen et al. [13]. Senza soglia ogni voxel toccato da un solo soggetto conta. **Scelta del progetto**: nessuna soglia sulle mappe (sezione 5). Nelle nostre mappe questo rende la diffusione della disconnessione molto ampia: la mediana dei voxel non nulli è il 36% del cervello, fino al 91% (`docs/dev/metadata.md`).

- **Ridondanza con la lesione.** La disconnessione strutturale indiretta non spiega quasi mai varianza in più rispetto alla lesione [6]; misure globali di disconnessione correlano fortemente con il volume della lesione [13] (sezione 15 per il nostro caso).

- **Limiti propri dei nostri dati** (fatti misurati nel progetto, non letteratura):
  - la trattografia esce dal cervello: in mediana lo 0,80% della massa della mappa sta fuori dalla maschera cerebrale, fino al 15,3% (`docs/dev/sdc_matrix.md`, 5845 soggetti a 2 mm);
  - per le maschere frazionarie di PSP non è noto se BCBToolKit binarizzi o usi pesi continui (`.claude/open_problems.md`);
  - `sub-STUKLFR0671` ha una mappa interamente nulla (`.claude/history/data_changelog.md`, 07-09-26).

Il **carico di disconnessione** (*disconnection load*) di un soggetto è la somma della probabilità di disconnessione sui voxel dentro il cervello. Dice **quanta** disconnessione produce la lesione, in totale, su tutto il cervello. È una **misura del progetto**: il nome e la scelta di mascherare sul cervello sono nostri (sezione 14 per gli equivalenti in letteratura).

Nel repo: colonne `disconnection_load_voxels_<g>` e `disconnection_mean_<g>` di `assets/metadata/sdc_metadata.csv`, con $g \in \{$`2mm`, `1mm`$\}$ (`src/features/sdc.py::compute_sdc_metadata`).

**Unità.** "Voxel pesati per probabilità". A 1 mm un voxel è 1 mm³, quindi $L^{(1\text{mm})}$ è in mm³. A 2 mm un voxel è 8 mm³ e il ricampionamento *nearest* tiene un voxel su otto, quindi $L^{(2\text{mm})} \approx L^{(1\text{mm})}/8$ (misurato su tutta la coorte: $8 \cdot L^{(2\text{mm})}/L^{(1\text{mm})}$ ha mediana 1,001, da 0,989 a 1,017, `docs/dev/metadata.md`).

**Nei nostri dati le due misure sono comunque molto correlate.** Su 5853 soggetti (`assets/metadata/participants.csv`, griglia 2 mm, misura del progetto del 21-10-26), la correlazione di Spearman tra `disconnection_load_voxels_2mm` e `lesion_volume_voxels_2mm` è 0,906. Tra i soggetti nel quartile più basso di volume (≤ 103 voxel a 2 mm), solo lo 0,5% ha un carico sopra la mediana della coorte. Il carico non è quindi un'informazione indipendente dal volume, ma lo riordina dove la sede conta. Lo stesso andamento è riportato in letteratura: una misura globale di disconnessione correla fortemente con il volume della lesione (correlazione bayesiana, media a posteriori 0,74, su 84 pazienti) [13].

| Fonte | Nome | Definizione | Rispetto al nostro carico |
|---|---|---|---|
| Ulrichsen et al. 2021 [13] | *disconnection severity*, *global disconnectivity* | (a) intensità media dei voxel della mappa di disconnessione; (b) numero di voxel con probabilità > 0,5 | (a) è il nostro $\bar d$ a meno del dominio della media, che il paper non specifica (tutta l'immagine o il cervello); (b) è la variante a soglia, scartata dal progetto (`docs/dev/metadata.md`) |
| BCBlib, `mapstats.tsv` [3] | `map_sum`, "disconnectome integral" | somma di tutti i valori della mappa | stessa somma, **senza** maschera cerebrale; il nostro carico esclude la parte fuori dal cervello |
| Griffis et al. 2019 [12] | *total SDC*, *SDC severity* | numero di disconnessioni regione-regione binarizzate | stesso concetto (quanta disconnessione in totale), oggetto diverso: conta coppie di regioni, non integra una mappa voxel |
| Egger et al. 2021 [16] | (somma del disconnettoma) | somma delle voci della matrice di disconnessione | come sopra, su una matrice di connettività |
| Griffis et al. 2021, Lesion Quantification Toolkit [17] | *disconnection severity* | famiglia di misure: tratto per tratto, mappe voxel, matrici tra parcelle | termine generico della stessa famiglia, non una formula unica |

Il nome **"disconnection load"** non l'abbiamo trovato in letteratura con questa definizione: va dichiarato come nome del progetto. Per un paper, la formulazione più vicina alle fonti è "*the sum of the voxel-wise probability of disconnection within the brain mask (disconnectome integral [3]), equivalent up to a constant to the mean disconnection probability used as a global disconnection severity measure in [13]*".
