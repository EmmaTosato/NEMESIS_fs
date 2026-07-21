#!/bin/bash
#SBATCH -J nemesis_replot_dim_reduction
#SBATCH -p brains
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH -t 00:10:00
#SBATCH -o /home/etosato/Projects/NEMESIS_fs/logs/slurm/replot_dim_reduction/%j.out
#SBATCH -e /home/etosato/Projects/NEMESIS_fs/logs/slurm/replot_dim_reduction/%j.err

set -euo pipefail

PROJECT_ROOT="/home/etosato/Projects/NEMESIS_fs"
CONDA_ENV="nemesis"
RUN_DIR="${PROJECT_ROOT}/results/dim_reduction/tsne/21-07_tsne_run1"

set +u
source /home/etosato/miniconda3/etc/profile.d/conda.sh
conda activate "${CONDA_ENV}"
set -u

cd "${PROJECT_ROOT}"
export PYTHONPATH="${PROJECT_ROOT}"

echo "---- Starting replot at $(date) ----"
python scripts/replot_dim_reduction.py --run-dir "${RUN_DIR}"
echo "---- Completed at $(date) ----"
