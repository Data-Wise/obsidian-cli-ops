"""Tests for AI shared structured output models."""

import json
import pytest
from ai.models import (
    AnalysisResult, ComparisonResult, SimilarNote,
    MergeCandidate, TagSuggestion, NoteQuality,
)


class TestAnalysisResult:
    """Tests for AnalysisResult dataclass."""

    def test_from_json_complete(self):
        data = {
            "summary": "A note about testing",
            "themes": ["testing", "quality"],
            "quality_score": 0.85,
            "suggestions": ["Add more examples"],
            "connections": ["CI/CD", "TDD"],
        }
        result = AnalysisResult.from_json(json.dumps(data))
        assert result.summary == "A note about testing"
        assert result.themes == ["testing", "quality"]
        assert result.quality_score == 0.85
        assert result.suggestions == ["Add more examples"]
        assert result.connections == ["CI/CD", "TDD"]

    def test_from_json_missing_fields(self):
        result = AnalysisResult.from_json('{"summary": "Just a summary"}')
        assert result.summary == "Just a summary"
        assert result.themes == []
        assert result.quality_score == 0.0
        assert result.suggestions == []
        assert result.connections == []

    def test_from_json_extra_fields_ignored(self):
        data = {
            "summary": "Test",
            "unknown_field": "should be ignored",
            "another_extra": 42,
        }
        result = AnalysisResult.from_json(json.dumps(data))
        assert result.summary == "Test"
        assert not hasattr(result, "unknown_field")

    def test_from_json_quality_score_clamped_high(self):
        result = AnalysisResult.from_json('{"quality_score": 1.5}')
        assert result.quality_score == 1.0

    def test_from_json_quality_score_clamped_low(self):
        result = AnalysisResult.from_json('{"quality_score": -0.3}')
        assert result.quality_score == 0.0

    def test_from_json_quality_score_invalid_type(self):
        result = AnalysisResult.from_json('{"quality_score": "not a number"}')
        assert result.quality_score == 0.0

    def test_from_json_empty_object(self):
        result = AnalysisResult.from_json('{}')
        assert result.summary == ""
        assert result.themes == []

    def test_from_json_invalid_json_raises(self):
        with pytest.raises(json.JSONDecodeError):
            AnalysisResult.from_json("not json at all")

    def test_from_json_non_object_raises(self):
        with pytest.raises(ValueError, match="Expected JSON object"):
            AnalysisResult.from_json('[1, 2, 3]')

    def test_to_dict(self):
        result = AnalysisResult(
            summary="Test",
            themes=["a"],
            quality_score=0.7,
            suggestions=["do this"],
            connections=["that"],
        )
        d = result.to_dict()
        assert d["summary"] == "Test"
        assert d["themes"] == ["a"]
        assert d["quality_score"] == 0.7


class TestComparisonResult:
    """Tests for ComparisonResult dataclass."""

    def test_from_json_complete(self):
        data = {
            "similarity_score": 0.75,
            "common_themes": ["python", "testing"],
            "differences": ["scope differs"],
            "relationship": "complementary",
        }
        result = ComparisonResult.from_json(json.dumps(data))
        assert result.similarity_score == 0.75
        assert result.common_themes == ["python", "testing"]
        assert result.differences == ["scope differs"]
        assert result.relationship == "complementary"

    def test_from_json_similarity_clamped(self):
        result = ComparisonResult.from_json('{"similarity_score": 2.0}')
        assert result.similarity_score == 1.0

    def test_from_json_extra_fields_ignored(self):
        data = {"similarity_score": 0.5, "should_merge": True}
        result = ComparisonResult.from_json(json.dumps(data))
        assert result.similarity_score == 0.5
        assert not hasattr(result, "should_merge")

    def test_from_json_empty_object(self):
        result = ComparisonResult.from_json('{}')
        assert result.similarity_score == 0.0
        assert result.common_themes == []
        assert result.relationship == ""

    def test_to_dict(self):
        result = ComparisonResult(similarity_score=0.8, relationship="related")
        d = result.to_dict()
        assert d["similarity_score"] == 0.8
        assert d["relationship"] == "related"


class TestSimilarNote:
    """Tests for SimilarNote dataclass."""

    def test_from_json_complete(self):
        data = {
            "note_id": 42,
            "title": "My Note",
            "similarity": 0.92,
            "reason": "Both about Python",
        }
        result = SimilarNote.from_json(json.dumps(data))
        assert result.note_id == 42
        assert result.title == "My Note"
        assert result.similarity == 0.92
        assert result.reason == "Both about Python"

    def test_from_json_minimal(self):
        result = SimilarNote.from_json('{"note_id": 1, "title": "X"}')
        assert result.note_id == 1
        assert result.title == "X"
        assert result.similarity == 0.0
        assert result.reason is None

    def test_from_json_extra_fields_ignored(self):
        data = {"note_id": 1, "title": "X", "path": "/should/be/ignored"}
        result = SimilarNote.from_json(json.dumps(data))
        assert not hasattr(result, "path")

    def test_to_dict(self):
        result = SimilarNote(note_id=5, title="Test", similarity=0.8, reason="similar")
        d = result.to_dict()
        assert d["note_id"] == 5
        assert d["reason"] == "similar"


# ── v3.2.0 Model Tests ───────────────────────────────────────────


class TestMergeCandidate:
    """Tests for MergeCandidate dataclass."""

    def test_from_dict_complete(self):
        data = {
            "note_a_id": "abc",
            "note_b_id": "def",
            "note_a_title": "Note A",
            "note_b_title": "Note B",
            "similarity": 0.92,
            "shared_links": ["Link1"],
            "shared_tags": ["tag1"],
            "overlapping_sections": [],
            "suggested_target": "Note A",
            "confidence": 0.85,
        }
        mc = MergeCandidate.from_dict(data)
        assert mc.note_a_id == "abc"
        assert mc.similarity == 0.92
        assert mc.confidence == 0.85
        assert mc.shared_tags == ["tag1"]

    def test_from_dict_clamps_similarity(self):
        mc = MergeCandidate.from_dict({"similarity": 1.5, "confidence": -0.3})
        assert mc.similarity == 1.0
        assert mc.confidence == 0.0

    def test_from_json_ignores_extra_keys(self):
        data = {"note_a_id": "x", "unknown_field": True}
        mc = MergeCandidate.from_json(json.dumps(data))
        assert mc.note_a_id == "x"
        assert not hasattr(mc, "unknown_field")

    def test_to_dict_round_trip(self):
        mc = MergeCandidate(note_a_id="a", note_b_id="b",
                            note_a_title="A", note_b_title="B",
                            similarity=0.9, confidence=0.8)
        d = mc.to_dict()
        mc2 = MergeCandidate.from_dict(d)
        assert mc2.similarity == mc.similarity
        assert mc2.note_a_title == mc.note_a_title


class TestTagSuggestion:
    """Tests for TagSuggestion dataclass."""

    def test_from_dict_with_tags(self):
        data = {
            "note_id": "n1",
            "note_title": "My Note",
            "suggested_tags": [
                {"tag": "python", "confidence": 0.9, "vault_usage_count": 5},
                {"tag": "testing", "confidence": 0.7, "vault_usage_count": 3},
            ],
            "existing_tags": [],
            "neighbor_tags": ["dev"],
        }
        ts = TagSuggestion.from_dict(data)
        assert len(ts.suggested_tags) == 2
        assert ts.suggested_tags[0]["tag"] == "python"
        assert ts.suggested_tags[0]["confidence"] == 0.9

    def test_from_dict_clamps_tag_confidence(self):
        data = {
            "suggested_tags": [{"tag": "x", "confidence": 1.5}],
        }
        ts = TagSuggestion.from_dict(data)
        assert ts.suggested_tags[0]["confidence"] == 1.0

    def test_from_json_minimal(self):
        ts = TagSuggestion.from_json('{"note_id": "n1"}')
        assert ts.note_id == "n1"
        assert ts.suggested_tags == []

    def test_to_dict(self):
        ts = TagSuggestion(note_id="n1", note_title="T",
                          suggested_tags=[{"tag": "a", "confidence": 0.8}])
        d = ts.to_dict()
        assert d["note_id"] == "n1"
        assert len(d["suggested_tags"]) == 1


class TestNoteQuality:
    """Tests for NoteQuality dataclass."""

    def test_from_dict_complete(self):
        data = {
            "note_id": "n1",
            "note_title": "Note 1",
            "overall_score": 72.5,
            "dimensions": {
                "completeness": 80.0,
                "connectivity": 60.0,
                "metadata": 100.0,
                "freshness": 50.0,
            },
            "issues": [{"severity": "high", "description": "orphan"}],
            "suggestions": ["Add links"],
        }
        nq = NoteQuality.from_dict(data)
        assert nq.overall_score == 72.5
        assert nq.dimensions["completeness"] == 80.0
        assert len(nq.issues) == 1

    def test_from_dict_clamps_overall_score(self):
        nq = NoteQuality.from_dict({"overall_score": 150.0})
        assert nq.overall_score == 100.0
        nq2 = NoteQuality.from_dict({"overall_score": -10.0})
        assert nq2.overall_score == 0.0

    def test_from_dict_clamps_dimension_scores(self):
        nq = NoteQuality.from_dict({"dimensions": {"completeness": 200.0, "connectivity": -5.0}})
        assert nq.dimensions["completeness"] == 100.0
        assert nq.dimensions["connectivity"] == 0.0

    def test_from_json_empty(self):
        nq = NoteQuality.from_json('{}')
        assert nq.overall_score == 0.0
        assert nq.dimensions == {}

    def test_to_dict_round_trip(self):
        nq = NoteQuality(note_id="n1", note_title="T", overall_score=55.0,
                         dimensions={"completeness": 60.0, "connectivity": 50.0})
        d = nq.to_dict()
        nq2 = NoteQuality.from_dict(d)
        assert nq2.overall_score == nq.overall_score
        assert nq2.dimensions == nq.dimensions
