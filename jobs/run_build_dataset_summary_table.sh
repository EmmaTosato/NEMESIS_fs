#!/bin/bash
#SBATCH -J nemesis_dataset_summary_table
#SBATCH -p brains
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH -t 00:10:00
#SBATCH -o /home/etosato/Projects/NEMESIS_fs/logs/slurm/build_dataset_summary_table/%j.out
#SBATCH -e /home/etosato/Projects/NEMESIS_fs/logs/slurm/build_dataset_summary_table/%j.err

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
python scripts/build_dataset_summary_table.py --output-dir results/tables
echo "---- Completed at $(date) ----"
