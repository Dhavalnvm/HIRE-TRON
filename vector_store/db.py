"""
Vector database management using ChromaDB
Handles storage and retrieval of job descriptions and resumes
"""

import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional
import logging
from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VectorStore:
    """Vector database for job descriptions and resumes"""
    
    def __init__(self):
        """Initialize ChromaDB client and collections"""
        self.client = chromadb.PersistentClient(
            path=Config.VECTOR_DB_PATH,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Create or get collections
        self.jd_collection = self.client.get_or_create_collection(
            name=Config.JD_COLLECTION,
            metadata={"description": "Job descriptions"}
        )
        
        self.resume_collection = self.client.get_or_create_collection(
            name=Config.RESUME_COLLECTION,
            metadata={"description": "Candidate resumes"}
        )
        
        logger.info("Vector store initialized successfully")
    
    def add_job_description(
        self,
        jd_id: str,
        text: str,
        embedding: List[float],
        metadata: Dict
    ) -> bool:
        """
        Add job description to vector store
        
        Args:
            jd_id: Unique identifier
            text: Job description text
            embedding: Vector embedding
            metadata: Additional metadata (title, skills, etc.)
        """
        try:
            self.jd_collection.add(
                ids=[jd_id],
                embeddings=[embedding],
                documents=[text],
                metadatas=[metadata]
            )
            logger.info(f"Added JD: {jd_id}")
            return True
        except Exception as e:
            logger.error(f"Error adding JD {jd_id}: {e}")
            return False
    
    def add_resume(
        self,
        resume_id: str,
        text: str,
        embedding: List[float],
        metadata: Dict
    ) -> bool:
        """
        Add resume to vector store
        
        Args:
            resume_id: Unique identifier
            text: Resume text
            embedding: Vector embedding
            metadata: Additional metadata (name, filename, etc.)
        """
        try:
            self.resume_collection.add(
                ids=[resume_id],
                embeddings=[embedding],
                documents=[text],
                metadatas=[metadata]
            )
            logger.info(f"Added resume: {resume_id}")
            return True
        except Exception as e:
            logger.error(f"Error adding resume {resume_id}: {e}")
            return False
    
    def search_similar_resumes(
        self,
        query_embedding: List[float],
        top_k: int = None
    ) -> Dict:
        """
        Search for similar resumes using vector similarity
        
        Args:
            query_embedding: Job description embedding
            top_k: Number of results to return
            
        Returns:
            Dictionary with ids, documents, metadatas, distances
        """
        if top_k is None:
            top_k = Config.TOP_K_CANDIDATES
            
        try:
            results = self.resume_collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k
            )
            logger.info(f"Retrieved {len(results['ids'][0])} similar resumes")
            return results
        except Exception as e:
            logger.error(f"Error searching resumes: {e}")
            return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}
    
    def get_job_description(self, jd_id: str) -> Optional[Dict]:
        """Retrieve specific job description"""
        try:
            result = self.jd_collection.get(ids=[jd_id])
            if result['ids']:
                return {
                    'id': result['ids'][0],
                    'text': result['documents'][0],
                    'metadata': result['metadatas'][0]
                }
            return None
        except Exception as e:
            logger.error(f"Error retrieving JD {jd_id}: {e}")
            return None
    
    def get_all_job_descriptions(self) -> List[Dict]:
        """Retrieve all job descriptions"""
        try:
            results = self.jd_collection.get()
            jds = []
            for i in range(len(results['ids'])):
                jds.append({
                    'id': results['ids'][i],
                    'text': results['documents'][i],
                    'metadata': results['metadatas'][i]
                })
            return jds
        except Exception as e:
            logger.error(f"Error retrieving all JDs: {e}")
            return []
    
    def get_resume(self, resume_id: str) -> Optional[Dict]:
        """Retrieve specific resume"""
        try:
            result = self.resume_collection.get(ids=[resume_id])
            if result['ids']:
                return {
                    'id': result['ids'][0],
                    'text': result['documents'][0],
                    'metadata': result['metadatas'][0]
                }
            return None
        except Exception as e:
            logger.error(f"Error retrieving resume {resume_id}: {e}")
            return None
    
    def clear_collection(self, collection_type: str) -> bool:
        """Clear a collection (jd or resume)"""
        try:
            if collection_type == "jd":
                self.client.delete_collection(Config.JD_COLLECTION)
                self.jd_collection = self.client.create_collection(
                    name=Config.JD_COLLECTION
                )
            elif collection_type == "resume":
                self.client.delete_collection(Config.RESUME_COLLECTION)
                self.resume_collection = self.client.create_collection(
                    name=Config.RESUME_COLLECTION
                )
            logger.info(f"Cleared {collection_type} collection")
            return True
        except Exception as e:
            logger.error(f"Error clearing {collection_type}: {e}")
            return False
    
    def get_collection_count(self, collection_type: str) -> int:
        """Get count of items in collection"""
        try:
            if collection_type == "jd":
                return self.jd_collection.count()
            elif collection_type == "resume":
                return self.resume_collection.count()
            return 0
        except Exception as e:
            logger.error(f"Error getting count: {e}")
            return 0