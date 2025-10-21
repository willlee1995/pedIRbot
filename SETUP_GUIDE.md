# Complete Setup Guide

## System Requirements

- **Python**: 3.9 or higher
- **RAM**: Minimum 8GB (16GB recommended for local models)
- **Storage**: 5GB+ free space (for models and vector database)
- **OS**: Windows, Linux, or macOS

## Installation Options

### Option 1: OpenAI Cloud (Recommended for Testing)

**Pros**: Fast, high-quality, easy setup
**Cons**: Requires API key, costs money, data goes to OpenAI

```bash
# 1. Install uv (fast Python package manager)
# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Create environment and install dependencies
uv venv
uv pip install -r requirements.txt

# 3. Activate environment
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# 4. Create .env file
copy env.example .env  # Windows
cp env.example .env  # Linux/Mac

# 5. Edit .env and add your OpenAI API key
OPENAI_API_KEY=sk-your-actual-key-here
EMBEDDING_PROVIDER=openai
LLM_PROVIDER=openai

# 6. Done! Skip to "Adding Documents" section
```

### Option 2: Ollama Local (Best for Privacy)

**Pros**: Free, private, no data leaves your machine
**Cons**: Slower, requires more setup, needs good GPU

```bash
# 1. Install Ollama
# Visit https://ollama.ai and download installer

# 2. Pull models
ollama pull alibayram/medgemma  # For medical LLM
# OR
ollama pull llama3              # General purpose
# OR
ollama pull mixtral             # High quality

# 3. Install uv and Python dependencies
# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create environment and install
uv venv
uv pip install -r requirements.txt

# 4. Activate environment
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# 5. Create .env file
copy env.example .env  # Windows
cp env.example .env  # Linux/Mac

# 6. Edit .env for Ollama
# Option A: Use Ollama embeddings (recommended for full privacy)
EMBEDDING_PROVIDER=ollama
OLLAMA_EMBEDDING_MODEL=embeddinggemma
LLM_PROVIDER=ollama
OLLAMA_CHAT_MODEL=alibayram/medgemma

# Option B: Use local Sentence Transformers
# EMBEDDING_PROVIDER=sentence-transformer
# SENTENCE_TRANSFORMER_MODEL=BAAI/bge-m3

# 7. Done!
```

### Option 3: Hybrid (OpenAI Embeddings + Ollama LLM)

**Pros**: Balance of quality and privacy
**Cons**: Requires both API key and Ollama

```bash
# 1. Install both Ollama (see Option 2) and setup Python environment
uv venv
uv pip install -r requirements.txt
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# 2. Edit .env
OPENAI_API_KEY=sk-your-key-here
EMBEDDING_PROVIDER=openai       # Use OpenAI for embeddings
LLM_PROVIDER=ollama             # Use Ollama for generation
OLLAMA_CHAT_MODEL=alibayram/medgemma
```

## Organizing Your Knowledge Base

### Directory Structure

Create folders for each source organization:

```
KB/
├── HKCH/               # Hong Kong Children's Hospital docs
│   ├── protocols/
│   └── patient_info/
├── SickKids/           # SickKids documents
│   └── procedures/
├── SIR/                # Society of Interventional Radiology
│   ├── patient_leaflets/
│   └── guidelines/
├── HKSIR/              # Hong Kong Society of IR
│   ├── english/
│   └── chinese/
└── CIRSE/              # CIRSE patient information
    └── leaflets/
```

### Supported File Formats

Using **MarkItDown** for unified conversion, the system supports:

- **PDF** (`.pdf`) - Most common for medical documents
- **Word** (`.docx`, `.doc`) - Editable documents
- **PowerPoint** (`.pptx`, `.ppt`) - Presentation files
- **Excel** (`.xlsx`, `.xls`, `.csv`) - Spreadsheets and data
- **HTML** (`.html`, `.htm`) - Web pages
- **Markdown** (`.md`) - Text-based documents
- **Plain Text** (`.txt`) - Simple text files
- **Images** (`.jpg`, `.png`) - With OCR capabilities (if available)
- **Audio** (`.mp3`, `.wav`) - With transcription (if available)

### Best Practices

1. **Use descriptive filenames**: `embolization_patient_guide_EN.pdf` not `doc1.pdf`
2. **Organize by source**: Helps with metadata filtering
3. **Include language in filename**: `leaflet_EN.pdf`, `leaflet_ZH.pdf`
4. **Keep originals**: Don't delete source PDFs after conversion

## First Run: Ingest Documents

```bash
# Make sure environment is activated
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Ingest all documents (first time - use --reset)
python scripts/ingest_documents.py KB/ --reset
```

Expected output:

```
INFO: Processing documents...
INFO: Found 25 files to process in KB
INFO: Processing: KB\HKCH\fasting_guide.pdf
INFO: Created 8 chunks from fasting_guide.pdf
...
INFO: Total chunks created: 156
INFO: Adding 156 chunks to vector store...
INFO: Successfully added 156 documents. Total count: 156
========================================
INGESTION COMPLETE
========================================
```

## Testing Your Setup

### 1. Quick Test - Interactive Chat

```bash
python test_chat.py
```

Try these test questions:

```
You: What is interventional radiology?
You: How long should a child fast?
You: 什麼是介入放射學？  (Chinese test)
You: stats  (Check system info)
You: quit  (Exit)
```

### 2. API Test

```bash
# Terminal 1 - Start server
python scripts/start_api.py --reload

# Terminal 2 - Test health
curl http://localhost:8000/health

# Terminal 2 - Test query
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"What are the risks of biopsy?\"}"
```

### 3. Evaluation Test

```bash
python scripts/run_evaluation.py test_data/sample_questions.json
```

Check `evaluation_results/` for outputs.

## Configuration Tuning

### For Better Accuracy

```env
# In .env
TOP_K_RETRIEVAL=7              # More context (default: 5)
HYBRID_ALPHA=0.8               # More semantic, less keyword
MAX_CHUNK_SIZE=768             # Larger chunks (default: 512)
```

### For Faster Responses

```env
TOP_K_RETRIEVAL=3              # Less context
OPENAI_CHAT_MODEL=gpt-4o-mini  # Faster model
```

### For Chinese Language Focus

```env
EMBEDDING_PROVIDER=sentence-transformer
SENTENCE_TRANSFORMER_MODEL=BAAI/bge-m3  # Excellent Chinese support
```

## Troubleshooting

### Issue: "No module named 'src'"

**Solution**: Make sure you're running from project root

```bash
cd D:\Development area\pedIRbot
python test_chat.py
```

### Issue: "Collection is empty"

**Solution**: Ingest documents

```bash
python scripts/ingest_documents.py KB/ --reset
```

### Issue: "OpenAI API key error"

**Solution**: Check `.env` file

```bash
# Make sure you have:
OPENAI_API_KEY=sk-...  # No quotes, no spaces
```

### Issue: "Ollama connection refused"

**Solution**: Start Ollama

```bash
# Check if running
ollama list

# If not installed, download from https://ollama.ai
```

### Issue: "Out of memory" when using local models

**Solutions**:

1. Use smaller model: `ollama pull llama3:8b`
2. Reduce chunk size: `MAX_CHUNK_SIZE=256`
3. Reduce retrieval: `TOP_K_RETRIEVAL=3`
4. Close other applications

### Issue: Slow embedding generation

**Solution**: Switch to OpenAI embeddings (much faster)

```env
EMBEDDING_PROVIDER=openai
OPENAI_EMBEDDING_MODEL=text-embedding-3-small  # Cheaper & faster
```

### Issue: UV network timeout during installation

**Symptom**: `Failed to download distribution due to network timeout`

**Solution**: Increase the timeout value

```bash
# Windows (PowerShell)
$env:UV_HTTP_TIMEOUT = "300"
uv pip install -r requirements.txt

# Linux/Mac
UV_HTTP_TIMEOUT=300 uv pip install -r requirements.txt

# For persistent setting, add to your shell profile:
export UV_HTTP_TIMEOUT=300
```

## Next Steps After Setup

1. **Add Your Documents**: Put real medical documents in `KB/`
2. **Ingest**: Run `python scripts/ingest_documents.py KB/ --reset`
3. **Test**: Use `test_chat.py` to verify accuracy
4. **Create Test Set**: Build comprehensive questions in JSON format
5. **Evaluate**: Run `scripts/run_evaluation.py` on your test set
6. **Compare Models**: Test different LLMs with `scripts/compare_models.py`
7. **Deploy**: Use FastAPI server for production testing

## Performance Expectations

### OpenAI Cloud

- **Embedding**: ~2-5 seconds per batch of 100 chunks
- **Query Response**: ~2-4 seconds
- **Accuracy**: Excellent

### Ollama Local (MedGemma3 on RTX 4090)

- **Embedding**: ~10-30 seconds per batch of 100 chunks
- **Query Response**: ~5-15 seconds
- **Accuracy**: Good to Excellent (model-dependent)

### Ollama Local (CPU only)

- **Embedding**: ~1-2 minutes per batch of 100 chunks
- **Query Response**: ~30-120 seconds
- **Not recommended** for interactive use

## Getting Help

1. Check `README.md` for full documentation
2. See `QUICKSTART.md` for 5-minute guide
3. Review log files for error details
4. Check API docs at `http://localhost:8000/docs`

## Security Notes

### For Production Deployment

1. **Never commit `.env`** - Contains API keys
2. **Use environment variables** - Don't hardcode keys
3. **Review prompts** - Medical disclaimers are critical
4. **Validate sources** - Only use approved medical documents
5. **Log queries** - For audit and improvement (anonymized)
6. **HIPAA compliance** - Consider Ollama for patient data
7. **Rate limiting** - Implement in production API

### API Key Security

```bash
# Good - in .env file (gitignored)
OPENAI_API_KEY=sk-...

# Bad - in code
api_key = "sk-..."  # Never do this!

# Good - environment variable (production)
export OPENAI_API_KEY=sk-...
```

---

**Ready?** Start with `QUICKSTART.md` for the fastest path to testing!
