#!/bin/bash
#SBATCH -J nemesis_download_sdc
#SBATCH -p brains
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH -t 01:00:00
#SBATCH -o /home/etosato/Projects/NEMESIS_fs/logs/slurm/download_sdc/%j.out
#SBATCH -e /home/etosato/Projects/NEMESIS_fs/logs/slurm/download_sdc/%j.err

set -euo pipefail

PROJECT_ROOT="/home/etosato/Projects/NEMESIS_fs"
CONDA_ENV="nemesis"

# Edit these before submitting - see `python scripts/download_sdc.py --help`
# for every option (datasets/categories default to "all" if left empty).
DATASETS=""      # e.g. "UNIPD/WashU UKLFR/stroke_UKLFR" - empty means every registered sdc dataset
CATEGORIES=""     # e.g. "disconnectome-LF lesion-LF" - empty means every category
OVERWRITE="false" # "true" to re-copy files that already exist locally
OUTPUT_ROOT="data/"

set +u
source /home/etosato/miniconda3/etc/profile.d/conda.sh
conda activate "${CONDA_ENV}"
set -u

cd "${PROJECT_ROOT}"

ARGS=(--output-root "${OUTPUT_ROOT}")
[ -n "${DATASETS}" ] && ARGS+=(--datasets ${DATASETS})
[ -n "${CATEGORIES}" ] && ARGS+=(--categories ${CATEGORIES})
[ "${OVERWRITE}" = "true" ] && ARGS+=(--overwrite)

echo "---- Starting SDC download at $(date) ----"
PYTHONPATH="${PROJECT_ROOT}" python scripts/download_sdc.py "${ARGS[@]}"
echo "---- Completed at $(date) ----"
