# Il flusso delle pipeline — riferimento tecnico

Come le pipeline si passano i dati, chi è la fonte di verità di cosa, e quali invarianti il codice fa rispettare. Per i comandi e l'ordine di lancio c'è la guida [`docs/guides/pipeline_order.md`](../guides/pipeline_order.md); i dettagli di ogni modulo stanno nei suoi file in `docs/dev/`.

## Livelli e fonti di verità

| Livello | Dove | Lo scrivono | Lo leggono |
|---|---|---|---|
| Dati grezzi | `data/clinical_connectome/` (gitignored) | a mano, da EBRAIN | `populate_metadata`, `compute_*_metadata`, le matrici, `mask_fc` |
| Registro e misure | `assets/metadata/` (in git) | `populate_metadata`, `compute_lesion_metadata`, `compute_sdc_metadata`, `enrich_metadata`, `build_excluded_subjects` | `enrich_metadata`, le matrici, i colori dei grafici, i notebook |
| Matrici | `data/derived/` (gitignored) | `build_lesion_matrix`, `build_sdc_matrix`, `mask_fc`, `build_fc_matrix` | `dim_reduction`, `clustering` |
| Risultati | `results/` (gitignored) | `dim_reduction`, `clustering` | `embedding_app`, i notebook |

Ogni dato nasce **in un solo posto**: i volumi delle lesioni in `lesion_metadata.csv`, il carico di disconnessione in `sdc_metadata.csv`, la lista di chi resta fuori in `excluded_subjects.csv`. `participants.csv` ne tiene una copia dichiarata (`enrich_metadata`), quindi va riallineato quando una fonte cambia.

`participants.csv` è la **fonte di verità delle variabili per l'analisi**: lo leggono i colori dei grafici (`embedding_coloring.color_values`), il pannello "Descrizione del cluster" (età, sesso, istruzione, NIHSS), `calibrate_lesion_side_threshold` (le etichette cliniche del lato), e i notebook `lesion_analysis`, `clustering_evaluation` e `sdc_analysis`. Il lettore è `src/utils/participants.py::load_participants_registry`, che interpreta i flag `has_*` come booleani veri.

## Due grafi di dipendenze

Le pipeline dipendono l'una dall'altra in due modi diversi.

**Per eseguire** (un file mancante o incoerente fa fallire la run):

| Pipeline | Per eseguire richiede |
|---|---|
| `populate_metadata` | i dati grezzi |
| `compute_lesion_metadata` | le maschere (non legge il registro) |
| `compute_sdc_metadata` | `participants.csv` (per `has_sdc`) e le mappe SDC |
| `enrich_metadata` | `participants.csv`, `lesion_metadata.csv`, `sdc_metadata.csv`, i tsv grezzi |
| `build_excluded_subjects` | `lesion_metadata.csv` e `participants.csv` (validazione) |
| `build_lesion_matrix`, `build_sdc_matrix` | `participants.csv` e `excluded_subjects.csv` |
| `mask_fc`, `build_fc_matrix` | solo dati grezzi (poi l'una l'output dell'altra) |
| `dim_reduction` | una matrice |
| `clustering` | una matrice, oppure un run di `dim_reduction` |

- Il registro serve alle matrici anche quando le maschere si cercano su disco: `load_excluded_subjects` valida l'intero file delle esclusioni contro il registro.
- `compute_lesion_metadata` non legge il registro; `compute_sdc_metadata` sì, per sapere chi ha `has_sdc`.
- Il ramo FC (`mask_fc` → `build_fc_matrix`) non legge né il registro né la lista delle esclusioni: sceglie i soggetti dal filtro di gruppo, derivato dal nome (`src/utils/subject_ids.py::group_of`).

**Per interpretare** (la run parte, ma il risultato è povero senza):
- `enrich_metadata` alimenta tutto ciò che legge una variabile dal registro. In `dim_reduction` un colore non risolvibile produce un `WARNING` e il grafico viene saltato; l'embedding è già salvato. In `embedding_app` lo stesso caso solleva un errore.
- Un soggetto assente dal registro non è un errore per i colori: viene disegnato come mancante e il conteggio è loggato.

## Un ordine circolare: la calibrazione del lato

`calibrate_lesion_side_threshold` legge l'indice di lateralità da `lesion_metadata.csv` e le etichette cliniche di `lesion_side` da `participants.csv` (scritte da `enrich_metadata`). Il suo risultato è la soglia `side_threshold` di `compute_lesion_metadata`. Per ricalibrarla l'ordine è:

```
compute_lesion_metadata → enrich_metadata → calibrate_lesion_side_threshold
   → nuova soglia nel config di compute_lesion_metadata
   → compute_lesion_metadata (overwrite: true) → enrich_metadata (overwrite: true)
```

La soglia in uso è già calibrata: il giro si rifà solo se cambiano griglia o dati.

## Artefatti e convenzioni

- **Cartella di matrice:** `matrix.npy`, `metadata.csv` (almeno `subject_id`, `dataset`), `manifest.json`, `config.md`, più array accessori (`non_constant_mask.npy` per la lesione, `tract_names.npy` per la streamline). `save_matrix` scrive in una cartella temporanea e la rinomina: un crash non lascia mai una cartella a metà. `load_matrix` richiede `manifest.json`.
- **Nome:** `<gg-mm>_<sessione>`, con la sessione nella forma `sX.Y-<formato>` (vocabolario chiuso, mai `_` al suo interno: `run_log` divide l'id sul primo `_`). `dim_reduction` e `clustering` aggiungono un tag derivato dai parametri (`_m_euclidean_nc2`); il ramo FC aggiunge l'`atlas_combo`.
- **Registro delle sessioni:** `docs/experiments/data_sessions.md`, a mano. Nessun codice lo legge né confronta `session_name` con `input_path`.
- **Output di `dim_reduction`:** `results/<modalità>/dim_reduction/{production,tuning}/<metodo>/...`; produzione e tuning non si incontrano mai su disco. **Output di `clustering`:** `results/<modalità>/clustering/{production,tuning}/<metodo>/<riduzione>/...`, dove `<riduzione>` è il metodo che ha prodotto l'embedding in ingresso (`raw` per una matrice non ridotta).

## Esclusioni e coorti

`excluded_subjects.csv` ha una riga per (soggetto, scope), con `reason` e `value`. Gli scope sono `all`, `lesion`, `sdc-parcellated`, `sdc-voxelwise`, `sdc-streamline`: un soggetto può essere inutilizzabile in una rappresentazione e valido nelle altre (uno zero nel CSV streamline può essere una misura vera, non un dato rotto).

- Ogni matrice chiede `load_excluded_subjects(path, scope)` e riceve le righe `all` più quelle del suo scope. Lo scope è un argomento obbligatorio: un valore predefinito farebbe ereditare in silenzio le esclusioni di un'altra matrice.
- Un soggetto con una riga `all` non può averne una più stretta: le due si contraddirebbero.
- La coorte di una matrice è dunque: soggetti del registro ammessi dal filtro di gruppo, meno le righe `all` e quelle del suo scope. Lesione e voxelwise condividono le righe `all`, quindi hanno la stessa coorte salvo righe specifiche; la streamline ne ha una più piccola quando ci sono righe `sdc-streamline`.
- Il ramo FC non usa questa lista.

## Semantica di `overwrite`

Lo stesso nome, con significati vicini ma non identici, in ogni pipeline:

| Pipeline | `false` | `true` |
|---|---|---|
| `populate_metadata` | tiene le righe esistenti **intatte, flag `has_*` compresi**, e aggiunge solo i soggetti nuovi (con le colonne di `enrich` vuote) | ricalcola le sue sette colonne (`OWN_COLUMNS`) per tutti i soggetti e riporta invariate quelle estranee; un soggetto non più ammesso viene rimosso, con le sue colonne di `enrich`, e finisce nel report |
| `compute_lesion_metadata`, `compute_sdc_metadata` | se il csv esiste, la run esce subito | ricalcola e sostituisce il csv |
| `enrich_metadata` | **append**: scrive solo le celle vuote | **riscrittura**: sostituisce ogni cella in scope |
| `build_excluded_subjects` | aggiunge righe senza toccare le esistenti | ricostruisce il csv dal solo config |
| matrici, `dim_reduction`, `clustering` | rifiutano una cartella di output già esistente (`FileExistsError`) | la sostituiscono per intero |

`enrich_metadata` ha in più `assets/metadata/participants_protected.json` (`columns`, `subjects`): le celle la cui colonna o il cui soggetto è elencato non vengono mai scritte, in nessuno dei due modi. Il file è validato contro il registro e contro le colonne che il config scrive (`_check_write_rules`): un refuso solleva, perché altrimenti non proteggerebbe nulla in silenzio. In append, un valore esistente diverso da quello appena calcolato resta, ma è contato a `WARNING` per colonna. Con `overwrite: true`, una cella vuota nella fonte svuota quella del registro senza avviso: ciò che esiste solo nel registro va protetto. Dettagli in [`metadata.md`](metadata.md).

## Controlli che fanno fallire la run

- **Join stretti** tra registro e csv di misure, nei due sensi: un soggetto con maschera (o disconnettoma) senza riga nel csv, una riga per un soggetto sconosciuto, o per uno con il flag `has_*` falso.
- **`load_excluded_subjects`** valida l'intero file, non solo lo scope richiesto: id inesistenti o ripetuti, `dataset` in disaccordo col registro, motivo o scope non registrati, `value` non numerico. Un file assente solleva; con la sola intestazione vale "nessuna esclusione, deliberatamente".
- **`clustering` con `reduced_data: true`** verifica che `viz_embedding_path` venga dallo stesso metodo e dagli stessi parametri dell'embedding in ingresso, tranne `n_components` (`_require_matching_reduction_run`): un grafico dei cluster su una geometria diversa sarebbe fuorviante.
- **I loader dei config** validano ogni campo prima di leggere un dato; i campi obbligatori mancanti o di tipo sbagliato sollevano.
- **I dry-run:** `compute_lesion_metadata`, `compute_sdc_metadata`, `enrich_metadata` e `build_excluded_subjects` accettano `--dry-run` (controlli e report, nessuna scrittura); le altre pipeline no.

## Registri dei parametri: stato mutabile

`config/registry/params_reduction.json`, `params_reduction_sdc.json` e `params_clustering.json` contengono i valori dell'ultima run che li ha toccati, non dei default. Una griglia lasciata da una run su dati di un tipo (una metrica binaria su una matrice grezza) può essere invalida per dati di un altro tipo (un embedding continuo). Prima di ripetere un tuning, si confronta la griglia con la colonna `params` del `runs_tuning.csv` di quella run, che è l'unica traccia di cosa fosse davvero in griglia.

## Provenienza

- **Ogni run di pipeline:** `logs/<pipeline>/` (log grezzo), `summaries/<pipeline>/` (report) e, per le matrici, `dim_reduction` e `clustering`, `runs.csv` (produzione) e `runs_tuning.csv` (tuning).
- **Ogni cartella di output:** il suo `config.md` riporta i parametri usati.
- **Le decisioni:** `.claude/history/` (`data_changelog.md`, `methods_changelog.md`, `project_changelog.md`).

## Esecuzione

In locale si lancia direttamente (`python -m src.pipeline.<nome> --config ...`); su cluster ogni pipeline ha il suo `jobs/run_<nome>.sh`, e la cartella `logs/slurm/<nome>/` deve esistere prima di `sbatch`. Le due forme eseguono lo stesso comando.
