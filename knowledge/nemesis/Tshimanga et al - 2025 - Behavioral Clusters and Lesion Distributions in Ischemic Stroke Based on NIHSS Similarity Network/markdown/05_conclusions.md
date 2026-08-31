## 5 Conclusions

In recent years, machine learning and data science have advanced significantly, offering new prospects across many domains. The medical field's complexity, with its numerous variables and statistical properties, makes it difficult to create data-driven mathematical models of diseases from healthcare data. In this paper, for the first time, we address stroke patient clustering, presenting a novel unsupervised data analysis pipeline tailored to the properties of health scales, and applied to a leading global cause of death and disability. Many studies have analyzed patient behavior and lesion

*[picture on PDF page 17]*

**Figure labels:**
- 123

locations, but they often rely on assumptions that can limit their validity, such as treating item modalities as numerical data and using linear models. This research complements existing viewpoints by following a new and precise methodological path and introducing new key elements. The methods presented are specifically tailored to address intrinsic problems of biomedical data. They focus on the thorough treatment of ordinal variables and avoid restrictive, distorting assumptions through the use of GDM and model-free lesion mapping. Additionally, these methods leverage an innovative approach based on evidence accumulation clustering.

The lesion maps show anatomical separation based on cluster membership, aligned with the expected localization of deficits, despite being based solely on the clustering of behavioral data. They describe a detailed structure of neurological syndromes that are in line with topographical and etiological features of acute stroke.

The novel and open source workflow here provided is flexible and of high methodological value, ready for extensive adaptations to multimodal biomedical data in other domains, whenever unsupervised phenotypizing of obervations is difficult but potentially enriching, and whenever clinical healthcare data comprises ordinal scales.

### Appendix 1. Dataset summary statistic

For all the 308 ischemic patients comprised in the two cohorts, Padua and St. Louis, somesummarystatisticshavebeencomputed,suchasmean(M)andstandarddeviation (SD) of every item, Table 1

The same statistics for the 172 subjects used for clustering, separated by cohorts are reported in Table 2.

***Table 1 Mean (M) and standard deviation (SD) calculated for every NIHSS item, calculated for all 308 ischemic subjects***

| NIHSS Item | Padua (189):M ± SD | St. Louis (119):M ± SD |
|---|---|---|
| LOC-Q | 0.14 ± 0.46 | 0.07 ± 0.31 |
| LOC-C | 0.02 ± 0.13 | 0.02 ± 0.13 |
| Best Gaze | 0.02 ± 0.14 | 0.07 ± 0.28 |
| Visual | 0.16 ± 0.49 | 0.28 ± 0.57 |
| Facial Palsy | 0.65 ± 0.64 | 0.34 ± 0.67 |
| Motor Arm R | 0.23 ± 0.68 | 0.60 ± 1.32 |
| Motor Leg R | 0.16 ± 0.53 | 0.35 ± 1.07 |
| Motor Arm L | 0.24 ± 0.78 | 0.48 ± 1.07 |
| Motor Leg L | 0.14 ± 0.56 | 0.29 ± 0.88 |
| Limb Ataxia | 0.05 ± 0.25 | 0.26 ± 0.54 |
| Sensory | 0.10 ± 0.32 | 0.40 ± 0.51 |
| Best Language | 0.47 ± 0.80 | 0.25 ± 0.59 |
| Dysarthria | 0.33 ± 0.50 | 0.38 ± 0.55 |
| Inattention | 0.12 ± 0.41 | 0.15 ± 0.46 |

*[picture on PDF page 18]*

**Figure labels:**
- 123

Lesion distribution, threshold=8

L

y=-17

R

31

23

***Table 2 Mean (M) and standard deviation (SD) calculated for every NIHSS item and calculated for the 172 ischemic subjects considered for clustering***

| NIHSS Item | Padua (116):M ± SD | St. Louis (56):M ± SD |
|---|---|---|
| LOC-Q | 0.20 ± 0.55 | 0.11 ± 0.41 |
| LOC-C | 0.03 ± 0.16 | 0.04 ± 0.19 |
| Best Gaze | 0.03 ± 0.18 | 0.05 ± 0.30 |
| Visual | 0.18 ± 0.52 | 0.36 ± 0.64 |
| Facial Palsy | 0.83 ± 0.62 | 0.38 ± 0.73 |
| Motor Arm R | 0.28 ± 0.77 | 0.59 ± 1.33 |
| Motor Leg R | 0.20 ± 0.59 | 0.46 ± 1.13 |
| Motor Arm L | 0.34 ± 0.90 | 0.64 ± 1.38 |
| Motor Leg L | 0.17 ± 0.64 | 0.55 ± 1.17 |
| Limb Ataxia | 0.06 ± 0.24 | 0.36 ± 0.64 |
| Sensory | 0.14 ± 0.37 | 0.48 ± 0.54 |
| Best Language | 0.62 ± 0.88 | 0.29 ± 0.59 |
| Dysarthria | 0.41 ± 0.53 | 0.45 ± 0.57 |
| Inattention | 0.16 ± 0.47 | 0.18 ± 0.51 |

The population lesion distribution for these patients having the images is reported in Fig. 6; voxels lesioned by less than 8 patients are not reported.

*[picture on PDF page 19]*

***Fig. 6 Lesion heat-map for the 172 ischemic patients used for clustering. Voxels lesioned in less than 8 subjects are omitted, for statistical reasons expressed in Section 2.4***

*[picture on PDF page 19]*

**Figure labels:**
- 123

R

### Appendix 2. Other Clustering Techniques

k -means and hierarchical clustering are two widely used clustering techniques. This section demonstrates why these methods are unsuitable for NIHSS items and suggests alternative approaches.

Since k is a hyper-parameter of k -means, we experimented with different values ranging from 2 to 9. The raw NIHSS can be input to k -means, along with its normalized and standardized versions. The algorithm defaults to using Euclidean distance for this analysis. Concerning the sklearn 'KMeans' function used, the initialization was set to random, inertia to 10, and the maximum number of iterations to 300, with a random state of 12345. Table 3 reports the number of subjects for each cluster across various normalization combinations and values of k .

To evaluate cluster quality, consider cluster size: both very large clusters (over 50% of subjects) and very small clusters (under 5% of subjects) are problematic. Large clusters obscure phenotypic differences, while small clusters lack statistical power. Prior hypotheses on the number of clusters and their sizes should be permissive, but finding only 1 cluster or only clusters with 1 subject are degenerate solutions. 50% is the largest intuitive fraction associated with random cluster assignment with a uniform prior in the simplest setting ( k = 2 ) ; similarly, 5% is widely used as a significance threshold in statistics. The same reasoning can be framed in terms of statistical power, as the same 5% threshold was used to select the voxel threshold of 8 patients in Section 2.4. Configurations with fewer than 8 or more than 85 subjects should be thus discarded. With these criteria, the only suitable configurations are normalized data with k = 5 and k = 6 and raw data with k = 5. In these configurations, clusters for Motor Right, Motor Left, and Language deficits were identified.

In all these three configurations the patients in Motor-R are 13, while the patients in Motor-L are respectively 14 for norm data and 16 for raw data; our clusters account better for patients with moderate and low scores in these items, giving 27 and 26 subjects respectively. The patients that are excluded from these three clusters are 74 in our work, while 114 with k -means. The main reasons for the observed behavior could be the high-dimensionality of the data, and the spherical-shape of clusters of the k -means algorithm.

***Table 3 Number of subjects, for each cluster, for all the possible combinations of k and normalization used***

| k | Standardized | Normalized | Raw |
|---|---|---|---|
| 2 | 157, 15 | 155, 17 | 156, 16 |
| 3 | 15, 13, 144 | 142, 13, 17 | 16, 13, 143 |
| 4 | 112, 15, 13, 32 | 111, 17, 13, 31 | 112, 16, 32, 12 |
| 5 | 93, 19, 13, 32, 15 | 75, 14, 39, 31, 13 | 37, 52, 16, 54, 13 |
| 6 | 13, 13, 16, 106, 19, 5 | 37, 13, 14, 64, 13, 31 | 58, 7, 9, 54, 12, 32 |
| 7 | 27, 13, 9, 7, 5, 19, 92 | 10, 18, 33, 31, 62, 5, 13 | 38, 21, 10, 6, 17, 67, 13 |
| 8 | 79, 18, 15, 5, 1, 15, 32, 26 | 37, 12, 10, 62, 23, 5, 10, 13 | 12, 12, 38, 52, 16, 32, 6, 4 |
| 9 | 27, 18, 15, 5, 1, 15, 13, 26, 52 | 37, 12, 10, 62, 23, 4, 10, 13, 1 | 12, 12, 38, 52, 12, 8, 5, 4, 29 |

In green the configurations with a number of subjects matching the 50-5% criterion

*[picture on PDF page 20]*

**Figure labels:**
- 123

Hierarchical (agglomerative) clustering is another popular technique used to progressively aggregate data together, based on a distance measure. At each iteration, the subjects below a distance threshold are grouped together. The algorithm results in a dendrogram, a tree-like diagram in which every data point corresponds to the leaves, and branches to track the merging of subjects in larger groups. Varying the distance threshold, the tree gives different numbers of clusters from a maximum equal to the number of patients to only one cluster of all patients. The standard technique to assess the 'true' number of clusters is to check the longest interval in terms of distance threshold (GDM), for which the number of clusters does not change. The longer the interval, the stronger the evidence for a structure and number of clusters. In our case, the distance is given by the GDM matrix (thus pre-computed), and the linkage mode was set to complete. Figure7 shows the number of clusters with respect to the GDM distance, where the optimal k was found to be 4. However following the rules before, there are the usual right/left motors and language clusters, but cluster 0 has 96 patients, that is more than half of the dataset.

*[picture on PDF page 21]*

***Fig. 7 Number of clusters found by the hierarchical clustering versus the distance values. In red is shown the longest interval corresponding to 4 clusters***

*[picture on PDF page 21]*

**Figure labels:**
- 123

In conclusion, vanilla k -means and hierarchical clustering, are not suited for the NIHSS data of our two cohorts; spectral clustering is the next most commonly used clustering technique and it was used as the base of this work.

### Appendix 3. Spectral Clustering

Spectral clustering is a very powerful clustering technique; however, its geometrical foundation makes it hard to understand at first glance for non-experts in the field. In Fig.8, it is reported a brief illustrated example of how spectral clustering works.

*[picture on PDF page 22]*

From the adjacency matrix W , built from the similarity measure with w ab = sab , the associated normalized Laplacian matrix Lsym is calculated [33]. If the graph of W has n separate sub-graphs, the Laplacian has n eigenvalues equal to 0. Similarly, if the Laplacian has n relatively small eigenvalues, the graph of W has n components far more connected internally than with one another. The eigenvectors associated with the n first, the smallest eigenvalues are then used to create the new embedding space, where the data set is projected to. Once the spectral embedding is performed, k -means clustering is typically run over the new data set with k equal to the number n of eigenvectors considered. k -means clustering results in a complete, hard partition of the data. The above steps would complete one level of spectral clustering. However, it is well known that k -means results depend heavily on the random initialization of the centroids. Consequently, different runs of the algorithm will yield different results and partitions. Ensembling of clustering results, also known as consensus clustering [57], is the process of aggregating different partitions from multiple algorithms into a single,

*[picture on PDF page 22]*

**Figure labels:**
- 123

robust one. Evidence Accumulation Clustering [35] is a particular consensus clustering technique. In particular, this technique is based on repeating N times the k -means algorithm. Through repetitions, evidence accumulates regarding which data samples consistently and reliably cluster together. The so called clustering co-occurrence (or co-clustering) matrix C is defined, where the entries Cab are the number of times two subjects a and b are clustered together over the N trials, as shown in Fig. 9.

*[picture on PDF page 23]*

**Figure labels:**
- 1° run
- 2° run
- 3° run
- ....
- Graph Induced by
- 1
- 3
- 2

The matrix C describes a new graph, where strong connections represent frequent associations in the same clusters. The default hard partition from k -means is lost to a soft partition of connected communities. Since the objective of clustering is still assigning labels to data points, a further clustering method could be applied to the co-clustering matrix C , to finally separate the communities in the new co-clustering network. In this work, a further spectral embedding and k -means is performed on C , given that its spectral properties and separability are enhanced compared to the original adjacency matrix W . This idea is analogous to work in [34], where the spectral embedding relies on a different Laplacian form, Lr w , and the clustering for evidence accumulations are several and different algorithms.

### 3.1 Statistics

Considering the number of times N the k -means has to be executed, the event two *patients are clustered together* is a dichotomous event; hence Cab follows a Binomial distribution. Since C can be written as C = NP , Cab are interpreted as mean values, so the error associated with each entry scales as 1 √ N . From statistical reasoning on the error of the variance, the minimum number of trials is, therefore, 200; in this work N = 1000. Going into the details of the k -means function implemented in scikit-learn , there is a parameter called ninit that indicates how many runs have to be executed to give the final answer, i.e., the labels. The idea behind this is to try different runs and choose that with the smallest inertia, as the best candidate out of the batch. Further details can be seen in the corresponding web page https://scikitlearn.org/stable/. Since in this work, the k -means is repeated several times in order to fully exploit the stochasticity of the centroids initialization, in principle ninit = 1. However as can be seen in Fig.10, moving from ninit = 4 to ninit = 1 gives rise to a

*[picture on PDF page 23]*

**Figure labels:**
- 123

bell-like shape probability distribution function, centered in 54; still the main peak of the inertia is in the bins [ 42 , 43 ] .

This indicates that increasing ninit a little bit (e.g., 4) is beneficial for having clusters with low inertia and avoid to have noisy-configurations with inertia around 54. However even in the case with ninit = 1 the final labels are equal to the case of ninit = 4.

*[picture on PDF page 24]*

### 3.2 Computational Benchmark

The time needed for the computation of the General Distance Measure (GDM) matrix and the time needed by the Repeated Spectral Clustering (RSC) algorithms are reported. In detail, a random NIHSS-like dataset with increasing size has been built, and fed to the proposed pipeline.

### 3.3 Matrices W and C , before and after RSC

This section aims to show the effect of the RSC algorithm, on the matrix of similarities W . In detail, the effect of clustering is making this matrix, the most block diagonal as possible. Then the co-clustering matrix C is compared to the matrix W .

### 3.4 Optimal number of clusters

The way in which n is chosen for W and C relies on the spectra of the normalized Laplacians of the matrices W , C . As stated above, in classical spectral clustering, n null eigenvalues indicate n completely separate groups in the data graph, and n very small eigenvalues followed by a larger eigenvalue indicate n softly distinct groups. So, in the absence of exactly 0-valued eigenvalues, the problem consists in finding a spectral gap, i.e., a large difference between an eigenvalue and all the other quasi-0 predecessors. The n -th spectral gap for W is the difference between the n + 1-th and the n -th ordered eigenvalues of the Laplacian matrix of W . For each value of k , repeated

*[picture on PDF page 24]*

**Figure labels:**
- 123

*[picture on PDF page 25]*

clustering of W constructs a different matrix Ck . The n -th spectral gap for Ck is again the difference between the n + 1-th and the n -th ordered eigenvalues of the Laplacian matrix of Ck . The max gap criterion would suggest to choose k for a given graph so that the k -th spectral gap (the difference between k + 1-th and k -th eigenvalues) is maximal. However, the graph of Ck has k subcomponents by construction, therefore the maximal spectral gap for C -K is always expected to be the k -th. The actual choice must be made among the different max gaps across the matrices Ck , for every k attempted. Thus domain knowledge and comparisons with the spectrum of W must be taken into account to select k . The interpretation of the criterion is to choose k so that RSC has the highest added value in terms of information.

In Fig. 13 is reported the max gaps of C for different k trials.

Figure13 is, therefore, the main tool to evaluate the quality of the cluster solution and thus the main tool to decide the optimal number of clusters. Regarding the results of the main manuscript, the optimal solution found is then k = 5. There is a priori knowledge of the minimum number of clusters to be found in this domain, which is

*[picture on PDF page 25]*

**Figure labels:**
- 123

1.00

• 100

1.00

• 100

- 900

- 800

- 0.75

- 0.75

- 750

- 700

- 600

- 500

- 0.50

- 500

- 400

- 300

- 250

- 0.25

- 0.25

- 200

- 100

- 01

0.00

0.00

*[picture on PDF page 26]*

3 as the main domains involved in stroke (language, motor right, and motor left): the solution should have at least 3 clusters, and k = 5 stands out among those clusterings.

Finally, in Fig. 14, the C graphs obtained for different k are shown, similarly to the case k = 5 shown in Fig.3 in the main manuscript. It can be seen that all other solutions ( k = 3 , 4 , 6), showing less separated clusters, respect the optimal solution k = 5, thus representing a situation in which different patients are often assigned to different clusters, making the assignment of patients to clusters unstable.

*[picture on PDF page 26]*

**Figure labels:**
- 123

*[picture on PDF page 27]*

#### Appendix 4. Stability of the RSC Results

The goal of this section is to investigate the stability of the clustering results with respect to the population size. Thus first the RSC clustering algorithm is applied to the two cohorts separately; in detail, the algorithm is applied to the 116 subjects from Padua and to the 56 subjects from St. Louis. Then the RSC algorithm is applied to the whole ischemic population, with the constraint of NIHSS > 0, comprising 248 subjects.

Concerning the first case, the optimal number of clusters is 4 for Padua and 4 for St. Louis. The Sankey's plot, displaying how patients clustered in Padua and St. Louis separately are mapped into the clusters obtained when the two cohorts are together, is shown in Fig.15.

The Facial Palsy Cluster C3 (34 patients) obtained from PD+SL shared 24/25 patients of PD Cluster C4. The Motor Left Cluster C0 (27 patients) obtained from PD+SL has 9/9 patients from SL Cluster C3 and 15/16 patients from PD Cluster C0.

*[picture on PDF page 27]*

**Figure labels:**
- 123

Network of Patients and Cluster Assignment K=3

Network of Patients and Cluster Assignment K=4

(A)

(B)

5117174

Co co

C1

Network of Patients and Cluster Assignment K=5

Network of Patients and Cluster Assignment K=6

Co

Co

C1

*Cluster color Legend "

P22/152P21

SOS 12/098

So% Sons 1673/1l

• 100

100

•900

•900

800

• 800

*[picture on PDF page 28]*

**Figure labels:**
- P12957
- C1
- C2
- Cluster color Legend
- (C)
- C3
- C4
- • 700
- - 600
- - 500
- - 400
- 300
- -200
- - 100
- 100
- •900
- - 800
- • 600
- -300
- 200
- (D)
- C5
- 700
- +600
- -500
- -400
- - 200
- +100
- -900
- •700
- -600
- 500
- 1300

The Motor Right Cluster C2 (26 patients) obtained from PD+SL has 10/11 patients from SL Cluster C1 and 16/24 patients from PD Cluster C2. The Language Cluster C4 (45 patients) obtained from PD+SL is mainly constituted of the 27/27 patients from PD Cluster C1 and other patients from SL Cluster C2 and 7/24 patients from PDCluster C3. Finally, the heterogeneous cluster C1 obtained from PD+SL has 14/15 patients from SL Cluster C0 and 15/24 patients from PD Cluster C3 and the remaining from SL Cluster C2. In summary, patients found in the clusters when the cohorts were kept separate are found again in the clusters obtained with the combined cohorts.

Concerning instead the ischemic population, with the constraint of NIHSS > 0, comprising 248 subjects, the optimal number of clusters found is 4, which radar charts are reported in Fig. 16.

*[picture on PDF page 28]*

**Figure labels:**
- 123

P24

Pill

PS7

PD/SL vs PD+SL

PD:C1

PD: CO

ISL:C3

_SL:C1

PD: C3

SL:C2

PD:C2

SL: CO

PD:C4

PD+SL:C4

*[picture on PDF page 29]*

**Figure labels:**
- PD+ SL: CO
- PD+SL:C2
- PD+SL:C1
- PD+SL:C3

Theresults here presented show high agreement, with the results presented in Fig.4. In detail, Cluster 3, Cluster 1, and Cluster 0 here obtained, show NIHSS symptoms

*[picture on PDF page 29]*

***Fig. 16 Radar charts for the clusters obtained from RSC, considering the 248 ischemic patients from both cohorts, with NIHSS > 0. In the radar plots the lines represent (in blue) the minimum, (in green) the median, and (in red) the maximum of the NIHSS values inside the cluster***

*[picture on PDF page 29]*

**Figure labels:**
- 123

profile very similar to those shown in Fig.4. The only difference here is that the language cluster is included in Cluster 2. This is reasonable for several reasons. First, here the optimal number of clusters is k = 4, which is less respect the one found in the main manuscript k = 5, so if all the other three clusters are the same, of course, two clusters have to be merged together. Secondly, the language cluster is the only one that can be adsorbed within another cluster, specifically in the Motor Right Cluster C2, since lesions for these two domains are lateralized on the same side of the brain. Finally, the other sub-optimal number of clusters is k = 7; since there are many more clusters available, the language cluster (as shown in Cluster 4 Fig. 4) is retrieved again.

#### Appendix 5. Voxel-wise Results

The statistical significant lesions shown in Fig.5, are here visualized in Fig.17 at different slices.

*[picture on PDF page 30]*

***Fig. 17 Significant voxels found from the voxel-wise analysis with FWER at p = 0 . 05 for different slices. At the top ( A ) in orange, Cluster 0 (left motor deficits), in the middle ( B ) in green, Cluster 2 (right motor deficits) and at the bottom ( C ) in light blue, Cluster 4 (language deficits)***

*[picture on PDF page 30]*

**Figure labels:**
- 123

#### Appendix 6. Distances

Five different distances have been used to calculate the distributions of the pair-wise similarities, together with GDM. These five distances are the most used in clustering as discussed in [55]. Since Manhattan and Euclidean distances are not normalized in the 0-1 range, the pair-wise distance has been normalized with respect to the maximum distance found in the dataset. Results are reported in Fig. 18.

*[picture on PDF page 31]*

Acknowledgements The principal investigators wish to thank the patients who participated in the study for their time and effort. The authors wish to thank Prof. Livio Finos for valuable discussions on the interplay between clustering and statistical tests. The authors wish to thank the reviewers for their time, effort, and insights that were fundamental in assessing the organization and shaping the presentation of the present work.

Author Contributions Material preparation and data collection were performed by ALB, MC, SF, and LP. Data analysis was performed by MA, LFT, and AZ. Medical interpretation was performed by ALB, MC, and SF. Conceptualization from MA MC, LFT, and AZ. The first draft of the manuscript was written by LFT and AZ and all authors commented and edited previous versions of the manuscript. All authors read and approved the final manuscript.

*[picture on PDF page 31]*

**Figure labels:**
- 123

Funding Openaccess funding provided by Università degli Studi di Padova within the CRUI-CARE Agreement. This work was supported by the 'Department of excellence 2018-2022' initiative of the Italian Ministry of education (MIUR) awarded to the Department of Neuroscience-University of Padua, by the European Union's Horizon Europe research and innovation programme under grant agreement no 101137074 HEREDITARY, and by the STARS@UNIPD funding program of the University of Padova, Italy, through the project MEDMAX.

Data Availability The data that support the findings of this study are not openly available due to reasons of sensitivity and are available from the corresponding author upon reasonable request. Data are located in controlled access data storage at Padova Neuroscience Center.

Code Availability Code is available at https://github.com/MedMaxLab/nihss_clustering

#### Declarations

Ethics Approval For data of patients of the Saint Louis cohort, this research complies with all relevant ethical regulations. Written informed consent was obtained from all participants in accordance with the Declaration of Helsinki and procedures established by the Washington University in Saint Louis Institutional Review Board. All participants were compensated for their time. All aspects of this study were approved by the Washington University School of Medicine (WUSM) Internal Review Board. For data of patients of the Padua cohort, participants from this dataset provided written informed consent following the Declaration of Helsinki principles and procedures established by the Stroke Unit and Neurological Clinic of the Hospital of Padua. This is a retrospective and non-interventional study, that received approval from the Ethics Committee of the Azienda Ospedale Università Padova.

Conflict of Interest The authors declare no competing interests.

OpenAccess Thisarticle is licensed under a Creative Commons Attribution 4.0 International License, which permits use, sharing, adaptation, distribution and reproduction in any medium or format, as long as you give appropriate credit to the original author(s) and the source, provide a link to the Creative Commons licence, and indicate if changes were made. The images or other third party material in this article are included in the article's Creative Commons licence, unless indicated otherwise in a credit line to the material. If material is not included in the article's Creative Commons licence and your intended use is not permitted by statutory regulation or exceeds the permitted use, you will need to obtain permission directly from the copyright holder. To view a copy of this licence, visit http://creativecommons.org/licenses/by/4.0/.

#### References

- Strong K, Mathers C, Bonita R (2007) Preventing stroke: saving lives around the world. Lancet Neurol 6(2):182-187. https://doi.org/10.1016/S1474-4422(07)70031-5
- Feigin VL, Stark BA, Johnson CO, Roth GA, Bisignano C et al (2021) Global, regional, and national burden of stroke and its risk factors, 1990-2019: a systematic analysis for the global burden of disease study 2019. Lancet Neurol 20(10):795-820. https://doi.org/10.1016/S1474-4422(21)00252-0
- Nasreddine ZS, Phillips NA, Bédirian V, Charbonneau S, Whitehead V, Collin I, Cummings JL, Chertkow H (2005) The Montreal Cognitive Assessment, MoCA: a brief screening tool for mild cognitive impairment. J Am Geriatr Soc 53(4):695-699. https://doi.org/10.1111/j.1532-5415.2005. 53221.x
- DemeyereN,RiddochMJ,SlavkovaED,BickertonW-L,HumphreysGW(2015)TheOxfordCognitive Screen (OCS): validation of a stroke-specific short cognitive screening tool. Psychol Assess 27(3):883894. https://doi.org/10.1037/pas0000082
- Brott T, Adams HP, Olinger CP, Marler JR, Barsan WG, Biller J, Spilker J, Holleran R, Eberle R, Hertzberg V (1989) Measurements of acute cerebral infarction: a clinical examination scale. Stroke 20(7):864-870. https://doi.org/10.1161/01.STR.20.7.864

*[picture on PDF page 32]*

**Figure labels:**
- 123

- Lyden PD, Lu M, Levine SR, Brott TG, Broderick J (2001) A modified national institutes of health stroke scale for use in stroke clinical trials. Stroke 32(6):1310-1317. https://doi.org/10.1161/01.STR. 32.6.1310
- Ali Z, Zahra Zeynali K, Homa S, Maryam P, Sara P, Majid G, Mojdeh G (2012) The underlying factor structure of national institutes of health stroke scale: an exploratory factor analysis. Int J Neurosci 122(3):140-144. https://doi.org/10.3109/00207454.2011.633721. PMID: 22023373
- Lyden P, Claesson L, Havstad S, Ashwood T, Lu M (2004) Factor analysis of the national institutes of health stroke scale in patients with large strokes. Arch Neurol 61(11):1677-1680. https://doi.org/10. 1001/archneur.61.11.1677. Accessed 30 Aug 2022
- Corbetta M, Ramsey L, Callejas A, Baldassarre A, Hacker CD, Siegel JS, Astafiev SV, Rengachary J, Zinn K, Lang CE, Connor LT, Fucetola R, Strube M, Carter AR, Shulman GL (2015) Common behavioral clusters and subcortical anatomy in stroke. Neuron 85(5):927-941. https://doi.org/10.1016/ j.neuron.2015.02.027
- Bisogno AL, Favaretto C, Zangrossi A, Monai E, Facchini S, De Pellegrin S, Pini L, Castellaro M, Basile AM, Baracchini C, Corbetta M (2021) A low-dimensional structure of neurological impairment in stroke. Brain Commun 3(2):119. https://doi.org/10.1093/braincomms/fcab119
- Cheng B, Chen J, Königsberg A, Mayer C, Rimmele L, Patil KR, Gerloff C, Thomalla G, Eickhoff SB (2023) Mapping the deficit dimension structure of the national institutes of health stroke scale. EBioMedicine 87. https://doi.org/10.1016/j.ebiom.2022.104425
- Woo D, Broderick JP, Kothari RU, Lu M, Brott T, Lyden PD, Marler JR, Grotta JC (1999) Does the national institutes of health stroke scale favor left hemisphere strokes? Stroke 30(11):2355-2359. https://doi.org/10.1161/01.STR.30.11.2355
- Fink JN, Selim MH, Kumar S, Silver B, Linfante I, Caplan LR, Schlaug G (2002) Is the association of national institutes of health stroke scale scores and acute magnetic resonance imaging stroke volume equal for patients with right- and left-hemisphere ischemic stroke? Stroke 33(4):954-958. https://doi. org/10.1161/01.STR.0000013069.24300.1D
- Rajashekar D, Wilms M, MacDonald ME, Schimert S, Hill MD, Demchuk A, Goyal M, Dukelow SP, Forkert ND (2022) Lesion-symptom mapping with NIHSS sub-scores in ischemic stroke patients. Stroke Vasc Neurol 7(2):124-131. https://doi.org/10.1136/svn-2021-001091. https://svn.bmj.com/ content/7/2/124.full.pdf
- Chen X, Zhan X, Chen M, Lei H, Wang Y, Wei D, Jiang X (2012) The prognostic value of combined NT-pro-BNP levels and NIHSS scores in patients with acute ischemic stroke. Intern Med 51(20):28872892. https://doi.org/10.2169/internalmedicine.51.8027
- Sucharew H, Khoury J, Moomaw CJ, Alwell K, Kissela BM, Belagaje S, Adeoye O, Khatri P, Woo D, Flaherty ML, Ferioli S, Heitsch L, Broderick JP, Kleindorfer D (2013) Profiles of the national institutes of health stroke scale items as a predictor of patient outcome. Stroke 44(8):2182-2187. https://doi.org/ 10.1161/STROKEAHA.113.001255
- Fischer U, Arnold M, Nedeltchev K, Brekenfeld C, Ballinari P, Remonda L, Schroth G, Mattle HP (2005) NIHSS score and arteriographic findings in acute ischemic stroke. Stroke 36(10):2121-2125. https://doi.org/10.1161/01.STR.0000182099.04994.fc
- Sarraj A, Albright K, Barreto AD, Boehme AK, Sitton CW, Choi J, Lutzker SL, Sun C-HJ, Bibars W, Nguyen CB, Mir O, Vahidy F, Wu T-C, Lopez GA, Gonzales NR, Edgell R, Martin-Schild S, Hallevi H, Chen PR, Dannenbaum M, Saver JL, Liebeskind DS, Nogueira RG, Gupta R, Grotta JC, Savitz SI (2013) Optimizing prediction scores for poor outcome after intra-arterial therapy in anterior circulation acute ischemic stroke. Stroke 44(12):3324-3330. https://doi.org/10.1161/STROKEAHA.113.001050
- Vogt G, Laage R, Shuaib A, Schneider A (2012) Initial lesion volume is an independent predictor of clinical stroke outcome at day 90. Stroke 43(5):1266-1272. https://doi.org/10.1161/STROKEAHA. 111.646570
- Mihalik A, Chapman J, Adams RA, Winter NR, Ferreira FS, Shawe-Taylor J, Mourão-Miranda J (2022) Canonical correlation analysis and partial least squares for identifying brain-behavior associations: a tutorial and a comparative study. Biol Psychiatry Cogn Neurosci Neuroimaging 7(11):1055-1067. https://doi.org/10.1016/j.bpsc.2022.07.012
- Yang W-C, Lai J-P, Liu Y-H, Lin Y-L, Hou H-P, Pai P-F (2024) Using medical data and clustering techniques for a smart healthcare system. Electronics 13(1). https://doi.org/10.3390/electronics13010140
- Kim J-T, Kim NR, Choi SH, Oh S, Park M-S, Lee S-H, Kim BC, Choi J, Kim MS (2022) Neural network-based clustering model of ischemic stroke patients with a maximally distinct distribution of 1-year vascular outcomes. Sci Rep 12(1):9420. https://doi.org/10.1038/s41598-022-13636-w

*[picture on PDF page 33]*

**Figure labels:**
- 123

- Bates E, Wilson SM, Saygin AP, Dick F, Sereno MI, Knight RT, Dronkers NF (2003) Voxel-based lesion-symptom mapping. Nat Neurosci 6(5):448-450. https://doi.org/10.1038/nn1050
- DeMarco AT, Turkeltaub PE (2018) A multivariate lesion symptom mapping toolbox and examination of lesion-volume biases and correction methods in lesion-symptom mapping. Technical report, Wiley Online Library
- Krishnagopal S, Lohse K, Braun R (2022) Stroke recovery phenotyping through network trajectory approaches and graph neural networks. Brain Inform 9(1):13. https://doi.org/10.1186/s40708-02200160-w
- Park J-Y, Na HK, Kim S, Kim H, Kim HJ, Seo SW, Na DL, Han CE, Seong J-K (2017) Robust identification of Alzheimer's disease subtypes based on cortical atrophy patterns. Sci Rep 7(1):43270
- Blondel VD, Guillaume J-L, Lambiotte R, Lefebvre E (2008) Fast unfolding of communities in large networks. J Stat Mech Theory Exp 2008(10):10008
- Luxburg U (2007) A tutorial on spectral clustering. Stat Comput 17(4):395-416. https://doi.org/10. 1007/s11222-007-9033-z
- Aref S, Mostajabdaveh M (2024) Analyzing modularity maximization in approximation, heuristic, and graph neural network algorithms for community detection. J Comput Sci 78:102283
- Fonov V, Evans AC, Botteron K, Almli CR, McKinstry RC, Collins DL (2011) Unbiased average age-appropriate atlases for pediatric studies. NeuroImage 54(1):313-327. https://doi.org/10.1016/j. neuroimage.2010.07.033
- Walesiak M (1993) Statystyczna Analiza Wielowymiarowa W Badaniach Marketingowych. Wydawnictwo Akademii Ekonomicznej we Wrocławiu, Wrocław, Poland
- Jajuga K, Walesiak M, Bak A (2003) On the general distance measure. In: Schwaiger M, Opitz O (eds) Exploratory data analysis in empirical research. Springer, Berlin, Heidelberg, pp 104-109
- Ng A, Jordan M, Weiss Y (2001) On spectral clustering: analysis and an algorithm. Adv Neural Inf Process Syst 14
- Nascimento MCV, Toledo FMB, Carvalho ACPLF (2009) Consensus clustering using spectral theory. In: Köppen M, Kasabov N, Coghill G (eds) Advances in neuro-information processing. Lecture Notes in Computer Science. Springer, Berlin, Heidelberg, pp 461-468. https://doi.org/10.1007/978-3-64202490-0_57
- Fred ALN, Jain AK (2002) Data clustering using evidence accumulation. In: 2002 International conference on pattern recognition, vol 4, pp 276-2804. https://doi.org/10.1109/ICPR.2002.1047450
- Wild CJ, Seber GAF (1993) Comparing two proportions from the same survey. Am Stat 47(3):178-181. https://doi.org/10.2307/2684972. Full publication date: Aug., 1993
- Holm S (1979) A simple sequentially rejective multiple test procedure. Scand J Stat 6(2):65-70. Full publication date: 1979
- Westfall PH, Young SS (1993) Resampling-based multiple testing: examples and methods for P-value adjustment. John Wiley and Sons, New York, NY
- Yushkevich PA, Gao Y, Gerig G (2016) ITK-SNAP: an interactive tool for semi-automatic segmentation of multi-modality biomedical images. In: 2016 38th Annual International Conference of the IEEE Engineering in Medicine and Biology Society (EMBC). IEEE, pp 3342-3345
- Tustison NJ, Cook PA, Holbrook AJ, Johnson HJ, Muschelli J, Devenyi GA, Duda JT, Das SR, Cullen NC, Gillen DL et al (2021) The ANTsX ecosystem for quantitative biological and medical imaging. Sci Rep 11(1):9068
- Fruchterman TMJ, Reingold EM (1991) Graph drawing by force-directed placement. Softw Pract Exp 21(11):1129-1164. https://doi.org/10.1002/spe.4380211102
- DimmickSJ,FaulderKC(2009)Normalvariantsofthecerebralcirculation at multidetector CT angiography. RadioGraphics 29(4):1027-1043. https://doi.org/10.1148/rg.294085730. PMID: 19605654
- Khatri R, Qureshi MA, Chaudhry MRA, Maud A, Vellipuram AR, Cruz-Flores S, Rodriguez GJ (2019) The angiographic anatomy of the sphenoidal segment of the middle cerebral artery and its relevance in mechanical thrombectomy. Interv Neurol 8(2-6):231-241. https://doi.org/10.1159/000502545
- Rhoton A (2002) The supratentorial arteries vol 51-4, pp 53-120. Neurosurgery, Gainesville, FL
- Regenhardt RW, Bonkhoff AK, Bretzner M, Etherton MR, Das AS, Hong S, Alotaibi NM, Vranic JE, Dmytriw AA, Stapleton CJ, Patel AB, Leslie-Mazwi TM, Rost NS (2022) Association of infarct topography and outcome after endovascular thrombectomy in patients with acute ischemic stroke. Neurology 98(11):1094-1103. https://doi.org/10.1212/WNL.0000000000200034

*[picture on PDF page 34]*

**Figure labels:**
- 123

- Vitti E, Kim G, Stockbridge MD, Hillis AE, Faria A V (2022) Left hemisphere bias of NIH stroke scale is most severe for middle cerebral artery strokes. Front Neurol 13:1. https://doi.org/10.3389/fneur. 2022.912782
- Meyer BC, Hemmen TM, Jackson CM, Lyden PD (2002) Modified national institutes of health stroke scale for use in stroke clinical trials. Stroke 33(5):1261-1266. https://doi.org/10.1161/01.STR. 0000015625.87603.A7
- Meyer BC, Lyden PD (2009) The modified national institutes of health stroke scale: its time has come. Int J Stroke 4(4):267-273. https://doi.org/10.1111/j.1747-4949.2009.00294.x. PMID: 19689755
- Bisogno AL, Franco Novelletto L, Zangrossi A, De Pellegrin S, Facchini S, Basile AM, Baracchini C, Corbetta M (2023) The Oxford Cognitive Screen (OCS) as an acute predictor of long-term functional outcome in a prospective sample of stroke patients. Cortex 166:33-42. https://doi.org/10.1016/j.cortex. 2023.04.015
- Price CJ, Seghier ML, Leff AP (2010) Predicting language outcome and recovery after stroke: the PLORAS system. Nat Rev Neurol 6(4):202-210. https://doi.org/10.1038/nrneurol.2010.15
- Hope TMH, Parker Jones O, Grogan A, Crinion J, Rae J, Ruffle L, Leff AP, Seghier ML, Price CJ, Green DW (2015) Comparing language outcomes in monolingual and bilingual stroke patients. Brain 138(4):1070-1083. https://doi.org/10.1093/brain/awv020
- Sophie R, Rachel M, B, Louise L, Hayley W, Kate L, Storm A, Diego L, L-P, Andrea G-V, Alexander P, L, Thomas M H, H, David W, G, Jennifer T, C, Cathy J, P (2022) Better long-term speech outcomes in stroke survivors who received early clinical speech and language therapy: what's driving recovery? Neuropsychol Rehabil 32(9), 2319-2341
- Gajardo-Vidal A, Lorca-Puls DL, Team P, Warner H, Pshdary B, Crinion JT, Leff AP, Hope TMH, Geva S, Seghier ML, Green DW, Bowman H, Price CJ (2021) Damage to Broca's area does not contribute to long-term speech production outcome after stroke. Brain 144(3):817-832. https://doi.org/10.1093/ brain/awaa460
- Koch PJ, Rudolf LF, Schramm P, Frontzkowski L, Marburg M, Matthis C, Schacht H, Fiehler J, Thomalla G, Hummel FC, Neumann A, Münte TF, Royl G, Machner B, Schulz R (2023) Preserved corticospinal tract revealed by acute perfusion imaging relates to better outcome after thrombectomy in stroke. Stroke 54(12):3081-3089. https://doi.org/10.1161/STROKEAHA.123.044221
- Kumar V, Chhabra JK, Kumar D (2014) Impact of distance measures on the performance of clustering algorithms. In: Mohapatra DP, Patnaik S (eds) Intelligent computing, networking, and informatics. Springer, New Delhi, pp 183-190
- Yu Z, Li L, You J, Wong H-S, Han G (2012) Sc 3 : triple spectral clustering-based consensus clustering framework for class discovery from cancer gene expression profiles. IEEE/ACM Transactions on Computational Biology and Bioinformatics. 9(6):1751-1765. https://doi.org/10.1109/TCBB.2012. 108
- Strehl A, Ghosh J (2002) Cluster ensembles - a knowledge reuse framework for combining multiple partitions. J Mach Learn Res 3:583-617. https://doi.org/10.1162/153244303321897735

Publisher's Note Springer Nature remains neutral with regard to jurisdictional claims in published maps and institutional affiliations.

*[picture on PDF page 35]*

**Figure labels:**
- 123

#### Authors and Affiliations

Louis Fabrice Tshimanga 1,2,3 · Andrea Zanola 1,2 · Silvia Facchini 1 · Antonio Luigi Bisogno 1,2 · Lorenzo Pini 2,5 · Manfredo Atzori 1,2,4 · Maurizio Corbetta 1,2,5

- B Louis Fabrice Tshimanga louisfabrice.tshimanga@unipd.it
- B Andrea Zanola andrea.zanola@studenti.unipd.it
- 1 Department of Neuroscience, University of Padua, Padua 35128, Italy
- 2 Padova Neuroscience Center, University of Padua, Padua 35128, Italy
- 3 Department of Information Engineering, University of Padua, Padua 35128, Italy
- 4 Information Systems Institute, University of Applied Sciences Western Switzerland (HES-SO Valais), Sierre 3960, Switzerland
- 5 Veneto Institute of Molecular Medicine, Padua 35128, Italy

*[picture on PDF page 36]*

**Figure labels:**
- 123