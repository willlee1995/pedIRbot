# Show Full Chunk Content in Bot Responses

## Update

Updated RAG pipeline to display **complete retrieved chunk content** instead of truncating to 200 characters.

---

## What Changed

### Before (Truncated):
```python
'sources': [
    {
        'content': 'Q: Why is treatment recommended? A: The goal of...',  # ❌ Truncated at 200 chars
        'filename': 'ablation_qna.xml',
        'score': 0.92
    }
]
```

### After (Full Content):
```python
'sources': [
    {
        'content': 'Q: Why is the treatment being recommended for my child? A: The goal of tumour ablation is to destroy the tumour without using surgery. Whether you are suitable for this procedure depends on the size and location of the tumour as well as your clinical situation.',  # ✅ FULL content
        'filename': 'ablation_qna.xml',
        'procedure': 'Ablation',
        'question_category': 'indication',
        'answer_part': '1/1',
        'is_qna': True,
        'score': 0.92
    }
]
```

---

## New Metadata Fields in Sources

### Available Information:

| Field | Purpose | Example |
|-------|---------|---------|
| **content** | Full retrieved chunk text | Complete Q&A pair |
| **source_org** | Organization/source | CIRSE, HKSIR, HKCH |
| **filename** | Source file name | ablation_qna.xml |
| **procedure** | Procedure name | Ablation, Biopsy |
| **question_category** | Question type | indication, risks_benefits |
| **answer_part** | Multi-part tracking | "1/5" (part 1 of 5) |
| **is_qna** | Is Q&A pair? | true/false |
| **score** | Relevance score | 0.92 |

---

## API Response Example

### POST /query

**Request:**
```json
{
  "query": "What are the risks of ablation?",
  "include_sources": true
}
```

**Response:**
```json
{
  "response": "Ablation procedures have several potential risks that should be discussed with your medical team...",
  "sources": [
    {
      "content": "Q: What are the benefits and potential risks of the treatment?\n\nA: The insertion of the needle or applicator may cause bleeding, which can be reduced by plugging the biopsy tract. If you have a lung biopsy there is risk of pneumothorax...",
      "source_org": "CIRSE",
      "filename": "ablation_qna.xml",
      "procedure": "Ablation",
      "question_category": "risks_benefits",
      "answer_part": "1/8",
      "is_qna": true,
      "score": 0.96
    },
    {
      "content": "Q: What are the benefits and potential risks of the treatment?\n\nA: Another risk is the accidental leakage of the chemical agent or uncontrolled depositing of radiation energy, which may cause serious damage to the surrounding tissues...",
      "source_org": "CIRSE",
      "filename": "ablation_qna.xml",
      "procedure": "Ablation",
      "question_category": "risks_benefits",
      "answer_part": "2/8",
      "is_qna": true,
      "score": 0.91
    }
  ],
  "is_emergency": false
}
```

---

## Files Updated

### src/rag_pipeline.py

#### Change 1: `generate_response()` method (line 194-203)
```python
# Before:
'content': doc['content'][:200] + '...',  # Truncated

# After:
'content': doc['content'],  # Full content
'procedure': doc['metadata'].get('procedure', 'Unknown'),
'question_category': doc['metadata'].get('question_category', 'Unknown'),
'answer_part': doc['metadata'].get('answer_part', 'Unknown'),
'is_qna': doc['metadata'].get('is_qna', False),
```

#### Change 2: `stream_response()` method (line 245-255)
```python
# Before: (no content field)
'source_org': doc['metadata'].get('source_org', 'Unknown'),
'filename': doc['metadata'].get('filename', 'Unknown'),

# After:
'content': doc['content'],  # Full content added
'procedure': doc['metadata'].get('procedure', 'Unknown'),
'question_category': doc['metadata'].get('question_category', 'Unknown'),
'answer_part': doc['metadata'].get('answer_part', 'Unknown'),
'is_qna': doc['metadata'].get('is_qna', False),
```

---

## Benefits

✅ **See exact source text** - No more guessing what was truncated  
✅ **Verify accuracy** - Check bot's context against source  
✅ **Understand chunking** - See how Q&A was split (answer_part)  
✅ **Identify procedure** - Know which procedure each chunk is from  
✅ **Track Q&A type** - See question_category for each chunk  
✅ **Better debugging** - Complete context for troubleshooting  

---

## Use Cases

### 1. **Verify Source Accuracy**
```json
// User sees full chunk that bot used
// Can verify bot's response matches source exactly
```

### 2. **Track Multi-Part Answers**
```json
// See "answer_part": "3/8"
// Know this is part 3 of an 8-part answer
// Can request other parts if needed
```

### 3. **Understand Retrieval**
```json
// See all chunks retrieved
// Understand why bot gave that answer
// See relevance scores for each chunk
```

### 4. **Debugging Q&A**
```json
// Identify if Q&A is being used or markdown
// Check procedure and category metadata
// Verify chunking strategy is working
```

---

## Example: Multi-Part Chunk Retrieval

**Query:** "What are the risks of ablation?"

**Retrieved Chunks:**
```
Chunk 1 (answer_part: 1/8, score: 0.96)
├─ Content: "A: The insertion of the needle may cause bleeding..."
├─ Procedure: Ablation
└─ Category: risks_benefits

Chunk 2 (answer_part: 2/8, score: 0.91)
├─ Content: "A: Another risk is accidental leakage of chemical agent..."
├─ Procedure: Ablation
└─ Category: risks_benefits

Chunk 3 (answer_part: 3/8, score: 0.88)
├─ Content: "A: Pneumothorax risk if lung biopsy is performed..."
├─ Procedure: Ablation
└─ Category: risks_benefits
```

---

## Testing

### Test with curl:

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What risks does ablation have?",
    "include_sources": true
  }' | python -m json.tool
```

**Look for:**
- ✅ "content" field with full text (not truncated)
- ✅ "procedure" field showing Ablation
- ✅ "question_category" showing risks_benefits
- ✅ "answer_part" if split chunks
- ✅ "is_qna" showing true for Q&A sources

---

## Configuration

### Disable Full Content (if needed):

```python
# In rag_pipeline.py, change back to:
'content': doc['content'][:200] + '...',  # Truncated
```

### Or modify include_sources parameter:

```bash
# Don't include sources at all
{"query": "...", "include_sources": false}
```

---

## Impact

| Aspect | Before | After |
|--------|--------|-------|
| Content in sources | 200 chars (truncated) | Full content ✅ |
| Metadata fields | 3-4 fields | 8+ fields ✅ |
| Response size | Smaller | Larger (full content) |
| User transparency | Limited | Full transparency ✅ |
| Debugging capability | Hard | Easy ✅ |

---

## What Users See

### In Chat Interface:

```
🤖 Bot Response:
Ablation has several important risks that you should discuss...

📋 Sources Retrieved:
─────────────────

[1] Ablation Procedure
    Category: Risks & Benefits (answer_part: 1/8)
    Source: ablation_qna.xml
    Score: 0.96
    
    Full Text:
    "Q: What are the benefits and potential risks?
     A: The insertion of the needle may cause bleeding..."

[2] Ablation Procedure
    Category: Risks & Benefits (answer_part: 2/8)
    Source: ablation_qna.xml
    Score: 0.91
    
    Full Text:
    "Q: What are the benefits and potential risks?
     A: Another risk is accidental leakage..."
```

---

## Summary

| Feature | Status |
|---------|--------|
| **Full content display** | ✅ Enabled |
| **Metadata fields** | ✅ 8+ fields |
| **Non-Q&A sources** | ✅ Supported |
| **Streaming sources** | ✅ Updated |
| **Backward compatible** | ✅ Yes |

---

## Next Steps

1. **Restart API:**
   ```bash
   python scripts/start_api.py
   ```

2. **Test query with sources:**
   ```bash
   curl -X POST http://localhost:8000/query \
     -d '{"query": "What risks?", "include_sources": true}'
   ```

3. **Verify full content is shown** ✅

---

**Now you see complete retrieved chunks in all bot responses!** 🚀

