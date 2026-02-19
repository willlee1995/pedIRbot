"""Check for file stem collisions."""
import sys
from pathlib import Path
from collections import defaultdict

def check_collisions():
    kb_path = Path('KB')
    file_patterns = ['*.md', '*.markdown', '*.html', '*.htm', '*.pdf', '*.txt']

    found_files = []
    for pattern in file_patterns:
        found_files.extend(kb_path.rglob(pattern))

    unique_files = list(set(f for f in found_files if f.is_file()))

    stems = defaultdict(list)
    for f in unique_files:
        stems[f.stem].append(f.name)

    collisions = {k: v for k, v in stems.items() if len(v) > 1}

    print(f"Total unique files: {len(unique_files)}")
    print(f"Total unique stems: {len(stems)}")
    print(f"Collisions found: {len(collisions)}")

    if collisions:
        print("\nExample collisions:")
        for k, v in list(collisions.items())[:10]:
            print(f"  Stem '{k}': {v}")

    # Specific check for the user's file
    target_stem = "sickkids_igt_GGJ_tubes_Primary_tube_insertion_by_image_guidance_7836"
    if target_stem in stems:
        print(f"\nTarget file matches: {stems[target_stem]}")

if __name__ == "__main__":
    check_collisions()
