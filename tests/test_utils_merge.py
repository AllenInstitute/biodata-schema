"""Tests for merge utilities"""

from unittest.mock import Mock

import pytest

from biodata_schema.utils.merge import (
    merge_coordinate_systems,
    merge_notes,
    merge_optional_list,
    merge_process_graph,
    merge_str_alphabetical,
    merge_str_tuple_lists,
)
from tests.coordinate_systems import BREGMA_ARI, MPM_MANIP_RFB


class TestMergeStrTupleLists:
    """Tests for merge_str_tuple_lists function"""

    def test_empty_lists(self):
        """Test merging two empty lists"""
        result = merge_str_tuple_lists([], [])
        assert result == []

    def test_first_list_longer(self):
        """Test merging when the first list is longer"""
        a = ["a", "b", "c"]
        b = ["d"]
        result = merge_str_tuple_lists(a, b)
        assert result == [("a", "d"), "b", "c"]

    def test_second_list_longer(self):
        """Test merging when the second list is longer"""
        a = ["a"]
        b = ["b", "c", "d"]
        result = merge_str_tuple_lists(a, b)
        assert result == [("a", "b"), "c", "d"]

    def test_tuples_in_both_lists(self):
        """Test merging when both lists contain tuples"""
        a = [("a", "b"), ("c", "d")]
        b = [("e", "f"), ("g", "h")]
        result = merge_str_tuple_lists(a, b)
        assert result == [("a", "b", "e", "f"), ("c", "d", "g", "h")]

    def test_deduplication_with_tuples(self):
        """Test deduplication when merging tuples"""
        a = [("a", "b"), "c"]
        b = [("b", "d"), "c"]
        result = merge_str_tuple_lists(a, b)
        assert result == [("a", "b", "d"), "c"]


class TestMergeStrAlphabetical:
    """Tests for merge_str_alphabetical function"""

    def test_both_strings_present(self):
        """Test merging when both strings are present"""
        result = merge_str_alphabetical("zebra", "apple")
        assert result == "apple_zebra"

    def test_both_strings_present_reverse_order(self):
        """Test merging with strings in reverse alphabetical order"""
        result = merge_str_alphabetical("apple", "zebra")
        assert result == "apple_zebra"

    def test_identical_strings(self):
        """Test merging identical strings"""
        result = merge_str_alphabetical("test", "test")
        assert result == "test"

    def test_first_string_none(self):
        """Test merging when first string is None"""
        result = merge_str_alphabetical(None, "test")
        assert result == "test"

    def test_second_string_none(self):
        """Test merging when second string is None"""
        result = merge_str_alphabetical("test", None)
        assert result == "test"

    def test_both_strings_none(self):
        """Test merging when both strings are None"""
        result = merge_str_alphabetical(None, None)
        assert result is None

    def test_multiple_words_sorted(self):
        """Test merging with multiple word strings"""
        result = merge_str_alphabetical("instrument_2", "instrument_1")
        assert result == "instrument_1_instrument_2"


class TestMergeNotes:
    """Tests for merge_notes function"""

    def test_both_notes_present(self):
        """Test merging when both notes are present"""
        notes1 = "Note 1"
        notes2 = "Note 2"
        result = merge_notes(notes1, notes2)
        assert result == "Note 1\nNote 2"

    def test_first_note_none(self):
        """Test merging when the first note is None"""
        notes1 = None
        notes2 = "Note 2"
        result = merge_notes(notes1, notes2)
        assert result == "Note 2"

    def test_second_note_none(self):
        """Test merging when the second note is None"""
        notes1 = "Note 1"
        notes2 = None
        result = merge_notes(notes1, notes2)
        assert result == "Note 1"

    def test_both_notes_none(self):
        """Test merging when both notes are None"""
        notes1 = None
        notes2 = None
        result = merge_notes(notes1, notes2)
        assert result is None


class TestRemoveDuplicates:
    """Tests for remove_duplicates function"""

    def test_empty_list(self):
        """Test with empty list"""
        from biodata_schema.utils.merge import remove_duplicates

        assert remove_duplicates([]) == []

    def test_no_duplicates(self):
        """Test with list that has no duplicates"""
        from biodata_schema.utils.merge import remove_duplicates

        assert remove_duplicates([1, 2, 3, 4]) == [1, 2, 3, 4]

    def test_with_duplicates(self, caplog):
        """Test with list that has duplicates"""
        from biodata_schema.utils.merge import remove_duplicates

        with caplog.at_level("INFO"):
            assert remove_duplicates([1, 2, 2, 3, 3, 4]) == [1, 2, 3, 4]
        assert len(caplog.records) == 1
        assert "Removed 2 duplicates from list" in caplog.text

    def test_preserves_order(self):
        """Test that order is preserved when removing duplicates"""
        from biodata_schema.utils.merge import remove_duplicates

        assert remove_duplicates([3, 1, 2, 1, 3, 4]) == [3, 1, 2, 4]

    def test_string_duplicates(self):
        """Test with string duplicates"""
        from biodata_schema.utils.merge import remove_duplicates

        assert remove_duplicates(["a", "b", "a", "c", "b"]) == ["a", "b", "c"]

    def test_all_duplicates(self):
        """Test with all elements being duplicates"""
        from biodata_schema.utils.merge import remove_duplicates

        assert remove_duplicates([1, 1, 1, 1]) == [1]


class TestMergeOptionalList:
    """Tests for merge_optional_list"""

    def test_both_none(self):
        """Test when both inputs are None"""
        assert merge_optional_list(None, None) is None

    def test_first_none(self):
        """Test when first input is None"""
        assert merge_optional_list(None, [1, 2, 3]) == [1, 2, 3]

    def test_second_none(self):
        """Test when second input is None"""
        assert merge_optional_list([1, 2, 3], None) == [1, 2, 3]

    def test_both_empty(self):
        """Test when both inputs are empty lists"""
        assert merge_optional_list([], []) is None

    def test_first_empty(self):
        """Test when first input is an empty list"""
        assert merge_optional_list([], [1, 2, 3]) == [1, 2, 3]

    def test_second_empty(self):
        """Test when second input is an empty list"""
        assert merge_optional_list([1, 2, 3], []) == [1, 2, 3]

    def test_both_non_empty(self):
        """Test when both inputs are non-empty lists"""
        assert merge_optional_list([1, 2], [3, 4]) == [1, 2, 3, 4]


class TestMergeCoordinateSystems:
    """Tests for merge_coordinate_systems"""

    def setup_method(self):
        """Set up test cases"""
        self.CSA = BREGMA_ARI
        self.CSB = MPM_MANIP_RFB

    def test_both_none(self):
        """Test when both inputs are None"""

        assert merge_coordinate_systems(None, None) is None

    def test_first_none(self):
        """Test when first input is None"""

        assert merge_coordinate_systems(None, self.CSA) == self.CSA

    def test_second_none(self):
        """Test when second input is None"""

        assert merge_coordinate_systems(self.CSA, None) == self.CSA

    def test_both_same(self):
        """Test when both inputs are the same"""

        assert merge_coordinate_systems(self.CSA, self.CSA) == self.CSA

    def test_both_different(self):
        """Test when both inputs are different"""

        with pytest.raises(ValueError):
            merge_coordinate_systems(self.CSA, self.CSB)


class TestMergeProcessGraph:
    """Tests for merge_process_graph"""

    def test_both_graphs_present(self):
        """Test merging when both graphs are present"""
        graph1 = {"proc1": ["proc2"], "proc2": []}
        graph2 = {"proc3": ["proc4"], "proc4": []}
        result = merge_process_graph(graph1, graph2, [], [])
        assert result == {"proc1": ["proc2"], "proc2": [], "proc3": ["proc4"], "proc4": []}

    def test_only_first_graph(self):
        """Test when only first graph is present"""
        graph1 = {"proc1": ["proc2"], "proc2": []}
        proc = Mock()
        proc.name = "proc3"
        result = merge_process_graph(graph1, None, [], [proc])
        assert result == {"proc1": ["proc2"], "proc2": [], "proc3": []}

    def test_only_second_graph(self):
        """Test when only second graph is present"""
        graph2 = {"proc3": ["proc4"], "proc4": []}
        proc = Mock()
        proc.name = "proc1"
        result = merge_process_graph(None, graph2, [proc], [])
        assert result == {"proc3": ["proc4"], "proc4": [], "proc1": []}

    def test_both_graphs_none(self):
        """Test when both graphs are None"""
        result = merge_process_graph(None, None, [], [])
        assert result is None
