### Abstract

This paper explores the critical role of data clustering in data science, emphasizing its methodologies, tools, and diverse applications. Traditional techniques, such as partitional and hierarchical clustering, are analyzed alongside advanced approaches such as data stream, density-based, graph-based, and model-based clustering for handling complex structured datasets. The paper highlights key principles underpinning clustering, outlines widely used tools and frameworks, introduces the workflow of clustering in data science, discusses challenges in practical implementation, and examines various applications of clustering. By focusing on these foundations and applications, the discussion underscores clustering's transformative potential. The paper concludes with insights into future research directions, emphasizing clustering's role in driving innovation and enabling data-driven decision-making.

Keywords: data mining, cluster analysis, data science, artificial intelligence, machine learning

## 1. Introduction

Advances in information and data acquisition technologies allow the daily collection of vast amounts of data from sources like sensors, the internet, and devices. These data reflect system behaviors and may contain valuable knowledge. K nowl -edge D iscovery in D atabases (KDD) uses D ata M ining and related methods to find useful patterns in large datasets. Data mining, also called knowledge extraction, applies specific algorithms for pattern detection. Figure 1 illustrates the general KDD process as described in (Abonyi & Feil, 2007), highlighting the role of D ata M ining as a key step in the overall process of knowledge discovery from data.

D ata S cience is a broader, interdisciplinary field that combines computer science, statistics, mathematics, domain expertise, and other techniques to extract insights and derive solutions from data (Kotu & Deshpande, 2018). While D ata M in -ing focuses on discovering patterns and relationships within datasets, it is just one step within the larger D ata S cience workflow. In the context of KDD, D ata S cience extends beyond pattern detection to include data preprocessing, visualization, predictive modeling, and decision-making, o ff ering a comprehensive framework for solving complex problems with data.

C lustering is a fundamental technique in D ata S cience , which organizes data into meaningful groups, or clusters, based on their intrinsic similarities (Aggarwal, 2013). A cluster is generally considered as a group of objects in which objects within each cluster are more closely related to one another than objects assigned to other di ff erent clusters. Unlike classification,

> ∗ Corresponding author: Tai Dinh (t dinh@kcg.ac.jp)

> ⊕ Contributed equally to this work

which relies on predefined labels, clustering is an unsupervised learning approach. It is 'unsupervised' because it is not guided by a priori ideas of which variables or samples belong in which clusters, and 'learning' because the machine algorithms learn how to cluster (Kassambara, 2017). This technique is widely used to handle complex, high-dimensional datasets and is pivotal for understanding the inherent organization of data (Han et al., 2022).

In today's data-driven world, where organizations and researchers deal with enormous volumes of data, clustering serves as a critical tool for summarizing and analyzing this information. By grouping similar data points, clustering aids in simplifying complex datasets, enabling better exploration and visualization, and laying the groundwork for further data analysis (Tukey et al., 1977). Furthermore, clustering finds applications in a wide array of fields. The objects to be clustered may include words, text, images, audio, video, longitudinal media data, graph nodes, or any collection of items that can be described by a set of features (Izenman, 2008). As a versatile tool, clustering has been widely employed as an intermediate step in numerous data mining and machine learning tasks. As illustrated in Figures 2, clustering is recognized as a fundamental branch of machine learning and a pivotal task in the broader field of data science.

Clustering has been applied across diverse domains, including natural sciences, social sciences, economics, education, engineering, and health science, to name a few (Dinh et al., 2025). Additionally, clustering is closely connected to other data science processes, such as regression and classification. For instance, clustering can enhance regression analysis by identifying distinct groups within data, which may then inform separate

### Data clustering: an essential technique in data science

Tai Dinh a, ⊕ , ∗ , Wong Hauchi a, ⊕ , Daniil Lisik b , Michal Koren c , Dat Tran d , Philip S. Yu e , Joaqu´ ın Torres-Sospedra f a The Kyoto College of Graduate Studies for Informatics, 7 Tanaka Monzencho, Sakyo Ward, Kyoto City, Kyoto, Japan b University of Gothenburg, Medicinaregatan 1F, 413 90, G¨ oteborg, Sweden

c Shenkar College of Engineering, Design and Art, Anne Frank St 12, Ramat Gan, Tel Aviv, Israel d University of Canberra, 11 Kirinari St, Bruce ACT 2617, Australia

e

Department of Computer Science, University of Illinois at Chicago, Chicago, USA f Department of Computer Science, University of Valencia, Valencia, Spain

*[picture on PDF page 2]*

**Figure labels:**
- Interpretation/
- Evaluation
- Data mining
- Data transformation
- Data preprocessing
- Data selection
- Target data
- Preprocessed data
- Transformed data
- Patterns
- Knowledge
- Data

rithms each of which seeks to organize a given data set into homogeneous subgroups, or clusters [63]. A cluster is generally considered as a group of objects in which each object is close to a central point of the cluster and that members of different clusters are far away from each other. In other words, those objects within each cluster are more closely related to one another than objects assigned to other different clusters. The obRegression Clustering Association Analysis Anomaly Data Science 2 provides an overview of clustering fundamentals, including a taxonomy of clustering methodologies and validation metrics. Section 3 introduces commonly used clustering algorithms, frameworks, libraries, tools, and the clustering workflow. Section 4 addresses key challenges in practical implementation. Section 5 explores various applications of clustering. Finally, Section 6 summarizes the paper and outlines potential directions for future work.

jects may be words, text, images, database records, nodes in a graph, or any collection

## 2. Basic of data clustering

in which individuals are described by a set of features or distinguishing relationships. In

### 2.1. A taxonomy of clustering methodologies

the literature, clustering algorithms fall into the group of unsupervised machine learning, 'unsupervised' because they are not guided by a priori ideas of which variables or samples belong in which clusters, and 'learning' because the machine algorithms learn Deep Learning Figure 2: Data science tasks (Kotu & Deshpande, 2018) Clustering is an unsupervised learning process that partitions a dataset D = { x 1 , x 2 , . . . , xn } where each data point xi ∈ R d , into k clusters C = { C 1 , C 2 , . . . , Ck } . The goal is to group similar data points into the same cluster while ensuring that points in di ff erent clusters are dissimilar. Formally, the clustering task can be expressed as the optimization of a clustering objective F ( C ), where:

               k [ j = 1 Cj = D , Ci ∩ Cj = ∅ for i , j (1) arg min C F ( C ) (2)

Partitional (partitioning) clustering, also known as nonhierarchical or flat clustering, partitions a dataset into a predefined number of clusters k, without constructing hierarchical structures. Figure 4 shows the general workflow of partitional clustering algorithms. The primary goal is to optimize an objective

*[picture on PDF page 2]*

**Figure labels:**
- Detection
- Recommendation
- Engines
- Time Series
- Forecasting
- Text Mining
- Feature
- Selection
- Classification

how to cluster [69]. The problem of clustering has been widely studied in data mining and machine learning literature since it can be applied to intermediate steps for other fundamental data mining problems and numerous application domains such as scientific data exploregression models for each cluster. Similarly, clustering can complement classification by identifying potential class labels or refining existing ones based on patterns in the data. By serving as both a foundational and complementary tool, clustering facilitates a deeper understanding of data, enabling more accurate predictions, targeted interventions, and e ffi cient resource allocation.

2

ration, information retrieval and text mining, web analysis, marketing, collaborative filtering, customer segmentation, data summarization, dynamic trend detection, multimedia data analysis, medical diagnostics, biological data analysis and social network This paper provides a comprehensive exploration of data clustering within the context of data science. It begins by delving into the fundamental concepts that underpin clustering, including key definitions and principles. The paper then examines various clustering methodologies, ranging from traditional techniques such as partitional and hierarchical clustering to more advanced approaches like data stream and subspace clustering. Finally, the discussion extends to the diverse applications of clustering, highlighting its impact across various fields and its potential to foster innovation. By presenting a detailed overview of these aspects, this paper aims to highlight the importance of data clustering in data science and o ff er readers a comprehensive understanding of this essential technique. Equation (1) indicates that clusters are non-overlapping and exhaustive, whereas equation (2) aims to enforce that each cluster Cj is defined such that points within the same cluster are more similar to each other (intra-cluster similarity) than those in di ff erent clusters (inter-cluster dissimilarity). Figure 3 shows a taxonomy of clustering algorithms. In what follows, we revisit some of the most commonly used types of clustering discussed in the literature.

The remainder of this paper is organized as follows: Section

*[picture on PDF page 3]*

**Figure labels:**
- Clustering
- algorithms
- Base on
- Data types
- Numerical
- data
- Categorical
- Mixed
- Multimedia
- Text
- Spatio-
- temporal
- Network
- Genome
- sequence
- Uncertain
- data char-
- acteristics
- High-
- dimensional
- clustering
- Stream
- Big data
- Static data
- Multi-view
- Dimensional
- reduction
- techniques
- Projected
- Matrix
- factorization
- Spectral
- t-SNE
- UMAP
- Techniques
- Partitional
- Hierarchical
- Density-
- based
- Model-
- Subspace
- Graph-
- GA-based
- Ensemble
- Probabilistic
- Base on data
- structure
- Structured
- Semi-
- structured
- Unstructured
- Relational
- Hybrid
- Graph

*[picture on PDF page 3]*

**Figure labels:**
- Initialize k
- Clusters Centers
- Assign Objects
- to k Clusters
- Update k
- Cluster Centers
- Check
- Convergence
- Clustering Results
- Dataset
- Yes
- No
- Hard Clustering
- Soft Clustering
- Similarity
- Measurement
- Clusters
- Initialization
- Agglomerative
- or Divisive?
- Iterative
- Dividing
- Merging
- Divisive
- Stopping
- criterion
- met?
- Figure 5: H ierarchical C lustering

function, such as minimizing intra-cluster distances or maximizing inter-cluster separation (Kaufman & Rousseeuw, 1990). Partitional clustering algorithms can be broadly categorized into hard partitional clustering and soft partitional clustering. Hard clustering, also referred to as crisp clustering, assigns each data point to exactly one non-overlapping cluster. Algorithms like K-M eans (Lloyd, 1982), K-M odes and K-P rototypes (Huang, 1998) fall under this category. In contrast, soft (or fuzzy) clustering allows data points to belong to multiple clusters simultaneously. Each point is assigned a membership value ranging

Feature Subset Selection

F1

Fз

Fm

h

from 0 (no membership) to 1 (full membership), indicating its degree of association with each cluster (Tan et al., 2019). This flexibility is particularly useful for datasets with overlapping or ambiguous boundaries.

Hierarchical clustering constructs a dendrogram to represent relationships among data points, using either an agglomerative (bottom-up) or divisive (top-down) approach (Han et al., 2022). Figure 5 shows the workflow of hierarchical clustering algorithms. In agglomerative clustering, each object initially starts as a separate cluster, and the two closest clusters are iteratively merged based on a similarity measure until only one cluster remains. Conversely, divisive clustering starts with all objects in a single cluster and recursively splits them into smaller clusters. The dendrogram illustrates the merging or splitting process, and the optimal number of clusters can be determined by cutting the dendrogram at a level that balances the number of clusters and their homogeneity.

*[picture on PDF page 4]*

**Figure labels:**
- DBSCAN
- epsilon = 1.20
- minPoints = 4
- Clustering Results
- Dataset
- Boundary
- Points
- Core
- Outlier
- 𝜖

Density-based clustering identifies clusters as dense regions of data points separated by sparser areas. Figure 6 shows the workflow of density-based clustering. Unlike partitional or hierarchical methods, it does not require specifying the number of clusters in advance. Instead, clusters are formed based on the density of points within a defined neighborhood. This approach is particularly e ff ective for discovering clusters of arbitrary shapes and handling noise in datasets. A prominent example is the DBSCAN algorithm (Ester et al., 1996), which groups points with su ffi cient density while labeling outliers as noise.

Model-based clustering is a statistical approach that assumes data is generated from a mixture of underlying probability distributions, with each distribution corresponding to a specific cluster (Fraley & Raftery, 2002). Figure 7 illustrates the workflow of a model-based clustering algorithm. This approach relies on a generative model in which clusters are represented by parametric probability distributions, such as Gaussian distributions in the widely used G aussian M ixture M odel (GMM). The

Clustering Results

*[picture on PDF page 4]*

**Figure labels:**
- Model
- Initialization
- Check
- Convergence
- Clustering Results
- Dataset
- Expectation
- Step
- Maximization
- Assign Data
- Instances into
- Clusters
- Yes
- No

method requires specifying distributional assumptions, as these directly influence the clustering outcome by defining the shape, size, and overlap of clusters. The clustering process involves estimating the parameters of these distributions and assigning data points to the cluster that maximizes their likelihood. By leveraging statistical principles, model-based clustering can effectively capture complex data structures, determine the optimal number of clusters using model selection criteria (e.g., Bayesian Information Criterion (BIC) or Akaike Information Criterion (AIC)), and handle overlapping clusters. However, the validity of the results depends on whether the chosen distributional assumptions align with the true underlying data characteristics.

*[picture on PDF page 4]*

**Figure labels:**
- Clustering Results
- Dataset
- Sub Clustering
- 𝒦
- Clustering 1
- Fusion All
- Clustering
- Feature Subset Selection
- ℱ௠
- …
- ℱଷ
- ℱଶ
- ℱଵ
- h
- t
- 1
- a
- u
- b
- v
- f
- 0
- g
- Sub Clustering 2
- Sub Clustering 1
- Clustering 2
- Final

Subspace clustering focuses on identifying clusters within specific subspaces of a high-dimensional dataset, rather than the full-dimensional space Parsons et al. (2004). Figure 8 shows the workflow of subspace clustering. The key idea is that meaningful clusters may exist in subsets of dimensions where data points share strong similarities, while other dimensions may in-

troduce noise. By searching for clusters in these relevant subspaces, this approach is particularly e ff ective for high dimensional data where traditional methods often struggle. Subspace clustering has proven valuable in domains such as bioinformatics and text analysis, where data often exhibit localized patterns in specific subsets of features.

*[picture on PDF page 5]*

**Figure labels:**
- Graph
- Constructio
- n Option
- Clustering Results
- Dataset
- Transform each
- data object into
- a graph node
- =
- 𝜔ଵ
- 𝜔ଶ
- 𝜔ଷ
- 𝜔ସ
- 𝜔ହ
- 𝜔଺
- 𝜔଻
- 𝜔଼
- 𝜔୩
- …
- Graph Embedding
- 𝑥ଵ
- 𝑥ଶ
- 𝑥ଷ
- 𝑥୬
- Numerical
- Clustering
- Final

Graph-based clustering represents data as a graph, where nodes correspond to data points and weighted edges reflect the similarity between them (Maier et al., 2008). Figure 9 shows the workflow of graph-based clustering. Clusters are formed as densely connected subgraphs, with sparse or minimal connections to nodes outside the cluster. The goal of graph-based clustering algorithms is to partition the graph by analyzing its edge structure, typically maximizing the total weight or number of edges within clusters while minimizing inter-cluster connections. This approach is particularly e ff ective for identifying non-convex clusters and handling complex data structures.

*[picture on PDF page 5]*

**Figure labels:**
- Cluster new
- dataset based
- on the last
- cluster model
- Perform Initial
- Clustering
- End
- Results
- Dataset Batch
- 𝐷ଵ
- Sliding Window
- 𝐷௞
- 𝐷ே
- …
- Data Stream
- Initial Cluster
- Presentation
- and Model
- Concept
- Drift?
- Recluster last
- and current
- batches
- New Cluster
- Start
- Input
- For reference
- No
- Yes
- Final Cluster
- Update

Data stream clustering dynamically groups similar data points in real-time as they flow continuously into a system Silva et al. (2013). Designed to handle high-velocity, large-volume, and unbounded data streams, it incrementally updates clusters to ensure e ffi cient and adaptive processing. The general framework of data stream clustering, illustrated in Figure 10, comprises several key steps. It begins with clustering the initial batch of data to establish a baseline configuration. A sliding window model is then employed to focus on the most recent data, ensuring that older, less relevant points are discarded. Clusters are represented through statistical summaries, such as centers or spreads, which are continuously updated to reflect new data. As new points arrive, they are incrementally assigned to existing clusters or used to form new ones, depending on their similarity. The framework also incorporates mechanisms to detect and respond to concept drift, adjusting the clustering model to accommodate shifts in the data distribution. Periodic maintenance is performed to refine clusters, which may involve merging, splitting, or repositioning them as needed. This iterative process ensures that the clustering remains adaptive, providing an up-to-date representation of the evolving data stream for downstream analysis.

*[picture on PDF page 5]*

**Figure labels:**
- Generate Clusters
- Assess Clusters
- Select Clusters
- Combine Clusters
- Alter Clusters
- Update Clusters
- Check
- Convergence
- Clustering Results
- Dataset
- Yes
- No

*[picture on PDF page 5]*

**Figure labels:**
- Base Clustering 1
- Consensus
- Function
- Clustering Results
- Dataset
- Base Clustering 2
- Base Clustering g
- Base Clustering M

Genetic algorithm (GA)-based clustering (Maulik & Bandyopadhyay, 2000) utilizes genetic algorithms (GAs) to improve

*[picture on PDF page 6]*

**Figure labels:**
- Internal
- metrics
- Silhouette Score
- Davies-Bouldin Index
- Dunn Index
- Xie-Beni Index
- Intra-Cluster Distance
- Inter-Cluster Distance
- Cluster Discrimination
- External
- Accuracy
- Precision
- Recall
- Entropy
- Rand Index
- F-Score (F-Measure)
- Mutual Information
- Jaccard Index
- Homogeneity
- Purity
- Adjusted Rand Index (ARI)
- Normalized Mutual Information (NMI)
- Normalized Variation of Information
- Fowlkes-Mallows Index
- Minkowski Score
- Computational
- Runtime
- Memory usage
- Scalability

clustering performance. GAs are search heuristics inspired by the process of natural selection, operating on a population of potential solutions and evolving them through selection, crossover, and mutation (Holland, 1992). Figure 11 shows the framework of GA-based clustering. In clustering, each potential solution (or chromosome) represents a partitioning of the dataset into clusters, where each cluster contains a subset of data points. By iteratively optimizing cluster assignments through evolutionary processes, GA-based methods o ff er robust solutions and reduce the risk of being trapped in local optima.

Ensemble clustering combines multiple clustering outputseither from di ff erent algorithms, multiple independent executions of the same algorithm (e.g., with varying initializations), or runs on subsets of the data-to produce a single consensus partition of the original dataset (Strehl & Ghosh, 2002). The workflow of ensemble clustering is illustrated in Figure 12. A typical ensemble framework consists of two main steps: (1) generating a set of base clustering results and (2) integrating these results into a final consensus clustering using a consensus function. Both the quality of the base clusterings and the e ff ectiveness of the consensus function play a critical role in determining the success of the ensemble. Additionally, a sensible combination of algorithms should be chosen, as di ff erent clustering algorithms operate under varying assumptions about the data and have distinct goals or definitions of optimal performance.

### 2.2. Clustering validation metrics

Figure 13 illustrates common metrics for assessing the performance of clustering algorithms. Internal validation metrics assess the quality of clustering algorithms by evaluating their performance based solely on the data used for clustering, without external references. External validation metrics, on the other hand, compare clustering results to an external ground truth or reference standard. In addition to quality-based metrics, the computational performance of clustering algorithms is also a critical consideration. R untime measures the time required for an algorithm to process the input dataset and produce outputs. Alower runtime indicates better computational e ffi ciency. S cal -ability assesses how the performance of clustering algorithms changes with varying dataset sizes. Good scalability implies that an algorithm maintains consistent performance across different data volumes. M emory usage quantifies the amount of memory required to execute a specific algorithm. Lower memory usage indicates better resource e ffi ciency. While lower runtime and memory usage generally indicate a more e ffi cient clustering algorithm in terms of computational complexity, these metrics should be balanced against the quality of clustering results, as assessed by internal and external validation metrics.

## 3. Data clustering algorithms

### 3.1. Popular clustering algorithms

*[picture on PDF page 6]*

**Figure labels:**
- DBSCAN
- Affinity Propagation
- Clustering

*[picture on PDF page 7]*

**Figure labels:**
- 1957
- K-M
- eans
- (Lloyd, 1982)
- 1963
- W
- ard
- L
- inkage
- HAC (Ward Jr, 1963)
- 1967
- (MacQueen et al., 1967)
- 1973
- S
- ingle
- HAC (Sibson, 1973)
- 1977
- C
- omplete
- HAC (Defays, 1977)
- 1979
- (Hartigan et al., 1979)
- 1982
- SOM
- s
- (Kohonen, 1982)
- 1984
- F
- uzzy
- C-M
- (Bezdek et al., 1984)
- 1990
- PAM (Kaufman & Rousseeuw, 1990)
- 1995
- M
- ean
- hift
- (Cheng, 1995)
- 1996
- DBSCAN (Ester et al., 1996)
- BIRCH (Zhang et al., 1996)
- 1997
- odes
- (Huang, 1997)
- 1998
- K-P
- rototypes
- (Huang, 1998)
- CLIQUE (Agrawal et al., 1998)
- MC
- lust
- (Fraley & Raftery, 1998)
- 1999
- (Huang & Ng, 1999)
- G
- enetic
- (Krishna & Murty, 1999)
- OPTICS (Ankerst et al., 1999)
- 2000
- R
- ock
- (Guha et al., 2000)
- 2001
- pectral
- lustering
- (Ng et al., 2001)
- 2002
- luster
- E
- nsemble
- (Strehl & Ghosh, 2002)
- 2003
- LDA (Blei et al., 2003)
- lu
- tream
- (Aggarwal et al., 2003)
- 2007
- A
- ffinity
- P
- ropagation
- (Frey & Dueck, 2007)
- 2008
- ouvain
- (Blondel et al., 2008)
- T-SNE (Van der Maaten & Hinton, 2008)
- 2017
- HDBSCAN (McInnes et al., 2017)
- 2018
- UMAP (McInnes et al., 2018)
- Hard partitional
- Fuzzy partitional
- Hierarchical
- Density-based
- Data stream
- Genetic Algorithm (GA)-based
- Subspace
- Ensemble
- Graph-based
- Model-based
- Dimensionality reduction

In machine learning, many clustering algorithms as shown in Figure 14 have been developed to approach existing problems users face from di ff erent perspectives. These algorithms vary in their methodologies, assumptions, and the data types they handle most e ff ectively. Some focus on minimizing distances between data points, while others prioritize density or hierarchical relationships. As data science continues to evolve, more and more algorithms have become integral tools in fields ranging from market segmentation to anomaly detection.

Figure 15 illustrates the progression of clustering algorithms over time. The figure highlights algorithms that are widely recognized and commonly utilized within the research community. In the subsequent sections, we will introduce some of the most prominent clustering algorithms, emphasizing their key features and applications.

K-M eans (Lloyd, 1982) is a popular algorithm of partitioning methods used for clustering data into groups based on similarity. Lloyd's algorithm (Algorithm 5) is the most common implementation of K-M eans . It begins by initializing k cluster centroids, which are typically chosen randomly. Each data point is then assigned to the nearest centroid based on a distance metric, usually E uclidean distance , forming k clusters. Once the assignments are made, the centroids are updated by calculating the mean position of all points in each cluster. These steps of assignment and update are repeated iteratively until the centroids stabilize or a stopping criterion is met, such as a maximum number of iterations or minimal movement of centroids.

MacQueen et al. (1967) provides another variant of K-M eans

#### Algorithm 1: Lloyd's K-M eans (Lloyd, 1982)

- 1 Initialize by randomly assigning each data point to one of the k clusters

