# PedIR RAG Backend

A comprehensive Retrieval-Augmented Generation (RAG) testing backend for a Pediatric Interventional Radiology Patient Education Chatbot, designed for Hong Kong Children's Hospital (HKCH).

## Overview

This system implements a production-ready RAG pipeline based on the research document `research.md`. It includes:

- **Document Processing**: Multi-format support (PDF, DOCX, PPTX, XLSX, HTML, images, audio) with MarkItDown conversion and intelligent chunking
- **Hybrid Retrieval**: Combines semantic (vector) search with keyword (BM25) search
- **Flexible LLM Integration**: Supports both OpenAI-compatible APIs and Ollama for local models
- **Bilingual Support**: Optimized for English and Traditional Chinese
- **Comprehensive Evaluation**: Built-in framework for testing and comparing models
- **Production-Ready API**: FastAPI server for deployment and testing

## Features

### ✨ Core Capabilities

- **Multiple Embedding Models**: OpenAI `text-embedding-3-large`, Sentence Transformers (BGE-M3), Ollama (mxbai-embed-large, nomic-embed-text)
- **Multiple LLM Providers**: OpenAI GPT models, Google Gemini, Ollama (alibayram/medgemma, Llama3, etc.)
- **Hybrid Retrieval**: Semantic + BM25 keyword search with configurable weighting
- **Safety Features**: Emergency keyword detection, medical disclaimer enforcement
- **Source Organization**: Automatic detection and tagging of documents from HKCH, SickKids, SIR, HKSIR, CIRSE

### 🏥 High-Quality Q&A Curation with MedGemma

NEW: Generate clinically accurate, parent-friendly Q&A pairs automatically using MedGemma!

```bash
# One command to generate 10 SIR standard questions for all procedures
python scripts/curate_with_medgemma.py

# Outputs XML files ready for RAG integration
```

**Features:**
- 🧠 Uses MedGemma medical LLM (or OpenAI GPT-4) for accurate answers
- 📋 Generates 10 SIR standard pediatric IR questions per procedure
- 📚 Processes all markdown documents (HKSIR, SickKids, etc.)
- 🔄 Intelligent context extraction and matching
- 💾 Structured XML output for RAG integration
- 🔧 Supports both local (free) and cloud-based LLMs

**Quick start:** See [MEDGEMMA_QUICKSTART.md](MEDGEMMA_QUICKSTART.md) for 5-minute setup

**Details:** Full guide at [MEDGEMMA_CURATION_GUIDE.md](MEDGEMMA_CURATION_GUIDE.md)

### 🔬 Evaluation & Testing

- Question-based evaluation with metrics tracking
- Multi-model comparison framework
- Excel export for manual expert review
- Latency and performance monitoring

## Project Structure

```
pedIRbot/
├── src/
│   ├── __init__.py
│   ├── document_processor.py    # Document loading and chunking
│   ├── embeddings.py            # Embedding model implementations
│   ├── vector_store.py          # ChromaDB vector database
│   ├── retriever.py             # Hybrid retrieval system
│   ├── llm.py                   # LLM provider integrations
│   ├── rag_pipeline.py          # Main RAG pipeline
│   ├── evaluation.py            # Evaluation framework
│   └── api.py                   # FastAPI server
├── scripts/
│   ├── ingest_documents.py      # Document ingestion script
│   ├── run_evaluation.py        # Evaluation runner
│   └── compare_models.py        # Model comparison
├── test_data/
│   └── sample_questions.json    # Sample test questions
├── KB/                          # Knowledge base folder (create this)
│   ├── HKCH/
│   ├── SickKids/
│   ├── SIR/
│   ├── HKSIR/
│   └── CIRSE/
├── config.py                    # Configuration management
├── requirements.txt             # Python dependencies
├── test_chat.py                 # Interactive testing interface
└── README.md                    # This file
```

## Installation

### 1. Prerequisites

- Python 3.9+
- **UV** (recommended for fast package management) - [Installation Guide](docs/UV_GUIDE.md)
- For local models: Ollama installed and running
- For OpenAI: Valid API key

### 2. Install Dependencies

We recommend using **`uv`** for fast, reliable Python package management:

```bash
# Install uv (if not already installed)
# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies with uv
uv venv
uv pip install -r requirements.txt

# Activate the environment
# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

<details>
<summary>Alternative: Traditional pip installation</summary>

```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

</details>

### 3. Configure Environment

Copy `.env.example` to `.env` and configure:

```bash
# For OpenAI
OPENAI_API_KEY=your_key_here
OPENAI_EMBEDDING_MODEL=text-embedding-3-large
OPENAI_CHAT_MODEL=gpt-4o

# For Ollama (if using local models)
OLLAMA_API_BASE=http://localhost:11434
OLLAMA_CHAT_MODEL=alibayram/medgemma

# Choose providers
EMBEDDING_PROVIDER=openai  # or sentence-transformer
LLM_PROVIDER=openai        # or ollama
```

## Usage

### Step 1: Prepare Knowledge Base

Organize your documents in the `KB/` folder:

```
KB/
├── HKCH/
│   ├── procedure_guide.pdf
│   └── fasting_instructions.docx
├── SickKids/
│   ├── patient_info.md
│   └── scraped_content.html  # From web scraper
├── SIR/
│   ├── embolization.pdf
├── HKSIR/
│   ├── leaflet_en.pdf
│   └── leaflet_zh.pdf
└── CIRSE/
    └── patient_info.pdf
```

**Optional: Scrape SickKids Content**

```bash
# Add URLs to KB/SickKids/urls_to_scrape.txt, then:
python scripts/scrape_sickkids.py --mode manual --urls-file KB/SickKids/urls_to_scrape.txt

# See docs/SCRAPING_GUIDE.md for details
```

### Step 2: Ingest Documents

```bash
# Ingest all documents (first time)
python scripts/ingest_documents.py KB/ --reset

# Add new documents (without resetting)
python scripts/ingest_documents.py KB/
```

### Step 3: Test the System

#### Interactive Chat

```bash
python test_chat.py
```

Example session:

```
You: How long should my child fast before the procedure?
PedIR-Bot: Based on standard guidelines, your child should typically...
[Sources: 3 documents]
  1. HKCH - fasting_instructions.pdf (score: 0.892)
  ...
```

#### API Server

```bash
# Start the server
uvicorn src.api:app --reload

# Test with curl
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the risks of embolization?"}'
```

API documentation available at: `http://localhost:8000/docs`

### Step 4: Run Evaluation

#### Single Model Evaluation

```bash
python scripts/run_evaluation.py test_data/sample_questions.json
```

This will generate:

- `evaluation_results/results_[model]_[timestamp].json` - Full results
- `evaluation_results/report_[model]_[timestamp].json` - Summary statistics
- `evaluation_results/results_[model]_[timestamp].xlsx` - Excel for manual review

#### Compare Multiple Models

Edit `scripts/compare_models.py` to configure models, then run:

```bash
python scripts/compare_models.py test_data/sample_questions.json
```

## Configuration

### Key Settings in `.env`

| Setting              | Description                           | Options                          |
| -------------------- | ------------------------------------- | -------------------------------- |
| `EMBEDDING_PROVIDER` | Embedding model provider              | `openai`, `sentence-transformer` |
| `LLM_PROVIDER`       | LLM provider                          | `openai`, `ollama`               |
| `TOP_K_RETRIEVAL`    | Number of documents to retrieve       | Default: 5                       |
| `HYBRID_ALPHA`       | Weight for semantic vs keyword search | 0.0-1.0 (default: 0.7)           |
| `MAX_CHUNK_SIZE`     | Document chunk size                   | Default: 512 characters          |

### Using MedGemma with Ollama

1. Install Ollama from https://ollama.ai
2. Pull the model:
   ```bash
   ollama pull alibayram/medgemma
   ```
3. Set in `.env`:
   ```
   LLM_PROVIDER=ollama
   OLLAMA_CHAT_MODEL=alibayram/medgemma
   ```

### Using OpenAI-Compatible APIs

For Gemini or other OpenAI-compatible endpoints:

```python
# In .env or config
OPENAI_API_BASE=https://your-endpoint.com/v1
OPENAI_API_KEY=your_key
OPENAI_CHAT_MODEL=your-model-name
```

## Evaluation Metrics

The system tracks:

- **Accuracy**: Factual correctness (1-6 scale, manual review)
- **Relevance**: How well response addresses query (1-6 scale, manual review)
- **Completeness**: Information completeness (1-3 scale, manual review)
- **Latency**: Response time in seconds (automatic)
- **Topic Coverage**: Percentage of expected topics covered (automatic)

## Advanced Features

### Custom Metadata Filtering

```python
# Filter by source organization
result = rag_pipeline.generate_response(
    query="What is embolization?",
    filter_dict={"source_org": "HKSIR"}
)
```

### Streaming Responses

```python
for chunk in rag_pipeline.stream_response(query="..."):
    if chunk['type'] == 'response':
        print(chunk['content'], end='', flush=True)
```

### Rebuilding BM25 Index

After adding documents:

```python
# Via API
curl -X POST "http://localhost:8000/rebuild-index"

# Or in code
retriever.rebuild_bm25_index()
```

## Safety & Medical Compliance

### Built-in Safeguards

1. **Emergency Keyword Detection**: Automatically detects emergency-related queries and provides appropriate guidance
2. **Grounding Enforcement**: LLM only uses information from retrieved context
3. **Medical Disclaimers**: Every response includes educational-only disclaimer
4. **No Medical Advice**: System forbidden from providing diagnosis or treatment recommendations

### Bilingual Support

- Automatically detects query language (English/Chinese)
- Generates response in matching language
- Supports Traditional Chinese characters
- Uses BGE-M3 or multilingual embeddings for cross-language understanding

## Troubleshooting

### No documents in vector store

```bash
# Check stats
curl http://localhost:8000/stats

# Reingest with reset
python scripts/ingest_documents.py KB/ --reset
```

### Ollama connection error

```bash
# Check Ollama is running
ollama list

# Verify API endpoint
curl http://localhost:11434/api/tags
```

### Poor retrieval quality

- Adjust `HYBRID_ALPHA` (higher = more semantic, lower = more keyword)
- Increase `TOP_K_RETRIEVAL` for more context
- Try different embedding models

## Research Background

This implementation is based on the comprehensive research plan in `research.md`, which outlines:

- Multi-phase knowledge base construction (sourcing, localization, pediatric adaptation)
- Rigorous validation protocol (internal validation, external expert review, focus groups)
- Ethical considerations for clinical deployment
- Governance and maintenance protocols

## Documentation

For detailed guides, see the documentation files:

- **[CLEANUP_WORKFLOW.md](CLEANUP_WORKFLOW.md)** - 🧹 **Clean SickKids HTML metadata pollution**
- **[docs/TWO_STAGE_INGESTION.md](docs/TWO_STAGE_INGESTION.md)** - 📝 **Two-stage ingestion workflow (convert → inspect → embed)**
- **[URGENT_FIX_CHUNK_SIZE.md](URGENT_FIX_CHUNK_SIZE.md)** - 🚨 **Fix chunk truncation (data loss!)**
- **[FIX_LOW_SCORES.md](FIX_LOW_SCORES.md)** - 🚨 **Fixing low similarity scores (<0.5)**
- **[QUICKSTART.md](QUICKSTART.md)** - Get started in 5 minutes
- **[SETUP_GUIDE.md](SETUP_GUIDE.md)** - Detailed installation and configuration
- **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** - Architecture overview
- **[UV_GUIDE.md](docs/UV_GUIDE.md)** - Using `uv` for environment management
- **[MARKITDOWN_GUIDE.md](docs/MARKITDOWN_GUIDE.md)** - Document conversion guide
- **[OLLAMA_EMBEDDINGS.md](docs/OLLAMA_EMBEDDINGS.md)** - Using Ollama embedding models
- **[OLLAMA_MODEL_CONTEXT_LIMITS.md](docs/OLLAMA_MODEL_CONTEXT_LIMITS.md)** - Model context limits and chunk sizing
- **[EMBEDDING_MODEL_GUIDE.md](docs/EMBEDDING_MODEL_GUIDE.md)** - Choosing and configuring embedding models
- **[LOW_SIMILARITY_TROUBLESHOOTING.md](docs/LOW_SIMILARITY_TROUBLESHOOTING.md)** - Troubleshooting retrieval quality
- **[RETRIEVAL_ANALYSIS_GUIDE.md](docs/RETRIEVAL_ANALYSIS_GUIDE.md)** - Analyzing matched documents in detail
- **[MARKDOWN_PREVIEW_GUIDE.md](docs/MARKDOWN_PREVIEW_GUIDE.md)** - Preview document conversions before ingestion
- **[SCRAPING_GUIDE.md](docs/SCRAPING_GUIDE.md)** - Web scraping for knowledge base content

## Contributing

To add new features:

1. Create feature branch
2. Add tests to `test_data/`
3. Update documentation
4. Submit pull request

## License

[Your License Here]

## Contact

For questions about this implementation, contact the HKCH Radiology development team.

---

**Note**: This is a testing backend. Before clinical deployment, complete all validation phases outlined in `research.md`, obtain institutional review board approval, and implement full governance protocols.
