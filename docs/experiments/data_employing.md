


# Data Employed in Pipelines

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
        R23["s2.3<br/>sdc_matrix<br/>dati in download<br/>N/A"]:::pending
    end

    subgraph COL1["Dim Reduction — Tuning"]
        direction TB
        T11["03/04-08 + 13-08<hr/>UMAP dice/euclidean<br/>nc2/nc3/nc10<hr/>t-SNE dice/euclidean<br/>nc2"]
        T12["26-08<hr/>UMAP dice/euclidean<br/>nc2/nc3<hr/>t-SNE dice/euclidean<br/>nc2"]
        T12R["no dim reduction"]
        T21["28-08<hr/>UMAP euclidean<br/>nc2/nc3<hr/>t-SNE euclidean<br/>nc2"]
        T22["07-09<hr/>UMAP euclidean<br/>nc2/nc3<hr/>t-SNE euclidean<br/>nc2"]
        T23["in attesa dei dati"]:::pending
    end

    subgraph COL2["Dim Reduction — Production"]
        direction TB
        P11["11-08<hr/>UMAP dice/euclidean<br/>nc2/nc3/nc10<hr/>t-SNE dice/euclidean<br/>nc2"]
        P12["28-08<hr/>UMAP dice/euclidean<br/>nc2/nc3/nc10<hr/>t-SNE dice/euclidean<br/>nc2"]
        P12R["no dim reduction"]
        P21["31-08<hr/>UMAP euclidean<br/>nc2/nc3<hr/>t-SNE euclidean<br/>nc2"]
        P22["07-09<hr/>UMAP euclidean<br/>nc2/nc3<hr/>t-SNE euclidean<br/>nc2"]
        P23["in attesa dei dati"]:::pending
    end

    subgraph COL3["Clustering — Tuning"]
        direction TB
        CT11["31-08<hr/>UMAP dice/euclidean<br/>nc2/nc3/nc10"]
        CT12["01-09<hr/>UMAP euclidean<br/>nc2"]
        CT12R["03-09<hr/>raw dice/euclidean<br/>264274 voxel<br/>agglomerative"]
        CT21["01-09<hr/>UMAP euclidean<br/>nc2/nc3"]
        CT22["10-09<hr/>UMAP euclidean<br/>nc2/nc3"]
        CT23["in attesa dei dati"]:::pending
    end

    subgraph COL4["Clustering — Production"]
        direction TB
        CP11["01-09<hr/>UMAP euclidean nc2<br/>6 opzioni k"]
        CP12["03-09<hr/>UMAP euclidean nc2<br/>6 opzioni k"]
        CP12R["run degenere"]:::pending
        CP21["non ancora lanciata"]:::pending
        CP22["10-09<hr/>UMAP euclidean nc2<br/>8 opzioni k"]
        CP23["non ancora lanciata"]:::pending
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

**s2.3** copre l'SDC per tutti i dataset in scope; il download dei dati è ancora in corso, quindi la sdc matrix non è ancora costruibile. Una volta completato il download: costruire la sdc matrix, poi replicare su s2.3 il resto della pipeline già percorsa per s2.2 (dim reduction tuning/produzione, clustering tuning/produzione).

