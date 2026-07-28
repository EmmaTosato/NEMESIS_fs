### BRAIN COMMUNICATIONS

### A low-dimensional structure of neurological impairment in stroke

Antonio Luigi Bisogno, 1,2 Chiara Favaretto, 1,2 Andrea Zangrossi, 1,2 Elena Monai, 1,2,3 Silvia Facchini, 1,2 Serena De Pellegrin, 3 Lorenzo Pini, 2 Marco Castellaro, 4 Anna Maria Basile, 3 Claudio Baracchini 1,3 and Maurizio Corbetta 1,2,3,5

Neurological deficits following stroke are traditionally described as syndromes related to damage of a specific area or vascular territory. Recent studies indicate that, at the population level, post-stroke neurological impairments cluster in three sets of correlated deficits across different behavioural domains. To examine the reproducibility and specificity of this structure, we prospectively studied first-time stroke patients ( n ¼ 237) using a bedside, clinically applicable, neuropsychological assessment and compared the behavioural and anatomical results with those obtained from a different prospective cohort studied with an extensive neuropsychological battery. The behavioural assessment at 1-week post-stroke included the Oxford Cognitive Screen and the National Institutes of Health Stroke Scale. A principal component analysis was used to reduce variables and describe behavioural variance across patients. Lesions were manually segmented on structural scans. The relationship between anatomy and behaviour was analysed using multivariate regression models. Three principal components explained  50 % of the behavioural variance across subjects. PC1 loaded on language, calculation, praxis, right side neglect and memory deficits; PC2 loaded on left motor, visual and spatial neglect deficits; PC3 loaded on right motor deficits. These components matched those obtained with a more extensive battery. The underlying lesion anatomy was also similar. Neurological deficits following stroke are correlated in a low-dimensional structure of impairment, related neither to the damage of a specific area or vascular territory. Rather they reflect widespread network impairment caused by focal lesions. These factors showed consistency across different populations, neurobehavioural batteries and, most importantly, can be described using a combination of clinically applicable batteries (National Institutes of Health Stroke Scale and Oxford Cognitive Screen). They represent robust behavioural biomarkers for future stroke population studies.

- 1 Department of Neuroscience, University of Padova, Padova 35100, Italy
- 2 Padova Neuroscience Center (PNC), University of Padova, Padova 35100, Italy
- 3 Azienda Ospedaliera Universita ` di Padova, Padova 35100, Italy
- 4 Department of Information Engineering, University of Padova, Padova 35100, Italy
- 5 Venetian Institute of Molecular Medicine, Padova 35100, Italy

Correspondence to: Maurizio Corbetta

Clinica Neurologica, Dipartimento di Neuroscienze

Universita' di Padova, via Giustiniani 2, 37128 Padova, Italy

E-mail: maurizio.corbetta@unipd.it

Keywords: stroke; biomarkers; behavioural; dimensionality

Abbreviations: MCA ¼ middle cerebral artery; NIHSS ¼ National Institutes of Health Stroke Scale; OCS ¼ Oxford Cognitive Screen; PC ¼ principal component; PCA ¼ principal component analysis; RR ¼ ridge regression; WU ¼ Washington University St. Louis

Received September 11, 2020. Revised March 03, 2021. Accepted June 01, 2021

> C The Author(s) (2021). Published by Oxford University Press on behalf of the Guarantors of Brain.This is an Open Access article distributed under the terms of the Creative

> V Commons Attribution License (http://creativecommons.org/licenses/by/4.0/), which permits unrestricted reuse, distribution, and reproduction in any medium, provided the original work is properly cited.

|

### Graphical Abstract

### Introduction

'You learn neurology stroke by stroke' C.M. Fisher (1961)

Neurologists traditionally classify behavioural syndromes based on the damage of specific brain regions (e.g. Broca aphasia) or the vascular distribution of stroke [e.g. middle cerebral artery (MCA)]. When behavioural deficits are correlated the explanation is that adjacent cortical regions suffer from the injury, be it ischaemia, as in right hemiplegia and Broca aphasia, or abnormal electrical activity, as in the Jacksonian march. 1-3 Dr Fisher described more than 70 different syndromes caused by focal ischaemia in his work. 1

However, recent work offers a different perspective showing that syndrome-based descriptions do not characterize behavioural deficits at the population level. For instance, the examination of samples of stroke patients with the National Institutes of Health Stroke Scale (NIHSS) identifies two factors: one for left and one for right hemisphere lesions, which split respectively in a cognitive and sensory-motor component, accounting for approximately 80% of behavioural variability across subjects. 4,5

Since cognitive deficits are only cursorily measured by the NIHSS, this simplified model may reflect a lack of sensitivity for impairment in multiple cognitive domains. However, a more recent analysis in a prospective sample of stroke patients ( n ¼ 132), tested with an extensive neuropsychological battery (44 tests covering multiple domains: language, motor, vision, memory, attention) at Washington University (WU) in St. Louis, discovered that three deficit components account for the majority (65%) of variability in performance. 6 These factors remained at three-twelve months post-stroke, tracked recovery, and could represent biomarkers of impairment. 7 The first factor loaded on language, including deficits of language expression and comprehension, and memory, both verbal and spatial. The second and third factors loaded on the contralateral motor and visual attention deficits, i.e. left deficits for right lesions, and vice versa. Neither local damage nor vascular distributions could account for the observed correlation of deficits in different domains. Instead, a strong relationship was observed with functional network damage measured with fMRI. 8-11

*[picture on PDF page 2]*

**Figure labels:**
- Language
- Calculation
- Memory
- Motor Left
- Inattention
- Egocentric-Neglect
- Left
- Motor Right
- Sensory
- Egocentric-
- Neglect Right

The first aim of this study was to validate through a short and clinically applicable assessment the previously identified structure of impairment in a different population: Veneto, Italy. We used the Oxford Cognitive Screening (OCS), specially developed by the late psychologist Glyn Humphreys and colleagues to study poststroke cognitive impairment. 12,13 This test covers language, memory, attention, calculation and praxis; it takes 10-15min to be administered-against more than 2 h for the WU battery-and with the NIHSS may provide a clinically suitable neurobehavioural assessment applicable in busy stroke units. The data were analysed to find robust components of impairment that were correlated across patients. The results were then compared to those obtained by analysing the independent dataset from WU in the same manner. The second aim was to examine the neuroanatomy of these factors using a multivariate machine learning approach. We related spatial patterns of damage to behavioural scores to find a lesion model that best accounted for the individual variability of scores. To replicate the neuroanatomy, we ran the same approach on the WU cohort.

### Materials and methods

### Study sample

The recruitment covered 22 months, from December 2017 to October 2019, and occurred at the Stroke Unit and Clinica Neurologica of the Hospital of Padova and the Stroke Unit of the Ospedale S. Antonio Padova.

The inclusion criteria, same as in the WU cohort, included:

- Age 18 or higher;
- First symptomatic stroke, ischaemic or haemorrhagic in aetiology;
- Up to two lacunes, clinically silent, less than 15 mm in size on CT scan;
- Time of enrolment: < 2 weeks from stroke onset;
- Awake, alert, and capable of participating in research.

Exclusion criteria included: (i) Previous stroke based on clinical imaging; (ii) Multifocal strokes; (iii) Inability to maintain wakefulness in the course of testing; (iv) More than two asymptomatic lesions on CT scan; (v) Presence of central nervous system tumours; (vi) History of dementia; (vii) Previous central nervous system surgeries; (viii) Schizophrenia, bipolar disorder, major depression or other severe psychiatric conditions; (ix) Other medical conditions that preclude active participation in research and may alter the interpretation of the behavioural/ imaging studies; and (x) Inability to provide consent; for severe aphasic patients informed consent next-of-kin gave informed consent.

### Procedures

We screened a total of N ¼ 1080 charts. Subjects ( n ¼ 237) with a first symptomatic stroke, ischaemic or haemorrhagic, were prospectively recruited, with n ¼ 180 meeting post-enrolment inclusion criteria. Supplementary Figure 1 describes the enrolment flowchart and shows reasons for lack of inclusion. Subjects were evaluated with a neurobehavioural battery at the acute phase (5 6 3.3 days post-stroke). The behavioural battery included the OCS 12 and the NIHSS. 14 We collected structural imaging (130 MRI scans and 50 CT scans) that was routinely performed for each subject at 5 6 4days post-stroke. Supplementary Figure 2 illustrates the design of the study.

### Measures

Experienced neurologists examined all patients using the NIHSS, 14 which was administered on admission, on discharge and at the time of testing (within a week). The NIHSS includes 15 subtests: level of consciousness subtests, gaze and visual field deficits, facial palsy, upper and lower motor deficits (right and left side), limb ataxia, sensory impairment, inattention, dysarthria and language deficits. The NIHSS scores at the time of testing were analysed. Also, we recorded: demographics data, stroke risk factors, other neurological, psychological, or psychiatric conditions, familiarity for stroke, stroke subtype (haemorrhagic or ischaemic), clinical presentation.

The OCS was administered the first week following stroke onset. The OCS is a brief tool-10-15 min longdeveloped to describe acute cognitive impairment poststroke. 12 It is structured around five cognitive domains: language, praxis, number processing, attention and memory, and consists of 10 individual subtests. In the language domain, picture naming, picture pointing and sentence reading subtests measure speech production, auditory comprehension and reading, respectively. In the memory domain, verbal and spatial memory are examined separately through the orientation, recall and recognition, and episodic memory subtests. Number writing, and calculation tasks evaluate number processing. An imitating meaningless gestures test measures praxis. Finally, the broken heart test includes several subtests each measuring a different aspect of attention. The overall accuracy rate (across the two fields) is a measure of sustained attention, which is necessary for a high overall performance. The number of misses either on the left or right visual field is a measure of egocentric neglect. Finally, missing gaps on the left or right side of the individual hearts is a measure of allocentric neglect. Visual fields are checked separately.

### MRI and CT lesions

MRI and/or CT scans were routinely performed on admission and follow up depending on clinical status. Lesions were manually segmented on structural MRI and CT scans using the ITK-snap imaging software system 15 and individually checked by a neurology resident and a board certified neurologist. 16,17 CT and MRI segmented lesions were mapped on the MNI152 atlas using the Advanced Normalization Tools. 18 The FSL software was used to create the overlap of individual lesions on a standard brain atlas, producing an overlay map of all lesions. 19 Finally, to precisely describe stroke topography, lesions were mapped on the Harvard-Oxford cortical and subcortical structural masks. 20

### Behavioural analysis

The statistical analysis included the OCS subtests scores and the NIHSS individual scores. All subtests were normalized to their maximum values, and sign-inverted, such that the largest values corresponded to the most severe level of deficit. Only patients who participated to all task sets were included. After having z -scored the behavioural scores, we used a principal component analysis (PCA) to reduce the number of variables and describe the variability of behavioural deficits. Since many variables were expected to be correlated, an oblique rotation (PROMAX) was used (for completeness non-rotated PCAs and the corresponding anatomical maps were computed). As the oblique rotation is dependent on the number of selected components, we decided to be consistent with Corbetta et al., 6 and selected the first three Principal Components (PCs).

Moreover, a correlation matrix was computed to graphically visualize the strength of correlation between tests. Many subtests were at ceiling, with most subjects reaching maximum scores. Matlab R2018b was used for all statistical analysis.

|

### Lesion-behaviour analysis

The analysis was run on our sample and a subset of patients of the WU cohort ( n ¼ 67 had completed all tests of the battery). To relate behavioural deficits to lesions, we employed a ridge regression algorithm (RR). 21 RR is a multivariate method based on machine learning. Multivariate methods control for hidden biases, such as the vascular distribution of damage, that consistently distort lesion-deficit maps computed using voxel-wise univariate methods. 22,23 These biases can displace inferred critical regions from their true locations in a manner opaque to replication. RR models allow us to predict behavioural variance based on structural features including volume and location (for additional detail of the procedure see Supplementary methods).

### Vascular territory control analysis

To test whether different vascular territories of the MCA were strongly associated with different PC scores, we clustered patients based on their lesion location. We computed the percentage overlap of each lesion with a mask of three vascular territories (deep branches, anterior-superior branch and posterior-inferior branch). 24 We clustered these groups of lesions based on their location within the vascular territories and selected the optimal number of clusters through Silhouette and Davies Bouldin indexes. We used mixed measures ANOVA, with PC (PC1-PC3) as within-subjects factor and clusters as between-subjects factor, to test the interaction effect of PC scores and anatomical clusters. We performed the same analysis on the subset of patients of the Washington University dataset ( n ¼ 67).

### Data availability

All data reported in the present study are available from the authors and all the software and algorithms used in the present study are cited in the Material and methods.

### Results

### Participants

The study sample had a mean age of 69years old. All patients were Caucasian. Most patients were male (53%). The majority had completed middle or high school in the Italian educational system (mean level of education: 10years). The most commonly identified stroke risk factors were hypertension (64% of patients) followed by smoking, diabetes mellitus, atrial fibrillation and coronary artery disease (Supplementary Table 1, Demographics and Clinical Characteristics).

In terms of stroke-related variables, the study sample presented a mean NIH score of 7.1 6 5.6 on admission, while the NIH score at the time of testing was 3.2 6 2.9. The NIH score used for the analysis was the one collected at the time of neuropsychological testing. Motor impairment was the most common deficit (90% of patients), followed by aphasia (34%), and neglect (20%). The aetiology of most strokes (89%) was ischaemic while 11% were haemorrhagic. Slightly less than half of the ischaemic patients underwent acute stroke treatment (42%) (Supplementary Table 2. Acute reperfusion therapy details). Finally, 44% of patients presented left hemisphere damage, 40% right hemisphere damage, 7.5% infratentorial lesions and 9% had clinical deficits without lesions on neuroimaging scans (Supplementary Table 3).

### Anatomy

To generate a precise description of stroke topography, we implemented a voxel-wise analysis of lesions. Figure 1 shows an overlay map of all segmented lesions normalized to a standardized brain atlas. 25 The segmented lesions included: 79 subjects with left hemisphere lesions, 71 subjects with right hemisphere lesions and 14 subjects with cerebellum or brainstem lesions. Sixteen subjects presented negative MRI/CT scans for acute events. Stroke topography was predominantly subcortical and concentrated in the basal ganglia, central white matter and thalamus. Cortical lesions predominantly occurred in the MCA territory. Specifically, 10% of lesions exclusively affected the cerebral cortex, 22% damaged subcortical structures, while 65% were cortico-subcortical lesions (Supplementary Tables 3 and 4). The structural damage in our study was similar to the topography of recent studies on prospective clinical samples. 6,26,27

*[picture on PDF page 4]*

**Figure labels:**
- R
- 0.00
- 0.17

### Behavioural PCA

A PCA was run on the OCS and NIHSS subtest scores to reduce the number of variables and identify hidden factors that capture behavioural variability. Most scores showed a long tail distribution with most patients having

|

a peak near zero with a long positive tail consistent with varying degree of deficit. While the identification of many components would be consistent with the existence of many distinct behavioural syndromes, the discovery of a small number of components is consistent with correlated deficits across functional domains. The PCA was run on 158 subjects with a complete dataset including all NIHSS and OCS scores (88% of the enrolled patients; 22 patients were not able to complete the assessment due to fatigue or underlying comorbities).

Three PCs accounted for nearly 50% of the behavioural variance (Fig. 2). PC1 accounted for 23.5% of the variance, PC2 for 14% of the variance and PC3 for 7.5% of the variance. This structure is represented in Fig. 2A where the size of each circle is proportional to the

*[picture on PDF page 5]*

**Figure labels:**
- A
- PC1
- Language
- 24%
- Calculation
- Memory
- Praxis
- PC2
- PC3
- Motor Left
- 13%
- Inattention
- Motor Right
- 8%
- Egocentric
- Sensory
- Neglect Left
- B
- Neglect Right
- Overall Performance
- Loadings PC 1 (NIH-OCS)
- Loadings PC 2 (NIH-OCS)
- Loadings PC 3 (NIH-OCS)
- LOC-questions
- LOC-commands
- best gaze
- Visual
- Facial Palsy
- Motor Arm R
- Motor Leg R
- Motor Arm L
- Motor Leg L
- Limb Ataxia
- sensory
- Best Language
- Dysarthria
- OCS-Denomination
- OCS-Semantics
- OCS-Orientation
- OCSttton
- OCS-Visual Field L
- OCS-Visual Field R
- OCS-Sentence reading
- OCS-Number writing
- OCS-Calculation
- OCStgon
- oOcS-a aes aray
- OCS-Hearts overall accuracy
- OCS-egocentric-neglect-R
- OCS-allocentric-neglect-R
- OCS-allocentric-neglect-L
- OCS-Imitating gesture-domina
- oCS--en gnant
- OCS-Verbal memory
- OCS-Episodic memory
- OCS-Executive function-misto
- 0.1
- 0.2
- 0.3
- -0.2
- 0
- 0.4
- 0.6

|

*[picture on PDF page 6]*

**Figure labels:**
- PC1
- PC2
- PC3
- OCS-Episodic memory
- 1
- OCS-Number writing
- OCS-Hearts overall accuracy
- 0.8
- OCS-Orientation
- OCS-Denomination
- OCS-Calculation
- OCS-Sentence reading
- 0.6
- OCS-Semantics
- OCS-Imitating gesture-dominant
- OCŠ-Verbal memory
- 0.4
- Best Language
- OCS-Visual Field R
- OCS-allocentric-neglect-R
- 0.2
- LOC-questions
- LOC-commands
- OCS-egocentric-neglect-R
- 0
- OCS-Executive function-misto
- Motor Arm L
- Motor Leg L
- -0.2
- Inattention
- best gaze
- OCS-Visual Field L
- -0.4
- OCS-egocentric-neglect-L
- sensory
- Visual
- -0.6
- OCS-allocentric-neglect-L
- Limb Ataxia
- Motor Arm R
- -0.8
- Motor Leg R
- Dysarthria
- Facial Palsy

percentage of variance explained by each factor across subjects. Figure 2B shows the loadings for each score (see Supplementary Fig. 3 for non-rotated PCA loadings results). Positive loadings indicate lower performance, while negative loadings indicate higher performance. PC1 loaded on language, memory, calculation, apraxia and allocentric neglect. PC2 loaded on left side motor, visual, left egocentric neglect and overall performance deficits. PC3 loaded on right side motor deficits.

The correlation among behavioural scores was also examined through a correlation matrix (Fig. 3). A 'block' structure along the diagonal indicates correlation among different tests. Consistently with PC1, there was a robust correlation between language, calculation, praxis, verbal and spatial memory tasks, and right allocentric neglect. Left motor deficits correlated with left visual field and left egocentric and allocentric neglect (PC2), while right motor deficits formed a separate cluster (PC3). Interestingly, some tests show positive correlation across two components. For instance, the OCS Heart overall accuracy, a test of general performance, and the OCS orientation were common to PC1 and PC2; dysarthria and face palsy, which were not computed separately for left versus right body/field, loaded on both left and right hemisphere-specific components.

In summary, this analysis identified three main sets of correlated behavioural deficits: one cognitive related to language, calculation, praxis, and memory deficits, and two contra-lesional motor-attention components. General performance influenced both the cognitive and left motorattention component.

### RR behaviour to anatomy

To study the relationship between structural damage and behavioural impairment, we applied a RR model. The analysis was conducted on subjects ( n ¼ 148) that included both behavioural and neuroimaging data. Figure 4A shows the scatter plots of the empirically measured behavioural scores versus the estimated behavioural scores from the RR model based on the lesion anatomy. Essentially, the model predicts the best fitting behavioural scores from the distribution of lesioned voxels across patients. Each dot represents a subject, and the size of each dot is scaled by the lesion volume. The model explained different levels of variance for each factor score: PC1: 38%; PC2: 44%; and, PC3: 9%, respectively.

Figure 5 shows the maps of the most predictive anatomical structures (weights of the RR) associated with each PC scores. The anatomical description goes from the dorsal to the ventral slices, and from the anterior to the posterior direction. The orange/yellow colour scale indicates damaged voxels associated with low performance, whereas the blue/teal colour scale indicates damaged voxels associated with high performance. Here,

|

*[picture on PDF page 7]*

**Figure labels:**
- PC1-R
- 2
- =0.38
- PC2-R
- = 0.44
- PC3- R
- = 0.09
- A
- 5
- LEFT
- RIGHT
- other
- PC1 scores - predicted
- 4
- PC2 scores - predicted
- PC3 scores - predicted
- 3
- 0
- -1
- 1
- PC1 scores
- PC2 scores
- PC3 scores
- B
- = 0.13
- = 0.56
- PC3-R
- =0.35
- 3.5
- scores - predicted
- 2.5
- 1.5
- PC1
- PC2
- 0.5
- -0.5

we focus on anatomical regions associated with low performance. Low performance on language, memory, calculation and praxis (PC1) correlated with damage of the left superior and middle frontal gyrus, left inferior parietal and underlying white matter, left occipital dorsal, left inferior frontal gyrus/insula and underlying white matter, left putamen and caudate, left thalamus, and left anterior middle and inferior temporal gyrus. Left motor and attention deficits (PC2) correlated with damage of the right superior, middle, and precentral gyrus, right superior and inferior parietal regions, right corona radiata and internal capsule, right caudate, putamen, and thalamus, and right superior and middle temporal gyrus, right orbitofrontal gyrus. Finally, low scores on right motor and attention deficits (PC3) localized to damage of the left caudate, putamen, and internal capsule, left thalamus, and left lateral occipital cortex.

### Validation: WU cohort

To test the external validity of our predictions, we applied the same analysis to the behavioural scores of the WU cohort. 6 The St. Louis WU cohort includes n ¼ 132 first-time stroke patients prospectively enrolled with the same criteria as this study; the behavioural battery takes 2.5 h, and includes 44 scores in 7 domains (motor, visual, language, spatial attention, general performance, verbal and spatial memory). A PCA on the behavioural scores also yielded three components (PC1-3) that explained 49% of the variance, which loaded on similar functional domains. PC1 (22.5%) loaded on language and verbal/spatial memory; PC2 (15%) on left motor, left visuospatial neglect, general performance and spatial memory; PC3 (11.4%) on right motor and right spatial neglect 6 (Supplementary Fig. 4). A RR model explained different levels of variance for each factor (PC1: 13%, PC2: 56% and PC3: 35%, respectively) (Fig. 4B).

The weights of the RR identified regions of the brain whose damage mostly contributed to the different PC scores. Low performance on language, memory, calculation and praxis (PC1) correlated with damage of several left hemisphere regions: left precentral white matter, left inferior parietal and underlying white matter, left insula and inferior frontal gyrus, left caudate, putamen, and thalamus, left anterior and middle temporal gyrus. This map contained also right hemisphere regions including

|

*[picture on PDF page 8]*

**Figure labels:**
- University of Padua Stroke Sample
- PC1
- PC2
- PC3
- R
- Z=22
- Z=37
- Z=52
- Z=67
- Z=82
- Z=97
- Z=112

right precentral white matter, right caudate, putamen, and thalamus, right insula, right anterior temporal gyrus. Left motor and attention deficits (PC2) localized to the right precentral cortex and underlying corona radiata, right caudate, putamen and internal capsule. A significant region was also in the left middle temporal gyrus. Finally, low scores on right motor and attention deficits (PC3) scores correlated with damage to the left precentral gyrus and underlying corona radiata, left internal capsule, putamen, and thalamus, left anterior inferior frontal gyrus (Fig. 6).

For each PC, we evaluated the spatial correlation between the maps obtained with our data and the maps obtained with the WU dataset, after having resampled both maps in the same space of the WU data. For PC1 we obtained a correlation r ¼ 0.66 ( P < 10   5 ); for PC2 r ¼ 0.35 ( P < 10   5 ); for PC3 r ¼ 0.11 ( P < 10   5 ). In general, the topography of damage related to the main axes of behavioural impairment was consistent between both samples of stroke patients.

### Control for vascular distribution

We tested whether lesions in different vascular territories [e.g. (deep vs. superficial branches of MCA] cause different profiles of deficits based on the PC behavioural scores. We clustered patients based on their lesion location. Cluster 1

included patients with lesions in deep, antero-superior and postero-inferior MCA branches. Cluster 2 included patients with lesions in the deep branches of MCA. Cluster 3 included patients with lesions in the postero-inferior branch of MCA and cluster 4 lesions in the antero-superior branch of MCA (Supplementary Fig. 5A). The mixed measures ANOVA, with PCs as within-subjects factor and clusters as between-subjects factor found a significant global interaction effect ( F ¼ 2.48, P ¼ 0.024), but no significant main effects. The interaction effect was driven by different patterns of PC scores between cluster 2 and 3 ( F ¼ 5.008, P ¼ 0.04, Bonferroni corrected for 6 multiple comparisons). This interaction shows that PC1 scores are stronger in cluster 3 given the cortical/perisylvian distribution, while PC3 scores are higher in cluster 2 given the subcortical location (Supplementary Fig. 5B). The same analysis on the subset of patients of the Washington University dataset ( n ¼ 67) found no interaction effect between PC scores and vascular clusters (Supplementary Fig. 5C).

### Discussion

This study investigated whether previously described 6 groups of correlated deficits describing post-stroke

|

*[picture on PDF page 9]*

**Figure labels:**
- Washington University Stroke Sample
- PC1
- PC2
- PC3
- R
- Z=23
- Z=38
- Z=53
- Z=68
- Z=83
- Z=98
- Z=113

behavioural variability could be validated using a different population and a different neuropsychological battery. Furthermore, we studied whether a simplified neurological and psychological assessment could be used as a sensitive measure of these axes of impairment. Finally, the topography of stroke lesions was analysed to map the relationship between structural damage and behavioural biomarkers.

The behaviour factor analysis showed a strong correlation between deficits across domains. Three factors explained  50% of the variance with Factor 1 loading on functions that are traditionally associated with the left hemisphere: language, verbal memory, calculation and praxis. However, on Factor 1, we also found visual episodic memory and general performance, functions that are typically associated with the right hemisphere.

In the language domain, subtests evaluated the level of speech production, auditory comprehension, reading capacities and general performance. All language tasks loaded under PC1 showing correlation that accounted for ffi24% of the whole variability of scores across subjects with no clear separation in the traditional aphasia syndromes, e.g. (Broca, Wernicke). This correlation among language deficits/syndromes is comparable to the St. Louis WU cohort: their PC1 accounted for 22.5% of variance. 6 Interestingly, the Padova PC1 also includes tasks for number processing abilities (Number Writing and Calculation). Number processing is traditionally associated with lesions of the parietal lobe, especially the left parietal (even though an association with right parietal cortex was recently described by Semenza et al). 28 PC1 also loaded on praxis, a left fronto-parietal function. 29 Finally, PC1 also loaded on verbal and visual memory, similarly to what we find in the St. Louis battery. Interestingly, the Padova PC1 also includes correlation with right visual neglect and general performance. Overall, then, both Padova and St. Louis PC1 capture correlated deficits in many traditional left hemisphere functions (language, calculation, praxis, verbal memory), but also right hemisphere functions (general performance and visual memory).

PC2 and PC3 capture in both batteries, respectively, left and right motor deficits. The ranking in variance explained is also similar, first left (PC2) then right (PC3) motor deficits. Interestingly, in the motor domain, we do not see the traditional vascular syndromes (e.g. middle vs. anterior cerebral vs. subcortical), but correlated deficits of both upper and lower extremity motor function. This is consistent with prior PCA studies on the NIHSS 4,5 and Corbetta et al. 6 While traditional

|

neuropsychological and neurophysiological investigations differentiate between sensory versus memory driven movements, and reaching versus grasping, 30-32 more recent studies emphasize the correlation among different kinds of ecological movements, and the low dimensionality of movements in terms of kinematic analysis, EMG activation, and even responses in motor cortex. A reaching movement for instance will require coordinated movements of shoulder, arm, elbow, wrist and fingers that occur together in patterns of neural activation (synergies). 33-36

The OCS does a good job in separating deficits of attention. General performance captured by the overall detection score on the Heart task loads on both PC1 and PC2. PC2 also captures left visual neglect, both egocentric, i.e. cantered on the body midline, and allocentric, i.e. cantered on the midline of objects, consistently with the syndrome of hemi-spatial neglect. 37 Interestingly, right allocentric neglect loads on PC1 consistent with the observation that this form of neglect is better conceptualized as a left hemisphere object agnosia. 37,38 Both Padova PC2 and PC3 are highly similar in structure to St. Louis, despite differences in the neuropsychological tests used.

Overall, then our study essentially replicates Corbetta et al. demonstrating that at the population level this lowdimensional structure of behavioural impairment is specific to stroke irrespective of population, time of testing (5 days Padova, 2weeks, 3-12months St. Louis) and other non-specific factors (i.e. variability in performance, low motivation, anxiety or depression) potentially present at the acute phase.

While the St. Louis battery takes between 1 and 1 = 2 and 2h being structured in 44 different scores covering multiple domains: motor, language, memory, attention, 6 the neurobehavioural battery in this study was shorter to administer. The OCS, a validated tool for cognitive assessment in stroke, 12 can be readily administered in approximately 10min. It has shown high levels of inclusivity, reliability, convergent and divergent validity between subtests and other cognitive tests, such as MOCA, BDAE, Wechsler. 12 It has been validated in several countries 12,39-44 stratified for age, gender and education level. Recent studies have demonstrated high levels of sensitivity in detecting stroke-specific cognitive impairments even in mild stroke. 45 The NIH stroke scale was designed to be standardized, repeatable, and usable in large multi-centre clinical trials. 46 Clinical researchers have widely accepted this scale due to high levels of inter-examiner and test-retest score consistency. 47 In addition, it has been repeatedly validated as an excellent predictor for patient outcome. 14 While previous studies on the factor structure of the sole NIH stroke scale 4,5 have identified two factors, one for each hemisphere, this study combining the NIHSS and OCS replicates the 3factor structure identified in Corbetta et al. 6 This implies that to capture cognitive impairment the NIHSS should be integrated with a more sensitive cognitive screen.

Importantly, we found that the combination of NIHSS and OCS had an excellent level of compliance. We were able to administer all subtests at 5days to 88% of enrolled patients, against 51% of enrolled patients at 2weeks on the St. Louis battery. It remains to be seen if the NIHSS/OCS battery will be sensitive to recovery similarly to the St. Louis battery. 7

It should be underscored, however, that in both datasets a significant amount of behavioural variance (  50%) was not described by our data reduction approach and the effect size of PC3 was in general quite small. Where does the rest of the behavioural variance in stroke go? One possibility would be to add more patients hoping that as more lesions sample-specific locations in the brain, more specific patterns of behaviour will emerge. This is possible, even though we currently feel this is unlikely. In Padova, we carried out a preliminary analysis with n ¼ 100 individuals (as compared to n ¼ 180 in the final analysis), and we obtained the same three factors explaining about the same amount of variance. In St. Louis, we more than doubled the subjects by running PCA on domain-specific components obtained on the maximum number of patients, and the variance accounted increased only by 15%.

So how can we improve our post-stroke behavioural description? It is possible that the percentage will increase as some other important cognitive domains are included (i.e. emotion, decision making, social cognition, theory of mind). In particular, the identified axes of behavioural impairment are similar to the main behavioural axes described in healthy subjects when considering the brain's functional lateralization through fMRI meta-analytic data. Karolis et al. showed that four axes (i.e. symbolic communication, perception/action, emotion and decision-making) could summarize the entire architecture of the brain's lateralization of function. 48 Karolis results could provide a physiological counterpart to the identified poststroke behavioural biomarkers, but it suggests that at least two additional cognitive domains (emotion and decision-making) shall be added to our short battery to provide a comprehensive behavioural profile of stroke patients.

When considering structural damage, our study demonstrated stroke topography was predominantly subcortical, with a paucity of cortical lesions. Lesions were extremely heterogeneous in volume, including both lacunar and hemispheric strokes. All vascular territories were involved, with the MCA predominantly affected in accordance with well-established stroke literature. 20,49 Cortical areas were exclusively affected in only 10% of patients, in agreement with data from other prospective clinical sample studies on acute stroke patients. 6,26,27 A significant portion of the sample (42%) underwent acute reperfusion therapy. Demographic factors and differences in clinical characteristics did not likely bias topography, especially as strong factors associated with subcortical damage (such as hypertension, diabetes type II and hemorrhagic strokes)

were actually slightly less represented in our sample in comparison with other consecutive sample studies. 50 Once again, these results emphasize how stroke (both in topography and symptoms) should be better conceptualized as a subcortical disease with secondary impact on white matter pathways and cortico-cortical and corticosubcortical functional interactions. 51

Finally, we investigated the relationship between behavioural biomarkers and stroke topography through a multivariate machine learning method. While previous studies have performed factor analysis to identify neural structures of pre-conceived and distinct functional domains (i.e. language, motor, memory, attention), 6,52 the PC scores of our subjects derive from statistical correlation alone and bypass the need of, often overlapping, behavioural classifications of deficits to map biomarkers. Most importantly, this completely data-driven approach provides topographical correlates regarding post-stroke multi-domain impairment. High PC1 (language, memory, calculation, praxis) scores mainly correlated with damage of left cortico-subcortical regions; high PC2 scores (left motor and visual attention) with damage of right corticosubcortical regions; high PC3 scores (right motor) with damage of left subcortical regions. The resulting maps are consistent with those obtained by running the same analysis on the St. Louis data set. 6 These results show that behavioural impairment following a stroke can be reliably related to lesion location and raise several interesting considerations.

Firstly, our anatomical correlates do not correspond to precise vascular territories. In fact, we tested if different vascular territories of the MCA were associated with different PC scores and found no clear association in either dataset (Supplementary Fig. 5).

Secondly, our structural models were able to explain only low-medium levels of variance for our components (PC1 ¼ 38%, PC2 ¼ 44% and PC3 ¼ 9%, respectively). These results agree with recent studies that show both lesion location and functional network impairment account for behavioural variance. 53 Moreover, while sensorimotor deficits are more precisely predicted by structural variables, cognitive deficits depend more on multi-network functional connectivity alterations. 8,54 As our components derive from statistical correlation alone, we believe models that include pathophysiological information (such as white matter disconnection and f-MRI analysis), could provide better results in predicting our behavioural biomarkers. 53,55,56

In conclusion, this study demonstrated a low-dimensional structure of neurological deficits following stroke using a combination of clinically applicable batteries. Neurological deficits post-focal lesions are more accurately described by correlated deficit components rather than the collection of individual syndromes as in traditional neurological teaching. We identified a few factors that showed consistency across different populations and

|

different neurobehavioural batteries. The associated lesion topography of the identified components was also robust.

The identified biomarkers are therefore sensitive measures of behavioural impairment when investigating the epidemiology, genetics, or pathophysiology of stroke. They should also be employed to assess the efficacy at the population level of novel acute or chronic interventions.

### Supplementary material

Supplementary material is available at Brain Communications online.

### Acknowledgements

The principal investigators wish to thank the participants who participated in the study for their time and effort.

### Funding

M.C. was supported by Progetto Strategico (2016-2020) University of Padova; National Institutes of Health NS095741 (2015-2020); BIAL Foundation Grant (20192021); Department of Excellence Italy Ministry of Research (MIUR) (2018-2022); CARIPARO Foundation (20202023); Neuro-Connectome, Ministry of Health, Italy (202031/12/2023). A.L.B. was supported by the Residency Neurology Program of the University of Padova.

### Competing interests

The authors report no conflicts of interest. All co-authors have seen and agree with the contents of the manuscript and there is no financial interest to report. We certify that the submission is original work and is not under review at any other publication.

### References

- Fisher C. Clinical syndromes in cerebral artery occlusion. In: Fields WS, (eds.) Pathogenesis and treatment of cerebrovascular disease. Charles C. Thomas; Springfield, III., 1961:pp 151-177.
- Broca P. Remarks on the seat of the faculty of articulated language, following an observation of aphemia (loss of speech). Bull Soc Anat. 1861;6:330-357. http://psychclassics.yorku.ca/Broca/ aphemie-e.htm (25 June 2018, date last accessed).
- Jackson. Suggestions on studying diseases of the central nervous system on Professor Owen's Vertebral Theory. Published online by Cambridge University Press: 26 July 2012
- Zandieh A, Kahaki ZZ, Sadeghian H, et al. The underlying factor structure of National Institutes of Health Stroke scale: An exploratory factor analysis. Int J Neurosci. 2012;122(3):140-144.
- Lyden P, Claesson L, Havstad S, Ashwood T, Lu M. Factor analysis of the National Institutes of Health Stroke scale in patients with large strokes. Arch Neurol. 2004;61(11):1677-

|

- Corbetta M, Ramsey L, Callejas A, et al. Common behavioral clusters and subcortical anatomy in stroke. Neuron. 2015;85(5): 927-941.
- Ramsey LE, Siegel JS, Lang CE, Strube M, Shulman GL, Corbetta M. Behavioural clusters and predictors of performance during recovery from stroke. Nat Hum Behav. 2017;1(3):0038.
- Siegel JS, Ramsey LE, Snyder AZ, et al. Disruptions of network connectivity predict impairment in multiple behavioral domains after stroke. Proc Natl Acad Sci U S A. 2016;113(30): E4367-E4376.
- Baldassarre A, Ramsey LE, Siegel JS, Shulman GL, Corbetta M. Brain connectivity and neurological disorders after stroke. Curr Opin Neurol. 2016;29(6):706-713.
- He BJ, Snyder AZ, Vincent JL, Epstein A, Shulman GL, Corbetta M. Breakdown of functional connectivity in frontoparietal networks underlies behavioral deficits in spatial neglect. Neuron. 2007;53(6):905-918.
- Carter AR, Astafiev SV, Lang CE, et al. Resting interhemispheric functional magnetic resonance imaging connectivity predicts performance after stroke. Ann Neurol. 2010;67(3):365-375.
- Demeyere N, Riddoch MJ, Slavkova ED, Bickerton W-L, Humphreys GW. The Oxford Cognitive Screen (OCS): Validation of a stroke-specific short cognitive screening tool. Psychol Assess. 2015;27(3):883-894.
- Demeyere N, Riddoch MJ, Slavkova ED, et al. Domain-specific versus generalized cognitive screening in acute stroke. J Neurol. 2016;263(2):306-315.
- Muir KW, Weir CJ, Murray GD, Povey C, Lees KR. Comparison of neurological scales and scoring systems for acute stroke prognosis. Stroke. 1996;27(10):1817-1820.
- Yushkevich PA, Piven J, Hazlett HC, et al. User-guided 3D active contour segmentation of anatomical structures: Significantly improved efficiency and reliability. Neuroimage. 2006;31(3): 1116-1128.
- Longstreth WT, Manolio TA, Arnold A, et al. Clinical correlates of white matter findings on cranial magnetic resonance imaging of 3301 elderly people. The Cardiovascular Health Study. Stroke. 1996;27(8):1274-1282.
- Wahlund LO, Barkhof F, Fazekas F, et al. A new rating scale for age-related white matter changes applicable to MRI and CT. Stroke. 2001;32(6):1318-1322.
- Avants BB, Tustison NJ, Song G, Cook PA, Klein A, Gee JC. A reproducible evaluation of ANTs similarity metric performance in brain image registration. Neuroimage. 2011;54(3):2033-2044.
- Jenkinson M, Beckmann CF, Behrens TEJ, Woolrich MW, Smith SM. FSL. Neuroimage. 2012;62(2):782-790.
- Desikan RS, Se ´ gonne F, Fischl B, Quinn BT, Dickerson BC, Blacker D, Buckner RL, Dale AM, Maguire RP, Hyman BT, Albert MS, Killiany RJ. An automated labeling system for subdividing the human cerebral cortex on MRI scans into gyral based regions of interest. Neuroimage. 2006 Jul 1;31(3):968-80.
- Problems N, Hoerl AE, Kennard RW. American Society for Quality Ridge Regression: Biased Estimation For; 1970. Vol 12, No.1 Published by American Statistical Association an American Society for quality;pp 55-77;https://www.math.arizona.edu/  hzhang/math574m/Read/ RidgeRegressionBiasedEstimationForNonorthogonalProblems.pdf
- (31 July 2020, date last accessed).
- Mah Y-H, Husain M, Rees G, Nachev P. Human brain lesion-deficit inference remapped. Brain. 2014;137(Pt 9):2522-2531.
- Phan TG, Chen J, Donnan G, Srikanth V, Wood A, Reutens DC. RD. Development of a new tool to correlate stroke outcome with infarct topography: A proof-of-concept study. Neuroimage. 2010; 49(1):127-133.
- Blumenfeld H. Chapter 10. In: Neuroanatomy through clinical cases, second Edition ; Sinauer Associates, Inc. Publishers. Sunderland Massachusetts; 2010.
- Rorden C, Bonilha L, Fridriksson J, Bender B, Karnath H-O. Agespecific CT and MRI templates for spatial normalization. Neuroimage. 2012;61(4):957-965.
- Kang D-W, Chalela JA, Ezzeddine MA, Warach S. Association of ischemic lesion patterns on early diffusion-weighted imaging with TOAST stroke subtypes. Arch Neurol. 2003;60(12):1730-doi: 10.1001/archneur.60.12.1730
- Wessels T, Wessels C, Ellsiepen A. Contribution of diffusionweighted imaging in determination of stroke etiology. AJNR Am J Neuroradiol. 2006;27(1):35-39.
- Montefinese M, Turco C, Piccione F, Semenza C. Causal role of the posterior parietal cortex for two-digit mental subtraction and addition: A repetitive TMS study. Neuroimage. 2017;155:72-81.
- Heilman KM, Watson RT. G-RL. Praxis. Chapter 14, Cambridge University Press. 2007; pp 199-213
- Kalaska JF, Scott SH, Cisek P, Sergio LE. Cortical control of reaching movements. Curr Opin Neurobiol. 1997;7(6):849-859.
- Rizzolatti G, Fogassi L, Gallese V. Parietal cortex: From sight to action. Curr Opin Neurobiol. 1997;7(4):562-567.
- Wise SP, Boussaoud D, Johnson PB, Caminiti R. Premotor and parietal cortex: Corticocortical connectivity and combinatorial computations. Annu Rev Neurosci. 1997;20(1):25-42.
- Cheung VCK, Turolla A, Agostini M, et al. Muscle synergy patterns as physiological markers of motor cortical damage. Proc Natl Acad Sci. 2012;109(36):14652-14656.
- Cheung VCK, Piron L, Agostini M, Silvoni S, Turolla A, Bizzi E. Stability of muscle synergies for voluntary actions after cortical stroke in humans. Proc Natl Acad Sci. 2009;106(46): 19563-19568.
- Howard IS, Ingram JN, Ko ¨rding KP, Wolpert DM. Statistics of natural movements are reflected in motor errors. J Neurophysiol. 2009;102(3):1902-1910.
- Ingram JN, Ko ¨rding KP, Howard IS, Wolpert DM. The statistics of natural hand movements. Exp Brain Res. 2008;188(2): 223-236.
- Corbetta M, Shulman GL. Spatial neglect and attention networks. Annu Rev Neurosci. 2011;34(1):569-599.
- Hillis A, Newhart M, Heidler J, Marsh EB, Barker P, Degaonkar M. The neglected role of the right hemisphere in spatial representation of words for reading. Aphasiology. 2005;19(3-5):225-238.
- Humphreys GW, Duta MD, Montana L, et al. Cognitive function in low-income and low-literacy settings: Validation of the tabletbased Oxford cognitive screen in the health and aging in Africa: A longitudinal study of an INDEPTH community in South Africa (HAALSI). J Gerontol Ser B Psychol Sci Soc Sci. 2017;72(1): 38-50.
- Robotham RJ, Riis JO, Demeyere N. A Danish version of the Oxford cognitive screen: A stroke-specific screening test as an alternative to the MoCA. Aging Neuropsychol Cogn. 2020;27(1): 52-65.
- Ramos CCF, Amado DK, Borges CR, Bergamaschi E, Nitrini R, Brucki SMD. Oxford cognitive screen - Brazilian portuguese version (OCS-Br): A pilot study. Dement Neuropsychol. 2018;12(4): 427-431.
- Huygelier H, Schraepen B, Demeyere N, Gillebert CR. The Dutch version of the Oxford Cognitive Screen (OCS-NL): Normative data and their association with age and socio-economic status. Aging Neuropsychol Cogn. 2019;27(5):765-786.
- Demeyere N, Sun S, Milosevich E, Vancleef K. Post-stroke cognition with the Oxford Cognitive Screen vs Montreal Cognitive Assessment: A multi-site randomized controlled study (OCSCARE). AMRC Open Res. 2019;1:12.
- Mancuso M, Varalta V, Sardella L, et al. Italian normative data for a stroke specific cognitive screening tool: The Oxford Cognitive Screen (OCS). Neurol Sci. 2016;37(10):1713-1721.
- Mancuso M, Demeyere N, Abbruzzese L, et al. Using the Oxford cognitive screen to detect cognitive impairment in stroke patients:

- A comparison with the mini-mental state examination. Front Neurol. 2018;9:101.
- Brott T, Adams HP, Olinger CP, et al. Measurements of acute cerebral infarction: A clinical examination scale. Stroke. 1989;20(7):864-870.
- Goldstein LB, Bertels C, Davis JN. Interrater reliability of the NIH stroke scale. Arch Neurol. 1989;46(6):660-662.
- Karolis VR, Corbetta M, Thiebaut de Schotten M. The architecture of functional lateralisation and its relationship to callosal connectivity in the human brain. Nat Commun. 2019;10(1):1417.
- Navarro-Orozco D, Sa ´ nchez-Manso JC. Neuroanatomy, Middle Cerebral Artery. StatPearls Publishing LLC; 2019. https://www. ncbi.nlm.nih.gov/books/NBK526002/ (13 September 2019, date last accessed).
- Bogousslavsky J, Van Melle G, Regli F. The Lausanne Stroke Registry: Analysis of 1,000 consecutive patients with first stroke. Stroke. 1988;19(9):1083-1092.
- Corbetta M, Siegel JS, Shulman GL. On the low dimensionality of behavioral deficits and alterations of brain network

|

- connectivity after focal injury HHS Public Access. Cortex. 2018; 107:229-237.
- Butler RA, Lambon Ralph MA, Woollams AM. Capturing multidimensionality in stroke aphasia: Mapping principal behavioural components to neural structures. Brain. 2014;137(12):3248-3266.
- Salvalaggio A, De Filippo De Grazia M, Zorzi M, Thiebaut de Schotten M, Corbetta M. Post-stroke deficit prediction from lesion and indirect structural and functional disconnection. Brain. 2020; 143(7):2173-2188.
- Siegel JS, Seitzman BA, Ramsey LE, et al. Re-emergence of modular brain networks in stroke recovery. Cortex. 2018;101: 44-59.
- Foulon C, Cerliani L, Kinkingne ´hun S, et al. Advanced lesion symptom mapping analyses and implementation as BCBtoolkit. Gigascience. 2018;7(3):1-17.
- Boes AD, Prasad S, Liu H, et al. Network localization of neurological symptoms from focal brain lesions. Brain. 2015;138(10): 3061-3075.