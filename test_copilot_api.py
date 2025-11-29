import requests
import json

BASE_URL = "http://localhost:8000"

def test_copilot_analyze():
    print("Testing Co-Pilot Analyze Endpoint...")
    
    payload = {
        "encounter_id": "test-encounter-1",
        "notes": "Patient complains of Jwara (fever) and Kasa (cough).",
        "patient_context": {
            "meds": ["Paracetamol"],
            "comorbidities": []
        },
        "actor": "clinician"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/copilot/analyze",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("Response:", json.dumps(response.json(), indent=2))
        else:
            print("Error:", response.text)
            
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_copilot_analyze()
