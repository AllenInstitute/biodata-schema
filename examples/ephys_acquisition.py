"""Generates an example JSON file for an ephys acquisition"""

import argparse
from datetime import datetime
from zoneinfo import ZoneInfo

from biodata_models.brain_atlas import CCFv3
from biodata_models.coordinates import AxisName, Direction, Origin
from biodata_models.modalities import Modality
from biodata_models.stimulus_modality import StimulusModality
from biodata_models.units import SizeUnit

from biodata_schema.components.configs import (
    EphysAssemblyConfig,
    ManipulatorConfig,
    ProbeConfig,
)
from biodata_schema.components.coordinates import (
    AtlasCoordinate,
    AtlasLibrary,
    Axis,
    CoordinateSystem,
    ReferenceCoordinateSystem,
    Rotation,
    Translation,
)
from biodata_schema.components.identifiers import Code, Software
from biodata_schema.components.stimulus import VisualStimulation
from biodata_schema.core.acquisition import (
    Acquisition,
    AcquisitionSubjectDetails,
    DataStream,
    StimulusEpoch,
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

bonsai_software = Software(name="Bonsai", version="2.7")

ephys_assembly_a_config = EphysAssemblyConfig(
    device_name="Ephys_assemblyA",
    manipulator=ManipulatorConfig(
        device_name="ManipulatorA",
        local_coordinate_system=MPM_MANIP_RFB,
        local_axis_positions=Translation(
            translation=[8422, 4205, 11087.5],
        ),
    ),
    probes=[
        ProbeConfig(
            primary_targeted_structure=CCFv3.LGD,
            device_name="ProbeA",
            atlas_coordinate=AtlasCoordinate(
                coordinate_system=AtlasLibrary.CCFv3_10um,
                translation=[8150, 3250, 7800],
            ),
            local_coordinate_system=MPM_MANIP_RFB,
            transform=[
                Translation(
                    translation=[5000, 5000, 0],
                ),
                Rotation(
                    angles=[8, 5.2, 0],
                ),
                # insertion depth runs along the probe's own Z axis, which points down
                Translation(
                    translation=[0, 0, 1],
                    reference_coordinate_system=ReferenceCoordinateSystem.LOCAL,
                ),
            ],
            notes=(
                "Moved Y to avoid blood vessel, X to avoid edge. Mouse made some noise during the recording"
                " with a sudden shift in signals. Lots of motion. Maybe some implant motion."
            ),
        )
    ],
)

ephys_assembly_b_config = EphysAssemblyConfig(
    device_name="Ephys_assemblyB",
    manipulator=ManipulatorConfig(
        device_name="ManipulatorB",
        local_coordinate_system=MPM_MANIP_RFB,
        local_axis_positions=Translation(
            translation=[8422, 4205, 11087.5],
        ),
    ),
    probes=[
        ProbeConfig(
            device_name="ProbeB",
            primary_targeted_structure=CCFv3.LC,
            atlas_coordinate=AtlasCoordinate(
                coordinate_system=AtlasLibrary.CCFv3_10um,
                translation=[8150, 3250, 7800],
            ),
            local_coordinate_system=MPM_MANIP_RFB,
            transform=[
                Translation(
                    translation=[5000, 5000, 0],
                ),
                # insertion depth runs along the probe's own Z axis, which points down
                Translation(
                    translation=[0, 0, 1],
                    reference_coordinate_system=ReferenceCoordinateSystem.LOCAL,
                ),
            ],
            notes=(
                "Trouble penetrating. Lots of compression, needed to move probe. Small amount of surface"
                " bleeding/bruising. Initial Target: X;10070.3\tY:7476.6"
            ),
        )
    ],
)


acquisition = Acquisition(
    experimenters=["John Smith"],
    subject_id="664484",
    acquisition_start_time=datetime(
        year=2023, month=4, day=25, hour=2, minute=35, second=0, tzinfo=ZoneInfo("America/Los_Angeles")
    ),
    acquisition_end_time=datetime(
        year=2023, month=4, day=25, hour=3, minute=16, second=0, tzinfo=ZoneInfo("America/Los_Angeles")
    ),
    acquisition_type="Receptive field mapping",
    instrument_id="EPHYS1",
    ethics_review_id=["2109"],
    subject_details=AcquisitionSubjectDetails(
        mouse_platform_name="Running Wheel",
    ),
    global_coordinate_system=BREGMA_ARI,
    stimulus_epochs=[
        StimulusEpoch(
            stimulus_name="Visual Stimulation",
            stimulus_modalities=[StimulusModality.VISUAL],
            stimulus_start_time=datetime(
                year=2023, month=4, day=25, hour=2, minute=45, second=0, tzinfo=ZoneInfo("America/Los_Angeles")
            ),
            stimulus_end_time=datetime(
                year=2023, month=4, day=25, hour=3, minute=10, second=0, tzinfo=ZoneInfo("America/Los_Angeles")
            ),
            code=Code(
                url="https://github.com/fakeorg/GratingAndFlashes/gratings_and_flashes.bonsai",
                core_dependency=bonsai_software,
                parameters=VisualStimulation(
                    stimulus_name="Static Gratings",
                    stimulus_parameters={
                        "grating_orientations": [0, 45, 90, 135],
                        "grating_orientation_unit": "degrees",
                        "grating_spatial_frequencies": [0.02, 0.04, 0.08, 0.16, 0.32],
                        "grating_spatial_frequency_unit": "cycles/degree",
                    },
                ),
                version="0.0.1",
            ),
        ),
        StimulusEpoch(
            stimulus_name="Visual Stimulation",
            stimulus_modalities=[StimulusModality.VISUAL],
            stimulus_start_time=datetime(
                year=2023, month=4, day=25, hour=3, minute=10, second=0, tzinfo=ZoneInfo("America/Los_Angeles")
            ),
            stimulus_end_time=datetime(
                year=2023, month=4, day=25, hour=3, minute=16, second=0, tzinfo=ZoneInfo("America/Los_Angeles")
            ),
            active_devices=["Stimulus Screen"],
            code=Code(
                url="https://github.com/fakeorg/GratingAndFlashes/gratings_and_flashes.bonsai",
                core_dependency=bonsai_software,
                parameters=VisualStimulation(
                    stimulus_name="Flashes",
                    stimulus_parameters={
                        "flash_interval": 5.0,
                        "flash_interval_unit": "seconds",
                        "flash_duration": 0.5,
                        "flash_duration_unit": "seconds",
                    },
                ),
                version="0.0.1",
            ),
        ),
    ],
    data_streams=[
        DataStream(
            stream_start_time=datetime(
                year=2023, month=4, day=25, hour=2, minute=45, second=0, tzinfo=ZoneInfo("America/Los_Angeles")
            ),
            stream_end_time=datetime(
                year=2023, month=4, day=25, hour=3, minute=16, second=0, tzinfo=ZoneInfo("America/Los_Angeles")
            ),
            modalities=[Modality.ECEPHYS],
            active_devices=[
                "Basestation Slot 3",
                "Ephys_assemblyA",
                "Ephys_assemblyB",
            ],
            configurations=[
                ephys_assembly_a_config,
                ephys_assembly_b_config,
            ],
        ),
        DataStream(
            stream_start_time=datetime(
                year=2023, month=4, day=25, hour=2, minute=35, second=0, tzinfo=ZoneInfo("America/Los_Angeles")
            ),
            stream_end_time=datetime(
                year=2023, month=4, day=25, hour=2, minute=45, second=0, tzinfo=ZoneInfo("America/Los_Angeles")
            ),
            modalities=[Modality.ECEPHYS],
            notes="664484_2023-04-24_20-06-37; Surface Finding",
            active_devices=[
                "Basestation Slot 3",
                "Ephys_assemblyA",
                "Ephys_assemblyB",
            ],
            configurations=[
                ephys_assembly_a_config,
                ephys_assembly_b_config,
            ],
        ),
    ],
)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default=None, help="Output directory for generated JSON file")
    args = parser.parse_args()

    serialized = acquisition.model_dump_json()
    deserialized = Acquisition.model_validate_json(serialized)
    deserialized.write_standard_file(prefix="ephys", output_directory=args.output_dir)
