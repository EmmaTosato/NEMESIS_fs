*[picture on PDF page 1]*

Contents lists available at ScienceDirect

### Computers in Biology and Medicine

journal homepage: www.elsevier.com/locate/compbiomed

### Pre-stimulus neural dynamics predict TMS responses: The role of fractal dimension and oscillatory activity

*[picture on PDF page 1]*

A.L. Bisogno a , S. Moaveninejad b , M. Corbetta a,c,d , C. Porcaro a,b,e,f,*

*[picture on PDF page 1]*

*[picture on PDF page 1]*

- a Department of Neuroscience and Padova Neuroscience Center, University of Padova, Padova, Italy
- b Biomedical Engineering Research to Advance and Innovate Translational Neuroscience (BRAIN Unit), Department of Neuroscience, University of Padova, Italy
- c *Veneto Institute of Molecular Medicine (VIMM), Padova, Italy*
- d *Azienda Ospedaliera Universit* ` *a di Padova, Padova, Italy*
- e Institute of Cognitive Sciences and Technologies (ISTC) -National Research Council (CNR), Rome, Italy
- f Centre for Human Brain Health and School of Psychology, University of Birmingham, Birmingham, United Kingdom

### A R T I C L E  I N F O

Keywords: TMS-EEG Pre-stimulus Gamma band Fractal dimension

TEPs

## 1. Introduction

The human brain operates at the intersection of stability and flexibility, a balance governed by criticality [1 -3]. Criticality is a concept derived from complex systems theory and refers to a state near a phase transition where systems exhibit maximal adaptability, computational efficiency,  and  scale-free  dynamics.  In  neuroscience,  this  framework provides a powerful lens for understanding how neural networks balance  segregation  and  integration  to  support  cognition  and  behavior. Deviations from criticality have been linked to several neurological and

### A B S T R A C T

*Background and objectives:* The brain operates near 'criticality ' balancing stability and adaptability for optimal function. Deviations from this state alter brain responses or signal neurological disorders. TMS-EEG is a powerful tool for studying criticality. In this study, we investigate how pre-stimulus features of activity (power) and signal complexity influence the amplitude of stimulus-related TMS evoked potentials (TEPs).

**Materials and methods**: We used a publicly available TMS-EEG dataset from 20 healthy individuals. TMS was applied to the left primary motor area (M1). We analyzed pre-stimulus features to measure power across frequency bands and Higuchi ' s Fractal Dimension (HFD), a measure of signal complexity. We examined the relationship between pre-stimulus estimated features and post-stimulus TEP amplitude across trials using machine learning.

Results: Stronger TEPs were measured when pre-stimulus activity contained lower gamma power and higher alpha power. Interestingly, lower pre-stimulus fractal dimension values, reflecting less complex baseline activity, were associated with increased TEP amplitudes. Partial correlation analysis showed that HFD (R = 0.30) was the most influential feature in predicting post-stimulus TEP. Machine learning models provided accurate predictions of post-stimulus TEP using the pre-stimulus EEG features (R 2 = 0.6867).

Discussion: Our  findings  are  consistent  with  the  brain  criticality  framework  highlighting  how  shifts  in  prestimulus TEP dynamics influence cortical responsiveness. Reduced gamma power and fractal dimension were associated with  stronger TEP  amplitudes,  suggesting  that  states closer to  order  optimize  responsiveness -conversely, higher gamma power and increased HFD, indicative of chaotic neuronal dynamics, dampened perturbation responses. The opposite effect of alpha power highlights the frequency-specific nuances of criticality, where inhibitory mechanisms may fine-tune responsiveness.

psychiatric disorders, highlighting their clinical relevance [4,5]. In brain criticality, Higuchi ' s Fractal Dimension (HFD) [6] provides a mean to assess how neural activity reflects scale-invariant dynamics in physiological [7 -9] and pathological conditions [10 -14].A higher HFD typically indicates greater complexity and variability in the signal, whereas lower values are usually related to reduced variability and stereotyped neural dynamics.

In  this  context,  transcranial  magnetic  stimulation  (TMS)  coupled with electroencephalography (EEG) offers a unique approach to study brain criticality by directly perturbing neural activity and capturing the *A.L. Bisogno et al.*

> * Corresponding author. Department of Neuroscience and Padova Neuroscience Center, University of Padova, Padova, Italy. *E-mail address:* camillo.porcaro@unipd.it (C. Porcaro).

*[picture on PDF page 1]*

*[picture on PDF page 1]*

*[picture on PDF page 1]*

resulting dynamics with high temporal precision. TMS-EEG recordings allow researchers to explore the current brain state by correlating TMSevoked potentials (TEPs) with the excitability and connectivity of neural circuits [15]. Evidence for the relationship between ongoing brain states and TEPs comes from studies examining TEPs during specific states such as sleep [16] and anesthesia, as well as in pathological conditions such as disorders of consciousness, stroke, and attention deficit hyperactivity disorder [17 -20]. TEPs are influenced by overarching changes in brain state and the ongoing variations in neuronal activity [21]. Cortical responses  to  TMS are not  fixed  but  are  dynamically  influenced  by  the intrinsic properties of the neural network at the moment of stimulation [22].  In  other  words,  state  dependence  may  account  for  substantial variability  in  activity  spread  after  perturbation.  Previous  work  has investigated the role of broadband phase and power on cortical excitability  using  motor-evoked  potentials  (MEPs)  and  TEPs  as  outputs. Recent  literature  has  focused  on  the  role  of  the  alpha  rhythm  and sensorimotor μ -oscillations  in  modulating  cortical  responses  of  the motor systems [23 -26]. The power of μ -alpha power in the stimulated sensorimotor cortex is related to increased TEP amplitude. This effect shows a stronger influence on early TEP components (P25 > N45 > P70 > N100). In contrast, this directly proportional effect of power in the contralateral (i.e, non-stimulated) sensorimotor cortex shows a stronger influence on late TEP components (P25 < N45 < P70) [23]. In addition, TMS applied at the negative peak of the μ -rhythm is associated with a greater amplitude of the evoked EEG potential at 100 ms post-stimulation,  as  compared  to  stimulation  applied  at  the  positive peak [24]. Recent work has considered the role of additional frequency bands in shaping responses to internal and external perturbations. For example, recent evidence from animal studies has shown that (spontaneous) broadband gamma oscillations in baseline or task-free conditions may reflect an increase in the overall level of circuit activity rather than synchronization between neurons [27,28]. Specifically, in mice lacking NMDAR activity in PV neurons, increased high-frequency power was associated with LFP oscillations and neuronal activity with decreased synchronicity [28]. In addition, gamma power spectral density (PSD) has been linked to in vivo measures of local excitatory/inhibitory (E/I) balance. E/I ratio can, in fact, be related to LFP-PSD slope in a range between 30 and 70 Hz. The predictive capacity of these features has been validated both across different species (i.e. rats and macaques) as well  as  under  pathological  conditions  (i.e.  administration  of  general anesthetics in macaques), tracking conscious state over time [29].

Based on these premises, this study focuses on analyzing the influence of both pre-stimulus power activity and fractal dimension, as an index of signal complexity, on the variability of the TEP response in the motor cortex. To address this issue, we first implement a descriptive approach that orders individual trials according to their pre-stimulus features,  independent  of  any  post-stimulus  measure.  Second,  we  test whether machine learning models can use the same features to provide an accurate estimate of perturbability using the evoked local field potential on the electrode under the stimulation and rank their predictive relevance. These results may help to establish robust EEG-derived biomarkers and improve TMS-based interventions to achieve behavioral changes in pathological conditions [30].

## 2. Materials and methods

### 2.1. Data acquisition

For this study, we take advantage of a publicly available TMS-EEG dataset.  This  dataset  has  been  extensively  described  by  Biabani  and colleagues [31] and the data are available for download from this repository:  https://doi.org/10.26180/5c0c8bf85eb24.  Specifically,  this dataset includes 20 right-handed healthy individuals between the ages of 18 and 40 years (24.50 ± 4.86 years; 14 females). EEG recordings were performed with the SynAmps2 EEG system (Neuroscan, Compumedics,  Australia)  from  62  TMS-compatible  Ag/AgCl-sintered  ring electrodes embedded in an elastic cap (EASYCAP, Germany). Electrodes were digitized  and co-registered  to  the  subject ' s  MRI  using  a  neuronavigation system (Brainsight ™ 2, Rogue Research Inc., Canada). TMS pulses were applied to the hand area of left M1, inducing consistent MEPs with the highest amplitude in the FDI muscle. A figure-of-eight coil  (C-B60)  connected  to  a  MagPro  X100 + Option  stimulator  (MagVenture, Denmark) was utilized.

Resting motor threshold (rMT) was determined as the minimum TMS intensity required to elicit MEPs > 50 μ V in at least 5 of 10 consecutive trials  (with  EEG  cap  on),  and  it  was  expressed  as  a  percentage  of maximum  stimulator  output  (%  MSO)  [22,32].  All  details  of  the experimental  design  and  acquisition  have  been  described  in  Biabani et al. [31] This specific study evaluated three different conditions: (i) 100 TMS pulses at an intensity of 120 % rMT over the left M1, (ii) 100 additional TMS pulses (at 120 % rMT) administered to the participants ' shoulder over the left acromioclavicular joint, (iii) 100 TMS pulses with the intensity of 80 % rMT over the left M1. We analyzed data for the first condition  (i.e.  suprathreshold  stimulation)  and  used  subthreshold stimulation (iii) as a control condition.

### 2.2. Data preprocessing

EEG recordings were analyzed using EEGLAB [33] and TESA [34] toolboxes. The precise pipeline for cleaning TMS-EEG data can be found in the supplementary methods of Biabani et al. [31,34]. All code for EEG processing and statistical analyses is available at https://github.com/ BMHLab/TEPs-PEPs, and all the preprocessed data can be downloaded from https://doi.org/10.26180/5c0c8bf85eb24.

### 2.3. Feature extraction

Two types of features were extracted: Higuchi ' s Fractal Dimension (HFD) [6] (time domain) and Power Spectrum Density PSD (frequency domain).

#### 2.3.1. Time domain features: HFD

HFD [6] is a widely used metric for quantifying fractal properties in time series data, providing a robust method for assessing the complexity and self-similarity of neural signals. HFD has been calculated according to the method proposed by Higuchi [6]. To compute HFD, the signal is first divided into multiple, smaller, consecutive segments ('windows ' ). HFD is then calculated individually for each segment (window) [9,10], and the **HFD values** obtained for each window are then averaged over all windows, encompassing the entire time series. In this study, HFD was computed using 600 ms windows extracted from the pre-stimulus interval ranging from 800 ms to 200 ms. This window was selected to isolate baseline activity before the onset of any stimulus-related neural dynamics. The resulting mean HFD value provides a quantitative measure of the complexity of the whole time series.

Formally, the signal is first discretized into multiple segments, each X (1), X(2), … , X(N) , where N is the total number of samples (data points). For each segment, a set k of new self-similar time series denoted as X k m is derived and is defined as follows:

X k m : X ( m ) , X ( m + k ) , X ( m + 2 k ) , … ., X ( m + int ( N k k ) k )

with m = 1, 2, … , k and k = 1, 2, kmax , and where both m and k are integers; m is the initial time and k is the time interval. kmax is a free tuning parameter, and int ( N k k ) is the integer part of the enclosed value.

For example, in the case of k = 4 and N = 100, four-time series are produced:

X 4 = X ( 1 ) , X ( 5 ) , X ( 9 ) , … , X ( 97 )

1 X 4 2 = X ( 2 ) , X ( 6 ) , … ., X ( 98 )

X 4 3 = X ( 3 ) , X ( 7 ) , … ., X ( 99 )

X 4 4 = X ( 4 ) , X ( 8 ) , … ., X ( 100 )

The length Lm ( k ) of each time series X k m is then calculated as:

Lm ( k ) = 1 k ⎛ ⎜ ⎜ ⎜ ⎜ ⎝ ∑ int ( N m k ) i = 1 ⃒ ⃒ ⃒ ⃒ ⃒ ⃒ ⃒ ( X ( m + ik ) X ( m +( i 1 ) k )|) ⎛ ⎜ ⎝ N 1 int ( N m k ) k ⎞ ⎟ ⎠

where the term ⎛ ⎜ ⎝ N 1 int ( N m k ) k ⎞ ⎟ ⎠ represents a normalizing factor. Therefore,

Lm ( k ) represents the normalized sum of the segment lengths which join pairs of points distant k samples, starting from the m-th sample, X(m).

Then,  the  length  of  the  curve  for  each  time  interval  k,  L(k),  is calculated as the mean of the k values Lm ( k ) for m = 1, 2, … k as:

L ( k ) = ∑ k m = 1 Lm ( k ) k

Then, an array of mean values L(k) is  produced,  and  the  HFD  is approximated as follows:

HFD = ln ( L ( k )) ln ( 1 k ) for k = 1 , 2 , . . ., kmax

The k value used to estimate the HFD was K = 50.[7]

The  HFD  on  the  pre-stimulus  values  obtained  for  each  trial  for channel C3 were ordered and divided into quartiles, which were then used to order the TEPs as first and then used as a feature for the machine learning analysis.

#### 2.3.2. Time domain features: DFA

We computed the Detrended Fluctuation Analysis (DFA) of our signal in the pre-stimulus interval as a control metric. First introduced by Peng et  al.  (1994),  DFA  is  a  robust  technique  for  identifying  long-range temporal  correlations  (LRTCs)  in  non-stationary  time  series.  As  it quantifies  scale  invariance  and  self-similarity  in  neural  signals  (two features indicative of systems operating near criticality), DFA can be used to assess whether brain activity exhibits critical dynamics, which are characterized by a balance between randomness and order. In our analysis, DFA was applied to the EEG time series. The procedure follows these steps: given a time series x ( i ) , i = 1 , 2 , ⋯ , N , the signal is first meancentered and integrated:

y ( k ) = ∑ k i = 1 ( x ( i ) x )

The integrated signal is divided into non-overlapping windows of length s . Within each window, a polynomial trend of order v , denoted y ( v ) s ( k ) ,  is  fitted  and  removed.  The  root-mean-square  fluctuation  is computed as:

F 2 v ( s ) = 1 s ∑ s k = 1 [ y (( v 1 ) s + k ) y ( v ) s ( k ) ] 2

The fluctuation function is then averaged across all segments Ns :

√

̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅̅ ̅

F ( s ) = 1 Ns ∑ Ns v = 1 F 2 v ( s ) √ √ √

A linear fit on the log-log plot of F ( s ) versus s yields the DFA scaling exponent α , where:

F ( s ) ∼ s α

The exponent α reflects  the degree of temporal correlation in the signal:

- ≈ 0 . 5: uncorrelated (white noise)
- 0 . 5 < α < 1: persistent LRTC
- α > 1: non-stationary processes with strong correlations

Although  mathematically  related  through  the  empirical  relation HFD = 3 α ,  DFA  and  HFD  capture  different  aspects  of  signal complexity. In our study, DFA was computed over the same pre-stimulus windows  as  HFD,  enabling  a  direct  comparison  of  their  predictive relationship  with  post-stimulus  TEP  variability.  Despite  this  mathematical connection, the two metrics capture different aspects of signal complexity. While HFD is more sensitive to local fluctuations and signal roughness, DFA emphasises long-range temporal correlations and scalefree dynamics. Consequently, we observed an inverse relationship between the two measures: signals characterised by higher HFD tended to exhibit lower DFA values, and vice versa. This opposing trend reflects their complementary sensitivity to different signal features, highlighting how the choice of complexity measure can influence the interpretation of  cortical  dynamics.  Notably,  both  HFD  and  DFA  were  significantly associated with variability in TEPs, suggesting that, despite responding in opposite directions, they both capture meaningful information related to the perturbability of the motor cortex. The full results of the DFA analysis are provided in the Supplementary Material (Fig. S1) and are briefly discussed in the main text.

#### 2.3.3. Frequency-domain features: PSD

We calculated single-trial PSDs using a Morlet wavelet with a constant parameter of seven, which provides the best compromise between time and frequency resolution.

The pre-stimulus PSD on channel C3 was obtained by integrating the pre-stimulus  activity  between 800  ms  and 200  ms  after  Morlet wavelet transform on the classical frequency bands, such as delta (1 -3 Hz),  theta  (4 -7  Hz),  alpha  (8 -13 Hz), beta (14 -30 Hz), and gamma (31 -90 Hz) bands. The PSD on the pre-stimulus values for each band and each trial on channel C3 were ordered and divided into quartiles, which were then used to order the TEPs first and then as features for the machine learning analysis.

### 2.4. Statistical analysis

A  point-by-point  two-sample  permutation t -test  (10,000  permutations; p < 0.01) was performed between post-stimulus Q1 and Q4 were performed,  and  a  false  discovery  rate  (FDR)  was  used  to  correct  for multiple comparisons [35].

The TEP was quantified using the evoked local field power (eLFP), defined as the area under the absolute post-stimulus EEG signal from the C3 electrode. For each trial, the signal was extracted from 15 ms to 600 ms post-stimulus (corresponding to samples 1015 to 1600 at a 1 kHz sampling rate), rectified (i.e., converted to absolute values), and integrated  numerically.  This  corresponds  to  summing  the  absolute  EEG values across the post-stimulus time window:

eLFPi ≈ ∑ 1600 j = 1015 ⃒ ⃒ xi t j )⃒ ⃒

Where:

- xi t j ) is the EEG signal from the C3 electrode at time t j for trial i ,
- t j discrete time points in milliseconds after the TMS pulse,
- i indexes the individual trials.

A partial correlation analysis was performed to examine the direct relationships between each pair of variables (delta, theta, alpha, beta, gamma, HFD and eLFP) while controlling for the influence of all other variables in the dataset. This analysis estimates the correlation between two variables while statistically removing the effect of the remaining variables. Before analysis, all variables were standardized (z-scored) to ensure  comparability  and  to  reduce  the  influence  of  differences  in measurement scales.

### 2.5. Machine learning based prediction

We  implemented  a  two-step  prediction  pipeline  to  evaluate  the predictive ability of different machine learning models. In the first step, the HFD was predicted using delta, theta, alpha, beta and gamma features estimated from the pre-stimulus TEP. In the second step, the predicted HFD and the original power band features were used to predict the eLFP computed in the post-stimulus TEP between 15 ms and 600 ms. The data set was divided into an 80 % training set and a 20 % test set for both  prediction  tasks.  We  evaluated  a  variety  of  machine  learning models,  including  ensemble  models  (RandomForestRegressor,  BaggingRegressor,  and  GradientBoostingRegressor)  and  other  regressors (XGBRegressor, LGBMRegressor, Support Vector Regressor (SVR), and Multi-Layer Perceptron Regressor (MLPRegressor)). The analysis consisted  of  three  main  steps.  First,  baseline  model  evaluation  was  performed by training each model with default parameters and assessing performance using the R 2 score and Mean Squared Error (MSE) on the test set. Second, hyperparameter optimisation was performed using grid search  with  5-fold  cross-validation  to  identify  the  optimal  hyperparameters  for  each  model,  after  which  the  best-performing  models were re-evaluated on the test set. Finally, ensemble learning techniques were used to improve prediction accuracy through model fusion further. Two  approaches  were  explored:  (1)  a  voting  regressor,  which  used weighted  averaging  to  combine  predictions  from  multiple  models, optimizing  the  weights  to  ensure  that  the  most  accurate  models contributed more to the final prediction, and (2) a stacking regressor, where outputs from the base models were fed into a final ridge regression estimator to refine predictions and improve accuracy.

## 3. Results

### 3.1. Effects of pre-stimulus HFD on post-stimulus TEPs

We  investigated whether TMS-evoked potentials after suprathreshold stimulation (i.e. 120 %) of the primary motor cortex (M1) differed according to pre-stimulus HFD values. The single trials of all the subjects were ordered by the HFD estimated on the pre-stimulus TEP (from 800 ms to 200 ms). Fig. 1 shows the differences between the averaged first (Q1) and last (Q4) quartiles of trials. HFD values showed a strong discriminative ability across quartiles with an inverse relationship with post-stimulus TEP (i.e. higher pre-stimulus HFD determined smaller TEPs). These results were confirmed by an inverse relationship when DFA values were assessed (Fig. S1). Again, although the amplitude was significantly reduced, the profile of well-established peaks following  sensorimotor  cortex  stimulation  was  maintained.  We  also calculated the percentage of trials falling into each HFD quartile at a single-subject level. In the first and last quartiles, 30 % of subjects presented less than 10 % of the trials, showing only modest intra-individual discriminative ability (See Supplementary Table S1 ).

### 3.2. Effects of pre-stimulus power bands on post-stimulus TEPs

We further investigated whether the amplitude of TMS-evoked potentials  after  supra-threshold stimulation (i.e. 120 %) of the primary motor cortex (M1) differed as a function of the pre-stimulus TEP power. Specifically,  we  examined  the  effect  of  the  power  across  frequency bands: delta (1 -3 Hz), theta (4 -7 Hz), alpha (8 -13 Hz), beta (14 -30 Hz), and gamma (31 -90 Hz). Single trials were concatenated across subjects and ordered by power in each frequency band. Fig. 2 shows the differences between the first (Q1) and last (Q4) quartiles of trials for each frequency  band.  All  frequency  bands  showed  discrimination  across quartiles, with the best results in the gamma band. In addition, power at all frequencies, except alpha power, showed an inverse relationship with post/stimulus  TEP  (i.e.  higher  pre-stimulus  delta,  theta,  beta,  and gamma determined smaller TEPs) (Fig. 2). These results were confirmed in the subthreshold stimulation condition despite a significantly reduced signal-to-noise ratio (see Supplementary Fig. S2). We also performed a control analysis of the TMS-evoked response in an electrode distant from the  stimulation  site  (i.e.  O2).  As  expected,  we  found  that  the  prestimulus  brain  state  had  only  a  minimal  influence  on  this  response compared to our test condition (see Supplementary Fig. S3).

Interestingly, although significantly reduced in amplitude, the profile of the well-established peaks following sensorimotor cortex stimulation was maintained in all conditions (i.e. P60, N100) [36]. To assess whether  this  specific  phenomenon  could  describe  both  inter-  and intra-individual variability in TEPs following left primary motor cortex stimulation,  we  calculated  the  percentage  of  trials  falling  into  each quartile at the individual subject level. This was repeated for each frequency band. Interestingly, in the first quartile, 5 % of subjects presented less than 10 % of trials in the delta frequency band, 10 % in the theta band, 25 % in the alpha band, 30 % in the beta band, and 15 % in the gamma band. In the last quartile 5 % of subjects presented less than 10 % of trials in the delta frequency band, 15 % in the theta band, 35 % in the alpha band, 35 % in the beta band, and 10 % in the gamma band. Overall, the percentages of trials classified based on delta, theta and gamma power showed the lowest intra-individual variability (See Supplementary Table S2 ).

*[picture on PDF page 4]*

**Figure labels:**
- Q1: Low FD
- Q1
- Q4
- FD: Q1 vs. Q4
- Q4: High FD
- 15
- PFDR<0.01
- TEP
- 0
- -18
- -200
- 200
- 400
- 600
- 200 400
- Time (ms)

*[picture on PDF page 5]*

**Figure labels:**
- Q1
- Q4
- Delta: Q1 vs. Q4
- 10
- Q1: Low D
- 二
- Q4: High D
- TEP
- 0
- PFDR<0.01
- 15
- -15
- -200
- 200
- 400
- 600
- Theta: Q1 vs. Q4
- Q1: Low T
- Q4: High T
- Alpha: Q1 vs. Q4
- Q1: Low A
- Q4: High A
- Beta: Q1 vs. Q4
- Q1: Low B
- Q4: High B
- Gamma: Q1 vs. Q4
- Q1: Low G
- Q4: High G
- -18
- Time (ms)

### 3.3. Partial correlation between features

**The partial correlation matrix presented in** Fig. 3 shows the R value for the correlation between each feature (delta, theta, alpha, beta, gamma, HFD and eLFP). Non-significant R values at p < 0.001 were set  to  zero. HFD (R = 0.30)  and  theta  power  (R = 0.29) emerged as the most influential features in predicting eLFP of the poststimulus TEP, with their negative correlations suggesting that higher pre-stimulus HFD and theta power are associated with lower eLFP . This highlights  their  role  in  shaping  the  neural  response  to  stimulation, particularly in modulating cortical excitability and signal complexity before  TMS application. Beta (R = 0.24)  and  gamma (R = 0.19) power showed weaker correlations, suggesting a less direct but relevant influence  on  post-stimulus  dynamics.  In  addition,  a  strong  negative correlation between alpha power and HFD (R = 0.55) indicates that higher alpha activity is associated with reduced signal complexity. In contrast, a positive correlation between gamma power and HFD (0.48) strengthens  the  link  between  high-frequency  oscillations  and  neural OptimizedStackingModel complexity.

*[picture on PDF page 6]*

**Figure labels:**
- Partial Correlation Heatmap
- 1
- delta
- -0.1342
- 0.8
- 0.6
- theta
- -0.2447
- -0.2909
- 0.4
- alpha
- 0.2132
- -0.5514
- Features
- 0.2
- beta
- 0.2085
- -0.2379
- 0
- -0.2
- gamma
- 0.4801
- -0.1858
- -0.4
- HFD
- -0.2978
- -0.6
- -0.8
- eLFP
- -1

### 3.4. Prediction of pre-stimulus HFD using pre-stimulus power band oscillations

We used pre-stimulus power bands (delta, theta, alpha, beta, and gamma) to predict pre-stimulus HFD . The best performing model was  the Stacking  Regressor with optimized  hyperparameters , following  the  steps  described  in  Section  2.5.  The  stacking  approach outperformed the individual models, achieving the highest R 2 score and the lowest normalized Mean Squared Error (nMSE) , demonstrating its effectiveness in capturing nonlinear dependencies between EEG frequency  bands  and  HFD.  Fig.  4a  illustrates  the  performance  of  the optimized **Stacking Regressor** in  predicting  H FD from pre-stimulus EEG power bands. The model achieved a high R 2 value of 0.7092 , indicating  strong  predictive  capability,  with  most  predicted  values closely following the ideal line of fit. The scatter plot shows a welldefined  correlation between  actual and  predicted HFD  values, demonstrating  that  the  model  effectively  captures  the  nonlinear  dependencies between EEG frequency features and HFD.

*[picture on PDF page 6]*

**Figure labels:**
- R²:0.7092, Normalized-MSE: 0.2908
- Feature Importance for HFD using Mutual Information
- 1.8
- Predictions
- Ideal Fit
- 0.35
- 1.7
- 0.30
- Predicted HFD Values
- 1.6
- Score
- 0.25
- 1.5
- Importance
- 0.20
- 1.4
- 0.15
- 1.3
- 0.10
- 0.05
- 1.2
- 0.00
- 1.1
- Actual HFD Values
- Alpha
- Theta
- Beta
- Delta
- Gamma
- (a)
- (b)

#### 3.4.1. Machine learning analysis of pre- and post-stimulus TEP

Multiple regression models were evaluated to predict the eLFP poststimulus TEP of the motor cortex. Among the individual models, the best performance was achieved by the **Optimized GBR** (R 2 = 0.6867, nMSE = 0.3130), closely followed by the **Optimized Voting Regressor** (R 2 ¼ 0.6869,  nMSE ¼ 0.3131) .  Each  model  underwent hyperparameter tuning using **Grid Search with 5-fold cross-validation** to find the optimal settings. An optimized voting regressor was implemented, combining predictions from the best-performing models using weighted averaging (see Supplementary Table S3 for a summary of the model performance). Fig. 5a illustrates  the performance of  the optimized Voting Regressor in predicting the eLFP using pre-stimulus EEG features (delta, theta, alpha, beta, gamma and HFD). Using ensemble learning through weighted averaging ,  the Voting Regressor slightly outperformed individual models, including **GBR (R** 2 ¼ 0.6867) and **XGBoost (R** 2 ¼ 0.6840) .

#### 3.4.2. Feature importance analysis

To determine the most influential features in predicting the eLFP, we applied  a Mutual  Information  (MI)  method .  MI  quantifies  the dependence  between  input  features  and  the  target  variable  while capturing both linear and nonlinear relationships. Fig. 4b and 5b show the ranked importance of each feature, with gamma emerging as the most  significant  predictor  ( MI  score ¼ 0.547 ),  followed  by beta (0.184) and HFD  (0.179) .  However,  the  MI  does  not  consider  the redundancy between features.

##### Optimized Voting Model (Best Weights) R²: 0.6869, Normalized-MSE: 0.3131

Predictions

Ideal Fit

2000

Predicted eLFP Values

8000

6000

4000

2000

4000

Actual eLFP Values

(a)

## 4. Discussion

We investigated how pre-stimulus power across multiple frequency bands and Higuchi ' s fractal dimension affect the individual TMS-evoked potential response following stimulation of the primary motor cortex (M1).

### 4.1. Fractal dimension as a measure of criticality in TMS-EEG

Our results showed an inverse relationship between the HFD of prestimulus  neural  dynamics  and  TMS-evoked  potentials  (TEPs).  Specifically, lower pre-stimulus HFD values were associated with larger poststimulus TEP amplitudes, whereas higher HFD values corresponded to smaller eLFP (Fig. 1).

This  finding  provides  new  insights  into  the  dynamic  role  of  prestimulus neural states in shaping the brain ' s response to external perturbations. In the context of criticality, our results suggest that a less complex pre-stimulus state, as indicated by reduced HFD, may correspond to a brain state closer to an ordered state. This ordered state may enhance  the  brain ' s  responsiveness  to  perturbations,  as  reflected  in larger  post-stimulus  TEP  amplitudes.  Conversely,  higher  HFD,  indicating a more chaotic pre-stimulus state, may represent a dynamic closer to criticality, where the system is less responsive but maintains a balance between integration and segregation of neural activity [37,38]. These findings  were  also  confirmed  when  the  DFA  values  at  baseline  were evaluated.

The  observed  inverse  relationship,  i.e.  lower  HFD,  higher  poststimulus  TEP  amplitudes,  is  consistent  with  theoretical  models  suggesting that brain responsiveness depends on the interplay between prestimulus neural complexity and external inputs [39 -41].A low HFD state may  reduce  internal  noise,  allowing  for  a  stronger,  more  coherent response to TMS. On the other hand, a high HFD state, characterized by scale-invariant dynamics, may buffer external perturbations, leading to attenuated TEPs [42,43]. This dynamic trade-off between responsiveness and stability may reflect a fundamental property of neural systems poised  near  criticality.  Our  findings  are  consistent  with  previous research showing that pre-stimulus neural states influence evoked responses.  HFD  studies  have  associated  higher  fractal  complexity  with greater neural variability and adaptability [44,45]. However, our work

*[picture on PDF page 7]*

**Figure labels:**
- Feature Importance for eLLFP using Mutual Information
- 0.5
- Importance Score
- 0.4
- 0.3
- 0.2
- 0.1
- 0.0
- Beta
- HFD
- Alpha
- Theta
- Delta
- Gamma
- (b)

6000

8000

*A.L. Bisogno et al.*

extends these findings by highlighting the specific role of pre-stimulus HFD  in  modulating  post-stimulus  TEP  amplitudes  while  providing  a direct link between the critical state measured by fractal dimension and the response to perturbation. Understanding the relationship between pre-stimulus HFD and TEPs may have significant implications for clinical  applications  of  TMS-EEG.  Deviations  from  the  observed  inverse relationship could serve as biomarkers for disorders characterized by altered criticality, such as epilepsy, depression, or schizophrenia [46, 47].

### 4.2. Relationship between pre-stimulus features and TMS-evoked potentials

Our results indicate that pre-stimulus gamma power had the strongest discriminative ability among frequency bands in predicting poststimulus TEP amplitude, with higher gamma power being associated with  reduced  TEP  amplitude.  This  inverse  relationship,  which  was observed for all frequencies except for the alpha range (8 -12 Hz), suggests that lower pre-stimulus gamma power correlates with a greater cortical  response  to  stimulation.  Partial  correlation  analysis  further confirmed  significant  inverse  relationships  between  theta,  beta,  and gamma power with post-stimulus TEP amplitude in the motor cortex (Fig. 2).

These  findings  are  consistent  with  previous  research  on  cortical excitability using motor-evoked potentials (MEPs). It has been proposed that alpha oscillations, primarily originating from primary sensory regions (S1), exert rhythmic inhibition on S1, resulting in a disinhibition of M1, thereby modulating sensorimotor excitability [48,49]. This effect appears to be state-dependent, occurring during open-eyes conditions but not during closed-eyes recordings [50,51]. Our results are consistent with  this  framework,  as  sensorimotor μ -alpha  power  showed  a  progressive modulation from early to late TEP components (P25 > N45 > P70 > N100), supporting previous findings [50].

Interestingly,  gamma  power  showed  an  inverse  relationship  with TEP amplitude following motor cortex stimulation. While gamma oscillations are often associated with cortical excitability [52], recent evidence suggests that under task-free conditions, gamma activity may be related to increased randomic neural activation circuit activity rather than effective neuronal synchronization [52]. This interpretation suggests that reduced pre-stimulus gamma power may indicate a state of reduced neural activity  synchronization,  thereby  facilitating  stronger TMS-evoked responses. Furthermore, intra-individual variability analysis showed that delta, theta, and gamma bands had the most stable trial distributions,  suggesting  their  central  role  in  determining  individual cortical responses to TMS. It is important to note that EEG signals in the gamma range  are  susceptible  to  muscular  artifacts,  requiring  robust pre-processing  techniques  [53,54].  Although  our  analysis  focused  on TEP  amplitudes  recorded  at  C3,  minimizing  contamination  by  scalp muscle activity, future studies should investigate whether the observed inverse relationship between pre-stimulus gamma power and TEPs extends beyond the sensorimotor cortex. This would be particularly relevant  given  that  pre-stimulus  alpha  power  has  been  shown  to  have opposite  effects  on  excitability  depending  on  the  cortical  region, enhancing motor cortex excitability while suppressing visual cortex responses [55].

### 4.3. Relationship between HFD and power band oscillations

Machine  learning  models  incorporating  pre-stimulus  power bands (delta, theta, alpha, beta, and gamma) were able to predict pre-stimulus HFD with high accuracy. Correlation analysis revealed a strong  inverse  relationship  between  alpha  power  HFD  (R = 0.55), suggesting  that  increased  alpha  activity  is  associated  with  reduced neural  complexity.  Alpha  oscillations  are  commonly  associated  with cortical  inhibition  and  functional  segregation,  which  may  suppress neural variability and contribute to a more stable brain state [56,57].

Conversely, a positive correlation between gamma power and HFD (R = 0.48) suggests that higher gamma activity is associated with increased neural complexity, reinforcing the role of high-frequency oscillations in increasing circuit activity rather than effective neuronal synchronization [57].

Theta (R = 0.29)  and  beta  (R = 0.24) power showed weaker correlations with HFD, suggesting that their influence on pre-stimulus complexity  is  less  pronounced.  Theta  activity,  often  associated  with large-scale  network  synchronization  and  inhibitory  control  [58,59], may  contribute  to  reduced  fractal  complexity  by  promoting  stable oscillatory dynamics. Beta oscillations, associated with motor control and cognitive processing, may have a more localized effect on neural variability.

### 4.4. Machine learning analysis and feature importance

The  machine  learning  analysis  further  supports  these  findings  by demonstrating that  pre-stimulus  TEP  features  can  be  used  to  predict post-stimulus TEP amplitude. *Feature importance analysis* using Mutual Information (MI) revealed that gamma power was the most influential predictor (**MI score** = 0.547), followed by beta power (0.184) and **HFD (0.179)**. This finding highlights the important role of high frequency oscillations  and  signal  complexity  in  shaping  the  post-stimulus  TEP response. The prominence of gamma power as a predictor is consistent with  its  role  in  local  circuit  excitability  and  neural  integration,  suggesting that pre-stimulus gamma activity may be a key modulator of the brain ' s response to TMS perturbation [57]. Although HFD ranked lower in the MI analysis, its consistent negative correlation with the eLFP (R = 0.30) suggests that it contributes to shaping cortical excitability by regulating the variability and predictability of neural states.

Interestingly, MI does not account for redundancy between features, meaning that the contribution of HFD, theta, and beta power to the TEP may be interdependent. The strong correlations between power bands and HFD suggest that oscillatory activity and fractal dynamics jointly influence cortical excitability before stimulation. Future studies employing  advanced  feature  selection  techniques,  such  as  recursive feature elimination or deep learning models, may help disentangle these complex  interactions and  refine predictive  models  for  TMS-EEG responses.

### 4.5. Implications and future directions

These findings provide a robust framework for understanding how pre-stimulus neural complexity and oscillatory dynamics shape cortical excitability.  By  integrating  traditional  correlation  analyses  with  machine learning-based feature importance ranking, we show that HFD, beta, and gamma power all contribute to the prediction of post-stimulus TEP responses, with gamma emerging as the most influential predictor.

Our results suggest that there is a non-additive interaction between pre-stimulus and post-stimulus brain activity. This finding is consistent with recent literature investigating the interplay between spontaneous and task-evoked activity [60 -62] as well as the role of resting-state activity in modulating consciousness [63]. Specifically, we demonstrate that  susceptibility  to  TMS  is  influenced  by  non-linear  integration  of ongoing neural inputs and that criticality measures may be essential for characterising this non-additive dynamic. Future studies could directly compare TMS-evoked and task-evoked responses, such as stimulating the M1 hand area alongside matched motor tasks, to better understand this relationship. Furthermore, the phase of the signal across different frequency bands should be examined in detail to understand the effect of external stimuli [64].

Importantly, these findings have potential clinical relevance, particularly  in  neurological  and  psychiatric  disorders  where  cortical excitability  is  altered  (e.g.,  epilepsy,  depression,  schizophrenia,  and stroke  rehabilitation).  If  HFD  and  power  band  features  can  serve  as biomarkers for individualized TMS responses, this could pave the way *A.L. Bisogno et al.*

for personalized neuromodulation protocols that optimize stimulation based on pre-stimulus brain states. Extending these analyses to different cortical  regions  may  further  refine  our  understanding  of  how  prestimulus  neural  complexity  modulates  TMS-induced  plasticity.  An important limitation of our study concerns signal pre-processing, specifically the use of ICA to remove muscle artifacts. This procedure may have  influenced  early  responses,  and  future  studies  should  consider employing SSP-SIR or simplifying the processing pipeline [65,66]. In addition, only considering the local field power of the evoked response is too simplistic and future studies should address the prediction of specific peaks (i.e. P60 for glutamatergic and N45 for GABAergic activity) [64] or  additional  well-established  TMS-EEG  features  (i.e.  number  of  deflections, natural frequency of stimulation) [67]. Finally, the integration with functional connectivity analyses and non-linear dynamical modelling could provide deeper insights into the mechanisms underlying TMS-EEG interactions in health and disease.

## 5. Conclusion

This study highlights the important role of pre-stimulus neural dynamics, specifically power spectral density (PSD) bands and Higuchi ' s Fractal Dimension (HFD), in shaping the brain ' s response to transcranial magnetic stimulation (TMS). The inverse relationship between gamma power, HFD and TEPs suggests that greater neural complexity stabilizes cortical  excitability  and  reduces  responsiveness  to  external  perturbations. By combining correlation analysis and machine learning, we show that HFD, gamma, and beta power significantly predict post-stimulus TMS responses, reinforcing the role of criticality in modulating brain reactivity.

Collectively,  these  findings  may  provide  valuable  insights  into neurodegenerative pathologies such as Alzheimer ' s disease, Parkinson ' s disease, and amyotrophic lateral sclerosis (ALS), where disturbances in criticality and brain dynamics are well-documented [68]. Reduced HFD in these conditions has been associated with impaired neural complexity and reduced information processing, which may correlate with altered cortical responsiveness to external perturbations such as TMS. In addition,  HFD and oscillatory features may serve as biomarkers for optimizing neuromodulatory interventions in conditions such as stroke or psychiatric disorders.

### CRediT authorship contribution statement

A.L. Bisogno: Writing -review & editing, Writing -original draft, Data curation. S. Moaveninejad: Writing -review & editing, Formal analysis, Data curation. M. Corbetta: Writing -review & editing, Supervision, Funding acquisition. C. Porcaro: Writing -review & editing, Writing -original draft, Supervision, Methodology, Funding acquisition, Formal analysis, Data curation, Conceptualization.

### Ethics statement

This study does not require ethical approval as it exclusively utilizes publicly available open-access data. No new human or animal subjects were involved in the research. The dataset used in this study can be accessed at https://doi.org/10.26180/5c0c8bf85eb24.

### Funding

MC was supported by the Italian Ministry of Health for ' Brain connectivity measured with high-density electroencephalography: a novel neurodiagnostic tool for stroke ' (NEUROCONN; RF-2018-1236689) and ' Eye-movement dynamics during free viewing as biomarker for assessment  of  visuospatial  functions  and  for  closed-loop  rehabilitation  in stroke ' (EYEMOVINSTROKE; RF-2019-12369300); European Research Executive  Agency  (REA)  (Grant  No.  860563) ' European  School  of Network Neuroscience (euSNN) ' ; Horizon 2020 SC5-2019-2 (Grant No.

869505) ' Visionary nature based Actions for enhancing Resilience in Cities (VARCITIES) ' ; HORIZON-ERC-SyG (Grant No.101071900) ' Neurological Mechanisms Of Injury And Sleep-Like Cellular Dynamics (NEMESIS) ' ;  HORIZON-  INFRA-2022  SERV  (Grant  No.  101147319) ' EBRAINS 2.0: A Research Infrastructure to Advance Neuroscience and Brain  Health ' .  ALB  and  CP  were  supported  by  HORIZON-ERC-SyG (Grant  No.101071900) ' Neurological Mechanisms  of Injury  And Sleep-Like Cellular Dynamics (NEMESIS) ' . CP and SM were supported by PRIN Grant No. MUR 20228ARNXS.

### Declaration of competing interest

The authors declare that they have no known competing financial interests or personal relationships that could have appeared to influence the work reported in this paper.

### Appendix A. Supplementary data

**Supplementary data** to this article can be found online at https://doi. org/10.1016/j.compbiomed.2025.111220.

### References

- J. O ' Byrne, K. Jerbi, How critical is brain criticality? Trends Neurosci. 45 (11) (Nov. 2022) 820 -837, https://doi.org/10.1016/J.TINS.2022.08.007.
- S. Safavi, M. Chalk, N.K. Logothetis, A. Levina, Signatures of criticality in efficient coding networks, Proc. Natl. Acad. Sci. U. S. A. 121 (41) (Oct. 2024), https://doi. org/10.1073/PNAS.2302730121.
- Y. Tian, et al., Theoretical foundations of studying criticality in the brain, Network Neuroscience 6 (4) (Oct. 2022) 1148 -1185, https://doi.org/10.1162/NETN_A_ 00269.
- K. Heiney, et al., Criticality, connectivity, and neural disorder: a multifaceted approach to neural computation, Front. Comput. Neurosci. 15 (Feb. 2021) 611183, https://doi.org/10.3389/FNCOM.2021.611183/BIBTEX.
- A. Palutla, S. Seth, S.S. Ashwin, M. Krishnan, Criticality in Alzheimer ' s and healthy brains: insights from phase-ordering, Cogn Neurodyn 18 (4) (Aug. 2024) 1789 -1797, https://doi.org/10.1007/S11571-023-10033-5.
- T. Higuchi, Approach to an irregular time series on the basis of the fractal theory, Physica D 31 (2) (Jun. 1988) 277 -283, https://doi.org/10.1016/0167-2789(88) 90081-4.
- M. Marino, et al., Neuronal dynamics enable the functional differentiation of resting state networks in the human brain, Hum. Brain Mapp. 40 (5) (Apr. 2019) 1445 -1457, https://doi.org/10.1002/HBM.24458.
- S. Kesi ´ c, S.Z. Spasi ´ c, Application of Higuchi ' s fractal dimension from basic to clinical neurophysiology: a review, Comput. Methods Progr. Biomed. 133 (Aug. 2016) 55 -70, https://doi.org/10.1016/J.CMPB.2016.05.014.
- C. Porcaro, S.D. Mayhew, M. Marino, D. Mantini, A.P. Bagshaw, Characterisation of haemodynamic activity in resting state networks by fractal analysis, Int. J. Neural Syst. 30 (12) (Dec. 2020), https://doi.org/10.1142/S0129065720500616.
- F.M. Smits, C. Porcaro, C. Cottone, A. Cancelli, P.M. Rossini, F. Tecchio, Electroencephalographic fractal dimension in healthy ageing and alzheimer ' s disease, PLoS One 11 (2) (Feb. 2016) e0149587, https://doi.org/10.1371/ JOURNAL.PONE.0149587.
- C. Porcaro, et al., Fractal dimension feature as a signature of severity in disorders of consciousness: an EEG study, Int. J. Neural Syst. 32 (7) (Jul. 2022), https://doi. org/10.1142/S0129065722500319.
- C. Porcaro, S.D. Mayhew, M. Marino, D. Mantini, A.P. Bagshaw, Characterisation of haemodynamic activity in resting state networks by fractal analysis, Int. J. Neural Syst. 30 (12) (Dec. 2020), https://doi.org/10.1142/S0129065720500616.
- F. Zappasodi, E. Olejarczyk, L. Marzetti, G. Assenza, V. Pizzella, F. Tecchio, Fractal dimension of EEG activity senses neuronal impairment in acute stroke, PLoS One 9 (6) (Jun. 2014) e100199, https://doi.org/10.1371/JOURNAL.PONE.0100199.
- S. Moaveninejad, S. Cauzzo, C. Porcaro, Fractal dimension and clinical neurophysiology fusion to gain a deeper brain signal understanding: a systematic review, Inf. Fusion 118 (Jun. 2025) 102936, https://doi.org/10.1016/J. INFFUS.2025.102936.
- E.A. Solomon, et al., TMS provokes target-dependent intracranial rhythms across human cortical and subcortical sites, Brain Stimul. 17 (3) (May 2024) 698 -712, https://doi.org/10.1016/J.BRS.2024.05.014.
- M. Massimini, R. Huber, F. Ferrarelli, S. Hill, G. Tononi, 'The Sleep Slow Oscillation as a Traveling Wave ' , 2004, https://doi.org/10.1523/JNEUROSCI.1318-04.2004.
- S. D ' Ambrosio, et al., Detecting cortical reactivity alterations induced by structural disconnection in subcortical stroke, Clin. Neurophysiol. 156 (Dec. 2023) 1 -3, https://doi.org/10.1016/J.CLINPH.2023.09.007.
- S. Sarasso, et al., Local sleep-like cortical reactivity in the awake brain after focal injury, Brain 143 (12) (Dec. 2020) 3672 -3684, https://doi.org/10.1093/BRAIN/ AWAA338.

*A.L. Bisogno et al.*

- M. Rosanova, et al., Recovery of cortical effective connectivity and recovery of consciousness in vegetative patients, Brain 135 (Pt 4) (2012) 1308 -1320, https:// doi.org/10.1093/BRAIN/AWR340.
- C. Tscherpel, S. Dern, L. Hensel, U. Ziemann, G.R. Fink, C. Grefkes, Brain responsivity provides an individual readout for motor recovery after stroke, Brain 143 (6) (Jun. 2020) 1873 -1888, https://doi.org/10.1093/BRAIN/AWAA127.
- A. Kabir, et al., Influence of large-scale brain state dynamics on the evoked response to brain stimulation, J. Neurosci. 44 (39) (Sep. 2024) e0782242024, https://doi.org/10.1523/JNEUROSCI.0782-24.2024.
- P.M. Rossini, et al., Non-invasive electrical and magnetic stimulation of the brain, spinal cord, roots and peripheral nerves: basic principles and procedures for routine clinical and research application. An updated report from an I.F.C.N. committee, Clin. Neurophysiol. 126 (6) (Jun. 2015) 1071 -1107, https://doi.org/ 10.1016/J.CLINPH.2015.02.001.
- Y. Bai, P. Belardinelli, U. Ziemann, Bihemispheric sensorimotor oscillatory network states determine cortical responses to transcranial magnetic stimulation, Brain Stimul. 15 (1) (Jan. 2022) 167 -178, https://doi.org/10.1016/J.BRS.2021.12.002.
- D. Desideri, C. Zrenner, U. Ziemann, P. Belardinelli, Phase of sensorimotor μ -oscillation modulates cortical responses to transcranial magnetic stimulation of the human motor cortex, J. Physiol. 597 (23) (Dec. 2019) 5671 -5686, https://doi. org/10.1113/JP278638.
- M.I. Stefanou, D. Desideri, P. Belardinelli, C. Zrenner, U. Ziemann, Phase synchronicity of μ -Rhythm determines efficacy of interhemispheric communication between human motor cortices, J. Neurosci. 38 (49) (Dec. 2018) 10525, https:// doi.org/10.1523/JNEUROSCI.1470-18.2018.
- M. Poorganji, et al., Pre-stimulus power but not phase predicts prefrontal cortical excitability in TMS-EEG, Biosensors (Basel) 13 (2) (Feb. 2023), https://doi.org/ 10.3390/BIOS13020220.
- N. Guyon, et al., Network asynchrony underlying increased broadband gamma power, J. Neurosci. 41 (13) (Mar. 2021) 2944 -2963, https://doi.org/10.1523/ JNEUROSCI.2250-20.2021.
- V.S. Sohal, J.L.R. Rubenstein, Excitation-inhibition balance as a framework for investigating mechanisms in neuropsychiatric disorders, Mol. Psychiatr. 24 (9) (Sep. 2019) 1248 -1257, https://doi.org/10.1038/S41380-019-0426-0.
- R. Gao, E.J. Peterson, B. Voytek, Inferring synaptic excitation/inhibition balance from field potentials, Neuroimage 158 (Sep. 2017) 70 -78, https://doi.org/ 10.1016/J.NEUROIMAGE.2017.06.078.
- S.E.W. Janssens, A.T. Sack, Spontaneous fluctuations in oscillatory brain state cause differences in transcranial magnetic stimulation effects within and between individuals, Front. Hum. Neurosci. 15 (Dec) (2021), https://doi.org/10.3389/ FNHUM.2021.802244.
- M. Biabani, A. Fornito, T.P. Mutanen, J. Morrow, N.C. Rogasch, Characterizing and minimizing the contribution of sensory inputs to TMS-evoked potentials, Brain Stimul. 12 (6) (Nov. 2019) 1537 -1552, https://doi.org/10.1016/J. BRS.2019.07.009.
- J. Rothwell, M. Hallett, A. Berardelli, A. Eisen, P. Rossini, W. Paulus, Magnetic stimulation: motor evoked potentials. The international Federation of clinical neurophysiology, Electroencephalogr. Clin. Neurophysiol. Suppl. 52 (1999) 97 -103.
- A. Delorme, S. Makeig, EEGLAB: an open source toolbox for analysis of single-trial EEG dynamics including independent component analysis, J. Neurosci. Methods 134 (1) (Mar. 2004) 9 -21, https://doi.org/10.1016/j.jneumeth.2003.10.009.
- N.C. Rogasch, et al., Analysing concurrent transcranial magnetic stimulation and electroencephalographic data: a review and introduction to the open-source TESA software, Neuroimage 147 (Feb. 2017) 934 -951, https://doi.org/10.1016/J. NEUROIMAGE.2016.10.031.
- T.E. Nichols, A.P. Holmes, Nonparametric permutation tests for functional neuroimaging: a primer with examples, Hum. Brain Mapp. 15 (1) (2001) 1, https:// doi.org/10.1002/HBM.1058.
- J.C. Hernandez-Pavon, et al., TMS combined with EEG: recommendations and open issues for data collection and analysis, Brain Stimul. 16 (2) (Mar. 2023) 567 -593, https://doi.org/10.1016/J.BRS.2023.02.009/ASSET/38FAD213-F1A7-4402BB2F-E77C6C5CC8BC/MAIN.ASSETS/GR2_LRG.JPG.
- W.L. Shew, D. Plenz, The functional benefits of criticality in the cortex, Neuroscientist 19 (1) (Feb. 2013) 88 -100, https://doi.org/10.1177/ 1073858412445487.
- D. Toker, F.T. Sommer, M. D ' Esposito, A simple method for detecting chaos in nature [Online]. Available: https://arxiv.org/abs/1904.00986v3, Mar. 2019. (Accessed 25 November 2024).
- M. Breakspear, Dynamic models of large-scale brain activity, Nat. Neurosci. 20 (3) (2017) 340 -352, https://doi.org/10.1038/nn.4497. Feb. 2017.
- E. Tagliazucchi, P. Balenzuela, D. Fraiman, D.R. Chialvo, Criticality in large-scale brain fmri dynamics unveiled by a novel point process analysis, Front. Physiol. 3 (FEB) (Feb. 2012) 20422, https://doi.org/10.3389/FPHYS.2012.00015/BIBTEX.
- G. Deco, M.L. Kringelbach, Great expectations: using whole-brain computational connectomics for understanding neuropsychiatric disorders, Neuron 84 (5) (Dec. 2014) 892 -905, https://doi.org/10.1016/J.NEURON.2014.08.034/ASSET/ 67067E3B-C8DC-48B4-A101-B9BCF2D2868E/MAIN.ASSETS/GR3_LRG.JPG.
- M. Massimini, F. Ferrarelli, R. Huber, S.K. Esser, H. Singh, G. Tononi, Breakdown of cortical effective connectivity during sleep, Science 309 (5744) (Sep. 2005) 2228 -2232, https://doi.org/10.1126/SCIENCE.1117256.
- S. Palva, J.M. Palva, Functional roles of alpha-band phase synchronization in local and large-scale cortical networks, Front. Psychol. 2 (SEP) (Sep. 2011) 10776, https://doi.org/10.3389/FPSYG.2011.00204/BIBTEX.
- B.J. He, Scale-free brain activity: past, present, and future, Trends Cognit. Sci. 18 (9) (2014) 480 -487, https://doi.org/10.1016/J.TICS.2014.04.003.
- M. Schartner, et al., Complexity of multi-dimensional spontaneous EEG decreases during propofol induced general anaesthesia, PLoS One 10 (8) (Aug. 2015), https://doi.org/10.1371/JOURNAL.PONE.0133532.
- D.S. Bassett, E.T. Bullmore, Human brain networks in health and disease, Curr. Opin. Neurol. 22 (4) (Aug. 2009) 340 -347, https://doi.org/10.1097/ WCO.0B013E32832D93DD.
- J. Yang, et al., Aberrant brain dynamics in major depressive disorder with suicidal ideation, J. Affect. Disord. 314 (Oct. 2022) 263 -270, https://doi.org/10.1016/J. JAD.2022.07.043.
- A. Stolk, et al., Electrocorticographic dissociation of alpha and beta rhythmic activity in the human sensorimotor system, eLife 8 (Oct) (2019), https://doi.org/ 10.7554/ELIFE.48065.
- M. Thies, C. Zrenner, U. Ziemann, T.O. Bergmann, Sensorimotor mu-alpha power is positively related to corticospinal excitability, Brain Stimul. 11 (5) (Sep. 2018) 1119 -1122, https://doi.org/10.1016/J.BRS.2018.06.006.
- T.O. Bergmann, A. Lieb, C. Zrenner, U. Ziemann, Pulsed facilitation of corticospinal excitability by the sensorimotor μ -Alpha rhythm, J. Neurosci. 39 (50) (Dec. 2019) 10034 -10043, https://doi.org/10.1523/JNEUROSCI.1730-19.2019.
- K. Ogata, H. Nakazono, T. Uehara, S. Tobimatsu, Prestimulus cortical EEG oscillations can predict the excitability of the primary motor cortex, Brain Stimul. 12 (6) (Nov. 2019) 1508 -1516, https://doi.org/10.1016/J.BRS.2019.06.013.
- A. Fernandez-Ruiz, A. Sirota, V. Lopes-dos-Santos, D. Dupret, Over and above frequency: gamma oscillations as units of neural circuit operations, Neuron 111 (7) (Apr. 2023) 936 -953, https://doi.org/10.1016/J.NEURON.2023.02.026.
- K.J. Pope, S.P. Fitzgibbon, T.W. Lewis, E.M. Whitham, J.O. Willoughby, Relation of gamma oscillations in scalp recordings to muscular activity, Brain Topogr. 22 (1) (Jun. 2009) 13 -17, https://doi.org/10.1007/S10548-009-0081-X/FIGURES/2.
- J.F. Hipp, M. Siegel, Dissociating neuronal gamma-band activity from cranial and ocular muscle activity in EEG, Front. Hum. Neurosci. 7 (JUN) (Jun. 2013) 338, https://doi.org/10.3389/FNHUM.2013.00338.
- Y. Song, P.C. Gordon, J. Metsomaa, M. Rostami, P. Belardinelli, U. Ziemann, Evoked EEG responses to TMS targeting regions outside the primary motor cortex and their test -retest reliability, Brain Topogr. 37 (1) (Jan. 2024) 19 -36, https:// doi.org/10.1007/S10548-023-01018-Y.
- W. Klimesch, Alpha-band oscillations, attention, and controlled access to stored information, Trends Cognit. Sci. 16 (12) (Dec. 2012) 606 -617, https://doi.org/ 10.1016/J.TICS.2012.10.007.
- B. Voytek, et al., Age-related changes in 1/f neural electrophysiological noise, J. Neurosci. 35 (38) (Sep. 2015) 13257 -13265, https://doi.org/10.1523/ JNEUROSCI.2332-14.2015.
- E. Bas ¸ar, Brain oscillations in neuropsychiatric disease, Dialogues Clin. Neurosci. 15 (3) (Sep. 2013) 291 -300, https://doi.org/10.31887/DCNS.2013.15.3/EBASAR.
- T.H. Donner, M. Siegel, A framework for local cortical oscillation patterns, Trends Cognit. Sci. 15 (5) (May 2011) 191 -199, https://doi.org/10.1016/J. TICS.2011.03.007.
- A. Wolff, et al., Atypical temporal dynamics of resting state shapes stimulus-evoked activity in depression -an EEG study on rest -stimulus interaction, Front. Psychiatr. 10 (Oct. 2019) 475953, https://doi.org/10.3389/FPSYT.2019.00719/XML.
- S. Wainio-Theberge, A. Wolff, G. Northoff, Dynamic relationships between spontaneous and evoked electrophysiological activity, Commun. Biol. 4 (1) (2021) 1 -17, https://doi.org/10.1038/s42003-021-02240-9. Jun. 2021.
- Z. Huang, et al., Is there a nonadditive interaction between spontaneous and evoked activity? phase-dependence and its relation to the temporal structure of scale-free brain activity, Cerebr. Cortex 27 (2) (Feb. 2017) 1037 -1059, https://doi. org/10.1093/CERCOR/BHV288.
- G. Northoff, F. Zilio, J. Zhang, Beyond task response -Pre-stimulus activity modulates contents of consciousness, Phys. Life Rev. 49 (Jul. 2024) 19 -37, https:// doi.org/10.1016/J.PLREV.2024.03.002.
- I. Gran ¨ o, et al., Local brain-state dependency of effective connectivity: a pilot TMS -EEG study, Open Research Europe 2 (Apr. 2022) 45, https://doi.org/ 10.12688/OPENRESEUROPE.14634.1.
- S. Casarotto, et al., The rt-TEP tool: real-time visualization of TMS-evoked potentials to maximize cortical activation and minimize artifacts, J. Neurosci. Methods 370 (Mar. 2022), https://doi.org/10.1016/J.JNEUMETH.2022.109486.
- P. Lioumis, M. Rosanova, The role of neuronavigation in TMS -EEG studies: current applications and future perspectives, J. Neurosci. Methods 380 (Oct. 2022) 109677, https://doi.org/10.1016/J.JNEUMETH.2022.109677.
- M. Rosanova, A. Casali, V. Bellina, F. Resta, M. Mariotti, M. Massimini, Natural frequencies of human corticothalamic circuits, J. Neurosci. 29 (24) (Jun. 2009) 7679 -7685, https://doi.org/10.1523/JNEUROSCI.0445-09.2009.
- B.J. West, Fractal physiology and the fractional calculus: a perspective, Front. Physiol. 1 (OCT) (Oct. 2010) 1886, https://doi.org/10.3389/FPHYS.2010.00012/ BIBTEX.