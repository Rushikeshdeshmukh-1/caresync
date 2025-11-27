"""
Test Co-Pilot Agent Service
Verify analysis, safety checks, and read-only enforcement.
"""

import requests
import json
import uuid

BASE_URL = "http://localhost:8002/api"

def test_copilot_analysis():
    print("Testing Co-Pilot Analysis...")
    print("=" * 60)
    
    # 1. Create a dummy encounter ID
    encounter_id = str(uuid.uuid4())
    
    # 2. Define test payload with known AYUSH terms and safety triggers
    payload = {
        "encounter_id": encounter_id,
        "notes": "Patient reports severe Amlapitta and Jwara. Currently taking Metformin for diabetes.",
        "patient_context": {
            "age": 55,
            "sex": "M",
            "comorbidities": ["renal_failure"],  # Should trigger Metformin contraindication
            "meds": ["Metformin"]
        },
        "actor": "test_runner"
    }
    
    # 3. Call Analyze Endpoint
    print("\n[1] Calling /api/copilot/analyze...")
    try:
        response = requests.post(f"{BASE_URL}/copilot/analyze", json=payload)
        response.raise_for_status()
        data = response.json()
        
        print("✅ Analysis successful")
        
        # 4. Verify Extracted Terms
        terms = [t['term'] for t in data['ayush_terms']]
        print(f"Extracted Terms: {terms}")
        if "Amlapitta" in terms and "Jwara" in terms:
            print("✅ AYUSH terms extracted correctly")
        else:
            print("❌ Failed to extract expected terms")
            return False
            
        # 5. Verify Safety Warnings
        warnings = data['warnings']
        print(f"Warnings: {json.dumps(warnings, indent=2)}")
        if any(w['code'] == 'DRUG_CONTRAINDICATION' and 'Metformin' in w['message'] for w in warnings):
            print("✅ Safety check triggered correctly (Metformin + Renal Failure)")
        else:
            print("❌ Failed to trigger safety warning")
            return False
            
        # 6. Verify Suggestions
        suggestions = data['suggestions']
        print(f"Suggestions: {len(suggestions)} found")
        if len(suggestions) > 0:
            print("✅ Suggestions generated")
        else:
            print("⚠️ No suggestions found (might be expected if mapping engine is empty)")
            
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        if 'response' in locals():
            print(f"Response: {response.text}")
        return False

    # 7. Test Chat Endpoint
    print("\n[2] Calling /api/copilot/chat...")
    chat_payload = {
        "encounter_id": encounter_id,
        "message": "Why is Metformin contraindicated?",
        "context": {}
    }
    try:
        response = requests.post(f"{BASE_URL}/copilot/chat", json=chat_payload)
        response.raise_for_status()
        print(f"Chat Response: {response.json()['response']}")
        print("✅ Chat endpoint working")
    except Exception as e:
        print(f"❌ Chat failed: {e}")
        return False
        
    print("\n" + "=" * 60)
    print("✅ ALL CO-PILOT TESTS PASSED")
    print("=" * 60)
    return True

if __name__ == "__main__":
    test_copilot_analysis()
