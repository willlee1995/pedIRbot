# Knowledge Base Categorization Implementation

## Overview

The knowledge base now supports automatic categorization by **region** and **procedure category** to improve retrieval efficiency.

## Changes Made

### 1. Region Categorization
- **Hong Kong**: Documents from HKCH or HKSIR are automatically tagged as "Hong Kong"
- **Non-Hong Kong**: All other documents are tagged as "Non-Hong Kong"

### 2. Procedure Category Classification
Documents are automatically classified into one of these categories:
- **Venous Access**: PICC, CVC, central line, catheter placement/removal, port-a-cath, etc.
- **Angiogram Related**: Angiography, angioplasty, vascular imaging, stent placement, etc.
- **Embolization Related**: Embolization, embolotherapy, coil embolization, etc.
- **Biopsy Related**: Biopsy, tissue sampling, fine needle aspiration, etc.
- **Pain Injection Relief Related**: Pain injections, nerve blocks, steroid injections, etc.
- **Other**: Documents that don't match any specific category

The classification is based on keyword matching in both the filename and document content.

## Implementation Details

### Files Modified

1. **`src/document_processor.py`**
   - Added `_detect_region()` method to classify by region
   - Added `_classify_procedure_category()` method to classify procedures
   - Metadata now includes `region` and `procedure_category` fields

2. **`src/retriever.py`**
   - Added `region` and `procedure_category` to metadata field info for SelfQueryRetriever
   - Allows filtering by these new fields during retrieval

3. **`src/tools.py`**
   - Updated `search_knowledge_base()` and `search_kb()` functions to support filtering by:
     - `region` (Hong Kong or Non-Hong Kong)
     - `procedure_category` (all categories listed above)

## Usage

### For New Documents

When you ingest new documents, they will be automatically categorized:

```bash
python scripts/ingest_documents.py KB/md --reset
```

### For Existing Documents

To apply categorization to existing documents in your knowledge base, you need to re-ingest them:

```bash
# Reset the collection and re-ingest all documents
python scripts/ingest_documents.py KB/md --reset
```

**Note**: This will delete all existing documents and re-index them with the new categorization metadata.

## Retrieval with Filters

You can now filter retrieval by region and procedure category:

### Example: Search for PICC-related documents from Hong Kong
```python
# Using the tool
search_knowledge_base(
    query="PICC insertion procedure",
    region="Hong Kong",
    procedure_category="Venous Access"
)
```

### Supported Filter Values

- **region**: `"Hong Kong"` or `"Non-Hong Kong"`
- **procedure_category**:
  - `"Venous Access"`
  - `"Angiogram Related"`
  - `"Embolization Related"`
  - `"Biopsy Related"`
  - `"Pain Injection Relief Related"`
  - `"Other"`

## Benefits

1. **Improved Retrieval Efficiency**: Documents are pre-categorized, allowing faster filtering
2. **Better Relevance**: Retrieval can be narrowed to specific regions and procedure types
3. **Structured Knowledge**: Knowledge base is now organized hierarchically (region → procedure category)
4. **Scalability**: Easy to add more categories or regions in the future

## Next Steps

1. **Re-ingest existing documents** to apply categorization:
   ```bash
   python scripts/ingest_documents.py KB/md --reset
   ```

2. **Test retrieval** with new filters:
   ```bash
   python scripts/analyze_retrieval.py "PICC insertion" --region "Hong Kong" --procedure_category "Venous Access"
   ```

3. **Verify categorization** by checking document metadata in your vector store

## Customization

To modify procedure categories or keywords, edit the `_classify_procedure_category()` method in `src/document_processor.py`:

- Add new categories by adding entries to `category_keywords` dictionary
- Adjust keywords for existing categories
- Modify the scoring logic if needed

