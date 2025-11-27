"""
Co-Pilot Agent Service
Provides evidence-backed suggestions, warnings, and summaries for clinical encounters.
Strictly enforces read-only access to mapping data.
"""

import logging
import json
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from models.database import AISuggestion, EncounterSummary, OrchestratorAudit
from services.mapping_engine import MappingEngine
from services.safeguards import safe_write, audit_log

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CoPilotService:
    def __init__(self, mapping_engine: MappingEngine):
        self.mapping_engine = mapping_engine
        self.model_version = "copilot-v1.0"
        
        # Simple rule-based safety checks (placeholder for a real DB)
        self.drug_interactions = {
            "metformin": {
                "contraindications": ["renal_failure", "severe_infection"],
                "interactions": ["alcohol", "iodinated_contrast"]
            },
            "aspirin": {
                "contraindications": ["bleeding_disorders", "peptic_ulcer"],
                "interactions": ["warfarin", "ibuprofen"]
            }
        }

    async def analyze_encounter(
        self, 
        db: Session, 
        encounter_id: str, 
        notes: str, 
        patient_context: Dict[str, Any],
        actor: str = "clinician"
    ) -> Dict[str, Any]:
        """
        Analyze encounter notes and provide suggestions.
        READ-ONLY access to mapping data.
        """
        try:
            # 1. NLU Preprocessing (Extract AYUSH terms)
            print("=== COPILOT SERVICE ANALYZE_ENCOUNTER CALLED (NEW CODE) ===")
            ayush_terms = self._extract_ayush_terms(notes)
            
            # 2. Mapping Retrieval (Read-Only)
            suggestions = []
            for term_data in ayush_terms:
                term = term_data['term']
                # Use MappingEngine's suggest method (which is read-only)
                result = await self.mapping_engine.suggest(term)
                candidates = result.get('results', [])
                
                for cand in candidates:
                    suggestions.append({
                        "ayush_term": term,
                        "icd11_code": cand['icd_code'],
                        "icd11_title": cand['icd_title'],
                        "confidence": cand['confidence'],
                        "explanation": f"Matched '{term}' with confidence {cand['confidence']}"
                    })
            
            # 3. Safety Checks
            warnings = self._check_safety(patient_context, suggestions)
            
            # 4. Generate Follow-ups (Rule-based for now)
            followups = self._generate_followups(suggestions, warnings)
            
            # 5. Persist Results (Additive Only)
            suggestion_record = AISuggestion(
                encounter_id=encounter_id,
                ayush_terms=ayush_terms,
                suggestions=suggestions,
                warnings=warnings,
                followups=followups,
                model_version=self.model_version
            )
            
            # Use safe_write to check permission (pass resource name, not db)
            if safe_write("ai_suggestions", suggestion_record, actor):
                db.add(suggestion_record)
                db.commit()
            
            # 6. Audit Log
            audit_log(
                action="copilot_analyze",
                actor=actor,
                encounter_id=encounter_id,
                resource_target="ai_suggestions",
                status="success",
                payload_summary={"term_count": len(ayush_terms), "suggestion_count": len(suggestions)}
            )
            
            return {
                "encounter_id": encounter_id,
                "ayush_terms": ayush_terms,
                "suggestions": suggestions,
                "warnings": warnings,
                "followups": followups,
                "model_version": self.model_version
            }
            
        except Exception as e:
            logger.error(f"Error in Co-Pilot analysis: {e}")
            audit_log(
                action="copilot_analyze",
                actor=actor,
                encounter_id=encounter_id,
                resource_target="ai_suggestions",
                status="failed",
                error_message=str(e)
            )
            raise

    def _extract_ayush_terms(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract AYUSH terms from text using regex/rules.
        Placeholder for NER model.
        """
        terms = []
        # Simple dictionary of known terms for demo
        known_terms = ["amlapitta", "kamala", "atisara", "jwara", "kasa", "shwasa"]
        
        lower_text = text.lower()
        for term in known_terms:
            for match in re.finditer(r'\b' + re.escape(term) + r'\b', lower_text):
                terms.append({
                    "term": term.capitalize(),
                    "span_start": match.start(),
                    "span_end": match.end()
                })
        
        return terms

    def _check_safety(self, context: Dict[str, Any], suggestions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Check for safety warnings based on patient context and suggestions.
        """
        warnings = []
        meds = context.get("meds", [])
        conditions = context.get("comorbidities", [])
        
        # Check drug interactions
        for med in meds:
            med_lower = med.lower()
            if med_lower in self.drug_interactions:
                rules = self.drug_interactions[med_lower]
                
                # Check contraindications
                for condition in conditions:
                    if condition.lower() in rules["contraindications"]:
                        warnings.append({
                            "code": "DRUG_CONTRAINDICATION",
                            "severity": "high",
                            "message": f"Contraindication: {med} with {condition}"
                        })
        
        return warnings

    def _generate_followups(self, suggestions: List[Dict[str, Any]], warnings: List[Dict[str, Any]]) -> List[str]:
        """
        Generate follow-up actions.
        """
        followups = []
        
        if warnings:
            followups.append("Review medication contraindications immediately.")
            
        if not suggestions:
            followups.append("Consider manual search for symptoms.")
            
        # Example rule
        for sugg in suggestions:
            if sugg["ayush_term"] == "Amlapitta":
                followups.append("Recommend dietary changes (Pathya/Apathya).")
                
        return list(set(followups))  # Deduplicate

    async def chat(self, db: Session, encounter_id: str, message: str, context: Dict[str, Any]) -> str:
        """
        Simple chat interface (placeholder for LLM).
        """
        # In a real implementation, this would call an LLM with RAG
        response = f"I understand you're asking about '{message}'. Based on the encounter context, I recommend reviewing the suggested ICD-11 codes. (This is a placeholder response)."
        
        audit_log(
            action="copilot_chat",
            actor="clinician",
            encounter_id=encounter_id,
            resource_target="chat",
            status="success",
            payload_summary={"message_length": len(message)}
        )
        
        return response
