
import logging
from services.mapping_engine import MappingEngine
from services.faiss_index import FaissIndex

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_load():
    print("Initializing MappingEngine...")
    # We don't need the actual FAISS index for this test, just the class structure
    # But MappingEngine requires it.
    # We can mock it or just let it try to load (it handles missing index gracefully)
    faiss_index = FaissIndex() 
    engine = MappingEngine(faiss_index=faiss_index)
    
    # Test term from new dataset
    test_code = "AAA-2.2"
    test_term = "prANavAtakopaH"
    
    print(f"Checking for code: {test_code}")
    
    if test_code.lower() in engine.ayush_map:
        entry = engine.ayush_map[test_code.lower()]
        print(f"SUCCESS: Found code {test_code}")
        print(f"Entry: {entry}")
    else:
        print(f"FAILURE: Could not find code {test_code}")

    print(f"Checking for term: {test_term}")
    if test_term.lower() in engine.ayush_map:
         entry = engine.ayush_map[test_term.lower()]
         print(f"SUCCESS: Found term {test_term}")
         print(f"Entry: {entry}")
    else:
        print(f"FAILURE: Could not find term {test_term}")

if __name__ == "__main__":
    verify_load()
