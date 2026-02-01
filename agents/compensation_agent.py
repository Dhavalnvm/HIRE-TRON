"""
Compensation Agent
Suggests salary ranges based on role requirements
"""

from openai import OpenAI
import json
import logging
from typing import Dict, Optional
from tenacity import retry, stop_after_attempt, wait_exponential
from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CompensationAgent:
    """Generate compensation recommendations"""
    
    def __init__(self):
        """Initialize OpenAI client"""
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.model = Config.CHAT_MODEL
    
    @retry(
        stop=stop_after_attempt(Config.MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def suggest_compensation(
        self,
        jd_text: str,
        parsed_jd: Optional[Dict] = None,
        candidate_score: Optional[int] = None
    ) -> Optional[Dict]:
        """
        Suggest compensation package
        
        Args:
            jd_text: Job description text
            parsed_jd: Optional parsed JD data
            candidate_score: Optional candidate match score
            
        Returns:
            Compensation recommendations
        """
        try:
            system_prompt = """You are an expert compensation and benefits analyst.
Your task is to suggest fair and competitive salary ranges.

Consider:
- Role level and responsibilities
- Required experience and skills
- Industry standards
- Geographic location
- Market demand

Provide:
- salary_min: Minimum salary (USD)
- salary_max: Maximum salary (USD)
- salary_median: Median/target salary (USD)
- equity: Equity compensation suggestion
- benefits: Recommended benefits package
- justification: Brief explanation

Return response as JSON with numeric values."""

            user_message = f"""Job Description:
{jd_text}

{"Candidate Match Score: " + str(candidate_score) if candidate_score else ""}

Suggest a competitive compensation package."""

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
            logger.info(f"Generated compensation: ${result.get('salary_min', 0)}-${result.get('salary_max', 0)}")
            return result
            
        except Exception as e:
            logger.error(f"Error generating compensation: {e}")
            return None