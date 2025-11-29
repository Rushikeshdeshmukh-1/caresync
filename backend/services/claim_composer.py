"""
Claim Composer Service
Generates claim packets from encounters for insurer submission
"""

import uuid
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy import text
from models.database import SessionLocal

logger = logging.getLogger(__name__)


class ClaimComposer:
    """Composes claim packets from encounter data"""
    
    def __init__(self):
        pass
    
    def generate_claim_packet(
        self,
        encounter_id: str,
        claim_type: str = "dual",  # ayush, icd11, dual
        insurer_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate claim packet from encounter
        
        Args:
            encounter_id: Encounter ID
            claim_type: Type of claim (ayush, icd11, dual)
            insurer_id: Optional insurer ID for template selection
            
        Returns:
            Claim packet data
        """
        session = SessionLocal()
        
        try:
            # Fetch encounter data
            encounter_query = text("""
                SELECT e.id, e.patient_id, e.clinician_id, e.encounter_date,
                       e.chief_complaint, e.notes, e.diagnosis,
                       p.name as patient_name, p.date_of_birth, p.gender,
                       u.name as clinician_name
                FROM encounters e
                JOIN patients p ON e.patient_id = p.id
                LEFT JOIN users u ON e.clinician_id = u.id
                WHERE e.id = :encounter_id
            """)
            
            encounter = session.execute(encounter_query, {"encounter_id": encounter_id}).fetchone()
            
            if not encounter:
                raise ValueError(f"Encounter {encounter_id} not found")
            
            # Fetch diagnoses
            diagnoses_query = text("""
                SELECT ayush_term_id, icd_code, diagnosis_type, confidence,
                       accepted_from_ai, clinician_modified
                FROM encounter_diagnoses
                WHERE encounter_id = :encounter_id
            """)
            
            diagnoses = session.execute(diagnoses_query, {"encounter_id": encounter_id}).fetchall()
            
            # Fetch prescriptions
            prescriptions_query = text("""
                SELECT medication, dosage, frequency, duration, instructions
                FROM prescriptions
                WHERE encounter_id = :encounter_id
            """)
            
            prescriptions = session.execute(prescriptions_query, {"encounter_id": encounter_id}).fetchall()
            
            # Build claim payload
            claim_payload = {
                "encounter": {
                    "id": encounter[0],
                    "date": encounter[3].isoformat() if encounter[3] else None,
                    "chief_complaint": encounter[4],
                    "notes": encounter[5],
                    "diagnosis_text": encounter[6]
                },
                "patient": {
                    "id": encounter[1],
                    "name": encounter[7],
                    "date_of_birth": encounter[8],
                    "gender": encounter[9]
                },
                "clinician": {
                    "id": encounter[2],
                    "name": encounter[10]
                },
                "diagnoses": [],
                "prescriptions": [],
                "claim_metadata": {
                    "claim_type": claim_type,
                    "generated_at": datetime.utcnow().isoformat(),
                    "version": "1.0"
                }
            }
            
            # Add diagnoses based on claim type
            for diag in diagnoses:
                diagnosis_entry = {
                    "ayush_term_id": diag[0],
                    "icd_code": diag[1],
                    "type": diag[2],
                    "confidence": float(diag[3]) if diag[3] else None,
                    "ai_suggested": bool(diag[4]),
                    "clinician_modified": bool(diag[5])
                }
                
                # Filter based on claim type
                if claim_type == "ayush" and diag[0]:
                    claim_payload["diagnoses"].append(diagnosis_entry)
                elif claim_type == "icd11" and diag[1]:
                    claim_payload["diagnoses"].append(diagnosis_entry)
                elif claim_type == "dual":
                    claim_payload["diagnoses"].append(diagnosis_entry)
            
            # Add prescriptions
            for rx in prescriptions:
                claim_payload["prescriptions"].append({
                    "medication": rx[0],
                    "dosage": rx[1],
                    "frequency": rx[2],
                    "duration": rx[3],
                    "instructions": rx[4]
                })
            
            # Create claim packet record
            claim_id = str(uuid.uuid4())
            
            insert_query = text("""
                INSERT INTO claim_packets
                (id, encounter_id, patient_id, clinician_id, insurer_id,
                 claim_type, payload, status, created_at)
                VALUES
                (:id, :encounter_id, :patient_id, :clinician_id, :insurer_id,
                 :claim_type, :payload, :status, :created_at)
            """)
            
            session.execute(insert_query, {
                "id": claim_id,
                "encounter_id": encounter_id,
                "patient_id": encounter[1],
                "clinician_id": encounter[2],
                "insurer_id": insurer_id,
                "claim_type": claim_type,
                "payload": json.dumps(claim_payload),
                "status": "draft",
                "created_at": datetime.utcnow()
            })
            
            session.commit()
            
            logger.info(f"Generated claim packet {claim_id} for encounter {encounter_id}")
            
            return {
                "claim_id": claim_id,
                "encounter_id": encounter_id,
                "claim_type": claim_type,
                "status": "draft",
                "payload": claim_payload
            }
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error generating claim: {str(e)}")
            raise
        finally:
            session.close()
    
    def submit_claim(self, claim_id: str) -> Dict[str, Any]:
        """
        Submit claim packet to insurer
        
        Args:
            claim_id: Claim packet ID
            
        Returns:
            Submission result
        """
        session = SessionLocal()
        
        try:
            # Update claim status
            update_query = text("""
                UPDATE claim_packets
                SET status = 'submitted',
                    submitted_at = :submitted_at,
                    updated_at = :updated_at
                WHERE id = :claim_id
            """)
            
            now = datetime.utcnow()
            
            session.execute(update_query, {
                "submitted_at": now,
                "updated_at": now,
                "claim_id": claim_id
            })
            
            session.commit()
            
            logger.info(f"Submitted claim {claim_id}")
            
            return {
                "claim_id": claim_id,
                "status": "submitted",
                "submitted_at": now.isoformat()
            }
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error submitting claim: {str(e)}")
            raise
        finally:
            session.close()


# Global service instance
_claim_composer: Optional[ClaimComposer] = None


def get_claim_composer() -> ClaimComposer:
    """Get global claim composer instance"""
    global _claim_composer
    if _claim_composer is None:
        _claim_composer = ClaimComposer()
    return _claim_composer
