*[picture on PDF page 1]*

### HHS Public Access

Author manuscript

Cell Rep. Author manuscript; available in PMC 2020 February 20.

Published in final edited form as:

Cell Rep. 2019 September 03; 28(10): 2527-2540.e9. doi:10.1016/j.celrep.2019.07.100.

### Structural Disconnections Explain Brain Network Dysfunction after Stroke

Joseph C. Griffis 1 , Nicholas V. Metcalf 1 , Maurizio Corbetta 1,2,3,4,5,6 , Gordon L. Shulman 1,2,7,*

1 Department of Neurology, Washington University School of Medicine, St. Louis, MO 63110, USA

2 Department of Radiology, Washington University School of Medicine, St. Louis, MO 63110, USA

3 Department of Anatomy and Neurobiology, Washington University School of Medicine, St. Louis, MO 63110, USA

4 Department of Bioengineering, Washington University School of Medicine, St. Louis, MO 63110, USA

5 Department of Neuroscience, University of Padua, Padua, Italy

6 Padua Neuroscience Center, Padua, Italy

7 Lead Contact

### SUMMARY

Stroke causes focal brain lesions that disrupt functional connectivity (FC), a measure of activity synchronization, throughout distributed brain networks. It is often assumed that FC disruptions reflect damage to specific cortical regions. However, an alternative explanation is that they reflect the structural disconnection (SDC) of white matter pathways. Here, we compare these explanations using data from 114 stroke patients. Across multiple analyses, we find that SDC measures outperform focal damage measures, including damage to putative critical cortical regions, for explaining FC disruptions associated with stroke. We also identify a core mode of structure-function covariation that links the severity of interhemispheric SDCs to widespread FC disruptions across patients and that correlates with deficits in multiple behavioral domains. We conclude that a lesion's impact on the structural connectome is what determines its impact on FC and that interhemispheric SDCs may play a particularly important role in mediating FC disruptions after stroke.

### Graphical Abstract

> * Correspondence: gshulman@wustl.edu. AUTHOR CONTRIBUTIONS J.C.G. and G.L.S. designed the analyses and wrote the paper. J.C.G. and N.V.M. performed data processing and analyses. J.C.G., G.L.S., and M.C. edited the paper. G.L.S. and M.C. contributed data and other resources.

> Supplemental Information can be found online at https://doi.org/10.1016/j.celrep.2019.07.100.

> The authors do not declare any competing interests.

### In Brief

Disruptions of brain network function in patients with focal brain lesions are often assumed to reflect damage to critical gray matter regions. Griffis et al. challenge this assumption by showing that network dysfunction primarily reflects the disconnection of white matter pathways, rather than the destruction of gray matter regions.

### INTRODUCTION

Disorders such as stroke cause focal brain lesions but also produce dysfunction in distributed brain networks (Carrera and Tononi, 2014). Functional connectivity (FC), a measure of the correlation between spontaneous activity fluctuations in remote brain regions (Biswal et al., 1995), has been used to identify several brain network abnormalities that predict behavioral deficits after stroke. These include reductions in (1) interhemispheric network integration (He et al., 2007; Carter et al., 2010; Wang et al., 2010; Park et al., 2011; Wu et al., 2011; van Meer et al., 2012; Golestani et al., 2013; Bauer et al., 2014; Lim et al., 2014; New et al., 2015; Siegel et al., 2016b; Tang et al., 2016); (2) ipsilesional network segregation (Baldassarre et al., 2014; Bauer et al., 2014; Eldaief et al., 2017); and (3) network modularity (Gratton et al., 2012; Siegel et al., 2018). An important next step is to determine how these FC abnormalities depend on the properties of the focal lesion (Carrera and Tononi, 2014; Corbetta et al., 2018).

Prior work on this topic has primarily focused on how FC disruptions depend on the FC network properties of damaged gray matter (GM) regions (Eldaief et al., 2017; Gratton et al.,

*[picture on PDF page 2]*

**Figure labels:**
- Region A
- Region B
- Normal Functional Connectivity
- BOLD Activity
- Time
- Structural Connection
- Post-stroke Functional Connectivity
- Lesion-induced Disconnection

2012; Nomura et al., 2010; Ovadia-Caro et al., 2013). Based on this work, it has been proposed that damage to cortical 'connector hub' regions, which interface with multiple FC networks, produces broad disruptions of FC and behavior (Gratton et al., 2012; Warren et al., 2014). However, this explanation ignores the fact that stroke, tumors, and traumatic brain injuries frequently affect the white matter (WM) (Corbetta et al., 2015; Esmaeili et al., 2018; Sharp et al., 2014) and overlooks evidence implicating the structural disconnection (SDC) of WM pathways in complex disorders such as spatial neglect (He et al., 2007; Thiebaut de Schotten et al., 2014) and aphasia (Fridriksson et al., 2013; Yourganov et al., 2016; Griffis et al., 2017a, 2017b).

Structural connectivity (SC) directly and indirectly shapes FC in the healthy brain (Adachi et al., 2012; Goñi et al., 2014; Greicius et al., 2009; van Den Heuvel et al., 2009; Honey et al., 2009). Accordingly, we expected that SDCs fundamentally shape the FC disruptions caused by stroke. This expectation aligns with the general predictions of computational studies that have simulated the effects of lesions on FC (Alstott et al., 2009; Cabral et al., 2012; Saenger et al., 2018; Váša et al., 2015), as well as with empirical reports of FC disruptions associated with callosal resections and traumatic brain injuries (Jilka et al., 2014; Johnston et al., 2008; Roland et al., 2017). Thus, we aimed to test the hypothesis that a lesion's distributed impact on the structural connectome, not its focal impact on critical GM regions, is what determines its impact on FC.

The relationship between SC and FC is an important topic in systems neuroscience (Mišič and Sporns, 2016; Park and Friston, 2013). However, because the structural connectome cannot be experimentally manipulated in human subjects, few studies have empirically examined how direct perturbations of the structural connectome are reflected in the functional connectome (Jilka et al., 2014; Johnston et al., 2008; Roland et al., 2017). Because focal brain lesions can be conceptualized as naturally occurring perturbations of the structural connectome, we also aimed to empirically characterize the relationship between SDC and FC patterns across patients.

We were particularly interested in whether this relationship might be dominated by a few core structure-function profiles. Stroke produces a small set of related FC abnormalities, and behavioral deficits appear similarly low-dimensional such that a few components account for most of the variance in performance within and across behavioral domains (Corbetta et al., 2015). A potential explanation for this is that strokes often disrupt multiple proximal fiber pathways that traverse vascular territories, leading to correlated deficits and network dysfunction (Corbetta et al., 2018). If this is true, then the relationship between SDC and FC patterns should also be low-dimensional, and the FC patterns identified based on their relationships to SDCs should reflect the core FC disruptions that have previously been identified based on their relationships to behavior.

### RESULTS

### Structural Measures

Structural MRI data acquired from 114 sub-acute stroke patients (mean time since stroke = 13.09 days, SD = 4.75 days) (Table S1) were used along with a regional GM parcellation

(359 regions) and a WM structural connectome atlas (70 tracts) to measure each lesion's focal and distributed anatomical impacts at different spatial scales (Figure 1A). For each patient, we defined two measures of focal damage: (1) a voxel-based measure indicating the lesion status (i.e., lesioned versus spared) of each voxel in the brain, including both GM and WM voxels (Figure 1B, voxel-based damage); and (2) a region-based measure quantifying the proportion of voxels in each GM region that overlapped with the lesion (Figure 1B, region-based damage). We also defined two measures of distributed SDCs: (1) a tract-based measure quantifying the proportion of streamlines in each tract that intersected the lesion (Figure 1B, tract-based SDC), and (2) a region-based measure quantifying the proportion of streamlines between each pair of brain regions that intersected the lesion (Figure 1B, regionbased SDC). See STAR Methods for details.

### Disconnection Measures Capture Common Effects of Disparate Lesions

Lesions in different locations can produce similar SDCs due to the spatially distributed nature of WM pathways (Catani et al., 2012). Thus, SDC measures should reveal commonalities among patients with heterogeneous lesions. To illustrate this, we summed the (1) binary voxel-based damage measures and (2) binarized region-based SDC measures across patients to create maps quantifying the number of patients with damage and disconnection at each voxel and connection in the brain (Figure 1C). Notably, the regionbased SDC overlap distribution (Figure 1D, orange histogram) was shifted to the right relative to the voxel-based damage overlap distribution (Figure 1D, blue histogram), indicating that SDC overlaps (max = 47; see dashed orange line in Figure 1D) were much more frequent than lesion overlaps (max = 18; see dashed blue line in Figure 1D) across patients. Thus, SDC measures can reveal common structural disruptions across patients with heterogeneous lesions.

### Functional Connectivity Measures

Resting-state fMRI data acquired from 114 sub-acute stroke patients and 24 demographically matched controls (Table S1) were used to measure FC between 324 cortical regions associated with different brain networks (Figures S2A-S2C). We defined 12 network-level summary measures to capture core FC disruptions associated with stroke, namely reductions in (1) interhemispheric network integration, (2) ipsilesional network segregation, and (3) network modularity. For each patient, we extracted the mean interhemispheric FC values for nine bilateral cortical networks (Figure S2D, left) and averaged these values to summarize interhemispheric within-network integration across the cortex (Figure S2D, left inset). We also extracted the mean FC values between the ipsilesional dorsal attention (DAN) and default mode (DMN) networks to summarize network segregation in the lesioned hemisphere (Figure S2D, middle). Finally, we averaged modularity estimates for a priori network partitions across multiple edge density thresholds to summarize the overall network structure (Figure S2D, right; mean shown in inset). These FC measures were used as dependent variables in subsequent analyses.

### Functional Connectivity Disruptions in Sub-acute Stroke

The mean FC matrices for patients and controls had similar topographies (Figure S2B; r = 0.96, p < 0.001). Subtracting the patient matrix from the control matrix revealed magnitude differences that were often in opposite directions for connections with positive versus negative values in the mean control matrix (Figure S2C; r = 0.42, p < 0.001), consistent with reduced within-network integration and between-network segregation after stroke. As expected, patients showed marked abnormalities in network-level summary measures relative to controls (Figure S2D), and this was not attributable to differences in total FC between groups (STAR Methods).

### Total Disconnection Is Superior to Cortical Hub Damage for Explaining Reduced Modularity

Reductions in modularity have been associated with damage to cortical regions with diverse between-network FC ('connector hubs') but not with damage to regions with diverse withinnetwork FC ('provincial hubs') (Gratton et al., 2012). Connector hubs have therefore been proposed as critical GM regions that produce widespread dysfunction when damaged (Warren et al., 2014). We aimed to replicate this effect in our data and compare its explanatory power to that of a simple summary measure of SDC severity, defined for each patient as the total number of region-based SDCs caused by their lesion (i.e., total SDC). For each patient, we also defined measures of FC connector and provincial hub damage as weighted means of the control-derived participation coefficient (PC) and within-module degree (WMD) values for damaged cortical regions as in the study by Gratton et al. (2012) (Figure 2A).

Replicating the connector damage effect, a 2-predictor multiple regression model, identified a significant effect of connector hub (Figure 2B; model 1, PC Dmg) but not provincial hub (Figure 2B; model 1, WMD Dmg) damage on modularity (see also Figure 2C, left). However, a 3-predictor model that included total SDC explained significantly more variance (F 1,110  = 22.6, p < 0.001) and featured total SDC as the only significant predictor (Figure 2B, model 2). This model was not improved by adding lesion volume, and total SDC remained the only significant predictor after lesion volume was added (Figure 2B, model 3). Correlational analyses confirmed that modularity was more strongly related to SDC than to connector hub damage (Figure 2C, left), even when adjusting for lesion volume (Figure 2C, right). Thus, the loss of modularity after stroke is better explained by SDC severity than by damage to cortical connector hub regions.

### Disconnection Provides the Best Anatomical Account of Network Dysfunction after Stroke

We next compared the ability of multivariate damage and SDC information to explain each network-level measure of FC disruption. For each FC measure (see Figure S2D), we fit four separate partial least-squares regression (PLSR) models by using the different structural measures (see Figure 1B) as predictors. The optimal number of PLS components for each model was determined by jackknife cross-validation, and confidence intervals (CIs) for the model fits were obtained by bootstrap resampling (1,000 bootstraps). To identify the best model of each FC measure, we compared Akaike information criterion (AIC) weights among models. AIC weights can be interpreted as conditional probabilities that a model is the best of a set given the data and the set of models (Wagenmakers and Farrell, 2004).

Across FC measures, the SDC models consistently explained more variance than the damage models (Figure 3A). Although SDC models tended to use more PLS components than damage models (Figure 3B), subsequent comparisons using AIC weights accounted for differences in model complexity, and similar results were obtained when only a single component was used for all models (Figure S3). Comparisons of AIC weights revealed that nine of the best models were region-based SDC models and the remaining three were tractbased SDC models (Figure 3C). SDC model performance could not be attributed to lesion volume effects, as the damage measures contained the most information about lesion volume (STAR Methods). Thus, SDC measures (particularly region-based SDC) consistently outperformed region-level and voxel-level damage measures for explaining core FC disruptions associated with stroke.

### Disconnection Patterns Associated with Core FC Disruptions

Prior work indicates that FC disruptions involving different networks are correlated across patients (Corbetta et al., 2018). We observed moderate-to-strong correlations among the different FC measures (bottom triangle in Figure 4A) that were reflected in the correlations of the unthresholded PLSR weights from the region-based SDC models (top triangle in Figure 4A). Consistent with the proposal that correlations among FC disruptions reflect the simultaneous disruption of proximal WM pathways within vascular territories (Corbetta et al., 2018), FC disruptions and corresponding SDC weight patterns were highly correlated among networks with dense connections traversing the middle cerebral artery (MCA) territory (Figure 4A, networks other than the visual network [VIS]; see Figure S1D) but were weakly-to-negatively correlated between these networks and other networks (Figure 4A, VIS).

To characterize the most salient SDCs associated with each core FC disruption, we extracted the region-based SDC PLSR model weights with significant 99% CIs (1,000 bootstraps) and positive signs (signs were flipped so that positive weights predicted more severe FC disruptions in all models) from the models of mean interhemispheric within-network FC, ipsilesional DAN-DMN FC, and network modularity. Mean model weights were larger for interhemispheric SDCs than for intrahemispheric SDCs (Figure 4B, compare orange and blue dots), and top weights corresponded overwhelmingly to interhemispheric SDCs within the MCA territory (Figure 4B, dots above the dashed lines; Figure 4C; see also Figure S4). The top weights also included several intrahemispheric SDCs involving right thalamocortical, fronto-parietal and fronto-temporal, and/or left frontal, frontostriatal, and frontothalamic pathways (Figure 4C; see also Figure S4). SDCs and/or lesions involving the cerebellum and brainstem (and to a lesser extent, VIS) were associated with less severe FC disruptions (Figures S4 and S5), consistent with the interpretation that the correlation among FC disruptions reflects co-occurring SDCs of diverse commissural and association pathways in the MCA territory.

### Low-Dimensional Covariance of Disconnection and Functional Connectivity Patterns

The results reported above support the conclusion that SDCs underlie core FC disruptions associated with stroke. However, because they were originally identified based on their relationships to behavior (rather than to SDCs), these core FC disruptions may not be the only or even the primary FC consequences of SDCs. To characterize the broader relationships between SDC and FC patterns across patients, we applied a data-driven partial least-squares correlation (PLSC) analysis to the full connection-level (i.e., un-summarized) SDC and FC matrices from the patient sample. PLSC performs a linear decomposition of the cross-covariance matrix to obtain a set of orthogonal latent variables (LVs)-linear combinations of the original structural and functional connections-that maximally explain the covariance between the SDC and FC datasets. The multivariate SDC and FC topographies linked by each LV are reflected in connection-level loadings (i.e., weights), and patient-level scores for each LV are obtained by multiplying the original data matrices by the corresponding loading vectors.

Consistent with the expectation that SDC and FC patterns would exhibit a low-dimensional relationship, 87% of the covariance between the full SDC and FC datasets was explained by the first 10 LVs (Figure 5A). Permutation testing (1,000 permutations) revealed that the first two LVs (i.e., LV1 and LV2) each explained significantly more covariance (45% and 21%, respectively) than expected under the empirical null (false discovery rate [FDR], p = 0.005). For each significant LV, we identified significant loadings (i.e., individual connections) as those with absolute bootstrap (1,000 bootstraps) signal-to-noise ratios (BSRs) greater than 2.5. Although both LV1 and LV2 accounted for a significant portion of the total covariance, the loadings on LV2 did not achieve significance (see Figure S6 for characterization of LV2). We therefore focused on characterizing LV1. Mean LV1 SDC (t 112  = 1.0, p = 0.34) and FC scores (t 112  = 0.62, p =0.53) did not differ significantly between patients with left versus right hemispheric lesions, indicating that LV1 was similarly expressed in both patient groups (see Figure S7 for separate analyses of each group).

At the patient level, expression of the LV1 SDC pattern was reliably associated with the expression of the LV1 FC pattern, as indicated by the correlation of SDC and FC scores across patients (Figure 5B; 99% CI = 0.73-0.78, 1,000 bootstraps). In terms of loading topographies, significant SDC loadings had only positive signs and corresponded to interhemispheric SDCs within and between networks (Figures 5C and 5D, see LV1 SDC). Significant FC loadings with positive signs consisted of interhemispheric and intrahemispheric functional connections that were almost exclusively between different networks (Figure 5C, LV1 FC; Figure 5D, right panels), whereas loadings with negative signs corresponded overwhelmingly to interhemispheric functional connections both within and between networks (Figure 5C, LV1 FC; Figure 5D, middle panel). These topographies are summarized in Figure 5D and show that the expression of the inter-hemispheric SDC+ pattern (Figure 5D, see SDC+) was associated with stronger FC between networks (i.e., reducing segregation; Figure 5D, see FC+) and weaker interhemispheric FC that was most pronounced within networks (i.e., reducing integration; Figure 5D, see FC-).

### LV1 Underlies Core Functional Connectivity Disruptions and Correlates with Behavior

The FC patterns associated with LV1 resembled two core FC disruptions associated with stroke: reductions of within-network interhemispheric FC and increases in between-network FC (Figures 6C and 6D). This suggests that the core FC disruptions associated with stroke are, in fact, primary consequences of SDCs. We confirmed this correspondence by correlating the patient LV1 scores with the a priori FC measures (Figure 6A, top row). Patient FC scores for LV1 showed an extremely strong negative correlation with mean interhemispheric within-network FC and moderately strong correlations with the other measures. Similar, but weaker, relationships were observed for LV1 SDC scores (Figure 6A, bottom row). Thus, core FC disruptions previously identified based on their relationships to behavior appear to largely reflect a single underlying FC pattern associated with interhemispheric SDCs.

To confirm that LV1 captured a behaviorally relevant structure-function relationship, we correlated patient-level LV1 scores with performance scores obtained from PCAs of multiple tests in the language, attention, visual memory, spatial memory, and motor domains (Corbetta et al., 2015). LV1 expression significantly correlated with behavioral impairments in multiple domains (Figure 6B, left), even when adjusting for lesion volume (Figure 6B, right). Together with the results described above, these results support the view that the low dimensionality of behavioral and brain dysfunction after stroke reflects correlated SDCs resulting from lesions within arterial territories.

### Disconnection Topographies Are Partially Reflected in Functional Connectivity Patterns

The SC and FC patterns that covary across healthy individuals feature divergent topographies, suggesting that they primarily reflect indirect network-level relationships (Mišić et al., 2016). However, normal inter-individual variability in SC measures might conceivably be dominated by relatively minor variations around a conserved macroscale architecture that underlies stable group-level FC phenomena like resting-state networks (Greicius et al., 2009; van Den Heuvel et al., 2009). Because SDCs are direct perturbations of this core architecture, we expected that their topographies would be at least partially reflected in linked FC patterns.

We assessed the topographic similarity of the SDC and FC components of LV1 by correlating the unthresholded loadings common to both components (Figure 7A). This revealed a weak but significant negative relationship between SDC and FC loadings (Figure 7B). Because the degree of structure-function correspondence might be expected to differ among connections with distinct network and/or hemispheric attributes, we separately computed the correlations between the SDC and FC loadings for different hemispheric and network connection categories. Although considerable correspondence was observed for within-network connections, very little was observed for between-network connections (Figure 7C). This finding was not driven by regional damage, as similar results were obtained in patients with little-to-no cortical damage (Figure S8). Thus, direct perturbations of the structural connectome are directly reflected by changes in the FC of disconnected nodes, but this effect appears to be primarily driven by within-network SDCs.

### DISCUSSION

Stroke disrupts the macroscale functional connectome (Grefkes and Fink, 2014; Baldassarre et al., 2016a; Carrera and Tononi, 2014; Fox, 2018). A complete understanding of stroke pathophysiology must link these functional disruptions back to the underlying structural lesion. Here, we advanced this goal by highlighting a key role of SDCs in determining the effects of stroke on brain network function. Specifically, we found that core FC signatures of stroke (1) are better explained by SDCs than by focal damage, and (2) largely reflect a single latent FC pattern that covaries with the severity of inter-hemispheric SDCs and partially reflects the underlying SDC topography.

### Anatomical Determinants of Functional Connectivity Disruptions after Stroke

We tested the hypothesis that SDCs are the primary anatomical factor underlying FC disruptions after stroke. Across multiple analyses, SDC measures outperformed focal damage measures for explaining core FC disruptions (Figures 2 and 3; Figure S3). Regionbased SDC measures typically performed best, but the comparable performance of the tractbased SDC measures is noteworthy given their macroscale resolution and their independence from the regional parcellation scheme. Voxel-based damage models, which largely emphasized WM damage in their weight maps (Figure S5), also outperformed region-based damage models that only considered GM damage (Figure 3A).

These results support the conclusion that FC disruptions primarily reflect SDCs and argue against the notion that most focal lesions selectively disrupt function within damaged functional networks (Nomura et al., 2010; Warren et al., 2014) while damage to cortical connector hubs causes broad network dysfunction (Gratton et al., 2012; Warren et al., 2014). Although this account has been highly influential, it has been challenged by recent evidence indicating that (1) lesions can disrupt FC between undamaged networks while sparing FC within damaged networks (Eldaief et al., 2017); (2) damage to 'connector' regions may not be particularly important for predicting FC disruptions in multivariate GM damage models (Yuan et al., 2017); and (3) task-evoked network disruptions can result from lesions that minimally overlap with constituent cortical regions but that cause extensive within-network SDCs (Griffis et al., 2017a). Although we directly replicated the effect of connector hub damage on modularity, the addition of SDC information increased the variance explained by a factor of 2.5 (Figure 2B), and the effect of connector hub damage was significantly weaker than the effect of total SDC even when accounting for lesion size (Figure 2C). More broadly, our PLSR results strongly argue against GM damage as a primary source of FC disruptions in patients with focal brain lesions, as the region-based damage models were consistently the worst-performing models tested (Figure 3; Figure S3).

The finding that SDCs can largely explain FC disruptions after stroke complements prior work on the role of SDCs in determining the cognitive and behavioral consequences of stroke (Catani et al., 2012; Chechlacz et al., 2013; Thiebaut de Schotten et al., 2014; Corbetta et al., 2015; Kuceyeski et al., 2015, 2016a; Yourganov et al., 2016; Griffis et al., 2017b, 2017a; Marebwa et al., 2017). Speculatively, SDC-behavior relationships may be partially mediated by the large-scale functional disruptions precipitated by SDCs. Future studies using path modeling or mediation analyses are an important next step toward understanding the complete relationship linking focal lesions to functional disruptions and behavioral impairments.

Our results also confirm a general prediction of previous computational modeling worknamely, that a lesion's impact on FC is strongly influenced by its expected impact on the structural connectome (Alstott et al., 2009; Cabral et al., 2012; Saenger et al., 2018; Váša et al., 2015). However, most computational studies have simulated SDCs by region-wise or random connection removal, and this makes it difficult to compare their specific results to results obtained from analyses of real patient data. For example, region-wise connection removal cannot account for WM damage that spares a region and/or a subset of its connections, and random connection removal cannot account for correlations among SDCs within the same vascular territories or fiber bundles. As our approach to measuring expected SDCs does not have these limitations, the incorporation of similar approaches into future modeling studies might enable more realistic simulations and improve the generalizability of specific findings.

### Links between Structural Disconnection, Functional Connectivity, and Behavior

We empirically characterized how perturbations of the structural connectome are reflected in whole-brain FC patterns. Our analyses revealed a low-dimensional relationship between SDC and FC, such that two-thirds of the SDC-FC covariance could be attributed to two LVs (Figure 5A). Principal-component analyses (PCAs) indicated that this result did not simply reflect an intrinsic low dimensionality of the lesion, SDC, or FC data (Figure S9). Although this does not imply that more specific SDC-FC relationships do not exist, it indicates that any such relationships account for a minority of the total covariance.

This analysis was partially motivated by the consideration that the FC patterns that maximally covary with SDCs might be distinct from the core FC disruptions reported in the literature. However, the FC pattern captured by LV1 clearly reflected core FC disruptions (Figures 5 and 6A) that have been identified based on their relationships to behavior and deviations from controls (for review, see Corbetta et al., 2018). Accordingly, patient-level expression of LV1 correlated with behavioral impairments (Figure 6B). This was particularly pronounced for attention, spatial memory, and motor domains, consistent with the notion that cortico-cortical FC is critical for higher cognitive functions (Corbetta et al., 2018) and with previous reports of corrrelated motor and attention deficits after stroke (Baldassarre et al., 2016b). Because the FC profile associated with LV1 was identified based on its relationship to SDCs rather than behavior, we speculate that it contains an aggregate of different behaviorally relevant FC topographies that covary with partially overlapping sets of interhemispheric SDCs. Consistent with this interpretation, the LV1 FC pattern qualitatively resembles the FC pattern that was found to predict multi-domain behavioral deficits in a previous analysis of FC data from this sample (Siegel et al., 2016b).

The relationships shown in Figure 6B are consistent with evidence indicating that behaviorally relevant FC abnormalities are correlated and tend to vary in topography and severity but not form (Corbetta et al., 2018). The weakening of interhemispheric FC is a common signature of impairments in multiple behavioral domains, and domain-specific deficits are associated with specific topographies of weakened connections (Carter et al., 2010; Park et al., 2011; Tang et al., 2016; Baldassarre et al., 2016b). Our results advance a mechanistic explanation for the low dimensionality of behavioral and FC disruptions after stroke. Specifically, they suggest that strokes within the MCA territory disrupt interhemispheric SC both within and between cortical networks, producing both direct and network-level effects on FC that lead to a breakdown in the balance of network integration and segregation.

Why might interhemispheric SDCs be particularly important for determining the functional consequences of focal brain lesions? One explanation is that stable interhemispheric integration is a fundamental component of large-scale FC organization (Shen et al., 2015a, 2015b) that shapes broader aspects of FC. This explanation is consistent with modeling results indicating that the interaction between callosal SC and physiological factors may partially mediate FC between other regions (Messé et al., 2014) and with empirical data indicating that interhemispheric SDCs both reduce inter-hemispheric FC and increase intrahemispheric FC in non-human primates (O'Reilly et al., 2013). Nonetheless, this is an open question that should be addressed in detail by future work.

The observed low-dimensional relationship between SDC and FC contrasts sharply with recent reports of high-dimensional covariance between SC and FC patterns in healthy individuals. For example, a recent PLSC study reported that 5 LVs explained only 22.6% of the covariance between SC and FC patterns in a sample of 156 healthy participants (Mišić et al., 2016). In contrast, the first 5 LVs identified by our PLSC analysis together explained over 80% of the structure-function covariance across patients (Figure 5A). One explanation for this stark difference is that normal variability in MRI measures of SC may reflect relatively minor but not inconsequential variations around an otherwise conserved structural scaffold that shapes the core FC topographies identified by group-level analyses, whereas variability in SDC measures reflects major differences in the integrity of this core scaffold. This explanation is consistent with the fact that the topographies of the SC and FC components of the LVs identified by Mišić et al. (2016) were discordant, whereas the SDC and FC components of LV1 identified by our analysis exhibited significant topographic similarity that was especially pronounced for within-network connections (Figure 7). Even so, the correspondence between the linked SDC and FC patterns was still relatively weak, and many of the most stable SDC loadings corresponded to connection types that showed weak topographic similarity (e.g., see interhemispheric between-network in Figures 5C and 7C). This suggests that much of the covariance between SDC and FC may reflect indirect SDC effects that arise by propagation along serial connections in polysynaptic pathways (Carter et al., 2012; Lu et al., 2011) or through large-scale network dynamics (Adachi et al., 2012; Alstott et al., 2009; Mišić et al., 2016) arising from the sudden loss of diverse afferent and/or efferent connections throughout distributed brain networks. Future studies should aim to characterize the nature of putative indirect SDC effects.

### Considerations for Studying Structure-Function Relationships in the Lesioned Brain

The current study featured several methodological advantages over previous work on this topic. By explicitly incorporating SDC measures, we were able to account for the effects of interest beyond what was possible using focal damage measures. This contrasts with the historical focus on GM damage by studies in this domain (Gratton et al., 2012; Nomura et al., 2010; Ovadia-Caro et al., 2013; Yuan et al., 2017), which ignores potentially relevant information about WM damage (e.g., compare voxel and regional damage model fits in Figure 3) and may lead to the mis-localization of WM effects into nearby GM regions

### Limitations

(Figure S5). The latter might occur when relevant variables (i.e., WM voxels) are not measured, but proxy information is available from correlated measured variables (i.e., GM regions). Hypothetically, this could also lead to distorted SDC weight topographies if outcomes were largely driven by GM damage. We accounted for this possibility by performing an additional PLSR analysis that included both region-based damage and SDC measures as predictors (see STAR Methods). Although the SDC weight topographies were unchanged, the damage weight topographies were substantially altered when SDCs were simultaneously modeled. This emphasizes the importance of accounting for potentially relevant lesion effects when drawing conclusions about critical locations or topographies in lesion analyses.

We also used data collected from a relatively large sample of first-ever stroke patients in the sub-acute recovery phase. Most previous studies utilized data obtained from relatively small samples of patients with diverse lesion etiologies (e.g., stroke, traumatic brain injury, and tumor resection) and/or at varying stages of recovery (Nomura et al., 2010; Gratton et al., 2012; Eldaief et al., 2017; Yuan et al., 2017). Larger patient samples increase power and stabilize effect estimates (Poldrack, 2012; Yarkoni, 2009), but the importance of studying patients with similar lesion etiologies at the same phase of recovery warrants further discussion.

All lesions are not created equal. The pathological origin of a given lesion contributes to its physiological and behavioral consequences (Anderson et al., 1990). For example, slowgrowing lesions (e.g., tumors) tend to produce less severe cognitive and behavioral deficits than sudden-onset lesions (e.g., ischemic stroke). This may reflect differences in the brain's ability to compensate for lesions that develop on different time scales (Des murget et al., 2007). Lesions resulting from specific pathologies may also exhibit spatial biases-medial prefrontal regions are frequently affected by low-grade glioma (Duffau and Capelle, 2004) but are infrequently affected by stroke (Corbetta et al., 2015; Sperber and Karnath, 2015). Furthermore, the behavioral and physiological consequences of brain lesions are not static but evolve throughout the course of recovery (Corbetta et al., 2005; Heiss et al., 1999; Ramsey et al., 2016; Rehme et al., 2011; Saur et al., 2006). Therefore, it is important to utilize data from patients with similar lesion etiologies and in the same recovery phase to minimize the risk of latent confounders in lesion analyses.

Diffusion MRI data were not available for this sample, and SDC measures were defined by intersecting patient lesions with a structural connectome atlas (see STAR Methods). Similar atlas-based approaches have been used by other recent lesion studies (Foulon et al., 2018; Griffis et al., 2017a; Hope et al., 2018; Kuceyeski et al., 2015, 2016a, 2016b; Pustina et al., 2017a), and analogous strategies are often used to study SCFC relationships in animal models (Adachi et al., 2012; Grandjean et al., 2017; Grayson et al., 2016; Shen et al., 2015b). These approaches assume similar approximations of individual structural connectomes by the atlas and cannot account for interindividual variability in un-damaged fiber pathways (Forkel and Catani, 2018; Forkel et al., 2014), but they also offer protection against potential biases arising from inter-individual differences in diffusion MRI data quality, reconstruction, etc. and provide an intuitive means of estimating SDCs relative to a common reference that can be used across independent samples and/or studies. Furthermore, the structural connectome atlas was based on very high-quality data (i.e., 90 direction highangular resolution diffusion imaging) from a very large sample of participants (i.e., N = 842) and was expert-vetted to reduce the likelihood of false-positive connections (Yeh et al., 2018). Thus, although direct patient SDC measures would be ideal, our results show that atlas-based measures provide important information about FC beyond what is present in focal damage measures.

Similarly, template-based areal parcellations may not provide comparable approximations of areal boundaries for all participants. Previous analyses of data from this sample have shown that the parcellation delineates largely homogeneous functional regions in both patients and controls (Siegel et al., 2018), but inter-individual variability in areal boundaries and/or network topographies could still influence our measures (Braga and Buck-ner, 2017; Gordon et al., 2017; Gratton et al., 2018; Marek et al., 2018). However, template-based parcellation approaches have advantages that are analogous to those described for template-based SDC approaches. Furthermore, the large amount of necessary data (Gordon et al., 2017) and the potential for distortions by lesion and/or hemodynamic factors (Siegel et al., 2017) make individual functional parcellations infeasible in sub-acute stroke patients.

Previous studies have successfully used expected SDC measures to model behavioral impairments (Foulon et al., 2018; Fridriksson et al., 2013; Griffis et al., 2017b; Kuceyeski et al., 2015, 2016b) and changes in brain structure (Foulon et al., 2018; Kuceyeski et al., 2014), but SDC measures may not always provide unique information (Hope et al., 2018). The utility of SDC measures will likely depend on several factors, including the degree to which the outcome of interest depends on SDCs versus focal damage, the quality of the SDC measures, and the lesion characteristics of the patient sample. Because SDC information is implicit in the lesion, it is likely that voxel-based lesion measures will provide similar information as SDC measures when lesion coverage and diversity is sufficiently high to recover the implicit SDCs, although this would likely require huge samples with diverse lesions and dense coverage throughout the brain (e.g., N = 818 in Hope et al., 2018). Even in scenarios where SDC and damage information enable similar prediction, we consider the inclusion of SDC information useful from a neuroscientific perspective.

### STAR ★ METHODS

### LEAD CONTACT AND MATERIALS AVAILABILITY

Requests for additional information or resources should be directed to the Lead Contact, Gordon Shulman (gshulman@wustl.edu).

### EXPERIMENTAL MODEL AND SUBJECT DETAILS

Participant informationPatients and controls provided written informed consent prior to participation in the study. Study procedures were performed in accordance with the Declaration of Helsinki ethical principles and approved by the Institutional Review Board at Washington University in St. Louis. The complete data collection protocol is described in full detail in our previous publication (Corbetta et al., 2015). Data from 132 first-time stroke patients who presented with clinical evidence of cognitive and/or behavioral impairment and data from 33 demographically matched healthy controls were considered for inclusion in the study. Data from 114 patients and 24 controls met quality control criteria (described below) and were included in the study. Participant demographics are shown in Table S1.

### METHOD DETAILS

Neuroimaging data collectionNeuroimaging data were collected using a Siemens 3T Tim-Trio scanner at the Washington University School of Medicine with a 12-channel head coil, and are fully described elsewhere (Corbetta et al., 2015; Siegel et al., 2016b). Sagittal T1-weighted MP-RAGE (TR = 1950 msec; TE = 2.26 msec, flip angle = 90 degrees; voxel dimensions = 1.0×1.0×1.0 mm), transverse T2-weighted turbo spin-echo (TR = 2500 msec; TE = 43 msec; voxel dimensions = 1×1×1), and sagittal T2-weighted FLAIR (TR = 750 msec; TE = 32 msec; voxel dimensions = 1.5×1.5×1.5 mm) structural scans were obtained along with gradient echo EPI (TR = 2000 msec; TE = 2 msec; 32 contiguous slices; 4×4 mm in-plane resolution) resting-state functional MRI scans. During the fMRI scans, participants were instructed to fixate on a small white centrally-located fixation cross presented against a black background on a screen at the back of the magnet bore. An Eyelink 1000 eye-tracking system (SR Research) was used to monitor when participant's eyes were opened/closed during each run. Between six and eight resting-state scans (128 volumes each) were obtained from each participant (~30 minutes total).

Lesion identificationLesions were manually segmented on each patient's structural MRI scans using the Analyze software package (Robb and Hanson, 1991). The T1weighted, T2-weighted, and T2-FLAIR scans were used in conjunction to ensure complete lesion delineation. If present, surrounding vasogenic edema was included in the lesion definition for all patients. All segmentations were reviewed by two board certified neurologists (Maurizio Corbetta and Alexandre Carter), and were reviewed a second time by MC. The final segmentations were used as binary lesion masks for subsequent processing and analysis steps. Lesion masks were transformed to MNI atlas space using a combination of linear transformations and non-linear warps and were resampled to have isotropic voxel resolution.

Behavioral measuresParticipants performed a behavioral battery consisting of multiple assessments within motor, language, attention, verbal memory, spatial memory, and visual domains. Principal components analyses (PCA) were used to decompose the behavioral data from each domain. Detailed descriptions of the behavioral testing and PCA analyses can be found in the Supplemental Material for Corbetta et al. (2015) and Siegel et al., (2016b). Analogously to other previous work (Ramsey et al., 2017; Siegel et al., 2016b, 2018), the first PCs from each behavioral domain (with the exception of vision) were considered as domain scores of interest and were used in analyses that related imaging measures to behavior (Figure 6B). Of the 114 patients that were included in the main analyses, 108 had data for the language domain, 93 had data for the attention domain, 101 had data for the motor domain, and 84 had data for the verbal and spatial memory domains.

MRI data processingFunctional MRI data pre-processing consisted of slice-timing correction using sinc interpolation, correction of inter-slice intensity differences resulting from interleaved acquisition, normalization of whole-brain intensity values to a mode of 1000, correction for distortion via synthetic field map estimation, and within- and betweenscan spatial re-alignment. BOLD data were re-aligned, co-registered to the corresponding structural images, normalized to atlas space, and resampled to 3mm cubic voxel resolution using a combination of linear transformations and non-linear warps. Prior to estimating FC, additional processing steps were applied to account for non-neural sources of signal variance. Confounds related to head motion, global signal fluctuations, and non-gray matter signal compartments were removed from the data by regression of the six head motion parameters obtained from rigid body correction, along with the global GM signal and the CSF and white matter signals extracted from FreeSurfer tissue segmentations (Dale et al., 1999). BOLD data were band-pass filtered (0.009 < f < 0.08 Hz) to retain low-frequency fluctuations. A frame was censored if it exceeded a 0.5 mm framewise displacement threshold, and the succeeding frame was also censored to further reduce confounds related to motion (Power et al., 2014). The first four frames of each run were discarded to allow for the scanner to achieve steady-state magnetization.

Cortical surface generation and subsequent fMRI data processing generally followed previously published minimal preprocessing procedures (Glasser et al., 2013), although some modifications were required to accommodate lesioned brains (Siegel et al., 2016b, 2017). FreeSurfer was used to automatically obtain anatomical surfaces from the T1weighted structural scans (Dale et al., 1999; Fischl et al., 1999), and the resulting segmentations were visually inspected to ensure accuracy. Data from patients with failed registrations and/or segmentations were modified by replacing the values of lesioned voxels with normal values from the structural atlas prior to running the registration and segmentation procedures, and the modified voxels were masked out after running the procedures (Siegel et al., 2017). Each hemisphere was resampled to 164,000 vertices, and the two hemispheres were registered to each other (Van Essen et al., 2001). The data were then down-sampled to 32,000 vertices per hemisphere. Ribbon-constrained sampling in Connectome Workbench was used to sample functional MRI volumes to each participant's individual surface, and voxels with coefficients of variation > 0.5 standard deviations above the mean of all voxels within a 5 mm sigma Gaussian neighborhood were excluded from volume to surface mapping (Glasser et al., 2013).

Participants were excluded if they had less than 180 usable frames of resting-state data after applying quality controls, and this resulted in the exclusion of 18 patients and 9 controls. The remaining 114 patients and 24 controls who had sufficient FC data were included in the primary analyses.

Parcels and network assignmentsWe used the Gordon333 cortical parcellation and network community assignments to obtain region-level and network-level measures of functional connectivity. This parcellation is based on functional connectivity boundary mapping and InfoMap community detection analyses of resting-state fMRI data from 120 healthy individuals (Gordon et al., 2016), and consists of 333 cortical regions associated with 13 large-scale networks. Previous studies involving the current dataset excluded 9

regions for having very low numbers of vertices, and so they were also excluded here for consistency (Siegel et al., 2016b, 2018). The remaining 324 surface-based cortical regions were used for subsequent surface-based estimation of functional connectivity.

In addition to the 324 cortical regions, we also defined a set of 35 sub-cortical and cerebellar regions to allow for the complete quantification of damage and disconnection throughout the brain. This set of regions consisted of 34 parcels from the automatic anatomical labeling (AAL) atlas (Tzourio-Mazoyer et al., 2002) that corresponded to different portions of the thalamus, basal ganglia, and cerebellum, and also included 1 region from the HarvardOxford Subcortical Atlas that corresponded to the brainstem. The full set of 359 regions is shown in Figure S1 and was used for subsequent estimation of regional damage and structural disconnection. The cortical regions were dilated by 2mm using the 'dilate' command in DSI_studio to improve the sensitivity of subsequent structural connectivity analyses (van Den Heuvel et al., 2009; Wilson et al., 2011) and to allow for a slightly relaxed threshold for determining cortical damage (Pustina et al., 2018).

Functional connectivity estimationRegion-wise functional connectivity matrices were constructed by correlating the average (i.e., across all within-region vertices) nuisanceregressed BOLD timeseries of each surface region with the average nuisance-regressed BOLD timeseries of every other region and applying the Fisher z-transformation to the resulting linear correlation values. For each patient, vertices that fell within the boundaries of the lesion were masked out, and regions with less than 60 vertices remaining after excluding lesioned vertices were completely excluded by setting the values to NaN, analogously to previous reports (Siegel et al., 2016b; Siegel et al., 2018). We note that analyses that were performed without removing lesioned vertices produced very similar results for all analyses (not shown), likely owing to the relatively low frequency of cortical lesions in our sample (Figure 1C; Figure S8A).

Template structural connectomeWe used a publicly available diffusion MRI streamline tractography atlas to create a template structural connectome. The tractography atlas was constructed using data from 842 Human Connectome Project participants (Yeh et al., 2018), and atlas data were accessed under the WU-Minn HCP open access data use term. To summarize the atlas construction, Yeh et al. (2018) reconstructed the high-angular resolution diffusion MRI data (b-values: 1000, 2000, and 3000 s/mm2; diffusion sampling directions: 90, 90, and 90; in-plane resolution: 1.25mm) from 842 Human Connectome Project participants in MNI space using Q-space diffeomorphic reconstruction (Yeh and Tseng, 2011), averaged the resulting spin distribution functions (SDFs) to obtain populationlevel streamline trajectories, and performed deterministic fiber tracking (Yeh et al., 2013b) to extract 550,000 streamline trajectories that were then vetted and labeled by a team of neuroanatomists (for detailed descriptions of the procedures, see Yeh et al., 2018). Thus, the tractography atlas consisted of expert-vetted end-to-end streamline trajectories in MNI space that were each associated with 1 of 66 neuroanatomically defined fiber bundles (e.g., superior longitudinal fasciculus, corpus callosum, etc.) corresponding to commissural, association, projection, brainstem, and cerebellar pathways (cranial nerves were not included). Because we expected that different segments of the corpus callosum might show different relationships to FC in the tract disconnection analyses, we split the corpus callosum into 5 segments based on the FreesurferSeg ROIs included with DSI_studio, resulting in a total of 70 tracts.

We used command line utilities provided in the DSI_studio software package to define the normative region-based structural connectome template based on the tractography atlas (Figure S1). To define the region-based structural connectome, we first combined the labeled streamline bundles from the structural connectome atlas (e.g., short-range U-fibers, callosal projections, etc.) into a single aggregate .trk file, and then extracted all streamlines that bilaterally terminated (i.e., began and ended) within any pair of the 359 volume-based regions. This resulted in a 359×359 structural connectivity adjacency matrix A S  where each entry A S ij indexed the number of streamlines connecting regions i and region j. Due to the close proximity of ventral visual and dorsal cerebellar regions, a small number of dorsal cerebellar streamlines were captured by the dilated visual regions. Therefore, we removed any connections between visual areas and the cerebellum.

### QUANTIFICATION AND STATISTICAL ANALYSIS

All quantification and statistical analyses were performed in MATLAB version 2015a that included the Statistics and Machine Learning Toolbox. Brain visualizations were created using the Connectome Workbench, MRIcroGL and SurfIce software packages. The matlab_nifti toolbox was used to convert raw voxel data in the nifti file format for visualization in MRIcroGL. The GRETNA toolbox was used to convert raw connection vectors/matrices into .edge and .node files for brain visualization in SurfIce.

Functional connectivity measuresFunctional connectivity matrices were averaged from each group to create the group-averaged functional connectivity matrices shown in Figure S2B. The mean matrix from the control group was subtracted from the mean matrix from the patient group to create a difference matrix (Figure S2C). Linear correlations between the upper triangles of the group-averaged and difference matrices were used to assess the similarity of mean functional connectivity topographies with each other and with the difference matrix.

We defined 12 a priori measures of network dysfunction based on previously reported functional connectivity abnormalities in sub-acute stroke patients. For each of nine bilateral functional networks, we averaged the FC strengths over all within-network interhemispheric functional connections. This resulted in nine network-specific interhemispheric functional connectivity measures (Figure S2D, left). To obtain a general measure of interhemispheric integration, we averaged the nine network-specific interhemispheric functional connectivity measures to obtain a single measure of mean interhemispheric within-network functional connectivity. We note that this measure essentially corresponded to the first principal component of the nine interhemispheric functional connectivity measures (R 2  = 0.94), which explained 70% of the total variance across the nine network-specific interhemispheric functional connectivity measures. To obtain a measure of network segregation, we averaged the functional connectivity values for all ipsilesional DAN and DMN functional connections (Figure S2D, middle). We chose this measure because previous analyses data from this sample have reliably reported reduced segregation between the DAN and DMN in patients (e.g., Ramsey et al., 2016; Siegel et al., 2016b). Finally, to obtain a global measure that considered both integration and segregation, we measured network modularity (Newman's Q) using the community_louvain function from the Brain Connectivity Toolbox (Rubinov and Sporns, 2010). Modularity estimation was performed using the 280 regions with specific a priori network assignments (i.e., excluding unassigned regions), and modules were defined a priori as the default network assignments in the Gordon333 parcellation for the reasons described in Siegel et al. (2016b). As in previous studies that have measured modularity in patients with focal brain lesions (Gratton et al., 2012; Siegel et al., 2018), we performed our analyses across multiple connection density thresholds ranging from 4% and 20% connection density in 2% steps (Figure S2D, right). The final modularity measure was obtained by averaging over connection density thresholds. We considered this appropriate as modularity estimates were highly correlated across thresholds such that a single principal component accounted for 95% of the total variance across thresholds (this component was almost perfectly colinear with the mean across thresholds - R 2  = 0.99). Unequal variance t tests were used to compare the a priori measures between patients and controls, and false discovery rate (FDR) correction was used to correct for multiple testing (Benjamini and Hochberg, 1995). Results of these analyses are shown in Figure S2D. We note that while some recent work suggests a potential for biases related to connection density thresholding when performing patient-control comparisons (e.g., Váša et al., 2018), this approach to modularity estimation was chosen as it was most comparable to the approaches used by previous studies on similar topics (e.g., Gratton et al., 2012; Siegel et al., 2018).

The parcel-level participation coefficients and within-module degree z-scores shown in Figure 2A were estimated by applying the Brain Connectivity Toolbox functions participation_coef and module_degree_zscore to the mean functional connectivity matrix from the control group (shown in Figure S2B) using the same regions and range of connection density thresholds as the modularity analyses (described above), and averaging across thresholds. Note that functional connectivity between parcels with Euclidean distances of less than 20mm was not used in the computation of these measures (Power et al., 2013). The connector hub and provincial damage measures (Figure 2) were defined according to the same procedure described by Gratton et al. (2012). For each patient, this involved multiplying the amount of damage to each region by its participation coefficient (connector hub damage) or its within-module degree z-score (provincial hub damage) and then averaging measures over regions. This produced a single connector hub damage measure and a single provincial hub damage measure for each patient.

We performed additional analyses to ensure that the observed group differences in modularity were not driven by false positives that could arise from applying proportional thresholding to data from groups that might differ in overall functional connectivity (van den Heuvel et al., 2017). We performed these analyses using overall functional connectivity defined as the mean of all positive functional connectivity values (van den Heuvel et al., 2017). First, we compared overall functional connectivity between patients and controls, and found that it did not significantly differ between groups (t = 0.29, p = 0.77). Next, we regressed overall functional connectivity out of the modularity measure and compared the residuals between patients and controls. Across the entire dataset, only ~11% of the variance was attributable to the effects of overall functional connectivity, and group differences persisted after regressing out the effect of overall functional connectivity. Similar results were also obtained when functional connectivity magnitude-based thresholds were used rather than edge density thresholds, and when modularity was computed on the weighted functional connectivity matrices (Rubinov and Sporns, 2011).

Structural lesion featuresMATLAB scripts utilizing functions from the matlab_nifti toolbox were used to obtain voxel-based damage and parcel-based gray matter damage measures (Figure 1B). For each patient, we re-shaped their 3×3×3mm lesion mask into a 1dimensional vector indexing the presence versus absence of damage at each voxel within the group-level lesion coverage area (hereafter referred to as 'voxel-based damage'). We also computed the proportion of each gray matter region that overlapped with each patient's lesion to create a 1-dimensional vector quantifying the amount of damage to each region within the group-level lesion coverage area (hereafter referred to as 'region-based damage'). MATLAB scripts implementing command line functions from the DSI_studio software package were used to obtain expected disconnections for each patient based on the intersection of their MNI-registered lesion and the structural connectome template, as described below.

For each patient, we extracted all streamlines that passed through the lesion to obtain a 359×359 structural disconnection adjacency matrix A D  where each entry A D ij quantified the number of streamlines connecting region i and region j that intersected the lesion (i.e., that were disconnected in that patient). We then normalized each structural disconnection matrix A D  via element-wise division by the structural connection matrix A S , such that entries in the resulting matrix A Dnorm  quantified the proportion of streamlines connecting region i and region j that were disconnected by the lesion. This step accounted for differences in the number of streamlines connecting different region pairs and ensured that all disconnection measurements were directly comparable and intuitively interpretable in terms of proportional disconnection rather than raw number of streamlines. The upper triangles (excluding diagonal elements) of the normalized disconnection matrices were then extracted and reshaped into a 1-dimensional vector quantifying the amount of disconnection for each connection (hereafter referred to as 'region-based disconnection'). For each patient, we also calculated the proportion of each neuroanatomically defined fiber bundle from the structural connectome atlas that was disconnected by the lesion, resulting in a 1-dimensional vector quantifying the amount of disconnection for each tract (hereafter referred to as 'tract-based disconnection'). Prior to performing any statistical analyses, the damage/disconnection vectors from all 114 patients were stacked on top of each other to form four separate data matrices.

Damage and disconnection frequency maps (Figure 1) were created using the voxel-based damage and region-based disconnection data. Voxel-based damage maps were summed across patients, resulting in a map that quantified the number of patients with damage to each voxel in the brain (Figure 1C, top). Region-based disconnections were binarized at a 1% disconnection threshold and summed across patients, resulting in a map that quantified the number of patients with damage to each connection in the structural connectome (Figure

1C, bottom). The damage and disconnection frequency measures were used to create the histograms shown in Figure 1D.

Multiple linear regressions and partial correlationsWe used multiple linear regressions to compare the effects of connector hub damage, provincial hub damage, and total disconnection (defined by summing the binarized region-based disconnections for each patient) on network modularity (Figure 2). We first fit a linear regression model that included connector hub and provincial hub damage as predictors (Figure 2B, Model 1). We then added total disconnection to the model to determine whether total disconnection explained additional variance beyond what could be attributed to the hub damage measures (i.e., F-test on R 2  change statistic; Figure 2B, Model 2), and to simultaneously evaluate the effects of all three measures in a single model. We then added lesion volume to determine whether the same effects were observed when lesion volume was included in the model (Figure 2B, Model 3). Effects were considered significant if they survived FDR correction at 0.05.

Because the original study by Gratton et al., (2012) used a correlation (i.e., rather than regression) approach, and because this allowed us to directly compare the strength of the relationships between different structural measures and modularity, we also performed correlational analyses (Figure 2C). For these analyses, we first computed the linear correlations between network modularity and total disconnection, connector hub damage, and provincial hub damage. We then compared each correlation using Steiger's z-tests. These analyses were then repeated after adjusting for lesion volume (i.e., partial correlation). Because the comparison between connector hub damage and provincial hub damage was intended to replicate the effect reported by Gratton et al., we used a one-tailed test (i.e., connector hub damage > provincial hub damage). Two-tailed tests were used to compare the correlations for total disconnection and connector hub damage. Effects were considered significant if they survived FDR correction at 0.05.

Partial least-squares regressionsWe used partial least-squares regressions (PLSR) to predict our a priori network-level functional connectivity measures from our structural damage and disconnection measures (Figures 3 and 4). PLSR is a multivariate regression technique (Wold et al., 2001) that is closely related to principal components regression (PCR) (Hotelling, 1957). Both PLSR and PCR are particularly useful for situations where there are more variables than observations and/or when there is high collinearity among the predictor variables. However, PLSR has important advantages over PCR (Abdi, 2010) that are primarily due to differences in the criteria used for decomposition of the predictor matrix. Namely, while PCR decomposes the predictor matrix X into a set of linearly independent components that maximally account for the variance in X and uses the scores on some subset of those components to predict Y , PLSR performs a dual decomposition of X and Y to obtain components from X that maximally account for the covariance with Y . This typically results in simpler models and is advantageous over PCR because it reduces the potential for important variables to be omitted from the model on the basis that they explain only small amounts of the variance in X (Abdi, 2010; Krishnan et al., 2011). Detailed descriptions of the theory and algorithms behind the PLSR approach can be found elsewhere (Abdi, 2010; Krishnan et al., 2011; McIntosh and Lobaugh, 2004; Tie Jong, 1993; Wold et al., 2001). We performed PLSR using the SIMPLS algorithm implemented in the plsregress function included with the MATLAB Statistics and Machine Learning Toolbox. Structural data matrices were mean-centered column-wise (default option for plsregress) prior to analysis. Predictor matrices were restricted to columns that had greater than two non-zero observations.

We fit PLSR models for each functional connectivity measure using the four different structural lesion measures as predictors. Leave-one-out (i.e., jackknife) optimization was used to identify the number of components (i.e., predictors) included for each model by adding components and measuring the change in prediction error with the inclusion of each additional component (Abdi, 2010). Components were added until the sum of squared prediction errors for the held-out cases increased with the addition of the new component, as increases in prediction error following the inclusion of additional components indicate overfitting to the training set (Abdi, 2010). This approach has been previously used for similar neuroimaging applications of PLSR (Kuceyeski et al., 2016b). The number of components for each model is shown in Figure 3B.

PLSR models were then fit to the full dataset using the optimal number of components identified for each model (Kuceyeski et al., 2015, 2016b). Bootstrap resampling (1000 bootstraps) was used to estimate CIs for the model fits and beta weights using the biascorrected and accelerated percentile method (Efron and Tibshirani, 1986) as implemented in the MATLAB function bootci (Figures 3A and 4). 95% CIs for model fits were adjusted to control the family-wise error rate for all 4 models fit to each FC measure, and therefore correspond to ~99% confidence intervals. 99% CIs were also estimated for the beta weights from each model. The signs of model weights were flipped as necessary so that positive weights predicted more severe FC disruptions for all models. Beta weights were also rescaled for the plots in Figures 4, S4, and S5 by multiplying all weights by a scalar value of 1000 (i.e., so that scientific notations would not overlap with the plot titles). Plots in Figure 4B were created using the MATLAB function plotSpread.

Comparisons of the different anatomical models of each functional connectivity outcome were performed using Akaike's information criterion weights (AICw; Figure 3C), as they incorporate information about both goodness-of-fit and model complexity (Kuceyeski et al., 2016b; Wagenmakers and Farrell, 2004). For each outcome variable, AICw were calculated as:

/u1D434/u1D43C /u1D436 /u1D464 = exp Δ/u1D434/u1D43C /u1D436 2 / ∑exp Δ/u1D434/u1D43C /u1D436 2

where ∆AIC corresponds to the difference between the AIC of each model and the minimum AIC across models for that outcome variable. The AIC weights for a given model from a set of candidate models can be interpreted as expressing the conditional probability that a given model is the best of all candidate models when considering both model performance and model complexity (Wagenmakers and Farrell, 2004). Thus, models with AIC weights closer to 1 are considered superior to models with AIC weights closer to 0. Linear correlations were computed among the unthresholded parcel disconnection weights from all 12 models and among all 12 functional connectivity measures (Figure 4A). Region-based disconnection model weights were extracted and plotted for different connection type categories (Figure 4B). The top 20% of significant weights from each model were projected to the brain for visualization (Figure 4C).

Partial least-squares correlationsWe used partial least-squares correlation (PLSC) of the full region-based disconnection and functional connectivity datasets to identify the patterns of structural disconnection and functional connectivity that maximally covary across patients (Figures 5, 6, and 7; Figures S6, S7, and S8). PLSC is a data-driven technique that is closely related to PLSR. PLSC seeks to define linear combinations of two data matrices ( X and Y ), referred to as latent variables (LVs), that maximally explain the covariance between the data matrices, and essentially involves performing a singular value decomposition (SVD) on the cross-block covariance matrix (Abdi, 2010; Krishnan et al., 2011; McIntosh and Lobaugh, 2004). PLSC has been successfully used to characterize covarying patterns of structural and functional connectivity in healthy individuals (Mišić et al., 2016) and has been successfully applied to other problems involving the relationships between structural and functional connectivity (Shen et al., 2015a, 2015b; Zimmermann et al., 2016).

Prior to performing the PLSC analysis, the upper triangle (excluding diagonal elements) of each patient's z-transformed functional connectivity matrix was extracted and reshaped into a 1-dimensional vector. The resulting vectors were then stacked on top of each other to create a patient-by-connection functional connectivity matrix, and an analogous patient-byconnection matrix that was created using the region-based disconnection matrices. Because the PLSC approach cannot accommodate missing values, functional connectivity between parcels that had been excluded from previous analyses (i.e., regions with < 60 vertices remaining) was set to 0 as in previously published multivariate analyses involving dense functional connectivity matrices from this sample (Siegel et al., 2016b). However, analyses that were performed without removing lesioned regions produced highly similar results (not shown), and control analyses that only included patients for whom no regions were removed (n = 51; see Additional Analyses) also produced results that were highly consistent with the main analyses (Figure S8). The patient-by-connection region-based disconnection ( X matrix) and functional connectivity ( Y matrix) matrices were mean-centered column-wise and used to compute the cross-product matrix X ' Y . Singular value decomposition (SVD) was then applied using the MATLAB function paq to obtain the solution:

/u1D417′/u1D418 = /u1D414/u1D412/u1D415′

/u1D414′/u1D414 = /u1D415′/u1D415 = /u1D408

producing a set of N-1 orthogonal LVs that each consisted of singular vectors U and V, and a diagonal matrix S containing the singular values. The singular vectors contained weighted

where linear combinations of the original data matrices that maximally covaried together, and the singular values encoded the proportion of the covariance between the original data matrices that was accounted for by each LV. Score matrices were computed by multiplying the original data matrices by the corresponding loading matrices to project each patient's data onto the LVs.

Permutation testing was used (1,000 permutations) to determine the significance of individual LVs (Abdi, 2010; Krishnan et al., 2011; McIntosh and Lobaugh, 2004), and bootstrap resampling (1,000 bootstraps) was used to compute bootstrap signal-to-noise ratios (BSRs) for the singular vector loadings associated with each LV by dividing the loadings by their bootstrapped standard error estimates (Abdi, 2010; Krishnan et al., 2011; McIntosh and Lobaugh, 2004). The (BSRs) quantify the stability of the loading estimates, and approximate z-scores (Efron and Tibshirani, 1986). Because the permutation and bootstrap procedures can produce LVs that do not match those obtained from PLSC of the original data, Procruste rotation was applied to the LVs obtained from the permutation/bootstrap analyses to ensure that they corresponded to those obtained from the original analyses (Krishnan et al., 2011; McIntosh and Lobaugh, 2004; Mišić et al., 2016). LVs obtained from the main PLSC analyses were considered significant if the permutation p value was less than 0.05 after correcting for tests across all 10 LVs that accounted for at least 1% of the covariance, and loadings were considered stable if the corresponding absolute BSRs were greater than 2.5 (i.e., p~0.01) (Krishnan et al., 2011; Mišićet al.,2016). Relevant results are shown in Figures 5, S6, S7, and S8.

Linear correlation was used to assess the strength of the relationship between LV1 functional connectivity and disconnection scores. Bootstrap resampling (1,000 bootstraps) was used to compute a 95% confidence interval on the correlation (Krishnan et al., 2011). Patient scores on the first LV (LV1) were linearly correlated with mean interhemispheric within-network functional connectivity, ipsilesional DAN-DMN functional connectivity, and network modularity measures, and with each of the behavioral measures (Figure 6). Linear correlations were also computed between the unthresholded disconnection and functional connectivity loading vectors for LV1 to characterize the topographic similarity of the linked structural and functional patterns (Figure 7). This analysis only considered loadings that were non-zero in both vectors (i.e., only cortico-cortical edges that had non-zero disconnection loadings). FDR correction was used to correct for multiple testing for each set of correlations.

Additional analysesWe performed additional analyses to (1) ensure that our main PLSR and PLSC results were not impacted by vascular factors as indexed by hemodynamic lags (Lv et al., 2013; Siegel et al., 2016a), (2) ensure that our main PLSR results held when all models were fit with only a single component, (3) ensure that our main PLSR and PLSC results did not depend on the inclusion of patients with lesions in either hemisphere, (4) ensure that the topographical similarity analyses of the PLSC loadings were not driven by the exclusion of highly damaged regions from the functional connectivity estimation, (5) ensure that the topographies of the region-based PLSR model weights were not distorted by including only disconnection information in the region-based disconnection PLSR models, (6) ensure that the main PLSR results were not attributable to lesion volume effects, and (7)

ensure that the low-dimensionality of the PLSC results was not constrained by an intrinsic low-dimensionality of the structural and/or functional measures. These analyses are described in more detail below.

### Controlling for large ipsilesional hemodynamic lags in PLSR/PLSC analyses-

Identification of patients with abnormal hemodynamic lags proceeded as follows. For each voxel, hemodynamic lags were with estimated with respect to the global gray matter signal using a window size of -8 s to 8 s (i.e., 4 TR), and the average difference in lag values between the lesioned and unlesioned hemispheres was computed for each patient as in previous work (Siegel et al., 2016a). To ensure that our main results were not driven by patients with potentially abnormal hemodynamics, supplemental PLSR and PLSC analyses were performed that excluded patients with lag differences greater than 2 standard deviations from the control mean (i.e., > 0.32 s; 20/114 patients excluded). We note that this threshold (0.32 s) is conservative compared to thresholds used in prior work (Siegel et al., 2016b, 2018). Results from the PLSR and PLSC analyses that excluded high-lag patients were highly consistent with the main results and are shown in Figure S3A and S7A.

### Controlling for differences in the number of PLSR components across models

-The PLSR parcel SDC models presented in Figure 3 often utilized more components than the damage models. While the number of components for each model was determined in a principled manner using jackknife cross-validation and the AIC weights incorporated information about model complexity, we wanted to ensure that similar results were obtained when all models utilized only a single component. We therefore fit all of the PLSR models using only a single component solution. The results of these analyses were highly consistent with the main analyses and are presented in Figure S3B.

### Controlling for the inclusion of patients with lesions in either hemisphere-

The analyses presented in the main text utilized data from patients with lesions in either the left or right hemisphere. To determine whether our main results held when analyses were restricted to patients with lesions in a single hemisphere, we performed separate PLSR and PLSC analyses for patients with left versus right hemispheric lesions. Results from the PLSR and PLSC analyses that were restricted to patients with lesions in a single hemisphere were highly consistent with the results from the main analyses and are shown in Figures S3C and S3D, and S7B and S7C, respectively.

Controlling for removal of damaged regions in PLSC analysesAs described in the description of the functional connectivity estimation procedures, lesioned vertices were not included in the estimation of functional connectivity, and regions that had less than 60 vertices remaining after excluding lesioned vertices were removed for each patient by setting them to NaN. When computing functional connectivity summary measures, this allowed us to completely exclude highly damaged regions. However, the PLSC analyses used the dense functional connectivity matrices and therefore could not accommodate NaN values. Therefore, functional connectivity for removed regions was set to 0 as in previous multivariate analyses (Siegel et al., 2016b). However, we were concerned that the removal of highly damaged regions from the functional connectivity matrices might introduce systematic covariance between disconnections caused by the lesions that resulted in region removal and the zero-valued cells in the functional connectivity matrix, as this could bias the solution and lead to artificial topographic similarity between the structural and functional loadings. While region removals were relatively infrequent (Figure S8A), we still wanted to control for this possibility. Therefore, we repeated the PLSC and topographic similarity analyses using only data from 51 patients for whom no regions were sufficiently damaged to be removed from the analyses. These patients had essentially minimal to no cortical damage (Figure S8B), and therefore the results could not be attributed to the effects of regional damage on functional connectivity. The results obtained from these analyses were highly similar to those obtained from the main analyses and are presented in Figure S8.

PLSR analyses with composite SDC and damage modelsThe results shown in Figure S5 suggested that region-based damage PLSR models sometimes mis-localized WM damage effects to nearby gray matter regions. This suggested that the region-based damage models were taking advantage of damage to gray matter regions that was correlated with the white matter damage effects identified by the voxel damage models. Because the regionbased disconnection models lacked explicit information about gray matter damage, we were concerned that the region-based disconnection topographies might be susceptible to similar distortion. Therefore, we performed supplemental analyses to determine whether the regionbased disconnection weight topographies were affected by including information about region-based gray matter damage. This analysis consisted of running the PLSR analyses with both the region-based disconnection and damage measures as predictors in the same model, and then correlating the resulting (unthresholded) PLSR weight vectors with those obtained from the original analyses. This revealed that the weight topographies of the region-based SDC models were virtually unchanged by the inclusion of the region-based damage measures (across-model mean correlation of weight vectors = 0.98, SD = 0.04). However, this did have substantial effect on the region-based damage weight topographies (across-model mean correlation of weight vectors = 0.79, SD = 0.24), consistent with what would be expected under the scenario described above given that the functional connectivity measures were most strongly related to white matter damage and structural disconnection.

### Comparing lesion volume information provided by damage and disconnection

measuresTo determine whether the effects observed for the disconnection measures might be driven by an underlying relationship to total lesion volume, we performed an additional PLSR analysis with lesion volume as the dependent variable. This allowed us to identify the multivariate damage/disconnection measure(s) that contained the most information about lesion volume. Given that lesion volume can be directly computed from the voxel-wise damage maps, and given that the total number of parcels damaged in a patient will be closely related to the size of the lesion, we expected that the damage measures would actually contain more information about lesion volume than the disconnection measures. The PLSR analysis revealed that the region-based and voxel-based damage models were able to almost perfectly explain the variance in lesion volume (R 2 's = 0.98 and 0.99, respectively), and explained substantially more variance in lesion volume than the regionbased and tract-based disconnection models (R 2 's = 0.67 and 0.72, respectively). Comparisons of AIC weights revealed that voxel-based damage measures provided the best account of lesion volume. Therefore, the potential effects of lesion volume were actually greatest for the damage models. This indicates that even though the damage models were able to capitalize directly on information about lesion volume to a much greater extent than the disconnection models, the disconnection models still outperformed them for explaining functional connectivity disruptions.

Dimensionality of structural and functional dataTo ensure that the lowdimensionality of the PLSC results was not simply reflecting an intrinsically lowdimensionality of the structural measures or functional connectivity measures, we performed principal component analyses (PCA) on the dense voxel-based damage, region-based disconnection, and functional connectivity data from the patient sample (Figure S9). Recall that in the PLSC analyses, the first 5 LVs explained over 80% of the total covariance between the dense structural disconnection and functional connectivity datasets (Figure 5A). By comparison, the dense voxel-based damage data were relatively high-dimensional - 28 components are necessary to explain 80% of the total variance across all voxels in the lesion coverage zone. The dense region-based disconnection data were lower-dimensional than the voxel-based damage data, but were still relatively high-dimensional - 15 components were necessary to explain 80% of the total variance in region-based disconnections across all connections in the disconnection coverage zone. Finally, the dense functional connectivity data were very high-dimensional - 72 components were necessary to explain 80% of the total variance in the functional connectivity data. These results indicate that there were far fewer salient covariance dimensions between the disconnection and functional connectivity data than there were variance dimensions in the voxel-based damage, region-based disconnection, or functional connectivity data. This argues against an intrinsic lowdimensionality of the dense structural or functional data as a source of the observed lowdimensional covariance.

### DATA AND CODE AVAILABILITY

The full set of neuroimaging and behavioral data are available at http://cnda.wustl.edu/app/ template/Login.vm. Specific data and analysis scripts are available on request to the authors.

### Supplementary Material

Refer to Web version on PubMed Central for supplementary material.

### ACKNOWLEDGMENT

Funding was provided by NIH grant R01 NS095741 to M.C. and NIMH grant R01 HD061117 to M.C. Data were provided (in part) by the Human Connectome Project, WU-Minn Consortium (principal investigators David Van Essen and Kamil Ugurbil; 1U54MH091657), funded by the 16 NIH institutes and centers that support the NIH Blueprint for Neuroscience Research and by the McDonnell Center for Systems Neuroscience at Washington University. We thank Alexandre Carter for assisting with lesion segmentation and Joshua Siegel for comments on earlier versions of the manuscript.

### REFERENCES

Abdi H (2010). Partial least squares regression and projection on latent structure regression (PLS Regression). WIRES Comput. Stat 2, 97-106.

- Adachi Y, Osada T, Sporns O, Watanabe T, Matsui T, Miyamoto K, and Miyashita Y (2012). Functional connectivity between anatomically unconnected areas is shaped by collective networklevel effects in the macaque cortex. Cereb. Cortex 22, 1586-1592. [PubMed: 21893683]
- Alstott J, Breakspear M, Hagmann P, Cammoun L, and Sporns O (2009). Modeling the impact of lesions in the human brain. PLoS Comput. Biol 5, e1000408. [PubMed: 19521503]
- Anderson SW, Damasio H, and Tranel D (1990). Neuropsychological Impairments Associated With Lesions Caused by Tumor or Stroke. Arch. Neurol 47, 397-405. [PubMed: 2322133]
- Baldassarre A, Ramsey L, Hacker CL, Callejas A, Astafiev SV, Metcalf NV, Zinn K, Rengachary J, Snyder AZ, Carter AR, et al. (2014). Large-scale changes in network interactions as a physiological signature of spatial neglect. Brain 137, 3267-3283. [PubMed: 25367028]
- Baldassarre A, Ramsey LE, Siegel JS, Shulman GL, and Corbetta M (2016a). Brain connectivity and neurological disorders after stroke. Curr. Opin. Neurol 29, 706-713. [PubMed: 27749394]
- Baldassarre A, Ramsey L, Rengachary J, Zinn K, Siegel JS, Metcalf NV, Strube MJ, Snyder AZ, Corbetta M, and Shulman GL (2016b). Dissociated functional connectivity profiles for motor and attention deficits in acute right-hemisphere stroke. Brain 139, 2024-2038. [PubMed: 27225794]
- Bauer AQ, Kraft AW, Wright PW, Snyder AZ, Lee JM, and Culver JP (2014). Optical imaging of disrupted functional connectivity following ischemic stroke in mice. Neuroimage 99, 388-401. [PubMed: 24862071]
- Benjamini Y, and Hochberg Y (1995). Controlling the False Discovery Rate: A Practical and Powerful Approach to Multiple Testing. J. R. Stat. Soc. B 57, 289-300.
- Biswal B, Yetkin FZ, Haughton VM, and Hyde JS (1995). Functional connectivity in the motor cortex of resting human brain using echo-planar MRI. Magn. Reson. Med 34, 537-541. [PubMed: 8524021]
- Braga RM, and Buckner RL (2017). Parallel Interdigitated Distributed Networks within the Individual Estimated by Intrinsic Functional Connectivity. Neuron 95, 457-471.e5. [PubMed: 28728026]
- Cabral J, Hugues E, Kringelbach ML, and Deco G (2012). Modeling the outcome of structural disconnection on resting-state functional connectivity. Neuroimage 62, 1342-1353. [PubMed: 22705375]
- Carrera E, and Tononi G (2014). Diaschisis: past, present, future. Brain 137, 2408-2422. [PubMed: 24871646]
- Carter AR, Astafiev SV, Lang CE, Connor LT, Rengachary J, Strube MJ, Pope DLW, Shulman GL, and Corbetta M (2010). Resting inter-hemispheric functional magnetic resonance imaging connectivity predicts performance after stroke. Ann. Neurol 67, 365-375. [PubMed: 20373348]
- Carter AR, Patel KR, Astafiev SV, Snyder AZ, Rengachary J, Strube MJ, Pope A, Shimony JS, Lang CE, Shulman GL, and Corbetta M (2012). Upstream dysfunction of somatomotor functional connectivity after corticospinal damage in stroke. Neurorehabil. Neural Repair 26, 7-19. [PubMed: 21803932]
- Catani M, Dell'acqua F, Bizzi A, Forkel SJ, Williams SC, Simmons A, Murphy DG, and Thiebaut de Schotten M (2012). Beyond cortical localization in clinico-anatomical correlation. Cortex 48, 1262-1287. [PubMed: 22995574]
- Chechlacz M, Rotshtein P, Hansen PC, Deb S, Riddoch MJ, and Humphreys GW (2013). The central role of the temporo-parietal junction and the superior longitudinal fasciculus in supporting multiitem competition: evidence from lesion-symptom mapping of extinction. Cortex 49, 487-506. [PubMed: 22192727]
- Corbetta M, Kincade MJ, Lewis C, Snyder AZ, and Sapir A (2005). Neural basis and recovery of spatial attention deficits in spatial neglect. Nat. Neurosci 8, 1603-1610. [PubMed: 16234807]
- Corbetta M, Ramsey L, Callejas A, Baldassarre A, Hacker CD, Siegel JS, Astafiev SV, Rengachary J, Zinn K, Lang CE, et al. (2015). Common behavioral clusters and subcortical anatomy in stroke. Neuron 85, 927-941. [PubMed: 25741721]
- Corbetta M, Siegel JS, and Shulman GL (2018). On the low dimensionality of behavioral deficits and alterations of brain network connectivity after focal injury. Cortex 107, 229-237. [PubMed: 29357980]
- Dale AM, Fischl B, and Sereno MI (1999). Cortical surface-based analysis. I. Segmentation and surface reconstruction. Neuroimage 9, 179-194. [PubMed: 9931268]

- Desmurget M, Bonnetblanc F, and Duffau H (2007). Contrasting acute and slow-growing lesions: a new door to brain plasticity. Brain 130, 898-914. [PubMed: 17121742]
- Duffau H, and Capelle L (2004). Preferential brain locations of low-grade gliomas. Cancer 100, 26222626. [PubMed: 15197805]
- Efron B, and Tibshirani R (1986). Bootstrap Methods for Standard Errors, Confidence Intervals, and Other Measures of Statistical Accuracy. Stat. Sci 1, 54-75.
- Eldaief MC, McMains S, Hutchison RM, Halko MA, and Pascual-Leone A (2017). Reconfiguration of Intrinsic Functional Coupling Patterns Following Circumscribed Network Lesions. Cereb. Cortex 27, 2894-2910. [PubMed: 27226439]
- Esmaeili M, Stensjøen AL, Berntsen EM, Solheim O, and Reinertsen I (2018). The direction of tumour growth in glioblastoma patients. Sci. Rep 8, 1199. [PubMed: 29352231]
- Van Essen DC, Drury HA, Dickson J, Harwell J, Hanlon D, and Anderson C (2001). An Integrated Software Suite for Surface-based Analyses of Cerebral Cortex. J. Am. Med. Inform. Assoc 8, 443459. [PubMed: 11522765]
- Fischl B, Sereno MI, and Dale AM (1999). Cortical surface-based analysis. II: Inflation, flattening, and a surface-based coordinate system. Neuroimage 9, 195-207. [PubMed: 9931269]
- Forkel SJ, and Catani M (2018). Lesion mapping in acute stroke aphasia and its implications for recovery. Neuropsychologia 115, 88-100. [PubMed: 29605593]
- Forkel SJ, Thiebaut de Schotten M, Dell'Acqua F, Kalra L, Murphy DGM, Williams SCR, and Catani M (2014). Anatomical predictors of aphasia recovery: a tractography study of bilateral perisylvian language networks. Brain 137, 2027-2039. [PubMed: 24951631]
- Foulon C, Cerliani L, Kinkingnéhun S, Levy R, Rosso C, Urbanski M, Volle E, and Thiebaut de Schotten M (2018). Advanced lesion symptom mapping analyses and implementation as BCBtoolkit. Gigascience 7, 1-17.
- Fox MD (2018). Mapping symptoms to brain networks using the human connectome. N. Engl. J. Med 379, 2237-2245. [PubMed: 30575457]
- Fridriksson J, Guo D, Fillmore P, Holland A, and Rorden C (2013). Damage to the anterior arcuate fasciculus predicts non-fluent speech production in aphasia. Brain 136, 3451-3460. [PubMed: 24131592]
- Glasser MF, Sotiropoulos SN, Wilson JA, Coalson TS, Fischl B, Andersson JL, Xu J, Jbabdi S, Webster M, Polimeni JR, et al.; WU-Minn HCP Consortium (2013). The minimal preprocessing pipelines for the Human Connectome Project. Neuroimage 80, 105-124. [PubMed: 23668970]
- Golestani AM, Tymchuk S, Demchuk A, and Goodyear BG; VISION-2 Study Group (2013). Longitudinal evaluation of resting-state FMRI after acute stroke with hemiparesis. Neurorehabil. Neural Repair 27, 153-163. [PubMed: 22995440]
- Goñi J, van den Heuvel MP, Avena-Koenigsberger A, Velez de Mendizabal N, Betzel RF, Griffa A, Hagmann P, Corominas-Murtra B, Thiran J-P, and Sporns O (2014). Resting-brain functional connectivity predicted by analytic measures of network communication. Proc. Natl. Acad. Sci. USA 111, 833-838. [PubMed: 24379387]
- Gordon EM, Laumann TO, Adeyemo B, Huckins JF, Kelley WM, and Petersen SE (2016). Generation and Evaluation of a Cortical Area Parcellation from Resting-State Correlations. Cereb. Cortex 26, 288-303. [PubMed: 25316338]
- Gordon EM, Laumann TO, Gilmore AW, Newbold DJ, Greene DJ, Berg JJ, Ortega M, Hoyt-Drazen C, Gratton C, Sun H, et al. (2017). Precision Functional Mapping of Individual Human Brains. Neuron 95, 791-807.e7. [PubMed: 28757305]
- Grandjean J, Zerbi V, Balsters J, Wenderoth N, and Rudina M (2017). The structural basis of largescale functional connectivity in the mouse. J. Neurosci 37, 8092-8101. [PubMed: 28716961]
- Gratton C, Nomura EM, Pérez F, and D'Esposito M (2012). Focal brain lesions to critical locations cause widespread disruption of the modular organization of the brain. J. Cogn. Neurosci 24, 12751285. [PubMed: 22401285]
- Gratton C, Laumann TO, Nielsen AN, Greene DJ, Gordon EM, Gilmore AW, Nelson SM, Coalson RS, Snyder AZ, Schlaggar BL, et al. (2018). Functional Brain Networks Are Dominated by Stable Group and Individual Factors, Not Cognitive or Daily Variation. Neuron 98, 439-452.e5. [PubMed: 29673485]

- Grayson DS, Bliss-Moreau E, Machado CJ, Bennett J, Shen K, Grant KA, Fair DA, and Amaral DG (2016). The Rhesus Monkey Connectome Predicts Disrupted Functional Networks Resulting from Pharmacogenetic Inactivation of the Amygdala. Neuron 91, 453-466. [PubMed: 27477019]
- Grefkes C, and Fink GR (2014). Connectivity-based approaches in stroke and recovery of function. Lancet Neurol. 13, 206-216. [PubMed: 24457190]
- Greicius MD, Supekar K, Menon V, and Dougherty RF (2009). Resting-state functional connectivity reflects structural connectivity in the default mode network. Cereb. Cortex 19, 72-78. [PubMed: 18403396]
- Griffis JC, Nenert R, Allendorfer JB, and Szaflarski JP (2017a). Linking left hemispheric tissue preservation to fMRI language task activation in chronic stroke patients. Cortex 96, 1-18. [PubMed: 28961522]
- Griffis JC, Nenert R, Allendorfer JB, and Szaflarski JP (2017b). Damage to white matter bottlenecks contributes to language impairments after left hemispheric stroke. Neuroimage Clin. 14, 552-565. [PubMed: 28337410]
- He BJ, Snyder AZ, Vincent JL, Epstein A, Shulman GL, and Corbetta M (2007). Breakdown of functional connectivity in frontoparietal networks underlies behavioral deficits in spatial neglect. Neuron 53, 905-918. [PubMed: 17359924]
- Heiss WD, Kessler J, Thiel A, Ghaemi M, and Karbe H (1999). Differential capacity of left and right hemispheric areas for compensation of poststroke aphasia. Ann. Neurol 45, 430-438. [PubMed: 10211466]
- Honey CJ, Sporns O, Cammoun L, Gigandet X, Thiran JP, Meuli R, and Hagmann P (2009). Predicting human resting-state functional connectivity from structural connectivity. Proc. Natl. Acad. Sci. USA 106, 2035-2040. [PubMed: 19188601]
- Hope TMH, Leff AP, and Price CJ (2018). Predicting language outcomes after stroke: Is structural disconnection a useful predictor? Neuroimage Clin. 19, 22-29. [PubMed: 30034998]
- Hotelling H (1957). The relations of the newer multivariate statistical methods to factor analysis. Br. J. Stat. Psychol 10, 69-79.
- Jilka SR, Scott G, Ham T, Pickering A, Bonnelle V, Braga RM, Leech R, and Sharp DJ (2014). Damage to the Salience Network and interactions with the Default Mode Network. J. Neurosci 34, 10798-10807. [PubMed: 25122883]
- Johnston JM, Vaishnavi SN, Smyth MD, Zhang D, He BJ, Zempel JM, Shimony JS, Snyder AZ, and Raichle ME (2008). Loss of resting interhemispheric functional connectivity after complete section of the corpus callosum. J. Neurosci 28, 6453-6458. [PubMed: 18562616]
- Krishnan A, Williams LJ, McIntosh AR, and Abdi H (2011). Partial Least Squares (PLS) methods for neuroimaging: a tutorial and review. Neuroimage 56, 455-475. [PubMed: 20656037]
- Kuceyeski A, Kamel H, Navi BB, Raj A, and Iadecola C (2014). Predicting future brain tissue loss from white matter connectivity disruption in ischemic stroke. Stroke 45, 717-722. [PubMed: 24523041]
- Kuceyeski A, Navi BB, Kamel H, Relkin N, Villanueva M, Raj A, Toglia J, O'Dell M, and Iadecola C (2015). Exploring the brain's structural connectome: A quantitative stroke lesion-dysfunction mapping study. Hum. Brain Mapp 36, 2147-2160. [PubMed: 25655204]
- Kuceyeski A, Shah S, Dyke JP, Bickel S, Abdelnour F, Schiff ND, Voss HU, and Raj A (2016a). The application of a mathematical model linking structural and functional connectomes in severe brain injury. Neuroimage Clin. 11, 635-647. [PubMed: 27200264]
- Kuceyeski A, Navi BB, Kamel H, Raj A, Relkin N, Toglia J, Iadecola C, and O'Dell M (2016b). Structural connectome disruption at baseline predicts 6-months post-stroke outcome. Hum. Brain Mapp 37, 2587-2601. [PubMed: 27016287]
- Lim DH, LeDue JM, Mohajerani MH, and Murphy TH (2014). Optogenetic mapping after stroke reveals network-wide scaling of functional connections and heterogeneous recovery of the periinfarct. J. Neurosci 34, 16455-16466. [PubMed: 25471583]
- Lu J, Liu H, Zhang M, Wang D, Cao Y, Ma Q, Rong D, Wang X, Buck-ner RL, and Li K (2011). Focal pontine lesions provide evidence that intrinsic functional connectivity reflects polysynaptic anatomical pathways. J. Neurosci 31, 15065-15071. [PubMed: 22016540]

- Lv Y, Margulies DS, Cameron Craddock R, Long X, Winter B, Gierhake D, Endres M, Villringer K, Fiebach J, and Villringer A (2013). Identifying the perfusion deficit in acute stroke with restingstate functional magnetic resonance imaging. Ann. Neurol 73, 136-140. [PubMed: 23378326]
- Marcus DS, Harwell J, Olsen T, Hodge M, Glasser MF, Prior F, Jenkinson M, Laumann T, Curtiss SW, and Van Essen DC (2011). Informatics and Data Mining Tools and Strategies for the Human Connectome Project. Front. Neuroinform 5, 1-12. [PubMed: 21472085]
- Marebwa BK, Fridriksson J, Yourganov G, Feenaughty L, Rorden C, and Bonilha L (2017). Chronic post-stroke aphasia severity is determined by fragmentation of residual white matter networks. Sci. Rep 7, 8188. [PubMed: 28811520]
- Marek S, Siegel JS, Gordon EM, Raut RV, Gratton C, Newbold DJ, Ortega M, Laumann TO, Adeyemo B, Miller DB, et al. (2018). Spatial and Temporal Organization of the Individual Human Cerebellum. Neuron 100, 977-993.e7. [PubMed: 30473014]
- McIntosh AR, and Lobaugh NJ (2004). Partial least squares analysis of neuroimaging data: applications and advances. Neuroimage 23, S250-S263. [PubMed: 15501095]
- Messé A, Rudrauf D, Benali H, and Marrelec G (2014). Relating structure and function in the human brain: relative contributions of anatomy, stationary dynamics, and non-stationarities. PLoS Comput. Biol 10, e1003530. [PubMed: 24651524]
- Mišić B, and Sporns O (2016). From regions to connections and networks: new bridges between brain and behavior. Curr. Opin. Neurobiol 40, 1-7. [PubMed: 27209150]
- Mišić B, Betzel RF, de Reus MA, van den Heuvel MP, Berman MG, McIntosh AR, and Sporns O (2016). Network-Level Structure-Function Relationships in Human Neocortex. Cereb. Cortex 26, 3285-3296. [PubMed: 27102654]
- New AB, Robin DA, Parkinson AL, Duffy JR, McNeil MR, Piguet O, Hornberger M, Price CJ, Eickhoff SB, and Ballard KJ (2015). Altered resting-state network connectivity in stroke patients with and without apraxia of speech. Neuroimage Clin. 8, 429-439. [PubMed: 26106568]
- Nomura EM, Gratton C, Visser RM, Kayser A, Perez F, and D'Esposito M (2010). Double dissociation of two cognitive control networks in patients with focal brain lesions. Proc. Natl. Acad. Sci. USA 107, 12017-12022. [PubMed: 20547857]
- O'Reilly JX, Croxson PL, Jbabdi S, Sallet J, Noonan MP, Mars RB, Browning PGF, Wilson CRE, Mitchell AS, Miller KL, et al. (2013). Causal effect of disconnection lesions on interhemispheric functional connectivity in rhesus monkeys. Proc. Natl. Acad. Sci. USA 110, 13982-13987. [PubMed: 23924609]
- Ovadia-Caro S, Villringer K, Fiebach J, Jungehulsing GJ, van der Meer E, Margulies DS, and Villringer A (2013). Longitudinal effects of lesions on functional networks after stroke. J. Cereb. Blood Flow Metab 33, 1279-1285. [PubMed: 23715061]
- Park HJ, and Friston K (2013). Structural and functional brain networks: from connections to cognition. Science 342, 1238411. [PubMed: 24179229]
- Park CH, Chang WH, Ohn SH, Kim ST, Bang OY, Pascual-Leone A, and Kim YH (2011). Longitudinal changes of resting-state functional connectivity during motor recovery after stroke. Stroke 42, 1357-1362. [PubMed: 21441147]
- Poldrack RA (2012). The future of fMRI in cognitive neuroscience. Neuro-image 62, 1216-1220. [PubMed: 21856431]
- Power JD, Schlaggar BLB, Lessov-Schlaggar CN, and Petersen SE (2013). Evidence for hubs in human functional brain networks. Neuron 79, 798-813. [PubMed: 23972601]
- Power JD, Mitra A, Laumann TO, Snyder AZ, Schlaggar BL, and Petersen SE (2014). Methods to detect, characterize, and remove motion artifact in resting state fMRI. Neuroimage 84, 320-341. [PubMed: 23994314]
- Pustina D, Coslett HB, Ungar L, Faseyitan OK, Medaglia JD, Avants B, and Schwartz MF (2017a). Enhanced estimations of post-stroke aphasia severity using stacked multimodal predictions. Hum. Brain Mapp. 38, 5603-5615. [PubMed: 28782862]
- Pustina D, Avants B, Faseyitan O, Medaglia J, and Branch Coslett H (2018). Improved accuracy of lesion to symptom mapping with multivariate sparse canonical correlations. Neuropsychologia 115, 154-166. [PubMed: 28882479]

- Ramsey LE, Siegel JS, Baldassarre A, Metcalf NV, Zinn K, Shulman GL, and Corbetta M (2016). Normalization of network connectivity in hemi-spatial neglect recovery. Ann. Neurol 80, 127-141. [PubMed: 27277836]
- Ramsey LE, Siegel JS, Lang CE, Strube M, Shulman GL, and Corbetta M (2017). Behavioural clusters and predictors of performance during recovery from stroke. Nat. Hum. Behav 1, 0038. [PubMed: 28713861]
- Rehme AK, Eickhoff SB, Wang LE, Fink GR, and Grefkes C (2011). Dynamic causal modeling of cortical activity from the acute to the chronic stage after stroke. Neuroimage 55, 1147-1158. [PubMed: 21238594]
- Robb RA, and Hanson DP (1991). A software system for interactive and quantitative visualization of multidimensional biomedical images. Australas. Phys. Eng. Sci. Med 14, 9-30. [PubMed: 2029243]
- Roland JL, Snyder AZ, Hacker CD, Mitra A, Shimony JS, Limbrick DD, Raichle ME, Smyth MD, and Leuthardt EC (2017). On the role of the corpus callosum in interhemispheric functional connectivity in humans. Proc. Natl. Acad. Sci. USA 114, 13278-13283. [PubMed: 29183973]
- Rubinov M, and Sporns O (2010). Complex network measures of brain connectivity: uses and interpretations. Neuroimage 52, 1059-1069. [PubMed: 19819337]
- Rubinov M, and Sporns O (2011). Weight-conserving characterization of complex functional brain networks. Neuroimage 56, 2068-2079. [PubMed: 21459148]
- Saenger VM, Ponce-Alvarez A, Adhikari M, Hagmann P, Deco G, and Corbetta M (2018). Linking Entropy at Rest with the Underlying Structural Connectivity in the Healthy and Lesioned Brain. Cereb. Cortex 47, 1-11.
- Saur D, Lange R, Baumgaertner A, Schraknepper V, Willmes K, Rijntjes M, and Weiller C (2006). Dynamics of language reorganization after stroke. Brain 129, 1371-1384. [PubMed: 16638796]
- Sharp DJ, Scott G, and Leech R (2014). Network dysfunction after traumatic brain injury. Nat. Rev. Neurol 10, 156-166. [PubMed: 24514870]
- Shen K, Hutchison RM, Bezgin G, Everling S, and McIntosh AR (2015a). Network structure shapes spontaneous functional connectivity dynamics. J. Neurosci 35, 5579-5588. [PubMed: 25855174]
- Shen K, Mišić B, Cipollini BN, Bezgin G, Buschkuehl M, Hutchison RM, Jaeggi SM, Kross E, Peltier SJ, Everling S, et al. (2015b). Stable long-range interhemispheric coordination is supported by direct anatomical projections. Proc. Natl. Acad. Sci. USA 112, 6473-6478. [PubMed: 25941372]
- Siegel JS, Snyder AZ, Ramsey L, Shulman GL, and Corbetta M (2016a). The effects of hemodynamic lag on functional connectivity and behavior after stroke. J. Cereb. Blood Flow Metab 36, 21622176. [PubMed: 26661223]
- Siegel JS, Ramsey LE, Snyder AZ, Metcalf NV, Chacko RV, Weinberger K, Baldassarre A, Hacker CD, Shulman GL, and Corbetta M (2016b). Disruptions of network connectivity predict impairment in multiple behavioral domains after stroke. Proc. Natl. Acad. Sci. USA 113, E4367E4376. [PubMed: 27402738]
- Siegel JS, Shulman GL, and Corbetta M (2017). Measuring functional connectivity in stroke: Approaches and considerations. J. Cereb. Blood Flow Metab 37, 2665-2678. [PubMed: 28541130]
- Siegel JS, Seitzman BA, Ramsey LE, Ortega M, Gordon EM, Dosen-bach NUF, Petersen SE, Shulman GL, and Corbetta M (2018). Re-emergence of modular brain networks in stroke recovery. Cortex 101, 44-59. [PubMed: 29414460]
- Sperber C, and Karnath HO (2015). Topography of acute stroke in a sample of 439 right brain damaged patients. Neuroimage Clin. 10, 124-128. [PubMed: 26759787]
- Tang C, Zhao Z, Chen C, Zheng X, Sun F, Zhang X, Tian J, Fan M, Wu Y, and Jia J (2016). Decreased Functional Connectivity of Homotopic Brain Regions in Chronic Stroke Patients: A Resting State fMRI Study. PLoS One 11, e0152875. [PubMed: 27074031]
- Thiebaut de Schotten M, Tomaiuolo F, Aiello M, Merola S, Silvetti M, Lecce F, Bartolomeo P, and Doricchi F (2014). Damage to white matter pathways in subacute and chronic spatial neglect: a group study and 2 single-case studies with complete virtual 'in vivo' tractography dissection. Cereb. Cortex 24, 691-706. [PubMed: 23162045]
- Tie Jong S (1993). SIMPLS: an alternative approach squares regression to partial least. Chemometr. Intell. Lab. Syst 18, 251-263.

- Tzourio-Mazoyer N, Landeau B, Papathanassiou D, Crivello F, Etard O, Delcroix N, Mazoyer B, and Joliot M (2002). Automated anatomical labeling of activations in SPM using a macroscopic anatomical parcellation of the MNI MRI single-subject brain. Neuroimage 15, 273-289. [PubMed: 11771995]
- van den Heuvel MP, Mandl RCW, Kahn RS, and Hulshoff Pol HE (2009). Functionally linked restingstate networks reflect the underlying structural connectivity architecture of the human brain. Hum. Brain Mapp 30, 3127-3141. [PubMed: 19235882]
- van den Heuvel MP, de Lange SC, Zalesky A, Seguin C, Yeo BTT, and Schmidt R (2017). Proportional thresholding in resting-state fMRI functional connectivity networks and consequences for patient-control connectome studies: Issues and recommendations. Neuroimage 152, 437-449. [PubMed: 28167349]
- van Meer MPA, Otte WM, van der Marel K, Nijboer CH, Kavelaars A, van der Sprenkel JWB, Viergever MA, and Dijkhuizen RM (2012). Extent of bilateral neuronal network reorganization and functional recovery in relation to stroke severity. J. Neurosci 32, 4495-4507. [PubMed: 22457497]
- Váša F, Shanahan M, Hellyer PJ, Scott G, Cabral J, and Leech R (2015). Effects of lesions on synchrony and metastability in cortical networks. Neuroimage 118, 456-467. [PubMed: 26049146]
- Váša F, Bullmore ET, and Patel AX (2018). Probabilistic thresholding of functional connectomes: Application to schizophrenia. Neuroimage 172, 326-340. [PubMed: 29277403]
- Wagenmakers EJ, and Farrell S (2004). AIC model selection using Akaike weights. Psychon. Bull. Rev 11, 192-196. [PubMed: 15117008]
- Wang L, Yu C, Chen H, Qin W, He Y, Fan F, Zhang Y, Wang M, Li K, Zang Y, et al. (2010). Dynamic functional reorganization of the motor execution network after stroke. Brain 133, 1224-1238. [PubMed: 20354002]
- Warren DE, Power JD, Bruss J, Denburg NL, Waldron EJ, Sun H, Petersen SE, and Tranel D (2014). Network measures predict neuropsycho-logical outcome after brain injury. Proc. Natl. Acad. Sci. USA 111, 14247-14252. [PubMed: 25225403]
- Wilson SM, Galantucci S, Tartaglia MC, Rising K, Patterson DK, Henry ML, Ogar JM, DeLeon J, Miller BL, and Gorno-Tempini ML (2011). Syntactic processing depends on dorsal language tracts. Neuron 72, 397-403. [PubMed: 22017996]
- Wold S, Sjöström M, and Eriksson L (2001). PLS-regression: A basic tool of chemometrics. Chemometr. Intell. Lab. Syst 58, 109-130.
- Wu W, Sun J, Jin Z, Guo X, Qiu Y, Zhu Y, and Tong S (2011). Impaired neuronal synchrony after focal ischemic stroke in elderly patients. Clin. Neurophysiol 122, 21-26. [PubMed: 20591730]
- Yarkoni T (2009). Big Correlations in Little Studies: Inflated fMRI Correlations Reflect Low Statistical Power-Commentary on Vul et al. (2009). Perspect. Psychol. Sci 4, 294-298. [PubMed: 26158966]
- Yeh FC, and Tseng WYI (2011). NTU-90: a high angular resolution brain atlas constructed by q-space diffeomorphic reconstruction. Neuroimage 58, 91-99. [PubMed: 21704171]
- Yeh FC, Verstynen TD, Wang Y, Fernández-Miranda JC, and Tseng WYI (2013b). Deterministic diffusion fiber tracking improved by quantitative anisotropy. PLoS One 8, e80713. [PubMed: 24348913]
- Yeh FC, Panesar S, Fernandes D, Meola A, Yoshino M, Fernandez-Miranda JC, Vettel JM, and Verstynen T (2018). Population-averaged atlas of the macroscale human structural connectome and its network topology. Neuroimage 178, 57-68. [PubMed: 29758339]
- Yourganov G, Fridriksson J, Rorden C, Gleichgerrcht E, and Bonilha L (2016). Multivariate Connectome-Based Symptom Mapping in Post-Stroke Patients: Networks Supporting Language and Speech. J. Neurosci 36, 6668-6679. [PubMed: 27335399]
- Yuan B, Fang Y, Han Z, Song L, He Y, and Bi Y (2017). Brain hubs in lesion models: Predicting functional network topology with lesion patterns in patients. Sci. Rep 7, 17908. [PubMed: 29263390]

Zimmermann J, Ritter P, Shen K, Rothmeier S, Schirner M, and McIntosh AR (2016). Structural architecture supports functional organization in the human aging brain at a regionwise and network level. Hum. Brain Mapp 37, 2645-2661. [PubMed: 27041212]

### Highlights

- White matter structural disconnections explain brain network dysfunction after stroke
- Damage to the gray matter, including 'hub' regions, provides less explanatory power
- Interhemispheric disconnections are linked to widespread functional disruptions
- Disconnection and disruption are topographically linked within functional networks

*[picture on PDF page 35]*

**Figure labels:**
- A
- B
- Structural
- Regional GM
- WMStructural
- Voxel-based
- Region-based
- Tract-based
- MRI
- Parcels
- Connectome Atlas
- damage
- SDC

*[picture on PDF page 35]*

**Figure labels:**
- C
- D
- Across-Patient Overlap Distributions
- 0.4
- Proportion of Voxels/Connections
- Voxel Damage
- in Across-Patient Overlap Map
- Regional SDC
- 0.35
- 0.3
- Dmg
- SDC
- 0.25
- Max=18
- Max=47
- 0.2
- Number of Patients with Damage
- 18
- 0.15
- 0.1
- 0.05
- 10
- 20
- 30
- 40
- 50
- 60
- Number of Patients with Damage/SDC
- Number of Patients with SDC
- 47

- (A) Structural data and atlases. From left to right: T2-weighted structural MRI scan from a single patient, regional GM parcellation, and diffusion MRI structural connectome atlas.
- (B) Example structural measures. From left to right: voxel damage, regional GM damage, tract-based SDC, and region-based SDC measures for a single patient.
- (C) Topographies of voxel damage (top) and region-based SDC (bottom) overlap across patients. Colormaps represent the number of patients with damage (top) and disconnection (bottom) at each voxel and connection, respectively. For SDC overlaps, lines represent connections and colored spheres represent regions. Sphere colors correspond to network assignments shown in Figure S2A.
- (D) Bar heights (y axis) indicate the proportion of voxels (blue) and connections (orange) in the across-patient overlap maps that are damaged in different numbers of patients (x axis). Dashed lines correspond to the maximum number of patients with damage and disconnection at any voxel and connection, respectively.

A

*[picture on PDF page 36]*

**Figure labels:**
- Connector Hubness
- B
- Model 1
- Model 2
- Standardized Beta
- 0
- *
- -0.5
- Adj. R²=0.10, FDRp<0.001
- Adj. R²=0.25, FDRp<0.001
- -1
- Participation Coefficient (PC)
- Provincial Hubness
- PC Dmg
- WMD Dmg
- Total SDC
- Model 3
- 0.5
- Adj. R²=0.24, FDRp<0.001
- Within-Module Degree (WMD)
- -3
- Lesion Vol
- C
- Correlations with Modularity
- Adjusted for Lesion Volume
- Partial Correlation (r)
- Correlation (r)
- -0.1
- n.s
- -0.2
- -0.3
- -0.4

- (A) FC participation coefficients (top) and within-module degree Z scores (bottom) for each cortical region in the mean control FC matrix.
- (B) Standardized betas (y axes) for structural measure predictor effects (x axes) from three nested regression models of network modularity in the patient group (n = 114). Error bars correspond to 95% CIs.
- (C) Correlations (left, y axis) and partial correlations (right, y axis) between structural measures (x axes) and modularity. *FDR, p < 0.05.

See also Figure S2.

*[picture on PDF page 37]*

**Figure labels:**
- A
- Mean IH
- DAN-DMN
- Modularity
- 0.6
- 2
- Model
- 0.4
- 0.2
- 0
- Region SDC
- Tract SDC
- Voxel Dmg
- Region Dmg
- Voxel
- VIS IH
- SMD IH
- SMV IH
- 0.3
- 0.1
- AUD IH
- CON IH
- VAN IH
- DAN IH
- FPN IH
- DMN IH
- B
- Ncomp
- C
- AIC Weights
- Best Models
- 8
- 3
- 0.8
- # Best Models
- 6
- 4
- DMNIH
- 1

- (A) PLSR model fits and family-wise error (FWE)-corrected 95% CIs. Plots show R 2  values (y axes) for different anatomical models (x axes) of each FC measure obtained from the patient group (n = 114).
- (B) Number of components included in each anatomical model (x axis) of each FC measure (y axis) as determined by jackknife cross-validation.
- (C) Left: model AIC weights for each anatomical model (x axis) of each FC measure (y axis). Right: number of times (y axis) each anatomical model (x axis) was selected as the best model of the set. The red boxes highlight distinct core FC disruptions. See also Figures S2 and S3.

A

FC Correlation SDC Weight Correlation FPN

DMN

Mean IH

DAN-DMN

Modularity

B

0.5

0

Positive Weights with Significant 99% Cls (Region-based SDC Models)

0.08

0.07

0.06

0.05

0.04

0.03

Rescaled Betas

0.02

0.01

Mean IH

t

DAN-DMN

ner:

0.12

0.1

0.08

0.06

0.04

0.02

WN BN WN BN

WN BN WN BN

Network Type

Interhemispheric

0.035

0.03

0.025

0.02

0.015

0.01

0.005

WN BN WN BN

WN:Within-Network

Intrahemispheric

----80th percentile

*[picture on PDF page 38]*

**Figure labels:**
- C
- Top 20% Positive Weights with Significant 99% Cls (Region-based SDC Models)
- Mean IH
- DAN-DMN
- Modularity
- Interhemispheric
- Intrahemispheric
- FC Network Affiliations
- Default Mode (DMN)
- V. Attention (VAN)
- Auditory (AUD)
- Somatomotor. V. (SMV)
- Fronto-Parietal (FPN)
- Cing-Opercular (CON)Visual (VIS)
- OOther/None
- D. Attention (DAN)
- Salience (SAL)
- Somatomotor. D. (SMD)

- Figure 4. Disconnection Patterns Associated with Core FC Disruptions (A) Correlations among the different FC measures (bottom triangle) and among the PLSR weight vectors from the region-based SDC models (top triangle). (B) Distributions of significant region-based SDC weights associated with reduced
- interhemispheric within-network FC, increased DAN-DMN FC, and reduced modularity in the patient group (n = 114). Weights are shown separately for different network and hemispheric connection types. Data points correspond to single connections. Dashed lines correspond to 80 th  percentile cutoffs of thresholded weights (points above these lines are plotted in C). Means and SDs are shown as line plots and error bars. (C) Brain plots show top 20% of weights in (B). See also Figures S4 and S5.

BN:Between-Network

Modularity

*[picture on PDF page 39]*

**Figure labels:**
- A
- B
- C
- LV1 Loading Bootstrap Ratios (BSRs)
- LVs Explaining > 1% Covariance
- LV1 Score Correlation
- LV1 SDC BSRs
- LV1 FC BSRs
- % Covariance Explained
- 5
- 40
- 45% covariance*
- 20
- LV1 FC Score
- 30
- 10
- 21% covariance*
- BSR
- 0
- -10
- *Significant 99% Cl
- -5
- 1 2 3 4 5 6 7
- 8
- 9 10
- WN BN WN BN
- Latent Variable
- LV1 SDC Score
- Network Type
- Interhemispheric
- WN:Within-Network
- Intrahemispheric
- BN:Between-Network
- |BSR| = 2.5 (Significance Threshold)

*[picture on PDF page 39]*

**Figure labels:**
- D
- Topographies of Linked SDC and FC Patterns (Summarized by Top Loadings with |BSR| > 2.5)
- LV1 Structural Pattern
- LV1 Functional Pattern
- SDC+
- FC-
- FC+
- (Interhemispheric)
- (Intrahemispheric)
- 1
- FC Network Affiliations
- Default Mode (DMN)
- OV. Attention (VAN)
- Auditory (AUD)
- Somatomotor. V. (SMV)
- Fronto-Parietal (FPN)
- Cing-Opercular (CON)
- Visual (VIS)
- OOther/None
- D. Attention (DAN)
- Salience (SAL)
- OSomatomotor. D. (SMD)

- (B) Relationship between patient SDC (x axis) and FC (y axis) scores for LV1.
- (C) LV1 SDC (left plot) and FC (right plot) BSRs (y axes) for different connection type categories (x axes). Dots correspond to individual connections. Dashed lines denote significance thresholds.
- (D) Multivariate SDC and FC topographies linked by LV1. Brain images show top 20% of significant positive (shown in red) and negative (shown in blue) loadings for SDC and FC patterns with significant BSRs (i.e., data points above and/or below dashed lines in C). See also Figures S6 and S7.

*[picture on PDF page 40]*

**Figure labels:**
- A
- LV1 FC Score Correlations with a priori FC Measures
- r=-0.92*
- FC
- 0.4
- r=0.63*
- 0.3
- r=-0.67*
- DAN-DMN
- Mean IH FC
- 0.2
- FC Modularity
- 1
- 0
- 0.1
- Ipsilesional
- -0.2
- -0.1
- -0.4
- -10
- 10
- 20
- -20
- 40
- LV1 FC Score
- LV1 SDC Score Correlations with a priori FC Measures
- r=-0.65*
- C
- F
- r=0.47*
- 0.25
- r=-0.51*
- ..
- 0.15
- lesional
- "
- 0.05
- Ipsile
- -0.3
- LV1 SDC Score
- B
- Behavioral Correlation
- Adjusted for Lesion Volume
- Correlation
- *
- Partial
- SDC
- -0.6
- -0.5
- Lang
- Att
- Motor
- MemS
- MemV

*[picture on PDF page 41]*

**Figure labels:**
- A
- Unthresholded LV1 SDC Loadings (Cortical)
- Unthresholded LV1 FC Loadings
- Left Hemisphere
- 300
- 100
- 250
- 50
- 0
- 200
- 国
- ::
- -50
- Right Hemisphere
- 31
- 11
- 150
- -100
- 江酒馆
- -150
- -200
- :
- -4
- -250
- FC Network Affiliations
- Default Mode (DMN)
- V. Attention (VAN)
- Auditory (AUD)
- Somatomotor. V. (SMV)
- Fronto-Parietal (FPN)
- Cing-Opercular (CON)
- Visual (VIS)
- OOther/None
- D. Attention (DAN)
- Salience (SAL)
- OSomatomotor. D. (SMD)
- B
- All Loadings
- C
- Interhemispheric (WN)
- Interhemispheric (BN)
- r=-0.15*
- r=-0.35*
- f=-0.06
- FC Loading
- Intrahemispheric (WN)
- Intrahemispheric (BN)
- LV1
- r=-0.47*
- r=-0.03
- 50 100 150
- 100 150
- LV1 SDC Loading

(A) Unthresholded LV1 SDC (left; cortical only) and FC (right) loadings obtained from PLSC of data from the patient group (n = 114). Matrices are organized as in Figure S2. (B) Relationship between LV1 SDC (x axis) and FC (y axis) loadings.

- (C) Relationships for different connection type categories (WN, within-network; BN, between-network). *FDR, p < 0.05.

See also Figures S6 and S8.

### KEY RESOURCES TABLE

| REAGENT or RESOURCE | SOURCE | IDENTIFIER |
|---|---|---|
| Software and Algorithms |   |   |
| MATLAB2015a | The MathWorks | RRID:SCR_001622 |
| DSLstudio | Fang-Chen Yeh, DSLstudio | RRID: SCR_009557; dsi-studio.labsolver.org/ |
| Connectome Workbench | Marcus et al., 2011 | RRID:SCR_008750; https://www.humanconnectome.org/software/ get-connectome-workbench |
| Freesurfer | Dale et al., 1999 | RRID: SCR_001847; http://surfer.nmr.mgh.harvard.edu/ |
| Brain Connectivity Toolbox | Rubinov and Sporns, 2010 | RRID:SCR_004841; http://sites.google.com/site/bctnet/ |
| GRETNA | NITRC | RRID: SCR_009487; https://www.nitrc.org/projects/gretna/ |
| Analyze | Robb and Hanson, 1991 | RRID: SCR_005988; https://analyzedirect.com/analyze-12-0/ |
| Surflce | NITRC | https://www.nitrc.org/projects/surfice |
| MRICroGL | NITRC | https://www.nitrc.org/projects/mricrogl |
| 4dfp_tools | NIL | ftp://imaging.wustl.edu/pub/raichlab/4dfp_tools/ |
| paq | Herve Abdi | https://www.utdallas.edu/~herve/ |
| plotSpread | MATLAB Central | https://www.mathworks.com/matlabcentral/fileexchange/37105-plot- spread-points-beeswarm-plot |
| matlab_nifti | MATLAB Central | RRID:SCR_016895; https://www.mathworks.com/matlabcentral/fileexchange/8797-tools- for-nifti-and-analyze-image |
| Other |   |   |
| Gordon rsfMRI parcellation | Gordon et al., 2016 | https://sites.wustl.edu/petersenschlaggarlab/resources/ |
| AAL Atlas | Tzourio-Mazoyer et al., 2002 | RRID:SCR_003550; http://www.gin.cnrs.fr/en/tools/aal-aal2/ |
| Harvard-Oxford Subcortical Atlas | Harvard Center for Morphometric Analysis | RRID:SCR_001476; https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/Atlases |
| HCP-842 Diffusion MRI Tractography Atlas | Yeh et al., 2018 | brain.labsolver.org/diffusion-mri-templates/tractography |