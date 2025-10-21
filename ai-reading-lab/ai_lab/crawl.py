"""
CLI tool for crawling papers from arXiv and DOI sources.
"""

from __future__ import annotations
import argparse
import json
from pathlib import Path
from .crawler import PaperCrawler, crawl_papers_from_file

def main():
    ap = argparse.ArgumentParser(description='Crawl papers from arXiv and DOI sources.')
    ap.add_argument('--identifiers', nargs='+', help='List of arXiv IDs or DOIs')
    ap.add_argument('--file', help='File containing identifiers (one per line)')
    ap.add_argument('--output', '-o', default='data', help='Output directory for downloaded files')
    ap.add_argument('--delay', type=float, default=1.0, help='Delay between requests (seconds)')
    ap.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    args = ap.parse_args()
    
    if not args.identifiers and not args.file:
        ap.error("Must provide either --identifiers or --file")
    
    # Collect identifiers
    identifiers = []
    if args.identifiers:
        identifiers.extend(args.identifiers)
    if args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            ap.error(f"File not found: {file_path}")
        identifiers.extend(crawl_papers_from_file(file_path, Path(args.output)))
    
    if not identifiers:
        print("No identifiers provided")
        return
    
    # Create crawler
    crawler = PaperCrawler(Path(args.output), delay=args.delay)
    
    # Crawl papers
    print(f"Crawling {len(identifiers)} papers...")
    results = crawler.crawl_papers(identifiers)
    
    # Save results
    results_file = Path(args.output) / 'crawl_results.json'
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"Successfully crawled {len(results)} papers")
    print(f"Results saved to: {results_file}")
    
    if args.verbose:
        for result in results:
            print(f"- {result.get('title', 'Unknown')} ({result.get('source', 'unknown')})")

if __name__ == '__main__':
    main()
