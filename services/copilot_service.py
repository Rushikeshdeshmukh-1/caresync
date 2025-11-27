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
        Smart chat interface using Local LLM (Ollama) with RAG and ICD-11 API.
        """
        import httpx
        from services.icd11_api import ICD11API
        from services.copilot_rag import CoPilotRAG
        
        # Initialize helpers (lazy load or singleton in real app, here locally)
        icd_api = ICD11API()
        rag = CoPilotRAG() # Will load existing index
        
        # Prepare context for LLM
        notes = context.get('notes', '')
        meds = context.get('meds', [])
        conditions = context.get('comorbidities', [])
        
        # 1. RAG Search (Ayurvedic Knowledge)
        rag_context = ""
        rag_results = rag.search(message, k=2)
        if rag_results:
            rag_texts = [f"- {r['text']}" for r in rag_results]
            rag_context = "\nRelevant Ayurvedic Knowledge:\n" + "\n".join(rag_texts)
            
        # 2. ICD-11 API Search (if asked)
        icd_context = ""
        if "code" in message.lower() or "icd" in message.lower():
            icd_results = await icd_api.search(message)
            if icd_results:
                icd_texts = [f"- {r['code']}: {r['title']} ({r['url']})" for r in icd_results]
                icd_context = "\nICD-11 Search Results:\n" + "\n".join(icd_texts)
        
        system_prompt = f"""You are an AI clinical assistant supporting a doctor in an AYUSH clinic.
        
        CONTEXT:
        - Clinical Notes: {notes}
        - Medications: {', '.join(meds) if meds else 'None'}
        - Conditions: {', '.join(conditions) if conditions else 'None'}
        {rag_context}
        {icd_context}
        
        INSTRUCTIONS:
        - Answer the user's question DIRECTLY based on the context and provided knowledge.
        - Use a professional, structured format (bullet points or short paragraphs).
        - DO NOT generate "Question:" or "Answer:" labels.
        - DO NOT hallucinate information not in the context.
        - If the information is missing, state "Not specified in the records."
        """

        try:
            # Try calling Ollama
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "http://localhost:11434/api/chat",
                    json={
                        "model": "gemma:2b",
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": message}
                        ],
                        "options": {
                            "temperature": 0.3
                        },
                        "stream": False
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    llm_response = data.get('message', {}).get('content', '')
                    if llm_response:
                        audit_log(
                            action="copilot_chat",
                            actor="clinician",
                            encounter_id=encounter_id,
                            resource_target="chat",
                            status="success",
                            payload_summary={"source": "ollama/gemma:2b", "rag_hits": len(rag_results)}
                        )
                        return llm_response

        except Exception as e:
            logger.warning(f"Ollama LLM failed, falling back to rule-based: {e}")

        # --- Fallback to Rule-Based Logic ---
        # (Keep existing fallback logic)
        message_lower = message.lower()
        response = ""
        
        # 1. Check for AYUSH terms in the message
        extracted_terms = self._extract_ayush_terms(message)
        if extracted_terms:
            term_responses = []
            for item in extracted_terms:
                term = item['term']
                result = await self.mapping_engine.suggest(term)
                candidates = result.get('results', [])
                if candidates:
                    top_cand = candidates[0]
                    term_responses.append(f"For **{term}**, the top ICD-11 mapping is **{top_cand['icd_code']}** ({top_cand['icd_title']}).")
                else:
                    term_responses.append(f"I recognized **{term}** but couldn't find a direct ICD-11 mapping.")
            response = " ".join(term_responses)

        # 2. Check for intent keywords
        elif "treatment" in message_lower or "medicine" in message_lower:
            response = "I cannot prescribe medications directly. However, based on the symptoms, consider reviewing standard treatment protocols for the identified conditions. Please check for any contraindications with current medications."
            
        elif "contraindication" in message_lower or "safety" in message_lower:
            # Re-run safety check on context
            warnings = self._check_safety(context, [])
            if warnings:
                warning_texts = [f"- {w['message']}" for w in warnings]
                response = "I found the following potential safety issues:\n" + "\n".join(warning_texts)
            else:
                response = "I didn't detect any specific contraindications based on the current patient context and medications."

        elif "summary" in message_lower:
            if notes:
                response = f"Here is a brief summary of the notes so far: The patient presents with symptoms described as '{notes[:50]}...'."
            else:
                response = "The clinical notes are currently empty."

        # 3. Fallback
        if not response:
            response = "I'm listening. You can ask me about specific AYUSH terms, potential contraindications, or for a summary of the current notes. (LLM is currently unavailable)"

        audit_log(
            action="copilot_chat",
            actor="clinician",
            encounter_id=encounter_id,
            resource_target="chat",
            status="success",
            payload_summary={"source": "rule-based", "message_length": len(message), "response_length": len(response)}
        )
        
        return response
