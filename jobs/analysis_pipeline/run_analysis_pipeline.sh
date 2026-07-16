#!/bin/bash
#SBATCH -J nemesis_analysis_pipeline
#SBATCH -p brains
#SBATCH --cpus-per-task=1
#SBATCH --mem=64G
#SBATCH -t 04:00:00
#SBATCH -o /home/etosato/Projects/NEMESIS_fs/logs/slurm/analysis_pipeline/%j.out
#SBATCH -e /home/etosato/Projects/NEMESIS_fs/logs/slurm/analysis_pipeline/%j.err

set -euo pipefail

PROJECT_ROOT="/home/etosato/Projects/NEMESIS_fs"
CONDA_ENV="nemesis"
# lesion_embedding.json does not exist yet - STEP_REGISTRY is still empty
# (see src/analysis/steps.py); update this path once a real config is added.
CONFIG_FILE="${PROJECT_ROOT}/config/lesion_embedding.json"

set +u
source /home/etosato/miniconda3/etc/profile.d/conda.sh
conda activate "${CONDA_ENV}"
set -u

cd "${PROJECT_ROOT}"

echo "---- Starting analysis pipeline at $(date) ----"
python -m src.pipeline.run_analysis_pipeline --config "${CONFIG_FILE}"
echo "---- Completed at $(date) ----"
