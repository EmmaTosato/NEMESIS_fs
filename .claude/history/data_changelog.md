# Changelog dei dati

Cosa è successo ai dati sotto `data/` — trasferimenti, potature, ripristini, spostamenti, correzioni.

**Perché esiste**: `data/` è gitignored, quindi `git log` non sa niente di cosa gli è successo. La storia del *codice* sta in git e non va duplicata qui; questo file copre solo ciò che git non può raccontare.

**Cosa NON va qui**: lo stato attuale dei dati (quello sta in `docs/guides/datasets.md`, sempre al presente) e i pattern di errore generalizzabili (`.claude/lessons_learned.md`).

Voci in ordine cronologico inverso.

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
