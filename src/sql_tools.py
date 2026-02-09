"""SQL tools for querying full documents from SQLite database."""
from typing import List, Optional
from langchain_core.tools import tool
from loguru import logger

from src.document_db import DocumentDatabase
from config import settings


# Global document database instance (initialized on first use)
_document_db: Optional[DocumentDatabase] = None


def get_document_db() -> DocumentDatabase:
    """Get or create document database instance."""
    global _document_db
    if _document_db is None:
        _document_db = DocumentDatabase()
    return _document_db


@tool
def get_document_by_id(document_id: str) -> str:
    """
    [PREFERRED] Retrieve a full document by its document ID.

    **USE THIS TOOL** to get complete document context. This is preferred over using chunked content
    from semantic search because it provides the full document without scattered information.

    Use this tool when you need the complete content of a specific document.
    Works especially well with search_documents_sql - first search by metadata, then fetch full documents.

    Document ID extraction:
    - If you see a filename like 'picc_insertion.md' in metadata, the document_id is 'picc_insertion'
    - If you see a chunk_id like 'picc_insertion_chunk_0', extract 'picc_insertion' (remove '_chunk_X')
    - Simply remove the file extension and '_chunk_X' suffix to get the document_id

    Args:
        document_id: The document ID (filename without .md extension, without chunk suffix)

    Returns:
        Full document content with complete metadata (complete context, not scattered chunks)
    """
    logger.info(f"🔍 Fetching full document: {document_id}")

    try:
        db = get_document_db()
        doc = db.get_document(document_id)

        if not doc:
            return f"Document with ID '{document_id}' not found in database."

        # Format full document content
        content = f"""Document ID: {doc['document_id']}
Filename: {doc['filename']}
Source: {doc['source_org']}
Region: {doc['region']}
Procedure Category: {doc['procedure_category']}
Procedure Type: {doc['procedure_type']}

Full Content:
{doc['content']}
"""
        logger.info(f"✅ Retrieved document: {doc['filename']} ({len(doc['content'])} chars)")
        return content
    except Exception as e:
        logger.error(f"Error fetching document {document_id}: {e}")
        logger.exception(e)
        return f"Error retrieving document: {str(e)}"


@tool
def search_documents_sql(
    source_org: Optional[str] = None,
    region: Optional[str] = None,
    procedure_category: Optional[str] = None,
    procedure_type: Optional[str] = None,
    filename_pattern: Optional[str] = None,
    content: Optional[str] = None,
    limit: int = 5
) -> str:
    """
    [ADVANCED] Search for documents in the SQLite database using metadata filters.

    **RETURNS FULL DOCUMENT CONTENT directly.**
    You do NOT need to call get_document_by_id after this.

    Use this tool when you know specific metadata (source_org, region, etc.) or need to search by exact filename.
    For general questions, use `search_kb` (semantic search) first.

    Args:
        source_org: Filter by source organization (HKCH, SickKids, SIR, HKSIR, CIRSE)
        region: Filter by region ('Hong Kong' or 'Non-Hong Kong')
        procedure_category: Filter by procedure category ('Venous Access', 'Angiogram Related', 'Embolization Related', 'Biopsy Related', 'Pain Injection Relief Related', 'Other')
        procedure_type: Filter by procedure type
        filename_pattern: SQL LIKE pattern for filename (e.g., '%PICC%' to find PICC-related documents)
        content: SQL LIKE pattern for content (e.g., '%flush efficiency%' to find documents mentioning flush efficiency)
        limit: Maximum number of results (default: 5)

    Returns:
        FULL content of matching documents with metadata
    """
    logger.info(f"🔍 SQL search: org={source_org}, region={region}, category={procedure_category}, content={content}")

    try:
        db = get_document_db()
        docs = db.search_documents(
            source_org=source_org,
            region=region,
            procedure_category=procedure_category,
            procedure_type=procedure_type,
            filename_pattern=filename_pattern,
            content=content,
            limit=limit
        )

        if not docs:
            return "No documents found matching the criteria."

        # Format results with FULL CONTENT
        results = []
        for i, doc in enumerate(docs, 1):
            results.append(
                f"\n{'='*80}\n"
                f"[{i}] Document ID: {doc['document_id']}\n"
                f"    Filename: {doc['filename']}\n"
                f"    Source: {doc['source_org']}\n"
                f"    Region: {doc['region']}\n"
                f"    Category: {doc['procedure_category']}\n"
                f"    Procedure Type: {doc['procedure_type']}\n"
                f"{'='*80}\n"
                f"FULL CONTENT:\n"
                f"{doc['content']}\n"
            )

        result_text = "\n".join(results)
        logger.info(f"✅ Found {len(docs)} documents (returning FULL content)")
        return f"Found {len(docs)} documents with FULL content:\n\n{result_text}"
    except Exception as e:
        logger.error(f"Error in SQL search: {e}")
        logger.exception(e)
        return f"Error searching documents: {str(e)}"


@tool
def get_documents_by_ids(document_ids: str) -> str:
    """
    Retrieve multiple full documents by their IDs.

    Use this tool when you have multiple document IDs and need their full content.

    Args:
        document_ids: Comma-separated list of document IDs (e.g., 'picc_insertion,biopsy_guide')

    Returns:
        Full content of all requested documents
    """
    logger.info(f"🔍 Fetching multiple documents: {document_ids}")

    try:
        # Parse comma-separated IDs
        ids_list = [id.strip() for id in document_ids.split(',')]

        db = get_document_db()
        docs = db.get_documents_by_ids(ids_list)

        if not docs:
            return f"No documents found for IDs: {document_ids}"

        # Format all documents
        results = []
        for doc in docs:
            results.append(
                f"\n{'='*80}\n"
                f"Document ID: {doc['document_id']}\n"
                f"Filename: {doc['filename']}\n"
                f"Source: {doc['source_org']}\n"
                f"Region: {doc['region']}\n"
                f"Category: {doc['procedure_category']}\n"
                f"Procedure Type: {doc['procedure_type']}\n"
                f"{'='*80}\n"
                f"{doc['content']}\n"
            )

        logger.info(f"✅ Retrieved {len(docs)} documents")
        return "\n".join(results)
    except Exception as e:
        logger.error(f"Error fetching documents: {e}")
        logger.exception(e)
        return f"Error retrieving documents: {str(e)}"


def get_sql_tools() -> List:
    """
    Get list of SQL tools for document database access.

    Returns:
        List of LangChain tools for SQLite document queries
    """
    return [
        # get_document_by_id,  # Disabled: search_documents_sql now returns full content
        search_documents_sql,
        # get_documents_by_ids, # Disabled: search_documents_sql now returns full content
    ]

