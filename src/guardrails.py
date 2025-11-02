"""LangChain guardrails for PedIR Bot agent."""
from typing import Any, Optional
from langchain_core.messages import HumanMessage, AIMessage
from loguru import logger

# Emergency keywords that trigger canned responses
EMERGENCY_KEYWORDS = [
    'severe bleeding', 'can\'t breathe', 'chest pain', 'allergic reaction',
    'emergency', 'urgent', 'ambulance', '999', 'unconscious',
    '不能呼吸', '嚴重出血', '胸痛', '過敏反應', '緊急'
]

EMERGENCY_RESPONSE = """This sounds like it could be an emergency. Please do not rely on this chatbot.

**Call 999 or go to the nearest Accident & Emergency department immediately.**

If you have urgent questions about your procedure, please contact the HKCH IR nurse coordinator at [phone number].
"""

EMERGENCY_RESPONSE_ZH = """這聽起來可能是緊急情況。請不要依賴此聊天機器人。

**請立即致電999或前往最近的急症室。**

如果您對手術有緊急疑問，請致電[電話號碼]聯絡香港兒童醫院介入放射科護士協調員。
"""


class EmergencyGuardrailMiddleware:
    """Deterministic guardrail: Block emergency-related queries before agent processing."""

    def __init__(self):
        self.emergency_keywords = [kw.lower() for kw in EMERGENCY_KEYWORDS]
        self.emergency_response = EMERGENCY_RESPONSE
        self.emergency_response_zh = EMERGENCY_RESPONSE_ZH

    def _extract_text_content(self, content) -> str:
        """
        Extract text from content that can be a string or list of content blocks.

        Args:
            content: Message content (string or list of dicts)

        Returns:
            Extracted text string
        """
        if isinstance(content, str):
            return content
        elif isinstance(content, list):
            # Handle structured content blocks (LangChain 1.0+)
            text_parts = []
            for block in content:
                if isinstance(block, dict):
                    # Extract text from content blocks
                    if block.get('type') == 'text':
                        text_parts.append(block.get('text', ''))
                    elif 'text' in block:
                        text_parts.append(str(block['text']))
                elif isinstance(block, str):
                    text_parts.append(block)
            return ' '.join(text_parts)
        else:
            # Fallback: convert to string
            return str(content)

    def check_emergency(self, query) -> Optional[str]:
        """
        Check if query contains emergency keywords.

        Args:
            query: User query (can be string or structured content)

        Returns:
            Emergency response if triggered, None otherwise
        """
        # Extract text from potentially structured content
        query_text = self._extract_text_content(query)
        query_lower = query_text.lower()

        for keyword in self.emergency_keywords:
            if keyword in query_lower:
                logger.warning(f"🚨 Emergency keyword detected: {keyword}")
                # Detect language and return appropriate response
                if any(ord(char) > 127 for char in query_text):  # Contains non-ASCII (likely Chinese)
                    return self.emergency_response_zh
                else:
                    return self.emergency_response

        return None


class SafetyCheckGuardrail:
    """Model-based guardrail: Validate final responses for safety and compliance."""

    def __init__(self, llm=None):
        """
        Initialize safety check guardrail.

        Args:
            llm: Optional LLM for safety checking (uses orchestrator_llm if not provided)
        """
        self.llm = llm
        self.safety_prompt_template = """You are a safety checker for a medical educational chatbot. Evaluate if this response is safe and appropriate for patients.

CRITICAL CHECKS:
1. Does it provide medical diagnosis or treatment advice? (Should be UNSAFE)
2. Does it interpret a patient's personal medical situation? (Should be UNSAFE)
3. Does it claim to be a substitute for professional medical advice? (Should be UNSAFE)
4. Does it contain inappropriate or harmful content? (Should be UNSAFE)
5. Does it only provide educational information based on context? (Should be SAFE)
6. Does it include the required disclaimer? (Preferred)

Respond with ONLY one word: 'SAFE' or 'UNSAFE'

Response to evaluate:
{response}
"""

    def check_safety(self, response: str, llm=None) -> tuple[bool, Optional[str]]:
        """
        Check if response is safe and compliant.

        Args:
            response: AI response to check
            llm: LLM to use for checking (uses self.llm if not provided)

        Returns:
            Tuple of (is_safe: bool, error_message: Optional[str])
        """
        if not self.llm and not llm:
            # If no LLM available, do basic checks
            logger.debug("No LLM provided for safety check, performing basic validation")
            return self._basic_safety_check(response)

        check_llm = llm or self.llm

        try:
            prompt = self.safety_prompt_template.format(response=response[:2000])  # Limit length
            result = check_llm.invoke([HumanMessage(content=prompt)])

            content = result.content if hasattr(result, 'content') else str(result)
            is_safe = "SAFE" in content.upper() and "UNSAFE" not in content.upper()

            if not is_safe:
                logger.warning(f"⚠️ Safety check failed: Response flagged as unsafe")
                return False, "I cannot provide that response as it may violate safety guidelines. Please rephrase your question or consult with a medical professional."

            logger.debug("✅ Safety check passed")
            return True, None

        except Exception as e:
            logger.error(f"Error in safety check: {e}")
            logger.exception(e)
            # On error, fall back to basic checks
            return self._basic_safety_check(response)

    def _basic_safety_check(self, response: str) -> tuple[bool, Optional[str]]:
        """Perform basic deterministic safety checks."""
        response_lower = response.lower()

        # Check for dangerous phrases
        dangerous_phrases = [
            "i diagnose",
            "you have",
            "you should take",
            "prescribe",
            "treatment plan",
            "medical advice",
            "i recommend treatment"
        ]

        for phrase in dangerous_phrases:
            if phrase in response_lower:
                logger.warning(f"⚠️ Basic safety check failed: Found dangerous phrase '{phrase}'")
                return False, "I cannot provide medical diagnosis or treatment advice. Please consult with your doctor."

        # Check if disclaimer is present
        if "educational purposes only" not in response_lower and "僅供教育目的" not in response:
            logger.warning("⚠️ Disclaimer missing from response")
            # Don't fail, just warn - disclaimer will be added by prompt

        return True, None

