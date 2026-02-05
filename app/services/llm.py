"""
LLM Service - Heuristic-based response generator (No OpenAI required)
"""

import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


class LLMService:
    """Service for generating responses using heuristic rules (no external LLM)"""
    
    def __init__(self):
        logger.info("LLM Service initialized in heuristic-only mode (no OpenAI)")
    
    @property
    def is_available(self) -> bool:
        """Check if LLM is available - always False since we don't use OpenAI"""
        return False
    
    async def complete(
        self,
        system_prompt: str,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """
        Generate a completion using heuristic rules (no OpenAI)
        
        Returns:
            Generated response text
        """
        # Return a heuristic-based response
        logger.info("Generating heuristic-based response")
        raise ValueError("LLM not configured - using heuristic fallback")
    
    async def complete_json(
        self,
        system_prompt: str,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.3
    ) -> Dict[str, Any]:
        """
        Generate a JSON response using heuristic rules (no OpenAI)
        
        Returns:
            Parsed JSON response
        """
        logger.info("Generating heuristic-based JSON response")
        raise ValueError("LLM not configured - using heuristic fallback")


# Singleton instance
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """Get or create LLM service singleton"""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
