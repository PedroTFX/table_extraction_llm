Research

# Distinguishing effects of area per se and isolation from the sample-area effect for true islands and habitat fragments

Zachary G. MacDonald, David C. Deane, Fangliang He, Clayton T. Lamb, Felix A. H. Sperling, John H. Acorn and Scott E. Nielsen

Z. G. MacDonald (https://orcid.org/0000-0002-7966-5712) ✉ (zmacdona@ualberta.ca), D. C. Deane (https://orcid.org/0000-0003-2144-624X), F. He (https://orcid.org/0000-0003-0774-4849), J. H. Acorn (https://orcid.org/0000-0001-6570-1949) and S. E. Nielsen (https://orcid.org/0000-0002-9754- 0630), Dept of Renewable Resources, Univ. of Alberta, Edmonton, Alberta, Canada. – C. T. Lamb (https://orcid.org/0000-0002-1961-0509), Univ. of British Columbia, Dept of Biology, Kelowna, British Columbia, Canada. – F. A. H. Sperling (https://orcid.org/0000-0001-5148-4226), Dept of Biological Sciences, Univ. of Alberta, Edmonton, Alberta, Canada.

Ecography 44: 1051–1066, 2021 doi: 10.1111/ecog.05563

Subject Editor: Henrique Pereira Editor-in-Chief: Miguel Araújo Accepted 21 March 2021

![](images/b904310f8f75351ddfdbf8b02105bfa89a61c9d941de8807b9da3ef856910f60.jpg)

The island species area relationship (ISAR) is an important tool for measuring variation in species diversity in variety of insular systems, from true-island archipelagoes to fragmented terrestrial landscapes. However, it sufers from several limitations. For example, due to the sample-area efect, positive relationships between species and area cannot be directly interpreted as evidence for deterministic efects of area per se. Additionally, richness-based analyses may obscure species-level responses to area and isolation that may better inform conservation practice. Here, we use random placement models to control for variation in abundance, occupancy and richness associated with the sample-area efect, allowing deterministic efects of area and isolation, and how they vary with species’ functional traits, to be resolved using linear mixed efects models. We demonstrate the utility of this approach using a butterfly assemblage persisting on a naturally fragmented landscape of lake islands. The ISAR did not significantly deviate from random placement in relation to island area, isolation or habitat diversity, supporting stochastic assembly consistent with the sample-area efect. Such inferences support the habitat amount hypothesis, which prioritizes preserving the maximum amount of habitat irrespective of its degree of fragmentation. However, species-level analyses demonstrated that species’ abundances were significantly lower on both smaller and more isolated islands than what is predicted by the sample-area efect. Moreover, efects of area per se were significantly greater for smaller, less mobile and rare species. Species’ occurrences also significantly deviated from predictions of the sample-area efect in relation to island isolation. Thus, our approach illustrates that richness-based analyses not only result in incorrect inferences on mechanisms underlying ISARs, but also obscure important efects of area per se and isolation on individual species that vary with functional traits. We therefore suggest that these efects should not be solely inferred from richness-based analyses, but rather evaluated on a speciesby-species basis.

Keywords: functional traits, habitat amount hypothesis, habitat fragmentation, island biogeography, sampling efects, species–area relationship

## Introduction

From true islands to habitat fragments on terrestrial landscapes, positive relationships between species richness and the area of islands or fragments are among the oldest and most widely documented patterns in ecology (Arrhenius 1921, MacArthur and Wilson 1963, Rosenzweig 1995, Gotelli and Graves 1996, He and Legendre 2002, Hanski  et  al. 2013). These island species-area relationships (ISARs, sensu Triantis et al. 2012, or ‘Type IV’ curves, sensu Scheiner 2003) have received considerable attention, in part due to their importance to conservation frameworks (reviewed by Shafer 1990, Lomolino 2000, Whittaker and Fernández-Palacios 2007). Although there are several documented divergences between the biogeographies of true islands and terrestrial habitat fragments (Laurance 2008, Mendenhall et al. 2014, Itescu 2019, Farneda  et  al. 2020), studies addressing trueisland systems can still help resolve what mechanisms underlie ISARs and how fragmentation efects are best measured (Diamond 1975, Simberlof and Abele 1976, 1982, Haila 2002, Haddad  et  al. 2015, MacDonald  et  al. 2018a, b). There are, however, at least two enduring problems with the use of ISARs in conservation that are generalizable to both true islands and habitat fragments: 1) ISARs may emerge from a combination of diferent mechanisms, each of which potentially informs a diferent conservation directive (Connor and McCoy 1979, Kadmon and Allouche 2007, MacDonald et al. 2018b); and 2) ISARs are emergent patterns of diversity that can mask diferential responses to habitat area among species that may require independent consideration for successful conservation planning (Ewers and Didham 2006, Öckinger et al. 2009, Franzén et al. 2012, Hanski 2015, MacDonald et al. 2018a). Here, we propose an approach to addressing each of these problems within a single modelling framework.

## Mechanisms underlying ISARs

Three hypotheses, each with distinct underlying mechanisms and conservation implications, have been proposed to account for ISARs and related spatial patterns of species richness: 1) the passive sampling hypothesis (Connor and McCoy 1979); 2) area per se, as outlined by the theory of island biogeography (MacArthur and Wilson 1963, Wilson and MacArthur 1967); and 3) the habitat diversity hypothesis (Williams 1964). The passive sampling hypothesis, originally developed within the context of oceanic islands, predicts that islands randomly sample individuals from the regional species pool in abundances proportional to their area (Connor and McCoy 1979). As larger islands sample more individuals, they sample more species according to the abundance distribution of the regional species pool (i.e. the ‘sample-area efect’). Thus, passive sampling serves as a useful null hypothesis, assuming random assembly of both individuals and species.

Area per se hypothesizes a disproportionate reduction in species richness as island area decreases, steepening the slope of ISARs within archipelagoes or fragmented terrestrial landscapes relative to species–area relationships within landscapes comprised of continuous habitat (Diamond 1972, 1975, Wilson and Willis 1975, Connor and McCoy 1979, Saccheri  et  al. 1998, Gonzalez 2000, Haila 2002, Haddad et al. 2015, MacDonald et al. 2018a, b). From a mechanistic perspective, area per se essentially invokes the theory of island biogeography, where species richness arises as a dynamic equilibrium between rates of extinction and colonization, which in turn depend on island area and isolation (MacArthur and Wilson 1963, Wilson and MacArthur 1967). More isolated populations occupying small islands are predicted to be more prone to stochastic extinction and small, isolated islands are less likely to be re-colonized from external source populations than larger, well-connected islands (Levins 1969, Hanski and Gyllenberg 1993, Orrock and Watling 2010). Thus, the theory of island biogeography addresses efects of both island area and isolation, predicting that immigration rates and rescue efects decrease as islands become increasingly isolated from neighboring habitat (i.e. the mainland or other islands), negatively afecting species’ probabilities of occurrence and therefore species richness (MacArthur and Wilson 1963, Wilson and MacArthur 1967, Brown and Kodric-Brown 1977, Hanski 1994, 1998, 1999).

As an alternative to dynamic balances between demographic rates predicted by the theory of island biogeography, Williams (1964) proposed that ISARs are driven by variation in habitat diversity among islands. The habitat diversity hypothesis predicts that island/fragment area correlates with species richness only insofar as area correlates with the intermediate variable of habitat diversity; larger sample areas generally contain more habitats, which support more species (Williams 1964, Nilsson  et  al. 1988, Rosenzweig 1995, Gotelli and Graves 1996). It follows that the presence or proportion of suitable habitat within islands/fragments should afect abundances and occurrences of individual species (Buckley 1982, Haila and Järvinen 1983). However, few studies have investigated how habitat associations of single species relate to emergent patterns of species richness in this context (but see Haila et al. 1983). Still, multiple studies addressing species richness support the habitat diversity hypothesis (Nilsson et al. 1988, Kadmon and Allouche 2007, Hortal  et  al. 2009). It has also been inferred that mechanisms predicted by the passive sampling hypothesis, theory of island biogeography and habitat diversity hypothesis may simultaneously contribute to ISARs (Connor and McCoy 1979, Kadmon and Allouche 2007, MacDonald et al. 2018b Chase et al. 2019).

## Complications in extending ISARs to conservation

Due to its success on true islands, conservation biologists were quick to recognize the potential for the theory of island biogeography to be applied to fragmented habitat on terrestrial landscapes, initially in the design of nature reserves (Diamond 1972, 1975, Wilson and Willis 1975). However, the extension of ISAR-based inferences from true islands to habitat fragments is complicated by diferences in their extents of insularity and interactions between habitat and non-habitat (i.e. matrix) areas (Itescu 2019). Whereas edges of true islands clearly delimit suitable habitat from a homogeneous matrix of unsuitable habitat (open water), species occurring on habitat fragments may utilize resources of heterogeneous terrestrial matrices and these matrices may differentially constrain or facilitate colonization rates of species (i.e. ‘matrix efects’; Dunning  et  al. 1992, Ricketts 2001). Thus, understanding habitat fragments as analogous to true islands may be problematic. More specifically, fragmentation efects observed within true-island systems may difer from those typical of fragmented terrestrial landscapes (Laurance 2008, Mendenhall et al. 2014, Farneda et al. 2020).

## SLOSS-based inferences

Irrespective of the mechanisms underlying ISARs, observations that species richness generally decreases as island/fragment area decreases and isolation increases have contributed to long-standing inferences that habitat fragmentation poses a major threat to species diversity (Diamond 1972, 1975, Noss 1991, Haila 2002, Hanski 2015, Fletcher et al. 2018). However, many of these inferences are founded on observations or experimental designs that have not suficiently decoupled the efects of area per se and isolation from the sample-area efect (i.e. decoupled habitat fragmentation from habitat loss; sensu Fahrig 2003, 2013, 2017, Hadley and Betts 2016). In the majority of studies successfully decoupling habitat fragmentation from habitat loss, single large habitat fragments are generally found to contain an equivalent or lesser number of species than sets of several small habitat fragments summing to an equivalent total area (Quinn and Harrison 1988, Fahrig 2003, 2013, 2017, 2020, Yaacobi et al. 2007, MacDonald et al. 2018a, b, Deane et al. 2020). Such comparisons contribute to the ongoing single-large-or-severalsmall (‘SLOSS’) debate, addressing how finite conservation eforts should prioritize the area and configuration of fragmented habitat and nature reserves (Diamond 1975, Abele and Connor 1979, Ovaskainen 2002, Tjørve 2010). In light of SLOSS-based observations that species richness is often equal or greater within sets of several small habitat fragments, Fahrig (2013) advanced the habitat amount hypothesis, predicting that the number of species persisting on fragmented landscapes is only a function of total habitat amount at the landscape scale irrespective of its spatial subdivision and configuration. The principal mechanism underlying the habitat amount hypothesis is the sample-area efect, as originally articulated by the passive sampling hypothesis (Connor and McCoy 1979). However, the habitat amount hypothesis extends implications of the sample-area efect to predict that there should also be no detectable efect of fragment isolation on species’ abundances, species’ occurrences or species richness after the sample-area efect has been accounted for (Fahrig 2013).

## The importance of understanding how species-level patterns affect ISARs

While the sample-area efect surely contributes to patterns of species richness within a variety of true-island systems and fragmented terrestrial landscapes, richness-based analyses may obscure important efects of both area per se and isolation on individual species (Ewers and Didham 2006, Öckinger et al. 2009, Franzén et al.2012, Hanski 2015, MacDonald  et  al. 2018a). Indeed, area per se and isolation efects have been inferred to vary widely among species, even within single landscapes and taxa (Henle et al. 2004, Ewers and Didham 2006, Nowicki  et  al. 2007, Öckinger  et  al. 2009, Hanski 2015, Hillebrand et al. 2018, MacDonald et al. 2018a). Functional traits, including body size (Gehring and Swihart 2003, Henle et al. 2004, Larsen et al. 2008, Prugh et al. 2008, Barbaro and Van Halder 2009, Warzecha et al. 2016), mobility/dispersal ability (Roland and Taylor 1997, Lens et al. 2002, Ewers and Didham 2006, Öckinger et al. 2009, MacDonald et al. 2018a, 2019), degree of ecological specialization (Tscharntke and Brandl 2004), rarity/conservation status (Ewers and Didham 2006) and trophic position (Tscharntke et al. 2002, Thies et al. 2005, Ewers and Didham 2006) are hypothesized to relate species’ sensitivity to area per se and isolation. Still, relatively few empirical studies have investigated how functional traits relate to interspecific variation in responses to area per se and isolation or how this interspecific variation scales to emergent patterns of species richness, such as those reflected in ISARs (Melbourne  et  al. 2004, but see Barbaro and Van Halder 2009, Öckinger et al. 2009).

## Distinguishing mechanisms underlying ISARs

Due to the sample-area efect, observations that species abundances, species’ probabilities of occurrence or species richness positively correlate with island/fragment area cannot be directly interpreted as evidence of efects of area per se (Connor and McCoy 1979, Fahrig 2003, 2013, 2017, Fletcher  et  al. 2018). Three established methods may be used to control for the sample-area efect: 1) comparing sets of islands/fragments that sum to equal areas but difer in degree of fragmentation, including the nested-set designs of Yaacobi  et  al. (2007) and MacDonald  et  al. (2018a, b) and comparisons of species accumulation curves proposed by Quinn and Harrison (1988); 2) extrapolating a speciesarea regression to the total area of all islands/fragments used to build the regression and comparing predicted and observed species richness (γ-diversity) (Rosenzweig 2004, Yaacobi et al. 2007, Santos et al. 2010, Gavish et al. 2012, MacDonald  et  al. 2018a, b); and 3) comparing equal-area sampling plots across islands/fragments (Westman 1983, Stevens 1986, Quinn  et  al. 1987, Kelly  et  al. 1989, Fahrig 2013, Watling et al. 2020). However, for methods 1 and 2 (SLOSS-based comparisons), substantial species turnover among several small islands/fragments can increase their aggregate richness relative to single large islands/fragments, such that important efects of area per se on individual spe cies are obscured (sensu Simberlof 1976, MacDonald et al. 2018b, Deane et al. 2020). Assuming species are uniformly distributed within islands/fragments, inferences drawn from method 3 may be robust for sessile taxa (e.g. vascular plants; Westman 1983, Quinn  et  al. 1987, Kelly  et  al. 1989), but remain tenuous for vagile species that move frequently within islands/fragments, as individual sampling plots may accumulate all vagile species within single islands/fragments if sampling efort is high. Additionally, if rare species are particularly sensitive to area per se or isolation, these efects are likely to go undetected when sampling at small spatial grain sizes dictated by method 3; rare species and important habitat types within islands/fragments may be missed entirely in comparisons of small sampling plots (Karger  et  al. 2014). Finally, each of the three established methods only contrast the sample-area efect with those of area per se (methods 1 and 2) or area per se and isolation (method 3); evaluating efects of isolation and habitat diversity requires additional analyses. A fourth method, recently proposed by Chase et al. (2019), employs parameters derived from individual-based rarefaction curves across various spatial scales within islands/fragments to distinguish between the sample-area efect and efects of area per se and habitat diversity. While this framework can efectively resolve mechanisms underlying ISARs, it cannot simultaneously evaluate efects of isolation, assess whether area per se and isolation diferentially afect species in relation to their functional traits, or be applied to existing datasets lacking abundance data for subplots stratified within each island fragment across diagnosable habitat heterogeneity.

In this paper, we present a novel application of random placement and linear mixed efects models that can simultaneously evaluate: 1) how area per se, isolation, and habitat diversity afect species’ abundances, species’ occurrences and species richness across true islands or terrestrial habitat fragments; and 2) whether interspecific variation in these responses relates to variation in species’ functional traits. This modelling framework is applicable to any dataset for which abundance data were collected for sets of true islands or habitat fragments with sampling efort standardized per unit area. We assess the utility of the framework using a butterfly assemblage persisting on a naturally fragmented landscape of true islands; Lake of the Woods, Canada. Methodological developments and basic inferences presented here are equally applicable to both true islands and terrestrial habitat fragments, so long as the edges of habitat fragments can be consistently delimited.

## Material and methods

## Overview of the modelling framework

Starting with the assumption that all individuals of each species are randomly distributed across true islands or habitat fragments in abundances proportional to their areas, random placement models can be used to calculate expected species abundances, expected probabilities of species’ occurrences and expected species richness for each island or fragment (Arrhenius 1921, Coleman 1981, Gotelli and Graves 1996, He and Legendre 2002). Resulting random placement values are equivalent to values of species’ abundances, species’ probabilities of occurrence and species richness predicted by the sample-area efect. Predictions of the passive sampling/ habitat amount hypotheses, theory of island biogeography and habitat diversity hypothesis may be then simultaneously evaluated by modelling relationships between random placement residuals (observed values minus random placement values) and the area, isolation and habitat diversity of individual islands/fragments. Variables measuring species’ functional traits may be introduced to abundance and occurrence models via interaction terms with island/fragment area and isolation to evaluate whether efects of area per se and isolation interspecifically vary contingent on the measured traits.

## Random placement models

We present random placement models in ascending order of mathematical complexity, from species’ abundances, to species’ occurrences, to species richness. Within random placement models, $a _ { _ j }$ is the area of the jth island/fragment, $A _ { \scriptscriptstyle T }$ is the total area of all islands/fragments, $n _ { i }$ is the abundance of species i summed across all islands/fragments and S is the total number of species observed. Islands or fragments that were not surveyed are not included in random placement models. According to the sample-area efect, the expected abundance of species i on island/fragment j is simply proportional to $j ^ { \flat } s$ area (model 1) and the occurrence probability follows the random placement model (model 2). The random placement model for expected richness on any island/fragment is simply the sum of the expected probabilities of occurrence over all species (model 3). This random placement richness model was first proposed a century ago by Arrhenius (1921) and later reinvented by Coleman (1981) with the inclusion of the variance.

$$
E \left(n _ {i j}\right) = n _ {i} \left(\frac {a _ {j}}{A _ {T}}\right)\tag{1}
$$

$$
E \left(O _ {i j}\right) = 1 - \left(1 - \frac {a _ {j}}{A _ {T}}\right) ^ {n _ {i}}\tag{2}
$$

$$
E \left(S _ {j}\right) = \sum_ {i = 1} ^ {S} \left\{1 - \left(1 - \frac {a _ {j}}{A _ {T}}\right) ^ {n _ {i}} \right\}\tag{3}
$$

## Modelling of random placement residuals

Subtracting random placement abundance and occurrence probability values from observed abundance and occurrence values for each species on each island/fragment produces abundance and occurrence residuals. The direction and magnitude of these residuals measure how abundances and occurrences of each species deviate from predictions of the sample-area efect. In the modelling framework described below, all species’ abundance residuals and all species’ occurrence residuals are concatenated across species for use in single linear mixed efects models; one model addressing all species abundances and one model addressing all species’ occurrences. Abundance residuals require standardization (subtracting the mean and dividing by standard deviation) before concatenation across species, as the range of possible values is greater for common species than rare species. While this is not the case for occurrence residuals (values bound between −1 and 1), standardization is still recommended to generate values that are commensurate among species. Richness residuals are similarly calculated for each island/fragment by subtracting random placement richness values from observed richness values. Standardization is recommended to facilitate comparisons of efect sizes among abundance, occurrence and richness analyses.

## Species’ abundances and occurrences

Linear mixed efects models are used to relate abundance and occurrence residuals to island/fragment variables while controlling for species identity as a random efect. If area per se afects species’ abundances or occurrences beyond variation associated with the sample-area efect, residuals will be positively related to area, indicating a disproportionate concentration of species’ abundances or occurrences on larger islands/ fragments. If isolation negatively afects species’ abundances or occurrences, residuals will be negatively related to measures of isolation specific to individual islands/fragments, indicating a disproportionate concentration of species’ abundances or occurrences on less isolated islands/fragments. Each of these results align with predictions of the theory of island biogeography. Alternatively, the absence of significant relationships between residuals and area or isolation would indicate that the sample-area efect suficiently accounts for variation in species’ abundances or occurrences across islands/ fragments of varying area or isolation. The combination these results would confer support for the passive sampling/habitat amount hypotheses. The proportion of species-specific suitable habitat and presence of species-specific resources within each island/fragment may also be included in linear mixed efects models. Positive relationships between abundance or occurrence residuals and these variables would indicate that availability of specific habitats or resources within islands/ fragments are important considerations that afect species abundances or occurrences, as predicted by the habitat diversity hypothesis.

If data on species’ functional traits are available, functional trait variables may be introduced to linear mixed efects models via interaction terms with island/fragment area and isolation. Here, a significant interaction between a functional trait variable and island/fragment area or isolation would indicate that area per se or isolation diferentially afects species’ abundances or occurrences contingent on the measured trait. Total abundance and number of occurrences (prevalence) for each species are also of interest, as rarity is cited as a predictor of species’ sensitivity to fragmentation (Ewers and Didham 2006). A significant positive interaction between total abundance or prevalence and island/fragment area would indicate that rare species are disproportionately concentrated or likely to occur on larger islands/fragments. Similarly, a significant negative interaction between total abundance or prevalence and island/fragment isolation would indicate that rare species are disproportionately concentrated or likely to occur on less isolated islands/fragments.

## Species richness

A similar modelling process may be applied to species richness using linear models. Significant relationships between richness residuals and island/fragment area or isolation would indicate that area per se or isolation significantly afects richness after controlling for the sample-area efect. Each of these results align with predictions of the theory of island biogeography. Conversely, the absence of significant relationships between residuals and area and isolation would indicate that the sample-area efect suficiently accounts for variation in species richness across islands/fragments of varying area or isolation. This combination of results would suggest that only habitat amount at the archipelago- or landscape-scale afects richness, as predicted by the passive sampling/habitat amount hypotheses. Predictions of the habitat diversity hypothesis may also be simultaneously evaluated by including measures of habitat diversity in linear models. Significant relationships between richness residuals and habitat diversity would indicate that, despite correlations between habitat diversity and island/fragment area, variation in habitat diversity among islands/fragments afects species richness beyond variation associated with both the sample-area efect and efects of area per se.

## Application of the modelling framework

## Study area

We assessed the utility of this modelling framework using a butterfly assemblage persisting on a \~1250 km<sup>2</sup> lake-island complex located in Sabaskong Bay, Lake of the Woods, Canada (Fig. 1). Diferential isostatic rebound and outlet restriction resulted in the flooding of the study area and isolation of land-bridge islands approximately 3000–4000 YA (Yang and Teller 2005). Given this substantial time-sinceisolation, we infer that species assemblages have relaxed to equilibria (> 1000 generations; based on categories suggested by Fahrig 2020). Butterflies represent a suitable taxon for this investigation, as most species complete their life cycles within relatively small patches of habitat, their detectability is generally high and their diversity correlates with that of many other terrestrial taxa (Thomas 2005, Nowicki  et  al. 2008, MacDonald  et  al. 2017, 2018a). Butterflies do not utilize open water at any life stage, meaning the matrix separating islands in this system is entirely unsuitable. This efectively controls for matrix efects (Dunning  et  al. 1992, Ricketts

![](images/cd619626b1a82d6660f5dab0cf34451abe977e754fe19e7b40c07ef861fcb69a.jpg)  
Figure 1. Map of the study area, located in Sabaskong Bay, Lake of the Woods, Canada. Butterfly abundance, occurrence and species rich ness data were collected for 30 study islands, varying in area from 0.09 to 8.4 ha, using repeated full island surveys.

2001), but also limits the generalizability of our inferred fragmentation efects to terrestrial landscapes (Laurance 2008, Mendenhall et al. 2014, Farneda et al. 2020).

Thirty islands, ranging in area from 0.1 to 8.0 ha, were randomly selected from lists of candidate islands compiled according to the methods of MacDonald  et  al. (2018a). Islands were only considered as candidates if they were isolated from other landmasses by at least 100 m, beyond the inferred visual ranges of butterflies (Rutowski 2003, MacDonald et al. 2019). The relative isolation of each study island was quantified at multiple scales as the proportion of water within 250-, 500-, 1000-, 1500-, 2000-, 2500-, 3000-, 3500-, 4000-, 4500- and 5000-m bufers. Bufers were generated from island edges, meaning isolation measures are independent from and uncorrelated with island area. We opted for these proportion-based measures because they have been shown to predict immigration rates, rescue efects and related ecological processes more accurately than distance-based measures (Moilanen and Nieminen 2002, Tischendorf et al. 2003, Prugh 2009). Habitat diversity was estimated on each island as the relative proportion of 14 habitat types, defined using structural properties of vegetation and geological features (Supporting information for habitat type descriptions).

## Survey protocol

Butterfly abundance data were collected for each of the 30 islands using repeated full-island surveys. Each island was visited four times at intervals between 10 and 14 days during the peak flight season (1 June 2015 to 20 Aug 2015). Sampling efort was standardized to 40 min per ha per survey across all islands, eliminating the need for sampling efort and diversity corrections (e.g. rarefaction or extrapolation, Chao  et  al. 2014, Fahrig 2020). Care was taken to visit all habitat types during each survey and handheld GPS units were used to ensure uniform coverage of islands. Recording observer tracks and capturing individuals whenever possible (kept as voucher specimens or released at the end of each survey) minimized the possibility of double counts, where individuals are recorded multiple times in single surveys. To ensure optimal and standardized butterfly activity, surveys were restricted to the hours of 10:45 to 15:45 and were not conducted in wind speeds over 15 km $\mathrm { h } ^ { - 1 }$ or in temperatures below $1 3 ^ { \circ } \mathrm { C } .$ If temperatures were below $1 7 ^ { \circ } \mathrm { C } ,$ , surveys were only conducted in sunny conditions (cloud cover < 40%). Surveys were conducted in temperatures above $1 7 ^ { \circ } \mathrm { C } ,$ , regardless of cloud cover (MacDonald et al. 2017).

The diversities of vascular plants and butterflies have been observed to positively correlate with one another in a variety of systems, primarily due to larval host plant associations (Erhardt 1985, Sparks and Parish 1995, Simonson et al. 2001, Croxton et al. 2005, Nowicki et al. 2007, Kitahara et al. 2008, MacDonald et al. 2018a, Riva et al. 2020). Accordingly, vascular plant species richness was quantified on each island using repeated full-island surveys (four surveys total), standardized to 40 min per ha per survey (MacDonald  et  al. 2018b for further details on vascular plant surveys). A total survey time of two hr and 40 min per ha is consistent with recent recommendations for boreal plant communities (Zhang et al. 2014). Only presence–absence data were collected for vascular plants, precluding use of our modelling framework (but see Simberlof and Gotelli 1984 for random colonization models applied to presence–absence data).

## Data analysis

We calculated values of species’ abundances, species’ probabilities of occurrence and species richness predicted by random placement for each of the 30 study islands using random placement models (1, 2 and 3, respectively). Abundance, occurrence and richness residuals were estimated as observed values minus random placement values. We next used linear mixed efects models to simultaneously: 1) quantify relationships between either abundance residuals or occurrence residuals and island variables, including area, isolation, proportion of suitable habitat and presence/absence of preferred larval host plants; 2) evaluate whether area per se or isolation diferentially afects species’ abundances or occurrences contingent on their functional traits. Separate models were built for each isolation buffer size (250, 500, 1000, 1500, 2000. 2500, 3000, 3500, 4000, 4500 and 5000 m). Each of these models had the same number of parameters (k) and only difered in the bufer size used to measure island isolation. We therefore directly compared models with log likelihood (Lamb et al. 2018), where the model with the maximum log likelihood identified the optimal bufer size. Relationships between log likelihood and bufer sizes were quantified using Pearson’s product moment correlation coeficients. The proportion of suitable habitat for each species was estimated as the total area of suitable habitat types divided by the total area of the island. Habitat types were classified as suitable for a species if we observed at least one individual within them during the repeated full-island surveys. The presence/absence of preferred larval host plants (compiled from Hall  et  al. 2014, Acorn and Sheldon 2017) for each species on each island was included as a binary variable. We included species’ wingspan (mm; as reported in Burke et al. 2011) in models as a functional trait variable, serving as a measure of both body size and mobility/dispersal ability (Roland and Taylor 1997, Lens et al. 2002, Ewers and Didham 2006, Öckinger et al. 2009, MacDonald  et  al. 2018a, 2019). Other functional traits predicted to relate to species’ sensitivity to fragmentation (e.g. degree of ecological specialization, trophic position) were either not measured or did not vary substantially among butterfly species and so were not investigated. As an inverse measure of species’ rarity, we included species’ total abundance and prevalence in abundance and occurrence models, respectively. To evaluate whether area per se or isolation diferentially afected species’ abundances or occurrences contingent on their functional traits, we included the following interaction terms: wingspan:area, wingspan:isolation, rarity:area and rarity:isolation. All non-binary predictor variables were standardized (subtracting the mean and dividing by standard deviation), permitting comparisons of efect sizes. The structure for both abundance and occurrence linear mixed efects models was as follows, where ‘habitat’ is the proportion of suitable habitat for each species on each island and ‘plants’ is the presence/absence of each species’ preferred larval host plants:

$$
\begin{array}{r l} f (\text { residuals }) & \sim \beta_ {1} (\text { area }) + \beta_ {2} (\text { isolation }) + \beta_ {3} (\text { habitat }) + \beta_ {4} (\text { plants }) \\ & + \beta_ {5} (\text { wingspan }) + \beta_ {6} (\text { rarity }) + \beta_ {7} (\text { wingspan:area }) \\ & + \beta_ {8} (\text { wingspan:isolation }) + \beta_ {9} (\text { rarity:area }) \\ & + \beta_ {1 0} (\text { rarity:isolation }) + (1 | \text { species   id }) + e \end{array}
$$

Linear models were fitted for species richness following the same basic protocol as abundance and occurrence linear mixed efects models. Predictor variables included island area, isolation, habitat diversity and vascular plant species richness. The most supported isolation bufer size was again assessed using log likelihood comparisons among models difering only in bufer size. Habitat diversity was estimated as the number of habitat types on each island. All predictor variables were standardized. The structure for richness linear models was as follows, where ‘habitat’ is the total number of habitat types recorded on each island and ‘plants’ is vascular plant species richness:

$$
f (\text { residuals }) \sim \beta_ {1} (\text { area }) + \beta_ {2} (\text { isolation }) + \beta_ {3} (\text { habitat }) + \beta_ {4} (\text { plants }) + e
$$

## Results

A total of 869 butterflies belonging to 34 species were observed during repeated full island surveys. Butterfly abundance data are reported in Supporting information. One species, Feniseca tarquinius, uniquely feeds on woolly aphids in its larval stage (Hall et al 2014, Acorn and Sheldon 2017). Only one individual of this species was observed across all surveys. We excluded it from abundance and occurrence models, which included presence/absence of preferred larval host plants as a predictor variable. All individuals belonging to all species were included in richness models.

## Species’ abundances

Comparing log likelihood among linear mixed efects models difering only in isolation bufer size resolved that the proportion of water within 250 m (smallest bufer size) was most supported (Table 1, Fig. 2a). Model support significantly declined across increasing bufer sizes $( \mathrm { r } { = } - 0 . 7 0 \dot { 9 } ;$ $_ { \mathrm { p = 0 } . 0 1 5 ) }$ , indicating that the amount of habitat immediately surrounding individual islands better predicted species abundances than the amount of habitat at broader spatial scales. Within the most supported model, abundance residuals were significantly related to both island area and isolation (Table 2, Fig. 3). Area per se had a significant positive efect on species’ abundances, while isolation had a significant negative efect, in accordance with mechanisms predicted by the theory of island biogeography. The absolute magnitude of the efects of area per se and isolation, inferred from standardized regression coeficients, were approximately equivalent. Together, these results indicate that the sample-area efect cannot account for variation in species’ abundances across islands of varying area and that habitat configuration, and not just total area, has important efects on species’ abundances in this system. Other island variables, including the proportion of suitable habitat and presence/absence of preferred larval host plants, were not related to species’ abundances.

Coeficients of the wingspan:area and rarity:area interaction terms were significantly negative, indicating that efects of area per se systematically varied across species in respect to these functional traits. Causality behind the wingspan:area interaction is clear; efects of area per se on abundance were greater for smaller, less mobile butterfly species. However, for rarity:area, it cannot be resolved whether efects of area per se on abundance were greater for rare species, or whether these species were rare within the dataset because they experience greater efects of area per se. Comparisons of the relative abundances of species between the mainland (continuous habitat) and islands (fragmented habitat) would help resolve the causal direction of this relationship; however, this was beyond the scope of this study. Relationships between abundance residuals and functional trait variables were not significant. This result is expected, as abundance residuals were standardized for each species individually before they were concatenated for use in linear mixed efects models.

Table 1. Log likelihood values for linear mixed effects (abundance and occurrence) and linear (species richness) models. For species abundances, species’ occurrences and species richness, separate models were built for a range of isolation buffers, measuring the proportion of open water within 250, 500, 1000, 1500, 2000, 2500, 3000, 3500, 4000, 4500 and 5000 m of island shores. Model sup port significantly declined across increasing isolation buffer sizes in all instances. The most supported buffer size for each model set is highlighted in bold.

<table><tr><td>Isolation buffer (m)</td><td>Abundance</td><td>Occurrence</td><td>Species richness</td></tr><tr><td>250</td><td>-1329.83</td><td>-1340.37</td><td>-36.79</td></tr><tr><td>500</td><td>-1330.22</td><td>-1340.71</td><td>-37.45</td></tr><tr><td>1000</td><td>-1330.99</td><td>-1342.89</td><td>-37.67</td></tr><tr><td>1500</td><td>-1332.11</td><td>-1341.77</td><td>-36.61</td></tr><tr><td>2000</td><td>-1332.00</td><td>-1340.52</td><td>-37.02</td></tr><tr><td>2500</td><td>-1332.05</td><td>-1340.72</td><td>-37.79</td></tr><tr><td>3000</td><td>-1332.17</td><td>-1341.71</td><td>-38.12</td></tr><tr><td>3500</td><td>-1332.13</td><td>-1342.61</td><td>-38.36</td></tr><tr><td>4000</td><td>-1332.01</td><td>-1343.28</td><td>-38.45</td></tr><tr><td>4500</td><td>-1331.86</td><td>-1343.60</td><td>-38.48</td></tr><tr><td>5000</td><td>-1331.87</td><td>-1343.53</td><td>-38.44</td></tr></table>

## Species’ occurrences

As with abundance linear mixed efects models, the most supported isolation bufer size for predicting occurrence residuals was 250 m (Table 1, Fig. 2a). Model support significantly declined across increasing bufer sizes $( \mathrm { r } { = } - 0 . 7 4 \check { 6 } ;$ $_ { \mathrm { p = 0 . 0 0 8 ) } }$ . Within the most supported model, occurrence residuals showed no relationship to island area, suggesting that the sample-area efect suficiently accounts for variation in species’ occurrences across islands that vary in area (Table 2, Fig. 3). This result confers support for the passive sampling/habitat amount hypotheses. However, occurrence residuals were significantly negatively related to island isolation, suggesting that island configuration has important efects on species’ occurrences, as predicted by the theory of island biogeography. Other island variables, including the proportion of suitable habitat and presence/absence of preferred larval host plants, were not significantly related to occurrence residuals.

Efects of functional trait variables (wingspan and rarity) and their interaction with island variables were not significant at $\alpha = 0 . 0 5$ . However, the coeficient of the wingspan:area interaction term was marginally significant at $\mathrm { p } { = } 0 . 0 6 9$ , suggesting that smaller, less mobile species were less likely than larger, more mobile species to occur on small islands. In other words, butterfly species richness on small islands may be disproportionately comprised of large butterfly species with high mobility.

## Species richness

The most supported isolation bufer size for predicting species richness residuals was 1500 m, which was only marginally more supported than the smallest (250 m) bufer size (Table 1, Fig. 2a). Notwithstanding, model support still significantly declined across increasing bufer sizes $\bar { ( } \mathrm { r } = - 0 . 8 3 \bar { 3 } ;$ $\mathrm { p } { = } 0 . 0 0 1 )$ . Within the most supported model, residuals were not significantly related to island area, isolation, habitat richness or vascular plant species richness (Table 2, Fig. 3). It should be noted, however, that the directionality of the island isolation coeficient aligned with predictions of the theory of island biogeography, and was significant at $\alpha { = } 0 . 1 0$ . Failure to resolve a significant efect at $\alpha = 0 . 0 5$ suggests that richness-based analyses confer less analytical power than abundance- and occurrence-based analyses. If we adopt the most commonly used significance threshold of $\alpha = 0 . 0 5$ , our linear model would suggest that the sample-area efect suficiently accounts for variation in richness observed across our study islands, conferring support for the passive sampling/habitat amount hypotheses and random assembly of species.

![](images/5954d59a220605e9621613d0a1bc5cfe03ff8a84fc8bbb1c61deb0470dc00c03.jpg)

![](images/f354a6d892b33269e4cda2b0e15996ecec40f932d1ef2b5f17b07cdeaef181ec.jpg)  
Figure 2. a) Standardized log likelihood values for linear mixed efects (abundance and occurrence) and linear (species richness) models where responding variables were random placement residuals. Explanatory variables for each model are listed in Table 2 and Figure 3. Separate models were built using diferent island isolation bufer sizes, quantifying using the proportion of open water within 250, 500, 1000, 1500, 2000, 2500, 3000, 3500, 4000, 4500, and 5000 m of island shores. To permit comparisons of relationships between log likelihood values and bufer sizes among abundance, occurrence, and species richness model sets, log likelihood scores were standardized for each model set by subtracting the mean and dividing by standard deviation. Model support significantly declined across increasing isolation bufer sizes in all instances. b) Log-log island species-area relationship (ISAR) for butterflies occurring on 30 study islands. The shaded blue polygon represents 95% confidence intervals for the log log ISAR linear regression (solid blue line), parameterized using observed richness values for all 30 islands. Random placemen richness values were calculated using a random placement model (model 3; see Materials and Methods). The shaded green polygon represents 95% interpolated confidence intervals for random placement values, calculated using Coleman’s (1981) formula for variance.

Table 2. Standardized regression coefficient estimates ('coeff.'). standard errors ('SE') and p-values ('p') from linear models fitting random placement residuals for species’ abundances, species’ occurrences and species richness. Included in all models were island area, measured in m<sup>2</sup> and island isolation, measured as the proportion of water within the most supported buffer size (250 m for abundance and occurrence; 1500 m for species richness). Within abundance and occurrence models, the proportion suitable habitat (‘habitat’) was measured for each species as the area of suitable habitat on each island divided by the area of the island. Presence/absence of each species’ preferred larval host plants (‘plants’) was included as a binary variable. Wingspan was included as a measure of species’ body size and as a proxy of disper sal ability. Each species’ total abundance and prevalence were used as an inverse measure of rarity in abundance and occurrence models, respectively. Species identity was included as a random effect in abundance and occurrence models. Within the species richness model, habitat diversity (‘habitat’) was estimated as the total number of habitat types recorded on each island. Plant diversity (‘plants’) was measured as vascular plant species richness. Significant coefficients (α=0.05) are highlighted in bold.

<table><tr><td rowspan="2">Variable</td><td colspan="3">Abundance</td><td colspan="3">Occurrence</td><td colspan="3">Species richness</td></tr><tr><td>coeff.</td><td>SE</td><td>p</td><td>coeff.</td><td>SE</td><td>p</td><td>coeff.</td><td>SE</td><td>p</td></tr><tr><td>area</td><td>0.087</td><td>0.032</td><td>0.007</td><td>0.005</td><td>0.033</td><td>0.884</td><td>0.294</td><td>0.292</td><td>0.323</td></tr><tr><td>isolation</td><td>-0.069</td><td>0.032</td><td>0.028</td><td>-0.073</td><td>0.032</td><td>0.022</td><td>-0.320</td><td>0.173</td><td>0.076</td></tr><tr><td>habitat</td><td>0.020</td><td>0.032</td><td>0.535</td><td>0.016</td><td>0.033</td><td>0.635</td><td>-0.763</td><td>0.395</td><td>0.075</td></tr><tr><td>plants</td><td>0.018</td><td>0.082</td><td>0.830</td><td>-0.070</td><td>0.083</td><td>0.400</td><td>0.110</td><td>0.484</td><td>0.822</td></tr><tr><td>wingspan</td><td>-0.001</td><td>0.035</td><td>0.973</td><td>-0.015</td><td>0.035</td><td>0.661</td><td></td><td></td><td></td></tr><tr><td>rarity</td><td>-0.004</td><td>0.032</td><td>0.892</td><td>-0.001</td><td>0.033</td><td>0.988</td><td></td><td></td><td></td></tr><tr><td>wingspan:area</td><td>-0.117</td><td>0.031</td><td>&lt; 0.001</td><td>-0.057</td><td>0.031</td><td>0.069</td><td></td><td></td><td></td></tr><tr><td>wingspan:isolation</td><td>0.012</td><td>0.031</td><td>0.708</td><td>0.006</td><td>0.031</td><td>0.838</td><td></td><td></td><td></td></tr><tr><td>rarity:area</td><td>-0.081</td><td>0.031</td><td>0.009</td><td>-0.009</td><td>0.032</td><td>0.783</td><td></td><td></td><td></td></tr><tr><td>rarity:isolation</td><td>0.012</td><td>0.031</td><td>0.688</td><td>0.041</td><td>0.032</td><td>0.196</td><td></td><td></td><td></td></tr></table>

![](images/e43f5e6a942599a6e473c37a8097dbd9f5f444476de7bd967a3b748e73bc286c.jpg)

![](images/36e153d71c6a94e19d0fe2f59a0ea4761a65c4dfaa81b1cc2d795b8a9574b3d6.jpg)

![](images/bea163cdf16e65c059428d4adf84ab90661950f3fb05de3931aca65c2e521e3d.jpg)  
Figure 3. Standardized regression coeficients and 95% confidence intervals from linear models relating random placement residuals to island characteristics and species’ functional traits for (a) species’ abundances, (b) species’ occurrences and (c) species richness. Included in all models were island area, measured in m<sup>2</sup> and island isolation, measured as the proportion of water within the most supported bufer size (250 m for abundance and occurrence; 1500 m for species richness). Within abundance and occurrence models, the proportion suitable habitat (‘suitable habitat’) was measured for each species as the area of suitable habitat on each island divided by the area of the island. Presence/absence of each species' preferred larval host plants was included as a binary variable. Wingspan was included as a measure of species’ body size and as a proxy of dispersal ability. Each species’ total abundance and prevalence were used as an inverse measure of rarity in abundance and occurrence models, respectively. Species identity was included as a random efect in abundance and occurrence models. Within the species richness model, habitat diversity was estimated as the total number of habitat types recorded on each island. Plant diversity was measured as vascular plant species richness. The shading of each variable’s point estimate (coeficient) and confidence interval is proportional to its p-value, with darker shades indicating greater significance. Coeficients with 95% confidence intervals not overlapping zero were inferred to be significant at α = 0.05.

## Discussion

Distinguishing mechanisms that underlie variation in species’ abundances, species’ occurrences and emergent patterns of species richness is not only of great interest within the context of fundamental ecology, but is also of paramount importance to applied ecology and understanding how habitat fragmentation afects species diversity (Diamond 1975, Simberlof and Abele 1976, 1982, Haila 2002, Haddad et al. 2015, Chase et al. 2019). Here, we detail a novel modelling framework to test hypotheses on which conservation directives are contingent (Fahrig 2003, 2013, 2017, Haddad et al. 2015, Hanski 2015, Fletcher  et  al. 2018). Applying this modelling framework to a butterfly assemblage persisting on a naturally fragmented landscape of true islands, we were able to resolve that: 1) island area per se and isolation significantly afect species’ abundances and occurrences contingent on their functional traits; and 2) important efects of area per se and isolation are not always apparent in aggregate diversity measures, such as those reflected in ISARs. Although there are several documented divergences between the biogeographies of true-island systems and fragmented habitat on terrestrial landscapes, findings from our study clearly demonstrate that fragmentation efects should not be inferred from richness-based analyses, but rather evaluated on a species-by-species basis.

## Inferences from the ISAR

Our modelling framework resolved that spatial patterns in butterfly species richness (i.e. the ISAR) did not significantly deviate from random placement in relation to island area, isolation, habitat diversity or vascular plant diversity. These ISAR-based inferences align with those of MacDonald et al.

(2018a), who used a series of SLOSS-based analyses to infer that butterfly species richness in this naturally fragmented landscape approximately conform to predictions of the sample-area efect, with no significant efects of area per se or isolation. Therefore, all analyses addressing efects of area per se and isolation on butterfly species richness in this system support the passive sampling/habitat amount hypotheses and Fahrig’s (2003, 2013, 2017) general conclusion that efects of fragmentation (i.e. area per se and isolation) are generally negligible after controlling for deleterious efects of habitat loss; only habitat amount at the landscape-scale afects species richness via its influence on regional species pools.

While there seems to be considerable support for the passive sampling/habitat amount hypotheses in the literature (Fahrig 2003, 2013, Martin 2018, Watling  et  al. 2020), a recent meta-analysis by Fahrig (2020), including 157 SLOSS comparisons from 58 studies, found that several small islands/ fragments contained more species than single large islands/ fragments in 72% of comparisons, equivalent numbers of species in 22% of comparisons and fewer species in 6% of comparisons. Removing studies with biased sampling efort in relation to island/fragment area shifted these figures to 58, 37 and 5%. Regardless, these results suggest that species richness varies with degree of fragmentation more often than it does not. Thus, the sample-area efect implicated in the passive sampling/habitat amount hypotheses cannot consistently account for SLOSS-based richness patterns. Furthermore, methods employed by Fahrig (2020) – specifically, comparisons of Quinn and Harrison (1988) species accumulation curves – sufer from an important limitation: substantial species turnover among several small islands/fragments can inflate their aggregate richness, such that important deviations from random placement (e.g. efects of area per se) are obscured (sensu Simberlof 1976, MacDonald et al. 2018b, Deane et al. 2020). This relationship may explain why several small islands/fragments are generally found to contain more species than single large fragments in the majority of SLOSSbased studies. While results of Fahrig’s (2020) meta-analysis are of great interest to both fundamental and applied ecology, they cannot necessarily be used to distinguish efects of area per se from the sample-area efect and cannot resolve additional efects of isolation or habitat diversity. Future investigations focusing on species richness would benefit from the inclusion of ISAR-based analyses that assess deviations from random placement on an island-by-island or fragment-byfragment basis, such as those included within the modelling framework presented here.

Additional deviations from random placement may be resolved by visually examining the ISAR and random placement richness values (Fig. 2b). In this study, observed richness values were generally less than random placement richness values (all islands except four). This pattern cannot be attributed to efects of area per se, because the direction and magnitude of richness residuals was relatively consistent across islands of varying area (Fig. 2b), as indicated by the insignificant coefficient of island area within the species richness linear model (Table 2). Rather, this relationship is best explained by spatial species aggregation, wherein conspecific individuals are more likely to co-occur on islands than what is predicted by random placement, reducing the species richness of individual islands (He and Legendre 2002). Therefore, although spatial patterns of species richness did not significantly deviate from random placement in respect to either island area or isolation, they did deviate from random placement in respect to spatial species aggregation. It is therefore clear that failure to resolve significant efects of area per se and isolation on species richness cannot be taken as direct evidence for random assembly of individuals and species, the fundamental prediction of the habitat amount/passive sampling hypotheses (c.f. Fahrig 2003, 2013, 2017, 2020). Rigorous evaluation of random assembly requires comparison of observed richness to expected richness predicted by null models, such as the random placement models presented here.

## Inferences from species’ abundances and occurrences

Inferring whether fragmentation is ‘good’ or ‘bad’ (sensu Fahrig 2017, Fletcher  et  al. 2018) based on emergent patterns of species richness is potentially susceptible to ‘ecological fallacy’ (sensu Robinson 1950), which describes biases that may arise when observed efects on aggregated variables (e.g. species richness) difer from causal relationships at more reductive and informative levels of organization (e.g. species’ abundances and occurrences). Indeed, our abundance and occurrence models resolved important efects of area per se and isolation that were not apparent in either ISARor SLOSS-based analyses (this study and MacDonald et al. 2018a, respectively). This discrepancy among inferences suggests that conflating responses of all species into a single aggregate measure (e.g. species richness) reduces our power to detect important relationships on which conservation directives should be contingent. Two such relationships were resolved when considering the entire species assemblage in abundance and occurrence models: 1) there was a disproportionate concentration of individuals on larger and less-isolated islands relative to what was predicted by the sample-area efect (passive sampling/habitat amount hypotheses); and 2) species were more likely to occur on less-isolated islands than what was predicted by the sample-area efect. It is therefore clear that the sample-area efect described by the passive sampling/habitat amount hypotheses cannot adequately account for spatial patterns in butterfly abundances and occurrences in this naturally fragmented landscape, which are better predicted by mechanisms outlined by the theory of island biogeography. It should be noted that the directionality of area per se and isolation efects were consistent among abundance, occurrence and richness models, but only statistically significant (α = 0.05) in the first two analyses, wherein species responses were not aggregated into a single measure.

Most interestingly, our modelling framework simultaneously resolved that efects of area per se on species abundances and occurrences varied significantly with species-specific functional traits, suggesting that mechanisms outlined by the theory of island biogeography are not neu tral with respect to species identity. Whether species’ sensitivity to fragmentation varies predictably with functiona traits is a long-standing and pertinent question in conser vation biology (Roland and Taylor 1997, Lens et al. 2002, Gehring and Swihart 2003, Henle et al. 2004, Tscharntke and Brandl 2004, Thies  et  al. 2005, Ewers and Didham 2006, Prugh  et  al. 2008, Barbaro and Van Halder 2009, Öckinger et al. 2009, Hanski 2015, Warzecha et al. 2016, MacDonald et al. 2018a, 2019). In this study, efects of area per se were significantly greater for butterfly species with smaller wingspans. For Canadian butterflies, wingspan is one of the strongest correlates of estimated mobility and dispersal ability (Burke  et  al. 2011); thus, we can infer that effects of area per se are greatest for small species of limited mobility (c.f. Larsen  et  al. 2008). This relationship may be explained by larger and more mobile butterfly species having the ability to move among multiple smal islands to meet their resource requirements. These ‘tran sient’ species may thereby exhibit patterns of abundance and occurrence that approximate random placement (Wilson and MacArthur 1967: Chapter 2; Rosenzweig 2004, MacDonald et al. 2018a). Such patterns would be predicted by ideal free distribution theory (sensu Dreisig 1995) if two conditions are met: 1) islands of varying area contain equivalent densities of resources; and 2) the mobil ity/dispersal ability of individuals is sufficient to render costs of inter-island movements negligible. By contrast, island edges may be perceived as impassible barriers for smaller and less mobile species, with energy expenditures and mortality risks associated with movement through the open-water matrix being too high for regular inter-island movements. Island edges may therefore delimit popula tions of smaller and less mobile species, which are gener ally restricted to larger islands that contain all resources required for mate location, reproduction, resting, roosting, predator escape and feeding (i.e. the functiona resource-based habitat concept; Dennis et al. 2003). Thi hypothesis is supported by analyses of MacDonald  et  al. (2018a), who resolved that the probability of butterfly species occurring on islands without their preferred lar val host plants was positively related to their wingspan and estimated mobility. Considered together, these results suggest that functional traits may be used to predict species’ sensitivity to fragmentation and that species identity should not be ignored when investigating mechanisms that underlie ISARs or in conservation planning. It is, how ever, important to recognize that the open-water matrix of this study landscape may be more unsuitable and less permeable than those of many fragmented terrestrial landscapes (Dunning  et  al. 1992, Ricketts 2001, Laurance 2008, Mendenhall et al. 2014, Itescu 2019, Farneda et al. 2020). It is therefore unclear the degree to which these relationships between species’ functional traits and effects of area per se and isolation are generalizable to conservation efforts addressing terrestrial landscapes fragmented through anthropogenic activities.

The abundance and occurrence modelling framework proposed here may also be implemented on a species-by-species basis by regressing island/fragment variables (area, isolation, presence/amount of suitable habitat or specific resources, etc.) on abundance and occurrence residuals for each species in separate linear models. This method of analysis precludes the simultaneous integration of functional trait analyses within models, but has the added advantage of identifying single species that are particularly sensitive to fragmentation (area per se and isolation) or other island/fragment variables of interest. This simple decomposition of our modelling framework may be used to resolve whether particular species require independent consideration within conservation frameworks.

## Isolation versus habitat amount

The relative isolation of islands addressed in this study was quantified across multiple scales as the proportion of water within 11 bufer sizes, ranging from 250 to 5000 m. These measures are equal to 1 minus the amount of landmass (habitat) within each bufer distance. Fahrig (2013) suggests that the habitat amount hypothesis would be supported by species’ abundances, species’ occurrences or species richness of equal-area sampling plots (stratified across fragments of varying area and isolation) correlating with the amount of habitat on the surrounding landscape more strongly than with the area of the individual fragments on which the sampling plots are located. This is because landscapes containing less habitat should contain fewer individuals (belonging to fewer species) due to the sample-area efect, meaning fragments within such landscapes will have smaller species pools from which their own diversities are randomly sampled. However, the ‘appropriate distance’ for quantifying the amount of habitat surrounding equal-area sampling plots is undefined and, most problematically, the area of individual fragments on which sampling plots are located becomes increasingly correlated with habitat amount as this distance is reduced. Thus, it may not be possible to decouple fragment area from habitat amount using Fahrig’s (2013) proposed method; particularly, for taxa that respond to habitat amount and configuration at fine spatial scales, including butterflies (Thomas and Abery 1995, MacDonald et al. 2017, 2018a, 2019, Saura 2020).

Within our modelling framework, variation in species’ abundances, species’ occurrences and species richness associated with full-island surveys and the sample-area efect is nullified in the calculation of random placement residuals. Abundance, occurrence and richness residuals can therefore be correlated with island/fragment area and the amount of surrounding habitat in a fashion similar to Fahrig’s (2013) proposed method of using equal-area sampling plots. However, because the area of individual islands/fragments is not included in our measures of the amount of surrounding habitat (our bufers are generated from island/fragment edges), the problem of island/fragment area becoming increasingly correlated with habitat amount at fine spatial scales is avoided. After controlling for efects of area per se, abundance and occurrence residuals were significantly related to island isolation. Model support significantly declined across increasing isolation bufer sizes for species’ abundances, species’ occurrences and species richness, suggesting that that the amount of habitat immediately surrounding islands, rather than the amount of habitat at broader landscape scales, has the greatest efect on butterflies in this system. Importantly, island area and isolation were efectively decoupled, as indicated by the absence of correlation between island area and isolation (e.g. 250 m bufer; r = 0.082; p = 0.668). Thus, in contrast with mechanisms outlined by the habitat amount hypothesis, isolation efects observed in this study are better attributed to the fact that individual butterflies moving through the open-water matrix are less likely to encounter more isolated islands (Andrén 1994), reducing species’ abundances and probabilities of occurrence, as predicted by the theory of island biogeography. This inference is further corroborated by analyses of MacDonald  et  al. (2018a), which showed that butterfly species turnover among islands of equal areas – a proxy for variation in species pools if islands indeed randomly sample species – was unrelated to Euclidean distance between islands. This result suggests a uniform species pool throughout the study landscape. Again, the degree to which these findings apply to fragmented terrestrial landscapes, wherein the suitability and permeability of matrices may vary, is unclear. For studies addressing fragmented terrestrial landscapes, isolation measures should not only account for the proportion of suitable habitat within various bufer distances, but also include measures of matrix suitability and permeability, if they are available (MacDonald et al. 2020).

## Habitat fragmentation and the narcissus effect

It is important to recognize a bias within this case study, and potentially other study designs addressing spatial patterns of species’ abundances, species’ occurrences or species richness across true islands or terrestrial habitat fragments. Here, we investigated efects of area per se and isolation on a naturally fragmented landscape of true islands with substantial time-since-isolation (3000–4000 YA; Yang and Teller 2005). Therefore, species that are particularly sensitive to fragmentation are unlikely to occur on islands at all. Although our modelling framework resolved significant efects of area per se and isolation on butterfly species’ abundances and occurrences, efects of area per se and isolation on the regional species pool were likely underestimated, as the species assemblage of adjacent continuous habitat was not quantified. This bias may be described as the ‘narcissus efect’, which addresses situations wherein a null model or study design unintentionally accounts for or excludes efects that are of interest (sensu Colwell and Winkler 1984). It is possible that this bias contributed to results of Fahrig’s (2017) review, where 68% (158/232) of studies addressing single species reported positive fragmentation efects; species that are particularly sensitive to fragmentation may be completely missed in many studies. We therefore suggest caution in interpreting results from study designs that are susceptible to the narcissus efect and encourage future studies to compare the identities and functional traits of species between islands/fragments and adjacent continuous habitat to assess potential biases resulting from the historic exclusion of fragmentation-sensitive species. This may be accomplished using our proposed modelling framework by surveying continuous habitat equal in area to the sum of all surveyed islands/fragments. Abundance data from continuous habitat may then be used in place of total abundances across all islands/fragments (n ) to calculate abundance, occurrence and richness random placement values for each island/fragment using the random placement models described above. Subtracting these random placement values from observed abundance, occurrence and richness values for each island/fragment will result in abundance, occurrence and richness residuals that may be used in our linear mixed efects models (abundance and occurrence) and linear models (richness) to resolve whether there are additional efects of area per se and isolation on the regional species pool.

## Conservation implications

Considerable uncertainty exists in the literature regarding the influence of area per se and isolation (i.e. habitat fragmentation) on populations and communities of wildlife (Fahrig 2003, 2013, 2017, Haddad  et  al. 2015, Hanski 2015, Fletcher et al. 2018). There is an immediate need to resolve this debate, as habitat loss and fragmentation are widespread and increasing (Hanski et al. 2013, Ibisch et al. 2016, Chase et al. 2020, Deane et al. 2020). We demonstrate here that ISAR- and SLOSS-based inferences, founded on emergent patterns of species richness, have the potential to obscure important interspecific variation in responses to area per se and isolation. To infer support for the passive sampling, habitat amount and related hypotheses from emergent patterns of species richness that spuriously conform to predictions of the sample-area efect is to simplistically cut rather than carefully untie the Gordian knot of ecological complexity. We suggest that, in addition to emergent patterns of species richness, information at more reductive and informative levels of organization (e.g. species’ abundances and occurrences) should be included in studies aiming to measure and understand efects of habitat fragmentation.

Acknowledgements – Vascular plant surveys and identifications were completed by Iraleigh Anderson and we thank him for valuable discussions and insights. We also thank Federico Riva for his review of a previous version of this manuscript.

Funding – This work was supported by a Natural Sciences and Engineering Research Council (NSERC) Discovery Grant to SEN (RGPIN-2014-04842) and NSERC Alexander Graham Bell Canada Graduate Scholarships – MSc and PhD (CGS – D and CGS – D) to ZGM

Conflicts of interest – The authors have no conflicts of interest to declare.

Permits – Permission to survey butterflies and vascular plants, including collection of voucher specimens, was granted by Ontario Parks.

## Author contributions

Zachary MacDonald: Conceptualization (lead); Formal analysis (lead); Funding acquisition (supporting); Methodology (lead); Project administration (equal); Resources (supporting); Software (lead); Validation (equal); Visualization (lead); Writing – original draft (lead); Writing – review and editing (lead). David Dean: Conceptualization (supporting); Formal analysis (supporting); Methodology (supporting); Resources (supporting); Software (supporting); Validation (equal); Visualization (supporting); Writing – original draft (supporting); Writing – review and editing (supporting). Fangliang He: Conceptualization (supporting); Formal analysis (supporting); Methodology (supporting); Software (supporting); Supervision (supporting); Validation (equal); Visualization (supporting); Writing – original draft (supporting); Writing – review and editing (supporting). Clayton Lamb: Conceptualization (supporting); Formal analysis (supporting); Methodology (supporting); Software (supporting); Validation (equal); Visualization (supporting); Writing – original draft (supporting); Writing – review and editing (supporting). Felix Sperling: Conceptualization (supporting); Formal analysis (supporting); Methodology (supporting); Supervision (supporting); Validation (equal); Visualization (supporting); Writing – original draft (supporting); Writing – review and editing (supporting). John Acorn: Conceptualization (supporting); Formal analysis (supporting); Methodology (supporting); Project administration (equal); Resources (supporting); Supervision (equal); Validation (equal); Visualization (supporting); Writing – original draft (supporting); Writing – review and editing (supporting). Scott E. Nielsen: Conceptualization (supporting); Formal analysis (supporting); Funding acquisition (lead); Methodology (supporting); Project administration (equal); Resources (supporting); Software (supporting); Supervision (equal); Validation (equal); Visualization (supporting); Writing – original draft (supporting); Writing – review and editing (supporting).

## Transparent Peer Review

The peer review history for this article is available at <https:// publons.com/publon/10.1111/ecog.05563>.

## Data availability statement

All butterfly, plant, and island data are provided in Supporting Information.

## References

Abele, L. G. and Connor, E. F. 1979. Application of island biogeography theory to refuge design: making the right decision for the wrong reasons. – In: Proceedings of the first conference on scientific research in the national parks, Vol. 1. US Department of the Interior, Washington, D.C., USA, pp. 89–94.

Acorn, J. and Sheldon, I. 2017. Butterflies of Ontario and eastern Canada. – Partners Publishing.

Andrén, H. 1994. Efects of habitat fragmentation on birds and mammals in landscapes with diferent proportions of suitable habitat: a review. – Oikos 71: 355–366.

Arrhenius, O. 1921. Species and area. – J. Ecol. 9: 95–99.

Barbaro, L. and Van Halder, I. 2009. Linking bird, carabid beetle and butterfly life-history traits to habitat fragmentation in mosaic landscapes. – Ecography 32: 321–333.

Brown, J. H. and Kodric-Brown, A. 1977. Turnover rates in insular biogeography: efect of immigration on extinction. – Ecology 58: 445–449.

Buckley, R. 1982. The habitat-unit model of island biogeography. – J. Biogeogr. 9: 339–344.

Burke, R. J. et al. 2011. A mobility index for Canadian butterfly species based on naturalists’ knowledge. – Biodivers. Conserv. 20: 2273–2295.

Chao, A. et al. 2014. Rarefaction and extrapolation with Hill numbers: a framework for sampling and estimation in species diversity studies. – Ecol. Monogr. 84: 45–67.

Chase, J. M. et al. 2019. A framework for disentangling ecological mechanisms underlying the island species–area. – Front. Biogeogr. 11: e40844.

Chase, J. M. et al. 2020. Ecosystem decay exacerbates biodiversity loss with habitat loss. – Nature 584: 238–243.

Coleman, B. D. 1981. On random placement and species–area relations. – Math. Biosci. 54: 191–215.

Colwell, R. K. and Winkler, D. W. 1984. A null model for null models in biogeography. – In: Strong Jr, D. R. et al. (eds), Ecological communities: conceptual issues and the evidence. Princeton Univ. Press, pp. 344–359.

Connor, E. F. and McCoy, E. D. 1979. The statistics and biology of the species–area relationship. – Am. Nat. 113: 791–833.

Croxton, P.  et  al. 2005. Linear hotspots? The floral and butterfly diversity of green lanes. – Biol. Conserv. 121: 579–584.

Deane, D. C.  et  al. 2020. Quantifying factors for understanding why several small patches host more species than a single large patch. – Biol. Conserv. 249: 108711.

Dennis, R. L. et al. 2003. Towards a functional resource-based concept for habitat: a butterfly biology viewpoint. – Oikos 102: 417–426.

Diamond, J. M. 1972. Biogeographic kinetics: estimation of relaxation times for avifaunas of southwest pacific islands. – Proc. Natl Acad. Sci. USA 69: 3199–3203.

Diamond, J. M. 1975. The island dilemma: lessons of modern biogeographic studies for the design of natural reserves. – Biol. Conserv. 7: 129–146.

Dreisig, H. 1995. Ideal free distributions of nectar foraging bumblebees. – Oikos 72: 161–172.

Dunning, J. B. et al. 1992. Ecological processes that afect populations in complex landscapes. – Oikos 65: 169–175.

Erhardt, A. 1985. Diurnal Lepidoptera: sensitive indicators of cultivated and abandoned grassland. – J. Appl. Ecol. 22: 849–861.

Ewers, R. M. and Didham, R. K. 2006. Confounding factors in the detection of species responses to habitat fragmentation. – Biol. Rev. 81: 117–142.

Fahrig, L. 2003. Efects of habitat fragmentation on biodiversity. – Annu. Rev. Ecol. Evol. Syst. 34: 487–515.

Fahrig, L. 2013. Rethinking patch size and isolation efects: the habitat amount hypothesis. – J. Biogeogr. 40: 1649–1663.

Fahrig, L. 2017. Ecological responses to habitat fragmentation per se. – Annu. Rev. Ecol. Evol. Syst. 48: 1–23.

Fahrig, L. 2020. Why do several small patches hold more species than few large patches? – Global Ecol. Biogeogr. 29: 615–628.

Farneda, F. Z. et al. 2020. Predicting biodiversity loss in island and countryside ecosystems through the lens of taxonomic and functional biogeography. – Ecography 43: 97–106.

Fletcher Jr, R. J. et al. 2018. Is habitat fragmentation good for biodiversity? – Biol. Conserv. 226: 9–15.

Franzén, M.  et  al. 2012. Species–area relationships are controlled by species traits. – PLoS One 7: e37359.

Gavish, Y. et al. 2012. Decoupling fragmentation from habitat loss for spiders in patchy agricultural landscapes. – Conserv. Biol. 26: 150–159.

Gehring, T. M. and Swihart, R. K. 2003. Body size, niche breadth and ecologically scaled responses to habitat fragmentation: mammalian predators in an agricultural landscape. – Biol. Conserv. 109: 283–295.

Gonzalez, A. 2000. Community relaxation in fragmented landscapes: the relation between species richness, area and age. – Ecol. Lett. 3: 441–448.

Gotelli, N. J. G. and Graves, G. R. 1996. Null models in ecology. – Smithsonian Inst. Press.

Haddad, N. M. et al. 2015. Habitat fragmentation and its lasting impact on Earth’s ecosystems. – Sci. Adv. 1: e1500052.

Hadley, A. S. and Betts, M. G. 2016 Refocusing habitat fragmentation research using lessons from the last decade. – Curr. Landscape Ecol. Rep. 1: 55–66.

Haila, Y. 2002. A conceptual genealogy of fragmentation research: from island biogeography to landscape ecology. – Ecol. Appl. 12: 321–334.

Haila, Y. and Järvinen, O. 1983. Land bird communities on a Finnish island: species impoverishment and abundance patterns. – Oikos 41: 255–273.

Haila, Y. et al. 1983. Colonization of islands by land birds: prevalence functions in a Finnish archipelago. – J. Biogeogr. 10: 499–531.

Hall, P. W.  et  al. 2014. The ROM field guide to butterflies of Ontario. – Royal Ontario Museum Press.

Hanski, I. 1994. A practical model of metapopulation dynamics. – J. Anim. Ecol. 63: 151–162.

Hanski, I. 1998. Metapopulation dynamics. – Nature 396: 41–49.

Hanski, I. 1999. Metapopulation ecology. – Oxford Univ. Press.

Hanski, I. 2015. Habitat fragmentation and species richness. – J. Biogeogr. 42: 989–993.

Hanski, I. and Gyllenberg, M. 1993. Two general metapopulation models and the core-satellite species hypothesis. – Am. Nat. 142:17-41.

Hanski, I. et al. 2013. Species–fragmented area relationship. – Proc. Natl Acad. Sci. USA 110: 12715–12720.

He, F. and Legendre, P. 2002. Species diversity patterns derived from species–area models. – Ecology 83: 1185–1198.

Henle, K. et al. 2004. Predictors of species sensitivity to fragmentation. – Biodivers. Conserv. 13: 207–251.

Hillebrand, H. et al. 2018. Biodiversity change is uncoupled from species richness trends: consequences for conservation and monitoring. – J. Appl. Ecol. 55: 169–184.

Hortal, J. et al. 2009. Island species richness increases with habitat diversity. – Am. Nat. 174: E205–E217.

Ibisch, P. L.  et  al. 2016. A global map of roadless areas and their conservation status. – Science 354: 1423–1427.

Itescu, Y. 2019. Are island-like systems biologically similar to islands? A review of the evidence. – Ecography 42: 1298–1314.

Kadmon, R. and Allouche, O. 2007. Integrating the efects of area, isolation and habitat heterogeneity on species diversity: a uni-

fication of island biogeography and niche theory. – Am. Nat. 170: 443–454.

Karger, D. N.  et  al. 2014. Island biogeography from regional to local scales: evidence for a spatially scaled echo pattern of fern diversity in the southeast Asian archipelago. – J. Biogeogr. 41: 250–260.

Kelly, B. J. et al. 1989. Causes of the species-area relation: a study of islands in Lake Manapouri, New Zealand. – J. Ecol. 77: 1021–1028.

Kitahara, M.  et  al. 2008. Relationship of butterfly diversity with nectar plant species richness in and around the Aokigahara primary woodland of Mount Fuji, central Japan. – Biodivers. Conserv. 17: 2713–2734.

Lamb, C. T. et al. 2018. Efects of habitat quality and access management on the density of a recovering grizzly bear population. – J. Appl. Ecol. 55: 1406–1417.

Larsen, T. H. et al. 2008. Understanding trait-dependent community disassembly: dung beetles, density functions and forest fragmentation. – Conserv. Biol. 22: 1288–1298.

Laurance, W. F. 2008. Theory meets reality: how habitat fragmentation research has transcended island biogeographic theory. – Biol. Conserv. 141: 1731–1744.

Lens, L. et al. 2002. Avian persistence in fragmented rainforest. – Science 298: 1236–1238.

Levins, R. 1969. Some demographic and genetic consequences of environmental heterogeneity for biological control. – Bull. Entomol. Soc. Am. 15: 237–240.

Lomolino, M. V. 2000. Ecology’s most general, yet protean pattern: the species–area relationship. – J. Biogeogr. 27: 17–26.

MacArthur, R. H. and Wilson, E. O. 1963. An equilibrium theory of insular zoogeography. – Evolution 17: 373–387.

MacDonald, Z. G. et al. 2017. Negative relationships between species richness and evenness render common diversity indices inadequate for assessing long-term trends in butterfly diversity. – Biodivers. Conserv. 26: 617–629.

MacDonald, Z. G. et al. 2018a. Decoupling habitat fragmentation from habitat loss: butterfly species mobility obscures fragmentation efects in a naturally fragmented landscape of lake islands. – Oecologia 186: 11–27.

MacDonald, Z. G. et al. 2018b. The theory of island biogeography, the sample-area efect and the habitat diversity hypothesis: complementarity in a naturally fragmented landscape of lake islands. – J. Biogeogr. 45: 2730–2743.

MacDonald, Z. G. et al. 2019. Perceptual range, targeting ability and visual habitat detection by greater fritillary butterflies Speyeria cybele (Lepidoptera: Nymphalidae) and Speyeria atlantis. – J. Insect Sci. 19: 1–10.

MacDonald, Z. G. et al. 2020. Gene flow and climate-associated genetic variation in a vagile habitat specialist. – Mol. Ecol. 29: 3889–3906.

Martin, C. A. 2018. An early synthesis of the habitat amount hypothesis. – Landscape Ecol. 33: 1831–1835.

Melbourne, B. A. et al. 2004. Species survival in fragmented landscapes: where to from here? – Biodivers. Conserv. 13: 275–284.

Mendenhall, C. D. et al. 2014. Predicting biodiversity change and averting collapse in agricultural landscapes. – Nature 509: 213–217.

Moilanen, A. and Nieminen, M. 2002. Simple connectivity measures in spatial ecology. – Ecology 83: 1131–1145.

Nilsson, S. G. et al. 1988. Habitat diversity or area per se? Species richness of woody plants, carabid beetles and land snails on islands. – J. Anim. Ecol. 57: 685–704.

Noss, R. F. 1991. Landscape connectivity: diferent functions at diferent scales. – In: Soulé, M. E. et al. (eds), Landscape linkages and biodiversity. Island Press.

Nowicki, P. et al. 2007. From metapopulation theory to conservation recommendations: lessons from spatial occurrence and abundance patterns of Maculinea butterflies. – Biol. Conserv. 140: 119–129.

Nowicki, P.  et  al. 2008. Butterfly monitoring methods: the ideal and the real world. – Israel J. Ecol. Evol. 54: 69–88.

Öckinger, E. et al. 2009. Mobility-dependent efects on species richness in fragmented landscapes. – Basic Appl. Ecol. 10: 573–578.

Orrock, J. L. and Watling, J. I. 2010. Local community size mediates ecological drift and competition in metacommunities. – Proc. R. Soc. B 277: 2185–2191.

Ovaskainen, O. 2002. Long-term persistence of species and the SLOSS problem. – J. Theor. Biol. 218: 419–433.

Prugh, L. R. 2009. An evaluation of patch connectivity measures. – Ecol. Appl. 19: 1300–1310.

Prugh, L. R.  et  al. 2008. Efect of habitat area and isolation on fragmented animal populations. – Proc. Natl Acad. Sci. USA 105: 20770–20775.

Quinn, J. F. and Harrison, S. P. 1988. Efects of habitat fragmentation and isolation on species richness: evidence from biogeographic patterns. – Oecologia 75: 132–140.

Quinn, S. L.  et  al. 1987. The island biogeography of Lake Manapouri, New Zealand. – J. Biogeogr. 14: 569–581.

Ricketts, T. H. 2001. The matrix matters: efective isolation in fragmented landscapes. – Am. Nat. 158: 87–99.

Riva, F.  et  al. 2020. Composite efects of cutlines and wildfire result in fire refuges for plants and butterflies in boreal treed peatlands. – Ecosystems 23: 1–13.

Robinson, W. S. 1950. Ecological correlations and the behavior of individuals. – Am. Sociol. Rev. 15: 351–357.

Roland, J. and Taylor, P. D. 1997. Insect parasitoid species respond to forest structure at diferent spatial scales. – Nature 386: 710.

Rosenzweig, M. L. 1995. Species diversity in space and time. – Cambridge Univ. Press.

Rosenzweig, M. L. 2004. Applying species–area relationships to the conservation of species diversity. – In: Lomolino, M. V. and Heaney, M. V. (eds), Frontiers in biogeography: new directions in the geography of nature. Sinauer Associates, pp. 325–344.

Rutowski, R. L. 2003. Visual ecology of adult butterflies. – In: Boggs, C. L. et al. (eds), Butterflies: ecology and evolution taking flight. Univ. of Chicago Press, pp. 9–25.

Saccheri, I.  et  al. 1998. Inbreeding and extinction in a butterfly metapopulation. – Nature 392: 491–494.

Santos, A. M.  et  al. 2010. Are species–area relationships from entire archipelagos congruent with those of their constituent islands? – Global Ecol. Biogeogr. 19: 527–540.

Saura, S. 2020. The habitat amount hypothesis implies negative efects of habitat fragmentation on species richness. – J. Biogeogr. 48: 11-22.

Scheiner, S. M. 2003. Six types of species–area curves. – Global Ecol. Biogeogr. 12: 441–447.

Shafer, C. L. 1990. Nature reserves: island theory and conservation practice. – Smithsonian Inst. Press.

Simberlof, D. 1976. Species turnover and equilibrium island biogeography. – Science 194: 572–578.

Simberlof, D. and Abele, L. G. 1976. Island biogeography theory and conservation practice. – Science 191: 285–286.

Simberlof, D. and Abele, L. G. 1982. Refuge design and island biogeographic theory: efects of fragmentation. – Am. Nat. 120: 41–50.

Simberlof, D. and Gotelli, N. 1984. Efects of insularisation on plant species richness in the prairie-forest ecotone. – Biol. Conserv. 29: 27–46.

Simonson, S. E. et al. 2001. Rapid assessment of butterfly diversity in a montane landscape. – Biodivers. Conserv. 10: 1369–1386.

Sparks, T. and Parish, T. 1995. Factors afecting the abundance of butterflies in field boundaries in Swavesey fens, Cambridgeshire, UK. – Biol. Conserv. 73: 221–227.

Stevens, G. C. 1986. Dissection of the species–area relationship among wood-boring insects and their host plants. – Am. Nat. 128: 35–46.

Thies, C. et al. 2005. The landscape context of cereal aphid–parasitoid interactions. – Proc. R. Soc. B 272: 203–210.

Thomas, C. D. and Abery, J. C. G. 1995. Estimating rates of butterfly decline from distribution maps: the efect of scale. – Biol. Conserv. 73: 59–65.

Thomas, J. A. 2005. Monitoring change in the abundance and distribution of insects using butterflies and other indicator groups. – Phil. Trans. R. Soc. B 360: 339–357.

Tischendorf, L.  et  al. 2003. Evaluation of patch isolation metrics in mosaic landscapes for specialist vs. generalist dispersers. – Landscape Ecol. 18: 41–50.

Tjørve, E. 2010. How to resolve the SLOSS debate: lessons from species-diversity models. – J. Theor. Biol. 264: 604–612.

Triantis, K. A. et al. 2012. The island species–area relationship: biology and statistics. – J. Biogeogr. 39: 215–231.

Tscharntke, T. and Brandl, R. 2004. Plant–insect interactions in fragmented landscapes. – Annu. Rev. Entomol. 49: 405–430.

Tscharntke, T. et al. 2002. Characteristics of insect populations on habitat fragments: a mini review. – Ecol. Res. 17: 229–239.

Warzecha, D.  et  al. 2016. Intraspecific body size increases with habitat fragmentation in wild bee pollinators. – Landscape Ecol. 31: 1449–1455.

Watling, J. I. et al. 2020. Support for the habitat amount hypothesis from a global synthesis of species density studies. – Ecol. Lett. 23: 674–681.

Westman, W. E. 1983. Island biogeography: studies on the xeric shrublands of the inner Channel Islands, California. – J. Biogeogr. 10: 97–118.

Whittaker, R. J. and Fernández-Palacios, J. M. 2007. Island biogeography: ecology, evolution and conservation, 2nd edn. – Oxford Univ. Press.

Williams, C. B. 1964. Patterns in the balance of nature. – Academic Press.

Wilson, E. O. and MacArthur, R. H. 1967. The theory of island biogeography. – Princeton Univ. Press.

Wilson, E. O. and Willis, E. O. 1975. Applied biogeography. – In: Cody, M. L. et al. (eds), Ecology and evolution of communities. Harvard Univ. Press, pp. 522–534.

Yaacobi, G. et al. 2007. Habitat fragmentation may not matter to species diversity. – Proc. R. Soc. B 274: 2409–2412.

Yang, Z. and Teller, J. T. 2005. Modeling the history of Lake of the Woods since 11 000 cal yr BP using GIS. – J. Paleolimnol. 33: 483–497.

Zhang, J. et al. 2014. Sampling plant diversity and rarity at landscape scales: importance of sampling time in species detectability. – PLoS One 9: e95334.