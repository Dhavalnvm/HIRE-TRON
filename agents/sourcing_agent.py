"""
Sourcing Strategy Agent
Suggests candidate sourcing channels and strategies
"""

from openai import OpenAI
import json
import logging
from typing import Dict, Optional
from tenacity import retry, stop_after_attempt, wait_exponential
from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SourcingAgent:
    """Generate candidate sourcing strategies"""
    
    def __init__(self):
        """Initialize OpenAI client"""
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.model = Config.CHAT_MODEL
    
    @retry(
        stop=stop_after_attempt(Config.MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def generate_strategy(
        self,
        jd_text: str,
        parsed_jd: Optional[Dict] = None
    ) -> Optional[Dict]:
        """
        Generate sourcing strategy for a role
        
        Args:
            jd_text: Job description text
            parsed_jd: Optional parsed JD data
            
        Returns:
            Sourcing strategy recommendations
        """
        try:
            system_prompt = """You are an expert talent sourcer and recruitment strategist.
Your task is to suggest effective channels and strategies to find candidates.

Provide:
- channels: List of recommended sourcing channels (LinkedIn, GitHub, job boards, etc.)
- keywords: Search keywords to use
- target_companies: Companies to target for poaching
- communities: Online communities and forums
- events: Relevant conferences and meetups
- outreach_tips: Tips for initial candidate outreach

Return response as JSON."""

            user_message = f"""Job Description:
{jd_text}

Suggest a comprehensive sourcing strategy for this role."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            logger.info(f"Generated sourcing strategy")
            return result
            
        except Exception as e:
            logger.error(f"Error generating sourcing strategy: {e}")
            return None