"""schema for subject metadata"""

from typing import Annotated, Literal, Optional

from pydantic import Field, SkipValidation, StringConstraints

from biodata_schema.base import DataCoreModel, Discriminated, DraftRequirement
from biodata_schema.components.subjects import (
    CalibrationObject,
    CellLine,
    FluorescentCellLine,
    HumanSubject,
    MouseSubject,
    NonHumanPrimateSubject,
)
from biodata_schema.utils.data_name_patterns import DataRegex


class Subject(DataCoreModel):
    """Description of a subject of data collection"""

    _IS_COLLECTION = True
    _MIN_COLLECTION_LENGTH = 1
    _DESCRIBED_BY_URL = DataCoreModel._DESCRIBED_BY_BASE_URL.default + "biodata_schema/core/subject.py"
    describedBy: str = Field(default=_DESCRIBED_BY_URL, json_schema_extra={"const": _DESCRIBED_BY_URL})
    schema_version: SkipValidation[Literal["3.0.2"]] = Field(default="3.0.2")
    subject_name: Annotated[str, DraftRequirement, StringConstraints(pattern=DataRegex.NO_UNDERSCORES.value)] = Field(
        ...,
        description="Unique name for the subject of data acquisition",
        title="Subject name",
    )
    cohort_name: Optional[str] = Field(default=None, title="Cohort")
    subject_details: Discriminated[
        MouseSubject | HumanSubject | NonHumanPrimateSubject | CellLine | FluorescentCellLine | CalibrationObject
    ] = Field(..., title="Subject Details")
    restrictions: Optional[str] = Field(
        default=None,
        description="Any restrictions on use or publishing based on subject source",
        title="Restrictions",
    )
    notes: Optional[str] = Field(default=None, title="Notes")

    @classmethod
    def default_filename(cls):
        """Return the standard subject collection filename."""
        return "subjects.json"
