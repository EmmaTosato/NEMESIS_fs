# Guida all'Atlas Building (Creazione Atlanti)

Questa guida descrive l'uso della pipeline `build_combined_atlas.py`, che è un pre-requisito opzionale necessario solo se intendi analizzare le lesioni raggruppandole per macro-aree anatomiche (Matrix Building di Categoria Parcellated).

**Script**: `src/pipeline/build_combined_atlas.py`
**Configurazione**: `config/pipelines/build_combined_atlas.json`

## Esecuzione (Locale vs Server/SLURM)

**1. Esecuzione sul Server (con SLURM)**
Sul server, lancia lo script inviandolo alla coda tramite SLURM (così non si interrompe se chiudi la connessione). Trovi lo script in `jobs/`:
```bash
sbatch jobs/run_build_combined_atlas.sh
```

**2. Esecuzione in Locale (senza SLURM)**
Dal tuo PC locale, dopo aver attivato l'ambiente `nemesis`, lancia la pipeline direttamente da terminale:
```bash
python -m src.pipeline.build_combined_atlas --config config/pipelines/build_combined_atlas.json
```
## Cosa significa "Atlas Building"?

Un "Atlante Cerebrale" in neuroimaging è un file immagine 3D (un volume NIfTI) in cui a diverse zone del cervello sono assegnati valori interi diversi (es. tutto ciò che vale 1 è la corteccia visiva primaria, tutto ciò che vale 2 è l'ippocampo, lo zero è lo sfondo vuoto). Serve da "stampino" per dividere il cervello in sezioni logiche.

In letteratura neuroscientifica, capita spesso di dover unire due atlanti diversi perché uno copre bene la corteccia esterna e l'altro descrive in dettaglio le strutture profonde.
Questo script fa esattamente questo: **fonde in un solo file due atlanti separati**.

Nel caso del nostro progetto NEMESIS, fonde:
1. L'Atlante **Corticale Glasser MMP** (360 regioni sulla superficie del cervello).
2. L'Atlante **Sottocorticale Harvard-Oxford** (limitatamente a 12 specifiche regioni profonde: talamo, caudato, putamen, pallido, ippocampo e amigdala per emisfero destro e sinistro).

Il risultato è un atlante univoco e completo da **372 regioni**, costruito ispirandosi al metodo pubblicato nello studio *Thiebaut de Schotten et al. 2020*.

**Nota sullo stato**: questa combinazione Glasser+Harvard-Oxford è stata costruita e usata **una sola volta**, in via esplorativa. Non è (ancora) la parcellazione anatomica adottata in modo definitivo dal progetto per la matrice di lesione — chi la ripropone in altri documenti dovrebbe trattarla come un'opzione disponibile, non come lo standard di fatto.

---

## Dettaglio dei Parametri JSON

Ecco cosa significano le impostazioni nel file `config/pipelines/build_combined_atlas.json`:

- **`cortical_atlas_path`**: `(Stringa)` Il percorso locale dell'atlante per la corteccia cerebrale. Solitamente punta al file `assets/atlases/MNI_Glasser_HCP_v1.0.nii.gz`.
- **`subcortical_atlas_path`**: `(Stringa)` Il percorso locale dell'atlante per le zone profonde. Punta al file `assets/atlases/HarvardOxford-sub-maxprob-thr25-2mm.nii.gz`.
- **`output_atlas_path`**: `(Stringa)` Come e dove vuoi chiamare il file combinato 3D in uscita. Es: `"assets/atlases/glasser_hcp_harvardoxford_subcortical_372.nii.gz"`.
- **`output_label_table_path`**: `(Stringa)` Dove salvare la legenda in formato CSV. Questo CSV accoppierà il valore numerico al nome reale della regione. Es: `"assets/atlases/glasser_hcp_harvardoxford_subcortical_372_labels.csv"`.
- **`overwrite`**: `(Booleano)` Imposta a `true` se l'atlante esiste già e vuoi ricrearlo forzando la sovrascrittura.

---

## Cosa succede durante l'esecuzione

Quando lanci lo script:
1. Il codice apre entrambi gli atlanti e verifica che condividano la stessa geometria (stessa "risoluzione" e "allineamento nello spazio").
2. Prende il blocco corticale e vi incastra le 12 strutture sottocorticali prese dal secondo atlante, scalando automaticamente gli indici in modo che le prime 360 aree siano corticali e le successive (361-372) siano sottocorticali, per evitare conflitti o sovrapposizioni matematiche.
3. Se ci sono sovrapposizioni spaziali (un millimetro del cervello che risulta appartenere sia alla corteccia che a un'area profonda), il conflitto viene sempre risolto **dando priorità alla corteccia**. Il programma ti avviserà comunque tramite un messaggio di log su quanti voxel sono andati in sovrapposizione.

## File in Uscita (Output)

- **Il file NIfTI** (`.nii.gz`): il volume 3D matematico. Questo sarà il file da fornire alla voce `atlas_path` nella configurazione del *Matrix Building*.
- **La tabella delle Etichette** (`.csv`): un file leggibile su Excel contenente colonne strutturate (es. `Value: 361`, `Name: L_Thalamus`, `Hemisphere: Left`, `Source: harvard_oxford_subcortical`).
- **Report di Costruzione**: in `summaries/build_combined_atlas/`, verrà generato un mini-documento di riepilogo per tracciare storicamente l'operazione.
