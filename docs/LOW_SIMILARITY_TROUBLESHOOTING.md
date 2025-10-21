# Low Similarity Scores Troubleshooting

## The Problem

If you're seeing cosine similarity scores **below 0.5** for most queries, this indicates poor semantic matching between your queries and the knowledge base.

### What Similarity Scores Mean

| Score Range   | Quality   | Interpretation                              |
| ------------- | --------- | ------------------------------------------- |
| **0.8 - 1.0** | Excellent | Query and document are very similar/related |
| **0.6 - 0.8** | Good      | Clear semantic relationship                 |
| **0.4 - 0.6** | Fair      | Some relationship but weak                  |
| **< 0.4**     | Poor      | Little to no semantic relationship          |

### Why <0.5 is Problematic

```
Query: "What is a PICC line?"
Retrieved:
  1. Bulimia document (score: 0.45) ← NOT RELEVANT!
  2. Meditation document (score: 0.38) ← NOT RELEVANT!
  3. Port document (score: 0.32) ← MAYBE RELEVANT?
```

**Problem**: The model can't tell the difference between relevant and irrelevant content!

## Root Causes

### Cause 1: embeddinggemma Limitations

**Issue**: `embeddinggemma` is a smaller model optimized for efficiency, not necessarily medical terminology.

**Evidence**:

- Medical acronyms (PICC, CVL, IR) not well understood
- Limited training on medical content
- Small context window (300 chars) = less semantic information
- Smaller embedding dimension (768 vs 1024)

**Solution**: Switch to a better model

### Cause 2: Chunk Size Too Small

**Issue**: 300-character chunks don't provide enough context for semantic understanding.

**Evidence**:

```
Chunk: "A PICC is a long, soft, thin tube. It is inserted into..."
Only 300 chars = incomplete explanation, missing key terms
```

**Solution**: Use larger chunks with better embedding model

### Cause 3: Non-Procedure Content Pollution

**Issue**: Knowledge base contains irrelevant SickKids content (bulimia, meditation, etc.)

**Evidence**: Your retrieval returned bulimia and meditation documents

**Solution**: Filter out non-procedure content

### Cause 4: Insufficient Medical Content

**Issue**: Not enough relevant content in knowledge base yet

**Solution**: Add more HKCH, SIR, HKSIR, CIRSE content

## Solutions

### Solution 1: Switch to Better Embedding Model (RECOMMENDED)

#### Option A: OpenAI (Best Quality)

```bash
# Edit .env
EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
OPENAI_EMBEDDING_MODEL=text-embedding-3-large
MAX_CHUNK_SIZE=512  # Can increase now

# Re-ingest
python scripts/ingest_documents.py KB/ --reset
```

**Expected improvement**:

- Scores: 0.3-0.5 → 0.7-0.9
- Much better medical terminology understanding
- Better multilingual support

#### Option B: mxbai-embed-large (Good Quality, Local)

```bash
# Pull model
ollama pull mxbai-embed-large

# Edit .env
EMBEDDING_PROVIDER=ollama
OLLAMA_EMBEDDING_MODEL=mxbai-embed-large
MAX_CHUNK_SIZE=512  # Can increase now

# Re-ingest
python scripts/ingest_documents.py KB/ --reset
```

**Expected improvement**:

- Scores: 0.3-0.5 → 0.6-0.8
- Better than embeddinggemma
- Larger context window
- Still private/local

#### Option C: BGE-M3 (Multilingual Focus)

```bash
# Edit .env
EMBEDDING_PROVIDER=sentence-transformer
SENTENCE_TRANSFORMER_MODEL=BAAI/bge-m3
MAX_CHUNK_SIZE=512

# Re-ingest
python scripts/ingest_documents.py KB/ --reset
```

**Expected improvement**:

- Scores: 0.3-0.5 → 0.65-0.85
- Excellent for EN/ZH content
- Good medical terminology
- Fully offline

### Solution 2: Add Minimum Score Threshold

I've already added this to `src/rag_pipeline.py`:

```python
MIN_RELEVANCE_SCORE = 0.4  # Reject docs with score < 0.4

high_quality_docs = [doc for doc in retrieved_docs if doc['score'] >= 0.4]

if not high_quality_docs:
    return "I don't have sufficiently relevant information..."
```

**What this does**:

- Filters out low-quality matches
- Prevents LLM from seeing irrelevant context
- Returns "I don't know" if all scores < 0.4

### Solution 3: Filter SickKids Content

```bash
# Remove non-procedure content
python scripts/filter_sickkids_content.py --execute

# Re-ingest
python scripts/ingest_documents.py KB/ --reset
```

### Solution 4: Adjust Retrieval Parameters

```bash
# Edit .env

# Try more keyword-focused retrieval
HYBRID_ALPHA=0.3  # More weight to BM25 keyword matching

# Retrieve more documents
TOP_K_RETRIEVAL=10  # Default is 5

# Re-test
python test_chat.py
```

## Diagnosis Tools

### Tool 1: Test Embedding Quality

```bash
# Run semantic similarity tests
python scripts/diagnose_embeddings.py

# Shows how well model matches queries to relevant vs irrelevant content
```

Expected output:

```
Test 1: "What is a PICC line?"
  Relevant doc similarity:   0.892 ✅
  Irrelevant doc similarity: 0.234 ❌
  Separation:                0.658 ✅

Average relevant similarity:   0.75
Average irrelevant similarity: 0.28
Average separation:            0.47 ✅
```

**Good**: Relevant > 0.6, Separation > 0.2
**Bad**: Relevant < 0.5, Separation < 0.15

### Tool 2: Test Actual Retrieval

```bash
# Test with real vector store
python scripts/diagnose_embeddings.py --test-retrieval

# Shows actual retrieval results and scores
```

### Tool 3: Analyze Specific Queries

```bash
# Analyze what's retrieved for specific query
python scripts/analyze_retrieval.py "What is a PICC line?" -k 10

# Shows:
# - Top 10 retrieved documents
# - Their scores
# - Content previews
# - Source distribution
```

## Quick Fix Comparison

| Solution             | Time         | Difficulty | Improvement | Privacy |
| -------------------- | ------------ | ---------- | ----------- | ------- |
| **Switch to OpenAI** | 5 min        | Easy       | +++++       | ❌      |
| **Switch to mxbai**  | 10 min       | Easy       | ++++        | ✅      |
| **Switch to BGE-M3** | 15 min       | Medium     | ++++        | ✅      |
| Filter SickKids      | 2 min        | Easy       | ++          | N/A     |
| Add score threshold  | Already done | N/A        | +           | N/A     |
| Adjust HYBRID_ALPHA  | 1 min        | Easy       | +           | N/A     |

## Recommended Action Plan

### Immediate (2 minutes):

```bash
# 1. Filter out non-procedure content
python scripts/filter_sickkids_content.py --execute

# 2. Re-ingest
python scripts/ingest_documents.py KB/ --reset

# 3. Test
python test_chat.py
```

### Short-term (10 minutes):

```bash
# Switch to better embedding model
# Edit .env:
EMBEDDING_PROVIDER=ollama
OLLAMA_EMBEDDING_MODEL=mxbai-embed-large
MAX_CHUNK_SIZE=512

# Pull model
ollama pull mxbai-embed-large

# Re-ingest
python scripts/ingest_documents.py KB/ --reset

# Test
python scripts/analyze_retrieval.py "What is a PICC line?"
```

### Long-term:

1. Add more HKCH, SIR, HKSIR, CIRSE content
2. Consider OpenAI embeddings for production
3. Implement query expansion/reformulation
4. Use cross-encoder reranking

## Verification

After implementing fixes, run:

```bash
# Test retrieval quality
python scripts/analyze_retrieval.py --test-picc

# Should now see:
# ✅ sickkids_PICC_insertion.html (score: 0.847)
# ✅ sickkids_Central_venous_line.html (score: 0.782)
# ✅ sickkids_PICC_removal.html (score: 0.756)
```

## Bottom Line

**Your observation is correct**: Scores <0.5 indicate the embedding model (`embeddinggemma`) is not performing well enough for your use case.

**Recommended fix**: Switch to `mxbai-embed-large` or OpenAI's `text-embedding-3-large` for better medical content matching. 🎯
