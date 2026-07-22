#!/bin/bash
#SBATCH -J nemesis_compute_sdc
#SBATCH -p brains
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH -t 04:00:00
#SBATCH -o /home/etosato/Projects/NEMESIS_fs/logs/slurm/compute_sdc/%A_%a.out
#SBATCH -e /home/etosato/Projects/NEMESIS_fs/logs/slurm/compute_sdc/%A_%a.err
# --array must be set at submission time, e.g. for 1150 subjects, at most 10
# running concurrently (the rest queue as pending until a slot frees up):
#SBATCH --array=0-1149%10

# Step 2/3 of the compute_sdc pipeline: one array task per subject (this
# array size, N tasks => N subjects, keeps the mapping trivial - see
# docs/guides/compute_sdc.md for chunking multiple subjects per task if the
# manifest grows large enough that per-subject array tasks become
# impractical for the scheduler). Requires manifest.csv to already exist
# (jobs/run_compute_sdc_manifest.sh must have completed first) and
# --cpus-per-task here must equal cores_per_subject in the config (see
# compute_sdc.json) - the two are the same number by construction, since
# each task processes exactly one subject.
#
# The %10 throttle caps concurrently RUNNING tasks at 10 - the remaining
# 1140 sit PENDING in the queue and SLURM starts each one as a running slot
# frees up, so cores_per_subject x 10 (not x 1150) is what's actually
# consumed from the `brains` partition at any given moment. Adjust the %N to
# whatever the partition can spare alongside other lab jobs.

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
