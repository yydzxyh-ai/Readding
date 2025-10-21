import json
import tempfile
from pathlib import Path
from ai_lab.summarize import extract_json_from_text, validate_and_fix_summary
from ai_lab.models import Summary


def test_extract_json_from_text():
    """Test JSON extraction from various text formats."""
    # Test direct JSON
    json_text = '{"title": "Test", "tl_dr": "Test summary"}'
    result = extract_json_from_text(json_text)
    assert result["title"] == "Test"
    assert result["tl_dr"] == "Test summary"
    
    # Test markdown JSON
    markdown_text = '```json\n{"title": "Markdown Test", "tl_dr": "Markdown summary"}\n```'
    result = extract_json_from_text(markdown_text)
    assert result["title"] == "Markdown Test"
    assert result["tl_dr"] == "Markdown summary"
    
    # Test invalid JSON fallback
    invalid_text = "This is not JSON at all"
    result = extract_json_from_text(invalid_text)
    assert result["title"] == "Failed to parse"
    assert result["tl_dr"] == "JSON parsing failed"


def test_validate_and_fix_summary():
    """Test summary validation and fixing."""
    # Test with missing fields
    incomplete_data = {"title": "Test Paper"}
    source_path = "/test/path.txt"
    result = validate_and_fix_summary(incomplete_data, source_path)
    
    # Check all required fields are present
    assert result["title"] == "Test Paper"
    assert result["tl_dr"] == "No summary available"
    assert result["contributions"] == []
    assert result["methods"] == []
    assert result["results"] == []
    assert result["limitations"] == []
    assert result["tags"] == []
    assert result["quotes"] == []
    assert result["references"] == []
    assert result["authors"] == []
    assert result["source_path"] == source_path
    
    # Test with invalid quote format
    data_with_quotes = {
        "title": "Test",
        "quotes": ["Simple string quote", {"text": "Dict quote", "span": "page 1"}]
    }
    result = validate_and_fix_summary(data_with_quotes, source_path)
    assert len(result["quotes"]) == 2
    assert result["quotes"][0]["text"] == "Simple string quote"
    assert result["quotes"][0]["span"] is None
    assert result["quotes"][1]["text"] == "Dict quote"
    assert result["quotes"][1]["span"] == "page 1"


def test_summary_model_validation():
    """Test that our validation produces valid Summary objects."""
    test_data = {
        "title": "Test Research Paper",
        "authors": ["John Doe", "Jane Smith"],
        "year": 2024,
        "venue": "Test Conference",
        "tl_dr": "This is a test paper about AI research.",
        "contributions": ["Novel algorithm", "Better performance"],
        "methods": ["Deep learning", "Neural networks"],
        "results": ["95% accuracy", "Faster training"],
        "limitations": ["Limited dataset", "High computational cost"],
        "tags": ["AI", "machine learning", "research"],
        "quotes": [
            {"text": "Our method achieves state-of-the-art results.", "span": "page 3"}
        ],
        "references": ["Smith et al. 2023", "Doe et al. 2022"],
        "source_path": "/test/path.txt"
    }
    
    # This should not raise an exception
    summary = Summary(**test_data)
    assert summary.title == "Test Research Paper"
    assert len(summary.contributions) == 2
    assert len(summary.quotes) == 1
    assert summary.quotes[0].text == "Our method achieves state-of-the-art results."
