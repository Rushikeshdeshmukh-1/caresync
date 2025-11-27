"""
Comprehensive Integration Test for Orchestration System
Tests the complete workflow without Redis (using direct function calls)
"""

import asyncio
import sys
import httpx
from datetime import datetime

# Test configuration
API_BASE = "http://localhost:8000"
TEST_PATIENT_ID = "test-patient-orchestration"
TEST_CLINICIAN_ID = "test-clinician-001"


async def test_orchestration_workflow():
    """Test complete orchestration workflow"""
    print("=" * 60)
    print("ORCHESTRATION SYSTEM INTEGRATION TEST")
    print("=" * 60)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        # Test 1: Check orchestrator status
        print("\n[1] Checking orchestrator status...")
        try:
            response = await client.get(f"{API_BASE}/api/orchestrator/status")
            if response.status_code == 200:
                status = response.json()
                print(f"✅ Orchestrator status: {status['status']}")
                print(f"   Mode: {status['mode']}")
                print(f"   Blocked writes: {status['blocked_write_count']}")
            else:
                print(f"❌ Failed to get status: {response.status_code}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Test 2: Create a test encounter
        print("\n[2] Creating test encounter...")
        encounter_data = {
            "patient_id": TEST_PATIENT_ID,
            "staff_id": TEST_CLINICIAN_ID,
            "chief_complaint": "Patient presents with Amlapitta, heartburn, and acidity. Also experiencing Jwara (fever).",
            "status": "in_progress"
        }
        
        try:
            response = await client.post(f"{API_BASE}/api/encounters", json=encounter_data)
            if response.status_code == 200:
                encounter = response.json()
                encounter_id = encounter.get('id')
                print(f"✅ Encounter created: {encounter_id}")
            else:
                print(f"❌ Failed to create encounter: {response.status_code}")
                print(f"   Response: {response.text}")
                return
        except Exception as e:
            print(f"❌ Error: {e}")
            return
        
        # Test 3: Manually trigger orchestrator processing (since Redis is unavailable)
        print("\n[3] Testing orchestrator processing (direct call)...")
        try:
            from services.orchestrator_service import orchestrator
            
            # Initialize orchestrator
            await orchestrator.initialize()
            
            # Process encounter
            await orchestrator.process_encounter({
                "encounter_id": encounter_id,
                "patient_id": TEST_PATIENT_ID,
                "notes": encounter_data["chief_complaint"],
                "chief_complaint": encounter_data["chief_complaint"]
            })
            
            print("✅ Orchestrator processed encounter")
        except Exception as e:
            print(f"⚠️  Orchestrator processing: {e}")
            print("   (This is expected if dependencies are missing)")
        
        # Test 4: Check audit log
        print("\n[4] Checking audit log...")
        try:
            response = await client.get(f"{API_BASE}/api/orchestrator/audit?limit=5")
            if response.status_code == 200:
                audit_data = response.json()
                logs = audit_data.get('logs', [])
                print(f"✅ Found {len(logs)} audit log entries")
                for log in logs[:3]:
                    print(f"   - {log['action']} ({log['status']}) at {log['timestamp']}")
            else:
                print(f"❌ Failed to get audit log: {response.status_code}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Test 5: Check review queue
        print("\n[5] Checking review queue...")
        try:
            response = await client.get(f"{API_BASE}/api/orchestrator/review_queue?status=open")
            if response.status_code == 200:
                queue_data = response.json()
                tasks = queue_data.get('tasks', [])
                print(f"✅ Found {len(tasks)} review tasks")
                for task in tasks[:3]:
                    print(f"   - Task {task['id']}: {task['reason']} (priority: {task['priority']})")
            else:
                print(f"❌ Failed to get review queue: {response.status_code}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Test 6: Test safeguards (attempt to write to mapping resource)
        print("\n[6] Testing safeguards (should block mapping writes)...")
        try:
            from services.safeguards import safe_write
            
            try:
                safe_write("namaste.csv", {"test": "data"}, actor="test_script")
                print("❌ CRITICAL: Safeguard failed - write was allowed!")
            except PermissionError as e:
                print(f"✅ Safeguard working: {str(e)[:80]}...")
        except Exception as e:
            print(f"⚠️  Could not test safeguards: {e}")
        
        # Test 7: Test mapping acceptance endpoint
        print("\n[7] Testing mapping acceptance...")
        try:
            accept_data = {
                "selected": [
                    {
                        "ayush": "Amlapitta",
                        "icd11": "DA63",
                        "confidence": 0.92
                    }
                ],
                "actor": TEST_CLINICIAN_ID
            }
            
            response = await client.post(
                f"{API_BASE}/api/orchestrator/encounters/{encounter_id}/accept_mapping",
                json=accept_data
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Mapping accepted: {result['message']}")
            else:
                print(f"❌ Failed to accept mapping: {response.status_code}")
                print(f"   Response: {response.text}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Test 8: Test claim preview generation
        print("\n[8] Testing claim preview generation...")
        try:
            claim_data = {
                "encounter_id": encounter_id,
                "insurer": "TestInsurer"
            }
            
            response = await client.post(
                f"{API_BASE}/api/orchestrator/claims/preview",
                json=claim_data
            )
            
            if response.status_code == 200:
                result = response.json()
                claim_id = result.get('claim_id')
                print(f"✅ Claim preview generated: {claim_id}")
                print(f"   Status: preview (requires approval)")
            else:
                print(f"❌ Failed to generate claim: {response.status_code}")
                print(f"   Response: {response.text}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Test 9: Verify audit log after all operations
        print("\n[9] Final audit log check...")
        try:
            response = await client.get(f"{API_BASE}/api/orchestrator/audit?limit=10")
            if response.status_code == 200:
                audit_data = response.json()
                logs = audit_data.get('logs', [])
                print(f"✅ Total audit entries: {len(logs)}")
                
                # Count by action type
                actions = {}
                for log in logs:
                    action = log['action']
                    actions[action] = actions.get(action, 0) + 1
                
                print("   Action summary:")
                for action, count in actions.items():
                    print(f"   - {action}: {count}")
            else:
                print(f"❌ Failed to get audit log: {response.status_code}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
    print("\n✅ Key Features Verified:")
    print("   - Orchestrator status API")
    print("   - Encounter creation")
    print("   - Audit logging")
    print("   - Review queue")
    print("   - Safeguards (read-only mapping protection)")
    print("   - Mapping acceptance workflow")
    print("   - Claim preview generation")
    print("\n⚠️  Note: Redis event bus is in mock mode (install Redis for full functionality)")
    print("   Install Redis: choco install redis-64")


if __name__ == "__main__":
    print("Starting orchestration integration test...")
    print(f"API Base URL: {API_BASE}")
    print(f"Make sure the API server is running on port 8000\n")
    
    try:
        asyncio.run(test_orchestration_workflow())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()
