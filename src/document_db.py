"""SQLite database for storing full document content."""
import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from loguru import logger

from config import settings


class DocumentDatabase:
    """SQLite database for storing full document content and metadata."""

    def __init__(self, db_path: str = None):
        """
        Initialize document database.

        Args:
            db_path: Path to SQLite database file (default: ./document_db.sqlite)
        """
        self.db_path = db_path or getattr(settings, 'document_db_path', './document_db.sqlite')
        self.connection = None
        self._initialize_db()

    def _initialize_db(self):
        """Initialize database schema."""
        self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row  # Return rows as dict-like objects

        cursor = self.connection.cursor()

        # Create documents table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id TEXT UNIQUE NOT NULL,
                filename TEXT NOT NULL,
                content TEXT NOT NULL,
                source_org TEXT,
                region TEXT,
                procedure_category TEXT,
                procedure_type TEXT,
                doc_type TEXT,
                age_group TEXT,
                target_audience TEXT,
                file_path TEXT,
                metadata_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create chunks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chunk_id TEXT UNIQUE NOT NULL,
                document_id TEXT NOT NULL,
                content TEXT NOT NULL,
                section_title TEXT,
                chunk_index INTEGER,
                chunking_method TEXT,
                metadata_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(document_id) REFERENCES documents(document_id)
            )
        """)

        # Migrate: add new columns to existing documents table if missing
        self._migrate_add_columns(cursor)

        # Create indexes for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_document_id ON documents(document_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_source_org ON documents(source_org)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_region ON documents(region)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_procedure_category ON documents(procedure_category)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_filename ON documents(filename)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_doc_type ON documents(doc_type)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_age_group ON documents(age_group)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON chunks(document_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_chunk_id ON chunks(chunk_id)
        """)

        self.connection.commit()
        logger.info(f"Initialized document database at {self.db_path}")

    def _migrate_add_columns(self, cursor):
        """Add new columns to existing tables if they don't exist (safe migration)."""
        # Check existing columns
        cursor.execute("PRAGMA table_info(documents)")
        existing_cols = {row[1] for row in cursor.fetchall()}

        new_cols = {
            'doc_type': 'TEXT',
            'age_group': 'TEXT',
            'target_audience': 'TEXT',
        }
        for col_name, col_type in new_cols.items():
            if col_name not in existing_cols:
                cursor.execute(f"ALTER TABLE documents ADD COLUMN {col_name} {col_type}")
                logger.info(f"Migrated: added column '{col_name}' to documents table")

    def store_document(
        self,
        document_id: str,
        filename: str,
        content: str,
        metadata: Dict[str, Any] = None
    ) -> bool:
        """
        Store a document in the database.

        Args:
            document_id: Unique identifier for the document
            filename: Original filename
            content: Full document content
            metadata: Document metadata dict

        Returns:
            True if successful, False otherwise
        """
        try:
            metadata = metadata or {}
            cursor = self.connection.cursor()

            # Extract common metadata fields
            source_org = metadata.get('source_org', '')
            region = metadata.get('region', '')
            procedure_category = metadata.get('procedure_category', '')
            procedure_type = metadata.get('procedure_type', '')
            doc_type = metadata.get('doc_type', '')
            age_group = metadata.get('age_group', '')
            target_audience = metadata.get('target_audience', '')
            file_path = metadata.get('source', '')

            # Store full metadata as JSON
            metadata_json = json.dumps(metadata)

            cursor.execute("""
                INSERT OR REPLACE INTO documents (
                    document_id, filename, content, source_org, region,
                    procedure_category, procedure_type, doc_type, age_group,
                    target_audience, file_path, metadata_json, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                document_id,
                filename,
                content,
                source_org,
                region,
                procedure_category,
                procedure_type,
                doc_type,
                age_group,
                target_audience,
                file_path,
                metadata_json,
                datetime.now().isoformat()
            ))

            self.connection.commit()
            logger.debug(f"Stored document: {document_id} ({len(content)} chars)")
            return True
        except Exception as e:
            logger.error(f"Error storing document {document_id}: {e}")
            logger.exception(e)
            return False

    def store_chunk(
        self,
        chunk_id: str,
        document_id: str,
        content: str,
        section_title: str = '',
        chunk_index: int = 0,
        chunking_method: str = '',
        metadata: Dict[str, Any] = None
    ) -> bool:
        """
        Store a document chunk in the chunks table.

        Args:
            chunk_id: Unique chunk identifier
            document_id: Parent document ID
            content: Chunk text content
            section_title: Section heading this chunk belongs to
            chunk_index: Position of chunk within the document
            chunking_method: How the chunk was created (semantic, sliding_window, etc.)
            metadata: Additional metadata as dict

        Returns:
            True if successful
        """
        try:
            cursor = self.connection.cursor()
            metadata_json = json.dumps(metadata or {})

            cursor.execute("""
                INSERT OR REPLACE INTO chunks (
                    chunk_id, document_id, content, section_title,
                    chunk_index, chunking_method, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                chunk_id,
                document_id,
                content,
                section_title,
                chunk_index,
                chunking_method,
                metadata_json,
            ))

            self.connection.commit()
            return True
        except Exception as e:
            logger.error(f"Error storing chunk {chunk_id}: {e}")
            return False

    def get_chunks_by_document(self, document_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve all chunks for a given document.

        Args:
            document_id: Parent document ID

        Returns:
            List of chunk dicts ordered by chunk_index
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT * FROM chunks WHERE document_id = ? ORDER BY chunk_index
            """, (document_id,))

            chunks = []
            for row in cursor.fetchall():
                metadata = json.loads(row['metadata_json']) if row['metadata_json'] else {}
                chunks.append({
                    'chunk_id': row['chunk_id'],
                    'document_id': row['document_id'],
                    'content': row['content'],
                    'section_title': row['section_title'],
                    'chunk_index': row['chunk_index'],
                    'chunking_method': row['chunking_method'],
                    'metadata': metadata,
                })
            return chunks
        except Exception as e:
            logger.error(f"Error retrieving chunks for {document_id}: {e}")
            return []

    def get_all_documents(self) -> List[Dict[str, Any]]:
        """
        Retrieve all documents (for review export).

        Returns:
            List of all document dicts
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM documents ORDER BY filename")

            documents = []
            for row in cursor.fetchall():
                metadata = json.loads(row['metadata_json']) if row['metadata_json'] else {}
                documents.append({
                    'document_id': row['document_id'],
                    'filename': row['filename'],
                    'content': row['content'],
                    'source_org': row['source_org'],
                    'region': row['region'],
                    'procedure_category': row['procedure_category'],
                    'procedure_type': row['procedure_type'],
                    'doc_type': row['doc_type'] if 'doc_type' in row.keys() else '',
                    'age_group': row['age_group'] if 'age_group' in row.keys() else '',
                    'target_audience': row['target_audience'] if 'target_audience' in row.keys() else '',
                    'file_path': row['file_path'],
                    'metadata': metadata,
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at']
                })
            return documents
        except Exception as e:
            logger.error(f"Error retrieving all documents: {e}")
            return []

    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a document by ID.

        Args:
            document_id: Document identifier

        Returns:
            Document dict with content and metadata, or None if not found
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT * FROM documents WHERE document_id = ?
            """, (document_id,))

            row = cursor.fetchone()
            if row:
                # Parse metadata JSON
                metadata = json.loads(row['metadata_json']) if row['metadata_json'] else {}

                return {
                    'document_id': row['document_id'],
                    'filename': row['filename'],
                    'content': row['content'],
                    'source_org': row['source_org'],
                    'region': row['region'],
                    'procedure_category': row['procedure_category'],
                    'procedure_type': row['procedure_type'],
                    'file_path': row['file_path'],
                    'metadata': metadata,
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at']
                }
            return None
        except Exception as e:
            logger.error(f"Error retrieving document {document_id}: {e}")
            logger.exception(e)
            return None

    def get_documents_by_ids(self, document_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Retrieve multiple documents by their IDs.

        Args:
            document_ids: List of document identifiers

        Returns:
            List of documents
        """
        try:
            if not document_ids:
                return []

            placeholders = ','.join('?' * len(document_ids))
            cursor = self.connection.cursor()
            cursor.execute(f"""
                SELECT * FROM documents WHERE document_id IN ({placeholders})
            """, document_ids)

            documents = []
            for row in cursor.fetchall():
                metadata = json.loads(row['metadata_json']) if row['metadata_json'] else {}
                documents.append({
                    'document_id': row['document_id'],
                    'filename': row['filename'],
                    'content': row['content'],
                    'source_org': row['source_org'],
                    'region': row['region'],
                    'procedure_category': row['procedure_category'],
                    'procedure_type': row['procedure_type'],
                    'file_path': row['file_path'],
                    'metadata': metadata,
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at']
                })

            return documents
        except Exception as e:
            logger.error(f"Error retrieving documents: {e}")
            logger.exception(e)
            return []

    def search_documents(
        self,
        source_org: Optional[str] = None,
        region: Optional[str] = None,
        procedure_category: Optional[str] = None,
        procedure_type: Optional[str] = None,
        filename_pattern: Optional[str] = None,
        content: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search documents by metadata filters.

        Args:
            source_org: Filter by source organization
            region: Filter by region
            procedure_category: Filter by procedure category
            procedure_type: Filter by procedure type
            filename_pattern: SQL LIKE pattern for filename
            content: SQL LIKE pattern for content
            limit: Maximum number of results

        Returns:
            List of matching documents
        """
        try:
            cursor = self.connection.cursor()
            conditions = []
            params = []

            if source_org:
                conditions.append("source_org = ?")
                params.append(source_org)
            if region:
                conditions.append("region = ?")
                params.append(region)
            if procedure_category:
                conditions.append("procedure_category = ?")
                params.append(procedure_category)
            if procedure_type:
                conditions.append("procedure_type = ?")
                params.append(procedure_type)
            if filename_pattern:
                # Auto-add wildcards if not present
                if '%' not in filename_pattern:
                    filename_pattern = f"%{filename_pattern}%"
                conditions.append("filename LIKE ?")
                params.append(filename_pattern)
            if content:
                # Auto-add wildcards if not present
                if '%' not in content:
                    content = f"%{content}%"
                conditions.append("content LIKE ?")
                params.append(content)

            where_clause = " AND ".join(conditions) if conditions else "1=1"
            params.append(limit)

            query = f"""
                SELECT * FROM documents
                WHERE {where_clause}
                ORDER BY
                    CASE WHEN region = 'Hong Kong' THEN 1 ELSE 2 END ASC,
                    updated_at DESC
                LIMIT ?
            """

            cursor.execute(query, params)

            documents = []
            for row in cursor.fetchall():
                metadata = json.loads(row['metadata_json']) if row['metadata_json'] else {}
                documents.append({
                    'document_id': row['document_id'],
                    'filename': row['filename'],
                    'content': row['content'],
                    'source_org': row['source_org'],
                    'region': row['region'],
                    'procedure_category': row['procedure_category'],
                    'procedure_type': row['procedure_type'],
                    'file_path': row['file_path'],
                    'metadata': metadata,
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at']
                })

            logger.debug(f"Found {len(documents)} documents matching filters")
            return documents
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            logger.exception(e)
            return []

    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        try:
            cursor = self.connection.cursor()

            cursor.execute("SELECT COUNT(*) as total FROM documents")
            total = cursor.fetchone()['total']

            cursor.execute("""
                SELECT COUNT(DISTINCT source_org) as orgs,
                       COUNT(DISTINCT region) as regions,
                       COUNT(DISTINCT procedure_category) as categories
                FROM documents
            """)
            stats = cursor.fetchone()

            return {
                'total_documents': total,
                'unique_orgs': stats['orgs'] if stats else 0,
                'unique_regions': stats['regions'] if stats else 0,
                'unique_categories': stats['categories'] if stats else 0
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}

    def reset_database(self):
        """Reset database (delete all documents and chunks)."""
        try:
            cursor = self.connection.cursor()
            cursor.execute("DELETE FROM chunks")
            cursor.execute("DELETE FROM documents")
            self.connection.commit()
            logger.warning("Database reset - all documents and chunks deleted")
        except Exception as e:
            logger.error(f"Error resetting database: {e}")

    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            logger.debug("Database connection closed")

