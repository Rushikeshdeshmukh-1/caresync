"""
Quick Backend Health Check
Simple test to see if backend is responding
"""

import requests
import time

def quick_test():
    print("Testing backend health...")
    
    try:
        start = time.time()
        response = requests.get("http://localhost:8000/", timeout=10)
        elapsed = time.time() - start
        print(f"✓ Root endpoint: {response.status_code} ({elapsed:.2f}s)")
        print(f"  Response: {response.text[:200]}")
    except requests.exceptions.Timeout:
        print("✗ Backend is timing out (>10s)")
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to backend")
    except Exception as e:
        print(f"✗ Error: {e}")

if __name__ == "__main__":
    quick_test()
