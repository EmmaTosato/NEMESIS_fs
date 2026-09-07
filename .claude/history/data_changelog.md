# Changelog dei dati

Cosa è successo ai dati sotto `data/` — trasferimenti, potature, ripristini, spostamenti, correzioni.

**Perché esiste**: `data/` è gitignored, quindi `git log` non sa niente di cosa gli è successo. La storia del *codice* sta in git e non va duplicata qui; questo file copre solo ciò che git non può raccontare.

**Cosa NON va qui**: lo stato attuale dei dati (quello sta in `docs/guides/datasets.md`, sempre al presente) e i pattern di errore generalizzabili (`.claude/lessons_learned.md`).

Voci in ordine cronologico inverso.

---

## 07-09-26 — `sub-STUKLFR0671`: mappa di disconnessione vuota nonostante una lesione grande

Emerso costruendo `sdc_matrix` s2.2-vol (prima run voxel-wise): il soggetto entra in matrice come riga interamente nulla.

Non è un artefatto del ricampionamento. Il file sorgente
`UKLFR/stroke_UKLFR/sdc/sub-STUKLFR0671/..._res-1_desc-disconnectome.nii.gz` ha
**0 voxel non nulli su 7.221.032**, mentre la sua maschera di lesione ne ha
**56.785**. Una lesione di quelle dimensioni che produce zero disconnessione non è
plausibile: è output degenere di BCBToolKit, non una proprietà del soggetto.

È l'unico caso tra i 1570 soggetti ammessi. Non è stato ricalcolato (`compute_sdc.py`
gira solo sul cluster) né rimosso dalla matrice.

Nota: lo stesso soggetto compare in `docs/dev/sdc_matrix.md` come l'esempio verificato
di chi *ha* una maschera registrata pur mancando dal `manual_masks/` locale — quel
fatto resta vero e non c'entra con questo. Qui il problema è a valle: la maschera c'è,
l'SDC è stato calcolato, ma il risultato è vuoto.

Conseguenza ancora vera oggi: chi usa `07-09_s2.2-vol` deve escluderlo, o accettare una
riga a zero indistinguibile da "nessuna disconnessione" — con metriche di distanza è un
outlier garantito.

---

## 06-09-26 — `lesion_matrix` s1.3-vol: 2 soggetti UKE entrano come righe tutte-zero

`build_lesion_matrix.py` (run `06-09_s1.3-vol`, 5720 soggetti) ha ammesso in matrice
`sub-STUKE0146` e `sub-STUKE0201` con `lesion_volume_voxels = 0`: righe interamente
nulle, indistinguibili da "nessuna lesione" pur essendo pazienti stroke.

Causa: sono le due lesioni piu' piccole della coorte. Le maschere raw sono valide
(1mm isotropo, 182x218x182, valori binari 0/1) ma contengono rispettivamente **16 e
3 voxel**. Il template di riferimento e' a 2mm (91x109x91, la maschera WashU
`sub-STUNIPD0001`) e `resample_interpolation` e' `nearest`, che campiona invece di
mediare: una lesione da 3 voxel a 1mm non sopravvive al ricampionamento se non cade
su un punto della griglia 2mm. Nessun altro dataset era finora sceso sotto questa
soglia, quindi il caso non si era mai presentato: s1.2-vol (5269 soggetti, gli stessi
dataset meno UKE) ha 0 righe nulle, con volume minimo 1 voxel (`sub-STUNIPD0208`) —
verificato ricalcolando le somme di riga da `25-08_s1.2-vol/matrix.npy`, che non ha
la colonna `lesion_volume_voxels` (aggiunta dopo quella run).

Non e' un bug di codice: e' perdita di segnale legittima del downsampling su lesioni
sotto-risoluzione. **Non e' stata presa alcuna decisione** su come trattarli — i due
soggetti restano in `06-09_s1.3-vol/matrix.npy`. Alternative sul tavolo, nessuna
adottata: escluderli in fase di build (il builder SDC ha gia' un guard-rail
equivalente, esclude esplicitamente chi non ha lesion mask registrata invece di
inserire una riga a zero; quello lesionale no), oppure tenerli e filtrarli a valle.

Conseguenza ancora vera oggi: chiunque usi `06-09_s1.3-vol` per dim reduction o
clustering ha 2 righe identicamente nulle nella matrice. Con metriche binarie
(jaccard/dice) una riga tutta-zero ha distanza indefinita o massima da chiunque —
vanno gestite prima, non dopo aver visto un outlier strano nell'embedding.

---

## 05-09-26 — `populate_metadata.py`: conteggi FC sbagliati per cartella potata

Prima run di `scripts/populate_metadata.py`: ha scritto `has_features=False` per 192 soggetti WashU che le FC ce l'hanno, perché `UNIPD/WashU/features/` era potata al campione di 10 e una scansione del disco non vede dentro un `.tar.gz`.

Corretto decomprimendo l'archivio, rilanciando con `overwrite=true` (`has_features` da 10 → 169 ST) e ricomprimendo. Da qui la scelta di **non** far leggere il manifest alla pipeline (la potatura è una misura temporanea di spazio locale, non una proprietà del progetto): la correzione resta manuale e documentata in `docs/dev/metadata.md`.

Introdotti nello stesso giorno i manifest `<nome>_archive_subjects.tsv` in ogni cartella potata, e corretto il comando di ripristino nei `README_ARCHIVE.md` (diceva `tar -xzf <archivio> -C .` ma l'archivio sta un livello sopra la cartella, quindi non lo trovava mai).

## 04-09-26 — `participants.tsv` accorpati in `metadata_tsv/`

I 6 `participants.tsv` sono stati spostati da `derivatives/<centro>/<coorte>/participants.tsv` a `data/clinical_connectome/metadata_tsv/participants_<SITO>.tsv`. La corrispondenza nome-file ↔ dataset non è più derivabile meccanicamente (`participants_UCL.tsv` ↔ `UCL-UK/UCLStrokeData`), da cui il registry esplicito `config/registry/metadata_sources.json`.

## 04-09-26 — SDC: appiattito il livello `dwi/`

Fino a questa data la copia locale annidava ogni file sotto `sdc/{subject_id}/dwi/{subject_id}_...` — una cartella `dwi/` fabbricata dal layout locale, non presente alla sorgente. Tutti i file dei 1602 soggetti nei 5 dataset sono stati spostati su di un livello (`sdc/{subject_id}/{subject_id}_...`) e le `dwi/` vuote rimosse.

## 03-09-26 — Onboarding di `UKE/WAKEUP_acute`

**SDC**: primo trasferimento via `rsync` risultato incompleto/corrotto — 221/451 soggetti con tutti i file a 0 byte. Scoperto e bloccato prima di toccare `derivatives/` grazie a un controllo di stabilità della dimensione nel tempo, **non** da un errore esplicito (rsync non ha segnalato nulla). Rifatto con `scp -r` diretto da `/data/corbetta/Clinical_connectome/features/Clinical_connectome_stroke/UKE/WAKEUP_acute/lesion`, verificato al 100% (451 × 35 file, nessuno a 0 byte, dimensione stabile su ricontrolli ripetuti) prima di sostituire la cartella.

**Maschere di lesione**: UKE non ha un oggetto `lesion` sul server, quindi nessun retrieval è possibile. Il `lesion-map` di ogni soggetto (la lesione ricampionata che BCBToolKit usa come input) è stato copiato sotto `manual_masks/{subject_id}/anat/` e **rinominato** togliendo `res-1` — necessario perché `Dataset.resolve()` cerca il template esatto, non basta che il file esista. L'originale è stato poi rimosso da `sdc/{subject_id}/` per non duplicarlo. Non riproducibile rilanciando una pipeline: solo ripetendo gli stessi passi a mano.

**SDC per gli altri 4 dataset**: aggiunti i `disconnectome-map` (.nii.gz voxel-wise) che mancavano; fino a quel momento la copia locale conteneva solo i CSV parcellati (`disconnectome-LF`/`lesion-LF`).

## 01-09-26 — `manual_masks/` ripristinate per intero

Le 5 cartelle `manual_masks/` (WashU, PSP, PASPORT, UKLFR, UCL-UK), potate il 26/08, sono state riportate al set completo. Restano potate solo `UNIPD/WashU/features/` e `data/derived/features/masked_fc/`.

## 26-08-26 — Prima potatura delle copie locali

`scripts/archive_local_raw_data.py` ha ridotto a 10 soggetti campione le 5 `manual_masks/`, `UNIPD/WashU/features/` e `data/derived/features/masked_fc/`, comprimendo il resto in `.tar.gz` verificati accanto a ciascuna cartella.
