from __future__ import annotations
import re
from typing import Dict, List, Any
from collections import Counter
import math

def clean_text(s: str) -> str:
    s = s.replace('\x00', ' ').replace('\u0000', ' ')
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def split_text(text: str, max_chars: int = 6000, overlap: int = 400) -> list[str]:
    words = text.split()
    chunks, cur, cur_len = [], [], 0
    for w in words:
        cur.append(w); cur_len += len(w) + 1
        if cur_len >= max_chars:
            chunk = " ".join(cur)
            chunks.append(chunk)
            if overlap > 0:
                keep = chunk[-overlap:]
                cur, cur_len = [keep], len(keep)
            else:
                cur, cur_len = [], 0
    if cur:
        chunks.append(" ".join(cur))
    return chunks

def faithfulness_proxy(summary: str, context: str) -> float:
    """
    Calculate a proxy measure for faithfulness between summary and context.
    
    This is a simple word overlap metric that serves as a placeholder for more
    sophisticated faithfulness evaluation methods.
    
    Args:
        summary: The generated summary text
        context: The original context/source text
        
    Returns:
        Float between 0.0 and 1.0 indicating faithfulness score
    """
    if not summary or not context:
        return 0.0
    
    # Normalize text: lowercase, remove punctuation, split into words
    summary_words = set(re.findall(r'\b\w+\b', summary.lower()))
    context_words = set(re.findall(r'\b\w+\b', context.lower()))
    
    if not summary_words:
        return 0.0
    
    # Calculate overlap ratio
    overlap = len(summary_words & context_words)
    return overlap / len(summary_words)

def calculate_coverage_metrics(summaries: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Calculate coverage metrics for a collection of summaries.
    
    This provides placeholder metrics for evaluating how well summaries
    cover the key aspects of the source documents.
    
    Args:
        summaries: List of summary dictionaries
        
    Returns:
        Dictionary with coverage metrics
    """
    if not summaries:
        return {
            'field_completeness': 0.0,
            'content_diversity': 0.0,
            'tag_coverage': 0.0,
            'average_contributions': 0.0,
            'average_methods': 0.0,
            'average_results': 0.0,
            'average_limitations': 0.0
        }
    
    # Required fields for completeness
    required_fields = ['title', 'tl_dr', 'contributions', 'methods', 'results', 'limitations']
    
    # Calculate field completeness
    total_fields = len(required_fields) * len(summaries)
    present_fields = 0
    
    for summary in summaries:
        for field in required_fields:
            if field in summary and summary[field]:
                if isinstance(summary[field], list):
                    if len(summary[field]) > 0:
                        present_fields += 1
                else:
                    present_fields += 1
    
    field_completeness = present_fields / total_fields if total_fields > 0 else 0.0
    
    # Calculate content diversity (based on unique tags)
    all_tags = []
    for summary in summaries:
        tags = summary.get('tags', [])
        all_tags.extend(tags)
    
    unique_tags = set(all_tags)
    tag_coverage = len(unique_tags) / len(all_tags) if all_tags else 0.0
    
    # Calculate average content richness
    avg_contributions = sum(len(s.get('contributions', [])) for s in summaries) / len(summaries)
    avg_methods = sum(len(s.get('methods', [])) for s in summaries) / len(summaries)
    avg_results = sum(len(s.get('results', [])) for s in summaries) / len(summaries)
    avg_limitations = sum(len(s.get('limitations', [])) for s in summaries) / len(summaries)
    
    # Calculate content diversity (entropy-based)
    all_content = []
    for summary in summaries:
        content_fields = ['contributions', 'methods', 'results', 'limitations']
        for field in content_fields:
            items = summary.get(field, [])
            all_content.extend([item.lower().strip() for item in items if item])
    
    if all_content:
        content_counter = Counter(all_content)
        total_content = len(all_content)
        entropy = -sum((count / total_content) * math.log2(count / total_content) 
                      for count in content_counter.values())
        max_entropy = math.log2(len(content_counter)) if content_counter else 0
        content_diversity = entropy / max_entropy if max_entropy > 0 else 0.0
    else:
        content_diversity = 0.0
    
    return {
        'field_completeness': field_completeness,
        'content_diversity': content_diversity,
        'tag_coverage': tag_coverage,
        'average_contributions': avg_contributions,
        'average_methods': avg_methods,
        'average_results': avg_results,
        'average_limitations': avg_limitations
    }

def evaluate_summary_quality(summary: Dict[str, Any], source_text: str = "") -> Dict[str, float]:
    """
    Evaluate the quality of a single summary.
    
    Args:
        summary: Summary dictionary
        source_text: Original source text (optional)
        
    Returns:
        Dictionary with quality metrics
    """
    metrics = {}
    
    # Faithfulness (if source text provided)
    if source_text:
        tl_dr = summary.get('tl_dr', '')
        metrics['faithfulness'] = faithfulness_proxy(tl_dr, source_text)
    else:
        metrics['faithfulness'] = 0.0
    
    # Completeness metrics
    required_fields = ['title', 'tl_dr', 'contributions', 'methods', 'results', 'limitations']
    present_fields = sum(1 for field in required_fields 
                        if field in summary and summary[field])
    metrics['completeness'] = present_fields / len(required_fields)
    
    # Content richness
    metrics['contributions_count'] = len(summary.get('contributions', []))
    metrics['methods_count'] = len(summary.get('methods', []))
    metrics['results_count'] = len(summary.get('results', []))
    metrics['limitations_count'] = len(summary.get('limitations', []))
    metrics['quotes_count'] = len(summary.get('quotes', []))
    metrics['tags_count'] = len(summary.get('tags', []))
    
    # Overall richness score
    total_content = (metrics['contributions_count'] + metrics['methods_count'] + 
                    metrics['results_count'] + metrics['limitations_count'])
    metrics['content_richness'] = min(total_content / 10.0, 1.0)  # Normalize to 0-1
    
    return metrics
