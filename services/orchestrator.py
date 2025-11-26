"""
Orchestration Agent
Background worker for processing unsynced records and routing to insurers/EHR
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os

logger = logging.getLogger(__name__)

PROCESS_INTERVAL = 5  # seconds


class Orchestrator:
    """Background orchestration agent for processing clinical records"""
    
    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or os.getenv("DATABASE_URL", "sqlite:///./terminology.db")
        self.engine = create_engine(self.database_url, connect_args={"check_same_thread": False})
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.running = False
    
    def get_session(self):
        """Get database session"""
        return self.SessionLocal()
    
    async def process_unsynced_records(self):
        """Process unsynced clinical records and create claims"""
        try:
            session = self.get_session()
            
            # Get unsynced records with consent
            query = text("""
                SELECT id, patient_id, ayush_term_id, icd_code, consent, notes, confidence, provenance
                FROM clinical_records
                WHERE synced = 0 AND consent = 1
                LIMIT 10
            """)
            
            rows = session.execute(query).fetchall()
            
            processed = 0
            for row in rows:
                try:
                    # Create claim JSON
                    claim = {
                        'claim_id': f'claim-{row.id}',
                        'patient_id': row.patient_id,
                        'icd_code': row.icd_code,
                        'ayush_term_id': row.ayush_term_id,
                        'consent': bool(row.consent),
                        'confidence': float(row.confidence) if row.confidence else None,
                        'provenance': json.loads(row.provenance) if row.provenance else {},
                        'notes': row.notes,
                        'timestamp': int(time.time())
                    }
                    
                    # Insert into claims log
                    insert_claim = text("""
                        INSERT INTO claims_log (record_id, claim_json, status, created_at)
                        VALUES (:rid, :cj, :st, CURRENT_TIMESTAMP)
                    """)
                    session.execute(insert_claim, {
                        "rid": str(row.id),
                        "cj": json.dumps(claim),
                        "st": "SENT"
                    })
                    
                    # Mark record as synced
                    update_record = text("""
                        UPDATE clinical_records
                        SET synced = 1
                        WHERE id = :rid
                    """)
                    session.execute(update_record, {"rid": str(row.id)})
                    
                    processed += 1
                    logger.info(f"Processed record {row.id} -> claim-{row.id}")
                    
                except Exception as e:
                    logger.error(f"Error processing record {row.id}: {str(e)}")
                    continue
            
            session.commit()
            session.close()
            
            if processed > 0:
                logger.info(f"Orchestrator processed {processed} records")
                
        except Exception as e:
            logger.error(f"Orchestrator error: {str(e)}")
    
    async def run(self):
        """Main orchestration loop"""
        self.running = True
        logger.info("Orchestrator agent started")
        
        while self.running:
            try:
                await self.process_unsynced_records()
            except Exception as e:
                logger.error(f"Orchestrator loop error: {str(e)}")
            
            await asyncio.sleep(PROCESS_INTERVAL)
    
    def stop(self):
        """Stop the orchestrator"""
        self.running = False
        logger.info("Orchestrator agent stopped")
