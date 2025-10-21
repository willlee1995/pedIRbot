# Investigating PICC Retrieval Issue

## The Problem

Query: (likely "What is a PICC line?" or similar)
Retrieved: **PICC Removal** page instead of **PICC Insertion** page

Score: 0.9769 ✅ (Very high!)
Length: 203 characters (Very short!)

## Why This Might Happen

### 1. Chunk Contains General PICC Info

The "removal" page might start with a general description of what a PICC is before explaining removal. The chunk might be capturing that intro.

### 2. Chunk Is Too Short (203 chars)

This is concerning! With `MAX_CHUNK_SIZE=1024`, chunks should be much larger. A 203-char chunk suggests:

- This is a very short section/heading
- The document wasn't chunked properly
- We're missing context

### 3. Title/Heading Bias

The chunk might be mostly the page title: "PICC removal: Caring for your child at home after the procedure" which contains "PICC" multiple times, leading to high keyword matching.

## How to Investigate

### Step 1: See the Full Chunk Content

```bash
# Run with --full to see complete content
python scripts/analyze_retrieval.py "What is a PICC line?" --full -k 10

# Or in interactive mode
python scripts/analyze_retrieval.py
Query to analyze: full
Query to analyze: What is a PICC line?
```

This will show you the **complete 203 characters** to see what's actually being matched.

### Step 2: Check All Retrieved Documents

```bash
python scripts/analyze_retrieval.py "What is a PICC line?" -k 10 --full

# Check if insertion pages are in top 10
```

### Step 3: Try More Specific Queries

```bash
# More specific queries
python scripts/analyze_retrieval.py "How is a PICC line inserted?" --full
python scripts/analyze_retrieval.py "PICC insertion procedure" --full
python scripts/analyze_retrieval.py "PICC line placement" --full
```

### Step 4: Check Chunking

```bash
# Verify all chunks are properly sized
python scripts/verify_chunks.py KB/SickKids/

# Look for very short chunks
```

## Possible Issues

### Issue 1: Title Pollution

**Problem**: The chunk is mostly just the title/heading with little actual content.

**Evidence**: 203 characters is about the length of:

```
"PICC removal: Caring for your child at home after the procedure
PICC removal: Caring for your child at home after the procedure
Source: SickKids AboutKidsHealth
Original URL: https://www.aboutkidshealth..."
```

This is metadata, not actual content!

**Solution**: The scraper or document processor might be including page metadata as chunk content. Need to filter this out.

### Issue 2: Poor Chunking

**Problem**: Document wasn't chunked properly, creating tiny chunks.

**Evidence**: 203 chars when `MAX_CHUNK_SIZE=1024`

**Solution**: Check the document processor's chunking logic.

### Issue 3: Query Too General

**Problem**: Query "What is a PICC line?" matches any page mentioning PICC.

**Evidence**: High score (0.9769) because "PICC" appears multiple times in title.

**Solution**: Use more specific queries or improve chunking to exclude metadata.

## Quick Diagnosis Commands

```bash
# 1. See what's in that chunk
python scripts/analyze_retrieval.py "What is a PICC line?" --full | head -100

# 2. Check if insertion pages exist
cd KB/SickKids
ls *PICC*insertion*

# 3. Export for detailed review
python scripts/analyze_retrieval.py "What is a PICC line?" -k 20 --export picc_issue.json
```

## Expected vs Actual

**Expected Top Results:**

1. ✅ PICC_insertion.html (What it is, why it's done)
2. ✅ PICC_placement_procedure.html (How it's inserted)
3. ✅ PICC_care.html (How to care for it)
4. ⚠️ PICC_removal.html (Only if query mentions removal)

**Actual:**

1. ❌ PICC_removal.html (score: 0.9769) - Wrong for general query!

## Next Steps

1. **Check the chunk content** - Is it just metadata?
2. **Review document processing** - Are we capturing actual content or just titles?
3. **Filter metadata** - Exclude page titles, URLs, sources from chunks
4. **Re-ingest** - After fixing chunking issues
