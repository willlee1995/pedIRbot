# Q&A Integration with RAG Pipeline

## Overview

Yes! The curated Q&A data is **perfect** for your RAG system. This document explains how the Q&A XML fits into your Retrieval-Augmented Generation pipeline and how to integrate it.

---

## 🏗️ Architecture

### Traditional RAG Flow (Current)
```
User Query
    ↓
[Embedding] → [Vector Search in KB markdown] → [Retrieval]
    ↓
[Retrieved Context] → [LLM Prompt Engineering] → [Response]
```

### Enhanced RAG Flow (With Q&A)
```
User Query
    ↓
[Embedding] → [Vector Search in KB + Q&A] → [Retrieval]
    ↓
[Retrieved Context] → [LLM Prompt Engineering] → [Response]
          (Now includes curated Q&A pairs!)
```

---

## 🔄 How Q&A Integrates into RAG

### 1. **Vectorization Phase**
Each Q&A pair becomes a searchable chunk in your vector store:

```xml
<qna id="q1">
  <question>Why is the treatment being recommended for my child?</question>
  <answer>The goal of tumour ablation is to destroy the tumour without using surgery...</answer>
</qna>
```

↓ Transforms to:

```python
DocumentChunk(
    content="Q: Why is the treatment being recommended for my child?\n\nA: The goal of tumour ablation is to destroy the tumour without using surgery...",
    metadata={
        'procedure': 'Ablation',
        'question_category': 'indication',
        'chunk_type': 'qna_pair',
        'is_qna': True,
        ...
    }
)
```

↓ Vectorized:

```
Vector: [0.234, -0.512, 0.891, ..., 0.123]  (embedding)
Content: "Q: Why is the treatment... A: The goal of tumour..."
Metadata: {procedure, category, source, ...}
```

### 2. **Retrieval Phase**
When a user asks a question:

```
User: "Why do children need ablation?"
↓
Embedding: [0.228, -0.508, 0.887, ..., 0.119]
↓
Vector Search finds similar Q&A pairs
↓
Retrieved Q&A chunk with high similarity
```

### 3. **Generation Phase**
The retrieved Q&A is used as context:

```
System Prompt:
"You are a helpful assistant. Use the following context to answer the question."

Context:
[Document 1] (Source: CIRSE - ablation_qna.xml)
Q: Why is the treatment being recommended for my child?
A: The goal of tumour ablation is to destroy the tumour without using surgery...

User Question: "Why do children need ablation?"
↓
LLM generates response using Q&A as grounded context
```

---

## 📥 Integration Steps

### Step 1: Ingest Q&A into Vector Store

Run the ingestion script:

```bash
python scripts/ingest_qna_to_rag.py
```

**Output:**
```
================================================================================
Q&A INGESTION INTO RAG VECTOR STORE
================================================================================
Q&A Directory: KB/qna_xml
Embedding Provider: ollama
Reset Vector Store: False
================================================================================

📦 Initializing embedding model...
✅ Embedding model initialized: OllamaEmbeddings

💾 Initializing vector store...

📄 Processing Q&A XML files...
Processing: ablation_qna.xml
Loaded 10 Q&A pairs from ablation_qna.xml
Created 10 chunks from 10 Q&A pairs

Processing: biopsy_qna.xml
... (6 more procedures)

📥 Ingesting 70 chunks into vector store...
✅ Successfully ingested 70 chunks

================================================================================
INGESTION SUMMARY
================================================================================
Total Chunks Ingested: 70
Source: KB/qna_xml
Vector Store Location: chroma_db
================================================================================

✅ Q&A data successfully ingested into RAG system!
```

### Step 2: (Optional) Reset Vector Store and Re-ingest

If you want to start fresh:

```bash
python scripts/ingest_qna_to_rag.py --reset
```

### Step 3: Query the RAG System

The Q&A data is now available for retrieval. Users can query it:

```python
# Via API
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Why do children need ablation?"}'

# Response will now include Q&A context!
```

---

## 🎯 Benefits of Q&A Integration

| Benefit | Description |
|---------|-------------|
| **Precise Retrieval** | Q&A pairs are exact, curated answers - higher quality context |
| **SIR Standards** | Retrieves responses that follow pediatric IR best practices |
| **Consistent Answers** | Same questions always retrieve the same Q&A pair |
| **Metadata Filtering** | Can filter by procedure, category, or question type |
| **Parent-Friendly** | Answers are already written for parents/families |
| **Reduced Hallucination** | LLM grounds responses in curated Q&A, not raw documents |

---

## 📊 Data Flow Example

### Example Query: "How long is ablation?"

**1. User Input:**
```
Query: "How long is ablation?"
Language: English
```

**2. Embedding:**
```
Query embedding: [0.156, -0.423, 0.678, ..., 0.234]
```

**3. Vector Search:**
```
Searches vector store for similar chunks

Results:
- ablation_qna.xml_Ablation_q4 (Score: 0.89)
  → Q: "How will the treatment be performed?"
  → A: "The procedure will be carried out using image guidance..."

- ablation_qna.xml_Ablation_q8 (Score: 0.73)
  → Q: "Will my child need to stay in a hospital?"
  → A: "The length of hospital stay depends on..."

- KB/md/HKSIR/ablation.md_chunk_5 (Score: 0.68)
  → "Typical ablation duration ranges from 30-90 minutes..."
```

**4. Context Assembly:**
```
[Document 1] (Source: CIRSE - ablation_qna.xml)
Q: How will the treatment be performed?
A: The procedure will be carried out using image guidance...

[Document 2] (Source: CIRSE - ablation_qna.xml)
Q: Will my child need to stay in a hospital?
A: The length of hospital stay depends on...

[Document 3] (Source: HKSIR - ablation.md)
Typical ablation duration ranges from 30-90 minutes...
```

**5. LLM Generation:**
```
System: "Based on the context, answer the user's question..."

Response: "Ablation procedures typically take 30-90 minutes, depending on 
the size and location of the tumor. The actual procedure time varies, but 
your child will be under anesthesia during this time. The total time spent 
at the hospital may be longer, including preparation and recovery time. 
Please discuss specific timing with your interventional radiologist."

[With disclaimer]
```

---

## 🔍 Query Examples

### Q&A Will Enhance These Types of Questions:

```
User: "What are the risks of ablation?"
→ Retrieves: ablation_qna.xml - q2 (Benefits & Risks)

User: "Will my child need to fast before biopsy?"
→ Retrieves: biopsy_qna.xml - q7 (Fasting)

User: "How is drainage performed?"
→ Retrieves: drainage_qna.xml - q4 (Procedure Method)

User: "Can we do sclerotherapy instead?"
→ Retrieves: sclerotherapy_qna.xml - q3 (Alternatives)

User: "What follows after gastrostomy?"
→ Retrieves: gastrostomy_qna.xml - q10 (Follow-up)
```

---

## 🛠️ Technical Implementation

### QnAXMLProcessor Class

The `QnAXMLProcessor` handles conversion:

```python
processor = QnAXMLProcessor()

# Load Q&A from XML
qna_pairs = processor.load_qna_xml('KB/qna_xml/ablation_qna.xml')
# Returns: [{'procedure': 'Ablation', 'question': '...', 'answer': '...', ...}]

# Convert to chunks for vectorization
chunks = processor.create_chunks_from_qna(qna_pairs, 'ablation_qna.xml')
# Returns: [DocumentChunk(...), DocumentChunk(...), ...]

# Process entire directory
all_chunks = processor.process_qna_directory('KB/qna_xml')
# Returns: [70 DocumentChunk objects from 7 procedures]
```

### Integration with Existing System

```python
# Your existing code (api.py, rag_pipeline.py)
# No changes needed!

vector_store = VectorStore(embedding_model)
# Already contains both:
# - KB markdown documents (from ingest_documents.py)
# - Q&A XML chunks (from ingest_qna_to_rag.py)

retriever = HybridRetriever(vector_store)
# Searches across both types automatically

rag_pipeline = RAGPipeline(retriever, llm_provider)
# Uses combined context from both sources
```

---

## 📝 Metadata Attached to Q&A Chunks

Each Q&A chunk includes rich metadata for filtering:

```python
{
    'source': 'KB/qna_xml/ablation_qna.xml',
    'filename': 'ablation_qna.xml',
    'file_type': '.xml',
    'source_org': 'CIRSE',
    'chunk_type': 'qna_pair',
    'procedure': 'Ablation',
    'qna_id': 'q1',
    'question_category': 'indication',
    'from_section': 'why_perform',
    'content_type': 'curated_qa',
    'is_qna': True,
}
```

### Filtering Examples:

```python
# Filter by procedure
vector_store.search(query, filter={'procedure': 'Ablation'})

# Filter by question category
vector_store.search(query, filter={'question_category': 'risks_benefits'})

# Filter to Q&A only
vector_store.search(query, filter={'is_qna': True})

# Filter by source organization
vector_store.search(query, filter={'source_org': 'CIRSE'})
```

---

## 🚀 Usage Workflow

### Initial Setup (One Time)

```bash
# 1. Curate Q&A from procedures
python scripts/create_qna_xml.py

# 2. Ingest Q&A into vector store
python scripts/ingest_qna_to_rag.py

# 3. Start API
python scripts/start_api.py
```

### Regular Operation

```bash
# Users query the system
curl -X POST http://localhost:8000/query \
  -d '{"query": "Why do children need ablation?"}'

# RAG pipeline automatically:
# 1. Embeds user query
# 2. Searches vector store (now includes Q&A)
# 3. Retrieves relevant chunks (mix of Q&A + markdown)
# 4. Generates response using retrieved context
```

### Updating Q&A

```bash
# 1. Edit source documents (KB/CIRSE ped procedure info/)
# 2. Regenerate Q&A XML
python scripts/create_qna_xml.py

# 3. Re-ingest into vector store
python scripts/ingest_qna_to_rag.py --reset

# 4. System automatically uses updated Q&A
```

---

## 🎨 Response Quality Improvements

### Before Q&A Integration:
```
User: "What are the risks of ablation?"

RAG retrieves:
- Chunk from markdown (generic info about risks)
- Chunk from markdown (procedure steps)
- Chunk from markdown (outcomes)

LLM generates response from general markdown context
```

### After Q&A Integration:
```
User: "What are the risks of ablation?"

RAG retrieves:
- [ablation_qna.xml - Q2] "What are the benefits and potential risks?"
  ✓ Direct answer to the question
- [Markdown chunk] Supporting technical details
- [Markdown chunk] Additional context

LLM generates response grounded in curated Q&A answer
→ More accurate, consistent, and parent-friendly response
```

---

## ⚙️ Configuration

### Vector Store Settings (config.py)

```python
# Chunk size for Q&A pairs (typically smaller)
CHUNK_SIZE = 512  # Q&A chunks are self-contained

# Search parameters
RETRIEVAL_K = 5  # Number of chunks to retrieve
HYBRID_ALPHA = 0.5  # Balance between keyword and semantic search

# Embedding model
EMBEDDING_PROVIDER = "ollama"  # or "openai", "huggingface"
```

### RAG Pipeline Settings

The RAG pipeline automatically uses all chunks:

```python
# No changes needed - Q&A is automatically included in retrieval!
rag_pipeline.generate_response(
    query="Why do children need ablation?",
    k=5,  # Retrieves top 5 chunks (could be Q&A or markdown)
    include_sources=True  # Shows which chunk was used
)
```

---

## 📈 Performance Considerations

| Aspect | Impact |
|--------|--------|
| **Vector Store Size** | +70 chunks (small) |
| **Search Latency** | Minimal (same retrieval cost) |
| **Response Quality** | ⬆️ Significantly improved |
| **Consistency** | ⬆️ High (curated Q&A) |
| **Maintenance** | ⬇️ Easier (single source of truth) |

---

## 🔗 Related Scripts

| Script | Purpose | Input | Output |
|--------|---------|-------|--------|
| `create_qna_xml.py` | Curate Q&A from procedures | Procedure docs | XML files |
| `ingest_qna_to_rag.py` | Ingest Q&A into vector store | XML files | Vector DB |
| `ingest_documents.py` | Ingest markdown into vector store | Markdown files | Vector DB |
| `start_api.py` | Start RAG API server | Config | API endpoint |

---

## ✅ Verification

### Check if Q&A is in Vector Store

```python
from src.vector_store import VectorStore
from src.embeddings import get_embedding_model

embedding_model = get_embedding_model()
vector_store = VectorStore(embedding_model)

# Search for a known question
results = vector_store.search("Why do children need ablation?", k=5)

for result in results:
    print(f"Source: {result['metadata'].get('filename')}")
    print(f"Is Q&A: {result['metadata'].get('is_qna')}")
    print(f"Procedure: {result['metadata'].get('procedure')}")
    print(f"Score: {result['score']}")
    print("---")
```

**Expected Output:**
```
Source: ablation_qna.xml
Is Q&A: True
Procedure: Ablation
Score: 0.92
---
Source: KB/md/HKSIR/ablation.md
Is Q&A: False
Procedure: N/A
Score: 0.71
---
```

---

## 🎓 Quick Start Command

Get everything running in 3 commands:

```bash
# 1. Curate Q&A
python scripts/create_qna_xml.py

# 2. Ingest Q&A + markdown
python scripts/ingest_qna_to_rag.py
python scripts/ingest_documents.py KB/md

# 3. Start API
python scripts/start_api.py
```

Now your RAG system is enhanced with curated Q&A! 🚀

---

## 📞 Troubleshooting

### Q&A chunks not appearing in results?

```bash
# Re-ingest with reset
python scripts/ingest_qna_to_rag.py --reset

# Verify vector store
python -c "
from src.vector_store import VectorStore
from src.embeddings import get_embedding_model
vs = VectorStore(get_embedding_model())
print(f'Total chunks: {vs.collection.count()}')
"
```

### Q&A chunks not matching queries?

- Check embeddings are working correctly
- Try simpler query terms
- Verify XML files are well-formed

### Performance degradation?

- Reduce `RETRIEVAL_K` if too many chunks retrieved
- Use metadata filtering to narrow results
- Monitor embedding model performance

---

**Status: ✅ Q&A is RAG-Ready!**

Your curated Q&A data is perfectly formatted for integration with your RAG pipeline. Start ingestion to enhance your system!

