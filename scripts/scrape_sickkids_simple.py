"""Simple, reliable scraper for SickKids using saved search results HTML or URL list."""
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
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from loguru import logger
from tqdm import tqdm


class SimpleSickKidsScraper:
    """Simple, reliable scraper using URL lists or saved HTML."""

    BASE_URL = "https://www.aboutkidshealth.ca"

    def __init__(self, output_dir: str = "KB/SickKids", delay: float = 2.0):
        """Initialize scraper."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        })

        self.scraped_count = 0
        self.metadata = {"scraped_articles": [], "last_scrape": None}

        logger.info(f"Simple SickKids scraper initialized")
        logger.info(f"Output: {self.output_dir}")

    def scrape_article(self, url: str) -> bool:
        """Scrape a single article."""
        try:
            logger.info(f"Fetching: {url}")

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
                # Fallback: get the whole body
                main_content = soup.find('body')

            # Remove scripts, styles, nav, footer
            for unwanted in main_content.find_all(['script', 'style', 'nav', 'footer', 'header']):
                unwanted.decompose()

            # Save the article
            filepath = self._save_article(url, title, str(main_content))

            self.metadata["scraped_articles"].append({
                "url": url,
                "title": title,
                "file": os.path.basename(filepath),
                "scraped_at": datetime.now().isoformat()
            })

            self.scraped_count += 1
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

        filename = f"sickkids_{safe_title}_{url_hash}.html"
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
    <meta name="category" content="Image Guidance">
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

    def scrape_from_file(self, urls_file: str):
        """Scrape URLs from a text file."""
        urls_path = Path(urls_file)

        if not urls_path.exists():
            logger.error(f"File not found: {urls_file}")
            return

        # Read URLs
        with open(urls_path, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]

        logger.info(f"Loaded {len(urls)} URLs from {urls_file}")

        if not urls:
            logger.error("No URLs found in file")
            return

        logger.info(f"Will scrape {len(urls)} articles")
        logger.info(f"Estimated time: {len(urls) * self.delay / 60:.1f} minutes")

        # Scrape each URL
        for url in tqdm(urls, desc="Scraping articles"):
            self.scrape_article(url)
            time.sleep(self.delay)

        # Save metadata
        self._save_metadata()

        logger.info("=" * 70)
        logger.info(f"✅ Successfully scraped: {self.scraped_count}/{len(urls)} articles")
        logger.info(f"📁 Saved to: {self.output_dir}")
        logger.info("=" * 70)

    def _save_metadata(self):
        """Save metadata to JSON."""
        self.metadata["last_scrape"] = datetime.now().isoformat()
        metadata_file = self.output_dir / "scrape_metadata.json"

        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, indent=2, ensure_ascii=False)

        logger.info(f"Metadata saved: {metadata_file}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Simple SickKids scraper")
    parser.add_argument(
        "urls_file",
        type=str,
        help="Path to text file with URLs (one per line)"
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
    logger.info("SickKids Simple Scraper")
    logger.info("=" * 70)

    scraper = SimpleSickKidsScraper(
        output_dir=args.output_dir,
        delay=args.delay
    )

    scraper.scrape_from_file(args.urls_file)

    logger.info("\nNext steps:")
    logger.info("1. python scripts/verify_chunks.py KB/SickKids/")
    logger.info("2. python scripts/ingest_documents.py KB/ --reset")
    logger.info("3. python test_chat.py")

