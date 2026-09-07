# Changelog dei metodi

Decisioni su **come analizziamo**: proxy per variabili mancanti, feature calcolate, soglie, metodi adottati o abbandonati — con le alternative scartate e il perché.

**Cosa NON va qui**: i risultati di un esperimento (`docs/experiments/`), i parametri di una singola run (`runs.csv`), il funzionamento corrente di una pipeline (`docs/`, sempre al presente).

Voci in ordine cronologico inverso.

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
