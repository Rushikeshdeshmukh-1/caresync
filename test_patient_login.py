"""
Test Patient Login
Quick script to test if patient login is working
"""

import requests

def test_patient_login():
    print("Testing patient login...")
    
    url = "http://localhost:8000/api/auth/login"
    
    # Test patient login
    payload = {
        "email": "patient@test.com",
        "password": "patient123"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        
        print(f"\nStatus Code: {response.status_code}")
        
        if response.ok:
            data = response.json()
            print("✓ Login successful!")
            print(f"  User: {data.get('user', {}).get('name')}")
            print(f"  Role: {data.get('user', {}).get('role')}")
            print(f"  Token: {data.get('access_token', '')[:30]}...")
        else:
            error = response.json()
            print(f"✗ Login failed: {error.get('detail', 'Unknown error')}")
            print(f"  Full response: {error}")
            
    except Exception as e:
        print(f"✗ Error: {str(e)}")

if __name__ == "__main__":
    test_patient_login()
