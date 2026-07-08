*[picture on PDF page 1]*

**Figure labels:**
- C1
- ←

### Disruptions of network connectivity predict impairment in multiple behavioral domains after stroke

Joshua Sarfaty Siegel a,1 , Lenny E. Ramsey a , Abraham Z. Snyder b , Nicholas V. Metcalf a , Ravi V. Chacko c , Kilian Weinberger d,e , Antonello Baldassarre a,f , Carl D. Hacker c , Gordon L. Shulman a , and Maurizio Corbetta a,b,c,g,h

a Department of Neurology, Washington University School of Medicine, St. Louis, MO 63110; b Mallinckrodt Institute of Radiology, Washington University School of Medicine, St. Louis, MO 63110; c Department of Biomedical Engineering, Washington University School of Medicine, St. Louis, MO 63110; d Department of Computer Science, Washington University School of Medicine, St. Louis, MO 63110; e Department of Computer Science, Cornell University, Ithaca, NY 14850; f Department of Neuroscience, Imaging, and Clinical Sciences, University of Chieti G. d ' Annunzio, 66013 Chieti, Italy; g Department of Anatomy & Neurobiology, Washington University School of Medicine, St. Louis, MO 63110; and h Department of Neuroscience, University of Padua, 35128 Padova, Italy

Edited by Danielle S. Bassett, University of Pennsylvania, Philadelphia, PA, and accepted by Editorial Board Member Michael S. Gazzaniga May 31, 2016 (received for review October 29, 2015)

Deficits following stroke are classically attributed to focal damage, but recent evidence suggests a key role of distributed brain network disruption. We measured resting functional connectivity (FC), lesion topography, and behavior in multiple domains (attention, visual memory, verbal memory, language, motor, and visual) in a cohort of 132 stroke patients, and used machine-learning models to predict neurological impairment in individual subjects. We found that visual memory and verbal memory were better predicted by FC, whereas visual and motor impairments were better predicted by lesion topography. Attention and language deficits were well predicted by both. Next, we identified a general pattern of physiological network dysfunction consisting of decrease of interhemispheric integration and intrahemispheric segregation, which strongly related to behavioral impairment in multiple domains. Network-specific patterns of dysfunction predicted specific behavioral deficits, and loss of interhemispheric communication across a set of regions was associated with impairment across multiple behavioral domains. These results link key organizational features of brain networks to brain -behavior relationships in stroke.

stroke | functional connectivity | interhemispheric | memory | language

A lthough structural damage from stroke is focal, remote dysfunction can occur in regions of the brain distant from the area of damage (1, 2). The set of regions that are directly damaged or indirectly affected is embedded within a larger functional network that is in dynamic balance with other networks in the brain. This framework posits that a lesion in a single location in the brain has the ability to disrupt brain functions far beyond the lesion boundaries (3 -5).

Numerous correlates of remote physiological dysfunction have been proposed, including abnormal task recruitment of contralesional brain areas (6 -8), disruption of metabolism (9) or regional cerebral blood flow (10, 11), and more recently disruption of signal coherence (12 -15).

However, there is only a limited understanding of how remote physiological dysfunction is related to lesion topography (14, 16). Moreover, the behavioral relevance of reported physiological changes is unclear. Although some studies have reported significant correlation with behavioral impairment, the total amount of behavioral variance explained is unknown. Finally, because mechanisms of remote dysfunction have typically been examined in relatively small groups of individuals, their generalization at the population level is unknown. As a result, physiological measures of brain function are not used in the evaluation and treatment of stroke victims.

More traditional lesion -symptom mapping studies have also used statistical methods to relate lesion topography to the severity of different behavioral deficits (17, 18). An implicit assumption of these studies is that the strength of association between structural damage and behavior is the same irrespective of the behavior that is measured. However, it is also possible that more integrative functions (attention, memory, and executive) rely to a greater extent on distributed processing than sensory and motor functions. Surprisingly, the degree to which lesion topography accounts for the variability across different deficits is mostly unknown (for exceptions, see refs. 19 -21) As a result, lesion -behavior predictions also have not entered the main stream of clinical neuroscience.

In this study, we hypothesize that structural damage caused by stroke produces robust, physiological changes in network coherence that explain behavioral variance at the population level. We interpret the effects of these physiological changes in terms of the known functional organization of the brain. Regions subserving similar functions are grouped into networks, i.e., sets of regions that are highly connected (e.g., motor cortex and supplementary motor area for motor behavior). Dysfunction of these networks should underlie deficits in corresponding behavioral domains.

We use a similar framework to understand the weights of functional connections in accounting for behavior. Based on the normal organization of brain networks, we hypothesize that sensorimotor functions, which are more dependent on input/output pathways and tend to be associated with networks that sit peripherally in the brain ' s overall graph, will be more strongly dependent on structural variables (e.g., lesion topography), and

### Significance

Since the early days of neuroscience, the relative merit of structural vs. functional network accounts in explaining neurological deficits has been intensely debated. Using a large stroke cohort and a machine-learning approach, we show that visual memory and verbal memory deficits are better predicted by functional connectivity than by lesion location, and visual and motor deficits are better predicted by lesion location than functional connectivity. In addition, we show that disruption to a subset of cortical areas predicts general cognitive deficit (spanning multiple behavior domains). These results shed light on the complementary value of structural vs. functional accounts of stroke, and provide a physiological mechanism for general multidomain deficits seen after stroke.

Author contributions: J.S.S., L.E.R., N.V.M., A.B., G.L.S., and M.C. designed research; J.S.S., L.E.R., N.V.M., G.L.S., and M.C. performed research; J.S.S., A.Z.S., N.V.M., R.V.C., K.W., and C.D.H. contributed new reagents/analytic tools; J.S.S., L.E.R., and A.Z.S. analyzed data; and J.S.S., A.Z.S., G.L.S., and M.C. wrote the paper.

The authors declare no conflict of interest.

This article is a PNAS Direct Submission. D.S.B. is a guest editor invited by the Editorial Board.

Data deposition: Neuroimaging and neuropsychological data are publicly available at https://cnda.wustl.edu/app/template/Login.vm. Matlab scripts were written to perform all analyses described. Scripts used for the main analyses (Figs. 1 -3 and 6) can be found at www.nil.wustl.edu/labs/corbetta/resources/.

1 To whom correspondence should be addressed. Email: jssiegel@wustl.edu.

This article contains supporting information online at www.pnas.org/lookup/suppl/doi:10. 1073/pnas.1521083113/-/DCSupplemental.

|

|

integrative functions (e.g., attention, memory) associated with more central networks will be more dependent on disrupted patterns of cortical coherence.

We evaluated these predictions within a clinically relevant sample, i.e., a large population of subacute stroke patients ( n = 132) shown to be representative of a larger clinical population. Neurological impairments were described using behavioral measures that capture a large amount of intersubject variance (19). Structural magnetic resonance imaging (MRI) and resting functional magnetic resonance imaging (R-fMRI) were used to measure lesion topography, and functional connectivity (FC) of brain networks, respectively. Structural and functional data were then entered into a ridge regression machine-learning algorithm to predict deficits at the single subject level in six behavioral domains: attention, visual memory, verbal memory, language, motor, and visual. Deficits were predicted using either a lesion-deficit model or an FC-deficit model, allowing us to compare the relative importance of lesion topography and network dysfunction in accounting for different behavioral deficits. Finally, FC-deficit models were used not only to identify the specific brain connections that were most predictive of deficits in each behavioral domain, but also to identify connections that predicted deficits across behavioral domains.

### Results

Abnormal FC Patterns in Stroke. We recruited 132 first-time symptomatic stroke patients 1 -2 wk after stroke, and 31 demographically matched controls. Patients were assessed with a broad neuropsychological battery measuring performance across six behavioral domains (vision, motor, language, visual memory, verbal memory, and attention), lesions were manually identified with multimodal segmentation, and 30 min of R-fMRI data were acquired. Twenty-one patients were excluded for hemodynamic lags (22, 23) and 11 patients and 4 controls were excluded for excessive head motion (24). After exclusion, 100 stroke patients and 27 age-matched controls were studied. To investigate the general effects of stroke, we compared FC features in the entire stoke cohort to those of the age-matched control cohort. A cortical parcellation of 324 regions was divided into 13 networks based on Gordon et al. (25) (Figs. S1 and S2). Within-network connections were further classified as interhemispheric homotopic, ipsilesional intrahemispheric, and contralesional intrahemispheric connections.

Fig. 1 shows the distribution of FC values in patients (red) and controls (blue) for three types of within-network connections: homotopic, ipsilesional, and contralesional. Decreased homotopic FC was the most prominent difference between patients and controls [ t -statistic = 4.26, P = 10 -4 , false discovery rate (FDR) correction]. This effect was also tested for individual networks and significant differences were observed in all networks except cingulo-opercular (CON), ventral attention network (VAN), and default mode network (DMN) (Fig. S3 B ). A three-factor analysis of variance (ANOVA) on homotopic FC revealed a significant effect of group ( P = 3 × 10 -22 ), a significant effect of resting state network (RSN) ( P = 4 × 10 -7 ), no significant effect of subject head motion ( P = 0.26), and no significant interaction. By contrast, within-network intrahemispheric connectivity was not significantly changed in both the ipsilesional and contralesional hemispheres (Fig. 1 B and C ).

To determine whether differences observed between groups might result from differences in global neuronal fluctuations, R-fMRI data were additionally processed without global signal regression but instead using CompCor to remove nonneuronal sources of blood-oxygenation-level dependent (BOLD) signal variance (26, 27). We found that functional connectivity analyses conducted without global signal regression produced highly similar results (Fig. S3).

Next, we compared connectivity values between networks. Only a single RSN pair showed significant FC changes in the stroke group. Ipsilesional dorsal attention network (DAN)-DMN FC connectivity was negative in controls but less negative in patients (Fig. 1 D and Fig. S3) ( t -statistic = -3.15, P = 0.0021). Further, we found a strong relationship between decreased DAN homotopic FC and increased ipsilesional DAN-DMN FC ( r = -0.61, P = 9e-10; Fig. 1 E ), and no correlation in age-matched controls ( r = 0.25, P = 0.19), with a significant difference between the two groups (Fisher r -toz -transform; z = -4.24, P < 0.001). Other networks showed a similar relationship between ipsilesional network segregation (from the DMN) and homotopic integration, but to a lesser degree [somatomotor dorsal (SMD), r = -0.45, P = 5.2e-6; somatomotor ventral (SMV), r = -0.28, P = 0.0103; CON, r = -0.56, P = 4.4e-7; VAN, r = -0.24, P = 0.0043; P values are FDR corrected for eight comparisons].

We tested the relationship between damage and homotopic FC (averaged across the brain) using a univariate correlation with lesion size and a multivariate correlation with lesion topography. We

*[picture on PDF page 2]*

**Figure labels:**
- A
- B
- C
- D
- E
- work)
- (within hetwork)
- (DAN-DMI
- 0.4
- N.S.
- 十
- p
- 0.2
- 0
- 1
- 0.5
- -0.5
- ts
- Controls
- † significant after permutation testing of all within- and be

|

*[picture on PDF page 3]*

**Figure labels:**
- A
- B
- C
- D
- FLAIR
- T1
- lesion-deficit
- ω weights
- (prediction)
- 1
- 0
- -1
- +
- R
- -2
- n
- r²=.448
- (ωTxi−yi)²+λ||ω||²
- -2 -1 0 1
- FC-deficit
- ωmatrix
- 324-ROI Parcellation
- FC
- i=1
- 72 7
- O
- Top
- 200
- r²=.234
- 0 1
- Left LesionRight Lesion
- with behavior

found that lesion size predicted average homotopic connectivity ( r = -0.46, P = 6 × 10 -7 ), but the prediction was not improved by adding information about lesion topography (multivariate prediction: r = 0.46, P = 7 × 10 -7 ). This result shows that average homotopic FC is decreased by a similar amount following lesions of similar sizes, irrespective of the topography of the lesions. Therefore, a decrease in homotopic FC is a general consequence of stroke. However, the topography of the decrease in FC (i.e., which connections show a decreased as opposed to the overall magnitude of the decrease) likely depends on the topography of the lesion.

Potential sources of unwanted variance were compared with homotopic connectivity to determine effects on FC differences within or between groups. Group and individual differences in homotopic FC were not significantly explained by head motion, percentage of time with eyes open, or lag laterality (Fig. S4).

Prediction of Behavioral Deficits Based on Lesion and FC. Next, we investigated the extent to which structural data and functional data explained deficits in the stroke patients. Following manual lesion segmentation and R-fMRI processing (Fig. S1), we used lesion maps, and vectorized FC matrices to generate lesion-deficit and FC-deficit models using leave-one-out ridge regression (Fig. 2).

variance explained ( r 2 ) by lesions (white bars) or by FC (black bars) in each model. The two rows of scatter plots show predicted and measured scores used to determine model accuracy for every subject. For simplicity, left and right motor and visual predictions have been combined to only show contralesional prediction. The significance of each model was determined using permutation tests: attention ( n = 80, lesion P = 4 × 10 -4 , FC P < 1 × 10 -4 ), visual memory ( n = 79, lesion P = 9 × 10 -4 , FC P < 1 × 10 -4 ), verbal memory ( n = 79, lesion P = 1.5 × 10 -3 , FC P < 1 × 10 -4 ), language ( n = 98, lesion P < 1 × 10 -4 , FC P < 1 × 10 -4 ), left motor ( n = 91, lesion P < 1 × 10 -4 , FC P = 1.1 × 10 -3 ), right motor ( n = 91, lesion P < 1 × 10 -4 , FC P < 1 × 10 -4 ), left visual ( n = 53, lesion P = 4 × 10 -4 , FC P = 0.0104), and right visual ( n = 53, lesion P = 1 × 10 -4 , FC P = 0.0902) (Fig. S5). An additional control analysis confirmed that FC-deficit model accuracies surpassed chance when information from lesion location was included in null models ( Supporting Information and Fig. S5).

Fig. 3 shows the accuracy of lesion-deficit and FC-deficit model predictions in each domain. The bar graphs indicate percent of Prediction accuracy of the FC and lesion models was directly compared using a two-tailed Wilcoxon paired signed rank test of prediction errors. After false discovery rate correction, four domains showed significant differences between lesion-deficit and FC-deficit model accuracy. Visual memory (lesion = 10.9%, FC = 36.4%, P = 0.015) and verbal memory (lesion = 18.7%, Fig. 3. Lesion-deficit and FC-deficit model accuracies vary by domain. The bar graph shows percent of variance explained across the six behavioral domains. White bars are lesion-deficit models, black bars are FC-deficit models. Lesion location predicts deficit significantly better in motor and visual domains. FC predicts deficit significantly better in the visual memory, and verbal memory domains. Statistical comparison between lesion-deficit and FC-deficit models (indicated by asterisks) were performed using a Wilcoxon signed rank test of prediction error and were FDR corrected. Horizontal gray lines represent P = 0.05 cutoffs for the null model generated by permuting domain scores 10,000 times for each domain. All models perform significantly better than chance. The scatter plots show the comparison between predicted and measured scores from lesiondeficit models ( Upper ) and FC-deficit models ( Lower ). Behavior scores are a composite of multiple tests in each domain and are on a z-normalized (mean = 0, SD = 1) scale. Motor and visual deficits were predicted separately for each hemisphere and the contralateral side, but combined for visualization.

*[picture on PDF page 3]*

**Figure labels:**
- Lesion
- ■ FC
- 95%%CI
- Permutatior
- 95% cutoff
- Wilcoxon
- * p < 0.05, FD
- corrected
- 1
- 0
- -21
- r²=.323
- -1
- -2
- -2 -1
- r²=.109
- r²=.187
- -3
- -3 -2 -1
- r²=.646
- -2-1
- r²=.448
- 4
- r²=.499
- Right strol
- Left stroke
- 1.
- - fit + 95%

|

|

FC = 41.6%, P = 0.007) were better predicted by FC than lesion location; whereas, motor (lesion = 44.8%, FC = 23.4%, P = 0.009) and visual deficits (lesion = 49.9%, FC = 13.3%, P = 0.013) were better predicted by lesion location than FC. Attention showed a trend for higher prediction by FC, and language was equally predicted by both inputs (Attention -lesion = 32.3%, FC = 45.0%, P = 0.074; Language -lesion = 64.6%, FC = 51.1%, P = 0.21). For a complete description of permutation testing and control analyses, see Supporting Information .

To determine if domain prediction results generalized to individual task performance scores, FC and lesion models were also generated for every performance measure included in the generation of domain scores. Some measures were predicted poorly. However, for measures that showed good prediction accuracy, the prediction differences observed in the domain scores frequently generalized to the raw scores (Fig. S6).

Topography of Behaviorally Predictive FC. Weights from the FC and lesion prediction models were averaged across all leave-one-out models and projected back onto the brain (Fig. 4; see also Fig. S7 for further visualization of FC-deficit and lesion-deficit weights). In Fig. 4, green edges indicate that increased FC predicted better behavior, and orange edges indicate that decreased FC predicted better behavior. It should be noted that positive and negative weights do not imply positive or negative FC values, only a positive or negative relationship with the behavior of interest. The top 200 strongest weights are illustrated. The size of each node is relative to the total contribution of all of its connections to the model.

stronger FC correlates with poorer performance. To compare the types of connections that were most heavily weighted in each domain, the top 1% of weights from each FC-deficit model were divided into four groups -interhemispheric positive, interhemispheric negative, within-hemisphere positive, and within-hemisphere negative. The bar graphs in Fig. 4 show the average contribution of each of the four types of connections across all prediction models. An ANOVA confirmed a significant difference in the contribution of connection types ( P = 1.6 × 10 -6 ) to deficit prediction, with positive interhemispheric weights showing the greatest contribution followed by negative within-hemisphere weights. Language is an exception because a significant prediction comes from positive intrahemispheric weights in the left hemisphere, i.e., accurate language performance depends on communication between regions of the left hemisphere.

In Fig. 5, the average contribution of all positive connections within an RSN (circle radius) and between RSN pairs (line thickness) is illustrated for each FC -behavior prediction. In attention and memory domains, connections between RSNs are particularly prominent. By contrast, language weights are more limited to connections within the auditory network, motor weights to connections within auditory and somatomotor networks, and visual weights to connections within visual and somatomotor networks, and connections between RSNs are not as prominent. To quantify this observation, we measured the ratio of positive weights within RSNs to positive weights between RSNs: attention: 1.431, visual memory: 1.526, verbal memory: 1.499, language = 1.768, motor = 1.605, visual = 1.624.

Considered side by side, common features of the FC-deficit maps are apparent (Fig. 4). Specifically, the strongest weights tend to be positive interhemispheric, i.e., stronger FC correlates with better performance; and negative intrahemispheric, i.e., Prediction of Common Behavioral Impairment. To further investigate shared features between models, we used multitask learning. All domains were predicted by two sets of weights simultaneously. One set ( ω k ) was optimized by domain and the other set ( ω o ) was

*[picture on PDF page 4]*

**Figure labels:**
- Attention
- Visual
- Verbal
- Language
- Memory
- A
- L
- R
- Inter-hem
- +
- within-hem +
- within-hem
- P
- 60
- 30
- 圭主
- +HM
- -HM
- WH-
- Edge Weight
- L Motor
- R Motor
- LVisual
- R Visual
- with behavior
- 8-model
- Mean
- 大
- 主主主主
- 圭主主主
- 圭主圭主
- 圭主主

|

***Fig. 4. Most predictive connections and nodes for each FC-deficit model. ( Left ) The top 200 connections driving each FC-behavior model are projected back on to a semitransparent cerebrum (PALS atlas). Green connections indicate positive weights (increased FC predicts better performance), and orange connections indicate negative weights (increased FC predicts worse performance). The subset of the 324 parcels included in the top 200 weights are displayed as spheres, sized according to their contribution to the model. ( Lower ) Weights from each FC-behavior model are divided into four groups: interhemispheric positive, interhemispheric negative, intrahemispheric positive, and intrahemispheric negative. Bars indicate the average contribution of each of the four groups. The average across models is shown at the bottom right. An ANOVA indicates a significant difference in contribution of the four connection types ( P = 1.6 × 10 -6 ).***

shared across all domains (Eq. 1 ). This procedure enabled us to differentiate domain-specific versus shared (across domain) correlates of neurological deficit in these eight domains. The optimized multitask learning model explained 28.7% of the variance across all patients and all five domains. The shared across-domain weights were explored to understand features of connectivity that predict common deficit across domains (Fig. 6). The shared weights involved overwhelmingly interhemispheric connections (Fig. 6 B ). Positive shared weights (green bars; reduced FC corresponds to worse deficit across domains) were distributed across RSNs, but weighed most heavily on dorsal attention network, cingulo-opercular network, auditory network, and somatomotor dorsal network (Fig. 6 D and E ).

### Discussion

We identified robust changes in network synchrony (measured with R-fMRI) after focal injury poststroke, and determined their behavioral significance in six domains (attention, visual memory, verbal memory, language, motor, and visual). In addition, we compared the behavioral significance of network synchrony and lesion location across domains.

We found that changes in inter- and intrahemispheric FC following stroke showed a consistent pattern across networks (Fig. 1 and Fig. S3). The largest changes in FC between patients and controls involved decreases in interhemispheric FC. Decreases in interhemispheric FC were accompanied by increases in intrahemispheric FC between networks that are normally segregated (e.g., DAN and DMN). Moreover, decreased interhemispheric FC was also the feature of FC that best predicted behavioral deficits within the patient sample. Decrement in specific RSNs predicted deficits in corresponding behavioral domains, consistent with the large-scale network organization of the brain (Figs. 3 -5). A multitask model revealed that reduced interhemispheric FC in a set of nodes predicted shared deficits across domains (Fig. 6). Jointly, the inter- and intrahemispheric changes in FC constitute a general physiological network phenotype of stroke injury.

We also found a fundamental difference between behavioral domains. Memory deficits were better predicted by functional connectivity than by lesion location, and motor and visual deficits were better predicted by lesion location than by functional connectivity. Language deficits were well predicted by both and attention deficits showed a trend toward FC > lesion (Fig. 3 and Fig. S6). These results suggest that the behavioral significance of network synchrony was greater for associative domains; whereas, the behavioral significance of lesion topography was greater for sensorimotor domains. Below, we suggest that this division follows naturally from the greater dependence of associative functions on large-scale distributed interactions between brain systems, and of sensory-motor functions on input -output pathways.

*[picture on PDF page 5]*

**Figure labels:**
- Visual
- Attention
- Motor
- Memory
- Verbal
- Language
- Auditory
- Dorsal Attention
- Somato-motor D.
- Cingulo-opercular
- Front-parietal
- Somato-motor V.
- Ventral Attention
- Default

Interhemispheric Connectivity and Stroke. Two lines of evidence from our study converge on the conclusion that disrupted communication between the hemispheres is a central feature of stroke. First, the largest and most consistent change in FC from controls to patients involved a decrease in interhemispheric, homotopic FC. Second, alterations in interhemispheric connections showed the strongest association with behavioral impairment across nearly all domains. Reductions in interhemispheric coherence were predominant not only in the functional connectivity related to specific deficits (12, 13, 28 -30), but also in the multidomain FC that generalized across deficits (Fig. 6). This result reveals a key insight into how a stroke disrupts cognition: severe strokes not only cause local damage but produce a disruption of interhemispheric balance.

The physiology underlying reduced interhemispheric FC following a stroke remains unclear. One explanation is that the structural connections or mechanisms that mediate the transfer of signals between the hemispheres might be damaged or functioning abnormally. For example, reduced interhemispheric FC is accompanied by decreases in manganese transfer from the contralesional to the ipsilesional hemisphere (29), consistent with a reduction in callosal fibers. Alternatively, signals in the damaged and undamaged hemispheres might undergo hemisphere-specific changes that reduce their correlation. EEG signals (power, coherence) are abnormal both within and across hemispheres poststroke, and correlate with behavioral impairment (31, 32).

We find that the global average reduction in interhemispheric FC could be partly predicted by lesion load ( r = 0.46), but could not be better predicted with additional information about lesion location. This is not to say that specific lesions do not disrupt interhemispheric FC in specific areas or networks. Prior studies have identified RSN-specific relationships between lesion location and FC disruption (14, 33). However, our results establish disrupted interhemispheric FC as a common effect of strokes, rather than a result of damage to specific structures such as the corpus callosum or thalamus. Further work is needed to better elucidate the cause of reduced interhemispheric coherence.

In our cohort, a decrease in interhemispheric FC was correlated with an increase in intrahemispheric FC between DMN and DAN (Fig. 1 E ). A similar phenomenon has been observed in monkeys following disconnection of the corpus callosum and anterior commissure (34). This suggests that integration of RSNs across the hemispheres is linked to segregation of task-positive and task-negative RSNs within the hemispheres. The poststroke reduction in integration and segregation can be thought of as resulting from a single disruptive process such as previously observed reductions in brain network modularity (35) and information capacity (36).

Structure vs. Function -Relative Contribution to Different Behavioral Deficits. In 1885, Carl Wernicke made the prescient observation that sensory and motor functions could be localized, but higher cognitive functions were instead dependent on communication across distributed brain networks.

|

|

*[picture on PDF page 6]*

**Figure labels:**
- A
- B
- C
- D
- E
- Multi-task learning model prediction
- (8 domains)
- 2[
- r²=.287
- -4
- -2
- 0
- 2
- Domain Scores
- with behavior
- Shared weights by
- Shared weights projected to
- connection type
- RSN
- Surface
- somato-
- motor
- 75
- dorsal
- 50
- 25
- auditory
- ±
- +HM
- -HM
- attention
- cingulo-
- total weight (∑|ωl)
- opercular
- 13

The acoustic images find their abode within the cortical terminals of the acoustic nerve, the visual images, within the cortical endings of the optic nerve, and the olfactory images in that of the olfactory nerve . . . Movement representation could be located in the cortical sites of the motor nerve origins... Any higher psychic process could not, I reasoned, be localized, but rested on the mutual interaction of these fundamental psychic elements mediated by means of their manifold connections via the association fibers (37).

However, only recently have the tools been available to quantitatively test this hypothesis. Here, we found that associative domains were better predicted by FC than lesion topography, and sensorimotor domains such as vision and motor were better predicted by lesion topography than FC.

Lesion-deficit mapping has been the cornerstone of functional localization since the early nineteenth century (38). The basic principle is that specific functions are performed in specific parts of the brain (38, 39), and therefore careful anatomoclinical correlations between behavioral impairment and structural damage can identify the part of the brain necessary for that function. One tacit assumption, however, is that sensory, motor, and cognitive functions are equally affected by structural damage. A second important set of results in our work instead emphasizes a fundamental distinction between cognitive and sensorimotor domains in relation to how well structural or functional connectivity damage explain behavioral variability. Below, we discuss the implication of our observations in understanding and comparing sensorimotor, memory, and language deficits.

Sensorimotor deficit. Behaviors that are directly dependent on the immediate interface with the environment can be localized with high fidelity in the cerebral cortex and depend on input/output white matter pathways. Accordingly, lesion location either in specialized cortex, underlying white matter, or connected subcortical regions, reliably predicted hemianopia (50% of variance) and hemiparesis (45% of variance). By contrast, FC explained a significantly smaller amount of behavioral variance, and motor and visual FC-deficit models showed positive weights that were largely confined within the corresponding damaged RSN rather than reflecting between-network connections, i.e., the connectivity changes occurred mainly within the damaged network. These results are consistent with the peripheral location of the visual and sensorimotor networks in the overall brain graph (40), and com-

|

putational studies showing that damage to peripheral nodes do not cause widespread alterations in network structure (3). Visual and verbal memory deficit. Visual memory and verbal memory deficit scores were better predicted by FC changes than lesion topography. The visual and verbal memory scores included measures of encoding and retrieval of visual shapes and words at short and long time intervals (Tables S1 -S3). These functions require the coordination of an ensemble of mental operations and computations occurring in parallel across distributed networks (41 -43). Correspondingly, weights in the memory FC-deficit models were distributed across many brain systems, in comparison with the more constrained distribution of motor and visual model weights.

Lesion-behavior studies have not clearly isolated a critical lesion site for visual or verbal memory. Likewise, a large literature on neglect indicates that a similar syndrome emerges for lesions at multiple cortical and subcortical sites (44). Single unit studies have localized signals consistent with spatial working memory in multiple cortical and subcortical regions that are connected by reciprocal anatomical pathways, suggesting that functions like memory and attention are distributed across many regions of the brain (42, 45, 46). This idea is also consistent with a large number of neuroimaging studies (47, 48).

Language deficit. Language impairments represent an interesting counterpoint to both sensorimotor and cognitive deficits. Both lesion topography and FC accounted for > 40% of behavioral variance, with no significant difference in accuracy between the two models. FC regions predictive of language impairment involved canonical language regions, but also bilateral connections within and between other RSNs (Figs. 4 and 5). Unlike other domains, language deficit showed substantial dependence on left intrahemispheric connectivity. Language disorders can arise not only from pure disruption of language processing, but also from disruption of bilaterally distributed support processes including auditory processing, visual attention as in reading, and motor planning for speech (49 -51). That both lesion and FC predicted above 40% of variance supports the increasingly accepted theory that language function relies on highly localized brain regions as well as bilaterally distributed brain networks and connections (52). Damage to any of these structures can compromise the communication and function of the language system as a whole.

Caveats/Limitations. The accuracy of brain network models depends in part on the brain regions used in the models. Important considerations for FC analysis include: ( i ) which the structures included, and ( ii ) how those structures are parcellated. We chose a cortical parcellation previously demonstrated to optimally separate FC data in healthy young adults (25). However, data from the cerebellum and basal ganglia were not included in this parcellation. Inclusion of these structures may improve FC-deficit models in future studies. Second, differences in connectivity between patients and age-matched controls could result from differences in parcellation fit (i.e., how well the parcellation matches real boundaries between functional brain areas) between groups. We assessed parcellation fit by measuring parcel homogeneity (53). We found a small but significant difference in parcel homogeneity (Fig. S2) with patients showing lower homogeneity than age-matched controls (paired t test: t -stat = 8.0, P < 0.0001). Thus, some univariate FC differences reported between patients and controls may result from greater homogeneity in controls than patients. However, the small difference in homogeneity is unlikely to account for the large difference in FC reported in Fig. 1.

In addition, because our stroke cohort was chosen to represent the normal clinical population, lesions were not evenly distributed across the cortex. Lesion-deficit accuracy may be further improved in a more evenly sampled population.

As is the case with multivariate regression, a larger sample might also improve prediction accuracy. This is especially the case for the visual domain, in which only 58 subjects were included. Still, FC- and lesion-deficit models within each domain use identical subject, thus comparisons drawn between the two should be robust.

Homotopic FC is more stable across time and across conditions than other types of functional connections (54). It is possible that our FC-deficit models load most heavily on interhemispheric FC because this stability enables greater fidelity in measurement of disruption. However, both the difference between patients and controls and the ability of interhemispheric FC to predict subtle deficits associated with disruption to the contralesional hemisphere suggests that this is not the only explanation for our observations.

### Conclusions

The present work points to the fundamental importance of interhemispheric integration and intrahemispheric segregation, and their disruption poststroke. More generally, this study links major features of the pathophysiology of stroke to the normal organization of brain networks. Deficits in behavioral domains involve abnormal FC in corresponding networks, and deficits across domains emphasize homotopic FC in a small number of key brain regions. Similarly, abnormal connectivity best accounts for behavioral deficits involving associative functions such as memory that involve interactions between brain systems. Conversely, FC is less predictive in sensorimotor domains, and the predictive connections that are observed tend to be local and within-network.

### Experimental Procedures

Subject Enrollment. Written informed consent was obtained from all participants in accordance with the Declaration of Helsinki and procedures established by the Washington University in Saint Louis Institutional Review Board. All participants were compensated for their time. All aspects of this study were approved by the Washington University School of Medicine (WUSM) Internal Review Board.

Subject enrollment and demographics are described in detail in ref. 19. Firsttime stroke patients were recruited by a research coordinator through the inpatient service at Barnes-Jewish Hospital and the Rehabilitation Institute of St. Louis. Inclusion criteria were: ( i ) age 18 or older, ( ii ) first symptomatic stroke, ischemic or intraparenchymal hemorrhagic etiology, ( iii ) clinical evidence of motor, language, attention, visual, or memory deficits based on neurological examination, and ( iv ) time of enrollment < 2 wk poststroke onset. Exclusion criteria were: ( i ) the inability to maintain wakefulness during testing,

( ii ) the presence of other neurological, psychiatric, or medical conditions that preclude active participation in research and/or may alter the interpretation of the behavioral/imaging studies (e.g., dementia, schizophrenia), or limit life expectancy to less than 1 y (e.g., cancer or congestive heart failure class IV), ( iii ) evidence of clinically significant periventricular white matter disease (equal or > grade 5 of ref. 55), and ( iv ) contraindications for MRI including claustrophobia or scanner-incompatible implants. In total, 6,260 charts were screened; 132 patients met all inclusion criteria and completed the entire subacute protocol (mean age 52.8 y with range 22 -77; 119 right handed, 63 female, 64 right hemisphere).

Demographically matched controls ( n = 31) were recruited and underwent the same behavioral and imaging examinations. Inclusion criteria for controls were: healthy adult matched to stroke study population by age, gender, handedness, and level of education. Exclusion criteria were: ( i ) a positive history of neurological, psychiatric, or medical abnormalities preventing participation in research activities, ( ii ) a history of atherosclerotic (coronary, cerebral, peripheral) artery disease, or ( iii ) an abnormal neurological examination with signs of central nervous system dysfunction. In total, 31 controls completed the entire subacute protocol [mean age 55.7 y (SD = 11.5) with a range 21 -83].

Neuropsychological Assessment. All participants underwent a behavioral battery that included several assessments of motor, language, attention, memory, and visual function following each scanning session (Table S1). Imaging and behavioral testing session usually were performed on the same day. Scores were only recorded for tasks that subjects were able to complete. Therefore, different domains have different numbers of subjects. Dimensionality reduction was performed on the performance data as described in detail in ref. 19. First, tasks were categorized as attention, memory, language, motor, and vision. A principal components analysis (PCA) was run on each category. In attention, the first component described 26.1% of variance and was strongly related to measures of visual field bias (Posner task: left/right accuracy differences: r = 0.83; Mesulam: center of cancellation: r = 0.75) and general performance (accuracy, r = -0.41). In memory, the first two components accounted for 66.2% of variance in all measures of related to memory. The first component was highly related to measures of delayed recall of visual information [brief visuospatial memory test (BVMT) delayed recall: r = 0.81] and the second component was related to recall of verbal information [Hopkins verbal learning test (HVLT) delayed recall: r = 0.93]. In language, the first component accounted for 77.3% of variance and was highly related to comprehension and production. In motor the first two components described left and right body deficit and explained 43.0% and 34.6% of variance, respectively.

Visual field deficits were measured in a computerized perimetry examination (Humphrey Field Analysis Model 750i). Each eye was tested using the central 24 -2 threshold SITA-FAST protocol. PCA was not done because vision was assessed with a single functional test. Instead, the two vision domain scores used were the mean pattern deviation scores in the left and right hemifields. All tests included and correlation with the domain scores are shown in Table S1.

In total, eight domains were used for FC-deficit and lesion-deficit modeling. Scores in each domain were continuous and were normalized to have a mean of 0 and SD of 1 in patients, and lower score indicating greater deficit. With deficit defined as at least 2 SDs below controls, we found the following: ( i ) attention (31 with deficit/88 total patients), ( ii ) visual memory (27/88), ( iii ) verbal memory (30/88), ( iv ) language (33/112), ( v ) left motor (37/106), ( vi ) right motor (39/106), ( vii ) left visual (13/58), and ( viii ) right visual (10/58).

MRI and Lesion Analysis. Individual T1 MRI images were registered to the Montreal Neurological Institute brain using FSL (FMRIB Software Library) FNIRT (FMRIB nonlinear imaging registration tool) (56). Lesions were manually segmented on individual structural MRI images (T1-weighted MPRAGE, T2-weighted spin echo images, and FLAIR images obtained 1 -3 wk poststroke) using the Analyze biomedical imaging software system (www. mayoclinic.org; ref. 57). Two board-certified neurologists (M.C. and Alexandre Carter) reviewed all segmentations. Special attention was given to distinguish lesion from cerebral spinal fluid (CSF), hemorrhage from surrounding vasogenic edema, and to identify the degree of periventricular white matter damage present. In hemorrhagic strokes, edema was included in the lesion. A neurologist (M.C.) reviewed all segmentations a second time, paying special attention to the borders of the lesions and degree of white matter disease. The staff that was involved in segmenting or in reviewing the lesions was blind to the individual behavioral data. Atlas-registered segmented lesions ranged from 0.02 to 82.97 cm 3 with a mean of 10.15 cm 3 (SD = 13.94 cm 3 ). Lesions were summed to display the number of patients with structural damage for each voxel (Fig. S1).

|

|

R-fMRI Acquisition. Patients were studied 2 wk (mean = 13.4 d, SD = 4.8 d), 3 mo (mean = 112.5 d, SD = 18.4 d), and 1 y (mean = 393.5 d, SD = 55.1 d) poststroke onset. Controls were studied twice at an interval of 3 mo. All imaging was performed using a Siemens 3T Tim-Trio scanner at WUSM and the standard 12-channel head coil. The MRI protocol included structural, functional, pulsed arterial spin labeling (PASL) and diffusion tensor scans. Structural scans included: ( i ) a sagittal T1-weighted MP-RAGE (TR = 1,950 msec, TE = 2.26 msec, flip angle = 90°, voxel size = 1.0 × 1.0 × 1.0 mm); ( ii ) a transverse T2-weighted turbo spin echo (TR = 2,500 msec, TE = 435 msec, voxel size = 1.0 × 1.0 × 1.0mm); and ( iii ) sagittal fluid attenuated inversion recovery (FLAIR) (TR = 7,500 msec, TE = 326 msec, voxel size = 1.5 × 1.5 × 1.5 mm). PASL acquisition parameters were: TR = 2,600 msec, TE = 13 msec, flip angle = 90°, bandwidth 2.232 kHz/Px, and FoV 220 mm; 120 volumes were acquired (322 s total), each containing 15 slices with slice thickness 6- and 23.7-mm gap. Resting state functional scans were acquired with a gradient echo EPI sequence (TR = 2,000 msec, TE = 27 msec, 32 contiguous 4-mm slices, 4 × 4 mm in-plane resolution) during which participants were instructed to fixate on a small cross in a low luminance environment. Six to eight resting state fMRI runs, each including 128 volumes (30 min total), were acquired.

fMRI Data Preprocessing. Preprocessing of fMRI data included: ( i ) compensation for asynchronous slice acquisition using sinc interpolation; ( ii ) elimination of odd/even slice intensity differences resulting from interleaved acquisition; ( iii ) whole brain intensity normalization to achieve a mode value of 1,000; ( iv ) removal of distortion using synthetic field map estimation and spatial realignment within and across fMRI runs; and ( v ) resampling to 3-mm cubic voxels in atlas space including realignment and atlas transformation in one resampling step. Cross-modal (e.g., T2 weighted to T1 weighted) image registration was accomplished by aligning image gradients (58). Cross-model image registration in patients was checked by comparing the optimized voxel similarity measure to the 97.5 percentile obtained in the control group. In some cases, structural images were substituted across sessions to improve the quality of registration.

Functional Connectivity Processing. FC processing was similar to previous work from the laboratory (28), with the addition of surface projection and processing steps developed by the Human Connectome Project (59). First, data were passed through several additional preprocessing steps: ( i ) regressors were computed based on freesurfer segmentation; ( ii ) removal by regression of the following sources of spurious variance: ( a ) six parameters obtained by rigid body correction of head motion, ( b ) the signal averaged over the whole brain, ( c ) signal from ventricles and CSF, and ( d ) signal from white matter; ( ii ) temporal filtering retaining frequencies in the 0.009 -0.08-Hz band; and ( iii ) frame censoring. The first four frames of each BOLD run were excluded. Frame censoring was computed using framewise displacement with a threshold of 0.5 mm. This frame-censoring criterion was uniformly applied to all R-fMRI data (patients and controls) before functional connectivity computations. Subjects with less than 120 usable BOLD frames were excluded (13 patients, 3 controls).

Surface Processing. Surface generation and processing of functional data followed procedures similar to Glasser et al. (59), with additional consideration for cortical segmentation in stroke patients. First, anatomical surfaces were generated for each subject ' s T1 MRI using FreeSurfer automated segmentation (60). This included brain extraction, segmentation, generation of white matter and pial surface, inflation of the surfaces to a sphere, and surface shape-based spherical registration to the subjects ' native ' surface to the fs_average surface. Segmentations were manually checked for accuracy. For patients in whom the stroke disrupted automated segmentation, or registration, values within lesioned voxels were filled with normal atlas values before segmentation, and then masked immediately after (seven patients). The left and right hemispheres were then resampled to 164,000 vertices and registered to each other (61), and finally downsampled to 10,242 vertices each for projection of functional data.

Following preprocessing of BOLD data, volumes were sampled to each subject ' s individual surface (between white matter and pial surface) using a ribbon-constrained sampling available in Connectome Workbench. Voxels with a high coefficient of variation (0.5 SDs above the mean coefficient of variation of all voxels in a 5-mm sigma Gaussian neighborhood) were excluded from volume to surface mapping (59). Time courses were then smoothed along the 10,242 vertex surface using a 6-mm FWHM Gaussian kernel. Finally, time courses of all vertices within a parcel are averaged to make a parcelwise time series.

Functional connectivity was then computed between each parcel using Fisher z -transformed Pearson correlation. Connectivity for any parcel that

|

fell within the boundaries of the lesion was removed from univariate analyses and set to zero for multivariate models.

Homotopic FC was computed for each region by measuring FC with the corresponding vertices on the opposite hemisphere. Subjects with severe hemodynamic lags (greater than 0.5-s interhemispheric difference) measured from R-fMRI (23) were excluded from all further FC analyses. This criterion excluded 21 subjects leaving a total of n = 100 stroke patients and n = 27 controls with FC data that met all of our quality controls.

Parcellation (Regions of Interest) and Community Assignments. We used a cortical surface parcellation generated by Gordon et al. (25) (Fig. S1). The parcellation is based on R-fMRI boundary mapping and achieves full cortical coverage and optimal region homogeneity. The parcellation includes 324 regions of interest (159 left hemisphere, 165 right hemisphere). The original parcellation includes 333 regions, and all regions less than 20 vertices (approximately 50 mm 2 ) were excluded. Notably, the parcellation was generated on young adults age 18 -33 and is applied here to adults age 21 -83. However, we know of no evidence to suggest that boundaries between cortical areas shift in the course of healthy aging.

To validate the community structure, we conducted modularity optimization on controls and patients (Fig. S2). Consistent with larger investigations of aging (62), we found that optimal community structure was largely, but not completely, consistent with predefined assignments. The location of intermingled colors in the spring-embedded areal graphs on the right of Fig. S2 suggest that regions that switch assignment are typically on the edge between communities. Note that community assignments have no bearing on FC-deficit models discussed below.

Univariate Network FC Analysis. Groupwide patient ( n = 100) versus control ( n = 27) FC differences were interrogated based on the resting state network described above. We compared distributions of homotopic, ipsilesion/ contralesional (randomly assigned L/R in control), and inter/intranetwork FC for patients and controls. In each case, patient-control distributions were compared using a two-tailed Student t test. Three types of within-network connectivity were compared at the whole brain level; homotopic, ipsilesional, and contralesional. FDR correction was conducted on these three statistical tests.

For nine individual RSNS, within and between network differences were assessed. Here, 99 stroke-control t tests (45 ipsilesional, 45 contralesional, 9 homotopic) were computed, significance cutoffs were determined via 10,000 permutations of group assignment (stroke versus control). Finally, the relationship between homotopic connectivity and ipsilesional DMN connectivity was assessed for eight RSNs (the nine used previously, minus the DMN), and results were FDR corrected for eight statistical tests.

Multivariate Ridge Regression. Lesion-deficit and FC-deficit relationships were interrogated using leave-one-out ridge regression models (Fig. 2). We chose to use a linear multivariate ridge regression function to minimize bias but retain the ability to plot predictive weights back to brain anatomy (20). Transductive PCA (63) was performed before modeling for both lesion topography as well as vectorized FC matrices (64). This step was carried out independently for every model and components that explained 95% of variance were retained. For lesion location, the PCA was performed on voxel-wise lesion maps from 65,549 3-mm 3 brain voxels and for functional connectivity, the PCA was performed on 324-choose-2 = 52,326 edges. The number of components retained for each model were as follows: ( i ) attention (50 lesion components, 74 FC components), ( ii ) visual memory: (43,72), ( iii ) verbal memory (43,72), ( iv ) language (56,90), ( v ) left motor (50,84), ( vi ) right motor (50,84), ( vii ) left visual (28,49), and ( viii ) right visual (28,49).

All ridge regression models were trained and tested using a leave-one-out cross validation (LOOCV) loop (65). In each loop, the regularization coefficient lambda was optimized by identifying a lambda between λ = 1 and 10 5 that minimized leave-one-out prediction error over the training set. Next, optimal weights were solved across the entire training set using gradient descent to minimize error for the ridge regression equation shown in Fig. 2. Optimal model weights were applied to the lesion/FC of the left-out subject to predict that subject ' s behavioral score. A prediction was generated for all subjects in this way. Model accuracy was assessed using the square of the Pearson correlation coefficient between measured and predicted behavior scores. To visualize feature weights, the weight matrix was averaged across all n leaveone-out loops to generate a single set of consensus weights. Thus, solving for all behavioral scores in each domain produced two outputs: ( i ) accuracy -% variance explained ( r 2 ), and ( ii ) a consensus weight map -a vector ( ω ) containing relative predictive weights for every voxel/connection. The weights ( ω ) from the model were back projected to the brain to display the most predictive functional connections and displayed using Caret (61).

Two models were combined for the left and right motor domains and left andright visual hemifields to determine the percent of variance explained for motor and visual models (left and right models are shown in Fig. S8). The combined models were later used to determine total within and between RSN contributions to FC-deficit models. Difference in prediction accuracy between lesion-deficit versus FC-deficit models were assessed by a two-tailed Wilcoxon signed rank test on the squared prediction error ðð ~ ω Þ T ~ xi -~ y i Þ 2 , where indexes participant.

FC-deficit network contribution was also quantified based on a priori assigned RSN membership (66). Thus, weights of all connections within and between each RSN were averaged to generate a 7 × 7 RSN weight matrix for each FC-deficit model.

The top 1% of weights were also classified according to four weight types: interhemispheric positive, interhemispheric negative, intrahemispheric positive, and intrahemispheric negative. The number of weights in the top 1% belonging to each of the four types was counted in each model. An ANOVA was run across all seven models to test for a difference in contribution between the four weight types.

An additional post hoc model was run to predict global homotopic connectivity (averaged across all parcels) based on lesion location. This lesionhomotopic FC model was set up in the same manner as the lesion-deficit prediction models.

Multitask Learning. To separate features of functional connectivity change that predict shared deficit across multiple domains versus those that are domain-specific, we applied multitask learning (67). Multitask learning (MTL) is a way to combine the FC-deficit prediction models by learning them jointly. In the setting of brain network decoding, it is reasonable to assume that some shared features determine domain-general functionality. The MTL equation simultaneously optimizes prediction for every domain by

- Carrera E, Tononi G (2014) Diaschisis: Past, present, future. Brain 137(Pt 9):2408 -2422.
- von Monakow C (1914) Die Lokalisation im Grosshirn: und der Abbau der Funktion durch kortikale Herde [ Localization in the Cerebrum and the Degeneration of Functions Through Conical Sources ] (Bergmann, Wiesbaden, Germany). German.
- Alstott J, Breakspear M, Hagmann P, Cammoun L, Sporns O (2009) Modeling the impact of lesions in the human brain. PLOS Comput Biol 5(6):e1000408.
- Corbetta M (2012) Functional connectivity and neurological recovery. Dev Psychobiol 54(3):239 -253.
- Fornito A, Zalesky A, Breakspear M (2015) The connectomics of brain disorders. Nat Rev Neurosci 16(3):159 -172.
- Buckner RL, Corbetta M, Schatz J, Raichle ME, Petersen SE (1996) Preserved speech abilities and compensation following prefrontal damage. Proc Natl Acad Sci USA 93(3):1249 -1253.
- Chollet F, et al. (1991) The functional anatomy of motor recovery after stroke in humans: A study with positron emission tomography. Ann Neurol 29(1):63 -71.
- Corbetta M, Kincade MJ, Lewis C, Snyder AZ, Sapir A (2005) Neural basis and recovery of spatial attention deficits in spatial neglect. Nat Neurosci 8(11):1603 -1610.
- Feeney DM, Baron JC (1986) Diaschisis. Stroke 17(5):817 -830.
- Hillis AE, et al. (2002) Subcortical aphasia and neglect in acute stroke: The role of cortical hypoperfusion. Brain 125(Pt 5):1094 -1104.
- Perani D, Vallar G, Cappa S, Messa C, Fazio F (1987) Aphasia and neglect after subcortical stroke. A clinical/cerebral perfusion correlation study. Brain 110(Pt 5):1211 -1229.
- Carter AR, et al. (2010) Resting interhemispheric functional magnetic resonance imaging connectivity predicts performance after stroke. Ann Neurol 67(3):365 -375.
- He BJ, et al. (2007) Breakdown of functional connectivity in frontoparietal networks underlies behavioral deficits in spatial neglect. Neuron 53(6):905 -918.
- Nomura EM, et al. (2010) Double dissociation of two cognitive control networks in patients with focal brain lesions. Proc Natl Acad Sci USA 107(26):12017 -12022.
- Wang L, et al. (2010) Dynamic functional reorganization of the motor execution network after stroke. Brain 133(Pt 4):1224 -1238.
- Boes AD, et al. (2015) Network localization of neurological symptoms from focal brain lesions. Brain 138(Pt 10):3061 -3075.
- Damasio H, Grabowski TJ, Tranel D, Hichwa RD, Damasio AR (1996) A neural basis for lexical retrieval. Nature 380(6574):499 -505.
- Karnath H-O, Ferber S, Himmelbach M (2001) Spatial awareness is a function of the temporal not the posterior parietal lobe. Nature 411(6840):950 -953.
- Corbetta M, et al. (2015) Common behavioral clusters and subcortical anatomy in stroke. Neuron 85(5):927 -941.
- Phan TG, et al. (2010) Development of a new tool to correlate stroke outcome with infarct topography: A proof-of-concept study. Neuroimage 49(1):127 -133.
- Smith DV, Clithero JA, Rorden C, Karnath H-O (2013) Decoding the anatomical network of spatial attention. Proc Natl Acad Sci USA 110(4):1518 -1523.
- Lv Y, et al. (2013) Identifying the perfusion deficit in acute stroke with resting-state functional magnetic resonance imaging. Ann Neurol 73(1):136 -140.
- Siegel JS, Snyder AZ, Ramsey L, Shulman GL, Corbetta M (2015) The effects of hemodynamic lag on functional connectivity and behavior after stroke. J Cereb Blood Flow Metab , 10.1177/0271678X15614846.
- Power JD, et al. (2014) Methods to detect, characterize, and remove motion artifact in resting state fMRI. NeuroImage 84:320 -341.

combining a domain-specific set of weights with a second set of weight that are held constant across all domains. L1 regularization is used to apply an equal cost function to each, such that the model is not biased toward using either shared or domain-specific weights.

The multitask optimization equation is:

argmin ω λ jj ω 0  ! jj 2 + X K k = 0 X n i = 1    ω 0 + ω k  !  T ~ xi -~ y i  2 + λ jj ω k  ! jj 2 . [1]

In Eq. 1 , the x vector indicates FC (in PCA space). The y vector contains behavioral scores for these same patients. λ , a regularization coefficient, is determined empirically using a leave-one-out approach over a range of λ values. The vector ω is the weight vector that describes the relative importance of each feature in x to the prediction of y . Here, n is the number of subjects, and K is the number of behavioral domains being combined in the MTL problem. The prediction for subject i in domain k is generated by combining a set of domain specific weights ω k with domain general weights ω 0 in the expression: yi = ð ω 0 + ω k ! Þ T ~ xi .

 Nodal contribution to the across-domain weights ð ω 0 Þ for the 324 ROIs was determined by taking the root-mean-square weight of all connections for each node. All statistical tests performed are reported in Table S3.

ACKNOWLEDGMENTS. We thank Nico Dosenbach and Brad Schlaggar for assistance with visualization software; Carl Hacker, Timothy Laumann, and Evan Gordon for data processing assistance; and Alexandre Carter for conceptual development. This study was supported by National Institute of Child Health and Human Development Health Award 5R01HD061117 (to M.C.), National Institute of Neurologic Disorders and Stroke (P30 NS048056 to A.Z.S.), National Institute of Health Medical Scientist Training Award 5T32GM007200-39 and American Heart Association Predoctoral Fellowship Award 14PRE19610010 (to J.S.S.).

- Gordon EM, et al. (2016) Generation and evaluation of a cortical area parcellation from resting-state correlations. Cereb Cortex 26(1):288 -303.
- Behzadi Y, Restom K, Liau J, Liu TT (2007) A component based noise correction method (CompCor) for BOLD and perfusion based fMRI. Neuroimage 37(1):90 -101.
- Muschelli J, et al. (2014) Reduction of motion-related artifacts in resting state fMRI using aCompCor. Neuroimage 96:22 -35.
- Baldassarre A, et al. (2014) Large-scale changes in network interactions as a physiological signature of spatial neglect. Brain 137(Pt 12):3267 -3283.
- van Meer MP, van der Marel K, Otte WM, Berkelbach van der Sprenkel JW, Dijkhuizen RM (2010) Correspondence between altered functional and structural connectivity in the contralesional sensorimotor cortex after unilateral stroke in rats: A combined resting-state functional MRI and manganese-enhanced MRI study. J Cereb Blood Flow Metab 30(10): 1707 -1711.
- Rehme AK, et al. (2015) Identifying neuroimaging markers of motor disability in acute stroke by machine learning techniques. Cereb Cortex 25(9):3046 -3056.
- Dubovik S, et al. (2012) The behavioral significance of coherent resting-state oscillations after stroke. Neuroimage 61(1):249 -257.
- Wu J, et al. (2015) Connectivity measures are robust biomarkers of cortical function and plasticity after stroke. Brain 138(Pt 8):2359 -2369.
- Baldassarre A, et al. (2016) Dissociated functional connectivity profiles for motor and attention deficits in acute right-hemisphere stroke. Brain , 10.1093/brain/aww107.
- O ' Reilly JX, et al. (2013) Causal effect of disconnection lesions on interhemispheric functional connectivity in rhesus monkeys. Proc Natl Acad Sci USA 110(34):13982 -13987.
- Gratton C, Nomura EM, Pérez F, D ' Esposito M (2012) Focal brain lesions to critical locations cause widespread disruption of the modular organization of the brain. J Cogn Neurosci 24(6):1275 -1285.
- Deco G, Tononi G, Boly M, Kringelbach ML (2015) Rethinking segregation and integration: Contributions of whole-brain modelling. Nat Rev Neurosci 16(7):430 -439.
- Wernicke C (1885) Some new studies on aphasia. Fortschr Med 824 -830.
- Broca P (1861) Remarks on the seat of the faculty of articulated language, following an observation of aphemia (loss of speech). Bull Soc Anat 6:330 -357.
- Brodmann K (1909) Comparative Localization Studies in the Brain Cortex, its Fundamentals Represented on the Basis of its Cellular Architecture (JA Barth, Leipzig, Germany).
- Power JD, et al. (2011) Functional network organization of the human brain. Neuron 72(4):665 -678.
- Corbetta M, Shulman GL (2002) Control of goal-directed and stimulus-driven attention in the brain. Nat Rev Neurosci 3(3):201 -215.
- Mesulam M-M (1990) Large-scale neurocognitive networks and distributed processing for attention, language, and memory. Ann Neurol 28(5):597 -613.
- Ullman S (1984) Visual routines. Cognition 18(1-3):97 -159.
- Corbetta M, Shulman GL (2011) Spatial neglect and attention networks. Annu Rev Neurosci 34(1):569 -599.
- Goldman-Rakic PS (1988) Topography of cognition: Parallel distributed networks in primate association cortex. Annu Rev Neurosci 11(1):137 -156.
- Posner MI, Petersen SE, Fox PT, Raichle ME (1988) Localization of cognitive operations in the human brain. Science 240(4859):1627 -1631.
- Owen AM, McMillan KM, Laird AR, Bullmore E (2005) N-back working memory paradigm: A meta-analysis of normative functional neuroimaging studies. Hum Brain Mapp 25(1):46 -59.

|

|

- Smith EE, Jonides J (1998) Neuroimaging analyses of human working memory. Proc Natl Acad Sci USA 95(20):12061 -12068.
- Connor LT, Albert ML, Helm-Estabrooks N, Obler LK (2000) Attentional modulation of language performance. Brain Lang 71(1):52 -55.
- Gracco VL, Abbs JH (1988) Central patterning of speech movements. Exp Brain Res 71(3):515 -526.
- Tallal P, et al. (1996) Language comprehension in language-learning impaired children improved with acoustically modified speech. Science 271(5245):81 -84.
- Fedorenko E, Thompson-Schill SL (2014) Reworking the language network. Trends Cogn Sci 18(3):120 -126.
- Craddock RC, James GA, Holtzheimer PE, 3rd, Hu XP, Mayberg HS (2012) A whole brain fMRI atlas generated via spatially constrained spectral clustering. Hum Brain Mapp 33(8):1914 -1928.
- Shen K, et al. (2015) Stable long-range interhemispheric coordination is supported by direct anatomical projections. Proc Natl Acad Sci USA 112(20):6473 -6478.
- Longstreth WT, Jr, et al. (1996) Clinical correlates of white matter findings on cranial magnetic resonance imaging of 3301 elderly people. The Cardiovascular Health Study. Stroke 27(8):1274 -1282.
- Andersson JL, Jenkinson M, Smith S (2007) Non-linear optimisation. FMRIB technical report TR07JA1. Univ Oxf FMRIB Cent Oxf UK . Available at fsl.fmrib.ox.ac.uk/analysis/ techrep/tr07ja1/tr07ja1.pdf. Accessed October 2, 2015.
- Robb RA, Hanson DP (1991) A software system for interactive and quantitative visualization of multidimensional biomedical images. Australas Phys Eng Sci Med 14(1):9 -30.

|

- Rowland DJ, Garbow JR, Laforest R, Snyder AZ (2005) Registration of [18F]FDG microPET and small-animal MRI. Nucl Med Biol 32(6):567 -572.
- Glasser MF, et al.; WU-Minn HCP Consortium (2013) The minimal preprocessing pipelines for the Human Connectome Project. Neuroimage 80:105 -124.
- Fischl B, Sereno MI, Tootell RBH, Dale AM (1999) High-resolution intersubject averaging and a coordinate system for the cortical surface. HumBrain Mapp 8(4):272 -284.
- Van Essen DC, et al. (2001) An integrated software suite for surface-based analyses of cerebral cortex. J Am Med Inform Assoc 8(5):443 -459.
- Chan MY, Park DC, Savalia NK, Petersen SE, Wig GS (2014) Decreased segregation of brain systems across the healthy adult lifespan. Proc Natl Acad Sci USA 111(46):E4997 -E5006.
- Zhu Y, Wu Y, Liu X, Mio W (2008) Transductive optimal component analysis. 19th International Conference on Pattern Recognition, 2008 (IEEE, Tampa, FL), pp 1 -4.
- Smith SM, Hyvärinen A, Varoquaux G, Miller KL, Beckmann CF (2014) Group-PCA for very large fMRI datasets. Neuroimage 101:738 -749.
- Golland P, Fischl B (2003) Permutation tests for classification: Towards statistical significance in image-based studies. Information Processing in Medical Imaging , eds Taylor C, Noble JA, Lecture Notes in Computer Science (Springer, Berlin ), pp 330 -341.
- Hacker CD, et al. (2013) Resting state network estimation in individual subjects. NeuroImage 82:616 -633.
- Daumé H, III (2009) Frustratingly easy domain adaptation. ArXiv Prepr ArXiv09071815.
- Bastian M, Heymann S, Jacomy M (2009) Gephi: an open source software for exploring and manipulating networks. Proceedings of the International Conference on Web and Social Media 8:361 -362.