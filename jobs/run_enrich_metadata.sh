#!/bin/bash
#SBATCH -J nemesis_enrich_metadata
#SBATCH -p brains
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH -t 00:10:00
#SBATCH -o /home/etosato/Projects/NEMESIS_fs/logs/slurm/enrich_metadata/%j.out
#SBATCH -e /home/etosato/Projects/NEMESIS_fs/logs/slurm/enrich_metadata/%j.err

set -euo pipefail

PROJECT_ROOT="/home/etosato/Projects/NEMESIS_fs"
CONDA_ENV="nemesis"
CONFIG_FILE="${PROJECT_ROOT}/config/pipelines/enrich_metadata.json"

set +u
source /home/etosato/miniconda3/etc/profile.d/conda.sh
conda activate "${CONDA_ENV}"
set -u

cd "${PROJECT_ROOT}"

echo "---- Starting lesion metadata enrichment at $(date) ----"
python -m src.pipeline.enrich_metadata --config "${CONFIG_FILE}"
echo "---- Completed at $(date) ----"
