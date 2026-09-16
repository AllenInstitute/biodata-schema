"""example data description"""

import argparse
from datetime import datetime, timezone

from biodata_models.data_name_patterns import DataLevel
from biodata_models.modalities import Modality
from biodata_models.organizations import Organization

from biodata_schema.components.identifiers import Person
from biodata_schema.core.data_description import DataDescription, Funding

d = DataDescription(
    modalities=[Modality.ECEPHYS, Modality.BEHAVIOR_VIDEOS],
    subject_id="123456",
    creation_time=datetime(2022, 2, 21, 16, 30, 1, tzinfo=timezone.utc),
    institution=Organization.AIND,
    investigators=[Person(name="Daniel Birman", registry_identifier="0000-0003-3748-6289")],
    funding_source=[Funding(funder=Organization.AI)],
    project_name="Example project",
    data_level=DataLevel.RAW,
    tags=["Pilot data"],
)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default=None, help="Output directory for generated JSON file")
    args = parser.parse_args()

    serialized = d.model_dump_json()
    deserialized = DataDescription.model_validate_json(serialized)
    deserialized.write_standard_file(output_directory=args.output_dir)
