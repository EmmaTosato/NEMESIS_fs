# Le pipeline attraversate da ogni matrice

Vista d'insieme delle tornate di esperimenti: dalla matrice di partenza al clustering di produzione. Il dettaglio di ogni sessione sta nel suo file, elencato nel [README](README.md).

## Seconda tornata — s1.4, s2.4

Una matrice per schema. Ogni matrice parte una volta sola e si dirama dove le pipeline divergono.

### s1.4-vol — lesione

```mermaid
flowchart LR
    classDef pending stroke-dasharray: 5 5

    subgraph COL0["Input matrix"]
        direction TB
        R14["s1.4-vol<br/>lesion_matrix<br/>07-10<br/>5845 subj."]
    end

    subgraph COL1["Dim Red. — Tuning"]
        direction TB
        T14["07-10<hr/><b>UMAP</b><br/>dice/euclidean<br/>nc2/nc3/nc10"]
        N14T["no dim reduction"]
    end

    subgraph COL2["Dim Red. — Prod."]
        direction TB
        P14["08-10<hr/><b>UMAP</b><br/>dice/euclidean<br/>nc2/nc3/nc10<hr/>12-10<br/><b>UMAP</b><br/>dice nc2<br/>n_neighbors 50<br/>(gemello 2D di nc10,<br/>solo per la vista)"]
        N14P["no dim reduction"]
    end

    subgraph COL3["Clustering — Tuning"]
        direction TB
        CT14["08-10<hr/>UMAP dice/euclidean<br/>nc2/nc3/nc10<br/>agglomerative, HDBSCAN"]
        CT14S["15-10<hr/>UMAP dice/euclidean<br/>nc2/nc3/nc10<br/>HDBSCAN soft<br/>mcs x ms x eom/leaf"]
        CT14R["08-10<hr/>raw dice/euclidean<br/>221955 voxel<br/>ADP"]
    end

    subgraph COL4["Clustering — Prod."]
        direction TB
        CP14["12-10<hr/>UMAP dice/euclidean<br/>nc2/nc10<br/>agglomerative ward: 23 run<br/>HDBSCAN: 40 run<br/>(67 run)"]
        CP14S["15-10<hr/>UMAP dice/euclidean<br/>nc2/nc10<br/>HDBSCAN soft: 12 run"]
        CP14R["12-10<hr/>raw dice<br/>221955 voxel<br/>ADP Z 2.5-4.0<br/>(4 run)"]
    end

    R14 --> T14 --> P14
    P14 --> CT14 --> CP14
    P14 --> CT14S --> CP14S
    R14 --> N14T --> N14P --> CT14R --> CP14R
```

### s2.4-vol — SDC voxelwise

Matrice **del 16-10**, ricostruita con i voxel fuori dal brain azzerati (227235 colonne). Manca una run in produzione: `hdbscan_soft` nc10, `min_cluster_size=100`, `min_samples=20`, `eom`.

```mermaid
flowchart LR
    classDef pending stroke-dasharray: 5 5

    subgraph COL0["Input matrix"]
        direction TB
        R24["s2.4-vol<br/>sdc_matrix<br/>16-10<br/>5845 subj.<br/>227235 colonne"]
    end

    subgraph COL1["Dim Red. — Tuning"]
        direction TB
        T24["16-10<hr/><b>UMAP</b><br/>euclidean<br/>nc2/nc3/nc10"]
        T24P["16-10<hr/><b>PCA</b><br/>none/varimax<br/>2-150 componenti"]
        N24T["no dim reduction"]
    end

    subgraph COL2["Dim Red. — Prod."]
        direction TB
        P24["16-10<hr/><b>UMAP</b><br/>euclidean<br/>nc2/nc3/nc10"]
        P24P["16-10 / 17-10<hr/><b>PCA</b><br/>non ruotata<br/>nc42, nc30<hr/>18-10<br/><b>PCA</b><br/>nc12, nc2<br/>(solo per la vista)"]
        N24P["no dim reduction"]
    end

    subgraph COL3["Clustering — Tuning"]
        direction TB
        CT24["16-10<hr/>UMAP euclidean<br/>nc2/nc3/nc10<br/>agglomerative, HDBSCAN"]
        CT24S["16-10<hr/>UMAP euclidean<br/>nc2/nc3/nc10<br/>HDBSCAN soft<br/>mcs x ms x eom/leaf"]
        CT24P["17-10<hr/>PCA nc42, nc30<br/>agglomerative, HDBSCAN<hr/>18-10<br/>PCA nc2, nc12<br/>agglomerative, HDBSCAN<hr/>19-10<br/>PCA nc2/nc12/nc30/nc42<br/>HDBSCAN soft<br/>mcs x ms x eom/leaf"]
        CT24R["16-10<hr/>raw dice/euclidean<br/>227235 voxel<br/>ADP"]
    end

    subgraph COL4["Clustering — Prod."]
        direction TB
        CP24["16-10<hr/>UMAP euclidean<br/>nc2/nc10<br/>agglomerative: 14 run<br/>HDBSCAN: 7 run<br/>(21 run)"]
        CP24S["16-10<hr/>UMAP euclidean<br/>nc2/nc10<br/>HDBSCAN soft: 4 run su 5"]
        CP24P["18-10 / 19-10<hr/>PCA nc42, nc30, nc12, nc2<br/>agglomerative<br/>ward k=3: 4 run<br/>HDBSCAN: 20 run<br/>HDBSCAN soft: 20 run<br/>(44 run)"]
        CP24R["16-10<hr/>raw dice<br/>227235 voxel<br/>ADP Z 2.0-3.5<br/>(4 run)"]
    end

    R24 --> T24 --> P24
    P24 --> CT24 --> CP24
    P24 --> CT24S --> CP24S
    R24 --> T24P --> P24P --> CT24P --> CP24P
    R24 --> N24T --> N24P --> CT24R --> CP24R
```

### s2.4-stream — SDC per tratto

Per tratto (87), non toccata dalla correzione dei voxel fuori dal brain.

```mermaid
flowchart LR
    classDef pending stroke-dasharray: 5 5

    subgraph COL0["Input matrix"]
        direction TB
        R25["s2.4-stream<br/>sdc_matrix<br/>07-10<br/>5831 subj.<br/>87 tratti"]
    end

    subgraph COL1["Dim Red. — Tuning"]
        direction TB
        N25T["no dim reduction"]
    end

    subgraph COL2["Dim Red. — Prod."]
        direction TB
        P25["14-10<hr/><b>UMAP</b><br/>euclidean nc2<br/>(solo per la vista)"]
        N25P["no dim reduction"]
    end

    subgraph COL3["Clustering — Tuning"]
        direction TB
        CT25["09-10<hr/>raw<br/>87 tratti<br/>agglomerative, HDBSCAN"]
        CT25R["08-10<hr/>raw dice/euclidean<br/>87 tratti<br/>ADP"]
        CT25S["15-10<hr/>raw<br/>87 tratti<br/>HDBSCAN soft<br/>mcs x ms x eom/leaf"]
    end

    subgraph COL4["Clustering — Prod."]
        direction TB
        CP25["14-10<hr/>raw<br/>87 tratti<br/>agglomerative<br/>average/cosine: 7 run<br/>HDBSCAN: 6 run<br/>(13 run)"]
        CP25R["14-10<hr/>raw dice<br/>87 tratti<br/>ADP Z 2.5-6.0<br/>(6 run)"]
        CP25S["nessuna combinazione usabile"]:::pending
    end

    R25 --> N25T --> P25 --> CT25 --> CP25
    N25T --> N25P --> CT25R --> CP25R
    N25P --> CT25S -.-> CP25S
```

## s2.4-vol del 07-10 — storico

Matrice **vecchia**, senza `correct_out_of_brain`: 291345 colonne, 64110 delle quali fuori dalla maschera cerebrale. La ricostruisce la s2.4-vol del 16-10 (sopra). I risultati stanno in `results/legacy/sdc_s2.4-vol_07-10/`.

```mermaid
flowchart LR
    classDef pending stroke-dasharray: 5 5

    subgraph COL0["Input matrix"]
        direction TB
        R24["s2.4-vol<br/>sdc_matrix<br/>07-10<br/>5845 subj.<br/>291345 colonne"]
    end

    subgraph COL1["Dim Red. — Tuning"]
        direction TB
        T24["07-10<hr/><b>UMAP</b><br/>euclidean<br/>nc2/nc3/nc10"]
        N24T["no dim reduction"]
    end

    subgraph COL2["Dim Red. — Prod."]
        direction TB
        P24["08-10<hr/><b>UMAP</b><br/>euclidean<br/>nc2/nc3/nc10"]
        N24P["no dim reduction"]
    end

    subgraph COL3["Clustering — Tuning"]
        direction TB
        CT24["09-10<hr/>UMAP euclidean<br/>nc2/nc3/nc10<br/>agglomerative, HDBSCAN"]
        CT24S["15-10<hr/>UMAP euclidean<br/>nc2/nc3/nc10<br/>HDBSCAN soft<br/>mcs x ms x eom/leaf"]
        CT24R["08-10<hr/>raw dice/euclidean<br/>291345 voxel<br/>ADP"]
    end

    subgraph COL4["Clustering — Prod."]
        direction TB
        CP24["12-10<hr/>UMAP euclidean<br/>nc2/nc10<br/>agglomerative: 14 run<br/>HDBSCAN: 7 run<br/>(21 run)"]
        CP24S["15-10 / 16-10<hr/>UMAP euclidean<br/>nc2/nc10<br/>HDBSCAN soft: 5 run"]
        CP24R["12-10<hr/>raw dice<br/>291345 voxel<br/>ADP Z 2.0-3.5<br/>(4 run)"]
    end

    R24 --> T24 --> P24
    P24 --> CT24 --> CP24
    P24 --> CT24S --> CP24S
    R24 --> N24T --> N24P --> CT24R --> CP24R
```

## Prima tornata — s1.1, s1.2, s2.1, s2.2

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

    subgraph COL1["Dim Red. — Tuning"]
        direction TB
        T11["03/04-08 + 13-08<hr/><b>UMAP</b><br/>dice/euclidean<br/>nc2/nc3/nc10<hr/><b>t-SNE</b><br/>dice/euclidean<br/>nc2"]
        T12["26-08<hr/><b>UMAP</b><br/>dice/euclidean<br/>nc2/nc3<hr/><b>t-SNE</b><br/>dice/euclidean<br/>nc2"]
        T12R["no dim reduction"]
        T21["28-08<hr/><b>UMAP</b><br/>euclidean<br/>nc2/nc3<hr/><b>t-SNE</b><br/>euclidean<br/>nc2"]
        T22["07-09<hr/><b>UMAP</b><br/>euclidean<br/>nc2/nc3<hr/><b>t-SNE</b><br/>euclidean<br/>nc2"]
        T23["no dim reduction"]
    end

    subgraph COL2["Dim Red. — Prod."]
        direction TB
        P11["11-08<hr/><b>UMAP</b><br/>dice/euclidean<br/>nc2/nc3/nc10<hr/><b>t-SNE</b><br/>dice/euclidean<br/>nc2"]
        P12["28-08<hr/><b>UMAP</b><br/>dice/euclidean<br/>nc2/nc3/nc10<hr/><b>t-SNE</b><br/>dice/euclidean<br/>nc2"]
        P12R["no dim reduction"]
        P21["31-08<hr/><b>UMAP</b><br/>euclidean<br/>nc2/nc3<hr/><b>t-SNE</b><br/>euclidean<br/>nc2"]
        P22["07-09<hr/><b>UMAP</b><br/>euclidean<br/>nc2/nc3<hr/><b>t-SNE</b><br/>euclidean<br/>nc2"]
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

    subgraph COL4["Clustering — Prod."]
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

Dove il metodo di clustering non è indicato: k-means, agglomerative, gmm, hdbscan, spectral.
