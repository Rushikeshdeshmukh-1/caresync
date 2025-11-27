"""
Event Bus using Redis Streams
Handles async event publishing and subscription
"""

import redis
import json
import logging
from typing import Dict, Any, Callable, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class EventBus:
    """Redis Streams-based event bus for orchestration"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        """
        Initialize event bus
        
        Args:
            redis_url: Redis connection URL
        """
        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            self.redis_client.ping()
            logger.info(f"Connected to Redis at {redis_url}")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}. Using mock mode.")
            self.redis_client = None
    
    def publish(self, topic: str, payload: Dict[str, Any]) -> Optional[str]:
        """
        Publish an event to a topic (using pub/sub for Redis 3.x compatibility)
        
        Args:
            topic: Event topic (e.g., 'encounter.created')
            payload: Event payload
            
        Returns:
            Message ID if successful, None otherwise
        """
        if not self.redis_client:
            logger.warning(f"Redis not available. Event not published: {topic}")
            return None
        
        try:
            # Add timestamp
            payload['_timestamp'] = datetime.utcnow().isoformat()
            
            # Publish using pub/sub
            num_subscribers = self.redis_client.publish(topic, json.dumps(payload))
            
            logger.info(f"Published event to {topic} ({num_subscribers} subscribers)")
            return f"{topic}:{datetime.utcnow().timestamp()}"
            
        except Exception as e:
            logger.error(f"Failed to publish event to {topic}: {e}")
            return None
    
    def subscribe(
        self,
        topic: str,
        handler: Callable[[Dict[str, Any]], None],
        consumer_group: str = "default",
        consumer_name: str = "worker-1"
    ):
        """
        Subscribe to a topic and process events (using pub/sub for Redis 3.x compatibility)
        
        Args:
            topic: Event topic to subscribe to
            handler: Callback function to handle events
            consumer_group: Consumer group name (ignored in pub/sub)
            consumer_name: Consumer name within group (ignored in pub/sub)
        """
        if not self.redis_client:
            logger.warning(f"Redis not available. Cannot subscribe to {topic}")
            return
        
        try:
            logger.info(f"Subscribing to {topic} using pub/sub")
            
            # Create pubsub instance
            pubsub = self.redis_client.pubsub()
            pubsub.subscribe(topic)
            
            # Listen for messages
            for message in pubsub.listen():
                try:
                    if message['type'] == 'message':
                        # Parse payload
                        payload = json.loads(message['data'])
                        
                        # Call handler
                        handler(payload)
                        logger.debug(f"Processed message from {topic}")
                
                except KeyboardInterrupt:
                    logger.info(f"Stopping subscription to {topic}")
                    break
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    # Continue listening
        
        except Exception as e:
            logger.error(f"Failed to subscribe to {topic}: {e}")
    
    def get_pending(self, topic: str, consumer_group: str = "default") -> list:
        """
        Get pending messages for a consumer group
        
        Args:
            topic: Event topic
            consumer_group: Consumer group name
            
        Returns:
            List of pending message IDs
        """
        if not self.redis_client:
            return []
        
        try:
            pending = self.redis_client.xpending(topic, consumer_group)
            return pending
        except Exception as e:
            logger.error(f"Failed to get pending messages: {e}")
            return []


# Global event bus instance
event_bus = EventBus()


# Event topic constants
class EventTopics:
    """Event topic constants"""
    ENCOUNTER_CREATED = "encounter.created"
    MAPPING_SUGGESTED = "mapping.suggested"
    ENCOUNTER_DUAL_CODED = "encounter.dual_coded"
    CLAIM_PREVIEWED = "claim.previewed"
    MODEL_DRIFT = "model.drift"
    ORCHESTRATOR_PAUSED = "orchestrator.paused"
