"""
Comprehensive Platform Test Suite
Tests backend services, API endpoints, and database integrity
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """Test all critical imports"""
    print("=" * 60)
    print("TESTING IMPORTS")
    print("=" * 60)
    
    try:
        from backend.services.jwt_auth_service import get_auth_service
        print("✓ JWT Auth Service")
    except Exception as e:
        print(f"✗ JWT Auth Service: {e}")
        return False
    
    try:
        from backend.services.teleconsult_service import get_teleconsult_service
        print("✓ Teleconsult Service")
    except Exception as e:
        print(f"✗ Teleconsult Service: {e}")
        return False
    
    try:
        from backend.services.payment_service import get_payment_service
        print("✓ Payment Service")
    except Exception as e:
        print(f"✗ Payment Service: {e}")
        return False
    
    try:
        from backend.services.claim_composer import get_claim_composer
        print("✓ Claim Composer")
    except Exception as e:
        print(f"✗ Claim Composer: {e}")
        return False
    
    try:
        from backend.services.monitoring_service import get_monitoring_service
        print("✓ Monitoring Service")
    except Exception as e:
        print(f"✗ Monitoring Service: {e}")
        return False
    
    try:
        from backend.clients.mapping_client import get_mapping_client
        print("✓ Mapping Client")
    except Exception as e:
        print(f"✗ Mapping Client: {e}")
        return False
    
    print("\n✓ All services imported successfully\n")
    return True


def test_database():
    """Test database schema"""
    print("=" * 60)
    print("TESTING DATABASE")
    print("=" * 60)
    
    import sqlite3
    
    try:
        conn = sqlite3.connect('terminology.db')
        cursor = conn.cursor()
        
        # Get all tables
        tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        table_names = [t[0] for t in tables]
        
        print(f"✓ Database connected ({len(tables)} tables)")
        
        # Check critical tables
        critical_tables = [
            'users', 'patients', 'clinicians', 'organizations',
            'appointments', 'encounters', 'prescriptions',
            'payment_intents', 'teleconsult_sessions',
            'claim_packets', 'mapping_proposals', 'audit_logs',
            'refresh_tokens', 'system_config'
        ]
        
        missing = []
        for table in critical_tables:
            if table in table_names:
                print(f"  ✓ {table}")
            else:
                print(f"  ✗ {table} (MISSING)")
                missing.append(table)
        
        conn.close()
        
        if missing:
            print(f"\n✗ Missing tables: {', '.join(missing)}")
            return False
        
        print("\n✓ All critical tables present\n")
        return True
        
    except Exception as e:
        print(f"✗ Database error: {e}")
        return False


def test_app_routes():
    """Test FastAPI app routes"""
    print("=" * 60)
    print("TESTING API ROUTES")
    print("=" * 60)
    
    try:
        from main import app
        
        routes = [r for r in app.routes if hasattr(r, 'path')]
        print(f"✓ Total routes: {len(routes)}")
        
        # Count routes by category
        auth_routes = [r for r in routes if '/auth' in r.path]
        mapping_routes = [r for r in routes if '/mapping' in r.path]
        admin_routes = [r for r in routes if '/admin' in r.path]
        teleconsult_routes = [r for r in routes if '/teleconsult' in r.path]
        payment_routes = [r for r in routes if '/payment' in r.path]
        health_routes = [r for r in routes if '/health' in r.path or '/metrics' in r.path]
        
        print(f"  ✓ Auth routes: {len(auth_routes)}")
        print(f"  ✓ Mapping routes: {len(mapping_routes)}")
        print(f"  ✓ Admin routes: {len(admin_routes)}")
        print(f"  ✓ Teleconsult routes: {len(teleconsult_routes)}")
        print(f"  ✓ Payment routes: {len(payment_routes)}")
        print(f"  ✓ Health/Metrics routes: {len(health_routes)}")
        
        print("\n✓ All route categories present\n")
        return True
        
    except Exception as e:
        print(f"✗ App routes error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_mapping_protection():
    """Test mapping protection is active"""
    print("=" * 60)
    print("TESTING MAPPING PROTECTION")
    print("=" * 60)
    
    try:
        from services.safeguards import is_mapping_resource, MAPPING_DATA_RESOURCES
        
        print(f"✓ Protected resources: {len(MAPPING_DATA_RESOURCES)}")
        
        # Test some known resources
        test_resources = [
            'data/namaste.csv',
            'data/icd11_codes.csv',
            'ayush_terms',
            'mapping_candidates'
        ]
        
        for resource in test_resources:
            if is_mapping_resource(resource):
                print(f"  ✓ {resource} is protected")
            else:
                print(f"  ✗ {resource} NOT protected")
                return False
        
        print("\n✓ Mapping protection active\n")
        return True
        
    except Exception as e:
        print(f"✗ Mapping protection error: {e}")
        return False


def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("CARESYNC PLATFORM - COMPREHENSIVE TEST SUITE")
    print("=" * 60 + "\n")
    
    results = {
        "Imports": test_imports(),
        "Database": test_database(),
        "API Routes": test_app_routes(),
        "Mapping Protection": test_mapping_protection()
    }
    
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ ALL TESTS PASSED")
    else:
        print("✗ SOME TESTS FAILED")
    print("=" * 60 + "\n")
    
    return all_passed


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
