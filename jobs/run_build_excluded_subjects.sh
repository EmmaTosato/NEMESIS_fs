#!/bin/bash
#SBATCH -J nemesis_build_excluded_subjects
#SBATCH -p brains
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH -t 00:05:00
#SBATCH -o /home/etosato/Projects/NEMESIS_fs/logs/slurm/build_excluded_subjects/%j.out
#SBATCH -e /home/etosato/Projects/NEMESIS_fs/logs/slurm/build_excluded_subjects/%j.err

set -euo pipefail

PROJECT_ROOT="/home/etosato/Projects/NEMESIS_fs"
CONDA_ENV="nemesis"
CONFIG_FILE="${PROJECT_ROOT}/config/pipelines/build_excluded_subjects.json"

set +u
source /home/etosato/miniconda3/etc/profile.d/conda.sh
conda activate "${CONDA_ENV}"
set -u

cd "${PROJECT_ROOT}"

echo "---- Starting excluded subjects list build at $(date) ----"
python -m src.pipeline.build_excluded_subjects --config "${CONFIG_FILE}"
echo "---- Completed at $(date) ----"
