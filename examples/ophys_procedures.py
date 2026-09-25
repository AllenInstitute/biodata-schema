"""0phys procedure mouse 625100"""

import argparse
import datetime

from biodata_models.brain_atlas import CCFv3
from biodata_models.coordinates import AxisName, Direction, Origin
from biodata_models.organizations import Organization
from biodata_models.pid_names import PIDName
from biodata_models.reagent import FluorophoreType, StainType
from biodata_models.registries import Registry
from biodata_models.species import Species
from biodata_models.units import SizeUnit, VolumeUnit

from biodata_schema.components.configs import ProbeConfig
from biodata_schema.components.coordinates import Axis, CoordinateSystem, ReferenceCoordinateSystem, Translation
from biodata_schema.components.devices import FiberProbe
from biodata_schema.components.injection_procedures import InjectionDynamics, InjectionProfile, ViralMaterial
from biodata_schema.components.reagent import FluorescentStain, Fluorophore, ProbeReagent, ProteinProbe
from biodata_schema.components.surgery_procedures import (
    Anaesthetic,
    BrainInjection,
    Headframe,
    Perfusion,
    ProbeImplant,
)
from biodata_schema.core.procedures import (
    Procedures,
    SpecimenProcedure,
    Surgery,
    WaterRestriction,
)

BREGMA_ARI = CoordinateSystem(
    name="BREGMA_ARI",
    origin=Origin.BREGMA,
    axis_unit=SizeUnit.MM,
    axes=[
        Axis(name=AxisName.AP, direction=Direction.PA),
        Axis(name=AxisName.ML, direction=Direction.LR),
        Axis(name=AxisName.SI, direction=Direction.SI),
    ],
)

MPM_MANIP_RFB = CoordinateSystem(
    name="MPM_MANIP_RFB",
    origin=Origin.TIP,
    axis_unit=SizeUnit.MM,
    axes=[
        Axis(name=AxisName.X, direction=Direction.LR),
        Axis(name=AxisName.Y, direction=Direction.BF),
        Axis(name=AxisName.Z, direction=Direction.UD),
    ],
)

t = datetime.datetime(2022, 7, 12, 7, 00, 00)
t2 = datetime.datetime(2022, 9, 23, 10, 22, 00)

probe = FiberProbe(
    name="Probe A",
    core_diameter=200,
    numerical_aperture=0.37,
    ferrule_material="Ceramic",
    total_length=0.5,
)
config = ProbeConfig(
    primary_targeted_structure=CCFv3.VTA,
    device_name="Probe A",
    local_coordinate_system=MPM_MANIP_RFB,
    transform=[
        Translation(
            translation=[-600, -3050, 0],
        ),
        # insertion depth runs along the probe's own Z axis, which points down
        Translation(
            translation=[0, 0, 4200],
            reference_coordinate_system=ReferenceCoordinateSystem.LOCAL,
        ),
    ],
)


p = Procedures(
    subject_id="625100",
    global_coordinate_system=BREGMA_ARI,
    subject_procedures=[
        Surgery(
            start_date=t.date(),
            experimenters=["Scientist Smith"],
            ethics_review_id="2109",
            animal_weight_prior=22.6,
            animal_weight_post=22.3,
            anaesthesia=Anaesthetic(anaesthetic_type="Isoflurane", duration=180, level=1.5),
            workstation_id="SWS 3",
            protocol_id="doi",
            global_coordinate_system=BREGMA_ARI,
            procedures=[
                Headframe(
                    protocol_id="2109",
                    headframe_type="AI straight",
                    headframe_part_number="TO ENTER",
                    headframe_material="Titanium",
                ),
                BrainInjection(
                    protocol_id="5678",
                    injection_materials=[
                        ViralMaterial(
                            name="AAV2/1-Syn-Flex-ChrimsonR-tdT",
                            addgene_id=PIDName(
                                registry=Registry.ADDGENE,
                                name="62723-AAV5",
                                registry_identifier="v122159",
                            ),
                            titer=20000000000000,
                        )
                    ],
                    coordinate_system_name=BREGMA_ARI.name,
                    coordinates=[
                        [
                            Translation(
                                translation=[-600, -3050, 0],
                            ),
                            # depth runs down the needle's own axis; SI is positive downward
                            Translation(
                                translation=[0, 0, 4200],
                                reference_coordinate_system=ReferenceCoordinateSystem.LOCAL,
                            ),
                        ],
                    ],
                    dynamics=[
                        InjectionDynamics(
                            volume=400,
                            volume_unit=VolumeUnit.NL,
                            profile=InjectionProfile.BOLUS,
                        )
                    ],
                    targeted_structure=CCFv3.VTA,
                ),
                ProbeImplant(
                    protocol_id="TO ENTER",
                    implanted_device=probe,
                    device_config=config,
                ),
            ],
        ),
        WaterRestriction(
            start_date="2023-05-15",
            ethics_review_id="1234",
            target_fraction_weight=25,
            minimum_water_per_day=1.5,
            baseline_weight=20.4,
            end_date="2023-05-23",
        ),
        Surgery(
            start_date="2023-05-31",
            experimenters=["Scientist Smith"],
            ethics_review_id="2109",
            anaesthesia=Anaesthetic(anaesthetic_type="Isoflurane", duration=30, level=3),
            workstation_id="SWS 3",
            protocol_id="doi",
            procedures=[
                Perfusion(protocol_id="dx.doi.org/10.17504/protocols.io.bg5vjy66", output_specimen_ids={"672640"})
            ],
        ),
    ],
    specimen_procedures=[
        SpecimenProcedure(
            procedure_type="Immunolabeling",
            specimen_id="625100_001",
            start_date="2023-06-09",
            end_date="2023-06-12",
            experimenters=["Scientist Smith"],
            protocol_id=["TO ENTER"],
            procedure_details=[
                ProbeReagent(
                    name="Chicken polyclonal to GFP",
                    source=Organization.ABCAM,
                    rrid=PIDName(
                        name="Chicken polyclonal to GFP", registry=Registry.RRID, registry_identifier="ab13970"
                    ),
                    lot_number="GR3361051-16",
                    target=ProteinProbe(
                        protein=PIDName(name="GFP", registry=Registry.UNIPROT, registry_identifier="P42212"),
                        species=Species.CHICKEN,
                        mass=10,
                    ),
                )
            ],
            notes="Primary dilution factor 1:1000 ---final concentration is 10ug/ml",
        ),
        SpecimenProcedure(
            procedure_type="Immunolabeling",
            specimen_id="625100_001",
            start_date="2023-06-12",
            end_date="2023-06-13",
            experimenters=["Scientist Smith"],
            protocol_id=["TO ENTER"],
            procedure_details=[
                FluorescentStain(
                    name="Alexa Fluor 488 goat anti-chicken IgY (H+L)",
                    source=Organization.THERMO_FISHER_SCIENTIFIC,
                    rrid=PIDName(
                        name="Alexa Fluor 488 goat anti-chicken IgY (H+L)",
                        registry=Registry.RRID,
                        registry_identifier="A11039",
                    ),
                    lot_number="2420700",
                    probe=ProteinProbe(
                        protein=PIDName(
                            name="Anti-chicken IgY (H+L)",
                        ),
                        species=Species.GOAT,
                        mass=4,
                    ),
                    stain_type=StainType.PROTEIN,
                    fluorophore=Fluorophore(
                        fluorophore_type=FluorophoreType.ALEXA,
                        excitation_wavelength=488,
                        excitation_wavelength_unit="nanometer",
                    ),
                ),
            ],
            notes="Secondary dilution factor 1:500 - final concentration 4ug/ml",
        ),
    ],
)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default=None, help="Output directory for generated JSON file")
    args = parser.parse_args()

    serialized = p.model_dump_json()
    deserialized = Procedures.model_validate_json(serialized)
    deserialized.write_standard_file(prefix="ophys", output_directory=args.output_dir)
