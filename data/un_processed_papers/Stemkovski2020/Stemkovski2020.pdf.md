L E T T E R

# Bee phenology is predicted by climatic variation and functional traits

Michael Stemkovski,<sup>1,2</sup>\* iD William D. Pearse,<sup>1,3</sup> iD Sean R. Griffin,<sup>2,4</sup> iD Gabriella L. Pardee,2,4 iD Jason Gibbs,<sup>5</sup> iD Terry Griswold,<sup>6</sup> John L. Neff,7 Ryan Oram,<sup>8</sup> Molly G. Rightmyer,<sup>9</sup> Cory S. Sheffield,<sup>8</sup> Karen Wright,<sup>10</sup> Brian D. Inouye,<sup>2,11</sup> David W. Inouye<sup>2,12</sup> iD and Rebecca E. Irwin<sup>2,13</sup>\*

## Abstract

Climate change is shifting the environmental cues that determine the phenology of interacting species. Plant–pollinator systems may be susceptible to temporal mismatch if bees and flowering plants differ in their phenological responses to warming temperatures. While the cues that trigge flowering are well-understood, little is known about what determines bee phenology. Using generalised additive models, we analyzed time-series data representing 67 bee species collected over 9 years in the Colorado Rocky Mountains to perform the first community-wide quantification of the drivers of bee phenology. Bee emergence was sensitive to climatic variation, advancing with earlier snowmelt timing, whereas later phenophases were best explained by functional traits including overwintering stage and nest location. Comparison of these findings to a long-term flower study showed that bee phenology is less sensitive than flower phenology to climatic variation, indicating potential for reduced synchrony of flowers and pollinators under climate change.

## Keywords

Climate change, emergence, environmental cues, GAM (generalised additive models), Hymenoptera, mismatch, peak, phenophases, senescence.

Ecology Letters (2020) 23: 1589–1598

## INTRODUCTION

Ecological relationships break down when the synchrony of interacting species is disrupted. Climate change is altering the phenology (timing of life-history events) of species, with spring events generally happening earlier (Bell et al., 2015; Cohen et al., 2018) and fall events later (Gallinat et al., 2015). Crucially, the rate of phenological shift varies among co-occurring species and guilds (Thackeray et al., 2016; Konig¨ et al., 2018). This is of particular concern for species within cross-guild associations, such as plants and their pollinators, because the two groups may have different sensitivities to environmental cues (Forrest and Thomson, 2011; Rafferty et al., 2015). Positively interacting species that experience a phenological mismatch due to different directions or rates of response to climate change are likely to suffer reduced fecundity or increased mortality (Visser and Gienapp, 2019). Mismatches due to climate change have been observed in consumer-resource systems (Kharouba et al., 2018) and mutualistic interactions (Petanidou et al., 2014). In the short term, mutualist species that experience a phenological mismatch are expected to suffer fitness losses, followed by adaptation to reestablish synchrony (Visser and Gienapp, 2019). If climate change outpaces the rate of adaptation, however, mutualists may experience irreparable de-coupling. Thus, it is critically important to understand the drivers of phenological shifts and compare their magnitudes for interacting species.

In plant–pollinator systems, phenological mismatch due to earlier spring events has been reported for early season flowers and their pollinators (Kudo et al., 2004; Kudo and Ida, 2013). As spring events such as snowmelt timing are projected to occur earlier under climate change (IPCC, 2014), these mismatches are expected to become more common and pronounced. Phenological mismatch in a pollination system could have negative fitness consequences for plants through pollen limitation (Rafferty and Ives, 2012; Kudo and Ida, 2013), and pollinators through a lack of floral resources (CaraDonna et al., 2018; Schenk et al., 2018). At the community level, mismatches can lead to a collapse of the mutualism (Warren and Bradford, 2014), and may reduce crop yield in agricultural systems if pollinator species richness is low (Bartomeus et al., 2013). While phenological responses to climate change have been well documented for plants (Parmesan and Yohe, 2003; CaraDonna et al., 2014; Konig¨ et al., 2018), less is known about the responses of pollinators, especially insect pollinators such as bees (Bartomeus et al., 2011). Even if bee and flowering phenologies are both responsive to temperature (Hegland et al., 2009; Forrest and Thomson, 2011; Renner and Zohner, 2018), they may not be equally sensitive to variation in temperature, potentially leading to a future mismatch under climate change (Ellwood et al., 2012; Ovaskainen et al., 2013; Petanidou et al., 2014; Olliff-Yang and Mesler, 2018). The few studies that have examined the phenological response of bees to environmental cues have been limited by practical constraints mostly to small subsets of the total bee community (e.g. Kehrberger and Holzschuh, 2019; Slominski and Burkle, 2019). To understand the full effects of climate change on plant communities, it is imperative to determine the community-level drivers of bee phenology given the role of bees as the primary pollinators in most ecosystems (Klein et al., 2007).

From the perspective of pollination, the most important bee activity is the flight period in which adults transfer pollen. The flight period can be described by three points in time (hereafter phenophases): emergence from nests (the beginning of adult foraging, rather than the time of eclosion), timing of the peak abundance of foragers, and senescence (the end of foraging). These phenophases may be driven by different environmental cues, but may also be linked by developmental time (Donnelly et al., 2011; Keenan and Richardson, 2015; Ettinger et al., 2018). Differences in temperature (Forrest and Thomson, 2011), soil moisture (Danforth, 1999; Olliff-Yang and Mesler, 2018), and snowmelt timing along elevation gradients in montane regions (Pyke et al., 2011) may shift bee emergence phenology. Snowmelt timing may be particularly influential in areas where the growing season is limited by many months of persistent snowpack. Given these sensitivities, bee phenology has advanced, on average, due to climate change (Bartomeus et al., 2011). Certain functional traits (those that influence fitness) may shape bee phenology (Diamond et al., 2011; Forrest, 2016), including variable thermal tolerance due to body mass (Stone and Wilmer, 1989), nest location (Bartomeus et al., 2011), and the life stage in which bees overwinter (Frund¨ et al., 2013). Species that nest above ground are expected to be more responsive to climatic variation, as air temperature is more variable than soil temperature (Parton and Logan, 1981), and the stage in which bees overwinter may interact with climate to determine when they can emerge from nests because prepupae-overwintering species must undergo additional development before emergence (Forrest, 2016). While these drivers of phenology have been described in isolation, understanding their relative importance and potential interactions is impossible without a comprehensive study that examines them simultaneously at the community level.

Here, we present findings on the drivers of bee phenology using 9 years of time-series data from a study of solitary bees along an elevation gradient. To make phenology estimates from a sparse time-series data set and to avoid the biases of first-observation dates (Miller-Rushing et al., 2008; Linden,´ 2018; Inouye et al., 2019), we introduce an approach based on generalised additive models that calculate the first 5%, middle, and last 5% of a distribution (van Strein et al., 2008), corresponding to the three phenophases of foraging bee populations. We used these estimates to determine the drivers of bee phenology at the community level, including climate, topography, and bee traits, by comparing phenological variation among years. Specifically, we investigated the predictions that earlier phenophases are more strongly affected by climate variation compared to late phenophases (Forrest, 2016), and that snowmelt timing is the primary driver of bee phenology in the subalpine ecosystem of this study, as it is for flower phenology (Inouye, 2008). We also predicted that species that overwinter as adults emerge earlier than those that overwinter as pre-pupae, because they are less constrained by development time in the early growing season (Frund¨ et al., 2013). Motivated by the idea that species’ phenological plasticity to climatic variation may be mediated by their traits (Diamond et al., 2011), we tested for an interaction between two traits (nest location and overwintering stage) and snowmelt timing. Finally, to explore whether bee phenology will track flower phenology under climate change (Ogilvie et al., 2017), we compared rates of advance in bee phenology in response to earlier snowmelt timing to published rates in flowering phenology at nearby study sites (CaraDonna et al., 2014). By providing the first community-level assessment of the drivers of bee phenology, our findings give insight into the future of plant–pollinator systems under forecasted climate change.

## METHODS

## Study system

We gathered data at 18 sites around the Rocky Mountain Biological Laboratory (RMBL) in the Elk Mountains of western Colorado, USA from 2009 to 2017 (Table S2). Sites were located along an elevation transect (2456–3438 metres above sea-level) in montane and subalpine habitats dominated by a diverse mixture of perennial flowering species (CaraDonna et al., 2014). The area is highly seasonal, with snowpack typically persisting from November until May. The short growing season of only a few summer months results in predominantly univoltine bee life cycles, although some bee species may exhibit parsivoltine life cycles (Forrest et al., 2019). The European honey bee Apis mellifera and other non-native bees were absent during the study period.

## Bee data collection

We sampled bees in habitat types that were representative of dominant vegetation types: wet meadows dominated by Veratrum tenuipetalum, those dominated by Salix spp., rocky dry meadows, and Artemisia spp. steppe. We conducted biweekly bee abundance surveys at each site using pan traps (following LeBuhn et al., 2003). We set out 10 each of white, fluorescent yellow, and fluorescent blue pan traps along two approx. perpendicular 45-m transects at intervals of 3 m, an array that passively attracts bees by mimicking a display of flowers. We deployed pan traps between approx. 0800 and 1700 (the period of maximum bee activity) only on warm, calm, sunny days and removed traps when these conditions changed drastically. Further details of the bee sampling are provided by Gezon et al. (2015). Specimens were identified to the lowest taxonomic resolution possible using a variety of resources (Michener et al., 1994; Michener, 2000; Gibbs, 2010; Scott et al., 2011). We excluded the pollen-foraging genera Anthidium, Ashmeadiella, Atoposmia, Eucera, Diadasia, and Dianthidium and all cleptoparasites (Coelioxys, Epeolus, Holcopasites, Nomada, Stelis, Sphecodes, and Triepeolus) because we were unable to identify them to species or they were very rare (together, individuals from these genera made up 4% of the collection). We were unable to identify most species of the diverse genus Andrena, so only four species in this genus are included in the analysis (this omission represents 3% of the total collection). The list of species included in the analysis is presented in Table S3. The population estimates at each sampling date were calculated as bees captured/hour of sampling, to account for variable sampling effort, including females and males (with the exception of Lasioglossum spp. for which we were only able to identify females). Because pan traps overrepresent small bees such as Halictids and under-represent large bees (Cane et al. 2000), we excluded the large-bodied genus Bombus from analyses (3% of pan-collected specimens).

## Climate, topographic, and trait data

To explain variation in bee phenology, we gathered data on yearly climate variation, topographic data associated with sites, and bee functional traits. We selected snowmelt timing, summer temperature, and summer rainfall as climate variables, elevation and solar incidence as topographic variables, and body mass, nest location, and overwintering stage as functional traits. Full details on the methods for gathering these data and justifications for their inclusion in the analyses are available in Supporting Information 1.

## Phenophase estimation

To bypass the problems of first-occurrence measures of sparse time-series data for many taxa including bees, take into account variable uncertainty, and estimate emergence, peak, and senescence dates from distributions of unknown form, we developed a novel application (validated in Supporting Information 2) of Generalized Additive Models (GAMs; Wood 2017). For each species/site/year combination, we fit a GAM with day-of-year as the explanatory variable and abundance as the response using a cubic spline smoothing basis with a Gaussian distribution family and performed generalised crossvalidation to avoid over-fitting. We set the dimension of the smoothing basis to 4 when there were < 5 observations, and 5 for ≥ 5 observations. For each model fit, we determined the peak timing by calculating the predicted date of the maximum of the model fit and found the first and last occurrence of 5% of the maximum to determine dates of emergence and senescence, respectively. We did not record estimates of emergence or senescence in cases where sampling began too late or ended too early to observe the tails of the distribution below 5% of the maximum. We also did not record estimates of peak abundance when we did not unambiguously observe the “crest” of the abundance curve, though we were able in some cases to estimate emergence or senescence but not peak by identifying the transition from zeroes to positive abundances. Due to this conservative approach, we were able to make emergence estimates for $47 \%$ of the total time-series, 40% for peak, and 53% for senescence. We calculated confidence intervals as twice the standard error at each phenophase. GAMs were implemented using the mgcv R-package (Wood, 2017).

## Modeling drivers of phenology

We created three candidate models by modelling emergence, peak, and senescence timing as functions of climate, topographic, and species trait variables, accounting for pseudoreplication at the site and species level by modelling these as random effects according to the equation

$$
D O Y _ {p h a s e} \sim \theta_ {c l i m} + \theta_ {t o p o} + \theta_ {t r a i t} + e _ {s i t e} + e _ {s p}
$$

where $D O Y _ { p h a s e }$ is the estimated day-of-year (DOY) of each phenophase, $\theta _ { c l i m }$ are the climate variables (snowmelt date, summer temperature, and summer precipitation), $\theta _ { t o p o }$ are the topographic variables (elevation and solar incidence), $\theta _ { t r a i t }$ are species traits (body mass, nest location, and overwintering stage), $e _ { s i t e }$ are sites, and $e _ { s p }$ are species. θ terms represent fixed effects, whereas e terms represent random effects, forming a mixed effects model (Bates et al., 2014). All terms were modelled as additive effects, with no interactions in this top model. Due to heterogeneity in the frequency of sampling, population numbers, and shape of the abundance curves, phenophase estimates have heterogeneous confidence intervals. To propagate this uncertainty through our analysis, we weighted the estimates based on the inverse of their standard errors. To generate directly comparable standardised effect sizes, we scaled and centred explanatory variables (Gelman and Hill, 2006). To make categorical variables comparable to continuous ones, we scaled the continuous variables by 0.5 standard deviations (Gelman, 2008).

Because it is not known which of the proposed variables determine bee phenology at the community level, we employed a model averaging protocol, following Burnham and Anderson (1998), to determine which variables were influential. We fit models with each possible combination of predictor variables and averaged coefficients from models within 4 AIC units of the best one. Because model averaging can bias estimates (Cade, 2015), we compared the averaged coefficients to the coefficients from the top model for each phenophase, finding very tight correlations (Pearson $r > 0 . 9 9 9$ for all three models, Figure S5). Additionally, we tested for multicollinearity, finding sufficiently low variance inflation factors for each predictor (Supporting Information 3).

To investigate whether climate would more strongly affect emergence timing, whereas other variables would be more influential for later phenophases, we calculated marginal and conditional $R ^ { 2 }$ values based on the single best model in the top model set and investigated variance partitioned between climate and trait variables by calculating the proportion of variance explained by models fitted with just climate and trait variables vs. the top model. Due to small sample sizes for some species/predictor variable combinations, we were unable to estimate independent parameter values for every species, and treated species as a random effect in the full model. To provide a visual aid of some species-specific responses to advancing snowmelt and to compare with reported flower phenology shifts, we performed a reduced analysis with the most common species (those that had ≥ 10 species/site/year estimates for two or more phenophases), modelling species responses as $\begin{array} { r } { D O Y _ { p h a s e } \sim \Theta _ { s n o w m e l t } * s p e c i e s + e _ { s i t e } . } \end{array}$ This analysis was conducted for 10 species: three from the Andrenidae, one from the Colletidae, four from the Halictidae, and two from the Megachilidae. We did not control for phylogeny in the analyses because we did not seek to describe the evolution of the present traits. To investigate whether certain traits influence the phenological responsiveness of species to climate, we modelled phenophase estimates as functions of snowmelt (for other climatic variables, see Supporting Information 3) interacting with nest location and overwintering stage, with variable intercepts and slopes, holding all else equal, modelled as $\begin{array} { r } { D O Y _ { p h a s e } \sim \Theta _ { s n o w m e l t } * \Theta _ { t r a i t } + e _ { s p } + e _ { s i t e } } \end{array}$ . We did not include interaction terms in the top model due to the difficulty of estimating many additional parameters with limited data and complications with model averaging (Galipaud et al. 2014). We also tested for the presence of phenological sequences (Keenan and Richardson, 2015; Ettinger et al., 2018) by modelling peak and senescence as linear functions of emergence. Model averaging and $R ^ { 2 }$ calculation (r.squaredGLMM function) were done using the MuMIn package (Barton 2015). We tested for significance of interactions using the lmerTest package (Kuznetsova et al., 2017), and all analyses were run in R version 3.4.4 (R core team 2018).

## RESULTS

The bee monitoring study yielded 1606 time-series of at least four abundance measures for 67 species at 18 sites (Table S2) in 9 years (2009–2017), representing 23,742 collected specimens across 751 sampling periods. The mean maximum species-specific catch rate across all time-series was 1.48 bees/hour, ranging from 0.11 to 35.14 bees/hour per sampling period. We were able to estimate 519 emergence, 438 peak, and 584 senescence dates. The mean emergence day-of-year across all years, sites, and species was 24 June 25 days, mean peak was 10 July 21 days, and mean senescence was 30 July 23 days. Responses to snowmelt, measured as the slope coefficient, fell generally between 0 and 1 days of phenological advance per day of snowmelt advance for most species (Figure 1; Table S4). Five phenophases across four species (Halictus virgatellus emergence and peak, Lasioglossum sedi senescence, Panurginus ineptus emergence, and Pseudopanurgus bakeri senescence) delayed in response to advanced snowmelt, though these effects were not significant. Hoplitis fulgida exhibited the greatest response in emergence to variation in snowmelt timing, whereas Hoplitis robusta had the greatest peak response (Figure 1). As an illustrative example, in the severe drought year of 2012, snowmelt occurred 25 days earlier than in other years, the median emergence phenology advanced by 34 days, peak by 15 days, and senescence by 4 days.

Each candidate predictor variable was represented in the model set (Figure 2). Bees emerged $( 1 1 . 5 2 \pm 2 . 6 8 )$ , peaked $( 1 2 . 8 2 \pm 2 . 4 2 ) $ , and senesced $( 7 . 8 1 \pm 2 . 4 4 ) $ later in years with

![](images/ba322f53dbeecd98f6a41f18dfaa92367cef8767e4a7d5d58bb9b3f3ada7dcab.jpg)

![](images/04d0bad3e0a743a441b3e88e2075ec696c22b10ff1dae6c15dba9bc22a721e77.jpg)  
Response to snowmelt Days of phenology shift Days of snowmelt shift

Figure 1 Common species vary in their responses to snowmelt timing, with most phenophase shifts falling between no response (0, dashed line) and perfect tracking (1, dotted line) of snowmelt. Points to the left of zero represent advances in response to advanced snowmelt timing, and those to the right represent delays. Blue points represent emergence shifts, green points represent peak, and brown points represent senescence. The width of bars represents twice the standard errors around the estimates of response.

later snowmelt date, and snowmelt timing had the largest absolute effect size among the climate variables for each phenophase. Elevation had the largest effect of the topographic variables, with bees at higher elevations emerging $( 1 3 . 5 7 \pm 3 . 2 3 )$ and peaking later $( 7 . 7 6 \pm 3 . 6 5 )$ , but senescing earlier $( - 5 . 9 2 \pm 4 . 0 5 )$ . Of the species traits, nest location had the largest effect on emergence timing; compared to bees that nest above ground, those that nest below ground emerged $( 1 1 . 2 1 \pm 4 . 3 0 )$ later but peaked $( - 4 . 5 7 \pm 3 . 8 4 )$ and senesced earlier $( - 9 . 8 2 \pm 4 . 2 9 ) $ . Overwintering stage had the largest effects on peak and senescence timing; bees that overwinter as adults emerged $( 1 . 9 1 \pm 3 . 5 2 ) $ , peaked $( 1 1 . 2 0 \pm 3 . 2 3 )$ ), and senesced earlier $( 2 0 . 9 1 \pm 3 . 5 9 )$ than those that overwinter as pre-pupae. Each phenophase model was roughly equally able to predict the variation in yearly phenology (Figure 3a). When phenophases were predicted with subsets of the predictor variables, climate variables explained a higher proportion of the total variation for earlier phenophases, whereas species traits explained more variation in later phenophases (Figure 3b).

![](images/30d1f6dc8d318dd7af8fadc91ab1f1e0891ec9f963353c23c5f3745b8479a7bd.jpg)  
Figure 2 Bee phenology is determined by interannual climatic variation, topography, and several species traits. The drivers vary in their relative effect across the phenophases, with the effect of climate variables generally lower for later phenophases. The first panel shows the standardised effect sizes of climate variables, the second topographic variables, and the third species traits on emergence (blue), peak (green), and senescence timing (brown) with standard errors around the estimates shown as brackets. Values greater than 0 represent later phenology, and those less than 0 represent earlier phenology Standardised effect sizes are defined as the slope coefficients derived from scaled and centred explanatory variables.

Full numerical details including significance are provided in Tables S5 and S6.

There was a significant interaction between nest location and snowmelt timing for emergence $( t _ { 4 3 3 } = - 3 . 2 7 8 , P < 0 . 0 1 )$ and peak phenology $( t _ { 3 6 0 } = - 2 . 8 6 1 , P < 0 . 0 1 )$ (Figure 4), and the difference in slope decreased across the phenophases. The interaction between snowmelt timing and overwintering stage was greatest for peak timing and smallest for senescence timing, but these interactions were not statistically significant (emergence: $t _ { 4 4 1 } = - 0 . 8 6 7$ $P > 0 . 0 5$ , peak $t _ { 3 6 8 } = - 1 . 5 6 5$ $P > 0 . 0 5 ,$ senescence $t _ { 4 7 0 } = - 0 . 4 8 1$ P> 0.05). Lastly, we found that emergence significantly predicted peak timing $( F _ { 1 , 2 1 2 } = 2 0 1 . 2 , ~ P < 0 . 0 0 0 1 )$ and senescence timing $( F _ { 1 , 1 0 4 } = 2 9 . 6 3 , P < 0 . 0 0 0 1 )$ but that emergence described less variation in senescence $( R ^ { 2 } = 0 . 2 2 )$ than in peak timing $( R ^ { 2 } = 0 . 4 9 )$ (Figure S6).

## DISCUSSION

We analysed time-series abundance data from a 9-year bee monitoring project to provide the first community-wide assessment of the main predictors of bee emergence, peak, and senescence phenology. While yearly climatic variation, topography, and species functional traits all shaped bee phenology, the emergence and peak phenophases were particularly sensitive to climate. Following patterns in early-season flowering phenology (Inouye, 2008), the timing of early snowmelt, which is a determinant of how much thermal energy is received by bee nests in this montane study area, was particularly influential in advancing the early phenophases. The later, senescence phenophase was determined to a greater extent by functional traits including nest location and the life stage in which bees overwinter (Frund¨ et al., 2013). Nest location also disposed certain species to respond more dynamically to climatic variation. Contrary to predictions (Forrest, 2016), we did not find that adult-overwintering species responded more dynamically to climatic cues despite being less limited by development time prior to emergence. These findings lead us to predict that under increasing temperatures and earlier snowmelt due to climate change, the bee community foraging season will begin earlier and increase in overall duration. However, certain species may be less able to shift their phenology due to variable responses (Figure 1) on the basis of functional traits (Figure 4).

## Bee phenology is determined by climate, topography, and species traits

Snowmelt timing was the main climatic driver of bee phenology, with earlier dates of snowmelt advancing emergence and peak in particular (Figure 2, panel 1). Snowmelt in this system is a major determinant of how much thermal radiation is received by bee nests (for species that nest below ground), so this finding supports previous work suggesting that adult bee emergence has thermal requirements (Kemp and Bosch, 2005; White et al., 2009; Forrest and Thompson, 2011). Thus, we expect bee species in areas without persistent snowpack to similarly adjust their phenology on the basis of thermal energy. Higher summer temperatures and lower summer rainfall resulted in significantly earlier bee emergence but not peak or senescence, resulting in longer community-wide flight periods. Spring events that shape the onset of a phenological process can have cascading effects on later phenophases, leading to phenological sequences, but this cascade can become less pronounced due to variation in developmental time and the influence of other cues (Keenan and Richardson, 2015; Ettinger et al., 2018). We found that emergence timing did predict peak and senescence timing, but that emergence timing described less variation in senescence than in peak timing (Figure S6). Thus, the earlier phenophase of bee foraging influences, but does not determine, the later phenophases. Sites at higher elevations experienced later bee emergence and peak times, but earlier senescence time (though the senescence effect was not significant), resulting in a shortened foraging season (Figure 2, panel 2). These findings support studies that found a phenological shift in bumble bee abundance based on elevation (Pyke et al., 2011) and are in line with findings on flower phenology (Theobald et al., 2017). We note that because we calculated climatic variables as constant across sites within each year, the elevation effect may be driven by local variation in snowmelt timing, which is determined in part by solar incidence and elevation in montane regions.

![](images/3b6a20286690fbf77ffe14a98b5fd202b65f8082d076a81ae100c773ed132ea1.jpg)  
Figure 3 While the models were roughly equal in their ability to predict phenological shifts across all phenophases (panel a), early phenophases were predicted more strongly by climate variables and late phenophases by species traits (panel b). Panel a compares the marginal and conditional $R ^ { 2 }$ values across the top models for each phenophase, and panel b shows the ratio of variance explained by reduced models of only climate and trait variables vs. the variance explained by the top model. The ratio of variance in panel b was calculated as $R _ { \mathrm { \ s u b s e t } } ^ { 2 } / R _ { \mathrm { \ t o t a l } } ^ { 2 }$ where $R _ { \mathrm { \ s u b s e t } } ^ { 2 }$ is the marginal $R ^ { 2 }$ of a model containing just climate or just species trait variables and $R _ { \mathrm { \ t o t a l } } ^ { 2 }$ is that of the top model containing all variables.

Turning to species traits, nest location and overwintering stage, but not body mass, had significant effects on phenophases (Figure 2, panel 3). Ground-nesting bee species emerged later than those that nest above ground, but senesced earlier, indicating that below-ground nesting bee species have shorter average foraging periods. While our finding that adult-overwintering bees have earlier phenology supports the idea that overwintering stage has a large effect on insect phenology broadly (Frund¨ et al., 2013; Forrest, 2016), we were surprised to find that the effect was larger on peak and senescence timing than on emergence timing, which deviates from our initial expectation that overwintering stage would primarily dictate emergence phenology. It may be that there is an evolutionary trade-off between adult mortality rate and the fast development rate that allows certain species to overwinter as adults [see Wright et al. (2010) for an example in plants] or simply that adult-overwintering species have shorter effective foraging lifespans because they spend more time in the adult phase. More long-term studies are needed to understand if this is a general trend, and mechanistic studies would provide insight on the physiological underpinnings of the pattern.

While climatic variation, topography, and species traits determine the date of bee phenophases when viewed separately, bee species’ functional traits mediate their climate sensitivities (i.e., our models support an interaction between functional traits and environment). Above-ground nesting species are more sensitive to snowmelt timing (Figure 4, top panel) and average summer temperature (Supporting Information 3) than those that nest below ground. This finding is slightly counter-intuitive when we consider that ground-nesting bees are buried by snow. The discrepancy may be explained by recognising that snowmelt timing is correlated with other potential phenological cues such as spring temperature. We would expect above-ground nesting bees to be more sensitive to temperature fluctuations, as above-ground temperature varies more than below-ground (Parton and Logan, 1981), and their nests are not insulated by snowpack. This suggests that above-ground nesters may suffer less phenological mismatch with plants under increased variability due to climate change. Surprisingly, we did not find a significant interaction between bee overwintering stage and snowmelt timing (Figure 4, bottom panel). Bees that overwinter as adults require less developmental time before emerging in the spring, so we expected their phenology to be more responsive to snowmelt timing. The finding that adult-overwintering bee species do not take advantage of this shorter developmental time suggests that there may not be a benefit to greater phenological sensitivity, or that other factors limit their sensitivity.

![](images/9d6773d78d54bcce84c65297fd6598c18b5a3f6764ad91f1886d6007cd80f505.jpg)  
Figure 4 Bee species that nest above ground and those that overwinter as adults are more sensitive to variation in snowmelt timing than species that nest below ground and that overwinter as pupae or prepupae. The top three panels show predicted phenophase responses to snowmelt based on nesting location, and the bottom panels show the same based on overwintering stage. The slope of the lines represents the sensitivity of each phenophase to snowmelt timing. P-values are presented for the two significant differences in slope at the α = 0.01 level.

## Different drivers of emergence and senescence phenology

The effect of snowmelt timing on emergence was nearly 50% greater than it was on senescence, and the absolute effects of temperature and rainfall on emergence were nearly an order of magnitude higher than on senescence, indicating that the onset of foraging is timed by external cues, whereas the end is less dynamic. These results match plant phenology findings that showed a reduction in the effect of snowmelt timing on later phenophases (Wipf, 2010). Similarly, in butterflies, early phenophases have been shown to advance more frequently in response to recent climate change (Roy and Sparks, 2000). Summer temperature and rainfall span the entirety of the active bee foraging season and also had larger effects on emergence than on later phenophases (Figure 2, panel 1), indicating that the pattern of a greater climate influence on early phenology is not entirely a byproduct of spring-specific climate variables. Late season phenology may be less sensitive to climatic fall events such as the date of first frost because adult bees – particularly those that nest below ground – are insulated from cold nights in their nests.

Although the predictive power of our models was similar for all phenophases (Figure 3a), climate variables explained more variance for early phenophases, and traits explained more variance for later phenophases (Figure 3b, Supporting Information 3). The effect of snowmelt on senescence is diluted by inherent interspecific variation in foraging flight period. In other words, the effect of the phenological sequence becomes reduced in later phenophases (Figure S6). Some plants exhibit stronger climatic control of spring phenology (Menzel, 2003) but stronger genetic control of autumn phenology (Fracheboud et al., 2009), and our results hint at a similar pattern in bees. The drivers of senescence phenology in insects may be particularly complex due to variation in life-history strategies (Gallinat et al., 2015). For example univoltine insect species are expected to advance their fall senescence, whereas multivoltine species may delay the end of their active period by producing additional generations. Lastly, our finding that spring and fall phenophases are determined by different drivers’ points to the necessity of studying the whole phenological distributions rather than focusing on the onset of an active period.

## Climate change implications

Two of the main effects of climate change in montane regions are an advance of snowmelt timing and increased temperatures (Ogilvie et al., 2017). Bee phenology at the community level is tied to snowmelt but does not precisely track it, and phenophases exhibit different responses to climatic variation. As climate explained more variation and produced larger shifts in early phenophases (Figure 2b), we expect that emergence and peak timing in areas of the world with increasing temperatures and decreasing precipitation will shift at greater rates than senescence, extending the active flight period of adult solitary bees. This could lead to additional generations during the growing season (Altermatt, 2010), or potentially a developmental trap in which species produce a maladaptive second generation that is ill-prepared for autumn conditions (Van Dyck et al. 2015). An extended active bee foraging season may have positive pollination outcomes, allowing pollen-limited plants to reproduce for longer periods of time, though this effect may be tempered by phenological mismatches or declining populations (Hedhly et al., 2009; Vanbergen et al., 2013).

Given observed trends and projections for earlier snowmelt timing, it is relevant to compare variation in bee phenology to that of flowers. A 39-year study of flowering phenology at the RMBL documented that the date of first flowering has advanced by 0.89 0.083 days per day of snowmelt advance (Caradonna et al., 2014). The flowering community in this subalpine region shows two distinct peaks in total floral abundance (Aldridge et al., 2011) which have shifted at different rates (first peak: 0.74 0.056 days per day of snowmelt; second peak: $0 . 5 3 \pm 0 . 0 9 5 \mathrm { { \ d a y s ) } }$ . We found that bee emergence timing shifted by 0.49 0.11 days per day of snowmelt advance (peak 0.49 0.09 days, and senescence $0 . 2 8 \pm 0 . 1$ days). Thus, bee phenophases are potentially less sensitive than flowering phenophases to shifts in snowmelt timing, with bee emergence advancing at 55% the rate of first flowering, and bee peak advancing at 67% and 93% the rate of the two flower peaks. The discrepancy in the rates of shift of bee emergence and first flowering may be partially due to differences in the metric of onset, as first occurrence data may be biased and are inherently different from our measure of the first 5% of the foraging population (van Strien et al., 2008). We also note that the flower phenology study comprised a narrow elevation band at separate sites in the middle of the present study’s roughly 1000 m elevation transect, and patterns of phenological shift may vary across elevation. Nevertheless, this difference in the sensitivities of bee and flowering phenology indicates the potential for a community-wide mismatch in this plant–pollinator system due to climate change. While the ability of both bees and flowering plants to respond to climatic cues is a promising sign for future synchrony under climate warming, the difference in rates of shift suggests at least short-term mismatches, which may become chronic if the interacting species are not able to adapt or shift their ranges to match the rate of climate change (van Asch et al., 2007).

## CONCLUSIONS

Community-level bee phenology is shaped primarily by climatic cues, elevation, nest location, and overwintering stage. Early phenology is particularly sensitive to climatic variation, whereas later phenology is determined more by functional traits, suggesting that climate change will affect emergence more than senescence, potentially lengthening the active foraging period of bees. And while more long-term and specieslevel studies are needed, the present results suggest that the responsiveness of bee phenology may lag behind that of flowers.

## ACKNOWLEDGEMENTS

W.D.P. and M.S. were funded by NSF ABI-1759965, NSF EF-1802605 and USDA Forest Service agreement 18-CS-11046000-041. M.S. was funded by the NSF Graduate Research Fellowship under Grant No. 1745048. Field work for this research was supported by NSF DEB-0922080 and DEB-1354104 to D.W.I, R.E.I. and B.D.I, and funds from NC State University to R.E.I. We thank the research assistants associated with the collection of the long-term bee data, and the RMBL and private land owners for access to field sites, billy barr for weather data and three anonymous reviewers whose comments greatly improved the paper. Any opinions, findings, conclusions or recommendations expressed in this material are those of the authors and do not necessarily reflect the views of the funding agencies.

## AUTHOR CONTRIBUTIONS

R.E.I., B.D.I. and D.W.I. designed research; M.S., S.R.G., G.L.P. and R.E.I. performed research; J.G., T.G., J.L.N., R.O., M.G.R., C.S.S. and K.W. provided taxonomic expertise; M.S. and W.D.P. analysed data; M.S. wrote the paper with feedback from all authors.

## PEER REVIEW

The peer review history for this article is available at https:// publons.com/publon/10.1111/ele.13583.

## DATA ACCESSIBILITY STATEMENT

We are committed to public access to data for scientific reproducibility and transparency. Our data and code for analysis are freely available on Dryad (https://datadryad.org/stash/ dataset/doi:10.5061/dryad.t76hdr7zc). The bee phenology monitoring project is ongoing, and more data have been added since this publication. The most up-to-date data are available through Open Science Framework (https://osf.io kmxyn/).

## REFERENCES

Aldridge, G., Inouye, D.W., Forrest, J.R.K., Barr, W.A. & Miller-Rushing, A.J. (2011). Emergence of a mid-season period of low floral resources in a montane meadow ecosystem associated with climate change. J. Ecol., 99, 905–913.

Altermatt, F. (2010). Climatic warming increases voltinism in European butterflies and moths. Proc. R. Soc. B Biol. Sci., 277, 1281–1287.

Bates, D., Machler, M., Bolker, B. & Walker, S. (2014). Fitting linear¨ mixed-effects models using lme4. J. Stat. Software, 67, 1–48.

Bartomeus, I., Ascher, J.S., Wagner, D., Danforth, B.N., Colla, S., Kornbluth, S. et al. (2011). Climate-associated phenological advances in bee pollinators and bee-pollinated plants. Proc. Natl Acad. Sci. USA, 108, 20645–20649.

Bartomeus, I., Park, M.G., Gibbs, J., Danforth, B.N., Lakso, A.N. & Winfree, R. (2013). Biodiversity ensures plant-pollinator phenological synchrony against climate change. Ecol. Lett., 16, 1331–1338.

Barton, K. (2015). Package ‘MuMIn’. Version, 1, 18.

Bell, J.R., Alderson, L., Izera, D., Kruger, T., Parker, S., Pickup, J. et al. (2015). Long-term phenological trends, species accumulation rates, aphid traits and climate: Five decades of change in migrating aphids. J. Animal Ecol., 84, 21–34.

Burnham, K.P. & Anderson, D.R. (1998). Practical use of the information-theoretic approach. Model selection and inference. Springer, New York, NY, pp. 75–117.

Cade, B.S. (2015). Model averaging and muddled multimodel inferences. Ecology, 96, 2370–2382.

Cane, J.H., Minckley, R.L. & Kervin, L.J. (2000). Sampling bees (Hymenoptera: Apiformes) for pollinator community studies: Pitfalls of pan-trapping. J. Kansas Entom. Soc., 73, 225–231.

CaraDonna, P.J., Iler, A.M. & Inouye, D.W. (2014). Shifts in flowering phenology reshape a subalpine plant community. Proc. Natl Acad. Sci. USA, 111, 4916–4921.

CaraDonna, P.J., Cunningham, J.L. & Iler, A.M. (2018). Experimental warming in the field delays phenology and reduces body mass, fat content and survival: Implications for the persistence of a pollinator under climate change. Funct. Ecol., 32, 2345–2356.

Cohen, J.M., Lajeunesse, M.J. & Rohr, J.R. (2018). A global synthesis of animal phenological responses to climate change. Nat. Clim. Change, 8, 224–228.

Danforth, B.N. (1999). Emergence dynamics and bet hedging in a desert bee, Perdita portalis. Proc. R. Soc. B Biol. Sci., 266, 1985–1994.

Diamond, S., Frame, A., Martin, R. & Buckely, L. (2011). Species’ traits predict phenological responses to climate change in butterflies. Ecology, 92, 1005–1012.

Donnelly, A., Caffarra, A. & O’Neill, B.F. (2011). A review of climatedriven mismatches between interdependent phenophases in terrestrial and aquatic ecosystems. Intl. J. Biometeorology, 55, 805–817.

Ellwood, E.R., Diez, J.M., Iba´nez, I., Primack, R.B., Kobori, H., Higuchi, H.˜ et al. (2012). Disentangling the paradox of insect phenology: Are temporal trends reflecting the response to warming? Oecologia, 168, 1161–1171.

Ettinger, A.K., Gee, S. & Wolkovich, E.M. (2018). Phenological sequences: how early-season events define those that follow. Am. J. Bot., 105, 1771–1780.

Forrest, J.R. (2016). Complex responses of insect phenology to climate change. Curr. Op. Insect Sci., 17, 49–54.

Forrest, J.R., Cross, R. & CaraDonna, P.J. (2019). Two-year bee, or not two-year bee? How voltinism is affected by temperature and season length in a high-elevation solitary bee. Am. Nat., 193, 560–574.

Forrest, J.R.K. & Thomson, J.D. (2011). An examination of synchrony between insect emergence and flowering in Rocky Mountain meadows. Ecol. Monogr., 81, 469–491.

Fracheboud, Y., Luquez, V., Bjork¨ en, L., Sj´ odin, A., Tuominen, H. &¨ Jansson, S. (2009). The control of autumn senescence in European aspen. Plant Phys., 149, 1982–1991.

Frund, J., Zieger, S.L. & Tscharntke, T. (2013). Response diversity of¨ wild bees to overwintering temperatures. Oecologia, 173, 1639–1648.

Gallinat, A.S., Primack, R.B. & Wagner, D.L. (2015). Autumn, the neglected season in climate change research. Trends Ecol. Evol., 30, 169–176.

Galipaud, M., Gillingham, M.A.F., David, M & Dechaume-Moncharmont, F.X. (2014) Ecologists overestimate the importance of predictor variables in model averaging: a plea for cautious interpretations. Methods in Ecology and Evolution, 5(10), 983–991. https://besjournals.onlinelibrary. wiley.com/doi/abs/10.1111/2041-210X.12251.

Gelman, A. (2008). Scaling regression inputs by dividing by two standard deviations. Stat. Med., 27, 2865–2873.

Gelman, A. & Hill, J. (2006). Data analysis using regression and multilevel/ hierarchical models. Cambridge University Press, Cambridge, United Kingdom and New York, NY.

Gezon, Z.J., Wyman, E.S., Ascher, J.S., Inouye, D.W. & Irwin, R.E. (2015). The effect of repeated, lethal sampling on wild bee abundance and diversity. Meth. Ecol. & Evol., 6, 1044–1054.

Gibbs, J. (2010). Revision of the metallic species of Lasioglossum (Dialictus) in Canada (Hymenoptera, Halictidae, Halictini). Zootaxa, 2591, 1–382.

Hedhly, A., Hormaza, J.I. & Herrero, M. (2009). Global warming and sexual plant reproduction. Trends Plant Sci., 14, 30–36.

Hegland, S.J., Nielsen, A., Lazaro, A., Bjerknes, A.L. & Totland, Ø.´ (2009). How does climate warming affect plant-pollinator interactions? Ecol. Lett., 12, 184–195.

Inouye, B.D., Ehrlen, J. & Underwood, N. (2019). Phenology as a process´ rather than an event: from individual reaction norms to community metrics. Ecol. Monogr., 89, 1–15.

Inouye, D.W. (2008). Effects of climate change on phenology, frost damage, and floral abundance of montane wildflowers. Ecology, 89, 353–362.

IPCC (2014) Climate Change 2014: Synthesis Report. Contribution of Working Groups I, II and III to the Fifth Assessment Report of the Intergovernmental Panel on Climate Change [Core Writing Team, R.K. Pachauri and L.A. Meyer (eds.)]. Cambridge University Press, Cambridge, United Kingdom and New York, NY.

Kemp, W.P. & Bosch, J. (2005). Effect of temperature on Osmia lignaria (Hymenoptera: Megachilidae) prepupa – adult development, survival, and emergence. J. Econ. Entom., 98, 1917–1923.

Kharouba, H.M., Ehrlen, J., Gelman, A., Bolmgren, K., Allen, J.M. &´ Travers, S.E. (2018). Global shifts in the phenological synchrony of species interactions over recent decades. Proc. Natl Acad. Sci. USA, 115, 5211–5216.

Klein, A.M., Vaissiere, B.E., Cane, J.H., Steffan-Dewenter, I.,\` Cunningham, S.A., Kremen, C. et al. (2007). Importance of pollinators in changing landscapes for world crops. Proc. R. Soc. B Biol. Sci., 274, 303–313.

Keenan, T.F. & Richardson, A.D. (2015). The timing of autumn senescence is affected by the timing of spring phenology: Implications for predictive models. Glob. Change Biol., 21, 2634–2641.

Kehrberger, S. & Holzschuh, A. (2019). Warmer temperatures advance flowering in a spring plant more strongly than emergence of two solitary spring bee species. PLoS One, 14, 1–15.

Konig, P., Tautenhahn, S., Cornelissen, J.H.C., Christine, R., Kattge, J.¨ & Gerhard, B. (2018). Advances in flowering phenology across the Northern Hemisphere are explained by functional traits. Glob. Ecol. & Biogeography, 27, 310–321.

Kudo, G. & Ida, T. (2013). Early onset of spring increases the phenological mismatch between plants and pollinators. Ecology, 94, 2311–2320.

Kudo, G., Nishikawa, Y., Kasagi, T. & Kosuge, S. (2004). Does seed production of spring ephemerals decrease when spring comes early? Ecol. Res., 19, 255–259.

Kuznetsova, A., Brockhoff, P.B. & Christensen, R.H.B. (2017). lmerTest Package: Tests in linear mixed effects models. J. Stat. Softw., 82, 1–26.

LeBuhn, G., Griswold, T., Minckley, R., Droege, S., Cane, J. & Buchmann, S. (2003). A standardized method for monitoring bee populations – The Bee Inventory (BI) Plot.

Linden, A. (2018). Adaptive and nonadaptive changes in phenological´ synchrony. Proc. Natl Acad. Sci. USA, 115, 5057–5059.

Menzel, A. (2003). Plant phenological anomalies in Germany and their relation to air temperature and NAO. Clim. Change, 57, 243–263.

Michener, C.D. (2000). The Bees of the World. Johns Hopkins Press, Baltimore, MD.

Michener, C.D., McGinley, R.J. & Danforth, B.N. (1994). The Bee Genera of North and Central America (Hymenoptera: Apoidea). Smithsonian Institution Press, Washington, D.C.

Miller-Rushing, A.J., Inouye, D.W. & Primack, R.B. (2008). How well do first flowering dates measure plant responses to climate change? The effects of population size and sampling frequency. J. Ecol., 96, 1289–1296.

Ogilvie, J.E., Griffin, S.R., Gezon, Z.J., Inouye, B.D., Underwood, N., Inouye, D.W. et al. (2017). Interannual bumble bee abundance is

driven by indirect climate effects on floral resource phenology. Ecol. Lett., 20, 1507–1515.

Olliff-yang, R.L. & Mesler, M.R. (2018). The potential for phenological mismatch between a perennial herb and its ground-nesting bee pollinator. AoB Plants, 10, 1–11.

Ovaskainen, O., Skorokhodova, S., Yakovleva, M., Sukhov, A., Kutenkov, A., Kutenkova, N. et al. (2013). Community-level phenological response to climate change. Proc. Natl Acad. Sci. USA, 110, 13434–13439.

Parton, W. & Logan, J. (1981). A model for diurnal variation in soil and air temperature. Ag. Meteorology, 23, 205–216.

Petanidou, T., Kallimanis, A.S., Sgardelis, S.P., Mazaris, A.D., Pantis, J.D. & Waser, N.M. (2014). Variable flowering phenology and pollinator use in a community suggest future phenological mismatch. Acta Oecologica, 59, 104–111.

Parmesan, C. & Yohe, G. (2003). A globally coherent fingerprint of climate change impacts across natural systems. Nature, 421, 37–42.

Pyke, G., Inouye, D.W. & Thomson, J. (2011). Activity and abundance of bumble bees near Crested Butte, Colorado: diel, seasonal, and elevation effects. Ecol. Entom., 36, 511–521.

Rafferty, N.E., CaraDonna, P.J. & Bronstein, J.L. (2015). Phenological shifts and the fate of mutualisms. Oikos, 124, 14–21.

Rafferty, N. & Ives, A.R. (2012). Pollinator effectiveness varies with experimental shifts in flowering time. Ecology, 93, 803–814.

Renner, S.S. & Zohner, C.M. (2018). Climate change and phenological mismatch in trophic interactions among plants, insects, and vertebrates. Annu. Rev. Ecol. Evol. Sys., 49, 165–182.

Roy, D.B. & Sparks, T.H. (2000). Phenology of British butterflies and climate change. Glob. Change Biol., 6, 407–416.

Schenk, M., Krauss, J. & Holzschuh, A. (2018). Desynchronizations in bee – plant interactions cause severe fitness losses in solitary bees. J. Animal Ecol., 87, 139–149.

Scott, V.L., Ascher, J.S., Griswold, T. & Nufio, C.R. (2011). The Bees of Colorado. University of Colorado Museum of Natural History, Boulder CO, Natural History Inventory of Colorado.

Slominski, A.H. & Burkle, L.A. (2019). Solitary bee life history traits and sex mediate responses to manipulated seasonal temperatures and season length. Front. Ecol. Eviron., 7, 1–15.

Stone, G.N. & Willmer, P.G. (1989). Warm-up rates and body temperatures in bees: The importance of body size, thermal regime and phylogeny. J. Exper. Biol., 147, 303–328.

Thackeray, S.J., Henrys, P.A., Hemming, D., Bell, J.R., Botham, M.S., Burthe, S. et al. (2016). Phenological sensitivity to climate across taxa and trophic levels. Nature, 535, 241–245.

Theobald, E., Breckheimer, I. & HilleRisLambers, J. (2017). Climate drives phenological reassembly of a mountain wild-flower meadow community. Ecology, 98, 2799–2812.

Van Asch, M., van Tienderen, P.H., Holleman, L.J.M. & Visser, M.E. (2007). Predicting adaptation of phenology in response to climate change, an insect herbivore example. Glob. Change Biol., 13, 1596–1604.

Van Dyck, H., Bonte, D., Puls, R., Gotthard, K. & Maes, D. (2015). The lost generation hypothesis: could climate change drive ectotherms into a developmental trap? Oikos, 124, 54–61.

Van Strien, A.J., Plantenga, W.F., Soldaat, L.L., Van Swaay, C.A.M. & WallisDeVries, M.F. (2008). Bias in phenology assessments based on first appearance data of butterflies. Oecologia, 156, 227–235.

Vanbergen, A.J., Garratt, M.P., Vanbergen, A.J., Baude, M., Biesmeijer, J.C., Britton, N.F. et al. (2013). Threats to an ecosystem service: Pressures on pollinators. Front. Ecol. Environ., 11, 251–259.

Visser, M.E. & Gienapp, P. (2019). Evolutionary and demographic consequences of phenological mismatches. Nat. Ecol. & Evol., 12, 879–885.

Warren, R.J. & Bradford, M.A. (2014). Mutualism fails when climate response differs between interacting species. Glob. Change Biol., 20, 466–474.

White, J., Son, Y. & Park, Y.-L. (2009). Temperature-dependent emergence of Osmia cornifrons (Hymenoptera: Megachilidae) adults. J. Econ. Entomol., 102, 2026–2032.

Wipf, S. (2010). Phenology, growth, and fecundity of eight subarctic tundra species in response to snowmelt manipulations. Plant Ecol., 207, 53–66.

Wood, S.N. (2017). Generalized Additive Models: An introduction with R. Chapman and Hall/CRC, Boca Raton, FL.

Wright, S.J., Kitajima, K., Kraft, N.J., Reich, P.B., Wright, I.J., Bunker, D.E. et al. (2010). Functional traits and the growth–mortality trade-off in tropical trees. Ecology, 91, 3664–3674.

## SUPPORTING INFORMATION

Additional supporting information may be found online in the Supporting Information section at the end of the article.

Editor, Tim Coulson Manuscript received 8 June 2020 First decision made 1 July 2020 Manuscript accepted 8 July 2020