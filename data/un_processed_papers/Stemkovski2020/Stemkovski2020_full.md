<!-- page 1 of 10 -->

0

Check for updates

ECOLOGYLETTERS

Ecology Letters, (2020) 23: 1589–1598

doi: 10.1111/ele.13583

## L E T T E R

# Bee phenology is predicted by climatic variation and functional traits

Michael Stemkovski,<sup>1,2</sup>\* iD
William D. Pearse,<sup>1,3</sup>
Sean R. Griffin,<sup>2,4</sup>
Gabriella L. Pardee,<sup>2,4</sup>
Jason Gibbs,<sup>5</sup>
Terry Griswold,<sup>6</sup>
John L. Neff,<sup>7</sup>
Ryan Oram,<sup>8</sup>
Molly G. Rightmyer,<sup>9</sup>
Cory S. Sheffield,<sup>8</sup>
Karen Wright,<sup>10</sup> Brian D.
Inouye,<sup>2,11</sup>
David W.
Inouye<sup>2,12</sup>
and
Rebecca E. Irwin<sup>2,13</sup>\*

![Image block](doc:1d5e952/tier:advanced/page:1/block:11)

![Image block](doc:1d5e952/tier:advanced/page:1/block:13)

![Image block](doc:1d5e952/tier:advanced/page:1/block:15)

![Image block](doc:1d5e952/tier:advanced/page:1/block:17)

![Image block](doc:1d5e952/tier:advanced/page:1/block:19)

![Image block](doc:1d5e952/tier:advanced/page:1/block:21)

![Image block](doc:1d5e952/tier:advanced/page:1/block:23)

![Image block](doc:1d5e952/tier:advanced/page:1/block:26)

![Image block](doc:1d5e952/tier:advanced/page:1/block:29)

![Image block](doc:1d5e952/tier:advanced/page:1/block:32)

![Image block](doc:1d5e952/tier:advanced/page:1/block:35)

## Abstract

Climate change is shifting the environmental cues that determine the phenology of interacting species. Plant–pollinator systems may be susceptible to temporal mismatch if bees and flowering plants differ in their phenological responses to warming temperatures. While the cues that trigger flowering are well-understood, little is known about what determines bee phenology. Using generalised additive models, we analyzed time-series data representing 67 bee species collected over 9 years in the Colorado Rocky Mountains to perform the first community-wide quantification of the drivers of bee phenology. Bee emergence was sensitive to climatic variation, advancing with earlier snowmelt timing, whereas later phenophases were best explained by functional traits including overwintering stage and nest location. Comparison of these findings to a long-term flower study showed that bee phenology is less sensitive than flower phenology to climatic variation, indicating potential for reduced synchrony of flowers and pollinators under climate change.

## Keywords

Climate change, emergence, environmental cues, GAM (generalised additive models), Hymenoptera, mismatch, peak, phenophases, senescence.

Ecology Letters (2020) 23: 1589–1598

## INTRODUCTION

Ecological relationships break down when the synchrony of interacting species is disrupted. Climate change is altering the phenology (timing of life-history events) of species, with spring events generally happening earlier (Bell et al., 2015; Cohen et al., 2018) and fall events later (Gallinat et al., 2015). Crucially, the rate of phenological shift varies among co-occurring species and guilds (Thackeray et al., 2016; Konig ¨ et al., 2018). This is of particular concern for species within cross-guild associations, such as plants and their pollinators, because the two groups may have different sensitivities to environmental cues (Forrest and Thomson, 2011; Rafferty et al., 2015). Positively interacting species that experience a phenological mismatch due to different directions or rates of response to climate change are likely to suffer reduced fecundity or increased mortality (Visser and Gienapp, 2019). Mismatches due to climate change have been observed in consumer-resource systems (Kharouba et al., 2018) and mutualistic interactions (Petanidou et al., 2014). In the short term,

mutualist species that experience a phenological mismatch are expected to suffer fitness losses, followed by adaptation to reestablish synchrony (Visser and Gienapp, 2019). If climate change outpaces the rate of adaptation, however, mutualists may experience irreparable de-coupling. Thus, it is critically important to understand the drivers of phenological shifts and compare their magnitudes for interacting species.

In plant–pollinator systems, phenological mismatch due to earlier spring events has been reported for early season flowers and their pollinators (Kudo et al., 2004; Kudo and Ida, 2013). As spring events such as snowmelt timing are projected to occur earlier under climate change (IPCC, 2014), these mismatches are expected to become more common and pronounced. Phenological mismatch in a pollination system could have negative fitness consequences for plants through pollen limitation (Rafferty and Ives, 2012; Kudo and Ida, 2013), and pollinators through a lack of floral resources (CaraDonna et al., 2018; Schenk et al., 2018). At the community level, mismatches can lead to a collapse of the mutualism (Warren and Bradford, 2014), and may reduce crop yield in agricultural

<small><span class="docvortex-page-footnote" data-block-type="page_footnote" style="color:#6b7280"><sup>1</sup>Department of Biology & Ecology Center, Utah State University, 5305 Old Main Hill, Logan, UT 84322, USA</span></small>

<small><span class="docvortex-page-footnote" data-block-type="page_footnote" style="color:#6b7280"><sup>2</sup>Rocky Mountain Biological Laboratory, Crested Butte, CO 81224, USA</span></small>

<small><span class="docvortex-page-footnote" data-block-type="page_footnote" style="color:#6b7280"><sup>3</sup>Department of Life Sciences, Imperial College London, Silwood Park Campus, Buckhurst Rd., Ascot, Berkshire SL5 7PY, UK</span></small>

<small><span class="docvortex-page-footnote" data-block-type="page_footnote" style="color:#6b7280"><sup>4</sup>Department of Integrative Biology, University of Texas at Austin, 2415 Speedway, Stop C0930, Austin, TX 78712, USA</span></small>

<small><span class="docvortex-page-footnote" data-block-type="page_footnote" style="color:#6b7280"><sup>5</sup>Department of Entomology, University of Manitoba, Winnipeg, Manitoba R3T 2N2, Canada</span></small>

<small><span class="docvortex-page-footnote" data-block-type="page_footnote" style="color:#6b7280"><sup>6</sup>USDA-ARS Pollinating Insects Research Unit, Utah State University, Logan, UT 84322-5310, USA</span></small>

<small><span class="docvortex-page-footnote" data-block-type="page_footnote" style="color:#6b7280"><sup>7</sup>Central Texas Melittological Institute, 7307 Running Rope, Austin, TX 78731, USA</span></small>

<small><span class="docvortex-page-footnote" data-block-type="page_footnote" style="color:#6b7280"><sup>8</sup>Royal Saskatchewan Museum, 2340 Albert Street, Regina, Saskatchewan S4P 2V7, Canada</span></small>

<small><span class="docvortex-page-footnote" data-block-type="page_footnote" style="color:#6b7280"><sup>9</sup>San Diego, CA 92116, USA</span></small>

<small><span class="docvortex-page-footnote" data-block-type="page_footnote" style="color:#6b7280">10<sub>Department</sub> of Entomology, Texas A&M University, 2475 TAMU, College Station, TX 77845, USA</span></small>

<small><span class="docvortex-page-footnote" data-block-type="page_footnote" style="color:#6b7280">11<sub>Department</sub> of Biological Science, Florida State University, Tallahassee, FL 32306, USA</span></small>

<small><span class="docvortex-page-footnote" data-block-type="page_footnote" style="color:#6b7280">12<sub>Department</sub> of Biology, University of Maryland, College Park, MD 20742, USA</span></small>

<small><span class="docvortex-page-footnote" data-block-type="page_footnote" style="color:#6b7280">13<sub>Department</sub> of Applied Ecology, North Carolina State University, Campus Box 7617, Raleigh, NC 27695, USA</span></small>

<small><span class="docvortex-page-footnote" data-block-type="page_footnote" style="color:#6b7280">\*Correspondence: E-mails: m.stemkovski@gmail.com; reirwin@ncsu.edu</span></small>

© 2020 John Wiley & Sons Ltd.

<!-- page 2 of 10 -->

1590

M. Stemkovski et al.

Letter

systems if pollinator species richness is low (Bartomeus et al., 2013). While phenological responses to climate change have been well documented for plants (Parmesan and Yohe, 2003; CaraDonna et al., 2014; Konig ¨ et al., 2018), less is known about the responses of pollinators, especially insect pollinators such as bees (Bartomeus et al., 2011). Even if bee and flowering phenologies are both responsive to temperature (Hegland et al., 2009; Forrest and Thomson, 2011; Renner and Zohner, 2018), they may not be equally sensitive to variation in temperature, potentially leading to a future mismatch under climate change (Ellwood et al., 2012; Ovaskainen et al., 2013; Petanidou et al., 2014; Olliff-Yang and Mesler, 2018). The few studies that have examined the phenological response of bees to environmental cues have been limited by practical constraints mostly to small subsets of the total bee community (e.g. Kehrberger and Holzschuh, 2019; Slominski and Burkle, 2019). To understand the full effects of climate change on plant communities, it is imperative to determine the community-level drivers of bee phenology given the role of bees as the primary pollinators in most ecosystems (Klein et al., 2007).

From the perspective of pollination, the most important bee activity is the flight period in which adults transfer pollen. The flight period can be described by three points in time (hereafter phenophases): emergence from nests (the beginning of adult foraging, rather than the time of eclosion), timing of the peak abundance of foragers, and senescence (the end of foraging). These phenophases may be driven by different environmental cues, but may also be linked by developmental time (Donnelly et al., 2011; Keenan and Richardson, 2015; Ettinger et al., 2018). Differences in temperature (Forrest and Thomson, 2011), soil moisture (Danforth, 1999; Olliff-Yang and Mesler, 2018), and snowmelt timing along elevation gradients in montane regions (Pyke et al., 2011) may shift bee emergence phenology. Snowmelt timing may be particularly influential in areas where the growing season is limited by many months of persistent snowpack. Given these sensitivities, bee phenology has advanced, on average, due to climate change (Bartomeus et al., 2011). Certain functional traits (those that influence fitness) may shape bee phenology (Diamond et al., 2011; Forrest, 2016), including variable thermal tolerance due to body mass (Stone and Wilmer, 1989), nest location (Bartomeus et al., 2011), and the life stage in which bees overwinter (Frund ¨ et al., 2013). Species that nest above ground are expected to be more responsive to climatic variation, as air temperature is more variable than soil temperature (Parton and Logan, 1981), and the stage in which bees overwinter may interact with climate to determine when they can emerge from nests because prepupae-overwintering species must undergo additional development before emergence (Forrest, 2016). While these drivers of phenology have been described in isolation, understanding their relative importance and potential interactions is impossible without a comprehensive study that examines them simultaneously at the community level.

Here, we present findings on the drivers of bee phenology using 9 years of time-series data from a study of solitary bees along an elevation gradient. To make phenology estimates from a sparse time-series data set and to avoid the biases of first-observation dates (Miller-Rushing et al., 2008; Linden, ´ 2018; Inouye et al., 2019), we introduce an approach based on

generalised additive models that calculate the first 5%, middle, and last 5% of a distribution (van Strein et al., 2008), corresponding to the three phenophases of foraging bee populations. We used these estimates to determine the drivers of bee phenology at the community level, including climate, topography, and bee traits, by comparing phenological variation among years. Specifically, we investigated the predictions that earlier phenophases are more strongly affected by climate variation compared to late phenophases (Forrest, 2016), and that snowmelt timing is the primary driver of bee phenology in the subalpine ecosystem of this study, as it is for flower phenology (Inouye, 2008). We also predicted that species that overwinter as adults emerge earlier than those that overwinter as pre-pupae, because they are less constrained by development time in the early growing season (Frund ¨ et al., 2013). Motivated by the idea that species’ phenological plasticity to climatic variation may be mediated by their traits (Diamond et al., 2011), we tested for an interaction between two traits (nest location and overwintering stage) and snowmelt timing. Finally, to explore whether bee phenology will track flower phenology under climate change (Ogilvie et al., 2017), we compared rates of advance in bee phenology in response to earlier snowmelt timing to published rates in flowering phenology at nearby study sites (CaraDonna et al., 2014). By providing the first community-level assessment of the drivers of bee phenology, our findings give insight into the future of plant–pollinator systems under forecasted climate change.

## METHODS

## Study system

We gathered data at 18 sites around the Rocky Mountain Biological Laboratory (RMBL) in the Elk Mountains of western Colorado, USA from 2009 to 2017 (Table S2). Sites were located along an elevation transect (2456–3438 metres above sea-level) in montane and subalpine habitats dominated by a diverse mixture of perennial flowering species (CaraDonna et al., 2014). The area is highly seasonal, with snowpack typically persisting from November until May. The short growing season of only a few summer months results in predominantly univoltine bee life cycles, although some bee species may exhibit parsivoltine life cycles (Forrest et al., 2019). The European honey bee Apis mellifera and other non-native bees were absent during the study period.

## Bee data collection

We sampled bees in habitat types that were representative of dominant vegetation types: wet meadows dominated by Veratrum tenuipetalum, those dominated by Salix spp., rocky dry meadows, and Artemisia spp. steppe. We conducted biweekly bee abundance surveys at each site using pan traps (following LeBuhn et al., 2003). We set out 10 each of white, fluorescent yellow, and fluorescent blue pan traps along two approx. perpendicular 45-m transects at intervals of 3 m, an array that passively attracts bees by mimicking a display of flowers. We deployed pan traps between approx. 0800 and 1700 (the period of maximum bee activity) only on warm, calm, sunny

© 2020 John Wiley & Sons Ltd.

14610248, 2020, 11, Downloaded from https://onlinelibrary.wiley.com/doi/10.1111/ele.13583 by Faculdade Medicina De Lisboa, Wiley Online Library on [31/10/2025]. See the Terms and Conditions (https://onlinelibrary.wiley.com/terms-and-conditions) on Wiley Online Library for rules of use; OA articles are governed by the applicable Creative Commons License

<!-- page 3 of 10 -->

Letter

Drivers of bee phenology

1591

days and removed traps when these conditions changed drastically. Further details of the bee sampling are provided by Gezon et al. (2015). Specimens were identified to the lowest taxonomic resolution possible using a variety of resources (Michener et al., 1994; Michener, 2000; Gibbs, 2010; Scott et al., 2011). We excluded the pollen-foraging genera Anthidium, Ashmeadiella, Atoposmia, Eucera, Diadasia, and Dianthidium and all cleptoparasites (Coelioxys, Epeolus, Holcopasites, Nomada, Stelis, Sphecodes, and Triepeolus) because we were unable to identify them to species or they were very rare (together, individuals from these genera made up 4% of the collection). We were unable to identify most species of the diverse genus Andrena, so only four species in this genus are included in the analysis (this omission represents 3% of the total collection). The list of species included in the analysis is presented in Table S3. The population estimates at each sampling date were calculated as bees captured/hour of sampling, to account for variable sampling effort, including females and males (with the exception of Lasioglossum spp. for which we were only able to identify females). Because pan traps overrepresent small bees such as Halictids and under-represent large bees (Cane et al. 2000), we excluded the large-bodied genus Bombus from analyses (3% of pan-collected specimens).

## Climate, topographic, and trait data

To explain variation in bee phenology, we gathered data on yearly climate variation, topographic data associated with sites, and bee functional traits. We selected snowmelt timing, summer temperature, and summer rainfall as climate variables, elevation and solar incidence as topographic variables, and body mass, nest location, and overwintering stage as functional traits. Full details on the methods for gathering these data and justifications for their inclusion in the analyses are available in Supporting Information 1.

## Phenophase estimation

To bypass the problems of first-occurrence measures of sparse time-series data for many taxa including bees, take into account variable uncertainty, and estimate emergence, peak, and senescence dates from distributions of unknown form, we developed a novel application (validated in Supporting Information 2) of Generalized Additive Models (GAMs; Wood 2017). For each species/site/year combination, we fit a GAM with day-of-year as the explanatory variable and abundance as the response using a cubic spline smoothing basis with a Gaussian distribution family and performed generalised cross-validation to avoid over-fitting. We set the dimension of the smoothing basis to 4 when there were < 5 observations, and 5 for ≥ 5 observations. For each model fit, we determined the peak timing by calculating the predicted date of the maximum of the model fit and found the first and last occurrence of 5% of the maximum to determine dates of emergence and senescence, respectively. We did not record estimates of emergence or senescence in cases where sampling began too late or ended too early to observe the tails of the distribution below 5% of the maximum. We also did not record estimates of peak abundance when we did not unambiguously observe the “crest” of

the abundance curve, though we were able in some cases to estimate emergence or senescence but not peak by identifying the transition from zeroes to positive abundances. Due to this conservative approach, we were able to make emergence estimates for $4 7 \%$ of the total time-series, 40% for peak, and 53% for senescence. We calculated confidence intervals as twice the standard error at each phenophase. GAMs were implemented using the mgcv R-package (Wood, 2017).

## Modeling drivers of phenology

We created three candidate models by modelling emergence, peak, and senescence timing as functions of climate, topographic, and species trait variables, accounting for pseudoreplication at the site and species level by modelling these as random effects according to the equation

$$
D O Y _ {\text {phase}} \sim \theta_ {\text {clim}} + \theta_ {\text {topo}} + \theta_ {\text {trait}} + e _ {\text {site}} + e _ {\text {sp}}
$$

where $D O Y _ { p h a s e }$ is the estimated day-of-year (DOY) of each phenophase, $\theta _ { c l i m }$ are the climate variables (snowmelt date, summer temperature, and summer precipitation), $\theta _ { t o p o }$ are the topographic variables (elevation and solar incidence), $\theta _ { t r a i t }$ are species traits (body mass, nest location, and overwintering stage), $e _ { s i t e }$ are sites, and $e _ { s p }$ are species. θ terms represent fixed effects, whereas e terms represent random effects, forming a mixed effects model (Bates et al., 2014). All terms were modelled as additive effects, with no interactions in this top model. Due to heterogeneity in the frequency of sampling, population numbers, and shape of the abundance curves, phenophase estimates have heterogeneous confidence intervals. To propagate this uncertainty through our analysis, we weighted the estimates based on the inverse of their standard errors. To generate directly comparable standardised effect sizes, we scaled and centred explanatory variables (Gelman and Hill, 2006). To make categorical variables comparable to continuous ones, we scaled the continuous variables by 0.5 standard deviations (Gelman, 2008).

Because it is not known which of the proposed variables determine bee phenology at the community level, we employed a model averaging protocol, following Burnham and Anderson (1998), to determine which variables were influential. We fit models with each possible combination of pre-dictor variables and averaged coefficients from models within 4 AIC units of the best one. Because model averaging can bias estimates (Cade, 2015), we compared the averaged coefficients to the coefficients from the top model for each phenophase, finding very tight correlations (Pearson $r > 0 . 9 9 9$ for all three models, Figure S5). Additionally, we tested for multi-collinearity, finding sufficiently low variance inflation factors for each predictor (Supporting Information 3).

To investigate whether climate would more strongly affect emergence timing, whereas other variables would be more influential for later phenophases, we calculated marginal and conditional $R ^ { 2 }$ values based on the single best model in the top model set and investigated variance partitioned between climate and trait variables by calculating the proportion of variance explained by models fitted with just climate and trait variables vs. the top model. Due to small sample sizes for some species/predictor variable combinations, we were unable to estimate independent parameter values for every species,

© 2020 John Wiley & Sons Ltd.

14610248, 2020, 11, Downloaded from https://onlinelibrary.wiley.com/doi/10.1111/ele.13583 by Faculdade Medicina De Lisboa, Wiley Online Library on [31/10/2025]. See the Terms and Conditions (https://onlinelibrary.wiley.com/terms-and-conditions) on Wiley Online Library for rules of use; OA articles are governed by the applicable Creative Commons License

<!-- page 4 of 10 -->

1592

M. Stemkovski et al.

Letter

and treated species as a random effect in the full model. To provide a visual aid of some species-specific responses to advancing snowmelt and to compare with reported flower phenology shifts, we performed a reduced analysis with the most common species (those that had ≥ 10 species/site/year estimates for two or more phenophases), modelling species responses as $D O Y _ { p h a s e }   \sim   \Theta _ { s n o w m e l t }   *   s p e c i e s   +   e _ { s i t e } .$ This analysis was conducted for 10 species: three from the Andrenidae, one from the Colletidae, four from the Halictidae, and two from the Megachilidae. We did not control for phylogeny in the analyses because we did not seek to describe the evolution of the present traits. To investigate whether certain traits influence the phenological responsiveness of species to climate, we modelled phenophase estimates as functions of snowmelt (for other climatic variables, see Supporting Information 3) interacting with nest location and overwintering stage, with variable intercepts and slopes, holding all else equal, modelled as $D O Y _ { p h a s e }   { \sim }   \Theta _ { s n o w m e l t }   { * }   \Theta _ { t r a i t }   { + }   e _ { s p }   { + }   e _ { s i t e }$ . We did not include interaction terms in the top model due to the difficulty of estimating many additional parameters with limited data and complications with model averaging (Galipaud et al. 2014). We also tested for the presence of phenological sequences (Keenan and Richardson, 2015; Ettinger et al., 2018) by modelling peak and senescence as linear functions of emergence. Model averaging and $R ^ { 2 }$ calculation (r.squaredGLMM function) were done using the MuMIn package (Barton 2015). We tested for significance of interactions using the lmerTest package (Kuznetsova et al., 2017), and all analyses were run in R version 3.4.4 (R core team 2018).

## RESULTS

The bee monitoring study yielded 1606 time-series of at least four abundance measures for 67 species at 18 sites (Table S2) in 9 years (2009–2017), representing 23,742 collected specimens across 751 sampling periods. The mean maximum species-specific catch rate across all time-series was 1.48 bees/hour, ranging from 0.11 to 35.14 bees/hour per sampling period. We were able to estimate 519 emergence, 438 peak, and 584 senescence dates. The mean emergence day-of-year across all years, sites, and species was 24 June - 25 days, mean peak was 10 July - 21 days, and mean senescence was 30 July - 23 days. Responses to snowmelt, measured as the slope coefficient, fell generally between 0 and 1 days of phenological advance per day of snowmelt advance for most species (Figure 1; Table S4). Five phenophases across four species (Halictus virgatellus emergence and peak, Lasioglossum sedi senescence, Panurginus ineptus emergence, and Pseudopanurgus bakeri senescence) delayed in response to advanced snowmelt, though these effects were not significant. Hoplitis fulgida exhibited the greatest response in emergence to variation in snowmelt timing, whereas Hoplitis robusta had the greatest peak response (Figure 1). As an illustrative example, in the severe drought year of 2012, snowmelt occurred 25 days earlier than in other years, the median emergence phenology advanced by 34 days, peak by 15 days, and senescence by 4 days.

Each candidate predictor variable was represented in the model set (Figure 2). Bees emerged $( 1 1 . 5 2 \pm 2 . 6 8 )$ , peaked $( 1 2 . 8 2 \pm 2 . 4 2 )$ , and senesced $( 7 . 8 1 \pm 2 . 4 4 )$ later in years with

| Bee Species | Phenology Shift Category | Response to snowmelt (Days of phenology shift / Days of snowmelt shift) |
| :--- | :--- | :--- |
| Dufourea harveyi | Peak | ~0.2 |
| Dufourea harveyi | Emergence | ~0.3 |
| Halictus rubicundus | Peak | ~-0.1 |
| Halictus rubicundus | Emergence | ~0.4 |
| Halictus virgatellus | Peak | ~0.1 |
| Halictus virgatellus | Emergence | ~0.0 |
| Hoplitis fulgida | Peak | ~0.6 |
| Hoplitis fulgida | Emergence | ~0.7 |
| Hoplitis robusta | Peak | ~0.4 |
| Hoplitis robusta | Emergence | ~0.5 |
| Hylaeus annulatus | Peak | ~0.3 |
| Hylaeus annulatus | Emergence | ~0.4 |
| Lasioglossum sedi | Peak | ~0.6 |
| Lasioglossum sedi | Emergence | ~0.2 |
| Panurginus cressoniellus | Peak | ~0.3 |
| Panurginus cressoniellus | Emergence | ~0.4 |
| Panurginus ineptus | Peak | ~0.1 |
| Panurginus ineptus | Emergence | ~0.2 |
| Pseudopanurgus bakeri | Peak | ~-0.2 |
| Pseudopanurgus bakeri | Emergence | ~0.4 |

Figure 1 Common species vary in their responses to snowmelt timing, with most phenophase shifts falling between no response (0, dashed line) and perfect tracking (1, dotted line) of snowmelt. Points to the left of zero represent advances in response to advanced snowmelt timing, and those to the right represent delays. Blue points represent emergence shifts, green points represent peak, and brown points represent senescence. The width of bars represents twice the standard errors around the estimates of response.

later snowmelt date, and snowmelt timing had the largest absolute effect size among the climate variables for each phenophase. Elevation had the largest effect of the topographic variables, with bees at higher elevations emerging $( 1 3 . 5 7 \pm 3 . 2 3 )$ and peaking later $( 7 . 7 6 \pm 3 . 6 5 )$ , but senescing earlier $( - 5 . 9 2 \pm 4 . 0 5 )$ . Of the species traits, nest location had the largest effect on emergence timing; compared to bees that nest above ground, those that nest below ground emerged $( 1 1 . 2 1 \pm 4 . 3 0 )$ later but peaked $( - 4 . 5 7 \pm 3 . 8 4 )$ and senesced earlier $( - 9 . 8 2 \pm 4 . 2 9 )$ . Overwintering stage had the largest effects on peak and senescence timing; bees that overwinter as adults emerged $( 1 . 9 1 \pm 3 . 5 2 )$ , peaked $( 1 1 . 2 0 \pm 3 . 2 3 )$ , and senesced earlier $( 2 0 . 9 1   \pm   3 . 5 9 )$ than those that overwinter as pre-pupae. Each phenophase model was roughly equally able to predict the variation in yearly phenology (Figure 3a). When phenophases were predicted with subsets of the predictor variables, climate variables explained a higher proportion of the total variation for earlier phenophases, whereas species traits explained more variation in later phenophases (Figure 3b).

© 2020 John Wiley & Sons Ltd.

14610248, 2020, 11, Downloaded from https://onlinelibrary.wiley.com/doi/10.1111/ele.13583 by Faculdade Medicina De Lisboa, Wiley Online Library on [31/10/2025]. See the Terms and Conditions (https://onlinelibrary.wiley.com/terms-and-conditions) on Wiley Online Library for rules of use; OA articles are governed by the applicable Creative Commons License

<!-- page 5 of 10 -->

Letter

Drivers of bee phenology

1593

| Category | Emergence (Standardized effect size) | Peak (Standardized effect size) | Senescence (Standardized effect size) |
| --- | --- | --- | --- |
| Snowmelt date | ~12 | ~13 | ~8 |
| Summer rainfall | ~10 | ~3 | ~-2 |
| Maximum temperature | ~-7 | ~2 | ~-1 |
| Elevation | ~14 | ~8 | ~-6 |
| Solar incidence | ~-6 | ~-2 | ~4 |
| Body mass | ~2 | ~-3 | ~-3 |
| Nest location (below ground) | ~11 | ~-5 | ~-10 |
| Overwintering (prepupae) | ~2 | ~11 | ~21 |

Figure 2 Bee phenology is determined by interannual climatic variation, topography, and several species traits. The drivers vary in their relative effect across the phenophases, with the effect of climate variables generally lower for later phenophases. The first panel shows the standardised effect sizes of climate variables, the second topographic variables, and the third species traits on emergence (blue), peak (green), and senescence timing (brown) with standard errors around the estimates shown as brackets. Values greater than 0 represent later phenology, and those less than 0 represent earlier phenology. Standardised effect sizes are defined as the slope coefficients derived from scaled and centred explanatory variables.

Full numerical details including significance are provided in Tables S5 and S6.

There was a significant interaction between nest location and snowmelt timing for emergence $\left( t _ { 4 3 3 } = - 3 . 2 7 8 , \; P < 0 . 0 1 \right)$ and peak phenology $\left( t _ { 3 6 0 } = - 2 . 8 6 1 , \: P < 0 . 0 1 \right)$ (Figure 4), and the difference in slope decreased across the phenophases. The interaction between snowmelt timing and overwintering stage was greatest for peak timing and smallest for senescence timing, but these interactions were not statistically significant (emergence: $t _ { 4 4 1 } = - 0 . 8 6 7$ $P > 0 . 0 5 .$ , peak $t _ { 3 6 8 } = - 1 . 5 6 5 ,$ $P > 0 . 0 5 ,$ senescence $t _ { 4 7 0 } = - 0 . 4 8 1$ , P> 0.05). Lastly, we found that emergence significantly predicted peak timing $( F _ { 1 , 2 1 2 } = 2 0 1 . 2 , \quad P < 0 . 0 0 0 1 )$ and senescence timing $( F _ { 1 , 1 0 4 } = 2 9 . 6 3 , \: P < 0 . 0 0 0 1 )$ but that emergence described less variation in senescence $( R ^ { 2 } = 0 . 2 2 )$ than in peak timing $( R ^ { 2 } = 0 . 4 9 )$ (Figure S6).

## DISCUSSION

We analysed time-series abundance data from a 9-year bee monitoring project to provide the first community-wide assessment of the main predictors of bee emergence, peak, and senescence phenology. While yearly climatic variation, topography, and species functional traits all shaped bee phenology, the emergence and peak phenophases were particularly sensitive to climate. Following patterns in early-season flowering phenology (Inouye, 2008), the timing of early snowmelt, which is a determinant of how much thermal energy is

received by bee nests in this montane study area, was particularly influential in advancing the early phenophases. The later, senescence phenophase was determined to a greater extent by functional traits including nest location and the life stage in which bees overwinter (Frund ¨ et al., 2013). Nest location also disposed certain species to respond more dynamically to climatic variation. Contrary to predictions (Forrest, 2016), we did not find that adult-overwintering species responded more dynamically to climatic cues despite being less limited by development time prior to emergence. These findings lead us to predict that under increasing temperatures and earlier snowmelt due to climate change, the bee community foraging season will begin earlier and increase in overall duration. However, certain species may be less able to shift their phenology due to variable responses (Figure 1) on the basis of functional traits (Figure 4).

## Bee phenology is determined by climate, topography, and species traits

Snowmelt timing was the main climatic driver of bee phenology, with earlier dates of snowmelt advancing emergence and peak in particular (Figure 2, panel 1). Snowmelt in this system is a major determinant of how much thermal radiation is received by bee nests (for species that nest below ground), so this finding supports previous work suggesting that adult bee emergence has thermal requirements (Kemp and Bosch, 2005; White et al., 2009; Forrest and Thompson, 2011). Thus, we

© 2020 John Wiley & Sons Ltd.

14610248, 2020, 11, Downloaded from https://onlinelibrary.wiley.com/doi/10.1111/ele.13583 by Faculdade Medicina De Lisboa, Wiley Online Library on [31/10/2025]. See the Terms and Conditions (https://onlinelibrary.wiley.com/terms-and-conditions) on Wiley Online Library for rules of use; OA articles are governed by the applicable Creative Commons License

<!-- page 6 of 10 -->

1594

M. Stemkovski et al.

Letter

| Category | Emergence \((R^{2}\) values) | Peak \((R^{2}\) values) | Senescence \((R^{2}\) values) |
| --- | --- | --- | --- |
| Marginal | ~0.50 | ~0.41 | ~0.45 |
| Conditional | ~0.86 | ~0.90 | ~0.85 |

Figure 3 While the models were roughly equal in their ability to predict phenological shifts across all phenophases (panel a), early phenophases were predicted more strongly by climate variables and late phenophases by species traits (panel b). Panel a compares the marginal and conditional $R ^ { 2 }$ values across the top models for each phenophase, and panel b shows the ratio of variance explained by reduced models of only climate and trait variables vs. the variance explained by the top model. The ratio of variance in panel b was calculated as $R _ { \mathrm { ~ s u b s e t } } ^ { 2 } / R _ { \mathrm { ~ t o t a l } } ^ { 2 }$ where $R _ { \mathrm { ~ s u b s e t } } ^ { 2 }$ is the marginal $R ^ { 2 }$ of a model containing just climate or just species trait variables and $R _ { \mathrm { t o t a l } } ^ { 2 }$ is that of the top model containing all variables.

expect bee species in areas without persistent snowpack to similarly adjust their phenology on the basis of thermal energy. Higher summer temperatures and lower summer rainfall resulted in significantly earlier bee emergence but not peak or senescence, resulting in longer community-wide flight periods. Spring events that shape the onset of a phenological process can have cascading effects on later phenophases, leading to phenological sequences, but this cascade can become less pronounced due to variation in developmental time and the influence of other cues (Keenan and Richardson, 2015; Ettinger et al., 2018). We found that emergence timing did predict peak and senescence timing, but that emergence timing described less variation in senescence than in peak timing (Figure S6). Thus, the earlier phenophase of bee foraging influences, but does not determine, the later phenophases. Sites at higher elevations experienced later bee emergence and peak times, but earlier senescence time (though the senescence effect was not significant), resulting in a shortened foraging season (Figure 2, panel 2). These findings support studies that found a phenological shift in bumble bee abundance based on elevation (Pyke et al., 2011) and are in line with findings on flower phenology (Theobald et al., 2017). We note that because we calculated climatic variables as constant across sites within each year, the elevation effect may be driven by local variation in snowmelt timing, which is determined in part by solar incidence and elevation in montane regions.

Turning to species traits, nest location and overwintering stage, but not body mass, had significant effects on phenophases (Figure 2, panel 3). Ground-nesting bee species emerged later than those that nest above ground, but senesced earlier, indicating that below-ground nesting bee species have shorter average foraging periods. While our finding that adult-overwintering bees have earlier phenology supports the

idea that overwintering stage has a large effect on insect phenology broadly (Frund ¨ et al., 2013; Forrest, 2016), we were surprised to find that the effect was larger on peak and senescence timing than on emergence timing, which deviates from our initial expectation that overwintering stage would primarily dictate emergence phenology. It may be that there is an evolutionary trade-off between adult mortality rate and the fast development rate that allows certain species to overwinter as adults [see Wright et al. (2010) for an example in plants] or simply that adult-overwintering species have shorter effective foraging lifespans because they spend more time in the adult phase. More long-term studies are needed to understand if this is a general trend, and mechanistic studies would provide insight on the physiological underpinnings of the pattern.

While climatic variation, topography, and species traits determine the date of bee phenophases when viewed separately, bee species’ functional traits mediate their climate sensitivities (i.e., our models support an interaction between functional traits and environment). Above-ground nesting species are more sensitive to snowmelt timing (Figure 4, top panel) and average summer temperature (Supporting Information 3) than those that nest below ground. This finding is slightly counter-intuitive when we consider that ground-nesting bees are buried by snow. The discrepancy may be explained by recognising that snowmelt timing is correlated with other potential phenological cues such as spring temperature. We would expect above-ground nesting bees to be more sensitive to temperature fluctuations, as above-ground temperature varies more than below-ground (Parton and Logan, 1981), and their nests are not insulated by snowpack. This suggests that above-ground nesters may suffer less phenological mismatch with plants under increased variability due to climate change. Surprisingly, we did not find a significant

© 2020 John Wiley & Sons Ltd.

14610248, 2020, 11, Downloaded from https://onlinelibrary.wiley.com/doi/10.1111/ele.13583 by Faculdade Medicina De Lisboa, Wiley Online Library on [31/10/2025]. See the Terms and Conditions (https://onlinelibrary.wiley.com/terms-and-conditions) on Wiley Online Library for rules of use; OA articles are governed by the applicable Creative Commons License

<!-- page 7 of 10 -->

Letter

Drivers of bee phenology

1595

| Stage | Group | Date of bare ground (DOY) | Estimated phenology (DOY) |
| --- | --- | --- | --- |
| Emergence | Above ground | ~118 | ~153 |
| Emergence | Below ground | ~118 | ~177 |
| Emergence | Adults | ~118 | ~165 |
| Emergence | Pupae/Prepupae | ~118 | ~170 |
| Peak | Above ground | ~118 | ~184 |
| Peak | Below ground | ~118 | ~184 |
| Peak | Adults | ~118 | ~176 |
| Peak | Pupae/Prepupae | ~118 | ~192 |
| Senescence | Above ground | ~118 | ~210 |
| Senescence | Below ground | ~118 | ~200 |
| Senescence | Adults | ~118 | ~195 |
| Senescence | Pupae/Prepupae | ~118 | ~220 |
| Emergence | Adults | ~118 | ~165 |
| Emergence | Pupae/Prepupae | ~118 | ~170 |
| Emergence | Adults | ~118 | ~165 |
| Emergence | Pupae/Prepupae | ~118 | ~195 |
| Peak | Adults | ~118 | ~176 |
| Peak | Pupae/Prepupae | ~118 | ~192 |
| Peak | Adults | ~118 | ~176 |
| Peak | Pupae/Prepupae | ~118 | ~205 |
| Senescence | Adults | ~118 | ~195 |
| Senescence | Pupae/Prepupae | ~118 | ~220 |
| Senescence | Adults | ~118 | ~200 |
| Senescence | Pupae/Prepupae | ~118 | ~230 |
| Emergence | Adults | ~118 | ~165 |
| Emergence | Pupae/Prepupae | ~118 | ~170 |
| Emergence | Adults | ~118 | ~165 |
| Emergence | Pupae/Prepupae | ~118 | ~195 |
| Peak | Adults | ~118 | ~176 |
| Peak | Pupae/Prepupae | ~118 | ~192 |
| Peak | Adults | ~118 | ~176 |
| Peak | Pupae/Prepupae | ~118 | ~205 |
| Senescence | Adults | ~118 | ~195 |
| Senescence | Pupae/Prepupae | ~118 | ~220 |
| Senescence | Adults | ~118 | ~200 |
| Senescence | Pupae/Prepupae | ~118 | ~230 |
| Emergence | Adults | ~118 | ~165 |
| Emergence | Pupae/Prepupae | ~118 | ~170 |
| Emergence | Adults | ~118 | ~165 |
| Emergence | Pupae/Prepupae | ~118 | ~195 |
| Peak | Adults | ~118 | ~176 |
| Peak | Pupae/Prepupae | ~118 | ~192 |
| Peak | Adults | ~118 | ~176 |
| Peak | Pupae/Prepupae | ~118 | ~205 |
| Senescence | Adults | ~118 | ~195 |
| Senescence | Pupae/Prepupae | ~118 | ~220 |
| Senescence | Adults | ~118 | ~200 |
| Senescence | Pupae/Prepupae | ~118 | ~230 |
| Emergence | Adults | ~118 | ~165 |
| Emergence | Pupae/Prepupae | ~118 | ~170 |
| Emergence | Adults | ~118 | ~165 |
| Emergence | Pupae/Prepupae | ~118 | ~195 |
| Peak | Adults | ~118 | ~176 |
| Peak | Pupae/Prepupae | ~118 | ~192 |
| Peak | Adults | ~118 | ~176 |
| Peak | Pupae/Prepupae | ~118 | ~205 |
| Senescence | Adults | ~118 | ~195 |
| Senescence | Pupae/Prepupae | ~118 | ~220 |
| Senescence | Adults | ~118 | ~200 |
| Senescence | Pupae/Prepupae | ~118 | ~230 |
| Emergence | Adults | ~118 | ~165 |
| Emergence | Pupae/Prepupae | ~118 | ~170 |
| Emergence | Adults | ~118 | ~165 |
| Emergence | Pupae/Prepupae | ~118 | ~195 |
| Peak | Adults | ~118 | ~176 |
| Peak | Pupae/Prepupae | ~118 | ~192 |
| Peak | Adults | ~118 | ~176 |
| Peak | Pupae/Prepupae | ~118 | ~205 |
| Senescence | Adults | ~118 | ~195 |
| Senescence | Pupae/Prepupae | ~118 | ~220 |
| Senescence | Adults | ~118 | ~200 |
| Senescence | Pupae/Prepupae | ~118 | ~230 |
| Emergence | Adults | ~118 | ~165 |
| Emergence | Pupae/Prepupae | ~118 | ~170 |
| Emergence | Adults | ~118 | ~165 |
| Emergence | Pupae/Prepupae | ~118 | ~195 |
| Peak | Adults | ~118 | ~176 |
| Peak | Pupae/Prepupae | ~118 | ~192 |
| Peak | Adults | ~118 | ~176 |
| Peak | Pupae/Prepupae | ~118 | ~205 |
| Senescence | Adults | ~118 | ~195 |
| Senescence | Pupae/Prepupae | ~118 | ~220 |
| Senescence | Adults | ~118 | ~200 |
| Senescence | Pupae/Prepupae | ~118 | ~230 |
| Emergence | Adults | ~118 | ~165 |
| Emergence | Pupae/Prepupae | ~118 | ~170 |
| Emergence | Adults | ~118 | ~165 |
| Emergence | Pupae/Prepupae | ~118 | ~195 |
| Peak | Adults | ~118 | ~176 |
| Peak | Pupae/Prepupae | ~118 | ~192 |
| Peak | Adults | ~118 | ~176 |
| Peak | Pupae/Prepupae | ~118 | ~205 |
| Senescence | Adults | ~118 | ~195 |
| Senescence | Pupae/Prepupae | ~118 | ~220 |
| Senescence | Adults | ~118 | ~200 |
| Senescence | Pupae/Prepupae | ~118 | ~230 |
| Emergence | Adults | ~118 | ~165 |
| Emergence | Pupae/Prepupae | ~118 | ~170 |
| Emergence | Adults | ~118 | ~165 |
| Emergence | Pupae/Prepupae | ~118 | ~195 |
| Peak | Adults | ~118 | ~176 |
| Peak | Pupae/Prepupae | ~118 | ~192 |
| Peak | Adults | ~118 | ~176 |
| Peak | Pupae/Prepupae | ~118 | ~205 |
| Senescence | Adults | ~118 | ~195 |
| Senescence | Pupae/Prepupae | ~118 | ~220 |
| Senescence | Adults | ~118 | ~200 |
| Senescence | Pupae/Prepupae | ~118 | ~230 |
| Emergence | Adults | ~118 | ~165 |
| Emergence | Pupae/Prepupae | ~118 | ~170 |
| Emergence | Adults | ~118 | ~165 |
| Emergence | Pupae/Prepupae | ~118 | ~195 |
| Peak | Adults | ~118 | ~176 |
| Peak | Pupae/Prepupae | ~118 | ~192 |
| Peak | Adults | ~118 | ~176 |
| Peak | Pupae/Prepupae | ~118 | ~205 |
| Senescence | Adults | ~118 | ~195 |
| Senescence | Pupae/Prepupae | ~118 | ~220 |
| Senescence | Adults | ~118 | ~200 |
| Senescence | Pupae/Prepupae | ~118 | ~230 |
| Emergence | Adults | ~118 | ~165 |
| Emergence | Pupae/Prepupae | ~118 | ~170 |
| Emergence | Adults | ~118 | ~165 |
| Emergence | Pupae/Prepupae | ~118 | ~195 |
| Peak | Adults | ~118 | ~176 |
| Peak | Pupae/Prepupae | ~118 | ~192 |
| Peak | Adults | ~118 | ~176 |
| Peak | Pupae/Prepupae | ~118 | ~205 |
| Senescence | Adults | ~118 | ~195 |
| Senescence | Pupae/Prepupae | ~118 | ~220 |
| Senescence | Adults | ~118 | ~200 |
| Senescence | Pupae/Prepupae | ~118 | ~230 |
| Emergence | Adults | ~118 | ~165 |
| Emergence | Pupae/Prepupae | ~118 | ~170 |
| Emergence | Adults | ~118 | ~165 |
| Emergence | Pupae/Prepupae | ~118 | ~195 |
| Peak | Adults | ~118 | ~176 |
| Peak | Pupae/Prepupae | ~118 | ~192 |
| Peak | Adults | ~118 | ~176 |
| Peak | Pupae/Prepupae | ~118 | ~205 |
| Senescence | Adults | ~118 | ~195 |
| Senescence | Pupae/Prepupae | ~118 | ~220 |
| Senescence | Adults | ~118 | ~200 |
| Senescence | Pupae/Prepupae | ~118 | ~230 |
| Emergence | Adults | ~118 | ~165 |
| Emergence | Pupae/Prepupae | ~118 | ~170 |
| Emergence | Adults | ~118 | ~165 |
| Emergence | Pupae/Prepupae | ~118 | ~195 |
| Peak | Adults | ~118 | ~176 |
| Peak | Pupae/Prepupae | ~118 | ~192 |
| Peak | Adults | ~118 | ~176 |
| Peak | Pupae/Prepupae | ~118 | ~205 |
| Senescence | Adults | ~118 | ~195 |
| Senescence | Pupae/Prepupae | ~118 | ~220 |
| Senescence | Adults | ~118 | ~200 |
| Senescence | Pupae/Prepupae | ~118 | ~230 |
| Emergence | Adults | ~118 | ~165 |
| Emergence | Pupae/Prepupae | ~118 | ~170 |
| Emergence | Adults | ~118 | ~165 |
| Emergence | Pupae/Prepupae | ~118 | ~195 |
| Peak | Adults | ~118 | ~176 |
| Peak | Pupae/Prepupae | ~118 | ~192 |
| Peak | Adults | ~118 | ~176 |
| Peak | Pupae/Prepupae | ~118 | ~205 |
| Senescence | Adults | ~118 | ~195 |
| Senescence | Pupae/Prepupae | ~118 | ~220 |
| Senescence | Adults | ~118 | ~200 |
| Senescence | Pupae/Prepupae | ~118 | ~230 |
| Emergence | Adults | ~118 | ~165 |
| Emergence | Pupae/Prepupae | ~118 | ~170 |
| Emergence | Adults | ~118 | ~165 |
| Emergence | Pupae/Prepupae | ~118 | ~195 |
| Peak | Adults | ~118 | ~176 |
| Peak | Pupae/Prepupae | ~118 | ~192 |
| Peak | Adults | ~118 | ~176 |
| Peak | Pupae/Prepupae | ~118 | ~205 |
| Senescence | Adults | ~118 | ~195 |
| Senescence | Pupae/Prepupae | ~118 | ~220 |
| Senescence | Adults | ~118 | ~200 |
| Senescence | Pupae/Prepupae | ~118 | ~230 |
| Emergence | Adults | ~118 | ~165 |
| Emergence | Pupae/Prepupae | ~118 | ~170 |
| Emergence | Adults | ~118 | ~165 |
| Emergence | Pupae/Prepupae | ~118 | ~195 |
| Peak | Adults | ~118 | ~176 |
| Peak | Pupae/Prepupae | ~118 | ~192 |
| Peak | Adults | ~118 | ~176 |
| Peak | Pupae/Prepupae | ~118 | ~205 |
| Senescence | Adults | ~118 | ~195 |
| Senescence | Pupae/Prepupae | ~118 | ~220 |
| Senescence | Adults | ~118 | ~200 |
| Senescence | Pupae/Prepupae | ~118 | ~230 |
| Emergence | Adults | ~118 | ~165 |
| Emergence | Pupae/Prepupae | ~118 | ~170 |
| Emergence | Adults | ~118 | ~165 |
| Emergence | Pupae/Prepupae | ~118 | ~195 |
| Peak | Adults | ~118 | ~176 |
| Peak | Pupae/Prepupae | ~118 | ~192 |
| Peak | Adults | ~118 | ~176 |
| Peak | Pupae/Prepupae | ~118 | ~205 |
| Senescence | Adults | ~118 | ~195 |
| Senescence | Pupae/Prepupae | ~118 | ~220 |
| Senescence | Adults | ~118 | ~200 |
| Senescence | Pupae/Prepupae | ~118 | ~230 |
| Emergence | Adults | ~118 | ~165 |
| Emergence | Pupae/Prepupae | ~118 | ~170 |
| Emergence | Adults | ~118 | ~165 |
| Emergence | Pupae/Prepupae | ~118 | ~195 |
| Peak | Adults | ~118 | ~176 |
| Peak | Pupae/Prepupae | ~118 | ~192 |
| Peak | Adults | ~118 | ~176 |
| Peak | Pupae/Prepupae | ~118 | ~205 |
| Senescence | Adults | ~118 | ~195 |
| Senescence | Pupae/Prepupae | ~118 | ~220 |
| Senescence | Adults | ~118 | ~200 |
| Senescence | Pupae/Prepupae | ~118 | ~230 |
| Emergence | Adults | ~118 | ~165 |
| Emergence | Pupae/Prepupae | ~118 | ~170 |
| Emergence | Adults | ~118 | ~165 |
| Emergence | Pupae/Prepupae | ~118 | ~195 |
| Peak | Adults | ~118 | ~176 |
| Peak | Pupae/Prepupae | ~118 | ~192 |
| Peak | Adults | ~118 | ~176 |
| Peak | Pupae/Prepupae | ~118 | ~205 |
| Senescence | Adults | ~118 | ~195 |
| Senescence | Pupae/Prepupae | ~118 | ~220 |
| Senescence | Adults | ~118 | ~200 |
| Senescence | Pupae/Prepupae | ~118 | ~230 |
| Emergence | Adults | ~118 | ~165 |
| Emergence | Pupae/Prepupae | ~118 | ~170 |
| Emergence | Adults | ~118 | ~165 |
| Emergence | Pupae/Prepupae | ~118 | ~195 |
| Peak | Adults | ~118 | ~176 |
| Peak | Pupae/Prepupae | ~118 | ~192 |
| Peak | Adults | ~118 | ~176 |
| Peak | Pupae/Prepupae | ~118 | ~205 |
| Senescence | Adults | ~118 | ~195 |
| Senescence | Pupae/Prepupae | ~118 | ~220 |
| Senescence | Adults | ~118 | ~200 |
| Senescence | Pupae/Prepupae | ~118 | ~230 |
| Emergence | Adults | ~118 | ~165 |
| Emergence | Pupae/Prepupae | ~118 | ~170 |
| Emergence | Adults | ~118 | ~165 |
| Emergence | Pupae/Prepupae | ~118 | ~195 |
| Peak | Adults | ~118 | ~176 |
| Peak | Pupae/Prepupae | ~118 | ~192 |
| Peak | Adults | ~118 | ~176 |
| Peak | Pupae/Prepupae | ~118 | ~205 |
| Senescence | Adults | ~118 | ~195 |
| Senescence | Pupae/Prepupae | ~118 | ~220 |
| Senescence | Adults | ~118 | ~200 |
| Senescence | Pupae/Prepupae | ~118 | ~230 |
| Emergence | Adults | ~118 | ~165 |
| Emergence | Pupae/Prepupae | ~118 | ~170 |
| Emergence | Adults | ~118 | ~165 |
| Emergence | Pupae/Prepupae | ~118 | ~195 |
| Peak | Adults | ~118 | ~176 |
| Peak | Pupae/Prepupae | ~118 | ~192 |
| Peak | Adults | ~118 | ~176 |
| Peak | Pupae/Prepupae | ~118 | ~205 |
| Senescence | Adults | ~118 | ~195 |
| Senescence | Pupae/Prepupae | ~118 | ~220 |
| Senescence | Adults | ~118 | ~200 |
| Senescence | Pupae/Prepupae | ~118 | ~230 |
| Emergence | Adults | ~118 | ~165 |
| Emergence | Pupae/Prepupae | ~118 | ~170 |
| Emergence | Adults | ~118 | ~165 |
| Emergence | Pupae/Prepupae | ~118 | ~195 |
| Peak | Adults | ~118 | ~176 |
| Peak | Pupae/Prepupae | ~118 | ~192 |
| Peak | Adults | ~118 | ~176 |
| Peak | Pupae/Prepupae | ~118 | ~205 |
| Senescence | Adults | ~118 | ~195 |
| Senescence | Pupae/Prepupae | ~118 | ~220 |
| Senescence | Adults | ~118 | ~200 |
| Senescence | Pupae/Prepupae | ~118 | ~230 |
| Emergence | Adults | ~118 | ~165 |
| Emergence | Pupae/Prepupae | ~118 | ~170 |
| Emergence | Adults | ~118 | ~165 |
| Emergence | Pupae/Prepupae | ~118 | ~195 |
| Peak | Adults | ~118 | ~176 |
| Peak | Pupae/Prepupae | ~118 | ~192 |
| Peak | Adults | ~118 | ~176 |
| Peak | Pupae/Prepupae | ~118 | ~205 |
| Senescence | Adults | ~118 | ~195 |
| Senescence | Pupae/Prepupae | ~118 | ~220 |
| Senescence | Adults | ~118 | ~200 |
| Senescence | Pupae/Prepupae | ~118 | ~230 |
| Emergence | Adults | ~118 | ~165 |
| Emergence | Pupae/Prepupae | ~118 | ~170 |
| Emergence | Adults | ~118 | ~165 |
| Emergence | Pupae/Prepupae | ~118 | ~195 |
| Peak | Adults | ~118 | ~176 |
| Peak | Pupae/Prepupae | ~118 | ~192 |
| Peak | Adults | ~118 | ~176 |
| Peak | Pupae/Prepupae | ~118 | ~205 |
| Senescence | Adults | ~118 | ~195 |
| Senescence | Pupae/Prepupae | ~118 | ~220 |
| Senescence | Adults | ~118 | ~200 |
| Senescence | Pupae/Prepupae | ~118 | ~230 |
| Emergence | Adults | ~118 | ~165 |
| Emergence | Pupae/Prepupae | ~118 | ~170 |
| Emergence | Adults | ~118 | ~165 |
| Emergence | Pupae/Prepupae | ~118 | ~195 |
| Peak | Adults | ~118 | ~176 |
| Peak | Pupae/Prepupae | ~118 | ~192 |
| Peak | Adults | ~118 | ~176 |
| Peak | Pupae/Prepupae | ~118 | ~205 |
| Senescence | Adults | ~118 | ~195 |
| Senescence | Pupae/Prepupae | ~118 | ~220 |
| Senescence | Adults | ~118 | ~200 |
| Senescence | Pupae/Prepupae | ~118 | ~230 |
| Emergence | Adults | ~118 | ~165 |
| Emergence | Pupae/Prepupae | ~118 | ~170 |
| Emergence | Adults | ~118 | ~165 |
| Emergence | Pupae/Prepupae | ~118 | ~195 |
| Peak | Adults | ~118 | ~176 |
| Peak | Pupae/Prepupae | ~118 | ~192 |
| Peak | Adults | ~118 | ~176 |
| Peak | Pupae/Prepupae | ~118 | ~205 |
| Senescence | Adults | ~118 | ~195 |
| Senescence | Pupae/Prepupae | ~118 | ~220 |
| Senescence | Adults | ~118 | ~200 |
| Senescence | Pupae/Prepupae | ~118 | ~230 |
| Emergence | Adults | ~118 | ~165 |
| Emergence | Pupae/Prepupae | ~118 | ~170 |
| Emergence | Adults | ~118 | ~165 |
| Emergence | Pupae/Prepupae | ~118 | ~195 |
| Peak | Adults | ~118 | ~176 |
| Peak | Pupae/Prepupae | ~118 | ~192 |
| Peak | Adults | ~118 | ~176 |
| Peak | Pupae/Prepupae | ~118 | ~205 |
| Senescence | Adults | ~118 | ~195 |
| Senescence | Pupae/Prepupae | ~118 | ~220 |
| Senescence | Adults | ~118 | ~200 |
| Senescence | Pupae/Prepupae | ~118 | ~230 |
| Emergence | Adults | ~118 | ~165 |
| Emergence | Pupae/Prepupae | ~118 | ~170 |
| Emergence | Adults | ~118 | ~165 |
| Emergence | Pupae/Prepupae | ~118 | ~195 |
| Peak | Adults | ~118 | ~176 |
| Peak | Pupae/Prepupae | ~118 | ~192 |
| Peak | Adults | ~118 | ~176 |
| Peak | Pupae/Prepupae | ~118 | ~205 |
| Senescence | Adults | ~118 | ~195 |
| Senescence | Pupae/Prepupae | ~118 | ~220 |
| Senescence | Adults | ~118 | ~200 |
| Senescence | Pupae/Prepupae | ~118 | ~230 |
| Emergence | Adults | ~118 | ~165 |
| Emergence | Pupae/Prepupae | ~118 | ~170 |
| Emergence | Adults | ~118 | ~165 |
| Emergence | Pupae/Prepupae | ~118 | ~195 |
| Peak | Adults | ~118 | ~176 |
| Peak | Pupae/Prepupae | ~118 | ~192 |
| Peak | Adults | ~118 | ~176 |
| Peak | Pupae/Prepupae | ~118 | ~205 |
| Senescence | Adults | ~118 | ~195 |
| Senescence | Pupae/Prepupae | ~118 | ~220 |
| Senescence | Adults | ~118 | ~200 |
| Senescence | Pupae/Prepupae | ~118 | ~230 |
| Emergence | Adults | ~118 | ~165 |
| Emergence | Pupae/Prepupae | ~118 | ~170 |
| Emergence | Adults | ~118 | ~165 |
| Emergence | Pupae/Prepupae | ~118 | ~195 |
| Peak | Adults | ~118 | ~176 |
| Peak | Pupae/Prepupae | ~118 | ~192 |
| Peak | Adults | ~118 | ~176 |
| Peak | Pupae/Prepupae | ~118 | ~205 |
| Senescence | Adults | ~118 | ~195 |
| Senescence | Pupae/Prepupae | ~118 | ~220 |
| Senescence | Adults | ~118 | ~200 |
| Senescence | Pupae/Prepupae | ~118 | ~230 |
| Emergence | Adults | ~118 | ~165 |

Figure 4 Bee species that nest above ground and those that overwinter as adults are more sensitive to variation in snowmelt timing than species that nest below ground and that overwinter as pupae or prepupae. The top three panels show predicted phenophase responses to snowmelt based on nesting location, and the bottom panels show the same based on overwintering stage. The slope of the lines represents the sensitivity of each phenophase to snowmelt timing. P-values are presented for the two significant differences in slope at the α = 0.01 level.

interaction between bee overwintering stage and snowmelt timing (Figure 4, bottom panel). Bees that overwinter as adults require less developmental time before emerging in the spring, so we expected their phenology to be more responsive to snowmelt timing. The finding that adult-overwintering bee species do not take advantage of this shorter developmental time suggests that there may not be a benefit to greater phenological sensitivity, or that other factors limit their sensitivity.

## Different drivers of emergence and senescence phenology

The effect of snowmelt timing on emergence was nearly 50% greater than it was on senescence, and the absolute effects of temperature and rainfall on emergence were nearly an order of magnitude higher than on senescence, indicating that the onset of foraging is timed by external cues, whereas the end is less dynamic. These results match plant phenology findings that showed a reduction in the effect of snowmelt timing on later phenophases (Wipf, 2010). Similarly, in butterflies, early phenophases have been shown to advance more frequently in response to recent climate change (Roy and Sparks, 2000). Summer temperature and rainfall span the entirety of the active bee foraging season and also had larger effects on emergence than on later phenophases (Figure 2, panel 1), indicating that the pattern of a greater climate influence on early phenology is not entirely a byproduct of spring-specific climate variables. Late season phenology may be less sensitive to climatic fall events such as the date of first frost because adult bees – particularly those that nest below ground – are insulated from cold nights in their nests.

Although the predictive power of our models was similar for all phenophases (Figure 3a), climate variables explained more variance for early phenophases, and traits explained more variance for later phenophases (Figure 3b, Supporting Information 3). The effect of snowmelt on senescence is diluted by inherent interspecific variation in foraging flight period. In other words, the effect of the phenological sequence becomes reduced in later phenophases (Figure S6). Some plants exhibit stronger climatic control of spring phenology (Menzel, 2003) but stronger genetic control of autumn phenology (Fracheboud et al., 2009), and our results hint at a similar pattern in bees. The drivers of senescence phenology in insects may be particularly complex due to variation in life-history strategies (Gallinat et al., 2015). For example univoltine insect species are expected to advance their fall senescence, whereas multivoltine species may delay the end of their active period by producing additional generations. Lastly, our finding that spring and fall phenophases are determined by different drivers’ points to the necessity of studying the whole phenological distributions rather than focusing on the onset of an active period.

## Climate change implications

Two of the main effects of climate change in montane regions are an advance of snowmelt timing and increased temperatures (Ogilvie et al., 2017). Bee phenology at the community level is tied to snowmelt but does not precisely track it, and phenophases exhibit different responses to climatic variation. As climate explained more variation and produced larger shifts in early phenophases (Figure 2b), we expect that

© 2020 John Wiley & Sons Ltd.

14610248, 2020, 11, Downloaded from https://onlinelibrary.wiley.com/doi/10.1111/ele.13583 by Faculdade Medicina De Lisboa, Wiley Online Library on [31/10/2025]. See the Terms and Conditions (https://onlinelibrary.wiley.com/terms-and-conditions) on Wiley Online Library for rules of use; OA articles are governed by the applicable Creative Commons License

<!-- page 8 of 10 -->

1596

M. Stemkovski et al.

Letter

emergence and peak timing in areas of the world with increasing temperatures and decreasing precipitation will shift at greater rates than senescence, extending the active flight period of adult solitary bees. This could lead to additional generations during the growing season (Altermatt, 2010), or potentially a developmental trap in which species produce a maladaptive second generation that is ill-prepared for autumn conditions (Van Dyck et al. 2015). An extended active bee foraging season may have positive pollination outcomes, allowing pollen-limited plants to reproduce for longer periods of time, though this effect may be tempered by phenological mismatches or declining populations (Hedhly et al., 2009; Vanbergen et al., 2013).

Given observed trends and projections for earlier snowmelt timing, it is relevant to compare variation in bee phenology to that of flowers. A 39-year study of flowering phenology at the RMBL documented that the date of first flowering has advanced by 0.89 - 0.083 days per day of snowmelt advance (Caradonna et al., 2014). The flowering community in this subalpine region shows two distinct peaks in total floral abundance (Aldridge et al., 2011) which have shifted at different rates (first peak: 0.74 - 0.056 days per day of snowmelt; second peak: $0 . 5 3 \pm 0 . 0 9 5 \mathrm { d a y s ) }$ . We found that bee emergence timing shifted by 0.49 - 0.11 days per day of snowmelt advance (peak 0.49 - 0.09 days, and senescence $0 . 2 8 \pm 0 . 1$ days). Thus, bee phenophases are potentially less sensitive than flowering phenophases to shifts in snowmelt timing, with bee emergence advancing at 55% the rate of first flowering, and bee peak advancing at 67% and 93% the rate of the two flower peaks. The discrepancy in the rates of shift of bee emergence and first flowering may be partially due to differences in the metric of onset, as first occurrence data may be biased and are inherently different from our measure of the first 5% of the foraging population (van Strien et al., 2008). We also note that the flower phenology study comprised a narrow elevation band at separate sites in the middle of the present study’s roughly 1000 m elevation transect, and patterns of phenological shift may vary across elevation. Nevertheless, this difference in the sensitivities of bee and flowering phenology indicates the potential for a community-wide mismatch in this plant–pollinator system due to climate change. While the ability of both bees and flowering plants to respond to climatic cues is a promising sign for future synchrony under climate warming, the difference in rates of shift suggests at least short-term mismatches, which may become chronic if the interacting species are not able to adapt or shift their ranges to match the rate of climate change (van Asch et al., 2007).

## CONCLUSIONS

Community-level bee phenology is shaped primarily by climatic cues, elevation, nest location, and overwintering stage. Early phenology is particularly sensitive to climatic variation, whereas later phenology is determined more by functional traits, suggesting that climate change will affect emergence more than senescence, potentially lengthening the active foraging period of bees. And while more long-term and specieslevel studies are needed, the present results suggest that the

responsiveness of bee phenology may lag behind that of flowers.

## ACKNOWLEDGEMENTS

W.D.P. and M.S. were funded by NSF ABI-1759965, NSF EF-1802605 and USDA Forest Service agreement 18-CS-11046000-041. M.S. was funded by the NSF Graduate Research Fellowship under Grant No. 1745048. Field work for this research was supported by NSF DEB-0922080 and DEB-1354104 to D.W.I, R.E.I. and B.D.I, and funds from NC State University to R.E.I. We thank the research assistants associated with the collection of the long-term bee data, and the RMBL and private land owners for access to field sites, billy barr for weather data and three anonymous reviewers whose comments greatly improved the paper. Any opinions, findings, conclusions or recommendations expressed in this material are those of the authors and do not necessarily reflect the views of the funding agencies.

## AUTHOR CONTRIBUTIONS

R.E.I., B.D.I. and D.W.I. designed research; M.S., S.R.G., G.L.P. and R.E.I. performed research; J.G., T.G., J.L.N., R.O., M.G.R., C.S.S. and K.W. provided taxonomic expertise; M.S. and W.D.P. analysed data; M.S. wrote the paper with feedback from all authors.

## PEER REVIEW

The peer review history for this article is available at [https://publons.com/publon/10.1111/ele.13583](https://publons.com/publon/10.1111/ele.13583).

## DATA ACCESSIBILITY STATEMENT

We are committed to public access to data for scientific reproducibility and transparency. Our data and code for analysis are freely available on Dryad (https://datadryad.org/stash/dataset/doi:10.5061/dryad.t76hdr7zc). The bee phenology monitoring project is ongoing, and more data have been added since this publication. The most up-to-date data are available through Open Science Framework ([https://osf.io/kmxyn/](https://osf.io/kmxyn/)).

## REFERENCES

- Aldridge, G., Inouye, D.W., Forrest, J.R.K., Barr, W.A. & Miller-Rushing, A.J. (2011). Emergence of a mid-season period of low floral resources in a montane meadow ecosystem associated with climate change. J. Ecol., 99, 905–913.
- Altermatt, F. (2010). Climatic warming increases voltinism in European butterflies and moths. Proc. R. Soc. B Biol. Sci., 277, 1281–1287.
- Bates, D., Machler, M., Bolker, B. & Walker, S. (2014). Fitting linear ¨ mixed-effects models using lme4. J. Stat. Software, 67, 1–48.
- Bartomeus, I., Ascher, J.S., Wagner, D., Danforth, B.N., Colla, S., Kornbluth, S. et al. (2011). Climate-associated phenological advances in bee pollinators and bee-pollinated plants. Proc. Natl Acad. Sci. USA, 108, 20645–20649.
- Bartomeus, I., Park, M.G., Gibbs, J., Danforth, B.N., Lakso, A.N. & Winfree, R. (2013). Biodiversity ensures plant-pollinator phenological synchrony against climate change. Ecol. Lett., 16, 1331–1338.

© 2020 John Wiley & Sons Ltd.

14610248, 2020, 11, Downloaded from https://onlinelibrary.wiley.com/doi/10.1111/ele.13583 by Faculdade Medicina De Lisboa, Wiley Online Library on [31/10/2025]. See the Terms and Conditions (https://onlinelibrary.wiley.com/terms-and-conditions) on Wiley Online Library for rules of use; OA articles are governed by the applicable Creative Commons License

<!-- page 9 of 10 -->

Letter

Drivers of bee phenology

1597

- Barton, K. (2015). Package ‘MuMIn’. Version, 1, 18.
- Bell, J.R., Alderson, L., Izera, D., Kruger, T., Parker, S., Pickup, J. et al. (2015). Long-term phenological trends, species accumulation rates, aphid traits and climate: Five decades of change in migrating aphids. J. Animal Ecol., 84, 21–34.
- Burnham, K.P. & Anderson, D.R. (1998). Practical use of the information-theoretic approach. Model selection and inference. Springer, New York, NY, pp. 75–117.
- Cade, B.S. (2015). Model averaging and muddled multimodel inferences. Ecology, 96, 2370–2382.
- Cane, J.H., Minckley, R.L. & Kervin, L.J. (2000). Sampling bees (Hymenoptera: Apiformes) for pollinator community studies: Pitfalls of pan-trapping. J. Kansas Entom. Soc., 73, 225–231.
- CaraDonna, P.J., Iler, A.M. & Inouye, D.W. (2014). Shifts in flowering phenology reshape a subalpine plant community. Proc. Natl Acad. Sci. USA, 111, 4916–4921.
- CaraDonna, P.J., Cunningham, J.L. & Iler, A.M. (2018). Experimental warming in the field delays phenology and reduces body mass, fat content and survival: Implications for the persistence of a pollinator under climate change. Funct. Ecol., 32, 2345–2356.
- Cohen, J.M., Lajeunesse, M.J. & Rohr, J.R. (2018). A global synthesis of animal phenological responses to climate change. Nat. Clim. Change, 8, 224–228.
- Danforth, B.N. (1999). Emergence dynamics and bet hedging in a desert bee, Perdita portalis. Proc. R. Soc. B Biol. Sci., 266, 1985–1994.
- Diamond, S., Frame, A., Martin, R. & Buckely, L. (2011). Species’ traits predict phenological responses to climate change in butterflies. Ecology, 92, 1005–1012.
- Donnelly, A., Caffarra, A. & O’Neill, B.F. (2011). A review of climatedriven mismatches between interdependent phenophases in terrestrial and aquatic ecosystems. Intl. J. Biometeorology, 55, 805–817.
- Ellwood, E.R., Diez, J.M., Ibánez, I., Primack, R.B., Kobori, H., Higuchi, H. ˜ et al. (2012). Disentangling the paradox of insect phenology: Are temporal trends reflecting the response to warming? Oecologia, 168, 1161–1171.
- Ettinger, A.K., Gee, S. & Wolkovich, E.M. (2018). Phenological sequences: how early-season events define those that follow. Am. J. Bot., 105, 1771–1780.
- Forrest, J.R. (2016). Complex responses of insect phenology to climate change. Curr. Op. Insect Sci., 17, 49–54.
- Forrest, J.R., Cross, R. & CaraDonna, P.J. (2019). Two-year bee, or not two-year bee? How voltinism is affected by temperature and season length in a high-elevation solitary bee. Am. Nat., 193, 560–574.
- Forrest, J.R.K. & Thomson, J.D. (2011). An examination of synchrony between insect emergence and flowering in Rocky Mountain meadows. Ecol. Monogr., 81, 469–491.
- Fracheboud, Y., Luquez, V., Bjork ¨ en, L., Sj ´ odin, A., Tuominen, H. & ¨ Jansson, S. (2009). The control of autumn senescence in European aspen. Plant Phys., 149, 1982–1991.
- Frund, J., Zieger, S.L. & Tscharntke, T. (2013). Response diversity of ¨ wild bees to overwintering temperatures. Oecologia, 173, 1639–1648.
- Gallinat, A.S., Primack, R.B. & Wagner, D.L. (2015). Autumn, the neglected season in climate change research. Trends Ecol. Evol., 30, 169–176.
- Galipaud, M., Gillingham, M.A.F., David, M & Dechaume-Moncharmont, F.X. (2014) Ecologists overestimate the importance of predictor variables in model averaging: a plea for cautious interpretations. Methods in Ecology and Evolution, 5(10), 983–991. [https://besjournals.onlinelibrary.wiley.com/doi/abs/10.1111/2041-210X.12251](https://besjournals.onlinelibrary.wiley.com/doi/abs/10.1111/2041-210X.12251).
- Gelman, A. (2008). Scaling regression inputs by dividing by two standard deviations. Stat. Med., 27, 2865–2873.
- Gelman, A. & Hill, J. (2006). Data analysis using regression and multilevel/ hierarchical models. Cambridge University Press, Cambridge, United Kingdom and New York, NY.
- Gezon, Z.J., Wyman, E.S., Ascher, J.S., Inouye, D.W. & Irwin, R.E. (2015). The effect of repeated, lethal sampling on wild bee abundance and diversity. Meth. Ecol. & Evol., 6, 1044–1054.

- Gibbs, J. (2010). Revision of the metallic species of Lasioglossum (Dialictus) in Canada (Hymenoptera, Halictidae, Halictini). Zootaxa, 2591, 1–382.
- Hedhly, A., Hormaza, J.I. & Herrero, M. (2009). Global warming and sexual plant reproduction. Trends Plant Sci., 14, 30–36.
- Hegland, S.J., Nielsen, A., Lazaro, A., Bjerknes, A.L. & Totland, Ø. ´ (2009). How does climate warming affect plant-pollinator interactions? Ecol. Lett., 12, 184–195.
- Inouye, B.D., Ehrlen, J. & Underwood, N. (2019). Phenology as a process ´ rather than an event: from individual reaction norms to community metrics. Ecol. Monogr., 89, 1–15.
- Inouye, D.W. (2008). Effects of climate change on phenology, frost damage, and floral abundance of montane wildflowers. Ecology, 89, 353–362.
- IPCC (2014) Climate Change 2014: Synthesis Report. Contribution of Working Groups I, II and III to the Fifth Assessment Report of the Intergovernmental Panel on Climate Change [Core Writing Team, R.K. Pachauri and L.A. Meyer (eds.)]. Cambridge University Press, Cambridge, United Kingdom and New York, NY.
- Kemp, W.P. & Bosch, J. (2005). Effect of temperature on Osmia lignaria (Hymenoptera: Megachilidae) prepupa – adult development, survival, and emergence. J. Econ. Entom., 98, 1917–1923.
- Kharouba, H.M., Ehrlen, J., Gelman, A., Bolmgren, K., Allen, J.M. & ´ Travers, S.E. (2018). Global shifts in the phenological synchrony of species interactions over recent decades. Proc. Natl Acad. Sci. USA, 115, 5211–5216.
- Klein, A.M., Vaissiere, B.E., Cane, J.H., Steffan-Dewenter, I., \` Cunningham, S.A., Kremen, C. et al. (2007). Importance of pollinators in changing landscapes for world crops. Proc. R. Soc. B Biol. Sci., 274, 303–313.
- Keenan, T.F. & Richardson, A.D. (2015). The timing of autumn senescence is affected by the timing of spring phenology: Implications for predictive models. Glob. Change Biol., 21, 2634–2641.
- Kehrberger, S. & Holzschuh, A. (2019). Warmer temperatures advance flowering in a spring plant more strongly than emergence of two solitary spring bee species. PLoS One, 14, 1–15.
- Konig, P., Tautenhahn, S., Cornelissen, J.H.C., Christine, R., Kattge, J. ¨ & Gerhard, B. (2018). Advances in flowering phenology across the Northern Hemisphere are explained by functional traits. Glob. Ecol. & Biogeography, 27, 310–321.
- Kudo, G. & Ida, T. (2013). Early onset of spring increases the phenological mismatch between plants and pollinators. Ecology, 94, 2311–2320.
- Kudo, G., Nishikawa, Y., Kasagi, T. & Kosuge, S. (2004). Does seed production of spring ephemerals decrease when spring comes early? Ecol. Res., 19, 255–259.
- Kuznetsova, A., Brockhoff, P.B. & Christensen, R.H.B. (2017). lmerTest Package: Tests in linear mixed effects models. J. Stat. Softw., 82, 1–26.
- LeBuhn, G., Griswold, T., Minckley, R., Droege, S., Cane, J. & Buchmann, S. (2003). A standardized method for monitoring bee populations – The Bee Inventory (BI) Plot.
- Linden, A. (2018). Adaptive and nonadaptive changes in phenological ´ synchrony. Proc. Natl Acad. Sci. USA, 115, 5057–5059.
- Menzel, A. (2003). Plant phenological anomalies in Germany and their relation to air temperature and NAO. Clim. Change, 57, 243–263.
- Michener, C.D. (2000). The Bees of the World. Johns Hopkins Press, Baltimore, MD.
- Michener, C.D., McGinley, R.J. & Danforth, B.N. (1994). The Bee Genera of North and Central America (Hymenoptera: Apoidea). Smithsonian Institution Press, Washington, D.C.
- Miller-Rushing, A.J., Inouye, D.W. & Primack, R.B. (2008). How well do first flowering dates measure plant responses to climate change? The effects of population size and sampling frequency. J. Ecol., 96, 1289–1296.
- Ogilvie, J.E., Griffin, S.R., Gezon, Z.J., Inouye, B.D., Underwood, N., Inouye, D.W. et al. (2017). Interannual bumble bee abundance is

© 2020 John Wiley & Sons Ltd.

14610248, 2020, 11, Downloaded from https://onlinelibrary.wiley.com/doi/10.1111/ele.13583 by Faculdade Medicina De Lisboa, Wiley Online Library on [31/10/2025]. See the Terms and Conditions (https://onlinelibrary.wiley.com/terms-and-conditions) on Wiley Online Library for rules of use; OA articles are governed by the applicable Creative Commons License

<!-- page 10 of 10 -->

1598

M. Stemkovski et al.

Letter

- driven by indirect climate effects on floral resource phenology. Ecol. Lett., 20, 1507–1515.
- Olliff-yang, R.L. & Mesler, M.R. (2018). The potential for phenological mismatch between a perennial herb and its ground-nesting bee pollinator. AoB Plants, 10, 1–11.
- Ovaskainen, O., Skorokhodova, S., Yakovleva, M., Sukhov, A., Kutenkov, A., Kutenkova, N. et al. (2013). Community-level phenological response to climate change. Proc. Natl Acad. Sci. USA, 110, 13434–13439.
- Parton, W. & Logan, J. (1981). A model for diurnal variation in soil and air temperature. Ag. Meteorology, 23, 205–216.
- Petanidou, T., Kallimanis, A.S., Sgardelis, S.P., Mazaris, A.D., Pantis, J.D. & Waser, N.M. (2014). Variable flowering phenology and pollinator use in a community suggest future phenological mismatch. Acta Oecologica, 59, 104–111.
- Parmesan, C. & Yohe, G. (2003). A globally coherent fingerprint of climate change impacts across natural systems. Nature, 421, 37–42.
- Pyke, G., Inouye, D.W. & Thomson, J. (2011). Activity and abundance of bumble bees near Crested Butte, Colorado: diel, seasonal, and elevation effects. Ecol. Entom., 36, 511–521.
- Rafferty, N.E., CaraDonna, P.J. & Bronstein, J.L. (2015). Phenological shifts and the fate of mutualisms. Oikos, 124, 14–21.
- Rafferty, N. & Ives, A.R. (2012). Pollinator effectiveness varies with experimental shifts in flowering time. Ecology, 93, 803–814.
- Renner, S.S. & Zohner, C.M. (2018). Climate change and phenological mismatch in trophic interactions among plants, insects, and vertebrates. Annu. Rev. Ecol. Evol. Sys., 49, 165–182.
- Roy, D.B. & Sparks, T.H. (2000). Phenology of British butterflies and climate change. Glob. Change Biol., 6, 407–416.
- Schenk, M., Krauss, J. & Holzschuh, A. (2018). Desynchronizations in bee – plant interactions cause severe fitness losses in solitary bees. J. Animal Ecol., 87, 139–149.
- Scott, V.L., Ascher, J.S., Griswold, T. & Nufio, C.R. (2011). The Bees of Colorado. University of Colorado Museum of Natural History, Boulder CO, Natural History Inventory of Colorado.
- Slominski, A.H. & Burkle, L.A. (2019). Solitary bee life history traits and sex mediate responses to manipulated seasonal temperatures and season length. Front. Ecol. Eviron., 7, 1–15.
- Stone, G.N. & Willmer, P.G. (1989). Warm-up rates and body temperatures in bees: The importance of body size, thermal regime and phylogeny. J. Exper. Biol., 147, 303–328.
- Thackeray, S.J., Henrys, P.A., Hemming, D., Bell, J.R., Botham, M.S., Burthe, S. et al. (2016). Phenological sensitivity to climate across taxa and trophic levels. Nature, 535, 241–245.

- Theobald, E., Breckheimer, I. & HilleRisLambers, J. (2017). Climate drives phenological reassembly of a mountain wild-flower meadow community. Ecology, 98, 2799–2812.
- Van Asch, M., van Tienderen, P.H., Holleman, L.J.M. & Visser, M.E. (2007). Predicting adaptation of phenology in response to climate change, an insect herbivore example. Glob. Change Biol., 13, 1596–1604.
- Van Dyck, H., Bonte, D., Puls, R., Gotthard, K. & Maes, D. (2015). The lost generation hypothesis: could climate change drive ectotherms into a developmental trap? Oikos, 124, 54–61.
- Van Strien, A.J., Plantenga, W.F., Soldaat, L.L., Van Swaay, C.A.M. & WallisDeVries, M.F. (2008). Bias in phenology assessments based on first appearance data of butterflies. Oecologia, 156, 227–235.
- Vanbergen, A.J., Garratt, M.P., Vanbergen, A.J., Baude, M., Biesmeijer, J.C., Britton, N.F. et al. (2013). Threats to an ecosystem service: Pressures on pollinators. Front. Ecol. Environ., 11, 251–259.
- Visser, M.E. & Gienapp, P. (2019). Evolutionary and demographic consequences of phenological mismatches. Nat. Ecol. & Evol., 12, 879–885.
- Warren, R.J. & Bradford, M.A. (2014). Mutualism fails when climate response differs between interacting species. Glob. Change Biol., 20, 466–474.
- White, J., Son, Y. & Park, Y.-L. (2009). Temperature-dependent emergence of Osmia cornifrons (Hymenoptera: Megachilidae) adults. J. Econ. Entomol., 102, 2026–2032.
- Wipf, S. (2010). Phenology, growth, and fecundity of eight subarctic tundra species in response to snowmelt manipulations. Plant Ecol., 207, 53–66.
- Wood, S.N. (2017). Generalized Additive Models: An introduction with R. Chapman and Hall/CRC, Boca Raton, FL.
- Wright, S.J., Kitajima, K., Kraft, N.J., Reich, P.B., Wright, I.J., Bunker, D.E. et al. (2010). Functional traits and the growth–mortality trade-off in tropical trees. Ecology, 91, 3664–3674.

## SUPPORTING INFORMATION

Additional supporting information may be found online in the Supporting Information section at the end of the article.

Editor, Tim Coulson

Manuscript received 8 June 2020

First decision made 1 July 2020

Manuscript accepted 8 July 2020

© 2020 John Wiley & Sons Ltd.

14610248, 2020, 11, Downloaded from https://onlinelibrary.wiley.com/doi/10.1111/ele.13583 by Faculdade Medicina De Lisboa, Wiley Online Library on [31/10/2025]. See the Terms and Conditions (https://onlinelibrary.wiley.com/terms-and-conditions) on Wiley Online Library for rules of use; OA articles are governed by the applicable Creative Commons License



<!-- ===== Complementary: Stemkovski2020_S1.docx.md ===== -->


<!-- page 1 of 1 -->

**Supplement 1: Climate, topography, and trait data gathering**

*Climate data*

We used data from a weather station at the RMBL operated by long-time resident, billy barr. We selected this data source because it was consistently collected throughout the duration of our study with no missing days, and because it provides a direct measure of snowmelt timing. In addition, this weather station was closer to the majority of our study sites than any other weather stations with data available.

For the climate variables, we made *a priori* selections of snowmelt date (first date of uncovered ground in a year), average monthly summer rainfall, and average monthly summer maximum temperature. We defined summer as the period between April 1 and September 30, the typical flight period for the bee community at the RMBL (Gezon et al. 2015). We did not include total snowfall or snow water content, because they were highly correlated with snowmelt date (*r=0.82* and *r=0.86*, respectively). We predicted that snowmelt date in particular would be a major driver of bee phenology, with earlier snowmelt driving earlier occurrences of all phenophases, because the persistent snowpack greatly limits the growing season in the study area and strongly affects flowering phenology (Inouye 2008) and bumble bee catch rates (Ogilvie et al., 2017). We calculated temperature and rainfall values over the entirety of the active bee season because bee foraging phenophases are distributed throughout the season. The flight periods of individual, univoltine species are thought to be short (just a few weeks), so many senescence events are expected to occur before many emergence events, and vice versa.

*Topographic data*

We assessed the effects of elevation and solar incidence on bee phenology. The elevation of our sites ranged from 2456 to 3438 meters above sea level (Table S2). Bee phenology has been shown to shift based on elevation in the study area (Pyke et al. 2011). Solar incidence was calculated as the hourly average angle to the sun from 0900 to 1800 on July 1 of each year using the *insol* R-package (Corripio 2014). We included this variable on the premise that sites with a more direct angle of incidence to the sun would experience warmer temperatures and receive more accumulated solar energy over the course of a season, which could advance some phenophases (Jackson 1966, Weiss et al. 1993, Allen et al. 2014). To calculate the degree of solar incidence, we obtained elevation, slope, and aspect data from a digital elevation map, and we verified slope and aspect data at each site using a clinometer and compass.

*Species trait data*

To examine the role of functional traits in determining bee phenology, we assessed the effect of body mass, nest location, and overwintering stage. We did not include sociality as a trait in the analysis because we specifically excluded the eusocial group *Bombus*, and some halcitids in our study system have been shown to exhibit variable solitary lifestyles at high elevations (Eickwort et al. 1996), while bees of the same species may be social at lower elevations. We calculated body mass by measuring intertegular distance (ITD) for up to ten individuals of each species and scaling the measurements according to an established ITD-to-mass relationship (Cane 1987). We chose body mass as a predictor because body mass has been shown to influence thermal tolerance (Stone & Willmer 1989). Thus, it may be that smaller bees have evolved more conservative phenologies (closer to the middle of the season) in order to avoid temperature extremes. We note that the present analysis is limited to smaller bodied bees due to the exclusion of *Bombus* from the analysis. We obtained nest location (above ground vs. below ground) and overwintering stage (adult vs. prepupae) for each species by compiling existing trait information from primary resources (Pardee 2018; Table S3).

**Supplement 2: Power analysis and method validation**

In order to validate the phenophase estimation method presented in this paper and to explore its performance, we conducted a power analysis using simulated data with known parameter values. We drew observations from a normal distribution to generate a simulated population time series. The mean was selected from a uniform distribution ranging from 50 to 200 days of the year, the standard deviation was varied by ten intervals from 7 to 50 days, and points were drawn every 14 days to mirror the actual bee monitoring protocol. These parameter values and sampling frequency were selected to reflect realistic ranges of bee abundance in our study system. The drawn values were rounded to the nearest one-day bin, and true peak timing, emergence, and senescence values were calculated as the maximum observed abundance, and the first and last days on which 5% of the maximum was observed, respectively. To test the efficacy of the phenophase estimation method at different re-sampling regimes, we added different levels of error to the observed values. The error terms were picked from a normal distribution centered at zero and with a standard deviation equal to the standard deviation of the simulated distribution multiplied by a scaling factor. We varied the scaling factor by ten intervals from 0 to 1. We then performed the GAM phenophase estimation method detailed previously on the sampled dataset to estimate phenophase values and generate confidence intervals (illustrated in Figure S1). We performed this procedure 500 times for each combination of standard deviation and error values, resulting in 50,000 total simulations. To test for the effectiveness of the method on skewed distributions, we repeated the above procedure with a skew-normal distribution, generated using the *sn* R-package (Azzalini 2020). For the skew-normal distribution, we varied the degree of skew from 0 to 1.5, applied error as before, and randomly selected the standard deviation for each data simulation.

The power of a statistical test is the probability of rejecting the null hypothesis when the alternative is true (Lehmann and Romano 2006). In the context of the present analysis, power is the proportion of simulations in which confidence intervals around phenophase estimates encompass the true phenophase value. At an α-criterion of 0.05, we would expect 80% of the true values to fall within the estimated confidence intervals. We found that the GAM phenophase estimation method consistently provided reliable estimates of the true phenophase values, though the power decreased as the proportion of added error increased (Figure S2). Power did not decrease as the standard deviation of the sampling distribution increased. As expected, the width of the confidence intervals increased as the proportion of added error and width of the sampling distribution increased. Additionally, we found that the power of the GAM method was higher when estimating peak timing, and the confidence intervals around the peak estimate were smaller than those for emergence and senescence timing across nearly all parameter combinations. This is to be expected, as values on the extremes of distributions are harder to estimate than those toward the center. When comparing actual and estimated phenophase values across all simulations with the proportion of error added < 0.5, the estimates accounted for 95% of the variation in emergence values, 99% for peak, and 83% for senescence. We detected slight bias in the phenophase estimates, with median error in actual versus estimated values being 3.8 days later for emergence, 2 days earlier for peak, and 1.7 days later earlier for senescence timing.

In summary, we found that the GAM method had high power when error rates were small, but gave reasonable estimates even when error was very high. The estimates generated by the method explained the vast majority of the variation in actual values, and the biases were small. We conclude that the GAM method adequately estimates actual phenophase timing within a set of parameters that is representative of the data within this study.

**Figure S1**. An illustration of the proposed phenophase estimation method on a simulated dataset where actual phenophase values are known. In this example, points (red filled circles) were drawn at an interval of 14 days from a distribution (black circles) centered at 170 with a standard deviation of 15, with no error added to the observations. The GAM method was applied to the observed time-series dataset, and phenophase estimates were made. These estimates (red lines) are plotted with confidence intervals (light red bars) and compared against actual phenophase values (black lines).

![Image block](doc:535e54f/tier:flash/page:1/block:14)

**Figure S2**. The phenophase estimation method effectively estimates the actual phenophase values regardless of the spread of the distribution, but is less able to make correct estimates as more error is added to observations. The power of the GAM method (left panels) decreases for each phenophase estimate as there is more error added to sampled points, but not as the standard deviation of the sample distribution increases. The width of the confidence intervals (right panels) increases as more error is added and as the standard deviation of the sample distribution increases.

![Image block](doc:535e54f/tier:flash/page:1/block:16)

**Figure S3.** The phenophase estimation method is effective at estimating phenophases of skewed distributions, though the power decreases as more error is added to observations. The width of the confidence intervals (right panels) increases as more error is added, and the confidence intervals around the long tail of the distribution (senescence) increase at higher levels of skew.

![Image block](doc:535e54f/tier:flash/page:1/block:18)

**Supplement 3: Additional statistical tests**

*Variance inflation factors*

Multicollinearity in predictor variables can lead to erroneous inference using standard linear modeling and model averaging techniques (Cade 2015). To avoid this issue, we examined correlations between all predictors before running models. This led us to exclude some variables such as snow depth and minimum temperature from our list of predictors. As a second step to ensure that our models did not suffer from multicollinearity, we calculated variance inflation factors (VIFs) for each of our top models using the vif function in the car R-package (Fox et al. 2012). We found that VIFs were all near one, with the highest value being 2.18 for temperature in the peak phenophase model. These VIF values were well below the threshold of VIF=5 in which highly correlated variables lead to problematic inference (James et al. 2013), so we concluded that our models did not suffer from mulitcollinearity.

*Additional interactions*

While we focused on the interactions of snowmelt timing with nest location and overwintering stage, we also tested for interactions between the other climatic variables (average summer maximum temperature and average summer rainfall) and the two functional traits. We found no significant nest location/rainfall or overwintering stage/temperature interactions for any phenophases. We did find a significant interaction between overwintering stage and rainfall but only for the peak phenophase, with species that overwinter as adults slightly advancing their peak with more rain and those that overwinter as prepupae delaying their peak (0.66 ± 0.25, t<sub>379</sub> = 2.669, p<0.01). We also found that the emergence and peak timing of species that nest above ground was more sensitive to temperature (emergence: 7.76 ± 2.88, t<sub>453</sub> = 2.694, p<0.01; peak: 8.87 ± 2.83, t<sub>379</sub> = 3.14, p<0.01), mirroring our earlier findings of a nest location/snowmelt interaction.

*Variance of random effects*

Another approach to look indirectly at the relative influence of climatic variation, topography, and functional traits on bee phenology is to fit a model without fixed effects that simply predicts phenophases on the basis of year, site, and species treated as random effects. This is represented as the model $DOY_{phase} \textasciitilde e_{year}+e_{site}+e_{species}$, where *e* represents a random effect, and *DOY*<em><sub>phase</sub></em> represents the estimated day-of-year of a phenophase. This results in three models, one for each of emergence, peak, and senescence. Upon fitting the model, we calculated the proportion of the variance attributed to each random effect by dividing the variance (the square of the standard deviation) by the sum of the variances of the other random effects including the residual variance. The raw variance values are given in Table S1, and the trends are summarized in Figure S4. We found that the variance attributed to years and sites was highest for emergence and decreased with later phenophases, while the variance attributed to species was highest for senescence. This supports our general finding that different bee phenophases are determined by different types of drivers, as well as the specific finding that climate more strongly influences emergence and functional traits more strongly influence senescence.

**Supplement 1-3 references**

Allen, J. M., Terres, M. A., Katsuki, T., Iwamoto, K., Kobori, H., Higuchi, H., … Silander, J. R. (2014). Modeling daily flowering probabilities: expected impact of climate change on Japanese cherry phenology. Glob. Change Biol., 20, 1251–1263.

Azzalini, M. A. (2020). sn: The Skew-Normal and Related Distributions Such as the Skew-t. R package version 1.6.1.

Cade, B. S. (2015). Model averaging and muddled multimodel inferences. Ecology, 96(9), 2370–2382

Cane, J. H. (1987). Estimation of bee size using intertegular span (Apoidea). J. Kansas Entom. Soc., 60, 145–147.

Corripio, J. G. (2014). insol: Solar radiation. R package version 1.2.

Eickwort, G. C., Eickwort, J. M., Gordon, J., & Eickwort, M. A. (1996). Solitary Behavior in a High-Altitude Population of the Social Sweat Bee *Halictus rubicundus* (Hymenoptera: Halictidae). Behav. Ecol. and Sociobio., 38, 227–233.

Fox, J., Weisberg, S., Adler, D., Bates, D., Baud-Bovy, G., Ellison, S., ... & Heiberger, R. (2012). Package ‘car’. Vienna: R Foundation for Statistical Computing.

Gezon, Z. J., Wyman, E. S., Ascher, J. S., Inouye, D. W., & Irwin, R. E. (2015). The effect of repeated, lethal sampling on wild bee abundance and diversity. Meth. Ecol. & Evol., 6, 1044–1054.

Inouye, D. W. (2008). Effects of climate change on phenology, frost damage, and floral abundance of montane wildflowers. Ecology, 89, 353–362.

Jackson, M. T. (1966). Effects of microclimate on spring flowering phenology. Ecology, 47, 407–415.

James, G., Witten, D., Hastie, T., & Tibshirani, R. (2013). An introduction to statistical learning. New York

Lehmann, E. L., & Romano, J. P. (2006). Testing statistical hypotheses. Springer Science & Business Media. New York, USA

Ogilvie, J. E., Griffin, S. R., Gezon, Z. J., Inouye, B. D., Underwood, N., Inouye, D. W., & Irwin, R. E. (2017). Interannual bumble bee abundance is driven by indirect climate effects on floral resource phenology. Ecol. Lett., 20, 1507–1515.

Pardee, G. (2018). Effects of climate change on plants, pollinators, and their interactions (doctoral dissertation). North Carolina State University, Raleigh, North Carolina.

Pyke, G., Inouye, D. W., & Thomson, J. (2011). Activity and abundance of bumble bees near Crested Butte, Colorado: diel, seasonal, and elevation effects. *Ecol. Entom.*, 36, 511–521.

Stone, G. N., & Willmer, P. G. (1989). Warm-up rates and body temperatures in bees: The importance of body size, thermal regime and phylogeny. J. Exper. Biol., 147, 303–328.

Weiss, S. B., Murphy, D. D., Ehrlich, P. R., & Metzler, C. F. (1993). Adult emergence phenology in checkerspot butterflies: The effects of macroclimate, topoclimate, and population history. Oecologia, 96, 261–270.

**Table S1**. The variance attributed to each random effect and residual variance.

| **Phenophase** | **Year variance** | **Site variance** | **Species variance** | **Residual variance** |
| --- | --- | --- | --- | --- |
| Emergence | 221.14 | 193.01 | 74.95 | 39.03 |
| Peak | 64.09 | 36.61 | 98.45 | 20.61 |
| Senescence | 21.77 | 46.24 | 170.66 | 42.46 |

**Figure S4**. The proportion of variance attributed to years and sites decreases across phenophases, while  it increases across phenophases for species. The proportional residual variance increases slightly across phenophases.

![Image block](doc:535e54f/tier:flash/page:1/block:47)

**Figure S5**. Model averaging did not bias our calculations of relative effect sizes. The coefficients derived from model averaging are highly correlated with those from the top model for each phenophase. The red lines represent one-to-one relationships, and all points fall very close to these lines.

![Image block](doc:535e54f/tier:flash/page:1/block:49)

**Figure S6**. Emergence significantly predicted later phenophases, with more variation explained in peak timing than in senescence timing.

![Image block](doc:535e54f/tier:flash/page:1/block:51)

**Table S2**. Information on the sites used in the analysis.

| **Site name** | **Elevation (m)** | **Latitude** | **Longitude** | **Aspect** | **Slope** |
| --- | --- | --- | --- | --- | --- |
| Almont Curve | 2456 | 38.66125 | -106.85152 | 168.69 | 10.825 |
| Almont | 2569 | 38.65622 | -106.86203 | 111.801 | 15.07 |
| CDOT | 2588 | 38.78257 | -106.87002 | 243.435 | 6.37937 |
| Lypps | 2639 | 38.74812 | -106.83269 | 263.66 | 6.45795 |
| Tuttle | 2877 | 38.954751 | -106.988704 | 243.435 | 3.1996 |
| Willey | 2884 | 38.955971 | -106.988482 | 261.87 | 5.05115 |
| Kettle Ponds | 2884 | 38.94435 | -106.97174 | 18.4349 | 2.26364 |
| Beaver | 2921 | 38.961597 | -106.993975 | 45 | 5.05115 |
| Seans | 2931 | 38.964099 | -106.992616 | 225 | 8.04947 |
| Rustlers | 2977 | 38.9885 | -107.00512 | 231.34 | 9.09464 |
| Davids | 2979 | 38.962124 | -106.986896 | 206.565 | 12.6044 |
| Gothic | 3001 | 38.963088 | -106.994866 | 71.565 | 11.18 |
| Little | 3061 | 38.96732 | -106.96885 | 135 | 8.04947 |
| Hill | 3069 | 38.96677 | -106.97009 | 123.69 | 19.827 |
| Copper | 3072 | 38.96896 | -106.96801 | 102.529 | 12.9794 |
| Snodgrass | 3224 | 38.92625 | -106.98172 | 118.74 | 23.8426 |
| Elko | 3230 | 39.01245 | -107.05279 | 45 | 1.01275 |
| Mexican Cut | 3438 | 39.02685 | -107.06513 | 51.3402 | 17.7528 |

**Table S3**. A list of the species, number of individuals, associated traits, number of individuals used in the analysis (#), and the number of phenophase estimates that we were able to make from the time-series data. Abbreviations are as follows: ITD is intertegular distance, Em. is emergence, and Sen. is senescence. Because there have not been species-levels trait studies on every species in the analysis, some nest location and overwintering stage traits have been inferred from other species in the same genera (marked with an \* in the references column). We also compared these trait values with those reported in papers summarizing traits by genus (Mitchell 1960, Mitchell 1962, Stephen et al. 1969, Michener 2007, Harmon-Threatt 2020).

<table><tr><td><p><strong>Family</strong></p></td><td><p><strong>Species</strong></p></td><td><p><strong>ITD (mm)</strong></p></td><td><p><strong>Nest loc.</strong></p></td><td><p><strong>Overw. stage</strong></p></td><td><p><strong>#</strong></p></td><td><p><strong>Em. points</strong></p></td><td><p><strong>Peak points</strong></p></td><td><p><strong>Sen. points</strong></p></td><td><p><strong>Reference</strong></p></td></tr><tr><td rowspan="10"><p>Andrenidae</p></td><td><p><em>Andrena algida</em></p><p>Smith 1853</p></td><td><p>1.91</p></td><td><p>below</p></td><td><p>adults</p></td><td><p>44</p></td><td><p>0</p></td><td><p>1</p></td><td><p>6</p></td><td><p>(LaBerge 1986)</p></td></tr><tr><td><p><em>Andrena lawrencei </em></p><p>Viereck &amp; Cockerell 1914</p></td><td><p>2.36</p></td><td><p>below</p></td><td><p>adults</p></td><td><p>20</p></td><td><p>0</p></td><td><p>0</p></td><td><p>1</p></td><td><p>(LaBerge and Ribble 1975)</p></td></tr><tr><td><p><em>Andrena nothocalaidis </em></p><p>Cockerell 1905</p></td><td><p>2.15</p></td><td><p>below</p></td><td><p>adults</p></td><td><p>5</p></td><td><p>0</p></td><td><p>0</p></td><td><p>1</p></td><td><p>(Thorp 1969; Cane &amp; Love 2016; Gezon et al. 2015)</p></td></tr><tr><td><p><em>Andrena transnigra </em></p><p>Viereck 1904</p></td><td><p>3.17</p></td><td><p>below</p></td><td><p>adults</p></td><td><p>19</p></td><td><p>0</p></td><td><p>0</p></td><td><p>5</p></td><td><p>(Bouseman and LaBerge 1978)</p></td></tr><tr><td><p><em>Calliopsis coloradensis </em></p><p>Cresson 1878</p></td><td><p>1.65</p></td><td><p>below</p></td><td><p>prepupae</p></td><td><p>4</p></td><td><p>2</p></td><td><p>1</p></td><td><p>1</p></td><td><p>(Mitchell 1960; Shinn 1967 Jackson 1966; Miliczky 1991; Sheffield et al. 2014)</p></td></tr><tr><td><p><em>Calliopsis teucrii </em></p><p>Cockerell 1899</p></td><td><p>1.41</p></td><td><p>below</p></td><td><p>prepupae</p></td><td><p>319</p></td><td><p>5</p></td><td><p>4</p></td><td><p>1</p></td><td><p>(Shinn 1967; Hefetz et al. 1982)</p></td></tr><tr><td><p><em>Panurginus cressoniellus</em></p><p>Cockerell 1898</p></td><td><p>1.3</p></td><td><p>below</p></td><td><p>prepupae</p></td><td><p>2269</p></td><td><p>29</p></td><td><p>48</p></td><td><p>29</p></td><td><p>(Stephen et al. 1969) *</p></td></tr><tr><td><p><em>Panurginus ineptus </em></p><p>Cockerell 1922</p></td><td><p>1.35</p></td><td><p>below</p></td><td><p>prepupae</p></td><td><p>946</p></td><td><p>36</p></td><td><p>38</p></td><td><p>37</p></td><td><p>(Gezon et al. 2015; Stephen et al. 1969) *</p></td></tr><tr><td><p><em>Pseudopanurgus bakeri </em></p><p>(Cockerell 1906)</p></td><td><p>1.12</p></td><td><p>below</p></td><td><p>prepupae</p></td><td><p>569</p></td><td><p>61</p></td><td><p>29</p></td><td><p>13</p></td><td><p>(Gezon et al. 2015; Stephen et al. 1969) *</p></td></tr><tr><td><p><em>Pseudopanurgus didirupa </em>(Cockerell 1908)</p></td><td><p>1.3</p></td><td><p>below</p></td><td><p>prepupae</p></td><td><p>102</p></td><td><p>19</p></td><td><p>6</p></td><td><p>3</p></td><td><p>(Gezon et al. 2015; Stephen et al. 1969) *</p></td></tr><tr><td rowspan="6"><p>Apidae</p></td><td><p><em>Anthophora terminalis </em></p><p>Cresson 1869</p></td><td><p>3.17</p></td><td><p>above</p></td><td><p>prepupae</p></td><td><p>10</p></td><td><p>3</p></td><td><p>3</p></td><td><p>1</p></td><td><p>(Medler 1964)</p></td></tr><tr><td><p><em>Ceratina neomexicana </em></p><p>Cockerell 1901</p></td><td><p>1.37</p></td><td><p>above</p></td><td><p>adults</p></td><td><p>67</p></td><td><p>1</p></td><td><p>3</p></td><td><p>5</p></td><td><p>(Michener 1936)</p></td></tr><tr><td><p><em>Melissodes confusus </em></p><p>Cresson 1878</p></td><td><p>3.01</p></td><td><p>below</p></td><td><p>prepupae</p></td><td><p>13</p></td><td><p>5</p></td><td><p>1</p></td><td><p>0</p></td><td><p>(LaBerge 1961; Clement 1973; Hurd et al. 1980)</p></td></tr><tr><td><p><em>Melissodes grindeliae </em></p><p>Cockerell 1898</p></td><td><p>2.72</p></td><td><p>below</p></td><td><p>prepupae</p></td><td><p>2</p></td><td><p>1</p></td><td><p>1</p></td><td><p>0</p></td><td><p>(LaBerge 1961; Clement 1973; Hurd et al. 1980)</p></td></tr><tr><td><p><em>Melissodes hymenoxidis </em></p><p>Cockerell 1906</p></td><td><p>3.11</p></td><td><p>below</p></td><td><p>prepupae</p></td><td><p>2</p></td><td><p>1</p></td><td><p>0</p></td><td><p>0</p></td><td><p>(LaBerge 1961; Clement 1973; Hurd et al. 1980)</p></td></tr><tr><td><p><em>Melissodes tristis </em></p><p>Cockerell 1894</p></td><td><p>3.07</p></td><td><p>below</p></td><td><p>prepupae</p></td><td><p>12</p></td><td><p>0</p></td><td><p>3</p></td><td><p>1</p></td><td><p>(LaBerge 1961; Clement 1973; Hurd et al. 1980)</p></td></tr><tr><td rowspan="6"><p>Colletidae</p></td><td><p><em>Colletes consors </em></p><p>Cresson 1868</p></td><td><p>2.19</p></td><td><p>below</p></td><td><p>adults</p></td><td><p>2</p></td><td><p>1</p></td><td><p>1</p></td><td><p>1</p></td><td><p>(Gezon et al. 2015; Sheffield et al. 2014) *</p></td></tr><tr><td><p><em>Colletes nigrifrons </em></p><p>Titus 1900</p></td><td><p>2.04</p></td><td><p>below</p></td><td><p>adults</p></td><td><p>38</p></td><td><p>6</p></td><td><p>8</p></td><td><p>5</p></td><td><p>(Gezon et al. 2015; Sheffield et al. 2014) *</p></td></tr><tr><td><p><em>Hylaeus annulatus </em></p><p>(L. 1758)</p></td><td><p>1.28</p></td><td><p>above</p></td><td><p>prepupae</p></td><td><p>353</p></td><td><p>34</p></td><td><p>14</p></td><td><p>6</p></td><td><p>(Gezon et al. 2015; Stephen et al. 1969) *</p></td></tr><tr><td><p><em>Hylaeus basalis </em></p><p>(Smith 1853)</p></td><td><p>1.85</p></td><td><p>above</p></td><td><p>prepupae</p></td><td><p>57</p></td><td><p>8</p></td><td><p>10</p></td><td><p>4</p></td><td><p>(Scott 1996)</p></td></tr><tr><td><p><em>Hylaeus modestus </em></p><p>Say 1837</p></td><td><p>1.38</p></td><td><p>above</p></td><td><p>prepupae</p></td><td><p>2</p></td><td><p>1</p></td><td><p>1</p></td><td><p>1</p></td><td><p>(Packer et al. 2007; Stephen et al. 1969)</p></td></tr><tr><td><p><em>Hylaeus rudbeckiae </em></p><p>(Cockerell &amp; Casad 1895)</p></td><td><p>0.97</p></td><td><p>above</p></td><td><p>prepupae</p></td><td><p>12</p></td><td><p>1</p></td><td><p>0</p></td><td><p>0</p></td><td><p>(Packer et al. 2007; Stephen et al. 1969)</p></td></tr><tr><td rowspan="23"><p>Halictidae</p></td><td><p><em>Agapostemon texanus </em></p><p>Cresson 1872</p></td><td><p>2.22</p></td><td><p>below</p></td><td><p>adults</p></td><td><p>170</p></td><td><p>3</p></td><td><p>1</p></td><td><p>0</p></td><td><p>(Roberts 1973a; Eickwort 1981)</p></td></tr><tr><td><p><em>Dufourea fimbriata ^</em></p><p>(Cresson 1878)</p></td><td><p>1.18</p></td><td><p>below</p></td><td><p>prepupae</p></td><td><p>50</p></td><td><p>8</p></td><td><p>7</p></td><td><p>3</p></td><td><p>Dumesh &amp; Sheffield 2012)</p></td></tr><tr><td><p><em>Dufourea harveyi ^</em></p><p>(Cockerell 1906)</p></td><td><p>1.18</p></td><td><p>below</p></td><td><p>prepupae</p></td><td><p>221</p></td><td><p>33</p></td><td><p>24</p></td><td><p>7</p></td><td><p>Dumesh &amp; Sheffield 2012)</p></td></tr><tr><td><p><em>Dufourea maura </em></p><p>(Cresson 1878)</p></td><td><p>1.73</p></td><td><p>below</p></td><td><p>prepupae</p></td><td><p>43</p></td><td><p>11</p></td><td><p>6</p></td><td><p>5</p></td><td><p>Dumesh &amp; Sheffield 2012)</p></td></tr><tr><td><p><em>Halictus confusus </em></p><p>Smith 1853</p></td><td><p>1.32</p></td><td><p>below</p></td><td><p>adults</p></td><td><p>38</p></td><td><p>2</p></td><td><p>1</p></td><td><p>1</p></td><td><p>(Dolphin 1971, 1978; Eickwort et al. 1996; Richards et al. 2010)</p></td></tr><tr><td><p><em>Halictus rubicundus </em></p><p>(Christ 1791)</p></td><td><p>1.87</p></td><td><p>below</p></td><td><p>adults</p></td><td><p>496</p></td><td><p>25</p></td><td><p>6</p></td><td><p>13</p></td><td><p>(Dolphin 1978)</p></td></tr><tr><td><p><em>Halictus tripartitus </em></p><p>Cockerell 1895</p></td><td><p>1.24</p></td><td><p>below</p></td><td><p>adults</p></td><td><p>231</p></td><td><p>2</p></td><td><p>8</p></td><td><p>7</p></td><td><p>(Dolphin 1978; Gezon et al. 2015; Roberts 1973b)</p></td></tr><tr><td><p><em>Halictus virgatellus </em></p><p>Cockerell 1901</p></td><td><p>1.44</p></td><td><p>below</p></td><td><p>adults</p></td><td><p>1722</p></td><td><p>10</p></td><td><p>19</p></td><td><p>26</p></td><td><p>(Gezon et al. 2015; Sheffield et al. 2014) *</p></td></tr><tr><td><p><em>Lasioglossum abundipunctum</em></p><p>Gibbs 2010</p></td><td><p>1.01</p></td><td><p>below</p></td><td><p>adults</p></td><td><p>136</p></td><td><p>3</p></td><td><p>3</p></td><td><p>9</p></td><td><p>(Gezon et al. 2015; Packer et al. 2007)</p></td></tr><tr><td><p><em>Lasioglossum ephialtum </em></p><p>Gibbs 2010</p></td><td><p>1.01</p></td><td><p>below</p></td><td><p>adults</p></td><td><p>4</p></td><td><p>1</p></td><td><p>1</p></td><td><p>1</p></td><td><p>(Gibbs, 2010)</p></td></tr><tr><td><p><em>Lasioglossum inconditum</em></p><p>(Cockerell 1916)</p></td><td><p>1.25</p></td><td><p>below</p></td><td><p>adults</p></td><td><p>980</p></td><td><p>6</p></td><td><p>3</p></td><td><p>45</p></td><td><p>(Gibbs et al. 2013)</p></td></tr><tr><td><p><em>Lasioglossum nigrum </em></p><p>(Viereck 1903)</p></td><td><p>1.28</p></td><td><p>below</p></td><td><p>adults</p></td><td><p>1865</p></td><td><p>4</p></td><td><p>6</p></td><td><p>40</p></td><td><p>(Packer et al. 2007)</p></td></tr><tr><td><p><em>Lasioglossum obnubilum</em></p><p>(Sandhouse 1924)</p></td><td><p>0.89</p></td><td><p>below</p></td><td><p>adults</p></td><td><p>167</p></td><td><p>5</p></td><td><p>4</p></td><td><p>5</p></td><td><p>(Gibbs 2010; Packer et al. 2007)</p></td></tr><tr><td><p><em>Lasioglossum occidentale</em></p><p>(Crawford 1902)</p></td><td><p>0.96</p></td><td><p>below</p></td><td><p>adults</p></td><td><p>46</p></td><td><p>3</p></td><td><p>5</p></td><td><p>4</p></td><td><p>(Packer et al. 2007)</p></td></tr><tr><td><p><em>Lasioglossum pacatum</em></p><p>(Sandhouse 1924)</p></td><td><p>1.12</p></td><td><p>below</p></td><td><p>adults</p></td><td><p>643</p></td><td><p>0</p></td><td><p>1</p></td><td><p>4</p></td><td><p>(Gibbs 2010; Packer et al. 2007)</p></td></tr><tr><td><p><em>Lasioglossum pavoninum </em></p><p>(Ellis 1913)</p></td><td><p>1.06</p></td><td><p>below</p></td><td><p>adults</p></td><td><p>51</p></td><td><p>3</p></td><td><p>2</p></td><td><p>3</p></td><td><p>(Gibbs 2010; Packer et al. 2007)</p></td></tr><tr><td><p><em>Lasioglossum prasinogaster </em></p><p>Gibbs 2010</p></td><td><p>1.14</p></td><td><p>below</p></td><td><p>adults</p></td><td><p>806</p></td><td><p>0</p></td><td><p>2</p></td><td><p>5</p></td><td><p>(Packer et al. 2007)</p></td></tr><tr><td><p><em>Lasioglossum ruidosense</em></p><p>(Cockerell 1897)</p></td><td><p>1.05</p></td><td><p>below</p></td><td><p>adults</p></td><td><p>1273</p></td><td><p>8</p></td><td><p>8</p></td><td><p>27</p></td><td><p>(Gibbs 2010; Packer et al. 2007)</p></td></tr><tr><td><p><em>Lasioglossum sandhousiellum</em></p><p>Gibbs 2010</p></td><td><p>1.08</p></td><td><p>below</p></td><td><p>adults</p></td><td><p>85</p></td><td><p>13</p></td><td><p>1</p></td><td><p>1</p></td><td><p>(Gibbs 2010; Packer et al. 2007)</p></td></tr><tr><td><p><em>Lasioglossum sedi </em></p><p>(Sandhouse 1924)</p></td><td><p>0.99</p></td><td><p>below</p></td><td><p>adults</p></td><td><p>6161</p></td><td><p>4</p></td><td><p>11</p></td><td><p>63</p></td><td><p>(Packer et al. 2007)</p></td></tr><tr><td><p><em>Lasioglossum semicaeruleum</em></p><p>(Cockerell 1895)</p></td><td><p>1.03</p></td><td><p>below</p></td><td><p>adults</p></td><td><p>41</p></td><td><p>3</p></td><td><p>5</p></td><td><p>2</p></td><td><p>(Gibbs 2010; Packer et al. 2007)</p></td></tr><tr><td><p><em>Lasioglossum tenax </em></p><p>(Sandhouse 1924)</p></td><td><p>1.06</p></td><td><p>below</p></td><td><p>adults</p></td><td><p>343</p></td><td><p>5</p></td><td><p>1</p></td><td><p>16</p></td><td><p>(Packer 1994)</p></td></tr><tr><td><p><em>Lasioglossum trizonatum </em></p><p>(Cresson 1874)</p></td><td><p>2.3</p></td><td><p>below</p></td><td><p>adults</p></td><td><p>359</p></td><td><p>2</p></td><td><p>0</p></td><td><p>13</p></td><td><p>(McGinley 1986)</p></td></tr><tr><td rowspan="22"><p>Megachilidae</p></td><td><p><em>Dianthidium heterulkei </em></p><p>Schwarz 1940</p></td><td><p>2.08</p></td><td><p>above</p></td><td><p>prepupae</p></td><td><p>49</p></td><td><p>7</p></td><td><p>3</p></td><td><p>0</p></td><td><p>(Krombein 1967; Clement 1976)</p></td></tr><tr><td><p><em>Hoplitis albifrons </em></p><p>(Kirby 1837)</p></td><td><p>2.43</p></td><td><p>above</p></td><td><p>prepupae</p></td><td><p>13</p></td><td><p>3</p></td><td><p>2</p></td><td><p>1</p></td><td><p>(Fye 1965)</p></td></tr><tr><td><p><em>Hoplitis fulgida </em></p><p>(Cresson 1864)</p></td><td><p>2.04</p></td><td><p>above</p></td><td><p>prepupae</p></td><td><p>88</p></td><td><p>9</p></td><td><p>12</p></td><td><p>4</p></td><td><p>(Tepedino &amp; Parker 1984)</p></td></tr><tr><td><p><em>Hoplitis robusta </em></p><p>(Nylander 1848)</p></td><td><p>1.39</p></td><td><p>above</p></td><td><p>prepupae</p></td><td><p>156</p></td><td><p>23</p></td><td><p>21</p></td><td><p>14</p></td><td><p>(Clement &amp; Rust 1975; Müller &amp; Richter 2018; Müller &amp; Mauss 2016)</p></td></tr><tr><td><p><em>Megachile frigida </em></p><p>Smith 1853</p></td><td><p>3.64</p></td><td><p>above</p></td><td><p>prepupae</p></td><td><p>7</p></td><td><p>2</p></td><td><p>1</p></td><td><p>0</p></td><td><p>(Hobbs &amp; Lilly 1954; Pengelly 1955; Stephen 1956; Jenkins &amp; Matthews 2004)</p></td></tr><tr><td><p><em>Megachile inermis </em></p><p>Provancher 1888</p></td><td><p>4.43</p></td><td><p>above</p></td><td><p>prepupae</p></td><td><p>4</p></td><td><p>1</p></td><td><p>1</p></td><td><p>0</p></td><td><p>(Stephen 1956; Medler 1958; Sheffield et al. 2008)</p></td></tr><tr><td><p><em>Megachile melanophaea </em></p><p>Smith 1853</p></td><td><p>3.26</p></td><td><p>below</p></td><td><p>prepupae</p></td><td><p>22</p></td><td><p>8</p></td><td><p>4</p></td><td><p>3</p></td><td><p>(Hobbs &amp; Lilly 1954; Pengelly 1955)</p></td></tr><tr><td><p><em>Megachile montivaga </em></p><p>Cresson 1878</p></td><td><p>2.61</p></td><td><p>above</p></td><td><p>prepupae</p></td><td><p>15</p></td><td><p>3</p></td><td><p>3</p></td><td><p>2</p></td><td><p>(Hicks 1926; Hobbs &amp; Lilly 1954; Baker et al. 1985)</p></td></tr><tr><td><p><em>Megachile perihirta </em></p><p>Cockerell 1898</p></td><td><p>3.53</p></td><td><p>below</p></td><td><p>prepupae</p></td><td><p>9</p></td><td><p>2</p></td><td><p>1</p></td><td><p>1</p></td><td><p>(Sladen 1918; Hicks 1926; Hobbs &amp; Lilly 1954; Bohart 1957)</p></td></tr><tr><td><p><em>Megachile pugnata </em></p><p>Say 1837</p></td><td><p>3.1</p></td><td><p>above</p></td><td><p>prepupae</p></td><td><p>1</p></td><td><p>1</p></td><td><p>0</p></td><td><p>0</p></td><td><p>(Medler 1964; Hobbs &amp; Lilly 1954; Sheffield et al. 2008)</p></td></tr><tr><td><p><em>Megachile relativa </em></p><p>Cresson 1878</p></td><td><p>2.47</p></td><td><p>above</p></td><td><p>prepupae</p></td><td><p>18</p></td><td><p>6</p></td><td><p>5</p></td><td><p>2</p></td><td><p>(Medler &amp; Koerber 1958; Sheffield et al. 2008)</p></td></tr><tr><td><p><em>Osmia albolateralis </em></p><p>Cockerell 1906</p></td><td><p>2.23</p></td><td><p>above</p></td><td><p>adults</p></td><td><p>56</p></td><td><p>5</p></td><td><p>7</p></td><td><p>4</p></td><td><p>(Rightmyer et al. 2013)</p></td></tr><tr><td><p><em>Osmia brevis </em></p><p>Cresson 1864</p></td><td><p>2.3</p></td><td><p>above</p></td><td><p>adults</p></td><td><p>21</p></td><td><p>2</p></td><td><p>2</p></td><td><p>2</p></td><td><p>(Baker et al. 1985; Cane 2014)</p></td></tr><tr><td><p><em>Osmia bruneri </em></p><p>Cockerell 1897</p></td><td><p>2.1</p></td><td><p>above</p></td><td><p>adults</p></td><td><p>5</p></td><td><p>0</p></td><td><p>0</p></td><td><p>1</p></td><td><p>(Baker et al. 1985; Cane et al. 2007; Frohlich 1983)</p></td></tr><tr><td><p><em>Osmia bucephala </em></p><p>Cresson 1864</p></td><td><p>3.76</p></td><td><p>above</p></td><td><p>adults</p></td><td><p>93</p></td><td><p>3</p></td><td><p>8</p></td><td><p>13</p></td><td><p>(Rightmyer et al. 2013) *</p></td></tr><tr><td><p><em>Osmia inermis </em></p><p>(Zetterstedi 1838)</p></td><td><p>2.35</p></td><td><p>above</p></td><td><p>adults</p></td><td><p>5</p></td><td><p>0</p></td><td><p>0</p></td><td><p>1</p></td><td><p>(Müller 2018; Sheffield et al. 2014)</p></td></tr><tr><td><p><em>Osmia longula </em></p><p>Cresson 1864</p></td><td><p>3.2</p></td><td><p>above</p></td><td><p>adults</p></td><td><p>6</p></td><td><p>1</p></td><td><p>1</p></td><td><p>2</p></td><td><p>(Cane et al. 2007; Rightmyer et al. 2013)</p></td></tr><tr><td><p><em>Osmia phaceliae </em></p><p>Cockerell 1907</p></td><td><p>1.78</p></td><td><p>above</p></td><td><p>adults</p></td><td><p>8</p></td><td><p>1</p></td><td><p>1</p></td><td><p>1</p></td><td><p>(Packer et al. 2007) *</p></td></tr><tr><td><p><em>Osmia sculleni </em></p><p>Sandhouse 18939</p></td><td><p>2.32</p></td><td><p>above</p></td><td><p>adults</p></td><td><p>3</p></td><td><p>0</p></td><td><p>1</p></td><td><p>1</p></td><td><p>(Cane et al. 2007; Sheffield et al. 2014) *</p></td></tr><tr><td><p><em>Osmia simillima </em></p><p>Smith 1853</p></td><td><p>2.53</p></td><td><p>above</p></td><td><p>adults</p></td><td><p>105</p></td><td><p>7</p></td><td><p>6</p></td><td><p>13</p></td><td><p>(Cane et al. 2007; Sheffield et al. 2014) *</p></td></tr><tr><td><p><em>Osmia tersula </em></p><p>Cockerell 1912</p></td><td><p>2.31</p></td><td><p>above</p></td><td><p>adults</p></td><td><p>6</p></td><td><p>1</p></td><td><p>2</p></td><td><p>2</p></td><td><p>(Cane et al. 2007; Sheffield et al. 2008)</p></td></tr><tr><td><p><em>Osmia “torchioi”</em></p><p>Griswold ms. name</p></td><td><p>1.82</p></td><td><p>above</p></td><td><p>adults</p></td><td><p>12</p></td><td><p>0</p></td><td><p>1</p></td><td><p>1</p></td><td><p>(Gezon et al., 2015)</p></td></tr></table>

*^ Dufourea harveyi* and *Dufourea fimbriata* may be synonymous in some parts of their range, but we found clear morphological differences between specimens in these groups in the present study area.

**Table S3 references**

Baker, J. R., Kuhn, E. D., & Bambara, S. B. (1985). Nests and immature stages of leafcutter bees (Hymenoptera: Megachilidae). *Journal of the Kansas Entomological Society*, 58, 290–313.

Bohart, G. E. (1957). Pollination of alfalfa and red clover. Annual Review of Entomology, 2(1), 355-380.

Bouseman, J. K., LaBerge, W. E. 1978. A revision of the bees of the genus Andrena of the Western Hemisphere. Part IX. Subgenus Melandrena. Transactions of the American Entomological Society 104: 275-390

Butler Jr, G. D. (1965). *Distribution and host plants of leaf-cutter bees in Arizona*. College of Agriculture, University of Arizona, Tucson, AZ.

Cane, J. H. (2014). The oligolectic bee *Osmia brevis* sonicates *Penstemon* flowers for pollen: a newly documented behavior for the Megachilidae. *Apidologie*, 45, 678–684.

Cane, J. H., Griswold, T., & Parker, F. D. (2007). Substrates and materials used for nesting by North American *Osmia* bees (Hymenoptera: Apiformes: Megachilidae). *Annals of the Entomological Society of America*, 100, 350–358.

Cane, J. H., & Love, B. (2016). Floral guilds of bees in sagebrush steppe: comparing bee usage of wildflowers available for postfire restoration. *Natural Areas Journal*, 36, 377–391.

Clement, S. L. (1973). The nesting biology of *Melissodes* (*Eumelissodes*) *rustica* (Say), with a description of the larva (Hymenoptera: Anthophoridae). *Journal of the Kansas Entomological Society*, 46, 516–525.

Clement, S.L. 1976. The biology of *Dianthidium heterulkei heterulkei* Schwarz, with a description of the larva (Hymenoptera, Megachilidae). Wasmann Journal of Biology 34: 9–22.

Clement SL, Rust RW (1975) The biology of Hoplitis robusta (Hymenoptera: Megachilidae). Entomological News 86(5/6): 115-120.

Dolphin, R. E. (1971, January). Observations of *Halictus confusus* Smith (Hymenoptera: Halictidae) on Woodland and Field Flowers. *Proceedings of the Indiana Academy of Science,* 81, 182-186.

Dolphin, R. E. (1978). Associates of the native bee, *Halictus* (Seladonia) *confusus* Smith (Hymenoptera: Halictidae). *Proceedings of the Indiana Academy of Science*, 88, 228–234.

Dumesh, S., & Sheffield, C. S. (2012). Bees of the genus *Dufourea* Lepeletier (Hymenoptera: Halictidae: Rophitinae) of Canada. *Canadian Journal of Arthropod Identification*, 20, 1–36.

Eickwort, G. C., Eickwort, M., Gordon, J., & Eickwort, M. A. (1996). Solitary behavior in a high-altitude population of the social sweat bee *Halictus rubicundus* (Hymenoptera: Halictidae). *Behavioral Ecology and Sociobiology*, 38, 227–233.

Fye, R. E. (1965). Biology of Apoidea taken in trap nests in northwestern Ontario (Hymenoptera). The Canadian Entomologist, 97(8), 863-877.

Frohlich, D. R. (1983). On the nesting biology of *Osmia* (Chenosmia) *bruneri* (Hymenoptera: Megachilidae). *Journal of the Kansas Entomological Society*, 56, 123–130.

Gezon, Z. J., Wyman, E. S., Ascher, J. S., Inouye, D. W., & Irwin, R. E. (2015). The effect of repeated, lethal sampling on wild bee abundance and diversity. *Methods in Ecology and Evolution*, 6, 1044–1054.

Gibbs, J. (2010). Revision of the metallic species of *Lasioglossum* (*Dialictus*) in Canada (Hymenoptera, Halictidae, Halictini). *Zootaxa*, 259, 1–382.

Gibbs, J., Ascher, J. S., Rightmyer, M. G., & Isaacs, R. (2017). The bees of Michigan (Hymenoptera: Apoidea: Anthophila), with notes on distribution, taxonomy, pollination, and natural history. *Zootaxa*, 4352, 1–160.

Gibbs, J., Packer, L., Dumesh, S., & Danforth, B. N. (2013). Revision and reclassification of *Lasioglossum (Evylaeus)*, *L. (Hemihalictus)* and *L. (Sphecodogastra)* in eastern North America (Hymenoptera: Apoidea: Halictidae). *Zootaxa*, 3672, 1–116.

Harmon-Threatt, A. (2020). Influence of Nesting Characteristics on Health of Wild Bee Communities. Annual Review of Entomology, 65, 39-56.

Hefetz, A., Eickwort, G. C., Blum, M. S., Cane, J., & Bohart, G. E. (1982). A comparative study of the exocrine products of cleptoparasitic bees (*Holcopasites*) and their hosts (*Calliopsis*) (Hymenoptera: Anthophoridae, Andrendae). *Journal of Chemical Ecology*, 8, 1389–1397.

Hicks, C. H. (1926). Nesting habits and parasites of certain bees of Boulder County, Colorado. University of Colorado Studies, 15, 217.

Hobbs, G. A. (1956). Ecology of the leaf-cutter bee *Megachile perihirta* Ckll. (Hymenoptera: Megachilidae) in relation to production of alfalfa seed. *The Canadian Entomoloigst*, 3414, 625–631.

Hobbs, G. A., & Lilly, C. E. (1954). Ecology of Species of *Megachile* Latreille in the mixed prairie region of southern Alberta with special reference to pollination of alfalfa. *Ecology*, 35, 453–462.

Hurd, P. D., Laberge, W. E., & Linsley, E. G. (1980). *Principal sunflower bees of North America with emphasis on the southwestern United States (Hymenoptera: Apoidea)*. Smithsonian Institution Press, Washington,  D.C.

Jackson, R. C. (1966). Some intersectional hybrids and relationships in *Haplopappus*. *The University of Kansas Science Bulletin*, 475–485.

James, R. R., & Pitts-Singer, T. L. (2008). Bee Pollination in Agricultural Ecosystems (pp. 219–222). Oxford University Press, New York, NY.

Jenkins, D. A., & Matthews, R. W. (2004). Cavity-nesting Hymenoptera in disturbed habitats of Georgia and South Carolina: nest architecture and seasonal occurrence. *Journal of the Kansas Entomological Society*, 77, 203–214.

Krombein, K. V. (1967). Trap-nesting wasps and bees: life histories and nest associates. Smithsonian, Washington, D. C.

LaBerge, W. E. (1986). The zoogeography of *Andrena* Fabricius (Hymenoptera: Andrenidae) of the Western Hemisphere. *Proceedings of the Ninth North American Prairie Conference*, 110, 110–115.

LaBerge, W. E., Ribble, D. W. 1975. A revision of the bees of the genus Andrena of the Western Hemisphere. Part VII. Subgenus Euandrena. Transactions of the American Entomological Society 101: 371-446.

Levin, M. D. (1966). Biological notes on *Osmia lignaria* and *Osmia californica* (Hymenoptera: Apoidea, Megachilidae). *Journal of the Kansas Entomological Society*, 39, 524–535.

McGinley, R. J. (1986). Studies of *Halictinae* (Apoidea: Halictidae), I: revision of new world *Lasioglossum* curtis. Smithsonian contributions to zoology.

Medler, J. T. (1964). *Anthophora (Clisodon) terminalis* Cresson in trap-nests in Wisconsin (Hymenoptera: Anthophoridae). *The Canadian Entomoloigst*, 96, 1332–1336.

Medler, J. T., & Koerber, T. W. (1958). Biology of *Megachile relativa* Cresson (Hymenoptera, Megachilidae) in trap-nests in Wisconsin. *Annals of the Entomological Society of America*, 51, 337–344.

Melander, A. L. (1902). The nesting habits of *Anthidium*. *Biological Bulletin*, 3, 27–32.

Michener, C. D. (1936). Western bees of the genus *Ceratina*, subgenus *Zaodontomerus*. American Museum Novitates, 844, 2–13.

Miliczky, E. (1991). Observations on the nesting biology of three species of p*anurgine* bees (Hymenoptera: Andrenidae). *Journal of the Kansas Entomological Society*, 64, 80–87.

Miliczky, E. (2008). Observations on the nesting biology of *Andrena (Plastandrena) prunorum* Cockerell in Washington State (Hymenoptera: Andrenidae). *Journal of the Kansas Entomological Society*, 81, 110–121.

Mitchell, T.B. 1960 Bees of the Eastern United States. North Carolina Agricultural Experiment Station Technical Bulletin No. 141.

Mitchell, T. B. (1962). Bees of the eastern United States. II Technical bulletin. North Carolina Agricultural Experiment Station, 152, 1-557.

Müller, A. (2018). Pollen host selection by predominantly alpine bee species of the genera *Andrena*, *Panurginus*, *Dufourea*, *Megachile*, *Hoplitis* and *Osmia* (Hymenoptera, Apoidea). *Alpine Entomology*, 2, 101–113.

Müller A, Richter H (2018). Dual function of *Potentilla* (Rosaceae) in the life history of the rare boreoalpine osmiine bee *Hoplitis* (Formicapis) *robusta* (Hymenoptera, Megachilidae). *Alpine Entomology* 2: 139–147.

Müller A, Mauss V (2016) Palaearctic *Hoplitis* bees of the subgenera *Formicapis* and *Tkalcua* (Megachilidae, Osmiini): biology, taxonomy and key to species. Zootaxa 4127(1): 105-120. http://dx.doi.org/10.11646/zootaxa.4127.1.5

Packer, L. (1994). *Lasioglossum (Dialictus) tenax* (Sandhouse) (Hymenoptera: Halictidae) as a solitary sweat bee. *Insect Society*, 41, 309–313.

Packer, L., Genaro, J. A., & Sheffield, C. S. (2007). The bee genera of Eastern Canada. *Canadian Journal of Arthropod Identification*, 3, 1–32.

Pengelly, D. H. (1955). The biology of bees of the genus *Megachile* with special reference to their importance in alfalfa seed production in southern Ontario. Cornell University Press.

Pesenko, Y.A., and Y.V. Astafurova. 2006. Contributions to the Halictidae fauna of the Eastern Palaearctic Region: subfamily Rophitinae (Hymenoptera: Halictidae). Entomofauna 27: 317-356.

Richards, M. H., Vickruck, J. L., & Rehan, S. M. (2010). Colony social organisation of *Halictus confusus* in southern Ontario, with comments on sociality in the subgenus *H. (Seladonia)*. Journal of Hymenoptera Research, 19(1), 144-158.

Rightmyer, M. G., Griswold, T., & Brady, S. G. (2013). Phylogeny and systematics of the bee genus *Osmia* (Hymenoptera: Megachilidae) with emphasis on North American *Melanosmia*: subgenera, synonymies and nesting biology revisited. *Systematic Entomology*, 38, 561–576.

Roberts, R. B. (1973a). Bees of Northwestern America: *Agapostemon*. *Oregon State University Agricultural Experiment Station*, 125, 1–23.

Roberts, R. B. (1973b). Bees of Northwestern America: *Halictus*. Oregon State University Agricultural Experiment Station, 1–23.

Scott, V. (1996). Pollen selection by three species of *Hylaeus* in Michigan (Hymenoptera: Colletidae). *Journal of the Kansas Entomological Society*, 69, 195–200.

Sheffield, C. S. (2008). Summer bees for spring crops? Potential problems with *Megachile rotundata* (Fab.)(Hymenoptera: Megachilidae) as a pollinator of lowbush blueberry (Ericaceae). Journal of the Kansas Entomological Society, 81(3), 276-287.

Sheffield, C. S., Frier, D., & Dumesh, S. (2014). The bees (Hymenoptera: Apoidea, Apiformes) of the prairies ecozone with comparisons to other grasslands of Canada. *Arthropods of Canadian Grasslands,* 4, 427–467.

Sladen, F. W. L. (1918). Pollination of alfalfa by bees of the genus *Megachile*. Table of Canadian species of the *latimanus* group. The Canadian Entomologist, 50(9), 301-304.

Stephen, W. P., Bohart, G. E., & Torchio, P. F. (1969). The biology and external morphology of bees with a synopsis of the genera of North-Western America. Oregon State University Agricultural Experiment Station, 1–146.

Tepedino, V. J., & Frohlich, D. R. (1982). Mortality factors, pollen utilization, and sex ratio in *Megachile pugnata* Say (Hymenoptera: Megachilidae), a candidate for commercial sunflower pollination. *Journal of the New York Entomological Society*, 90, 269–274.

Tepedino, V. J., & Parker, F. D. (1984). Nest selection, mortality and sex ratio in *Hoplitis fulgida* (Cresson) (Hymenoptera: Megachilidae). *Journal of the Kansas Entomological Society*, 57, 181–189.

Thorp, R. W. 1969. Systematics and ecology of bees of the subgenus Diandrena (Hymenoptera: Andrenidae). University of California Publications in Entomology 52: 1-146.

**Table S4**. Coefficients for species-specific shifts in phenophases in response to snowmelt timing (Figure 1). The three phenophases (emergence, peak, senescence) are separated by commas.

| **Species** | **Slope** | **SE** | ***t*** |
| --- | --- | --- | --- |
| *Dufourea harveyi* | 0.22, 0.18, NA | 0.32, 0.30, NA | 0.68, 0.59, NA |
| *Halictus rubicundus* | 0.42, NA, 0.13 | 0.46, NA, 0.57 | 0.42, NA, 0.22 |
| *Halictus virgatellus* | -0.01, -0.09, 1.45 | 1.12, 0.39, 0.66 | -0.21,-0.68, 2.01 |
| *Hoplitis fulgida* | 0.86, 0.83, NA | 0.63, 0.39, NA | 1.02, 1.68, NA |
| *Hoplitis robusta* | 0.52, 0.84, 0.5 | 0.61, 0.42, 0.9 | 0.48, 1.59, 0.41 |
| *Hylaeus annulatus* | 0.65, 0.5, NA | 0.38, 0.35, NA | 1.13, 0.92, NA |
| *Lasioglossum sedi* | NA, 0.8, -0.14 | NA, 0.51, 0.59 | NA, 1.22, -0.45 |
| *Panurginus cressoniellus* | 0.56, 0.29, 0.71 | 0.46, 0.36, 0.74 | 0.74, 0.31, 0.79 |
| *Panurginus ineptus* | -0.07, 0.09, 0.19, | 0.47, 0.35, 0.66 | -0.62, -0.24, 0.1 |
| *Pseudopanurgus bakeri* | 0.53, 0.09, -0.25 | 0.39, 0.37, 0.73 | 0.79, -0.24,-0.52 |

**Table S5**. Coefficients of standardized effect sizes from the full model of bee phenology (Figure 2). The three phenophases (emergence, peak, senescence) are separated by commas. Significant effects at the α=0.05 level are bold, but all effects were determined to be important by the model averaging protocol.

| **Predictor** | **Slope** | **SE** | ***z*** | ***P*** |
| --- | --- | --- | --- | --- |
| Snowmelt date | **11.52**, **12.82**, **7.81** | 2.68, 2.42, 2.44 | 4.28, 5.26, 3.19 | &lt;0.01, &lt;0.01, &lt;0.01 |
| Summer rainfall | **10.04**, 2.73, -1.85 | 2.12, 2.06, 2.12 | 4.72, 1.32, 0.87 | &lt;0.01, 0.19, 0.38 |
| Maximum temperature | **-7.34**, 1.40, -0.90 | 2.41, 2.22, 2.47 | 3.04, 0.63, 0.36 | &lt;0.01, 0.53, 0.72 |
| Elevation | **13.57**, **7.76**, -5.92 | 3.23, 3.65, 4.05 | 4.15, 2.12, 1.46 | &lt;0.01, 0.03, 0.15 |
| Solar Incidence | -6.13, -1.68, 4.03 | 3.40, 3.27, 4.04 | 1.80, 0.56, 1.00 | 0.07, 0.57, 0.32 |
| Body Mass | 2.08, -2.58, -2.79 | 3.23, 3.26, 3.57 | 0.64, 0.79, 0.78 | 0.54, 0.43, 0.43 |
| Nest Location (below ground) | **11.21**, -4.57, **-9.82** | 4.30, 3.84, 4.29 | 2.60, 1.19, 2.28 | &lt;0.01, 0.24, 0.02 |
| Overwintering stage (prepupae) | 1.91, **11.20**, **20.91** | 3.52, 3.23, 3.59 | 0.54, 3.45, 5.81 | 0.59, &lt;0.01, &lt;0.01 |

**Table S6**. Marginal and conditional R<sup>2</sup> values for the three phenology top models, as well as the proportion of variance explained by subsetted climate and trait models (Figure 3).

<table><tr><td><p><strong>Model</strong></p></td><td><p><strong>Phenophase</strong></p></td><td><p><strong>Marginal R<sup>2</sup></strong></p></td><td><p><strong>Conditional R<sup>2</sup></strong></p></td><td><p><strong>Proportion of marginal variance explained</strong></p></td></tr><tr><td rowspan="3"><p>Full model</p></td><td><p>Emergence</p></td><td><p>0.49</p></td><td><p>0.86</p></td><td rowspan="3"></td></tr><tr><td><p>Peak</p></td><td><p>0.40</p></td><td><p> 0.89</p></td></tr><tr><td><p>Senescence</p></td><td><p>0.45</p></td><td><p>0.84</p></td></tr><tr><td rowspan="3"><p>Climate only</p></td><td><p>Emergence</p></td><td><p>0.26</p></td><td><p> 0.85</p></td><td><p>0.53</p></td></tr><tr><td><p>Peak</p></td><td><p>0.16</p></td><td><p>0.88</p></td><td><p>0.41</p></td></tr><tr><td><p>Senescence</p></td><td><p>0.07</p></td><td><p>0.84</p></td><td><p>0.16</p></td></tr><tr><td rowspan="3"><p>Traits only</p></td><td><p>Emergence</p></td><td><p>0.11</p></td><td><p>0.79</p></td><td><p>0.22</p></td></tr><tr><td><p>Peak</p></td><td><p>0.22</p></td><td><p>0.85</p></td><td><p>0.55</p></td></tr><tr><td><p>Senescence</p></td><td><p>0.43</p></td><td><p>0.82</p></td><td><p>0.95</p></td></tr></table>