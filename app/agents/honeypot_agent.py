"""
HoneyPot Agent - Autonomous scammer engagement agent
"""

import logging
from typing import List, Dict, Any, Optional

from app.models import AgentState, StrategyChoice, ConversationHistory
from app.prompts import AGENT_PERSONA_PROMPT, STRATEGY_PROMPT
from app.services.llm import get_llm_service

logger = logging.getLogger(__name__)


class HoneyPotAgent:
    """
    Autonomous agent for engaging with scammers.
    Maintains persona, selects strategies, and generates believable responses.
    """
    
    def __init__(self):
        self._llm = get_llm_service()
    
    async def select_strategy(
        self,
        conversation: Optional[ConversationHistory],
        agent_state: AgentState
    ) -> StrategyChoice:
        """
        Select the next engagement strategy based on conversation context.
        """
        turn_count = len(conversation.turns) if conversation else 0
        
        prompt = STRATEGY_PROMPT.format(
            trust_level=agent_state.trust_level,
            curiosity_level=agent_state.curiosity_level,
            previous_strategy=agent_state.strategy,
            turn_count=turn_count
        )
        
        try:
            # Get recent messages for context
            recent_messages = ""
            if conversation and conversation.turns:
                for turn in conversation.turns[-4:]:
                    recent_messages += f"{turn.role}: {turn.content}\n"
            
            result = await self._llm.complete_json(
                system_prompt=prompt,
                user_message=f"Recent conversation:\n{recent_messages}\n\nSelect best strategy.",
                temperature=0.4
            )
            
            strategy = result.get("strategy", "neutral")
            reasoning = result.get("reasoning", "")
            
            logger.debug(f"Selected strategy: {strategy} - {reasoning}")
            
            return StrategyChoice(strategy=strategy, reasoning=reasoning)
            
        except Exception as e:
            logger.warning(f"Strategy selection failed: {e}")
            return StrategyChoice(strategy="neutral", reasoning="Fallback to neutral")
    
    def update_agent_state(
        self,
        current_state: AgentState,
        strategy: StrategyChoice,
        scam_detected: bool
    ) -> AgentState:
        """
        Update agent state based on interaction.
        """
        new_trust = current_state.trust_level
        new_curiosity = current_state.curiosity_level
        
        if scam_detected and not current_state.scam_confirmed:
            new_curiosity = min(1.0, new_curiosity + 0.1)
        
        # Adjust trust based on strategy
        if strategy.strategy == "delay_response":
            new_trust = max(0.0, new_trust - 0.05)
        elif strategy.strategy == "request_confirmation":
            new_trust = max(0.0, new_trust - 0.03)
        elif strategy.strategy in ["ask_payment_details", "ask_link_again"]:
            new_trust = min(1.0, new_trust + 0.02)
        
        return AgentState(
            trust_level=round(new_trust, 2),
            curiosity_level=round(new_curiosity, 2),
            strategy=strategy.strategy,
            scam_confirmed=current_state.scam_confirmed or scam_detected
        )
    
    async def generate_reply(
        self,
        message: str,
        conversation_history: List[Dict[str, Any]],
        strategy: str,
        agent_state: AgentState
    ) -> str:
        """
        Generate a believable reply to the scammer.
        """
        # Format persona prompt with current strategy
        system_prompt = AGENT_PERSONA_PROMPT.format(strategy=strategy)
        
        # Add state context
        state_context = f"""
Current internal state (do not reveal):
- Trust: {agent_state.trust_level:.1f}/1.0
- Curiosity: {agent_state.curiosity_level:.1f}/1.0
- Strategy to use: {strategy}
"""
        system_prompt = system_prompt + "\n" + state_context
        
        try:
            reply = await self._llm.complete(
                system_prompt=system_prompt,
                user_message=message,
                conversation_history=conversation_history,
                temperature=0.8,
                max_tokens=300
            )
            
            # Clean up the reply
            reply = reply.strip().strip('"').strip("'")
            
            logger.info(f"Generated reply using strategy '{strategy}': {reply[:50]}...")
            return reply
            
        except Exception as e:
            logger.error(f"Failed to generate reply: {e}")
            return self._get_fallback_reply(strategy)
    
    def _get_fallback_reply(self, strategy: str) -> str:
        """Get a fallback reply if LLM fails."""
        fallbacks = {
            "ask_payment_details": "I'm a bit confused about the payment. Can you explain again?",
            "ask_link_again": "Sorry, I couldn't open that link. Could you send it again?",
            "delay_response": "Let me check with my family first. Can we continue later?",
            "request_confirmation": "Just to be sure, can you confirm those details again?",
            "express_concern": "I'm a little worried. Is this really legitimate?",
            "neutral": "I see. Can you tell me more about this?"
        }
        return fallbacks.get(strategy, "I'm not sure I understand. Could you explain?")
    
    def generate_neutral_reply(self, message: str) -> str:
        """Generate a simple neutral reply for non-scam messages."""
        return "Thank you for your message. How can I help you today?"


# Singleton
_agent: Optional[HoneyPotAgent] = None

def get_honeypot_agent() -> HoneyPotAgent:
    global _agent
    if _agent is None:
        _agent = HoneyPotAgent()
    return _agent
