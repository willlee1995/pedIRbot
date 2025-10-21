"""Filter SickKids content to keep only procedure-related articles."""
import sys
import os
from pathlib import Path

# Add parent directory to path FIRST
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import re
import shutil
from typing import List, Set

from bs4 import BeautifulSoup
from loguru import logger


class SickKidsContentFilter:
    """Filter SickKids content to keep only procedure-related articles."""

    # Keywords that indicate procedure-related content (KEEP these)
    PROCEDURE_KEYWORDS = [
        # Image-guided procedures
        "image guidance", "image guided", "imaging", "fluoroscopy",
        "ultrasound guided", "ct guided", "mri guided",

        # Interventional procedures
        "biopsy", "drainage", "insertion", "catheter", "picc", "cvl",
        "port", "tube insertion", "line insertion", "ablation",
        "embolization", "angioplasty", "angiography", "sclerotherapy",

        # Procedure-related terms
        "procedure", "intervention", "percutaneous", "minimally invasive",
        "sedation for procedure", "preparation for procedure",
        "caring for your child after", "home care after",

        # Specific procedures
        "nephrostomy", "cecostomy", "gastrostomy", "g tube", "gj tube",
        "chest tube", "myelogram", "arthrogram", "lumbar puncture",
        "central venous", "peripherally inserted", "femoral vein",

        # Interventional radiology specific
        "interventional radiology", "ir procedure", "evlt",
        "varicocele", "abscess", "botox injection", "steroid injection"
    ]

    # Keywords that indicate NON-procedure content (EXCLUDE these)
    EXCLUDE_KEYWORDS = [
        # Mental health / behavioral
        "bulimia", "anorexia", "eating disorder", "body image",
        "mental health", "depression", "anxiety", "self-esteem",
        "guided imagery", "guided meditation", "relaxation",

        # General health topics
        "healthy living", "nutrition", "exercise", "sleep",
        "parenting", "development", "behavioral", "psychology",
        "school", "learning", "social",

        # Non-interventional topics
        "medication", "drug treatment", "oral medicine",
        "symptoms", "diagnosis", "when to call",

        # Teens/kids specific non-procedure
        "teen mental health", "peer pressure", "puberty"
    ]

    def __init__(self, sickkids_dir: str = "KB/SickKids"):
        """
        Initialize filter.

        Args:
            sickkids_dir: SickKids directory to filter
        """
        self.sickkids_dir = Path(sickkids_dir)
        self.excluded_dir = self.sickkids_dir / "excluded"
        self.excluded_dir.mkdir(exist_ok=True)

        logger.info(f"Initialized content filter for: {self.sickkids_dir}")

    def is_procedure_related(self, filepath: Path) -> tuple[bool, str]:
        """
        Check if a file contains procedure-related content.

        Args:
            filepath: Path to HTML file

        Returns:
            Tuple of (is_procedure_related, reason)
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            soup = BeautifulSoup(content, 'html.parser')

            # Get title and text content
            title_tag = soup.find('title') or soup.find('h1')
            title = title_tag.get_text().lower() if title_tag else ""

            # Get main text
            text = soup.get_text().lower()

            # Check for exclusion keywords first (higher priority)
            for keyword in self.EXCLUDE_KEYWORDS:
                if keyword in title or text.count(keyword) > 2:
                    return False, f"Contains exclude keyword: '{keyword}'"

            # Check for procedure keywords
            procedure_matches = []
            for keyword in self.PROCEDURE_KEYWORDS:
                if keyword in title:
                    procedure_matches.append(keyword)
                elif keyword in text:
                    # Count occurrences
                    count = text.count(keyword)
                    if count >= 2:  # Mentioned at least twice
                        procedure_matches.append(keyword)

            if procedure_matches:
                return True, f"Matches keywords: {', '.join(procedure_matches[:3])}"
            else:
                return False, "No strong procedure keywords found"

        except Exception as e:
            logger.error(f"Error analyzing {filepath}: {e}")
            return False, f"Error: {e}"

    def filter_directory(self, dry_run: bool = True) -> dict:
        """
        Filter all HTML files in directory.

        Args:
            dry_run: If True, only report what would be done (don't move files)

        Returns:
            Dictionary with statistics
        """
        html_files = list(self.sickkids_dir.glob("*.html"))

        logger.info(f"Found {len(html_files)} HTML files to analyze")

        keep_files = []
        exclude_files = []

        # Analyze each file
        for filepath in html_files:
            is_procedure, reason = self.is_procedure_related(filepath)

            if is_procedure:
                keep_files.append((filepath, reason))
                logger.info(f"✅ KEEP: {filepath.name}")
                logger.info(f"   Reason: {reason}")
            else:
                exclude_files.append((filepath, reason))
                logger.warning(f"❌ EXCLUDE: {filepath.name}")
                logger.warning(f"   Reason: {reason}")

        # Summary
        logger.info("\n" + "=" * 70)
        logger.info("FILTERING SUMMARY")
        logger.info("=" * 70)
        logger.info(f"Total files analyzed: {len(html_files)}")
        logger.info(f"Keep (procedure-related): {len(keep_files)}")
        logger.info(f"Exclude (non-procedure): {len(exclude_files)}")
        logger.info("=" * 70)

        # Move excluded files
        if not dry_run and exclude_files:
            logger.info(f"\nMoving {len(exclude_files)} files to: {self.excluded_dir}")

            for filepath, reason in exclude_files:
                dest = self.excluded_dir / filepath.name
                shutil.move(str(filepath), str(dest))
                logger.info(f"  Moved: {filepath.name}")

            logger.info(f"\n✓ Excluded files moved to: {self.excluded_dir}")
            logger.info(f"✓ Kept {len(keep_files)} procedure-related files in {self.sickkids_dir}")
        elif exclude_files:
            logger.info(f"\n⚠️  DRY RUN MODE: No files moved")
            logger.info(f"   Run with --execute to actually move files")

        return {
            "total": len(html_files),
            "keep": len(keep_files),
            "exclude": len(exclude_files),
            "keep_files": [str(f[0].name) for f in keep_files],
            "exclude_files": [str(f[0].name) for f in exclude_files]
        }


def main(sickkids_dir: str = "KB/SickKids", dry_run: bool = True):
    """
    Filter SickKids content.

    Args:
        sickkids_dir: SickKids directory
        dry_run: If True, don't actually move files
    """
    logger.info("SickKids Content Filter")
    logger.info("Purpose: Keep only procedure-related content")
    logger.info("=" * 70)

    filter_tool = SickKidsContentFilter(sickkids_dir)
    stats = filter_tool.filter_directory(dry_run=dry_run)

    logger.info("\n📋 RECOMMENDATIONS:")

    if stats["exclude"] > 0:
        logger.info(f"1. Review the {stats['exclude']} files marked for exclusion above")
        logger.info(f"2. If correct, run with --execute to move them")
        logger.info(f"3. Excluded files will be moved to: {sickkids_dir}/excluded/")
        logger.info(f"4. After filtering, re-ingest: python scripts/ingest_documents.py KB/ --reset")
    else:
        logger.info("✅ All files appear to be procedure-related!")
        logger.info("   No filtering needed.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Filter SickKids content to keep only procedure-related articles"
    )
    parser.add_argument(
        "--dir",
        type=str,
        default="KB/SickKids",
        help="SickKids directory to filter"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually move files (default is dry-run)"
    )

    args = parser.parse_args()

    main(args.dir, dry_run=not args.execute)

