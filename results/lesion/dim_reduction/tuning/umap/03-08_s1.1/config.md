e  eicoiarncaanttlinlmunttim

# clinical_connectome — lesion › dim_reduction › umap › tuning › 03-08_s1.1

## Config

```json
{
  "project": "clinical_connectome",
  "input_path": "data/derived/lesion_matrix/21-07_s1.1",
  "reduction_method": "umap",
  "params_file": "config/registry/params_reduction.json",
  "session_name": "s1.1",
  "base_params": {
    "n_neighbors": 15,
    "min_dist": 0.0,
    "n_components": 2,
    "random_state": 0,
    "metric": "jaccard"
  },
  "tuning_grid": {
    "metric": [
      "euclidean",
      "jaccard",
      "dice"
    ],
    "regress_out_volume": [
      false,
      true
    ],
    "n_components": [
      2,
      5,
      10
    ],
    "n_neighbors": [
      5,
      15,
      30,
      50,
      100
    ],
    "min_dist": [
      0.0,
      0.1,
      0.25
    ]
  },
  "nested_params": [
    "metric",
    "regress_out_volume",
    "n_components"
  ]
}
```

## Summary

Swept parameters: ['metric', 'regress_out_volume', 'n_components', 'n_neighbors', 'min_dist']
Nested parameters (one subfolder per real combination): ['metric', 'regress_out_volume', 'n_components']
Free/grid parameters (embeddings_grid.png per leaf): ['n_neighbors', 'min_dist']
Combinations evaluated: 180
Metric: trustworthiness

Warning: no automatic selection - inspect tuning_results.csv/tuning_plot.png (or the per-leaf embeddings_grid_*.png) and pick parameters by hand.

---

**Nota (04-08-26)**: il blocco "## Config" sopra era rimasto disallineato dalla struttura reale delle cartelle (dichiarava solo 2 `nested_params`, 60 combinazioni) — corretto qui ricostruendolo dalla struttura reale su disco (12 leaf, 15 righe ciascuno nei rispettivi `tuning_results.csv`, verificati), non da un file di config originale conservato altrove (non disponibile). Sotto, un secondo blocco con lo snapshot **live** di `config/registry/params_reduction.json`'s `umap`, per riferimento — attenzione: riflette lo stato del registro condiviso in questo momento, non necessariamente i parametri esatti che hanno prodotto ogni combinazione già presente in questa cartella (es. oggi il suo `tuning_grid.metric` non include più `"euclidean"` e il suo `n_components` non include più `2` - quei valori sono già stati coperti in una fase precedente, il registro è stato ristretto per proseguire solo sulle combinazioni mancanti).

## Registry snapshot (`config/registry/params_reduction.json` → `umap`, letto il 04-08-26)

```json
{
  "tag_param": "metric",
  "tag_prefix": "m_",
  "params": {
    "n_neighbors": 15,
    "min_dist": 0.0,
    "n_components": 2,
    "random_state": 0,
    "metric": "jaccard"
  },
  "tuning_grid": {
    "metric": [
      "jaccard",
      "dice"
    ],
    "n_components": [
      5,
      10
    ],
    "regress_out_volume": [
      false
    ],
    "n_neighbors": [
      5,
      15,
      30,
      50,
      100
    ],
    "min_dist": [
      0.0,
      0.1,
      0.25
    ]
  },
  "nested_params": [
    "metric",
    "n_components",
    "regress_out_volume"
  ],
  "trustworthiness_n_neighbors": 10
}
```
