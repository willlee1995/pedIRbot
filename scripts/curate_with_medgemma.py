"""
High-quality Q&A curation using MedGemma for pediatric IR procedures.

This script processes markdown documents and uses MedGemma (via Ollama) to generate
comprehensive, clinically accurate answers to the 10 SIR standard questions for
pediatric interventional radiology patients.

The output is structured XML following the Q&A format for RAG integration.
"""
import sys
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import xml.etree.ElementTree as ET
from xml.dom import minidom
import re
import time
from collections import defaultdict

# Add parent directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from loguru import logger
from config import settings

try:
    from src.llm import get_llm_provider
except ImportError:
    logger.warning("Could not import LLM provider, will use direct Ollama connection")
    get_llm_provider = None


# Pediatric IR SIR Standard Questions
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


class MedGemmaCurator:
    """Curate procedure knowledge into structured Q&A using MedGemma LLM."""

    def __init__(self, output_dir: str, use_ollama: bool = None):
        """
        Initialize curator with LLM provider.

        Args:
            output_dir: Directory to save XML Q&A files
            use_ollama: Whether to use Ollama (True) or OpenAI (False)
                       If None, reads from config settings
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Determine provider: explicit arg > config settings > default to Ollama
        if use_ollama is None:
            # Read from config
            self.use_ollama = (settings.llm_provider == "ollama")
            logger.info(f"LLM Provider from config: {settings.llm_provider}")
        else:
            self.use_ollama = use_ollama
            
        self.llm_provider = None
        self.procedures_processed = 0
        self.total_questions_generated = 0

        # Initialize LLM
        self._init_llm()

    def _init_llm(self):
        """Initialize LLM provider."""
        try:
            if get_llm_provider:
                provider_name = "ollama" if self.use_ollama else "openai"
                self.llm_provider = get_llm_provider(provider=provider_name)
                logger.info(f"✅ LLM initialized: {self.llm_provider.__class__.__name__}")
                logger.info(f"   Provider: {provider_name}")
                if not self.use_ollama:
                    logger.info(f"   API Base: {settings.openai_api_base}")
                    logger.info(f"   Model: {settings.openai_chat_model}")
            else:
                logger.warning("LLM provider not available, will use Ollama directly")
        except Exception as e:
            logger.error(f"Error initializing LLM: {e}")
            logger.warning("Will attempt direct Ollama connection")

    def extract_procedure_name(self, filename: str) -> str:
        """
        Extract procedure name from markdown filename.

        Examples:
            "EN01 Angioplasty and stent eng 2010.md" → "Angioplasty and Stent"
            "ablation_pediatric.md" → "Ablation Pediatric"
        """
        # Remove extension
        name = Path(filename).stem

        # Remove prefixes like "EN01", timestamps, etc.
        name = re.sub(r'^EN\d+\s*', '', name)  # Remove "EN01 " prefix
        name = re.sub(r'\s+(eng|ENG|2010|2015)\s*$', '', name)  # Remove language/year suffix
        name = re.sub(r'_\d{8}_\d{6}', '', name)  # Remove timestamps

        # Clean up and title case
        name = name.replace('_', ' ').replace('-', ' ')
        name = ' '.join(word.capitalize() for word in name.split())

        return name

    def read_markdown(self, file_path: Path) -> str:
        """Read markdown file content."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading {file_path}: {e}")
            return ""

    def extract_key_sections(self, content: str) -> Dict[str, str]:
        """
        Extract key sections from markdown content.

        Handles multiple formats:
        1. Markdown headers: ## What is...
        2. Plain text headers: What is...
        3. HTML remnants: <h2>What is...</h2>

        Looks for headers like:
        - ## What is...
        - What is...
        - <h2>What is...</h2>
        - Introduction
        - Procedure
        - Risks
        - Indications
        """
        sections = {}

        # First, clean HTML tags
        content_clean = re.sub(r'<h[1-6][^>]*>(.*?)</h[1-6]>', r'\1', content, flags=re.IGNORECASE)
        content_clean = re.sub(r'<[^>]+>', '', content_clean)
        content_clean = re.sub(r'&[a-z]+;', '', content_clean)

        # Strategy 1: Try markdown headers (## Header)
        header_pattern = r'^##\s+(.+?)\n(.*?)(?=^##|\Z)'
        matches = list(re.finditer(header_pattern, content_clean, re.MULTILINE | re.DOTALL))

        if matches:
            for match in matches:
                header_title = match.group(1).strip().lower()
                header_content = match.group(2).strip()
                self._categorize_section(sections, header_title, header_content)
            return sections

        # Strategy 2: Look for plain text headers (single word/phrase at start of line followed by content)
        # This handles formats like:
        # Introduction
        # 
        # Some content here...
        #
        # Procedure
        # More content...
        
        plain_headers = [
            ('overview', ['introduction', 'background', 'what is', 'definition', 'overview']),
            ('procedure', ['procedure', 'how', 'technique', 'method', 'performing', 'process', 'treatment is performed']),
            ('indication', ['indication', 'why', 'reason', 'purpose', 'indications', 'clinical use', 'when']),
            ('risks', ['risk', 'complication', 'adverse', 'side effect', 'dangers', 'complications', 'what could go wrong']),
            ('benefits', ['benefit', 'advantage', 'goal', 'outcome', 'benefit']),
            ('preparation', ['preparation', 'prepare', 'before', 'fast', 'fasting', 'pre-procedure', 'getting ready', 'beforehand']),
            ('followup', ['follow', 'follow-up', 'recovery', 'after', 'post-procedure', 'care after', 'home', 'outcome'])
        ]
        
        for section_type, keywords in plain_headers:
            for keyword in keywords:
                # Match keyword at start of line (case-insensitive), followed by blank line and content
                # This pattern is more lenient
                pattern = rf'(?:^|\n)({re.escape(keyword)}[^\n]*?)\s*\n\s*\n(.+?)(?=(?:\n\n(?:' + '|'.join(kw for _, kws in plain_headers for kw in kws) + r'))|$)'
                
                matches_for_keyword = list(re.finditer(pattern, content_clean, re.MULTILINE | re.IGNORECASE | re.DOTALL))
                
                if matches_for_keyword:
                    for match in matches_for_keyword:
                        header_content = match.group(2).strip()
                        if len(header_content) > 50:  # Only if substantial content
                            # Prefer longer content if section already exists
                            if section_type not in sections or len(header_content) > len(sections.get(section_type, '')):
                                sections[section_type] = header_content[:2000]
                    if section_type in sections:
                        break  # Found this section type, move to next
        
        # Strategy 3: More aggressive - just look for section keywords anywhere as delimiters
        if len(sections) < 3:  # If we haven't found enough sections yet
            all_keywords = [kw for _, kws in plain_headers for kw in kws]
            # Escape and join keywords for regex
            escaped_keywords = [re.escape(kw) for kw in all_keywords]
            delimiter_pattern = r'\n(' + '|'.join(escaped_keywords) + r')[^\n]*\n'
            
            try:
                # Split by keyword delimiters
                parts = re.split(delimiter_pattern, content_clean, flags=re.IGNORECASE)
                
                # Process splits: alternating between delimiters and content
                for i in range(1, len(parts), 2):
                    if i + 1 < len(parts):
                        keyword = parts[i].lower()
                        content_part = parts[i + 1].strip()
                        
                        if len(content_part) > 50:
                            for section_type, keywords_list in plain_headers:
                                if keyword in [kw.lower() for kw in keywords_list]:
                                    if section_type not in sections or len(content_part) > len(sections.get(section_type, '')):
                                        sections[section_type] = content_part[:2000]
                                    break
            except Exception as e:
                logger.debug(f"Strategy 3 regex split failed: {e}, skipping aggressive extraction")

        # If still missing overview/indication, use beginning of document
        if 'overview' not in sections and 'indication' not in sections:
            first_500 = content_clean[:500].strip()
            if len(first_500) > 50:
                sections['overview'] = first_500

        # If still no sections, treat entire content as general
        if not sections:
            sections['general'] = content_clean[:3000]
        # Also add general content if nothing matched
        elif 'general' not in sections:
            sections['general'] = content_clean[:2000]

        return sections

    def _categorize_section(self, sections: Dict[str, str], header_title: str, header_content: str):
        """Helper to categorize a section by title."""
        if any(word in header_title for word in ['what', 'definition', 'overview', 'introduction', 'background', 'learn']):
            sections['overview'] = header_content
        elif any(word in header_title for word in ['how', 'procedure', 'technique', 'method', 'performance', 'process']):
            sections['procedure'] = header_content
        elif any(word in header_title for word in ['why', 'indication', 'reason', 'purpose', 'when']):
            sections['indication'] = header_content
        elif any(word in header_title for word in ['risk', 'complication', 'adverse']):
            sections['risks'] = header_content
        elif any(word in header_title for word in ['benefit', 'advantage', 'outcome', 'goal']):
            sections['benefits'] = header_content
        elif any(word in header_title for word in ['preparation', 'prepare', 'before', 'fast']):
            sections['preparation'] = header_content
        elif any(word in header_title for word in ['recover', 'follow', 'after', 'outcome']):
            sections['followup'] = header_content
        else:
            if 'general' not in sections:
                sections['general'] = ""
            sections['general'] += "\n\n" + header_content

    def generate_answer_with_medgemma(
        self,
        question: str,
        procedure_name: str,
        sections: Dict[str, str],
        attempt: int = 1
    ) -> str:
        """
        Generate answer using MedGemma LLM.

        Args:
            question: The SIR question
            procedure_name: Name of the procedure
            sections: Extracted content sections
            attempt: Attempt number for retries

        Returns:
            Generated answer text
        """
        if attempt > 3:
            logger.warning(f"Max retries reached for question about {procedure_name}")
            return self._generate_fallback_answer(question, sections, procedure_name)

        # Build context from relevant sections
        context = self._build_context_for_question(question, sections)

        if not context:
            logger.debug(f"No context found for {procedure_name} - {question[:50]}...")
            return self._generate_fallback_answer(question, sections, procedure_name)

        # Create prompt for MedGemma
        prompt = self._create_medgemma_prompt(
            question=question,
            procedure_name=procedure_name,
            context=context
        )

        try:
            response = None
            
            # Priority 1: Direct Ollama call (most reliable)
            if not self.llm_provider:
                logger.debug("No LLM provider configured, using direct Ollama")
                response = self._call_ollama_direct(prompt)
            else:
                # Try to use LLM provider with messages format
                logger.debug(f"Using LLM provider: {self.llm_provider.__class__.__name__}")
                
                # Build messages in the format expected by LLM providers
                messages = [
                    {"role": "system", "content": "You are a pediatric interventional radiology expert helping parents understand medical procedures. Provide clear, compassionate, and clinically accurate answers suitable for parents."},
                    {"role": "user", "content": prompt}
                ]
                
                try:
                    # Try with standard parameters
                    response = self.llm_provider.generate(
                        messages=messages,
                        temperature=0.3,
                        max_tokens=500
                    )
                except TypeError as e:
                    logger.debug(f"LLM provider with messages failed: {e}")
                    # Fallback to direct Ollama
                    try:
                        response = self._call_ollama_direct(prompt)
                    except Exception as e2:
                        logger.debug(f"Direct Ollama also failed: {e2}")
                        raise

            if response and len(response.strip()) > 20:
                logger.debug(f"✓ Generated answer for {procedure_name}")
                return response.strip()
            else:
                raise ValueError("Empty or too short response")

        except Exception as e:
            logger.warning(f"LLM generation failed (attempt {attempt}): {type(e).__name__}: {str(e)[:100]}")
            if attempt < 3:
                time.sleep(2)  # Brief delay before retry
                return self.generate_answer_with_medgemma(
                    question, procedure_name, sections, attempt + 1
                )
            else:
                logger.debug(f"Using fallback answer for {procedure_name}")
                return self._generate_fallback_answer(question, sections, procedure_name)

    def _build_context_for_question(self, question: str, sections: Dict[str, str]) -> str:
        """Build relevant context from sections for a specific question."""
        q_lower = question.lower()
        context_parts = []

        # Map questions to relevant sections
        if "why" in q_lower and "recommended" in q_lower:
            if 'indication' in sections:
                context_parts.append(sections['indication'])
            if 'overview' in sections:
                context_parts.append(sections['overview'])
        elif "benefits" in q_lower and "risks" in q_lower:
            if 'benefits' in sections:
                context_parts.append(sections['benefits'])
            if 'risks' in sections:
                context_parts.append(sections['risks'])
        elif "alternative" in q_lower:
            if 'indication' in sections:
                context_parts.append(sections['indication'])
            if 'procedure' in sections:
                context_parts.append(sections['procedure'])
        elif "how" in q_lower and "performed" in q_lower:
            if 'procedure' in sections:
                context_parts.append(sections['procedure'])
        elif "sedation" in q_lower or "anesthesia" in q_lower:
            if 'procedure' in sections:
                context_parts.append(sections['procedure'])
            if 'preparation' in sections:
                context_parts.append(sections['preparation'])
        elif "preparation" in q_lower:
            if 'preparation' in sections:
                context_parts.append(sections['preparation'])
            if 'procedure' in sections:
                context_parts.append(sections['procedure'][:500])
        elif "eat" in q_lower or "drink" in q_lower or "fast" in q_lower:
            if 'preparation' in sections:
                context_parts.append(sections['preparation'])
        elif "hospital" in q_lower or "stay" in q_lower:
            if 'followup' in sections:
                context_parts.append(sections['followup'])
            if 'procedure' in sections:
                context_parts.append(sections['procedure'][:300])
        elif "restriction" in q_lower or "activity" in q_lower or "return" in q_lower:
            if 'followup' in sections:
                context_parts.append(sections['followup'])
        elif "follow" in q_lower:
            if 'followup' in sections:
                context_parts.append(sections['followup'])
        else:
            # Default: use all available content
            context_parts = [v for v in sections.values() if v]

        # Combine and limit context size
        context = "\n\n".join(filter(None, context_parts))
        return context[:2000]  # Limit to 2000 chars for LLM context

    def _create_medgemma_prompt(self, question: str, procedure_name: str, context: str) -> str:
        """Create a prompt optimized for MedGemma."""
        return f"""You are a pediatric interventional radiology expert helping parents understand medical procedures.

PROCEDURE: {procedure_name}

BACKGROUND INFORMATION:
{context}

QUESTION FROM PARENT: {question}

Please provide a clear, compassionate, and clinically accurate answer suitable for parents of pediatric patients. 
Focus on:
1. Being understandable to non-medical parents
2. Being accurate and based on the procedure information provided
3. Addressing pediatric-specific concerns
4. Being honest about uncertainties (e.g., "This will be discussed with your medical team")

ANSWER:"""

    def _call_ollama_direct(self, prompt: str) -> str:
        """Call Ollama directly if LLM provider is not available."""
        try:
            import requests
            import json

            ollama_url = settings.ollama_api_base or "http://localhost:11434"
            model = settings.ollama_chat_model or "alibayram/medgemma"

            response = requests.post(
                f"{ollama_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "temperature": 0.3,
                    "num_predict": 500,
                    "stream": False,
                },
                timeout=120
            )

            if response.status_code == 200:
                result = response.json()
                return result.get("response", "").strip()
            else:
                logger.error(f"Ollama API error: {response.status_code}")
                return ""

        except Exception as e:
            logger.error(f"Error calling Ollama: {e}")
            return ""

    def _generate_fallback_answer(
        self,
        question: str,
        sections: Dict[str, str],
        procedure_name: str
    ) -> str:
        """Generate fallback answer when LLM is not available."""
        q_lower = question.lower()

        # Extract best matching section content
        relevant_content = ""

        if "why" in q_lower and "recommended" in q_lower:
            relevant_content = sections.get('indication', sections.get('overview', ''))
        elif "benefits" in q_lower or "risks" in q_lower:
            relevant_content = sections.get('risks', sections.get('benefits', ''))
        elif "alternative" in q_lower:
            relevant_content = sections.get('indication', sections.get('procedure', ''))
        elif "how" in q_lower:
            relevant_content = sections.get('procedure', '')
        elif "sedation" in q_lower or "anesthesia" in q_lower:
            relevant_content = sections.get('procedure', '')
        elif "preparation" in q_lower or "fast" in q_lower or "eat" in q_lower:
            relevant_content = sections.get('preparation', '')
        elif "follow" in q_lower or "activity" in q_lower:
            relevant_content = sections.get('followup', '')
        else:
            relevant_content = sections.get('overview', sections.get('general', ''))

        # Clean and trim
        relevant_content = self._clean_text(relevant_content)
        if len(relevant_content) > 500:
            relevant_content = relevant_content[:500] + "..."

        if relevant_content:
            return relevant_content
        else:
            return f"Please consult with your pediatric interventional radiologist for specific details about {procedure_name}."

    def _clean_text(self, text: str) -> str:
        """Clean and format text for XML."""
        if not text:
            return ""

        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)

        # Remove markdown formatting
        text = re.sub(r'[*_#\[\]`]', '', text)

        # Remove reference markers like [1], [2], etc.
        text = re.sub(r'\[\d+\]', '', text)

        # Remove URLs
        text = re.sub(r'https?://[^\s]+', '', text)

        return text.strip()

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

    def create_qna_xml(
        self,
        procedure_name: str,
        sections: Dict[str, str]
    ) -> ET.Element:
        """
        Create XML element for procedure Q&A using MedGemma.

        Args:
            procedure_name: Name of the procedure
            sections: Parsed procedure sections

        Returns:
            XML Element containing Q&A pairs
        """
        procedure_elem = ET.Element('procedure')
        procedure_elem.set('name', procedure_name)
        procedure_elem.set('curation_method', 'medgemma')

        qna_set = ET.SubElement(procedure_elem, 'qna_set')
        generated_count = 0

        for idx, question in enumerate(SIR_QUESTIONS, 1):
            logger.info(f"  Q{idx}: {question[:60]}...")

            # Generate answer using MedGemma
            answer = self.generate_answer_with_medgemma(question, procedure_name, sections)

            # Validate answer
            if not answer or len(answer) < 20:
                logger.debug(f"  ⚠️  Skipping Q{idx}: answer too short or empty")
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
            ET.SubElement(meta, 'curation_model').text = settings.ollama_chat_model or 'alibayram/medgemma'
            ET.SubElement(meta, 'confidence').text = 'high'  # Assume high confidence for now

            generated_count += 1
            self.total_questions_generated += 1

        logger.info(f"  ✅ Generated {generated_count} Q&A pairs")
        return procedure_elem

    def prettify_xml(self, elem: ET.Element) -> str:
        """Return a pretty-printed XML string."""
        rough_string = ET.tostring(elem, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")

    def curate_from_markdown_directory(self, markdown_dir: str):
        """
        Curate all procedures from markdown directory using MedGemma.

        Args:
            markdown_dir: Directory containing markdown files
        """
        logger.info("=" * 80)
        logger.info("PEDIATRIC IR - HIGH-QUALITY Q&A CURATION WITH MEDGEMMA")
        logger.info("=" * 80)
        logger.info(f"Source: {markdown_dir}")
        logger.info(f"Output: {self.output_dir}")
        logger.info(f"LLM: {settings.ollama_chat_model or 'alibayram/medgemma'}")
        logger.info("=" * 80)

        md_path = Path(markdown_dir)
        if not md_path.exists():
            logger.error(f"Markdown directory not found: {markdown_dir}")
            return

        # Find all markdown files
        markdown_files = sorted(md_path.rglob('*.md'))
        logger.info(f"\nFound {len(markdown_files)} markdown files\n")

        # Group by source
        by_source = defaultdict(list)
        for md_file in markdown_files:
            source = md_file.parent.name
            by_source[source].append(md_file)

        # Create master QNA
        master_qna = ET.Element('procedures')
        master_qna.set('total', str(len(markdown_files)))
        master_qna.set('curation_method', 'medgemma')

        # Process each source
        for source_name, source_files in sorted(by_source.items()):
            logger.info(f"\n{'='*60}")
            logger.info(f"Processing source: {source_name} ({len(source_files)} files)")
            logger.info(f"{'='*60}\n")

            # Process documents 21 onwards (skip first 20)
            start_idx = 20
            end_idx = None  # Process until the end
            files_to_process = source_files[start_idx:end_idx]
            
            logger.info(f"Processing documents {start_idx + 1} to {len(source_files)} ({len(files_to_process)} files)\n")
            
            for md_file in files_to_process:
                try:
                    logger.info(f"Processing: {md_file.name}")

                    # Extract procedure name
                    procedure_name = self.extract_procedure_name(md_file.name)
                    logger.info(f"  Procedure: {procedure_name}")

                    # Read content
                    content = self.read_markdown(md_file)
                    if not content or len(content) < 100:
                        logger.warning(f"  ⚠️  Content too short")
                        continue

                    # Extract sections
                    sections = self.extract_key_sections(content)
                    logger.info(f"  Sections: {', '.join(sections.keys())}")

                    # Create Q&A using MedGemma
                    proc_elem = self.create_qna_xml(procedure_name, sections)

                    # Add to master
                    master_qna.append(proc_elem)
                    self.procedures_processed += 1

                    # Save individual procedure XML
                    output_file = (
                        self.output_dir /
                        f"{procedure_name.lower().replace(' ', '_')}_qna_medgemma.xml"
                    )
                    xml_str = self.prettify_xml(proc_elem)
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(xml_str)
                    logger.info(f"  Saved: {output_file.name}\n")

                except Exception as e:
                    logger.error(f"  ❌ Error: {e}\n")
                    continue

        # Save master file
        if self.procedures_processed > 0:
            master_file = self.output_dir / "procedures_master_qna_medgemma.xml"
            xml_str = self.prettify_xml(master_qna)
            with open(master_file, 'w', encoding='utf-8') as f:
                f.write(xml_str)

            logger.info("=" * 80)
            logger.info("✅ CURATION COMPLETE!")
            logger.info(f"Procedures processed: {self.procedures_processed}")
            logger.info(f"Q&A pairs generated: {self.total_questions_generated}")
            logger.info(f"Master file saved: {master_file}")
            logger.info("=" * 80)
        else:
            logger.warning("No procedures were successfully processed")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Curate pediatric IR procedures into high-quality Q&A"
    )
    parser.add_argument(
        "markdown_dir",
        type=str,
        nargs='?',
        default="KB/md",
        help="Source directory containing markdown files (default: KB/md)"
    )
    parser.add_argument(
        "output_dir",
        type=str,
        nargs='?',
        default="KB/qna_xml",
        help="Output directory for XML Q&A files (default: KB/qna_xml)"
    )
    parser.add_argument(
        "--use-openai",
        action="store_true",
        help="Force use of OpenAI (overrides .env setting)"
    )
    parser.add_argument(
        "--use-ollama",
        action="store_true",
        help="Force use of Ollama (overrides .env setting)"
    )

    args = parser.parse_args()

    markdown_dir = Path(args.markdown_dir)
    output_dir = Path(args.output_dir)

    if not markdown_dir.exists():
        logger.error(f"Markdown directory not found: {markdown_dir}")
        return 1

    # Determine provider
    # Priority: Command line args > .env config > default (Ollama)
    use_ollama = None
    if args.use_openai:
        use_ollama = False
        logger.info("Using OpenAI (from command line)")
    elif args.use_ollama:
        use_ollama = True
        logger.info("Using Ollama (from command line)")
    else:
        logger.info(f"Using provider from .env config: {settings.llm_provider}")

    # Create curator
    curator = MedGemmaCurator(
        output_dir=str(output_dir),
        use_ollama=use_ollama  # None = read from config
    )

    # Curate procedures
    curator.curate_from_markdown_directory(str(markdown_dir))

    return 0


if __name__ == "__main__":
    sys.exit(main())
