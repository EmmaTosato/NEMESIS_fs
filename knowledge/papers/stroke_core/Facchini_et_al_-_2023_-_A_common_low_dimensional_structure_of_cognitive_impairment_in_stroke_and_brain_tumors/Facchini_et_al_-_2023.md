*[picture on PDF page 1]*

Contents lists available at ScienceDirect

### NeuroImage: Clinical

journal homepage: www.elsevier.com/locate/ynicl

### A common low dimensional structure of cognitive impairment in stroke and brain tumors

Silvia Facchini a , Chiara Favaretto b , Marco Castellaro c , Andrea Zangrossi b , Margherita Zannin a , Antonio Luigi Bisogno a , Valentina Baro d , Maria Giulia Anglani e , Antonio Vallesi a,b , Claudio Baracchini f , **Domenico D** ' Avella d , Alessandro Della Puppa g , Carlo Semenza a,b , Maurizio Corbetta a,b,h,*

- a *Clinica Neurologica, Azienda Ospedale Universit* ` *a Padova, and Department of Neuroscience, University of Padua, Italy*
- b *Padova Neuroscience Center (PNC), University of Padua, Italy*
- c *Department of Information Engineering, University of Padua, Italy*
- d *Paediatric and Functional Neurosurgery Unit, Azienda Ospedale Universit* ` *a Padova, and Department of Neuroscience, University of Padua, Italy*
- e *Neuroradiology Unit, Azienda Ospedale Universit* ` *a Padova, Padua, Italy*
- f *Stroke Unit and Neurosonology Laboratory, Azienda Ospedale Universit* ` *a Padova, Padua, Italy*
- g Neurosurgery Unit, Department of Neuroscience, Psychology, Pharmacology and Child Health, Careggi University Hospital and University of Florence, Italy
- h *Venetian Institute of Molecular Medicine, VIMM, Padua, Italy*

### A R T I C L E  I N F O

Keywords: Stroke Neuro-oncology Neuropsychology Cognition

Neural networks

## 1. Introduction

Research  in  neuropsychology  has  traditionally  focused  on  the behavioral  effects  of  focal  brain  injuries,  especially  stroke  and  brain tumors. Typically, the lesions caused by these different pathologies are

### A B S T R A C T

Introduction: Neuropsychological studies infer  brain-behavior  relationships  from  focal  lesions  like  stroke  and tumors. However, these pathologies impair brain function through different mechanisms even when they occur at the same brain ' s location. The aim of this study was to compare the profile of cognitive impairment in patients with brain tumors vs. stroke and examine the correlation with lesion location in each pathology.

Methods: Patients with first time stroke (n = 77) or newly diagnosed brain tumors (n = 76) were assessed with a neuropsychological battery. Their lesions were mapped with MRI scans. Test scores were analyzed using principal  component  analysis  (PCA)  to  measure  their  correlation,  and  logistic  regression  to  examine  differences between pathologies. Next, with ridge regression we examined whether lesion features (location, volume) were associated with behavioral performance.

Results: The  PCA  showed  a  similar  cognitive  impairment  profile  in  tumors  and  strokes  with  three  principal components (PCs) accounting for about half of the individual variance. PC1 loaded on language, verbal memory, and executive/working memory; PC2 loaded on general performance, visuo-spatial attention and memory, and executive functions; and, PC3 loaded on calculation, reading and visuo-spatial attention. The average lesion distribution  was  different,  and  lesion  location  was  correlated  with  cognitive  deficits  only  in  stroke.  *Logistic regression* found language and calculation more affected in stroke, and verbal memory and verbal fluency more affected in tumors.

Conclusions: A similar low dimensional set of behavioral impairments was found both in stroke and brain tumors, even  though  each  pathology  caused  some  specific  deficits  in  different  domains.  The  lesion  distribution  was different for stroke and tumors and correlated with behavioral impairment only in stroke.

combined in group analyses to examine the anatomical basis of behavioral deficits. However, it is unknown if tumors and strokes affect the same cognitive functions, even when the lesion is at the same location. The pathophysiology of tumors and strokes is different. Strokes cause an acute (minutes, hours) disruption of local neuronal activity through a

> Abbreviations: OCS, Oxford Cognitive Screen; PCA, principal components analysis; RR, Ridge Regression.

> * Corresponding author at: Department of Neuroscience, Clinica Neurologica, University of Padova, Via Giustiniani 5, Padova 35128, Italy. *E-mail address:* maurizio.corbetta@unipd.it (M. Corbetta).

### https://doi.org/10.1016/j.nicl.2023.103518

*[picture on PDF page 1]*

*S. Facchini et al.*

loss of blood flow. Tumors in contrast grow slowly (weeks, months) and displace neural structures affecting function through different mechanisms  (e.g.,  oedema,  mechanical  pressure,  neuroinflammation).  The relative slow growth may induce in theory an adaptation, and through the recruitment of neural plasticity mechanisms a different pattern of deficits (Klein et al., 2012).

There  have  been  only  a  handful  of  studies  that  have  directly compared the behavioral deficits induced by these two kinds of focal lesions. Anderson et al. (1990) found that tumors caused less severe and less  specific  deficits  for  the  site  of  damage.  Cipolotti  et  al.  (2015) examined executive tasks in frontal lesions, and found no significant difference in performance among strokes, high grade gliomas, low grade gliomas and meningiomas. A recent study by van Grinsven et al. (2023) used a lesion-symptom mapping approach to examine the influence of the etiology (stroke, tumor) in the localization of verbal memory and verbal fluency. They found substantial differences in lesion volume and topography  between  the  groups.  Despite  clear  differences  in  lesion topography, the cognitive profile was quite similar at the group-level. However, different neuroanatomical correlates were found in the two pathologies.

Here we re-examine the issue of cognitive impairment in stroke vs. brain tumors by testing the hypothesis that these two kinds of focal lesions will produce a low dimensional pattern of correlated behavioral deficits analogously to what we recently reported in stroke (Corbetta et  al.,  2015;  Bisogno  et  al.,  2021).  While  traditionally  teaching  in neurology  and  neuropsychology  emphasize  the  occurrence  of  many different cognitive syndromes, each with its own specific localization, more recent studies clearly show that cognitive deficits post-stroke are strongly correlated within and between functional domains across many patients. Accordingly, a small number of behavioral factors or components capture large fractions of inter-individual variability in cognitive performance. This low dimensionality has been shown with the National Institute  of  Health  Stroke  Scale  (NIHSS;  Lyden  et  al.,  2004;  Zandieh et  al.,  2012)  a  scale  that  measures  cognition cursorily, but also with more  in-depth  experimental  (Corbetta  et  al.,  2015)  or  more  clinical neurobehavioral assessments (Massa et al., 2015; Bisogno et al., 2021. Notably, these components accurately describe recovery of function and chronic impairment (Ramsey et al., 2017) representing robust behavioral phenotypes for large scale studies. The low dimensional organization  of  behavioral  impairment  corresponds  to  a  low  dimensional pattern of structural and functional connectivity abnormalities at the whole brain level (Corbetta et al., 2018; Thiebaut de Schotten et al., 2020; Salvalaggio et al., 2020).

Based on the above studies, we compared neuropsychological performance across multiple domains (language, memory, attention, executive  function)  in  a  prospective  series  of  stroke  and  brain  tumors asking  the  following  questions.  First,  will  the  pattern  of  behavioral impairment be similar in stroke and tumors? To study the correlation among neuropsychological tests, we used principal component analysis (PCA) to find possible patterns of inter-test and inter-subject correlation. Second, is lesion location strongly predictive of behavioral deficits in tumor at the individual level, as previously found in stroke? (Corbetta et al., 2015; Salvalaggio et al., 2020; Karnath et al., 2004). To address the issue, we apply ridge regression to compare the degree of correlation between  behavioral  deficits  and  lesion  location  in  stroke  and  brain tumors.

The discovery of similar vs. different patterns of cognitive impairment  in  stroke  and  tumors  is  theoretically  and  clinically  relevant. Theoretically, it is important to ask whether stroke and tumors can be interchangeably used as examples of focal lesions, and whether the low dimensionality of behavioral impairment found in stroke generalizes to another pathology. Clinically, with improvements in acute stroke care and surgical treatment of brain tumors, cognitive deficits are increasingly recognized causes of long-term disability in stroke (Kruithof et al., 2016; Wassenius et al., 2020; Silva et al., 2021) and tumors (Hansen et al., 2021). A definition of behavioral phenotypes would be helpful to plan pharmacological and rehabilitation interventions.

## 2. Material and methods

### 2.1. Subjects

We enrolled patients with brain tumors (n = 76) and patients with first symptomatic ischemic or haemorrhagic stroke (n = 133) admitted to the Neurology and Neurosurgery Unit of Padua University Hospital from December 2017 to February 2019. For all patients the exclusion criteria were as follows: 1. Age under 18; 2. Prior history of neurological or psychiatric disorders; 3. Previous central nervous system surgeries; 4. Presence of other medical conditions that precluded active participation in research and/or might alter the interpretation of the behavioral/imaging studies. In the case of brain tumors, additional exclusion criteria were  metastases  and  recurrences.  In  the  case  of  stroke,  additional exclusion criteria were more than two clinically silent lacunes, < 15 mm in  size  on  CT scan, and multifocal strokes. To make the two cohorts comparable from a neuropsychological perspective, we included only patients who were able to complete all tests of the neuropsychological assessment. All tumor patients were able to successfully complete the neuropsychological  battery.  A  significant  number  of  stroke  patients failed to complete the battery for the following reasons: 19 patients for severe aphasia; 8 for hemiplegia of dominant upper limb that prevented the administration of paper-and-pencil tests; 11 for both severe aphasia and hemiplegia; 4 for insufficient knowledge of Italian language; 5 for refusing to complete the whole battery; 9 for early transfer to another rehabilitation hospital. The final numbers of patients in the two cohorts were as follows: tumors n = 76 and stroke n = 77. Therefore, our stroke cohort represents a sample of patients with milder deficits.

This  is  a  retrospective  and  non-interventional  study.  This  study received approval from the Ethics Committee of the Azienda Ospedale Universit ` a  Padova  (Protocol  Number  70n/AO/20).  We  obtained  a waiver  for  written  informed  consent  since  all  data  were  collected retrospectively and anonymously.

### 2.2. Neuropsychological assessment

The  neuropsychological  assessment  tested  different  cognitive  domains. Specifically, we employed (1) the Oxford Cognitive Screen (OCS; Demeyere et al., 2015): a brief screening tool composed of tests of language, visual attention, spatial neglect, praxis abilities, visual and verbal memory,  calculation,  number  reading  and  executive  functions;  (2) subtests of the Esame Neuropsicologico Breve 2 (Mondini et al., 2011): the Trail Making Test (TMT), forms A and B (selective attention and switching  ability),  Phonemic  fluency,  Prose  memory  immediate  and delay  recall,  and  Memory  interference  test;  (3)  Boston  Naming  Test (BNT, visual naming); (4) forward and backward Digit span; and, (5) forward and backward Corsi block-tapping test (short-term and working memory).

*Subjects* in the stroke cohort were tested within two weeks from their event; subjects in the tumor cohort were also tested within two weeks of their hospitalization for a first clinical manifestation (e.g., confusion, focal deficit, or seizures) and prior to surgery.

### 2.3. Imaging

For each patient, an MRI or CT scan was collected. The ITK-snap imaging software system (version 3.6.0; Yushkevich et al., 2006) was used to manually segment lesions. All lesions were segmented by two of the authors (SF segmented tumor lesions, AB segmented stroke lesions) and were checked by a board-certified neuro-radiologist (author MGA). For stroke, either the CT (n. 14) or the Fluid Attenuated Inversion Recovery (FLAIR) sequence (n. 63) were used and segmented lesions were mapped on the 2 mm version of the Montreal Neurological Institute 152 6th generation atlas (Grabner et al., 2006) using the Clinical Toolbox of *S. Facchini et al.*

the SPM software system (Rorden et al., 2012). For tumor lesions, 3D T1w, FLAIR, and T2w sequences were used to manually segment the tumor lesion core and the oedema region separately. Segmented lesions were  mapped  on  the  same  atlas  using  the  Advanced  Normalization Toolbox (ANTs; Avants et al., 2011). The FMRIB Software Library (FSL; Jenkinson et al., 2012) was used to create a frequency map of individual lesions on the MNI152 atlas, thus producing an overlay map of all lesions for stroke, tumor core, and tumor core plus oedema.

### 2.4. Behavioral analysis

Firstly,  we  applied  a  dimensionality  reduction  using  principal component  analysis  (PCA)  to  the  behavioral  scores  (Turken  and Dronkers, 2011). PCA is a technique that identifies hidden variables or factors that capture the correlation of behavioral scores across subjects. Since  behavioral  scores  were  expected  to  be  correlated,  an  oblique rotation was used to maximize the segregation in different components as in previous work. A priori we set out to look at the first three components, based on prior stroke studies in which three components capture the majority of variance (Corbetta et al., 2015; Bisogno et al., 2021).

Secondly, a logistic regression model was run to test the discriminating  power  of  neuropsychological  tests  in  differentiating  the  two cognitive profiles. The model aim is to distinguish observations into two categories (Stock and Watson, 2015). In the model, these variables were controlled: age, gender, education, side of lesion (right vs. left).

### 2.5. Anatomical-clinical correlation

The  second  step  involved  modelling  of  the  behavioral  scores  in relation to the anatomical lesions. To be consistent with our previous studies (Corbetta et al., 2015; Salvalaggio et al., 2020; Bisogno et al., 2021; Pini et al., 2021) we performed a ridge regression (RR) analysis (Hoerl and Kennard, 1970). This method is applied when the number of predictors is high as compared to the number of subjects. The aim of the lesion-behavior analysis was to use lesion information in terms of voxelwise damage (location, volume) to explain behavioral deficits described in terms of behavioral PCs previously calculated. The predictor used was a binary matrix of lesioned voxels (for each subject and for each voxel, the entry of the matrix is set to 1 if the voxel is lesioned and 0 otherwise). The RR results furnished a map of weights linking lesion locations with behavioral deficits at the level of individual subjects. For example, a positive weight assigned to a voxel indicates that a lesion in such a voxel is likely related to the deficit appearance. It also provides an estimate of how that model accounts for the behavioral variability across subjects, in terms of variance explained (R 2 ). Consistently with our previous papers (Corbetta et al., 2015; Salvalaggio et al., 2020, Favaretto et al., 2022) we did not use a nested validation loop. The main rationale for using a nested cross-validation loop would be to ensure generalization of results  to  a  different  data  set,  and  it  would  be  necessary  to  predict behavioral PCs from lesions in new subjects. However, our main goal here is to establish whether lesions can explain behavioral PCs within the current data set (without aiming to generalize results to other data sets). We first applied a spatial PCA, and we used as regressors only the first Np PCs, which explained at least 95% of the original variance.

Thus, for each of the behavioral PCs, we estimated the model weights vector β as:

β = X T X + λI ) 1 X T y

where X ∈ R Ns × Np is the predictors matrix ( Ns is the number of subjects and Np is the number of selected spatial PCs), after z-scoring with respect to the whole matrix; X T ∈ R Np × Ns is the transpose of X , y ∈ R Ns is the vector of the outcome variable to be predicted (i.e. the selected behavioral  PC  score,  after  z-scoring), I ∈ R Np × Np is  the  identity  matrix  of dimension Np , and λ ∈ R is the regularization parameter, optimized as follows.

For each of the three RR models, the regularization parameter λ was optimized  by  identifying  a  value  within [ 10 5 , 10 5 ] ,  with  200  logarithmic steps. For each of these 200 values of λ ,  each RR model was trained and tested using a leave-one-out cross validation loop (LOOCV). In each loop, the optimal λ ( λ opt ) value was the one that minimized the prediction error over the training set.

Model accuracy was assessed through the coefficient of determination R 2 :

R 2 = 1 ∑ Ns i = 1

where yi represents the i -th element of vector y , and yi is its prediction.

The statistical significance of each model was estimated through a permutation  test,  with  10 , 000  iterations.  For  each  iteration,  the behavioral  scores  were  randomly  permuted  across  subjects,  and  the LOOCV with λ optimization was used to fit the RR model to the randomized  score.  The  p-value  for  the  observed R 2 was  defined  as  the probability of the R 2 of the randomized dataset to be larger than the observed R 2 (models with p-value < 0.05 were considered statistically significant).

To obtain the optimal set of RR model weights β , the average weights across the Ns loops at λ opt was considered. The distribution of weights obtained with the permutation test was used as null distribution to select the statistically significant weights. Only the β i that fall at the left or right ends (2.5%) of the tails of the null distribution were considered significant. These selected weights were back projected to the brain to display a map of the most predictive lesioned voxels. Finally, Gaussian smoothing (variance = 1) and scaling within [ 1 , + 1 ] was applied on the maps. Weights lower than 0.05 in absolute values were not shown.

RR models were employed to map lesion-behavioral deficits in both cohorts (brain tumor and stroke) separately. We repeated the RR estimation  for  the  tumor  patients ' cohort,  considering  the  tumor  core portion or the combination of both tumor core and oedema. The RR weights  obtained  for  the  tumor  core  as  behavioral  predictor  were compared to the RR weights estimated when considering the core plus the oedema region. This analysis examined whether the oedema region is behaviorally relevant.

Statistics  and  Machine  Learning  Toolbox  (https://it.mathworks. com/products/statistics.html) as implemented for Matlab R2018b was used for all statistical analysis.

## 3. Results

### 3.1. Demographic characteristics of the sample

The stroke sample (n = 77) included n = 8 haemorrhagic and n = 69 ischemic. The main risk factors identified in the medical history were hypertension (n = 53), smoke (n = 22), diabetes (n = 14), atrial fibrillation (n = 7). The mean NIHSS score was 2.08 (SD = 2.04; range = 0 -9). Most stroke patients were mild in severity (80% of patients had NIHSS score < 4). 75% of patients showed at least one motor symptom (arm weakness, leg weakness, facial palsy, or dysarthria). The tumor cohort consisted of n = 16 meningiomas and n = 60 gliomas, of which 7 low grade and 53 high grade.

The stroke sample was slightly older than the oncological sample (t (150) = 2.44; p = 0.016), whereas the two groups were similar in terms of mean education (t(147) = 1.81; p = 0.07). Gender differences were similar with an overall majority of males affected ( χ 2 (1) = 2.41; p = 0.12). Handedness did not differ among the two cohorts ( χ 2 (1) = 2.38; p = 0.21) (**Table 1** ) .

### 3.2. Principal components of behavioral impairment

To directly compare the behavioral impairment in stroke and tumors, the PCA was run on the whole sample (n = 153) yielding three main *S. Facchini et al.*

***Table 1 Demographic characteristics for neuro-oncological and stroke cohorts.***

|   | Brain tumors N ¼ 76 | Stroke N ¼ 77 | Statistical differences |
|---|---|---|---|
| Mean age (SD) | 59.6 (13.4) | 65.4 (13.9) | T = 2.44; p = 0.016 |
| Mean education (SD) | 10.4 (3.7) | 11.6 (4.4) | T = 1.81; p = 0.07 |
| Gender |   |   | χ 2 = 2.41; p = 0.12 |
| Male | 41 | 51 |   |
| Female | 35 | 26 |   |
| Handedness |   |   | χ 2 = 2.38; p = 0.21 |
| Right | 73 | 68 |   |
| Left | 3 | 9 |   |
| WHO 2016 Classification |   | - |   |
| Meningioma | 16 |   |   |
| II Oligodendroglioma | 2 |   |   |
| II Astrocytoma | 5 |   |   |
| III Gliosarcoma | 6 |   |   |
| IV Astrocytoma IDH-WT | 10 |   |   |
| IV Glioblastoma IDH-WT | 32 |   |   |
| IV Glioblastoma IDH-M | 5 |   |   |

Group differences were tested with a T-Test or a Pearson-Fisher χ 2 test; significant difference was found in mean age only.

factors that explained 41.5% of the variance (Fig. 1). We considered three PCs with oblique rotation as we assumed some correlation among tests.  Positive  loadings  indicate  lower  performance,  while  negative loadings indicate higher performance. PC1 accounted for 25% of the variance, PC2 for 9% of the variance and PC3 for 7.5% of the variance.

PC1  loaded  on  language,  verbal  memory,  and  executive/working memory (OCS-denomination, OCS-sentence reading, OCS-number writing, OCS-verbal memory, OCS-episodic memory, OCS-visual field right,  Memory  intereference  10  s,  Memory  interference  30  s,  Prose memory immediate, Prose memory delayed, Phonemic fluency, Digit *S. Facchini et al.*

*[picture on PDF page 4]*

**Figure labels:**
- 100
- Explained Variance
- 50
- 0
- 1 2 3 4 5 6 7 8 9 10 1 12 3 14 15 16 17 18 19 20 21 2 23 24 25 26 27 28 29
- PCs

*[picture on PDF page 4]*

**Figure labels:**
- Loadings PC1
- Loadings PC2
- Loadings PC3
- OCS-Denomination
- OCS-Semantics
- OCS-Orientation
- 'OCS-Visual Field right
- OCS-Visual Field right
- OCS-Visual Field left
- 'OCS-Visual Field left
- OCS-Sentence Reading
- OCS-Number Writing
- OCS-Calculation
- OCS-Egocentric Neglectright
- OCS-Allocentric Neglectright
- OCS-Hearts Overall Accuracy
- OCS-Egocentric Neglectleft
- 'OCS-Hearts Overall Accuracy
- 'OCS-Calculation
- OCS-Egocentic Neglectleft
- OCS-Allocentric Neglectleft
- 'OCS-AllocentricNeglectleft
- OCS-Verbal Memory
- OCS-*Episodic Memory*
- OCS-Executive Function simple
- OCS-Executive Functionsimple
- OCS-Executive Functionmixed
- Memory Interference 10s
- Memory Interference 30s
- Prose Memory immediate
- Prose Memory delayed
- Trail Making Test A
- Trail Making Test B
- *Phonemic Fluency*
- Corsi Test forward
- Corsi Test backward
- Digit Span forward
- Boston Naming Test
- Digit Span backward
- -0.2
- 0
- 0.2
- 0.4
- -0.4

*[picture on PDF page 5]*

**Figure labels:**
- 1
- Prose Memory delayed
- Prose Memory immediate
- Memory Interference 30s
- Memory Interference 10s
- Boston Naming Test
- 0.8
- *Phonemic Fluency*
- OCS-Denomination
- Digit Span forward
- OCS-Verbal Memory
- OCS-*Episodic Memory*
- 0.6
- OCS-Hearts Overall Accuracy
- Corsi Test backward
- Trail Making Test A
- OCS-Executive Function simple
- Corsi Test forward
- 0.4
- Trail Making Test B
- OCS-Egocentric Neglect right
- OCS-Executive Function mixed
- Digit Span backward
- 0.2
- OCS-Visual Field left
- OCS-Egocentric Neglect left
- OCS-Orientation
- OCS-Calculation
- OCS-Sentence Reading
- 0
- OCS-Number Writing
- OCS-Allocentric Neglect left
- OCS-Semantics
- OCS-Allocentric Neglect right
- OCS-Visual Field right
- -0.2

span forward and backward, Boston Naming Test, TMT form B); PC2 loaded  on  visuo-spatial  attention,  working  memory,  and  executive functions  (OCS-visual  field  left,  OCS-hearts  overall  accuracy,  OCSegocentric and allocentric neglect, OCS-executive function, TMT form A and B, Corsi Test forward and backward, Digit span backward); PC3 loaded on calculation, reading and visuospatial attention (OCS-orientation,  OCS-number  writing,  OCS-sentence  reading,  OCS-calculation, OCS-egocentric  neglect  left,  OCS-executive  function).  A  mixed  measure  ANOVA  confirmed  that  the  PC  loadings  were  not  significantly different in the tumor and stroke cohorts (F(2,296) = 1.47; p = 0.23).

The strength of pairwise correlation between tests can be visualized through a correlation matrix (Fig. 2). A correlation is evident between language,  verbal  memory,  executive/working  memory  (PC1)  with  r values ranging between r = 0.81 to r = 0.17; visuo-spatial attention correlated with executive functions (PC2) with r values ranging between r = 0.68 to r = 0.09; a third cluster included verbal functions (reading, writing, semantic knowledge), calculation, and visuo-spatial attention (PC3) with r values ranging between r = 0.53 to r = 0.16. In conclusion across domains and subjects, three factors accounted for a significant fraction of the variance, both in tumor and stroke.

To confirm these findings, we also ran the PCA separately in the two samples (Supplementary Fig. 1 ) : in the two groups the first three components  explained  a  similar  percentage  of  the  total  variance  (Stroke sample: 44.6%; Tumor sample: 48%). Moreover, the tests with the major loadings in each component were similar in the two groups: PC1 loaded on language, verbal memory, and executive/working memory (explained  variance  stroke  sample:  28%;  tumor  sample:  27%)  PC2 loaded on visuospatial attention and working memory, and executive functions (explained variance stroke sample: 9.2%; tumor sample: 12%);

PC3  was  the  most  different  between  the  two  groups,  however  it explained a low percentage of the total variance (explained variance stroke sample: 7.4%; tumor sample: 9%). We also repeated the analysis by considering only gliomas in the oncological cohort obtaining similar results (see Supplementary Fig. 2).

Finally, to test that the components found in stroke, as in previous studies (Corbetta et al., 2015; Bisogno et al., 2021), explain variance in the tumor data set, we first normalized both tumor data on stroke data and we applied the loadings coming from the PCA on stroke data. In this way, all patients could be projected into the same components space. Fig. 3 shows the distribution of scores along the three PC axes in stroke and tumor patients. It is apparent that the two populations cannot be separated,  indicating  that  the  cognitive  profiles  of  stroke  and  tumor patients can be summarized in the same principal components space. Finally, we reconstructed the original tumor data from the first three PCs, by multiplying the matrix of individual scores on the first three PCs (Npatientsx3)  with  the  rotated  matrix  of  the  loadings  of  the  same  PCs obtained from the stroke sample (Ntestsx3). Then, we correlated the data reconstructed in this way with the original data and obtained an R 2 = 30.3%. Hence, the three PCs on the stroke dataset explain 30% of the variance in the tumor dataset.

### 3.3. Logistic regression

While the previous analyses show that a significant portion of individual cognitive performance variability can be summarized by a common cognitive structure, we were also interested in differences between groups. **Table 2** shows scores for each test in the two groups (number of patients below normal cut-off, median and IQR). Supplementary Table 1

*S. Facchini et al.*

*[picture on PDF page 6]*

**Figure labels:**
- Stroke
- PC1
- Tumor
- 2
- 4
- PC2
- PC3
- -2
- 0
- 9

shows the median and IQR scores for each neuropsychological test for the different subgroups of the tumor sample (high grade glioma, low grade glioma, meningioma).

Differences in the cognitive profile were investigated by means of a logistic  regression  with  age,  education,  gender,  lesion  side  (right  vs. left), and tests scores as predictors. Five tests significantly discriminated a tumor from a stroke patient. Higher scores (more normal) in OCSdenomination  (z = 2.79;  p = 0.005)  and  OCS-calculation  (z = 3.17; p = 0.001) were positively associated with tumors; in contrast, high  scores  (more  normal)  in  OCS-episodic  memory  (z = 2.75;  p = 0.005), Memory interference 10 s (z = 2.28; p = 0.022), and Phonemic fluency (z = 2.21; p = 0.027) were positively associated with strokes (Fig. 4). We controlled all models for multicollinearity by means of the Variance Inflation Factors (VIF) which should be < 10 to suggest no potentially harmful collinearity. The AUC was 0.889. In other words, strokes  showed  more  impairment  in  language  denomination  and calculation  whereas  tumors  showed  more  impairment  in  episodic memory, verbal recall, and verbal executive function (fluency).

### 3.4. Lesion anatomy

Lesions were segmented and normalized to the MNI152 atlas (Fig. 5). Stroke lesions were localized more commonly subcortically especially in the basal ganglia and central white matter in agreement with previous maps (Corbetta et al., 2015; Thiebaut de Schotten et al., 2020; Bisogno et  al.,  2021).  Tumor  lesions  occurred  prevalently  in  the  frontal  and temporal white -grey matter junction, with a more heterogeneous distribution (Supplementary Table 2 shows the top regions of damage in the two cohorts). In general, the overlap of individual lesions was low with < 20% of patients with a lesion in the same location. The percentage of overlap increased in the tumor sample when considering the region of oedema.

### 3.5. Ridge regression models of lesion-to-behavior

We used ridge regression to model the behavioral scores based on lesion  information  (location,  volume).  The  analysis  aims  to  use  the lesion information to estimate behavioral scores at the individual level that  are  then  compared  with  the  empirically  measured  scores.  This analysis was conducted on patients who had both neuroimaging and neuropsychological data (tumor: n = 66; stroke: n = 67). Fig. 6 shows on the Y-axis the predicted score based on the lesion, while on the X-axis the actual score. It is apparent that when considering the tumor core, the lesion location did not explain any of the PC scores (R 2 < 10%). When considering the region of the tumor core plus oedema, the relationship was significant for PC1 ( R 2 = 0.16, p = 0.01). In the stroke population, the association was significant for PC1 ( R 2 = 0.13, p = 0.04), PC2 ( R 2 = 0.30, p < 0.001) scores, and not significant for PC3 ( R 2 = 0.39, p = 0.06). The analysis run by considering only gliomas was also not significant (Supplementary Fig. 3 ) .

Fig. 7 shows the maps with the lesion locations significantly associated with the behavioral scores. PC1-RR stroke map involves left peri -sylvian  cortex  consistent  with  language  impairments,  and  bilateral fronto-parietal and basal ganglia consistent with memory and executive deficits (both spatial and verbal). PC2-RR stroke map highlights posterior  right  hemisphere  regions  (occipito-parietal)  consistent  with  left visuo-spatial and overall performance deficits. Bilateral basal ganglia and frontal lesions are consistent with executive deficits. PC3-RR map *S. Facchini et al.*

***Table 2 Descriptive incidences of cognitive performance for each test in the two groups.***

|   | Brain tumors | Brain tumors | Stroke | Stroke |
|---|---|---|---|---|
|   | N. of patients below normal cut-off | Median (IQR) | N. of patients below normal cut-off | Median (IQR) |
| Oxford Cognitive Screen (OCS) |   |   |   |   |
| Denomination | 12 | 4 (3.75 - 4) | 28 | 3 (3 - 4) |
| Semantics | 0 | 3 (3 - 3) | 1 | 3 (3 - 3) |
| Orientation | 0 | 4 (4-4) | 2 | 4 (4-4) |
| Visual Field-Right | 2 | 4 (4-4) | 2 | 4 (4-4) |
| Visual Field-Left | 5 | 2 (2-2) | 3 | 2 (2-2) |
| Sentence Reading | 15 | 15 (15 - 15) | 18 | 15 (15 - 15) |
| Number Writing | 4 | 3 (3-3) | 6 | 3 (3-3) |
| Calculation | 11 | 4 (4-4) | 20 | 4 (3-4) |
| Hearts Overall Accuracy | 27 | 46 (43.75 - 49) | 28 | 47 (43 - 49) |
| Egocentric Neglect-Right | 9 | 0 (0-1) | 9 | 0 (0-1) |
| Egocentric Neglect-Left | 7 | 0 (0-1) | 8 | 0 (0-1) |
| Allocentric Neglect-Right | 1 | 0 (0-0) | 4 | 0 (0-0) |
| Allocentric Neglect-Left | 1 | 0 (0-0) | 2 | 0 (0-0) |
| Verbal Memory | 24 | 3 (2-4) | 22 | 3 (3-4) |
| Episodic Memory | 16 | 4 (4-4) | 11 | 4 (4-4) |
| Executive Function-Simple | 8 | 12 (12-12) | 13 | 12 (11-12) |
| Executive Function-Mixed | 14 | 13 (11-13) | 23 | 13 (10-13) |
| Memory Interference-10 sec | 13 | 6 (4-8) | 13 | 7 (5-9) |
| Memory Interference-30 sec | 14 | 5 (3-7) | 13 | 6 (4-8) |
| Prose Memory-Immediate | 16 | 10 (7-14) | 15 | 12 (8-14) |
| Prose Memory-Delayed | 22 | 13 (9-17) | 14 | 14 (9-17) |
| Trail Making Test-A | 3 | 38 (18-51.25) | 10 | 44 (30-70) |
| Trail Making Test-B | 21 | 126 (91.75-204) | 22 | 140 (86-255) |
| Phonemic Fluency | 23 | 10.3 (7.93-13.7) | 17 | 11 (7.67-15) |
| Corsi Test forward | 4 | 5 (4-6) | 3 | 5 (4-6) |
| Corsi Test backward | 13 | 4 (4-5) | 3 | 4 (4-6) |
| Digit Span forward | 15 | 5 (4-6) | 5 | 5 (5-6) |
| Digit Span Backward | 13 | 4 (3-5) | 10 | 4 (3-5) |
| Boston Naming Test | 26 | 13 (12 - 14) | 33 | 13 (10 - 14) |

Descriptive incidences of cognitive performance for each test in the two groups (number of patients below normal cut-off, median).Five tests significantly discriminated a tumor from a stroke patient. High scores (more normal) in OCS-denomination and OCS-calculation were positively associated with tumors (bold font in the table); high scores (more normal) in OCS-episodic memory, Memory interference 10 s, and Phonemic fluency were positively associated with strokes (italic font in the table).

shows bilateral cortical and subcortical lesions. Interestingly, none of the tumor RR maps were significant except for a marginal PC1 that splits left and right hemisphere lesions with positive loadings associated with more severe deficits in the left peri -sylvian cortex.

### 3.6. Cognitive performance of patients with similar lesion location (cluster analysis)

To  compare  the  neuropsychological  performance  of  stroke  and tumor patients with similar lesion locations, we conducted an exploratory analysis using a spectral clustering algorithm to divide patients in four anatomical clusters (see Supplementary Analysis and Results for a detailed description of the method). The analysis was limited by the low numerosity of each cluster (cluster 1: tumor (T) = 7, stroke (S) = 10; cluster 2: T = 21, S = 28; cluster 3: T = 18, S = 20; cluster 4: T = 10, S = 9). Therefore, most details are presented in the Supplementary results (see also Supplementary Fig. 4, and Supplementary Table 3).

We note only that differences in cognitive performance found in the logistic regression analysis were localized to specific anatomical clusters. Lesions in cluster 1 localized to left prefrontal regions, and stroke patients, as shown in the logistic regression (Fig. 4), performed worse on the naming subtest of the OCS than tumor patients (F = 9.343, p < 0.01). Also in agreement with the logistic regression, tumor patients performed worse on memory tests than stroke patients in cluster 2 (left temporal) and cluster 3 (right frontal).

## 4. Discussion

Focal neurological disorders (stroke, tumors) have been the prime model for studying the localization and organization of sensory, motor, and cognitive functions in the brain. While sensory and motor deficits are  accurately  detected  with  a  neurological  examination,  even  in  a structured scale like the NIHSS, the evaluation of cognitive deficits requires more in-depth neuropsychological testing. Cognitive deficits in focal brain disorders are clinically relevant as they represent the main cause of disability (Olesen et al., 2012). For instance, both brain tumor and stroke patients experience loss of memory and concentration that compromise their return to work (Treger et al., 2007; Randazzo and Peters, 2016; Ghanbari Ghoshchi et al., 2020).

This study compared the cognitive performance of patients with mild stroke vs. brain tumor lesions, specifically whether the low dimensional structure of cognitive deficits found in stroke also occurs in brain tumors. Secondly, stroke and brain tumors both occur preferentially in the white matter. Since lesion location is strongly associated with behavioral deficits in stroke (Corbetta et al., 2015; Salvalaggio et al., 2020; Karnath et al., 2004), we asked whether the same occurred for brain tumor lesions.

### 4.1. Methodological considerations

We focused on cognitive symptoms, and considered only data from patients  who  were  able  to  complete  the  whole  neuropsychological assessment. While every enrolled tumor patients completed the assessment, only about 60% of enrolled stroke patients were able to do so (n = 77 out of n = 133). As a result, our stroke sample was milder (mean NIHSS score on admission = 6.3 ± 4.1; score at the time of testing = 2.08 ± 2.05) as compared to other recently reported samples (Corbetta et al., 2015: mean NIHSS score on admission = 7.5; Bisogno et al., 2021: mean *S. Facchini et al.*

*[picture on PDF page 8]*

**Figure labels:**
- OCS-Denomination
- OCS-Visual Field right
- OCS-Visual Field left
- OCS-Sentence Reading
- OCS-Number Writing
- OCS-Calculation
- OCS-Hearts Overall Accuracy
- OCS-Egocentric Neglect right
- OCS-Egocentric Neglect left
- OCS-Allocentric Neglect right
- OCS-Allocentric Neglect left
- OCS-Verbal Memory
- OCS-*Episodic Memory*
- OCS-Executive Function simple
- OCS-Executive Function mixed
- Memory Interference 10s
- Memory Interference 30s
- Prose Memory immediate
- Prose Memory delayed
- Trail Making Test A
- Trail Making Test B
- *Phonemic Fluency*
- Corsi Test forward
- Corsi Test backward
- Digit Span forward
- Digit Span backward
- Boston Naming Test
- -3
- -2
- -1
- 0
- 1
- 2
- 3

NIHSS score on admission = 7.1 ± 5.6; at the time of testing = 3.2 ± 2.9). Accordingly, the percentage of patients with motor deficits was lower (75% vs 90% in Bisogno et al., 2021). However, the stroke and tumor sample  were  similar  in  terms  of  mean  education  and  gender, whereas the stroke population was slightly older. The  tumor sample included both meningiomas (n = 16) and gliomas (n = 60), but the results did not change when only gliomas were analyzed.

The lesion topography (Fig. 5) was quite different: the core tumor lesions  affected  the  grey-white  matter  junction,  with  a  predominant frontal  and  temporal  distribution  (Mandal  et  al.,  2020).  When  the oedema region was also considered the damage extended deeply and broadly in the white matter sparing only occipital and superior parietal cortex. Strokes damaged predominantly basal ganglia and central white matter, with only 10 -15% involving cortex, as previously reported in larger cohorts (Corbetta et al., 2015; Thiebaut de Schotten et al., 2020; Bisogno et al., 2021; Kang et al., 2003; Wessels et al., 2006). The degree of  overlap across lesions was low ( < 20%). Our maps resemble those reported recently by van Grinsven et al. (2023), who also showed a low lesion overlap per area (12.8 % for tumor, and 4.8 % per stroke) with only about 1/3 of the areas involved in both pathologies in more than 5% of patients.

### 4.2. A common low dimensional structure of cognitive impairment in brain tumors and stroke

The first notable result is that a low dimensional set of correlated cognitive deficits explained about half of the variability across subjects, both when all patients were considered jointly (Figs. 1 -2) or split by pathology (Supplementary Fig. 1). The variance explained by the first three components in the joint PCA (42%) was comparable to Bisogno et al. ' s (2021) in which three components explained 50% of the variance in a larger and more severe stroke sample (n = 158). The first component loaded on language, verbal memory, and executive/working memory; the  second  component  loaded  on  visuo-spatial  attention  (OCS-hearts overall  accuracy,  OCS-egocentric  and  allocentric  neglect),  working memory and executive functions (e.g., TMT A and B, Corsi Test, Digit span backwards); the third component loaded on deficits of reading, calculation, and visuo-spatial that were partly captured in components 1 and 2. The selection of three components was a priori based on previous work in stroke (Corbetta et al., 2015; Bisogno et al., 2021), and components 1 and 2 were similar to those reported after including motor deficits (Corbetta et al., 2015; Bisogno et al., 2021). We also directly tested how much variance of the cognitive scores in tumor patients could be predicted by the component structure derived from the stroke cohort. About 30% of the variability in tumor patients ' performance can be described by using the loadings derived from stroke; also the two populations  are  indistinguishable  when  plotted  in  the  three  component space (Fig. 3).

Recently, Sperber et al. (2023) have criticized the low dimensionality of behavioral deficits in stroke as an artifact of lesion anatomy. However, as recently discussed (Pini et al., 2023), anatomy alone does not  explain  the  low  dimensionality  of  cognitive  deficits  after  focal injury. In fact, even after considering the variables indicated by Sperber et al. we showed that behavior is summarized by the lowest number of components as compared to anatomical models alone. Moreover, the current work shows a similar correlation for lesions of different etiologies that are localized on average to different anatomical sites. Finally, we found correlation among behavioral scores in tumors in which lesion location  did  not  explain  behavioral  variance  (Fig.  5).  Overall,  we conclude that the low dimensionality of behavioral deficits cannot be explained by anatomy alone.

Even though mild stroke and tumors yielded a similar pattern of correlated cognitive deficits, we also found some evidence of differentiation in their cognitive profile. Mild stroke patients were more affected in functions that require more localized processing such as language and calculation as shown in the logistic regression model (OCS-denomination;  OCS-calculation, Fig. 4). The stronger impairment of stroke patients in OCS-denomination localized in left prefrontal regions (cluster 1,  Suppl.  Fig.  4).  In  contrast,  tumor  patients  were  more  affected  in memory  performance  (OCS-episodic  memory,  Memory  interference, Phonemic fluency, Fig. 4) that localized in left temporal (cluster 2) and right frontal (cluster 3) (Suppl. Fig. 4 ) .

A similar pattern has been recently reported in van Grinsven et al. (2023). Using lesion-symptom mapping they investigated performance for  verbal  memory  and  language  in  two  cohorts  of  stroke  and  brain tumor patients. They found comparable group-level impairment, similarly to our PCA results, and a different lesion topography, as we did. When looking  for  anatomical  locations  related  to  behavioral  performance, they reported a correlation between memory performance and areas  surrounding  the  left  hippocampus  in  brain  tumors,  but  not  in stroke sample. Moreover, several left hemisphere cortical regions (left insula,  rolandic  operculum,  Heschl ' s  gyrus)  were  linked  to  verbal fluency impairment, but only when the lesion was a tumor. Therefore, although van Grinsven et al. (2023) emphasize differences across pathologies, the actual data are quite similar across studies with evidence of both similarity and mild differences. Despite the general low lesionsymptom correlation in brain tumors (see paragraph below for a discussion), we found some vulnerability to memory impairment in left temporal tumors as compared to strokes. The left temporal region is one of the most common sites in gliomas possibly because the hippocampus is one of the sites where neural stem cells are generated (Mandal et al., 2020). The left hippocampus was also found as an ' eloquent ' hotspot for verbal memory and critically linked to memory deficits in brain tumor patients (Campanella et al., 2018). Finally, when considering only the *S. Facchini et al.*

*[picture on PDF page 9]*

**Figure labels:**
- TUMOR CORE +
- EDEMA
- R
- 0.15
- TUMOR CORE
- STROKE

left hemisphere, patients suffering from tumors in the anterior temporal lobe were most frequently and severely impaired in verbal memory as compared to lesions in other areas (Behrens et al., 2021).

The description of cognitive phenotypes that capture large amount of variance, and that are specific for a certain pathology, could be clinically relevant because it allows to shift the focus of clinicians from the rare and interesting cases to the great majority of patients. This is especially true in the case of brain tumors, where symptoms are subtler. These phenotypes  are  robust  and  shall  be  used  for  large  scale  studies  of treatment,  genetics,  or  outcome.  The  importance  of  shifting  from  a modular to a network-wide view of cognitive impairment in brain tumors has been also advocated by Duffau and colleagues (Duffau, 2018; Herbet and Duffau, 2020; Duffau, 2021).

### 4.3. Low behavioral specificity of lesion location in tumors

The second important question concerned the correlation between the behavioral scores and the anatomical lesions. The lesion topography was  different  with  tumors  affecting  predominantly  the  frontal  and temporal white -gray matter junction while stroke damaging prevalently the basal ganglia and deep white matter (Fig. 5). This different topography is also consistent with van Grinsven et al. (2023).

The  ridge  regression  detected  a  relationship  between  anatomical lesions and behavioral deficits at the individual subject level only in stroke. PC1 deficits loading on language and memory localized in left > right peri -sylvian, bilateral basal ganglia and frontal cortex. PC2 deficits loading  on  general  performance  and  visuo-spatial  localized  to  right occipito-parietal  cortex.  Notably,  no  significant  correlation  was  obtained  in  brain  tumors  using  the  core  lesion  locations.  A  significant correlation for PC1 was obtained only when considering core-oedema lesions and localized to the left peri -sylvian cortex like in stroke.

The low behavioral specificity of lesion location in tumors shall be considered  preliminary  given  the  relatively  low  number  of  patients tested. Anderson et al. (1990) had previously noted that extensive tumors involving areas of different lobes do not lead to cognitive damage in contrast with strokes with same extension. Van Grinsven et al. (2023) found that lesion volumes were larger in the tumor group and correlated with cognitive performance. However, at the group level, this difference in volume did not result in more severe cognitive impairment in the tumor as compared to the stroke population.

Different research groups have pointed out that even large tumors in eloquent areas, or recurrences of brain tumors operated on, do not cause the  expected  cognitive  deficits,  and  that  this  can  be  related  to  two mechanisms: plasticity and remapping of function that occurs as tumors grow; and those cognitive functions do not map onto specific regions but network of regions (Duffau, 2017; Nenning et al., 2020; Duffau, 2021) . Studies on brain tumor prognosis have found contrasting values of lesion location and volume in terms of survival (Awad et al., 2017; Curtin et al., 2021).  We  have  recently  completed  a  study  looking  at  variables  accounting for post-surgical cognitive performance and found little value of pre-operative lesion location and volume. In contrast, we found presurgical  neuropsychological  scores  to  be  highly  predictive  of  post- *S. Facchini et al.*

TUMOR CORE +

*[picture on PDF page 10]*

**Figure labels:**
- PC1 - R2 = 0.16
- PC2 - R2 = −0.00
- PC3 - R2 = 0.06
- scores - predicted
- 3
- LEFT
- PC2 scores - predicted
- 4
- RIGHT
- 2
- EDEMA
- 1
- 0
- C1
- PC3 s
- -1
- P
- PC1 scores
- PC2 scores
- PC3 scores
- PC1 - R2 = 0.04
- PC2 - R2 = 0.02
- PC3 - R2 = 0.07
- • LEFT
- TUMOR CORE
- PC1
- PC3
- PC1 - R2 = 0.13
- PC2 - R2 = 0.39
- PC3 - R2 = 0.39
- 6
- STROKE
- PC2

surgical performance. These findings support the notion that cognitive functions are distributed and remapped in brain tumors, and that psychological evaluations more than anatomical lesions are a good read-out of current brain function (Zangrossi et al., 2022).

In contrast to the low predictive value of lesion core location, we did find some correlation for PC1 (language, memory) when the region of oedema was added to the lesion core location. The map highlighted the left peri -sylvian region that was one of the regions predictive in stroke. A link  between  oedema  and  cognitive  function  has  been  described  in relation to radiotherapy treatment (Wang et al., 2021). Recently, we showed  abnormal  functional  connectivity  in  cortical  regions  remote from the tumor core, but presumably connected to it by anatomical fibers that travel through the surrounding oedema region (Silvestri et al.,

2022). In conclusion, the anatomical analysis provides preliminary evidence  that  tumor  location  is  less  correlated  overall  with  cognitive impairment than stroke location.

## 5. Conclusions and limitations

This study shows that mild acute strokes and brain tumors cause a similar pattern of cognitive impairment across cognitive domains and subjects. We also show specific deficits that are stronger in one or the other pathology.

A common behavioral deficit correlation in mild stroke and tumors, notwithstanding  their  different  lesion  topography,  provides  evidence that lesion location alone is not enough  to explain behavioral *S. Facchini et al.*

### STROKE

*[picture on PDF page 11]*

**Figure labels:**
- R
- PC1
- p = 0.04
- PC2
- p < 0.001
- PC3
- p = 0.06
- TUMOR (core plus edema)
- p = 0.01
- -0.01 0.01

-1

***Fig. 7. Ridge regression maps. Ridge regression maps of PCs for significant correlation are represented. In the stroke population, significant correlation is found in PC1, PC2 and PC3 (lines above); in the tumor population, only PC1 reported a significant correlation when considering the core with the oedema (below). Warm colors represent positive correlation between anatomical voxels and high PC values (i.e. high level of impairment in the corresponding domains). Cold colors represent negative correlation between anatomical voxels and high PC values.***

impairment. In stroke, we, and others (Thiebaut de Schotten et al., 2020) have  argued  that  lesions  in  many  locations  cause  a  much  lower dimensional pattern of structural disconnection and functional connectivity alteration (Siegel et al., 2016; Salvalaggio et al., 2020). Importantly, these network abnormalities are more associated with cognitive impairment than lesion location, which is instead strongly linked with sensory  and  motor  functions  (Siegel  et  al.,  2016;  Salvalaggio  et  al., 2020). We postulate that similar mechanisms are at work in tumors, as also supported by the surgical and neuropsychological observations of Duffau (2018).

The study is limited by the sample size that prevents any conclusion about  differences  in  cognitive  performance  for  lesions  at  the  same location with different etiology. Another limitation is that we focused on milder strokes to make them more comparable to the performance of brain tumors. Therefore, our results cannot be generalized to the entire stroke population. Moreover, in our sample, stroke lesions incompletely covered  the  typical  distribution  as  shown  in  prior  studies  (Corbetta et al., 2015; Thiebaut de Schotten et al., 2020; Bisogno et al., 2021). This limits conclusions about brain-behavior correlation in regions that were not damaged. However, the low-dimensional cognitive pattern described with the PCA is like previous work based on a larger sample and a wider distribution of lesions (Corbetta et al., 2015; Bisogno et al., 2021). Moreover, we did not perform a nested cross-validation to optimize  the  hyperparameter  in  the  ridge  regression,  thus  current  ridge regression  findings might  be  sample-specific  and their  generalization should be tested by a replication on an independent cohort.

Finally, our analysis was based just on lesion location and volume. Future studies may consider other structural or functional variables that may  relate  to  performance  and  may  differ  between  etiology:  white matter  integrity,  functional  networks,  cortical  atrophy.  A  natural extension  of  this  study  would  be  to  examine  behavioral  predictions separately  for  tumor  core  and  oedema  region  to  assess  the  role  of oedema in causing cognitive deficits, by comparing behavioral prediction  using  disconnection  methods  (Boes  et  al.,  2015;  Thiebaut  de Schotten and Foulon, 2018; Thiebaut de Schotten et al., 2020; Pini et al., 2021). In clinical practice steroid treatment is empirically given to treat oedema, and patients ' neurological deficits do improve.

### CRediT authorship contribution statement

Silvia Facchini: Conceptualization, Methodology, Writing -original draft. Chiara  Favaretto: Formal  analysis,  Methodology,  Software. Marco  Castellaro: Formal  analysis,  Validation. Andrea  Zangrossi: Formal analysis, Validation. Margherita Zannin: Investigation. Antonio Luigi Bisogno: Investigation. Valentina Baro: Investigation. Maria Giulia Anglani: Data curation, Supervision. Antonio Vallesi: Supervision. Claudio Baracchini: Supervision. Domenico D ' Avella: Supervision. Alessandro Della Puppa: Supervision. Carlo Semenza: Supervision. Maurizio  Corbetta: Conceptualization,  Methodology, Writing -review & editing, Project administration.

### Declaration of Competing Interest

The authors declare that they have no known competing financial interests or personal relationships that could have appeared to influence the work reported in this paper.

### Data availability

Data will be made available on request.

### Acknowledgements

We thank our patients who participated in the study, and their family for  support.  Without  their  willingness  to  help  for  improving  future clinical  diagnosis  and  treatment  this  study  would  have  not  been possible.

### Study funding

MC was supported by Fondazione Cassa di Risparmio di Padova e Rovigo  (CARIPARO)  Grant  Agreement  number  55403; Ministry  of *S. Facchini et al.*

Health,  Italy  (RF-2008-12366899) Brain  connectivity  measured  with high-density electroencephalography: a novel neurodiagnostic tool for stroke- NEUROCONN; BIAL foundation grant (Grant Agreement number 361/18); H2020 European School of Network Neuroscience (euSNN); H2020 Visionary Nature Based Actions For Heath, Wellbeing & Resilience in Cities (VARCITIES); Ministry of Health Italy (RF-201912369300): Eye-movement dynamics during free viewing as biomarker for assessment of visuospatial functions and for closed-loop rehabilitation in stroke (EYEMOVINSTROKE); European Union (ERC-2022-SYG NEMESIS Grant number 101071900) *. Views and opinions expressed are* *however those of the author(s) only and do not necessarily reflect those of the* European  Union  or  the  European  Research  Council  Executive  Agency. Neither the European Union nor the granting authority can be held responsible for them.

### Appendix A. Supplementary data

**Supplementary data** to this article can be found online at https://doi. org/10.1016/j.nicl.2023.103518.

### References

- Anderson, S.W., Damasio, H., Tranel, D., 1990. Neuropsychological impairment associated with lesions caused by tumor or stroke. Arch. Neurol. 47, 397 -405.
- Avants, B.B., Tustison, N.J., Song, G., Cook, P.A., Klein, A., Gee, J.C., 2011. A reproducible evaluation of ANTs similarity metric performance in brain image registration. Neuroimage 54 (3), 2033 -2044.
- Awad, A.W., Karsy, M., Sanai, N., Spetzler, R., Zhang, Y., Xu, Y., Mahan, M.A., 2017. Impact of removed tumor volume and location on patient outcome in glioblastoma. J. Neurooncol. 135 (1), 161 -171.
- Behrens, M., Thakur, N., Lortz, I., Seifert, V., Kell, C.A., Forster, M.-T., 2021. Neurocognitive deficits in patients suffering from glioma in speech-relevant areas of the left hemisphere. Clin. Neurol. Neurosurg. 207, 106816.
- Bisogno, A.L., Favaretto, C., Zangrossi, A., Monai, E., Facchini, S., De Pellegrin, S., Pini, L., Castellaro, M., Basile, A.M., Baracchini, C., Corbetta, M., 2021. A lowdimensional structure of neurological impairment in stroke. Brain Commun. 3 (2), 1 -13.
- Boes, A.D., Prasad, S., Liu, H., Liu, Q.i., Pascual-Leone, A., Caviness, V.S., Fox, M.D., 2015. Network localization of neurological symptoms from focal brain lesions. Brain 138 (10), 3061 -3075.
- Campanella, F., Del Missier, F., Shallice, T., Skrap, M., 2018. Localizing memory functions in brain tumor patients: anatomical hotspots. World Neurosurg. 120, e690 -e709.
- Cipolotti, L., Healy, C., Chan, E., Bolsover, F., Lecce, F., White, M., Span ` o, B., Shallice, T., Bozzali, M., 2015. The impact of different aetiologies on the cognitive performance of frontal patients. Neuropsychologia 68, 21 -30.
- Corbetta, M., Ramsey, L., Callejas, A., Baldassarre, A., Hacker, C.D., Siegel, J.S., Astafiev, S.V., Rengachary, J., Zinn, K., Lang, C.E., Tabor Connor, L., Fucetola, R., Strube, M., Carter, A.R., Shulman, G.L., 2015. Common behavioral clusters and subcortical anatomy in stroke. Neuron 85 (5), 927 -941.
- Corbetta, M., Siegel, J.S., Shulman, G.L., 2018. On the low dimensionality of behavioral deficits and alterations of brain network connectivity after focal injury. Cortex 107, 229 -237.
- Curtin, L., Whitmire, P., White, H., Bond, K.M., Mrugale, M.M., Hu, L.S., Swanson, K.R., 2021. Shape matters: morphological metrics of glioblastoma imaging abnormalities as biomarkers of prognosis. Sci. Rep. 11 (1), 23202.
- Demeyere, N., Riddoch, M.J., Slavkova, E.D., Bickerton, W.L., Humphreys, G.W., 2015. The Oxford Cognitive Screen (OCS): Validation of a stroke-specific short cognitive screening tool. Psychol. Assess. 27 (3), 883 -894.
- Duffau, H., 2017. A two-level model of interindividual anatomo-functional variability of the brain and its implications for neurosurgery. Cortex 86, 303 -313.
- Duffau, H., 2018. The error of Broca: From the traditional localizationist concept to a connectomal anatomy of human brain. J. Chem. Neuroanat. 89, 73 -81.
- Duffau, H., 2021. The death of localizationism: The concepts of functional connectome and neuroplasticity deciphered by awake mapping, and their implications for best care of brain-damaged patients. Rev. Neurol. 177 (9), 1093 -1103.
- Favaretto, C., Allegra, M., Deco, G., Metcalf, N.V., Griffis, J.C., Shulman, G.L., Brovelli, A., Corbetta, M., 2022. Subcortical-cortical dynamical states of the human brain and their breakdown in stroke. Nat. Commun. 13 (1), 5069.
- Ghanbari Ghoshchi, S., De Angelis, S., Morone, G., Panigazzi, M., Persechino, B., Tramontano, M., Capodaglio, E., Zoccolotti, P., Paolucci, S., Iosa, M., 2020. Return to Work and Quality of Life after Stroke in Italy: A Study on the Efficacy of Technologically Assisted Neurorehabilitation. Int. J. Environ. Res. Public Health 17 (14), 5233.
- Grabner, G., Janke, A.L., Budge, M.M., Smith, D., Pruessner, J., Collins, D.L., 2006. Symmetric Atlasing and Model Based Segmentation: An Application to the Hippocampus in Older Adults. In: Larsen R, Nielsen M, Sporring J (Eds.), Medical Image Computing and Computer-Assisted Intervention -MICCAI 2006. Lecture Notes in Computer Science, vol 4191. Springer, Berlin, Heidelberg.
- Hansen, A., Pedersen, C.B., Minet, L.R., Beier, D., Jarden, J.O., S ø gaard, K., 2021. Hemispheric tumor location and the impact on health-related quality of life, symptomatology, and functional performance outcomes in patients with glioma: an exploratory cross-sectional study. Disabil. Rehabil. 43 (10), 1443 -1449.
- Herbet, G., Duffau, H., 2020. Revisiting the Functional Anatomy of the Human Brain: Toward a Meta-Networking Theory of Cerebral Functions. Physiol. Rev. 100 (3), 1181 -1228.
- Hoerl, A.E., Kennard, R.W., 1970. American Society for Quality Ridge Regression: Biased Estimation For Nonorthogonal Problems. Technometrics 12 (1), 55 -67.
- Jenkinson, M., Beckmann, C.F., Behrens, T.E.J., Woolrich, M.W., Smith, S.M., 2012. FSL. NeuroImage 62 (2), 782 -790.
- Kang, D.W., Chalela, J.A., Ezzeddine, M.A., Warach, S., 2003. Association of ischemic lesion patterns on early diffusion-weighted imaging with TOAST stroke subtypes. Arch. Neurol. 60, 1730 -1734.
- Karnath, H.O., Fruhmann Berger, M., Küker, W., Rorden, C., 2004. The anatomy of spatial neglect based on voxelwise statistical analysis: a study of 140 patients. Cereb. Cortex 14 (10), 1164 -1172.
- Klein, M., Duffau, H., De Witt Hamer, P.C., 2012. Cognition and resective surgery for diffuse infiltrative glioma: an overview. J. Neurooncol. 108 (2), 309 -318.
- Kruithof, W.J., Post, M.W., van Mierlo, M.L., van den Bos, G.A., de Man-van Ginkel, J.M., Visser-Meily, J.M., 2016. Caregiver burden and emotional problems in partners of stroke patients at two months and one year post-stroke: Determinants and prediction. Patient Educ. Couns. 99 (10), 1632 -1640.
- Lyden, P., Claesson, L., Havstad, S., Ashwood, T., Lu, M., 2004. Factor analysis of the National Institutes of Health Stroke Scale in patients with large strokes. Arch. Neurol. 61 (11), 1677 -1680.
- Mandal, A.S., Romero-Garcia, R., Hart, M.G., Suckling, J., 2020. Genetic, cellular, and connectomic characterization of the brain regions commonly plagued by glioma. Brain 143, 3294 -3307.
- Massa, M.S., Wang, N., Bickerton, W.L., Demeyere, N., Riddoch, M.J., Humphreys, G.W., 2015. On the importance of cognitive profiling: A graphical modelling analysis of domain-specific and domain-general deficits after stroke. Cortex 71, 190 -204.
- Mondini, S., Mapelli, D,, Vestri, A., Arcara, G., Bisiacchi, P.S., 2011. Esame neuropsicologico breve II. Una batteria di test per lo screening neuropsicologico, Milano: Raffello Cortina Editore.
- Nenning, K.H., Furtner, J., Kiesel, B., Schwartz, E., Roetzer, T., Fortelny, N., Bock, C., Grisold, A., Marko, M., Leutmezer, F., Liu, H., Golland, P., Stoecklein, S., Hainfellner, J.A., Kasprian, G., Prayer, D., Marosi, C., Widhalm, G., Woehrer, A., Langs, G., 2020. Distributed changes of the functional connectome in patients with glioblastoma. Sci. Rep. 10 (1), 18312.
- Olesen, J., Gustavsson, A., Svensson, M., Wittchen, H.U., J ¨ onsson, B., CDBE2010 study group, 2012. The economic cost of brain disorders in Europe: Economic cost of brain disorders in Europe. Eur. J. Neurol. 19, 155 -162.
- Pini, L., Bisogno, A. L., Salvalaggio, A., Shulman, G.L., Corbetta, M., 2023. The correlation of behavioural deficits post-stroke: a trivial issue? Brain, Letter to the editor.
- Pini, L., Salvalaggio, A., De Filippo De Grazia, M., Zorzi, M., Thiebaut de Schotten, M., Corbetta, M., 2021. A novel stroke lesion network mapping approach: improved accuracy yet still low deficit prediction. Brain Commun., 3(4), fcab259.
- Ramsey, L.E., Siegel, J.S., Lang, C.E., Strube, M., Shulman, G.L., Corbetta, M., 2017. Behavioral clusters and predictors of performance during recovery from stroke. Nat. Hum. Behav. 1 (3), 0038.
- Randazzo, D., Peters, K.B., 2016. Psychosocial distress and its effects on the healthrelated quality of life of primary brain tumor patients. CNS Oncol. 5 (4), 241 -249. Rorden, C., Bonilha, L., Fridriksson, J., Bender, B., Karnath, H.O., 2012. Age-specific CT and MRI templates for spatial normalization. Neuroimage 61 (4), 957 -965.
- Salvalaggio, A., De Filippo De Grazia, M., Zorzi, M., Thiebaut de Schotten, M., Corbetta, M., 2020. Post-stroke deficit prediction from lesion and indirect structural and functional disconnection. Brain, 143(7), 2173 -2188.
- Siegel, J.S., Ramsey, L.E., Snyder, A.Z., Metcalf, N.V., Chacko, R.V., Weinberger, K., Baldassarre, A., Hacker, C.D., Shulman, G.L., Corbetta, M., 2016. Disruptions of network connectivity predict impairment in multiple behavioral domains after stroke. PNAS 113 (30).
- Silva, C.R.R.D., Pimenta, C.J.L., Viana, L.R.C., Ferreira, G.R.S., Bezerra, T.A., Costa, T.F. D., et al., 2021. Specific health-related quality of life in Cerebrovascular accident survivors: associated factors. Rev. Bras. Enferm. 29, 75(3):e20210407.
- Silvestri, E., Moretto, M., Facchini, S., Castellaro, M., Anglani, M., Monai, E., D ' Avella, D., Della Puppa, A., Cecchin, D., Bertoldo, A., Corbetta, M., 2022. Widespread cortical functional disconnection in gliomas: an individual network mapping approach. Brain Commun. 4 (2), fcac082.
- Sperber, C., Gallucci, L., Umarova, R., 2023. The low dimensionality of post-stroke cognitive deficits: it ' s the lesion anatomy! Brain, 146, 2443-2452.
- Stock, J.H., Watson, M.W., 2015. Regression with a Binary Dependent Variable. In: Introduction to Econometrics, 3 ª ed. Pearson, pp. 442 -443.
- Thiebaut de Schotten, M., Foulon, C., 2018. The rise of a new associationist school for lesion-symptom mapping. Brain 141, 2 -4.
- Thiebaut de Schotten, M., Foulon, C., Nachev, P., 2020. Brain disconnections link structural connectivity with function and behavior. Nat. Commun. 11 (1), 5094.
- Treger, I., Shames, J., Giaquinto, S., Ring, H., 2007. Return to work in stroke patients. Disabil. Rehabi. 29 (17), 1397 -1403.
- Turken, A.U., Dronkers, N.F., 2011. The neural architecture of the language comprehension network: converging evidence from lesion and connectivity analyses. Front. Syst. Neurosci. 5, 1.
- van Grinsven, E.E., Smits, A.R., van Kessel, E., Raemaekers, M.A.H., de Haan, E.H.F., Huenges Wajer, I.M.C., Ruijters, V.J., Philippens, M.E.P., Verhoeff, J.J.C., Ramsey, N.F., Robe, P.A.J.T., Snijders, T.J., van Zandvoort, M.J.E., 2023. The impact

*S. Facchini et al.*

- of etiology in lesion-symptom mapping -A direct comparison between tumor and stroke. NeuroImage: Clinical 37, 103305.
- Wang, X., Chen, D., Qiu, J., Li, S., Zheng, X., 2021. The relationship between the degree of brain edema regression and changes in cognitive function in patients with recurrent glioma treated with bevacizumab and temozolomide. Quant. Imaging Med. Surg. 11 (11), 4556 -4568.
- Wassenius, C., Claesson, L., Blomstrand, C., Jood, K., Carlsson, G., 2020. Integrating consequences of stroke into everyday life - Experiences from a long-term perspective. Scand. J. Occup. Ther. 12, 1 -13.
- Wessels, T., Wessels, C., Ellsiepen, A., Reuter, I., Trittmacher, S., Stolz, E., Jauss, M., 2006. Contribution of diffusion-weighted imaging in determination of stroke etiology. AJNR Am. J. Neuroradiol. 27, 35 -39.
- Yushkevich, P.A., Piven, J., Hazlett, H.C., Gimpel Smith, R., Ho, S., Gee, J.C., Gerig, G., 2006. User-guided 3D active contour segmentation of anatomical structures: Significantly improved efficiency and reliability. Neuroimage 31 (3), 1116 -1128.
- Zandieh, A., Kahaki, Z.Z., Sadeghian, H., Pourashraf, M., Parviz, S., Ghaffarpour, M., Ghabaee, M., 2012. The underlying factor structure of National Institutes of Health Stroke scale: an exploratory factor analysis. Int. J. Neurosci. 122 (3), 140 -144.
- Zangrossi, A., Silvestri, E., Bisio, M., Bertoldo, A., De Pellegrin, S., Vallesi, A., Della Puppa, A., D ' Avella, D., Denaro, L., Scienza, R., Mondini, S., Semenza, C., Corbetta, M., 2022. Predictors of cognitive outcome after brain tumor resection in glioma patients, personal communication. NeuroImage: Clinical 36, 103219.