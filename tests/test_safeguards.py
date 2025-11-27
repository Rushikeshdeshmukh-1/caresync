"""
Test Safeguards System
Verify that mapping resources are protected from writes
"""

import pytest
from services.safeguards import safe_write, is_mapping_resource, orchestrator_state
from models.database import SessionLocal, OrchestratorAudit


def test_is_mapping_resource():
    """Test mapping resource detection"""
    # Should be protected
    assert is_mapping_resource("namaste.csv") == True
    assert is_mapping_resource("data/namaste.csv") == True
    assert is_mapping_resource("namaste_mappings_table") == True
    assert is_mapping_resource("data/faiss_index.bin") == True
    
    # Should NOT be protected
    assert is_mapping_resource("encounters") == False
    assert is_mapping_resource("data/patients.csv") == False
    assert is_mapping_resource("review_queue") == False


def test_safe_write_blocks_mapping_resources():
    """Test that safe_write blocks writes to mapping resources"""
    # Should raise PermissionError
    with pytest.raises(PermissionError) as exc_info:
        safe_write("namaste.csv", {"test": "data"})
    
    assert "READ-ONLY" in str(exc_info.value)
    
    # Check audit log was created
    session = SessionLocal()
    recent_audit = session.query(OrchestratorAudit).order_by(
        OrchestratorAudit.timestamp.desc()
    ).first()
    
    assert recent_audit is not None
    assert recent_audit.action == "mapping_write_blocked"
    assert recent_audit.status == "blocked"
    assert recent_audit.attempted_write == True
    
    session.close()


def test_safe_write_allows_non_mapping_resources():
    """Test that safe_write allows writes to non-mapping resources"""
    # Should NOT raise error
    try:
        result = safe_write("encounters", {"test": "data"})
        assert result == True
    except PermissionError:
        pytest.fail("safe_write should allow writes to non-mapping resources")


def test_orchestrator_pause_on_multiple_blocked_writes():
    """Test that orchestrator pauses after multiple blocked writes"""
    # Reset state
    orchestrator_state.reset_blocked_writes()
    orchestrator_state.resume()
    
    # Simulate 3 blocked writes
    for i in range(3):
        try:
            safe_write("namaste.csv", {"attempt": i})
        except PermissionError:
            orchestrator_state.increment_blocked_writes()
    
    # Orchestrator should be paused
    assert not orchestrator_state.is_active()
    assert orchestrator_state._mode == "paused"


def test_audit_log_creation():
    """Test that audit logs are created correctly"""
    from services.safeguards import audit_log
    
    audit_id = audit_log(
        action="test_action",
        actor="test_actor",
        status="success",
        resource_target="test_resource",
        payload_summary={"test": "data"}
    )
    
    assert audit_id > 0
    
    # Verify in database
    session = SessionLocal()
    audit_entry = session.query(OrchestratorAudit).filter(
        OrchestratorAudit.id == audit_id
    ).first()
    
    assert audit_entry is not None
    assert audit_entry.action == "test_action"
    assert audit_entry.actor == "test_actor"
    assert audit_entry.status == "success"
    
    session.close()


if __name__ == "__main__":
    print("Running safeguard tests...")
    pytest.main([__file__, "-v"])
