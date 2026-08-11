# Guida all'Atlas Building (Creazione Atlanti)

Questa guida descrive l'uso della pipeline `build_combined_atlas.py`, un pre-requisito **opzionale** necessario solo se si intende analizzare le lesioni raggruppandole per macro-aree anatomiche (*Matrix Building di Categoria Parcellated*).

- **Script**: `src/pipeline/build_combined_atlas.py`
- **Configurazione**: `config/pipelines/build_combined_atlas.json`

---

## Esecuzione

### 1. Sul Server (tramite SLURM)
L'esecuzione tramite SLURM previene interruzioni dovute alla chiusura della connessione.
```bash
sbatch jobs/run_build_combined_atlas.sh
```

### 2. In Locale
Dal PC locale, dopo aver attivato l'ambiente `nemesis`, lanciare direttamente da terminale:
```bash
python -m src.pipeline.build_combined_atlas --config config/pipelines/build_combined_atlas.json
```

---

## Cos'è l'Atlas Building?

Un "Atlante Cerebrale" in neuroimaging è un file immagine 3D (un volume NIfTI) in cui a diverse zone del cervello sono assegnati valori interi univoci (es. `1` = corteccia visiva primaria, `2` = ippocampo, `0` = sfondo). Funge da "stampino" per dividere il cervello in sezioni logiche.

In neuroscienze è spesso necessario unire atlanti diversi per combinare dettagli superficiali e profondi. **Questo script fonde in un solo file due atlanti separati:**

1. **Atlante Corticale Glasser MMP**: 360 regioni sulla superficie del cervello.
2. **Atlante Sottocorticale Harvard-Oxford**: limitatamente a 12 strutture profonde (talamo, caudato, putamen, pallido, ippocampo e amigdala per emisferi dx e sx).

**Risultato**: Un atlante univoco e completo da **372 regioni** (basato sul metodo *Thiebaut de Schotten et al. 2020*).

> **Nota Operativa**: Questa combinazione è stata costruita e usata *una sola volta* in via esplorativa. Non è lo standard definitivo del progetto, ma un'opzione disponibile.

---

## Dettaglio Parametri JSON

Impostazioni in `config/pipelines/build_combined_atlas.json`:

| Parametro | Tipo | Descrizione | Esempio / Default |
| :--- | :--- | :--- | :--- |
| **`cortical_atlas_path`** | *Stringa* | Percorso locale atlante corticale. | `"assets/atlases/MNI_Glasser_HCP_v1.0.nii.gz"` |
| **`subcortical_atlas_path`** | *Stringa* | Percorso locale atlante sottocorticale. | `"assets/atlases/HarvardOxford-sub-maxprob-thr25-2mm.nii.gz"` |
| **`output_atlas_path`** | *Stringa* | Percorso/nome del volume 3D combinato in uscita. | `"assets/atlases/glasser_hcp_harvardoxford_subcortical_372.nii.gz"` |
| **`output_label_table_path`** | *Stringa* | Percorso/nome della legenda CSV che accoppia valore numerico a nome regione. | `"assets/atlases/glasser_hcp_harvardoxford_subcortical_372_labels.csv"` |
| **`overwrite`** | *Booleano* | Se `true`, forza la sovrascrittura se il file esiste già. | `false` |

---

## Flusso di Esecuzione

1. **Verifica Geometria**: Controlla che gli atlanti condividano stessa risoluzione e allineamento spaziale.
2. **Fusione e Indici**: Inserisce le 12 strutture sottocorticali nell'atlante corticale mantenendo la convenzione Glasser:
   - Emisfero Sx Corticale: **1-180** ➔ Sottocorticale Sx: **181-186**
   - Emisfero Dx Corticale: **1001-1180** ➔ Sottocorticale Dx: **1181-1186**
   Gli indici non sono continui, evitando conflitti tra le due metà.
3. **Risoluzione Conflitti**: Se vi è sovrapposizione spaziale, la priorità è **sempre data alla corteccia** (con segnalazione a log dei voxel sovrapposti).

---

## Output Generato

L'esecuzione produce:

- **File NIfTI (`.nii.gz`)**: Il volume 3D matematico, da usare come `atlas_path` nel *Matrix Building*.
- **Tabella Etichette (`.csv`)**: Legenda strutturata con colonne come `Value`, `Name`, `Hemisphere` (con `L`/`R`), e `Source`.
- **Report di Costruzione**: Un documento di riepilogo salvato in `summaries/build_combined_atlas/`.
