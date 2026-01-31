# LEANN Implementation Notes

## ⚠️ Windows Compatibility Issue

**IMPORTANT**: LEANN's `leann-backend-hnsw` package does not have pre-built wheels for Windows. This means installation will fail on Windows systems.

### Solutions for Windows Users

1. **Use WSL (Windows Subsystem for Linux)** - Recommended
   - Install WSL: https://docs.microsoft.com/en-us/windows/wsl/install
   - Run your Python environment in WSL
   - Install LEANN normally: `pip install leann`

2. **Build from Source** (Advanced)
   - Requires C++ compiler (Visual Studio Build Tools)
   - Clone LEANN repository and build backend manually
   - Complex and may have compatibility issues

3. **Use Docker/Linux Container**
   - Run your application in a Linux container
   - LEANN will install normally

4. **Wait for Windows Support**
   - Check LEANN GitHub for Windows wheel updates
   - Consider using ChromaDB in the meantime

## Overview

This implementation provides a LEANN-based vector store as an alternative to ChromaDB, maintaining the same interface for easy migration.

## Files Created

1. **`src/vector_store_leann.py`**: LEANN vector store implementation
2. **`src/tools_leann.py`**: LEANN-based LangChain tools
3. **`scripts/ingest_documents_leann.py`**: Script to build LEANN indexes
4. **`scripts/compare_leann_chromadb.py`**: Comparison script
5. **`docs/LEANN_GUIDE.md`**: Usage guide

## Important Notes

### Embedding Model Integration

**⚠️ IMPORTANT**: The current implementation assumes LEANN's `LeannBuilder` and `LeannSearcher` can work with external embedding models. However, LEANN may require:

1. **Embedding model passed to builder/searcher**: You may need to modify the implementation to pass the embedding model:

```python
# If LEANN requires embedding model:
builder = LeannBuilder(
    backend_name=self.backend,
    embedding_model=self.embedding_model  # May be required
)
```

2. **Custom embedding function**: LEANN might need a custom embedding function:

```python
def embed_function(text: str) -> List[float]:
    return self.embedding_model.embed_query(text)

builder = LeannBuilder(
    backend_name=self.backend,
    embedding_function=embed_function
)
```

3. **LEANN's own embedding model**: LEANN might use its own embedding model internally. Check LEANN documentation.

### API Adjustments Needed

The implementation may need adjustments based on the actual LEANN API:

1. **`builder.add_text()`**: May need different parameters or method name
2. **`builder.build_index()`**: Parameters may differ (check if `graph_degree`, `complexity`, etc. are correct)
3. **`searcher.search()`**: Return format may differ - adjust result parsing in `similarity_search()`
4. **Metadata filters**: Format may differ - adjust `filter_dict` conversion

### Testing Required

Before using in production:

1. **Install LEANN**: `pip install leann`
2. **Test basic operations**:
   ```python
   from leann import LeannBuilder, LeannSearcher
   # Test building and searching
   ```
3. **Verify API compatibility**: Check if the API matches our implementation
4. **Adjust as needed**: Update `vector_store_leann.py` based on actual API

### Migration Path

1. **Keep ChromaDB**: Don't remove ChromaDB implementation yet
2. **Test LEANN**: Build a small index and test search
3. **Compare results**: Use `compare_leann_chromadb.py`
4. **Gradual migration**: Switch one component at a time
5. **Monitor performance**: Check storage savings and search quality

## Quick Test

```python
# Test LEANN integration
from src.vector_store_leann import LEANNVectorStore
from src.embeddings import get_embedding_model

embedding_model = get_embedding_model()
vector_store = LEANNVectorStore(embedding_model)

# Add a test document
from src.document_processor import DocumentChunk
chunk = DocumentChunk(
    content="Test document",
    metadata={"source": "test"},
    chunk_id="test-1"
)
vector_store.add_documents([chunk])
vector_store.build_index(force=True)

# Search
results = vector_store.similarity_search("test", k=1)
print(results)
```

## Troubleshooting

### "LEANN is not installed"
```bash
pip install leann
```

### "Index not built or loaded"
Build the index first:
```bash
python scripts/ingest_documents_leann.py KB/md --reset
```

### API Errors
Check LEANN documentation and adjust implementation:
- Review `src/vector_store_leann.py`
- Check LEANN GitHub for API changes
- Test with LEANN CLI first: `leann build --help`

## References

- [LEANN GitHub](https://github.com/yichuan-w/LEANN)
- [LEANN Documentation](https://github.com/yichuan-w/LEANN#readme)
- [LEANN Paper](https://arxiv.org/abs/2506.08276)

## Next Steps

1. Install LEANN: `pip install leann`
2. Test with small dataset
3. Adjust API calls based on actual LEANN API
4. Compare with ChromaDB
5. Migrate gradually

