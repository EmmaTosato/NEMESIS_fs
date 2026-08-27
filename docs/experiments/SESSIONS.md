# Sessions — clinical_connectome

Narrativa umana su cosa significa ogni sessione (il `session_name`/`s1.1` usato da
`dim_reduction.py`/`clustering.py` per taggare i propri run) — scritta a mano, mai generata.
Spostato qui da `data/SESSIONS.md` il 15-08-26 (`docs/dev/clustering_migration_plan.md` §6):
narrativa di progetto, non dato grezzo/derivato, quindi appartiene a `docs/` non a `data/`.

Formato a chiavi fisse per riga (una riga per chiave, valore dopo `:`) invece della prosa
libera di prima — resta scrivibile/leggibile a mano, ma diventa anche regex-abile da
`scripts/build_dim_reduction_strategies_csv.py`. 3 chiavi per sessione, in quest'ordine:

- `Starting date`: `DD-MM` o vuoto se non ancora iniziata.
- `Datasets`: elenco separato da virgola, stessi nomi usati da `config/pipelines/retrieval_*.json`.
- `Modality`: descrizione libera in una riga sola (niente sotto-elenchi — se servono più voci,
  elencarle nella stessa riga separate da virgola, come già fa `Datasets`).

Non aggiungere una quarta chiave senza aggiornare anche il parser dello script.

## Session 1.1

- Starting date: 21-07
- Datasets: UNIPD/WashU, UNIPD/PASPORT, UNIPD/PSP, UKLFR/stroke_UKLFR
- Modality: Lesion in 2D matrix volumetric

## Session 1.2

- Starting date:
- Datasets: UNIPD/WashU, UNIPD/PASPORT, UNIPD/PSP, UKLFR/stroke_UKLFR, UCL-UK StrokeData
- Modality: Lesion in 2D matrix volumetric
- Notes: one dataset more (UCL)

## Session 2.1

- Starting date: 26-08
- Datasets: UNIPD/WashU, UNIPD/PASPORT, UNIPD/PSP, UKLFR/stroke_UKLFR
- Modality: SDC

## Session 3.1

- Starting date: 26-07
- Datasets: UNIPD/WashU
- Modality: Features (FC matrices, stacked in 2D)
