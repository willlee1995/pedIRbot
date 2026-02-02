"""Specialized scraper for SickKids search results pages - extracts and scrapes articles from search results."""
import sys
import os
from pathlib import Path

# Add parent directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import time
import re
import json
from urllib.parse import urljoin, urlparse
from typing import List, Set
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from loguru import logger
from tqdm import tqdm


class SickKidsSearchResultsScraper:
    """Scraper for SickKids search results pages - extracts article links and scrapes them."""

    BASE_URL = "https://www.aboutkidshealth.ca"

    def __init__(self, output_dir: str = "KB/SickKids", delay: float = 2.0):
        """Initialize scraper."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.aboutkidshealth.ca/',
        })

        self.extracted_articles: List[str] = []
        self.scraped_articles: List[dict] = []
        self.metadata = {
            "search_results_pages": [],
            "extracted_articles": [],
            "scraped_articles": [],
            "last_scrape": None
        }

        logger.info(f"SickKids Search Results Scraper initialized")
        logger.info(f"Output: {self.output_dir}")

    def extract_articles_from_search_page(self, search_url: str) -> List[str]:
        """
        Extract article links from a search results page.
        
        Args:
            search_url: URL of the search results page
            
        Returns:
            List of article URLs found on the page
        """
        try:
            logger.info(f"Fetching search page: {search_url}")
            response = self.session.get(search_url, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Find all article links in search results
            # Look for links that match SickKids article pattern
            articles = []
            
            # Find main content area
            main_content = soup.find('main') or soup.find('div', role='main') or soup.find('div', {'class': re.compile('search|results', re.I)})
            
            if main_content:
                # Look for article links
                for link in main_content.find_all('a', href=True):
                    href = link.get('href')
                    
                    # Filter for actual article pages
                    if href and '/article/' in href.lower() or (href.startswith('/') and 'health' in href.lower()):
                        # Make absolute URL
                        full_url = urljoin(self.BASE_URL, href)
                        
                        # Avoid duplicates
                        if full_url not in articles and full_url not in self.extracted_articles:
                            articles.append(full_url)
                            logger.debug(f"Found article: {full_url}")
            
            logger.info(f"Extracted {len(articles)} article links from search page")
            self.extracted_articles.extend(articles)
            
            self.metadata["search_results_pages"].append({
                "url": search_url,
                "articles_found": len(articles),
                "extracted_at": datetime.now().isoformat()
            })
            
            return articles

        except Exception as e:
            logger.error(f"Error extracting articles from {search_url}: {e}")
            return []

    def scrape_article(self, url: str) -> bool:
        """
        Scrape a single article.
        
        Args:
            url: URL of article to scrape
            
        Returns:
            True if successfully scraped and saved
        """
        try:
            logger.info(f"Scraping article: {url}")

            response = self.session.get(url, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract title
            title_tag = soup.find('h1')
            if not title_tag:
                title_tag = soup.find('title')
            title = title_tag.get_text().strip() if title_tag else "Untitled"

            # Extract main content
            main_content = soup.find('main') or soup.find('article') or soup.find('div', role='main')

            if not main_content:
                main_content = soup.find('body')

            # Remove unwanted elements
            for unwanted in main_content.find_all(['script', 'style', 'nav', 'footer', 'header']):
                unwanted.decompose()

            # Save the article
            filepath = self._save_article(url, title, str(main_content))

            self.scraped_articles.append({
                "url": url,
                "title": title,
                "file": os.path.basename(filepath),
                "scraped_at": datetime.now().isoformat()
            })

            logger.info(f"✓ Saved: {os.path.basename(filepath)}")
            return True

        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return False

    def _save_article(self, url: str, title: str, content: str) -> str:
        """Save article to HTML file."""
        # Create safe filename from title
        safe_title = re.sub(r'[^\w\s-]', '', title)
        safe_title = re.sub(r'[-\s]+', '_', safe_title)
        safe_title = safe_title[:80]

        # Extract a hash from URL for uniqueness
        url_hash = abs(hash(url)) % 10000

        filename = f"sickkids_igt_{safe_title}_{url_hash}.html"
        filepath = self.output_dir / filename

        # Create HTML with metadata
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="source" content="SickKids AboutKidsHealth">
    <meta name="source_org" content="SickKids">
    <meta name="url" content="{url}">
    <meta name="scraped_date" content="{datetime.now().strftime('%Y-%m-%d')}">
    <meta name="category" content="Image-Guided Therapy">
    <title>{title}</title>
</head>
<body>
    <h1>{title}</h1>
    <p><strong>Source:</strong> <a href="{url}">SickKids AboutKidsHealth</a></p>
    <p><strong>Original URL:</strong> {url}</p>
    <p><strong>Scraped:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    <hr>
    {content}
</body>
</html>
"""

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)

        return str(filepath)

    def run(self, search_urls: List[str]):
        """
        Run the scraper on search results pages.
        
        Args:
            search_urls: List of search results page URLs
        """
        logger.info("=" * 70)
        logger.info("SickKids IGT Search Results Scraper")
        logger.info("=" * 70)

        # Extract articles from all search pages
        logger.info(f"\nPhase 1: Extracting articles from {len(search_urls)} search page(s)...")
        for search_url in tqdm(search_urls, desc="Processing search pages"):
            self.extract_articles_from_search_page(search_url)
            time.sleep(self.delay / 2)  # Shorter delay for search pages

        logger.info(f"\nFound {len(self.extracted_articles)} unique articles total")

        # Scrape each article
        logger.info(f"\nPhase 2: Scraping {len(self.extracted_articles)} articles...")
        for article_url in tqdm(self.extracted_articles, desc="Scraping articles"):
            self.scrape_article(article_url)
            time.sleep(self.delay)

        # Save metadata
        self.metadata["extracted_articles"] = self.extracted_articles
        self.metadata["scraped_articles"] = self.scraped_articles
        self.metadata["last_scrape"] = datetime.now().isoformat()

        self._save_metadata()

        logger.info("\n" + "=" * 70)
        logger.info(f"✅ Scraping Complete!")
        logger.info(f"📄 Articles scraped: {len(self.scraped_articles)}/{len(self.extracted_articles)}")
        logger.info(f"📁 Saved to: {self.output_dir}")
        logger.info("=" * 70)

    def _save_metadata(self):
        """Save metadata to JSON."""
        metadata_file = self.output_dir / "scrape_metadata_igt.json"

        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, indent=2, ensure_ascii=False)

        logger.info(f"Metadata saved: {metadata_file}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Scrape SickKids IGT search results")
    parser.add_argument(
        "search_urls",
        type=str,
        nargs='+',
        help="Search results page URLs (space-separated)"
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
        default=2.0,
        help="Delay between requests (seconds)"
    )

    args = parser.parse_args()

    logger.info("=" * 70)
    logger.info("SickKids IGT Search Results Scraper")
    logger.info("=" * 70)

    scraper = SickKidsSearchResultsScraper(
        output_dir=args.output_dir,
        delay=args.delay
    )

    scraper.run(args.search_urls)

    logger.info("\nNext steps:")
    logger.info("1. python scripts/verify_chunks.py KB/SickKids/")
    logger.info("2. python scripts/ingest_documents.py KB/ --reset")
    logger.info("3. python test_chat.py")

