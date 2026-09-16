"""Test for merge functions"""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pytest
from biodata_models.modalities import Modality

from biodata_schema.components.identifiers import Code
from biodata_schema.core.acquisition import AcquisitionSubjectDetails
from biodata_schema.core.procedures import Procedures
from biodata_schema.core.processing import DataProcess, Processing, ProcessName, ProcessStage
from biodata_schema.core.quality_control import QCMetric, QCStatus, QualityControl, Stage, Status
from examples.exaspim_acquisition import acq
from examples.procedures import p, t, t2


class TestComposability:
    """Tests for merge functions"""

    @classmethod
    def setup_class(cls):
        """Load example files for testing"""
        cls.exaspim_acquisition = acq
        cls.procedures = p
        cls.procedures_time0 = t
        cls.procedures_time1 = t2

    def test_merge_quality_control(self):
        """Test adding two QualityControl objects"""

        metrics = [
            QCMetric(
                name="Dict example",
                modality=Modality.ECEPHYS,
                stage=Stage.PROCESSING,
                value={"stuff": "in_a_dict"},
                status_history=[
                    QCStatus(evaluator="Bob", timestamp=datetime.fromisoformat("2020-10-10"), status=Status.PASS)
                ],
                tags={"type": "Drift map"},
            ),
            QCMetric(
                name="Drift map pass/fail",
                modality=Modality.ECEPHYS,
                stage=Stage.PROCESSING,
                value=False,
                description="Manual evaluation of whether the drift map looks good",
                reference="s3://some-data-somewhere",
                status_history=[
                    QCStatus(evaluator="Bob", timestamp=datetime.fromisoformat("2020-10-10"), status=Status.PASS)
                ],
                tags={"type": "Drift map"},
            ),
        ]

        q1 = QualityControl(
            metrics=metrics,
            default_grouping=["type"],
        )

        q2 = QualityControl(
            metrics=metrics + metrics,
            default_grouping=["type"],
        )

        q3 = q1 + q2
        assert q3 is not None
        assert len(q3.metrics) == 6
        assert q3.default_grouping == ["type"]

        # Test incompatible schema versions
        q1_orig_schema_v = q1.schema_version
        q1.schema_version = "0.1.0"

        with pytest.raises(ValueError) as context:
            q1 + q2
        assert "Cannot combine QualityControl objects with different schema versions" in repr(context.value)

        # Test various versions of concatenating notes
        q1.schema_version = q1_orig_schema_v
        q1.notes = "note1"
        q2.notes = "note2"
        q3 = q1 + q2
        assert q3.notes == "note1\nnote2"

        q1.notes = None
        q3 = q1 + q2
        assert q3.notes == "note2"

        q1.notes = "note1"
        q2.notes = None
        q3 = q1 + q2
        assert q3.notes == "note1"

        # Test duplicate removal in merging
        q1 = QualityControl(
            metrics=metrics,
            key_experimenters=["Alice", "Bob"],
            default_grouping=["group1", ("group1", "group2")],
            allow_tag_failures=["FailTag1", "FailTag2"],
        )

        q2 = QualityControl(
            metrics=metrics,
            key_experimenters=["Bob", "Charlie"],  # Bob is duplicate
            default_grouping=[("group1", "group2"), "group3"],  # ("group1", "group2") is duplicate
            allow_tag_failures=["FailTag2", "FailTag3"],  # FailTag2 is duplicate
        )

        # Test that naive concatenation would have duplicates
        naive_experimenters = (q1.key_experimenters or []) + (q2.key_experimenters or [])
        naive_default_grouping = q1.default_grouping + q2.default_grouping
        naive_allow_tag_failures = q1.allow_tag_failures + q2.allow_tag_failures

        assert naive_experimenters.count("Bob") == 2  # Should have duplicates
        assert naive_default_grouping.count(("group1", "group2")) == 2  # Should have duplicates
        assert naive_allow_tag_failures.count("FailTag2") == 2  # Should have duplicates

        # Test that the + operator removes duplicates
        q3 = q1 + q2

        assert q3.key_experimenters is not None
        assert q3.key_experimenters.count("Bob") == 1  # Should be deduplicated
        assert set(q3.key_experimenters) == {"Alice", "Bob", "Charlie"}

        assert len(q3.default_grouping) == 2
        assert q3.default_grouping[0] == ("group1", "group2")
        assert q3.default_grouping[1] == ("group1", "group2", "group3")

        assert q3.allow_tag_failures.count("FailTag2") == 1  # Should be deduplicated
        assert set(q3.allow_tag_failures) == {"FailTag1", "FailTag2", "FailTag3"}

    def test_merge_acquisition(self):
        """Test merging two Acquisition objects"""

        t = datetime(2022, 11, 22, 8, 43, 00, tzinfo=ZoneInfo("America/Los_Angeles"))

        acq1 = self.exaspim_acquisition.model_copy()
        acq2 = self.exaspim_acquisition.model_copy()

        merged_acq = acq1 + acq2

        assert len(merged_acq.experimenters) == 1
        assert len(merged_acq.maintenance) == 2
        assert len(merged_acq.calibrations) == 2
        assert len(merged_acq.data_streams) == 1
        assert merged_acq.acquisition_start_time == t
        assert merged_acq.acquisition_end_time == t
        assert merged_acq.acquisition_type == "ExaSPIM"
        assert merged_acq.instrument_id == acq1.instrument_id

        empty_type_acq = self.exaspim_acquisition.model_copy()
        empty_type_acq.acquisition_type = ""
        merged_empty_type = empty_type_acq + acq2
        assert merged_empty_type.acquisition_type == "ExaSPIM"

        merged_empty_type = acq2 + empty_type_acq
        assert merged_empty_type.acquisition_type == "ExaSPIM"

        conflicting_type_acq = self.exaspim_acquisition.model_copy()
        conflicting_type_acq.acquisition_type = "Other"
        with pytest.raises(ValueError):
            acq2 + conflicting_type_acq

        # Test duplicate removal in merging
        acq3 = self.exaspim_acquisition.model_copy()
        acq4 = self.exaspim_acquisition.model_copy()

        # Add duplicate values to test removal
        acq3.experimenters = ["Alice", "Bob"]
        acq3.ethics_review_id = ["ethics1", "ethics2"]

        acq4.experimenters = ["Bob", "Charlie"]  # Bob is duplicate
        acq4.ethics_review_id = ["ethics2", "ethics3"]  # ethics2 is duplicate

        # Test that naive concatenation would have duplicates
        naive_experimenters = acq3.experimenters + acq4.experimenters
        naive_ethics_review_id = (acq3.ethics_review_id or []) + (acq4.ethics_review_id or [])

        assert naive_experimenters.count("Bob") == 2  # Should have duplicates
        assert naive_ethics_review_id.count("ethics2") == 2  # Should have duplicates

        # Test that the + operator removes duplicates
        merged_acq_dedup = acq3 + acq4

        assert merged_acq_dedup.experimenters.count("Bob") == 1  # Should be deduplicated
        assert set(merged_acq_dedup.experimenters) == {"Alice", "Bob", "Charlie"}

        assert merged_acq_dedup.ethics_review_id is not None
        assert merged_acq_dedup.ethics_review_id.count("ethics2") == 1  # Should be deduplicated
        assert set(merged_acq_dedup.ethics_review_id) == {"ethics1", "ethics2", "ethics3"}

        # Test incompatible schema versions
        acq1_orig_schema_v = acq1.schema_version
        acq1.schema_version = "0.1.0"

        with pytest.raises(ValueError) as context:
            acq1 + acq2
        assert "Cannot combine Acquisition objects with different schema versions" in repr(context.value)

        acq1.schema_version = acq1_orig_schema_v

        # Test incompatible subject IDs
        acq2.subject_id = "different_id"
        with pytest.raises(ValueError) as context:
            acq1 + acq2
        assert "Cannot combine Acquisition objects that differ in key fields" in repr(context.value)

        # Test instrument_id merging
        acq2.subject_id = acq1.subject_id
        acq1.instrument_id = "instrument_zebra"
        acq2.instrument_id = "instrument_apple"
        merged_acq_instruments = acq1 + acq2
        assert merged_acq_instruments.instrument_id == "instrument_apple_instrument_zebra"

        # Test incompatible SubjectDetails
        acq1 = self.exaspim_acquisition.model_copy()
        acq2 = self.exaspim_acquisition.model_copy()
        subject_details = AcquisitionSubjectDetails(
            mouse_platform_name="mouse_platform_name",
        )
        acq1.subject_details = subject_details
        acq2.subject_details = subject_details

        with pytest.raises(ValueError) as context:
            acq1 + acq2
        assert "SubjectDetails cannot be combined in Acquisition" in repr(context.value)

    def test_procedures_add(self):
        """Test the __add__ method of Procedures"""

        p1 = self.procedures.model_copy()
        p2 = self.procedures.model_copy()

        combined = p1 + p2

        assert combined.subject_id == "625100"
        assert len(combined.subject_procedures) == 4
        assert combined.subject_procedures[0].start_date == self.procedures_time0.date()
        assert combined.subject_procedures[1].start_date == self.procedures_time1.date()
        assert combined.subject_procedures[2].start_date == self.procedures_time0.date()
        assert combined.subject_procedures[3].start_date == self.procedures_time1.date()

        # Test combining with different subject IDs raises ValueError
        p3 = Procedures(subject_id="different_id")
        with pytest.raises(ValueError):
            _ = p1 + p3

        p2.schema_version = "0.0.0"
        with pytest.raises(ValueError) as context:
            _ = p1 + p2

        assert "Schema versions must match to combine Procedures" in str(context.value)

    def test_add_processing_objects(self):
        """Test the __add__ method of Processing"""

        t = datetime(2022, 11, 22, 8, 43, 00, tzinfo=timezone.utc)

        # Create two simple Processing objects
        p1 = Processing.create_with_sequential_process_graph(
            data_processes=[
                DataProcess(
                    experimenters=["Dr. Dan"],
                    process_type=ProcessName.DENOISING,
                    stage=ProcessStage.PROCESSING,
                    output_path="path/to/outputs1",
                    start_date_time=t,
                    end_date_time=t,
                    code=Code(
                        url="https://url/for/analysis1",
                        version="0.1.1",
                    ),
                ),
            ],
            notes="First processing object",
        )

        p2 = Processing.create_with_sequential_process_graph(
            data_processes=[
                DataProcess(
                    experimenters=["Dr. Jane"],
                    process_type=ProcessName.COMPRESSION,
                    stage=ProcessStage.PROCESSING,
                    output_path="path/to/outputs2",
                    start_date_time=t,
                    end_date_time=t,
                    code=Code(
                        url="https://url/for/compression",
                        version="0.1.1",
                    ),
                ),
            ],
            notes="Second processing object",
        )

        # Combine the two Processing objects
        combined = p1 + p2

        # Check that the combined object has the correct data_processes and notes
        assert len(combined.data_processes) == 2
        assert combined.data_processes[0].name == ProcessName.DENOISING
        assert combined.data_processes[1].name == ProcessName.COMPRESSION
        assert "First processing object" in combined.notes
        assert "Second processing object" in combined.notes
        # check combined dependency graph
        assert p1.dependency_graph.items() <= combined.dependency_graph.items()
        # remove the first process from p2_graph, check that rest of the graph is unchanged in combined graph
        p2.dependency_graph.pop(p2.process_names[0])
        assert p2.dependency_graph.items() <= combined.dependency_graph.items()
        # check that the graphs are linked properly
        assert [p1.process_names[-1]] == combined.dependency_graph[p2.process_names[0]]

        # Test with incompatible schema versions
        p3 = p2.model_copy()
        p3.schema_version = "0.0.0"

        with pytest.raises(ValueError) as e:
            _ = p1 + p3
        assert "Cannot add Processing objects with different schema versions." in str(e.value)

        # Test with duplicate processes
        with pytest.warns(Warning) as w:
            combined = p1 + p1
        assert "Processing objects have repeated processes" in str(w.list[0].message)
        assert combined.data_processes[1].name == "Denoising_1"

        with pytest.warns(Warning) as w:
            combined = combined + combined
        assert "Processing objects have repeated processes" in str(w.list[0].message)
        assert combined.data_processes[2].name == "Denoising_2"
        assert combined.data_processes[3].name == "Denoising_3"

    def test_merge_dependency_graph(self):
        """Test merging dependency graphs"""

        t = datetime(2022, 11, 22, 8, 43, 00, tzinfo=timezone.utc)

        # Test None/None case
        p1 = Processing(
            data_processes=[
                DataProcess(
                    experimenters=["Dr. Dan"],
                    process_type=ProcessName.DENOISING,
                    stage=ProcessStage.PROCESSING,
                    start_date_time=t,
                    code=Code(url="https://example.com", version="1.0"),
                )
            ],
            dependency_graph=None,
        )

        p2 = Processing(
            data_processes=[
                DataProcess(
                    experimenters=["Dr. Jane"],
                    process_type=ProcessName.COMPRESSION,
                    stage=ProcessStage.PROCESSING,
                    start_date_time=t,
                    code=Code(url="https://example.com", version="1.0"),
                )
            ],
            dependency_graph=None,
        )

        combined = p1 + p2
        assert combined.dependency_graph is None

        # Test both set case
        p3 = Processing.create_with_sequential_process_graph(
            data_processes=[
                DataProcess(
                    experimenters=["Dr. Dan"],
                    process_type=ProcessName.DENOISING,
                    stage=ProcessStage.PROCESSING,
                    start_date_time=t,
                    code=Code(url="https://example.com", version="1.0"),
                )
            ],
        )

        p4 = Processing.create_with_sequential_process_graph(
            data_processes=[
                DataProcess(
                    experimenters=["Dr. Jane"],
                    process_type=ProcessName.COMPRESSION,
                    stage=ProcessStage.PROCESSING,
                    start_date_time=t,
                    code=Code(url="https://example.com", version="1.0"),
                )
            ],
        )

        combined = p3 + p4
        assert combined.dependency_graph is not None
        assert len(combined.dependency_graph) == 2
        assert "Denoising" in combined.dependency_graph
        assert "Compression" in combined.dependency_graph
        assert combined.dependency_graph["Compression"] == ["Denoising"]

        # Test self has graph, other doesn't
        combined = p3 + p2
        assert combined.dependency_graph is not None
        assert "Denoising" in combined.dependency_graph

        # Test other has graph, self doesn't
        combined = p2 + p4
        assert combined.dependency_graph is not None
        assert "Compression" in combined.dependency_graph
