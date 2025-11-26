"""
FAISS Index Service for Vector Search
Uses sentence-transformers for embeddings and FAISS for efficient similarity search
"""

import os
import numpy as np
import faiss
import logging
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

MODEL_NAME = 'all-MiniLM-L6-v2'


class FaissIndex:
    """FAISS-based vector search index for ICD-11 codes"""
    
    def __init__(self, index_path: str = 'data/icd_index.faiss', texts_path: str = 'data/icd_texts.npy'):
        self.index_path = index_path
        self.texts_path = texts_path
        self.model = SentenceTransformer(MODEL_NAME)
        self.index: Optional[faiss.Index] = None
        self.icd_texts: Optional[np.ndarray] = None
        self.icd_codes: List[str] = []
        
        # Load existing index if available
        if os.path.exists(index_path) and os.path.exists(texts_path):
            try:
                self.index = faiss.read_index(index_path)
                self.icd_texts = np.load(texts_path, allow_pickle=True)
                logger.info(f"Loaded FAISS index from {index_path} with {self.index.ntotal} vectors")
            except Exception as e:
                logger.error(f"Error loading FAISS index: {str(e)}")
                self.index = None
                self.icd_texts = None
    
    def build_index(self, icd_data: List[Dict[str, Any]], out_index_path: Optional[str] = None, out_texts_path: Optional[str] = None):
        """
        Build FAISS index from ICD-11 data
        
        Args:
            icd_data: List of dicts with 'code', 'title', 'description' keys
            out_index_path: Optional output path for index
            out_texts_path: Optional output path for texts
        """
        try:
            # Prepare texts for embedding
            texts = []
            codes = []
            
            for item in icd_data:
                code = item.get('code', '')
                title = item.get('title', '')
                description = item.get('description', '') or item.get('short_description', '')
                
                # Create searchable text
                text = f"{code} {title} {description}".strip()
                texts.append(text)
                codes.append(code)
            
            if not texts:
                logger.warning("No texts to index")
                return False
            
            logger.info(f"Encoding {len(texts)} ICD-11 texts...")
            # Generate embeddings
            embeddings = self.model.encode(
                texts,
                convert_to_numpy=True,
                show_progress_bar=True,
                batch_size=32
            )
            
            # Create FAISS index
            dimension = embeddings.shape[1]
            index = faiss.IndexFlatL2(dimension)
            index.add(embeddings.astype('float32'))
            
            # Save index and texts
            out_index_path = out_index_path or self.index_path
            out_texts_path = out_texts_path or self.texts_path
            
            os.makedirs(os.path.dirname(out_index_path), exist_ok=True)
            os.makedirs(os.path.dirname(out_texts_path), exist_ok=True)
            
            faiss.write_index(index, out_index_path)
            np.save(out_texts_path, np.array(texts))
            
            # Store codes separately for lookup
            codes_path = out_texts_path.replace('.npy', '_codes.npy')
            np.save(codes_path, np.array(codes))
            
            self.index = index
            self.icd_texts = np.array(texts)
            self.icd_codes = codes
            
            logger.info(f"Built FAISS index with {index.ntotal} vectors, saved to {out_index_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error building FAISS index: {str(e)}")
            raise
    
    def query(self, text: str, k: int = 3) -> List[Dict[str, Any]]:
        """
        Query the FAISS index for similar ICD-11 codes
        
        Args:
            text: Query text (AYUSH term or description)
            k: Number of results to return
            
        Returns:
            List of dicts with 'code', 'text', 'distance', 'index' keys
        """
        if self.index is None or self.icd_texts is None:
            logger.warning("FAISS index not loaded, returning empty results")
            return []
        
        try:
            # Encode query text
            query_embedding = self.model.encode([text], convert_to_numpy=True)
            
            # Search in FAISS
            distances, indices = self.index.search(query_embedding.astype('float32'), k)
            
            results = []
            for dist, idx in zip(distances[0].tolist(), indices[0].tolist()):
                if idx < 0 or idx >= len(self.icd_texts):
                    continue
                
                text_result = str(self.icd_texts[int(idx)])
                code = self.icd_codes[int(idx)] if int(idx) < len(self.icd_codes) else f"ICD{int(idx)}"
                
                results.append({
                    'code': code,
                    'text': text_result,
                    'index': int(idx),
                    'distance': float(dist)
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Error querying FAISS index: {str(e)}")
            return []
    
    def is_loaded(self) -> bool:
        """Check if index is loaded"""
        return self.index is not None and self.icd_texts is not None
