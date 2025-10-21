"""Scraper for SickKids AboutKidsHealth using search results."""
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
from typing import Set, List, Dict, Any
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from loguru import logger
from tqdm import tqdm


class SickKidsSearchScraper:
    """Scraper that extracts article URLs from SickKids search results."""

    BASE_URL = "https://www.aboutkidshealth.ca"
    SEARCH_URL = "https://www.aboutkidshealth.ca/search/"

    def __init__(self, output_dir: str = "KB/SickKids", delay: float = 2.0):
        """
        Initialize the scraper.

        Args:
            output_dir: Directory to save scraped HTML files
            delay: Delay between requests (seconds) - be respectful!
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.delay = delay
        self.visited_urls: Set[str] = set()
        self.scraped_count = 0

        # Setup session with headers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })

        # Metadata tracking
        self.metadata_file = self.output_dir / "scrape_metadata.json"
        self.metadata = self._load_metadata()

        logger.info(f"Initialized SickKids search scraper")
        logger.info(f"Output directory: {self.output_dir}")

    def _load_metadata(self) -> Dict:
        """Load existing scrape metadata."""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"scraped_articles": [], "search_queries": [], "last_scrape": None}

    def _save_metadata(self):
        """Save scrape metadata."""
        self.metadata["last_scrape"] = datetime.now().isoformat()
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, indent=2, ensure_ascii=False)

    def get_search_results(self, query: str, max_results: int = 100) -> List[str]:
        """
        Get article URLs from search results.

        Args:
            query: Search query
            max_results: Maximum number of results to collect

        Returns:
            List of article URLs
        """
        logger.info(f"Searching for: '{query}'")

        # Build search URL
        search_url = f"{self.SEARCH_URL}?text={quote_plus(query)}&language=en"

        article_urls = []
        page = 1

        try:
            while len(article_urls) < max_results:
                # Add pagination parameter (SickKids uses pagenumber=X)
                if page > 1:
                    current_url = f"{search_url}&pagenumber={page}"
                else:
                    current_url = search_url

                logger.info(f"Fetching search results page {page}: {current_url}")

                response = self.session.get(current_url, timeout=15)
                response.raise_for_status()

                soup = BeautifulSoup(response.content, 'html.parser')

                # Extract article links
                # Search results use <a class="ms-srch-item-path"> for article links
                found_links = 0

                # Method 1: Find links with specific class (most reliable)
                article_links = soup.find_all('a', class_='ms-srch-item-path')

                for link in article_links:
                    href = link.get('href')
                    if not href:
                        continue

                    # Make absolute URL
                    full_url = urljoin(self.BASE_URL, href)

                    # Filter for English language and relevant paths
                    if ('language=en' in full_url.lower() and
                        ('/healthaz/' in full_url.lower() or '/article' in full_url.lower())):
                        if full_url not in article_urls:
                            article_urls.append(full_url)
                            found_links += 1
                            logger.debug(f"Found article: {full_url}")

                # Method 2: Fallback - look for healthaz/other/ links
                if found_links == 0:
                    for link in soup.find_all('a', href=True):
                        href = link.get('href')
                        if href and '/healthaz/' in href.lower() and 'language=en' in href.lower():
                            full_url = urljoin(self.BASE_URL, href)
                            if full_url not in article_urls:
                                article_urls.append(full_url)
                                found_links += 1

                logger.info(f"Found {found_links} article links on page {page}")

                # Stop if no links found
                if found_links == 0:
                    logger.info("No more article links found")
                    break

                # Check if there are more pages
                # From HTML: <ul class="pagination simple-pagination">
                #   <li class="active"><span class="current">1</span></li>
                #   <li><span>2</span></li>...<li><span class="next">»</span></li>

                has_next_page = False

                # Simple approach: Just try to find pagination and extract max page number
                pagination = soup.find('ul', class_='pagination')

                if pagination:
                    logger.info("✓ Pagination element found, analyzing...")

                    # Extract all page numbers from <span> elements
                    all_page_nums = []
                    for span in pagination.find_all('span'):
                        text = span.get_text().strip()
                        # Check if it's a digit (page number)
                        if text.isdigit():
                            all_page_nums.append(int(text))
                            logger.info(f"  Found page number: {text}")
                        else:
                            logger.debug(f"  Skipping non-numeric span: '{text}'")

                    if all_page_nums:
                        max_page = max(all_page_nums)
                        logger.info(f"📄 Pages visible: {sorted(set(all_page_nums))}, max: {max_page}")

                        # If current page < max page, continue
                        if page < max_page:
                            has_next_page = True
                            logger.info(f"✓ More pages available (current: {page}, max: {max_page})")
                        else:
                            logger.info(f"✗ On last page (current: {page}, max: {max_page})")
                    else:
                        logger.warning("No page numbers found in pagination")
                else:
                    logger.warning("No pagination element found")

                if not has_next_page:
                    logger.info(f"Stopping pagination at page {page}")
                    break

                # Check if we have enough articles
                if len(article_urls) >= max_results:
                    logger.info(f"Reached max_results limit ({max_results})")
                    break

                page += 1

                # Safety limit
                if page > 20:
                    logger.warning("Reached safety page limit (20)")
                    break

                # Delay before next page
                logger.info(f"Waiting {self.delay}s before fetching page {page}...")
                time.sleep(self.delay)

        except Exception as e:
            logger.error(f"Error fetching search results: {e}")

        logger.info(f"Total article URLs found: {len(article_urls)}")

        # Save URLs to file for reference
        urls_file = self.output_dir / f"found_urls_{query.replace(' ', '_')}.txt"
        with open(urls_file, 'w', encoding='utf-8') as f:
            f.write(f"# URLs found for query: {query}\n")
            f.write(f"# Total: {len(article_urls)}\n")
            f.write(f"# Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            for url in article_urls:
                f.write(f"{url}\n")

        logger.info(f"URLs saved to: {urls_file}")

        return article_urls[:max_results]

    def scrape_article(self, url: str) -> bool:
        """
        Scrape a single article.

        Args:
            url: Article URL

        Returns:
            True if successfully scraped
        """
        if url in self.visited_urls:
            logger.debug(f"Already visited: {url}")
            return False

        try:
            logger.info(f"Scraping article: {url}")

            response = self.session.get(url, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract title
            title_tag = soup.find('h1') or soup.find('title')
            title = title_tag.get_text().strip() if title_tag else "Untitled"

            # Extract main article content
            # Try multiple selectors
            content = (
                soup.find('article') or
                soup.find('main') or
                soup.find(class_=re.compile(r'content|article', re.I)) or
                soup.find('div', {'role': 'main'})
            )

            if not content:
                logger.warning(f"No main content found for: {url}")
                content = soup.find('body')

            # Remove unwanted elements
            for unwanted in content.find_all(['script', 'style', 'nav', 'footer', 'header', 'aside']):
                unwanted.decompose()

            # Save the article
            saved_path = self._save_article(url, title, content)

            # Update metadata
            self.metadata["scraped_articles"].append({
                "url": url,
                "title": title,
                "file": os.path.basename(saved_path),
                "scraped_at": datetime.now().isoformat()
            })

            self.visited_urls.add(url)
            self.scraped_count += 1

            return True

        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            self.visited_urls.add(url)
            return False

    def _save_article(self, url: str, title: str, content) -> str:
        """
        Save article to HTML file.

        Args:
            url: Article URL
            title: Article title
            content: BeautifulSoup content

        Returns:
            Path to saved file
        """
        # Create safe filename
        safe_title = re.sub(r'[^\w\s-]', '', title)
        safe_title = re.sub(r'[-\s]+', '_', safe_title)
        safe_title = safe_title[:80]

        # Extract content ID from URL if available
        content_id_match = re.search(r'contentid=(\d+)', url)
        content_id = content_id_match.group(1) if content_id_match else abs(hash(url)) % 10000

        filename = f"sickkids_{safe_title}_{content_id}.html"
        filepath = self.output_dir / filename

        # Create structured HTML with metadata
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
    <p><strong>Original URL:</strong> <a href="{url}">{url}</a></p>
    <p><strong>Scraped:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    <hr>
    {content}
</body>
</html>
"""

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)

        logger.info(f"✓ Saved: {filename}")
        return str(filepath)

    def scrape_from_search(self, query: str, max_articles: int = 50):
        """
        Main method: Search and scrape articles.

        Args:
            query: Search query
            max_articles: Maximum number of articles to scrape
        """
        logger.info("=" * 70)
        logger.info("SickKids AboutKidsHealth Search-Based Scraper")
        logger.info("=" * 70)
        logger.info(f"Search query: '{query}'")
        logger.info(f"Max articles: {max_articles}")
        logger.info(f"Delay: {self.delay}s")
        logger.info("=" * 70)

        # Record search query
        self.metadata["search_queries"].append({
            "query": query,
            "date": datetime.now().isoformat(),
            "max_articles": max_articles
        })

        # Get article URLs from search results
        article_urls = self.get_search_results(query, max_results=max_articles)

        if not article_urls:
            logger.warning("No article URLs found in search results")
            logger.info("This could mean:")
            logger.info("1. No results for this query")
            logger.info("2. Site structure changed (selectors need updating)")
            logger.info("3. Network issue")
            return

        logger.info(f"Will scrape {len(article_urls)} articles")
        logger.info(f"Estimated time: {len(article_urls) * self.delay / 60:.1f} minutes")

        # Scrape each article with progress bar
        for url in tqdm(article_urls, desc="Scraping articles"):
            self.scrape_article(url)
            time.sleep(self.delay)

        # Save metadata
        self._save_metadata()

        logger.info("=" * 70)
        logger.info("SCRAPING COMPLETE")
        logger.info("=" * 70)
        logger.info(f"Successfully scraped: {self.scraped_count} articles")
        logger.info(f"Saved to: {self.output_dir}")
        logger.info(f"Metadata: {self.metadata_file}")
        logger.info("=" * 70)

        # Summary
        logger.info("\nNext steps:")
        logger.info(f"1. Check scraped files: ls {self.output_dir}/*.html")
        logger.info(f"2. Verify chunks: python scripts/verify_chunks.py {self.output_dir}")
        logger.info(f"3. Ingest: python scripts/ingest_documents.py KB/ --reset")


def main(queries: List[str] = None,
         max_articles: int = 50,
         output_dir: str = "KB/SickKids",
         delay: float = 2.0):
    """
    Main function for SickKids search scraper.

    Args:
        queries: List of search queries
        max_articles: Maximum articles per query
        output_dir: Output directory
        delay: Delay between requests
    """
    # Default queries focused on image guidance
    if not queries:
        queries = [
            "Image guided",
            "interventional radiology",
            "fluoroscopy procedure",
            "ultrasound guided",
            "CT guided",
        ]

    scraper = SickKidsSearchScraper(
        output_dir=output_dir,
        delay=delay
    )

    # Process each query
    for query in queries:
        logger.info(f"\n{'='*70}")
        logger.info(f"Processing query: '{query}'")
        logger.info(f"{'='*70}\n")

        scraper.scrape_from_search(query, max_articles=max_articles)

        # Delay between queries
        if query != queries[-1]:
            logger.info(f"Waiting {delay * 2}s before next query...")
            time.sleep(delay * 2)

    logger.info("\n" + "=" * 70)
    logger.info("ALL QUERIES COMPLETE")
    logger.info("=" * 70)
    logger.info(f"Total articles scraped: {scraper.scraped_count}")
    logger.info(f"Output directory: {scraper.output_dir}")
    logger.info("=" * 70)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Scrape SickKids AboutKidsHealth using search results"
    )
    parser.add_argument(
        "--query",
        type=str,
        default="Image guided",
        help="Search query (default: 'Image guided')"
    )
    parser.add_argument(
        "--queries",
        type=str,
        nargs='+',
        help="Multiple search queries"
    )
    parser.add_argument(
        "--max-articles",
        type=int,
        default=50,
        help="Maximum articles to scrape per query"
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
        default=2.0,
        help="Delay between requests in seconds (minimum 1.5)"
    )

    args = parser.parse_args()

    # Enforce minimum delay
    if args.delay < 1.0:
        logger.warning(f"Delay {args.delay}s is too short. Setting to 1.5s minimum.")
        args.delay = 1.5

    # Use either single query or multiple queries
    queries = args.queries if args.queries else [args.query]

    logger.info("SickKids AboutKidsHealth Search Scraper")
    logger.info("Please be respectful:")
    logger.info(f"- Delay between requests: {args.delay}s")
    logger.info(f"- Max articles per query: {args.max_articles}")
    logger.info("- Only scraping publicly available content")

    main(
        queries=queries,
        max_articles=args.max_articles,
        output_dir=args.output_dir,
        delay=args.delay
    )

