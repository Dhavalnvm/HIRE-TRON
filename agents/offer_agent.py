"""
Offer Letter Agent
Generates professional offer letters
"""

from openai import OpenAI
import logging
from typing import Dict, Optional
from tenacity import retry, stop_after_attempt, wait_exponential
from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OfferAgent:
    """Generate offer letters"""
    
    def __init__(self):
        """Initialize OpenAI client"""
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.model = Config.CHAT_MODEL
    
    @retry(
        stop=stop_after_attempt(Config.MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def generate_offer_letter(
        self,
        candidate_name: str,
        job_title: str,
        company_name: str,
        salary: int,
        start_date: str,
        parsed_jd: Optional[Dict] = None,
        additional_details: Optional[Dict] = None
    ) -> Optional[str]:
        """
        Generate professional offer letter
        
        Args:
            candidate_name: Candidate's name
            job_title: Position title
            company_name: Company name
            salary: Annual salary
            start_date: Proposed start date
            parsed_jd: Optional parsed job description
            additional_details: Optional benefits, equity, etc.
            
        Returns:
            Formatted offer letter
        """
        try:
            system_prompt = """You are an expert HR professional specializing in offer letters.
Generate a professional, warm, and legally sound offer letter.

Include:
- Warm welcome
- Position details
- Compensation and benefits
- Start date
- Reporting structure
- Next steps
- Standard legal disclaimers

Use professional business letter format."""

            benefits = ""
            if additional_details:
                if additional_details.get('benefits'):
                    benefits = f"\nBenefits: {additional_details['benefits']}"
                if additional_details.get('equity'):
                    benefits += f"\nEquity: {additional_details['equity']}"

            user_message = f"""Generate an offer letter with:
- Candidate: {candidate_name}
- Position: {job_title}
- Company: {company_name}
- Salary: ${salary:,} per year
- Start Date: {start_date}{benefits}

Make it professional yet welcoming."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,
                max_tokens=1500
            )
            
            letter = response.choices[0].message.content
            logger.info(f"Generated offer letter for {candidate_name}")
            return letter
            
        except Exception as e:
            logger.error(f"Error generating offer letter: {e}")
            return None