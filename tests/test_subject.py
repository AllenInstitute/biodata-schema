"""tests for Subject"""

import datetime

import pydantic
import pytest
from biodata_models.organizations import Organization
from biodata_models.pid_names import PIDName
from biodata_models.registries import Registry
from biodata_models.species import Species, Strain

from biodata_schema.components.subjects import BreedingInfo, CellLine, Housing, LightCycle, MouseSubject
from biodata_schema.core.subject import Subject


class TestSubject:
    """tests for subject"""

    def test_constructors(self):
        """try building Subjects"""

        with pytest.raises(pydantic.ValidationError):
            Subject()

        now = datetime.datetime.now()

        s = Subject(
            subject_id="123456",
            subject_details=MouseSubject(
                species=Species.HOUSE_MOUSE,
                strain=Strain.C57BL_6J,
                sex="Male",
                date_of_birth=now.date(),
                genotype="wt",
                source=Organization.AI,
                housing=Housing(
                    light_cycle=LightCycle(
                        lights_on_time=now.time(),
                        lights_off_time=now.time(),
                    ),
                    cage_id="543",
                ),
                breeding_info=BreedingInfo(
                    maternal_id="546543",
                    maternal_genotype="Emx1-IRES-Cre/wt; Camk2a-tTa/Camk2a-tTA",
                    paternal_id="232323",
                    paternal_genotype="Ai93(TITL-GCaMP6f)/wt",
                ),
                alleles=[PIDName(registry_identifier="12345", name="adsf", registry=Registry.MGI)],
            ),
        )

        Subject.model_validate_json(s.model_dump_json())

        assert s is not None

    def test_cell_line_subject_constructor(self):
        """try building Subjects with cell line details"""

        s = Subject(
            subject_id="cell-line-123",
            subject_details=CellLine(
                cell_line_name="HEK293T",
                cell_line_type=PIDName(
                    registry_identifier="CLO:0000001", name="immortalized cell line", registry="Cell Line Ontology"
                ),
                species=Species.HUMAN,
                protein=PIDName(registry_identifier="P12345", name="GFAP", registry=Registry.UNIPROT),
                gene=PIDName(registry_identifier="672", name="BRCA1", registry=Registry.NCBI),
                cell_structure="nucleus",
                fluorescent_protein=PIDName(registry_identifier="FPbase:123", name="EGFP", registry="FPbase"),
            ),
        )

        restored = Subject.model_validate_json(s.model_dump_json())

        assert isinstance(restored.subject_details, CellLine)
        assert restored.subject_details.cell_line_name == "HEK293T"
        assert restored.subject_details.gene.registry == Registry.NCBI
