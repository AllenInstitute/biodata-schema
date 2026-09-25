"""ephys procedure mouse 625100"""

import argparse
from datetime import datetime, timezone

from biodata_models.brain_atlas import CCFv3
from biodata_models.coordinates import AxisName, Direction, Origin
from biodata_models.units import SizeUnit, VolumeUnit

from biodata_schema.components.configs import ProbeConfig
from biodata_schema.components.coordinates import (
    Axis,
    CoordinateSystem,
    ReferenceCoordinateSystem,
    Rotation,
    Translation,
)
from biodata_schema.components.devices import EphysProbe
from biodata_schema.components.injection_procedures import (
    InjectionDynamics,
    InjectionProfile,
    TarsVirusIdentifiers,
    ViralMaterial,
)
from biodata_schema.components.surgery_procedures import (
    Anaesthetic,
    BrainInjection,
    Craniotomy,
    CraniotomyType,
    Perfusion,
    ProbeImplant,
)
from biodata_schema.core.procedures import (
    Procedures,
    Surgery,
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

BREGMA_RAS = CoordinateSystem(
    name="BREGMA_RAS",
    origin=Origin.BREGMA,
    axis_unit=SizeUnit.MM,
    axes=[
        Axis(name=AxisName.ML, direction=Direction.LR),
        Axis(name=AxisName.AP, direction=Direction.PA),
        Axis(name=AxisName.SI, direction=Direction.IS),
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

# If a timezone isn't specified, the timezone of the computer running this
# script will be used as default
t = datetime(2022, 7, 12, 7, 00, 00, tzinfo=timezone.utc)
t2 = datetime(2022, 9, 23, 10, 22, 00, tzinfo=timezone.utc)

coordinate_system = BREGMA_RAS
coordinate_system.name = "LAMBDA_RAS"
coordinate_system.origin = Origin.LAMBDA

probe = EphysProbe(
    name="Probe A",
    probe_model="Neuropixels UHD (Fixed)",
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

surgery1 = Surgery(
    start_date=t.date(),
    protocol_id="doi",
    experimenters=["Scientist Smith"],
    ethics_review_id="2109",
    animal_weight_prior=22.6,
    animal_weight_post=22.3,
    anaesthesia=Anaesthetic(anaesthetic_type="Isoflurane", duration=1, level=1.5),
    global_coordinate_system=coordinate_system,
    workstation_id="SWS 3",
    procedures=[
        ProbeImplant(
            implanted_device=probe,
            device_config=config,
        ),
        Craniotomy(
            craniotomy_type=CraniotomyType.CIRCLE,
            protocol_id="1234",
            coordinate_system_name="LAMBDA_RAS",
            position=Translation(translation=[-2, 2, 0]),
            size=1,
            size_unit=SizeUnit.MM,
        ),
        BrainInjection(
            protocol_id="5678",
            injection_materials=[
                ViralMaterial(
                    name="AAV2-Flex-ChrimsonR",
                    tars_identifiers=TarsVirusIdentifiers(
                        virus_tars_id="AiV222",
                        plasmid_tars_alias=["AiP222"],
                        prep_lot_number="VT222",
                    ),
                    titer=2300000000,
                )
            ],
            coordinate_system_name=coordinate_system.name,
            coordinates=[
                [
                    Translation(translation=[-0.85, -3.8, 0]),
                    Rotation(
                        angles=[0, 10, 0],
                    ),
                    # depth runs down the rotated needle axis, negative because SI points superior
                    Translation(
                        translation=[0, 0, -3.3],
                        reference_coordinate_system=ReferenceCoordinateSystem.LOCAL,
                    ),
                ],
            ],
            dynamics=[
                InjectionDynamics(
                    volume=200,
                    volume_unit=VolumeUnit.NL,
                    profile=InjectionProfile.BOLUS,
                )
            ],
            targeted_structure=CCFv3.VISP,
        ),
    ],
)

p = Procedures(
    subject_id="625100",
    global_coordinate_system=BREGMA_ARI,
    subject_procedures=[
        surgery1,
        Surgery(
            start_date=t2.date(),
            experimenters=["Scientist Smith"],
            ethics_review_id="2109",
            protocol_id="doi",
            global_coordinate_system=BREGMA_ARI,
            procedures=[
                Perfusion(
                    protocol_id="doi_of_protocol",
                    output_specimen_ids=["2", "1"],
                )
            ],
        ),
    ],
)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default=None, help="Output directory for generated JSON file")
    args = parser.parse_args()

    serialized = p.model_dump_json()
    deserialized = Procedures.model_validate_json(serialized)
    deserialized.write_standard_file(output_directory=args.output_dir)
