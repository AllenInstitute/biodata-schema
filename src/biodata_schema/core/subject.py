"""schema for mostly mouse metadata"""

from typing import Annotated, Literal, Optional

from pydantic import Field, SkipValidation

from biodata_schema.base import DataCoreModel, Discriminated, DraftRequirement
from biodata_schema.components.subjects import CalibrationObject, HumanSubject, MouseSubject, NonHumanPrimateSubject


class Subject(DataCoreModel):
    """Description of a subject of data collection"""

    _DESCRIBED_BY_URL = DataCoreModel._DESCRIBED_BY_BASE_URL.default + "biodata_schema/core/subject.py"
    describedBy: str = Field(default=_DESCRIBED_BY_URL, json_schema_extra={"const": _DESCRIBED_BY_URL})
    schema_version: SkipValidation[Literal["3.0.2"]] = Field(default="3.0.2")
    subject_name: Annotated[str, DraftRequirement] = Field(
        ...,
        description="Unique name for the subject of data acquisition",
        title="Subject name",
    )

    subject_details: Discriminated[MouseSubject | HumanSubject | NonHumanPrimateSubject | CalibrationObject] = Field(
        ..., title="Subject Details"
    )

    notes: Optional[str] = Field(default=None, title="Notes")
