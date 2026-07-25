# Masking delle feature FC in funzione della lesione — teoria e decisioni di metodo

> Fonte: Siegel et al. 2016 (*PNAS*), Griffis et al. 2019 (*Neuron*, in `assets/papers/`), XCP-D (`xcp_d/interfaces/connectivity.py`). Implementazione: `src/features/functional.py`, `src/pipeline/mask_fc.py`/`build_fc_matrix.py`. Prototipo eseguito su dati reali: `notebooks/fc_lesion_masking.ipynb`.

## Cos'è una matrice di connettività funzionale (FC)

Il cervello viene diviso in centinaia di piccole zone ("nodi" o "parcel"). Per ogni coppia di zone si misura, con la risonanza funzionale a riposo, quanto la loro attività è sincronizzata nel tempo — un numero vicino a 1 vuol dire "si accendono e si spengono insieme", vicino a 0 vuol dire "indipendenti", negativo vuol dire "si muovono in modo opposto". Il risultato per tutte le coppie possibili è una tabella nodo × nodo. Esempio con un cervello semplificato a 4 zone (A, B, C, D):

| | A | B | C | D |
|---|---|---|---|---|
| **A** | 1.00 | 0.62 | 0.10 | 0.35 |
| **B** | 0.62 | 1.00 | 0.05 | 0.20 |
| **C** | 0.10 | 0.05 | 1.00 | 0.40 |
| **D** | 0.35 | 0.20 | 0.40 | 1.00 |

Due proprietà sempre vere:
- **La diagonale è sempre 1** (una zona è perfettamente sincronizzata con se stessa) — non porta informazione, si scarta sempre.
- **La matrice è simmetrica** (A-B == B-A) — si tiene solo metà, il "triangolo superiore".

Nei dati reali (coorte WashU) i nodi non sono lettere ma ~239 regioni cerebrali reali, definite da una mappa di parcellazione (vedi sotto).

## Notazione: cosa significa `NodoA__NodoB`

Per usare questi dati in un modello statistico serve una forma piatta (un vettore), non una tabella 2D. Ogni connessione viene quindi rinominata concatenando i nomi delle due zone con un doppio underscore, tenendo solo il triangolo superiore (niente diagonale, niente doppioni come `B__A`): per 4 zone si ottengono 6 connessioni uniche (`A__B`, `A__C`, `A__D`, `B__C`, `B__D`, `C__D`).

Nei dati reali un nome di connessione ha quindi questa forma, es. `7Networks_LH_Default_IPL_1__7Networks_RH_Cont_PFCl_4` — connessione tra il nodo `7Networks_LH_Default_IPL_1` (lobo parietale inferiore sinistro, rete di default mode) e il nodo `7Networks_RH_Cont_PFCl_4` (corteccia prefrontale laterale destra, rete di controllo esecutivo). Con 239 nodi si ottengono 28.441 connessioni uniche per paziente.

## Il problema: lesione + FC

Ogni paziente stroke ha due tipi di dati sul cervello:
- **La lesione**: la zona di tessuto danneggiato (un'immagine 3D che dice, voxel per voxel, "qui c'è danno / qui no").
- **La FC**: la matrice descritta sopra, già calcolata per la coorte WashU.

Se una zona è dentro la lesione (tessuto morto/danneggiato), il segnale che ne esce non è più "attività cerebrale reale" — è rumore o assenza di segnale. Senza un intervento, si rischia di scambiare "questa zona è distrutta" per "comunicazione alterata tra zone sane". Serve quindi marcare come mancante ogni valore di connettività che coinvolge una zona troppo danneggiata, prima di poter usare questi dati per collegare lesione/disconnessione ai deficit clinici.

## Da dove viene il metodo (letteratura)

Non un metodo inventato per l'occasione — lo stesso approccio già usato in letteratura su questa stessa coorte (WashU, laboratorio Corbetta):

- **Siegel et al. 2016** — le connessioni delle zone dentro la lesione vengono rimosse dalle analisi (o azzerate, quando lo strumento a valle non accetta valori mancanti).
- **Griffis et al. 2019** (già in `assets/papers/`) — versione più precisa: una zona viene esclusa solo se una percentuale sufficiente del suo territorio è dentro la lesione. Soglia standard di campo: **50%**. Citazione esatta: *"Because the PLSC approach cannot accommodate missing values, functional connectivity between parcels that had been excluded ... was set to 0"* — il valore mancante viene marcato come tale (NaN) e sostituito con un valore concreto **solo nel momento in cui serve** a uno strumento che non tollera dati mancanti, non prima.
- **XCP-D** (`xcp_d/interfaces/connectivity.py`, classe `NiftiParcellate`) — il software che ha generato le matrici FC reali usa già un meccanismo identico (`min_coverage`, soglia di default 0.5), per un problema diverso (copertura BOLD). Si riusa lo stesso meccanismo con la lesione al posto del problema originale.

## Decisioni di metodo prese

1. **Niente funzione di conteggio scritta a mano** — si riusa `nilearn.maskers.NiftiLabelsMasker`, stesso schema a doppio masker di XCP-D (un masker senza maschera conta tutti i voxel, uno con `mask_img` conta i sani, il rapporto è la coverage).
2. **Le zone compromesse vengono marcate con NaN, non azzerate direttamente** — l'azzeramento (o un'altra strategia) avviene solo più avanti, come passo separato ed esplicito (Fase C, vicino a `dim_reduction.py`), subito prima di un metodo che non tollera NaN.
3. **Le matrici mascherate (con NaN) vengono salvate su disco così come sono**, prima di essere vettorizzate — formato ispezionabile a occhio per il controllo di qualità, indipendente da come verranno poi impilate/vettorizzate.
4. **Due pipeline separate** (`mask_fc.py`/`build_fc_matrix.py`), non una sola: permette di analizzare quanto ogni paziente è compromesso e decidere una soglia di esclusione prima di costruire la matrice finale, senza dover rifare il masking ogni volta.

## Esempio numerico: come funziona il masking, passo per passo

Atlante giocattolo a 4 zone (A, B, C, D), un paziente con lesione all'80% su C e al 30% su D:

1. **Carica la lesione** del paziente.
2. **Riallinea la lesione alla griglia dell'atlante** (`resample_to_img`, nearest neighbor) — lesione e atlante sono due file creati separatamente: anche a parità di dimensioni, l'orientamento spaziale reale va sempre verificato e corretto, mai assunto identico.
3. **Calcola la percentuale di zona sana**, per ciascuna delle 4 zone: A=100%, B=100%, C=20% (compromessa), D=70% (ancora valida).
4. **Decide quali zone sono compromesse** (soglia 50%): solo C.
5. **Carica la matrice di connettività** del paziente (tabella 4×4) e verifica che i nomi delle zone combacino con l'atlante.
6. **Marca con NaN** tutta la riga e tutta la colonna di C (compromessa) — A, B, D restano intatte.
7. **Salva su disco** questa matrice 4×4 mascherata, così com'è.
8. **Vettorizza**: tiene solo le 6 connessioni uniche (`A__B`, `A__C`, `A__D`, `B__C`, `B__D`, `C__D`), di cui 3 ora sono NaN (quelle che coinvolgono C).

Ripetendo questo per più pazienti (Fase B), ognuno ha zone diverse compromesse (dipende da dove ha la lesione), ma le etichette delle connessioni restano le stesse per tutti, nello stesso ordine — solo così si possono impilare in un'unica tabella pazienti × connessioni.

**Due direzioni di controllo qualità, dopo l'impilamento**:
- **Per paziente** (`fc_matrix.isna().sum(axis=1)`): quante connessioni sono NaN per quel paziente — quanto è compromesso complessivamente. È la base per decidere una soglia di *esclusione paziente* (vedi `notebooks/artifacts_inspection.ipynb`, sezione "Masked FC matrices").
- **Per connessione** (`fc_matrix.isna().sum(axis=0)`): quante volte, nel campione di pazienti considerato, *quella specifica connessione* (es. `NodoA__NodoB`) risulta NaN. Se una connessione è NaN in troppi pazienti del campione, è un problema di qualità della *feature* (quella colonna ha troppo pochi dati validi per essere utile a valle), non del paziente — domanda diversa da quella sopra.

## L'atlante (mappa cerebrale)

Per sapere quanto è dentro la lesione ogni singola zona serve una mappa di riferimento che dice esattamente dove sono i confini di ciascuna delle ~239 zone usate per calcolare la FC — senza questa mappa non si sa a quale zona appartiene ogni punto del cervello. Va caricata una sola volta (non per paziente): la mappa è sempre la stessa, cambia solo la lesione da confrontarci.

Contenuto (già pronto sul server EBRAIN, cartella `Atlases/fmriprep/atlas-<combo>/`, copiata in locale in `assets/atlases/fmriprep/`):
- Un'immagine 3D (`*_res-2_dseg.nii.gz`) dove ogni punto del cervello ha un numero che identifica a quale zona appartiene (0 = fuori dal cervello).
- Una tabella (`*_dseg.tsv`) che traduce ogni numero in un nome leggibile.

Si usa direttamente la versione a **2mm** di risoluzione (`res-2`) perché è già alla stessa risoluzione della lesion mask WashU — evita un passaggio di ricampionamento in più. 12 combinazioni di atlante sono disponibili (`Yan{100,200,300,400}TianS{1,2,3}Buckner7N`); oggi solo `Yan200TianS2Buckner7N` è stata validata/usata sui dati reali.

## Riferimento rapido — pipeline reale

- `data/derived/features/masked_fc/<combo>/` — matrici mascherate per singolo paziente (CSV con NaN) + `mask_summary.csv` (quanti nodi compromessi per paziente).
- `data/derived/features/fc_matrix/<combo>/<data>_<session>/` — matrice 2D finale (pazienti × connessioni), impilata e vettorizzata, ancora con i NaN dentro.
- Guida utente: `docs/guides/fc_matrix_building.md`. Architettura: `docs/dev/analysis.md`.
