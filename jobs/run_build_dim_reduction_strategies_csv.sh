#!/bin/bash
#SBATCH -J nemesis_dim_reduction_strategies
#SBATCH -p brains
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH -t 00:15:00
#SBATCH -o /home/etosato/Projects/NEMESIS_fs/logs/slurm/build_dim_reduction_strategies_csv/%j.out
#SBATCH -e /home/etosato/Projects/NEMESIS_fs/logs/slurm/build_dim_reduction_strategies_csv/%j.err

set -euo pipefail

PROJECT_ROOT="/home/etosato/Projects/NEMESIS_fs"
CONDA_ENV="nemesis"

set +u
source /home/etosato/miniconda3/etc/profile.d/conda.sh
conda activate "${CONDA_ENV}"
set -u

cd "${PROJECT_ROOT}"
export PYTHONPATH="${PROJECT_ROOT}"

echo "---- Starting dim_reduction_strategies.csv build at $(date) ----"
python scripts/build_dim_reduction_strategies_csv.py --results-root results
echo "---- Completed at $(date) ----"
