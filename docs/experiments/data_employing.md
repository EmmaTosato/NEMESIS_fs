


# Data Employed in Pipelines

## First Experiment Session

```mermaid
flowchart LR
    classDef pending stroke-dasharray: 5 5

    subgraph COL0["Input matrix"]
        direction TB
        R11["s1.1-vol<br/>lesion_matrix<br/>21-07<br/>1150 subj."]
        R12["s1.2-vol<br/>lesion_matrix<br/>25-08<br/>5269 subj."]
        R12R["s1.2-vol<br/>lesion_matrix<br/>25-08<br/>5269 subj."]
        R21["s2.1-schaefer-200-tian-s2<br/>sdc_matrix<br/>27-08<br/>1119 subj."]
        R22["s2.2-vol<br/>sdc_matrix<br/>07-09<br/>1570 subj."]
        R23["s2.3-stream<br/>sdc_matrix<br/>87 tratti<br/>non ancora costruita"]:::pending
    end

    subgraph COL1["Dim Reduction — Tuning"]
        direction TB
        T11["03/04-08 + 13-08<hr/>UMAP dice/euclidean<br/>nc2/nc3/nc10<hr/>t-SNE dice/euclidean<br/>nc2"]
        T12["26-08<hr/>UMAP dice/euclidean<br/>nc2/nc3<hr/>t-SNE dice/euclidean<br/>nc2"]
        T12R["no dim reduction"]
        T21["28-08<hr/>UMAP euclidean<br/>nc2/nc3<hr/>t-SNE euclidean<br/>nc2"]
        T22["07-09<hr/>UMAP euclidean<br/>nc2/nc3<hr/>t-SNE euclidean<br/>nc2"]
        T23["no dim reduction"]
    end

    subgraph COL2["Dim Reduction — Production"]
        direction TB
        P11["11-08<hr/>UMAP dice/euclidean<br/>nc2/nc3/nc10<hr/>t-SNE dice/euclidean<br/>nc2"]
        P12["28-08<hr/>UMAP dice/euclidean<br/>nc2/nc3/nc10<hr/>t-SNE dice/euclidean<br/>nc2"]
        P12R["no dim reduction"]
        P21["31-08<hr/>UMAP euclidean<br/>nc2/nc3<hr/>t-SNE euclidean<br/>nc2"]
        P22["07-09<hr/>UMAP euclidean<br/>nc2/nc3<hr/>t-SNE euclidean<br/>nc2"]
        P23["no dim reduction"]
    end

    subgraph COL3["Clustering — Tuning"]
        direction TB
        CT11["31-08<hr/>UMAP dice/euclidean<br/>nc2/nc3/nc10"]
        CT12["01-09<hr/>UMAP euclidean<br/>nc2"]
        CT12R["03-09<hr/>raw dice/euclidean<br/>264274 voxel<br/>agglomerative"]
        CT21["01-09<hr/>UMAP euclidean<br/>nc2/nc3"]
        CT22["10-09<hr/>UMAP euclidean<br/>nc2/nc3"]
        CT23["non ancora lanciata<hr/>raw<br/>87 tratti"]:::pending
    end

    subgraph COL4["Clustering — Production"]
        direction TB
        CP11["01-09<hr/>UMAP euclidean nc2<br/>6 opzioni k"]
        CP12["03-09<hr/>UMAP euclidean nc2<br/>6 opzioni k"]
        CP12R["run degenere"]:::pending
        CP21["non ancora lanciata"]:::pending
        CP22["10-09<hr/>UMAP euclidean nc2<br/>8 opzioni k"]
        CP23["non ancora lanciata<hr/>raw<br/>k 4-10"]:::pending
    end

    R11 --> T11 --> P11 --> CT11 --> CP11
    R12 --> T12 --> P12 --> CT12 --> CP12
    R12R --> T12R --> P12R --> CT12R -.-> CP12R
    R21 --> T21 --> P21 --> CT21 -.-> CP21
    R22 --> T22 --> P22 --> CT22 --> CP22
    R23 -.-> T23 -.-> P23 -.-> CT23 -.-> CP23
```


## Notes
The clustering that are done when the methods are not specified:

- k-means
- agglomerative
- gmm
- hdbscan
- spectral


## Second Experiment Session

```mermaid
flowchart LR
    classDef pending stroke-dasharray: 5 5

    subgraph COL0["Input matrix"]
        direction TB
        R14["s1.4-vol<br/>lesion_matrix<br/>07-10<br/>5845 subj."]
        R24["s2.4-vol<br/>sdc_matrix<br/>07-10<br/>5845 subj."]
        R25["s2.4-stream<br/>sdc_matrix<br/>07-10<br/>5831 subj.<br/>87 tratti"]
        R14R["s1.4-vol<br/>lesion_matrix<br/>07-10<br/>5845 subj."]
        R24R["s2.4-vol<br/>sdc_matrix<br/>07-10<br/>5845 subj."]
        R25R["s2.4-stream<br/>sdc_matrix<br/>07-10<br/>5831 subj."]
    end

    subgraph COL1["Dim Reduction — Tuning"]
        direction TB
        T14["07-10<hr/>UMAP dice/euclidean<br/>nc2/nc3/nc10"]
        T24["07-10<hr/>UMAP euclidean<br/>nc2/nc3/nc10"]
        T25["no dim reduction"]
        T14R["no dim reduction"]
        T24R["no dim reduction"]
        T25R["no dim reduction"]
    end

    subgraph COL2["Dim Reduction — Production"]
        direction TB
        P14["08-10<hr/>UMAP dice/euclidean<br/>nc2/nc3/nc10<hr/>12-10<br/>UMAP dice nc2<br/>n_neighbors 50<br/>(gemello 2D di nc10,<br/>solo per la vista)"]
        P24["08-10<hr/>UMAP euclidean<br/>nc2/nc3/nc10"]
        P25["14-10<hr/>UMAP euclidean nc2<br/>(solo per la vista)"]
        P14R["no dim reduction"]
        P24R["no dim reduction"]
        P25R["no dim reduction"]
    end

    subgraph COL3["Clustering — Tuning"]
        direction TB
        CT14["08-10<hr/>UMAP dice/euclidean<br/>nc2/nc3/nc10<br/>agglomerative, HDBSCAN"]
        CT24["09-10<hr/>UMAP euclidean<br/>nc2/nc3/nc10<br/>agglomerative, HDBSCAN"]
        CT25["09-10<hr/>raw<br/>87 tratti<br/>agglomerative, HDBSCAN"]
        CT14R["08-10<hr/>raw dice/euclidean<br/>221955 voxel<br/>ADP"]
        CT24R["08-10<hr/>raw dice/euclidean<br/>291345 voxel<br/>ADP"]
        CT25R["08-10<hr/>raw dice/euclidean<br/>87 tratti<br/>ADP"]
    end

    subgraph COL4["Clustering — Production"]
        direction TB
        CP14["12-10<hr/>UMAP dice/euclidean<br/>nc2/nc10<br/>agglomerative ward: 23 run<br/>HDBSCAN: 40 run<br/>(67 run)"]
        CP24["12-10<hr/>UMAP euclidean<br/>nc2/nc10<br/>agglomerative: 14 run<br/>HDBSCAN: 7 run<br/>(21 run)"]
        CP25["14-10<hr/>raw<br/>87 tratti<br/>agglomerative average/cosine: 7 run<br/>HDBSCAN: 6 run<br/>(13 run)"]
        CP14R["12-10<hr/>raw dice<br/>221955 voxel<br/>ADP Z 2.5-4.0<br/>(4 run)"]
        CP24R["12-10<hr/>raw dice<br/>291345 voxel<br/>ADP Z 2.0-3.5<br/>(4 run)"]
        CP25R["14-10<hr/>raw dice<br/>87 tratti<br/>ADP Z 2.5-6.0<br/>(6 run)"]
    end

    R14 --> T14 --> P14 --> CT14 --> CP14
    R24 --> T24 --> P24 --> CT24 --> CP24
    R25 --> T25 --> P25 --> CT25 --> CP25
    R14R --> T14R --> P14R --> CT14R --> CP14R
    R24R --> T24R --> P24R --> CT24R --> CP24R
    R25R --> T25R --> P25R --> CT25R --> CP25R
```

## Notes
- **Produzione di clustering, 12-10 e 14-10:** 111 run. Per ogni matrice si sono prodotti i candidati "buoni" e "discreti" del tuning del 12-10 ([`clustering/s1_tuning.md`](clustering/s1_tuning.md), [`clustering/s2_tuning.md`](clustering/s2_tuning.md)); i diari sono [`clustering/s1_production.md`](clustering/s1_production.md) e [`clustering/s2_production.md`](clustering/s2_production.md).

