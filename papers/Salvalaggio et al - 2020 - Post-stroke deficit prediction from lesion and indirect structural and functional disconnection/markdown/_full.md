BRAIN

*[picture on PDF page 1]*

**Figure labels:**
- A JOURNAL OF NEUROLOGY

### Post-stroke deficit prediction from lesion and indirect structural and functional disconnection

Alessandro Salvalaggio, 1 Michele De Filippo De Grazia, 2 Marco Zorzi, 2,3 Michel Thiebaut de Schotten 4,5 and Maurizio Corbetta 1,6,7

See Umarova and Thomalla (doi:10.1093/brain/awaa186) for a scientific commentary on this article.

Behavioural deficits in stroke reflect both structural damage at the site of injury, and widespread network dysfunction caused by structural, functional, and metabolic disconnection. Two recent methods allow for the estimation of structural and functional disconnection from clinical structural imaging. This is achieved by embedding a patient's lesion into an atlas of functional and structural connections in healthy subjects, and deriving the ensemble of structural and functional connections that pass through the lesion, thus indirectly estimating its impact on the whole brain connectome. This indirect assessment of network dysfunction is more readily available than direct measures of functional and structural connectivity obtained with functional and diffusion MRI, respectively, and it is in theory applicable to a wide variety of disorders. To validate the clinical relevance of these methods, we quantified the prediction of behavioural deficits in a prospective cohort of 132 first-time stroke patients studied at 2 weeks post-injury (mean age 52.8 years, range 22-77; 63 females; 64 right hemispheres). Specifically, we used multivariate ridge regression to relate deficits in multiple functional domains (left and right visual, left and right motor, language, spatial attention, spatial and verbal memory) with the pattern of lesion and indirect structural or functional disconnection. In a subgroup of patients, we also measured direct alterations of functional connectivity with resting-state functional MRI. Both lesion and indirect structural disconnection maps were predictive of behavioural impairment in all domains (0.16 5 R 2 5 0.58) except for verbal memory (0.05 5 R 2 5 0.06). Prediction from indirect functional disconnection was scarce or negligible (0.01 5 R 2 5 0.18) except for the right visual field deficits (R 2 = 0.38), even though multivariate maps were anatomically plausible in all domains. Prediction from direct measures of functional MRI functional connectivity in a subset of patients was clearly superior to indirect functional disconnection. In conclusion, the indirect estimation of structural connectivity damage successfully predicted behavioural deficits post-stroke to a level comparable to lesion information. However, indirect estimation of functional disconnection did not predict behavioural deficits, nor was a substitute for direct functional connectivity measurements, especially for cognitive disorders.

- 1 Clinica Neurologica, Department of Neuroscience, and Padova Neuroscience Center (PNC), University of Padova, Italy
- 2 IRCCS San Camillo Hospital, Venice, Italy
- 3 Department of General Psychology, and Padova Neuroscience Center (PNC), University of Padova, Italy
- 4 Brain Connectivity and Behaviour Laboratory, Sorbonne Universities, Paris, France
- 5 Groupe d'Imagerie Neurofonctionnelle, Institut des Maladies Neurode ´ge ´ne ´ratives-UMR 5293, CNRS, CEA University of Bordeaux, Bordeaux, France
- 6 Venetian Institute of Molecular Medicine, VIMM, Padova, Italy
- 7 Department of Neurology, Radiology, Neuroscience Washington University School of Medicine, St.Louis, MO, USA

Correspondence to: Prof. Maurizio Corbetta

Clinica Neurologica, Department of Neuroscience, via Giustiniani 2, 35128 Padova, Italy

E-mail: maurizio.corbetta@unipd.it

|

|

Keywords: stroke; connectivity; lesion; structural disconnection; functional disconnection

Abbreviations: FC = functional connectivity; FDC = functional disconnection; fMRI = functional MRI; SDC = structural disconnection

### Introduction

Behavioural deficits in stroke reflect both structural damage at the site of injury (Harlow, 1848; Broca, 1861; Wernicke, 1874), and widespread network dysfunction caused by structural, functional, and metabolic disconnection (von Monakow, 1914; Baron et al. , 1986, 1992; Perani et al. , 1988; Corbetta et al. , 2005; Carrera and Tononi, 2014).

Recently, we have shown that stroke causes alterations of functional connectivity (FC) measured with functional MRI (fMRI) in widespread parts of cortex that appear structurally normal (He et al. , 2007; Carter et al. , 2010, 2012). Notably, FC alterations accurately predict behavioural deficits, explaining  40-60% of the variability of behavioural scores across subjects at the acute stage (Siegel et al. , 2016). They also distinguish patients with good and poor recovery of function, especially for cognitive deficits (Siegel et al. , 2018; for a review see Corbetta et al. , 2018). There is also evidence that changes in macroscale structural connectivity are associated with behavioural deficits, and their recovery (Stinear et al. , 2007; Schaechter et al. , 2009; Schlaug et al. , 2009; Ivanova et al. , 2016; Hope et al. , 2017; Umarova et al. , 2017).

However, measuring behaviour and MRI signals to measure network-level dysfunction in patients is hardly simple, it is expensive, and it is not easily implemented in clinical practice.

A possible solution to this problem has come in the last few years from the development of large databases of functional and diffusion MRI data, and pipelines of analysis for the generation of so-called 'connectomes', i.e. the ensemble of functional or structural connections among brain regions that are common in a large group of healthy subjects (Yeo et al. , 2011; Catani and Thiebaut de Schotten, 2012; Glasser et al. , 2013).

One method, known as 'lesion network mapping' (Boes et al. , 2015; Fox, 2018), computes whole-brain FC to or from the lesion, i.e. the temporal correlation of the fMRI signal between the lesion and the rest of the brain. This method highlights the ensemble of functional connections that connect the site of damage with the rest of the brain either through direct or indirect anatomical connections. This functional map may thus correspond to the networklevel FC abnormalities caused by the lesion (functional disconnection, FDC). This method has been applied in many studies to investigate network dysfunction in a whole host of neurological and psychiatric conditions (Fischer et al. , 2016; Laganiere et al. , 2016; Darby et al. , 2017, 2018 a , b , 2019; Fasano et al. , 2017; Fox, 2018; Joutsa et al. , 2018, 2019; Cohen et al. , 2019; Corp et al. , 2019; Ferguson et al. , 2019; Kim et al. , 2019; Padmanabhan et al. , 2019) that are either rare or when functional MRI data are lacking (Fox, 2018).

A similar method, known as the 'dys-connectome', estimates structural disconnection from clinical structural MRI lesions (Foulon et al. , 2018). The method estimates in a population of healthy subjects, the probability of normal white matter tracts, measured with diffusion imaging, that pass through the lesion. In a structural disconnection (SDC) map, each voxel in the brain indicates the probability of structural disconnection caused by the lesion to healthy white matter tracts (Forkel and Catani, 2018; Ivanova et al. , 2018). The specificity of disconnection in both methods is typically assessed by comparing the disconnection patterns produced by a 'target' syndrome with that produced by a 'control' syndrome/s (Darby et al. , 2017, 2018 a , b , 2019; Fasano et al. , 2017; Joutsa et al. , 2018; Corp et al. , 2019).

However, the sensitivity of indirect disconnection methods in predicting behavioural deficits is unknown. This is an essential requirement for studying network-behaviour relationships, stratifying patients' severity, predicting long-term outcome, or as a potential marker of response to novel therapeutic interventions.

In this study we take advantage of the Washington University Stroke project, which has carefully characterized a prospective sample of first-time stroke patients with an indepth behavioural battery and multi-modal imaging (structural, diffusion MRI, functional, perfusion MRI). Neurological impairment was quantified in different domains (motor, vision, language, attention, and memory) through a set of deficit components that capture the bulk of the inter-subject covariance across test scores (Corbetta et al. , 2015). The study had three goals. First, we tested how well indirect measures of structural and functional disconnection predict behavioural deficits poststroke using lesion-based predictions as a baseline. Previous work on this cohort showed that lesion location accurately predicts motor and visual deficits, and much less accurately cognitive deficits (Corbetta et al. , 2015; Siegel et al. 2016). In contrast, cognitive deficits are better explained by widespread patterns of abnormal FC (Siegel et al. , 2016, 2018), as well as macroscale structural plasticity (Hope et al. , 2017; Umarova et al. , 2017). Second, we compared predictions for lesions and indirect disconnection, in isolation or combined, to see if they explain different sources of variance. In fact, as an example, SDC maps contain information about the inter-subject variability of structural connections to or from a lesion, and may capture different variability than lesion location. Third, in a subgroup of patients, we also obtained direct fMRI-FC measures in addition to FDC maps. This allowed us to compare indirect with direct functional abnormalities measures (He et al. , 2007; Carter et al. , 2010; Baldassarre et al. , 2014; Siegel et al. , 2016, 2018; Ramsey et al ., 2017).

### Materials and methods

### Subject enrolment

The patient cohort is the same as in Corbetta et al. (2015). All participants provided informed consent following the Declaration of Helsinki and procedures established by the Washington University in Saint Louis Institutional Review Board. First-time stroke patients ( n = 132) were recruited through the in-patient service at Barnes-Jewish Hospital and the Rehabilitation Institute of St. Louis (mean age 52.8 years with range 22-77; 119 right-handed; 63 females; 64 right hemispheres). Corbetta et al. (2015) ran control analyses to ensure that this sample was representative of the clinical stroke population of a tertiary stroke centre in the US Midwest. Inclusion and exclusion criteria are provided in the Supplementary material.

### Neuropsychological and behavioural assessment

All participants underwent a behavioural battery (Corbetta et al. , 2015). The battery includes 42 different measures, and was run typically on the same day as the imaging session and lasted  2.5 h. The battery is 'broad' as it covers many domains of function and 'deep' since, in each domain, it measures different processes that are potentially dissociable based on physiological or neuropsychological work. For instance, the language battery measures auditory comprehension, speech production, and reading both at the single word and sentence level; it also tests aspects of semantic fluency and phonological processing (see Supplementary material for a description of tasks).

In the present study the following domains were considered: language (including lesions of both hemispheres), motor left (including right lesions), motor right (left lesion), visual left (right lesions), visual right (left lesions), verbal memory (lesions from both hemispheres), spatial memory (lesions from both hemispheres), and attention (visual field bias, with lesions from both hemispheres). Not all participants completed all neuropsychological tasks; therefore, scores in different domains have different numbers of subjects.

We ran a principal component analysis (PCA) on the behavioural scores of the different tests within each domain (e.g. motor, visual, language, etc.) for dimensionality reduction (Corbetta et al. , 2015; Ramsey et al. , 2017). For each domain we obtained one or two components that accounted for the majority of variance (Supplementary material). For example, one language component accounted for 77.3% of the variance and was related to both comprehension, production, and reading deficits. The component scores in each domain were continuous and were normalized to have a mean of 0 and standard deviation (SD) of 1; lower scores indicate a more severe impairment in that functional domain. The Factorial scores for each domain are reported in Supplementary Table 1.

### MRI procedure and scanning

The full MRI protocol is described in Corbetta et al. (2015). Scanning was performed with a Siemens 3 T Tim-Trio scanner at the School of Medicine of the Washington University in St. Louis, including: structural, functional, and diffusion imaging. Structural scans consisted of: (i) a sagittal MP-RAGE T1-

|

weighted image (repetition time = 1950 ms, echo time = 2.26 ms, flip angle = 9  , voxel size = 1.0 -1.0 -1.0 mm); (ii) a transverse turbo spin-echo T2-weighted image (repetition time = 2500 ms, echo time = 435 ms, voxel-size = 1.0 -1.0 -1.0 mm); and (iii) a sagittal FLAIR (fluid-attenuated inversion recovery) (repetition time = 7500 ms, echo time = 326 ms, voxel size = 1.5 -1.5 -1.5 mm).

### MRI and lesion analysis

Lesion segmentation was performed as described in Siegel et al. (2016). Lesions were manually segmented on individual structural MRI images (T1-weighted MP-RAGE, T2-weighted spinecho images, and FLAIR images) using the Analyze biomedical imaging software system (www.mayoclinic.org; Robb and Hanson, 1991). Two board-certified neurologists (Drs Maurizio Corbetta and Alex Carter) reviewed all segmentations. Supplementary Table 1 provides the volume of segmented lesions in atlas space.

### Data preprocessing

Registrations of the T1 MRI images were performed using BCBtoolkit (Foulon et al. , 2018; http://toolkit.bcblab.com). Since spatial normalization can be affected by the presence of a brain lesion, each lesion or signal abnormalities due to the lesion (manually segmented) can be used as a mask during the normalization procedure to optimize the brain normalization (Ripolle ´s et al ., 2012; Volle et al ., 2013). Here we used an enantiomorphic approach (Nachev et al. , 2008) to replace the lesioned tissue with healthy tissue of the contralateral hemisphere. T1 images are registered to the template (MNI152) using affine and diffeomorphic deformations (Klein et al. , 2009; Avants et al. , 2011). The volumebased procedure is different from the surface-based registration used in previous work on the same dataset (Siegel et al. , 2016). This variation and related success or failure of the registration in different subjects explains slight differences in the number of subjects included in the two studies.

### Structural disconnection maps

SDC maps were calculated using the BCB-toolkit (Foulon et al. , 2018). We used a set of 176 healthy controls from the 'Human Connectome Project' 7 T diffusion-weighted imaging datasets to track fibres passing through each lesion (age 29.5 ± 3.6 years, 72 male subjects; HCP7T; http://www.humanconnectome.org/ study/hcp-young-adult/; Vu et al. , 2015). Each patient's lesion traced in the MNI152 space was used as seed for the tractography in Trackvis (http://trackvis.org/). In an SDC map, the value in each voxel takes into account the interindividual variability of tract reconstructions in controls and indicates at each voxel probability of disconnection from 0 to 1 for a given lesion (Thiebaut de Schotten et al. , 2011, 2015). Therefore, this approach indirectly estimates the degree of structural disconnection.

### Functional disconnection maps

Following the methods described in Boes et al. (2015), we generated an FDC map for each lesion. This approach indirectly estimates the degree of functional disconnection produced by a lesion. We used the same n = 176 7 T 'Human Connectome

|

project' healthy subjects to estimate the average Pearson correlation between the time course of a region of interest corresponding to the lesion and the rest of the brain. Each patient's lesion in MNI152 space was a seed region of interest for a wholebrain resting-state functional connectivity in each of the control subjects. The resulting n = 176 functional connectivity maps were averaged in MNI space to produce an FDC map (Foulon et al. , 2018). In the resulting FDC map, the value in each voxel indicates an average strength of correlation between -1 and +1 between the time course of region of interest corresponding to the lesion and the rest of the brain. Therefore, both SDC and FDC maps estimate, based on the structural and functional connectivity variability of the same healthy subjects, the putative effect of a lesion in causing structural or functional network disconnection.

### Resting state functional MRI functional connectivity maps

One subgroup of subjects, in which both structural (T1, T2, FLAIR) and resting state-functional MRI (R-fMRI) data were available, participated in an analysis comparing direct versus indirect estimates of FDC (demographic data for this subgroup are provided in Supplementary Table 1). The detailed experimental procedures are in Siegel et al. (2016). Restingstate functional scans acquired with a gradient echo EPI sequence (repetition time = 2000 ms, echo time = 27 ms, 32 contiguous 4-mm slices, 4 -4 mm in-plane resolution) required participants to fixate on a small cross in a low luminance environment. Six to eight resting-state scans, each including 128 volumes (30 min total), were acquired. The fMRI preprocessing steps are described in the Supplementary material. The cortical surface parcellation generated by Gordon et al. (2016) was used. The parcellation is based on R-fMRI boundary mapping and achieves full cortical coverage and optimal region homogeneity. The parcellation includes 324 regions of interest (159 in the left hemisphere, 165 in the right hemisphere). The original parcellation includes 333 regions, but all regions with less than 20 vertices (  50 mm 2 ) were excluded.

### Lesion, structural disconnection, functional disconnection and functional connectivity symptom mapping

For each method (lesion, SDC, FDC, and FC), and for each behavioural score (language, motor left, motor right, verbal memory, spatial memory, attention, visual left, visual right), multivariate analyses were carried out as follows: Features of the lesion/SDC/FDC/FC images extracted by PCA were used as multivariate predictors for a ridge regression model trained to predict patients' behavioural outcomes (Corbetta et al. , 2015; Siegel et al. , 2016). Ridge regression differs from multiple linear regression because it uses L2-normalization to regularize model coefficients, so that unimportant features are automatically down-weighted or eliminated, thereby preventing overfitting and improving generalization on test data

(Le Cessie and Van Houwelingen, 1992). The model weights W are computed as:

W ¼ X T X þ k I ð Þ   1 X T Y (1)

where X is the set of predictors and Y is the outcome variable. The regularization term provides a constraint on the size of weights and it is controlled by parameter k ð lambda Þ . A tuning procedure is necessary to find the appropriate value of k . Importantly, this approach also allows to project predictive weights back to brain anatomy in a simple way (Phan et al. , 2010). Moreover, its predictive performance in lesionbehaviour mapping is relatively unaffected by sample size in comparison to other machine learning techniques (Chauhan et al. , 2019).

Before applying ridge regression, PCA was performed on each dataset (lesion, SDC, FDC and FC) to reduce the dimensionality of the input. For lesion, FDC and SDC maps the PCA was performed on 902229 2-mm 3 brain voxels (whole-brain images); for FC it was carried out on the full matrix of 52326 edges resulting from 324 nodes/parcels. Regardless of the size and nature (e.g. binary versus continuous) of the input images, PCA returns a set of (continuous) principal component (PC) scores. Components that explained 95% of the variance were retained and used as input for the ridge regression model. All predictors (PC scores) and the outcome variable (behavioural score) were z -normalized before applying ridge regression. All ridge regression models were trained and tested using a leave-one-(patient)out cross validation (LOOCV) loop (Golland and Fischl, 2003). In each loop, the regularization coefficient k was optimized by identifying a value between k = 10 -5 and 10 5 (logarithmic steps) that minimized leave-one-out prediction error over the training set. Optimal weights were solved across the entire training set using gradient descent to minimize error for the ridge regression equation by varying lambda. These model weights were then applied to the left-out patient to predict the behavioural score. A prediction was generated for all patients in this way.

Model accuracy was assessed using the coefficient of determination

P

R 2 ¼ 1   Y   Y 0 ð Þ 2 P Y   Y 0    2 (2)

where Y are the measured behaviour scores, Y 0 are the predicted behaviour scores and Y 0 is the mean of predicted behaviour scores. The statistical significance of all LOOCV results was assessed using permutation test. For each dataset and domain, the behavioural scores were randomly permuted across subjects 10000 times, and ridge regression models were fit to the sets of randomized labels. A P -value was calculated as the probability of observing the reported R 2 values by chance (number of permutations with R 2 4 observed R 2 ) / (number of permutations). Only models with P -values 5 0.05 were considered reliable. Moreover, we statistically compared reliable models within the same domain (e.g. lesion versus SDC for language scores) in terms of prediction errors, computed as squared difference between measured and predicted behaviour scores (i.e. squared residuals). These were compared across models using the Wilcoxon signed rank test (non-parametric test for paired data). Z -score and corresponding P -value [false discovery rate (FDR)

corrected for multiple comparisons] are reported for each pair of models (see results in Supplementary Table 2).

Finally, the ridge regression weight matrix was averaged across all n LOOCV loops to generate a single set of consensus weights. Statistical reliability of each consensus weight was assessed by comparing its distribution of values (throughout the LOOCV loops) to a null distribution (obtained from the null models generated for permutation testing) using an FDR corrected t -test. The final set of (statistically reliable) consensus weights was back projected to the brain (using the transpose matrix of PC coefficients) to display a map of the most predictive voxels (lesion, SDC, FDC) or functional connections (FC matrices) (Fig. 1). Gaussian smoothing (sigma = 1) and linear normalization [range (-1,1)] was applied on the maps for better visualization.

We also performed an additional analysis using lesion and SDC in combination to assess whether the joint information can increase predictive accuracy.

In addition, we ran univariate analyses (see results in the Supplementary material) to ensure that our results are robust across different methodologies.

### Data availability

All the data reported in the present study are available to the authors and all the software and algorithms used in the present study are cited in the material and methods.

### Results

We used a cohort of first-time stroke subjects (Corbetta et al. , 2015), studied within 2 weeks post-stroke with an indepth behavioural battery of motor, visual, language, memory, and attention functions. We examined the accuracy of prediction of post-stroke deficits based on four kinds of brain signals: structural damage, indirect estimates of structural and functional disconnection, and direct fMRI-FC measures.

Supplementary Table 1 shows demographic information of the cohort. The number of subjects was different for the different domains because scores for language, memory, and attention were pooled across left and right hemisphere lesions, whereas scores for visual and motor deficits were independently considered for each side (e.g. left or right visual field). Since analyses were performed separately for each domain, the demographic data are reported for each domain. The mean age across the different domains varied between 49.8 ± 9.0 years (visual left) and 54.9 ± 11.9 years (motor right limbs). The mean education years varied between 13.1 ± 2.3 years (motor: left limbs) and 13.8 ± 2.7 years (visual left). Lesion volume was, on average, between 3.9 ± 5.1 (verbal memory and motor right limbs) and 7.3 ± 10.3 (visual left) cm 3 across the different domains. This sample is representative of the clinical stroke population of a tertiary US medical centre (Corbetta et al. , 2015).

*[picture on PDF page 5]*

**Figure labels:**
- Behavioural score
- Projected beta-weights
- Scatter plots and
- (e.g. Motor left)
- maps
- explained variance
- PCA data reduction + Ridge
- Regression with Leave-one-out
- Cross-Validation
- Lesion maps (from
- i=1
- n
- (wtxi − yi)² + λ||w|z
- R²= 0.35
- -fit
- Patient
- score
- -3
- -2
- -1
- 0
- 1
- 2
- each subject)
- Prediction behavioral
- (wtxi − yi)² + λ||w||²
- R²= 0.37
- SDC maps (from
- R²= 0.12
- FDC maps (from
- Real score

|

|

Figure 1 shows a schematic workflow of the analysis. For each behavioural score (e.g. motor left) we compute a set of ridge regression models, with leave-one-out cross validation, to predict behavioural deficits based on lesion or disconnection (SDC, FDC) maps computed from healthy participants' atlases (see 'Materials and methods' section). The model optimizes the prediction of behavioural variability (as the difference between real versus predicted scores, see scatter plot in Fig. 1).

A similar set of analyses used univariate voxel-wise regression using as the dependent variable, respectively, the lesion, SDC, and FDC maps. This process generates a set of t-maps that show damaged voxels significantly related to behavioural impairment. We report univariate regression methods and results in the Supplementary material.

### Multivariate ridge regression

The ridge regression approach optimizes the prediction of behavioural deficits through a minimization procedure of the error between real and predicted scores. This method provides an estimate of the highest possible explainable variance and allows one to visualize back onto the brain the weights contributing to the prediction.

### Visual deficits

Visual impairment was assessed in each patient, separately for the left and right visual field, with a visual field pattern score, derived from the computerized perimetry. These scores were modelled to find the most predictive lesion, SDC, or FDC patterns. The lesion map for right visual field deficits (Fig. 2, top row) shows the most predictive positive (red-yellow scale indicates more severe deficits) weights in the left occipital cortex, both medially and laterally, extending in the geniculo-calcarine radiation. Interestingly, there was also contribution of the left frontal eye field. This map explains 58% of the variability of the right visual field pattern scores. The left visual field deficit lesion map is similar (Supplementary Fig. 1, top row), and explains 40% of the variability. The corresponding SDC maps (Fig. 2 and Supplementary Fig. 1, middle row) are more extensive, and involve the splenium, the geniculo-calcarine radiation on both sides, the bilateral frontal eye field, and the inferior frontal-occipital fasciculus (IFOF) homolateral to the lesion. Damage to the internal capsule and cingulate bundle are negatively predictive of visual deficits (negative weights are very small compared to positive weights, as can be seen from the blue-teal colour scale in the images). The SDC model explains 23-33% of the variance. The FDC maps (Fig. 2 and Supplementary Fig. 1, bottom row) show a complete map of the bilateral visual occipital network, and temporoparietal junction and inferior frontal gyrus (for right visual field deficits), overlapping with the ventral attention/ salience network. Negative predictive weights occur in frontal and parietal regions and thalamus. The FDC maps explain 18% (left visual field) and 38% (right visual field) of the variability. Though the lesion model seems to explain a larger proportion of variance than the other models, statistical comparisons show no significant differences among the models (Wilcoxon test, all P 4 0.05; Supplementary Table 2), likely due to the small sample size.

### Motor deficits

We assessed motor deficits with a combination of tests of strength, dexterity, speed, and function that strongly correlated across subjects, yielding for each side of the body a 'motor deficit component score.' The lesion model explained 35% of the variability of left-side motor deficit scores with the most positive predictive weights in the homolateral corona radiata, internal capsule, and putamen (Fig. 3, top row). The lesion distribution for right-side motor deficits was similar with 28% of the variability accounted for (Supplementary Fig. 2, top row). The SDC model explained 37% of the variability of left-side motor deficit scores with localization in the bilateral corona radiata, bilateral cerebral peduncle, and corpus callosum (Fig. 3, middle row). Anatomically similar SDC maps in the opposite hemisphere explained 42% of the variability of right-side motor deficits (Supplementary Fig. 2, middle row).

The FDC model weights correspond to a beautiful map of the motor network, including bilateral motor, premotor, prefrontal, supplementary motor, and anterior cingulate, basal ganglia, and motor cerebellum. However, this anatomically sound functional anatomy explained only 8% of left-side motor deficits (Fig. 3, bottom row), and 12% of right motor deficits (Supplementary Fig. 2, bottom row). Statistical comparisons showed no difference between lesion and SDC models. However, SDC models were significantly superior to FDC models for both left ( z = -2.896, P = 0.004) and right ( z = -3.031, P = 0.002) motor deficits. Lesion were superior to FDC models for left motor deficits ( z = -2.596, P = 0.009; Supplementary Table 2).

### Language and verbal memory deficits

The group of subjects tested on the language battery was the largest ( n = 116). The language battery from the Boston Diagnostic Aphasia Examination measured auditory comprehension, speech production, and reading both at the single word and sentence level. A single language deficit score accounted for 4 70%ofbehavioural variability across subjects.

The lesion model, including left and right hemisphere lesions, explained 48% of the language score variability with the most predictive weights in the left frontal, insula, temporal, parietal, and peri-sylvian white matter; basal ganglia, and thalamus. Interestingly, the right inferior frontal cortex and bilateral frontal eye field are also significantly involved in the prediction of language impairment (Fig. 4, top row). The SDC map showed severe disconnection of most left hemisphere white matter tracts (IFOF, arcuate, inferior and superior longitudinal, and cingulate) and corpus callosum, and explained 41% of the variability (Fig. 4, middle row). The FDC map showed positive weights in bilateral (left 4 right) frontal, temporal, parietal cortical regions, bilateral basal ganglia, and posterolateral cerebellum (right 4

|

*[picture on PDF page 7]*

**Figure labels:**
- Visual right (left lesion) n = 31
- Lesion
- R
- R²= 0.58
- Patient
- fit
- -2
- -1
- 0
- Structural disconnection (SDC)
- Prediction
- R²= 0.33
- -5
- -3
- Functional disconnection (FDC)
- R²= 0.38
- -fit
- Real

*[picture on PDF page 7]*

**Figure labels:**
- Motor left (right lesion) n = 51
- Lesion
- R
- R²=0.35
- Patient
- -2
- -1
- 0
- 1
- Structural disconnection (SDC)
- Prediction
- R²= 0.37
- ---fit
- Functional disconnection (FDC)
- -3
- R²=0.12
- Real

left) in regions of the language and default networks (Fig. 4, bottom row). However, once again, even though the FDC map appears anatomically plausible, the variability of language deficits accounted for is only 6%.

The statistical analysis showed that lesions predicted language scores more accurately than SDC ( z = -2.372, P = 0.018) or FDC ( z = -4.681, P 5 0.001). In addition, SDC models were significantly more accurate than

|

*[picture on PDF page 8]*

**Figure labels:**
- Language n = 116
- Lesion
- R
- R²=0.48
- Patient
- -2
- -1
- 1
- Structural disconnection (SDC)
- Prediction
- R²= 0.41
- -fit
- Functional disconnection (FDC)
- -3
- 0
- R²= 0.06
- ·fit
- Real

FDC models ( z = -3.212, P = 0.001; Supplementary Table 2).

Verbal memory measured with the Hopkins Verbal Learning Test-Revised (HVLT-R) (Brandt and Benedict, 2001) included tests of immediate, delayed recall, and recognition. A single memory factor accounted for 4 60% of variability across participants. The lesion model localized left basal ganglia and thalamus, left lateral temporal, bilateral medial occipital-temporal lobe, and FEF bilaterally (Fig. 5, top row). However, this map predicted only 6% of the variation of memory scores.

The SDC model shows extensive white matter disconnection of the left hemisphere white matter, resembling the language SDC map. The SDC map, however, explains only 5% of the variance (Fig. 5, middle row). The FDC model localizes to bilateral occipital lobes, bilateral basal ganglia-thalamus, and medial parietal-frontal cortices in correspondence of the default mode network (Fig. 5, bottom row). Interestingly, this map resembles a memory circuitry map recently discovered with the same FDC method in a group of patients with lesions causing amnesia (Ferguson et al. , 2019). A spatial correlation analysis of the unthresholded FDC values between ours and Ferguson's amnesia map at the level of cortical and subcortical parcels (Catani and Thiebaut de Schotten, 2012; Glasser et al. , 2016) showed a significant overlap (Pearson r = 0.485, P 5 2.5031 -23 ) (Supplementary Fig. 3A-C). Moreover, lesion sites associated with worse memory scores in both datasets localized to the left basal ganglia and left periventricular frontal white matter. Conversely lesions associated with more normal memory scores localized to the right frontal white matter (Supplementary Fig. 3D and E). However, the FDC pattern for memory explained only 1% of the variance of memory scores, which was not significantly different from chance.

In summary, our analysis shows that neither lesion, SDC, or FDC predict verbal memory deficits. This finding is consistent with our previous work in which direct fMRI-FC measures, but not lesion topography, predict memory performance (Corbetta et al. , 2015; Siegel et al. , 2016, 2018).

### Spatial memory and attention

Spatial memory included spatial span, and immediate and delayed recall, and recognition, of visual figures on the Brief Visuospatial Memory Test-Revised (BVMT-R) (Benedict, 1997). A single 'spatial memory deficit,' explained 4 60% of the variance.

The lesion model accounted for 19% of the variability and included bilateral basal ganglia, thalamus, frontal eye field, and occipital cortex. The SDC model weighted on bilateral white matter tracts, and predicted also 19% of the variability. Finally, the FDC model mapped bilaterally on the frontoparietal, and cingulo-opercular networks that are involved in working memory and task maintenance (Dosenbach et al. , 2006; Seeley et al. , 2007), but these maps explained only 4% of the behavioural scores (Supplementary Fig. 4). There was a significant difference with SDC maps more predictive than FDC maps ( z = -2.883, P = 0.004). No other comparison was significant.

The spatial attention factor combined deficits of lateralized attention with/without motor responses (visual field bias).

|

*[picture on PDF page 9]*

**Figure labels:**
- Verbal Memory n = 88
- Lesion
- -1
- R
- -2
- R²=0.06
- Patient
- 0
- 2
- Structural disconnection (SDC)
- Prediction
- R²=0.05
- -it
- 1
- Functional disconnection (FDC)
- R²=0.01
- -fit
- Real

The lesion model predicted 18% of impairment variability. The SDC model accounted for 16% of variability. Finally, the FDC map predicted only 10% of the variability (Supplementary Fig. 5). No significant differences were detected with the Wilcoxon test.

Overall, for spatial memory and attention, lesion and SDC models predicted with moderate accuracy; FDC was significantly less predictive than SDC for spatial memory, but not for spatial attention.

### Structural-functional disconnection versus functional connectivity prediction of language and memory

In a subgroup of subjects ( n = 88) FC matrices from resting state fMRI were available for a direct comparison on language and memory scores. SDC and FDC maps for language scores (Fig. 6, top and middle rows) were similar to those previously obtained in the larger sample. SDC predicted well language scores (R 2 = 0.47), while FDC predicted weakly (R 2 =0.16). Direct FC maps also predicted well language scores (R 2 =0.42), with two kinds of connections being the most predictive: inter-hemispheric and left 4 right intra-hemisphere FC decreases (Fig. 6, bottom row). Statistical comparisons showed that SDC was more predictive than FDC ( z = -2.351, P = 0.019), and FC more predictive than FDC ( z = 2.908, P = 0.004; Supplementary Table 2).

The same analysis was carried out on spatial memory ( n = 71) (Fig. 7) and verbal memory ( n = 71) scores (Supplementary Fig. 6). For spatial memory, SDC

predicted 8% of the variability while FDC was not predictive (R 2 = 0.00). In contrast direct FC measures provided moderate accuracy (R 2 = 0.20) with strong inter-hemispheric positive weights associated with strong memory performance, and strong intra-hemispheric weights associated with poor memory performance (replicating Siegel et al. , 2016). The difference in predictive accuracy between SDC and FC models was not statistically significant.

For verbal memory, SDC maps explained a small portion of variability (R 2 = 0.10), as in the whole sample. FDC prediction was not different from chance (no map is presented because the model weights were not statistically reliable). Functional MRI-FC connectivity predicted significantly memory scores (R 2 = 0.15), with poor performance associated with abnormally high intra-hemispheric FC. Further, in this case no significant difference was detected between SDC and FC. Results for other conditions are shown in Table 1 and Supplementary Table 2, motor domains showed no prediction from FDC (R 2 = 0.00), visual domains showed high prediction from fMRIFC (40%, left) and from FDC (52%, right) but affected by low sample size ( n = 20 and 28), attention showed low prediction from all methods.

### Summary of multivariate ridge regression results

Table 1 shows a summary of the ridge regression analyses across different domains.

|

*[picture on PDF page 10]*

**Figure labels:**
- Language n = 88
- Structural disconnection (SDC)
- R²= 0.47
- Patient
- R
- -fit
- -3
- -2
- -1
- 0
- 1
- Functional disconnection (FDC)
- Prediction
- R²= 0.16
- r-fMRI changes
- R²=0.42
- Real

Several notable results are apparent. First, lesion and SDC explain comparable proportions of variance across behavioural domains. In fact, models using both lesion and SDC maps as input for the ridge regression (last column) never performed better than the best model trained on a single type of map, with the only exception of attention (lesion R 2 = 0.18; SDC R 2 = 0.16; lesion + SDC = R 2 = 0.60). In some domains, e.g. motor right, SDC prediction is higher than for lesions (R 2 = 0.42 versus 0.28), while in others, e.g. visual deficits, the opposite is true. Second, FDC prediction is always worse in all domains. Only for right visual field deficits FDC performs comparably to lesion and SDC (lesion R 2 = 0.58; SDC R 2 = 0.33; FDC R 2 = 0.38). Third, critically, the variability of functional disconnection maps across subjects can be expressed through a small number of components, i.e. individual maps are low-dimensional. In contrast, a larger number of components is necessary to explain the spatial variability of lesions and individual SDC maps. The lower dimensionality of FDC maps makes the discrimination of patients with different levels of behavioural impairment more challenging. Univariate maps (Supplementary material) show that all three methods provide biologically plausible localization. The SDC method shows a more widespread, and bilateral, anatomical disconnection pattern than the lesion maps. The FDC approach shows surprisingly more focal patterns of functional disconnection with an overall lower statistical sensitivity, as for example in the motor domain where the critical lesions are subcortical.

### Discussion

The present study aimed to predict the behavioural variability of neurological deficits at 2 weeks post-stroke, based on different types of information: the structural damage caused by the stroke itself, the inferred network disconnection based on structural connectivity (SDC) or functional connectivity (FDC) maps, and the FC measured directly with fMRI.

The SDC and FDC maps estimate the putative network-level disconnection induced by stroke lesions through estimation of either the white matter tracts that go through the lesion (SDC) or the temporal correlation of the fMRI signal between the lesion and the rest of the brain (FDC). The corresponding SDC and FDC voxel-wise maps hence provide a probabilistic measure of the affected white matter pathways or the correlation of different brain regions with the site of damage.

The indirect disconnection approach is beautifully simple. It has been successfully applied for mapping functional network dysfunction in a variety of neuropsychiatric disorders (Darby et al. , 2018 a , b ; Ferguson et al. , 2019; Kim et al. , 2019; Padmanabhan et al. , 2019) and to locate potential cortical sites of non-invasive brain stimulation (Joutsa et al. , 2019).

|

*[picture on PDF page 11]*

**Figure labels:**
- Memory S n = 71
- Structural disconnection (SDC)
- R²= 0.08
- Patient
- R
- -2
- -1
- 0
- 1
- 2
- Functional disconnection (FDC)
- Prediction
- R²= 0.00
- ---fit
- r-fMRI changes
- R²= 0.20
- --fit
- Real

***Table 1 Ridge regression analysis: R 2 values***

|   | Subjects, n | Lesion | SDC | FDC | Lesion+SDC |
|---|---|---|---|---|---|
| Language | 116 | R 2 = 0.48; comp = 58 | R 2 = 0.41; comp = 29 | R 2 = 0.06; comp = 6 | R 2 = 0.46; comp = 87 |
| Motor left (right lesion) | 51 | R 2 = 0.35; comp = 26 | R 2 = 0.37; comp = 18 | R 2 = 0.12; comp = 5 | R 2 = 0.38; comp = 44 |
| Motor right (left lesion) | 57 | R 2 = 0.28; comp = 28 | R 2 = 0.42; comp = 21 | R 2 = 0.08; comp = 5 | R 2 = 0.42; comp = 49 |
| Visual left (right lesion) | 25 | R 2 = 0.40; comp = 12 | R 2 = 0.23; comp = 14 | R 2 = 0.18; comp = 5 | Overfit; comp = 27 |
| Visual right (left lesion) | 31 | R 2 = 0.58; comp = 15 | R 2 = 0.33; comp = 16 | R 2 = 0.38; comp = 6 | Overfit; comp = 31 |
| Verbal memory | 88 | R 2 = 0.06; comp = 43 | R 2 = 0.05; comp = 27 | R 2 = 0.01 b ; comp = 6 | R 2 = 0.05; comp = 70 |
| Spatial memory | 88 | R 2 = 0.19; comp = 43 | R 2 = 0.19; comp = 27 | R 2 = 0.04; comp = 6 | R 2 = 0.19; comp = 70 |
| Attention (visual field bias) | 94 | R 2 = 0.18; comp = 50 | R 2 = 0.16; comp = 29 | R 2 = 0.10; comp = 7 | R 2 = 0.60; comp = 79 |
| Subgroup of patients who underwent both r-fMRI and indirect estimation of structural and functional disconnection | Subgroup of patients who underwent both r-fMRI and indirect estimation of structural and functional disconnection | Subgroup of patients who underwent both r-fMRI and indirect estimation of structural and functional disconnection | Subgroup of patients who underwent both r-fMRI and indirect estimation of structural and functional disconnection | Subgroup of patients who underwent both r-fMRI and indirect estimation of structural and functional disconnection | Subgroup of patients who underwent both r-fMRI and indirect estimation of structural and functional disconnection |
|   | Subjects, n | SDC | FDC | fMRI-FC |   |
| Language | 88 | R 2 = 0.47; comp = 28 | R 2 = 0.16; comp = 6 | R 2 = 0.42; comp = 79 |   |
| Motor left (right lesion) | 34 | R 2 = 0.19; comp = 15 | R 2 = 0.00 b ; comp = 5 | R 2 = 0.14; comp = 31 |   |
| Motor right (left lesion) | 48 | R 2 = 0.34; comp = 20 | R 2 = 0.01; comp = 5 | R 2 = 0.08; comp = 43 |   |
| Visual left (right lesion) | 20 | R 2 = 0.15; comp = 12 | R 2 = 0.07; comp = 5 | R 2 = 0.40; comp = 18 |   |
| Visual right (left lesion) | 28 | R 2 = 0.46; comp = 16 | R 2 = 0.52; comp = 6 | R 2 = 0.00 b ; comp = 25 |   |
| Verbal memory | 71 | R 2 = 0.10; comp = 26 | R 2 = 0.00 b ; comp = 6 | R 2 = 0.15; comp = 64 |   |
| Spatial memory | 71 | R 2 = 0.08; comp = 26 | R 2 = 0.00 b ; comp = 6 | R 2 = 0.20; comp = 64 |   |
| Attention (visual field bias) | 73 | R 2 = 0.05; comp = 28 | R 2 = 0.03; comp = 7 | R 2 = 0.05; comp = 66 |   |

comp = number of PCA components; fMRI-FC = resting state MRI-functional connectivity; PCA = principal component analysis.

> a 93% PCA components (overfitting with 95%).

b Model not significant.

The method, recognized as a significant innovation (e.g. shortlisted for the 2019 Nature Research Award for Driving Global Impact), requires only clinical structural scans to infer network abnormalities that would otherwise require expensive, time-consuming, and complicated fMRI or tractography analysis. The accuracy of the method relies on replication in

|

independent samples, the anatomical specificity of the disconnection for the syndrome or condition of interest, the underlying anatomical plausibility, and, more recently, the correlation with behavioural scores (Ferguson et al. , 2019).

Here we planned to examine the behavioural relevance of these indirect disconnection methods towards predicting neurological impairment post-stroke. Accurate behavioural prediction is essential to use these methods for brain-behaviour correlation in neuropsychology, outcome prediction, and as an assessment of potential responsiveness to novel interventions. We applied multivariate machine learning to predict the behavioural variance of multiple post-stroke deficits using lesions (as a gold standard) versus SDC versus FDC maps. In the second set of analyses, for domains that are strongly predicted by fMRI-FC measures (e.g. memory, attention), we compared behavioural prediction by indirect versus direct measures of network disconnection.

The results were straightforward. SDC predicts behavioural deficits similarly to lesion information. FDC always performs worse or even at chance level for several domains, such as language and memory. Direct fMRI-FC measures are always superior to FDC.

### Why is structural disconnection a better measure than functional disconnection?

SDC predicted behavioural scores to a level comparable to lesion location. The behavioural variance predicted with lesions ranged in the language, vision, and motor domains between 28% and 58%. The corresponding range for SDC was 23-42%. In contrast, the range for FDC was 0.060.38%, with most scores in the low teens (Table 1).

The main reason for the superiority of lesions and SDC is the more significant variability of spatial components necessary to summarize patterns of structural damage or disconnection, as compared to patterns of functional disconnection (FDC). The number of principal components was always higher for lesion and SDC than FDC patterns (Table 1). Higher spatial variability means that more components are available to model the behavioural data.

Why are FDC patterns low dimensional? There are both biological and methodological explanations. Biologically, functional networks are low dimensional even in healthy subjects. From any voxel in the brain at 3 T with a repetition time of 2 s, most subjects show  7-13 networks (Power et al. , 2011; Yeo et al. , 2011; Hacker et al. , 2013). Moreover, methodologically, networks that are segregated in healthy subjects may mix in the FDC maps because the lesion, from which the maps are derived, contain voxels belonging to different networks. An example of network mixing is illustrated by the occipital lesions that cause visual field deficits. These lesions yield FDC maps that include not only the visual network but also the ventral attention network with predictive voxels in anterior cingulate. Finally, most lesions are localized in the subcortical nuclei and white matter. Functional connectivity cortical maps from subcortical nuclei are not very selective because of local spread of the blood oxygenation level-dependent (BOLD) signal correlation (e.g. in the caudate or thalamus). In the white matter, the BOLD signal is low signal-to-noise, and lesions can damage neighbouring white matter pathways common to multiple networks. Since the inputs to the ridge regression are the principal components of the different maps, empirically we noted that FDC maps have lower dimensionality than SDC or lesion maps, thus decreasing their sensitivity for modelling purposes.

The discovery that FDC patterns have low dimensionality despite the relatively high heterogeneity of stroke lesion topography is problematic for the sensitivity of the method. Even though most FDC patterns were anatomically plausible, hence suggestive of true functional disconnection, the behavioural analysis shows that these patterns do not discriminate accurately between patients with more or less severe deficits. Take for instance the FDC maps for language or verbal memory (Figs 4 and 5). They include a left-lateralized language network that includes a right postero-lateral cerebellum component (Petersen et al. , 1988; Guell et al. , 2018), and a medial parietal-frontal network for memory deficits that significantly overlap with a circuit recently identified for amnesia (Ferguson et al. , 2019). However, these FDC maps account for only 4% and 1% of the variance in language and memory scores, respectively.

### What do functional disconnection maps show?

FDC maps pick up anatomically plausible networks, and perform slightly better in terms of behavioural prediction when the lesions are localized mainly in cortex, but their behavioural accuracy is low when the lesions are in the white matter. A good case example is the FDC map for visual deficits. The lesion map shows cortical damage in the occipital lobe; correspondingly, FDC show gorgeous visual network disconnection maps with a high behavioural prediction accuracy (R 2 = 38% for right visual deficits; R 2 = 18% for left visual deficits) (Fig. 2 and Supplementary Fig. 1). In contrast, consider the motor deficit maps in which the most predictive lesioned voxels are in the white matter of the corona radiata and descending motor pathways. Notably, the FDC maps show motor and premotor cortical regions, but with low behavioural accuracy (right motor R 2 = 12; left motor R 2 = 8%) (Fig. 3 and Supplementary Fig. 2). However, there are also counter-examples. In language, the predictive damage involves large swaths of peri-sylvian grey matter; FDC maps are anatomically plausible, yet, the behavioural prediction is poor.

### Are structural disconnection maps better than lesions in predicting behaviour?

The answer to this question is no. SDC maps are helpful for localization of structural disconnection beyond the lesion, thus providing a view of the impact of stroke on the whole brain. The behavioural prediction from SDC is comparable to lesions; however, it does not account for independent variance, except for attention, as shown from the joint models (Table 1).

The widespread pattern of estimated SDC poses a puzzle: is there a true alteration of structural connectivity, or is this an artefact of the method? This will have to wait for a direct comparison of indirect versus direct methods for structural disconnection. Griffis et al. (2019) recently showed a strong relationship between empirically measured changes in FC and SDC patterns, thus giving support to the idea that longrange anatomical disconnection occurs and mediate the functional disconnection effects of focal lesions. We also know that fMRI-FC recovers in parallel with behaviour (Park et al. , 2011; Corbetta, 2012). In combination, these findings suggest that SDC may occur acutely and recover over time. Strong evidence for white matter remodelling is still scarce in humans (Umarova et al. , 2017) while animal models show that transient structural connectivity changes occur and are modulated by treatment (Ding et al. , 2008; Zijden et al ., 2008; Li et al. , 2009). White matter remodelling after focal injury is a crucial topic for future investigations.

### Shall we acquire functional MRI to measure functional connectivity abnormalities?

The answer to this question is, in general, yes. As in our published work, we found that fMRI-FC significantly predicts cognitive deficits, especially memory and visuospatial attention (He et al. , 2007; Baldassarre et al. , 2014; Siegel et al. , 2016; and this study). A decrement of inter-hemispheric correlation in homologous regions of different networks and an increase of intra-hemispheric correlation between regions of networks typically segregated best predict behavioural deficits. In contrast, we found limited behavioural valence in the FDC maps. Therefore, indirect functional disconnection methods are no surrogate at this stage of direct fMRI measures if behavioural correlation is a goal.

### Caveats and limitations

The FDC approach in this study slightly differs from the FDC method already published. In previous reports (Boes et al. , 2015; Fasano et al. , 2017; Darby et al. , 2018 a , b ), specificity of the network disconnection maps was examined using a dichotomous split between two groups of subjects, e.g. subjects with or without a specific symptom or syndrome. Here we predict continuous behavioural scores of a specific type of deficit, e.g. language dysfunction. Also, we did not apply a threshold to the functional connectivity maps. Finally, the number of healthy controls was lower but the quality of the functional MRI was higher. We do not think that any of these factors influenced the results.

|

Another limitation is the possibility that our maps of structural and functional disconnection over-estimated the degree of disconnection due to the younger age of the healthy subjects control group. For instance, Geerligs et al. (2015) compared functional connectivity at the network level in a group of young (mean age = 20.6 years) and older adults (50-55 years old), and showed no difference in the somatomotor and visual networks, but weaker connectivity in the cognitive networks of older adults. However, the anatomical details of the disconnection maps were not the primary concern, rather, their ability to explain behavioural variance. Foulon et al. (2018) measured whether SDC maps vary with age. They generated disconnection maps in cohort of subjects with different ages, and quantified similarities of SDC at the whole-brain level in young (21-30 years old) versus older subjects (later decades). They found disconnection maps to be similar across decades. Therefore, we feel that this limitation is minor, and does not affect our main conclusions.

### Conclusions

The indirect mapping of structural and functional disconnections after focal lesions may highlight widespread alterations of network organization, but caution is necessary when interpreting disconnection for behavioural correlation. The 'dys-connectome' (SDC) method predicts similarly to lesions likely because the information provided by the pattern of structural disconnection is essentially coincident with the structural damage of the lesion. The FCD method includes both direct and indirect connections, but it is not very sensitive. The FDC method is not a proxy for direct fMRI measures of network dysfunction.

### Acknowledgements

Drs Michael Ferguson and Michael Fox for providing us with data from Ferguson et al. (2019).

### Funding

Padova Neuroscience Center PhD doctorate program to A.S.; NIH grant R01 NS095741; FLAG-ERA JTC 2017; Dipartimento Eccellenza del MIUR Neuro-DiP; Progetto Strategico UniPD to M.C.; the European Research Council (ERC) under the European Union's Horizon 2020 research and innovation programme (grant agreement No. 818521) to M.TdS.; the Italian Ministry of Health under Grant Number RF-2013-02359306 to M.Z.

### Competing interests

The authors report no competing interests.

|

### Supplementary material

Supplementary material is available at Brain online.

### References

- Adolphs R, Damasio H, Tranel D, Cooper G, Damasio AR. A role for somatosensory cortices in the visual recognition of emotion as revealed by three-dimensional lesion mapping. J Neurosci 2000; 20: 2683-90.
- Avants BB, Tustison NJ, Song G, Cook PA, Klein A, Gee JC. A reproducible evaluation of ANTs similarity metric performance in brain image registration. Neuroimage 2011; 54: 2033-44.
- Baldassarre A, Ramsey L, Hacker CL, Callejas A, Astafiev SV, Metcalf NV, et al. Large-scale changes in network interactions as a physiological signature of spatial neglect. Brain 2014; 137: 3267-83.
- Baldassarre A, Ramsey LE, Siegel JS, Shulman GL, Corbetta M. Brain connectivity and neurological disorders after stroke. Curr Opin Neurol 2016; 29: 706-13.
- Baron JC, D'Antona R, Pantano P, Serdaru M, Samson Y, Bousser MG. Effects of thalamic stroke on energy metabolism of the cerebral cortex. A positron tomography study in man. Brain 1986; 109: 1243-59.
- Baron JC, Levasseur M, Mazoyer B, Legault-Demare F, Mauguie `re F, Pappata S, et al. Thalamocortical diaschisis: positron emission tomography in humans. J Neurol Neurosurg Psychiatry 1992; 55: 935-42.
- Benedict R. Brief Visuospatial Memory Test-revised: Professional Manual. Odessa, FL: Psychol Assessment Resour; 1997.
- Boes AD, Prasad S, Liu H, Liu Q, Pascual-Leone A, Caviness VS Jr, et al. Network localization of neurological symptoms from focal brain lesions. Brain 2015; 138: 3061-75.
- Brandt J, Benedict RHB. Hopkins Verbal Learning Test-revised: Professional manual. Odessa, Florida: Psychological Assesment Resources; 2001.
- Broca PP. Loss of speech, chronic softening, and partial destruction of the anterior left lobe of the brain. Bull Soc Anthropol 1861; 2: 235-8.
- Carrera E, Tononi G. Diaschisis: past, present, future. Brain 2014; 137: 2408-22.
- Carter AR, Astafiev SV, Lang CE, Connor LT, Rengachary J, Strube MJ, et al. Resting interhemispheric functional magnetic resonance imaging connectivity predicts performance after stroke. Ann Neurol 2010; 67: 365-75.
- Carter AR, Patel KR, Astafiev SV, Snyder AZ, Rengachary J, Strube MJ, et al. Upstream dysfunction of somatomotor functional connectivity after corticospinal damage in stroke. Neurorehabil Neural Repair 2012; 26: 7-19.
- Catani M, Thiebaut de Schotten M. Atlas of human brain connections. Oxford: Oxford University Press; 2012.
- Catani M, Dell'acqua F, Vergani F, Malik F, Hodge H, Roy P, et al. Short frontal lobe connections of the human brain. Cortex 2012; 48: 273-91.
- Chauhan S, Vig L, De Filippo De Grazia M, Corbetta M, Ahmad S, et al. A comparison of shallow and deep learning methods for predicting cognitive performance of stroke patients from MRI lesion images. Front Neuroinform 2019; 13: 53.
- Cohen AL, Soussand L, Corrow SL, Martinaud O, Barton JJS, Fox MD. Looking beyond the face area: lesion network mapping of prosopagnosia. Brain 2019; 142: 3975-90.
- Corbetta M. Functional connectivity and neurological recovery. Dev Psychobiol 2012; 54: 239-53.
- Corbetta M, Shulman GL. Control of goal-directed and stimulusdriven attention in the brain. Nat Rev Neurosci 2002; 3: 201-15.
- Corbetta M, Kincade MJ, Lewis C, Snyder AZ, Sapir A. Neural basis and recovery of spatial attention deficits in spatial neglect. Nat Neurosci 2005; 8: 1603-10.
- Corbetta M, Ramsey L, Callejas A, Baldassarre A, Hacker CD, Siegel JS, et al. Common behavioral clusters and subcortical anatomy in stroke. Neuron 2015; 85: 927-41.
- Corbetta M, Siegel JS, Shulman GL. On the low dimensionality of behavioral deficits and alterations of brain network connectivity after focal injury. Cortex 2018; 107: 229-37.
- Corp DT, Joutsa J, Darby RR, Delnooz CCS, van de Warrenburg BPC, Cooke D, et al. Network localization of cervical dystonia based on causal brain lesions. Brain 2019; 142: 1660-74.
- Darby RR, Horn A, Cushman F, Fox MD. Lesion network localization of criminal behavior. Proc Natl Acad Sci USA 2018a; 115: 601-6.
- Darby RR, Joutsa J, Burke MJ, Fox MD. Lesion network localization of free will. Proc Natl Acad Sci USA 2018b; 115: 10792-7.
- Darby RR, Joutsa J, Fox MD. Network localization of heterogeneous neuroimaging findings. Brain 2019; 142: 70-9.
- Darby RR, Laganiere S, Pascual-Leone A, Prasad S, Fox MD. Finding the imposter: brain connectivity of lesions causing delusional misidentifications. Brain 2017; 140: 497-507.
- Ding G, Jiang Q, Li L, Zhang L, Zhang ZG, Ledbetter KA, et al. Magnetic resonance imaging investigation of axonal remodeling and angiogenesis after embolic stroke in sildenafil-treated rats. J Cereb Blood Flow Metab 2008; 28: 1440-8.
- Dosenbach NU, Visscher KM, Palmer ED, Miezin FM, Wenger KK, Kang HC, et al. A core system for the implementation of task sets. Neuron 2006; 50: 799-812.
- Du J, Yang F, Zhang Z, Hu J, Xu Q, Hu J, et al. Early functional MRI activation predicts motor outcome after ischemic stroke: a longitudinal, multimodal study. Brain Imaging Behav 2018; 12: 1804-13.
- Fasano A, Laganiere SE, Lam S, Fox MD. Lesions causing freezing of gait localize to a cerebellar functional network. Ann Neurol 2017; 81: 129-41.
- Feng W, Wang J, Chhatbar PY, Doughty C, Landsittel D, Lioutas VA, et al. Corticospinal tract lesion load: an imaging biomarker for stroke motor outcomes. Ann Neurol 2015; 78: 860-70.
- Ferguson MA, Lim C, Cooke D, Darby RR, Wu O, Rost NS, et al. A human memory circuit derived from brain lesions causing amnesia. Nat Commun 2019; 10: 3497.
- Fiorelli M, Blin J, Bakchine S, Laplane D, Baron JC. PET studies of cortical diaschisis in patients with motor hemi-neglect. J Neurol Sci 1991; 104: 135-42.
- Fischer DB, Boes AD, Demertzi A, Evrard HC, Laureys S, Edlow BL, et al. A human brain network derived from coma-causing brainstem lesions. Neurology 2016; 87: 2427-34.
- Forkel SJ, Catani M. Lesion mapping in acute stroke aphasia and its implications for recovery. Neuropsychologia 2018; 115: 88-100.
- Foulon C, Cerliani L, Kinkingne ´hun S, Levy R, Rosso C, Urbanski M, et al. Advanced lesion symptom mapping analyses and implementation as BCBtoolkit. Gigascience 2018; 7: 1-17.
- Fox MD. Mapping symptoms to brain networks with the human connectome. N Engl J Med 2018; 379: 2237-45.
- Geerligs L, Renken RJ, Saliasi E, Maurits NM, Lorist MM. A brainwide study of age-related changes in functional connectivity. Cereb Cortex 2015; 25: 1987-99.
- Gla ¨ scher J, Tranel D, Paul LK, Rudrauf D, Rorden C, Hornaday A, et al. Lesion mapping of cognitive abilities linked to intelligence. Neuron 2009; 61: 681-91.
- Glasser MF, Coalson TS, Robinson EC, Hacker CD, Harwell J, Yacoub E, et al. A multi-modal parcellation of human cerebral cortex. Nature 2016; 536: 171-8.
- Glasser MF, Sotiropoulos SN, Wilson JA, Coalson TS, Fischl B, Andersson JL, et al. The minimal preprocessing pipelines for the Human Connectome Project. Neuroimage 2013; 80: 105-24.
- Golland P, Fischl B. Permutation tests for classification: towards statistical significance in image-based studies. In: C Taylor, JA Noble, editors. Information Processing in Medical Imaging. Lecture Notes in Computer Science. Berlin: Springer; 2003. pp.330-341.
- Gordon EM, Laumann TO, Adeyemo B, Huckins JF, Kelley WM, Petersen SE. Generation and evaluation of a cortical area parcellation from resting-state correlations. Cereb Cortex 2016; 26: 288-303.

- Grefkes C, Fink GR. Connectivity-based approaches in stroke and recovery of function. Lancet Neurol 2014; 13: 206-16.
- Griffis JC, Metcalf NV, Corbetta M, Shulman GL. Structural disconnections explain brain network dysfunction after stroke. Cell Rep 2019; 28: 2527-40.e9.
- Guell X, Gabrieli JDE, Schmahmann JD. Triple representation of language, working memory, social and emotion processing in the cerebellum: convergent evidence from task and seed-based resting-state fMRI analyses in a single large cohort. Neuroimage 2018; 172: 437-49.
- Hacker CD, Laumann TO, Szrama NP, Baldassarre A, Snyder AZ, Leuthardt EC, et al. Resting state network estimation in individual subjects. Neuroimage 2013; 82: 616-33.
- Harlow JM. Passage of an iron rod through the head. Boston Med Surg J 1848; 39: 389-93.
- He BJ, Shulman GL, Snyder AZ, Corbetta M. The role of impaired neuronal communication in neurological disorders. Curr Opin Neurol 2007; 20: 655-60.
- He BJ, Snyder AZ, Vincent JL, Epstein A, Shulman GL, Corbetta M. Breakdown of functional connectivity in frontoparietal networks underlies behavioral deficits in spatial neglect. Neuron 2007; 53: 905-18.
- Hillis AE, Wityk RJ, Barker PB, Beauchamp NJ, Gailloud P, Murphy K, et al. Subcortical aphasia and neglect in acute stroke: the role of cortical hypoperfusion. Brain 2002; 125: 1094-104.
- Hodgson K, Adluru G, Richards LG, Majersik JJ, Stoddard G, Adluru N, et al. Predicting motor outcomes in stroke patients using diffusion spectrum MRI microstructural measures. Front Neurol 2019; 10: 72.
- Hope TMH, Leff AP, Prejawa S, Bruce R, Haigh Z, Lim L, et al. Right hemisphere structural adaptation and changing language skills years after left hemisphere stroke. Brain 2017; 140: 1718-28.
- Ionta S, Heydrich L, Lenggenhager B, Mouthon M, Fornari E, Chapuis D, et al. Multisensory mechanisms in temporo-parietal cortex support self-location and first-person perspective. Neuron 2011; 70: 363-74.
- Ivanova MV, Dragoy O, Kuptsova SV, Yu Akinina S, Petrushevskii AG, et al. Neural mechanisms of two different verbal working memory tasks: a VLSM study. Neuropsychologia 2018; 115: 25-41.
- Ivanova MV, Isaev DY, Dragoy OV, Akinina YS, Petrushevskiy AG, Fedina ON, et al. Diffusion-tensor imaging of major white matter tracts and their role in language processing in aphasia. Cortex 2016; 85: 165-81.
- Joutsa J, Horn A, Hsu J, Fox MD. Localizing Parkinsonism based on focal brain lesions. Brain 2018; 141: 2445-56.
- Joutsa J, Shih LC, Fox MD. Mapping Holmes tremor circuit using the human brain connectome. Ann Neurol 2019; 86: 812-20.
- Kim NY, Hsu J, Talmasov D, Joutsa J, Soussand L, Wu O, et al. Lesions causing hallucinations localize to one common brain network. Mol Psychiatry 2019; doi: 10.1038/s41380-019-0565-3. [Epub ahead of print]
- Klein A, Andersson J, Ardekani BA, Ashburner J, Avants B, Chiang MC, et al. Evaluation of 14 nonlinear deformation algorithms applied to human brain MRI registration. Neuroimage 2009; 46: 786-802.
- Laganiere S, Boes AD, Fox MD. Network localization of hemichoreahemiballismus. Neurology 2016; 86: 2187-95.
- Le Cessie S, Van Houwelingen JC. Ridge estimators in logistic regression. J R Stat Soc Ser C (Appl Stat) 1992; 41: 191-201.
- Li L, Jiang Q, Ding G, Zhang L, Zhang ZG, Li Q, et al. MRI identification of white matter reorganization enhanced by erythropoietin treatment in a rat model of focal ischemia. Stroke 2009; 40: 936-41.
- Lin DD, Kleinman JT, Wityk RJ, Gottesman RF, Hillis AE, Lee AW, et al. Crossed cerebellar diaschisis in acute stroke detected by dynamic susceptibility contrast MR perfusion imaging. AJNR Am J Neuroradiol 2009; 30: 710-5.

|

- Nachev P, Coulthard E, Ja ¨ ger HR, Kennard C, Husain M. Enantiomorphic normalization of focally lesioned brains. Neuroimage 2008; 39: 1215-26.
- Padmanabhan JL, Cooke D, Joutsa J, Siddiqi SH, Ferguson M, Darby RR, Soussand L, et al. A human depression circuit derived from focal brain lesions. Biol Psychiatry 2019; 86: 749-58.
- Park CH, Chang WH, Ohn SH, Kim ST, Bang OY, Pascual-Leone A, et al. Longitudinal changes of resting-state functional connectivity during motor recovery after stroke. Stroke 2011; 42: 1357-62.
- Perani D, Di Piero V, Lucignani G, Gilardi MC, Pantano P, Rossetti C, et al. Remote effects of subcortical cerebrovascular lesions: a SPECT cerebral perfusion study. J Cereb Blood Flow Metab 1988; 8: 560-7.
- Petersen SE, Fox PT, Posner MI, Mintun M, Raichle ME. Positron emission tomographic studies of the cortical anatomy of single-word processing. Nature 1988; 331: 585-9.
- Phan TG, Chen J, Donnan G, Srikanth V, Wood A, Reutens DC. Development of a new tool to correlate stroke outcome with infarct topography: A proof-of-concept study. Neuroimage 2010; 49: 127-33.
- Power JD, Cohen AL, Nelson SM, Wig GS, Barnes KA, Church JA, et al. Functional network organization of the human brain. Neuron 2011; 72: 665-78.
- Ramsey LE, Siegel JS, Lang CE, Strube M, Shulman GL, Corbetta M. Behavioural clusters and predictors of performance during recovery from stroke. Nat Hum Behav 2017; 1: 0038.
- Ripolle ´s P, Marco-Pallare ´s J, de Diego-Balaguer R, Miro ´ J, Falip M, Juncadella M, et al. Analysis of automated methods for spatial normalization of lesioned brains. Neuroimage 2012; 60: 1296-306.
- Robb RA, Hanson DP. A software system for interactive and quantitative visualization of multidimensional biomedical images. Australas Phys Eng Sci Med 1991; 14: 9-30.
- Schaechter JD, Fricker ZP, Perdue KL, Helmer KG, Vangel MG, Greve DN, et al. Microstructural status of ipsilesional and contralesional corticospinal tract correlates with motor skill in chronic stroke patients. Hum Brain Mapp 2009; 30: 3461-74.
- Schlaug G, Marchina S, Norton A. Evidence for plasticity in whitematter tracts of patients with chronic Broca's aphasia undergoing intense intonation-based speech therapy. Ann N Y Acad Sci 2009; 1169: 385-94.
- Seeley WW, Menon V, Schatzberg AF, Keller J, Glover GH, Kenna H, et al. Dissociable intrinsic connectivity networks for salience processing and executive control. J Neurosci 2007; 27: 2349-56.
- Siegel JS, Ramsey LE, Snyder AZ, Metcalf NV, Chacko RV, Weinberger K, et al. Disruptions of network connectivity predict impairment in multiple behavioral domains after stroke. Proc Natl Acad Sci USA 2016; 113: E4367-76.
- Siegel JS, Seitzman BA, Ramsey LE, Ortega M, Gordon EM, Dosenbach NUF, et al. Re-emergence of modular brain networks in stroke recovery. Cortex 2018; 101: 44-59.
- Sperber C, Karnath HO. On the validity of lesion-behaviour mapping methods. Neuropsychologia 2018; 115: 17-24.
- Stinear CM, Barber PA, Smale PR, Coxon JP, Fleming MK, Byblow WD. Functional potential in chronic stroke patients depends on corticospinal tract integrity. Brain 2007; 130 (Pt 1): 170-80.
- Thiebaut de Schotten M, Dell'Acqua F, Ratiu P, Leslie A, Howells H, Cabanis E, et al. From Phineas Gage and Monsieur Leborgne to H.M.: revisiting disconnection syndromes. Cereb Cortex 2015; 25: 4812-27.
- Thiebaut de Schotten M, Dell'Acqua F, Forkel SJ, Simmons A, Vergani F, Murphy DG, et al. A lateralized brain network for visuospatial attention. Nat Neurosci 2011; 14: 1245-6.
- Thiebaut de Schotten M, Dell'Acqua F, Valabregue R, Catani M. Monkey to human comparative anatomy of the frontal lobe association tracts. Cortex 2012; 48: 82-96.
- Thiebaut de Schotten M, Ffytche DH, Bizzi A, Dell'Acqua F, Allin M, Walshe M, et al. Atlasing location, asymmetry and inter-subject

|

- variability of white matter tracts in the human brain with MR diffusion tractography. Neuroimage 2011; 54: 49-59.
- Thiebaut de Schotten M, Tomaiuolo F, Aiello M, Merola S, Silvetti M, Lecce F, et al. Damage to white matter pathways in subacute and chronic spatial neglect: a group study and 2 single-case studies with complete virtual 'in vivo' tractography dissection. Cereb Cortex 2014; 24: 691-706.
- Umarova RM, Beume L, Reisert M, Kaller CP, Klo ¨ppel S, Mader I, et al. Distinct white matter alterations following severe stroke: longitudinal DTI study in neglect. Neurology 2017; 88: 1546-55.
- Volle E, Levy R, Burgess PW, A new era for lesion-behavior mapping of prefrontal functions. In: DT Stuss, RT Knight, editors. Principles of frontal lobe function. Oxford: Oxford University Press; 2013. p. 500-523.
- von Monakow C. Die Lokalisation im Grosshirn: und der Abbau der Funktion durch kortikale Herde [Localization in the Cerebrum and
- the Degeneration of Functions Through Conical Sources]. Wiesbaden, Germany: Bergmann; 1914.
- Vu AT, Auerbach E, Lenglet C, Moeller S, Sotiropoulos SN, Jbabdi S, et al. High resolution whole brain diffusion imaging at 7T for the Human Connectome Project. Neuroimage 2015; 122: 318-31.
- Wernicke C. Der aphasische Symptomenkomplex. Breslau: Cohn & Weigert; 1874.
- Yeo BT, Krienen FM, Sepulcre J, Sabuncu MR, Lashkari D, Hollinshead M, et al. The organization of the human cerebral cortex estimated by intrinsic functional connectivity. J Neurophysiol 2011; 106: 1125-65.
- Zijden JP, Toorn A, Marel K, Dijkhuizen RM. Longitudinal in vivo MRI of alterations in perilesional tissue after transient ischemic stroke in rats. Exp Neurol 2008; 212: 207-12.
- Zihl J, Heywood CA. The contribution of single case studies to the neuroscience of vision. Psych J 2016; 5: 5-17.