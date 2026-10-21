#!/bin/bash
#SBATCH -J nemesis_evaluate_clustering_tuning
#SBATCH -p brains
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH -t 01:00:00
#SBATCH -o /home/etosato/Projects/NEMESIS_fs/logs/slurm/evaluate_clustering_tuning/%j.out
#SBATCH -e /home/etosato/Projects/NEMESIS_fs/logs/slurm/evaluate_clustering_tuning/%j.err

set -euo pipefail

PROJECT_ROOT="/home/etosato/Projects/NEMESIS_fs"
CONDA_ENV="nemesis"
CONFIG_FILE="${PROJECT_ROOT}/config/pipelines/evaluate_clustering_tuning.json"

set +u
source /home/etosato/miniconda3/etc/profile.d/conda.sh
conda activate "${CONDA_ENV}"
set -u

cd "${PROJECT_ROOT}"

echo "---- Starting evaluate_clustering_tuning at $(date) ----"
python -m src.pipeline.evaluate_clustering_tuning --config "${CONFIG_FILE}"
echo "---- Completed at $(date) ----"
