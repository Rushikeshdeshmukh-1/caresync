import asyncio
import logging
from services.mapping_engine import MappingEngine
from services.faiss_index import FaissIndex

logging.basicConfig(level=logging.WARNING)

async def main():
    print("="*70)
    print("COMPREHENSIVE MAPPING ENGINE TEST REPORT")
    print("="*70)
    
    print("\n[1/5] Initializing Mapping Engine...")
    faiss_index = FaissIndex()
    mapping_engine = MappingEngine(faiss_index)
    
    print(f"[OK] AYUSH mappings loaded: {len(mapping_engine.ayush_map)}")
    print(f"[OK] ICD-11 codes loaded: {len(mapping_engine.icd11_map)}")
    print(f"[OK] FAISS index: {'YES' if faiss_index.index else 'NO'}")
    if faiss_index.index:
        print(f"  - Vectors: {faiss_index.index.ntotal}")
    
    results = {'exact': 0, 'rule': 0, 'embedding': 0}
    
    # TEST 1: EXACT MATCH
    print("\n" + "="*70)
    print("[2/5] TESTING EXACT MATCH (CSV Lookup)")
    print("="*70)
    
    tests = [("Jwara", True), ("Kasa", True), ("jwara", True), ("XYZ123", False)]
    
    for term, should_match in tests:
        result = mapping_engine.suggest(term, k=1)
        match_type = result.get('type')
        has_results = len(result.get('results', [])) > 0
        
        if should_match:
            passed = match_type == 'exact' and has_results
        else:
            passed = match_type != 'exact'
        
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status} {term:20s} - Type: {match_type}")
        
        if passed and should_match:
            results['exact'] += 1
            icd = result['results'][0].get('icd_code', 'N/A')
            print(f"       ICD Code: {icd}")
    
    print(f"\nExact Match: {results['exact']}/3 passed")
    
    # TEST 2: RULE-BASED MATCH
    print("\n" + "="*70)
    print("[3/5] TESTING RULE-BASED MATCH")
    print("="*70)
    
    rule_tests = [("fever", True), ("cough", True), ("xyz123", False)]
    
    for term, should_match in rule_tests:
        rule_result = mapping_engine.rule_match(term)
        passed = (rule_result is not None) == should_match
        
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status} {term:20s} - Found: {rule_result is not None}")
        
        if rule_result:
            print(f"       ICD: {rule_result.get('icd_code')}")
            print(f"       Reason: {rule_result.get('reason')}")
        
        if passed and should_match:
            results['rule'] += 1
    
    print(f"\nRule Match: {results['rule']}/2 passed")
    
    # TEST 3: EMBEDDING SEARCH
    print("\n" + "="*70)
    print("[4/5] TESTING EMBEDDING SEARCH (AI)")
    print("="*70)
    
    emb_tests = [
        "high body temperature",
        "difficulty breathing",
        "stomach pain"
    ]
    
    for term in emb_tests:
        result = mapping_engine.suggest(term, k=3)
        match_type = result.get('type')
        has_results = len(result.get('results', [])) > 0
        
        passed = has_results and match_type in ['faiss', 'embedding']
        
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status} {term:30s}")
        print(f"       Type: {match_type}, Results: {len(result.get('results', []))}")
        
        if has_results and passed:
            results['embedding'] += 1
            for i, r in enumerate(result['results'][:2], 1):
                icd = r.get('icd_code', 'N/A')
                title = r.get('icd_title', 'N/A')[:35]
                conf = r.get('confidence', 0)
                print(f"         {i}. {icd} - {title} ({conf:.2f})")
    
    print(f"\nEmbedding Search: {results['embedding']}/3 passed")
    
    # FINAL REPORT
    print("\n" + "="*70)
    print("[5/5] FINAL REPORT")
    print("="*70)
    
    print("\n[COMPONENT STATUS]")
    print(f"  1. Exact Match:      {'WORKING' if results['exact'] >= 2 else 'BROKEN'}")
    print(f"  2. Rule Match:       {'WORKING' if results['rule'] >= 1 else 'BROKEN'}")
    print(f"  3. Embedding Search: {'WORKING' if results['embedding'] >= 2 else 'BROKEN'}")
    
    print("\n[ISSUES]")
    if results['rule'] < 1:
        print("  - Rule matching not working (ICD-10 vs ICD-11 mismatch)")
    if results['embedding'] < 2:
        print("  - Embedding search may have issues")
    if results['exact'] >= 2 and results['rule'] < 1 and results['embedding'] >= 2:
        print("  - Only rule matching needs fixing")
    
    print("\n" + "="*70)

if __name__ == "__main__":
    asyncio.run(main())
