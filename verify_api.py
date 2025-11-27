from fastapi.testclient import TestClient
from main import app
import os

def test_api():
    print("Initializing TestClient...")
    client = TestClient(app)
    
    print("\nTesting /api/icd11/search...")
    response = client.get("/api/icd11/search?q=diabetes")
    if response.status_code == 200:
        data = response.json()
        print(f"Success! Found {len(data.get('destinationEntities', []))} results.")
        if data.get('destinationEntities'):
            first = data['destinationEntities'][0]
            print(f"First result: {first.get('title')} (ID: {first.get('id')})")
            
            # Test entity details
            entity_id = first.get('id')
            # The ID might be a full URL, we can pass it directly or extract the ID
            # The route accepts {entity_id:path} so it handles slashes
            
            print(f"\nTesting /api/icd11/entity/{entity_id}...")
            # We need to encode the URL if it's a full path, or just pass it if the client handles it.
            # TestClient handles paths well.
            response_entity = client.get(f"/api/icd11/entity/{entity_id}")
            
            if response_entity.status_code == 200:
                details = response_entity.json()
                print("Entity details fetched successfully.")
                print(f"Title: {details.get('title')}")
            else:
                print(f"Failed to fetch entity: {response_entity.status_code} - {response_entity.text}")
    else:
        print(f"Search failed: {response.status_code} - {response.text}")

if __name__ == "__main__":
    # Check if credentials are set
    if not os.getenv("ICD11_CLIENT_ID") or os.getenv("ICD11_CLIENT_ID") == "your_client_id_here":
        print("WARNING: ICD11_CLIENT_ID is not set. API calls will likely fail.")
    
    try:
        test_api()
    except Exception as e:
        print(f"An error occurred: {e}")
