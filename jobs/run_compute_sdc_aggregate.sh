#!/bin/bash
#SBATCH -J nemesis_compute_sdc_aggregate
#SBATCH -p brains
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH -t 00:15:00
#SBATCH -o /home/etosato/Projects/NEMESIS_fs/logs/slurm/compute_sdc_aggregate/%j.out
#SBATCH -e /home/etosato/Projects/NEMESIS_fs/logs/slurm/compute_sdc_aggregate/%j.err

# Step 3/3 of the compute_sdc pipeline: merge every array task's per-subject
# outcome into <output_dir>/{prep,features}, write the run summary/RUNS.md
# entry. Submit only after every jobs/run_compute_sdc.sh array task has
# finished (sbatch --dependency=afterany:<array_job_id> from the manifest's
# submission, or manually once `sacct` shows the array complete) - see
# docs/guides/compute_sdc.md.

set -euo pipefail

PROJECT_ROOT="/home/etosato/Projects/NEMESIS_fs"
CONDA_ENV="nemesis"
CONFIG_FILE="${PROJECT_ROOT}/config/pipelines/compute_sdc.json"

set +u
source /home/etosato/miniconda3/etc/profile.d/conda.sh
conda activate "${CONDA_ENV}"
set -u

cd "${PROJECT_ROOT}"

echo "---- Starting compute_sdc aggregate at $(date) ----"
python -m src.pipeline.compute_sdc --config "${CONFIG_FILE}" --mode aggregate
echo "---- Completed at $(date) ----"
