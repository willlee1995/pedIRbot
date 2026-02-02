"""
Ingest curated Q&A XML data into RAG vector database.

This script processes the structured Q&A XML files and ingests them into
the vector store, making them available for retrieval in the RAG pipeline.
"""
import sys
import os
from pathlib import Path
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional

# Add parent directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from loguru import logger
from src.vector_store import VectorStore
from src.embeddings import get_embedding_model
from src.document_processor import DocumentChunk
from config import settings


class QnAXMLProcessor:
    """Process Q&A XML files for RAG ingestion."""

    def __init__(self):
        """Initialize the Q&A processor."""
        self.processed_qna = []

    def load_qna_xml(self, xml_file: str) -> List[Dict[str, Any]]:
        """
        Load Q&A pairs from XML file.

        Args:
            xml_file: Path to XML file

        Returns:
            List of Q&A pair dictionaries
        """
        qna_pairs = []

        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()

            # Handle both individual procedure files and master file
            procedures = root.findall('.//procedure') if root.tag == 'procedures' else [root]

            for procedure in procedures:
                procedure_name = procedure.get('name', 'Unknown')

                for qna in procedure.findall('.//qna'):
                    qna_id = qna.get('id', '')
                    question = qna.findtext('question', '')
                    answer = qna.findtext('answer', '')

                    # Extract metadata
                    metadata_elem = qna.find('metadata')
                    category = ''
                    from_section = ''

                    if metadata_elem is not None:
                        category = metadata_elem.findtext('question_category', '')
                        from_section = metadata_elem.findtext('from_section', '')

                    qna_pairs.append({
                        'procedure': procedure_name,
                        'qna_id': qna_id,
                        'question': question,
                        'answer': answer,
                        'category': category,
                        'from_section': from_section
                    })

            logger.info(f"Loaded {len(qna_pairs)} Q&A pairs from {Path(xml_file).name}")
            return qna_pairs

        except Exception as e:
            logger.error(f"Error loading Q&A XML {xml_file}: {e}")
            return []

    def create_chunks_from_qna(self, qna_pairs: List[Dict[str, Any]], source_file: str) -> List[DocumentChunk]:
        """
        Convert Q&A pairs into DocumentChunks for vectorization.

        Long answers are split into multiple chunks to stay under 800 chars.
        Each chunk includes the question for context.

        Args:
            qna_pairs: List of Q&A pair dictionaries
            source_file: Source XML filename

        Returns:
            List of DocumentChunk objects
        """
        chunks = []
        chunk_index = 0
        max_chunk_size = 800  # Increased to 800 for better context retention

        for qna in qna_pairs:
            procedure = qna['procedure']
            question = qna['question']
            answer = qna['answer']
            category = qna['category']

            # Create question part (reusable across sub-chunks)
            question_prefix = f"Q: {question}\n\nA: "

            # If answer is short enough, create single chunk
            if len(question_prefix) + len(answer) <= max_chunk_size:
                combined_content = question_prefix + answer

                metadata = {
                    'source': str(Path('KB/qna_xml') / source_file),
                    'filename': source_file,
                    'file_type': '.xml',
                    'source_org': 'CIRSE',
                    'chunk_type': 'qna_pair',
                    'procedure': procedure,
                    'qna_id': qna['qna_id'],
                    'question_category': category,
                    'from_section': qna['from_section'],
                    'content_type': 'curated_qa',
                    'is_qna': True,
                    'answer_part': '1/1',  # Single part
                }

                chunk_id = f"{source_file}_{procedure}_{qna['qna_id']}"

                chunks.append(DocumentChunk(
                    content=combined_content,
                    metadata=metadata,
                    chunk_id=chunk_id
                ))

            else:
                # Split long answer into multiple chunks
                # Reserve space for question prefix
                answer_space = max_chunk_size - len(question_prefix)

                # Split answer by sentences first
                sentences = self._split_into_sentences(answer)
                sub_chunks = []
                current_sub = ""

                for sentence in sentences:
                    # Add sentence if it fits
                    test_content = current_sub + sentence if not current_sub else current_sub + " " + sentence
                    if len(test_content) <= answer_space:
                        current_sub = test_content if not current_sub else current_sub + " " + sentence
                    else:
                        # Current sentence doesn't fit
                        if current_sub.strip():
                            sub_chunks.append(current_sub.strip())
                        current_sub = sentence

                if current_sub.strip():
                    sub_chunks.append(current_sub.strip())

                # Create chunk for each sub-chunk
                total_parts = len(sub_chunks)
                for part_num, sub_answer in enumerate(sub_chunks, 1):
                    combined_content = question_prefix + sub_answer

                    metadata = {
                        'source': str(Path('KB/qna_xml') / source_file),
                        'filename': source_file,
                        'file_type': '.xml',
                        'source_org': 'CIRSE',
                        'chunk_type': 'qna_pair',
                        'procedure': procedure,
                        'qna_id': qna['qna_id'],
                        'question_category': category,
                        'from_section': qna['from_section'],
                        'content_type': 'curated_qa',
                        'is_qna': True,
                        'answer_part': f'{part_num}/{total_parts}',  # e.g., "1/5"
                    }

                    chunk_id = f"{source_file}_{procedure}_{qna['qna_id']}_part{part_num}"

                    chunks.append(DocumentChunk(
                        content=combined_content,
                        metadata=metadata,
                        chunk_id=chunk_id
                    ))

                    chunk_index += 1

        logger.info(f"Created {len(chunks)} chunks from {len(qna_pairs)} Q&A pairs (800 char limit)")
        return chunks

    def _split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences while preserving structure.

        Args:
            text: Text to split

        Returns:
            List of sentences
        """
        import re

        # Split on sentence-ending punctuation
        sentences = re.split(r'(?<=[.!?])\s+', text)

        # Filter out empty strings and rejoin short fragments
        result = []
        for sentence in sentences:
            if sentence.strip():
                result.append(sentence.strip())

        return result

    def process_qna_directory(self, qna_dir: str) -> List[DocumentChunk]:
        """
        Process all Q&A XML files in a directory.

        Args:
            qna_dir: Path to directory containing Q&A XML files

        Returns:
            List of all DocumentChunk objects
        """
        all_chunks = []
        qna_path = Path(qna_dir)

        if not qna_path.exists():
            logger.error(f"Q&A directory not found: {qna_dir}")
            return all_chunks

        # Find all XML files (skip master file if processing individually)
        xml_files = list(qna_path.glob('*_qna_medgemma.xml'))

        logger.info(f"Found {len(xml_files)} Q&A files to process")

        for xml_file in sorted(xml_files):
            try:
                logger.info(f"Processing: {xml_file.name}")

                # Load Q&A pairs
                qna_pairs = self.load_qna_xml(str(xml_file))

                if not qna_pairs:
                    logger.warning(f"No Q&A pairs found in {xml_file.name}")
                    continue

                # Create chunks
                chunks = self.create_chunks_from_qna(qna_pairs, xml_file.name)

                all_chunks.extend(chunks)

            except Exception as e:
                logger.error(f"Error processing {xml_file.name}: {e}")
                continue

        logger.info(f"Total chunks created: {len(all_chunks)}")
        return all_chunks


def main(qna_dir: str = "KB/qna_xml", reset: bool = False):
    """
    Ingest Q&A data into RAG vector database.

    Args:
        qna_dir: Path to directory containing Q&A XML files
        reset: Whether to reset the vector store before ingestion
    """
    logger.info("=" * 80)
    logger.info("Q&A INGESTION INTO RAG VECTOR STORE")
    logger.info("=" * 80)
    logger.info(f"Q&A Directory: {qna_dir}")
    logger.info(f"Embedding Provider: {settings.embedding_provider}")
    logger.info(f"Reset Vector Store: {reset}")
    logger.info("=" * 80)

    try:
        # Initialize embedding model
        logger.info("\n📦 Initializing embedding model...")
        embedding_model = get_embedding_model()
        logger.info(f"✅ Embedding model initialized: {embedding_model.__class__.__name__}")

        # Initialize vector store
        logger.info("\n💾 Initializing vector store...")
        vector_store = VectorStore(embedding_model)

        # Reset if requested
        if reset:
            logger.warning("🗑️  Resetting vector store...")
            vector_store.reset_collection()
            logger.info("✅ Vector store reset")

        # Process Q&A XML files
        logger.info("\n📄 Processing Q&A XML files...")
        processor = QnAXMLProcessor()
        chunks = processor.process_qna_directory(qna_dir)

        if not chunks:
            logger.error("No chunks to ingest!")
            return 1

        logger.info(f"\n📥 Ingesting {len(chunks)} chunks into vector store...")

        # Ingest chunks
        ingested = vector_store.add_documents(chunks)

        logger.info(f"✅ Successfully ingested {ingested} chunks")

        # Print summary
        logger.info("\n" + "=" * 80)
        logger.info("INGESTION SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Total Chunks Ingested: {ingested}")
        logger.info(f"Source: {qna_dir}")
        logger.info(f"Vector Store Location: {vector_store.collection_name}")
        logger.info("=" * 80)

        logger.info("\n✅ Q&A data successfully ingested into RAG system!")
        logger.info("\n📝 You can now query the RAG system with procedure-related questions.")
        logger.info("   The system will retrieve relevant Q&A pairs for context.")

        return 0

    except Exception as e:
        logger.error(f"❌ Error during ingestion: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Ingest curated Q&A data into RAG vector store"
    )
    parser.add_argument(
        "qna_dir",
        type=str,
        nargs='?',
        default="KB/qna_xml",
        help="Directory containing Q&A XML files (default: KB/qna_xml)"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset the vector store before ingestion"
    )

    args = parser.parse_args()

    sys.exit(main(qna_dir=args.qna_dir, reset=args.reset))
