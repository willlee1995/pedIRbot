"""Test script to verify search results parsing."""
import sys
import os
from pathlib import Path

# Add parent directory to path FIRST
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from loguru import logger


def test_parse_search_page(url: str):
    """
    Test parsing a search results page.

    Args:
        url: Search results URL
    """
    logger.info(f"Testing URL: {url}")

    try:
        # Fetch page
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        })

        response = session.get(url, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract article links
        article_links = soup.find_all('a', class_='ms-srch-item-path')

        logger.info(f"Found {len(article_links)} article links with class='ms-srch-item-path'")

        # Extract and display URLs
        base_url = "https://www.aboutkidshealth.ca"
        found_urls = []

        for link in article_links:
            href = link.get('href')
            if href:
                full_url = urljoin(base_url, href)
                if 'language=en' in full_url.lower():
                    found_urls.append(full_url)

                    # Extract title
                    h3 = link.find('h3')
                    title = h3.get_text().strip() if h3 else "No title"

                    logger.info(f"  ✓ {title}")
                    logger.info(f"    {full_url}")

        # Check pagination
        pagination = soup.find('ul', class_='pagination')
        if pagination:
            logger.info(f"\nPagination found:")

            # Find page numbers
            page_nums = []
            for span in pagination.find_all('span'):
                text = span.get_text().strip()
                if text.isdigit():
                    page_nums.append(int(text))
                elif text == '»':
                    logger.info("  Next button (») found")
                elif text == '«':
                    logger.info("  Previous button («) found")

            if page_nums:
                logger.info(f"  Page numbers visible: {sorted(page_nums)}")
                logger.info(f"  Maximum page: {max(page_nums)}")

        # Summary
        print("\n" + "=" * 70)
        print(f"SUMMARY")
        print("=" * 70)
        print(f"Total article links found: {len(found_urls)}")
        print(f"URL pattern: /healthaz/[category]/[article-name]/?language=en")
        print(f"Pagination detected: {'Yes' if pagination else 'No'}")
        print("=" * 70)

        return found_urls

    except Exception as e:
        logger.error(f"Error: {e}")
        return []


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test search results parsing")
    parser.add_argument(
        "--url",
        type=str,
        default="https://www.aboutkidshealth.ca/search/?text=Image+guided&language=en",
        help="Search results URL to test"
    )
    parser.add_argument(
        "--page",
        type=int,
        help="Specific page number to test (optional)"
    )

    args = parser.parse_args()

    # Build URL with page number if specified
    url = args.url
    if args.page:
        if '?' in url:
            url = f"{url}&pagenumber={args.page}"
        else:
            url = f"{url}?pagenumber={args.page}"

    print("=" * 70)
    print("SickKids Search Parser Test")
    print("=" * 70)

    found_urls = test_parse_search_page(url)

    if found_urls:
        print("\n✅ Parser is working correctly!")
        print(f"Found {len(found_urls)} article URLs")
        print("\nYou can now run the full scraper:")
        print("python scripts/scrape_sickkids_search.py --query 'Image guided' --max-articles 233 --delay 2.0")
    else:
        print("\n❌ Parser found no URLs - site structure may have changed")
        print("Consider using manual mode with urls_to_scrape.txt instead")

