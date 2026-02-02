# IGT Scraper - Quick Start

## TL;DR

### Run the scraper (easiest way on Windows):
```bash
cd C:\Users\willl\Development Area\pedIRbot
python scripts/scrape_sickkids_search_igt.py "https://www.aboutkidshealth.ca/search/?text=IGT&language=en&facets=healthcategorylist%3Aprocedures" "https://www.aboutkidshealth.ca/search/?text=IGT&language=en&facets=healthcategorylist%3Aprocedures&pagenumber=2"
```

### Then ingest into knowledge base:
```bash
python scripts/ingest_documents.py KB/ --reset
```

### Test it:
```bash
python test_chat.py
```

---

## What This Does

1. **Fetches** the 2 SickKids IGT search result pages
2. **Extracts** all 26+ article links from the search results
3. **Scrapes** each article for full content
4. **Saves** everything as clean HTML files in `KB/SickKids/`
5. **Tracks** everything in `scrape_metadata_igt.json`

---

## Articles That Will Be Scraped

✓ PICC insertion  
✓ Central venous lines (CVL)  
✓ Nephrostomy tubes  
✓ Chest tube insertion  
✓ Varicocele embolization  
✓ Bone ablation  
✓ Kidney biopsy  
✓ Skin biopsies  
✓ Cerebral angiography  
✓ G/GJ tube procedures  
✓ Botox with image guidance  
✓ And 15+ more image-guided procedures

---

## Files Created

- `scripts/scrape_sickkids_search_igt.py` - The main scraper
- `scripts/run_igt_scrape.ps1` - PowerShell runner
- `scripts/run_igt_scrape.bat` - Batch file runner
- `IGT_SCRAPE_README.md` - Full documentation

---

## Configuration

**Need different timing?**
```bash
python scripts/scrape_sickkids_search_igt.py \
    "URL1" "URL2" \
    --delay 1.5
```

**Different output folder?**
```bash
python scripts/scrape_sickkids_search_igt.py \
    "URL1" "URL2" \
    --output-dir "custom/folder"
```

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Script can't find URLs | Check internet connection |
| No articles extracted | Increase delay with `--delay 3.0` |
| Articles fail to scrape | Try with `--delay 2.5` |
| Permission denied | Ensure KB/SickKids directory exists and is writable |

---

## Full Documentation

See `IGT_SCRAPE_README.md` for complete details and advanced options.

