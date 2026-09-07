# Matrici costruite — composizione e note di qualità

Una sezione per matrice prodotta da `build_lesion_matrix.py`/`build_sdc_matrix.py`/`build_fc_matrix.py`, con la sua composizione reale e le anomalie che un consumatore a valle (dim reduction, clustering) deve conoscere **prima** di interpretare un risultato.

Complementare, non sovrapposto, a:

- [`data_sessions.md`](../data_sessions.md) — cosa significa ogni sessione (coorte, modalità), scritto a mano
- [`data_employing.md`](../data_employing.md) — quale matrice alimenta quale run di dim reduction/clustering
- `runs.csv` in ogni `data/derived/<pipeline>/` — provenienza della singola run (parametri, output, timestamp)

Qui sta solo ciò che nessuno dei tre dice: **cosa c'è davvero dentro la matrice**.

---

## Convenzione: griglia 2mm per ogni matrice voxel-wise

Ogni matrice voxel-wise del progetto è costruita sulla stessa griglia **MNI152NLin6Asym a 2mm** (91×109×91), fissata da `reference_template_path` — oggi la maschera di `sub-STUNIPD0001` (WashU). Vale per `build_lesion_matrix.py` e per `build_sdc_matrix.py` in modalità `voxelwise`, con `resample_interpolation: "nearest"`.

Le sorgenti non sono tutte a 2mm: le maschere di lesione UKE e i `disconnectome-map` di ogni dataset sono a **1mm** (182×218×182, 7,2M voxel). Vengono quindi ricampionate al momento della costruzione della matrice, non prima.

**Perché 2mm.** A 1mm una matrice SDC voxel-wise su ~1570 soggetti sarebbe dell'ordine delle decine di GB, contro pochi GB a 2mm: la risoluzione piena non è trattabile in locale. In più la griglia comune rende le matrici lesionale e SDC **allineate voxel per voxel**, quindi direttamente confrontabili — che è il punto della rappresentazione multimodale.

**Cosa costa.** `nearest` campiona, non media: passando da 1mm a 2mm tiene 1 voxel su 8 e scarta gli altri. Su una maschera binaria di lesione questo può azzerare del tutto le lesioni più piccole (è successo — vedi s1.3-vol sotto). Su mappe di disconnessione continue l'effetto è più lieve, perché quei valori variano in modo graduale nello spazio e un campione è rappresentativo del suo intorno, ma resta una perdita reale.

## `lesion_matrix` — s1.3-vol (`data/derived/lesion_matrix/06-09_s1.3-vol`)

Matrice **5720 × 266418**, voxel-wise binaria (`uint8`), griglia 2mm, colonne costanti scartate (`non_constant_mask.npy`).

| Dataset | Soggetti |
| :--- | ---: |
| UCL-UK/UCLStrokeData | 4119 |
| UKLFR/stroke_UKLFR | 697 |
| UKE/WAKEUP_acute | 451 |
| UNIPD/WashU | 202 |
| UNIPD/PSP | 168 |
| UNIPD/PASPORT | 83 |

Nessun soggetto escluso da `group_filter` (tutti ST).

### ⚠️ 2 righe interamente nulle

`sub-STUKE0146` e `sub-STUKE0201` (entrambi UKE/WAKEUP_acute) hanno `lesion_volume_voxels = 0`: sono in matrice come vettori tutti-zero, indistinguibili da "nessuna lesione".

Le maschere di partenza sono valide ma minuscole — 16 e 3 voxel a 1mm. Il ricampionamento sulla griglia 2mm del template con `nearest` campiona invece di mediare, e a quella dimensione la lesione può non intercettare alcun punto della griglia. È perdita di segnale attesa su lesioni sotto-risoluzione, non un difetto della pipeline.

**I due soggetti restano in matrice**: 2 su 5720 non giustificano un filtro in fase di build (decisione 07-09-26). Chi usa questa matrice li esclude a valle se gli serve — `sub-STUKE0146` e `sub-STUKE0201`, riconoscibili da `lesion_volume_voxels == 0`.

Attenzione però sotto metriche binarie (`jaccard`, `dice`, quelle di default sul lesionale): una riga tutta-zero ha distanza indefinita o massima da ogni altra, quindi può comparire come outlier isolato in un embedding senza motivo apparente. Contesto completo in [`.claude/history/data_changelog.md`](../../../.claude/history/data_changelog.md) (voce 06-09-26).

Il fenomeno è nuovo in s1.3-vol: s1.2-vol (stessi dataset meno UKE) non ha righe nulle, e la sua lesione più piccola sopravvive con 1 voxel.
