# Embedding Model Selection Guide

## Quick Reference Table

| Model                  | Provider              | Chunk Size | Speed  | Privacy | Cost | Best For           |
| ---------------------- | --------------------- | ---------- | ------ | ------- | ---- | ------------------ |
| text-embedding-3-large | OpenAI                | 512-8192   | ⚡⚡⚡ | ❌      | \$\$ | Production quality |
| text-embedding-3-small | OpenAI                | 512-8192   | ⚡⚡⚡ | ❌      | \$   | Fast & cheap       |
| embeddinggemma         | Ollama                | **300**    | ⚡⚡   | ✅      | Free | Medical content    |
| mxbai-embed-large      | Ollama                | 512-768    | ⚡     | ✅      | Free | High quality local |
| nomic-embed-text       | Ollama                | 512        | ⚡⚡   | ✅      | Free | Fast local         |
| BGE-M3                 | Sentence Transformers | 512-1024   | ⚡⚡   | ✅      | Free | Multilingual       |

## Configuration by Model

### embeddinggemma (Current Setup)

**Best for**: Medical/scientific content, Gemma ecosystem

```bash
# .env configuration
EMBEDDING_PROVIDER=ollama
OLLAMA_EMBEDDING_MODEL=embeddinggemma
MAX_CHUNK_SIZE=300  # ⚠️ CRITICAL - Must be 300 or less
CHUNK_OVERLAP=50
```

**Pros**:

- Optimized for medical/scientific text
- Integrates with MedGemma3 LLM
- Completely private
- Free

**Cons**:

- Small context window (~400-512 chars)
- Requires smaller chunks
- Slower than OpenAI

**Setup**:

```bash
ollama pull embeddinggemma
```

### mxbai-embed-large

**Best for**: General purpose, high quality local embeddings

```bash
# .env configuration
EMBEDDING_PROVIDER=ollama
OLLAMA_EMBEDDING_MODEL=mxbai-embed-large
MAX_CHUNK_SIZE=512  # Can go up to 768
CHUNK_OVERLAP=50
```

**Pros**:

- High quality (comparable to OpenAI)
- Larger context window
- Completely private
- Free

**Cons**:

- Larger model size (~669MB)
- Slower embedding generation

**Setup**:

```bash
ollama pull mxbai-embed-large
```

### OpenAI text-embedding-3-large

**Best for**: Production, highest quality

```bash
# .env configuration
EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
OPENAI_EMBEDDING_MODEL=text-embedding-3-large
MAX_CHUNK_SIZE=512  # Can go up to 8192
CHUNK_OVERLAP=50
```

**Pros**:

- State-of-the-art quality
- Very fast
- Large context window
- Excellent multilingual support

**Cons**:

- Requires API key
- Costs money (~\$0.13 per 1M tokens)
- Data sent to OpenAI

### BGE-M3 (Sentence Transformers)

**Best for**: Multilingual content, offline use

```bash
# .env configuration
EMBEDDING_PROVIDER=sentence-transformer
SENTENCE_TRANSFORMER_MODEL=BAAI/bge-m3
MAX_CHUNK_SIZE=512
CHUNK_OVERLAP=50
```

**Pros**:

- Excellent multilingual support (EN/ZH)
- Completely offline
- Free
- Good quality

**Cons**:

- Large download (~2GB)
- Slower than OpenAI
- High memory usage

## Chunk Size Guidelines

### Why Chunk Size Matters

Embedding models have a **maximum context length** (in tokens, not characters). If your text exceeds this limit, the embedding will fail or be truncated.

### Recommended Settings

| Model             | MIN Chunk | MAX Chunk | OPTIMAL     |
| ----------------- | --------- | --------- | ----------- |
| embeddinggemma    | 100       | **300**   | **250-300** |
| mxbai-embed-large | 200       | 768       | 512         |
| nomic-embed-text  | 200       | 512       | 400         |
| OpenAI (3-large)  | 200       | 8192      | 512-1024    |
| BGE-M3            | 200       | 1024      | 512         |

### Setting Chunk Size

In your `.env` file:

```bash
# For embeddinggemma - REQUIRED
MAX_CHUNK_SIZE=300

# For larger models - OPTIONAL
# MAX_CHUNK_SIZE=512
```

## Troubleshooting Context Length Errors

### Error: "input length exceeds the context length"

**Symptom**: Embedding fails during document ingestion

**Immediate Fix**:

```bash
# 1. Stop the ingestion (Ctrl+C)

# 2. Edit .env
MAX_CHUNK_SIZE=300  # Or smaller

# 3. Restart ingestion
python scripts/ingest_documents.py KB/ --reset
```

**Permanent Fix**: The code now automatically truncates chunks that are too long, but it's better to set the right chunk size from the start.

### Verification

After changing chunk size, verify:

```python
from config import settings
print(f"Current chunk size: {settings.max_chunk_size}")
# Should print: Current chunk size: 300
```

## Switching Between Models

### From embeddinggemma to mxbai-embed-large

```bash
# 1. Pull the new model
ollama pull mxbai-embed-large

# 2. Edit .env
OLLAMA_EMBEDDING_MODEL=mxbai-embed-large
MAX_CHUNK_SIZE=512  # Can increase chunk size

# 3. Re-ingest documents (embeddings are different!)
python scripts/ingest_documents.py KB/ --reset
```

### From Ollama to OpenAI

```bash
# 1. Edit .env
EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
OPENAI_EMBEDDING_MODEL=text-embedding-3-large
MAX_CHUNK_SIZE=512  # Can increase

# 2. Re-ingest documents
python scripts/ingest_documents.py KB/ --reset
```

## Performance Optimization

### For Speed (Development/Testing)

```bash
EMBEDDING_PROVIDER=openai
OPENAI_EMBEDDING_MODEL=text-embedding-3-small  # Cheaper & faster
MAX_CHUNK_SIZE=512
```

### For Quality (Production)

```bash
EMBEDDING_PROVIDER=openai
OPENAI_EMBEDDING_MODEL=text-embedding-3-large
MAX_CHUNK_SIZE=512
```

### For Privacy (Clinical Deployment)

```bash
EMBEDDING_PROVIDER=ollama
OLLAMA_EMBEDDING_MODEL=mxbai-embed-large  # Better than embeddinggemma
MAX_CHUNK_SIZE=512
```

### For Medical Content (Specialized)

```bash
EMBEDDING_PROVIDER=ollama
OLLAMA_EMBEDDING_MODEL=embeddinggemma
MAX_CHUNK_SIZE=300  # ⚠️ Must be 300 or less
```

## Best Practices

### 1. Match Chunk Size to Model

Always set `MAX_CHUNK_SIZE` appropriate for your embedding model:

```bash
# embeddinggemma
MAX_CHUNK_SIZE=300

# mxbai, nomic, BGE-M3
MAX_CHUNK_SIZE=512

# OpenAI
MAX_CHUNK_SIZE=512  # or higher
```

### 2. Re-ingest After Changing Models

**IMPORTANT**: Different embedding models create different vector representations. Always re-ingest when switching:

```bash
python scripts/ingest_documents.py KB/ --reset
```

### 3. Test Before Production

Test retrieval quality after changing embedding models:

```bash
python test_chat.py
# Ask several test questions
# Verify responses are still accurate
```

## FAQ

**Q: Why does embeddinggemma have a smaller context limit?**
A: It's a smaller, more specialized model designed for efficiency. The trade-off is a smaller context window.

**Q: Will smaller chunks hurt retrieval quality?**
A: Not necessarily. Smaller chunks can actually improve precision if they're well-structured. The system uses overlap to maintain context.

**Q: Can I use different chunk sizes for different documents?**
A: Not currently. All documents use the same `MAX_CHUNK_SIZE` setting.

**Q: What happens if I don't reduce chunk size for embeddinggemma?**
A: The new code will automatically truncate, but it's better to set the right size to avoid information loss.

---

**Current Setup**: You're using `embeddinggemma` → Set `MAX_CHUNK_SIZE=300` in `.env`! ✅
