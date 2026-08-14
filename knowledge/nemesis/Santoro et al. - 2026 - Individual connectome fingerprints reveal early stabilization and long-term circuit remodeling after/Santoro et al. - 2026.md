available under a CC-BY 4.0 International license. (which was not certified by peer review) is the author/funder, who has granted bioRxiv a license to display the preprint in perpetuity. It is made bioRxiv preprint doi: https://doi.org/10.64898/2026.03.27.714711; this version posted March 31, 2026. The copyright holder for this preprint

### Individual connectome fingerprints reveal early stabilization and long-term circuit remodeling after stroke

Andrea Santoro, 1, 2, ∗ Alessandro Lucatelli, 2 Fabienne Windel, 3, 4 Beatrice Lugli, 3, 4 Maria Giulia Preti, 2, 5 Lisa Fleury, 3, 4 Flavia Petruso, 2, 5 Elena Beanato, 3, 4 Dimitri Van De Ville ‡ , 2, 5 Friedhelm Christoph Hummel ‡ , 3, 4, 6 and Enrico Amico ‡ 7, 8, 2, †

1 ISI Foundation, Turin, Italy

2 Neuro-X Institute, ´ Ecole Polytechnique F´ ed´ erale de Lausanne (EPFL), Geneva, Switzerland 3

Defitech Chair of Clinical Neuroengineering, Neuro-X Institute,

´ Ecole Polytechnique F´ ed´ erale de Lausanne (EPFL), Geneva, 1202, Switzerland

4 Defitech Chair of Clinical Neuroengineering, Neuro-X Institute,

EPFL Valais, Clinique Romande de R´ eadaptation, Sion 1950, Switzerland

5 Department of Radiology and Medical Informatics, University of Geneva, Switzerland

Department of Clinical Neuroscience, University of Geneva Medical School, Geneva 1206, Switzerland

7 School of Mathematics, University of Birmingham, Birmingham, UK

8

Centre for Human Brain Health, University of Birmingham, Birmingham, UK (Dated: March 27, 2026)

Stroke is one of the leading causes of global disability, yet the principles governing how focal brain injury disrupts large-scale neural connectivity over time remain poorly understood. Here, we leverage a longitudinal multimodal dataset to track the evolution of individual-specific connectivity patterns, or 'brain fingerprints', over the first year after stroke. Despite a persistent shift from healthy architecture, we demonstrate that each patient's unique functional connectome fingerprint is remarkably resilient and stabilizes within three weeks. This early global stabilization masks a protracted system-specific reorganization of brain circuits, which is characterized by an initial increase in connectivity within sensory and attention systems, followed by a decline across higher-level association networks. A joint structure-function embedding further shows that recovery involves a gradual shift toward the normative healthy range, driven primarily by functional reconfiguration atop a stable structural lesion. Crucially, a multivariate prediction model reveals that early functional signatures selectively forecast long-term impairment in language, executive function, and attention. Together, our results define the post-stroke brain as a shifting but constrained dynamical system, identifying early-stabilized brain patterns as biomarkers for individual recovery profiles and targets for personalized neurorehabilitation.

Keywords: stroke, functional connectivity, fingerprinting, brain reconfiguration

Advancements in network neuroscience have revolutionized our understanding of the brain [1, 2], shifting from the concept of isolated regions to recognizing it as a highly interconnected system [3, 4]. The availability of large-scale neuroimaging datasets [5, 6] has enabled detailed mapping of functional and structural connections, providing invaluable benchmarks for exploring neural connectivity [7, 8]. This network-based perspective has yielded profound insights into how different brain regions interact to support brain function and how their disruption contributes to neurological disorders [9-12].

A notable development in this field is the concept of brain fingerprinting, which posits that an individual's unique pattern of brain connectivity can serve as a distinctive identifier, much like a fingerprint [13-16]. Early studies demonstrated that functional connectomes derived from resting-state functional magnetic resonance imaging (fMRI) are stable over time and can reliably distinguish individuals within a population [17]. Be-

> ∗ andrea.santoro@isi.it

> † e.amico@bham.ac.uk

> ‡ These authors share co-senior authorship

yond fMRI, brain fingerprinting has been observed across modalities - including EEG, MEG and fNIRS - supporting the notion that stable, person-specific features are a general property of brain organization rather than an artifact of a single measurement technique [18-23]. These individualized profiles have also been linked to individual differences in cognitive abilities and behavioral traits [24-27], underscoring the potential of brain fingerprinting as a biomarker for personalized neuroscience. Yet, despite increasing applications in neuropsychiatric and neurodegenerative contexts [28-31], the extent to which fingerprints persist, reorganize, or break down after acute focal brain injury remains largely unknown.

Stroke offers a compelling clinical case. It is a leading cause of disability worldwide [32-34], and is increasingly understood as a network disorder: a focal lesion can trigger widespread changes in both structural and functional connectivity through direct disconnection and remote physiological effects [35-43]. Mechanisms such as diaschisis [44], through which localized brain injury causes dysfunction in remote regions due to disrupted neural pathways, illustrate how stroke-induced damage extends beyond the lesion, affecting widespread neural pathways. This extensive network disruption impairs

6

communication between brain regions [45-47], altering local and global network properties [48-50] and impacting both cognitive and motor functions [51-56].

The potential for functional recovery following stroke varies considerably among patients [57, 58], with fewer than 15% achieving complete motor restoration [59] and pooled analyses reporting post-stroke cognitive impairment in approximately 38% of individuals [60]. This variability has been linked to lesion size, lesion location, damage to critical white matter tracts, and individual neuroplastic responses [42, 61-63]. Neural reorganization after stroke is a dynamic, time-sensitive process involving both the ipsilesional and contralesional hemispheres. While an early increase of contralesional connectivity may initially serve a compensatory role, prolonged hyperactivity in the contralesional hemisphere has been associated with poorer long-term outcomes, possibly due to maladaptive plasticity interfering with recovery in the affected hemisphere [64]. Conversely, strengthening ipsilesional connectivity and promoting reorganization within the damaged hemisphere are often correlated with better functional recovery [65]. These opposing neural changes underscore the importance of precisely characterizing connectivity patterns that facilitate (or hinder) long-term rehabilitation. Despite these insights, most studies to date rely on group-level analyses or cross-sectional designs, which fail to capture individual-level trajectories and the evolving nature of recovery [49, 66, 67]. Additionally, it remains unclear how functional connectivity patterns evolve from the acute phase to chronic stages, and how these changes relate to clinical outcomes [52, 68-70]. These gaps highlight the need for longitudinal investigations that can more accurately map the interplay between network reorganization and functional gains.

Here, we address these open questions using a longitudinal multimodal dataset [71], tracking stroke patients across four distinct stages during the first year after the ictal event. We combine complementary analyses to conceptualize this recovery as an individualized, time-resolved network process. We first quantify the resilience of patient-specific functional 'fingerprints' using identifiability tools [17], contextualizing these stable signatures against a largely stationary structural disconnection backbone and evolving functional hyperand hypo-connectivity. We then embed patients in a joint structure-function state space, framing recovery as a shift toward healthy variability under strict anatomical constraints. Finally, using multivariate brain-behavior association and ridge-based predictive modeling, we test whether early functional signatures forecast long-term clinical recovery across multiple domains. Together, this framework moves beyond group averages to connect stable individual identity with selective circuit remodeling, providing a robust route toward individualized biomarkers for prognosis and targeted neurorehabilitation.

### RESULTS

To investigate the principles governing individual brain network reorganization after a focal injury, we leveraged the TiMeS cohort - a longitudinal, observational study of stroke recovery characterized by high-density multimodal imaging, including resting-state fMRI and diffusion-weighted imaging, as well as a detailed clinical assessment [71]. We analyzed N = 64 patients across four critical stages of recovery: acute ( T 1 , ∼ 1 week), early sub-acute ( T 2 , ∼ 3 weeks), late sub-acute ( T 3 , ∼ 3 months), and chronic ( T 4 , ∼ 12 months). Lesion anatomy was heterogeneous but frequently involved subcortical structures (Fig. 1 a ), providing a stringent test of how disruption of cortico-subcortical pathways reshapes large-scale functional organization over time. To maximize statistical power, all available data were included for each analysis unless otherwise specified (see Methods).

Recognizing that group-level averages often conceal the idiosyncratic nature of recovery, we developed a multi-stage analytical framework to track the functional reconfiguration of each patient's connectome over time (Fig. 1 b-f ). For each session, whole-brain functional connectivity (FC) was estimated from resting-state BOLD time series using a parcellation of 377 regions, comprising 360 cortical areas from the Glasser atlas [72] and 17 subcortical regions (see Methods). Connectivity patterns were benchmarked against a normative reference derived from two healthy control cohorts acquired with matched scanning protocols and preprocessing (ECONS and TrainStim, for a total of n = 41 subjects; see Methods).

To quantify the preservation of individual-specific topography despite injury, we employed a brain fingerprinting approach [17]. For each session pairing ( T i , T j ), we constructed an identifiability matrix and derived withinsubject similarity ( I self ) and between-subject similarity ( I others ) to assess whether patients remained more similar to their own past or future selves than to other individuals (Fig. 1 c ). Furthermore, we localized stability and remodeling by estimating link-wise reliability with intraclass correlation (ICC) [73, 74], distinguishing statistically persistent connections from those that were selectively dynamic across recovery and summarizing these effects across canonical functional systems (Fig.1 d ).

We then characterized structural damage and functional dysfunction at complementary scales, from individual links to canonical network blocks, and summarized each patient's longitudinal evolution in a joint structurefunction space (Fig. 1 e ). In this embedding, patients were positioned according to their structural and functional similarity to the healthy reference, providing a compact description of how whole-brain states shift relative to the range of healthy variability and motivating a dynamical-systems view of recovery as transitions within a constrained landscape. Finally, to establish the clinical relevance of these network shifts, we coupled connectome reconfiguration to multidomain behavioral profiles using

(a)

Number of lesioned patients

Stroke patients

T1 T2 T3 T4

64 52 44 28

(a) FC fingerprinting localization

Functionally altered links

FP L VADA SM VIS

SC DMN

VIS SM DA VA L FP DMN SC

Statistically persistent

Retest

![Figure on PDF page 3](figures/img_p003_0.png)

**Figure labels:**

- 12
- Healthy controls
- ECONS TrainStim
- 31|
- 10
- Functionally
- healthy links
- VIS
- 9.8
- SM
- 15
- DA
- - 7.1
- 16
- 5.6
- VA
- 25
- L-
- 26 | 25
- 18
- 11
- 33
- FP -
- 9.7
- 8.6
- DMN
- 17
- 20
- 14
- 9.4
- 5.8
- 4.5
- Functional recovery
- (e)
- 1 week (T1) )
- 3 weeks (12)
- - 3 months (T3)
- 1 year (T4)
- Connectome alterations across time
- Similarity with
- average healthy
- Structural alterations
- Function
- Structure
- Functional alterations
- (f)
- Patient Retest (T.)
- other
- test(s)
- others.
- Patient Test (T;)
- 0.2
- Identification (r)|
- 0.8
- Brain-behavior prediction
- Latent
- mask
- Neglect
- Brain features
- PLSC
- Language -
- Sensory-
- Ridge
- Executive -
- regression
- Attention -
- Ra score
- Clinical scores
- (Y)

ICC connections

***FIG. 1. Mapping connectome disruption and individual stability after stroke. (a) TiMeS cohort [71], showing the lesion overlap map for the stroke cohort and sample sizes across four post-stroke assessments (T1: ∼ 1 week; T2: ∼ 3 weeks; T3: ∼ 3 months; T4: ∼ 1 year), together with healthy control groups used for benchmark (ECONS and TrainStim). (b) Restingstate fMRI BOLD time series were used to derive whole-brain functional connectivity (FC) matrices at each time point for each participant. (c) Longitudinal brain identification based on a test-retest similarity matrix obtained by correlating each patient's connectivity pattern at test ( T i ) and retest ( T j ) sessions; high diagonal values ( I self ) indicate reliable within-subject connectivity 'fingerprints' relative to between-subject similarity ( I others ). (d) Spatial specificity analysis of the functional connectome fingerprint, in which statistically persistent connections (intraclass correlation, ICC) are classified as functionally altered or functionally preserved and summarized across canonical large-scale networks to map patterns of recovery. (e) Structural disconnection and functional deviations relative to healthy controls are quantified longitudinally and summarized in a joint structure-function similarity space, capturing patients' recovery trajectories. (f) Brain-behavior associations were assessed using multivariate Partial Least Squares Correlation (PLSC) to identify connectivity patterns covarying with clinical scores; the resulting latent connectivity mask was then used to constrain ridge regression models for out-of-sample prediction of longitudinal outcomes across behavioral domains.***

a two-stage framework (Fig. 1 f ). Partial Least Squares Correlation (PLSC) [75] identified latent brain-behavior components at a given time point, and the resulting connectivity signature was carried forward to constrain ridge regression models for out-of-sample prediction of followup clinical scores while avoiding data-leakage from feature selection [76, 77] (see Methods for details).

### The individual connectome fingerprint is resilient and consolidates early after stroke

We first investigated whether focal injury induces a return toward canonical healthy organization or a persistence in a pathological state. Using I clinical , we quantified the similarity of each patient's FC to the healthy reference cohort (ECONS) and benchmarked these values against the baseline similarity observed between two independent healthy groups (TrainStim vs. ECONS; Fig. 2 a ). Across the first year post-stroke, patients exhibited a sustained and significant shift away from the healthy normative range. This divergence was robust in the acute ( T 1 ), early sub-acute ( T 2 ), and chronic stages ( T 4 ; p < 0 . 01, FDR-corrected Mann-Whitney U test), while the T 3 interval exhibited a marginal trend ( p = 0 . 053).

Despite this sustained global shift, FC patterns of stroke patients remained strongly identifiable. I self was consistently higher than between-subject similarity, demonstrating that each patient preserved an idiosyncratic connectome signature that generalizes across months of recovery (Fig. 2 b ). This individual fingerprint was highly robust even in the acute phase, with identification rates exceeding 75% between T 1 and chronic stages (i.e., T 3 , T 4 ; see Supplementary Fig. S1). This indicates that focal injury perturbs the connectome without erasing its patient-specific organization.

The longitudinal trajectory of identification suggested rapid consolidation rather than prolonged instability. Al- tests)

![FIG. 2. Longitudinal evolution of functional connectome identification following stroke . (a) Distribution of connectome similarity scores I clinical for healthy controls (TrainStim vs. ECONS) and stroke patients (relative to ECONS) across four time points. Stroke scores are significantly lower than healthy controls at T 1 , T 2 , and T 4 ( ∗ ∗ p < 0 . 01, FDR-corrected Mann-Whitney U test), with a marginal trend at T 3 ( p = 0 . 053). (b) Distribution of self-identifiability scores ( I self ), quantifying patient connectome similarity between earlier time points and the chronic outcome (T4). Significantly lower I self at T 1 compared to T 2 indicates rapid functional reorganization of the individual fingerprint within the first three weeks post-stroke ( ∗ ∗ ∗ p < 0 . 001, LMM). I self at T 2 shows no significant difference from T 3 ( p FDR = 0 . 054). (c) Median I self within and between seven canonical networks and subcortical structures (VIS, visual; SM, somatomotor; DA, dorsal attention; VA, ventral attention; L, limbic; FP, frontoparietal; DMN, default mode) and subcortical structures (SC). Comparing (T1,T4) and (T2,T4) reveals how specific networks consolidate their functional distinctiveness over time. (d) Significant relative percentage increase in I self from acute to sub-acute stages ( T 1 → T 2 ), referenced to the chronic baseline ( T 4 ). Warmer colors denote networks undergoing rapid functional reconfiguration, notably the ventral attention (VA), limbic (L), and somatomotor (SM) systems ( p < 0 . 05, LMM).](figures/page_004.svg)

**Figure labels:**

- (a)
- (d)
- (c)
- (b)
- Functional networks

though the acute phase ( T 1 ) showed the lowest selfsimilarity relative to the chronic stage, the fingerprint sharpened significantly by the three-week mark ( T 2 ), where identification rates rose to 80%. To account for unbalanced longitudinal sampling and repeated measures, we tested these effects using a linear mixed model (LMM). The LMM confirmed an early stabilization of the fingerprint, confirming that individual signatures stabilize rapidly; I self at T 2 showed no significant difference from T 3 when compared to the one-year endpoint of the study (Fig. 2b; LMM, p FDR < 0 . 001 for the ( T 2 , T 4 ) vs. ( T 3 , T 4 ) comparison). These results support a rapid transition toward a stable, individual-specific 'recovery brain fingerprint' within the first month, even though the functional connectome remains globally shifted away from healthy benchmark.

This consolidation was not spatially uniform across the connectome. When examining the I self distributions on pairs of canonical resting-state networks [78], association networks showed the strongest longitudinal stability (Fig. 2 c ). In particular, the default mode and frontoparietal networks maintained high withinnetwork self-similarity across recovery, consistent with a role as stable anchors of individual functional identity despite prevalent subcortical injury. Converging evidence comes from our edge-wise reliability analysis; using an intraclass-correlation (ICC) approach to identify fingerprint-defining connections, edges within and involving frontoparietal and default mode systems were among the most reliably expressed across sessions (Supplementary Fig. S2), reinforcing their role as 'identitystabilizing' components. By contrast, network blocks involving subcortical and somatomotor-related systems showed lower reliability, consistent with greater susceptibility of cortico-subcortical loops to lesion-driven disruption and compensatory reconfiguration.

Critically, early improvements in identifiability ( I self ) were localized to specific subsets of functional networks rather than occurring globally (Fig. 2 d ). This suggests that fingerprint consolidation relies on the targeted

(a)

4

8

VIS SM DA VA L FP DMN SC

VIS SM DA VA L FP DMN SC

1 week (T1)

(b)

OMN

(c)

T0.40.

Fraction

0.20

0.00

VIS

WH+

IH+

Within-Hemisphere (Hyperconnectivity)

12

16

20 0

VIS SM DA VA L FP DMN SC

4

VIS SM DA VA L EP DMN SC

6

8

10

VIS SM DA VA L FP DMN SC

![FIG. 3. Longitudinal functional reconfiguration decouples from structural damage following stroke. (a) Grouplevel matrices displaying the percentage of DWI-derived structurally lesioned edges (upper triangle) and functionally altered edges (lower triangle; FDR-corrected Mann-Whitney U test, q < 0 . 05) relative to healthy controls across four time points ( T 1 -T 4 ). Structural disconnection patterns remain relatively static, whereas functional alterations evolve dynamically, revealing a spatial dissociation between the fixed structural injury and time-varying functional reorganization throughout the first year. (b) Circular plots depict positive (hyperconnectivity, red) and negative (hypoconnectivity, blue) functional alterations at T1-T4, as quantified by Cohen's d effect size. (c) Box plots summarize the fraction of altered edges that are within-hemisphere (WH) or inter-hemisphere (IH), further subdivided into hyperconnectivity ( WH +; IH +) and hypoconnectivity ( WH -; IH -). Early stages ( T 1 -T 2 ) are dominated by within-hemisphere hyperconnectivity, whereas the late sub-acute/chronic phase ( T 3 -T 4 ) shows a relative increase in inter-hemispheric alterations, consistent with a shift from local to cross-hemispheric plasticity. Data are shown for the longitudinal subset ( n = 22). Network abbreviations: VIS, visual; SM, somatomotor; DA, dorsal attention; VA, ventral attention; L, limbic; FP, frontoparietal; DMN, default mode; SC, subcortical.](figures/img_p005_0.png)

**Figure labels:**

- SM
- VIS SM DA VA L FP DMN SC
- 3 weeks (T2)
- VIS
- 3 months (T3)
- 1 year (T4)
- OMN
- 1
- Cohen's D
- NWa
- WH-
- IH-
- WH+
- IH+
- Inter-Hemisphere (Hyperconnectivity)
- • Within-Hemisphere (Hypoconnectivity)
- \ Inter-Hemisphere (Hypoconnectivity)

re-stabilization of specific circuits rather than uniform brain-wide normalization. This rapid shift toward a stable regime by T 2 was highly consistent across different time-point comparisons, confirming that networks are unstable at T 1 but remain stable from T 2 onward (Supplementary Fig. S3). These localized effects were fully preserved in a sensitivity analysis restricted to patients with complete four-timepoint data (Supplementary Fig. S4).'

### Decoupling of functional reconfiguration from structural lesion

The rapid consolidation of whole-brain fingerprints by the early sub-acute stage ( T 2 ) raises a key question: can stable individual-level identity coexist with ongoing remodeling of specific connections? We first quantified the structural impact of stroke by estimating each patient's disconnectome from diffusion-weighted imaging, capturing the set of white-matter pathways disrupted by the lesion. To minimize longitudinal confounds, we focused on the subset of patients with complete multi-

![FIG. 4. Longitudinal distribution of positive and negative functional network alterations. Matrices report the network-level fraction of functional edges significantly altered in stroke patients relative to healthy controls (ECONS) across four stages (T1: 1 week; T2: 3 weeks; T3: 3 months; T4: 1 year). Significance was determined via edge-wise Mann-Whitney U tests (70 876 comparisons, FDR-corrected at q < 0 . 05), and aggregated by network block. (a) Fraction of positive alterations (hyper-connectivity), highlighting a left-hemispheric intra-hemispheric peak at T2, primarily involving VA, L, and FP systems. (b) Fraction of negative alterations (hypo-connectivity), which peaks at T3 and persists into the chronic phase, with prominent involvement of VIS and SM networks. Black lines delineate left-hemisphere, right-hemisphere, and inter-hemispheric blocks. Abbreviations: VIS, visual; SM, somatomotor; DA, dorsal attention; VA, ventral attention; L, limbic; FP, frontoparietal; DMN, default mode; SC, subcortical.](figures/page_006.svg)

**Figure labels:**

- Left Hemisphere
- Right Hemisphere
- (a)
- (b)

modal data across time. We then summarized the proportion of structurally lesioned edges within and between canonical Yeo networks (Fig. 3 a , top; orange scale). Remarkably, the overarching topography of structural disconnection remained largely stable over the first year. While this macro-scale pattern was preserved, it is important to note that structural connectivity can undergo secondary longitudinal alterations, such as Wallerian degeneration, particularly in initially damaged networks or following larger lesions [42]. Nevertheless, this conclusion held across alternative lesion-tracking approaches (Supplementary Fig. S5 for comparisons), including lesiononly disconnection estimates and BCB toolkit-based reconstructions [79]. Together, these analyses delineate a stable structural 'backbone' that constrains the space of possible functional configurations, yet does not by itself explain or predict the trajectory of functional reorganization. Rather, functional connectivity appears to decouple from the structural lesion backbone over time.

Indeed, in contrast to this structurally stable disconnection pattern, the functional connectome exhibited a sustained and system-specific trajectory of changes (Fig. 3 a , bottom; purple scale). To map these alterations without imposing a priori constraints, we performed a large-scale univariate analysis across all func- tional connections ( K = 70876), comparing the distribution of each edge in patients versus healthy controls (ECONS) at each time point (Mann-Whitney U test; FDR-corrected P < 0 . 05). Aggregating significant effects within and between Yeo networks revealed a clear decoupling across scales. Although I self indicates that global identity stabilizes by three weeks, the set of altered functional links continues to evolve across months, indicating ongoing circuit-level remodeling well into the chronic phase.

Statistical significance identifies which edges differ from healthy norms, but not whether they are strengthened or weakened. We therefore quantified effect sizes (Cohen's d ) [80] for all significantly altered links, interpreting positive values ( d > 0) as hyper-connectivity and negative values ( d < 0) as hypo-connectivity. Network-level patterns were visualized with circular connectograms and hemispheric summaries (Fig. 3 b-c ). This decomposition revealed a marked temporal asymmetry. Hyper-connectivity was most prominent early after stroke, spanning both intraand inter-hemispheric connections and disproportionately involving sensory and attention-related systems, consistent with transient compensatory coupling. In contrast, hypo-connectivity accumulated more gradually and became increasingly preva-

lent from the acute through late sub-acute stages, particularly for links involving higher-order association systems.

These sign-dependent effects were especially evident in the network-resolved profiles. From three months onward ( T 3 ), hyper-connectivity was most pronounced within somatomotor circuitry and in somatomotor-ventral attention (VA) interactions, suggesting strengthened coupling between action-related and salience/attention pathways during late sub-acute recovery. In parallel, widespread hypo-connectivity emerged from FP, DMN, and SC systems, consistent with persistent disruption of corticosubcortical integration and reduced long-range coupling within association architecture. At the hemispheric level, the fraction of hypo-connected edges increased from T 1 to T 3 (Fig. 3 c ), indicating that negative deviations from the healthy baseline can accumulate even as the patientspecific fingerprint consolidates.

Together, these results establish a dissociation between a largely time-invariant structural injury backbone and a time-varying functional phenotype. The post-stroke connectome rapidly converges to a stable, individually specific configuration at the whole-brain level, yet continues to reorganize through selective, network-specific remodeling.

### Temporal asymmetry of hyper- and hypo-connectivity phenotypes

To quantify the sign-dependent effects more directly, we summarized the fraction of significantly altered edges within and between canonical networks, separately for positive and negative deviations from healthy controls, and further stratified them by hemispheric topology (left-left, right-right, and inter-hemispheric blocks; Fig. 4). This representation provides a compact view of how abnormal coupling evolves across recovery while retaining information about network identity and laterality.

Hyper-connectivity followed an early and transient course (Fig. 4 a ). At one week post stroke ( T 1 ), only a small fraction of edges showed increased coupling relative to controls. By three weeks ( T 2 ), hyper-connectivity rose sharply and organized into coherent network blocks, dominated by within-hemisphere effects with additional inter-hemispheric involvement. These increases were most evident among sensory and attention-related systems, consistent with a short-lived phase of compensatory strengthening of functional coupling after the acute insult. By T 3 and T 4 , the overall extent of hyperconnectivity decreased, indicating that the early increase does not persist but gives way to a more selective pattern as recovery progresses.

Hypo-connectivity displayed a delayed and more sustained trajectory (Fig. 4 b ). Negative deviations from healthy controls were modest at T 1 but became more prevalent by T 2 and reached their broadest expression at three months ( T 3 ), spanning a wider set of network interactions and involving both intra- and inter-hemispheric edges. These effects were not confined to a single system. Instead, they extended across higher-order association networks and prominently involved subcortical interactions, consistent with persistent disruption of cortico-subcortical integration and long-range coupling. Although the overall burden of hypo-connectivity partially receded by one year ( T 4 ), substantial negative deviations remained, indicating that chronic-stage functional architecture stays measurably altered even after consolidation of global fingerprinting.

These hemispherically resolved trajectories refine the picture emerging from Fig. 3. Post-stroke reorganization is marked by an early increase in hyper-connectivity that peaks in the early sub-acute stage, followed by a broader rise in hypo-connectivity that culminates months after the event. This temporal asymmetry supports a model in which the connectome stabilizes rapidly at the level of global identity, while specific network interactions continue to be reshaped through sequential, partly opposing phases of functional coupling during recovery.

### Recovery as a longitudinal migration toward a healthy structure-function manifold

The results above point to a dissociation across scales. Whole-brain identifiability stabilizes early, yet specific links and network interactions continue to remodel over months. We therefore asked whether these highdimensional changes can be summarized as a coordinated shift in joint structure-function organization (Fig. 5). This view frames recovery as the evolution of a dynamical system in which large-scale functional activity is constrained by an attractor-like landscape shaped by the structural connectome [81-83]. We embedded each patient at each time point in a two-dimensional state space defined by similarity of their structural and functional connectome to the mean healthy template (ECONS), and benchmarked patient positions against the distribution of healthy variability.

In this space, the acute stroke acted as a strong perturbation that scattered individuals away from the healthy manifold. At T 1 , 42% of patients lay outside the healthy template, driven primarily by reduced FC similarity despite comparatively preserved whole-brain SC similarity. This structure-function dissociation is consistent with connectional diaschisis, in which focal lesions induce widespread remote functional consequences through disconnection and network-level rebalancing [44]. More generally, it is in line with prior work showing that anatomy constrains, but does not uniquely determine, functional coupling, which can be reshaped through indirect pathways and distributed interactions across the connectome [84, 85].

During their first year post-stroke, patients showed a systematic and individualized drift back to the healthy

![FIG. 5. Longitudinal convergence of the post-stroke connectome toward the healthy manifold. (a-d) Each panel shows a bivariate embedding of stroke patients at acute ( T 1 ), early sub-acute ( T 2 ), late sub-acute ( T 3 ), and chronic ( T 4 ) stages. Each point denotes one patient positioned by their similarity (Pearson correlation) to a healthy reference template derived from the ECONS cohort, computed separately for structural connectivity (SC; x-axis) and functional connectivity (FC; y-axis). The shaded density indicates the distribution of healthy controls and patients and their 95% confidence, defining the range of (healthy) normative variability. Percentages report the fraction of patients outside this healthy envelope at each stage. Patients show a pronounced structure-function dissociation early after stroke, with relatively preserved SC similarity but reduced and highly variable FC similarity. Across the first year, patient trajectories shift toward the healthy density peak primarily along the FC axis, whereas SC similarity remains comparatively stable, consistent with recovery dominated by functional reconfiguration on top of a largely invariant structural scaffold. Substantial inter-individual dispersion persists at late stages, reflecting heterogeneous network-level consequences of injury and compensatory adaptations.](figures/page_008.svg)

**Figure labels:**

- 0.90
- 0.92
- 0.94
- 0.96
- 0.98
- 1.00
- Structural similarity with average healthy SC
- 0.2
- 0.3
- 0.4
- 0.5
- 0.6
- 0.7
- 0.8
- Functional similarity with average healthy FC
- N = 60
- 42% outside
- Healthy
- (a)
- T1
- N = 50
- 28% outside
- (b)
- T2
- N = 41
- 24% outside
- (c)
- T3
- N = 33
- 18% outside
- (d)
- T4

manifold, reflected by a progressive reduction in outliers. Importantly, this shift was not driven by global 'structural repair'. Structural similarity remained comparatively stable over time, consistent with the largely stationary structural backbone reported in Fig. 3 a , whereas functional similarity increased monotonically. This pattern matches models in which the structural connectome provides relatively rigid constraints, while functional interactions remain more flexible and can reorganize over months as network dynamics settle into new stable configurations [81, 82].

Convergence toward the healthy manifold was nonetheless incomplete. Substantial dispersion persisted at every stage, consistent with heterogeneity in lesion anatomy, compensatory strategies, and the distributed network consequences of injury [50, 86, 87]. This state-space view provides a compact whole-brain account of recovery. Rather than simply reverting to a generic template, the post-stroke brain appears to navigate a constrained dynamical landscape that increasingly overlaps with the healthy structure-function manifold, while retaining marked individual variability shaped by the injury.

### Behavioral recovery is domain-specific and only partly explained by lesion size

Having established that post-stroke recovery involves both stable global identity and ongoing network remodeling, we next asked how these connectome changes relate to clinical recovery outcomes. We first summarized the longitudinal behavioral profile of the cohort using low-dimensional-composite scores derived for each behav- ioral domain from the full neuropsychological battery via non-negative matrix factorization (NMF), yielding single domain scores comparable across time points (Fig. 6). In this representation, higher values indicate greater impairment. Across the first year, most domains showed a clear reduction in impairment from T 1 to T 4 , consistent with overall behavioral improvement. Importantly, recovery was not uniform across domains. Motor and sensory scores were already low at T 1 and remained low across time, with comparatively little dispersion across individuals. In contrast, higher-order cognitive domains such as attention and executive function showed substantial inter-individual variability, indicating a wide range of recovery phenotypes.

We next examined the extent to which early impairment could be attributed to the sheer scale of the structural damage. Lesion burden, quantified as logtransformed lesion volume (Fig. 6 b ), was correlated with acute composite scores at T 1 (Fig. 6 c ). While most behavioral domains showed significant associations with lesion size, indicating that larger lesions typically produce more severe acute deficits, motor impairment was a notable exception. The weak dependence of motor scores on lesion volume aligns with the established principle that motor outcome is governed less by overall lesion size than by whether the lesion disrupts critical descending motor pathways, such as the corticospinal tract [88, 89].

To further illustrate the granularity of individual trajectories, we highlight the longitudinal profile of one representative case (patient P019; Fig. 6 d ). This patient showed severe acute motor impairment, followed by a delayed improvement that became apparent from T 3 onward, underscoring that recovery can unfold on distinct timescales within the same individual and across do-

NMF scores

9

![FIG. 6. Domain-specific behavioral recovery and its relationship to structural lesion burden. (a) Behavioral composite scores across six domains (Motor, Attention, Executive, Sensory, Language, Neglect) over time. Scores were derived using Non-negative Matrix Factorization (NMF) to ensure cross-session comparability; higher scores indicate greater clinical impairment. Boxplots show median, interquartile range, and 1.5 × IQR whiskers at each timepoint (T1: ∼ 1 week, T2: ∼ 3 weeks, T3: ∼ 3 months, T4: ∼ 1 year) (b) Distribution of structural lesion burden across the cohort, quantified as the log-transformed number of voxels (log(1 + voxels)). (c) Correlation between acute lesion volume and behavioral impairment at T1. While most domains (Attention, Executive, Sensory, Language, Neglect) show a significant positive correlation with total lesion size, motor impairment exhibits a notable dissociation ( r = 0 . 19, p = 0 . 14), suggesting that motor outcomes are driven more by lesion topography than gross volume. (d) Example of longitudinal profile (patient P019) showing domain scores across time points, illustrating within-subject heterogeneity and delayed improvement in motor impairment emerging from T3 onward. Parentheses report the NMF domain composite score (arbitrary units; scaled to [0,1]) at each timepoint; higher values indicate greater impairment. This individual example is shown for illustration and is not intended to be representative of the full cohort.](figures/page_009.svg)

**Figure labels:**

- (a)
- (b)
- (c)
- (d)
- Patient 019

mains.

### Multivariate brain-behavior coupling reveals a predictive acute functional signature

The behavioral trajectories across the first post-stroke year revealed both a shared recovery trend and substantial inter-individual variability, motivating a direct test of whether early connectome organization carries prognostic information about later clinical status. We therefore implemented a two-stage brain-behavior framework that combines multivariate association with out-ofsample prediction (Fig. 7). In the first stage, we used Partial Least Squares Correlation (PLSC) to identify latent modes that maximize covariance between wholebrain functional connectivity (brain block) and the set of behavioral domain scores (behavior block) [75]. In the second stage, we converted the significant PLSC brain component into an interpretable connectivity mask and used this reduced feature set to constrain ridge regression models, evaluated with leave-one-subject-out (LOSO) cross-validation. In a way, this strategy follows connectome-based prediction principles [27], while explicitly leveraging multivariate brain-behavior structure. To avoid data leakage [76], we enforced strict temporal separation between feature discovery and prediction. Behavioral scores were first residualized to remove linear time effects, ensuring that predictions were not driven by simple mean recovery trends. Furthermore, PLSC feature selection was performed solely on T i data, and the resulting connectivity mask was then applied to predict behavior at strictly independent follow-up time points (i.e. T i +1 to T 4 ).

At the acute stage, PLSC identified a robust multivariate connectivity pattern with significant edges distributed across canonical systems and carrying both positive and negative weights (Fig. 7 b ). When summarized at the network level, the latent mask emphasized between-network interactions and a characteristic bal-

![FIG. 7. Multivariate brain-behavior mapping and longitudinal forecasting of clinical outcomes. (a) Two-stage predictive framework coupling Partial Least Squares Correlation (PLSC) with Ridge regression. Latent axes of maximal covariance between functional connectivity (Brain X ) and behavioral scores (Behavior Y ) are identified via PLSC. Significant components generate a connectivity mask for Ridge regression, validated using a leave-one-subject-out (LOSO) approach to predict outcomes at subsequent time points ( T i → T i +1 ... 4 ). (b) Network-level aggregation of the significant PLSC connectivity mask derived at the acute stage ( T 1 ). Heatmaps display the percentage of significantly negative (blue) and positive (red) edges, highlighting the prominent contribution of higher-order association systems (FP, DMN) and subcortical structures (SC) to the acute behavioral phenotype. (c) LOSO prediction performance ( R 2 ) for individual behavioral domains using the T 1 latent mask. The model successfully forecasts language, executive, and attention outcomes at follow-up ( T 2 , T 3 , T 4 ), whereas motor and neglect domains show negligible predictability from this functional signature. (d) Prediction accuracy for a global composite behavioral score across longitudinal intervals. Accuracy decays as the temporal gap from T 1 increases but peaks during the late sub-acute to chronic transition ( T 3 → T 4 ; R 2 = 0 . 584), reflecting late-stage stabilization of the brain-behavior relationship. (e) Scatter plots correlating actual versus predicted global scores for some of the intervals reported in panel (d).](figures/page_010.svg)

**Figure labels:**

- (b)
- (a)
- (c)
- (e)
- (d)
- PLSC significant mask (T1)
- T2
- T3
- T4
- Leave-one-subject-out prediction with T1 mask
- Prediction
- (R 2
- )
- Ridge
- Regression
- PLSC
- (covariance)
- Brain
- (X)
- Behavior
- (Y)
- Latent
- mask
- Brain-behavior pipeline
- Composite score prediction

ance of positively and negatively weighted edges, providing an interpretable functional signature of acute impairment that could be propagated forward as a fixed feature set. Using this acute PLSC-derived mask, ridge regression yielded selective, domain-specific prediction at follow-up (Fig. 7 c ). In LOSO prediction, acute connectome features explained meaningful variance in language, executive, and attention outcomes across subsequent stages, whereas other domains showed limited or no predictability from the same mask. This specificity was not trivially explained by model flexibility. Prediction performance was stable across ridge regularization strengths (main analyses: α = 1), and models trained on the full, unmasked FC did not yield significant predictions across hyperparameter choices. These results indicate that the covariance-informed mask isolates a subset of altered connections that is disproportionately informative for later cognitive outcomes.

We next assessed whether the same framework cap- tures recovery at a global level. To do so, we derived a single composite impairment score per patient and time point by summarizing the joint domain profile (convexhull composite; see Methods for details), and repeated the PLSC-mask and ridge prediction across longitudinal intervals (Fig. 7 d-e ). Prediction accuracy decreased as the temporal gap from baseline increased, consistent with the accumulating influence of ongoing reorganization and intercurrent clinical factors over longer horizons. Notably, prediction was strongest for the late interval T 3 → T 4 ( R 2 = 0 . 584, r = 0 . 809, p < 0 . 001), exceeding performance for T 1 → T 2 ( R 2 = 0 . 444, r = 0 . 669, p < 0 . 001) and T 1 → T 4 ( R 2 = 0 . 322, r = 0 . 670, p < 0 . 001). This late-stage peak suggests that once patients reach the late sub-acute phase, behavior and the underlying functional configuration become more tightly coupled and therefore more predictable.

Together, these analyses link early connectome organization to later clinical status in a longitudinally separated

pipeline. PLSC isolates a multivariate acute connectivity signature [75], and ridge regression shows that this signature predicts recovery outcomes in specific cognitive domains as well as in a global composite measure.

### DISCUSSION

Stroke is increasingly viewed as a network disorder, in which focal lesions propagate their impact across large-scale systems by inducing disconnection and remote physiological alterations [3, 4, 44, 45, 47, 56]. Leveraging multimodal longitudinal data from the TiMeS cohort [71], we provided a multi-scale view of post-stroke connectome dynamics across the first year of recovery. Despite substantial focal damage, individual functional identity is remarkably resilient, consolidating within the first three weeks into a stable, patient-specific configuration. This early stabilization of global identity does not imply functional stasis, as link-wise connectivity continues to reorganize over months with a distinct temporal ordering of hyper- and hypo-connectivity. At the macroscale, patients show a gradual shift toward the range of healthy structure-function variability, despite a largely stationary structural backbone. Together, these results frame recovery as constrained navigation of a dynamical structure-function landscape, in which a stable individual scaffold emerges quickly while selected circuits continue to remodel within anatomical limits. Crucially, this early network organization is directly linked to clinical recovery, forming a stable foundation that predicts long-term behavioral outcomes.

### The paradox of rapid stabilization and persistent plasticity

Connectome fingerprinting was originally established as the capacity of functional connectivity to identify healthy individuals across sessions and conditions [15, 17, 28, 31, 90, 91]. Our data extend this framework to stroke, demonstrating that a focal injury does not permanently destabilize the idiosyncratic architecture of the individual brain. Instead, the connectome consolidates rapidly: by the early sub-acute phase (3 weeks), patients are as identifiable to themselves as they are in the late subacute/chronic phase. This suggests that the post-stroke brain does not remain in prolonged flux; rather, it quickly relaxes into a new 'recovery configuration', consistent with dynamical systems perspectives where brain activity occupies a restricted repertoire of metastable states constrained by the underlying anatomy [81, 82]. In this view, stroke acts as a high-energy perturbation that displaces the system from its pre-injury basin of attraction, but the system rapidly settles into a new local minimum rather than drifting without structure.

Crucially, this global stability coexists with-and perhaps relies on-the plasticity of specific functional an- chors. We found that higher-order association networks (DMN, FPN) maintained the strongest longitudinal stability, whereas subcortical and sensorimotor loops were more variable. This aligns with the notion that association cortices provide an integrative backbone for cognition [36, 78], while cortico-subcortical loops-which are particularly vulnerable to lesion-induced disruption-undergo more pronounced reweighting as sensorimotor control is re-optimized. This network-specific stability helps reconcile why global identifiability can plateau early even as clinically meaningful recovery continues: a stable functional identity provides the necessary background for the targeted remodeling of specific circuits.

### Decoupling of structural injury and functional reorganization

A central contribution of this work is to separate stable from dynamic components of post-stroke network change. The structural disconnection backbone estimated from diffusion data was largely stable across time, consistent with the view that the anatomical consequences of infarction stabilize early and show only limited changes further on, even when their network consequences are widespread [45, 47]. Functional connectivity, in contrast, continued to reorganize well into the chronic phase, consistent with longitudinal work showing evolving disruptions and partial normalization over months [35, 37, 38, 49]. This dissociation echoes a broader principle that anatomy constrains but does not uniquely determine function, which is shaped by indirect pathways, distributed interactions, and state-dependent dynamics [81, 82, 84]. It also provides a network-level substrate for diaschisis, where focal damage produces remote dysfunction through disconnection and rebalancing of interactions across systems [44].

Beyond this structure-function decoupling, our results refine the temporal interpretation of post-stroke plasticity. Specifically, we initially observed an early, transient increase in functional hyper-connectivity. This acute response was followed by a delayed rise in hypoconnectivity that peaked months post-stroke, disproportionately affecting association networks and corticosubcortical interactions. Early hyper-connectivity may reflect compensatory recruitment of available resources and short-term stabilization of communication, consistent with reports of distributed engagement in early recovery [40, 62, 65]. However, persistent hyperconnectivity is not necessarily adaptive. Models of interhemispheric imbalance and maladaptive contralesional influence predict poorer outcomes when compensatory recruitment becomes entrenched [64], especially in wellrecovered patients with limited remaining deficits [92]. The later emergence of widespread hypo-connectivity, especially in higher-order association systems and subcortical interactions, is consistent with network-disconnection

accounts of cognitive deficits after stroke [45, 46, 56]. Together, these findings argue against a simple narrative of monotonic 'normalization'. Instead, recovery appears to unfold through sequential phases of coupling and decoupling as the system rebalances integration and segregation and settles into a new stable configuration to limit remaining deficits [49].

### Recovery as a trajectory in a structure-function manifold

Patients were displaced acutely away from the healthy structure-function regime, mainly along the functional axis, and then gradually shifted back toward the envelope of healthy variability. This picture aligns with wholebrain modeling views in which the structural connectome shapes an attractor-like landscape of feasible functional states [82, 83]. In this framing, the stationary structural coordinate reflects the rigidity of the anatomical scaffold after focal injury, whereas the gradual increase in functional similarity reflects re-tuning of dynamics constrained by surviving pathways. Convergence was nonetheless incomplete. Substantial dispersion persisted across stage, consistent with variability in lesion topography, disconnection profiles, and compensatory strategies [45, 47, 87]. Rather than noise, this dispersion may reflect distinct recovery phenotypes in which injury reshapes the structure-function mapping differently, leading some patients to stable but suboptimal configurations.

### Multivariate brain-behavior signatures of recovery

Apractical motivation for individualized network mapping is prognosis, as it is still a challenge based on clinical evaluation only. Using domain-specific behavioral composites that are comparable across time [43], we found that while acute impairment in most domains scaled with overall lesion volume, motor deficits exhibited a notable dissociation. This matches a well-established principle that motor impairment and recovery depend strongly on lesion topography and corticospinal tract integrity rather than lesion size alone [43, 58, 88, 89, 93]. However, it is important to note that the limited variability of motor scores within our specific cohort may have statistically attenuated this association. The interplay of these biological constraints and potential analytic artifacts aligns closely with ongoing debates surrounding proportional recovery rules [57, 94-96].

Our brain-behavior analyses extend lesion-based accounts by directly coupling distributed functional architecture to multidomain behavior. PLSC is well-suited for this setting because it extracts latent modes that maximize covariance between high-dimensional brain features and multivariate behavior [75]. Using PLSC-derived masks to constrain ridge regression, we found that acute functional signatures carried prognostic information for language, executive function, and attention. Notably, these are domains that depend on distributed association networks and long-range integration [46, 56]. In contrast, motor and neglect outcomes were less predictable from the same functional mask. While this aligns with the tighter dependence of motor outcomes on specific descending pathways and the clinical heterogeneity of spatial-attention deficits, this limited predictability must be interpreted with caution. As noted above, the restricted variability of motor scores within our specific cohort likely attenuated the performance of these statistical models. Methodologically, our temporally separated feature discovery and follow-up prediction design follows best practices in connectome-based predictive modeling and addresses known pitfalls of leakage and overly optimistic estimates in moderate samples [27, 76]. The peak predictability from late sub-acute to chronic stages further suggests that after ∼ 3 months, the coupling between functional architecture and clinical phenotype becomes tighter and more stable, consistent with consolidation of a chronic recovery configuration.

### Limitations and future directions

Several limitations should guide interpretation. Missing modalities across time points reduce balanced sampling, and replication in larger cohorts with denser follow-up will be important. Resting-state fMRI after stroke can be influenced by vigilance, medication, and vascular or hemodynamic alterations, and future work should incorporate physiological monitoring and measures of vascular reactivity to better dissociate neuronal from vascular contributions. Predictive modeling in moderate samples remains vulnerable to instability, and external validation and multi-site generalization tests are critical, as emphasized by the broader neuroimaging prediction literature [76]. Extending fingerprinting and prediction to multimodal signals that show robust identifiability and may be more scalable clinically could strengthen translation [20, 21, 23].

Finally, functional connectivity and downstream inference can be sensitive to demographic and clinical covariates, as well as to how confounds are handled in multivariate pipelines [77, 97-99]. Although the main text reports results without explicitly residualizing age, sex, or lesion burden from FC, we consider robustness by re-estimating key effects after residualizing FC using linear mixed-effects models that included these covariates (Methods). This alternative specification yielded quite similar and concordant results for fingerprint stabilization, network-level hyper-/hypo-connectivity trajectories, and brain-behavior associations (Supplementary Figs. S6, S7, S8), supporting the interpretation that our main conclusions reflect genuine longitudinal reconfiguration rather than bein driven by these confounders.

In conclusion, our findings highlight a critical dissoci-

ation in post-stroke recovery: while structural damage remains largely stable, the brain rapidly consolidates a new, stable functional identity. This early stabilization provides a crucial macro-scale architecture, which allows specific networks to reorganize over the following months. Ultimately, mapping these dynamic functional shifts offers a powerful and individualized framework for predicting long-term behavioral recovery.

### METHODS

### Participants and study design

We analyzed longitudinal data from the TiMeS (Toward individualized medicine in stroke) cohort [71], a study examining stroke recovery with multimodal neuroimaging and detailed neuropsychological evaluation. Patients were assessed at four post-stroke stages: acute ( T 1 , ∼ 1 week), early sub-acute ( T 2 , ∼ 3 weeks), late subacute ( T 3 , ∼ 3 months), and chronic ( T 4 , ∼ 12 months). The present analyses included up to N = 64 stroke patients (availability varied across time points and modalities; mean age 66 . 5 ± 13 . 9 years; 18 females). See Table I for exact sample sizes per time point and analysis. Inclusion criteria were (1) age ≥ 18 years; (2) diagnosis of a first-ever or recurrent, ischemic or hemorrhagic stroke; (3) enrollment within 7 days of the stroke incident; (4) presence of upper-limb motor impairment, objectified by clinical assessment. For the full eligibility criteria, refer to [71]. Two healthy control cohorts were used to define normative reference distributions, ECONS ( N = 31, mean age 69 . 1 ± 4 . 2) and TrainStim ( N = 10, mean age 69 . 9 ± 4 . 6) [100, 101], acquired with harmonized protocols and processed with the same pipeline as the patient data. ECONS served as the primary reference for computing clinical identifiability and functional deviation statistics. All participants provided written informed consent in accordance with the Declaration of Helsinki, and the study was approved by the local Ethics Committee (Canton of Valais and Canton of Geneva, Switzerland). Because longitudinal follow-up was incomplete for some participants, each analysis used all available data for the required modality and time point unless stated otherwise. Analyses requiring joint structure-function information were restricted to participants with complete multimodal data for the corresponding sessions.

### MRI acquisition and preprocessing

Magnetic resonance imaging (MRI) data were acquired on a 3T Siemens Prisma scanner. Resting-state BOLD fMRI was acquired using a multi-band echo-planar imaging (EPI) sequence (TR = 1 , 250 ms; TE = 32 ms; flip angle = 58 ◦ ; 2 mm isotropic resolution; multiband factor 5). Each session comprised 8.13 minutes of eyesopen (375 volumes). Structural and diffusion-weighted imaging (DWI) sequences were acquired at each session using the parameters listed in the TiMeS protocol [71]. Resting-state BOLD data were preprocessed using a standard pipeline including slice-timing correction, realignment, and co-registration to the structural scan. To mitigate non-neural noise, we applied nuisance regression (6 motion parameters, mean white matter, and cerebrospinal fluid signals) and bandpass filtering (0 . 01-0 . 15 Hz).

Diffusion preprocessing and structural connectome estimation

Diffusion-weighted data underwent the following pre-processing steps using MRtrix3 (version 3.0.4; https://www.mrtrix.org/) and FSL (version 6.0.6.4; https://fsl.fmrib.ox.ac.uk/fsl/docs/): Gibbs ringing was removed with MRtrix3, brain extraction was performed using FSL BET, susceptibility-induced distortion correction was applied with FSL topup, eddy-current and motion corrections were implemented using FSL eddy, and bias-field inhomogeneity was corrected with FSL FAST. Segmentation, including the brainstem, was performed using FreeSurfer (version 7.4; https://surfer.nmr.mgh.harvard.edu/). Anatomical images were registered to diffusion space using ANTs (version 2.4.4; https://github.com/ANTsX/ANTs) to ensure alignment, and tissue-type maps were generated for multi-tissue modeling. Fiber orientation distributions were estimated using multi-shell, multi-tissue constrained spherical deconvolution (MSMT-CSD) [102], and whole-brain tractography was performed using probabilistic tracking with 10 million streamlines. Streamline weights were refined using SIFT2 [103] to improve the biological accuracy and reduce the weighting of false positive connections. A subject-specific structural connectome was obtained by mapping streamline weights to the Glasser atlas regions using the MRtrix3 tck2connectome function.

Functional and structural connectome construction

For each session, whole-brain functional connectivity (FC) was estimated using a combined cortical-subcortical parcellation of 377 regions: 360 cortical parcels from the Glasser parcellation atlas [72] and 17 subcortical as provided by the HCP release (filename 'Atlas ROI2.nii.gz'; left and right: thalamus, caudate, putamen, pallidum, amygdala, accumbens, ventral diencephalon; and brainstem). Hippocampal parcels of the Glasser parcellation were considered as subcortical ones. Individual functional connectomes were constructed by computing the Pearson correlation coefficient between all pairs of regional time series, resulting in a 377 × 377 symmetric association matrix. For network-level analy-

ses, nodes were assigned to seven canonical Resting State Networks (RSNs) [78] (Visual, Somatomotor, Dorsal Attention, Ventral Attention, Limbic, Frontoparietal, Default Mode) plus Subcortical structures.

### Connectome fingerprinting and identifiability metrics

To quantify the stability of patient-specific functional architecture, we employed the connectome fingerprinting framework [15, 17]. For subject s at time points T i and T j , longitudinal self-similarity was defined as

I self ,s ( T i , T j ) = corr( FC s ( T i ) , F C s ( T j )) , (1)

For each interval ( T i , T j ), we constructed an identifiability matrix by correlating vectorized FC patterns across all pairs of subjects (test at T i , retest at T j ). Within-subject similarity corresponds to diagonal entries, whereas between-subject similarity corresponds to off-diagonal entries. Differential identifiability was defined as

I diff = I self -I others , (2)

capturing whether, on average, subjects remain more similar to themselves than to other individuals.

### Clinical similarity to healthy controls

To quantify deviation from healthy norms, we computed an individual clinical similarity index adapted from Ref. [28]. For each stroke subject s at time T i ,

I clinical ,s ( T i ) = 1 N H N H ∑ h =1 corr( FC s ( T i ) , ( FC h )) , (3)

where FC h denotes the FC of healthy individual h and N H is the number of controls.

### Statistical inference for longitudinal fingerprinting

To account for repeated measures and unbalanced sampling, we tested changes in I self across longitudinal intervals using linear mixed-effects models (LMMs) with subject-specific random intercepts:

I self ∼ Interval + (1 | Subject) , (4)

where Interval is a categorical fixed effect representing the time pairing (e.g., T 1 -T 4 , T 2 -T 4 , T 3 -T 4 ).Models were fit using restricted maximum likelihood (REML), and inference on fixed effects was performed using Wald tests (FDR-corrected). Effect sizes were summarized using Cohen's d [80]. Mann-Whitney U tests were used for I clinical comparisons, with FDR correction at q < 0 . 05.

### Single-edge fingerprinting and link reliability

To localize stable connections that support individual identifiability, we estimated the intraclass correlation coefficient (ICC) for each edge using a one-way randomeffects model [74]. For a given interval ( T i , T j ), each subject contributed two observations per edge, e n ( T i ) and e n ( T j ). ICC was computed as

ICC(1) = MSB -MSW MSB+( k -1)MSW , (5)

where MSB and MSW denote between-subject and within-subject mean squares, respectively, and k = 2 observations per subject. Edges with ICC > 0 . 6 were defined as reliable individual edges , consistent with thresholds used in prior fingerprinting work [23, 31]. To mitigate sample-size dependence of ICC estimates, we used bootstrapping: for each interval, ICC matrices were computed over 200 bootstrap resamples using a fixed number of subjects ( N = 15) drawn from those available for that interval, and then averaged. Node-level contributions were obtained by summing ICC values across incident edges, yielding a nodal ICC score that reflects the extent to which a node's connectivity profile contributes to identifiability.

### Structural disconnection and disconnectome estimation

To characterize the structural backbone of stroke, we estimated a disconnectome from diffusion-derived structural connectivity by overlaying each participant's binary lesion mask onto the tractogram and retaining only streamlines intersecting the lesion. For each subject and time point, we derived an indicator of structurally disrupted edges by thresholding edges with nonzero disconnection evidence in the disconnectome matrices. Group summaries were computed as the fraction of subjects exhibiting a disrupted edge within each within- and between-network block. Robustness was assessed by comparing the primary disconnectome estimation against alternative lesion-based procedures, including BCB toolkit-based disconnection [79], yielding convergent group-level patterns (Supplementary Figs. S5).

### Whole-brain structure-function state-space embedding

To provide a compact description of longitudinal brainstate shifts, we embedded each patient session into a joint structure-function space defined by similarity to a normative healthy template. Structural similarity was computed as cosine similarity between the vectorized subject structural connectome and the mean healthy structural connectome (ECONS). Functional similarity was computed analogously using the vectorized FC and the mean healthy FC. The healthy reference distribution was represented with a two-dimensional Gaussian kernel density

estimate (KDE), and a normative envelope was defined by thresholding this density at 95%. Patient sessions falling outside this envelope were classified as outside healthy variability. Longitudinal changes were summarized by a drift toward the peak of the healthy density and by the time-dependent fraction of outliers.

### Behavioral scores

At each time point, patients underwent a multidomain behavioral assessment comprising 40 validated tests spanning motor, sensory, and cognitive functions [71]. Missing data were imputed using principal component-based methods (missMDA). Motor and sensory scores were normalized as ratios between affected and unaffected limbs, and all measures were subsequently min-max scaled such that higher values reflected greater impairment. To derive a single interpretable score per domain, variables with ceiling effects or high intercorrelations ( r > 0 . 8) within the same domain were excluded. Non-negative matrix factorization (NMF) [104] was then applied at T1 to extract one latent, non-negative feature per domain, yielding normalized (0-1), additive measures of impairment across Motor, Attention, Executive, Language, and Neglect domains, with higher values consistently reflecting greater impairment. The resulting model was applied to subsequent timepoints to ensure consistent scaling and enable longitudinal comparisons. Model performance was assessed using variance accounted for (VAF), with the derived features explaining 66% of the variance for Neglect and greater than 80% for all other domains. Lesion size was quantified as the number of lesioned voxels at T 1 and analyzed as log(1 + voxels). Associations between lesion volume and acute behavioral impairment were assessed using Spearman correlation.

### Detrending behavioral scores for longitudinal prediction

Because behavioral scores exhibited systematic time dependence, we reduced temporal confounding before prediction. For subjects with complete longitudinal behavioral data, we fit an ordinary least squares model for each domain as a function of time (coded as 0, 1, 2, 3 for T 1 . . . T 4 ) and retained residuals as detrended behavioral scores. For subjects without complete longitudinal behavioral data, we retained raw scores to avoid extrapolation. This procedure reduces apparent predictability driven by shared temporal trends rather than brainbehavior coupling.

Multivariate brain-behavior association and leakage-aware prediction

We related FC features to multidomain behavior using Partial Least Squares Correlation (PLSC) [75].

At each time point T i , we assembled a brain matrix X (subjects × edges, using vectorized FC) and a behavioral matrix Y (subjects × domains, using detrended NMF scores). PLSC was computed with pyls ( behavioral pls ) Python package [105], assessing latent-variable significance via permutation testing ( n perm = 1 , 000) and edge reliability via bootstrapping ( n boot = 1 , 000). Reliable edges were defined using a bootstrap-ratio threshold | BSR | ≥ 2 . 0.

To test prognostic value while minimizing data leakage, we enforced temporal separation between feature discovery and prediction. Specifically, PLSC was fit only at time T i using brain and behavior from T i , yielding a latent connectivity mask. This fixed mask was then applied to FC at later sessions ( T i +1 . . . T 4 ) to predict follow-up behavior. Prediction used ridge regression (L2regularized linear regression) evaluated with leave-onesubject-out (LOSO) cross-validation. The ridge penalty was set to α = 1 in primary analyses, with stable results across alternative values (e.g. α = 0 . 1 , 10). Performance was quantified using out-of-sample R 2 for each behavioral domain and for a global composite impairment score.

### Covariate handling and robustness analyses

Main results are presented using minimally adjusted FC estimates, without explicitly regressing demographic or clinical covariates from the connectomes. To assess whether our findings were sensitive to potential confounding by age, sex, or lesion burden, we repeated the principal analyses after residualizing FC using linear mixed-effects models (LME). Across all core results-fingerprint stabilization, network-level hyper/hypo-connectivity trajectories, the joint structurefunction embedding, and brain-behavior associationsthe residualized analyses produced results that were quite similar to the primary analyses (Supplementary Figs. S6S8).

Covariate correction was implemented independently for each FC edge using a two-stage procedure designed to remove only population-level nuisance effects while preserving subject-specific connectivity structure (i.e., random intercepts). In the first stage, we estimated age and sex effects using all participants (patients and controls) with the following model:

FC s,t = β 0 + β 1 Age s + β 2 Sex s + u s + e s,t . (6)

Here, FC s,t denotes the FC value for a given edge for subject s at session/time point t ; β 0 is a fixed intercept; β 1 and β 2 are fixed-effect coefficients for age (zscored) and sex (effect-coded); u s is the subject-specific random intercept capturing stable between-subject differences; and e s,t is the residual term capturing withinsubject/session variability not explained by the model (statsmodels MixedLM , REML). We subtracted only the fixed-effect contribution of age and sex, ˆ β 1 Age s + ˆ β 2 Sex s ,

thereby retaining u s (and thus the subject-specific baseline).

In the second stage, restricted to stroke patients, we modeled the age/sex-adjusted FC values as a function of lesion size:

FC (1) s,t = γ 0 + γ 1 log(1 + voxels s,t ) + v s + r s,t , (7)

where log(1 + voxels s,t ) is the log-transformed lesion volume (mean-centered within patients), γ 0 and γ 1 are fixed effects, v s is a patient-specific random intercept, and r s,t is the residual term. As above, we subtracted only the fixed-effect lesion-size contribution, ˆ γ 1 log(1 + voxels s,t ), preserving the patient-specific intercept v s .

### Multiple-comparison correction

Unless stated otherwise, statistical tests were twosided. Edge-wise analyses controlled false discovery rate across connections using Benjamini-Hochberg correction ( q < 0 . 05). Mixed-model contrasts were FDR-corrected across planned comparisons. Effect sizes are reported as Cohen's d [80] where appropriate.

### Code availability

The Python code used in this work will be made available upon acceptance of the manuscript on AS GitHub page.

### Acknowledgment

A.S. has received funding from the European Union's Horizon 2020 research and innovation programme under the Marie Skglyph[suppress] lodowska-Curie grant agreement no. 101208090. A.S. thanks D. Orsenigo, M. Nurisso, and M. Diano for helpful discussions. This study was funded by 'Personalized Health and Related Technologies (PHRT#2017-205) of the ETH Domain to FCH, the Defitech Foundation (Strike-the-Stroke project, Morges, Switzerland) to FCH, and the Wyss Center for Bio and Neuroengineering (WP030; Geneva, Switzerland) to FCH.

***TABLE I. Data availability across the TiMeS longitudinal cohort . Entries report the number of stroke patients with available data for resting-state fMRI (BOLD), BOLD plus behavioral assessment, BOLD plus lesion information, or all modalities jointly, at each post-stroke session. Columns labeled T i & T j indicate the number of patients with data available at both time points, enabling paired longitudinal analyses. Columns labeled T1-T3 and T1-T4 indicate the number of patients with complete longitudinal coverage across the corresponding interval.***

|                   | T1 | T2 | T3 | T4 | T 1& T 2 | T 1& T 3 | T 1& T 4 | T 2& T 3 | T 2& T 4 | T 3& T 4 | T1-T3 | T1-T4 |
| ----------------- | -- | -- | -- | -- | -------- | -------- | -------- | -------- | -------- | -------- | ----- | ----- |
| BOLD              | 62 | 53 | 44 | 40 | 45       | 39       | 33       | 37       | 31       | 31       | 32    | 22    |
| BOLD & Behavioral | 56 | 53 | 43 | 39 | 43       | 37       | 31       | 36       | 30       | 30       | 31    | 21    |
| BOLD & Lesions    | 60 | 50 | 41 | 33 | 43       | 37       | 27       | 33       | 24       | 25       | 30    | 17    |
| All               | 54 | 50 | 40 | 33 | 41       | 35       | 26       | 32       | 24       | 25       | 29    | 17    |

- O. Sporns, G. Tononi, and R. K¨ otter, 'The Human Connectome: A Structural Description of the Human Brain,' PLoS Computational Biology 1 , e42 (2005).
- D. S. Bassett and O. Sporns, 'Network neuroscience,' Nature neuroscience 20 , 353-364 (2017).
- E. Bullmore and O. Sporns, 'Complex brain networks: Graph theoretical analysis of structural and functional systems,' Nature Reviews Neuroscience 10 , 186-198 (2009).
- E. Bullmore and O. Sporns, 'The economy of brain network organization,' Nature Reviews Neuroscience 13 , 336-349 (2012).
- D. C. Van Essen, K. Ugurbil, E. Auerbach, D. Barch, T. E. J. Behrens, R. Bucholz, A. Chang, L. Chen, M. Corbetta, S. W. Curtiss, S. Della Penna, D. Feinberg, M. F. Glasser, N. Harel, A. C. Heath, L. LarsonPrior, D. Marcus, G. Michalareas, S. Moeller, R. Oostenveld, S. E. Petersen, F. Prior, B. L. Schlaggar, S. M. Smith, A. Z. Snyder, J. Xu, and E. Yacoub, 'The Human Connectome Project: A data acquisition perspective,' NeuroImage Connectivity, 62 , 2222-2231 (2012).
- D. C. Van Essen, S. M. Smith, D. M. Barch, T. E. J. Behrens, E. Yacoub, and K. Ugurbil, 'The WU-Minn Human Connectome Project: An overview,' NeuroImage Mapping the Connectome, 80 , 62-79 (2013).
- A. Fornito, A. Zalesky, and E. Bullmore, Fundamentals of Brain Network Analysis (Academic Press, 2016).
- O. Sporns, 'Structure and function of complex brain networks,' Dialogues in Clinical Neuroscience 15 , 247262 (2022).
- C. J. Stam, 'Modern network science of neurological disorders,' Nature Reviews Neuroscience 15 , 683-695 (2014).
- S. E. Morgan, S. R. White, E. T. Bullmore, and P. E. V´ ertes, 'A Network Neuroscience Approach to Typical and Atypical Brain Development,' Biological Psychiatry: Cognitive Neuroscience and Neuroimaging Computational Methods and Modeling in Psychiatry, 3 , 754766 (2018).
- D. S. Bassett, C. H. Xia, and T. D. Satterthwaite, 'Understanding the Emergence of Neuropsychiatric Disorders With Network Neuroscience,' Biological Psychiatry: Cognitive Neuroscience and Neuroimaging Computational Methods and Modeling in Psychiatry, 3 , 742753 (2018).
- L. Douw, E. van Dellen, A. A. Gouw, A. Griffa, W. de Haan, M. van den Heuvel, A. Hillebrand, P. Van Mieghem, I. A. Nissen, W. M. Otte, Y. D. Reijmer, M. M. Schoonheim, M. Senden, E. C. W. van Straaten, B. M. Tijms, P. Tewarie, and C. J. Stam, 'The road ahead in clinical network neuroscience,' Network Neuroscience 3 , 969-993 (2019).
- F. De Vico Fallani, G. Vecchiato, J. Toppi, L. Astolfi, and F. Babiloni, 'Subject identification through standard EEG signals during resting states,' in 2011 Annual International Conference of the IEEE Engineering in Medicine and Biology Society (2011) pp. 2331-2333.
- O. Miranda-Dominguez, B. D. Mills, S. D. Carpenter, K. A. Grant, C. D. Kroenke, J. T. Nigg, and D. A. Fair, 'Connectotyping: Model Based Fingerprinting of the Functional Connectome,' PLOS ONE 9 , e111048

(2014).

- E. S. Finn, X. Shen, D. Scheinost, M. D. Rosenberg, J. Huang, M. M. Chun, X. Papademetris, and R. T. Constable, 'Functional connectome fingerprinting: Identifying individuals using patterns of brain connectivity,' Nature Neuroscience 18 , 1664-1671 (2015).
- M. G. Preti, D. Van De Ville, and E. Amico, 'Brain fingerprinting: A signal processing perspective,' IEEE Signal Processing Magazine 42 , 91-102 (2025).
- E. Amico and J. Go˜ ni, 'The quest for identifiability in human functional connectomes,' Scientific Reports 8 , 1-14 (2018), arxiv:1707.02365.
- M. Fraschini, M. Demuru, A. Crobe, F. Marrosu, C. J. Stam, and A. Hillebrand, 'The effect of epoch length on estimated EEG functional connectivity and brain network organisation,' Journal of Neural Engineering 13 , 036015 (2016).
- W. Kong, L. Wang, S. Xu, F. Babiloni, and H. Chen, 'EEG Fingerprints: Phase Synchronization of EEG Signals as Biomarker for Subject Identification,' IEEE Access 7 , 121165-121173 (2019).
- M. Demuru and M. Fraschini, 'EEG fingerprinting: Subject-specific signature based on the aperiodic component of power spectrum,' Computers in Biology and Medicine 120 , 103748 (2020).
- J. d. S. Rodrigues, F. L. Ribeiro, J. R. Sato, R. C. Mesquita, and C. E. B. J´ unior, 'Identifying individuals using fNIRS-based cortical connectomes,' Biomedical Optics Express 10 , 2889-2897 (2019).
- J. da Silva Castanheira, H. D. Orozco Perez, B. Misic, and S. Baillet, 'Brief segments of neurophysiological activity enable individual differentiation,' Nature Communications 12 , 5713 (2021).
- E. Sareen, S. Zahar, D. V. D. Ville, A. Gupta, A. Griffa, and E. Amico, 'Exploring MEG brain fingerprints: Evaluation, pitfalls, and interpretations,' NeuroImage 240 , 118331 (2021).
- E. S. Finn and M. D. Rosenberg, 'Beyond fingerprinting: Choosing predictive connectomes over reliable connectomes,' NeuroImage 239 , 118254 (2021).
- M. D. Rosenberg, E. S. Finn, D. Scheinost, X. Papademetris, X. Shen, R. T. Constable, and M. M. Chun, 'A neuromarker of sustained attention from whole-brain functional connectivity,' Nature Neuroscience 19 , 165171 (2016).
- W. Liu, N. Kohn, and G. Fern´ andez, 'Intersubject similarity of personality is associated with intersubject similarity of brain connectivity patterns,' NeuroImage 186 , 56-69 (2019).
- X. Shen, E. S. Finn, D. Scheinost, M. D. Rosenberg, M. M. Chun, X. Papademetris, and R. T. Constable, 'Using connectome-based predictive modeling to predict individual behavior from brain connectivity,' Nat Protoc 12 , 506-518 (2017).
- P. Sorrentino, R. Rucco, A. Lardone, M. Liparoti, E. Troisi Lopez, C. Cavaliere, A. Soricelli, V. Jirsa, G. Sorrentino, and E. Amico, 'Clinical connectome fingerprints of cognitive decline,' NeuroImage 238 , 118253 (2021).
- E. Troisi Lopez, R. Minino, M. Liparoti, A. Polverino, A. Romano, R. De Micco, F. Lucidi, A. Tessitore,
- Amico, G. Sorrentino, V. Jirsa, and P. Sorrentino, 'Fading of brain network fingerprint in Parkinson's disease predicts motor clinical impairment,' Human Brain Mapping 44 , 1239-1250 (2023).
- A. Romano, E. Trosi Lopez, M. Liparoti, A. Polverino, R. Minino, F. Trojsi, S. Bonavita, L. Mandolesi, C. Granata, E. Amico, G. Sorrentino, and P. Sorrentino, 'The progressive loss of brain network fingerprints in Amyotrophic Lateral Sclerosis predicts clinical impairment,' NeuroImage: Clinical 35 , 103095 (2022).
- S. Stampacchia, S. Asadi, S. Tomczyk, F. Ribaldi, M. Scheffler, K.-O. L¨ ovblad, M. Pievani, A. B. Fall, M. G. Preti, P. G. Unschuld, D. Van De Ville, O. Blanke, G. B. Frisoni, V. Garibotto, and E. Amico, 'Fingerprints of brain disease: Connectome identifiability in Alzheimer's disease,' Communications Biology 7 , 1-16 (2024).
- V. L. Feigin, R. V. Krishnamurthi, P. Parmar, B. Norrving, G. A. Mensah, D. A. Bennett, S. Barker-Collo, A. E. Moran, R. L. Sacco, T. Truelsen, S. Davis, J. D. Pandian, M. Naghavi, M. H. Forouzanfar, G. Nguyen, C. O. Johnson, T. Vos, A. Meretoja, C. J. Murray, G. A. Roth, and GBD 2013 Writing Group and GBD 2013 Stroke Panel Experts Group, 'Update on the Global Burden of Ischemic and Hemorrhagic Stroke in 19902013: The GBD 2013 Study,' Neuroepidemiology 45 , 161-176 (2015).
- P. B. Gorelick, 'The global burden of stroke: Persistent and disabling,' The Lancet Neurology 18 , 417-418 (2019).
- T. Vos, S. S. Lim, C. Abbafati, K. M. Abbas, M. Abbasi, and et al., 'Global burden of 369 diseases and injuries in 204 countries and territories, 1990-2019: A systematic analysis for the Global Burden of Disease Study 2019,' The Lancet 396 , 1204-1222 (2020).
- E. M. Nomura, C. Gratton, R. M. Visser, A. Kayser, F. Perez, and M. D'Esposito, 'Double dissociation of two cognitive control networks in patients with focal brain lesions,' Proceedings of the National Academy of Sciences 107 , 12017-12022 (2010).
- C. Gratton, E. M. Nomura, F. P´ erez, and M. D'Esposito, 'Focal Brain Lesions to Critical Locations Cause Widespread Disruption of the Modular Organization of the Brain,' Journal of Cognitive Neuroscience 24 , 1275-1285 (2012).
- A. K. Rehme and C. Grefkes, 'Cerebral network disorders after stroke: Evidence from imaging-based connectivity analyses of active and resting brain states in humans,' The Journal of Physiology 591 , 17-31 (2013).
- S. Ovadia-Caro, K. Villringer, J. Fiebach, G. J. Jungehulsing, E. van der Meer, D. S. Margulies, and A. Villringer, 'Longitudinal Effects of Lesions on Functional Networks after Stroke,' Journal of Cerebral Blood Flow & Metabolism 33 , 1279-1285 (2013).
- B. Yuan, Y. Fang, Z. Han, L. Song, Y. He, and Y. Bi, 'Brain hubs in lesion models: Predicting functional network topology with lesion patterns in patients,' Scientific Reports 7 , 17908 (2017).
- M. C. Eldaief, S. McMains, R. M. Hutchison, M. A. Halko, and A. Pascual-Leone, 'Reconfiguration of Intrinsic Functional Coupling Patterns Following Circumscribed Network Lesions,' Cerebral Cortex 27 , 28942910 (2017).
- A. G. Guggisberg, P. J. Koch, F. C. Hummel, and C. M. Buetefisch, 'Brain networks and their relevance for stroke rehabilitation,' Clinical Neurophysiology 130 , 1098-1124 (2019).
- P. J. Koch, C.-H. Park, G. Girard, E. Beanato, P. Egger, G. G. Evangelista, J. Lee, M. J. Wessel, T. Morishita, G. Koch, J.-P. Thiran, A. G. Guggisberg, C. Rosso, Y.H. Kim, and F. C. Hummel, 'The structural connectome and motor recovery after stroke: Predicting natural recovery,' Brain 144 , 2107-2119 (2021).
- G. G. Evangelista, P. Egger, J. Br¨ ugger, E. Beanato, P. J. Koch, M. Ceroni, L. Fleury, A. Cadic-Melchior, N. H. Meyer, D. d. L. Rodr´ ıguez, G. Girard, B. L´ eger, J.-L. Turlan, A. M¨ uhl, P. Vuadens, J. Adolphsen, C. E. Jagella, C. Constantin, V. Alvarez, D. San Mill´ an, C. Bonvin, T. Morishita, M. J. Wessel, D. Van De Ville, and F. C. Hummel, 'Differential Impact of Brain Network Efficiency on Poststroke Motor and Attentional Deficits,' Stroke 54 , 955-963 (2023).
- E. Carrera and G. Tononi, 'Diaschisis: Past, present, future,' Brain 137 , 2408-2422 (2014).
- J. C. Griffis, N. V. Metcalf, M. Corbetta, and G. L. Shulman, 'Structural Disconnections Explain Brain Network Dysfunction after Stroke,' Cell Reports 28 , 2527-2540.e9 (2019).
- A. Salvalaggio, M. De Filippo De Grazia, M. Zorzi, M. Thiebaut de Schotten, and M. Corbetta, 'Poststroke deficit prediction from lesion and indirect structural and functional disconnection,' Brain 143 , 21732188 (2020).
- M. Thiebaut de Schotten, C. Foulon, and P. Nachev, 'Brain disconnections link structural connectivity with function and behaviour,' Nature Communications 11 , 5094 (2020).
- J. Lu, H. Liu, M. Zhang, D. Wang, Y. Cao, Q. Ma, D. Rong, X. Wang, R. L. Buckner, and K. Li, 'Focal Pontine Lesions Provide Evidence That Intrinsic Functional Connectivity Reflects Polysynaptic Anatomical Pathways,' Journal of Neuroscience 31 , 15065-15071 (2011).
- J. S. Siegel, B. A. Seitzman, L. E. Ramsey, M. Ortega, E. M. Gordon, N. U. F. Dosenbach, S. E. Petersen, G. L. Shulman, and M. Corbetta, 'Re-emergence of modular brain networks in stroke recovery,' Cortex 101 , 44-59 (2018).
- J. C. Griffis, N. V. Metcalf, M. Corbetta, and G. L. Shulman, 'Damage to the shortest structural paths between brain regions is associated with disruptions of resting-state functional connectivity after stroke,' NeuroImage 210 , 116589 (2020).
- B. J. He, A. Z. Snyder, J. L. Vincent, A. Epstein, G. L. Shulman, and M. Corbetta, 'Breakdown of Functional Connectivity in Frontoparietal Networks Underlies Behavioral Deficits in Spatial Neglect,' Neuron 53 , 905918 (2007).
- A. R. Carter, S. V. Astafiev, C. E. Lang, L. T. Connor, J. Rengachary, M. J. Strube, D. L. W. Pope, G. L. Shulman, and M. Corbetta, 'Resting interhemispheric functional magnetic resonance imaging connectivity predicts performance after stroke,' Annals of Neurology 67 , 365375 (2010).
- C.-h. Park, W. H. Chang, S. H. Ohn, S. T. Kim, O. Y. Bang, A. Pascual-Leone, and Y.-H. Kim, 'Longitudinal Changes of Resting-State Functional Connectivity Dur-

ing Motor Recovery After Stroke,' Stroke 42 , 1357-1362 (2011).

- C. Tang, Z. Zhao, C. Chen, X. Zheng, F. Sun, X. Zhang, J. Tian, M. Fan, Y. Wu, and J. Jia, 'Decreased Functional Connectivity of Homotopic Brain Regions in Chronic Stroke Patients: A Resting State fMRI Study,' PLOS ONE 11 , e0152875 (2016).
- A. Baldassarre, L. E. Ramsey, J. S. Siegel, G. L. Shulman, and M. Corbetta, 'Brain connectivity and neurological disorders after stroke,' Current Opinion in Neurology 29 , 706 (2016).
- J. S. Siegel, L. E. Ramsey, A. Z. Snyder, N. V. Metcalf, R. V. Chacko, K. Weinberger, A. Baldassarre, C. D. Hacker, G. L. Shulman, and M. Corbetta, 'Disruptions of network connectivity predict impairment in multiple behavioral domains after stroke,' Proceedings of the National Academy of Sciences 113 , E4367-E4376 (2016).
- W. D. Byblow, C. M. Stinear, P. A. Barber, M. A. Petoe, and S. J. Ackerley, 'Proportional recovery after stroke depends on corticomotor integrity,' Annals of Neurology 78 , 848-859 (2015).
- P. J. Koch and F. C. Hummel, 'Toward precision medicine: Tailoring interventional strategies based on noninvasive brain stimulation for motor recovery after stroke,' Current Opinion in Neurology 30 , 388 (2017).
- H. T. Hendricks, J. van Limbeek, A. C. Geurts, and M. J. Zwarts, 'Motor recovery after stroke: A systematic review of the literature,' Archives of Physical Medicine and Rehabilitation 83 , 1629-1637 (2002).
- Y.-Y. Huang, S.-D. Chen, X.-Y. Leng, K. Kuo, Z.-T. Wang, M. Cui, L. Tan, K. Wang, Q. Dong, and J.-T. Yu, 'Post-Stroke Cognitive Impairment: Epidemiology, Risk Factors, and Management,' Journal of Alzheimer's Disease 86 , 983-999 (2022).
- C. Grefkes, D. A. Nowak, S. B. Eickhoff, M. Dafotakis, J. K¨ ust, H. Karbe, and G. R. Fink, 'Cortical connectivity after subcortical stroke assessed with functional magnetic resonance imaging,' Annals of Neurology 63 , 236-246 (2008).
- C. Grefkes and G. R. Fink, 'Reorganization of cerebral networks after stroke: New insights from neuroimaging with connectivity approaches,' Brain 134 , 1264-1276 (2011).
- L. Talozzi, S. J. Forkel, V. Pacella, V. Nozais, E. Allart, C. Piscicelli, D. P´ erennou, D. Tranel, A. Boes, M. Corbetta, P. Nachev, and M. Thiebaut de Schotten, 'Latent disconnectome prediction of long-term cognitivebehavioural symptoms in stroke,' Brain 146 , 19631978 (2023), https://academic.oup.com/brain/articlepdf/146/5/1963/50725103/awad013.pdf.
- C. Grefkes and G. R. Fink, 'Connectivity-based approaches in stroke and recovery of function,' The Lancet Neurology 13 , 206-216 (2014).
- A. K. Rehme, S. B. Eickhoff, C. Rottschy, G. R. Fink, and C. Grefkes, 'Activation likelihood estimation metaanalysis of motor-related neural activity after stroke,' NeuroImage 59 , 2771-2782 (2012).
- A. R. Carter, G. L. Shulman, and M. Corbetta, 'Why use a connectivity-based approach to study stroke and recovery of function?' Neuroimage 62 , 2271-2280 (2012).
- U. N. Ismail, N. Yahya, and H. A. Manan, 'Investigating functional connectivity related to stroke recovery: A

systematic review,' Brain Res 1840 , 149023 (2024).

- L. E. Ramsey, J. S. Siegel, C. E. Lang, M. Strube, G. L. Shulman, and M. Corbetta, 'Behavioural clusters and predictors of performance during recovery from stroke,' Nat Hum Behav 1 , 0038 (2017).
- A. K. Bonkhoff, A. K. Rehme, L. Hensel, C. Tscherpel, L. J. Volz, F. A. Espinoza, H. Gazula, V. M. Vergara, G. R. Fink, V. D. Calhoun, N. S. Rost, and C. Grefkes, 'Dynamic connectivity predicts acute motor impairment and recovery post-stroke,' Brain Commun 3 , fcab227 (2021).
- Y. Tao, T. Schnur, J. Ding, R. Martin, and B. Rapp, 'Longitudinal changes in functional connectivity networks in the first year following stroke,' bioRxiv , 2025.03.10.642404 (2025).
- L. Fleury, P. J. Koch, M. J. Wessel, C. Bonvin, D. San Millan, C. Constantin, P. Vuadens, J. Adolphsen, A. Cadic Melchior, J. Br¨ ugger, E. Beanato, M. Ceroni, P. Menoud, D. De Leon Rodriguez, V. Zufferey, N. H. Meyer, P. Egger, S. Harquel, T. Popa, E. Raffin, G. Girard, J.-P. Thiran, C. Vaney, V. Alvarez, J.-L. Turlan, A. M¨ uhl, B. L´ eger, T. Morishita, S. Micera, O. Blanke, D. Van De Ville, and F. C. Hummel, 'Toward individualized medicine in stroke-The TiMeS project: Protocol of longitudinal, multi-modal, multi-domain study in stroke,' Frontiers in Neurology 13 (2022), 10.3389/fneur.2022.939640.
- M. F. Glasser, T. S. Coalson, E. C. Robinson, C. D. Hacker, J. Harwell, E. Yacoub, K. Ugurbil, J. Andersson, C. F. Beckmann, M. Jenkinson, S. M. Smith, and D. C. Van Essen, 'A multi-modal parcellation of human cerebral cortex,' Nature 536 , 171-178 (2016).
- P. E. Shrout and J. L. Fleiss, 'Intraclass correlations: Uses in assessing rater reliability,' Psychological Bulletin 86 , 420-428 (1979).
- D. Liljequist, B. Elfving, and K. Skavberg Roaldsen, 'Intraclass correlation - a discussion and demonstration of basic features,' PLOS ONE 14 , 1-35 (2019).
- A. Krishnan, L. J. Williams, A. R. McIntosh, and H. Abdi, 'Partial Least Squares (PLS) methods for neuroimaging: A tutorial and review,' NeuroImage Multivariate Decoding and Brain Reading, 56 , 455-475 (2011).
- G. Varoquaux, 'Cross-validation failure: Small sample sizes lead to large error bars,' NeuroImage 180 , 68-77 (2018).
- M. Rosenblatt, L. Tejavibulya, R. Jiang, S. Noble, and D. Scheinost, 'Data leakage inflates prediction performance in connectome-based machine learning models,' Nat Commun 15 , 1829 (2024).
- B. T. Thomas Yeo, F. M. Krienen, J. Sepulcre, M. R. Sabuncu, D. Lashkari, M. Hollinshead, J. L. Roffman, J. W. Smoller, L. Z¨ ollei, J. R. Polimeni, B. Fischl, H. Liu, and R. L. Buckner, 'The organization of the human cerebral cortex estimated by intrinsic functional connectivity,' Journal of Neurophysiology 106 , 11251165 (2011).
- C. Foulon, L. Cerliani, S. Kinkingn´ ehun, R. Levy, C. Rosso, M. Urbanski, E. Volle, and M. Thiebaut de Schotten, 'Advanced lesion symptom mapping analyses and implementation as BCBtoolkit,' Gigascience 7 , giy004 (2018).
- J. Cohen, Statistical power analysis for the behavioral sciences (routledge, 2013).
- G. Deco, G. Tononi, M. Boly, and M. L. Kringelbach, 'Rethinking segregation and integration: Contributions of whole-brain modelling,' Nat Rev Neurosci 16 , 430439 (2015).
- M. Breakspear, 'Dynamic models of large-scale brain activity,' Nat Neurosci 20 , 340-352 (2017).
- J. Vohryzek, G. Deco, B. Cessac, M. L. Kringelbach, and J. Cabral, 'Ghost Attractors in Spontaneous Brain Activity: Recurrent Excursions Into FunctionallyRelevant BOLD Phase-Locking States,' Front. Syst. Neurosci. 14 (2020), 10.3389/fnsys.2020.00020.
- C. J. Honey, O. Sporns, L. Cammoun, X. Gigandet, J. P. Thiran, R. Meuli, and P. Hagmann, 'Predicting human resting-state functional connectivity from structural connectivity,' Proceedings of the National Academy of Sciences 106 , 2035-2040 (2009).
- J. Go˜ ni, M. P. van den Heuvel, A. Avena-Koenigsberger, N. Velez de Mendizabal, R. F. Betzel, A. Griffa, P. Hagmann, B. Corominas-Murtra, J.-P. Thiran, and O. Sporns, 'Resting-brain functional connectivity predicted by analytic measures of network communication,' Proceedings of the National Academy of Sciences 111 , 833-838 (2014).
- E. Schlemm, R. Schulz, M. B¨ onstrup, L. Krawinkel, J. Fiehler, C. Gerloff, G. Thomalla, and B. Cheng, 'Structural brain networks and functional motor outcome after stroke-a prospective cohort study,' Brain Commun 2 , fcaa001 (2020).
- R. P. Rocha, L. Ko¸ cillari, S. Suweis, M. De Filippo De Grazia, M. T. de Schotten, M. Zorzi, and M. Corbetta, 'Recovery of neural dynamics criticality in personalized whole-brain models of stroke,' Nat Commun 13 , 3683 (2022).
- S. J. Page, L. V. Gauthier, and S. White, 'Size Doesn't Matter: Cortical Stroke Lesion Volume Is Not Associated With Upper Extremity Motor Impairment and Function in Mild, Chronic Hemiparesis,' Archives of Physical Medicine and Rehabilitation 94 , 817-821 (2013).
- L. L. Zhu, R. Lindenberg, M. P. Alexander, and G. Schlaug, 'Lesion Load of the Corticospinal Tract Predicts Motor Impairment in Chronic Stroke,' Stroke 41 , 910-915 (2010).
- A. I. Luppi, D. Golkowski, A. Ranft, R. Ilg, D. Jordan, D. Bzdok, A. M. Owen, L. Naci, E. A. Stamatakis, E. Amico, and B. Misic, 'General anaesthesia decreases the uniqueness of brain functional connectivity across individuals and species,' Nat Hum Behav 9 , 987-1004 (2025).
- I. Ricchi, A. Santoro, N. Kinany, C. Landelle, A. Khatibi, S. Vahdat, J. Doyon, R. L. Barry, and D. Van De Ville, 'Spine-prints: Transposing brain fingerprints to the spinal cord,' Imaging Neuroscience 4 , IMAG.a.1128 (2026).
- F. C. Hummel, P. Celnik, A. Pascual-Leone, F. Fregni, W. D. Byblow, C. M. Buetefisch, J. Rothwell, L. G. Cohen, and C. Gerloff, 'Controversy: Noninvasive and invasive cortical stimulation show efficacy in treating stroke patients,' Brain Stimulation 1 , 370-382 (2008).
- C. M. Stinear, 'Prediction of motor recovery after stroke: Advances in biomarkers,' The Lancet Neurology 16 , 826-836 (2017).
- R. L. Hawe, S. H. Scott, and S. P. Dukelow, 'Taking Proportional Out of Stroke Recovery,' Stroke 50 , 204-

211 (2019).

- T. M. H. Hope, K. Friston, C. J. Price, A. P. Leff, P. Rotshtein, and H. Bowman, 'Recovery after stroke: Not so proportional after all?' Brain 142 , 15-22 (2019).
- H. Bowman, A. Bonkhoff, T. Hope, C. Grefkes, and C. Price, 'Inflated Estimates of Proportional Recovery From Stroke,' Stroke 52 , 1915-1920 (2021).
- L. Snoek, S. Mileti´ c, and H. S. Scholte, 'How to control for confounds in decoding analyses of neuroimaging data,' NeuroImage 184 , 741-760 (2019).
- R. Ciric, D. H. Wolf, J. D. Power, D. R. Roalf, G. L. Baum, K. Ruparel, R. T. Shinohara, M. A. Elliott, S. B. Eickhoff, C. Davatzikos, R. C. Gur, R. E. Gur, D. S. Bassett, and T. D. Satterthwaite, 'Benchmarking of participant-level confound regression strategies for the control of motion artifact in studies of functional connectivity,' NeuroImage 154 , 174-187 (2017).
- S. Hamdan, B. C. Love, G. G. von Polier, S. Weis, H. Schwender, S. B. Eickhoff, and K. R. Patil, 'Confound-leakage: Confound removal in machine learning leads to leakage,' Gigascience 12 , giad071 (2023).
- M. Durand-Ruel, C.-h. Park, M. Moyne, P. MaceiraElvira, T. Morishita, and F. C. Hummel, 'Early motor skill acquisition in healthy older adults: Brain correlates of the learning process,' Cerebral Cortex 33 , 73567368 (2023), https://academic.oup.com/cercor/articlepdf/33/12/7356/50537941/bhad044.pdf.
- P. Maceira-Elvira, T. Popa, A.-C. Schmid, A. CadicMelchior, H. M¨ uller, R. Schaer, L. G. Cohen, and F. C. Hummel, 'Native learning ability and not age determines the effects of brain stimulation,' npj Sci. Learn. 9 , 69 (2024).
- B. Jeurissen, J.-D. Tournier, T. Dhollander, A. Connelly, and J. Sijbers, 'Multi-tissue constrained spherical deconvolution for improved analysis of multi-shell diffusion MRI data,' NeuroImage 103 , 411-426 (2014).
- R. E. Smith, J.-D. Tournier, F. Calamante, and A. Connelly, 'SIFT2: Enabling dense quantitative assessment of brain white matter connectivity using streamlines tractography,' NeuroImage 119 , 338-351 (2015).
- D. Lee and H. S. Seung, 'Algorithms for non-negative matrix factorization,' Advances in neural information processing systems 13 (2000).
- R. Markello and pyls developers, 'pypyls: A python implementation of partial least squares (pls) decomposition,' GitHub repository.

(a)

1.0 -

0.8 -

0.6 -

0.4 -

0.2 -

0

(d)

Patient Retest (T2)

Patient Retest (T3)

(T1, T4)

0.5 -

0.4 -

![FIG. S1. Longitudinal identifiability metrics across all pairs of time points. (a-c) Distributions of self-identifiability ( I self ), between-subject identifiability ( I others ), and identifiability difference [ I diff = ( I self -I others ]), for connectomes compared against the late-chronic reference ( T 4 ), i.e. between T1-T4, T2-T4 and T3-T4. All three metrics indicate that subject-level reconfiguration is largest between the acute (T1) and early sub-acute (T2) phases, as T1-T4 shows markedly lower identifiability than T2-T4 and T3-T4 (( ∗∗ p < 0 . 05, ∗∗ p < 0 . 01, Wilcoxon test, FDR-corrected). (d) Identifiability matrices for all longitudinal pairings, reporting success rate (SR), mean I diff , and Cohen's d . Pairings that are closer in time (e.g., T 1 -T 2 , T 2 -T 3 ) generally show higher SR and larger effect sizes. Notably, despite its shorter temporal separation, T 1 -T 3 shows lower SR and smaller effects than later intervals involving T 4 (e.g., T 2 -T 4 , T 3 -T 4 ), reinforcing the conclusion that a disproportionate reorganization of individual connectome identity is concentrated between the acute ( T 1 ) and early sub-acute ( T 2 ) stages.](figures/img_p022_0.png)

**Figure labels:**

- lothers
- 0.4 -
- 0.3 -
- 0.2
- 8 0.2-
- 0-
- -0.2
- (T2, 74)
- SR = 84.44%, Idir = 23.4, effect size = 2.57
- Patient Test (71)
- SR = 89.19%, Idiff = 23.63, effect size = 2.99
- Patient Test (T2)
- (T3, 74)
- 0.8
- Identification (r)
- (T1, 74)
- SR = 82.05%, /dim = 20.14, effect size = 2.1
- Patient Retest (T4)
- Patient Retest (T3)
- Patient Test (T1)
- SR = 83.87%, Idim = 24.91, effect size = 3.07
- (T1, T4)
- SR = 81.82%, Idir = 18.36, effect size = 1.96
- SR = 83.87%, Idir = 23.7, effect size = 2.97
- Patient Test (T3)

VIS

FP L VA DA SM

DMN

VIS -

SM-

DA -

VA-

L-

FP -

DMN -

SC -

•

VIS

![FIG. S2. Spatial specificity of connectome fingerprinting across times. Topography of stable individual functional connections, defined by an Intraclass Correlation Coefficient ( ICC ) > 0 . 6, evaluated between early recovery stages ( T 1 , T 2 , T 3 ) and the chronic baseline ( T 4 ). Matrices display the percentage of these highly stable edges within and between canonical functional networks and subcortical structures. Notably, connections involving higher-order association systems-specifically the frontoparietal (FP) and default mode (DMN) networks-exhibit the highest proportion of stable edges across evaluated intervals, suggesting that these networks form a persistent functional infrastructure that anchors the individual connectome post-stroke. To eliminate variance driven by sample attrition, this analysis was restricted exclusively to the subset of 22 patients common to the analyzed longitudinal intervals. Network abbreviations: VIS, visual; SM, somatomotor; DA, dorsal attention; VA, ventral attention; L, limbic; FP, frontoparietal; DMN, default mode; SC, subcortical.](figures/img_p023_0.png)

**Figure labels:**

- SM DA VA
- L FP
- DMN SC
- T1-T4
- VIS
- SM DA VA L FP
- T2-T4
- T3-T4
- DMN
- • SC
- VIS SM DA VA L FP DMN SC
- 5
- 15
- 20
- Percentage of connections with ICC > 0.6
- 30
- 40

![FIG. S3. Network-resolved consolidation of longitudinal self-identifiability. Heatmaps report the median withinsubject similarity ( I self ; Pearson correlation) of functional connectivity patterns computed between early sessions and the chronic endpoint ( T 4 ), summarized within and between canonical networks (VIS, SM, DA, VA, L, FP, DMN, SC). Top panels show median I self for the ( T 1 , T 4 ), ( T 2 , T 4 ), and ( T 3 , T 4 ) intervals. In line with an early reconfiguration of the individual fingerprint, I self increases markedly from T 1 to T 2 (and remains elevated at T 3 ), whereas differences between T 2 and T 3 are minimal, indicating little additional change after the early sub-acute stage. Bottom panels quantify the relative median increase in I self between successive early intervals (e.g., T 1 → T 2 , T 1 → T 3 , T 2 → T 3 ), expressed as a percentage of the corresponding T 4 -referenced baseline, further emphasizing that the dominant shift occurs between T 1 and T 2 rather than between T 2 and T 3 . Statistical significance of interval effects was assessed using linear mixed-effects models with subject-specific random intercepts and FDR correction across network blocks.](figures/page_024.svg)

**Figure labels:**

- VIS SM DA VA
- L
- FP DMNSC
- VIS
- SM
- DA
- VA
- FP
- DMN
- SC
- 0.63
- 0.37 0.60
- 0.60 0.52 0.62
- 0.40 0.54 0.57 0.63
- 0.29 0.25 0.30 0.38 0.53
- 0.49 0.44 0.58 0.60 0.40 0.64
- 0.49 0.44 0.57 0.61 0.44 0.61 0.70
- 0.39 0.39 0.37 0.46 0.47 0.38 0.42 0.54
- Median
- I
- self
- (T1
- T4)
- 0.73
- 0.50 0.67
- 0.63 0.61 0.69
- 0.55 0.63 0.65 0.71
- 0.42 0.38 0.43 0.47 0.61
- 0.55 0.56 0.64 0.67 0.48 0.70
- 0.59 0.58 0.65 0.68 0.54 0.67 0.74
- 0.46 0.47 0.47 0.54 0.54 0.45 0.47 0.56
- (T2
- 0.70
- 0.42 0.62
- 0.61 0.58 0.68
- 0.50 0.58 0.63 0.69
- 0.39 0.36 0.43 0.48 0.60
- 0.51 0.48 0.63 0.63 0.46 0.69
- 0.55 0.52 0.67 0.65 0.52 0.64 0.78
- 0.43 0.47 0.38 0.53 0.51 0.39 0.45 0.57
- (T3
- 0.3
- 0.4
- 0.5
- 0.6
- 0.7
- 0.8
- Pearson
- 15.4
- 33.8 10.9
- 3.5
- 17.9
- 9.9
- 35.9 17.4 14.3 12.6
- 42.5 51.8 41.1 21.9 14.4
- 11.3 27.6 11.3 11.6 19.3 10.1
- 20.2 30.4 15.1 11.0 20.9 11.1
- 6.1
- 17.6 19.8 27.0 18.0 14.3 18.1 10.9
- increase with respect to T4
- T1
- T2
- 10.7
- 13.4
- 2.5
- 11.0
- 8.7
- 25.3
- 8.5
- 11.1 10.1
- 31.8 45.4 42.2 25.3 13.4
- 2.6
- 9.2
- 8.4
- 5.1
- 16.3
- 8.1
- 12.5 16.3 18.1
- 6.3
- 17.7
- 11.5
- 8.8
- 21.7
- T3
- 10
- 20
- 30
- 40
- 50
- 60
- Relative increase (%)

![FIG. S4. Longitudinal evolution of clinical and functional connectome identification in the complete-case subsample. Analyses replicate Fig. 2 using only patients with resting-state fMRI available at all four post-stroke sessions ( N = 22), reducing statistical power but preserving the overall pattern of effects. (a) Clinical identifiability ( I clinical ), defined as similarity of each patient's FC to the ECONS reference, remains reduced relative to the healthy control comparison (TrainStim vs. ECONS) across timepoints; in this smaller subsample, group differences are attenuated and some contrasts no longer reach significance, consistent with limited power. (b) Self-identifiability ( I self ) between earlier sessions and the chronic endpoint (T4) shows the same temporal profile as in the full cohort, with lower stability for the acute interval ( T 1 -T 4 ) relative to later intervals and a rapid increase by the early sub-acute stage. In this subsample, the early increase is weaker and does not consistently survive correction, but the direction of effect matches the main analysis (LMM with subject-specific random intercept; FDRcorrected). (c) Network-resolved I self (median within/between Yeo networks and subcortical structures) reproduces the relative pattern of higher stability in association systems and lower stability in sensorimotor/subcortical blocks, albeit with increased variance. (d) Relative percentage increase in I self from T 1 to T 2 , referenced to T 4 , shows the same networks contributing most to early consolidation (notably VA, L, and SM), but with reduced statistical sensitivity compared to the full sample.](figures/page_025.svg)

**Figure labels:**

- (a)
- (d)
- (c)
- (b)
- Functional networks

/IS

/IS -

/IS -

2.3

0.6

0.3

ion - sion -

1.00

ion 1

1.00

1.00

sion -

1.00

SM -

SM - 0.2

SM - 8.8

1.3

3

13.3

4.7

DA -

DA -

0.7

4

0.2

DA -I

CB -

СВ -

CB-

CB -

VA -

VA

VA

1.1

2.5

9.6

0.45

0.49

0.52

0.48

8

0.2

3.6

1.7

12.8

4.4

L-

L-

STI-

DTI -

1.1

0.2

10.1

2.8

0.1

0.60

0.59

DTI-

0.60

DTI-

0.57

Fp

0.1

FP -

6.2

FP -

0.8

0.9

11.5

2.9

Lesion

MN - 4.5

MN -

0.5

0.1

Lesion

Lesion

Lesion

SC - 10.8

SC

SC -

0.8

2.6

VIS

1.6

5.2

0.9

1.00

1.00

9.1

1.9

0.8

5.8

1.6

2.2

0.68

0.5

0.68

0.74

0.74

0.8

1.7

7.2

5.7

1.1

0.3

12.1

0.4

1.8

10.1

16

8.5

4.9

SM

VIS SM

VIS SM

4.5

2.9

DA

DA

1.2

2.3

3.9

0.8

8.5

3.1

1.5

5.2

0.4

4

0.9

8.1

0.4

5.5

0.8

4.1

2.1

8.5

1.6

5.5

0.2

0.8

0.5

0.2

0.8

0.7

0.2

0.8

0.6

• 10

- 15

![FIG. S5. Comparison of direct and indirect measures of structural disconnection. Longitudinal quantification of structural network disruption for the same subset of patients used in Fig 3 estimated using three complementary methodological approaches across four time points (T1, 1 week; T2, 3 weeks; T3, 3 months; T4, 1 year). (a) Matrices display the network-level percentage of disconnected edges estimated via direct lesion masking (Lesion impairment), (b) probabilistic tractography using the BCB toolkit (BCB impairment), and (c) empirical patient-specific DTI tractography (DTI impairment). While the spatial topography of damage-heavily affecting subcortical (SC) and somatomotor (SM) connections-is consistent across methods, direct lesion masking yields higher absolute impairment magnitudes compared to DTI-based estimates. (d) Correlation matrices (Pearson's r) quantifying the spatial similarity between the structural damage profiles generated by each method. High positive correlations confirm that the topological pattern of the disconnectome is robust to the specific modality used for estimation. Network abbreviations: VIS, Visual; SM, Somatomotor; DA, Dorsal Attention; VA, Ventral Attention; L, Limbic; FP, FrontoParietal; DMN, Default Mode Network; SC, Subcortical.](figures/page_026.svg)

**Figure labels:**

- (a)
- (b)
- (c)
- (d)
- T1 - 1 week
- T2 - 3 weeks
- T3 - 3 months
- T4 - 1 year
- Lesion impairment
- DTI impairment
- BCB impairment
- 9.4
- 11
- 6
- 7.9
- 6.3
- 12.1
- L
- 9.1
- 7.8
- 13.9
- 6.2
- 12.6
- 17.7
- FP DMN SC
- 4.7
- 5.3
- 4.2
- VIS
- 9.9
- 8,9
- 15.3
- SM
- 8.9
- 6.1
- 6.6
- 5.6
- 12.2
- DA
- 9.7
- 10.2
- 9.2
- 15.5
- VA
- 6.8
- 7.6
- 6.4
- 7
- - 4.9
- - 5.4
- 5.9
- - 4.1
- 12.8
- 13.5| 12.6 18.3
- 9.8
- 9.5
- 8.3
- 13.6
- 11.1
- DAI
- 11.3
- 9.3
- 8.7
- 7.7
- 8.1
- 5.1
- 5.8
- 4.3
- 11.8
- 12.5 11.3 | 16.4
- L FP DMN SC
- 13.1
- 8
- 7.2
- 8.2
- 12.5
- 6.9
- 10.8
- 7.3
- 11.9
- 5.7
- 10.4
- 14.6
- 10
- 2.1
- 2
- 1.3
- 5.4
- 2.2
- 1.4
- 1.1
- 5.2
- 3.6
- 16.6
- 0.7
- 3
- 3.1
- 4.1
- 2.8
- 11.2
- VIS SM
- 2.6
- 1.7
- 4.9
- 3.8
- 9.6
- 2.4
- 3.3
- 23.3
- 0.5
- 0.2
- 1.9
- 1.6
- 0.6
- 0.3
- 1
- 1.5
- VIS SM DA
- 0.8
- 13.8
- 0.9
- 1.2
- 2.7
- 7.1
- 4.6
- 2.3
- 3.2
- 4.8
- 3.4
- 17.6
- 5
- 0
- 0.1
- 0.4
- DA VA
- 2.1 1.4
- 8.6
- 1.8
- 1.00
- DTI

0.74

0.74

0.68

0.68

26

![FIG. S6. Robustness of clinical and functional connectome identification controlling for age, gender, and lesion size. Functional connectivity matrices were residualized for age and gender (all subjects) and log-transformed lesion volume (stroke patients only) prior to analysis. (a) Distribution of clinical identifiability scores ( I clinical ) for healthy controls (TrainStim vs. ECONS) and stroke patients (relative to ECONS). Controlling for covariates, stroke scores are significantly lower than healthy controls across all four time points ( ∗ ∗ ∗ p < 0 . 001, FDR-corrected Mann-Whitney U test). (b) Distribution of selfidentifiability scores ( I self ), quantifying patient connectome similarity between earlier time points and the chronic outcome ( T 4 ). Significantly lower I self at T 1 compared to T 2 confirms that the rapid functional reorganization of the individual fingerprint within the first three weeks is robust to demographic and injury severity factors ( ∗∗∗ p < 0 . 001, LMM). (c) Median I self within and between seven canonical networks (VIS, visual; SM, somatomotor; DA, dorsal attention; VA, ventral attention; L, limbic; FP, frontoparietal; DMN, default mode) and subcortical structures (SC). (d) Significant relative percentage increase in I self from acute to early sub-acute stages ( T 1 → T 2 ), referenced to the chronic baseline ( T 4 ). Consistent with the main analysis, warmer colors denote networks undergoing rapid functional reconfiguration, notably the ventral attention (VA), limbic (L), and somatomotor (SM) systems ( p < 0 . 05, LMM).](figures/page_027.svg)

**Figure labels:**

- (a)
- (d)
- (c)
- (b)
- Functional networks

(a)

5

10

VIS SM DA VA L FP DMN SC

VIS SM DA VA L FP DMN SC

1 week (T1)

(b)

NWa

(c)

, 0.401

0.30

edges alt.

0.20

0.10

Fraction

VIS

WH+

IH+

Within-Hemisphere (Hyperconnectivity)

20

25

30 0

VIS SM DA VA L FP DMN SC

2

4

VIS SM DA VA L FP DMN SC

6

8

10

VIS SM DA VA L FP DMN SC

![FIG. S7. Robustness of longitudinal structural and functional alterations controlling for age, gender, and lesion size. Functional connectivity matrices were residualized for age and gender (all subjects) and log-transformed lesion volume (stroke patients only) prior to analysis. (a) Group-level matrices displaying the percentage of DTI-derived structurally lesioned edges (upper triangle) and covariate-residualized functionally altered edges (lower triangle; FDR-corrected Mann-Whitney U test, q < 0 . 05) relative to healthy controls across four time points ( T 1 -T 4 ). Consistent with the main findings, structural disconnection patterns remain static, whereas functional alterations evolve dynamically, confirming that the spatial dissociation between fixed structural injury and time-varying functional reorganization is independent of these covariates. (b) Circular plots depict positive (hyperconnectivity, red) and negative (hypoconnectivity, blue) functional alterations at T 1 -T 4 , quantified by Cohen's d effect sizes from the residualized data. (c) Box plots summarize the fraction of altered edges classified as withinhemisphere (WH) or inter-hemispheric (IH), further subdivided into hyperconnectivity ( WH +; IH +) and hypoconnectivity ( WH -; IH -). Early stages ( T 1 -T 2 ) are dominated by within-hemisphere hyperconnectivity, whereas the late sub-acute/chronic phase ( T 3 -T 4 ) shows a relative increase in inter-hemispheric alterations, validating the shift from local to cross-hemispheric plasticity. Data are shown for the longitudinal subset ( n = 22). Network abbreviations: VIS, visual; SM, somatomotor; DA, dorsal attention; VA, ventral attention; L, limbic; FP, frontoparietal; DMN, default mode; SC, subcortical.](figures/img_p028_0.png)

**Figure labels:**

- SM
- VIS SM DA VA L FP DMN SC
- 3 weeks (T2)
- VIS
- 3 months (T3)
- 1 year (T4)
- SC
- OMN
- ds
- Cohen's D
- WH-
- IH-
- WH+
- IH+
- Inter-Hemisphere (Hyperconnectivity)
- • Within-Hemisphere (Hypoconnectivity)
- Inter-Hemisphere (Hypoconnectivity)

15

![FIG. S8. Robustness of multivariate brain-behavior mapping and longitudinal prediction controlling for age, gender, and lesion size. Functional connectivity matrices were residualized for age and gender (all subjects) and logtransformed lesion volume (stroke patients only) prior to analysis. (a) Two-stage predictive framework coupling Partial Least Squares Correlation (PLSC) with Ridge regression. Latent axes of maximal covariance between the residualized functional connectivity (Brain X ) and behavioral scores (Behavior Y ) are identified via PLSC. Significant components generate a connectivity mask for Ridge regression, validated using a leave-one-subject-out (LOSO) approach to predict outcomes at subsequent time points ( T i → T i +1 ... 4 ). (b) Network-level aggregation of the significant PLSC connectivity mask derived at the acute stage ( T 1 ) from the residualized data. Heatmaps display the percentage of significantly negative (blue) and positive (red) edges, highlighting the prominent contribution of higher-order association systems (FP, DMN) and subcortical structures (SC) to the acute behavioral phenotype. (c) LOSO prediction performance ( R 2 ) for individual behavioral domains using the T 1 latent mask. Consistent with the main findings, the model successfully forecasts language, executive, and attention outcomes at follow-up ( T 2 , T 3 , T 4 ), whereas motor and neglect domains show negligible predictability from this functional signature. (d) Prediction accuracy for a global composite behavioral score across longitudinal intervals. Accuracy decays as the temporal gap from T 1 increases but peaks during the late sub-acute transition ( T 3 → T 4 ; R 2 = 0 . 533), confirming that the late-stage stabilization of the brain-behavior relationship is robust to demographic and injury severity factors. (e) Scatter plots correlating actual versus predicted global scores for key intervals reported in panel (d) (e.g., T 1 → T 2 , R 2 = 0 . 484, r = 0 . 698, p < 0 . 001).](figures/page_029.svg)

**Figure labels:**

- (b)
- (a)
- (c)
- (e)
- (d)
- PLSC significant mask (T1)
- T2
- T3
- T4
- Leave-one-subject-out prediction with T1 mask
- Prediction
- (R 2
- )
- Ridge
- Regression
- PLSC
- (covariance)
- Brain
- (X)
- Behavior
- (Y)
- Latent
- mask
- Brain-behavior pipeline
- Composite score prediction
- Residualized
