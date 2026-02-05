"""
Scam Intent Detection Service
"""

import re
import logging
from typing import List, Dict, Any

from app.models import ScamDetectionResult
from app.prompts import DETECTION_PROMPT
from app.services.llm import get_llm_service

logger = logging.getLogger(__name__)


class ScamDetectionService:
    """Service for detecting scam intent in messages"""
    
    # Heuristic scam indicators
    SCAM_KEYWORDS = [
        r'\b(otp|one.?time.?password)\b',
        r'\b(kyc|know.?your.?customer)\b',
        r'\b(urgent|immediately|expire|suspend)\b',
        r'\b(refund|cashback|bonus|prize|lottery|winner)\b',
        r'\b(verify|verification|validate)\b',
        r'\b(bank.?account|account.?details|card.?number)\b',
        r'\b(upi|gpay|paytm|phonepe|bhim)\b',
        r'\b(click.?here|click.?link|tap.?link)\b',
        r'\b(blocked|deactivated|suspended|locked)\b',
        r'\b(customer.?care|support.?team|helpline)\b',
        r'\b(transfer|send.?money|payment)\b',
        r'\b(pin|cvv|password|credentials)\b',
    ]
    
    # URL pattern
    URL_PATTERN = r'https?://[^\s<>"{}|\\^`\[\]]+'
    SHORT_URL_DOMAINS = ['bit.ly', 'tinyurl', 'goo.gl', 't.co', 'rebrand.ly', 'is.gd', 'v.gd']
    
    def __init__(self):
        self._llm = get_llm_service()
        self._compiled_patterns = [re.compile(p, re.IGNORECASE) for p in self.SCAM_KEYWORDS]
        self._url_pattern = re.compile(self.URL_PATTERN, re.IGNORECASE)
    
    def _heuristic_detection(self, message: str) -> tuple[bool, float]:
        """
        Apply heuristic rules for scam detection
        
        Returns:
            Tuple of (is_scam, confidence)
        """
        # Ensure message is a string
        if not isinstance(message, str):
            message = str(message) if message else ""
        
        message_lower = message.lower()
        
        # Count matching patterns
        match_count = 0
        for pattern in self._compiled_patterns:
            if pattern.search(message):
                match_count += 1
        
        # Check for URLs
        urls = self._url_pattern.findall(message)
        has_suspicious_url = False
        for url in urls:
            for domain in self.SHORT_URL_DOMAINS:
                if domain in url.lower():
                    has_suspicious_url = True
                    break
        
        # Calculate heuristic confidence
        if has_suspicious_url:
            match_count += 2
        
        # Determine if scam based on pattern matches
        if match_count >= 3:
            return True, min(0.5 + (match_count * 0.1), 0.9)
        elif match_count >= 1:
            return True, 0.3 + (match_count * 0.1)
        
        return False, 0.1
    
    async def detect(
        self,
        message: str,
        conversation_history: List[Dict[str, Any]] = None
    ) -> ScamDetectionResult:
        """
        Detect scam intent in a message
        
        Uses LLM-based detection with fallback to heuristics
        
        Args:
            message: The message to analyze
            conversation_history: Optional conversation context
            
        Returns:
            ScamDetectionResult with is_scam and confidence
        """
        # First, apply heuristic detection
        heuristic_scam, heuristic_confidence = self._heuristic_detection(message)
        
        try:
            # Build context for LLM
            context_messages = ""
            if conversation_history:
                for turn in conversation_history[-5:]:  # Last 5 turns for context
                    role = turn.get("role", "user")
                    content = turn.get("content", "")
                    context_messages += f"{role}: {content}\n"
            
            user_prompt = f"""Conversation context:
{context_messages}

Latest message to analyze:
{message}

Classify this message for scam intent."""

            # Get LLM classification
            result = await self._llm.complete_json(
                system_prompt=DETECTION_PROMPT,
                user_message=user_prompt,
                temperature=0.1  # Low temperature for consistent classification
            )
            
            is_scam = result.get("is_scam", False)
            confidence = float(result.get("confidence", 0.5))
            
            # Combine LLM and heuristic results
            if heuristic_scam and is_scam:
                # Both agree - high confidence
                final_confidence = max(confidence, heuristic_confidence)
            elif heuristic_scam or is_scam:
                # One detected scam - moderate confidence
                final_confidence = (confidence + heuristic_confidence) / 2
                is_scam = True
            else:
                # Neither detected scam
                final_confidence = min(confidence, heuristic_confidence)
            
            logger.info(
                f"Scam detection result: is_scam={is_scam}, "
                f"confidence={final_confidence:.2f}, "
                f"llm_conf={confidence:.2f}, "
                f"heuristic_conf={heuristic_confidence:.2f}"
            )
            
            return ScamDetectionResult(
                is_scam=is_scam,
                confidence=round(final_confidence, 2)
            )
            
        except Exception as e:
            logger.warning(f"LLM detection failed, using heuristics only: {e}")
            return ScamDetectionResult(
                is_scam=heuristic_scam,
                confidence=heuristic_confidence
            )


# Singleton instance
_detection_service = None


def get_detection_service() -> ScamDetectionService:
    """Get or create detection service singleton"""
    global _detection_service
    if _detection_service is None:
        _detection_service = ScamDetectionService()
    return _detection_service
