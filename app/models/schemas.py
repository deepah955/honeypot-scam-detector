"""
Pydantic schemas for all data models
"""

from datetime import datetime
from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class MessageRequest(BaseModel):
    """Incoming message request schema"""
    conversation_id: str = Field(..., min_length=1, description="Unique conversation identifier")
    message: str = Field(..., min_length=1, description="Incoming message content")


class EngagementMetrics(BaseModel):
    """Engagement metrics for the conversation"""
    turns: int = Field(default=0, ge=0, description="Number of conversation turns")
    duration_seconds: int = Field(default=0, ge=0, description="Total conversation duration in seconds")


class Intelligence(BaseModel):
    """Extracted scam intelligence"""
    upi_ids: List[str] = Field(default_factory=list, description="Extracted UPI IDs")
    bank_accounts: List[str] = Field(default_factory=list, description="Extracted bank account numbers")
    urls: List[str] = Field(default_factory=list, description="Extracted URLs")
    phones: List[str] = Field(default_factory=list, description="Extracted phone numbers")
    ifsc_codes: List[str] = Field(default_factory=list, description="Extracted IFSC codes")


class MessageResponse(BaseModel):
    """Response schema for honeypot endpoint"""
    scam_detected: bool = Field(..., description="Whether scam intent was detected")
    engagement_metrics: EngagementMetrics = Field(..., description="Engagement statistics")
    intelligence: Intelligence = Field(..., description="Extracted intelligence data")
    reply: str = Field(..., description="Agent's reply message")


class ScamDetectionResult(BaseModel):
    """Result from scam detection service"""
    is_scam: bool = Field(..., description="Whether the message is classified as scam")
    confidence: float = Field(..., ge=0, le=1, description="Detection confidence score")


class AgentState(BaseModel):
    """Agent state stored in memory"""
    trust_level: float = Field(default=0.5, ge=0, le=1, description="Current trust level with scammer")
    curiosity_level: float = Field(default=0.7, ge=0, le=1, description="Current curiosity level")
    strategy: str = Field(default="neutral", description="Current engagement strategy")
    scam_confirmed: bool = Field(default=False, description="Whether scam has been confirmed")


class ConversationTurn(BaseModel):
    """Single conversation turn"""
    role: Literal["user", "assistant"] = Field(..., description="Message sender role")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Turn timestamp")


class ConversationHistory(BaseModel):
    """Full conversation history"""
    conversation_id: str = Field(..., description="Unique conversation identifier")
    turns: List[ConversationTurn] = Field(default_factory=list, description="List of conversation turns")
    agent_state: AgentState = Field(default_factory=AgentState, description="Current agent state")
    started_at: datetime = Field(default_factory=datetime.utcnow, description="Conversation start time")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last update time")


class StrategyChoice(BaseModel):
    """Strategy selection result"""
    strategy: Literal[
        "ask_payment_details",
        "ask_link_again",
        "delay_response",
        "request_confirmation",
        "express_concern",
        "neutral"
    ] = Field(..., description="Selected engagement strategy")
    reasoning: str = Field(default="", description="Reasoning for strategy choice")
