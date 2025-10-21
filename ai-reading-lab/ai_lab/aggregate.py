from __future__ import annotations
import argparse, glob, json, pathlib, datetime as dt
from typing import List, Dict
from collections import defaultdict
import re

def merge_json_summaries(pattern: str) -> List[Dict]:
    """Load and merge JSON summary files from a glob pattern."""
    items = []
    files_found = list(glob.glob(pattern))
    
    if not files_found:
        print(f"Warning: No files found matching pattern: {pattern}")
        return items
    
    print(f"Found {len(files_found)} JSON files to process...")
    
    for p in files_found:
        try:
            path = pathlib.Path(p)
            if not path.exists():
                print(f"Warning: File does not exist: {p}")
                continue
                
            content = path.read_text(encoding='utf-8')
            if not content.strip():
                print(f"Warning: Empty file: {p}")
                continue
                
            obj = json.loads(content)
            
            # Validate that it has the basic structure we expect
            if not isinstance(obj, dict):
                print(f"Warning: Invalid JSON structure in {p}")
                continue
                
            # Add metadata
            obj['_file'] = str(path)
            obj['_filename'] = path.name
            obj['_processed_at'] = dt.datetime.now().isoformat()
            
            items.append(obj)
            
        except json.JSONDecodeError as e:
            print(f"Warning: Invalid JSON in {p}: {e}")
            continue
        except (FileNotFoundError, PermissionError) as e:
            print(f"Warning: Cannot read {p}: {e}")
            continue
        except (OSError, UnicodeDecodeError) as e:
            print(f"Warning: Unexpected error processing {p}: {e}")
            continue
    
    print(f"Successfully loaded {len(items)} valid JSON summaries")
    return items

def sanitize_anchor(text: str) -> str:
    """Create a valid markdown anchor from text."""
    # Remove special characters and convert to lowercase
    anchor = re.sub(r'[^\w\s-]', '', text.lower())
    # Replace spaces and multiple hyphens with single hyphen
    anchor = re.sub(r'[\s-]+', '-', anchor)
    return anchor.strip('-')

def format_list_items(items: List[str], max_items: int = 3) -> str:
    """Format a list of items for markdown display."""
    if not items:
        return ""
    display_items = items[:max_items]
    if len(items) > max_items:
        display_items.append(f"... and {len(items) - max_items} more")
    return "; ".join(display_items)

def render_markdown_digest(items: List[Dict]) -> str:
    """Render a comprehensive markdown digest from JSON summaries."""
    today = dt.date.today().isoformat()
    title = f"# Weekly Digest — {today}\n"
    
    if not items:
        return title + "\n> No summaries available for this week.\n"
    
    # Group items by their first tag
    groups = defaultdict(list)
    for item in items:
        tags = item.get('tags', [])
        if not tags:
            tags = ['General']
        primary_tag = tags[0]
        groups[primary_tag].append(item)
    
    # Sort groups alphabetically
    sorted_groups = sorted(groups.items())
    
    # Build the markdown content
    lines = [title]
    
    # Add summary statistics
    total_papers = len(items)
    total_groups = len(sorted_groups)
    lines.extend([
        f"**Summary**: {total_papers} papers across {total_groups} categories\n",
        "---\n"
    ])
    
    # Add table of contents
    lines.extend(['## 📋 Table of Contents', ''])
    for tag, group_items in sorted_groups:
        anchor = sanitize_anchor(tag)
        lines.append(f"- [{tag}](#{anchor}) ({len(group_items)} papers)")
    lines.append('')
    
    # Add content sections
    for tag, group_items in sorted_groups:
        anchor = sanitize_anchor(tag)
        lines.extend([
            f"## {tag} {{#{anchor}}}",
            ''
        ])
        
        # Sort items within group by title
        group_items.sort(key=lambda x: x.get('title', '').lower())
        
        for item in group_items:
            # Extract basic info
            title_text = item.get('title', 'Untitled')
            authors = item.get('authors', [])
            year = item.get('year')
            venue = item.get('venue')
            tl_dr = item.get('tl_dr', 'No summary available')
            
            # Build paper header
            paper_title = f"### {title_text}"
            if authors:
                author_str = ", ".join(authors[:3])
                if len(authors) > 3:
                    author_str += " et al."
                paper_title += f" *by {author_str}*"
            if year:
                paper_title += f" ({year})"
            if venue:
                paper_title += f" — {venue}"
            
            lines.extend([
                paper_title,
                ''
            ])
            
            # Add TL;DR
            lines.extend([
                f"**TL;DR**: {tl_dr}",
                ''
            ])
            
            # Add structured content
            contributions = item.get('contributions', [])
            if contributions:
                contrib_text = format_list_items(contributions, 3)
                lines.append(f"**Contributions**: {contrib_text}")
            
            methods = item.get('methods', [])
            if methods:
                methods_text = format_list_items(methods, 3)
                lines.append(f"**Methods**: {methods_text}")
            
            results = item.get('results', [])
            if results:
                results_text = format_list_items(results, 3)
                lines.append(f"**Results**: {results_text}")
            
            limitations = item.get('limitations', [])
            if limitations:
                limits_text = format_list_items(limitations, 2)
                lines.append(f"**Limitations**: {limits_text}")
            
            # Add quotes if available
            quotes = item.get('quotes', [])
            if quotes:
                lines.append("**Key Quotes**:")
                for quote in quotes[:2]:  # Show max 2 quotes
                    if isinstance(quote, dict):
                        quote_text = quote.get('text', '')
                        quote_span = quote.get('span', '')
                        if quote_text:
                            if quote_span:
                                lines.append(f"- \"{quote_text}\" ({quote_span})")
                            else:
                                lines.append(f"- \"{quote_text}\"")
                    elif isinstance(quote, str):
                        lines.append(f"- \"{quote}\"")
            
            # Add tags
            all_tags = item.get('tags', [])
            if all_tags:
                tag_str = ", ".join([f"`{tag}`" for tag in all_tags])
                lines.append(f"**Tags**: {tag_str}")
            
            # Add source information
            source_path = item.get('source_path') or item.get('_file', '')
            if source_path:
                # Make source path more readable
                if source_path.startswith('/'):
                    source_path = pathlib.Path(source_path).name
                lines.extend([
                    '',
                    f"**Source**: `{source_path}`",
                    ''
                ])
            
            lines.append('---\n')
    
    # Add footer
    lines.extend([
        "---",
        f"*Generated on {dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
        f"*Total: {total_papers} papers in {total_groups} categories*"
    ])
    
    return "\n".join(lines)

def main():
    ap = argparse.ArgumentParser(description='Merge JSON summaries into a weekly Markdown digest.')
    ap.add_argument('--json_glob', required=True, help="Glob for JSON summaries e.g. 'summaries/json/*.json'")
    ap.add_argument('--out', required=True, help='Output path for digest markdown')
    ap.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    args = ap.parse_args()
    
    try:
        # Load and merge JSON summaries
        items = merge_json_summaries(args.json_glob)
        
        if not items:
            print("No valid JSON summaries found. Exiting.")
            return
        
        # Generate markdown digest
        if args.verbose:
            print("Generating markdown digest...")
        
        md = render_markdown_digest(items)
        
        # Write output
        output_path = pathlib.Path(args.out)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(md, encoding='utf-8')
        
        print(f"✓ Successfully generated digest: {output_path}")
        print(f"  - {len(items)} papers processed")
        print(f"  - {len(md)} characters written")
        
        if args.verbose:
            # Show some statistics
            total_contributions = sum(len(item.get('contributions', [])) for item in items)
            total_methods = sum(len(item.get('methods', [])) for item in items)
            total_results = sum(len(item.get('results', [])) for item in items)
            total_limitations = sum(len(item.get('limitations', [])) for item in items)
            
            print(f"  - Total contributions: {total_contributions}")
            print(f"  - Total methods: {total_methods}")
            print(f"  - Total results: {total_results}")
            print(f"  - Total limitations: {total_limitations}")
        
    except (OSError, ValueError, TypeError) as e:
        print(f"✗ Error generating digest: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1
    
    return 0

if __name__ == '__main__':
    main()
