"""Advanced scraper for SickKids with sitemap crawling and content filtering."""
import sys
import os
from pathlib import Path

# Add parent directory to path FIRST
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import time
import re
import json
from urllib.parse import urljoin, urlparse, quote_plus
from typing import Set, List, Dict, Any, Optional
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from loguru import logger
from tqdm import tqdm


class AdvancedSickKidsScraper:
    """Advanced scraper for SickKids with filtering and content extraction."""
    
    BASE_URL = "https://www.aboutkidshealth.ca"
    
    # Keywords to filter relevant content
    RELEVANCE_KEYWORDS = [
        # Imaging techniques
        "image guidance", "image guided", "imaging", "radiology",
        "fluoroscopy", "ultrasound", "ct scan", "mri", "x-ray",
        
        # Procedures
        "interventional", "biopsy", "drainage", "catheter",
        "needle", "guidewire", "angiography", "embolization",
        
        # Related terms
        "minimally invasive", "percutaneous", "sedation",
        "anesthesia", "procedure", "intervention"
    ]
    
    def __init__(self, output_dir: str = "KB/SickKids", delay: float = 1.5):
        """
        Initialize advanced scraper.
        
        Args:
            output_dir: Directory to save scraped content
            delay: Delay between requests (be respectful!)
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Educational/Research Bot for Medical Content Curation)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        })
        
        self.visited = set()
        self.saved_count = 0
        
        # Metadata tracking
        self.metadata_file = self.output_dir / "scrape_metadata.json"
        self.metadata = self._load_metadata()
        
        logger.info(f"Initialized advanced SickKids scraper")
        logger.info(f"Output: {self.output_dir}")
    
    def _load_metadata(self) -> Dict:
        """Load existing scrape metadata."""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"scraped_urls": [], "last_scrape": None}
    
    def _save_metadata(self):
        """Save scrape metadata."""
        self.metadata["last_scrape"] = datetime.now().isoformat()
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, indent=2)
    
    def get_sitemap_urls(self) -> List[str]:
        """
        Try to get URLs from sitemap.xml.
        
        Returns:
            List of URLs from sitemap
        """
        sitemap_url = f"{self.BASE_URL}/sitemap.xml"
        
        try:
            logger.info(f"Fetching sitemap: {sitemap_url}")
            response = self.session.get(sitemap_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'xml')
            urls = [loc.text for loc in soup.find_all('loc')]
            
            logger.info(f"Found {len(urls)} URLs in sitemap")
            return urls
            
        except Exception as e:
            logger.warning(f"Could not fetch sitemap: {e}")
            return []
    
    def filter_relevant_urls(self, urls: List[str]) -> List[str]:
        """
        Filter URLs for relevance to image guidance.
        
        Args:
            urls: List of URLs to filter
            
        Returns:
            Filtered list of relevant URLs
        """
        relevant = []
        
        for url in urls:
            url_lower = url.lower()
            
            # Check if URL contains any relevance keywords
            if any(keyword in url_lower for keyword in self.RELEVANCE_KEYWORDS):
                relevant.append(url)
        
        logger.info(f"Filtered to {len(relevant)} relevant URLs from {len(urls)} total")
        return relevant
    
    def check_content_relevance(self, soup: BeautifulSoup) -> bool:
        """
        Check if page content is relevant to image guidance.
        
        Args:
            soup: BeautifulSoup object of page
            
        Returns:
            True if content is relevant
        """
        # Get all text content
        text = soup.get_text().lower()
        
        # Count keyword matches
        matches = sum(1 for keyword in self.RELEVANCE_KEYWORDS if keyword in text)
        
        # Require at least 2 keyword matches
        return matches >= 2
    
    def extract_clean_content(self, soup: BeautifulSoup) -> Optional[BeautifulSoup]:
        """
        Extract main content and remove navigation/ads/etc.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            Cleaned content
        """
        # Remove unwanted elements
        for element in soup.find_all(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            element.decompose()
        
        # Remove ads and social media
        for element in soup.find_all(class_=re.compile(r'(ad|advertisement|social|share|comment)', re.I)):
            element.decompose()
        
        # Try to find main content
        main_content = soup.find('main') or soup.find('article') or soup.find(class_='content')
        
        if not main_content:
            # Fallback: find largest text block
            main_content = soup.find('body')
        
        return main_content
    
    def scrape_url(self, url: str) -> bool:
        """
        Scrape a single URL.
        
        Args:
            url: URL to scrape
            
        Returns:
            True if successfully scraped and saved
        """
        if url in self.visited:
            return False
        
        try:
            # Fetch page
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Check relevance
            if not self.check_content_relevance(soup):
                logger.info(f"Skipping (not relevant): {url}")
                self.visited.add(url)
                return False
            
            # Extract and clean content
            content = self.extract_clean_content(soup)
            
            if not content:
                logger.warning(f"No content extracted from: {url}")
                self.visited.add(url)
                return False
            
            # Extract title
            title_tag = soup.find('title')
            title = title_tag.get_text().strip() if title_tag else "Untitled"
            
            # Save page
            page_data = {
                'url': url,
                'title': title,
                'html': str(content),
                'full_html': str(soup)
            }
            
            filepath = self.save_page(page_data)
            
            # Update metadata
            self.metadata["scraped_urls"].append({
                "url": url,
                "title": title,
                "file": os.path.basename(filepath),
                "scraped_at": datetime.now().isoformat()
            })
            
            self.visited.add(url)
            self.saved_count += 1
            
            return True
            
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            self.visited.add(url)
            return False
    
    def save_page(self, page_data: Dict[str, Any]) -> str:
        """Save page with metadata."""
        title = page_data['title']
        url = page_data['url']
        
        # Create safe filename
        safe_title = re.sub(r'[^\w\s-]', '', title)
        safe_title = re.sub(r'[-\s]+', '_', safe_title)
        safe_title = safe_title[:80]
        
        url_hash = abs(hash(url)) % 10000
        filename = f"sickkids_{safe_title}_{url_hash}.html"
        filepath = self.output_dir / filename
        
        # Create structured HTML
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="source" content="SickKids AboutKidsHealth">
    <meta name="source_org" content="SickKids">
    <meta name="url" content="{url}">
    <meta name="scraped_date" content="{datetime.now().strftime('%Y-%m-%d')}">
    <title>{title}</title>
</head>
<body>
    <h1>{title}</h1>
    <p><strong>Source:</strong> <a href="{url}">SickKids AboutKidsHealth</a></p>
    <p><strong>URL:</strong> {url}</p>
    <hr>
    {page_data['html']}
</body>
</html>
"""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"✓ Saved: {filename}")
        return str(filepath)
    
    def run(self, start_urls: List[str] = None, use_sitemap: bool = True):
        """
        Run the scraper.
        
        Args:
            start_urls: Starting URLs to scrape
            use_sitemap: Whether to try using sitemap
        """
        logger.info("=" * 60)
        logger.info("SickKids AboutKidsHealth Advanced Scraper")
        logger.info("=" * 60)
        
        urls_to_scrape = []
        
        # Get URLs from sitemap
        if use_sitemap:
            sitemap_urls = self.get_sitemap_urls()
            relevant_urls = self.filter_relevant_urls(sitemap_urls)
            urls_to_scrape.extend(relevant_urls)
        
        # Add manual start URLs
        if start_urls:
            urls_to_scrape.extend(start_urls)
        
        # Remove duplicates
        urls_to_scrape = list(set(urls_to_scrape))
        
        logger.info(f"Total URLs to process: {len(urls_to_scrape)}")
        
        # Scrape with progress bar
        for url in tqdm(urls_to_scrape, desc="Scraping pages"):
            self.scrape_url(url)
            time.sleep(self.delay)
        
        # Save metadata
        self._save_metadata()
        
        logger.info("=" * 60)
        logger.info("SCRAPING COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Successfully scraped: {self.saved_count} pages")
        logger.info(f"Saved to: {self.output_dir}")
        logger.info(f"Metadata: {self.metadata_file}")
        logger.info("=" * 60)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Advanced scraper for SickKids AboutKidsHealth"
    )
    parser.add_argument(
        "--sitemap",
        action="store_true",
        help="Use sitemap.xml to find URLs"
    )
    parser.add_argument(
        "--urls",
        type=str,
        nargs='+',
        help="Manual list of URLs to scrape"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="KB/SickKids",
        help="Output directory"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.5,
        help="Delay between requests (seconds)"
    )
    
    args = parser.parse_args()
    
    scraper = AdvancedSickKidsScraper(
        output_dir=args.output_dir,
        delay=args.delay
    )
    
    scraper.run(
        start_urls=args.urls,
        use_sitemap=args.sitemap
    )

