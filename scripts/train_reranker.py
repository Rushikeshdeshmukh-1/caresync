"""
Reranker Training Script
Trains a LogisticRegression reranker from mapping feedback
"""

import sqlite3
import numpy as np
import json
import os
import logging
from typing import Dict, List, Tuple
from sentence_transformers import SentenceTransformer
from sklearn.linear_model import LogisticRegression
import joblib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB = 'data/db.sqlite'
MODEL_PATH = 'data/reranker.joblib'
EMB_MODEL = SentenceTransformer('all-MiniLM-L6-v2')
AYUSH_MAP_PATH = 'data/ayush_mappings.json'


def lexical_overlap(text1: str, text2: str) -> float:
    """Compute lexical overlap between two texts"""
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    if not words1:
        return 0.0
    return len(words1 & words2) / len(words1)


def load_feedback() -> List[Tuple]:
    """Load feedback data from database"""
    if not os.path.exists(DB):
        logger.warning(f"Database {DB} not found")
        return []
    
    try:
        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        
        # Query feedback with related record data
        query = """
            SELECT 
                mf.id,
                cr.ayush_term_id,
                cr.icd_code,
                mf.new_icd_code,
                mf.action
            FROM mapping_feedback mf
            JOIN clinical_records cr ON mf.record_id = cr.id
            WHERE mf.action IN ('accepted', 'edited', 'rejected')
        """
        
        cur.execute(query)
        rows = cur.fetchall()
        conn.close()
        
        logger.info(f"Loaded {len(rows)} feedback records")
        return rows
    except Exception as e:
        logger.error(f"Error loading feedback: {str(e)}")
        return []


def load_icd_texts() -> Dict[str, str]:
    """Load ICD-11 texts for lookup"""
    icd_texts = {}
    
    # Try loading from numpy array
    texts_path = 'data/icd_texts.npy'
    if os.path.exists(texts_path):
        try:
            arr = np.load(texts_path, allow_pickle=True)
            for text in arr:
                try:
                    parsed = json.loads(text)
                    code = parsed.get('code') or parsed.get('icd_code', '')
                    title = parsed.get('title') or parsed.get('icd_title', '')
                    desc = parsed.get('description') or parsed.get('short_description', '')
                    icd_texts[code] = f"{title} {desc}".strip()
                except:
                    # Try pipe-separated format
                    parts = str(text).split('|')
                    if len(parts) >= 2:
                        code = parts[0].strip()
                        title = parts[1].strip()
                        icd_texts[code] = title
        except Exception as e:
            logger.warning(f"Error loading ICD texts from numpy: {str(e)}")
    
    # Try loading from CSV
    csv_path = 'data/icd_short.csv'
    if os.path.exists(csv_path):
        try:
            import csv
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    code = row.get('code', '')
                    title = row.get('title', '')
                    desc = row.get('short_description', '') or row.get('description', '')
                    if code:
                        icd_texts[code] = f"{title} {desc}".strip()
        except Exception as e:
            logger.warning(f"Error loading ICD texts from CSV: {str(e)}")
    
    logger.info(f"Loaded {len(icd_texts)} ICD-11 text mappings")
    return icd_texts


def load_ayush_mappings() -> Dict[str, Dict]:
    """Load AYUSH term mappings"""
    ayush_map = {}
    
    if os.path.exists(AYUSH_MAP_PATH):
        try:
            with open(AYUSH_MAP_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    for entry in data:
                        term = entry.get('ayush', '').lower()
                        if term:
                            ayush_map[term] = entry
                elif isinstance(data, dict):
                    ayush_map = {k.lower(): v for k, v in data.items()}
        except Exception as e:
            logger.error(f"Error loading AYUSH mappings: {str(e)}")
    
    return ayush_map


def build_training_examples(rows: List[Tuple], icd_texts: Dict[str, str], ayush_map: Dict[str, Dict]) -> Tuple[np.ndarray, np.ndarray]:
    """Build training examples from feedback"""
    X = []
    y = []
    
    for rid, ayush_term_id, icd_code, new_icd_code, action in rows:
        try:
            # Get AYUSH term text
            ayush_entry = ayush_map.get(ayush_term_id.lower(), {})
            ayush_text = ayush_entry.get('description', '') or ayush_entry.get('ayush', ayush_term_id)
            
            # Get ICD text
            target_code = new_icd_code if new_icd_code and action == 'edited' else icd_code
            icd_text = icd_texts.get(target_code, target_code)
            
            if not ayush_text or not icd_text:
                continue
            
            # Compute features
            # Feature 1: Embedding distance
            emb_a = EMB_MODEL.encode([ayush_text])[0]
            emb_i = EMB_MODEL.encode([icd_text])[0]
            distance = float(np.linalg.norm(emb_a - emb_i))
            
            # Feature 2: Lexical overlap
            lex = lexical_overlap(ayush_text, icd_text)
            
            # Feature 3: Rule matched (binary - simplified)
            rule_matched = 1.0 if ayush_term_id.lower() in ayush_map else 0.0
            
            # Feature 4: Is seed match (binary)
            is_seed = 1.0 if ayush_entry.get('source') == 'seed' else 0.0
            
            # Label: 1 for accepted/edited, 0 for rejected
            label = 1 if action in ('accepted', 'edited') else 0
            
            X.append([distance, lex, rule_matched, is_seed])
            y.append(label)
            
        except Exception as e:
            logger.warning(f"Error processing feedback row {rid}: {str(e)}")
            continue
    
    return np.array(X), np.array(y)


def main():
    """Main training function"""
    logger.info("Starting reranker training...")
    
    # Load data
    rows = load_feedback()
    if not rows:
        logger.warning("No feedback to train on. Collect more feedback first.")
        return
    
    if len(rows) < 10:
        logger.warning(f"Not enough feedback samples ({len(rows)} < 10). Collect more feedback.")
        return
    
    icd_texts = load_icd_texts()
    ayush_map = load_ayush_mappings()
    
    # Build training examples
    X, y = build_training_examples(rows, icd_texts, ayush_map)
    
    if len(X) == 0:
        logger.warning("No valid training examples generated")
        return
    
    logger.info(f"Training on {len(X)} examples (positive: {sum(y)}, negative: {len(y) - sum(y)})")
    
    # Train model
    clf = LogisticRegression(random_state=42, max_iter=1000)
    clf.fit(X, y)
    
    # Save model
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump(clf, MODEL_PATH)
    
    # Evaluate
    score = clf.score(X, y)
    logger.info(f"Reranker trained and saved to {MODEL_PATH}")
    logger.info(f"Training accuracy: {score:.3f}")
    
    # Show feature importance
    if hasattr(clf, 'coef_'):
        logger.info(f"Feature coefficients: distance={clf.coef_[0][0]:.3f}, "
                   f"lexical={clf.coef_[0][1]:.3f}, rule={clf.coef_[0][2]:.3f}, "
                   f"seed={clf.coef_[0][3]:.3f}")


if __name__ == '__main__':
    main()
