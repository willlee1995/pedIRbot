# SickKids Scraping Quick Start

Get SickKids content into your knowledge base in 3 easy steps!

## Method 1: Manual URL List (Recommended)

### Step 1: Find Relevant Articles

Visit [AboutKidsHealth](https://www.aboutkidshealth.ca/) and search for:

- "image guided procedures"
- "interventional radiology"
- "fluoroscopy"
- "biopsy"

### Step 2: Create URL List

Edit `KB/SickKids/urls_to_scrape.txt`:

```text
https://www.aboutkidshealth.ca/Article?contentid=1234&language=English
https://www.aboutkidshealth.ca/Article?contentid=5678&language=English
https://www.aboutkidshealth.ca/Article?contentid=9012&language=English
```

### Step 3: Run Scraper

```bash
# Activate environment
.venv\Scripts\activate

# Scrape (with 2 second delay to be respectful)
python scripts/scrape_sickkids.py --mode manual \
  --urls-file KB/SickKids/urls_to_scrape.txt \
  --delay 2.0
```

Expected output:

```
[1/3] Scraping: https://www.aboutkidshealth.ca/Article?contentid=1234...
✓ Saved: sickkids_Image_Guided_Biopsy_1234.html
[2/3] Scraping: https://www.aboutkidshealth.ca/Article?contentid=5678...
✓ Saved: sickkids_Fluoroscopy_Procedure_5678.html
...
Completed: 3 pages saved
```

### Step 4: Ingest into RAG

```bash
# Now ingest all KB content including scraped HTML
python scripts/ingest_documents.py KB/ --reset
```

Done! The scraped content is now searchable. ✅

## Method 2: Scrape All Search Result Pages (Recommended!)

```bash
# Scrape all 10 pages of "Image guided" search results automatically
python scripts/scrape_sickkids_all_pages.py \
  --query "Image guided" \
  --pages 10 \
  --delay 2.0
```

This will:

- Fetch pages 1-10 from search results
- Extract ~200-233 article URLs
- Scrape each article automatically
- Save all content to KB/SickKids/

**Note**: Takes about 8-10 minutes for all 233 articles with 2s delay.

## Method 3: Advanced Scraper with Sitemap

```bash
# Uses sitemap.xml to find relevant pages
python scripts/scrape_sickkids_advanced.py --sitemap --delay 2.0
```

## Quick Commands

```bash
# Basic scrape from URL list
python scripts/scrape_sickkids.py --mode manual --urls-file KB/SickKids/urls_to_scrape.txt

# With slower delay (more respectful)
python scripts/scrape_sickkids.py --mode manual --urls-file KB/SickKids/urls_to_scrape.txt --delay 3.0

# Search mode
python scripts/scrape_sickkids.py --mode search --max-pages 10

# Check what was scraped
ls KB/SickKids/*.html
cat KB/SickKids/scrape_metadata.json

# Ingest everything
python scripts/ingest_documents.py KB/ --reset
```

## Scraping Parameters

| Parameter     | Description              | Recommended Value |
| ------------- | ------------------------ | ----------------- |
| `--delay`     | Seconds between requests | 1.5-3.0           |
| `--max-pages` | Maximum pages to scrape  | 10-50             |
| `--mode`      | `manual` or `search`     | `manual`          |

## Best Practices

### ✅ DO

- Start with a small test (5-10 URLs)
- Use 2+ second delays
- Scrape during off-peak hours
- Verify content quality after scraping
- Keep metadata file for tracking

### ❌ DON'T

- Scrape thousands of pages at once
- Use delays < 1 second
- Re-scrape already downloaded content
- Ignore robots.txt
- Scrape non-public content

## Troubleshooting

### No files created

**Check**:

```bash
ls KB/SickKids/
# Should see .html files
```

**If empty**:

- Check internet connection
- Verify URLs in urls_to_scrape.txt are valid
- Try with `--delay 3.0`

### "Connection refused" errors

- Site may be blocking automated requests
- Try increasing delay to 3-5 seconds
- Check you're not being rate-limited
- Try manual mode instead of search mode

### Files are empty or have errors

- Inspect a file to see what was captured
- Site structure may have changed
- Update content selectors in scraper script
- Try advanced scraper

## What Gets Scraped

Each scraped page includes:

- Article title
- Main content
- Source URL
- Scrape date
- Source attribution

MarkItDown will then convert this to clean text for embedding.

## Full Workflow

```bash
# 1. Scrape content
python scripts/scrape_sickkids.py --mode manual --urls-file KB/SickKids/urls_to_scrape.txt --delay 2.0

# 2. Verify chunks
python scripts/verify_chunks.py KB/SickKids/

# 3. Ingest to vector DB
python scripts/ingest_documents.py KB/ --reset

# 4. Test retrieval
python test_chat.py
# Ask: "What does SickKids say about image-guided biopsies?"
```

## Example URLs to Start With

Sample SickKids AboutKidsHealth topics (you'll need to find actual URLs):

- Image-guided biopsies in children
- Fluoroscopy procedures
- Sedation for imaging procedures
- Ultrasound-guided drainage
- Preparation for imaging tests

## See Also

- **Full Guide**: `docs/SCRAPING_GUIDE.md`
- **SickKids KB README**: `KB/SickKids/README.md`
- **Web Scraping Ethics**: Always be respectful!

---

**Ready to scrape?** Add your URLs and run the scraper! 🚀
