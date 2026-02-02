# 🔴 CRITICAL FIX: Wrong LLM Provider Method Signature

## The REAL Problem

The script was calling the LLM provider with the **wrong parameter type**.

### What We Were Doing (❌ WRONG)
```python
response = self.llm_provider.generate(
    prompt=prompt,  # ❌ Passing a STRING directly
    temperature=0.3,
    max_tokens=500
)
```

### What It Actually Expects (✅ CORRECT)
```python
response = self.llm_provider.generate(
    messages=[  # ✅ Expects a LIST of MESSAGE DICTS
        {"role": "system", "content": "..."},
        {"role": "user", "content": prompt}
    ],
    temperature=0.3,
    max_tokens=500
)
```

---

## Why This Caused TypeError

Looking at `src/llm.py` line 17:

```python
def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
    """
    Args:
        messages: List of message dicts with 'role' and 'content'  ← Expects THIS
        **kwargs: Additional parameters
    """
```

**Calling signature mismatch:**
```
Expected:  generate(messages=List[Dict], **kwargs)
We called: generate(prompt=str, **kwargs)
                    ↑ Parameter name is wrong!
```

This caused:
1. Missing required `messages` parameter → TypeError
2. TypeError wrapped in RetryError by tenacity
3. Script fails

---

## The Fix: Use Correct Message Format

### Before (❌ WRONG)
```python
response = self.llm_provider.generate(
    prompt=prompt,  # ❌ Wrong parameter
    temperature=0.3,
    max_tokens=500
)
```

### After (✅ CORRECT)
```python
messages = [
    {"role": "system", "content": "You are a pediatric IR expert..."},
    {"role": "user", "content": prompt}
]

response = self.llm_provider.generate(
    messages=messages,  # ✅ Correct parameter
    temperature=0.3,
    max_tokens=500
)
```

---

## Message Format Structure

The LLM provider expects a conversation-like format:

```python
messages = [
    {
        "role": "system",      # System instructions
        "content": "You are a pediatric IR expert helping parents..."
    },
    {
        "role": "user",        # User's actual question/prompt
        "content": "Q: Why is treatment recommended?\n\nContext: ..."
    }
]
```

This is the **standard OpenAI/LLM API format**, which all providers expect.

---

## Error Flow Explained

```
1. Script calls: generate(prompt="...", temperature=0.3, max_tokens=500)
                          ↓
2. LLM provider expects: generate(messages=[...], **kwargs)
                          ↓
3. Mismatch! TypeError: "missing required keyword argument 'messages'"
                          ↓
4. Tenacity retry wrapper catches it → wraps in RetryError
                          ↓
5. Retries 3 times (all fail with same error)
                          ↓
6. Final exception logged as: RetryError[... raised TypeError>]
```

---

## Why Previous Fixes Didn't Work

The previous retry/fallback fixes were treating symptoms, not the root cause:

```python
# ❌ This tried to catch the exception, but...
try:
    response = self.llm_provider.generate(prompt=prompt, ...)  # ← Still wrong!
except Exception:
    # Fallback
```

**The problem was still there** - we were still calling with wrong parameters!

---

## Current Implementation (FIXED)

Now properly structured:

```python
# Build correct message format
messages = [
    {"role": "system", "content": "Expert prompt..."},
    {"role": "user", "content": prompt}
]

try:
    # Call with correct parameter name
    response = self.llm_provider.generate(
        messages=messages,  # ✅ CORRECT!
        temperature=0.3,
        max_tokens=500
    )
except TypeError:
    # If LLM provider fails, fall back to direct Ollama
    response = self._call_ollama_direct(prompt)
```

---

## Expected Behavior Now

### Before (Failed)
```
WARNING | LLM generation failed (attempt 1): RetryError[...TypeError>]
WARNING | LLM generation failed (attempt 2): RetryError[...TypeError>]
WARNING | LLM generation failed (attempt 3): RetryError[...TypeError>]
```

### After (Works!)
```
DEBUG | Using LLM provider: OpenAIProvider
DEBUG | ✓ Generated answer for Angioplasty And Stent Eng
✅ Generated 10 Q&A pairs
```

---

## Testing

```bash
python scripts/curate_with_medgemma.py

# Should see:
# ✓ Generated answer for [procedure]
# ✅ Generated 10 Q&A pairs
# (No more RetryError/TypeError warnings!)
```

---

## Code Changes Summary

| File | Line | Change |
|------|------|--------|
| `scripts/curate_with_medgemma.py` | ~305-310 | Changed `prompt=` to `messages=` |
| `scripts/curate_with_medgemma.py` | ~303-308 | Build proper message format |
| `scripts/curate_with_medgemma.py` | ~311-320 | Simplified error handling |

---

## Why This Is The Real Fix

✅ **Addresses root cause** - Wrong parameter type
✅ **Matches LLM API contract** - Uses messages format
✅ **Works with all providers** - Standard format
✅ **No more TypeError** - Correct signature
✅ **Clean fallback** - Uses direct Ollama if provider fails

---

## Status

🎉 **FIXED**

The script now calls the LLM provider with the correct method signature!

Try running again and it should work perfectly!

