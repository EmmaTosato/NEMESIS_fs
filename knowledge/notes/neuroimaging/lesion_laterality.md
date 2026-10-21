# Lato della lesione calcolato geometricamente: regola, calibrazione, stato in NEMESIS

Come il repo attribuisce a ogni maschera un indice di lateralità (`laterality_index_<g>`) e un lato (`lesion_side_<g>`: `left`/`right`/`both`), su ogni griglia `<g>` (`1mm`, `2mm`). Codice: `src/features/lesion.py` (`_hemisphere_masks`, `_laterality_index`, `lesion_side_from_laterality_index`, chiamate da `_metrics_on_grid`); calibrazione: `src/pipeline/calibrate_lesion_side_threshold.py`. I passaggi comuni a tutte le metriche (allineamento, binarizzazione, correzione fuori dal cervello) e la notazione sono in [`lesion_metrics.md`](lesion_metrics.md) §1.

Il documento è in tre parti:

- **[Parte 1 — La regola](#parte-1--la-regola)**: formula, soglia, da dove vengono.
- **[Parte 2 — La geometria](#parte-2--la-geometria)**: coordinate mondo, piano mediano, casi limite.
- **[Parte 3 — Lo stato in NEMESIS](#parte-3--lo-stato-in-nemesis)**: calibrazione, numeri, limiti.

---

# Parte 1 — La regola

## 1. Perché serve un lato geometrico

`lesion_side` è prima di tutto un dato clinico, letto dal tsv del dataset quando quella colonna esiste. Tre degli otto dataset (UCL-UK, PASPORT, `UNIPD/NEMESIS_T0`) non la hanno, e negli altri alcune celle sono vuote. La maschera esiste per ogni soggetto con lesione, quindi il lato si deriva dalla maschera. Nel registro `participants.csv` il lato geometrico riempie **solo** le celle che il dato clinico lascia vuote (`lesion_side_source = "geometric"`); la forzatura per dataset `geometric_override_datasets` è spenta (`docs/guides/metadata.md`). In `lesion_metadata.csv`, invece, il lato geometrico è calcolato per tutti i soggetti, a prescindere dal dato clinico.

## 2. L'indice di lateralità

Sia $\ell^{*}_g$ la maschera binaria corretta sulla griglia $g$ ([`lesion_metrics.md`](lesion_metrics.md) §1.2) e $x(v)$ la coordinata mondo sinistra-destra del voxel $v$ (§4). I voxel di lesione dei due emisferi sono

$$L_g = \sum_{v} \ell^{*}_g(v)\,\mathbb{1}[x(v) < 0], \qquad R_g = \sum_{v} \ell^{*}_g(v)\,\mathbb{1}[x(v) > 0]$$

e l'indice è

$$LI_g = \frac{L_g - R_g}{L_g + R_g}, \qquad LI_g = \text{NaN se } L_g + R_g = 0$$

Codice: `_laterality_index(left_voxels, right_voxels)`, con `left_voxels = (lesion & left_mask).sum()` in `_metrics_on_grid`. $LI_g \in [-1, 1]$: $+1$ lesione tutta a sinistra, $-1$ tutta a destra, vicino a 0 distribuita in modo simile sui due lati. Adimensionale; $L_g$ e $R_g$ sono voxel della griglia $g$.

È la forma classica del laterality index, $LI = (Q_{LH} - Q_{RH})/(Q_{LH} + Q_{RH})$, definita in letteratura fMRI per quantità non negative, il cui caso più comune è il numero di voxel per emisfero [1]; lo stesso schema è implementato nel LI-toolbox [2]. **Applicare l'indice a una maschera di lesione** invece che a una mappa di attivazione è un adattamento del progetto: un paper peer-reviewed che lo definisca per le maschere di lesione, **fonte non trovata**. L'adattamento è validato sui dati del progetto, contro le etichette cliniche (§8).

## 3. La soglia di bilateralità

Con soglia $t$ (`side_threshold`, 0,20 in produzione):

$$\text{lesion\_side}_g = \begin{cases} \text{both} & |LI_g| < t \\ \text{left} & LI_g \geq t \\ \text{right} & LI_g \leq -t \end{cases}$$

Codice: `lesion_side_from_laterality_index`: `both` se `abs(LI) < t`, altrimenti `left` se `LI > 0`, altrimenti `right`. Per $t > 0$ coincide con la formula. Due casi limite:

- con $t = 0$ (ammesso dal config, che valida $t \in [0, 1]$) un indice esattamente 0 risulta `right`, non `both`;
- un indice `NaN` non arriva mai alla funzione: `_metrics_on_grid` scrive `NaN` anche nel lato, e la funzione solleva `ValueError` se lo riceve.

**Da dove viene 0,20.** In letteratura fMRI, con l'indice scalato in $[-1, 1]$, la soglia di dominanza emisferica è "usually set to 0.2", con valori 0,1, 0,15, 0,25 e 0,3 usati in altri lavori [1]. $|LI| \geq 0{,}2$ equivale a dire che il lato maggiore ha almeno 1,5 volte i voxel dell'altro [1]:

$$LI \geq t \iff \frac{L}{R} \geq \frac{1 + t}{1 - t} = 1{,}5 \quad (t = 0{,}2)$$

Usare 0,20 per le lesioni è una **scelta del progetto**, verificata contro le etichette cliniche (§8; [`.claude/history/methods_changelog.md`](../../../.claude/history/methods_changelog.md), voce del 28-09-26 "`lesion_side` geometrico: soglia di bilateralità 0.20, dal protocollo standard di letteratura").

---

# Parte 2 — La geometria

## 4. Coordinate mondo della griglia, non della maschera

Il lato si conta **sulla griglia**, non sul file originale. Ogni maschera viene prima portata sulla griglia attraverso il proprio affine ([`lesion_metrics.md`](lesion_metrics.md) §1.3: le maschere hanno tre header, LAS +90, RAS −90, RAS −91); poi `_hemisphere_masks` calcola le due metà dall'affine del template della griglia:

$$x(i) = a_{00}\, i + a_{03}$$

dove $i$ è l'indice del primo asse e $a_{00}, a_{03}$ i termini della prima riga dell'affine. Se l'asse è orientato `L` il segno è invertito, così $x > 0$ è sempre l'emisfero destro anatomico. Tagliare l'array a metà della shape sarebbe sbagliato: il template a 1 mm non è simmetrico (x da −91 a +90 mm) e le maschere su disco hanno origini e orientamenti diversi.

## 5. Il piano mediano

I voxel con $x = 0$ esatto non appartengono a nessuno dei due emisferi: sono esclusi da $L_g$ e da $R_g$, non assegnati a un lato. È lo stesso principio per cui in fMRI le regioni mesiali sono di solito escluse dal calcolo del laterality index [1].

| Griglia | Fette a sinistra ($x<0$) | Fette a destra ($x>0$) | Piano $x=0$ escluso |
|---|---|---|---|
| 1 mm | 91 (x da −91 a −1) | 90 (x da +1 a +90) | 1 fetta, $218 \times 182 = 39\,676$ voxel |
| 2 mm | 45 (x da −90 a −2) | 45 (x da +2 a +90) | 1 fetta, $109 \times 91 = 9\,919$ voxel |

Il piano escluso è spesso 1 mm su una griglia e 2 mm sull'altra, quindi per una lesione quasi tutta mediana i due indici non sono interscambiabili.

## 6. Casi limite: indice indefinito

$LI_g$ è `NaN`, e il lato vuoto, quando $L_g + R_g = 0$. Succede in tre casi:

| Caso | Soggetti nel csv attuale, griglia 2 mm |
|---|---|
| maschera vuota | `sub-STUKLFR0671` |
| lesione persa nel sottocampionamento a 2 mm, o tutta fuori dal cervello e azzerata dalla correzione | `sub-STUKE0146`, `sub-STUKE0201` (persa a 2 mm); `sub-STUNIPD0558` (fuori dal cervello) |
| lesione tutta sul piano mediano | `sub-STUCLUK0362`, `sub-STUCLUK1284`, `sub-STUCLUK1739` (5, 6 e 15 voxel, sede `infratentorial`) |

A 1 mm l'indice è indefinito per il solo `sub-STUKLFR0671`: le tre lesioni mediane di UCL-UK hanno $LI_{1\text{mm}} = -1$, perché a 1 mm i loro voxel fuori dal piano mediano stanno tutti a destra. Sono casi di dominio, non errori (`code_standards.md` §0).

## 7. Controllo della geometria dell'affine

`_hemisphere_masks` solleva `ValueError` se la prima riga dell'affine del template ha un termine fuori diagonale (rotazione o shear: $x$ non dipenderebbe più dal solo primo indice) o se `nib.aff2axcodes` non etichetta il primo asse come `R` o `L`. I template in uso sono assiali e RAS, quindi il controllo non scatta: protegge da un template cambiato.

---

# Parte 3 — Lo stato in NEMESIS

## 8. La calibrazione

`src/pipeline/calibrate_lesion_side_threshold.py --grid <g>` legge `laterality_index_<g>` da `assets/metadata/lesion_metadata.csv` (nessuna maschera aperta) e lo confronta con le etichette cliniche di `assets/metadata/participants.csv` (`lesion_side_source == "clinical"`) per le soglie da 0,00 a 0,60, passo 0,02. I soggetti con indice indefinito sono esclusi. I dataset con etichetta clinica sono cinque: `UNIPD/WashU`, `UNIPD/PSP`, `UKLFR/stroke_UKLFR`, `UKE/WAKEUP_acute`, `UKE/SFB936_ses01`.

Sui file attuali, a 2 mm: 1448 soggetti etichettati, 3 con indice indefinito, **1445** usati (816 `left`, 605 `right`, 24 `both`).

| Soglia | Accuratezza | Corretti |
|---|---|---|
| 0,20 (in uso) | **97,4%** | 1408/1445 |
| 0,28 (massimo della griglia di soglie) | 97,5% | 1409/1445 |

Matrice di confusione a 0,20 (righe = etichetta clinica, colonne = lato geometrico):

| clinico \ geometrico | left | right | both |
|---|---:|---:|---:|
| left | 807 | 8 | 1 |
| right | 7 | 598 | 0 |
| both | 14 | 7 | **3** |

A 1 mm, sugli stessi cinque dataset (1447 soggetti, PSP compresa): 97,4% a 0,20 (1409/1447), massimo 0,28. Escludendo PSP, le cui maschere a 1 mm sono frazionarie, sugli stessi 1350 soggetti 0,20 dà lo stesso lato a 1 mm e a 2 mm per tutti i 1350 ([`.claude/history/methods_changelog.md`](../../../.claude/history/methods_changelog.md), voce del 06-10-26 "Verifica del lato forzato (WashU) con test comportamentali; soglia a 1 mm verificata; calibrazione rifatta").

**Decisione in vigore: 0,20 su entrambe le griglie.** Lo scarto dal massimo è di un soggetto su 1445, e una soglia ottimizzata su 24 esempi di `both` rischia di adattarsi al campione.

## 9. Limiti

- **La classe `both` è debole.** A 0,20 il metodo riconosce 3 dei 24 `both` clinici; il massimo nella griglia di soglie è 7 su 24, a 0,58-0,60, al prezzo di classificare `both` molte lesioni unilaterali. Per 14 dei 24 la lesione sta quasi tutta da un lato ($|LI| \geq 0{,}9$, `docs/guides/metadata.md`): il `both` clinico e una maschera bilaterale non sono lo stesso fatto.
- **Inversioni piene.** 15 soggetti hanno lato clinico e geometrico opposti con $|LI| \geq 0{,}95$; nessuna soglia li corregge. Senza di loro l'accordo a 0,20 è 98,4% (`docs/guides/metadata.md`, sezione "Forzare il lato geometrico").
- **Lesioni infratentoriali.** L'indice attribuisce un lato anche a lesioni di tronco o cervelletto. I paper di riferimento del laboratorio riportano il lato come categoria e trattano tronco e cervelletto a parte: Corbetta et al. 2015 elencano tronco e cervelletto come categorie di sede proprie [3], Bisogno et al. 2021 contano separatamente 79 lesioni sinistre, 71 destre e 14 di cervelletto o tronco [4]. Chi confronta con quei lavori filtra con `location_infratentorial_2mm` ([`lesion_location.md`](lesion_location.md)).
- **Lato anatomico.** L'indice dice da che parte del piano mediano MNI sta la massa della lesione, non da che parte stanno i sintomi.
- **Nessuna regola quantitativa nei paper core.** Nei testi di Corbetta 2015 [3], Salvalaggio 2020 [5], Bisogno 2021 [4] e Talozzi 2023 [6] (in `knowledge/papers/stroke_core/`) il lato è riportato come emisfero colpito (es. "64 right hemispheres" [5]; percentuali per emisfero per coorte [6]), senza una regola numerica per attribuirlo da una maschera.

## 10. Cosa succede oggi, per dataset

`compute_lesion_metadata` calcola il lato per **ogni** soggetto con maschera e per ogni griglia (`lesion_side_1mm`, `lesion_side_2mm`). `enrich_metadata` ne copia una griglia nel registro (`lesion_metadata.lesion_side_from`, in produzione `lesion_side_2mm`) solo dove la risoluzione clinica ha lasciato la cella vuota.

- **UCL-UK, PASPORT, UNIPD/NEMESIS_T0**: nessun lato clinico, ogni soggetto riceve il lato geometrico.
- **WashU, PSP, UKLFR, UKE/WAKEUP_acute, UKE/SFB936_ses01**: il lato geometrico copre solo le celle cliniche vuote.

## 11. Riferimento rapido

- Config: `config/pipelines/compute_lesion_metadata.json` → `side_threshold`, `grids`, `correct_out_of_brain`; `config/pipelines/enrich_metadata.json` → `lesion_metadata.lesion_side_from`.
- Codice: `src/features/lesion.py` (`_metrics_on_grid`, `_hemisphere_masks`, `_laterality_index`, `lesion_side_from_laterality_index`).
- Calibrazione: `python -m src.pipeline.calibrate_lesion_side_threshold --grid <g> --datasets ...`.
- Architettura del registro: `docs/dev/metadata.md`. Guida: `docs/guides/metadata.md`.

## Fonti

1. Seghier ML (2008). Laterality index in functional MRI: methodological issues. *Magnetic Resonance Imaging* 26:594-601. https://doi.org/10.1016/j.mri.2007.10.010 — formula classica, conteggio dei voxel come quantità più comune, soglia "usually set to 0.2" (0,1-0,3 in altri lavori), regioni mesiali di solito escluse.
2. Wilke M, Lidzba K (2007). LI-tool: a new toolbox to assess lateralization in functional MR-data. *Journal of Neuroscience Methods* 163:128-136. https://doi.org/10.1016/j.jneumeth.2007.01.026
3. Corbetta M, Ramsey L, Callejas A, et al. (2015). Common behavioral clusters and subcortical anatomy in stroke. *Neuron* 85:927-941. https://doi.org/10.1016/j.neuron.2015.02.027
4. Bisogno AL, Favaretto C, Zangrossi A, et al. (2021). A low-dimensional structure of neurological impairment in stroke. *Brain Communications* 3:fcab119. https://doi.org/10.1093/braincomms/fcab119
5. Salvalaggio A, De Filippo De Grazia M, Zorzi M, Thiebaut de Schotten M, Corbetta M (2020). Post-stroke deficit prediction from lesion and indirect structural and functional disconnection. *Brain* 143:2173-2188. https://doi.org/10.1093/brain/awaa156
6. Talozzi L, Forkel SJ, Pacella V, et al. (2023). Latent disconnectome prediction of long-term cognitive-behavioural symptoms in stroke. *Brain* 146:1963-1978. https://doi.org/10.1093/brain/awad013
