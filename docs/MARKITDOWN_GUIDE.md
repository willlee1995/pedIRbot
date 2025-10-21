# MarkItDown Integration Guide

## Overview

The PedIR RAG backend uses **MarkItDown** (by Microsoft) to convert all document formats to Markdown before vectorization. This ensures optimal compatibility with LLMs and provides a unified, structured text format for all knowledge base documents.

## Why MarkItDown?

1. **LLM-Optimized Format**: Markdown is the ideal format for LLMs, preserving structure while remaining plain text
2. **Unified Processing**: Single conversion pipeline for all document types
3. **Better Context Preservation**: Maintains headings, lists, tables, and formatting
4. **Wide Format Support**: Handles Office documents, web pages, images, and more
5. **Microsoft-Backed**: Actively maintained by Microsoft with regular improvements

## Supported Formats

### Document Formats

- **PDF** (`.pdf`) - Medical guidelines, patient information leaflets
- **Word** (`.docx`, `.doc`) - Procedure protocols, clinical documents
- **PowerPoint** (`.pptx`, `.ppt`) - Medical presentations, training materials
- **Excel** (`.xlsx`, `.xls`, `.csv`) - Data tables, medication lists, protocols

### Web Formats

- **HTML** (`.html`, `.htm`) - Web-scraped medical information

### Text Formats

- **Markdown** (`.md`, `.markdown`) - Already in optimal format
- **Plain Text** (`.txt`) - Simple text documents

### Multimedia (Optional Features)

- **Images** (`.jpg`, `.jpeg`, `.png`) - Requires OCR capabilities
- **Audio** (`.mp3`, `.wav`) - Requires transcription service

## How It Works

```python
# 1. MarkItDown converts document to Markdown
markitdown = MarkItDown()
result = markitdown.convert("procedure_guide.pdf")
markdown_text = result.text_content

# 2. Markdown is converted to clean plain text
html = markdown.markdown(markdown_text)
plain_text = BeautifulSoup(html).get_text()

# 3. Text is chunked with overlap
chunks = processor.chunk_text(plain_text, metadata)

# 4. Chunks are embedded and stored
vector_store.add_documents(chunks)
```

## Benefits for Medical Documents

### 1. Preserves Document Structure

- **Headings** → Hierarchical sections maintained
- **Lists** → Procedure steps, risk factors clearly separated
- **Tables** → Medication schedules, comparison charts preserved
- **Emphasis** → Important warnings/notes highlighted

### 2. Handles Complex Medical PDFs

- Multi-column layouts
- Footnotes and references
- Headers and footers (filtered out)
- Page numbers (removed)

### 3. Multilingual Support

- Excellent Unicode support for Traditional Chinese
- Preserves mixed EN/ZH content
- Handles medical terminology in both languages

### 4. Table Extraction

MarkItDown excels at converting tables to Markdown format:

**Input (Excel/PDF table):**

```
+----------------+----------+
| Medication     | Dosage   |
+----------------+----------+
| Metformin      | 500mg    |
| Coumadin       | 5mg      |
+----------------+----------+
```

**Output (Markdown):**

```markdown
| Medication | Dosage |
| ---------- | ------ |
| Metformin  | 500mg  |
| Coumadin   | 5mg    |
```

**Final Text (for embedding):**

```
Medication Dosage
Metformin 500mg
Coumadin 5mg
```

## Prerequisites

Make sure you have the environment set up with `uv`:

```bash
# Install uv
# Windows: powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
# Linux/Mac: curl -LsSf https://astral.sh/uv/install.sh | sh

# Create environment and install dependencies
uv venv
uv pip install -r requirements.txt

# Activate
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac
```

## Configuration

### Basic Usage

```python
from src.document_processor import DocumentProcessor

processor = DocumentProcessor(
    chunk_size=512,        # Adjust based on your needs
    chunk_overlap=50       # Overlap for context preservation
)

# Process single file
text, metadata = processor.load_document("KB/HKCH/fasting_guide.pdf")

# Process entire directory
chunks = processor.process_directory("KB/")
```

### Advanced: Custom File Patterns

```python
# Only process specific formats
chunks = processor.process_directory(
    "KB/",
    file_patterns=['*.pdf', '*.docx', '*.html']
)

# Process presentations only
chunks = processor.process_directory(
    "KB/Presentations/",
    file_patterns=['*.pptx', '*.ppt']
)
```

## Troubleshooting

### Issue: MarkItDown Conversion Fails

**Symptom**: Warning message "Falling back to simple text extraction"

**Causes**:

- Corrupted file
- Unsupported format variant
- Missing dependencies (e.g., OCR for images)

**Solution**: The system automatically falls back to text extraction

### Issue: Poor Quality Output from PDFs

**Causes**:

- Scanned PDFs without OCR layer
- Complex layouts (multiple columns)
- Heavy graphics/images

**Solutions**:

1. Pre-process PDFs with OCR (Adobe Acrobat, Tesseract)
2. Use text-layer PDFs when possible
3. Manually convert to DOCX for better results

### Issue: Tables Not Preserved

**Solution**: MarkItDown converts tables to Markdown tables, which are then converted to plain text. For critical tables, consider:

1. Using Excel/CSV format instead
2. Pre-processing tables manually
3. Adjusting chunk size to keep tables together

## Performance Considerations

### Processing Speed

| Format | Speed (approx) | Notes                       |
| ------ | -------------- | --------------------------- |
| TXT/MD | Very Fast      | Direct read                 |
| DOCX   | Fast           | Native support              |
| PDF    | Medium         | Layout parsing required     |
| PPTX   | Medium         | Text extraction from slides |
| XLSX   | Fast           | Table conversion            |
| HTML   | Fast           | Direct parsing              |
| Images | Slow           | Requires OCR (if enabled)   |

### Memory Usage

- **Small files** (<1MB): Minimal impact
- **Large PDFs** (10-50MB): Moderate memory usage
- **Batch processing**: Processes files sequentially to manage memory

## Best Practices

### 1. Document Preparation

- Use text-layer PDFs (not scanned images)
- Ensure proper encoding (UTF-8)
- Clean up headers/footers in source documents
- Remove watermarks and background graphics

### 2. File Organization

```
KB/
├── HKCH/
│   ├── procedures/      # Clinical procedures
│   ├── protocols/       # Treatment protocols
│   └── patient_info/    # Patient-facing materials
├── SIR/
│   ├── guidelines/      # Clinical guidelines
│   └── leaflets/        # Patient leaflets
└── HKSIR/
    ├── english/
    └── chinese/
```

### 3. Quality Control

After ingestion, check logs for:

```
✓ Successfully converted X.pdf (12,543 chars)  # Good
✗ Falling back to simple extraction           # Check file
```

### 4. Chunk Size Optimization

For medical documents:

- **Short Q&A**: 256-512 chars
- **Procedure descriptions**: 512-1024 chars
- **Clinical guidelines**: 768-1536 chars

Adjust `MAX_CHUNK_SIZE` in `.env` accordingly.

## Integration with RAG Pipeline

### Full Workflow

```
1. Document Ingestion
   ├─ MarkItDown converts to Markdown
   ├─ Markdown → Plain Text
   └─ Text → Chunks

2. Vectorization
   ├─ Chunks → Embeddings
   └─ Store in ChromaDB

3. Retrieval
   ├─ Query → Embedding
   ├─ Semantic Search
   ├─ BM25 Keyword Search
   └─ Hybrid Ranking

4. Generation
   ├─ Retrieved Chunks → Context
   ├─ Context + Prompt → LLM
   └─ Response
```

### Quality Assurance

The MarkItDown integration includes:

- Automatic fallback on conversion errors
- Detailed logging of conversion process
- Metadata tracking of source format
- Character encoding detection

## Examples

### Example 1: Converting Medical Protocol PDF

```python
processor = DocumentProcessor()
text, metadata = processor.load_document("KB/HKCH/sedation_protocol.pdf")

print(f"Extracted {len(text)} characters")
print(f"Source: {metadata['source_org']}")
print(f"Type: {metadata['file_type']}")
```

### Example 2: Batch Processing Multiple Formats

```python
# Process entire knowledge base with all formats
chunks = processor.process_directory("KB/")

# Statistics
print(f"Total chunks: {len(chunks)}")
print(f"Formats processed: {set(c.metadata['file_type'] for c in chunks)}")
```

### Example 3: Handling Bilingual Documents

```python
# MarkItDown preserves both English and Chinese
text, metadata = processor.load_document("KB/HKSIR/leaflet_bilingual.pdf")

# Text contains both languages
assert "procedure" in text.lower()  # English
assert "手術" in text  # Chinese
```

## References

- [MarkItDown GitHub](https://github.com/microsoft/markitdown)
- [MarkItDown Documentation](https://pypi.org/project/markitdown/)
- Microsoft AI Blog on MarkItDown

## Changelog

### Version 0.1.0 (Current)

- Integrated MarkItDown for unified conversion
- Support for 10+ document formats
- Automatic fallback mechanism
- Bilingual (EN/ZH) optimization

### Future Enhancements

- Optional OCR integration for scanned PDFs
- Audio transcription for medical lectures
- Enhanced table preservation
- Custom MarkItDown plugins for medical formats
