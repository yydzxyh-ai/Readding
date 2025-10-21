import json
import tempfile
from pathlib import Path
from ai_lab.aggregate import merge_json_summaries, render_markdown_digest
from ai_lab.utils import calculate_coverage_metrics, evaluate_summary_quality


def test_merge_json_summaries_snapshot():
    """Snapshot test for merge_json_summaries function."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create consistent test data
        test_summaries = [
            {
                "title": "Test Paper 1",
                "authors": ["John Doe", "Jane Smith"],
                "year": 2024,
                "venue": "Test Conference",
                "tl_dr": "This is a test paper about machine learning and AI research.",
                "contributions": [
                    "Novel machine learning algorithm",
                    "Improved performance on benchmark datasets",
                    "New theoretical framework"
                ],
                "methods": [
                    "Deep neural networks",
                    "Gradient descent optimization",
                    "Cross-validation"
                ],
                "results": [
                    "95% accuracy on test set",
                    "Faster training time",
                    "Better generalization"
                ],
                "limitations": [
                    "Requires large dataset",
                    "High computational cost"
                ],
                "tags": ["AI", "machine learning", "deep learning"],
                "quotes": [
                    {"text": "Our method achieves state-of-the-art results", "span": "page 3"}
                ],
                "references": ["Smith et al. 2023", "Doe et al. 2022"],
                "source_path": "/test/path1.pdf"
            },
            {
                "title": "Test Paper 2",
                "authors": ["Alice Johnson"],
                "year": 2023,
                "venue": "Another Conference",
                "tl_dr": "This paper presents a new approach to natural language processing.",
                "contributions": [
                    "New NLP architecture",
                    "Better language understanding"
                ],
                "methods": [
                    "Transformer models",
                    "Attention mechanisms"
                ],
                "results": [
                    "90% accuracy on NLP tasks",
                    "Improved efficiency"
                ],
                "limitations": [
                    "Limited to English language",
                    "Requires pre-trained models"
                ],
                "tags": ["NLP", "transformer", "language processing"],
                "quotes": [
                    {"text": "Our approach shows significant improvements", "span": "abstract"}
                ],
                "references": ["Johnson et al. 2023"],
                "source_path": "/test/path2.pdf"
            }
        ]
        
        # Write JSON files
        for i, summary in enumerate(test_summaries):
            json_path = temp_path / f"summary_{i+1}.json"
            json_path.write_text(json.dumps(summary, indent=2), encoding='utf-8')
        
        # Test merge function
        pattern = str(temp_path / "*.json")
        result = merge_json_summaries(pattern)
        
        # Verify structure and content
        assert len(result) == 2
        
        # Check that metadata is added
        for item in result:
            assert '_file' in item
            assert '_filename' in item
            assert '_processed_at' in item
        
        # Check that original content is preserved
        titles = [item['title'] for item in result]
        assert "Test Paper 1" in titles
        assert "Test Paper 2" in titles
        
        # Verify specific fields
        paper1 = next(item for item in result if item['title'] == "Test Paper 1")
        assert paper1['authors'] == ["John Doe", "Jane Smith"]
        assert paper1['year'] == 2024
        assert len(paper1['contributions']) == 3
        assert len(paper1['tags']) == 3
        assert paper1['tags'] == ["AI", "machine learning", "deep learning"]
        
        paper2 = next(item for item in result if item['title'] == "Test Paper 2")
        assert paper2['authors'] == ["Alice Johnson"]
        assert paper2['year'] == 2023
        assert len(paper2['contributions']) == 2
        assert paper2['tags'] == ["NLP", "transformer", "language processing"]


def test_render_markdown_digest_snapshot():
    """Snapshot test for render_markdown_digest function."""
    test_summaries = [
        {
            "title": "Snapshot Test Paper",
            "authors": ["Test Author"],
            "year": 2024,
            "venue": "Test Venue",
            "tl_dr": "This is a snapshot test paper for consistent output verification.",
            "contributions": ["Test contribution 1", "Test contribution 2"],
            "methods": ["Test method 1", "Test method 2"],
            "results": ["Test result 1", "Test result 2"],
            "limitations": ["Test limitation 1"],
            "tags": ["test", "snapshot"],
            "quotes": [
                {"text": "This is a test quote", "span": "page 1"}
            ],
            "source_path": "/test/snapshot.pdf"
        }
    ]
    
    # Generate markdown
    md = render_markdown_digest(test_summaries)
    
    # Verify structure
    assert "# Weekly Digest —" in md
    assert "## 📋 Table of Contents" in md
    assert "## test" in md  # First tag becomes section
    assert "### Snapshot Test Paper" in md
    assert "**TL;DR**: This is a snapshot test paper" in md
    assert "**Contributions**: Test contribution 1; Test contribution 2" in md
    assert "**Methods**: Test method 1; Test method 2" in md
    assert "**Results**: Test result 1; Test result 2" in md
    assert "**Limitations**: Test limitation 1" in md
    assert "**Tags**: `test`, `snapshot`" in md
    assert "**Source**: `snapshot.pdf`" in md
    assert "*Generated on" in md


def test_coverage_metrics_snapshot():
    """Snapshot test for coverage metrics calculation."""
    test_summaries = [
        {
            "title": "Complete Paper",
            "tl_dr": "Complete test paper",
            "contributions": ["contribution 1", "contribution 2"],
            "methods": ["method 1", "method 2", "method 3"],
            "results": ["result 1", "result 2"],
            "limitations": ["limitation 1"],
            "tags": ["AI", "ML"]
        },
        {
            "title": "Partial Paper",
            "tl_dr": "Partial test paper",
            "contributions": ["contribution 3"],
            "methods": ["method 4"],
            "results": [],
            "limitations": ["limitation 2", "limitation 3"],
            "tags": ["AI", "NLP"]
        }
    ]
    
    metrics = calculate_coverage_metrics(test_summaries)
    
    # Verify metrics structure
    expected_keys = [
        'field_completeness', 'content_diversity', 'tag_coverage',
        'average_contributions', 'average_methods', 'average_results',
        'average_limitations'
    ]
    
    for key in expected_keys:
        assert key in metrics
        assert isinstance(metrics[key], float)
        assert 0.0 <= metrics[key] <= 1.0 or key.startswith('average_')
    
    # Verify specific values
    assert metrics['average_contributions'] == 1.5  # (2 + 1) / 2
    assert metrics['average_methods'] == 2.0  # (3 + 1) / 2
    assert metrics['average_results'] == 1.0  # (2 + 0) / 2
    assert metrics['average_limitations'] == 1.5  # (1 + 2) / 2
    
    # Field completeness should be high since most fields are present
    assert metrics['field_completeness'] > 0.8


def test_evaluate_summary_quality_snapshot():
    """Snapshot test for individual summary quality evaluation."""
    test_summary = {
        "title": "Quality Test Paper",
        "tl_dr": "This paper presents a new machine learning approach for natural language processing tasks.",
        "contributions": ["Novel architecture", "Better performance"],
        "methods": ["Deep learning", "Attention mechanism"],
        "results": ["95% accuracy", "Faster training"],
        "limitations": ["High computational cost"],
        "tags": ["ML", "NLP"],
        "quotes": [{"text": "Our method works well", "span": "page 1"}]
    }
    
    source_text = "This paper presents a novel machine learning approach for natural language processing. The method uses deep learning and attention mechanisms to achieve better performance on various NLP tasks."
    
    metrics = evaluate_summary_quality(test_summary, source_text)
    
    # Verify metrics structure
    expected_keys = [
        'faithfulness', 'completeness', 'contributions_count', 'methods_count',
        'results_count', 'limitations_count', 'quotes_count', 'tags_count',
        'content_richness'
    ]
    
    for key in expected_keys:
        assert key in metrics
        assert isinstance(metrics[key], (int, float))
    
    # Verify specific values
    assert metrics['contributions_count'] == 2
    assert metrics['methods_count'] == 2
    assert metrics['results_count'] == 2
    assert metrics['limitations_count'] == 1
    assert metrics['quotes_count'] == 1
    assert metrics['tags_count'] == 2
    
    # Completeness should be 1.0 since all required fields are present
    assert metrics['completeness'] == 1.0
    
    # Faithfulness should be > 0 since there's word overlap
    assert metrics['faithfulness'] > 0.0
    
    # Content richness should be reasonable
    assert 0.0 <= metrics['content_richness'] <= 1.0


def test_empty_inputs_snapshot():
    """Snapshot test for edge cases with empty inputs."""
    # Test empty summaries list
    coverage_metrics = calculate_coverage_metrics([])
    assert coverage_metrics['field_completeness'] == 0.0
    assert coverage_metrics['content_diversity'] == 0.0
    assert coverage_metrics['tag_coverage'] == 0.0
    
    # Test empty summary
    empty_summary = {}
    quality_metrics = evaluate_summary_quality(empty_summary)
    assert quality_metrics['completeness'] == 0.0
    assert quality_metrics['contributions_count'] == 0
    assert quality_metrics['content_richness'] == 0.0
    
    # Test faithfulness with empty inputs
    from ai_lab.utils import faithfulness_proxy
    assert faithfulness_proxy("", "") == 0.0
    assert faithfulness_proxy("some text", "") == 0.0
    assert faithfulness_proxy("", "some text") == 0.0
