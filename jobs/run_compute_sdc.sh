#!/bin/bash
#SBATCH -J nemesis_compute_sdc
#SBATCH -p brains
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH -t 04:00:00
#SBATCH -o /home/etosato/Projects/NEMESIS_fs/logs/slurm/compute_sdc/%A_%a.out
#SBATCH -e /home/etosato/Projects/NEMESIS_fs/logs/slurm/compute_sdc/%A_%a.err
# --array must be set at submission time. For 1150 subjects we'd want one
# task per subject (0-1149), but the cluster's MaxArraySize=1001 (see
# `scontrol show config | grep MaxArraySize`) rejects that outright - so
# this is chunked to 575 tasks x 2 subjects/task instead (stride slice,
# still complete/disjoint coverage - see docs/guides/compute_sdc.md), at
# most 3 running concurrently (the rest queue as pending until a slot frees
# up):
#SBATCH --array=0-574%3

# Step 2/3 of the compute_sdc pipeline: one array task per ~2 subjects
# (chunked from the ideal 1-subject-per-task mapping - see comment on
# --array above - because the cluster's MaxArraySize rejects a 1150-task
# array). Requires manifest.csv to already exist (jobs/run_compute_sdc_manifest.sh
# must have completed first) and --cpus-per-task here must equal
# cores_per_subject in the config (compute_sdc.json) - bcb-lf-preprocess/
# bcb-lesion-features share that core budget across every subject in a
# task's staging folder, not per-subject.
#
# The %3 throttle caps concurrently RUNNING tasks at 3 - the remaining 572
# sit PENDING in the queue and SLURM starts each one as a running slot frees
# up, so cores_per_subject x 3 (not x 575) is what's actually consumed from
# the `brains` partition at any given moment. Capped at 3 to stay within
# this user's max-concurrent-jobs quota on the cluster - do not raise
# without checking that quota first.

set -euo pipefail

PROJECT_ROOT="/home/etosato/Projects/NEMESIS_fs"
CONDA_ENV="nemesis"
CONFIG_FILE="${PROJECT_ROOT}/config/pipelines/compute_sdc.json"
# Fixed at the manifest's total chunk count (575, see --array comment above),
# NOT ${SLURM_ARRAY_TASK_COUNT} - that reflects how many elements are in
# *this* sbatch submission, which is wrong the moment --array is overridden
# to a subset (e.g. `sbatch --array=250-574%3` to retry only failed task
# IDs): task-count must stay 575 for select_chunk()'s stride slice to keep
# mapping each task-id to the same subjects it always has.
TASK_COUNT=575

set +u
source /home/etosato/miniconda3/etc/profile.d/conda.sh
conda activate "${CONDA_ENV}"
set -u

cd "${PROJECT_ROOT}"

echo "---- Starting compute_sdc task ${SLURM_ARRAY_TASK_ID}/${TASK_COUNT} at $(date) ----"
python -m src.pipeline.compute_sdc \
  --config "${CONFIG_FILE}" \
  --mode run \
  --task-id "${SLURM_ARRAY_TASK_ID}" \
  --task-count "${TASK_COUNT}"
echo "---- Completed at $(date) ----"
