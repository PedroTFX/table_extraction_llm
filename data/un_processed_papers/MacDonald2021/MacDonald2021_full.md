<!-- page 1 of 16 -->

0

Check for updates

## ECOGRAPHY

## Research

# Distinguishing effects of area per se and isolation from the sample-area effect for true islands and habitat fragments

**Zachary G. MacDonald, David C. Deane, Fangliang He, Clayton T. Lamb, Felix A. H. Sperling, John H. Acorn and Scott E. Nielsen**

Z. G. MacDonald (https://orcid.org/0000-0002-7966-5712) ✉ (zmacdona@ualberta.ca), D. C. Deane (https://orcid.org/0000-0003-2144-624X), F. He (https://orcid.org/0000-0003-0774-4849), J. H. Acorn (https://orcid.org/0000-0001-6570-1949) and S. E. Nielsen (https://orcid.org/0000-0002-9754-0630), Dept of Renewable Resources, Univ. of Alberta, Edmonton, Alberta, Canada. – C. T. Lamb (https://orcid.org/0000-0002-1961-0509), Univ. of British Columbia, Dept of Biology, Kelowna, British Columbia, Canada. – F. A. H. Sperling (https://orcid.org/0000-0001-5148-4226), Dept of Biological Sciences, Univ. of Alberta, Edmonton, Alberta, Canada.

## Ecography

**44: 1051–1066, 2021**

doi: 10.1111/ecog.05563

Subject Editor: Henrique Pereira

Editor-in-Chief: Miguel Araújo

Accepted 21 March 2021

![Image block](doc:cfca8f8/tier:advanced/page:1/block:14)

NSO

NORDIC SOCIETY OIKOS

www.ecography.org

The island species area relationship (ISAR) is an important tool for measuring variation in species diversity in variety of insular systems, from true-island archipelagoes to fragmented terrestrial landscapes. However, it suffers from several limitations. For example, due to the sample-area effect, positive relationships between species and area cannot be directly interpreted as evidence for deterministic effects of area per se. Additionally, richness-based analyses may obscure species-level responses to area and isolation that may better inform conservation practice. Here, we use random placement models to control for variation in abundance, occupancy and richness associated with the sample-area effect, allowing deterministic effects of area and isolation, and how they vary with species’ functional traits, to be resolved using linear mixed effects models. We demonstrate the utility of this approach using a butterfly assemblage persisting on a naturally fragmented landscape of lake islands. The ISAR did not significantly deviate from random placement in relation to island area, isolation or habitat diversity, supporting stochastic assembly consistent with the sample-area effect. Such inferences support the habitat amount hypothesis, which prioritizes preserving the maximum amount of habitat irrespective of its degree of fragmentation. However, species-level analyses demonstrated that species’ abundances were significantly lower on both smaller and more isolated islands than what is predicted by the sample-area effect. Moreover, effects of area per se were significantly greater for smaller, less mobile and rare species. Species’ occurrences also significantly deviated from predictions of the sample-area effect in relation to island isolation. Thus, our approach illustrates that richness-based analyses not only result in incorrect inferences on mechanisms underlying ISARs, but also obscure important effects of area per se and isolation on individual species that vary with functional traits. We therefore suggest that these effects should not be solely inferred from richness-based analyses, but rather evaluated on a speciesby-species basis.

Keywords: functional traits, habitat amount hypothesis, habitat fragmentation, island biogeography, sampling effects, species–area relationship

<small><span class="docvortex-page-footnote" data-block-type="page_footnote" style="color:#6b7280">© 2021 The Authors. Ecography published by John Wiley & Sons Ltd on behalf of Nordic Society Oikos This is an open access article under the terms of the Creative Commons Attribution License, which permits use, distribution and reproduction in any medium, provided the original work is properly cited. 10 1 1051</span></small>

<!-- page 2 of 16 -->

## Introduction

From true islands to habitat fragments on terrestrial landscapes, positive relationships between species richness and the area of islands or fragments are among the oldest and most widely documented patterns in ecology (Arrhenius 1921, MacArthur and Wilson 1963, Rosenzweig 1995, Gotelli and Graves 1996, He and Legendre 2002, Hanski  et  al. 2013). These island species-area relationships (ISARs, sensu Triantis et al. 2012, or ‘Type IV’ curves, sensu Scheiner 2003) have received considerable attention, in part due to their importance to conservation frameworks (reviewed by Shafer 1990, Lomolino 2000, Whittaker and Fernández-Palacios 2007). Although there are several documented divergences between the biogeographies of true islands and terrestrial habitat fragments (Laurance 2008, Mendenhall et al. 2014, Itescu 2019, Farneda  et  al. 2020), studies addressing trueisland systems can still help resolve what mechanisms underlie ISARs and how fragmentation effects are best measured (Diamond 1975, Simberloff and Abele 1976, 1982, Haila 2002, Haddad  et  al. 2015, MacDonald  et  al. 2018a, b). There are, however, at least two enduring problems with the use of ISARs in conservation that are generalizable to both true islands and habitat fragments: 1) ISARs may emerge from a combination of different mechanisms, each of which potentially informs a different conservation directive (Connor and McCoy 1979, Kadmon and Allouche 2007, MacDonald et al. 2018b); and 2) ISARs are emergent patterns of diversity that can mask differential responses to habitat area among species that may require independent consideration for successful conservation planning (Ewers and Didham 2006, Öckinger et al. 2009, Franzén et al. 2012, Hanski 2015, MacDonald et al. 2018a). Here, we propose an approach to addressing each of these problems within a single modelling framework.

## Mechanisms underlying ISARs

Three hypotheses, each with distinct underlying mechanisms and conservation implications, have been proposed to account for ISARs and related spatial patterns of species richness: 1) the passive sampling hypothesis (Connor and McCoy 1979); 2) area per se, as outlined by the theory of island biogeography (MacArthur and Wilson 1963, Wilson and MacArthur 1967); and 3) the habitat diversity hypothesis (Williams 1964). The passive sampling hypothesis, originally developed within the context of oceanic islands, predicts that islands randomly sample individuals from the regional species pool in abundances proportional to their area (Connor and McCoy 1979). As larger islands sample more individuals, they sample more species according to the abundance distribution of the regional species pool (i.e. the ‘sample-area effect’). Thus, passive sampling serves as a useful null hypothesis, assuming random assembly of both individuals and species.

Area per se hypothesizes a disproportionate reduction in species richness as island area decreases, steepening the

slope of ISARs within archipelagoes or fragmented terrestrial landscapes relative to species–area relationships within landscapes comprised of continuous habitat (Diamond 1972, 1975, Wilson and Willis 1975, Connor and McCoy 1979, Saccheri  et  al. 1998, Gonzalez 2000, Haila 2002, Haddad et al. 2015, MacDonald et al. 2018a, b). From a mechanistic perspective, area per se essentially invokes the theory of island biogeography, where species richness arises as a dynamic equilibrium between rates of extinction and colonization, which in turn depend on island area and isolation (MacArthur and Wilson 1963, Wilson and MacArthur 1967). More isolated populations occupying small islands are predicted to be more prone to stochastic extinction and small, isolated islands are less likely to be re-colonized from external source populations than larger, well-connected islands (Levins 1969, Hanski and Gyllenberg 1993, Orrock and Watling 2010). Thus, the theory of island biogeography addresses effects of both island area and isolation, pre-dicting that immigration rates and rescue effects decrease as islands become increasingly isolated from neighboring habitat (i.e. the mainland or other islands), negatively affecting species’ probabilities of occurrence and therefore species richness (MacArthur and Wilson 1963, Wilson and MacArthur 1967, Brown and Kodric-Brown 1977, Hanski 1994, 1998, 1999).

As an alternative to dynamic balances between demographic rates predicted by the theory of island biogeography, Williams (1964) proposed that ISARs are driven by variation in habitat diversity among islands. The habitat diversity hypothesis predicts that island/fragment area correlates with species richness only insofar as area correlates with the intermediate variable of habitat diversity; larger sample areas generally contain more habitats, which support more species (Williams 1964, Nilsson  et  al. 1988, Rosenzweig 1995, Gotelli and Graves 1996). It follows that the presence or proportion of suitable habitat within islands/fragments should affect abundances and occurrences of individual species (Buckley 1982, Haila and Järvinen 1983). However, few studies have investigated how habitat associations of single species relate to emergent patterns of species richness in this context (but see Haila et al. 1983). Still, multiple studies addressing species richness support the habitat diversity hypothesis (Nilsson et al. 1988, Kadmon and Allouche 2007, Hortal  et  al. 2009). It has also been inferred that mechanisms predicted by the passive sampling hypothesis, theory of island biogeography and habitat diversity hypothesis may simultaneously contribute to ISARs (Connor and McCoy 1979, Kadmon and Allouche 2007, MacDonald et al. 2018b, Chase et al. 2019).

## Complications in extending ISARs to conservation

Due to its success on true islands, conservation biologists were quick to recognize the potential for the theory of island biogeography to be applied to fragmented habitat on terrestrial landscapes, initially in the design of nature reserves (Diamond 1972, 1975, Wilson and Willis 1975). However,

1052

1600587, 2021, 7, Downloaded from https://nsojournals.onlinelibrary.wiley.com/doi/10.1111/ecog.05563 by Faculdade Medicina De Lisboa, Wiley Online Library on [05/11/2025]. See the Terms and Conditions (https://onlinelibrary.wiley.com/terms-and-conditions) on Wiley Online Library for rules of use; OA articles are governed by the applicable Creative Commons License

<!-- page 3 of 16 -->

the extension of ISAR-based inferences from true islands to habitat fragments is complicated by differences in their extents of insularity and interactions between habitat and non-habitat (i.e. matrix) areas (Itescu 2019). Whereas edges of true islands clearly delimit suitable habitat from a homogeneous matrix of unsuitable habitat (open water), species occurring on habitat fragments may utilize resources of heterogeneous terrestrial matrices and these matrices may differentially constrain or facilitate colonization rates of species (i.e. ‘matrix effects’; Dunning  et  al. 1992, Ricketts 2001). Thus, understanding habitat fragments as analogous to true islands may be problematic. More specifically, fragmentation effects observed within true-island systems may differ from those typical of fragmented terrestrial landscapes (Laurance 2008, Mendenhall et al. 2014, Farneda et al. 2020).

## SLOSS-based inferences

Irrespective of the mechanisms underlying ISARs, observations that species richness generally decreases as island/frag ment area decreases and isolation increases have contributed to long-standing inferences that habitat fragmentation poses a major threat to species diversity (Diamond 1972, 1975, Noss 1991, Haila 2002, Hanski 2015, Fletcher et al. 2018). However, many of these inferences are founded on observations or experimental designs that have not sufficiently decoupled the effects of area per se and isolation from the sample-area effect (i.e. decoupled habitat fragmentation from habitat loss; sensu Fahrig 2003, 2013, 2017, Hadley and Betts 2016). In the majority of studies successfully decoupling habitat fragmentation from habitat loss, single large habitat fragments are generally found to contain an equivalent or lesser number of species than sets of several small habitat fragments summing to an equivalent total area (Quinn and Harrison 1988, Fahrig 2003, 2013, 2017, 2020, Yaacobi et al. 2007, MacDonald et al. 2018a, b, Deane et al. 2020). Such comparisons contribute to the ongoing single-large-or-severalsmall (‘SLOSS’) debate, addressing how finite conservation efforts should prioritize the area and configuration of fragmented habitat and nature reserves (Diamond 1975, Abele and Connor 1979, Ovaskainen 2002, Tjørve 2010). In light of SLOSS-based observations that species richness is often equal or greater within sets of several small habitat fragments, Fahrig (2013) advanced the habitat amount hypothesis, pre-dicting that the number of species persisting on fragmented landscapes is only a function of total habitat amount at the landscape scale irrespective of its spatial subdivision and configuration. The principal mechanism underlying the habitat amount hypothesis is the sample-area effect, as originally articulated by the passive sampling hypothesis (Connor and McCoy 1979). However, the habitat amount hypothesis extends implications of the sample-area effect to predict that there should also be no detectable effect of fragment isolation on species’ abundances, species’ occurrences or species richness after the sample-area effect has been accounted for (Fahrig 2013).

## The importance of understanding how species-level patterns affect ISARs

While the sample-area effect surely contributes to patterns of species richness within a variety of true-island systems and fragmented terrestrial landscapes, richness-based analyses may obscure important effects of both area per se and isolation on individual species (Ewers and Didham 2006, Öckinger et al. 2009, Franzén et al.2012, Hanski 2015, MacDonald  et  al. 2018a). Indeed, area per se and isolation effects have been inferred to vary widely among species, even within single landscapes and taxa (Henle et al. 2004, Ewers and Didham 2006, Nowicki  et  al. 2007, Öckinger  et  al. 2009, Hanski 2015, Hillebrand et al. 2018, MacDonald et al. 2018a). Functional traits, including body size (Gehring and Swihart 2003, Henle et al. 2004, Larsen et al. 2008, Prugh et al. 2008, Barbaro and Van Halder 2009, Warzecha et al. 2016), mobility/dispersal ability (Roland and Taylor 1997, Lens et al. 2002, Ewers and Didham 2006, Öckinger et al. 2009, MacDonald et al. 2018a, 2019), degree of ecological specialization (Tscharntke and Brandl 2004), rarity/conservation status (Ewers and Didham 2006) and trophic position (Tscharntke et al. 2002, Thies et al. 2005, Ewers and Didham 2006) are hypothesized to relate species’ sensitivity to area per se and isolation. Still, relatively few empirical studies have investigated how functional traits relate to interspecific variation in responses to area per se and isolation or how this interspecific variation scales to emergent patterns of species richness, such as those reflected in ISARs (Melbourne  et  al. 2004, but see Barbaro and Van Halder 2009, Öckinger et al. 2009).

## Distinguishing mechanisms underlying ISARs

Due to the sample-area effect, observations that species abundances, species’ probabilities of occurrence or species richness positively correlate with island/fragment area cannot be directly interpreted as evidence of effects of area per se (Connor and McCoy 1979, Fahrig 2003, 2013, 2017, Fletcher  et  al. 2018). Three established methods may be used to control for the sample-area effect: 1) comparing sets of islands/fragments that sum to equal areas but differ in degree of fragmentation, including the nested-set designs of Yaacobi  et  al. (2007) and MacDonald  et  al. (2018a, b) and comparisons of species accumulation curves proposed by Quinn and Harrison (1988); 2) extrapolating a speciesarea regression to the total area of all islands/fragments used to build the regression and comparing predicted and observed species richness (γ-diversity) (Rosenzweig 2004, Yaacobi et al. 2007, Santos et al. 2010, Gavish et al. 2012, MacDonald  et  al. 2018a, b); and 3) comparing equal-area sampling plots across islands/fragments (Westman 1983, Stevens 1986, Quinn  et  al. 1987, Kelly  et  al. 1989, Fahrig 2013, Watling et al. 2020). However, for methods 1 and 2 (SLOSS-based comparisons), substantial species turnover among several small islands/fragments can increase their aggregate richness relative to single large islands/fragments,

1053

16000587, 2021, 7, Downloaded from https://nsojournals.onlinelibrary.wiley.com/doi/10.1111/ecog.05563 by Faculdade Medicina De Lisboa, Wiley Online Library on [05/11/2025]. See the Terms and Conditions (https://onlinelibrary.wiley.com/terms-and-conditions) on Wiley Online Library for rules of use; OA articles are governed by the applicable Creative Commons License

<!-- page 4 of 16 -->

such that important effects of area per se on individual species are obscured (sensu Simberloff 1976, MacDonald et al. 2018b, Deane et al. 2020). Assuming species are uniformly distributed within islands/fragments, inferences drawn from method 3 may be robust for sessile taxa (e.g. vascular plants; Westman 1983, Quinn  et  al. 1987, Kelly  et  al. 1989), but remain tenuous for vagile species that move frequently within islands/fragments, as individual sampling plots may accumulate all vagile species within single islands/fragments if sampling effort is high. Additionally, if rare species are particularly sensitive to area per se or isolation, these effects are likely to go undetected when sampling at small spatial grain sizes dictated by method 3; rare species and important habitat types within islands/fragments may be missed entirely in comparisons of small sampling plots (Karger  et  al. 2014). Finally, each of the three established methods only contrast the sample-area effect with those of area per se (methods 1 and 2) or area per se and isolation (method 3); evaluating effects of isolation and habitat diversity requires additional analyses. A fourth method, recently proposed by Chase et al. (2019), employs parameters derived from individual-based rarefaction curves across various spatial scales within islands/fragments to distinguish between the sample-area effect and effects of area per se and habitat diversity. While this framework can effectively resolve mechanisms underlying ISARs, it cannot simultaneously evaluate effects of isolation, assess whether area per se and isolation differentially affect species in relation to their functional traits, or be applied to existing datasets lacking abundance data for subplots stratified within each island/ fragment across diagnosable habitat heterogeneity.

In this paper, we present a novel application of random placement and linear mixed effects models that can simultaneously evaluate: 1) how area per se, isolation, and habitat diversity affect species’ abundances, species’ occurrences and species richness across true islands or terrestrial habitat fragments; and 2) whether interspecific variation in these responses relates to variation in species’ functional traits. This modelling framework is applicable to any dataset for which abundance data were collected for sets of true islands or habitat fragments with sampling effort standardized per unit area. We assess the utility of the framework using a butterfly assemblage persisting on a naturally fragmented landscape of true islands; Lake of the Woods, Canada. Methodological developments and basic inferences presented here are equally applicable to both true islands and terrestrial habitat fragments, so long as the edges of habitat fragments can be consistently delimited.

## Material and methods

## Overview of the modelling framework

Starting with the assumption that all individuals of each species are randomly distributed across true islands or habitat fragments in abundances proportional to their areas, random placement models can be used to calculate expected species’

abundances, expected probabilities of species’ occurrences and expected species richness for each island or fragment (Arrhenius 1921, Coleman 1981, Gotelli and Graves 1996, He and Legendre 2002). Resulting random placement values are equivalent to values of species’ abundances, species’ probabilities of occurrence and species richness predicted by the sample-area effect. Predictions of the passive sampling/ habitat amount hypotheses, theory of island biogeography and habitat diversity hypothesis may be then simultaneously evaluated by modelling relationships between random placement residuals (observed values minus random placement values) and the area, isolation and habitat diversity of individual islands/fragments. Variables measuring species’ functional traits may be introduced to abundance and occurrence models via interaction terms with island/fragment area and isolation to evaluate whether effects of area per se and isolation interspecifically vary contingent on the measured traits.

## Random placement models

We present random placement models in ascending order of mathematical complexity, from species’ abundances, to species’ occurrences, to species richness. Within random placement models, $a _ { i }$ is the area of the jth island/fragment, $A _ { T }$ is the total area of all islands/fragments, $n _ { i }$ is the abundance of species i summed across all islands/fragments and S is the total number of species observed. Islands or fragments that were not surveyed are not included in random placement models. According to the sample-area effect, the expected abundance of species i on island/fragment j is simply proportional to $j s$ area (model 1) and the occurrence probability follows the random placement model (model 2). The random placement model for expected richness on any island/fragment is simply the sum of the expected probabilities of occurrence over all species (model 3). This random placement richness model was first proposed a century ago by Arrhenius (1921) and later reinvented by Coleman (1981) with the inclusion of the variance.

$$
E \left(n _ {i j}\right) = n _ {i} \left(\frac {a _ {j}}{A _ {T}}\right) \tag {1}
$$

$$
E \left(O _ {i j}\right) = 1 - \left(1 - \frac {a _ {j}}{A _ {T}}\right) ^ {n _ {i}} \tag {2}
$$

$$
E \left(S _ {j}\right) = \sum_ {i = 1} ^ {S} \left\{1 - \left(1 - \frac {a _ {j}}{A _ {T}}\right) ^ {n _ {i}} \right\} \tag {3}
$$

## Modelling of random placement residuals

Subtracting random placement abundance and occurrence probability values from observed abundance and occurrence values for each species on each island/fragment produces

16000587, 2021, 7, Downloaded from https://nsojournals.onlinelibrary.wiley.com/doi/10.1111/ecog.05563 by Faculdade Medicina De Lisboa, Wiley Online Library on [05/11/2025]. See the Terms and Conditions (https://onlinelibrary.wiley.com/terms-and-conditions) on Wiley Online Library for rules of use; OA articles are governed by the applicable Creative Commons License

1054

<!-- page 5 of 16 -->

abundance and occurrence residuals. The direction and magnitude of these residuals measure how abundances and occurrences of each species deviate from predictions of the sample-area effect. In the modelling framework described below, all species’ abundance residuals and all species’ occurrence residuals are concatenated across species for use in single linear mixed effects models; one model addressing all species abundances and one model addressing all species’ occurrences. Abundance residuals require standardization (subtracting the mean and dividing by standard deviation) before concatenation across species, as the range of possible values is greater for common species than rare species. While this is not the case for occurrence residuals (values bound between −1 and 1), standardization is still recommended to generate values that are commensurate among species. Richness residuals are similarly calculated for each island/fragment by subtracting random placement richness values from observed richness values. Standardization is recommended to facilitate comparisons of effect sizes among abundance, occurrence and richness analyses.

## Species’ abundances and occurrences

Linear mixed effects models are used to relate abundance and occurrence residuals to island/fragment variables while controlling for species identity as a random effect. If area per se affects species’ abundances or occurrences beyond variation associated with the sample-area effect, residuals will be positively related to area, indicating a disproportionate concentration of species’ abundances or occurrences on larger islands/ fragments. If isolation negatively affects species’ abundances or occurrences, residuals will be negatively related to measures of isolation specific to individual islands/fragments, indicating a disproportionate concentration of species’ abundances or occurrences on less isolated islands/fragments. Each of these results align with predictions of the theory of island biogeography. Alternatively, the absence of significant relationships between residuals and area or isolation would indicate that the sample-area effect sufficiently accounts for variation in species’ abundances or occurrences across islands/ fragments of varying area or isolation. The combination these results would confer support for the passive sampling/habitat amount hypotheses. The proportion of species-specific suitable habitat and presence of species-specific resources within each island/fragment may also be included in linear mixed effects models. Positive relationships between abundance or occurrence residuals and these variables would indicate that availability of specific habitats or resources within islands/ fragments are important considerations that affect species abundances or occurrences, as predicted by the habitat diversity hypothesis.

If data on species’ functional traits are available, functional trait variables may be introduced to linear mixed effects models via interaction terms with island/fragment area and isolation. Here, a significant interaction between a functional trait variable and island/fragment area or isolation would indicate that area per se or isolation differentially affects species’ abundances or occurrences contingent on the measured trait. Total

abundance and number of occurrences (prevalence) for each species are also of interest, as rarity is cited as a predictor of species’ sensitivity to fragmentation (Ewers and Didham 2006). A significant positive interaction between total abundance or prevalence and island/fragment area would indicate that rare species are disproportionately concentrated or likely to occur on larger islands/fragments. Similarly, a significant negative interaction between total abundance or prevalence and island/fragment isolation would indicate that rare species are disproportionately concentrated or likely to occur on less isolated islands/fragments.

## Species richness

A similar modelling process may be applied to species richness using linear models. Significant relationships between richness residuals and island/fragment area or isolation would indicate that area per se or isolation significantly affects richness after controlling for the sample-area effect. Each of these results align with predictions of the theory of island biogeography. Conversely, the absence of significant relationships between residuals and area and isolation would indicate that the sample-area effect sufficiently accounts for variation in species richness across islands/fragments of varying area or isolation. This combination of results would suggest that only habitat amount at the archipelago- or landscape-scale affects richness, as predicted by the passive sampling/habitat amount hypotheses. Predictions of the habitat diversity hypothesis may also be simultaneously evaluated by including measures of habitat diversity in linear models. Significant relationships between richness residuals and habitat diversity would indicate that, despite correlations between habitat diversity and island/fragment area, variation in habitat diversity among islands/fragments affects species richness beyond variation associated with both the sample-area effect and effects of area per se.

## Application of the modelling framework

## Study area

We assessed the utility of this modelling framework using a butterfly assemblage persisting on a \~1250 km<sup>2</sup> lake-island complex located in Sabaskong Bay, Lake of the Woods, Canada (Fig. 1). Differential isostatic rebound and outlet restriction resulted in the flooding of the study area and isolation of land-bridge islands approximately 3000–4000 YA (Yang and Teller 2005). Given this substantial time-sinceisolation, we infer that species assemblages have relaxed to equilibria (> 1000 generations; based on categories suggested by Fahrig 2020). Butterflies represent a suitable taxon for this investigation, as most species complete their life cycles within relatively small patches of habitat, their detectability is generally high and their diversity correlates with that of many other terrestrial taxa (Thomas 2005, Nowicki  et  al. 2008, MacDonald  et  al. 2017, 2018a). Butterflies do not utilize open water at any life stage, meaning the matrix separating islands in this system is entirely unsuitable. This effectively controls for matrix effects (Dunning  et  al. 1992, Ricketts

1055

16000587, 2021, 7, Downloaded from https://nsojournals.onlinelibrary.wiley.com/doi/10.1111/ecog.05563 by Faculdade Medicina De Lisboa, Wiley Online Library on [05/11/2025]. See the Terms and Conditions (https://onlinelibrary.wiley.com/terms-and-conditions) on Wiley Online Library for rules of use; OA articles are governed by the applicable Creative Commons License

<!-- page 6 of 16 -->

| Category | Description |
| --- | --- |
| Land | Green area representing land use |
| Water | Light blue area representing water usage |
| Study islands | Black cross markers indicating study locations (0.1 to 8 ha) |
| Isolation buffer | Yellow circles representing isolation buffers (e.g. 250 m) |

Figure 1. Map of the study area, located in Sabaskong Bay, Lake of the Woods, Canada. Butterfly abundance, occurrence and species richness data were collected for 30 study islands, varying in area from 0.09 to 8.4 ha, using repeated full island surveys.

2001), but also limits the generalizability of our inferred fragmentation effects to terrestrial landscapes (Laurance 2008, Mendenhall et al. 2014, Farneda et al. 2020).

Thirty islands, ranging in area from 0.1 to 8.0 ha, were randomly selected from lists of candidate islands compiled according to the methods of MacDonald  et  al. (2018a). Islands were only considered as candidates if they were isolated from other landmasses by at least 100 m, beyond the inferred visual ranges of butterflies (Rutowski 2003, MacDonald et al. 2019). The relative isolation of each study island was quantified at multiple scales as the proportion of water within 250-, 500-, 1000-, 1500-, 2000-, 2500-, 3000-, 3500-, 4000-, 4500- and 5000-m buffers. Buffers were generated from island edges, meaning isolation measures are independent from and uncorrelated with island area. We opted for these proportion-based measures because they have been shown to predict immigration rates, rescue effects and related ecological processes more accurately than distance-based measures (Moilanen and Nieminen 2002, Tischendorf et al. 2003, Prugh 2009). Habitat diversity was estimated on each island as the relative proportion of 14 habitat types, defined using structural properties of vegetation and geological features (Supporting information for habitat type descriptions).

## Survey protocol

Butterfly abundance data were collected for each of the 30 islands using repeated full-island surveys. Each island was visited four times at intervals between 10 and 14 days during the peak flight season (1 June 2015 to 20 Aug 2015). Sampling effort was standardized to 40 min per ha per survey across all islands, eliminating the need for sampling effort and diversity corrections (e.g. rarefaction or extrapolation, Chao  et  al. 2014, Fahrig 2020). Care was taken to visit all habitat types during each survey and handheld GPS units were used to ensure uniform coverage of islands. Recording observer tracks and capturing individuals whenever possible (kept as voucher specimens or released at the end of each survey) minimized the possibility of double counts, where individuals are recorded multiple times in single surveys. To ensure optimal and standardized butterfly activity, surveys were restricted to the hours of 10:45 to 15:45 and were not conducted in wind speeds over 15 km $\mathrm { h } ^ { - 1 }$ or in temperatures below $1 3 ^ { \circ } \mathrm { C } .$ If temperatures were below $1 7 ^ { \circ } \mathrm { C } ,$ surveys were only conducted in sunny conditions (cloud cover < 40%). Surveys were conducted in temperatures above $1 7 ^ { \circ } \mathrm { C } ,$ regardless of cloud cover (MacDonald et al. 2017).

1056

16000587, 2021, 7, Downloaded from https://nsojournals.onlinelibrary.wiley.com/doi/10.1111/ecog.05563 by Faculdade Medicina De Lisboa, Wiley Online Library on [05/11/2025]. See the Terms and Conditions (https://onlinelibrary.wiley.com/terms-and-conditions) on Wiley Online Library for rules of use; OA articles are governed by the applicable Creative Commons License

<!-- page 7 of 16 -->

The diversities of vascular plants and butterflies have been observed to positively correlate with one another in a variety of systems, primarily due to larval host plant associations (Erhardt 1985, Sparks and Parish 1995, Simonson et al. 2001, Croxton et al. 2005, Nowicki et al. 2007, Kitahara et al. 2008, MacDonald et al. 2018a, Riva et al. 2020). Accordingly, vascular plant species richness was quantified on each island using repeated full-island surveys (four surveys total), standardized to 40 min per ha per survey (MacDonald  et  al. 2018b for further details on vascular plant surveys). A total survey time of two hr and 40 min per ha is consistent with recent recommendations for boreal plant communities (Zhang et al. 2014). Only presence–absence data were collected for vascular plants, precluding use of our modelling framework (but see Simberloff and Gotelli 1984 for random colonization models applied to presence–absence data).

## Data analysis

We calculated values of species’ abundances, species’ probabilities of occurrence and species richness predicted by random placement for each of the 30 study islands using random placement models (1, 2 and 3, respectively). Abundance, occurrence and richness residuals were estimated as observed values minus random placement values. We next used linear mixed effects models to simultaneously: 1) quantify relationships between either abundance residuals or occurrence residuals and island variables, including area, isolation, proportion of suitable habitat and presence/absence of preferred larval host plants; 2) evaluate whether area per se or isolation differentially affects species’ abundances or occurrences contingent on their functional traits. Separate models were built for each isolation buffer size (250, 500, 1000, 1500, 2000, 2500, 3000, 3500, 4000, 4500 and 5000 m). Each of these models had the same number of parameters (k) and only differed in the buffer size used to measure island isolation. We therefore directly compared models with log likelihood (Lamb et al. 2018), where the model with the maximum log likelihood identified the optimal buffer size. Relationships between log likelihood and buffer sizes were quantified using Pearson’s product moment correlation coefficients. The proportion of suitable habitat for each species was estimated as the total area of suitable habitat types divided by the total area of the island. Habitat types were classified as suitable for a species if we observed at least one individual within them during the repeated full-island surveys. The presence/absence of preferred larval host plants (compiled from Hall  et  al. 2014, Acorn and Sheldon 2017) for each species on each island was included as a binary variable. We included species’ wingspan (mm; as reported in Burke et al. 2011) in models as a functional trait variable, serving as a measure of both body size and mobility/dispersal ability (Roland and Taylor 1997, Lens et al. 2002, Ewers and Didham 2006, Öckinger et al. 2009, MacDonald  et  al. 2018a, 2019). Other functional traits predicted to relate to species’ sensitivity to fragmentation (e.g. degree of ecological specialization, trophic position) were either not measured or did not vary substantially among butterfly species and so were not investigated. As an

inverse measure of species’ rarity, we included species’ total abundance and prevalence in abundance and occurrence models, respectively. To evaluate whether area per se or isolation differentially affected species’ abundances or occurrences contingent on their functional traits, we included the following interaction terms: wingspan:area, wingspan:isolation, rarity:area and rarity:isolation. All non-binary predictor variables were standardized (subtracting the mean and dividing by standard deviation), permitting comparisons of effect sizes. The structure for both abundance and occurrence linear mixed effects models was as follows, where ‘habitat’ is the proportion of suitable habitat for each species on each island and ‘plants’ is the presence/absence of each species’ preferred larval host plants:

$$
\begin{array}{l} f (\text {residuals}) \sim \beta_ {1} (\text {area}) + \beta_ {2} (\text {isolation}) + \beta_ {3} (\text {habitat}) + \beta_ {4} (\text {plants}) \\ + \beta_ {5} (\text {wingspan}) + \beta_ {6} (\text {rarity}) + \beta_ {7} (\text {wingspan : area}) \\ + \beta_ {8} (\text {wingspan}: \text {isolation}) + \beta_ {9} (\text {rarity}: \text {area}) \\ + \beta_ {1 0} (\text {rarity : isolation}) + (1 | \text {species id}) + e \\ \end{array}
$$

Linear models were fitted for species richness following the same basic protocol as abundance and occurrence linear mixed effects models. Predictor variables included island area, isolation, habitat diversity and vascular plant species richness. The most supported isolation buffer size was again assessed using log likelihood comparisons among models differing only in buffer size. Habitat diversity was estimated as the number of habitat types on each island. All predictor variables were standardized. The structure for richness linear models was as follows, where ‘habitat’ is the total number of habitat types recorded on each island and ‘plants’ is vascular plant species richness:

$$
f (\text {residuals}) \sim \beta_ {1} (\text {area}) + \beta_ {2} (\text {isolation}) + \beta_ {3} (\text {habitat}) + \beta_ {4} (\text {plants}) + e
$$

## Results

A total of 869 butterflies belonging to 34 species were observed during repeated full island surveys. Butterfly abundance data are reported in Supporting information. One species, Feniseca tarquinius, uniquely feeds on woolly aphids in its larval stage (Hall et al 2014, Acorn and Sheldon 2017). Only one individual of this species was observed across all surveys. We excluded it from abundance and occurrence models, which included presence/absence of preferred larval host plants as a predictor variable. All individuals belonging to all species were included in richness models.

## Species’ abundances

Comparing log likelihood among linear mixed effects models differing only in isolation buffer size resolved that the

1057

16000587, 2021, 7, Downloaded from https://nsojournals.onlinelibrary.wiley.com/doi/10.1111/ecog.05563 by Faculdade Medicina De Lisboa, Wiley Online Library on [05/11/2025]. See the Terms and Conditions (https://onlinelibrary.wiley.com/terms-and-conditions) on Wiley Online Library for rules of use; OA articles are governed by the applicable Creative Commons License

<!-- page 8 of 16 -->

proportion of water within 250 m (smallest buffer size) was most supported (Table 1, Fig. 2a). Model support significantly declined across increasing buffer sizes $(r = - 0.70\tilde{9};$ $p   =   0 . 0 1 5 )$ , indicating that the amount of habitat immediately surrounding individual islands better predicted species abundances than the amount of habitat at broader spatial scales. Within the most supported model, abundance residuals were significantly related to both island area and isolation (Table 2, Fig. 3). Area per se had a significant positive effect on species’ abundances, while isolation had a significant negative effect, in accordance with mechanisms predicted by the theory of island biogeography. The absolute magnitude of the effects of area per se and isolation, inferred from standardized regression coefficients, were approximately equivalent. Together, these results indicate that the sample-area effect cannot account for variation in species’ abundances across islands of varying area and that habitat configuration, and not just total area, has important effects on species’ abundances in this system. Other island variables, including the proportion of suitable habitat and presence/absence of preferred larval host plants, were not related to species’ abundances.

Coefficients of the wingspan:area and rarity:area interaction terms were significantly negative, indicating that effects of area per se systematically varied across species in respect to these functional traits. Causality behind the wingspan:area interaction is clear; effects of area per se on abundance were greater for smaller, less mobile butterfly species. However, for rarity:area, it cannot be resolved whether effects of area per se on abundance were greater for rare species, or whether these species were rare within the dataset because they experience greater effects of area per se. Comparisons of the relative abundances of species between the mainland (continuous habitat) and islands (fragmented habitat) would help resolve the causal direction of this relationship; however, this was beyond the scope of this study. Relationships between

Table 1. Log likelihood values for linear mixed effects (abundance and occurrence) and linear (species richness) models. For species’ abundances, species’ occurrences and species richness, separate models were built for a range of isolation buffers, measuring the proportion of open water within 250, 500, 1000, 1500, 2000, 2500, 3000, 3500, 4000, 4500 and 5000 m of island shores. Model support significantly declined across increasing isolation buffer sizes in all instances. The most supported buffer size for each model set is highlighted in bold.

| Isolation buffer (m) | Abundance | Occurrence | Species richness |
| --- | --- | --- | --- |
| 250 | -1329.83 | -1340.37 | -36.79 |
| 500 | -1330.22 | -1340.71 | -37.45 |
| 1000 | -1330.99 | -1342.89 | -37.67 |
| 1500 | -1332.11 | -1341.77 | -36.61 |
| 2000 | -1332.00 | -1340.52 | -37.02 |
| 2500 | -1332.05 | -1340.72 | -37.79 |
| 3000 | -1332.17 | -1341.71 | -38.12 |
| 3500 | -1332.13 | -1342.61 | -38.36 |
| 4000 | -1332.01 | -1343.28 | -38.45 |
| 4500 | -1331.86 | -1343.60 | -38.48 |
| 5000 | -1331.87 | -1343.53 | -38.44 |

abundance residuals and functional trait variables were not significant. This result is expected, as abundance residuals were standardized for each species individually before they were concatenated for use in linear mixed effects models.

## Species’ occurrences

As with abundance linear mixed effects models, the most supported isolation buffer size for predicting occurrence residuals was 250 m (Table 1, Fig. 2a). Model support significantly declined across increasing buffer sizes $(r = - 0.74\tilde{6};$ $p   =   0 . 0 0 8 )$ . Within the most supported model, occurrence residuals showed no relationship to island area, suggesting that the sample-area effect sufficiently accounts for variation in species’ occurrences across islands that vary in area (Table 2, Fig. 3). This result confers support for the passive sampling/habitat amount hypotheses. However, occurrence residuals were significantly negatively related to island isolation, suggesting that island configuration has important effects on species’ occurrences, as predicted by the theory of island biogeography. Other island variables, including the proportion of suitable habitat and presence/absence of preferred larval host plants, were not significantly related to occurrence residuals.

Effects of functional trait variables (wingspan and rarity) and their interaction with island variables were not significant at $\alpha   =   0 . 0 5$ . However, the coefficient of the wingspan:area interaction term was marginally significant at $p   =   0 . 0 6 9$ , suggesting that smaller, less mobile species were less likely than larger, more mobile species to occur on small islands. In other words, butterfly species richness on small islands may be disproportionately comprised of large butterfly species with high mobility.

## Species richness

The most supported isolation buffer size for predicting species richness residuals was 1500 m, which was only marginally more supported than the smallest (250 m) buffer size (Table 1, Fig. 2a). Notwithstanding, model support still significantly declined across increasing buffer sizes $\bar{(}  r= -0.83\bar{3};$ $p   =   0 . 0 0 1 )$ . Within the most supported model, residuals were not significantly related to island area, isolation, habitat richness or vascular plant species richness (Table 2, Fig. 3). It should be noted, however, that the directionality of the island isolation coefficient aligned with predictions of the theory of island biogeography, and was significant at $\alpha   =   0 . 1 0$ . Failure to resolve a significant effect at $\alpha   =   0 . 0 5$ suggests that richness-based analyses confer less analytical power than abundance- and occurrence-based analyses. If we adopt the most commonly used significance threshold of $\alpha   =   0 . 0 5$ , our linear model would suggest that the sample-area effect sufficiently accounts for variation in richness observed across our study islands, conferring support for the passive sampling/habitat amount hypotheses and random assembly of species.

1058

1600587, 2021, 7, Downloaded from https://nsojournals.onlinelibrary.wiley.com/doi/10.1111/ecog.05563 by Faculdade Medicina De Lisboa, Wiley Online Library on [05/11/2025]. See the Terms and Conditions (https://onlinelibrary.wiley.com/terms-and-conditions) on Wiley Online Library for rules of use; OA articles are governed by the applicable Creative Commons License

<!-- page 9 of 16 -->

![Image block](doc:cfca8f8/tier:advanced/page:9/block:1)

Figure 2. a) Standardized log likelihood values for linear mixed effects (abundance and occurrence) and linear (species richness) models where responding variables were random placement residuals. Explanatory variables for each model are listed in Table 2 and Figure 3. Separate models were built using different island isolation buffer sizes, quantifying using the proportion of open water within 250, 500, 1000, 1500, 2000, 2500, 3000, 3500, 4000, 4500, and 5000 m of island shores. To permit comparisons of relationships between log likelihood values and buffer sizes among abundance, occurrence, and species richness model sets, log likelihood scores were standardized for each model set by subtracting the mean and dividing by standard deviation. Model support significantly declined across increasing isolation buffer sizes in all instances. b) Log-log island species-area relationship (ISAR) for butterflies occurring on 30 study islands. The shaded blue polygon represents 95% confidence intervals for the loglog ISAR linear regression (solid blue line), parameterized using observed richness values for all 30 islands. Random placement richness values were calculated using a random placement model (model 3; see Materials and Methods). The shaded green polygon represents 95% interpolated confidence intervals for random placement values, calculated using Coleman’s (1981) formula for variance.

Table 2. Standardized regression coefficient estimates (‘coeff.’), standard errors (‘SE’) and p-values (‘p’) from linear models fitting random placement residuals for species’ abundances, species’ occurrences and species richness. Included in all models were island area, measured in m<sup>2</sup> and island isolation, measured as the proportion of water within the most supported buffer size (250 m for abundance and occurrence; 1500 m for species richness). Within abundance and occurrence models, the proportion suitable habitat (‘habitat’) was measured for each species as the area of suitable habitat on each island divided by the area of the island. Presence/absence of each species’ preferred larval host plants (‘plants’) was included as a binary variable. Wingspan was included as a measure of species’ body size and as a proxy of dispersal ability. Each species’ total abundance and prevalence were used as an inverse measure of rarity in abundance and occurrence models, respectively. Species identity was included as a random effect in abundance and occurrence models. Within the species richness model, habitat diversity (‘habitat’) was estimated as the total number of habitat types recorded on each island. Plant diversity (‘plants’) was measured as vascular plant species richness. Significant coefficients (α =0.05) are highlighted in bold.

<table><tr><td rowspan="2">Variable</td><td colspan="3">Abundance</td><td colspan="3">Occurrence</td><td colspan="3">Species richness</td></tr><tr><td>coeff.</td><td>SE</td><td>p</td><td>coeff.</td><td>SE</td><td>p</td><td>coeff.</td><td>SE</td><td>p</td></tr><tr><td>area</td><td>0.087</td><td>0.032</td><td>0.007</td><td>0.005</td><td>0.033</td><td>0.884</td><td>0.294</td><td>0.292</td><td>0.323</td></tr><tr><td>isolation</td><td>-0.069</td><td>0.032</td><td>0.028</td><td>-0.073</td><td>0.032</td><td>0.022</td><td>-0.320</td><td>0.173</td><td>0.076</td></tr><tr><td>habitat</td><td>0.020</td><td>0.032</td><td>0.535</td><td>0.016</td><td>0.033</td><td>0.635</td><td>-0.763</td><td>0.395</td><td>0.075</td></tr><tr><td>plants</td><td>0.018</td><td>0.082</td><td>0.830</td><td>-0.070</td><td>0.083</td><td>0.400</td><td>0.110</td><td>0.484</td><td>0.822</td></tr><tr><td>wingspan</td><td>-0.001</td><td>0.035</td><td>0.973</td><td>-0.015</td><td>0.035</td><td>0.661</td><td></td><td></td><td></td></tr><tr><td>rarity</td><td>-0.004</td><td>0.032</td><td>0.892</td><td>-0.001</td><td>0.033</td><td>0.988</td><td></td><td></td><td></td></tr><tr><td>wingspan:area</td><td>-0.117</td><td>0.031</td><td>&lt; 0.001</td><td>-0.057</td><td>0.031</td><td>0.069</td><td></td><td></td><td></td></tr><tr><td>wingspan:isolation</td><td>0.012</td><td>0.031</td><td>0.708</td><td>0.006</td><td>0.031</td><td>0.838</td><td></td><td></td><td></td></tr><tr><td>rarity:area</td><td>-0.081</td><td>0.031</td><td>0.009</td><td>-0.009</td><td>0.032</td><td>0.783</td><td></td><td></td><td></td></tr><tr><td>rarity:isolation</td><td>0.012</td><td>0.031</td><td>0.688</td><td>0.041</td><td>0.032</td><td>0.196</td><td></td><td></td><td></td></tr></table>

1059

16000587, 2021, 7, Downloaded from https://nsojournals.onlinelibrary.wiley.com/doi/10.1111/ecog.05563 by Faculdade Medicina De Lisboa, Wiley Online Library on [05/11/2025]. See the Terms and Conditions (https://onlinelibrary.wiley.com/terms-and-conditions) on Wiley Online Library for rules of use; OA articles are governed by the applicable Creative Commons License

<!-- page 10 of 16 -->

![Image block](doc:cfca8f8/tier:advanced/page:10/block:1)

Figure 3. Standardized regression coefficients and 95% confidence intervals from linear models relating random placement residuals to island characteristics and species’ functional traits for (a) species’ abundances, (b) species’ occurrences and (c) species richness. Included in all models were island area, measured in m<sup>2</sup> and island isolation, measured as the proportion of water within the most supported buffer size (250 m for abundance and occurrence; 1500 m for species richness). Within abundance and occurrence models, the proportion suitable habitat (‘suitable habitat’) was measured for each species as the area of suitable habitat on each island divided by the area of the island. Presence/absence of each species’ preferred larval host plants was included as a binary variable. Wingspan was included as a measure of species’ body size and as a proxy of dispersal ability. Each species’ total abundance and prevalence were used as an inverse measure of rarity in abundance and occurrence models, respectively. Species identity was included as a random effect in abundance and occurrence models. Within the species richness model, habitat diversity was estimated as the total number of habitat types recorded on each island. Plant diversity was measured as vascular plant species richness. The shading of each variable’s point estimate (coefficient) and confidence interval is proportional to its p-value, with darker shades indicating greater significance. Coefficients with 95% confidence intervals not overlapping zero were inferred to be significant at α = 0.05.

## Discussion

Distinguishing mechanisms that underlie variation in species’ abundances, species’ occurrences and emergent patterns of species richness is not only of great interest within the context of fundamental ecology, but is also of paramount importance to applied ecology and understanding how habitat fragmentation affects species diversity (Diamond 1975, Simberloff and Abele 1976, 1982, Haila 2002, Haddad et al. 2015, Chase et al. 2019). Here, we detail a novel modelling framework to test hypotheses on which conservation directives are contingent (Fahrig 2003, 2013, 2017, Haddad et al. 2015, Hanski 2015, Fletcher  et  al. 2018). Applying this modelling framework to a butterfly assemblage persisting on a naturally fragmented landscape of true islands, we were able to resolve that: 1) island area per se and isolation significantly affect species’ abundances and occurrences contingent on

their functional traits; and 2) important effects of area per se and isolation are not always apparent in aggregate diversity measures, such as those reflected in ISARs. Although there are several documented divergences between the biogeographies of true-island systems and fragmented habitat on terrestrial landscapes, findings from our study clearly demonstrate that fragmentation effects should not be inferred from richness-based analyses, but rather evaluated on a species-by-species basis.

## Inferences from the ISAR

Our modelling framework resolved that spatial patterns in butterfly species richness (i.e. the ISAR) did not significantly deviate from random placement in relation to island area, isolation, habitat diversity or vascular plant diversity. These ISAR-based inferences align with those of MacDonald et al.

16000587, 2021, 7, Downloaded from https://nsojournals.onlinelibrary.wiley.com/doi/10.1111/ecog.05563 by Faculdade Medicina De Lisboa, Wiley Online Library on [05/11/2025]. See the Terms and Conditions (https://onlinelibrary.wiley.com/terms-and-conditions) on Wiley Online Library for rules of use; OA articles are governed by the applicable Creative Commons License

1060

<!-- page 11 of 16 -->

(2018a), who used a series of SLOSS-based analyses to infer that butterfly species richness in this naturally fragmented landscape approximately conform to predictions of the sample-area effect, with no significant effects of area per se or isolation. Therefore, all analyses addressing effects of area per se and isolation on butterfly species richness in this system support the passive sampling/habitat amount hypotheses and Fahrig’s (2003, 2013, 2017) general conclusion that effects of fragmentation (i.e. area per se and isolation) are generally negligible after controlling for deleterious effects of habitat loss; only habitat amount at the landscape-scale affects species richness via its influence on regional species pools.

While there seems to be considerable support for the passive sampling/habitat amount hypotheses in the literature (Fahrig 2003, 2013, Martin 2018, Watling  et  al. 2020), a recent meta-analysis by Fahrig (2020), including 157 SLOSS comparisons from 58 studies, found that several small islands/ fragments contained more species than single large islands/ fragments in 72% of comparisons, equivalent numbers of species in 22% of comparisons and fewer species in 6% of comparisons. Removing studies with biased sampling effort in relation to island/fragment area shifted these figures to 58, 37 and 5%. Regardless, these results suggest that species richness varies with degree of fragmentation more often than it does not. Thus, the sample-area effect implicated in the passive sampling/habitat amount hypotheses cannot consistently account for SLOSS-based richness patterns. Furthermore, methods employed by Fahrig (2020) – specifically, comparisons of Quinn and Harrison (1988) species accumulation curves – suffer from an important limitation: substantial species turnover among several small islands/fragments can inflate their aggregate richness, such that important deviations from random placement (e.g. effects of area per se) are obscured (sensu Simberloff 1976, MacDonald et al. 2018b, Deane et al. 2020). This relationship may explain why several small islands/fragments are generally found to contain more species than single large fragments in the majority of SLOSS-based studies. While results of Fahrig’s (2020) meta-analysis are of great interest to both fundamental and applied ecology, they cannot necessarily be used to distinguish effects of area per se from the sample-area effect and cannot resolve additional effects of isolation or habitat diversity. Future investigations focusing on species richness would benefit from the inclusion of ISAR-based analyses that assess deviations from random placement on an island-by-island or fragment-by-fragment basis, such as those included within the modelling framework presented here.

Additional deviations from random placement may be resolved by visually examining the ISAR and random placement richness values (Fig. 2b). In this study, observed richness values were generally less than random placement richness values (all islands except four). This pattern cannot be attributed to effects of area per se, because the direction and magnitude of richness residuals was relatively consistent across islands of varying area (Fig. 2b), as indicated by the insignificant coefficient of island area within the species richness linear model (Table 2). Rather, this relationship is best explained by spatial

species aggregation, wherein conspecific individuals are more likely to co-occur on islands than what is predicted by random placement, reducing the species richness of individual islands (He and Legendre 2002). Therefore, although spatial patterns of species richness did not significantly deviate from random placement in respect to either island area or isolation, they did deviate from random placement in respect to spatial species aggregation. It is therefore clear that failure to resolve significant effects of area per se and isolation on species richness cannot be taken as direct evidence for random assembly of individuals and species, the fundamental pre-diction of the habitat amount/passive sampling hypotheses (c.f. Fahrig 2003, 2013, 2017, 2020). Rigorous evaluation of random assembly requires comparison of observed richness to expected richness predicted by null models, such as the random placement models presented here.

## Inferences from species’ abundances and occurrences

Inferring whether fragmentation is ‘good’ or ‘bad’ (sensu Fahrig 2017, Fletcher  et  al. 2018) based on emergent patterns of species richness is potentially susceptible to ‘ecological fallacy’ (sensu Robinson 1950), which describes biases that may arise when observed effects on aggregated variables (e.g. species richness) differ from causal relationships at more reductive and informative levels of organization (e.g. species’ abundances and occurrences). Indeed, our abundance and occurrence models resolved important effects of area per se and isolation that were not apparent in either ISAR-or SLOSS-based analyses (this study and MacDonald et al. 2018a, respectively). This discrepancy among inferences suggests that conflating responses of all species into a single aggregate measure (e.g. species richness) reduces our power to detect important relationships on which conservation directives should be contingent. Two such relationships were resolved when considering the entire species assemblage in abundance and occurrence models: 1) there was a disproportionate concentration of individuals on larger and less-isolated islands relative to what was predicted by the sample-area effect (passive sampling/habitat amount hypotheses); and 2) species were more likely to occur on less-isolated islands than what was predicted by the sample-area effect. It is therefore clear that the sample-area effect described by the passive sampling/habitat amount hypotheses cannot adequately account for spatial patterns in butterfly abundances and occurrences in this naturally fragmented landscape, which are better pre-dicted by mechanisms outlined by the theory of island biogeography. It should be noted that the directionality of area per se and isolation effects were consistent among abundance, occurrence and richness models, but only statistically significant (α = 0.05) in the first two analyses, wherein species’ responses were not aggregated into a single measure.

Most interestingly, our modelling framework simultaneously resolved that effects of area per se on species abundances and occurrences varied significantly with species-specific functional traits, suggesting that mechanisms

1061

16000587, 2021, 7, Downloaded from https://nsojournals.onlinelibrary.wiley.com/doi/10.1111/ecog.05563 by Faculdade Medicina De Lisboa, Wiley Online Library on [05/11/2025]. See the Terms and Conditions (https://onlinelibrary.wiley.com/terms-and-conditions) on Wiley Online Library for rules of use; OA articles are governed by the applicable Creative Commons License

<!-- page 12 of 16 -->

outlined by the theory of island biogeography are not neutral with respect to species identity. Whether species’ sensitivity to fragmentation varies predictably with functional traits is a long-standing and pertinent question in conservation biology (Roland and Taylor 1997, Lens et al. 2002, Gehring and Swihart 2003, Henle et al. 2004, Tscharntke and Brandl 2004, Thies  et  al. 2005, Ewers and Didham 2006, Prugh  et  al. 2008, Barbaro and Van Halder 2009, Öckinger et al. 2009, Hanski 2015, Warzecha et al. 2016, MacDonald et al. 2018a, 2019). In this study, effects of area per se were significantly greater for butterfly species with smaller wingspans. For Canadian butterflies, wingspan is one of the strongest correlates of estimated mobility and dispersal ability (Burke  et  al. 2011); thus, we can infer that effects of area per se are greatest for small species of limited mobility (c.f. Larsen  et  al. 2008). This relationship may be explained by larger and more mobile butterfly species having the ability to move among multiple small islands to meet their resource requirements. These ‘transient’ species may thereby exhibit patterns of abundance and occurrence that approximate random placement (Wilson and MacArthur 1967: Chapter 2; Rosenzweig 2004, MacDonald et al. 2018a). Such patterns would be predicted by ideal free distribution theory (sensu Dreisig 1995) if two conditions are met: 1) islands of varying area contain equivalent densities of resources; and 2) the mobility/dispersal ability of individuals is sufficient to render costs of inter-island movements negligible. By contrast, island edges may be perceived as impassible barriers for smaller and less mobile species, with energy expenditures and mortality risks associated with movement through the open-water matrix being too high for regular inter-island movements. Island edges may therefore delimit populations of smaller and less mobile species, which are generally restricted to larger islands that contain all resources required for mate location, reproduction, resting, roosting, predator escape and feeding (i.e. the functional resource-based habitat concept; Dennis et al. 2003). This hypothesis is supported by analyses of MacDonald  et  al. (2018a), who resolved that the probability of butterfly species occurring on islands without their preferred larval host plants was positively related to their wingspan and estimated mobility. Considered together, these results suggest that functional traits may be used to predict species’ sensitivity to fragmentation and that species identity should not be ignored when investigating mechanisms that underlie ISARs or in conservation planning. It is, however, important to recognize that the open-water matrix of this study landscape may be more unsuitable and less permeable than those of many fragmented terrestrial landscapes (Dunning  et  al. 1992, Ricketts 2001, Laurance 2008, Mendenhall et al. 2014, Itescu 2019, Farneda et al. 2020). It is therefore unclear the degree to which these relationships between species’ functional traits and effects of area per se and isolation are generalizable to conservation efforts addressing terrestrial landscapes fragmented through anthropogenic activities.

The abundance and occurrence modelling framework proposed here may also be implemented on a species-by-species basis by regressing island/fragment variables (area, isolation, presence/amount of suitable habitat or specific resources, etc.) on abundance and occurrence residuals for each species in separate linear models. This method of analysis precludes the simultaneous integration of functional trait analyses within models, but has the added advantage of identifying single species that are particularly sensitive to fragmentation (area per se and isolation) or other island/fragment variables of interest. This simple decomposition of our modelling framework may be used to resolve whether particular species require independent consideration within conservation frameworks.

## Isolation versus habitat amount

The relative isolation of islands addressed in this study was quantified across multiple scales as the proportion of water within 11 buffer sizes, ranging from 250 to 5000 m. These measures are equal to 1 minus the amount of landmass (habitat) within each buffer distance. Fahrig (2013) suggests that the habitat amount hypothesis would be supported by species’ abundances, species’ occurrences or species richness of equal-area sampling plots (stratified across fragments of varying area and isolation) correlating with the amount of habitat on the surrounding landscape more strongly than with the area of the individual fragments on which the sampling plots are located. This is because landscapes containing less habitat should contain fewer individuals (belonging to fewer species) due to the sample-area effect, meaning fragments within such landscapes will have smaller species pools from which their own diversities are randomly sampled. However, the ‘appropriate distance’ for quantifying the amount of habitat surrounding equal-area sampling plots is undefined and, most problematically, the area of individual fragments on which sampling plots are located becomes increasingly correlated with habitat amount as this distance is reduced. Thus, it may not be possible to decouple fragment area from habitat amount using Fahrig’s (2013) proposed method; particularly, for taxa that respond to habitat amount and configuration at fine spatial scales, including butterflies (Thomas and Abery 1995, MacDonald et al. 2017, 2018a, 2019, Saura 2020).

Within our modelling framework, variation in species’ abundances, species’ occurrences and species richness associated with full-island surveys and the sample-area effect is nullified in the calculation of random placement residuals. Abundance, occurrence and richness residuals can therefore be correlated with island/fragment area and the amount of surrounding habitat in a fashion similar to Fahrig’s (2013) proposed method of using equal-area sampling plots. However, because the area of individual islands/fragments is not included in our measures of the amount of surrounding habitat (our buffers are generated from island/fragment edges), the problem of island/fragment area becoming increasingly correlated with habitat amount at fine spatial scales is avoided. After controlling for effects of area per se,

1062

1600587, 2021, 7, Downloaded from https://nsojournals.onlinelibrary.wiley.com/doi/10.1111/ecog.05563 by Faculdade Medicina De Lisboa, Wiley Online Library on [05/11/2025]. See the Terms and Conditions (https://onlinelibrary.wiley.com/terms-and-conditions) on Wiley Online Library for rules of use; OA articles are governed by the applicable Creative Commons License

<!-- page 13 of 16 -->

abundance and occurrence residuals were significantly related to island isolation. Model support significantly declined across increasing isolation buffer sizes for species’ abundances, species’ occurrences and species richness, suggesting that that the amount of habitat immediately surrounding islands, rather than the amount of habitat at broader landscape scales, has the greatest effect on butterflies in this system. Importantly, island area and isolation were effectively decoupled, as indicated by the absence of correlation between island area and isolation (e.g. 250 m buffer; r = 0.082; p = 0.668). Thus, in contrast with mechanisms outlined by the habitat amount hypothesis, isolation effects observed in this study are better attributed to the fact that individual butterflies moving through the open-water matrix are less likely to encounter more isolated islands (Andrén 1994), reducing species’ abundances and probabilities of occurrence, as predicted by the theory of island biogeography. This inference is further corroborated by analyses of MacDonald  et  al. (2018a), which showed that butterfly species turnover among islands of equal areas – a proxy for variation in species pools if islands indeed randomly sample species – was unrelated to Euclidean distance between islands. This result suggests a uniform species pool throughout the study landscape. Again, the degree to which these findings apply to fragmented terrestrial landscapes, wherein the suitability and permeability of matrices may vary, is unclear. For studies addressing fragmented terrestrial landscapes, isolation measures should not only account for the proportion of suitable habitat within various buffer distances, but also include measures of matrix suitability and permeability, if they are available (MacDonald et al. 2020).

## Habitat fragmentation and the narcissus effect

It is important to recognize a bias within this case study, and potentially other study designs addressing spatial patterns of species’ abundances, species’ occurrences or species richness across true islands or terrestrial habitat fragments. Here, we investigated effects of area per se and isolation on a naturally fragmented landscape of true islands with substantial time-since-isolation (3000–4000 YA; Yang and Teller 2005). Therefore, species that are particularly sensitive to fragmentation are unlikely to occur on islands at all. Although our modelling framework resolved significant effects of area per se and isolation on butterfly species’ abundances and occurrences, effects of area per se and isolation on the regional species pool were likely underestimated, as the species assemblage of adjacent continuous habitat was not quantified. This bias may be described as the ‘narcissus effect’, which addresses situations wherein a null model or study design unintentionally accounts for or excludes effects that are of interest (sensu Colwell and Winkler 1984). It is possible that this bias contributed to results of Fahrig’s (2017) review, where 68% (158/232) of studies addressing single species reported positive fragmentation effects; species that are particularly sensitive to fragmentation may be completely missed in many studies. We therefore suggest caution in interpreting results from study designs that are susceptible to the narcissus effect

and encourage future studies to compare the identities and functional traits of species between islands/fragments and adjacent continuous habitat to assess potential biases resulting from the historic exclusion of fragmentation-sensitive species. This may be accomplished using our proposed modelling framework by surveying continuous habitat equal in area to the sum of all surveyed islands/fragments. Abundance data from continuous habitat may then be used in place of total abundances across all islands/fragments (n ) to calculate abundance, occurrence and richness random placement values for each island/fragment using the random placement models described above. Subtracting these random placement values from observed abundance, occurrence and richness values for each island/fragment will result in abundance, occurrence and richness residuals that may be used in our linear mixed effects models (abundance and occurrence) and linear models (richness) to resolve whether there are additional effects of area per se and isolation on the regional species pool.

## Conservation implications

Considerable uncertainty exists in the literature regarding the influence of area per se and isolation (i.e. habitat fragmentation) on populations and communities of wildlife (Fahrig 2003, 2013, 2017, Haddad  et  al. 2015, Hanski 2015, Fletcher et al. 2018). There is an immediate need to resolve this debate, as habitat loss and fragmentation are widespread and increasing (Hanski et al. 2013, Ibisch et al. 2016, Chase et al. 2020, Deane et al. 2020). We demonstrate here that ISAR- and SLOSS-based inferences, founded on emergent patterns of species richness, have the potential to obscure important interspecific variation in responses to area per se and isolation. To infer support for the passive sampling, habitat amount and related hypotheses from emergent patterns of species richness that spuriously conform to pre-dictions of the sample-area effect is to simplistically cut rather than carefully untie the Gordian knot of ecological complexity. We suggest that, in addition to emergent patterns of species richness, information at more reductive and informative levels of organization (e.g. species’ abundances and occurrences) should be included in studies aiming to measure and understand effects of habitat fragmentation.

Acknowledgements – Vascular plant surveys and identifications were completed by Iraleigh Anderson and we thank him for valuable discussions and insights. We also thank Federico Riva for his review of a previous version of this manuscript.

Funding – This work was supported by a Natural Sciences and Engineering Research Council (NSERC) Discovery Grant to SEN (RGPIN-2014-04842) and NSERC Alexander Graham Bell Canada Graduate Scholarships – MSc and PhD (CGS – D and CGS – D) to ZGM

Conflicts of interest – The authors have no conflicts of interest to declare.

Permits – Permission to survey butterflies and vascular plants, including collection of voucher specimens, was granted by Ontario Parks.

1063

16000587, 2021, 7, Downloaded from https://nsojournals.onlinelibrary.wiley.com/doi/10.1111/ecog.05563 by Faculdade Medicina De Lisboa, Wiley Online Library on [05/11/2025]. See the Terms and Conditions (https://onlinelibrary.wiley.com/terms-and-conditions) on Wiley Online Library for rules of use; OA articles are governed by the applicable Creative Commons License

<!-- page 14 of 16 -->

## Author contributions

**Zachary MacDonald**: Conceptualization (lead); Formal analysis (lead); Funding acquisition (supporting); Methodology (lead); Project administration (equal); Resources (supporting); Software (lead); Validation (equal); Visualization (lead); Writing – original draft (lead); Writing – review and editing (lead). **David Dean**: Conceptualization (supporting); Formal analysis (supporting); Methodology (supporting); Resources (supporting); Software (supporting); Validation (equal); Visualization (supporting); Writing – original draft (supporting); Writing – review and editing (supporting). **Fangliang He**: Conceptualization (supporting); Formal analysis (supporting); Methodology (supporting); Software (supporting); Supervision (supporting); Validation (equal); Visualization (supporting); Writing – original draft (supporting); Writing – review and editing (supporting). **Clayton Lamb**: Conceptualization (supporting); Formal analysis (supporting); Methodology (supporting); Software (supporting); Validation (equal); Visualization (supporting); Writing – original draft (supporting); Writing – review and editing (supporting). **Felix Sperling**: Conceptualization (supporting); Formal analysis (supporting); Methodology (supporting); Supervision (supporting); Validation (equal); Visualization (supporting); Writing – original draft (supporting); Writing – review and editing (supporting). **John Acorn**: Conceptualization (supporting); Formal analysis (supporting); Methodology (supporting); Project administration (equal); Resources (supporting); Supervision (equal); Validation (equal); Visualization (supporting); Writing – original draft (supporting); Writing – review and editing (supporting). **Scott E. Nielsen**: Conceptualization (supporting); Formal analysis (supporting); Funding acquisition (lead); Methodology (supporting); Project administration (equal); Resources (supporting); Software (supporting); Supervision (equal); Validation (equal); Visualization (supporting); Writing – original draft (supporting); Writing – review and editing (supporting).

## Transparent Peer Review

The peer review history for this article is available at &lt;https://publons.com/publon/10.1111/ecog.05563&gt;.

## Data availability statement

All butterfly, plant, and island data are provided in Supporting Information.

## References

Abele, L. G. and Connor, E. F. 1979. Application of island biogeography theory to refuge design: making the right decision for the wrong reasons. – In: Proceedings of the first conference on scientific research in the national parks, Vol. 1. US Department of the Interior, Washington, D.C., USA, pp. 89–94.

- Acorn, J. and Sheldon, I. 2017. Butterflies of Ontario and eastern Canada. – Partners Publishing.
- Andrén, H. 1994. Effects of habitat fragmentation on birds and mammals in landscapes with different proportions of suitable habitat: a review. – Oikos 71: 355–366.
- Arrhenius, O. 1921. Species and area. – J. Ecol. 9: 95–99.
- Barbaro, L. and Van Halder, I. 2009. Linking bird, carabid beetle and butterfly life-history traits to habitat fragmentation in mosaic landscapes. – Ecography 32: 321–333.
- Brown, J. H. and Kodric-Brown, A. 1977. Turnover rates in insular biogeography: effect of immigration on extinction. – Ecology 58: 445–449.
- Buckley, R. 1982. The habitat-unit model of island biogeography. – J. Biogeogr. 9: 339–344.
- Burke, R. J. et al. 2011. A mobility index for Canadian butterfly species based on naturalists’ knowledge. – Biodivers. Conserv. 20: 2273–2295.
- Chao, A. et al. 2014. Rarefaction and extrapolation with Hill numbers: a framework for sampling and estimation in species diversity studies. – Ecol. Monogr. 84: 45–67.
- Chase, J. M. et al. 2019. A framework for disentangling ecological mechanisms underlying the island species–area. – Front. Biogeogr. 11: e40844.
- Chase, J. M. et al. 2020. Ecosystem decay exacerbates biodiversity loss with habitat loss. – Nature 584: 238–243.
- Coleman, B. D. 1981. On random placement and species–area relations. – Math. Biosci. 54: 191–215.
- Colwell, R. K. and Winkler, D. W. 1984. A null model for null models in biogeography. – In: Strong Jr, D. R. et al. (eds), Ecological communities: conceptual issues and the evidence. Princeton Univ. Press, pp. 344–359.
- Connor, E. F. and McCoy, E. D. 1979. The statistics and biology of the species–area relationship. – Am. Nat. 113: 791–833.
- Croxton, P.  et  al. 2005. Linear hotspots? The floral and butterfly diversity of green lanes. – Biol. Conserv. 121: 579–584.
- Deane, D. C.  et  al. 2020. Quantifying factors for understanding why several small patches host more species than a single large patch. – Biol. Conserv. 249: 108711.
- Dennis, R. L. et al. 2003. Towards a functional resource-based concept for habitat: a butterfly biology viewpoint. – Oikos 102: 417–426.
- Diamond, J. M. 1972. Biogeographic kinetics: estimation of relaxation times for avifaunas of southwest pacific islands. – Proc. Natl Acad. Sci. USA 69: 3199–3203.
- Diamond, J. M. 1975. The island dilemma: lessons of modern biogeographic studies for the design of natural reserves. – Biol. Conserv. 7: 129–146.
- Dreisig, H. 1995. Ideal free distributions of nectar foraging bumblebees. – Oikos 72: 161–172.
- Dunning, J. B. et al. 1992. Ecological processes that affect populations in complex landscapes. – Oikos 65: 169–175.
- Erhardt, A. 1985. Diurnal Lepidoptera: sensitive indicators of cultivated and abandoned grassland. – J. Appl. Ecol. 22: 849–861.
- Ewers, R. M. and Didham, R. K. 2006. Confounding factors in the detection of species responses to habitat fragmentation. – Biol. Rev. 81: 117–142.
- Fahrig, L. 2003. Effects of habitat fragmentation on biodiversity. – Annu. Rev. Ecol. Evol. Syst. 34: 487–515.
- Fahrig, L. 2013. Rethinking patch size and isolation effects: the habitat amount hypothesis. – J. Biogeogr. 40: 1649–1663.
- Fahrig, L. 2017. Ecological responses to habitat fragmentation per se. – Annu. Rev. Ecol. Evol. Syst. 48: 1–23.

1064

16000587, 2021, 7, Downloaded from https://nsojournals.onlinelibrary.wiley.com/doi/10.1111/ecog.05563 by Faculdade Medicina De Lisboa, Wiley Online Library on [05/11/2025]. See the Terms and Conditions (https://onlinelibrary.wiley.com/terms-and-conditions) on Wiley Online Library for rules of use; OA articles are governed by the applicable Creative Commons License

<!-- page 15 of 16 -->

- Fahrig, L. 2020. Why do several small patches hold more species than few large patches? – Global Ecol. Biogeogr. 29: 615–628.
- Farneda, F. Z. et al. 2020. Predicting biodiversity loss in island and countryside ecosystems through the lens of taxonomic and functional biogeography. – Ecography 43: 97–106.
- Fletcher Jr, R. J. et al. 2018. Is habitat fragmentation good for biodiversity? – Biol. Conserv. 226: 9–15.
- Franzén, M.  et  al. 2012. Species–area relationships are controlled by species traits. – PLoS One 7: e37359.
- Gavish, Y. et al. 2012. Decoupling fragmentation from habitat loss for spiders in patchy agricultural landscapes. – Conserv. Biol. 26: 150–159.
- Gehring, T. M. and Swihart, R. K. 2003. Body size, niche breadth and ecologically scaled responses to habitat fragmentation: mammalian predators in an agricultural landscape. – Biol. Conserv. 109: 283–295.
- Gonzalez, A. 2000. Community relaxation in fragmented landscapes: the relation between species richness, area and age. – Ecol. Lett. 3: 441–448.
- Gotelli, N. J. G. and Graves, G. R. 1996. Null models in ecology. – Smithsonian Inst. Press.
- Haddad, N. M. et al. 2015. Habitat fragmentation and its lasting impact on Earth’s ecosystems. – Sci. Adv. 1: e1500052.
- Hadley, A. S. and Betts, M. G. 2016 Refocusing habitat fragmentation research using lessons from the last decade. – Curr. Landscape Ecol. Rep. 1: 55–66.
- Haila, Y. 2002. A conceptual genealogy of fragmentation research: from island biogeography to landscape ecology. – Ecol. Appl. 12: 321–334.
- Haila, Y. and Järvinen, O. 1983. Land bird communities on a Finnish island: species impoverishment and abundance patterns. – Oikos 41: 255–273.
- Haila, Y. et al. 1983. Colonization of islands by land birds: prevalence functions in a Finnish archipelago. – J. Biogeogr. 10: 499–531.
- Hall, P. W.  et  al. 2014. The ROM field guide to butterflies of Ontario. – Royal Ontario Museum Press.
- Hanski, I. 1994. A practical model of metapopulation dynamics. – J. Anim. Ecol. 63: 151–162.
- Hanski, I. 1998. Metapopulation dynamics. – Nature 396: 41–49.
- Hanski, I. 1999. Metapopulation ecology. – Oxford Univ. Press.
- Hanski, I. 2015. Habitat fragmentation and species richness. – J. Biogeogr. 42: 989–993.
- Hanski, I. and Gyllenberg, M. 1993. Two general metapopulation models and the core-satellite species hypothesis. – Am. Nat. 142: 17–41.
- Hanski, I. et al. 2013. Species–fragmented area relationship. – Proc. Natl Acad. Sci. USA 110: 12715–12720.
- He, F. and Legendre, P. 2002. Species diversity patterns derived from species–area models. – Ecology 83: 1185–1198.
- Henle, K. et al. 2004. Predictors of species sensitivity to fragmentation. – Biodivers. Conserv. 13: 207–251.
- Hillebrand, H. et al. 2018. Biodiversity change is uncoupled from species richness trends: consequences for conservation and monitoring. – J. Appl. Ecol. 55: 169–184.
- Hortal, J. et al. 2009. Island species richness increases with habitat diversity. – Am. Nat. 174: E205–E217.
- Ibisch, P. L.  et  al. 2016. A global map of roadless areas and their conservation status. – Science 354: 1423–1427.
- Itescu, Y. 2019. Are island-like systems biologically similar to islands? A review of the evidence. – Ecography 42: 1298–1314.
- Kadmon, R. and Allouche, O. 2007. Integrating the effects of area, isolation and habitat heterogeneity on species diversity: a uni-

- fication of island biogeography and niche theory. – Am. Nat. 170: 443–454.
- Karger, D. N.  et  al. 2014. Island biogeography from regional to local scales: evidence for a spatially scaled echo pattern of fern diversity in the southeast Asian archipelago. – J. Biogeogr. 41: 250–260.
- Kelly, B. J. et al. 1989. Causes of the species-area relation: a study of islands in Lake Manapouri, New Zealand. – J. Ecol. 77: 1021–1028.
- Kitahara, M.  et  al. 2008. Relationship of butterfly diversity with nectar plant species richness in and around the Aokigahara primary woodland of Mount Fuji, central Japan. – Biodivers. Conserv. 17: 2713–2734.
- Lamb, C. T. et al. 2018. Effects of habitat quality and access management on the density of a recovering grizzly bear population. – J. Appl. Ecol. 55: 1406–1417.
- Larsen, T. H. et al. 2008. Understanding trait-dependent community disassembly: dung beetles, density functions and forest fragmentation. – Conserv. Biol. 22: 1288–1298.
- Laurance, W. F. 2008. Theory meets reality: how habitat fragmentation research has transcended island biogeographic theory. – Biol. Conserv. 141: 1731–1744.
- Lens, L. et al. 2002. Avian persistence in fragmented rainforest. – Science 298: 1236–1238.
- Levins, R. 1969. Some demographic and genetic consequences of environmental heterogeneity for biological control. – Bull. Entomol. Soc. Am. 15: 237–240.
- Lomolino, M. V. 2000. Ecology’s most general, yet protean pattern: the species–area relationship. – J. Biogeogr. 27: 17–26.
- MacArthur, R. H. and Wilson, E. O. 1963. An equilibrium theory of insular zoogeography. – Evolution 17: 373–387.
- MacDonald, Z. G. et al. 2017. Negative relationships between species richness and evenness render common diversity indices inadequate for assessing long-term trends in butterfly diversity. – Biodivers. Conserv. 26: 617–629.
- MacDonald, Z. G. et al. 2018a. Decoupling habitat fragmentation from habitat loss: butterfly species mobility obscures fragmentation effects in a naturally fragmented landscape of lake islands. – Oecologia 186: 11–27.
- MacDonald, Z. G. et al. 2018b. The theory of island biogeography, the sample-area effect and the habitat diversity hypothesis: complementarity in a naturally fragmented landscape of lake islands. – J. Biogeogr. 45: 2730–2743.
- MacDonald, Z. G. et al. 2019. Perceptual range, targeting ability and visual habitat detection by greater fritillary butterflies Speyeria cybele (Lepidoptera: Nymphalidae) and Speyeria atlantis. – J. Insect Sci. 19: 1–10.
- MacDonald, Z. G. et al. 2020. Gene flow and climate-associated genetic variation in a vagile habitat specialist. – Mol. Ecol. 29: 3889–3906.
- Martin, C. A. 2018. An early synthesis of the habitat amount hypothesis. – Landscape Ecol. 33: 1831–1835.
- Melbourne, B. A. et al. 2004. Species survival in fragmented landscapes: where to from here? – Biodivers. Conserv. 13: 275–284.
- Mendenhall, C. D. et al. 2014. Predicting biodiversity change and averting collapse in agricultural landscapes. – Nature 509: 213–217.
- Moilanen, A. and Nieminen, M. 2002. Simple connectivity measures in spatial ecology. – Ecology 83: 1131–1145.
- Nilsson, S. G. et al. 1988. Habitat diversity or area per se? Species richness of woody plants, carabid beetles and land snails on islands. – J. Anim. Ecol. 57: 685–704.

1065

1600587, 2021, 7, Downloaded from https://nsojournals.onlinelibrary.wiley.com/doi/10.1111/ecog.05563 by Faculdade Medicina De Lisboa, Wiley Online Library on [05/11/2025]. See the Terms and Conditions (https://onlinelibrary.wiley.com/terms-and-conditions) on Wiley Online Library for rules of use; OA articles are governed by the applicable Creative Commons License

<!-- page 16 of 16 -->

- Noss, R. F. 1991. Landscape connectivity: different functions at different scales. – In: Soulé, M. E. et al. (eds), Landscape linkages and biodiversity. Island Press.
- Nowicki, P. et al. 2007. From metapopulation theory to conservation recommendations: lessons from spatial occurrence and abundance patterns of Maculinea butterflies. – Biol. Conserv. 140: 119–129.
- Nowicki, P.  et  al. 2008. Butterfly monitoring methods: the ideal and the real world. – Israel J. Ecol. Evol. 54: 69–88.
- Öckinger, E. et al. 2009. Mobility-dependent effects on species richness in fragmented landscapes. – Basic Appl. Ecol. 10: 573–578.
- Orrock, J. L. and Watling, J. I. 2010. Local community size mediates ecological drift and competition in metacommunities. – Proc. R. Soc. B 277: 2185–2191.
- Ovaskainen, O. 2002. Long-term persistence of species and the SLOSS problem. – J. Theor. Biol. 218: 419–433.
- Prugh, L. R. 2009. An evaluation of patch connectivity measures. – Ecol. Appl. 19: 1300–1310.
- Prugh, L. R.  et  al. 2008. Effect of habitat area and isolation on fragmented animal populations. – Proc. Natl Acad. Sci. USA 105: 20770–20775.
- Quinn, J. F. and Harrison, S. P. 1988. Effects of habitat fragmentation and isolation on species richness: evidence from biogeographic patterns. – Oecologia 75: 132–140.
- Quinn, S. L.  et  al. 1987. The island biogeography of Lake Manapouri, New Zealand. – J. Biogeogr. 14: 569–581.
- Ricketts, T. H. 2001. The matrix matters: effective isolation in fragmented landscapes. – Am. Nat. 158: 87–99.
- Riva, F.  et  al. 2020. Composite effects of cutlines and wildfire result in fire refuges for plants and butterflies in boreal treed peatlands. – Ecosystems 23: 1–13.
- Robinson, W. S. 1950. Ecological correlations and the behavior of individuals. – Am. Sociol. Rev. 15: 351–357.
- Roland, J. and Taylor, P. D. 1997. Insect parasitoid species respond to forest structure at different spatial scales. – Nature 386: 710.
- Rosenzweig, M. L. 1995. Species diversity in space and time. – Cambridge Univ. Press.
- Rosenzweig, M. L. 2004. Applying species–area relationships to the conservation of species diversity. – In: Lomolino, M. V. and Heaney, M. V. (eds), Frontiers in biogeography: new directions in the geography of nature. Sinauer Associates, pp. 325–344.
- Rutowski, R. L. 2003. Visual ecology of adult butterflies. – In: Boggs, C. L. et al. (eds), Butterflies: ecology and evolution taking flight. Univ. of Chicago Press, pp. 9–25.
- Saccheri, I.  et  al. 1998. Inbreeding and extinction in a butterfly metapopulation. – Nature 392: 491–494.
- Santos, A. M.  et  al. 2010. Are species–area relationships from entire archipelagos congruent with those of their constituent islands? – Global Ecol. Biogeogr. 19: 527–540.
- Saura, S. 2020. The habitat amount hypothesis implies negative effects of habitat fragmentation on species richness. – J. Biogeogr. 48: 11-22.
- Scheiner, S. M. 2003. Six types of species–area curves. – Global Ecol. Biogeogr. 12: 441–447.
- Shafer, C. L. 1990. Nature reserves: island theory and conservation practice. – Smithsonian Inst. Press.
- Simberloff, D. 1976. Species turnover and equilibrium island biogeography. – Science 194: 572–578.
- Simberloff, D. and Abele, L. G. 1976. Island biogeography theory and conservation practice. – Science 191: 285–286.

- Simberloff, D. and Abele, L. G. 1982. Refuge design and island biogeographic theory: effects of fragmentation. – Am. Nat. 120: 41–50.
- Simberloff, D. and Gotelli, N. 1984. Effects of insularisation on plant species richness in the prairie-forest ecotone. – Biol. Conserv. 29: 27–46.
- Simonson, S. E. et al. 2001. Rapid assessment of butterfly diversity in a montane landscape. – Biodivers. Conserv. 10: 1369–1386.
- Sparks, T. and Parish, T. 1995. Factors affecting the abundance of butterflies in field boundaries in Swavesey fens, Cambridgeshire, UK. – Biol. Conserv. 73: 221–227.
- Stevens, G. C. 1986. Dissection of the species–area relationship among wood-boring insects and their host plants. – Am. Nat. 128: 35–46.
- Thies, C. et al. 2005. The landscape context of cereal aphid–parasitoid interactions. – Proc. R. Soc. B 272: 203–210.
- Thomas, C. D. and Abery, J. C. G. 1995. Estimating rates of butterfly decline from distribution maps: the effect of scale. – Biol. Conserv. 73: 59–65.
- Thomas, J. A. 2005. Monitoring change in the abundance and distribution of insects using butterflies and other indicator groups. – Phil. Trans. R. Soc. B 360: 339–357.
- Tischendorf, L.  et  al. 2003. Evaluation of patch isolation metrics in mosaic landscapes for specialist vs. generalist dispersers. – Landscape Ecol. 18: 41–50.
- Tjørve, E. 2010. How to resolve the SLOSS debate: lessons from species-diversity models. – J. Theor. Biol. 264: 604–612.
- Triantis, K. A. et al. 2012. The island species–area relationship: biology and statistics. – J. Biogeogr. 39: 215–231.
- Tscharntke, T. and Brandl, R. 2004. Plant–insect interactions in fragmented landscapes. – Annu. Rev. Entomol. 49: 405–430.
- Tscharntke, T. et al. 2002. Characteristics of insect populations on habitat fragments: a mini review. – Ecol. Res. 17: 229–239.
- Warzecha, D.  et  al. 2016. Intraspecific body size increases with habitat fragmentation in wild bee pollinators. – Landscape Ecol. 31: 1449–1455.
- Watling, J. I. et al. 2020. Support for the habitat amount hypothesis from a global synthesis of species density studies. – Ecol. Lett. 23: 674–681.
- Westman, W. E. 1983. Island biogeography: studies on the xeric shrublands of the inner Channel Islands, California. – J. Biogeogr. 10: 97–118.
- Whittaker, R. J. and Fernández-Palacios, J. M. 2007. Island biogeography: ecology, evolution and conservation, 2nd edn. – Oxford Univ. Press.
- Williams, C. B. 1964. Patterns in the balance of nature. – Academic Press.
- Wilson, E. O. and MacArthur, R. H. 1967. The theory of island biogeography. – Princeton Univ. Press.
- Wilson, E. O. and Willis, E. O. 1975. Applied biogeography. – In: Cody, M. L. et al. (eds), Ecology and evolution of communities. Harvard Univ. Press, pp. 522–534.
- Yaacobi, G. et al. 2007. Habitat fragmentation may not matter to species diversity. – Proc. R. Soc. B 274: 2409–2412.
- Yang, Z. and Teller, J. T. 2005. Modeling the history of Lake of the Woods since 11 000 cal yr BP using GIS. – J. Paleolimnol. 33: 483–497.
- Zhang, J. et al. 2014. Sampling plant diversity and rarity at landscape scales: importance of sampling time in species detectability. – PLoS One 9: e95334.

16000587, 2021, 7, Downloaded from https://nsojournals.onlinelibrary.wiley.com/doi/10.1111/ecog.05563 by Faculdade Medicina De Lisboa, Wiley Online Library on [05/11/2025]. See the Terms and Conditions (https://onlinelibrary.wiley.com/terms-and-conditions) on Wiley Online Library for rules of use; OA articles are governed by the applicable Creative Commons License

1066



<!-- ===== Complementary: MacDonald2021_S1.xlsx.md ===== -->


<!-- page 1 of 5 -->

## manuscript\_information

| MacDonald, Z. G., Deane, D. C., Lamb, C. T., He, F., Acorn, J. H., and Nielsen, S. E. Distinguishing effects of area *per se* and isolation from the sample-area effect for true islands and habitat fragments. – Ecography. |
| --- |

<!-- page 2 of 5 -->

## butterfly\_abundance\_data

| isl_id | area_ha | easting | northing | plant_rich | isolation_250 | isolation_500 | isolation_1000 | isolation_2500 | isolation_5000 | solid_rock_shoreline | broken_rock_shoreline | beach_shoreline | shoreline_meadow | inland_meadow | short_shrubland | tall_shrubland | deciduous_woodland | coniferous_woodland | mixed_woodland | deciduous_forest | coniferous_forest | mixed_forest | inland_rock_outcrops | habitat_richness | P..canadensis | C..philodice | C..interior | P..oleracea | P..rapae | F..tarquinius | S..titus | S..liparops | S..calanus | C..lucia | C..neglecta | D..plexippus | L..arthemis.arthemis | S..cybele | V..virginiensis | V..cardui | V..atalanta | A..milberti | P..progne | P..gracilis | P..comma | P..cocyta | L..anthedon | M..cymela | E..icelus | C..palaemon | A..numitor | H..sassacus | T..lineola | P..peckius | P..themistocles | P..hobomok | E..dion | E..vestris | P..canadensis.hostplants | C..philodice.hostplants | C..interior.hostplants | P..oleracea.hostplants | P..rapae.hostplants | F..tarquinius.hostplants | S..titus.hostplants | S..liparops.hostplants | S..calanus.hostplants | C..lucia.hostplants | C..neglecta.hostplants | D..plexippus.hostplants | L..arthemis.hostplants | S..cybele.hostplants | V..virginiensis.hostplants | V..cardui.hostplants | V..atalanta.hostplants | A..milberti.hostplants | P..progne.hostplants | P..gracilis.hostplants | P..comma.hostplants | P..cocyta.hostplants | L..anthedon.hostplants | M..cymela.hostplants | E..icelus.hostplants | C..palaemon.hostplants | A..numitor.hostplants | H..sassacus.hostplants | T..lineola.hostplants | P..peckius.hostplants | P..themistocles.hostplants | P..hobomok.hostplants | E..dion.hostplants | E..vestris.hostplants |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 812 | 0.0851 | 419512 | 5445942 | 47 | 0.976278 | 0.9391527 | 0.8429512 | 0.6131599 | 0.505436617 | 35 | 0 | 0 | 10 | 15 | 5 | 30 | 0 | 5 | 0 | 0 | 0 | 0 | 0 | 6 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 1 | 1 | NA | 1 | 1 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 1 | 1 | 1 | 0 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 707 | 0.0906 | 416447 | 5444826 | 4 | 0.9997769 | 0.960628 | 0.8893364 | 0.7297673 | 0.654637521 | 97.5 | 0 | 0 | 0 | 2.5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | NA | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 543 | 0.0934 | 392055 | 5442638 | 29 | 0.9638154 | 0.9696171 | 0.9923761 | 0.8422862 | 0.769915244 | 90 | 0 | 0 | 0 | 2.5 | 0 | 7.5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 1 | 1 | NA | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 1 | 0 | 0 | 0 | 1 | 1 | 1 | 0 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 1218 | 0.0972 | 404819 | 5451529 | 17 | 0.9996761 | 0.9992988 | 0.918732 | 0.7292887 | 0.629208175 | 75 | 0 | 0 | 20 | 0 | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 0 | 0 | 0 | 0 | 8 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | NA | 1 | 1 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 0 | 0 | 1 | 1 | 1 | 0 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 0 |
| 177 | 0.0984 | 401010 | 5435434 | 20 | 0.996378 | 0.8544651 | 0.688861 | 0.5179846 | 0.478041705 | 80 | 0 | 0 | 0 | 0 | 15 | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | NA | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 0 | 1 | 1 | 0 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 0 |
| 1314 | 0.0989 | 404526 | 5453090 | 64 | 0.7468733 | 0.654714 | 0.6707345 | 0.6861004 | 0.633169396 | 10 | 2.5 | 0 | 7.5 | 0 | 5 | 0 | 5 | 0 | 0 | 70 | 0 | 0 | 0 | 6 | 1 | 0 | 0 | 0 | 10 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 1 | 1 | 1 | NA | 0 | 1 | 1 | 1 | 1 | 0 | 1 | 0 | 0 | 1 | 0 | 0 | 1 | 1 | 0 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 730 | 0.1051 | 418703 | 5445047 | 55 | 0.9888427 | 0.9388788 | 0.8710972 | 0.6568085 | 0.553116421 | 15 | 5 | 0 | 5 | 1 | 10 | 24 | 0 | 40 | 0 | 0 | 0 | 0 | 0 | 7 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 1 | 1 | NA | 1 | 1 | 1 | 1 | 1 | 0 | 0 | 1 | 0 | 1 | 1 | 1 | 1 | 1 | 0 | 1 | 1 | 1 | 0 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 992 | 0.107 | 404862 | 5447991 | 34 | 0.8941086 | 0.9240439 | 0.8922135 | 0.8123017 | 0.740720833 | 70 | 0 | 0 | 2.5 | 2.5 | 5 | 10 | 0 | 10 | 0 | 0 | 0 | 0 | 0 | 6 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 6 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 1 | 1 | NA | 1 | 1 | 0 | 1 | 1 | 0 | 1 | 0 | 0 | 0 | 0 | 1 | 1 | 1 | 0 | 0 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 736 | 0.1932 | 419841 | 5445119 | 63 | 0.9998958 | 0.9561305 | 0.8447248 | 0.6002664 | 0.499673928 | 20 | 5 | 0 | 10 | 5 | 5 | 50 | 0 | 5 | 0 | 0 | 0 | 0 | 0 | 7 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 1 | 1 | NA | 1 | 1 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 1 | 1 | 0 | 1 | 1 | 1 | 0 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 967 | 0.1962 | 396893 | 5447893 | 37 | 0.9993719 | 0.9337659 | 0.9581018 | 0.7805155 | 0.690567733 | 0 | 15 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 5 | 80 | 0 | 0 | 0 | 3 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 1 | 0 | 0 | NA | 1 | 1 | 0 | 1 | 1 | 0 | 1 | 0 | 0 | 0 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 1292 | 0.2037 | 405344 | 5452705 | 57 | 0.9331401 | 0.7656161 | 0.7252461 | 0.6845197 | 0.575460619 | 14 | 1 | 0 | 15 | 5 | 25 | 0 | 37.5 | 0 | 0 | 0 | 0 | 0 | 2.5 | 7 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 1 | 0 | 0 | NA | 1 | 1 | 0 | 1 | 1 | 0 | 1 | 0 | 0 | 0 | 0 | 1 | 1 | 1 | 0 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 1196 | 0.2132 | 403354 | 5450922 | 63 | 0.9951596 | 0.9629123 | 0.8733021 | 0.7273405 | 0.676656257 | 25 | 5 | 0 | 10 | 0 | 5 | 20 | 0 | 15 | 15 | 0 | 0 | 0 | 5 | 8 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 1 | 1 | 1 | NA | 1 | 1 | 1 | 1 | 1 | 0 | 1 | 1 | 0 | 1 | 0 | 1 | 0 | 0 | 0 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 1152 | 0.3955 | 401423 | 5450220 | 82 | 0.9081955 | 0.8783254 | 0.7824978 | 0.6867561 | 0.685190969 | 25 | 5 | 0 | 10 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 59 | 0 | 0 | 5 | 0 | 0 | 0 | 10 | 6 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 1 | 1 | NA | 1 | 0 | 1 | 1 | 1 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 1 | 1 | 0 | 0 | 1 | 1 | 0 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 500 | 0.4074 | 412659 | 5441417 | 32 | 0.9997115 | 0.999397 | 0.9446968 | 0.696943 | 0.544283574 | 10 | 0 | 0 | 0 | 0 | 10 | 62.5 | 15 | 2.5 | 0 | 0 | 0 | 0 | 0 | 5 | 0 | 0 | 0 | 0 | 5 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 1 | 1 | 1 | NA | 1 | 1 | 0 | 1 | 1 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 0 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 0 |
| 285 | 0.8252 | 391599 | 5437694 | 106 | 0.9687873 | 0.9254558 | 0.8626981 | 0.855478 | 0.773064148 | 5 | 5 | 0 | 2.5 | 0 | 2.5 | 25 | 0 | 5 | 0 | 0 | 55 | 0 | 0 | 7 | 0 | 0 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 3 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 1 | 1 | 1 | NA | 1 | 1 | 1 | 1 | 1 | 0 | 1 | 0 | 0 | 0 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 618 | 0.9439 | 400932 | 5443720 | 57 | 0.9910412 | 0.987548 | 0.9951929 | 0.9825681 | 0.812726356 | 5 | 5 | 0 | 15 | 2.5 | 15 | 52.5 | 0 | 2.5 | 0 | 0 | 0 | 0 | 2.5 | 8 | 0 | 0 | 0 | 0 | 10 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 1 | 1 | NA | 1 | 1 | 0 | 1 | 1 | 0 | 1 | 0 | 0 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 0 |
| 306 | 0.9454 | 395895 | 5437923 | 91 | 0.9994396 | 0.9438824 | 0.912408 | 0.9309408 | 0.940592268 | 15 | 1 | 0 | 14 | 10 | 24 | 15 | 0 | 20 | 0 | 0 | 0 | 0 | 1 | 8 | 0 | 0 | 0 | 18 | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 7 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 1 | 1 | 1 | NA | 1 | 1 | 1 | 1 | 1 | 0 | 1 | 0 | 0 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 637 | 0.9505 | 400742 | 5443974 | 73 | 0.9899429 | 0.9883033 | 0.995339 | 0.9832401 | 0.827588141 | 10 | 5 | 0 | 10 | 5 | 50 | 10 | 0 | 5 | 0 | 0 | 0 | 0 | 5 | 8 | 0 | 0 | 0 | 0 | 6 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 1 | 1 | NA | 1 | 1 | 0 | 1 | 1 | 0 | 1 | 0 | 0 | 1 | 1 | 1 | 1 | 1 | 0 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 0 |
| 802 | 0.9573 | 414356 | 5445871 | 77 | 0.998932 | 0.9925446 | 0.9366482 | 0.8800296 | 0.641005022 | 7.5 | 2.5 | 0.1 | 5 | 0 | 20 | 35 | 0 | 25 | 0 | 0 | 0 | 0 | 5 | 8 | 0 | 0 | 0 | 1 | 13 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 1 | 1 | NA | 1 | 1 | 1 | 1 | 1 | 0 | 0 | 0 | 0 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 537 | 0.9697 | 395094 | 5442435 | 90 | 0.8678306 | 0.768942 | 0.9189056 | 0.9389059 | 0.906227542 | 7.5 | 2.5 | 0 | 10 | 5 | 20 | 15 | 0 | 30 | 0 | 0 | 10 | 0 | 0 | 8 | 0 | 0 | 0 | 4 | 3 | 0 | 5 | 0 | 2 | 0 | 2 | 0 | 1 | 0 | 1 | 0 | 9 | 0 | 3 | 1 | 0 | 6 | 0 | 1 | 0 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 1 | 1 | 1 | NA | 1 | 1 | 1 | 1 | 1 | 0 | 1 | 1 | 0 | 0 | 0 | 1 | 1 | 1 | 0 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 874 | 0.9816 | 402331 | 5446861 | 81 | 0.811234 | 0.6217065 | 0.7216415 | 0.8129516 | 0.799541208 | 9 | 1 | 1 | 1 | 4 | 14 | 25 | 30 | 0 | 5 | 0 | 0 | 0 | 10 | 10 | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 1 | 1 | 1 | NA | 1 | 1 | 1 | 1 | 1 | 0 | 1 | 0 | 0 | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 737 | 1.0207 | 415873 | 5445135 | 71 | 0.9994938 | 0.9781615 | 0.9604586 | 0.7806593 | 0.655971452 | 9 | 1 | 0 | 10 | 2.5 | 17.5 | 49 | 10 | 0 | 0 | 0 | 0 | 0 | 1 | 8 | 0 | 0 | 0 | 1 | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 1 | 1 | NA | 1 | 1 | 0 | 1 | 1 | 0 | 1 | 0 | 0 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 451 | 1.0218 | 411910 | 5440824 | 70 | 0.9986454 | 0.9532694 | 0.9127541 | 0.6430513 | 0.460729145 | 9 | 1 | 0 | 2.5 | 0 | 15 | 45 | 10 | 5 | 7.5 | 0 | 0 | 0 | 5 | 9 | 0 | 0 | 0 | 0 | 26 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 1 | 1 | 1 | NA | 1 | 1 | 0 | 1 | 1 | 0 | 1 | 0 | 0 | 1 | 1 | 1 | 1 | 1 | 0 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 621 | 1.8339 | 411892 | 5443553 | 112 | 0.9540595 | 0.8939958 | 0.8195473 | 0.878303 | 0.683919127 | 5 | 5 | 0.1 | 2.5 | 10 | 15 | 25 | 10 | 15 | 10 | 0 | 0 | 0 | 2.5 | 11 | 3 | 0 | 0 | 1 | 8 | 1 | 0 | 0 | 0 | 10 | 11 | 0 | 11 | 0 | 0 | 0 | 7 | 0 | 0 | 0 | 0 | 1 | 0 | 7 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 1 | 1 | 1 | NA | 1 | 1 | 1 | 1 | 1 | 0 | 1 | 0 | 0 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 152 | 1.9761 | 394475 | 5434831 | 102 | 0.9990445 | 0.9480383 | 0.9675077 | 0.909231 | 0.918301762 | 2.5 | 1 | 2.5 | 1 | 8 | 7.5 | 7.5 | 0 | 10 | 0 | 0 | 60 | 0 | 0 | 9 | 0 | 0 | 0 | 0 | 11 | 0 | 0 | 0 | 1 | 1 | 2 | 0 | 1 | 1 | 0 | 0 | 11 | 0 | 8 | 0 | 4 | 1 | 13 | 1 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 1 | 1 | 1 | NA | 1 | 1 | 1 | 1 | 1 | 0 | 1 | 1 | 0 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 1146 | 2.0495 | 399266 | 5450045 | 131 | 0.9190247 | 0.7155196 | 0.6123127 | 0.601852 | 0.670083071 | 2.5 | 2.5 | 0.1 | 1 | 1 | 15 | 25 | 25 | 0 | 20 | 5 | 0 | 0 | 3 | 11 | 2 | 0 | 2 | 9 | 0 | 0 | 0 | 0 | 0 | 6 | 9 | 0 | 2 | 0 | 0 | 1 | 2 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 1 | 1 | 1 | NA | 1 | 1 | 1 | 1 | 1 | 0 | 1 | 0 | 0 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 558 | 2.1064 | 395074 | 5442833 | 95 | 0.9946451 | 0.9567228 | 0.9266174 | 0.9210016 | 0.895193707 | 9 | 1 | 0 | 9 | 1 | 10 | 10 | 0 | 30 | 30 | 0 | 0 | 0 | 0 | 8 | 1 | 0 | 0 | 5 | 8 | 0 | 0 | 4 | 0 | 0 | 9 | 0 | 1 | 0 | 0 | 0 | 5 | 0 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1 | 1 | 1 | NA | 1 | 1 | 1 | 1 | 1 | 0 | 1 | 1 | 0 | 0 | 1 | 1 | 1 | 1 | 0 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 505 | 3.9847 | 410647 | 5441427 | 152 | 0.9971401 | 0.9347221 | 0.789505 | 0.6199093 | 0.474051895 | 5 | 1 | 1 | 2.5 | 1 | 5 | 30 | 2.5 | 5 | 1 | 5 | 25 | 15 | 1 | 14 | 2 | 0 | 0 | 27 | 3 | 0 | 0 | 0 | 0 | 5 | 0 | 0 | 9 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 25 | 2 | 14 | 0 | 0 | 3 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 1 | 1 | 1 | 1 | 1 | NA | 1 | 1 | 1 | 1 | 1 | 0 | 1 | 1 | 1 | 1 | 0 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 642 | 4.0207 | 393592 | 5444084 | 159 | 0.9429391 | 0.7915043 | 0.6365269 | 0.7897051 | 0.756004069 | 2.5 | 2.5 | 0.1 | 2.5 | 2.5 | 10 | 10 | 10 | 5 | 10 | 0 | 10 | 20 | 15 | 13 | 0 | 0 | 0 | 52 | 14 | 0 | 0 | 0 | 2 | 0 | 16 | 0 | 4 | 3 | 0 | 0 | 42 | 0 | 2 | 0 | 0 | 0 | 5 | 15 | 0 | 4 | 2 | 1 | 0 | 0 | 0 | 6 | 0 | 0 | 1 | 1 | 1 | 1 | 1 | NA | 1 | 1 | 1 | 1 | 1 | 0 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 755 | 8.3669 | 418218 | 5445116 | 167 | 0.9770612 | 0.9226979 | 0.7681061 | 0.6685349 | 0.56573173 | 4 | 0.1 | 0.1 | 1 | 5 | 20 | 15 | 5 | 5 | 20 | 0 | 0 | 20 | 5 | 12 | 3 | 1 | 11 | 2 | 3 | 0 | 2 | 9 | 0 | 4 | 21 | 0 | 20 | 1 | 0 | 0 | 5 | 1 | 6 | 0 | 0 | 2 | 3 | 66 | 1 | 4 | 1 | 0 | 0 | 1 | 2 | 13 | 0 | 0 | 1 | 1 | 1 | 1 | 1 | NA | 1 | 1 | 1 | 1 | 1 | 0 | 1 | 1 | 1 | 1 | 0 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |

<!-- page 3 of 5 -->

## habitat\_type\_descriptions

| Habitat class | Vegetation characteristics | Substrate characteristics | # of island occurrences |
| --- | --- | --- | --- |
| Solid rock shoreline | &lt;10% vegetation cover | granite gneiss rock | 29 |
| Broken rock shoreline | 0 - 75% vegetation cover | mix of cobble and boulder | 23 |
| Beach shoreline | &lt;10% vegetation cover | course to fine sand | 8 |
| Shoreline meadow | herbaceous angiosperms adjacent to shoreline | some soil development | 25 |
| Inland meadow | herbaceous angiosperms disjunct from shoreline | some soil development | 20 |
| Short shrubland | woody vegetation ≤ 1 m | some soil development | 27 |
| Tall shrubland | woody vegetation > 1 m | some soil development | 24 |
| Deciduous woodland | deciduous tree species; ≤ 75% canopy coverage | soil with major organic component | 11 |
| Coniferous woodland | coniferous tree species; ≤ 75% canopy coverage | soil with major organic component | 19 |
| Mixed woodland | both deciduous and coniferous tree species; ≤ 75% canopy coverage | soil with major organic component | 10 |
| Deciduous forest | deciduous tree species; > 75% canopy coverage | soil with major organic component | 4 |
| Coniferous forest | coniferous tree species; > 75% canopy coverage | soil with major organic component | 6 |
| Mixed forest | both deciduous and coniferous tree species; > 75% canopy coverage | soil with major organic component | 3 |
| Inland rock outcrops | &lt;10% vegetation cover | granite gneiss rock | 14 |

<!-- page 4 of 5 -->

## functional\_trait\_data

| family | species_full | species | wingspan | total_abundance | prevalence | total_hostplant_occurrences | occurences_without_hostplant |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Papilionidae | Papilio canadensis | P..canadensis | 71.5 | 12 | 6 | 28 | 0 |
| Pieridae | Colias philodice | C..philodice | 43 | 1 | 1 | 11 | 0 |
| Pieridae | Colias interior | C..interior | 41 | 15 | 3 | 17 | 0 |
| Pieridae | Pieris oleracea | P..oleracea | 41 | 132 | 13 | 26 | 0 |
| Pieridae | Pieris rapae | P..rapae | 39.5 | 153 | 24 | 26 | 1 |
| Lycaenidae | Feniseca tarquinius | F..tarquinius | 27.5 | 1 | 1 | NA | NA |
| Lycaenidae | Satyrium titus | S..titus | 28 | 7 | 2 | 26 | 0 |
| Lycaenidae | Satyrium liparops | S..liparops | 24.5 | 15 | 4 | 26 | 0 |
| Lycaenidae | Satyrium calanus | S..calanus | 28.5 | 5 | 3 | 16 | 0 |
| Lycaenidae | Celastrina lucia | C..lucia | 26 | 27 | 6 | 28 | 0 |
| Lycaenidae | Celastrina neglecta | C..neglecta | 26 | 77 | 11 | 26 | 0 |
| Nymphalidae | Danaus plexippus | D..plexippus | 99 | 1 | 1 | 0 | 1 |
| Nymphalidae | Limenitis arthemis | L..arthemis | 62.5 | 55 | 14 | 21 | 1 |
| Nymphalidae | Speyeria cybele | S..cybele | 75 | 6 | 4 | 8 | 1 |
| Nymphalidae | Vanessa virginiensis | V..virginiensis | 46.5 | 1 | 1 | 3 | 1 |
| Nymphalidae | Vanessa cardui | V..cardui | 54 | 1 | 1 | 19 | 0 |
| Nymphalidae | Vanessa atalanta | V..atalanta | 51 | 111 | 19 | 17 | 1 |
| Nymphalidae | Aglais milberti | A..milberti | 43 | 2 | 2 | 23 | 0 |
| Nymphalidae | Polygonia progne | P..progne | 43.5 | 23 | 7 | 26 | 1 |
| Nymphalidae | Polygonia gracilis | P..gracilis | 38.5 | 1 | 1 | 26 | 0 |
| Nymphalidae | Polygonia comma | P..comma | 46.5 | 4 | 1 | 13 | 0 |
| Nymphalidae | Phyciodes cocyta | P..cocyta | 30 | 36 | 6 | 24 | 0 |
| Nymphalidae | Lethe anthedon | L..anthedon | 48 | 28 | 6 | 30 | 0 |
| Nymphalidae | Megisto cymela | M..cymela | 35.5 | 106 | 7 | 30 | 0 |
| Hesperiidae | Erynnis icelus | E..icelus | 26.5 | 1 | 1 | 21 | 0 |
| Hesperiidae | Carterocephalus palaemon | C..palaemon | 25.5 | 13 | 5 | 30 | 0 |
| Hesperiidae | Ancyloxypha numitor | A..numitor | 21.5 | 8 | 5 | 30 | 0 |
| Hesperiidae | Hesperia sassacus | H..sassacus | 27.5 | 1 | 1 | 30 | 0 |
| Hesperiidae | Thymelicus lineola | T..lineola | 22.5 | 1 | 1 | 30 | 0 |
| Hesperiidae | Polites peckius | P..peckius | 23 | 1 | 1 | 30 | 0 |
| Hesperiidae | Polites themistocles | P..themistocles | 23.5 | 2 | 1 | 30 | 0 |
| Hesperiidae | Poanes hobomok | P..hobomok | 28 | 20 | 3 | 30 | 0 |
| Hesperiidae | Euphyes dion | E..dion | 32 | 1 | 1 | 24 | 0 |
| Hesperiidae | Euphyes vestris | E..vestris | 25 | 1 | 1 | 24 | 0 |

<!-- page 5 of 5 -->

## larval\_host\_plants

|  | larval host plants ( Acorn &amp; Sheldon, 2017): | Salix spp., Populus spp., Acer spp., Prunus spp., Malus sylvestris, Fraxinis spp. | Many Fabaceae, particulalry Trifolium repens and Medicago sativa | Vaccinium spp. | Dentaria diphylla and relatives | Brassicaceae, particularly cultivated plants | Our only carnivorous butterfly--feeds on aphids | Salix spp. | Quercus spp., Carya spp., and Juglans spp., | Prunus spp., Amelanchier alnifolia, Quercus spp., Salix spp., Populus spp., Vaccinium spp. | Viburnum spp., Cornus spp., Prunus spp., Spiraea alba, Vaccinium spp., Rhododendron groenlandicum, Celastrus scandens | Cornus spp. and Ceanothus americanus (Southern ON) | Asclepias spp. | Salix spp., Populus spp., and Betula spp. | Viola spp. | Various Asteraceae | Cirsium spp. and Carduus spp. | Urticaceae | Urtica spp. | Laportea canadensis, Ulmus spp., and Humulus lupulus | Ribes spp. | Ribes spp. | Symphyotrichum spp., Oclemena spp., Doellingeria spp., and Eurybia spp. | Poaceae | Poaceae | Populus spp., Salix spp., and Betula spp. | Poaceae | Poaceae | Many Poaceae, Phleum pratense is preferred | Poaceae | Poaceae | Poaceae | Poaceae | Carex spp. | Carex spp. |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | larval host plants (Hall et al., 2014;): | Fraxinus spp., Salix spp., Populus spp., and Prunus spp. | Many different legumes (Fabaceae) | Vaccinium spp. | Brassicaceae, particularly Cardamine (Dentaria) spp. Turritis spp., and Arabis spp. | Brassicaceae, particularly Brassica oleraceae | Our only carnivorous butterfly--feeds on aphids | Prunus spp., particularly P. serotina and P.virginiana | Quercus spp., Carya spp., and Juglans cinerea | Rosaceae, including Prunus spp., Crataegus spp., and Vaccinium spp. | Prunus spp., Viburnum lantanoides, V. lentago, and Vaccinium spp. | Cornus spp., Ceanothus americanus, Spiraea spp., and Vibernum spp. | Asclepias spp. | Salix spp., Populus spp., and Betula spp. | Viola spp. | Asteraceae, including Antennaria spp. and Gnaphalium spp. | Asteraceae, including Cirsium spp., Carduus spp., Centaurea spp., and Arctium spp. | Urticaceae, including Urtica dioica and Laportea canadensis | Urtica spp., Salix spp., and Helianthus spp. | Laportea canadensis, Ulmus spp., and Humulus lupulus | Ribes spp. | Ribes spp. | Symphyotrichum spp., Oclemena spp., Doellingeria spp., and Eurybia spp. | Poaceae, including Brachyelytrum erectum | Poaceae, including Poa pratensis and Dactylis glomerata | Populus spp., Salix spp., and Betula spp. | Poaceae, including Calamagrostis spp. and Bromus spp. | Poaceae, including Poa spp. and Leersia oryzoides | Many Poaceae, Phleum pratense is preferred | Schizachyrium scoparium, Danthonia spicata, and Panicum spp. | Poaceae, including Poa pratensis, Schizachyrium scoparium | Many Poacaea spp., especially Panicum spp., Digitaria spp., and Poa spp. | Poaceae, including Panicum spp. and Poa spp. | Sedges, including Carex lacustris, C. hyalinolepis, C. stricta, and C. acutiformis | Many different sedges (Cyperaceae) |
| family | species | P. canadensis | C. philodice | C. interior | P. oleracea | P. rapae | F. tarquinius | S. titus | S. calanus | S. liparops | C. lucia | C. neglecta | D. plexippus | L. arthemis | S. cybele | V. virginiensis | V. cardui | V. atalanta | A. milberti | P. comma | P. progne | P. gracilis | P. cocyta | L. anthedon | M. cymela | E. icelus | C. palaemon | A. numitor | T. lineola | H. sassacus | P. peckius | P. themistocles | P. hobomok | E. dion | E. vestris |
| Aceraceae | Acer negundo | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Aceraceae | Acer rubrum | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Aceraceae | Acer spicatum | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Alismataceae | Sagittaria rigida | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Anacardiaceae | Rhus glabra | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Anacardiaceae | Toxicodendron rydbergii | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Apiaceae | Heracleum maximum | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Apiaceae | Osmorhiza longistylis | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Apiaceae | Sium suave | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Apocynaceae | Apocynum androsaemifolium | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Apocynaceae | Apocynum cannibanum | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Araliaceae | Aralia hispida | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Araliaceae | Aralia nudicaulis | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Asteraceae | Achillea millefolium | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Asteraceae | Ambrosia artemisiifolia | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Asteraceae | Anaphalis margaritacea | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Asteraceae | Antennaria neglecta | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Asteraceae | Antennaria parvifolia | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Asteraceae | Bidens cernua | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Asteraceae | Bidens connata | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Asteraceae | Bidens frondosa | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Asteraceae | Cirsium arvense | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Asteraceae | Cirsium vulgare | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Asteraceae | Erigeron canadensis | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Asteraceae | Erigeron strigosus | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Asteraceae | Erigeron philadelphicus | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Asteraceae | Eupatorium perfoliatum | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Asteraceae | Eurybia macrophylla | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Asteraceae | Euthamia graminifolia | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Asteraceae | Hieracium scabrum | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Asteraceae | Hieracium umbellatum | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Asteraceae | Lactuca biennis | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Asteraceae | Lactuca canadensis | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Asteraceae | Lactuca ludoviciana | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Asteraceae | Solidago gigantea | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Asteraceae | Solidago nemoralis | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Asteraceae | Sonchus asper | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Asteraceae | Symphyotrichum ciliolatum | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Asteraceae | Symphyotrichum lanceolatum | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Asteraceae | Taraxacum officinale | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Asteraceae | Xanthium strumarium | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Balsaminaceae | Impatiens capensis | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Betulaceae | Alnus incana | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Betulaceae | Alnus viridis | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Betulaceae | Betula papyrifera | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Betulaceae | Corylus cornuta | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Boraginaceae | Hackelia deflexa | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Boraginaceae | Myosotis sp. 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Brassicaceae | Barbarea orthoceras | 0 | 0 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Brassicaceae | Boechera grahamii | 0 | 0 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Brassicaceae | Boechera stricta | 0 | 0 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Brassicaceae | Cardamine parviflora | 0 | 0 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Brassicaceae | Cardamine pensylvanica | 0 | 0 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Brassicaceae | Erysimum cheiranthoides | 0 | 0 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Brassicaceae | Rorippa palustris | 0 | 0 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Campanulaceae | Campanula rotundifolia | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Campanulaceae | Triodanis perfoliata | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Caprifoliaceae | Diervilla lonicera | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Caprifoliaceae | Lonicera canadensis | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Caprifoliaceae | Lonicera dioica | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Caprifoliaceae | Sambucus racemosa | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Caprifoliaceae | Symphoricarpos albus | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Caprifoliaceae | Viburnum lentago | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Caprifoliaceae | Viburnum rafinesquianum | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Caryophyllaceae | Cerastium arvense | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Caryophyllaceae | Cerastium fontanum | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Caryophyllaceae | Moehringia laterifolia | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Caryophyllaceae | Silene antirrhina | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Caryophyllaceae | Stellaria longifolia | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Celastraceae | Celastrus scandens | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Chenopodiaceae | Chenopodium album | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Chenopodiaceae | Chenopodium berlandierii | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Chenopodiaceae | Chenopodium simplex | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Convolvulaceae | Calystegia sepium | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Cornaceae | Cornus alba | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Cornaceae | Cornus canadensis | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Cornaceae | Cornus rugosa | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Cupressaceae | Juniperus communis | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Cupressaceae | Juniperus horizontalis | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Cupressaceae | Thuja occidentalis | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Cuscutaceae | Cuscuta pentagona | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Cyperaceae | Carex aquatilis | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 |
| Cyperaceae | Carex atherodes | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 |
| Cyperaceae | Carex backii | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 |
| Cyperaceae | Carex brunnescens | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 |
| Cyperaceae | Carex intumescens | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 |
| Cyperaceae | Carex lasiocarpa | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 |
| Cyperaceae | Carex peckii | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 |
| Cyperaceae | Carex pellita | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 |
| Cyperaceae | Carex pensylvanica | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 |
| Cyperaceae | Carex siccata | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 |
| Cyperaceae | Carex sp. 10 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 |
| Cyperaceae | Carex sp. 11 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 |
| Cyperaceae | Carex sp. 11 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 |
| Cyperaceae | Carex sp. 14 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 |
| Cyperaceae | Carex sp. 15 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 |
| Cyperaceae | Carex sp. 17 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 |
| Cyperaceae | Carex sp. 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 |
| Cyperaceae | Carex sp. 6 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 |
| Cyperaceae | Carex sp. 8 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 |
| Cyperaceae | Carex stricta | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 |
| Cyperaceae | Carex trisperma | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 |
| Cyperaceae | Cyperaceae sp. 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Cyperaceae | Cyperus odoratus | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Cyperaceae | Cyperus squarrosus | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Cyperaceae | Eleocharis acicularis | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Cyperaceae | Eleocharis palustris | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Cyperaceae | Schoenoplectus acutus | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Cyperaceae | Schoenoplectus heterochaetus | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Cyperaceae | Schoenoplectus pungens | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Cyperaceae | Schoenoplectus tabernaemontani | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Cyperaceae | Scirpus cyperinus | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Dennstaedtiaceae | Pteridium aquilinum | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Dryopteridaceae | Athyrium filix-femina | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Dryopteridaceae | Dryopteris carthusiana | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Dryopteridaceae | Gymnocarpium dryopteris | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Dryopteridaceae | Matteuccia struthiopteris | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Dryopteridaceae | Woodsia ilvensis | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Equisetaceae | Equisetum arvense | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Equisetaceae | Equisetum sylvaticum | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Ericaceae | Arctostaphylos uva-ursi | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Ericaceae | Vaccinium angustifolium | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Ericaceae | Vaccinium caespitosum | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Ericaceae | Vaccinium myrtilloides | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Fabaceae | Astragalus canadensis | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Fabaceae | Glycyrrhiza lepidota | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Fabaceae | Lathyrus ochroleucus | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Fabaceae | Lathyrus palustris | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Fabaceae | Strophostyles leiosperma | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Fabaceae | Vicia americana | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Fagaceae | Quercus macrocarpa | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Fumariaceae | Capnoides sempervirens | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Fumariaceae | Corydalis aurea | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Fumariaceae | Dicentra cucullaria | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Geraniaceae | Geranium bicknellii | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Grossulariaceae | Ribes americanum | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Grossulariaceae | Ribes glandulosum | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Grossulariaceae | Ribes hirtellum | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Grossulariaceae | Ribes sp. 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Grossulariaceae | Ribes triste | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Hypericaceae | Hypercium majus | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Juncaceae | Juncus balticus | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Juncaceae | Juncus dudleyi | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Juncaceae | Juncus interior | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Lamiaceae | Dracocephalum parviflorum | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Lamiaceae | Galeopsis tetrahit | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Lamiaceae | Lycopus americanus | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Lamiaceae | Lycopus asper | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Lamiaceae | Mentha arvensis | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Lamiaceae | Scutellaria galericulata | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Lamiaceae | Scutellaria laterifolia | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Lamiaceae | Stachys arenicola | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Lamiaceae | Stachys pilosa | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Liliaceae | Maianthemum canadense | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Liliaceae | Maianthemum racemosum | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Liliaceae | Maianthemum stellatum | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Liliaceae | Polygonatum pubescens | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Liliaceae | Trillium cernuum | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Liliaceae | Uvularia sessilifolia | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Lycopodiaceae | Dendrolycopodium dendroideum | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Oleaceae | Fraxinus nigra | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Oleaceae | Fraxinus pensylvanica | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Onagraceae | Circaea lutetiana | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Onagraceae | Epilobium angustifolium | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Onagraceae | Epilobium ciliatum | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Onagraceae | Oenothera oakesiana | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Onagraceae | Oenothera biennis | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Ophioglossaceae | Botrypus virginianus | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Orchidaceae | Cypripedium acaule | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Oxalidaceae | Oxalis stricta | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Pinaceae | Abies balsamea | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Pinaceae | Picea glauca | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Pinaceae | Pinus banksiana | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Pinaceae | Pinus resinosa | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Pinaceae | Pinus strobus | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Plantaginaceae | Plantago major | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Poaceae | Agrostis scabra | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 0 |
| Poaceae | Alopecurus aequalis | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 0 |
| Poaceae | Anthoxanthum hirtum | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 0 |
| Poaceae | Bromus ciliatus | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 0 |
| Poaceae | Calamagrostis canadensis | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 0 |
| Poaceae | Cinna latifolia | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 0 |
| Poaceae | Danthonia spicata | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 0 |
| Poaceae | Dichanthelium acuminatum | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 0 |
| Poaceae | Echinochloa walteri | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 0 |
| Poaceae | Elymus trachycaulis | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 0 |
| Poaceae | Glyceria borealis | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 0 |
| Poaceae | Muhlenbergia sylvatica | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 0 |
| Poaceae | Oryzopsis asperifolia | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 0 |
| Poaceae | Panicum capillare | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 0 |
| Poaceae | Phalaris arundinaceae | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 0 |
| Poaceae | Phragmites australis | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 0 |
| Poaceae | Piptatherum pungens | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 0 |
| Poaceae | Poa glauca | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 0 |
| Poaceae | Poa inteior | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 0 |
| Poaceae | Poa palustris | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 0 |
| Poaceae | Poa pratensis | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 0 |
| Poaceae | Poaceae sp. 5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 0 |
| Poaceae | Schizachne purparescens | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 0 |
| Poaceae | Zizania palustris | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 0 |
| Polemoniaceae | Collomia linearis | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Polygonaceae | Fallopia cilinodis | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Polygonaceae | Fallopia scandens | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Polygonaceae | Persicaria amphibia | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Polygonaceae | Persicaria lapathifolia | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Polygonaceae | Persicaria punctata | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Polygonaceae | Persicaria sagittata | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Polygonaceae | Polygonum douglasii | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Polygonaceae | Rumex fueginus | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Polygonaceae | Rumex triangulivalvis | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Polypodiaceae | Polypodium virginianum | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Portulacaceae | Portulaca oleracea | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Primulaceae | Lysimachia ciliata | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Primulaceae | Lysimachia terrestris | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Primulaceae | Trientalis borealis | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Pyrolaceae | Chimaphila umbellata | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Pyrolaceae | Pyrola asarifolia | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Ranunculaceae | Actaea rubra | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Ranunculaceae | Anemone canadensis | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Ranunculaceae | Aquilegia canadensis | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Ranunculaceae | Ranunculus abortivus | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Ranunculaceae | Ranunculus flammula | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Ranunculaceae | Ranunculus macounii | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Ranunculaceae | Ranunculus pensylvanicus | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Rosaceae | Amelanchier sanguinea | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Rosaceae | Crataegus sp. 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Rosaceae | Drymocallis arguta | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Rosaceae | Fragaria virginiana | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Rosaceae | Geum aleppicum | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Rosaceae | Geum canadense | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Rosaceae | Potentilla norveigica | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Rosaceae | Potentilla rivalis | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Rosaceae | Prunus pensylvanica | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Rosaceae | Prunus virginiana | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Rosaceae | Rosa acicularis | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Rosaceae | Rosa blanda | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Rosaceae | Rosa woodsii | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Rosaceae | Rubus idaeus | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Rosaceae | Rubus pubescens | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Rosaceae | Sibbaldia tridentata | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Rosaceae | Sorbus aucuparia | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Rosaceae | Sorbus decora | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Rosaceae | Spiraea alba | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Rubiaceae | Galium aparine | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Rubiaceae | Galium boreale | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Rubiaceae | Galium trifidum | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Rubiaceae | Galium triflorum | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Rubiaceae | Houstonia longifolia | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Salicaceae | Populus tremuloides | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Salicaceae | Salix amygdaloides | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Salicaceae | Salix bebbiana | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Salicaceae | Salix discolor | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Salicaceae | Salix eriocephala | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Salicaceae | Salix humilis | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Salicaceae | Salix interior | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Salicaceae | Salix petiolaris | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Salicaceae | Salix planifolia | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Salicaceae | Salix serissima | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Salicaceae | Salix sp. 2 | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Salicaceae | Salix sp. 5 | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Santalaceae | Comandra umbellata | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Saxifragaceae | Heuchera richardsonii | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Saxifragaceae | Mitella nuda | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Scrophulariaceae | Agalinis tenuifolia | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Scrophulariaceae | Penstemon sp. 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Scrophulariaceae | Verbascum thapsus | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Scrophulariaceae | Veronica peregrina | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Selaginellaceae | Selaginella rupestris | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Smilacaceae | Smilax herbacea | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Solanaceae | Solanum ptychanthum | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Sparganiaceae | Sparganium eurycarpum | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Taxaceae | Taxus canadensis | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Tiliaceae | Tilia americana | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Typhaceae | Typha latifolia | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Ulmaceae | Ulmus americana | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Urticaceae | Urtica dioica | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Verbenaceae | Verbena hastata | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Violaceae | Viola canadensis | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Violaceae | Viola novae-angliae | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Violaceae | Viola sp. 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Vitaceae | Parthenocissus quinquefolia | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |