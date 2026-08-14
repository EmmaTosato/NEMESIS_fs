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

