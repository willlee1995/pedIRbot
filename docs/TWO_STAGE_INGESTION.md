# Two-Stage Document Ingestion Guide

This guide explains the new two-stage ingestion workflow that separates document conversion from embedding.

## Why Two Stages?

**Old workflow (one-stage):**

```
Documents → MarkItDown → Chunking → Embedding → Vector Store
           (hidden/not inspectable)
```

**New workflow (two-stage):**

```
Stage 1: Documents → MarkItDown → Markdown files (KB/md/)
                                      ↓ (inspectable!)
Stage 2: Markdown files → Chunking → Embedding → Vector Store
```

### Benefits

1. ✅ **Inspect conversions** - See what MarkItDown extracted before embedding
2. ✅ **Debug issues** - Identify metadata pollution, poor extraction, etc.
3. ✅ **Fix and re-ingest** - Edit markdown files, then re-embed without re-converting
4. ✅ **Version control** - Track changes to converted content
5. ✅ **Faster iteration** - Skip conversion step when re-ingesting
6. ✅ **Quality control** - Review content before it goes into the knowledge base

## The Two-Stage Workflow

### Stage 1: Convert to Markdown

Convert all documents from `KB/` to markdown and save in `KB/md/`:

```bash
# Basic conversion
python scripts/convert_to_markdown.py

# Convert from custom source/output
python scripts/convert_to_markdown.py KB KB/md

# Force re-conversion (overwrite existing)
python scripts/convert_to_markdown.py --force

# Clean output directory first
python scripts/convert_to_markdown.py --clean
```

**What happens:**

1. Scans `KB/` for all supported file types
2. Converts each to markdown using MarkItDown
3. Saves to `KB/md/` preserving directory structure
4. Copies existing `.md` files as-is
5. Shows statistics and warnings

**Supported file types:**

- Documents: PDF, DOCX, PPTX, XLSX
- Web: HTML, HTM
- Images: JPG, JPEG, PNG
- Audio: MP3, WAV
- Already markdown: MD, MARKDOWN (copied)

**Output:**

```
KB/md/
├── SickKids/
│   ├── sickkids_PICC_insertion.md
│   ├── sickkids_PICC_removal.md
│   └── sickkids_liver_biopsy.md
├── HKCH/
│   ├── procedures_guide.md
│   └── safety_protocols.md
└── SIR/
    └── standards.md
```

### Stage 2: Ingest Markdown

Embed the markdown files into the vector store:

```bash
# Basic ingestion (uses KB/md/ by default)
python scripts/ingest_documents.py --reset

# Explicit path
python scripts/ingest_documents.py KB/md --reset

# Add to existing (no reset)
python scripts/ingest_documents.py KB/md
```

**What happens:**

1. Reads markdown files from `KB/md/`
2. Chunks the text
3. Generates embeddings
4. Stores in vector database
5. Shows statistics

## Complete Workflow Example

### Initial Setup

```bash
# 1. Convert all documents to markdown
python scripts/convert_to_markdown.py

# Output:
# ✅ Successfully converted: 45
# 📄 Markdown files copied: 3
# ⏭️  Skipped (exists): 0
# ❌ Failed: 2

# 2. Inspect converted markdown (optional but recommended)
ls KB/md/SickKids/

# 3. Preview specific files
python scripts/preview_markdown_conversion.py KB/SickKids/picc_insertion.html

# 4. Ingest markdown files
python scripts/ingest_documents.py KB/md --reset

# Output:
# ✅ INGESTION COMPLETE
# Total documents: 1,234

# 5. Test retrieval
python scripts/analyze_retrieval.py "What is a PICC line?"
```

### Updating Content

When you add new documents or fix existing ones:

```bash
# 1. Convert new/changed documents only
python scripts/convert_to_markdown.py
# (Skips already converted files)

# 2. Re-ingest everything
python scripts/ingest_documents.py KB/md --reset
```

### Force Re-conversion

If you've improved the scraper or need to re-convert:

```bash
# 1. Re-convert everything
python scripts/convert_to_markdown.py --force

# 2. Re-ingest
python scripts/ingest_documents.py KB/md --reset
```

### Cleaning and Starting Fresh

```bash
# 1. Clean markdown directory
python scripts/convert_to_markdown.py --clean
# Confirms before deleting KB/md/

# 2. Re-convert
python scripts/convert_to_markdown.py

# 3. Re-ingest
python scripts/ingest_documents.py KB/md --reset
```

## Directory Structure

```
pedIRbot/
├── KB/                          # Original documents
│   ├── SickKids/
│   │   ├── *.html              # Scraped HTML
│   │   └── *.pdf               # Downloaded PDFs
│   ├── HKCH/
│   │   └── *.docx              # Word documents
│   └── SIR/
│       └── *.pdf               # Guidelines
│
├── KB/md/                       # Converted markdown (Stage 1 output)
│   ├── SickKids/
│   │   ├── sickkids_PICC_insertion.md
│   │   └── sickkids_liver_biopsy.md
│   ├── HKCH/
│   │   └── procedures_guide.md
│   └── SIR/
│       └── standards.md
│
└── chroma_db/                   # Vector database (Stage 2 output)
    └── [vector store files]
```

## Inspection Between Stages

After Stage 1, inspect the markdown before ingesting:

### 1. Quick Check

```bash
# List converted files
ls -lh KB/md/SickKids/

# Check file sizes (very small = potential issue)
```

### 2. Preview Specific Files

```bash
# Preview conversion
python scripts/preview_markdown_conversion.py KB/SickKids/picc_insertion.html

# Shows:
# - Markdown content
# - Plain text (what gets chunked)
# - Warnings about issues
# - Chunk previews (with --chunks)
```

### 3. Read Markdown Directly

```bash
# Open in editor
code KB/md/SickKids/sickkids_PICC_insertion.md

# Or cat/less
cat KB/md/SickKids/sickkids_PICC_insertion.md
```

### 4. Search for Issues

```bash
# Find very short files (potential metadata-only)
find KB/md/ -name "*.md" -size -500c

# Search for metadata pollution
grep -r "Source: SickKids" KB/md/

# Search for duplicate titles
# (manually check files with repeated first lines)
```

## Fixing Issues

If you find issues in the markdown:

### Option 1: Fix Markdown Directly

```bash
# Edit the markdown file
code KB/md/SickKids/sickkids_PICC_insertion.md

# Remove metadata, fix formatting, etc.

# Re-ingest (no need to re-convert)
python scripts/ingest_documents.py KB/md --reset
```

### Option 2: Fix Source and Re-convert

```bash
# Fix the scraper or original document
# Then re-convert
python scripts/convert_to_markdown.py --force

# Re-ingest
python scripts/ingest_documents.py KB/md --reset
```

### Option 3: Exclude Bad Files

```bash
# Delete bad markdown files
rm KB/md/SickKids/sickkids_bad_file.md

# Re-ingest
python scripts/ingest_documents.py KB/md --reset
```

## Advanced Options

### Convert Specific Directory

```bash
# Convert only SickKids
python scripts/convert_to_markdown.py KB/SickKids KB/md/SickKids
```

### Convert with Custom Settings

```bash
# Non-recursive (single directory level)
python scripts/convert_to_markdown.py --no-recursive
```

### Ingest with All Formats (Not Recommended)

```bash
# Allow non-markdown files (bypasses Stage 1)
python scripts/ingest_documents.py KB --allow-all-formats --reset
# ⚠️  Not recommended! Use two-stage workflow instead
```

## Troubleshooting

### No Files Converted

**Problem**: `Found 0 files to convert`

**Solutions**:

```bash
# Check source directory exists
ls KB/

# Check file extensions are supported
ls KB/SickKids/

# Use --force to re-convert
python scripts/convert_to_markdown.py --force
```

### Conversion Failures

**Problem**: `❌ Failed: 5`

**Solutions**:

- Check logs for specific errors
- Verify files are not corrupted
- Try converting individual files with preview tool
- Update MarkItDown if compatibility issue

### Very Short Markdown Files

**Problem**: `⚠️ Very short content (203 chars)`

**Solutions**:

```bash
# Preview to see what's there
python scripts/preview_markdown_conversion.py KB/SickKids/short_file.html

# If mostly metadata, exclude or fix source
rm KB/md/SickKids/short_file.md

# Or fix source and re-convert
```

### Ingestion Finds No Documents

**Problem**: `❌ No documents processed!`

**Solutions**:

```bash
# Check markdown directory exists
ls KB/md/

# Verify it contains .md files
find KB/md/ -name "*.md"

# Run Stage 1 if missing
python scripts/convert_to_markdown.py
```

## Best Practices

### 1. Always Use Two Stages

✅ **DO:**

```bash
python scripts/convert_to_markdown.py
python scripts/ingest_documents.py KB/md --reset
```

❌ **DON'T:**

```bash
python scripts/ingest_documents.py KB --allow-all-formats --reset
```

### 2. Inspect Before Ingesting

✅ **DO:**

```bash
python scripts/convert_to_markdown.py
# Check a few files
cat KB/md/SickKids/sickkids_PICC_insertion.md
# Then ingest
python scripts/ingest_documents.py KB/md --reset
```

### 3. Version Control Markdown

✅ **DO:**

```bash
git add KB/md/
git commit -m "Add converted markdown files"
```

### 4. Keep Source and Markdown in Sync

✅ **DO:**

```bash
# After adding new sources
python scripts/convert_to_markdown.py  # Converts new files only
python scripts/ingest_documents.py KB/md --reset
```

### 5. Clean Re-conversion When Needed

✅ **DO:**

```bash
# After fixing scraper or major changes
python scripts/convert_to_markdown.py --clean
# Confirm deletion
python scripts/convert_to_markdown.py
python scripts/ingest_documents.py KB/md --reset
```

## Quick Reference

```bash
# Stage 1: Convert to Markdown
python scripts/convert_to_markdown.py                    # Basic
python scripts/convert_to_markdown.py --force             # Re-convert all
python scripts/convert_to_markdown.py --clean             # Clean first
python scripts/convert_to_markdown.py KB custom/output   # Custom paths

# Inspect (between stages)
python scripts/preview_markdown_conversion.py KB/SickKids/file.html
cat KB/md/SickKids/file.md
find KB/md/ -name "*.md" -size -500c                     # Find short files

# Stage 2: Ingest Markdown
python scripts/ingest_documents.py --reset                # Basic
python scripts/ingest_documents.py KB/md --reset          # Explicit
python scripts/ingest_documents.py KB/md                  # Add to existing

# Test
python scripts/analyze_retrieval.py "Your query here"
python test_chat.py
```

## See Also

- `docs/MARKDOWN_PREVIEW_GUIDE.md` - Preview tool usage
- `docs/MARKITDOWN_GUIDE.md` - MarkItDown details
- `docs/RETRIEVAL_ANALYSIS_GUIDE.md` - Testing retrieval
- `QUICKSTART.md` - Getting started guide
