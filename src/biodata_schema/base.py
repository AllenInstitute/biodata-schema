"""generic base class with supporting validators and fields for basic AIND schema"""

import json
import logging
import re
import warnings
from pathlib import Path
from typing import Annotated, Any, ClassVar, List, Literal, Optional, Sequence, TypeVar, get_args

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    NaiveDatetime,
    PrivateAttr,
    SerializeAsAny,
    ValidationError,
    ValidatorFunctionWrapHandler,
    create_model,
    field_validator,
    model_validator,
)
from pydantic.functional_validators import WrapValidator

from biodata_schema.utils.validators import recursive_check_paths, recursive_coord_system_check

logger = logging.getLogger(__name__)

MAX_FILE_SIZE = 500 * 1024  # 500KB


class DraftRequirement:
    """Marker for fields required by the draft metadata schema."""


def _coerce_naive_datetime(v: Any, handler: ValidatorFunctionWrapHandler) -> AwareDatetime:
    """Validator to wrap around AwareDatetime to set a default timezone as user's locale"""
    try:
        return handler(v)
    except ValidationError:
        # Try to parse the input as a naive datetime object and attach timezone info
        return create_model("TempNaiveDatetimeModel", dt=(NaiveDatetime, ...)).model_validate({"dt": v}).dt.astimezone()


AwareDatetimeWithDefault = Annotated[AwareDatetime, WrapValidator(_coerce_naive_datetime)]


def is_dict_corrupt(input_dict: dict) -> bool:
    """
    Checks that dictionary keys, included nested keys, do not contain
    forbidden characters ("$" and ".").

    Parameters
    ----------
    input_dict : dict

    Returns
    -------
    bool
        True if input_dict is not a dict, or if any keys contain
        forbidden characters. False otherwise.

    """

    def has_corrupt_keys(input) -> bool:
        """Recursively checks nested dictionaries and lists"""
        if isinstance(input, dict):
            for key, value in input.items():
                if "$" in key or "." in key:
                    return True
                elif has_corrupt_keys(value):
                    return True
        elif isinstance(input, list):
            for item in input:
                if has_corrupt_keys(item):
                    return True
        return False

    # Top-level input must be a dictionary
    if not isinstance(input_dict, dict):
        return True
    return has_corrupt_keys(input_dict)


class _GenericModel(BaseModel, extra="allow"):
    """Base class for generic types that can be used in AIND schema"""

    @model_validator(mode="after")
    def validate_fieldnames(self):
        """Warn users when field names contain forbidden characters
        These characters will cause issues with MongoDB queries
        """
        model_dict = json.loads(self.model_dump_json(by_alias=True))
        if is_dict_corrupt(model_dict):
            warnings.warn("MongoDB queries may not work as expected for fields that contain '.' or '$'")
        return self


GenericModel = SerializeAsAny[_GenericModel]

T = TypeVar("T")
CoreModelT = TypeVar("CoreModelT", bound="DataCoreModel")
Discriminated = Annotated[T, Field(discriminator="object_type")]
DiscriminatedList = List[Discriminated[T]]


class DataModel(BaseModel):
    """BaseModel that disallows extra fields

    Also performs validation checks / coercion / upgrades where necessary
    """

    model_config = ConfigDict(extra="forbid", use_enum_values=True)
    object_type: ClassVar[str]  # This prevents Pydantic from treating it as a normal field

    def __init_subclass__(cls, **kwargs):
        """Automatically set the correct `object_type` as a Literal[...]"""
        super().__init_subclass__(**kwargs)
        object_type_value = cls._object_type_from_name()
        cls.__annotations__["object_type"] = Literal[object_type_value]  # Set literal type annotation
        cls.object_type = object_type_value  # Set the value on the class itself

    @model_validator(mode="before")
    def coerce_object_type(cls, values):
        """Ensure that object_type is set to the correct value

        This ensures that subclasses/parent classes can be deserialized correctly
        """
        cls_object_type = cls._object_type_from_name()
        if isinstance(values, dict) and "object_type" in values and values["object_type"] != cls_object_type:
            values["object_type"] = cls_object_type
        return values

    @classmethod
    def _object_type_from_name(cls) -> str:
        """Convert a class name to a object_type

        Adds a space anytime a lowercase letter is followed by a capital letter
        or when multiple capitals are followed by a lowercase

        Then makes everything after the first space lowercase
        """
        # add spaces when a lowercase letter is followed by a capital letter
        name_with_prespaces = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", cls.__name__)
        # add spaces before the last capital letter in a series of capitals is followed by a lowercase letter
        name_with_spaces = re.sub(r"(?<=\w)(?=[A-Z][a-z])", " ", name_with_prespaces)
        name_split = name_with_spaces.split(" ", 1)
        first_part = name_split[0]
        if len(name_split) > 1:
            second_part = " " + name_split[1].lower()
        else:
            second_part = ""
        return first_part + second_part

    @model_validator(mode="after")
    def unit_validator(self):
        """Ensure that all fields matching the pattern variable_unit are set if
        they have a matching variable that is set (!= None)

        This also checks the multi-variable condition, i.e. variable_unit is set
        if any of variable_* are set
        """
        # Accumulate a dictionary mapping variable : unit/unit_value
        values = self.__dict__.items()
        for unit_name, unit_value in values:
            if "_unit" in unit_name and not unit_value:
                var_name = unit_name.rsplit("_unit", 1)[0]

                # Go through all the values again, if any value matches the variable name
                # and is set, then the unit needs to be set as well
                for variable_name, variable_value in values:
                    if variable_name == var_name and variable_value is not None:
                        raise ValueError(f"Unit {unit_name} is required when {variable_name} is set.")

                # One more time, now looking for the multi-variable condition
                for variable_name, variable_value in values:
                    # skip the unit itself
                    if variable_name != unit_name:
                        if var_name in variable_name and variable_value is not None:
                            raise ValueError(f"Unit {unit_name} is required when {variable_name} is set.")
        return self


class DataCoreModel(DataModel):
    """Generic base class to hold common fields/validators/etc for all basic AIND schema"""

    _IS_COLLECTION: ClassVar[bool] = False
    _FILE_EXTENSION = PrivateAttr(default=".json")
    _DESCRIBED_BY_BASE_URL = PrivateAttr(
        default="https://raw.githubusercontent.com/AllenNeuralDynamics/biodata-schema/main/src/"
    )

    describedBy: str = Field(...)
    schema_version: str = Field(
        ..., pattern=r"^\d+.\d+.\d+$", description="schema version", title="Version", frozen=True
    )

    @field_validator("schema_version", mode="before")
    @classmethod
    def coerce_version(cls, v: str) -> str:
        """Update the schema version to the latest version"""
        return get_args(cls.model_fields["schema_version"].annotation)[0]

    @classmethod
    def default_filename(cls):
        """
        Returns standard filename in snakecase
        """
        parent_classes = [
            base_class
            for base_class in cls.__bases__
            if base_class.__name__ != DataCoreModel.__name__ and issubclass(base_class, DataModel)
        ]

        name = cls.__name__

        if len(parent_classes):
            name = parent_classes[0].__name__

        return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower() + cls._FILE_EXTENSION.default

    @classmethod
    def write_standard_file(
        cls: type[CoreModelT],
        records: CoreModelT | List[CoreModelT],
        output_directory: Path | str | None = None,
        prefix: Optional[str] = None,
        filename_suffix: Optional[str] = None,
        suffix: Optional[str] = None,
    ) -> None:
        """
        Writes schema to standard json file.
        Subjects and procedures accept one record or a list and are always written as arrays.
        Other core models accept a single record and are written as objects.
        Parameters
        ----------
        records: DataCoreModel or List[DataCoreModel]
            Validated record(s) of the model class being written.

        output_directory: Path or str, optional
            optional Path object for output directory.
            Default: None

        prefix: Optional[str]
            optional str for intended filepath with extra naming convention
            Default: None

        filename_suffix: Optional[str]
            optional str for intended filename suffix
            Default: None

        suffix: Optional[str]
            optional str for replacing the file extension
            Default: None
        """
        if isinstance(records, list) and not cls._IS_COLLECTION:
            raise ValueError(f"{cls.__name__} does not use a collection file.")
        items = records if isinstance(records, list) else [records]
        if any(not isinstance(record, cls) for record in items):
            raise TypeError(f"{cls.__name__}.write_standard_file requires {cls.__name__} records.")
        value: DataCoreModel | Sequence[DataCoreModel] = items if cls._IS_COLLECTION else items[0]

        directory = Path.cwd() if output_directory is None else Path(output_directory)
        recursive_check_paths(value, directory)

        filename = cls.default_filename()
        extension = cls._FILE_EXTENSION.default
        if prefix:
            filename = str(prefix) + "_" + filename
        if filename_suffix:
            filename_without_ext = filename.rsplit(extension, 1)[0]
            filename = filename_without_ext + "_" + filename_suffix + extension
        if suffix:
            filename = filename.replace(extension, suffix)
        filename = directory / filename

        serialized = (
            value.model_dump_json(indent=3)
            if isinstance(value, DataCoreModel)
            else json.dumps([record.model_dump(mode="json") for record in value], indent=3)
        )
        with filename.open("w") as f:
            f.write(serialized)

        if len(serialized) > MAX_FILE_SIZE:
            logger.warning(f"File size exceeds {MAX_FILE_SIZE / 1024} KB: {filename}")

    @model_validator(mode="after")
    def coordinate_system_validator(self):
        """Validate that all coordinates match the defined coordinate system"""

        recursive_coord_system_check(self, None, None)

        return self
