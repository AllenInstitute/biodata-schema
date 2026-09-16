"""test processing"""

from datetime import datetime

import pydantic
import pytest
from biodata_models.system_architecture import CPUArchitecture, OperatingSystem
from biodata_models.units import MemoryUnit

from biodata_schema.components.identifiers import Code, DataAsset
from biodata_schema.core.processing import (
    DataProcess,
    Processing,
    ProcessName,
    ProcessStage,
    ResourceTimestamped,
    ResourceUsage,
)

t = datetime.fromisoformat("2024-09-13T14:00:00")
code = Code(
    name="Example pipeline",
    input_data=[
        DataAsset(url="s3 path to inputs"),
    ],
    url="https://url/for/pipeline",
    version="0.1.1",
)


class TestProcessing:
    """tests for processing schema"""

    def test_constructors(self):
        """test creation"""

        with pytest.raises(pydantic.ValidationError):
            Processing()

        # Create a valid Processing object
        p = Processing.create_with_sequential_process_graph(
            data_processes=[
                DataProcess(
                    experimenters=["Dr. Dan"],
                    process_type=ProcessName.DENOISING,
                    stage=ProcessStage.PROCESSING,
                    code=code,
                    output_path="./path/to/outputs",
                    start_date_time=t,
                    end_date_time=t,
                ),
            ]
        )

        assert p is not None
        assert p.data_processes[0].name == ProcessName.DENOISING

    def test_resource_usage(self):
        """Test the ResourceUsage class"""

        resources = ResourceUsage(
            os=OperatingSystem.MACOS_SONOMA,
            architecture=CPUArchitecture.X86_64,
            cpu_usage=[ResourceTimestamped(timestamp=datetime.fromisoformat("2024-09-13"), usage=0.5)],
        )

        assert resources is not None

        with pytest.raises(pydantic.ValidationError):
            ResourceUsage()

    def test_resource_usage_unit_validators(self):
        """Test that unit validators work"""

        # Check ram
        with pytest.raises(ValueError) as e:
            ResourceUsage(
                os=OperatingSystem.MACOS_SONOMA,
                architecture=CPUArchitecture.X86_64,
                cpu_usage=[ResourceTimestamped(timestamp=datetime.fromisoformat("2024-09-13"), usage=0.5)],
                ram=1,
            )

        expected_exception = "Unit ram_unit is required when ram is set"

        assert expected_exception in repr(e.value)

        resources = ResourceUsage(
            os=OperatingSystem.MACOS_SONOMA,
            architecture=CPUArchitecture.X86_64,
            cpu_usage=[ResourceTimestamped(timestamp=datetime.fromisoformat("2024-09-13"), usage=0.5)],
            ram=1,
            ram_unit=MemoryUnit.GB,
        )
        assert resources is not None

        # Check system memory
        with pytest.raises(ValueError) as e:
            ResourceUsage(
                os=OperatingSystem.MACOS_SONOMA,
                architecture=CPUArchitecture.X86_64,
                cpu_usage=[ResourceTimestamped(timestamp=datetime.fromisoformat("2024-09-13"), usage=0.5)],
                system_memory=1,
            )

        expected_exception = "Unit system_memory_unit is required when system_memory is set"

        assert expected_exception in repr(e.value)

        # Test with no data_processes (covered by the model's default validation).

    def test_unique_process_names(self):
        """Test that process names are unique within a Processing object"""

        # Test with duplicate process names
        with pytest.raises(ValueError) as e:
            Processing.create_with_sequential_process_graph(
                data_processes=[
                    DataProcess(
                        experimenters=["Dr. Dan"],
                        process_type=ProcessName.DENOISING,
                        stage=ProcessStage.PROCESSING,
                        start_date_time=t,
                        end_date_time=t,
                        code=code,
                    ),
                    DataProcess(
                        experimenters=["Dr. Dan"],
                        process_type=ProcessName.DENOISING,
                        stage=ProcessStage.PROCESSING,
                        start_date_time=t,
                        end_date_time=t,
                        code=code,
                    ),
                ]
            )
        assert "data_processes must have unique names" in str(e.value)

    def test_validate_data_processes(self):
        """Test the validate_data_processes method"""

        # Test with valid data_processes
        p = Processing.create_with_sequential_process_graph(
            data_processes=[
                DataProcess(
                    experimenters=["Dr. Dan"],
                    name="My Analysis",
                    process_type=ProcessName.ANALYSIS,
                    stage=ProcessStage.ANALYSIS,
                    output_path="./path/to/outputs",
                    start_date_time=t,
                    end_date_time=t,
                    code=code,
                ),
            ]
        )
        assert p is not None

        # Test with data_processes as a list of lists
        with pytest.raises(pydantic.ValidationError):
            Processing(
                data_processes=[
                    [
                        DataProcess(
                            experimenters=["Dr. Dan"],
                            name="My Analysis",
                            process_type=ProcessName.ANALYSIS,
                            stage=ProcessStage.ANALYSIS,
                            output_path="./path/to/outputs",
                            start_date_time=t,
                            end_date_time=t,
                            code=code,
                        ),
                    ]
                ]
            )

    def test_rename_process(self):
        """Test the rename_process method"""
        # Create a processing object with multiple processes
        process1 = DataProcess(
            name="process1",
            experimenters=["Dr. Dan"],
            process_type=ProcessName.COMPRESSION,
            stage=ProcessStage.PROCESSING,
            code=code,
            start_date_time=t,
            end_date_time=t,
        )
        process2 = DataProcess(
            name="process2",
            experimenters=["Dr. Dan"],
            process_type=ProcessName.ANALYSIS,
            stage=ProcessStage.ANALYSIS,
            code=code,
            start_date_time=t,
            end_date_time=t,
        )
        process3 = DataProcess(
            name="process3",
            experimenters=["Dr. Dan"],
            process_type=ProcessName.SPIKE_SORTING,
            stage=ProcessStage.PROCESSING,
            code=code,
            start_date_time=t,
            end_date_time=t,
        )

        # Create process graph where process2 depends on process1, and process3 depends on process2
        dependency_graph = {
            "process1": [],
            "process2": ["process1"],
            "process3": ["process2"],
        }

        p = Processing(data_processes=[process1, process2, process3], dependency_graph=dependency_graph)

        # Rename process2 to new_name
        p.rename_process("process2", "new_name")

        # Check that the process was renamed in data_processes
        process_names = [proc.name for proc in p.data_processes]
        assert "new_name" in process_names
        assert "process2" not in process_names

        # Check that the process was renamed in dependency_graph keys
        assert "new_name" in p.dependency_graph
        assert "process2" not in p.dependency_graph

        # Check that references to the process were updated in dependency_graph values
        assert p.dependency_graph["process3"] == ["new_name"]
        assert p.dependency_graph["new_name"] == ["process1"]

        # Test error case - renaming a process that doesn't exist
        with pytest.raises(ValueError) as e:
            p.rename_process("non_existent", "another_name")
        assert "not found in data_processes" in str(e.value)

    def test_validate_process_graph(self):
        """Test the validate_process_graph method"""
        # Create a valid processing object
        process1 = DataProcess(
            name="process1",
            experimenters=["Dr. Dan"],
            process_type=ProcessName.COMPRESSION,
            stage=ProcessStage.PROCESSING,
            code=code,
            start_date_time=t,
            end_date_time=t,
        )
        process2 = DataProcess(
            name="process2",
            experimenters=["Dr. Dan"],
            process_type=ProcessName.ANALYSIS,
            stage=ProcessStage.ANALYSIS,
            code=code,
            start_date_time=t,
            end_date_time=t,
        )

        # Valid case - all processes are in dependency_graph and all keys in dependency_graph are processes
        dependency_graph = {
            "process1": [],
            "process2": ["process1"],
        }

        p = Processing(data_processes=[process1, process2], dependency_graph=dependency_graph)
        assert p is not None

        # Invalid case 1 - process in data_processes not in dependency_graph
        process3 = DataProcess(
            name="process3",
            experimenters=["Dr. Dan"],
            process_type=ProcessName.SPIKE_SORTING,
            stage=ProcessStage.PROCESSING,
            code=code,
            start_date_time=t,
            end_date_time=t,
        )

        with pytest.raises(ValueError) as e:
            Processing(data_processes=[process1, process2, process3], dependency_graph=dependency_graph)
        assert "dependency_graph must include all processes in data_processes" in str(e.value)

        # Invalid case 2 - process in dependency_graph not in data_processes
        invalid_graph = {
            "process1": [],
            "process2": ["process1"],
            "process3": ["process2"],
        }

        with pytest.raises(ValueError) as e:
            Processing(data_processes=[process1, process2], dependency_graph=invalid_graph)
        assert "data_processes must include all processes in dependency_graph" in str(e.value)

    def test_dependency_graph_none(self):
        """Tests that no issue is raised if dependency_graph is None"""
        processing = Processing(
            data_processes=[
                DataProcess(
                    start_date_time=datetime(2024, 10, 10, 1, 2, 3),
                    end_date_time=datetime(2024, 10, 11, 1, 2, 3),
                    process_type=ProcessName.COMPRESSION,
                    experimenters=["AIND Scientific Computing"],
                    stage=ProcessStage.PROCESSING,
                    code=Code(
                        url="www.example.com/ephys_compression",
                        version="0.0.1",
                    ),
                ),
                DataProcess(
                    start_date_time=datetime(2024, 10, 10, 1, 2, 3),
                    end_date_time=datetime(2024, 10, 11, 1, 2, 4),
                    process_type=ProcessName.OTHER,
                    experimenters=["AIND Scientific Computing"],
                    stage=ProcessStage.PROCESSING,
                    code=Code(url="", version="0.0.1"),
                    notes="Data was copied.",
                ),
            ]
        )
        assert processing.dependency_graph is None

    def test_validate_pipeline_names(self):
        """Test the validate_pipeline_names method"""

        # Create valid pipelines
        pipelines = [
            Code(name="Pipeline1", url="https://example.com/pipeline1", version="1.0"),
            Code(name="Pipeline2", url="https://example.com/pipeline2", version="1.0"),
        ]

        # Create valid data_processes
        process1 = DataProcess(
            name="process1",
            experimenters=["Dr. Dan"],
            process_type=ProcessName.COMPRESSION,
            stage=ProcessStage.PROCESSING,
            code=code,
            start_date_time=t,
            end_date_time=t,
            pipeline_name="Pipeline1",
        )
        process2 = DataProcess(
            name="process2",
            experimenters=["Dr. Dan"],
            process_type=ProcessName.ANALYSIS,
            stage=ProcessStage.ANALYSIS,
            code=code,
            start_date_time=t,
            end_date_time=t,
            pipeline_name="Pipeline2",
        )

        # Valid case
        p = Processing(
            data_processes=[process1, process2],
            dependency_graph={"process1": [], "process2": ["process1"]},
            pipelines=pipelines,
        )
        assert p is not None

        # Invalid case - pipeline_name not in pipelines list
        process3 = DataProcess(
            name="process3",
            experimenters=["Dr. Dan"],
            process_type=ProcessName.SPIKE_SORTING,
            stage=ProcessStage.PROCESSING,
            code=code,
            start_date_time=t,
            end_date_time=t,
            pipeline_name="NonExistentPipeline",
        )

        with pytest.raises(ValueError) as e:
            Processing(
                data_processes=[process1, process2, process3],
                dependency_graph={"process1": [], "process2": ["process1"], "process3": ["process2"]},
                pipelines=pipelines,
            )
        assert "Pipeline name 'NonExistentPipeline' not found in pipelines list" in str(e.value)

    def test_order_processes(self):
        """Test the order_processes method"""

        # Create processes with different start times (out of order)
        t1 = datetime.fromisoformat("2024-09-13T14:00:00")
        t2 = datetime.fromisoformat("2024-09-13T12:00:00")  # Earlier time
        t3 = datetime.fromisoformat("2024-09-13T16:00:00")  # Later time

        process1 = DataProcess(
            name="process1",
            experimenters=["Dr. Dan"],
            process_type=ProcessName.COMPRESSION,
            stage=ProcessStage.PROCESSING,
            code=code,
            start_date_time=t1,
            end_date_time=t1,
        )
        process2 = DataProcess(
            name="process2",
            experimenters=["Dr. Dan"],
            process_type=ProcessName.ANALYSIS,
            stage=ProcessStage.ANALYSIS,
            code=code,
            start_date_time=t2,
            end_date_time=t2,
        )
        process3 = DataProcess(
            name="process3",
            experimenters=["Dr. Dan"],
            process_type=ProcessName.SPIKE_SORTING,
            stage=ProcessStage.PROCESSING,
            code=code,
            start_date_time=t3,
            end_date_time=t3,
        )

        # Create Processing with out-of-order processes
        dependency_graph = {"process1": [], "process2": [], "process3": []}
        p = Processing(data_processes=[process1, process2, process3], dependency_graph=dependency_graph)

        # Check that processes were reordered by start_date_time
        expected_order = [process2, process1, process3]  # t2 < t1 < t3
        actual_names = [proc.name for proc in p.data_processes]
        expected_names = [proc.name for proc in expected_order]
        assert actual_names == expected_names

        # Check that notes were updated
        assert "Processes were reordered by start_date_time" in p.notes

        # Test with already ordered processes
        process4 = DataProcess(
            name="process4",
            experimenters=["Dr. Dan"],
            process_type=ProcessName.COMPRESSION,
            stage=ProcessStage.PROCESSING,
            code=code,
            start_date_time=t1,
            end_date_time=t1,
        )
        process5 = DataProcess(
            name="process5",
            experimenters=["Dr. Dan"],
            process_type=ProcessName.ANALYSIS,
            stage=ProcessStage.ANALYSIS,
            code=code,
            start_date_time=t3,
            end_date_time=t3,
        )

        dependency_graph2 = {"process4": [], "process5": []}
        p2 = Processing(data_processes=[process4, process5], dependency_graph=dependency_graph2)

        # Check that order wasn't changed and no reordering note was added
        assert [proc.name for proc in p2.data_processes] == ["process4", "process5"]
        assert p2.notes is None

        # Test with existing notes
        dependency_graph3 = {"process1": [], "process2": [], "process3": []}
        p3 = Processing(
            data_processes=[process1, process2, process3], dependency_graph=dependency_graph3, notes="Existing notes"
        )

        # Check that reordering note was appended to existing notes
        assert "Existing notes; Processes were reordered by start_date_time" in p3.notes

        # Test with empty data_processes
        p4 = Processing(data_processes=[], dependency_graph={})
        assert len(p4.data_processes) == 0
        assert p4.notes is None


class TestDataProcessValidateOther:
    """Tests for DataProcess.validate_other"""

    def _make(self, process_type, **kwargs):
        """Helper method to create a DataProcess with default values and override with kwargs"""
        return DataProcess(
            process_type=process_type,
            stage=ProcessStage.PROCESSING,
            experimenters=["Dr. Dan"],
            code=code,
            start_date_time=t,
            **kwargs,
        )

    # --- ProcessName.OTHER ---

    def test_other_with_name_passes(self):
        """OTHER is allowed when a custom name is provided"""
        dp = self._make(ProcessName.OTHER, name="my custom step")
        assert dp.process_type == ProcessName.OTHER

    def test_other_with_notes_passes(self):
        """OTHER is allowed when notes describe the process"""
        dp = self._make(ProcessName.OTHER, notes="some detail")
        assert dp.process_type == ProcessName.OTHER

    def test_other_with_name_and_notes_passes(self):
        """OTHER is allowed when both name and notes are provided"""
        dp = self._make(ProcessName.OTHER, name="step", notes="detail")
        assert dp.process_type == ProcessName.OTHER

    def test_other_without_name_or_notes_fails(self):
        """OTHER without name or notes should raise a ValidationError"""
        with pytest.raises(pydantic.ValidationError) as ctx:
            self._make(ProcessName.OTHER)
        assert "name' or 'notes' must specify process details" in str(ctx.value)

    # --- ProcessName.ANALYSIS ---

    def test_analysis_with_name_passes(self):
        """ANALYSIS is allowed when a custom name is provided"""
        dp = self._make(ProcessName.ANALYSIS, name="my analysis")
        assert dp.process_type == ProcessName.ANALYSIS

    def test_analysis_with_notes_passes(self):
        """ANALYSIS is allowed when notes are provided"""
        dp = self._make(ProcessName.ANALYSIS, notes="analysis detail")
        assert dp.process_type == ProcessName.ANALYSIS

    def test_analysis_without_name_or_notes_fails(self):
        """ANALYSIS without name or notes should raise a ValidationError"""
        with pytest.raises(pydantic.ValidationError) as ctx:
            self._make(ProcessName.ANALYSIS)
        assert "name' or 'notes' must specify process details" in str(ctx.value)

    # --- Other process types are not affected ---

    def test_compression_without_name_or_notes_passes(self):
        """Non-OTHER/ANALYSIS types do not require name or notes"""
        dp = self._make(ProcessName.COMPRESSION)
        assert dp.process_type == ProcessName.COMPRESSION
