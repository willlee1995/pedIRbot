# PowerShell script to run the IGT search results scraper
# This script scrapes SickKids search results for IGT (Image-Guided Therapy) procedures

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "SickKids IGT Search Results Scraper" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# Define the search URLs
$searchUrls = @(
    "https://www.aboutkidshealth.ca/search/?text=IGT&language=en&facets=healthcategorylist%3Aprocedures",
    "https://www.aboutkidshealth.ca/search/?text=IGT&language=en&facets=healthcategorylist%3Aprocedures&pagenumber=2"
)

Write-Host "URLs to process:" -ForegroundColor Yellow
foreach ($url in $searchUrls) {
    Write-Host "  - $url"
}
Write-Host ""

# Run the scraper
Write-Host "Starting scraper..." -ForegroundColor Green
python scripts/scrape_sickkids_search_igt.py `
    $searchUrls[0] `
    $searchUrls[1] `
    --output-dir "KB/SickKids" `
    --delay 2.0

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Scraping Complete!" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Review the scraped content in KB/SickKids/"
Write-Host "2. python scripts/verify_chunks.py KB/SickKids/"
Write-Host "3. python scripts/ingest_documents.py KB/ --reset"
Write-Host "4. python test_chat.py"

