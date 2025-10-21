"""
arXiv and DOI crawler for fetching PDFs and metadata.

This module provides functionality to download papers from arXiv and DOI sources,
respecting usage terms and rate limits. It includes metadata extraction and
proper citation information.
"""

from __future__ import annotations
import json
import logging
import re
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

class PaperCrawler:
    """Crawler for fetching papers from arXiv and DOI sources."""
    
    def __init__(self, download_dir: Path, delay: float = 1.0):
        """
        Initialize the crawler.
        
        Args:
            download_dir: Directory to save downloaded files
            delay: Delay between requests in seconds
        """
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.delay = delay
        
        # Setup session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set user agent to identify our crawler
        self.session.headers.update({
            'User-Agent': 'AI-Reading-Lab/1.0 (https://github.com/your-repo/ai-reading-lab)'
        })
    
    def _rate_limit(self):
        """Apply rate limiting between requests."""
        if self.delay > 0:
            time.sleep(self.delay)
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for filesystem compatibility."""
        # Remove or replace invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # Limit length
        if len(filename) > 200:
            filename = filename[:200]
        return filename.strip()
    
    def fetch_arxiv_paper(self, arxiv_id: str) -> Optional[Dict]:
        """
        Fetch a paper from arXiv.
        
        Args:
            arxiv_id: arXiv identifier (e.g., '1912.07753' or '1912.07753v1')
            
        Returns:
            Dictionary with paper metadata and local file path, or None if failed
        """
        try:
            # Clean arXiv ID
            arxiv_id = arxiv_id.replace('arXiv:', '').replace('arxiv:', '')
            if not re.match(r'^\d{4}\.\d{4,5}(v\d+)?$', arxiv_id):
                logger.error(f"Invalid arXiv ID format: {arxiv_id}")
                return None
            
            logger.info(f"Fetching arXiv paper: {arxiv_id}")
            
            # Fetch metadata
            metadata_url = f"http://export.arxiv.org/api/query?id_list={arxiv_id}"
            self._rate_limit()
            
            response = self.session.get(metadata_url, timeout=30)
            response.raise_for_status()
            
            # Parse metadata (simplified XML parsing)
            content = response.text
            metadata = self._parse_arxiv_metadata(content)
            
            if not metadata:
                logger.error(f"Failed to parse metadata for {arxiv_id}")
                return None
            
            # Download PDF
            pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
            pdf_filename = self._sanitize_filename(f"{arxiv_id}_{metadata.get('title', 'paper')}.pdf")
            pdf_path = self.download_dir / pdf_filename
            
            if pdf_path.exists():
                logger.info(f"PDF already exists: {pdf_path}")
            else:
                self._rate_limit()
                pdf_response = self.session.get(pdf_url, timeout=60)
                pdf_response.raise_for_status()
                
                with open(pdf_path, 'wb') as f:
                    f.write(pdf_response.content)
                
                logger.info(f"Downloaded PDF: {pdf_path}")
            
            # Add local file path to metadata
            metadata['local_file'] = str(pdf_path)
            metadata['source'] = 'arxiv'
            metadata['arxiv_id'] = arxiv_id
            
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to fetch arXiv paper {arxiv_id}: {e}")
            return None
    
    def _parse_arxiv_metadata(self, xml_content: str) -> Optional[Dict]:
        """Parse arXiv API XML response."""
        try:
            import xml.etree.ElementTree as ET
            
            root = ET.fromstring(xml_content)
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            
            entry = root.find('atom:entry', ns)
            if entry is None:
                return None
            
            # Extract metadata
            title = entry.find('atom:title', ns)
            title = title.text.strip() if title is not None else "Unknown Title"
            
            summary = entry.find('atom:summary', ns)
            summary = summary.text.strip() if summary is not None else ""
            
            # Extract authors
            authors = []
            for author in entry.findall('atom:author', ns):
                name = author.find('atom:name', ns)
                if name is not None:
                    authors.append(name.text.strip())
            
            # Extract publication date
            published = entry.find('atom:published', ns)
            published = published.text if published is not None else ""
            
            # Extract categories
            categories = []
            for category in entry.findall('atom:category', ns):
                term = category.get('term')
                if term:
                    categories.append(term)
            
            return {
                'title': title,
                'authors': authors,
                'abstract': summary,
                'published': published,
                'categories': categories,
                'venue': 'arXiv'
            }
            
        except Exception as e:
            logger.error(f"Failed to parse arXiv metadata: {e}")
            return None
    
    def fetch_doi_paper(self, doi: str) -> Optional[Dict]:
        """
        Fetch a paper using DOI.
        
        Args:
            doi: DOI identifier (e.g., '10.1038/nature12373')
            
        Returns:
            Dictionary with paper metadata and local file path, or None if failed
        """
        try:
            # Clean DOI
            doi = doi.replace('https://doi.org/', '').replace('http://dx.doi.org/', '')
            
            logger.info(f"Fetching DOI paper: {doi}")
            
            # Try to get metadata from CrossRef
            metadata = self._fetch_crossref_metadata(doi)
            
            if not metadata:
                logger.warning(f"Could not fetch metadata for DOI: {doi}")
                metadata = {'title': f'DOI: {doi}', 'authors': [], 'venue': 'Unknown'}
            
            # Try to find and download PDF
            pdf_path = self._download_doi_pdf(doi, metadata.get('title', 'paper'))
            
            if pdf_path:
                metadata['local_file'] = str(pdf_path)
                metadata['source'] = 'doi'
                metadata['doi'] = doi
                return metadata
            else:
                logger.warning(f"Could not download PDF for DOI: {doi}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to fetch DOI paper {doi}: {e}")
            return None
    
    def _fetch_crossref_metadata(self, doi: str) -> Optional[Dict]:
        """Fetch metadata from CrossRef API."""
        try:
            url = f"https://api.crossref.org/works/{doi}"
            self._rate_limit()
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            work = data.get('message', {})
            
            # Extract metadata
            title = work.get('title', ['Unknown Title'])[0]
            
            authors = []
            for author in work.get('author', []):
                given = author.get('given', '')
                family = author.get('family', '')
                if given or family:
                    authors.append(f"{given} {family}".strip())
            
            venue = work.get('container-title', ['Unknown'])[0]
            published = work.get('published-print', work.get('published-online', {}))
            year = published.get('date-parts', [[None]])[0][0] if published else None
            
            return {
                'title': title,
                'authors': authors,
                'venue': venue,
                'year': year,
                'doi': doi
            }
            
        except Exception as e:
            logger.error(f"Failed to fetch CrossRef metadata: {e}")
            return None
    
    def _download_doi_pdf(self, doi: str, title: str) -> Optional[Path]:
        """Attempt to download PDF for a DOI."""
        try:
            # Try common PDF URLs
            pdf_urls = [
                f"https://doi.org/{doi}",
                f"https://dx.doi.org/{doi}",
            ]
            
            for url in pdf_urls:
                try:
                    self._rate_limit()
                    response = self.session.get(url, timeout=30, allow_redirects=True)
                    
                    # Check if response is a PDF
                    if 'application/pdf' in response.headers.get('content-type', ''):
                        filename = self._sanitize_filename(f"{doi}_{title}.pdf")
                        pdf_path = self.download_dir / filename
                        
                        with open(pdf_path, 'wb') as f:
                            f.write(response.content)
                        
                        logger.info(f"Downloaded PDF: {pdf_path}")
                        return pdf_path
                    
                except Exception as e:
                    logger.debug(f"Failed to download from {url}: {e}")
                    continue
            
            logger.warning(f"Could not find downloadable PDF for DOI: {doi}")
            return None
            
        except Exception as e:
            logger.error(f"Error downloading DOI PDF: {e}")
            return None
    
    def crawl_papers(self, identifiers: List[str]) -> List[Dict]:
        """
        Crawl multiple papers by their identifiers.
        
        Args:
            identifiers: List of arXiv IDs or DOIs
            
        Returns:
            List of successfully fetched paper metadata
        """
        results = []
        
        for identifier in identifiers:
            identifier = identifier.strip()
            if not identifier:
                continue
            
            try:
                # Determine if it's arXiv or DOI
                if re.match(r'^\d{4}\.\d{4,5}(v\d+)?$', identifier.replace('arXiv:', '').replace('arxiv:', '')):
                    result = self.fetch_arxiv_paper(identifier)
                elif identifier.startswith('10.') or 'doi.org' in identifier:
                    result = self.fetch_doi_paper(identifier)
                else:
                    logger.warning(f"Unknown identifier format: {identifier}")
                    continue
                
                if result:
                    results.append(result)
                    logger.info(f"Successfully fetched: {result.get('title', 'Unknown')}")
                else:
                    logger.warning(f"Failed to fetch: {identifier}")
                    
            except Exception as e:
                logger.error(f"Error processing {identifier}: {e}")
                continue
        
        logger.info(f"Crawled {len(results)} papers successfully")
        return results

def crawl_papers_from_file(identifiers_file: Path, download_dir: Path) -> List[Dict]:
    """
    Crawl papers from a file containing identifiers.
    
    Args:
        identifiers_file: Path to file containing arXiv IDs or DOIs (one per line)
        download_dir: Directory to save downloaded files
        
    Returns:
        List of successfully fetched paper metadata
    """
    try:
        with open(identifiers_file, 'r', encoding='utf-8') as f:
            identifiers = [line.strip() for line in f if line.strip()]
        
        crawler = PaperCrawler(download_dir)
        return crawler.crawl_papers(identifiers)
        
    except Exception as e:
        logger.error(f"Failed to crawl papers from file: {e}")
        return []
