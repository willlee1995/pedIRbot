"""Debug script to test HTML and PDF loading."""
import sys
import os
from pathlib import Path

# Add project root to path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.document_processor import DocumentProcessor
from loguru import logger

def debug_loaders():
    processor = DocumentProcessor(markdown_only=False)

    # Test HTML
    html_path = Path(r"d:\Development area\pedIRbot\KB\Sickkids\sickkids_igt_GGJ_tubes_Primary_tube_insertion_by_image_guidance_7836.html")
    if html_path.exists():
        print(f"\n🔍 Testing HTML loader on: {html_path.name}")
        try:
            text = processor._load_html(html_path)
            print(f"✅ Success! Content length: {len(text)}")
            print("-" * 40)
            print(text[:500])
            print("-" * 40)
        except Exception as e:
            print(f"❌ HTML loader failed: {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"⚠️  HTML file not found: {html_path}")

    # Test PDF
    pdf_path = Path(r"d:\Development area\pedIRbot\KB\HKCH Appt sheet\B_NVIR_FeedingTube_20230913.pdf")
    if pdf_path.exists():
        print(f"\n🔍 Testing PDF loader on: {pdf_path.name}")
        try:
            text, meta = processor.load_document(str(pdf_path))
            print(f"✅ Success! Content length: {len(text)}")
            print("-" * 40)
            print(text[:500])
            print("-" * 40)
        except Exception as e:
            print(f"❌ PDF loader failed: {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"⚠️  PDF file not found: {pdf_path}")

if __name__ == "__main__":
    debug_loaders()
