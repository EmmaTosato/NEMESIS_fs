#!/bin/bash

REMOTE_USER="etosato"
REMOTE_HOST="147.162.114.111"
REMOTE_DIR="/data/corbetta/Clinical_connectome/features/Clinical_connectome_stroke/UCL-UK/UCLStrokeData/lesion"
LOCAL_DIR="/Users/emmatosato/Local Projects/Local PhD Projects/NEMESIS_fs/sdc_download"

mkdir -p "$LOCAL_DIR"

# Elenca sul remoto tutti i file che matchano il pattern
ssh "${REMOTE_USER}@${REMOTE_HOST}" \
  "find '$REMOTE_DIR' -maxdepth 2 -name 'sub-*_space-MNI152NLin6Asym_res-1_desc-disconnectome.nii.gz'" \
| while IFS= read -r remote_file; do
    sub=$(basename "$(dirname "$remote_file")")
    mkdir -p "$LOCAL_DIR/$sub"
    echo "Scarico $remote_file ..."
    scp "${REMOTE_USER}@${REMOTE_HOST}:$remote_file" "$LOCAL_DIR/$sub/"
done
