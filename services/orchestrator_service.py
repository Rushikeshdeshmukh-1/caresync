"""
Orchestrator Service
Main agentic workflow coordinator with READ-ONLY mapping enforcement
"""

import asyncio
import logging
import re
from typing import Dict, Any, List, Optional
from datetime import datetime

from services.event_bus import event_bus, EventTopics
from services.safeguards import safe_write, audit_log, orchestrator_state, notify_admin
from services.mapping_engine import MappingEngine
from services.faiss_index import FaissIndex
from services.icd11_service import ICD11Service
from models.database import SessionLocal, Encounter, ReviewQueue

logger = logging.getLogger(__name__)

# System prompt - enforces constraints
SYSTEM_PROMPT = """
SYSTEM INSTRUCTION — CareSync Workflow Orchestrator Agent (Highest Priority)

You are the "CareSync Orchestrator Agent" whose job is to coordinate workflow between clinicians, patients, insurers, and analytics systems.

CRITICAL CONSTRAINTS (MUST NEVER BE BROKEN)
1. **DO NOT modify any NAMASTE → ICD mapping datastore**. This includes any file, table, FAISS index, JSON, CSV, or model weights that are the authoritative mapping source.
2. **READ-ONLY for mappings**: treat the mapping store as immutable.
3. **All outbound actions that change patient, mapping, or claim data must be either:**
   - an audited database write authorized by a clinician action; or
   - an ephemeral preview that remains in status `preview` until explicitly approved.

Fail-safe behavior when constraint is at risk:
  • If you detect any attempt to write to the NAMASTE→ICD mapping store, immediately abort the write, create an audit record with `action_attempt = "blocked"`, notify the admin channel, and escalate to human review.
"""


class OrchestratorService:
    """Main orchestrator service for agentic workflows"""
    
    def __init__(self):
        """Initialize orchestrator"""
        self.mapping_engine = None
        self.icd11_service = None
        logger.info("Orchestrator initialized")
        logger.info(SYSTEM_PROMPT)
    
    async def initialize(self):
        """Initialize async components"""
        # Initialize services
        faiss_index = FaissIndex()
        self.icd11_service = ICD11Service()
        await self.icd11_service.initialize()
        
        self.mapping_engine = MappingEngine(faiss_index, self.icd11_service)
        logger.info("Orchestrator services initialized")
    
    def extract_ayush_terms(self, notes: str) -> List[str]:
        """
        Extract AYUSH terms from clinical notes
        Simple rule-based extraction for now
        
        Args:
            notes: Clinical notes text
            
        Returns:
            List of extracted AYUSH terms
        """
        # Simple extraction: look for capitalized terms and known patterns
        # TODO: Replace with proper NER model
        
        # Common AYUSH term patterns
        patterns = [
            r'\b[A-Z][a-z]+(?:pitta|vata|kapha)\b',  # Dosha-related
            r'\b[A-Z][a-z]+(?:roga|vyAdhi)\b',  # Disease terms
            r'\bAmlapitta\b',
            r'\bJwara\b',
            r'\bKasa\b',
            r'\bShwasa\b'
        ]
        
        terms = []
        for pattern in patterns:
            matches = re.findall(pattern, notes, re.IGNORECASE)
            terms.extend(matches)
        
        # Also extract from notes if it contains specific keywords
        if notes:
            words = notes.split()
            for word in words:
                if len(word) > 3 and word[0].isupper():
                    terms.append(word)
        
        # Remove duplicates and return
        return list(set(terms))[:5]  # Limit to 5 terms
    
    async def process_encounter(self, encounter_data: Dict[str, Any]):
        """
        Process encounter.created event
        Main orchestration logic with safeguards
        
        Args:
            encounter_data: Encounter event payload
        """
        encounter_id = encounter_data.get('encounter_id')
        notes = encounter_data.get('notes', '') or encounter_data.get('chief_complaint', '')
        
        logger.info(f"Processing encounter {encounter_id}")
        
        # Check if orchestrator is active
        if not orchestrator_state.is_active():
            logger.warning(f"Orchestrator is paused. Skipping encounter {encounter_id}")
            audit_log(
                action="encounter_skipped",
                actor="orchestrator_agent",
                status="blocked",
                encounter_id=encounter_id,
                error_message="Orchestrator is paused"
            )
            return
        
        try:
            # Step 1: Extract AYUSH terms
            ayush_terms = self.extract_ayush_terms(notes)
            logger.info(f"Extracted {len(ayush_terms)} AYUSH terms: {ayush_terms}")
            
            if not ayush_terms:
                logger.info(f"No AYUSH terms found in encounter {encounter_id}")
                return
            
            # Step 2: Get mapping suggestions (READ-ONLY)
            all_suggestions = []
            for term in ayush_terms:
                try:
                    result = await self.mapping_engine.suggest(term, k=3)
                    suggestions = result.get('results', [])
                    all_suggestions.extend(suggestions)
                except Exception as e:
                    logger.error(f"Error getting suggestions for term '{term}': {e}")
            
            logger.info(f"Got {len(all_suggestions)} total suggestions")
            
            # Step 3: Create audit log
            audit_log(
                action="mapping_suggested",
                actor="orchestrator_agent",
                status="success",
                encounter_id=encounter_id,
                payload_summary={
                    "ayush_terms": ayush_terms,
                    "num_suggestions": len(all_suggestions)
                },
                model_version=getattr(self.mapping_engine, 'version', 'v1.0'),
                evidence={
                    "suggestions": all_suggestions[:5]  # Store top 5
                }
            )
            
            # Step 4: Check confidence and create review tasks if needed
            low_confidence_suggestions = [
                s for s in all_suggestions if s.get('confidence', 0) < 0.7
            ]
            
            if low_confidence_suggestions:
                self._create_review_task(
                    encounter_id=encounter_id,
                    reason="low_confidence",
                    payload={
                        "ayush_terms": ayush_terms,
                        "low_confidence_suggestions": low_confidence_suggestions
                    }
                )
            
            # Step 5: Publish mapping.suggested event
            event_bus.publish(EventTopics.MAPPING_SUGGESTED, {
                "encounter_id": encounter_id,
                "suggestions": all_suggestions,
                "model_version": getattr(self.mapping_engine, 'version', 'v1.0')
            })
            
            # Step 6: Auto-accept high confidence (>0.95) if policy allows
            # For now, we'll skip auto-accept and always require human review
            logger.info(f"Encounter {encounter_id} processed successfully")
            
        except Exception as e:
            logger.error(f"Error processing encounter {encounter_id}: {e}")
            audit_log(
                action="encounter_processing_failed",
                actor="orchestrator_agent",
                status="failed",
                encounter_id=encounter_id,
                error_message=str(e)
            )
    
    def _create_review_task(
        self,
        encounter_id: str,
        reason: str,
        payload: Dict[str, Any],
        priority: str = "normal"
    ):
        """
        Create a review queue task
        
        Args:
            encounter_id: Encounter ID
            reason: Reason for review
            payload: Full context
            priority: Priority level
        """
        try:
            session = SessionLocal()
            
            review_task = ReviewQueue(
                encounter_id=encounter_id,
                reason=reason,
                priority=priority,
                payload=payload,
                status='open'
            )
            
            session.add(review_task)
            session.commit()
            task_id = review_task.id
            session.close()
            
            logger.info(f"Created review task {task_id} for encounter {encounter_id}")
            
            # Notify clinician (placeholder)
            # TODO: Implement WebSocket/notification system
            
        except Exception as e:
            logger.error(f"Failed to create review task: {e}")
    
    async def run(self):
        """
        Main orchestrator loop
        Subscribes to encounter.created events
        """
        await self.initialize()
        
        logger.info("Orchestrator starting...")
        logger.info("Subscribing to encounter.created events")
        
        # Subscribe to encounter.created
        def handler(payload):
            # Run async handler in event loop
            asyncio.create_task(self.process_encounter(payload))
        
        event_bus.subscribe(
            EventTopics.ENCOUNTER_CREATED,
            handler,
            consumer_group="orchestrator",
            consumer_name="orchestrator-1"
        )


# Global orchestrator instance
orchestrator = OrchestratorService()


if __name__ == "__main__":
    # Run orchestrator
    asyncio.run(orchestrator.run())
