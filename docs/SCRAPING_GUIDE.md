# Web Scraping Guide for SickKids Content

## Overview

The PedIR RAG backend includes web scrapers to collect content from **SickKids AboutKidsHealth** website, specifically focused on image guidance and interventional radiology procedures.

## ⚠️ Important: Ethical Scraping

### Be Respectful

1. **Rate Limiting**: Default 1.5 second delay between requests
2. **Reasonable Limits**: Max 100 pages by default
3. **Public Content Only**: Only scrape publicly available information
4. **Attribution**: All scraped pages include source attribution
5. **Check robots.txt**: Respect the site's crawling policies

### Legal Considerations

- Content is for **educational purposes** only
- Attribute source properly in all uses
- Do not violate copyright or terms of service
- Consider reaching out to SickKids for permission for large-scale scraping

## Scraper Options

### Option 1: Basic Scraper (`scrape_sickkids.py`)

Simple keyword-based scraper with two modes.

**Search Mode** (searches site for keywords):

```bash
python scripts/scrape_sickkids.py --mode search
```

**Manual Mode** (scrapes specific URLs from file):

```bash
python scripts/scrape_sickkids.py --mode manual --urls-file KB/SickKids/urls_to_scrape.txt
```

### Option 2: Advanced Scraper (`scrape_sickkids_advanced.py`)

More sophisticated scraper with content filtering and sitemap support.

**Using Sitemap**:

```bash
python scripts/scrape_sickkids_advanced.py --sitemap
```

**Manual URLs**:

```bash
python scripts/scrape_sickkids_advanced.py --urls "https://www.aboutkidshealth.ca/article1" "https://www.aboutkidshealth.ca/article2"
```

## Quick Start

### Step 1: Find Relevant URLs

Visit AboutKidsHealth and search for relevant topics:

```
https://www.aboutkidshealth.ca/
```

Search for:

- "image guided procedures"
- "interventional radiology"
- "fluoroscopy"
- "ultrasound guided biopsy"
- etc.

### Step 2: Add URLs to List

Edit `KB/SickKids/urls_to_scrape.txt`:

```text
# SickKids URLs for image guidance procedures
https://www.aboutkidshealth.ca/Article?contentid=1234&language=English
https://www.aboutkidshealth.ca/Article?contentid=5678&language=English
# Add more URLs...
```

### Step 3: Run Scraper

```bash
# Scrape the URLs
python scripts/scrape_sickkids.py --mode manual --urls-file KB/SickKids/urls_to_scrape.txt

# With custom delay (be more respectful)
python scripts/scrape_sickkids.py --mode manual --urls-file KB/SickKids/urls_to_scrape.txt --delay 2.0
```

### Step 4: Verify Scraped Content

```bash
# Check output directory
ls KB/SickKids/

# Should see:
# sickkids_Image_Guided_Biopsy_1234.html
# sickkids_Fluoroscopy_Procedure_5678.html
# scrape_metadata.json
```

### Step 5: Ingest into Vector Database

```bash
# Now ingest the scraped HTML (MarkItDown will convert to text)
python scripts/ingest_documents.py KB/ --reset
```

## Configuration Options

### Delay Between Requests

```bash
# Faster (use with caution)
--delay 0.5

# Default (recommended)
--delay 1.5

# Very respectful (slow but safest)
--delay 3.0
```

### Maximum Pages

```bash
# Small test
--max-pages 10

# Default
--max-pages 100

# Large scrape (be careful!)
--max-pages 500
```

### Custom Keywords

```bash
# Search for specific terms
python scripts/scrape_sickkids.py --mode search --keywords "biopsy,drainage,catheter"
```

## Output Format

### HTML Files

Each scraped page is saved as HTML with metadata:

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="source" content="SickKids AboutKidsHealth" />
    <meta name="source_org" content="SickKids" />
    <meta name="url" content="https://..." />
    <meta name="scraped_date" content="2025-10-21" />
    <title>Image-Guided Biopsy in Children</title>
  </head>
  <body>
    <h1>Image-Guided Biopsy in Children</h1>
    <p><strong>Source:</strong> SickKids AboutKidsHealth</p>
    <hr />
    [Article content...]
  </body>
</html>
```

### Metadata File

`scrape_metadata.json` tracks all scraped URLs:

```json
{
  "scraped_urls": [
    {
      "url": "https://...",
      "title": "Image-Guided Biopsy",
      "file": "sickkids_Image_Guided_Biopsy_1234.html",
      "scraped_at": "2025-10-21T14:30:00"
    }
  ],
  "last_scrape": "2025-10-21T14:30:00"
}
```

## Advanced Features

### Automatic Sitemap Crawling

```bash
# Scraper will:
# 1. Fetch sitemap.xml
# 2. Filter for relevant URLs
# 3. Scrape matching pages
python scripts/scrape_sickkids_advanced.py --sitemap --delay 2.0
```

### Content Relevance Filtering

The advanced scraper automatically:

- Filters URLs by keywords
- Checks page content for relevance
- Skips non-medical pages
- Only saves relevant content

### Progress Tracking

Uses `tqdm` for progress bars:

```
Scraping pages: 45/100 [████████░░] 45% ETA: 2m 15s
```

## Best Practices

### 1. Start Small

```bash
# Test with a few URLs first
python scripts/scrape_sickkids.py --mode manual --urls-file test_urls.txt --max-pages 5
```

### 2. Verify Content Quality

```bash
# Check a few scraped files
cat KB/SickKids/sickkids_*.html | head -50

# Make sure content is relevant and well-formatted
```

### 3. Respect the Site

```bash
# Use reasonable delays
--delay 2.0

# Limit pages
--max-pages 50

# Scrape during off-peak hours (e.g., late night)
```

### 4. Track Your Scraping

The metadata file tracks what you've scraped. Use it to avoid re-scraping:

```python
# Check what's already scraped
import json
with open('KB/SickKids/scrape_metadata.json') as f:
    data = json.load(f)
    print(f"Already scraped: {len(data['scraped_urls'])} pages")
```

## Troubleshooting

### Issue: "Connection refused" or timeouts

**Cause**: Network issues or site blocking

**Solution**:

```bash
# Increase timeout and delay
--delay 3.0

# Try again later
# Check your internet connection
```

### Issue: No URLs found in search mode

**Cause**: Search functionality might work differently

**Solution**: Use manual mode with specific URLs instead

```bash
# Switch to manual mode
python scripts/scrape_sickkids.py --mode manual --urls-file KB/SickKids/urls_to_scrape.txt
```

### Issue: "No relevant content" for most pages

**Cause**: Keyword filtering is too strict

**Solution**: Edit the relevance keywords in the script or use specific URLs

### Issue: Scraped files are empty or have errors

**Cause**: Site structure changed or wrong content selectors

**Solution**:

1. Inspect a sample page source
2. Update content selectors in the scraper
3. Report issue for script update

## Manual URL Collection Workflow

The most reliable approach:

### Step 1: Manual Search

1. Visit https://www.aboutkidshealth.ca/
2. Search for: "image guided procedures"
3. Browse results and note relevant articles

### Step 2: Create URL List

Add URLs to `KB/SickKids/urls_to_scrape.txt`:

```text
https://www.aboutkidshealth.ca/Article?contentid=123&language=English
https://www.aboutkidshealth.ca/Article?contentid=456&language=English
https://www.aboutkidshealth.ca/Article?contentid=789&language=English
```

### Step 3: Scrape

```bash
python scripts/scrape_sickkids.py --mode manual \
  --urls-file KB/SickKids/urls_to_scrape.txt \
  --delay 2.0
```

### Step 4: Verify

```bash
# Check files
ls KB/SickKids/*.html

# Verify content
python scripts/verify_chunks.py KB/SickKids/
```

### Step 5: Ingest

```bash
# Add to vector database (HTML will be converted by MarkItDown)
python scripts/ingest_documents.py KB/ --reset
```

## Example Search Queries

Useful search terms for AboutKidsHealth:

- "image guided biopsy"
- "interventional radiology children"
- "fluoroscopy pediatric"
- "ultrasound guided drainage"
- "CT guided procedure"
- "sedation imaging procedure"
- "minimally invasive pediatric"

## Common SickKids Topics

Relevant areas to look for:

1. **Imaging Procedures**

   - X-ray, CT, MRI, Ultrasound
   - Fluoroscopy-guided procedures

2. **Interventional Procedures**

   - Biopsies
   - Drainage procedures
   - Catheter placements
   - Vascular interventions

3. **Preparation & Aftercare**
   - Fasting instructions
   - Sedation information
   - Post-procedure care
   - When to call the doctor

## Integration with RAG System

### Automatic Source Detection

Files saved to `KB/SickKids/` are automatically tagged:

```python
metadata['source_org'] = 'SickKids'  # Auto-detected from path
```

### Query Filtering

You can filter retrieval by source:

```python
result = rag_pipeline.generate_response(
    query="What is image-guided biopsy?",
    filter_dict={"source_org": "SickKids"}
)
```

## Next Steps

After scraping SickKids content:

1. **Ingest**: `python scripts/ingest_documents.py KB/ --reset`
2. **Test**: `python test_chat.py`
3. **Verify**: Ask questions about topics you scraped
4. **Evaluate**: Run evaluation to check quality

## Resources

- [SickKids AboutKidsHealth](https://www.aboutkidshealth.ca/)
- [Ethical Web Scraping Guidelines](https://en.wikipedia.org/wiki/Web_scraping#Legal_issues)
- [robots.txt Specification](https://www.robotstxt.org/)

## Safety Notes

- Always check `robots.txt` before scraping
- Use reasonable delays (1-3 seconds)
- Identify your bot in User-Agent
- Stop if you get rate-limited (429 errors)
- Consider contacting SickKids for bulk data access

---

**Remember**: Be a good web citizen! Scrape responsibly. 🌐
