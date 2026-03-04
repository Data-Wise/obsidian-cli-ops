"""Tests for AI shared structured output models."""

import json
import pytest
from ai.models import AnalysisResult, ComparisonResult, SimilarNote


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
