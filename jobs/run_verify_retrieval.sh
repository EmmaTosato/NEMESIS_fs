#!/bin/bash
#SBATCH -J nemesis_verify_retrieval
#SBATCH -p brains
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH -t 01:00:00
#SBATCH -o /home/etosato/Projects/NEMESIS_fs/logs/slurm/verify_retrieval/%j.out
#SBATCH -e /home/etosato/Projects/NEMESIS_fs/logs/slurm/verify_retrieval/%j.err

set -euo pipefail

PROJECT_ROOT="/home/etosato/Projects/NEMESIS_fs"
CONDA_ENV="nemesis"
CONFIG_FILE="${PROJECT_ROOT}/config/pipelines/retrieval.json"

set +u
source /home/etosato/miniconda3/etc/profile.d/conda.sh
conda activate "${CONDA_ENV}"
set -u

cd "${PROJECT_ROOT}"
export PYTHONPATH="${PROJECT_ROOT}"

echo "---- Starting verification at $(date) ----"
python scripts/verify_retrieval.py --config "${CONFIG_FILE}"
echo "---- Completed at $(date) ----"
