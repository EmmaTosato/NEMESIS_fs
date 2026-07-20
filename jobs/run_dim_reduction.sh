#!/bin/bash
#SBATCH -J nemesis_dim_reduction
#SBATCH -p brains
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
#SBATCH -t 01:00:00
#SBATCH -o /home/etosato/Projects/NEMESIS_fs/logs/slurm/dim_reduction/%j.out
#SBATCH -e /home/etosato/Projects/NEMESIS_fs/logs/slurm/dim_reduction/%j.err

set -euo pipefail

PROJECT_ROOT="/home/etosato/Projects/NEMESIS_fs"
CONDA_ENV="nemesis"
CONFIG_FILE="${PROJECT_ROOT}/config/pipelines/dim_reduction.json"

set +u
source /home/etosato/miniconda3/etc/profile.d/conda.sh
conda activate "${CONDA_ENV}"
set -u

cd "${PROJECT_ROOT}"

echo "---- Starting dimensionality reduction at $(date) ----"
python -m src.pipeline.dim_reduction --config "${CONFIG_FILE}"
echo "---- Completed at $(date) ----"
