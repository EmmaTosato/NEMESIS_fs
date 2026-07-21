# Running the analysis pipeline on SLURM — handoff for whoever launches/monitors these jobs

Self-contained note for a fresh chat/agent that will take over submitting and watching `sbatch` jobs for the analysis pipeline (`build_lesion_matrix.py` → `dim_reduction.py`/`dim_reduction_clustering.py`/`clustering.py`). Reflects state as of **21-07-26, ~12:00** — re-verify with `squeue -u etosato` and by looking at what's actually on disk before trusting anything below as still true; this is an operational snapshot, not frozen documentation like `docs/`.

Full usage reference: `docs/guides/analysis.md` (how to configure each script). This note is only about the SLURM launch/monitor mechanics and one sharp edge that bit us today.

## The one thing to never do: edit a config while its job is still PENDING

Every one of the 4 pipeline scripts is launched via `sbatch jobs/run_<script>.sh`, and every one of those job scripts hardcodes a single config path, e.g.:

```bash
CONFIG_FILE="${PROJECT_ROOT}/config/pipelines/dim_reduction.json"
...
python -m src.pipeline.dim_reduction --config "${CONFIG_FILE}"
```

**`sbatch` does not snapshot the config file's content at submission time** — it queues the job, and the job script only holds a *path*. The file is read from disk at the moment SLURM actually executes the script, which can be minutes or hours after submission (`PENDING` state, cluster load/priority-dependent). So:

- If you `sbatch` a job (e.g. t-SNE) and it sits `PENDING`, then edit `config/pipelines/dim_reduction.json` to a different run (e.g. UMAP) before that job actually starts, **the pending job will silently run the new config instead of the one it was submitted for** — no error, no warning, just the wrong run under that job id.
- **Rule**: before editing a config file that a script reads, confirm with `squeue -u etosato` that no job referencing that same config/script is still `PENDING` or `RUNNING`. If one is, either wait for it to leave the queue (finished/cancelled/failed) or cancel it first (`scancel <jobid>`) before touching the file.
- This bit us today: a t-SNE `dim_reduction.json` run (job 332525) was submitted, sat `PENDING`, and before touching the file for a UMAP run we had to explicitly wait/cancel rather than overwrite it live.

## Launch / monitor / cancel cheatsheet

```bash
conda activate nemesis   # only needed for ad-hoc checks; sbatch jobs activate it themselves

# launch (never run the python module directly on the login node)
sbatch jobs/run_build_lesion_matrix.sh
sbatch jobs/run_dim_reduction.sh
sbatch jobs/run_dim_reduction_clustering.sh
sbatch jobs/run_clustering.sh

# check what's queued/running
squeue -u etosato

# check a finished job's outcome (state, exit code) after it leaves squeue
sacct -j <jobid> --format=JobID,State,ExitCode -n -P

# job stdout/stderr (also useful while still running)
cat logs/slurm/<pipeline_name>/<jobid>.out
cat logs/slurm/<pipeline_name>/<jobid>.err

# cancel a job still in the queue
scancel <jobid>
```

Each script also writes its own report/log independent of SLURM's own `.out`/`.err` (see `docs/guides/analysis.md`): `reports/<script>/<project>/*.md`, `logs/<script>/<project>/*.log`, and an append-only `RUNS.md` at the method-folder level of its output.

## State as of this note

- **`build_lesion_matrix.py`**: only one real completed run exists on disk — `data/derived/lesion_matrix/21-07_s1/` (voxel-wise, `parcellate: false`, shape `(1150, 254865)`). Reference grid: `reference_template_path` = one `UNIPD/WashU` subject's lesion mask (2mm, `91×109×91` — matches FSL's `MNI152_T1_2mm_brain.nii.gz` grid exactly, chosen deliberately over an implicit "first file found" — see `docs/dev/analysis.md`).
- `config/pipelines/build_lesion_matrix.json` **currently holds a parcellated config** (`parcellate: true`, `atlas_path: assets/atlases/glasser_hcp_harvardoxford_subcortical_372.nii.gz` — the 372-region Glasser HCP + Harvard-Oxford atlas from `build_combined_atlas.py`, `session_name: "mmp372_s1"`) — **this was submitted (job 332516) then cancelled by the user before it ever ran**. Nothing at `data/derived/lesion_matrix/*mmp372_s1*` exists yet. Still a valid, ready-to-submit config if/when this run is wanted.
- **`dim_reduction.py`**: no run has completed — `results/dim_reduction/` doesn't exist yet.
- `config/pipelines/dim_reduction.json` **currently holds a t-SNE config** (`input_path: data/derived/lesion_matrix/21-07_s1`, i.e. the voxel-wise matrix — deliberately chosen over the not-yet-built parcellated one, `session_name: "tsne_s1"`, `run_notes` citing Thiebaut de Schotten et al. 2020 for the fixed params) — **this was submitted (job 332525) then cancelled by the user before it ever ran**. Still valid, ready-to-submit.
- Next thing floated in conversation but not yet acted on: switching `dim_reduction.json` to `"reduction_method": "umap"` for a UMAP run. Safe to do now (queue is empty — confirmed via `squeue -u etosato`), but will overwrite the t-SNE config in place, same file, so re-submitting t-SNE later means editing it back first.
- `dim_reduction_clustering.py`/`clustering.py`: not touched yet in this round — no runs, configs untouched since the multi-method clustering feature work (`clustering_methods` is a list field now, see `docs/dev/analysis.md`).

## Pointers

- `docs/guides/analysis.md` — full config field reference for all 4 scripts, output layout, fine-tuning workflow, method-comparison plots.
- `docs/dev/analysis.md` — architecture/design rationale, including why `reference_template_path` is explicit now (not derived from a dataset).
- `docs/guides/datasets.md` — per-dataset voxel resolution table (why `UNIPD/WashU` was picked as the 2mm reference).
- `.claude/stato_progetto.md` — broader project state snapshot (not run-specific).
