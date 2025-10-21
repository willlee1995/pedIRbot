"""Web scraper for SickKids AboutKidsHealth image guidance content."""
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
from urllib.parse import urljoin, urlparse
from typing import Set, List, Dict, Any

import requests
from bs4 import BeautifulSoup
from loguru import logger


class SickKidsImageGuidanceScraper:
    """Scraper for SickKids AboutKidsHealth image guidance content."""

    BASE_URL = "https://www.aboutkidshealth.ca"
    SEARCH_KEYWORDS = [
        "image guidance",
        "image guided",
        "interventional radiology",
        "fluoroscopy",
        "ultrasound guided",
        "CT guided",
        "MRI guided",
        "biopsy",
        "drainage"
    ]

    def __init__(self, output_dir: str = "KB/SickKids",
                 delay: float = 1.0,
                 max_pages: int = 100):
        """
        Initialize the scraper.

        Args:
            output_dir: Directory to save scraped HTML files
            delay: Delay between requests (seconds) - be respectful!
            max_pages: Maximum number of pages to scrape
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.delay = delay
        self.max_pages = max_pages
        self.visited_urls: Set[str] = set()
        self.scraped_count = 0

        # Setup session with headers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })

        logger.info(f"Initialized SickKids scraper")
        logger.info(f"Output directory: {self.output_dir}")
        logger.info(f"Delay between requests: {self.delay}s")

    def search_site(self, keywords: List[str]) -> List[str]:
        """
        Search the site for pages matching keywords.

        Args:
            keywords: List of search keywords

        Returns:
            List of URLs found
        """
        found_urls = []

        for keyword in keywords:
            try:
                logger.info(f"Searching for: '{keyword}'")

                # SickKids search URL (may need adjustment based on actual site structure)
                search_url = f"{self.BASE_URL}/search?q={keyword.replace(' ', '+')}"

                response = self.session.get(search_url, timeout=10)
                response.raise_for_status()

                soup = BeautifulSoup(response.content, 'html.parser')

                # Find article links (adjust selector based on actual site structure)
                # Common patterns for medical sites:
                links = soup.find_all('a', href=True)

                for link in links:
                    href = link.get('href')
                    if href:
                        full_url = urljoin(self.BASE_URL, href)

                        # Filter for article pages (adjust patterns as needed)
                        if self._is_relevant_url(full_url, keyword):
                            found_urls.append(full_url)

                logger.info(f"Found {len(found_urls)} URLs for '{keyword}'")
                time.sleep(self.delay)

            except Exception as e:
                logger.error(f"Error searching for '{keyword}': {e}")
                continue

        # Remove duplicates
        found_urls = list(set(found_urls))
        logger.info(f"Total unique URLs found: {len(found_urls)}")

        return found_urls

    def _is_relevant_url(self, url: str, keyword: str) -> bool:
        """
        Check if URL is relevant for scraping.

        Args:
            url: URL to check
            keyword: Search keyword

        Returns:
            True if URL should be scraped
        """
        url_lower = url.lower()

        # Skip non-article pages
        skip_patterns = [
            '/search', '/login', '/register', '/cart', '/checkout',
            '/contact', '/about', '/privacy', '/terms',
            '.pdf', '.jpg', '.png', '.gif', '.css', '.js'
        ]

        if any(pattern in url_lower for pattern in skip_patterns):
            return False

        # Include if URL or path contains relevant keywords
        relevant_patterns = [
            'article', 'health', 'procedure', 'treatment',
            'radiology', 'imaging', 'guidance', 'biopsy',
            'intervention', 'fluoroscopy', 'ultrasound'
        ]

        return any(pattern in url_lower for pattern in relevant_patterns)

    def scrape_page(self, url: str) -> Dict[str, Any]:
        """
        Scrape a single page.

        Args:
            url: URL to scrape

        Returns:
            Dictionary with page data
        """
        try:
            logger.info(f"Scraping: {url}")

            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract title
            title_tag = soup.find('title')
            title = title_tag.get_text().strip() if title_tag else "Untitled"

            # Extract main content (adjust selector based on actual site)
            # Try common content selectors
            content = None
            for selector in ['article', 'main', '.content', '.article-content', '#content']:
                content = soup.select_one(selector)
                if content:
                    break

            if not content:
                content = soup.find('body')

            return {
                'url': url,
                'title': title,
                'content': content,
                'html': str(content) if content else '',
                'full_html': str(soup)
            }

        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return None

    def save_page(self, page_data: Dict[str, Any]) -> str:
        """
        Save scraped page to HTML file.

        Args:
            page_data: Page data dictionary

        Returns:
            Path to saved file
        """
        # Create safe filename from title and URL
        title = page_data['title']
        url = page_data['url']

        # Clean title for filename
        safe_title = re.sub(r'[^\w\s-]', '', title)
        safe_title = re.sub(r'[-\s]+', '_', safe_title)
        safe_title = safe_title[:100]  # Limit length

        # Add URL hash for uniqueness
        url_hash = abs(hash(url)) % 10000

        filename = f"{safe_title}_{url_hash}.html"
        filepath = self.output_dir / filename

        # Create HTML document with metadata
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="source" content="SickKids AboutKidsHealth">
    <meta name="url" content="{page_data['url']}">
    <meta name="scraped_date" content="{time.strftime('%Y-%m-%d')}">
    <title>{page_data['title']}</title>
</head>
<body>
    <h1>{page_data['title']}</h1>
    <p><strong>Source:</strong> <a href="{page_data['url']}">{page_data['url']}</a></p>
    <hr>
    {page_data['html']}
</body>
</html>
"""

        # Save to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)

        logger.info(f"Saved: {filename}")
        return str(filepath)

    def scrape_search_results(self, start_url: str = None, keywords: List[str] = None):
        """
        Main scraping method - search and scrape relevant pages.

        Args:
            start_url: Starting URL (optional)
            keywords: Search keywords (optional, uses defaults)
        """
        keywords = keywords or self.SEARCH_KEYWORDS

        logger.info("=" * 60)
        logger.info("Starting SickKids AboutKidsHealth Scraper")
        logger.info("=" * 60)

        # Method 1: Search-based scraping
        urls_to_scrape = self.search_site(keywords)

        # Method 2: If start_url provided, also crawl from there
        if start_url:
            logger.info(f"Also crawling from: {start_url}")
            urls_to_scrape.append(start_url)

        # Scrape each URL
        logger.info(f"Will scrape up to {min(len(urls_to_scrape), self.max_pages)} pages")

        for i, url in enumerate(urls_to_scrape[:self.max_pages], 1):
            if url in self.visited_urls:
                continue

            logger.info(f"[{i}/{min(len(urls_to_scrape), self.max_pages)}] Processing: {url}")

            # Scrape page
            page_data = self.scrape_page(url)

            if page_data and page_data['html']:
                # Save page
                self.save_page(page_data)
                self.scraped_count += 1

            self.visited_urls.add(url)

            # Be respectful - delay between requests
            if i < min(len(urls_to_scrape), self.max_pages):
                time.sleep(self.delay)

        logger.info("=" * 60)
        logger.info("SCRAPING COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Pages scraped: {self.scraped_count}")
        logger.info(f"Output directory: {self.output_dir}")
        logger.info("=" * 60)

    def scrape_manual_urls(self, urls: List[str]):
        """
        Scrape a manually provided list of URLs.

        Args:
            urls: List of URLs to scrape
        """
        logger.info(f"Scraping {len(urls)} manually provided URLs...")

        for i, url in enumerate(urls, 1):
            if url in self.visited_urls:
                logger.info(f"[{i}/{len(urls)}] Already visited: {url}")
                continue

            logger.info(f"[{i}/{len(urls)}] Scraping: {url}")

            page_data = self.scrape_page(url)

            if page_data and page_data['html']:
                self.save_page(page_data)
                self.scraped_count += 1

            self.visited_urls.add(url)

            if i < len(urls):
                time.sleep(self.delay)

        logger.info(f"Completed: {self.scraped_count} pages saved")


def main(mode: str = "search",
         keywords: str = None,
         urls_file: str = None,
         output_dir: str = "KB/SickKids",
         delay: float = 1.0,
         max_pages: int = 100):
    """
    Main function for SickKids scraper.

    Args:
        mode: 'search' or 'manual'
        keywords: Comma-separated keywords for search mode
        urls_file: Path to file with URLs (one per line) for manual mode
        output_dir: Output directory for scraped HTML
        delay: Delay between requests
        max_pages: Maximum pages to scrape
    """
    scraper = SickKidsImageGuidanceScraper(
        output_dir=output_dir,
        delay=delay,
        max_pages=max_pages
    )

    if mode == "search":
        # Search mode: use keywords
        if keywords:
            keyword_list = [k.strip() for k in keywords.split(',')]
        else:
            keyword_list = scraper.SEARCH_KEYWORDS

        scraper.scrape_search_results(keywords=keyword_list)

    elif mode == "manual":
        # Manual mode: read URLs from file
        if not urls_file:
            logger.error("Manual mode requires --urls-file parameter")
            return

        urls_path = Path(urls_file)
        if not urls_path.exists():
            logger.error(f"URLs file not found: {urls_file}")
            return

        with open(urls_path, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]

        logger.info(f"Loaded {len(urls)} URLs from {urls_file}")
        scraper.scrape_manual_urls(urls)

    else:
        logger.error(f"Unknown mode: {mode}. Use 'search' or 'manual'")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Scrape SickKids AboutKidsHealth image guidance content"
    )
    parser.add_argument(
        "--mode",
        type=str,
        default="search",
        choices=['search', 'manual'],
        help="Scraping mode: 'search' (search by keywords) or 'manual' (use URL list)"
    )
    parser.add_argument(
        "--keywords",
        type=str,
        help="Comma-separated keywords for search mode (default: image guidance related)"
    )
    parser.add_argument(
        "--urls-file",
        type=str,
        help="Path to file with URLs (one per line) for manual mode"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="KB/SickKids",
        help="Output directory for scraped HTML files"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Delay between requests in seconds (be respectful!)"
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=100,
        help="Maximum number of pages to scrape"
    )

    args = parser.parse_args()

    logger.info("SickKids AboutKidsHealth Scraper")
    logger.info("Please be respectful of the website:")
    logger.info("- Using reasonable delays between requests")
    logger.info("- Limiting number of pages")
    logger.info("- Only scraping publicly available content")

    main(
        mode=args.mode,
        keywords=args.keywords,
        urls_file=args.urls_file,
        output_dir=args.output_dir,
        delay=args.delay,
        max_pages=args.max_pages
    )

