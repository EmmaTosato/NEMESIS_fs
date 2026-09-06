# Resampling delle maschere di lesione — regola, sfumature e stato reale in NEMESIS

> Fonte: Bisogno et al. 2025 (*Brain Communications*, in `knowledge/nemesis/`), FSL (`flirt -applyxfm` + `fslmaths -thr 0.5 -bin`), `nilearn.image.resample_to_img`. Implementazione: `src/features/lesion.py` (`_needs_resample`/`_load_and_binarize_lesion`), `src/sdc/resample.py`, `src/features/sdc.py`. Misure empiriche: questo documento, § Parte 3.

Il documento è in tre parti:

- **[Parte 1 — La regola](#parte-1--la-regola)**: quale interpolazione si usa e perché, per tipo di dato. *Il perché concettuale.*
- **[Parte 2 — La sfumatura del downsampling](#parte-2--la-sfumatura-del-downsampling)**: cosa fa davvero `nearest` quando riduce la risoluzione, l'alternativa classica, e l'interazione con `binarize_threshold`. *Il perché delle scelte tecniche.*
- **[Parte 3 — Lo stato reale in NEMESIS](#parte-3--lo-stato-reale-in-nemesis)**: quali coorti vengono davvero ricampionate, con quali numeri misurati, e cosa comporta cambiare la regola oggi. *I fatti su cui poggia la decisione in vigore.*

---

# Parte 1 — La regola

## 1. Perché serve un resampling

Le maschere di lesione arrivano dai vari centri già normalizzate in MNI152NLin6Asym, ma **non sulla stessa griglia di voxel**: risoluzioni native diverse (1mm, 1.5mm, 2mm) e, in casi isolati, bounding box diversi. Per impilarle in una matrice pazienti × voxel serve una griglia comune, fissata esplicitamente da `reference_template_path` (oggi un soggetto WashU a 2mm — scelta esplicita e non derivata dai dati, vedi `docs/dev/lesion_matrix.md`).

## 2. La regola va per tipo di dato, non per direzione

Non conta se si sta ingrandendo o riducendo la risoluzione: conta **cosa rappresentano i valori**.

| Tipo di dato | Interpolazione | Perché |
|---|---|---|
| Maschere binarie, atlanti, segmentazioni | **`nearest`** | I valori sono etichette, non quantità. Qualunque altra interpolazione produce valori che non appartengono al set di etichette |
| T1, BOLD, mappe di probabilità, disconnectome | `linear` o `continuous` | Il dato è continuo per natura, la media tra due valori vicini è essa stessa un valore valido |

Il caso limite che rende la regola evidente è l'**atlante**: interpolare linearmente tra il voxel etichettato `12` e il voxel etichettato `47` produce `~30`, cioè una regione anatomica che non c'entra nulla con nessuna delle due. Per una maschera binaria il danno è più contenuto ma della stessa natura: si ottengono valori in `(0, 1)` che non sono né "lesionato" né "sano" e vanno risogliati per tornare a significare qualcosa.

## 3. Riscontro in letteratura

Non è una convenzione interna al progetto. Bisogno et al. 2025, che lavora sulla stessa coorte, descrive esattamente questo passaggio:

> *"The normalization matrix was then applied to the lesion mask through a nearest neighbour interpolation function."*

Lo stesso criterio è già applicato altrove nel repo per lo stesso motivo — vedi `knowledge/neuroimaging/fc_lesion_masking.md` (riallineamento lesione → griglia dell'atlante, `nearest`).

## 4. Come il repo applica la regola

Coerentemente, in tre punti indipendenti:

- `src/features/lesion.py::_load_and_binarize_lesion` — maschera binaria, interpolazione configurabile (`resample_interpolation`), oggi `nearest`.
- `src/sdc/resample.py::resample_lesion_if_needed` — maschera binaria, `nearest` **hardcoded**, con la motivazione nel docstring (*"any other interpolation would invent values that are neither 0 nor 1"*). Attenzione: qui la griglia di destinazione è quella canonica **1mm**, non i 2mm della lesion matrix — è un resampling con scopo diverso (rendere l'input digeribile a `bcb-lf-preprocess`, vedi `docs/debugging/debug_23_07_26.md`), non lo stesso passaggio.
- `src/features/sdc.py::_load_disconnectome_voxels` — campo continuo, **mai binarizzato**, interpolazione tipicamente `linear`/`continuous` (`docs/guides/sdc_matrix_building.md`).

---

# Parte 2 — La sfumatura del downsampling

## 5. `nearest` in downsampling non fa una media

Quando si scende di risoluzione (es. 1mm → 2mm) ogni voxel di destinazione copre 8 voxel sorgente. `nearest` ne prende **uno solo**, quello geometricamente più vicino al centro, e scarta gli altri 7. Non è un'aggregazione, è un **campionamento**.

Per una lesione di dimensioni ordinarie l'effetto è trascurabile e non sistematico (misure in [§ 9](#9-quanto-pesa-davvero-il-downsampling-misura-su-uke)). Per una lesione molto piccola può azzerarla del tutto: se la lesione non contiene nessuno dei punti campionati, sparisce.

## 6. L'alternativa classica: soglia di maggioranza

Il modo standard di downsamplare una maschera binaria quando si vuole conservare il volume è a due passi:

1. ricampionare con **`linear`** → ogni voxel di destinazione riceve la *frazione* del proprio volume occupata dalla lesione (partial volume);
2. **risogliare a 0.5** → si tiene il voxel se la lesione ne occupa più della metà.

È la ricetta FSL (`flirt -applyxfm` seguito da `fslmaths -thr 0.5 -bin`) ed è pratica comune in lesion-symptom mapping. Conserva meglio il volume delle lesioni piccole, al prezzo di introdurre una regola di decisione in più.

## 7. L'interazione con `binarize_threshold` (importante)

La pipeline binarizza **dopo** il resample:

```python
# src/features/lesion.py::_load_and_binarize_lesion
if _needs_resample(img, reference_img):
    img = resample_to_img(img, reference_img, interpolation=resample_interpolation, ...)
data = img.get_fdata() > binarize_threshold
```

La conseguenza è che i due campi non sono indipendenti:

- con **`nearest`** i valori restano esattamente `0` o `1`, quindi `> 0.5` non scarta nulla: **`binarize_threshold` è un no-op**;
- con **`linear`**/`continuous` i valori diventano frazioni in `[0, 1]` e lo stesso `binarize_threshold: 0.5` diventa la soglia di maggioranza del § 6.

In altre parole la pipeline è già scritta per lo schema partial-volume; oggi quel meccanismo semplicemente non si attiva. Il campo non è morto (`code_standards.md` §5) — è condizionato all'altro.

> Nota: `continuous` (spline di ordine 3 in nilearn) può produrre overshoot ai bordi, cioè valori leggermente `< 0` o `> 1`. Per una maschera binaria `linear` è la scelta più prudente delle due.

---

# Parte 3 — Lo stato reale in NEMESIS

## 8. Quali coorti vengono davvero ricampionate

Griglie native verificate direttamente sui file (06-09-26), contro la griglia di riferimento `(91, 109, 91)` @ 2mm:

| Coorte | N | Griglia nativa | Ricampionata? |
|---|---|---|---|
| UNIPD/WashU | 202 | 2mm `(91,109,91)` | no |
| UCL-UK/UCLStrokeData | 4119 | 2mm `(91,109,91)` | no |
| UNIPD/PASPORT | 83 | 1mm `(182,218,182)` | **sì** |
| UNIPD/PSP | 168 | 1mm `(182,218,182)` | **sì** |
| UKLFR/stroke_UKLFR | 697 | 1.5mm `(121,145,121)`, 2 soggetti `(104,125,90)` | **sì** |
| UKE/WAKEUP_acute | 451 | 1mm `(182,218,182)` | **sì** |

Il downsampling con `nearest` **non è un caso nuovo**: riguarda già 948 soggetti presenti in `s1.1-vol` e `s1.2-vol` (PASPORT + PSP + UKLFR). In `s1.1-vol` erano 948 su 1150, cioè l'**82% della coorte**; in `s1.2-vol`, diluiti da UCL-UK, sono 948 su 5269 (18%).

## 9. Quanto pesa davvero il downsampling — misura su UKE

Misurato sui 451 soggetti UKE, confrontando il volume ottenuto a 2mm con quello atteso (`voxel_1mm / 8`):

| Statistica | Valore |
|---|---|
| Mediana del rapporto | **1.001** |
| Intervallo 5–95% | 0.89 – 1.13 |
| Soggetti azzerati | **2** su 451 |

Il rapporto mediano ~1 dice che `nearest` **non introduce bias sistematico** di volume: la dispersione è simmetrica attorno al valore atteso. I due soggetti azzerati sono `sub-STUKE0201` (3 voxel a 1mm = 0,003 ml) e `sub-STUKE0146` (16 voxel = 0,016 ml): lesioni sotto qualunque soglia di rilevanza clinica, non un artefatto di allineamento.

⚠️ **Una riga tutta a zero non viene segnalata da nessuna parte.** Il controllo in `src/features/lesion.py` solleva un errore solo se si azzerano *tutti* i soggetti (controllo in aggregato, deliberato: un singolo soggetto a zero è un caso di dominio legittimo). Due righe tutte-zero entrano quindi nella matrice senza warning nel report né nel log. A valle non sono innocue: con metrica `jaccard`/`dice` la distanza tra due vettori tutti-zero è indefinita e scikit-learn la restituisce come `0`, quindi i due soggetti risulterebbero identici tra loro.

## 10. I due soggetti UKLFR non canonici

`sub-STUKLFR0253` e `sub-STUKLFR0464` hanno shape `(104,125,90)` invece di `(121,145,121)`. Non è uno spazio diverso: stesso voxel 1.5mm, stesso orientamento, **bounding box ritagliato** con origine traslata (`[76.5, -110.5, -48.5]` invece di `[90, -126, -72]`, cioè 9 voxel tolti sull'asse x).

Vengono gestiti correttamente perché `resample_to_img` lavora in coordinate mondo, e perché `_needs_resample` confronta **shape *e* affine**, non la sola shape — un controllo sulla sola risoluzione li avrebbe considerati "già allineati" (sono 1.5mm come gli altri 695) e li avrebbe impilati traslati.

## 11. Conseguenza pratica sulla scelta

Poiché il downsampling riguarda già 948 soggetti storici, **cambiare `nearest` → `linear` non è un aggiustamento locale a una coorte nuova**: riscriverebbe le righe di PASPORT, PSP e UKLFR, rendendo la sessione risultante non confrontabile con `s1.1-vol`/`s1.2-vol`.

**Decisione in vigore: `nearest`.** È lo standard per il tipo di dato (§ 2-3), è la regola con cui sono state costruite tutte le sessioni esistenti, non introduce bias di volume misurabile (§ 9), e il costo noto — le lesioni sotto ~0,02 ml — è sotto la soglia di rilevanza clinica.

Se in futuro si volesse passare allo schema partial-volume del § 6, va fatto **ricostruendo anche le sessioni precedenti**, non solo la nuova, e va misurato prima quanto cambiano i 948 soggetti storici.

## 12. Riferimento rapido

- Config: `config/pipelines/build_lesion_matrix.json` → `resample_interpolation`, `binarize_threshold`, `reference_template_path`.
- Codice: `src/features/lesion.py` (`_needs_resample`, `_load_and_binarize_lesion`, `_AFFINE_ATOL`).
- Guida utente: `docs/guides/matrix_building.md`. Architettura: `docs/dev/lesion_matrix.md`.
- Caso continuo (SDC): `docs/guides/sdc_matrix_building.md`, `docs/dev/sdc_matrix.md`.
