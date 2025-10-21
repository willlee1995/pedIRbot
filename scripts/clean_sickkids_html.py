"""Clean up scraped SickKids HTML files by removing unwanted sections."""
import sys
import os
from pathlib import Path

# Add parent directory to path FIRST
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from loguru import logger
from bs4 import BeautifulSoup
from tqdm import tqdm


def clean_html_file(file_path: Path, backup: bool = True, dry_run: bool = False):
    """
    Clean a single HTML file.

    Args:
        file_path: Path to HTML file
        backup: Create backup before modifying
        dry_run: Show what would be done without modifying

    Returns:
        True if cleaned, False if no changes needed
    """
    try:
        # Read original file
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        original_content = ''.join(lines)

        # Parse HTML
        soup = BeautifulSoup(original_content, 'html.parser')

        # Track what we remove
        removed_elements = []

        # Remove elements with data-propname="AtSickKids"
        for elem in soup.find_all(attrs={'data-propname': 'AtSickKids'}):
            removed_elements.append(f"data-propname='AtSickKids': {elem.name}")
            elem.decompose()

        # Remove elements with aria-controls="article-AtSickKids"
        for elem in soup.find_all(attrs={'aria-controls': 'article-AtSickKids'}):
            removed_elements.append(f"aria-controls='article-AtSickKids': {elem.name}")
            elem.decompose()

        # Get cleaned HTML
        cleaned_html = str(soup)

        # Remove first 31 lines (as user specified)
        # But keep DOCTYPE and html tag if present
        cleaned_lines = cleaned_html.splitlines(keepends=True)

        # Find where actual content starts (skip first 31 lines or until <body>)
        skip_lines = min(31, len(cleaned_lines))

        # Keep DOCTYPE if present
        final_lines = []
        for i, line in enumerate(cleaned_lines):
            if i < skip_lines:
                # Keep DOCTYPE, html, and head tags
                if any(tag in line.lower() for tag in ['<!doctype', '<html', '<head']):
                    final_lines.append(line)
            else:
                final_lines.append(line)

        cleaned_content = ''.join(final_lines)

        # Check if anything changed
        if cleaned_content == original_content:
            return False

        if dry_run:
            logger.info(f"Would clean {file_path.name}:")
            for elem in removed_elements[:5]:
                logger.info(f"  - Remove: {elem}")
            if len(removed_elements) > 5:
                logger.info(f"  ... and {len(removed_elements) - 5} more elements")
            logger.info(f"  - Remove first 31 lines")
            return True

        # Create backup if requested
        if backup:
            backup_path = file_path.with_suffix('.html.bak')
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(original_content)
            logger.debug(f"Created backup: {backup_path.name}")

        # Write cleaned file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(cleaned_content)

        logger.debug(f"Cleaned {file_path.name} (removed {len(removed_elements)} elements)")
        return True

    except Exception as e:
        logger.error(f"Failed to clean {file_path.name}: {e}")
        return False


def clean_directory(directory: Path, pattern: str = "*.html", backup: bool = True, dry_run: bool = False):
    """
    Clean all HTML files in directory.

    Args:
        directory: Directory containing HTML files
        pattern: File pattern to match
        backup: Create backups before modifying
        dry_run: Show what would be done without modifying
    """
    logger.info("=" * 70)
    logger.info("SICKKIDS HTML CLEANUP")
    logger.info("=" * 70)
    logger.info(f"Directory: {directory}")
    logger.info(f"Pattern: {pattern}")
    logger.info(f"Backup: {backup}")
    logger.info(f"Dry run: {dry_run}")
    logger.info("=" * 70)

    # Find HTML files
    html_files = list(directory.rglob(pattern))

    if not html_files:
        logger.warning(f"No files found matching '{pattern}' in {directory}")
        return

    logger.info(f"\nFound {len(html_files)} HTML files")

    if dry_run:
        logger.info("\n🔍 DRY RUN - No files will be modified")

    # Clean files
    logger.info("\n🧹 Cleaning files...")

    cleaned_count = 0
    skipped_count = 0
    failed_count = 0

    with tqdm(total=len(html_files), desc="Cleaning", unit="file") as pbar:
        for file_path in html_files:
            result = clean_html_file(file_path, backup=backup, dry_run=dry_run)

            if result is True:
                cleaned_count += 1
            elif result is False:
                skipped_count += 1
            else:
                failed_count += 1

            pbar.update(1)

    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("CLEANUP SUMMARY")
    logger.info("=" * 70)
    logger.info(f"Total files:     {len(html_files)}")
    logger.info(f"✅ Cleaned:      {cleaned_count}")
    logger.info(f"⏭️  Skipped:      {skipped_count} (no changes needed)")
    logger.info(f"❌ Failed:       {failed_count}")

    if backup and cleaned_count > 0 and not dry_run:
        logger.info(f"\n💾 Backups created: {cleaned_count} .html.bak files")
        logger.info("   To restore: rename .html.bak back to .html")

    logger.info("=" * 70)

    if dry_run and cleaned_count > 0:
        logger.info(f"\n✅ {cleaned_count} files would be cleaned")
        logger.info("   Run without --dry-run to apply changes")
    elif cleaned_count > 0:
        logger.info(f"\n✅ Successfully cleaned {cleaned_count} files")
        logger.info("\n💡 Next steps:")
        logger.info("   1. Re-convert to markdown: python scripts/convert_to_markdown.py --force")
        logger.info("   2. Re-ingest: python scripts/ingest_documents.py --reset")
    else:
        logger.info("\n✅ All files are already clean!")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Clean up SickKids HTML files by removing unwanted sections"
    )
    parser.add_argument(
        "directory",
        type=str,
        nargs='?',
        default="KB/SickKids",
        help="Directory containing HTML files (default: KB/SickKids)"
    )
    parser.add_argument(
        "--pattern",
        type=str,
        default="*.html",
        help="File pattern to match (default: *.html)"
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Don't create backup files"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without modifying files"
    )

    args = parser.parse_args()

    directory = Path(args.directory)

    if not directory.exists():
        logger.error(f"Directory not found: {directory}")
        return 1

    clean_directory(
        directory,
        pattern=args.pattern,
        backup=not args.no_backup,
        dry_run=args.dry_run
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())

