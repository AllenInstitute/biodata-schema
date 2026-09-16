"""example MRIAcquisition and MRIScan"""

import argparse
from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from biodata_models.coordinates import AxisName, Direction, Origin
from biodata_models.modalities import Modality
from biodata_models.units import MagneticFieldUnit, SizeUnit, TimeUnit

from biodata_schema.components.configs import MRAcquisitionType, MRIScan, PulseSequenceType, SubjectPosition
from biodata_schema.components.coordinates import Affine, Axis, CoordinateSystem, Scale, Translation
from biodata_schema.components.devices import Scanner
from biodata_schema.core.acquisition import (
    Acquisition,
    AcquisitionSubjectDetails,
    DataStream,
)

MRI_LPS = CoordinateSystem(
    name="MRI_LPS",
    origin=Origin.ORIGIN,
    axis_unit=SizeUnit.MM,
    axes=[
        Axis(name=AxisName.X, direction=Direction.RL),
        Axis(name=AxisName.Y, direction=Direction.AP),
        Axis(name=AxisName.Z, direction=Direction.IS),
    ],
)

mri_scanner = Scanner(
    name="Scanner 72",
    magnetic_strength=7,
    magnetic_strength_unit=MagneticFieldUnit.T,
)

scan1 = MRIScan(
    index=1,
    device_name="Scanner 72",
    setup=True,
    mr_acquisition_type=MRAcquisitionType.SCAN_2D,
    pulse_sequence_type=PulseSequenceType.RARE,
    rare_factor=8,
    echo_time=Decimal("0.00342"),
    echo_time_unit=TimeUnit.S,
    repetition_time=Decimal("100.0"),
    repetition_time_unit=TimeUnit.S,
    subject_position=SubjectPosition.SUPINE,
    resolution=Scale(scale=[0.5, 0.4375, 0.52]),
    resolution_unit=SizeUnit.MM,
    notes="Set up scan for the 3D scan.",
)

scan2 = MRIScan(
    index=2,
    device_name="Scanner 72",
    setup=False,
    mr_acquisition_type=MRAcquisitionType.SCAN_3D,
    pulse_sequence_type=PulseSequenceType.RARE,
    rare_factor=4,
    echo_time=Decimal("0.00533333333333333"),
    echo_time_unit=TimeUnit.S,
    effective_echo_time=Decimal("0.0106666666666666998253276688046753406524658203125"),
    repetition_time=Decimal("0.5"),
    repetition_time_unit=TimeUnit.S,
    affine_transform=[
        Affine(
            affine_transform=[[1.0, 0.0, 0.0, 0.0], [0.0, 0.0, -1.0, 0.0], [0.0, 1.0, 0.0, 0.0]],
        ),
        Translation(
            translation=[-6.1, 7.0, 7.9],
        ),
    ],
    subject_position=SubjectPosition.SUPINE,
    resolution=Scale(scale=[0.5, 0.4375, 0.52]),
    resolution_unit=SizeUnit.MM,
    notes=None,
)

stream = DataStream(
    stream_start_time=datetime(2024, 3, 12, 16, 27, 55, 584892, tzinfo=ZoneInfo("America/Los_Angeles")),
    stream_end_time=datetime(2024, 3, 12, 16, 27, 55, 584892, tzinfo=ZoneInfo("America/Los_Angeles")),
    active_devices=["Scanner 72"],
    configurations=[scan1, scan2],
    modalities=[Modality.MRI],
)

acquisition = Acquisition(
    subject_id="123456",
    acquisition_start_time=datetime(2024, 3, 12, 16, 27, 55, 584892, tzinfo=ZoneInfo("America/Los_Angeles")),
    acquisition_end_time=datetime(2024, 3, 12, 16, 27, 55, 584892, tzinfo=ZoneInfo("America/Los_Angeles")),
    experimenters=["John Smith"],
    protocol_id=["dx.doi.org/10.57824/protocols.io.bh7kl4n6"],
    ethics_review_id=["1234"],
    acquisition_type="3D MRI Volume",
    instrument_id="NA",
    global_coordinate_system=MRI_LPS,
    subject_details=AcquisitionSubjectDetails(
        mouse_platform_name="cradle",
    ),
    data_streams=[stream],
    notes="There was some information about this scan acquisition",
)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default=None, help="Output directory for generated JSON file")
    args = parser.parse_args()

    serialized = acquisition.model_dump_json()
    deserialized = Acquisition.model_validate_json(serialized)
    deserialized.write_standard_file(prefix="mri", output_directory=args.output_dir)
