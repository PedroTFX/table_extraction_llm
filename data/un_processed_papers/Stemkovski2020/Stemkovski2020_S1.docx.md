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