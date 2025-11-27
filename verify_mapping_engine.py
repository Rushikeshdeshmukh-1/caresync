import asyncio
import os
from services.icd11_service import ICD11Service
from services.mapping_engine import MappingEngine
from services.faiss_index import FaissIndex

# Mock FaissIndex to avoid loading large files if not needed, or use real one if simple
class MockFaissIndex:
    def is_loaded(self):
        return False
    def query(self, term, k=5):
        return []

async def main():
    print("Initializing services...")
    
    # Check credentials
    if not os.getenv("ICD11_CLIENT_ID") or os.getenv("ICD11_CLIENT_ID") == "your_client_id_here":
        print("WARNING: ICD11_CLIENT_ID is not set. API calls will fail.")
        return

    icd11_service = ICD11Service()
    # We can use a mock FaissIndex since we want to test the API fallback
    # which happens when local candidates are empty.
    faiss_index = MockFaissIndex()
    
    mapping_engine = MappingEngine(faiss_index, icd11_service)
    
    # Use a term likely not in the CSV but valid in ICD-11
    term = "COVID-19" 
    print(f"\nTesting suggestion for '{term}' (expecting API fallback)...")
    
    try:
        result = await mapping_engine.suggest(term)
        print(f"Result type: {result.get('type')}")
        
        results = result.get('results', [])
        print(f"Found {len(results)} results.")
        
        if results:
            first = results[0]
            print(f"First result: {first.get('icd_title')} (Code: {first.get('icd_code')})")
            print(f"Provenance: {first.get('provenance')}")
            
            if first.get('provenance', {}).get('source') == 'who_icd11_api':
                print("SUCCESS: Result came from WHO ICD-11 API.")
            else:
                print("WARNING: Result did not come from API as expected.")
        else:
            print("No results found.")
            
    except Exception as e:
        print(f"Error during suggestion: {e}")

if __name__ == "__main__":
    asyncio.run(main())
