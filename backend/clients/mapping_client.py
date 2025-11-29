"""
Read-Only Mapping Client
Provides read-only access to NAMASTE→ICD mapping resources
Uses separate read-only database credentials to enforce immutability
"""

import os
import csv
import logging
from typing import List, Dict, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class MappingClient:
    """
    Read-only client for NAMASTE→ICD mapping lookups.
    
    This client enforces mapping immutability by:
    1. Using read-only database credentials (if DB-based)
    2. Only exposing read methods (no write/update/delete)
    3. Loading data from CSV files (inherently read-only)
    """
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.namaste_map: Dict[str, Dict] = {}
        self.icd11_map: Dict[str, Dict] = {}
        
        # Load mappings from CSV (read-only)
        self._load_namaste_mappings()
        self._load_icd11_codes()
        
        logger.info(f"MappingClient initialized (READ-ONLY mode)")
        logger.info(f"Loaded {len(self.namaste_map)} NAMASTE mappings")
        logger.info(f"Loaded {len(self.icd11_map)} ICD-11 codes")
    
    def _load_namaste_mappings(self):
        """Load NAMASTE mappings from CSV (read-only)"""
        namaste_csv = self.data_dir / "namaste.csv"
        
        if not namaste_csv.exists():
            logger.warning(f"NAMASTE CSV not found at {namaste_csv}")
            return
        
        try:
            with open(namaste_csv, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    code = row.get('code', '').strip()
                    display = row.get('display', '').strip()
                    definition = row.get('definition', '').strip()
                    icd_code = row.get('icd11_tm2_code', '').strip()
                    
                    # Index by display name (case-insensitive)
                    if display:
                        term_key = display.lower().strip()
                        self.namaste_map[term_key] = {
                            'ayush': display,
                            'code': code,
                            'icd_code': icd_code,
                            'definition': definition,
                            'source': 'namaste_csv'
                        }
                    
                    # Also index by code
                    if code:
                        self.namaste_map[code.lower()] = {
                            'ayush': display,
                            'code': code,
                            'icd_code': icd_code,
                            'definition': definition,
                            'source': 'namaste_csv'
                        }
            
            logger.info(f"✓ Loaded {len(self.namaste_map)} NAMASTE mappings from CSV")
            
        except Exception as e:
            logger.error(f"Error loading NAMASTE mappings: {str(e)}")
    
    def _load_icd11_codes(self):
        """Load ICD-11 codes from CSV (read-only)"""
        icd11_csv = self.data_dir / "icd11_codes.csv"
        
        if not icd11_csv.exists():
            logger.warning(f"ICD-11 CSV not found at {icd11_csv}")
            return
        
        try:
            with open(icd11_csv, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    code = row.get('code', '').strip()
                    title = row.get('title', '').strip()
                    description = row.get('description', '').strip()
                    
                    if code:
                        self.icd11_map[code] = {
                            'code': code,
                            'title': title,
                            'description': description
                        }
            
            logger.info(f"✓ Loaded {len(self.icd11_map)} ICD-11 codes from CSV")
            
        except Exception as e:
            logger.error(f"Error loading ICD-11 codes: {str(e)}")
    
    # ==================== READ-ONLY METHODS ====================
    
    def lookup(self, ayush_term: str) -> Optional[Dict[str, Any]]:
        """
        Lookup AYUSH term and return ICD-11 mapping (READ-ONLY)
        
        Args:
            ayush_term: AYUSH term to lookup
            
        Returns:
            Mapping dict with ICD-11 code if found, None otherwise
        """
        term_lower = ayush_term.strip().lower()
        mapping = self.namaste_map.get(term_lower)
        
        if mapping:
            icd_code = mapping.get('icd_code', '')
            if icd_code and icd_code in self.icd11_map:
                icd11_info = self.icd11_map[icd_code]
                return {
                    'ayush_term': mapping.get('ayush', ayush_term),
                    'ayush_code': mapping.get('code', ''),
                    'icd_code': icd_code,
                    'icd_title': icd11_info['title'],
                    'icd_description': icd11_info['description'],
                    'definition': mapping.get('definition', ''),
                    'source': 'namaste_csv_exact_match'
                }
            elif icd_code:
                # ICD code exists but not in our CSV
                return {
                    'ayush_term': mapping.get('ayush', ayush_term),
                    'ayush_code': mapping.get('code', ''),
                    'icd_code': icd_code,
                    'icd_title': f"ICD-11 Code: {icd_code}",
                    'definition': mapping.get('definition', ''),
                    'source': 'namaste_csv_exact_match'
                }
            else:
                # No ICD code (new NAMASTE term)
                return {
                    'ayush_term': mapping.get('ayush', ayush_term),
                    'ayush_code': mapping.get('code', 'NAMASTE'),
                    'icd_code': None,
                    'icd_title': mapping.get('ayush', ayush_term),
                    'definition': mapping.get('definition', ''),
                    'source': 'namaste_csv_no_icd_mapping'
                }
        
        return None
    
    def lookup_batch(self, ayush_terms: List[str]) -> List[Dict[str, Any]]:
        """
        Batch lookup of multiple AYUSH terms (READ-ONLY)
        
        Args:
            ayush_terms: List of AYUSH terms
            
        Returns:
            List of mapping dicts
        """
        results = []
        for term in ayush_terms:
            mapping = self.lookup(term)
            if mapping:
                results.append(mapping)
        return results
    
    def get_icd11_code(self, icd_code: str) -> Optional[Dict[str, Any]]:
        """
        Get ICD-11 code details (READ-ONLY)
        
        Args:
            icd_code: ICD-11 code
            
        Returns:
            ICD-11 code details if found, None otherwise
        """
        return self.icd11_map.get(icd_code)
    
    def search_namaste(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search NAMASTE terms by keyword (READ-ONLY)
        
        Args:
            query: Search query
            limit: Maximum results to return
            
        Returns:
            List of matching NAMASTE terms
        """
        query_lower = query.lower()
        results = []
        
        seen_terms = set()
        for key, mapping in self.namaste_map.items():
            ayush_term = mapping.get('ayush', '')
            
            # Avoid duplicates (since we index by both term and code)
            if ayush_term in seen_terms:
                continue
            
            # Simple keyword matching
            if query_lower in ayush_term.lower() or query_lower in mapping.get('definition', '').lower():
                results.append({
                    'ayush_term': ayush_term,
                    'ayush_code': mapping.get('code', ''),
                    'icd_code': mapping.get('icd_code', ''),
                    'definition': mapping.get('definition', '')
                })
                seen_terms.add(ayush_term)
            
            if len(results) >= limit:
                break
        
        return results
    
    def get_all_namaste_terms(self) -> List[str]:
        """
        Get all NAMASTE terms (READ-ONLY)
        
        Returns:
            List of all NAMASTE terms
        """
        seen_terms = set()
        terms = []
        
        for mapping in self.namaste_map.values():
            ayush_term = mapping.get('ayush', '')
            if ayush_term and ayush_term not in seen_terms:
                terms.append(ayush_term)
                seen_terms.add(ayush_term)
        
        return sorted(terms)
    
    def get_stats(self) -> Dict[str, int]:
        """
        Get mapping statistics (READ-ONLY)
        
        Returns:
            Dict with counts of mappings
        """
        # Count unique AYUSH terms
        unique_terms = set()
        mapped_terms = 0
        unmapped_terms = 0
        
        for mapping in self.namaste_map.values():
            ayush_term = mapping.get('ayush', '')
            if ayush_term and ayush_term not in unique_terms:
                unique_terms.add(ayush_term)
                if mapping.get('icd_code'):
                    mapped_terms += 1
                else:
                    unmapped_terms += 1
        
        return {
            'total_namaste_terms': len(unique_terms),
            'mapped_to_icd11': mapped_terms,
            'unmapped': unmapped_terms,
            'total_icd11_codes': len(self.icd11_map)
        }


# Global read-only mapping client instance
_mapping_client: Optional[MappingClient] = None


def get_mapping_client() -> MappingClient:
    """
    Get global read-only mapping client instance
    
    Returns:
        MappingClient instance
    """
    global _mapping_client
    if _mapping_client is None:
        _mapping_client = MappingClient()
    return _mapping_client
