"""test quality metrics"""

from datetime import datetime

import pytest
from biodata_models.modalities import Modality
from pydantic import ValidationError

from biodata_schema.core.quality_control import (
    QCMetric,
    QCStatus,
    QualityControl,
    Stage,
    Status,
    _get_filtered_statuses,
    _get_status_by_date,
)
from examples.quality_control import q as quality_control


class TestQualityControl:
    """test quality metrics schema"""

    def test_constructors(self):
        """testing constructors"""

        with pytest.raises(ValidationError):
            QualityControl()

        assert quality_control is not None

    def test_tags_property(self):
        """test that QualityControl.tags returns all unique tag values"""
        tags = quality_control.tags
        assert isinstance(tags, list)
        assert "Probe A" in tags
        assert "Probe B" in tags
        assert "Probe C" in tags
        assert "Video 1" in tags
        assert "Video 2" in tags
        assert len(tags) == 5

    def test_tag_pairs_property(self):
        """test that QualityControl.tag_pairs returns all unique key:value pairs"""
        tag_pairs = quality_control.tag_pairs
        assert isinstance(tag_pairs, list)
        assert "probe:Probe A" in tag_pairs
        assert "probe:Probe B" in tag_pairs
        assert "probe:Probe C" in tag_pairs
        assert "video:Video 1" in tag_pairs
        assert "video:Video 2" in tag_pairs
        assert len(tag_pairs) == 5

    def test_overall_status(self):
        """test that overall status goes to pass/pending/fail correctly"""

        test_metrics = [
            QCMetric(
                name="Dict example",
                modality=Modality.ECEPHYS,
                stage=Stage.PROCESSING,
                value={"stuff": "in_a_dict"},
                status_history=[
                    QCStatus(evaluator="Bob", timestamp=datetime.fromisoformat("2020-10-10"), status=Status.PASS)
                ],
                tags={"group": "Drift map"},
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
                tags={"group": "Drift map"},
            ),
        ]

        assert test_metrics[0].status.status == Status.PASS

        q = QualityControl(metrics=test_metrics + test_metrics, default_grouping=["group"])  # duplicate the metrics

        # check that overall status gets auto-set if it has never been set before
        assert q.evaluate_status() == Status.PASS

        # Add a pending metric
        q.metrics.append(
            QCMetric(
                name="Drift map pending",
                modality=Modality.ECEPHYS,
                stage=Stage.PROCESSING,
                value=False,
                description="Manual evaluation of whether the drift map looks good",
                reference="s3://some-data-somewhere",
                status_history=[
                    QCStatus(
                        evaluator="Automated", timestamp=datetime.fromisoformat("2020-10-10"), status=Status.PENDING
                    )
                ],
                tags={"group": "Drift map"},
            )
        )

        assert q.evaluate_status() == Status.PENDING

        # Add a failing metric
        q.metrics.append(
            QCMetric(
                name="Drift map fail",
                modality=Modality.ECEPHYS,
                stage=Stage.PROCESSING,
                value=False,
                description="Manual evaluation of whether the drift map looks good",
                reference="s3://some-data-somewhere",
                status_history=[
                    QCStatus(evaluator="Automated", timestamp=datetime.fromisoformat("2020-10-10"), status=Status.FAIL)
                ],
                tags={"group": "Drift map"},
            )
        )

        assert q.evaluate_status() == Status.FAIL

    def test_evaluation_status(self):
        """test that evaluation status goes to pass/pending/fail correctly"""
        metrics = [
            QCMetric(
                name="Multiple values example",
                modality=Modality.ECEPHYS,
                stage=Stage.PROCESSING,
                value={"stuff": "in_a_dict"},
                status_history=[
                    QCStatus(evaluator="Automated", timestamp=datetime.fromisoformat("2020-10-10"), status=Status.PASS)
                ],
                tags={"group": "Drift map"},
            ),
            QCMetric(
                name="Drift map pass/fail",
                modality=Modality.ECEPHYS,
                stage=Stage.PROCESSING,
                value=False,
                description="Manual evaluation of whether the drift map looks good",
                reference="s3://some-data-somewhere",
                status_history=[
                    QCStatus(evaluator="Automated", timestamp=datetime.fromisoformat("2020-10-10"), status=Status.PASS)
                ],
                tags={"group": "Drift map"},
            ),
        ]

        qc = QualityControl(metrics=metrics, default_grouping=["group"])
        assert qc.evaluate_status(tag="Drift map") == Status.PASS

        # Add a pending metric, evaluation should now evaluate to pending
        qc.metrics.append(
            QCMetric(
                name="Drift map pending",
                modality=Modality.ECEPHYS,
                stage=Stage.PROCESSING,
                value=False,
                description="Manual evaluation of whether the drift map looks good",
                reference="s3://some-data-somewhere",
                status_history=[
                    QCStatus(
                        evaluator="Automated", timestamp=datetime.fromisoformat("2020-10-10"), status=Status.PENDING
                    )
                ],
                tags={"group": "Drift map"},
            )
        )

        assert qc.evaluate_status(tag="Drift map") == Status.PENDING

        # Add a failing metric, evaluation should now evaluate to fail
        qc.metrics.append(
            QCMetric(
                name="Drift map fail",
                modality=Modality.ECEPHYS,
                stage=Stage.PROCESSING,
                value=False,
                description="Manual evaluation of whether the drift map looks good",
                reference="s3://some-data-somewhere",
                status_history=[
                    QCStatus(evaluator="Automated", timestamp=datetime.fromisoformat("2020-10-10"), status=Status.FAIL)
                ],
                tags={"group": "Drift map"},
            )
        )

        assert qc.evaluate_status(tag="group:Drift map") == Status.FAIL

    def test_allowed_failed_metrics(self):
        """Test that if you set the flag to allow failures that tags pass"""

        metrics = [
            QCMetric(
                name="Multiple values example",
                modality=Modality.ECEPHYS,
                stage=Stage.PROCESSING,
                value={"stuff": "in_a_dict"},
                status_history=[
                    QCStatus(evaluator="Automated", timestamp=datetime.fromisoformat("2020-10-10"), status=Status.PASS)
                ],
                tags={"group": "Drift map"},
            ),
            QCMetric(
                name="Drift map pass/fail",
                modality=Modality.ECEPHYS,
                stage=Stage.PROCESSING,
                value=False,
                description="Manual evaluation of whether the drift map looks good",
                reference="s3://some-data-somewhere",
                status_history=[
                    QCStatus(
                        evaluator="Automated", timestamp=datetime.fromisoformat("2020-10-10"), status=Status.PENDING
                    )
                ],
                tags={"group": "Drift map"},
            ),
        ]

        # First check that a pending evaluation still evaluates properly
        qc = QualityControl(
            metrics=metrics,
            default_grouping=["group"],
        )

        assert qc.evaluate_status(tag="group:Drift map") == Status.PENDING

        # Replace the pending evaluation with a fail, evaluation should not evaluate to pass
        qc.metrics[1].status_history[0].status = Status.FAIL

        assert qc.evaluate_status(tag="group:Drift map") == Status.FAIL

        # Now add the tag to allow_tag_failures
        qc.allow_tag_failures = ["group:Drift map"]

        assert qc.evaluate_status(tag="group:Drift map") == Status.PASS

    def test_metric_history_order(self):
        """Test that the order of the metric status history list is preserved when dumping"""
        t0 = datetime.fromisoformat("2020-10-10")
        t1 = datetime.fromisoformat("2020-10-11")
        t2 = datetime.fromisoformat("2020-10-12")

        metric = QCMetric(
            name="Multiple values example",
            modality=Modality.ECEPHYS,
            stage=Stage.PROCESSING,
            value={"stuff": "in_a_dict"},
            status_history=[
                QCStatus(evaluator="Automated", timestamp=t0, status=Status.PASS),
                QCStatus(evaluator="Automated", timestamp=t1, status=Status.PASS),
                QCStatus(evaluator="Automated", timestamp=t2, status=Status.PASS),
            ],
            tags={"group": "Drift map"},
        )

        qc = QualityControl(metrics=[metric], default_grouping=["group"])

        # roundtrip to json to check that metric order is preserved
        json = qc.model_dump_json()
        qc_rebuild = QualityControl.model_validate_json(json)

        # because the actual model uses AwareDatetime objects we have to strip the timezone
        roundtrip_t0 = qc_rebuild.metrics[0].status_history[0].timestamp
        roundtrip_t1 = qc_rebuild.metrics[0].status_history[1].timestamp
        roundtrip_t2 = qc_rebuild.metrics[0].status_history[2].timestamp

        roundtrip_t0 = roundtrip_t0.replace(tzinfo=None)
        roundtrip_t1 = roundtrip_t1.replace(tzinfo=None)
        roundtrip_t2 = roundtrip_t2.replace(tzinfo=None)

        assert roundtrip_t0 == t0
        assert roundtrip_t1 == t1
        assert roundtrip_t2 == t2

    def test_metric_status(self):
        """Ensure that at least one status object exists for metric_status_history"""

        with pytest.raises(ValueError) as context:
            QCMetric(
                name="Multiple values example",
                modality=Modality.ECEPHYS,
                stage=Stage.PROCESSING,
                value={"stuff": "in_a_dict"},
                status_history=[],
            )

        expected_exception = "List should have at least 1 item after validation, not 0"
        assert expected_exception in repr(context.value)

    def test_multi_acquisition(self):
        """Ensure that the multi-asset QC validator checks for evaluated_assets"""
        # Check for non-multi-acquisition that all evaluated_assets are None
        t0 = datetime.fromisoformat("2020-10-10")

        metric = QCMetric(
            name="Dict example",
            modality=Modality.ECEPHYS,
            stage=Stage.PROCESSING,
            value={"stuff": "in_a_dict"},
            status_history=[
                QCStatus(evaluator="Automated", timestamp=t0, status=Status.PASS),
            ],
            tags={"type": "Test"},
        )

        assert metric.stage != Stage.MULTI_ASSET
        assert metric.evaluated_assets is None

        # Check that single-asset QC with evaluated_assets throws a validation error
        with pytest.raises(ValidationError) as context:
            QCMetric(
                name="Dict with evaluated assets list",
                modality=Modality.ECEPHYS,
                stage=Stage.PROCESSING,
                value={"stuff": "in_a_dict"},
                status_history=[
                    QCStatus(evaluator="Automated", timestamp=t0, status=Status.PASS),
                ],
                evaluated_assets=["asset0", "asset1"],
                tags={"type": "Test"},
            )

        assert "is a single-asset metric and should not have evaluated_assets" in repr(context.value)

        # Check that multi-asset with empty evaluated_assets raises a validation error
        with pytest.raises(ValidationError) as context:
            QCMetric(
                name="Missing evaluated assets",
                modality=Modality.ECEPHYS,
                stage=Stage.MULTI_ASSET,
                value={"stuff": "in_a_dict"},
                status_history=[
                    QCStatus(evaluator="Automated", timestamp=t0, status=Status.PASS),
                ],
                evaluated_assets=[],
                tags={"type": "Test"},
            )

        assert "is a multi-asset metric and must have evaluated_assets" in repr(context.value)

        # Check that multi-asset with missing evaluated_assets raises a validation error
        with pytest.raises(ValidationError) as context:
            QCMetric(
                name="Multiple values example",
                modality=Modality.ECEPHYS,
                stage=Stage.MULTI_ASSET,
                value={"stuff": "in_a_dict"},
                status_history=[
                    QCStatus(evaluator="Automated", timestamp=t0, status=Status.PASS),
                ],
                tags={"type": "Test"},
            )

        assert "is a multi-asset metric and must have evaluated_assets" in repr(context.value)

    def test_status_filters(self):
        """Test that QualityControl.status(modality, stage) filters correctly"""

        test_metrics = [
            QCMetric(
                name="Multiple values example",
                modality=Modality.ECEPHYS,
                stage=Stage.PROCESSING,
                value={"stuff": "in_a_dict"},
                status_history=[
                    QCStatus(evaluator="Bob", timestamp=datetime.fromisoformat("2020-10-10"), status=Status.PASS)
                ],
                tags={"group": "test_group"},
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
                tags={"group": "test_group"},
            ),
            QCMetric(
                name="Multiple values example 2",
                modality=Modality.BEHAVIOR,
                stage=Stage.RAW,
                value={"stuff": "in_a_dict"},
                status_history=[
                    QCStatus(evaluator="Bob", timestamp=datetime.fromisoformat("2020-10-10"), status=Status.FAIL)
                ],
                tags={"group": "test_group2"},
            ),
            QCMetric(
                name="Drift map pass/fail 2",
                modality=Modality.BEHAVIOR,
                stage=Stage.RAW,
                value=False,
                description="Manual evaluation of whether the drift map looks good",
                reference="s3://some-data-somewhere",
                status_history=[
                    QCStatus(evaluator="Bob", timestamp=datetime.fromisoformat("2020-10-10"), status=Status.PASS)
                ],
                tags={"group": "test_group2"},
            ),
            QCMetric(
                name="Multiple values example 3",
                modality=Modality.BEHAVIOR_VIDEOS,
                stage=Stage.RAW,
                value={"stuff": "in_a_dict"},
                status_history=[
                    QCStatus(evaluator="Bob", timestamp=datetime.fromisoformat("2020-10-10"), status=Status.PENDING)
                ],
                tags={"type": "tag1"},
            ),
            QCMetric(
                name="Drift map pass/fail 3",
                modality=Modality.BEHAVIOR_VIDEOS,
                stage=Stage.RAW,
                value=False,
                description="Manual evaluation of whether the drift map looks good",
                reference="s3://some-data-somewhere",
                status_history=[
                    QCStatus(evaluator="Bob", timestamp=datetime.fromisoformat("2020-10-10"), status=Status.PASS)
                ],
                tags={"type": "tag1"},
            ),
        ]

        # Confirm that the status filters work
        q = QualityControl(metrics=test_metrics, default_grouping=[("group", "type")])

        # Check that the status field was built correctly
        assert q.status == {
            # Stages
            "Processing": Status.PASS,
            "Raw data": Status.FAIL,
            # Modalities
            "behavior": Status.FAIL,
            "behavior-videos": Status.PENDING,
            "ecephys": Status.PASS,
            # Tags (now in key:value format)
            "group:test_group": Status.PASS,
            "group:test_group2": Status.FAIL,
            "type:tag1": Status.PENDING,
        }

        assert q.evaluate_status() == Status.FAIL
        assert q.evaluate_status(modality=Modality.BEHAVIOR) == Status.FAIL
        assert q.evaluate_status(modality=Modality.ECEPHYS) == Status.PASS
        assert q.evaluate_status(modality=[Modality.ECEPHYS, Modality.BEHAVIOR]) == Status.FAIL
        assert q.evaluate_status(stage=Stage.RAW) == Status.FAIL
        assert q.evaluate_status(stage=Stage.PROCESSING) == Status.PASS
        assert q.evaluate_status(tag="type:tag1") == Status.PENDING

    def test_status_date(self):
        """QualityControl.status(date=) should return the correct status for the given date"""

        t1 = datetime.fromisoformat("1000-01-01 00:00:00+00:00")
        t2 = datetime.fromisoformat("2000-01-01 00:00:00+00:00")
        t3 = datetime.fromisoformat("3000-01-01 00:00:00+00:00")

        metric = QCMetric(
            name="Drift map pass/fail",
            modality=Modality.ECEPHYS,
            stage=Stage.PROCESSING,
            value=False,
            status_history=[
                QCStatus(evaluator="Bob", timestamp=t1, status=Status.FAIL),
                QCStatus(evaluator="Bob", timestamp=t2, status=Status.PENDING),
                QCStatus(evaluator="Bob", timestamp=t3, status=Status.PASS),
            ],
            tags={"group": "test_group"},
        )

        # Note: The date filtering is currently not implemented in the new schema
        # This test would need to be updated once date filtering is implemented
        qc = QualityControl(metrics=[metric], default_grouping=["group"])

        assert qc.evaluate_status(date=t3) == Status.PASS
        assert qc.evaluate_status(date=t2) == Status.PENDING
        assert qc.evaluate_status(date=t1) == Status.FAIL

    def test_get_status_by_date_helper(self):
        """Test the _get_status_by_date helper function with various scenarios"""

        # Create timestamps for testing
        t1 = datetime.fromisoformat("2020-01-01T00:00:00+00:00")
        t2 = datetime.fromisoformat("2020-02-01T00:00:00+00:00")
        t3 = datetime.fromisoformat("2020-03-01T00:00:00+00:00")

        # Create a metric with multiple status history entries
        metric = QCMetric(
            name="Test metric",
            modality=Modality.ECEPHYS,
            stage=Stage.PROCESSING,
            value=True,
            status_history=[
                QCStatus(evaluator="Alice", timestamp=t1, status=Status.FAIL),
                QCStatus(evaluator="Bob", timestamp=t2, status=Status.PENDING),
                QCStatus(evaluator="Charlie", timestamp=t3, status=Status.PASS),
            ],
            tags={"type": "test"},
        )

        # Test getting status at different dates

        # Date before any status - should return earliest status
        early_date = datetime.fromisoformat("1999-01-01T00:00:00+00:00")
        assert _get_status_by_date(metric, early_date) == Status.FAIL

        # Date exactly at first status
        assert _get_status_by_date(metric, t1) == Status.FAIL

        # Date between first and second status
        between_t1_t2 = datetime.fromisoformat("2020-01-15T00:00:00+00:00")
        assert _get_status_by_date(metric, between_t1_t2) == Status.FAIL

        # Date exactly at second status
        assert _get_status_by_date(metric, t2) == Status.PENDING

        # Date between second and third status
        between_t2_t3 = datetime.fromisoformat("2020-02-15T00:00:00+00:00")
        assert _get_status_by_date(metric, between_t2_t3) == Status.PENDING

        # Date exactly at third status
        assert _get_status_by_date(metric, t3) == Status.PASS

        # Date after all statuses - should return most recent status
        future_date = datetime.fromisoformat("2025-01-01T00:00:00+00:00")
        assert _get_status_by_date(metric, future_date) == Status.PASS

        # Test with single status entry
        single_status_metric = QCMetric(
            name="Single status metric",
            modality=Modality.BEHAVIOR,
            stage=Stage.RAW,
            value=42,
            status_history=[
                QCStatus(evaluator="Dave", timestamp=t2, status=Status.PASS),
            ],
            tags={"type": "single"},
        )

        # Date before single status - should return that status
        assert _get_status_by_date(single_status_metric, t1) == Status.PASS
        # Date at single status
        assert _get_status_by_date(single_status_metric, t2) == Status.PASS
        # Date after single status
        assert _get_status_by_date(single_status_metric, t3) == Status.PASS

    def test_get_filtered_statuses_helper(self):
        """Test the _get_filtered_statuses helper function with various filters"""

        # Create test date
        test_date = datetime.fromisoformat("2020-06-01T00:00:00+00:00")

        # Use existing quality_control example and add some test metrics
        test_metrics = list(quality_control.metrics)  # Copy existing metrics

        # Add some additional test metrics with different modalities, stages, and tags
        additional_metrics = [
            QCMetric(
                name="Test BEHAVIOR metric",
                modality=Modality.BEHAVIOR,
                stage=Stage.PROCESSING,
                value=True,
                status_history=[QCStatus(evaluator="Test", timestamp=test_date, status=Status.PASS)],
                tags={"type": "behavior_tag", "group": "shared_tag"},
            ),
            QCMetric(
                name="Test OPHYS metric",
                modality=Modality.POPHYS,
                stage=Stage.ANALYSIS,
                value=42,
                status_history=[QCStatus(evaluator="Test", timestamp=test_date, status=Status.FAIL)],
                tags={"type": "ophys_tag", "group": "shared_tag"},
            ),
            QCMetric(
                name="Test metric with early fail",
                modality=Modality.ECEPHYS,
                stage=Stage.RAW,
                value=False,
                status_history=[
                    QCStatus(
                        evaluator="Test",
                        timestamp=datetime.fromisoformat("2020-01-01T00:00:00+00:00"),
                        status=Status.FAIL,
                    ),
                    QCStatus(evaluator="Test", timestamp=test_date, status=Status.PASS),
                ],
                tags={"test": "time_test"},
            ),
        ]

        all_metrics = test_metrics + additional_metrics

        # Test filtering by modality
        ecephys_statuses = _get_filtered_statuses(
            metrics=all_metrics,
            date=test_date,
            modality_filter=[Modality.ECEPHYS],
        )
        # Should include ECEPHYS metrics from quality_control example + our test metric
        assert len(ecephys_statuses) > 0

        behavior_statuses = _get_filtered_statuses(
            metrics=all_metrics,
            date=test_date,
            modality_filter=[Modality.BEHAVIOR],
        )
        assert len(behavior_statuses) == 1  # Our test BEHAVIOR metric
        assert behavior_statuses[0] == Status.PASS

        # Test filtering by stage
        raw_statuses = _get_filtered_statuses(
            metrics=all_metrics,
            date=test_date,
            stage_filter=[Stage.RAW],
        )
        assert len(raw_statuses) > 0

        analysis_statuses = _get_filtered_statuses(
            metrics=all_metrics,
            date=test_date,
            stage_filter=[Stage.ANALYSIS],
        )
        assert len(analysis_statuses) == 1  # Our test OPHYS metric
        assert analysis_statuses[0] == Status.FAIL

        # Test filtering by tag
        shared_tag_statuses = _get_filtered_statuses(
            metrics=all_metrics,
            date=test_date,
            tag_filter=["group:shared_tag"],
        )
        assert len(shared_tag_statuses) == 2  # Our BEHAVIOR and OPHYS test metrics
        assert Status.PASS in shared_tag_statuses
        assert Status.FAIL in shared_tag_statuses

        # Test filtering by multiple criteria
        ecephys_raw_statuses = _get_filtered_statuses(
            metrics=all_metrics,
            date=test_date,
            modality_filter=[Modality.ECEPHYS],
            stage_filter=[Stage.RAW],
        )
        assert len(ecephys_raw_statuses) > 0

        # Test date-based status retrieval
        earlier_date = datetime.fromisoformat("2020-03-01T00:00:00+00:00")
        time_test_statuses = _get_filtered_statuses(
            metrics=all_metrics,
            date=earlier_date,
            tag_filter=["test:time_test"],
        )
        assert len(time_test_statuses) == 1
        assert time_test_statuses[0] == Status.FAIL  # Should get the earlier FAIL status

        # Test allow_tag_failures
        ophys_fail_statuses = _get_filtered_statuses(
            metrics=all_metrics,
            date=test_date,
            tag_filter=["type:ophys_tag"],
            allow_tag_failures=["type:ophys_tag"],
        )
        assert len(ophys_fail_statuses) == 1
        assert ophys_fail_statuses[0] == Status.PASS  # FAIL converted to PASS

        # Test with no matching filters
        no_match_statuses = _get_filtered_statuses(
            metrics=all_metrics,
            date=test_date,
            tag_filter=["nonexistent_tag"],
        )
        assert len(no_match_statuses) == 0

        # Test with empty metrics list
        empty_statuses = _get_filtered_statuses(
            metrics=[],
            date=test_date,
        )
        assert len(empty_statuses) == 0

        # Test multiple modalities and stages
        multi_modality_statuses = _get_filtered_statuses(
            metrics=all_metrics,
            date=test_date,
            modality_filter=[Modality.BEHAVIOR, Modality.POPHYS],
        )
        assert len(multi_modality_statuses) == 2  # Our BEHAVIOR and OPHYS test metrics

        multi_stage_statuses = _get_filtered_statuses(
            metrics=all_metrics,
            date=test_date,
            stage_filter=[Stage.PROCESSING, Stage.ANALYSIS],
        )
        assert len(multi_stage_statuses) == 2  # Our BEHAVIOR and OPHYS test metrics

    def test_helper_functions_integration(self):
        """Test that helper functions work correctly when used by QualityControl.evaluate_status"""

        # Create a test date
        test_date = datetime.fromisoformat("2020-06-01T00:00:00+00:00")

        # Create metrics with time-based status changes
        metrics = [
            QCMetric(
                name="Time-sensitive metric 1",
                modality=Modality.ECEPHYS,
                stage=Stage.PROCESSING,
                value=True,
                status_history=[
                    QCStatus(
                        evaluator="Test",
                        timestamp=datetime.fromisoformat("2020-01-01T00:00:00+00:00"),
                        status=Status.FAIL,
                    ),
                    QCStatus(
                        evaluator="Test",
                        timestamp=datetime.fromisoformat("2020-06-01T00:00:00+00:00"),
                        status=Status.PASS,
                    ),
                ],
                tags={"group": "time_sensitive"},
            ),
            QCMetric(
                name="Time-sensitive metric 2",
                modality=Modality.ECEPHYS,
                stage=Stage.PROCESSING,
                value=False,
                status_history=[
                    QCStatus(
                        evaluator="Test",
                        timestamp=datetime.fromisoformat("2020-01-01T00:00:00+00:00"),
                        status=Status.PASS,
                    ),
                    QCStatus(
                        evaluator="Test",
                        timestamp=datetime.fromisoformat("2020-07-01T00:00:00+00:00"),
                        status=Status.FAIL,
                    ),
                ],
                tags={"group": "time_sensitive"},
            ),
        ]

        qc = QualityControl(
            metrics=metrics,
            default_grouping=["group"],
        )

        # Test status at different times
        early_date = datetime.fromisoformat("2020-02-01T00:00:00+00:00")
        # At early date: metric 1 is FAIL, metric 2 is PASS -> overall FAIL
        early_status = qc.evaluate_status(date=early_date, tag="group:time_sensitive")
        assert early_status == Status.FAIL

        # At test date: metric 1 is PASS, metric 2 is PASS -> overall PASS
        test_status = qc.evaluate_status(date=test_date, tag="group:time_sensitive")
        assert test_status == Status.PASS

        # At late date: metric 1 is PASS, metric 2 is FAIL -> overall FAIL
        late_date = datetime.fromisoformat("2020-08-01T00:00:00+00:00")
        late_status = qc.evaluate_status(date=late_date, tag="group:time_sensitive")
        assert late_status == Status.FAIL

    def test_new_format_default_grouping_all_strings(self):
        """Test that new format with all strings in default_grouping is NOT converted"""

        # Test new format: list of strings for default_grouping + dict-based tags
        new_format_dict = {
            "metrics": [
                {
                    "object_type": "QC metric",
                    "name": "New format metric",
                    "modality": {"name": "Extracellular electrophysiology", "abbreviation": "ecephys"},
                    "stage": "Processing",
                    "value": 42,
                    "status_history": [{"evaluator": "Test", "timestamp": "2020-10-10", "status": "Pass"}],
                    "tags": {"group": "test_group", "probe": "probeA"},
                }
            ],
            "default_grouping": ["group", "probe"],
        }

        qc_new = QualityControl.model_validate(new_format_dict)

        # Should NOT convert - keep as-is
        assert qc_new.default_grouping == ["group", "probe"]
        # Tags should remain as dict
        assert qc_new.metrics[0].tags == {"group": "test_group", "probe": "probeA"}

    def test_new_format_default_grouping_mixed(self):
        """Test that new format with mixed strings and tuples in default_grouping is NOT converted"""

        # Test new format: mixed strings and tuples for default_grouping + dict-based tags
        new_format_dict = {
            "metrics": [
                {
                    "object_type": "QC metric",
                    "name": "New format metric",
                    "modality": {"name": "Extracellular electrophysiology", "abbreviation": "ecephys"},
                    "stage": "Processing",
                    "value": 42,
                    "status_history": [{"evaluator": "Test", "timestamp": "2020-10-10", "status": "Pass"}],
                    "tags": {"group": "test_group", "probe": "probeA", "shank": "shank1"},
                }
            ],
            "default_grouping": ["group", ("probe", "shank")],
        }

        qc_new = QualityControl.model_validate(new_format_dict)

        # Should NOT convert - keep as-is
        assert qc_new.default_grouping == ["group", ("probe", "shank")]
        # Tags should remain as dict
        assert qc_new.metrics[0].tags == {"group": "test_group", "probe": "probeA", "shank": "shank1"}

    def test_empty_metrics_does_not_convert_default_grouping(self):
        """Test that fix_default_grouping_list does not alter default_grouping when metrics is empty"""

        empty_metrics_dict = {
            "metrics": [],
            "default_grouping": ["group1", "group2"],
        }

        qc = QualityControl.model_validate(empty_metrics_dict)

        assert qc.default_grouping == ["group1", "group2"]
