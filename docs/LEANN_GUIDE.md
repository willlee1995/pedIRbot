# LEANN Integration Guide

This guide explains how to use LEANN (Low-Storage Vector Index) as an alternative to ChromaDB in the PedIR RAG backend.

## What is LEANN?

LEANN is a vector database that provides **97% storage savings** while maintaining fast, accurate retrieval. It achieves this through:

- **Graph-based selective recomputation**: Only computes embeddings for nodes in the search path
- **High-degree preserving pruning**: Keeps important "hub" nodes while removing redundant connections
- **Dynamic batching**: Efficiently batches embedding computations for GPU utilization
- **Two-level search**: Smart graph traversal that prioritizes promising nodes

## Installation

### ⚠️ Windows Users

LEANN's `leann-backend-hnsw` does not have Windows wheels. You have these options:

1. **Use WSL (Recommended)**: Install Windows Subsystem for Linux and run Python there
2. **Build from source**: Requires C++ compiler (complex)
3. **Use Docker**: Run in a Linux container
4. **Use ChromaDB**: Continue using ChromaDB until Windows support is available

### Linux/macOS Installation

Install LEANN:

```bash
pip install leann
```

Or with UV:

```bash
uv pip install leann
```

## Quick Start

### 1. Build LEANN Index

Use the LEANN ingestion script to build an index from your documents:

```bash
# Basic usage (markdown files only)
python scripts/ingest_documents_leann.py KB/md --reset

# With custom parameters
python scripts/ingest_documents_leann.py KB/md --reset \
    --backend hnsw \
    --graph-degree 32 \
    --complexity 64 \
    --compact \
    --recompute
```

### 2. Use LEANN in Your Code

Replace `VectorStore` with `LEANNVectorStore`:

```python
from src.vector_store_leann import LEANNVectorStore
from src.embeddings import get_embedding_model

# Initialize LEANN vector store
embedding_model = get_embedding_model()
vector_store = LEANNVectorStore(embedding_model)

# Search
results = vector_store.similarity_search(
    query="What is a PICC line?",
    k=5,
    filter_dict={"source_org": "HKCH"}
)
```

### 3. Use LEANN Tools

Replace `tools.py` imports with `tools_leann.py`:

```python
from src.tools_leann import get_knowledge_base_tools_leann

tools = get_knowledge_base_tools_leann(vector_store)
```

## Configuration

LEANN settings are in `config.py`:

```python
# LEANN Vector Index Configuration
leann_persist_directory: str = ".leann/indexes"
leann_backend: Literal["hnsw", "diskann"] = "hnsw"
leann_graph_degree: int = 32
leann_complexity: int = 64
leann_compact: bool = True
leann_recompute: bool = True
```

### Backend Options

- **HNSW** (default): Ideal for most datasets with maximum storage savings
- **DiskANN**: Advanced option with superior search performance for large-scale deployments

### Parameters

- **graph_degree**: Graph degree for HNSW (default: 32)
- **complexity**: Build/search complexity (default: 64). Higher = more accurate but slower
- **compact**: Use compact storage (default: True). Provides 97% storage savings
- **recompute**: Enable recomputation (default: True). Required for compact mode

## Comparison with ChromaDB

### Storage Comparison

Run the comparison script:

```bash
python scripts/compare_leann_chromadb.py
```

Expected results:
- **ChromaDB**: ~3.8 GB for 2.1M vectors
- **LEANN**: ~324 MB for 2.1M vectors
- **Savings**: ~91-97%

### Performance

LEANN maintains fast search performance while using significantly less storage:
- Similar or faster search times
- Lower memory footprint
- Better scalability for large datasets

## Migration from ChromaDB

### Step 1: Build LEANN Index

```bash
python scripts/ingest_documents_leann.py KB/md --reset
```

### Step 2: Update Your Code

Replace imports:

```python
# Old
from src.vector_store import VectorStore
from src.tools import get_knowledge_base_tools

# New
from src.vector_store_leann import LEANNVectorStore
from src.tools_leann import get_knowledge_base_tools_leann
```

### Step 3: Update Initialization

```python
# Old
vector_store = VectorStore(embedding_model)

# New
vector_store = LEANNVectorStore(
    embedding_model,
    backend="hnsw",
    compact=True,
    recompute=True
)
```

### Step 4: Test

Run your application and verify:
- Search results are similar
- Performance is acceptable
- Storage is significantly reduced

## Advanced Usage

### Metadata Filtering

LEANN supports metadata filtering with operators:

```python
# Equality filter
results = vector_store.similarity_search(
    query="PICC insertion",
    filter_dict={"source_org": "HKCH"}
)

# Multiple filters
results = vector_store.similarity_search(
    query="angiogram",
    filter_dict={
        "source_org": "HKCH",
        "region": "Hong Kong",
        "procedure_category": "Angiogram Related"
    }
)
```

### Custom Search Parameters

```python
results = vector_store.similarity_search(
    query="your query",
    k=10,
    complexity=128,  # Higher complexity = more accurate
    recompute=True   # Enable recomputation
)
```

### Index Management

```python
# Get statistics
stats = vector_store.get_stats()
print(f"Index size: {stats['index_size_mb']} MB")

# Reset index
vector_store.reset_index()

# Delete index
vector_store.delete_index()
```

## Troubleshooting

### Index Not Found

If you see "Index not built or loaded":
1. Build the index: `python scripts/ingest_documents_leann.py KB/md --reset`
2. Check index path in `config.py`
3. Verify index exists: `ls .leann/indexes/`

### Import Errors

If you see "LEANN is not installed":
```bash
pip install leann
```

### Search Performance Issues

- Increase `complexity` for better accuracy (slower)
- Use `diskann` backend for large datasets
- Check if `recompute` is enabled (required for compact mode)

### Storage Not Reduced

- Ensure `compact=True` in config
- Ensure `recompute=True` (required for compact mode)
- Rebuild index with `--reset` flag

## Best Practices

1. **Use HNSW for most cases**: Provides best storage savings
2. **Use DiskANN for large-scale**: Better performance for very large datasets
3. **Enable compact storage**: Always use `compact=True` for maximum savings
4. **Enable recomputation**: Required for compact mode
5. **Rebuild after updates**: Use `--reset` when updating documents
6. **Monitor index size**: Use `get_stats()` to track storage

## CLI Usage

LEANN also provides a CLI for direct usage:

```bash
# Build index
leann build my-index --docs KB/md

# Search
leann search my-index "your query" --top-k 5

# Interactive chat
leann ask my-index --interactive

# List indexes
leann list

# Remove index
leann remove my-index
```

## References

- [LEANN GitHub](https://github.com/yichuan-w/LEANN)
- [LEANN Paper](https://arxiv.org/abs/2506.08276)
- [LEANN Documentation](https://github.com/yichuan-w/LEANN#readme)

## Support

For issues specific to LEANN:
- Check LEANN GitHub issues
- Review LEANN documentation
- Test with LEANN CLI first

For integration issues:
- Check this guide
- Review `src/vector_store_leann.py` implementation
- Compare with ChromaDB implementation in `src/vector_store.py`

