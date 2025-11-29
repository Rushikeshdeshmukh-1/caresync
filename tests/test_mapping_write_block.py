"""
Tests for Mapping Write Protection
Verifies that mapping resources are protected from unauthorized writes
"""

import pytest
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.safeguards import safe_write, is_mapping_resource, orchestrator_state, MAPPING_DATA_RESOURCES
from backend.clients.mapping_client import MappingClient, get_mapping_client


class TestMappingResourceDetection:
    """Test mapping resource detection"""
    
    def test_is_mapping_resource_csv_files(self):
        """Test that CSV files are detected as mapping resources"""
        assert is_mapping_resource("data/namaste.csv")
        assert is_mapping_resource("namaste.csv")
        assert is_mapping_resource("data/icd11_codes.csv")
        assert is_mapping_resource("icd11_codes.csv")
    
    def test_is_mapping_resource_tables(self):
        """Test that database tables are detected as mapping resources"""
        assert is_mapping_resource("ayush_terms")
        assert is_mapping_resource("mapping_candidates")
        assert is_mapping_resource("icd_codes")
    
    def test_is_mapping_resource_faiss_index(self):
        """Test that FAISS indices are detected as mapping resources"""
        assert is_mapping_resource("data/faiss_index.bin")
        assert is_mapping_resource("data/icd_index.faiss")
        assert is_mapping_resource("mapping_index_faiss")
    
    def test_is_mapping_resource_model_weights(self):
        """Test that model weights are detected as mapping resources"""
        assert is_mapping_resource("data/reranker.joblib")
        assert is_mapping_resource("mapping_model_weights")
    
    def test_is_not_mapping_resource(self):
        """Test that non-mapping resources are not detected"""
        assert not is_mapping_resource("encounters")
        assert not is_mapping_resource("patients")
        assert not is_mapping_resource("mapping_feedback")
        assert not is_mapping_resource("ai_suggestions")
        assert not is_mapping_resource("encounter_diagnoses")
    
    def test_mapping_resources_loaded_from_config(self):
        """Test that mapping resources are loaded from config file"""
        # Should have loaded resources from config/mapping_resources.yml
        assert len(MAPPING_DATA_RESOURCES) > 0
        assert "data/namaste.csv" in MAPPING_DATA_RESOURCES
        assert "ayush_terms" in MAPPING_DATA_RESOURCES


class TestSafeWrite:
    """Test safe_write function"""
    
    def test_safe_write_blocks_csv_files(self):
        """Test that safe_write blocks writes to CSV files"""
        with pytest.raises(PermissionError, match="Blocked attempt to write to mapping resource"):
            safe_write("data/namaste.csv", {"test": "data"}, actor="test_actor")
    
    def test_safe_write_blocks_tables(self):
        """Test that safe_write blocks writes to mapping tables"""
        with pytest.raises(PermissionError, match="Blocked attempt to write to mapping resource"):
            safe_write("ayush_terms", {"term": "test"}, actor="test_actor")
    
    def test_safe_write_blocks_faiss_index(self):
        """Test that safe_write blocks writes to FAISS index"""
        with pytest.raises(PermissionError, match="Blocked attempt to write to mapping resource"):
            safe_write("data/faiss_index.bin", b"binary data", actor="test_actor")
    
    def test_safe_write_blocks_reranker(self):
        """Test that safe_write blocks writes to reranker model"""
        with pytest.raises(PermissionError, match="Blocked attempt to write to mapping resource"):
            safe_write("data/reranker.joblib", {"model": "data"}, actor="test_actor")
    
    def test_safe_write_allows_non_mapping_resources(self):
        """Test that safe_write allows writes to non-mapping resources"""
        # Should not raise PermissionError
        result = safe_write("encounters", {"id": "123"}, actor="test_actor")
        assert result is True
        
        result = safe_write("mapping_feedback", {"feedback": "test"}, actor="test_actor")
        assert result is True
    
    def test_safe_write_increments_blocked_counter(self):
        """Test that safe_write increments blocked write counter"""
        # Reset counter
        orchestrator_state.reset_blocked_writes()
        initial_count = orchestrator_state._blocked_write_count
        
        # Attempt blocked write
        try:
            safe_write("data/namaste.csv", {"test": "data"}, actor="test_actor")
        except PermissionError:
            pass
        
        # Counter should have incremented
        assert orchestrator_state._blocked_write_count == initial_count + 1
    
    def test_orchestrator_pauses_after_threshold(self):
        """Test that orchestrator pauses after 3 blocked writes"""
        # Reset and set to active
        orchestrator_state.reset_blocked_writes()
        orchestrator_state.resume()
        assert orchestrator_state.is_active()
        
        # Attempt 3 blocked writes
        for i in range(3):
            try:
                safe_write(f"data/namaste.csv", {"attempt": i}, actor="test_actor")
            except PermissionError:
                pass
        
        # Orchestrator should be paused
        assert not orchestrator_state.is_active()
        assert orchestrator_state._mode == "paused"


class TestMappingClient:
    """Test MappingClient read-only functionality"""
    
    @pytest.fixture
    def client(self):
        """Create MappingClient instance"""
        return MappingClient(data_dir="data")
    
    def test_mapping_client_loads_data(self, client):
        """Test that MappingClient loads data from CSV"""
        assert len(client.namaste_map) > 0
        assert len(client.icd11_map) > 0
    
    def test_mapping_client_lookup(self, client):
        """Test MappingClient lookup method"""
        # Try looking up a common AYUSH term
        result = client.lookup("kasa")
        
        if result:
            assert 'ayush_term' in result
            assert 'icd_code' in result
            assert result['source'] == 'namaste_csv_exact_match'
    
    def test_mapping_client_lookup_case_insensitive(self, client):
        """Test that lookup is case-insensitive"""
        result1 = client.lookup("kasa")
        result2 = client.lookup("KASA")
        result3 = client.lookup("Kasa")
        
        # All should return same result (or all None)
        if result1:
            assert result1.get('ayush_term') == result2.get('ayush_term')
            assert result1.get('ayush_term') == result3.get('ayush_term')
    
    def test_mapping_client_get_icd11_code(self, client):
        """Test getting ICD-11 code details"""
        # Try a common ICD code
        result = client.get_icd11_code("J20.9")
        
        if result:
            assert result['code'] == "J20.9"
            assert 'title' in result
    
    def test_mapping_client_search_namaste(self, client):
        """Test searching NAMASTE terms"""
        results = client.search_namaste("cough", limit=5)
        
        # Should return list (may be empty if no matches)
        assert isinstance(results, list)
        assert len(results) <= 5
    
    def test_mapping_client_get_stats(self, client):
        """Test getting mapping statistics"""
        stats = client.get_stats()
        
        assert 'total_namaste_terms' in stats
        assert 'mapped_to_icd11' in stats
        assert 'unmapped' in stats
        assert 'total_icd11_codes' in stats
        
        # Stats should be consistent
        assert stats['total_namaste_terms'] == stats['mapped_to_icd11'] + stats['unmapped']
    
    def test_mapping_client_has_no_write_methods(self, client):
        """Test that MappingClient has no write methods"""
        # Should not have write/update/delete methods
        assert not hasattr(client, 'write')
        assert not hasattr(client, 'update')
        assert not hasattr(client, 'delete')
        assert not hasattr(client, 'insert')
        assert not hasattr(client, 'create')
    
    def test_get_mapping_client_singleton(self):
        """Test that get_mapping_client returns singleton"""
        client1 = get_mapping_client()
        client2 = get_mapping_client()
        
        # Should be same instance
        assert client1 is client2


class TestMappingImmutability:
    """Integration tests for mapping immutability"""
    
    def test_no_write_paths_to_mapping_data(self):
        """Test that there are no code paths that write to mapping data"""
        # This is a meta-test that verifies the architecture
        
        # MappingClient should only have read methods
        client = get_mapping_client()
        read_only_methods = ['lookup', 'lookup_batch', 'get_icd11_code', 'search_namaste', 'get_all_namaste_terms', 'get_stats']
        
        for method_name in read_only_methods:
            assert hasattr(client, method_name)
        
        # safe_write should block all mapping resources
        for resource in MAPPING_DATA_RESOURCES:
            with pytest.raises(PermissionError):
                safe_write(resource, {"test": "data"}, actor="test")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
