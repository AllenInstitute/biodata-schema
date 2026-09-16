"""test Imaging"""

from datetime import datetime, timezone

import pytest
from biodata_models.modalities import Modality
from biodata_models.organizations import Organization
from pydantic import ValidationError

from biodata_schema.components.configs import Image
from biodata_schema.components.coordinates import Affine, Rotation, Scale, Translation
from biodata_schema.components.devices import Laser, Objective, ScanningStage
from biodata_schema.components.identifiers import Code
from biodata_schema.core.acquisition import Acquisition
from biodata_schema.core.instrument import Instrument
from biodata_schema.core.processing import DataProcess, ProcessName, ProcessStage
from examples.exaspim_acquisition import acq
from tests.coordinate_systems import BREGMA_ARI


class TestImaging:
    """test imaging schemas"""

    def test_acquisition_constructor(self):
        """testing Acquisition constructor"""
        with pytest.raises(ValidationError):
            Acquisition()

        assert acq is not None

    def test_instrument_constructor(self):
        """testing Instrument constructor"""
        with pytest.raises(ValidationError):
            Instrument()

        laser = Laser(
            manufacturer=Organization.HAMAMATSU,
            serial_number="1234",
            name="Laser A",
            wavelength=488,
        )

        objective = Objective(
            name="TLX Objective",
            numerical_aperture=0.2,
            magnification=3.6,
            immersion="multi",
            manufacturer=Organization.THORLABS,
            model="TL4X-SAP",
            notes="Thorlabs TL4X-SAP with LifeCanvas dipping cap and correction optics.",
        )

        scan_stage = ScanningStage(
            name="Sample stage Z",
            model="LS-50",
            manufacturer=Organization.ASI,
            stage_axis_direction="Detection axis",
            stage_axis_name="Z",
            travel=50,
        )

        i = Instrument(
            instrument_id="room_exaSPIM1-1_20231004",
            modalities=[Modality.SPIM],
            global_coordinate_system=BREGMA_ARI,
            modification_date=datetime.now().date(),
            components=[objective, laser, scan_stage],
        )

        assert i is not None

    def test_modality_spim_requires_components(self):
        """testing Modality SPIM requires components"""
        with pytest.raises(ValidationError) as e2:
            Instrument(
                instrument_id="room_exaSPIM1-1_20231004",
                modalities=[Modality.SPIM],
                modification_date=datetime(2020, 10, 10, 0, 0, 0).date(),
                global_coordinate_system=BREGMA_ARI,
                components=[],
            )

        assert "modality 'SPIM' requires at least one device" in repr(e2.value)

    def test_registration(self):
        """test the tile models"""
        parameters = {
            "tiles": [
                Image(
                    channel_name="488",
                    image_to_acquisition_transform=[
                        Affine(affine_transform=[[0, 1, 2, 3], [4, 5, 6, 7], [8, 9, 10, 11], [0, 0, 0, 1]]),
                    ],
                ),
                Image(
                    channel_name="488",
                    image_to_acquisition_transform=[
                        Translation(
                            translation=[0, 1, 2],
                        ),
                        Rotation(
                            angles=[1, 2, 3],
                        ),
                        Scale(
                            scale=[1, 2, 3],
                        ),
                    ],
                ),
            ],
        }
        t = DataProcess(
            process_type=ProcessName.IMAGE_TILE_ALIGNMENT,
            stage=ProcessStage.PROCESSING,
            experimenters=["Dr. Dan"],
            start_date_time=datetime.now(tz=timezone.utc),
            end_date_time=datetime.now(tz=timezone.utc),
            output_path="some/path",
            code=Code(
                url="https://github.com/abcd",
                parameters=parameters,
                version="0.0.1",
            ),
        )

        assert t is not None
