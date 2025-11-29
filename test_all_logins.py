"""
Direct Login Test - Test all user accounts
"""

import requests
import json

def test_login(email, password, role_name):
    print(f"\n{'='*60}")
    print(f"Testing {role_name} login: {email}")
    print('='*60)
    
    url = "http://localhost:8000/api/auth/login"
    payload = {"email": email, "password": password}
    
    try:
        response = requests.post(url, json=payload, timeout=5)
        
        print(f"Status Code: {response.status_code}")
        
        if response.ok:
            data = response.json()
            print("✓ LOGIN SUCCESSFUL!")
            print(f"  Name: {data.get('user', {}).get('name')}")
            print(f"  Email: {data.get('user', {}).get('email')}")
            print(f"  Role: {data.get('user', {}).get('role')}")
            print(f"  Token: {data.get('access_token', '')[:40]}...")
            return True
        else:
            print("✗ LOGIN FAILED")
            try:
                error = response.json()
                print(f"  Error: {error.get('detail', 'Unknown error')}")
            except:
                print(f"  Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("✗ REQUEST TIMEOUT (backend may still be loading)")
        return False
    except requests.exceptions.ConnectionError:
        print("✗ CONNECTION ERROR (backend not running?)")
        return False
    except Exception as e:
        print(f"✗ ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    print("\n🔐 Testing All User Logins")
    print("="*60)
    
    # Test all accounts
    results = {
        "Admin": test_login("admin@test.com", "admin123", "Admin"),
        "Doctor": test_login("doctor@test.com", "doctor123", "Doctor"),
        "Patient": test_login("patient@test.com", "patient123", "Patient")
    }
    
    print(f"\n{'='*60}")
    print("SUMMARY")
    print('='*60)
    for role, success in results.items():
        status = "✓ WORKING" if success else "✗ FAILED"
        print(f"{role:10} {status}")
    
    if not results["Patient"]:
        print("\n⚠️  PATIENT LOGIN FAILED!")
        print("Run: python create_patient_account.py")
