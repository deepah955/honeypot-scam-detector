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


@router.get("/test")
async def test_page():
    """Interactive test page for the API"""
    from fastapi.responses import HTMLResponse
    
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Honeypot API Tester</title>
        <style>
            * { box-sizing: border-box; margin: 0; padding: 0; }
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; }
            .container { max-width: 800px; margin: 0 auto; background: white; border-radius: 15px; padding: 40px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); }
            h1 { color: #2c3e50; margin-bottom: 10px; }
            .subtitle { color: #7f8c8d; margin-bottom: 30px; }
            .form-group { margin-bottom: 20px; }
            label { display: block; margin-bottom: 8px; color: #34495e; font-weight: 600; }
            input, textarea { width: 100%; padding: 12px; border: 2px solid #ecf0f1; border-radius: 8px; font-size: 14px; font-family: inherit; transition: border-color 0.3s; }
            input:focus, textarea:focus { outline: none; border-color: #3498db; }
            textarea { min-height: 120px; resize: vertical; }
            button { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; padding: 15px 30px; border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer; width: 100%; transition: transform 0.2s, box-shadow 0.2s; }
            button:hover { transform: translateY(-2px); box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4); }
            button:active { transform: translateY(0); }
            button:disabled { opacity: 0.6; cursor: not-allowed; }
            .response { margin-top: 30px; padding: 20px; background: #f8f9fa; border-radius: 8px; border-left: 4px solid #3498db; }
            .response h3 { color: #2c3e50; margin-bottom: 15px; }
            .response pre { background: #2c3e50; color: #ecf0f1; padding: 15px; border-radius: 6px; overflow-x: auto; font-size: 13px; line-height: 1.5; }
            .status { display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; margin-bottom: 10px; }
            .status.success { background: #d4edda; color: #155724; }
            .status.error { background: #f8d7da; color: #721c24; }
            .loading { display: none; text-align: center; padding: 20px; }
            .loading.active { display: block; }
            .spinner { border: 3px solid #f3f3f3; border-top: 3px solid #667eea; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; margin: 0 auto; }
            @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
            .example { background: #fff3cd; border: 1px solid #ffc107; border-radius: 6px; padding: 15px; margin-bottom: 20px; }
            .example h4 { color: #856404; margin-bottom: 10px; }
            .example p { color: #856404; font-size: 14px; margin: 5px 0; }
            .example code { background: #fff; padding: 2px 6px; border-radius: 3px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🧪 Honeypot API Tester</h1>
            <p class="subtitle">Test the scam detection endpoint interactively</p>
            
            <div class="example">
                <h4>💡 Try These Example Scam Messages:</h4>
                <p>• "<strong>Your KYC is pending. Please share OTP to verify your account.</strong>"</p>
                <p>• "<strong>Congratulations! You won prize money. Send UPI details now.</strong>"</p>
                <p>• "<strong>Your account will be blocked. Click link and verify immediately.</strong>"</p>
            </div>
            
            <form id="testForm">
                <div class="form-group">
                    <label for="conversationId">Conversation ID</label>
                    <input type="text" id="conversationId" value="test-conv-001" placeholder="e.g., test-conv-001">
                </div>
                
                <div class="form-group">
                    <label for="message">Message to Test</label>
                    <textarea id="message" placeholder="Enter a message to test for scam detection...">Hello, your KYC is pending. Share OTP now!</textarea>
                </div>
                
                <button type="submit" id="submitBtn">🔍 Test Message</button>
            </form>
            
            <div class="loading" id="loading">
                <div class="spinner"></div>
                <p style="margin-top: 10px; color: #667eea;">Processing...</p>
            </div>
            
            <div class="response" id="response" style="display: none;">
                <h3>Response</h3>
                <div id="responseContent"></div>
            </div>
        </div>
        
        <script>
            document.getElementById('testForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                
                const conversationId = document.getElementById('conversationId').value;
                const message = document.getElementById('message').value;
                const submitBtn = document.getElementById('submitBtn');
                const loading = document.getElementById('loading');
                const responseDiv = document.getElementById('response');
                const responseContent = document.getElementById('responseContent');
                
                // Show loading
                submitBtn.disabled = true;
                loading.classList.add('active');
                responseDiv.style.display = 'none';
                
                try {
                    const response = await fetch('/honeypot/message', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'x-api-key': 'test-api-key-123'
                        },
                        body: JSON.stringify({
                            conversation_id: conversationId,
                            message: message
                        })
                    });
                    
                    const data = await response.json();
                    
                    // Show response
                    loading.classList.remove('active');
                    responseDiv.style.display = 'block';
                    
                    const statusClass = response.ok ? 'success' : 'error';
                    const statusText = response.ok ? 'SUCCESS' : 'ERROR';
                    
                    responseContent.innerHTML = `
                        <span class="status ${statusClass}">${statusText}</span>
                        <pre>${JSON.stringify(data, null, 2)}</pre>
                    `;
                    
                    submitBtn.disabled = false;
                } catch (error) {
                    loading.classList.remove('active');
                    responseDiv.style.display = 'block';
                    responseContent.innerHTML = `
                        <span class="status error">ERROR</span>
                        <pre>${error.message}</pre>
                    `;
                    submitBtn.disabled = false;
                }
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


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
            conversation_id = str(body_json.get("conversation_id", conversation_id))
            message = str(body_json.get("message", message))
    except (json.JSONDecodeError, Exception) as e:
        logger.warning(f"Could not parse request body, using defaults: {e}")
    
    # Ensure values are strings
    conversation_id = str(conversation_id) if conversation_id else "default-test-conversation"
    message = str(message) if message else "Hello, this is a test message."
    
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
