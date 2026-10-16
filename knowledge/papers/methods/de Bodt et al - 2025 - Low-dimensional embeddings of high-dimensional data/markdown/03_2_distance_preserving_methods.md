## 3 . 2 Distance-preserving methods

While linear methods construct an explicit mapping from the high-dimensional to the low-dimensional space, some other methods directly optimize the placement of lowdimensional points. Such methods are sometimes imprecisely referred to as nonlinear dimensionality reduction, but it is more accurate to call them non-parametric . One prominent example dating back to the 1950 s and 1960 s is multidimensional scaling (MDS), which maximizes the preservation of high-dimensional distances in the lowdimensional embedding space (Borg and Groenen, 1997 ). While traditional implementations are slow, the recently introduced SQuadMDS algorithm (Lambert et al., 2022 a) provides a fast approximation suitable for large datasets.

MDS exists in several flavors. What is described above is called metric MDS . There is a simpler variant known

***Table 1 : Selection of widely used embedding methods (Section 3 ). Typical use cases and typical target dimensionality are based on the most common uses and not exhaustive. The 'SVD' column indicates whether the exact solution can be obtained via singular value decomposition or eigendecomposition.***

| Method | Loss function | Typical dim. | Parametric | SVD | Typical use cases |
|---|---|---|---|---|---|
| PCA | Reconstruction error | 1 - 100 | linear | ✓ | Preprocess; visualize |
| Metric MDS | Distance preservation | 2 or 3 | × | × | Visualize global structure |
| Isomap | Geodesic distance preserv. | 2 or 3 | × | ✓ | Visualize contin. structures |
| Factor analysis | Likelihood | 1 - 10 | linear | × | Interpret latent variables |
| GTM | Likelihood | 1 or 2 | non-linear | × | Visualize contin. structures |
| Laplacian eig. | Constrained neighb. preserv. | 1 - 10 | × | ✓ | Preprocess; visualize |
| LLE | Local reconstruction | 1 - 10 | × | ✓ | Visualize contin. structures |
| PHATE | Potential distance preserv. | 2 or 3 | × | × | Visualize contin. structures |
| t -SNE | Neighbor preservation | 2 or 3 | × | × | Visualize clusters |
| UMAP | Neighbor preservation | 2 - 10 | × | × | Visualize clusters; preprocess |
| Autoencoders | Reconstruction error | 2 - 100 | non-linear | × | Preprocess; visualize |

as classical MDS , or Torgerson MDS (Torgerson, 1952 ), or principal coordinates analysis (PCoA) (Gower, 1966 ), which can be solved exactly via eigendecomposition and, when applied to pairwise Euclidean distances, is equivalent to PCA. Non-metric MDS additionally optimizes a monotonic transformation of high-dimensional distances (Shepard, 1962 a,b; Kruskal, 1964 a,b), but scalable implementations are lacking. Weighted distance-preservation schemes include Sammon's mapping (Sammon, 1969 ) and curvilinear component analysis (CCA) (Demartines and H´ erault, 1997 ), which favor the preservation of short highdimensional and low-dimensional distances, respectively.

