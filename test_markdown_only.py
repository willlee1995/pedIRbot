"""Quick test to verify markdown-only mode works."""
import sys
from pathlib import Path

# Add current directory to path FIRST
sys.path.insert(0, str(Path(__file__).parent))

from src.document_processor import DocumentProcessor
from loguru import logger

# Test 1: Standard mode (should use MarkItDown)
print("=" * 70)
print("TEST 1: Standard Mode (with MarkItDown conversion)")
print("=" * 70)

processor_standard = DocumentProcessor(
    chunk_size=1024,
    chunk_overlap=50,
    markdown_only=False
)

print(f"MarkItDown initialized: {processor_standard.markitdown is not None}")
print()

# Test 2: Markdown-only mode (should NOT use MarkItDown)
print("=" * 70)
print("TEST 2: Markdown-Only Mode (no MarkItDown)")
print("=" * 70)

processor_md = DocumentProcessor(
    chunk_size=1024,
    chunk_overlap=50,
    markdown_only=True
)

print(f"MarkItDown initialized: {processor_md.markitdown is not None}")
print()

# Test 3: Load a markdown file in markdown-only mode
print("=" * 70)
print("TEST 3: Load Markdown File (markdown-only mode)")
print("=" * 70)

md_file = Path("KB/md/Sickkids/sickkids_Peripherally_inserted_central_catheter_PICC_insertion_using_image_guidance_4705.md")

if md_file.exists():
    text = processor_md.load_document(str(md_file))
    print(f"Loaded {md_file.name}")
    print(f"Length: {len(text)} characters")
    print(f"Preview: {text[:200]}...")
else:
    print(f"File not found: {md_file}")

print()

# Test 4: Try to load HTML in markdown-only mode (should skip)
print("=" * 70)
print("TEST 4: Try HTML in Markdown-Only Mode (should skip)")
print("=" * 70)

html_file = Path("KB/Sickkids/sickkids_Peripherally_inserted_central_catheter_PICC_insertion_using_image_guidance_4705.html")

if html_file.exists():
    text = processor_md.load_document(str(html_file))
    if not text:
        print(f"✅ Correctly skipped HTML file: {html_file.name}")
    else:
        print(f"❌ Should have skipped HTML file but got {len(text)} chars")
else:
    print(f"HTML file not found: {html_file}")

print()
print("=" * 70)
print("Tests complete!")
print("=" * 70)

