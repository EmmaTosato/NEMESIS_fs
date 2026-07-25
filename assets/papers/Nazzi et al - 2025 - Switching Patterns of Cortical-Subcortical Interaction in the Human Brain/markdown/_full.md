### Systems/Circuits

### Switching Patterns of Cortical -Subcortical Interaction in the Human Brain

*[picture on PDF page 1]*

Alessandro Nazzi, 1 Chiara Favaretto, 2 Antonino Vallesi, 1 , 2 Maurizio Corbetta, 1 , 2 , 3 and Michele Allegra 1 , 4 1 Padova Neuroscience Center, University of Padova, Padova 35129, Italy, 2 Department of Neuroscience, University of Padova, Padova 35121, Italy, 3 Veneto Institute for Molecular Medicine, Padova 35129, Italy, and 4 Department of Physics and Astronomy ' Galileo Galilei ' , University of Padova, Padova 35131, Italy

It is still poorly understood how subcortical structures contribute to spontaneous infraslow brain activity. In fact, cortical spontaneous activity is often analyzed in isolation, possibly a result of a long-standing ' corticocentric bias ' . Here, we consider a large cohort of healthy human subjects of either sex (Human Connectome Project database), and we perform a dynamic functional connectivity (FC) analysis to investigate fl uctuations of cortical -subcortical interactions. Our analysis shows that FC shifts in the cortex and the subcortex are synchronized. Two core subcortical ' clusters ' comprising, respectively, limbic regions (hippocampus and amygdala) and subcortical nuclei (thalamus and basal ganglia) show a temporally fl exible coupling with cortical regions. Correspondingly, we consistently observe two recurring FC patterns (states). In State 1, limbic regions couple with the default mode network, and in State 2, they couple with sensorimotor networks. An opposite pattern is observed for the thalamus/basal ganglia. Our fi ndings suggest that cortical -subcortical interactions contribute to shaping whole-brain spontaneous FC patterns and underline the relevance of including the subcortex in descriptions of large-scale spontaneous brain activity.

Key words: dynamic functional connectivity; fMRI; Human Connectome Project; subcortical regions

### Signi fi cance Statement

Imaging of the whole brain at rest has shown that distant brain regions engage in transient interactions, giving rise to timevarying coupling patterns. Previous studies analyzing these complex dynamics have generally overlooked subcortical regions. In our study, we analyze functional MRI data of a large cohort of subjects from the Human Connectome Project, demonstrating that the alternation of different coupling patterns is a phenomenon involving the cortex and subcortex simultaneously. Limbic regions (hippocampus and amygdala) and subcortical nuclei (thalamus and basal ganglia) form coherent ' blocks, ' fl exibly changing their coupling with cortical regions. Our results suggest that cortical -subcortical interactions might contribute to shaping whole-brain spontaneous activity, emphasizing the importance of including subcortical structures in brain connectivity studies.

### Introduction

Even in the absence of external stimuli and overt behavior, the human brain thrives with activity (Raichle, 2010; Raichle, 2011). As revealed by resting-state fMRI functional connectivity (FC) studies, a key feature of this spontaneous activity is the wellde fi ned spatiotemporal organization of its fl uctuations. This phenomenon has been intensively analyzed at the cortical level,

Received Sept. 3, 2024; revised June 17, 2025; accepted July 14, 2025.

Author contributions: A.V., M.C., and M.A. designed research; A.N., C.F., A.V., and M.A. performed research; A.N., C.F., A.V., and M.A. analyzed data; A.N., C.F., and M.A. wrote the paper.

A.N. and M.C. received support from the Fondazione Cassa di Risparmio di Padova e Rovigo (CARIPARO), Grant Agreement Number 55403. M.C. and M.A. received support from the European Union, ' ERC-2022-SYG NEMESIS, ' Grant Number 101071900. M.C. received support from the Italian Ministry of Health for ' Brain connectivity measured with high-density electroencephalography: a novel neurodiagnostic tool for stroke ' (NEUROCONN; RF-2018-1236689) and ' Eye-movement dynamics during free viewing as biomarker for assessment of visuospatial functions and for closedloop rehabilitation in stroke ' (EYEMOVINSTROKE; RF-2019-12369300); European Research Executive Agency (REA; Grant Number 860563) ' European School of Network Neuroscience (euSNN) ' ; Horizon 2020 SC5-2019-2 (Grant No. 869505) ' Visionary nature based Actions for enhancing Resilience in Cities (VARCITIES) ' ; and HORIZON- INFRA-2022 SERV (Grant leading to a well-established paradigm: activity fl uctuations re fl ect the existence of a set of canonical ' intrinsic networks ' (Uddin et al., 2019). In comparison, the subcortical level has received much less attention, and cortical -subcortical interactions remain relatively understudied. A few studies have concentrated on spatial aspects of cortical -subcortical interaction: focusing on single subcortical structures, such as the thalamus Number 101147319) ' EBRAINS 2.0: A Research Infrastructure to Advance Neuroscience and Brain Health. ' M.A. received support from the University of Padova, Department of Physics and Astronomy ' Galileo Galilei ' , through the DOR grant "E ff etti fototermici di nanoparticelle d ' oro (AuNPs) irradiate con luce NIR. Views and opinions expressed are those of the author(s) only and do not necessarily re fl ect those of the European Union or the European Research Council Executive Agency. Neither the European Union nor the granting authority can be held responsible for them. No funders played any role in the study design, data collection and analysis, decision to publish, or preparation of the manuscript.

The authors declare no competing fi nancial interests.

Correspondence should be addressed to Michele Allegra at michele.allegra@unipd.it.

This paper contains supplemental material available at: https://doi.org/10.1523/JNEUROSCI.1855-24.2025 https://doi.org/10.1523/JNEUROSCI.1855-24.2025

Copyright © 2025 the authors

(Hwang et al., 2017), hippocampus (Blessing et al., 2016), or cerebellum (Buckner et al., 2011), they showed that all of these structures can be subdivided into subregions having di ff erent FC patterns with the cortex. However, as these works concentrated on static rather than time-varying FC (Hutchison et al., 2013; Preti et al., 2017; Lurie et al., 2020), the temporal aspect was essentially unexplored. The static picture of subcortical -cortical connectivity may hide a dynamic landscape where subcortical structures couple fl exibly with cortical regions and vice versa. Evidence in favor of this hypothesis was provided by Favaretto et al. (2022), who investigated the fl uctuations in subcortical and cortical -subcortical FC in stroke patients. This study observed synchronized fl uctuations in cortical and subcortical FC and identi fi ed two main ' blocks ' of highly synchronized subcortical structures alternating between di ff erent patterns of connectivity with cortical networks.

Here we analyze dynamic cortical -subcortical interactions in a wide cohort of healthy young participants from the Human Connectome Project (HCP; Smith et al., 2013). The large sample size ( N =1,200) and fi ne temporal resolution (0.71 s) allow for a statistically reliable characterization of time-varying FC, reducing instabilities due to individual variability, sampling variability, and artifacts. By combining several data reduction steps, including principal component analysis (PCA) and clustering, our analysis concentrates on a leading, global modulation of cortical -subcortical connectivity. This phenomenon has several facets, con fi rming the main fi ndings of Favaretto et al. (2022). We observe a leading component of subcortical dynamic connectivity, explaining a sizable fraction of the total variance. This component naturally splits subcortical structures into two groups characterized by internal synchronization and dynamic links with cortical networks. These groups of subcortical structures fl exibly switch their connectivity with cortical networks, giving rise to di ff erent global connectivity states or ' dynamic functional states ' (DFSs). These fi ndings are robust with respect to details of the analysis pipeline used, including speci fi c choices of cortical -subcortical parcellation. We investigate the relationship between these dynamic connectivity shifts and behavior, testing the link between the individual expression of DFSs and individual cognitive scores.

### Materials and Methods

HCPdataset. The HCP ' s dataset included 1,206 human participants, who underwent neuroimaging sessions and a large battery of behavioral tests. Of the 1,206 participants, 1,096 were scanned with a modi fi ed 3 T Siemens ' Connectome Skyra ' scanner at the Washington University, using a standard 32-channel Siemens receive head coil and a speci fi cally designed ' body ' transmission coil. Pulse sequence included slice-accelerated multiband acquisition with a multiband factor of 8, spatial resolution of 2 mm isotropic voxels, and TR=0.7 s. Participants underwent two 15 min scanning sessions with opposite phase encoding directions (L/R and R/L) while fi xating on a crosshair. We included in the analysis only participants that were scanned both in the L/R and in the R/L direction for 840 s ( n =1,078; n =583 males; n =495 females). Weusedpreprocessed data provided by the HCP. The HCP ' s preprocessing pipeline is divided into two distinct protocols (Glasser et al., 2013): one applied entirely on the volume data involving temporal fi ltering and denoising and the second one regarding mapping the data to cortical surfaces and subcortical gray-matter domains using the Connectivity Informatics Technology Initiative fi le format. One promising approach for removing structured artifacts involves denoising each 15 min rfMRI scan with the independent component analysis (ICA)-based tool called FSL ' s MELODIC. This tool, paired with the FMRIB ' S ICA-based X-noise fi lter, allows decomposing the data into multiple components (comprising a spatial map and a corresponding time course) and to classify them in order to subsequently regress out the confounding ones. Additionally, in line with Favaretto et al. (2022), we included two supplementary preprocessing steps: signals were band-passed in the frequency band [0.009, 0.08 Hz] with a Butterworth fi lter of Order 1, and the mean GM signal was linearly regressed [global signal regression (GSR)].

Parcellation. For our initial analysis, we used the same parcellation used in Favaretto et al. (2022). Time series were projected on the cortical surface of each subject divided according to the resting-state FC (RSFC) boundary mapping developed by Gordon et al. (Gordon et al., 2016). This technique leverages abrupt transitions in RSFC to noninvasively identify the borders separating cortical areas. The original parcellation includes 333 regions, but all regions with <20 vertices ( ∼ 50 mm 2 ) were excluded due to low signal-to-noise ratio (SNR). The remaining 324 regions were further reduced to 71 by a clustering procedure (Favaretto et al., 2022) and grouped into eight resting-state networks (RSNs): visual network (VIS), sensory motor hand -mouth network (SMN), auditory network (AUD), control or cingulo-opercular network (CON), ventral attention network (VAN), dorsal attention network (DAN), frontoparietal network (FPN), default mode network (DMN), and limbic network (LIM). We also considered 19 subcortical and cerebellar regions derived from the FreeSurfer subcortical atlas (Fischl et al., 2002; Fischl, 2012). Expanding the initial analysis to aid the investigation of cortical -subcortical interactions, we used a di ff erent parcellation of the subcortex (Tian et al., 2020), which provides four di ff erent parcellations with an increasing degree of granularity. The coarsest parcellation includes eight bilateral regions, while the most fi ne-grained one comprises 27 bilateral regions (see Supplementary Table 2 of Tian et al., 2020). This subcortical cartography was based on RSFC gradients: region boundaries were identi fi ed on the basis of strong shifts in FC gradients. To analyze the cerebellum, we considered the cerebellar parcellation by Buckner et al. (2011). This parcellation was obtained by considering the RSFC between the cerebellum and the cortex. In particular, the cortex was divided into seven RSNs (Yeo et al., 2011), and the FC between each voxel in the cerebellum and each cortical RNS was assessed; based on the maximal FC, cerebellum voxels were assigned to one of seven clusters based on their maximum correlation with cortical regions. Finally, we considered an anatomical parcellation of the thalamus ( ' Morel atlas ' ) provided by Krauth et al. (2010). This map was obtained from detailed histological maps of the thalamus.

Sliding-window FC. FC dynamics were investigated through slidingwindow temporal correlation, one of the most straightforward approaches for dynamic FC (dFC) analysis. Similarly to a moving average function, this technique computes a succession of pairwise Fisher z -transformed Pearson ' s correlation matrices, relative to windows of a given width. These correlation matrices are informative of the timevarying FC between the networks considered in the brain parcellation of choice. Importantly, to compensate for the di ff erence in TR durations between the WU and the HCP datasets (TR = 2 s in WU vs TR = 0.7 s in HCP), we downsampled HCP ' s time series to one-third of the points. Then, from the downsampled time series, we extracted windows lasting ∼ 1 min (28 TRs), with a sliding step of 3 TRs ( ∼ 2 s). Window-length choice represents a critical point in dynamical FC analysis (Leonardi and Van De Ville, 2015). Namely, having windows shorter than the analyzed components ' wavelengths might cause spurious fl uctuations in dFC. Similarly, too long windows might prevent legitimate functional fl uctuations to be identi fi ed. Thus, we selected our sliding window ' s width on the basis of previous results (Favaretto et al., 2022). Additionally, each correlation matrix was approximated by projecting it onto the corresponding eigenspace, de fi ned by the fi rst eigenvector vi . Since eigenvectors are de fi ned less than the sign, we averted this problem by translating each eigenvector into the reconstructed square matrix vi × v t i , saving the vectorized upper-triangular part alone, avoiding redundancies in the data. Ultimately, all the resulting vectors were concatenated across windows, subjects, and time points.

Definition of DFSs. The last step for de fi ning DFSs required the application of a timewise K -means clustering procedure with correlation distance. K -means is a clustering technique, aiming to partition an N -dimensional population into k clusters based on a sample. Each observation belongs to the cluster with the nearest mean (e.g., cluster centroid), serving as a prototype of the cluster. In this case, this procedure resulted in a set of fi ve DFSs (all the operations described up to now are summarized in Fig. 1 b ). This algorithm minimizes within-cluster variances, taking into account a range of possible distance metrics. For this analysis, we employed the correlation distance, which is de fi ned as follows:

d ( x , c ) = 1 -( x -x )( c -c ) ′ /NameMe.129/NameMe.129/NameMe.129/NameMe.129/NameMe.129/NameMe.129/NameMe.129/NameMe.129/NameMe.129/NameMe.129/NameMe.129/NameMe.129/NameMe.129/NameMe.129/NameMe.129/NameMe.129 ( x -x )( x -x ) ′ √ /NameMe.129/NameMe.129/NameMe.129/NameMe.129/NameMe.129/NameMe.129/NameMe.129/NameMe.129/NameMe.129/NameMe.129/NameMe.129/NameMe.129/NameMe.129/NameMe.129 /NameMe.129 ( c -c )( c -c ) ′ √ ,

where x is an observation and c is a centroid. In addition, x = 1 p ∑ p j = 1 xj ( ) 1 /shortrightarrow p , c = 1 p ∑ p j = 1 cj ( ) 1 /shortrightarrow p , and 1 /shortrightarrow p is a row vector of p ones. Furthermore, the optimal K value was deducted by comparing the clustering performances with di ff erent numbers of clusters (from 2 to 6), with respect to a metric for interpreting and validating the consistency within clusters of data: the Silhouette value. This parameter is a measure of the fi tness of a certain data point for its cluster of belonging, compared with other clusters. This metric ranges from -1, indicating the lowest fi tness, to +1, indicating the highest fi tness. Then, for a certain data point i [ CI , where CI is the cluster of belonging, the Silhouette value is de fi ned as follows:

s ( i ) = b ( i ) -a ( i ) max{ a ( i ), b ( i )} , if | CI | . 1,

where a ( i ) is the mean distance between i and all the other data points belonging to the same cluster, while b ( i ) is the smallest mean distance between i and all the data points belonging to other clusters. Additionally, the clustering procedure associated each sliding window with a speci fi c DFS, so that for each subject we had a discrete time series x ( n ) (with n ranging from 1 to 746), where each value represented the active DFS for that time window. These time courses allowed us to evaluate three dynamical measures for each state, namely, fraction time f k , being the percentage of times during which a state is active:

f k = # ( x ( n ) = k ) 746 , k = 1, . . . , K ,

where #( a ) stands for the number of occurrences of the condition a . The dwell time l k , being the average length of periods in which each state remains continuously active, is calculated as follows:

l k = 1 | Lk | ∑ | Lk | i = 1 Lk [ i ],

where Lk is the set having cardinality | Lk |, with each element Lk [ i ] representing the length of a period of continuous activity of state k . The transition probability DFS i . DFS j , from DFS i to DFS j , where

DFS i . j = # ( x ( n = i ) ^ x ( n + 1) = j ) # ( x ( n ) = x ( n + 1)) ,

being the ratio between the number of jumps from DFS i to DFS j over the total amount of jumps.

Phase randomization. Phase randomization (PR) is a common framework for generating null data extensively employed in physics (Prichard and Theiler, 1994). Recently, it has also been applied to fMRI data for studying dFC (Allen et al., 2014; Hindriks et al., 2016). The PR procedure performs a discrete Fourier transform (DFT) of the original time series, adds a uniformly distributed random phase to each frequency, and then performs the inverse DFT to create surrogate data. Crucially, the random phases are created individually for each frequency, but they remain consistent across various regions of the brain.

Adding the same random phase to the same frequency components of the RSNs preserves the static FC and the lagged cross-covariance structure in the surrogates (in addition, also the mean, variance, and power spectrum of the signals are preserved). This class of surrogates corresponds to the null hypothesis that time series are generated by a linear, stationary Gaussian process (Liégeois et al., 2017).

Behavioral analysis. The HCP provides a large array of subject measures (SMs; i.e., individual measures for each participant), covering demographic, psychometric, and behavioral information. The full list of SMs with a detailed description can be found in the HCP 1200 Manual. SMs comprise demographics (e.g., education, employment, income); physical and mental health history, present and past use of tobacco, alcohol, marijuana, and other drugs; symptoms/history of eating disorders, depression, psychosis, antisocial personality, obsessive -compulsive disorder, post-traumatic stress, social phobia, and panic attack; Folstein MiniMental State Exam; Pittsburgh Sleep Quality Index; Parental Psychiatric and neurologic history; handedness assessment; menstrual cycle and other endocrine information in females; urine drug assessment, breathalyzer test, blood test; NIH Toolbox behavioral tests (which includes 19 subdomains within the broad domains of cognitive, motor, emotional, and sensory functions); and Non-NIH Toolbox behavioral tests (color vision, contrast sensitivity, personality, attention, episodic memory, fl uid intelligence, emotion processing, spatial processing, and delay discounting).

Starting from a subset of 158 of such SMs, Smith et al. (2015) performed a canonical correlation analysis (CCA) linking the SMs with the individual static FC matrices, which resulted in a principal axis of FC -SM covariation. They list 59 SMs with a large loading onto the principal axis. The 59 SMs include demographics and scores of tests for fl uid and crystallized intelligence, dexterity and endurance, language, vision, taste, processing speed, life function, impulsivity and aggressiveness, and drug abuse. The list of all 59 SMs with their identi fi er is reported in Table S1.

We replicated the analysis by Smith et al. (2015) using the same methodology. However, we used a larger cohort of subjects from the HCP database (i.e. 1,206 vs 461 HCP subjects), and we computed connectivity matrices in the Schaefer100 + FreeSurfer cortical -subcortical parcellation. The raw behavioral measures for the selected 158 SMs were initially subject to a rank-based inverse Gaussian transformation to enforce Gaussianity, avoiding the in fl uence of potential outliers. Additionally, 17 potential confound SMs (including head motion) were regressed out from the behavioral data (for a complete list, see Smith et al., 2015). To account for missing data, a subjects × subjects covariance matrix was estimated by ignoring missing values for either subject, which was then projected onto the nearest valid positive-de fi nite covariance matrix. Finally, the eigenvalue decomposition was computed onto the resulting covariance matrix, and the fi rst 100 eigenvectors were kept. Regarding connectivity data (referred to as N ), we computed subject-wise partial temporal correlation between the time series of each region keeping only the upper-triangular part of each correlation matrix. The resulting vectors were concatenated across subjects and the Pearson ' s correlation values transformed into z statistics with Fisher ' s transformation. Then, this connectivity matrix was demeaned column-wise, globally variance-normalized, and the same confound SMs were regressed out. Lastly, a PCA was computed on N , keeping the fi rst 100 components. The fully preprocessed behavioral and connectivity matrices ( S and N , respectively) were ultimately fed into a CCA, identifying 100 components aiming to optimize demixing matrices A and B to ensure that the resulting matrices U = N ∗ A and V = S ∗ B were highly similar to each other.

Granziol and Cona (2024) analyzed 38 SMs re fl ecting cognitive and processing aspects, mental health and behavioral problems, personality characteristics, and substance use frequencies. The 38 SMs, with their unique identi fi ers as provided by the HCP consortium, are reported in Table S1. Exploratory graph analysis (EGA; Golino and Epskamp, 2017) was used to cluster these SMs into ' communities ' or clusters of SMs characterized by high correlation. Brie fl y, EGA works with the following steps: (1) the graphical LASSO algorithm (Friedman et al., 2008)

was used to fi nd partial correlations between the 38 SMs, and (2) the walktrap community detection algorithm (Pons and Latapi, 2005) is applied to fi nd clusters/communities. Seven domains were identi fi ed (mental health, substance abuse, low cognitive functions, high cognitive functions, pain, delay discounting, and externalizing problems).

We replicated the analysis by Granziol and Cona (2024) using the graphical LASSO algorithm with sparsity 0.5, as implemented in the R package ' glasso ' ; we then applied the walktrap community detection as implemented in the R ' igraph ' package. We computed network loadings for each measure as follows (Christensen and Golino, 2019): starting from the partial correlation matrix Wij , where i , j = 1, · · · , NSM , we considered all SMs assigned to factor c and computed loading as L ic = ∑ i [ c | Wij | , and then we normalized loadings as zic = Lic / S j Ljc . Given the set of SMs for all subjects, Xik where k = 1, . . . , N subjects, we computed community/cluster scores for each subject as Sck = ∑ i zicXik .

Ultimately, we assessed the impact of variability in dFC patterns via a generalized linear model (GLM) in an exploratory analysis considering di ff erent predictors [fraction times, dwell times, P jump(RSN1 | RSN2), and individual DFSs] and the two behavioral scores described above (i.e., Smith ' s behavioral mode and Granziol ' s 7 communities scores) as alternative dependent variables.

### Results

### Analysis overview

We considered a large sample of healthy human subjects ( n = 1,078) from the HCP (Smith et al., 2013; Van Essen et al., 2013). For each subject, we extracted average BOLD time series for cortical regions and subcortical/cerebellar regions. We computed FC matrices for sliding windows with a 60 s duration, projected them onto the space spanned by the principal eigenvector, and vectorized them; we then concatenated together all time windows and subjects and performed a K -means clustering over windows. The resulting clusters are termed ' DFSs. '

In Figure 1 a we show the average BOLD signal of two cortical networks (sensorimotor and default mode) and two subcortical regions (thalamus and hippocampus). Starting from slidingwindow FC (swFC), we extract the DFSs (Fig. 1 b ), which correspond to di ff erent patterns of cortical -subcortical interaction. This is evident in Figure 1 d , where we show dynamic variations of FC associated with the di ff erent DFSs. In DFS1, the DMN (considered to be the ' task-negative ' network) correlates positively with the hippocampus and negatively with the thalamus, while the opposite pattern is observed for the sensorimotor network (SMN). In DFS2, this trend is reversed, as task-negative regions correlate negatively with the hippocampus and positively with the thalamus, while the opposite pattern is observed for task-positive regions (DAN and primary networks).

### Existence of two groups of subcortical regions

The fi rst principal eigenvector v can be thought of as a ' compact ' representation of the windowed FC. The temporal evolution of v across windows thus captures dynamic changes in FC. We performed a PCA on the subcortical projection of v (i.e., entries of v corresponding to subcortical regions). This allows identifying coordinated ' fl uctuations ' in windowed FC across time. By this approach, Favaretto et al. (2022) identi fi ed two groups of subcortical regions exhibiting anticorrelated FC fl uctuations: a fi rst group ( ' subcortical cluster 1, ' ' SC1 ' ) comprising the hippocampus and amygdala and a second group ( ' subcortical cluster 2, ' ' SC2 ' ) comprising the thalamus, basal ganglia, and cerebellum.

We used a combined parcellation including eight bilateral subcortical regions (Tian et al., 2020) as well as seven bilateral cerebellar regions associated (via strong values of static FC) with one of the classical seven cortical RSNs (Buckner et al., 2011). We identi fi ed a principal component (PC1) explaining

32% of the total variance (Fig. 2 c ). Subsequent PCs explained, respectively, 13, 8, and 6% of the variance, while all components beyond the fourth explained <4% of the variance; 13 components are required to explain 90% of the variance (Fig. 2 a ). PC1 loaded positively (bilaterally) on the anterior thalamus, putamen, caudate, and most cerebellar subregions, with strongest e ff ects on the cerebellar subregion associated with the DAN; it loaded negatively on the hippocampus and amygdala (bilaterally). Weak e ff ects were observed in the globus pallidus, nucleus accumbens, and the cerebellar subregion associated with the DMN (Fig. 2 c ). A volumetric brain representation of the component is given in Figure 2 d .

We performed hierarchical clustering based on the PC loadings on the fi rst fi ve principal components. We clearly obtained a major split between a group comprising the thalamus, basal ganglia, and the part of the cerebellum associated with taskpositive networks (DAN, SMN) and a group comprising the hippocampus and amygdala. The part of the cerebellum associated with DMN and CON was relatively isolated. This fi nding is in strong agreement with the cluster division obtained by Favaretto et al. (2022). Consistently, we also term ' SC1 ' the group comprising the anterior thalamus, putamen, caudate, and most of the cerebellum and ' SC2 ' the group comprising the hippocampus and amygdala. Thus, the dimension corresponding to PC1 captures a key modulation of subcortical connectivity, explaining a large (35%) fraction of variance and distinguishing two main groups of subcortical regions. The remaining 65% of the variance is explained by more fi ne-grained patterns.

These results do not depend on the speci fi c parcellation used. In the Supplementary Materials, we display consistent results obtained with other parcellations, including the FreeSurfer parcellation (Fischl, 2012), a more fi ne-grained parcellation with 28 bilateral subcortical regions (Tian et al., 2020), and a fi ner subdivision of the thalamus (Krauth et al., 2010). In all cases, we found a main PC explaining at least 25% of the variance, aligning with the above-described PC1 and yielding a similar split of subcortical/cerebellar regions (Fig. S1). In the FreeSurfer parcellation, we only observed a stronger alignment of the nucleus accumbens with SC2. The Tian parcellation with 28 bilateral regions did not provide a more nuanced picture than the parcellation with 8 regions. When using the Morel parcellation of the thalamus (Krauth et al., 2010), PC1 loaded positively on the medial, lateral, and anterior regions of the thalamus and more weakly on the posterior regions and the additional nuclei.

By performing analysis in single subjects, we obtained a PC with an average correlation of 0.73 with the group-level PC. Results for an exemplar subject are reported in Figure S4 a . In summary, this component is very robust and found independently of the speci fi c subcortical parcellation used.

### Coordination of cortical and subcortical connectivity shifts

Next, we investigated the general coordination between cortical and subcortical connectivity shifts. We fi rst investigated whether large shifts in cortical connectivity were associated with equally strong shifts in subcortical connectivity and vice versa. Approximating the FC with its fi rst eigenvector v , we computed the average windowed FC within each RSN and computed an RSN-wide FC change as the di ff erence between two successive windows (Favaretto et al., 2022). We identi fi ed an ' FC jump ' whenever this di ff erence fell in the upper tail of the corresponding distribution ( fi fth percentile). Finally, we computed conditional probabilities P jump(RSN1 | RSN2) of observing an FC

*[picture on PDF page 5]*

**Figure labels:**
- a
- BOLD signal
- BOLD signal + DFSs
- SMN
- DMN
- mmM
- NWMMwwM
- wmwwNW
- THA
- HIP
- 50
- 100
- 150
- 200
- 250
- time
- b
- DFC (t)
- v(t)
- v(t) * v(t)T
- ()∆
- DFS1
- DFS2
- K-means clustering
- dynamic FC
- FC>0
- FC<0
- SMN-
- DMN-

time

***Figure 1. Analysis overview. This work focuses on dynamic cortical -subcortical interactions. Two groups of subcortical regions (a ' limbic ' group comprising hippocampus/amygdala and a ' subcortical nuclei ' group comprising thalamus/basal ganglia) couple dynamically with cortical regions, showing fl exible connectivity with task-positive regions and task-negative regions. Connectivity switches are well captured by DFSs, i.e., recurring patterns of whole-brain (cortical -subcortical) connectivity. a , Average, BOLD signal from four networks: the sensorimotor network, the DMN, the limbic group, and the subcortical nuclei group for an example subject. For the sake of visualization, we represented these networks on the brain with typical seed regions associated with each of them (the M1 regions for the SMN, the inferior parietal lobule for the DMN, the thalamus for the fi rst subcortical group, and the hippocampus for the second subcortical group). b , Overview of the analysis pipeline. swFC is computed using sliding windows of 60 s duration (with a step of 3 s). Then, each swFC matrix is approximated as v i × v t i , by projecting on the leading eigenspace de fi ned by the fi rst eigenvector v i . The upper-triangular part of these swFC matrices is vectorized and concatenated across windows and subjects, in order to fi nally apply a timewise K -means clustering algorithm with correlation distance to identify a set of recurring swFC patterns or DFSs. Each sliding window is assigned to a speci fi c DFS. c , BOLD signal of four key regions (same as in panel a ), with di ff erent colors highlighting the DFS of the corresponding window (the window centered at that point). Two DFSs capture the dynamic coupling between subcortical and cortical regions. In particular, in DFS1 the hippocampus couples positively with the DMN and negatively with the sensorimotor network, while the thalamus shows an opposite trend. In DFS2, this pattern of subcortical -cortical connectivity is reversed. d , Time courses of the subcortical -cortical swFC, shaded with di ff erent colors according to the corresponding DFSs. The dynamic coupling described above can be noted: switching trends of subcortical -cortical connectivity are summarized graphically in the brain plots on the right.***

jump in RSN1, given that a jump is observed in RSN2. Synchronization between cortical and subcortical jumps re fl ects into higher-than-chance conditional probabilities of cortical given subcortical jumps and vice versa. All conditional probabilities were >50% (Fig. 3 a ), implying that FC jumps are strongly synchronized among all networks, cortical and subcortical alike. Notably, conditional probabilities involving cortical networks and subcortical groups were always >60%. Those involving simultaneous jumps between SC1 (basal ganglia/thalamus/cerebellum) and cortical networks are among the strongest conditional probabilities.

Analogously to our previous analysis, we performed PCA on v , this time including both cortical and subcortical regions. This allows identifying coordinated FC fl uctuations among the cortex and subcortex. We found two main PCs explaining, each, roughly 20% of the variance. The third PCs explained 8% of the variance, while all components beyond the third explained <4% of the variance; 53 components were required to explain 90% of the variance (Fig. 3 b ). The fi rst PC (Fig. 3 c ) loaded positively (bilaterally) on the DAN, the control network (CON), and SC1; it loaded negatively on the DMN and LIM and SC2 and had weaker and/or inconsistent (mixed positive/negative) weights on other cortical networks. The second PC (Fig. 3 d ) loaded positively (bilaterally) on the DMN, the FPN, and most of SC1; it loaded negatively on the SMN, AUD, and SC2 and had weaker and/or inconsistent (mixed positive/negative) weights on other cortical networks. Notably, the subcortical part of both PCs was strongly correlated with the previously identi fi ed leading component of dynamical subcortical connectivity ( R =0.87; R =0.6). This is a further indication that subcortical connectivity shifts are related to cortical shifts: the two whole-brain PCs depict variations in coupling of the two subcortical blocks with di ff erent cortical networks.

*[picture on PDF page 6]*

**Figure labels:**
- a
- b
- Explained variance
- Hierarchical clustering across PC #
- 100
- cumulative
- raw
- 80
- Exp.
- 60
- Var.
- 40
- 20
- 0
- 5
- 10
- 15
- CER VAN
- R CER VAN
- R CER DMN
- PC #
- C
- Principal Component of
- d
- subcortical dFC
- L aTHA
- 0.2163
- 0.3
- -0.2
- 0.2
- L pTHA
- 0.03879
- L CAU
- 0.1839
- L PUT
- 0.2111
- 0.25
- L GP
- 0.08443
- L HIP
- -0.1887
- L AMY
- -0.1563
- L NAc
- 0.1157
- R aTHA
- 0.2089
- R pTHA
- 0.0549
- 0.15
- R CAU
- 0.1516
- R PUT
- 0.2004
- R GP
- 0.05031
- 0.1
- R HIP
- -0.1848
- R AMY
- -0.1508
- R NAC
- 0.08639
- 0.05
- L CER VIS
- 0.03929
- L CER SMN
- 0.1503
- L CER DAN
- 0.2942
- L CER VAN
- 0.3165
- L CER LIM
- 0.1644
- L CER CON
- 0.2697
- -0.05
- L CER DMN
- 0.08033
- R CER VIS
- 0.07569
- R CER SMN
- 0.1659
- -0.1
- R CER DAN
- 0.2746
- 0.2997
- R CER LIM
- 0.1645
- -0.15
- R CER CON
- 0.2595
- 0.07845

### DFSs

To fi nd DFSs, we performed K -means clustering for increasing values of K (the total number of clusters), using the GordonLaumann +FreeSurfer parcellation (Fischl et al., 2002; Fischl, 2012; Gordon et al., 2016). As typical for K -means, increasing K leads to the survival of the most robust clusters and the splitting of the dimmer into subclusters. The ' optimal ' number of clusters should correspond to the largest value of the Silhouette coe ffi cient. This criterion suggests that the optimal number of clusters is K =2 (Fig. S2). Unsurprisingly, the two states found at K =2 are also the two most stable states across all choices of K (Fig. S2). The states found for K =5 qualitatively align with the K =5 states of Favaretto et al. (2022). A detailed comparison is presented in Figure S3.

***Table 1. Region labels***

| Region short name | Region name |
|---|---|
| Tian subcortical parcellation |   |
| AMY | Amygdala |
| lAMY | Lateral amygdala |
| mAMY | Medial amygdala |
| BST | Brainstem |
| CAU | Caudate nucleus |
| CAU-VA | Ventral anterior caudate |
| CAU-DA | Dorsal anterior caudate |
| CAU-b | Caudate body |
| CAU-t | Caudate tail |
| CER | Cerebellum |
| DIE | Ventral diencephalon |
| GP | Globus pallidus |
| aGP | Anterior globus pallidus |
| pGP | Posterior globus pallidus |
| HIP | Hippocampus |
| HIP-hm1 | Hippocampus head medial subdivision 1 |
| HIP-hm2 | Hippocampus head medial subdivision 1 |
| HIP-hl | Hippocampus head lateral subdivision |
| HIP-b | Hippocampus body |
| HIP-t | Hippocampus tail |
| NAc | Nucleus accumbens |
| NAc-s | Nucleus accumbens shell |
| NAc-c | Nucleus accumbens core |
| PUT | Putamen |
| PUT-VP | Ventral posterior putamen |
| PUT-DP | Dorsal posterior putamen |
| THA | Thalamus |
| aTHA | Anterior thalamus |
| THA-VAip | Inferior ventroanterior thalamus, posterior division |
| THA-VAia | Inferior ventroanterior thalamus, anterior division |
| THA-VAs | Superior ventroanterior thalamus |
| THA-DAm | Medial dorsal anterior thalamus |
| THA-DAl | Lateral dorsal anterior thalamus |
| pTHA | Posterior thalamus |
| THA-DP | Dorsoposterior thalamus |
| THA-VPm | Medial ventroposterior thalamus |
| THA-VPl | Lateral ventroposterior thalamus |
| Morel thalamus parcellation |   |
| mTHA | Medial thalamus |
| pTHA | Posterior thalamus |
| rnTHA | Red nucleus |
| mttTHA | Mammillothalamic tract |
| SThTHA | Subthalamic nucleus |

In Figure 4, a and b , we show the K =2 states displayed in a matrix and in a brain surface/volume representation, respectively. DFS1 closely resembles the typical pattern of healthy static FC. It displays high DAN/DMN segregation, while SC2 (limbic) couples positively with DMN and negatively with DAN. DFS2 presents a negative coupling between cognitive networks (DAN, VAN, CON, FPN, DMN, LIM) and primary networks (VIS, AUD, SMN). At the same time, SC1 (limbic) couples negatively with DMN and positively with primary networks, while SC2 (thalamus/basal ganglia/cerebellum) displays the opposite pattern. These two states capture the competitive relationship between basal ganglia/thalamus (SC1) and limbic nuclei (SC2) for coupling with DMN or primary networks. The coupling between cortical and subcortical regions in the two states is summarized in Figure 4 c . Unsurprisingly, these two states are associated, respectively, with high scores on the fi rst and second cortical -subcortical principal components (Fig. 5).

The two states are robustly observed also at the single-subject level (Fig. S4 a ). By performing analysis in single subjects, we obtained two states with very similar centroids. On average, the correlation between individual and group-level centroids was 0.64 and 0.63.

The states found qualitatively align with those of Favaretto et al. (2022). A detailed comparison is presented in Text S1 and Figure S3.

We tested the robustness of the K =2 analysis with respect to the choice of cortical and subcortical parcellation. For a di ff erent cortical parcellation, we used the well-known Schaefer atlas with 100 regions (Schaefer et al., 2018). For the Schaefer atlas, regions are divided into RSNs according to the classical classi fi cation (Yeo et al., 2011), where the control network (CON) includes regions associated with the FPN and the VAN includes regions associated with the cingulo-opercular network (Gordon et al., 2016). For a di ff erent subcortical parcellation, we used the same atlas described above (Tian et al., 2020), which does not include cerebellar regions. In Figure S1 f , we show the results of changing cortical and subcortical parcellation, respectively. The core structure of the DFS ( K =2) is preserved across the parcellation changes. In particular, DFS1 is characterized by a strong DAN -DMNanticorrelation, while the hippocampus couples positively with the DMN and negatively with the taskpositive networks. Conversely, DFS2 is characterized by a strong segregation of the primary networks from the association networks. The hippocampus/amygdala (SC2) correlate positively with primary networks and negatively with association networks, while the opposite pattern is observed for thalamus/basal ganglia (SC1).

Next, we investigated the impact of speci fi c preprocessing and analysis choices. Firstly, in our analysis, we used a time window of 60 s. Reducing the time window length had a negligible e ff ect on results (Fig. S3 b ). Secondly, we performed GSR. This decision is in line with current practice in dFC analysis and other approaches to investigate dynamical phenomena in fMRI (Demertzi, 2024). In fact, the GS generally creates a strong component of BOLD activity that can dominate above other dynamic phenomena (Bolt et al., 2022). When not performing GSR, the subcortical PC was mildly a ff ected, showing that the split of subcortical regions into two clusters is not contingent on GSR. However, GSR has a non-negligible impact on the structure of the two DFSs (Fig. S3 a ). When not performing GSR, we still observed two DFSs representing a positive versus negative coupling of SC2 with sensorimotor networks. These DFS were related, but not equivalent to those reported in the main analysis (correlation between the centroids ρ =0.62; ρ =0.54). Thirdly, in our analysis we used the full HCP dataset, which includes a large number of genetically related subjects. We performed an analysis on a subset of 100 unrelated subjects (54 females, 46 males; Van Essen et al., 2013), which led to equivalent results (Fig. S4 b ), consistent with the previous analysis showing that results qualitatively hold at the single-subject level.

Finally, to test whether the lagged cross-covariance structure of the data is su ffi cient to yield the observed DFSs, we applied PR. PR generates surrogate data that preserve the empirically measured cross-covariances but are linear and Gaussian (Liégeois et al., 2017). As shown in Figure S3 c , the main subcortical PC and the DFSs resulting from the PR-generated time series closely resemble the ones obtained with the original data. This correspondence is furtherly corroborated by a correlation between centroids of 0.99 and 0.98, respectively.

*[picture on PDF page 8]*

**Figure labels:**
- a

*[picture on PDF page 8]*

**Figure labels:**
- b

*[picture on PDF page 8]*

**Figure labels:**
- Conditional FC jump probabilities
- Explained variance
- Pjump(RSN1 | RSN2)
- 0.7
- 80
- VIS
- cumulative
- SMN
- 70
- raw
- AUD
- 0.6
- 60
- CON
- Var. Exp.
- 50
- 2
- VAN
- RSN
- DAN
- 0.5
- 40
- FPN
- 30
- DMN
- LIM
- 0.4
- 20
- SC1
- 10
- SC2
- 0.3
- 0
- 5
- 15
- PC #
- RSN 1
- d
- C
- PC1
- PC2
- R

### Correlation with behavior

We tested a possible correlation between individual dFC metrics and individual behavioral traits. The large array of behavioral variables ( ' SMs ' ) available in the HCP dataset were summarized into a few general descriptors capturing key aspects of cognition and behavior (Fig. 6 c ). We fi rst used the positive -negative mode (PNM) of behavior -FC covariation (Smith et al., 2015), which is a single indicator of global behavioral/social function (see Materials and Methods). In addition, we considered seven individual markers identi fi ed in a recent study (Granziol and Cona, 2024) which capture di ff erent aspects of cognition (Fig. 6 c ).

*[picture on PDF page 9]*

**Figure labels:**
- a
- DFS1
- DFS2
- VIS
- SMN
- AUD
- CON
- VAN
- DAN
- FPN
- DMN
- LIM
- SUB
- C
- LEFT
- RIGHT
- Fraction times
- 0.01
- SC1
- SC2
- 100
- 80
- 60
- 0
- %
- 40
- 20
- -0.01
- Cortico-subcortical average connectivity
- Dwell times
- 300
- 250
- seconds
- 200
- 150
- 50
- NON
- WIM
- 1
- 2

DFS

***Figure 4. DFS analysis. a , Matrix representation of the DFSs displayed globally (top) and with a focus on the cortical -subcortical interactions (bottom). The most robust states observed for K =2capture the alternating connectivity pattern observed in the Washington dataset between limbic regions (i.e., hippocampus and amygdala) and task-negative versus task-positive networks. b , Volumetric representation of the DFSs ( K =2). c , Average connectivity between subcortical clusters (SC1 and SC2) and cortical networks in the two most robust DFSs. d , Distribution of fraction and dwell times for the K =2 states. FTs/DTs were averaged within subjects and then plotted across subjects, resulting in violin plots that display the mean values (black lines). VIS, visual network; SMN, sensorimotor network; AUD, auditory network; CON, cingulo-opercular network; VAN, ventral attention network; DAN, dorsal attention network; FPN, frontoparietal network; DMN, default mode network.***

We fi rst tested for correlation between behavioral metrics and individual fraction/dwell times obtained with K =2. We performed a linear regression using the behavioral metrics as dependent variables and the fraction/dwell times as predictors. The total regression R 2 was always lower than 0.01, meaning that fraction/dwell times explain <1% of the variation in the behavioral metrics considered (Fig. 6 d ). We thus found no signi fi cant e ff ect of fraction/dwell times on behavioral metrics (permutation test on R 2 , corrected for 32 comparisons). In addition, we tested whether the probabilities of synchronized jumps between cortical regions and the two main subcortical clusters could predict behavior. We averaged the conditional probabilities (Fig. 3 a ) by aggregating cortical regions, regions belonging to SC1, and regions belonging to SC2, obtaining a 3 × 3 matrix of synchronized jumps. From this matrix we extracted four entries corresponding to the probabilities of synchronized jumps between the cortex and, respectively, SC1 and SC2. We performed a linear regression using the behavioral metrics as dependent variables and these probabilities as predictors. The total regression R 2 was always lower than 0.01 and nonsigni fi cant (Fig. 6 d ). Finally, we tested whether the average FC patterns in each DFS could predict behavior. We computed an average DFS pattern for each individual subject, by averaging the swFC over time windows assigned to one of the K =2 DFSs (Fig. 6 a ). This can be considered as a DFS pattern ' adjusted ' to each participant. We averaged the FC

*[picture on PDF page 10]*

**Figure labels:**
- VIS
- SMN
- AUD
- CON
- VAN
- Leading eigenvector of FC (v)
- DAN
- FPN
- DMN
- LIM
- L CER
- L THA
- L CAU
- L PUT
- L GP
- BST
- L HIP
- L AMY
- L NAc
- L DIE
- R CER
- R THA
- R CAU
- R PUT
- R GP
- R HIP
- R AMY
- R NAC
- R DIE
- DFS
- 0.5
- pcl
- PCs of v
- pc2

patterns by aggregating task-positive regions (SMN, DAN, VIS), task-negative regions (CON, DMN), regions belonging to SC1, and regions belonging to SC2, obtaining two 4 × 4 matrices (one for each DFS) for each participant. We performed a linear regression using the behavioral metrics as dependent variables and the entries of this matrix as predictors. The total regression R 2 was signi fi cant for the PNM, which displayed R 2 =0.07, with a signi fi cant e ff ect ( p =0.003; permutation test on R 2 ; corrected for 32 comparisons). Higher values of the PNM are associated with higher segregation within the cortex and between the cortex and SC1 in DFS1 and, conversely, higher integration within the cortex and between the cortex and SC1 in DFS2 (Fig. 6 b ).

*[picture on PDF page 11]*

**Figure labels:**
- Single subject
- Regression over subjects
- a
- DFS1
- DFS1 prediction of PNM (t-stat)
- t
- PRI
- COG
- SC1
- SC2
- DFS2
- DFS2 prediction of PNM (t-stat)
- C
- Positive-negative mode
- Behavioral communities
- R² for predictors
- Correlation (r) between each SM and
- 0.34
- Positive
- Fluid intelligence (number of correct responses)
- Card sorting unadjusted
- 60/
- Card sorting adjusted for age
- V08
- FT
- DT
- JP
- FC
- Picture sequence memory test unadjusted
- V33
- 0.1
- V
- Variable short Penn line orientation (number of correct responses)
- Picture sequence memory test adjusted for age
- V07
- V03
- MTL
- the CCA mode
- Flanker test (unadjusted)
- /32
- LCF
- 0.01
- ▲
- Flanker test (adjusted for age)
- List sorting working memory test (unadjusted)
- V30
- V06
- DDT
- 2
- R
- K
- A
- 0.2
- List sorting working memory test (adjusted for age)
- V34
- V15
- HCF
- 0.001
- - 0.29 +
- DSM antisocial personality problems
- V28
- V25
- SUB
- ■
- Total weekdays with cigarettes in last week
- Frequency drunk (heaviest 12-month period)
- /35
- EXT
- 0.0001
- Positive test for THC (cannabis)
- V26
- Age at first alcohol use
- V36
- ●
- Negative
- Electronic visual acuity score (denominator)
- Anger-physical aggression score
- PNM
- PAI
- LHF
- Thought problems score (self-report)
- - 0.4 †
- Variable short Penn line orientation (total positions off)

### Discussion

In spite of a traditional ' corticocentric bias ' in human neuroscience (Parvizi, 2009), recent research has shown that subcortical areas play critical roles in advanced cognition (Shine, 2021; Janacsek et al., 2022; Saban and Gabay, 2023, Suzuki et al., 2023). Accordingly, the subcortex should be included in descriptions of large-scale brain dynamics. While most neuroimaging studies have portrayed a ' static ' coupling between subcortical structures and cortical RSNs (Habas et al., 2009; Greene et al., 2020; Barnett et al., 2021; Ezama et al., 2021; Li et al., 2021), Favaretto et al. (2022) provided evidence that subcortical structures couple ' fl exibly ' with cortical networks, using dFC on a cohort of stroke patients. The present study corroborates and extends their fi ndings using a large sample of healthy young participants.

Our dFC analysis targeted variations in cortical -subcortical coupling occurring in the ' infaslow ' frequency range accessible to fMRI (<0.1 Hz or >10 s). We showed that FC rearrangements involve the cortex and the subcortex jointly, as large subcortical connectivity shifts predicted large cortical shifts with >60% accuracy and vice versa (Fig. 3 a ). We identi fi ed two principal modes (principal components) explaining a large fraction of the temporal variance in cortical -subcortical FC (Fig. 3 c , d ). Notably, restricting attention to the subcortex alone (Fig. 2) yielded a subcortical mode that strongly aligned with the two whole-brain modes, providing further evidence of cortical -subcortical synchronization in connectivity shifts. These principal modes re fl ect a low-dimensional modulation of cortical -subcortical coupling, involving connectivity switches between two groups of subcortical regions ( ' SC1, ' comprising hippocampus/amygdala, and ' SC2, ' comprising the thalamus, basal ganglia, and the ' taskpositive ' cerebellum; Fig. 2) and cortical networks. Switches were encapsulated by two main patterns of cortical -subcortical connectivity, DFS1 and DFS2 (Figs. 4 and 5). The hippocampus/amygdala coupled positively with the DMN and negatively with the SMN in DFS1, while couplings were reversed in DFS2. Conversely, the thalamus/basal ganglia/cerebellum coupled positively with the DMN and negatively with the SMN in DFS2 and had weak coupling with the cortex in DFS1. Overall, DFS1 more closely resembled the static FC pattern, with strong DAN -DMN anticorrelation and a correspondingly antinomic pattern in the coupling of hippocampus/amygdalawiththe cortex. DFS2, instead, was characterized by a strong segregation of the primary networks from the association networks and a correspondingly antinomic pattern in the coupling of both hippocampus/amygdala and thalamus/basal ganglia/cerebellum with the cortex.

The observed internal cohesion of the two clusters fi nds support in both classical and recent results, while their apparent antagonism is neither widely discussed nor reported in the literature (an exception is Milardi et al., 2019). SC2 comprises regions of the ' limbic system ' for emotion and memory (Catani et al., 2013; Rolls, 2015). The tight coupling within SC1 is less straightforward to interpret, as it involves anatomically and functionally heterogeneous regions. The cerebellum and basal ganglia were traditionally thought to be independent, giving complementary contributions to learning and motor control (Doya, 2000), and to communicate only at the cortical level. Nonetheless, recent fi ndings provided solid evidence that the two systems are reciprocally interconnected not only at the level of the thalamus (Hintzen et al., 2018) but also through more direct subcortical pathways (Bostan and Strick, 2018; Milardi et al., 2019). This suggests that the cerebellum, basal ganglia, and thalamus constitute an integrated network (Bostan and Strick, 2018) acting in concert with the cortex via cortical -subcortical loops.

The global, low-dimensional modulation highlighted in this work explained ∼ 40% of the temporal variance in cortical -subcortical connectivity, thus not representing an exhaustive characterization of connectivity fl uctuations (in fact, a large number of components are required to explain 80% of the variance). Principal components beyond the second were associated with less ' clustered ' and more nuanced spatial patterns, di ff erentiating among regions within the two subcortical clusters and cortical RSNs (Fig. S5). While a deeper understanding of speci fi c cortical -subcortical networks and their unique modes of interaction deserves further investigation, our fi ndings point at the presence of a slow, brain-wide modulation of cortical -subcortical FC. The large amount of variance explained by the fi rst two principal components (Fig. 3 c , d ) and their stability across parcellations and subjects corroborate this hypothesis.

Testing for ' signi fi cance ' of the observed patterns is challenging due to the lack of a standard null model. PR (Liégeois et al., 2017) leads to surrogates matching all spectral and crosscorrelation properties of the original data and retaining many dynamical features such as dFC (Liégeois et al., 2017), coactivation patterns (Matsui et al., 2022), and high-amplitude co fl uctuation events (Ladwig et al., 2022), which questions their appropriateness as a null model (Miller et al., 2018). In line with previous literature (Abrol et al., 2017; Miller et al., 2018), our DFSs closely matched PR surrogates (Fig. S3 c ), implying that they substantially depend on the lagged cross-covariance structure of the time series. This is consistent with a nonchaotic, quasiperiodic alternation between states.

Currently, we hesitate to advance strong hypotheses on what could drive the observed FC rearrangements. Invasive recordings in rats have revealed that di ff erent types of subcortical events, such as slow-frequency activity (Chan et al., 2017), ripples and dentate spikes in the hippocampus (Nitzan et al., 2022, Farrell et al., 2024), and regular spikes and spindles in the thalamus (Xiao et al., 2017, Wang et al., 2023), can trigger widespread cortical e ff ects, re fl ecting in BOLD signal changes (Chan et al., 2017;

Wang et al., 2023). However, no such evidence has been collected in humans so far.

Amorepromising hypothesis regards slow, modulatory physiological processes. ' Arousal, ' regulated by the noradrenergic system, undergoes periodic fl uctuations over a timescale of several seconds, re fl ected in pupil diameter and EEG vigilance metrics. Concurrent fMRI-pupillometry and fMRI-EEG showed that arousal modulates the BOLD signal (Wong et al., 2013; Chang et al., 2016; Wang et al., 2016; Allen et al., 2018; Raut et al., 2021; Gu et al., 2022; Lee et al., 2022; Raut et al., 2025), inducing ' global, low-dimensional ' fl uctuations in brain dynamics. Recent evidence suggests that arousal-related modulation of wholebrain dynamics is associated with a shift between an ' inward ' and ' outward ' mode of cognition (Yang et al., 2024; Yang et al., 2025). The ' inward ' phase, occurring during low arousal, is associated with a higher activation of the DMN and the hippocampus and accompanied by an increase in hippocampal short-wave-ripple events and replays (Yang et al., 2019). The ' outward ' phase, occurring during high arousal, is associated with a higher activation of sensorimotor networks and the DAN. The switch between the two phases is quasiperiodic and explains the early observation of a ' quasiperiodic pattern ' in fMRI, characterized by an alternation of DMN and DAN activation (Thompson et al., 2014; Fransson and Strindberg, 2023), which can be more accurately characterized as a ' traveling wave ' of activity propagating from exteroceptive sensorimotor regions to interoceptive DMN ones (Raut et al., 2021; Bolt et al., 2022; Mäki-Marttunen and Nieuwenhuis, 2024). Surprisingly, this phenomenon has not been investigated at the subcortical level. Here, we observed alternation between a state with strong hippocampus -DMN coupling and DAN -DMN anticorrelation (DFS1) and another with strong coupling among primary networks and between hippocampus and SMN (DFS2). The ' internal ' and ' external ' modes of cognition may thus be characterized by distinct ' coupling patterns ' between the subcortex and cortex. Future work may exploit a database including both fMRI and ' arousal ' (pupil diameter) measurements to test for a direct alignment between our dFC analysis and the above-described QPP/traveling wave approaches.

Finally, since exploratory analyses searching for association between brain function and behavior require very large samples (thousands of individuals; Marek et al., 2022), we restricted our connectivity -behavior analysis to a few summary metrics, including the ' PNM of population covariation ' (Smith et al., 2015) that highlights a global individual ' function outcome. ' Consistently with previously reported weak correlations between behavior and summary metrics of dFC (Lee et al., 2023), we did not fi nd a signi fi cant relationship between behavior and fraction times, dwell times or the probabilities of cortical -subcortical FC jumps (Fig. 6). Possibly, these summary measures do not account for individual variation in FC ' strength, ' which may be necessary to predict a signi fi cant fraction of behavioral variability (Smith et al., 2015; Liégeois et al., 2019). In fact, when considering network-averaged FC strengths associated with DFS1 and DFS2 in single individuals, we obtained signi fi cant correlations with behavior, up to R 2 =0.07 for the PNM. More positive values of the PNM (associated with better cognitive health) corresponded to a dynamic cortical -subcortical connectivity reorganization where the cortex and SC1 are ' less integrated ' in DFS1 and ' more integrated ' in DFS2. Healthier cognition may thus require a stronger modulation of SC1 integration with the cortex.

In conclusion, the human brain at rest is characterized by slow fl uctuations in FC. Changes occur simultaneously in the cortex and subcortex, as two main groups of subcortical regions (thalamus/basal ganglia/cerebellum vs hippocampus/amygdala) show fl exible coupling arrangements with task-positive and task-negative cortical regions. The mechanisms underlying this global connectivity modulation are presently unknown and demand further investigation.

### Data Availability

The code employed for this manuscript is available at https:// github.com/alessandronazzi/DynamicFunctionalConnectivity.

### References

- Abrol A, Damaraju E, Miller RL, Stephen JM, Claus ED, Mayer AR, Calhoun VD (2017) Replicability of time-varying connectivity patterns in large resting state fMRI samples. Neuroimage 163:160 -176.
- Allen EA, Damaraju E, Plis SM, Erhardt EB, Eichele T, Calhoun VD (2014) Tracking whole-brain connectivity dynamics in the resting state. Cereb Cortex 24:663 -676.
- Allen EA, Damaraju E, Eichele T, Wu L, Calhoun VD (2018) EEG signatures of dynamic functional network connectivity states. Brain Topogr 31:101 -116.
- Barnett AJ, Reilly W, Dimsdale-Zucker HR, Mizrak E, Reagh Z, Ranganath C (2021) Intrinsic connectivity reveals functionally distinct corticohippocampal networks in the human brain. PLoS Biol 19:e3001275.
- Blessing EM, Beissner F, Schumann A, Brünner F, Bär K (2016) A data-driven approach to mapping cortical and subcortical intrinsic functional connectivity along the longitudinal hippocampal axis. Hum Brain Mapp 37:462 -476.
- Bolt T, Nomi JS, Bzdok D, Salas JA, Chang C, Thomas Yeo BT, Uddin LQ, Keilholz SD (2022) A parsimonious description of global functional brain organization in three spatiotemporal patterns. Nat Neurosci 25:1093 -1103.
- Bostan AC, Strick PL (2018) The basal ganglia and the cerebellum: nodes in an integrated network. Nat Rev Neurosci 19:338 -350.
- Buckner RL, Krienen FM, Castellanos A, Diaz JC, Yeo BTT (2011) The organization of the human cerebellum estimated by intrinsic functional connectivity. J Neurophysiol 106:2322 -2345.
- Catani M, Dell ' Acqua F, De Schotten MT (2013) A revised limbic system model for memory, emotion and behaviour. Neurosci Biobehav Rev 37: 1724 -1737.
- Chan RW, et al. (2017) Low-frequency hippocampal -cortical activity drives brain-wide resting-state functional MRI connectivity. Proc Natl Acad Sci U S A 114:33.
- Chang C, Leopold DA, Schölvinck ML, Mandelkow H, Picchioni D, Liu X, Ye FQ, Turchi JN, Duyn JH (2016) Tracking brain arousal fl uctuations with fMRI. Proc Natl Acad Sci U S A 113:4518 -4523.
- Christensen A, Golino H (2019) Estimating the stability of the number of factors via Bootstrap Exploratory Graph Analysis: A tutorial.
- Demertzi A (2024) To regress out or not? An update on the fMRI global signal debate. In Organization of the human brain mapping 2024 .
- Doya K (2000) Complementary roles of basal ganglia and cerebellum in learning and motor control. Curr Opin Neurobiol 10:732 -739.
- Ezama L, Hernández-Cabrera JA, Seoane S, Pereda E, Janssen N (2021) Functional connectivity of the hippocampus and its sub fi elds in restingstate networks. Eur J Neurosci 53:3378 -3393.
- Farrell JS, Hwaun E, Dudok B, Soltesz I (2024) Neural and behavioural state switching during hippocampal dentate spikes. Nature 628:590 -595.
- Favaretto C, Allegra M, Deco G, Metcalf NV, Grif fi s JC, Shulman GL, Brovelli A, Corbetta M (2022) Subcortical-cortical dynamical states of the human brain and their breakdown in stroke. Nat Commun 13:5069.
- Fischl B (2012). FreeSurfer. Neuroimage 62:774 -781.
- Fischl B, Salat DH, Busa E, Albert M, Dieterich M, Haselgrove C, Van Der Kouwe A, Killiany R, Kennedy D, Klaveness S (2002) Whole brain segmentation: automated labeling of neuroanatomical structures in the human brain. Neuron 33:341 -355.
- Fransson P, Strindberg M (2023) Brain network integration, segregation and quasi-periodic activation and deactivation during tasks and rest. Neuroimage 268:119890.
- Friedman J, Hastie T, Tibshirani R (2008) Sparse inverse covariance estimation with the graphical lasso. Biostatistics 9:432 -441.
- Glasser MF, et al. (2013) The minimal preprocessing pipelines for the human connectome project. Neuroimage 80:105 -124.
- Golino HF, Epskamp S (2017) Exploratory graph analysis: a new approach for estimating the number of dimensions in psychological research. PLoS One 12:e0174035.
- Gordon EM, Laumann TO, Adeyemo B, Huckins JF, Kelley WM, Petersen SE (2016) Generation and evaluation of a cortical area parcellation from resting-state correlations. Cereb Cortex 26:288 -303.
- Granziol U, Cona G (2024) Architecture and relationships among cognition, mental health and other human domains revealed by network analysis perspective. Curr Psychol 43:4945 -4960.
- Greene DJ, Marek S, Gordon EM, Siegel JS, Gratton C, Laumann TO, Gilmore AW, Berg JJ, Nguyen AL, Dierker D (2020) Integrative and networkspeci fi c connectivity of the basal ganglia and thalamus de fi ned in individuals. Neuron 105:742 -758.
- Gu Y, Han F, Sainburg LE, Schade MM, Buxton OM, Duyn JH, Liu X (2022) An orderly sequence of autonomic and neural events at transient arousal changes. Neuroimage 264:119720.
- Habas C, Kamdar N, Nguyen D, Prater K, Beckmann CF, Menon V, Greicius MD(2009) Distinct cerebellar contributions to intrinsic connectivity networks. J Neurosci 29:8586 -8594.
- Hindriks R, Adhikari MH, Murayama Y, Ganzetti M, Mantini D, Logothetis NK, Deco G (2016) Can sliding-window correlations reveal dynamic functional connectivity in resting-state fMRI? Neuroimage 127:242 -256.
- Hintzen A, Pelzer EA, Tittgemeyer M (2018) Thalamic interactions of cerebellum and basal ganglia. Brain Struct Funct 223:569 -587.
- Hutchison RM, Womelsdorf T, Allen EA, Bandettini PA, Calhoun VD, Corbetta M, Della Penna S, Duyn JH, Glover GH, Gonzalez-Castillo J (2013) Dynamic functional connectivity: promise, issues, and interpretations. Neuroimage 80:360 -378.
- Hwang K, Bertolero MA, Liu WB, D ' Esposito M (2017) The human thalamus is an integrative hub for functional brain networks. J Neurosci 37:5594 -5607.
- Janacsek K, Evans TM, Kiss M, Shah L, Blumenfeld H, Ullman MT (2022) Subcortical cognition: the fruit below the rind. Annu Rev Neurosci 45: 361 -386.
- Krauth A, Blanc R, Poveda A, Jeanmonod D, Morel A, Székely G (2010) A mean three-dimensional atlas of the human thalamus: generation from multiple histological data. Neuroimage 49:2053 -2062.
- Ladwig Z, Seitzman BA, Dworetsky A, Yu Y, Adeyemo B, Smith DM, Petersen SE, Gratton C (2022) BOLD co fl uctuation ' events ' are predicted from static functional connectivity. Neuroimage 260:119476.
- Lee K, Horien C, O ' Connor D, Garand-Sheridan B, Tokoglu F, Scheinost D, Lake EM, Constable RT (2022) Arousal impacts distributed hubs modulating the integration of brain functional connectivity. Neuroimage 258: 119364.
- Lee K, Ji JL, Fonteneau C, Berkovitch L, Rahmati M, Pan L, Repov š G, Krystal JH, Murray JD, Anticevic A (2023) Human brain state dynamics re fl ect individual neuro-phenotypes. bioRxiv. https://www.ncbi.nlm.nih.gov/ pmc/articles/PMC10542143/
- Leonardi N, Van De Ville D (2015) On spurious and real fl uctuations of dynamic functional connectivity during rest. Neuroimage 104:430 -436.
- Li J, Curley WH, Guerin B, Dougherty DD, Dalca AV, Fischl B, Horn A, Edlow BL (2021) Mapping the subcortical connectivity of the human default mode network. Neuroimage 245:118758.
- Liegeois R, Laumann TO, Snyder AZ, Zhou J, Yeo BT (2017) Interpreting temporal fl uctuations in resting-state functional connectivity MRI. Neuroimage 163:437 -455.
- Liégeois R, Li J, Kong R, Orban C, Van De Ville D, Ge T, Sabuncu MR, Yeo BTT (2019) Resting brain dynamics at different timescales capture distinct aspects of human behavior. Nat Commun 10:2317.
- Lurie DJ, Kessler D, Bassett DS, Betzel RF, Breakspear M, Kheilholz S, Kucyi A, Liégeois R, Lindquist MA, McIntosh AR (2020) Questions and controversies in the study of time-varying functional connectivity in resting fMRI. Netw Neurosci 4:30 -69.
- Mäki-Marttunen V, Nieuwenhuis S (2024) Neuromodulatory in fl uences on propagation of brain waves along the unimodal-transmodal gradient. bioRxiv, 2024-10.
- Marek S, et al. (2022) Reproducible brain-wide association studies require thousands of individuals. Nature 603:654 -660.
- Matsui T, Pham TQ, Jimura K, Chikazoe J (2022) On co-activation pattern analysis and non-stationarity of resting brain activity. Neuroimage 249: 118904.

- Milardi D, Quartarone A, Bramanti A, Anastasi G, Bertino S, Basile GA, Buonasera P, Pilone G, Celeste G, Rizzo G (2019) The cortico-basal ganglia-cerebellar network: past, present and future perspectives. Front Syst Neurosci 13:61.
- Miller RL, Abrol A, Adali T, Levin-Schwarz Y, Calhoun VD (2018) Resting-state fMRI dynamics and null models: perspectives, sampling variability, and simulations. Front Neurosci 12:551.
- Nitzan N, Swanson R, Schmitz D, Buzsáki G (2022) Brain-wide interactions during hippocampal sharp wave ripples. Proc Natl Acad Sci U S A 119: e2200931119.
- Parvizi J (2009) Corticocentric myopia: old bias in new cognitive sciences. Trends Cogn Sci 13:354 -359.
- Pons P, Latapy M (2005) Computing communities in large networks using random walks. In: Computer and information sciences -ISCIS 2005 (Yolum P, Güngör T, Gürgen F, Özturan C, eds), Vol. 3733, pp 284 -293. Berlin, Heidelberg: Springer.
- Preti MG, Bolton TA, Van De Ville D (2017) The dynamic functional connectome: state-of-the-art and perspectives. Neuroimage 160:41 -54.
- Prichard D, Theiler J (1994) Generating surrogate data for time series with several simultaneously measured variables. Phys Rev Lett 73:951 -954.
- Raichle ME (2010) Two views of brain function. Trends Cogn Sci 14:180 -190. Raichle ME (2011) The restless brain. Brain Connect 1:3 -12.
- Raut RV, Snyder AZ, Mitra A, Yellin D, Fujii N, Malach R, Raichle ME (2021) Global waves synchronize the brain ' s functional systems with fl uctuating arousal. Sci Adv 7:eabf2709.
- Raut RV, et al. (2025) Arousal as a universal embedding for spatiotemporal brain dynamics. BioRxiv, 2023-11.
- Rolls ET (2015) Limbic systems for emotion and for memory, but no single limbic system. Cortex 62:119 -157.
- Saban W, Gabay S (2023) Contributions of lower structures to higher cognition: towards a dynamic network model. J Intell 11:121.
- Schaefer A, Kong R, Gordon EM, Laumann TO, Zuo X-N, Holmes AJ, Eickhoff SB, Yeo BT (2018) Local-global parcellation of the human cerebral cortex from intrinsic functional connectivity MRI. Cereb Cortex 28: 3095 -3114.
- Shine JM (2021) The thalamus integrates the macrosystems of the brain to facilitate complex, adaptive brain network dynamics. Prog Neurobiol 199:101951.
- Smith SM, Beckmann CF, Andersson J, Auerbach EJ, Bijsterbosch J, Douaud G, Duff E, Feinberg DA, Griffanti L, Harms MP (2013) Resting-state fMRI in the human connectome project. Neuroimage 80:144 -168.
- Smith SM, Nichols TE, Vidaurre D, Winkler AM, Behrens TE, Glasser MF, Ugurbil K, Barch DM, Van Essen DC, Miller KL (2015) A positivenegative mode of population covariation links brain connectivity, demographics and behavior. Nat Neurosci 18:1565 -1567.
- Suzuki M, Pennartz CM, Aru J (2023) How deep is the brain? the shallow brain hypothesis. Nat Rev Neurosci 24:778 -791.
- Thompson GJ, Pan WJ, Magnuson ME, Jaeger D, Keilholz SD (2014) Quasi-periodic patterns (QPP): large-scale dynamics in resting state fMRI that correlate with local infraslow electrical activity. Neuroimage 84:1018 -1031.
- Tian Y, Margulies DS, Breakspear M, Zalesky A (2020) Topographic organization of the human subcortex unveiled with functional connectivity gradients. Nat Neurosci 23:1421 -1432.
- Uddin LQ, Yeo BT, Spreng RN (2019) Towards a universal taxonomy of macro-scale functional human brain networks. Brain Topogr 32:926 -942.
- Van Essen DC, Smith SM, Barch DM, Behrens TE, Yacoub E, Ugurbil K, Consortium W-MH (2013) The WU-minn human connectome project: an overview. Neuroimage 80:62 -79.
- Wang C, Ong JL, Patanaik A, Zhou J, Chee MWL (2016) Spontaneous eyelid closures link vigilance fl uctuation with fMRI dynamic connectivity states. Proc Natl Acad Sci U S A 113:9653 -9658.
- Wang X, Leong AT, Tan SZ, Wong EC, Liu Y, Lim L-W, Wu EX (2023) Functional MRI reveals brain-wide actions of thalamically-initiated oscillatory activities on associative memory consolidation. Nat Commun 14:2195.
- Wong CW, Olafsson V, Tal O, Liu TT (2013) The amplitude of the restingstate fMRI global signal is related to EEG vigilance measures. Neuroimage 83:983 -990.
- Xiao D, Vanni MP, Mitelut CC, Chan AW, LeDue JM, Xie Y, Chen AC, Swindale NV, Murphy TH (2017) Mapping cortical mesoscopic networks of single spiking cortical or sub-cortical neurons. Elife 6:e19976.
- Yang M, Logothetis NK, Sara SJ, Eschenko O (2019) The Locus Coeruleus activity during hippocampal-cortical communication. In 49th Annual Meeting of the Society for Neuroscience (Neuroscience 2019) (pp 1197-1198).
- Yang Y, Leopold DA, Duyn JH, Liu X (2024) Propagating cortical waves coordinate sensory encoding and memory retrieval in the human brain. bioRxiv, 2024-06.
- Yang Y, Leopold DA, Duyn JH, Sipe GO, Liu X (2025) Sensory encoding alternates with hippocampal ripples across cycles of forebrain spiking cascades. Adv Sci 12:2406224.
- Yeo BT, et al. (2011) The organization of the human cerebral cortex estimated by intrinsic functional connectivity. J Neurophysiol 106:1125 -1165.