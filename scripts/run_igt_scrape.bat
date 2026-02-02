@echo off
REM Batch script to run the IGT search results scraper
REM This script scrapes SickKids search results for IGT (Image-Guided Therapy) procedures

echo ======================================
echo SickKids IGT Search Results Scraper
echo ======================================
echo.

REM Run the scraper with both search URLs
python scripts/scrape_sickkids_search_igt.py ^
    "https://www.aboutkidshealth.ca/search/?text=IGT&language=en&facets=healthcategorylist%%3Aprocedures" ^
    "https://www.aboutkidshealth.ca/search/?text=IGT&language=en&facets=healthcategorylist%%3Aprocedures&pagenumber=2" ^
    --output-dir "KB/SickKids" ^
    --delay 2.0

echo.
echo ======================================
echo Scraping Complete!
echo ======================================
echo.
echo Next steps:
echo 1. Review the scraped content in KB/SickKids/
echo 2. python scripts/verify_chunks.py KB/SickKids/
echo 3. python scripts/ingest_documents.py KB/ --reset
echo 4. python test_chat.py
echo.
pause

