#!/bin/bash
#SBATCH -J nemesis_check_lesion_quality
#SBATCH -p brains
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
#SBATCH -t 02:00:00
#SBATCH -o /home/etosato/Projects/NEMESIS_fs/logs/slurm/check_lesion_quality/%j.out
#SBATCH -e /home/etosato/Projects/NEMESIS_fs/logs/slurm/check_lesion_quality/%j.err

set -euo pipefail

PROJECT_ROOT="/home/etosato/Projects/NEMESIS_fs"
CONDA_ENV="nemesis"
CONFIG_FILE="${PROJECT_ROOT}/config/pipelines/build_lesion_matrix.json"
OUTPUT_PATH="${PROJECT_ROOT}/assets/metadata/lesion_quality_metrics.csv"

set +u
source /home/etosato/miniconda3/etc/profile.d/conda.sh
conda activate "${CONDA_ENV}"
set -u

cd "${PROJECT_ROOT}"
export PYTHONPATH="${PROJECT_ROOT}"

echo "---- Starting check_lesion_quality at $(date) ----"
python -m src.pipeline.check_lesion_quality --config "${CONFIG_FILE}" --output-path "${OUTPUT_PATH}"
echo "---- Completed at $(date) ----"
