# clinical_connectome_23-07-26

## 15:32

## Config

```json
{
  "output_root": "data",
  "project": "clinical_connectome",
  "file_patterns": "config/registry/file_patterns_server.json",
  "datasets": [
    "UNIPD/WashU"
  ],
  "group_filter": [
    "ST"
  ],
  "subjects": null,
  "retrieve": [
    {
      "object": "feature",
      "pipeline": null,
      "datatype": "func",
      "suffix": "FC-pearson"
    },
    {
      "object": "feature",
      "pipeline": null,
      "datatype": "func",
      "suffix": "motion"
    },
    {
      "object": "feature",
      "pipeline": null,
      "datatype": "func",
      "suffix": "outliers"
    }
  ],
  "include_tabular_data": true,
  "overwrite": false
}
```

## Summary

| dataset     | copied | skipped (exists) | failed | participants.tsv |
| ----------- | ------ | ---------------- | ------ | ---------------- |
| UNIPD/WashU | 2704   | 0                | 0      | skipped (exists) |

## Failed

*A file's copy did not complete correctly, for the reason given. Sub-grouped by which object/pipeline/datatype/suffix was requested.*

- none

## File not found

*No registered file found for a specific subject (or an explicitly requested subject not present in this dataset). "empty folder" means the directory that would hold the file exists but is empty; "not found" covers every other case. Sub-grouped by which object/pipeline/datatype/suffix was requested.*

**feature/func/FC-pearson** (19)

- UNIPD/WashU: sub-STUNIPD0001 - no feature/func/FC-pearson (empty folder)
- UNIPD/WashU: sub-STUNIPD0021 - no feature/func/FC-pearson (empty folder)
- UNIPD/WashU: sub-STUNIPD0026 - no feature/func/FC-pearson (empty folder)
- UNIPD/WashU: sub-STUNIPD0064 - no feature/func/FC-pearson (empty folder)
- UNIPD/WashU: sub-STUNIPD0086 - no feature/func/FC-pearson (empty folder)
- UNIPD/WashU: sub-STUNIPD0090 - no feature/func/FC-pearson (empty folder)
- UNIPD/WashU: sub-STUNIPD0093 - no feature/func/FC-pearson (empty folder)
- UNIPD/WashU: sub-STUNIPD0101 - no feature/func/FC-pearson (empty folder)
- UNIPD/WashU: sub-STUNIPD0119 - no feature/func/FC-pearson (empty folder)
- UNIPD/WashU: sub-STUNIPD0130 - no feature/func/FC-pearson (empty folder)
- UNIPD/WashU: sub-STUNIPD0134 - no feature/func/FC-pearson (empty folder)
- UNIPD/WashU: sub-STUNIPD0136 - no feature/func/FC-pearson (empty folder)
- UNIPD/WashU: sub-STUNIPD0137 - no feature/func/FC-pearson (empty folder)
- UNIPD/WashU: sub-STUNIPD0139 - no feature/func/FC-pearson (empty folder)
- UNIPD/WashU: sub-STUNIPD0163 - no feature/func/FC-pearson (empty folder)
- UNIPD/WashU: sub-STUNIPD0171 - no feature/func/FC-pearson (empty folder)
- UNIPD/WashU: sub-STUNIPD0195 - no feature/func/FC-pearson (empty folder)
- UNIPD/WashU: sub-STUNIPD0206 - no feature/func/FC-pearson (empty folder)
- UNIPD/WashU: sub-STUNIPD0220 - no feature/func/FC-pearson (empty folder)

**feature/func/motion** (19)

- UNIPD/WashU: sub-STUNIPD0001 - no feature/func/motion (empty folder)
- UNIPD/WashU: sub-STUNIPD0021 - no feature/func/motion (empty folder)
- UNIPD/WashU: sub-STUNIPD0026 - no feature/func/motion (empty folder)
- UNIPD/WashU: sub-STUNIPD0064 - no feature/func/motion (empty folder)
- UNIPD/WashU: sub-STUNIPD0086 - no feature/func/motion (empty folder)
- UNIPD/WashU: sub-STUNIPD0090 - no feature/func/motion (empty folder)
- UNIPD/WashU: sub-STUNIPD0093 - no feature/func/motion (empty folder)
- UNIPD/WashU: sub-STUNIPD0101 - no feature/func/motion (empty folder)
- UNIPD/WashU: sub-STUNIPD0119 - no feature/func/motion (empty folder)
- UNIPD/WashU: sub-STUNIPD0130 - no feature/func/motion (empty folder)
- UNIPD/WashU: sub-STUNIPD0134 - no feature/func/motion (empty folder)
- UNIPD/WashU: sub-STUNIPD0136 - no feature/func/motion (empty folder)
- UNIPD/WashU: sub-STUNIPD0137 - no feature/func/motion (empty folder)
- UNIPD/WashU: sub-STUNIPD0139 - no feature/func/motion (empty folder)
- UNIPD/WashU: sub-STUNIPD0163 - no feature/func/motion (empty folder)
- UNIPD/WashU: sub-STUNIPD0171 - no feature/func/motion (empty folder)
- UNIPD/WashU: sub-STUNIPD0195 - no feature/func/motion (empty folder)
- UNIPD/WashU: sub-STUNIPD0206 - no feature/func/motion (empty folder)
- UNIPD/WashU: sub-STUNIPD0220 - no feature/func/motion (empty folder)

**feature/func/outliers** (19)

- UNIPD/WashU: sub-STUNIPD0001 - no feature/func/outliers (empty folder)
- UNIPD/WashU: sub-STUNIPD0021 - no feature/func/outliers (empty folder)
- UNIPD/WashU: sub-STUNIPD0026 - no feature/func/outliers (empty folder)
- UNIPD/WashU: sub-STUNIPD0064 - no feature/func/outliers (empty folder)
- UNIPD/WashU: sub-STUNIPD0086 - no feature/func/outliers (empty folder)
- UNIPD/WashU: sub-STUNIPD0090 - no feature/func/outliers (empty folder)
- UNIPD/WashU: sub-STUNIPD0093 - no feature/func/outliers (empty folder)
- UNIPD/WashU: sub-STUNIPD0101 - no feature/func/outliers (empty folder)
- UNIPD/WashU: sub-STUNIPD0119 - no feature/func/outliers (empty folder)
- UNIPD/WashU: sub-STUNIPD0130 - no feature/func/outliers (empty folder)
- UNIPD/WashU: sub-STUNIPD0134 - no feature/func/outliers (empty folder)
- UNIPD/WashU: sub-STUNIPD0136 - no feature/func/outliers (empty folder)
- UNIPD/WashU: sub-STUNIPD0137 - no feature/func/outliers (empty folder)
- UNIPD/WashU: sub-STUNIPD0139 - no feature/func/outliers (empty folder)
- UNIPD/WashU: sub-STUNIPD0163 - no feature/func/outliers (empty folder)
- UNIPD/WashU: sub-STUNIPD0171 - no feature/func/outliers (empty folder)
- UNIPD/WashU: sub-STUNIPD0195 - no feature/func/outliers (empty folder)
- UNIPD/WashU: sub-STUNIPD0206 - no feature/func/outliers (empty folder)
- UNIPD/WashU: sub-STUNIPD0220 - no feature/func/outliers (empty folder)

File Not Found Count = 57

## Skipped - object not present in this dataset

*A retrieve item whose object this dataset structurally lacks entirely (e.g. no features/ tree) - skipped for this dataset only, every other dataset and item still runs. Not an error.*

- none

## Non-conforming subject folders

*Folders found on disk that don't match the expected subject naming convention - excluded from retrieval.*

- none

## Mismatched

*A local file's checksum differs from its current source - possible corruption, or the source changed after this file was copied.*

- none

## Not copied despite source having it

*Verification found the source file, but data/ doesn't have it - a copy that silently failed to land.*

- none

## Unexpected local files

*Present in data/ but not the current resolution for any expected subject/retrieve item - stale naming or a leftover from a prior run.*
