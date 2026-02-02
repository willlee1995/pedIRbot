# Using .env Configuration

## How It Works Now

The curation script now **automatically reads your `.env` file** to determine which LLM provider to use.

### Priority Order

```
1. Command line arguments (if provided)
2. .env configuration (settings.llm_provider)
3. Default: Ollama
```

---

## Setup for OpenRouter

### 1. Create/Update `.env` File

```bash
cp env.example .env
```

### 2. Edit `.env` with OpenRouter Settings

```env
# OpenRouter Configuration
OPENAI_API_KEY=sk-or-your-openrouter-api-key
OPENAI_API_BASE=https://openrouter.ai/api/v1
OPENAI_CHAT_MODEL=openai/gpt-oss-20b:free

# Set LLM provider to OpenAI (which works with OpenRouter)
LLM_PROVIDER=openai

# Optional: Keep embeddings with OpenAI
EMBEDDING_PROVIDER=openai
```

### 3. Run the Script

```bash
python scripts/curate_with_medgemma.py
```

**That's it!** The script will automatically read your `.env` and use OpenRouter.

---

## What You'll See

When the script starts, you'll see:

```
INFO | LLM Provider from config: openai
✅ LLM initialized: OpenAIProvider
   Provider: openai
   API Base: https://openrouter.ai/api/v1
   Model: openai/gpt-oss-20b:free
```

---

## Command Line Overrides

You can still override the `.env` settings from the command line:

### Use OpenAI (OpenRouter) regardless of `.env`:
```bash
python scripts/curate_with_medgemma.py --use-openai
```

### Force Ollama regardless of `.env`:
```bash
python scripts/curate_with_medgemma.py --use-ollama
```

---

## Configuration Priority

### Best Practice: Use `.env`

```bash
# Set your preference in .env once
# Then just run the script
python scripts/curate_with_medgemma.py
```

### Override for One-Off Run

```bash
# Use Ollama just this time, even if .env says OpenAI
python scripts/curate_with_medgemma.py --use-ollama
```

---

## Environment Variables

### For OpenRouter (Recommended)

```env
OPENAI_API_KEY=sk-or-your-key-here
OPENAI_API_BASE=https://openrouter.ai/api/v1
OPENAI_CHAT_MODEL=openai/gpt-oss-20b:free
LLM_PROVIDER=openai
```

### For OpenAI (Paid)

```env
OPENAI_API_KEY=sk-your-openai-key
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_CHAT_MODEL=gpt-4o
LLM_PROVIDER=openai
```

### For Ollama (Local)

```env
OLLAMA_API_BASE=http://localhost:11434
OLLAMA_CHAT_MODEL=alibayram/medgemma
LLM_PROVIDER=ollama
```

---

## Verify Configuration

```bash
python -c "from config import settings; print(f'LLM Provider: {settings.llm_provider}'); print(f'API Base: {settings.openai_api_base}'); print(f'Model: {settings.openai_chat_model}')"
```

Should output:
```
LLM Provider: openai
API Base: https://openrouter.ai/api/v1
Model: openai/gpt-oss-20b:free
```

---

## Troubleshooting

### Script still using Ollama?

1. Check your `.env` file exists:
   ```bash
   ls -la .env
   ```

2. Verify LLM_PROVIDER setting:
   ```bash
   grep LLM_PROVIDER .env
   # Should show: LLM_PROVIDER=openai
   ```

3. Check it's in the root directory:
   ```bash
   pwd
   # Should be: /path/to/pedIRbot
   ls -la .env
   # .env should be listed here
   ```

4. Force OpenAI from command line:
   ```bash
   python scripts/curate_with_medgemma.py --use-openai
   ```

---

## Performance

### With OpenRouter (`openai/gpt-oss-20b:free`)

```
⚡ 2-5 seconds per procedure
📦 250 procedures = 10-20 minutes
💰 Free tier
```

---

## Next Run

```bash
# Just run it - config is automatic now!
python scripts/curate_with_medgemma.py

# Should use OpenRouter and be fast!
```

---

**Status**: ✅ **Config-driven setup complete**

The script now respects your `.env` settings automatically!

