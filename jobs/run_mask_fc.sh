#!/bin/bash
#SBATCH -J nemesis_mask_fc
#SBATCH -p brains
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
#SBATCH -t 02:00:00
#SBATCH -o /home/etosato/Projects/NEMESIS_fs/logs/slurm/mask_fc/%j.out
#SBATCH -e /home/etosato/Projects/NEMESIS_fs/logs/slurm/mask_fc/%j.err

set -euo pipefail

PROJECT_ROOT="/home/etosato/Projects/NEMESIS_fs"
CONDA_ENV="nemesis"
CONFIG_FILE="${PROJECT_ROOT}/config/pipelines/mask_fc.json"

set +u
source /home/etosato/miniconda3/etc/profile.d/conda.sh
conda activate "${CONDA_ENV}"
set -u

cd "${PROJECT_ROOT}"

echo "---- Starting FC lesion masking at $(date) ----"
python -m src.pipeline.mask_fc --config "${CONFIG_FILE}"
echo "---- Completed at $(date) ----"
