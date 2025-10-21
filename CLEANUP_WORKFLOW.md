# SickKids HTML Cleanup Workflow

## The Problem

Scraped SickKids HTML files contain unwanted sections:

- Elements with `data-propname="AtSickKids"` (navigation/metadata)
- Elements with `aria-controls="article-AtSickKids"` (UI controls)
- First 31 lines of each file (headers/navigation)

This causes:

- ❌ Metadata pollution in converted markdown
- ❌ Short files (mostly metadata, little content)
- ❌ Irrelevant content in embeddings
- ❌ Poor retrieval quality

## Solution: Clean & Re-Process

### Step 1: Clean Existing HTML Files

Clean up already-scraped files:

```bash
# Dry run first (see what would be cleaned)
python scripts/clean_sickkids_html.py --dry-run

# Output:
# Would clean 45 files:
#   - Remove: data-propname='AtSickKids' elements
#   - Remove: aria-controls='article-AtSickKids' elements
#   - Remove first 31 lines
```

If the dry run looks good, apply the cleanup:

```bash
# Clean all HTML files (creates .html.bak backups)
python scripts/clean_sickkids_html.py

# Output:
# ✅ Cleaned: 42
# ⏭️  Skipped: 3 (no changes needed)
# 💾 Backups created: 42 .html.bak files
```

**Options:**

```bash
# Clean specific directory
python scripts/clean_sickkids_html.py KB/SickKids

# Clean without backups
python scripts/clean_sickkids_html.py --no-backup

# Custom file pattern
python scripts/clean_sickkids_html.py --pattern "*PICC*.html"
```

### Step 2: Re-Convert to Markdown

After cleaning HTML, re-convert to markdown:

```bash
# Force re-conversion (overwrite existing markdown)
python scripts/convert_to_markdown.py --force

# Output:
# ✅ Successfully converted: 45
# 📄 Markdown files copied: 3
```

Now check a file to verify cleanup worked:

```bash
# Check the PICC removal file that was 203 chars
cat KB/md/SickKids/sickkids_PICC_removal_*.md

# Should now have more content, less metadata
```

### Step 3: Re-Ingest

Embed the cleaned markdown:

```bash
python scripts/ingest_documents.py --reset

# Output:
# ✅ INGESTION COMPLETE
# Total documents: 1,234
```

### Step 4: Test Retrieval

Verify improvement:

```bash
python scripts/analyze_retrieval.py "What is a PICC line?" --full

# Should now see:
# ✅ PICC insertion page (not removal!)
# ✅ Higher quality content
# ✅ No metadata pollution
```

## Complete Cleanup Workflow

```bash
# 1. Clean HTML files
python scripts/clean_sickkids_html.py --dry-run  # Preview
python scripts/clean_sickkids_html.py            # Execute

# 2. Re-convert to markdown
python scripts/convert_to_markdown.py --force

# 3. Inspect markdown (optional)
cat KB/md/SickKids/sickkids_PICC_insertion.md
python scripts/preview_markdown_conversion.py KB/SickKids/picc_insertion.html

# 4. Re-ingest
python scripts/ingest_documents.py --reset

# 5. Test
python scripts/analyze_retrieval.py "What is a PICC line?"
python test_chat.py
```

## Future Scraping (Already Fixed!)

The scraper (`scripts/scrape_sickkids_all_pages.py`) is now updated to automatically remove these sections during scraping.

Future scrapes will be clean automatically:

```bash
# New scrapes will be clean
python scripts/scrape_sickkids_all_pages.py --pages 10

# No need to run cleanup script!
```

## Restoring Backups (If Needed)

If cleanup went wrong, restore from backups:

```bash
# Restore a single file
mv KB/SickKids/sickkids_PICC_insertion.html.bak KB/SickKids/sickkids_PICC_insertion.html

# Restore all files (in KB/SickKids/)
cd KB/SickKids
for file in *.html.bak; do
    mv "$file" "${file%.bak}"
done
```

Or in PowerShell:

```powershell
# Restore all
Get-ChildItem KB/SickKids/*.html.bak | ForEach-Object {
    Rename-Item $_ $_.Name.Replace('.html.bak', '.html')
}
```

## Troubleshooting

### "No files found"

**Problem**: `No files found matching '*.html'`

**Solution**:

```bash
# Check directory exists
ls KB/SickKids/

# Specify correct directory
python scripts/clean_sickkids_html.py KB/SickKids
```

### "Still seeing metadata in markdown"

**Problem**: Metadata still appears after cleanup

**Solutions**:

```bash
# 1. Verify HTML was actually cleaned
grep "AtSickKids" KB/SickKids/*.html
# Should find nothing

# 2. Force re-conversion
python scripts/convert_to_markdown.py --clean
python scripts/convert_to_markdown.py

# 3. Check specific file
python scripts/preview_markdown_conversion.py KB/SickKids/problematic_file.html
```

### "Cleaned too much content"

**Problem**: Important content was removed

**Solutions**:

```bash
# 1. Restore from backup
mv KB/SickKids/file.html.bak KB/SickKids/file.html

# 2. Adjust cleanup script if needed (less aggressive)

# 3. Re-scrape specific file
# (scraper already has the fix, so re-scraping is safe)
```

## Verification Checklist

After cleanup, verify:

- [ ] HTML files no longer contain `data-propname="AtSickKids"`
- [ ] Markdown files are longer than before (more actual content)
- [ ] Markdown files don't start with repeated titles
- [ ] PICC insertion page is now retrieved instead of removal page
- [ ] Retrieved chunks have meaningful content, not just metadata

Quick verification:

```bash
# Check no AtSickKids metadata remains
grep -r "AtSickKids" KB/SickKids/*.html
# Should return nothing

# Check markdown file sizes increased
ls -lh KB/md/SickKids/ | grep PICC

# Test specific query
python scripts/analyze_retrieval.py "What is a PICC line?" -k 5 --full
```

## Summary

**For existing files:**

1. Run cleanup script
2. Re-convert to markdown
3. Re-ingest

**For future scraping:**

- ✅ Already fixed in scraper!
- New scrapes will be clean automatically

**Total time:** ~10-15 minutes depending on number of files
