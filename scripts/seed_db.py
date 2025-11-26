"""
Seed Database Script
Populates database with initial data
"""

import os
import sys
import json
import logging

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import init_db, SessionLocal, User, AyushTerm, IcdCode
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def seed_ayush_terms():
    """Seed AYUSH terms from JSON file"""
    ayush_file = 'data/ayush_mappings.json'
    
    if not os.path.exists(ayush_file):
        logger.warning(f"AYUSH mappings file not found: {ayush_file}")
        logger.info("Run scripts/seed_ayush_data.py first")
        return 0
    
    session = SessionLocal()
    count = 0
    
    try:
        with open(ayush_file, 'r', encoding='utf-8') as f:
            mappings = json.load(f)
        
        for mapping in mappings:
            term = mapping.get('ayush', '')
            if not term:
                continue
            
            # Check if term exists
            existing = session.query(AyushTerm).filter(AyushTerm.term == term).first()
            if existing:
                continue
            
            # Create new term
            ayush_term = AyushTerm(
                id=str(uuid.uuid4()),
                term=term,
                language=mapping.get('language', ''),
                description=mapping.get('description', ''),
                source=mapping.get('source', 'seed')
            )
            session.add(ayush_term)
            count += 1
        
        session.commit()
        logger.info(f"Seeded {count} AYUSH terms")
    except Exception as e:
        logger.error(f"Error seeding AYUSH terms: {str(e)}")
        session.rollback()
    finally:
        session.close()
    
    return count


def seed_icd_codes():
    """Seed ICD-11 codes from CSV or JSON"""
    session = SessionLocal()
    count = 0
    
    try:
        # Try loading from CSV
        csv_file = 'data/icd_short.csv'
        if os.path.exists(csv_file):
            import csv
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    code = row.get('code', '')
                    if not code:
                        continue
                    
                    # Check if exists
                    existing = session.query(IcdCode).filter(IcdCode.code == code).first()
                    if existing:
                        continue
                    
                    icd_code = IcdCode(
                        code=code,
                        title=row.get('title', ''),
                        description=row.get('short_description', '') or row.get('description', '')
                    )
                    session.add(icd_code)
                    count += 1
        
        session.commit()
        logger.info(f"Seeded {count} ICD-11 codes")
    except Exception as e:
        logger.error(f"Error seeding ICD codes: {str(e)}")
        session.rollback()
    finally:
        session.close()
    
    return count


def seed_users():
    """Seed sample users"""
    session = SessionLocal()
    count = 0
    
    try:
        # Create demo clinician
        existing = session.query(User).filter(User.email == 'demo@clinician.com').first()
        if not existing:
            user = User(
                id=str(uuid.uuid4()),
                name="Demo Clinician",
                email="demo@clinician.com",
                role="clinician"
            )
            session.add(user)
            count += 1
        
        session.commit()
        logger.info(f"Seeded {count} users")
    except Exception as e:
        logger.error(f"Error seeding users: {str(e)}")
        session.rollback()
    finally:
        session.close()
    
    return count


def main():
    """Main seeding function"""
    logger.info("Initializing database...")
    init_db()
    
    logger.info("Seeding database...")
    ayush_count = seed_ayush_terms()
    icd_count = seed_icd_codes()
    user_count = seed_users()
    
    logger.info(f"Database seeding complete:")
    logger.info(f"  AYUSH terms: {ayush_count}")
    logger.info(f"  ICD-11 codes: {icd_count}")
    logger.info(f"  Users: {user_count}")


if __name__ == '__main__':
    main()
