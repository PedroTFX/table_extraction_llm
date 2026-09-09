Supporting Information

Appendix S1: Test for spatial independence

Figure S1-1: Spline (cross)-correlograms with average autocorrelation coefficient and 95% confidence bands (function spline.correlog in the package ncf within R; Bjørnstad & Falck 2001) for the residuals of the regional linear models shown in Fig. 2. (a) Phylogenetic diversity, (b) functional diversity, (c) body size diversity, (d) mean body size, (e) dead-wood diameter niche diversity, (f) mean dead-wood diameter niche, (g) dead-wood decay diversity, (h) mean dead-wood decay niche, (i) canopy cover niche diversity, (j) mean canopy cover niche. All diversity measures are effect sizes from null models (see Material and methods).

Appendix S2: Climate and landscape variables

As geographic variables, latitude and longitude were used as standardized Gauss-Krueger coordinates. Landscape characteristics (radius 3 km around the center of each stand) were estimated using the Europe-wide land-cover mapping project CORINE (http://www.corine.dfd.dlr.de), which used satellite remote-sensing images at a scale of 1:100,000. Land-use information comprises 44 categories, which were used to calculate the following variables (for CORINE types, see Table 1). 1) To characterize the fragmentation, we calculated the proportion of forest. 2) As an indicator of the severity of the transformation of remaining forests to conifer plantations in the originally beech-dominated forest landscape under study, we calculated the proportion of broad-leaf trees relative to the extent of forest. 3) For the extent of human settlements as an indicator for increasing management pressure, we calculated the proportion of traffic and settlements. For Switzerland, the variables were taken from www.swisstopo.admin.ch; for Ukraine, the variables were estimated from Google Earth aerial photos.

Climate variables were extracted from WorldClim with a resolution of 30 seconds and calculated as a mean value within 1 km radius; a larger radius would lead to inaccurate values for sites in rough terrain (Hijmans et al. 2005). We selected bio1, bio10, bio 12, and bio18 as ecologically meaningful variables. Each of the pairs of temperature and precipitation were highly correlated. Therefore, we decided to use the mean temperature (bio10) and precipitation of the warmest month (bio18) because they are related to the most important part of the life cycle of beetles.

Appendix S3: Species list and traits

Niche positions for each species were derived from data published by Möller (2009). Diameter was classified as < 15 cm, 15–35 cm, > 35 cm, and > 70 cm. Decay was classified in 5 classes from 0 (alive) to 4 (class 4 equates to class 4/5 in Albrecht 1990). Canopy cover was classified as sunny, semi-sunny, and shady. The increasing occurrence of a species in one or several of this ordinal classes was scored as 0.5 (very rare), 1 (rare), 2 (common), and 3 (preferred). Based on these values, we calculated for each species a weighted score for each niche value. As an example, we provide the calculation of dead-wood decay niche position of the stag beetle Lucanus cervus as follows:

<table>
<tr><td>Decay stage:</td><td>0</td><td>1</td><td>2</td><td>3</td><td>4/5</td></tr>
<tr><td>Decay class:</td><td>1</td><td>2</td><td>3</td><td>4</td><td>5</td></tr>
<tr><td>Ordinal score:</td><td>0</td><td>0</td><td>3</td><td>2</td><td>0</td></tr>
<tr><td>Calculation of niche position:</td><td>(0×1 + 0×2 + 3×3 + 2×4 + 0×5)/5</td><td>(0×1 + 0×2 + 3×3 + 2×4 + 0×5)/5</td><td>(0×1 + 0×2 + 3×3 + 2×4 + 0×5)/5</td><td>(0×1 + 0×2 + 3×3 + 2×4 + 0×5)/5</td><td>(0×1 + 0×2 + 3×3 + 2×4 + 0×5)/5</td></tr>
<tr><td>Dead-wood decay niche position:</td><td>3.4</td><td>3.4</td><td>3.4</td><td>3.4</td><td>3.4</td></tr>
</table>

The complete list of species recorded and their species traits are shown in Table S3-1.

Table S3-1: The species trait body size (mm) and the niche positions dead-wood diameter, dead-wood decay, and canopy cover of saproxylic beetle species used in the present study.

<table>
<tr><td>Family</td><td>Species</td><td>Body size</td><td>Diameter</td><td>Decay</td><td>Canopy cover</td></tr>
<tr><td>CARABIDAE</td><td>Tachyta nana</td><td>2.00</td><td>2.50</td><td>2.83</td><td>1.00</td></tr>
<tr><td>RHYSODIDAE</td><td>Rhysodes sulcatus</td><td>7.00</td><td>3.00</td><td>3.40</td><td>1.80</td></tr>
<tr><td>HISTERIDAE</td><td>Plegaderus vulneratus</td><td>1.00</td><td>2.29</td><td>2.00</td><td>1.50</td></tr>
<tr><td>HISTERIDAE</td><td>Plegaderus caesus</td><td>1.00</td><td>3.00</td><td>4.00</td><td>1.83</td></tr>
<tr><td>HISTERIDAE</td><td>Plegaderus dissectus</td><td>1.00</td><td>2.50</td><td>4.00</td><td>2.40</td></tr>
<tr><td>HISTERIDAE</td><td>Abraeus granulum</td><td>1.00</td><td>3.00</td><td>4.00</td><td>2.40</td></tr>
<tr><td>HISTERIDAE</td><td>Abraeus parvulus</td><td>1.00</td><td>3.80</td><td>4.00</td><td>1.40</td></tr>
<tr><td>HISTERIDAE</td><td>Abraeus perpusillus</td><td>1.00</td><td>3.20</td><td>4.00</td><td>2.00</td></tr>
<tr><td>HISTERIDAE</td><td>Acritus minutus</td><td>1.00</td><td>2.80</td><td>2.25</td><td>1.00</td></tr>
<tr><td>HISTERIDAE</td><td>Aeletes atomarius</td><td>1.00</td><td>3.80</td><td>4.00</td><td>1.50</td></tr>
<tr><td>HISTERIDAE</td><td>Dendrophilus punctatus</td><td>4.00</td><td>4.00</td><td>4.60</td><td>2.00</td></tr>
<tr><td>HISTERIDAE</td><td>Paromalus flavicornis</td><td>1.00</td><td>3.00</td><td>3.43</td><td>2.40</td></tr>
<tr><td>HISTERIDAE</td><td>Paromalus parallelepipedus</td><td>2.00</td><td>2.50</td><td>2.00</td><td>1.40</td></tr>
<tr><td>HISTERIDAE</td><td>Hololepta plana</td><td>8.00</td><td>3.00</td><td>2.40</td><td>1.40</td></tr>
<tr><td>HISTERIDAE</td><td>Platysoma compressum</td><td>3.00</td><td>3.00</td><td>2.40</td><td>1.25</td></tr>
<tr><td>HISTERIDAE</td><td>Eblisia minor</td><td>3.00</td><td>3.00</td><td>3.50</td><td>1.25</td></tr>
<tr><td>SPHAERITIDAE</td><td>Sphaerites glabratus</td><td>6.00</td><td>2.50</td><td>3.20</td><td>2.00</td></tr>
<tr><td>CHOLEVIDAE</td><td>Nemadus colonoides</td><td>1.00</td><td>4.00</td><td>4.75</td><td>1.80</td></tr>
<tr><td>LEIODIDAE</td><td>Anisotoma humeralis</td><td>3.00</td><td>2.50</td><td>4.00</td><td>2.40</td></tr>
<tr><td>LEIODIDAE</td><td>Anisotoma castanea</td><td>3.00</td><td>2.50</td><td>4.00</td><td>2.40</td></tr>
<tr><td>LEIODIDAE</td><td>Anisotoma glabra</td><td>3.00</td><td>3.00</td><td>4.00</td><td>2.40</td></tr>
<tr><td>LEIODIDAE</td><td>Anisotoma orbicularis</td><td>2.00</td><td>2.50</td><td>4.00</td><td>2.40</td></tr>
<tr><td>LEIODIDAE</td><td>Liodopria serricornis</td><td>2.00</td><td>2.29</td><td>4.00</td><td>2.60</td></tr>
<tr><td>LEIODIDAE</td><td>Agathidium nigripenne</td><td>3.00</td><td>2.00</td><td>3.00</td><td>2.00</td></tr>
<tr><td>SCYDMAENIDAE</td><td>Euthiconus conicicollis</td><td>1.00</td><td>3.20</td><td>4.20</td><td>2.50</td></tr>
<tr><td>SCYDMAENIDAE</td><td>Neuraphes carinatus</td><td>1.00</td><td>3.00</td><td>3.89</td><td>2.17</td></tr>
<tr><td>SCYDMAENIDAE</td><td>Neuraphes ruthenus</td><td>1.00</td><td>2.29</td><td>4.00</td><td>2.50</td></tr>
<tr><td>SCYDMAENIDAE</td><td>Neuraphes plicicollis</td><td>1.00</td><td>2.71</td><td>4.00</td><td>2.50</td></tr>
<tr><td>SCYDMAENIDAE</td><td>Scydmoraphes sparshalli</td><td>1.00</td><td>2.29</td><td>4.00</td><td>2.50</td></tr>
<tr><td>SCYDMAENIDAE</td><td>Scydmoraphes minutus</td><td>1.00</td><td>3.00</td><td>4.00</td><td>2.00</td></tr>
<tr><td>SCYDMAENIDAE</td><td>Stenichnus godarti</td><td>1.00</td><td>3.20</td><td>4.00</td><td>1.80</td></tr>
<tr><td>SCYDMAENIDAE</td><td>Stenichnus bicolor</td><td>1.00</td><td>3.00</td><td>3.17</td><td>1.60</td></tr>
<tr><td>SCYDMAENIDAE</td><td>Microscydmus minimus</td><td>0.70</td><td>3.00</td><td>4.50</td><td>2.00</td></tr>
<tr><td>SCYDMAENIDAE</td><td>Euconnus pragensis</td><td>1.00</td><td>3.50</td><td>4.50</td><td>2.20</td></tr>
<tr><td>SCYDMAENIDAE</td><td>Scydmaenus perrisii</td><td>1.00</td><td>3.80</td><td>4.00</td><td>1.60</td></tr>
<tr><td>SCYDMAENIDAE</td><td>Scydmaenus hellwigii</td><td>1.00</td><td>3.50</td><td>4.00</td><td>1.40</td></tr>
<tr><td>PTILIIDAE</td><td>Nossidium pilosellum</td><td>1.00</td><td>4.00</td><td>4.50</td><td>2.00</td></tr>
<tr><td>PTILIIDAE</td><td>Ptenidium gressneri</td><td>0.90</td><td>4.00</td><td>4.50</td><td>2.60</td></tr>
<tr><td>PTILIIDAE</td><td>Ptenidium turgidum</td><td>0.90</td><td>3.00</td><td>4.00</td><td>2.60</td></tr>
<tr><td>PTILIIDAE</td><td>Micridium halidaii</td><td>0.60</td><td>3.20</td><td>4.40</td><td>2.50</td></tr>
<tr><td>PTILIIDAE</td><td>Ptinella limbata</td><td>0.80</td><td>2.50</td><td>4.00</td><td>2.50</td></tr>
<tr><td>PTILIIDAE</td><td>Ptinella aptera</td><td>0.80</td><td>2.50</td><td>4.00</td><td>2.50</td></tr>
<tr><td>PTILIIDAE</td><td>Ptinella tenella</td><td>0.50</td><td>2.50</td><td>4.00</td><td>2.50</td></tr>
<tr><td>PTILIIDAE</td><td>Ptinella errabunda</td><td>0.80</td><td>2.50</td><td>4.00</td><td>2.50</td></tr>
<tr><td>PTILIIDAE</td><td>Pteryx suturalis</td><td>0.80</td><td>3.00</td><td>4.13</td><td>2.50</td></tr>
<tr><td>PTILIIDAE</td><td>Baeocrara variolosa</td><td>0.90</td><td>2.29</td><td>4.50</td><td>2.50</td></tr>
<tr><td>STAPHYLINIDAE</td><td>Scaphidium quadrimaculatum</td><td>5.00</td><td>2.33</td><td>4.00</td><td>2.60</td></tr>
<tr><td>STAPHYLINIDAE</td><td>Scaphisoma agaricinum</td><td>1.00</td><td>2.33</td><td>4.00</td><td>2.60</td></tr>
<tr><td>STAPHYLINIDAE</td><td>Scaphisoma boreale</td><td>2.50</td><td>3.00</td><td>4.60</td><td>2.60</td></tr>
<tr><td>STAPHYLINIDAE</td><td>Phloeocharis subtilissima</td><td>1.00</td><td>2.33</td><td>3.00</td><td>1.50</td></tr>
<tr><td>STAPHYLINIDAE</td><td>Acrulia inflata</td><td>2.00</td><td>2.60</td><td>3.67</td><td>2.50</td></tr>
<tr><td>STAPHYLINIDAE</td><td>Phyllodrepa melanocephala</td><td>4.00</td><td>3.40</td><td>4.00</td><td>2.00</td></tr>
<tr><td>STAPHYLINIDAE</td><td>Hapalaraea pygmaea</td><td>2.00</td><td>3.75</td><td>4.00</td><td>2.00</td></tr>
<tr><td>STAPHYLINIDAE</td><td>Phloeonomus punctipennis</td><td>1.00</td><td>2.00</td><td>2.50</td><td>1.50</td></tr>
<tr><td>STAPHYLINIDAE</td><td>Nudobius lentus</td><td>7.00</td><td>2.60</td><td>2.25</td><td>1.60</td></tr>
<tr><td>STAPHYLINIDAE</td><td>Atrecus affinis</td><td>6.00</td><td>2.60</td><td>4.00</td><td>2.60</td></tr>
<tr><td>STAPHYLINIDAE</td><td>Hesperus rufipennis</td><td>9.00</td><td>3.75</td><td>4.50</td><td>2.00</td></tr>
<tr><td>STAPHYLINIDAE</td><td>Gabrius splendidulus</td><td>5.00</td><td>2.60</td><td>3.71</td><td>2.50</td></tr>
<tr><td>STAPHYLINIDAE</td><td>Velleius dilatatus</td><td>19.00</td><td>3.75</td><td>4.60</td><td>1.60</td></tr>
<tr><td>STAPHYLINIDAE</td><td>Quedius truncicola</td><td>11.00</td><td>3.75</td><td>4.50</td><td>2.17</td></tr>
<tr><td>STAPHYLINIDAE</td><td>Quedius microps</td><td>4.00</td><td>3.40</td><td>4.00</td><td>2.25</td></tr>
<tr><td>STAPHYLINIDAE</td><td>Quedius brevicornis</td><td>10.00</td><td>3.75</td><td>4.50</td><td>2.00</td></tr>
<tr><td>STAPHYLINIDAE</td><td>Quedius maurus</td><td>7.00</td><td>2.33</td><td>4.60</td><td>2.17</td></tr>
<tr><td>STAPHYLINIDAE</td><td>Quedius xanthopus</td><td>8.00</td><td>2.67</td><td>3.67</td><td>2.40</td></tr>
<tr><td>STAPHYLINIDAE</td><td>Sepedophilus testaceus</td><td>4.00</td><td>2.33</td><td>4.13</td><td>2.00</td></tr>
<tr><td>STAPHYLINIDAE</td><td>Gyrophaena minima</td><td>1.00</td><td>2.60</td><td>3.67</td><td>2.40</td></tr>
<tr><td>STAPHYLINIDAE</td><td>Gyrophaena strictula</td><td>1.00</td><td>2.60</td><td>3.25</td><td>2.17</td></tr>
<tr><td>STAPHYLINIDAE</td><td>Gyrophaena boleti</td><td>1.00</td><td>2.60</td><td>3.25</td><td>2.40</td></tr>
<tr><td>STAPHYLINIDAE</td><td>Agaricochara latissima</td><td>1.00</td><td>2.60</td><td>3.25</td><td>2.40</td></tr>
<tr><td>STAPHYLINIDAE</td><td>Placusa depressa</td><td>2.00</td><td>2.60</td><td>2.25</td><td>1.50</td></tr>
<tr><td>STAPHYLINIDAE</td><td>Placusa tachyporoides</td><td>2.00</td><td>2.60</td><td>1.60</td><td>1.60</td></tr>
<tr><td>STAPHYLINIDAE</td><td>Anomognathus cuspidatus</td><td>1.00</td><td>2.33</td><td>2.75</td><td>1.60</td></tr>
<tr><td>STAPHYLINIDAE</td><td>Leptusa pulchella</td><td>2.00</td><td>2.60</td><td>3.80</td><td>1.83</td></tr>
<tr><td>STAPHYLINIDAE</td><td>Leptusa fumida</td><td>2.00</td><td>2.60</td><td>3.80</td><td>2.50</td></tr>
<tr><td>STAPHYLINIDAE</td><td>Euryusa castanoptera</td><td>3.00</td><td>3.00</td><td>2.00</td><td>1.75</td></tr>
<tr><td>STAPHYLINIDAE</td><td>Euryusa optabilis</td><td>2.00</td><td>3.00</td><td>4.00</td><td>1.50</td></tr>
<tr><td>STAPHYLINIDAE</td><td>Bolitochara obliqua</td><td>3.00</td><td>2.33</td><td>3.25</td><td>2.50</td></tr>
<tr><td>STAPHYLINIDAE</td><td>Bolitochara lucida</td><td>4.00</td><td>2.33</td><td>3.83</td><td>2.50</td></tr>
<tr><td>STAPHYLINIDAE</td><td>Dinaraea aequata</td><td>2.00</td><td>2.60</td><td>3.50</td><td>2.50</td></tr>
<tr><td>STAPHYLINIDAE</td><td>Dadobia immersa</td><td>1.00</td><td>1.25</td><td>2.50</td><td>1.40</td></tr>
<tr><td>STAPHYLINIDAE</td><td>Atheta picipes</td><td>2.00</td><td>3.00</td><td>3.25</td><td>2.17</td></tr>
<tr><td>STAPHYLINIDAE</td><td>Phloeopora testacea</td><td>2.00</td><td>2.00</td><td>2.25</td><td>1.50</td></tr>
<tr><td>STAPHYLINIDAE</td><td>Phloeopora corticalis</td><td>2.00</td><td>2.00</td><td>2.25</td><td>1.50</td></tr>
<tr><td>STAPHYLINIDAE</td><td>Phloeopora scribae</td><td>2.00</td><td>2.00</td><td>2.25</td><td>1.50</td></tr>
<tr><td>STAPHYLINIDAE</td><td>Ischnoglossa prolixa</td><td>2.00</td><td>2.33</td><td>3.25</td><td>2.00</td></tr>
<tr><td>PSELAPHIDAE</td><td>Bibloporus bicolor</td><td>1.00</td><td>3.00</td><td>3.40</td><td>2.40</td></tr>
<tr><td>PSELAPHIDAE</td><td>Euplectus nanus</td><td>1.00</td><td>3.00</td><td>4.00</td><td>2.20</td></tr>
<tr><td>PSELAPHIDAE</td><td>Euplectus karsteni</td><td>1.00</td><td>3.00</td><td>4.13</td><td>1.80</td></tr>
<tr><td>PSELAPHIDAE</td><td>Euplectus fauveli</td><td>1.00</td><td>3.40</td><td>4.33</td><td>2.00</td></tr>
<tr><td>PSELAPHIDAE</td><td>Plectophloeus fischeri</td><td>1.00</td><td>3.00</td><td>4.17</td><td>2.50</td></tr>
<tr><td>LYCIDAE</td><td>Dictyopterus aurora</td><td>10.00</td><td>2.50</td><td>4.00</td><td>2.40</td></tr>
<tr><td>LYCIDAE</td><td>Pyropterus nigroruber</td><td>8.00</td><td>2.50</td><td>4.00</td><td>1.50</td></tr>
<tr><td>LYCIDAE</td><td>Platycis minutus</td><td>7.00</td><td>2.50</td><td>4.00</td><td>2.40</td></tr>
<tr><td>LYCIDAE</td><td>Platycis cosnardi</td><td>7.00</td><td>3.80</td><td>3.60</td><td>2.50</td></tr>
<tr><td>LYCIDAE</td><td>Lygistopterus sanguineus</td><td>9.00</td><td>2.50</td><td>3.50</td><td>1.40</td></tr>
<tr><td>CANTHARIDAE</td><td>Malthinus punctatus</td><td>5.00</td><td>2.29</td><td>3.20</td><td>1.67</td></tr>
<tr><td>CANTHARIDAE</td><td>Malthinus seriepunctatus</td><td>4.00</td><td>2.29</td><td>3.20</td><td>1.67</td></tr>
<tr><td>CANTHARIDAE</td><td>Malthinus fasciatus</td><td>4.00</td><td>2.29</td><td>3.20</td><td>1.67</td></tr>
<tr><td>CANTHARIDAE</td><td>Malthinus balteatus</td><td>3.00</td><td>2.29</td><td>3.20</td><td>1.67</td></tr>
<tr><td>CANTHARIDAE</td><td>Malthinus facialis</td><td>3.00</td><td>2.29</td><td>3.20</td><td>1.67</td></tr>
<tr><td>CANTHARIDAE</td><td>Malthinus biguttatus</td><td>5.00</td><td>2.29</td><td>3.20</td><td>1.67</td></tr>
<tr><td>CANTHARIDAE</td><td>Malthinus frontalis</td><td>4.00</td><td>2.29</td><td>3.20</td><td>1.67</td></tr>
<tr><td>CANTHARIDAE</td><td>Malthodes flavoguttatus</td><td>4.00</td><td>2.29</td><td>3.20</td><td>1.67</td></tr>
<tr><td>CANTHARIDAE</td><td>Malthodes dispar</td><td>4.00</td><td>2.29</td><td>3.20</td><td>1.67</td></tr>
<tr><td>CANTHARIDAE</td><td>Malthodes maurus</td><td>3.00</td><td>2.29</td><td>3.20</td><td>1.67</td></tr>
<tr><td>CANTHARIDAE</td><td>Malthodes fuscus</td><td>4.00</td><td>2.29</td><td>3.20</td><td>1.67</td></tr>
<tr><td>CANTHARIDAE</td><td>Malthodes spretus</td><td>4.00</td><td>2.29</td><td>3.20</td><td>1.67</td></tr>
<tr><td>CANTHARIDAE</td><td>Malthodes alpicola</td><td>4.00</td><td>2.29</td><td>3.20</td><td>1.67</td></tr>
<tr><td>CANTHARIDAE</td><td>Malthodes guttifer</td><td>4.00</td><td>2.29</td><td>3.20</td><td>1.67</td></tr>
<tr><td>CANTHARIDAE</td><td>Malthodes marginatus</td><td>4.00</td><td>2.29</td><td>3.20</td><td>1.50</td></tr>
<tr><td>CANTHARIDAE</td><td>Malthodes mysticus</td><td>4.00</td><td>2.29</td><td>3.20</td><td>1.67</td></tr>
<tr><td>CANTHARIDAE</td><td>Malthodes hexacanthus</td><td>2.00</td><td>2.29</td><td>3.20</td><td>1.67</td></tr>
<tr><td>CANTHARIDAE</td><td>Malthodes pumilus</td><td>1.00</td><td>2.29</td><td>3.20</td><td>1.50</td></tr>
<tr><td>CANTHARIDAE</td><td>Malthodes spathifer</td><td>3.00</td><td>2.29</td><td>3.20</td><td>1.50</td></tr>
<tr><td>CANTHARIDAE</td><td>Malthodes crassicornis</td><td>2.00</td><td>2.29</td><td>3.20</td><td>1.67</td></tr>
<tr><td>CANTHARIDAE</td><td>Malthodes holdhausi</td><td>2.00</td><td>2.29</td><td>3.20</td><td>1.75</td></tr>
<tr><td>CANTHARIDAE</td><td>Malthodes brevicollis</td><td>2.00</td><td>2.29</td><td>3.20</td><td>1.67</td></tr>
<tr><td>MALACHIIDAE</td><td>Hypebaeus flavipes</td><td>1.00</td><td>3.20</td><td>3.50</td><td>1.50</td></tr>
<tr><td>MALACHIIDAE</td><td>Malachius bipustulatus</td><td>5.00</td><td>2.29</td><td>3.20</td><td>1.50</td></tr>
<tr><td>MELYRIDAE</td><td>Aplocnemus impressus</td><td>4.00</td><td>3.20</td><td>3.25</td><td>1.50</td></tr>
<tr><td>MELYRIDAE</td><td>Aplocnemus nigricornis</td><td>4.00</td><td>2.29</td><td>2.50</td><td>1.50</td></tr>
<tr><td>MELYRIDAE</td><td>Aplocnemus tarsalis</td><td>5.00</td><td>2.29</td><td>2.50</td><td>1.50</td></tr>
<tr><td>MELYRIDAE</td><td>Aplocnemus alpestris</td><td>5.00</td><td>2.29</td><td>2.50</td><td>1.50</td></tr>
<tr><td>MELYRIDAE</td><td>Trichoceble floralis</td><td>5.00</td><td>2.71</td><td>2.75</td><td>1.00</td></tr>
<tr><td>MELYRIDAE</td><td>Dasytes niger</td><td>4.00</td><td>2.29</td><td>3.20</td><td>1.00</td></tr>
<tr><td>MELYRIDAE</td><td>Dasytes obscurus</td><td>5.00</td><td>1.86</td><td>3.20</td><td>1.50</td></tr>
<tr><td>MELYRIDAE</td><td>Dasytes cyaneus</td><td>5.00</td><td>1.86</td><td>3.20</td><td>2.00</td></tr>
<tr><td>MELYRIDAE</td><td>Dasytes virens</td><td>4.00</td><td>1.86</td><td>3.20</td><td>1.50</td></tr>
<tr><td>MELYRIDAE</td><td>Dasytes plumbeus</td><td>4.00</td><td>1.86</td><td>3.20</td><td>1.50</td></tr>
<tr><td>MELYRIDAE</td><td>Dasytes aeratus</td><td>4.00</td><td>1.86</td><td>3.20</td><td>1.00</td></tr>
<tr><td>MELYRIDAE</td><td>Dasytes fusculus</td><td>4.00</td><td>1.86</td><td>3.20</td><td>1.00</td></tr>
<tr><td>CLERIDAE</td><td>Tillus elongatus</td><td>8.00</td><td>2.71</td><td>3.00</td><td>1.50</td></tr>
<tr><td>CLERIDAE</td><td>Opilo mollis</td><td>10.00</td><td>2.50</td><td>3.00</td><td>1.50</td></tr>
<tr><td>CLERIDAE</td><td>Thanasimus formicarius</td><td>8.00</td><td>2.29</td><td>2.25</td><td>1.50</td></tr>
<tr><td>CLERIDAE</td><td>Thanasimus rufipes</td><td>6.00</td><td>2.00</td><td>2.25</td><td>1.40</td></tr>
<tr><td>CLERIDAE</td><td>Thanasimus pectoralis</td><td>6.00</td><td>2.29</td><td>2.25</td><td>1.40</td></tr>
<tr><td>CLERIDAE</td><td>Clerus mutillarius</td><td>12.00</td><td>3.00</td><td>2.00</td><td>1.40</td></tr>
<tr><td>CLERIDAE</td><td>Dermestoides sanguinicollis</td><td>8.00</td><td>3.80</td><td>3.00</td><td>1.40</td></tr>
<tr><td>TROGOSSITIDAE</td><td>Nemosoma elongatum</td><td>5.00</td><td>2.00</td><td>2.00</td><td>1.40</td></tr>
<tr><td>TROGOSSITIDAE</td><td>Tenebroides fuscus</td><td>8.00</td><td>2.71</td><td>2.80</td><td>1.40</td></tr>
<tr><td>PELTIDAE</td><td>Peltis grossa</td><td>15.00</td><td>3.00</td><td>3.40</td><td>1.40</td></tr>
<tr><td>PELTIDAE</td><td>Ostoma ferruginea</td><td>8.00</td><td>3.00</td><td>3.40</td><td>1.40</td></tr>
<tr><td>PELTIDAE</td><td>Thymalus limbatus</td><td>6.00</td><td>2.50</td><td>3.25</td><td>2.00</td></tr>
<tr><td>LOPHOCATERIDAE</td><td>Grynocharis oblonga</td><td>6.00</td><td>3.00</td><td>3.00</td><td>1.50</td></tr>
<tr><td>LYMEXYLONIDAE</td><td>Hylecoetus dermestoides</td><td>12.00</td><td>3.00</td><td>2.00</td><td>1.50</td></tr>
<tr><td>LYMEXYLONIDAE</td><td>Hylecoetus flabellicornis</td><td>8.00</td><td>3.00</td><td>2.00</td><td>1.80</td></tr>
<tr><td>LYMEXYLONIDAE</td><td>Lymexylon navale</td><td>11.00</td><td>3.00</td><td>2.00</td><td>1.40</td></tr>
<tr><td>ELATERIDAE</td><td>Ampedus sinuatus</td><td>8.00</td><td>3.00</td><td>3.40</td><td>1.50</td></tr>
<tr><td>ELATERIDAE</td><td>Ampedus erythrogonus</td><td>6.00</td><td>3.50</td><td>3.86</td><td>2.50</td></tr>
<tr><td>ELATERIDAE</td><td>Ampedus rufipennis</td><td>11.00</td><td>3.00</td><td>3.40</td><td>1.50</td></tr>
<tr><td>ELATERIDAE</td><td>Ampedus balteatus</td><td>8.00</td><td>2.50</td><td>3.40</td><td>1.50</td></tr>
<tr><td>ELATERIDAE</td><td>Ampedus praeustus</td><td>11.00</td><td>3.50</td><td>3.40</td><td>1.40</td></tr>
<tr><td>ELATERIDAE</td><td>Ampedus aethiops</td><td>10.00</td><td>2.50</td><td>3.40</td><td>1.50</td></tr>
<tr><td>ELATERIDAE</td><td>Ampedus nigerrimus</td><td>9.00</td><td>3.00</td><td>3.50</td><td>2.50</td></tr>
<tr><td>ELATERIDAE</td><td>Ampedus sanguineus</td><td>14.00</td><td>3.00</td><td>3.40</td><td>1.50</td></tr>
<tr><td>ELATERIDAE</td><td>Ampedus cinnabarinus</td><td>13.00</td><td>3.00</td><td>3.40</td><td>1.40</td></tr>
<tr><td>ELATERIDAE</td><td>Ampedus pomonae</td><td>9.00</td><td>2.00</td><td>3.50</td><td>1.00</td></tr>
<tr><td>ELATERIDAE</td><td>Ampedus sanguinolentus</td><td>10.00</td><td>2.29</td><td>3.40</td><td>2.00</td></tr>
<tr><td>ELATERIDAE</td><td>Ampedus pomorum</td><td>10.00</td><td>2.50</td><td>3.67</td><td>2.00</td></tr>
<tr><td>ELATERIDAE</td><td>Ampedus quercicola</td><td>10.00</td><td>2.50</td><td>3.40</td><td>1.50</td></tr>
<tr><td>ELATERIDAE</td><td>Ampedus nigroflavus</td><td>11.00</td><td>3.00</td><td>3.40</td><td>1.40</td></tr>
<tr><td>ELATERIDAE</td><td>Ampedus elongatulus</td><td>7.00</td><td>2.50</td><td>3.67</td><td>1.50</td></tr>
<tr><td>ELATERIDAE</td><td>Ampedus melanurus</td><td>8.00</td><td>3.00</td><td>3.40</td><td>1.50</td></tr>
<tr><td>ELATERIDAE</td><td>Ampedus elegantulus</td><td>9.00</td><td>3.50</td><td>3.40</td><td>2.50</td></tr>
<tr><td>ELATERIDAE</td><td>Ampedus nigrinus</td><td>8.00</td><td>2.50</td><td>3.67</td><td>2.50</td></tr>
<tr><td>ELATERIDAE</td><td>Ampedus auripes</td><td>9.00</td><td>3.00</td><td>3.40</td><td>1.50</td></tr>
<tr><td>ELATERIDAE</td><td>Brachygonus megerlei</td><td>10.00</td><td>3.80</td><td>4.60</td><td>1.80</td></tr>
<tr><td>ELATERIDAE</td><td>Ischnodes sanguinicollis</td><td>9.00</td><td>4.00</td><td>5.00</td><td>2.17</td></tr>
<tr><td>ELATERIDAE</td><td>Procraerus tibialis</td><td>8.00</td><td>3.00</td><td>3.40</td><td>1.50</td></tr>
<tr><td>ELATERIDAE</td><td>Elater ferrugineus</td><td>20.00</td><td>4.00</td><td>5.00</td><td>1.83</td></tr>
<tr><td>ELATERIDAE</td><td>Melanotus rufipes</td><td>15.00</td><td>3.00</td><td>3.67</td><td>2.40</td></tr>
<tr><td>ELATERIDAE</td><td>Melanotus castanipes</td><td>17.00</td><td>3.00</td><td>3.67</td><td>2.40</td></tr>
<tr><td>ELATERIDAE</td><td>Melanotus crassicollis</td><td>15.00</td><td>2.50</td><td>3.88</td><td>1.40</td></tr>
<tr><td>ELATERIDAE</td><td>Lacon lepidopterus</td><td>15.00</td><td>3.00</td><td>3.40</td><td>1.00</td></tr>
<tr><td>ELATERIDAE</td><td>Lacon querceus</td><td>10.00</td><td>3.80</td><td>3.40</td><td>1.80</td></tr>
<tr><td>ELATERIDAE</td><td>Anostirus purpureus</td><td>11.00</td><td>2.50</td><td>3.40</td><td>1.40</td></tr>
<tr><td>ELATERIDAE</td><td>Anostirus castaneus</td><td>9.00</td><td>2.50</td><td>3.40</td><td>1.40</td></tr>
<tr><td>ELATERIDAE</td><td>Anostirus sulphuripennis</td><td>11.00</td><td>2.50</td><td>3.40</td><td>1.40</td></tr>
<tr><td>ELATERIDAE</td><td>Calambus bipustulatus</td><td>7.00</td><td>2.71</td><td>3.50</td><td>1.50</td></tr>
<tr><td>ELATERIDAE</td><td>Hypoganus inunctus</td><td>9.00</td><td>3.00</td><td>3.40</td><td>1.60</td></tr>
<tr><td>ELATERIDAE</td><td>Denticollis rubens</td><td>13.00</td><td>2.29</td><td>3.40</td><td>2.60</td></tr>
<tr><td>ELATERIDAE</td><td>Denticollis linearis</td><td>10.00</td><td>2.50</td><td>3.40</td><td>2.50</td></tr>
<tr><td>ELATERIDAE</td><td>Diacanthous undulatus</td><td>15.00</td><td>3.00</td><td>3.40</td><td>2.50</td></tr>
<tr><td>ELATERIDAE</td><td>Stenagostus rhombeus</td><td>18.00</td><td>2.71</td><td>3.40</td><td>1.60</td></tr>
<tr><td>ELATERIDAE</td><td>Crepidophorus mutilatus</td><td>14.00</td><td>3.80</td><td>4.60</td><td>1.80</td></tr>
<tr><td>CEROPHYTIDAE</td><td>Cerophytum elateroides</td><td>6.00</td><td>3.50</td><td>3.50</td><td>1.50</td></tr>
<tr><td>EUCNEMIDAE</td><td>Melasis buprestoides</td><td>7.00</td><td>2.29</td><td>3.00</td><td>1.40</td></tr>
<tr><td>EUCNEMIDAE</td><td>Isorhipis melasoides</td><td>9.00</td><td>3.00</td><td>2.00</td><td>1.40</td></tr>
<tr><td>EUCNEMIDAE</td><td>Isorhipis marmottani</td><td>6.00</td><td>2.29</td><td>3.00</td><td>1.50</td></tr>
<tr><td>EUCNEMIDAE</td><td>Eucnemis capucina</td><td>5.00</td><td>3.80</td><td>3.50</td><td>1.50</td></tr>
<tr><td>EUCNEMIDAE</td><td>Dromaeolus barnabita</td><td>5.00</td><td>2.29</td><td>3.60</td><td>1.00</td></tr>
<tr><td>EUCNEMIDAE</td><td>Dirhagus pygmaeus</td><td>5.00</td><td>2.29</td><td>3.50</td><td>2.00</td></tr>
<tr><td>EUCNEMIDAE</td><td>Dirhagus lepidus</td><td>5.00</td><td>2.29</td><td>3.50</td><td>2.25</td></tr>
<tr><td>EUCNEMIDAE</td><td>Nematodes filum</td><td>5.00</td><td>3.00</td><td>3.00</td><td>1.00</td></tr>
<tr><td>EUCNEMIDAE</td><td>Epiphanis cornutus</td><td>5.00</td><td>2.50</td><td>3.50</td><td>1.50</td></tr>
<tr><td>EUCNEMIDAE</td><td>Hylis olexai</td><td>4.00</td><td>3.00</td><td>3.50</td><td>1.50</td></tr>
<tr><td>EUCNEMIDAE</td><td>Hylis cariniceps</td><td>5.00</td><td>2.29</td><td>3.50</td><td>2.17</td></tr>
<tr><td>EUCNEMIDAE</td><td>Hylis foveicollis</td><td>5.00</td><td>2.29</td><td>3.50</td><td>1.80</td></tr>
<tr><td>EUCNEMIDAE</td><td>Hylis procerulus</td><td>4.00</td><td>2.50</td><td>3.50</td><td>1.50</td></tr>
<tr><td>EUCNEMIDAE</td><td>Xylophilus corticalis</td><td>5.00</td><td>2.71</td><td>3.50</td><td>1.40</td></tr>
<tr><td>EUCNEMIDAE</td><td>Xylophilus testaceus</td><td>3.00</td><td>2.71</td><td>3.50</td><td>1.40</td></tr>
<tr><td>LISSOMIDAE</td><td>Drapetes cinctus</td><td>4.00</td><td>2.50</td><td>3.50</td><td>1.00</td></tr>
<tr><td>BUPRESTIDAE</td><td>Melanophila acuminata</td><td>9.00</td><td>2.00</td><td>1.75</td><td>1.00</td></tr>
<tr><td>BUPRESTIDAE</td><td>Anthaxia salicis</td><td>6.00</td><td>1.20</td><td>2.00</td><td>1.00</td></tr>
<tr><td>BUPRESTIDAE</td><td>Anthaxia nitidula</td><td>6.00</td><td>1.00</td><td>1.75</td><td>1.40</td></tr>
<tr><td>BUPRESTIDAE</td><td>Anthaxia quadripunctata</td><td>6.00</td><td>1.20</td><td>1.75</td><td>1.00</td></tr>
<tr><td>BUPRESTIDAE</td><td>Chrysobothris affinis</td><td>12.00</td><td>2.50</td><td>2.00</td><td>1.00</td></tr>
<tr><td>BUPRESTIDAE</td><td>Agrilus biguttatus</td><td>10.00</td><td>2.50</td><td>1.60</td><td>1.40</td></tr>
<tr><td>BUPRESTIDAE</td><td>Agrilus laticornis</td><td>5.00</td><td>1.20</td><td>1.75</td><td>1.40</td></tr>
<tr><td>BUPRESTIDAE</td><td>Agrilus obscuricollis</td><td>4.00</td><td>1.00</td><td>2.00</td><td>1.40</td></tr>
<tr><td>BUPRESTIDAE</td><td>Agrilus angustulus</td><td>5.00</td><td>1.00</td><td>2.00</td><td>1.40</td></tr>
<tr><td>BUPRESTIDAE</td><td>Agrilus sulcicollis</td><td>7.00</td><td>2.00</td><td>1.75</td><td>1.40</td></tr>
<tr><td>BUPRESTIDAE</td><td>Agrilus olivicolor</td><td>4.00</td><td>1.00</td><td>2.00</td><td>1.40</td></tr>
<tr><td>BUPRESTIDAE</td><td>Agrilus viridis</td><td>7.00</td><td>1.80</td><td>1.75</td><td>1.40</td></tr>
<tr><td>BUPRESTIDAE</td><td>Agrilus auricollis</td><td>7.00</td><td>1.00</td><td>1.75</td><td>1.00</td></tr>
<tr><td>CLAMBIDAE</td><td>Calyptomerus alpestris</td><td>1.00</td><td>1.20</td><td>3.29</td><td>2.00</td></tr>
<tr><td>SCIRTIDAE</td><td>Prionocyphon serricornis</td><td>4.00</td><td>3.00</td><td>3.00</td><td>2.50</td></tr>
<tr><td>DERMESTIDAE</td><td>Attagenus schaefferi</td><td>4.00</td><td>3.50</td><td>4.20</td><td>1.50</td></tr>
<tr><td>DERMESTIDAE</td><td>Attagenus punctatus</td><td>4.00</td><td>3.80</td><td>3.50</td><td>1.40</td></tr>
<tr><td>DERMESTIDAE</td><td>Globicornis nigripes</td><td>2.00</td><td>3.20</td><td>3.50</td><td>1.40</td></tr>
<tr><td>DERMESTIDAE</td><td>Globicornis corticalis</td><td>3.00</td><td>3.20</td><td>3.50</td><td>1.40</td></tr>
<tr><td>DERMESTIDAE</td><td>Megatoma undata</td><td>5.00</td><td>3.00</td><td>3.50</td><td>1.50</td></tr>
<tr><td>DERMESTIDAE</td><td>Trinodes hirtus</td><td>2.00</td><td>3.80</td><td>3.50</td><td>1.75</td></tr>
<tr><td>NOSODENDRIDAE</td><td>Nosodendron fasciculare</td><td>4.00</td><td>3.00</td><td>1.50</td><td>1.83</td></tr>
<tr><td>BOTHRIDERIDAE</td><td>Teredus cylindricus</td><td>4.00</td><td>3.20</td><td>2.50</td><td>2.00</td></tr>
<tr><td>BOTHRIDERIDAE</td><td>Oxylaemus cylindricus</td><td>3.00</td><td>3.00</td><td>2.00</td><td>1.50</td></tr>
<tr><td>BOTHRIDERIDAE</td><td>Oxylaemus variolosus</td><td>3.00</td><td>3.80</td><td>4.13</td><td>2.00</td></tr>
<tr><td>CERYLONIDAE</td><td>Philothermus evanescens</td><td>2.00</td><td>3.00</td><td>4.00</td><td>2.40</td></tr>
<tr><td>CERYLONIDAE</td><td>Cerylon fagi</td><td>2.00</td><td>3.00</td><td>3.67</td><td>2.50</td></tr>
<tr><td>CERYLONIDAE</td><td>Cerylon histeroides</td><td>2.00</td><td>2.50</td><td>3.67</td><td>2.50</td></tr>
<tr><td>CERYLONIDAE</td><td>Cerylon ferrugineum</td><td>1.00</td><td>2.50</td><td>2.40</td><td>1.50</td></tr>
<tr><td>CERYLONIDAE</td><td>Cerylon deplanatum</td><td>1.00</td><td>2.50</td><td>2.00</td><td>1.40</td></tr>
<tr><td>NITIDULIDAE</td><td>Soronia oblonga</td><td>6.00</td><td>2.50</td><td>1.50</td><td>2.00</td></tr>
<tr><td>NITIDULIDAE</td><td>Carpophilus sexpustulatus</td><td>2.00</td><td>2.29</td><td>1.60</td><td>1.50</td></tr>
<tr><td>NITIDULIDAE</td><td>Epuraea guttata</td><td>3.00</td><td>3.00</td><td>1.14</td><td>2.00</td></tr>
<tr><td>NITIDULIDAE</td><td>Epuraea fuscicollis</td><td>3.00</td><td>3.00</td><td>1.14</td><td>2.00</td></tr>
<tr><td>NITIDULIDAE</td><td>Epuraea neglecta</td><td>2.00</td><td>2.20</td><td>1.60</td><td>1.60</td></tr>
<tr><td>NITIDULIDAE</td><td>Epuraea pallescens</td><td>2.00</td><td>2.00</td><td>1.60</td><td>1.60</td></tr>
<tr><td>NITIDULIDAE</td><td>Epuraea laeviuscula</td><td>3.00</td><td>2.50</td><td>2.00</td><td>1.40</td></tr>
<tr><td>NITIDULIDAE</td><td>Epuraea deubeli</td><td>2.00</td><td>3.00</td><td>2.00</td><td>1.50</td></tr>
<tr><td>NITIDULIDAE</td><td>Epuraea thoracica</td><td>3.00</td><td>1.80</td><td>2.00</td><td>1.50</td></tr>
<tr><td>NITIDULIDAE</td><td>Epuraea angustula</td><td>2.00</td><td>2.50</td><td>2.00</td><td>1.40</td></tr>
<tr><td>NITIDULIDAE</td><td>Epuraea boreella</td><td>2.00</td><td>2.00</td><td>2.00</td><td>1.50</td></tr>
<tr><td>NITIDULIDAE</td><td>Epuraea marseuli</td><td>3.00</td><td>2.20</td><td>2.25</td><td>1.50</td></tr>
<tr><td>NITIDULIDAE</td><td>Epuraea pygmaea</td><td>2.00</td><td>2.00</td><td>2.00</td><td></td></tr>
<tr><td>NITIDULIDAE</td><td>Epuraea longula</td><td>2.00</td><td>2.20</td><td>1.60</td><td>1.60</td></tr>
<tr><td>NITIDULIDAE</td><td>Epuraea binotata</td><td>2.00</td><td>1.20</td><td>2.25</td><td>2.00</td></tr>
<tr><td>NITIDULIDAE</td><td>Epuraea terminalis</td><td>3.00</td><td>2.00</td><td>1.75</td><td>1.60</td></tr>
<tr><td>NITIDULIDAE</td><td>Epuraea biguttata</td><td>3.00</td><td>2.80</td><td>1.83</td><td>1.50</td></tr>
<tr><td>NITIDULIDAE</td><td>Epuraea variegata</td><td>2.00</td><td>2.50</td><td>3.40</td><td>2.50</td></tr>
<tr><td>NITIDULIDAE</td><td>Epuraea muehli</td><td>2.00</td><td>1.20</td><td>2.00</td><td>1.50</td></tr>
<tr><td>NITIDULIDAE</td><td>Epuraea silacea</td><td>3.00</td><td>3.00</td><td>3.40</td><td>2.17</td></tr>
<tr><td>NITIDULIDAE</td><td>Epuraea rufomarginata</td><td>3.00</td><td>1.20</td><td>2.00</td><td>1.60</td></tr>
<tr><td>NITIDULIDAE</td><td>Amphotis marginata</td><td>4.00</td><td>4.00</td><td>4.00</td><td>1.50</td></tr>
<tr><td>NITIDULIDAE</td><td>Ipidia binotata</td><td>4.00</td><td>3.00</td><td>2.50</td><td>1.50</td></tr>
<tr><td>NITIDULIDAE</td><td>Cyllodes ater</td><td>4.00</td><td>3.00</td><td>2.60</td><td>1.60</td></tr>
<tr><td>NITIDULIDAE</td><td>Cychramus variegatus</td><td>6.00</td><td>3.00</td><td>3.40</td><td>2.00</td></tr>
<tr><td>NITIDULIDAE</td><td>Cychramus luteus</td><td>4.00</td><td>2.50</td><td>3.40</td><td>2.00</td></tr>
<tr><td>NITIDULIDAE</td><td>Cryptarcha strigata</td><td>3.00</td><td>2.50</td><td>1.14</td><td>2.00</td></tr>
<tr><td>NITIDULIDAE</td><td>Cryptarcha undata</td><td>2.00</td><td>2.50</td><td>1.14</td><td>2.00</td></tr>
<tr><td>NITIDULIDAE</td><td>Glischrochilus quadriguttatus</td><td>4.00</td><td>2.20</td><td>1.50</td><td>1.60</td></tr>
<tr><td>NITIDULIDAE</td><td>Glischrochilus quadripunctatus</td><td>4.00</td><td>2.29</td><td>2.00</td><td>1.50</td></tr>
<tr><td>NITIDULIDAE</td><td>Pityophagus ferrugineus</td><td>5.00</td><td>2.50</td><td>2.00</td><td>1.50</td></tr>
<tr><td>MONOTOMIDAE</td><td>Rhizophagus grandis</td><td>5.00</td><td>3.00</td><td>2.00</td><td>1.50</td></tr>
<tr><td>MONOTOMIDAE</td><td>Rhizophagus depressus</td><td>3.00</td><td>2.50</td><td>2.00</td><td>1.40</td></tr>
<tr><td>MONOTOMIDAE</td><td>Rhizophagus ferrugineus</td><td>3.00</td><td>2.50</td><td>2.00</td><td>2.00</td></tr>
<tr><td>MONOTOMIDAE</td><td>Rhizophagus parallelocollis</td><td>3.00</td><td>2.29</td><td>3.50</td><td>2.60</td></tr>
<tr><td>MONOTOMIDAE</td><td>Rhizophagus perforatus</td><td>3.00</td><td>2.50</td><td>2.00</td><td>1.60</td></tr>
<tr><td>MONOTOMIDAE</td><td>Rhizophagus picipes</td><td>3.00</td><td>2.00</td><td>2.25</td><td>1.50</td></tr>
<tr><td>MONOTOMIDAE</td><td>Rhizophagus dispar</td><td>3.00</td><td>2.50</td><td>2.50</td><td>1.60</td></tr>
<tr><td>MONOTOMIDAE</td><td>Rhizophagus bipustulatus</td><td>2.00</td><td>2.50</td><td>2.50</td><td>1.60</td></tr>
<tr><td>MONOTOMIDAE</td><td>Rhizophagus nitidulus</td><td>3.00</td><td>2.29</td><td>2.80</td><td>2.00</td></tr>
<tr><td>MONOTOMIDAE</td><td>Rhizophagus brancsiki</td><td>4.00</td><td>2.67</td><td>4.17</td><td>3.00</td></tr>
<tr><td>MONOTOMIDAE</td><td>Rhizophagus parvulus</td><td>2.00</td><td>3.00</td><td>1.60</td><td>1.60</td></tr>
<tr><td>MONOTOMIDAE</td><td>Rhizophagus cribratus</td><td>3.00</td><td>3.00</td><td>2.71</td><td>2.40</td></tr>
<tr><td>MONOTOMIDAE</td><td>Cyanostolus aeneus</td><td>2.00</td><td>2.00</td><td>2.00</td><td>1.50</td></tr>
<tr><td>CUCUJIDAE</td><td>Cucujus cinnaberinus</td><td>13.00</td><td>3.00</td><td>2.40</td><td>1.50</td></tr>
<tr><td>CUCUJIDAE</td><td>Pediacus depressus</td><td>4.00</td><td>2.50</td><td>2.00</td><td>1.50</td></tr>
<tr><td>CUCUJIDAE</td><td>Pediacus dermestoides</td><td>4.00</td><td>2.50</td><td>2.00</td><td>1.00</td></tr>
<tr><td>SILVANIDAE</td><td>Silvanus bidentatus</td><td>3.00</td><td>2.50</td><td>2.00</td><td>1.40</td></tr>
<tr><td>SILVANIDAE</td><td>Silvanus unidentatus</td><td>2.00</td><td>2.00</td><td>2.00</td><td>1.40</td></tr>
<tr><td>SILVANIDAE</td><td>Silvanoprus fagi</td><td>2.00</td><td>1.00</td><td>2.00</td><td>1.50</td></tr>
<tr><td>SILVANIDAE</td><td>Uleiota planata</td><td>5.00</td><td>2.00</td><td>2.50</td><td>1.50</td></tr>
<tr><td>SILVANIDAE</td><td>Dendrophagus crenatus</td><td>6.00</td><td>2.00</td><td>2.50</td><td>1.50</td></tr>
<tr><td>PHLOEOSTICHIDAE</td><td>Phloeostichus denticollis</td><td>4.00</td><td>2.29</td><td>1.50</td><td>1.50</td></tr>
<tr><td>EROTYLIDAE</td><td>Tritoma bipustulata</td><td>3.00</td><td>2.50</td><td>3.40</td><td>1.50</td></tr>
<tr><td>EROTYLIDAE</td><td>Triplax aenea</td><td>3.00</td><td>3.00</td><td>3.40</td><td>1.50</td></tr>
<tr><td>EROTYLIDAE</td><td>Triplax elongata</td><td>6.00</td><td>3.00</td><td>3.00</td><td>2.00</td></tr>
<tr><td>EROTYLIDAE</td><td>Triplax russica</td><td>5.00</td><td>3.00</td><td>3.40</td><td>2.17</td></tr>
<tr><td>EROTYLIDAE</td><td>Triplax scutellaris</td><td>5.00</td><td>3.00</td><td>3.40</td><td>2.00</td></tr>
<tr><td>EROTYLIDAE</td><td>Triplax carpathica</td><td>4.00</td><td>3.00</td><td>3.40</td><td>2.67</td></tr>
<tr><td>EROTYLIDAE</td><td>Triplax lepida</td><td>4.00</td><td>2.00</td><td>3.40</td><td>2.40</td></tr>
<tr><td>EROTYLIDAE</td><td>Triplax rufipes</td><td>4.00</td><td>2.29</td><td>3.40</td><td>2.40</td></tr>
<tr><td>EROTYLIDAE</td><td>Triplax collaris</td><td>3.00</td><td>2.50</td><td>3.40</td><td>2.40</td></tr>
<tr><td>EROTYLIDAE</td><td>Dacne rufifrons</td><td>2.00</td><td>3.00</td><td>3.17</td><td>1.75</td></tr>
<tr><td>EROTYLIDAE</td><td>Dacne bipustulata</td><td>2.00</td><td>2.50</td><td>3.17</td><td>1.50</td></tr>
<tr><td>BIPHYLLIDAE</td><td>Diplocoelus fagi</td><td>3.00</td><td>2.29</td><td>2.50</td><td>1.50</td></tr>
<tr><td>CRYPTOPHAGIDAE</td><td>Henoticus serratus</td><td>2.00</td><td>2.50</td><td>2.83</td><td>2.00</td></tr>
<tr><td>CRYPTOPHAGIDAE</td><td>Pteryngium crenatum</td><td>1.00</td><td>2.50</td><td>3.00</td><td>2.00</td></tr>
<tr><td>CRYPTOPHAGIDAE</td><td>Cryptophagus cylindrus</td><td>1.00</td><td>1.00</td><td>2.00</td><td>1.00</td></tr>
<tr><td>CRYPTOPHAGIDAE</td><td>Cryptophagus lysholmi</td><td>2.00</td><td>3.00</td><td>4.17</td><td></td></tr>
<tr><td>CRYPTOPHAGIDAE</td><td>Cryptophagus subdepressus</td><td>2.00</td><td>1.50</td><td>2.50</td><td>2.00</td></tr>
<tr><td>CRYPTOPHAGIDAE</td><td>Cryptophagus micaceus</td><td>2.00</td><td>3.80</td><td>4.60</td><td>1.50</td></tr>
<tr><td>CRYPTOPHAGIDAE</td><td>Cryptophagus labilis</td><td>2.00</td><td>3.00</td><td>4.00</td><td>1.50</td></tr>
<tr><td>CRYPTOPHAGIDAE</td><td>Cryptophagus intermedius</td><td>2.00</td><td>1.86</td><td>3.20</td><td>1.50</td></tr>
<tr><td>CRYPTOPHAGIDAE</td><td>Cryptophagus dorsalis</td><td>2.00</td><td>3.20</td><td>4.00</td><td>1.50</td></tr>
<tr><td>CRYPTOPHAGIDAE</td><td>Cryptophagus corticinus</td><td>2.00</td><td>2.00</td><td>2.00</td><td>1.40</td></tr>
<tr><td>CRYPTOPHAGIDAE</td><td>Micrambe abietis</td><td>2.00</td><td>1.00</td><td>2.00</td><td>1.50</td></tr>
<tr><td>CRYPTOPHAGIDAE</td><td>Caenoscelis ferruginea</td><td>1.00</td><td>2.29</td><td>4.00</td><td>2.50</td></tr>
<tr><td>CRYPTOPHAGIDAE</td><td>Caenoscelis sibirica</td><td>2.00</td><td>2.29</td><td>4.00</td><td>2.50</td></tr>
<tr><td>CRYPTOPHAGIDAE</td><td>Atomaria ornata</td><td>1.00</td><td>1.00</td><td>2.00</td><td>2.25</td></tr>
<tr><td>CRYPTOPHAGIDAE</td><td>Atomaria turgida</td><td>1.00</td><td>1.00</td><td>2.00</td><td>2.00</td></tr>
<tr><td>CRYPTOPHAGIDAE</td><td>Atomaria diluta</td><td>1.00</td><td>2.00</td><td>3.29</td><td>2.50</td></tr>
<tr><td>CRYPTOPHAGIDAE</td><td>Atomaria alpina</td><td>1.00</td><td>2.50</td><td>3.25</td><td>2.50</td></tr>
<tr><td>CRYPTOPHAGIDAE</td><td>Atomaria elongatula</td><td>1.00</td><td>3.00</td><td>3.80</td><td>2.50</td></tr>
<tr><td>CRYPTOPHAGIDAE</td><td>Atomaria pulchra</td><td>1.00</td><td>1.20</td><td>2.00</td><td>1.67</td></tr>
<tr><td>CRYPTOPHAGIDAE</td><td>Atomaria atrata</td><td>1.00</td><td>1.00</td><td>2.00</td><td>1.40</td></tr>
<tr><td>CRYPTOPHAGIDAE</td><td>Atomaria procerula</td><td>2.00</td><td>1.00</td><td>2.00</td><td>1.50</td></tr>
<tr><td>CRYPTOPHAGIDAE</td><td>Atomaria bella</td><td>1.00</td><td>2.00</td><td>3.00</td><td>2.50</td></tr>
<tr><td>CRYPTOPHAGIDAE</td><td>Atomaria lohsei</td><td>1.00</td><td>1.20</td><td>2.00</td><td>1.50</td></tr>
<tr><td>LAEMOPHLOEIDAE</td><td>Laemophloeus monilis</td><td>3.00</td><td>2.29</td><td>2.50</td><td>1.50</td></tr>
<tr><td>LAEMOPHLOEIDAE</td><td>Laemophloeus kraussi</td><td>3.00</td><td>1.20</td><td>2.25</td><td>1.40</td></tr>
<tr><td>LAEMOPHLOEIDAE</td><td>Placonotus testaceus</td><td>2.00</td><td>2.20</td><td>2.50</td><td>1.00</td></tr>
<tr><td>LAEMOPHLOEIDAE</td><td>Notolaemus unifasciatus</td><td>1.00</td><td>2.00</td><td>2.00</td><td>1.50</td></tr>
<tr><td>LAEMOPHLOEIDAE</td><td>Cryptolestes duplicatus</td><td>1.00</td><td>2.00</td><td>1.75</td><td>1.60</td></tr>
<tr><td>LAEMOPHLOEIDAE</td><td>Cryptolestes spartii</td><td>1.00</td><td>1.80</td><td>2.25</td><td>1.00</td></tr>
<tr><td>LAEMOPHLOEIDAE</td><td>Leptophloeus alternans</td><td>2.00</td><td>1.20</td><td>2.00</td><td>1.00</td></tr>
<tr><td>LAEMOPHLOEIDAE</td><td>Lathropus sepicola</td><td>1.00</td><td>2.50</td><td>2.40</td><td>1.00</td></tr>
<tr><td>LATRIDIIDAE</td><td>Latridius hirtus</td><td>1.00</td><td>2.20</td><td>4.00</td><td>2.17</td></tr>
<tr><td>LATRIDIIDAE</td><td>Latridius consimilis</td><td>1.00</td><td>3.00</td><td>3.71</td><td>1.75</td></tr>
<tr><td>LATRIDIIDAE</td><td>Latridius brevicollis</td><td>2.00</td><td>3.00</td><td>4.00</td><td>2.00</td></tr>
<tr><td>LATRIDIIDAE</td><td>Enicmus brevicornis</td><td>1.00</td><td>1.86</td><td>2.50</td><td>1.50</td></tr>
<tr><td>LATRIDIIDAE</td><td>Enicmus fungicola</td><td>1.00</td><td>2.50</td><td>3.75</td><td>1.83</td></tr>
<tr><td>LATRIDIIDAE</td><td>Enicmus planipennis</td><td>1.00</td><td>2.00</td><td>3.50</td><td>1.75</td></tr>
<tr><td>LATRIDIIDAE</td><td>Enicmus testaceus</td><td>1.00</td><td>1.67</td><td>3.00</td><td>2.25</td></tr>
<tr><td>LATRIDIIDAE</td><td>Enicmus atriceps</td><td>1.00</td><td>1.86</td><td>3.00</td><td>2.25</td></tr>
<tr><td>LATRIDIIDAE</td><td>Stephostethus pandellei</td><td>2.00</td><td>2.00</td><td>2.40</td><td>2.00</td></tr>
<tr><td>LATRIDIIDAE</td><td>Stephostethus alternans</td><td>2.00</td><td>1.50</td><td>3.00</td><td>2.40</td></tr>
<tr><td>LATRIDIIDAE</td><td>Stephostethus rugicollis</td><td>1.00</td><td>1.00</td><td>2.50</td><td>2.00</td></tr>
<tr><td>LATRIDIIDAE</td><td>Corticaria abietorum</td><td>1.00</td><td>1.00</td><td>2.25</td><td>2.00</td></tr>
<tr><td>LATRIDIIDAE</td><td>Corticaria linearis</td><td>1.00</td><td>1.00</td><td>2.25</td><td>1.75</td></tr>
<tr><td>LATRIDIIDAE</td><td>Corticaria polypori</td><td>1.00</td><td>3.80</td><td>4.00</td><td>1.50</td></tr>
<tr><td>LATRIDIIDAE</td><td>Corticaria alleni</td><td>1.00</td><td>3.20</td><td>3.80</td><td>1.50</td></tr>
<tr><td>LATRIDIIDAE</td><td>Corticaria longicollis</td><td>1.00</td><td>3.00</td><td>4.29</td><td>1.50</td></tr>
<tr><td>LATRIDIIDAE</td><td>Corticarina lambiana</td><td>1.00</td><td>1.20</td><td>2.50</td><td></td></tr>
<tr><td>MYCETOPHAGIDAE</td><td>Eulagius filicornis</td><td>4.00</td><td>2.15</td><td>2.60</td><td>2.60</td></tr>
<tr><td>MYCETOPHAGIDAE</td><td>Triphyllus bicolor</td><td>3.00</td><td>3.00</td><td>3.50</td><td>2.40</td></tr>
<tr><td>MYCETOPHAGIDAE</td><td>Litargus connexus</td><td>2.00</td><td>2.29</td><td>2.75</td><td>1.50</td></tr>
<tr><td>MYCETOPHAGIDAE</td><td>Litargus balteatus</td><td>2.00</td><td>2.00</td><td>3.00</td><td>1.50</td></tr>
<tr><td>MYCETOPHAGIDAE</td><td>Mycetophagus quadripustulatus</td><td>5.00</td><td>2.50</td><td>3.40</td><td>2.40</td></tr>
<tr><td>MYCETOPHAGIDAE</td><td>Mycetophagus ater</td><td>5.00</td><td>3.00</td><td>3.80</td><td>1.75</td></tr>
<tr><td>MYCETOPHAGIDAE</td><td>Mycetophagus piceus</td><td>4.00</td><td>3.00</td><td>3.50</td><td>1.83</td></tr>
<tr><td>MYCETOPHAGIDAE</td><td>Mycetophagus salicis</td><td>4.00</td><td>3.00</td><td>3.50</td><td>1.83</td></tr>
<tr><td>MYCETOPHAGIDAE</td><td>Mycetophagus decempunctatus</td><td>4.00</td><td>3.00</td><td>3.00</td><td>2.00</td></tr>
<tr><td>MYCETOPHAGIDAE</td><td>Mycetophagus atomarius</td><td>4.00</td><td>2.00</td><td>3.17</td><td>2.40</td></tr>
<tr><td>MYCETOPHAGIDAE</td><td>Mycetophagus quadriguttatus</td><td>4.00</td><td>3.75</td><td>4.50</td><td>1.50</td></tr>
<tr><td>MYCETOPHAGIDAE</td><td>Mycetophagus multipunctatus</td><td>4.00</td><td>2.50</td><td>3.50</td><td>2.17</td></tr>
<tr><td>MYCETOPHAGIDAE</td><td>Mycetophagus fulvicollis</td><td>4.00</td><td>3.00</td><td>3.80</td><td>2.00</td></tr>
<tr><td>MYCETOPHAGIDAE</td><td>Mycetophagus populi</td><td>4.00</td><td>3.80</td><td>3.60</td><td>2.00</td></tr>
<tr><td>COLYDIIDAE</td><td>Pycnomerus terebrans</td><td>4.00</td><td>3.80</td><td>4.00</td><td>1.50</td></tr>
<tr><td>COLYDIIDAE</td><td>Endophloeus markovichianus</td><td>6.00</td><td>2.29</td><td>2.83</td><td>1.40</td></tr>
<tr><td>COLYDIIDAE</td><td>Coxelus pictus</td><td>2.00</td><td>1.50</td><td>3.40</td><td>1.50</td></tr>
<tr><td>COLYDIIDAE</td><td>Synchita humeralis</td><td>3.00</td><td>2.29</td><td>3.25</td><td>1.50</td></tr>
<tr><td>COLYDIIDAE</td><td>Synchita separanda</td><td>4.00</td><td>3.00</td><td>3.00</td><td>1.50</td></tr>
<tr><td>COLYDIIDAE</td><td>Cicones variegatus</td><td>2.00</td><td>3.00</td><td>3.40</td><td>2.17</td></tr>
<tr><td>COLYDIIDAE</td><td>Cicones undatus</td><td>2.00</td><td>1.80</td><td>3.25</td><td>1.60</td></tr>
<tr><td>COLYDIIDAE</td><td>Bitoma crenata</td><td>3.00</td><td>2.50</td><td>2.50</td><td>1.00</td></tr>
<tr><td>COLYDIIDAE</td><td>Colydium elongatum</td><td>6.00</td><td>2.50</td><td>2.00</td><td>1.40</td></tr>
<tr><td>CORYLOPHIDAE</td><td>Sacium pusillum</td><td>1.00</td><td>2.50</td><td>3.00</td><td>1.50</td></tr>
<tr><td>CORYLOPHIDAE</td><td>Arthrolips obscurus</td><td>1.00</td><td>2.29</td><td>3.50</td><td>1.50</td></tr>
<tr><td>CORYLOPHIDAE</td><td>Orthoperus punctulatus</td><td>1.00</td><td>1.67</td><td>3.29</td><td>2.20</td></tr>
<tr><td>CORYLOPHIDAE</td><td>Orthoperus atomus</td><td>0.90</td><td>1.86</td><td>3.29</td><td>2.20</td></tr>
<tr><td>CORYLOPHIDAE</td><td>Orthoperus mundus</td><td>0.90</td><td>1.67</td><td>3.29</td><td>2.20</td></tr>
<tr><td>CORYLOPHIDAE</td><td>Orthoperus brunnipes</td><td>0.90</td><td>1.86</td><td>3.29</td><td>2.20</td></tr>
<tr><td>CORYLOPHIDAE</td><td>Orthoperus nigrescens</td><td>0.80</td><td>1.67</td><td>3.29</td><td>2.20</td></tr>
<tr><td>ENDOMYCHIDAE</td><td>Symbiotes latus</td><td>2.00</td><td>3.20</td><td>3.60</td><td>2.17</td></tr>
<tr><td>ENDOMYCHIDAE</td><td>Symbiotes gibberosus</td><td>1.00</td><td>3.20</td><td>3.60</td><td>2.17</td></tr>
<tr><td>ENDOMYCHIDAE</td><td>Symbiotes armatus</td><td>2.00</td><td>3.50</td><td>4.00</td><td>1.00</td></tr>
<tr><td>ENDOMYCHIDAE</td><td>Leiesthes seminigra</td><td>2.00</td><td>3.80</td><td>3.80</td><td>1.40</td></tr>
<tr><td>ENDOMYCHIDAE</td><td>Mycetina cruciata</td><td>4.00</td><td>3.00</td><td>3.50</td><td>2.40</td></tr>
<tr><td>ENDOMYCHIDAE</td><td>Endomychus coccineus</td><td>5.00</td><td>2.29</td><td>3.40</td><td>2.17</td></tr>
<tr><td>ASPIDIPHORIDAE</td><td>Sphindus dubius</td><td>1.00</td><td>2.50</td><td>4.00</td><td>1.50</td></tr>
<tr><td>ASPIDIPHORIDAE</td><td>Arpidiphorus orbiculatus</td><td>1.00</td><td>2.50</td><td>4.00</td><td>1.50</td></tr>
<tr><td>CISIDAE</td><td>Octotemnus glabriculus</td><td>1.00</td><td>2.50</td><td>3.40</td><td>2.50</td></tr>
<tr><td>CISIDAE</td><td>Ropalodontus perforatus</td><td>2.00</td><td>2.67</td><td>3.25</td><td>1.40</td></tr>
<tr><td>CISIDAE</td><td>Wagaicis wagai</td><td>1.00</td><td>2.50</td><td>3.25</td><td>1.50</td></tr>
<tr><td>CISIDAE</td><td>Sulcacis affinis</td><td>1.00</td><td>2.50</td><td>3.40</td><td>1.50</td></tr>
<tr><td>CISIDAE</td><td>Sulcacis bidentulus</td><td>1.00</td><td>3.00</td><td>3.25</td><td>1.50</td></tr>
<tr><td>CISIDAE</td><td>Sulcacis fronticornis</td><td>1.00</td><td>2.50</td><td>3.40</td><td>1.40</td></tr>
<tr><td>CISIDAE</td><td>Cis lineatocribratus</td><td>1.00</td><td>2.50</td><td>3.40</td><td>2.60</td></tr>
<tr><td>CISIDAE</td><td>Cis nitidus</td><td>1.00</td><td>2.50</td><td>3.40</td><td>2.50</td></tr>
<tr><td>CISIDAE</td><td>Cis jacquemartii</td><td>1.00</td><td>2.50</td><td>3.25</td><td>2.00</td></tr>
<tr><td>CISIDAE</td><td>Cis glabratus</td><td>1.00</td><td>2.50</td><td>3.25</td><td>2.00</td></tr>
<tr><td>CISIDAE</td><td>Cis comptus</td><td>2.00</td><td>2.50</td><td>3.25</td><td>1.40</td></tr>
<tr><td>CISIDAE</td><td>Cis hispidus</td><td>2.00</td><td>2.50</td><td>3.25</td><td>1.67</td></tr>
<tr><td>CISIDAE</td><td>Cis setiger</td><td>2.00</td><td>2.50</td><td>3.25</td><td>1.50</td></tr>
<tr><td>CISIDAE</td><td>Cis micans</td><td>2.00</td><td>2.50</td><td>3.25</td><td>1.50</td></tr>
<tr><td>CISIDAE</td><td>Cis boleti</td><td>3.00</td><td>2.50</td><td>3.40</td><td>1.75</td></tr>
<tr><td>CISIDAE</td><td>Cis rugulosus</td><td>3.00</td><td>2.50</td><td>3.25</td><td>1.50</td></tr>
<tr><td>CISIDAE</td><td>Cis quadridens</td><td>1.00</td><td>2.50</td><td>3.25</td><td>2.00</td></tr>
<tr><td>CISIDAE</td><td>Cis punctulatus</td><td>2.00</td><td>2.20</td><td>3.25</td><td>1.50</td></tr>
<tr><td>CISIDAE</td><td>Cis fagi</td><td>1.00</td><td>2.50</td><td>3.25</td><td>1.50</td></tr>
<tr><td>CISIDAE</td><td>Cis castaneus</td><td>1.00</td><td>2.50</td><td>3.40</td><td>1.67</td></tr>
<tr><td>CISIDAE</td><td>Cis dentatus</td><td>2.00</td><td>2.50</td><td>3.25</td><td>1.50</td></tr>
<tr><td>CISIDAE</td><td>Cis bidentatus</td><td>2.00</td><td>3.00</td><td>3.40</td><td>2.50</td></tr>
<tr><td>CISIDAE</td><td>Cis fissicornis</td><td>1.00</td><td>2.50</td><td>3.25</td><td>1.40</td></tr>
<tr><td>CISIDAE</td><td>Orthocis alni</td><td>2.00</td><td>1.00</td><td>2.75</td><td>2.00</td></tr>
<tr><td>CISIDAE</td><td>Orthocis pygmaeus</td><td>1.00</td><td>1.86</td><td>3.00</td><td>1.00</td></tr>
<tr><td>CISIDAE</td><td>Orthocis vestitus</td><td>1.00</td><td>1.86</td><td>3.00</td><td>1.40</td></tr>
<tr><td>CISIDAE</td><td>Orthocis festivus</td><td>2.00</td><td>1.86</td><td>3.00</td><td>1.75</td></tr>
<tr><td>CISIDAE</td><td>Orthocis lucasi</td><td>2.00</td><td>2.50</td><td>2.25</td><td>1.00</td></tr>
<tr><td>CISIDAE</td><td>Ennearthron cornutum</td><td>1.00</td><td>2.29</td><td>3.40</td><td>1.75</td></tr>
<tr><td>CISIDAE</td><td>Hadreule elongatulum</td><td>1.00</td><td>3.00</td><td>3.43</td><td>1.00</td></tr>
<tr><td>LYCTIDAE</td><td>Lyctus brunneus</td><td>5.00</td><td>2.50</td><td>2.50</td><td>1.00</td></tr>
<tr><td>BOSTRICHIDAE</td><td>Bostrichus capucinus</td><td>10.00</td><td>1.50</td><td>2.40</td><td>1.00</td></tr>
<tr><td>BOSTRICHIDAE</td><td>Xylopertha retusa</td><td>4.00</td><td>1.00</td><td>2.00</td><td>1.40</td></tr>
<tr><td>ANOBIIDAE</td><td>Dorcatoma androgyna</td><td>2.00</td><td>4.00</td><td>3.67</td><td>2.50</td></tr>
<tr><td>ANOBIIDAE</td><td>Hedobia imperialis</td><td>4.00</td><td>1.86</td><td>3.00</td><td>1.50</td></tr>
<tr><td>ANOBIIDAE</td><td>Grynobius planus</td><td>5.00</td><td>2.29</td><td>3.00</td><td>1.50</td></tr>
<tr><td>ANOBIIDAE</td><td>Dryophilus anobioides</td><td>2.00</td><td>1.00</td><td>2.50</td><td></td></tr>
<tr><td>ANOBIIDAE</td><td>Dryophilus pusillus</td><td>2.00</td><td>1.00</td><td>2.50</td><td>1.50</td></tr>
<tr><td>ANOBIIDAE</td><td>Ochina ptinoides</td><td>3.00</td><td>1.00</td><td>3.00</td><td>1.40</td></tr>
<tr><td>ANOBIIDAE</td><td>Xestobium plumbeum</td><td>4.00</td><td>1.00</td><td>2.50</td><td>2.00</td></tr>
<tr><td>ANOBIIDAE</td><td>Xestobium rufovillosum</td><td>7.00</td><td>3.00</td><td>3.25</td><td>2.00</td></tr>
<tr><td>ANOBIIDAE</td><td>Xestobium austriacum</td><td>7.00</td><td>2.29</td><td>3.00</td><td>1.80</td></tr>
<tr><td>ANOBIIDAE</td><td>Episernus granulatus</td><td>3.00</td><td>1.00</td><td>2.33</td><td>1.50</td></tr>
<tr><td>ANOBIIDAE</td><td>Ernobius nigrinus</td><td>3.00</td><td>1.00</td><td>1.86</td><td>1.50</td></tr>
<tr><td>ANOBIIDAE</td><td>Ernobius longicornis</td><td>3.00</td><td>1.00</td><td>1.86</td><td>1.50</td></tr>
<tr><td>ANOBIIDAE</td><td>Ernobius abietinus</td><td>3.00</td><td>1.00</td><td>1.86</td><td>1.50</td></tr>
<tr><td>ANOBIIDAE</td><td>Ernobius abietis</td><td>3.00</td><td>1.00</td><td>1.86</td><td>1.50</td></tr>
<tr><td>ANOBIIDAE</td><td>Ernobius mollis</td><td>4.00</td><td>1.20</td><td>2.50</td><td>1.50</td></tr>
<tr><td>ANOBIIDAE</td><td>Oligomerus brunneus</td><td>5.00</td><td>3.00</td><td>3.00</td><td>1.40</td></tr>
<tr><td>ANOBIIDAE</td><td>Gastrallus immarginatus</td><td>2.00</td><td>3.00</td><td>2.00</td><td>1.40</td></tr>
<tr><td>ANOBIIDAE</td><td>Gastrallus laevigatus</td><td>2.00</td><td>1.20</td><td>2.25</td><td>1.40</td></tr>
<tr><td>ANOBIIDAE</td><td>Anobium punctatum</td><td>3.00</td><td>2.50</td><td>3.00</td><td>1.50</td></tr>
<tr><td>ANOBIIDAE</td><td>Anobium hederae</td><td>3.00</td><td>1.00</td><td>3.00</td><td>1.40</td></tr>
<tr><td>ANOBIIDAE</td><td>Anobium inexspectatum</td><td>3.00</td><td>1.00</td><td>3.00</td><td>1.40</td></tr>
<tr><td>ANOBIIDAE</td><td>Anobium nitidum</td><td>3.00</td><td>3.00</td><td>3.00</td><td>1.67</td></tr>
<tr><td>ANOBIIDAE</td><td>Anobium costatum</td><td>4.00</td><td>1.00</td><td>2.50</td><td>2.00</td></tr>
<tr><td>ANOBIIDAE</td><td>Anobium fulvicorne</td><td>3.00</td><td>1.20</td><td>2.50</td><td>2.00</td></tr>
<tr><td>ANOBIIDAE</td><td>Anobium rufipes</td><td>5.00</td><td>1.80</td><td>3.00</td><td>1.50</td></tr>
<tr><td>ANOBIIDAE</td><td>Anobium emarginatum</td><td>4.00</td><td>2.20</td><td>1.80</td><td>1.50</td></tr>
<tr><td>ANOBIIDAE</td><td>Anobium denticolle</td><td>5.00</td><td>2.50</td><td>3.00</td><td>1.50</td></tr>
<tr><td>ANOBIIDAE</td><td>Anobium pertinax</td><td>5.00</td><td>3.00</td><td>3.00</td><td>1.50</td></tr>
<tr><td>ANOBIIDAE</td><td>Priobium carpini</td><td>4.00</td><td>2.71</td><td>3.25</td><td>1.40</td></tr>
<tr><td>ANOBIIDAE</td><td>Ptilinus pectinicornis</td><td>4.00</td><td>2.50</td><td>3.00</td><td>1.50</td></tr>
<tr><td>ANOBIIDAE</td><td>Ptilinus fuscus</td><td>4.00</td><td>3.00</td><td>3.00</td><td>1.50</td></tr>
<tr><td>ANOBIIDAE</td><td>Mesocoelopus niger</td><td>3.00</td><td>1.00</td><td>3.00</td><td>1.40</td></tr>
<tr><td>ANOBIIDAE</td><td>Dorcatoma flavicornis</td><td>2.00</td><td>3.80</td><td>3.40</td><td>1.80</td></tr>
<tr><td>ANOBIIDAE</td><td>Dorcatoma setosella</td><td>2.00</td><td>3.00</td><td>3.00</td><td>1.60</td></tr>
<tr><td>ANOBIIDAE</td><td>Dorcatoma chrysomelina</td><td>2.00</td><td>3.80</td><td>3.40</td><td>1.80</td></tr>
<tr><td>ANOBIIDAE</td><td>Dorcatoma substriata</td><td>2.00</td><td>2.50</td><td>3.25</td><td>1.60</td></tr>
<tr><td>ANOBIIDAE</td><td>Dorcatoma minor</td><td>2.00</td><td>3.00</td><td>3.25</td><td>1.50</td></tr>
<tr><td>ANOBIIDAE</td><td>Dorcatoma punctulata</td><td>2.00</td><td>3.00</td><td>3.25</td><td>2.00</td></tr>
<tr><td>ANOBIIDAE</td><td>Dorcatoma dresdensis</td><td>3.00</td><td>2.50</td><td>3.25</td><td>1.50</td></tr>
<tr><td>ANOBIIDAE</td><td>Dorcatoma robusta</td><td>4.00</td><td>3.00</td><td>3.25</td><td>1.50</td></tr>
<tr><td>PTINIDAE</td><td>Ptinus rufipes</td><td>3.00</td><td>1.86</td><td>3.00</td><td>1.50</td></tr>
<tr><td>OEDEMERIDAE</td><td>Calopus serraticornis</td><td>19.00</td><td>2.29</td><td>3.40</td><td>2.50</td></tr>
<tr><td>OEDEMERIDAE</td><td>Nacerdes melanura</td><td>11.00</td><td>2.50</td><td>3.40</td><td>1.50</td></tr>
<tr><td>OEDEMERIDAE</td><td>Nacerdes carniolica</td><td>13.00</td><td>2.50</td><td>3.50</td><td>1.50</td></tr>
<tr><td>OEDEMERIDAE</td><td>Chrysanthia viridissima</td><td>8.00</td><td>1.20</td><td>3.40</td><td>1.50</td></tr>
<tr><td>OEDEMERIDAE</td><td>Chrysanthia nigricornis</td><td>6.00</td><td>1.20</td><td>3.40</td><td>1.50</td></tr>
<tr><td>OEDEMERIDAE</td><td>Ischnomera sanguinicollis</td><td>10.00</td><td>3.80</td><td>3.40</td><td>2.00</td></tr>
<tr><td>OEDEMERIDAE</td><td>Ischnomera caerulea</td><td>8.00</td><td>3.00</td><td>3.40</td><td>2.00</td></tr>
<tr><td>OEDEMERIDAE</td><td>Ischnomera cyanea</td><td>8.00</td><td>3.00</td><td>3.40</td><td>2.00</td></tr>
<tr><td>OEDEMERIDAE</td><td>Ischnomera cinerascens</td><td>8.00</td><td>3.00</td><td>3.40</td><td>2.00</td></tr>
<tr><td>SALPINGIDAE</td><td>Lissodema cursor</td><td>3.00</td><td>1.00</td><td>2.25</td><td>1.50</td></tr>
<tr><td>SALPINGIDAE</td><td>Lissodema denticolle</td><td>2.00</td><td>1.40</td><td>2.25</td><td>1.50</td></tr>
<tr><td>SALPINGIDAE</td><td>Rabocerus foveolatus</td><td>3.00</td><td>1.20</td><td>2.00</td><td>1.50</td></tr>
<tr><td>SALPINGIDAE</td><td>Rabocerus gabrieli</td><td>3.00</td><td>1.80</td><td>2.00</td><td>1.50</td></tr>
<tr><td>SALPINGIDAE</td><td>Sphaeriestes castaneus</td><td>3.00</td><td>1.20</td><td>2.00</td><td>1.50</td></tr>
<tr><td>SALPINGIDAE</td><td>Vincenzellus ruficollis</td><td>3.00</td><td>2.00</td><td>2.40</td><td>2.40</td></tr>
<tr><td>SALPINGIDAE</td><td>Salpingus planirostris</td><td>3.00</td><td>2.00</td><td>2.25</td><td>2.00</td></tr>
<tr><td>SALPINGIDAE</td><td>Salpingus ruficollis</td><td>3.00</td><td>2.00</td><td>2.25</td><td>2.00</td></tr>
<tr><td>PROSTOMIDAE</td><td>Prostomis mandibularis</td><td>5.00</td><td>3.00</td><td>3.50</td><td>2.60</td></tr>
<tr><td>PYROCHROIDAE</td><td>Pyrochroa coccinea</td><td>16.00</td><td>3.00</td><td>2.40</td><td>2.00</td></tr>
<tr><td>PYROCHROIDAE</td><td>Pyrochroa serraticornis</td><td>12.00</td><td>2.50</td><td>2.40</td><td>2.00</td></tr>
<tr><td>PYROCHROIDAE</td><td>Schizotus pectinicornis</td><td>8.00</td><td>1.20</td><td>2.50</td><td>2.00</td></tr>
<tr><td>SCRAPTIIDAE</td><td>Scraptia fuscula</td><td>2.00</td><td>2.71</td><td>4.13</td><td>1.50</td></tr>
<tr><td>SCRAPTIIDAE</td><td>Cyrtanaspis phalerata</td><td>3.00</td><td>1.86</td><td>4.00</td><td>1.50</td></tr>
<tr><td>SCRAPTIIDAE</td><td>Anaspis humeralis</td><td>2.00</td><td>2.29</td><td>4.00</td><td>1.50</td></tr>
<tr><td>SCRAPTIIDAE</td><td>Anaspis lurida</td><td>3.00</td><td>2.29</td><td>4.00</td><td>1.50</td></tr>
<tr><td>SCRAPTIIDAE</td><td>Anaspis frontalis</td><td>3.00</td><td>2.29</td><td>4.00</td><td>1.50</td></tr>
<tr><td>SCRAPTIIDAE</td><td>Anaspis maculata</td><td>2.00</td><td>2.29</td><td>4.00</td><td>1.50</td></tr>
<tr><td>SCRAPTIIDAE</td><td>Anaspis marginicollis</td><td>3.00</td><td>2.29</td><td>4.00</td><td>1.50</td></tr>
<tr><td>SCRAPTIIDAE</td><td>Anaspis thoracica</td><td>2.00</td><td>2.29</td><td>4.00</td><td>1.50</td></tr>
<tr><td>SCRAPTIIDAE</td><td>Anaspis ruficollis</td><td>2.00</td><td>2.29</td><td>4.00</td><td>1.50</td></tr>
<tr><td>SCRAPTIIDAE</td><td>Anaspis regimbarti</td><td>3.00</td><td>2.29</td><td>4.00</td><td>1.50</td></tr>
<tr><td>SCRAPTIIDAE</td><td>Anaspis garneysi</td><td>3.00</td><td>2.15</td><td>4.00</td><td>2.00</td></tr>
<tr><td>SCRAPTIIDAE</td><td>Anaspis rufilabris</td><td>2.00</td><td>2.29</td><td>4.00</td><td>1.50</td></tr>
<tr><td>SCRAPTIIDAE</td><td>Anaspis costai</td><td>3.00</td><td>2.29</td><td>4.00</td><td>1.50</td></tr>
<tr><td>SCRAPTIIDAE</td><td>Anaspis flava</td><td>3.00</td><td>2.29</td><td>4.00</td><td>1.50</td></tr>
<tr><td>SCRAPTIIDAE</td><td>Anaspis varians</td><td>2.00</td><td>2.29</td><td>4.00</td><td>1.40</td></tr>
<tr><td>ADERIDAE</td><td>Aderus populneus</td><td>2.00</td><td>4.00</td><td>4.50</td><td>1.50</td></tr>
<tr><td>ADERIDAE</td><td>Euglenes pygmaeus</td><td>2.00</td><td>3.80</td><td>4.00</td><td>1.50</td></tr>
<tr><td>ADERIDAE</td><td>Euglenes oculatus</td><td>2.00</td><td>3.80</td><td>4.00</td><td>1.50</td></tr>
<tr><td>ADERIDAE</td><td>Anidorus nigrinus</td><td>2.00</td><td>1.20</td><td>3.50</td><td>1.50</td></tr>
<tr><td>RHIPIPHORIDAE</td><td>Pelecotoma fennica</td><td>4.00</td><td>3.00</td><td>3.00</td><td>1.40</td></tr>
<tr><td>MORDELLIDAE</td><td>Tomoxia bucephala</td><td>7.00</td><td>2.29</td><td>3.00</td><td>1.40</td></tr>
<tr><td>MORDELLIDAE</td><td>Variimorda villosa</td><td>7.00</td><td>2.33</td><td>3.00</td><td>1.40</td></tr>
<tr><td>MORDELLIDAE</td><td>Mordella huetheri</td><td>6.00</td><td>2.29</td><td>3.00</td><td>1.40</td></tr>
<tr><td>MORDELLIDAE</td><td>Mordella aculeata</td><td>6.00</td><td>2.29</td><td>3.00</td><td>1.40</td></tr>
<tr><td>MORDELLIDAE</td><td>Mordella brachyura</td><td>6.00</td><td>2.29</td><td>3.00</td><td>1.40</td></tr>
<tr><td>MORDELLIDAE</td><td>Mordella holomelaena</td><td>7.00</td><td>2.29</td><td>3.00</td><td>1.40</td></tr>
<tr><td>MORDELLIDAE</td><td>Curtimorda maculosa</td><td>4.00</td><td>3.00</td><td>3.50</td><td>1.00</td></tr>
<tr><td>MORDELLIDAE</td><td>Mordellistena neuwaldeggiana</td><td>3.00</td><td>2.29</td><td>3.50</td><td>2.50</td></tr>
<tr><td>MORDELLIDAE</td><td>Mordellistena variegata</td><td>4.00</td><td>2.29</td><td>3.50</td><td>1.75</td></tr>
<tr><td>MORDELLIDAE</td><td>Mordellochroa abdominalis</td><td>5.00</td><td>2.29</td><td>3.50</td><td>1.75</td></tr>
<tr><td>MELANDRYIDAE</td><td>Mycetoma suturale</td><td>7.00</td><td>2.50</td><td>3.25</td><td>2.50</td></tr>
<tr><td>MELANDRYIDAE</td><td>Hallomenus binotatus</td><td>4.00</td><td>2.50</td><td>3.40</td><td>2.00</td></tr>
<tr><td>MELANDRYIDAE</td><td>Orchesia micans</td><td>4.00</td><td>2.50</td><td>3.25</td><td>2.17</td></tr>
<tr><td>MELANDRYIDAE</td><td>Orchesia luteipalpis</td><td>4.00</td><td>2.50</td><td>3.25</td><td>2.40</td></tr>
<tr><td>MELANDRYIDAE</td><td>Orchesia minor</td><td>3.00</td><td>1.00</td><td>3.40</td><td>2.00</td></tr>
<tr><td>MELANDRYIDAE</td><td>Orchesia fasciata</td><td>3.00</td><td>1.20</td><td>3.40</td><td>2.00</td></tr>
<tr><td>MELANDRYIDAE</td><td>Orchesia undulata</td><td>4.00</td><td>2.50</td><td>3.50</td><td>2.50</td></tr>
<tr><td>MELANDRYIDAE</td><td>Orchesia blandula</td><td>3.00</td><td>1.90</td><td>3.25</td><td>2.40</td></tr>
<tr><td>MELANDRYIDAE</td><td>Anisoxya fuscula</td><td>3.00</td><td>1.00</td><td>3.00</td><td>1.50</td></tr>
<tr><td>MELANDRYIDAE</td><td>Abdera affinis</td><td>3.00</td><td>2.29</td><td>3.25</td><td>1.60</td></tr>
<tr><td>MELANDRYIDAE</td><td>Abdera flexuosa</td><td>3.00</td><td>2.29</td><td>3.25</td><td>2.40</td></tr>
<tr><td>MELANDRYIDAE</td><td>Abdera quadrifasciata</td><td>3.00</td><td>1.00</td><td>3.00</td><td>1.50</td></tr>
<tr><td>MELANDRYIDAE</td><td>Dircaea australis</td><td>10.00</td><td>3.00</td><td>3.40</td><td>1.80</td></tr>
<tr><td>MELANDRYIDAE</td><td>Phloiotrya rufipes</td><td>7.00</td><td>1.20</td><td>3.40</td><td>1.75</td></tr>
<tr><td>MELANDRYIDAE</td><td>Phloiotrya vaudoueri</td><td>9.00</td><td>2.20</td><td>3.00</td><td>1.50</td></tr>
<tr><td>MELANDRYIDAE</td><td>Xylita laevigata</td><td>8.00</td><td>2.50</td><td>3.50</td><td>2.00</td></tr>
<tr><td>MELANDRYIDAE</td><td>Xylita livida</td><td>5.00</td><td>2.50</td><td>3.50</td><td>1.50</td></tr>
<tr><td>MELANDRYIDAE</td><td>Serropalpus barbatus</td><td>13.00</td><td>2.20</td><td>2.25</td><td>2.00</td></tr>
<tr><td>MELANDRYIDAE</td><td>Hypulus quercinus</td><td>5.00</td><td>2.29</td><td>3.50</td><td>2.50</td></tr>
<tr><td>MELANDRYIDAE</td><td>Melandrya caraboides</td><td>13.00</td><td>2.29</td><td>3.40</td><td>1.60</td></tr>
<tr><td>MELANDRYIDAE</td><td>Melandrya barbata</td><td>10.00</td><td>2.29</td><td>3.40</td><td>2.40</td></tr>
<tr><td>MELANDRYIDAE</td><td>Melandrya dubia</td><td>13.00</td><td>2.29</td><td>3.40</td><td>2.00</td></tr>
<tr><td>MELANDRYIDAE</td><td>Conopalpus testaceus</td><td>6.00</td><td>1.20</td><td>3.40</td><td>2.00</td></tr>
<tr><td>MELANDRYIDAE</td><td>Conopalpus brevicollis</td><td>3.00</td><td>1.00</td><td>3.50</td><td>2.00</td></tr>
<tr><td>MELANDRYIDAE</td><td>Osphya bipunctata</td><td>8.00</td><td>1.20</td><td>3.25</td><td>2.50</td></tr>
<tr><td>TETRATOMIDAE</td><td>Tetratoma fungorum</td><td>4.00</td><td>3.00</td><td>3.40</td><td>2.00</td></tr>
<tr><td>TETRATOMIDAE</td><td>Tetratoma desmarestii</td><td>3.00</td><td>1.67</td><td>3.00</td><td>1.60</td></tr>
<tr><td>TETRATOMIDAE</td><td>Tetratoma ancora</td><td>3.00</td><td>1.86</td><td>3.00</td><td>2.50</td></tr>
<tr><td>ALLECULIDAE</td><td>Allecula morio</td><td>7.00</td><td>3.50</td><td>4.60</td><td>1.50</td></tr>
<tr><td>ALLECULIDAE</td><td>Allecula rhenana</td><td>8.00</td><td>3.50</td><td>4.60</td><td>1.50</td></tr>
<tr><td>ALLECULIDAE</td><td>Prionychus ater</td><td>13.00</td><td>4.00</td><td>4.60</td><td>2.00</td></tr>
<tr><td>ALLECULIDAE</td><td>Prionychus melanarius</td><td>11.00</td><td>3.20</td><td>4.29</td><td>1.40</td></tr>
<tr><td>ALLECULIDAE</td><td>Pseudocistela ceramboides</td><td>11.00</td><td>3.20</td><td>4.29</td><td>1.50</td></tr>
<tr><td>ALLECULIDAE</td><td>Mycetochara flavipes</td><td>5.00</td><td>2.71</td><td>3.83</td><td>1.50</td></tr>
<tr><td>ALLECULIDAE</td><td>Mycetochara axillaris</td><td>7.00</td><td>3.80</td><td>4.17</td><td>1.80</td></tr>
<tr><td>ALLECULIDAE</td><td>Mycetochara humeralis</td><td>4.00</td><td>3.80</td><td>4.17</td><td>1.50</td></tr>
<tr><td>ALLECULIDAE</td><td>Mycetochara linearis</td><td>5.00</td><td>3.00</td><td>4.29</td><td>1.50</td></tr>
<tr><td>TENEBRIONIDAE</td><td>Bolitophagus reticulatus</td><td>6.00</td><td>3.00</td><td>3.33</td><td>1.60</td></tr>
<tr><td>TENEBRIONIDAE</td><td>Bolitophagus interruptus</td><td>4.00</td><td>3.00</td><td>3.33</td><td>1.50</td></tr>
<tr><td>TENEBRIONIDAE</td><td>Eledona agricola</td><td>2.00</td><td>3.00</td><td>3.40</td><td>2.00</td></tr>
<tr><td>TENEBRIONIDAE</td><td>Diaperis boleti</td><td>7.00</td><td>2.50</td><td>3.40</td><td>1.75</td></tr>
<tr><td>TENEBRIONIDAE</td><td>Neomida haemorrhoidalis</td><td>5.00</td><td>3.00</td><td>2.60</td><td>2.00</td></tr>
<tr><td>TENEBRIONIDAE</td><td>Scaphidema metallicum</td><td>7.00</td><td>2.29</td><td>3.80</td><td>2.50</td></tr>
<tr><td>TENEBRIONIDAE</td><td>Platydema violaceum</td><td>6.00</td><td>2.60</td><td>3.40</td><td>2.00</td></tr>
<tr><td>TENEBRIONIDAE</td><td>Platydema dejeanii</td><td>5.00</td><td>2.50</td><td>3.40</td><td>1.40</td></tr>
<tr><td>TENEBRIONIDAE</td><td>Pentaphyllus testaceus</td><td>1.00</td><td>3.80</td><td>4.40</td><td>1.50</td></tr>
<tr><td>TENEBRIONIDAE</td><td>Corticeus unicolor</td><td>6.00</td><td>3.00</td><td>2.50</td><td>2.17</td></tr>
<tr><td>TENEBRIONIDAE</td><td>Corticeus bicolor</td><td>3.00</td><td>2.20</td><td>2.25</td><td>1.50</td></tr>
<tr><td>TENEBRIONIDAE</td><td>Corticeus bicoloroides</td><td>3.00</td><td>3.80</td><td>3.80</td><td>1.50</td></tr>
<tr><td>TENEBRIONIDAE</td><td>Corticeus fasciatus</td><td>3.00</td><td>3.80</td><td>3.00</td><td>1.40</td></tr>
<tr><td>TENEBRIONIDAE</td><td>Diaclina fagi</td><td>4.00</td><td>3.00</td><td>3.50</td><td>1.00</td></tr>
<tr><td>TENEBRIONIDAE</td><td>Uloma culinaris</td><td>10.00</td><td>3.00</td><td>3.40</td><td>1.50</td></tr>
<tr><td>TENEBRIONIDAE</td><td>Uloma rufa</td><td>8.00</td><td>2.50</td><td>3.40</td><td>1.33</td></tr>
<tr><td>TENEBRIONIDAE</td><td>Stenomax aeneus</td><td>14.00</td><td>3.00</td><td>3.50</td><td>1.75</td></tr>
<tr><td>SCARABAEIDAE</td><td>Cetonia aurata</td><td>17.00</td><td>3.00</td><td>4.00</td><td>1.00</td></tr>
<tr><td>SCARABAEIDAE</td><td>Protaetia lugubris</td><td>22.00</td><td>3.80</td><td>4.20</td><td>1.80</td></tr>
<tr><td>SCARABAEIDAE</td><td>Valgus hemipterus</td><td>7.00</td><td>2.50</td><td>3.50</td><td>1.50</td></tr>
<tr><td>SCARABAEIDAE</td><td>Osmoderma eremita</td><td>27.00</td><td>3.50</td><td>4.20</td><td>1.80</td></tr>
<tr><td>SCARABAEIDAE</td><td>Gnorimus nobilis</td><td>16.00</td><td>3.80</td><td>4.20</td><td>1.50</td></tr>
<tr><td>SCARABAEIDAE</td><td>Trichius fasciatus</td><td>10.00</td><td>2.50</td><td>3.50</td><td>1.50</td></tr>
<tr><td>LUCANIDAE</td><td>Lucanus cervus</td><td>50.00</td><td>3.00</td><td>3.40</td><td>1.40</td></tr>
<tr><td>LUCANIDAE</td><td>Dorcus parallelipipedus</td><td>25.00</td><td>3.00</td><td>3.40</td><td>1.50</td></tr>
<tr><td>LUCANIDAE</td><td>Platycerus caprea</td><td>14.00</td><td>2.00</td><td>3.40</td><td>2.00</td></tr>
<tr><td>LUCANIDAE</td><td>Platycerus caraboides</td><td>11.00</td><td>2.00</td><td>3.40</td><td>2.00</td></tr>
<tr><td>LUCANIDAE</td><td>Ceruchus chrysomelinus</td><td>13.00</td><td>3.00</td><td>3.25</td><td>2.50</td></tr>
<tr><td>LUCANIDAE</td><td>Sinodendron cylindricum</td><td>14.00</td><td>3.00</td><td>3.25</td><td>2.20</td></tr>
<tr><td>CERAMBYCIDAE</td><td>Leiopus linnei</td><td>8.00</td><td>1.20</td><td>2.00</td><td>1.50</td></tr>
<tr><td>CERAMBYCIDAE</td><td>Megopis scabricornis</td><td>40.00</td><td>3.20</td><td>2.80</td><td>1.40</td></tr>
<tr><td>CERAMBYCIDAE</td><td>Prionus coriarius</td><td>31.00</td><td>3.00</td><td>3.00</td><td>1.80</td></tr>
<tr><td>CERAMBYCIDAE</td><td>Spondylis buprestoides</td><td>18.00</td><td>2.50</td><td>2.75</td><td>1.80</td></tr>
<tr><td>CERAMBYCIDAE</td><td>Arhopalus rusticus</td><td>20.00</td><td>2.50</td><td>2.50</td><td>1.50</td></tr>
<tr><td>CERAMBYCIDAE</td><td>Tetropium castaneum</td><td>13.00</td><td>2.20</td><td>2.00</td><td>1.50</td></tr>
<tr><td>CERAMBYCIDAE</td><td>Tetropium fuscum</td><td>12.00</td><td>2.20</td><td>2.00</td><td>1.50</td></tr>
<tr><td>CERAMBYCIDAE</td><td>Rhagium bifasciatum</td><td>17.00</td><td>2.50</td><td>3.40</td><td>2.50</td></tr>
<tr><td>CERAMBYCIDAE</td><td>Rhagium sycophanta</td><td>18.00</td><td>3.00</td><td>2.00</td><td>1.50</td></tr>
<tr><td>CERAMBYCIDAE</td><td>Rhagium mordax</td><td>17.00</td><td>2.50</td><td>2.25</td><td>1.50</td></tr>
<tr><td>CERAMBYCIDAE</td><td>Rhagium inquisitor</td><td>15.00</td><td>2.50</td><td>2.40</td><td>1.80</td></tr>
<tr><td>CERAMBYCIDAE</td><td>Oxymirus cursor</td><td>23.00</td><td>2.50</td><td>3.60</td><td>1.80</td></tr>
<tr><td>CERAMBYCIDAE</td><td>Stenocorus meridianus</td><td>20.00</td><td>2.29</td><td>3.40</td><td>1.83</td></tr>
<tr><td>CERAMBYCIDAE</td><td>Evodinus clathratus</td><td>11.00</td><td>1.80</td><td>3.00</td><td>1.50</td></tr>
<tr><td>CERAMBYCIDAE</td><td>Gaurotes virginea</td><td>10.00</td><td>2.29</td><td>3.40</td><td>1.50</td></tr>
<tr><td>CERAMBYCIDAE</td><td>Dinoptera collaris</td><td>8.00</td><td>1.20</td><td>3.50</td><td>1.50</td></tr>
<tr><td>CERAMBYCIDAE</td><td>Pidonia lurida</td><td>10.00</td><td>2.50</td><td>3.40</td><td>2.00</td></tr>
<tr><td>CERAMBYCIDAE</td><td>Cortodera femorata</td><td>9.00</td><td>1.00</td><td>3.00</td><td>1.50</td></tr>
<tr><td>CERAMBYCIDAE</td><td>Cortodera humeralis</td><td>9.00</td><td>1.20</td><td>3.50</td><td>1.50</td></tr>
<tr><td>CERAMBYCIDAE</td><td>Grammoptera ustulata</td><td>7.00</td><td>1.00</td><td>3.00</td><td>1.50</td></tr>
<tr><td>CERAMBYCIDAE</td><td>Grammoptera ruficornis</td><td>5.00</td><td>1.00</td><td>2.75</td><td>1.40</td></tr>
<tr><td>CERAMBYCIDAE</td><td>Grammoptera abdominalis</td><td>7.00</td><td>1.00</td><td>3.00</td><td>1.50</td></tr>
<tr><td>CERAMBYCIDAE</td><td>Alosterna tabacicolor</td><td>7.00</td><td>2.50</td><td>3.60</td><td>2.50</td></tr>
<tr><td>CERAMBYCIDAE</td><td>Leptura aurulenta</td><td>18.00</td><td>3.00</td><td>3.25</td><td>1.40</td></tr>
<tr><td>CERAMBYCIDAE</td><td>Leptura quadrifasciata</td><td>15.00</td><td>2.50</td><td>3.25</td><td>1.50</td></tr>
<tr><td>CERAMBYCIDAE</td><td>Leptura maculata</td><td>17.00</td><td>2.50</td><td>3.25</td><td>1.50</td></tr>
<tr><td>CERAMBYCIDAE</td><td>Leptura aethiops</td><td>12.00</td><td>2.00</td><td>3.00</td><td>1.50</td></tr>
<tr><td>CERAMBYCIDAE</td><td>Anoplodera sexguttata</td><td>9.00</td><td>2.50</td><td>3.40</td><td>2.50</td></tr>
<tr><td>CERAMBYCIDAE</td><td>Corymbia maculicornis</td><td>9.00</td><td>2.50</td><td>3.50</td><td>1.80</td></tr>
<tr><td>CERAMBYCIDAE</td><td>Corymbia rubra</td><td>14.00</td><td>2.50</td><td>3.50</td><td>1.50</td></tr>
<tr><td>CERAMBYCIDAE</td><td>Corymbia scutellata</td><td>17.00</td><td>3.00</td><td>3.40</td><td>1.40</td></tr>
<tr><td>CERAMBYCIDAE</td><td>Anastrangalia sanguinolenta</td><td>10.00</td><td>2.29</td><td>3.50</td><td>1.50</td></tr>
<tr><td>CERAMBYCIDAE</td><td>Anastrangalia dubia</td><td>12.00</td><td>2.50</td><td>3.00</td><td>1.50</td></tr>
<tr><td>CERAMBYCIDAE</td><td>Judolia sexmaculata</td><td>11.00</td><td>2.29</td><td>3.40</td><td>2.50</td></tr>
<tr><td>CERAMBYCIDAE</td><td>Pachytodes cerambyciformis</td><td>9.00</td><td>2.29</td><td>3.17</td><td>1.80</td></tr>
<tr><td>CERAMBYCIDAE</td><td>Stenurella melanura</td><td>7.00</td><td>1.00</td><td>3.40</td><td>1.50</td></tr>
<tr><td>CERAMBYCIDAE</td><td>Stenurella nigra</td><td>7.00</td><td>1.00</td><td>3.40</td><td>1.50</td></tr>
<tr><td>CERAMBYCIDAE</td><td>Cerambyx scopolii</td><td>22.00</td><td>2.29</td><td>2.00</td><td>1.40</td></tr>
<tr><td>CERAMBYCIDAE</td><td>Obrium brunneum</td><td>5.00</td><td>1.00</td><td>2.00</td><td>1.50</td></tr>
<tr><td>CERAMBYCIDAE</td><td>Molorchus minor</td><td>11.00</td><td>1.20</td><td>2.00</td><td>1.50</td></tr>
<tr><td>CERAMBYCIDAE</td><td>Molorchus umbellatarum</td><td>6.00</td><td>1.00</td><td>2.00</td><td>1.50</td></tr>
<tr><td>CERAMBYCIDAE</td><td>Callimus angulatus</td><td>8.00</td><td>1.00</td><td>3.00</td><td>1.40</td></tr>
<tr><td>CERAMBYCIDAE</td><td>Aromia moschata</td><td>23.00</td><td>1.80</td><td>1.25</td><td>1.40</td></tr>
<tr><td>CERAMBYCIDAE</td><td>Rosalia alpina</td><td>26.00</td><td>3.00</td><td>2.75</td><td>1.40</td></tr>
<tr><td>CERAMBYCIDAE</td><td>Pyrrhidium sanguineum</td><td>10.00</td><td>1.90</td><td>2.00</td><td>1.40</td></tr>
<tr><td>CERAMBYCIDAE</td><td>Phymatodes testaceus</td><td>12.00</td><td>2.29</td><td>2.00</td><td>1.50</td></tr>
<tr><td>CERAMBYCIDAE</td><td>Phymatodes pusillus</td><td>7.00</td><td>1.00</td><td>2.00</td><td>1.00</td></tr>
<tr><td>CERAMBYCIDAE</td><td>Phymatodes alni</td><td>5.00</td><td>1.00</td><td>2.00</td><td>1.50</td></tr>
<tr><td>CERAMBYCIDAE</td><td>Xylotrechus antilope</td><td>11.00</td><td>1.20</td><td>2.00</td><td>1.00</td></tr>
<tr><td>CERAMBYCIDAE</td><td>Clytus arietis</td><td>10.00</td><td>2.00</td><td>2.50</td><td>1.50</td></tr>
<tr><td>CERAMBYCIDAE</td><td>Clytus lama</td><td>11.00</td><td>1.50</td><td>2.00</td><td>1.40</td></tr>
<tr><td>CERAMBYCIDAE</td><td>Plagionotus detritus</td><td>14.00</td><td>3.00</td><td>2.00</td><td>1.00</td></tr>
<tr><td>CERAMBYCIDAE</td><td>Plagionotus arcuatus</td><td>13.00</td><td>3.00</td><td>2.00</td><td>1.00</td></tr>
<tr><td>CERAMBYCIDAE</td><td>Anaglyptus mysticus</td><td>9.00</td><td>1.86</td><td>2.75</td><td>1.50</td></tr>
<tr><td>CERAMBYCIDAE</td><td>Monochamus sutor</td><td>19.00</td><td>2.00</td><td>2.00</td><td>1.00</td></tr>
<tr><td>CERAMBYCIDAE</td><td>Mesosa nebulosa</td><td>12.00</td><td>1.20</td><td>2.00</td><td>1.50</td></tr>
<tr><td>CERAMBYCIDAE</td><td>Pogonocherus hispidulus</td><td>6.00</td><td>1.00</td><td>2.25</td><td>2.00</td></tr>
<tr><td>CERAMBYCIDAE</td><td>Pogonocherus hispidus</td><td>6.00</td><td>1.00</td><td>2.25</td><td>2.00</td></tr>
<tr><td>CERAMBYCIDAE</td><td>Pogonocherus fasciculatus</td><td>6.00</td><td>1.00</td><td>2.00</td><td>1.50</td></tr>
<tr><td>CERAMBYCIDAE</td><td>Leiopus nebulosus</td><td>8.00</td><td>1.20</td><td>2.00</td><td>1.50</td></tr>
<tr><td>CERAMBYCIDAE</td><td>Exocentrus adspersus</td><td>6.00</td><td>1.00</td><td>2.00</td><td>1.40</td></tr>
<tr><td>CERAMBYCIDAE</td><td>Exocentrus lusitanus</td><td>5.00</td><td>1.00</td><td>2.75</td><td>1.50</td></tr>
<tr><td>CERAMBYCIDAE</td><td>Saperda populnea</td><td>12.00</td><td>1.00</td><td>1.00</td><td>1.00</td></tr>
<tr><td>CERAMBYCIDAE</td><td>Saperda scalaris</td><td>15.00</td><td>2.00</td><td>2.00</td><td>1.50</td></tr>
<tr><td>CERAMBYCIDAE</td><td>Stenostola dubia</td><td>11.00</td><td>1.00</td><td>3.00</td><td>1.50</td></tr>
<tr><td>CERAMBYCIDAE</td><td>Tetrops praeustus</td><td>4.00</td><td>1.00</td><td>2.50</td><td>1.50</td></tr>
<tr><td>ANTHRIBIDAE</td><td>Platyrhinus resinosus</td><td>11.00</td><td>2.29</td><td>3.00</td><td>1.40</td></tr>
<tr><td>ANTHRIBIDAE</td><td>Tropideres albirostris</td><td>4.00</td><td>1.20</td><td>2.25</td><td>1.40</td></tr>
<tr><td>ANTHRIBIDAE</td><td>Phaeochrotes cinctus</td><td>2.00</td><td>1.00</td><td>2.50</td><td>1.50</td></tr>
<tr><td>ANTHRIBIDAE</td><td>Enedreutes sepicola</td><td>3.00</td><td>1.00</td><td>3.25</td><td>1.50</td></tr>
<tr><td>ANTHRIBIDAE</td><td>Dissoleucas niveirostris</td><td>3.00</td><td>1.00</td><td>3.00</td><td>1.40</td></tr>
<tr><td>ANTHRIBIDAE</td><td>Anthribus albinus</td><td>9.00</td><td>1.86</td><td>3.00</td><td>1.75</td></tr>
<tr><td>ANTHRIBIDAE</td><td>Opanthribus tessellatus</td><td>2.00</td><td>1.00</td><td>3.00</td><td>1.40</td></tr>
<tr><td>ANTHRIBIDAE</td><td>Choragus horni</td><td>1.00</td><td>2.29</td><td>3.00</td><td>2.00</td></tr>
<tr><td>ANTHRIBIDAE</td><td>Choragus sheppardi</td><td>2.00</td><td>2.29</td><td>3.00</td><td>2.00</td></tr>
<tr><td>SCOLYTIDAE</td><td>Cyclorhipidion bodoanus</td><td>2.00</td><td>2.50</td><td>2.00</td><td>1.50</td></tr>
<tr><td>SCOLYTIDAE</td><td>Crypturgus subcribosus</td><td>1.00</td><td>2.00</td><td>2.00</td><td>1.00</td></tr>
<tr><td>SCOLYTIDAE</td><td>Scolytus rugulosus</td><td>2.00</td><td>1.20</td><td>1.75</td><td>1.50</td></tr>
<tr><td>SCOLYTIDAE</td><td>Scolytus intricatus</td><td>3.00</td><td>1.20</td><td>1.75</td><td>1.50</td></tr>
<tr><td>SCOLYTIDAE</td><td>Scolytus mali</td><td>3.00</td><td>1.80</td><td>1.75</td><td>1.40</td></tr>
<tr><td>SCOLYTIDAE</td><td>Scolytus carpini</td><td>2.00</td><td>1.20</td><td>2.00</td><td>1.50</td></tr>
<tr><td>SCOLYTIDAE</td><td>Scolytus laevis</td><td>4.00</td><td>1.20</td><td>1.75</td><td>1.00</td></tr>
<tr><td>SCOLYTIDAE</td><td>Scolytus scolytus</td><td>4.00</td><td>2.29</td><td>1.75</td><td>1.50</td></tr>
<tr><td>SCOLYTIDAE</td><td>Scolytus multistriatus</td><td>2.00</td><td>1.67</td><td>1.75</td><td>1.40</td></tr>
<tr><td>SCOLYTIDAE</td><td>Phthorophloeus spinulosus</td><td>2.00</td><td>1.00</td><td>2.00</td><td>1.40</td></tr>
<tr><td>SCOLYTIDAE</td><td>Phloeophthorus rhododactylus</td><td>1.00</td><td>1.00</td><td>2.00</td><td>1.00</td></tr>
<tr><td>SCOLYTIDAE</td><td>Hylastes ater</td><td>4.00</td><td>2.50</td><td>2.00</td><td>1.50</td></tr>
<tr><td>SCOLYTIDAE</td><td>Hylastes brunneus</td><td>4.00</td><td>2.50</td><td>2.00</td><td>1.50</td></tr>
<tr><td>SCOLYTIDAE</td><td>Hylastes opacus</td><td>3.00</td><td>2.50</td><td>2.00</td><td>1.40</td></tr>
<tr><td>SCOLYTIDAE</td><td>Hylastes cunicularius</td><td>3.00</td><td>2.50</td><td>2.00</td><td>1.50</td></tr>
<tr><td>SCOLYTIDAE</td><td>Hylastes linearis</td><td>3.00</td><td>2.50</td><td>2.00</td><td>1.50</td></tr>
<tr><td>SCOLYTIDAE</td><td>Hylastes attenuatus</td><td>2.00</td><td>1.80</td><td>2.00</td><td>1.50</td></tr>
<tr><td>SCOLYTIDAE</td><td>Hylastes angustatus</td><td>3.00</td><td>2.50</td><td>2.00</td><td>1.50</td></tr>
<tr><td>SCOLYTIDAE</td><td>Hylurgops glabratus</td><td>4.00</td><td>2.50</td><td>2.00</td><td>2.20</td></tr>
<tr><td>SCOLYTIDAE</td><td>Hylurgops palliatus</td><td>2.00</td><td>2.50</td><td>2.00</td><td>2.20</td></tr>
<tr><td>SCOLYTIDAE</td><td>Tomicus piniperda</td><td>4.00</td><td>2.29</td><td>1.75</td><td>1.50</td></tr>
<tr><td>SCOLYTIDAE</td><td>Hylurgus ligniperda</td><td>5.00</td><td>2.50</td><td>2.00</td><td>1.40</td></tr>
<tr><td>SCOLYTIDAE</td><td>Polygraphus grandiclava</td><td>2.00</td><td>1.20</td><td>2.00</td><td>1.50</td></tr>
<tr><td>SCOLYTIDAE</td><td>Polygraphus poligraphus</td><td>2.00</td><td>1.80</td><td>2.00</td><td>1.50</td></tr>
<tr><td>SCOLYTIDAE</td><td>Hylesinus crenatus</td><td>5.00</td><td>3.00</td><td>2.00</td><td>1.50</td></tr>
<tr><td>SCOLYTIDAE</td><td>Hylesinus oleiperda</td><td>2.00</td><td>1.20</td><td>2.00</td><td>1.50</td></tr>
<tr><td>SCOLYTIDAE</td><td>Leperisinus fraxini</td><td>3.00</td><td>2.71</td><td>2.00</td><td>1.50</td></tr>
<tr><td>SCOLYTIDAE</td><td>Leperisinus orni</td><td>2.00</td><td>1.00</td><td>2.00</td><td>1.50</td></tr>
<tr><td>SCOLYTIDAE</td><td>Kissophagus hederae</td><td>2.00</td><td>1.00</td><td>2.00</td><td>1.00</td></tr>
<tr><td>SCOLYTIDAE</td><td>Xylechinus pilosus</td><td>2.00</td><td>2.17</td><td>2.00</td><td>1.40</td></tr>
<tr><td>SCOLYTIDAE</td><td>Phloeosinus thujae</td><td>1.00</td><td>1.00</td><td>1.75</td><td>1.00</td></tr>
<tr><td>SCOLYTIDAE</td><td>Crypturgus cinereus</td><td>1.00</td><td>2.20</td><td>2.00</td><td>2.00</td></tr>
<tr><td>SCOLYTIDAE</td><td>Crypturgus hispidulus</td><td>1.00</td><td>2.20</td><td>2.00</td><td>2.00</td></tr>
<tr><td>SCOLYTIDAE</td><td>Crypturgus pusillus</td><td>1.00</td><td>1.20</td><td>2.00</td><td>1.00</td></tr>
<tr><td>SCOLYTIDAE</td><td>Lymantor coryli</td><td>2.00</td><td>1.00</td><td>3.00</td><td>2.00</td></tr>
<tr><td>SCOLYTIDAE</td><td>Xylocleptes bispinus</td><td>2.00</td><td>1.00</td><td>2.00</td><td>1.50</td></tr>
<tr><td>SCOLYTIDAE</td><td>Dryocoetes autographus</td><td>3.00</td><td>2.40</td><td>2.00</td><td>1.60</td></tr>
<tr><td>SCOLYTIDAE</td><td>Dryocoetes hectographus</td><td>3.00</td><td>2.00</td><td>2.00</td><td></td></tr>
<tr><td>SCOLYTIDAE</td><td>Dryocoetes villosus</td><td>3.00</td><td>3.00</td><td>2.00</td><td>1.60</td></tr>
<tr><td>SCOLYTIDAE</td><td>Cryphalus piceae</td><td>1.00</td><td>1.00</td><td>2.00</td><td>1.00</td></tr>
<tr><td>SCOLYTIDAE</td><td>Cryphalus intermedius</td><td>1.00</td><td>1.00</td><td>2.00</td><td>1.00</td></tr>
<tr><td>SCOLYTIDAE</td><td>Cryphalus abietis</td><td>1.00</td><td>1.00</td><td>2.00</td><td>1.00</td></tr>
<tr><td>SCOLYTIDAE</td><td>Ernoporicus fagi</td><td>1.00</td><td>1.00</td><td>2.00</td><td>1.50</td></tr>
<tr><td>SCOLYTIDAE</td><td>Ernoporicus caucasicus</td><td>1.00</td><td>1.20</td><td>2.00</td><td>1.50</td></tr>
<tr><td>SCOLYTIDAE</td><td>Ernoporus tiliae</td><td>1.00</td><td>1.00</td><td>2.00</td><td>1.50</td></tr>
<tr><td>SCOLYTIDAE</td><td>Pityophthorus exsculptus</td><td>1.00</td><td>1.00</td><td>2.00</td><td>1.50</td></tr>
<tr><td>SCOLYTIDAE</td><td>Pityophthorus pityographus</td><td>1.00</td><td>1.00</td><td>1.75</td><td>1.50</td></tr>
<tr><td>SCOLYTIDAE</td><td>Pityophthorus pubescens</td><td>1.00</td><td>1.00</td><td>2.00</td><td>1.50</td></tr>
<tr><td>SCOLYTIDAE</td><td>Pityophthorus lichtensteini</td><td>1.00</td><td>1.00</td><td>2.00</td><td>1.50</td></tr>
<tr><td>SCOLYTIDAE</td><td>Gnathotrichus materiarius</td><td>3.00</td><td>2.20</td><td>2.00</td><td>1.50</td></tr>
<tr><td>SCOLYTIDAE</td><td>Taphrorychus bicolor</td><td>2.00</td><td>1.80</td><td>2.00</td><td>1.50</td></tr>
<tr><td>SCOLYTIDAE</td><td>Taphrorychus villifrons</td><td>2.00</td><td>2.29</td><td>2.00</td><td>1.50</td></tr>
<tr><td>SCOLYTIDAE</td><td>Pityogenes chalcographus</td><td>2.00</td><td>1.67</td><td>1.75</td><td>1.40</td></tr>
<tr><td>SCOLYTIDAE</td><td>Pityogenes quadridens</td><td>1.00</td><td>1.00</td><td>2.00</td><td>1.40</td></tr>
<tr><td>SCOLYTIDAE</td><td>Pityogenes bidentatus</td><td>2.00</td><td>1.00</td><td>2.00</td><td>1.40</td></tr>
<tr><td>SCOLYTIDAE</td><td>Pityokteines spinidens</td><td>2.00</td><td>2.20</td><td>1.75</td><td>1.50</td></tr>
<tr><td>SCOLYTIDAE</td><td>Pityokteines curvidens</td><td>2.00</td><td>2.50</td><td>1.75</td><td>1.40</td></tr>
<tr><td>SCOLYTIDAE</td><td>Orthotomicus suturalis</td><td>2.00</td><td>2.00</td><td>2.00</td><td>1.00</td></tr>
<tr><td>SCOLYTIDAE</td><td>Orthotomicus laricis</td><td>3.00</td><td>1.80</td><td>2.00</td><td>1.50</td></tr>
<tr><td>SCOLYTIDAE</td><td>Ips typographus</td><td>4.00</td><td>2.50</td><td>1.75</td><td>1.50</td></tr>
<tr><td>SCOLYTIDAE</td><td>Ips cembrae</td><td>5.00</td><td>2.17</td><td>1.75</td><td>1.40</td></tr>
<tr><td>SCOLYTIDAE</td><td>Ips sexdentatus</td><td>6.00</td><td>2.29</td><td>1.75</td><td>1.40</td></tr>
<tr><td>SCOLYTIDAE</td><td>Xyleborus dispar</td><td>1.00</td><td>2.00</td><td>2.00</td><td>1.50</td></tr>
<tr><td>SCOLYTIDAE</td><td>Xyleborus saxeseni</td><td>2.00</td><td>2.29</td><td>2.00</td><td>1.50</td></tr>
<tr><td>SCOLYTIDAE</td><td>Xyleborus monographus</td><td>2.00</td><td>2.50</td><td>2.00</td><td>1.40</td></tr>
<tr><td>SCOLYTIDAE</td><td>Xyleborus dryographus</td><td>2.00</td><td>2.50</td><td>2.00</td><td>1.50</td></tr>
<tr><td>SCOLYTIDAE</td><td>Xyleborus germanus</td><td>1.00</td><td>2.20</td><td>2.00</td><td>1.50</td></tr>
<tr><td>SCOLYTIDAE</td><td>Xyleborus alni</td><td>2.00</td><td>2.50</td><td>2.00</td><td>1.50</td></tr>
<tr><td>SCOLYTIDAE</td><td>Xyloterus domesticus</td><td>3.00</td><td>2.50</td><td>2.00</td><td>1.60</td></tr>
<tr><td>SCOLYTIDAE</td><td>Xyloterus signatus</td><td>3.00</td><td>2.50</td><td>2.00</td><td>1.50</td></tr>
<tr><td>SCOLYTIDAE</td><td>Xyloterus lineatus</td><td>3.00</td><td>2.29</td><td>2.00</td><td>1.50</td></tr>
<tr><td>SCOLYTIDAE</td><td>Xyloterus laevae</td><td>3.00</td><td>2.50</td><td>2.00</td><td>1.50</td></tr>
<tr><td>PLATYPODIDAE</td><td>Platypus cylindrus</td><td>5.00</td><td>2.80</td><td>2.00</td><td>1.40</td></tr>
<tr><td>PLATYPODIDAE</td><td>Platypus oxyurus</td><td>5.00</td><td>2.80</td><td>2.00</td><td>1.50</td></tr>
<tr><td>CURCULIONIDAE</td><td>Cossonus parallelepipedus</td><td>5.00</td><td>3.80</td><td>3.00</td><td>2.00</td></tr>
<tr><td>CURCULIONIDAE</td><td>Cossonus linearis</td><td>5.00</td><td>3.00</td><td>3.00</td><td>2.00</td></tr>
<tr><td>CURCULIONIDAE</td><td>Rhyncolus elongatus</td><td>4.00</td><td>3.00</td><td>3.00</td><td>1.50</td></tr>
<tr><td>CURCULIONIDAE</td><td>Rhyncolus sculpturatus</td><td>4.00</td><td>2.71</td><td>3.00</td><td>1.50</td></tr>
<tr><td>CURCULIONIDAE</td><td>Rhyncolus ater</td><td>3.00</td><td>2.29</td><td>3.00</td><td>2.40</td></tr>
<tr><td>CURCULIONIDAE</td><td>Phloeophagus lignarius</td><td>3.00</td><td>3.00</td><td>3.00</td><td>2.00</td></tr>
<tr><td>CURCULIONIDAE</td><td>Phloeophagus thomsoni</td><td>3.00</td><td>3.80</td><td>3.00</td><td>2.17</td></tr>
<tr><td>CURCULIONIDAE</td><td>Stereocorynes truncorum</td><td>2.00</td><td>3.00</td><td>3.00</td><td>2.00</td></tr>
<tr><td>CURCULIONIDAE</td><td>Pissodes piceae</td><td>8.00</td><td>2.20</td><td>2.00</td><td>1.40</td></tr>
<tr><td>CURCULIONIDAE</td><td>Magdalis armigera</td><td>3.00</td><td>1.00</td><td>2.00</td><td>1.40</td></tr>
<tr><td>CURCULIONIDAE</td><td>Magdalis phlegmatica</td><td>4.00</td><td>1.00</td><td>2.00</td><td>1.40</td></tr>
<tr><td>CURCULIONIDAE</td><td>Magdalis nitida</td><td>4.00</td><td>1.00</td><td>2.00</td><td>1.40</td></tr>
<tr><td>CURCULIONIDAE</td><td>Magdalis duplicata</td><td>3.00</td><td>1.00</td><td>2.00</td><td>1.40</td></tr>
<tr><td>CURCULIONIDAE</td><td>Trachodes hispidus</td><td>3.00</td><td>1.00</td><td>3.50</td><td>2.25</td></tr>
<tr><td>CURCULIONIDAE</td><td>Hylobius abietis</td><td>10.00</td><td>2.50</td><td>2.00</td><td>1.50</td></tr>
<tr><td>CURCULIONIDAE</td><td>Dryophthorus corticalis</td><td>3.00</td><td>3.80</td><td>3.40</td><td>1.50</td></tr>
<tr><td>CURCULIONIDAE</td><td>Camptorhinus statua</td><td>7.00</td><td>3.00</td><td>2.00</td><td>1.00</td></tr>
<tr><td>CURCULIONIDAE</td><td>Acalles roboris</td><td>3.00</td><td>1.20</td><td>3.25</td><td>2.00</td></tr>
<tr><td>CURCULIONIDAE</td><td>Acalles pyrenaeus</td><td>3.00</td><td>1.20</td><td>3.25</td><td>2.00</td></tr>
<tr><td>CURCULIONIDAE</td><td>Acalles camelus</td><td>2.00</td><td>2.00</td><td>3.25</td><td>2.50</td></tr>
<tr><td>CURCULIONIDAE</td><td>Acalles parvulus</td><td>2.00</td><td>1.20</td><td>3.25</td><td>2.00</td></tr>
<tr><td>CURCULIONIDAE</td><td>Acalles dubius</td><td>2.00</td><td>1.20</td><td>3.25</td><td>2.00</td></tr>
<tr><td>CURCULIONIDAE</td><td>Acalles lemur</td><td>2.00</td><td>1.20</td><td>3.25</td><td>2.00</td></tr>
<tr><td>CURCULIONIDAE</td><td>Acalles echinatus</td><td>2.00</td><td>1.20</td><td>3.25</td><td>2.00</td></tr>
<tr><td>CURCULIONIDAE</td><td>Acalles commutatus</td><td>2.00</td><td>1.20</td><td>3.25</td><td>2.33</td></tr>
<tr><td>CURCULIONIDAE</td><td>Acalles micros</td><td>1.00</td><td>1.20</td><td>3.25</td><td>2.33</td></tr>
<tr><td>CURCULIONIDAE</td><td>Acalles ptinoides</td><td>2.00</td><td>1.20</td><td>3.25</td><td>1.50</td></tr>
<tr><td>CURCULIONIDAE</td><td>Acalles hypocrita</td><td>4.00</td><td>1.20</td><td>3.25</td><td>2.00</td></tr>
<tr><td>CURCULIONIDAE</td><td>Acallocrates denticollis</td><td>4.00</td><td>1.20</td><td>3.25</td><td>2.00</td></tr>
</table>

Appendix S4: Phylogeny

Figure S4-1: Final phylogenetic tree of the 752 saproxylic beetle species sampled in the study. The tree was constructed using the topology provided in the phylogeny of Hunt et al. (2007) as a basic tree. The topology was expanded with the phylogenies of subgroups and with taxonomical information (see Material and methods). The final tree was calibrated with 24 fossil records. Note: To read the species name, zoom in.

We constructed a phylogenetic tree of the sampled saproxylic beetles to control for relationships of species in trait-environment correlations and to calculate the phylogenetic diversity of assemblages. The current phylogeny of beetles is still under debate (Hunt et al. 2007; Lawrence et al. 2011). Therefore, we decided to use the most comprehensive genetic phylogeny provided by Hunt et al. (2007) as a basic topology. We expanded this tree using higher-resolution topology of several subgroups (for Ciidae Buder et al. 2008; for Scolytinae Bussler et al. 2011; for Curculionidae Jordal et al. 2011; for Elateridae Kundrata & Bocak 2011), and we used additional information from taxonomic classification following the Catalogue of the Palaearctic Coleoptera (Löbl & Smetana 2003-2011). We constructed a tree using the function as.phylo in the add-on package ape (Paradis et al. 2004) within the framework of R version 2.13.1 (RDevelopmentCoreTeam 2011). The final tree topology was calibrated using 24 calibration points (Table S4-1) for certain nodes using the function bladj in the add-on package phylocom (Webb et al. 2008).

Table S4-1: Calibration points used in the phylogenetic tree predicted from fossil records.

<table>
<tr><td>Age (million years)</td><td>Taxon</td><td>Reference</td></tr>
<tr><td>285</td><td>Oldest beetle</td><td>(Hunt et al. 2007)</td></tr>
<tr><td>150.8 ± 4.0</td><td>Scarabaeoidea</td><td>(Hunt et al. 2007)</td></tr>
<tr><td>216.5 ± 2.0</td><td>Staphylinidae</td><td>(Hunt et al. 2007)</td></tr>
<tr><td>196.5 ± 1.0</td><td>Elateridae</td><td>(Hunt et al. 2007)</td></tr>
<tr><td>95</td><td>Bostrichiformia</td><td>(Grimaldi &amp; Engels 2003)</td></tr>
<tr><td>80</td><td>Oldest Ripihoridae</td><td>(Grimaldi &amp; Engels 2003)</td></tr>
<tr><td>181</td><td>Tenebrionoidea</td><td>(Wang &amp; Zhang 2011)</td></tr>
<tr><td>150.8</td><td>Chrysomelidae</td><td>(Hunt et al. 2007)</td></tr>
<tr><td>150</td><td>Mordellidae</td><td>(Hunt et al. 2007)</td></tr>
<tr><td>130</td><td>Scolytinae</td><td>(Kirejtshuk et al. 2009)</td></tr>
<tr><td>80</td><td>Cryptophagidae</td><td>(Zherikhin 1977)</td></tr>
<tr><td>37</td><td>Cryphalus</td><td>(Kirejtshuk 2009)</td></tr>
<tr><td>31</td><td>Dryoecoetus</td><td>(Kirejtshuk 2009)</td></tr>
<tr><td>37</td><td>Taphrorychus</td><td>(Kirejtshuk 2009)</td></tr>
<tr><td>20</td><td>Gnathotrichus</td><td>(Kirejtshuk 2009)</td></tr>
<tr><td>37</td><td>Ips</td><td>(Kirejtshuk 2009)</td></tr>
<tr><td>37</td><td>Tomicus</td><td>(Kirejtshuk 2009)</td></tr>
<tr><td>20</td><td>Pitophterus</td><td>(Kirejtshuk 2009)</td></tr>
<tr><td>37</td><td>Hylastes</td><td>(Kirejtshuk 2009)</td></tr>
<tr><td>31</td><td>Hylesinus</td><td>(Kirejtshuk 2009)</td></tr>
<tr><td>37</td><td>Hylurgops</td><td>(Kirejtshuk 2009)</td></tr>
<tr><td>20</td><td>Scolytus</td><td>(Kirejtshuk 2009)</td></tr>
<tr><td>37</td><td>Xyleborus</td><td>(Kirejtshuk 2009)</td></tr>
<tr><td>37</td><td>Xylechinus</td><td>(Kirejtshuk 2009)</td></tr>
</table>

Appendix S5: Relationship of body size and niche positions of species to forest-use intensity

Figure S5-1: Correlation of body size and niche position of species (Europe-wide scale: 704 species, regional scale: 284 species) and forest-use intensity extracted from the first two CCA axes (conifer axis: CCA1 on the Europe-wide scale and CCA2 on the regional scale; dead wood/veteran tree axis: CCA2 on the Europe-wide scale and CCA1 on the regional scale). Significant correlations (p < 0.05) are indicated by a regression line.

Appendix S6: Results of linear regression analysis

Table S6-1: Results of a generalized linear mixed effect model (lmer) using the forest stand as random factor and showing the effects of predictor variables on overall phylogenetic and functional diversity and the diversity of single traits. Predictor variables included geographic, landscape, local climate, and local habitat variables. Single traits on the Europe-wide scale included body size, dead-wood diameter niche, dead-wood decay niche, and canopy cover niche. Standardized effect sizes for the mean pairwise distance (dispersion) were used as response variable. Significant values (p < 0.05) are in bold, and marginally not significant values (p < 0.10) are in bold italics. Note that R²-values were calculated based on fixed effects only.

<table>
<tr><td>Variable type</td><td>Variable</td><td></td><td>Phylogenetic diversity</td><td>Phylogenetic diversity</td><td></td><td>Functional diversity</td><td>Functional diversity</td><td></td><td>Body size</td><td>Body size</td><td></td><td>Diameter niche</td><td>Diameter niche</td><td></td><td>Decay niche</td><td>Decay niche</td><td></td><td>Canopy cover niche</td><td>Canopy cover niche</td></tr>
<tr><td>Variable type</td><td>Variable</td><td></td><td>z-value</td><td>p-value</td><td></td><td>z-value</td><td>p-value</td><td></td><td>z-value</td><td>p-value</td><td></td><td>z-value</td><td>p-value</td><td></td><td>z-value</td><td>p-value</td><td></td><td>z-value</td><td>p-value</td></tr>
<tr><td>Intercept</td><td></td><td></td><td></td><td>&lt;0.001</td><td></td><td></td><td>&lt;0.001</td><td></td><td></td><td>&lt;0.001</td><td></td><td></td><td>&lt;0.001</td><td></td><td></td><td>&lt;0.001</td><td></td><td></td><td>&lt;0.001</td></tr>
<tr><td>Geographic</td><td>Latitude</td><td></td><td>1.395</td><td>0.163</td><td></td><td></td><td>0.262</td><td></td><td></td><td>0.402</td><td></td><td></td><td>0.026</td><td></td><td></td><td>0.661</td><td></td><td>1.436</td><td>0.151</td></tr>
<tr><td>Geographic</td><td>Longitude</td><td></td><td>2.714</td><td>0.007</td><td></td><td>3.787</td><td>&lt;0.001</td><td></td><td>2.404</td><td>0.016</td><td></td><td>2.347</td><td>0.019</td><td></td><td></td><td>0.013</td><td></td><td>5.652</td><td>&lt;0.001</td></tr>
<tr><td>Landscape</td><td>Forest area</td><td></td><td></td><td>0.035</td><td></td><td></td><td>0.494</td><td></td><td>0.222</td><td>0.825</td><td></td><td></td><td>0.466</td><td></td><td></td><td>0.021</td><td></td><td>0.839</td><td>0.401</td></tr>
<tr><td>Landscape</td><td>Broad-leaf trees</td><td></td><td>2.659</td><td>0.008</td><td></td><td></td><td>0.689</td><td></td><td></td><td>0.040</td><td></td><td></td><td>0.155</td><td></td><td></td><td>0.328</td><td></td><td>5.058</td><td>&lt;0.001</td></tr>
<tr><td>Landscape</td><td>Urban area</td><td></td><td></td><td>0.222</td><td></td><td></td><td>0.002</td><td></td><td></td><td>&lt;0.001</td><td></td><td></td><td>0.009</td><td></td><td></td><td>0.777</td><td></td><td></td><td>0.539</td></tr>
<tr><td>Local climate</td><td>Temperature</td><td></td><td>2.643</td><td>0.008</td><td></td><td></td><td>0.045</td><td></td><td>0.427</td><td>0.670</td><td></td><td></td><td>0.003</td><td></td><td>0.061</td><td>0.951</td><td></td><td></td><td>0.009</td></tr>
<tr><td>Local climate</td><td>Precipitation</td><td></td><td>1.978</td><td>0.048</td><td></td><td>0.270</td><td>0.787</td><td></td><td></td><td>0.654</td><td></td><td>0.124</td><td>0.902</td><td></td><td></td><td>0.412</td><td></td><td>1.723</td><td>0.085</td></tr>
<tr><td>Local habitat</td><td>Protection</td><td></td><td>0.951</td><td>0.342</td><td></td><td></td><td>0.543</td><td></td><td></td><td>0.450</td><td></td><td></td><td>0.294</td><td></td><td>1.157</td><td>0.247</td><td></td><td>0.310</td><td>0.756</td></tr>
<tr><td>Local habitat</td><td>Veteran trees</td><td></td><td>0.266</td><td>0.791</td><td></td><td>1.614</td><td>0.107</td><td></td><td>1.604</td><td>0.109</td><td></td><td>1.520</td><td>0.128</td><td></td><td></td><td>0.180</td><td></td><td>1.513</td><td>0.130</td></tr>
<tr><td>Local habitat</td><td>Dead wood</td><td></td><td></td><td>0.120</td><td></td><td></td><td>0.522</td><td></td><td>3.588</td><td>&lt;0.001</td><td></td><td></td><td>&lt;0.001</td><td></td><td></td><td>0.124</td><td></td><td></td><td>0.257</td></tr>
<tr><td>Local habitat</td><td>Tree diversity</td><td></td><td>1.604</td><td>0.109</td><td></td><td>0.769</td><td>0.442</td><td></td><td></td><td>0.984</td><td></td><td>2.362</td><td>0.018</td><td></td><td>0.479</td><td>0.632</td><td></td><td></td><td>0.407</td></tr>
<tr><td>Local habitat</td><td>Conifers</td><td></td><td></td><td>0.169</td><td></td><td></td><td>0.657</td><td></td><td></td><td>0.737</td><td></td><td></td><td>0.985</td><td></td><td>0.277</td><td>0.781</td><td></td><td>1.042</td><td>0.297</td></tr>
<tr><td>Multiple R²</td><td>Multiple R²</td><td></td><td>0.134</td><td>0.134</td><td></td><td>0.109</td><td>0.109</td><td></td><td>0.488</td><td>0.488</td><td></td><td>0.181</td><td>0.181</td><td></td><td>0.032</td><td>0.032</td><td></td><td>0.156</td><td>0.156</td></tr>
</table>

Table S6-2: Results of a generalized linear mixed effect model (lmer) using the forest stand as random factor and showing the effects of predictor variables. Predictor variables included geographic, landscape, local climate, and local habitat variables. Single traits on the Europe-wide scale included mean body size and position at the niche axis of dead-wood diameter, dead-wood decay stage, and canopy cover. Significant values (p < 0.05) are in bold; marginally not significant values (p < 0.10) are in bold italics. Note that R²-values were calculated based on fixed effects only.

<table>
<tr><td>Variable type</td><td>Variable</td><td></td><td>Body size</td><td>Body size</td><td></td><td>Diameter niche axis</td><td>Diameter niche axis</td><td></td><td>Decay niche axis</td><td>Decay niche axis</td><td></td><td>Canopy cover niche axis</td><td>Canopy cover niche axis</td></tr>
<tr><td>Variable type</td><td>Variable</td><td></td><td>z-value</td><td>p-value</td><td></td><td>z-value</td><td>p-value</td><td></td><td>z-value</td><td>p-value</td><td></td><td>z-value</td><td>p-value</td></tr>
<tr><td>Geographic</td><td>Latitude</td><td></td><td></td><td>0.041</td><td></td><td>5.315</td><td>&lt;0.001</td><td></td><td>2.747</td><td>0.006</td><td></td><td>3.794</td><td>&lt;0.001</td></tr>
<tr><td>Geographic</td><td>Longitude</td><td></td><td>3.703</td><td>&lt;0.001</td><td></td><td>0.194</td><td>0.846</td><td></td><td>3.934</td><td>&lt;0.001</td><td></td><td>1.887</td><td>0.059</td></tr>
<tr><td>Landscape</td><td>Forest area</td><td></td><td></td><td>0.878</td><td></td><td></td><td>0.007</td><td></td><td></td><td>0.084</td><td></td><td>0.340</td><td>0.734</td></tr>
<tr><td>Landscape</td><td>Broad-leaf trees</td><td></td><td></td><td>0.013</td><td></td><td></td><td>0.971</td><td></td><td>1.567</td><td>0.117</td><td></td><td>4.528</td><td>&lt;0.001</td></tr>
<tr><td>Landscape</td><td>Urban area</td><td></td><td></td><td>0.052</td><td></td><td>1.718</td><td>0.086</td><td></td><td></td><td>0.880</td><td></td><td></td><td>0.326</td></tr>
<tr><td>Local climate</td><td>Temperature</td><td></td><td>0.816</td><td>0.415</td><td></td><td>3.464</td><td>&lt;0.001</td><td></td><td>1.934</td><td>0.053</td><td></td><td>0.737</td><td>0.461</td></tr>
<tr><td>Local climate</td><td>Precipitation</td><td></td><td></td><td>0.139</td><td></td><td>1.070</td><td>0.285</td><td></td><td>2.411</td><td>0.016</td><td></td><td>5.729</td><td>&lt;0.001</td></tr>
<tr><td>Local habitat</td><td>Protection</td><td></td><td>0.168</td><td>0.866</td><td></td><td>3.913</td><td>&lt;0.001</td><td></td><td>1.098</td><td>0.272</td><td></td><td>0.780</td><td>0.435</td></tr>
<tr><td>Local habitat</td><td>Veteran trees</td><td></td><td>0.716</td><td>0.474</td><td></td><td>1.843</td><td>0.065</td><td></td><td>2.976</td><td>0.003</td><td></td><td>2.112</td><td>0.035</td></tr>
<tr><td>Local habitat</td><td>Dead wood</td><td></td><td>3.797</td><td>&lt;0.001</td><td></td><td>3.053</td><td>0.002</td><td></td><td>0.769</td><td>0.442</td><td></td><td></td><td>0.035</td></tr>
<tr><td>Local habitat</td><td>Tree diversity</td><td></td><td></td><td>0.963</td><td></td><td></td><td>0.632</td><td></td><td></td><td>0.125</td><td></td><td>1.503</td><td>0.133</td></tr>
<tr><td>Local habitat</td><td>Conifers</td><td></td><td></td><td>0.466</td><td></td><td>0.481</td><td>0.631</td><td></td><td>1.623</td><td>0.105</td><td></td><td>0.152</td><td>0.879</td></tr>
<tr><td>Multiple R²</td><td>Multiple R²</td><td></td><td>0.108</td><td>0.108</td><td></td><td>0.334</td><td>0.334</td><td></td><td>0.139</td><td>0.139</td><td></td><td>0.169</td><td>0.169</td></tr>
</table>

Table S6-3: Results of linear regression analyses fitted by the linear model function (lm) showing the effects of predictor variables on overall phylogenetic and functional diversity as well as diversity of single traits. Single traits on the regional scale included body size, dead-wood diameter niche, dead-wood decay niche, and canopy cover niche. Standardized effect sizes for the mean pairwise distance (dispersion) were used as response variable. For all these measurements, significant z-values above zero indicate trend from clumping to overdispersion of the assemblage characteristic along the respective predictor, and values below zero indicate the opposite (Pausas & Verdu 2010). Significant values (p < 0.05) are in bold; marginally not significant values (p < 0.10) are in bold italics.

<table>
<tr><td></td><td></td><td>Phylogenetic</td><td>Phylogenetic</td><td></td><td>Functional</td><td>Functional</td><td></td><td>Body size</td><td>Body size</td><td></td><td>Diameter</td><td>Diameter</td><td></td><td>Decay</td><td>Decay</td><td></td><td>Canopy cover</td><td>Canopy cover</td></tr>
<tr><td>Variable</td><td></td><td>t-value</td><td>p-value</td><td></td><td>t-value</td><td>p-value</td><td></td><td>t-value</td><td>p-value</td><td></td><td>t-value</td><td>p-value</td><td></td><td>t-value</td><td>p-value</td><td></td><td>t-value</td><td>p-value</td></tr>
<tr><td>Intercept</td><td></td><td></td><td>0.007</td><td></td><td></td><td>0.210</td><td></td><td></td><td>0.813</td><td></td><td></td><td>0.748</td><td></td><td></td><td>0.700</td><td></td><td></td><td>0.056</td></tr>
<tr><td>Protection</td><td></td><td>0.682</td><td>0.498</td><td></td><td>0.391</td><td>0.697</td><td></td><td></td><td>0.630</td><td></td><td>0.209</td><td>0.836</td><td></td><td>2.101</td><td>0.040</td><td></td><td></td><td>0.980</td></tr>
<tr><td>Veteran trees</td><td></td><td>0.546</td><td>0.587</td><td></td><td></td><td>0.546</td><td></td><td></td><td>0.270</td><td></td><td>0.444</td><td>0.659</td><td></td><td></td><td>0.692</td><td></td><td>0.249</td><td>0.804</td></tr>
<tr><td>Dead wood</td><td></td><td>1.788</td><td>0.079</td><td></td><td>0.470</td><td>0.640</td><td></td><td>2.538</td><td>0.014</td><td></td><td></td><td>0.012</td><td></td><td></td><td>0.164</td><td></td><td>1.641</td><td>0.106</td></tr>
<tr><td>Tree diversity</td><td></td><td>0.234</td><td>0.816</td><td></td><td></td><td>0.424</td><td></td><td></td><td>0.295</td><td></td><td>0.778</td><td>0.439</td><td></td><td></td><td>0.388</td><td></td><td></td><td>0.769</td></tr>
<tr><td>Conifers</td><td></td><td></td><td>0.114</td><td></td><td></td><td>0.322</td><td></td><td></td><td>0.102</td><td></td><td>0.373</td><td>0.710</td><td></td><td>0.690</td><td>0.493</td><td></td><td></td><td>0.415</td></tr>
<tr><td>Multiple R²</td><td></td><td>0.181</td><td>0.181</td><td></td><td>0.041</td><td>0.041</td><td></td><td>0.068</td><td>0.068</td><td></td><td>0.050</td><td>0.050</td><td></td><td>0.042</td><td>0.042</td><td></td><td>0.027</td><td>0.027</td></tr>
</table>

Table S6-4: Results of linear regression analyses fitted by the linear model function (lm) showing the effects of predictor variables on mean body size and mean position at the niche axis of dead-wood diameter, dead-wood decay stage, and canopy cover on the regional scale. Analysis is based on the complete data set (flight-interception traps, hand collection). Significant values (p < 0.05) are in bold; marginally not significant values (p < 0.10) are in bold italics.

<table>
<tr><td></td><td></td><td>Body size</td><td>Body size</td><td></td><td>Diameter niche axis</td><td>Diameter niche axis</td><td></td><td>Decay niche axis</td><td>Decay niche axis</td><td></td><td>Canopy cover niche axis</td><td>Canopy cover niche axis</td></tr>
<tr><td>Variable</td><td></td><td>t-value</td><td>p-value</td><td></td><td>t-value</td><td>p-value</td><td></td><td>t-value</td><td>p-value</td><td></td><td>t-value</td><td>p-value</td></tr>
<tr><td>Protection</td><td></td><td></td><td>0.264</td><td></td><td>1.550</td><td>0.126</td><td></td><td>0.646</td><td>0.521</td><td></td><td>0.878</td><td>0.383</td></tr>
<tr><td>Veteran trees</td><td></td><td></td><td>0.550</td><td></td><td>0.542</td><td>0.590</td><td></td><td>0.721</td><td>0.474</td><td></td><td></td><td>0.787</td></tr>
<tr><td>Dead wood</td><td></td><td>2.798</td><td>0.007</td><td></td><td>2.751</td><td>0.008</td><td></td><td>2.766</td><td>0.007</td><td></td><td>1.599</td><td>0.115</td></tr>
<tr><td>Tree diversity</td><td></td><td></td><td>0.784</td><td></td><td></td><td>0.885</td><td></td><td>0.101</td><td>0.920</td><td></td><td></td><td>0.781</td></tr>
<tr><td>Conifers</td><td></td><td></td><td>0.329</td><td></td><td></td><td>0.070</td><td></td><td></td><td>0.460</td><td></td><td></td><td>0.694</td></tr>
<tr><td>Multiple R²</td><td></td><td>0.123</td><td>0.123</td><td></td><td>0.438</td><td>0.438</td><td></td><td>0.313</td><td>0.313</td><td></td><td>0.128</td><td>0.128</td></tr>
</table>

Appendix S7: Correlation of individuals and mean body size

Figure S7-1:

Appendix S8: Correlation of effect sizes of single traits

Figure S8-1: Correlation plots of the standardized effect size for the mean pairwise distance for the functional diversity based on a Euclidian distance matrix for each trait (see Materials and methods for details). For all these measurements, values above zero indicate overdispersion of the assemblage characteristic, and values below zero indicate clumping of the characteristic (Pausas & Verdu 2010). Significant correlations (p < 0.05) are indicated by a regression line. Each data point represents one plot on the Europe-wide scale (1,156 in total).

Appendix S9: Correlation of dead-wood amount and mean body size and niche positions

Figure S9-1: Correlation of dead-wood amount and mean body size and mean niche positions of saproxylic beetle assemblages. The gray symbols show data per plots of the regional study in the Steigerwald. The black symbols indicate the mean values of the three dead-wood classes of the Europe-wide study. For illustration, the scales of the original classification of dead-wood diameter, dead-wood decay stage, and canopy cover niche are given on the right y-axis.

Appendix S10: Correlation of dead-wood amount and maximum dead-wood diameter

Figure S10-1: Correlation of dead-wood amount and maximum diameter of logs of 242 circular sampling plots of the regional study in the Steigerwald. Note that structural parameters were assessed on a higher number of plots than beetle assemblages. Pearson's product-moment correlation: t = 11, df = 240, p < 0.001, R² = 0.37.

Appendix S11: Supporting information references

Albrecht, L. 1990. Grundlagen, Ziele und Methodik der waldökologischen Forschung in Naturwaldreservaten. Schriftenreihe Naturwaldreservate in Bayern 1:1-221.

Bjørnstad, O. N., and W. Falck. 2001. Nonparametric spatial covariance functions: estimation and testing. Environmental and Ecological Statistics 8:53-70.

Buder, G., C. Grossmann, A. Hundsdörfer, and K.-D. Klass. 2008. A Contribution to the Phylogeny of the Ciidae and its Relationships with Other Cucujoid and Tenebrionoid Beetles (Coleoptera: Cucujiformia). Arthropod Systematics & Phylogeny 66:165 -190.

Bussler, H., C. Bouget, H. Brustel, M. Brändle, V. Riedinger, R. Brandl, and J. Müller. 2011. Abundance and pest classification of scolytid species (Coleoptera: Curculionidae, Scolytinae) follow different patterns. Forest Ecology and Management 262:1887-1894.

Grimaldi, D., and M. S. Engels 2003. Evolution of Insects. Cambridge University Press, New York, USA.

Hijmans, R. J., S. E. Cameron, J. L. Parra, P. G. Jones, and A. Jarvis. 2005. Very high resolution interpolated climate surface for global land areas. International Journal of Climatology 25:1965-1978.

Hunt, T., et al. 2007. A comprehensive phylogeny of beetles reveals the evolutionary origins of a superradiation. Science 318:1913-1916.

Jordal, B. H., A. S. Sequeira, and A. I. Cognato. 2011. The age and phylogeny of wood boring weevils and the origin of subsociality. Molecular Phylogenetics and Evolution 59:708-724.

Kirejtshuk, A. G. 2009. Family Scolytidae Latr., 1804 - bark beetles: Atlas of extinct groups of beetles bark beetle. .

Kirejtshuk, A. G., D. Azar, R. Beaver, M. Mandelshtam, and A. Nel. 2009. The most ancient bark beetle known: a new tribe, genus and species from Lebanese amber (Coleoptera, Curculionidae, Scolytinae). Systematic Ecology 31:101-112.

Kundrata, R., and L. Bocak. 2011. The phylogeny and limits of Elateridae (Insecta, Coleoptera): is there a common tendency of click beetles to soft-bodiedness and neoteny? Zoologica Scripta 40:364-378.

Lawrence, J. F., A. Ślipiński, A. E. Seago, M. K. Thayer, A. F. Newton, and A. E. Marvaldi. 2011. Phylogeny of the Coleoptera Based on Morphological Characters of Adults and Larvae. Annales Zoologici 61:1-217.

Löbl, I., and A. Smetana, editors. 2003-2011. Catalogue of the Palearctic Coleoptera Volume I-VI. Apollo Books, Stenstrup.

Möller, G. 2009. Struktur- und Substratbindung holzbewohnender Insekten, Schwerpunkt Coleoptera - Käfer. Page 284. Fachbereich Biologie, Chemie, Pharmazie. Freien Universität Berlin, Berlin.

Paradis, E., J. Claude, and K. Strimmer. 2004. APE: analyses of phylogenetics and evolution in R language. Bioinformatics 20:289-290.

Pausas, J. G., and M. Verdu. 2010. The Jungle of Methods for Evaluating Phenotypic and Phylogenetic Structure of Communities. Bioscience 60:614-625.

RDevelopmentCoreTeam. 2011. R: A language and environment for statistical computing. R Foundation for Statistical Computing, Vienna, Austria.

Wang, B., and H. Zhang. 2011. The oldest Tenebrionoidea (Coleoptera) from the Middle Jurassic of China. Journal of Paleontology 85:266-270.

Webb, C. O., D. D. Ackerly, and S. W. Kembel. 2008. Phylocom: software for the analysis of phylogenetic community structure and trait evolution. Bioinformatics 24:2098-2100.

Zherikhin, V. V. 1977. Families Cerophytidae, Acanthocnemidae, Cryptophagidae, Lathridiidae, Attelabidae, Curculionidae. Pages 130-182 in B. B. Rohdendorf, editor. Mesozoic Coleoptera, Moscow: Nauka.