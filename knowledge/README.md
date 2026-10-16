# knowledge/

Diviso per funzione, non per argomento.

| Cartella | Cosa contiene | Chi la scrive |
|---|---|---|
| [`notes/`](notes/) | Le nostre sintesi: metodologia, guide di tuning, note di neuroimaging, riassunti dei paper | noi, a mano |
| [`papers/`](papers/) | Le fonti estratte da PDF (docling), una cartella per paper | l'estrazione, sola lettura |

## `notes/`

- [`dim_reduction_clustering/`](notes/dim_reduction_clustering/) — metodi impiegati, guide di tuning, survey della letteratura, clustering dopo riduzione dimensionale
- [`neuroimaging/`](notes/neuroimaging/) — lateralità e localizzazione della lesione, ricampionamento, mascheramento della FC
- [`stroke_literature/`](notes/stroke_literature/) — `summaries_core.md` e `summaries_related.md` (riassunto per paper), `scope_by_category.md` (scopo di ogni paper centrale per macro-categoria)

## `papers/`

[`papers/index.md`](papers/index.md) elenca tutti i paper. Tre gruppi: `stroke_core/` (riferimento di NEMESIS), `stroke_related/` (affini), `methods/` (riduzione dimensionale e clustering, più slide e pagine web).

Dentro ogni cartella il testo è il file `.md` (di solito `<Autore> et al - <Anno>.md`, in alcune `markdown/_full.md`); `manifest.json` e `figures.json` descrivono l'estrazione. Non tutte le cartelle hanno l'estrazione completa.

Aggiungere un paper: cartella nel gruppo giusto di `papers/`, riga in `papers/index.md`.
