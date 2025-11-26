"""
Build FAISS Index Script
Creates FAISS index from ICD-11 data for vector search
"""

import os
import sys
import csv
import json
import logging
from typing import List, Dict, Any

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.faiss_index import FaissIndex

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_icd_from_csv(csv_path: str) -> List[Dict[str, Any]]:
    """Load ICD-11 data from CSV file"""
    icd_data = []
    
    if not os.path.exists(csv_path):
        logger.warning(f"CSV file not found: {csv_path}")
        return icd_data
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                icd_data.append({
                    'code': row.get('code', ''),
                    'title': row.get('title', ''),
                    'description': row.get('short_description', '') or row.get('description', '')
                })
        logger.info(f"Loaded {len(icd_data)} ICD-11 codes from CSV")
    except Exception as e:
        logger.error(f"Error loading CSV: {str(e)}")
    
    return icd_data


def load_icd_from_json(json_path: str) -> List[Dict[str, Any]]:
    """Load ICD-11 data from JSON file"""
    icd_data = []
    
    if not os.path.exists(json_path):
        logger.warning(f"JSON file not found: {json_path}")
        return icd_data
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                icd_data = data
            elif isinstance(data, dict):
                icd_data = list(data.values())
        logger.info(f"Loaded {len(icd_data)} ICD-11 codes from JSON")
    except Exception as e:
        logger.error(f"Error loading JSON: {str(e)}")
    
    return icd_data


def main():
    """Main function to build FAISS index"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Build FAISS index from ICD-11 data')
    parser.add_argument('--icd_csv', type=str, default='data/icd_short.csv',
                       help='Path to ICD-11 CSV file')
    parser.add_argument('--icd_json', type=str, default=None,
                       help='Path to ICD-11 JSON file (optional)')
    parser.add_argument('--out_index', type=str, default='data/icd_index.faiss',
                       help='Output path for FAISS index')
    parser.add_argument('--out_texts', type=str, default='data/icd_texts.npy',
                       help='Output path for texts array')
    
    args = parser.parse_args()
    
    # Load ICD data
    icd_data = []
    
    if args.icd_csv:
        icd_data.extend(load_icd_from_csv(args.icd_csv))
    
    if args.icd_json:
        icd_data.extend(load_icd_from_json(args.icd_json))
    
    if not icd_data:
        logger.error("No ICD-11 data loaded. Please provide --icd_csv or --icd_json")
        return
    
    # Build index
    faiss_index = FaissIndex()
    success = faiss_index.build_index(icd_data, args.out_index, args.out_texts)
    
    if success:
        logger.info(f"FAISS index built successfully!")
        logger.info(f"  Index: {args.out_index}")
        logger.info(f"  Texts: {args.out_texts}")
        logger.info(f"  Vectors: {faiss_index.index.ntotal if faiss_index.index else 0}")
    else:
        logger.error("Failed to build FAISS index")


if __name__ == '__main__':
    main()
