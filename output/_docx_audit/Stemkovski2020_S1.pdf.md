## Supplement 1: Climate, topography, and trait data gathering

## Climate data

We used data from a weather station at the RMBL operated by long-time resident, billy barr. We selected this data source because it was consistently collected throughout the duration of our study with no missing days, and because it provides a direct measure of snowmelt timing. In addition, this weather station was closer to the majority of our study sites than any other weather stations with data available.

For the climate variables, we made a priori selections of snowmelt date (first date of uncovered ground in a year), average monthly summer rainfall, and average monthly summer maximum temperature. We defined summer as the period between April 1 and September 30, the typical flight period for the bee community at the RMBL (Gezon et al. 2015). We did not include total snowfall or snow water content, because they were highly correlated with snowmelt date $\scriptstyle ( r = 0 . 8 2$ and $r { = } 0 . 8 6 ,$ , respectively). We predicted that snowmelt date in particular would be a major driver of bee phenology, with earlier snowmelt driving earlier occurrences of all phenophases, because the persistent snowpack greatly limits the growing season in the study area and strongly affects flowering phenology (Inouye 2008) and bumble bee catch rates (Ogilvie et al., 2017). We calculated temperature and rainfall values over the entirety of the active bee season because bee foraging phenophases are distributed throughout the season. The flight periods of individual, univoltine species are thought to be short (just a few weeks), so many senescence events are expected to occur before many emergence events, and vice versa.

## Topographic data

We assessed the effects of elevation and solar incidence on bee phenology. The elevation of our sites ranged from 2456 to 3438 meters above sea level (Table S2). Bee phenology has been shown to shift based on elevation in the study area (Pyke et al. 2011). Solar incidence was calculated as the hourly average angle to the sun from 0900 to 1800 on July 1 of each year using the insol R-package (Corripio 2014). We included this variable on the premise that sites with a more direct angle of incidence to the sun would experience warmer temperatures and receive more accumulated solar energy over the course of a season, which could advance some phenophases (Jackson 1966, Weiss et al. 1993, Allen et al.

2014). To calculate the degree of solar incidence, we obtained elevation, slope, and aspect data from a digital elevation map, and we verified slope and aspect data at each site using a clinometer and compass.

## Species trait data

To examine the role of functional traits in determining bee phenology, we assessed the effect of body mass, nest location, and overwintering stage. We did not include sociality as a trait in the analysis because we specifically excluded the eusocial group Bombus, and some halcitids in our study system have been shown to exhibit variable solitary lifestyles at high elevations (Eickwort et al. 1996), while bees of the same species may be social at lower elevations. We calculated body mass by measuring intertegular distance (ITD) for up to ten individuals of each species and scaling the measurements according to an established ITD-to-mass relationship (Cane 1987). We chose body mass as a predictor because body mass has been shown to influence thermal tolerance (Stone & Willmer 1989). Thus, it may be that smaller bees have evolved more conservative phenologies (closer to the middle of the season) in order to avoid temperature extremes. We note that the present analysis is limited to smaller bodied bees due to the exclusion of Bombus from the analysis. We obtained nest location (above ground vs. below ground) and overwintering stage (adult vs. prepupae) for each species by compiling existing trait information from primary resources (Pardee 2018; Table S3).

## Supplement 2: Power analysis and method validation

In order to validate the phenophase estimation method presented in this paper and to explore its performance, we conducted a power analysis using simulated data with known parameter values. We drew observations from a normal distribution to generate a simulated population time series. The mean was selected from a uniform distribution ranging from 50 to 200 days of the year, the standard deviation was varied by ten intervals from 7 to 50 days, and points were drawn every 14 days to mirror the actual bee monitoring protocol. These parameter values and sampling frequency were selected to reflect realistic ranges of bee abundance in our study system. The drawn values were rounded to the nearest one-day bin, and true peak timing, emergence, and senescence values were calculated as the maximum observed abundance, and the first and last days on which 5% of the maximum was observed, respectively. To test the efficacy of the phenophase estimation method at different re-sampling regimes, we added different levels of error to the observed values. The error terms were picked from a normal distribution centered at zero and with a standard deviation equal to the standard deviation of the simulated distribution multiplied by a scaling factor. We varied the scaling factor by ten intervals from 0 to 1. We then performed the GAM phenophase estimation method detailed previously on the sampled dataset to estimate phenophase values and generate confidence intervals (illustrated in Figure S1). We performed this procedure 500 times for each combination of standard deviation and error values, resulting in 50,000 total simulations. To test for the effectiveness of the method on skewed distributions, we repeated the above procedure with a skew-normal distribution, generated using the sn R-package (Azzalini 2020). For the skew-normal distribution, we varied the degree of skew from 0 to 1.5, applied error as before, and randomly selected the standard deviation for each data simulation.

The power of a statistical test is the probability of rejecting the null hypothesis when the alternative is true (Lehmann and Romano 2006). In the context of the present analysis, power is the proportion of simulations in which confidence intervals around phenophase estimates encompass the true phenophase value. At an α-criterion of 0.05, we would expect 80% of the true values to fall within the estimated confidence intervals. We found that the GAM phenophase estimation method consistently provided reliable estimates of the true phenophase values, though the power decreased as the proportion of added error increased (Figure S2). Power did not decrease as the standard deviation of the sampling distribution increased. As expected, the width of the confidence intervals increased as the proportion of added error and width of the sampling distribution increased. Additionally, we found that the power of the GAM method was higher when estimating peak timing, and the confidence intervals around the peak estimate were smaller than those for emergence and senescence timing across nearly all parameter combinations. This is to be expected, as values on the extremes of distributions are harder to estimate than those toward the center. When comparing actual and estimated phenophase values across all simulations with the proportion of error added < 0.5, the estimates accounted for 95% of the variation in emergence values, 99% for peak, and 83% for senescence. We detected slight bias in the phenophase estimates, with median error in actual versus estimated values being 3.8 days later for emergence, 2 days earlier for peak, and 1.7 days later earlier for senescence timing.

In summary, we found that the GAM method had high power when error rates were small, but gave reasonable estimates even when error was very high. The estimates generated by the method explained the vast majority of the variation in actual values, and the biases were small. We conclude that the GAM method adequately estimates actual phenophase timing within a set of parameters that is representative of the data within this study.

Figure S1. An illustration of the proposed phenophase estimation method on a simulated dataset where actual phenophase values are known. In this example, points (red filled circles) were drawn at an interval of 14 days from a distribution (black circles) centered at 170 with a standard deviation of 15, with no error added to the observations. The GAM method was applied to the observed time-series dataset, and phenophase estimates were made. These estimates (red lines) are plotted with confidence intervals (light red bars) and compared against actual phenophase values (black lines).

![](images/c452050d6ad32b3d7d88a82f7b544a35451a05a871d1353ecfcc7ae4c0a0892d.jpg)

Figure S2. The phenophase estimation method effectively estimates the actual phenophase values1 regardless of the spread of the distribution, but is less able to make correct estimates as more error is2 3 added to observations. The power of the GAM method (left panels) decreases for each phenophase 4 estimate as there is more error added to sampled points, but not as the standard deviation of the sample 5 distribution increases. The width of the confidence intervals (right panels) increases as more error is 6 added and as the standard deviation of the sample distribution increases.

![](images/81d806b48bc31c8c1e28c79645d5acf2e710c3f1c7d83cd0524b3a32a9d2ce2f.jpg)

Figure S3. The phenophase estimation method is effective at estimating phenophases of skewed1 distributions, though the power decreases as more error is added to observations. The width of the2 confidence intervals (right panels) increases as more error is added, and the confidence intervals around3 the long tail of the distribution (senescence) increase at higher levels of skew.

![](images/bc3d3013d62220687842c51da56cd280ee3e07d695c2cc4c0f8500a0e01ccac2.jpg)

## Supplement 3: Additional statistical tests

Variance inflation factors

Multicollinearity in predictor variables can lead to erroneous inference using standard linear modeling and model averaging techniques (Cade 2015). To avoid this issue, we examined correlations between all predictors before running models. This led us to exclude some variables such as snow depth and minimum temperature from our list of predictors. As a second step to ensure that our models did not suffer from multicollinearity, we calculated variance inflation factors (VIFs) for each of our top models using the vif function in the car R-package (Fox et al. 2012). We found that VIFs were all near one, with the highest value being 2.18 for temperature in the peak phenophase model. These VIF values were well below the threshold of VIF=5 in which highly correlated variables lead to problematic inference (James et al. 2013), so we concluded that our models did not suffer from mulitcollinearity.

## Additional interactions

While we focused on the interactions of snowmelt timing with nest location and overwintering stage, we also tested for interactions between the other climatic variables (average summer maximum temperature and average summer rainfall) and the two functional traits. We found no significant nest location/rainfall or overwintering stage/temperature interactions for any phenophases. We did find a significant interaction between overwintering stage and rainfall but only for the peak phenophase, with species that overwinter as adults slightly advancing their peak with more rain and those that overwinter as prepupae delaying their peak $( 0 . 6 6 \pm 0 . 2 5 , \mathrm { t } _ { 3 7 9 } = 2 . 6 6 9 , \mathrm { p } { < } 0 . 0 1 )$ . We also found that the emergence and peak timing of species that nest above ground was more sensitive to temperature (emergence: 7.76 ± 2.88, $_ { \mathrm { t } _ { 4 5 3 } } = 2 . 6 9 4$ $\mathrm { p } { < } 0 . 0 1$ ; peak: $8 . 8 7 \pm 2 . 8 3 $ , t<sub>379</sub> = 3.14, p<0.01), mirroring our earlier findings of a nest location/snowmelt interaction.

## Variance of random effects

Another approach to look indirectly at the relative influence of climatic variation, topography, and functional traits on bee phenology is to fit a model without fixed effects that simply predicts

phenophases on the basis of year, site, and species treated as random effects. This is represented as the model $D O Y _ { \it \ p h a s e } \sim e _ { \it y e a r } + e _ { \it s i t e } + e _ { \it s p e c i e s } ,$ where e represents a random effect, and $D O Y _ { p h a s e }$ represents the estimated day-of-year of a phenophase. This results in three models, one for each of emergence, peak, and senescence. Upon fitting the model, we calculated the proportion of the variance attributed to each random effect by dividing the variance (the square of the standard deviation) by the sum of the variances of the other random effects including the residual variance. The raw variance values are given in Table S1, and the trends are summarized in Figure S4. We found that the variance attributed to years and sites was highest for emergence and decreased with later phenophases, while the variance attributed to species was highest for senescence. This supports our general finding that different bee phenophases are determined by different types of drivers, as well as the specific finding that climate more strongly influences emergence and functional traits more strongly influence senescence.

## Supplement 1-3 references

Allen, J. M., Terres, M. A., Katsuki, T., Iwamoto, K., Kobori, H., Higuchi, H., … Silander, J. R. (2014). Modeling daily flowering probabilities: expected impact of climate change on Japanese cherry phenology. Glob. Change Biol., 20, 1251–1263.

Azzalini, M. A. (2020). sn: The Skew-Normal and Related Distributions Such as the Skew-t. R package version 1.6.1.

Cade, B. S. (2015). Model averaging and muddled multimodel inferences. Ecology, 96(9), 2370–2382

Cane, J. H. (1987). Estimation of bee size using intertegular span (Apoidea). J. Kansas Entom. Soc., 60, 145–147.

Corripio, J. G. (2014). insol: Solar radiation. R package version 1.2.

Eickwort, G. C., Eickwort, J. M., Gordon, J., & Eickwort, M. A. (1996). Solitary Behavior in a High-Altitude Population of the Social Sweat Bee Halictus rubicundus (Hymenoptera: Halictidae). Behav. Ecol. and Sociobio., 38, 227–233.

Fox, J., Weisberg, S., Adler, D., Bates, D., Baud-Bovy, G., Ellison, S., ... & Heiberger, R. (2012). Package ‘car’. Vienna: R Foundation for Statistical Computing.

Gezon, Z. J., Wyman, E. S., Ascher, J. S., Inouye, D. W., & Irwin, R. E. (2015). The effect of repeated, lethal sampling on wild bee abundance and diversity. Meth. Ecol. & Evol., 6, 1044–1054.

Inouye, D. W. (2008). Effects of climate change on phenology, frost damage, and floral abundance of1 2 montane wildflowers. Ecology, 89, 353–362.

Jackson, M. T. (1966). Effects of microclimate on spring flowering phenology. Ecology, 47, 407–415.3

James, G., Witten, D., Hastie, T., & Tibshirani, R. (2013). An introduction to statistical learning. New4 5 York

Lehmann, E. L., & Romano, J. P. (2006). Testing statistical hypotheses. Springer Science & Business6 7 Media. New York, USA

Ogilvie, J. E., Griffin, S. R., Gezon, Z. J., Inouye, B. D., Underwood, N., Inouye, D. W., & Irwin, R. E. (2017). Interannual bumble bee abundance is driven by indirect climate effects on floral resource phenology. Ecol. Lett., 20, 1507–1515.

Pardee, G. (2018). Effects of climate change on plants, pollinators, and their interactions (doctoral dissertation). North Carolina State University, Raleigh, North Carolina.

Pyke, G., Inouye, D. W., & Thomson, J. (2011). Activity and abundance of bumble bees near Crested Butte, Colorado: diel, seasonal, and elevation effects. Ecol. Entom., 36, 511–521.

Stone, G. N., & Willmer, P. G. (1989). Warm-up rates and body temperatures in bees: The importance of body size, thermal regime and phylogeny. J. Exper. Biol., 147, 303–328.

Weiss, S. B., Murphy, D. D., Ehrlich, P. R., & Metzler, C. F. (1993). Adult emergence phenology in checkerspot butterflies: The effects of macroclimate, topoclimate, and population history. Oecologia, 96, 261–270.

Table S1. The variance attributed to each random effect and residual variance.1

<table><tr><td>Phenophase</td><td>Year variance</td><td>Site variance</td><td>Species variance</td><td>Residual variance</td></tr><tr><td>Emergence</td><td>221.14</td><td>193.01</td><td>74.95</td><td>39.03</td></tr><tr><td>Peak</td><td>64.09</td><td>36.61</td><td>98.45</td><td>20.61</td></tr><tr><td>Senescence</td><td>21.77</td><td>46.24</td><td>170.66</td><td>42.46</td></tr></table>

Figure S4. The proportion of variance attributed to years and sites decreases across phenophases, while1 it increases across phenophases for species. The proportional residual variance increases slightly across2 phenophases.3

![](images/592ccf1b14e49c50923ce0e62c31ee49c0c2073b5f05f5c0562e4aa639c62396.jpg)

Figure S5. Model averaging did not bias our calculations of relative effect sizes. The coefficients1 derived from model averaging are highly correlated with those from the top model for each2 phenophase. The red lines represent one-to-one relationships, and all points fall very close to these3 4 lines.

![](images/fc3de0fe71be2c67bece9560257d4abbe9128eb7786ecb7920a7efceebe5173b.jpg)

![](images/1f7664242daefff7018f47a628dce6c2510bb38ec40f4bbe38e2eadca61ef571.jpg)

![](images/67f853ae01a83b7e9799d55d175357f16f0a2c19a9726ee772b1398bd4fcc2d0.jpg)

Figure S6. Emergence significantly predicted later phenophases, with more variation explained in peak1 timing than in senescence timing.2

![](images/71054dc7fca7d038c24a9909e6605f74b7bfcd9ac37fd3a1f782a06bb18d53eb.jpg)

<table><tr><td>Site name</td><td>Elevation (m)</td><td>Latitude</td><td>Longitude</td><td>Aspect</td><td>Slope</td></tr><tr><td>Almont Curve</td><td>2456</td><td>38.66125</td><td>-106.85152</td><td>168.69</td><td>10.825</td></tr><tr><td>Almont</td><td>2569</td><td>38.65622</td><td>-106.86203</td><td>111.801</td><td>15.07</td></tr><tr><td>CDOT</td><td>2588</td><td>38.78257</td><td>-106.87002</td><td>243.435</td><td>6.37937</td></tr><tr><td>Lypps</td><td>2639</td><td>38.74812</td><td>-106.83269</td><td>263.66</td><td>6.45795</td></tr><tr><td>Tuttle</td><td>2877</td><td>38.954751</td><td>-106.988704</td><td>243.435</td><td>3.1996</td></tr><tr><td>Willey</td><td>2884</td><td>38.955971</td><td>-106.988482</td><td>261.87</td><td>5.05115</td></tr><tr><td>Kettle Ponds</td><td>2884</td><td>38.94435</td><td>-106.97174</td><td>18.4349</td><td>2.26364</td></tr><tr><td>Beaver</td><td>2921</td><td>38.961597</td><td>-106.993975</td><td>45</td><td>5.05115</td></tr><tr><td>Seans</td><td>2931</td><td>38.964099</td><td>-106.992616</td><td>225</td><td>8.04947</td></tr><tr><td>Rustlers</td><td>2977</td><td>38.9885</td><td>-107.00512</td><td>231.34</td><td>9.09464</td></tr><tr><td>Davids</td><td>2979</td><td>38.962124</td><td>-106.986896</td><td>206.565</td><td>12.6044</td></tr><tr><td>Gothic</td><td>3001</td><td>38.963088</td><td>-106.994866</td><td>71.565</td><td>11.18</td></tr><tr><td>Little</td><td>3061</td><td>38.96732</td><td>-106.96885</td><td>135</td><td>8.04947</td></tr><tr><td>Hill</td><td>3069</td><td>38.96677</td><td>-106.97009</td><td>123.69</td><td>19.827</td></tr><tr><td>Copper</td><td>3072</td><td>38.96896</td><td>-106.96801</td><td>102.529</td><td>12.9794</td></tr><tr><td>Snodgrass</td><td>3224</td><td>38.92625</td><td>-106.98172</td><td>118.74</td><td>23.8426</td></tr><tr><td>Elko</td><td>3230</td><td>39.01245</td><td>-107.05279</td><td>45</td><td>1.01275</td></tr><tr><td>Mexican Cut</td><td>3438</td><td>39.02685</td><td>-107.06513</td><td>51.3402</td><td>17.7528</td></tr></table>

Table S3. A list of the species, number of individuals, associated traits, number of individuals used in1 the analysis (#), and the number of phenophase estimates that we were able to make from the time-2 series data. Abbreviations are as follows: ITD is intertegular distance, Em. is emergence, and Sen. is3 4 senescence. Because there have not been species-levels trait studies on every species in the analysis, 5 some nest location and overwintering stage traits have been inferred from other species in the same genera (marked with an \* in the references column). We also compared these trait values with those6 reported in papers summarizing traits by genus (Mitchell 1960, Mitchell 1962, Stephen et al. 1969,7 Michener 2007, Harmon-Threatt 2020).8

<table><tr><td>Family</td><td>Species</td><td>ITD (mm)</td><td>Nest loc.</td><td>Overw. stage</td><td>#</td><td>Em. points</td><td>Peak points</td><td>Sen. points Reference</td></tr><tr><td rowspan="10">Andrenidae</td><td>Andrena algidaSmith 1853</td><td>1.91</td><td>below</td><td>adults</td><td>44</td><td>0</td><td>1</td><td>6 (LaBerge 1986)</td></tr><tr><td>Andrena lawrenceiViereck &amp; Cockerell 1914</td><td>2.36</td><td>below</td><td>adults</td><td>20</td><td>0</td><td>0</td><td>1 (LaBerge and Ribble 1975)</td></tr><tr><td>Andrena nothocalaidisCockerell 1905</td><td>2.15</td><td>below</td><td>adults</td><td>5</td><td>0</td><td>0</td><td>(Thorp 1969; Cane &amp; Love 1 2016; Gezon et al. 2015)</td></tr><tr><td>Andrena transnigraViereck 1904</td><td>3.17</td><td>below</td><td>adults</td><td>19</td><td>0</td><td>0</td><td>(Bouseman and LaBerge 5 1978)</td></tr><tr><td>Calliopsis coloradensisCresson 1878</td><td>1.65</td><td>below</td><td>prepupae</td><td>4</td><td>2</td><td>1</td><td>(Mitchell 1960; Shinn 1967 Jackson 1966; Miliczky 1 1991; Sheffield et al. 2014)</td></tr><tr><td>Calliopsis teucriiCockerell 1899</td><td>1.41</td><td>below</td><td>prepupae</td><td>319</td><td>5</td><td>4</td><td>(Shinn 1967; Hefetz et al. 1 1982)</td></tr><tr><td>Panurginus cressoniellusCockerell 1898</td><td>1.3</td><td>below</td><td>prepupae</td><td>2269</td><td>29</td><td>48</td><td>29 (Stephen et al. 1969) *</td></tr><tr><td>Panurginus ineptusCockerell 1922</td><td>1.35</td><td>below</td><td>prepupae</td><td>946</td><td>36</td><td>38</td><td>(Gezon et al. 2015; Stephen 37 et al. 1969) *</td></tr><tr><td>Pseudopanurgus bakeri(Cockerell 1906)</td><td>1.12</td><td>below</td><td>prepupae</td><td>569</td><td>61</td><td>29</td><td>(Gezon et al. 2015; Stephen 13 et al. 1969) *</td></tr><tr><td>Pseudopanurgus didirupa(Cockerell 1908)</td><td>1.3</td><td>below</td><td>prepupae</td><td>102</td><td>19</td><td>6</td><td>(Gezon et al. 2015; Stephen 3 et al. 1969) *</td></tr><tr><td rowspan="6">Apidae</td><td>Anthophora terminalisCresson 1869</td><td>3.17</td><td>above</td><td>prepupae</td><td>10</td><td>3</td><td>3</td><td>1 (Medler 1964)</td></tr><tr><td>Ceratina neomexicanaCockerell 1901</td><td>1.37</td><td>above</td><td>adults</td><td>67</td><td>1</td><td>3</td><td>5 (Michener 1936)</td></tr><tr><td>Melissodes confususCresson 1878</td><td>3.01</td><td>below</td><td>prepupae</td><td>13</td><td>5</td><td>1</td><td>(LaBerge 1961; Clement 0 1973; Hurd et al. 1980)</td></tr><tr><td>Melissodes grindeliaeCockerell 1898</td><td>2.72</td><td>below</td><td>prepupae</td><td>2</td><td>1</td><td>1</td><td>(LaBerge 1961; Clement 0 1973; Hurd et al. 1980)</td></tr><tr><td>Melissodes hymenoxidisCockerell 1906</td><td>3.11</td><td>below</td><td>prepupae</td><td>2</td><td>1</td><td>0</td><td>(LaBerge 1961; Clement 0 1973; Hurd et al. 1980)</td></tr><tr><td>Melissodes tristisCockerell 1894</td><td>3.07</td><td>below</td><td>prepupae</td><td>12</td><td>0</td><td>3</td><td>(LaBerge 1961; Clement 1 1973; Hurd et al. 1980)</td></tr><tr><td rowspan="6">Colletidae</td><td>Colletes consorsCresson 1868</td><td>2.19</td><td>below</td><td>adults</td><td>2</td><td>1</td><td>1</td><td>(Gezon et al. 2015; Sheffield 1et al. 2014) *</td></tr><tr><td>Colletes nigrifronsTitus 1900</td><td>2.04</td><td>below</td><td>adults</td><td>38</td><td>6</td><td>8</td><td>(Gezon et al. 2015; 5 Sheffield et al. 2014) *</td></tr><tr><td>Hylaeus annulatus(L. 1758)</td><td>1.28</td><td>above</td><td>prepupae</td><td>353</td><td>34</td><td>14</td><td>(Gezon et al. 2015; Stephen 6 et al. 1969) *</td></tr><tr><td>Hylaeus basalis(Smith 1853)</td><td>1.85</td><td>above</td><td>prepupae</td><td>57</td><td>8</td><td>10</td><td>4 (Scott 1996)</td></tr><tr><td>Hylaeus modestusSay 1837</td><td>1.38</td><td>above</td><td>prepupae</td><td>2</td><td>1</td><td>1</td><td>(Packer et al. 2007; Stephen 1 et al. 1969)</td></tr><tr><td>Hylaeus rudbeckiae(Cockerell &amp; Casad 1895)</td><td>0.97</td><td>above</td><td>prepupae</td><td>12</td><td>1</td><td>0</td><td>(Packer et al. 2007; Stephen 0 et al. 1969)</td></tr><tr><td rowspan="18">Halictidae</td><td>Agapostemon texanusCresson 1872</td><td>2.22</td><td>below</td><td>adults</td><td>170</td><td>3</td><td>1</td><td>(Roberts 1973a; Eickwort 01981)</td></tr><tr><td>Dufourea fimbriata^(Cresson 1878)</td><td>1.18</td><td>below</td><td>prepupae</td><td>50</td><td>8</td><td>7</td><td>3 Dumesh &amp; Sheffield 2012)</td></tr><tr><td>Dufourea harveyi^(Cockerell 1906)</td><td>1.18</td><td>below</td><td>prepupae</td><td>221</td><td>33</td><td>24</td><td>7 Dumesh &amp; Sheffield 2012)</td></tr><tr><td>Dufourea maura(Cresson 1878)</td><td>1.73</td><td>below</td><td>prepupae</td><td>43</td><td>11</td><td>6</td><td>5 Dumesh &amp; Sheffield 2012)</td></tr><tr><td>Halictus confususSmith 1853</td><td>1.32</td><td>below</td><td>adults</td><td>38</td><td>2</td><td>1</td><td>(Dolphin 1971, 1978; Eickwort et al. 1996; 1 Richards et al. 2010)</td></tr><tr><td>Halictus rubicundus(Christ 1791)</td><td>1.87</td><td>below</td><td>adults</td><td>496</td><td>25</td><td>6</td><td>13 (Dolphin 1978)</td></tr><tr><td>Halictus tripartitusCockerell 1895</td><td>1.24</td><td>below</td><td>adults</td><td>231</td><td>2</td><td>8</td><td>(Dolphin 1978; Gezon et al. 7 2015; Roberts 1973b)</td></tr><tr><td>Halictus virgatellusCockerell 1901</td><td>1.44</td><td>below</td><td>adults</td><td>1722</td><td>10</td><td>19</td><td>(Gezon et al. 2015; 26 Sheffield et al. 2014) *</td></tr><tr><td>LasioglossumabundipunctumGibbs 2010</td><td>1.01</td><td>below</td><td>adults</td><td>136</td><td>3</td><td>3</td><td>(Gezon et al. 2015; Packer 9 et al. 2007)</td></tr><tr><td>Lasioglossum ephialtumGibbs 2010</td><td>1.01</td><td>below</td><td>adults</td><td>4</td><td>1</td><td>1</td><td>1 (Gibbs, 2010)</td></tr><tr><td>Lasioglossum inconditum(Cockerell 1916)</td><td>1.25</td><td>below</td><td>adults</td><td>980</td><td>6</td><td>3</td><td>45 (Gibbs et al. 2013)</td></tr><tr><td>Lasioglossum nigrum(Viereck 1903)</td><td>1.28</td><td>below</td><td>adults</td><td>1865</td><td>4</td><td>6</td><td>40 (Packer et al. 2007)</td></tr><tr><td>Lasioglossum obnubilum(Sandhouse 1924)</td><td>0.89</td><td>below</td><td>adults</td><td>167</td><td>5</td><td>4</td><td>(Gibbs 2010; Packer et al. 5 2007)</td></tr><tr><td>Lasioglossum occidentale(Crawford 1902)</td><td>0.96</td><td>below</td><td>adults</td><td>46</td><td>3</td><td>5</td><td>4 (Packer et al. 2007)</td></tr><tr><td>Lasioglossum pacatum(Sandhouse 1924)</td><td>1.12</td><td>below</td><td>adults</td><td>643</td><td>0</td><td>1</td><td>(Gibbs 2010; Packer et al. 4 2007)</td></tr><tr><td>Lasioglossum pavoninum(Ellis 1913)</td><td>1.06</td><td>below</td><td>adults</td><td>51</td><td>3</td><td>2</td><td>(Gibbs 2010; Packer et al. 3 2007)</td></tr><tr><td>LasioglossumprasinogasterGibbs 2010</td><td>1.14</td><td>below</td><td>adults</td><td>806</td><td>0</td><td>2</td><td>5 (Packer et al. 2007)</td></tr><tr><td>Lasioglossum ruidosense(Cockerell 1897)</td><td>1.05</td><td>below</td><td>adults</td><td>1273</td><td>8</td><td>8</td><td>27 (Gibbs 2010; Packer et al.2007)</td></tr><tr><td rowspan="5"></td><td>Lasioglossum sandhousiellum Gibbs 2010</td><td>1.08</td><td>below</td><td>adults</td><td>85</td><td>13</td><td>1</td><td>(Gibbs 2010; Packer et al. 1 2007)</td></tr><tr><td>Lasioglossum sedi (Sandhouse 1924)</td><td>0.99</td><td>below</td><td>adults</td><td>6161</td><td>4</td><td>11</td><td>63 (Packer et al. 2007)</td></tr><tr><td>Lasioglossum semicaeruleum (Cockerell 1895)</td><td>1.03</td><td>below</td><td>adults</td><td>41</td><td>3</td><td>5</td><td>(Gibbs 2010; Packer et al. 2 2007)</td></tr><tr><td>Lasioglossum tenax (Sandhouse 1924)</td><td>1.06</td><td>below</td><td>adults</td><td>343</td><td>5</td><td>1</td><td>16 (Packer 1994)</td></tr><tr><td>Lasioglossum trizonatum (Cresson 1874)</td><td>2.3</td><td>below</td><td>adults</td><td>359</td><td>2</td><td>0</td><td>13 (McGinley 1986)</td></tr><tr><td rowspan="16">Megachilidae</td><td>Dianthidium heterulkei Schwarz 1940</td><td>2.08</td><td>above</td><td>prepupae</td><td>49</td><td>7</td><td>3</td><td>(Krombein 1967; Clement 01976)</td></tr><tr><td>Hopitis albifrons (Kirby 1837)</td><td>2.43</td><td>above</td><td>prepupae</td><td>13</td><td>3</td><td>2</td><td>1 (Fye 1965)</td></tr><tr><td>Hopitis fulgida (Cresson 1864)</td><td>2.04</td><td>above</td><td>prepupae</td><td>88</td><td>9</td><td>12</td><td>4 (Tepedino &amp; Parker 1984)</td></tr><tr><td>Hopitis robusta (Nylander 1848)</td><td>1.39</td><td>above</td><td>prepupae</td><td>156</td><td>23</td><td>21</td><td>(Clement &amp; Rust 1975; Müller &amp; Richter 2018; 14 Müller &amp; Mauss 2016)</td></tr><tr><td>Megachile frigida Smith 1853</td><td>3.64</td><td>above</td><td>prepupae</td><td>7</td><td>2</td><td>1</td><td>(Hobbs &amp; Lilly 1954; Pengelly 1955; Stephen 1956; Jenkins &amp; Matthews 0 2004)</td></tr><tr><td>Megachile inermis Provancher 1888</td><td>4.43</td><td>above</td><td>prepupae</td><td>4</td><td>1</td><td>1</td><td>(Stephen 1956; Medler 0 1958; Sheffield et al. 2008)</td></tr><tr><td>Megachile melanophaea Smith 1853</td><td>3.26</td><td>below</td><td>prepupae</td><td>22</td><td>8</td><td>4</td><td>(Hobbs &amp; Lilly 1954; 3 Pengelly 1955)</td></tr><tr><td>Megachile montivaga Cresson 1878</td><td>2.61</td><td>above</td><td>prepupae</td><td>15</td><td>3</td><td>3</td><td>(Hicks 1926; Hobbs &amp; Lilly 2 1954; Baker et al. 1985)</td></tr><tr><td>Megachile perihirta Cockerell 1898</td><td>3.53</td><td>below</td><td>prepupae</td><td>9</td><td>2</td><td>1</td><td>(Sladen 1918; Hicks 1926; Hobbs &amp; Lilly 1954; Bohart 1 1957)</td></tr><tr><td>Megachile pugnata Say 1837</td><td>3.1</td><td>above</td><td>prepupae</td><td>1</td><td>1</td><td>0</td><td>(Medler 1964; Hobbs &amp; Lilly 1954; Sheffield et al. 0 2008)</td></tr><tr><td>Megachile relativa Cresson 1878</td><td>2.47</td><td>above</td><td>prepupae</td><td>18</td><td>6</td><td>5</td><td>(Medler &amp; Koerber 1958; 2 Sheffield et al. 2008)</td></tr><tr><td>Osmia albolateralis Cockerell 1906</td><td>2.23</td><td>above</td><td>adults</td><td>56</td><td>5</td><td>7</td><td>4 (Rightmyer et al. 2013)</td></tr><tr><td>Osmia brevis Cresson 1864</td><td>2.3</td><td>above</td><td>adults</td><td>21</td><td>2</td><td>2</td><td>(Baker et al. 1985; Cane 2 2014)</td></tr><tr><td>Osmia bruneri Cockerell 1897</td><td>2.1</td><td>above</td><td>adults</td><td>5</td><td>0</td><td>0</td><td>(Baker et al. 1985; Cane et 1 al. 2007; Frohlich 1983)</td></tr><tr><td>Osmia bucephala Cresson 1864</td><td>3.76</td><td>above</td><td>adults</td><td>93</td><td>3</td><td>8</td><td>13 (Rightmyer et al. 2013) *</td></tr><tr><td>Osmia inermis (Zetterstedi 1838)</td><td>2.35</td><td>above</td><td>adults</td><td>5</td><td>0</td><td>0</td><td>(Müller 2018; Sheffield et 1 al. 2014)</td></tr><tr><td rowspan="6"></td><td>Osmia longulaCresson 1864</td><td>3.2</td><td>above</td><td>adults</td><td>6</td><td>1</td><td>1</td><td>(Cane et al. 2007;2 Rightmyer et al. 2013)</td></tr><tr><td>Osmia phaceliaeCockerell 1907</td><td>1.78</td><td>above</td><td>adults</td><td>8</td><td>1</td><td>1</td><td>1 (Packer et al. 2007) *</td></tr><tr><td>Osmia sculleniSandhouse 18939</td><td>2.32</td><td>above</td><td>adults</td><td>3</td><td>0</td><td>1</td><td>(Cane et al. 2007; Sheffield1 et al. 2014) *</td></tr><tr><td>Osmia simillimaSmith 1853</td><td>2.53</td><td>above</td><td>adults</td><td>105</td><td>7</td><td>6</td><td>(Cane et al. 2007; Sheffield13 et al. 2014) *</td></tr><tr><td>Osmia tersulaCockerell 1912</td><td>2.31</td><td>above</td><td>adults</td><td>6</td><td>1</td><td>2</td><td>(Cane et al. 2007; Sheffield2 et al. 2008)</td></tr><tr><td>Osmia “torchioi”Griswold ms. name</td><td>1.82</td><td>above</td><td>adults</td><td>12</td><td>0</td><td>1</td><td>1 (Gezon et al., 2015)</td></tr></table>

^ Dufourea harveyi and Dufourea fimbriata may be synonymous in some parts of their range, but we found clear morphological differences between specimens in these groups in the present study area.

## Table S3 references

Baker, J. R., Kuhn, E. D., & Bambara, S. B. (1985). Nests and immature stages of leafcutter bees (Hymenoptera: Megachilidae). Journal of the Kansas Entomological Society, 58, 290–313.

Bohart, G. E. (1957). Pollination of alfalfa and red clover. Annual Review of Entomology, 2(1), 355-380.

Bouseman, J. K., LaBerge, W. E. 1978. A revision of the bees of the genus Andrena of the Western Hemisphere. Part IX. Subgenus Melandrena. Transactions of the American Entomological Society 104: 275-390

Butler Jr, G. D. (1965). Distribution and host plants of leaf-cutter bees in Arizona. College of Agriculture, University of Arizona, Tucson, AZ.

Cane, J. H. (2014). The oligolectic bee Osmia brevis sonicates Penstemon flowers for pollen: a newly documented behavior for the Megachilidae. Apidologie, 45, 678–684.

Cane, J. H., Griswold, T., & Parker, F. D. (2007). Substrates and materials used for nesting by North American Osmia bees (Hymenoptera: Apiformes: Megachilidae). Annals of the Entomological Society of America, 100, 350–358.

Cane, J. H., & Love, B. (2016). Floral guilds of bees in sagebrush steppe: comparing bee usage of wildflowers available for postfire restoration. Natural Areas Journal, 36, 377–391.

Clement, S. L. (1973). The nesting biology of Melissodes (Eumelissodes) rustica (Say), with a description of the larva (Hymenoptera: Anthophoridae). Journal of the Kansas Entomological Society, 46, 516–525.

Clement, S.L. 1976. The biology of Dianthidium heterulkei heterulkei Schwarz, with a description of the larva (Hymenoptera, Megachilidae). Wasmann Journal of Biology 34: 9–22.

Clement SL, Rust RW (1975) The biology of Hoplitis robusta (Hymenoptera: Megachilidae). Entomological News 86(5/6): 115-120.

Dolphin, R. E. (1971, January). Observations of Halictus confusus Smith (Hymenoptera: Halictidae) on Woodland and Field Flowers. Proceedings of the Indiana Academy of Science, 81, 182-186.

Dolphin, R. E. (1978). Associates of the native bee, Halictus (Seladonia) confusus Smith (Hymenoptera: Halictidae). Proceedings of the Indiana Academy of Science, 88, 228–234.

Dumesh, S., & Sheffield, C. S. (2012). Bees of the genus Dufourea Lepeletier (Hymenoptera: Halictidae: Rophitinae) of Canada. Canadian Journal of Arthropod Identification, 20, 1–36.

Eickwort, G. C., Eickwort, M., Gordon, J., & Eickwort, M. A. (1996). Solitary behavior in a high-altitude population of the social sweat bee Halictus rubicundus (Hymenoptera: Halictidae). Behavioral Ecology and Sociobiology, 38, 227–233.

Fye, R. E. (1965). Biology of Apoidea taken in trap nests in northwestern Ontario (Hymenoptera). The Canadian Entomologist, 97(8), 863-877.

Frohlich, D. R. (1983). On the nesting biology of Osmia (Chenosmia) bruneri (Hymenoptera: Megachilidae). Journal of the Kansas Entomological Society, 56, 123–130.

Gezon, Z. J., Wyman, E. S., Ascher, J. S., Inouye, D. W., & Irwin, R. E. (2015). The effect of repeated, lethal sampling on wild bee abundance and diversity. Methods in Ecology and Evolution, 6, 1044–1054.

Gibbs, J. (2010). Revision of the metallic species of Lasioglossum (Dialictus) in Canada (Hymenoptera, Halictidae, Halictini). Zootaxa, 259, 1–382.

Gibbs, J., Ascher, J. S., Rightmyer, M. G., & Isaacs, R. (2017). The bees of Michigan (Hymenoptera: Apoidea: Anthophila), with notes on distribution, taxonomy, pollination, and natural history. Zootaxa, 4352, 1–160.

Gibbs, J., Packer, L., Dumesh, S., & Danforth, B. N. (2013). Revision and reclassification of Lasioglossum (Evylaeus), L. (Hemihalictus) and L. (Sphecodogastra) in eastern North America (Hymenoptera: Apoidea: Halictidae). Zootaxa, 3672, 1–116.

Harmon-Threatt, A. (2020). Influence of Nesting Characteristics on Health of Wild Bee Communities. Annual Review of Entomology, 65, 39-56.

Hefetz, A., Eickwort, G. C., Blum, M. S., Cane, J., & Bohart, G. E. (1982). A comparative study of the exocrine products of cleptoparasitic bees (Holcopasites) and their hosts (Calliopsis) (Hymenoptera: Anthophoridae, Andrendae). Journal of Chemical Ecology, 8, 1389–1397.

Hicks, C. H. (1926). Nesting habits and parasites of certain bees of Boulder County, Colorado. University of Colorado Studies, 15, 217.

Hobbs, G. A. (1956). Ecology of the leaf-cutter bee Megachile perihirta Ckll. (Hymenoptera: Megachilidae) in relation to production of alfalfa seed. The Canadian Entomoloigst, 3414, 625–631.

Hobbs, G. A., & Lilly, C. E. (1954). Ecology of Species of Megachile Latreille in the mixed prairie region of southern Alberta with special reference to pollination of alfalfa. Ecology, 35, 453–462.

Hurd, P. D., Laberge, W. E., & Linsley, E. G. (1980). Principal sunflower bees of North America with emphasis on the southwestern United States (Hymenoptera: Apoidea). Smithsonian Institution Press, Washington, D.C.

Jackson, R. C. (1966). Some intersectional hybrids and relationships in Haplopappus. The University of Kansas Science Bulletin, 475–485.

James, R. R., & Pitts-Singer, T. L. (2008). Bee Pollination in Agricultural Ecosystems (pp. 219–222). Oxford University Press, New York, NY.

Jenkins, D. A., & Matthews, R. W. (2004). Cavity-nesting Hymenoptera in disturbed habitats of Georgia and South Carolina: nest architecture and seasonal occurrence. Journal of the Kansas Entomological Society, 77, 203–214.

Krombein, K. V. (1967). Trap-nesting wasps and bees: life histories and nest associates. Smithsonian, Washington, D. C.

LaBerge, W. E. (1986). The zoogeography of Andrena Fabricius (Hymenoptera: Andrenidae) of the Western Hemisphere. Proceedings of the Ninth North American Prairie Conference, 110, 110–115.

LaBerge, W. E., Ribble, D. W. 1975. A revision of the bees of the genus Andrena of the Western Hemisphere. Part VII. Subgenus Euandrena. Transactions of the American Entomological Society 101: 371-446.

Levin, M. D. (1966). Biological notes on Osmia lignaria and Osmia californica (Hymenoptera: Apoidea, Megachilidae). Journal of the Kansas Entomological Society, 39, 524–535.

McGinley, R. J. (1986). Studies of Halictinae (Apoidea: Halictidae), I: revision of new world Lasioglossum curtis. Smithsonian contributions to zoology.

Medler, J. T. (1964). Anthophora (Clisodon) terminalis Cresson in trap-nests in Wisconsin (Hymenoptera: Anthophoridae). The Canadian Entomoloigst, 96, 1332–1336.

Medler, J. T., & Koerber, T. W. (1958). Biology of Megachile relativa Cresson (Hymenoptera, Megachilidae) in trap-nests in Wisconsin. Annals of the Entomological Society of America, 51, 337–344.

Melander, A. L. (1902). The nesting habits of Anthidium. Biological Bulletin, 3, 27–32.

Michener, C. D. (1936). Western bees of the genus Ceratina, subgenus Zaodontomerus. American Museum Novitates, 844, 2–13.

Miliczky, E. (1991). Observations on the nesting biology of three species of panurgine bees (Hymenoptera: Andrenidae). Journal of the Kansas Entomological Society, 64, 80–87.

Miliczky, E. (2008). Observations on the nesting biology of Andrena (Plastandrena) prunorum Cockerell in Washington State (Hymenoptera: Andrenidae). Journal of the Kansas Entomological Society, 81, 110–121.

Mitchell, T.B. 1960 Bees of the Eastern United States. North Carolina Agricultural Experiment Station Technical Bulletin No. 141.

Mitchell, T. B. (1962). Bees of the eastern United States. II Technical bulletin. North Carolina Agricultural Experiment Station, 152, 1-557.

Müller, A. (2018). Pollen host selection by predominantly alpine bee species of the genera Andrena, Panurginus, Dufourea, Megachile, Hoplitis and Osmia (Hymenoptera, Apoidea). Alpine Entomology, 2, 101–113.

Müller A, Richter H (2018). Dual function of Potentilla (Rosaceae) in the life history of the rare boreoalpine osmiine bee Hoplitis (Formicapis) robusta (Hymenoptera, Megachilidae). Alpine Entomology 2: 139–147.

Müller A, Mauss V (2016) Palaearctic Hoplitis bees of the subgenera Formicapis and Tkalcua (Megachilidae, Osmiini): biology, taxonomy and key to species. Zootaxa 4127(1): 105-120. http://dx.doi.org/10.11646/zootaxa.4127.1.5

Packer, L. (1994). Lasioglossum (Dialictus) tenax (Sandhouse) (Hymenoptera: Halictidae) as a solitary sweat bee. Insect Society, 41, 309–313.

Packer, L., Genaro, J. A., & Sheffield, C. S. (2007). The bee genera of Eastern Canada. Canadian Journal of Arthropod Identification, 3, 1–32.

Pengelly, D. H. (1955). The biology of bees of the genus Megachile with special reference to their importance in alfalfa seed production in southern Ontario. Cornell University Press.

Pesenko, Y.A., and Y.V. Astafurova. 2006. Contributions to the Halictidae fauna of the Eastern Palaearctic Region: subfamily Rophitinae (Hymenoptera: Halictidae). Entomofauna 27: 317-356.

Richards, M. H., Vickruck, J. L., & Rehan, S. M. (2010). Colony social organisation of Halictus confusus in southern Ontario, with comments on sociality in the subgenus H. (Seladonia). Journal of Hymenoptera Research, 19(1), 144- 158.

Rightmyer, M. G., Griswold, T., & Brady, S. G. (2013). Phylogeny and systematics of the bee genus Osmia (Hymenoptera: Megachilidae) with emphasis on North American Melanosmia: subgenera, synonymies and nesting biology revisited. Systematic Entomology, 38, 561–576.

Roberts, R. B. (1973a). Bees of Northwestern America: Agapostemon. Oregon State University Agricultural Experiment Station, 125, 1–23.

Roberts, R. B. (1973b). Bees of Northwestern America: Halictus. Oregon State University Agricultural Experiment Station, 1–23.

Scott, V. (1996). Pollen selection by three species of Hylaeus in Michigan (Hymenoptera: Colletidae). Journal of the Kansas Entomological Society, 69, 195–200.

Sheffield, C. S. (2008). Summer bees for spring crops? Potential problems with Megachile rotundata (Fab.)(Hymenoptera: Megachilidae) as a pollinator of lowbush blueberry (Ericaceae). Journal of the Kansas Entomological Society, 81(3), 276-287.

Sheffield, C. S., Frier, D., & Dumesh, S. (2014). The bees (Hymenoptera: Apoidea, Apiformes) of the prairies ecozone with comparisons to other grasslands of Canada. Arthropods of Canadian Grasslands, 4, 427–467.

Sladen, F. W. L. (1918). Pollination of alfalfa by bees of the genus Megachile. Table of Canadian species of the latimanus group. The Canadian Entomologist, 50(9), 301-304.

Stephen, W. P., Bohart, G. E., & Torchio, P. F. (1969). The biology and external morphology of bees with a synopsis of the genera of North-Western America. Oregon State University Agricultural Experiment Station, 1–146.

Tepedino, V. J., & Frohlich, D. R. (1982). Mortality factors, pollen utilization, and sex ratio in Megachile pugnata Say (Hymenoptera: Megachilidae), a candidate for commercial sunflower pollination. Journal of the New York Entomological Society, 90, 269–274.

Tepedino, V. J., & Parker, F. D. (1984). Nest selection, mortality and sex ratio in Hoplitis fulgida (Cresson) (Hymenoptera: Megachilidae). Journal of the Kansas Entomological Society, 57, 181–189.

Thorp, R. W. 1969. Systematics and ecology of bees of the subgenus Diandrena (Hymenoptera: Andrenidae). University of California Publications in Entomology 52: 1-146.

Table S4. Coefficients for species-specific shifts in phenophases in response to snowmelt timing1 (Figure 1). The three phenophases (emergence, peak, senescence) are separated by commas.2

<table><tr><td>Species</td><td>Slope</td><td>SE</td><td>t</td></tr><tr><td>Dufourea harveyi</td><td>0.22, 0.18, NA</td><td>0.32, 0.30, NA</td><td>0.68, 0.59, NA</td></tr><tr><td>Halictus rubicundus</td><td>0.42, NA, 0.13</td><td>0.46, NA, 0.57</td><td>0.42, NA, 0.22</td></tr><tr><td>Halictus virgatellus</td><td>-0.01, -0.09, 1.45</td><td>1.12, 0.39, 0.66</td><td>-0.21,-0.68, 2.01</td></tr><tr><td>Hoplitis fulgida</td><td>0.86, 0.83, NA</td><td>0.63, 0.39, NA</td><td>1.02, 1.68, NA</td></tr><tr><td>Hoplitis robusta</td><td>0.52, 0.84, 0.5</td><td>0.61, 0.42, 0.9</td><td>0.48, 1.59, 0.41</td></tr><tr><td>Hylaeus annulatus</td><td>0.65, 0.5, NA</td><td>0.38, 0.35, NA</td><td>1.13, 0.92, NA</td></tr><tr><td>Lasioglossum sedi</td><td>NA, 0.8, -0.14</td><td>NA, 0.51, 0.59</td><td>NA, 1.22, -0.45</td></tr><tr><td>Panurginus cressoniellus</td><td>0.56, 0.29, 0.71</td><td>0.46, 0.36, 0.74</td><td>0.74, 0.31, 0.79</td></tr><tr><td>Panurginus ineptus</td><td>-0.07, 0.09, 0.19,</td><td>0.47, 0.35, 0.66</td><td>-0.62, -0.24, 0.1</td></tr><tr><td>Pseudopanurgus bakeri</td><td>0.53, 0.09, -0.25</td><td>0.39, 0.37, 0.73</td><td>0.79, -0.24,-0.52</td></tr></table>

Table S5. Coefficients of standardized effect sizes from the full model of bee phenology (Figure 2).1 The three phenophases (emergence, peak, senescence) are separated by commas. Significant effects at2 the α=0.05 level are bold, but all effects were determined to be important by the model averaging3 4 protocol.

<table><tr><td>Predictor</td><td>Slope</td><td>SE</td><td>z</td><td>P</td></tr><tr><td>Snowmelt date</td><td>11.52, 12.82, 7.81</td><td>2.68, 2.42, 2.44</td><td>4.28, 5.26, 3.19</td><td>&lt;0.01, &lt;0.01,&lt;0.01</td></tr><tr><td>Summer rainfall</td><td>10.04, 2.73, -1.85</td><td>2.12, 2.06, 2.12</td><td>4.72, 1.32, 0.87</td><td>&lt;0.01, 0.19, 0.38</td></tr><tr><td>Maximum temperature</td><td>-7.34, 1.40, -0.90</td><td>2.41, 2.22, 2.47</td><td>3.04, 0.63, 0.36</td><td>&lt;0.01, 0.53, 0.72</td></tr><tr><td>Elevation</td><td>13.57, 7.76, -5.92</td><td>3.23, 3.65, 4.05</td><td>4.15, 2.12, 1.46</td><td>&lt;0.01, 0.03, 0.15</td></tr><tr><td>Solar Incidence</td><td>-6.13, -1.68, 4.03</td><td>3.40, 3.27, 4.04</td><td>1.80, 0.56, 1.00</td><td>0.07, 0.57, 0.32</td></tr><tr><td>Body Mass</td><td>2.08, -2.58, -2.79</td><td>3.23, 3.26, 3.57</td><td>0.64, 0.79, 0.78</td><td>0.54, 0.43, 0.43</td></tr><tr><td>Nest Location (below ground)</td><td>11.21, -4.57, -9.82</td><td>4.30, 3.84, 4.29</td><td>2.60, 1.19, 2.28</td><td>&lt;0.01, 0.24, 0.02</td></tr><tr><td>Overwintering stage (prepupae)</td><td>1.91, 11.20, 20.91</td><td>3.52, 3.23, 3.59</td><td>0.54, 3.45, 5.81</td><td>0.59, &lt;0.01, &lt;0.01</td></tr></table>

Table S6. Marginal and conditional1 $\mathtt { R } ^ { 2 }$ values for the three phenology top models, as well as the proportion of variance explained by subsetted climate and trait models (Figure 3).2

<table><tr><td>Model</td><td>Phenophase</td><td>Marginal R2</td><td>Conditional R2</td><td>Proportion of marginal variance explained</td></tr><tr><td rowspan="3">Full model</td><td>Emergence</td><td>0.49</td><td>0.86</td><td rowspan="3"></td></tr><tr><td>Peak</td><td>0.40</td><td>0.89</td></tr><tr><td>Senescence</td><td>0.45</td><td>0.84</td></tr><tr><td rowspan="3">Climate only</td><td>Emergence</td><td>0.26</td><td>0.85</td><td>0.53</td></tr><tr><td>Peak</td><td>0.16</td><td>0.88</td><td>0.41</td></tr><tr><td>Senescence</td><td>0.07</td><td>0.84</td><td>0.16</td></tr><tr><td rowspan="3">Traits only</td><td>Emergence</td><td>0.11</td><td>0.79</td><td>0.22</td></tr><tr><td>Peak</td><td>0.22</td><td>0.85</td><td>0.55</td></tr><tr><td>Senescence</td><td>0.43</td><td>0.82</td><td>0.95</td></tr></table>