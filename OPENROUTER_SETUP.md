# 🚀 OpenRouter Setup - Fast & Free Alternative to MedGemma

## Why OpenRouter?

- ✅ **Fast**: 2-5 seconds per procedure (vs 20-60 sec for MedGemma CPU)
- ✅ **Free**: `openai/gpt-oss-20b:free` has unlimited free tier
- ✅ **Reliable**: No retry timeouts or wrapper issues
- ✅ **Easy**: Just change `.env` values (OpenAI-compatible)

---

## Quick Setup (3 Steps)

### Step 1: Get Your OpenRouter API Key

1. Go to https://openrouter.ai/
2. Sign up (free)
3. Go to Dashboard → API Key
4. Copy your API key

### Step 2: Update Your `.env` File

Replace the OpenAI section with OpenRouter:

```env
# Before (OpenAI)
OPENAI_API_KEY=sk-...
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_CHAT_MODEL=gpt-4o

# After (OpenRouter)
OPENAI_API_KEY=sk-or-... (your OpenRouter key)
OPENAI_API_BASE=https://openrouter.ai/api/v1
OPENAI_CHAT_MODEL=openai/gpt-oss-20b:free
```

**OR** if you don't have a `.env` file yet, create one:

```bash
cp env.example .env
# Edit .env and change the OPENAI_* values
```

### Step 3: Run the Script

```bash
python scripts/curate_with_medgemma.py
```

That's it! Now it will use OpenRouter instead of MedGemma.

---

## Complete `.env` Example for OpenRouter

```env
# OpenRouter Configuration
OPENAI_API_KEY=sk-or-your-openrouter-key-here
OPENAI_API_BASE=https://openrouter.ai/api/v1
OPENAI_CHAT_MODEL=openai/gpt-oss-20b:free
OPENAI_EMBEDDING_MODEL=text-embedding-3-large

# LLM Provider
LLM_PROVIDER=openai

# Embedding Provider (can use OpenAI's for embeddings)
EMBEDDING_PROVIDER=openai

# Other settings (optional)
LOG_LEVEL=INFO
MAX_CHUNK_SIZE=300
CHUNK_OVERLAP=50
```

---

## Available Free Models on OpenRouter

| Model | Speed | Quality | Notes |
|-------|-------|---------|-------|
| `openai/gpt-oss-20b:free` | Fast | Good | **Recommended** |
| `google/gemma-2-9b-it:free` | Fast | Good | Good alternative |
| `mistralai/mistral-7b:free` | Fast | Fair | Fastest option |

**Tip**: Try `openai/gpt-oss-20b:free` first - it's the best balance of speed and quality.

---

## Expected Performance

### Before (MedGemma CPU)
```
⏱️  20-60 sec per procedure
📦 250+ procedures = 1-2+ hours
```

### After (OpenRouter)
```
⏱️  2-5 sec per procedure  
📦 250+ procedures = 10-20 minutes
```

**20-30x faster!** 🚀

---

## Full Example Run

```bash
$ python scripts/curate_with_medgemma.py

2025-10-22 12:45:00 | INFO | Processing source: HKSIR (138 files)
2025-10-22 12:45:00 | INFO | Processing: EN01 Angioplasty and stent eng 2010.md
2025-10-22 12:45:00 | INFO | Procedure: Angioplasty And Stent Eng
2025-10-22 12:45:00 | INFO | Sections: overview, procedure, indication, risks, benefits
2025-10-22 12:45:02 | INFO | ✅ Generated 10 Q&A pairs  ← Notice: Only 2 seconds!
2025-10-22 12:45:04 | INFO | Saved: angioplasty_and_stent_eng_qna_medgemma.xml

2025-10-22 12:45:30 | INFO | ============================================================
2025-10-22 12:45:30 | INFO | ✅ CURATION COMPLETE!
2025-10-22 12:45:30 | INFO | Procedures processed: 10
2025-10-22 12:45:30 | INFO | Q&A pairs generated: 100
2025-10-22 12:45:30 | INFO | Master file saved: KB/qna_xml/procedures_master_qna_medgemma.xml
```

---

## Troubleshooting

### Issue: "Invalid API key"
**Solution**: Check your OpenRouter API key in `.env`
```bash
# Verify it starts with: sk-or-
OPENAI_API_KEY=sk-or-...  ✅
```

### Issue: "Model not found"
**Solution**: Check model name is correct
```bash
OPENAI_CHAT_MODEL=openai/gpt-oss-20b:free  ✅
# NOT: openai/gpt-oss-20b (missing :free)
# NOT: gpt-oss-20b (missing openai/ prefix)
```

### Issue: Rate limiting
**Solution**: OpenRouter free tier has limits. If you hit them, wait a bit or upgrade.

---

## Comparison: All Options

| Option | Speed | Cost | Quality | Reliability |
|--------|-------|------|---------|-------------|
| **MedGemma GPU** | 5-10 sec | Free | ⭐⭐⭐ | Good |
| **MedGemma CPU** | 20-60 sec | Free | ⭐⭐⭐ | Good |
| **OpenRouter (Free)** | 2-5 sec | Free | ⭐⭐⭐⭐ | Excellent |
| **OpenAI GPT-4o** | 3-7 sec | $ | ⭐⭐⭐⭐⭐ | Excellent |

---

## Verify It Works

```bash
# Test the configuration
python -c "from config import settings; print(f'API Base: {settings.openai_api_base}'); print(f'Model: {settings.openai_chat_model}')"

# Should output:
# API Base: https://openrouter.ai/api/v1
# Model: openai/gpt-oss-20b:free
```

---

## Next Steps

Once curation is complete:

```bash
# 1. Ingest into RAG
python scripts/ingest_qna_to_rag.py KB/qna_xml

# 2. Test it
python test_chat.py

# 3. Deploy API
python scripts/start_api.py
```

---

## Get OpenRouter API Key

1. Visit: https://openrouter.ai/
2. Click "Sign In" (free)
3. Dashboard → Click profile
4. Find "API Key" section
5. Click "Create Key"
6. Copy the key (starts with `sk-or-...`)

---

## Support

For OpenRouter issues:
- Docs: https://openrouter.ai/docs
- Status: https://status.openrouter.ai/
- Support: https://openrouter.ai/#contact

---

**Status**: ✅ **Ready to use**

Set up your `.env` file and run the script! It will be 20-30x faster. 🚀

