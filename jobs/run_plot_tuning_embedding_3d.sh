#!/bin/bash
#SBATCH -J nemesis_plot_tuning_embedding_3d
#SBATCH -p brains
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH -t 00:10:00
#SBATCH -o /home/etosato/Projects/NEMESIS_fs/logs/slurm/plot_tuning_embedding_3d/%j.out
#SBATCH -e /home/etosato/Projects/NEMESIS_fs/logs/slurm/plot_tuning_embedding_3d/%j.err

set -euo pipefail

PROJECT_ROOT="/home/etosato/Projects/NEMESIS_fs"
CONDA_ENV="nemesis"
EMBEDDINGS_NPZ="${PROJECT_ROOT}/results/lesion/dim_reduction/tuning/umap/26-08_s1.2-vol/embeddings.npz"
METADATA_CSV="${PROJECT_ROOT}/results/lesion/dim_reduction/tuning/umap/26-08_s1.2-vol/metadata.csv"
COMBO_KEY="metric=dice,n_components=3,n_neighbors=5,min_dist=0.0"
REDUCTION_METHOD="umap"
OUTPUT_DIR="${PROJECT_ROOT}/results/lesion/dim_reduction/tuning/umap/26-08_s1.2-vol/metric=dice/n_components=3"

set +u
source /home/etosato/miniconda3/etc/profile.d/conda.sh
conda activate "${CONDA_ENV}"
set -u

cd "${PROJECT_ROOT}"
export PYTHONPATH="${PROJECT_ROOT}"

echo "---- Starting plot_tuning_embedding_3d at $(date) ----"
python scripts/plot_tuning_embedding_3d.py \
  --embeddings-npz "${EMBEDDINGS_NPZ}" \
  --metadata-csv "${METADATA_CSV}" \
  --combo-key "${COMBO_KEY}" \
  --reduction-method "${REDUCTION_METHOD}" \
  --output-dir "${OUTPUT_DIR}"
echo "---- Completed at $(date) ----"
