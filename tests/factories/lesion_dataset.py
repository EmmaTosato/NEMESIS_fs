"""Dataset di lesioni sintetico su disco + config di `build_lesion_matrix` + run già eseguita."""

from __future__ import annotations

import json
from pathlib import Path

import nibabel as nib
import numpy as np
import pandas as pd

from tests.factories.ids import subject_id

AFFINE = np.diag([2.0, 2.0, 2.0, 1.0])
SHAPE = (10, 10, 10)
LESION_GLOB = "*/lesion/manual_masks/anat/*_label-lesion_mask.nii.gz"
EMPTY_EXCLUSION_HEADER = "subject_id,dataset,reason,scope,value\n"


def write_empty_exclusion_list(tmp_path: Path) -> str:
    """Lista di esclusione con solo l'header: il modo esplicito di dire "non escludere nessuno"
    (un file MANCANTE è rifiutato da `load_excluded_subjects`)."""
    path = tmp_path / "excluded_subjects.csv"
    path.write_text(EMPTY_EXCLUSION_HEADER)
    return str(path)


def write_lesion_subject(data_root: Path, dataset: str, sid: str, lesion_voxels, affine=AFFINE, shape=SHAPE) -> Path:
    subject_dir = data_root / dataset / sid / "lesion" / "manual_masks" / "anat"
    subject_dir.mkdir(parents=True, exist_ok=True)
    volume = np.zeros(shape, dtype=np.float32)
    for voxel in lesion_voxels:
        volume[tuple(voxel)] = 1.0
    path = subject_dir / f"{sid}_label-lesion_mask.nii.gz"
    nib.save(nib.Nifti1Image(volume, affine), path)
    return path


def write_lesion_dataset(data_root: Path, n_subjects: int = 8, seed: int = 0, dataset: str = "siteA", voxels_per_lesion: int = 5) -> list[str]:
    """Scrive `n_subjects` maschere con `voxels_per_lesion` voxel casuali; ritorna gli ID in ordine."""
    rng = np.random.default_rng(seed)
    ids = []
    for i in range(n_subjects):
        sid = subject_id(i)
        voxels = [tuple(rng.integers(0, SHAPE[0], size=3)) for _ in range(voxels_per_lesion)]
        write_lesion_subject(data_root, dataset, sid, voxels)
        ids.append(sid)
    return ids


def write_reference_template(path: Path, affine=AFFINE, shape=SHAPE) -> Path:
    nib.save(nib.Nifti1Image(np.zeros(shape, dtype=np.float32), affine), path)
    return path


def lesion_matrix_config(tmp_path: Path, data_root: Path, output_root: Path, overrides: dict | None = None) -> dict:
    template = write_reference_template(tmp_path / "reference_template.nii.gz")
    cfg = {
        "project": "testproj",
        "data_root": str(data_root),
        "datasets": ["siteA"],
        "excluded_subjects_path": write_empty_exclusion_list(tmp_path),
        "representation": "voxelwise",
        "reference_template_path": str(template),
        "lesion_glob": LESION_GLOB,
        "binarize_threshold": 0.5,
        "resample_interpolation": "nearest",
        "output_root": str(output_root),
        "session_name": "run1",
        "overwrite": False,
        "run_notes": None,
    }
    cfg.update(overrides or {})
    return cfg


def write_json(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload))
    return path


def run_build_lesion_matrix(tmp_path: Path, monkeypatch, n_subjects: int = 8, seed: int = 0) -> Path:
    """Esegue il vero `build_lesion_matrix.main` su un dataset sintetico e ritorna la cartella della run."""
    from src.pipeline import build_lesion_matrix

    monkeypatch.setattr(build_lesion_matrix, "LOGS_ROOT", tmp_path / "bl_logs")
    data_root = tmp_path / "data"
    write_lesion_dataset(data_root, n_subjects, seed)
    output_root = tmp_path / "matrix_out"
    cfg_path = write_json(tmp_path / "build.json", lesion_matrix_config(tmp_path, data_root, output_root))
    assert build_lesion_matrix.main(["--config", str(cfg_path)]) == 0
    return next(p for p in output_root.iterdir() if p.is_dir())


def add_clinical_columns(run_dir: Path) -> None:
    """Aggiunge `lesion_side`/`nihss` al `metadata.csv` di una run (dim_reduction non arricchisce i metadati)."""
    path = run_dir / "metadata.csv"
    metadata = pd.read_csv(path)
    metadata["lesion_side"] = ["left" if i % 2 == 0 else "right" for i in range(len(metadata))]
    metadata["nihss"] = [float(4 + i) for i in range(len(metadata))]
    metadata.to_csv(path, index=False)
