"""
Terminology Service for NAMASTE codes
Handles CSV ingestion, CodeSystem generation, and ConceptMap creation
"""

from fhir.resources.codesystem import CodeSystem, CodeSystemConcept
from fhir.resources.valueset import ValueSet, ValueSetCompose, ValueSetComposeInclude
from fhir.resources.conceptmap import ConceptMap, ConceptMapGroup, ConceptMapGroupElement, ConceptMapGroupElementTarget
from fhir.resources.bundle import Bundle, BundleEntry, BundleEntryRequest
from fhir.resources.condition import Condition
from typing import List, Dict, Optional, Any
import csv
import os
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class TerminologyService:
    """Service for managing NAMASTE terminology"""
    
    def __init__(self):
        self.namaste_codes: Dict[str, Dict] = {}
        self.namaste_to_tm2_map: Dict[str, List[str]] = {}
        self.tm2_to_namaste_map: Dict[str, List[str]] = {}
        self.data_dir = "data"
        os.makedirs(self.data_dir, exist_ok=True)
    
    async def initialize(self):
        """Initialize service by loading NAMASTE data"""
        namaste_file = os.path.join(self.data_dir, "namaste.csv")
        if os.path.exists(namaste_file):
            await self.ingest_namaste_csv(namaste_file)
        else:
            logger.warning(f"NAMASTE CSV not found at {namaste_file}. Service will use WHO API for all mappings.")
            # Don't create dummy data - rely on API
    
    async def ingest_namaste_csv(self, csv_path: str):
        """
        Ingest NAMASTE CSV export and generate FHIR CodeSystem
        Expected CSV format: code,display,definition,system,who_term,icd11_tm2_code
        """
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                logger.info(f"Loading {len(rows)} NAMASTE codes from {csv_path}")
                
                for row in rows:
                    code = str(row.get('code', '')).strip()
                    display = str(row.get('display', '')).strip()
                    definition = str(row.get('definition', '')).strip()
                    system = str(row.get('system', 'NAMASTE')).strip()
                    who_term = str(row.get('who_term', '')).strip()
                    icd11_tm2_code = str(row.get('icd11_tm2_code', '')).strip()
                    
                    if code:
                        self.namaste_codes[code] = {
                            "code": code,
                            "display": display or code,
                            "definition": definition,
                            "system": system,
                            "who_term": who_term,
                            "icd11_tm2_code": icd11_tm2_code
                        }
                        
                        # Build mapping
                        if icd11_tm2_code:
                            if code not in self.namaste_to_tm2_map:
                                self.namaste_to_tm2_map[code] = []
                            if icd11_tm2_code not in self.namaste_to_tm2_map[code]:
                                self.namaste_to_tm2_map[code].append(icd11_tm2_code)
                            
                            if icd11_tm2_code not in self.tm2_to_namaste_map:
                                self.tm2_to_namaste_map[icd11_tm2_code] = []
                            if code not in self.tm2_to_namaste_map[icd11_tm2_code]:
                                self.tm2_to_namaste_map[icd11_tm2_code].append(code)
            
            logger.info(f"Loaded {len(self.namaste_codes)} NAMASTE codes")
            return True
        except Exception as e:
            logger.error(f"Error ingesting NAMASTE CSV: {str(e)}")
            raise
    
    
    def get_namaste_codesystem(self) -> CodeSystem:
        """Generate FHIR CodeSystem for NAMASTE"""
        concepts = []
        for code, data in self.namaste_codes.items():
            concept = CodeSystemConcept(
                code=code,
                display=data["display"],
                definition=data.get("definition")
            )
            concepts.append(concept)
        
        codesystem = CodeSystem(
            id="namaste",
            url="http://namaste.ayush.gov.in/fhir/CodeSystem/namaste",
            version="1.0.0",
            name="NAMASTE",
            title="National AYUSH Morbidity & Standardized Terminologies Electronic",
            status="active",
            experimental=False,
            date=datetime.utcnow().isoformat(),
            publisher="Ministry of Ayush, Government of India",
            description="NAMASTE codes for Ayurveda, Siddha, and Unani disorders",
            caseSensitive=True,
            content="complete",
            concept=concepts
        )
        
        return codesystem
    
    def get_namaste_valueset(self) -> ValueSet:
        """Generate FHIR ValueSet for NAMASTE diagnoses"""
        include = ValueSetComposeInclude(
            system="http://namaste.ayush.gov.in/fhir/CodeSystem/namaste",
            version="1.0.0"
        )
        
        compose = ValueSetCompose(include=[include])
        
        valueset = ValueSet(
            id="namaste-diagnosis",
            url="http://namaste.ayush.gov.in/fhir/ValueSet/namaste-diagnosis",
            version="1.0.0",
            name="NAMASTEDiagnosis",
            title="NAMASTE Diagnosis ValueSet",
            status="active",
            experimental=False,
            date=datetime.utcnow().isoformat(),
            publisher="Ministry of Ayush, Government of India",
            description="ValueSet for NAMASTE diagnosis codes",
            compose=compose
        )
        
        return valueset
    
    def get_namaste_to_tm2_conceptmap(self) -> ConceptMap:
        """Generate ConceptMap for NAMASTE to ICD-11 TM2"""
        elements = []
        
        for source_code, target_codes in self.namaste_to_tm2_map.items():
            targets = [
                ConceptMapGroupElementTarget(
                    code=target_code,
                    display=f"ICD-11 TM2: {target_code}",
                    equivalence="relatedto"
                )
                for target_code in target_codes
            ]
            
            element = ConceptMapGroupElement(
                code=source_code,
                display=self.namaste_codes.get(source_code, {}).get("display", source_code),
                target=targets
            )
            elements.append(element)
        
        group = ConceptMapGroup(
            source="http://namaste.ayush.gov.in/fhir/CodeSystem/namaste",
            target="http://id.who.int/icd/release/11/mms/release/icd11Mms",
            element=elements
        )
        
        conceptmap = ConceptMap(
            id="namaste-to-icd11-tm2",
            url="http://namaste.ayush.gov.in/fhir/ConceptMap/namaste-to-icd11-tm2",
            version="1.0.0",
            name="NAMASTEToICD11TM2",
            title="NAMASTE to ICD-11 TM2 ConceptMap",
            status="active",
            experimental=False,
            date=datetime.utcnow().isoformat(),
            publisher="Ministry of Ayush, Government of India",
            description="ConceptMap mapping NAMASTE codes to ICD-11 TM2",
            group=[group]
        )
        
        return conceptmap
    
    async def search(self, query: str, system: Optional[str] = None, limit: int = 20) -> List[Dict]:
        """
        Search diagnoses across NAMASTE, ICD-11 TM2, and Biomedicine
        """
        results = []
        query_lower = query.lower()
        
        # Search NAMASTE codes
        if not system or system == "NAMASTE":
            for code, data in self.namaste_codes.items():
                if (query_lower in code.lower() or 
                    query_lower in data["display"].lower() or
                    query_lower in data.get("definition", "").lower()):
                    results.append({
                        "code": code,
                        "display": data["display"],
                        "system": "http://namaste.ayush.gov.in/fhir/CodeSystem/namaste",
                        "system_name": "NAMASTE",
                        "definition": data.get("definition"),
                        "who_term": data.get("who_term"),
                        "icd11_tm2_code": data.get("icd11_tm2_code")
                    })
                    if len(results) >= limit:
                        break
        
        return results[:limit]
    
    async def translate(
        self, 
        source_code: str, 
        source_system: str, 
        target_system: str
    ) -> Dict[str, Any]:
        """
        Translate codes between NAMASTE and ICD-11 TM2
        """
        if source_system == "NAMASTE" and target_system == "ICD11-TM2":
            target_codes = self.namaste_to_tm2_map.get(source_code, [])
            return {
                "source_code": source_code,
                "source_system": source_system,
                "target_system": target_system,
                "target_codes": target_codes,
                "equivalence": "relatedto"
            }
        elif source_system == "ICD11-TM2" and target_system == "NAMASTE":
            target_codes = self.tm2_to_namaste_map.get(source_code, [])
            return {
                "source_code": source_code,
                "source_system": source_system,
                "target_system": target_system,
                "target_codes": target_codes,
                "equivalence": "relatedto"
            }
        else:
            raise ValueError(f"Translation not supported from {source_system} to {target_system}")
    
    async def validate_double_coding(self, bundle: Bundle) -> Bundle:
        """
        Validate FHIR Bundle ensures ProblemList entries have both NAMASTE and ICD-11 codes
        """
        validated_entries = []
        
        for entry in bundle.entry or []:
            resource = entry.resource
            
            if isinstance(resource, Condition):
                # Check for double coding
                coding = resource.code.coding if resource.code else []
                has_namaste = any(
                    c.system == "http://namaste.ayush.gov.in/fhir/CodeSystem/namaste"
                    for c in coding
                )
                has_icd11 = any(
                    "icd11" in c.system.lower() or "who.int" in c.system.lower()
                    for c in coding
                )
                
                if not (has_namaste and has_icd11):
                    raise ValueError(
                        f"Condition {resource.id} must have both NAMASTE and ICD-11 codes for double coding"
                    )
            
            validated_entries.append(entry)
        
        bundle.entry = validated_entries
        return bundle
    
    async def store_bundle(self, bundle: Bundle) -> str:
        """Store validated bundle and return bundle ID"""
        bundle_id = bundle.id or f"bundle-{datetime.utcnow().isoformat()}"
        
        # In production, store in database
        # For now, save to file
        bundle_file = os.path.join(self.data_dir, f"bundles/{bundle_id}.json")
        os.makedirs(os.path.dirname(bundle_file), exist_ok=True)
        
        with open(bundle_file, 'w') as f:
            json.dump(bundle.dict(), f, indent=2)
        
        return bundle_id
