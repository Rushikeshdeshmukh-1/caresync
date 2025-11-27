import asyncio
import os
from services.icd11_service import ICD11Service

async def main():
    print("Initializing ICD11Service...")
    service = ICD11Service()
    
    client_id = os.getenv("ICD11_CLIENT_ID")
    if not client_id or client_id == "your_client_id_here":
        print("WARNING: ICD11_CLIENT_ID is not set or is using the placeholder.")
        print("Authentication is expected to fail.")
    
    try:
        print("\nAttempting to get token...")
        token = await service.get_token()
        print(f"Success! Token received: {token[:10]}...")
        
        print("\nSearching for 'diabetes'...")
        results = await service.search_entities("diabetes")
        print(f"Search successful! Found {len(results.get('destinationEntities', []))} results.")
        
        if results.get('destinationEntities'):
            first_entity = results['destinationEntities'][0]
            print(f"First result: {first_entity.get('title')} (ID: {first_entity.get('id')})")
            
            print(f"\nFetching details for {first_entity.get('id')}...")
            details = await service.get_entity(first_entity['id'])
            print("Details fetched successfully.")
            if 'code' in details and details['code']:
                 print(f"Code: {details['code']}")
            else:
                 print("Note: No code found in Foundation entity. Use MMS linearization for codes.")
            
    except Exception as e:
        print(f"\nERROR: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
