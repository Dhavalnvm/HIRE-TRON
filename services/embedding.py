"""
Embedding service using OpenAI API
Handles text embedding generation for vector storage
"""

from openai import OpenAI
from typing import List
import logging
from tenacity import retry, stop_after_attempt, wait_exponential
from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmbeddingService:
    """Generate embeddings using OpenAI API"""
    
    def __init__(self):
        """Initialize OpenAI client"""
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.model = Config.EMBEDDING_MODEL
    
    @retry(
        stop=stop_after_attempt(Config.MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text
        
        Args:
            text: Input text to embed
            
        Returns:
            List of floats representing the embedding
        """
        try:
            # Clean and truncate text if needed
            text = text.replace("\n", " ").strip()
            if len(text) > 8000:  # Rough token limit
                text = text[:8000]
            
            response = self.client.embeddings.create(
                model=self.model,
                input=text
            )
            
            embedding = response.data[0].embedding
            logger.info(f"Generated embedding with {len(embedding)} dimensions")
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embeddings
        """
        embeddings = []
        for text in texts:
            try:
                embedding = self.generate_embedding(text)
                embeddings.append(embedding)
            except Exception as e:
                logger.error(f"Failed to embed text: {e}")
                embeddings.append([])
        
        return embeddings