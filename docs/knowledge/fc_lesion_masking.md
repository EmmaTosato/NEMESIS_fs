# Masking delle feature FC in funzione della lesione — teoria e decisioni di metodo

> Fonte: Siegel et al. 2016 (*PNAS*), Griffis et al. 2019 (*Neuron*, in `papers/`), XCP-D (`xcp_d/interfaces/connectivity.py`). Implementazione: `src/features/functional.py`, `src/pipeline/mask_fc.py`/`build_fc_matrix.py`. Prototipo eseguito su dati reali: `notebooks/fc_lesion_masking.ipynb`.

Il documento è in tre parti:

- **[Parte 1 — Teoria](#parte-1--teoria)**: cos'è il dato, come si chiama, qual è il problema, da dove viene il metodo, cos'è l'atlante. *Il perché concettuale.*
- **[Parte 2 — Decisioni implementative generali](#parte-2--decisioni-implementative-generali)**: le scelte di metodo prese e il loro razionale, il controllo qualità, i percorsi su disco. *Il perché delle scelte tecniche.*
- **[Parte 3 — Procedura passo per passo](#parte-3--procedura-passo-per-passo)**: cosa succede in sequenza, dallo step 1 (carica la lesione) fino a impilamento e controllo qualità. *Il cosa, in ordine — è questa la parte che il notebook rispecchia cella per cella.*

---

# Parte 1 — Teoria

## 1. Cos'è una matrice di connettività funzionale (FC)

Il cervello viene diviso in centinaia di piccole zone ("nodi" o "parcel"). Per ogni coppia di zone si misura, con la risonanza funzionale a riposo, quanto la loro attività è sincronizzata nel tempo — un numero vicino a 1 vuol dire "si accendono e si spengono insieme", vicino a 0 vuol dire "indipendenti", negativo vuol dire "si muovono in modo opposto". Il risultato per tutte le coppie possibili è una tabella nodo × nodo. Esempio con un cervello semplificato a 4 zone (A, B, C, D):

|       | A    | B    | C    | D    |
| ----- | ---- | ---- | ---- | ---- |
| **A** | 1.00 | 0.62 | 0.10 | 0.35 |
| **B** | 0.62 | 1.00 | 0.05 | 0.20 |
| **C** | 0.10 | 0.05 | 1.00 | 0.40 |
| **D** | 0.35 | 0.20 | 0.40 | 1.00 |

Due proprietà sempre vere:

- **La diagonale è sempre 1** (una zona è perfettamente sincronizzata con se stessa) — non porta informazione, si scarta sempre.
- **La matrice è simmetrica** (A-B == B-A) — si tiene solo metà, il "triangolo superiore".

Nei dati reali (coorte WashU) i nodi non sono lettere ma ~239 regioni cerebrali reali, definite dalla mappa di parcellazione descritta nella [sezione 5](#5-latlante-mappa-cerebrale).

## 2. Notazione: cosa significa `NodoA__NodoB`

Per usare questi dati in un modello statistico serve una forma piatta (un vettore), non una tabella 2D. Ogni connessione viene quindi rinominata concatenando i nomi delle due zone con un doppio underscore, tenendo solo il triangolo superiore (niente diagonale, niente doppioni come `B__A`): per 4 zone si ottengono 6 connessioni uniche (`A__B`, `A__C`, `A__D`, `B__C`, `B__D`, `C__D`).

Nei dati reali un nome di connessione ha quindi questa forma, es. `7Networks_LH_Default_IPL_1__7Networks_RH_Cont_PFCl_4` — connessione tra il nodo `7Networks_LH_Default_IPL_1` (lobo parietale inferiore sinistro, rete di default mode) e il nodo `7Networks_RH_Cont_PFCl_4` (corteccia prefrontale laterale destra, rete di controllo esecutivo). Con 239 nodi si ottengono 28.441 connessioni uniche per paziente.

## 3. Il problema: lesione + FC

Ogni paziente stroke ha due tipi di dati sul cervello:

- **La lesione**: la zona di tessuto danneggiato (un'immagine 3D che dice, voxel per voxel, "qui c'è danno / qui no").
- **La FC**: la matrice descritta sopra, già calcolata per la coorte WashU.

Se una zona è dentro la lesione (tessuto morto/danneggiato), il segnale che ne esce non è più "attività cerebrale reale" — è rumore o assenza di segnale. Senza un intervento, si rischia di scambiare "questa zona è distrutta" per "comunicazione alterata tra zone sane". Serve quindi marcare come mancante ogni valore di connettività che coinvolge una zona troppo danneggiata, prima di poter usare questi dati per collegare lesione/disconnessione ai deficit clinici.

## 4. Da dove viene il metodo (letteratura)

Non un metodo inventato per l'occasione — lo stesso approccio già usato in letteratura su questa stessa coorte:

- **Siegel et al. 2016** — le connessioni delle zone dentro la lesione vengono rimosse dalle analisi (o azzerate, quando lo strumento a valle non accetta valori mancanti).
- **Griffis et al. 2019** — versione più precisa: una zona viene esclusa solo se una percentuale sufficiente del suo territorio è dentro la lesione. Soglia standard di campo: **50%**. Citazione esatta: *"Because the PLSC approach cannot accommodate missing values, functional connectivity between parcels that had been excluded ... was set to 0"* — il valore mancante viene marcato come tale (NaN) e sostituito con un valore concreto **solo nel momento in cui serve** a uno strumento che non tollera dati mancanti, non prima.
- **XCP-D** (`xcp_d/interfaces/connectivity.py`, classe `NiftiParcellate`) — il software che ha generato le matrici FC reali usa già un meccanismo identico (`min_coverage`, soglia di default 0.5), per un problema diverso (copertura BOLD). Si riusa lo stesso meccanismo con la lesione al posto del problema originale.

### Sensibilità alla soglia: cosa succede ai valori estremi

`min_coverage` non è un valore hardcoded nel codice — è un campo obbligatorio di `config/pipelines/mask_fc.json` (oggi `0.5`), validato in `[0.0, 1.0]` da `src/analysis/build_config.py` (`_require_float_in_range`) e **senza default implicito**: se il campo manca, il caricamento del config solleva `ValueError`, mai un valore silenzioso (coerente con `code_standards.md` §0). Senza una soglia il concetto di "nodo compromesso" non è definibile — resta solo la coverage, un numero continuo tra 0 e 1.

La decisione booleana vive in `src/features/functional.py`, `find_compromised_nodes` — confronto stretto, non `<=`:

```python
return node_names[parcel_coverage < min_coverage]
```

Ai due estremi:

- **`min_coverage = 0.0`**: `parcel_coverage < 0.0` è sempre falso — nessun nodo verrebbe mai marcato compromesso, nemmeno uno distrutto al 100%. Il masking sarebbe di fatto disattivato: il segnale di tessuto morto verrebbe trattato come attività neurale reale, la stessa confusione descritta nella [sezione 3](#3-il-problema-lesione--fc).
- **`min_coverage = 1.0`**: qualunque nodo con anche un solo voxel dentro la lesione (coverage < 100%) verrebbe marcato compromesso. Con lesion mask reali (rumore di segmentazione, resampling) questo marca compromessi molti più nodi per paziente rispetto a `0.5` — sui dati reali WashU, con soglia `0.5` la mediana è 1 nodo compromesso su 169 pazienti (media 3.9, vedi `notebooks/artifacts_inspection.ipynb`, sezione "Masked FC matrices"); una soglia `1.0` sposterebbe questa distribuzione molto più in alto, senza un guadagno scientifico corrispondente.

`0.5` non è quindi un numero scelto ad hoc in questo progetto: è lo stesso standard di campo di Griffis et al. 2019, riusato dallo stesso meccanismo (`min_coverage`) già presente in XCP-D per il proprio problema di copertura BOLD. Per verificarne la sensibilità sui dati reali, l'approccio corretto è uno sweep esplicito (rilanciare `mask_fc.py` con `min_coverage` a es. 0.3/0.5/0.7 e confrontare le distribuzioni di `mask_summary.csv`), non la sua rimozione.

## 5. L'atlante (mappa cerebrale)

Per sapere quanto è dentro la lesione ogni singola zona serve una mappa di riferimento che dice esattamente dove sono i confini di ciascuna delle ~239 zone usate per calcolare la FC — senza questa mappa non si sa a quale zona appartiene ogni punto del cervello. Va caricata una sola volta (non per paziente): la mappa è sempre la stessa, cambia solo la lesione da confrontarci.

Contenuto (già pronto sul server EBRAIN, cartella `Atlases/fmriprep/atlas-<combo>/`, copiata in locale in `assets/atlases/fmriprep/`):

- Un'immagine 3D (`*_res-2_dseg.nii.gz`) dove ogni punto del cervello ha un numero che identifica a quale zona appartiene (0 = fuori dal cervello).
- Una tabella (`*_dseg.tsv`) che traduce ogni numero in un nome leggibile.

Si usa direttamente la versione a **2mm** di risoluzione (`res-2`) perché è già alla stessa risoluzione della lesion mask WashU — evita un passaggio di ricampionamento in più. 12 combinazioni di atlante sono disponibili (`Yan{100,200,300,400}TianS{1,2,3}Buckner7N`); oggi solo `Yan200TianS2Buckner7N` è stata validata/usata sui dati reali.

Il concetto chiave che l'atlante rende possibile calcolare è la **coverage**: la percentuale di voxel sani di una zona, ottenuta sovrapponendo lesione e atlante. È il numero su cui si decide se una zona è compromessa; il calcolo concreto è lo [step 3 della procedura](#step-1-8--per-ogni-paziente-mask_fcpy).

---

# Parte 2 — Decisioni implementative generali

## Decisioni di metodo prese

1. **Niente funzione di conteggio scritta a mano** — si riusa `nilearn.maskers.NiftiLabelsMasker`, stesso schema a doppio masker di XCP-D (un masker senza maschera conta tutti i voxel, uno con `mask_img` conta i sani, il rapporto è la coverage).
2. **Le zone compromesse vengono marcate con NaN, non azzerate direttamente** — l'azzeramento (o un'altra strategia) avviene solo più avanti, come passo separato ed esplicito (vicino a `dim_reduction.py`), subito prima di un metodo che non tollera NaN.
3. **Le matrici mascherate (con NaN) vengono salvate su disco così come sono**, prima di essere vettorizzate — formato ispezionabile a occhio per il controllo di qualità, indipendente da come verranno poi impilate/vettorizzate.
4. **Due pipeline separate** (`mask_fc.py`/`build_fc_matrix.py`), non una sola: permette di analizzare quanto ogni paziente è compromesso e decidere una soglia di esclusione prima di costruire la matrice finale, senza dover rifare il masking ogni volta. Quali step spettano a quale pipeline è mostrato nella [Parte 3](#parte-3--procedura-passo-per-passo).

## Controllo qualità dopo l'impilamento

Una volta costruita la tabella pazienti × connessioni, si contano i NaN in due direzioni diverse — due domande distinte, non la stessa misura vista due volte:

- **Per paziente** (`fc_matrix.isna().sum(axis=1)`): quante connessioni sono NaN per quel paziente — quanto è compromesso complessivamente. È la base per decidere una soglia di *esclusione paziente* (vedi `notebooks/artifacts_inspection.ipynb`, sezione "Masked FC matrices").
- **Per connessione** (`fc_matrix.isna().sum(axis=0)`): quante volte, nel campione di pazienti considerato, *quella specifica connessione* (es. `NodoA__NodoB`) risulta NaN. Se una connessione è NaN in troppi pazienti, è un problema di qualità della *feature* (quella colonna ha troppo pochi dati validi per essere utile a valle), non del paziente — domanda diversa da quella sopra.

## Riferimento rapido — pipeline reale

- `data/derived/features/masked_fc/<combo>/` — matrici mascherate per singolo paziente (CSV con NaN) + `mask_summary.csv` (quanti nodi compromessi per paziente).
- `data/derived/features/fc_matrix/<combo>/<data>_<session>/` — matrice 2D finale (pazienti × connessioni), impilata e vettorizzata, ancora con i NaN dentro.
- Guida utente: `docs/guides/fc_matrix_building.md`. Architettura: `docs/dev/analysis.md`.

---

# Parte 3 — Procedura passo per passo

La procedura completa, in ordine di esecuzione, dall'inizio fino alla matrice finale con controllo qualità. Ogni step è illustrato sull'atlante giocattolo a 4 zone (A, B, C, D) della [sezione 1](#1-cosè-una-matrice-di-connettività-funzionale-fc).

Si divide in tre blocchi, che corrispondono a tre momenti diversi:

- **Setup** — una sola volta all'avvio.
- **Step 1-8 — per ogni paziente, uno alla volta** → li fa `mask_fc.py`.
- **Step 9-12 — tutti i pazienti insieme, dopo che ognuno ha finito gli step 1-8** → li fa `build_fc_matrix.py`.

## Setup — Carica l'atlante

Carica la mappa cerebrale (immagine con i numeri-zona + tabella che li traduce in nomi, [sezione 5](#5-latlante-mappa-cerebrale)). Una sola volta, non per paziente: è sempre la stessa mappa, cambia solo la lesione da confrontarci. Da qui si ricava l'elenco ordinato dei nomi delle zone (`node_names`), riusato da tutti gli step successivi.

## Step 1-8 — per ogni paziente (`mask_fc.py`)

Questi 8 step si ripetono identici per **ogni** paziente, uno alla volta. Sotto, un paziente giocattolo con lesione all'80% sulla zona C e al 30% sulla zona D.

1. **Carica la lesione** del paziente — l'immagine 3D che dice, voxel per voxel, dove c'è danno.
2. **Riallinea la lesione alla griglia dell'atlante** (`resample_to_img`, nearest neighbor). Lesione e atlante sono due file creati separatamente: anche a parità di dimensioni, l'orientamento spaziale reale va sempre verificato e corretto, mai assunto identico.
3. **Calcola la coverage** (percentuale di zona sana), per ciascuna delle 4 zone. Ogni zona è un insieme di voxel (piccoli cubetti 3D, es. 2mm×2mm×2mm) — la zona C, per dire, è fatta di 50 voxel in tutto. Sovrapponendo lesione e atlante si conta quanti di quei 50 voxel *non* sono dentro la lesione: se sono 10, la coverage è 10/50 = **20%**. Risultato per le 4 zone: A=100%, B=100%, C=20%, D=70%.
4. **Decide quali zone sono compromesse** — coverage sotto la soglia del 50% ([sezione 4](#4-da-dove-viene-il-metodo-letteratura)). Nel nostro esempio: solo **C** (20% < 50%; D con 70% resta valida).
5. **Carica la matrice di connettività** del paziente (tabella 4×4) e verifica che i nomi delle zone combacino con l'atlante — se l'ordine non corrisponde, ci si ferma con un errore, mai si maschera "per posizione".
6. **Marca con NaN** tutta la riga e tutta la colonna delle zone compromesse. Qui: riga C e colonna C → NaN. A, B, D restano intatte. (NaN e non zero: il valore concreto si decide solo a valle, decisione 2 della [Parte 2](#decisioni-di-metodo-prese).)
7. **Salva su disco** questa matrice 4×4 mascherata, così com'è — è l'**unico output su disco** di questo blocco (un CSV per paziente, in `masked_fc/<combo>/`).
8. **Vettorizza**: appiattisce la matrice mascherata nelle 6 connessioni uniche del triangolo superiore (`A__B`, `A__C`, `A__D`, `B__C`, `B__D`, `C__D`), di cui 3 ora NaN (quelle che coinvolgono C). Il risultato è un **vettore in memoria** per questo paziente — *non* viene salvato da solo su disco: resta lì in attesa dell'impilamento (step 10).

Il vettore del nostro paziente giocattolo (**paziente 1**), dopo lo step 8:

| A__B | A__C | A__D | B__C | B__D | C__D |
| ---- | ---- | ---- | ---- | ---- | ---- |
| 0.62 | NaN  | 0.35 | NaN  | 0.20 | NaN  |

## Step 9-12 — tutti i pazienti insieme (`build_fc_matrix.py`)

Questi step partono **solo dopo** che *ogni* paziente ha completato gli step 1-8 e ha prodotto il suo vettore. Non ha senso impilare o fare controllo qualità su un paziente solo — servono tutti insieme.

Per mostrarli con numeri concreti serve più di un paziente: aggiungiamo un **paziente 2**, con lesione sulla zona **A** (A compromessa, le altre sane). Il suo vettore dopo lo step 8:

| A__B | A__C | A__D | B__C | B__D | C__D |
| ---- | ---- | ---- | ---- | ---- | ---- |
| NaN  | NaN  | NaN  | 0.05 | 0.20 | 0.40 |

9. **Verifica l'allineamento delle etichette** tra pazienti: tutti devono avere le stesse identiche connessioni, nello stesso ordine. Se un paziente ha etichette diverse, ci si ferma con un errore — mai si impila "per posizione".
10. **Impila**: mette il vettore di ogni paziente come una riga di un'unica tabella pazienti × connessioni.

    |            | A__B | A__C | A__D | B__C | B__D | C__D |
    | ---------- | ---- | ---- | ---- | ---- | ---- | ---- |
    | paziente 1 | 0.62 | NaN  | 0.35 | NaN  | 0.20 | NaN  |
    | paziente 2 | NaN  | NaN  | NaN  | 0.05 | 0.20 | 0.40 |

11. **Controllo qualità** — conta i NaN nelle due direzioni ([Parte 2](#controllo-qualità-dopo-limpilamento) per il significato di ciascuna):
    - **per paziente** (per riga): paziente 1 → 3 NaN, paziente 2 → 3 NaN;
    - **per connessione** (per colonna): `A__C` è NaN in **entrambi** (2/2, un endpoint compromesso in ciascuno), `B__D` non è mai NaN (0/2, B e D sane in tutti), le altre 1/2.
12. **Salva la matrice impilata** su disco (in `fc_matrix/<combo>/<data>_<session>/`), ancora con i NaN dentro — è l'output finale di questa pipeline.

**E l'imputazione (NaN → valore concreto)?** Non fa parte di questa procedura. È un passo separato e successivo, da fare solo subito prima di un metodo che non tollera NaN (PCA/UMAP), vicino a `dim_reduction.py` (decisione 2 della [Parte 2](#decisioni-di-metodo-prese)). La matrice salvata allo step 12 resta volutamente con i NaN.
