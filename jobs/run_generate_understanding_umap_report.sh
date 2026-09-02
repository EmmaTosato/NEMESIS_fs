#!/bin/bash
#SBATCH -J nemesis_generate_understanding_umap_report
#SBATCH -p brains
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH -t 00:15:00
#SBATCH -o /home/etosato/Projects/NEMESIS_fs/logs/slurm/generate_understanding_umap_report/%j.out
#SBATCH -e /home/etosato/Projects/NEMESIS_fs/logs/slurm/generate_understanding_umap_report/%j.err

set -euo pipefail

PROJECT_ROOT="/home/etosato/Projects/NEMESIS_fs"
CONDA_ENV="nemesis"
UMAP_TUNING_DIR="${PROJECT_ROOT}/results/lesion/dim_reduction/tuning/umap/13-08_s1.1-vol"
TSNE_TUNING_DIR="${PROJECT_ROOT}/results/lesion/dim_reduction/tuning/tsne/13-08_s1.1-vol"

set +u
source /home/etosato/miniconda3/etc/profile.d/conda.sh
conda activate "${CONDA_ENV}"
set -u

cd "${PROJECT_ROOT}"
export PYTHONPATH="${PROJECT_ROOT}"

echo "---- Starting understanding_umap report generation at $(date) ----"
python -m src.pipeline.generate_understanding_umap_report \
  --umap-tuning-dir "${UMAP_TUNING_DIR}" \
  --tsne-tuning-dir "${TSNE_TUNING_DIR}"
echo "---- Completed at $(date) ----"
