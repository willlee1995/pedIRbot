"""
Create comprehensive Q&A XML dataset from procedure knowledge base using SIR standard questions.

This script transforms procedure documents into structured XML Q&A pairs following the
Society of Interventional Radiology (SIR) parent education standards.
"""
import sys
import os
from pathlib import Path
from typing import Dict, List, Tuple
import xml.etree.ElementTree as ET
from xml.dom import minidom
import re

# Add parent directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from loguru import logger


# SIR Standard Questions for Pediatric Interventional Radiology
SIR_QUESTIONS = [
    "Why is the treatment being recommended for my child?",
    "What are the benefits and potential risks of the treatment?",
    "Are there alternative options?",
    "How will the treatment be performed?",
    "Will my child require sedation or anesthesia? Will a pediatric anesthesia specialist be provided?",
    "What special preparations will we need to make to ensure my child is ready for the treatment?",
    "May they eat or drink prior to the procedure? If not, for how long must they abstain from food and drink?",
    "Will my child need to stay in a hospital? If so, for how long?",
    "Will there be any restrictions on my child's activities? If so, when can my child return to normal activity?",
    "What follow up will be required after the treatment?",
]


class QnACurator:
    """Curate procedure knowledge into structured Q&A format."""

    def __init__(self, source_dir: str, output_dir: str):
        """
        Initialize curator.

        Args:
            source_dir: Directory containing procedure text files
            output_dir: Directory to save XML Q&A files
        """
        self.source_dir = Path(source_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def extract_procedure_name(self, filename: str) -> str:
        """Extract procedure name from filename."""
        # Remove 'original_' prefix and timestamp suffix
        name = re.sub(r'^original_', '', filename)
        name = re.sub(r'_\d{8}_\d{6}\.txt$', '', name)
        # Replace underscores with spaces and capitalize
        name = name.replace('_', ' ').title()
        return name

    def read_procedure_content(self, file_path: Path) -> str:
        """Read procedure content from file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading {file_path}: {e}")
            return ""

    def parse_procedure_sections(self, content: str) -> Dict[str, str]:
        """
        Parse procedure content into sections.

        Expected sections:
        - What is [procedure]?
        - How does the procedure work?
        - Why perform it?
        - Where to perform it?
        - What are the risks?
        """
        sections = {}

        # Extract sections using regex
        patterns = {
            'definition': r'##\s*(?:What is|Definition)[^\n]*\n(.*?)(?=##|$)',
            'how_it_works': r'##\s*How does the procedure work\?\n(.*?)(?=##|$)',
            'why_perform': r'##\s*Why perform it\?\n(.*?)(?=##|$)',
            'where_perform': r'##\s*Where to perform it\?\n(.*?)(?=##|$)',
            'risks': r'##\s*What are the risks\?\n(.*?)(?=##|$)',
            'other': r'##\s*[^#]*?\n(.*?)(?=##|$)',
        }

        for key, pattern in patterns.items():
            match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
            if match:
                sections[key] = match.group(1).strip()

        return sections

    def generate_answer(self, question: str, sections: Dict[str, str], procedure_name: str) -> str:
        """
        Generate answer for a given question based on procedure sections.

        Args:
            question: The SIR standard question
            sections: Parsed procedure sections
            procedure_name: Name of the procedure

        Returns:
            Generated answer text
        """
        q_lower = question.lower()

        # Map questions to relevant sections
        if "why" in q_lower and "recommended" in q_lower:
            answer = sections.get('why_perform', '')
            if not answer:
                answer = sections.get('definition', '')
            return self._clean_text(answer)

        elif "benefits" in q_lower and "risks" in q_lower:
            risks = sections.get('risks', '')
            definition = sections.get('definition', '')
            benefits = sections.get('why_perform', '')
            answer = f"Benefits: {benefits}\n\nRisks: {risks}"
            return self._clean_text(answer)

        elif "alternative" in q_lower:
            # Extract alternatives from definition or how_it_works
            content = sections.get('how_it_works', '')
            if not content:
                content = sections.get('definition', '')
            return self._clean_text(content)

        elif "performed" in q_lower or "how" in q_lower:
            answer = sections.get('how_it_works', '')
            return self._clean_text(answer)

        elif "sedation" in q_lower or "anesthesia" in q_lower:
            content = sections.get('how_it_works', '')
            if 'anesthetized' in content.lower() or 'sedation' in content.lower():
                return self._clean_text(content)
            return "Please consult with your interventional radiologist about anesthesia requirements for this specific procedure."

        elif "preparation" in q_lower or "prepare" in q_lower:
            return "Specific preparation instructions will be provided by your medical team based on your child's individual needs and the nature of the procedure."

        elif "eat" in q_lower or "drink" in q_lower or "abstain" in q_lower:
            return "Fasting requirements will be provided by your medical team. In most cases, you will receive specific instructions on when to stop eating and drinking before the procedure."

        elif "hospital" in q_lower or "stay" in q_lower:
            return "The length of hospital stay depends on the specific procedure and your child's condition. Your medical team will discuss this with you."

        elif "restriction" in q_lower or "activity" in q_lower or "return" in q_lower:
            return "Activity restrictions after the procedure will depend on the specific procedure performed. Your medical team will provide detailed post-procedure instructions."

        elif "follow" in q_lower or "follow-up" in q_lower:
            return "Follow-up care may include imaging studies, clinical examinations, or additional procedures as determined by your interventional radiologist."

        else:
            # Default: return relevant content
            return self._clean_text(sections.get('definition', ''))

    def _clean_text(self, text: str) -> str:
        """Clean and format text for XML."""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove markdown formatting
        text = re.sub(r'[*_#\[\]`]', '', text)
        # Remove bibliography references
        text = re.sub(r'\d+\.\s*\w+.*$', '', text, flags=re.MULTILINE)
        return text.strip()

    def create_qna_xml(self, procedure_name: str, sections: Dict[str, str]) -> ET.Element:
        """
        Create XML element for procedure Q&A.

        Args:
            procedure_name: Name of the procedure
            sections: Parsed procedure sections

        Returns:
            XML Element containing Q&A pairs
        """
        # Create root procedure element
        procedure_elem = ET.Element('procedure')
        procedure_elem.set('name', procedure_name)

        # Create Q&A pairs
        qna_set = ET.SubElement(procedure_elem, 'qna_set')

        for idx, question in enumerate(SIR_QUESTIONS, 1):
            # Generate answer
            answer = self.generate_answer(question, sections, procedure_name)

            # Skip if answer is empty or too generic
            if len(answer) < 20:
                logger.debug(f"Skipping question {idx}: answer too short")
                continue

            # Create Q&A pair element
            qna = ET.SubElement(qna_set, 'qna')
            qna.set('id', f"q{idx}")

            # Add question
            q_elem = ET.SubElement(qna, 'question')
            q_elem.text = question

            # Add answer
            a_elem = ET.SubElement(qna, 'answer')
            a_elem.text = answer

            # Add metadata
            meta = ET.SubElement(qna, 'metadata')
            ET.SubElement(meta, 'question_category').text = self._categorize_question(question)
            ET.SubElement(meta, 'from_section').text = self._get_source_section(question)

        return procedure_elem

    def _categorize_question(self, question: str) -> str:
        """Categorize question type."""
        q_lower = question.lower()
        if "why" in q_lower or "recommended" in q_lower:
            return "indication"
        elif "benefits" in q_lower or "risks" in q_lower:
            return "risks_benefits"
        elif "alternative" in q_lower:
            return "alternatives"
        elif "performed" in q_lower or "how" in q_lower:
            return "procedure_method"
        elif "sedation" in q_lower or "anesthesia" in q_lower:
            return "anesthesia"
        elif "preparation" in q_lower:
            return "preparation"
        elif "eat" in q_lower or "drink" in q_lower:
            return "fasting"
        elif "hospital" in q_lower or "stay" in q_lower:
            return "hospitalization"
        elif "restriction" in q_lower or "activity" in q_lower:
            return "recovery_activity"
        elif "follow" in q_lower:
            return "follow_up"
        else:
            return "general"

    def _get_source_section(self, question: str) -> str:
        """Identify which section of procedure document this question pertains to."""
        q_lower = question.lower()
        if "why" in q_lower or "recommended" in q_lower:
            return "why_perform"
        elif "how" in q_lower:
            return "how_it_works"
        elif "risks" in q_lower or "benefits" in q_lower:
            return "risks"
        else:
            return "general"

    def prettify_xml(self, elem: ET.Element) -> str:
        """Return a pretty-printed XML string."""
        rough_string = ET.tostring(elem, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")

    def curate_procedures(self):
        """Curate all procedures from source directory."""
        logger.info("=" * 80)
        logger.info("PEDIATRIC IR - Q&A CURATION (SIR Standards)")
        logger.info("=" * 80)
        logger.info(f"Source: {self.source_dir}")
        logger.info(f"Output: {self.output_dir}")
        logger.info("=" * 80)

        # Find all procedure files
        procedure_files = sorted(self.source_dir.glob('original_*.txt'))

        if not procedure_files:
            logger.warning("No procedure files found!")
            return

        logger.info(f"\nFound {len(procedure_files)} procedures to curate\n")

        # Process each procedure
        master_qna = ET.Element('procedures')
        master_qna.set('total', str(len(procedure_files)))

        for file_path in procedure_files:
            try:
                logger.info(f"Processing: {file_path.name}")

                # Extract procedure name
                procedure_name = self.extract_procedure_name(file_path.name)
                logger.info(f"  Procedure: {procedure_name}")

                # Read content
                content = self.read_procedure_content(file_path)
                if not content:
                    logger.warning(f"  ⚠️  No content read")
                    continue

                # Parse sections
                sections = self.parse_procedure_sections(content)
                logger.info(f"  Sections found: {', '.join(sections.keys())}")

                # Create Q&A XML
                proc_elem = self.create_qna_xml(procedure_name, sections)

                # Count Q&A pairs
                qna_count = len(proc_elem.find('qna_set'))
                logger.info(f"  ✅ Generated {qna_count} Q&A pairs")

                # Add to master
                master_qna.append(proc_elem)

                # Save individual procedure XML
                output_file = self.output_dir / f"{procedure_name.lower().replace(' ', '_')}_qna.xml"
                xml_str = self.prettify_xml(proc_elem)
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(xml_str)
                logger.info(f"  Saved: {output_file.name}\n")

            except Exception as e:
                logger.error(f"  ❌ Error processing {file_path.name}: {e}\n")
                continue

        # Save master Q&A file
        master_file = self.output_dir / "procedures_master_qna.xml"
        xml_str = self.prettify_xml(master_qna)
        with open(master_file, 'w', encoding='utf-8') as f:
            f.write(xml_str)

        logger.info("=" * 80)
        logger.info(f"✅ Curation complete!")
        logger.info(f"Master file saved: {master_file}")
        logger.info("=" * 80)


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Curate procedure documents into SIR standard Q&A XML format"
    )
    parser.add_argument(
        "source_dir",
        type=str,
        nargs='?',
        default="KB/CIRSE ped procedure info",
        help="Source directory containing procedure files (default: KB/CIRSE ped procedure info)"
    )
    parser.add_argument(
        "output_dir",
        type=str,
        nargs='?',
        default="KB/qna_xml",
        help="Output directory for XML Q&A files (default: KB/qna_xml)"
    )

    args = parser.parse_args()

    source_dir = Path(args.source_dir)
    output_dir = Path(args.output_dir)

    # Validate source
    if not source_dir.exists():
        logger.error(f"Source directory not found: {source_dir}")
        return 1

    # Create curator
    curator = QnACurator(str(source_dir), str(output_dir))

    # Curate procedures
    curator.curate_procedures()

    return 0


if __name__ == "__main__":
    sys.exit(main())

