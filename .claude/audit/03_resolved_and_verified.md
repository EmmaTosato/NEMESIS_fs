# 03 — Verifiche superate e fix confermati

## `.claude/CLAUDE.md` (76/76 righe)
| Verifica | Come provata |
|---|---|
| Conda env `nemesis` definito in `environment.yml` | `environment.yml:1` `name: nemesis` |
| Pacchetti elencati a CLAUDE.md:11 presenti in env | letto `environment.yml` (nibabel/nilearn in sezione `pip:`) |
| Entry point `src/pipeline/*.py` e `scripts/*.py` | `ls src/pipeline scripts` |
| Convenzione `jobs/run_<name>.sh` file singoli, nessuna sottocartella | `find jobs -mindepth 1 -type d` → vuoto |
| Log SLURM in `logs/slurm/<pipeline>/%j.{out,err}` | grep di `#SBATCH -o/-e` su 18/18 job; cartella = nome pipeline |
| `jobs/run_build_lesion_matrix.sh` esempio di riferimento | letto per intero: header, conda activate, cd, invocazione `python -m src.pipeline.build_lesion_matrix --config ...` |
| Guide in `docs/guides/` elencate esistono (14) e le 4 ritirate sono assenti | `[ -f ... ]` per 18 nomi |
| Doc `docs/dev/` elencati esistono (14) | `[ -f ... ]` |
| `docs/notes/` non esiste | `ls docs/notes` → errore |
| Moduli `src/analysis/{cluster_*,anatomical_maps}.py` esistono | `[ -f ... ]` 6/6 |
| `management/{meetings,cheatsheets,nemesis_project,slides}`, `knowledge/{notes,papers,papers/index.md}` | `ls` |
| `src/{analysis,features,pipeline,utils}`, `tests/{unit,integration}` | `ls` |
| `README.md` ha "What's implemented so far" | `README.md:64` |
| Import `@code_standards.md`/`@lessons_learned.md` | i file esistono in `.claude/` (relativi a CLAUDE.md) |
| Skill `history` | `.claude/skills/history/SKILL.md` |
| `.claude/history/` contiene i 4 file nominati | `ls` |

Fix già applicati: nessuno (nessuna modifica a file di progetto; solo creazione di `.claude/audit/`).
