BRAIN

*[picture on PDF page 1]*

**Figure labels:**
- A JOURNAL OF NEUROLOGY

### Acute ischaemic stroke alters the brain's preference for distinct dynamic connectivity states

Anna K. Bonkhoff, 1,2,3 Flor A. Espinoza, 4 Harshvardhan Gazula, 5 Victor M. Vergara, 5 Lukas Hensel, 1 Jochen Michely, 1 Theresa Paul, 1 Anne K. Rehme, 1 Lukas J. Volz, 1 Gereon R. Fink, 1,2 Vince D. Calhoun 4,5 and Christian Grefkes 1,2

Acute ischaemic stroke disturbs healthy brain organization, prompting subsequent plasticity and reorganization to compensate for the loss of specialized neural tissue and function. Static resting state functional MRI studies have already furthered our understanding of cerebral reorganization by estimating stroke-induced changes in network connectivity aggregated over the duration of several minutes. In this study, we used dynamic resting state functional MRI analyses to increase temporal resolution to seconds and explore transient configurations of motor network connectivity in acute stroke. To this end, we collected resting state functional MRI data of 31 patients with acute ischaemic stroke and 17 age-matched healthy control subjects. Stroke patients presented with moderate to severe hand motor deficits. By estimating dynamic functional connectivity within a sliding window framework, we identified three distinct connectivity configurations of motor-related networks. Motor networks were organized into three regional domains, i.e. a cortical, subcortical and cerebellar domain. The dynamic connectivity patterns of stroke patients diverged from those of healthy controls depending on the severity of the initial motor impairment. Moderately affected patients ( n = 18) spent significantly more time in a weakly connected configuration that was characterized by low levels of connectivity, both locally as well as between distant regions. In contrast, severely affected patients ( n = 13) showed a significant preference for transitions into a spatially segregated connectivity configuration. This configuration featured particularly high levels of local connectivity within the three regional domains as well as anti-correlated connectivity between distant networks across domains. A third connectivity configuration represented an intermediate connectivity pattern compared to the preceding two, and predominantly encompassed decreased interhemispheric connectivity between cortical motor networks independent of individual deficit severity. Alterations within this third configuration thus closely resembled previously reported ones originating from static resting state functional MRI studies post-stroke. In summary, acute ischaemic stroke not only prompted changes in connectivity between distinct networks, but it also caused characteristic changes in temporal properties of large-scale network interactions depending on the severity of the individual deficit. These findings offer new vistas on the dynamic neural mechanisms underlying acute neurological symptoms, cortical reorganization and treatment effects in stroke patients.

- 1 Department of Neurology, University Hospital Cologne and Medical Faculty, University of Cologne, Germany
- 2 Cognitive Neuroscience, Institute of Neuroscience and Medicine (INM-3), Research Centre Juelich, Juelich, Germany
- 3 Queen Square Institute of Neurology, University College London, London, UK
- 4 The Mind Research Network, Albuquerque, New Mexico, USA
- 5 Tri-institutional Center for Translational Research in Neuroimaging and Data Science (TReNDS), Georgia State University, Georgia Institute of Technology, Emory University, Atlanta, Georgia, USA

> V C The Author(s) (2020). Published by Oxford University Press on behalf of the Guarantors of Brain.

|

|

Correspondence to: Christian Grefkes Institute of Neuroscience and Medicine - Cognitive Neuroscience (INM-3) Research Centre Juelich, Juelich Germany

E-mail: c.grefkes@fz-juelich.de

Keywords: hand motor deficits; dynamic functional network connectivity; sliding window analysis; functional segregation; functional integration

Abbreviations: ARAT = Action Research Arm Test; dFNC = dynamic functional network connectivity; ICA = independent component analysis

### Introduction

Ischaemic stroke is a major cause of sudden focal brain damage that severely disrupts structural and functional integrity at both local and global scales (von Monakow, 1914; Carrera and Tononi, 2014). Functional neuroimaging has strongly contributed to reveal neural mechanisms engaged in post-stroke plasticity and reorganization (Grefkes and Fink, 2011, 2014; Ward, 2017). More precisely, resting state functional MRI studies have frequently demonstrated disturbances in interhemispheric connectivity following stroke (Carter et al. , 2010; Wang et al. , 2010; Golestani et al. , 2013; Rehme et al. , 2014). A highly consistent finding encountered in motor stroke is the reduction of interhemispheric connectivity between the primary sensorimotor cortices, which develops in the first weeks after stroke and returns to levels observed in healthy subjects in parallel with behavioural recovery (van Meer et al. , 2010; Park et al. , 2011; Volz et al. , 2016). However, as conventionally applied analysis tools do not allow for a fine-grained temporal evaluation of resting state functional MRI signals, it is currently unknown whether such stroke-induced alterations in functional network connectivity additionally exhibit fluctuations dependent on symptom severity. These temporal variations could reflect network flexibility necessary for neural reorganization underlying recovery of function.

Importantly, the temporal resolution of resting state functional MRI data has recently been increased by the advent of timevarying or 'dynamic' functional network connectivity (dFNC) analyses (Chang and Glover, 2010; Allen et al. , 2014; Calhoun et al. , 2014). In contrast to the assumption of 'static' connectivity over the entire duration of a functional MRI scan, 'dynamic' analyses now allow connectivity between brain areas to differ over short periods of time. Consequently, connectivity changes can be assessed in the range of seconds instead of several minutes. By summarizing reoccurring large-scale patterns of connectivity, dFNC analyses can then be presented as distinct 'connectivity states' of the brain, as well as transition trajectories between them. These dynamic measures may enable a more sophisticated evaluation of the spontaneously fluctuating nature of neural signals compared to static ones, may possess behavioural relevance (Vidaurre et al. , 2019) and are increasingly suggested as novel biomarkers of disease (for reviews see Hutchison et al. , 2013; Preti et al. , 2017; Lurie et al ., 2020). For example, Kim et al. (2017) applied dFNC analyses on Parkinson's disease patients' data and substantiated a significant association between the occurrences of dynamic connectivity states and clinical disease severity. These dynamic patterns uncovered reductions in functional network segregation that did not manifest in static analyses. Likewise, Espinoza et al . (2019) reported a significantly increased occurrence of a particularly weakly connected dynamic connectivity state in Huntington's disease, which was not detected using static analyses.

Given the increased capacity of dFNC analyses in delineating spontaneously forming connectivity states, such a dynamic approach seems to be particularly well suited to assess conditions requiring high levels of network flexibility, as, for example, in the case of stroke-induced acute lesions. A focal lesion may not only disrupt communication within the motor system, but also alter the brain's predilection for certain connectivity states (Vergara et al. , 2018). Specific dynamic patterns may be crucial for the process of neural reorganization and hence determine the potential of the brain to recover (van der Horn et al. , 2019).

Therefore, the goal of the current study was to investigate dFNC of the motor system in patients with acute ischaemic stroke. We analysed resting state functional MRI data from 31 first-ever stroke patients, presenting with moderate-to-severe hand motor deficits, and 17 age-matched healthy control subjects. We hypothesized distinct dFNC patterns in stroke patients linked to symptom severity, i.e. specific patterns for severely and moderately affected patients, which were not assessable in the static analysis framework. In particular, we expected to observe temporally highly variable global changes in functional connectivity, readily interpretable as segregation and integration between functional domains (Friston, 2002; Eickhoff and Grefkes, 2011). Therefore, the dFNC approach seems to be promising for revealing the complex network effects that acute stroke exerts on the dynamic interactions among brain areas during the recovery process.

### Materials and methods

### Participants

Thirty-two first-ever acute ischaemic stroke patients admitted to the University Hospital of Cologne, Department of Neurology [mean age ± standard deviation (SD): 68.4 ± 12.1 years, 19 males, days post stroke ± SD: 7.2 ± 2.7] and 17 healthy controls (mean age ± SD: 65.4 ± 6.4 years, 15 males) were recruited. One stroke patient was excluded because of severe head motion during scanning (see below), leaving 31 patients for the final analysis. Stroke patients presented with acute unilateral hand motor deficits. Further inclusion criteria were: (i) 40-90 years of age; (ii) diffusion-weighted MRI (DWI) positive for ischaemic stroke; (iii) structurally intact ipsilesional precentral gyrus (M1) as verified by MRI; (iv) within 2 weeks from symptom onset (one patient was included 16 days after stroke); and (v) absence of severe aphasia, apraxia, and neglect. Exclusion criteria were: (i) any contraindication to MRI (e.g. cardiac pacemaker); (ii) epilepsy; (iii) infarcts in multiple territories; (iv) haemorrhagic stroke; and (v) further neurological diseases. Furthermore, no patient featured a haemorrhagic transformation of the ischaemic lesion. In addition, 17 age-matched healthy subjects with no neurological or psychiatric disease served as control group. All subjects provided informed written consent in accordance with the Declaration of Helsinki and all aspects of this study were approved by the local ethics committee.

Please note that the raw data of 26 patients were previously included in Volz et al. (2016). Importantly, the scopes of the two studies strongly differ [dynamic functional connectivity analysis in acute stroke in the current study versus effects of repetitive transcranial magnetic stimulation (rTMS) on motor recovery in Volz et al. (2016)]. There is no overlap, neither in the research question nor in any of the results. Therefore, all analyses described here are novel.

### Hand motor function and clinical assessments

Hand motor deficits were quantified using the Action Research Arm Test (ARAT) (Yozbatiran et al. , 2008). This test is widely used in stroke research and assesses gross and fine upper limb function in four dimensions (i.e. grasp, grip, pinch, and gross movements; range 0-57; 57 = normal performance, 0 = unable to perform any movements). Furthermore, we obtained the National Institutes of Health Stroke Scale (NIHSS) for each patient.

To test for the impact of the motor deficit on dFNC, we divided the sample into (i) a subgroup of severely affected patients (ARAT score 0-28); and (ii) a subgroup of lightly to moderately affected patients (ARAT score 29-57). For two patients, ARAT scores were unavailable because of technical reasons. The first patient was severely affected, according to an NIHSS of 16, and suffered from hemiplegia with no residual arm function. This was equivalent to an ARAT score close to 0, hence the patient was assigned to the severely affected subgroup. The second patient was mildly affected (NIHSS = 3) and had only minor hand motor deficits. Therefore, this patient was assigned to the moderately affected subgroup. Demographic characteristics of all study participants and clinical features of stroke patients are listed in Table 1.

### MRI

Acquisition of resting state functional MRI data was performed on a Siemens Trio 3 T scanner (Siemens Medical Solutions). The following gradient echo-planar imaging (EPI) parameters were applied: repetition time = 2200 ms, echo time = 30 ms, field of view = 200 mm, 33 slices, voxel size: 3.1 -3.1 -3.1 mm 3 , 20% distance factor, flip angle = 90  , 183 volumes (slice

|

coverage of the whole brain). Participants were instructed to lie motionless in the scanner and keep fixating on a red cross on a black screen all through the approximately 7-min session. For stroke patients, we additionally collected DWI images (repetition time = 5100 ms, echo time = 104 ms, field of view = 230 mm, 30 slices, voxel size = 1.8 -1.8 -3.0 mm 3 ) to obtain detailed information on lesion location and extent.

### Preprocessing of resting state functional MRI data

Resting state functional MRI data were preprocessed using the Statistical Parametric Mapping software package (SPM12, Wellcome Trust Centre for Neuroimaging, London, UK; www. fil.ion.ucl.ac.uk/spm) as implemented in MATLAB (version R2019a, MathWorks, Inc., Natick, MA, USA). In case of righthemispheric lesions ( n = 8), images were flipped along the midsagittal plane. In this way, all lesions were located in the left hemisphere, thereby ignoring effects specific to the left or right hemisphere. The first four volumes ('dummy' images) of each scan were discarded to allow for the development of a steady blood oxygenation level-dependent activity signal. Preprocessing of the remaining 179 volumes continued with head movement correction by affine realignment to each scan's mean image. In stroke subjects, diffusion-weighted images were co-registered to the mean EPI. Image volumes were spatially normalized using the 'unified segmentation' option after masking lesioned tissue (Ashburner and Friston, 2005). In a final preprocessing step, images were smoothed using a Gaussian kernel with a full-width at half-maximum (FWHM) of 8 mm.

### Controlling for head motion

We verified the absence of severe motion by calculating individual mean and maximum framewise displacements (Power et al. , 2012). As dynamic functional connectivity analyses are sensitive to head motion, we excluded one subject (Subject 32) with a maximum framewise translation of 12.2 mm. No significant group difference in framewise displacements was observable when comparing the final sample of 31 stroke patients with the 17 healthy controls (two-sided t -test: P = 0.79).

### Intrinsic connectivity networks

The intrinsic connectivity network components used for functional connectivity estimations were computed using spatially constrained independent component analysis (ICA) (Lin et al. , 2010; Du and Fan, 2013) based on components estimated from resting state functional MRI data of 405 healthy controls (Calhoun et al. , 2001; Allen et al. , 2014; components are available for download from: http://trendscenter.org/software/). The advantage of using a spatially constrained ICA approach with components from healthy participants on the current data sample is that parcellations are not biased by stroke lesions, yet are still adaptive to the individual and provide enhanced robustness to artefacts and noise compared to single-subject ICA denoising and regression-based back-reconstruction (Du et al. , 2016; Salman et al. , 2019). We refer to Salman et al. (2019) for a detailed description of the group information guided ICA ('back-reconstruction') algorithm. Given that all patients were scanned very early after stroke (on average 7.2 days), cortical

|

***Table 1 Demographics and clinical characteristics of stroke patients and healthy controls.***

|   | Stroke patients ( n = 31) | Healthy controls ( n = 17) | P -value |
|---|---|---|---|
| Age, years, mean (range) | 68.4 (42-89) | 65.4 (57-82) | 0.4 |
| Sex, % female | 39 | 12 | 0.1 |
| Mean framewise displacement, mean (range) | 0.28 (0.09-0.83) | 0.27 (0.07-0.51) | 0.8 |
| Days since stroke, mean (range) | 7.2 (1-16) | - | - |
| NIHSS | 8 | - | - |
| ARATaffected hand, mean (range) | 30 (0-57) | - | - |
| Lesion volume, ml, median (range) | 12.8 (1.4-136.6) | - | - |
| CSToverlap %, median (range) | 6.8 (0.0-59.1) | - | - |

Values are presented as mean (range) unless otherwise stated. Age and mean framewise displacement values were compared by means of two-sided t -tests, sex frequencies by means of a Pearson's chi-squared test.

reorganization is rather unlikely to have significantly changed the functional architecture (Rehme et al. , 2011), further justifying the use of a healthy sample for defining the network components of interests. As all patients were selected based on the presence of a motor deficit, we focused our analysis on the motor system. Accordingly, we obtained 15 motor network components (as extracted in Allen et al. , 2014). After back-reconstruction, we decided to exclude two of these 15 components because of spatial inaccuracies and a low ratio of low-frequency to high-frequency spectra, a marker of poor signal quality. The remaining 13 network components were identified as (i) left (ipsilesional) primary sensorimotor cortex; (ii) right (contralesional) primary sensorimotor cortex; (iii) bilateral ventral premotor cortex; (iv) supplementary motor area (SMA); (v) bilateral postcentral gyrus; (vi-vii) paracentral lobule (I and II); (viii) bilateral superior parietal lobule; (ix-xi) three subcortical (SC) components: putamen I, putamen II and thalamus; and (xii and xiii) two cerebellar (CB) components: cerebellum right and left. These network components were assigned to one of three domains, i.e. sensorimotor, subcortical and cerebellar domains (Fig. 1).

Before entering the resulting spatial maps and corresponding time courses into further static and dynamic functional connectivity pipelines, time courses were detrended (i.e. accounting for linear, quadratic and cubic trends in the data), despiked using 3Ddespike (Cox, 1996) and filtered by a fifth-order Butterworth low-pass filter with a high-frequency cut-off of 0.15 Hz. Finally, each time course was normalized for variance (Rachakonda et al. , 2007).

### Static functional network connectivity analysis

The multivariate analysis of covariance (MANCOVAN) toolbox within GIFT (http://trendscenter.org/software/gift) was used to evaluate significant associations of connectivity within and between functional networks and the independent variables age, gender, translation, rotation, and group status (healthy controls - moderately affected stroke patients - severely affected stroke patients). We proceeded in sequential multi- and univariate manners, as first outlined in Allen et al. (2011). Translation and rotation were computed as the mean of the absolute differences between consecutive time frames. Age, translation and rotation were treated as continuous variables, while gender and group status were defined as categorical variables.

### Within-network connectivity

For each of the 13 network components, analyses were separately performed on the signal intensities of the respective spatial maps. These intensities represent a measure of the coherence (connectivity) between voxels within the spatial map. We began with the full set of independent variables and PCA-dimensionality reduced voxel intensities of spatial maps as multivariate, dependent variables. We then obtained reduced models by backward elimination, i.e. relying on F -tests at each step, and retained significant independent variables only. Afterwards, we computed univariate, voxelwise t -tests for those independent variables that had remained significant in the multivariate analysis after backward selection. More precisely, we tested for differences in signal intensity for each voxel within a spatial map dependent upon the significant variable, e.g. group status, while accounting for the remaining independent variables. As this resulted in several thousand individual t -tests, a separate one for each voxel in a given spatial map, we applied false discovery rate (FDR)-correction for multiple comparisons to determine statistical significance at a level of P 5 0.05 (Benjamini and Hochberg, 1995).

### Between-network connectivity

To assess static connectivity, pairwise Pearson correlations were computed on the Z -transformed time courses for each participant . This resulted in 78 connectivity pair values per participant, according to the formula: 13 network components -(13 network components - 1) / 2 = 78.

Considering healthy controls, moderately and severely affected patients separately, we evaluated static functional network connectivity differences in a three-level one-way ANOVA (level of significance P 5 0.05). Post hoc t -tests (healthy versus moderate, healthy versus severe, moderate versus severe) were performed in case of significant ANOVA results (level of significance P 5 0.05, FDR-corrected).

### Dynamic functional network connectivity

DFNC was estimated by means of the sliding window approach as implemented in the GIFT toolbox (Sako  glu et al. , 2010; Allen et al. , 2014; Calhoun et al. , 2014; Damaraju et al. , 2014). We first defined 159 individual tapered windows by sliding time rectangles of 44 s (width = 20 repetition times). These time windows were convolved with a Gaussian of 7 s ( r = 3 repetition

|

*[picture on PDF page 5]*

**Figure labels:**
- A
- B
- Ventral_Precentral
- Sensorimotor_r
- *
- 0.8
- Sensorimotor_l
- 0.6
- Ventral
- SMA
- precentral
- Sensorimotor Sensorimotor
- R
- L
- Putamen I
- Putamen II
- Paracentral_I
- 0.4
- Correlations (z)
- Postcentral
- 0.2
- Paracentral_II
- Superior_parietal
- Thalamus
- -0.2
- Postcentral Paracentral I
- Putamen_I
- Putamen_II
- -0.4
- -0.6
- Cerebellum_r
- -0.8
- Superior parietal
- Paracentral II
- Cerebellum R Cerebellum L
- Cerebellum_l
- lobule

times) and shifted in steps of 2.2 s (one repetition time). We opted for common parameter settings, particularly as prior studies have provided evidence that a window width between 30 and 60 s enables successful estimation of dFNCs, which are not governed by noise (Lie ´geois et al. , 2016; Preti et al. , 2017). Within each of these windows, we computed dFNCs from the l 1-regularized precision matrix, i.e. sparse inverse covariance matrix (Friedman et al. , 2008; Varoquaux et al. , 2010; Smith et al. , 2011). We regressed out the covariates age, sex, mean framewise translation and rotation. Finally, we applied Fisher's Z -transformation to functional connectivity matrices to obtain Z -values and stabilize variance for further analyses.

### Clustering analysis

Aiming to condense and thereby improve the interpretability of the rich information of 159 dFNC matrices per subject, we used k-means clustering (Lloyd, 1982) to compute reoccurring functional connectivity patterns, i.e. 'connectivity states', across time and subject space (Hutchison et al. , 2013; Allen et al. , 2014; Calhoun et al. , 2014). We implemented the l 1 distance function ('Manhattan distance') given its suitability for high-dimensional data (Aggarwal et al. , 2001). By convention (Allen et al. , 2014; Espinoza et al ., 2018), this clustering approach was applied to all subjects' connectivity matrices twice: first, to determine the optimal number of clusters k (referred to as 'states'), and then to construct the final k connectivity states. We decided upon the number k by relying on three complementary criteria: the silhouette measure (Rousseeuw, 1987), the elbow criterion based upon the cluster validity index, computed as the ratio between withincluster distance to between-cluster distances (Allen et al. , 2014) and a state frequency of 4 10% (Espinoza et al ., 2018). Each window of each subject was assigned to one of these connectivity states. Notably, this analysis does not guarantee that all participants visit all of the connectivity states, i.e. some might enter only one or two states in spite of three or more existing states. We compared the group-averaged connectivity states originating from the dynamic functional connectivity analysis with the group-averaged static functional connectivity obtained earlier by calculating the Manhattan distance.

### Statistical analysis of dynamic connectivity measures

We statistically evaluated the following dynamic connectivity measures: (i) fraction times (the percentage of total time a subject spent in a given state); (ii) dwell times (the time a subject spent in a state without switching to another one ); (iii) numbers of transitions (how often a subject changed states); and (iv) transition likelihoods (percentages of transition likelihood between the k connectivity states). Additionally, we tested for group differences in dynamic connectivity pairs within each connectivity state. Similar to the between-network static functional connectivity analysis, we initially performed three-level one-way

|

ANOVAs to test for differences between the three groups: healthy controls, moderately and severely affected stroke patients (level of significance P 5 0.05). Post hoc t -tests (healthy versus moderate, healthy versus severe, moderate versus severe) were added in case of significant ANOVA results ( post hoc t -tests: level of significance, P 5 0.05, FDR-corrected).

### Domain-wide segregation

In addition to qualitatively describing connectivity patterns across motor domains for static and dynamic connectivity configurations, we computed respective segregation values using a formula proposed by Chan et al. (2014) and Wig (2017):

System segregation ¼ mean ð Zw Þ   mean ð Zb Þ mean ð Zw Þ (1)

Mean(Zw) here represents the average of all within-domain correlations, while mean(Zb) denotes the average of all between-domain correlations, measured as Fisher's Z -transformed r . Note that we set all negative correlation values to 0 in accordance with Chan et al. (2014).

In the case of static between-network connectivity, we computed one segregation value per subject (and thus static connectivity matrix) and tested for group differences in segregation using a one-way ANOVA with three levels (healthy controls, moderately affected patients, and severely affected patients, level of significance: P 5 0.05). In contrast, in the case of dynamic network connectivity, we calculated 159 segregation values per subject, given that we had obtained one dynamic connectivity matrix per each of the 159 sliding windows. Analogous to the previous static analysis, we tested for group differences in a one-way ANOVA framework (healthy controls, moderately affected patients, and severely affected patients, level of significance: P 5 0.05), this time entering 159 -subject dynamic connectivity matrices in total. We furthermore evaluated connectivity state differences in segregation, also by means of a one-way ANOVA with three levels (connectivity state 1, connectivity state 2, and connectivity state 3, level of significance: P 5 0.05).

### Replication analysis

To verify the main results reported for the sample described above, an independent replication sample of n = 24 acute stroke patients with hand motor impairments and n = 30 control patients was used (see Supplementary material for more details).

### Data and code availability

MATLAB scripts for dFNC computation were based on templates available in the GIFT toolbox, additional jupyter notebooks in python 3.7 for statistical evaluations and visualizations can be found here: https://github.com/AnnaBonkhoff/DFNC_Stroke.

### Results

### Demographic and clinical characteristics

There were no significant differences in age, sex category and mean framewise displacement between healthy controls and all stroke patients (Table 1). Patients were scanned 7.2 [ ± 0.6 standard error of the mean (SEM)] days after stroke onset with no statistically significant difference in time since stroke between subgroups.

As we defined patient subgroups based on a discrete ARAT cut-off of 29 (i.e. half of the maximum score), severely affected patients ( n = 13, ARAT 5 29) and moderately affected patients ( n = 18, ARAT 5 29) differed significantly in regard to their motor performance ( P 5 0.05): arm motor function was significantly lower in the severely affected group (ARAT = 10.0 ± 3.1 SEM) compared to the moderately affected group (ARAT = 44.5 ± 2.4 SEM). In contrast, covariates including age, days post-stroke and lesion volume did not significantly differ between groups (Supplementary Table 1).

### Static functional network connectivity

### Within-network connectivity

MANCOVANanalyses indicated statistically significant group differences between healthy controls, moderately affected and severely affected stroke patients within the spatial maps of seven of eight cortical sensorimotor components and one subcortical component (sensorimotor cortex left and right, SMA, paracentral I and II, postcentral and superior parietal, but not the ventral precentral cortex; putamen II). Subsequent univariate, i.e. voxel-wise analyses, centring on group differences (healthy controls-moderately affected stroke patients, healthy controls-severely affected stroke patients, moderately affected stroke patients-severely affected stroke patients) and signal intensities of each voxel within a spatial map, provided further evidence of significantly lowered within-network connectivity in the motor system early after stroke (Fig. 2E). Here, patients with moderate motor deficits featured more widespread reductions of connectivity within cortical sensorimotor networks compared to healthy controls, whereas severely affected patients showed more circumscribed connectivity reductions compared to healthy controls (Fig. 2E). However, when comparing both patient groups statistically, we only obtained a very small cluster of voxels with lowered signal intensity located in ipsilesional sensorimotor cortex ( P 5 0.05, FDRcorrected for multiple comparisons).

### Between-network connectivity

Static functional network connectivity (over the entire scanning time series) was calculated as (Fisher Z -scored) Pearson's correlation between 78 individual component pairs. In general, we observed strong intra-domain connectivity, i.e. component pairs within either the sensorimotor, subcortical or cerebellar domains were highly positively correlated. In contrast, inter-domain connectivity was comparably low, i.e. components from sensorimotor and subcortical or cerebellar domains were either independent from each other or negatively connected (Fig. 1B). When screening for group differences between controls, moderately and severely affected patients by means of a one-way ANOVA, 18

|

*[picture on PDF page 7]*

**Figure labels:**
- A
- B
- C
- 12
- All patients
- CST Overlap
- Moderate
- Severe
- Deficits
- E
- Putamen II
- Sensorimotor left
- Postcentral left
- Paracentrall
- Sensorimotor right
- Postcentral
- right
- Significantly lower
- signal intensity than controls
- Within-network connectivity
- Moderately affected patients
- Severely affected patients
- Moderately > Severely affected patients

connectivity pairs showed significantly altered between-network component connectivity. These alterations were mostly located in the cortical sensorimotor domain (Fig. 1B). Post hoc t -tests, contrasting severely affected patients and healthy controls, revealed a stroke-induced increase in connectivity between subcortical components ( P 5 0.05, FDR-corrected). In contrast, moderately affected patients comprised decreases in connectivity strength when compared to healthy controls ( P 5 0.05, FDR-corrected). For example, connectivity was lower between the left and right sensorimotor components and ventral precentral components, as well as postcentral components and the supplementary motor area and both cerebellar components (see Fig. 3 for details on altered connectivity pairs). Moderately and severely affected patients did not feature significantly different static connectivity after correction for multiple comparisons.

### Dynamic functional network connectivity

We next investigated the temporal properties of functional connectivity, i.e. dFNC. By applying the k -means clustering algorithm to the estimated 159 functional connectivity matrices per subject and the optimization criteria for the number of states mentioned above (Fig. 4B), we identified three connectivity states, i.e. quasi-stable connectivity patterns, that reoccurred across all subjects during functional MRI scanning. The states are presented and described in the order given by k -means clustering. The first connectivity state was characterized by highly positive intra-domain connectivity and highly negative inter-domain connectivity. We refer to this state as the 'regionally densely connected' state with strong inter-domain segregation (overall frequency of State 1: 29%, Fig. 4A). This connectivity state was also the one that most closely matched the static connectivity estimates in terms of Manhattan distance. The second connectivity state featured comparably weak intra-domain connectivity, which was particularly true for connections of the ventral precentral and postcentral components. Inter-domain connectivity values close to zero additionally implied a low connectivity between the three domains. We therefore call this state the 'weakly connected' state (overall frequency

|

*[picture on PDF page 8]*

**Figure labels:**
- A
- B
- Paracentral
- SMA
- Postcentral
- SernsotrL
- Sensootlor
- SensotrR
- Paracentral_II
- SensomtrR
- Paracentral_ll
- Ventral_Precentral
- Superior_parietal
- Cerebellum_L
- Cerebellum_R
- Putamen_l
- Putamen_1
- Thalamus
- Putamen_II
- Significantly more connected
- Putamen_I
- than controls
- Significantly less connected
- Moderately affected patients
- Severely affected patients

of State 2: 43%, Fig. 4A). The third connectivity state represented a combination of the preceding two: positive intra-domain connectivity, slightly positive connectivity between the sensorimotor and subcortical domains and negative connectivity between the cerebellar and both of the sensorimotor and subcortical domains (overall frequency of State 3: 27%, Fig. 4A). Therefore, instead of one static connectivity state in the form of one FNC matrix, we now obtained three dynamic connectivity states and dFNC matrices. Importantly, one dynamic connectivity state, the weakly connected State 2, differed markedly from the static version.

### Temporal characteristics

We subsequently tested for between-group differences in the measures of dynamic behaviour. Three-level one-way ANOVAs comparing healthy controls, moderately and severely affected stroke patients revealed significant differences of temporal features in State 2, i.e. the weakly connected state (fraction and dwell times of State 2: P 5 0.05) (Fig. 5A and B). Moderately affected patients had the most deviating behaviour: when contrasted with healthy controls, they particularly preferred State 2 and spent more time in it in total as well as dwelled longer once having entered it ( post hoc t -tests: fraction and dwell times P 5 0.05, FDR-corrected).

With respect to severely affected patients, moderately affected patients again tended to spend more time in State 2 ( post hoc t -tests: faction time: P = 0.07, FDR-corrected; dwell time: not significant). In contrast, there were no significant between-group differences for the absolute number of transitions between states. Subjects switched five to seven times on average during the entire scanning period (one-way ANOVA: P 4 0.05, Fig. 5C).

Next, we evaluated the transition likelihoods between states. There were significant between-group effects (ANOVA P 5 0.05) with respect to the likelihood of staying within a state and switching to a new one; consistent with the observed increase in fraction and dwell times in State 2, moderately affected patients were more likely to stay in the weakly connected state compared to both healthy controls and severely affected patients ( post hoc t -tests: P 5 0.05, FDRcorrected). Of note, severely affected patients presented with a markedly different behaviour. They were not only less likely to remain in the weakly connected State 2, but demonstrated a significant preference for the regionally densely connected State 1. Coming from State 2, they were more likely to switch to State 1 compared to moderately affected patients ( post hoc t -tests: P 5 0.05, FDR-corrected) and healthy controls ( P = 0.056, FDR-corrected, Fig. 6). Moderately affected patients and controls did not differ in this aspect.

|

*[picture on PDF page 9]*

**Figure labels:**
- A
- Dynamic connectivity states of all participants
- State 1:2237 (29 %)State 2: 3318 (43 %)
- State 3: 2077 (27 %)
- 0.6
- SMN
- 0.4
- Correlations (z)
- 02
- -0.2
- S
- .0.4
- -0.6
- B
- -0.8
- Elbow criterion
- C
- State 1
- State 2
- State 3
- Cluster validity index
- 0.8
- Controls n = 13 (77%)
- Controls n = 15 (88%)
- Controls n = 16 (94%)
- 0.2
- 2
- 3
- 6
- Number of clusters
- Percentage of dFNC
- 08
- Moderate n = 13 (72%)
- Moderate n = 17 [94%]1
- 09
- 40
- 20
- 7
- Severe n = 11 (85%)
- Severe n = 12 (92%)
- Severe n = 9 (69%]

### Dynamic connectivity characteristics

Lastly, we examined between-group differences in connectivity strengths for each of the three connectivity states. While we did not detect any significant effects for State 1, i.e. the regionally densely connected state, moderately affected patients featured a number of differences in States 2 and 3 compared to both severely affected patients and healthy

|

*[picture on PDF page 10]*

**Figure labels:**
- A
- (*)
- B
- C
- 16
- Controls
- Moderately affected
- 160
- 14
- 1.0
- Severely affected
- 140
- 12
- Fraction time
- 0.8
- Dwell time
- 100
- 120
- Traniions
- 10
- 0.6
- 80
- 8
- 0.4
- 60
- 6
- 40
- 4
- 0.2
- 20
- 2
- 0.0
- t.0
- 2.0
- 3.0
- 0
- State

*[picture on PDF page 10]*

**Figure labels:**
- To State
- 1
- 2
- 3
- Difference in transition likelihood (%)
- 0.08
- From State
- 0.04
- *
- 0.00
- -0.04
- Controls - Moderately affected
- Controls - Severely affected
- Moderately - Severely affected

controls. This was especially true with respect to the connectivity of ipsilesional primary sensorimotor cortex and subcortical components (Fig. 7). In moderately affected patients, connectivity differences in State 3 matched those of the static analysis to a great extent, with reduced connectivity in stroke patients between the ipsilesional left and contralesional right sensorimotor components, as well as bi-hemispherical SMA and one of the paracentral lobule components. Of note, we found reduced connectivity between the right contralesional sensorimotor and paracentral lobule components when contrasting severely affected patients with controls. This interhemispheric difference was not detectable in the static analysis and can hence be interpreted as increased sensitivity of the dynamic analysis. Lastly, moderately and severely affected patients differed in three cortical-subcortical-cerebellar connectivity strengths: paracentral-putamen, left sensorimotor-putamen and putamen-left cerebellum (Fig. 7).

### Differences in domain-wide segregation

For static connectivity data, we did not observe a significant difference in domain-wide segregation across healthy controls and both patient groups (three-level ANOVA: P = 0.39). This situation changed distinctly once we considered dynamic

|

*[picture on PDF page 11]*

**Figure labels:**
- A
- B
- SMA
- Paracentral_N
- Controls n = 15 (88%)
- Controls n = 16 [94%]
- Superior_parietal
- Carebeßum_L
- Cerebetlum_L
- Thalamus
- Moderate n = 17 [94%]
- Moderate n = 13 [72%]
- Connectivity State 2: Moderately affected patients > Controls
- Connectivity State 3: Moderately affected patients > Controls
- C
- D
- Paracentnal
- Paracentral
- Postcertral
- Paracentral_
- Paracentral_8
- Controls n = 16 (94%]
- Supenior_parietal
- Cerebeluan_L
- Cerebelum_L
- Significantly less connected
- Severe n = 9 [69%]
- Connectivity State 3: Severely affected patients > Controls
- Connectivity State 3: Severely affected patients > Moderately affected patients

connectivity data; a significant ANOVA-result ( P 5 0.001) indicated an overall difference between controls and the two patient groups. Post hoc t -tests revealed significant differences between all of the subgroup constellations. Moderately affected patients presented with significantly lower segregation values than healthy controls and severely affected patients, while severely affected patients had higher segregation values than healthy controls and moderately affected patients ( post hoc t -tests: P 0.001, FDR-corrected for multiple comparisons; system segregation: healthy controls: 0.83, moderately affected: 0.81, severely affected: 0.87). Furthermore, the three connectivity states significantly diverged in their degree of segregation: State 1, the densely connected state, was also the one with the highest degree of segregation, followed by the less segregated States 2 and 3 (three-level ANOVA: P 0.001, post hoc t -tests: P 5 0.01, FDR-corrected for multiple comparisons, State 1: 0.95, State 2: 0.89, State 3: 0.83). Therefore, the reduced degree of segregation that moderately affected patients presented with was also expressed in their longer dwell and fraction times in State 2, a comparatively less segregated state. Conversely, the significantly higher transition likelihood of severely affected patients into State 1 matches their higher degree of segregation in comparison to moderately affected patients and healthy controls.

### Replication analysis

We repeated the main dynamic connectivity analysis steps in an independent sample of 24 acute ischaemic stroke patients with motor symptoms to test the robustness of our findings. A group of 30 age-matched ischaemic stroke patients without

|

any motor symptoms replaced the healthy control sample of the main analysis. Once again, we identified three connectivity states that resembled those in the main analysis. We obtained a highly connected State 1, a weakly connected State 2, and a State 3 combining integration between cortical and subcortical motor areas and segregation between cortical motor and cerebellar areas (Supplementary Fig. 4). Importantly, we could replicate significantly increased dwell times in State 2 in the case of moderately affected patients compared to stroke patients presenting without any motor symptoms. Furthermore, we found significantly increased inter-domain segregation in patients with severe motor symptoms, as was reflected by a significantly higher intra-domain compared to inter-domain connectivity (Chan et al. , 2014). Stroke patients with moderate motor symptoms presented with a significant reduction in inter-domain segregation. Therefore, we were able to replicate the main findings in a completely independent dataset, which was scanned in a different setting, with different technical parameters and field strengths. These findings underscore the robustness of the dynamic connectivity changes observed for patients with motor impairments very early after stroke (see Supplementary material for a detailed description of results).

### Summary

In summary, we found significant differences in the preferences for connectivity states depending on the degree of motor impairment. While moderately affected patients spent more time in a weakly connected state, severely affected patients transitioned more often to a regionally densely connected state with strong intra-domain (e.g. cortico-cortical) connectivity and negative inter-domain (e.g. cortico-subcortical) connectivity. These differences in dynamic connectivity patterns were also reflected by an overall decreased network segregation in case of moderate motor symptoms and increased segregation in case of severe symptoms. Importantly, these impairment-related differences in network segregation did not emerge in the static analysis. Interestingly, and somewhat surprisingly, functional connectivity estimates differed more between moderately affected patients and healthy controls than between severely affected patients and healthy controls. This was particularly the case for disturbed static functional connectivity between specific brain regions, where moderately affected patients presented with multiple reduced functional connectivity pairs. In cases of severely affected patients and the static between-network analysis, we found altered functional connectivity pairs only in the subcortical domain. Disturbances at the level of cortical regions became evident exclusively in the dynamic analysis. We here substantiated lowered between-network connectivity for the contralesional sensorimotor and paracentral lobule components post-stroke, indicating an added benefit of dynamic analysis.

### Discussion

DFNC analyses encompass the capacity of more fine-grained conclusions in the temporal domain when working with functional resting state MRI data (Allen et al. , 2014; Calhoun et al. , 2014). In this study, we dissected the dynamic connectivity behaviour of ischaemic stroke patients within the first few days of their acute event, putting a particular emphasis on hand motor function and the sensorimotor system. We here considered behaviourally well-characterized stroke patients with symptoms ranging from mild upper limb impairment to complete paralysis, which therefore reflected a comprehensive clinical spectrum of motor impairments. Of note, stroke patients diverged from healthy controls depending on the severity of their motor deficit. Patients with severe motor symptoms showed a significant preference for transitioning to State 1, a regionally densely connected state with strong intra-domain connectivity. Conversely, moderately impaired patients spent significantly more time in State 2, a weakly connected state. Both of these patterns remained hidden in previous conventional static analyses. The third connectivity state did not differ in terms of dynamic connectivity specific measures, such as transitions, fraction and dwell times, but reflected many of the connectivity differences observed in the static analysis and previously described in the literature (Carter et al. , 2010; Wang et al. , 2010; Golestani et al. , 2013; Rehme et al. , 2014). Contrary to our initial expectations, moderately affected patients comprised more pronounced alterations in functional connectivity for both the static and dynamic analyses, despite their weaker clinical deficit. These alterations were located between the ipsiand contralesional sensorimotor cortices as well as the contralesional sensorimotor cortex and bilateral paracentral cortex. Importantly, in case of severe motor symptoms, significantly reduced inter-hemispheric connectivity between cortical sensorimotor components was exclusively found in the dynamic analysis, highlighting its higher sensitivity in comparison to the static analysis.

### Functional integration and segregation

Dynamic connectivity states can be interpreted within the concepts of functional integration and functional segregation (Eickhoff and Grefkes, 2011; Friston, 2011). Functional segregation refers to the parcellation of the brain into regionally unique modules (i.e. areas), each of which may be assigned to a particular domain. These domains can either orchestrate information transmission from one to the other (referred to as integration) or process information in isolation (referred to as segregation), essentially balancing the two extremes to maintain healthy brain function (Sporns, 2013). Below, we evaluate the computed three connectivity states within the framework of these concepts .

### Severely affected patients and State 1

The regionally densely connected State 1 was characterized by highly positive intra-domain connectivity, i.e. within the sensorimotor, subcortical or cerebellar domains, and negative inter-domain connectivity, i.e. between sensorimotor-subcortical, sensorimotor-cerebellar and subcorticalcerebellar domains. Altogether, this can be interpreted as high segregation between domains. In view of the significantly increased transition likelihood to this State 1, severely affected patients thus preferred a state where information could easily travel from one component to another in the same domain. However, information exchange between components of distinct domains was hindered. This high intra-domain connectivity or integration was reminiscent of the over-activation and excessive recruitment of cortical motor areas, particularly of contralesional M1, bilateral premotor cortex and SMA, in task-based studies post-stroke (e.g. Ward et al. , 2003; Rehme et al. , 2011, for a review see Rehme et al. , 2012). Importantly, Rehme et al. , 2011 uncovered these activity changes exclusively for severely affected patients, starting a few days after stroke, and suggested these to represent early signs of reorganization. Conceivably, the observed dynamic pattern here, even though expressing connectivity instead of activation and recruitment, could be a respective correlate, demonstrating the increased employment of functional connections within welldefined domains, aiming to recover lost motor performance. This specific pattern may not have been discovered and described in preceding static analyses, as it was solely expressed in the temporal markers of our dynamic analysis.

Segregation, as a measure of spatial functional specialization, can be quantified in multiple ways and is often linked to brain modularity. This graph theoretical measure compares densities of connections within and between domains, with higher values implying greater modularity and segregation of domains (Newman, 2004). Brain modularity was recently suggested as biomarker of intervention-related brain plasticity, since higher baseline values of modularity were shown to be predictive of later gains in cognitive function (Gallen and D'Esposito, 2019). This relationship could be established not only for healthy ageing brains, but also, notably, structurally damaged brains of patients with traumatic brain injury (Arnemann et al. , 2015; Gallen et al. , 2016; Baniqued et al. , 2018). Similarly, when limiting analyses to the cortical motor and visual domains, Mattar et al. (2018) extracted a link between pronounced modularity and prospective motor skill learning. In these regards, the predilection of severely affected patients for the segregated State 1 could represent an attempt to facilitate brain plasticity enabling motor recovery. Nonetheless, it has previously been hypothesized that modularity and segregation might follow an inverse U-shaped curve and values on either end of the scale could co-occur with maladaptive behaviour (Duncan and Small, 2016). Therefore, not having any available long-term behavioural markers prohibits a definitive conclusion at this point and necessitates future research to investigate links between segregation and motor recovery.

### Moderately affected patients and State 2

In contrast, moderately affected patients spent significantly more time in State 2 that comprised low intra-domain

|

integration and relatively increased inter-domain connectivity, which is interpretable as reduced segregation. Decreased segregation has been found in healthy as well as pathological ageing (Chan et al. , 2014; Kim et al. , 2017; Wig, 2017). In principle, this pattern of decreased segregation is also well in line with previous reports of reductions in modularity poststroke, reflecting a decrease in segregation between domains (Gratton et al. , 2012; Duncan and Small, 2016; Siegel et al. , 2016, 2018). Duncan and Small (2016) and Siegel et al. (2018) reported initially reduced and subsequently increasing segregation in parallel to functional recovery, suggesting reduced segregation to be a signature of impaired function. However, substantial differences in average scanning time after stroke [i.e. 2 weeks (Siegel et al. , 2018), 40 months (Duncan and Small, 2016) and 1 week in our study] and clinical deficit [i.e. predominantly cognitive symptoms (Siegel et al. , 2018), aphasia (Duncan and Small, 2016) and motor symptoms here] impede any direct transfer of their conclusions to our findings. The interpretation of reduced segregation in moderately affected patients as a correlate of impaired function is additionally challenged by the fact that clinically more affected patients did not show similar alterations. Hence, in our setting, reduced segregation rather appeared as a signature of (early) reorganization, given that moderately and severely affected patients differed in motor performance by definition, but not in lesion volume or corticospinal tract overlap. This interpretation is supported by comparable findings of increasing integration (i.e. decreasing segregation) in case of recovery after traumatic brain injury (Kuceyeski et al. , 2019). Also, one could imagine that new connections could be more easily established starting from a weakly connected state, providing a basis for higher network flexibility. In contrast, the regionally densely connected State 1 with high intra-domain, yet low inter-domain connectivity might facilitate regional processing and hence reorganization in the case of a severe disruption of motor output.

Contextualizing our findings of altered dynamic connectivity patterns in acute stroke patients with motor symptoms: Hu et al. (2018) investigated regional dynamic connectivity in 19 patients with acute ischaemic stroke (on average 4 days post-stroke) with moderate motor symptoms and described an initial reduction of temporal variability in primary motor, auditory and visual cortex compared to healthy controls. Chen et al. (2018) computed whole-brain dynamic connectivity for 64 patients with subacute stroke (7-31 days post-stroke) and substantiated significant dynamic connectivity differences (relative to healthy controls), primarily affecting connections between either contraor ipsilesional M1 regions and visual, insular and inferior parietal regions. Duncan and Small (2018) established a first link between dynamic connectivity and recovery in chronic stroke. They leveraged the sliding window approach to track dynamic network changes of 12 chronically aphasic stroke patients (on average 40 months post-stroke) during a 6-week intervention. Estimating 10 different connectivity states in total, the increase in dwell time in one of these, a particularly weakly connected state, correlated with an increase in

|

language performance. Lastly, we may compare our findings to those originating from a study with patients suffering from small vessel disease. Clinically, patients with subcortical ischaemic vascular dementia predominantly present with prolonged and not necessarily acute onset neurocognitive decline as well as chronic deep white matter hyperintensities and subcortical lacunar infarcts (Hachinski et al. , 2006). The analysis of their dynamic functional connectivity revealed that fraction and dwell times were increased in a weakly connected state and reduced in a densely connected state; the former finding being much alike our main finding for moderately affected patients. Altogether, the previous and present findings suggest a consistently present link between dynamic measures and vascular disease, rendering it a promising future technique in the field of neurorehabilitation.

### Limitations and future directions

Although our sample size of 31 acute stroke patients is relatively small, it was apparently equipped with sufficient statistical power, especially given the replication of previous static functional connectivity findings. We were able to exploit detailed measures of motor function by relying on a competitive group size of severely affected patients ( n = 13) ( cf. , 6-10 severely affected patients in Carter et al. , 2010; Wang et al. , 2010; Park et al. , 2011; Golestani et al. , 2013; Rehme et al. , 2014). We further link current limitations to future directions: in light of the spatial heterogeneity of stroke lesions as well as not yet satisfactorily accurate predictions of individual recovery trajectories, future studies should involve larger sample sizes and evaluate symptoms in a finegrained as well as prospective fashion to corroborate and extend current finding. In this way, confidence in their generalizability could be further increased. Eventually, this would represent a natural succession to the approach presented here, where we focused on dynamic connectivity differences within motor-related networks at the acute stage post-stroke. It would enable elucidating pressing questions, such as: are dynamic connectivity measures predictive of future outcomes, especially in regard to treatment effects, including TMS and transcranial direct current stimulation (tDCS)? How do non-motor symptoms affect dynamic connectivity comprising all conceivable domains? How do dynamic connectivity measures evolve over time? Existing literature already suggests a delicate relationship between connectivity changes and the exact time point post-stroke. It has been shown that asymmetries in bi-hemispherical connectivity peaked approximately 1 month after the acute event (Park et al. , 2011) and, considering rats, different temporal trajectories emerged depending on lesion location (van Meer et al. , 2010). Asynchronistic behaviour could conceivably explain why severely and moderately affected patients differed in their dynamic connectivity profiles in our analysis. As a reasonable interpretation, moderately affected patients may have traversed through a more segregated phase already when regaining function, while severely affected patients lagged behind. Moreover, it remains to be elucidated whether the dynamic connectivity changes that we observe here reflect adaptive and maladaptive effects. Lastly, it might be promising to link findings of functional MRI determined connectivity states to micro states as inferred from EEG data, in light of the increased temporal resolution in both cases (with EEG providing even higher temporal resolutions) (Zappasodi et al. , 2017).

### Conclusion

Dynamic functional connectivity analyses hold promise to capture critical characteristics of cognition and behaviour in health and disease (Hutchison et al. , 2013). In this study, we build upon this notion by implementing dynamic functional connectivity analyses to investigate the temporal behaviour within the motor system of 31 acute stroke patients presenting with impairments of hand motor function. Significant deficit-severity dependent dynamic patterns demonstrated the added value of dynamic connectivity measures as (resting state) biomarkers of ischaemic vascular disease. Patients with severe deficits preferred a regionally densely connected, highly segregated state, i.e. a condition previously associated with an enhanced level of brain plasticity (Gallen and D'Esposito, 2019). On the other hand, patients with moderate deficits spent significantly more time in a weakly connected state with reduced segregation. Therefore, the degree of motor impairment seemed to be associated with differential dynamic network reorganization patterns in acute stroke patients. Importantly, these impairment-related network effects have not been detected in previous static connectivity studies in early stroke. Likewise, classical task-based activation studies did not detect differential reorganization patterns for patients with mild-to-moderate motor impairments either (Rehme et al. , 2011). Hence, using a dynamic connectivity approach allowed new insights into the systems-level effects that a stroke has on neural processing within the motor system, pointing to differential reorganizational mechanisms depending on the initial motor deficit. In the future, these insights might be of particular importance when aiming to interfere with network reorganization very early after stroke, e.g. when inducing cortical plasticity using non-invasive brain stimulation to promote recovery of function (Grefkes and Fink, 2012; Lefaucheur et al. , 2020).

### Acknowledgements

We are grateful to our colleagues at the Department of Neurology, University Hospital Cologne and Medical Faculty, University of Cologne for valuable support and discussions. Furthermore, we are grateful to our research participants without whom this work would not have been possible.

### Funding

A.K.B's clinician scientist position is supported by the Dean's Office, Faculty of Medicine, University of Cologne.

### Competing interests

The authors report no competing interests.

### Supplementary material

Supplementary material is available at Brain online.

### References

- Aggarwal CC, Hinneburg A, Keim DA. On the surprising behavior of distance metrics in high dimensional space. In: International Conference on Database Theory. Springer; 2001. P. 420-34
- Allen EA, Damaraju E, Plis SM, Erhardt EB, Eichele T, Calhoun VD. Tracking whole-brain connectivity dynamics in the resting state. Cereb Cortex 2014; 24: 663-76.
- Allen EA, Erhardt EB, Damaraju E, Gruner W, Segall JM, Silva RF, et al. A baseline for the multivariate comparison of resting-state networks. Front Syst Neurosci 2011; 5: 2.
- Arnemann KL, Chen A-W, Novakovic-Agopian T, Gratton C, Nomura EM, D'Esposito M. Functional brain network modularity predicts response to cognitive training after brain injury. Neurology 2015; 84: 1568-74.
- Ashburner J, Friston KJ. Unified segmentation. Neuroimage 2005; 26: 839-51.
- Baniqued PL, Gallen CL, Voss MW, Burzynska AZ, Wong CN, Cooke GE, et al. Brain network modularity predicts exercise-related executive function gains in older adults. Front Aging Neurosci 2018; 9: 426.
- Benjamini Y, Hochberg Y. Controlling the false discovery rate: a practical and powerful approach to multiple testing. J R Stat Soc: Ser B 1995; 57: 289-300.
- Calhoun VD, Adali T, Pearlson GD, Pekar JJ. A method for making group inferences from functional MRI data using independent component analysis. Hum Brain Mapp 2001; 14: 140-51.
- Calhoun VD, Miller R, Pearlson G, Adalı T. The chronnectome: timevarying connectivity networks as the next frontier in fMRI data discovery. Neuron 2014; 84: 262-74.
- Carrera E, Tononi G. Diaschisis: past, present, future. Brain 2014; 137: 2408-22.
- Carter AR, Astafiev SV, Lang CE, Connor LT, Rengachary J, Strube MJ, et al. Resting interhemispheric functional magnetic resonance imaging connectivity predicts performance after stroke. Ann Neurol 2010; 67: 365-75.
- Chan MY, Park DC, Savalia NK, Petersen SE, Wig GS. Decreased segregation of brain systems across the healthy adult lifespan. Proc Natl Acad Sci U S A 2014; 111: E4997-5006.
- Chang C, Glover GH. Time-frequency dynamics of resting-state brain connectivity measured with fMRI. Neuroimage 2010; 50: 81-98.
- Chen J, Sun D, Shi Y, Jin W, Wang Y, Xi Q, et al. Alterations of static functional connectivity and dynamic functional connectivity in motor execution regions after stroke. Neurosci Lett 2018; 686: 112-21.
- Cox RW. AFNI: software for analysis and visualization of functional magnetic resonance neuroimages. Comput Biomed Res 1996; 29: 162-73.

|

- Damaraju E, Allen EA, Belger A, Ford JM, McEwen S, Mathalon DH, et al. Dynamic functional connectivity analysis reveals transient states of dysconnectivity in schizophrenia. NeuroImage: Clin 2014; 5: 298-308.
- Du Y, Allen EA, He H, Sui J, Wu L, Calhoun VD. Artifact removal in the context of group ICA: a comparison of single-subject and group approaches. Hum Brain Mapp 2016; 37: 1005-25.
- Du Y, Fan Y. Group information guided ICA for fMRI data analysis. Neuroimage 2013; 69: 157-97.
- Duncan ES, Small SL. Increased modularity of resting state networks supports improved narrative production in aphasia recovery. Brain Connect 2016; 6: 524-9.
- Duncan ES, Small SL. Changes in dynamic resting state network connectivity following aphasia therapy. Brain Imaging Behav 2018; 12: 1141-9.
- Eickhoff SB, Grefkes C. Approaches for the integrated analysis of structure, function and connectivity of the human brain. Clin EEG Neurosci 2011; 42: 107-21.
- Espinoza FA, Liu J, Ciarochi J, Turner JA, Vergara VM, Caprihan A. et al. Dynamic functional network connectivity in Huntington's disease and its associations with motor and cognitive measures. Human Brain Mapping 2019; 40: 1955-68.
- Espinoza FA, Turner JA, Vergara VM, Miller RL, Mennigen E, Liu J, et al. Whole-brain connectivity in a large study of Huntington's disease gene mutation carriers and healthy controls. Brain Connectivity 2018; 8: 166-78.
- Friedman J, Hastie T, Tibshirani R. Sparse inverse covariance estimation with the graphical lasso. Biostatistics 2008; 9: 432-41.
- Friston K. Beyond phrenology: what can neuroimaging tell us about distributed circuitry? Annu Rev Neurosci 2002; 25: 221-50.
- Friston KJ. Functional and effective connectivity: a review. Brain Connect 2011; 1: 13-36.
- Gallen CL, Baniqued PL, Chapman SB, Aslan S, Keebler M, Didehbani N, et al. Modular brain network organization predicts response to cognitive training in older adults. PloS One 2016; 11: e0169015.
- Gallen CL, D'Esposito M. Brain modularity: a biomarker of intervention-related plasticity. Trends Cogn Sci 2019; 23: 293-304.
- Golestani A-M, Tymchuk S, Demchuk A, Goodyear BG; VISION-2 Study Group. Longitudinal evaluation of resting-state fMRI after acute stroke with hemiparesis. Neurorehabil Neural Repair 2013; 27: 153-63.
- Gratton C, Nomura EM, Pe ´rez F, D'Esposito M. Focal brain lesions to critical locations cause widespread disruption of the modular organization of the brain. J Cogn Neurosci 2012; 24: 1275-85.
- Grefkes C, Fink GR. Reorganization of cerebral networks after stroke: new insights from neuroimaging with connectivity approaches. Brain 2011; 134: 1264-76.
- Grefkes C, Fink GR. Disruption of motor network connectivity poststroke and its noninvasive neuromodulation. Curr Opin Neurol 2012; 25: 670-5.
- Grefkes C, Fink GR. Connectivity-based approaches in stroke and recovery of function. Lancet Neurol 2014; 13: 206-16.
- Hachinski V, Iadecola C, Petersen RC, Breteler MM, Nyenhuis DL, Black SE, et al. National Institute of Neurological Disorders and Stroke-Canadian stroke network vascular cognitive impairment harmonization standards. Stroke 2006; 37: 2220-41.
- Hu J, Du J, Xu Q, Yang F, Zeng F, Weng Y, et al. Dynamic network analysis reveals altered temporal variability in brain regions after stroke: a longitudinal resting-state fMRI study. Neural Plast 2018; 2018: 1-10.
- Hutchison RM, Womelsdorf T, Allen EA, Bandettini PA, Calhoun VD, Corbetta M, et al. Dynamic functional connectivity: promise, issues, and interpretations. NeuroImage 2013; 80: 360-78.
- Kim J, Criaud M, Cho SS, Dı ´ez-Cirarda M, Mihaescu A, Coakeley S, et al. Abnormal intrinsic brain functional network dynamics in Parkinson's disease. Brain 2017; 140: 2955-67.

|

- Kuceyeski AF, Jamison KW, Owen JP, Raj A, Mukherjee P. Longitudinal increases in structural connectome segregation and functional connectome integration are associated with better recovery after mild TBI. bioRxiv 2019; 320515.
- Lefaucheur J-P, Aleman A, Baeken C, Benninger DH, Brunelin J, Di Lazzaro V, et al. Evidence-based guidelines on the therapeutic use of repetitive transcranial magnetic stimulation (rTMS): an update (2014-2018). Clin Neurophysiol 2020; 131: 474-528.
- Lie ´ geois R, Ziegler E, Phillips C, Geurts P, Go ´mez F, Bahri MA, et al. Cerebral functional connectivity periodically (de) synchronizes with anatomical constraints. Brain Struct Funct 2016; 221: 2985-97.
- Lin Q-H, Liu J, Zheng Y-R, Liang H, Calhoun VD. Semiblind spatial ICA of fMRI using spatial constraints. Hum Brain Mapp 2010; 31: 1076-88.
- Lloyd S. Least squares quantization in PCM. IEEE Trans Inform Theory 1982; 28: 129-37.
- Lurie DJ, Kessler D, Bassett DS, Betzel RF, Breakspear M, Kheilholz S, et al. Questions and controversies in the study of time-varying functional connectivity in resting fMRI. Netw Neurosci 2020; 4: 30-69.
- Mattar MG, Wymbs NF, Bock AS, Aguirre GK, Grafton ST, Bassett DS. Predicting future learning from baseline network architecture. Neuroimage 2018; 172: 107-17.
- Newman M. Fast algorithm for detecting community structure in networks. Phys Rev E 2004; 69: 066133.
- Park C, Chang WH, Ohn SH, Kim ST, Bang OY, Pascual-Leone A, et al. Longitudinal changes of resting-state functional connectivity during motor recovery after stroke. Stroke 2011; 42: 1357-62.
- Power JD, Barnes KA, Snyder AZ, Schlaggar BL, Petersen SE. Spurious but systematic correlations in functional connectivity MRI networks arise from subject motion. Neuroimage 2012; 59: 2142-54.
- Preti MG, Bolton TA, Van De Ville D. The dynamic functional connectome: state-of-the-art and perspectives. Neuroimage 2017; 160: 41-54.
- Rachakonda S, Egolf E, Correa N, Calhoun V. Group ICA of fMRI toolbox (GIFT) manual. 2007. Dostupne ´z. Available from: http:// www nitrc org/docman/view php/55/295/v1 3d_ GIFTManual pdf (5 November 2011, date last accessed).
- Rehme AK, Eickhoff SB, Rottschy C, Fink GR, Grefkes C. Activation likelihood estimation meta-analysis of motor-related neural activity after stroke. Neuroimage 2012; 59: 2771-82.
- Rehme AK, Fink GR, von Cramon DY, Grefkes C. The role of the contralesional motor cortex for motor recovery in the early days after stroke assessed with longitudinal FMRI. Cereb Cortex 2011; 21: 756-68.
- Rehme AK, Volz LJ, Feis D-L, Bomilcar-Focke I, Liebig T, Eickhoff SB, et al. Identifying neuroimaging markers of motor disability in acute stroke by machine learning techniques. Cereb Cortex 2014; 25: 3046-56.
- Rousseeuw PJ. Silhouettes: a graphical aid to the interpretation and validation of cluster analysis. J Comput Appl Math 1987; 20: 53-65.
- Sako  glu U ¨ , Pearlson GD, Kiehl KA, Wang YM, Michael AM, Calhoun VD. A method for evaluating dynamic functional network connectivity and task-modulation: application to schizophrenia. Magn Reson Mater Phys 2010; 23: 351-66.
- Salman MS, Du Y, Lin D, Fu Z, Fedorov A, Damaraju E, et al. Group ICA for identifying biomarkers in schizophrenia:'Adaptive'networks via spatially constrained ICA show more sensitivity to group differences than spatio-temporal regression. NeuroImage: Clin 2019; 22: 101747.
- Siegel JS, Ramsey LE, Snyder AZ, Metcalf NV, Chacko RV, Weinberger K, et al. Disruptions of network connectivity predict impairment in multiple behavioral domains after stroke. Proc Natl Acad Sci U S A 2016; 113: E4367-76.
- Siegel JS, Seitzman BA, Ramsey LE, Ortega M, Gordon EM, Dosenbach NUF, et al. Re-emergence of modular brain networks in stroke recovery. Cortex 2018; 101: 44-59.
- Smith SM, Miller KL, Salimi-Khorshidi G, Webster M, Beckmann CF, Nichols TE, et al. Network modelling methods for FMRI. NeuroImage 2011; 54: 875-91.
- Sporns O. Network attributes for segregation and integration in the human brain. Curr Opin Neurobiol 2013; 23: 162-71.
- van der Horn HJ, Vergara VM, Espinoza FA, Calhoun VD, Mayer AR, van der Naalt J. Functional outcome is tied to dynamic brain states after mild to moderate traumatic brain injury. Hum Brain Mapp 2019; 41: 617-631.
- van Meer MP, van der Marel K, Wang K, Otte WM, el Bouazati S, Roeling TA, et al. Recovery of sensorimotor function after experimental stroke correlates with restoration of resting-state interhemispheric functional connectivity. J Neurosci 2010; 30: 3964-72.
- Varoquaux G, Gramfort A, Poline J-B, Thirion B. Brain covariance selection: better individual functional connectivity models using population prior. In: Advances in Neural Information Processing Systems; 2010. p. 2334-42.
- Vergara VM, Mayer AR, Kiehl KA, Calhoun VD. Dynamic functional network connectivity discriminates mild traumatic brain injury through machine learning. NeuroImage: Clin 2018; 19: 30-7.
- Vidaurre D, Arenas AL, Smith SM, Woolrich MW. Behavioural relevance of spontaneous, transient brain network interactions in fMRI. bioRxiv 2019; 779736.
- Volz LJ, Rehme AK, Michely J, Nettekoven C, Eickhoff SB, Fink GR, et al. Shaping early reorganization of neural networks promotes motor function after stroke. Cereb Cortex 2016; 26: 2882-94.
- von Monakow C. Die Lokalisation im Grosshirn und der Abbau der Funktion durch kortikale Herde. Munich: JF Bergmann; 1914.
- Wang L, Yu C, Chen H, Qin W, He Y, Fan F, et al. Dynamic functional reorganization of the motor execution network after stroke. Brain 2010; 133: 1224-38.
- Ward NS. Restoring brain function after stroke-bridging the gap between animals and humans. Nat Rev Neurol 2017; 13: 244.
- Ward NS, Brown MM, Thompson AJ, Frackowiak R. Neural correlates of outcome after stroke: a cross-sectional fMRI study. Brain 2003; 126: 1430-48.
- Wig GS. Segregated systems of human brain networks. Trends Cogn Sci 2017; 21: 981-96.
- Yozbatiran N, Der-Yeghiaian L, Cramer SC. A standardized approach to performing the action research arm test. Neurorehabil Neural Repair 2008; 22: 78-90.
- Zappasodi F, Croce P, Giordani A, Assenza G, Giannantoni NM, Profice P, et al. Prognostic value of EEG microstates in acute stroke. Brain Topogr 2017; 30: 698-710.