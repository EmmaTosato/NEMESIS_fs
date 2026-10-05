# Lato della lesione (lesion_side) calcolato geometricamente — regola, calibrazione, stato reale in NEMESIS

> Fonte: Wilke & Lidzba (LI-toolbox, la convenzione standard di *laterality index* in letteratura fMRI/lesione), il protocollo "Calculating the Laterality Index Using FSL for Stroke Neuroimaging" (Rorden e colleghi, *GigaScience* 2016) — stessa formula applicata qui a maschere di lesione binarie invece che a mappe di attivazione statistica. Implementazione: `src/features/lesion.py` (`compute_lesion_laterality_metrics`, `_hemisphere_masks`, `lesion_side_from_laterality_index`). Calibrazione empirica: `src/pipeline/calibrate_lesion_side_threshold.py`, misure in questo documento.

Il documento è in tre parti:

- **[Parte 1 — La regola](#parte-1--la-regola)**: la formula, la soglia, perché è la convenzione standard. *Il perché concettuale.*
- **[Parte 2 — Le sfumature geometriche](#parte-2--le-sfumature-geometriche)**: coordinate world vs indice di voxel, orientamento RAS, il piano di midline. *Il perché delle scelte tecniche.*
- **[Parte 3 — Lo stato reale in NEMESIS](#parte-3--lo-stato-reale-in-nemesis)**: la calibrazione vera, i numeri, i limiti noti. *I fatti su cui poggia la decisione in vigore.*

---

# Parte 1 — La regola

## 1. Perché serve un fallback geometrico

`lesion_side` (`left`/`right`/`both`) è un dato clinico prima di tutto — arriva dal tsv grezzo del dataset, quando quella colonna esiste. Ma 3 degli 8 dataset in-scope non hanno mai avuto questa colonna (UCL-UK, PASPORT, e il nuovo `UNIPD/NEMESIS_T0` onboardato il 28-09-26), e altri hanno celle vuote per singoli soggetti pur avendo la colonna. La maschera di lesione, però, esiste sempre per un soggetto ammesso — quindi il lato si può derivare geometricamente, come fallback esplicito, e come sostituto del dato clinico dove questo esiste solo per i dataset dichiarati in `geometric_override_datasets` (`config/pipelines/enrich_metadata.json`) e solo quando il lato clinico è l'opposto esatto di quello geometrico — vedi `docs/guides/metadata.md`.

## 2. La formula: laterality index

$$LI = \frac{L - R}{L + R}$$

dove $L$/$R$ sono i voxel di lesione rispettivamente a sinistra e a destra della midline MNI. È la stessa identica formula usata per la lateralizzazione dell'attivazione fMRI (LI-toolbox, Wilke & Lidzba) e già applicata a maschere di lesione stroke nel protocollo FSL di Rorden — non una convenzione inventata per questo progetto.

$LI \in (-1, 1)$: positivo → lesione a prevalenza sinistra, negativo → prevalenza destra, vicino a 0 → bilaterale.

## 3. La soglia di bilateralità

$$\text{lesion\_side} = \begin{cases} \text{both} & |LI| < \text{threshold} \\ \text{left} & LI \geq \text{threshold} \\ \text{right} & LI \leq -\text{threshold} \end{cases}$$

Il valore standard in letteratura per "bilaterale" è **|LI| < 0.20**. Non è l'unica convenzione possibile (alcuni protocolli fMRI usano soglie diverse per z-score di attivazione), ma è quella più diffusa per un LI calcolato su conteggio di voxel/volume, il caso rilevante qui (maschera binaria, non mappa continua).

---

# Parte 2 — Le sfumature geometriche

## 4. Coordinate world, non indice di voxel grezzo

Il conteggio $L$/$R$ non si fa sull'indice di voxel (`i < shape[0]/2`) ma sulla **coordinata world** derivata dall'affine dell'immagine (`_hemisphere_masks`, `src/features/lesion.py`): `world_x = affine[0,0] * i + affine[0,3]`. Motivo: due maschere con la stessa shape possono avere origini leggermente diverse (visto empiricamente su questo stesso repo — un template di riferimento con origine a `-91` e una maschera di esempio a `-90`, un voxel di scarto), quindi un taglio a metà shape sposterebbe la midline reale di un voxel per chi non è esattamente allineato. La coordinata world è invariante a questo.

## 5. Orientamento RAS, il piano di midline esatto

Le maschere del progetto sono in `MNI152NLin6Asym`, orientamento **RAS** (verificato via `nib.aff2axcodes` sul template di riferimento) — l'asse x del mondo cresce verso destra, quindi world-x negativo = sinistra, positivo = destra, **world-x = 0 è esattamente la midline sagittale**. Nessun ricampionamento comune serve per questo calcolo: basta l'affine proprio di ogni maschera nativa.

Il piano esatto di midline (un'unica fetta di voxel, quella con world-x più vicino a 0) **non appartiene a nessun lato** — esclusa da entrambi i conteggi, non arbitrariamente assegnata a uno dei due. Per la griglia di riferimento del progetto (`182×218×182` @ 1mm) questo esclude esattamente `218×182 = 39676` voxel, una singola fetta sagittale — verificato empiricamente.

## 6. Il caso limite: `laterality_index` indefinito

Un soggetto con **zero voxel di lesione su entrambi i lati** (lesione confinata interamente al piano di midline, o — non atteso per un soggetto ST reale, ma non escluso dal codice — nessuna lesione) produce `laterality_index = NaN`, un caso di dominio legittimo (`code_standards.md` §0), non un errore. Il soggetto resta con `lesion_side` vuoto, mai classificato a forza. Verificato su dati reali: 3 soggetti su 1448 nel set di calibrazione (§ 8).

## 7. Validazione della geometria dell'affine

`_hemisphere_masks` non assume ciecamente che il primo asse di voxel sia l'asse sinistra-destra: solleva `ValueError` se la prima riga dell'affine ha un termine fuori diagonale (rotazione/shear — il calcolo assumerebbe erroneamente che `world_x` dipenda solo dall'indice del primo asse) o se `nib.aff2axcodes` non etichetta quell'asse come `R`/`L` (un affine degenere o corrotto). Non un caso mai osservato sui dati reali del progetto — tutti in griglia MNI standard, assiale-allineata — ma un controllo esplicito piuttosto che un'assunzione silenziosa.

---

# Parte 3 — Lo stato reale in NEMESIS

## 8. La calibrazione vera (28-09-26)

Eseguita con `src/pipeline/calibrate_lesion_side_threshold.py` sui 5 dataset che hanno `lesion_side` clinico in `assets/metadata/participants.csv` (`lesion_side_source == "clinical"`): `UNIPD/WashU`, `UNIPD/PSP`, `UKLFR/stroke_UKLFR`, `UKE/WAKEUP_acute`, `UKE/SFB936_ses01` (quest'ultimo onboardato lo stesso giorno — la nota di `docs/dev/metadata.md` di sessioni precedenti parlava di "4 dataset", ora sono 5).

**1445 soggetti** utilizzabili (3 esclusi, `laterality_index` indefinito — § 6). Distribuzione etichette vere: 816 `left`, 605 `right`, 24 `both`.

| Soglia | Accuratezza | Corretti |
|---|---|---|
| 0.20 (default letteratura) | **97.4%** | 1407/1445 |
| 0.36 (ottimo su questi dati, grid search 0.00–0.60, passo 0.02) | 97.5% | 1409/1445 |

La differenza (+2 soggetti su 1445) non giustifica scostarsi dalla convenzione standard — usare 0.36 rischierebbe di overfittare sui soli 24 esempi di `both` disponibili. **Decisione in vigore: 0.20.**

Matrice di confusione a soglia 0.20 (righe = etichetta clinica, colonne = predizione geometrica):

| vero \ predetto | left | right | both |
|---|---:|---:|---:|
| left | 807 | 8 | 1 |
| right | 7 | 597 | 1 |
| both | 14 | 7 | **3** |

## 9. Il limite noto: la classe "bilaterale"

`left`/`right` sono classificati correttamente in oltre il 98% dei casi. **`both` è il punto debole**: solo 3/24 riconosciuti a qualunque soglia ragionevole nell'intervallo testato (0.00–0.60) — un vero bilaterale tende comunque a pendere leggermente da un lato nel conteggio voxel puro (asimmetrie di segmentazione, forma della lesione), quindi una soglia globale unica non isola bene questa classe rara (24/1445 = 1.7% del set di calibrazione). Non è un bug della soglia scelta: nessuna soglia testata fa sensibilmente meglio su questa classe specifica.

## 10. Cosa succede oggi, per dataset

Il lato geometrico è attribuito da `compute_lesion_metadata.py` per **ogni** soggetto con maschera e per ogni griglia dichiarata (`lesion_side_1mm`, `lesion_side_2mm` in `assets/metadata/lesion_metadata.csv`), indipendentemente da quale sia il suo dato clinico. `enrich_metadata.py` ne copia una griglia nel registro (`lesion_metadata.lesion_side_from`, in produzione `lesion_side_2mm`) **solo** dove la risoluzione clinica ha lasciato la cella vuota, marcando `lesion_side_source = "geometric"` — vedi `docs/guides/metadata.md`. L'ambito è la lista `datasets` di `config/pipelines/compute_lesion_metadata.json`: tutti gli 8 dataset ST del progetto sono coperti.

- **UCL-UK, PASPORT, UNIPD/NEMESIS_T0**: mai avuto `lesion_side` clinico — ogni soggetto ammesso riceve il fallback geometrico.
- **WashU, PSP, UKLFR, UKE/WAKEUP_acute, UKE/SFB936_ses01**: quasi completi clinicamente — il fallback copre solo le celle residue vuote (~230 soggetti tra WashU/PSP, verificato in `docs/dev/metadata.md`).

## 11. Riferimento rapido

- Config: `config/pipelines/compute_lesion_metadata.json` → `side_threshold`, `grids`, `correct_out_of_brain`. In `config/pipelines/enrich_metadata.json` → `lesion_metadata.lesion_side_from`, che sceglie quale griglia alimenta il registro.
- Codice: `src/features/lesion.py` (`compute_lesion_metadata`, `_laterality_index`, `_hemisphere_masks`, `lesion_side_from_laterality_index`).
- Calibrazione: `src/pipeline/calibrate_lesion_side_threshold.py --grid <nome>` — legge `laterality_index_<grid>` dal csv e non apre nessuna maschera, quindi ricalibrare su un'altra griglia è un cambio di argomento.

**Attenzione: la calibrazione qui sopra vale per la griglia a 2 mm.** La stessa soglia è applicata anche a 1 mm, dove non è verificata. Non è ovvio che trasferisca: il piano mediano escluso da entrambi gli emisferi è spesso 1 mm su una griglia e 2 mm sull'altra (la griglia a 1 mm ha 91 fette a sinistra e 90 a destra, quella a 2 mm 45 e 45), quindi per una lesione quasi tutta mediana i due indici non sono interscambiabili. Finché non si esegue `--grid 1mm`, `lesion_side_1mm` è indicativa.
- Architettura del registro: `docs/dev/metadata.md`. Guida utente: `docs/guides/metadata.md`.
- Decisione registrata: `.claude/history/methods_changelog.md`, 28-09-26.
