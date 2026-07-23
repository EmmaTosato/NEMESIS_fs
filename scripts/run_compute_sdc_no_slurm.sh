#!/bin/bash
# Runs the compute_sdc pipeline (manifest -> parallel run -> aggregate)
# without SLURM: for quick tests on a handful of subjects, or on a machine
# without a scheduler. Production runs on the cluster go through
# jobs/run_compute_sdc_manifest.sh + jobs/run_compute_sdc.sh (array) +
# jobs/run_compute_sdc_aggregate.sh instead (see docs/guides/compute_sdc.md,
# ".claude/CLAUDE.md" reserves jobs/ for the sbatch convention - this script
# intentionally lives in scripts/, not jobs/, since it never goes through
# sbatch).
#
# Parallelism here is a bounded local process pool (xargs -P), not a SLURM
# array: TASK_COUNT = local CPU count / cores_per_subject (from the config),
# rounded down and floored at 1, so tasks never oversubscribe the machine's
# cores the same way --cpus-per-task does per array task on the cluster.
#
# Usage:
#   scripts/run_compute_sdc_no_slurm.sh [config_file] [--dry-run] [--background]

set -euo pipefail

PROJECT_ROOT="/home/etosato/Projects/NEMESIS_fs"
CONDA_ENV="nemesis"
CONFIG_FILE="${PROJECT_ROOT}/config/pipelines/compute_sdc.json"
DRY_RUN=""
RUN_IN_BACKGROUND=0

for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN="--dry-run" ;;
    --background) RUN_IN_BACKGROUND=1 ;;
    *) CONFIG_FILE="$arg" ;;
  esac
done

set +u
source /home/etosato/miniconda3/etc/profile.d/conda.sh
conda activate "${CONDA_ENV}"
set -u

cd "${PROJECT_ROOT}"

RUN_NAME=$(jq -r '.session_name' "${CONFIG_FILE}")
LOG_DIR="logs/local/compute_sdc/${RUN_NAME}"
mkdir -p "${LOG_DIR}"

run_all() {
    echo "---- Starting compute_sdc (local) at $(date) ----"

    python -m src.pipeline.compute_sdc --config "${CONFIG_FILE}" --mode manifest

    CORES_PER_SUBJECT=$(jq -r '.cores_per_subject' "${CONFIG_FILE}")
    HOST_CORES=$(nproc)
    TASK_COUNT=$(( HOST_CORES / CORES_PER_SUBJECT ))
    if [ "${TASK_COUNT}" -lt 1 ]; then
        echo "cores_per_subject (${CORES_PER_SUBJECT}) exceeds host cores (${HOST_CORES}) - refusing to oversubscribe" >&2
        exit 1
    fi
    echo "local pool: ${TASK_COUNT} concurrent task(s) (${HOST_CORES} cores / ${CORES_PER_SUBJECT} cores-per-subject)"

    # Without this, each bcb-lf-preprocess subprocess defaults to using every
    # host core for BLAS threading (OpenBLAS/numpy ignore cores_per_subject),
    # so TASK_COUNT concurrent processes oversubscribe far past HOST_CORES
    # and pthread_create starts failing under load - see debug session 23/07/26.
    export OPENBLAS_NUM_THREADS="${CORES_PER_SUBJECT}"
    export OMP_NUM_THREADS="${CORES_PER_SUBJECT}"

    seq 0 "$(( TASK_COUNT - 1 ))" | xargs -I{} -P "${TASK_COUNT}" \
        python -m src.pipeline.compute_sdc --config "${CONFIG_FILE}" --mode run \
        --task-id {} --task-count "${TASK_COUNT}" ${DRY_RUN}

    if [ -z "${DRY_RUN}" ]; then
        python -m src.pipeline.compute_sdc --config "${CONFIG_FILE}" --mode aggregate
    fi

    echo "---- Completed at $(date) ----"
}

if [ "${RUN_IN_BACKGROUND}" -eq 1 ]; then
    LOG_FILE="${LOG_DIR}/$(date +%d-%m-%y__%H-%M-%S).log"
    nohup bash -c "$(declare -f run_all); run_all" > "${LOG_FILE}" 2>&1 &
    echo "running in background (pid $!), log: ${LOG_FILE}"
else
    run_all
fi
