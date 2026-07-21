#!/bin/bash
#SBATCH -J nemesis_data_summary
#SBATCH -p brains
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH -t 01:00:00
#SBATCH -o /home/etosato/Projects/NEMESIS_fs/logs/slurm/data_summary/%j.out
#SBATCH -e /home/etosato/Projects/NEMESIS_fs/logs/slurm/data_summary/%j.err

set -euo pipefail

PROJECT_ROOT="/home/etosato/Projects/NEMESIS_fs"
CONDA_ENV="nemesis"
CONFIG_FILE="${PROJECT_ROOT}/config/pipelines/retrieval_server.json"

set +u
source /home/etosato/miniconda3/etc/profile.d/conda.sh
conda activate "${CONDA_ENV}"
set -u

cd "${PROJECT_ROOT}"
export PYTHONPATH="${PROJECT_ROOT}"

echo "---- Starting data summary at $(date) ----"
python scripts/data_summary.py --config "${CONFIG_FILE}"
echo "---- Completed at $(date) ----"
