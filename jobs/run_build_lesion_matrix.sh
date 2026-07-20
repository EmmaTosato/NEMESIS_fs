#!/bin/bash
#SBATCH -J nemesis_build_lesion_matrix
#SBATCH -p brains
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
#SBATCH -t 02:00:00
#SBATCH -o /home/etosato/Projects/NEMESIS_fs/logs/slurm/build_lesion_matrix/%j.out
#SBATCH -e /home/etosato/Projects/NEMESIS_fs/logs/slurm/build_lesion_matrix/%j.err

set -euo pipefail

PROJECT_ROOT="/home/etosato/Projects/NEMESIS_fs"
CONDA_ENV="nemesis"
CONFIG_FILE="${PROJECT_ROOT}/config/pipelines/build_lesion_matrix.json"

set +u
source /home/etosato/miniconda3/etc/profile.d/conda.sh
conda activate "${CONDA_ENV}"
set -u

cd "${PROJECT_ROOT}"

echo "---- Starting lesion matrix build at $(date) ----"
python -m src.pipeline.build_lesion_matrix --config "${CONFIG_FILE}"
echo "---- Completed at $(date) ----"
