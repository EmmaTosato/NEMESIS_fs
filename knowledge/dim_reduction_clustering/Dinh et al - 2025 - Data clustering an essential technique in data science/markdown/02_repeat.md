## 2 repeat

- 3 Find the smallest dissimilarity in D , say dIJ , between two clusters I and J
- 4 Merge clusters I and J into a new cluster IJ
- 5 Compute new distances from cluster IJ to any other cluster K :
- Single linkage: dIJ , K = min( dIK , dJK ),
- Complete linkage: dIJ , K = max( dIK , dJK ),
- Average linkage: dIJ , K = P i ∈ I ∪ J P k ∈ K dik NIJ · NK .

Update the dissimilarity matrix M by:

- Remove rows and columns corresponding to clusters and J ,
- Add a row and column for the new cluster IJ ,
- Fill in the new distances dIJ , K for the updated matrix.

Record the merge and its distance

- 6 until only one cluster remains
- 7 Output: Dendrogram representing the merge sequence.

I

### Algorithm 5: P artitioning A round M edoids (PAM)

Input: D = { x 1 , x 2 , . . . , xn } is the set of data points, k is the number of medoids.

- 1 Build phase:
- 2 Greedily select k points from D as the medoids to minimize the cost.
- 3 Assign each xi ∈ D to the closest medoid.
- 4 Swap phase:
- while the cost of the current configuration decreases do

5 6 foreach medoid m do 7 foreach non-medoid o do 8 Compute the cost change ∆ for swapping m and o . 9 if ∆ is the best cost change so far then 10 Store m best ← m and o best ← o 11 end 12 end 13 end 14 if a swap mbest and obest reduces the cost then 15 Perform the swap of m best and o best . 16 end 17 else 18 break // Stop if no swap reduces the cost. 19 end 20 end

### Algorithm 6: Abstract DBSCAN (Schubert et al., 2017)

diagram that represents the nested grouping of data points and the distances between clusters. The dendrogram can be cut at a chosen level to define the desired clusters. The merging of clusters is determined by a linkage criterion, which specifies how the distance between clusters is calculated. Common linkage methods include S ingle L inkage (Sibson, 1973), which uses the shortest distance between any two points in di ff erent clusters, often resulting in elongated or chain-like clusters; C om -plete L inkage (Defays, 1977), which considers the farthest distance between points, producing more compact and spherical clusters; and A verage L inkage , which calculates the average distance between all pairs of points across clusters and o ff ers a balance between the two extremes. W ard L inkage (Ward Jr, 1963) minimizes the total within-cluster variance by reducing the sum of squared di ff erences across all clusters. This variance minimizing approach is conceptually similar to the K-M eans objective but is implemented through an agglomerative hierarchical strategy. HAC is widely applied in bioinformatics, social network analysis, and text mining to uncover hierarchical relationships in complex datasets.

1 Compute neighbors of each point and identify core points // Identify core points 2 Join neighboring core points into clusters // Assign core points 3 forall non-core point do 4 if can add to a neighboring core point then 5 Add to the core point // Assign border points 6 end 7 else 8 Add to noise // Assign noise points 9 end 10 end

Density-Based Spatial Clustering of Applications with Noise (DBSCAN) (Ester et al., 1996) identifies clusters as contiguous regions of high point density, separated by areas of lower density. Algorithm 10 shows the main steps of DBSCAN. The algorithm requires two parameters, epsilon ( ϵ ), which defines the radius of the neighborhood around a data point, and minPts , the minimum number of points required to form a dense region.

Data points are classified into three categories: core points , which have at least minPts neighbors within their ϵ radius; border points , which lie within the ϵ neighborhood of a core point but do not meet the minPts threshold themselves; and noise points , which are not part of any cluster. Clusters are formed by linking core points and their reachable neighbors iteratively, allowing the algorithm to discover clusters of arbitrary shapes. DBSCANdoes not require a pre-defined number of clusters and is robust to noise and outliers. However, its performance depends on the careful selection of ϵ and minPts , as these parameters influence the sensitivity to cluster density and the detection of meaningful patterns in the data.

The G enetic K-M eans algorithm (Krishna & Murty, 1999) extends the traditional K-M eans by integrating genetic operators to improve clustering performance. K-M eans is e ffi cient but often sensitive to initial centroid placement and prone to getting stuck in local minima. G enetic K-M eans addresses these limitations by using genetic operations like selection, crossover, and mutation to search for better cluster configurations. The algorithm begins with an initial population of solutions, where each solution represents a set of centroids. The fitness of each solution is evaluated by minimizing intra-cluster variance (sum of squared distances within clusters). The best solutions are selected for reproduction, and genetic operators generate new solutions, enabling a global search for optimal centroids. Over multiple generations, the algorithm evolves toward a configuration that minimizes clustering errors. This global search capability makes G enetic K-M eans more robust, especially for complex datasets with noise, outliers, or irregular cluster shapes.

C lustering in QUE st (CLIQUE) (Agrawal et al., 1998) is a subspace clustering algorithm designed for high-dimensional data. It partitions the data space into a grid of cells and identifies clusters by analyzing cell density. Regions with densities above a minimum threshold are considered potential clusters. The algorithm operates in two main stages: first, it identifies dense regions by examining the density of grid cells. Second, it selects dense subspaces containing significant data points. Unlike traditional methods, CLIQUE clusters data in subspaces rather than the full space, making it ideal for high-dimensional datasets. CLIQUE can detect clusters of arbitrary shapes without requiring prior knowledge of the number of clusters. Its scalability and e ffi ciency make it well-suited for large, complex datasets. It should be noted that CLIQUE allows overlapping clustering by identifying clusters independently in various subspaces, permitting a data point to belong to multiple clusters. In contrast, projected clustering (Aggarwal et al., 1999) generates disjoint clusters, assigning each data point to a single cluster within its relevant subspace, resulting in simpler, nonoverlapping structures.

C lu S tream (Aggarwal et al., 2003) is a data stream clustering algorithm designed for large, dynamic, and time-varying data. It operates in two phases: first, it incrementally maintains micro-clusters, which compactly capture local patterns in real time as new data points arrive. Second, it periodically performs macro-clustering by aggregating these micro-clusters to reveal global structures and trends. The algorithm dynamically adapts by merging, splitting, and updating clusters, making it suitable for evolving data streams. Its computational e ffi ciency and low memory usage make C lu S tream e ff ective for large-scale, realtime clustering applications.

C luster E nsembles (Strehl & Ghosh, 2002) is a pioneering work in ensemble clustering, formally defining the problem and proposing three consensus functions: CSPA (C luster -based S imilarity P artitioning A lgorithm ), HGPA (H yper G raph P artitioning A lgorithm ), and MCLA (M eta -CL ustering A l -gorithm ). Unlike earlier studies in phylogenetics and data fusion that explored combining multiple clusterings, this work introduced a mutual information-based optimization framework and methods that enable knowledge reuse without requiring ac- cess to original features. The approach generates diverse clustering solutions by employing di ff erent algorithms or multiple runs of the same algorithm with varying random initializations (e.g., di ff erent starting points for k-means). This diversity enhances the stability and improves the quality of the final clustering, particularly in distributed and noisy data scenarios, making it e ff ective for data with complex patterns or uncertain structures.

MC lust (Fraley & Raftery, 1998) is an R library that implements G aussian M ixture M odels (GMM) for probabilistic and flexible clustering. It assumes data arises from a mixture of Gaussian distributions, with each cluster defined by parameters such as a mean vector, covariance matrix, and mixing coe ffi cient. Using the E xpectation -M aximization (EM) algorithm, MC lust iteratively calculates cluster membership probabilities and updates Gaussian parameters to maximize data likelihood. Its flexibility stems from the ability to capture diverse shapes and densities via covariance matrices, making it suitable for complex datasets. Additionally, MC lust automatically selects the optimal number of clusters using the Bayesian Information Criterion (BIC), enhancing its adaptability and robustness.

L ouvain C lustering (Blondel et al., 2008) is a graph-based network community detection method that optimizes modularity, a measure of the density of edges within communities compared to those between them. The algorithm operates in two phases. First, it assigns nodes to communities by iteratively maximizing modularity gains through node movement. Next, these communities are aggregated into super-nodes, and the process is repeated hierarchically. This multi-level approach enables L ouvain C lustering to e ffi ciently detect communities at di ff erent scales, making it highly scalable and e ff ective for analyzing large, complex networks.

U niform M anifold A pproximation and P rojection (UMAP) (McInnes et al., 2018) is a dimensionality reduction technique that excels at preserving the local and global structure of highdimensional data in a lower-dimensional space. It operates by constructing a high-dimensional graph of data points and optimizing its low-dimensional embedding to maintain the graph's topological properties. This capability makes UMAP an e ff ective preprocessing step for clustering, as it enhances the separation of data clusters by revealing inherent patterns and groupings. Its scalability and flexibility enable UMAP to handle large and complex datasets, making it a popular choice for clustering tasks in fields such as genomics, image analysis, and natural language processing. Recently, Sun et al. (2024) proposed R ic -ci N et , a deep clustering model based on a Riemannian Generative Model. Like UMAP, this approach leverages Riemannian space instead of the traditional Euclidean space, demonstrating improvements in clustering performance.

### 3.2. Libraries, Tools, and Frameworks

P ython has become the most used language on GitHub 2 , overtaking JavaScript after a 10-year run as the most used lan-

> 2

> https://github.blog/news-insights/octoverse/ octoverse-2024/#the-most-popular-programming-languages

*[picture on PDF page 11]*

**Figure labels:**
- Scikit-learn
- :
- offers
- robust
- clustering
- algorithms
- like
- k-
- means,  DBSCAN,  and  hierarchical  clustering  with  easy-to-
- use interfaces.
- NumPy
- provides
- foundational
- numerical
- operations
- for
- implementing
- custom
- clustering algorithms.
- Pandas
- :  facilitates  data  manipulation
- and preprocessing before clustering.
- SciPy
- includes
- hierarchical
- and distance computation functions.
- Seaborn
- :  visualizes  clustering  results
- effectively with clustermap, heatmaps.
- R
- : provides diverse clustering packages (e.g., cluster,
- factoextra) for statistical clustering and visualization.
- TensorFlow
- :  enables  deep  clustering  methods
- with custom neural network-based models.
- MATLAB
- :  offers built-in clustering including k-
- means
- and
- Gaussian
- mixture
- models,
- with
- advanced visualization.
- Orange
- :  features  an  intuitive  GUI  for
- clustering workflows and visual analysis.
- Tableau
- :  enables  clustering
- visualizations directly within
- dashboards using k-means.
- Power BI
- :  provides  automated
- clustering and grouping features
- for visual insights.
- Weka
- : offers a wide range of clustering
- algorithms like k-means and EM with GUI
- support.
- RapidMiner
- :  integrates  clustering  algorithms  into  an
- end-to-end data science workflow environment.
- Clustering Tools
- and Frameworks

guage. In P ython , clustering is e ff ortless with S cikit -learn 3 , a versatile and user-friendly machine learning library. It provides e ffi cient implementations of popular clustering algorithms like K-M eans , DBSCAN, HDBSCAN, H ierarchical C lustering , M ean S hift , and S pectral C lustering , making it a go-to choice for data scientists and engineers. With its intuitive API and seamless integration with libraries such as N um P y 4 and P an -das 5 , S cikit -learn is a good choice for prototyping and experimenting with di ff erent clustering tasks. For instance, performing K-M eans clustering can be achieved with just a few lines of code, typically involving steps like data preprocessing, model fitting, and result visualization.

R 6 is a statistical programming language renowned for its strength in exploratory data analysis and visualization. Libraries like cluster 7 and factoextra 8 provide robust tools for implementing clustering techniques, including K-M eans , with an emphasis on visually interpreting cluster distributions. Its capabilities make R a preferred choice for academic research and projects requiring statistical rigor and insightful presentation.

MATLAB is a high-level language designed for numerical computation and visualization, o ff ering built-in functions for clustering 9 such as K-M eans , H ierarchical C lustering , KM edoids , DBSCAN, S pectral C lustering , G aussian M ixture M odels and A ffinity P ropagation C lustering . Widely used in academia and industries like engineering and finance, MATLAB enables precise modeling and insightful visualizations. For instance, its hierarchical clustering tools allow users to visualize cluster relationships with dendrograms, providing an intuitive way to explore data structure.

O range D ata M ining 10 is an open-source platform for data

> 3 https://scikit-learn.org/1.5/modules/clustering.html

> 4 https://numpy.org/

> 5 https://pandas.pydata.org/

> 6 https://www.r-project.org/

> 7 https://cran.r-project.org/web/packages/cluster/index. html

> 8 https://cran.r-project.org/web/packages/factoextra/ index.html

> 9 https://www.mathworks.com/help/stats/cluster-analysis. html?s_tid=CRUX_lftnav

> 10 https://orangedatamining.com/

visualization and analysis, o ff ering widges, drag-and-drop interface for tasks like preprocessing, clustering, and classification. It supports clustering methods such as K-M eans , H ierar -chical C lustering , DBSCAN, and N etwork C lustering , with tools for parameter tuning, cluster visualization, and quality assessment. Advanced visualizations like dendrograms and scatter plots make it easy to explore and interpret cluster assignments. Its integration with P ython scripting and add-ons further extends its versatility for machine learning and statistical analysis.

T ableau 11 leverages clustering to identify patterns and group similar data points within visualizations. With its built-in KM eans clustering, users can segment data directly in dashboards, enabling deeper insights into customer behavior, market trends, or performance metrics without requiring extensive coding.

P ower BI 12 includes clustering as part of its data analytics features, using algorithms like K-M eans and E xpectation M aximization to uncover hidden patterns in datasets. Clustering helps users segment data dynamically within reports and dashboards, making it ideal for tasks like customer segmentation, sales analysis, and anomaly detection.

W eka 13 provides an accessible platform for clustering through its extensive machine learning library, supporting methods like K-M eans , DBSCAN, H ierarchical C lustering and EM. Users can apply clustering to explore and analyze data patterns, often as a preprocessing step for further classification or prediction tasks.

R apid M iner 14 o ff ers clustering tools for tasks like market segmentation and outlier detection. With support for various techniques such as K-M eans and H ierarchical C lustering , DBSCAN, and K-M edoids , users can combine clustering workflows with advanced machine learning models for end-to-end data analysis.

> 11 https://help.tableau.com/current/pro/desktop/en-us/ clustering.htm#how-clustering-works

> 12 https://learn.microsoft.com/en-us/analysis-services/ data-mining/microsoft-clustering-algorithm?view= asallproducts-allversions

> 13 https://www.tutorialspoint.com/weka/weka_clustering.htm

> 14 https://docs.rapidminer.com/latest/studio/operators/ index.html

• Visualization

Statistical Summaries

Correlation Analysis

Busin dly Radartin

• Outlier Detection.

diu visudl summaries.

*[picture on PDF page 12]*

**Figure labels:**
- Clustering
- Workflow
- Exploratory Data Analysis
- Understand the data
- structure, detect
- anomalies, and gain
- insights to inform
- preprocessing and
- analysis.
- Key data insights
- and visual
- summaries.
- Data Preprocessing
- Prepare the dataset by
- handling missing
- values, outliers, and
- scaling to ensure
- reliable clustering.
- Cleaned and
- prepared dataset.
- Algorithm Selection
- Choose the most
- suitable clustering
- method based on data
- characteristics and
- analysis goals.
- Best-suited
- clustering algorithm.
- Optimization
- Fine-tune clustering
- parameters to improve
- accuracy, and
- meaningfulness of the
- results.
- Tuned model with
- optimal parameters.
- Evaluation
- Assess the quality,
- stability of the
- clustering to ensure
- valid, and robust
- groupings.
- Validated and
- robust clustering.
- Interpretation
- Analyze, and explain
- the clusters'
- characteristics to
- derive actionable
- insights, and
- meaningful
- conclusions.
- Cluster
- insights.
- Figure 17: A general workflow of clustering tasks
- •
- Visualization
- Dimensionality Reduction
- Statistical Summaries
- Correlation Analysis
- Outlier Detection.
- Normalization/Stand
- ardization
- Missing Value
- Imputation
- Dimensionality
- Reduction
- Feature Engineering
- Outlier Removal.
- Silhouette Score
- Davies-Bouldin Index
- Dunn Index
- Cluster Purity
- Adjusted Rand
- Index.
- Cluster Profiling
- Centroid Visualization
- Feature Importance
- Heatmaps
- Domain Insights.
- Model Optimization
- K-Means
- DBSCAN
- Hierarchical
- Gaussian Mixture
- Models
- Spectral Clustering.
- Elbow Method
- Silhouette Analysis
- Grid Search
- Cross-Validation for
- Clustering Stability
- Tuning.
- • Dimensionality
- • Feature Engineering
- • Outlier Removal.
- • Elbow Method
- • Silhouette Analysis
- • Cluster Profiling
- • Domain Insights.

### 3.3. Clustering workflow in data science

Figure 17 illustrates the overall workflow of the clustering process, while Figure 18 highlights various options available for each step in the workflow. The first step, E xploratory

D ata A nalysis (EDA), involves examining the dataset to understand its structure and distribution. During this phase, patterns, anomalies, and outliers are detected, and key insights are derived using visualization and statistical techniques. These in-

sights provide valuable context and help inform the subsequent steps of the process.

Following EDA, D ata P reprocessing ensures the dataset is prepared for clustering by addressing issues such as missing values, outliers, and di ff ering scales. Techniques like standardization or normalization, for instance, can help to align feature scales, while handling inconsistencies improves data quality. However, the specific preprocessing steps required depend on the nature of the dataset and the clustering algorithm being used. Proper preprocessing is essential to minimize the risk of biased or unreliable results.

The third step, A lgorithm S election , focuses on identifying the most appropriate clustering method based on the dataset characteristics and the analysis goals. Depending on data complexity, cluster shapes / characteristics, and computational requirements, algorithms like K-M eans , DBSCAN, or hierarchical clustering may be chosen. The choice of algorithm lays the foundation for producing meaningful groupings.

After selecting an algorithm, O ptimization is performed to fine-tune parameters, such as the number of clusters or distance metrics. Adjustments at this stage enhance the clustering's accuracy and ensure that the results are both precise and interpretable. Fine-tuning the model makes the clusters more relevant to the underlying data structure.

In the E valuation phase, the quality and stability of the clusters are assessed using metrics such as silhouette score, Dunn index, or cohesion and separation measures. This ensures that the groupings are valid, robust, and aligned with the intended analysis goals. Evaluation is critical for verifying the clustering's reliability and significance.

Finally, the I nterpretation step involves analyzing the characteristics of each cluster to derive actionable insights. By understanding the unique attributes and patterns within each group, meaningful conclusions can be drawn, aiding decision-making or further research. This step transforms raw data clusters into comprehensible and valuable insights.

Altogether, this workflow ensures a systematic approach to clustering, moving from raw data exploration to actionable insights with clarity and rigor.

## 4. Challenges in practical implementation

### 4.1. Data-related challenges

Clustering high-dimensional data is challenging due to the curse of dimensionality , where distances lose interpretability, making distance-based methods less e ff ective (Peng et al., 2023). Dimensionality reduction techniques such as Principal Component Analysis (PCA), t-distributed Stochastic Neighbor Embedding (t-SNE), and UMAP help capture key features, while alternative methods like S ubspace C lustering , such as CLIQUE, perform better in high dimensions.

Clustering large-scale datasets is computationally intensive. Algorithms like H ierarchical C lustering scale poorly, while M ini -B atch K-M eans 15 , which processes small random subsets,

> 15 https://scikit-learn.org/stable/modules/generated/ sklearn.cluster.MiniBatchKMeans.html

and distributed frameworks like A pache S park address scalability by enabling parallel computing. Preprocessing steps, such as dimensionality reduction, further helps managing data size.

Noise and outliers distort cluster assignments, particularly in K-M eans , where centroids are shifted (Iam-On, 2020). Algorithms like DBSCAN handle noise better by marking outliers, though their performance depends heavily on parameter tuning, especially with varying cluster densities. Preprocessing with outlier detection techniques, such as Isolation Forest 16 , helps remove outliers before clustering.

Missing data disrupts clustering by a ff ecting distance calculations. Multiple imputation techniques, which account for uncertainty by generating multiple plausible datasets, are generally preferred for addressing this issue. Simpler imputation methods, such as replacing missing values with the mean or median, may be used in less critical scenarios but risk introducing bias. In cases of excessive missing data, removing features or records might be unavoidable, or clustering methods that can handle missing data directly can be applied (Dinh et al., 2021).

### 4.2. Algorithms-related challenges

Algorithm selection is crucial, as di ff erent clustering methods excel under specific conditions. For instance, K-M eans is e ff ective for spherical clusters but struggles with varying densities or irregular shapes, while DBSCAN handles arbitrary shapes and noise but depends heavily on parameter tuning. H ierarchi -cal C lustering o ff ers detailed, dendrogram-based insights but is computationally expensive for large datasets. Visualization techniques, such as t-SNE or UMAP, can aid in exploring the data structure. Comparing algorithms using metrics like the S il -houette score or D avies -B ouldin index can guide the selection of the most suitable method for achieving meaningful clustering results tailored to the analysis goals.

Algorithm settings also play a vital role, as clustering outcomes are sensitive to hyperparameters. K-M eans requires specifying the number of clusters ( k ), DBSCAN relies on ϵ (distance threshold) and minPts (minimum points per cluster), and H ier -archical C lustering depends on linkage criteria. Optimal tuning of these settings often involves methods like E lbow plots, S ilhouette analysis (Dinh et al., 2019), or advanced techniques such as grid search and Bayesian optimization, supported by domain expertise for improved results.

## 5. Applications of data clustering in data science

Clustering plays an important role across diverse domains in data science, enabling insightful analysis and e ffi cient solutions. Figure 19 illustrates potential applications of clustering in data science, which are discussed in detail below.

In E xplainable AI, clustering reveals underlying patterns in data, making complex models more interpretable and enhancing transparency in decision-making processes (AlvarezGarcia et al., 2024). In B ig D ata A nalysis , clustering organizes

> 16 https://scikit-learn.org/1.5/modules/generated/ sklearn.ensemble.IsolationForest.html

kesearch

Mining

Learning

Learniny

Visualization

Al

Analysis

Video Analysi lodels (LLM

Analytics

Analysis

Data Analys!:

Analytics

Big Data

Analysis

Analytics

Learning

Management

Diodilalysis

Systems

0.6

•Dò

Doll

AAA

*[picture on PDF page 14]*

**Figure labels:**
- Explainable
- AI
- Big Data
- Reinforcement
- Learning
- Data
- Visualization
- Management
- Large
- Language
- Models (LLMs)
- Market
- Analysis
- Image
- Mining
- Time Series
- Predictive
- Analytics
- NLP / Text
- Machine
- Audio,
- Video Analysis
- Deep
- Bioanalysis
- Generative
- Exploratory
- Data Analysis
- Recommender
- Systems
- Qualitative
- Research
- X C2

massive and unstructured datasets into manageable groups, facilitating anomaly detection, customer segmentation, and pattern discovery, which are essential for industries like finance, healthcare, and social media (Nasraoui & N'Cir, 2019). R ec -ommender S ystems leverage clustering to group users or items based on behavioral similarities, enabling personalized recommendations that improve user engagement and system performance (Gasparetti et al., 2021). Similarly, in R einforcement L earning , clustering simplifies complex environments by grouping states or actions with similar outcomes, reducing dimensionality and expediting optimal policy learning (Chang et al., 2024).

*[picture on PDF page 14]*

**Figure labels:**
- 0
- -0.1
- 0.1
- Elu 120
- -0.4
- -0.2
- 0.2
- 0.4
- -0.3
- 0.3
- 0.5
- diau g
- (a) Scatter plot of the original data
- -0.6
- 0.6
- C1
- C2
- C3
- (b) Scatter plot of clustering results

Clustering is integral to E xploratory D ata A nalysis (EDA), as it identifies hidden structures and relationships, such as customer segments or patient subgroups, providing a foundation for further analysis (Tukey et al., 1977). For D ata V isual -ization , clustering organizes high-dimensional data into interpretable groups, aiding techniques like t-SNE and UMAP to highlight patterns and simplify analysis. Tools such as dendrograms, scatterplots, and heatmaps often accompany clustering methods to provide intuitive representations, allowing users to gain insights and guide further analysis or decision-making (Waskom, 2021). Figure 20 illustrates how K-M eans performs clustering to segment a biological dataset named Brown dataset 17 into three clusters. Figure 21 illustrates the use of H ierarchical C lustering with Ward's linkage and normalized Euclidean distance to organize the nutrition food dataset 18 into a hierarchical structure.

> 17 https://datasets.biolab.si/core/brown-selected.tab

> 18

> https://www.kaggle.com/datasets/cid007/ food-and-vegetable-nutrition-dataset

In G enerative AI, clustering enhances e ffi ciency by segmenting datasets into meaningful subsets, improving model outputs such as realistic image generation or coherent text generation. Clustering also optimizes D ata M anagement by grouping similar records for better retrieval, deduplication, and quality assurance, especially in large-scale databases (Garc´ ıa-Saiz et al., 2017).

In D ata A nalytics , clustering enables actionable insights by segmenting datasets into homogeneous groups, aiding in targeted marketing, customer retention strategies, and behavioral analysis (Reutterer & Dan, 2021). L arge L anguage M odels (LLM) benefit from clustering, which organizes text data into semantically similar groups, aiding in model fine-tuning, contextual understanding, summarization, and mitigating hallucinations in LLMs (He & Li, 2024). For M arket A nalysis , clustering identifies distinct customer segments and market trends, empowering businesses to design personalized campaigns, optimize pricing strategies, and understand competitor dynamics (M¨ uller & Hamm, 2014).

Clustering is a core technique in D ata M ining , uncovering hidden patterns in data for anomaly detection, trend analysis, and knowledge discovery across diverse fields (Berkhin, 2006). In I mage A nalysis , clustering groups similar pixels or features, enabling tasks like image segmentation, object recognition, and medical diagnostics. Recent advancements in LLMs have transformed image-based clustering by enabling feature extraction through embeddings. These embeddings represent high-dimensional image features in a compact vector format, capturing semantic relationships e ff ectively (Huang et al., 2024). Once features are extracted, traditional clustering techniques like K-M eans or DBSCAN are applied in the embedding space to group similar images (Khan et al., 2025). T ime S eries A nal -ysis employs clustering to group similar temporal patterns, aiding in forecasting, anomaly detection, and understanding trends in domains like finance, retail, energy, and engineering (Aghabozorgi et al., 2015; Inoue et al., 2024). P redictive A nalytics uses clustering to create meaningful data groups, enhancing targeted predictions in areas like healthcare, where it supports patient outcome predictions (Ganapathy et al., 2024), and in customer analytics for churn prediction (Rajamohamed & Manokaran, 2018).

In N atural L anguage P rocessing (NLP), clustering identifies themes, topics, and semantic relationships by grouping similar words, sentences, or documents, thereby streamlining

0.21

-0.2

-0.4

-0.6

*[picture on PDF page 15]*

**Figure labels:**
- Apple
- Pear
- Potato
- Sweet Corn
- Plums
- Nectarine
- Peach
- Banana
- Watermelon
- Grapes
- Sweet Cherries
- Sweet Potato
- Cantaloupe
- Carrot
- Leaf Lettuce
- Avocado
- Lemon
- Lime
- Radishes
- Green Onion
- Cucumber
- Iceberg Lettuce
- Mushrooms
- Tomato
- Cauliflower
- Green Cabbage
- Celery
- Green (Snap) Beans
- Asparagus
- Summer Squash
- Broccoli
- Kiwi
- Bell Pepper
- Strawberries
- Grapefruit
- Orange
- Honeydew Melon
- Pineapple
- Onion
- Tangerine
- Ocean Perch
- Rainbow Trout
- Salmon, Atlantic
- Catfish
- Swordfish
- Salmon, Chum
- Tilapia
- Orange Roughy
- Haddock
- Pollock
- Halibut
- Tuna
- Cod
- Flounder/Sole
- Rockfish
- Shrimp
- Scallops, about 6 large or 14 small
- Blue Crab
- Lobster
- Clams, about 12 small
- Oysters, about 12 medium
- Seafood
- Fruits
- Vegetables

tasks like sentiment analysis and topic modeling (Cozzolino & Ferraro, 2022). For sentiment analysis, clustering groups text data, such as customer reviews or social media posts, based on their emotional tone or underlying themes (Yu et al., 2023a,b). Similarly, in social network analysis, clustering is instrumental in community detection, uncovering subgroups of interconnected individuals or entities within a larger network (Malliaros & Vazirgiannis, 2013). These applications provide valuable insights into behavioral trends, opinion mining, and the dynamics of social ecosystems.

B ioanalysis relies heavily on clustering to group genes, classify cell types, and detect protein families, advancing research in personalized medicine and drug discovery (Udrescu et al., 2016). In personalized medicine, clustering is used to group patients based on genetic markers, symptoms, or treatment responses, aiding in the design of tailored therapeutic strategies. By identifying distinct biological / clinical patterns, clustering facilitates a deeper understanding of complex biological systems and supports precision healthcare initiatives (Lisik et al., 2025).

Clustering also supports M achine L earning by reducing dimensionality, initializing models, and identifying outliers, which enhances model robustness and performance (Yang et al., 2021). For A udio and V ideo A nalysis , clustering separates similar signals or frames, enabling speech recognition, speaker diarization, activity segmentation, and anomaly detection in videos (Qiu et al., 2024). Clustering complements D eep L earning workflows by organizing data for e ffi cient training or unsupervised representation learning. By clustering neural network embeddings, it uncovers meaningful patterns, validates models, and identifies latent structures in complex datasets (Yang et al., 2017).

Finally, clustering is a valuable tool in Q ualitative R esearch , as it helps identify patterns and groupings within complex, unstructured data (Macia, 2015). Specifically, clustering can be used to group similar themes, narratives, or codes from interviews, focus groups, or textual data, enabling researchers to uncover shared experiences or perspectives. In M ixed Q uan -titative and Q ualitative R esearch , clustering bridges the two approaches by integrating quantitative data, such as survey responses, with qualitative insights, like open-ended questions, to group participants or phenomena based on combined attributes (P´ eladeau, 2021). This enhances the depth of analysis, enabling researchers to explore nuanced patterns and relationships while maintaining a holistic view of the dataset (Henry et al., 2015).

## 6. Conclusion

Data clustering is an important and commonly used technique in data science, serving as a cornerstone for organizing complex datasets into coherent groups based on intrinsic similarities. As demonstrated in this paper, clustering not only simplifies high-dimensional data but also provides a robust framework for identifying latent structures and patterns that are critical for exploratory analysis and downstream tasks. Its flexibility and applicability across a broad spectrum of data types and domains underscore its enduring significance in solving intricate data challenges.

The integration of clustering with emerging technologies, particularly LLMs represents a significant advancement in the field. LLMs, with their ability to generate high-quality embeddings and capture nuanced patterns in data, enhance clustering

by providing more meaningful and compact feature representations. These embeddings are particularly useful for unstructured data, such as text and images, enabling traditional clustering algorithms, such as K-M eans to operate e ff ectively in reduced-dimensional spaces. This synergy between clustering and LLMs opens new avenues for applications ranging from image-based analysis to text mining, where extracting semantic relationships and organizing information is essential.

### Declaration of competing interest

The authors declare that they have no known competing financial interests or personal relationships that could have appeared to influence the work reported in this paper.

### References

- Abonyi, J., & Feil, B. (2007). Cluster analysis for data mining and system identification . Springer Science & Business Media.
- Aggarwal, C. C. (2013). An introduction to cluster analysis. In Data Clustering: Algorithms and Applications (pp. 1-28). Chapman and Hall / CRC.
- Aggarwal, C. C., Philip, S. Y., Han, J., & Wang, J. (2003). A framework for clustering evolving data streams. In Proceedings 2003 VLDB conference (pp. 81-92). Elsevier.
- Aggarwal, C. C., Wolf, J. L., Yu, P. S., Procopiuc, C., & Park, J. S. (1999). Fast algorithms for projected clustering. ACM SIGMoD record , 28 , 61-72.
- Aghabozorgi, S., Shirkhorshidi, A. S., & Wah, T. Y. (2015). Time-series clustering-a decade review. Information systems , 53 , 16-38.
- Agrawal, R., Gehrke, J., Gunopulos, D., & Raghavan, P. (1998). Automatic subspace clustering of high dimensional data for data mining applications. In Proceedings of the 1998 ACM SIGMOD international conference on Management of data (pp. 94-105).
- Alvarez-Garcia, M., Ibar-Alonso, R., & Arenas-Parra, M. (2024). A comprehensive framework for explainable cluster analysis. Information Sciences , 663 , 120282.
- Anderberg, M. R. (1973). Cluster Analysis for Applications . Probability and Mathematical Statistics: A Series of Monographs and Textbooks. Academic Press.
- Ankerst, M., Breunig, M. M., Kriegel, H.-P., & Sander, J. (1999). Optics: Ordering points to identify the clustering structure. ACM Sigmod record , 28 , 49-60.
- Berkhin, P. (2006). A survey of clustering data mining techniques. In Grouping multidimensional data: Recent advances in clustering (pp. 25-71). Springer.
- Bezdek, J. C., Ehrlich, R., & Full, W. (1984). Fcm: The fuzzy c-means clustering algorithm. Computers & geosciences , 10 , 191-203.
- Blei, D. M., Ng, A. Y., & Jordan, M. I. (2003). Latent dirichlet allocation. Journal of machine Learning research , 3 , 993-1022.
- Blondel, V. D., Guillaume, J.-L., Lambiotte, R., & Lefebvre, E. (2008). Fast unfolding of communities in large networks. Journal of statistical mechanics: theory and experiment , 2008 , P10008.
- Chang, X., Li, Y., Zhang, G., Liu, D., & Fu, C. (2024). An improved reinforcement learning method based on unsupervised learning. IEEE Access , 12 , 12295-12307.
- Cheng, Y. (1995). Mean shift, mode seeking, and clustering. IEEE transactions on pattern analysis and machine intelligence , 17 , 790-799.
- Cozzolino, I., & Ferraro, M. B. (2022). Document clustering. Wiley Interdisciplinary Reviews: Computational Statistics , 14 , e1588.
- Defays, D. (1977). An e ffi cient algorithm for a complete link method. The computer journal , 20 , 364-366.
- Dinh, D.-T., Fujinami, T., & Huynh, V.-N. (2019). Estimating the optimal number of clusters in categorical data clustering by silhouette coe ffi cient. In Knowledge and Systems Sciences: 20th International Symposium, KSS 2019, Da Nang, Vietnam, November 29-December 1, 2019, Proceedings 20 (pp. 1-17). Springer.
- Dinh, D.-T., Huynh, V.-N., & Sriboonchitta, S. (2021). Clustering mixed numerical and categorical data with missing values. Information Sciences , 571 , 418-442.
- Dinh, T., Hauchi, W., Fournier-Viger, P., Lisik, D., Ha, M.-Q., Dam, H.-C., & Huynh, V.-N. (2025). Categorical data clustering: 25 years beyond k-modes. Expert Systems with Applications , .
- Ester, M., Kriegel, H.-P., Sander, J., Xu, X. et al. (1996). A density-based algorithm for discovering clusters in large spatial databases with noise. In kdd (pp. 226-231). volume 96.
- Fraley, C., & Raftery, A. (1998). Mclust: Software for model-based cluster and discriminant analysis. Department of Statistics, University of Washington: Technical Report , 342 , 1312.
- Fraley, C., & Raftery, A. E. (2002). Model-based clustering, discriminant analysis, and density estimation. Journal of the American statistical Association , 97 , 611-631.
- Frey, B. J., & Dueck, D. (2007). Clustering by passing messages between data points. science , 315 , 972-976.
- Ganapathy, S., Thoidingjam, V., & Sen, A. (2024). A brain tumor prediction system for detecting the tumor disease using mini batch k-means clustering and cnn. Multimedia Tools and Applications , (pp. 1-39).
- Garc´ ıa-Saiz, D., Zorrilla, M., & Bosque, J. L. (2017). A clustering-based knowledge discovery process for data centre infrastructure management. The Journal of Supercomputing , 73 , 215-226.
- Gasparetti, F., Sansonetti, G., & Micarelli, A. (2021). Community detection in social recommender systems: a survey. Applied Intelligence , 51 , 39753995.
- Guha, S., Rastogi, R., & Shim, K. (2000). Rock: A robust clustering algorithm for categorical attributes. Information systems , 25 , 345-366.
- Han, J., Pei, J., & Tong, H. (2022). Data Mining: Concepts and Techniques . Elsevier Science.
- Hartigan, J. A., Wong, M. A. et al. (1979). A k-means clustering algorithm. Applied statistics , 28 , 100-108.
- He, L., & Li, K. (2024). Mitigating hallucinations in llm using k-means clustering of synonym semantic relevance. Authorea Preprints , .
- Henry, D., Dymnicki, A. B., Mohatt, N., Allen, J., & Kelly, J. G. (2015). Clustering methods with qualitative data: a mixed-methods approach for prevention research with small samples. Prevention science , 16 , 1007-1016.
- Holland, J. H. (1992). Adaptation in natural and artificial systems: an introductory analysis with applications to biology, control, and artificial intelligence . MIT press.
- Huang, H., Wang, C., Wei, X., & Zhou, Y. (2024). Deep image clustering: A survey. Neurocomputing , 599 , 128101.
- Huang, Z. (1997). A fast clustering algorithm to cluster very large categorical data sets in data mining. In Proceedings of the SIGMOD Workshop on Research Issues on Data Mining and Knowledge Discovery (pp. 1-8).
- Huang, Z. (1998). Extensions to the k-means algorithm for clustering large data sets with categorical values. Data mining and knowledge discovery , 2 , 283-304.
- Huang, Z., & Ng, M. K. (1999). A fuzzy k-modes algorithm for clustering categorical data. IEEE transactions on Fuzzy Systems , 7 , 446-452.
- Iam-On, N. (2020). Clustering data with the presence of attribute noise: a study of noise completely at random and ensemble of multiple k-means clusterings. International journal of machine learning and cybernetics , 11 , 491509.
- Inoue, T., Kubota, K., Ikami, T., Egami, Y., Nagai, H., Kashikawa, T., Kimura, K., & Matsuda, Y. (2024). Clustering method for time-series images using quantum-inspired digital annealer technology. Communications Engineering , 3 , 10.
- Izenman, A. J. (2008). Cluster analysis. In Modern Multivariate Statistical Techniques: Regression, Classification, and Manifold Learning (pp. 407462). New York, NY: Springer New York.
- Kassambara, A. (2017). Practical guide to cluster analysis in R: Unsupervised machine learning volume 1. Sthda.
- Kaufman, L., & Rousseeuw, P. J. (1990). Finding groups in data: an introduction to cluster analysis . John Wiley & Sons.
- Khan, R., Dobesova, R., Yang, Y., & Dinh, T. (2025). Enhanced feature-based clustering for urban land use pattern detection. In 16th International Conference on Knowledge and Systems Engineering (KSE) . IEEE.
- Kohonen, T. (1982). Self-organized formation of topologically correct feature maps. Biological cybernetics , 43 , 59-69.
- Kotu, V., & Deshpande, B. (2018). Data science: concepts and practice . Morgan Kaufmann.
- Krishna, K., & Murty, M. N. (1999). Genetic k-means algorithm. IEEE Transactions on Systems, Man, and Cybernetics, Part B (Cybernetics) , 29 , 433-

439.

- Lisik, D., Basna, R., Dinh, T., Hennig, C., Shah, S. A., Wennergren, G., Goks¨ or, E., & Nwaru, B. I. (2025). Artificial intelligence in pediatric allergy research. European Journal of Pediatrics , 184 , 1-20.
- Lloyd, S. (1982). Least squares quantization in pcm. IEEE transactions on information theory , 28 , 129-137.
- Van der Maaten, L., & Hinton, G. (2008). Visualizing data using t-sne. Journal of machine learning research , 9 .
- Macia, L. (2015). Using clustering as a tool: Mixed methods in qualitative data analysis. The Qualitative Report , 20 , 1083-1094.
- MacQueen, J. et al. (1967). Some methods for classification and analysis of multivariate observations. In Proceedings of the fifth Berkeley symposium on mathematical statistics and probability (pp. 281-297). volume 1.
- Maier, M., Luxburg, U., & Hein, M. (2008). Influence of graph construction on graph-based clustering measures. Advances in neural information processing systems , 21 .
- Malliaros, F. D., & Vazirgiannis, M. (2013). Clustering and community detection in directed networks: A survey. Physics reports , 533 , 95-142.
- MATLAB (2025). Matlab for machine learning. URL: https://www. mathworks.com/solutions/machine-learning.html .
- Maulik, U., & Bandyopadhyay, S. (2000). Genetic algorithm-based clustering technique. Pattern recognition , 33 , 1455-1465.
- McInnes, L., Healy, J., Astels, S. et al. (2017). hdbscan: Hierarchical density based clustering. J. Open Source Softw. , 2 , 205.
- McInnes, L., Healy, J., & Melville, J. (2018). Umap: Uniform manifold approximation and projection for dimension reduction. arXiv preprint arXiv:1802.03426 , .
- M¨ uller, H., & Hamm, U. (2014). Stability of market segmentation with cluster analysis-a methodological approach. Food Quality and Preference , 34 , 7078.
- Nasraoui, O., & N'Cir, C.-E. B. (2019). Clustering methods for big data analytics: Techniques, Toolboxes and Applications . Springer.
- Ng, A., Jordan, M., & Weiss, Y. (2001). On spectral clustering: Analysis and an algorithm. Advances in neural information processing systems , 14 .
- Parsons, L., Haque, E., & Liu, H. (2004). Subspace clustering for high dimensional data: a review. Acm sigkdd explorations newsletter , 6 , 90-105.
- P´ eladeau, N. (2021). Cluster analysis for mixed methods research. In The Routledge Reviewer's Guide to Mixed Methods Analysis (pp. 57-68). Routledge.
- Peng, D., Gui, Z., & Wu, H. (2023). Interpreting the curse of dimensionality from distance concentration and manifold e ff ect. arXiv preprint arXiv:2401.00422 , .
- Qiu, S., Ye, J., Zhao, J., He, L., Liu, L., Bicong, E., & Huang, X. (2024). Video anomaly detection guided by clustering learning. Pattern Recognition , 153 , 110550.
- Rajamohamed, R., & Manokaran, J. (2018). Improved credit card churn prediction based on rough clustering and supervised learning techniques. Cluster Computing , 21 , 65-77.
- Reddy, C. K., & Vinzamuri, B. (2013). A survey of partitional and hierarchical clustering algorithms. In Data Clustering: Algorithms and Applications (pp. 87-110). Chapman and Hall / CRC.
- Reutterer, T., & Dan, D. (2021). Cluster analysis in marketing research. In Handbook of market research (pp. 221-249). Springer.
- Schubert, E., Sander, J., Ester, M., Kriegel, H. P., & Xu, X. (2017). Dbscan revisited, revisited: why and how you should (still) use dbscan. ACMTransactions on Database Systems (TODS) , 42 , 1-21.
- Sibson, R. (1973). Slink: an optimally e ffi cient algorithm for the single-link cluster method. The computer journal , 16 , 30-34.
- Silva, J. A., Faria, E. R., Barros, R. C., Hruschka, E. R., Carvalho, A. C. d., & Gama, J. (2013). Data stream clustering: A survey. ACM Computing Surveys (CSUR) , 46 , 1-31.
- Strehl, A., & Ghosh, J. (2002). Cluster ensembles-a knowledge reuse framework for combining multiple partitions. Journal of machine learning research , 3 , 583-617.
- Sun, L., Hu, J., Zhou, S., Huang, Z., Ye, J., Peng, H., Yu, Z., & Yu, P. (2024). Riccinet: Deep clustering via a riemannian generative model. In Proceedings of the ACM on Web Conference 2024 (pp. 4071-4082).
- Tan, P., Steinbach, M., Karpatne, A., & Kumar, V. (2019). Introduction to Data Mining (Second Edition) . Pearson.
- Tukey, J. W. et al. (1977). Exploratory data analysis volume 2. Reading, MA. Udrescu, L., Sbˆ arcea, L., Topˆ ırceanu, A., Iovanovici, A., Kurunczi, L., Bogdan, P., & Udrescu, M. (2016). Clustering drug-drug interaction networks with
- energy model layouts: community analysis and drug repurposing. Scientific reports , 6 , 32745.
- Ward Jr, J. H. (1963). Hierarchical grouping to optimize an objective function. Journal of the American statistical association , 58 , 236-244.
- Waskom, M. L. (2021). Seaborn: statistical data visualization. Journal of Open Source Software , 6 , 3021.
- Wu, X., Kumar, V., Quinlan, J. R., Ghosh, J., Yang, Q., Motoda, H., McLachlan, G. J., Ng, A., Liu, B., Philip, S. Y . et al. (2008). Top 10 algorithms in data mining. Knowledge and information systems , 14 , 1-37.
- Yang, B., Fu, X., Sidiropoulos, N. D., & Hong, M. (2017). Towards k-meansfriendly spaces: Simultaneous deep learning and clustering. In international conference on machine learning (pp. 3861-3870). PMLR.
- Yang, J., Rahardja, S., & Fr¨ anti, P. (2021). Mean-shift outlier detection and filtering. Pattern Recognition , 115 , 107874.
- Yu, Y., Dinh, D.-T., Nguyen, B.-H., Yu, F., & Huynh, V.-N. (2023a). Mining insights from esports game reviews with an aspect-based sentiment analysis framework. IEEE Access , 11 , 61161-61172.
- Yu, Y., Dinh, T., Yu, F., & Huynh, V.-N. (2023b). Understanding mobile game reviews through sentiment analysis: A case study of pubgm. In International Conference on Model and Data Engineering (pp. 102-115). Springer.
- Zhang, T., Ramakrishnan, R., & Livny, M. (1996). Birch: an e ffi cient data clustering method for very large databases. ACM sigmod record , 25 , 103114.