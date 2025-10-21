"""Convert all documents in KB/ to markdown and store in KB/md/."""
import sys
import os
from pathlib import Path
import shutil

# Add parent directory to path FIRST
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from loguru import logger
from markitdown import MarkItDown
from tqdm import tqdm
import re


class MarkdownConverter:
    """Convert documents to markdown format."""

    # Supported file types
    SUPPORTED_EXTENSIONS = {
        '.pdf', '.docx', '.pptx', '.xlsx',
        '.html', '.htm',
        '.jpg', '.jpeg', '.png',
        '.mp3', '.wav'
    }

    def __init__(self, source_dir: str, output_dir: str):
        """
        Initialize converter.

        Args:
            source_dir: Source directory containing documents
            output_dir: Output directory for markdown files
        """
        self.source_dir = Path(source_dir)
        self.output_dir = Path(output_dir)
        self.markitdown = MarkItDown()

        # Statistics
        self.stats = {
            'total_files': 0,
            'converted': 0,
            'skipped': 0,
            'failed': 0,
            'already_md': 0
        }

    def _should_convert(self, file_path: Path) -> bool:
        """Check if file should be converted."""
        # Skip if already markdown
        if file_path.suffix.lower() in ['.md', '.markdown']:
            return False

        # Check if supported
        return file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS

    def _get_output_path(self, source_file: Path) -> Path:
        """
        Get output path for converted markdown file.

        Preserves directory structure from source.
        """
        # Get relative path from source_dir
        rel_path = source_file.relative_to(self.source_dir)

        # Change extension to .md
        output_rel = rel_path.with_suffix('.md')

        # Combine with output directory
        output_path = self.output_dir / output_rel

        return output_path

    def _clean_markdown(self, markdown_text: str) -> str:
        """
        Clean up converted markdown.

        Removes excessive blank lines and other artifacts.
        """
        # Remove excessive blank lines (more than 2)
        text = re.sub(r'\n{3,}', '\n\n', markdown_text)

        # Remove trailing whitespace
        lines = [line.rstrip() for line in text.splitlines()]
        text = '\n'.join(lines)

        return text.strip()

    def convert_file(self, file_path: Path, force: bool = False) -> bool:
        """
        Convert a single file to markdown.

        Args:
            file_path: Path to file to convert
            force: Force conversion even if output exists

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get output path
            output_path = self._get_output_path(file_path)

            # Check if already exists
            if output_path.exists() and not force:
                logger.debug(f"Skipping {file_path.name} (already converted)")
                self.stats['skipped'] += 1
                return True

            # Create output directory
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Convert to markdown
            logger.debug(f"Converting {file_path.name}...")
            result = self.markitdown.convert(str(file_path))
            markdown_text = result.text_content

            # Clean up markdown
            markdown_text = self._clean_markdown(markdown_text)

            # Check if content is too short (likely just metadata)
            if len(markdown_text.strip()) < 100:
                logger.warning(f"⚠️  {file_path.name} converted to very short content ({len(markdown_text)} chars)")

            # Write to output
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(markdown_text)

            logger.debug(f"✅ Converted {file_path.name} → {output_path.name} ({len(markdown_text)} chars)")
            self.stats['converted'] += 1
            return True

        except Exception as e:
            logger.error(f"❌ Failed to convert {file_path.name}: {e}")
            self.stats['failed'] += 1
            return False

    def copy_markdown_files(self, force: bool = False):
        """Copy existing markdown files to output directory."""
        logger.info("Copying existing markdown files...")

        md_files = list(self.source_dir.rglob('*.md')) + list(self.source_dir.rglob('*.markdown'))

        if not md_files:
            logger.info("No existing markdown files found")
            return

        copied = 0
        for md_file in md_files:
            try:
                output_path = self._get_output_path(md_file)

                # Skip if exists and not forcing
                if output_path.exists() and not force:
                    self.stats['skipped'] += 1
                    continue

                # Create output directory
                output_path.parent.mkdir(parents=True, exist_ok=True)

                # Copy file
                shutil.copy2(md_file, output_path)
                copied += 1
                self.stats['already_md'] += 1

            except Exception as e:
                logger.error(f"Failed to copy {md_file.name}: {e}")

        logger.info(f"Copied {copied} existing markdown files")

    def convert_directory(self, force: bool = False, recursive: bool = True):
        """
        Convert all supported files in source directory.

        Args:
            force: Force conversion even if output exists
            recursive: Recursively process subdirectories
        """
        logger.info("=" * 70)
        logger.info("MARKDOWN CONVERSION")
        logger.info("=" * 70)
        logger.info(f"Source: {self.source_dir}")
        logger.info(f"Output: {self.output_dir}")
        logger.info(f"Force: {force}")
        logger.info(f"Recursive: {recursive}")
        logger.info("=" * 70)

        # Find all files to convert
        logger.info("\n🔍 Scanning for files...")

        if recursive:
            all_files = [f for f in self.source_dir.rglob('*') if f.is_file()]
        else:
            all_files = [f for f in self.source_dir.glob('*') if f.is_file()]

        # Filter to supported files
        files_to_convert = [f for f in all_files if self._should_convert(f)]

        self.stats['total_files'] = len(files_to_convert)

        logger.info(f"Found {len(all_files)} total files")
        logger.info(f"Found {len(files_to_convert)} files to convert")
        logger.info(f"Supported types: {', '.join(sorted(self.SUPPORTED_EXTENSIONS))}")

        if not files_to_convert:
            logger.warning("No files to convert!")
            return

        # Convert files with progress bar
        logger.info("\n🔄 Converting files...")

        with tqdm(total=len(files_to_convert), desc="Converting", unit="file") as pbar:
            for file_path in files_to_convert:
                self.convert_file(file_path, force=force)
                pbar.update(1)

        # Copy existing markdown files
        self.copy_markdown_files(force=force)

        # Print summary
        logger.info("\n" + "=" * 70)
        logger.info("CONVERSION SUMMARY")
        logger.info("=" * 70)
        logger.info(f"Total files scanned:     {len(all_files)}")
        logger.info(f"Files to convert:        {self.stats['total_files']}")
        logger.info(f"✅ Successfully converted: {self.stats['converted']}")
        logger.info(f"📄 Markdown files copied:  {self.stats['already_md']}")
        logger.info(f"⏭️  Skipped (exists):       {self.stats['skipped']}")
        logger.info(f"❌ Failed:                 {self.stats['failed']}")
        logger.info("=" * 70)

        if self.stats['failed'] > 0:
            logger.warning(f"\n⚠️  {self.stats['failed']} files failed to convert. Check logs for details.")

        logger.info(f"\n✅ Conversion complete! Markdown files saved to: {self.output_dir}")
        logger.info(f"\nNext step: python scripts/ingest_documents.py {self.output_dir} --reset")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Convert all documents to markdown format"
    )
    parser.add_argument(
        "source_dir",
        type=str,
        nargs='?',
        default="KB",
        help="Source directory containing documents (default: KB)"
    )
    parser.add_argument(
        "output_dir",
        type=str,
        nargs='?',
        default="KB/md",
        help="Output directory for markdown files (default: KB/md)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force conversion even if output files exist"
    )
    parser.add_argument(
        "--no-recursive",
        action="store_true",
        help="Don't recursively process subdirectories"
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean output directory before conversion"
    )

    args = parser.parse_args()

    source_dir = Path(args.source_dir)
    output_dir = Path(args.output_dir)

    # Validate source
    if not source_dir.exists():
        logger.error(f"Source directory not found: {source_dir}")
        return 1

    # Clean output if requested
    if args.clean and output_dir.exists():
        logger.warning(f"🗑️  Cleaning output directory: {output_dir}")
        response = input("Are you sure? This will delete all files in the output directory. (yes/no): ")
        if response.lower() == 'yes':
            shutil.rmtree(output_dir)
            logger.info("Output directory cleaned")
        else:
            logger.info("Clean cancelled")
            return 0

    # Create converter
    converter = MarkdownConverter(source_dir, output_dir)

    # Convert
    converter.convert_directory(
        force=args.force,
        recursive=not args.no_recursive
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())

