

import nibabel as nib
import numpy as np
from pathlib import Path
import os

def correct_mni_lesions(lesion_file, mni_brain_mask_file='/Users/sebastiano/fsl/data/standard/MNI152_T1_2mm_brain_mask.nii.gz',
                        out_dir='', dry_run=False):
    """Correct the lesions in the MNI space by removing voxels outside the brain mask."""

    lesion = nib.load(lesion_file)
    mni_brain_mask = nib.load(mni_brain_mask_file)

    lesion_data = lesion.get_fdata()
    mni_brain_mask_data = mni_brain_mask.get_fdata()
    print(f'N voxels outside MNI brain mask: {np.sum(lesion_data[mni_brain_mask_data == 0])}.\n'
          f' Ratio of lesion voxels outside MNI brain mask: {(np.sum(lesion_data[mni_brain_mask_data == 0]) / np.sum(lesion_data)):.2f}')

    if not dry_run:
        lesion_data[mni_brain_mask_data == 0] = 0
        nib.save(nib.Nifti1Image(lesion_data, lesion.affine, header=lesion.header), os.path.join(out_dir, lesion_file.name))





