"""
Configuration file for HIRE-TRON-X
Manages API keys, constants, and system settings
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """System configuration"""
    
    # OpenAI Settings
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    EMBEDDING_MODEL = "text-embedding-3-small"
    CHAT_MODEL = "gpt-4-turbo-preview"
    TEMPERATURE = 0.7
    MAX_TOKENS = 2000
    
    # Vector Store Settings
    VECTOR_DB_PATH = "./chroma_db"
    JD_COLLECTION = "job_descriptions"
    RESUME_COLLECTION = "resumes"
    TOP_K_CANDIDATES = 10
    
    # Agent Settings
    AGENT_TIMEOUT = 60  # seconds
    MAX_RETRIES = 3
    
    # File Settings
    UPLOAD_DIR = "./data"
    JD_DIR = "./data/jds"
    RESUME_DIR = "./data/resumes"
    MAX_FILE_SIZE = 10  # MB
    
    # Scoring Settings
    PASS_THRESHOLD = 70
    
    @classmethod
    def validate(cls):
        """Validate critical configuration"""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not set. Please add it to .env file")
        
        # Create directories if they don't exist
        os.makedirs(cls.JD_DIR, exist_ok=True)
        os.makedirs(cls.RESUME_DIR, exist_ok=True)
        os.makedirs(cls.VECTOR_DB_PATH, exist_ok=True)
        
        return True

# Validate on import
Config.validate()