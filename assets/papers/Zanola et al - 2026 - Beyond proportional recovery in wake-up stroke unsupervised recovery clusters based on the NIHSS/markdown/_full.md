### METHODOLOGY

### Open Access

### Beyond proportional recovery in wake-up stroke: unsupervised recovery clusters based on the NIHSS

*[picture on PDF page 1]*

Andrea Zanola 1,2*† , Antonio Luigi Bisogno 1,2,3† , Veronika Vadinova 1,3 , Götz Thomalla 4 , Bastian Cheng 4 , Manfredo Atzori 1,2,5 and Maurizio Corbetta 1,2,3

### Abstract

Post-stroke rehabilitation is a complex process influenced by several neurophysiological factors. The recovery is traditionally predicted based on initial impairment using linear models. The Proportional Recovery Rule (PRR), developed on the Fugl-Meyer scale, has even been proposed as a therapeutic target. In this framework, patients are classified as 'fitters' or 'non-fitters' , though this distinction depends on the methodology used. Additionally, issues like mathematical coupling and ceiling effects on clinical scales could raise concerns about the validity of these models. To overcome these issues, Repeated Spectral Clustering (RSC) was used to identify recovery patterns based on NIHSS. We selected 201 patients from the WAKE-UP trail, all moderately impaired at onset and still impaired at 22-36 h. Clustering was performed using a similarity matrix based on pairwise absolute differences between recovery ratios, calculated from 22-36 h to 90 days post-stroke. Cluster differences were tested with prognostic factors, including lesion volume, side, treatment, and the Heidelberg scale. The PRR was fit to the cohort for comparison with clustering results. The linear fit reproduced findings consistent with the literature, such as a correlation of ρ ( x, ∆) = 0 . 73 and an average recovery ratio of 70% for the 'fitters'. RSC grouped patients into six recovery clusters: C 0 (full recovery), C 1 (above average), C 2 and C 3 (average, PRR-aligned), C 4 (below average), and C 5 (deterioration). NIHSS scores in most patients declined non-proportionally. Lesion volume was not significantly different across clusters, while left-sided strokes were higher in low recovery clusters. Patients with a recovery ratio ≥ 0 . 3 within two weeks mostly fell into favorable clusters ( C 0 -C 3 ), covering ≈ 90% of such cases. The identified clusters provide a refined view of stroke recovery following wake-up stroke. Clustering better captures patient similarities, enabling the assessment of neurophysiological differences between groups and supporting tailored interventions.

Keywords Stroke, Clustering, Longitudinal clustering, NIHSS, Recovery ratio

> † Andrea Zanola and Antonio Luigi Bisogno have contributed equally to this work.

> *Correspondence:

Andrea Zanola

> andrea.zanola@studenti.unipd.it

> 1 Department of Neuroscience, University of Padua, 35128 Padua, Italy

*[picture on PDF page 1]*

**Figure labels:**
- 2 Padua Neuroscience Center, University of Padua, 35128 Padua, Italy
- 3 Veneto Institute of Molecular Medicine, 35128 Padua, Italy
- 4 Department of Neurology, University Medical Center HamburgEppendorf, 20246 Hamburg, Germany
- 5 Information Systems Institute, University of Applied Sciences Western Switzerland (HES-SO Valais), 3960 Sierre, Switzerland
- ©  The  Author(s)  2026. Open  Access This  article  is  licensed  under  a  Creative  Commons  Attribution-NonCommercial-NoDerivatives  4.0 International License, which permits any non-commercial use, sharing, distribution and reproduction in any medium or format, as long as you give appropriate credit to the original author(s) and the source, provide a link to the Creative Commons licence, and indicate if you modified the licensed material. You do not have permission under this licence to share adapted material derived from this article or parts of it. The images or other third party material in this article are included in the article's Creative Commons licence, unless indicated otherwise in a credit line to the material. If material is not included in the article's Creative Commons licence and your intended use is not permitted by statutory regulation or exceeds the permitted use, you will need to obtain permission directly from the copyright holder. To view a copy of this licence, visit   h  t  t  p  :  /  /  c  r  e  a  t  i v  e  c o  m  m  o  n  s . o  r g  / l i c  e  n s  e s  / b  y  n  c  n  d  / 4  . 0  /.

### Introduction

Recovery  after  stroke  is  a  complex  and  multifaceted process that involves the interplay of neurological, physiological,  and  environmental  factors.  Longitudinal datasets offer a valuable opportunity to investigate recovery  trajectories  over  time  to  identify  prognostic  factors and therapeutic targets. Traditional approaches to studying stroke recovery have relied heavily on evaluating outcomes  in  acute  versus  chronic  phases.  Although  these methods yield important insights, they often fall short in capturing the heterogeneity of recovery patterns between individuals. A key concept in this domain is the categorization of patients into 'fitters' versus 'non-fitters' , based on  how  closely  their  recovery  trajectories  align  with established mathematical models [1, 2].

However, this dichotomy and related framework have notable  limitations.  First,  from  a  methodological  perspective, some authors [3, 4], have raised concerns about the  issue  of  mathematical  coupling,  since  proportional recovery is calculated based on acute versus acute minus chronic scores, which inherently links the two variables. Second, widely described in recent literature [5], the ceiling  effect  is  present  in  commonly  used  clinical  scales. Essentially, this reflects a reduced sensitivity to the variability  currently  observed,  implying  that  there  may  be additional variability that remains undetected. This leads to the possibility that unexplained variability is underestimated [3]. Another major concern, from a physiological  standpoint,  is  that  this  theoretical  framework  has been interpreted to suggest that normal recovery entails regaining  approximately  70%  of  the  initial  deficit.  Such an interpretation risks oversimplifying the complex and individualized mechanisms  of  stroke  recovery.  Most importantly,  this  proportional  recovery  has  often  been interpreted as ground truth and, in certain cases, can be considered  a  valuable  therapeutic  target  to  obtain  [6]. Unfortunately, strong neurophysiological evidence in this regard is still lacking, and most authors have focused on specific deficits and clinical scales (i.e. Fugl Meyer [7] and motor deficits). The literature reflects a lively debate, with some studies arguing for the utility of the 'fitters' versus 'non-fitters'  categorization  and  others  highlighting  its constraints and potential biases [4, 8-10].

In  light  of  these  challenges,  the  present  study  aims to  provide  a  complementary  approach  to  describe  the recovery of stroke patients by using unsupervised techniques. Classical methodologies are focused on the statistical  evaluation  of  the  goodness-of-fit  of  a  model  for the whole population, assessing how one or more independent variables describe one or more dependent ones (e.g.,  how  acute  score  describes  the  chronic  one).  Clustering,  one  of  the  main  unsupervised  techniques,  is particularly  effective  in  finding  groups  of  subjects,  i.e. phenotypes, within the analyzed population. Specifically, while statistical techniques focus primarily on correlation between variables, clustering instead focuses on grouping subjects  based  on  their  similarity  to  one  another.  From this  perspective,  clustering  can  be  seen  as  an  analysis of  the  'subject  correlation'  representing  a  complementary,  but  opposite,  approach  to  the  conventional  analysis of feature correlation [11, 12]. As mentioned in Yang et  al.  [13],  clustering  is  one  of  the  most  useful  methods for  analyzing  similarities  between  patients  for  precision medicine.  It  groups  patients  into  subsets  that  are  clinically  meaningful and can be used for a variety of tasks, such as policy making and personalized therapies. Kim et al. [14] stresses that finding similar clusters among stroke patients  can  be  helpful  from  a  medical  perspective,  as it can lead to the discovery of new patterns and ways to manage stroke more effectively.

In  this  work,  we  apply  clustering  algorithms  tailored for  biomedical  data  analysis  [11]  to  the  recovery  ratio ( RR ) [15, 16] of patients, based on the National Institute of  Health  Stroke  Scale  (NIHSS) [17],  in  a  large  longitudinal sample of wake-up [18] stroke patients. The recovery ratio used for clustering is calculated using the total NIHSS scores measured in the subacute phase (22-36 h) and 90 days (i.e. (acute score-chronic score)/acute score, see  Eq.  1).  This  approach  presents  several  advantages over  the  existing  methods.  First,  clustering  enables  the identification  of  heterogeneous  recovery  patterns  in  a fully  data-driven  manner,  without  assuming  a  specific underlying  recovery  model.  Second,  because  clustering does not rely on regression relationships between acute and chronic scores, it mitigates concerns related to mathematical  coupling  that  affect  traditional  proportionalrecovery  analyses.  Beyond  these  strengths,  we  further evaluate  the  approach  by  testing  established  prognostic markers  of  wake-up  stroke  recovery  as  external  validation  features,  providing  insight  into  the  biological  and clinical relevance of the clusters. Finally, we demonstrate a  potential  clinical  application  by  showing  that  early impairment  and  early  recovery  measures  can  assist  in predicting cluster membership, highlighting the value of our framework for early patient stratification.

### Methods

### Dataset

WAKE-UP [18] is  an  investigator-initiated,  multicenter, randomized, double-blind, placebo-controlled clinical trial  involving  stroke  patients  with  an  unknown time of onset. Patients were randomly assigned to receive intravenous  alteplase  (rtPA)  or  placebo.  The  study  was  registered  under  the  identifier  NCT01525290.  The  dataset includes 503 patients, with NIHSS [17] scores measured at four time points: onset, 22-36 h, 7 days, and 90 days.

For  the  purposes  of  this  study,  patients  with  a  Levelof-Consciousness  Vigilance  (LOC-V)  score  of  zero  and complete  NIHSS  data  at  all  four  time  points  (no  missing values) were selected. Patients were further selected based on stroke severity, as measured by the total NIHSS score  at  onset.  Only  patients  with  a  total  NIHSS  score greater than 4 (moderate stroke severity) were included; patients with a total NIHSS score of zero at 22-36 h after the event were further excluded from the analysis. These selection  criteria  were  designed  to  reduce  the  inherent ceiling  effect  of  the  NIHSS  and  focus  on  patients  with persistent deficits. In practice this reduces the number of subjects living at the origin of the plane in Fig. 1, where a proper recovery ratio is not defined. In the supplementary material Sect. 1 a summary schema of the inclusion criteria and the consequent effect on the size of the population is reported.

For  each  subject,  general  demographic  information (age,  sex  and  treatment  group),  lesion  characteristics (lesion  side,  lesion  volume,  large  vessel  occlusion  and lacunes),  the  90-day  modified  Rankin  Scale  (mRS)  [19], the  Heidelberg  hemorrhage  classification  [20],  and  the NIHSS with all 15 sub-items are available. The mRS scale assesses  disability  and  dependence  after  a  stroke,  while the Heidelberg classification categorizes intracranial hemorrhages following ischemic stroke.

### Fitters versus non-fitters calculation

The  chronic  and  sub-acute  NIHSS  scores  were  analyzed  to  evaluate  proportional  recovery.  The  proportional  recovery  rule  (PRR)  was  modeled  by  fitting  a linear regression model where the change in score (subacute  minus  chronic)  was  the  dependent  variable  and the  sub-acute  score  was  the  independent  variable.  The intercept of the model was constrained to zero; the medical  and  statistical  reasons  behind  can  be  found  in  the supplementary material Sect. 2. The fitted model is displayed in Fig. 1, Panel B, with the 95% confidence interval  (CI)  shown  in  gray  and  the  70%  prediction  interval (PI) in light blue. Both intervals were calculated following  Howell  [21],  2007;  further  methodological  details are provided in the supplementary material, Sect 3. The prediction interval was used to classify participants into 'fitters' and 'non-fitters' . Subjects falling within the 70% PI were labeled as fitters (marked with circles, ◦ ),  while those outside were considered non-fitters (marked with crosses, × ).

However, the distinction between 'fitters' versus 'nonfitters'  (or  outliers)  is  far  from  being  unique.  Different techniques dichotomize the population in different ways, highlighting  different  aspects  of  the  data.  An  notable effort  has  been  made  to  compare  different  techniques in  Kundert  et  al.  [5],  2019.  In  order  to  briefly  review and compare these methods, they have been applied to the  population  under  study.  Seven  methods  to  define 'non-fitters' or outliers have been used and reported in Fig. 2; methodological details can be found in the supplementary material Sect. 4. The distribution of the recovery ratio for the entire population is also reported in the same figure.

*[picture on PDF page 3]*

### Recovery ratio

A  recovery  ratio  index  ( RR )  of  the  form  (acute  scorechronic score)/acute score, was used to study the degree of  recovery,  as  described  in  previous  work  [15,  16]. Let's denote as S ,  a  score or a measure of choice, aimed at  quantifying  the  impairment;  then  the  recovery  ratio index is defined as

RR = S t 1 -S t 0 ¯ S CTL -S t 0 = 1 -S t 1 S t 0 (1)

In  Eq.  1, S t 0 represents  the  sub-acute  score  measured at  an  initial  time  point t 0 ,  while S t 1 represents  the chronic score measured at a later time point t 1 . The term ¯ S CTL denotes  the  average  score  for  the  control  population.  In  Ramsey et al., 2017, the RR is  computed relative to the mean of a control population, since pre-event

(pre-morbid) scores are unavailable and healthy controls also show variability. When considering the total NIHSS as the score S however, ¯ S CTL equals zero, since healthy individuals have a total NIHSS of zero, which simplifies the  formula.  This  formula  applies  only  when  the  subacute  score  is  greater  than  zero,  i.e.,  only  for  impaired patients.  We  used  the  recovery  ratio  based  on  the  total NIHSS  as  most  patients  showed  neurological  impairment in only a limited number of subscales. Since some patients  exhibit  a  worse  condition  at  the  chronic  time point  than  at  the  sub-acute  stage  (deterioration),  the recovery  ratio  can  be  negative  in  these  cases.  For  the selected  sample  of  201  subjects,  the  average  recovery ratio is ¯ RR negative = 0 . 58 ± 0 . 67 .  Recovery ratios below zero  were  set  to  zero,  and  patients  showing  no  spontaneous  post-stroke  recovery  or  worsening  were  treated equally in the analysis. With this convention, the average recovery ratio becomes ¯ RR all = 0 . 65 ± 0 . 31 .

### Clustering

Clustering is a popular unsupervised technique, particularly useful in the identification of phenotypes [14], which can  be  effectively  used  to  find  groups  of  patients  with common recovery. The following procedure was applied to cluster the data according to the recovery ratio.

*[picture on PDF page 4]*

- The total NIHSS score at 22-36 h (sub-acute score) and the total NIHSS score at 90 days (chronic score) are used to calculate the recovery ratio ( RR ) for each subject, as defined in Eq. 1.
- The distance between subjects is calculated using the Manhattan distance on their recovery ratios. Between two subjects i and j , the distance is d ij = | RR i -RR j | . Distances are divided with respect to the maximum value found in the dataset.
- The matrix D ( ij ) = d ij is obtained from the pairwise distances between patients. After that, the similarity matrix ( W = ⊮ -D -I ) is calculated and used as input for the clustering algorithm.
- The application of the Repeated Spectral Clustering (RSC) [11] algorithm to the similarity matrix W allows the identification of groups of patients with similar recovery ratios.

The RSC algorithm is a blend of spectral clustering [22], known to work well with similarities matrices representing  graphs,  and  consensus  clustering  [23],  known  to  be powerful  since  it  allows  to  deal  with  the  variability  of results  that  stem  from  random  initializations.  In  brief, RSC takes the matrix W as input to the spectral clustering  procedure. Instead of running k -means just once, it is performed N times to account for randomness in centroid initialization. Across these N iterations, the number of  times  two  patients  are  assigned  to  the  same  cluster is  recorded.  The  more  frequently  two  subjects  are  clustered together, the stronger the evidence that they should remain in the same cluster in the final assignment. This differs  from  the  practice  of  calculating  the  average  centroids  over  the N runs.  The  final  cluster  assignment  is based  on  the  co-occurrence  matrix C ,  where  each  element C ij represents the number of times subjects i and j were clustered together across all runs. For a complete description of the algorithm, including technical details and its application to NIHSS scores, refer to Tshimanga et al. [11], 2025.

The optimal number of clusters is determined by calculating  the  maximum spectral gap for different cluster configurations (i.e. different k )  [11].  The  elbow criterion is a simple and effective way to find the optimal number of  clusters.  In  particular,  for k = 6 ,  the  maximum spectral  gap  is  at  the  end  of  a  high  plateau,  indicating  wellseparated  groups,  while  for k = 7 ,  it  decreases  sharply, indicating  subjects  that  are  worst  separated  in  groups. Thus, k = 6 is chosen as the optimal number of clusters. For more details, see the supplementary material Sect. 5.

The clustering algorithm uses the recovery ratio, which is  derived  from  the  total  NIHSS  at  two  distinct  time points. The total NIHSS constitutes the aggregate of the 15  individual  items  that  comprise  the  scale.  All  other features,  including  general  subject  information,  lesion information,  90-day  mRS,  and  the  Heidelberg  hemorrhage  classification,  were  excluded  from  the  clustering process.  Instead,  these  features  were  used  as  validation features to characterize the resulting clusters and assess differences  between  them.  The  numerical  and  ordinal features  between  the  six  groups  have  been  compared with  the  Kruskal-Wallis  [24]  test  as  omnibus,  and  then the Mann-Whiteny U [25] as post hoc for pairwise comparisons. Boolean or categorical features have been compared between the six groups with the χ 2 independence test [26] as omnibus and post hoc for pairwise comparisons. The p -values of the omnibus tests, as well as those of the post hoc test, were corrected for multiple comparisons using the FDR Benjamini-Hochberg correction [27]. The statistics used in this work to evaluate the effect size of  the  aforementioned  tests  are  reported  in  the  supplementary material, Sect. 6.

### Chronic disability and early recovery

To  explore  the  potential  clinical  utility  of  the  identified clusters,  we  investigated  whether  early  impairment  and early  recovery  measures  could  assist  in  predicting  cluster  membership.  The  early  recovery  ratio,  calculated between 22-36 h and 7 days as described in Eq. 1, was used for this purpose. These values are routinely obtainable  during  the  acute  hospitalization  period,  making them clinically practical indicators. The 90-day mRS was dichotomized  into  two  groups:  scores ≤ 2 ,  and  scores greater than 2. This threshold is clinically relevant, as an mRS score of 2 indicates a mild disability that does not interfere  with  daily  activities.  To  examine  the  relationship  between  early  recovery  and  long-term  outcomes, we  compared  the  number  of  subjects  with  mRS  scores greater than 2 versus those with scores of 2 or less across different recovery intervals. The 95% confidence intervals for these proportions were estimated using binomial statistics and are shown in Fig. 5, Panel A. Panel C reports the same analysis, with mRS presented as ordinal intervals  rather  than  dichotomized  values.  Additionally,  the percentage  of  subjects  in  each  cluster  across  recovery intervals is presented in Fig. 5, Panel B.

### Results

### Clinical sample

As  a  result  of  the  adopted  inclusion  criteria,  the  final analysis focused on 201 patients who were still impaired at 22-36 h (total NIHSS greater than zero). None of the 201  subjects  in  the  selected  cohort  had  an  mRS  score of  6  (death).  Demographics,  risk  factors,  together  with clinical characteristics are summarized in Table 1. A χ 2 independence test  did  not  reveal  statistically  significant differences  in  the  distribution  of  male  and  female  participants  between  the  treated  and  non-treated  groups ( χ 2 (1 , 201) = 0 . 44 , p = 0 . 51 ).  Moreover,  there  are  no The table reports demographic information (age, gender), lesion information (side and volume) and risk factors; moreover it is reported also the mRS at 90 days,  the  total  NIHSS  score  at  the  four  visits  and  the  percentage  of  treated patients over the investigated population significant  differences  in  terms  of  median  age  between the  four  groups,  as  assessed  by  the  Kruskal-Willis  test ( H (3) = 3 . 53 , p = 0 . 32) .  For  this  work,  a  significance level of α = 0 . 01 was chosen.

***Table 1 Demographics, risk factors and clinical characteristics***

| Stroke Population ( n = 201 ) | Stroke Population ( n = 201 ) | Stroke Population ( n = 201 ) |
|---|---|---|
| Age (years) | Mean ± SD | 65.4 ± 11.2 |
| Gender | Male | 59% |
|   | Female | 41% |
| Lesion Side | Right | 37% (75) |
|   | Left | 60% (121) |
|   | Both | 3% (5) |
| Lesion Volume (mL) | Mean ± SD | 8.3 ± 12.1 |
| Risk Factors | Arterial Hypertension | 49% (98) |
|   | Atrial Fibrillation | 15% (30) |
|   | Transient Ischemic Attack | 2% (5) |
|   | Previous Ischemic Stroke | 12% (25) |
|   | Hypercholesterolemia | 38% (74) |
|   | Diabetes mellitus type II | 18% (36) |
| mRS at 90 days | Mean ± SD | 2.0 ± 1.2 |
| NIHSS at onset | Mean ± SD | 8.9 ± 4.0 |
| NIHSS at 22/36 h | Mean ± SD | 6.5 ± 5.1 |
| NIHSS at 7 days | Mean ± SD | 5.1 ± 4.8 |
| NIHSS at 90 days | Mean ± SD | 2.8 ± 3.4 |
| Revascularization Treatment | rTPA | 47% (94) |
|   | None | 53% (107) |

Regarding the lesion side, among the 201 subjects, 121 (60%) had left side lesions, 75 (37%) had right side lesions, and 5 (3%) had bilateral lesions. The average lesion volume, measured at hospital admission using apparent diffusion  coefficient  MRI  maps,  was 8 . 3 ± 12 . 1 mL  (mean ± standard deviation). The distribution of cardiovascular risk  factors  and  the  clinical  characteristics  for  the  201 selected subjects is also reported.

### Fitters versus non-fitters calculation

The chronic and sub-acute scores were strongly correlated (Fig.  1,  Panel  A;  Spearman's ρ s (201) = 0 . 73 , p < 0 . 001 ), consistent with previous findings [28]. Panel B of Fig. 1 shows the fitted PRR model (dashed black line), together with  the  70%  and  95%  intervals.  Approximately  70%  of participants  fell  within  the  prediction  interval,  yielding an  average  recovery  ratio  of ¯ RRfi tters = 0 . 69 ± 0 . 27 ,  in line with established literature.

Panel  B  also  highlights  a  clear  ceiling  effect:  a  concentration  of  observations  approaching  the  maximal recovery limit (100%, green line), which compresses the observed change for subjects with low sub-acute impairment and can inflate apparent proportionality. Many subjects near the scale upper bound can bias both the slope estimate  and  the  classification  of  fitters/non-fitters;  the statistical  implications  are  discussed  in  the  supplementary material, Sect. 2.

The dichotomization into 'fitters' and 'non-fitters' has been proved to be highly method-dependent. As shown in  Fig.  2,  the  various  methods  led  to  differing  estimates of  the  average  recovery  ratio,  illustrating  how  patients may  be  classified  differently  depending  on  the  chosen approach. Moreover, the recovery ratio distribution deviates  from  normality,  indicating  that  the  PRR  does  not represent the typical amount of recovery in this cohort.

The  variability  in  the  average  recovery  ratios  arises from  the  different  criteria  and  algorithms  used  across methods.  Classifying  the  same  patient  as  a  'fitter'  or a  'non-fitter'  depending  on  the  method  highlights  the inherent limitations of this dichotomization. In addition, Fig. 2 shows that the proportional recovery rule does not represent  the  typical  amount  of  recovery,  i.e  the  recovery ratio is not normally distributed. This motivates the transition toward a more nuanced, data-driven approach: clustering.

### Clustering recovery ratio

The  repeated  spectral  clustering  (RSC)  algorithm,  as described  in  Sect.  2,  uses  exclusively  the  recovery  ratio defined  in  Eq.  1.  This  variable  is  reported  against  the total  NIHSS  at  22-36  h  (sub-acute)  in  Panel  A  of  Fig. 3.  Although  clustering  is  performed  on  the  similarity matrix W ,  as  described  in  Sect.  Clustering,  the  visible effect of the algorithm is horizontal separation between subjects.  This  allows  to  have  clusters  with  a  defined recovery  ratio  with  low  variation.  For  example,  cluster C 0 ,  which  contains  all  subjects  with  a  perfect  recovery ratio of 100%, has a null standard deviation; C 5 instead, is  the  cluster  with the worst mean recovery ratio which is  close  to  1%.  Within  this  group,  there  are  all  subjects  with  a  chronic  score  worse  than  sub-acute  one. At  the  population  level,  the  sub-acute  score  is  significantly but moderately associated with the recovery ratio ( ρ s (201) = -0 . 34 , p < 0 . 001) .

The  bottom  part  of  Fig.  3  illustrates  the  difference between  how  patients  are  grouped  using  a  clustering approach (Panel  B)  versus  how  they  are  divided  in  'fitters'  and  'non-fitters'  using  the  traditional  statistical method (Panel C). Interestingly, cluster C 3 closely follows the fitted linear model, shown by the black dashed line.

Panel  D  of  Fig.  3  shows  the  proportional  recovery rules  obtained  fitting  the  subjects  for  each  cluster.  As reported in the legend, there is a strict  correspondence between the average RR of  each cluster and the angular coefficients  of  these  lines.  The  70%  prediction  interval is  reported  for  every  fitted  line.  Looking  at  the  prediction intervals of each cluster, these models discriminate subjects  at  one  standard  deviation,  when  the  sub-acute NIHSS  score  is  greater  than  six.  The  cluster C 5 (in brown) overlaps with the cluster C 4 (in violet), probably due to the few subjects assigned to the first (19), and consequently a broad prediction interval. Moreover, cluster C 5 is clearly associated with people who actually become more  impaired  at  90  days  compared  to  22-36  h  (the intercept is - 1.9). Only for the cluster C 5 , a linear model with the intercept is significantly better than one without ( F (1 , 17) = 9 . 08 , p < . 01 , f 2 = 0 . 53) .

*[picture on PDF page 7]*

**Figure labels:**
- ρs(201) = −. 34, p < .001
- 70% Prediction Interval
- 20
- 00
- y = − 1.62x + 75.19
- C₀ : y = 1.0x
- 95% Cl
- 18
- C1 : y = 0.8x
- 16
- C₂:y=0.7x
- RR=82%
- C₃:y= 0.5x
- RR=100%
- RR=66%
- 80
- e
- (4-22SSHIN -
- 14
- C4 : y = 0.2x
- C5:y= 0.2x−1.9
- 12
- IC2
- 10
- RR=49%
- 60
- 8
- C3
- 0aPSSHIN)
- 6
- RR=24%
- 40
- 4
- 2
- RR=1%
- 0
- 1
- -2
- -4
- (D)
- JC5
- (A)
- -6
- -8
- 5
- 15
- 22
- 24
- NIHSS22-36h
- ρs(201) =.73, p <.001
- y = 0.54x
- C0: 54 subj.
- 70% PI
- C1: 34 subj.
- C2: 40 subj.
- Fitters
- C3: 33 subj.
- ×
- Non-Fitters
- 100% recovery
- 70% recovery
- x
- C4:21 subj.
- C5: 19 subj.
- - Z2SSHIN — 06SSHIN)-
- +
- 0% recovery
- N ° subjects
- (B)
- (C)

In  conclusions,  while  the  PRR  gives  a  methodological way  to  identify  'fitters'  versus  'non-fitters' ,  the  clustering-based  procedure  gives  rise  to  a  data-driven  family of  groups,  sharing  similar  recovery.  As  a  consequence, subjects are not distinguished anymore between 'fitters' versus 'non-fitters' , but rather between levels of recovery.

In summary, C 0 (blue) has perfect recovery, C 1 (orange) has above average recovery, C 2 (green) and C 3 (red) have average  recovery  (in  line  with  the  expectations  of  the PRR), C 4 (violet) has below average recovery, and finally C 5 (brown) has no recovery.

### Differences between clusters

The  clustering  algorithm  uses  only  the  recovery  ratio, which is an efficient way to group patients who recover similarly  together.  Concerning  the  other  features  that have not been used by the algorithm, Fig. 4 gives a useful insight.

6

*[picture on PDF page 8]*

**Figure labels:**
- ρs(201) = . 40, ρ < . 001
- Lesión Side
- 00
- y = 0.9x + 2.7
- (A)
- ●
- (B)
- GG
- 30
- 95% Cl
- 80
- 25
- 20
- 60
- sqns
- 15
- N
- 40
- 8
- 10
- 0
- 5
- O
- NIHSS22-36h
- left
- right
- both
- ρs(201) = − .56, ρ < .001
- (C)
- 100
- CO
- y = − 13.3x + 90.9
- 2-36h vs day90
- N ° subjects
- 2
- JC2
- e
- 16
- 3
- 22-
- RR%
- C4
- non treated
- C5
- (D)
- rtPA treated
- C0
- C1
- C2
- C
- 1
- 4

Panel  A  of  Fig.  4  shows  the  linear  relation  between the lesion  volume  (expressed  in  mL)  and  the  subacute score; points are colored by cluster assignment. The  two  variables are significantly correlated ( ρ s (201) = 0 . 40 , p < 0 . 001) ,  but  there  is  no  significant association  between  lesion  volumes  and  clusters  (Kruskal-Willis test, H (5) = 7 , p = 0 . 22) .  In  other  words, there is no significant relation between lesion volume at admission and recovery measured at 90 days.

Panel B of Fig. 4 represents the distribution of the lesion side (left, right, bilateral) in the obtained clusters. The clusters obtained with RSC show significant differences in lesion laterality ( χ 2 (5 , 201) = 25 . 6 , p = 0 . 004 , V = 0 . 25) . In particular C 0 includes  more  right  lesions  than  expected, while C 3 more  left lesions (pairwise  post  hoc  test, χ 2 (1 , 87) = 14 . 8 , p = 0 . 009 , V = 0 . 41) . In other words, the sides of the lesions are not randomly divided by clusters.  Subjects  with  perfect  recovery ( C 0 ) have  significantly  more  right  than  left  lesions;  conversely,  patients in clusters with average recovery ( C 3 ) have significantly more left than right lesions.

In  Fig.  4  Panel  C,  the  recovery  ratio  distribution  is reported  for  each  group,  where  patients  have  been separated  between  treated  with  rtPA  (magenta)  and non-treated  (blue).  As  can  be  seen  in  Fig.  4,  there  are no significant differences between the distributions of  the  two  groups  for  each  cluster,  and  there  is  no  significant association between treatment and clusters ( χ 2 (5 , 201) = 5 . 7 , p = 0 . 33) . Therefore, while rtPA improves NIHSS and mRS scores acutely and at 3 months (see  supplementary  material  Sect.  7,  Fig.  3),  data  show that  patients  treated  with  rtPA  have  the  same  recovery trajectories  than  patients  non  treated  with  rtPA  after the first  24  h  from  the  event.  Finally,  no  significant  differences were found between the clusters with respect to the Heidelberg hemorrhagic classification.

The recovery ratio and the 90 days mRS are significantly correlated ( ρ s (201) = 0 . 56 , p < 0 . 001) ,  and  there  is  an association between the RSC clusters and motor abilities at 90 days (Kruskal-Willis' test, H (5) = 74 . 3 , p < 0 . 001 , η 2 = 0 . 36) .  Post  hoc  pairwise  comparisons,  conducted using  the  Mann-Whitney  U  test,  reveal  significant  differences  between C 0 and  all  other  clusters, C 1 versus C 3 and C 4 ,  and C 2 versus C 4 .  Finally, no cardiovascular risk  factor  is  associated  with  a  specific  cluster,  and  we found no significant differences between clusters, both at α = 0 . 01 .

### Prediction of long-term recovery by early recovery ratio

In  addition,  we  evaluated  whether  cluster  identity  and overall patient outcome  were associated with early recovery patterns. This aspect is clinically relevant, as  it  can  provide  prognostic  information  for  patients and caregivers during hospitalization. The relationship  between  disability  at  90  days  and  the  early  recovery  ratio-calculated  between  22-36  h  and  7  days-was examined  across  the  identified  clusters.  The  results  are reported in Fig. 5.

In  Panel  A  and  in  Panel  C,  it  can  be  observed  that  a recovery  ratio  between  -  0.1  and  0.3  does  not  provide sufficient information to predict whether chronic disability  will  be  severe  or  not  (random  chance  level).  In  contrast, an early recovery ratio greater than 0.3 substantially increases  the  probability  of  achieving  a  mild  disability. Panel  B,  shows  the  same  result  from  a  clustering  point of view. A recovery ratio between - 0.1 and 0.3 does not provide sufficient information to determine which recovery cluster the patient will belong to. The probability of being assigned to a group characterized by above average recovery ( C 0 , C 1 or C 2 )  is  56% and 67% for the second and third ranges, and increases to 72% and 97% for the last  two.  The  probability  of  being  assigned  to  a  group characterized by below average recovery ( C 4 or C 5 ) instead follows the opposite trend.

### Discussion

In this work, we applied an unsupervised learning technique to the study of stroke recovery. Repeated spectral clustering (RSC), a recently developed procedure to tailor biomedical data heterogeneity [11], was applied to the recovery ratio  based  on  total  NIHSS  in  a  large  longitudinal  sample  of  stroke  patients.  This  approach  grouped patients into distinct recovery clusters providing several clinical implications.

### Recovery ratio and clustering

One of the main criticisms of  the  PRR  is  mathematical coupling, i.e. the fact that recovery is inherently dependent on the initial impairment. Essentially, from a mathematical  point  of  view,  fitting  a  linear  model  means establishing a linear relationship between an independent variable (the sub-acute score) and a dependent variable, the change (sub-acute score minus chronic score), which inherently  includes  the  independent  variable.  This  has caused much debate in the medical community, as evidenced  by  the  extensive  literature  on  the  subject.  This methodology  has  been  theoretically  criticized  by  some and supported by others.

The amount of recovery can be quantified as an absolute change, as previously mentioned, or in relative terms such as the recovery ratio index ( RR ).  The  definition  of recovery  ratio,  in  the  framework  of  PRR,  is  induced  by the variables chosen on the horizontal and vertical axes and by the linearity of the model. Instead, with clustering,  the  definition  of  recovery  ratio  could  be  carefully chosen a priori and not forced to be of the shape of Eq. 1; the quantities of interest to quantify the recovery can be even nonlinearly correlated. Although it is true that RR defined  by  the  PRR  framework  and  used  for  this  work has in its definition the ratio between chronic and acute scores, it is not calculated from a correlation or from the fit of a model; it simply represents a patient-specific estimate  of  recovery.  In  addition,  this  choice  establishes  a strong link between the traditional statistical framework and the clustering results obtained in this work.

*[picture on PDF page 10]*

Once the linear model is fitted, the identification of 'fitters' versus 'non-fitters' may prove to be a great source of controversy. As shown in Fig. 2, depending on the way patients  are  selected,  different  average  recovery  ratios can be estimated because different patients are included in  the  estimate.  This  shows  how  the  same  theoretical framework can give subjective outcomes. Clustering the recovery ratio instead is an effective way both to group patients  with  similar  recovery  and  to  incorporate  time into a clustering algorithm. The six clusters found exhibit different  levels  of  recovery,  with  patients  described  by their own PRR as indicated by Fig. 3, Panel D. The prediction intervals of these models are narrow and well separate  subjects  into  clusters.  This  clustering  scheme  may provide a novel methodology capable of fully exploiting longitudinal ordinal data, such as those presented in this paper.

### Clinical implications

From a clinical perspective, the described dataset  includes  a  large  sample  of  stroke  patients  with  an unknown time of onset. Wake-up strokes generally show poorer  outcomes  at  three  months  than  known  onset strokes [29]. Although several studies have explored the relationship  between  this  stroke  category  and  revascularization  therapies  [30,  31],  leading  to  progressively expanded  treatment  indications,  research  on  general prognostic markers for recovery remains limited. In this context, we were able to provide a fine-grained description  of  this  population  over  time.  Specifically,  in  most patients, NIHSS scores progressively declined in a nonproportional manner (see from Panel D to Panel I, Fig. 5 in the supplementary material, Sect. 8). In other words, most of the patients did not recover a fixed proportional amount  of  their  initial  deficit  (see  Fig.  2).  On  the  contrary,  the  identified  clusters  included  patients  with  distinct  trajectories,  such  as  additive,  proportional,  or  no improvement  profiles,  while  still  capturing  a  consistent amount  of  recovery  during  the  first  three  months  (i.e., the  critical  period  for  spontaneous  recovery)  [32].  This becomes  particularly  evident  when  further  differentiating between severity categories for moderate and severe patient trajectories (see from Panel A to Panel C, Fig. 5 in the supplementary material, Sect. 5).

The  identified  clusters  are  likely  to  reflect  underlying neurophysiological  differences  that  influence  recovery trajectories.  To  evaluate  this,  we  tested  available  prognostic  factors  (i.e.  well-established  post  stroke  recovery prognostic biomarkers) as validation features of the proposed  approach.  No  significant  differences  in  recovery ratio ( RR )  (i.e.  from  22-36 h to 90 days) were observed between  patients  who  received  rtPA  and  those  who received a placebo. This finding is consistent with expectations, as RR calculation spans from 22-36 h to 90 days post-stroke, whereas rtPA effects mainly affects the initial hours after the event [33]. Figures 3 and 4 in the supplementary  material  show  improved  early  recovery  (from onset  to  22-36  h)  after  acute  revascularization  treatment and no difference in the subsequent, spontaneous recovery from 22-36 h to 90 days. A positive correlation between stroke volume and NIHSS at 22-36 h supports the expected relationship between initial stroke severity and early  impairment  [34,  35].  However,  stroke  volume did not correlate with RR (and thus with cluster assignment), indicating that lesion size alone does not predict long-term  recovery  patterns.  This  finding  corroborates existing evidence that volume explains only a limited portion of outcomes, primarily related to initial impairment also  following  wake  up  stroke  [36-38].  A  negative  correlation was observed between the mRS scores and both the RR and  recovery  groups,  suggesting  that  patients with  worse  functional  outcomes  tend  to  exhibit  poorer recovery trajectories. Worse recovery was also observed in patients with lesions of the left hemisphere. While this is consistent with some previous studies reporting worse functional  outcomes  for  left-sided  strokes  in  knownonset stroke [39], several studies have shown right hemisphere lesions also significantly affect recovery, especially reducing  patients'  compliance  to  rehabilitation  [40,  41]. Our results may, therefore, be explained by the NIHSS's well-established increased sensitivity to left-sided strokes and  should  be  validated  using  additional  clinical  scales in  specific  behavioral  domains  [42,  43].  Interestingly, no  cluster  presented  a  significantly  higher  frequency of  patients  with  hemorrhagic  transformation  following rtPA. This suggests a relatively small impact of this feature on long-term disability of wake-up strokes undergoing thrombolytic treatment. These results underscore the substantial benefits of rtPA over its risks in this typology of  stroke.  Future  work should evaluate the role of additional prognostic features of wake-up strokes, including vessel  occlusion  (i.e.  anterior  versus  posterior  circulation), comorbidites (i.e. hypertension as well as other cardiovascular risk factors) and neurophysiology indices (i.e. presence/absence  of  motor  evoked  potentials)  on  final disability,  using  a  similar  framework.  Finally,  patients who achieved an RR of  0.3  or  higher  within  two  weeks post-hospitalization consistently clustered into favorable outcome groups, with approximately 90% falling  within clusters C 0 , C 1 , C 2 ,  and C 3 .  A  similar  pattern  emerged when  considering  mRS  scores  dichotomized  for  good (mRS ≤ 2) and poor (mRS > 2) outcomes. These results provide a valuable stratification, readily available during hospitalization  (i.e.  the  first  week  after  the  event)  with several prognostic implications for the patient and caregivers. In addition, these findings highlight the potential clinical  application  of  this  clustering  approach,  demonstrating  its  scalability  across  large  datasets.  Specifically, this methodology draws a useful parallel to how the mRS is employed in clinical trials for rtPA and thrombectomy. Just  as  these  trials  aim  to  identify  an  increased  proportion  of  patients  achieving  favorable  mRS  outcomes, future  interventions  on  neuroplasticity  and  functional re-organization after stroke could focus on shifting more patients toward the most favorable recovery clusters.

### Limitations and future directions

Regarding the limitations of this study, a potential caveat is that for patients with an NIHSS score below 6 at  22-36 h, the six linear models and their corresponding  prediction  intervals  do  not  adequately  discriminate  between  individuals.  This  could  somewhat  limit the analysis by questioning the validity of these clusters and the separability between them. This is related to the 'ceiling' effect. In fact, in the statistical model shown in Fig. 3 Panel C, the prediction interval (in light blue) for a NIHSS less than 6 hardly discriminates points between 'fitters' and 'non-fitters' , questioning the validity of this subdivision  for  low-impaired  subjects.  Other  clinical measures could be used to discriminate subjects even in this area of low impairment. Specifically, while the clustering approach was limited to only one variable (i.e. the recovery ratio), this was calculated from two variables at different times. Although the use of one variable could be criticized, it is worth underlining that clustering is not a dimensionality  reduction  technique.  Future  work  could exploit  the  combination  of  additional  variables  for  the purpose  of  phenotyping  patients;  nonetheless,  clustering the recovery ratio can be seen as a clever strategy to embody  time  in  a  clustering  algorithm.  The  full  deficit dynamics  at  additional  time  points  could  be  explored, enriching current knowledge about stroke recovery. Spontaneous  recovery  after  stroke  extends  well  beyond the first three months; additional data from the chronic phase  could  enable  a  more  refined  characterization  of recovery trajectories. Additional neurophysiological differences across clusters deserve further exploration. These include neuroimaging features (i.e. lesion location, lesion  induced  disconnection)  as  well  as  electro-physiological  signals  (i.e.  evoked  potentials  and  resting  state electroencephalography). Finally, it should be noted that these  results  are  limited  to  the  sample  in  analysis  and only  indirectly  account  for  several  well  described  prognostic factors (i.e. hypertension, vessel occlusion, comorbidities,  cortico-spinal  tract  integrity,  among  others). Therefore, replication in independent cohorts and evaluations using alternative clinical evaluations will be essential to validate and expand these results.

### Conclusion

This paper aims to pave the way for a new, data-driven approach to studying stroke recovery. By using unsupervised  techniques  such  as  Repeated  Spectral  Clustering, we  offer  a  more  precise  sub-division  of  patients  based on  their  recovery  trajectories.  Clustering  the  recovery ratio is an efficient way to embody time within the algorithm, while also accommodating the inherent variability in recovery across individuals. This flexible and scalable framework supports the analysis of larger, more heterogeneous  datasets  and  enables  continuous  evaluation  of neurophysiological differences between groups. Ultimately,  it  offers  insights  into  the  mechanisms  of  poststroke  recovery  that  extend  beyond  the  Proportional Recovery Rule.

### Supplementary Information

The online version contains supplementary material available at   h  t  t  p  s  :  /  /  d  o  i  .  o  r g  /  1 0  . 1  1  8 6  / s  1 2  9  8 4  0  2  5 -  0 1  8  7 2  -  w.

Supplementary file 1.

### Author contributions

A.Z. did the analysis and wrote the main manuscript. A.L.B. did the interpretation of the data and wrote the main manuscript. V.V. reviewed the main manuscript. G.T. acquired the data. B.C. acquired the data and reviewed the main manuscript. M.A. reviewed the main manuscript. M.C. did the interpretation of the data and reviewed the main manuscript. All authors reviewed and approved the submitted version of the manuscript.

### Funding

This work was supported by the STARS@UNIPD funding program of the University of Padova, Italy, through the project: MEDMAX. This project has received funding from the European Union's Horizon Europe research and innovation program under grant agreement No. 101137074 - HEREDITARY. ALB, VV and MC were supported by HORIZON-ERC-SyG (Grant No. 101071900) 'Neurological Mechanisms of Injury And Sleep-Like Cellular Dynamics (NEMESIS)'. MC was supported by HORIZON-INFRA-2022-SERV (Grant No. 101147319) 'EBRAINS 2.0: A Research Infrastructure to Advance Neuroscience and Brain Health'. MC was also supported by the Italian Ministry of Health 'Eye-movement dynamics during free viewing as biomarker for assessment of visuospatial functions and for closed-loop rehabilitation in stroke' (EYEMOVINSTROKE; RF-2019-12369300), by the Cariparo Foundation Excellence grant 2023-2024 (Agreement No. 68076; AWARENET project) and by the Ministry of University and Research, PRIN 20229Z7M8N 'Tracking the brain priors for predictive coding' .

### Data availability

No datasets were generated or analysed during the current study.

### Declarations

Ethics approval and consent to participate

Not applicable

### Consent for publication

Not applicable

### Competing interests

The authors declare no competing interests.

Received: 17 June 2025 / Accepted: 30 December 2025

### References

- Krakauer J, Marshall R. The proportional recovery rule for stroke revisited. Ann Neurol. 2015;78(6):845-7.   h  t  t  p  s  :  /  /  d  o  i  .  o  r  g  /  1 0  . 1  0  0 2  / a  n  a . 2  4  5  3  7.
- Prabhakaran S, Zarahn E, Riley C, Speizer A, Chong JY, Lazar RM, et al. Interindividual variability in the capacity for motor recovery after ischemic stroke. Neurorehabil Neural Repair. 2008;22(1):64-71.   h  t  t  p  s  :  /  /  d  o  i  .  o  r  g  /  1  0  .  1  1  7  7  /  1  5  4  5  9 6  8  3 0  7  3 0  5  3  0  2. ( PMID: 17687024 ).
- Bowman H, Bonkhoff A, Hope T, Grefkes C, Price C. Inflated estimates of proportional recovery from stroke. Stroke. 2021;52(5):1915-20.   h  t  t  p  s  :  /  /  d  o  i  .  o  r  g /  1 0  . 1  1  6 1  / S  T  R O  K  E  A  H  A . 1  2  0 . 0  3  3 0  3  1.
- Hawe RL, Scott SH, Dukelow SP. Response by hawe et al to letter regarding article, taking proportional out of stroke recovery. Stroke. 2019;50(5):126-126. h  t t  p s  : /  / d  o  i . o  r g  /  1 0  . 1  1  6 1  / S  T  R O  K  E  A  H  A . 1  1  9 . 0  2  4 7  9  4.
- Kundert R, Goldsmith J, Veerbeek JM, Krakauer JW, Luft AR. What the proportional recovery rule is (and is not): methodological and statistical considerations. Neurorehabil Neural Repair. 2019;33(11):876-87.   h  t  t  p  s  :  /  /  d  o  i  .  o  r  g  /  1  0  .  1  1 7  7  / 1  5  4 5  9  6 8  3  1 9  8  7 2  9  9  6. ( PMID: 31524062 ).
- Bonkhoff AK, Hope T, Bzdok D, Guggisberg AG, Hawe RL, Dukelow SP, et al. Bringing proportional recovery into proportion: bayesian modelling of poststroke motor impairment. Brain. 2020;143(7):2189-206.   h  t  t  p  s  :  /  /  d  o  i  .  o  r  g  /  1  0  .  1  0  9 3  / b  r a  i n  /  a w  a  a  1  4  6.
- Fugl-Meyer A, Jääskö L, Leyman I, Olsson S, Steglind S. The post-stroke hemiplegic patient. 1. a method for evaluation of physical performance. Scand J Rehabil Med. 1975;7(1):13-31.
- Hope TMH, Friston K, Price CJ, Leff AP , Rotshtein P , Bowman H. Recovery after stroke: Not so proportional after all? Brain. 2018;142(1):15-22.   h  t  t  p  s  :  /  /  d  o  i  .  o  r  g  / 1  0  . 1  0  9 3  / b  r a  i n  /  a w  y  3  0  2.
- Vliet R, Selles RW, Andrinopoulou E-R, Nijland R, Ribbers GM, Frens MA, et al. Predicting upper limb motor impairment recovery after stroke: a mixture model. Ann Neurol. 2020;87(3):383-93.   h  t  t  p  s  :  /  /  d  o  i  .  o  r  g  /  1  0  .  1  0  0  2  /  a  n  a  .  2 5  6  7  9.
- Winters C, Wegen EEH, Daffertshofer A, Kwakkel G. Generalizability of the proportional recovery model for the upper extremity after an ischemic stroke. Neurorehabil Neural Repair. 2015;29(7):614-22.   h  t  t  p  s  :  /  /  d  o  i  .  o  r  g  /  1  0  .  1  1  7  7  /  1  5  4  5 9  6  8 3  1  4 5  6  2 1  1  5. ( PMID: 25505223 ).

- Tshimanga LF, Zanola A, Facchini S, Bisogno AL, Pini L, Atzori M, et al. Behavioral clusters and lesion distributions in ischemic stroke, based on nihss similarity network. J Healthc Inform Res. 2025.   h  t  t  p  s  :  /  /  d  o  i  .  o  r  g  /  1  0  .  1  0  0  7  /  s  4  1  6  6 6  0  2  5 -  0 0  1  9 7  -  6.
- Cheng B, Chen J, Königsberg A, Mayer C, Rimmele L, Patil KR, et al. Mapping the deficit dimension structure of the national institutes of health stroke scale. EBioMedicine. 2023;87:104425.   h  t  t  p  s  :  /  /  d  o  i  .  o  r  g  /  1  0  .  1  0  1  6  /  j . e  b  i o  m  . 2  0  2 2  .  1  0 4  4  2  5.
- Yang W-C, Lai J-P , Liu Y-H, Lin Y-L, Hou H-P , Pai P-F. Using medical data and clustering techniques for a smart healthcare system. Electron. 2024;13(1):140. h  t t  p s  : /  / d  o  i . o  r g  /  1 0  . 3  3  9 0  / e  l e  c  t r  o n  i c  s 1  3  0 1  0  1  4  0.
- Kim J-T, Kim NR, Choi SH, Oh S, Park M-S, Lee S-H, et al. Neural network-based clustering model of ischemic stroke patients with a maximally distinct distribution of 1-year vascular outcomes. Sci Rep. 2022;12(1):9420.   h  t  t  p  s  :  /  /  d  o  i  .  o  r  g  / 1  0  . 1  0  3 8  / s  4 1  5  9 8  0  2  2 -  1 3  6  3 6  -  w.
- Ramsey LE, Siegel JS, Lang CE, Strube M, Shulman GL, Corbetta M. Behavioural clusters and predictors of performance during recovery from stroke. Nat Hum Behav. 2017;1(3):0038.   h  t  t  p  s  :  /  /  d  o  i  .  o  r  g  /  1  0  .  1  0  3  8  / s  4 1  5  6 2  0  1  6 -  0 0  3  8.
- Lazar RM, Minzer B, Antoniello D, Festa JR, Krakauer JW, Marshall RS. Improvement in aphasia scores after stroke is well predicted by initial severity. Stroke. 2010;41(7):1485-8.   h  t  t  p  s  :  /  /  d  o  i  . o  r g  /  1 0  . 1  1  6 1  / S  T  R O  K  E  A  H  A . 1  0  9 . 5  7  7 3  3  8.
- Chalos V, Ende NAM Lingsma HF, Mulder MJHL, Venema E, Dijkland SA, Berkhemer OA, Yoo AJ, Broderick JP , Palesch YY, Yeatts SD, Roos YBWEM, Oostenbrugge RJ, Zwam WH, Majoie CBLM, Lugt A, Roozenbeek B, Dippel DWJ, MR CLEAN Investigators* Berkhemer OA, Fransen PSS, Beumer D, Berg LA, Lingsma HF, Yoo AJ, Schonewille WJ, Vos JA, Nederkoorn PJ, Wermer MJH, Walderveen MAA, Staals J, Hofmeijer J, Oostayen JA, Nijeholt, GJL, Boiten J, Brouwer PA, Emmer BJ, Bruijn SF, Dijk LC, Kappelle LJ, Lo RH, Dijk EJ, Vries J, Kort PLM, Rooij WJJ, Berg JSP , Hasselt BAAM, Aerden LAM, Dallinga RJ, Visser MC, Bot JCJ, Vroomen PC, Eshghi O, Schreuder THCML, Heijboer RJJ, Keizer K, Tielbeek AV, Hertog HM, Gerrits DG, Berg-Vos RM, Karas GB, Steyerberg EW, Flach HZ, Marquering HA, Sprengers MES, Jenniskens SFM, Beenen LFM, Berg R, Koudstaal PJ, Zwam WH, Roos YBWEM, Lugt A, Oostenbrugge RJ, Majoie CBLM, Dippel DWJ. National institutes of health stroke scale. Stroke 2020;51(1):282-290.   h  t  t  p  s  :  /  /  d  o  i  .  o  r g  /  1 0  . 1  1  6 1  / S  T  R O  K  E  A  H  A . 1  1  9 . 0  2  6 7  9  1
- Aschman TAD, Audebert HJ, Nitschmann S. Mrt-gesteuerte thrombolyse bei schlaganfall. Der Internist. 2019;60(4):420-3.   h  t  t  p  s  :  /  /  d  o  i  .  o  r  g  /  1  0  .  1  0  0  7  /  s  0  0  1  0  8 -  0 1  8  0  5  4 4  -  9.
- Rankin J. Cerebral vascular accidents in patients over the age of 60: Ii. prognosis. Scottish Med J. 1957;2(5):200-15.   h  t  t  p  s  :  /  /  d  o  i  .  o  r  g  /  1  0  .  1  1  7  7  /  0  0  3  6 9  3  3 0  5  7  0 0  2  0 0  5  0  4. ( PMID: 13432835 ).
- Kummer R, Broderick JP, Campbell BCV, Demchuk A, Goyal M, Hill MD, et al. The heidelberg bleeding classification. Stroke. 2015;46(10):2981-6.   h  t  t  p  s  :  /  /  d  o i . o  r g  /  1 0  . 1  1  6 1  / S  T  R O  K  E  A  H  A . 1  1  5 . 0  1  0 0  4  9.
- Howell DC. Statistical Methods for Psychology. Belmont: Thomson Wadsworth; 2007.
- Luxburg U. A tutorial on spectral clustering. Stat Comput. 2007;17(4):395-416. h  t t  p s  : /  / d  o  i . o  r g  /  1 0  . 1  0  0 7  / s  1 1  2  2 2  0  0  7 -  9 0  3  3 -  z.
- Fred ALN, Jain AK. Data clustering using evidence accumulation. In: 2002 International Conference on Pattern Recognition vol. 4, 2002. pp. 276-2804.   h t  t p  s  : /  / d  o  i . o  r g  /  1 0  . 1  1  0 9  / I C  P  R  . 2  0  0 2  . 1  0  4 7  4  5  0
- Kruskal WH, Wallis WA. Use of ranks in one-criterion variance analysis. J Am Stat Assoc. 1952;47(260):583-621.   h  t  t  p  s  :  /  /  d  o  i  .  o  r  g  /  1  0  .  1  0  8  0  / 0  1  6 2  1  4 5  9  . 1  9  5 2  .  1  0 4  8  3 4  4  1.
- Mann H.B, Whitney D.R. On a test of whether one of two random variables is stochastically larger than the other. The annal math stat 1947:50-60
- Agresti A. An Introduction to Categorical Data Analysis. 2nd ed. Hoboken: Wiley; 2007.
- Benjamini Y, Hochberg Y. Controlling the false discovery rate: a practical and powerful approach to multiple testing. J Royal Stat Soc Ser B Methodol. 1995;57(1):289-300.
- Chong B, Wang A, Stinear CM. Proportional recovery after stroke: addressing concerns regarding mathematical coupling and ceiling effects. Neurorehabil
- Neural Repair. 2023;37(7):488-98.   h  t  t  p  s  :  /  /  d  o  i  .  o  r  g  /  1  0  .  1  1  7  7 /  1 5  4  5 9  6  8 3  2  3 1  1  7 7  5  9 8. ( PMID: 37269116 ).
- Hervella P , Alonso-Alonso ML, Pérez-Mato M, Rodríguez-Yáñez M, Arias-Rivas S, López-Dequidt I, et al. Surrogate biomarkers of outcome for wake-up ischemic stroke. BMC Neurol. 2022;22(1):215.   h  t  t  p  s  :  /  /  d  o  i  .  o  r  g  /  1  0  .  1  1  8  6  /  s  1  2  8  8 3  0  2  2 -  0 2  7  4 0  -  z.
- ...Schlemm L, Braemswig TB, Boutitie F, Vynckier J, Jensen M, Galinovic I, et al. WAKE-UP Investigators: cerebral microbleeds and treatment effect of intravenous thrombolysis in acute stroke. Neurology. 2022;98(3):302-14.   h  t  t  p  s  :  /  /  d  o  i  . o  r g  /  1 0  . 1  2  1 2  / W  N  L  . 0  0  0 0  0  0 0  0  0 0  0  1 3  0  5  5.
- Thomalla G, Simonsen CZ, Boutitie F, Andersen G, Berthezene Y, Cheng B, et al. Mri-guided thrombolysis for stroke with unknown time of onset. N Engl J Med. 2018;379(7):611-22.   h  t  t  p  s  :  /  /  d  o  i  .  o  r  g  /  1  0  . 1  0  5 6  / N  E  J M  o  a  1  8 0  4  3  5  5.
- Wade DT, Wood VA, Hewer RL. Recovery after stroke-the first 3 months. Neurol Neurosurg Psychiatry. 1985;48(1):7-13.   h  t  t  p  s  :  /  /  d  o  i  .  o  r  g  /  1  0  .  1  1  3  6  /  j  n  n  p  .  4 8  . 1  .  7.
- null: Tissue plasminogen activator for acute ischemic stroke. New England J Med 1995;333(24):1581-1588.   h  t  t  p  s  :  /  /  d  o  i  .  o  r  g  /  1  0  .  1  0  5  6  / N  E  J M  1  9  9  5 1  2  1 4  3  3 3  2  4 0  1
- Ghoneem A, Osborne MT, Abohashem S, Naddaf N, Patrich T, Dar T, et al. Association of socioeconomic status and infarct volume with functional outcome in patients with ischemic stroke. JAMA Netw Open. 2022;5(4):229178229178.   h  t  t  p  s  : /  / d  o  i . o  r g  /  1 0  . 1  0  0 1  / j a  m  a  n  e t  w  o  r k  o  p e  n  . 2  0  2 2  . 9  1  7  8.
- Lee K-J, Kim JY, Kang J, Kim BJ, Kim S-E, Oh H, et al. Hospital volume and mortality in acute ischemic stroke patients: Effect of adjustment for stroke severity. J Stroke Cerebrovasc Dis. 2020;29(5):104753.   h  t  t  p  s  :  /  /  d  o  i  .  o  r  g  /  1  0  .  1  0  1  6  / j . j s  t r  o k  e  c e  r e  b  r o  v  a s  d  i s  . 2  0  2 0  . 1  0  4 7  5  3.
- Rosso C, Samson Y. The ischemic penumbra: the location rather than the volume of recovery determines outcome. Curr Opin Neuro. 2014;27(1):35-41.
- Koch PJ, Rudolf LF, Schramm P , Frontzkowski L, Marburg M, Matthis C, et al. Preserved corticospinal tract revealed by acute perfusion imaging relates to better outcome after thrombectomy in stroke. Stroke. 2023;54(12):3081-9.   h  t t  p s  : /  / d  o  i . o  r g  /  1 0  . 1  1  6 1  / S  T  R O  K  E  A  H  A . 1  2  3 . 0  4  4 2  2  1.
- Schlemm E, Ingwersen T, Königsberg A, Boutitie F, Ebinger M, Endres M, et al. Preserved structural connectivity mediates the clinical effect of thrombolysis in patients with anterior-circulation stroke. Nat Commun. 2021;12(1):2590.   h  t  t p  s  : /  / d  o  i . o  r g  /  1 0  . 1  0  3 8  / s  4 1  4  6 7  0  2  1 -  2 2  7  8 6  -  w.
- Hedna VS, Bodhit AN, Ansari S, Falchook AD, Stead L, Heilman KM, et al. Hemispheric differences in ischemic stroke: Is left-hemisphere stroke more common? J Clin Neurol. 2013;9(2):97-102.   h  t  t  p  s  :  /  /  d  o  i  .  o  r  g  /  1  0  .  3  9  8  8  /  j  c  n  .  2  0  1 3  . 9  . 2  .  9  7.
- Aszalós Z, Barsi P , Vitrai J, Nagy Z. Lateralization as a factor in the prognosis of middle cerebral artery territorial infarct. Eur Neurol. 2002;48(3):141-5.   h  t  t  p  s  :  /  / d  o  i . o  r g  /  1 0  . 1  1  5 9  / 0  0  0 0  6  5 5  1  5.
- Ween JE, Alexander MP, D'Esposito M, Roberts M. Factors predictive of stroke outcome in a rehabilitation setting. Neurol. 1996;47(2):388-92.   h  t  t  p  s  :  /  /  d  o  i  .  o  r  g /  1 0  . 1  2  1 2  / W  N  L  . 4  7  . 2  . 3  8  8.
- Woo D, Broderick JP , Kothari RU, Lu M, Brott T, Lyden PD, et al. Does the national institutes of health stroke scale favor left hemisphere strokes? Stroke. 1999;30(11):2355-9.   h  t  t  p  s  :  /  /  d  o  i  .  o  r g  /  1 0  . 1  1  6 1  / 0  1  . S  T  R . 3  0  . 1  1  . 2  3  5  5.
- Fink JN, Selim MH, Kumar S, Silver B, Linfante I, Caplan LR, et al. Is the association of national institutes of health stroke scale scores and acute magnetic resonance imaging stroke volume equal for patients with right- and lefthemisphere ischemic stroke? Stroke. 2002;33(4):954-8.   h  t  t  p  s  :  /  /  d  o  i  .  o  r  g  /  1  0  .  1  1  6 1  / 0  1  . S  T  R . 0  0  0 0  0  1 3  0  6 9  . 2  4  3 0  0  .  1  D.

### Publisher's Note

Springer Nature remains neutral with regard to jurisdictional claims in published maps and institutional affiliations.