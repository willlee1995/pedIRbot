"""
Ingest curated Q&A Markdown data into RAG vector database.

This script processes the structured Q&A markdown files (*_qa.md) from numbered
KB folders and ingests them into the vector store for RAG retrieval.
"""
import sys
import os
import re
from pathlib import Path
from typing import List, Dict, Any

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


class QnAMarkdownProcessor:
    """Process Q&A Markdown files for RAG ingestion."""

    def __init__(self):
        """Initialize the Q&A processor."""
        self.processed_qna = []

    def load_qna_markdown(self, md_file: str) -> List[Dict[str, Any]]:
        """
        Load Q&A pairs from markdown file.

        Args:
            md_file: Path to markdown file

        Returns:
            List of Q&A pair dictionaries
        """
        qna_pairs = []
        
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract metadata from header
            category = ""
            source = ""
            
            # Look for Category line
            category_match = re.search(r'\*\*Category.*?:\*\*\s*(.+)', content)
            if category_match:
                category = category_match.group(1).strip()
            
            source_match = re.search(r'\*\*Source.*?:\*\*\s*(.+)', content)
            if source_match:
                source = source_match.group(1).strip()
            
            # Split by Q&A sections (## Q1:, ## Q2:, etc.)
            # Pattern matches ## Q followed by number and colon
            qna_pattern = r'##\s+Q(\d+):\s*(.+?)(?=##\s+Q\d+:|---\s*$|\*Medical Disclaimer|\Z)'
            
            matches = re.findall(qna_pattern, content, re.DOTALL)
            
            for qna_num, qna_content in matches:
                # Extract the question (first line after Q#:)
                lines = qna_content.strip().split('\n')
                question_eng = lines[0].strip() if lines else ""
                
                # Look for Chinese question (## 問題X:)
                chinese_q_match = re.search(r'##\s+問題\d+[：:]\s*(.+)', qna_content)
                question_chi = chinese_q_match.group(1).strip() if chinese_q_match else ""
                
                # Extract answer - everything after "**Answer 答案:**"
                answer_match = re.search(r'\*\*Answer\s*答案\s*[：:]?\*\*\s*(.+)', qna_content, re.DOTALL)
                if answer_match:
                    answer = answer_match.group(1).strip()
                    # Clean up the answer - remove trailing ---
                    answer = re.sub(r'\n---\s*$', '', answer).strip()
                else:
                    # Fallback: take everything after the Chinese question
                    if chinese_q_match:
                        answer_start = chinese_q_match.end()
                        answer = qna_content[answer_start:].strip()
                    else:
                        answer = '\n'.join(lines[1:]).strip()
                
                # Combine questions for better retrieval
                combined_question = question_eng
                if question_chi:
                    combined_question = f"{question_eng}\n{question_chi}"
                
                qna_pairs.append({
                    'qna_id': f"q{qna_num}",
                    'question': combined_question,
                    'question_eng': question_eng,
                    'question_chi': question_chi,
                    'answer': answer,
                    'category': category,
                    'source': source
                })
            
            logger.info(f"Loaded {len(qna_pairs)} Q&A pairs from {Path(md_file).name}")
            return qna_pairs

        except Exception as e:
            logger.error(f"Error loading Q&A markdown {md_file}: {e}")
            import traceback
            traceback.print_exc()
            return []

    def create_chunks_from_qna(self, qna_pairs: List[Dict[str, Any]], source_file: str, relative_path: str) -> List[DocumentChunk]:
        """
        Convert Q&A pairs into DocumentChunks for vectorization.

        Long answers are split into multiple chunks to stay under 800 chars.
        Each chunk includes the question for context.

        Args:
            qna_pairs: List of Q&A pair dictionaries
            source_file: Source markdown filename
            relative_path: Relative path from KB root

        Returns:
            List of DocumentChunk objects
        """
        chunks = []
        max_chunk_size = 800

        for qna in qna_pairs:
            question = qna['question']
            answer = qna['answer']
            category = qna['category']

            # Create question part (reusable across sub-chunks)
            question_prefix = f"Q: {question}\n\nA: "

            # If answer is short enough, create single chunk
            if len(question_prefix) + len(answer) <= max_chunk_size:
                combined_content = question_prefix + answer

                metadata = {
                    'source': f"KB/{relative_path}",
                    'filename': source_file,
                    'file_type': '.md',
                    'source_org': 'HKCH',
                    'chunk_type': 'qna_pair',
                    'qna_id': qna['qna_id'],
                    'question_category': category,
                    'content_type': 'curated_qa',
                    'is_qna': True,
                    'answer_part': '1/1',
                    'language': 'bilingual',
                }

                chunk_id = f"{source_file}_{qna['qna_id']}"

                chunks.append(DocumentChunk(
                    content=combined_content,
                    metadata=metadata,
                    chunk_id=chunk_id
                ))

            else:
                # Split long answer into multiple chunks
                answer_space = max_chunk_size - len(question_prefix)
                sentences = self._split_into_sentences(answer)
                sub_chunks = []
                current_sub = ""

                for sentence in sentences:
                    test_content = current_sub + sentence if not current_sub else current_sub + " " + sentence
                    if len(test_content) <= answer_space:
                        current_sub = test_content if not current_sub else current_sub + " " + sentence
                    else:
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
                        'source': f"KB/{relative_path}",
                        'filename': source_file,
                        'file_type': '.md',
                        'source_org': 'HKCH',
                        'chunk_type': 'qna_pair',
                        'qna_id': qna['qna_id'],
                        'question_category': category,
                        'content_type': 'curated_qa',
                        'is_qna': True,
                        'answer_part': f'{part_num}/{total_parts}',
                        'language': 'bilingual',
                    }

                    chunk_id = f"{source_file}_{qna['qna_id']}_part{part_num}"

                    chunks.append(DocumentChunk(
                        content=combined_content,
                        metadata=metadata,
                        chunk_id=chunk_id
                    ))

        logger.info(f"Created {len(chunks)} chunks from {len(qna_pairs)} Q&A pairs")
        return chunks

    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences while preserving structure."""
        # Split on sentence-ending punctuation or newlines
        sentences = re.split(r'(?<=[.!?。！？])\s+|\n+', text)
        return [s.strip() for s in sentences if s.strip()]

    def find_qa_files(self, kb_dir: str) -> List[Path]:
        """
        Find all Q&A markdown files in numbered KB folders.

        Args:
            kb_dir: Path to KB directory

        Returns:
            List of Path objects to Q&A files
        """
        kb_path = Path(kb_dir)
        qa_files = []

        if not kb_path.exists():
            logger.error(f"KB directory not found: {kb_dir}")
            return qa_files

        # Find files matching *_qa.md in folders starting with digits (00_, 01_, etc.)
        for folder in sorted(kb_path.iterdir()):
            if folder.is_dir() and re.match(r'^\d{2}_', folder.name):
                # Recursively find *_qa.md files
                for qa_file in folder.rglob('*_qa.md'):
                    qa_files.append(qa_file)
                    
        logger.info(f"Found {len(qa_files)} Q&A files in numbered folders")
        return qa_files

    def process_qa_files(self, kb_dir: str) -> List[DocumentChunk]:
        """
        Process all Q&A markdown files in numbered KB folders.

        Args:
            kb_dir: Path to KB directory

        Returns:
            List of all DocumentChunk objects
        """
        all_chunks = []
        kb_path = Path(kb_dir)
        
        qa_files = self.find_qa_files(kb_dir)

        for qa_file in qa_files:
            try:
                # Get relative path from KB root
                relative_path = qa_file.relative_to(kb_path)
                
                logger.info(f"Processing: {relative_path}")

                # Load Q&A pairs
                qna_pairs = self.load_qna_markdown(str(qa_file))

                if not qna_pairs:
                    logger.warning(f"No Q&A pairs found in {qa_file.name}")
                    continue

                # Create chunks
                chunks = self.create_chunks_from_qna(
                    qna_pairs, 
                    qa_file.name,
                    str(relative_path)
                )
                all_chunks.extend(chunks)

            except Exception as e:
                logger.error(f"Error processing {qa_file.name}: {e}")
                import traceback
                traceback.print_exc()
                continue

        logger.info(f"Total chunks created: {len(all_chunks)}")
        return all_chunks


def main(kb_dir: str = "KB", reset: bool = False):
    """
    Ingest Q&A data into RAG vector database.

    Args:
        kb_dir: Path to KB directory containing numbered folders
        reset: Whether to reset the vector store before ingestion
    """
    logger.info("=" * 80)
    logger.info("Q&A MARKDOWN INGESTION INTO RAG VECTOR STORE")
    logger.info("=" * 80)
    logger.info(f"KB Directory: {kb_dir}")
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

        # Process Q&A markdown files
        logger.info("\n📄 Processing Q&A markdown files from numbered folders...")
        processor = QnAMarkdownProcessor()
        chunks = processor.process_qa_files(kb_dir)

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
        logger.info(f"Source: {kb_dir} (numbered folders)")
        logger.info(f"Vector Store Location: {vector_store.collection_name}")
        logger.info("=" * 80)

        logger.info("\n✅ Q&A data successfully ingested into RAG system!")
        logger.info("\n📝 You can now query the RAG system with procedure-related questions.")

        return 0

    except Exception as e:
        logger.error(f"❌ Error during ingestion: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Ingest curated Q&A markdown files into RAG vector store"
    )
    parser.add_argument(
        "kb_dir",
        type=str,
        nargs='?',
        default="KB",
        help="KB directory containing numbered folders (default: KB)"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset the vector store before ingestion"
    )

    args = parser.parse_args()

    sys.exit(main(kb_dir=args.kb_dir, reset=args.reset))
