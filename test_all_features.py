"""
Comprehensive Platform Test Suite
Tests all backend APIs and features to identify issues
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_health_endpoints():
    """Test health and monitoring endpoints"""
    print("\n=== Testing Health & Monitoring ===")
    
    endpoints = [
        "/api/health",
        "/api/health/ready",
        "/api/health/live",
        "/api/metrics"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            status = "✓" if response.status_code == 200 else "✗"
            print(f"{status} {endpoint}: {response.status_code}")
        except Exception as e:
            print(f"✗ {endpoint}: ERROR - {str(e)}")

def test_auth_endpoints():
    """Test authentication endpoints"""
    print("\n=== Testing Authentication ===")
    
    # Test login
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@test.com", "password": "admin123"},
            timeout=5
        )
        if response.status_code == 200:
            print(f"✓ Login: {response.status_code}")
            data = response.json()
            token = data.get('access_token')
            return token
        else:
            print(f"✗ Login: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"✗ Login: ERROR - {str(e)}")
        return None

def test_protected_endpoints(token):
    """Test protected endpoints with authentication"""
    print("\n=== Testing Protected Endpoints ===")
    
    if not token:
        print("✗ No token available, skipping protected endpoint tests")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    endpoints = [
        ("/api/auth/me", "GET"),
        ("/api/patients", "GET"),
        ("/api/appointments", "GET"),
        ("/api/encounters", "GET"),
        ("/api/prescriptions", "GET"),
        ("/api/admin/mapping/feedback", "GET"),
        ("/api/admin/audit-logs", "GET"),
    ]
    
    for endpoint, method in endpoints:
        try:
            if method == "GET":
                response = requests.get(f"{BASE_URL}{endpoint}", headers=headers, timeout=5)
            else:
                response = requests.post(f"{BASE_URL}{endpoint}", headers=headers, timeout=5)
            
            status = "✓" if response.status_code in [200, 201] else "✗"
            print(f"{status} {method} {endpoint}: {response.status_code}")
        except Exception as e:
            print(f"✗ {method} {endpoint}: ERROR - {str(e)}")

def test_mapping_endpoints(token):
    """Test mapping-related endpoints"""
    print("\n=== Testing Mapping Endpoints ===")
    
    if not token:
        print("✗ No token available, skipping mapping tests")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test mapping search
    try:
        response = requests.post(
            f"{BASE_URL}/api/mapping/search",
            headers=headers,
            json={"query": "fever", "limit": 5},
            timeout=5
        )
        status = "✓" if response.status_code == 200 else "✗"
        print(f"{status} Mapping Search: {response.status_code}")
    except Exception as e:
        print(f"✗ Mapping Search: ERROR - {str(e)}")

def test_database_connectivity():
    """Test database connectivity"""
    print("\n=== Testing Database ===")
    
    try:
        import sqlite3
        conn = sqlite3.connect('terminology.db')
        cursor = conn.cursor()
        
        # Check key tables
        tables = ['users', 'patients', 'appointments', 'encounters', 'audit_logs']
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"✓ Table '{table}': {count} records")
            except Exception as e:
                print(f"✗ Table '{table}': ERROR - {str(e)}")
        
        conn.close()
    except Exception as e:
        print(f"✗ Database connection: ERROR - {str(e)}")

def main():
    print("=" * 60)
    print("CARESYNC PLATFORM - COMPREHENSIVE TEST SUITE")
    print("=" * 60)
    
    # Test health endpoints (no auth required)
    test_health_endpoints()
    
    # Test database
    test_database_connectivity()
    
    # Test authentication and get token
    token = test_auth_endpoints()
    
    # Test protected endpoints
    test_protected_endpoints(token)
    
    # Test mapping endpoints
    test_mapping_endpoints(token)
    
    print("\n" + "=" * 60)
    print("TEST SUITE COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()
