# Quick Start Guide

Get the PedIR RAG Backend up and running in 5 minutes.

## Step 1: Install (2 minutes)

```bash
# Clone and navigate
cd pedIRbot

# Install uv (fast Python package manager)
# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create environment and install dependencies
uv venv
uv pip install -r requirements.txt

# Activate environment
# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

## Step 2: Configure (1 minute)

Create a `.env` file:

```bash
# For OpenAI (easiest to start)
OPENAI_API_KEY=sk-your-key-here
OPENAI_EMBEDDING_MODEL=text-embedding-3-large
OPENAI_CHAT_MODEL=gpt-4o

EMBEDDING_PROVIDER=openai
LLM_PROVIDER=openai
```

**OR** for Ollama (local, no API key needed):

```bash
# First, install Ollama and pull models:
# ollama pull alibayram/medgemma
# ollama pull embeddinggemma

OLLAMA_API_BASE=http://localhost:11434
OLLAMA_CHAT_MODEL=alibayram/medgemma
OLLAMA_EMBEDDING_MODEL=embeddinggemma

EMBEDDING_PROVIDER=ollama  # Use Ollama for embeddings too!
LLM_PROVIDER=ollama

# Important: embeddinggemma needs smaller chunks
MAX_CHUNK_SIZE=300
```

## Step 3: Add Documents (30 seconds)

Put your documents (PDF/DOCX/PPTX/XLSX/HTML/Markdown/images) in the `KB/` folder:

```
KB/
├── HKCH/your-document.pdf
├── SIR/another-document.docx
└── HKSIR/info.md
```

## Step 4: Verify Chunks (Optional - 10 seconds)

```bash
# Recommended: Check chunks are properly sized
python scripts/verify_chunks.py KB/
```

You should see:

```
✅ SUCCESS: All chunks are within the size limit!
Average size: 287 chars
Maximum size: 300 chars
```

## Step 5: Ingest Documents (30 seconds - 2 minutes)

```bash
python scripts/ingest_documents.py KB/ --reset
```

You should see:

```
INFO: Created 45 chunks from doc.pdf (avg: 287 chars, max: 300 chars)
INFO: Processing batch 1/5
INFO: Successfully added 245 documents. Total count: 245
════════════════════════════════════════════════
INGESTION COMPLETE
════════════════════════════════════════════════
```

**⚠️ Important**: You should NOT see many truncation ERROR messages. If you do, see `IMPORTANT_FIX_README.md` or `docs/CHUNKING_EXPLAINED.md`

## Step 6: Test! (30 seconds)

### Option A: Interactive Chat

```bash
python test_chat.py
```

Then ask questions:

```
You: How long should my child fast before the procedure?
PedIR-Bot: [detailed answer based on your documents]
```

### Option B: API Server

```bash
# Terminal 1: Start server
python scripts/start_api.py --reload

# Terminal 2: Test
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the risks?"}'
```

Visit `http://localhost:8000/docs` for interactive API documentation.

## Next Steps

### Run Evaluation

```bash
python scripts/run_evaluation.py test_data/sample_questions.json
```

### Compare Models

Edit `scripts/compare_models.py` to add your models, then:

```bash
python scripts/compare_models.py test_data/sample_questions.json
```

### Switch to MedGemma (Ollama)

```bash
# Install Ollama
# Download from https://ollama.ai

# Pull models
ollama pull alibayram/medgemma
ollama pull embeddinggemma

# Update .env
# EMBEDDING_PROVIDER=ollama
# OLLAMA_EMBEDDING_MODEL=embeddinggemma
# LLM_PROVIDER=ollama
# OLLAMA_CHAT_MODEL=alibayram/medgemma
# MAX_CHUNK_SIZE=300

# Test
python test_chat.py
```

## Troubleshooting

### "No documents in vector store"

→ Run ingestion: `python scripts/ingest_documents.py KB/ --reset`

### "OpenAI API error"

→ Check your API key in `.env`

### "Ollama connection failed"

→ Make sure Ollama is running: `ollama list`

### "Module not found"

→ Activate environment: `.venv\Scripts\activate` (Windows) or `source .venv/bin/activate` (Linux/Mac)

### "Network timeout" during installation

→ Increase UV timeout:

```bash
# Windows (PowerShell)
$env:UV_HTTP_TIMEOUT = "300"
uv pip install -r requirements.txt

# Linux/Mac
UV_HTTP_TIMEOUT=300 uv pip install -r requirements.txt
```

## Common Commands

```bash
# Ingest documents
python scripts/ingest_documents.py KB/

# Interactive testing
python test_chat.py

# Start API server
python scripts/start_api.py --reload

# Run evaluation
python scripts/run_evaluation.py test_data/sample_questions.json

# Compare models
python scripts/compare_models.py test_data/sample_questions.json
```

## Configuration Tips

### Improve Retrieval Quality

In `.env`, adjust:

```bash
TOP_K_RETRIEVAL=5          # More = more context
HYBRID_ALPHA=0.7           # 0.0 = pure keyword, 1.0 = pure semantic
MAX_CHUNK_SIZE=512         # Larger = more context per chunk
```

### Speed vs Quality

- **Fastest**: `gpt-4o-mini` + `text-embedding-3-small`
- **Best Quality**: `gpt-4o` + `text-embedding-3-large`
- **Privacy**: Ollama with local models
- **Balanced**: `gpt-4o-mini` + `text-embedding-3-large`

## Need Help?

1. Check logs for errors
2. Verify `.env` configuration
3. Test vector store: `curl http://localhost:8000/stats`
4. See full README.md for advanced features

---

**Ready to go?** Start with `python test_chat.py` and ask your first question!
