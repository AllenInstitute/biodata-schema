"""tests for Model"""

import pydantic
import pytest

from biodata_schema.core.model import Model
from examples.model import m


class TestModel:
    """tests for model"""

    def test_constructors(self):
        """try building model"""

        with pytest.raises(pydantic.ValidationError):
            Model()

        Model.model_validate_json(m.model_dump_json())

        assert m is not None
