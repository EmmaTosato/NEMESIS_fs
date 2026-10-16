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

