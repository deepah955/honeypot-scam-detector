"""
Engagement Metrics Service
"""

import logging
from datetime import datetime
from typing import Optional

from app.models import ConversationHistory, EngagementMetrics, Intelligence

logger = logging.getLogger(__name__)


class MetricsService:
    """Service for calculating engagement metrics"""
    
    def calculate_metrics(
        self,
        conversation: Optional[ConversationHistory]
    ) -> EngagementMetrics:
        """
        Calculate engagement metrics for a conversation
        
        Args:
            conversation: The conversation history
            
        Returns:
            EngagementMetrics with turns and duration
        """
        if not conversation:
            return EngagementMetrics(turns=0, duration_seconds=0)
        
        # Calculate turn count
        turns = len(conversation.turns)
        
        # Calculate duration in seconds
        duration_seconds = 0
        if conversation.started_at and conversation.last_updated:
            try:
                delta = conversation.last_updated - conversation.started_at
                duration_seconds = int(delta.total_seconds())
            except Exception as e:
                logger.warning(f"Failed to calculate duration: {e}")
                duration_seconds = 0
        
        return EngagementMetrics(
            turns=turns,
            duration_seconds=max(0, duration_seconds)
        )
    
    def calculate_entity_count(self, intelligence: Intelligence) -> int:
        """
        Calculate total extracted entities
        
        Args:
            intelligence: The extracted intelligence
            
        Returns:
            Total count of entities
        """
        return (
            len(intelligence.upi_ids) +
            len(intelligence.bank_accounts) +
            len(intelligence.urls) +
            len(intelligence.phones) +
            len(intelligence.ifsc_codes)
        )
    
    def calculate_engagement_score(
        self,
        metrics: EngagementMetrics,
        intelligence: Intelligence
    ) -> float:
        """
        Calculate an engagement score (0-100)
        
        Higher score indicates more successful engagement
        
        Args:
            metrics: Engagement metrics
            intelligence: Extracted intelligence
            
        Returns:
            Engagement score between 0 and 100
        """
        # Weights for different factors
        TURN_WEIGHT = 2.0  # Points per turn
        DURATION_WEIGHT = 0.01  # Points per second
        ENTITY_WEIGHT = 10.0  # Points per extracted entity
        
        # Calculate component scores
        turn_score = min(metrics.turns * TURN_WEIGHT, 30)
        duration_score = min(metrics.duration_seconds * DURATION_WEIGHT, 20)
        entity_count = self.calculate_entity_count(intelligence)
        entity_score = min(entity_count * ENTITY_WEIGHT, 50)
        
        # Total score capped at 100
        total_score = turn_score + duration_score + entity_score
        
        logger.debug(
            f"Engagement score: {total_score:.1f} "
            f"(turns={turn_score:.1f}, duration={duration_score:.1f}, entities={entity_score:.1f})"
        )
        
        return min(100.0, round(total_score, 1))


# Singleton instance
_metrics_service = None


def get_metrics_service() -> MetricsService:
    """Get or create metrics service singleton"""
    global _metrics_service
    if _metrics_service is None:
        _metrics_service = MetricsService()
    return _metrics_service
