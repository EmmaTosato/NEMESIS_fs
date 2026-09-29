#!/bin/bash
#SBATCH -J nemesis_populate_metadata
#SBATCH -p brains
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH -t 01:00:00
#SBATCH -o /home/etosato/Projects/NEMESIS_fs/logs/slurm/populate_metadata/%j.out
#SBATCH -e /home/etosato/Projects/NEMESIS_fs/logs/slurm/populate_metadata/%j.err

set -euo pipefail

PROJECT_ROOT="/home/etosato/Projects/NEMESIS_fs"
CONDA_ENV="nemesis"
CONFIG_FILE="${PROJECT_ROOT}/config/pipelines/populate_metadata.json"

set +u
source /home/etosato/miniconda3/etc/profile.d/conda.sh
conda activate "${CONDA_ENV}"
set -u

cd "${PROJECT_ROOT}"

echo "---- Starting populate_metadata at $(date) ----"
python -m src.pipeline.populate_metadata --config "${CONFIG_FILE}"
echo "---- Completed at $(date) ----"
