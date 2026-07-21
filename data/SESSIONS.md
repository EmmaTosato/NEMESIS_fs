# Sessions — clinical_connectome

Hand-written, one entry per session_name (session number, e.g. `s1.1`) used
anywhere in the pipeline (data/ and results/) — what the session is for,
which datasets/modality it covers. Not auto-generated: individual run
entries (params/output/notes per run_id) live in each pipeline's own
`runs.csv` instead (`data/derived/<pipeline>/runs.csv`,
`results/<modality>/<pipeline>/<method>/runs.csv`), see `docs/dev/analysis.md`.

## Session 1.1
- First run of the pipeline
- Starting date 21-07
- "UNIPD/WashU", "UNIPD/PASPORT", "UNIPD/PSP", "UKLFR/stroke_UKLFR"
- Data Modality: Lesion

## Session 1.2
- Parcellated on the 372-region Glasser HCP + Harvard-Oxford subcortical atlas
- Data Modality: Lesion
