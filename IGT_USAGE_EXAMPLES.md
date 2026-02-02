# IGT Scraper - Usage Examples

## Table of Contents
1. [Basic Usage](#basic-usage)
2. [Different Configuration Options](#configuration-options)
3. [Integration with RAG Pipeline](#integration)
4. [Troubleshooting Examples](#troubleshooting)
5. [Advanced Usage](#advanced)

---

## Basic Usage

### Example 1: Simplest Way (Just Run It)
```bash
python scripts/scrape_sickkids_search_igt.py \
    "https://www.aboutkidshealth.ca/search/?text=IGT&language=en&facets=healthcategorylist%3Aprocedures" \
    "https://www.aboutkidshealth.ca/search/?text=IGT&language=en&facets=healthcategorylist%3Aprocedures&pagenumber=2"
```

**What happens:**
- Extracts all article links from both search pages
- Scrapes each article
- Saves to `KB/SickKids/`
- Uses 2-second delay between requests

**Expected time:** ~2-3 minutes for 26+ articles

---

## Configuration Options

### Example 2: Faster Scraping (1-second delay)
```bash
python scripts/scrape_sickkids_search_igt.py \
    "https://www.aboutkidshealth.ca/search/?text=IGT&language=en&facets=healthcategorylist%3Aprocedures" \
    "https://www.aboutkidshealth.ca/search/?text=IGT&language=en&facets=healthcategorylist%3Aprocedures&pagenumber=2" \
    --delay 1.0
```

**Use case:** Stable, fast internet connection  
**Expected time:** ~1-1.5 minutes

---

### Example 3: Slower Scraping (Respectful - 5 second delay)
```bash
python scripts/scrape_sickkids_search_igt.py \
    "https://www.aboutkidshealth.ca/search/?text=IGT&language=en&facets=healthcategorylist%3Aprocedures" \
    "https://www.aboutkidshealth.ca/search/?text=IGT&language=en&facets=healthcategorylist%3Aprocedures&pagenumber=2" \
    --delay 5.0
```

**Use case:** Slower internet or extra respectful scraping  
**Expected time:** ~4-5 minutes

---

### Example 4: Custom Output Directory
```bash
python scripts/scrape_sickkids_search_igt.py \
    "https://www.aboutkidshealth.ca/search/?text=IGT&language=en&facets=healthcategorylist%3Aprocedures" \
    "https://www.aboutkidshealth.ca/search/?text=IGT&language=en&facets=healthcategorylist%3Aprocedures&pagenumber=2" \
    --output-dir "KB/IGT_Articles"
```

**Result:** Articles saved to `KB/IGT_Articles/`  
**Use case:** Keep IGT articles separate from other content

---

### Example 5: All Options Combined
```bash
python scripts/scrape_sickkids_search_igt.py \
    "https://www.aboutkidshealth.ca/search/?text=IGT&language=en&facets=healthcategorylist%3Aprocedures" \
    "https://www.aboutkidshealth.ca/search/?text=IGT&language=en&facets=healthcategorylist%3Aprocedures&pagenumber=2" \
    --output-dir "KB/SickKids/IGT" \
    --delay 2.5
```

**Result:** Articles saved to custom directory with custom delay

---

## Integration

### Example 6: Full Pipeline - Run Everything in Sequence
```bash
# Step 1: Run the scraper
python scripts/scrape_sickkids_search_igt.py \
    "https://www.aboutkidshealth.ca/search/?text=IGT&language=en&facets=healthcategorylist%3Aprocedures" \
    "https://www.aboutkidshealth.ca/search/?text=IGT&language=en&facets=healthcategorylist%3Aprocedures&pagenumber=2"

# Step 2: Wait for completion, then verify
python scripts/verify_chunks.py KB/SickKids/

# Step 3: Ingest into knowledge base
python scripts/ingest_documents.py KB/ --reset

# Step 4: Test the system
python test_chat.py
```

---

### Example 7: Quick Integration (3 commands)
```bash
# Scrape, verify, and ingest in sequence
python scripts/scrape_sickkids_search_igt.py "URL1" "URL2" && \
python scripts/verify_chunks.py KB/SickKids/ && \
python scripts/ingest_documents.py KB/ --reset
```

---

### Example 8: Batch Processing with Multiple Scopes
If you want to scrape multiple topics separately:

```bash
# Scrape IGT articles
python scripts/scrape_sickkids_search_igt.py "URL1" "URL2" --output-dir "KB/SickKids/IGT"

# Scrape other procedures
python scripts/scrape_sickkids_advanced.py --sitemap

# Then ingest all
python scripts/ingest_documents.py KB/ --reset
```

---

## Troubleshooting

### Example 9: Debugging Connection Issues
```bash
# Try with longer delay
python scripts/scrape_sickkids_search_igt.py \
    "URL1" "URL2" \
    --delay 3.0
```

**If still failing:**
```bash
# Check if URLs are accessible manually
# curl "https://www.aboutkidshealth.ca/search/?text=IGT&..."

# Or try even longer delay
python scripts/scrape_sickkids_search_igt.py \
    "URL1" "URL2" \
    --delay 5.0
```

---

### Example 10: Verify Output
```bash
# Check what was scraped
cat KB/SickKids/scrape_metadata_igt.json

# List all scraped files
ls -la KB/SickKids/sickkids_igt_*.html

# Count articles
ls KB/SickKids/sickkids_igt_*.html | wc -l

# View an article
cat KB/SickKids/sickkids_igt_picc_insertion_*.html
```

---

### Example 11: Troubleshoot Incomplete Scraping
```bash
# Check metadata to see what failed
python -c "import json; m=json.load(open('KB/SickKids/scrape_metadata_igt.json')); print(f\"Found: {len(m['extracted_articles'])}, Scraped: {len(m['scraped_articles'])}\")"

# Re-run with longer delays and check logs
python scripts/scrape_sickkids_search_igt.py "URL1" "URL2" --delay 3.0
```

---

## Advanced

### Example 12: Combining with Existing Scrapers
```bash
# Get IGT articles
python scripts/scrape_sickkids_search_igt.py "URL1" "URL2"

# Get other content from sitemap
python scripts/scrape_sickkids_advanced.py --sitemap

# Ingest all at once
python scripts/ingest_documents.py KB/ --reset
```

---

### Example 13: Extracting Specific Article Types
If you only want certain articles (manual approach):

```bash
# Save article URLs to file
# (You'd do this manually or with a separate script)

# Then scrape from file using simple scraper
python scripts/scrape_sickkids_simple.py urls.txt
```

---

### Example 14: Monitoring Progress
```bash
# In one terminal: Run the scraper
python scripts/scrape_sickkids_search_igt.py "URL1" "URL2"

# In another terminal: Monitor output
watch -n 5 'ls -la KB/SickKids/ | tail -5'

# Or on Windows PowerShell:
while($true) { Clear-Host; ls KB/SickKids/ | tail -5; Start-Sleep -Seconds 5 }
```

---

### Example 15: Validate Articles Before Ingesting
```bash
# Scrape
python scripts/scrape_sickkids_search_igt.py "URL1" "URL2"

# Verify structure
python scripts/verify_chunks.py KB/SickKids/

# Check metadata
python -c "
import json
meta = json.load(open('KB/SickKids/scrape_metadata_igt.json'))
print(f'✓ Pages processed: {len(meta[\"search_results_pages\"])}')
print(f'✓ Articles found: {len(meta[\"extracted_articles\"])}')
print(f'✓ Articles scraped: {len(meta[\"scraped_articles\"])}')
print(f'✓ Success rate: {len(meta[\"scraped_articles\"])/max(1, len(meta[\"extracted_articles\"]))*100:.1f}%')
"

# If good, ingest
python scripts/ingest_documents.py KB/ --reset
```

---

## Real-World Scenarios

### Scenario 1: "I just want the IGT articles scraped"
```bash
python scripts/scrape_sickkids_search_igt.py \
    "https://www.aboutkidshealth.ca/search/?text=IGT&language=en&facets=healthcategorylist%3Aprocedures" \
    "https://www.aboutkidshealth.ca/search/?text=IGT&language=en&facets=healthcategorylist%3Aprocedures&pagenumber=2"
```

---

### Scenario 2: "I want IGT articles AND the full SickKids content"
```bash
# Get IGT
python scripts/scrape_sickkids_search_igt.py "URL1" "URL2"

# Get everything else
python scripts/scrape_sickkids_advanced.py --sitemap

# Ingest all
python scripts/ingest_documents.py KB/ --reset
```

---

### Scenario 3: "I want to test the scraper first"
```bash
# Run on both pages
python scripts/scrape_sickkids_search_igt.py "URL1" "URL2" --delay 3.0

# Check results
cat KB/SickKids/scrape_metadata_igt.json

# Verify a few articles
ls KB/SickKids/sickkids_igt_*.html | head -3 | xargs -I {} sh -c 'echo "=== {} ===" && head -50 {}'

# If good, proceed to ingestion
python scripts/ingest_documents.py KB/ --reset
```

---

### Scenario 4: "I'm concerned about rate limiting"
```bash
# Use conservative delays
python scripts/scrape_sickkids_search_igt.py \
    "URL1" "URL2" \
    --delay 5.0
```

This will:
- Take ~2.5 minutes longer
- Be very respectful to the website
- Reduce chance of rate limiting

---

## Quick Copy-Paste Commands

### Windows PowerShell
```powershell
# Simple run
python scripts/scrape_sickkids_search_igt.py "https://www.aboutkidshealth.ca/search/?text=IGT&language=en&facets=healthcategorylist%3Aprocedures" "https://www.aboutkidshealth.ca/search/?text=IGT&language=en&facets=healthcategorylist%3Aprocedures&pagenumber=2"

# Full pipeline
python scripts/scrape_sickkids_search_igt.py "https://www.aboutkidshealth.ca/search/?text=IGT&language=en&facets=healthcategorylist%3Aprocedures" "https://www.aboutkidshealth.ca/search/?text=IGT&language=en&facets=healthcategorylist%3Aprocedures&pagenumber=2"; python scripts/verify_chunks.py KB/SickKids/; python scripts/ingest_documents.py KB/ --reset
```

### Windows Command Prompt
```cmd
:: Run the scraper
python scripts/scrape_sickkids_search_igt.py "https://www.aboutkidshealth.ca/search/?text=IGT&language=en&facets=healthcategorylist%%3Aprocedures" "https://www.aboutkidshealth.ca/search/?text=IGT&language=en&facets=healthcategorylist%%3Aprocedures&pagenumber=2"

:: Or use the batch file
scripts\run_igt_scrape.bat
```

### Linux/Mac
```bash
# Simple run
python scripts/scrape_sickkids_search_igt.py \
    "https://www.aboutkidshealth.ca/search/?text=IGT&language=en&facets=healthcategorylist%3Aprocedures" \
    "https://www.aboutkidshealth.ca/search/?text=IGT&language=en&facets=healthcategorylist%3Aprocedures&pagenumber=2"

# Full pipeline with pipes
python scripts/scrape_sickkids_search_igt.py \
    "https://www.aboutkidshealth.ca/search/?text=IGT&language=en&facets=healthcategorylist%3Aprocedures" \
    "https://www.aboutkidshealth.ca/search/?text=IGT&language=en&facets=healthcategorylist%3Aprocedures&pagenumber=2" && \
python scripts/verify_chunks.py KB/SickKids/ && \
python scripts/ingest_documents.py KB/ --reset
```

---

## Need Help?

- **Quick start:** See `IGT_QUICK_START.md`
- **Full docs:** See `IGT_SCRAPE_README.md`
- **Overview:** See `IGT_IMPLEMENTATION_SUMMARY.md`
- **Code:** See `scripts/scrape_sickkids_search_igt.py`

