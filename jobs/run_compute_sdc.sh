#!/bin/bash
#SBATCH -J nemesis_compute_sdc
#SBATCH -p brains
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH -t 04:00:00
#SBATCH -o /home/etosato/Projects/NEMESIS_fs/logs/slurm/compute_sdc/%A_%a.out
#SBATCH -e /home/etosato/Projects/NEMESIS_fs/logs/slurm/compute_sdc/%A_%a.err
# --array must be set at submission time, e.g. for 120 subjects:
#SBATCH --array=0-119

# Step 2/3 of the compute_sdc pipeline: one array task per subject (this
# array size, N tasks => N subjects, keeps the mapping trivial - see
# docs/guides/compute_sdc.md for chunking multiple subjects per task if the
# manifest grows large enough that per-subject array tasks become
# impractical for the scheduler). Requires manifest.csv to already exist
# (jobs/run_compute_sdc_manifest.sh must have completed first) and
# --cpus-per-task here must equal cores_per_subject in the config (see
# compute_sdc.json) - the two are the same number by construction, since
# each task processes exactly one subject.

set -euo pipefail

PROJECT_ROOT="/home/etosato/Projects/NEMESIS_fs"
CONDA_ENV="nemesis"
CONFIG_FILE="${PROJECT_ROOT}/config/pipelines/compute_sdc.json"

set +u
source /home/etosato/miniconda3/etc/profile.d/conda.sh
conda activate "${CONDA_ENV}"
set -u

cd "${PROJECT_ROOT}"

echo "---- Starting compute_sdc task ${SLURM_ARRAY_TASK_ID}/${SLURM_ARRAY_TASK_COUNT} at $(date) ----"
python -m src.pipeline.compute_sdc \
  --config "${CONFIG_FILE}" \
  --mode run \
  --task-id "${SLURM_ARRAY_TASK_ID}" \
  --task-count "${SLURM_ARRAY_TASK_COUNT}"
echo "---- Completed at $(date) ----"
