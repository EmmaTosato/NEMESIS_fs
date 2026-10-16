# Le pipeline attraversate da ogni matrice

Vista d'insieme delle tornate di esperimenti: dalla matrice di partenza al clustering di produzione. Il dettaglio di ogni sessione sta nel suo file, elencato nel [README](README.md).

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

Dove il metodo di clustering non è indicato: k-means, agglomerative, gmm, hdbscan, spectral.

## s2.4-vol del 07-10 — matrice con i voxel fuori dal brain non azzerati

Le run che si basano sulla matrice **vecchia** di s2.4-vol (291345 colonne, 64110 delle quali fuori dalla maschera cerebrale, senza `correct_out_of_brain`). Restano come storico della pipeline SDC prima della correzione; la matrice del 16-10 le rifà nella seconda tornata, qui sotto.

```mermaid
flowchart LR
    classDef pending stroke-dasharray: 5 5

    subgraph COL0["Input matrix"]
        direction TB
        R24["s2.4-vol<br/>sdc_matrix<br/>07-10<br/>5845 subj.<br/>291345 colonne"]
        R24R["s2.4-vol<br/>sdc_matrix<br/>07-10<br/>5845 subj."]
        R24S["s2.4-vol<br/>sdc_matrix<br/>07-10<br/>5845 subj."]
    end

    subgraph COL1["Dim Reduction — Tuning"]
        direction TB
        T24["07-10<hr/>UMAP euclidean<br/>nc2/nc3/nc10<hr/>16-10<br/>PCA none/varimax<br/>2-150 componenti"]
        T24R["no dim reduction"]
        T24S["07-10<hr/>UMAP euclidean<br/>nc2/nc3/nc10"]
    end

    subgraph COL2["Dim Reduction — Production"]
        direction TB
        P24["08-10<hr/>UMAP euclidean<br/>nc2/nc3/nc10"]
        P24R["no dim reduction"]
        P24S["08-10<hr/>UMAP euclidean<br/>nc2/nc3/nc10"]
    end

    subgraph COL3["Clustering — Tuning"]
        direction TB
        CT24["09-10<hr/>UMAP euclidean<br/>nc2/nc3/nc10<br/>agglomerative, HDBSCAN"]
        CT24R["08-10<hr/>raw dice/euclidean<br/>291345 voxel<br/>ADP"]
        CT24S["15-10<hr/>UMAP euclidean<br/>nc2/nc3/nc10<br/>HDBSCAN soft<br/>mcs x ms x eom/leaf"]
    end

    subgraph COL4["Clustering — Production"]
        direction TB
        CP24["12-10<hr/>UMAP euclidean<br/>nc2/nc10<br/>agglomerative: 14 run<br/>HDBSCAN: 7 run<br/>(21 run)"]
        CP24R["12-10<hr/>raw dice<br/>291345 voxel<br/>ADP Z 2.0-3.5<br/>(4 run)"]
        CP24S["15-10 / 16-10<hr/>UMAP euclidean<br/>nc2/nc10<br/>HDBSCAN soft: 5 run"]
    end

    R24 --> T24 --> P24 --> CT24 --> CP24
    R24R --> T24R --> P24R --> CT24R --> CP24R
    R24S --> T24S --> P24S --> CT24S --> CP24S
```

Tre rami per matrice: principale (UMAP, poi agglomerative e HDBSCAN), ADP sulla matrice grezza, `hdbscan_soft`. Il tuning PCA del 16-10 (`results/sdc/dim_reduction/tuning/pca`) non ha produzione né clustering in `results/`: il clustering sui 42 punteggi è un prototipo in `tmp/`, fuori dal repo ([s2.4-vol](s2.4-vol.md)).

## Seconda tornata — s1.4, s2.4

La lesione (s1.4-vol, 07-10) e le due SDC: s2.4-vol **del 16-10**, ricostruita con i voxel fuori dal brain azzerati (227235 colonne), e s2.4-stream (07-10, per tratto, non toccata dalla correzione). Le run di s2.4-vol sulla matrice vecchia del 07-10 sono nello schema precedente. I nodi tratteggiati di s2.4-vol sono da rifare: le scelte di produzione sono le stesse del 12 e del 14 ottobre, e la PCA si fa altrove.

```mermaid
flowchart LR
    classDef pending stroke-dasharray: 5 5

    subgraph COL0["Input matrix"]
        direction TB
        R14["s1.4-vol<br/>lesion_matrix<br/>07-10<br/>5845 subj."]
        R24["s2.4-vol<br/>sdc_matrix<br/>16-10<br/>5845 subj.<br/>227235 colonne"]
        R25["s2.4-stream<br/>sdc_matrix<br/>07-10<br/>5831 subj.<br/>87 tratti"]
        R14R["s1.4-vol<br/>lesion_matrix<br/>07-10<br/>5845 subj."]
        R24R["s2.4-vol<br/>sdc_matrix<br/>16-10<br/>5845 subj."]
        R25R["s2.4-stream<br/>sdc_matrix<br/>07-10<br/>5831 subj."]
        R14S["s1.4-vol<br/>lesion_matrix<br/>07-10<br/>5845 subj."]
        R24S["s2.4-vol<br/>sdc_matrix<br/>16-10<br/>5845 subj."]
        R25S["s2.4-stream<br/>sdc_matrix<br/>07-10<br/>5831 subj."]
    end

    subgraph COL1["Dim Reduction — Tuning"]
        direction TB
        T14["07-10<hr/>UMAP dice/euclidean<br/>nc2/nc3/nc10"]
        T24["16-10<hr/>UMAP euclidean<br/>nc2/nc3/nc10"]
        T25["no dim reduction"]
        T14R["no dim reduction"]
        T24R["no dim reduction"]
        T25R["no dim reduction"]
        T14S["07-10<hr/>UMAP dice/euclidean<br/>nc2/nc3/nc10"]
        T24S["16-10<hr/>UMAP euclidean<br/>nc2/nc3/nc10"]
        T25S["no dim reduction"]
    end

    subgraph COL2["Dim Reduction — Production"]
        direction TB
        P14["08-10<hr/>UMAP dice/euclidean<br/>nc2/nc3/nc10<hr/>12-10<br/>UMAP dice nc2<br/>n_neighbors 50<br/>(gemello 2D di nc10,<br/>solo per la vista)"]
        P24["16-10<hr/>UMAP euclidean<br/>nc2/nc3/nc10"]
        P25["14-10<hr/>UMAP euclidean nc2<br/>(solo per la vista)"]
        P14R["no dim reduction"]
        P24R["no dim reduction"]
        P25R["no dim reduction"]
        P14S["08-10<hr/>UMAP dice/euclidean<br/>nc2/nc3/nc10"]
        P24S["16-10<hr/>UMAP euclidean<br/>nc2/nc3/nc10"]
        P25S["no dim reduction"]
    end

    subgraph COL3["Clustering — Tuning"]
        direction TB
        CT14["08-10<hr/>UMAP dice/euclidean<br/>nc2/nc3/nc10<br/>agglomerative, HDBSCAN"]
        CT24["da rifare<hr/>UMAP euclidean<br/>nc2/nc3/nc10<br/>agglomerative, HDBSCAN"]:::pending
        CT25["09-10<hr/>raw<br/>87 tratti<br/>agglomerative, HDBSCAN"]
        CT14R["08-10<hr/>raw dice/euclidean<br/>221955 voxel<br/>ADP"]
        CT24R["da rifare<hr/>raw dice/euclidean<br/>227235 voxel<br/>ADP"]:::pending
        CT25R["08-10<hr/>raw dice/euclidean<br/>87 tratti<br/>ADP"]
        CT14S["15-10<hr/>UMAP dice/euclidean<br/>nc2/nc3/nc10<br/>HDBSCAN soft<br/>mcs x ms x eom/leaf"]
        CT24S["da rifare<hr/>UMAP euclidean<br/>nc2/nc3/nc10<br/>HDBSCAN soft<br/>mcs x ms x eom/leaf"]:::pending
        CT25S["15-10<hr/>raw<br/>87 tratti<br/>HDBSCAN soft<br/>mcs x ms x eom/leaf"]
    end

    subgraph COL4["Clustering — Production"]
        direction TB
        CP14["12-10<hr/>UMAP dice/euclidean<br/>nc2/nc10<br/>agglomerative ward: 23 run<br/>HDBSCAN: 40 run<br/>(67 run)"]
        CP24["non ancora lanciata"]:::pending
        CP25["14-10<hr/>raw<br/>87 tratti<br/>agglomerative average/cosine: 7 run<br/>HDBSCAN: 6 run<br/>(13 run)"]
        CP14R["12-10<hr/>raw dice<br/>221955 voxel<br/>ADP Z 2.5-4.0<br/>(4 run)"]
        CP24R["non ancora lanciata"]:::pending
        CP25R["14-10<hr/>raw dice<br/>87 tratti<br/>ADP Z 2.5-6.0<br/>(6 run)"]
        CP14S["15-10<hr/>UMAP dice/euclidean<br/>nc2/nc10<br/>HDBSCAN soft: 12 run"]
        CP24S["non ancora lanciata"]:::pending
        CP25S["nessuna combinazione usabile"]:::pending
    end

    R14 --> T14 --> P14 --> CT14 --> CP14
    R24 --> T24 --> P24 -.-> CT24 -.-> CP24
    R25 --> T25 --> P25 --> CT25 --> CP25
    R14R --> T14R --> P14R --> CT14R --> CP14R
    R24R --> T24R -.-> P24R -.-> CT24R -.-> CP24R
    R25R --> T25R --> P25R --> CT25R --> CP25R
    R14S --> T14S --> P14S --> CT14S --> CP14S
    R24S --> T24S --> P24S -.-> CT24S -.-> CP24S
    R25S --> T25S --> P25S --> CT25S -.-> CP25S
```

Ogni matrice compare tre volte: il ramo principale (UMAP, poi agglomerative e HDBSCAN), il ramo ADP sulla matrice grezza, e il ramo `hdbscan_soft`. Le date dei nodi di s2.4-vol si scrivono man mano che le run esistono.
