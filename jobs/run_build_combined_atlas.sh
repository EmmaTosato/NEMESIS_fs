#!/bin/bash
#SBATCH -J nemesis_build_combined_atlas
#SBATCH -p brains
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH -t 00:30:00
#SBATCH -o /home/etosato/Projects/NEMESIS_fs/logs/slurm/build_combined_atlas/%j.out
#SBATCH -e /home/etosato/Projects/NEMESIS_fs/logs/slurm/build_combined_atlas/%j.err

set -euo pipefail

PROJECT_ROOT="/home/etosato/Projects/NEMESIS_fs"
CONDA_ENV="nemesis"
CONFIG_FILE="${PROJECT_ROOT}/config/pipelines/build_combined_atlas.json"

set +u
source /home/etosato/miniconda3/etc/profile.d/conda.sh
conda activate "${CONDA_ENV}"
set -u

cd "${PROJECT_ROOT}"

echo "---- Starting combined atlas build at $(date) ----"
python -m src.pipeline.build_combined_atlas --config "${CONFIG_FILE}"
echo "---- Completed at $(date) ----"
