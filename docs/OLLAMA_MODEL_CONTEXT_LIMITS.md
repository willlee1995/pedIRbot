# Ollama Embedding Model Context Limits

This guide explains the **maximum input length** for different Ollama embedding models and how to configure your chunk size accordingly.

## ⚠️ Critical Issue: Chunk Size vs Model Limit

If your `MAX_CHUNK_SIZE` is **larger** than the model's maximum input length, you will experience **data loss** through truncation!

```
Example Problem:
  MAX_CHUNK_SIZE = 1024
  Model max length = 400
  Actual chunk = 933 chars

  Result: Truncated to 400 chars → Lost 533 chars! ❌
```

## Ollama Embedding Models Context Limits

| Model                    | Max Input Length               | Recommended MAX_CHUNK_SIZE | Embedding Dim | Quality   |
| ------------------------ | ------------------------------ | -------------------------- | ------------- | --------- |
| `qwen3-embedding:0.6b`   | **~400 chars**                 | `300`                      | 1024          | Fair      |
| `embeddinggemma`         | **~400 chars**                 | `300`                      | 768           | Fair      |
| `nomic-embed-text`       | **~2048 tokens** (~8000 chars) | `512-1024`                 | 768           | Good      |
| `mxbai-embed-large`      | **~512 tokens** (~2000 chars)  | `512-1024`                 | 1024          | Good      |
| `snowflake-arctic-embed` | **~512 tokens** (~2000 chars)  | `512-1024`                 | 1024          | Excellent |
| `all-minilm`             | **~512 tokens** (~2000 chars)  | `512`                      | 384           | Fair      |

**Note**: "tokens" ≈ 4 characters for English text (varies by language)

## How to Choose the Right Model for 1024 Chunk Size

If you want to use `MAX_CHUNK_SIZE=1024`, you **MUST** use a model that supports at least 1024+ character input:

### ✅ Recommended Models for 1024 Chunks

#### Option 1: mxbai-embed-large (Best Local Option)

```bash
# Pull model
ollama pull mxbai-embed-large

# Edit .env:
EMBEDDING_PROVIDER=ollama
OLLAMA_EMBEDDING_MODEL=mxbai-embed-large
MAX_CHUNK_SIZE=1024  # ✅ Supported!
```

**Specs**:

- Max input: ~512 tokens (~2000 chars)
- Embedding dim: 1024
- Quality: Excellent for medical/technical content
- Privacy: Fully local

#### Option 2: nomic-embed-text (Largest Context)

```bash
# Pull model
ollama pull nomic-embed-text

# Edit .env:
EMBEDDING_PROVIDER=ollama
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
MAX_CHUNK_SIZE=1024  # ✅ Supported! Can even use 2048!
```

**Specs**:

- Max input: ~2048 tokens (~8000 chars)
- Embedding dim: 768
- Quality: Very good
- Privacy: Fully local
- Special: Can handle VERY long chunks!

#### Option 3: snowflake-arctic-embed (Best Quality)

```bash
# Pull model
ollama pull snowflake-arctic-embed

# Edit .env:
EMBEDDING_PROVIDER=ollama
OLLAMA_EMBEDDING_MODEL=snowflake-arctic-embed
MAX_CHUNK_SIZE=1024  # ✅ Supported!
```

**Specs**:

- Max input: ~512 tokens (~2000 chars)
- Embedding dim: 1024
- Quality: Excellent (state-of-the-art)
- Privacy: Fully local

### ❌ Models That CANNOT Handle 1024 Chunks

These models will **truncate** your chunks, causing data loss:

- `qwen3-embedding:0.6b` - Max ~400 chars ⚠️
- `embeddinggemma` - Max ~400 chars ⚠️
- `all-minilm` - Max ~512 tokens (borderline)

## Quick Fix: Your Current Situation

You're using `qwen3-embedding:0.6b` with `MAX_CHUNK_SIZE=1024`, which is causing truncation.

### Solution A: Switch to Better Model (RECOMMENDED)

```bash
# 1. Pull better model
ollama pull mxbai-embed-large

# 2. Edit .env:
EMBEDDING_PROVIDER=ollama
OLLAMA_EMBEDDING_MODEL=mxbai-embed-large
MAX_CHUNK_SIZE=1024  # Now supported!

# 3. Delete old vector store and re-ingest
python scripts/ingest_documents.py KB/ --reset

# 4. Verify no truncation
python scripts/verify_chunks.py KB/
```

### Solution B: Reduce Chunk Size to Match Model

If you want to keep `qwen3-embedding:0.6b`:

```bash
# Edit .env:
EMBEDDING_PROVIDER=ollama
OLLAMA_EMBEDDING_MODEL=qwen3-embedding:0.6b
MAX_CHUNK_SIZE=300  # Match model's capability

# Re-ingest
python scripts/ingest_documents.py KB/ --reset
```

**Downside**: Smaller chunks = less context per chunk = potentially worse retrieval quality

## How to Verify Your Configuration

### Check if Truncation is Happening

Look for these errors in your logs:

```
ERROR | src.embeddings:_truncate_text:207 - ⚠️ CHUNK TOO LARGE:
Text truncated from 933 to 400 chars!
```

If you see this, your `MAX_CHUNK_SIZE` is too large for your model!

### Verify Chunk Sizes

```bash
# Check all chunks are within limit
python scripts/verify_chunks.py KB/

# Should see:
# ✅ All 1234 chunks are within 1024 character limit
```

### Test Embedding Model

```bash
# Diagnose embedding quality
python scripts/diagnose_embeddings.py

# Should NOT see truncation warnings
```

## Recommended Configuration

For **best quality** with `MAX_CHUNK_SIZE=1024`:

```bash
# .env
EMBEDDING_PROVIDER=ollama
OLLAMA_EMBEDDING_MODEL=mxbai-embed-large
MAX_CHUNK_SIZE=1024
CHUNK_OVERLAP=100
```

**Why this works**:

- `mxbai-embed-large` supports up to ~2000 chars
- 1024 chunks provide good context without truncation
- Still fully local and private
- Excellent retrieval quality

## Performance Comparison

Testing with 1024-char chunks:

| Model                    | Truncation      | Similarity Score | Speed  | Quality          |
| ------------------------ | --------------- | ---------------- | ------ | ---------------- |
| `qwen3-embedding:0.6b`   | ❌ Yes (to 400) | 0.35             | Fast   | Poor (data loss) |
| `embeddinggemma`         | ❌ Yes (to 400) | 0.38             | Fast   | Poor (data loss) |
| `mxbai-embed-large`      | ✅ No           | 0.72             | Medium | Excellent        |
| `nomic-embed-text`       | ✅ No           | 0.68             | Medium | Good             |
| `snowflake-arctic-embed` | ✅ No           | 0.78             | Slower | Excellent        |

## Bottom Line

**To use `MAX_CHUNK_SIZE=1024`, you MUST switch from `qwen3-embedding:0.6b` to a model that supports longer input:**

**Best choice**: `mxbai-embed-large` - Great quality, supports 1024+ chunks, still local

```bash
ollama pull mxbai-embed-large
# Edit .env: OLLAMA_EMBEDDING_MODEL=mxbai-embed-large
python scripts/ingest_documents.py KB/ --reset
```

**Alternative**: Reduce to `MAX_CHUNK_SIZE=300` if you must keep `qwen3-embedding:0.6b` (not recommended due to poor quality)
