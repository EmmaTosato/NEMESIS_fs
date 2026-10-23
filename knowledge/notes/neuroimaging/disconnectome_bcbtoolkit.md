# Disconnettoma strutturale e BCBToolKit — teoria, calcolo, carico di disconnessione

> Nota di metodo, pensata come base per la sezione Metodi di un paper. Ogni affermazione fattuale ha una fonte, numerata nella sezione [Fonti](#fonti) in fondo. Le scelte del progetto sono dichiarate come tali; i punti non verificati sono segnalati come tali.
>
> Implementazione nel repo: [`docs/dev/sdc_matrix.md`](../../../docs/dev/sdc_matrix.md) (le tre matrici) e [`docs/dev/metadata.md`](../../../docs/dev/metadata.md), sezione `sdc_metadata.csv` (il carico di disconnessione).

La nota è in tre parti:

- **[Parte 1 — BCBToolKit](#parte-1--bcbtoolkit)**: cos'è, chi lo sviluppa, i moduli, la trattografia normativa, come il progetto lo usa.
- **[Parte 2 — Il disconnettoma strutturale (SDC)](#parte-2--il-disconnettoma-strutturale-sdc)**: perché si usa, come si calcola, cosa vuol dire un valore, i limiti, le tre rappresentazioni del repo.
- **[Parte 3 — Il carico di disconnessione](#parte-3--il-carico-di-disconnessione)**: definizione, formula, differenza dal volume della lesione, equivalenti in letteratura.

---

# Parte 1 — BCBToolKit

## 1. Cos'è e chi lo sviluppa

**BCBToolKit** (scritto anche *BCBtoolkit*) è un pacchetto software gratuito per l'analisi delle lesioni cerebrali: misura l'effetto di una lesione focale sui circuiti a distanza, attraverso la connettività strutturale e funzionale di soggetti sani [1].

- **Chi**: Brain Connectivity and Behaviour Laboratory (BCBlab), Sorbonne Universités, Parigi. Il README ufficiale lo attribuisce a Michel Thiebaut de Schotten e Chris Foulon [2]; il paper di riferimento è Foulon et al. 2018, *GigaScience* [1].
- **Licenza e piattaforme**: BSD 3-Clause; Linux e macOS; scritto in Java, Bash e R, dipende da FSL [1, 2]. Il README specifica che il toolkit non è approvato per uso clinico [2].
- **Pagina del progetto**: http://toolkit.bcblab.com [1]. Durante la stesura di questa nota (21-10-26) il sito non era raggiungibile; i contenuti riportati qui vengono dal paper [1] e dai repository GitHub ufficiali [2, 3].

**BCBlib** è una libreria Python dello stesso laboratorio, sviluppata da Chris Foulon [3]. Contiene due comandi che orchestrano BCBToolKit e ne estraggono le feature [3]:

- `bcb-lf-preprocess` (**Stage 1**): porta le lesioni in MNI152NLin6Asym a 1 mm e calcola i disconnettomi.
- `bcb-lesion-features` (**Stage 2**): estrae, dall'output di Stage 1, le sovrapposizioni con gli atlanti.

## 2. I moduli

Foulon et al. 2018 descrivono un insieme di metodi complementari, ciascuno implementato come strumento del toolkit [1]. I nomi in corsivo sono quelli usati nel paper.

| Modulo | Cosa fa | Usato dal progetto |
|---|---|---|
| *Normalisation* | Porta l'immagine T1 del paziente nello spazio MNI152. Usa un approccio **enantiomorfico**: il tessuto lesionato viene sostituito dal tessuto sano controlaterale prima di calcolare la deformazione, perché la lesione altererebbe la registrazione [1, 6]. | No (le maschere arrivano già in MNI) |
| *Tractotron* | Confronta la lesione con un atlante di tratti di sostanza bianca e dà, per ogni tratto, la probabilità che sia disconnesso. Nel paper un tratto è "coinvolto" se la lesione cade dove la probabilità di presenza del tratto supera il 50% [1]. Da riga di comando (`tractotron_cli.sh`) scrive due matrici lesioni × tratti: *probability* e *proportion* (quota del volume del tratto binarizzato coperta dalla lesione); la soglia di binarizzazione del tratto è 0,5 di default [2]. | No |
| *Disconnectome map* | Usa la lesione come seme della trattografia in un gruppo di soggetti sani e produce una mappa voxel per voxel della probabilità di disconnessione [1]. Da riga di comando: `run_disco.sh` [2]. | **Sì**: è la mappa da cui nasce tutto l'SDC del repo |
| *AnaCOM2* | Identifica le disconnessioni associate a un deficit: raggruppa i pazienti per regione disconnessa e confronta le loro prestazioni con quelle dei controlli [1]. | No |
| *Funcon* | Calcola reti di connettività funzionale a riposo, *seed-based*, nei soggetti sani [1]. | No |
| Spessore corticale | Stima lo spessore corticale con il metodo DiReCT, dopo il riempimento enantiomorfico della lesione [1]. Il nome del modulo nel toolkit non è verificato. | No |

## 3. La trattografia normativa

Il disconnettoma non usa la diffusione del paziente: usa le trattografie di **soggetti sani** (normativa), in cui la lesione viene "proiettata" [1, 5, 6, 7].

**La fonte dei dati.** I soggetti normativi delle versioni recenti vengono dallo Human Connectome Project, diffusione a 7 T [5, 6, 7], acquisita con il protocollo di Vu et al. 2015 [8]. Sono giovani adulti: 29,5 ± 3,6 anni nel sottoinsieme di 176 soggetti usato da Salvalaggio et al. [6].

**Come è ricostruita** (procedura riportata da Talozzi et al. 2023 per 176 soggetti HCP 7T [7]):

- preprocessing HCP standard (TOPUP, EDDY), 65 volumi a b = 2000 s/mm², voxel isotropo di 1,05 mm;
- trattografia **deterministica** whole-brain con StarTrack, deconvoluzione sferica (Richardson-Lucy smorzato), angolo massimo 35°, passo 0,5 mm, lunghezza minima 15 mm;
- le trattografie individuali sono portate in MNI152 (template di densità di streamline, ANTs GreedySyN).

**Quanti soggetti.** Il numero cambia tra versioni e articoli:

| Fonte | Soggetti normativi |
|---|---|
| Thiebaut de Schotten et al. 2015 (versione precedente, 3 T, non HCP) | 129, 18-79 anni [4] |
| Foulon et al. 2018 (paper del toolkit) | 10 [1] |
| Thiebaut de Schotten et al. 2020 | 163, HCP 7T [5] |
| Salvalaggio et al. 2020; Talozzi et al. 2023 | 176, HCP 7T [6, 7] |
| Ulrichsen et al. 2021 (utilizzatori del toolkit) | 170, HCP 7T [13] |
| README di BCBToolKit | 178 nell'atlante incluso (2 mm); 180 negli atlanti scaricabili a 2 mm e a 1 mm [2] |
| **Mappe di questo progetto** | **178** (vedi sotto) |

Il valore 178 delle nostre mappe è **verificato sui dati**, non preso da una fonte: il minimo valore non nullo di ogni disconnettoma (`map_min_nonzero` nei `mapstats.tsv`) è sempre 0,005618 = 1/178, cioè un solo soggetto su 178 (controllato sui `mapstats.tsv` dei disconnettomi di tutti e 5852 i soggetti con mappa non vuota, degli 8 dataset; `sub-STUKLFR0671` ha la mappa vuota; vedi anche `docs/dev/metadata.md`). Quale dei rilasci elencati sopra corrisponda esattamente a queste 178 trattografie **non è verificato**.

Foulon et al. 2018 riportano che 10 soggetti bastano per una mappa che condivide più del 70% della varianza con quella della popolazione, e che la somiglianza anatomica non cala con l'età [1].

## 4. Come nasce la mappa di probabilità

Per ogni paziente e ogni soggetto normativo $k = 1, \dots, N$ [1, 7]:

1. la lesione (in MNI) viene usata come **seme**: si tengono le streamline del soggetto $k$ che attraversano la lesione;
2. queste streamline diventano una **mappa di visitazione binaria** $b_k(v) \in \{0, 1\}$: vale 1 se almeno una streamline passa per il voxel $v$ [7];
3. le $N$ mappe binarie vengono **mediate**.

$$d(v) = \frac{1}{N} \sum_{k=1}^{N} b_k(v) \in [0, 1]$$

Foulon et al. 2018 descrivono una variante in cui la lesione viene registrata nello spazio nativo di ogni controllo, la trattografia è fatta lì (Trackvis) e la mappa riportata in MNI [1]; Talozzi et al. 2023 filtrano trattografie già portate in MNI [7]. Il README di BCBToolKit chiede che la maschera sia in MNI e alla stessa risoluzione dell'atlante di trattografie [2], il che è coerente con la seconda variante. Quale variante esegua `run_disco.sh` nella versione usata **non è verificato** sul codice.

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

# Parte 2 — Il disconnettoma strutturale (SDC)

## 6. Cos'è

Il **disconnettoma strutturale** (*structural disconnectome*, SDC) di un paziente è la mappa delle connessioni di sostanza bianca che la sua lesione interrompe [1, 5]. Non si misura sul paziente: si **stima** mettendo la sua lesione dentro un connettoma normativo di soggetti sani e raccogliendo le fibre che la attraversano [6]. Per questo si chiama anche disconnessione **indiretta** [6].

## 7. Perché si usa

**L'ipotesi della disconnessione.** Una lesione non danneggia solo il tessuto in cui si trova: interrompe i fasci che passano di lì, e le aree collegate da quei fasci, anche se intatte, non funzionano più normalmente [9, 10]. È la tradizione delle sindromi da disconnessione, riformulata da Geschwind nel 1965 [9] e ripresa con la trattografia moderna [4, 10].

**Diaschisi.** È la disfunzione di una regione lontana dalla lesione ma connessa ad essa; il termine è di von Monakow (1914) [11]. Carrera e Tononi distinguono la diaschisi focale dalla diaschisi **connettiva**, cioè i cambiamenti di connettività strutturale e funzionale tra regioni lontane dalla lesione, più coerente con i deficit clinici [11]. Thiebaut de Schotten et al. 2015 separano le due cose: diaschisi = disfunzione di una regione distante connessa all'area danneggiata; disconnessione = disfunzione di due aree intatte collegate da un tratto danneggiato [4].

**Il deficit dipende dalla disconnessione, non solo dalla sede.** Tre risultati su cui il progetto si appoggia (sintesi in `knowledge/notes/stroke_literature/summaries_core.md`):

- **Griffis et al. 2019** (114 pazienti): la disconnessione strutturale spiega le alterazioni di connettività funzionale molto meglio del danno alla materia grigia; aggiungere la "SDC totale" moltiplica per circa 2,5 la varianza spiegata della perdita di modularità (R² aggiustato da 0,10 a 0,25) e resta l'unico predittore significativo anche aggiungendo il volume della lesione [12].
- **Salvalaggio et al. 2020** (132 pazienti): la disconnessione strutturale indiretta predice i deficit in quasi tutti i domini (0,16 < R² < 0,58, esclusa la memoria verbale), con un'accuratezza paragonabile alla lesione; la combinazione lesione + SDC migliora solo l'attenzione [6]. La disconnessione funzionale indiretta, invece, non predice [6].
- **Thiebaut de Schotten et al. 2020** (1333 lesioni): il disconnettoma è legato alle mappe di attivazione funzionale più della sola lesione [5].
- **Talozzi et al. 2023**: un embedding UMAP dei disconnettomi predice punteggi neuropsicologici a un anno meglio di sei modelli concorrenti, tra cui la topologia della lesione e il volume della lesione con l'età [7].

## 8. Cosa significa un valore tra 0 e 1

$d(v)$ è la **frazione dei soggetti normativi** in cui almeno una streamline che attraversa la lesione passa per il voxel $v$ [5, 7]. Tiene conto della variabilità interindividuale della ricostruzione dei tratti [1, 6]:

- $d(v) = 1$: in tutti i soggetti sani, la lesione interrompe fibre che passano da $v$;
- $d(v) = 0{,}5$: succede in metà dei soggetti;
- $d(v) = 1/N$ (nelle nostre mappe 1/178): succede in un solo soggetto;
- $d(v) = 0$: in nessuno.

È una probabilità **di popolazione**: dice quanto è frequente, tra i cervelli sani, che quella lesione tocchi fibre dirette a $v$. Non è la probabilità che *questo* paziente abbia davvero perso le fibre in $v$.

Thiebaut de Schotten et al. 2015 scelgono di considerare solo i voxel sopra il 50%, "il nucleo anatomico quasi invariabile" di un tratto, non la sua periferia [4]. Foulon et al. 2018 riportano le mappe tra 50% e 100% [1].

## 9. Quando si usa

- Quando del paziente si ha solo un'immagine strutturale clinica (T1, FLAIR, CT) e nessuna diffusione: è il vantaggio principale dei metodi indiretti [6, 13].
- Su coorti grandi e multicentriche, dove una trattografia individuale di qualità non è disponibile per tutti [5, 7].
- Per mappare deficit su reti di sostanza bianca, e per predire deficit ed esiti [6, 7].

## 10. Limiti

- **Nessuna trattografia individuale.** La mappa è quella che la lesione produrrebbe in cervelli sani, non quella del paziente: non vede la variabilità anatomica individuale né le alterazioni preesistenti [4, 5].
- **La normativa è giovane e sana.** I soggetti HCP 7T hanno circa 29 anni [6], i pazienti stroke molto di più. Gli autori dichiarano di privilegiare la qualità del connettoma rispetto all'età [5]; Thiebaut de Schotten et al. 2015 segnalano che cambiamenti legati a età e sesso possono sovra- o sottostimare l'estensione della disconnessione [4].
- **Gli errori della trattografia.** Falsi positivi e falsi negativi, incroci di fibre, scelte di parametri: la trattografia può non corrispondere alle connessioni vere [4, 13].
- **La soglia di probabilità.** Non c'è una soglia unica: 50% in [1] e [4], nessuna soglia di default in `run_disco.sh` [2], soglia 0,5 per un conteggio di voxel in Ulrichsen et al. [13]. Senza soglia ogni voxel toccato da un solo soggetto conta. **Scelta del progetto**: nessuna soglia sulle mappe (sezione 5). Nelle nostre mappe questo rende la diffusione della disconnessione molto ampia: la mediana dei voxel non nulli è il 36% del cervello, fino al 91% (`docs/dev/metadata.md`).
- **Ridondanza con la lesione.** La disconnessione strutturale indiretta non spiega quasi mai varianza in più rispetto alla lesione [6]; misure globali di disconnessione correlano fortemente con il volume della lesione [13] (sezione 15 per il nostro caso).
- **Disconnessione non è disfunzione.** La mappa dice quali fibre passano dalla lesione, non quanto la loro perdita alteri la funzione.
- **Limiti propri dei nostri dati** (fatti misurati nel progetto, non letteratura):
  - la trattografia esce dal cervello: in mediana lo 0,80% della massa della mappa sta fuori dalla maschera cerebrale, fino al 15,3% (`docs/dev/sdc_matrix.md`, 5845 soggetti a 2 mm);
  - per le maschere frazionarie di PSP non è noto se BCBToolKit binarizzi o usi pesi continui (`.claude/open_problems.md`);
  - `sub-STUKLFR0671` ha una mappa interamente nulla (`.claude/history/data_changelog.md`, 07-09-26).

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

# Parte 3 — Il carico di disconnessione

## 12. Definizione

Il **carico di disconnessione** (*disconnection load*) di un soggetto è la somma della probabilità di disconnessione sui voxel dentro il cervello. Dice **quanta** disconnessione produce la lesione, in totale, su tutto il cervello. È una **misura del progetto**: il nome e la scelta di mascherare sul cervello sono nostri (sezione 14 per gli equivalenti in letteratura).

Per il soggetto $s$, su una griglia $g$ con maschera cerebrale $B_g$ e mappa $d_s$ ricampionata su $g$:

$$L_s^{(g)} = \sum_{v \in B_g} d_s(v)$$

La **media** è lo stesso carico diviso per il numero di voxel cerebrali:

$$\bar d_s^{(g)} = \frac{L_s^{(g)}}{|B_g|} \in [0, 1]$$

Il divisore $|B_g|$ è una costante della griglia, quindi $L$ e $\bar d$ ordinano i soggetti in modo identico: sono la stessa misura in due unità. $\bar d$ si legge come frazione (la probabilità di disconnessione media sul cervello).

Nel repo: colonne `disconnection_load_voxels_<g>` e `disconnection_mean_<g>` di `assets/metadata/sdc_metadata.csv`, con $g \in \{$`2mm`, `1mm`$\}$ (`src/features/sdc.py::compute_sdc_metadata`).

**Unità.** "Voxel pesati per probabilità". A 1 mm un voxel è 1 mm³, quindi $L^{(1\text{mm})}$ è in mm³. A 2 mm un voxel è 8 mm³ e il ricampionamento *nearest* tiene un voxel su otto, quindi $L^{(2\text{mm})} \approx L^{(1\text{mm})}/8$ (misurato su tutta la coorte: $8 \cdot L^{(2\text{mm})}/L^{(1\text{mm})}$ ha mediana 1,001, da 0,989 a 1,017, `docs/dev/metadata.md`).

## 13. Cosa lo distingue dal volume della lesione

Il volume della lesione conta i voxel **della lesione**:

$$V_s^{(g)} = \sum_{v \in B_g} \ell_s(v), \qquad \ell_s(v) \in \{0, 1\}$$

Il carico integra la probabilità di disconnessione su **tutto il cervello**, lesione e resto. Sostituendo la definizione di $d$ (sezione 4) si vede cosa misura:

$$L_s = \sum_{v \in B} \frac{1}{N} \sum_{k=1}^{N} b_{s,k}(v) = \frac{1}{N} \sum_{k=1}^{N} \bigl|\{v \in B : b_{s,k}(v) = 1\}\bigr|$$

cioè **il volume medio, sui soggetti normativi, del territorio di sostanza bianca attraversato dalle fibre che passano per la lesione**. Il volume misura quanto tessuto è danneggiato; il carico misura quanto cervello dipende, tramite le fibre, dal tessuto danneggiato.

Una conseguenza: due lesioni dello stesso volume possono avere carichi molto diversi. Una lesione piccola dentro un fascio denso, dove passano molte fibre lunghe, ha un carico alto; una lesione grande in una zona attraversata da poche fibre ne ha uno basso. Thiebaut de Schotten et al. 2015 fanno l'esempio clinico: una piccola lesione della capsula interna può compromettere le funzioni del tratto corticospinale più di una lesione grande della corona radiata [4]. Egger et al. 2021 riportano che lesioni più piccole concentrate sugli hub di rete possono avere esiti motori gravi quanto lesioni molto più grandi [16].

**Nei nostri dati le due misure sono comunque molto correlate.** Su 5853 soggetti (`assets/metadata/participants.csv`, griglia 2 mm, misura del progetto del 21-10-26), la correlazione di Spearman tra `disconnection_load_voxels_2mm` e `lesion_volume_voxels_2mm` è 0,906. Tra i soggetti nel quartile più basso di volume (≤ 103 voxel a 2 mm), solo lo 0,5% ha un carico sopra la mediana della coorte. Il carico non è quindi un'informazione indipendente dal volume, ma lo riordina dove la sede conta. Lo stesso andamento è riportato in letteratura: una misura globale di disconnessione correla fortemente con il volume della lesione (correlazione bayesiana, media a posteriori 0,74, su 84 pazienti) [13].

## 14. Equivalenti in letteratura

Una misura equivalente esiste, con nomi diversi:

| Fonte | Nome | Definizione | Rispetto al nostro carico |
|---|---|---|---|
| Ulrichsen et al. 2021 [13] | *disconnection severity*, *global disconnectivity* | (a) intensità media dei voxel della mappa di disconnessione; (b) numero di voxel con probabilità > 0,5 | (a) è il nostro $\bar d$ a meno del dominio della media, che il paper non specifica (tutta l'immagine o il cervello); (b) è la variante a soglia, scartata dal progetto (`docs/dev/metadata.md`) |
| BCBlib, `mapstats.tsv` [3] | `map_sum`, "disconnectome integral" | somma di tutti i valori della mappa | stessa somma, **senza** maschera cerebrale; il nostro carico esclude la parte fuori dal cervello |
| Griffis et al. 2019 [12] | *total SDC*, *SDC severity* | numero di disconnessioni regione-regione binarizzate | stesso concetto (quanta disconnessione in totale), oggetto diverso: conta coppie di regioni, non integra una mappa voxel |
| Egger et al. 2021 [16] | (somma del disconnettoma) | somma delle voci della matrice di disconnessione | come sopra, su una matrice di connettività |
| Griffis et al. 2021, Lesion Quantification Toolkit [17] | *disconnection severity* | famiglia di misure: tratto per tratto, mappe voxel, matrici tra parcelle | termine generico della stessa famiglia, non una formula unica |

Il nome **"disconnection load"** non l'abbiamo trovato in letteratura con questa definizione: va dichiarato come nome del progetto. Per un paper, la formulazione più vicina alle fonti è "*the sum of the voxel-wise probability of disconnection within the brain mask (disconnectome integral [3]), equivalent up to a constant to the mean disconnection probability used as a global disconnection severity measure in [13]*".

## 15. Scelte del progetto, in breve

- Somma **dentro la maschera cerebrale**: la parte fuori è trattografia che esce dal cervello, non disconnessione (stessa scelta di `correct_out_of_brain` per le lesioni).
- **Nessuna soglia** sulla probabilità.
- **Due griglie**, 1 mm (nativa) e 2 mm (produzione).
- Ogni mappa è portata sulla griglia col **suo** header: le mappe hanno tre orientamenti diversi tra i dataset.

Motivazioni, alternative scartate e numeri: `docs/dev/metadata.md`, sezione `sdc_metadata.csv`, e `.claude/history/methods_changelog.md`.

---

# Fonti

1. Foulon C, Cerliani L, Kinkingnéhun S, Levy R, Rosso C, Urbanski M, Volle E, Thiebaut de Schotten M. Advanced lesion symptom mapping analyses and implementation as BCBtoolkit. *GigaScience* 2018;7(3):1-17. https://doi.org/10.1093/gigascience/giy004
2. Thiebaut de Schotten M, Foulon C. BCBToolKit, repository GitHub ufficiale e README. https://github.com/chrisfoulon/BCBToolKit (consultato il 21-10-26).
3. Foulon C. BCBlib, repository GitHub ufficiale: README, `bcblib/tools/lesion_features/_disco.py`, `_streamline.py`, `_pipeline.py`, `bcblib/tools/damage_profile/_stats.py`, ramo `master`. https://github.com/chrisfoulon/BCBlib (consultato il 21-10-26).
4. Thiebaut de Schotten M, Dell'Acqua F, Ratiu P, et al. From Phineas Gage and Monsieur Leborgne to H.M.: Revisiting Disconnection Syndromes. *Cerebral Cortex* 2015;25(12):4812-4827. https://doi.org/10.1093/cercor/bhv173
5. Thiebaut de Schotten M, Foulon C, Nachev P. Brain disconnections link structural connectivity with function and behaviour. *Nature Communications* 2020;11:5094. https://doi.org/10.1038/s41467-020-18920-9
6. Salvalaggio A, De Filippo De Grazia M, Zorzi M, Thiebaut de Schotten M, Corbetta M. Post-stroke deficit prediction from lesion and indirect structural and functional disconnection. *Brain* 2020;143(7):2173-2188. https://doi.org/10.1093/brain/awaa156
7. Talozzi L, Forkel SJ, Pacella V, et al. Latent disconnectome prediction of long-term cognitive-behavioural symptoms in stroke. *Brain* 2023;146(5):1963-1978. https://doi.org/10.1093/brain/awad013
8. Vu AT, Auerbach E, Lenglet C, et al. High resolution whole brain diffusion imaging at 7T for the Human Connectome Project. *NeuroImage* 2015;122:318-331. https://doi.org/10.1016/j.neuroimage.2015.08.004
9. Geschwind N. Disconnexion syndromes in animals and man. I. *Brain* 1965;88(2):237-294. https://doi.org/10.1093/brain/88.2.237
10. Catani M, ffytche DH. The rises and falls of disconnection syndromes. *Brain* 2005;128(10):2224-2239. https://doi.org/10.1093/brain/awh622
11. Carrera E, Tononi G. Diaschisis: past, present, future. *Brain* 2014;137(9):2408-2422. https://doi.org/10.1093/brain/awu101
12. Griffis JC, Metcalf NV, Corbetta M, Shulman GL. Structural Disconnections Explain Brain Network Dysfunction after Stroke. *Cell Reports* 2019;28(10):2527-2540.e9. https://doi.org/10.1016/j.celrep.2019.07.100
13. Ulrichsen KM, Kolskår KK, Richard G, et al. Structural brain disconnectivity mapping of post-stroke fatigue. *NeuroImage: Clinical* 2021;30:102635. https://doi.org/10.1016/j.nicl.2021.102635
14. Yeh FC, Panesar S, Fernandes D, et al. Population-averaged atlas of the macroscale human structural connectome and its network topology. *NeuroImage* 2018;178:57-68. https://doi.org/10.1016/j.neuroimage.2018.05.027
15. Yeh FC. Population-based tract-to-region connectome of the human brain and its hierarchical topology. *Nature Communications* 2022;13:4933. https://doi.org/10.1038/s41467-022-32595-4
16. Egger P, Evangelista GG, Koch PJ, et al. Disconnectomics of the Rich Club Impacts Motor Recovery After Stroke. *Stroke* 2021;52(6):2115-2124. https://doi.org/10.1161/STROKEAHA.120.031541
17. Griffis JC, Metcalf NV, Corbetta M, Shulman GL. Lesion Quantification Toolkit: A MATLAB software tool for estimating grey matter damage and white matter disconnections in patients with focal brain lesions. *NeuroImage: Clinical* 2021;30:102639. https://doi.org/10.1016/j.nicl.2021.102639
