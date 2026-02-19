"""LLM-based metadata extraction using OpenRouter with gemini-2.5-flash-lite."""
import json
import re
from typing import Dict, Any, Optional

import httpx
from loguru import logger

from config import settings


# The structured schema for metadata extraction
METADATA_SCHEMA = {
    "procedure_type": "The specific medical procedure discussed (e.g., 'PICC insertion', 'Embolization', 'Biopsy', 'Cecostomy tube insertion'). Use 'General' if not procedure-specific.",
    "doc_type": "The type of document: one of 'Patient Leaflet', 'Appointment Form', 'Clinical Protocol', 'Consent Form', 'Educational Material', 'FAQ', 'Other'.",
    "age_group": "The target age group: one of 'Pediatric', 'Adult', 'All Ages'. Default to 'Pediatric' if discussing children or in a pediatric context.",
    "target_audience": "Who this document is for: one of 'Patient/Parent', 'Clinician', 'Both'.",
}

EXTRACTION_PROMPT = """You are a medical document classifier. Given the following document text, extract structured metadata.

Return ONLY a valid JSON object with these exact fields:
- "procedure_type": {procedure_type}
- "doc_type": {doc_type}
- "age_group": {age_group}
- "target_audience": {target_audience}

Document text (first 2000 characters):
---
{text}
---

Respond with ONLY the JSON object, no other text."""


class MetadataExtractor:
    """Extract structured metadata from document text using an LLM via OpenRouter."""

    def __init__(
        self,
        api_key: str = None,
        api_base: str = None,
        model: str = None,
    ):
        self.api_key = api_key or settings.openrouter_api_key
        self.api_base = api_base or settings.openrouter_api_base
        self.model = model or settings.openrouter_metadata_model
        self.client = httpx.Client(timeout=30.0)
        logger.info(f"MetadataExtractor initialized with model: {self.model}")

    def extract(self, text: str) -> Dict[str, Any]:
        """
        Extract metadata from document text using the LLM.

        Args:
            text: Full document text (will be truncated to first 2000 chars for the prompt)

        Returns:
            Dict with keys: procedure_type, doc_type, age_group, target_audience
        """
        if not text or len(text.strip()) < 20:
            logger.warning("Text too short for metadata extraction, using defaults")
            return self._default_metadata()

        # Build the prompt with first 2000 chars
        truncated_text = text[:2000]
        prompt = EXTRACTION_PROMPT.format(
            text=truncated_text,
            **METADATA_SCHEMA,
        )

        try:
            response = self.client.post(
                f"{self.api_base}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://pedirbot.local",
                    "X-Title": "PedIRBot Metadata Extraction",
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.1,
                    "max_tokens": 300,
                },
            )
            response.raise_for_status()
            result = response.json()

            # Extract the content from the response
            content = result["choices"][0]["message"]["content"].strip()

            # Parse JSON from the response (handle markdown code blocks)
            json_str = self._extract_json(content)
            metadata = json.loads(json_str)

            # Validate fields
            metadata = self._validate_metadata(metadata)

            logger.debug(f"Extracted metadata: {metadata}")
            return metadata

        except httpx.HTTPStatusError as e:
            logger.error(f"OpenRouter API error: {e.response.status_code} - {e.response.text}")
            return self._default_metadata()
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            return self._default_metadata()
        except Exception as e:
            logger.error(f"Metadata extraction failed: {e}")
            return self._default_metadata()

    def _extract_json(self, content: str) -> str:
        """Extract JSON from LLM response, handling markdown code blocks."""
        # Try to find JSON in code blocks
        code_block_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
        if code_block_match:
            return code_block_match.group(1)

        # Try to find raw JSON
        json_match = re.search(r'\{[^{}]*\}', content, re.DOTALL)
        if json_match:
            return json_match.group(0)

        # Return the content as-is and let JSON parser handle errors
        return content

    def _validate_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize extracted metadata fields."""
        valid_doc_types = [
            'Patient Leaflet', 'Appointment Form', 'Clinical Protocol',
            'Consent Form', 'Educational Material', 'FAQ', 'Other'
        ]
        valid_age_groups = ['Pediatric', 'Adult', 'All Ages']
        valid_audiences = ['Patient/Parent', 'Clinician', 'Both']

        result = {}
        result['procedure_type'] = metadata.get('procedure_type', 'General')
        result['doc_type'] = metadata.get('doc_type', 'Other')
        if result['doc_type'] not in valid_doc_types:
            result['doc_type'] = 'Other'
        result['age_group'] = metadata.get('age_group', 'Pediatric')
        if result['age_group'] not in valid_age_groups:
            result['age_group'] = 'Pediatric'
        result['target_audience'] = metadata.get('target_audience', 'Patient/Parent')
        if result['target_audience'] not in valid_audiences:
            result['target_audience'] = 'Patient/Parent'

        return result

    def _default_metadata(self) -> Dict[str, Any]:
        """Return default metadata when extraction fails."""
        return {
            'procedure_type': 'General',
            'doc_type': 'Other',
            'age_group': 'Pediatric',
            'target_audience': 'Patient/Parent',
        }

    def close(self):
        """Close the HTTP client."""
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
