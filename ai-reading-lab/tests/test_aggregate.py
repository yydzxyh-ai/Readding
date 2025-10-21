import json
import tempfile
from pathlib import Path
from ai_lab.aggregate import (
    merge_json_summaries, 
    render_markdown_digest, 
    sanitize_anchor, 
    format_list_items
)


def test_sanitize_anchor():
    """Test anchor sanitization for markdown links."""
    assert sanitize_anchor("Machine Learning") == "machine-learning"
    assert sanitize_anchor("AI & NLP") == "ai-nlp"
    assert sanitize_anchor("Deep Learning (2024)") == "deep-learning-2024"
    assert sanitize_anchor("Computer Vision") == "computer-vision"
    assert sanitize_anchor("") == ""


def test_format_list_items():
    """Test list formatting for markdown display."""
    items = ["item1", "item2", "item3", "item4", "item5"]
    
    # Test with max_items = 3
    result = format_list_items(items, 3)
    assert "item1; item2; item3; ... and 2 more" == result
    
    # Test with max_items = 2
    result = format_list_items(items, 2)
    assert "item1; item2; ... and 3 more" == result
    
    # Test with empty list
    result = format_list_items([], 3)
    assert result == ""
    
    # Test with fewer items than max
    result = format_list_items(["item1", "item2"], 3)
    assert result == "item1; item2"


def test_merge_json_summaries():
    """Test merging JSON summary files."""
    # Create temporary JSON files
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create test JSON files
        summary1 = {
            "title": "Test Paper 1",
            "authors": ["John Doe"],
            "year": 2024,
            "tl_dr": "This is a test paper",
            "contributions": ["Novel method", "Better results"],
            "methods": ["Deep learning"],
            "results": ["95% accuracy"],
            "limitations": ["Limited dataset"],
            "tags": ["AI", "machine learning"],
            "source_path": "/test/path1.pdf"
        }
        
        summary2 = {
            "title": "Test Paper 2",
            "authors": ["Jane Smith"],
            "year": 2023,
            "tl_dr": "Another test paper",
            "contributions": ["New algorithm"],
            "methods": ["Neural networks"],
            "results": ["90% accuracy"],
            "limitations": ["High computational cost"],
            "tags": ["NLP", "deep learning"],
            "source_path": "/test/path2.pdf"
        }
        
        # Write JSON files
        json1_path = temp_path / "summary1.json"
        json2_path = temp_path / "summary2.json"
        
        json1_path.write_text(json.dumps(summary1), encoding='utf-8')
        json2_path.write_text(json.dumps(summary2), encoding='utf-8')
        
        # Test merging
        pattern = str(temp_path / "*.json")
        items = merge_json_summaries(pattern)
        
        assert len(items) == 2
        assert all('_file' in item for item in items)
        assert all('_filename' in item for item in items)
        assert all('_processed_at' in item for item in items)
        
        # Check that content is preserved
        titles = [item['title'] for item in items]
        assert "Test Paper 1" in titles
        assert "Test Paper 2" in titles


def test_merge_json_summaries_empty():
    """Test merging with no files."""
    items = merge_json_summaries("nonexistent/*.json")
    assert items == []


def test_merge_json_summaries_invalid():
    """Test merging with invalid JSON files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create invalid JSON file
        invalid_json_path = temp_path / "invalid.json"
        invalid_json_path.write_text("invalid json content", encoding='utf-8')
        
        # Create empty file
        empty_json_path = temp_path / "empty.json"
        empty_json_path.write_text("", encoding='utf-8')
        
        pattern = str(temp_path / "*.json")
        items = merge_json_summaries(pattern)
        
        # Should return empty list due to invalid JSON
        assert items == []


def test_render_markdown_digest_empty():
    """Test rendering with no items."""
    md = render_markdown_digest([])
    assert "# Weekly Digest —" in md
    assert "No summaries available" in md


def test_render_markdown_digest_single_item():
    """Test rendering with a single item."""
    item = {
        "title": "Test Paper",
        "authors": ["John Doe"],
        "year": 2024,
        "venue": "Test Conference",
        "tl_dr": "This is a test paper about AI",
        "contributions": ["Novel method", "Better performance"],
        "methods": ["Deep learning", "Neural networks"],
        "results": ["95% accuracy", "Faster training"],
        "limitations": ["Limited dataset", "High cost"],
        "tags": ["AI", "machine learning"],
        "quotes": [
            {"text": "Our method achieves state-of-the-art results", "span": "page 3"}
        ],
        "source_path": "/test/path.pdf"
    }
    
    md = render_markdown_digest([item])
    
    # Check basic structure
    assert "# Weekly Digest —" in md
    assert "## 📋 Table of Contents" in md
    assert "## AI" in md  # First tag becomes section
    assert "### Test Paper" in md
    assert "**TL;DR**: This is a test paper about AI" in md
    assert "**Contributions**: Novel method; Better performance" in md
    assert "**Methods**: Deep learning; Neural networks" in md
    assert "**Results**: 95% accuracy; Faster training" in md
    assert "**Limitations**: Limited dataset; High cost" in md
    assert "**Source**: `path.pdf`" in md
    assert "**Tags**: `AI`, `machine learning`" in md


def test_render_markdown_digest_multiple_items():
    """Test rendering with multiple items in different categories."""
    items = [
        {
            "title": "AI Paper",
            "authors": ["John Doe"],
            "year": 2024,
            "tl_dr": "AI research paper",
            "contributions": ["Novel AI method"],
            "methods": ["Deep learning"],
            "results": ["95% accuracy"],
            "limitations": ["Limited data"],
            "tags": ["AI", "machine learning"],
            "source_path": "/ai/paper.pdf"
        },
        {
            "title": "NLP Paper",
            "authors": ["Jane Smith"],
            "year": 2023,
            "tl_dr": "NLP research paper",
            "contributions": ["New NLP technique"],
            "methods": ["Transformer"],
            "results": ["90% accuracy"],
            "limitations": ["High cost"],
            "tags": ["NLP", "language processing"],
            "source_path": "/nlp/paper.pdf"
        }
    ]
    
    md = render_markdown_digest(items)
    
    # Check structure
    assert "# Weekly Digest —" in md
    assert "## 📋 Table of Contents" in md
    assert "## AI" in md
    assert "## NLP" in md
    assert "**Summary**: 2 papers across 2 categories" in md
    
    # Check that items are grouped by first tag
    ai_section_start = md.find("## AI")
    nlp_section_start = md.find("## NLP")
    assert ai_section_start < nlp_section_start
    
    # Check content
    assert "### AI Paper" in md
    assert "### NLP Paper" in md


def test_render_markdown_digest_no_tags():
    """Test rendering with items that have no tags."""
    item = {
        "title": "Untagged Paper",
        "tl_dr": "Paper without tags",
        "contributions": ["Some contribution"],
        "tags": [],  # Empty tags
        "source_path": "/test/paper.pdf"
    }
    
    md = render_markdown_digest([item])
    
    # Should default to "General" category
    assert "## General" in md
    assert "### Untagged Paper" in md


def test_render_markdown_digest_quotes():
    """Test rendering with quotes."""
    item = {
        "title": "Paper with Quotes",
        "tl_dr": "Paper with important quotes",
        "contributions": ["Some contribution"],
        "tags": ["Test"],
        "quotes": [
            {"text": "First important quote", "span": "page 1"},
            {"text": "Second important quote", "span": "page 5"},
            {"text": "Third quote that should be truncated", "span": "page 10"}
        ],
        "source_path": "/test/paper.pdf"
    }
    
    md = render_markdown_digest([item])
    
    assert "**Key Quotes**:" in md
    assert '"First important quote" (page 1)' in md
    assert '"Second important quote" (page 5)' in md
    # Third quote should be truncated (only show max 2)
    assert '"Third quote that should be truncated"' not in md
