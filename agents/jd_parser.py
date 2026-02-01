"""
Job Description Parser Agent
Extracts structured information from job descriptions
"""

from openai import OpenAI
import json
import logging
from typing import Dict, Optional
from tenacity import retry, stop_after_attempt, wait_exponential
from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class JDParserAgent:
    """Parse job descriptions into structured data"""
    
    def __init__(self):
        """Initialize OpenAI client"""
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.model = Config.CHAT_MODEL
    
    @retry(
        stop=stop_after_attempt(Config.MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def parse(self, jd_text: str) -> Optional[Dict]:
        """
        Parse job description into structured format
        
        Args:
            jd_text: Raw job description text
            
        Returns:
            Structured job information
        """
        try:
            system_prompt = """You are an expert recruiter and job description analyst.
Your task is to parse job descriptions and extract structured information.

Extract the following information:
- title: Job title
- company: Company name (if mentioned)
- location: Job location
- experience_required: Years of experience required
- skills: List of required technical and soft skills
- responsibilities: Key responsibilities
- qualifications: Educational and professional qualifications
- salary_range: Salary range if mentioned
- employment_type: Full-time, Part-time, Contract, etc.

Return your response as a JSON object with these fields."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Parse this job description:\n\n{jd_text}"}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            logger.info(f"Parsed JD: {result.get('title', 'Unknown')}")
            return result
            
        except Exception as e:
            logger.error(f"Error parsing JD: {e}")
            return None
    
    def extract_key_requirements(self, parsed_jd: Dict) -> str:
        """Extract key requirements as a summary string"""
        try:
            requirements = []
            
            if parsed_jd.get('title'):
                requirements.append(f"Title: {parsed_jd['title']}")
            
            if parsed_jd.get('experience_required'):
                requirements.append(f"Experience: {parsed_jd['experience_required']}")
            
            if parsed_jd.get('skills'):
                skills = parsed_jd['skills']
                if isinstance(skills, list):
                    requirements.append(f"Skills: {', '.join(skills[:10])}")
                else:
                    requirements.append(f"Skills: {skills}")
            
            return " | ".join(requirements)
            
        except Exception as e:
            logger.error(f"Error extracting requirements: {e}")
            return "Requirements extraction failed"