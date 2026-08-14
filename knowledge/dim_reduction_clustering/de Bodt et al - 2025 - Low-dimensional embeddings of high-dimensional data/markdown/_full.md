### L ow -dimensional embeddings of high -dimensional data

Cyril de Bodt 1 , 2 ,* , Alex Diaz-Papkovich 3 ,* , Michael Bleher 4 , Kerstin Bunte 5 , Corinna Coupette 6 , 7 , 8 , Sebastian Damrich 9 , Enrique Fita Sanmartin 10 , 11 , Fred A. Hamprecht 12 , Em˝ oke- ´ Agnes Horv´ at 13 , Dhruv Kohli 14 , Smita Krishnaswamy 15 , John A. Lee 2 , Boudewijn P. F. Lelieveldt 16 , Leland McInnes 17 , Ian T. Nabney 18 , Maximilian Noichl 19 , Pavlin G. Poliˇ car 20 , Bastian Rieck 21 , Guy Wolf 10 , 11 , Gal Mishne 14 ,+ , and Dmitry Kobak 9 ,+

* Equal contribution

> + Equal contribution

1 Department of Mathematics and Namur Research Institute for Complex Systems (naXys), University of Namur, Belgium 2 ICTEAM Institute, UCLouvain, Louvain-la-Neuve, Belgium 3 Data Science Institute, Brown University, Providence, Rhode Island, United States 4 Institute for Mathematics, Heidelberg University, Germany 5 University of Groningen, The Netherlands 6 Aalto University, Finland 7 Max Planck Institute for Informatics, Saarbr¨ ucken, Germany 8 Max Planck Institute for Tax Law and Public Finance, Munich, Germany 9 Hertie Institute for AI in Brain Health, University of T¨ ubingen, Germany 10 Universit´ e de Montr´ eal, Canada 11 Mila, Montr´ eal, Canada 12 IWR, Heidelberg University, Germany 13 Northwestern University, Evanston, Illinois, United States 14 UC San Diego, California, United States 15 Yale University, New Haven, Connecticut, United States 16 Department of Radiology, Leiden University Medical Center, The Netherlands 17 Tutte Institute for Mathematics and Computing, Ottawa, Canada 18 University of Bristol, United Kingdom

19 Department of Philosophy and Religious Studies, Utrecht University, The Netherlands 20 Faculty of Computer and Information Science, University of Ljubljana, Slovenia 21 University of Fribourg, Switzerland

/a0 dmitry.kobak@uni-tuebingen.de

August 25 ,

2025

### Abstract

Large collections of high-dimensional data have become nearly ubiquitous across many academic fields and application domains, ranging from biology to the humanities. Since working directly with high-dimensional data poses challenges, the demand for algorithms that create low-dimensional representations, or embeddings , for data visualization, exploration, and analysis is now greater than ever. In recent years, numerous embedding algorithms have been developed, and their usage has become widespread in research and industry. This surge of interest has resulted in a large and fragmented research field that faces technical challenges alongside fundamental debates, and it has left practitioners without clear guidance on how to effectively employ existing methods. Aiming to increase coherence and facilitate future work, in this review we provide a detailed and critical overview of recent developments, derive a list of best practices for creating and using low-dimensional embeddings, evaluate popular approaches on a variety of datasets, and discuss the remaining challenges and open problems in the field.

## 1 Introduction

At the heart of scientific inquiry lie curiosity and intuition. Scientists observe the world, detect patterns, create hypotheses, and make inferences. The ever-increasing amount of data collected as part of virtually all scientific endeavors requires researchers to observe the data, detect patterns in the data, and formulate hypotheses about the data. Since John Tukey famously summarized these aims as exploratory data analysis (EDA) in the 1970 s (Tukey, 1977 ), both the number of samples and the number of features in a typical dataset have increased by several orders of magnitude, motivating the development of new analytical approaches. One of these approaches is dimensionality reduction .

Large collections of high-dimensional data have become widespread in almost every discipline, with samples of interest ranging from molecules in chemistry to publications in the digital humanities and single cells or organisms in biology. These samples are typically characterized by thousands of features, such as atomic properties, word frequencies, or gene-expression measurements, resulting in high-dimensional data. However, empirical observations in many domains suggest that while the data are observed in high dimensions, the number of intrinsic dimensions that characterize the variability in the data is often much smaller. This has motivated the development of multiple dimensionality-reduction methods that learn low-dimensional representations, commonly referred to as embeddings , of high-dimensional data.

Low-dimensional embeddings typically have to sacrifice some high-dimensional information and distort the original data (Welch, 1974 ; Johnson and Lindenstrauss, 1984 ; Larsen and Nelson, 2017 ; Nonato and Aupetit, 2018 ). This has motivated the development of many algorithms that make different trade-offs and preserve different properties of the data, resulting in a fast-growing and dynamic area of machine-learning research (Lee and Verleysen, 2007 ; Espadoto et al., 2019 ; Nguyen and Holmes, 2019 ; Armstrong et al., 2022 ; Wang et al., 2023 a; Meil˘ a and Zhang, 2024 ; Wayland et al., 2024 ). The resulting methods are often used as a preprocessing step to reduce highdimensional noise or to render downstream tasks such as clustering or prediction more computationally tractable.

Embeddings have also become a powerful and popular tool in exploratory data analysis, enabling interpretable representations in two or three dimensions that are amenable to direct visualization and human interaction. This has motivated the widespread adoption of low-dimensional embeddings across disciplines as different as single-cell biology (Kobak and Berens, 2019 ; Becht et al., 2019 ), human genetics (Diaz-Papkovich et al., 2019 ), biochemistry (Durairaj et al., 2023 ), philosophy (Noichl, 2021 ), metascience (Gonz´ alez-M´ arquez et al., 2024 ), and sports analytics (Garc´ ıa-Aliaga et al., 2021 ).

As the field evolves, it becomes increasingly important to not only develop better embedding methods but also establish best practices for the creation, evaluation, application, presentation, and documentation of lowdimensional embeddings in the scientific process. In this review, following a reflection on the role of lowdimensional embeddings in the scientific enterprise (Section 2 ), we provide an overview of common approaches to dimensionality reduction and highlight popular algorithms representing each approach, focusing on their underlying motivations, advantages, and limitations (Section 3 ). We showcase selected algorithms on several example datasets from different research areas to illustrate the trade-offs involved (Section 4 ), offer specific guidance and best practices relevant to real-world applications (Section 5 ), and outline important challenges that remain in the field (Section 6 ). The paper is coauthored by the participants of the Dagstuhl seminar 24122 on Low-Dimensional Embeddings of High-Dimensional Data , held in March 2024 , and builds on our seminar discussions (Kobak et al., 2024 ).

## 2 Epistemic roles of embeddings

In scientific fields that collect large quantities of highdimensional data, such as single-cell transcriptomics, em-

bedding and visualizing data in 2 D has become a nearly ubiquitous practice. This has generated some debate and controversy, with critics emphasizing inevitable distortions (Wang et al., 2023 b; Chari and Pachter, 2023 ) and advocates emphasizing practical usefulness (Lause et al., 2024 ). Studies have also noted artifacts that can arise from visualizing data in low dimensions (Diaconis et al., 2008 ; Morton et al., 2017 ; Lebedev et al., 2019 ), and drew attention to frequent misuse of such embeddings (Jeon et al., 2025 ). This raises an epistemological question: What role do low-dimensional embeddings play in the scientific endeavor?

One answer is that (low-dimensional) embeddings fall into the category of exploratory data analysis. EDA (Tukey, 1977 ) was developed as a hypothesis-free approach to data analysis, complementing confirmatory approaches such as hypothesis testing. Visualization techniques play a critical role in EDA because, as Tukey argued, 'the picture-examining eye is the best finder we have of the wholly unanticipated' (Tukey, 1980 ). Hence, a low-dimensional visualization can reveal properties of the data that the researchers were not even considering (Yanai and Lercher, 2020 ), sometimes referred to as unknown unknowns .

Two-dimensional embeddings depicted as a scatter plot can be easily interpreted due to the Gestalt principles of human perception (Koffka, 1935 ), which characterize how humans group elements and recognize patterns. For example, the principle of proximity and the principle of common region state that objects placed near each other are perceived as similar, whereas those in separate areas are seen as distinct. Under this interpretation, rather than serving as tools for testing predefined hypotheses, embeddings serve a purpose similar to that of traditional box plots, scatter plots, and histograms, allowing researchers to inspect the data distribution. This inspection process can yield new insights and hypotheses that should subsequently be tested in a confirmatory framework - i.e., embeddings help with hypothesis generation .

In EDA, the epistemic role of low-dimensional embeddings resembles that of microscopes in biomedicine or telescopes in astronomy: They can immediately reveal information that is otherwise hidden from the naked eye. In our own work, we have found 2 D embeddings useful for guiding further research by exposing unexpected phenomena, such as clusters of retracted papers in collections of abstracts (Gonz´ alez-M´ arquez et al., 2024 ), a common precursor of two different cell types in mass-spectroscopic data (Li et al., 2018 ), or continuous variation in singlecell transcriptomic data (Scala et al., 2021 ). Furthermore, embeddings can safeguard against errors and assist quality control because suspicious clusters, outliers, or processing errors become immediately apparent (Anscombe,

1973 ; Yanai and Lercher, 2020 ). This helps to identify issues such as batch effects (Poliˇ car et al., 2023 ), incorrect labels (Diaz-Papkovich et al., 2023 ), or duplicated samples (B¨ ohm et al., 2023 ).

Beyond hypothesis generation, embeddings can also support scientific communication . When embeddings are used to present and explain research, they take the epistemic role of a map . Just like a map provides a concise, abstracted overview of a territory, embeddings can facilitate data navigation or guide the narrative in communicating analysis results. Even more importantly, embeddings can increase the transparency of scientific communication. Even when the datasets are openly published alongside a manuscript, the readers will only rarely download and start exploring the data themselves. Yet when presented with an adequate embedding, a reader can critically examine the structure revealed by the embedding, and this can help verify the results or prompt subsequent exploration and follow-up studies.

In summary, we consider immediacy and transparency the two main virtues of two-dimensional embeddings. At the same time, the immediacy of vision is exactly what underlies the controversies and debates about embeddings: A visual impression can be misleading, yet hard to overcome ('seeing is believing'), calling into question the scientific objectivity of the whole enterprise. Indeed, critics have derisively compared two-dimensional embeddings to art (Chari and Pachter, 2023 ) and to reading tea leaves, implying their unscientific or pseudoscientific character, and have called to forgo them entirely. Notably, two-dimensional embeddings have attracted more criticism than other EDA tools such as clustering, even though clustering also requires subjective choices (Kleinberg, 2002 ; Von Luxburg et al., 2012 ; Hennig, 2015 ) and can arguably introduce even larger distortions as it typically forces the data into a discrete (i.e., zero-dimensional) representation. This criticism is largely due to the immediacy of vision leveraged by embeddings: While immediacy is a virtue, it comes with the risk of being deceiving.

The discussion about the role of low-dimensional data representations in science has a long history, connecting to concerns regarding the use of visualizations in data analysis. Already during the early beginnings of statistical computer graphics, Anscombe ( 1973 ) opposed the idea that 'performing intricate calculations is virtuous, whereas actually looking at the data is cheating' and defended the utility of data visualizations. And, as Daston and Galison ( 2007 ) show, the push against graphic aids to science extends back to at least the late nineteenth century. In this review, we adopt the stance that, when applied and interpreted with the appropriate care (see especially Section 5 ), low-dimensional embeddings constitute a useful tool that can add genuine scientific value by making

 

*[picture on PDF page 4]*

**Figure labels:**
-   
-  
-                           
-                          

the way science approaches big datasets less error-prone and more transparent.

## 3 Overview of embedding methods

Given a collection of high-dimensional data samples x ∈ R D , dimensionality-reduction techniques construct low-dimensional representatives z ∈ R d with d ≪ D , aiming to preserve certain characteristics of the original data. The low-dimensional samples can be obtained via a function fW : R D → R d parametrized by a set of learnable parameters W , or in a non-parametric way when only the embedding positions themselves are learned. Representing high-dimensional data in a lower-dimensional space usually means sacrificing some information, due to the loss of degrees of freedom and limited expressiveness of the restricted space.

The choices of which information to discard and which characteristics to retain form the foundation of any dimensionality-reduction strategy. Today, myriad methods exist, aiming to preserve different characteristics (e.g., variance or pairwise distances), with different mapping strategies (parametric or non-parametric, linear or nonlinear), and using diverse optimization approaches. Multiple books have been written on the subject (Lee and Verleysen, 2007 ; Lespinats et al., 2022 ; Ghojogh et al., 2023 ). In this section, we give a non-exhaustive, concise overview of existing methods, their relationships, and the trade-offs they involve, focusing on techniques that are historically important or currently commonly used in practice (Table 1 ).

## 3 . 1 Linear methods

Developed in the early 20 th century as one of the very first dimensionality-reduction algorithms, principal component analysis (PCA) (Pearson, 1901 ; Hotelling, 1933 ) is defined as a linear projection from the high-dimensional data space onto orthogonal axes, yielding uncorrelated variables known as principal components (PCs). PCs are ordered by decreasing variance, with each PC capturing a certain fraction of the total original variance. Among all linear mappings to a given target dimension, the PCA projection maximally preserves data variance and minimizes the reconstruction error. The exact PCA solution can be obtained in terms of the eigendecomposition of the data covariance matrix.

PCA has countless applications (Jolliffe, 1986 ; Ringn´ er, 2008 ) both as a data-preprocessing method and as a datavisualization method. When PCA is used for data preprocessing, the data is often reduced to 10 -100 dimensions for downstream computational analysis. In contrast, when PCA is used for data visualization, the leading 2 -3 PCs are plotted directly. The orthogonal linear projection and its intuitive objective function make PCA visualizations particularly easy to interpret. The earliest visualization of a 2 D PCA embedding that we identified is a 1960 paper (Jolicoeur and Mosimann, 1960 ) analyzing turtle carapace measurements (Figure 1 ). In the 1970 s, related methods were developed specifically for visualization, such as the biplot (Gabriel, 1971 ) and correspondence analysis (Greenacre, 1984 ). The simplicity and popularity of PCA motivated the development of numerous extensions, such as sparse PCA (Zou et al., 2006 ), robust PCA (Cand` es et al., 2011 ), kernel PCA (Sch¨ olkopf et al., 1997 ), and probabilistic PCA (Tipping and Bishop, 1999 b).

Similarly defined as a linear transformation, independent component analysis (ICA) (Comon, 1994 ) generalizes PCA by looking for independent instead of uncorrelated components. While not as popular as PCA, ICA has been widely used in some fields, e.g., for blind source separation in electric brain recordings (Makeig et al., 1995 ).

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

## 3 . 3 Probabilistic methods

Another class of methods is based on postulating a generative model: Probabilistic methods represent the data using a probabilistic mapping from some unobserved latent variables to the high-dimensional space. Then, the expectation-maximization (EM) algorithm is employed to find the most likely mapping and the corresponding latent variables. This approach is motivated by the idea that a small number of latent variables drives the meaningful variability in the high-dimensional data. The simplest example is the probabilistic formulation of PCA (Tipping and Bishop, 1999 b), which showed that if the latent variables are continuous, the mapping from the latent space to the data space is linear, and the high-dimensional noise is equally strong in all dimensions, then the latent variables are given by the principal components. The probabilistic perspective on PCA allows for many generalizations, such as mixtures (Tipping and Bishop, 1999 a), hierarchies (Bishop and Tipping, 1998 ), and Bayesian formulations (Bishop, 1998 ).

When allowing the high-dimensional noise to have different magnitudes in different dimensions, the same model leads to factor analysis. This has been developed largely in parallel to PCA in the early 20 th century (Spearman, 1904 ; Thurstone, 1931 ), and it has been popular in psychometrics, usually as a tool to extract interpretable latent factors and not for visualization (Everett, 1984 ). The linear map expresses the factor loadings , while the diagonal elements represent independent noise variances for each variable. Extensions of factor analysis to timeseries data have been developed in neuroscience (Yu et al., 2008 ).

Probabilistic PCA and factor analysis are limited by their linearity and the restricted form of the latent-variable distribution. Increasing their expressive power brings computational challenges: arbitrary nonlinear functions and distributions usually lead to intractable algorithms. Generative topographic mapping (GTM) (Bishop et al., 1998 ) hence defines the latent distribution as a finite regular grid of delta functions over the low-dimensional (usually 2 D) latent space and uses non-linear mapping functions. The stretching and magnification of the latent-space representation to fit the data can be measured using differential geometry; the separation between clusters can be visualized by plotting the magnification factors in latent space (Bishop et al., 1997 b). Similarly, the curvature of the manifold can be used to quantify how well the manifold fits the data (Tino et al., 2001 a). Extensions of GTM can model discrete variables and heterogeneous data (Nabney et al., 2005 ), as well as time series by using a hidden Markov model (Bishop et al., 1997 a). More recently, the restriction to a grid of delta functions has been relaxed through the use of Gaussian process mappings (Lawrence, 2003 ), which tends to provide a smoother distribution of points in the latent space.

## 3 . 4 Spectral methods

This group of methods is based on the manifold assumption , i.e., the hypothesis that the original data points lie on a low-dimensional manifold within the high-dimensional space. Spectral methods approximate the data manifold by representing the neighbor relations between data points as a graph - e.g., in a k -nearest-neighbor ( k NN) graph, the data points (nodes) are connected (edges) to their k nearest neighbors in the high-dimensional space. The core idea behind spectral methods is to find a lowdimensional embedding of the data that preserves the structural relationships defined by this graph. Solving the resulting objectives usually involves computing the spectral decomposition (eigendecomposition) of matrices derived from the weighted adjacency matrix of the graph. Most notably, Laplacian eigenmaps (Belkin and Niyogi, 2002 ) perform an eigendecomposition of the normalized graph Laplacian, which yields a constrained embedding such that neighboring points in the graph end up close together in the embedding. Theoretical results show that Laplacian-based embeddings approximate the geometry of the underlying data manifold (Belkin and Niyogi, 2006 ; Singer, 2006 ).

Closely related to Laplacian eigenmaps are diffusion maps (Coifman and Lafon, 2006 ; Nadler et al., 2006 ). Here, the diffusion distance between any two points is defined based on the similarity of fixed-length random walks on the graph emanating from these two points. Diffusion maps approximate this distance with an embedding given by scaled eigenvectors of the normalized random-walk graph Laplacian. Specific normalizations of this matrix can yield embeddings that are invariant to the density of the sampled data points (Coifman and Lafon, 2006 ), which is important when non-uniform sampling is an artifact of the data-acquisition process, rather than a reflection of the geometry of the data (Lafon et al., 2006 ). Extensions include considering information on the local curvature of the high-dimensional point cloud (Singer and Wu, 2012 , 2017 ) or approximating the commute-time distances that consider random walks of arbitrary length between pairs of points (Taylor and Meyer, 2012 ).

Other methods compute the eigendecomposition of more specialized data-dependent matrices arising from the k NN graph. Locally linear embedding (LLE) (Roweis and Saul, 2000 ) aims to preserve local relationships by reconstructing each data point as a linear combination of its neighbors, with extensions capturing higher-order information (Donoho and Grimes, 2003 ). In contrast, maximum variance unfolding (MVU) (Weinberger and Saul, 2006 ; Song et al., 2007 ) aims to maximize variance in the low-dimensional space while maintaining the local distances defined by the nearest-neighbor graph.

Similar to PCA, eigendecompositions in spectral methods yield a whole sequence of eigenvectors, and more than two eigenvectors may often be needed to adequately represent the graph structure. As an alternative, to obtain a 2 Dor 3 Dembedding that reflects distances on the graph, MDS (Section 3 . 2 ) can be applied to pairwise graph-based distances. This was first suggested in Isomap, which amounts to classical MDS of the geodesic distances on the k NN graph (Tenenbaum et al., 2000 ). Isomap works well for revealing smooth nonlinear manifolds in low-noise settings, but it can suffer from high-dimensional noise because geodesic distances can be very sensitive to shortcut edges in the graph. A more recent approach called PHATE (Moon et al., 2019 ) uses metric MDS of potential distances, which are a variant of diffusion distances inspired by information geometry. Both are less influenced by shortcuts, making PHATE more robust than Isomap. Variants of PHATE have been proposed for multiscale embeddings (Kuchroo et al., 2022 ) and for capturing the dynamics of evolving systems (Gigante et al., 2019 ).

Most spectral approaches obtain a global embedding of the data via an eigendecomposition of a graph matrix, e.g., the graph Laplacian. In contrast, bottom-up manifold-learning approaches such as local tangent space alignment (LTSA) (Zhang and Zha, 2004 ), low distortion local eigenmaps (LDLE) (Kohli et al., 2021 ), and Riemannian alignment of tangent spaces (RATS) (Kohli et al., 2024 ), first construct separate low-dimensional embeddings of local neighborhoods in the data (using local PCA or subsets of the eigenvectors of the graph Laplacian) and then align them to obtain a single global embedding.

## 3 . 5 Neighbor-embedding methods

Neighbor-embedding methods, going back to the seminal stochastic neighbor embedding (SNE) algorithm (Hinton and Roweis, 2002 ), are also based on neighbor graphs of the data, such as k NN graphs. These methods aim to construct an embedding such that high-dimensional neighbors remain neighbors in the embedding while high-dimensional non-neighbors are placed far apart. While metric MDS aims to preserve all pairwise highdimensional distances, large and small, SNE only aims to preserve nearest neighbors, corresponding to the smallest pairwise distances.

The focus on nearest-neighbor preservation over global distance preservation offers one main advantage: MDS often fails to generate useful embeddings because highdimensional distances tend to be all similar to each other (a phenomenon known as norm concentration (Aggarwal et al., 2001 ; Francois et al., 2007 )), one manifestation of the curse of dimensionality. Hence, these high-dimensional distances cannot be meaningfully reproduced in 2 D (see

*[picture on PDF page 7]*

**Figure labels:**
-     
-  
-      
-       
-                                     
-             
-            
-                      
-           
-                  
-              

Section 4 ). Neighbor embeddings tend to work better than MDS because they focus on preserving neighbors, irrespective of what the distances between them originally were (Lee and Verleysen, 2011 ). Consequently, methods based on neighbor embeddings have gained traction in recent years, as evidenced by the growing popularity of their most prominent representatives, t -SNE and UMAP (Figure 2 ).

A modification of the original SNE, t -SNE (van der Maaten and Hinton, 2008 ) allows some of the neighbors to drift further away. As a result, it is less influenced by the shortcut k NN edges (see also Section 3 . 4 ) and can often produce a better overall embedding without points crowding together too strongly. Motivated by the practical success of the SNE framework, many modifications have been proposed, such as hierarchical (Pezzotti et al., 2016 a), multiscale (Lee et al., 2015 ; de Bodt et al., 2022 ), and heavy-tailed (Yang et al., 2009 ; Kobak et al., 2019 ) SNE variants. The growing interest in visualizing datasets with ever-increasing sample size has led to the development of accelerated t -SNE implementations that use approximate k NN graphs and physics-inspired methods for approximate optimization (Yang et al., 2013 ; van der Maaten, 2014 ; Vladymyrov and Carreira-Perpinan, 2014 ; Linderman et al., 2019 ; Pezzotti et al., 2019 ; Artemenkov and Panov, 2020 ). Modern implementations (Poliˇ car et al., 2024 ) easily scale to tens of millions of samples.

UMAP (McInnes et al., 2018 ; Healy and McInnes, 2024 ) is based on an earlier accelerated modification of t -SNE (Tang et al., 2016 ). The main difference between UMAP and t -SNE can be understood when interpreting neighbor-embedding algorithms as physical systems, where points move in the embedding space under attractive forces between neighbors and indiscriminate re- pulsive forces between all points until an equilibrium is reached (Carreira-Perpin´ an, 2010 ). UMAP employs stronger attraction forces than t -SNE (Damrich et al., 2023 ), resulting in more compact and pronounced clusters, but both methods belong to a whole attraction-repulsion spectrum of neighbor embeddings (B¨ ohm et al., 2022 ). Other differences between UMAP and t -SNE, such as the choice of edge weights, have been shown to be of little importance (Damrich and Hamprecht, 2021 ). UMAP's popularity inspired the development of multiple related methods (Amid and Warmuth, 2019 ; Wang et al., 2021 ). Recently, UMAP embeddings to 5 -10 dimensions have been used for density clustering in some application areas (Grootendorst, 2022 ; Diaz-Papkovich et al., 2023 ; Healy and McInnes, 2024 ). We believe more work is needed to better understand and validate this clustering approach (see [Section 6](06_3_evaluation.md) ).

Similar to MDS, optimizing a neighbor-embedding objective is non-convex. Hence, different initializations can result in different embeddings, corresponding to different local optima. Modern implementations benefit from informative initializations (Kobak and Linderman, 2021 ), and various optimization heuristics such as dimensionality annealing (Vladymyrov, 2019 ) have been suggested.

Neighbor-embedding methods can also be interpreted as low-dimensional layouts of k NN graphs. Other graphlayout algorithms, such as force-directed graph layouts, can be used on k NN graphs, also resulting in neighbor embeddings. One example is ForceAtlas 2 (Jacomy et al., 2014 ), which leads to even stronger attractive forces compared to UMAP (B¨ ohm et al., 2022 ). Conversely, UMAPand t -SNE can be used as graph layouts for generic graphs, such as citation networks (B¨ ohm et al., 2025 ).

## 3 . 6 Parametric methods

Except for linear and probabilistic methods, most methods described above are non-parametric, i.e., they construct an embedding without learning an explicit mapping between the high-dimensional and the lowdimensional coordinates. While flexible, one limitation of these kinds of approaches is that adding out-of-sample data into existing embeddings is not straightforward (Bengio et al., 2004 ). One family of non-linear parametric methods are auto-encoders (Hinton and Salakhutdinov, 2006 ), where geometric or topological constraints on the non-linear mapping have been used to obtain more geometrically accurate parametric embeddings of the data (Jia et al., 2015 ; Li et al., 2020 , 2021 ; Peterfreund et al., 2020 ; Moor et al., 2020 ; Duque et al., 2023 ; Nazari et al., 2023 ).

Many non-parametric methods can be converted into their parametric variants using various neural network ar-

chitectures. However, the effects of such parametrization have only recently been systematically explored (Duque et al., 2023 ; Huang et al., 2024 ). Many such approaches have been proposed for spectral embeddings Mishne et al. ( 2019 b); Shaham et al. ( 2018 ); Pai et al. ( 2019 ); Duque et al. ( 2020 ) and neighbor-embedding methods (van der Maaten, 2009 ; Bunte et al., 2012 a; Gisbrecht et al., 2015 ; Sainburg et al., 2021 ; Carreira-Perpin´ an and Vladymyrov, 2015 ; Damrich et al., 2023 ).

## 3 . 7 Supervised methods

All methods surveyed above are unsupervised : They do not use class labels that may be available in the dataset and focus on the faithful preservation of structure in the highdimensional data. In contrast, supervised dimensionality reduction looks for an embedding with high separation of predefined classes. These two goals may be conflicting if the most prominent high-dimensional structure is not driven by the class labels.

A supervised linear method called linear discriminant analysis (LDA) (Rao, 1948 ) can be seen as a supervised version of PCA, seeking to maximize the separation between means of projected classes while minimizing variance within each projected class. Two-dimensional LDA scatter plots were in use even before PCA scatter plots (Rao, 1948 ; Jolicoeur, 1959 ). Related methods include demixed PCA (Kobak et al., 2016 ) for data with multiple sets of class labels, as well as canonical correlation analysis (Hotelling, 1936 ) and reduced-rank regression (Izenman, 1975 ) for data with multiple continuous labels.

Another linear method, neighborhood component analysis (Goldberger et al., 2004 ) finds a projection that maximizes the k NN classification accuracy in the embedding. Other works use the class information to construct supervised pairwise distances and then feed them into unsupervised embedding methods (Venna et al., 2010 ; Bunte et al., 2012 b) - supervised variants of Isomap (Geng et al., 2005 ; Li and Guo, 2006 ) and PHATE (Rhodes et al., 2021 ) were developed following this principle. Similarly, class information can also be used to inform neighbor-embedding algorithms (Yu et al., 2017 ; Hajderanj et al., 2019 ; Cheng et al., 2021 ).

## 4 Example applications

Representing high-dimensional data in low-dimensional spaces requires trade-offs, and each method will preserve different aspects of the input data to a different extent (Section 3 ). Therefore, the utility of a given method will strongly depend on the data type and on the analysis goal. To illustrate this, we apply six popular embedding methods-PCA, MDS, Laplacian Eigenmaps (LE), PHATE, t -SNE, and UMAP-to create 2 D visualizations of realworld datasets from three data modalities and scientific domains: text data, single-cell transcriptomics data, and population-genetics data. We also quantitatively evaluate the different methods regarding their capacity to preserve local and global structure.

Text data Neighbor embeddings have been used in recent years to visualize and obtain explorable embeddings of large document corpora, such as library contents (Schmidt, 2018 ), collections of philosophy papers (Noichl, 2021 ), or biomedical articles (Gonz´ alez-M´ arquez et al., 2024 ). They can also be used to investigate more specialized textual formats, like mathematical formulas (Noichl, 2023 ). Here, we visualized a collection of 485900 text paragraphs taken from the Simple English Wikipedia and represented as 768 -dimensional vectors using a language model (see Methods) (Figure 3 ). Both UMAP and t -SNE embeddings exhibited numerous clusters that were semantically meaningful and corresponded to well-defined topics, such as video games or mathematics . While the UMAP embedding showed more clearly separated larger clusters, t -SNE emphasized smaller clusters corresponding to sub-topics, for example, individual countries within the world countries topic.

Manifold-learning methods such as PHATE and Laplacian eigenmaps produced embeddings that were more difficult to interpret, likely because the input data did not have prominent continuous manifold structures. Finally, PCA and especially MDS yielded fuzzy 2 D embeddings lacking useful structure. Indeed, MDS aims to preserve high-dimensional pairwise distances, which in this case tend to be all similar and hence cannot be meaningfully reproduced in 2 D. Note that PCA and Laplacian eigenmaps yield a sequence of eigenvectors, and more than two dimensions are needed to represent the data accurately. In this dataset, the first two principal components represented less than 7 % of the total variance.

Single-cell transcriptomics data In the field of singlecell biology, two-dimensional visualizations, typically based on neighbor embeddings or manifold-learning methods, have become a commonplace tool: they assist with the exploration of cell types and their development and provide a concise visual data summary in publications. Here, we use two datasets for which biology dictates very different data geometry. One dataset (Tasic et al., 2018 ) contains 23800 cells from the adult mouse brain and has a large number of hierarchically organized cell types (Figure 4 ). The other dataset (Kanton et al., 2019 ) contains 20300 cells from primate brain organoids collected during organoid development and has prominent one-dimensional organization correspond-

UMAP

Cities and Towns in France

United States

Cities, Towns and Counties

Ice Hockey

Biographies of

*[picture on PDF page 9]*

**Figure labels:**
- Sports Players
- Sports and
- Recreation
- Biographies of
- Athletes and
- Sportspeople
- •WWE Wrestlers
- Regions of
- France.
- Census Details,
- Global Geography
- Zoology
- Amphibians
- Music
- Movies
- Classical Music
- Actors and
- Actresses
- Cities and Towns
- Aircraft and
- Spacecraft
- in Germany
- Educational|
- Public Transport Institutions
- Systems
- Biographies in
- Arts, Literature
- and Journalism
- British and
- French Royal
- Families
- Television'
- Series
- Countries of the
- World
- Conflict and War
- Historic
- Buildings and
- Monuments
- Religion and
- Deities
- Scientists and
- Mathematicians
- Celebrities
- Notable
- Historical
- Events
- Politicians
- American
- National
- US Politicians
- Governments and
- Parliaments
- Social Sciences
- and Humanities
- Deaths of Famous
- People
- Languages and
- Grammar
- Food and Cooking
- Plants and
- Botany
- Software and
- Computing
- Video Games
- Biology and
- Molecular
- Chemistry
- Biology Medicine and
- Diseases
- Physics Mathematics
- Astronomy
- Lapl. Eig.
- PCA
- Atlantic
- Tropical Storms
- and Hurricanes
- PHATE
- MDS

ing to developmental time (Figure 5 ). We use standard preprocessing steps (see Methods), including dimensionality reduction from tens of thousands of original features (genes) to 50 principal components.

In the dataset from Tasic et al. ( 2018 ), PCA and MDS embeddings clearly emphasized three major classes of cells: inhibitory neurons, excitatory neurons, and nonneural cells (Figure 4 ), with MDS and PHATE indicating further variability within some of the classes. The UMAP and t -SNE embeddings suggested that cells were grouped into around a dozen well-separated cell families (with UMAP compressing them more than t -SNE), but they did not convey any information on the large-scale organization of such families into classes. To some extent, this can be remedied by multiscale t -SNE that combines local quality of t -SNE with the global layout similar to MDS (de Bodt et al., 2022 ). Notably, Laplacian eigenmaps embedding collapsed major classes almost to single points, corresponding to disconnected components in the k NN graph. While this property of Laplacian eigenmaps is useful for downstream clustering known as spectral clustering (Ng et al., 2001 ; Shi and Malik, 2000 ), it arguably counteracts meaningful visualization.

The appeal of manifold-learning methods can be seen when embedding the dataset from Kanton et al. ( 2019 ) (Figure 5 ). Here, the first component of Laplacian eigenmaps corresponded to developmental time. The same developmental trajectory was visible in the PHATE embedding (as well as in the ForceAtlas 2 layout of the k NN graph of the data, see B¨ ohm et al. ( 2022 )). In contrast, UMAP and especially t -SNE embeddings highlighted individual clusters and did not show the continuous developmental structure. These observations illustrate why diffusion-based methods, emphasizing continuous variation, are often used in developmental single-cell biology (Haghverdi et al., 2015 ; Angerer et al., 2016 ; Moon et al., 2019 ). Using the same dataset, Damrich et al. ( 2024 b) argued that adjusting the strength of attractive forces in neighbor embedding algorithms can be helpful when working with developmental data.

Soccer Players t-SNE

PCA

Excitatory neurons

MDS

t-SNE

L2/3 IT|

*[picture on PDF page 10]*

**Figure labels:**
- Inhibitory neurons
- PHATE
- UMAP
- L5 NP
- L6 NP
- L6 CT|
- Serpinf1 i
- Sncg
- L2/3 IT|
- Pvalb
- L5 PT
- Lamp5

Population-genetics data Population-genetic studies use 2 D embeddings to visualize population structure that arises from patterns of non-random mating over generations, providing insights into demographic history. We used 3450 human genotypes from the 1000 Genomes Project (The 1000 Genomes Project Consortium, 2015 ), which sampled data from 26 populations around the world (Figure 6 ). We employed standard preprocessing to filter data to 54000 single-nucleotide polymorphisms (SNPs) as features (see Methods). UMAP and t -SNE embeddings formed clusters of individuals sharing recent genetic ancestry and hence represented the 26 sampled populations. UMAP formed tighter and larger clusters (e.g., East Asian, European, African, etc.), whereas t -SNE exhibited smaller clusters, including multiple clusters consisting of just several genotypes and corresponding to single families (siblings and parents). However, individuals who share ancestry from multiple clusters (e.g., a child with parents from different continents) may appear in such embeddings within one cluster rather than between them, i.e., these methods can exaggerate the separation between clusters.

In contrast, PCA showed more continuous structure with several prominent axes (Figure 6 ). Since the largest source of genetic variation in this data is geographic distance between populations, the terminals of the PC axes represented the geographical ancestry regions: Africa, South Asia, East Asia, and Europe. Central and South American individuals, who tend to have recent ancestry from Europe and Africa in addition to their own indigenous ancestry, appeared between these clusters. However, PCA required more than two components to fully represent this structure, making the 2 D figure difficult to read correctly and suggesting that visualizing further PCs can be useful (for example, the green points overlapped with other points in 2 D, but were separated along PC 3 ). Notably, MDS embedding of this dataset produced a disc with weakly separated classes: Since the leading PCs captured only a small fraction of the total variance ( 5 . 8 % by the first two PCs in contrast to nearly 50 % in our single-cell transcriptomics examples), the high-dimensional pairwise distances were dominated by other sources of variation.

Quantitative evaluation To quantitatively compare the showcased embedding methods, we computed several measures that capture how well an embedding preserves global and local structure (Table 2 ). Across the four datasets, t -SNE embeddings had the highest local quality, while PCA and MDS embeddings had the highest global quality (Figure 7 ), in line with existing single-cell benchmarks (Huang et al., 2022 ; Lause et al., 2024 ; Sun et al.,

Lapl. Eig.

PCA

MDS

Lapl. Eig.

10 days

15 days:

1 month

*[picture on PDF page 11]*

**Figure labels:**
- 2 months
- 4 months
- 0 days
- / 4 days
- PHATE
- 10 days
- 15 days
- 1 month
- 4 months.
- 4 days
- UMAP

2019 ; Wang et al., 2023 a; Xiang et al., 2021 ). For the data from Kanton et al. ( 2019 ) with its underlying continuous structure, PHATE and Laplacian Eigenmaps also showed higher global quality than t -SNE and UMAP. Importantly, these metrics do not quantify all relevant aspects of an embedding (see [Section 6](06_3_evaluation.md) ).

Overall, across the four datasets, we demonstrated that different embedding methods represent different aspects of the high-dimensional data. Practitioners need to be aware of the trade-offs involved and emphasize them in their scientific communication, in particular when creating visualizations - such as those of human genotype data -that can potentially fuel societally contentious debates. In the next section, we provide some guidance toward this end.

## 5 Guidance and best practices

Low-dimensional embeddings are tools to examine and represent data - analogous to how microscopes are used to inspect cells and maps are designed to chart territories. Working with each tool requires taking multiple careful decisions, such as how to calibrate a microscope or what projection to use for a map. The choices made to create low-dimensional embeddings should be equally deliberate.

In this section, we have compiled some of the best practices for working with low-dimensional embeddings based on our experience. We group our guidance into four categories: preparation, exploration, presentation, and communication. Our exposition complements the work by Nguyen and Holmes ( 2019 ), which mainly focuses on best practices in the context of linear dimensionality-reduction techniques. We provide recommendations regarding a broader range of dimensionalityreduction methods, with an emphasis on visualization.

Preparation Here, we discuss how to prepare the data and choose the appropriate embedding method.

- 1 . Choose the embedding approach. Are you interested in a 2 D or 3 D embedding for visualization purposes or in higher-dimensional embeddings for downstream analysis (e.g., classification, clustering, or topological analysis)? Is interpretability of individual dimensions important? What aspects of the data are of primary interest: fine-grained clusters? large-scale clusters? continuous manifolds? These questions should guide the choice of method, as discussed in Sections 3 and 4 .
- 2 . Preprocess the data and select features. Different types of data may require different preprocessing

t-SNE

PCA

MDS

African

Lapl. Eig.

t-SNE

*[picture on PDF page 12]*

**Figure labels:**
- South Asian
- Central/South American
- European
- PHATE
- UMAP
- CHS
- CDX CHB - JPT
- PULA GIH
- BEB
- LWK
- ACB
- ASW & ESN.
- YRI • MSL
- GWD
- CEU GBR
- IBS A TSI
- PURI
- MXL LOLM
- PEL

strategies: sample selection based on quality control, feature selection based on variability, normalization of samples, standardization of features, logtransformation of values, etc. All of this may substantially alter the data distribution and, hence, the embedding results. Note that changing the measurement units of individual features (e.g., from meters to millimeters) can strongly affect the data geometry as well. The optimal preprocessing workflow is often field-specific and benefits from familiarity with the data-generation process. In some cases, features can be constructed using pretrained models - for example, texts, images, or audio samples can be converted into high-dimensional vectors (often also called embeddings) using a pretrained language model or a convolutional neural network. However, one should be aware that this strategy also introduces any biases from these models into the preprocessed data.

- 3 . Pick an appropriate distance or similarity measure. Most embedding methods rely on a distance or similarity measure between data points. The default distance is typically Euclidean, but other distances, e.g., cosine, Mahalanobis, or Wasserstein, can be used instead, based on the data type or expected local ge-

ometry (Talmon and Coifman, 2013 ; Mishne et al., 2016 ; O'Toole and Horv´ at, 2023 ; Benisty et al., 2024 ). Domain knowledge can also determine more effective domain-specific similarity measures that will impact the quality of an embedding (Lozupone and Knight, 2005 ; Talmon et al., 2012 ).

- 4 . Determine the number of PCs to keep. For many types of data, standard preprocessing pipelines include a denoising step with PCA, preserving only a subset of PCs as input to a secondary embedding algorithm. This step can affect the results, especially if a large fraction of variance is discarded in the PCA step. See Jolliffe ( 1986 , Sec 6 . 1 ) for strategies to choose the number of PCs.

Exploration Here, we summarize what to keep in mind when exploring an embedding of a given dataset.

- 5 . Look at multiple embedding methods. Visualizing data with multiple embedding methods is analogous to using multiple types of microscopes on a biological sample. In Section 4 , we showed how PCA, MDS, UMAP, t -SNE, LE, and PHATE can highlight different aspects of the data. However, to be able to interpret the differences meaningfully, it is important

- to be aware of the differences between the algorithms and the trade-offs involved (Sections 3 and 4 ).
- 6 . Consider hyperparameters. Many methods have conceptual hyperparameters that can be adjusted meaningfully, similar to adjusting the focus of a microscope, with different values bringing different aspects of the data into view (Diaz-Papkovich et al., 2021 ). For the methods based on a k NN graph, one such parameter is the number of neighbors ( k ) or its equivalents, such as perplexity in t -SNE (Skrodzki et al., 2023 ). Similarly, moving along the attractionrepulsion spectrum in neighbor-embedding methods can be useful for data exploration (Damrich et al., 2024 b). Beyond conceptual hyperparameters, many methods also have technical hyperparameters (for example, those related to optimization). For most use cases, we recommend leaving these at their default values.
- 7 . Investigate unusual shapes or patterns. Odd and unusual shapes in 2 D or 3 D embeddings can highlight issues with the data or the preprocessing pipeline, calling for additional quality control and filtering steps (for some examples, see Lause et al. ( 2021 ); Gonz´ alez-M´ arquez et al. ( 2024 ); Nazari et al. ( 2023 )). For example, unusually elongated shapes can be the result of erroneously including sample numbers as a spurious feature.
- 8 . Use features and metadata to color the points. The samples in the embedding can be colored by individual features to reveal which of them are influencing which aspects of the embedding. This can help interpret the embedding in terms of the original features. In addition, individual samples often have associated metadata that are not part of the features used for dimensionality reduction (e.g., sample collection site, sample collection date, various measures of sample quality, etc.). Coloring an embedding by metadata variables can identify problematic batch effects or highlight unexpected findings (for examples of the latter, see Gonz´ alez-M´ arquez et al. 2024 ).
- 9 . Be aware of method limitations. When using an embedding method, it is important to be aware of its limitations and possible distance distortions (see [Section 6](06_3_evaluation.md) . 3 for details). For example, points overlapping in a 2 D or 3 D PCA projection or Laplacian eigenmaps may be highly distinct and separated along subsequent components (Figures 4 and 6 ), and it is common in data exploration to plot pairwise combinations of subsequent components. Spectral embeddings and MDS can exhibit shapes such as horseshoes that are not scientifically meaningful (Diaconis
- et al., 2008 ; Morton et al., 2017 ). Notably, in neighbor embeddings, between-cluster distances are not indicative of the high-dimensional between-cluster distances.
- 10 . Do not perform downstream analysis on 2 D embeddings. 2 D embeddings are not suited for downstream computational analysis, as they can introduce distortions and artifacts that will be picked up downstream. It is usually more appropriate to perform regression, classification, or clustering on higherdimensional data, and only use 2 D embeddings for exploration and communication. See [Section 6](06_3_evaluation.md) about using embeddings of higher dimensionality (e.g., 5 D or 10 D) for downstream analysis.
- 11 . Always independently test your hypotheses. As we emphasize throughout the paper, 2 D and 3 D embeddings are an exploratory tool that can reveal unexpected patterns, suggest hypotheses, and guide researchers toward a confirmatory analysis. However, it is important to further verify such observations. A 2 D or 3 D embedding should not be used to support definitive scientific statements about the data. Rather, it can serve as a starting point for further analysis.

*[picture on PDF page 13]*

**Figure labels:**
-    
-                                      
-                                       
-           
-      
-     
-          
-             
-              

Visualization Here, we note some useful hints and possible pitfalls when preparing figures with 2 D embeddings.

- 12 . Choose an appropriate color map. Patterns in data can jump out much more clearly given a suitable color contrast, and inadequate coloring can distort the perception of patterns in the data. Embeddings are frequently colored by discrete class labels (Figures 3 to 6 ), which can become challenging if there are many classes. Specialized packages exist for generating extended discrete color palettes (McInnes, 2024 ; Neuwirth, 2022 ) as well as color-blind-friendly palettes (Steenwyk and Rokas, 2021 ; Rocchini et al., 2024 ). Continuous metadata or features should be encoded using continuous color maps (for some examples, see Huisman et al. ( 2017 ); Diaz-Papkovich et al. ( 2019 )). It is important to ensure that these color maps are perceptually uniform -i.e., that equal steps in the colormap reflect equal steps in the data (Liu and Heer, 2018 ). When continuous feature values have a clear midpoint (e.g., 0 ) and the deviations from this midpoint are of interest, diverging color maps should be used.
- 13 . Avoid overplotting. Scatter plots with too many points can become crowded and difficult to parse. Reducing the size and increasing the transparency of points can highlight patterns that are otherwise obscured. When classes have different sizes, smaller groups may get hidden underneath larger ones in the visualization, which can be mitigated by plotting larger groups first. Sometimes, groups in the data can also be hidden in a scatter plot due to an unfortunate row order in the data matrix. Consider randomizing the plotting order of points.
- 14 . Remove axis ticks and labels. While for some methods, e.g., MDS or diffusion maps, Euclidean distances in the embedding space are meaningful, for methods that do not preserve distances, such as neighbor embeddings, embedding distances are not interpretable. Tick marks suggest that distances between points or clusters can be measured, so it is better to remove them. Labeling the axes as 'PC 1 ( 13 %)' and 'PC 2 ( 10 %)' (showing the PC number and the fraction of explained variance) makes sense for PCA embeddings. However, this is not the case for MDS or neighbor embeddings: These methods are invariant to rotation, such that no separate meaning can be attached to the individual axes. Hence, one may want to drop axis labels such as 't-SNE 1 ' and 't-SNE 2 ' entirely. Square axis frames can also be replaced with circular frames (Nonato and Aupetit, 2018 ).
- 15 . Fix the aspect ratio. Squeezing or stretching the embedding in one direction distorts the distances between points and should be avoided. In most
- cases, embeddings should be plotted in 1 : 1 aspect ratio, which is usually not the default plot setting and needs to be manually set when producing a figure (in Python, via plt.axis("equal")) . This is true not only for neighbor embeddings but also for PCA, where each component naturally has different variance (see Figure 1 ). An alternative approach often used in PCA and factor analysis (and especially in biplot visualizations, see Gabriel 1971 ) is to display standardized components, with each component scaled to have unit variance.
- 16 . Be intentional and upfront with aesthetic choices. Figure design and aesthetic choices can guide readers toward correct interpretations. For example, if a published embedding should serve as a map, serif fonts or map-like color palettes can invoke viewing habits familiar from geographical maps (with all associated conventions around distortions etc.), rather than those of classical statistical graphics (for an example, see La Manno et al. 2021 ).

Communication Here, we highlight some key considerations for presenting embeddings in scientific papers.

- 17 . Emphasize method limitations. Be clear in communicating what interpretations and conclusions can be drawn from the embedding. For example, when showing a neighbor-embedding plot with clearly separated clusters, emphasize that between-cluster distances and placement of the clusters with respect to each other may not be meaningful. If an embedding plays a big role in your narrative, report evaluation measures such as the variance explained or the fraction of preserved nearest neighbors (Section 6 . 3 ).
- 18 . Report details to ensure reproducibility. When reporting your methods, state the versions and parameters of the software required to reproduce your results. For example: 'We used the Python implementation of UMAP umap-learn version 0 . 5 . 0 with default minimum distance and n neighbors set to 50 '. Making your code available in a public repository and listing the dependencies and their versions following community standards is recommended to facilitate reproducibility.
- 19 . Be transparent about data exploration. If subsequent analyses were carried out as a result of embedding-guided data exploration, state this in the Methods section. If a range of methods or parameter choices was used in the exploration process, mention this in the text as well: 'We varied the values of hyperparameter X from 10 to 50 , obtaining qualitatively similar results.'

20 . Use supplementary embeddings. Different methods or hyperparameters can highlight different aspects of data structure (see Items 5 and 6 above). Providing additional embeddings as supplementary materials can improve readers' understanding of the data without overburdening the main text.

## 6 Challenges

In this section, we discuss important open questions and challenges for the field of low-dimensional embeddings. We group these challenges into three categories: related to algorithm development, related to human interpretation and interaction, and related to the evaluation of dimensionality-reduction outputs.

## 6 . 1 Algorithm development

Scalability Many recent algorithmic developments have been motivated by the ever-growing size of available datasets, and we expect this trend to continue in the future. More work is needed on efficient GPU implementations (Chan et al., 2018 ; Pezzotti et al., 2019 ; Nolet et al., 2021 ) and parallelization across multiple GPUs. Another promising direction is compressing the data by reducing numerical precision or converting the data to binarized form (Zhang and Saab, 2021 ; Bouland et al., 2023 ). This will likely lead to a trade-off between embedding quality and the runtime, with optimal choices depending on the application.

Another scaling possibility lies in downsampling methods that construct an embedding based on landmark points (Loukas, 2019 ; Pezzotti et al., 2016 a; Silva and Tenenbaum, 2003 ; Long and Ferguson, 2019 ; Moon et al., 2019 ; Shen and Wu, 2022 ). Coarse-graining methods that maintain the topological and geometric structure of the data and avoid introducing artifacts (Huguet et al., 2023 ; Loukas, 2019 ) deserve more research attention. Furthermore, additional efforts could be devoted to developing interactive hierarchical embeddings (Pezzotti et al., 2016 a; Marc´ ılio-Jr et al., 2024 ) that load and/or construct a more detailed embedding on zoom-in. A related approach is to construct an initial embedding using a subset of the data, and then progressively refine the embedding as additional samples are coming in, e.g., in an environment with streaming data (Pezzotti et al., 2016 b).

Optimization While spectral methods rely on eigendecomposition and produce a solution corresponding to a global minimum of their loss function, many popular embedding algorithms (including the neighbor-embedding methods t -SNE and UMAP) rely on the iterative optimiza- tion of non-convex loss functions (Section 3 ), and hence, can suffer from local minima. Optimization heuristics such as informative initialization (Kobak and Linderman, 2021 ) are employed to alleviate this problem. Further research is needed to develop methods that combine convex optimization of spectral techniques with neighbor embeddings.

Multiscale methods that preserve both local and global structures could help here as well, as reproducing global patterns constrains the overall shape of the embedding and leaves less freedom for local structures to move around (Lee et al., 2024 ). Another promising optimization approach is dimensionality annealing or, alternatively, enabling embedding points to move along temporarily added dimensions (Vladymyrov, 2019 ).

Non-standard metrics and metric learning Most methods reviewed here rely on a particular distance metric, such as Euclidean or cosine. Such metrics may not be optimal for heterogeneous data combining numerical and categorical features, in the presence of missing data (de Bodt et al., 2019 ; Gilbert and Sonthalia, 2018 ; Mishne et al., 2019 a), or for data with rich internal symmetries, such as text or image datasets. Developing embedding methods that can learn adequate distance metrics in such cases, revealing otherwise hidden data structures, remains an important challenge (Lin et al., 2023 ). Such metric learning can be guided by supervised signals (Rhodes et al., 2021 , 2023 ) or by self-supervised learning approaches. Recently, self-supervised learning based on data augmentation has been used to optimize a neural network implementing 2 D embedding of image data (B¨ ohm et al., 2023 ).

Optimal dimensionality In this review, we focused on low-dimensional embeddings for data exploration, which typically demands very few dimensions. Another goal of low-dimensional embeddings may be downstream analysis, such as clustering, which may be challenging to do in the original high-dimensional space. For example, spectral clustering (Ng et al., 2001 ; Shi and Malik, 2000 ) applies k -means clustering to Laplacian eigenmaps. In this case, the appropriate embedding dimensionality is typically larger than two. Some recent work obtained promising clustering results working with neighbor embeddings of dimensionality 5 -10 (Grootendorst, 2022 ; Diaz-Papkovich et al., 2023 ). More work is needed to benchmark and to study the theoretical properties of such approaches. A related challenge is to identify an optimal embedding dimensionality, perhaps related to the intrinsic dimensionality of the data (Levina and Bickel, 2004 ; Camastra and Staiano, 2016 ).

## 6 . 2 Interpretability and interactivity

User studies As low-dimensional embeddings are tools for visual data analysis, it is important to understand how people use such embeddings in practice. Nevertheless, user studies have been relatively rare. The few existing studies showed, inter alia, that the most effective embedding technique depends on the task (Xia et al., 2021 ), that people tend to disregard the methods' mathematical objectives and use them as black boxes (Morariu et al., 2023 ), and that experts and novices evaluate embeddings differently (Lewis et al., 2012 ): novices prefer to see more continuous gradual structures, whereas experts adapt their preference for gradual vs. clustered structures depending on the dataset. Also, people prefer to use embeddings that 'catch the eye', which, in turn, is influenced by class separability (Doh et al., 2025 ). However, larger and more focused user studies are needed, with participants facing specific data-exploration goals.

Interpretability Due to the nonparametric nature of many embedding algorithms, low-dimensional positions may be difficult to interpret and to relate to the original variables (Bibal and Fr´ enay, 2019 ). Questions like 'Which original features cause these two clusters to be separated?' or 'Why is this outlier so far away?' are common, and answering them requires follow-up analysis. Explainability tools can make these questions easier to tackle. Even for parametric but highly nonlinear methods, such as autoencoders, interpretation can be challenging.

Several studies proposed post-hoc explainability approaches, fitting intrinsically interpretable models like linear regressions or decision trees to relate embedding coordinates to the original features in local regions of the embedding space (Bibal et al., 2020 ; Lambert et al., 2022 b; Ovcharenko et al., 2024 ). Nonlinear compositions of functions from a user-defined dictionary were also used for this purpose (Koelle et al., 2022 , 2024 ). Other works enriched the visualizations with additional graphical elements, annotating regions of the embedding space (Kandogan, 2012 ; Pagliosa et al., 2016 ; Tian et al., 2021 ; Novak et al., 2023 ; Poliˇ car and Zupan, 2024 ). Moreover, several works developed intrinsically interpretable approximations of existing embedding methods (Bibal et al., 2021 b; Couplet et al., 2023 ). Compared to post-hoc explainability techniques, such approaches can enable interpreting the embedding directly, rather than through local approximations. More work is needed in this direction, in particular to integrate interpretability measures into the design of dimensionality-reduction algorithms.

Post-hoc validation Dedicated techniques are needed to enable users to confirm the existence of patterns they see in the low-dimensional embedding in the highdimensional space. This would allow users to identify real patterns and not over-interpret spurious ones appearing in the visualization due to method limitations. For instance, computational-topology tools such as persistent homology can validate the presence of loops (Edelsbrunner et al., 2002 ; Damrich et al., 2024 a; Kohli et al., 2024 ). The clusters visible in an embedding should become similarly verifiable, potentially by other means. While modern neighbor embeddings excel at representing clusters in the data, the clustering illusion is a recognized cognitive bias (Gilovich, 1991 ), and sometimes an embedding can be misleading in suggesting the presence of clusters.

Interactive tools Data exploration and communication can be enhanced through software that allows dynamic interaction with embeddings (Sacha et al., 2016 , 2017 ). This includes capabilities such as zooming, displaying metadata on mouse-over events, providing summaries for selected points, dynamic switching between multiple embeddings of the same data or showing paired embeddings side-by-side (Huisman et al., 2017 ), interactive visualizations of feature gradients (Li et al., 2023 ), animations illustrating how embeddings change over time or in response to hyperparameter adjustments (Damrich et al., 2024 b), and many more. Motion can be particularly effective at communicating subtle changes, serving as an important perceptual channel (Ware and Bobrow, 2006 ; Heer and Robertson, 2007 ; Munzner, 2014 ), and interactivity can identify patterns that may be obscured in static images (Pezzotti et al., 2016 b). Interactive tools have also been used to identify distortions in the embedding (Lespinats and Aupetit, 2011 ; Heulot et al., 2013 ) as well as to explain structures in the embedding space in relation to the original high-dimensional features (Stahnke et al., 2016 ; Bibal et al., 2021 a; Eckelt et al., 2022 ).

There are ongoing efforts to develop hierarchical data representations, where users can select a subset of points with a lasso-like tool and then generate a new embedding using only the selected points to study finer-scale substructure (Tino et al., 2001 b; Pezzotti et al., 2016 a; Van Unen et al., 2017 ; Marc´ ılio-Jr et al., 2024 ; H¨ ollt et al., 2019 ). This has led to the development of software such as ManiVault (Vieth et al., 2023 ), which allows rapid prototyping of dedicated data viewers, Cytosplore (Hodge et al., 2019 ), a viewer developed for single-cell and spatial data, or DeepScatter (Nomic AI, 2025 ), an in-browser interactive viewer supporting data loading on demand.

## 6 . 3 Evaluation

Quality measures Dimensionality-reduction methods produce outputs that can be difficult to assess quantita-

tively (Machado et al., 2025 ), and multiple complementary measures have been suggested to evaluate the quality of a given embedding (Section 4 , Figure 7 ).

The preservation of pairwise distances can be assessed through stress-based measures (Borg and Groenen, 1997 ), Shepard diagrams (de Leeuw and Mair, 2015 ), and normalized measures such as σ -distortion (Chennuru Vankadara and von Luxburg, 2018 ). Local distance preservation can also form the basis of global distortion measures (Jang et al., 2021 ). To measure the preservation of neighborhoods across various scales, from local to global, ranked distances are often used (France and Carroll, 2007 ; Lee and Verleysen, 2009 ; Venna et al., 2010 ; de Bodt et al., 2022 ; Griparis et al., 2016 ; Novak et al., 2023 ). If ground-truth class labels are available, then additional measures can be based on classification accuracy, on class separation (e.g., silhouette score, Rousseeuw ( 1987 )), or on the extent that clustering in the embedding reflects the original classes (Mokbel et al., 2010 , 2011 ; Espadoto et al., 2019 ; Huang et al., 2022 ; Wang et al., 2023 a; Lause et al., 2024 ). If the high-dimensional data contains nontrivial topological structures, persistent homology can be used to evaluate their preservation in the embedding (Rieck and Leitte, 2015 ; Paul and Chalup, 2017 ).

These criteria are useful to compare the performance of several dimensionality-reduction methods, but their absolute values can be difficult to interpret directly. As the theoretically best performance achievable on a given dataset is typically unknown, the question of whether an embedding is good enough often remains unanswered. Therefore, developing model-independent and robust measures that produce interpretable absolute values remains an important research direction.

Fine-grained visualization of embedding quality Embedding quality can vary across the embedding space, and local quality measures can provide additional information compared to a single global measure computed over the entire embedding. It is important to develop software that enables fine-grained evaluations and integrates them into visualizations, e.g., by coloring points according to the local embedding quality (Pezzotti et al., 2016 b; Thijssen et al., 2024 ; Tian et al., 2023 ; Benato et al., 2023 ), or by overlaying the embedding with additional graphical elements (Aupetit, 2007 ; Seifert et al., 2010 ; Schreck et al., 2010 ; Heulot et al., 2013 ; Martins et al., 2014 ).

Theoretical guarantees For many embedding methods, it is difficult to establish rigorous theoretical guarantees, and despite some progress in this direction (Tenenbaum et al., 2000 ; Zhang and Zha, 2004 ; Linderman and Steinerberger, 2022 ; Cai and Ma, 2022 ; Arora et al., 2018 ), further work is needed. Such guarantees can, for exam- ple, include bounds on the distortion incurred in the low-dimensional embeddings, or thresholds on the noise levels and inter-cluster linkage probabilities that allow recovery of the true clusters from their noisy observations. Even simple methods with a long history, such as classical MDS, can have surprising mathematical properties (Lim and M´ emoli, 2024 ; Kroshnin et al., 2022 ). Closer theoretical connections between different visualization methods (Noack, 2009 ; Damrich et al., 2023 ; Huguet et al., 2024 ) will clarify the relative strengths of each method. Further advancements in theoretical understanding could also provide a more rigorous framework for evaluating the performance of dimensionality-reduction methods.

## 7 Conclusion and vision

Today, researchers live in a world where their capacity to access or produce data often exceeds their ability to understand it. Since much of this data is high-dimensional, machine-learning methods that produce low-dimensional embeddings have gained importance in exploratory data analysis. In this paper, we argued that low-dimensional embeddings and visualizations can guide analyses and discussions, highlight interesting patterns, and yield new hypotheses, investigations, or questions. By creating compelling figures and adding transparency to the scientific process, embeddings also play an important role in research communication. Paraphrasing George Box (Box, 1979 ): All embeddings are wrong, but some are useful.

As data availability continues to improve, we anticipate an increased interest in low-dimensional embedding methods across various data-intensive disciplines. This includes not only machine learning and biotechnology, but also interdisciplinary fields like digital humanities and computational social science. The continued cross-pollination between methods and applications across such widely different domains promises exciting methodological developments for the field. Research on low-dimensional embeddings has already made tremendous progress (compare Figure 1 with Figure 3 ), and we expect further advances in the oncoming years.

However, as we emphasized throughout the paper, embedding methods often involve technical complexities that may not be immediately apparent to their users. Making these methods accessible to interdisciplinary researchers requires promoting awareness of best practices and methodological limitations. It also requires addressing the many remaining algorithmic and interpretational challenges identified above. Overall, embedding methods hold strong potential to shape the future of data-driven research.

### Acknowledgments

This work was conceived at the Dagstuhl seminar 24122 supported by the Leibniz Center for Informatics. CdB conducted part of this work while being a beneficiary of an FSR Incoming Post-doctoral Fellowship from UCLouvain. ADP is supported by National Institutes of Health (NIH) Grant R 35 GM 139628 . MB is funded by the Deutsche Forschungsgemeinschaft (DFG, German Research Foundation) under Germany's Excellence Strategy EXC 2181 / 1 -390900948 (the Heidelberg STRUCTURES Excellence Cluster). KB is supported by the Netherlands Organisation for Scientific Research (NWO) under Vidi grant number VI.Vidi. 193 . 098 . CC conducted part of this work while supported by Digital Futures at KTH Royal Institute of Technology. SD is supported by the German Ministry of Science and Education (BMBF) via the T¨ ubingen AI Center ( 01 IS 18039 ) and by the National Institutes of Health (UM 1 MH 130981 ). SD and DK are supported by the Gemeinn¨ utzige Hertie-Stiftung. E ´ AH is supported by the National Science Foundation (NSF CAREER Grant IIS1943506 ). JAL is a research director with the Belgian F.R.S.-FNRS (Fonds National de la Recherche Scientifique). BR acknowledges that this work has received funding from the Swiss State Secretariat for Education, Research and Innovation (SERI). GW is supported by a Humboldt Research Fellowship, CIFAR AI Chair, and NSERC Discovery grant 03267 . GMis partially supported by the National Science Foundation grants CCF2217058 and EFRI BRAID 2223822 . DK is a member of the Germany's Excellence cluster 2064 'Machine Learning New Perspectives for Science' (EXC 390727645 ). The content provided here is solely the responsibility of the authors and does not necessarily represent the official views of the funding agencies.

### References

Charu C Aggarwal, Alexander Hinneburg, and Daniel A Keim. On the surprising behavior of distance metrics in high dimensional space. In International Conference on Database Theory , pages 420 -434 , 2001 .

- Ehsan Amid and Manfred K Warmuth. TriMap: Largescale dimensionality reduction using triplets. arXiv , 2019 .
- Philipp Angerer, Laleh Haghverdi, Maren B¨ uttner, Fabian J Theis, Carsten Marr, and Florian Buettner. destiny: diffusion maps for large-scale single-cell data in r. Bioinformatics , 32 ( 8 ): 1241 -1243 , 2016 .

Francis J Anscombe. Graphs in statistical analysis. The American Statistician , 27 ( 1 ): 17 -21 , 1973 .

George Armstrong, Gibraan Rahman, Cameron Martino, Daniel McDonald, Antonio Gonzalez, Gal Mishne, and Rob Knight. Applications and comparison of dimensionality reduction methods for microbiome data. Frontiers in Bioinformatics , 2 , 2022 .

Sanjeev Arora, Wei Hu, and Pravesh K Kothari. An analysis of the t-SNE algorithm for data visualization. In Conference on Learning Theory , pages 1455 -1462 , 2018 .

Aleksandr Artemenkov and Maxim Panov. NCVis: noise contrastive approach for scalable visualization. In The Web Conference , pages 2941 -2947 , 2020 .

Micha¨ el Aupetit. Visualizing distortions and recovering topology in continuous projection techniques. Neurocomputing , 70 ( 7 ): 1304 -1330 , 2007 .

- Etienne Becht, Leland McInnes, John Healy, CharlesAntoine Dutertre, Immanuel WH Kwok, Lai Guan Ng, Florent Ginhoux, and Evan W Newell. Dimensionality reduction for visualizing single-cell data using UMAP. Nature Biotechnology , 37 ( 1 ): 38 -44 , 2019 .
- Mikhail Belkin and Partha Niyogi. Laplacian eigenmaps and spectral techniques for embedding and clustering. In Advances in Neural Information Processing Systems , pages 585 -591 , 2002 .
- Mikhail Belkin and Partha Niyogi. Convergence of Laplacian eigenmaps. In Advances in Neural Information Processing Systems , volume 19 , 2006 .
- B´ arbara C Benato, Alexandre X Falc˜ ao, and Alexandru C Telea. Measuring the quality of projections of highdimensional labeled data. Computers & Graphics , 116 : 287 -297 , 2023 .
- Yoshua Bengio, Olivier Delalleau, Nicolas Le Roux, JeanFranc ¸ois Paiement, Pascal Vincent, and Marie Ouimet. Learning eigenfunctions links spectral embedding and kernel PCA. Neural Computation , 16 ( 10 ): 2197 -2219 , 2004 .
- Hadas Benisty, Daniel Barson, Andrew H Moberly, Sweyta Lohani, Lan Tang, Ronald R Coifman, Michael C Crair, Gal Mishne, Jessica A Cardin, and Michael J Higley. Rapid fluctuations in functional connectivity of cortical networks encode spontaneous behavior. Nature Neuroscience , 27 ( 1 ): 148 -158 , 2024 .
- Adrien Bibal and Benoit Fr´ enay. Measuring quality and interpretability of dimensionality reduction visualizations. In SafeML ICLR Workshop , 2019 .

Adrien Bibal, Viet Minh Vu, G´ eraldin Nanfack, and Benoit Fr´ enay. Explaining t-SNE embeddings locally by adapting LIME. In ESANN , pages 393 -398 , 2020 .

- Adrien Bibal, Antoine Clarinval, Bruno Dumas, and Benoit Fr´ enay. IXVC: An interactive pipeline for explaining visual clusters in dimensionality reduction visualizations with decision trees. Array , 11 : 100080 , 2021 a.
- Adrien Bibal, Rebecca Marion, Rainer von Sachs, and Benoit Fr´ enay. BIOT: Explaining multidimensional nonlinear MDS embeddings using the Best Interpretable Orthogonal Transformation. Neurocomputing , 453 : 109 -118 , 2021 b.
- Christopher Bishop. Bayesian PCA. In Advances in Neural Information Processing Systems , volume 11 , 1998 .
- Christopher Bishop, Geoffrey E. Hinton, and Iain G. D. Strachan. GTM through time. In International Conference on Artificial Neural Networks , pages 111 -116 , 1997 a.
- Christopher M Bishop and Michael E Tipping. A hierarchical latent variable model for data visualization. IEEE Transactions on Pattern Analysis and Machine Intelligence , 20 ( 3 ): 281 -293 , 1998 .
- Christopher M Bishop, Markus Svens´ en, and Christopher KI Williams. Magnification factors for the GTM algorithm. In International Conference on Artificial Neural Networks , pages 64 -69 , 1997 b.
- Christopher M Bishop, Markus Svens´ en, and Christopher KI Williams. GTM: The generative topographic mapping. Neural Computation , 10 ( 1 ): 215 -234 , 1998 .
- Jan Niklas B¨ ohm, Philipp Berens, and Dmitry Kobak. Attraction-repulsion spectrum in neighbor embeddings. Journal of Machine Learning Research , 23 ( 95 ): 1 -32 , 2022 .
- Jan Niklas B¨ ohm, Philipp Berens, and Dmitry Kobak. Unsupervised visualization of image datasets using contrastive learning. In International Conference on Learning Representations , pages 1 -21 , 2023 .
- Jan Niklas B¨ ohm, Marius Keute, Alica Guzm´ an, Sebastian Damrich, Andrew Draganov, and Dmitry Kobak. Node Embeddings via Neighbor Embeddings. arXiv , 2025 .
- Ingwer Borg and Patrick J F Groenen. Modern multidimensional scaling: theory and applications . Springer Science & Business Media, 1997 .
- Gerard A Bouland, Ahmed Mahfouz, and Marcel JT Reinders. Consequences and opportunities arising due to sparser single-cell RNA-seq datasets. Genome Biology , 24 ( 1 ): 86 , 2023 .
- George EP Box. Robustness in the strategy of scientific model building. In Robustness in Statistics , pages 201 -236 . Elsevier, 1979 .
- Kerstin Bunte, Michael Biehl, and Barbara Hammer. A general framework for dimensionality reducing data visualization mapping. Neural Computation , 24 ( 3 ): 771 -804 , 2012 a.
- Kerstin Bunte, Petra Schneider, Barbara Hammer, FrankMichael Schleif, Thomas Villmann, and Michael Biehl. Limited rank matrix learning, discriminative dimension reduction and visualization. Neural Networks , 26 : 159 -173 , 2012 b.
- Tony Cai and Rong Ma. Theoretical foundations of t-SNE for visualizing high-dimensional clustered data. Journal of Machine Learning Research , 23 ( 301 ): 1 -54 , 2022 .
- Francesco Camastra and Antonino Staiano. Intrinsic dimension estimation: Advances and open problems. Information Sciences , 328 : 26 -41 , 2016 .
- Emmanuel J Cand` es, Xiaodong Li, Yi Ma, and John Wright. Robust principal component analysis? Journal of the ACM (JACM) , 58 ( 3 ): 1 -37 , 2011 .
- Miguel Carreira-Perpin´ an. The Elastic Embedding Algorithm for Dimensionality Reduction. In International Conference on Machine Learning , volume 10 , pages 167 -174 , 2010 .
- Miguel A Carreira-Perpin´ an and Max Vladymyrov. A fast, universal algorithm to learn parametric nonlinear embeddings. In Advances in Neural Information Processing Systems , volume 28 , 2015 .
- David M Chan, Roshan Rao, Forrest Huang, and John F Canny. t-SNE-CUDA: GPU-Accelerated t-SNE and its Applications to Modern Data. In International Symposium on Computer Architecture and High Performance Computing , pages 330 -338 , 2018 .
- Tara Chari and Lior Pachter. The specious art of single-cell genomics. PLOS Computational Biology , 19 ( 8 ):e 1011288 , 2023 .
- Yichen Cheng, Xinlei Wang, and Yusen Xia. Supervised t-distributed stochastic neighbor embedding for data visualization and classification. INFORMS Journal on Computing , 33 ( 2 ): 566 -585 , 2021 .
- Leena Chennuru Vankadara and Ulrike von Luxburg. Measures of distortion for machine learning. In Advances in Neural Information Processing Systems , volume 31 , 2018 .
- Ronald R Coifman and St´ ephane Lafon. Diffusion Maps. Applied and Computational Harmonic Analysis , 21 ( 1 ): 5 -30 , 2006 .

- Pierre Comon. Independent component analysis, A new concept? Signal Processing , 36 ( 3 ): 287 -314 , 1994 .
- Edouard Couplet, Pierre Lambert, Michel Verleysen, Dounia Mulders, John Aldo Lee, and Cyril de Bodt. Natively Interpretable t-SNE. In AIMLAI workshop colocated with ECML-PKDD , 2023 .
- Sebastian Damrich and Fred A Hamprecht. On UMAP's true loss function. In Advances in Neural Information Processing Systems , volume 34 , pages 5798 -5809 , 2021 .
- Sebastian Damrich, Jan Niklas B¨ ohm, Fred A Hamprecht, and Dmitry Kobak. From t -SNE to UMAP with contrastive learning. In International Conference on Learning Representations , pages 1 -44 , 2023 .
- Sebastian Damrich, Philipp Berens, and Dmitry Kobak. Persistent homology for high-dimensional data based on spectral methods. In Advances in Neural Information Processing Systems , volume 38 , 2024 a.
- Sebastian Damrich, Manuel V Klockow, Philipp Berens, Fred A Hamprecht, and Dmitry Kobak. Visualizing single-cell data with the neighbor embedding spectrum. bioRxiv , pages 2024 -04 , 2024 b.
- Lorraine Daston and Peter L Galison. Objectivity . Princeton University Press, 2007 .
- Cyril de Bodt, Dounia Mulders, Michel Verleysen, and John Aldo Lee. Nonlinear Dimensionality Reduction with Missing Data using Parametric Multiple Imputations. IEEE Transactions on Neural Networks and Learning Systems , 30 ( 4 ): 1166 -1179 , 2019 .
- Cyril de Bodt, Dounia Mulders, Michel Verleysen, and John Aldo Lee. Fast multiscale neighbor embedding. IEEE Transactions on Neural Networks and Learning Systems , 33 ( 4 ): 1546 -1560 , 2022 .
- Jan de Leeuw and Patrick Mair. Shepard Diagram. In Wiley StatsRef: Statistics Reference Online . John Wiley & Sons, Ltd Chichester, UK, 2015 .
- Pierre Demartines and Jeanny H´ erault. Curvilinear component analysis: a self-organizing neural network for nonlinear mapping of data sets. IEEE Transactions on Neural Networks , 8 ( 1 ): 148 -154 , 1997 .
- Persi Diaconis, Sharad Goel, and Susan Holmes. Horseshoes in Multidimensional Scaling And Local Kernel Methods. The Annals of Applied Statistics , 2 ( 3 ): 777 -807 , 2008 .
- Alex Diaz-Papkovich, Luke Anderson-Trocm´ e, Chief BenEghan, and Simon Gravel. UMAP reveals cryptic population structure and phenotype heterogeneity in large genomic cohorts. PLoS Genetics , 15 ( 11 ):e 1008432 , 2019 .
- Alex Diaz-Papkovich, Luke Anderson-Trocm´ e, and Simon Gravel. A review of UMAP in population genetics. Journal of Human Genetics , 66 ( 1 ): 85 -91 , 2021 .
- Alex Diaz-Papkovich, Shadi Zabad, Chief Ben-Eghan, Luke Anderson-Trocm´ e, Georgette Femerling, Vikram Nathan, Jenisha Patel, and Simon Gravel. Topological stratification of continuous genetic variation in large biobanks. bioRxiv , 2023 .
- Seoyoung Doh, Hyeon Jeon, Sungbok Shin, Ghulam Jilani Quadri, Nam Wook Kim, and Jinwook Seo. Understanding bias in perceiving dimensionality reduction projections. arXiv preprint arXiv: 2507 . 20805 , 2025 .
- David L Donoho and Carrie Grimes. Hessian eigenmaps: Locally linear embedding techniques for highdimensional data. Proceedings of the National Academy of Sciences , 100 ( 10 ): 5591 -5596 , 2003 .
- Andres F. Duque, Sacha Morin, Guy Wolf, and Kevin R. Moon. Geometry Regularized Autoencoders. IEEE Transactions on Pattern Analysis and Machine Intelligence , 45 ( 6 ): 7381 -7394 , 2023 .
- Andr´ es F. Duque, Sacha Morin, Guy Wolf, and Kevin Moon. Extendable and invertible manifold learning with geometry regularized autoencoders. In IEEE International Conference on Big Data (Big Data) , pages 5027 -5036 , 2020 .
- Janani Durairaj, Andrew M Waterhouse, Toomas Mets, Tetiana Brodiazhenko, Minhal Abdullah, Gabriel Studer, Gerardo Tauriello, Mehmet Akdel, Antonina Andreeva, Alex Bateman, et al. Uncovering new families and folds in the natural protein universe. Nature , 622 ( 7983 ): 646 -653 , 2023 .
- Klaus Eckelt, Andreas Hinterreiter, Patrick Adelberger, Conny Walchshofer, Vaishali Dhanoa, Christina Humer, Moritz Heckmann, Christian Steinparz, and Marc Streit. Visual Exploration of Relationships and Structure in Low-Dimensional Embeddings. IEEE Transactions on Visualization and Computer Graphics , 29 ( 7 ): 3312 -3326 , 2022 .
- Edelsbrunner, Letscher, and Zomorodian. Topological persistence and simplification. Discrete & Computational Geometry , 28 ( 4 ): 511 -533 , 2002 .
- Mateus Espadoto, Rafael M Martins, Andreas Kerren, Nina ST Hirata, and Alexandru C Telea. Toward a quantitative survey of dimension reduction techniques. IEEE Transactions on Visualization and Computer Graphics , 27 ( 3 ): 2153 -2173 , 2019 .
- BS Everett. An Introduction to Latent Variable Models . Springer Netherlands, 1984 .

- Stephen France and Douglas Carroll. Development of an agreement metric based upon the RAND index for the evaluation of dimensionality reduction techniques, with applications to mapping customer data. In International Workshop on Machine Learning and Data Mining in Pattern Recognition , pages 499 -517 , 2007 .
- Damien Francois, Vincent Wertz, and Michel Verleysen. The concentration of fractional distances. IEEE Trans. Knowl. Data Eng. , 19 ( 7 ): 873 -886 , 2007 .
- Karl Ruben Gabriel. The biplot graphic display of matrices with application to principal component analysis. Biometrika , 58 ( 3 ): 453 -467 , 1971 .
- Abraham Garc´ ıa-Aliaga, Mois´ es Marquina, Javier Coter´ on, Asier Rodr´ ıguez-Gonz´ alez, and Sergio Luengo-S´ anchez. In-game behaviour analysis of football players using machine learning techniques based on player statistics. International Journal of Sports Science & Coaching , 16 ( 1 ): 148 -157 , 2021 .
- Xin Geng, De-Chuan Zhan, and Zhi-Hua Zhou. Supervised nonlinear dimensionality reduction for visualization and classification. IEEE Transactions on Systems, Man, and Cybernetics, Part B (Cybernetics) , 35 ( 6 ): 1098 -1107 , 2005 .
- Benyamin Ghojogh, Mark Crowley, Fakhri Karray, and Ali Ghodsi. Elements of dimensionality reduction and manifold learning . Springer, 2023 .
- Scott Gigante, Adam S Charles, Smita Krishnaswamy, and Gal Mishne. Visualizing the PHATE of Neural Networks. In Advances in Neural Information Processing Systems , volume 32 , 2019 .
- Anna C Gilbert and Rishi Sonthalia. Unsupervised metric learning in presence of missing data. In 56 th Annual Allerton Conference on Communication, Control, and Computing (Allerton) , pages 313 -321 , 2018 .
- Thomas Gilovich. How we know what isn't so: The fallibility of human reason in everyday life . The Free Press, 1991 .
- Andrej Gisbrecht, Alexander Schulz, and Barbara Hammer. Parametric nonlinear dimensionality reduction using kernel t-SNE. Neurocomputing , 147 : 71 -82 , 2015 .
- Jacob Goldberger, Geoffrey E Hinton, Sam Roweis, and Russ R Salakhutdinov. Neighbourhood components analysis. In Advances in Neural Information Processing Systems , volume 17 , 2004 .
- Rita Gonz´ alez-M´ arquez, Luca Schmidt, Benjamin M Schmidt, Philipp Berens, and Dmitry Kobak. The landscape of biomedical research. Patterns , 5 ( 6 ), 2024 .
- John C Gower. Some distance properties of latent root and vector methods used in multivariate analysis. Biometrika , 53 ( 3 -4 ): 325 -338 , 1966 .
- MJ Greenacre. Theory and applications of correspondence analysis . Academic Press, 1984 .
- Andreea Griparis, Daniela Faur, and Mihai Datcu. A dimensionality reduction approach to support visual data mining: Co-ranking-based evaluation. In International Conference on Communications , pages 391 -394 , 2016 .
- Maarten Grootendorst. BERTopic: Neural topic modeling with a class-based TF-IDF procedure. arXiv , 2022 .
- Laleh Haghverdi, Florian Buettner, and Fabian J Theis. Diffusion maps for high-dimensional single-cell analysis of differentiation data. Bioinformatics , 31 ( 18 ): 2989 -2998 , 2015 .
- Laureta Hajderanj, Isakh Weheliye, and Daqing Chen. A new supervised t-SNE with dissimilarity measure for effective data visualization and classification. In International Conference on Software and Information Engineering , pages 232 -236 , 2019 .
- John Healy and Leland McInnes. Uniform manifold approximation and projection. Nature Reviews Methods Primers , 4 ( 1 ): 82 , 2024 .
- Jeffrey Heer and George Robertson. Animated Transitions in Statistical Data Graphics. IEEE Transactions on Visualization and Computer Graphics , 13 ( 6 ): 1240 -1247 , 2007 .
- Christian Hennig. What are the true clusters? Pattern Recognition Letters , 64 : 53 -62 , 2015 .
- Heulot, M. Aupetit, and J-D. Fekete. ProxiLens: Interactive Exploration of High-Dimensional Data using Projections. In EuroVis Workshop on Visual Analytics using Multidimensional Projections , 2013 .
- Geoffrey Hinton and Sam Roweis. Stochastic neighbor embedding. In Advances in Neural Information Processing Systems , volume 15 , pages 833 -840 , 2002 .
- Geoffrey E Hinton and Ruslan R Salakhutdinov. Reducing the dimensionality of data with neural networks. Science , 313 ( 5786 ): 504 -507 , 2006 .
- Rebecca D Hodge, Trygve E Bakken, Jeremy A Miller, Kimberly A Smith, Eliza R Barkan, Lucas T Graybuck, Jennie L Close, Brian Long, Nelson Johansen, Osnat Penn, et al. Conserved cell types with divergent features in human versus mouse cortex. Nature , 573 ( 7772 ): 61 -68 , 2019 .

- Thomas H¨ ollt, Anna Vilanova, Nicola Pezzotti, Boudewijn PF Lelieveldt, and Helwig Hauser. Focus+ context exploration of hierarchical embeddings. 38 ( 3 ): 569 -579 , 2019 .
- Harold Hotelling. Analysis of a complex of statistical variables into principal components. Journal of Educational Psychology , 24 ( 6 ): 417 -441 , 1933 .
- Harold Hotelling. Relations Between Two Sets of Variates. Biometrika , 28 ( 3 / 4 ): 321 -377 , 1936 .
- Haiyang Huang, Yingfan Wang, Cynthia Rudin, and Edward P Browne. Towards a comprehensive evaluation of dimension reduction methods for transcriptomic data visualization. Communications Biology , 5 ( 1 ), 2022 .
- Haiyang Huang, Yingfan Wang, and Cynthia Rudin. Navigating the Effect of Parametrization for Dimensionality Reduction. In Conference on Neural Information Processing Systems , 2024 .
- Guillaume Huguet, Alexander Tong, Bastian Rieck, Jessie Huang, Manik Kuchroo, Matthew Hirn, Guy Wolf, and Smita Krishnaswamy. Time-Inhomogeneous Diffusion Geometry and Topology. SIAM Journal on Mathematics of Data Science , 5 ( 2 ): 346 -372 , 2023 .
- Guillaume Huguet, Alexander Tong, Edward De Brouwer, Yanlei Zhang, Guy Wolf, Ian Adelstein, and Smita Krishnaswamy. A Heat Diffusion Perspective on Geodesic Preserving Dimensionality Reduction. In Advances in Neural Information Processing Systems , volume 36 , 2024 .
- Sjoerd MH Huisman, Baldur Van Lew, Ahmed Mahfouz, Nicola Pezzotti, Thomas H¨ ollt, Lieke Michielsen, Anna Vilanova, Marcel JT Reinders, and Boudewijn PF Lelieveldt. Brainscope: interactive visual exploration of the spatial and temporal human brain transcriptome. Nucleic Acids Research , 45 ( 10 ):e 83 -e 83 , 2017 .
- Alan Julian Izenman. Reduced-rank regression for the multivariate linear model. Journal of Multivariate Analysis , 5 ( 2 ): 248 -264 , 1975 .
- Mathieu Jacomy, Tommaso Venturini, Sebastien Heymann, and Mathieu Bastian. ForceAtlas 2 , a continuous graph layout algorithm for handy network visualization designed for the Gephi software. PloS one , 9 ( 6 ): e 98679 , 2014 .
- Cheongjae Jang, Yung-Kyun Noh, and Frank Chongwoo Park. A Riemannian geometric framework for manifold learning of non-Euclidean data. Advances in Data Analysis and Classification , 15 ( 3 ): 673 -699 , 2021 .
- Hyeon Jeon, Jeongin Park, Sungbok Shin, and Jinwook Seo. Stop misusing t-SNE and UMAP for visual analytics. arXiv preprint arXiv: 2506 . 08725 , 2025 .
- Kui Jia, Lin Sun, Shenghua Gao, Zhan Song, and Bertram E Shi. Laplacian auto-encoders: An explicit learning of nonlinear data manifold. Neurocomputing , 160 : 250 -260 , 2015 .
- William B. Johnson and Joram Lindenstrauss. Extensions of Lipschitz mappings into Hilbert space. Contemporary Mathematics , 26 : 189 -206 , 1984 .
- Jolicoeur and J. E. Mosimann. Size and shape variation in the painted turtle. A principal component analysis. Growth , 24 : 339 -354 , 1960 .
- Pierre Jolicoeur. Multivariate geographical variation in the wolf Canis lupus L. Evolution , pages 283 -299 , 1959 .
- Ian T Jolliffe. Principal Component Analysis and Factor Analysis. In Principal Component Analysis , pages 115 -128 . Springer, 1986 .
- Eser Kandogan. Just-in-time annotation of clusters, outliers, and trends in point-based data visualizations. In IEEE Conference on Visual Analytics Science and Technology (V AST) , pages 73 -82 , 2012 .
- Sabina Kanton, Michael James Boyle, Zhisong He, Malgorzata Santel, Anne Weigert, F´ atima Sanch´ ıs-Calleja, Patricia Guijarro, Leila Sidow, Jonas Simon Fleck, Dingding Han, Zhengzong Qian, Michael Heide, Wieland B. Huttner, Philipp Khaitovich, Svante P¨ a¨ abo, Barbara Treutlein, and J. Gray Camp. Organoid singlecell genomic atlas uncovers human-specific features of brain development. Nature , 574 ( 7778 ): 418 -422 , 2019 .
- Jon Kleinberg. An impossibility theorem for clustering. In Advances in Neural Information Processing Systems , volume 15 , 2002 .
- Dmitry Kobak and Philipp Berens. The art of using t-SNE for single-cell transcriptomics. Nature Communications , 10 ( 1 ), 2019 .
- Dmitry Kobak and George C Linderman. Initialization is critical for preserving global data structure in both t-SNE and UMAP. Nature Biotechnology , 39 ( 2 ): 156 -157 , 2021 .
- Dmitry Kobak, Wieland Brendel, Christos Constantinidis, Claudia E Feierstein, Adam Kepecs, Zachary F Mainen, Xue-Lian Qi, Ranulfo Romo, Naoshige Uchida, and Christian K Machens. Demixed principal component analysis of neural population data. eLife , 5 :e 10989 , 2016 .

- Dmitry Kobak, George Linderman, Stefan Steinerberger, Yuval Kluger, and Philipp Berens. Heavy-tailed kernels reveal a finer cluster structure in t-SNE visualisations. In Joint European Conference on Machine Learning and Knowledge Discovery in Databases , pages 124 -139 , 2019 .
- Dmitry Kobak, Fred A. Hamprecht, Smita Krishnaswamy, Gal Mishne, and Sebastian Damrich. Low-Dimensional Embeddings of High-Dimensional Data: Algorithms and Applications (Dagstuhl Seminar 24122 ). Dagstuhl Reports , 14 ( 3 ): 92 -115 , 2024 .
- Samson J. Koelle, Hanyu Zhang, Marina Meila, and YuChia Chen. Manifold Coordinates with Physical Meaning. Journal of Machine Learning Research , 23 ( 133 ): 1 -57 , 2022 .
- Samson J Koelle, Hanyu Zhang, Octavian-Vlad Murad, and Marina Meila. Consistency of dictionary-based manifold learning. In International Conference on Artificial Intelligence and Statistics , pages 4348 -4356 , 2024 .
- Koffka. Principles of Gestalt psychology. Harcourt, Brace, 1935 .
- Dhruv Kohli, Alexander Cloninger, and Gal Mishne. LDLE: Low distortion local eigenmaps. Journal of Machine Learning Research , 22 ( 282 ): 1 -64 , 2021 .
- Dhruv Kohli, Johannes S Nieuwenhuis, Alexander Cloninger, Gal Mishne, and Devika Narain. RATS: Unsupervised manifold learning using low-distortion alignment of tangent spaces. bioRxiv , pages 2024 -10 , 2024 .
- Alexey Kroshnin, Eugene Stepanov, and Dario Trevisan. Infinite multidimensional scaling for metric measure spaces. ESAIM: Control, Optimisation and Calculus of Variations , 28 ( 58 ), 2022 .
- Joseph B Kruskal. Multidimensional scaling by optimizing goodness of fit to a nonmetric hypothesis. Psychometrika , 29 ( 1 ): 1 -27 , 1964 a.
- Joseph B Kruskal. Nonmetric multidimensional scaling: a numerical method. Psychometrika , 29 ( 2 ): 115 -129 , 1964 b.
- Manik Kuchroo, Jessie Huang, Patrick Wong, JeanChristophe Grenier, Dennis Shung, Alexander Tong, Carolina Lucas, Jon Klein, Daniel B Burkhardt, Scott Gigante, et al. Multiscale PHATE identifies multimodal signatures of COVID19 . Nature Biotechnology , 40 ( 5 ): 681 -691 , 2022 .
- Gioele La Manno, Kimberly Siletti, Alessandro Furlan, Daniel Gyllborg, Elin Vinsland, Alejandro Mossi Albiach, Christoffer Mattsson Langseth, Irina Khven, Alex R Lederer, Lisa M Dratva, et al. Molecular architecture of
- the developing mouse brain. Nature , 596 ( 7870 ): 92 -96 , 2021 .
- Stephane Lafon, Yosi Keller, and Ronald R Coifman. Data fusion and multicue data matching by diffusion maps. IEEE Transactions on Pattern Analysis and Machine Intelligence , 28 ( 11 ): 1784 -1797 , 2006 .
- Pierre Lambert, Cyril de Bodt, Michel Verleysen, and John A Lee. SQuadMDS: A lean Stochastic Quartet MDS improving global structure preservation in neighbor embedding like t-SNE and UMAP. Neurocomputing , 503 : 17 -27 , 2022 a.
- Pierre Lambert, Rebecca Marion, Julien Albert, Emmanuel Jean, Sacha Corbugy, and Cyril de Bodt. Globally local and fast explanations of t-SNE-like nonlinear embeddings. In AIMLAI workshop co-located with ACM International Conference on Information and Knowledge Management , 2022 b.
- Kasper Green Larsen and Jelani Nelson. Optimality of the Johnson-Lindenstrauss lemma. In IEEE 58 th Annual Symposium on Foundations of Computer Science (FOCS) , pages 633 -638 , 2017 .
- Jan Lause, Philipp Berens, and Dmitry Kobak. Analytic Pearson residuals for normalization of single-cell RNAseq UMI data. Genome Biology , 22 : 1 -20 , 2021 .
- Jan Lause, Dmitry Kobak, and Philipp Berens. The art of seeing the elephant in the room: 2 D embeddings of single-cell data do make sense. bioRxiv , pages 2024 -03 , 2024 .
- Neil Lawrence. Gaussian process latent variable models for visualisation of high dimensional data. In Advances in Neural Information Processing Systems , volume 16 , 2003 .
- Mikhail A Lebedev, Alexei Ossadtchi, Nil Adell Mill, N´ uria Armengol Urp´ ı, Maria R Cervera, and Miguel AL Nicolelis. Analysis of neuronal ensemble activity reveals the pitfalls and shortcomings of rotation dynamics. Scientific Reports , 9 ( 1 ): 18978 , 2019 .
- A. Lee and M. Verleysen. Shift-invariant similarities circumvent distance concentration in stochastic neighbor embedding and variants. Procedia Computer Science , 4 : 538 -547 , 2011 .
- John A Lee and Michel Verleysen. Nonlinear dimensionality reduction . Springer Science & Business Media, 2007 .
- John A Lee and Michel Verleysen. Quality assessment of dimensionality reduction: Rank-based criteria. Neurocomputing , 72 ( 7 ): 1431 -1443 , 2009 .

- John A Lee, Diego H Peluffo-Ord´ o˜ nez, and Michel Verleysen. Multi-scale similarities in stochastic neighbour embedding: Reducing dimensionality while preserving both local and global structure. Neurocomputing , 169 : 246 -261 , 2015 .
- John A. Lee, Edouard Couplet, Pierre Lambert, Ludovic Journaux, Dounia Mulders, Cyril de Bodt, and Michel Verleysen. Forget early exaggeration in t-SNE: early hierarchization preserves global structure. In ESANN , pages 321 -326 , 2024 .
- Sylvain Lespinats and Micha¨ el Aupetit. CheckViz: Sanity Check and Topological Clues for Linear and NonLinear Mappings. Computer Graphics Forum , 30 ( 1 ): 113 -125 , 2011 .
- Sylvain Lespinats, Benoit Colange, and Denys Dutykh. Nonlinear Dimensionality Reduction Techniques . Springer, 2022 .
- Elizaveta Levina and Peter Bickel. Maximum likelihood estimation of intrinsic dimension. In Advances in Neural Information Processing Systems , volume 17 , 2004 .
- Lewis, L. Van der Maaten, and V. de Sa. A Behavioral Investigation of Dimensionality Reduction. In Annual Meeting of the Cognitive Science Society , volume 34 , 2012 .
- Chang Li, Julian Thijssen, Thomas Kroes, Mitchell de Boer, Tamim Abdelaal, Thomas H¨ ollt, and Boudewijn Lelieveldt. Spacewalker enables interactive gradient exploration for spatial transcriptomics data. Cell Reports Methods , 3 ( 12 ), 2023 .
- Chun-Guang Li and Jun Guo. Supervised isomap with explicit mapping. In International Conference on Innovative Computing, Information and Control , volume 3 , pages 345 -348 , 2006 .
- Henry Li, Ofir Lindenbaum, Xiuyuan Cheng, and Alexander Cloninger. Variational diffusion autoencoders with random walk sampling. In European Conference on Computer Vision , pages 362 -378 , 2020 .
- Na Li, Vincent van Unen, Thomas H¨ ollt, Allan Thompson, Jeroen van Bergen, Nicola Pezzotti, Elmar Eisemann, Anna Vilanova, Susana M Chuva de Sousa Lopes, Boudewijn PF Lelieveldt, et al. Mass cytometry reveals innate lymphoid cell differentiation pathways in the human fetal intestine. Journal of Experimental Medicine , 215 ( 5 ): 1383 -1396 , 2018 .
- Siyuan Li, Haitao Lin, Zelin Zang, Lirong Wu, Jun Xia, and Stan Z Li. Invertible manifold learning for dimension reduction. In ECML PKDD , pages 713 -728 , 2021 .
- Sunhyuk Lim and Facundo M´ emoli. Classical multidimensional scaling on metric measure spaces. Information and Inference: A Journal of the IMA , 13 ( 2 ):iaae 007 , 2024 .
- Ya-Wei Eileen Lin, Ronald R. Coifman, Gal Mishne, and Ronen Talmon. Hyperbolic Diffusion Embedding and Distance for Hierarchical Representation Learning. In International Conference on Machine Learning , volume 202 , pages 21003 -21025 , 2023 .
- George C Linderman and Stefan Steinerberger. Dimensionality reduction via dynamical systems: the case of t-SNE. SIAM Review , 64 ( 1 ): 153 -178 , 2022 .
- George C Linderman, Manas Rachh, Jeremy G Hoskins, Stefan Steinerberger, and Yuval Kluger. Fast interpolation-based t-SNE for improved visualization of single-cell RNA-seq data. Nature Methods , 16 ( 3 ): 243 -245 , 2019 .
- Yang Liu and Jeffrey Heer. Somewhere Over the Rainbow: An Empirical Assessment of Quantitative Colormaps. In Conference on Human Factors in Computing Systems , pages 1 -12 , 2018 .
- Andrew W Long and Andrew L Ferguson. Landmark diffusion maps (L-dMaps): Accelerated manifold learning out-of-sample extension. Applied and Computational Harmonic Analysis , 47 ( 1 ): 190 -211 , 2019 .
- Andreas Loukas. Graph reduction with spectral and cut guarantees. Journal of Machine Learning Research , 20 ( 116 ): 1 -42 , 2019 .
- Catherine Lozupone and Rob Knight. UniFrac: a new phylogenetic method for comparing microbial communities. Applied and Environmental Microbiology , 71 ( 12 ): 8228 -8235 , 2005 .
- Alister Machado, Michael Behrisch, and Alexandru Telea. Necessary but not Sufficient: Limitations of Projection Quality Metrics. In Computer Graphics Forum , page e 70101 , 2025 .
- Scott Makeig, Anthony Bell, Tzyy-Ping Jung, and Terrence J Sejnowski. Independent Component Analysis of Electroencephalographic Data. In Advances in Neural Information Processing Systems , volume 8 , 1995 .
- Wilson E Marc´ ılio-Jr, Danilo M Eler, Fernando V Paulovich, and Rafael M Martins. HUMAP: hierarchical uniform manifold approximation and projection. IEEE Transactions on Visualization and Computer Graphics , 2024 .

- Rafael Messias Martins, Danilo Barbosa Coimbra, Rosane Minghim, and A.C. Telea. Visual analysis of dimensionality reduction quality for parameterized projections. Computers & Graphics , 41 : 26 -42 , 2014 .
- Leland McInnes. Glasbey Categorical Color Palette Tools. https://pypi.org/project/glasbey/ , Jun 2024 .
- Leland McInnes, John Healy, and James Melville. Umap: Uniform manifold approximation and projection for dimension reduction. arXiv preprint arXiv: 1802 . 03426 , 2018 .
- Marina Meil˘ a and Hanyu Zhang. Manifold learning: What, how, and why. Annual Review of Statistics and Its Application , 11 , 2024 .
- Gal Mishne, Ronen Talmon, Ron Meir, Jackie Schiller, Maria Lavzin, Uri Dubin, and Ronald R Coifman. Hierarchical coupled-geometry analysis for neuronal structure and activity pattern discovery. IEEE Journal of Selected Topics in Signal Processing , 10 ( 7 ): 1238 -1253 , 2016 .
- Gal Mishne, Eric Chi, and Ronald Coifman. Co-manifold learning with missing data. In International Conference on Machine Learning , pages 4605 -4614 , 2019 a.
- Gal Mishne, Uri Shaham, Alexander Cloninger, and Israel Cohen. Diffusion nets. Applied and Computational Harmonic Analysis , 47 ( 2 ): 259 -285 , 2019 b.
- Bassam Mokbel, Andrej Gisbrecht, and Barbara Hammer. On the effect of clustering on quality assessment measures for dimensionality reduction. In NIPS workshop on Challenges of Data Visualization , 2010 .
- Bassam Mokbel, Andrej Gisbrecht, and Barbara Hammer. Quality Assessment Measures for Dimensionality Reduction Applied on Clustering. In ICOLE , page 75 , 2011 .
- Kevin R Moon, David Van Dijk, Zheng Wang, Scott Gigante, Daniel B Burkhardt, William S Chen, Kristina Yim, Antonia van den Elzen, Matthew J Hirn, Ronald R Coifman, et al. Visualizing structure and transitions in high-dimensional biological data. Nature Biotechnology , 37 ( 12 ): 1482 -1492 , 2019 .
- Michael Moor, Max Horn, Bastian Rieck, and Karsten Borgwardt. Topological Autoencoders. In International Conference on Machine Learning , volume 119 , pages 7045 -7054 , 2020 .
- Morariu, A. Bibal, R. Cutura, B. Frenay, and M. Sedlmair. Predicting User Preferences of Dimensionality Reduction Embedding Quality. IEEE Transactions on Visualization & Computer Graphics , 29 ( 01 ): 745 -755 , 2023 .
- James T Morton, Liam Toran, Anna Edlund, Jessica L Metcalf, Christian Lauber, and Rob Knight. Uncovering the horseshoe effect in microbial analyses. Msystems , 2 ( 1 ): 10 -1128 , 2017 .
- Tamara Munzner. Visualization Analysis and Design . CRC Press, 2014 .
- Ian T Nabney, Yi Sun, Peter Tino, and Ata Kab´ an. Semisupervised learning of hierarchical latent trait models for data visualization. IEEE Transactions on Knowledge and Data Engineering , 17 ( 3 ): 384 -400 , 2005 .
- Boaz Nadler, Stephane Lafon, Ioannis Kevrekidis, and Ronald R Coifman. Diffusion maps, spectral clustering and eigenfunctions of Fokker-Planck operators. In Advances in Neural Information Processing Systems , pages 955 -962 , 2006 .
- Philipp Nazari, Sebastian Damrich, and Fred A Hamprecht. Geometric autoencoders: what you see is what you decode. In International Conference on Machine Learning , pages 25834 -25857 , 2023 .
- Erich Neuwirth. RColorBrewer: ColorBrewer Palettes, 2022 . URL https://cran.r-project.org/web/ packages/RColorBrewer/index.html .
- Andrew Ng, Michael Jordan, and Yair Weiss. On Spectral Clustering: Analysis and an algorithm. In Advances in Neural Information Processing Systems , volume 14 , 2001 .
- Lan Huong Nguyen and Susan Holmes. Ten quick tips for effective dimensionality reduction. PLoS Computational Biology , 15 ( 6 ):e 1006907 , 2019 .
- Andreas Noack. Modularity clustering is force-directed layout. Physical Review E , 79 ( 2 ): 026102 , 2009 .
- Maximilian Noichl. Modeling the structure of recent philosophy. Synthese , 198 ( 6 ): 5089 -5100 , 2021 .
- Maximilian Noichl. How localized are computational templates? A machine learning approach. Synthese , 201 ( 3 ), 2023 .
- Corey J Nolet, Victor Lafargue, Edward Raff, Thejaswi Nanditale, Tim Oates, John Zedlewski, and Joshua Patterson. Bringing UMAP closer to the speed of light with GPU acceleration. In AAAI Conference on Artificial Intelligence , volume 35 , pages 418 -426 , 2021 .
- Nomic AI. DeepScatter, 2025 . URL https://github.com/ nomic-ai/deepscatter .
- Luis Gustavo Nonato and Michael Aupetit. Multidimensional projection for visual analytics: Linking techniques with distortions, tasks, and layout enrichment. IEEE Transactions on Visualization and Computer Graphics , 25 ( 8 ): 2650 -2673 , 2018 .

- David Novak, Cyril de Bodt, Pierre Lambert, John A Lee, Sofie Van Gassen, and Yvan Saeys. A framework for quantifiable local and global structure preservation in single-cell dimensionality reduction. bioRxiv , 2023 .
- Olga Ovcharenko, Rita Sevastjanova, and Valentina Boeva. Feature Clock: High-Dimensional Effects in TwoDimensional Plots. In IEEE Visualization and Visual Analytics (VIS) , pages 151 -155 , 2024 .
- Katherine O'Toole and Em˝ oke- ´ Agnes Horv´ at. Novelty and cultural evolution in modern popular music. EPJ Data Science , 12 ( 1 ): 3 , 2023 .
- Lucas Pagliosa, Paulo Pagliosa, and Luis Gustavo Nonato. Understanding attribute variability in multidimensional projections. In SIBGRAPI Conference on Graphics, Patterns and Images , pages 297 -304 , 2016 .
- Gautam Pai, Ronen Talmon, Alex Bronstein, and Ron Kimmel. Dimal: Deep isometric manifold learning using sparse geodesic sampling. In IEEE Winter Conference on Applications of Computer Vision , pages 819 -828 , 2019 .
- Rahul Paul and Stephan K Chalup. A study on validating non-linear dimensionality reduction using persistent homology. Pattern Recognition Letters , 100 : 160 -166 , 2017 .
- Karl Pearson. On lines and planes of closest fit to systems of points in space. The London, Edinburgh, and Dublin Philosophical Magazine and Journal of Science , 2 ( 11 ): 559 -572 , 1901 .
- Fabian Pedregosa, Ga¨ el Varoquaux, Alexandre Gramfort, Vincent Michel, Bertrand Thirion, Olivier Grisel, Mathieu Blondel, Peter Prettenhofer, Ron Weiss, Vincent Dubourg, et al. Scikit-learn: Machine learning in Python. Journal of Machine Learning Research , 12 : 2825 -2830 , 2011 .
- Erez Peterfreund, Ofir Lindenbaum, Felix Dietrich, Tom Bertalan, Matan Gavish, Ioannis G Kevrekidis, and Ronald R Coifman. Local conformal autoencoder for standardized data coordinates. Proceedings of the National Academy of Sciences , 117 ( 49 ): 30918 -30927 , 2020 .
- Pezzotti, T. H¨ ollt, B. Lelieveldt, E. Eisemann, and A. Vilanova. Hierarchical Stochastic Neighbor Embedding. Computer Graphics Forum , 35 ( 3 ): 21 -30 , 2016 a.
- Nicola Pezzotti, Boudewijn PF Lelieveldt, Laurens Van Der Maaten, Thomas H¨ ollt, Elmar Eisemann, and Anna Vilanova. Approximated and user steerable t-SNE for progressive visual analytics. IEEE Transactions on Visualization and Computer Graphics , 23 ( 7 ): 1739 -1752 , 2016 b.
- Nicola Pezzotti, Julian Thijssen, Alexander Mordvintsev, Thomas H¨ ollt, Baldur Van Lew, Boudewijn PF Lelieveldt, Elmar Eisemann, and Anna Vilanova. GPGPU linear complexity t-SNE optimization. IEEE Transactions on Visualization and Computer Graphics , 26 ( 1 ): 1172 -1181 , 2019 .
- Pavlin G Poliˇ car, Martin Straˇ zar, and Blaˇ z Zupan. Embedding to reference t-SNE space addresses batch effects in single-cell classification. Machine Learning , 112 ( 2 ): 721 -740 , 2023 .
- Pavlin G Poliˇ car, Martin Straˇ zar, and Blaˇ z Zupan. openTSNE: a modular Python library for t-SNE dimensionality reduction and embedding. Journal of Statistical Software , 109 : 1 -30 , 2024 .
- Pavlin G. Poliˇ car and Blaˇ z Zupan. VERA: Generating Visual Explanations of Two-Dimensional Embeddings via Region Annotation. arXiv , 2024 .
- Shaun Purcell, Benjamin Neale, Kathe Todd-Brown, Lori Thomas, Manuel A. R. Ferreira, David Bender, Julian Maller, Pamela Sklar, Paul I. W. de Bakker, Mark J. Daly, and Pak C. Sham. PLINK: A Tool Set for WholeGenome Association and Population-Based Linkage Analyses. The American Journal of Human Genetics , 81 ( 3 ): 559 -575 , 2007 .
- C Radhakrishna Rao. The utilization of multiple measurements in problems of biological classification. Journal of the Royal Statistical Society. Series B (Methodological) , 10 ( 2 ): 159 -203 , 1948 .
- Jake S Rhodes, Adele Cutler, Guy Wolf, and Kevin R Moon. Random forest-based diffusion information geometry for supervised visualization and data exploration. In Statistical Signal Processing Workshop (SSP) , pages 331 -335 , 2021 .
- Jake S Rhodes, Adrien Aumon, Sacha Morin, Marc Girard, Catherine Larochelle, Elsa Brunet-Ratnasingham, Am´ elie Pagliuzza, Lorie Marchitto, Wei Zhang, Adele Cutler, et al. Gaining biological insights through supervised data visualization. bioRxiv , pages 2023 -11 , 2023 .
- Bastian Rieck and Heike Leitte. Persistent homology for the evaluation of dimensionality reduction schemes. Computer Graphics Forum , 34 ( 3 ): 431 -440 , 2015 .
- Markus Ringn´ er. What is principal component analysis? Nature Biotechnology , 26 ( 3 ): 303 -304 , 2008 .
- Duccio Rocchini, Ludovico Chieffallo, Elisa Thouverai, Rossella D'Introno, Francesca Dagostin, Emma Donini, Giles Foody, Simon Garnier, Guilherme G. Mazzochini,

- Vitezslav Moudry, Bob Rudis, Petra Simova, Michele Torresani, and Jakub Nowosad. Under the mantra: 'Make use of colorblind friendly graphs'. Environmetrics , 35 ( 6 ):e 2877 , 2024 .
- Peter J Rousseeuw. Silhouettes: a graphical aid to the interpretation and validation of cluster analysis. Journal of Computational and Applied Mathematics , 20 : 53 -65 , 1987 .
- Sam Roweis and Lawrence Saul. Nonlinear dimensionality reduction by locally linear embedding. Science , 290 ( 5500 ): 2323 -2326 , 2000 .
- Dominik Sacha, Leishi Zhang, Michael Sedlmair, John A Lee, Jaakko Peltonen, Daniel Weiskopf, Stephen C North, and Daniel A Keim. Visual interaction with dimensionality reduction: A structured literature analysis. IEEE Transactions on Visualization and Computer Graphics , 23 ( 1 ): 241 -250 , 2016 .
- Dominik Sacha, Michael Sedlmair, Leishi Zhang, John A. Lee, Jaakko Peltonen, Daniel Weiskopf, Stephen C. North, and Daniel A. Keim. What you see is what you can change: Human-centered machine learning by interactive visualization. Neurocomputing , 268 : 164 -175 , 2017 .
- Tim Sainburg, Leland McInnes, and Timothy Q Gentner. Parametric UMAP embeddings for representation and semisupervised learning. Neural Computation , 33 ( 11 ): 2881 -2907 , 2021 .
- John W Sammon. A nonlinear mapping for data structure analysis. IEEE Trans. Comput. , 100 ( 5 ): 401 -409 , 1969 .
- Federico Scala, Dmitry Kobak, Matteo Bernabucci, Yves Bernaerts, Cathryn Ren´ e Cadwell, Jesus Ramon Castro, Leonard Hartmanis, Xiaolong Jiang, Sophie Laturnus, Elanine Miranda, et al. Phenotypic variation of transcriptomic cell types in mouse motor cortex. Nature , 598 ( 7879 ): 144 -150 , 2021 .
- Benjamin Schmidt. Stable random projection: Lightweight, general-purpose dimensionality reduction for digitized libraries. Journal of Cultural Analytics , 3 ( 1 ), 2018 .
- Bernhard Sch¨ olkopf, Alexander Smola, and Klaus-Robert M¨ uller. Kernel principal component analysis. In Artificial Neural Networks - ICANN , pages 583 -588 , 1997 .
- Tobias Schreck, Tatiana von Landesberger, and Sebastian Bremm. Techniques for Precision-Based Visual Analysis of Projected Data. Information Visualization , 9 ( 3 ): 181 -193 , 2010 .
- Christin Seifert, Vedran Sabol, and Wolfgang Kienreich. Stress Maps: Analysing Local Phenomena in Dimensionality Reduction Based Visualisations. In International Symposium on Visual Analytics Science and Technology , 2010 .
- Uri Shaham, Kelly Stanton, Henry Li, Ronen Basri, Boaz Nadler, and Yuval Kluger. SpectralNet: Spectral Clustering using Deep Neural Networks. In International Conference on Learning Representations , 2018 .
- Chao Shen and Hau-Tieng Wu. Scalability and robustness of spectral embedding: landmark diffusion is all you need. Information and Inference: A Journal of the IMA , 11 ( 4 ): 1527 -1595 , 2022 .
- Roger N Shepard. The analysis of proximities: multidimensional scaling with an unknown distance function. I. Psychometrika , 27 ( 2 ): 125 -140 , 1962 a.
- Roger N Shepard. The analysis of proximities: multidimensional scaling with an unknown distance function. II. Psychometrika , 27 ( 3 ): 219 -246 , 1962 b.
- Jianbo Shi and Jitendra Malik. Normalized cuts and image segmentation. IEEE Transactions on Pattern Analysis and Machine Intelligence , 22 ( 8 ): 888 -905 , 2000 .
- Vin D. Silva and Joshua B. Tenenbaum. Global versus local methods in nonlinear dimensionality reduction. In Advances in Neural Information Processing Systems , volume 15 , pages 705 --712 , 2003 .
- Amit Singer. From graph to manifold Laplacian: The convergence rate. Applied and Computational Harmonic Analysis , 21 ( 1 ): 128 -134 , 2006 .
- Amit Singer and H-T Wu. Vector diffusion maps and the connection Laplacian. Communications on Pure and Applied Mathematics , 65 ( 8 ): 1067 -1144 , 2012 .
- Amit Singer and Hau-Tieng Wu. Spectral convergence of the connection Laplacian from random samples. Information and Inference: A Journal of the IMA , 6 ( 1 ): 58 -123 , 2017 .
- Martin Skrodzki, Nicolas F. Chaves de Plaza, Thomas H¨ ollt, Elmar Eisemann, and Klaus Hildebrandt. Navigating Perplexity: A linear relationship with the data set size in t-SNE embeddings. arXiv , 2023 .
- Le Song, Arthur Gretton, Karsten Borgwardt, and Alex Smola. Colored Maximum Variance Unfolding. In Advances in Neural Information Processing Systems , volume 20 , 2007 .
- Charles Spearman. 'General Intelligence' Objectively Determined and Measured. The American Journal of Psychology , 15 ( 2 ): 201 -292 , 1904 .

- Julian Stahnke, Marian D¨ ork, Boris M¨ uller, and Andreas Thom. Probing Projections: Interaction Techniques for Interpreting Arrangements and Errors of Dimensionality Reductions. IEEE Transactions on Visualization and Computer Graphics , 22 ( 1 ): 629 -638 , 2016 .
- Jacob L. Steenwyk and Antonis Rokas. ggpubfigs: Colorblind-Friendly Color Palettes and ggplot 2 Graphic System Extensions for Publication-Quality Scientific Figures. Microbiology Resource Announcements , 10 ( 44 ), 2021 .
- Shiquan Sun, Jiaqiang Zhu, Ying Ma, and Xiang Zhou. Accuracy, robustness and scalability of dimensionality reduction methods for single-cell RNA-seq analysis. Genome Biology , 20 : 1 -21 , 2019 .
- Ronen Talmon and Ronald R Coifman. Empirical intrinsic geometry for nonlinear modeling and time series filtering. Proceedings of the National Academy of Sciences , 110 ( 31 ): 12535 -12540 , 2013 .
- Ronen Talmon, Israel Cohen, and Sharon Gannot. Singlechannel transient interference suppression with diffusion maps. IEEE Transactions on Audio, Speech, and Language Processing , 21 ( 1 ): 132 -144 , 2012 .
- Jian Tang, Jingzhou Liu, Ming Zhang, and Qiaozhu Mei. Visualizing large-scale and high-dimensional data. In International Conference on World Wide Web , pages 287 -297 , 2016 .
- Bosiljka Tasic, Zizhen Yao, Lucas T. Graybuck, Kimberly A. Smith, Thuc Nghi Nguyen, Darren Bertagnolli, Jeff Goldy, Emma Garren, Michael N. Economo, Sarada Viswanathan, Osnat Penn, Trygve Bakken, Vilas Menon, Jeremy Miller, Olivia Fong, Karla E. Hirokawa, Kanan Lathia, Christine Rimorin, Michael Tieu, Rachael Larsen, Tamara Casper, Eliza Barkan, Matthew Kroll, Sheana Parry, Nadiya V. Shapovalova, Daniel Hirschstein, Julie Pendergraft, Heather A. Sullivan, Tae Kyung Kim, Aaron Szafer, Nick Dee, Peter Groblewski, Ian Wickersham, Ali Cetin, Julie A. Harris, Boaz P. Levi, Susan M. Sunkin, Linda Madisen, Tanya L. Daigle, Loren Looger, Amy Bernard, John Phillips, Ed Lein, Michael Hawrylycz, Karel Svoboda, Allan R. Jones, Christof Koch, and Hongkui Zeng. Shared and distinct transcriptomic cell types across neocortical areas. Nature , 563 ( 7729 ): 72 -78 , 2018 .
- Kye M Taylor and Franc ¸ois G Meyer. A random walk on image patches. SIAM Journal on Imaging Sciences , 5 ( 2 ): 688 -725 , 2012 .
- Joshua B Tenenbaum, Vin De Silva, and John C Langford. A global geometric framework for nonlinear dimensionality reduction. Science , 290 ( 5500 ): 2319 -2323 , 2000 .
- The 1000 Genomes Project Consortium. A global reference for human genetic variation. Nature , 526 ( 7571 ): 68 -74 , 2015 .
- Julian Thijssen, Zonglin Tian, and Alexandru Telea. Interactive tools for explaining multidimensional projections for high-dimensional tabular data. Computers & Graphics , 122 : 103987 , 2024 .
- Louis Leon Thurstone. Multiple factor analysis. Psychological Review , 38 ( 5 ), 1931 .
- Zonglin Tian, Xiaorui Zhai, Daan van Driel, Gijs van Steenpaal, Mateus Espadoto, and Alexandru Telea. Using multiple attribute-based explanations of multidimensional projections to explore high-dimensional data. Computers & Graphics , 98 : 93 -104 , 2021 .
- Zonglin Tian, Wouter Castelein, Tamara Mchedlidze, and Alexandru C Telea. Measuring and Interpreting the Quality of 3 DProjections of High-Dimensional Data. In International Joint Conference on Computer Vision, Imaging and Computer Graphics , pages 348 -373 , 2023 .
- Peter Tino, Ian Nabney, and Yi Sun. Using directional curvatures to visualize folding patterns of the GTM projection manifolds. In Artificial Neural Networks ICANN , pages 421 -428 , 2001 a.
- Peter Tino, Ian Nabney, Yi Sun, and Bruce S Williams. A principled approach to interactive hierarchical nonlinear visualization of high-dimensional data. Frontiers in Data Mining and Bioinformatics , 2001 b.
- Michael E Tipping and Christopher M Bishop. Mixtures of probabilistic principal component analyzers. Neural Computation , 11 ( 2 ): 443 -482 , 1999 a.
- Michael E Tipping and Christopher M Bishop. Probabilistic Principal Component Analysis. Journal of the Royal Statistical Society Series B: Statistical Methodology , 61 ( 3 ): 611 -622 , 1999 b.
- Warren S Torgerson. Multidimensional scaling: I. Theory and method. Psychometrika , 17 ( 4 ): 401 -419 , 1952 .
- John W Tukey. Exploratory data analysis . Addison-Wesley, 1977 .
- John W. Tukey. We Need Both Exploratory and Confirmatory. The American Statistician , 34 ( 1 ): 23 -25 , 1980 .
- Laurens van der Maaten. Learning a parametric embedding by preserving local structure. In Artificial Intelligence and Statistics , pages 384 -391 , 2009 .
- Laurens van der Maaten. Accelerating t-SNE using treebased algorithms. Journal of Machine Learning Research , 15 ( 1 ): 3221 -3245 , 2014 .

- Laurens van der Maaten and Geoffrey Hinton. Visualizing Data using t-SNE. Journal of Machine Learning Research , 9 ( 86 ): 2579 -2605 , 2008 .
- Vincent Van Unen, Thomas H¨ ollt, Nicola Pezzotti, Na Li, Marcel JT Reinders, Elmar Eisemann, Frits Koning, Anna Vilanova, and Boudewijn PF Lelieveldt. Visual analysis of mass cytometry data by hierarchical stochastic neighbour embedding reveals rare cell types. Nature Communications , 8 ( 1 ): 1740 , 2017 .
- Jarkko Venna, Jaakko Peltonen, Kristian Nybo, Helena Aidos, and Samuel Kaski. Information Retrieval Perspective to Nonlinear Dimensionality Reduction for Data Visualization. Journal of Machine Learning Research , 11 ( 13 ): 451 -490 , 2010 .
- Alexander Vieth, Thomas Kroes, Julian Thijssen, Baldur van Lew, Jeroen Eggermont, Soumyadeep Basu, Elmar Eisemann, Anna Vilanova, Thomas H¨ ollt, and Boudewijn Lelieveldt. ManiVault: A Flexible and Extensible Visual Analytics Framework for HighDimensional Data. IEEE Transactions on Visualization and Computer Graphics , 2023 .
- Max Vladymyrov. No Pressure! Addressing the Problem of Local Minima in Manifold Learning Algorithms. In Advances in Neural Information Processing Systems , volume 32 , 2019 .
- Max Vladymyrov and Miguel Carreira-Perpinan. Lineartime training of nonlinear low-dimensional embeddings. In Artificial Intelligence and Statistics , pages 968 -977 , 2014 .
- Ulrike Von Luxburg, Robert C Williamson, and Isabelle Guyon. Clustering: Science or art? In ICML Workshop on Unsupervised and Transfer Learning , pages 65 -79 , 2012 .
- Kaiwen Wang, Yuqiu Yang, Fangjiang Wu, Bing Song, Xinlei Wang, and Tao Wang. Comparative analysis of dimension reduction methods for cytometry by timeof-flight data. Nature Communications , 14 ( 1 ), 2023 a.
- Shu Wang, Eduardo D Sontag, and Douglas A Lauffenburger. What cannot be seen correctly in 2 D visualizations of single-cell 'omics data? Cell Systems , 14 ( 9 ): 723 -731 , 2023 b.
- Yingfan Wang, Haiyang Huang, Cynthia Rudin, and Yaron Shaposhnik. Understanding how dimension reduction tools work: an empirical approach to deciphering t-SNE, UMAP, TriMAP, and PaCMAP for data visualization. Journal of Machine Learning Research , 22 ( 201 ): 1 -73 , 2021 .
- Colin Ware and Rusty Bobrow. Motion coding for pattern detection. In Symposium on Applied Perception in Graphics and Visualization , pages 107 -110 , 2006 .
- Jeremy Wayland, Corinna Coupette, and Bastian Rieck. Mapping the Multiverse of Latent Representations. In International Conference on Machine Learning (ICML) , 2024 .
- Kilian Q Weinberger and Lawrence K Saul. An Introduction to Nonlinear Dimensionality Reduction by Maximum Variance Unfolding. In American Association for Artificial Intelligence , volume 6 , pages 1683 -1686 , 2006 .
- Lloyd Welch. Lower bounds on the maximum cross correlation of signals (Corresp.). IEEE Transactions on Information Theory , 20 ( 3 ): 397 -399 , 1974 .
- Jiazhi Xia, Yuchen Zhang, Jie Song, Yang Chen, Yunhai Wang, and Shixia Liu. Revisiting dimensionality reduction techniques for visual cluster analysis: An empirical study. IEEE Transactions on Visualization and Computer Graphics , 28 ( 1 ): 529 -539 , 2021 .
- Ruizhi Xiang, Wencan Wang, Lei Yang, Shiyuan Wang, Chaohan Xu, and Xiaowen Chen. A comparison for dimensionality reduction methods of single-cell RNAseq data. Frontiers in Genetics , 12 , 2021 .
- Itai Yanai and Martin Lercher. A hypothesis is a liability. Genome Biology , 21 : 1 -5 , 2020 .
- Zhirong Yang, Irwin King, Zenglin Xu, and Erkki Oja. Heavy-tailed symmetric stochastic neighbor embedding. In Advances in Neural Information Processing Systems , pages 2169 -2177 , 2009 .
- Zhirong Yang, Jaakko Peltonen, and Samuel Kaski. Scalable Optimization of Neighbor Embedding for Visualization. In International Conference on Machine Learning , volume 2 , pages 127 -135 , 2013 .
- Byron M Yu, John P Cunningham, Gopal Santhanam, Stephen Ryu, Krishna V Shenoy, and Maneesh Sahani. Gaussian-process factor analysis for low-dimensional single-trial analysis of neural population activity. In Advances in Neural Information Processing Systems , volume 21 , 2008 .
- Meiting Yu, Siqian Zhang, Lingjun Zhao, and Gangyao Kuang. Deep supervised t-SNE for SAR target recognition. In International Conference on Frontiers of Sensors Technologies , pages 265 -269 , 2017 .
- Jinjie Zhang and Rayan Saab. Faster binary Embeddings for preserving Euclidean distances. In International Conference on Learning Representations , 2021 .

- Zhenyue Zhang and Hongyuan Zha. Principal Manifolds and Nonlinear Dimensionality Reduction via Tangent Space Alignment. SIAM Journal on Scientific Computing , 26 ( 1 ): 313 -338 , 2004 .
- Hui Zou, Trevor Hastie, and Robert Tibshirani. Sparse Principal Component Analysis. Journal of Computational and Graphical Statistics , 15 ( 2 ): 265 -286 , 2006 .

## 8 Methods

Data and code availability All analysis code is openly available at https://github.com/dkobak/ low-dim-embeddings-review/ . All datasets are openly available and, for convenience and reproducibility, the preprocessed versions are shared in our repository.

Data sources and preprocessing For all datasets, we aimed to use standard preprocessing steps, usually taken from prior work.

- The Simple English Wikipedia data were downloaded from https://huggingface.co/datasets/ Cohere/wikipedia-22-12-simple-embeddings . This dataset contains 485859 text paragraphs from the Simple English Wikipedia, represented as 768 -dimensional vectors using a language model ( multilingual-22-12 from Cohere.AI; the model generated embeddings of text paragraphs with the prepended Wikipedia article title). We scaled each of these vectors to have a unit l 2-norm, ensuring that Euclidean and cosine distances yield identical k NN sets.

To annotate the UMAP embedding, we used the Toponymy library ( https://github.com/ TutteInstitute/toponymy ). Toponymy performed HDBSCAN clustering of the 2 D UMAP embedding (with cluster selection method="leaf" ). The cluster labels were generated by Toponymy through extracting various types of information from each cluster (including representative exemplars, distinguishing keyphrases, and relevant sub-clusters) and passing this to a generative LLM ( c4ai-command-r-08-2024 from Cohere.AI) to generate a concise human-readable name.

- Tasic et al. data (Tasic et al., 2018 ) contain 23822 cells from mouse cortex, with 45768 genes as features. This is an integer count matrix showing how many RNA molecules of each gene were detected in each cell. We followed preprocessing steps used in Kobak and Berens ( 2019 ). This includes selecting 3 000 highly variable genes, normalizing by the total gene count in each cell, log ( 1 + x ) transformation, and finally projecting to 50 components via PCA. The remaining 50 components preserve 62 . 6 % of the total 3 000 -dimensional variance. Note that the fraction of variance explained by the first two PCs reported in the main text is with respect to the 50 -dimensional data, and all quality measures for all methods were computed based on the 50 -dimensional data as well.
- Kanton et al. data (Kanton et al., 2019 ) contain 20272 cells from human brain organoids (cell line 409 b 2 ), with 32856 genes as features. We followed preprocessing steps used in B¨ ohm et al. ( 2022 ) and Damrich et al. ( 2024 b). As above, these include selecting 1000 highly variable genes, normalization, log-transformation, and PCA projection to 50 components (preserving 60 . 2 % of the total 1000 -dimensional variance). As above, the fraction of variance explained by the first two PCs reported in the main text is with respect to the 50 -dimensional data, and all quality measures were computed based on the 50 -dimensional data as well.
- The raw 1000 Genomes Project data (The 1000 Genomes Project Consortium, 2015 ) are available at https://ftp.1000genomes.ebi.ac.uk . This dataset contains 3450 human genotypes. We used PLINK (Purcell et al., 2007 ) to filter for linkage disequilibrium and high variability regions as described in (Diaz-Papkovich et al., 2019 ) and (Diaz-Papkovich et al., 2023 ). The specific PLINK parameters are given in the shell scripts available in our GitHub repository. This resulted in an integer-valued data matrix with 53999 features, containing values 0 , 1 , and 2 , representing the number of alleles differing from a reference genome. We replaced missing values, coded as -1, by 0 . Preprocessing did not involve PCA projection.

Algorithm implementations For all methods, we aimed at using the most standard Python implementation with default parameters.

- For PCA, we used sklearn.decomposition.PCA from scikit-learn version 1 . 5 . 1 (Pedregosa et al., 2011 ), with svd solver='arpack' .
- For MDS, we used the stochastic SQuadMDS algorithm (Lambert et al., 2022 a) with the default parameters (including PCA initialization) using the code provided at https://github.com/PierreLambert3/ SQuaD-MDS-and-FItSNE-hybrid (commit 4cfa8b4 ). The 1000 Genomes dataset was small enough to use a non-stochastic MDS implementation, so for that dataset, we used sklearn.manifold.MDS with the default parameters and manually provided PCA initialization to the fit() function.
- For Laplacian Eigenmaps, we used sklearn.manifold.SpectralEmbedding with n neighbors=100 . We tried various numbers of nearest neighbors and obtained similar embeddings. The default value in this implementation is 10 % of

the sample size, which is computationally unfeasible for large datasets. For the Simple English Wikipedia dataset, we used solver='amg' as the default solver only works with dense matrices and raised memory errors.

- For PHATE, we used the phate library (Moon et al., 2019 ), version 1 . 0 . 11 , with all default parameters (in particular, the number of nearest neighbors was set to 5 ).
- For t -SNE, we used the opentsne library (Poliˇ car et al., 2024 ), version 1 . 0 . 2 , with all default parameters (in particular, perplexity 30 and PCA initialization).
- For UMAP, we used the umap-learn library (McInnes et al., 2018 ), version 0 . 5 . 7 , with all default parameters (in particular, 15 nearest neighbors and spectral initialization). For the Simple English Wikipedia dataset, we increased the number of training epochs to 500 to ensure better convergence.

Some embeddings were flipped horizontally and/or vertically to ease visual comparison between methods.

Quality assessment We employed four quality measures to evaluate the 24 embeddings (four datasets and six methods). These quality measures are described below, with n denoting the sample size in a given dataset, δ ij denoting the high-dimensional Euclidean pairwise distances, and dij denoting the low-dimensional Euclidean pairwise distances.

- The Pearson correlation between δ ij and dij (Becht et al., 2019 ; Kobak and Berens, 2019 ). The correlation was computed across the set of all n ( n -1 ) /2 pairwise distances. For the Wikipedia dataset, we estimated the correlation using a random subset of 1000 points, computing the correlation over all 1 000 · ( n -1 ) pairwise distances between these points and all points in the dataset. This measure serves as the y -axis in Figure 7 .
- The σ -distortion (Chennuru Vankadara and von Luxburg, 2018 ) between δ ij and dij . This measure is defined via the ratios ρ ij = dij / δ ij . If we denote the average ratio as ¯ ρ , then the σ -distortion is defined as the variance of the normalized ratios ρ ij /¯ ρ , i.e., the average value of ( ρ ij /¯ ρ -1 ) 2 . The variance is computed over all n ( n -1 ) /2 normalized ratios. Note that this measure is not affected by the scale of the embedding distances dij . For the Wikipedia dataset, we estimated the σ -distortion using a random subset of 1 000 points and computing the variance over 1 000 · ( n -1 ) normalized ratio values.
- The average overlap between the 10 nearest neighbors in the high-dimensional space and the 10 nearest neighbors in the embedding, averaged across all data points (Lee and Verleysen, 2009 ; Kobak and Berens, 2019 ). This measure was computed using exact nearest neighbors, averaging across all n points in the dataset. This measure serves as the x -axis in Figure 7 .
- The area under the rescaled neighbor-preservation curve (Lee et al., 2015 ). This measure quantifies the reproduction of neighborhoods across neighborhoods of varying size. The computation is based on the average overlap between high-dimensional and low-dimensional neighborhoods of size k ∈ [ 1, n -2 ] ,

Q ( k ) = 1 n ∑ i ∣ ∣ ∣ ν k i ∩ n k i ∣ ∣ ∣ k , ( 1 )

where ν k i and n k i are sets of k nearest neighbors of data point i in the original space and in the embedding, respectively. Note that for k = 10, this gives the same measure as described above and used in Figure 7 . For the Wikipedia dataset, we estimated Q ( k ) as an average over a random subset of 1000 points, based on determining, for each point in the subset, the exact high-dimensional and low-dimensional neighborhoods among all points in the dataset, for all values of k ∈ [ 1, n -2 ] (Novak et al., 2023 ).

For a random embedding, the expected value of Q ( k ) is k / ( n -1 ) . Following Lee et al. ( 2015 ), we rescale Q ( k ) as

R ( k ) = ( n -1 ) Q ( k ) -k n -1 -k , ( 2 )

such that for any value of k , R = 0 corresponds to the chance level and R = 1 corresponds to a perfect neighborhood overlap.

Finally, we compute the area under the R ( k ) curve from k = 1 to k = n -2, with logarithmic scaling of the k -axis to give more weight to smaller neighborhoods (and with a scaling factor to make AUC lie between 0 and 1 ), as

AUC = ( n -2 ∑ k = 1 k -1 ) -1 n -2 ∑ k = 1 R ( k ) k . ( 3 )

***Table 2 : Values of the quality measures for all embeddings. The best value in each row is highlighted in bold. As indicated by the arrow annotations to the quality measures ( ↑ | ↓ ), for σ -distortion, lower scores are better, whereas for all other measures, higher scores are better.***

| Dataset | Quality measure | PCA | MDS | LE | PHATE | t -SNE | UMAP |
|---|---|---|---|---|---|---|---|
| Tasic et al. | Distance correlation ↑ | . 92 | . 88 | . 25 | . 34 | . 45 | . 53 |
| Tasic et al. | σ -distortion ↓ | . 34 | . 13 | 1 . 03 | . 23 | . 19 | . 20 |
| Tasic et al. | k NN preservation ↑ | . 02 | . 04 | . 11 | . 19 | . 46 | . 25 |
| Tasic et al. | AUC ↑ | . 21 | . 29 | . 32 | . 34 | . 50 | . 41 |
| Kanton et al. | Distance correlation ↑ | . 88 | . 89 | . 73 | . 72 | . 67 | . 64 |
| Kanton et al. | σ -distortion ↓ | . 21 | . 11 | . 40 | . 35 | . 15 | . 20 |
| Kanton et al. | k NN preservation ↑ | . 02 | . 04 | . 07 | . 14 | . 38 | . 21 |
| Kanton et al. | AUC ↑ | . 24 | . 29 | . 26 | . 31 | . 46 | . 37 |
| 1000 Genomes Project | Distance correlation ↑ | . 83 | . 70 | . 30 | . 65 | . 68 | . 46 |
| 1000 Genomes Project | σ -distortion ↓ | . 39 | . 21 | . 91 | . 28 | . 23 | . 36 |
| 1000 Genomes Project | k NN preservation ↑ | . 04 | . 04 | . 04 | . 12 | . 20 | . 14 |
| 1000 Genomes Project | AUC ↑ | . 24 | . 20 | . 20 | . 29 | . 41 | . 27 |
| Simple English Wikipedia k | Distance correlation ↑ | . 32 | . 63 | . 18 | . 14 | . 27 | . 23 |
| Simple English Wikipedia k | σ -distortion ↓ | . 28 | . 19 | 1 . 88 | . 80 | . 22 | . 27 |
| Simple English Wikipedia k | NN preservation ↑ | . 00 | . 00 | . 01 | . 02 | . 26 | . 08 |
| Simple English Wikipedia k | AUC ↑ | . 06 | . 07 | . 08 | . 07 | . 21 | . 13 |