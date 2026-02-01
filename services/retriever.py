"""
Retrieval service
Coordinates vector search and document retrieval
"""

from typing import List, Dict, Optional
import logging
from vector_store.db import VectorStore
from services.embedding import EmbeddingService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RetrievalService:
    """Coordinate retrieval operations"""
    
    def __init__(self):
        """Initialize services"""
        self.vector_store = VectorStore()
        self.embedding_service = EmbeddingService()
    
    def retrieve_candidates_for_job(
        self,
        jd_id: str,
        top_k: int = 10
    ) -> List[Dict]:
        """
        Retrieve top candidates for a job description
        
        Args:
            jd_id: Job description ID
            top_k: Number of candidates to retrieve
            
        Returns:
            List of candidate dictionaries with resume text and metadata
        """
        try:
            # Get job description
            jd = self.vector_store.get_job_description(jd_id)
            if not jd:
                logger.error(f"Job description {jd_id} not found")
                return []
            
            # Generate embedding for JD
            jd_embedding = self.embedding_service.generate_embedding(jd['text'])
            
            # Search for similar resumes
            results = self.vector_store.search_similar_resumes(
                query_embedding=jd_embedding,
                top_k=top_k
            )
            
            # Format results
            candidates = []
            for i in range(len(results['ids'][0])):
                candidates.append({
                    'resume_id': results['ids'][0][i],
                    'resume_text': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'similarity_score': 1 - results['distances'][0][i]  # Convert distance to similarity
                })
            
            logger.info(f"Retrieved {len(candidates)} candidates for job {jd_id}")
            return candidates
            
        except Exception as e:
            logger.error(f"Error retrieving candidates: {e}")
            return []
    
    def get_jd_text(self, jd_id: str) -> Optional[str]:
        """Get job description text"""
        jd = self.vector_store.get_job_description(jd_id)
        return jd['text'] if jd else None