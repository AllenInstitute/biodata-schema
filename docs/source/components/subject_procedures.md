# Subject_procedures

## Model definitions

### ClinicalVisit

Description of an outpatient clinical visit

| Field | Type | Title (Description) |
|-------|------|-------------|
| `start_date` | `datetime.date` | Start date  |
| `samples` | Optional[List[[SampleCollection](surgery_procedures.md#samplecollection)]] | Samples  |
| `surveys` | `Optional[List[str]]` | Surveys  |
| `diagnosis` | `Optional[List[biodata_models.human_disease.HumanDiseaseModel]]` | Diagnosis  |
| `treatment` | Optional[List[[Treatment](#treatment)]] | Treatment  |
| `notes` | `Optional[str]` | Notes  |


### FoodRestriction

Description of a food restriction procedure

| Field | Type | Title (Description) |
|-------|------|-------------|
| `ethics_review_id` | `str` | Ethics review ID  |
| `target_fraction_weight` | `int` | Target fraction weight (%)  |
| `target_fraction_weight_unit` | [UnitlessUnit](../biodata_models/units.md#unitlessunit) | Target fraction weight unit  |
| `minimum_food_per_day` | `float` | Minimum food per day  |
| `minimum_food_per_day_unit` | [MassUnit](../biodata_models/units.md#massunit) | Minimum food per day unit  |
| `baseline_weight` | `float` | Baseline weight (g) (Weight at start of food restriction) |
| `weight_unit` | [MassUnit](../biodata_models/units.md#massunit) | Weight unit  |
| `start_date` | `datetime.date` | Food restriction start date  |
| `end_date` | `Optional[datetime.date]` | Food restriction end date  |
| `protocol_id` | `Optional[str]` | Protocol ID (DOI for protocols.io) |


### GenericSubjectProcedure

Description of a non-surgical procedure performed on a subject

| Field | Type | Title (Description) |
|-------|------|-------------|
| `start_date` | `datetime.date` | Start date  |
| `experimenters` | `Optional[List[str]]` | experimenter(s)  |
| `ethics_review_id` | `str` | Ethics review ID  |
| `description` | `str` | Description  |
| `notes` | `Optional[str]` | Notes  |
| `protocol_id` | `Optional[str]` | Protocol ID (DOI for protocols.io) |


### NonSurgicalInjection

Injection procedure performed outside of surgery,
which may include one or more injections at different locations/depths

| Field | Type | Title (Description) |
|-------|------|-------------|
| `start_date` | `datetime.date` | Start date  |
| `ethics_review_id` | `str` | Ethics review ID  |
| `protocol_id` | `Optional[str]` | Protocol ID (DOI for protocols.io) |
| `injections` | List[[Injection](injection_procedures.md#injection)] | Injections  |
| `notes` | `Optional[str]` | Notes  |


### SelfAdministeredTreatment

Description of a treatment taken over a period of time (e.g. a prescription taken at home)

| Field | Type | Title (Description) |
|-------|------|-------------|
| `start_date` | `datetime.date` | Treatment start date  |
| `end_date` | `Optional[datetime.date]` | Treatment end date  |
| `notes` | `Optional[str]` | Notes  |
| `therapeutic` | [Reagent](reagent.md#reagent) or [Vaccine](reagent.md#vaccine) | Therapeutic  |
| `dose` | `Optional[float]` | Dose  |
| `dose_unit` | [MassUnit](../biodata_models/units.md#massunit) or [VolumeUnit](../biodata_models/units.md#volumeunit) or NoneType | Dose unit  |
| `dose_schedule` | `Optional[str]` | Dose schedule (Details on treatment schedule, e.g. once daily) |


### Surgery

Description of subject procedures performed at one time

| Field | Type | Title (Description) |
|-------|------|-------------|
| `start_date` | `datetime.date` | Start date  |
| `experimenters` | `Optional[List[str]]` | experimenter(s)  |
| `ethics_review_id` | `Optional[str]` | Ethics review ID  |
| `animal_weight_prior` | `Optional[float]` | Animal weight (g) (Animal weight before procedure) |
| `animal_weight_post` | `Optional[float]` | Animal weight (g) (Animal weight after procedure) |
| `weight_unit` | [MassUnit](../biodata_models/units.md#massunit) | Weight unit  |
| `anaesthesia` | Optional[[Anaesthetic](surgery_procedures.md#anaesthetic)] | Anaesthesia  |
| `workstation_id` | `Optional[str]` | Workstation ID  |
| `global_coordinate_system` | [CoordinateSystem](coordinates.md#coordinatesystem) or "Not applicable" | Surgery global coordinate system (Origin and axis definitions for coordinates within this surgery. Required when coordinates are provided. Use 'Not applicable' when no global coordinate system applies.) |
| `measured_coordinates` | Optional[Dict[[Origin](../biodata_models/coordinates.md#origin), [Translation](coordinates.md#translation)]] | Measured coordinates (Coordinates measured during the procedure, for example Bregma and Lambda) |
| `procedures` | List[[CatheterImplant](surgery_procedures.md#catheterimplant) or [Craniotomy](surgery_procedures.md#craniotomy) or [DeviceImplant](surgery_procedures.md#deviceimplant) or [ProbeImplant](surgery_procedures.md#probeimplant) or [Headframe](surgery_procedures.md#headframe) or [BrainInjection](surgery_procedures.md#braininjection) or [Injection](injection_procedures.md#injection) or [MyomatrixInsertion](surgery_procedures.md#myomatrixinsertion) or [GenericSurgeryProcedure](surgery_procedures.md#genericsurgeryprocedure) or [Perfusion](surgery_procedures.md#perfusion) or [SampleCollection](surgery_procedures.md#samplecollection)] | Procedures  |
| `notes` | `Optional[str]` | Notes  |
| `protocol_id` | `Optional[str]` | Protocol ID (DOI for protocols.io) |


### TrainingProtocol

Description of an animal training protocol

| Field | Type | Title (Description) |
|-------|------|-------------|
| `training_name` | `str` | Training protocol name  |
| `start_date` | `datetime.date` | Training protocol start date  |
| `end_date` | `Optional[datetime.date]` | Training protocol end date  |
| `curriculum_code` | Optional[[Code](identifiers.md#code)] | Curriculum code (Code describing the directed graph used for the training curriculum) |
| `notes` | `Optional[str]` | Notes  |
| `protocol_id` | `Optional[str]` | Protocol ID (DOI for protocols.io) |


### Treatment

Description of a treatment procedure

| Field | Type | Title (Description) |
|-------|------|-------------|
| `therapeutic` | [Reagent](reagent.md#reagent) or [Vaccine](reagent.md#vaccine) | Therapeutic  |
| `dose` | `Optional[float]` | Dose  |
| `dose_unit` | [MassUnit](../biodata_models/units.md#massunit) or [VolumeUnit](../biodata_models/units.md#volumeunit) or NoneType | Dose unit  |
| `dose_schedule` | `Optional[str]` | Dose schedule (Details on treatment schedule, e.g. once daily) |


### WaterRestriction

Description of a water restriction procedure

| Field | Type | Title (Description) |
|-------|------|-------------|
| `ethics_review_id` | `str` | Ethics review ID  |
| `target_fraction_weight` | `int` | Target fraction weight (%)  |
| `target_fraction_weight_unit` | [UnitlessUnit](../biodata_models/units.md#unitlessunit) | Target fraction weight unit  |
| `minimum_water_per_day` | `float` | Minimum water per day (mL)  |
| `minimum_water_per_day_unit` | [VolumeUnit](../biodata_models/units.md#volumeunit) | Minimum water per day unit  |
| `baseline_weight` | `float` | Baseline weight (g) (Weight at start of water restriction) |
| `weight_unit` | [MassUnit](../biodata_models/units.md#massunit) | Weight unit  |
| `start_date` | `datetime.date` | Water restriction start date  |
| `end_date` | `Optional[datetime.date]` | Water restriction end date  |
| `protocol_id` | `Optional[str]` | Protocol ID (DOI for protocols.io) |


