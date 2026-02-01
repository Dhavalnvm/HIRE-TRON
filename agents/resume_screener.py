"""
Resume Screening Agent
Evaluates resumes against job descriptions
"""

from openai import OpenAI
import json
import logging
from typing import Dict, Optional
from tenacity import retry, stop_after_attempt, wait_exponential
from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ResumeScreenerAgent:
    """Screen resumes against job requirements"""
    
    def __init__(self):
        """Initialize OpenAI client"""
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.model = Config.CHAT_MODEL
    
    @retry(
        stop=stop_after_attempt(Config.MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def screen(
        self,
        jd_text: str,
        resume_text: str,
        parsed_jd: Optional[Dict] = None
    ) -> Optional[Dict]:
        """
        Screen resume against job description
        
        Args:
            jd_text: Job description text
            resume_text: Resume text
            parsed_jd: Optional parsed JD data
            
        Returns:
            Screening results with score and analysis
        """
        try:
            system_prompt = """You are an expert technical recruiter and resume screener.
Your task is to evaluate how well a candidate's resume matches a job description.

Analyze:
1. Skills match (technical and soft skills)
2. Experience level and relevance
3. Education and qualifications
4. Overall cultural and role fit

Provide:
- score: Overall match score from 0-100
- strengths: List of 3-5 key strengths
- weaknesses: List of 3-5 gaps or concerns
- recommendation: "HIRE", "MAYBE", or "REJECT"
- reasoning: Brief explanation of your decision

Be objective and thorough. Return response as JSON."""

            user_message = f"""Job Description:
{jd_text}

Resume:
{resume_text}

Evaluate this candidate's fit for the role."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.5,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            logger.info(f"Screened resume - Score: {result.get('score', 'N/A')}")
            return result
            
        except Exception as e:
            logger.error(f"Error screening resume: {e}")
            return None