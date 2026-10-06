#!/bin/bash
#SBATCH -J nemesis_compute_sdc_metadata
#SBATCH -p brains
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
#SBATCH -t 03:00:00
#SBATCH -o /home/etosato/Projects/NEMESIS_fs/logs/slurm/compute_sdc_metadata/%j.out
#SBATCH -e /home/etosato/Projects/NEMESIS_fs/logs/slurm/compute_sdc_metadata/%j.err

# 8G is generous on purpose but not large: the computation is streaming (one 1mm map at a time,
# see src/features/sdc.py::compute_sdc_metadata), so peak memory is a few 1mm volumes plus the
# brain mask - tens of MB, independent of how many subjects are in scope. Time, not memory, is
# what scales: one read plus one resampling per subject (~0.2 s each, measured locally, so ~15
# min for the full cohort - the 3h limit is a wide margin for a slower shared filesystem).

set -euo pipefail

PROJECT_ROOT="/home/etosato/Projects/NEMESIS_fs"
CONDA_ENV="nemesis"
CONFIG_FILE="${PROJECT_ROOT}/config/pipelines/compute_sdc_metadata.json"

set +u
source /home/etosato/miniconda3/etc/profile.d/conda.sh
conda activate "${CONDA_ENV}"
set -u

cd "${PROJECT_ROOT}"
export PYTHONPATH="${PROJECT_ROOT}"

echo "---- Starting compute_sdc_metadata at $(date) ----"
python -m src.pipeline.compute_sdc_metadata --config "${CONFIG_FILE}"
echo "---- Completed at $(date) ----"
