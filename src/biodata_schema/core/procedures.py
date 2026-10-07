"""schema for various Procedures"""

from typing import List, Literal, Optional

from pydantic import Field, SkipValidation, model_validator

from biodata_schema.base import DataCoreModel, DiscriminatedList
from biodata_schema.components.coordinates import CoordinateSystem
from biodata_schema.components.injection_procedures import Injection
from biodata_schema.components.specimen_procedures import SpecimenProcedure
from biodata_schema.components.subject_procedures import (
    GenericSubjectProcedure,
    NonSurgicalInjection,
    Surgery,
    TrainingProtocol,
    WaterRestriction,
)
from biodata_schema.utils.merge import merge_coordinate_systems, merge_notes
from biodata_schema.utils.validators import recursive_get_device_names, subject_specimen_name_compatibility


class Procedures(DataCoreModel):
    """Description of all procedures performed on a subject, including surgeries, injections, and tissue processing"""

    _DESCRIBED_BY_URL = DataCoreModel._DESCRIBED_BY_BASE_URL.default + "biodata_schema/core/procedures.py"
    describedBy: str = Field(default=_DESCRIBED_BY_URL, json_schema_extra={"const": _DESCRIBED_BY_URL})

    schema_version: SkipValidation[Literal["3.0.2"]] = Field(default="3.0.2")
    subject_name: str = Field(
        ...,
        description="Unique name for the subject associated with these procedures",
        title="Subject name",
    )
    subject_procedures: DiscriminatedList[
        Surgery | Injection | NonSurgicalInjection | TrainingProtocol | WaterRestriction | GenericSubjectProcedure
    ] = Field(default=[], title="Subject Procedures", description="Procedures performed on a live subject")
    specimen_procedures: List[SpecimenProcedure] = Field(
        default=[], title="Specimen Procedures", description="Procedures performed on tissue extracted after perfusion"
    )

    # Coordinate system
    global_coordinate_system: Optional[CoordinateSystem] = Field(
        default=None,
        title="Global Coordinate System",
        description=(
            "Origin and axis definitions for determining the configured position of devices implanted during"
            " procedures. Required when coordinates are provided within the Procedures"
        ),
    )

    notes: Optional[str] = Field(default=None, title="Notes")

    def get_device_names(self) -> List[str]:
        """Get all device names for implanted devices in the procedures"""
        device_names = set()

        for procedure in self.subject_procedures:
            # These commented lines are left in case we added implanted_devices to a subject procedure
            # if hasattr(procedure, "implanted_device") and procedure.implanted_device is not None:
            #     device_names.add(procedure.implanted_device.name)
            if hasattr(procedure, "procedures"):
                for surgery_procedure in procedure.procedures:
                    if (
                        hasattr(surgery_procedure, "implanted_device")
                        and surgery_procedure.implanted_device is not None
                    ):
                        device_names.update(recursive_get_device_names(surgery_procedure.implanted_device))

        # These commented lines are left in case we added implanted_devices to a specimen procedure
        # for spec_proc in self.specimen_procedures:
        #     if hasattr(spec_proc, "implanted_device") and spec_proc.implanted_device is not None:
        #         device_names.add(spec_proc.implanted_device.name)

        return list(device_names)

    @model_validator(mode="after")
    def reject_injections(self):
        """Reject bare injections since they must be wrapped
        in a Surgery or NonSurgicalInjection procedure
        """

        for procedure in self.subject_procedures:
            if isinstance(procedure, Injection):
                raise ValueError("Injection procedures must be wrapped in a Surgery or NonSurgicalInjection procedure.")

        return self

    @model_validator(mode="after")
    def validate_subject_specimen_names(self):
        """Validate that this subject_name and specimen_name match"""

        # Return if no specimen procedures
        if self.specimen_procedures:
            specimen_names = []
            for spec_proc in self.specimen_procedures:
                specimen_name = spec_proc.specimen_name
                if isinstance(specimen_name, list):
                    specimen_names.extend(specimen_name)
                else:
                    specimen_names.append(specimen_name)

            if any(
                not subject_specimen_name_compatibility(self.subject_name, specimen_name)
                for specimen_name in specimen_names
            ):
                raise ValueError("specimen_name must be an extension of the subject_name.")

        return self

    def __add__(self, other: "Procedures") -> "Procedures":
        """Combine two Procedures objects"""

        if not self.schema_version == other.schema_version:
            raise ValueError("Schema versions must match to combine Procedures")

        if self.subject_name != other.subject_name:
            raise ValueError("Subject names must match to combine Procedures objects.")

        coordinate_system = merge_coordinate_systems(self.global_coordinate_system, other.global_coordinate_system)

        return Procedures(
            subject_name=self.subject_name,
            subject_procedures=self.subject_procedures + other.subject_procedures,
            specimen_procedures=self.specimen_procedures + other.specimen_procedures,
            global_coordinate_system=coordinate_system,
            notes=merge_notes(self.notes, other.notes),
        )
