"""Debug file discovery logic."""
import sys
import os
from pathlib import Path

def debug_discovery():
    kb_path = Path('KB')
    if not kb_path.exists():
        print(f"❌ KB directory not found: {kb_path.absolute()}")
        return

    print(f"Searching in: {kb_path.absolute()}")

    file_patterns = ['*.md', '*.markdown', '*.html', '*.htm', '*.pdf', '*.txt']
    print(f"Patterns: {file_patterns}")

    found_files = []
    for pattern in file_patterns:
        matches = list(kb_path.rglob(pattern))
        print(f"  Pattern '{pattern}': {len(matches)} matches")
        found_files.extend(matches)

    unique_files = list(set(f for f in found_files if f.is_file()))
    print(f"\nTotal unique files found: {len(unique_files)}")

    html_files = [f for f in unique_files if f.suffix.lower() in ['.html', '.htm']]
    print(f"HTML files in list: {len(html_files)}")
    for f in html_files[:5]:
        print(f"  - {f.name}")

if __name__ == "__main__":
    debug_discovery()
