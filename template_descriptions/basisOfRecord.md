Definition: The nature of the data record, decided PER MEASUREMENT based on how that measurement was obtained. Different measurements in the same paper can differ.

You are tagging ONE measurement type. Judge it by what that measurement is, not the paper as a whole.

Valid values (Darwin Core):


PreservedSpecimen: measured off a collected/preserved specimen (pinned, dried, in ethanol, museum/voucher). Use for MORPHOLOGY — body size, wing length, tibia length, mandible length, weight, anything measured with calipers/microscope/imaging on a dead specimen.
LivingSpecimen: organism alive and maintained (zoo, garden, culture collection).
HumanObservation: depends on a human/personal observation of live organism in situ. Use for BEHAVIOUR / ECOLOGY — nesting material, larval diet, pollen transport, foraging, activity time, phenology.
Plain Examples for HumanObservation: 
"evidence of a dwc:Occurrence taken from field notes or literature"
"a record of a dwc:Occurrence without physical evidence or evidence captured with a machine"
Occurrence:	A Event that establishes the state of a Organism at a particular place and time.


Rule: morphological/physical trait -> PreservedSpecimen; behavioural/ecological/natural-history trait -> HumanObservation; if neither clearly applies -> Occurrence. Collecting specimens doesn't make a behaviour PreservedSpecimen; observing a live animal doesn't make a body measurement HumanObservation.

If not stated, infer from the methods (e.g. "specimens pinned and deposited" implies morphology is PreservedSpecimen).
