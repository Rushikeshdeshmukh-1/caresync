"""
Simplified Orchestration Test
Tests core orchestration features without dependencies
"""

import asyncio
import httpx

API_BASE = "http://localhost:8000"


async def test_orchestration_features():
    """Test orchestration-specific features"""
    print("=" * 70)
    print("ORCHESTRATION SYSTEM TEST")
    print("=" * 70)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        # Test 1: Orchestrator Status
        print("\n✓ TEST 1: Orchestrator Status")
        print("-" * 70)
        try:
            response = await client.get(f"{API_BASE}/api/orchestrator/status")
            if response.status_code == 200:
                status = response.json()
                print(f"✅ Status: {status['status']}")
                print(f"   Mode: {status['mode']}")
                print(f"   Blocked writes: {status['blocked_write_count']}")
                print(f"   Last reset: {status['last_reset']}")
            else:
                print(f"❌ FAILED: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ ERROR: {e}")
            return False
        
        # Test 2: Audit Log
        print("\n✓ TEST 2: Audit Log")
        print("-" * 70)
        try:
            response = await client.get(f"{API_BASE}/api/orchestrator/audit?limit=10")
            if response.status_code == 200:
                data = response.json()
                logs = data.get('logs', [])
                print(f"✅ Retrieved {len(logs)} audit entries")
                if logs:
                    print(f"   Recent actions:")
                    for log in logs[:3]:
                        print(f"   - {log['action']} ({log['status']})")
                else:
                    print(f"   (No audit entries yet)")
            else:
                print(f"❌ FAILED: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ ERROR: {e}")
            return False
        
        # Test 3: Review Queue
        print("\n✓ TEST 3: Review Queue")
        print("-" * 70)
        try:
            response = await client.get(f"{API_BASE}/api/orchestrator/review_queue?status=open")
            if response.status_code == 200:
                data = response.json()
                tasks = data.get('tasks', [])
                print(f"✅ Retrieved {len(tasks)} review tasks")
                if tasks:
                    print(f"   Open tasks:")
                    for task in tasks[:3]:
                        print(f"   - Task {task['id']}: {task['reason']} (priority: {task['priority']})")
                else:
                    print(f"   (No pending review tasks)")
            else:
                print(f"❌ FAILED: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ ERROR: {e}")
            return False
        
        # Test 4: Safeguards
        print("\n✓ TEST 4: Safeguards (Read-Only Mapping Protection)")
        print("-" * 70)
        try:
            from services.safeguards import safe_write, is_mapping_resource
            
            # Test resource detection
            print("   Testing resource detection:")
            test_cases = [
                ("namaste.csv", True),
                ("data/namaste.csv", True),
                ("encounters", False),
                ("patients", False)
            ]
            
            all_correct = True
            for resource, should_be_protected in test_cases:
                is_protected = is_mapping_resource(resource)
                status = "✓" if is_protected == should_be_protected else "✗"
                print(f"   {status} {resource}: {'protected' if is_protected else 'allowed'}")
                if is_protected != should_be_protected:
                    all_correct = False
            
            if not all_correct:
                print("❌ Resource detection failed")
                return False
            
            # Test write blocking
            print("\n   Testing write blocking:")
            try:
                safe_write("namaste.csv", {"test": "data"})
                print("   ❌ CRITICAL: Write was allowed (safeguard failed!)")
                return False
            except PermissionError as e:
                print(f"   ✅ Write blocked: {str(e)[:60]}...")
            
            # Check audit log for blocked write
            response = await client.get(f"{API_BASE}/api/orchestrator/audit?action=mapping_write_blocked&limit=1")
            if response.status_code == 200:
                data = response.json()
                if data.get('logs'):
                    print("   ✅ Blocked write logged in audit")
                else:
                    print("   ⚠️  Blocked write not in audit (may be from previous run)")
            
        except Exception as e:
            print(f"❌ ERROR: {e}")
            return False
        
        # Test 5: Pause/Resume
        print("\n✓ TEST 5: Pause/Resume Controls")
        print("-" * 70)
        try:
            # Pause
            response = await client.post(f"{API_BASE}/api/orchestrator/pause")
            if response.status_code == 200:
                print("✅ Orchestrator paused")
            else:
                print(f"❌ Pause failed: {response.status_code}")
                return False
            
            # Check status
            response = await client.get(f"{API_BASE}/api/orchestrator/status")
            if response.status_code == 200:
                status = response.json()
                if status['status'] == 'paused':
                    print("✅ Status confirmed: paused")
                else:
                    print(f"❌ Status mismatch: {status['status']}")
                    return False
            
            # Resume
            response = await client.post(f"{API_BASE}/api/orchestrator/resume")
            if response.status_code == 200:
                print("✅ Orchestrator resumed")
            else:
                print(f"❌ Resume failed: {response.status_code}")
                return False
            
            # Check status again
            response = await client.get(f"{API_BASE}/api/orchestrator/status")
            if response.status_code == 200:
                status = response.json()
                if status['status'] == 'active':
                    print("✅ Status confirmed: active")
                else:
                    print(f"❌ Status mismatch: {status['status']}")
                    return False
            
        except Exception as e:
            print(f"❌ ERROR: {e}")
            return False
        
        # Test 6: Database Tables
        print("\n✓ TEST 6: Database Tables")
        print("-" * 70)
        try:
            from models.database import SessionLocal, OrchestratorAudit, ReviewQueue, ClaimPacket, ModelMetrics
            
            session = SessionLocal()
            
            # Count records in each table
            audit_count = session.query(OrchestratorAudit).count()
            review_count = session.query(ReviewQueue).count()
            claim_count = session.query(ClaimPacket).count()
            metrics_count = session.query(ModelMetrics).count()
            
            print(f"✅ orchestrator_audit: {audit_count} records")
            print(f"✅ review_queue: {review_count} records")
            print(f"✅ claim_packets: {claim_count} records")
            print(f"✅ model_metrics: {metrics_count} records")
            
            session.close()
            
        except Exception as e:
            print(f"❌ ERROR: {e}")
            return False
    
    return True


async def main():
    print("Testing Orchestration System Components\n")
    
    success = await test_orchestration_features()
    
    print("\n" + "=" * 70)
    if success:
        print("✅ ALL TESTS PASSED")
        print("=" * 70)
        print("\n🎉 Orchestration system is working correctly!")
        print("\nKey Features Verified:")
        print("  ✓ Orchestrator status monitoring")
        print("  ✓ Audit logging")
        print("  ✓ Review queue management")
        print("  ✓ Read-only safeguards (mapping protection)")
        print("  ✓ Pause/resume controls")
        print("  ✓ Database tables")
        print("\n⚠️  Note: Redis event bus is in mock mode")
        print("   For full async functionality: choco install redis-64")
    else:
        print("❌ SOME TESTS FAILED")
        print("=" * 70)
        print("\nPlease check the errors above")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nTest interrupted")
    except Exception as e:
        print(f"\n\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
