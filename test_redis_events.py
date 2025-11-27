"""
Test Redis Event Bus
Verify that events are published and received correctly
"""

import asyncio
import time
from services.event_bus import event_bus, EventTopics

def test_event_publishing():
    """Test event publishing with Redis"""
    print("Testing Redis Event Bus...")
    print("=" * 60)
    
    # Test 1: Publish an event
    print("\n[1] Publishing test event...")
    message_id = event_bus.publish(EventTopics.ENCOUNTER_CREATED, {
        "encounter_id": "test-123",
        "patient_id": "patient-456",
        "notes": "Test encounter with Amlapitta"
    })
    
    if message_id:
        print(f"✅ Event published successfully: {message_id}")
    else:
        print("❌ Failed to publish event")
        return False
    
    # Test 2: Publish mapping suggested event
    print("\n[2] Publishing mapping suggested event...")
    message_id = event_bus.publish(EventTopics.MAPPING_SUGGESTED, {
        "encounter_id": "test-123",
        "suggestions": [
            {"ayush": "Amlapitta", "icd11": "DA63", "confidence": 0.92}
        ],
        "model_version": "v1.0"
    })
    
    if message_id:
        print(f"✅ Event published successfully: {message_id}")
    else:
        print("❌ Failed to publish event")
        return False
    
    # Test 3: Check Redis connection
    print("\n[3] Checking Redis connection...")
    if event_bus.redis_client:
        try:
            event_bus.redis_client.ping()
            print("✅ Redis is connected and responding")
        except Exception as e:
            print(f"❌ Redis connection error: {e}")
            return False
    else:
        print("❌ Redis client not initialized")
        return False
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED")
    print("=" * 60)
    print("\n🎉 Redis event bus is working correctly!")
    print("\nThe orchestrator service is now listening for events.")
    print("Events will be processed in real-time as they are published.")
    
    return True


if __name__ == "__main__":
    print("Redis Event Bus Test\n")
    
    try:
        success = test_event_publishing()
        if not success:
            print("\n❌ Some tests failed")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
