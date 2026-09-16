"""Validator utility functions"""

import logging
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Any, List, Optional, Union

from pydantic_extra_types.timezone_name import TimeZoneName

from biodata_schema.components.wrappers import AssetPath

logger = logging.getLogger(__name__)

# Fields that should have the same length as the coordinate system axes
AXIS_TYPES = ["Translation", "Rotation", "Scale"]


class TimeValidation(Enum):
    """Enum for time validation types."""

    BETWEEN = "between"
    """Time should be between start and end."""
    AFTER = "after"
    """Time should be after the start time."""
    BEFORE = "before"
    """Time should be before the end time."""


def subject_specimen_id_compatibility(subject_id: str, specimen_id: str) -> bool:
    """Check whether a subject_id and specimen_id are compatible"""
    return subject_id in specimen_id


def recursive_time_validation_check(data, acquisition_start_time=None, acquisition_end_time=None):
    """Recursively check fields for TimeValidation annotations and validate against acquisition times.

    Parameters
    ----------
    data : Any
        The data structure to check recursively
    acquisition_start_time : Optional[datetime]
        The acquisition start time to validate against
    acquisition_end_time : Optional[datetime]
        The acquisition end time to validate against
    """
    if not data:
        return

    # Check if this object has fields with TimeValidation annotations
    if hasattr(data, "__annotations__") and hasattr(data, "__dict__"):
        for field_name, field_value in data.__dict__.items():
            if field_name in getattr(data, "__annotations__", {}):
                # Check if the field has TimeValidation annotation
                annotation = data.__annotations__[field_name]
                if hasattr(annotation, "__metadata__"):
                    for metadata in annotation.__metadata__:
                        if isinstance(metadata, TimeValidation):
                            # Validate the field value against the time constraint
                            if field_value and acquisition_start_time and acquisition_end_time:
                                _validate_time_constraint(
                                    field_value, metadata, acquisition_start_time, acquisition_end_time, field_name
                                )

    # Recursively check nested structures
    _time_validation_recurse_helper(data, acquisition_start_time, acquisition_end_time)


def _convert_to_comparable(value, reference_datetime):
    """Convert date to datetime using the timezone from reference, or return as-is if already datetime"""
    if isinstance(value, date) and not isinstance(value, datetime):
        # Convert date to datetime at midnight with same timezone as reference
        return datetime.combine(value, datetime.min.time()).replace(tzinfo=reference_datetime.tzinfo)
    return value


def _validate_time_constraint(field_value, time_validation, start_time, end_time, field_name):
    """Validate a single time field against the specified constraint."""

    # Convert field_value to be comparable with start_time and end_time
    comparable_field_value = _convert_to_comparable(field_value, start_time)

    if time_validation == TimeValidation.BETWEEN:
        if not (start_time <= comparable_field_value <= end_time):
            raise ValueError(
                f"Field '{field_name}' with value {field_value} must be between {start_time} and {end_time}"
            )
    elif time_validation == TimeValidation.AFTER:
        if comparable_field_value <= start_time:
            raise ValueError(f"Field '{field_name}' with value {field_value} must be after {start_time}")
    elif time_validation == TimeValidation.BEFORE:
        if comparable_field_value >= end_time:
            raise ValueError(f"Field '{field_name}' with value {field_value} must be before {end_time}")


def _time_validation_recurse_helper(data, acquisition_start_time, acquisition_end_time):
    """Helper function for recursive_time_validation_check: recurse calls for lists and objects only"""
    if isinstance(data, list):
        for item in data:
            recursive_time_validation_check(item, acquisition_start_time, acquisition_end_time)
        return
    elif hasattr(data, "__dict__"):
        for attr_name, attr_value in data.__dict__.items():
            if attr_name == "object_type":
                continue  # skip object_type
            if callable(attr_value):
                continue  # skip methods

            recursive_time_validation_check(attr_value, acquisition_start_time, acquisition_end_time)


def _recurse_helper(data, **kwargs):
    """Helper function for recursive coordinate system validation.

    Recursively processes lists and objects, calling recursive_coord_system_check
    on each element or attribute.

    Parameters
    ----------
    data : Any
        The data structure to process recursively
    **kwargs
        Keyword arguments passed to recursive_coord_system_check
    """
    if isinstance(data, (list, tuple, dict)):
        items = data.values() if isinstance(data, dict) else data
        for item in items:
            recursive_coord_system_check(item, **kwargs)
        return
    elif hasattr(data, "__dict__"):
        for attr_name, attr_value in data.__dict__.items():
            if attr_name == "object_type":
                continue  # skip object_type
            if callable(attr_value):
                continue  # skip methods

            if attr_name == "dimensions" and hasattr(data, "dimensions_unit"):
                continue
            field_kwargs = kwargs
            if attr_name == "local_axis_positions" and getattr(data, "local_coordinate_system", None):
                field_kwargs = dict(
                    kwargs,
                    coordinate_system_name=data.local_coordinate_system.name,
                    axis_count=len(data.local_coordinate_system.axes),
                )
            recursive_coord_system_check(attr_value, **field_kwargs)


def _iter_transforms(value):
    """Find transforms in a field, including nested transform lists and mappings."""
    from biodata_schema.components.coordinates import Affine, Rotation, Scale, Translation

    if isinstance(value, (Translation, Rotation, Scale, Affine)):
        yield value
    elif isinstance(value, (list, tuple, dict)):
        for item in value.values() if isinstance(value, dict) else value:
            yield from _iter_transforms(item)


def _check_transform_dimensions(transform, axis_count: int):
    """Check the parameters of a transform against its coordinate frame."""
    from biodata_schema.components.coordinates import Affine, Rotation, Scale

    if isinstance(transform, Affine):
        matrix = transform.affine_transform
        if len(matrix) not in (axis_count, axis_count + 1) or any(len(row) != axis_count + 1 for row in matrix):
            raise ValueError(f"Axis count mismatch for Affine, expected {axis_count} axes")
        return
    if isinstance(transform, Rotation):
        parameters = transform.angles
    elif isinstance(transform, Scale):
        parameters = transform.scale
    else:
        parameters = transform.translation
    if len(parameters) != axis_count:
        raise ValueError(
            f"Axis count mismatch for {transform.object_type}, expected {axis_count} axes, but found {len(parameters)}"
        )


def _system_check_helper(data, coordinate_system_name: Optional[str], axis_count: Optional[int]):
    """Helper function to validate coordinate system requirements for objects with transforms.

    Only validates coordinate system requirements if the object contains transform components
    (Translation, Rotation, or Scale). Objects without transforms don't require coordinate systems.

    Parameters
    ----------
    data : object
        The object to validate
    coordinate_system_name : Optional[str]
        Expected coordinate system name (can be None if no transforms present)
    axis_count : Optional[int]
        Expected number of axes in the coordinate system (can be None if no transforms present)

    Raises
    ------
    ValueError
        If coordinate system is required but missing, system name doesn't match,
        or transform field length doesn't match axis count
    """
    object_type = getattr(data, "object_type", type(data).__name__)
    transform_components = (
        [transform for value in vars(data).values() for transform in _iter_transforms(value)]
        if hasattr(data, "__dict__")
        else []
    )
    if transform_components:
        if not coordinate_system_name or not axis_count:
            raise ValueError(
                f"CoordinateSystem is required when a Transform or Coordinate is present (object_type: {object_type})"
            )

        if data.coordinate_system_name != coordinate_system_name:
            raise ValueError(
                f"System name mismatch for {object_type}, expected {coordinate_system_name}, "
                f"found {data.coordinate_system_name}"
            )

        for transform_component in transform_components:
            _check_transform_dimensions(transform_component, axis_count)


def recursive_coord_system_check(
    data, coordinate_system_name: Optional[str], axis_count: Optional[int], local_coordinate_system=None
):
    """Recursively validate coordinate system requirements for objects with transforms.

    Traverses the data structure and validates that objects with transform components
    (Translation, Rotation, Scale) have the correct coordinate system name and that
    transform field lengths match the expected axis count.

    Parameters
    ----------
    data : Any
        The data structure to validate recursively
    coordinate_system_name : Optional[str]
        Expected coordinate system name (can be None if no transforms present)
    axis_count : Optional[int]
        Expected number of axes in the coordinate system (can be None if no transforms present)

    Raises
    ------
    ValueError
        If coordinate system is required but missing, system name doesn't match,
        or transform field length doesn't match axis count

    Notes
    -----
    Objects without transform components are not required to have coordinate systems.
    Nested global coordinate systems override the inherited global frame. Local frames
    apply to local-reference transforms; atlas coordinates carry their own frame.
    """
    from biodata_schema.components.coordinates import Affine, Rotation, Scale, Translation

    if data is None or isinstance(data, Enum):
        return

    _cs = getattr(data, "global_coordinate_system", None) or getattr(data, "coordinate_system", None)
    if _cs:
        coordinate_system_name = _cs.name
        axis_count = len(_cs.axes)
        local_coordinate_system = None
    local_coordinate_system = getattr(data, "local_coordinate_system", None) or local_coordinate_system
    if axis_count is None and local_coordinate_system is not None:
        coordinate_system_name = local_coordinate_system.name
        axis_count = len(local_coordinate_system.axes)

    if isinstance(data, (Translation, Rotation, Scale, Affine)):
        reference = getattr(data, "reference_coordinate_system", "global")
        transform_axis_count = axis_count
        if reference == "local" and local_coordinate_system is not None:
            transform_axis_count = len(local_coordinate_system.axes)
        if not transform_axis_count:
            raise ValueError(
                f"CoordinateSystem is required when a Transform or Coordinate is present "
                f"(object_type: {data.object_type})"
            )
        _check_transform_dimensions(data, transform_axis_count)
        return

    # Check if the object we are looking at has a coordinate_system_name field
    if hasattr(data, "coordinate_system_name"):
        _system_check_helper(data, coordinate_system_name, axis_count)

    _recurse_helper(
        data=data,
        coordinate_system_name=coordinate_system_name,
        axis_count=axis_count,
        local_coordinate_system=local_coordinate_system,
    )


def recursive_get_named_objects(obj: Any) -> List[tuple]:
    """Recursively extract (name, object) pairs from a DataModel object and its nested fields.

    Unlike :func:`recursive_get_all_names`, this keeps the object each name came from, so
    callers can tell a genuine name collision between two distinct objects apart from the
    same object being referenced in more than one place.
    """
    pairs = []

    if obj is None or isinstance(obj, Enum):  # Skip None and Enums
        return pairs

    elif isinstance(obj, list):  # Handle lists
        for item in obj:
            pairs.extend(recursive_get_named_objects(item))

    elif hasattr(obj, "__dict__"):  # Handle objects (including Pydantic models)
        if not hasattr(obj, "object_type"):
            # All DataModel objects should have an object_type attribute
            return pairs
        if hasattr(obj, "name") and isinstance(obj.name, str):  # Ensure name is a string
            pairs.append((obj.name, obj))

        # Continue recursion into fields
        for field_value in vars(obj).values():
            pairs.extend(recursive_get_named_objects(field_value))

    return pairs


def recursive_get_device_names(obj: Any) -> List[str]:
    """Collect names of addressable devices and assemblies, excluding other named models."""
    from biodata_schema.components.devices import Assembly, Device

    return [name for name, item in recursive_get_named_objects(obj) if isinstance(item, (Device, Assembly))]


def recursive_get_all_names(obj: Any) -> List[str]:
    """Recursively extract all 'name' fields from a DataModel object and its nested fields."""
    names = []

    if obj is None or isinstance(obj, Enum):  # Skip None and Enums
        return names

    elif isinstance(obj, list):  # Handle lists
        for item in obj:
            names.extend(recursive_get_all_names(item))

    elif hasattr(obj, "__dict__"):  # Handle objects (including Pydantic models)
        if not hasattr(obj, "object_type"):
            # All DataModel objects should have an object_type attribute
            return names
        if hasattr(obj, "name") and isinstance(obj.name, str):  # Ensure name is a string
            names.append(obj.name)

        # Continue recursion into fields
        for field_value in vars(obj).values():
            names.extend(recursive_get_all_names(field_value))

    return names


def recursive_check_paths(obj: Any, directory: Optional[Path] = None):
    """Recursively check for AssetPath objects and validate their paths.
    This function raises a ValueError if a path is absolute.
    It also checks if the paths exist and logs a warning if they do not.
    If the object is a list, tuple, set, or dict, it recursively checks each item.

    Parameters
    ----------
    obj : Any
    directory : Optional[Path], optional
        root directory, by default uses the current working directory

    Raises
    ------
    ValueError
        If an AssetPath is absolute rather than relative to the metadata directory.
    """
    if isinstance(obj, Enum):
        return

    if isinstance(obj, AssetPath):
        if obj.is_absolute():
            raise ValueError(f"AssetPath {obj} is absolute, file paths must be relative to the metadata directory")

        if directory is None:
            directory = Path.cwd()
        full_path = directory / obj
        if not full_path.exists():
            logger.warning(
                f"AssetPath {full_path} does not exist, ensure file paths are relative to the metadata directory"
            )
    elif isinstance(obj, (list, tuple, set, dict)):
        items = obj.values() if isinstance(obj, dict) else obj
        for item in items:
            recursive_check_paths(item, directory)
    elif hasattr(obj, "__dict__"):
        for value in vars(obj).values():
            recursive_check_paths(value, directory)


def validate_creation_time_after_midnight(
    creation_time: Optional[Union[datetime, date]], reference_time: Optional[datetime]
) -> None:
    """Validate that creation_time is on or after midnight of the reference_time's day.

    Parameters
    ----------
    creation_time : Optional[datetime]
        The creation time to validate (datetime or date objects are supported)
    reference_time : Optional[datetime]
        The reference time to compare against (typically acquisition_end_time)

    Raises
    ------
    ValueError
        If creation_time is before midnight of the reference_time's day
    """
    if not creation_time or not reference_time:
        return

    # Convert date to datetime if needed
    if isinstance(creation_time, date) and not isinstance(creation_time, datetime):
        creation_time = datetime.combine(creation_time, datetime.min.time())

    # If creation_time is timezone-naive (local time),
    # add the same timezone as reference_time
    if isinstance(creation_time, datetime) and creation_time.tzinfo is None and reference_time.tzinfo is not None:
        creation_time = creation_time.replace(tzinfo=reference_time.tzinfo)

    # Get midnight of the reference time day
    reference_date = reference_time.date()
    midnight_of_reference_day = datetime.combine(reference_date, datetime.min.time()).replace(
        tzinfo=reference_time.tzinfo
    )

    # Validate that creation_time is on or after midnight of the reference day
    if isinstance(creation_time, datetime) and creation_time < midnight_of_reference_day:
        raise ValueError(
            f"Creation time ({creation_time}) "
            f"must be on or after midnight of the reference day ({midnight_of_reference_day})"
        )


def extract_timezone_from_datetime(dt: datetime) -> Union[int, TimeZoneName]:
    """Extract timezone information from a datetime object.

    Parameters
    ----------
    dt : datetime
        A timezone-aware datetime object

    Returns
    -------
    Union[int, TimeZoneName]
        A TimeZoneName (IANA name string) if the tzinfo is a ZoneInfo-backed timezone,
        or an integer representing the UTC offset in hours for fixed-offset timezones
        such as datetime.timezone.utc or datetime.timezone(timedelta(...)).

    Raises
    ------
    ValueError
        If the datetime is not timezone-aware

    Notes
    -----
    Prefer using ZoneInfo (from the zoneinfo standard library) when constructing
    timezone-aware datetimes so that the IANA timezone name is preserved.
    Fixed-offset timezones (e.g. timezone.utc, timezone(timedelta(hours=-7))) will
    be stored as integer UTC offsets in hours and lose their named identity.
    """
    if not hasattr(dt, "tzinfo") or dt.tzinfo is None:
        raise ValueError("datetime must be timezone-aware")

    key = getattr(dt.tzinfo, "key", None)
    if key is not None:
        return TimeZoneName(key)

    offset = dt.utcoffset()
    return int(offset.total_seconds() // 3600)
