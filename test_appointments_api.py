"""
Test script for Appointments V2 API
"""
import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"

def test_appointments_api():
    """Test appointments V2 API endpoints"""
    print("Testing Appointments V2 API...\n")
    
    # Test 1: List appointments
    print("1. Testing GET /api/v2/appointments")
    response = requests.get(f"{BASE_URL}/api/v2/appointments")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Found {len(data.get('appointments', []))} appointments")
    print()
    
    # Test 2: Create appointment
    print("2. Testing POST /api/v2/appointments")
    # First, get a patient and staff ID
    patients = requests.get(f"{BASE_URL}/api/patients?limit=1").json()
    staff = requests.get(f"{BASE_URL}/api/patients?limit=1").json()  # Using patients as placeholder
    
    if patients.get('patients'):
        patient_id = patients['patients'][0]['id']
        
        # Create appointment
        start_time = (datetime.utcnow() + timedelta(days=1)).isoformat()
        end_time = (datetime.utcnow() + timedelta(days=1, hours=1)).isoformat()
        
        appointment_data = {
            "patientId": patient_id,
            "doctorId": "admin",  # Using admin as placeholder
            "startTime": start_time,
            "endTime": end_time,
            "reason": "Test appointment",
            "notes": "Created via API test"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v2/appointments",
            json=appointment_data
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            appointment_id = data.get('appointment', {}).get('id')
            print(f"   Created appointment: {appointment_id}")
            
            # Test 3: Get appointment
            print("\n3. Testing GET /api/v2/appointments/{id}")
            response = requests.get(f"{BASE_URL}/api/v2/appointments/{appointment_id}")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                print(f"   Retrieved appointment successfully")
            
            # Test 4: Update appointment
            print("\n4. Testing PUT /api/v2/appointments/{id}")
            update_data = {
                "status": "confirmed",
                "notes": "Updated via API test"
            }
            response = requests.put(
                f"{BASE_URL}/api/v2/appointments/{appointment_id}",
                json=update_data
            )
            print(f"   Status: {response.status_code}")
            
            # Test 5: Cancel appointment
            print("\n5. Testing POST /api/v2/appointments/{id}/cancel")
            response = requests.post(f"{BASE_URL}/api/v2/appointments/{appointment_id}/cancel")
            print(f"   Status: {response.status_code}")
        else:
            print(f"   Error: {response.text}")
    else:
        print("   No patients found to create appointment")
    
    print()
    
    # Test 6: Dashboard stats
    print("6. Testing GET /api/dashboard/stats (V2 data)")
    response = requests.get(f"{BASE_URL}/api/dashboard/stats")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Total patients: {data.get('total_patients')}")
        print(f"   Today's appointments: {data.get('today_appointments')}")
        print(f"   Pending appointments: {data.get('pending_appointments')}")
        print(f"   Data source: {data.get('data_source')}")
    print()
    
    print("✓ API tests completed!")

if __name__ == "__main__":
    test_appointments_api()
