"""
LLM Service for OpenAI-compatible API interactions
"""

import json
import logging
from typing import Optional, List, Dict, Any

from openai import AsyncOpenAI

from app.config import get_settings

logger = logging.getLogger(__name__)


class LLMService:
    """Service for LLM interactions"""
    
    def __init__(self):
        settings = get_settings()
        self._client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url
        )
        self._model = settings.openai_model
    
    async def complete(
        self,
        system_prompt: str,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """
        Generate a completion from the LLM
        
        Args:
            system_prompt: System-level instructions
            user_message: Current user message
            conversation_history: Optional list of previous messages
            temperature: Creativity parameter
            max_tokens: Maximum response tokens
            
        Returns:
            Generated response text
        """
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history if provided
        if conversation_history:
            for turn in conversation_history:
                messages.append({
                    "role": turn.get("role", "user"),
                    "content": turn.get("content", "")
                })
        
        # Add current message
        messages.append({"role": "user", "content": user_message})
        
        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"LLM completion failed: {e}")
            raise
    
    async def complete_json(
        self,
        system_prompt: str,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.3
    ) -> Dict[str, Any]:
        """
        Generate a JSON response from the LLM
        
        Args:
            system_prompt: System-level instructions
            user_message: Current user message
            conversation_history: Optional list of previous messages
            temperature: Creativity parameter (lower for deterministic JSON)
            
        Returns:
            Parsed JSON response
        """
        response = await self.complete(
            system_prompt=system_prompt,
            user_message=user_message,
            conversation_history=conversation_history,
            temperature=temperature,
            max_tokens=500
        )
        
        # Clean response - remove markdown code blocks if present
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        response = response.strip()
        
        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {response}")
            raise ValueError(f"Invalid JSON response from LLM: {e}")


# Singleton instance
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """Get or create LLM service singleton"""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
