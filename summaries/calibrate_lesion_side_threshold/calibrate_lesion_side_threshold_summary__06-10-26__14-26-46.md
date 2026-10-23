# calibrate_lesion_side_threshold — 06-10-26 14:26:46

grid: 2mm
datasets: ['UNIPD/WashU', 'UNIPD/PSP', 'UKLFR/stroke_UKLFR', 'UKE/WAKEUP_acute', 'UKE/SFB936_ses01']
subjects with a usable clinical label + computable laterality_index: 1445
ground-truth label distribution: {'left': 816, 'right': 605, 'both': 24}

## Accuracy vs. threshold

| threshold | accuracy | correct/total |
|---|---|---|
| 0.00 | 0.972 | 1405/1445 |
| 0.02 | 0.973 | 1406/1445 |
| 0.04 | 0.974 | 1407/1445 |
| 0.06 | 0.974 | 1407/1445 |
| 0.08 | 0.974 | 1407/1445 |
| 0.10 | 0.974 | 1407/1445 |
| 0.12 | 0.974 | 1407/1445 |
| 0.14 | 0.974 | 1408/1445 |
| 0.16 | 0.974 | 1408/1445 |
| 0.18 | 0.974 | 1408/1445 |
| 0.20 *(literature default)* | 0.974 | 1408/1445 |
| 0.22 | 0.974 | 1408/1445 |
| 0.24 | 0.974 | 1408/1445 |
| 0.26 | 0.974 | 1408/1445 |
| 0.28 *(best)* | 0.975 | 1409/1445 |
| 0.30 | 0.975 | 1409/1445 |
| 0.32 | 0.975 | 1409/1445 |
| 0.34 | 0.974 | 1408/1445 |
| 0.36 | 0.974 | 1408/1445 |
| 0.38 | 0.974 | 1408/1445 |
| 0.40 | 0.974 | 1408/1445 |
| 0.42 | 0.974 | 1408/1445 |
| 0.44 | 0.973 | 1406/1445 |
| 0.46 | 0.973 | 1406/1445 |
| 0.48 | 0.972 | 1405/1445 |
| 0.50 | 0.972 | 1405/1445 |
| 0.52 | 0.972 | 1404/1445 |
| 0.54 | 0.972 | 1404/1445 |
| 0.56 | 0.972 | 1405/1445 |
| 0.58 | 0.973 | 1406/1445 |
| 0.60 | 0.972 | 1405/1445 |

## Confusion matrix — Literature default (|LI| < 0.2), threshold=0.20

rows = clinical label, columns = geometric prediction

| true \ predicted | left | right | both |
|---|---|---|---|
| left | 807 | 8 | 1 |
| right | 7 | 598 | 0 |
| both | 14 | 7 | 3 |

## Confusion matrix — Best on this data, threshold=0.28

rows = clinical label, columns = geometric prediction

| true \ predicted | left | right | both |
|---|---|---|---|
| left | 807 | 8 | 1 |
| right | 7 | 598 | 0 |
| both | 14 | 6 | 4 |

## Per-subject laterality_index (first 20 rows, for spot-checking)

| subject_id | dataset | lesion_side | laterality_index |
|---|---|---|---|
| sub-STUNIPD0001 | UNIPD/WashU | right | -1.0 |
| sub-STUNIPD0002 | UNIPD/WashU | left | -1.0 |
| sub-STUNIPD0003 | UNIPD/WashU | left | 1.0 |
| sub-STUNIPD0005 | UNIPD/WashU | left | 1.0 |
| sub-STUNIPD0006 | UNIPD/WashU | right | -1.0 |
| sub-STUNIPD0008 | UNIPD/WashU | right | 1.0 |
| sub-STUNIPD0009 | UNIPD/WashU | left | 1.0 |
| sub-STUNIPD0011 | UNIPD/WashU | left | 1.0 |
| sub-STUNIPD0012 | UNIPD/WashU | right | -1.0 |
| sub-STUNIPD0013 | UNIPD/WashU | right | -1.0 |
| sub-STUNIPD0014 | UNIPD/WashU | right | -1.0 |
| sub-STUNIPD0015 | UNIPD/WashU | left | 1.0 |
| sub-STUNIPD0016 | UNIPD/WashU | right | -1.0 |
| sub-STUNIPD0017 | UNIPD/WashU | left | 0.9985479186834464 |
| sub-STUNIPD0019 | UNIPD/WashU | right | -1.0 |
| sub-STUNIPD0020 | UNIPD/WashU | right | -0.788712011577424 |
| sub-STUNIPD0021 | UNIPD/WashU | left | 1.0 |
| sub-STUNIPD0023 | UNIPD/WashU | left | 1.0 |
| sub-STUNIPD0024 | UNIPD/WashU | right | -1.0 |
| sub-STUNIPD0025 | UNIPD/WashU | left | 0.6058091286307054 |
