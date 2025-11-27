import os
import logging
import pandas as pd
from typing import List, Dict, Any, Optional
from services.faiss_index import FaissIndex

logger = logging.getLogger(__name__)

class CoPilotRAG:
    """
    RAG Service for Co-Pilot using local Ayurvedic dataset.
    """
    
    def __init__(self, index_path: str = 'data/copilot_knowledge.faiss', texts_path: str = 'data/copilot_texts.npy'):
        self.index_path = index_path
        self.texts_path = texts_path
        self.faiss_index = FaissIndex(index_path, texts_path)
        
    def ingest_excel(self, file_path: str) -> bool:
        """
        Ingest Ayurvedic dataset from Excel into FAISS index.
        """
        if not os.path.exists(file_path):
            logger.error(f"Dataset file not found: {file_path}")
            return False
            
        try:
            logger.info(f"Ingesting dataset from {file_path}...")
            df = pd.read_excel(file_path)
            
            # Convert rows to text documents
            documents = []
            for _, row in df.iterrows():
                # Construct a rich text representation
                disease = row.get('Disease', 'Unknown')
                symptoms = row.get('Symptoms', '')
                herbs = row.get('Ayurvedic Herbs', '')
                diet = row.get('Diet and Lifestyle Recommendations', '')
                doshas = row.get('Doshas', '')
                
                # Create a structured text block for embedding
                text_content = (
                    f"Disease: {disease}. "
                    f"Symptoms: {symptoms}. "
                    f"Doshas: {doshas}. "
                    f"Ayurvedic Herbs: {herbs}. "
                    f"Diet: {diet}."
                )
                
                documents.append({
                    'code': disease, # Use disease name as 'code' for lookup
                    'title': disease,
                    'description': text_content
                })
            
            # Build index
            success = self.faiss_index.build_index(documents)
            if success:
                logger.info(f"Successfully ingested {len(documents)} documents into Co-Pilot Knowledge Base.")
            return success
            
        except Exception as e:
            logger.error(f"Error ingesting dataset: {e}")
            return False

    def search(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        """
        Search the knowledge base.
        """
        if not self.faiss_index.is_loaded():
            logger.warning("Co-Pilot Knowledge Base not loaded.")
            return []
            
        return self.faiss_index.query(query, k)
