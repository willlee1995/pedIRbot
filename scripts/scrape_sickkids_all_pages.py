"""Scraper that fetches all 10 pages of SickKids search results."""
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
from urllib.parse import urljoin, quote_plus
from typing import Set, List, Dict
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from loguru import logger
from tqdm import tqdm


class SickKidsAllPagesScraper:
    """Scraper that processes all pages (no pagination detection needed)."""

    BASE_URL = "https://www.aboutkidshealth.ca"
    SEARCH_URL = "https://www.aboutkidshealth.ca/search/"

    def __init__(self, output_dir: str = "KB/SickKids", delay: float = 2.0):
        """Initialize scraper."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.delay = delay
        self.visited_urls: Set[str] = set()
        self.scraped_count = 0

        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        })

        self.metadata = {"scraped_articles": [], "search_queries": []}

        logger.info(f"Initialized SickKids all-pages scraper")
        logger.info(f"Output: {self.output_dir}")

    def get_all_article_urls(self, query: str, num_pages: int = 10) -> List[str]:
        """
        Get article URLs from all search result pages.

        Args:
            query: Search query
            num_pages: Total number of pages to scrape

        Returns:
            List of all article URLs found
        """
        logger.info(f"Searching for: '{query}'")
        logger.info(f"Will process {num_pages} pages")

        search_url = f"{self.SEARCH_URL}?text={quote_plus(query)}&language=en"
        all_urls = []

        for page in range(1, num_pages + 1):
            # Build page URL
            if page == 1:
                page_url = search_url
            else:
                page_url = f"{search_url}&pagenumber={page}"

            logger.info(f"\n📄 Fetching page {page}/{num_pages}: {page_url}")

            try:
                response = self.session.get(page_url, timeout=15)
                response.raise_for_status()

                soup = BeautifulSoup(response.content, 'html.parser')

                # Extract article links
                article_links = soup.find_all('a', class_='ms-srch-item-path')

                page_urls = []
                for link in article_links:
                    href = link.get('href')
                    if href:
                        full_url = urljoin(self.BASE_URL, href)

                        # Filter for English language
                        if 'language=en' in full_url.lower() and full_url not in all_urls:
                            page_urls.append(full_url)
                            all_urls.append(full_url)

                logger.info(f"   ✓ Found {len(page_urls)} article URLs on page {page}")

                # Delay before next page
                if page < num_pages:
                    logger.info(f"   Waiting {self.delay}s before next page...")
                    time.sleep(self.delay)

            except Exception as e:
                logger.error(f"   ✗ Error fetching page {page}: {e}")
                continue

        logger.info(f"\n{'='*70}")
        logger.info(f"📊 TOTAL: Found {len(all_urls)} unique article URLs across {num_pages} pages")
        logger.info(f"{'='*70}")

        return all_urls

    def scrape_article(self, url: str) -> bool:
        """Scrape a single article."""
        if url in self.visited_urls:
            return False

        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract title
            title_tag = soup.find('h1') or soup.find('title')
            title = title_tag.get_text().strip() if title_tag else "Untitled"

            # Extract main content
            main_content = soup.find('main') or soup.find('article') or soup.find('div', role='main')

            if not main_content:
                main_content = soup.find('body')

            # Remove unwanted elements
            for unwanted in main_content.find_all(['script', 'style', 'nav', 'footer', 'header']):
                unwanted.decompose()

            # Save article
            filepath = self._save_article(url, title, str(main_content))

            self.metadata["scraped_articles"].append({
                "url": url,
                "title": title,
                "file": os.path.basename(filepath),
                "scraped_at": datetime.now().isoformat()
            })

            self.visited_urls.add(url)
            self.scraped_count += 1

            return True

        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            self.visited_urls.add(url)
            return False

    def _save_article(self, url: str, title: str, content: str) -> str:
        """Save article to HTML file."""
        safe_title = re.sub(r'[^\w\s-]', '', title)
        safe_title = re.sub(r'[-\s]+', '_', safe_title)
        safe_title = safe_title[:80]

        url_hash = abs(hash(url)) % 10000
        filename = f"sickkids_{safe_title}_{url_hash}.html"
        filepath = self.output_dir / filename

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="source" content="SickKids AboutKidsHealth">
    <meta name="source_org" content="SickKids">
    <meta name="url" content="{url}">
    <meta name="scraped_date" content="{datetime.now().strftime('%Y-%m-%d')}">
    <meta name="category" content="Image Guidance">
    <title>{title}</title>
</head>
<body>
    <h1>{title}</h1>
    <p><strong>Source:</strong> <a href="{url}">SickKids AboutKidsHealth</a></p>
    <p><strong>Original URL:</strong> {url}</p>
    <hr>
    {content}
</body>
</html>
"""

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)

        return str(filepath)

    def _save_metadata(self):
        """Save metadata."""
        self.metadata["last_scrape"] = datetime.now().isoformat()
        metadata_file = self.output_dir / "scrape_metadata.json"

        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, indent=2, ensure_ascii=False)

    def run(self, query: str = "Image guided", num_pages: int = 10):
        """
        Run the complete scraping process.

        Args:
            query: Search query
            num_pages: Number of pages to scrape (default: 10)
        """
        logger.info("=" * 70)
        logger.info("SickKids All-Pages Scraper")
        logger.info("=" * 70)
        logger.info(f"Query: '{query}'")
        logger.info(f"Pages: {num_pages}")
        logger.info(f"Delay: {self.delay}s")
        logger.info("=" * 70)

        # Record search
        self.metadata["search_queries"].append({
            "query": query,
            "num_pages": num_pages,
            "date": datetime.now().isoformat()
        })

        # Step 1: Get all article URLs from all pages
        logger.info("\n🔍 STEP 1: Collecting article URLs from all pages...")
        article_urls = self.get_all_article_urls(query, num_pages)

        if not article_urls:
            logger.error("No article URLs found!")
            return

        # Save URLs to file
        urls_file = self.output_dir / f"all_urls_{query.replace(' ', '_')}.txt"
        with open(urls_file, 'w', encoding='utf-8') as f:
            f.write(f"# SickKids AboutKidsHealth - '{query}' search results\n")
            f.write(f"# Total URLs: {len(article_urls)}\n")
            f.write(f"# Pages scraped: {num_pages}\n")
            f.write(f"# Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            for url in article_urls:
                f.write(f"{url}\n")

        logger.info(f"✓ URLs saved to: {urls_file}")

        # Step 2: Scrape all articles
        logger.info(f"\n📥 STEP 2: Scraping {len(article_urls)} articles...")
        logger.info(f"Estimated time: {len(article_urls) * self.delay / 60:.1f} minutes\n")

        for url in tqdm(article_urls, desc="Scraping articles"):
            self.scrape_article(url)
            time.sleep(self.delay)

        # Save metadata
        self._save_metadata()

        # Summary
        logger.info("\n" + "=" * 70)
        logger.info("✅ SCRAPING COMPLETE")
        logger.info("=" * 70)
        logger.info(f"Total URLs found: {len(article_urls)}")
        logger.info(f"Successfully scraped: {self.scraped_count}")
        logger.info(f"Failed: {len(article_urls) - self.scraped_count}")
        logger.info(f"Output directory: {self.output_dir}")
        logger.info("=" * 70)

        logger.info("\n📋 Next steps:")
        logger.info("1. python scripts/verify_chunks.py KB/SickKids/")
        logger.info("2. python scripts/ingest_documents.py KB/ --reset")
        logger.info("3. python test_chat.py")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Scrape all pages of SickKids search results (no pagination detection)"
    )
    parser.add_argument(
        "--query",
        type=str,
        default="Image guided",
        help="Search query"
    )
    parser.add_argument(
        "--pages",
        type=int,
        default=10,
        help="Number of pages to scrape (default: 10)"
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
        help="Delay between requests (minimum 1.5s)"
    )

    args = parser.parse_args()

    # Enforce minimum delay
    if args.delay < 1.5:
        logger.warning(f"Delay {args.delay}s too short. Setting to 1.5s")
        args.delay = 1.5

    scraper = SickKidsAllPagesScraper(
        output_dir=args.output_dir,
        delay=args.delay
    )

    scraper.run(
        query=args.query,
        num_pages=args.pages
    )

