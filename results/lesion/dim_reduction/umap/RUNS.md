# Run history — umap

## Session 1.1
- First run of the pipeline 
- Starting date 21-07
- "UNIPD/WashU", "UNIPD/PASPORT", "UNIPD/PSP", "UKLFR/stroke_UKLFR"


### s1.1 — 21-07-26 14:23

Params: {"base_params": {"n_neighbors": 15, "min_dist": 0.1, "n_components": 2, "random_state": 0}, "tuning_grid": {"n_neighbors": [5, 15, 30, 50], "min_dist": [0.0, 0.1, 0.25, 0.5]}}
Output: results/dim_reduction/umap/tuning/21-07_s1.1
Note: UMAP fine-tuning (n_neighbors x min_dist sweep)

### s1.1_d01 — 21-07-26 14:45

Params: {"n_neighbors": 15, "min_dist": 0.1, "n_components": 2, "random_state": 0}
Output: results/dim_reduction/umap/21-07_s1.1_d01
Note: UMAP production run with fine-tuned params (n_neighbors=15, min_dist=0.1)

