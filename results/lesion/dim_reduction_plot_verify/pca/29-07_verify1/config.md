# clinical_connectome dim_reduction (pca) — 29-07-26 09:31

## Config

```json
{
  "project": "clinical_connectome",
  "input_path": "data/derived/lesion_matrix/21-07_s1.1",
  "reduction_method": "pca",
  "params_file": "/private/tmp/claude-501/-Users-emmatosato-Local-Projects-Local-PhD-Projects-NEMESIS-fs/25bf3c10-6892-45d6-80bf-4d5a0ac0f006/scratchpad/params_reduction_verify.json",
  "output_root": "results/lesion/dim_reduction_plot_verify",
  "session_name": "verify1",
  "overwrite": true,
  "fine_tuning": false,
  "regress_out_volume": false,
  "run_notes": "scratch run to visually verify the new Dataset/Volume/Side plots - not a real production result, safe to delete"
}
```

## Summary

Input matrix shape: 1150 subjects x 254865 features
Embedding shape: 1150 subjects x 2 components
Params used: {"n_components": 2, "random_state": 0}
