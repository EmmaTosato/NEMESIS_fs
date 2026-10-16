### The brain's 'dark energy' puzzle: How strongly is glucose metabolism linked to resting-state brain activity?

Tommaso Volpi 1,2 , Erica Silvestri 3 , Marco Aiello 4 , John J Lee 5 , Andrei G Vlassenko 5 , Manu S Goyal 5 , Maurizio Corbetta 1,6 and Alessandra Bertoldo 1,3

### Abstract

Brain glucose metabolism, which can be investigated at the macroscale level with [ 18 F]FDG PET, displays significant regional variability for reasons that remain unclear. Some of the functional drivers behind this heterogeneity may be captured by resting-state functional magnetic resonance imaging (rs-fMRI). However, the full extent to which an fMRIbased description of the brain's spontaneous activity can describe local metabolism is unknown. Here, using two multimodal datasets of healthy participants, we built a multivariable multilevel model of functional-metabolic associations, assessing multiple functional features, describing the 1) rs-fMRI signal, 2) hemodynamic response, 3) static and 4) time-varying functional connectivity, as predictors of the human brain's metabolic architecture. The full model was trained on one dataset and tested on the other to assess its reproducibility. We found that functional-metabolic spatial coupling is nonlinear and heterogeneous across the brain, and that local measures of rs-fMRI activity and synchrony are more tightly coupled to local metabolism. In the testing dataset, the degree of functional-metabolic spatial coupling was also related to peripheral metabolism. Overall, although a significant proportion of regional metabolic variability can be described by measures of spontaneous activity, additional efforts are needed to explain the remaining variance in the brain's 'dark energy'.

### Keywords

Brain glucose metabolism, spontaneous activity, functional-metabolic model, [ 18 F]FDG PET, multilevel modeling

Received 31 May 2023; Revised 5 January 2024; Accepted 11 February 2024

### Introduction

Brain glucose consumption can be assessed in vivo by [ 18 F]fluorodeoxyglucose positron emission tomography ([ 18 F]FDG PET). 1 As evidenced by [ 18 F]FDG studies, glucose metabolism displays significant regional variability in the healthy brain. The reasons behind this heterogeneity in glucose expense, however, remain largely unexplained. Crucially, most of the remarkable metabolic budget of the brain, /C24 25% of glucose use in the face of only 2% of body weight, is spent during rest, 2 with similar numbers also for cerebral blood flow ( CBF ) and oxygen consumption ( CMRO 2). This so-called 'dark energy' of the brain is thought to be largely employed for maintaining resting potentials and subthreshold synaptic transmission, 3,4 since most of the energy budget of a neuron is utilized at the level of the synapses, rather than in the neuron's body. 5 Based on these premises, regional differences in brain metabolism should be well explained by variability in spontaneous activity, which has been extensively explored with blood-oxygen-level-dependent (BOLD)

> 1 Padova Neuroscience Center, University of Padova, Padova, Italy

> 2 Department of Radiology and Biomedical Imaging, Yale University School

> of Medicine, New Haven, CT, USA

> 3 Department of Information Engineering, University of Padova, Padova, Italy

> 4 IRCCS SDN, 80143, Naples, Italy

> 5 Neuroimaging Laboratories at the Mallinckrodt Institute of Radiology,

> Washington University School of Medicine, St Louis, MO, USA

> 6 Department of Neuroscience, University of Padova, Padova, Italy

### Corresponding authors:

Tommaso Volpi, 801 Howard Ave, 06519 New Haven, CT, USA. Email: tommaso.volpi@yale.edu

Alessandra Bertoldo, Via Gradenigo 6/B, 35122 Padova, Italy. Email: alessandra.bertoldo@unipd.it

*[picture on PDF page 1]*

Journal of Cerebral Blood Flow & Metabolism 2024, Vol. 44(8) 1433-1449 ! The Author(s) 2024 Article reuse guidelines: sagepub.com/journals-permissions DOI: 10.1177/0271678X241237974 journals.sagepub.com/home/jcbfm

*[picture on PDF page 1]*

resting-state functional magnetic resonance imaging (rs-fMRI). 6 In addition to local activity , the functional relationships between spontaneous activity patterns of different brain regions (both close and distant) may also drive glucose consumption. 7 With respect to this, rs-fMRI has been used to calculate the so-called 'functional connectivity' (FC), i.e., the statistical relation among BOLD signal fluctuations of different brain regions. 8 The large-scale FC profile -be it static (sFC) or time-varying (tvFC) 9 -of a given brain region, which can be summarized using graph metrics derived from network theory, 10 is likely to prove relevant to its metabolic consumption.

To date, the literature exploring spatial associations between [ 18 F]FDG PET measures of glucose metabolism and a handful of rs-fMRI metrics (amplitude of low-frequency fluctuations, ALFF ; regional homogeneity, ReHo ; FC strength) has reported somewhat inconsistent results, with BOLD-based features capable of explaining from 0 to 64% of regional metabolic variance, depending on multiple factors. 11-15 One of the functional measures with the most consistent association with [ 18 F]FDG metabolism is ReHo, an index of local BOLD synchronization. 14-16

Here, we set out to re-assess the predictive power of rs-fMRI-derived variables on the regional variability of glucose consumption, expanding on previous analyses from multiple perspectives. First, we employed two independent datasets, to verify the robustness and reproducibility of the functional-metabolic associations in two cohorts of age-matched healthy adults, with different imaging protocols. Specifically, Dataset 1 refers to a dataset of simultaneously acquired [ 18 F]FDG PET and rs-fMRI data in healthy adults (n ¼ 26, 59.3 /C6 10.9 years old) from two published studies, 12,17 which we analyzed in previous work. 18 Dataset 2 , on the other hand, comes from a different pool of healthy adults (n ¼ 33, 58.4 /C6 13.7 years old), undergoing sequential [ 18 F]FDG PET and rs-fMRI acquisitions. 19 Secondly, to our knowledge, no study has yet attempted a multivariable description of glucose metabolism using BOLD-based functional features representing different properties of the brain's spontaneous activity. This is potentially an important drawback, since glucose consumption is expected to support a wide variety of metabolic reactions, 4,20 which in turn underpin complex processes of cellular homeostasis and synaptic plasticity potentially reflected in different features of the rs-fMRI signal. We further articulate this in a multilevel modeling framework, to fully characterize the individual variability in the functional-metabolic coupling.

Within this framework, we calculated a total of 50 BOLD-based functional features (see Table 1 for the complete list), pooled into four categories, i.e., 1) signal, 2) hemodynamic response function (HRF), 21

3) sFC, and 4) tvFC, for both datasets. These features were chosen to provide a complete characterization of the information contained in the BOLD signal, whether with respect to its local properties, its vascular information, or the network connectivity structure that can be derived from it, both static and changing over time. With this rich arsenal of functional variables, we set out to address multiple questions. Throughout, we controlled for multiple hypothesis testing using false discovery rates (FDR). First, we assessed the strength of the bivariate spatial associations between functional features and glucose metabolism (expressed as [ 18 F] FDG standardized uptake value ratio, SUVR ) across all brain regions, to understand how strong the relationship between brain glucose consumption and BOLD local activity magnitude , local activity synchronization , inter-regional large-scale FC, hemodynamics , is. Moreover, to probe the spatial heterogeneity of the functional-metabolic coupling, we looked at how it changes according to the ranking of brain regions based on glucose metabolism. Then, we focused on explaining population-level metabolic variance across regions by combining a selected group of functional features with a multivariable regression model, and evaluating how much the chosen group of predictors was populated by local vs. large-scale functional properties. Finally, we examined between-individual variability of the functional-metabolic coupling, and whether this could be explained by participant-specific demographics (e.g., age, sex) or peripheral metabolism (weight, body-mass index, insulin levels etc.).

### Materials and methods

### Participants and imaging protocols

Dataset 1 includes 26 healthy participants (13 F; 59.3 /C6 10.9 years) from two studies. 12,17 Imaging procedures were approved by the Code of Ethics of the World Medical Association and the Institutional Review Board and Ethics Committee at the Technische Universit € at Mu ¨ nchen 17 and the SDN Foundation. 12 [ 18 F]FDG PET, rs-fMRI (TR/TE ¼ 2000/30 ms, 3-4mm isotropic), T1-weighted (T1w) MR data were simultaneously collected on identical Siemens Biograph mMR scanners.

Dataset 2 includes 33 age-matched healthy participants (22 F; 58.4 /C6 13.7 years) from the AMBR study. 19 Imaging procedures were approved by Human Research Protection Office and Radioactive Drug Research Committee at Washington University in Saint Louis. T1w, rs-fMRI were acquired on a Siemens Prisma fit scanner (TR/TE ¼ 800/33 ms, 2.4 mm isotropic, multiband factor 6). Static PET

***Table 1. Extracted rs-fMRI features and their categories.***

| Pools | rs-fMRI variables |
|---|---|
| Signal | med-BOLD : median of the BOLD time series 32 MAD - BOLD : median absolute deviation (MAD) of the BOLD time series 77 skew-BOLD : skewness of the BOLD time series 78 ApEn-BOLD : approximate entropy (ApEn) of the BOLD time series 31 rApEn-BOLD : range ApEn of the BOLD time series 79 AR-BOLD : reflection coefficient of the first-order autoregressive AR(1) 79 |
| HRF sFC | model fit to BOLD time series ALFF : amplitude of low frequency fluctuations (ALFF) of BOLD time series 32 ReHo : regional homogeneity of BOLD time series 33 MAD-ReHo : MAD of the time-varying ReHo (tvReHo) 80 CV-ReHo : percent coefficient of variation of tvReHo 80 peaks-BOLD : number of BOLD pseudo-events 21 peak-HRF : height of HRF peak 21 hrf-DEG : degree (DEG) of HRF correlation matrix [ original metric ] hrf-STR : strength (STR) of HRF correlation matrix [ original metric ] hrf-CC : clustering coefficient (CC) of HRF correlation matrix [ original metric ] hrf-BC : betweenness centrality (BC) of HRF correlation matrix [ original metric ] hrf-EC : eigenvector centrality (EC) of HRF correlation matrix [ original metric ] hrf-LE : local efficiency (LE) of HRF correlation matrix [ original metric ] hrf-GE : global efficiency (GE) of HRF correlation matrix [ original metric ] s-DEG : DEG of sFC 36 s-STR : STR of sFC 36 s-CC : CC of sFC 36 s-BC : BC of sFC 36 s-EC : EC of sFC 36 s-LE : LE of sFC 36 s-GE : GE of sFC 36 med-LEig : median of the Leading Eigenvector (LEig)'s time series 37 |
|   | mdiff-DEG : temporal median of the differentials (mdiff) of DEG time series [ original metric ] mdiff-STR : mdiff of STR time series [ original metric ] mdiff-CC : mdiff of CC time series [ original metric ] mdiff-BC : diff of BC time series [ original metric ] mdiff-EC : mdiff of EC time series [ original metric ] mdiff-LE : mdiff of LE time series [ original metric ] mdiff-GE : mdiff of GE time series [ original metric ] CV-DEG : coefficient of variation of DEG time series 81 |
| tvFC | CV-STR : percent coefficient of variation of STR time series 81 CV-CC : percent coefficient of variation of CC time series 81 CV-BC : percent coefficient of variation of BC time series 81 CV-EC : percent coefficient of variation of EC time series 81 CV-LE : percent coefficient of variation of LE time series 81 CV-GE: percent coefficient of variation of GE time series 81 SampEn-DEG : sample entropy (SampEn) of DEG time series 82 SampEn-STR : SampEn of STR time series 82 SampEn-CC : SampEn of CC time series 82 SampEn-BC : SampEn of BC time series 82 SampEn-LE : SampEn of LE time series 82 SampEn-GE : SampEn of GE time series 82 MAD-LEig : MAD of LEig time series 37 CV-LEig : percent coefficient of variation of LEig time series 37 mdiff-LEig : mdiff of LEig time series 37 |

Fifty fMRI-derived variables, divided according to the pool to which they belong: 1) signal, 2) hemodynamic response function (HRF), 3) static functional connectivity (sFC), 4) time-varying functional connectivity (tvFC). See Supplementary Methods for full description of the features.

images was obtained by summing late frames (40 0 -60 0 ) of PET acquisitions (Siemens ECAT HR þ ).

All studies were conducted according to the principled outlined in the Declaration of Helsinki. All participants provided written consent.

Details are reported in Supplementary Methods and in. 12,17,19

### Data preprocessing

In Dataset 1 , a surface-based pipeline was employed (based on the Human Connectome Project minimal pipeline 22 ) as in our previous study. 18 In Dataset 2, the same preprocessing steps were performed in volumetric space. See Supplementary Methods for details.

PET images were normalized by injected dose and participant's weight into standard uptake values ( SUV ), and then intensity-normalized into SUVR dividing by whole-brain average SUV. 23 SUVR maps were parcellated into 216 regions (200 Schaefer regions, 24 16 subcortical regions 25 ). Spatial smoothing was avoided, to minimize partial volume effects. In Dataset 2 , due to lower spatial resolution, Iterative Yang partial volume correction was performed. 26,27

Rs-fMRI preprocessing included slice-timing correction, nuisance regression, 28,29 high-pass filtering (cutoff ¼ 0.008 Hz). Additional motion correction steps were calibrated based on the type of rs-fMRI features to be extracted, i.e., a) despiking for tvFC, HRF, and other time-varying measures, which require a less aggressive approach that respects the temporal structure of the signal, b) censoring, i.e., a more aggressive approach, for sFC and other static measures 30 ). Rs-fMRI signals were also parcellated.

### Resting-state fMRI feature extraction

Fifty rs-fMRI features were obtained in each participant. The extracted features were chosen to describe different aspects of the BOLD 1) signal , 2) HRF , 3) sFC , 4) tvFC (Table 1). The signal pool (1) contains features related to the basic statistics of the BOLD time series (temporal median, variance, skewness), its complexity/entropy, 31 its low-frequency fluctuations ( ALFF ), 32 local coherence ( ReHo ) 33 and highamplitude events ( peaks-BOLD ). The HRF pool (2) includes features related to the HRF, 21 which links the BOLD signal to neural activity. 34 Among these we have the HRF peak amplitude (a potential proxy for CBF 35 ) and the correlations between HRF time series of different regions, which we introduced here for the first time 21 to describe functional networks of potentially pure vascular activity, which were summarized at the region level by means of graph properties, for correspondence with traditional FC studies. 36

In the sFC pool (3) the same graph metrics are again employed to characterize sFC, i.e., FC calculated across the entire fMRI scan. The tvFC pool (4) describes the temporal variation of graph metrics across sliding windows 9 as a measure of FC variability of each brain region. FC was characterized both as the correlation between BOLD signal magnitudes , and as the coherence of their phases , as they may provide complementary views. 37

Overall, this wide range of functional metrics were selected to represent the majority of known properties of the rs-fMRI signal and its FC. See Supplementary Methods for details.

### Bivariate analysis of the functional-metabolic relationship

The bivariate spatial relationship between SUVR and rs-fMRI properties was assessed at group level, taking the region-wise across-individual median values for SUVR and each functional feature. After testing for Gaussianity (p < 0.05, Shapiro-Wilk 38 ) the SUVR -fMRI association across regions was evaluated via Pearson's correlation (p < 0.05, Benjamini-Hochberg FDR correction 39 ). Furthermore, the type of bivariate relationship between SUVR and each rs-fMRI measure was tested by comparing four models, i.e., 1) linear , 2) mono-exponential , 3) power law , 4) log-linear . Model selection was performed using the residual sum of squares (RSS). 40 The spatial heterogeneity in the [ 18 F]FDG-fMRI relationship was probed by assessing correlations iteratively across clusters of regions with increasingly high or low SUVR . The threshold levels were determined by considering linearly increasing percentiles of the SUVR distribution over all regions, going from the 1 st (all 216 regions) to 85 th percentile (33 highSUVR regions), and then according to linearly decreasing SUVR percentiles, from the 100 th (again, all regions) to the 15 th percentile (33 lowSUVR regions). For each threshold level (i.e., group of chosen regions), Pearson's correlations between SUVR and all rs-fMRI features were calculated (p < 0.05, FDR-corrected across thresholds and number of features). 39 The absolute correlation values were summed across all 50 associations for each percentile, to determine which threshold corresponded to the maximum SUVR -fMRI coupling across features. The rationale for this analysis was to explore whether the level of coupling between SUVR and rs-fMRI measures is dependent on the average regional metabolism (low vs. high), or uniform across the entire range of SUVR values. See Supplementary Methods for details.

### Multivariable modeling of the functional-metabolic relationship at group level

After bivariate model selection, the log-linear model (i.e., logarithmic transformation of rs-fMRI variables) was chosen for multivariable modeling for simplicity (i.e., to avoid nonlinear fitting during feature selection, see Supplementary Methods). At group level, we used a multilinear regression approach to assess how much group region-wise SUVR variance could be explained by linear combination of multiple rs-fMRI features. Predictors and outcome were centered and scaled by their standard deviation (SD) across brain regions. To assess multicollinearity, we examined the correlations among predictors, design matrix condition number j X ð Þ , and variance inflation factors (VIFs). 41 The initial fit, obtained with all 50 rs-fMRI predictors, was interpreted as the highest possible predictive power contained in the available features, despite overparameterization. 42

To obtain a mathematically sound model, predictors were chosen based on a feature selection approach which would preserve the individual information and interpretation of each selected feature. Group-level feature selection was performed, since working at individual level would lead to unstable estimates. Importantly, feature selection was performed only on Dataset 1 ( training dataset); the chosen models were then applied to Dataset 2 ( testing dataset), unseen by model training. Between eleven selection strategies and resulting models, the choice was performed according to: 1) number of selected features, 2) design matrix j X ð Þ after selection, 3) VIFs, 4) R 2 , 5) BIC, 6) RSS, 7) estimate precision (%SE, percent standard error divided by estimated value), 8) estimate signs, i.e., the concordance with the signs of the corresponding bivariate correlation. 40 Specifically, the aim was to find models that minimized j X ð Þ , VIFs BIC, RSS, %SE of parameter estimates and maximized the R 2 , while maintaining sign concordance and potentially some heterogeneity in the pools which the features belonged to. See Supplementary Table 1 for details. The elected strategies include: a) non-negative least squares (NNLS), 43 b) elastic net regression, 44 c) general-to-specific (GETS) modeling. 45

### Full hierarchical modeling of the functional-metabolic relationship

Afull multilevel (mixed-effects) modeling approach was implemented to characterize in a single stage both group-level and individual-level effects contributing to the relationship between SUVR and the selected rs-fMRI variables, i.e., fixed effects h and random effects g i , respectively. 46 The individual -level (firstlevel) model is:

yi ¼ Fi ð Xi ; w i Þ zi ¼ yi þ vi

with yi as the SUVR prediction for the i th individual ( i ¼ 1 ; . . . ; m ), which is a function of Xi ð the fixedeffects design matrix composed by the rs-fMRI features), and of parameters w i to be estimated; zi is the vector of the SUVR and vi is the within-individual variability , assumed to be normally distributed with zero mean and variance r 2 i . The population -level (second-level) model describes w i combining the population parameters h and the random variability of individual parameters around the population mean g i :

w i ¼ h þ g i

g i /C24 N 0 ; X ð Þ

where g i is normally distributed with zero mean, independent across individuals and with covariance matrix X (assumed to be full). The features selected with the group-average approach were included in the first-level model (after within-individual z-scoring).

The overall and individual multilevel model R 2 were evaluated, considering the pooled data of all participants (R 2 pooled ) and the single individual data (R 2 i ), respectively. The across-individual median (avg. wres) and median absolute deviation (MAD) divided by median of the weighted residuals were evaluated. The areas with higher positive ([0.5;1.5]) or negative ([ /C0 1.5; /C0 0.5]) avg. wres were visualized to highlight the areas where the model underestimates or overestimates the measured SUVR.

For details, see Supplementary Methods.

In Dataset 2 , participant-specific covariates were available, i.e., age ([years]), sex, height ([m]), weight ([kg]), body-mass index (BMI, [kg/m 2 ]), body-surface area (BSA, [m 2 ]), insulin plasma levels ([mIU/L]). Pearson's correlations (p < 0.05, uncorrected and FDR-corrected) and linear models relating R 2 i and covariates were calculated.

### Results

### BOLD-based features and their relationships

A flowchart describing [ 18 F]FDG PET and rs-fMRI analysis for both datasets is shown in Figure 1.

We extracted 50 rs-fMRI variables at the individual level, and subdivided them into 4 a priori -defined

• BOLD MRI

Signal

Hemodynamic response function (HRF)

Static FC (sFC)

Time-varying FC (tvFC)

Dataset 1

![Figure 1. Flowchart of rs-fMRI ( left ) and [ 18 F]FDG PET ( right ) data processing, feature extraction and analysis, for both datasets ( Dataset 1 and 2 ). The parcel-wise rs-fMRI data were used to extract fifty features representative of four 'pools', i.e., 1) signal and local measures, 2) HRF , 3) sFC , 4) tvFC . The PET -fMRI spatial coupling was investigated using bivariate correlation; moreover, after model selection performed on Dataset 1 (training dataset), multivariable multilevel modeling was carried out for individuals of both datasets.](figures/img_p006_0.png)

**Figure labels:**
- Dataset 2
- mananann
- Bivariate correlation
- Model selection
- Multivariable multilevel modeling
- Milit
- ["FIFDG SUVR
- 1.4
- 1.2

pools: 1) signal , 2) HRF , 3) sFC , 4) tvFC (Table 1). These functional metrics were selected to represent the majority of known properties of the rs-fMRI signal and its FC.

The correlation matrix between the 50 rs-fMRI variables was computed at group-average level for Dataset 1 (Figure 2(a)) and Dataset 2 (Figure 2(b)), to assess the degree of spatial redundancy between the extracted features. The a priori clustering into 4 pools was fairly consistent with the observed correlation structure. Signal, HRF, and sFC features ( upper block ) were distinguished and generally negatively correlated with tvFC features ( lower block ). There were some differences between the two datasets (especially in the signal and HRF pools, which displayed weaker relationships in Dataset 2 ).

### Bivariate functional-metabolic associations

We began by investigating bivariate spatial relationships between SUVR and the 50 functional variables at group-average level, as in previous studies. 11,12 Many significant across-region associations were detected (Pearson's r, p < 0.05, FDR-corrected 39 ) Correlation coefficients are shown in Figure 2(c) ( Dataset 1 ) and (d) ( Dataset 2 ). In Dataset 1 , the strongest positive associations (all p < 10 /C0 12 ) were detected for 1) ReHo (r ¼ 0.57), 2) temporal MAD of ReHo ( MAD-ReHo ) (r ¼ 0.50), 3) BOLD autoregressive coefficient ( AR-BOLD ) (r ¼ 0.54), i.e., measures of BOLD local activity and synchronization. In Dataset 2 the strongest positive correlations (p < 10 /C0 12 ) were again with 1) ReHo (r ¼ 0.73), 2) MAD-ReHo (r ¼ 0.73), 3) AR-BOLD (r ¼ 0.69). The strongest negative correlations (p < 10 /C0 12 ) for Dataset 1 were peaks-BOLD (r ¼/C0 0.52), a measure of the number of highamplitude events in the BOLD signal, coefficient of temporal variation of betweenness centrality ( CV-BC ) (r ¼/C0 0.45), and median differential of global efficiency temporal variability ( mdiff-GE ) (r ¼/C0 0.45). For Dataset 2 , we also have ALFF (r ¼/C0 0.67), and again peaks-BOLD (r ¼/C0 0.66), and mdiff-GE (r ¼/C0 0.65). This pattern of functional-metabolic correlations in the training dataset is well reproduced in the testing dataset (Figure 2(c) and (d)) (Pearson's correlation between z-transformed correlations: r ¼ 0.88, p < 10 /C0 9 ). Of note, positive associations emerged for the majority of the signal-based, HRF and sFC-related features, while tvFC metrics displayed a consistent negative association with glucose metabolism. Importantly, the functional features that have the highest correlations with SUVR mainly belong to the local BOLD pool.

4[18F]FDG PET :

(a)

Signal

HRF

SFC

tVFC

(c)

Pearson's R

0.5

1÷66684655558

13152

Signal

0.4

02

![Figure 2. Bivariate correlations among rs-fMRI variables, and between rs-fMRI variables and SUVR , at group-average level. The pattern of Pearson's correlations (p < 0.05, FDR-corrected, non-significant values in white) among rs-fMRI features, divided according to the pool to which they have been assigned (1) signal, 2) HRF , 3) sFC, 4) tvFC), is shown in a ( Dataset 1 ) and b ( Dataset 2 ). The rsfMRI features are tested for association with group median SUVR across regions via Pearson's correlations (p < 0.05, significant values after FDR correction indicated with an asterisk), as shown in c ( Dataset 1 ) and d ( Dataset 2 ).](figures/img_p007_0.png)

**Figure labels:**
- -02
- -0.4
- -0.6
- -0.8
- HRF
- sFC
- tvFC
- Pearson's R
- SFC
- (p)
- -0.2
- 1918g
- 0.5
- ПР 141
- Signal
- 68688
- maill-LEig

### Functional-metabolic associations are stronger in low-metabolism brain regions

To further investigate the relationship between glucose metabolism and BOLD measures and its expected spatial heterogeneity, 47 Pearson's correlations were iteratively re-evaluated across groups of brain regions with progressively higher or progressively lower mean SUVR . Specifically, correlations were tested by considering regions with progressively higher SUVR values, as well as regions with progressively lower SUVR values (Supplementary Figure 1). Correlations between metabolism and all 50 features (Pearson's r, p < 0.05, FDR-corrected) are shown in Figure 3(a) ( Dataset 1 ) and (b) ( Dataset 2 ), for each threshold level along the SUVR distribution. Assessing the correlation in nodes with progressively higher SUVR ( right side of Figure 3 (a) and (b)) does not lead to any effect for the majority of measures in both datasets. However, a marked increase in many associations can be observed by assessing correlations over nodes with lower SUVR values ( left side of Figure 3(a) and (b)). Notable exceptions to this overall pattern are some features from the signal and local rs-fMRI pool (e.g., ReHo ), which in both datasets maintain a consistent statistically significant relationship with SUVR irrespective of the pool of regions chosen for correlation testing. We identified the threshold corresponding to the highest SUVR -fMRI coupling (i.e., sum of all correlation weights across features) and reported the spatial pattern of the included regions in Figure 3(c) ( Dataset 1 ) and (d) ( Dataset 2 ). In Dataset 1 , parcels belonged to temporal/limbic areas (including hippocampus), sensorimotor cortices, cerebellum, and subcortical regions (e.g., pallidum). Some differences emerged in Dataset 2 , such as a stronger involvement of insula and medial frontal cortex, as well as thalamus and caudate.

These findings suggest the existence of a nonlinear spatial relationship between glucose metabolism and most functional features: stronger and more linear associations are present across a range of brain regions with low-average metabolism, with weaker coupling as SUVR gets higher. This nonlinear association was tested by comparing four models, confirming a tendency towards nonlinearity (Supplementary Figure 2).

### A multivariable combination of BOLD features to explain glucose metabolism

We then set out to assess which combination of functional features was best able to explain the spatial pattern of glucose metabolism using multivariable multilevel modeling. 46 We chose to identify relevant predictors at the population level, exploiting the

(b)

Signal

HRF

0.6

0.4

(a)

Signal

HRF

SFC

tvFC

(c)

0.8

lower

SUVR

< 50** pret.

![Figure 3. Bivariate functional-metabolic associations are stronger across regions with low glucose metabolism. Pearson's correlations (p < 0.05, FDR-corrected, non-significant values in white) between SUVR and all rs-fMRI features ( y axis ), evaluated across nodes selected by linearly increasing ( x axis - right side ) and decreasing ( x axis - left side ) percentiles of the SUVR distributions are shown in a ( Dataset 1 ) and b ( Dataset 2 ). On top of both panels, we reported representative examples of histograms showing the SUVR percentiles (i.e., brain regions) which are included in each correlation ( in green ), i.e., bottom 20% or 50% ( left ), or top 50 or 20% ( right ), of the SUVR distribution. The dashed black lines show the percentiles with maximum correlation across features (corresponding to the 40% of regions with lower SUVR for Dataset 1 , and 50% of regions with lower SUVR for Dataset 2 ). For these two percentile thresholds, the corresponding brain regions are assessed are highlighted in green in c ( Dataset 1 ) and d ( Dataset 2 ) - 87 regions in Dataset 1 , 106 regions in Dataset 2.](figures/img_p008_0.png)

**Figure labels:**
- SUVR percentiles
- 0.2
- -02
- -0.4
- -0.6
- 28888578288228888899288889781889288
- "SUVR percentiles"
- Pearson's R
- Signal
- HRF
- SFC
- tvFC
- (d)
- 48X88948888848888889889888₴
- -0.2
- -SUVR percentiles

denoising properties of the average. The selected model structures were then used to characterize the individual variability of the spatial functional-metabolic association, using the fact that [ 18 F]FDG and rs-fMRI were acquired in the same participants, allowing us to obtain a multivariable description of glucose metabolism at individual level. Importantly, multivariable models were identified in Dataset 1 , and then their reproducibility was tested in Dataset 2 .

To preliminarily assess the maximum explanatory power provided by the available rs-fMRI features, we fit a regression model employing all 50 rs-fMRI features in a log-linear form (i.e., with log-transformed predictors, to account for the detected nonlinearity).

For Dataset 1 , the model had an R 2 value of 0.62. In Dataset 2 , the model had higher explanatory power (R 2 ¼ 0.79). However, saturation was not reached in either case, despite the number of parameters (p ¼ 50). Strong correlations between predictors were obviously present (Figure 2), with a high condition number for both design matrices ( j X Dataset 1 ð Þ¼ 70.58, j X Dataset 2 ð Þ ¼ 83.35). 41

To reach a sound multivariable regression model, feature selection was performed on Dataset 1 . Among eleven tested methods, the chosen approach (employing NNLS estimation 43 and elastic net regression 44 ) led to a 9-parameter (9p) model. Though the 9p model was the best in characterizing the link between functional higher

SUVR

> 801" prct.

(b) s

0.5

lower

SUVR

higher

SUVR

> 80** prct.

(a)

Signal

HRF

sFC

tvFC

ApEn-BOLD

ReHo

(b)

Signal

ApEn-BOLD - rApEn-BOLD

ReHo and metabolic features, a simplified 3p model was also derived (via NNLS and GETS modeling 45 ) as a parsimonious version of the model, having a lower predictive performance but increased estimate precision. In the 9p model, the selected functional variables were 1) approximate entropy of BOLD ( ApEn-BOLD ), 2) range ApEn-BOLD ( rApEn-BOLD ), 3) ReHo , 4) coefficient of variation of ReHo ( CV-ReHo ), 5) peaksBOLD , 6) local efficiency of HRF network ( hrf-LE ), 7) sFC betweenness centrality ( s-BC ), 8) median of leading eigenvectors of BOLD phase coherence ( medLEig ), 9) coefficient of variation of betweenness centrality ( CV-BC ). Features 1-5 are from the signal pool, 6 is from the HRF pool, 7-8 from the sFC pool, and 9 from the tvFC pool. In the 3p model, the selected functional variables were 1) ReHo , 2) CV-ReHo , 3) CV-BC . Both solutions were evaluated in terms of goodness of fit (R 2 ¼ 0.41 for the 9p model, and R 2 ¼ 0.37 for the 3p model) and precision of the estimates (mean /C6 SD of the %SE: 66.7 /C6 17.8% in the 9p model, 27.6 /C6 8.1% in the 3p model). When applied to Dataset 2 , the 9p model had an R 2 of 0.69 but a low precision of the estimates (mean /C6 SD of the %SE: 179.3 /C6 226.7%). The 3p model had an R 2 of 0.59 with better precision (mean /C6 SD of the %SE: 27.1 /C6 13.2%).

The first five predictors of the 9p model, and two for the 3p model, belong to the signal and local synchronization pool, which additionally supports a stronger functional-metabolic relationship for local features. Notably, the identified predictors were chosen with moderate/high consistency across the eleven feature selection methods (with ReHo as the most consistent), highlighting the robustness of their association with glucose metabolism (Supplementary Figures 3, 4).

### Between-individual variability of the functionalmetabolic model

We then fully characterized the BOLDSUVR spatial association across the brain and its variability across individuals, applying the multilevel modeling framework to the individual data using the identified predictors. Moreover, we tested the robustness and reproducibility of the models identified on Dataset 1 by applying them on Dataset 2 .

The fixed -effect ( h ) estimates 46 are reported in Figure 4(a) ( Dataset 1 ) and (b) ( Dataset 2 ). The relative importance of the nine parameters was overall similar in the two datasets: in particular, ReHo always had the highest weight, consistently with the bivariate analysis; moreover, ApEn-BOLD , rApEn-BOLD , CV-ReHo and peaks-BOLD , all belonging to the signal/local pool, maintain a similar role in the two datasets. More instability was detected for the remaining parameters belonging to the HRF, sFC and tvFC pools (with the exception of med-LEig ), which in Dataset 2 became non-significant (SEs crossing the zero line) or flipped their sign. This was also present for the 3p model, with the fixed effect for CV-BC flipping sign from negative ( Dataset 1 ) to positive ( Dataset 2 ). Importantly, if ReHo alone was used as a predictor, we could still

![Figure 4. Multilevel modeling of glucose metabolism: fixed effects (9-parameter model). Estimate weights and standard errors (SEs) for the fixed effects h , which represent the parameters that best explain SUVR across brain regions at group level. The nine selected predictors, shown for Dataset 1 (a) and Dataset 2 (b) on the y axis, are grouped according to the pool they belong to: approximate entropy of BOLD ( ApEn-BOLD ), range ApEn-BOLD ( rApEn-BOLD ), regional homogeneity ( ReHo ), coefficient of variation of ReHo ( CV-ReHo ), number of high-amplitude events in BOLD signal ( peaks-BOLD ), local efficiency of HRF network ( hrf-LE ), betweenness centrality of static FC ( s-BC ), median of leading eigenvectors of BOLD phase coherence ( med-LEig ), coefficient of variation of betweenness centrality ( CV-BC ).](figures/img_p009_0.png)

explain 32% (R 2 ¼ 0.321) and 53% (R 2 ¼ 0.527) of the variance in group-level SUVR for Dataset 1 and 2 respectively.

When looking at the average of the 9p model residuals across participants, which highlighted how well each region's SUVR was described by the chosen combination of predictors, differences between the datasets emerge (Figure 5(a) and (b)). The highlighted positive and negative peaks identify regions with high and low SUVR , respectively, which are not satisfactorily explained by the combination of the available rsfMRI features (under- and over-estimated, respectively). In Dataset 1 , we found high positive values in posteromedial cortex (posterior cingulate cortex in particular), which were attenuated in Dataset 2. Moreover, some positive weights were present in frontolateral/motor cortex for Dataset 2 , which were missing in Dataset 1. The subcortex showed higher consistency, with positive values in thalamus and caudate, and negative in hippocampi and cerebellum. This deficiency in explanatory power was also consistent across individuals, i.e., the areas with high residuals also had the lowest between-individual variability ( not shown ).

Individual variability in the functional-metabolic association was non-negligible. When pooling all participant data, the explained variance of the 9p model (R 2 pooled) was 0.245 in Dataset 1 , and 0.346 in Dataset 2 (0.18 and 0.278 for the 3p model, respectively). The ReHo -only model had an R 2 pooled of 0.148 in Dataset 1 , and 0.266 in Dataset 2 . The multilevel model individual R 2 (R 2 i) displayed high variability, from 0.05 to 0.45 in Dataset 1 (Figure 5(c)) and from 0.01 to 0.54 in Dataset 2 (Figure 5(d)).

Only for Dataset 2 , individual covariates were available, which allowed us to explore whether the variability in the multilevel R 2 i values would (at least partly) be explained by participants' demographics (age, sex, height) and information on their peripheral metabolic status. Indeed, weight, BMI, BSA and insulin were all negatively correlated with the 9p model R 2 i (Figure 6), although only weight and BSA survived FDR correction. These correlations remain consistent when assessing the 3p model and the ReHo -only model ( not shown ). By combining covariates, an improved description of the R 2 i variability can be reached: weight and insulin levels combined can explain 39% of the variance in 9p R 2 i (adjusted R 2 ¼ 0.389, n ¼ 24). No effect of age or sex on the functional-metabolic coupling was detected.

### Discussion

In this work, we attempted to comprehensively investigate and model how much of the spatial variance in healthy glucose metabolism, as measured by [ 18 F]FDG

PET, can be explained by different aspects of the brain's spontaneous activity, as measured by rsfMRI. We hypothesized that a combination of many facets of spontaneous BOLD activity would be able to capture multiple aspects of the brain's molecular processes, and thereby collectively explain (part of) glucose metabolic variance. We took advantage of the rigorous framework offered by multilevel modeling to account for between-individual variability in the functionalmetabolic spatial relationship. Moreover, we assessed the reproducibility of our findings using two independent datasets, to verify the robustness of the functionalmetabolic model even in the presence of different acquisition parameters. In addition to the functional variables that have already been associated with glucose metabolism, i.e., ALFF , ReHo , the strength of static FC, 11-13,15,18 we extended our assessment to a variety of previously unexplored features, including time-varying FC and hemodynamic response. To our knowledge, this is the first study to model the [ 18 F] FDG PET vs. rs-fMRI functional-metabolic coupling using a multivariable approach, attempting to identify the best subset of functional metrics to explain metabolic variability across regions. This is a novel attempt to address the complexity of brain glucose metabolism, 20 which involves both oxidative and glycolytic components supporting numerous cellular processes (protein synthesis, protein modification, cell signaling, housekeeping duties, postsynaptic potentials, vesicle recycling etc.). 4,20 The exact partitioning of the brain's energy budget into these processes remains an object of debate and ongoing research, 3,48 and some of these processes might be reflected in different features of spontaneous activity captured by the rs-fMRI signal.

The multilevel model best explaining regional metabolic variability consisted of nine functional variables ( ApEn-BOLD, rApEn-BOLD, peaks-BOLD, ReHo, CV-ReHo, hrf-LE, s-BC, med-LEig, CV-BC ). We found that, despite availability of a large number of features, the strongest and most consistently selected predictors of glucose metabolism came from local properties of the BOLD signal, such as temporal aspects of the signal and its local synchronization ( ReHo, peaks-BOLD ). Crucially, ReHo was the most relevant feature in both our test and validation dataset, and both with bivariate and multilevel modeling. Why does ReHo correlate best with [ 18 F]FDG PET uptake? As a measure of local signal homogeneity, ReHo might reflect underlying features of intra-regional sub-organization, 15,49 including cytoarchitectural features (e.g., myelination 50 ) which are known to differentiate primary sensorimotor areas from association areas. It is also possible that regions with high ReHo require more collective activity that increase glucose utilization. Overall, this points to ReHo being one of the most

(a)

(c)

Individual R2

-1.5

0.6

0

.2

(b)

![Figure 5. Multilevel modeling of glucose metabolism: explained regional variability (9-parameter model). Across-individual average of weighted residuals vi of the multilevel model (avg. wres), for Dataset 1 (a) and Dataset 2 (b), visualized in the [ /C0 1.5/ /C0 0.5; 0.5/1.5] range for each brain region. Boxplot of individual R 2 values - R 2 i (median and boxes of 25th and 75th percentile are in overlay) representing the SUVR spatial variance explained by the BOLD-based predictors at individual level, for Dataset 1 (c) and Dataset 2 (d).](figures/img_p011_0.png)

**Figure labels:**
- avg. wres
- -8-84
- +=8o
- 1.5
- -1.5
- (d)
- 0.6
- 0.5 -
- Individual R2
- 0.4
- 0.3 -
- 0.2 -
- 0.1

promising metabolic proxies 16 (see Supplementary Discussion).

On the other hand, our results also support the idea that large-scale functional connectivity (at least when summarized by graph metrics) is only partially linked to local metabolism, even when PET and fMRI are simultaneously acquired ( Dataset 1 ). The strength of static FC was not a strong proxy of glucose metabolism, as we showed in, 18 and the betweenness centrality, which was more consistently associated with glucose metabolism, was a weaker contributor to the multivariable model (fixed effect weights, Figure 4). The temporal variability of FC (tvFC), on the other hand, had a negative association with metabolism in both datasets (Figure 2), showing a tendency for metabolic consumption to be higher if functional

(a)

0.8

0.7

0.6

0.5 A

* 0.4

0.3

0.2

0.1

0

-0.1

50

0.8

0.7

0.6

0.5

0.4

0.3

0.2

Model F

(c)

Model R2

0.1

-0.1

-0.2

1.6

Model R? vs. Weight, r = -0.495, p = 0.003, PFoR = 0.033

Д

Data

Linear Fit

•- 95% Prediction Interval

Д

0.8

0.7

0.6

0.5

ДД

EA

![Figure 6. Multilevel modeling of glucose metabolism: individual variability vs. covariates in Dataset 2 . Scatter plots of the significant correlations (p < 0.05, both uncorrected and FDR-corrected) between individual R 2 i values (9-parameter model) and participant covariates: weight [kg] (a), body-mass index - BMI [kg/m 2 ] (b), body-surface area - BSA [m 2 ] (c), insulin plasma levels [mIU/L] (d). These correlations are assessed in Dataset 2 only.](figures/img_p012_0.png)

**Figure labels:**
- ДД
- Д
- 60
- 70
- 80
- 90
- Weight [kg]
- 100
- 110
- 120
- Model R? vs. BSA, r =-0,492, p = 0.004, PFDR = 0.033
- Data
- • Linear Fit
- • - 95% Prediction Interval
- D
- 1.8
- 2
- 2.2
- BSA (m2]
- 2.4
- 2.6
- 2.8
- 0.4
- Model R?
- 0.3
- 0.2
- 0.1
- 0
- -0.1
- -0.2
- 15
- (d)
- 0.7
- 0.6
- 0.5
- * 0.3
- Model I
- 20
- 25
- 30
- BMI [kg/m']
- 35
- 40
- Model R? vs. Insulin, r = -0,473, p = 0.02, PFDR = 0.118
- Linear Fit
- - 95% Prediction Interval
- 5
- 10
- Insulin [mIU/L]
- 45

connectivity is stable over time, which may imply that maintaining a stable FC is an energy-expensive process as recently suggested. 51 To our knowledge, this association has not been previously reported. While we refer to our previous work for discussion on the metabolic basis of FC 18 , we also hypothesize that bringing [ 18 F] FDG PET estimates into a 'connectivity' framework might improve their match with large-scale FC, with ongoing research on metabolic connectivity offering new perspectives for functional-metabolic integration. 52-54

When examining how functional-metabolic relationships are modulated across pools of regions selected according to their metabolic ranking, we found that, consistently across both datasets, in groups of nodes with higher glucose consumption functional-metabolic coupling was not stronger, but instead the correlations increased significantly when assessed across nodes with lower and lower metabolic consumption (Figure 3). What this implies is that regions with high [ 18 F]FDG uptake remain unexplained by most rs-fMRI functional features (with the exception of a few variables from the local BOLD pool). This finding, which is consistent for both datasets, demonstrates that the [ 18 F]FDGfMRI spatial relationship is nonlinear for most of the functional features, as previously hinted for a few specific measures. 11,47 This was directly tested using model selection (between linear, exponential, power law, loglinear relationships), and a nonlinear model could be attributed to 86% of the cases.

These findings may reflect known nonlinearities in the associations between the BOLD signal and neuronal activity, 55 to which glucose metabolism is more directly related; 5 moreover, nonlinear models such as

(b)

Model R? vs. BMI, r = -0.382, p = 0.028, PFoR = 0.128

Data

Linear Fit

power laws are commonly identified in biology, particularly when metabolic budgets are involved. 11 A nonlinear spatial relationship between resting CBF , a main ingredient of BOLD, and brain glucose metabolism has also been reported, complicating the original picture that saw CBF and glucose consumption as linearly coupled. 56

The difficulty of functional predictors to explain the metabolic rates of regions with high [ 18 F]FDG uptake is confirmed when looking at the zones of polarization in the multilevel model residuals, especially in Dataset 1 (Figure 4), with 'outliers' with higher metabolism which are poorly described by the available rs-fMRI features. From a biological standpoint, this may imply that high-metabolism regions are richer in properties that are not well captured by rs-fMRI, e.g., receptor and synaptic density, structural connections, fast neural activity, non-oxidative glucose metabolism, glutamate metabolism in astrocytes, signaling associated with the astrocyte-neuron lactate shuttle, rapid ATP production at highly active synapses, and other mechanistic hypotheses under active investigation. 4,20

In contrast to high group-level model R 2 values (0.4 for Dataset 1 , and 0.7 for 2 ), the individual model R 2 values were remarkably variable across individuals, ranging from 0.05 to 0.45 in Dataset 1 , and from 0.01 to 0.54 in 2 . This highlights the fact that the functionalmetabolic spatial relationship can vary significantly between individuals: for some, glucose consumption was more dependent on the underlying spontaneous functional architecture, but for other individuals, it was largely independent of spontaneous functional data. We clearly considered non-biological artifacts that dissociate fMRI 57 from PET 58 in terms of reproducibility. However, physiological reasons might also underlie this uncoupling. On this, in Dataset 2 (where participant-specific covariates were available) we detected a significant negative association between the strength of functional-metabolic coupling (multilevel model individual R 2 ) and participant weight, bodymass index, body-surface area, and insulin levels. It is possible that individual differences in peripheral metabolism alter how glucose is consumed to supply the brain's functional needs, 59 thereby affecting individual functional-metabolic coupling. More investigations in this area are needed, as this could help to reveal how and why certain metabolic diseases, such as diabetes, impart increased risk for neurological disorders. 60

Overall, the spatial heterogeneity and interindividual variability in the functional-metabolic show there is an uncoupling between brain metabolism and rsfMRI, 61 and argue that [ 18 F]FDG PET adds significant information alone and beyond rs-fMRI. While several current massive neuroimaging studies, e.g., HCP, 62

ABCD, 63 UK Biobank, 64 only acquire MRI, PET ('the white elephant' 65 ) still provides unique molecular information than cannot yet be replaced.

A key step in our framework has been to verify how robust our functional-metabolic model would be when tested on two datasets with different scanning characteristics and preprocessing pipelines. Dataset 1 , in particular, a) consists of simultaneously acquired [ 18 F] FDG PET and rs-fMRI data, which should minimize within-individual variability; 66 b) its [ 18 F]FDG data are obtained with a newer PET scanner (Siemens Biograph mMR 67 ); c) its rs-fMRI data are acquired with an older, conventional MR sequence (single-band, TR /C24 2 s, 3-4 mm 3 voxels) for a 7' /C0 10' duration; d) is processed with a surface space pipeline. In Dataset 2 , on the other hand, a) [ 18 F]FDG PET and rs-fMRI acquisitions are sequential; b) the [ 18 F]FDG data come from an older PET scanner (Siemens ECAT HR þ 68 ); c) rsfMRI data is obtained on a newer MRI scanner (Siemens Prismafit 69 ) with a state-of-the-art research sequence (multi-band, TR ¼ 0.8 s, 2.5 mm 3 voxels), but with a shorter scan duration (5'); d) a volume space pipeline is employed. The group-average SUVR estimates obtained from the two datasets are highly correlated (r ¼ 0.78), as can be expected due to high test-retest reliability of [ 18 F]FDG PET. 58 Each of the rs-fMRI features, on the other hand, have varying degrees of reproducibility between datasets; the HRF pool, in particular, seems to be the most affected by the different acquisition parameters in Dataset 2 , although the reasons for this are not yet evident. These technical discrepancies among the two datasets, which clearly have some impact on the results, further emphasize the strength of the main outcome of this work, i.e., that, in spite of these differences, the functionalmetabolic coupling is strongest for local BOLD measures, and localized synchrony in particular, and that a significant proportion of [ 18 F]FDG variance remains unexplained.

As to study limitations, the BOLD signal is known to be not only an indirect measure of neuronal activity, but it is also subjected to significant contamination from systemic modulations, both hemodynamic (heart rate variability, vasomotion etc.) and respiratory (e.g., respiratory volume variability): 70 this must always be remembered when interpreting spontaneous activity measures from rs-fMRI data. Moreover, [ 18 F]FDG SUVR may offer a biologically confounded view of glucose consumption. SUVR , which was employed here as well as in the majority of the literature on [ 18 F]FDG-fMRI coupling 12-14 due to it being the easiest to obtain in clinical PET imaging, is a semiquantitative and relative index, 71 which does not allow to unravel the kinetic relationships between the rate constants of the [ 18 F]FDG compartmental model, 1

i.e., K 1 (ml/cm 3 /min), the tracer inflow through the blood-brain barrier, k 2 (min /C0 1 ), its efflux into the venous blood, k 3 (min /C0 1 ), the hexokinase phosphorylation rate. 1,72 Moreover, a comprehensive understanding of the functional-metabolic relationships emerging from [ 18 F]FDG PET and rs-fMRI data would benefit from directly assessing other features, such as CBF and CMRO2 , as probed by [ 15 O]H2O PET 73 and [ 15 O]O2 PET 74 respectively, which would help elucidate the roles of hemodynamics and oxidative and nonoxidative metabolism, 75 as recently done in. 15 Also, the increasing availability of PET systems with much higher sensitivity and spatial resolution 76 is expected to allow to re-evaluate these associations with a higher degree of confidence. As to the sample sizes employed in this study, our two datasets are comparable to other multimodal PET-MRI studies, which are lengthy and technically challenging experiments typically limited to small numbers of participants. 12-14 Notably, the multilevel modeling approach, which we used to assess the variability of the intermodal spatial association across participants, is known to be robust and statistically valid for smaller sample sizes. 46 Finally, despite the use of sophisticated modeling approaches, this work remains correlational in nature: only a perturbational approach is going to allow to elucidate causal links between glucose metabolism and specific BOLDbased properties of spontaneous activity, and understand which of these has a direct vs. indirect link with metabolic consumption.

Summing up, we have used a comprehensive multimodal framework to model the regional variability of glucose metabolism, measured by [ 18 F]FDG SUVR , making predictions based on spontaneous activity, measured through a wide range of rs-fMRI properties. Regions with low-average glucose consumption are characterized by a stronger functional-metabolic coupling, implying the presence of a nonlinear, spatially heterogeneous relationship between glucose consumption and spontaneous activity. Moreover, using multivariable multilevel modeling to identify the best subset of functional metrics able to predict metabolic variance across brain regions, we have shown that functional metrics based on BOLD local properties, in particular its local synchronization ( ReHo ), are the most tightly related to glucose metabolism, and that this is reproducible in a dataset not seen during model training. Finally, we have shed light on the between-individual variability of functional-metabolic coupling, partly attributed to differences in peripheral metabolism. In conclusion, regional metabolic variability is only partly explained by resting-state brain activity as described by rs-fMRI. Further work is necessary to better understand the remaining spatial and inter-individual variance in brain glucose consumption.

### Funding

The author(s) disclosed receipt of the following financial support for the research, authorship, and/or publication of this article: Funding for the acquisitions in Washington University in Saint Louis was provided by McDonnell Center for Systems Neuroscience and NIH/NIA R01AG053503 and R01AG057536. Some of the MRI sequences used were obtained from Massachusetts General Hospital. The authors would like to thank Dr. Valentin Riedl for making part of Dataset 1 available.

### Declaration of conflicting interests

The author(s) declared no potential conflicts of interest with respect to the research, authorship, and/or publication of this article.

### Authors' contributions

TV and AB designed the research. MA collected part of the data for one of the original studies. TV analyzed the data. TV, ES, JJL, AGV, MSG, MC and AB interpreted the results. TV wrote the manuscript. All authors revised the manuscript.

### Supplementary material

Supplemental material for this article is available online.

### ORCID iDs

Tommaso Volpi https://orcid.org/0000-0002-5451-6710 John J Lee https://orcid.org/0000-0003-2269-6267 Manu S Goyal https://orcid.org/0000-0003-1970-4270

### References

- Sokoloff L, Reivich M, Kennedy C, et al. The [14C]deoxyglucose method for the measurement of local cerebral glucose utilization: theory, procedure, and normal values in the conscious and anesthetized albino rat. J Neurochem 1977; 28: 897-916.
- Clarke DD and Sokoloff L. Circulation and Energy Metabolism of the Brain. In: Siegel GJ, Agranoff BW, Albers RW, et al., (eds.), Basic neurochemistry: molecular, cellular and medical aspects. 6th edn, Ch. 31. Philadelphia: Lippincott-Raven, 1999.
- Raichle ME. The brain's dark energy. Science 2006; 314: 1249-1250.
- Attwell D and Laughlin SB. An energy budget for signaling in the grey matter of the brain. J Cereb Blood Flow Metab 2001; 21: 1133-1145.
- Sokoloff L. Energetics of functional activation in neural tissues. Neurochem Res 1999; 24: 321-329.
- Fox MD and Raichle ME. Spontaneous fluctuations in brain activity observed with functional magnetic resonance imaging. Nat Rev Neurosci 2007; 8: 700-711.
- Raichle ME. The restless brain: how intrinsic activity organizes brain function. Philos Trans R Soc Lond B Biol Sci 2015; 370: 20140172.
- Yeo BTT, Krienen FM, Sepulcre J, et al. The organization of the human cerebral cortex estimated by intrinsic

- functional connectivity. J Neurophysiol 2011; 106: 1125-1165.
- Allen EA, Damaraju E, Plis SM, et al. Tracking wholebrain connectivity dynamics in the resting state. Cereb Cortex 2014; 24: 663-676.
- Power JD, Cohen AL, Nelson SM, et al. Functional network organization of the human brain. Neuron 2011; 72: 665-678.
- Tomasi D, Wang GJ and Volkow ND. Energetic cost of brain functional connectivity. Proc Natl Acad Sci U S A 2013; 110: 13642-13647.
- Aiello M, Salvatore E, Cachia A, et al. Relationship between simultaneously acquired resting-state regional cerebral glucose metabolism and functional MRI: a PET/MR hybrid scanner study. NeuroImage 2015; 113: 111-121.
- Nugent AC, Martinez A, D'Alfonso A, et al. The relationship between glucose metabolism, Resting-State fMRI BOLD signal, and GABA A -Binding potential: a preliminary study in healthy subjects and those with temporal lobe epilepsy. J Cereb Blood Flow Metab 2015; 35: 583-591.
- Wang J, Sun H, Cui B, et al. The relationship among glucose metabolism, cerebral blood flow, and functional activity: a hybrid PET/fMRI study. Mol Neurobiol 2021; 58: 2862-2873.
- Deng S, Franklin CG, O'Boyle M, et al. Hemodynamic and metabolic correspondence of resting-state voxelbased physiological metrics in healthy adults. NeuroImage 2022; 250: 118923.
- Bernier M, Croteau E, Castellano CA, et al. Spatial distribution of resting-state BOLD regional homogeneity as a predictor of brain glucose uptake: a study in healthy aging. NeuroImage 2017; 150: 14-22.
- Riedl V, Bienkowska K, Strobel C, et al. Local activity determines functional connectivity in the resting human brain: a simultaneous FDG PET/fMRI study. J Neurosci 2014; 34: 6260-6266.
- Palombit A, Silvestri E, Volpi T, et al. Variability of regional glucose metabolism and the topology of functional networks in the human brain. NeuroImage 2022; 257: 119280.
- Goyal MS, Blazey T, Metcalf NV, et al. Brain aerobic glycolysis and resilience in Alzheimer disease. Proc Natl Acad Sci U S A 2023; 120: e2212256120.
- Magistretti PJ and Allaman I. A cellular perspective on brain energy metabolism and functional imaging. Neuron 2015; 86: 883-901.
- Wu GR, Liao W, Stramaglia S, et al. A blind deconvolution approach to recover effective connectivity brain networks from resting state fMRI data. Med Image Anal 2013; 17: 365-374.
- Glasser MF, Sotiropoulos SN, Wilson JA, WU-Minn HCP Consortium, et al. The minimal preprocessing pipelines for the human connectome project. NeuroImage 2013; 80: 105-124.
- Byrnes KR, Wilson CM, Brabazon F, et al. FDG-PET imaging in mild traumatic brain injury: a critical review. Front Neuroenergetics 2014; 5: 13.
- Schaefer A, Kong R, Gordon EM, et al. Local-Global parcellation of the human cerebral cortex from intrinsic functional connectivity MRI. Cereb Cortex 2018; 28: 3095-3114.
- Wang H and Yushkevich PA. Multi-atlas segmentation with joint label fusion and corrective learning - an open source implementation. Front Neuroinform 2013; 7: 27.
- Erlandsson K, Buvat I, Pretorius PH, et al. A review of partial volume correction techniques for emission tomography and their applications in neurology, cardiology and oncology. Phys Med Biol 2012; 57: R119-59.
- Thomas BA, Cuplov V, Bousse A, et al. PETPVC: a toolbox for performing partial volume correction techniques in positron emission tomography. Phys Med Biol 2016; 61: 7975-7993.
- Behzadi Y, Restom K, Liau J, et al. A component-based noise correction method (CompCor) for BOLD and perfusion based fMRI. NeuroImage 2007; 37: 90-101.
- Ciric R, Wolf DH, Power JD, et al. Benchmarking of participant-level confound regression strategies for the control of motion artifact in studies of functional connectivity. NeuroImage 2017; 154: 174-187.
- Power JD, Mitra A, Laumann TO, et al. Methods to detect, characterize, and remove motion artifact in resting state fMRI. NeuroImage 2014; 84: 320-341.
- Sokunbi MO, Staff RT, Waiter GD, et al. Inter-individual differences in fMRI entropy measurements in old age. IEEE Trans Biomed Eng 2011; 58: 3206-3214.
- Zou QH, Zhu CZ, Yang Y, et al. An improved approach to detection of amplitude of low-frequency fluctuation (ALFF) for resting-state fMRI: Fractional ALFF. J Neurosci Methods 2008; 172: 137-141.
- Zang Y, Jiang T, Lu Y, et al. Regional homogeneity approach to fMRI data analysis. NeuroImage 2004; 22: 394-400.
- Buxton RB and Frank LR. A model for the coupling between cerebral blood flow and oxygen metabolism during neural stimulation. J Cereb Blood Flow Metab 1997; 17: 64-72.
- Wu GR and Marinazzo D. Sensitivity of the resting-state haemodynamic response function estimation to autonomic nervous system fluctuations. Phil Trans R Soc A 2016 May 13; 374: 20150190.
- Rubinov M and Sporns O. Complex network measures of brain connectivity: uses and interpretations. NeuroImage 2010; 52: 1059-1069.
- Cabral J, Vidaurre D, Marques P, et al. Cognitive performance in healthy older adults relates to spontaneous switching between states of functional connectivity during rest. Sci Rep 2017; 7: 5135.
- Shapiro SS and Wilk MB. An analysis of variance test for normality (complete samples). Biometrika 1965; 52: 591-611.
- Benjamini Y and Hochberg Y. Controlling the false discovery rate: a practical and powerful approach to multiple testing. J Royal Statistical Soc B 1995; 57: 289-300.
- Mu ¨ ller S, Scealy JL and Welsh AH. Model selection in linear mixed models. Statist Sci 2013; 28: 135-167.

- Belsley DA. Conditioning diagnostics: collinearity and weak data in regression. (Probability and mathematical statistics) . New York: Wiley, 1991, 396p.
- Cobelli C and DiStefano JJ. Parameter and structural identifiability concepts and ambiguities: a critical review and analysis. Am J Physiol 1980; 239: R7-24.
- Meinshausen N. Sign-constrained least squares estimation for high-dimensional regression. Electron J Stat 2013; 7: 1607-1631.
- Zou H and Hastie T. Regularization and variable selection via the elastic net. J R Stat Soc B 2005; 67: 301-320.
- Hoover KD and Perez SJ. Data mining reconsidered: encompassing and the general-to-specific approach to specification search. Econom J 1999; 2: 167-191.
- Hox JJ, Moerbeek M and R van de S. Multilevel analysis: techniques and applications. (Quantitative methodology series). Third edition . New York, NY: Routledge, 2017.
- Shokri-Kojori E, Tomasi D, Alipanahi B, et al. Correspondence between cerebral glucose metabolism and BOLD reveals relative power and cost in human brain. Nat Commun 2019; 10: 690.
- Yu Y, Akif A, Herman P, et al. A 3D atlas of functional human brain energetic connectome based on neuropil distribution. Cereb Cortex 2023; 33: 3996-4012.
- Jiang L and Zuo XN. Regional homogeneity: a multimodal, multiscale neuroimaging marker of the human connectome. Neuroscientist 2016; 22: 486-505.
- Glasser MF, Coalson TS, Robinson EC, et al. A multimodal parcellation of human cerebral cortex. Nature 2016; 536: 171-178.
- Deng S, Li J, Thomas Yeo BT, et al. Control theory illustrates the energy efficiency in the dynamic reconfiguration of functional connectivity. Commun Biol 2022; 5: 295.
- Amend M, Ionescu TM, Di X, et al. Functional restingstate brain connectivity is accompanied by dynamic correlations of application-dependent [18F]FDG PET-tracer fluctuations. NeuroImage 2019; 196: 161-172.
- Jamadar SD, Ward PGD, Liang EX, et al. Metabolic and hemodynamic resting-state connectivity of the human brain: a high-temporal resolution simultaneous BOLDfMRI and FDG-fPET multimodality study. Cereb Cortex 2021; Feb 3: bhaa393.
- Volpi T, Vallini G, Silvestri E, et al. A new framework for metabolic connectivity mapping using bolus [18F]FDG PET and kinetic modelling. Biorxiv 2022; Dec.
- Kim SG and Ogawa S. Biophysical and physiological origins of blood oxygenation level-dependent fMRI signals. J Cereb Blood Flow Metab 2012; 32: 1188-1206.
- Henriksen OM, Vestergaard MB, Lindberg U, et al. Interindividual and regional relationship between cerebral blood flow and glucose metabolism in the resting brain. J Appl Physiol (1985) 2018; 125: 1080-1089.
- Noble S, Scheinost D and Constable RT. A decade of test-retest reliability of functional connectivity: a systematic review and meta-analysis. NeuroImage 2019; 203: 116157.
- Maquet P, Dive D, Salmon E, et al. Reproducibility of cerebral glucose utilization measured by PET and the
- [18F]-2-fluoro-2-deoxy-d-glucose method in resting, healthy human subjects. Eur J Nucl Med 1990; 16: 267-273.
- Rebelos E, Bucci M, Karjalainen T, et al. Insulin resistance is associated with enhanced brain glucose uptake during euglycemic hyperinsulinemia: a Large-Scale PET cohort. Diabetes Care 2021; 44: 788-794.
- Biessels GJ and Despa F. Cognitive decline and dementia in diabetes mellitus: mechanisms and clinical implications. Nat Rev Endocrinol 2018; 14: 591-604.
- Goyal MS and Snyder AZ. Uncoupling in intrinsic brain activity. Proc Natl Acad Sci USA 2021; 118: e2110556118.
- Elam JS, Glasser MF, Harms MP, et al. The human connectome project: a retrospective. NeuroImage 2021; 244: 118543.
- Casey BJ, Cannonier T, Conley MI, et al. The adolescent brain cognitive development (ABCD) study: Imaging acquisition across 21 sites. Dev Cogn Neurosci 2018; 32: 43-54.
- Miller KL, Alfaro-Almagro F, Bangerter NK, et al. Multimodal population brain imaging in the UK biobank prospective epidemiological study. Nat Neurosci 2016; 19: 1523-1536.
- Gunn RN and Rabiner EA. PET neuroimaging: the elephant unpacks his trunk. NeuroImage 2014; 94: 408-410.
- Cecchin D, Palombit A, Castellaro M, et al. Brain PET and functional MRI: why simultaneously using hybrid PET/MR systems? Q J Nucl Med Mol Imaging 2017; 61: 345-359.
- Karlberg AM, Sæther O, Eikenes L, et al. Quantitative comparison of PET performance -siemens biograph mCT and mMR. EJNMMI Phys 2016; 3: 5.
- Brix G, Zaers J, Adam LE, et al. Performance evaluation of a whole-body PET scanner using the NEMA protocol. National electrical manufacturers association. J Nucl Med 1997; 38: 1614-1623.
- Potvin O, Khademi A, Chouinard I, CCNA group, et al. Measurement variability following MRI system upgrade. Front Neurol 2019; 10: 726.
- Chen JE, Lewis LD, Chang C, et al. Resting-state 'physiological networks. NeuroImage 2020; 213: 116707.
- Hamberg LM, Hunter GJ, Alpert NM, et al. The dose uptake ratio as an index of glucose metabolism: useful parameter or oversimplification? J Nucl Med 1994; 35: 1308-1312.
- Bertoldo A, Rizzo G and Veronese M. Deriving physiological information from PET images: from SUV to compartmental modelling. Clin Transl Imaging 2014; 2: 239-251.
- Huisman MC, van Golen LW, Hoetjes NJ, et al. Cerebral blood flow and glucose metabolism in healthy volunteers measured using a high resolution PET scanner. EJNMMI Res 2012; 2: 63.
- Fan AP, An H, Moradi F, et al. Quantification of brain oxygen extraction and metabolism with [15O]-gas PET: a technical review in the era of PET/MRI. NeuroImage 2020; 220: 117136.

- Vaishnavi SN, Vlassenko AG, Rundle MM, et al. Regional aerobic glycolysis in the human brain. Proc Natl Acad Sci U S A 2010; 107: 17757-17762.
- Meikle SR, Sossi V, Roncali E, et al. Quantitative PET in the 2020s: a roadmap. Phys Med Biol 2021; 66: 06RM01.
- Garrett DD, Kovacevic N, McIntosh AR, et al. Blood oxygen Level-Dependent signal variability is more than just noise. J Neurosci 2010; 30: 4914-4921.
- Amor TA, Russo R, Diez I, et al. Extreme brain events: higher-order statistics of brain resting activity and its relation with structural connectivity. EPL 2015; 111: 68007.
- Omidvarnia A, Mesbah M, Pedersen M, et al. Range entropy: a bridge between signal complexity and selfsimilarity. Entropy (Basel) 2018; 20: 962.
- Deng L, Sun J, Cheng L, et al. Characterizing dynamic local functional connectivity in the human brain. Sci Rep 2016; 6: 26976.
- Hellyer PJ, Barry EF, Pellizzon A, et al. Protein synthesis is associated with high-speed dynamics and broad-band stability of functional hubs in the brain. NeuroImage 2017; 155: 209-216.
- Pedersen M, Omidvarnia A, Walz JM, et al. Spontaneous brain network activity: analysis of its temporal complexity. Netw Neurosci 2017; 1: 100-115.