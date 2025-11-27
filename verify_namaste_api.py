
import httpx
import json
import time

def test_namaste_suggest_live():
    url = "http://localhost:8002/api/suggest"
    print(f"Testing live server at {url}...")
    
    terms = [
        "prANavAtakopaH",
        "udAnavAtakopaH",
        "vyAnavAtakopaH"
    ]
    
    for term in terms:
        print(f"\nTesting term: '{term}'...")
        try:
            response = httpx.post(url, json={"term": term, "k": 5}, timeout=10.0)
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('data', {}).get('results', [])
                print(f"Success! Found {len(results)} results.")
                for res in results:
                    print(f"  - Code: {res.get('icd_code')}, Title: {res.get('icd_title')}, Confidence: {res.get('confidence')}")
                    if res.get('provenance') and res['provenance'][0].get('source') == 'namaste_csv':
                         print("    (Confirmed NAMASTE exact match)")
            else:
                print(f"Request failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Connection error: {e}")
            print("Is the server running on port 8000?")

if __name__ == "__main__":
    test_namaste_suggest_live()
