"""
Simple Backend Health Check
Tests if backend is responding at all
"""

import requests

print("Checking backend health...")

try:
    response = requests.get("http://localhost:8000/health", timeout=2)
    print(f"✓ Backend is responding!")
    print(f"  Status: {response.status_code}")
    print(f"  Response: {response.json()}")
except requests.exceptions.Timeout:
    print("✗ Backend timeout - still loading")
except requests.exceptions.ConnectionError:
    print("✗ Backend not running")
except Exception as e:
    print(f"✗ Error: {e}")

print("\nTrying login endpoint...")
try:
    response = requests.post(
        "http://localhost:8000/api/auth/login",
        json={"email": "patient@test.com", "password": "patient123"},
        timeout=10
    )
    print(f"✓ Login endpoint responded!")
    print(f"  Status: {response.status_code}")
    if response.ok:
        data = response.json()
        print(f"  User: {data.get('user', {}).get('name')}")
        print(f"  Role: {data.get('user', {}).get('role')}")
    else:
        print(f"  Error: {response.json()}")
except requests.exceptions.Timeout:
    print("✗ Login timeout - backend may be loading ML models")
    print("  Wait 30-60 seconds and try again")
except Exception as e:
    print(f"✗ Error: {e}")
