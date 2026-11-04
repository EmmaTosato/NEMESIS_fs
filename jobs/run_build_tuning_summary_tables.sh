#!/bin/bash
#SBATCH -J nemesis_tuning_summary_tables
#SBATCH -p brains
#SBATCH --cpus-per-task=1
#SBATCH --mem=16G
#SBATCH -t 00:30:00
#SBATCH -o /home/etosato/Projects/NEMESIS_fs/logs/slurm/build_tuning_summary_tables/%j.out
#SBATCH -e /home/etosato/Projects/NEMESIS_fs/logs/slurm/build_tuning_summary_tables/%j.err

set -euo pipefail

PROJECT_ROOT="/home/etosato/Projects/NEMESIS_fs"
CONDA_ENV="nemesis"

set +u
source /home/etosato/miniconda3/etc/profile.d/conda.sh
conda activate "${CONDA_ENV}"
set -u

cd "${PROJECT_ROOT}"
export PYTHONPATH="${PROJECT_ROOT}"

echo "---- Starting at $(date) ----"
python scripts/build_tuning_summary_tables.py --output-dir results/tables/tuning_sum_03-11
echo "---- Completed at $(date) ----"
