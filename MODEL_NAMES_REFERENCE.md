# Model Names Reference

## Correct Ollama Model Names

### LLM Models

| Description                | Correct Name         | Pull Command                     |
| -------------------------- | -------------------- | -------------------------------- |
| **MedGemma (Medical LLM)** | `alibayram/medgemma` | `ollama pull alibayram/medgemma` |
| Llama 3                    | `llama3`             | `ollama pull llama3`             |
| Llama 3.1                  | `llama3.1`           | `ollama pull llama3.1`           |
| Mixtral                    | `mixtral`            | `ollama pull mixtral`            |
| Gemma 2                    | `gemma2`             | `ollama pull gemma2`             |

### Embedding Models

| Description          | Correct Name             | Pull Command                         |
| -------------------- | ------------------------ | ------------------------------------ |
| **Gemma Embeddings** | `embeddinggemma`         | `ollama pull embeddinggemma`         |
| mxbai Large          | `mxbai-embed-large`      | `ollama pull mxbai-embed-large`      |
| Nomic Embed          | `nomic-embed-text`       | `ollama pull nomic-embed-text`       |
| Snowflake Arctic     | `snowflake-arctic-embed` | `ollama pull snowflake-arctic-embed` |
| all-MiniLM           | `all-minilm`             | `ollama pull all-minilm`             |

## Current PedIR Configuration

### Recommended Setup (Medical Focus)

```bash
# .env
EMBEDDING_PROVIDER=ollama
OLLAMA_EMBEDDING_MODEL=embeddinggemma

LLM_PROVIDER=ollama
OLLAMA_CHAT_MODEL=alibayram/medgemma

MAX_CHUNK_SIZE=300  # Required for embeddinggemma
```

### Pull Commands

```bash
# Pull both models
ollama pull alibayram/medgemma
ollama pull embeddinggemma

# Verify they're available
ollama list
```

## Why These Model Names?

### alibayram/medgemma

- **Full name**: `alibayram/medgemma` (community model)
- **NOT** `medgemma3` (doesn't exist)
- **NOT** `medgemma` (refers to a different model)
- **Source**: Custom medical fine-tune by alibayram
- **Use case**: Medical question-answering

### embeddinggemma

- **Full name**: `embeddinggemma` (official Google model)
- **NOT** `gemma-embeddings` or `embedding-gemma`
- **Source**: Google's official embedding model
- **Use case**: Text embeddings for retrieval

## Common Mistakes

### ❌ Wrong Names

```bash
ollama pull medgemma3           # Doesn't exist
ollama pull medgemma            # Different model
ollama pull gemma-embeddings    # Doesn't exist
```

### ✅ Correct Names

```bash
ollama pull alibayram/medgemma  # Medical LLM ✓
ollama pull embeddinggemma      # Embeddings ✓
```

## Verify Your Installation

```bash
# List all installed models
ollama list

# You should see:
# alibayram/medgemma:latest
# embeddinggemma:latest
```

## Model Information

### alibayram/medgemma

```bash
# Get model info
ollama show alibayram/medgemma

# Test it
ollama run alibayram/medgemma "What is interventional radiology?"
```

### embeddinggemma

```bash
# Test embeddings
ollama embeddings embeddinggemma "test text"
```

## Configuration Templates

### Template 1: Full Medical Stack

```bash
# .env
EMBEDDING_PROVIDER=ollama
OLLAMA_EMBEDDING_MODEL=embeddinggemma
LLM_PROVIDER=ollama
OLLAMA_CHAT_MODEL=alibayram/medgemma
MAX_CHUNK_SIZE=300
```

### Template 2: Hybrid (Quality Embeddings + Medical LLM)

```bash
# .env
EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=sk-your-key
LLM_PROVIDER=ollama
OLLAMA_CHAT_MODEL=alibayram/medgemma
MAX_CHUNK_SIZE=512
```

### Template 3: Development/Testing

```bash
# .env - Fast OpenAI models
EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=sk-your-key
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
LLM_PROVIDER=openai
OPENAI_CHAT_MODEL=gpt-4o-mini
MAX_CHUNK_SIZE=512
```

## Quick Reference

| What You Want      | Model Name           | Config Setting                             |
| ------------------ | -------------------- | ------------------------------------------ |
| Medical LLM        | `alibayram/medgemma` | `OLLAMA_CHAT_MODEL=alibayram/medgemma`     |
| Medical Embeddings | `embeddinggemma`     | `OLLAMA_EMBEDDING_MODEL=embeddinggemma`    |
| General LLM        | `llama3.1`           | `OLLAMA_CHAT_MODEL=llama3.1`               |
| Quality Embeddings | `mxbai-embed-large`  | `OLLAMA_EMBEDDING_MODEL=mxbai-embed-large` |
| Fast Embeddings    | `nomic-embed-text`   | `OLLAMA_EMBEDDING_MODEL=nomic-embed-text`  |

---

**Always use the exact model names as shown in this reference!** 🎯
