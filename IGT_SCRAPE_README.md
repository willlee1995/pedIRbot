# SickKids IGT Search Results Scraper

## Overview

This scraper is designed to extract and scrape all articles from SickKids AboutKidsHealth search results pages for Image-Guided Therapy (IGT) procedures.

### What It Does

1. **Extracts article links** from search results pages
2. **Scrapes each article** individually for full content
3. **Saves everything** as clean HTML files with metadata
4. **Tracks progress** in JSON metadata files

## URLs to Scrape

The scraper will process these two search results pages:

- **Page 1:** https://www.aboutkidshealth.ca/search/?text=IGT&language=en&facets=healthcategorylist%3Aprocedures
- **Page 2:** https://www.aboutkidshealth.ca/search/?text=IGT&language=en&facets=healthcategorylist%3Aprocedures&pagenumber=2

Based on the search results provided, these pages contain **26+ articles** related to IGT procedures.

## Quick Start

### Option 1: PowerShell (Recommended for Windows)

```powershell
cd C:\Users\willl\Development Area\pedIRbot
.\scripts\run_igt_scrape.ps1
```

### Option 2: Batch File (Windows)

```cmd
cd C:\Users\willl\Development Area\pedIRbot
scripts\run_igt_scrape.bat
```

### Option 3: Direct Python Command

```bash
python scripts/scrape_sickkids_search_igt.py \
    "https://www.aboutkidshealth.ca/search/?text=IGT&language=en&facets=healthcategorylist%3Aprocedures" \
    "https://www.aboutkidshealth.ca/search/?text=IGT&language=en&facets=healthcategorylist%3Aprocedures&pagenumber=2" \
    --output-dir "KB/SickKids" \
    --delay 2.0
```

## Features

### Respectful Scraping
- 2-second delay between requests (configurable)
- Professional User-Agent header
- Proper HTTP headers

### Article Extraction
- Automatically finds and extracts article links from search results
- Filters out duplicate URLs
- Makes relative URLs absolute

### Content Cleaning
- Removes scripts, styles, navigation, footers, headers
- Extracts main content only
- Preserves article structure

### Metadata Tracking
- Saves which articles were found on each search page
- Records which articles were successfully scraped
- Timestamps for all operations
- Output: `scrape_metadata_igt.json`

## Output Structure

```
KB/SickKids/
├── sickkids_igt_article_title_1234.html
├── sickkids_igt_article_title_5678.html
├── sickkids_igt_article_title_9012.html
└── scrape_metadata_igt.json
```

Each HTML file includes:
- Original article URL
- Scrape timestamp
- Clean, extracted content
- Metadata headers

## Configuration Options

### Custom Output Directory
```bash
python scripts/scrape_sickkids_search_igt.py \
    "https://..." \
    "https://..." \
    --output-dir "custom/path"
```

### Custom Delay Between Requests
```bash
python scripts/scrape_sickkids_search_igt.py \
    "https://..." \
    "https://..." \
    --delay 1.0
```

## Next Steps After Scraping

1. **Verify the scraped content:**
   ```bash
   python scripts/verify_chunks.py KB/SickKids/
   ```

2. **Ingest into the knowledge base:**
   ```bash
   python scripts/ingest_documents.py KB/ --reset
   ```

3. **Test the RAG pipeline:**
   ```bash
   python test_chat.py
   ```

## Metadata Output

After scraping, `scrape_metadata_igt.json` will contain:

```json
{
  "search_results_pages": [
    {
      "url": "https://www.aboutkidshealth.ca/search/?text=IGT&...",
      "articles_found": 26,
      "extracted_at": "2025-10-22T14:30:00.123456"
    }
  ],
  "extracted_articles": [
    "https://www.aboutkidshealth.ca/Article?contentid=...",
    ...
  ],
  "scraped_articles": [
    {
      "url": "https://www.aboutkidshealth.ca/Article?contentid=...",
      "title": "Article Title",
      "file": "sickkids_igt_article_title_1234.html",
      "scraped_at": "2025-10-22T14:30:05.123456"
    },
    ...
  ],
  "last_scrape": "2025-10-22T14:35:00.123456"
}
```

## Troubleshooting

### No articles found?
- Check your internet connection
- Verify the URLs are accessible
- Check the console output for error messages
- Try increasing the delay (--delay 3.0)

### Articles not being scraped?
- Some articles may have different HTML structure
- Check the logs for specific errors
- Manually visit the article URLs to verify they exist

### Connection timeouts?
- Increase the delay between requests
- Check your internet connection
- Verify the SickKids site is accessible

## Related Articles in Search Results

From the search results provided, the scraper will extract and process:

- **Port** - Venous access for medications and blood draws
- **Botox therapy for spasticity** - Using image guidance
- **Botox injections into salivary glands** - For excessive drooling
- **Chest tube insertion** - Using image guidance for pleural fluid/air
- **Nephrostomy tube insertion** - Using image guidance
- **PICC insertion** - Using image guidance
- **Central venous line (CVL) insertion** - Via internal jugular vein and femoral vein
- **Varicocele embolization** - Using image guidance
- **Endovenous laser therapy (EVLT)** - Using image guidance
- **Skin and muscle biopsy** - Using image guidance
- **Bone ablation** - Using image guidance
- **Kidney biopsy** - Using image guidance
- **Cerebral angiography and endovascular embolization**
- **G/GJ tubes** - Gastrostomy and gastrojejunostomy procedures
- **Cecostomy tube insertion** - Using image guidance
- And more!

## Notes

- The scraper respects robots.txt and uses appropriate rate limiting
- Content is saved for local educational/research purposes
- Each file is tagged with source metadata for attribution
- The system integrates with your existing RAG pipeline

## Support

If you encounter any issues:
1. Check the console output for error messages
2. Verify all dependencies are installed: `pip install -r requirements.txt`
3. Ensure the KB/SickKids directory is writable
4. Try running with increased delay: `--delay 3.0`

