"""
Mapping Engine - Translator Agent
Implements rule-first → embedding → reranker pipeline for AYUSH to ICD-11 mapping
"""

import json
import os
import logging
from typing import Dict, Any, List, Optional
from sentence_transformers import SentenceTransformer
import joblib

from services.faiss_index import FaissIndex
import csv

logger = logging.getLogger(__name__)
# Trigger reload for NAMASTE data update

AYUSH_MAP_PATH = 'data/ayush_mappings.json'
RERANKER_PATH = 'data/reranker.joblib'
MODEL_NAME = 'all-MiniLM-L6-v2'


class MappingEngine:
    """Primary translator agent for AYUSH to ICD-11 mapping using CSV data"""
    
    def __init__(self, faiss_index: FaissIndex, icd11_service: Optional[Any] = None):
        self.faiss = faiss_index
        self.icd11_service = icd11_service
        self.model = SentenceTransformer(MODEL_NAME)
        self.ayush_map: Dict[str, Dict] = {}
        self.icd11_map: Dict[str, Dict] = {}  # ICD-11 code lookup
        self.reranker = None
        
        # Load AYUSH mappings from CSV
        self._load_ayush_mappings()
        
        # Load ICD-11 codes from CSV
        self._load_icd11_codes()
        
        # Load reranker if available
        self._load_reranker()
    
    def _load_ayush_mappings(self):
        """Load AYUSH term mappings from CSV"""
        namaste_csv = 'data/namaste.csv'
        if os.path.exists(namaste_csv):
            try:
                with open(namaste_csv, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    
                    for row in reader:
                        code = row.get('code', '').strip()
                        display = row.get('display', '').strip()
                        definition = row.get('definition', '').strip()
                        icd_code = row.get('icd11_tm2_code', '').strip()
                        
                        # Skip if no valid ICD code - REMOVED to allow new NAMASTE terms
                        # if not icd_code or len(icd_code) < 2:
                        #    continue
                        
                        # Index by display name (term) - lowercase for case-insensitive search
                        if display:
                            term_key = display.lower().strip()
                            self.ayush_map[term_key] = {
                                'ayush': display,
                                'code': code,
                                'icd_code': icd_code,
                                'definition': definition,
                                'source': 'namaste_csv'
                            }
                        
                        # Also index by code
                        if code:
                            self.ayush_map[code.lower()] = {
                                'ayush': display,
                                'code': code,
                                'icd_code': icd_code,
                                'definition': definition,
                                'source': 'namaste_csv'
                            }
                
                logger.info(f"Loaded {len(self.ayush_map)} AYUSH mappings from CSV")
                # Debug: Print a few examples
                if len(self.ayush_map) > 0:
                    for term in ['kasa', 'jwara', 'shwasa']:
                        if term in self.ayush_map:
                            logger.info(f"✓ {term} -> ICD: {self.ayush_map[term].get('icd_code')}")
            except Exception as e:
                logger.error(f"Error loading AYUSH mappings from CSV: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
        else:
            logger.warning(f"NAMASTE CSV not found at {namaste_csv}")
    
    def _load_icd11_codes(self):
        """Load ICD-11 codes from CSV"""
        icd11_csv = 'data/icd11_codes.csv'
        if os.path.exists(icd11_csv):
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
                
                logger.info(f"Loaded {len(self.icd11_map)} ICD-11 codes from CSV")
            except Exception as e:
                logger.error(f"Error loading ICD-11 codes from CSV: {str(e)}")
        else:
            logger.warning(f"ICD-11 CSV not found at {icd11_csv}")
    
    def _load_reranker(self):
        """Load trained reranker model if available"""
        if os.path.exists(RERANKER_PATH):
            try:
                self.reranker = joblib.load(RERANKER_PATH)
                logger.info(f"Loaded reranker from {RERANKER_PATH}")
            except Exception as e:
                logger.warning(f"Could not load reranker: {str(e)}")
                self.reranker = None
    
    def exact_match(self, term: str) -> Optional[Dict[str, Any]]:
        """
        Check for exact match in NAMASTE CSV
        
        Args:
            term: AYUSH term to match
            
        Returns:
            Mapping dict with ICD-11 code if found, None otherwise
        """
        term_lower = term.strip().lower()
        exact = self.ayush_map.get(term_lower)
        
        if exact:
            # Get ICD-11 details from CSV
            icd_code = exact.get('icd_code', '')
            if icd_code and icd_code in self.icd11_map:
                icd11_info = self.icd11_map[icd_code]
                return {
                    'icd_code': icd_code,
                    'icd_title': icd11_info['title'],
                    'icd_description': icd11_info['description'],
                    'ayush_term': exact.get('ayush', term),
                    'source': 'namaste_csv_exact_match'
                }
            elif icd_code:
            # ICD code exists but not in our CSV, return what we have
                return {
                    'icd_code': icd_code,
                    'icd_title': f"ICD-11 Code: {icd_code}",
                    'ayush_term': exact.get('ayush', term),
                    'source': 'namaste_csv_exact_match'
                }
            else:
                # No ICD code (new NAMASTE term), return NAMASTE info
                return {
                    'icd_code': exact.get('code', 'NAMASTE'), # Use NAMASTE code as fallback
                    'icd_title': exact.get('ayush', term),    # Use AYUSH term as title
                    'icd_description': exact.get('definition', ''),
                    'ayush_term': exact.get('ayush', term),
                    'source': 'namaste_csv_exact_match'
                }
        
        return None
    
    def rule_match(self, term: str) -> Optional[Dict[str, Any]]:
        """
        Apply rule-based heuristics using keyword matching in ICD-11 CSV
        
        Args:
            term: AYUSH term to match
            
        Returns:
            Rule-based mapping if matched, None otherwise
        """
        term_lower = term.lower()
        
        # Common AYUSH term keyword to ICD-11 code mappings
        keyword_to_icd = {
            'amlapitta': 'K21.0',
            'aamla': 'K21.0',
            'kasa': 'J20.9',
            'shwasa': 'J98.8',
            'jwara': 'R50.9',
            'shotha': 'M79.1',
            'aruchi': 'R63.0',
            'amavata': 'M79.3',
            'pandu': 'D64.9',
            'kamala': 'K59.0',
            'atisara': 'K59.0',
            'grahani': 'K58.9',
            'chhardi': 'R11',
            'vibandha': 'K59.0',
            'prameha': 'E11.9',
            'apasmara': 'G40.9',
            'shiroshula': 'R51',
            'ardhavabhedaka': 'G43.9',
            'netraroga': 'H57.9',
            'timira': 'H53.1',
        }
        
        # Find matching keyword
        matched_icd = None
        matched_keyword = None
        for key, icd_code in keyword_to_icd.items():
            if key in term_lower:
                matched_icd = icd_code
                matched_keyword = key
                break
        
        # If we have a match, get ICD-11 details from CSV
        if matched_icd and matched_icd in self.icd11_map:
            icd11_info = self.icd11_map[matched_icd]
            return {
                'icd_code': matched_icd,
                'icd_title': icd11_info['title'],
                'icd_description': icd11_info['description'],
                'reason': f'keyword rule: {matched_keyword} -> {matched_icd}'
            }
        
        return None
    
    def embedding_candidates(self, term: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Get ICD-11 candidates by searching in ICD-11 CSV using text matching
        
        Args:
            term: AYUSH term or description
            k: Number of candidates to return
            
        Returns:
            List of candidate dicts with code, title, distance
        """
        candidates = []
        term_lower = term.lower()
        
        # Search in ICD-11 CSV by matching term in title or description
        for code, icd_info in self.icd11_map.items():
            title = icd_info.get('title', '').lower()
            description = icd_info.get('description', '').lower()
            
            # Simple text matching
            if term_lower in title or term_lower in description or any(word in title for word in term_lower.split()):
                # Calculate simple distance (inverse of match quality)
                match_score = 0
                if term_lower in title:
                    match_score += 2
                if term_lower in description:
                    match_score += 1
                if any(word in title for word in term_lower.split()):
                    match_score += 0.5
                
                distance = 10.0 - match_score  # Lower distance = better match
                
                candidates.append({
                    'icd_code': code,
                    'icd_title': icd_info['title'],
                    'icd_description': icd_info.get('description', ''),
                    'distance': distance,
                    'provenance': {'step': 'csv_text_match', 'source': 'icd11_csv'}
                })
        
        # Sort by distance (lower is better) and return top k
        candidates.sort(key=lambda x: x['distance'])
        
        # If FAISS is available, use it for better ranking
        if self.faiss.is_loaded() and len(candidates) > 0:
            try:
                # Use FAISS to rerank top candidates
                faiss_results = self.faiss.query(term, k=min(k*2, len(candidates)))
                # Update distances from FAISS if available
                for i, cand in enumerate(candidates[:k*2]):
                    if i < len(faiss_results):
                        cand['distance'] = faiss_results[i]['distance']
                        cand['provenance']['step'] = 'csv_faiss_hybrid'
            except Exception as e:
                logger.warning(f"Error using FAISS for reranking: {str(e)}")
        
        return candidates[:k]
    
    def compute_confidence(self, rule_score: float, distance: float, reranker_prob: Optional[float] = None) -> float:
        """
        Compute confidence score from rule score and embedding distance
        
        Args:
            rule_score: Score from rule matching (0.0-1.0)
            distance: FAISS L2 distance
            reranker_prob: Optional reranker probability
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        # Convert distance to similarity score (inverse relationship)
        dist_score = 1.0 / (1.0 + distance)
        
        # Combine rule and distance scores
        combined = 0.6 * rule_score + 0.4 * dist_score
        
        # Apply reranker adjustment if available
        if reranker_prob is not None:
            combined = 0.7 * combined + 0.3 * reranker_prob
        
        # Clamp to [0, 1]
        return float(max(0.0, min(1.0, combined)))
    
    def lexical_overlap(self, text1: str, text2: str) -> float:
        """Compute lexical overlap between two texts"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        if not words1:
            return 0.0
        return len(words1 & words2) / len(words1)
    
    async def suggest(self, term: str, symptoms: Optional[str] = None, k: int = 3) -> Dict[str, Any]:
        """
        Main suggestion method implementing the full pipeline
        
        Args:
            term: AYUSH term
            symptoms: Optional symptoms description
            k: Number of results to return
            
        Returns:
            Dict with type, results, and provenance
        """
        provenance = []
        query_text = term
        if symptoms:
            query_text = f"{term} {symptoms}"
        
        # Step 1: Exact match in NAMASTE CSV
        exact = self.exact_match(term)
        if exact:
            provenance.append({
                'step': 'exact',
                'source': 'namaste_csv',
                'term': exact.get('ayush_term', term)
            })
            return {
                'type': 'exact',
                'results': [{
                    'icd_code': exact.get('icd_code', ''),
                    'icd_title': exact.get('icd_title', ''),
                    'confidence': 0.99,
                    'provenance': provenance
                }]
            }
        
        # Step 2: Rule match using keyword rules
        rule = self.rule_match(term)
        if rule:
            provenance.append({
                'step': 'rule',
                'rule': rule.get('reason', 'keyword match'),
                'source': 'csv_keyword_mapping'
            })
            conf = self.compute_confidence(1.0, distance=0.1)
            return {
                'type': 'rule',
                'results': [{
                    'icd_code': rule['icd_code'],
                    'icd_title': rule['icd_title'],
                    'confidence': conf,
                    'provenance': provenance
                }]
            }
        
        # Step 3: Text-based search in ICD-11 CSV
        candidates = self.embedding_candidates(query_text, k=k * 2)  # Get more for reranking
        
        if not candidates and self.icd11_service:
            # Fallback to API if no local candidates
            try:
                api_results = await self.icd11_service.search_entities(query_text)
                if api_results.get('destinationEntities'):
                    for entity in api_results['destinationEntities'][:k]:
                         # Strip HTML tags from title
                         raw_title = entity.get('title', '')
                         clean_title = raw_title.replace("<em class='found'>", "").replace("</em>", "")
                         
                         # Get code (MMS uses 'theCode')
                         code = entity.get('theCode', '')
                         
                         candidates.append({
                            'icd_code': code,
                            'icd_title': clean_title,
                            'icd_description': '', # MMS search often doesn't return description
                            'distance': 0.5, 
                            'confidence': 0.8,
                            'provenance': {'step': 'api_fallback', 'source': 'who_icd11_api'}
                        })
            except Exception as e:
                logger.error(f"API fallback error: {str(e)}")

        if not candidates:
            return {
                'type': 'faiss',
                'results': [],
                'provenance': [{'step': 'faiss', 'error': 'No candidates found'}]
            }
        
        # Step 4: Rerank if reranker available
        if self.reranker and len(candidates) > 1:
            try:
                # Prepare features for reranker
                features = []
                for cand in candidates:
                    # Features: [distance, lexical_overlap, rule_matched, is_seed_match]
                    dist = cand.get('distance', 10.0)
                    lex = self.lexical_overlap(term, cand.get('icd_title', ''))
                    rule_matched = 0.0  # Already checked
                    is_seed = 0.0  # Could check against seed mappings
                    features.append([dist, lex, rule_matched, is_seed])
                
                # Get reranker probabilities
                reranker_probs = self.reranker.predict_proba(features)[:, 1]  # Positive class probability
                
                # Combine with original scores
                for i, cand in enumerate(candidates):
                    reranker_prob = float(reranker_probs[i]) if i < len(reranker_probs) else 0.5
                    conf = self.compute_confidence(0.0, cand.get('distance', 10.0), reranker_prob)
                    cand['confidence'] = conf
                    cand['provenance']['reranker_prob'] = reranker_prob
            except Exception as e:
                logger.warning(f"Reranker error: {str(e)}, using distance-based confidence")
                for cand in candidates:
                    conf = self.compute_confidence(0.0, cand.get('distance', 10.0))
                    cand['confidence'] = conf
        else:
            # No reranker, use distance-based confidence
            for cand in candidates:
                conf = self.compute_confidence(0.0, cand.get('distance', 10.0))
                cand['confidence'] = conf
        
        # Sort by confidence and return top k
        candidates.sort(key=lambda x: x.get('confidence', 0.0), reverse=True)
        results = candidates[:k]
        
        # Add provenance
        for result in results:
            if 'provenance' not in result:
                result['provenance'] = {}
            result['provenance']['step'] = 'faiss'
            result['provenance']['method'] = 'reranker' if self.reranker else 'distance'
        
        return {
            'type': 'faiss',
            'results': results,
            'provenance': [{'step': 'faiss', 'candidates_considered': len(candidates)}]
        }
