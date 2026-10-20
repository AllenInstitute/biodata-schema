"""schema for various Procedures"""

from typing import List, Literal, Optional

from pydantic import Field, SkipValidation

from biodata_schema.base import DataCoreModel, DiscriminatedList
from biodata_schema.components.specimen_procedures import SpecimenProcedure
from biodata_schema.components.subject_procedures import (
    SelfAdministeredTreatment,
    ClinicalVisit,
    FoodRestriction,
    GenericSubjectProcedure,
    NonSurgicalInjection,
    Surgery,
    TrainingProtocol,
    WaterRestriction,
)
from biodata_schema.utils.merge import merge_notes
from biodata_schema.utils.validators import recursive_get_device_names


class Procedures(DataCoreModel):
    """Description of all procedures performed on a subject, including surgeries, injections, and tissue processing"""

    _IS_COLLECTION = True
    _DESCRIBED_BY_URL = DataCoreModel._DESCRIBED_BY_BASE_URL.default + "biodata_schema/core/procedures.py"
    describedBy: str = Field(default=_DESCRIBED_BY_URL, json_schema_extra={"const": _DESCRIBED_BY_URL})

    schema_version: SkipValidation[Literal["3.0.2"]] = Field(default="3.0.2")
    subject_name: str = Field(
        ...,
        description="Unique name for the subject associated with these procedures",
        title="Subject name",
    )
    subject_procedures: DiscriminatedList[
        SelfAdministeredTreatment
        | ClinicalVisit
        | FoodRestriction
        | GenericSubjectProcedure
        | NonSurgicalInjection
        | Surgery
        | TrainingProtocol
        | WaterRestriction
    ] = Field(default=[], title="Subject Procedures", description="Procedures performed on a live subject")
    specimen_procedures: List[SpecimenProcedure] = Field(
        default=[], title="Specimen Procedures", description="Procedures performed on tissue extracted after perfusion"
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

    def __add__(self, other: "Procedures") -> "Procedures":
        """Combine two Procedures objects"""

        if not self.schema_version == other.schema_version:
            raise ValueError("Schema versions must match to combine Procedures")

        if self.subject_name != other.subject_name:
            raise ValueError("Subject names must match to combine Procedures objects.")

        return Procedures(
            subject_name=self.subject_name,
            subject_procedures=self.subject_procedures + other.subject_procedures,
            specimen_procedures=self.specimen_procedures + other.specimen_procedures,
            notes=merge_notes(self.notes, other.notes),
        )
