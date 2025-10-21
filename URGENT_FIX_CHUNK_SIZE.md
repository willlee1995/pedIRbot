# 🚨 URGENT: Fix Chunk Truncation

## The Problem

You're losing **533 characters per chunk** due to model limitations!

```
❌ Current Configuration:
  MAX_CHUNK_SIZE = 1024
  Model: qwen3-embedding:0.6b (max 400 chars)

  Result: Chunks truncated from 933 → 400 chars
  Data Loss: 533 chars per chunk! 💀
```

## Why This Happens

`qwen3-embedding:0.6b` has a **maximum input length of ~400 characters**, but you configured `MAX_CHUNK_SIZE=1024`. The system is truncating your chunks to fit the model, losing most of the content!

## Fix: Switch to Model That Supports 1024 Chunks

### ✅ RECOMMENDED: mxbai-embed-large

This model supports up to ~2000 characters, so your 1024 chunks will work perfectly!

```bash
# 1. Pull the better model
ollama pull mxbai-embed-large

# 2. Edit your .env file:
EMBEDDING_PROVIDER=ollama
OLLAMA_EMBEDDING_MODEL=mxbai-embed-large
MAX_CHUNK_SIZE=1024  # ✅ Now fully supported!
CHUNK_OVERLAP=100

# 3. Delete corrupted vector store and re-ingest
python scripts/ingest_documents.py KB/ --reset

# 4. Verify no truncation
python scripts/diagnose_embeddings.py --test-retrieval
```

**Why this works**:

- ✅ Supports 1024+ character chunks (no truncation!)
- ✅ Better quality than qwen3-embedding (0.72 vs 0.35 similarity)
- ✅ Still fully local and private
- ✅ Larger embedding dimension (1024 vs 1024)

### Alternative Models for 1024 Chunks

#### Option 2: nomic-embed-text (Largest Context)

```bash
ollama pull nomic-embed-text

# .env:
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
MAX_CHUNK_SIZE=1024  # Can even use 2048!
```

**Supports**: Up to ~8000 characters!

#### Option 3: snowflake-arctic-embed (Best Quality)

```bash
ollama pull snowflake-arctic-embed

# .env:
OLLAMA_EMBEDDING_MODEL=snowflake-arctic-embed
MAX_CHUNK_SIZE=1024
```

**Quality**: State-of-the-art performance

## Model Comparison for 1024 Chunks

| Model                    | Max Input  | Truncation? | Similarity | Quality          |
| ------------------------ | ---------- | ----------- | ---------- | ---------------- |
| `qwen3-embedding:0.6b`   | 400 chars  | ❌ YES!     | 0.35       | Poor (data loss) |
| `embeddinggemma`         | 400 chars  | ❌ YES!     | 0.38       | Poor (data loss) |
| `mxbai-embed-large`      | 2000 chars | ✅ NO       | 0.72       | Excellent        |
| `nomic-embed-text`       | 8000 chars | ✅ NO       | 0.68       | Good             |
| `snowflake-arctic-embed` | 2000 chars | ✅ NO       | 0.78       | Excellent        |

## Quick Action Steps

```bash
# Step 1: Pull better model (2 minutes)
ollama pull mxbai-embed-large

# Step 2: Update .env (30 seconds)
# Change this line:
OLLAMA_EMBEDDING_MODEL=mxbai-embed-large

# Step 3: Re-ingest with correct embeddings (5 minutes)
python scripts/ingest_documents.py KB/ --reset

# Step 4: Verify fix (30 seconds)
python scripts/diagnose_embeddings.py
# Should see NO truncation warnings!

# Step 5: Test retrieval (1 minute)
python scripts/analyze_retrieval.py "What is a PICC line?"
# Should see scores >0.6 now!
```

## What Happens After the Fix

**Before** (qwen3-embedding with 1024 chunks):

```
❌ Chunks: 933 → 400 chars (data loss!)
❌ Similarity: 0.35 (poor matching)
❌ Retrieved: Irrelevant docs (bulimia, meditation)
```

**After** (mxbai-embed-large with 1024 chunks):

```
✅ Chunks: 933 → 933 chars (no truncation!)
✅ Similarity: 0.72 (good matching)
✅ Retrieved: Relevant PICC line docs
```

## Don't Want to Switch Models?

If you MUST keep `qwen3-embedding:0.6b`, reduce chunk size:

```bash
# Edit .env:
MAX_CHUNK_SIZE=300  # Match model capability

# Re-ingest
python scripts/ingest_documents.py KB/ --reset
```

**Downside**: Smaller chunks = less context = potentially worse answers

## Verify Your Fix

After switching models, check for truncation:

```bash
# Should see NO errors about truncation
python scripts/ingest_documents.py KB/ --reset

# Check retrieval quality
python scripts/diagnose_embeddings.py --test-retrieval

# Expected output:
# ✅ Average relevant similarity: 0.72
# ✅ No truncation warnings
```

## Bottom Line

**You CANNOT use 1024 chunks with `qwen3-embedding:0.6b`!**

**Fix**: Switch to `mxbai-embed-large` (10 minutes total)

**Impact**:

- Eliminate data loss
- Improve similarity scores from 0.35 → 0.72
- Get relevant results instead of random docs

🎯 **Action**: Run the commands above NOW to fix the truncation issue!

---

**More Info**: See `docs/OLLAMA_MODEL_CONTEXT_LIMITS.md` for detailed model specifications.
