"""Helper script to reset KB and re-ingest filtered documents."""
import sys
import os
from pathlib import Path

# Get the absolute path of the script's directory
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)

# Add the project root to the Python path
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from scripts.ingest_documents import main
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Reset KB and ingest filtered documents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Reset and ingest from default KB/md folder
  python scripts/reset_and_ingest.py

  # Reset and ingest from custom folder
  python scripts/reset_and_ingest.py KB/filtered_docs

  # Reset and ingest, allowing all file formats (not recommended)
  python scripts/reset_and_ingest.py KB/filtered_docs --allow-all-formats
        """
    )

    parser.add_argument(
        "kb_folder",
        type=str,
        nargs='?',
        default="KB/md",
        help="Path to folder containing filtered documents (default: KB/md)"
    )

    parser.add_argument(
        "--allow-all-formats",
        action="store_true",
        help="Allow processing non-markdown files (not recommended)"
    )

    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Skip confirmation prompt (useful for automation)"
    )

    args = parser.parse_args()

    # Check if folder exists
    kb_path = Path(args.kb_folder)
    if not kb_path.exists():
        print(f"❌ Error: Folder does not exist: {args.kb_folder}")
        print(f"\n💡 Please ensure your filtered documents are in the specified folder.")
        sys.exit(1)

    # Count files
    if args.allow_all_formats:
        file_patterns = ['*.pdf', '*.docx', '*.doc', '*.pptx', '*.ppt',
                        '*.xlsx', '*.xls', '*.csv', '*.md', '*.markdown',
                        '*.txt', '*.html', '*.htm']
        files = []
        for pattern in file_patterns:
            files.extend(kb_path.rglob(pattern))
        file_count = len([f for f in files if f.is_file()])
    else:
        files = list(kb_path.rglob('*.md')) + list(kb_path.rglob('*.markdown'))
        file_count = len([f for f in files if f.is_file()])

    # Confirmation
    if not args.confirm:
        print("=" * 70)
        print("⚠️  WARNING: This will DELETE all existing knowledge base data!")
        print("=" * 70)
        print(f"\n📁 Source folder: {args.kb_folder}")
        print(f"📄 Files to ingest: {file_count}")
        print(f"🔧 Markdown only: {'No (all formats)' if args.allow_all_formats else 'Yes'}")
        print("\n⚠️  This action cannot be undone!")
        response = input("\nContinue? (yes/no): ")

        if response.lower() != 'yes':
            print("\n❌ Reset cancelled.")
            sys.exit(0)

    print("\n" + "=" * 70)
    print("🔄 RESETTING AND RE-INGESTING KNOWLEDGE BASE")
    print("=" * 70)
    print()

    # Call the main ingestion function with reset=True
    try:
        main(
            kb_folder=args.kb_folder,
            reset=True,  # Always reset
            markdown_only=not args.allow_all_formats,
            picc_only=False
        )
        print("\n" + "=" * 70)
        print("✅ RESET AND RE-INGESTION COMPLETE")
        print("=" * 70)
    except Exception as e:
        print("\n" + "=" * 70)
        print(f"❌ ERROR: {e}")
        print("=" * 70)
        import traceback
        traceback.print_exc()
        sys.exit(1)

