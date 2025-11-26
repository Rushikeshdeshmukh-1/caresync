"""
ICD-11 Service for fetching TM2 and Biomedicine codes from local CSV data
"""

from fhir.resources.codesystem import CodeSystem, CodeSystemConcept
from typing import List, Dict, Optional, Any
from datetime import datetime
import os
import logging
import csv
import json

logger = logging.getLogger(__name__)


class ICD11Service:
    """Service for managing ICD-11 codes (TM2 and Biomedicine) using local CSV data"""
    
    def __init__(self):
        self.tm2_codes: Dict[str, Dict] = {}
        self.biomedicine_codes: Dict[str, Dict] = {}
        self.data_dir = "data"
        self.icd11_csv_path = os.path.join(self.data_dir, "icd11_codes.csv")
    
    async def initialize(self):
        """Initialize service - load data from CSV"""
        logger.info("Initializing ICD-11 Service (Offline Mode)...")
        self._load_icd11_codes()
        logger.info(f"ICD-11 service initialized - Loaded {len(self.biomedicine_codes)} codes from CSV")
    
    def _load_icd11_codes(self):
        """Load ICD-11 codes from CSV"""
        if os.path.exists(self.icd11_csv_path):
            try:
                with open(self.icd11_csv_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        code = row.get('code', '').strip()
                        title = row.get('title', '').strip()
                        description = row.get('description', '').strip()
                        
                        if code:
                            # Store in biomedicine codes (assuming most are biomedicine for now)
                            # In a real scenario, we might distinguish TM2 if the CSV has a type column
                            # For now, we'll put them in biomedicine_codes as the main lookup
                            self.biomedicine_codes[code] = {
                                "code": code,
                                "display": title,
                                "definition": description,
                                "system": "http://id.who.int/icd/release/11/mms/release/icd11Mms",
                                "foundation_uri": f"http://id.who.int/icd/entity/{code}" # Placeholder URI
                            }
                            
                            # Also populate TM2 codes if they look like TM codes (heuristic)
                            if code.startswith("TM") or "Traditional Medicine" in title:
                                self.tm2_codes[code] = self.biomedicine_codes[code]
                                
            except Exception as e:
                logger.error(f"Error loading ICD-11 codes from CSV: {str(e)}")
        else:
            logger.warning(f"ICD-11 CSV not found at {self.icd11_csv_path}")

    async def get_tm2_codesystem(self) -> CodeSystem:
        """Generate FHIR CodeSystem for ICD-11 TM2"""
        concepts = []
        for code, data in self.tm2_codes.items():
            concept = CodeSystemConcept(
                code=code,
                display=data["display"],
                definition=data.get("definition")
            )
            concepts.append(concept)
        
        codesystem = CodeSystem(
            id="icd11-tm2",
            url="http://id.who.int/icd/release/11/mms/release/icd11Mms",
            version="2024-01",
            name="ICD11TM2",
            title="ICD-11 Traditional Medicine Module 2",
            status="active",
            experimental=False,
            date=datetime.utcnow().isoformat(),
            publisher="World Health Organization",
            description="ICD-11 Traditional Medicine Module 2 codes",
            caseSensitive=True,
            content="complete",
            concept=concepts
        )
        
        return codesystem
    
    async def get_biomedicine_codesystem(self) -> CodeSystem:
        """Generate FHIR CodeSystem for ICD-11 Biomedicine"""
        concepts = []
        # Limit to first 1000 to avoid huge payload if list is large
        count = 0
        for code, data in self.biomedicine_codes.items():
            concept = CodeSystemConcept(
                code=code,
                display=data["display"],
                definition=data.get("definition")
            )
            concepts.append(concept)
            count += 1
            if count >= 1000:
                break
        
        codesystem = CodeSystem(
            id="icd11-biomedicine",
            url="http://id.who.int/icd/release/11/mms/release/icd11Mms",
            version="2024-01",
            name="ICD11Biomedicine",
            title="ICD-11 Biomedicine",
            status="active",
            experimental=False,
            date=datetime.utcnow().isoformat(),
            publisher="World Health Organization",
            description="ICD-11 Biomedicine codes",
            caseSensitive=True,
            content="complete",
            concept=concepts
        )
        
        return codesystem
    
    async def get_biomedicine_code(self, code: str) -> Dict[str, Any]:
        """Get specific ICD-11 Biomedicine code from local data"""
        if code in self.biomedicine_codes:
            return self.biomedicine_codes[code]
        else:
            raise ValueError(f"ICD-11 code {code} not found in local data")
    
    async def search_biomedicine(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search ICD-11 Biomedicine codes from local data"""
        results = []
        query_lower = query.lower()
        
        for code, data in self.biomedicine_codes.items():
            if query_lower in data["display"].lower() or query_lower in data.get("definition", "").lower() or query_lower in code.lower():
                results.append(data)
                if len(results) >= limit:
                    break
        
        logger.info(f"Found {len(results)} ICD-11 codes locally for query: {query}")
        return results
    
    async def search_icd11_by_term(self, term: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search ICD-11 codes (both TM2 and Biomedicine) by term
        """
        # Reuse search_biomedicine as it searches all loaded codes
        return await self.search_biomedicine(term, limit)
    
    async def get_tm2_code(self, code: str) -> Dict[str, Any]:
        """Get specific ICD-11 TM2 code"""
        if code in self.tm2_codes:
            return self.tm2_codes[code]
        elif code in self.biomedicine_codes:
             # Fallback if it's in the main list but not tagged as TM2
             return self.biomedicine_codes[code]
        else:
            raise ValueError(f"ICD-11 TM2 code {code} not found")
