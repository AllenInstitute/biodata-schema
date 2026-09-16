"""Tests for subjects details models"""

from datetime import datetime

import pytest
from biodata_models.organizations import Organization
from biodata_models.pid_names import PIDName
from biodata_models.registries import Registry
from biodata_models.species import Species, Strain

from biodata_schema.components.subjects import (
    BreedingInfo,
    CalibrationObject,
    Housing,
    HumanSubject,
    LightCycle,
    MatingStatus,
    MouseSubject,
    NonHumanPrimateSubject,
    Sex,
)


class TestMouseSubject:
    """Test the mouse subject model"""

    def setup_method(self):
        """Set up the tests"""
        self.now = datetime.now()

    def test_validate_inhouse_breeding_info(self):
        """Test the inhouse breeding info validator"""

        with pytest.raises(ValueError) as context:
            MouseSubject(
                sex=Sex.MALE,
                date_of_birth=self.now.date(),
                strain=Strain.C57BL_6J,
                species=Species.HOUSE_MOUSE,
                genotype="wt",
                source=Organization.AI,
                housing=Housing(
                    light_cycle=LightCycle(
                        lights_on_time=self.now.time(),
                        lights_off_time=self.now.time(),
                    ),
                    cage_id="543",
                ),
                alleles=[PIDName(registry_identifier="12345", name="adsf", registry=Registry.MGI)],
            )
        assert "Breeding info should be provided for subjects bred in house" in str(context.value)

    def test_validate_species_strain(self):
        """Test the species and strain validator"""

        with pytest.raises(ValueError) as context:
            MouseSubject(
                sex=Sex.MALE,
                date_of_birth=self.now.date(),
                strain=Strain.BALB_C,
                species=Species.HUMAN,
                genotype="wt",
                source=Organization.JAX,
                housing=Housing(
                    light_cycle=LightCycle(
                        lights_on_time=self.now.time(),
                        lights_off_time=self.now.time(),
                    ),
                    cage_id="543",
                ),
                alleles=[PIDName(registry_identifier="12345", name="adsf", registry=Registry.MGI)],
            )
        assert "The animal species and it's strain's species do not match" in str(context.value)


class TestHumanSubject:
    """Test the human subject model"""

    def test_validate_species_is_human(self):
        """Test the species validator"""

        with pytest.raises(ValueError) as context:
            HumanSubject(sex=Sex.MALE, species=Species.HOUSE_MOUSE, year_of_birth=1962, source=Organization.UCSD)
        assert "HumanSubject species must be HUMAN" in str(context.value)

    def test_validate_species_is_human_success(self):
        """Test the species validator with valid human species"""

        # This test covers line 173 - the successful return path
        subject = HumanSubject(sex=Sex.FEMALE, species=Species.HUMAN, year_of_birth=1990, source=Organization.AI)

        assert subject.species == Species.HUMAN
        assert subject.sex == Sex.FEMALE
        assert subject.year_of_birth == 1990
        assert subject.source == Organization.AI

    def test_validate_species_is_human_from_dict(self):
        """Test the species validator with a serialized human species"""

        subject = HumanSubject(
            sex=Sex.FEMALE,
            species=Species.HUMAN.model_dump(),
            year_of_birth=1990,
            source=Organization.AI,
        )

        assert subject.species == Species.HUMAN


class TestNonHumanPrimateSubject:
    """Test the non-human primate subject model"""

    def setup_method(self):
        """Set up the tests"""
        self.now = datetime.now()

    def test_non_human_primate_without_date_of_birth(self):
        """Test creating NonHumanPrimateSubject without optional date_of_birth"""

        subject = NonHumanPrimateSubject(
            species=Species.RHESUS_MACAQUE,
            sex=Sex.MALE,
            year_of_birth=2019,
            mating_status=MatingStatus.UNMATED,
            source=Organization.JAX,
        )

        assert subject.species == Species.RHESUS_MACAQUE
        assert subject.sex == Sex.MALE
        assert subject.date_of_birth is None
        assert subject.year_of_birth == 2019
        assert subject.mating_status == MatingStatus.UNMATED
        assert subject.source == Organization.JAX

    def test_non_human_primate_mating_status_unknown(self):
        """Test NonHumanPrimateSubject with unknown mating status"""

        subject = NonHumanPrimateSubject(
            species=Species.RHESUS_MACAQUE,
            sex=Sex.FEMALE,
            year_of_birth=2021,
            mating_status=MatingStatus.UNKNOWN,
            source=Organization.AI,
        )

        assert subject.mating_status == MatingStatus.UNKNOWN

    def test_validate_date_year_consistency_valid(self):
        """Test that date_of_birth year matching year_of_birth is valid"""
        from datetime import date

        birth_date = date(2020, 5, 15)
        subject = NonHumanPrimateSubject(
            species=Species.RHESUS_MACAQUE,
            sex=Sex.FEMALE,
            date_of_birth=birth_date,
            year_of_birth=2020,  # Matching year
            mating_status=MatingStatus.MATED,
            source=Organization.COLUMBIA,
        )

        assert subject.date_of_birth == birth_date
        assert subject.year_of_birth == 2020

    def test_validate_date_year_consistency_invalid(self):
        """Test that mismatched date_of_birth year and year_of_birth raises ValueError"""
        from datetime import date

        with pytest.raises(ValueError) as context:
            NonHumanPrimateSubject(
                species=Species.RHESUS_MACAQUE,
                sex=Sex.MALE,
                date_of_birth=date(2019, 8, 10),  # Year 2019
                year_of_birth=2020,  # Different year
                mating_status=MatingStatus.UNMATED,
                source=Organization.COLUMBIA,
            )

        assert "Date of birth (2019) does not match year of birth (2020)" in str(context.value)

    def test_validate_date_year_consistency_no_date(self):
        """Test that validation passes when date_of_birth is None"""

        subject = NonHumanPrimateSubject(
            species=Species.RHESUS_MACAQUE,
            sex=Sex.FEMALE,
            date_of_birth=None,  # No date provided
            year_of_birth=2021,
            mating_status=MatingStatus.UNKNOWN,
            source=Organization.AI,
        )

        assert subject.date_of_birth is None
        assert subject.year_of_birth == 2021


class TestCalibrationObject:
    """Test the calibration object model"""

    def test_calibration_object_with_description_only(self):
        """Test creating a CalibrationObject with only description (minimal case)"""

        calibration_obj = CalibrationObject(description="Simple calibration sphere")

        assert calibration_obj.description == "Simple calibration sphere"
        assert not calibration_obj.empty  # Default should be False
        assert calibration_obj.objects is None  # Default should be None

    def test_calibration_object_empty(self):
        """Test creating an empty CalibrationObject"""

        calibration_obj = CalibrationObject(empty=True, description="Empty calibration - no object used")

        assert calibration_obj.empty
        assert calibration_obj.description == "Empty calibration - no object used"
        assert calibration_obj.objects is None


class TestBreedingInfo:
    """Test the breeding info model"""

    def test_breeding_info(self):
        """Test creating BreedingInfo"""

        breeding_info = BreedingInfo(
            maternal_id="M001", maternal_genotype="wt/wt", paternal_id="P001", paternal_genotype="wt/wt"
        )

        assert breeding_info.maternal_id == "M001"
        assert breeding_info.maternal_genotype == "wt/wt"
        assert breeding_info.paternal_id == "P001"
        assert breeding_info.paternal_genotype == "wt/wt"
