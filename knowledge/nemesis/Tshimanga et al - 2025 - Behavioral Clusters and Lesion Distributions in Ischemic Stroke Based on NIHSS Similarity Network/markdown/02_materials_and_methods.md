## 2 Materials and Methods

### 2.1 Data

The NIHSS data consist of 15 items describing the health state, abilities, and cognitive functions of first-stroke ischemic patients from Padua University Hospital and from Washington University in St. Louis. Some items are based on exterior observations that assess damage in specific areas of the brain, while other items test patients with more complex tasks, possibly involving disparate brain regions. NIHSS scores here refer to the acute phase. The average time between the stroke event and the NIHSS assessment for the n = 189 ischemic subjects in Padua is 4 . 7 ± 2 . 8 days, while for the n = 119 ischemic subjects in St. Louis, it is 12 . 8 ± 4 . 6 days. The average age instead is 68 . 9 ± 15 . 0 years for Padua and 55 . 3 ± 11 . 7 years for St. Louis. A brief summary of statistics of the NIHSS items for the 308 ischemic subjects, are reported in the supplementary material Appendix 1. Statistics and clustering are computed and performed on the subset of subjects from both hospitals, with total NIHSS > 0 and with available brain scans, resulting in n = 172 patients selected. The initial selection assumes that a total NIHSS score of 0 results from lesions that do not affect function in a measurable way, while the latter selection enables symptoms-to-lesions mapping that would otherwise be impossible. The Level Of Consciousness (LOC)-Vigilance item is removed and the only subject not scoring 0 is filtered out: LOC-Vigilance > 0 signals that the subject is not conscious and other deficits cannot be assessed, directly leading to missing data and the impossibility of relating lesions to symptoms properly.

Imaging data come from CT and MRI scans, co-registered in MNI152 standard space [30] at 1mm 3 resolution, with lesions segmented by professionals. The lesion volume is calculated from the lesion masks in the co-registered space; the average lesion volume is 32 . 71 ± 47 . 37 mL. The population lesion distribution for the 172 patients is reported in Appendix 1. A summarizing scheme of data selection is shown in Fig. 1.

*[picture on PDF page 4]*

**Figure labels:**
- 123

127

Ischemic: 189

101

Total NIHSS Score > 0: 150

M

76

With MRI: 116

M

F

59

57

109

104

F

93

*[picture on PDF page 5]*

**Figure labels:**
- Hemorrhagic: 18
- Other: 29
- M
- F
- 11
- 71
- 15
- 14
- 88
- 74
- No MRI: 34
- 17
- Ischemic: 119
- 63
- 56
- Total NIHSS Score > 0: 98
- 51
- 47
- With MRI: 56
- No MRI: 42
- 28
- 23
- 19
- Hemorrhagic: 30
- 12
- 18
- Other: 48
- 29

### 2.2 Correlations and Distances

Denoting P the set of n patients, and Xn = 172 , m = 14 the matrix of NIHSS observations considered, the relationship between NIHSS items across the population is explored withstatistics suitable for ordinal data. Deficits co-occurrences are counted irrespective of severity: for each couple of items, the number of patients exhibiting both deficits is counted. Then Spearman's rank correlation coefficient among items is computed, to measure positive and negative associations of severity. These are all operations of type X T X ( m = 14 , m = 14 ) and only serve as descriptive statistics of the dataset.

The General Distance Measure [31, 32] (GDM) is the proximity measure quantifying how different two patients are, based on their profile composed of 14 NIHSS scores. The GDM is defined as taking inspiration from Kendall's General Correlation Coefficient, in order to process continuous as well as ordinal values. It is here corrected and simplified in notation as:

dab = m ∑ j = 1 dabj with dabj = 1 2 m --σ 2 abj + ∑ n c = 1 , c /negationslash= a , b σ acj σ bcj 2 [ ∑ m j = 1 ∑ n c = 1 σ 2 acj ∑ m j = 1 ∑ n c = 1 σ 2 bcj ] 1 2 , (1)

and

σ abj =      1 , if xaj > xbj -1 , if xaj < xbj 0 , if xaj = xbj (2)

*[picture on PDF page 5]*

**Figure labels:**
- 123

Padua: 236

St. Louis: 197

#### with

a , b , c = 1 , 2 , ..., n : indexes of the n subjects (stroke patients) j = 1 , 2 , ..., m : index of the m variables (NIHSS items) xaj : value of the variable j for subject a (NIHSS score) σ abj : sign of the difference between patient a and patient b for item j dabj : distance between subjects a and b , on item j . dab : distance between subjects a and b .

Note that the GDM and its complement, the General Similarity Measure (GSM, of value sab := 1 -dab ), depend on the whole cohort observations X for each pairwise computation. These are operations of type XX T ( n = 172 , n = 172 ) , thus computing similarities between patients can be seen as the dual problem with respect to that of computing correlations between variables. The matrix of all pairwise relationships is symmetric, describing an undirected weighted graph: it is hence called the adjacency matrix W ( n = 172 , n = 172 ) for the graph G ( P , W ) , with n nodes referring to the patients and n ( n -1 )/ 2 weighted edges referring to the GSM of all pairs of patients. For simplicity, W will hereon denote the matrix or the network, depending on context.

### 2.3 Repeated Spectral Clustering

Repeated Spectral Clustering (RSC) is a novel consensus clustering approach, defined in this paper based on spectral clustering, and aimed at dealing with the variability of results that stems from random initializations. Spectral clustering is the name for techniques based on the spectrum of the adjacency matrix's (or graph's) Laplacian [28]. Further arguments for using spectral clustering instead of other common techniques, such as hierarchical clustering and k -means, can be found in supplementary material Appendix 2. Spectral clustering consists of two steps: spectral embedding, and clustering in the embedding space. The spectral embedding step yields Euclidean coordinates for the network nodes, in the space defined by the eigenvectors of the graph Laplacian. The actual clustering step can be any algorithm working in Euclidean spaces, typically k -means in embedding space [33], as in the present case. RSC is also a consensus clustering technique, with two distinct phases of spectral clustering. In the first phase, there is evidence accumulation: the results of N different spectral clustering runs on W are recorded in the ( n × n ) consensus matrix C . In the second phase, C itself undergoes spectral clustering [34]. RSC is defined by the use of Lsym spectral clustering [33] for both phases, whereas other consensus clustering methods change algorithm between the two phases, or change algorithm and/or data subset in the N runs of the first phase. While the entries of W measure the similarities between any two subjects, the corresponding entries of C count how many times those any two subjects are clustered together over the N runs of the evidence accumulation phase [35] (clustering co-occurrence, from now on co-clustering). The more times two subjects are co-clustered, the more evidence those subjects are actually similar and co-members of a statistically stable cluster. Matrix C too induces a weighted undirected graph and its spectral properties and visual aspect highlight how the subject nodes are better separable than they are in W . Notably, while data partitions based on W may vary widely due to random initializations, both the entries of C and the resulting partitions are

*[picture on PDF page 6]*

**Figure labels:**
- 123

remarkably stable. Defined in this way, RSC unifies the ability to find clusters in spectral embedding with the robustness of results regarding centroids initialization, thanks to the evidence accumulation stage. As with other algorithms akin to k -means, the number of clusters k is set a priori or heuristically: here, the methodology relies on the spectral properties of C as a function of k . Overall, RSC can be interpreted as a way to extract the clustering signal C in the noisy W , averaging multiple measurements. The modules of RSC are described in Algorithms 1, 2, and 3 for spectral embedding, clustering, and the whole RSC, respectively. Appendix 3 provides a deeper introduction to spectral clustering, an analysis of how the number of random initializations impacts and stabilizes the final results, and detailed arguments for the better separability of C with respect to W .

#### Algorithm 1 Spectral embedding.

- 1: inputs : A , k
- 2: compute graph Laplacian from adjacency matrix A
- 3: compute k eigenvectors for the k smallest eigenvalues of Laplacian
- 4: employ eigenvectors as columns of matrix UA
- 5: L2-normalize UA rows, giving matrix TA
- 6: return TA

#### Algorithm 2 Clustering.

- 1: inputs : T , k
- 2: compute clusters with k -means for the co-ordinates in T
- 3: return labels

#### Algorithm 3 Repeated spectral clustering.

- 1: inputs : W , k
- 2: instantiate C ← 0 n , n 3: perform **Algorithm 1** with ( W , k ) 4: set repetitions N ← 1000 5: while N /negationslash= 0 do 6: perform **Algorithm 2** with ( TW , k ) 7: update C 8: N ← N -1 9: end while 10: perform Algorithm 1 with ( C , k ) 11: perform Algorithm 2 with ( TC , k )

### 2.4 Voxel-wise Analysis

The application of RSC to the affinity matrix obtained from the GDM pairwise similarities leads to the isolation of clusters. In order to evaluate how a cluster is different

*[picture on PDF page 7]*

**Figure labels:**
- 123

/triangleright TA is the matrix of embeddings of A

from the others, lesion density maps can be visually compared in Fig.4. Each map is obtained by averaging the binary lesion masks in the respective cluster: thus, each voxel's intensity represents the normalized frequency (scaled between 0 and 1) of lesions occurring in that voxel within the cluster. In other words, it shows the proportion of patients in the cluster with a lesion in that location. To quantitatively test how significant are differences between clusters, we further perform a voxel-wise analysis. Since the objective of the clustering algorithm is to separate clusters in the space related to NIHSS items, statistical tests on the separation in these same variables would lead to inflated p-values. For this reason, the statistical analysis focuses on voxels that are lesioned with significantly different frequencies across clusters.

The analysis conducted is composed of the following steps:

- The comparisons are done in a one vs all-but-one way; the null-hypothesis H 0 affirms that the lesion distribution in one cluster is not different from the lesion distribution of all the remaining patients.
- From the 182 × 218 × 182 available voxels in MNI-152 template, we select those that are lesioned at least 8 times, which corresponds to the 5% of the patients. This is both for a statistical reason, since these voxels carry a greater effect size, as well as a computational reason, since this selection considers only 241163 voxels.
- The test performed is the difference between proportions with pooled variance [36]:

where ni : number of patients in cluster i .

n : number of patients (172).

v + i : number of times voxel v , is lesioned ( + ) considering patients in cluster i .

v + : number of times voxel v , is lesioned ( + ) considering all the patients.

- Apermutational approach is used, where patients' cluster assignment is randomly shuffled; for each selected voxel the statistic is computed 5000 times. In this way the distribution of the statistic t v can be built under H 0, where there is random assignment of patients' lesions to clusters.
- Due to the large number of hypotheses under test (1 for each voxel), a multiplecomparison correction is needed. Both Bonferroni and Holm's [37] methods are largely conservative, so a multistep-maxT (Westfall & Young [38]) procedure is used instead. This allows a Family Wise Error Rate (FWER) control at α = 0 . 01.

Since RSC is performed with k =5, the presented methodology is applied five times. These other five comparisons are not taken into account by the max-T algorithm; consequently, a Bonferroni correction is applied. Therefore, the results are said to be overall corrected, with FWER at α = 0 . 05.

*[picture on PDF page 8]*

**Figure labels:**
- 123

t v = | v + i ni -v + -v + i n -ni | √ v + n ( 1 -v + n )( 1 ni + 1 n -ni ) (3)

### 2.5 Open-source Software Tools

Manual segmentations and template normalizations preliminary [10] for this work were done respectively with ITK-snap [39] and ANTs [40]. Filtering data, statistical analyses, clustering, lesion frequency map computation, and visualization are all performed with the Python 3 programming language, and its libraries numpy, pandas, scipy, scikit-learn, nibabel, and nilearn . Voxel-wise analyses are conducted with the R programming language, and its libraries foreach, doFuture, utils, scales, reticulate . The multi-step maxT correction is done using the code available at https://github.com/ livioivil/r41sqrt10. In order to allow the usage of the presented analytic workflow by the scientific community on different datasets, code is available at https://github.com/ MedMaxLab/nihss_clustering; data will be available upon reasonable request to the authors.

