# Retrieval Analysis Guide

This guide explains how to analyze and inspect what documents are being retrieved for your queries.

## Overview

The RAG system retrieves relevant documents from the knowledge base to answer questions. Understanding **what** is retrieved and **why** is crucial for:

- Diagnosing poor answer quality
- Verifying relevant content is in the knowledge base
- Tuning retrieval parameters
- Identifying irrelevant or low-quality content

## Tools Available

### 1. Analyze Retrieval Script

The `scripts/analyze_retrieval.py` tool provides detailed analysis of document retrieval.

#### Basic Usage

```bash
# Analyze a single query
python scripts/analyze_retrieval.py "What is a PICC line?"

# Analyze with top 10 results
python scripts/analyze_retrieval.py "PICC insertion" -k 10

# Show full chunk content (not just preview)
python scripts/analyze_retrieval.py "liver biopsy" --full

# Export results to JSON file
python scripts/analyze_retrieval.py "PICC line" --export results.json
```

#### What You'll See

For each retrieved document, the tool shows:

```
═══════════════════════════════════════════════════════════════════
📄 Document 1 of 5 ✅
═══════════════════════════════════════════════════════════════════
Filename:      sickkids_PICC_insertion.html
Source:        SickKids
Chunk ID:      chunk_0
Combined Score: 0.8472 ✅
  ├─ Semantic:  0.89
  └─ BM25:      0.72
Chunk Length:  843 characters

──────────────────────────────────────────────────────────────────
CONTENT:
──────────────────────────────────────────────────────────────────
A PICC (Peripherally Inserted Central Catheter) is a long, soft,
thin, flexible tube that is inserted into a vein in your child's
arm...

[Showing 300 of 843 characters. Use --full to see complete content]
```

**Score Indicators**:

- ✅ **Green (0.7+)**: High relevance - document is very likely relevant
- ⚠️ **Yellow (0.5-0.7)**: Medium relevance - document may be relevant
- ❌ **Red (<0.5)**: Low relevance - document likely not relevant

#### Interactive Mode

```bash
# Start interactive analysis
python scripts/analyze_retrieval.py

Query to analyze: What is a PICC line?
[Shows results]

Query to analyze: full
Full content display: ON

Query to analyze: liver biopsy
[Shows full content for all chunks]

Query to analyze: quit
```

Commands in interactive mode:

- `full` - Toggle full content display
- `quit` / `exit` / `q` - Exit

#### Batch Analysis

```bash
# Test multiple queries
python scripts/analyze_retrieval.py --queries \
  "What is a PICC line?" \
  "How is a liver biopsy performed?" \
  "Central venous catheter insertion"

# Pre-defined PICC tests
python scripts/analyze_retrieval.py --test-picc
```

#### Export Results

Export detailed analysis to JSON for further processing:

```bash
python scripts/analyze_retrieval.py "PICC line" --export picc_analysis.json
```

Export file structure:

```json
{
  "query": "What is a PICC line?",
  "timestamp": "2024-10-22T00:00:00",
  "settings": {
    "embedding_provider": "ollama",
    "hybrid_alpha": 0.7,
    "k": 10
  },
  "results": [
    {
      "rank": 1,
      "filename": "sickkids_PICC_insertion.html",
      "source": "SickKids",
      "score": 0.8472,
      "semantic_score": 0.89,
      "bm25_score": 0.72,
      "chunk_id": "chunk_0",
      "length": 843,
      "content": "Full chunk content...",
      "metadata": {...}
    }
  ]
}
```

### 2. Interactive Chat with Details

The `test_chat.py` interface can show detailed document information.

#### Basic Usage

```bash
# Start with verbose mode enabled
python test_chat.py --verbose

# Or start normally and toggle later
python test_chat.py
```

#### Toggle Details During Chat

```
You: details
Detailed document display: ON ✅

You: What is a PICC line?

PedIR-Bot: [Answer...]

═══════════════════════════════════════════════════════════════
📚 MATCHED DOCUMENTS (5 total)
═══════════════════════════════════════════════════════════════

📄 Document 1 ✅
────────────────────────────────────────────────────────────────
File:     sickkids_PICC_insertion.html
Source:   SickKids
Score:    0.8472 ✅
Length:   843 characters

Content preview:
A PICC (Peripherally Inserted Central Catheter) is a long, soft...
```

#### Compact View (Default)

Without `--verbose` or `details` command:

```
You: What is a PICC line?

PedIR-Bot: [Answer...]

[Sources: 5 documents]
  1. SickKids - sickkids_PICC_insertion.html (score: 0.847) ✅
  2. SickKids - sickkids_Central_venous_line.html (score: 0.782) ✅
  3. HKCH - PICC_care_guide.pdf (score: 0.721) ✅
  4. SickKids - sickkids_IV_access.html (score: 0.543) ⚠️
  5. SIR - IR_procedures.pdf (score: 0.412) ❌
```

## Understanding the Scores

### Combined Score

The **combined score** is a weighted average of semantic and BM25 scores:

```
Combined = (HYBRID_ALPHA × Semantic) + ((1 - HYBRID_ALPHA) × BM25)
```

Default `HYBRID_ALPHA = 0.7` means:

- 70% weight on semantic similarity (meaning)
- 30% weight on BM25 (keyword matching)

### Semantic Score

Measures **meaning similarity** using vector embeddings:

- Based on embeddings from your embedding model
- High score = query and document are semantically related
- Works well for synonyms and related concepts
- Example: "PICC" matches "peripherally inserted central catheter"

### BM25 Score

Measures **keyword overlap**:

- Based on exact word matching (with term frequency weighting)
- High score = many query words appear in document
- Works well for technical terms and acronyms
- Example: "PICC line insertion" scores high if document contains those exact words

## Interpreting Results

### Good Retrieval Example

```
Query: "What is a PICC line?"

Top 3 Results:
  1. sickkids_PICC_insertion.html (0.847) ✅
  2. sickkids_Central_venous_line.html (0.782) ✅
  3. HKCH_PICC_care_guide.pdf (0.721) ✅

✅ All scores > 0.7
✅ All documents are PICC-related
✅ Good mix of sources
```

**This is excellent retrieval quality!**

### Poor Retrieval Example

```
Query: "What is a PICC line?"

Top 3 Results:
  1. sickkids_Bulimia_treatment.html (0.412) ❌
  2. sickkids_Meditation_guide.html (0.387) ❌
  3. HKCH_Mental_health.pdf (0.321) ❌

❌ All scores < 0.5
❌ No documents are PICC-related
❌ Irrelevant content
```

**This indicates a problem** - see troubleshooting below.

## Troubleshooting Poor Retrieval

### Problem 1: All Scores < 0.5

**Symptom**: Top results have scores below 0.5

**Causes**:

1. Embedding model is weak (e.g., `embeddinggemma`, `qwen3-embedding`)
2. No relevant content in knowledge base
3. Query phrasing doesn't match content

**Solutions**:

```bash
# 1. Switch to better embedding model
ollama pull mxbai-embed-large
# Edit .env: OLLAMA_EMBEDDING_MODEL=mxbai-embed-large
python scripts/ingest_documents.py KB/ --reset

# 2. Check if relevant content exists
python scripts/analyze_retrieval.py "PICC line" -k 20

# 3. Try different query phrasing
python scripts/analyze_retrieval.py "peripherally inserted central catheter"
```

See: `FIX_LOW_SCORES.md` and `docs/LOW_SIMILARITY_TROUBLESHOOTING.md`

### Problem 2: Irrelevant Documents Retrieved

**Symptom**: Retrieved docs are not related to query (e.g., bulimia for PICC query)

**Causes**:

1. Knowledge base contains too much irrelevant content
2. Embedding model cannot distinguish topics

**Solutions**:

```bash
# Filter out non-procedure content
python scripts/filter_sickkids_content.py --execute
python scripts/ingest_documents.py KB/ --reset

# Try more keyword-focused retrieval
# Edit .env: HYBRID_ALPHA=0.3 (more BM25 weight)
```

### Problem 3: Good Scores but Wrong Content

**Symptom**: Scores are high (>0.6) but content isn't relevant

**Causes**:

1. Documents contain similar words but different meaning
2. Embedding model is confusing similar terms

**Solutions**:

```bash
# Use more keyword matching
# Edit .env: HYBRID_ALPHA=0.4

# Or switch to better embedding model
ollama pull snowflake-arctic-embed
```

### Problem 4: No Results Retrieved

**Symptom**: 0 documents retrieved

**Causes**:

1. Vector store is empty
2. Query doesn't match any content

**Solutions**:

```bash
# Check vector store
python test_chat.py
You: stats

# Re-ingest if empty
python scripts/ingest_documents.py KB/ --reset
```

## Tuning Retrieval

### Adjust HYBRID_ALPHA

Controls semantic vs keyword matching:

```bash
# More semantic (meaning-based) - Default
HYBRID_ALPHA=0.7

# Balanced
HYBRID_ALPHA=0.5

# More keyword-based (exact matching)
HYBRID_ALPHA=0.3
```

**When to use more keywords** (lower alpha):

- Medical acronyms and technical terms
- Exact procedure names
- When embedding model is weak

**When to use more semantic** (higher alpha):

- Natural language questions
- Synonyms and related concepts
- With good embedding models

### Adjust TOP_K_RETRIEVAL

Number of documents to retrieve:

```bash
# More context (may include less relevant docs)
TOP_K_RETRIEVAL=10

# Default - balanced
TOP_K_RETRIEVAL=5

# Only highly relevant (may miss some context)
TOP_K_RETRIEVAL=3
```

### Adjust MIN_RELEVANCE_SCORE

Minimum score threshold to use a document:

```bash
# Strict - only very relevant docs
MIN_RELEVANCE_SCORE=0.6

# Default - balanced
MIN_RELEVANCE_SCORE=0.4

# Permissive - use more docs
MIN_RELEVANCE_SCORE=0.3
```

## Best Practices

### 1. Start with Analysis

Before chatting, analyze what gets retrieved:

```bash
python scripts/analyze_retrieval.py "What is a PICC line?" --full
```

### 2. Check Multiple Queries

Test various phrasings:

```bash
python scripts/analyze_retrieval.py --queries \
  "What is a PICC line?" \
  "PICC line" \
  "peripherally inserted central catheter" \
  "PICC insertion procedure"
```

### 3. Export for Review

Save results for detailed review:

```bash
python scripts/analyze_retrieval.py "PICC line" --export picc_results.json
```

### 4. Monitor Scores

**Target scores**:

- ✅ **0.7+**: Excellent - use with confidence
- ⚠️ **0.5-0.7**: Good - usually relevant
- ❌ **<0.5**: Poor - likely not relevant

If most scores are <0.5, switch embedding model!

### 5. Verify Sources

Check that retrieved documents come from expected sources:

- HKCH procedures
- SIR guidelines
- Relevant SickKids procedure pages
- NOT general health topics

## Quick Reference

```bash
# Analyze single query
python scripts/analyze_retrieval.py "query here"

# Show full content
python scripts/analyze_retrieval.py "query" --full

# Top 20 results
python scripts/analyze_retrieval.py "query" -k 20

# Export to JSON
python scripts/analyze_retrieval.py "query" --export results.json

# Interactive analysis
python scripts/analyze_retrieval.py

# Chat with details
python test_chat.py --verbose
# Or toggle during chat:
You: details
```

## See Also

- `FIX_LOW_SCORES.md` - Fixing low similarity scores
- `docs/LOW_SIMILARITY_TROUBLESHOOTING.md` - Detailed troubleshooting
- `docs/OLLAMA_MODEL_CONTEXT_LIMITS.md` - Model specifications
- `docs/EMBEDDING_MODEL_GUIDE.md` - Choosing embedding models
