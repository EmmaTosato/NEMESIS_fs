# Esperimenti

Un file per **sessione**: una coorte, una matrice, e tutto quello che ci è stato fatto sopra, in ordine — dim reduction, clustering, decisioni.

| Sessione | Data | Modalità | Soggetti | Dove è arrivata |
|---|---|---|---|---|
| [s1.1-vol](s1.1-vol.md) | 21-07 | Lesione voxel-wise | 1150 | Clustering di produzione, 6 opzioni di k |
| [s1.2-vol](s1.2-vol.md) | 27-07 | Lesione voxel-wise | 5269 | Clustering di produzione, 6 opzioni di k |
| [s1.3-vol](s1.3-vol.md) | 06-09 | Lesione voxel-wise | 5720 | Solo matrice, mai usata a valle |
| [s1.4-vol](s1.4-vol.md) | 07-10 | Lesione voxel-wise | 5845 | Clustering di produzione, 79 run |
| [s2.1-schaefer-200-tian-s2](s2.1-schaefer-200-tian-s2.md) | 26-08 | SDC parcellata | 1119 | Clustering di tuning, nessuna produzione |
| [s2.2-vol](s2.2-vol.md) | 07-09 | SDC voxel-wise | 1570 | Clustering di produzione, 8 opzioni di k |
| [s2.4-vol](s2.4-vol.md) | 07-10 | SDC voxel-wise, voxel fuori dal brain non azzerati | 5845 | Clustering di produzione, 30 run |
| [s2.4-vol](s2.4-vol.md#seconda-tornata-16-10--voxel-fuori-dal-brain-azzerati) | 16-10 | SDC voxel-wise, voxel fuori dal brain azzerati | 5845 | Clustering di produzione, 29 run su 30 (dim reduction e clustering di tuning completi); PCA: tuning, nc30 e nc42, 2 run di clustering |
| [s2.4-stream](s2.4-stream.md) | 07-10 | SDC streamline, 87 tratti | 5831 | Clustering di produzione, 19 run |

Due sessioni non hanno un file: **s2.3-stream** (mai costruita con quel nome, rifatta come s2.4-stream sulla lista di esclusioni attuale) e la **sessione 3** (FC), che non è ancora partita.

Due viste d'insieme:

- [**lineage.md**](lineage.md) — da quale sessione deriva quale, cosa cambia tra l'una e l'altra, e quali coorti si possono confrontare tra loro.
- [**pipelines.md**](pipelines.md) — quali pipeline ha attraversato ogni matrice, dalla costruzione al clustering di produzione.

## Il nome di una sessione

`sX.Y-<formato>`: track e coorte, più un suffisso di formato obbligatorio. Il vocabolario è chiuso e mai con un `_` dentro (`src/utils/run_log.py::append_run_log_entry` ricava `session` splittando `run_id` sul primo `_`).

| Tag | Significato |
|---|---|
| `vol` | Matrice voxel-wise, non parcellata — lesione (s1.x) o disconnettoma (s2.x) |
| `stream` | Streamline per tratto (`LF-lesion_atlas-yeh_hcp1065_streamline.csv`), un valore per tratto |
| `schaefer-200-tian-s2` | Parcellata sull'atlante Schaefer-200 + Tian S2 |
| `Yan100TianS1Buckner7N` … `Yan400TianS3Buckner7N` | FC parcellata su uno dei 12 atlas_combo Yan/Tian/Buckner, un tag per combo |

**Soggetti** = righe effettive della matrice, non quanti ne esistono su disco: per l'SDC un soggetto entra solo se ha *sia* la maschera registrata *sia* l'output SDC richiesto.

## Cosa sta qui e cosa no

Qui: cosa è stato provato, cosa si è visto, cosa si è deciso e perché.

Altrove:

- **Le tabelle complete** di ogni tuning: `tuning_results.csv` nella cartella della run, linkata da ogni sezione. Per il clustering ci sono anche i report per run in [`results/reports/cluster_tuning_notebooks/`](../../results/reports/cluster_tuning_notebooks/) (tabelle ordinate per silhouette, lettura per gruppi di k, immagini).
- **I parametri di una singola run**: il suo `config.md` e la riga in `runs.csv`.
- **Il perché di una scelta di metodo**, con le alternative scartate: [`.claude/history/methods_changelog.md`](../../.claude/history/methods_changelog.md).
- **Come si lancia una pipeline**: [`docs/guides/`](../guides/).
- **Come è costruita una matrice** (griglia 2mm comune, ricampionamento `nearest`, colonne costanti): [`docs/dev/lesion_matrix.md`](../dev/lesion_matrix.md) e [`docs/dev/sdc_matrix.md`](../dev/sdc_matrix.md).
