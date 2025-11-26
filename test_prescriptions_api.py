"""
Test script for Prescriptions V2 API
"""

import requests
import json
from datetime import datetime, timedelta

API_BASE = "http://localhost:8000"

def test_prescriptions_api():
    print("Testing Prescriptions V2 API...\n")
    
    # 1. List prescriptions
    print("1. Testing GET /api/v2/prescriptions")
    response = requests.get(f"{API_BASE}/api/v2/prescriptions")
    print(f"   Status: {response.status_code}")
    if response.ok:
        data = response.json()
        print(f"   Found {data['count']} prescriptions")
    print()
    
    # 2. Create prescription
    print("2. Testing POST /api/v2/prescriptions")
    prescription_data = {
        "patientId": "1",  # Assuming patient ID 1 exists
        "doctorId": "admin",
        "diagnosis": "Common Cold",
        "notes": "Rest and hydration recommended",
        "items": [
            {
                "medicine_name": "Paracetamol",
                "form": "Tablet",
                "dose": "500mg",
                "frequency": "3 times daily",
                "duration": "5 days",
                "instructions": "Take after meals"
            },
            {
                "medicine_name": "Vitamin C",
                "form": "Tablet",
                "dose": "1000mg",
                "frequency": "Once daily",
                "duration": "7 days",
                "instructions": "Take with water"
            }
        ]
    }
    
    response = requests.post(
        f"{API_BASE}/api/v2/prescriptions",
        json=prescription_data
    )
    print(f"   Status: {response.status_code}")
    if response.ok:
        data = response.json()
        prescription_id = data['prescription']['id']
        print(f"   Created prescription ID: {prescription_id}")
        print(f"   Items count: {len(data['prescription']['items'])}")
    else:
        print(f"   Error: {response.text}")
        prescription_id = None
    print()
    
    if prescription_id:
        # 3. Get prescription details
        print(f"3. Testing GET /api/v2/prescriptions/{prescription_id}")
        response = requests.get(f"{API_BASE}/api/v2/prescriptions/{prescription_id}")
        print(f"   Status: {response.status_code}")
        if response.ok:
            data = response.json()
            print(f"   Diagnosis: {data.get('diagnosis')}")
            print(f"   Items: {len(data.get('items', []))}")
        print()
        
        # 4. Update prescription
        print(f"4. Testing PUT /api/v2/prescriptions/{prescription_id}")
        update_data = {
            "diagnosis": "Common Cold with Fever",
            "notes": "Rest, hydration, and monitor temperature"
        }
        response = requests.put(
            f"{API_BASE}/api/v2/prescriptions/{prescription_id}",
            json=update_data
        )
        print(f"   Status: {response.status_code}")
        if response.ok:
            print("   Prescription updated successfully")
        print()
        
        # 5. List prescriptions again
        print("5. Testing GET /api/v2/prescriptions (after creation)")
        response = requests.get(f"{API_BASE}/api/v2/prescriptions")
        print(f"   Status: {response.status_code}")
        if response.ok:
            data = response.json()
            print(f"   Total prescriptions: {data['count']}")
        print()
    
    print("✓ Prescriptions API tests completed!")

if __name__ == "__main__":
    try:
        test_prescriptions_api()
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to API. Make sure the backend is running on port 8000")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
