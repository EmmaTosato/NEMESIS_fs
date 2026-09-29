#!/bin/bash
#SBATCH -J nemesis_calibrate_lesion_side
#SBATCH -p brains
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH -t 00:20:00
#SBATCH -o /home/etosato/Projects/NEMESIS_fs/logs/slurm/calibrate_lesion_side_threshold/%j.out
#SBATCH -e /home/etosato/Projects/NEMESIS_fs/logs/slurm/calibrate_lesion_side_threshold/%j.err

set -euo pipefail

PROJECT_ROOT="/home/etosato/Projects/NEMESIS_fs"
CONDA_ENV="nemesis"

# Which grid's laterality_index to calibrate on, and the datasets that carry
# clinically-sourced lesion_side labels - edit before submitting.
GRID="2mm"
DATASETS=(UNIPD/WashU UNIPD/PSP UKLFR/stroke_UKLFR UKE/WAKEUP_acute UKE/SFB936_ses01)

set +u
source /home/etosato/miniconda3/etc/profile.d/conda.sh
conda activate "${CONDA_ENV}"
set -u

cd "${PROJECT_ROOT}"

echo "---- Starting lesion_side threshold calibration at $(date) ----"
python -m src.pipeline.calibrate_lesion_side_threshold \
    --grid "${GRID}" \
    --datasets "${DATASETS[@]}"
echo "---- Completed at $(date) ----"
