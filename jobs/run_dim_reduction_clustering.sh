#!/bin/bash
#SBATCH -J nemesis_dim_reduction_clustering
#SBATCH -p brains
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
#SBATCH -t 01:00:00
#SBATCH -o /home/etosato/Projects/NEMESIS_fs/logs/slurm/dim_reduction_clustering/%j.out
#SBATCH -e /home/etosato/Projects/NEMESIS_fs/logs/slurm/dim_reduction_clustering/%j.err

set -euo pipefail

PROJECT_ROOT="/home/etosato/Projects/NEMESIS_fs"
CONDA_ENV="nemesis"
CONFIG_FILE="${PROJECT_ROOT}/config/pipelines/dim_reduction_clustering.json"

set +u
source /home/etosato/miniconda3/etc/profile.d/conda.sh
conda activate "${CONDA_ENV}"
set -u

cd "${PROJECT_ROOT}"

echo "---- Starting dim-reduction + clustering at $(date) ----"
python -m src.pipeline.dim_reduction_clustering --config "${CONFIG_FILE}"
echo "---- Completed at $(date) ----"
