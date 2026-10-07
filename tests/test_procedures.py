"""test Procedures"""

from datetime import date
from unittest.mock import call, patch

import pytest
from biodata_models.anatomy import (
    AnatomyModel,
    MouseAnatomyLookup,
    MouseBloodVessels,
    MouseGroundWireLocations,
    MouseInjectionTargets,
)
from biodata_models.brain_atlas import CCFv3
from biodata_models.coordinates import AnatomicalRelative
from biodata_models.organizations import Organization
from biodata_models.registries import Registry
from biodata_models.specimen_procedure_types import SpecimenProcedureType
from biodata_models.units import ConcentrationUnit, CurrentUnit, SizeUnit, TimeUnit, VolumeUnit
from pydantic import ValidationError

from biodata_schema.components.configs import CatheterConfig
from biodata_schema.components.coordinates import Origin, ReferenceCoordinateSystem, Translation
from biodata_schema.components.devices import Catheter, Device
from biodata_schema.components.injection_procedures import (
    InjectionDynamics,
    InjectionProfile,
    NonViralMaterial,
    TarsVirusIdentifiers,
    ViralMaterial,
)
from biodata_schema.components.specimen_procedures import (
    HCRSeries,
    PlanarSection,
    PlanarSectioning,
    Section,
    Sectioning,
    SectionOrientation,
    SpecimenProcedure,
)
from biodata_schema.components.subject_procedures import BrainInjection, Injection, Surgery
from biodata_schema.components.surgery_procedures import CatheterImplant, Craniotomy, CraniotomyType, GroundWireImplant
from biodata_schema.core.procedures import Procedures
from biodata_schema.utils.exceptions import OneOfError
from tests.coordinate_systems import BREGMA_ARI, BREGMA_RAS


def mouse_anatomy(name: str) -> AnatomyModel:
    """Construct an offline anatomy model fixture."""
    return AnatomyModel(name=name, registry=Registry.EMAPA, registry_identifier="EMAPA:TEST")


class TestProcedures:
    """test Procedures"""

    def setup_method(self):
        """Set up test data"""
        self.start_date = date.fromisoformat("2020-10-10")

    def test_required_field_validation_check(self):
        """Tests that validation error is thrown if subject_name is not set."""
        with pytest.raises(ValidationError):
            Procedures()

        p = Procedures(subject_name="12345")
        assert "12345" == p.subject_name

    def test_unwrapped_injection_rejected(self):
        """Unwrapped Injection in subject_procedures should raise"""
        with pytest.raises(ValidationError):
            Procedures(
                subject_name="12345",
                subject_procedures=[
                    Injection(
                        injection_materials=[NonViralMaterial(name="saline", source=Organization.OTHER)],
                        dynamics=[
                            InjectionDynamics(
                                volume=1,
                                volume_unit=VolumeUnit.UL,
                                duration=1,
                                duration_unit=TimeUnit.S,
                                profile=InjectionProfile.BOLUS,
                            )
                        ],
                    )
                ],
            )

    @patch("biodata_models.anatomy.MouseAnatomyLookup.get_by_name")
    def test_injection_material_check(self, mock_get_by_name):
        """Check for validation error when injection_materials is empty"""
        mock_get_by_name.return_value = mouse_anatomy(MouseInjectionTargets.RETRO_ORBITAL.value)

        with pytest.raises(ValidationError) as e:
            Procedures(
                subject_name="12345",
                subject_procedures=[
                    Surgery(
                        start_date=self.start_date,
                        experimenters=["Mam Moth"],
                        procedures=[
                            Injection(
                                protocol_id="134",
                                injection_materials=[],  # An empty list is invalid
                                dynamics=[
                                    InjectionDynamics(
                                        volume=1,
                                        volume_unit=VolumeUnit.UL,
                                        duration=1,
                                        duration_unit=TimeUnit.S,
                                        profile=InjectionProfile.BOLUS,
                                    )
                                ],
                                targeted_structure=MouseAnatomyLookup.get_by_name(MouseInjectionTargets.RETRO_ORBITAL),
                                relative_position=[AnatomicalRelative.LEFT],
                            ),
                        ],
                    )
                ],
            )

        assert "injection_materials" in repr(e.value)
        mock_get_by_name.assert_called_once_with(MouseInjectionTargets.RETRO_ORBITAL)

    @patch("biodata_models.anatomy.MouseAnatomyLookup.get_by_name")
    def test_injection_material_none(self, mock_get_by_name):
        """Check for validation error when injection_materials is None"""
        mock_get_by_name.return_value = mouse_anatomy(MouseInjectionTargets.RETRO_ORBITAL.value)
        with pytest.raises(ValidationError) as e:
            Procedures(
                subject_name="12345",
                subject_procedures=[
                    Surgery(
                        start_date=self.start_date,
                        experimenters=["Mam Moth"],
                        procedures=[
                            Injection(
                                protocol_id="134",
                                injection_materials=None,
                                dynamics=[
                                    InjectionDynamics(
                                        volume=1,
                                        volume_unit=VolumeUnit.UL,
                                        duration=1,
                                        duration_unit=TimeUnit.S,
                                        profile=InjectionProfile.BOLUS,
                                    )
                                ],
                                targeted_structure=MouseAnatomyLookup.get_by_name(MouseInjectionTargets.RETRO_ORBITAL),
                                relative_position=[AnatomicalRelative.LEFT],
                            ),
                        ],
                    )
                ],
            )

        assert "injection_materials" in repr(e.value)
        mock_get_by_name.assert_called_once_with(MouseInjectionTargets.RETRO_ORBITAL)

    @patch("biodata_models.anatomy.MouseAnatomyLookup.get_by_name")
    def test_injection_materials_list(self, mock_get_by_name):
        """Valid injection_materials list"""
        mock_get_by_name.side_effect = lambda target_name: AnatomyModel(
            name=target_name.value,
            registry=Registry.EMAPA,
            registry_identifier="EMAPA:TEST",
        )

        p = Procedures(
            subject_name="12345",
            global_coordinate_system=BREGMA_ARI,
            subject_procedures=[
                Surgery(
                    start_date=self.start_date,
                    experimenters=["Mam Moth"],
                    ethics_review_id="234",
                    protocol_id="123",
                    global_coordinate_system=BREGMA_ARI,
                    measured_coordinates={
                        Origin.BREGMA: Translation(
                            translation=[0, 0, 0],
                        ),
                        Origin.LAMBDA: Translation(
                            translation=[-4.1, 0, 0],
                        ),
                    },
                    procedures=[
                        Injection(
                            protocol_id="134",
                            injection_materials=[
                                ViralMaterial(
                                    name="AAV2-Flex-ChrimsonR",
                                    tars_identifiers=TarsVirusIdentifiers(
                                        virus_tars_id="AiV222",
                                        plasmid_tars_alias=["AiP222"],
                                        prep_lot_number="VT222",
                                    ),
                                    titer=2300000000,
                                )
                            ],
                            targeted_structure=MouseAnatomyLookup.get_by_name(MouseInjectionTargets.RETRO_ORBITAL),
                            relative_position=[AnatomicalRelative.LEFT],
                            dynamics=[
                                InjectionDynamics(
                                    volume=1,
                                    volume_unit=VolumeUnit.UL,
                                    duration=1,
                                    duration_unit=TimeUnit.S,
                                    profile=InjectionProfile.BOLUS,
                                )
                            ],
                        ),
                        Injection(
                            protocol_id="234",
                            injection_materials=[
                                NonViralMaterial(
                                    name="drug_xyz",
                                    source=Organization.AI,
                                    lot_number="12345",
                                    concentration=1,
                                    concentration_unit=ConcentrationUnit.UM,
                                )
                            ],
                            targeted_structure=MouseAnatomyLookup.get_by_name(MouseInjectionTargets.INTRAPERITONEAL),
                            dynamics=[
                                InjectionDynamics(
                                    volume=1,
                                    volume_unit=VolumeUnit.UL,
                                    profile=InjectionProfile.BOLUS,
                                )
                            ],
                        ),
                        BrainInjection(
                            protocol_id="bca",
                            coordinate_system_name="BREGMA_ARI",
                            injection_materials=[
                                ViralMaterial(
                                    name="AAV2-Flex-ChrimsonR",
                                    tars_identifiers=TarsVirusIdentifiers(
                                        virus_tars_id="AiV222",
                                        plasmid_tars_alias=["AiP222"],
                                        prep_lot_number="VT222",
                                    ),
                                    titer=2300000000,
                                )
                            ],
                            dynamics=[
                                InjectionDynamics(
                                    volume=1,
                                    volume_unit=VolumeUnit.UL,
                                    duration=1,
                                    duration_unit=TimeUnit.S,
                                    profile=InjectionProfile.BOLUS,
                                )
                            ],
                            coordinates=[
                                [
                                    Translation(
                                        translation=[0.5, 1, 0],
                                    ),
                                    Translation(
                                        translation=[0, 0, 1],
                                        reference_coordinate_system=ReferenceCoordinateSystem.LOCAL,
                                    ),
                                ],
                            ],
                            targeted_structure=CCFv3.VISP6A,
                        ),
                    ],
                )
            ],
        )

        mock_get_by_name.assert_has_calls(
            [call(MouseInjectionTargets.RETRO_ORBITAL), call(MouseInjectionTargets.INTRAPERITONEAL)]
        )
        assert mock_get_by_name.call_count == 2

        assert 1 == len(p.subject_procedures)
        assert p == Procedures.model_validate_json(p.model_dump_json())

    def test_validate_procedure_type(self):
        """Test that the procedure type validation error works"""

        with pytest.raises(ValidationError) as e:
            SpecimenProcedure(
                specimen_name="1000",
                procedure_type="Other",
                start_date=self.start_date,
                end_date=date.fromisoformat("2020-10-11"),
                experimenters=["Mam Moth"],
                protocol_id=["10"],
                notes=None,
            )
        assert "notes cannot be empty if procedure_type is Other" in repr(e.value)

        with pytest.raises(ValidationError) as e:
            SpecimenProcedure(
                specimen_name="1000",
                procedure_type="Immunolabeling",
                start_date=self.start_date,
                end_date=date.fromisoformat("2020-10-11"),
                experimenters=["Mam Moth"],
                protocol_id=["10"],
                notes=None,
            )
        assert "FluorescentStain or ProbeReagent required if procedure_type is Immunolabeling" in repr(e.value)

        with pytest.raises(ValidationError) as e:
            SpecimenProcedure(
                specimen_name="1000",
                procedure_type="Hybridization Chain Reaction",
                start_date=date.fromisoformat("2020-10-10"),
                end_date=date.fromisoformat("2020-10-11"),
                experimenters=["Mam Moth"],
                protocol_id=["10"],
                notes=None,
            )
        assert "HCRSeries required if procedure_type is HCR" in repr(e.value)

        with pytest.raises(ValidationError) as e:
            SpecimenProcedure(
                specimen_name="1000",
                procedure_type="Sectioning",
                start_date=date.fromisoformat("2020-10-10"),
                end_date=date.fromisoformat("2020-10-11"),
                experimenters=["Mam Moth"],
                protocol_id=["10"],
                notes=None,
            )
        assert "Sectioning required if procedure_type is Sectioning" in repr(e.value)

        with pytest.raises(ValidationError) as e:
            SpecimenProcedure(
                specimen_name="1000",
                procedure_type=SpecimenProcedureType.BARSEQ,
                start_date=date.fromisoformat("2020-10-10"),
                end_date=date.fromisoformat("2020-10-11"),
                experimenters=["Mam Moth"],
                protocol_id=["10"],
                notes=None,
            )
        assert "GeneProbeSet required if procedure_type is BarSEQ" in repr(e.value)

        assert (
            SpecimenProcedure(
                specimen_name="1000",
                procedure_type="Other",
                start_date=date.fromisoformat("2020-10-10"),
                end_date=date.fromisoformat("2020-10-11"),
                experimenters=["Mam Moth"],
                protocol_id=["10"],
                notes="some extra information",
            )
        ) is not None

        assert (
            SpecimenProcedure(
                specimen_name="1000",
                procedure_type="Sectioning",
                start_date=date.fromisoformat("2020-10-10"),
                end_date=date.fromisoformat("2020-10-11"),
                experimenters=["Mam Moth"],
                protocol_id=["10"],
                notes=None,
                procedure_details=[Sectioning(sections=[Section(output_specimen_name="1000_spinal")])],
            )
        ) is not None

    def test_validate_procedure_type_multiple(self):
        """Test that error thrown when multiple types are passed to procedure_details"""

        with pytest.raises(ValidationError) as e:
            SpecimenProcedure(
                specimen_name="1000",
                procedure_type="Other",
                start_date=date.fromisoformat("2020-10-10"),
                end_date=date.fromisoformat("2020-10-11"),
                experimenters=["Mam Moth"],
                protocol_id=["10"],
                notes="some extra information",
                procedure_details=[
                    HCRSeries.model_construct(),
                    PlanarSectioning.model_construct(),
                ],
            )
        assert "SpecimenProcedure.procedure_details should only contain one type of model" in repr(e.value)

    def test_coordinate_volume_validator(self):
        """Test validator for list lengths on BrainInjection"""

        # Should be okay
        inj1 = BrainInjection(
            protocol_id="abc",
            coordinate_system_name="BREGMA_ARI",
            coordinates=[
                [
                    Translation(
                        translation=[0.5, 1, 0, 0],
                    ),
                ],
                [
                    Translation(
                        translation=[0.5, 1, 0, 1],
                    ),
                ],
            ],
            dynamics=[
                InjectionDynamics(
                    volume=1,
                    volume_unit=VolumeUnit.UL,
                    profile=InjectionProfile.PULSED,
                ),
                InjectionDynamics(
                    volume=2,
                    volume_unit=VolumeUnit.UL,
                    profile=InjectionProfile.PULSED,
                ),
            ],
            injection_materials=[
                ViralMaterial(
                    name="AAV2-Flex-ChrimsonR",
                    tars_identifiers=TarsVirusIdentifiers(
                        virus_tars_id="AiV222",
                        plasmid_tars_alias=["AiP222", "AiP223"],
                        prep_lot_number="VT222",
                    ),
                    titer=2300000000,
                )
            ],
        )
        assert len(inj1.coordinates) == len(inj1.dynamics)

        # Different coordinates and dynamics list lengths should raise an error
        with pytest.raises(ValidationError) as e:
            BrainInjection(
                protocol_id="abc",
                coordinate_system_name="BREGMA_ARI",
                coordinates=[
                    [
                        Translation(
                            translation=[0.5, 1, 0, 0],
                        ),
                    ],
                    [
                        Translation(
                            translation=[0.5, 1, 0, 1],
                        ),
                    ],
                ],
                injection_materials=[
                    ViralMaterial(
                        name="AAV2-Flex-ChrimsonR",
                        tars_identifiers=TarsVirusIdentifiers(
                            virus_tars_id="AiV222",
                            plasmid_tars_alias=["AiP222"],
                            prep_lot_number="VT222",
                        ),
                        titer=2300000000,
                    )
                ],
                dynamics=[
                    InjectionDynamics(
                        volume=1,
                        volume_unit=VolumeUnit.UL,
                        profile=InjectionProfile.PULSED,
                    ),
                ],
            )

        assert "Unmatched list sizes for injection volumes and coordinate depths" in repr(e.value)

    def test_sectioning(self):
        """Test sectioning"""

        # Updated initialization to use the new Section class
        sectioning_procedure = PlanarSectioning(
            global_coordinate_system=BREGMA_ARI,
            sections=[
                PlanarSection(
                    output_specimen_name="123456_001",
                    targeted_structure=CCFv3.MOP,
                    coordinate_system_name="BREGMA_ARI",
                    start_coordinate=Translation(
                        translation=[0.3, 0, 0],
                    ),
                    end_coordinate=Translation(
                        translation=[0.5, 0, 0],
                    ),
                ),
                PlanarSection(
                    output_specimen_name="123456_002",
                    coordinate_system_name="BREGMA_ARI",
                    start_coordinate=Translation(
                        translation=[0.5, 0, 0],
                    ),
                    end_coordinate=Translation(
                        translation=[0.7, 0, 0],
                    ),
                ),
                PlanarSection(
                    output_specimen_name="123456_003",
                    coordinate_system_name="BREGMA_ARI",
                    start_coordinate=Translation(
                        translation=[0.7, 0, 0],
                    ),
                    thickness=0.1,
                    thickness_unit=SizeUnit.MM,
                ),
            ],
            section_orientation=SectionOrientation.CORONAL,
        )
        assert sectioning_procedure is not None

        valid_section = PlanarSection(
            output_specimen_name="123456_001",
            coordinate_system_name="BREGMA_ARI",
            start_coordinate=Translation(
                translation=[0.3, 0, 0, 0],
            ),
            thickness=100.0,
            thickness_unit=SizeUnit.UM,
        )
        assert valid_section is not None

        # Raise error if neither end_coordinate nor thickness is provided
        with pytest.raises(OneOfError):
            PlanarSection(
                output_specimen_name="123456_001",
                coordinate_system_name="BREGMA_ARI",
                start_coordinate=Translation(
                    translation=[0.3, 0, 0],
                ),
            )

    def test_validate_subject_specimen_names(self):
        """Test that the subject_name and specimen_name match"""

        with pytest.raises(ValidationError) as e:
            Procedures(
                subject_name="12345",
                specimen_procedures=[
                    SpecimenProcedure(
                        specimen_name="9999_1000",
                        procedure_type="Other",
                        start_date=date.fromisoformat("2020-10-10"),
                        end_date=date.fromisoformat("2020-10-11"),
                        experimenters=["Mam Moth"],
                        protocol_id=["10"],
                        notes="some notes",
                    )
                ],
            )
        expected_exception = "specimen_name must be an extension of the subject_name."
        assert expected_exception in str(e.value)

    def test_validate_subject_specimen_name_list_valid(self):
        """Test that specimen_name accepts a list of strings when all contain subject_name"""

        valid_procedure = Procedures(
            subject_name="12345",
            specimen_procedures=[
                SpecimenProcedure(
                    specimen_name=["12345_001", "12345_002"],
                    procedure_type="Other",
                    start_date=date.fromisoformat("2020-10-10"),
                    end_date=date.fromisoformat("2020-10-11"),
                    experimenters=["Mam Moth"],
                    protocol_id=["10"],
                    notes="some notes",
                )
            ],
        )
        assert valid_procedure is not None

    def test_craniotomy_position_validation(self):
        """Test validation for craniotomy position"""

        # Should be okay
        craniotomy = Craniotomy(
            protocol_id="123",
            craniotomy_type=CraniotomyType.CIRCLE,
            coordinate_system_name="TestSystem",
            position=Translation(
                translation=[0.5, 1, 0, 0],
            ),
            size=2.0,
            size_unit=SizeUnit.MM,
        )
        assert craniotomy is not None

        # Missing position for required craniotomy types should raise an error
        with pytest.raises(ValueError) as e:
            Craniotomy(
                protocol_id="123",
                craniotomy_type=CraniotomyType.CIRCLE,
                coordinate_system_name="TestSystem",
                size=2.0,
                size_unit=SizeUnit.MM,
            )
        assert "Craniotomy.position must be provided for craniotomy type Circle" in str(e.value)

        with pytest.raises(ValueError) as e:
            Craniotomy(
                protocol_id="123",
                craniotomy_type=CraniotomyType.SQUARE,
                coordinate_system_name="TestSystem",
                size=2.0,
                size_unit=SizeUnit.MM,
            )
        assert "Craniotomy.position must be provided for craniotomy type Square" in str(e.value)

        with pytest.raises(ValueError) as e:
            Craniotomy(
                protocol_id="123",
                craniotomy_type=CraniotomyType.WHC,
                coordinate_system_name="TestSystem",
            )
        assert "Craniotomy.position must be provided for craniotomy type Whole hemisphere craniotomy" in str(e.value)

        # Should be okay for craniotomy types that do not require position
        craniotomy = Craniotomy(
            protocol_id="123",
            craniotomy_type=CraniotomyType.DHC,
        )
        assert craniotomy is not None

    def test_craniotomy_system_name_if_position(self):
        """Test that coordinate_system_name is required if position is provided"""
        # Should be okay
        craniotomy = Craniotomy(
            protocol_id="123",
            craniotomy_type=CraniotomyType.CIRCLE,
            coordinate_system_name="TestSystem",
            position=Translation(
                translation=[0.5, 1, 0, 0],
            ),
            size=2.0,
            size_unit=SizeUnit.MM,
        )
        assert craniotomy is not None

        # Missing coordinate_system_name for required craniotomy types should raise an error
        with pytest.raises(ValueError) as e:
            Craniotomy(
                protocol_id="123",
                craniotomy_type=CraniotomyType.CIRCLE,
                position=Translation(
                    translation=[0.5, 1, 0, 0],
                ),
                size=2.0,
                size_unit=SizeUnit.MM,
            )
        assert "Craniotomy.coordinate_system_name must be provided if Craniotomy.position is provided" in str(e.value)

    def test_craniotomy_size_validation(self):
        """Test validation for craniotomy size"""

        # Should be okay
        craniotomy = Craniotomy(
            protocol_id="123",
            craniotomy_type=CraniotomyType.CIRCLE,
            coordinate_system_name="TestSystem",
            position=Translation(
                translation=[0.5, 1, 0, 0],
            ),
            size=2.0,
            size_unit=SizeUnit.MM,
        )
        assert craniotomy is not None

        # Missing size for required craniotomy types should raise an error
        with pytest.raises(ValueError) as e:
            Craniotomy(
                protocol_id="123",
                craniotomy_type=CraniotomyType.CIRCLE,
                coordinate_system_name="TestSystem",
                position=Translation(
                    translation=[0.5, 1, 0, 0],
                ),
            )
        assert "Craniotomy.size must be provided for craniotomy type Circle" in str(e.value)

        with pytest.raises(ValueError) as e:
            Craniotomy(
                protocol_id="123",
                craniotomy_type=CraniotomyType.SQUARE,
                coordinate_system_name="TestSystem",
                position=Translation(
                    translation=[0.5, 1, 0, 0],
                ),
            )
        assert "Craniotomy.size must be provided for craniotomy type Square" in str(e.value)

        # Should be okay for craniotomy types that do not require size
        craniotomy = Craniotomy(
            protocol_id="123",
            craniotomy_type=CraniotomyType.DHC,
        )
        assert craniotomy is not None

    def test_check_volume_or_current(self):
        """Test validation for InjectionDynamics to ensure either volume or injection_current is provided"""

        # Should be valid with volume provided
        dynamics = InjectionDynamics(
            profile=InjectionProfile.BOLUS,
            volume=1.0,
            volume_unit=VolumeUnit.UL,
        )
        assert dynamics is not None

        # Should be valid with injection_current provided
        dynamics = InjectionDynamics(
            profile=InjectionProfile.BOLUS,
            injection_current=0.5,
            injection_current_unit=CurrentUnit.UA,
        )
        assert dynamics is not None

        # Should raise an error when neither volume nor injection_current is provided
        with pytest.raises(ValueError) as e:
            InjectionDynamics(
                profile=InjectionProfile.BOLUS,
            )
        assert "Either volume or injection_current must be provided." in str(e.value)

    def test_get_device_names(self):
        """Test get_device_names method returns correct device names"""

        # Test with no devices
        procedures = Procedures(subject_name="12345")
        assert procedures.get_device_names() == []

    def test_get_device_names_with_constructed_surgery_procedure(self):
        """Test device-name traversal without requiring external anatomy lookups."""
        device = Device.model_construct(name="Catheter")
        surgery_procedure = CatheterImplant.model_construct(implanted_device=device)
        procedures = Procedures.model_construct(
            subject_name="12345",
            subject_procedures=[Surgery.model_construct(procedures=[surgery_procedure])],
        )

        assert procedures.get_device_names() == ["Catheter"]

    @patch("biodata_models.anatomy.MouseAnatomyLookup.get_by_name")
    def test_get_device_names_with_surgery_procedures(self, mock_get_by_name):
        """Test get_device_names method with nested surgery procedures"""
        mock_get_by_name.return_value = mouse_anatomy(MouseBloodVessels.CAROTID_ARTERY.value)

        device1 = Catheter(
            name="Catheter",
            catheter_port="Single",
            catheter_design="Magnetic",
            catheter_material="Naked",
        )

        config = CatheterConfig(
            device_name="Catheter",
            targeted_structure=MouseAnatomyLookup.get_by_name(MouseBloodVessels.CAROTID_ARTERY),
        )

        # Test with surgery containing procedures with implanted devices
        surgery_procedure = CatheterImplant(
            where_performed=Organization.AIND,
            implanted_device=device1,
            device_config=config,
        )

        procedures = Procedures(
            subject_name="12345",
            subject_procedures=[
                Surgery(
                    start_date=self.start_date,
                    experimenters=["Test Person"],
                    procedures=[surgery_procedure],
                )
            ],
        )
        device_names = procedures.get_device_names()
        assert "Catheter" in device_names
        assert len(device_names) == 1
        mock_get_by_name.assert_called_once_with(MouseBloodVessels.CAROTID_ARTERY)

    @patch("biodata_models.anatomy.MouseAnatomyLookup.get_by_name")
    def test_catheter_blood_vessel_target_lookup(self, mock_get_by_name):
        """Common catheter blood-vessel targets can use the v2 lookup enum."""
        mock_get_by_name.return_value = mouse_anatomy(MouseBloodVessels.CAROTID_ARTERY.value)

        config = CatheterConfig(
            device_name="Catheter",
            targeted_structure=MouseAnatomyLookup.get_by_name(MouseBloodVessels.CAROTID_ARTERY),
        )

        assert config.targeted_structure.name == MouseBloodVessels.CAROTID_ARTERY.value
        mock_get_by_name.assert_called_once_with(MouseBloodVessels.CAROTID_ARTERY)

    @patch("biodata_models.anatomy.MouseAnatomyLookup.get_by_name")
    def test_ground_wire_location_lookup(self, mock_get_by_name):
        """Common ground-wire locations can use the v2 lookup enum."""
        mock_get_by_name.return_value = mouse_anatomy(MouseGroundWireLocations.BRAIN.value)

        implant = GroundWireImplant(
            ground_electrode_location=MouseAnatomyLookup.get_by_name(MouseGroundWireLocations.BRAIN),
        )

        assert implant.ground_electrode_location.name == MouseGroundWireLocations.BRAIN.value
        mock_get_by_name.assert_called_once_with(MouseGroundWireLocations.BRAIN)

    def test_procedures_addition_coordinate_system_validation(self):
        """Test that Procedures addition raises error for different coordinate systems"""

        # Create two procedures with different coordinate systems
        p1 = Procedures(
            subject_name="12345",
            global_coordinate_system=BREGMA_ARI,
        )

        p2 = Procedures(
            subject_name="12345",
            global_coordinate_system=BREGMA_RAS,  # Different coordinate system
        )

        # Test that combining procedures with different coordinate systems raises ValueError
        with pytest.raises(ValueError) as context:
            _ = p1 + p2

        assert "Cannot merge differing coordinate systems" in str(context.value)
        assert "BREGMA_ARI" in str(context.value)
        assert "BREGMA_RAS" in str(context.value)

        # Test that combining procedures with same coordinate systems works
        p3 = Procedures(
            subject_name="12345",
            global_coordinate_system=BREGMA_ARI,  # Same coordinate system as p1
        )

        combined = p1 + p3
        assert combined.global_coordinate_system == BREGMA_ARI
        assert len(combined.subject_procedures) == 0  # Both started with empty procedures
