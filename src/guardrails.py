"""LangChain guardrails for PedIR Bot agent."""
from typing import Any, Optional
from langchain_core.messages import HumanMessage, AIMessage
from loguru import logger

# Emergency keywords that trigger canned responses
# Note: For PedIR context, we need specific qualifiers to avoid false positives
# when discussing procedures like embolization that involve bleeding management
EMERGENCY_KEYWORDS = [
    # Breathing emergencies (always urgent)
    "can't breathe", "cannot breathe", "not breathing", "stopped breathing",
    # Cardiac (always urgent)
    'chest pain', 'heart attack',
    # Severe allergic reaction
    'anaphylaxis', 'severe allergic reaction', 'throat swelling',
    # True emergencies
    'emergency room', 'call 999', 'call ambulance', '999', 'unconscious', 'passed out',
    # Chinese emergency terms
    '不能呼吸', '胸痛', '過敏反應', '緊急', '昏迷', '急症室',
    # Post-procedure true emergencies (require "heavy/uncontrolled" qualifier)
    'uncontrolled bleeding', 'heavy bleeding', "bleeding won't stop", "bleeding will not stop",
    '大量出血', '無法止血'
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
        # Updated prompt to be context-aware for pediatric IR educational content
        self.safety_prompt_template = """You are a safety checker for a pediatric interventional radiology (IR) educational chatbot.
This chatbot provides educational information about IR procedures like embolization, catheter insertion, biopsies, etc.

CONTEXT: This is a PATIENT EDUCATION chatbot, NOT a diagnostic tool.
It is NORMAL and SAFE for responses to:
- Discuss procedure descriptions (including bleeding, pain, risks like embolization).
- Mention expected side effects and complications.
- Give post-procedure care instructions.
- Advise when to seek medical attention.
- Ask for clarification if the user's question is unclear.
- State that it cannot answer or provide a disclaimer.

ONLY mark as UNSAFE if the response:
1. Provides a specific diagnosis for the user ("You have condition X").
2. Prescribes specific dosage of medication ("Take 500mg of drug Y").
3. Explicitly advises AGAINST seeking medical care when symptoms are urgent.
4. Contains clearly toxic, hateful, or harmful content unrelated to medical education.

Mark as SAFE if the response:
- Is educational in nature.
- Is a refusal to answer due to lack of information.
- Is a disclaimer.
- Discusses medical topics generally without diagnosing the specific user.

Respond with ONLY: 'SAFE' or 'UNSAFE'
If you are unsure, default to 'SAFE' but you can add a short reason after the keyword.

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

