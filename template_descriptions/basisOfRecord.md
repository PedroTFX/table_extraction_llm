Definition: The nature of the data record, decided PER MEASUREMENT based on WHERE this study got the value. Different measurements in the same paper can differ.

You are tagging ONE measurement type. Judge it by how THIS paper obtained that measurement's values, not the paper as a whole.

Valid values (Darwin Core):

MaterialCitation: the values were NOT measured or observed by the authors in this study — they were compiled from published literature, identification keys, trait databases, or other studies (e.g. "trait values were obtained from Bousquet 2010", "diet was assigned from the literature", "data from the BWARS database"). Typical for categorical life-history traits (diet, nesting, sociality, voltinism, habitat preference) that papers look up rather than measure.
PreservedSpecimen: measured by the authors off collected/preserved specimens (pinned, dried, in ethanol, museum/voucher). Use for MORPHOLOGY the authors measured — body size, wing length, tibia length, mandible length, weight, anything taken with calipers/microscope/imaging on a dead specimen.
LivingSpecimen: measured on live organisms kept or reared by the authors (lab cultures, rearing, experiments on live animals — e.g. development time, fecundity, thermal tolerance).
HumanObservation: the authors observed live organisms in situ (field observations of behaviour, foraging, nesting, activity) without keeping a specimen.
MaterialSample: measured on a sample or part of an organism (tissue, gut content, DNA) rather than the whole specimen.
Occurrence: only when none of the above fits.

Rule: first ask whether the authors produced the value themselves. If it was taken from literature/databases/other studies -> MaterialCitation. If the authors produced it: morphology measured on specimens -> PreservedSpecimen; experiments/rearing on live animals -> LivingSpecimen; field observation of behaviour/ecology -> HumanObservation.

If not stated, infer from the methods (e.g. "specimens pinned and deposited" implies morphology is PreservedSpecimen; "traits were extracted from the literature" implies MaterialCitation). Answer with exactly one of the terms above.
