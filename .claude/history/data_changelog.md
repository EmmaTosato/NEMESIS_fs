# Changelog dei dati

Cosa è successo ai dati sotto `data/` — trasferimenti, potature, ripristini, spostamenti, correzioni.

**Perché esiste**: `data/` è gitignored, quindi `git log` non sa niente di cosa gli è successo. La storia del *codice* sta in git e non va duplicata qui; questo file copre solo ciò che git non può raccontare.

**Cosa NON va qui**: lo stato attuale dei dati (quello sta in `docs/guides/datasets.md`, sempre al presente) e i pattern di errore generalizzabili (`.claude/lessons_learned.md`).

Voci in ordine cronologico inverso.

---

## 23-09-26 — `UNIPD/NEMESIS_T0`: subject id grezzi rinominati in forma canonica

**Perché era necessario**: i subject id grezzi di NEMESIS_T0 (`sub-p001`, `sub-c002`, ...)
non rispettano la convenzione `sub-<ST|PD|GM><SITE>[HC]<NUM>` che `group_of()`
(`src/retrieval/dataset.py`) richiede — ogni modulo che scopre i soggetti scandendo
`sub-*` direttamente (`src/features/lesion.py`, `sdc.py`, `subject_discovery.py`)
chiama `group_of()` senza condizioni e solleverebbe `ValueError` sul primo soggetto.

**Cosa è cambiato**: script one-off `scripts/rename_nemesis_t0_subjects.py` (dry-run di
default, `--execute` per scrivere). Copre l'unione dei `sub-p*` visti nel tsv grezzo e su
disco (82 id distinti: 72 in comune, 6 solo nel tsv, 4 solo su disco — non un semplice
sottoinsieme). Numerazione: `UNIPD` è un contatore unico condiviso da WashU/PSP/PASPORT
(0001-0585 già occupati, verificato su disco senza buchi riusati), quindi i nuovi id
continuano da 0586. Assegnati in ordine crescente del numero originale.

Eseguito su:
- **76 cartelle** rinominate sia sotto `manual_masks/` che sotto `sdc/` (`sub-p001`→
  `sub-STUNIPD0586` ... `sub-p090`→`sub-STUNIPD0666`, più `sub-p123`→`sub-STUNIPD0667`),
  ogni file dentro ciascuna cartella rinominato di conseguenza (prefisso del nome file).
- **`data/clinical_connectome/metadata_tsv/participants_NEMESIS_T0.tsv`**: colonna
  `participant_id` riscritta in forma canonica per le 82 righe `sub-p*`; l'id grezzo
  originale preservato in una nuova colonna `participant_id_dmp` (stesso schema già usato
  dal tsv di `UKE_SFB`). Aggiunte anche **4 righe mancanti** (`sub-p010`, `sub-p047`,
  `sub-p076`, `sub-p077`) per soggetti che avevano la scansione su disco ma nessuna riga
  clinica nel tsv originale — età/sesso/gruppo lasciati vuoti, nessun dato clinico noto
  per loro. Le **6 righe rimaste solo-tsv** (`sub-p032`, `sub-p033`, `sub-p053`,
  `sub-p081`, `sub-p084`, `sub-p123`) non hanno scansione sul disco: nessuna azione
  possibile, restano escluse dal join di `populate_metadata.py` (comportamento atteso,
  riportato nel report del run, non un errore).
- I 22 `sub-c*` (controlli sani) **non toccati**: nessun dato su disco per loro (0
  cartelle), e comunque fuori scope per `group_filter: ["ST"]` come ogni altro HC del
  progetto (`docs/dev/metadata.md`).

**Conseguenza ancora vera oggi**: `config/registry/metadata_sources.json` ha già la voce
`UNIPD/NEMESIS_T0`, ma il dataset **non è ancora** in `datasets` di
`config/pipelines/populate_metadata.json` — `assets/metadata/participants.csv` non
riflette ancora questi 76 (o 72, al netto dei 6 solo-tsv) soggetti finché quella run non
viene lanciata.

---

## 23-09-26 — Aggiunti 2 dataset nuovi, sostituite le lesion mask di 6 dataset esistenti

**2 dataset nuovi aggiunti a `data/clinical_connectome/derivatives/`**: UKE/SFB936_ses01
(56 soggetti) e UNIPD/NEMESIS_T0 (76 soggetti), copiati da `sdc_download/lesion/` —
`manual_masks/<sub>/anat/` (solo lesion mask, `res-1` rimosso) + `sdc/<sub>/` (disconnectome
map con `res-1` mantenuto, 2 mapstats.tsv, 30 CSV parcellati per atlante). Output SDC già
completo per entrambi, nessun run di `compute_sdc.py` necessario. **Non ancora in-scope**:
assenti da `docs/guides/datasets.md`, `config/registry/`, `assets/metadata/participants.csv`
— onboarding non fatto, `participants.tsv` reali non ancora recuperati (a carico dell'utente).

**Lesion mask sostituite per 6 dataset esistenti** (`manual_masks/*/anat/`, vecchi file
eliminati prima della sostituzione, sorgente una copia `rsync` fresca in `sdc_download/`,
`res-1` rimosso): UCL-UK/UCLStrokeData 4119→4119, UKE/WAKEUP_acute 451→451,
UKLFR/stroke_UKLFR 697→705, UNIPD/PASPORT 83→83, UNIPD/PSP 168→168, UNIPD/WashU 202→195.

UKLFR non è un semplice swap 1:1: persi 24 soggetti con maschera manuale ma senza dato SDC,
guadagnati 32 nuovi. WashU perde 7 soggetti senza sostituto disponibile (accettato
esplicitamente dall'utente) — verificato che nessuno dei 7 è HC (nessun soggetto HC esiste
per WashU in `manual_masks/`, `features/`, `sdc/` né in `participants.csv`, solo ST).

`sdc_download/lesion/`: i 2 dataset nuovi mantengono la propria copia (sorgente di verità,
non spostata); i 6 dataset solo-maschera sono stati spostati (`mv`), quindi `sdc_download`
non ne contiene più i file — dettagli di rinomina in `sdc_download/lesion/README.md`.

Conseguenza ancora vera oggi: `assets/metadata/participants.csv` non riflette ancora questi
cambiamenti (né i 2 dataset nuovi, né il delta di UKLFR/WashU) — va rigenerato. Risoluzione
voxel di UKLFR/WashU passata da 1.5mm/2.0mm nativo a 1mm (stessa fonte dell'SDC) — ha esposto
una fragilità di `reference_template_path` risolta lo stesso giorno, vedi `project_changelog.md`
23-09-26.

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
