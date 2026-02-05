"""
Memory store implementation with Redis primary and in-memory fallback
"""

import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod

import redis.asyncio as redis
from redis.exceptions import ConnectionError, TimeoutError

from app.config import get_settings
from app.models import ConversationHistory, ConversationTurn, AgentState

logger = logging.getLogger(__name__)


class BaseMemoryStore(ABC):
    """Abstract base class for memory stores"""
    
    @abstractmethod
    async def get_conversation(self, conversation_id: str) -> Optional[ConversationHistory]:
        """Retrieve conversation history"""
        pass
    
    @abstractmethod
    async def save_conversation(self, conversation: ConversationHistory) -> bool:
        """Save conversation history"""
        pass
    
    @abstractmethod
    async def append_turn(self, conversation_id: str, turn: ConversationTurn) -> bool:
        """Append a turn to conversation"""
        pass
    
    @abstractmethod
    async def update_agent_state(self, conversation_id: str, state: AgentState) -> bool:
        """Update agent state for conversation"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if store is healthy"""
        pass


class InMemoryStore(BaseMemoryStore):
    """In-memory fallback store"""
    
    def __init__(self):
        self._store: Dict[str, Dict[str, Any]] = {}
        logger.info("Initialized in-memory store")
    
    async def get_conversation(self, conversation_id: str) -> Optional[ConversationHistory]:
        """Retrieve conversation from memory"""
        data = self._store.get(conversation_id)
        if not data:
            return None
        return ConversationHistory(**data)
    
    async def save_conversation(self, conversation: ConversationHistory) -> bool:
        """Save conversation to memory"""
        try:
            self._store[conversation.conversation_id] = conversation.model_dump(mode="json")
            return True
        except Exception as e:
            logger.error(f"Failed to save conversation: {e}")
            return False
    
    async def append_turn(self, conversation_id: str, turn: ConversationTurn) -> bool:
        """Append turn to conversation"""
        try:
            if conversation_id not in self._store:
                # Create new conversation
                conversation = ConversationHistory(
                    conversation_id=conversation_id,
                    turns=[turn]
                )
                return await self.save_conversation(conversation)
            
            self._store[conversation_id]["turns"].append(turn.model_dump(mode="json"))
            self._store[conversation_id]["last_updated"] = datetime.utcnow().isoformat()
            return True
        except Exception as e:
            logger.error(f"Failed to append turn: {e}")
            return False
    
    async def update_agent_state(self, conversation_id: str, state: AgentState) -> bool:
        """Update agent state"""
        try:
            if conversation_id not in self._store:
                return False
            self._store[conversation_id]["agent_state"] = state.model_dump(mode="json")
            self._store[conversation_id]["last_updated"] = datetime.utcnow().isoformat()
            return True
        except Exception as e:
            logger.error(f"Failed to update agent state: {e}")
            return False
    
    async def health_check(self) -> bool:
        """In-memory store is always healthy"""
        return True


class RedisMemoryStore(BaseMemoryStore):
    """Redis-based memory store"""
    
    def __init__(self, redis_client: redis.Redis, ttl: int = 86400):
        self._redis = redis_client
        self._ttl = ttl
        self._fallback = InMemoryStore()
        logger.info("Initialized Redis memory store")
    
    def _key(self, conversation_id: str) -> str:
        """Generate Redis key for conversation"""
        return f"honeypot:conversation:{conversation_id}"
    
    async def get_conversation(self, conversation_id: str) -> Optional[ConversationHistory]:
        """Retrieve conversation from Redis"""
        try:
            data = await self._redis.get(self._key(conversation_id))
            if not data:
                return None
            return ConversationHistory(**json.loads(data))
        except (ConnectionError, TimeoutError) as e:
            logger.warning(f"Redis connection error, using fallback: {e}")
            return await self._fallback.get_conversation(conversation_id)
        except Exception as e:
            logger.error(f"Failed to get conversation: {e}")
            return None
    
    async def save_conversation(self, conversation: ConversationHistory) -> bool:
        """Save conversation to Redis"""
        try:
            data = conversation.model_dump_json()
            await self._redis.setex(
                self._key(conversation.conversation_id),
                self._ttl,
                data
            )
            return True
        except (ConnectionError, TimeoutError) as e:
            logger.warning(f"Redis connection error, using fallback: {e}")
            return await self._fallback.save_conversation(conversation)
        except Exception as e:
            logger.error(f"Failed to save conversation: {e}")
            return False
    
    async def append_turn(self, conversation_id: str, turn: ConversationTurn) -> bool:
        """Append turn to conversation in Redis"""
        try:
            conversation = await self.get_conversation(conversation_id)
            if not conversation:
                conversation = ConversationHistory(
                    conversation_id=conversation_id,
                    turns=[]
                )
            
            conversation.turns.append(turn)
            conversation.last_updated = datetime.utcnow()
            return await self.save_conversation(conversation)
        except Exception as e:
            logger.error(f"Failed to append turn: {e}")
            return False
    
    async def update_agent_state(self, conversation_id: str, state: AgentState) -> bool:
        """Update agent state in Redis"""
        try:
            conversation = await self.get_conversation(conversation_id)
            if not conversation:
                return False
            
            conversation.agent_state = state
            conversation.last_updated = datetime.utcnow()
            return await self.save_conversation(conversation)
        except Exception as e:
            logger.error(f"Failed to update agent state: {e}")
            return False
    
    async def health_check(self) -> bool:
        """Check Redis connection"""
        try:
            await self._redis.ping()
            return True
        except Exception:
            return False


class MemoryStore:
    """Main memory store with automatic fallback"""
    
    def __init__(self):
        self._store: Optional[BaseMemoryStore] = None
        self._redis_client: Optional[redis.Redis] = None
    
    async def initialize(self) -> None:
        """Initialize the memory store"""
        settings = get_settings()
        
        if settings.use_redis_fallback:
            try:
                self._redis_client = redis.from_url(
                    settings.redis_url,
                    password=settings.redis_password,
                    encoding="utf-8",
                    decode_responses=True
                )
                # Test connection
                await self._redis_client.ping()
                self._store = RedisMemoryStore(
                    self._redis_client,
                    ttl=settings.memory_ttl_seconds
                )
                logger.info("Connected to Redis successfully")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis, using in-memory fallback: {e}")
                self._store = InMemoryStore()
        else:
            self._store = InMemoryStore()
    
    async def close(self) -> None:
        """Close connections"""
        if self._redis_client:
            await self._redis_client.close()
    
    async def get_conversation(self, conversation_id: str) -> Optional[ConversationHistory]:
        """Get conversation history"""
        if not self._store:
            await self.initialize()
        return await self._store.get_conversation(conversation_id)
    
    async def save_conversation(self, conversation: ConversationHistory) -> bool:
        """Save conversation history"""
        if not self._store:
            await self.initialize()
        return await self._store.save_conversation(conversation)
    
    async def append_turn(self, conversation_id: str, turn: ConversationTurn) -> bool:
        """Append a turn to conversation"""
        if not self._store:
            await self.initialize()
        return await self._store.append_turn(conversation_id, turn)
    
    async def update_agent_state(self, conversation_id: str, state: AgentState) -> bool:
        """Update agent state"""
        if not self._store:
            await self.initialize()
        return await self._store.update_agent_state(conversation_id, state)
    
    async def health_check(self) -> bool:
        """Check store health"""
        if not self._store:
            return False
        return await self._store.health_check()


# Singleton instance
_memory_store: Optional[MemoryStore] = None


async def get_memory_store() -> MemoryStore:
    """Get or create memory store singleton"""
    global _memory_store
    if _memory_store is None:
        _memory_store = MemoryStore()
        await _memory_store.initialize()
    return _memory_store
