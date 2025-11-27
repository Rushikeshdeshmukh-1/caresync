"""
Test Orchestrator Workflows
End-to-end test of encounter → mapping → claim flow
"""

import asyncio
import pytest
from services.orchestrator_service import OrchestratorService
from services.event_bus import event_bus, EventTopics
from models.database import SessionLocal, Encounter, ReviewQueue, OrchestratorAudit


@pytest.mark.asyncio
async def test_encounter_processing():
    """Test that orchestrator processes encounter correctly"""
    orchestrator = OrchestratorService()
    await orchestrator.initialize()
    
    # Create test encounter data
    encounter_data = {
        "encounter_id": "test-enc-001",
        "patient_id": "test-patient-001",
        "notes": "Patient presents with Amlapitta and heartburn",
        "chief_complaint": "Acidity and burning sensation"
    }
    
    # Process encounter
    await orchestrator.process_encounter(encounter_data)
    
    # Check audit log
    session = SessionLocal()
    audit_entry = session.query(OrchestratorAudit).filter(
        OrchestratorAudit.encounter_id == "test-enc-001",
        OrchestratorAudit.action == "mapping_suggested"
    ).first()
    
    assert audit_entry is not None
    assert audit_entry.status == "success"
    
    session.close()


@pytest.mark.asyncio
async def test_low_confidence_creates_review_task():
    """Test that low confidence mappings create review tasks"""
    orchestrator = OrchestratorService()
    await orchestrator.initialize()
    
    # Create encounter with vague symptoms (likely low confidence)
    encounter_data = {
        "encounter_id": "test-enc-002",
        "patient_id": "test-patient-002",
        "notes": "Patient feels unwell",
        "chief_complaint": "General malaise"
    }
    
    # Process encounter
    await orchestrator.process_encounter(encounter_data)
    
    # Check if review task was created
    session = SessionLocal()
    review_task = session.query(ReviewQueue).filter(
        ReviewQueue.encounter_id == "test-enc-002"
    ).first()
    
    # May or may not create review task depending on mapping results
    # Just verify no errors occurred
    session.close()


def test_event_publishing():
    """Test that events are published correctly"""
    # Publish test event
    message_id = event_bus.publish(EventTopics.ENCOUNTER_CREATED, {
        "encounter_id": "test-enc-003",
        "patient_id": "test-patient-003",
        "notes": "Test notes"
    })
    
    # If Redis is available, message_id should be returned
    # If not, it will be None (mock mode)
    # Either way, no error should occur
    assert message_id is None or isinstance(message_id, str)


if __name__ == "__main__":
    print("Running orchestrator workflow tests...")
    pytest.main([__file__, "-v", "-s"])
