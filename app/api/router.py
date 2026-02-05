"""
API Router - Main honeypot endpoint
"""

import logging
import json
from datetime import datetime
from typing import Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Request

from app.models import (
    MessageRequest,
    MessageResponse,
    ConversationTurn,
    ConversationHistory,
    AgentState,
)
from app.memory import get_memory_store
from app.services.detection import get_detection_service
from app.services.extractor import get_extractor_service
from app.services.metrics import get_metrics_service
from app.agents import get_honeypot_agent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/honeypot", tags=["honeypot"])


@router.get("/message")
async def get_message_info():
    """GET endpoint for testing - returns basic service info"""
    return {
        "status": "operational",
        "endpoint": "/honeypot/message",
        "method": "POST",
        "required_headers": {"x-api-key": "your-api-key"},
        "example_body": {
            "conversation_id": "test-123",
            "message": "Your message here"
        }
    }


@router.post("/message", response_model=MessageResponse)
async def process_message(request: Request) -> MessageResponse:
    """
    Process an incoming scam conversation message.
    
    1. Load conversation history
    2. Run scam detection
    3. Engage with honeypot agent if scam
    4. Extract intelligence
    5. Return structured response
    """
    # Parse request body - handle empty or malformed bodies gracefully
    conversation_id = "default-test-conversation"
    message = "Hello, this is a test message."
    
    try:
        body = await request.body()
        if body:
            body_json = json.loads(body)
            conversation_id = body_json.get("conversation_id", conversation_id)
            message = body_json.get("message", message)
    except (json.JSONDecodeError, Exception) as e:
        logger.warning(f"Could not parse request body, using defaults: {e}")
    
    logger.info(f"Processing message for conversation: {conversation_id}")
    
    try:
        # Get services
        memory = await get_memory_store()
        detection = get_detection_service()
        extractor = get_extractor_service()
        metrics_service = get_metrics_service()
        agent = get_honeypot_agent()
        
        # Load conversation history
        conversation = await memory.get_conversation(conversation_id)
        if not conversation:
            conversation = ConversationHistory(
                conversation_id=conversation_id,
                turns=[],
                agent_state=AgentState(),
                started_at=datetime.utcnow()
            )
        
        # Prepare history for services
        history_dicts = [
            {"role": t.role, "content": t.content}
            for t in conversation.turns
        ]
        
        # Run scam detection
        detection_result = await detection.detect(message, history_dicts)
        scam_detected = detection_result.is_scam
        
        logger.info(f"Scam detected: {scam_detected} (confidence: {detection_result.confidence})")
        
        # Add incoming message to history
        user_turn = ConversationTurn(
            role="user",
            content=message,
            timestamp=datetime.utcnow()
        )
        await memory.append_turn(conversation_id, user_turn)
        
        # Update history for agent
        history_dicts.append({"role": "user", "content": message})
        
        # Generate reply
        if scam_detected:
            # Select strategy
            strategy = await agent.select_strategy(conversation, conversation.agent_state)
            
            # Update agent state
            new_state = agent.update_agent_state(
                conversation.agent_state,
                strategy,
                scam_detected
            )
            await memory.update_agent_state(conversation_id, new_state)
            
            # Generate honeypot reply
            reply = await agent.generate_reply(
                message=message,
                conversation_history=history_dicts[:-1],  # Exclude current
                strategy=strategy.strategy,
                agent_state=new_state
            )
        else:
            reply = agent.generate_neutral_reply(message)
        
        # Add reply to history
        assistant_turn = ConversationTurn(
            role="assistant",
            content=reply,
            timestamp=datetime.utcnow()
        )
        await memory.append_turn(conversation_id, assistant_turn)
        
        # Get updated conversation for metrics
        conversation = await memory.get_conversation(conversation_id)
        
        # Extract intelligence
        full_history = [
            {"role": t.role, "content": t.content}
            for t in conversation.turns
        ]
        intelligence = await extractor.extract(full_history)
        
        # Calculate metrics
        engagement_metrics = metrics_service.calculate_metrics(conversation)
        
        response = MessageResponse(
            scam_detected=scam_detected,
            engagement_metrics=engagement_metrics,
            intelligence=intelligence,
            reply=reply
        )
        
        logger.info(
            f"Response: scam={scam_detected}, "
            f"turns={engagement_metrics.turns}, "
            f"entities={metrics_service.calculate_entity_count(intelligence)}"
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
